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
import json
import os
import shutil
import subprocess
import re
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


PROMPTS = {"diagnose": prompt_diagnose, "fix": prompt_fix, "merge": prompt_merge, "sweep": prompt_sweep, "decide": prompt_decide, "analyze": prompt_analyze, "readmesync": prompt_readmesync, "escalate": prompt_escalate, "scan-stale": prompt_scan_stale, "rebase": prompt_rebase, "audit": prompt_audit}


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


def _invoke_claude(prompt, schema, payload, wall):
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
    if console_path:
        cmd = [CLAUDE, "-p", prompt, "--json-schema", schema,
               "--output-format", "stream-json", "--verbose"] + _resume(payload)
        if MODEL:
            cmd += ["--model", MODEL]
        collected = []
        with open(console_path, "w") as cf:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
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
               "--output-format", "json"] + _resume(payload)
        if MODEL:
            cmd += ["--model", MODEL]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=wall)
        if proc.returncode != 0:
            raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr[:500]}")
        env = json.loads(proc.stdout.strip())
    if env.get("is_error") or env.get("api_error_status"):
        raise RuntimeError(f"claude api error: {env.get('api_error_status') or str(env.get('result',''))[:300]}")
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


def run_claude(task, payload):
    """Static-verb path: prompt + schema come from the in-code PROMPTS/SCHEMAS
    registries keyed by the CI verb (diagnose/fix/merge/...)."""
    if STUB:
        return STUB_RESPONSES[task]
    schema = json.dumps(SCHEMAS[task])
    prompt = PROMPTS[task](payload)
    wall = 1800 if task == "fix" else TIMEOUT
    return _invoke_claude(prompt, schema, payload, wall)


# --- Generic executor (Phase 1A, REQ-AIEXEC-002) -------------------------------
# Control inversion: the task definition is no longer in code. The BPMN flow passes
# `ai_prompt` (instruction) + `ai_output_schema` (the result contract) as process
# variables; the worker forwards them here as payload `prompt` / `output_schema`,
# plus the full process `data`. A new business domain needs NO new platform code.
_GENERIC_DROP = {"ai_prompt", "ai_output_schema", "sid", "_sid", "_piid", "_node",
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
                     + json.dumps(business, ensure_ascii=False, indent=2)[:8000]
                     + "\n```")
    return "\n".join(parts)


def run_claude_generic(payload):
    if not (payload.get("prompt") or "").strip():
        raise RuntimeError("generic executor requires a non-empty `prompt`")
    prompt = prompt_generic(payload)
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
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        task = self.path.rsplit("/", 1)[-1]
        if task not in PROMPTS and task not in ("release", "execute"):
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
            else:
                result = run_claude(task, payload)
            self._send(200, result)
        except subprocess.TimeoutExpired:
            self._send(504, {"error": "task timeout"})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print("[agent-task-node] " + (fmt % args), flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    print(f"[agent-task-node] listening on :{port} (claude={CLAUDE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
