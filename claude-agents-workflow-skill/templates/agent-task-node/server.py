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
    "intake": {"sufficient": True, "understanding": "stub", "openQuestions": [], "assumptions": [], "outOfScope": []},
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
    "intake": {
        "type": "object",
        "properties": {
            # Not a decision about whether to build — that is preflight's (cheap, before
            # spend) and PmReview's (expensive, after artifacts). This says only whether the
            # requirement is understood well enough for someone to write a spec from it.
            "sufficient": {"type": "boolean"},
            "understanding": {"type": "string"},
            "openQuestions": {"type": "array", "items": {"type": "object", "properties": {
                "question": {"type": "string"},
                "why": {"type": "string"},
                # A question that BLOCKS cannot be answered by an assumption: proceeding on a
                # guess here produces work that is confidently wrong rather than visibly
                # incomplete.
                "blocking": {"type": "boolean"}},
                "required": ["question"]}},
            "assumptions": {"type": "array", "items": {"type": "object", "properties": {
                "assumption": {"type": "string"}, "because": {"type": "string"}},
                "required": ["assumption"]}},
            "outOfScope": {"type": "array", "items": {"type": "string"}},
            # New work or a continuation, CHECKED against what this product has actually
            # run — not copied from the submitter's tick. `verified` says whether the claim
            # was confirmed against that list, so a downstream reader can tell a checked
            # answer from an unchecked one.
            "continuation": {"type": "object", "properties": {
                "kind": {"type": "string", "enum": ["new", "continue"]},
                "slug": {"type": "string"},
                "verified": {"type": "boolean"},
                "why": {"type": "string"}},
                "required": ["kind", "verified"]},
        },
        "required": ["sufficient", "understanding", "openQuestions"],
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
             "scenarioActors": '{"employee":"wang:pw","manager":"lin:pw","admin":"boss:pw","finance":"wang:pw"}'},
    "nav": {"navPath": "dashboard/src/app/core/navigation/nav.config.ts",
            "routesPath": "dashboard/src/app/app.routes.ts"},
    "personas": ["簽核者", "申請人", "管理員"],
    "qualityBar": {"coverage": 80, "archQube": 90},
}


def _deep_merge(base, over):
    """`over` onto `base`, recursively. Returns `base`, mutated.

    A one-level update() replaces whole sub-trees: a profile setting `sim.readApi.login`
    silently deleted every other key under `sim.readApi`. The loss is invisible — the caller
    reads a default that is no longer there and gets "" — so it presents as the feature never
    having worked rather than as a config that overwrote its neighbours.
    """
    for k, v in (over or {}).items():
        if k.startswith("$"):
            continue  # $repo / $branch are identity claims, checked elsewhere, never merged
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def _registry_project(repo, branch):
    """Ask the platform's project registry about this (repo, branch).

    Returns {"asked": False} when no registry is configured — the pipeline then falls back to
    the hardcoded allowlist, marked second-class in the report, exactly as a declared gate
    list is. Returns {"error": ...} when a registry IS configured and cannot be reached: that
    must never degrade into "not registered" (which refuses everything) nor into the
    allowlist (which is the copy the registry exists to replace). Both are answers a caller
    has to make on purpose.
    """
    url = (os.environ.get("SDLC_REGISTRY_URL") or "").rstrip("/")
    if not url:
        return {"asked": False}
    if not url.startswith("http"):
        url = "http://" + url
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=15) as r:
            body = json.load(r)
    except Exception as e:
        return {"asked": True, "error": str(e)}
    if body.get("error"):
        return {"asked": True, "error": body["error"]}
    match = next((p for p in (body.get("projects") or [])
                  if (p.get("repo") or "").lower() == repo.lower()
                  and (p.get("integrationBranch") or "") == branch), None)
    return {"asked": True, "project": match}


def _required_cells(payload, workdir):
    """The verification dimensions each of this product's flows MUST have covered.

    Derived from BPMN structure by the same script the gate runs, so it is available the
    moment the flow exists — before any code is written, and without a diff to ground it.

    This is the half of the exam paper that is worth handing over early. The other half —
    generated Playwright cases — cannot move: `_gen_testcases` grounds itself in `gh pr
    diff` to get the real routes and selectors, and before implement there is no PR, so an
    early version would invent the selectors it exists to avoid inventing.

    Returns {flow: [cells]} or {} when the product ships no derivation script.
    """
    script = os.path.join(workdir or "", "scripts/scenario-matrix.py")
    if not workdir or not os.path.isfile(script):
        return {}
    prof = _load_profile(payload).get("flow", {})
    env = dict(os.environ)
    env["SM_CODE_ROOT"] = workdir
    env["SCENARIO_JSON"] = "1"
    for k, v in (("SM_FLOW_DIR", prof.get("flowDir")),
                 ("SM_SIM_DIR", prof.get("scenarioDir")),
                 ("SCENARIO_PROFILE", prof.get("scenarioProfile"))):
        if v:
            env[k] = str(v)
    try:
        r = subprocess.run(["python3", script], capture_output=True, text=True,
                           timeout=120, env=env, cwd=workdir)
        return (json.loads(r.stdout or "{}") or {}).get("cellsRequired", {}) or {}
    except Exception as e:
        print("[agent-task-node] required-cells unavailable: %s" % e, flush=True)
        return {}


def _acceptance_brief(payload, workdir):
    """What this implementation will be judged against, stated BEFORE it is written.

    TDD's value is not that tests exist — it is that the specification becomes executable
    ahead of the implementation, so the implementation is constrained by it. For a model the
    working half of that mechanism is simply KNOWING THE ACCEPTANCE CRITERIA IN ADVANCE; a
    red bar first is the human-facing half.

    Implement used to receive srs / sdd / uiuxSpec / rework_feedback / manager_notes and
    nothing about how it would be checked, while `_gen_testcases` ran afterwards inside the
    test node — a second AI session re-reading the same SRS. That is not merely test-after;
    the exam and the answer share a source.

    So the two halves are labelled honestly rather than blurred:

      requiredCells is DETERMINISTIC and independent. It comes from the flow's structure,
      not from anyone's reading of the spec, so it is the one constraint that cannot be
      satisfied by re-interpreting the SRS the same way twice.

      The acceptance criteria come from the SRS, which the pipeline itself wrote. They
      constrain, and they do not independently verify. Saying so is the difference between
      a check and a reminder that looks like one.
    """
    parts = []
    srs = payload.get("srs") or (payload.get("design") or {}).get("srs")
    if srs:
        txt = json.dumps(srs, ensure_ascii=False) if isinstance(srs, (dict, list)) else str(srs)
        parts.append(
            "\n## 你將被什麼檢驗 —— 驗收條件(來自 SRS,實作前就已存在)\n"
            "```json\n" + txt[:6000] + "\n```\n"
            "這些條件是本次 PR 的及格線,不是參考資料。動手前先讀完,"
            "並在交付說明裡逐條說明你如何滿足它們。\n"
            "> 注意:這份 SRS 是本管線自己產出的,所以它**約束**你,但它**不是獨立驗證**——"
            "同一份規格被讀兩次不會變成兩個證據。\n")
    cells = _required_cells(payload, workdir)
    if cells:
        lines = "\n".join("- `%s`:%s" % (f, "、".join(c)) for f, c in sorted(cells.items()) if c)
        if lines:
            parts.append(
                "\n## 你將被什麼檢驗 —— 必須覆蓋的驗證維度(從流程結構確定性推導)\n"
                + lines + "\n"
                "若本次改動觸及上列任何流程,該流程的每一個維度都必須有**可證偽**的情境覆蓋"
                "(反例真的被拒、對照組真的分歧),否則情境閘會擋下這個 PR。\n"
                "> 這一份**不是**任何人對規格的詮釋,是從 BPMN 結構機械導出的——"
                "所以它是唯一無法靠「把同一份 SRS 再讀一次」滿足的約束。\n")
    return "".join(parts)



def _flow_inventory(payload, workdir):
    """Which business flows this product has, and where their verification stands.

    Mechanical: the flow files plus the gate's own derivation. "Progress" stated as a
    number nobody can trace is the kind of context that makes a model more confident about
    something possibly wrong, so this reports flows and uncovered cells or it reports that
    it could not look.
    """
    cells = _required_cells(payload, workdir)
    if not cells:
        return None
    prof = _load_profile(payload).get("flow", {})
    script = os.path.join(workdir or "", "scripts/scenario-matrix.py")
    uncovered = {}
    try:
        env = dict(os.environ)
        env.update({"SM_CODE_ROOT": workdir, "SCENARIO_JSON": "1"})
        for k, v in (("SM_FLOW_DIR", prof.get("flowDir")),
                     ("SM_SIM_DIR", prof.get("scenarioDir")),
                     ("SCENARIO_PROFILE", prof.get("scenarioProfile"))):
            if v:
                env[k] = str(v)
        r = subprocess.run(["python3", script], capture_output=True, text=True,
                           timeout=120, env=env, cwd=workdir)
        uncovered = (json.loads(r.stdout or "{}") or {}).get("uncovered", {}) or {}
    except Exception:
        uncovered = {}
    return {"flows": sorted(cells), "requiredCells": cells, "uncovered": uncovered}



def _existing_features(payload):
    """What has already been built (or is being built) FOR THIS REPO, from the Data Index.

    Mechanical, and it exists so the intake node can CHECK the answer to "is this new or a
    continuation" rather than believe it. A person reaching for this pipeline rarely
    remembers whether a slug was used eighteen months ago; two features in this product have
    already been started twice, and nothing asked.

    Keyed on (repo, slug) — a slug names a feature within a product, not across products.
    """
    di = (os.environ.get("SIM_DATA_INDEX_URL") or os.environ.get("DATA_INDEX_URL")
          or os.environ.get("TEST_DATAINDEX") or "").rstrip("/")
    repo = str(_pv(payload, "repo")).strip()
    if not (di and repo):
        return None
    if not di.startswith("http"):
        di = "http://" + di
    q = ('{ ProcessInstances(where:{processId:{equal:"sdlc-code-flow"}, '
         'state:{in:[ACTIVE,COMPLETED]}}){ id state variables } }')
    try:
        import urllib.request
        req = urllib.request.Request(di + "/graphql",
                                     data=json.dumps({"query": q}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = (json.load(r).get("data") or {}).get("ProcessInstances") or []
    except Exception as e:
        print("[agent-task-node] existing-features unavailable: %s" % e, flush=True)
        return None
    out = []
    for i in rows:
        v = i.get("variables")
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except Exception:
                v = {}
        v = v or {}
        slug = (v.get("slug") or "").strip()
        if not slug or (v.get("repo") or "").lower() != repo.lower():
            continue
        out.append({"slug": slug, "state": i.get("state"), "instance": i.get("id"),
                    "hasPr": bool(v.get("pr")),
                    "request": (str(v.get("feature_request") or ""))[:120]})
    return out or []


def project_context(payload, workdir=None):
    """What project this work belongs to — assembled from the tree and the running system,
    never from the model's recollection.

    SA writes the specification, and until now it received exactly `feature_request`, `repo`,
    `base`, `slug` and `uiFacing`. It did not know what the product IS, what it already does,
    what else is being built alongside, or where verification stands. Meanwhile PmReview —
    the LAST node — got the siblings list and the whole app navigation map. The context was
    arriving four AI sessions after the node that most needed it, which is why an SRS so
    often reads like the spec of a standalone tool rather than the Nth feature of a product.

    Every entry is either extracted or reported ABSENT. A plausible-sounding narrative in
    place of a missing fact is the worst possible filler here: downstream cannot tell it from
    the real thing, and it makes four subsequent nodes more confident about something nobody
    checked. Same rule as the gates — could-not-look is not the same as nothing-there.
    """
    out, missing = {}, []
    prof = _load_profile(payload)

    # Only when the profile was actually READ. `_load_profile` falls back to aaf's defaults,
    # so a product that declared nothing would otherwise be described to its own design nodes
    # using aaf's personas — the exact "absent configuration means use aaf's" the whole
    # generalisation effort removed, reintroduced here as context.
    personas = prof.get("personas") if prof.get("_ref") else None
    if personas:
        out["personas"] = personas
    else:
        missing.append("personas (.arcana/project.json not read for this repo)")

    app_map = _fetch_app_map(payload)
    if app_map:
        out["existingFeatures"] = app_map[:4000]
    else:
        missing.append("app navigation map")

    sibs = payload.get("siblings")
    if sibs:
        out["inFlight"] = str(sibs)[:2000]
    elif payload.get("backlogId"):
        missing.append("sibling features (backlogId set but none returned)")

    notes = payload.get("manager_notes") or payload.get("managerNotes")
    if notes:
        out["humanNotes"] = str(notes)[:2000]

    feats = _existing_features(payload)
    if feats is None:
        missing.append("this product's existing features (Data Index unreachable)")
    elif feats:
        out["alreadyBuilt"] = feats[:40]

    inv = _flow_inventory(payload, workdir)
    if inv:
        out["flows"] = inv["flows"]
        out["verificationGaps"] = inv["uncovered"] or "(none — every required cell covered)"
    else:
        missing.append("flow inventory / verification coverage")

    return {"context": out, "unavailable": missing}


def project_brief(payload, workdir=None):
    """`project_context` as prose for a prompt, with the gaps named rather than smoothed over."""
    pc = project_context(payload, workdir)
    ctx, missing = pc["context"], pc["unavailable"]
    if not ctx and not missing:
        return ""
    parts = ["\n## 這個專案是什麼 —— 你正在其中工作的產品現況\n",
             "以下每一項都是從樹裡或執行中的系統**機械擷取**的,不是任何人的敘述。\n"]
    label = {"personas": "使用者角色", "existingFeatures": "已存在的功能與路由",
             "alreadyBuilt": "這個產品已經跑過(或正在跑)的 feature —— 用來判斷這是新案還是延續",
             "inFlight": "同批正在開發的功能", "humanNotes": "人類在此功能上留下的指示",
             "flows": "本產品的業務流程", "verificationGaps": "尚未被可證偽情境覆蓋的驗證維度"}
    for k, v in ctx.items():
        body = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        parts.append("\n### %s\n%s\n" % (label.get(k, k), body))
    if missing:
        parts.append(
            "\n### 取不到的部分(**不要據此想像**)\n"
            + "".join("- %s\n" % m for m in missing)
            + "上列資訊本次無法取得。缺少的事實請當成**未知**處理:需要它才能決定的設計,"
              "請明確列為待確認問題,不要用聽起來合理的假設補位。"
              "一段編造的專案現況與真的無法區分,而它會讓後面每一個節點更確信一件可能錯的事。\n")
    return "".join(parts)




def _intake_form_section(p):
    """The human's answers, and what was asked of them last round.

    A round that cannot see the previous one just asks the same questions again — the loop
    then costs the person time and returns nothing, which is how a human-in-the-loop step
    gets removed for being annoying rather than for being wrong.
    """
    raw = p.get("intakeForm")
    rnd = p.get("intakeRound") or 0
    if not raw:
        return "\n## 表單狀態\n第 1 輪,尚無填答內容。\n"
    try:
        form = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        form = {"(unparsed)": str(raw)[:2000]}
    label = {"feature_request": "需求描述", "target_users": "服務對象", "placement": "放在哪裡",
             "acceptance": "怎麼算做完", "out_of_scope": "這次不做什麼",
             "pm_answers": "對上輪追問的回覆", "pm_questions": "上輪的追問",
             "pm_assumptions": "上輪採取的假設"}
    parts = ["\n## 使用者填答(第 %s 輪)\n" % (int(rnd) + 1)]
    for k, v in (form or {}).items():
        if v not in (None, "", [], {}):
            parts.append("\n### %s\n%s\n" % (label.get(k, k),
                         json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v))
    parts.append(
        "\n**這一輪的規則**:上面「對上輪追問的回覆」若已回答某題,該題就**不要再問**。"
        "只問**這次填答之後仍然無法決定**的事。重複追問已經回答過的東西,會讓這個迴圈"
        "變成消耗對方時間而不產出資訊 —— 那正是這種人機迴圈被移除的原因,"
        "而它被移除的理由通常是「很煩」,不是「它錯了」。\n")
    return "".join(parts)


def prompt_intake(p):
    """The intake (front PM) node: understand the project, then say what is still UNKNOWN.

    Its output is not a decision — admission is preflight's job (cheap, before spend) and
    acceptability is PmReview's (expensive, after artifacts exist). Putting a judgement here
    would answer "should we build this" twice, both times on insufficient evidence.

    What it does is the thing nothing else does: turn "under-specified" from an invisible
    condition into a written list. Today a request like "make a coverage screen" reaches SA
    with no product context, SA silently picks answers for everything the sentence left out,
    and those picks arrive downstream indistinguishable from requirements. The picks may even
    be good — the problem is nobody can tell which parts were decided and which were guessed.

    So: questions go to the human channel this feature already owns (`feature:<slug>`), and
    anything still unanswered becomes a NAMED ASSUMPTION that travels with the spec. An
    assumption someone can read and correct is worth incomparably more than the same choice
    made silently.
    """
    return (
        "你是這個產品的 PM。任務**不是**決定要不要做,而是把「這個需求在這個產品裡到底是什麼」"
        "弄清楚,並且把**還不清楚的部分明確列出來**,讓後面寫規格的人有依據、而不是自己猜。\n\n"
        "## 需求(原始輸入)\n" + str(p.get("feature_request") or p.get("goal") or "(未提供)") + "\n"
        + _intake_form_section(p)
        + project_brief(p, _ensure_checkout(p) if p.get("_piid") else p.get("_workdir"))
        + "\n## 你要產出什麼\n"
        "1. `understanding`:用產品的語言重述這個需求 —— 它服務哪個角色、放在現有 IA 的哪裡、"
        "與已存在的哪些功能相鄰或重疊。**只根據上面機械擷取的事實**,不要引入你的先驗印象。\n"
        "2. `openQuestions`:**做這件事必須知道、但目前資料回答不了的問題**。每一條要具體到"
        "能被一句話回答(不是「範圍為何」,而是「這個畫面要不要顯示已退休的流程?」)。"
        "沒有問題就給空陣列 —— 不要為了看起來嚴謹而湊。\n"
        "3. `assumptions`:每一條未決問題,你**為了讓工作能繼續**而採取的立場,以及為什麼。"
        "這些會原樣傳給 SA,並且會被當成**假設而非需求**看待。\n"
        "4. `outOfScope`:明確不做的事 —— 界線沒畫,範圍就會在 implement 階段自己長大。\n"
        "5. `continuation`:`{\"kind\": \"new|continue\", \"slug\": \"…\", \"verified\": true|false, \"why\": \"…\"}`"
        " —— 這是新案還是延續既有 feature。**必須拿上面『這個產品已經跑過的 feature』清單查證,"
        "不得照抄填答者的勾選**。兩個方向的錯不對稱:當成新案會重做已經做過的事(浪費,但看得見);"
        "當成延續會把改動疊到別人的工作區上(可能不可逆,而且沒人會發現)。\n"
        "  · 填答說「延續」但該 slug 不在清單裡 → `verified:false`,並列為 **blocking** 問題,"
        "不要靜默改判成新案。\n"
        "  · 填答說「新案」但清單裡有名稱或描述高度相近的 → 也要問,"
        "因為本產品已經有兩個 feature 被起過兩次,而每次都沒有人被問過。\n"
        "  · 清單本身取不到 → `verified:false` 並說明無法查證,不得假裝查過。\n\n"
        "## 紀律\n"
        "- 上面標為「取不到」的資訊,就是**未知**。不得用聽起來合理的敘述補位:"
        "一段編造的專案現況與真的無法區分,而它會讓後面每個節點更確信一件可能錯的事。\n"
        "- 若某個問題不被回答就**無法**負責任地繼續,把它放進 `blocking: true`。\n"
        "- 重述必須可被對照:引用你依據的是哪一條擷取到的事實。\n"
    )


def post_open_questions(payload, questions):
    """Put the intake node's questions where a human will actually see them.

    Reuses the channel this feature already has — `feature:<slug>`, the same thread
    `manager_notes` reads back at implement and pm-review — rather than inventing a second
    place for humans to look. A question filed somewhere nobody reads is the same as no
    question, and this pipeline already learned that lesson once: before that thread existed,
    the only human input to a running feature was HOLD, which stops the round.
    """
    slug = str(_pv(payload, "slug")).strip()
    api = (os.environ.get("READ_API") or os.environ.get("TEST_API_TARGET") or "").rstrip("/")
    if not (slug and api and questions):
        return {"posted": 0, "reason": "no slug / no read-API / no questions"}
    if not api.startswith("http"):
        api = "http://" + api
    body = ("【PM 待確認】此功能在規格開始前有以下未決問題。未回答者將以 intake 節點列出的"
            "假設繼續,並在 SRS 中標為假設而非需求:\n"
            + "".join("%d. %s\n" % (i, q) for i, q in enumerate(questions, 1)))
    try:
        import urllib.request
        req = urllib.request.Request(
            api + "/api/v1/designer/chat/note",
            data=json.dumps({"kind": "feature", "id": slug, "text": body}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"posted": len(questions), "status": r.status}
    except Exception as e:
        # Best-effort: the questions still travel in the node's output and into SA's prompt.
        print("[agent-task-node] could not post open questions: %s" % e, flush=True)
        return {"posted": 0, "error": str(e)}



def dispose_pr(payload):
    """Close out this run's PR according to how the run ended.

    A PR's life was tied to nothing. The flow finished — merged, rejected, escalated,
    aborted — and the PR stayed open regardless, so the queue only ever grew: 42 open PRs,
    of which today's audit found five already landed by other routes and thirteen produced
    by a single fan-out in July. Nobody was neglecting them; nothing had ever been
    responsible for closing them.

    Three endings, three dispositions, and the difference matters to whoever reads the queue:

      GO       — leave it. StartMerge hands it to merge-flow; closing it here would race.
      NOGO     — close it, with the reason. Work that was judged not good enough should not
                 sit in the queue looking like work awaiting review.
      HOLD     — convert to draft and say who is being waited on. A HOLD is a question for a
                 human, and a question nobody can see is not a question.

    An open PR should mean "someone could act on this". Anything else erodes that, and a
    queue nobody trusts gets ignored wholesale — which is what happened here.
    """
    # The verdict is not its own variable: the PM node writes one JSON blob into `pmReview`
    # and the gateway greps that string for "verdict":"GO". Read it the same way rather than
    # inventing a field, so this node and the gateway can never disagree about what happened.
    review_raw = str(_pv(payload, "pmReview") or "")
    verdict, feedback = "", ""
    try:
        j = json.loads(review_raw) if review_raw.strip().startswith("{") else {}
        verdict = str(j.get("verdict") or "").strip().upper()
        feedback = str(j.get("feedback") or "")[:1500]
    except Exception:
        pass
    if not verdict:
        # Same tolerance for whitespace the gateway uses.
        flat = review_raw.replace(" ", "").replace("\n", "")
        for v in ("GO", "NOGO", "HOLD"):
            if '"verdict":"%s"' % v in flat:
                verdict = v
                break
        # NOGO contains GO as a substring; the loop checks GO first, so re-check.
        if verdict == "GO" and '"verdict":"NOGO"' in flat:
            verdict = "NOGO"
    if not feedback:
        feedback = str(_pv(payload, "feedback") or "")[:1500]

    url, _ = _pr_url_and_branch(payload)
    if not url:
        raw = str(_pv(payload, "pr") or "")
        if raw.strip().startswith("{"):
            try:
                url = str(json.loads(raw).get("prUrl") or "")
            except Exception:
                pass
        elif raw.startswith("http"):
            url = raw.strip()
    slug = str(_pv(payload, "slug")).strip()
    if not url:
        return {"disposed": False, "reason": "no PR for this instance", "verdict": verdict}
    if verdict == "GO":
        return {"disposed": False, "reason": "GO — left open for merge-flow", "verdict": verdict,
                "pr": url}

    iid = payload.get("_piid") or ""
    if verdict == "NOGO":
        body = ("【自動關閉 — PM 判定 NOGO】\n\n"
                "本輪的 PM 節點判定這份交付不足以出貨,而重試次數已用盡。\n\n"
                "關閉而不是留著,是因為一個開著的 PR 應該代表「有人可以對它動手」。"
                "一份已被判定不足、又沒有人在處理的 PR 留在佇列裡,會讓整個佇列變得不可信 —— "
                "而不可信的佇列會被整批忽略。\n\n"
                "PM 的理由:\n" + (feedback or "(未提供)") + "\n\n"
                "要續作請重開,或以同一 slug 重跑一輪(`%s`)。" % slug)
        r = subprocess.run(["gh", "pr", "close", url, "--comment", body],
                           capture_output=True, text=True, timeout=60)
        return {"disposed": r.returncode == 0, "action": "closed", "verdict": verdict,
                "pr": url, "error": (r.stderr or "")[-200:] if r.returncode else None}

    # HOLD, or a run that ended without a verdict at all (aborted, escalated, crashed).
    why = "PM 判定 HOLD — 需要人裁決" if verdict == "HOLD" else \
          "流程結束時沒有 PM 判定(中止或升級)"
    body = ("【自動轉為草稿 — %s】\n\n"
            "這份 PR 在等一個人,而不是在等審查。轉成草稿是為了讓佇列裡「可以動手的」與"
            "「在等人回答的」分得開 —— 一個沒有人看得見的問題,不是問題。\n\n"
            "實例:%s\nslug:%s\n\n"
            "PM 的說明:\n%s\n\n"
            "裁決後把它轉回 ready 即可繼續。" % (why, iid, slug, feedback or "(未提供)"))
    subprocess.run(["gh", "pr", "comment", url, "--body", body],
                   capture_output=True, text=True, timeout=60)
    r = subprocess.run(["gh", "pr", "ready", url, "--undo"], capture_output=True, text=True, timeout=60)
    return {"disposed": r.returncode == 0, "action": "converted to draft", "verdict": verdict or "(none)",
            "pr": url, "error": (r.stderr or "")[-200:] if r.returncode else None}


def preflight(payload):
    """Can this pipeline legitimately run against this repo? Answered in seconds, before a
    single AI session is paid for. Returns {"ok": bool, "reason": str, "checks": [...]}.

    The allowlist was checked in `implement` only — the FOURTH node. SA, SD and uiux had
    already run, so a repo the pipeline was never allowed to touch cost three full sessions
    before anything said no. Everything here is `gh api` and file reads.

    The strongest check is that every path the profile DECLARES actually exists at the ref.
    It uses the same information the gates need later, verified once up front — and it kills
    the wrong-tree false green at the source rather than detecting it downstream: a gate
    pointed at a directory that does not exist cannot report "found nothing" if the run never
    started.

    A `$repo` / `$branch` in the profile is an identity claim, and a mismatch is a REFUSAL,
    not something to merge around. It catches the most common way a profile ends up lying:
    copied from another repo.
    """
    checks, repo = [], str(_pv(payload, "repo")).strip()
    base = str(_pv(payload, "base", "main")).strip()
    _, pr_branch = _pr_url_and_branch(payload)
    ref = pr_branch or base

    def fail(reason):
        return {"ok": False, "reason": reason, "checks": checks, "repo": repo, "ref": ref}

    if not repo:
        return fail("no repo declared — nothing to check this pipeline against")

    # May this pipeline spend on this repo? The registry is the authority; the hardcoded
    # allowlist is a copy of the answer, in another language, in another repo. Same
    # first-class/second-class split the gate policy uses: asked beats declared, and which
    # one answered is recorded, because a copy can disagree while looking like agreement.
    reg = _registry_project(repo, base)
    if reg.get("error"):
        return fail("project registry unreachable (%s) — refusing rather than falling back to "
                    "the hardcoded allowlist, which is a copy that can disagree with it"
                    % reg["error"])
    if reg.get("asked"):
        proj = reg.get("project")
        if not proj:
            return fail("no registered SDLC project for %s@%s — register it (status starts at "
                        "'onboarding') before the pipeline may spend on it" % (repo, base))
        if proj.get("status") != "active":
            return fail("project %r is %r, not 'active' — registered is not the same as "
                        "authorised to spend" % (proj.get("projectId"), proj.get("status")))
        checks.append("registry: %s (%s, %s)" % (proj.get("projectId"), proj.get("tier"),
                                                 proj.get("status")))
        payload["_sdlc_project"] = proj
    else:
        if repo not in IMPLEMENT_REPO_ALLOWLIST:
            return fail("repo %r is not in the pipeline allowlist %s (checked BEFORE any AI "
                        "session, not at implement)" % (repo, sorted(IMPLEMENT_REPO_ALLOWLIST)))
        checks.append("allowlist: ok (second-class — SDLC_REGISTRY_URL unset, so this is a "
                      "hardcoded copy of what the registry knows)")

    prof = _load_profile(payload)
    declared = prof.get("_ref")
    checks.append("profile: %s" % ("read from " + declared if declared else
                                   "absent — running on defaults"))

    # Identity. A profile that names a different repo is a copy, and the copy's paths describe
    # a tree that is not this one.
    for key, want, what in (("$repo", repo, "repo"), ("$branch", base, "branch")):
        claim = str(prof.get(key) or "").strip()
        if claim and claim.lower() != want.lower():
            return fail("profile claims %s %r but this run is %r — a profile copied from "
                        "another project describes a tree that is not this one" % (what, claim, want))
    if declared:
        checks.append("identity: ok")

    # Every declared path must exist at this ref. This is the one that removes the wrong-tree
    # false green: the gate later reads these same paths.
    paths = [p for p in [
        prof.get("app", {}).get("appDir"),
        prof.get("nav", {}).get("navPath"),
        prof.get("nav", {}).get("routesPath"),
        prof.get("flow", {}).get("flowDir"),
        prof.get("flow", {}).get("scenarioDir"),
    ] if p]
    missing = []
    for p in paths:
        # Existence only — no --jq. The contents API answers with an object for a file and an
        # ARRAY for a directory, so any jq path expression fails on one of the two, and the
        # failure looks exactly like "the path is missing". `appDir` is a directory; that is
        # how this first reported aaf's own tree as absent.
        r = subprocess.run(["gh", "api", f"repos/{repo}/contents/{p}?ref={ref}"],
                           capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            missing.append(p)
    if missing:
        return fail("declared path(s) do not exist at %s: %s — the gates would later read these "
                    "and report nothing found" % (ref, ", ".join(missing)))
    checks.append("paths: %d declared, all present at %s" % (len(paths), ref))

    return {"ok": True, "reason": "", "checks": checks, "repo": repo, "ref": ref,
            "profileRef": declared}


def _load_profile(payload):
    """The target repo's `.arcana/project.json` (run-recipe + nav paths + personas), merged over
    the dashboard defaults. Best-effort + cached on the payload. The single seam another app plugs
    into; absent → dashboard defaults (aaf unaffected).

    Two bugs meant this seam had never actually opened:

    `payload.get("repo")` is empty for every design node. `do_execute` — which drives SA, SD and
    uiux — nests the instance variables under `data`, so the repo was invisible here and the whole
    fetch was skipped by `if repo:`. Those three nodes have therefore always run on
    `_PROFILE_DEFAULTS` no matter what a repo declared, and nothing errored: it presented as "the
    model still guesses paths". `_pv` exists precisely for this and was already documented as the
    fix for the same class of bug elsewhere.

    And it read only the base ref, so the first PR to ADD a profile could not be judged under it —
    the same problem `_api_path_inventory` already solved by trying the PR ref first.
    """
    if "_profile" in payload:
        return payload["_profile"]
    import copy
    prof = copy.deepcopy(_PROFILE_DEFAULTS)
    repo = str(_pv(payload, "repo")).strip()
    base = str(_pv(payload, "base", "main")).strip()
    if repo:
        _, pr_branch = _pr_url_and_branch(payload)
        for ref in [r for r in (pr_branch, base) if r]:
            try:
                r = subprocess.run(
                    ["gh", "api", f"repos/{repo}/contents/.arcana/project.json?ref={ref}",
                     "--jq", ".content"],
                    capture_output=True, text=True, timeout=25)
                raw = "".join((r.stdout or "").split())
                if not raw:
                    continue
                loaded = json.loads(base64.b64decode(raw).decode("utf-8", "replace"))
                _deep_merge(prof, loaded)
                prof["_ref"] = ref
                break
            except Exception:
                continue
    payload["_profile"] = prof
    return prof


def _fetch_app_map(payload):
    """B (IA-redundancy critic): fetch the app's WHOLE navigation map (all existing top-level
    features + routes) at the BASE ref, so the PM can judge redundancy against EVERY existing
    feature — not just this initiative's `siblings`. This is what catches "a new 流程追蹤 view when
    流程監控 already lists those instances". Best-effort (empty on failure so the PM degrades to the
    siblings-only check). Paths default to the dashboard nav/routes; a per-app Project Profile can
    override navPath/routesPath (the generalization seam). Returns a compact string."""
    # `_pv`, not `.get` — this runs for the PM/design nodes, whose variables arrive under `data`.
    repo = str(_pv(payload, "repo")).strip()
    base = str(_pv(payload, "base", "main")).strip()
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
            # Check the exit code. Without it a gh error message gets base64-decoded into
            # mojibake and returned AS THE APP'S NAVIGATION MAP — 230 bytes of noise that the
            # caller cannot distinguish from a real answer, and that a model will dutifully
            # reason about. Absence of information presented as information.
            if r.returncode != 0:
                continue
            raw = "".join((r.stdout or "").split())
            if not raw:
                continue
            try:
                content = base64.b64decode(raw, validate=True).decode("utf-8")
            except Exception:
                continue
            if content:
                out.append(f"# {pth}\n{content[:3500]}")
        except Exception:
            pass
    return "\n\n".join(out)[:7000]



def _report_for_pm(report):
    """The test report as the PM should read it — and honest when it had to be shortened.

    2800 characters cut the report mid-JSON, so the PM was judging a fragment while it looked
    like the whole thing. The gate verdicts (which gate ran, which could not) live past that
    point, which means the node deciding GO/NOGO could not see the very evidence this branch
    spent its whole length making legible.
    """
    if report is None:
        return "(無)"
    s = report if isinstance(report, str) else json.dumps(report, ensure_ascii=False)
    if len(s) <= 40_000:
        return s
    return (s[:40_000] + "\n\n[!! 測試報告在此被截斷 —— 後面還有內容。"
            "未讀到的部分不得視為「沒有問題」,若判斷需要它請以 HOLD 要求完整報告 !!]")


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
        f"AI semantic gate + a GOAL-DIRECTED JOURNEY WALKTHROUGH on it): "
        f"{_report_for_pm(p.get('testReport'))}\n"
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


PROMPTS = {"intake": prompt_intake, "diagnose": prompt_diagnose, "fix": prompt_fix, "merge": prompt_merge, "sweep": prompt_sweep, "decide": prompt_decide, "analyze": prompt_analyze, "readmesync": prompt_readmesync, "escalate": prompt_escalate, "scan-stale": prompt_scan_stale, "rebase": prompt_rebase, "audit": prompt_audit, "pm-review": prompt_pm_review}


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


def _pv(payload, key, default=""):
    """A flow variable, wherever the dispatcher happened to put it.

    `do_implement` sends `repo`/`base`/`slug` at the top level; `do_execute` — which drives
    SA / SD / uiux — sends every instance variable nested under `data` instead. Code reading
    only the top level therefore worked for implement and silently did nothing for the design
    nodes: the repo checkout was never created and the grounding block never reached a prompt,
    while both looked wired. Nothing errored, so the failure presented as "the model still
    guesses paths" rather than "the fix never ran".
    """
    v = payload.get(key)
    if v in (None, ""):
        d = payload.get("data")
        if isinstance(d, dict):
            v = d.get(key)
    return v if v not in (None, "") else default


def _instance_root(piid):
    return os.path.join(WORK_ROOT, _safe_seg(piid)) if piid else None


def _freeze(path):
    """Seal a finished instance's workspace: it is that run's audit record.

    TAMPER-EVIDENT, NOT TAMPER-PROOF — and the difference is stated here because assuming the
    stronger property is how an audit trail becomes worthless without anyone noticing. This
    agent runs as root, and root ignores permission bits; `/work` is a bind mount, so the
    immutable attribute is unavailable too. Measured, not assumed: with `chmod -R a-w` applied,
    a write from this process still succeeded.

    So freezing does two things. `chmod -R a-w` stops ordinary tooling and accidental writes —
    real, just not sufficient. The manifest is what actually carries the guarantee: a SHA-256
    of every file, written at seal time, against which `_verify_frozen` can later prove whether
    the record still says what it said. Prevention needs a non-root runtime or a
    write-once store; until then, detection is the honest claim.
    """
    ok = True
    try:
        digests = {}
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in filenames:
                if fn in (".frozen.sha256", ".workspace.json"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, path)
                try:
                    h = hashlib.sha256()
                    with open(full, "rb") as fh:
                        for chunk in iter(lambda: fh.read(1 << 20), b""):
                            h.update(chunk)
                    digests[rel] = h.hexdigest()
                except OSError:
                    continue
        with open(os.path.join(path, ".frozen.sha256"), "w") as f:
            json.dump({"sealedFiles": len(digests), "digests": digests}, f)
        marker = os.path.join(path, ".workspace.json")
        if os.path.isfile(marker):
            meta = json.load(open(marker))
            meta["frozen"] = True
            meta["sealedFiles"] = len(digests)
            with open(marker, "w") as f:
                json.dump(meta, f, ensure_ascii=False)
        subprocess.run(["chmod", "-R", "a-w", path], capture_output=True, timeout=120)
    except Exception as e:
        ok = False
        print("[agent-task-node] could not seal %s: %s" % (path, e), flush=True)
    return ok


def _verify_frozen(path):
    """Does a sealed workspace still hold what it held? Returns (ok, [changed paths])."""
    man = os.path.join(path, ".frozen.sha256")
    if not os.path.isfile(man):
        return False, ["(never sealed)"]
    digests = json.load(open(man)).get("digests", {})
    bad = []
    for rel, want in digests.items():
        full = os.path.join(path, rel)
        try:
            h = hashlib.sha256()
            with open(full, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            if h.hexdigest() != want:
                bad.append(rel)
        except OSError:
            bad.append(rel + " (missing)")
    return (not bad), bad


def _copy_tree(src, dst):
    """Copy a previous workspace. Reflink (copy-on-write) when the filesystem offers it,
    otherwise a real copy.

    Explicitly NOT hardlinks: they share inodes, so an append or an in-place edit in the new
    run would rewrite the frozen original — a silent violation of the one property this whole
    scheme exists to provide, and one nobody would notice until an audit asked.
    """
    r = subprocess.run(["cp", "-a", "--reflink=auto", src, dst], capture_output=True, text=True, timeout=1800)
    if r.returncode == 0:
        return True, "reflink/copy"
    r = subprocess.run(["cp", "-a", src, dst], capture_output=True, text=True, timeout=1800)
    return (r.returncode == 0), ("copy" if r.returncode == 0 else (r.stderr or "")[-200:])


def _resolve_workspace_source(payload):
    """Which previous instance this run continues from.

    Explicit `workspaceFrom` (an instance id) or the sentinel "latest" — the newest frozen
    workspace carrying the same (repo, slug). Anything else (absent / "new") starts clean.
    Declared at START, per the flow contract: a run that discovers its own history halfway
    through cannot be reasoned about, and a default of "whatever was most recently on disk"
    would make two identical starts behave differently.

    The key is (repo, slug), not slug. A slug names a feature within a product; `dark-mode`
    in one repo is not the continuation of `dark-mode` in another. Inheriting across products
    hands SA/SD/uiux another product's tree as their ground truth — and they would not
    notice, because a workspace looks exactly like a workspace.

    A marker with no `repo` is not adoptable once the payload declares one: it cannot be
    shown to be about this product, and starting clean is the recoverable error where
    continuing from the wrong tree is not. Markers written from here on carry it, so this
    self-heals.
    """
    want = str(_pv(payload, "workspaceFrom")).strip()
    if not want or want in ("new", "none"):
        return None
    piid = payload.get("_piid") or ""
    if want != "latest":
        src = _instance_root(want)
        return src if src and os.path.isdir(src) else None
    slug = str(_pv(payload, "slug")).strip()
    repo = str(_pv(payload, "repo")).strip()
    if not slug:
        return None
    best, best_mt = None, -1
    try:
        for name in os.listdir(WORK_ROOT):
            if name == _safe_seg(piid):
                continue
            root = os.path.join(WORK_ROOT, name)
            marker = os.path.join(root, ".workspace.json")
            if not os.path.isfile(marker):
                continue
            try:
                meta = json.load(open(marker))
            except Exception:
                continue
            # Only a FROZEN workspace is a safe source: an unfrozen one may still be being
            # written by a live run, and copying it mid-write yields a state that never existed.
            if meta.get("slug") != slug or not meta.get("frozen"):
                continue
            if repo and str(meta.get("repo") or "").lower() != repo.lower():
                continue
            mt = os.path.getmtime(marker)
            if mt > best_mt:
                best, best_mt = root, mt
    except OSError:
        return None
    return best


def _ensure_instance_workspace(payload):
    """Create this instance's workspace once, copying a previous run when asked.

    The workspace is per INSTANCE, not per node: SA / SD / uiux / implement all work in the
    same checkout, so a design node can `ls` the code it is designing against instead of being
    handed a lossy description of it. Nodes previously each got their own empty directory,
    which is why SD spent minutes calling `gh api` to rediscover a repo layout every run — and
    still wrote file paths that do not exist.
    """
    piid = payload.get("_piid")
    root = _instance_root(piid)
    if not root:
        return None
    marker = os.path.join(root, ".workspace.json")
    if os.path.isfile(marker):
        return root
    # `repo` is part of the workspace's identity, not decoration: without it a later
    # `workspaceFrom:"latest"` cannot tell which product this tree belongs to, and lineage
    # you cannot key on is lineage you cannot trust.
    meta = {"instance": piid, "slug": _pv(payload, "slug"), "repo": str(_pv(payload, "repo")).strip(),
            "from": None, "frozen": False}
    src = _resolve_workspace_source(payload)
    if src:
        ok, how = _copy_tree(src, root)
        if ok:
            # Writable again: the COPY is this run's scratch. The source stays frozen.
            subprocess.run(["chmod", "-R", "u+w", root], capture_output=True, timeout=300)
            meta["from"] = os.path.basename(src)
            meta["how"] = how
            # Freeze the source now that something descends from it. Lineage without
            # immutability is a citation to a document that can still be edited.
            _freeze(src)
            print("[agent-task-node] workspace %s copied from %s (%s)" % (piid, meta["from"], how), flush=True)
        else:
            meta["copyError"] = how
            print("[agent-task-node] workspace copy failed (%s) — starting clean" % how, flush=True)
    try:
        os.makedirs(root, exist_ok=True)
        with open(marker, "w") as f:
            json.dump(meta, f, ensure_ascii=False)
    except OSError:
        return None
    return root


def _feature_branch(payload, slug):
    """The branch a feature is developed on. One definition, because it is an identity.

    Branch namespaces are per-repo, so `feat/dark-mode` in two products is two branches and
    needs no product prefix. What DID diverge is that the branch was built from a
    configurable `branchPrefix` in one place and hardcoded as `"feat/" + slug` in the
    duplicate-PR check in another: set `branchPrefix` and that check queries a head that
    never exists, finds no open PR, and starts a duplicate child on every scan — silently,
    since "no PR found" and "no PR for the branch I guessed" look identical.
    """
    return "%s%s" % ((payload.get("branchPrefix") or "feat/").strip(), slug)


def _remote_repo(wd):
    """The `owner/name` an existing checkout actually points at, lowercased, or "" if it has
    no origin.

    `repo` is the GitHub `owner/name` form everywhere in this file (`gh -R`, the implement
    allowlist), so that is the identity to recover — and it is always the LAST TWO segments,
    which is what makes this robust across the shapes a remote can take: the clone here
    embeds a token (`https://x-access-token:...@host/o/n`), a human checkout may be
    `git@host:o/n.git` or `ssh://git@host/o/n`, and an enterprise host may carry a port.
    Peeling prefixes one rule at a time gets each of those subtly wrong (a port reads as a
    path segment); taking the tail does not.
    """
    r = subprocess.run(["git", "-C", wd, "remote", "get-url", "origin"],
                       capture_output=True, text=True, timeout=30)
    url = (r.stdout or "").strip()
    if r.returncode != 0 or not url:
        return ""
    parts = [p for p in re.split(r"[/:]", re.sub(r"\.git$", "", url)) if p]
    return "/".join(parts[-2:]).lower() if len(parts) >= 2 else ""


def _ensure_checkout(payload):
    """The instance workspace's git checkout — the ground every node stands on.

    Cloned once per instance (or inherited from the copied workspace), at `<instance>/repo`.

    An inherited checkout is only reusable if it is a checkout OF THE DECLARED REPO. It used
    to be enough that `.git` existed, which meant a workspace continued from another product
    silently made SA/SD/uiux reason about the wrong tree — the most expensive kind of wrong,
    because every node downstream treats a checkout as ground truth and nothing looks broken.
    Mismatch is not an error to report and continue past; it is re-cloned.
    """
    root = _ensure_instance_workspace(payload)
    repo = str(_pv(payload, "repo")).strip()
    if not root or not repo:
        return None
    wd = os.path.join(root, "repo")
    if os.path.isdir(os.path.join(wd, ".git")):
        have = _remote_repo(wd)
        if have == repo.lower():
            return wd
        print("[agent-task-node] inherited checkout is %s, need %s — re-cloning"
              % (have or "(no origin)", repo), flush=True)
    base = str(_pv(payload, "base", "main")).strip()
    token = os.environ.get("GH_TOKEN", "")
    url = "https://x-access-token:%s@github.com/%s" % (token, repo)
    shutil.rmtree(wd, ignore_errors=True)
    if os.path.exists(wd):
        # An inherited tree descends from a frozen one (`chmod -R a-w`), so the first pass
        # can leave part of it behind — and `git clone` into a non-empty directory fails
        # with a message about the destination, never about the stale tree that caused it.
        subprocess.run(["chmod", "-R", "u+w", wd], capture_output=True, timeout=300)
        shutil.rmtree(wd, ignore_errors=True)
    c = subprocess.run(["git", "clone", "--depth", "1", "--branch", base, url, wd],
                       capture_output=True, text=True, timeout=600)
    if c.returncode != 0:
        print("[agent-task-node] checkout failed: %s" % (c.stderr or "")[-200:], flush=True)
        return None
    return wd


def _workspace(payload):
    """Per-(instance, node) working dir: $WORK_ROOT/<piid>/<node>/. Gives every node of
    every process instance its own cwd, so concurrent flows — including multiple instances
    of the SAME flow (fan-out children) — never share a working directory or clobber files."""
    piid, node = payload.get("_piid"), payload.get("_node")
    if not piid or not node:
        return None
    # Inside the instance's checkout when there is one, so every node works in the real
    # repository rather than an empty directory beside it.
    wd = _ensure_checkout(payload)
    if wd:
        return wd
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
        _seed_instance_settings(cfg)
        return cfg
    except OSError:
        return None


# Tool permissions for a headless run. Seeded separately from the credentials above so
# instances created before this existed pick it up too.
#
# Without a settings.json in CLAUDE_CONFIG_DIR there are no allow rules at all, and a
# `claude -p` run has no human to approve anything — so the first Bash command it needs
# simply fails. That is not hypothetical: the SCAN node reported
#   "SCAN aborted: `gh pr list` was blocked by the permission sandbox (requires approval)"
# and returned zero PRs while looking like a normal completion. The mounted /root/.claude
# has the rules but the per-instance dir never inherited them.
#
# Deliberately NOT a copy of the host's settings.json: that carries hooks (archive
# preflight, auto-osearch), a statusline and plugins that are meaningless-to-broken in
# this container. Only the tool permissions are seeded, and only what a bounded agent
# working on a throwaway clone needs. This is strictly narrower than the
# `--dangerously-skip-permissions` the implement / pm-review verbs already pass.
_AGENT_SETTINGS = {
    "permissions": {"allow": ["Bash", "Read", "Edit", "Write", "WebFetch(domain:*)"]},
    "includeCoAuthoredBy": False,
}


def _seed_instance_settings(cfg):
    """Write the headless permission rules into an instance config dir (idempotent)."""
    path = os.path.join(cfg, "settings.json")
    if os.path.exists(path):
        return
    try:
        os.makedirs(cfg, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(_AGENT_SETTINGS, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)          # atomic: a concurrent run never reads a half file
    except OSError as e:
        print("[agent-task-node] could not seed instance settings: %s" % e, flush=True)


class RateLimitError(RuntimeError):
    """Claude hit a rate/usage limit (HTTP 429/529 or 'Overloaded'). Distinct from other
    failures so the worker can back off + NOT count it toward an instance's retry budget."""


_RATE_RE = re.compile(r"rate.?limit|overloaded|usage limit|too many requests|\b429\b|\b529\b", re.I)



# Transient trouble reaching the API — not this instance's fault, and not a verdict on the
# work it was doing.
#
# An implement node ran 50 minutes and 134 turns before the CLI returned
# "API Error: Unable to connect to API (ECONNRESET)". The agent raised a plain
# RuntimeError, the worker treated it as a failed attempt, burned all three retries against
# the same flaky network, and aborted the instance. Fifty minutes of work, discarded because
# a socket closed.
#
# Rate limits already get this treatment: a 429 tells the worker to back off WITHOUT
# spending the instance's retries, because the run did nothing wrong. A connection reset is
# the same kind of event and deserves the same answer. What distinguishes both from a real
# failure is that retrying later is likely to work — nothing about the task has been
# disproved.
_TRANSIENT_RE = re.compile(
    r"ECONNRESET|ECONNREFUSED|ETIMEDOUT|EPIPE|ENOTFOUND|EAI_AGAIN|socket hang up|"
    r"unable to connect to api|network error|connection (?:reset|refused|closed|error)|"
    r"fetch failed|\bETIMEDOUT\b|\b50[234]\b",
    re.I)


def _transient_api(status, text):
    """True if this looks like the network gave out rather than the work being wrong."""
    try:
        if int(status) in (500, 502, 503, 504):
            return True
    except (TypeError, ValueError):
        pass
    return bool(text and _TRANSIENT_RE.search(str(text)))


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
        # The prompt goes in on stdin, not argv. Linux caps a single argv string at
        # MAX_ARG_STRLEN (128 KiB) and the limit is in BYTES, so CJK prose hits it at
        # roughly 43k characters. A 22k-char answer set plus a 25k-char SRS is ~145 KB and
        # execve fails outright: "[Errno 7] Argument list too long: '/usr/bin/claude'",
        # which is what killed the SD node three times today before the worker gave up.
        #
        # The old 24_000-char input cap had been hiding this — not by design, just by being
        # small enough. Raising it to make room for a real specification uncovered the wall
        # behind it. stdin has no such ceiling, so the size question goes back to being about
        # the model's context, which is where it belongs.
        cmd = [CLAUDE, "-p", "--json-schema", schema,
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
        # Feed the prompt from a file rather than writing it down a pipe: a 145 KB write
        # would block on the 64 KB pipe buffer while this side is not yet reading stdout,
        # and the deadlock would look like a hang rather than an error.
        _pf = tempfile.NamedTemporaryFile("w", suffix=".prompt", delete=False, encoding="utf-8")
        _pf.write(prompt)
        _pf.close()
        with open(console_path, "w") as cf, open(_pf.name, "r", encoding="utf-8") as _pin:
            proc = subprocess.Popen(cmd, stdin=_pin, stdout=subprocess.PIPE,
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
        try:
            os.unlink(_pf.name)
        except OSError:
            pass
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
        # Same reason as the streaming path above: prompt on stdin, never argv.
        cmd = [CLAUDE, "-p", "--json-schema", schema,
               "--output-format", "json"] + _resume(payload) + _skill_flags(payload) + _perm_flags(payload) + _dir_flags(payload)
        if MODEL:
            cmd += ["--model", MODEL]
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              timeout=wall, cwd=cwd, env=run_env)
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
        # Same handling, different cause: the network dropped, so the run has not been
        # judged. Surfacing this as a 429 keeps the instance's retries for real failures.
        if _transient_api(_aerr, _amsg) or _transient_api(_aerr, str(_aerr)):
            raise RateLimitError(f"claude api transient network error: {_aerr or _amsg}")
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


def _repo_layout(payload):
    """The repository's REAL shape — top-level source directories and the stack markers that
    say what it is written in.

    The design nodes (SA / SD / uiux) receive a feature request and nothing else. Asked to
    produce a file plan, they produce one for the most common project they can imagine. On
    2026-07-21 the SD node designed a NestJS backend with `src/flows/flows.controller.ts` and
    an Angular CLI layout for a repo whose backend is Rust/axum under
    `arcana-cloud-rust/crates/` — nineteen file paths, none of which existed, and an endpoint
    the product has never had. The reasoning was sound; the ground was invented.

    That is the same defect already fixed downstream for the test generators: the model cannot
    see the repository, so telling it not to guess is useless — it has to be handed the facts.
    One tree call, cached on the payload.
    """
    if "_repo_layout" in payload:
        return payload["_repo_layout"]
    out = {"dirs": [], "stack": []}
    repo = _pv(payload, "repo")
    _, _br = _pr_url_and_branch(payload)
    ref = _br or _pv(payload, "base", "main")
    if not repo:
        payload["_repo_layout"] = out
        return out
    try:
        raw = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/trees/{ref}?recursive=1",
             "--jq", '.tree[] | select(.type=="blob") | .path'],
            capture_output=True, text=True, timeout=120).stdout.split()
        MARKERS = {"Cargo.toml": "Rust (cargo)", "pom.xml": "Java/Maven",
                   "go.mod": "Go", "package.json": "Node/npm",
                   "requirements.txt": "Python", "pyproject.toml": "Python"}
        skip = ("node_modules/", "target/", "dist/", ".git/", "usage/")
        dirs, stack = {}, []
        for p in raw:
            if p.startswith(skip) or any(x in p for x in skip):
                continue
            base = p.rsplit("/", 1)[-1]
            if base in MARKERS:
                where = p.rsplit("/", 1)[0] if "/" in p else "(root)"
                entry = f"{MARKERS[base]} — {where}"
                if entry not in stack:
                    stack.append(entry)
            # Directory of the file, capped at depth 4 so the sketch stays readable.
            d = "/".join(p.split("/")[:-1][:4])
            if d:
                dirs[d] = dirs.get(d, 0) + 1
        # Collapse per language, shallowest path first. Unfiltered, a repo with a dozen Rust
        # crates fills the list with Rust and pushes the FRONT END off it — the half of the
        # 2026-07-21 hallucination that invented an Angular CLI layout.
        by_lang = {}
        for e in stack:
            lang, where = e.split(" — ", 1)
            by_lang.setdefault(lang, []).append(where)
        out["stack"] = [
            f"{lang} — " + ", ".join(sorted(w, key=lambda x: (x.count("/"), x))[:2])
            for lang, w in by_lang.items()
        ]
        # Busiest directories first: where the code actually lives.
        out["dirs"] = [d for d, _ in sorted(dirs.items(), key=lambda kv: -kv[1])[:60]]
    except Exception as e:
        print("[agent-task-node] repo layout unavailable: %s" % e, flush=True)
    payload["_repo_layout"] = out
    return out


def _repo_grounding_block(payload):
    """The prompt fragment that stops a design node inventing a stack."""
    lay = _repo_layout(payload)
    if not lay["dirs"] and not lay["stack"]:
        return ""
    paths = _api_path_inventory(payload)
    b = ["\n\nREPOSITORY GROUNDING — this is the repository the work lands in, read from the "
         "branch itself. Design AGAINST it. Every file path you name must sit under one of the "
         "directories below, and you may not assume a framework that is not in the stack list: a "
         "plan written for a project that does not exist costs a full implement round and reads, "
         "to whoever gets the PR, as though the feature was attempted and failed."]
    if lay["stack"]:
        b.append("Stack (from its own manifests):\n  " + "\n  ".join(lay["stack"]))
    if lay["dirs"]:
        b.append("Source directories (busiest first):\n  " + "\n  ".join(lay["dirs"]))
    if paths:
        b.append("Existing API paths — extend this surface, do not invent a parallel one:\n  "
                 + "\n  ".join(paths[:40]))
    b.append("If the request cannot be placed in this layout, say so in your output instead of "
             "relocating the project.")
    state = _productization_state(payload)
    if state:
        b.append(state)
    return "\n\n".join(b)


def _productization_state(payload):
    """Current verified state of the product, from the CDP full-function walk committed at
    `docs/productization/function-walk.json`.

    A design node otherwise starts blind to what already works and re-specifies covered ground.
    The walk records, per function, whether it is reachable, whether its negative boundary holds,
    and — crucially — whether its business chain has actually been exercised (`chainCovered`) or
    only its entrance. Feeding it in points the design at the UNCOVERED cells instead of retesting
    green ones, and stops it treating an entrance-only check as proof the chain works.

    Read from the instance checkout (this run's cwd), so it is the branch's own state, not a
    stale copy fetched separately. Absent file = nothing appended; this never fails a node.
    """
    root = _instance_root(payload.get("_piid"))
    if not root:
        return ""
    path = os.path.join(root, "repo", "docs/productization/function-walk.json")
    try:
        rpt = json.load(open(path))
    except Exception:
        return ""
    s = rpt.get("summary", {})
    lines = [
        "PRODUCT STATE — from the CDP function walk (docs/productization/function-walk.json, "
        "schema %s). This is what is already verified; design toward the gaps, not the greens."
        % rpt.get("schemaVersion", "?"),
        "Coverage: positive %s/%s, negative(entrance) %s/%s."
        % (s.get("positivePass"), s.get("positiveTotal"),
           s.get("negativePass"), s.get("negativeTotal")),
    ]
    unc = s.get("chainUncovered", [])
    if unc:
        lines.append(
            "Business chains NOT yet exercised by any run (entrance-only) — a feature touching "
            "one of these must not be called done on a UI check alone; its real gate is "
            "scenario-walk / flow-sim: " + ", ".join(unc))
    # Point at the design model + naming rules rather than transcribe them — the nodes run in the
    # checkout and can read the file, which never goes stale the way a copied prompt fragment does.
    # One rule is inlined because it is the highest-signal and the easiest to violate: the naming
    # axis is what-must-I-do vs what-am-I-watching, not who-sent-what.
    tree = os.path.join(root, "repo", "docs/productization/function-tree.md")
    if os.path.exists(tree):
        lines.append(
            "A product function tree (WHO x WHEN) with the PRECISE execution-period model and "
            "naming rules is at docs/productization/function-tree.md — READ IT before designing "
            "anything on the my-flows / approvals surface or naming a user-facing label. "
            "Standing rule: the vocabulary axis is action-state (待辦 = requires my action, "
            "incl. unsubmitted drafts; 流程追蹤 = flows I have touched, auto), NEVER the mailbox "
            "metaphor (收件匣 / 送件匣) — a draft is not 'received' and a flow I signed is not "
            "'sent', so those words are wrong by construction.")
    return "\n  ".join(lines)


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
    # Ground every AI node that plans work against a repo. Cheap (one cached tree call) and
    # only appended when a `repo` is actually known, so non-repo flows are untouched.
    if _pv(payload, "repo"):
        parts.append(_repo_grounding_block(payload))
    return "\n".join(parts)


# The keys that CARRY the specification. Bounding these is not a size optimisation —
# it deletes the thing the node was asked to work from.
#
# The uniform 600-char bound below treats a 14 KB requirement the same as a repo name, so
# the first field to be gutted was always the largest, which is always the one that matters.
# Today that cost a full run: four rounds of intake answers (14 KB) were cut to 600 chars,
# SA correctly refused with INPUT_INCOMPLETE, and SD then invented a design from the refusal.
SPEC_BEARING = (
    "feature_request", "intakeForm", "intakeReview", "srs", "sdd", "uiuxSpec",
    "acceptance", "requiredCells", "rework_feedback", "manager_notes", "ai_input",
    "pm_answers", "out_of_scope", "target_users", "placement",
)


def _bounded_json(business, cap=200_000):
    """Serialize node input data for prompt embedding WITHOUT silently amputating
    late keys. The old raw `[:8000]` slice cut the JSON mid-string, so any key
    sorting after a fat one vanished — a `goal` after a bloated `existing` made the
    decompose node effectively blind (2026-07-19 incident). Strategy: full dump if
    it fits; else bound the NON-spec-bearing leaves first, and only touch the
    spec-bearing ones if that is not enough — naming each one that was cut.

    Two things changed on 2026-07-28, both after the same failure:

    `cap` was 24_000. Four rounds of intake Q&A plus the requirement come to ~18 KB of
    prose before any other field, so a thorough requirement crossed the cap by existing.
    200_000 is the same order as the design cap this file already uses elsewhere and is
    small against the model's context; the point of a cap here is to stop a runaway field,
    not to ration a specification.

    Bounding was uniform at 600 chars per string leaf. Uniform means the specification and
    the repo slug are equally expendable, so in practice the specification went first —
    it is always the biggest. Now the fields that carry the spec are bounded last, and when
    one is bounded the marker names it, because a model that cannot see what it is missing
    will fill the hole itself. SA did the right thing today (refused, named the gaps) but
    SD did not — it designed from the refusal.
    """
    txt = json.dumps(business, ensure_ascii=False, indent=2)
    if len(txt) <= cap:
        return txt

    def bound(v, limit):
        if isinstance(v, str) and len(v) > limit:
            return v[:limit] + "…[truncated: %d of %d chars shown]" % (limit, len(v))
        if isinstance(v, list):
            return [bound(x, limit) for x in v[:80]] + (
                ["…[%d more truncated]" % (len(v) - 80)] if len(v) > 80 else [])
        if isinstance(v, dict):
            return {k: bound(x, limit) for k, x in v.items()}
        return v

    # Pass 1: squeeze everything that is NOT carrying the specification.
    squeezed = {k: (v if k in SPEC_BEARING else bound(v, 600)) for k, v in business.items()}
    txt = json.dumps(squeezed, ensure_ascii=False, indent=2)
    if len(txt) <= cap:
        return txt

    # Pass 2: the spec itself has to give. Say so, per field, in the data the model reads —
    # an unannounced cut is the failure mode this whole function exists to prevent.
    cut = []
    for k in list(squeezed):
        if k in SPEC_BEARING and isinstance(squeezed[k], str) and len(squeezed[k]) > 20_000:
            cut.append(k)
            squeezed[k] = bound(squeezed[k], 20_000)
    if cut:
        squeezed["_TRUNCATION_WARNING"] = (
            "These specification fields were shortened to fit and are INCOMPLETE: %s. "
            "Do not infer the missing content — say which field is short and stop."
            % ", ".join(cut))
    txt = json.dumps(squeezed, ensure_ascii=False, indent=2)
    if len(txt) <= cap:
        return txt
    return txt[:cap] + (
        "\n…(DATA TRUNCATED at %d chars — later keys may be missing; say so if a needed "
        "field is absent)" % cap)


# Nodes that are writing the specification / design and therefore need to know which product
# they are writing it FOR. Deliberately a list rather than "everyone": the brief costs a repo
# read and several API calls, and a node that only transforms its input gains nothing from it.
_CONTEXT_NODES = {"sa", "sd", "uiux", "genflow", "intake"}


def run_claude_generic(payload):
    if not (payload.get("prompt") or "").strip():
        raise RuntimeError("generic executor requires a non-empty `prompt`")
    prompt = _with_memory(prompt_generic(payload), payload)
    # The design nodes used to receive feature_request / repo / base / slug / uiFacing and
    # nothing else — no idea what the product is, what it already does, or what else is being
    # built beside it. PmReview, the LAST node, was the only one holding the app map and the
    # sibling list. Context arriving four AI sessions after the node that needed most of it is
    # why an SRS so often reads like a standalone tool's spec rather than this product's Nth
    # feature.
    node = str(payload.get("_node") or "").strip().lower()
    if node in _CONTEXT_NODES:
        brief = project_brief(payload, _ensure_checkout(payload))
        if brief:
            prompt = prompt + "\n" + brief
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
    branch = _feature_branch(payload, slug)
    # Clone under this (instance, node) workspace so concurrent implement runs are isolated;
    # fall back to a temp dir for direct calls that carry no _piid/_node.
    # The instance's own checkout — the SAME one SA / SD / uiux read, so implement builds on
    # what they actually looked at rather than a private clone they never saw.
    workdir = _ensure_checkout(payload)
    # Only the FALLBACK dir is ours to delete. The instance checkout must survive this call:
    # it is what a later run copies forward and what the seal hashes. Left unset, the cleanup
    # below crashed with an unbound `tmp` the moment a real checkout existed — implement failed
    # three times and the run was aborted, for a variable that was never assigned.
    tmp = None
    if not workdir:
        tmp = tempfile.mkdtemp(prefix="implement-%s-" % slug)
        workdir = os.path.join(tmp, "repo")
    try:
        # --- Phase A: put the checkout on a fresh branch off `base` ---
        # Inherited (copied) or cloned, it may sit on any ref and carry a previous run's
        # edits. Reset hard: a feature branch that quietly starts from someone else's
        # uncommitted work produces a diff nobody can account for.
        clone_url = "https://x-access-token:%s@github.com/%s" % (token, repo)
        if not os.path.isdir(os.path.join(workdir, ".git")):
            shutil.rmtree(workdir, ignore_errors=True)
            c = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", base, clone_url, workdir],
                capture_output=True, text=True, timeout=300)
            if c.returncode != 0:
                return {"error": "clone failed: %s" % (c.stderr or c.stdout)[-500:]}
        else:
            subprocess.run(["git", "-C", workdir, "remote", "set-url", "origin", clone_url],
                           capture_output=True, text=True, timeout=60)
            f = subprocess.run(["git", "-C", workdir, "fetch", "--depth", "1", "origin", base],
                               capture_output=True, text=True, timeout=300)
            if f.returncode != 0:
                return {"error": "fetch failed: %s" % (f.stderr or f.stdout)[-500:]}
            subprocess.run(["git", "-C", workdir, "reset", "--hard", "FETCH_HEAD"],
                           capture_output=True, text=True, timeout=120)
            subprocess.run(["git", "-C", workdir, "clean", "-fd"],
                           capture_output=True, text=True, timeout=120)

        # --- Phase B: Claude writes code in the workdir (bound to the dev skill) ---
        design = payload.get("design")
        # The SRS is the most expensive artifact this pipeline makes — four rounds of intake
        # questions bought it. Cutting it to 8000 characters handed the designer a spec that
        # ended mid-sentence, and SD said so in its own words: "visibly truncated mid-sentence
        # (AC-03 ends ...[truncated])". The tokens saved are worth far less than the implement
        # round that gets built on a spec nobody could finish reading.
        design_str = json.dumps(design, ensure_ascii=False) if design is not None else ""
        if len(design_str) > 120_000:
            # A cap still exists, but it is far above any real spec and it SAYS SO — a silent
            # cut is indistinguishable from a spec that simply ended there.
            design_str = design_str[:120_000] + "\n\n[!! 本 SRS/SDD 在此被截斷 —— 後面還有內容。" \
                                                "缺少的部分請視為未知,不要當成規格到此為止 !!]"
        full_prompt = (
            instruction
            + "\n\n## 目標\n在目前工作目錄（已 clone 的 repo）實作此功能，嚴格遵守 repo 既有架構慣例"
              "（你載入的 developer skill 已含 Clean Arch / MVVM / arch-qube 規範），並**寫對應單元測試**。\n"
              "## 交付前自我驗證（重要）\n開 PR 前**必須**讓受影響的子專案在本地編譯通過：進到該子專案（例如 `dashboard/`）跑 "
              "`npm ci && npm run build`，有編譯錯就修到綠；並為新功能寫**會通過的單元測試**。**不要交出沒編譯過的碼**"
              "——下游 CI（build + ng test + arch-qube + Sonar）會擋，交紅碼只會被 PM NOGO 退回重做、白費一輪。"
              "時間預算內以「編得過、架構乾淨、測試通過」為第一優先；最後簡述你改了什麼。\n"
            + ("\n## 設計 (SRS/SDD)\n```json\n" + design_str + "\n```\n" if design_str else "")
            # The exam paper, handed over before the work rather than after it.
            + _acceptance_brief(payload, workdir))
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
        # A rework round pushes to the SAME branch, so the PR usually already exists — the
        # commits are on it either way. Creating is the FIRST round's job, not every round's.
        # Reported as an error, "a pull request for branch X already exists" landed in the
        # `pr` process variable and the PM node read it as a failed delivery: the loop was
        # working exactly as designed and the flow said it had broken.
        existing = subprocess.run(
            ["gh", "pr", "list", "-R", repo, "--head", branch, "--state", "open",
             "--json", "url", "--jq", ".[0].url"],
            capture_output=True, text=True, timeout=120, env=env).stdout.strip()
        if existing:
            return {"prUrl": existing, "branch": branch, "summary": summary,
                    "filesChanged": files_changed, "pushed": True,
                    "buildStatus": build_status, "prReused": True}
        pr = subprocess.run(
            ["gh", "pr", "create", "-R", repo, "--base", base, "--head", branch,
             "--title", "feat: %s" % slug, "--body", body],
            capture_output=True, text=True, timeout=120, cwd=workdir, env=env)
        if pr.returncode != 0:
            # Lost a race, or the listing missed it: recover the URL rather than fail a round
            # whose code is already pushed.
            recovered = subprocess.run(
                ["gh", "pr", "list", "-R", repo, "--head", branch, "--state", "open",
                 "--json", "url", "--jq", ".[0].url"],
                capture_output=True, text=True, timeout=120, env=env).stdout.strip()
            if recovered:
                return {"prUrl": recovered, "branch": branch, "summary": summary,
                        "filesChanged": files_changed, "pushed": True,
                        "buildStatus": build_status, "prReused": True}
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
        if tmp:
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




def _touched_flows(payload):
    """The business flows this PR changed — the process ids of any .bpmn2 in its file list.

    The scenario gate is scoped to these so a feature answers for the flows it TOUCHED, not the
    repo's whole scenario backlog: changing leave-approval.bpmn2 must not be blocked by an unrelated
    gap in purchase. A UI feature changes no .bpmn2 → empty → the gate is a no-op. Cached; best
    effort (an unreadable PR just yields none, and the gate then no-ops rather than false-blocking).
    """
    if "_touched_flows" in payload:
        return payload["_touched_flows"]
    flows, paths, repo = [], [], payload.get("repo") or ""
    url, _ = _pr_url_and_branch(payload)
    num = ""
    m = re.search(r"/pull/(\d+)", url or "")
    if m:
        num = m.group(1)
    try:
        if repo and num:
            files = subprocess.run(
                ["gh", "api", f"repos/{repo}/pulls/{num}/files", "--paginate", "--jq", ".[].filename"],
                capture_output=True, text=True, timeout=90).stdout.split()
            for fn in files:
                if fn.endswith(".bpmn2"):
                    flows.append(os.path.basename(fn)[:-6])
                    # Keep the PATH, not just the stem. The gate can then read exactly the files
                    # this PR changed instead of re-deriving a directory from a hardcoded layout —
                    # which is how it used to report "ran, found nothing" while pointed at a tree
                    # that did not exist. We already have the paths here; throwing them away was
                    # the whole bug.
                    paths.append(fn)
    except Exception as e:
        print("[agent-task-node] touched-flows unavailable: %s" % e, flush=True)
    payload["_touched_flows"] = sorted(set(flows))
    payload["_touched_flow_paths"] = sorted(set(paths))
    return payload["_touched_flows"]


def _scenario_autofill(payload):
    """S3b: in-pipeline auto-fill. For each touched flow with an uncovered required cell, an AI
    drafts a falsifiable scenario pair and the machine PROVES it diverges against a throwaway
    engine; proven pairs are committed to the PR. Opt-in (SCENARIO_AUTOFILL=1). It NEVER silently
    passes a gap: an unproven or unfillable cell is returned for escalate, and S3a still blocks.

    Caveat, stated because it bounds correctness: the throwaway engine runs the DEPLOYED flows
    (the arcana/kogito-bpmn image), so a scenario is proven against the deployed shape of the flow.
    When a PR changes the flow STRUCTURE, that proof is against the old shape — S3a's static check
    on the PR's own .bpmn2 still blocks a genuinely new uncovered cell, so nothing passes unproven.
    Full correctness needs the PR's compiled engine (a maven build), deferred.
    """
    if os.environ.get("SCENARIO_AUTOFILL") != "1":
        return {"ran": False, "reason": "disabled (SCENARIO_AUTOFILL!=1)"}
    touched = _touched_flows(payload)
    if not touched:
        return {"ran": False, "reason": "no touched business flow"}
    flow_sim = os.environ.get("FLOW_SIM_BIN", "/usr/local/bin/flow-sim")
    if not os.path.exists(flow_sim):
        return {"ran": False, "reason": "flow-sim binary not in agent image"}
    # This binary is a build artifact copied into the image by hand, with nothing tying it to
    # the source it was built from. "The simulator ran and found nothing" has therefore never
    # carried a claim about WHICH simulator — the same gap the stale-image gate closed for
    # services. Demand a schema it understands; an unreadable answer means an old copy, and
    # an old copy is notRun, not a pass.
    _need_schema = int(os.environ.get("FLOW_SIM_MIN_SCHEMA", "1"))
    try:
        _v = json.loads(subprocess.run([flow_sim, "--version"], capture_output=True, text=True,
                                       timeout=30).stdout or "{}")
        _have = int(_v.get("scenarioSchema", 0))
    except Exception as e:
        return {"ran": False, "reason": "flow-sim --version unreadable (%s) — too old to trust" % e}
    if _have < _need_schema:
        return {"ran": False,
                "reason": "flow-sim scenario schema %s < required %s — stale binary in image"
                          % (_have, _need_schema)}
    net = os.environ.get("TEST_NETWORK", "arcana-ai-agent-flow_default")
    repo = payload.get("repo") or ""
    _, branch = _pr_url_and_branch(payload)
    if not (repo and branch):
        return {"ran": False, "reason": "no repo/branch"}
    token = os.environ.get("GH_TOKEN", "")
    eng = "aaf-sim-autofill-" + (_safe_seg(payload.get("_piid")) or "adhoc")[:12]
    src = tempfile.mkdtemp(prefix="autofill-")
    filled, escalate = {}, []

    def curl(url):
        r = subprocess.run(["docker", "run", "--rm", "--network", net, "curlimages/curl:latest",
                            "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip()

    try:
        auth = ("x-access-token:%s@" % token) if token else ""
        c = subprocess.run(["git", "clone", "--depth", "1", "--branch", branch,
                            "https://%sgithub.com/%s" % (auth, repo), src],
                           capture_output=True, text=True, timeout=300)
        if c.returncode != 0:
            return {"ran": False, "reason": "clone failed: " + (c.stderr or "")[-160:]}
        if not os.path.exists(os.path.join(src, "scripts/scenario-autofill.py")):
            return {"ran": False, "reason": "PR has no scenario-autofill.py (pre-S2 branch)"}

        subprocess.run(["docker", "rm", "-f", eng], capture_output=True, timeout=60)
        r = subprocess.run(
            ["docker", "run", "-d", "--name", eng, "--network", net,
             "-e", "JDBC_URL=jdbc:postgresql://kogito-pg:5432/workflow",
             "-e", "POSTGRES_USER=kogito", "-e", "POSTGRES_PASSWORD=kogito",
             "-e", "KAFKA_BOOTSTRAP=kafka:9092", "-e", "KOGITO_SERVICE_URL=http://%s:8080" % eng,
             "arcana/kogito-bpmn:1.0.0"],
            capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"ran": False, "reason": "engine start failed: " + (r.stderr or "")[-160:]}
        ready = False
        for _ in range(50):
            if curl("http://%s:8080/q/health/ready" % eng) == "200":
                ready = True
                break
            time.sleep(3)
        if not ready:
            return {"ran": False, "reason": "throwaway engine never became ready"}

        env = dict(os.environ)
        env.update({
            "FLOW_SIM": flow_sim,
            "SIM_ENGINE_URL": "http://%s:8080" % eng,
            "SIM_API_URL": os.environ.get("TEST_API_TARGET", "http://aaf-arcana-cloud-rust:8080"),
            "ENGINE_URL": "http://aaf-kogito-bpmn:8080",
            "SIM_DATA_INDEX_URL": os.environ.get("TEST_DATAINDEX", "http://aaf-data-index:8080"),
            "BPMN_DIR": os.path.join(src, "kogito-bpmn/src/main/resources/boo/arcana"),
            "CLAUDE": CLAUDE,
        })
        for flow in touched:
            af = subprocess.run(["python3", os.path.join(src, "scripts/scenario-autofill.py"), flow],
                                capture_output=True, text=True, timeout=2400, env=env, cwd=src)
            tail = (af.stdout or "")[-400:]
            print("[agent-task-node] autofill %s: rc=%s %s" % (flow, af.returncode, tail.replace("\n", " ")), flush=True)
            if af.returncode == 0 and "無需自動補" not in af.stdout:
                filled[flow] = "filled"
            elif af.returncode != 0:
                escalate.append(flow)

        if filled:
            def g(*a):
                return subprocess.run(["git", "-C", src, *a], capture_output=True, text=True, timeout=120)
            g("add", "scripts/sample-scenarios")
            g("-c", "user.email=agent@arcana.boo", "-c", "user.name=AI-BPM Scenario Gate",
              "commit", "-m", "test(scenario): auto-fill proven-falsifiable scenarios for " + ", ".join(filled))
            g("push", "origin", branch)
        return {"ran": True, "filled": sorted(filled), "escalate": sorted(escalate)}
    finally:
        subprocess.run(["docker", "rm", "-f", eng], capture_output=True, timeout=60)
        shutil.rmtree(src, ignore_errors=True)


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
    paths, repo = [], _pv(payload, "repo")
    # Read the PR's OWN ref, not the base: a feature that ADDS an endpoint is exactly the case
    # where the generator has nothing to go on, and inventorying `main` would leave that new
    # path out — sending the model back to guessing for the one endpoint under test.
    _, _br = _pr_url_and_branch(payload)
    base = _br or _pv(payload, "base", "main")
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




# ── Read-only access to the RUNNING system, for the nodes that have to diagnose it ──────────
#
# implement / pm-review hold the source and the diff and nothing else, so an entire class of
# problem is structurally invisible to them: the code is right and the running thing is not.
# Every hard diagnosis on 2026-07-20 needed exactly this and none of it was available —
# whether `requester` actually survived into the engine's variables (F-5), whether the
# deployed bundle contained the component at all (a two-day-old image serving a "missing"
# feature), whether a user has a Postgres role (F-1).
#
# Read-only on purpose and by construction, not by convention: the `arcana_readonly` login has
# SELECT and nothing else, so a diagnosing node cannot repair what it is looking at — a fix
# must still travel through a gated PR, and a node that could edit production would make the
# whole review chain optional.

_SITE_MAX = 8000


def _site_sql(query, db="arcana"):
    """Run one read-only SELECT against the live database. Returns text (truncated).

    Rejects anything that is not a SELECT/WITH before it reaches the wire. This prefix check is
    the SECOND line, not the only one — it is trivially defeated by `SELECT 1; DROP TABLE x`,
    which it lets through and the DATABASE then refuses ("must be owner of table"). Verified
    both ways on 2026-07-20. Keep both: the check gives a node a clear reason instead of a
    stack trace, and the grant is what actually makes the guarantee true.
    """
    q = (query or "").strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with|explain|show)\b", q):
        return "refused: read-only site access takes SELECT/WITH/EXPLAIN/SHOW only"
    if not re.match(r"^[A-Za-z0-9_]+$", db or ""):
        return "refused: bad database name"
    try:
        r = subprocess.run(
            ["docker", "exec", "-e", "PGPASSWORD=" + os.environ.get("SITE_PG_PASS", "readonly"),
             os.environ.get("TEST_PG_CONTAINER", "aaf-kogito-pg"),
             "psql", "-U", os.environ.get("SITE_PG_USER", "arcana_readonly"),
             "-h", "127.0.0.1", "-d", db, "-P", "pager=off", "-c", q],
            capture_output=True, text=True, timeout=120)
        return ((r.stdout or "") + (r.stderr or ""))[:_SITE_MAX]
    except Exception as e:
        return f"site sql failed: {e}"


def _site_http(path, base=None):
    """GET a path on the DEPLOYED app — the artifact users actually receive.

    The question "is this component even in the bundle the browser is being served?" cannot be
    answered from the repository, and answering it wrongly cost two days of a feature looking
    broken when it had simply never been deployed.
    """
    base = base or os.environ.get("SITE_APP_URL", "http://aaf-dashboard:80")
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "--network",
             os.environ.get("TEST_NETWORK", "arcana-ai-agent-flow_default"),
             "curlimages/curl:latest", "-s", "-m", "30", base + path],
            capture_output=True, text=True, timeout=120)
        return (r.stdout or "")[:_SITE_MAX]
    except Exception as e:
        return f"site http failed: {e}"


def _site_images():
    """What is actually RUNNING, and since when — the 'merged ≠ deployed' question."""
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}"],
            capture_output=True, text=True, timeout=60)
        return (r.stdout or "")[:_SITE_MAX]
    except Exception as e:
        return f"site images failed: {e}"


def site_flow(payload):
    """`site` verb — read-only observation of the running system.

    `{"kind": "sql", "query": "...", "db": "arcana"}` | `{"kind": "http", "path": "/..."}` |
    `{"kind": "images"}`
    """
    kind = (payload.get("kind") or "").lower()
    if kind == "sql":
        return {"kind": "sql", "result": _site_sql(payload.get("query", ""), payload.get("db", "arcana"))}
    if kind == "http":
        return {"kind": "http", "result": _site_http(payload.get("path", "/"), payload.get("base"))}
    if kind == "images":
        return {"kind": "images", "result": _site_images()}
    return {"error": "kind must be one of: sql, http, images"}




def smoke_flow(payload):
    """`smoke` verb — does the DEPLOYED artifact actually work? (C)

    The definition of done stopped at a green PR, and that is one step short of the thing the
    user receives. On 2026-07-19/20 a feature was reported missing for two days while its code
    sat merged: the deployed image was older than the branch, and nginx served a cached
    index.html pinning browsers to the previous bundle. Both were invisible to every gate,
    because every gate tested a PREVIEW built from source — never the artifact.

    So this asks the only question that survives a merge: is the running system, as users get
    it, still working? It runs AFTER deploy, against the real URL, and it is deliberately the
    same scenario suite the test node uses — a business chain that completed on the PR's own
    backend and no longer completes on the deployed one is exactly the regression this exists
    to catch, and reusing it means there is no second definition of "working" to drift.

    Non-negotiable: it must fail on "could not reach the deployment" too. A smoke that treats
    an unreachable app as nothing-to-report would sign off on an outage.
    """
    app = payload.get("appUrl") or os.environ.get("SITE_APP_URL", "http://aaf-dashboard:80")
    api = payload.get("apiUrl") or os.environ.get("TEST_API_TARGET", "http://aaf-arcana-cloud-rust:8080")
    net = os.environ.get("TEST_NETWORK", "arcana-ai-agent-flow_default")
    # The RBAC gate casts as `user:pass,user:pass`; `scenarioActors` is a role→credential JSON
    # for the chain scenarios. Passing one where the other is expected silently seats no actors
    # at all, which the gate then reports as three login failures — a harness mismatch wearing
    # the costume of a broken deployment.
    actors = payload.get("actors") or str(_load_profile(payload)["auth"].get("rbacActors", ""))
    out = {"appUrl": app, "apiUrl": api}

    # 1. Is the app being served at all, and is it the build we think it is?
    idx = _site_http("/", app)
    out["appServed"] = bool(idx) and "<" in idx
    m = re.search(r"(main-[A-Z0-9]+\.js)", idx or "")
    out["bundle"] = m.group(1) if m else None

    # 2. Does the API answer, and does auth still work end to end?
    who = payload.get("smokeUser") or str(_load_profile(payload)["auth"].get("user", "boss"))
    pw = payload.get("smokePass") or str(_load_profile(payload)["auth"].get("pass", "pw"))
    login = subprocess.run(
        ["docker", "run", "--rm", "--network", net, "curlimages/curl:latest", "-s", "-m", "30",
         "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST", f"{api}/api/v1/auth/login",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"username_or_email": who, "password": pw})],
        capture_output=True, text=True, timeout=120)
    out["loginStatus"] = (login.stdout or "").strip()
    out["apiAlive"] = out["loginStatus"] == "200"

    # 3. A real user-facing check that changes NOTHING.
    #
    #    The mutating business chains deliberately do NOT run here, and scenario-walk refuses
    #    them anyway: proving a deployment works by filing real leave requests on it is not a
    #    smoke test, it is damage. What CAN be asked of a live system is whether it offers each
    #    identity exactly what they may have — the RBAC UI gate logs in as several people,
    #    navigates, and reads. It would have caught the deployed-but-unguarded `/org` that
    #    exposed the whole staff directory.
    if actors:
        r = subprocess.run(
            ["docker", "run", "--rm", "--network", net,
             "-e", "RBACUI_BASE=" + app, "-e", "RBACUI_ACTORS=" + actors,
             "-e", "RBACUI_NAV_CONFIG=/e2e/nav.config.ts",
             "--entrypoint", "node",
             os.environ.get("TEST_RUNNER_IMAGE", "aaf-test-runner:local"),
             "/e2e/rbac-ui-gate.mjs"],
            capture_output=True, text=True, timeout=1200)
        line = next((l for l in reversed((r.stdout or "").splitlines())
                     if l.startswith("RBACUI:")), "")
        try:
            g = json.loads(line[len("RBACUI:"):]) if line else {}
        except Exception:
            g = {}
        out["rbacUiTotal"] = int(g.get("total", 0) or 0)
        out["rbacUiFail"] = int(g.get("fail", 0) or 0)
        out["rbacUiLeaks"] = int(g.get("leaks", 0) or 0)
        out["rbacUiRan"] = out["rbacUiTotal"] > 0
    else:
        out["rbacUiRan"] = False

    # Business chains are NOT exercised here. Saying so keeps a shallow pass from reading like
    # the deep one the test node produces — the whole point of this file is that a green must
    # not claim more than it verified.
    out["chainsExercised"] = False

    out["allPass"] = bool(out["appServed"] and out["apiAlive"]
                          and out.get("rbacUiFail", 0) == 0)
    if not out["allPass"]:
        out["reason"] = ("deployment unreachable" if not (out["appServed"] and out["apiAlive"])
                         else "the deployed app offers someone a screen they may not have")
    print("[agent-task-node] smoke: " + json.dumps(out, ensure_ascii=False)[:400], flush=True)
    return out


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

    # S3b: before the test run, auto-fill any uncovered scenario cell of a touched flow and push
    # the proven scenarios to the PR — so the scenario gate (S3a) inside the runner then sees the
    # coverage complete. Opt-in and best-effort: disabled or unfillable leaves the gap for S3a to
    # block. Runs before the runner clones, so the pushed scenarios are in the branch it pulls.
    autofill = _scenario_autofill(payload)
    if autofill.get("ran"):
        print("[agent-task-node] scenario autofill: filled=%s escalate=%s"
              % (autofill.get("filled"), autofill.get("escalate")), flush=True)

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
            # Whether the business chain SHOULD have run. Set when this PR touches the backend,
            # so the runner can tell "no backend change, legitimately not run" from "backend
            # change, but the isolated backend never came up, so the one mutating multi-actor
            # gate was silently skipped and the green means less than it looks". Without this
            # the skip is invisible: scenarioRan=false reads identically in both cases.
            "-e", "SW_EXPECTED=" + ("1" if pr_backend_applicable else ""),
            # Scenario gate: the business flows this PR actually changed. The runner runs the
            # scenario matrix scoped to these, so a feature is judged on the flows it touched — a
            # changed .bpmn2 whose required 7W1H cell has no falsifiable scenario blocks the test,
            # a UI feature that touches no flow is a no-op.
            "-e", "SCENARIO_TOUCHED=" + ",".join(_touched_flows(payload)),
            # The PR's own paths: the gate reads exactly these files instead of guessing a
            # directory. And EXPECTED says a gate that should have run but did not is a
            # failure, not a silent skip — the same rule scenario-walk already lives by.
            "-e", "SCENARIO_TOUCHED_PATHS=" + ",".join(payload.get("_touched_flow_paths") or []),
            "-e", "SCENARIO_GATE_EXPECTED=" + ("1" if _touched_flows(payload) else "0"),
            # Where THIS product keeps its flows, its scenario library, and which cell
            # rulebook applies. Everything else about the gate had been generalised while
            # the one thing deciding which files it reads stayed hardcoded to aaf's layout,
            # so the first non-aaf repo made it report "the declared flowDir does not exist"
            # — honest, and unable to run. Paths are facts about a tree, so they come from
            # the tree's own .arcana/project.json.
            "-e", "SM_FLOW_DIR=" + str(_pf.get("flow", {}).get("flowDir", "")),
            "-e", "SM_SIM_DIR=" + str(_pf.get("flow", {}).get("scenarioDir", "")),
            "-e", "SCENARIO_PROFILE=" + str(_pf.get("flow", {}).get("scenarioProfile", "")),
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
            # S3b: what the in-pipeline scenario auto-fill did (or why it didn't). An escalate here
            # means a touched flow's cell could not be filled falsifiably — the scenario gate in
            # the runner then blocks it, so this is legible rather than a silent skip.
            rep["scenarioAutofill"] = autofill
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
            chk = subprocess.run(["gh", "pr", "list", "-R", repo, "--head", _feature_branch(payload, slug),
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
        if task not in PROMPTS and task not in ("release", "execute", "publish-flow", "implement", "test", "uiux-audit", "site", "smoke", "dispose-pr"):
            return self._send(404, {"error": f"unknown task {task}"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})
        # Before spending anything. The allowlist used to be checked in `implement` — the
        # fourth node — so a repo this pipeline was never allowed to touch cost three full AI
        # sessions (SA, SD, uiux) before anything said no. Seconds of `gh api` here instead.
        # Payloads with no repo (decompose works from a goal) have nothing to check and skip.
        if task in ("execute", "implement") and str(_pv(payload, "repo")).strip():
            pf = preflight(payload)
            if not pf["ok"]:
                print("[agent-task-node] preflight refused: %s" % pf["reason"], flush=True)
                return self._send(200, {"error": "preflight: " + pf["reason"],
                                        "preflight": pf, "ran": False})
            print("[agent-task-node] preflight ok: %s" % "; ".join(pf["checks"]), flush=True)

        try:
            if task == "release":
                result = run_release(payload)
            elif task == "execute":
                result = run_claude_generic(payload)
            elif task == "publish-flow":
                result = publish_flow(payload)
            elif task == "implement":
                result = implement_flow(payload)
            elif task == "smoke":
                # AFTER deploy, against the artifact users receive — the step the DoD was
                # missing when a merged feature spent two days looking broken.
                result = smoke_flow(payload)
            elif task == "site":
                # Read-only observation of the RUNNING system, for nodes whose diagnosis needs
                # more than the repo. Cannot write anything: the DB login holds SELECT only.
                result = site_flow(payload)
            elif task == "dispose-pr":
                result = dispose_pr(payload)
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
