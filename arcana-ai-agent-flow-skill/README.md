# arcana-ai-agent-flow-skill

An autonomous **CI workflow platform**: a single Kogito BPMN engine runs three
processes, an agent fleet drives them, humans take over seamlessly when AI
can't finish, and everything is watched live on a bpmn-js dashboard.

- **Single engine** — Kogito **BPMN** (SonataFlow retired 2026-06-09) running
  **ci-flow** (red-build remediation: Triage→Build→Fix⟲→Decide, unfixable →
  parked `humanFixTask`), **merge-flow** (green PR: Merge(ai)→Release(ai) —
  squash-merge + release-please, full-auto releases), **ci-maintenance**
  (hourly read-only governance: Scan→Analyze(ai)→Remediate→Verify) → one
  **Kogito Data Index** (PostgreSQL, GraphQL).
- **Engine-agnostic read-API** — `arcana-cloud-rust` (Axum) serves
  `/api/v1/workflows/*` (processes / instance / timeline / graph / **raw BPMN
  XML** for bpmn-js), annotating each instance with `currentNode`/`currentRole`.
- **Angular dashboard** — instance table + **bpmn-js** flow diagram
  (visited/current/error highlight, polling) + **handoff banner** (parked human
  task → copyable `docker exec -it agent-task-node claude --resume <sid>`),
  behind nginx `/api` proxy (single origin).
- **task-worker (Rust, 1.3.0)** — dispatch by task name
  (triage/build/fix/decide/analyze/merge/release): `ai` → agent-task-node
  (Claude CLI with session persistence, `sid` threading; `/task/release` is
  deterministic release-please), `jenkins` → Jenkins rebuild, `human` → **never
  auto-completed** (parked). Reconciler (300s) repairs Data-Index drift from
  engine truth.
- **Self-fixing Fix(ai) node** — the agent fixes red builds autonomously before
  escalating: **archive-first** (vsearch/csearch the session archive for a proven
  fix — a human's manual fix is ingested ~15 min later and reused next time), a
  **dependency-major playbook** (peer-dep coupling → bundle the framework codemod
  e.g. `ng update`; test-runner-major coverage drop → `coverage.exclude`; stale
  lockfile → regenerate), and **disposable-container builds** (`docker run node:24
  …`) to use toolchains its own container lacks. Pushes to the PR branch; main
  stays review-gated. Novel failures still park for human handoff.
- **ci-maint-endpoint (Rust Axum)** — read-only health probe
  (`/scan` `/remediate` `/verify`), zero docker socket.
- **CI trigger v7** — Jenkins RunListener: red build → ci-flow (6h cooldown);
  fleet-wide green PR build → merge-flow (autonomous merge + release).

Built Mac-first, deployed to bluesea behind Authelia 2FA at
`https://workflow.arcana.boo`.

## Layout
- `SKILL.md` — entry point: architecture, the three processes, components, build/deploy, gotchas.
- `references/architecture.md` — single-engine design + Cannerflow spirit + flow details.
- `references/deploy-bluesea.md` — production runbook (images, compose, agent prereqs incl. GH_TOKEN/npx, Authelia, B2 trigger v7).
- `references/build-gotchas.md` — every build/deploy/ops trap + fix.
- `templates/` — runnable artifacts: kogito-bpmn engine (all three production `.bpmn2`), workflow-task-worker (Rust: main.rs/Cargo.toml/Dockerfile), read-api (controller + clients + Dockerfile), dashboard (nginx + Dockerfile), bluesea-jenkins trigger (v7), docker-compose (mac + bluesea) + deploy-bluesea.sh.

## Quick start
See `SKILL.md` → "Build & deploy". Mac-first: `docker compose -f
templates/docker-compose.mac.yml up -d --build`. Production: build arm64 images,
ship + `deploy-bluesea.sh`, front with Authelia.
