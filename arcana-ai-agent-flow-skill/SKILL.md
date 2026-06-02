---
name: arcana-ai-agent-flow-skill
description: Build & operate a self-service workflow monitoring platform with role-based BPMN + automated SonataFlow on one queryable layer, an engine-agnostic read-API, and a live Angular dashboard. A dual Kogito engine (BPMN for human/role decision flows, SonataFlow for fully-automated flows) feeds one Kogito Data Index; arcana-cloud-rust (Axum) serves /api/v1/workflows/*; an Angular SPA shows a multi-instance task list + live SVG flow diagram (role lanes, current/visited highlight); a task-worker drives flows (ai→agent-task-node/Claude, jenkins→Jenkins). Use when the user wants a workflow engine + real-time monitoring dashboard, to orchestrate CI remediation as a visible role-based flow, or to deploy this stack behind Authelia. Triggers "arcana-ai-agent-flow", "workflow monitor", "工作流監控", "BPMN dashboard", "Kogito Data Index", "SonataFlow 監控", "流程引擎 + dashboard".
skill_name: arcana-ai-agent-flow-skill
skill_version: 1.0.0
created_date: 2026-06-02
skill_type: complex
status: production (deployed to bluesea / workflow.arcana.boo)
---

# arcana-ai-agent-flow skill

A self-service, layered workflow platform: define flows (each node assigned a
**role**), watch instances + a **live flow diagram** in real time, and have an
agent fleet **drive** the flows. Built Mac-first, deployed to bluesea behind
Authelia 2FA at `https://workflow.arcana.boo`.

## What this builds

```
[人工/角色決策] Kogito BPMN 引擎          [全自動] SonataFlow 引擎
  BPMN, node GroupId=ai|jenkins             CNCF .sw.yaml, no human tasks
        └── process/task events ─┐     ┌── process events
                                 ▼     ▼
              Kogito Data Index (PostgreSQL)  ← one queryable layer (GraphQL)
                                 │  ProcessDefinition.type = BPMN | SW
                                 ▼
   arcana-cloud-rust  /api/v1/workflows/*  (Axum read-API, engine-agnostic)
     /processes (status+role filter, currentNode+currentRole+engine)
     /processes/:id  /processes/:id/timeline  /definitions/:id/graph
                                 ▼  (/api proxy, single origin → no CORS)
   Angular dashboard → nginx     +    workflow-task-worker (drives flows)
     multi-instance table              ai      → agent-task-node (Claude)
     live SVG flow diagram             jenkins → Jenkins build
     (role lanes, polling 3s)
```

**Design spirit (Cannerflow):** roles are first-class; engines are abstracted
behind a clean semantic read-API; the UI speaks goal/flow/role, never BPMN XML.
See `references/architecture.md`.

## When to use

- User wants a **workflow engine + real-time monitoring** (task list + dynamic
  flow diagram), with process design + instances stored in PostgreSQL.
- Orchestrate **CI failure remediation as a visible role-based flow** (red build
  → diagnose(ai) → rebuild(jenkins) → decide(ai)) instead of opaque inline logic.
- Dual-engine: human/role decision flows (BPMN) **and** automated flows
  (SonataFlow) on one dashboard, distinguished by an `engine` badge.

## Components (templates/)

| Path | What |
|---|---|
| `kogito-bpmn/` | Quarkus 3.8.4 + Kogito 10 BPMN engine (flattened standalone pom, PG persistence, **kafka events addon**). `ci-flow.bpmn2` = Start→Triage(ai)→Build(jenkins)→Decide(ai)→End, each userTask `GroupId`-assigned. |
| `kogito-swf/` | SonataFlow engine (`org.apache.kie.sonataflow:sonataflow-quarkus`), `ci-maintenance.sw.yaml` automated flow → same Data Index. |
| `read-api/` | `workflow_controller.rs` (engine-agnostic endpoints), `data_index.rs` (GraphQL client), `bpmn.rs` (parse sequence-flow edges + GroupId roles), `Dockerfile.flow` (installs `protobuf-compiler`). Drop into a copy of the arcana-cloud-rust template; **repository must be PostgreSQL**. |
| `dashboard/` | nginx.conf (SPA + `/api` proxy via resolver+variable) + Dockerfile (node:24, `npm install`). Build the Angular feature with angular-developer-skill: multi-instance table (Process/Engine/Instance/State/CurrentNode/Role/Started/Completed, default ACTIVE filter, click→detail) + SVG flow-diagram (role lanes, visited/current/pending). |
| `workflow-task-worker/` | stdlib-python poller: ready Data-Index tasks → node-aware dispatch (Triage→agent-task-node `/task/diagnose` [+`/task/fix` on red `*/main` fixable code/deps/test], Build→Jenkins rebuild, Decide→from result). `MODE=auto` (local) / `real` (prod). |
| `bluesea-jenkins/ci-bpmn-trigger.groovy` | Jenkins RunListener: any non-SUCCESS build → POST create a ci-flow BPMN instance (replaces inline routine). |
| `docker-compose.mac.yml` | Local stack (adds its own kafka). |
| `docker-compose.bluesea.yml` + `.mac.yml` + `deploy-bluesea.sh` + `kogito-pg-init/` | Production overlay (external devops_default, reuse existing kafka, kogito-pg 3 DBs) + one-shot deploy script + Mac dry-run override. Includes `ci-scheduler` (hourly `ci-maintenance` heartbeat → always-fresh dashboard; `SCHEDULE_SECS` tunable). |

## Build & deploy

1. **Mac-first**: `cd <project> && docker compose -f docker-compose.mac.yml up -d --build`; verify Data Index GraphQL (`:8180/graphql`) returns ProcessInstances + UserTaskInstances with `potentialGroups`; read-API + dashboard via the proxy. (Engines need `mvn clean package` first — see gotchas.)
2. **read-API**: copy the arcana-cloud-rust template (don't edit the upstream), port its repository **MySQL→PostgreSQL**, add the `read-api/` files, wire `clients` mod + `workflow_client`/`bpmn_repo` into `AppState` + nest `/workflows` after the auth layer (no token).
3. **bluesea**: build 5 arm64 images, `docker save | ssh | docker load`, ship `deploy-bluesea.sh` + assets, create `.env` (secrets), `./deploy-bluesea.sh [--with-worker]`. Front with Authelia (subdomain + cert + nginx server block). See `references/deploy-bluesea.md`.

## Critical gotchas (full list in `references/build-gotchas.md`)

- Events addon needs the **kafka connector**: add `quarkus-smallrye-reactive-messaging-kafka` (NOT `quarkus-messaging-kafka` — not in quarkus-bom 3.8.4) **and** `quarkus.arc.exclude-types=io.smallrye.reactive.messaging.providers.metrics.MetricDecorator`.
- Data Index image (arm64): `apache/incubator-kie-kogito-data-index-postgresql:10.0.x-20260329-linux-arm64`; mount each engine's `target/classes/META-INF/resources/persistence/protobuf` into `/home/kogito/data/protobufs`.
- read-API prod Dockerfile must `apt-get install protobuf-compiler` (arcana-grpc/prost-build needs `protoc`); set `ARCANA__SECURITY__GRPC_TLS_ENABLED=false` (production.toml enables it).
- nginx `/api` proxy: use `resolver 127.0.0.11` + `set $upstream …; proxy_pass $upstream;` (no URI) so it survives upstream restarts AND forwards the full `/api/...` path.
- `engine` field comes from Data Index `ProcessDefinition.type` (`BPMN`→bpmn, `SW`→swf); `ProcessInstance` has no `type`.
- Dashboard Dockerfile: `node:24-alpine` + `npm install` (not `npm ci`) for musl/arm64 native optional deps.

## References
- `references/architecture.md` — full dual-engine design, layers, role model, decisions.
- `references/deploy-bluesea.md` — bluesea import runbook (images, compose overlay, worker, Authelia subdomain, B2 Jenkins trigger).
- `references/build-gotchas.md` — every build/deploy trap hit + fix.
