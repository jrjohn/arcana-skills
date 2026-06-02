# arcana-ai-agent-flow-skill

A self-service **workflow monitoring platform**: define role-based flows, watch
instances + a live flow diagram in real time, and let an agent fleet drive them.

- **Dual engine** — Kogito **BPMN** (human/role decision flows) + **SonataFlow**
  (automated flows) → one **Kogito Data Index** (PostgreSQL, GraphQL).
- **Engine-agnostic read-API** — `arcana-cloud-rust` (Axum) serves
  `/api/v1/workflows/*` (processes / instance / timeline / definition graph),
  annotating each instance with `engine` (bpmn/swf), `currentNode`, `currentRole`.
- **Angular dashboard** — multi-instance task list (status filter, default
  ACTIVE) + live SVG flow diagram (role lanes ai/jenkins, visited/current/pending
  highlight, 3s polling), behind nginx `/api` proxy (single origin).
- **task-worker** — drives flows: `ai` → agent-task-node (Claude `/task/diagnose`
  +`/task/fix`), `jenkins` → Jenkins rebuild.
- **CI trigger** — Jenkins red build → creates a BPMN instance (orchestrated,
  visible) instead of opaque inline logic.

Built Mac-first, deployed to bluesea behind Authelia 2FA at
`https://workflow.arcana.boo`.

## Layout
- `SKILL.md` — entry point: architecture, when-to-use, components, build/deploy, gotchas.
- `references/architecture.md` — full dual-engine design + Cannerflow spirit + role model.
- `references/deploy-bluesea.md` — production import runbook (images, compose overlay, worker, Authelia subdomain, B2 trigger).
- `references/build-gotchas.md` — every build/deploy trap + fix.
- `templates/` — runnable artifacts: engines (kogito-bpmn, kogito-swf), read-api (controller + clients + Dockerfile), dashboard (nginx + Dockerfile), workflow-task-worker, bluesea-jenkins trigger, docker-compose (mac + bluesea) + deploy-bluesea.sh.

## Quick start
See `SKILL.md` → "Build & deploy". Mac-first: `docker compose -f
templates/docker-compose.mac.yml up -d --build`. Production: build arm64 images,
ship + `deploy-bluesea.sh`, front with Authelia.
