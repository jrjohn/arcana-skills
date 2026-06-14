---
name: arcana-ai-agent-flow-skill
description: Build & operate an autonomous CI workflow platform on a SINGLE Kogito BPMN engine (SonataFlow retired 2026-06-09) running three processes — ci-flow (red-build remediation with human handoff — park at humanFixTask, resume the agent's Claude session via `claude --resume <sid>`), merge-flow (verified-green PR automerge + automatic release-please releases), ci-maintenance (hourly read-only health governance) — all feeding one Kogito Data Index, driven by a Rust task-worker dispatching to a Claude agent-task-node, monitored live on an Angular bpmn-js dashboard behind Authelia. Use when the user wants a workflow engine + real-time monitoring dashboard, autonomous CI remediation/merge/release as visible BPMN flows, or AI-to-human handoff with session continuity. Triggers "arcana-ai-agent-flow", "workflow monitor", "工作流監控", "BPMN dashboard", "Kogito Data Index", "green PR automerge", "human handoff", "流程引擎 + dashboard".
skill_version: 1.1.0
created_date: 2026-06-02
skill_type: complex
status: production (deployed to bluesea / workflow.arcana.boo)
---

# arcana-ai-agent-flow skill

An autonomous CI workflow platform: a **single Kogito BPMN engine** runs three
processes (remediate red builds, automerge + release green PRs, hourly health
governance), an agent fleet **drives** them (Claude + Jenkins), humans take over
seamlessly when AI can't finish, and everything is watched live on a bpmn-js
dashboard. Built Mac-first, deployed to bluesea behind Authelia 2FA at
`https://workflow.arcana.boo`.

> SonataFlow (the former second engine) was **retired 2026-06-09** — its only
> flow (ci-maintenance) was a heartbeat shell, BPMN is a superset of SWF for
> this platform, and SWF's real edge (Knative scale-to-zero) was unused with
> both engines running as always-on containers. ci-maintenance was ported to
> BPMN; one engine now runs everything.

## What this builds

```
Jenkins RunListener (ci-bpmn-trigger.groovy v7)            ci-scheduler (hourly)
  red build ──POST /ci-flow (6h cooldown)─┐                  POST /ci-maintenance
  green PR build (fleet-wide) ─POST /merge-flow─┐                   │
                                          ▼     ▼                   ▼
                 Kogito BPMN engine (Quarkus, PG persistence, kafka events)
                   ci-flow:        Triage(ai)→Build(jenkins)→Fix(ai)⟲→Decide(ai)
                                     →endGate→ humanFixTask(human) | End
                   merge-flow:     Start→Merge(ai)→Release(ai)→End
                   ci-maintenance: Scan→Analyze(ai)→Remediate→Verify  (scriptTasks
                                     → ci-maint-endpoint, read-only, no docker sock)
                        │ process/task events (kafka)
                        ▼
            Kogito Data Index (PostgreSQL, GraphQL)  ← one queryable layer
                        ▼
   arcana-cloud-rust  /api/v1/workflows/*  (Axum read-API, BPMN_DIR → bpmn-js XML)
                        ▼  (/api proxy, single origin)
   Angular dashboard (bpmn-js diagrams, handoff banner w/ claude --resume cmd)
                        +
   workflow-task-worker (RUST) — dispatch by task name; group=human NEVER
   auto-completed (parked); reconciler repairs Data Index from engine truth
     ai      → agent-task-node (Claude CLI, persistent session via sid)
     jenkins → Jenkins rebuild
```

## When to use

- User wants a **workflow engine + real-time monitoring** (task list + live
  bpmn-js flow diagram), with processes + instances stored in PostgreSQL.
- Orchestrate **CI failure remediation as a visible role-based flow** (red build
  → diagnose(ai) → rebuild(jenkins) → fix(ai) → decide(ai)) with **human
  handoff** instead of dead-ending: unfixable builds park at a human task and
  the human resumes the agent's exact Claude session.
- **Autonomous green-PR merging + releases**: any fleet PR that builds green is
  verified and squash-merged by the agent, then release-please runs on every
  merge — release PRs are themselves green → automerged → releases cut
  **full-auto** (requires conventional commits; Renovate PRs qualify).
- **Hourly health governance** as an auditable flow: read-only scan → AI
  analysis (severity + recommendation) → bounded remediation → verify, all
  process vars visible in the dashboard (KPI/audit).

## The three processes (templates/kogito-bpmn/*.bpmn2 — production copies)

| Process | Shape | Notes |
|---|---|---|
| `ci-flow` | Triage(ai)→Build(jenkins)→[fixable? Fix(ai)→Build ⟲3]→Decide(ai)→endGate | endGate: green or AI-judged-merged → End; else → **humanFixTask (group=human)** — parked until a human completes it `out=verify` (re-Build) or `out=giveup` (→failEnd). `sid` process var threads ONE Claude conversation through triage/fix/decide and is what the human resumes. |
| `merge-flow` | Start→Merge(ai)→Release(ai)→End | Merge: agent re-checks `gh pr view/checks` (open + green + no conflicts) then `gh pr merge --squash --delete-branch`. Release: via agent `/task/release` — FIRST a scoped claude **readme-sync** pass (syncs README **version claims** vs the repo's dependency manifests via `gh api`, PLUS the dynamic **Tests** badge from the latest green main build's Jenkins console and the **Coverage** badge from the **SonarQube** measures API — `coverage` metric, projectKey read from the Jenkinsfile; commits `docs: sync README versions + CI badges` if stale, leaves a badge unchanged if the number can't be determined reliably), THEN deterministic `npx release-please@16 github-release` + `release-pr` (released detection = ground-truth latest-tag before/after, not output parsing); skips repos without release-please-config. `POST /task/readmesync {repo}` also works standalone. |
| `ci-maintenance` | Scan→Analyze(ai)→Remediate→Verify | scriptTasks call `boo.arcana.MaintHttp` → ci-maint-endpoint (`/scan` disk+Jenkins+cron results, `/remediate` only re-onlines Jenkins nodes, `/verify`). Analyze = AI severity/recommendation. Execution stays on host cron; flow is read-only orchestration + record. |

## Components (templates/)

| Path | What |
|---|---|
| `kogito-bpmn/` | Quarkus 3.8.4 + Kogito 10 BPMN engine (flattened standalone pom, PG persistence, **kafka events addon**). Ships all three `.bpmn2` (production copies). userTasks are `GroupId`-assigned (ai/jenkins/human). |
| `workflow-task-worker/` | **Rust** poller (`main.rs`, image `arcana/task-worker:1.3.0`): ready Data-Index tasks → dispatch by lowercased task name — triage/build/fix/decide/analyze/merge/release. Task-level tokio concurrency (fix=1, ai=2, jenkins=3). **group=human is NEVER auto-completed** — parked (stays Ready, logs `⏸ PARKED` once). `with_sid()`/`pick_sid()` thread the Claude session id through ai tasks. Reconciler (every `RECONCILE_SECS=300`, writes DI's PG directly) repairs Data-Index drift from **engine truth** both ways — survives kafka outages. `MODE=auto` (local synth) / `real` (prod). |
| `read-api/` | `workflow_controller.rs` (engine-agnostic endpoints incl. `/definitions/{id}/bpmn` → raw XML for bpmn-js), `data_index.rs` (GraphQL client), `bpmn.rs` (sequence-flow edges + GroupId roles), `Dockerfile.flow` (installs `protobuf-compiler`). Drop into a copy of the arcana-cloud-rust template; **repository must be PostgreSQL**. Reads `BPMN_DIR=/app/bpmn`. |
| `dashboard/` | nginx.conf (SPA + `/api` proxy via resolver+variable) + Dockerfile (node:24, `npm install`). Angular: multi-instance table + **bpmn-js** diagram (falls back to custom SVG only if no BPMN XML). **Handoff banner**: a run with a Ready human-group task shows amber banner with `sid` + copyable `docker exec -it agent-task-node claude --resume <sid>`. `nodeStatus()` honors instance state (FaultNode→Failed when terminal, not perma-Running). |
| `bluesea-jenkins/ci-bpmn-trigger.groovy` | RunListener **v7** (production copy): red build → POST `/ci-flow` (6h per-job cooldown); green PR build, fleet-wide (`.*-app(-pipeline)?-mb/.*` + CHANGE_URL) → POST `/merge-flow {job,prUrl}`. Install to `init.groovy.d`, hot-apply via `/scriptText`. |
| `docker-compose.bluesea.yml` (+ `.mac.yml`, `deploy-bluesea.sh`, `kogito-pg-init/`) | Production compose (synced): kogito-pg (3 DBs), kogito-bpmn, **ci-maint-endpoint** (Rust Axum, `/data` + `/var/log` read-only, Jenkins API, **zero docker socket**), data-index, read-API, dashboard, task-worker (`RECONCILE_GROUPS=ai,jenkins,human`), ci-scheduler (hourly ci-maintenance POST). |
| `docker-compose.mac.yml` | Local stack (adds its own kafka). |

## Fix-node remediation strategy (ci-flow `Fix(ai)`)

The Fix node (worker → agent-task-node `/task/fix`, prompt in `server.py`) is built to fix autonomously and only escalate when it genuinely can't:

1. **Archive-first** — before reinventing, it `vsearch`/`csearch` the shared session archive for a proven fix to the same root cause. Every past fix (any session) is recallable; a human's manual fix gets ingested (~15 min) and becomes the agent's playbook for the next occurrence.
2. **Dependency-major playbook** (encoded in the prompt so it's recognised on first sight) — renovate `chore(deps)` majors fail in patterned ways:
   - **peer-dep coupling** — a tooling major can't go alone (e.g. `typescript` 6 is locked to Angular 22; `npm ci` shows ERESOLVE `peer … from @angular/*`). Fix = bundle the framework major via its official codemod (`ng update @angular/core@N @angular/cli@N @angular/cdk@N`), which auto-applies migration schematics, then ONE combined PR.
   - **quality-gate coverage drop** after a test-runner major (vitest/jest) — tests pass but SonarQube `coverage < 80`. The runner changed coverage *scope* (e.g. vitest v4 newly counts 0%-covered bootstrap/entry files). Fix = add them to `coverage.exclude` (same category as already-excluded `src/index.ts`) — never pad fake tests or lower the gate.
   - **lockfile out of sync** (`renovate/artifacts` failed) → regenerate (`npm install`) + commit.
3. **Disposable-container build** — the agent container has python/java/rust + the docker CLI but only node v22 and no go/gradle. When a fix needs a toolchain it lacks or a newer version (e.g. `ng update` to Angular 22 needs node ≥ 24.15), it builds in a throwaway official-image container exactly like CI (`docker run --rm -v $(pwd):/w -w /w node:24 …`) instead of parking with "can't build locally". (`permissions.allow` has bare `Bash` → docker runs headless.)
4. **Close the loop** — applies the fix to the PR-head branch the failing pipeline will rebuild (feature branches aren't protected); only fixes that must target main open a PR + stop (review-gated).

**Self-fixes vs parks:** code-level API breaks (fixed go#31 mongo-driver `coverage.out` → merged), recurrences, and known patterns → self-fix; a genuinely-novel failure the first time → park for human handoff (below). Big framework majors stay review-gated even when buildable (pushed to the PR branch, never auto-merged to main).

## Human handoff (ci-flow)

1. AI can't fix → endGate routes to `humanFixTask` (group=human); worker parks it.
2. Dashboard shows the parked run (`currentNode=HumanFix`) + banner with the command:
   `docker exec -it agent-task-node claude --resume <sid>` — re-attaches the
   **same Claude conversation** the agent used (agent-task-node runs `claude -p`
   WITH session persistence; `/root/.claude` is a host bind mount so sessions
   survive recreate).
3. Human fixes, then completes the task `out=verify` (loops back to Build to
   confirm green) or `out=giveup` (→ failEnd).

## Build & deploy

1. **Mac-first**: `docker compose -f docker-compose.mac.yml up -d --build`;
   verify Data Index GraphQL (`:8180/graphql`) returns ProcessInstances +
   UserTaskInstances with `potentialGroups`. (Engine needs `mvn clean package`
   first — central-only mirror, see gotchas.)
2. **read-API**: copy the arcana-cloud-rust template (don't edit upstream), port
   repository **MySQL→PostgreSQL**, add `read-api/` files, nest `/workflows`
   after the auth layer (no token).
3. **bluesea**: build arm64 images, `docker save | ssh | docker load` (worker +
   engine can also build ON bluesea: worker is self-contained Rust; engine via
   maven-docker jar then `docker build`), `./deploy-bluesea.sh [--with-worker]`,
   front with Authelia. Agent `/task/release` needs `GH_TOKEN` + node/npx in the
   agent container. See `references/deploy-bluesea.md`.

## Critical gotchas (full list in `references/build-gotchas.md`)

- Engine Maven build in containers: jboss.org repo is flaky → **central-only
  mirror + `-U`** or the build stalls (see memory kogito-bpmn-maven-jboss-trap).
- **BPMN XML comments must not contain `--`** (e.g. `claude --resume`) —
  Kogito codegen dies with SAXParseException "string -- not permitted".
- **Changing a process's node structure without bumping its version** leaves
  stale rows in Data Index `definitions_nodes` (old + new nodes overlay on the
  same `version=1.0`) → garbled diagram. Bump the version, or DELETE the stale
  node ids. Instances execute correctly either way.
- **After engine `--force-recreate`, restart the task-worker** — its in-memory
  ready cache goes stale (shows N ready while engine/DI have 0).
- Kafka outage ≠ lost instances: the engine is the source of truth; the worker
  re-checks `complete()` failures against the engine and the **reconciler**
  repairs Data Index both ways. Never abort instances off stale DI work-items.
- Events addon needs the kafka connector `quarkus-smallrye-reactive-messaging-kafka`
  (NOT `quarkus-messaging-kafka`) + the MetricDecorator ArC exclude.
- nginx `/api` proxy: `resolver 127.0.0.11` + `set $upstream …; proxy_pass $upstream;`
  (no URI) so it survives upstream restarts and forwards the full path.
- New/changed BPMN diagram on the dashboard: ship the `.bpmn2` to `./bpmn/`,
  restart the read-API, and hard-refresh the SPA (bpmnXml signal cache).

## References
- `references/architecture.md` — single-engine design, the three flows, role model, decisions.
- `references/deploy-bluesea.md` — bluesea runbook (images, compose, worker, Authelia, B2 trigger).
- `references/build-gotchas.md` — every build/deploy trap hit + fix.
