#!/usr/bin/env python3
"""
agent-task-node — Claude agent as a SonataFlow execution node.

Exposes scoped CI-maintenance tasks over HTTP. Each task runs a focused
`claude -p` invocation with a JSON Schema so the workflow engine gets a
validated, typed result back (no free-text parsing).

POST /task/diagnose  {"job":..,"buildUrl":..}      -> {cause,fixable,proposedAction,confidence}
POST /task/fix       {"job":..,"cause":..}          -> {action,prUrl,branch,summary,pushed}
POST /task/merge     {"prUrl":..}                   -> {merged,reason}
GET  /healthz                                       -> {"ok":true}

Design notes:
- SonataFlow owns flow/state/retry. This node does the intelligent step and
  returns typed JSON. It is NOT amnesiac: each call persists a Claude session
  and returns its `session_id` as `_sid`; the worker threads that `sid` back so
  the whole flow's AI steps share ONE continuous conversation (diagnose -> fix
  -> retries -> decide), and a human can re-attach to it for handoff via
  `docker exec -it agent-task-node claude --resume <sid>`.
- `claude -p --json-schema <schema>` (CLI >= 2.1.x) validates output.
- Prompts are kept terse + per-task (decomposed from the old daily.md).
  They lean on the agent's memory (arch-qube / network-prune / disk traps).
- Auth: relies on the mounted claude-home (/root/.claude) credentials,
  same as the existing daily-ci-agent image this is built FROM.
"""
import base64
import json
import os
import shutil
import subprocess
import re
import time
import hashlib
import tempfile
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
MODEL = os.environ.get("AGENT_MODEL", "")  # empty => settings-driven default
TIMEOUT = int(os.environ.get("AGENT_TASK_TIMEOUT", "900"))  # 15 min per task
STUB = os.environ.get("AGENT_STUB", "") == "1"  # test mode: skip claude, return canned typed JSON
STUB_RESPONSES = {
    "analyze": {"assessment": "stub", "severity": "ok", "recommendation": "none", "needsHuman": False},

    "diagnose": {"cause": "stub: simulated build failure", "category": "code",
                 "fixable": True, "proposedAction": "stub: minimal patch", "confidence": 0.9},
    "fix": {"action": "stub-pr", "prUrl": "https://github.com/jrjohn/stub/pull/1",
            "branch": "ci/stub-fix", "summary": "stub: applied minimal fix", "pushed": True},
    "merge": {"merged": True, "reason": "stub: green build, auto-merged"},
    "readmesync": {"updated": False, "changes": [], "reason": "stub: README accurate"},
    "sweep": {"checked": 14, "red": [], "retriggered": 0, "summary": "stub: all repos green"},
    "decide": {"action": "merge", "resolved": True, "reason": "stub: build green, merge"},
    "escalate": {"resolution": "recorded", "action": "stub: recorded for review", "reason": "stub: exhausted -> recorded"},
    "pm-review": {"verdict": "GO", "dimensions": [{"name": "stub", "pass": True, "note": "stub"}], "feedback": "", "confidence": 0.9},
}

# --- JSON Schemas: the typed contract SonataFlow switches/retries on ---
SCHEMAS = {
    "scan-stale": {
        "type": "object",
        "properties": {
            "started": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["started"],
    },
    "rebase": {
        "type": "object",
        "properties": {
            "rebased": {"type": "boolean"},
            "ciStatus": {"type": "string", "enum": ["green", "red", "pending", "diverged", "conflict"]},
            "reason": {"type": "string"},
        },
        "required": ["rebased", "ciStatus"],
    },
    "audit": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
            "reason": {"type": "string"},
        },
        "required": ["decision"],
    },
    "readmesync": {
        "type": "object",
        "properties": {
            "updated": {"type": "boolean"},
            "changes": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["updated", "reason"],
    },
    "analyze": {
        "type": "object",
        "properties": {
            "assessment": {"type": "string"},
            "severity": {"type": "string", "enum": ["ok", "warn", "critical"]},
            "recommendation": {"type": "string"},
            "needsHuman": {"type": "boolean"},
        },
        "required": ["assessment", "severity", "recommendation"],
    },

    "diagnose": {
        "type": "object",
        "properties": {
            "cause": {"type": "string"},
            "category": {"type": "string",
                         "enum": ["code", "test", "infra", "registry", "disk",
                                  "network", "flaky-transient", "unknown"]},
            "fixable": {"type": "boolean"},
            "proposedAction": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["cause", "category", "fixable", "proposedAction"],
    },
    "fix": {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "prUrl": {"type": "string"},
            "branch": {"type": "string"},
            "summary": {"type": "string"},
            "pushed": {"type": "boolean"},
        },
        "required": ["action", "summary", "pushed"],
    },
    "merge": {
        "type": "object",
        "properties": {
            "merged": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["merged"],
    },
    "sweep": {
        "type": "object",
        "properties": {
            "checked": {"type": "integer"},
            "red": {"type": "array", "items": {"type": "string"}},
            "retriggered": {"type": "integer"},
            "summary": {"type": "string"},
        },
        "required": ["checked", "red", "summary"],
    },
    "decide": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["merge", "escalate", "retry", "review"]},
            "resolved": {"type": "boolean"},
            "reason": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["action", "resolved", "reason"],
    },
    "pm-review": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["GO", "NOGO", "HOLD"]},
            "dimensions": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string"}, "pass": {"type": "boolean"}, "note": {"type": "string"}},
                "required": ["name", "pass"]}},
            "feedback": {"type": "string"},
            "confidence": {"type": "number"},
            "backlog": {"type": "array", "items": {"type": "object", "properties": {"feature_request": {"type": "string"}, "slug": {"type": "string"}, "uiFacing": {"type": "string"}, "priority": {"type": "integer"}}, "required": ["feature_request", "slug"]}},
        },
        "required": ["verdict", "dimensions"],
    },
    "escalate": {
        "type": "object",
        "properties": {
            "resolution": {"type": "string",
                           "enum": ["retry", "closed", "recorded", "merged"]},
            "action": {"type": "string"},
            "reason": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["resolution", "reason"],
    },
}

# --- Per-task prompts (decomposed from daily.md; terse, schema does the shape) ---
def prompt_diagnose(p):
    return (
        f"A Jenkins pipeline build failed. job={p.get('job')} buildUrl={p.get('buildUrl')}.\n"
        "Fetch the console log (curl the buildUrl + /consoleText via the jenkins service), "
        "find the FIRST failing stage and the actual error.\n"
        "BEFORE you classify, SEARCH THE SHARED SESSION ARCHIVE — it holds every past run "
        "(yours and jrjohn's) and the recurring CI traps WITH how they were resolved. Run "
        "`csearch '\"<verbatim error line>\"'` on the exact error string (phrase-quote it), and "
        "`vsearch '<what broke, in plain words>'` for how a similar failure was diagnosed/fixed "
        "before. Recurring traps worth looking up: arch-qube registry blob loss (short read EOF), "
        "docker network prune racing compose builds (network not found), disk-pressure flood "
        "watermark, testcontainer needing docker.sock, mysql container unhealthy (often "
        "flaky-transient). Let what the archive returns inform the cause and proposedAction "
        "instead of guessing.\n"
        "Decide if it is agent-fixable via a code/config change on a PR branch, vs infra needing "
        "host action (not your job), vs a transient that just needs a re-trigger.\n"
        "HARD RULE for the `fixable` field: set fixable=true ONLY when category is "
        "`code` or `test` (a real defect a PR branch can actually change). For category "
        "in {infra, registry, disk, network, flaky-transient, unknown} you MUST set "
        "fixable=false — these are host/infra or non-deterministic issues no PR can fix. "
        "If recent builds of the same branch are green or the failure is non-deterministic, "
        "classify it flaky-transient with fixable=false (it just needs a re-trigger). Never "
        "set fixable=true for a flaky/infra cause even if you can imagine a hardening change. "
        "Return the diagnosis."
    )

def prompt_fix(p):
    return (
        f"Fix the diagnosed CI failure for job={p.get('job')}. Root cause: {p.get('cause')}.\n"
        "FIRST consult the shared session archive for a PROVEN fix instead of reinventing one: "
        "`vsearch '<root-cause concept>'` (how a similar failure was fixed before) and "
        "`csearch '\"<key error / identifier>\"'` for the exact symptom — reuse the known-good change "
        "if one exists.\n"
        "DEPENDENCY-MAJOR PLAYBOOK (renovate `chore(deps)`/`fix(deps)` majors fail in patterned ways — "
        "recognise before giving up):\n"
        " (a) PEER-DEP COUPLING: a tooling major can't go alone — e.g. `typescript` major is locked to "
        "the framework (Angular 21 peers ts<6.0, Angular 22 requires ts>=6.0). If `npm ci`/install shows "
        "ERESOLVE/`peer ... from @angular/*`, the fix is to BUNDLE the framework major: run its official "
        "codemod (`ng update @angular/core@N @angular/cli@N @angular/cdk@N`) which auto-applies migration "
        "schematics, then push the combined change. (needs node >= the new CLI's floor; if the toolchain "
        "is too old to run the codemod, say so and pushed=false.)\n"
        " (b) QUALITY-GATE DROP after a test-runner major (vitest/jest): tests still pass but SonarQube "
        "`coverage X < 80` fails. The runner changed coverage SCOPE (e.g. vitest v4 newly counts bootstrap/"
        "entry files at 0%). Run `npx vitest run --coverage`, find the new 0% bootstrap/runtime-only files, "
        "and add them to `coverage.exclude` (same category as already-excluded entry files like src/index.ts) "
        "— do NOT pad fake tests, and never lower the threshold.\n"
        " (c) LOCKFILE out of sync (`renovate/artifacts` failed): regenerate it (`npm install`) and commit.\n"
        "TEST FAILURES — FIX THE ROOT CAUSE, NEVER THE SCOREBOARD: a failing test is an executable "
        "spec of intended behaviour; green is only a PROXY for correct, so do not game it. When a test "
        "fails, FIRST adjudicate which side is actually wrong — the CODE or the TEST — using the "
        "requirement / PR intent, the acceptance criteria, and the assertion's git blame. If the CODE "
        "violates the intended behaviour, fix the CODE (this is the default assumption). Do NOT weaken, "
        "loosen, delete, skip, `.only`/`xit`, or re-point a test ASSERTION to match buggy code just to "
        "go green — that silently discards the intent and is WORSE than a red that flags the problem "
        "(same principle as coverage above: never lower the bar to pass it). Weakening or removing a "
        "test is a SPEC change, not a fix: only do it when the test genuinely encodes obsolete/incorrect "
        "behaviour, and then say so explicitly in the commit message + report. If you cannot confidently "
        "tell whether the code or the test is the source of truth, DO NOT guess and DO NOT touch the "
        "test — set action=escalate, pushed=false, and hand it to a human with your findings.\n"
        "CLOSE THE LOOP — apply the fix where the failing pipeline will actually RE-TEST it, so the "
        "flow's next Build can go green on its own (do NOT leave the fix in a separate un-merged PR "
        "that the failing build never sees — that is the #1 reason a run gets stuck at human handoff):\n"
        " - If this is a PR / feature-branch build (the job contains 'PR-<n>' or a non-default branch, "
        "e.g. 'esp32-app-pipeline-mb/PR-11' or '.../feat%2Fxxx'): check out THAT branch (the PR head) "
        "and commit + push the minimal fix DIRECTLY to it via git/gh. The pipeline rebuild then picks "
        "it up. If you instead opened a fix PR whose BASE is that same feature branch and its checks "
        "are already green with no conflicts, just merge it (`gh pr merge <n> --squash --delete-branch`) "
        "— same effect. Feature branches are NOT protected; applying the fix there is exactly what a "
        "human reviewer would do.\n"
        " - ONLY if the fix must target main/master (a protected branch): open a PR and STOP — never "
        "merge into main yourself; that stays review-gated.\n"
        "TOOLCHAIN: this container has python/java/rust + the docker CLI but only node v22 and no "
        "go/gradle. When a fix needs a toolchain you lack or a newer version (e.g. `ng update` to "
        "Angular 22 needs node>=24.15, or a go/gradle build), DO NOT give up — build in a disposable "
        "official-image container exactly like CI does: "
        "`docker run --rm -v \"$(pwd)\":/w -w /w node:24 sh -c \"npm ci && npx ng update ... && npm run build\"` "
        "(or golang:1.25, gradle:8-jdk21, etc.). Commit the result from the host. Only set pushed=false "
        "if even a containerised build cannot verify the fix.\n"
        "Verify before you push: run the same build/tests the pipeline runs, locally; only push a change "
        "you can justify. If you cannot build/verify locally, or the cause is infra/host-level or "
        "transient (not code-fixable), set action accordingly and pushed=false. Report which branch you "
        "pushed to and whether the local build passed (set pushed=true only if you actually applied it "
        "to the branch the pipeline will rebuild)."
    )

def prompt_readmesync(p):
    repo = p.get("repo", "")
    return (
        f"You are the README-sync step of the release node. Repo: {repo}. "
        "Using `gh api` only (do NOT clone): fetch README.md and the repo's dependency "
        "manifest(s) — whichever exist of package.json, build.gradle / build.gradle.kts / "
        "gradle/libs.versions.toml, Cargo.toml, go.mod, pyproject.toml / requirements.txt, "
        "*.csproj, idf_component.yml. Compare EVERY version claim in the README (shields.io "
        "badges, tech-stack tables, prose like 'Vite 6.3') against the actual manifest versions; "
        "fix ONLY stale factual version numbers, do not reword anything else.\n"
        "For Android/Gradle repos ALSO sync build-toolchain versions that live OUTSIDE the "
        "dependency manifests (the generic check above misses these): read "
        "gradle/wrapper/gradle-wrapper.properties (distributionUrl -> Gradle major.minor from "
        "'gradle-X.Y.Z-*.zip'), gradle/libs.versions.toml (android-gradle-plugin -> AGP major.minor, "
        "kotlin -> Kotlin), and app/build.gradle.kts (compileSdk, targetSdk, minSdk — exact integers). "
        "Update the matching README claims wherever they appear: the AGP / compileSdk / Gradle shields "
        "badges, any 'Build System' tech-table rows, and Prerequisites prose (e.g. 'Gradle 9.5+', "
        "'compileSdk 37, targetSdk 36'). Badges use major.minor (AGP 9.2, Gradle 9.5); SDK levels are "
        "exact integers. Add NO new badges/rows — only correct numbers in claims that already exist.\n"
        "For HarmonyOS/ArkTS repos the SDK version also lives outside npm/maven manifests: read "
        "build-profile.json5 (compatibleSdkVersion / targetSdkVersion, format like 5.0.0(12) where "
        "12 is the API level), AppScope/app.json5 (minAPIVersion / targetAPIVersion - exact integers), "
        "and oh-package.json5 or hvigor/hvigor-config.json5 (modelVersion = the HarmonyOS NEXT version, "
        "e.g. 5.0.0). Update the matching README claims: the HarmonyOS NEXT X.Y and API NN shields "
        "badges, the SDK Target / SDK Minimum tech-table rows (API 12 (HarmonyOS 5.0.0)), and the "
        "Prerequisites prose (HarmonyOS SDK: API 12 (5.0.0)). Keep the NEXT version and API level "
        "consistent (5.0.0 <-> API 12). Correct numbers only in claims that already exist; add no badges.\n"
        "ALSO sync the dynamic Tests and Coverage shields.io badges to live CI values:\n"
        " - COVERAGE: read the SonarQube projectKey from the repo Jenkinsfile (gh api, "
        "grep -oE 'sonar.projectKey=[^ \"]+', usually <lang>-app), then "
        "curl -s -u \"$SONARQUBE_TOKEN:\" \"$SONAR_HOST_URL/api/measures/component?component=<key>&metricKeys=coverage\" "
        "→ the coverage value; update the Coverage badge (e.g. Coverage-87.5%25-<color>; "
        "color >=80 brightgreen, >=60 yellow, else red).\n"
        " - TESTS: read the latest GREEN main build console "
        "curl -s -u \"$JENKINS_USER:$JENKINS_TOKEN\" \"$JENKINS_URL/job/<job>-app-pipeline-mb/job/main/lastStableBuild/consoleText\" "
        "(derive <job> from the repo: arcana-angular->angular, arcana-cloud-go->go, arcana-cloud-nodejs->node, "
        "arcana-cloud-python->python, arcana-cloud-rust->rust, arcana-cloud-springboot->springboot). Extract the "
        "test runner's total passing count — match whichever appears: 'TOTAL: N SUCCESS' (karma), "
        "'Test Files N passed' / 'Tests N passed' (vitest), 'N passed' (pytest), 'Tests run: N, Failures: 0' "
        "(maven/gradle), or sum the per-package 'ok' lines (go). Update the Tests badge to Tests-<N>%2520passing "
        "(note: a literal space in a shields URL is %2520... actually use %20). "
        "If you cannot determine a number reliably, LEAVE that badge unchanged — never guess.\n"
        "Commit everything (versions + badges) in ONE commit titled 'docs: sync README versions + CI badges' "
        "via gh api PUT (fetch the file sha first). If the README is already accurate, change nothing. "
        "Respond with JSON: updated (bool), changes (list of 'old -> new' strings), reason."
    )

def prompt_merge(p):
    return (
        f"PR {p.get('prUrl')} reported a green verifying build. "
        "Autonomous-merge policy (ALL verified-green PRs, any type — feature, hardening, dep): "
        "verify with `gh pr view` and `gh pr checks` that the PR is OPEN, not a draft, has no "
        "merge conflicts, and EVERY status check listed by `gh pr checks` is green/passing (treat ALL checks as required, not just one). For repos that run multiple pipelines each posting their own context (e.g. arcana-ai-bpm posts `ci/rust` AND `ci/angular`), require every per-pipeline context green; never treat the shared `continuous-integration/jenkins/pr-merge` as authoritative, since whichever pipeline finishes last overwrites it. If so, squash-merge "
        "it: `gh pr merge <url> --squash --delete-branch`. Do NOT merge if ANY check is "
        "pending/failing, the PR is draft/closed/already-merged, or there are conflicts — in those "
        "cases take no action. Return whether you merged and why/why not."
    )

def prompt_sweep(p):
    return (
        "Safety-net sweep of ALL Arcana repos (the periodic maintenance pass that "
        "replaced the old cron daily-run). For each repo, check the latest main-branch "
        "Jenkins build status. List repos whose main is RED. For each RED main, re-trigger "
        "its Jenkins build so the maintenance workflow picks up the resulting build event. "
        "Also note repos with an open Renovate/dep PR that is green but unmerged. Return "
        "counts (checked, retriggered) + the red repo list + a short summary."
    )

def prompt_decide(p):
    return (
        f"A CI auto-remediation flow for job={p.get('job')} finished its "
        f"build/fix loop. Final build result: {p.get('buildResult')}. "
        f"Fix attempts: {p.get('attempts')}. "
        f"Diagnosis: {str(p.get('triage'))[:1500]}. "
        f"Fix outcome: {str(p.get('fix'))[:1500]}.\n"
        "Decide the final outcome. If the build is green (SUCCESS): action=merge, "
        "resolved=true (the failure cleared / the fix worked). If retries were "
        "exhausted without green, or the cause was infra / transient / not "
        "code-fixable: action=escalate, resolved=false. Give a concise reason a "
        "human reviewer can act on."
    )

def prompt_analyze(p):
    return (
        "You are the CI infrastructure health analyst for a self-hosted CI fleet "
        "(Jenkins + Docker + Nexus on one host). Below is a JSON scan: disk usage%, "
        "Jenkins health (busy executors, offline nodes), and the last result line "
        "from each host maintenance cron (ci-disk-gc, ci-watchdog, nexus-blob-maint).\n\n"
        f"Scan: {str(p.get('scan'))[:3000]}\n\n"
        "Assess overall health. Is anything trending wrong or anomalous? Is the host "
        "cron keeping disk under control or losing to a build storm? Are offline "
        "Jenkins nodes a transient blip or a real problem? Pick a severity and give a "
        "concise recommendation: what (if anything) a HUMAN should do, vs leave to the "
        "host cron self-healing. BEFORE you judge, you may vsearch/csearch the archive "
        "for past disk/Jenkins incidents to spot a recurring pattern."
    )


def prompt_escalate(p):
    job = p.get("job", "")
    return (
        f"You are the AUTONOMOUS ESCALATION node of a self-maintaining CI flow. The build/fix "
        f"loop for job={job} did NOT reach green. buildResult={p.get('buildResult')}, "
        f"fix attempts={p.get('attempts')}, escalation retryCount so far={p.get('retryCount')}.\n"
        f"Diagnosis: {str(p.get('triage'))[:1500]}\n"
        f"Fix outcome: {str(p.get('fix'))[:1200]}\n"
        f"Decision: {str(p.get('decision'))[:800]}\n"
        "THIS FLOW HAS NO HUMAN FALLBACK — the park-for-human step was removed. You MUST drive this "
        "instance to a clean terminal yourself. Pick exactly ONE resolution and EXECUTE its action "
        "before returning.\n"
        "STEP 1 — READ THE REAL EVIDENCE; do NOT trust the diagnosis blindly (it has been wrong "
        "before: a flaky testcontainers startup was misdiagnosed as a JDK/toolchain bug and a PR was "
        "parked three times). Fetch the actual build log and read the genuine failure tail: "
        f"curl -s -u \"$JENKINS_USER:$JENKINS_TOKEN\" \"{p.get('buildUrl','')}consoleText\" "
        "(append 'consoleText' to buildUrl).\n"
        "STEP 2 — CROSS-SIGNAL via the shared archive (decisive): `vsearch '<failure concept>' aaf` "
        "and `csearch '\"<exact error>\"' aaf` for how this class of failure resolved before, AND "
        "check whether main is currently green and whether sibling PRs pass. If main/siblings are "
        "green and only this build trips on an unstable symptom (testcontainers/container startup, "
        "timeout / exit 124, network, registry, OOM), it is FLAKY/INFRA — NOT this PR's code.\n"
        "STEP 3 — CHOOSE & EXECUTE (MVP policy):\n"
        " (A) FLAKY / transient / infra (cross-signal says it is not this PR's fault) AND retryCount "
        "< 3 -> resolution='retry'. Change NO code; the flow waits, then re-runs the build "
        "automatically. (At retryCount>=3 the flow force-terminates regardless, so if you would retry "
        "but the cap is hit, fall through to the matching unfixable branch below.)\n"
        " (B) PR-context and genuinely unfixable after 3 fix attempts (a renovate dependency major "
        "that cannot land — peer-locked / upstream-broken — or PR code the author must redo): CLOSE "
        "the PR with an explanatory comment. Derive repo+number from the job (e.g. "
        "'arcana-cloud-springboot-app-pipeline-mb/PR-32' -> repo arcana-cloud-springboot, PR 32), then "
        "`gh pr comment <n> --repo jrjohn/<repo> --body '<why it cannot land, what was tried, that "
        "renovate will re-propose / the author can reopen>'` followed by `gh pr close <n> --repo "
        "jrjohn/<repo>`. -> resolution='closed'.\n"
        " (C) main/master broken and not auto-fixable (fixes + retries exhausted): DO NOT revert or "
        "push to main (MVP boundary — main stays human-reviewed). Instead RECORD LOUDLY: make your "
        "reason a clear one-paragraph incident note (job, real root cause from the log, what was "
        "tried, why a human is needed). It is already captured to the console + archive + dashboard "
        "for asynchronous human review. -> resolution='recorded'.\n"
        " (D) If you find the build is actually GREEN now -> resolution='merged' (let the success path "
        "proceed).\n"
        "Return resolution (one of retry|closed|recorded|merged), the action you executed, and a "
        "concise reason. NEVER leave the instance without a resolution — 'recorded' is the safe "
        "default if you cannot act."
    )


def prompt_scan_stale(p):
    return (
        "You are the SCAN node of the unstick scheduler. Find stale-base PRs and start ONE "
        "unstick-flow remediation per PR. A PR is 'stale-base stuck' when its CI is red ONLY because "
        "its base moved (main advanced past it) — it will never go green on its own.\n"
        "STEP 1 — list open PRs (start with jrjohn/arcana-ai-bpm): "
        "`gh pr list --repo jrjohn/arcana-ai-bpm --state open --json number,url,headRefName,mergeStateStatus,isDraft`.\n"
        "STEP 2 — for each NON-draft PR, classify as STALE-STUCK only if mergeStateStatus is BEHIND or "
        "UNSTABLE/DIRTY AND `gh pr checks <url>` shows a failing check AND the PR is behind main (its "
        "base moved since the failing build ran). SKIP PRs that are green, draft, or red for a genuine "
        "code reason (not base-staleness).\n"
        "STEP 3 — for each stale-stuck PR, START a remediation flow by POSTing to the engine:\n"
        "`curl -s -X POST http://aaf-kogito-bpmn:8080/unstick-flow -H 'Content-Type: application/json' "
        "-d '{\"prUrl\":\"<url>\",\"subject\":\"unstick <repo>#<num>\"}'`. ONE per PR — do not start a "
        "second unstick-flow for a PR that already has an active one; when in doubt, skip rather than "
        "duplicate.\n"
        "Return started (how many unstick-flow instances you started) and a reason listing the PRs."
    )


def prompt_rebase(p):
    pr = p.get("prUrl", "")
    return (
        f"You are the EXECUTOR (NOT the auditor) for unstucking a stale-base PR: {pr}. Do the rebase "
        "and re-run CI, then STOP. You have NO merge authority — never merge.\n"
        f"STEP 1 — `gh pr view {pr} --json headRefName,baseRefName,headRepositoryOwner,headRepository,url` "
        "to learn the branch + base + repo. Clone/cd that repo, `git fetch origin`.\n"
        "STEP 2 — SAFETY: compare the PR head with origin/<headRef>. If they diverged (someone pushed "
        "since the PR's last build), do NOT force-push — return rebased=false, ciStatus='diverged', "
        "stop. This protects an author's unpushed/just-pushed work.\n"
        "STEP 3 — `git rebase origin/<base>` (origin/main). Resolve only mechanical/trivial conflicts; "
        "on any real conflict return rebased=false, ciStatus='conflict', stop.\n"
        "STEP 4 — push with `git push --force-with-lease` (NEVER plain --force).\n"
        f"STEP 5 — wait for the re-triggered CI to settle: poll `gh pr checks {pr}` until no check is "
        "pending (give it up to ~20 min).\n"
        "Return rebased (bool), ciStatus ('green' if every check passed, 'red' if any failed, 'pending' "
        "if still running at timeout, else 'diverged'/'conflict'), and a short reason. An INDEPENDENT "
        "auditor will re-verify everything — report facts honestly."
    )


def prompt_audit(p):
    pr = p.get("prUrl", "")
    claim = str(p.get("rebaseResult", ""))[:500]
    return (
        f"You are an INDEPENDENT AUDITOR of a rebased PR: {pr}. The executor reported: \"{claim}\". "
        "DO NOT trust that claim — verify everything yourself from scratch. You are the judge; the "
        "executor's word means nothing.\n"
        f"CHECK 1 — `gh pr view {pr} --json state,isDraft,mergeable,mergeStateStatus`: must be OPEN, "
        "not draft, mergeable=MERGEABLE, mergeStateStatus CLEAN or UNSTABLE (not DIRTY/BEHIND/BLOCKED).\n"
        f"CHECK 2 — `gh pr checks {pr}`: EVERY per-pipeline status context must be green. For "
        "arcana-ai-bpm that means BOTH `ci/rust` AND `ci/angular`. Do NOT rely on the shared "
        "`continuous-integration/jenkins/pr-merge` (whichever pipeline finishes last overwrites it). "
        "If any required check is still pending -> PENDING. If any is genuinely failing -> REJECTED.\n"
        f"CHECK 3 — rebase cleanliness: `gh pr diff {pr}` must contain ONLY the PR's intended logical "
        "change, nothing extra dragged in by the rebase. If the diff grew unexpected content -> REJECTED.\n"
        "Return decision = APPROVED (all three pass) | PENDING (checks still running) | REJECTED (any "
        "check red, not mergeable, or unclean rebase), plus a concise reason citing what you actually "
        "observed — not what the executor claimed."
    )


# --- C (generalization): per-app Project Profile — how to build/run/review THIS app. Read from the
# target repo's `.arcana/project.json` at the base ref, merged over the dashboard defaults, so the
# journey-walkthrough + IA gates work on OTHER apps (a repo drops its own profile: different appDir/
# buildCmd/auth/navPath). Absent profile → dashboard defaults (aaf's own values) → zero regression. ---
_PROFILE_DEFAULTS = {
    "app": {"appDir": "dashboard", "buildCmd": "npm run build", "distGlob": "dist"},
    "run": {"previewPort": 8087, "apiTarget": "http://aaf-arcana-cloud-rust:8080"},
    "auth": {"user": "boss", "pass": "pw", "usernameSelector": "#login-username",
             "passwordSelector": "#login-password",
             # RBAC UI gate: needs >=2 personas with DIFFERENT permissions, because every
             # assertion it makes is about the DIFFERENCE between them (an admin alone
             # proves nothing about what a plain employee is offered). Empty disables it.
             "rbacActors": "boss:pw,lin:pw,wang:pw",
             # scenario-walk casts by ROLE, because a business chain is about handing state
             # between identities. Empty disables it.
             "scenarioActors": '{"employee":"wang:pw","manager":"lin:pw","admin":"boss:pw"}'},
    "nav": {"navPath": "dashboard/src/app/core/navigation/nav.config.ts",
            "routesPath": "dashboard/src/app/app.routes.ts"},
    "personas": ["簽核者", "申請人", "管理員"],
    "qualityBar": {"coverage": 80, "archQube": 90},
}


def _load_profile(payload):
    """The target repo's `.arcana/project.json` at the base ref (run-recipe + nav paths + personas),
    merged over the dashboard defaults. Best-effort + cached on the payload. The single seam another
    app plugs into; absent → dashboard defaults (aaf unaffected)."""
    if "_profile" in payload:
        return payload["_profile"]
    import copy
    prof = copy.deepcopy(_PROFILE_DEFAULTS)
    repo = payload.get("repo") or ""
    base = payload.get("base") or "main"
    if repo:
        try:
            r = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/.arcana/project.json?ref={base}", "--jq", ".content"],
                capture_output=True, text=True, timeout=25)
            raw = "".join((r.stdout or "").split())
            if raw:
                loaded = json.loads(base64.b64decode(raw).decode("utf-8", "replace"))
                for k, v in loaded.items():
                    if isinstance(v, dict) and isinstance(prof.get(k), dict):
                        prof[k].update(v)
                    elif not k.startswith("$"):
                        prof[k] = v
        except Exception:
            pass
    payload["_profile"] = prof
    return prof


def _fetch_app_map(payload):
    """B (IA-redundancy critic): fetch the app's WHOLE navigation map (all existing top-level
    features + routes) at the BASE ref, so the PM can judge redundancy against EVERY existing
    feature — not just this initiative's `siblings`. This is what catches "a new 流程追蹤 view when
    流程監控 already lists those instances". Best-effort (empty on failure so the PM degrades to the
    siblings-only check). Paths default to the dashboard nav/routes; a per-app Project Profile can
    override navPath/routesPath (the generalization seam). Returns a compact string."""
    repo = payload.get("repo") or ""
    base = payload.get("base") or "main"
    if not repo:
        return ""
    nav = _load_profile(payload).get("nav", {})
    paths = [nav.get("navPath") or "dashboard/src/app/core/navigation/nav.config.ts",
             nav.get("routesPath") or "dashboard/src/app/app.routes.ts"]
    out = []
    for pth in paths:
        try:
            r = subprocess.run(["gh", "api", f"repos/{repo}/contents/{pth}?ref={base}", "--jq", ".content"],
                               capture_output=True, text=True, timeout=30)
            raw = "".join((r.stdout or "").split())
            content = base64.b64decode(raw).decode("utf-8", "replace") if raw else ""
            if content:
                out.append(f"# {pth}\n{content[:3500]}")
        except Exception:
            pass
    return "\n\n".join(out)[:7000]


def prompt_pm_review(p):
    return (
        "You are the PM readiness gate (your PM skill carries the full rubric). A gated PR was "
        "produced by the SA -> SD -> (UI/UX) -> Implement pipeline. Decide whether it satisfies the "
        "manager's requirement and is READY to ship, or must iterate.\n"
        f"PR: {p.get('prUrl')}  (subject: {p.get('job') or p.get('subject')})\n"
        f"Inspect the ACTUAL change first: `gh pr diff {p.get('prUrl') or ''}` and `gh pr view "
        f"{p.get('prUrl') or ''}`. Judge against the evidence, do not trust summaries.\n"
        f"- SRS (acceptance criteria to trace): {str(p.get('srs'))[:4000]}\n"
        f"- SDD (design to conform to): {str(p.get('sdd'))[:3000]}\n"
        f"- UI/UX spec (usability target, if user-facing): {str(p.get('uiuxSpec'))[:3000]}\n"
        f"- SIBLING features in this SAME initiative (each with its verdict/state — cross-check against "
        f"these, like a countersigner reading prior sign-offs): {str(p.get('siblings'))[:2800]}\n"
        f"- APP NAVIGATION MAP — ALL existing top-level features + routes at base `{p.get('base') or 'main'}` "
        f"(to judge IA redundancy against the WHOLE app, not just siblings): "
        f"{_fetch_app_map(p) or '(unavailable — degrade to the siblings check)'}\n"
        f"- TEST NODE RESULT (the platform's OWN CI — it built THIS exact PR and ran feature testcases + the "
        f"AI semantic gate + a GOAL-DIRECTED JOURNEY WALKTHROUGH on it): {str(p.get('testReport'))[:2800]}\n"
        "HARD PRE-GATE first: (a) BUILD — the implement result's `buildStatus` (also printed as `Local build "
        "gate:` in the PR body) is DETERMINISTIC: `OK` means the code compiled via `npm ci && npm run build`, so "
        "it BUILDS — treat that as ground truth and NEVER read the implement Summary's prose as a build failure "
        "(the Summary is unreliable LLM self-narration; buildStatus/Local-build-gate is the fact). `RED:` = it "
        "genuinely will not compile -> NOGO. (b) TESTS/QUALITY — the TEST NODE above already ran this exact PR "
        "build through the platform's own CI; its `testReport` is your PRIMARY quality evidence: allPass=false or "
        "a non-empty failures[] -> NOGO(quality) naming the failing testcases; aiFindings with severity=fail -> "
        "NOGO citing them. **journeyFindings with kind=journey-blocked -> NOGO, HIGHEST PRIORITY**: a BLOCKED "
        "journey means a real user CANNOT COMPLETE the core task — the feature RENDERS but the action is "
        "unreachable (rendered != actionable, e.g. 'as 簽核者 cannot reach 核准 — the row opened a read-only "
        "view'); this is the class the diff/screenshot review misses, NOGO naming the blocked journey + reason "
        "so Implement wires the missing path. A separate green CI check-rollup / SonarQube is CONFIRMATORY but NOT required — do NOT "
        "HOLD merely because SONARQUBE_TOKEN / CI env is unset when the testReport is present. arch-qube>=90 "
        "still applies where it is checkable. Bars unmet -> NOGO(quality).\n"
        "Then the FIVE dimensions: (1) usability - audit the built UI in the diff against the UX rubric; you "
        "CAN catch objective violations (equal-weight N-quadrant dumps, non-collapsible toolbars, no "
        "progressive disclosure, cognitive overload, off-scan-path primary actions, tiny targets, WCAG/state "
        "gaps) -> NOGO with the fix; ONLY genuinely subjective/brand calls -> HOLD. (2) completeness - every "
        "SRS AC-N traceable to code + a test in the diff; list missing ACs. (3) design conformance - matches "
        "SDD layers/approach + arch-qube. (4) schedule - not stuck. (5) goal-fit - actually solves the "
        "requirement / advances the manager's goal, not a hollow shell.\n"
        "(6) cross-feature (only if `siblings` non-empty) - like a countersigner reading prior sign-offs: "
        "does this feature OVERLAP/duplicate a sibling? is it CONSISTENT with siblings (naming, UX pattern, "
        "API shape)? are its DEPENDENCIES satisfied - a sibling this needs must be COMPLETED with verdict GO; "
        "if a needed sibling is not yet GO, return NOGO/HOLD and name which sibling to wait for. do the "
        "features TOGETHER cover the goal (flag gaps)?\n"
        "(7) IA COHERENCE / whole-app redundancy - using the APP NAVIGATION MAP above (ALL existing "
        "features, NOT just siblings): does this feature DUPLICATE or substantially OVERLAP an existing "
        "one — a new list/view showing the same data a menu item already shows (e.g. a '追蹤/tracking' "
        "page when a '監控/monitoring' page already lists those instances), or a redundant nav item / "
        "two menu entries doing the same job / an IA that will confuse users about where to go? "
        "Distinguish a genuinely-NEW capability from a redundant RE-SLICE of existing data. If redundant "
        "-> NOGO proposing to MERGE into the existing surface (or file a consolidation backlog item), "
        "rather than shipping a parallel duplicate view. (Only flag real overlap — a new capability that "
        "merely lives near an existing one is fine.)\n"
        "OUT-OF-SCOPE FINDINGS: a gate/test finding NOT in this feature's scope must not block/HOLD "
        "this PR and must NOT be dropped either — you own the product backlog: convert each real one "
        "into a `backlog` item (feature_request one concrete sentence + slug + uiFacing + priority), "
        "deduped against siblings. HOLD is only for THIS feature's own human-decision gaps.\n"
        "ANTI-GOODHART (non-negotiable): never lower/soften an AC, design, or UX bar to reach GO; no dimension "
        "passes without cited evidence; if the SAME gap survived the previous round -> HOLD (do not churn).\n"
        f"Previous round verdict (no-progress detection): {str(p.get('pmReview'))[:1500]}\n"
        f"Iteration (pmAttempts): {p.get('pmAttempts')}\n"
        "Return the verdict JSON (verdict GO|NOGO|HOLD, per-dimension pass+note citing evidence, and if NOGO "
        "a concrete actionable `feedback` naming the exact gap + fix so Implement resolves it in ONE pass)."
    )


PROMPTS = {"diagnose": prompt_diagnose, "fix": prompt_fix, "merge": prompt_merge, "sweep": prompt_sweep, "decide": prompt_decide, "analyze": prompt_analyze, "readmesync": prompt_readmesync, "escalate": prompt_escalate, "scan-stale": prompt_scan_stale, "rebase": prompt_rebase, "audit": prompt_audit, "pm-review": prompt_pm_review}


def _resume(payload):
    """Resume an existing Claude session if the worker threaded a `sid` back in.

    This is what gives the agent CONTINUITY across the flow: diagnose opens a
    session, fix resumes it (so it already has the diagnosis reasoning in
    context), each fix retry resumes the same session (so attempt N remembers
    what attempt N-1 already tried instead of starting amnesiac), and decide
    resumes it (so it judges with the full trail). It is also the SAME session a
    human re-attaches to via `docker exec -it agent-task-node claude --resume
    <sid>` when a run parks for handoff. Empty list = fresh (still-persisted)
    session.
    """
    sid = payload.get("sid") or payload.get("_sid")
    return ["--resume", str(sid)] if sid else []


def _skill_flags(payload):
    """Real skill binding, 1–5 skills per node (John, 2026-07-18): `ai_skill` is a
    comma-separated list of skill names; each resolved skill's SKILL.md is injected
    as an appended system prompt (in listed order — put the ROLE skill first, support
    skills after) and its dir exposed so referenced files resolve. More than 5 →
    only the first 5 load (logged), keeping the context cost bounded.

    Path-guarded per name: safe slug AND realpath containment inside `SKILLS_DIR`;
    unknown/missing names are skipped (never fails the task — the node still runs on
    its `ai_prompt` alone). Empty list = no skill (design-time validation is where
    "an AI node MUST pick ≥1 skill" is enforced; runtime stays permissive so legacy
    flows keep running)."""
    raw = (payload.get("ai_skill") or "").strip()
    if not raw:
        return []
    skills_dir = os.environ.get("SKILLS_DIR", "")
    if not skills_dir:
        return []
    root = os.path.realpath(skills_dir)
    names = [n.strip() for n in raw.split(",") if n.strip()]
    if len(names) > 5:
        print("[agent-task-node] ai_skill lists %d skills; loading first 5" % len(names), flush=True)
        names = names[:5]
    parts, dirs = [], []
    for name in names:
        if not re.match(r"^[a-z][a-z0-9._-]+$", name):
            continue
        skill_dir = os.path.realpath(os.path.join(root, name))
        if skill_dir != root and not skill_dir.startswith(root + os.sep):
            continue  # containment guard against traversal
        md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(md):
            continue
        try:
            parts.append("# ===== SKILL: %s =====\n\n" % name + open(md, encoding="utf-8").read())
            dirs.append(skill_dir)
        except Exception:
            continue
    if not parts:
        return []
    # Concatenate into ONE appended system-prompt file — repeated
    # --append-system-prompt-file flags have unspecified CLI semantics, a single
    # merged file is deterministic. Listed order = precedence order.
    merged = os.path.join(tempfile.gettempdir(), "skills-%s.md" % hashlib.sha256(
        ",".join(names).encode()).hexdigest()[:12])
    # Atomic publish: concurrent tasks with the same skill set share this path, and a
    # plain truncate-write could hand a parallel `claude` process a half-written file.
    # Write to a unique sibling then os.replace() — readers see old or new, never torn.
    tmp = merged + ".%d.tmp" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts))
    os.replace(tmp, merged)
    flags = ["--append-system-prompt-file", merged]
    for d in dirs:
        flags += ["--add-dir", d]
    # Isolation (anti-pollution): ONLY the contract-listed skills are force-injected.
    # Disable the Skill tool so the agent cannot auto-discover the other ~50 mounted
    # skills — the node uses its listed set and only that set.
    return flags + ["--disallowedTools", "Skill"]


def _perm_flags(payload):
    """Opt-in `--dangerously-skip-permissions`, ONLY when the caller sets
    `skip_permissions` (the `implement` verb does). Safe there because the code is
    written inside an isolated container on a throwaway clone and the PR is opened
    by a deterministic finalizer downstream — bounded blast radius — and it avoids
    the mounted claude-home allow-list gap that blocks git/gh in default mode."""
    return ["--dangerously-skip-permissions"] if payload.get("skip_permissions") else []


def _dir_flags(payload):
    """Extra working dirs Claude may read/write (`add_dirs`), e.g. the implement
    verb's cloned repo workdir. Each becomes an `--add-dir <path>`."""
    out = []
    for d in payload.get("add_dirs") or []:
        if isinstance(d, str) and d:
            out += ["--add-dir", d]
    return out


WORK_ROOT = os.environ.get("WORK_ROOT", "/work")


def _safe_seg(v):
    """Filesystem-safe path segment from a piid/node value."""
    return "".join(c for c in str(v) if c.isalnum() or c in "-_") or "x"


def _workspace(payload):
    """Per-(instance, node) working dir: $WORK_ROOT/<piid>/<node>/. Gives every node of
    every process instance its own cwd, so concurrent flows — including multiple instances
    of the SAME flow (fan-out children) — never share a working directory or clobber files."""
    piid, node = payload.get("_piid"), payload.get("_node")
    if not piid or not node:
        return None
    ws = os.path.join(WORK_ROOT, _safe_seg(piid), _safe_seg(node))
    try:
        os.makedirs(ws, exist_ok=True)
        return ws
    except OSError:
        return None


def _instance_claude_config(piid):
    """Per-instance isolated Claude config dir ($WORK_ROOT/<piid>/.claude), seeded once from
    the mounted /root/.claude auth. Concurrent instances then keep their own session state
    (.claude.json) instead of contending on one shared ~/.claude (and never write back to
    the host mount). Returns the dir for CLAUDE_CONFIG_DIR, or None to fall back to default."""
    if not piid:
        return None
    cfg = os.path.join(WORK_ROOT, _safe_seg(piid), ".claude")
    try:
        creds = os.path.join(cfg, ".credentials.json")
        if not os.path.exists(creds):
            os.makedirs(cfg, exist_ok=True)
            if os.path.exists("/root/.claude/.credentials.json"):
                shutil.copy("/root/.claude/.credentials.json", creds)
            dst_json = os.path.join(cfg, ".claude.json")
            if os.path.exists("/root/.claude.json"):
                shutil.copy("/root/.claude.json", dst_json)
            else:
                with open(dst_json, "w") as f:
                    f.write("{}")
        return cfg
    except OSError:
        return None


class RateLimitError(RuntimeError):
    """Claude hit a rate/usage limit (HTTP 429/529 or 'Overloaded'). Distinct from other
    failures so the worker can back off + NOT count it toward an instance's retry budget."""


_RATE_RE = re.compile(r"rate.?limit|overloaded|usage limit|too many requests|\b429\b|\b529\b", re.I)


def _rate_limited(status, text):
    """True if an HTTP status / claude error text signals a rate or usage limit."""
    try:
        if int(status) in (429, 529):
            return True
    except (TypeError, ValueError):
        pass
    return bool(text and _RATE_RE.search(str(text)))


def _invoke_claude(prompt, schema, payload, wall, cwd=None):
    """Core Claude invocation shared by the static-verb path (run_claude) and the
    control-inverted generic executor (run_claude_generic). `prompt` + `schema`
    (a JSON string) are already resolved; `wall` is the wall-clock kill in seconds.
    Returns the validated structured_output with `_usage`/`_sid` attached."""
    # Live console: if the worker passed _piid/_node and CONSOLE_DIR is set,
    # stream the Claude conversation (stream-json) line-by-line to a shared log
    # so the dashboard shows it like a Jenkins console; else plain json mode.
    # The stream-json `result` event still carries structured_output + usage.
    console_dir = os.environ.get("CONSOLE_DIR", "")
    piid, node = payload.get("_piid"), payload.get("_node")
    console_path = None
    if console_dir and piid and node:
        keep = lambda v: "".join(c for c in str(v) if c.isalnum() or c in "-_")
        try:
            os.makedirs(console_dir, exist_ok=True)
            console_path = os.path.join(console_dir, keep(piid) + "__" + keep(node) + ".jsonl")
        except OSError:
            console_path = None
    # Claude refuses --dangerously-skip-permissions as root unless it believes it's
    # in a sandbox. The agent-task-node container IS an isolated sandbox, so signal
    # it via IS_SANDBOX=1 (only for skip-permissions runs; others inherit env).
    # Per-instance / per-node isolation: own cwd + own Claude config dir, so concurrent
    # flows (incl. many instances of the same flow) never share a working dir or session
    # state. Falls back to the shared default when _piid/_node are absent (direct calls).
    ws = _workspace(payload)
    if ws and cwd is None:
        cwd = ws
    run_env = dict(os.environ)
    cfg_dir = _instance_claude_config(payload.get("_piid"))
    if cfg_dir:
        run_env["CLAUDE_CONFIG_DIR"] = cfg_dir
    if payload.get("skip_permissions"):
        run_env["IS_SANDBOX"] = "1"
    if console_path:
        cmd = [CLAUDE, "-p", prompt, "--json-schema", schema,
               "--output-format", "stream-json", "--verbose"] + _resume(payload) + _skill_flags(payload) + _perm_flags(payload) + _dir_flags(payload)
        if MODEL:
            cmd += ["--model", MODEL]
        collected = []
        # Retries of the same node reuse the SAME <piid>__<node>.jsonl path; opening "w"
        # would clobber the FAILED attempt we most need to debug (a timed-out implement
        # leaves no trace otherwise). Archive a non-empty prior attempt to a timestamped
        # sibling first — the live path stays clean for the current attempt, history kept.
        try:
            if os.path.exists(console_path) and os.path.getsize(console_path) > 0:
                os.replace(console_path, "%s.%d.jsonl" % (console_path[:-6], int(time.time())))
        except OSError:
            pass
        with open(console_path, "w") as cf:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, cwd=cwd, env=run_env)
            # wall-clock kill: without it an abandoned run streams forever (a Fix
            # orphan ran 8h17m on 2026-06-04). fix gets 30 min for local build
            # verification; everything else the standard TIMEOUT.
            import threading as _th
            _wall = wall
            _killer = _th.Timer(_wall, proc.kill)
            _killer.daemon = True
            _killer.start()
            try:
                for line in proc.stdout:
                    cf.write(line)
                    cf.flush()
                    collected.append(line)
                proc.wait(timeout=TIMEOUT)
            finally:
                _killer.cancel()
        if proc.returncode != 0:
            err = proc.stderr.read()[:500] if proc.stderr else ""
            if _rate_limited(None, err):
                raise RateLimitError(f"claude rate-limited (exit {proc.returncode}): {err}")
            raise RuntimeError(f"claude exit {proc.returncode}: {err}")
        env = {}
        for line in collected:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                env = ev
    else:
        cmd = [CLAUDE, "-p", prompt, "--json-schema", schema,
               "--output-format", "json"] + _resume(payload) + _skill_flags(payload) + _perm_flags(payload) + _dir_flags(payload)
        if MODEL:
            cmd += ["--model", MODEL]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=wall, cwd=cwd, env=run_env)
        if proc.returncode != 0:
            if _rate_limited(None, proc.stderr):
                raise RateLimitError(f"claude rate-limited (exit {proc.returncode}): {proc.stderr[:500]}")
            raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr[:500]}")
        env = json.loads(proc.stdout.strip())
    if env.get("is_error") or env.get("api_error_status"):
        _aerr = env.get("api_error_status")
        _amsg = str(env.get("result", ""))[:300]
        if _rate_limited(_aerr, _amsg) or _rate_limited(_aerr, str(_aerr)):
            raise RateLimitError(f"claude api rate-limited: {_aerr or _amsg}")
        raise RuntimeError(f"claude api error: {_aerr or _amsg}")
    so = env.get("structured_output")
    if so is None:
        raise RuntimeError(f"no structured_output in claude result: {str(env)[:300]}")
    if isinstance(so, dict):
        usage = env.get("usage") or {}
        mu = env.get("modelUsage") or {}
        model = next(iter(mu), None) or env.get("model")
        so["_usage"] = {
            "model": model,
            "input": int((usage.get("input_tokens") or 0)
                         + (usage.get("cache_read_input_tokens") or 0)
                         + (usage.get("cache_creation_input_tokens") or 0)),
            "output": int(usage.get("output_tokens") or 0),
        }
        # Hand the session id back so the worker can persist it on the process
        # instance (var `sid`) and thread it into the next AI task — continuity +
        # the handle a human resumes for handoff.
        sid = env.get("session_id")
        if sid:
            so["_sid"] = sid
    return so


# --- Phase 1B: osearch memory pre-fetch ---------------------------------------
# Before invoking Claude, pull semantically-relevant organizational memory from the
# team archive (crs pgsearch --vec: bge-m3 query embed + HNSW over archive_main.msg)
# and inject it, provenance-tagged, ahead of the task prompt. Best-effort: a miss or
# timeout NEVER fails the task. Connection reuses the same ARCHIVE_PG the worker uses;
# CRS_PG_HOST defaults to the cert CN (arcana.boo, a devops_default alias) so crs's
# TLS verification passes, and CRS_OLLAMA_URL points at the in-cluster ollama.
PREFETCH = os.environ.get("MEMORY_PREFETCH", "1") != "0"
CRS_BIN = os.environ.get("CRS_BIN", "/root/bin/crs")
PREFETCH_LIMIT = int(os.environ.get("MEMORY_PREFETCH_LIMIT", "4"))
# 15s tolerates a cold Ollama (first bge-m3 embed loads the model into VRAM); warm
# queries are ~0.8-2.8s. A single cold start must not knock out memory recall.
PREFETCH_TIMEOUT = int(os.environ.get("MEMORY_PREFETCH_TIMEOUT", "15"))
_PROJ_PREFIX = "-Users-jrjohn-Documents-projects-"


def _crs_pg_env():
    url = os.environ.get("ARCHIVE_PG", "")
    m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)", url)
    if not m:
        return None
    user, pw, _host, _port, db = m.groups()
    e = dict(os.environ)
    e.update({
        "CRS_PG_HOST": os.environ.get("CRS_PG_HOST", "arcana.boo"),
        "CRS_PG_PORT": os.environ.get("CRS_PG_PORT", "5432"),
        "CRS_PG_USER": user, "CRS_PG_PASSWORD": pw, "CRS_PG_DB": db,
        "CRS_OLLAMA_URL": os.environ.get("CRS_OLLAMA_URL", "http://ollama:11434/api/embed"),
    })
    return e


def _mem_query(payload):
    src = dict(payload)
    src.update(payload.get("data") or {})
    parts = [str(src[k]) for k in ("prompt", "job", "cause", "subject",
                                   "buildResult", "prUrl", "ai_input") if src.get(k)]
    return " ".join(parts)[:400]


# Circuit breaker: trip only after PREFETCH_FAIL_THRESHOLD *consecutive* failures
# (a genuine archive outage), so a lone cold-start timeout doesn't knock out recall.
# Once tripped, prefetch is skipped for PREFETCH_COOLDOWN s. Any success resets it.
_PREFETCH_COOLDOWN_UNTIL = 0.0
_PREFETCH_FAILS = 0
PREFETCH_COOLDOWN = int(os.environ.get("MEMORY_PREFETCH_COOLDOWN", "300"))
PREFETCH_FAIL_THRESHOLD = int(os.environ.get("MEMORY_PREFETCH_FAIL_THRESHOLD", "3"))


def fetch_memory(query):
    """Semantic archive recall (Phase 1B). Returns a provenance-tagged context block
    or '' — never raises. Tagged stale-aware so the agent verifies before acting."""
    global _PREFETCH_COOLDOWN_UNTIL, _PREFETCH_FAILS
    if not PREFETCH or not (query or "").strip():
        return ""
    now = time.time()
    if now < _PREFETCH_COOLDOWN_UNTIL:
        return ""
    env = _crs_pg_env()
    if not env:
        return ""
    try:
        p = subprocess.run([CRS_BIN, "pgsearch", "--vec", "--limit", str(PREFETCH_LIMIT),
                            "--json", query], capture_output=True, text=True,
                           timeout=PREFETCH_TIMEOUT, env=env)
        rows = (json.loads(p.stdout).get("results", [])
                if p.returncode == 0 and p.stdout.strip() else [])
    except Exception:
        _PREFETCH_FAILS += 1
        if _PREFETCH_FAILS >= PREFETCH_FAIL_THRESHOLD:
            _PREFETCH_COOLDOWN_UNTIL = now + PREFETCH_COOLDOWN
            _PREFETCH_FAILS = 0
        return ""
    _PREFETCH_FAILS = 0  # success resets the consecutive-failure counter
    lines = []
    for r in rows:
        proj = (r.get("project") or "").replace(_PROJ_PREFIX, "").strip("-") or "?"
        ts = (r.get("ts") or "")[:16]
        sid = (r.get("session_id") or "")[:8]
        content = " ".join((r.get("content") or "").split())[:280]
        if content:
            lines.append(f"- [{proj}|{ts}|{sid}] {content}")
    if not lines:
        return ""
    return ("## Relevant history (team archive — semantic recall; may be stale, "
            "verify before acting)\n" + "\n".join(lines) + "\n")


def _with_memory(prompt, payload):
    mem = fetch_memory(_mem_query(payload))
    return (mem + "\n" + prompt) if mem else prompt


def run_claude(task, payload):
    """Static-verb path: prompt + schema come from the in-code PROMPTS/SCHEMAS
    registries keyed by the CI verb (diagnose/fix/merge/...)."""
    if STUB:
        return STUB_RESPONSES[task]
    schema = json.dumps(SCHEMAS[task])
    prompt = _with_memory(PROMPTS[task](payload), payload)
    wall = 1800 if task in ("fix", "pm-review") else TIMEOUT
    return _invoke_claude(prompt, schema, payload, wall)


# --- Generic executor (Phase 1A, REQ-AIEXEC-002) -------------------------------
# Control inversion: the task definition is no longer in code. The BPMN flow passes
# `ai_prompt` (instruction) + `ai_output_schema` (the result contract) as process
# variables; the worker forwards them here as payload `prompt` / `output_schema`,
# plus the full process `data`. A new business domain needs NO new platform code.
_GENERIC_DROP = {"ai_prompt", "ai_output_schema", "ai_skill", "sid", "_sid", "_piid", "_node",
                 "prompt", "output_schema", "data"}


def _generic_schema(payload):
    sch = payload.get("output_schema")
    if isinstance(sch, str):
        sch = json.loads(sch) if sch.strip() else None
    if not sch:
        # Always hand claude --json-schema a schema; default = free-form envelope.
        sch = {"type": "object", "properties": {"result": {"type": "string"}},
               "required": ["result"], "additionalProperties": True}
    return sch


def prompt_generic(payload):
    instruction = payload.get("prompt") or ""
    data = dict(payload.get("data") or {})
    # ai_input carries arbitrary business data as a JSON string, so a flow stays
    # domain-agnostic (the generic 3-variable contract: ai_prompt + ai_output_schema
    # + ai_input). Parse + merge it; the engine only persists declared variables, so
    # undeclared top-level POST fields never arrive — everything rides in ai_input.
    raw_input = data.pop("ai_input", None)
    business = {k: v for k, v in data.items() if k not in _GENERIC_DROP}
    if raw_input not in (None, ""):
        try:
            parsed = json.loads(raw_input) if isinstance(raw_input, str) else raw_input
        except (ValueError, TypeError):
            parsed = raw_input
        if isinstance(parsed, dict):
            business.update(parsed)
        else:
            business["ai_input"] = parsed
    parts = [instruction]
    if business:
        parts.append("\n\n## Input data\n```json\n"
                     + _bounded_json(business)
                     + "\n```")
    return "\n".join(parts)


def _bounded_json(business, cap=24000):
    """Serialize node input data for prompt embedding WITHOUT silently amputating
    late keys. The old raw `[:8000]` slice cut the JSON mid-string, so any key
    sorting after a fat one vanished — a `goal` after a bloated `existing` made the
    decompose node effectively blind (2026-07-19 incident). Strategy: full dump if
    it fits; else bound long string leaves / long arrays per-value and retry; only
    then hard-cap WITH an explicit marker so the model knows data is incomplete."""
    txt = json.dumps(business, ensure_ascii=False, indent=2)
    if len(txt) <= cap:
        return txt

    def bound(v):
        if isinstance(v, str) and len(v) > 600:
            return v[:600] + "…[truncated]"
        if isinstance(v, list):
            return [bound(x) for x in v[:80]] + (["…[%d more truncated]" % (len(v) - 80)] if len(v) > 80 else [])
        if isinstance(v, dict):
            return {k: bound(x) for k, x in v.items()}
        return v

    txt = json.dumps(bound(business), ensure_ascii=False, indent=2)
    if len(txt) <= cap:
        return txt
    return txt[:cap] + "\n…(DATA TRUNCATED at %d chars — later keys may be missing; say so if a needed field is absent)" % cap


def run_claude_generic(payload):
    if not (payload.get("prompt") or "").strip():
        raise RuntimeError("generic executor requires a non-empty `prompt`")
    prompt = _with_memory(prompt_generic(payload), payload)
    schema = json.dumps(_generic_schema(payload))
    return _invoke_claude(prompt, schema, payload, 1800)


def run_release(payload):
    """Deterministic release automation (no AI): run release-please for the
    repo of the just-merged PR. github-release cuts a tag+Release+changelog if
    a release PR was merged; release-pr opens/updates the next release PR.
    Idempotent and safe to re-run. Repos without release-please-config are
    skipped. Token comes from the container's GH_TOKEN."""
    pr = payload.get("prUrl") or payload.get("repo") or ""
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", pr)
    if m:
        owner, repo = m.group(1), m.group(2)
    else:
        parts = pr.strip().strip("/").split("/")
        if len(parts) >= 2:
            owner, repo = parts[-2], parts[-1]
        else:
            return {"released": False, "reason": "cannot parse repo from prUrl: %r" % pr}
    repo_url = "%s/%s" % (owner, repo)
    token = os.environ.get("GH_TOKEN", "")
    chk = subprocess.run(["gh", "api", "repos/%s/contents/release-please-config.json" % repo_url],
                         capture_output=True, text=True)
    if chk.returncode != 0:
        return {"released": False, "repo": repo_url,
                "reason": "no release-please config in %s, skipped" % repo_url}
    def _latest_tag():
        p = subprocess.run(["gh", "api", "repos/%s/releases/latest" % repo_url,
                            "--jq", ".tag_name"], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    def _open_release_pr():
        # component repos use release-please--branches--main--components--<name>,
        # so match the branch PREFIX instead of an exact --head value
        p = subprocess.run(["gh", "pr", "list", "-R", repo_url, "--state", "open",
                            "--json", "number,title,headRefName",
                            "--jq", r'.[] | select(.headRefName | startswith("release-please--branches--")) | "#\(.number) \(.title)"'],
                           capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    # README-sync first: a scoped claude pass fixes stale version claims so the
    # docs commit lands on main BEFORE release-pr computes the release.
    readme = {"updated": False, "reason": "readme-sync skipped"}
    usage = None
    try:
        readme = run_claude("readmesync", {"repo": repo_url,
                                           "_piid": payload.get("_piid"),
                                           "_node": payload.get("_node")})
        usage = readme.pop("_usage", None)
        readme.pop("_sid", None)
    except Exception as e:
        readme = {"updated": False, "reason": "readme-sync error: %s" % e}

    tag_before = _latest_tag()
    logs = {}
    for phase in ("github-release", "release-pr"):
        p = subprocess.run(
            ["npx", "--yes", "release-please@16", phase,
             "--repo-url=%s" % repo_url, "--token=%s" % token],
            capture_output=True, text=True, timeout=240)
        logs[phase] = (p.stdout or "") + (p.stderr or "")
    gr = logs.get("github-release", "")
    rp = logs.get("release-pr", "")
    # Ground truth, not output parsing: did the latest release change, and is
    # a release PR actually open now?
    tag_after = _latest_tag()
    released = bool(tag_after) and tag_after != tag_before
    pr_open = _open_release_pr()
    bits = []
    if released:
        bits.append("github release cut: %s" % tag_after)
    if pr_open:
        bits.append("release PR open: %s" % pr_open)
    err = ("GitHubAPIError" in gr or "GitHubAPIError" in rp)
    if err:
        bits.append("release-please reported an API error (see logs)")
    if readme.get("updated"):
        bits.append("readme synced: %s" % "; ".join(readme.get("changes", []))[:200])
    if not bits:
        bits.append("no releasable change")
    return {"released": released, "repo": repo_url, "reason": "; ".join(bits),
            "readme": readme, "_usage": usage,
            "githubRelease": gr[-700:], "releasePr": rp[-700:]}


# --- Designer publish (Phase 1C / C5) -------------------------------------
# Deterministic, NO AI. Turns a designed BPMN flow into a GATED PR on the
# platform repo (arcana-ai-bpm). It NEVER merges and NEVER self-deploys: the
# PR is opened for CI (kogito build) + human / merge-flow to gate the actual
# deploy. Modelled on run_release's git/gh-via-subprocess structure.

PROC_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
# 拋轉計算 companion DMN: a bare .dmn filename (no path traversal, no slashes)
DMN_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}\.dmn$")
PUBLISH_REPO = os.environ.get("PUBLISH_REPO", "jrjohn/arcana-ai-bpm")
# whitespace below is load-bearing: it must match the golden proto byte-for-byte
# (data-index-protobufs/demo-generic.proto). Tabs for indent, trailing spaces,
# and the @VariableInfo continuation line starting with a single space.
_FIELD_ANN = ("\t/* @Field(index = Index.YES, store = Store.YES) @SortableField */ \n")
_VAR_ANN = ("\t/* @Field(index = Index.YES, store = Store.YES) @SortableField\n"
            " @VariableInfo(tags=\"\") */ \n")


def _message_name(process_id):
    """demo-generic -> Demo_generic : '-' -> '_', first char upper-cased."""
    s = process_id.replace("-", "_")
    return s[:1].upper() + s[1:]


def gen_proto(process_id, var_names):
    """Pure function: BPMN process id + ordered variable names -> Kogito
    data-index .proto text. Output matches data-index-protobufs/demo-generic.proto
    exactly in structure (proto2, package keeps the dash, message name upper-cased
    with '-'->'_', id field first, KogitoMetadata last)."""
    msg = _message_name(process_id)
    lines = []
    lines.append('syntax = "proto2"; \n')
    lines.append("package boo.arcana.%s; \n" % process_id)
    lines.append('import "kogito-index.proto";\n')
    lines.append('import "kogito-types.proto";\n')
    lines.append('option kogito_model = "%s";\n' % msg)
    lines.append('option kogito_id = "%s";\n' % process_id)
    lines.append("\n")
    lines.append("/* @Indexed */ \n")
    lines.append("message %s { \n" % msg)
    lines.append('\toption java_package = "boo.arcana";\n')
    # field 1: id
    lines.append(_FIELD_ANN)
    lines.append("\toptional string id = 1; \n")
    # fields 2..N: each process variable, in document order
    n = 2
    for name in var_names:
        lines.append(_VAR_ANN)
        lines.append("\toptional string %s = %d; \n" % (name, n))
        n += 1
    # last field: metadata
    lines.append(_FIELD_ANN)
    lines.append(
        "\toptional org.kie.kogito.index.model.KogitoMetadata metadata = %d; \n" % n)
    lines.append("}\n")
    return "".join(lines)


def _local(tag):
    """Strip XML namespace -> localname (namespace-agnostic parsing)."""
    return tag.rsplit("}", 1)[-1]


def _parse_bpmn(bpmn_xml):
    """Return (process_id, [var_names in document order]) from a BPMN2 string.
    Namespace-agnostic on localnames 'process' and 'property'."""
    root = ET.fromstring(bpmn_xml)
    proc = None
    for el in root.iter():
        if _local(el.tag) == "process":
            proc = el
            break
    if proc is None:
        raise RuntimeError("no <process> element in bpmnXml")
    pid = proc.get("id") or ""
    var_names = []
    for el in proc.iter():
        if _local(el.tag) == "property":
            nm = el.get("name") or el.get("id")
            if nm:
                var_names.append(nm)
    return pid, var_names


def publish_flow(payload):
    """Deterministic gated-publish (NO AI). Validates the flow, generates the
    data-index proto, scaffolds the three platform-repo files, and opens a
    GATED PR on arcana-ai-bpm — never merges, never deploys. CI (kogito build)
    + human / merge-flow gate the actual deploy.

    payload: { processId, bpmnXml, dmnXml?, dmnFileName?, dry_run? }
    returns: { prUrl, branch } | { proto, files, processId } (dry_run) | { error }

    拋轉計算: a flow whose businessRuleTask invokes a generated companion DMN passes
    it as dmnXml/dmnFileName; it lands in the SAME gated PR (both or neither), since
    publishing the BPMN alone would deploy a flow bound to a DMN that isn't there.
    """
    process_id = (payload.get("processId") or "").strip()
    bpmn_xml = payload.get("bpmnXml") or ""
    dmn_xml = payload.get("dmnXml") or ""
    dmn_file_name = (payload.get("dmnFileName") or "").strip()
    dry_run = bool(payload.get("dry_run"))

    # --- validate / sanitize (prevents path traversal + bad filenames) ---
    if not PROC_ID_RE.match(process_id):
        return {"error": "invalid processId %r: must match ^[a-z][a-z0-9-]{0,63}$"
                % process_id}
    if not bpmn_xml.strip():
        return {"error": "bpmnXml is empty"}
    try:
        parsed_id, var_names = _parse_bpmn(bpmn_xml)
    except Exception as e:
        return {"error": "cannot parse bpmnXml: %s" % e}

    # If the BPMN's own process id disagrees, rewrite it to match processId so
    # the proto / filenames / engine id are all consistent.
    if parsed_id != process_id:
        bpmn_xml = re.sub(
            r'(<[^>]*\bprocess\b[^>]*\bid=")[^"]*(")',
            lambda m: m.group(1) + process_id + m.group(2),
            bpmn_xml, count=1)

    proto = gen_proto(process_id, var_names)
    rel_files = {
        "bpmn/%s.bpmn2" % process_id: bpmn_xml,
        "kogito-bpmn/src/main/resources/boo/arcana/%s.bpmn2" % process_id: bpmn_xml,
        "data-index-protobufs/%s.proto" % process_id: proto,
    }

    # --- 拋轉計算: the companion DMN ships in the same PR as the BPMN that binds it ---
    if dmn_xml.strip() or dmn_file_name:
        if not (dmn_xml.strip() and dmn_file_name):
            return {"error": "dmnXml and dmnFileName must be provided together"}
        # sanitize: a bare .dmn filename, no path traversal
        if not DMN_NAME_RE.match(dmn_file_name):
            return {"error": "invalid dmnFileName %r: must match ^[a-z0-9][a-z0-9._-]*\\.dmn$"
                    % dmn_file_name}
        rel_files["bpmn/%s" % dmn_file_name] = dmn_xml
        rel_files["kogito-bpmn/src/main/resources/boo/arcana/%s" % dmn_file_name] = dmn_xml

    # --- dry run: scaffold into a temp dir, skip push/PR (locally verifiable) ---
    if dry_run:
        tmp = tempfile.mkdtemp(prefix="publish-%s-" % process_id)
        try:
            for rel, content in rel_files.items():
                dst = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w") as f:
                    f.write(content)
            return {"dry_run": True, "processId": process_id,
                    "proto": proto, "files": sorted(rel_files.keys()),
                    "scaffoldDir": tmp, "varNames": var_names}
        finally:
            # keep scaffoldDir for the caller to inspect; do not delete here
            pass

    # --- real path: clone, write files, open a GATED PR (never merge) ---
    token = os.environ.get("GH_TOKEN", "")
    branch = "designer/publish-%s" % process_id
    tmp = tempfile.mkdtemp(prefix="publish-%s-" % process_id)
    workdir = os.path.join(tmp, "repo")
    try:
        clone_url = "https://x-access-token:%s@github.com/%s" % (token, PUBLISH_REPO)
        c = subprocess.run(["git", "clone", "--depth", "1", clone_url, workdir],
                           capture_output=True, text=True, timeout=240)
        if c.returncode != 0:
            return {"error": "clone failed: %s" % (c.stderr or c.stdout)[-500:]}

        def _git(*args):
            return subprocess.run(["git", "-C", workdir, *args],
                                  capture_output=True, text=True, timeout=120)

        _git("checkout", "-b", branch)
        for rel, content in rel_files.items():
            dst = os.path.join(workdir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write(content)
        _git("add", "-A")
        # A fresh clone has no committer identity; set it inline so `git commit`
        # never fails with "Author identity unknown" (that previously slipped past
        # the nothing-to-commit guard and pushed an empty branch).
        cm = _git("-c", "user.email=agent@arcana.boo", "-c", "user.name=AI-BPM Designer",
                  "commit", "-m", "feat(designer): publish flow %s" % process_id)
        if cm.returncode != 0:
            if "nothing to commit" in (cm.stdout + cm.stderr):
                return {"error": "no changes to publish for %s" % process_id}
            return {"error": "commit failed: %s" % (cm.stderr or cm.stdout)[-500:]}
        ps = _git("push", "-u", "origin", branch, "--force")
        if ps.returncode != 0:
            return {"error": "push failed: %s" % (ps.stderr or ps.stdout)[-500:]}

        body = ("Designer-published flow `%s`.\n\n"
                "This is a **GATED** PR — opened by the AI-BPM designer, NOT a "
                "self-deploy. CI (kogito build) + human / merge-flow gate the "
                "actual deploy. Do not auto-merge without the green gate.\n\n"
                "Files:\n- `bpmn/%s.bpmn2`\n"
                "- `kogito-bpmn/src/main/resources/boo/arcana/%s.bpmn2`\n"
                "- `data-index-protobufs/%s.proto`\n"
                % (process_id, process_id, process_id, process_id))
        # RBAC P2 provenance — INFORMATIONAL only. Authorization lives in the
        # read-API's flow_meta table; the PR body just records who published what
        # tier so a human reading the PR sees it without querying PG.
        author = payload.get("authorUsername") or ""
        tier = payload.get("tier") or ""
        if author or tier:
            body += "\nProvenance: author `%s` · tier `%s`\n" % (author or "?", tier or "personal")
        if dmn_file_name:
            body += ("- `bpmn/%s`\n- `kogito-bpmn/src/main/resources/boo/arcana/%s`\n"
                     "  (拋轉計算 companion DMN — the flow's businessRuleTask binds it "
                     "by namespace/model, so it ships in this same PR)\n"
                     % (dmn_file_name, dmn_file_name))
        env = dict(os.environ)
        if token:
            env["GH_TOKEN"] = token
        pr = subprocess.run(
            ["gh", "pr", "create", "-R", PUBLISH_REPO,
             "--base", "main", "--head", branch,
             "--title", "feat(designer): publish flow %s" % process_id,
             "--body", body],
            capture_output=True, text=True, timeout=120, cwd=workdir, env=env)
        if pr.returncode != 0:
            return {"error": "pr create failed: %s" % (pr.stderr or pr.stdout)[-500:]}
        pr_url = pr.stdout.strip().splitlines()[-1] if pr.stdout.strip() else ""
        return {"prUrl": pr_url, "branch": branch, "processId": process_id}
    except subprocess.TimeoutExpired:
        return {"error": "publish timed out"}
    except Exception as e:
        return {"error": "publish failed: %s" % e}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- Implement verb: AI writes real code → GATED PR (self-development) ----------
# The missing piece for "AI BPM self-develops its own CODE features". Combines the
# two halves already proven on this platform: the fix verb's Claude-driven code
# writing (_invoke_claude) + publish_flow's deterministic gated-PR finalizer.
# Unlike fix (repo inferred from a job string, Claude clones ambiguously) every
# hard-coded assumption is parameterized: repo / base / slug / skill.
IMPLEMENT_REPO_ALLOWLIST = set(
    (os.environ.get("IMPLEMENT_REPOS") or "jrjohn/arcana-ai-bpm").split(","))
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def _ensure_claude_config():
    """`claude --dangerously-skip-permissions` errors if `~/.claude.json` is absent
    (normal mode auto-creates it on first run). On a freshly-(re)built container the
    implement verb could be the first claude call — restore the newest backup (or a
    minimal stub) so skip-permissions mode doesn't fail. Best-effort no-op if present."""
    home = os.path.expanduser("~")
    cfg = os.path.join(home, ".claude.json")
    if os.path.exists(cfg):
        return
    try:
        bdir = os.path.join(home, ".claude", "backups")
        backups = sorted(f for f in os.listdir(bdir) if f.startswith(".claude.json.backup")) \
            if os.path.isdir(bdir) else []
        if backups:
            shutil.copy(os.path.join(bdir, backups[-1]), cfg)
        else:
            with open(cfg, "w") as f:
                f.write("{}")
    except Exception:
        pass


def implement_flow(payload):
    """AI code-implementation → GATED PR.

    Phases: (A) deterministic clone <repo>@<base> into a temp workdir;
    (B) Claude writes the feature per `design`, binding `ai_skill` (e.g.
    arcana-angular-developer-skill), running IN the workdir with skip-permissions
    + --add-dir so it can read/write the repo and write tests; (C) deterministic
    branch/commit/push + `gh pr create` GATED PR (never merges, never deploys —
    quality gates + merge-flow gate the actual merge).

    payload: { repo, base, slug, ai_skill, prompt, design?, branchPrefix?, wall? }
    returns: { prUrl, branch, summary, filesChanged, pushed } | { error }
    """
    repo = (payload.get("repo") or "").strip()
    base = (payload.get("base") or "").strip()
    slug = (payload.get("slug") or "").strip()
    instruction = (payload.get("prompt") or "").strip()
    branch_prefix = (payload.get("branchPrefix") or "feat/").strip()

    if repo not in IMPLEMENT_REPO_ALLOWLIST:
        return {"error": "repo %r not in implement allowlist %s"
                % (repo, sorted(IMPLEMENT_REPO_ALLOWLIST))}
    if not _SLUG_RE.match(slug):
        return {"error": "invalid slug %r: must match ^[a-z][a-z0-9-]{0,63}$" % slug}
    if not base:
        return {"error": "base branch required"}
    if not instruction:
        return {"error": "prompt (implementation instruction) required"}

    token = os.environ.get("GH_TOKEN", "")
    branch = "%s%s" % (branch_prefix, slug)
    # Clone under this (instance, node) workspace so concurrent implement runs are isolated;
    # fall back to a temp dir for direct calls that carry no _piid/_node.
    ws = _workspace(payload)
    tmp = ws or tempfile.mkdtemp(prefix="implement-%s-" % slug)
    workdir = os.path.join(tmp, "repo")
    try:
        # --- Phase A: clone the base branch ---
        # workspace persists across a rework loop (same instance+node), so clear any prior
        # clone before re-cloning (mkdtemp used to give a fresh dir each call).
        shutil.rmtree(workdir, ignore_errors=True)
        clone_url = "https://x-access-token:%s@github.com/%s" % (token, repo)
        c = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", base, clone_url, workdir],
            capture_output=True, text=True, timeout=300)
        if c.returncode != 0:
            return {"error": "clone failed: %s" % (c.stderr or c.stdout)[-500:]}

        # --- Phase B: Claude writes code in the workdir (bound to the dev skill) ---
        design = payload.get("design")
        design_str = json.dumps(design, ensure_ascii=False)[:8000] if design is not None else ""
        full_prompt = (
            instruction
            + "\n\n## 目標\n在目前工作目錄（已 clone 的 repo）實作此功能，嚴格遵守 repo 既有架構慣例"
              "（你載入的 developer skill 已含 Clean Arch / MVVM / arch-qube 規範），並**寫對應單元測試**。\n"
              "## 交付前自我驗證（重要）\n開 PR 前**必須**讓受影響的子專案在本地編譯通過：進到該子專案（例如 `dashboard/`）跑 "
              "`npm ci && npm run build`，有編譯錯就修到綠；並為新功能寫**會通過的單元測試**。**不要交出沒編譯過的碼**"
              "——下游 CI（build + ng test + arch-qube + Sonar）會擋，交紅碼只會被 PM NOGO 退回重做、白費一輪。"
              "時間預算內以「編得過、架構乾淨、測試通過」為第一優先；最後簡述你改了什麼。\n"
            + ("\n## 設計 (SRS/SDD)\n```json\n" + design_str + "\n```\n" if design_str else ""))
        sch = payload.get("ai_output_schema") or {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "filesChanged": {"type": "array", "items": {"type": "string"}},
                "testsPass": {"type": "boolean"}},
            "required": ["summary"]}
        schema = json.dumps(sch) if not isinstance(sch, str) else sch
        _ensure_claude_config()           # skip-permissions needs ~/.claude.json present
        cp = dict(payload)
        cp["skip_permissions"] = True     # bounded: throwaway clone in a sandbox
        cp["add_dirs"] = [workdir]
        result = _invoke_claude(full_prompt, schema, cp,
                                int(payload.get("wall") or 3300), cwd=workdir)  # 55min: finish in ONE attempt (avoid ×3 retry)
        summary = result.get("summary") if isinstance(result, dict) else str(result)

        # --- Phase C: deterministic gated PR ---
        def _git(*args):
            return subprocess.run(["git", "-C", workdir, *args],
                                  capture_output=True, text=True, timeout=120)
        _git("checkout", "-b", branch)

        # --- Phase B.5: build gate — compile affected sub-app(s) BEFORE opening the PR.
        # implement used to push unverified code → ci/angular went red → PmReview NOGO churn.
        # Compile locally; on failure feed the errors back to Claude (bounded) so the PR that
        # lands actually builds. No browser here → ng test/coverage stay CI-gated. A persistent
        # RED still opens the PR (never worse than the old behaviour) but is flagged in the body.
        BUILD_CMDS = {"dashboard": "(npm ci || npm install) && npm run build"}
        def _changed_subapps():
            tops = set()
            for ln in _git("status", "--porcelain").stdout.splitlines():
                p = ln[3:].strip().strip('"')
                if " -> " in p:
                    p = p.split(" -> ", 1)[1]
                tops.add(p.split("/", 1)[0])
            return tops
        def _build_gate():
            for d in sorted(_changed_subapps()):
                cmd = BUILD_CMDS.get(d)
                sub = os.path.join(workdir, d)
                if not cmd or not os.path.isdir(sub):
                    continue
                b = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True,
                                   timeout=900, cwd=sub)
                if b.returncode != 0:
                    return d, (b.stderr or b.stdout)[-4000:]
            return None
        build_status = "OK"
        gate = _build_gate()
        _gate_tries = 0
        while gate is not None and _gate_tries < 2:
            _gate_tries += 1
            _d, _errlog = gate
            fix_prompt = ("你剛在此工作目錄實作的功能，`%s/` 的 `npm run build` 編譯失敗。"
                          "以下是編譯錯誤輸出，請只改必要的檔把它修到**編譯通過**，不要動無關的檔：\n\n"
                          "```\n%s\n```\n" % (_d, _errlog))
            try:
                result = _invoke_claude(fix_prompt, schema, cp,
                                        int(payload.get("wall") or 1800), cwd=workdir)
                if isinstance(result, dict) and result.get("summary"):
                    summary = result.get("summary")
            except Exception as e:
                build_status = "fix-invoke-error: %s" % e
                break
            gate = _build_gate()
        if gate is not None and not build_status.startswith("fix-invoke"):
            build_status = "RED: %s build failing after %d fix attempt(s)" % (gate[0], _gate_tries)

        _git("add", "-A")
        cm = _git("-c", "user.email=agent@arcana.boo", "-c", "user.name=AI-BPM Implementer",
                  "commit", "-m", "feat: %s" % slug)
        if cm.returncode != 0:
            if "nothing to commit" in (cm.stdout + cm.stderr):
                return {"error": "implement produced no changes for %s" % slug,
                        "summary": summary, "pushed": False}
            return {"error": "commit failed: %s" % (cm.stderr or cm.stdout)[-500:]}
        diff = _git("diff", "--name-only", "%s..HEAD" % base)
        files_changed = [l for l in diff.stdout.splitlines() if l.strip()]
        # dry_run: prove the clone + Claude-writes-code phase without opening a PR.
        if payload.get("dry_run"):
            stat = _git("diff", "--stat", "%s..HEAD" % base)
            return {"dry_run": True, "branch": branch, "summary": summary,
                    "filesChanged": files_changed, "diffstat": stat.stdout[-2000:],
                    "pushed": False}
        ps = _git("push", "-u", "origin", branch, "--force")
        if ps.returncode != 0:
            return {"error": "push failed: %s" % (ps.stderr or ps.stdout)[-500:]}
        body = ("AI-implemented feature `%s`.\n\n"
                "This is a **GATED** PR — written by the AI-BPM Implement node, NOT a "
                "self-deploy. Quality gates (CI build + tests + arch-qube) + merge-flow "
                "gate the actual merge/deploy. Do not auto-merge without the green gate.\n\n"
                "Local build gate: %s\n\n"
                "Summary: %s\n" % (slug, build_status, summary or "(none)"))
        env = dict(os.environ)
        if token:
            env["GH_TOKEN"] = token
        pr = subprocess.run(
            ["gh", "pr", "create", "-R", repo, "--base", base, "--head", branch,
             "--title", "feat: %s" % slug, "--body", body],
            capture_output=True, text=True, timeout=120, cwd=workdir, env=env)
        if pr.returncode != 0:
            return {"error": "pr create failed: %s" % (pr.stderr or pr.stdout)[-500:],
                    "branch": branch, "filesChanged": files_changed}
        pr_url = pr.stdout.strip().splitlines()[-1] if pr.stdout.strip() else ""
        return {"prUrl": pr_url, "branch": branch, "summary": summary,
                "filesChanged": files_changed, "pushed": True, "buildStatus": build_status}
    except subprocess.TimeoutExpired:
        return {"error": "implement timed out"}
    except RateLimitError:
        raise  # propagate so do_POST returns 429 → worker trips the rate-limit breaker
    except Exception as e:
        return {"error": "implement failed: %s" % e}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _pr_url_and_branch(payload):
    """The worker passes the implement node's result JSON (incl. prUrl + branch) as `prUrl`;
    pull the real URL + branch out of it (or fall back to plain fields)."""
    raw = payload.get("prUrl") or ""
    url = raw if isinstance(raw, str) else ""
    branch = ""
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            j = json.loads(raw)
            url = j.get("prUrl", "") or ""
            branch = j.get("branch", "") or ""
        except Exception:
            pass
    return url, (branch or payload.get("branch") or "")




def _api_path_inventory(payload):
    """The API paths the app ACTUALLY calls, read from its own repository layer.

    The generators were told to ground UI routes and selectors in the diff and never guess —
    and were told nothing at all about API paths, so they invented candidate lists. On PR #71
    every generated testcase probed `/api/me/permissions`, `/me/permissions` and
    `/api/v1/me/permissions`; the real path is `/api/v1/users/me/permissions`. All four
    testcases and all three AC checks failed against a URL the product has never had.

    A false RED costs as much as a false green: it teaches people the gate is noise, and then
    the real failure is the one nobody looks at. So hand over the inventory instead of asking
    the model to remember an API surface it cannot see.

    Best-effort and cached on the payload; an empty list simply leaves the prompt as it was.
    """
    if "_api_paths" in payload:
        return payload["_api_paths"]
    paths, repo = [], payload.get("repo") or ""
    # Read the PR's OWN ref, not the base: a feature that ADDS an endpoint is exactly the case
    # where the generator has nothing to go on, and inventorying `main` would leave that new
    # path out — sending the model back to guessing for the one endpoint under test.
    _, _br = _pr_url_and_branch(payload)
    base = _br or payload.get("base") or "main"
    src_dir = str(_load_profile(payload)["app"].get("apiDir", "dashboard/src/app/repository/impl"))
    try:
        listing = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{src_dir}?ref={base}", "--jq", ".[].name"],
            capture_output=True, text=True, timeout=90).stdout.split()
        for name in listing:
            if not name.endswith(".ts") or name.endswith(".spec.ts"):
                continue
            body = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{src_dir}/{name}?ref={base}",
                 "--jq", ".content"], capture_output=True, text=True, timeout=90).stdout
            raw = base64.b64decode("".join(body.split())).decode("utf-8", "replace") if body.strip() else ""
            for m in re.finditer(r"['\"`](v1/[A-Za-z0-9_\-/:${}.]+)['\"`]", raw):
                p = "/api/" + m.group(1)
                if p not in paths:
                    paths.append(p)
    except Exception as e:
        print("[agent-task-node] api inventory unavailable: %s" % e, flush=True)
    payload["_api_paths"] = sorted(paths)
    return payload["_api_paths"]


def _api_grounding_block(payload):
    """The prompt fragment that stops a generator inventing endpoints."""
    paths = _api_path_inventory(payload)
    if not paths:
        return ""
    return (
        "\n\nAPI GROUNDING — these are the ONLY endpoint paths this application calls, read from "
        "its own repository layer. If an assertion needs an API, use one of these VERBATIM; do "
        "not shorten, re-nest or invent a variant, and do not write a 'try several candidates' "
        "loop — a probe that guesses reports the product broken when only the guess was.\n"
        "Call them ONLY through the injected `api(path)` helper, never `page.request.*` directly: "
        "this app holds its token in localStorage and attaches it with an interceptor, so a raw "
        "request carries no Authorization header and every protected endpoint answers 401 — a "
        "failure the test causes and then blames on the product.\n"
        "Assert on the STATUS CODE, and on a response field ONLY if that exact field name appears "
        "in the diff or SRS. Do not infer one from the endpoint's name — a check that expects "
        "`permissions` from an endpoint returning `functions` fails a working API and reads as a "
        "product defect.\n  "
        + "\n  ".join(paths[:60])
    )


def _gen_testcases(payload):
    """T4-2: generate feature-specific Playwright testcases (.mjs) from the ACs + the PR diff, so
    the Test gate checks THIS feature (not just org regression). Returns the .mjs text, or None to
    fall back to the default regression set (the runner then uses org-designer.testcases.mjs)."""
    srs = payload.get("srs") or ""
    if isinstance(srs, (dict, list)):
        srs = json.dumps(srs, ensure_ascii=False)
    url, _ = _pr_url_and_branch(payload)
    diff = ""
    if url:
        try:
            diff = (subprocess.run(["gh", "pr", "diff", url], capture_output=True, text=True,
                                   timeout=90).stdout or "")[:12000]
        except Exception:
            diff = ""
    if not (srs or diff):
        return None
    prompt = (
        "You are writing Playwright e2e testcases for a NEW feature, to run against a LIVE preview "
        "of the app (already logged in, at BASE_URL).\n\n"
        "Acceptance criteria (SRS):\n" + (srs or "(none)") + "\n\n"
        "The feature's code (PR diff — use the REAL selectors / visible text from here):\n"
        + (diff or "(none)") + "\n\n"
        "GROUNDING — the feature's ROUTE and SELECTORS must come from the PR diff above: read the\n"
        "app.routes.ts changes for the route, and the new components' HTML templates for real\n"
        "classes/text. NEVER reuse another feature's route or selector as a guess — e.g. `/org`\n"
        "and `.org-designer` belong to the Org feature and are WRONG unless this diff touches them.\n"
        "If the diff shows no obvious container class, wait on visible text from the feature's\n"
        "template (getByText) instead of inventing a selector.\n\n"
        "Write a JavaScript ES module exporting `testcases`, EXACTLY this shape:\n"
        "export const testcases = [\n"
        "  { id: 'FEAT-01', name: '<short zh desc>', run: async ({ page, assert, shot, base, shared }) => {\n"
        "      await page.goto(`${base}/<route>`, { waitUntil: 'domcontentloaded' });\n"
        "      await page.waitForSelector('<real selector>', { timeout: 20000 });\n"
        "      await shot('before');\n"
        "      const actual = (await page.locator('<real selector>').innerText()).trim();\n"
        "      assert(actual === '<expected>', `got ${actual}`);\n"
        "  } },\n];\n\n"
        "Rules:\n"
        "- Assert on a REAL end-state value the feature produces (text / count / attribute) — NEVER "
        "on the mere presence of a 'success' string.\n"
        "- Use ONLY selectors / routes / text that appear in the diff or SRS; if unsure, prefer "
        "role/text locators (getByText, getByRole).\n"
        "- 2-4 focused testcases for the key ACs (include edge cases like empty / error / a11y if "
        "the SRS mentions them).\n"
        "- `assert(cond, msg)` throws on false; `shot(name)` screenshots; `base` is the origin; "
        "`shared` persists across testcases.\n"
        "- Output ONLY the module code — no markdown fences, no prose."
    )
    schema = json.dumps({"type": "object", "additionalProperties": False,
                         "properties": {"testcasesMjs": {"type": "string"}},
                         "required": ["testcasesMjs"]})
    prompt += _api_grounding_block(payload)
    try:
        # 600s: generating a full Playwright module from a large diff regularly exceeds
        # 300s (and a silent None here demotes the run to the org REGRESSION set, whose
        # pre-existing failures then churn the feature's rework loop for nothing).
        out = _invoke_claude(prompt, schema, payload, wall=600)
        mjs = ((out or {}).get("testcasesMjs") or "").replace("```javascript", "") \
            .replace("```js", "").replace("```", "").strip()
        if "export const testcases" not in mjs:
            print("[agent-task-node] testcase GEN produced no module (len=%d) — falling back to regression"
                  % len(mjs), flush=True)
            return None
        return mjs
    except Exception as e:
        print("[agent-task-node] testcase GEN failed: %s — falling back to regression" % e, flush=True)
        return None


def _gen_journeys(payload):
    """T4-3: derive 1-3 GOAL-DIRECTED user journeys (persona + goal + start route) from the ACs + PR
    diff, for the journey-walk gate. The gate drives the live preview toward each goal and FAILS if a
    journey is BLOCKED (the task cannot be completed) — the class of bug static screenshots miss
    ("the page renders, but there is no way to sign"). Journeys are NON-MUTATING: they verify the
    action control is REACHABLE, never actually submit/approve/delete. Returns a JSON-array string, or
    None to skip the journey gate (non-UI feature / no source)."""
    if str(payload.get("uiFacing", "")).strip().lower() not in ("true", "1", "yes"):
        return None  # backend-only feature → no UI journey
    srs = payload.get("srs") or ""
    if isinstance(srs, (dict, list)):
        srs = json.dumps(srs, ensure_ascii=False)
    url, _ = _pr_url_and_branch(payload)
    diff = ""
    if url:
        try:
            diff = (subprocess.run(["gh", "pr", "diff", url], capture_output=True, text=True,
                                   timeout=90).stdout or "")[:12000]
        except Exception:
            diff = ""
    if not (srs or diff):
        return None
    # 以人為本 (Phase B): journey generation runs under arcana-journey-test-skill —
    # persona WORK CHAINS across features with endpoint-state acceptance, not just
    # single-screen reachability. Mutating goals are produced ONLY when
    # JOURNEY_MUTATE=1 (isolated API_TARGET; the preview's /api proxies to a REAL
    # backend by default, and mutating real data is never acceptable).
    gen_payload = dict(payload)
    gen_payload["ai_skill"] = "arcana-journey-test-skill"
    mutate = os.environ.get("JOURNEY_MUTATE", "") == "1"
    mutate_note = (
        "MUTATION MODE IS ON (isolated stack): goals may really press submit/approve and MUST "
        "assert the endpoint state (success toast / list gains a row / status change) — not seeing "
        "it = BLOCKED.\n" if mutate else
        "CRITICAL — NON-MUTATING: each goal MUST end at 'confirm the <action control> is present "
        "and reachable (do NOT press it)'. Reaching the point where the user COULD act is the "
        "pass.\n")
    prompt = (
        "You define GOAL-DIRECTED user journeys for a UI walkthrough gate. The gate drives a LIVE "
        "preview of the app (already logged in as admin) toward each goal and FAILS the journey if the "
        "user CANNOT complete the task (the control to act is unreachable).\n\n"
        "Acceptance criteria (SRS):\n" + (srs or "(none)") + "\n\n"
        "The feature's code (PR diff — routes come from app.routes.ts changes, personas/actions from "
        "the new templates):\n" + (diff or "(none)") + "\n\n"
        "Define 1-3 journeys for the feature's PRIMARY user task(s). Each = one persona completing one "
        "real WORK CHAIN (multi-screen numbered steps are welcome — follow your skill's chain "
        "library, trimmed to what this PR touches).\n"
        + mutate_note +
        "Every goal also appends the 以人為本 observation clause from your skill (system words / "
        "fake data / dead buttons / inhuman error copy => finding).\n"
        "Each journey: persona (a role this app serves — prefer one of: "
        + "/".join(_load_profile(payload).get("personas") or ["使用者"]) + "), goal (zh, one concrete task "
        "ending at a reachable control, include '不要真的按下'), start (the route from the diff, e.g. /todo).\n"
        "Output strictly JSON: {\"journeys\":[{\"persona\":\"...\",\"goal\":\"...\",\"start\":\"/...\"}]}. No prose."
    )
    schema = json.dumps({"type": "object", "additionalProperties": False,
                         "properties": {"journeys": {"type": "array", "items": {
                             "type": "object", "additionalProperties": False,
                             "properties": {"persona": {"type": "string"}, "goal": {"type": "string"},
                                            "start": {"type": "string"}},
                             "required": ["persona", "goal", "start"]}}},
                         "required": ["journeys"]})
    try:
        out = _invoke_claude(prompt, schema, gen_payload, wall=420)
        js = [j for j in ((out or {}).get("journeys") or []) if j.get("goal") and j.get("start")][:3]
        return json.dumps(js, ensure_ascii=False) if js else None
    except Exception as e:
        print("[agent-task-node] journey GEN failed: %s — skipping journey gate" % e, flush=True)
        return None


def _gen_api_checks(payload):
    """AC→API acceptance for NON-UI features (uiFacing=false) — the counterpart of
    _gen_journeys: derive up to 6 GET-only endpoint-state checks from the SRS ACs + PR
    diff, executed deterministically by the runner's api-checks.mjs against the real
    read-API. Each check asserts an OBSERVABLE state (status + optional stable response
    substring), so a backend AC is verified by execution, not only by implement's own
    unit tests. Non-mutating by construction (GET /api/* only). Returns a JSON-array
    string, or None to skip (UI feature / no source)."""
    if str(payload.get("uiFacing", "")).strip().lower() in ("true", "1", "yes"):
        return None  # UI feature → the journey gate owns acceptance
    srs = payload.get("srs") or ""
    if isinstance(srs, (dict, list)):
        srs = json.dumps(srs, ensure_ascii=False)
    url, _ = _pr_url_and_branch(payload)
    diff = ""
    if url:
        try:
            diff = (subprocess.run(["gh", "pr", "diff", url], capture_output=True, text=True,
                                   timeout=90).stdout or "")[:12000]
        except Exception:
            diff = ""
    if not (srs or diff):
        return None
    prompt = (
        "You define API-level ACCEPTANCE CHECKS for a backend feature. A deterministic runner "
        "will log in as admin and execute each check with a plain GET against the real API, "
        "asserting the HTTP status and (optionally) a stable substring of the response body.\n\n"
        "Acceptance criteria (SRS):\n" + (srs or "(none)") + "\n\n"
        "The feature's code (PR diff — real routes come from the router/controller changes):\n"
        + (diff or "(none)") + "\n\n"
        "Rules:\n"
        "- Up to 6 checks covering the feature's PRIMARY ACs; fewer is fine.\n"
        "- GET only, path MUST start with /api/ and MUST exist in the diff or be a known route — "
        "NEVER invent paths; if an AC has no GET-observable state, skip it.\n"
        "- expectContains: a SHORT stable substring (a JSON key like \"skills\" — never volatile "
        "values like timestamps/ids).\n"
        "- name: zh, states WHICH AC this check proves.\n"
        "Output strictly JSON: {\"checks\":[{\"name\":\"...\",\"path\":\"/api/v1/...\","
        "\"expectStatus\":200,\"expectContains\":\"...\"}]}. No prose."
    )
    schema = json.dumps({"type": "object", "additionalProperties": False,
                         "properties": {"checks": {"type": "array", "items": {
                             "type": "object", "additionalProperties": False,
                             "properties": {"name": {"type": "string"}, "path": {"type": "string"},
                                            "expectStatus": {"type": "integer"},
                                            "expectContains": {"type": "string"}},
                             "required": ["name", "path", "expectStatus"]}}},
                         "required": ["checks"]})
    prompt += _api_grounding_block(payload)
    try:
        out = _invoke_claude(prompt, schema, dict(payload), wall=300)
        cs = [c for c in ((out or {}).get("checks") or [])
              if str(c.get("path", "")).startswith("/api/")][:6]
        return json.dumps(cs, ensure_ascii=False) if cs else None
    except Exception as e:
        print("[agent-task-node] api-check GEN failed: %s — skipping AC-API gate" % e, flush=True)
        return None




# ── PR-built backend: stop testing a PR's frontend against somebody else's backend ──────────
#
# The preview has always proxied `/api` to the DEPLOYED read-API, so a PR that changed Rust was
# invisible to every gate: journey, api-checks and the RBAC gates all talked to a backend that
# did not contain the change under review. On 2026-07-20 that was 8 of 12 real defects — the
# flow could write those fixes and could not verify a single one, while reporting green.
#
# So when a PR touches the backend, build ITS read-API and point the gates at that instead.
#
# Two deliberate limits, because the smallest thing that answers "is the PR's backend correct"
# is much smaller than a full private stack:
#   - only the read-API is rebuilt. The engine is BPMN compiled at image build and gated
#     separately by maven; Kafka/data-index carry no PR code.
#   - the database is a THROWAWAY COPY of the dev one (10 MB, ~0.1s to dump), not a fresh
#     schema. Real data means the gates behave normally instead of failing on an empty org
#     tree, and a copy means an unreviewed migration in the PR cannot touch the shared DB —
#     which it would, since migrations run at startup.

_PR_BACKEND_PATHS = ("arcana-cloud-rust/",)


def _touches_backend(work, base, repo="", branch=""):
    """Does this PR change backend code? `git diff --name-only` against the base ref.

    A shallow clone has no base ref until it is fetched, and the first version of this silently
    swallowed that failure and answered "no backend change" — so the expensive, correct path was
    skipped and the run looked deliberately cheap instead of broken. When the diff cannot be
    computed we now answer YES: paying for a build we might not need is recoverable, testing a
    backend change against the deployed API while reporting green is not.
    """
    # Ask GitHub first: it knows the PR's file list without needing history the shallow clone
    # does not have. `git` stays as the offline fallback.
    if repo and branch:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls?head={repo.split('/')[0]}:{branch}&state=all",
             "--jq", ".[0].number"], capture_output=True, text=True, timeout=90)
        num = (r.stdout or "").strip()
        if num.isdigit():
            f = subprocess.run(["gh", "api", f"repos/{repo}/pulls/{num}/files", "--paginate",
                                "--jq", ".[].filename"], capture_output=True, text=True, timeout=120)
            if f.returncode == 0 and (f.stdout or "").strip():
                return any(x.startswith(pref) for x in f.stdout.splitlines()
                           for pref in _PR_BACKEND_PATHS)
    subprocess.run(["git", "-C", work, "fetch", "--depth", "50", "origin", base],
                   capture_output=True, timeout=300)
    for ref in (f"origin/{base}", base):
        r = subprocess.run(["git", "-C", work, "diff", "--name-only", f"{ref}...HEAD"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and (r.stdout or "").strip():
            return any(f.startswith(p) for f in r.stdout.splitlines() for p in _PR_BACKEND_PATHS)
    print("[agent-task-node] pr-backend: cannot diff against %s — assuming the backend changed"
          % base, flush=True)
    return True


def _pg_exec(sql, db="postgres"):
    return subprocess.run(
        ["docker", "exec", os.environ.get("TEST_PG_CONTAINER", "aaf-kogito-pg"),
         "psql", "-U", os.environ.get("TEST_PG_USER", "kogito"), "-d", db, "-tAc", sql],
        capture_output=True, text=True, timeout=180)


def _start_pr_backend(repo, branch, base, piid, net):
    """Build the PR's read-API + give it a throwaway copy of the dev DB. Returns
    `(api_target, teardown)`; `(None, teardown)` when it does not apply or could not be built.

    Never raises: a backend preview that cannot be built must degrade to today's behaviour
    (test against the deployed API) rather than fail the node for an infrastructure problem —
    but it says WHICH happened, because a silently skipped isolation is how you end up
    trusting a green that never exercised the change.
    """
    tag = piid[:12].lower() or "adhoc"
    cname, dbname, image = f"aaf-pr-api-{tag}", f"arcana_pr_{tag}", f"aaf-pr-api:{tag}"
    src = tempfile.mkdtemp(prefix="pr-backend-")
    state = {"container": None, "db": None, "image": None, "src": src}

    def teardown():
        if state["container"]:
            subprocess.run(["docker", "rm", "-f", state["container"]], capture_output=True, timeout=120)
        if state["db"]:
            _pg_exec(f'DROP DATABASE IF EXISTS "{state["db"]}" WITH (FORCE)')
        if state["image"]:
            subprocess.run(["docker", "rmi", "-f", state["image"]], capture_output=True, timeout=120)
        shutil.rmtree(state["src"], ignore_errors=True)

    try:
        auth = ""
        if os.environ.get("GH_TOKEN"):
            auth = "x-access-token:" + os.environ["GH_TOKEN"] + "@"
        clone = subprocess.run(
            ["git", "clone", "--depth", "50", "--branch", branch,
             f"https://{auth}github.com/{repo}", src],
            capture_output=True, text=True, timeout=600)
        if clone.returncode != 0:
            print("[agent-task-node] " + "pr-backend: clone failed, falling back to the deployed API", flush=True)
            return None, teardown
        if not _touches_backend(src, base, repo, branch):
            print("[agent-task-node] " + "pr-backend: PR does not touch the backend — deployed API is the right target", flush=True)
            return None, teardown

        print("[agent-task-node] " + "pr-backend: building the PR's read-API (this is the point — its own code, not the deployed one)", flush=True)
        b = subprocess.run(
            ["docker", "build", "-f", "Dockerfile.flow", "-t", image, "."],
            cwd=os.path.join(src, "arcana-cloud-rust"), capture_output=True, text=True, timeout=3000)
        if b.returncode != 0:
            print("[agent-task-node] " + "pr-backend: BUILD FAILED — " + (b.stderr or "")[-400:], flush=True)
            return "BUILD_FAILED", teardown
        state["image"] = image

        # Throwaway copy of the dev DB: real data, and migrations in the PR stay contained.
        _pg_exec(f'DROP DATABASE IF EXISTS "{dbname}" WITH (FORCE)')
        c = _pg_exec(f'CREATE DATABASE "{dbname}"')
        if c.returncode != 0:
            print("[agent-task-node] " + "pr-backend: could not create the throwaway DB — " + (c.stderr or "")[-200:], flush=True)
            return None, teardown
        state["db"] = dbname
        pg = os.environ.get("TEST_PG_CONTAINER", "aaf-kogito-pg")
        user = os.environ.get("TEST_PG_USER", "kogito")
        subprocess.run(
            ["docker", "exec", pg, "sh", "-c",
             f'pg_dump -U {user} -d arcana | psql -q -U {user} -d "{dbname}"'],
            capture_output=True, text=True, timeout=600)

        # `docker create` + `docker cp` + `docker start`, not `-d -v`: this agent runs INSIDE a
        # container, so a `-v` source path would be resolved on the docker HOST and silently mount
        # nothing. `docker cp` streams from the client's own filesystem, so the PR's clone reaches
        # the container. The BPMN dir is not optional — /definitions reads it, and without it the
        # API answers `[]` for every flow, which looks like a working backend serving an empty
        # system and would fail the gates for entirely the wrong reason.
        # Names are deterministic, so a crash that skipped teardown would block every later run
        # on this instance with a name conflict. Clear the corpse first.
        subprocess.run(["docker", "rm", "-f", cname], capture_output=True, timeout=120)
        run = subprocess.run(
            ["docker", "create", "--name", cname, "--network", net,
             "-e", f"ARCANA__DATABASE__URL=postgres://{user}:{user}@{pg}:5432/{dbname}",
             "-e", f"DATAINDEX_PG=postgres://{user}:{user}@{pg}:5432/dataindex",
             "-e", "ARCANA_ENVIRONMENT=production",
             "-e", "ARCANA__REDIS__ENABLED=false",
             "-e", "ARCANA__SECURITY__GRPC_TLS_ENABLED=false",
             "-e", "ARCANA__SECURITY__JWT_SECRET=" + os.environ.get(
                 "JWT_SECRET", "local-dev-jwt-secret-change-me-0123456789"),
             "-e", "AUTH_MODE=ldap",
             "-e", "LDAP_URL=ldap://aaf-openldap:389",
             "-e", "LDAP_BASE_DN=dc=arcana,dc=local",
             "-e", "LDAP_USER_BASE=ou=people,dc=arcana,dc=local",
             "-e", "LDAP_GROUP_BASE=ou=groups,dc=arcana,dc=local",
             "-e", "LDAP_BIND_DN=cn=admin,dc=arcana,dc=local",
             "-e", "LDAP_BIND_PW=admin",
             "-e", "DATA_INDEX_URL=http://aaf-data-index:8080",
             "-e", "AGENT_TASK_URL=" + os.environ.get("AGENT_TASK_URL", "http://agent-task-node:8090"),
             image],
            capture_output=True, text=True, timeout=300)
        if run.returncode != 0:
            print("[agent-task-node] " + "pr-backend: container create failed — " + (run.stderr or "")[-300:], flush=True)
            return None, teardown
        state["container"] = cname
        for sub in ("bpmn", "usage", "console"):
            d = os.path.join(src, sub)
            if os.path.isdir(d):
                subprocess.run(["docker", "cp", d + "/.", f"{cname}:/app/{sub}"],
                               capture_output=True, timeout=300)
        st = subprocess.run(["docker", "start", cname], capture_output=True, text=True, timeout=120)
        if st.returncode != 0:
            print("[agent-task-node] " + "pr-backend: container failed to start — " + (st.stderr or "")[-300:], flush=True)
            return None, teardown

        target = f"http://{cname}:8080"
        for _ in range(60):
            probe = subprocess.run(
                ["docker", "run", "--rm", "--network", net, "curlimages/curl:latest",
                 "-sf", "-o", "/dev/null", f"{target}/api/v1/definitions"],
                capture_output=True, timeout=60)
            if probe.returncode == 0:
                print("[agent-task-node] " + f"pr-backend: the PR's read-API is live at {target} — gates now test THIS code", flush=True)
                return target, teardown
            time.sleep(3)
        # Built but will not run. Falling back to the deployed API here would recreate exactly the
        # blindness this whole mechanism exists to remove — a green earned against code that is not
        # the code under review. Stop, and hand over the startup log so a human can tell the two
        # causes apart: the PR's backend is broken, or the throwaway DB carries migrations this
        # branch does not have (it is a copy of the CURRENT dev DB, so a PR based on an older ref
        # can legitimately be behind it).
        logs = subprocess.run(["docker", "logs", "--tail", "30", cname],
                              capture_output=True, text=True, timeout=120)
        tail = ((logs.stderr or "") + (logs.stdout or "")).strip()[-600:]
        if not tail:
            # It can genuinely exit with nothing on either stream — observed with an older
            # arcana-server. Saying "no output" plus the exit code beats an empty quote that
            # reads like the log was lost.
            code = subprocess.run(["docker", "inspect", cname, "--format", "{{.State.ExitCode}}"],
                                  capture_output=True, text=True, timeout=60)
            tail = ("the process exited with code %s and wrote nothing to stdout/stderr; "
                    "reproduce with: docker run --rm --network %s %s"
                    % ((code.stdout or "?").strip(), net, image))
        print("[agent-task-node] pr-backend: read-API never became ready — " + tail, flush=True)
        return "UNHEALTHY:" + tail, teardown
    except Exception as e:
        print("[agent-task-node] " + f"pr-backend: {type(e).__name__}: {e}", flush=True)
        return None, teardown




def _post_commit_status(repo, branch, rep):
    """Report the test node's verdict to GitHub as a commit status.

    Jenkins never built this repo — no commit in its history has ever carried a status — so
    `gh pr checks` had nothing to report and the green-PR automerge chain, which gates on
    exactly that, could never fire. Ten PRs piled up behind a signal that was never sent.

    The platform is already its own CI, and a stricter one than a build would be: it compiles
    the PR's frontend AND backend, runs the lints, drives the UI, and walks whole business
    chains as several people. All it was missing was telling GitHub.

    The description carries what was NOT verified, not just the verdict. A green that
    silently skipped the scenario walk, or ran against the deployed backend rather than the
    PR's, is worth strictly less than one that did neither — and the person reading a single
    line of check summary is exactly who needs to know which kind they are looking at.
    """
    if not repo or not branch:
        return
    try:
        sha = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{branch}", "--jq", ".sha"],
            capture_output=True, text=True, timeout=90).stdout.strip()
        if not sha:
            return
        ok = bool(rep.get("allPass"))
        caveats = []
        if rep.get("staleGates"):
            caveats.append("gates missing from runner")
        if not rep.get("prBackendTested") and rep.get("prBackendApplicable"):
            caveats.append("deployed backend, not the PR's")
        if not rep.get("scenarioRan"):
            caveats.append("no scenario walk")
        if not rep.get("featureTests"):
            caveats.append("regression only")
        desc = "%s/%s testcases" % (rep.get("passed", 0), rep.get("total", 0))
        if caveats:
            desc += " — unverified: " + ", ".join(caveats)
        subprocess.run(
            ["gh", "api", "-X", "POST", f"repos/{repo}/statuses/{sha}",
             "-f", "state=" + ("success" if ok else "failure"),
             "-f", "context=arcana/sdlc-test",
             "-f", "description=" + desc[:138]],
            capture_output=True, timeout=90)
        print("[agent-task-node] posted commit status arcana/sdlc-test=%s on %s: %s"
              % ("success" if ok else "failure", sha[:8], desc), flush=True)
    except Exception as e:
        # Never let reporting break the node — the verdict itself is already computed.
        print("[agent-task-node] commit status post failed: %s" % e, flush=True)


def test_flow(payload):
    """do_test node (P-SDLC): run the dedicated playwright runner image via the mounted docker.sock.
    T4: when a PR branch is known, the runner clones + builds it and serves a preview so e2e run
    against the PR's ACTUAL (unmerged) code; feature-specific testcases are generated from the ACs
    + PR diff (T4-2) so the gate checks THIS feature, not just org regression. Runs REAL e2e
    (falsifiable, screenshot-backed), writes a testcase Excel + evidence to MinIO, returns a
    testReport. Fail-safe: any error -> allPass:false so the flow REWORKS. Chromium / build tooling
    live in the runner image, not this agent — the agent needs only the mounted docker.sock."""
    keep = lambda v: "".join(c for c in str(v) if c.isalnum() or c in "-_") or "adhoc"
    piid = keep(payload.get("_piid") or payload.get("slug") or "adhoc")
    net = os.environ.get("TEST_NETWORK", "arcana-ai-agent-flow_default")
    repo = payload.get("repo") or ""
    _, branch = _pr_url_and_branch(payload)
    base = payload.get("base") or "main"
    # A PR that changes the backend gets its OWN read-API built and pointed at; otherwise the
    # deployed one stays the right target and nothing extra is paid. `teardown` runs in the
    # finally below — a leaked container would poison every later run on this network.
    api_target = os.environ.get("TEST_API_TARGET", "http://aaf-arcana-cloud-rust:8080")
    pr_teardown = lambda: None
    pr_backend_used = False
    # Whether a PR-built backend was even APPLICABLE — a frontend-only PR that legitimately
    # skipped it must not be reported as "unverified backend".
    pr_backend_applicable = False
    if repo and branch:
        built, pr_teardown = _start_pr_backend(repo, branch, base, piid, net)
        if isinstance(built, str) and built.startswith("UNHEALTHY:"):
            pr_teardown()
            return {"testReport": json.dumps({
                "allPass": False, "total": 0, "passed": 0,
                "reason": "PR backend built but would not start: " + built[len("UNHEALTHY:"):][-300:]})}
        if built == "BUILD_FAILED":
            # Unbuildable backend is a failing test, not a fallback: shipping it would break
            # the deployed API, and testing the OLD one would report green for exactly that.
            pr_teardown()
            return {"testReport": json.dumps({
                "allPass": False, "total": 0, "passed": 0,
                "reason": "PR backend build FAILED (unbuildable backend code)"})}
        if built:
            api_target, pr_backend_used = built, True
            pr_backend_applicable = True
    cmd = ["docker", "run", "--rm", "--network", net,
           # claude auth for the runner's AI semantic review step (uiux-ai-review.mjs): pass the
           # SAME long-lived OAuth token the agent uses (env, not a shared-home mount — the mount
           # caused a .credentials backup/corruption race). Empty/invalid -> the runner's
           # `command -v claude` + login check skips the AI pass (not fatal).
           "-e", "CLAUDE_CODE_OAUTH_TOKEN=" + os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
           "-e", "IS_SANDBOX=1",
           "-e", "MINIO_URL=" + os.environ.get("TEST_MINIO_URL", "http://aaf-minio:9000"),
           "-e", "MINIO_USER=" + os.environ.get("MINIO_ROOT_USER", "minioadmin"),
           "-e", "MINIO_PASS=" + os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"),
           "-e", "MINIO_BUCKET=arcana-attachments",
           "-e", "INSTANCE=" + piid,
           "-e", "API_TARGET=" + api_target]
    # C: per-app run-recipe from the Project Profile (defaults = dashboard, so aaf is unchanged). The
    # runner + journey/uiux mjs read these instead of hard-coding the dashboard build/port/login.
    _pf = _load_profile(payload)
    cmd += ["-e", "APP_SUBDIR=" + str(_pf["app"].get("appDir", "dashboard")),
            "-e", "BUILD_CMD=" + str(_pf["app"].get("buildCmd", "npm run build")),
            "-e", "PREVIEW_PORT=" + str(_pf["run"].get("previewPort", 8087)),
            "-e", "UIUX_USER=" + str(_pf["auth"].get("user", "boss")),
            "-e", "UIUX_PASS=" + str(_pf["auth"].get("pass", "pw")),
            "-e", "JW_USER=" + str(_pf["auth"].get("user", "boss")),
            "-e", "JW_PASS=" + str(_pf["auth"].get("pass", "pw")),
            # The screen->function map is parsed from the app's OWN nav config (already in the
            # profile), so the gate follows a renamed/moved guard instead of restating it.
            "-e", "RBACUI_ACTORS=" + str(_pf["auth"].get("rbacActors", "")),
            # Only meaningful with a PR-built backend; the harness itself refuses a shared API.
            "-e", "SW_ACTORS=" + (str(_pf["auth"].get("scenarioActors", "")) if pr_backend_used else ""),
            "-e", "RBACUI_NAV_CONFIG=/work/repo/" + str(_pf["nav"].get(
                "navPath", "dashboard/src/app/core/navigation/nav.config.ts"))]
    if repo and branch:  # T4-1: build the PR branch and test its real code
        cmd += ["-e", "REPO=" + repo, "-e", "BRANCH=" + branch,
                "-e", "GH_TOKEN=" + os.environ.get("GH_TOKEN", "")]
    else:                # regression fallback: test the already-running app
        cmd += ["-e", "TARGET_URL=" + os.environ.get("TEST_TARGET_URL", "http://aaf-dashboard:80")]
    gen = _gen_testcases(payload)  # T4-2: feature-specific testcases (else default regression)
    if gen:
        cmd += ["-e", "TESTCASES_B64=" + base64.b64encode(gen.encode()).decode()]
    jrn = _gen_journeys(payload)  # T4-3: goal-directed journeys for the walkthrough gate (UI features)
    if jrn:
        cmd += ["-e", "JOURNEYS_B64=" + base64.b64encode(jrn.encode()).decode()]
    apc = _gen_api_checks(payload)  # AC→API acceptance (non-UI features)
    if apc:
        cmd += ["-e", "API_CHECKS_B64=" + base64.b64encode(apc.encode()).decode()]
    cmd.append(os.environ.get("TEST_RUNNER_IMAGE", "aaf-test-runner:local"))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=2400)
        line = next((l for l in reversed((r.stdout or "").splitlines())
                     if l.startswith("TESTREPORT:")), "")
        if line:
            rep = json.loads(line[len("TESTREPORT:"):])
            rep["featureTests"] = bool(gen)  # true = tested THIS feature; false = regression only
            # Which backend answered matters as much as the result: a green earned against the
            # DEPLOYED api says nothing about a PR that changed the backend, and the PM has to be
            # able to tell those two greens apart.
            rep["prBackendTested"] = pr_backend_used
            rep["prBackendApplicable"] = pr_backend_applicable
            _post_commit_status(repo, branch, rep)
            return rep
        tail = ((r.stderr or "") + (r.stdout or ""))[-400:]
        bad = {"allPass": False, "total": 0, "passed": 0,
               "reason": "runner emitted no TESTREPORT (exit %s): %s" % (r.returncode, tail)}
        _post_commit_status(repo, branch, bad)
        return bad
    except Exception as e:
        return {"allPass": False, "total": 0, "passed": 0, "reason": "test runner invoke failed: %s" % e}
    finally:
        # Always: a leaked container/DB would poison every later run on this network.
        pr_teardown()


def uiux_audit_flow(payload):
    """Deterministic UI/UX self-audit -> auto-open GATED PRs (the detection->action wiring).
    Runs the AI semantic gate (uiux-ai-review) against the DEPLOYED dashboard via the test-runner,
    then for each FAIL finding starts ONE sdlc-code-flow — a gated PR that STOPS at the PR: the
    flow's own Test + PM gates decide the merge, nothing auto-merges here. Deduped by a
    deterministic slug (against active sdlc-flows AND open PRs) and capped (UIUX_AUDIT_MAX) so a
    single run never floods the fleet. Returns {findings, fails, started, skipped, triggered}."""
    net = os.environ.get("TEST_NETWORK", "arcana-ai-agent-flow_default")
    base = payload.get("base_url") or os.environ.get("UIUX_AUDIT_BASE", "http://aaf-dashboard:80")
    routes = payload.get("routes") or os.environ.get(
        "UIUX_AUDIT_ROUTES",
        "/workflow,/org,/evaluation,/approvals,/governance,/form-designer,/designer,/profile")
    engine = os.environ.get("ENGINE_URL", "http://aaf-kogito-bpmn:8080")
    di = os.environ.get("DATA_INDEX_URL", "http://aaf-data-index:8080")
    repo = payload.get("repo") or os.environ.get("UIUX_AUDIT_REPO", "jrjohn/arcana-ai-bpm")
    target_base = payload.get("target_base") or os.environ.get("UIUX_AUDIT_TARGET_BASE", "main")
    _cap = payload.get("cap")  # explicit None check so cap=0 (dry-run) is honoured, not falsy->default
    cap = int(_cap if _cap is not None else os.environ.get("UIUX_AUDIT_MAX", "2"))

    def _curl_json(method, url, body=None, timeout=60):
        cmd = ["curl", "-s", "-X", method, url, "-H", "Content-Type: application/json"]
        if body is not None:
            cmd += ["-d", json.dumps(body)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return json.loads(r.stdout or "{}")
        except Exception:
            return {}

    # 1. run the AI semantic gate in the test-runner (playwright screenshots + claude vision)
    cmd = ["docker", "run", "--rm", "--network", net,
           "-e", "CLAUDE_CODE_OAUTH_TOKEN=" + os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
           "-e", "IS_SANDBOX=1", "-e", "UIUX_BASE=" + base, "-e", "UIUX_ROUTES=" + routes,
           "--entrypoint", "node",
           os.environ.get("TEST_RUNNER_IMAGE", "aaf-test-runner:local"), "/e2e/uiux-ai-review.mjs"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return {"findings": 0, "started": 0, "error": "audit gate timed out"}
    line = next((l for l in reversed((r.stdout or "").splitlines()) if l.startswith('{"routes')), "")
    try:
        data = json.loads(line)
    except Exception:
        return {"findings": 0, "started": 0, "error": "audit gate produced no findings json",
                "tail": (r.stdout or r.stderr or "")[-300:]}
    fails = [f for f in data.get("findings", []) if f.get("severity") == "fail"]

    # 2. dedup: slugs of currently-active sdlc-flows (don't re-open what's in flight)
    active_slugs = set()
    q = {"query": "{ ProcessInstances(where:{processId:{equal:\"sdlc-code-flow\"},"
                  "state:{equal:ACTIVE}}){ variables } }"}
    for pi in (_curl_json("POST", di + "/graphql", q, 30).get("data", {}) or {}).get("ProcessInstances", []) or []:
        v = pi.get("variables")
        v = json.loads(v) if isinstance(v, str) else (v or {})
        if v.get("slug"):
            active_slugs.add(v["slug"])

    def _slug(route, kind):
        s = ("uiux-" + (route or "").strip("/").replace("/", "-") + "-" + (kind or "issue")).lower()
        s = re.sub(r"[^a-z0-9-]+", "-", s).strip("-")[:60]
        return s or "uiux-audit"

    env = dict(os.environ)
    started, skipped, triggered = 0, 0, []
    for f in fails:
        if started >= cap:
            break
        slug = _slug(f.get("route", ""), f.get("kind", "issue"))
        if slug in active_slugs:
            skipped += 1
            continue
        try:  # open PR on this deterministic branch already? then it's covered — skip
            chk = subprocess.run(["gh", "pr", "list", "-R", repo, "--head", "feat/" + slug,
                                  "--state", "open", "--json", "number"],
                                 capture_output=True, text=True, timeout=60, env=env)
            if chk.returncode == 0 and json.loads(chk.stdout or "[]"):
                skipped += 1
                continue
        except Exception:
            pass
        fr = ("[UI/UX 自動稽核] %s — %s。請依 app-uiux-designer rubric 修正此問題(純前端 dashboard,"
              "不動後端 API);修好後同一畫面應通過 AI 語意 gate。" % (f.get("route", ""), f.get("detail", "")))
        sr = _curl_json("POST", engine + "/sdlc-code-flow",
                        {"feature_request": fr, "repo": repo, "base": target_base,
                         "slug": slug, "uiFacing": "true"}, 60)
        if sr.get("id"):
            started += 1
            triggered.append(slug)
        else:
            skipped += 1
    return {"findings": len(data.get("findings", [])), "fails": len(fails),
            "started": started, "skipped": skipped, "triggered": triggered, "cap": cap}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self._send(200, {"ok": True})
        elif self.path == "/skills":
            # Skill catalogue for the designer's node picker: every dir in SKILLS_DIR
            # holding a SKILL.md. Only the agent container mounts the skills volume,
            # so the read-API proxies this instead of listing a dir it doesn't have.
            skills_dir = os.environ.get("SKILLS_DIR", "")
            names = []
            if skills_dir and os.path.isdir(skills_dir):
                for entry in sorted(os.listdir(skills_dir)):
                    if os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md")):
                        names.append(entry)
            self._send(200, {"skills": names})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        task = self.path.rsplit("/", 1)[-1]
        if task not in PROMPTS and task not in ("release", "execute", "publish-flow", "implement", "test", "uiux-audit"):
            return self._send(404, {"error": f"unknown task {task}"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})
        try:
            if task == "release":
                result = run_release(payload)
            elif task == "execute":
                result = run_claude_generic(payload)
            elif task == "publish-flow":
                result = publish_flow(payload)
            elif task == "implement":
                result = implement_flow(payload)
            elif task == "test":
                result = test_flow(payload)
            elif task == "uiux-audit":
                result = uiux_audit_flow(payload)
            else:
                result = run_claude(task, payload)
            self._send(200, result)
        except subprocess.TimeoutExpired:
            self._send(504, {"error": "task timeout"})
        except RateLimitError as e:
            # distinct 429 so the worker can back off + not burn the instance's retries
            self._send(429, {"error": str(e), "rate_limited": True})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print("[agent-task-node] " + (fmt % args), flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    print(f"[agent-task-node] listening on :{port} (claude={CLAUDE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
