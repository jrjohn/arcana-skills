# Deploy the workflow platform to bluesea

Runbook for deploying the compose/images to **bluesea** (arcana.boo, aarch64,
`devops_default`, behind Authelia at `https://workflow.arcana.boo`) and wiring
the real Jenkins / agent-task-node. Most steps need John's `!` (bluesea infra is
classifier-gated). Mac images are **arm64** → directly compatible.

> **Single engine** since 2026-06-09: the `kogito-swf` service was **removed
> from the compose** (SonataFlow retired; ci-maintenance ported to BPMN). If
> upgrading an older deployment: `docker stop/rm aaf-kogito-swf && docker rmi
> arcana/kogito-swf:1.0.0`, point ci-scheduler's POST at
> `aaf-kogito-bpmn:8080/ci-maintenance`, drop the service + depends_on.

---

## Decisions (settled)

1. **Image delivery** — build on Mac, `docker save | scp | docker load`. The
   worker and engine can ALSO build directly on bluesea (worker = self-contained
   Rust `docker build workflow-task-worker/`; engine = maven-docker jar
   `docker run maven:3.9-eclipse-temurin-21 mvn -DskipTests package` with the
   central-only mirror, then `docker build kogito-bpmn/`).
2. **Kafka** — reuse the existing bluesea kafka (`KAFKA_BOOTSTRAP=kafka:9092`).
3. **PostgreSQL** — one `kogito-pg` container (DBs: `workflow`, `dataindex`,
   `arcana`). Don't reuse sonarqube-db / archive PG. Engine state persists in
   kogito-pg across container recreates.
4. **Dashboard exposure** — behind Authelia (2FA), publish `127.0.0.1:<port>` only.

---

## 1 — Pre-flight (John `!`)

```bash
df -h /data; free -g
docker ps --format '{{.Names}}\t{{.Image}}' | grep -iE 'kafka|jenkins|agent-task'
docker network ls | grep devops_default
```

---

## 2 — Images

Current production set:

| Image | Notes |
|---|---|
| `arcana/kogito-bpmn:1.0.0` | the single engine — ci-flow + merge-flow + ci-maintenance |
| `arcana/ci-maint-endpoint:1.0.0` | Rust Axum read-only probe (`/scan` `/remediate` `/verify`); mounts `/data:ro` + `/var/log:ro`; **no docker socket** |
| `arcana/arcana-cloud-rust:1.0.0` | read-API (`Dockerfile.flow`, installs `protobuf-compiler`) |
| `arcana/dashboard:1.0.0` | Angular + nginx (bpmn-js diagrams, handoff banner) |
| `arcana/task-worker:1.3.0` | **Rust** worker — 1.1.0 added human-park + sid threading, 1.2.0 analyze, **1.3.0 release dispatch** |
| `apache/incubator-kie-kogito-data-index-postgresql:10.0.x-20260329-linux-arm64` | pull |

Transfer (Mac):
```bash
docker save arcana/kogito-bpmn:1.0.0 arcana/ci-maint-endpoint:1.0.0 \
            arcana/arcana-cloud-rust:1.0.0 arcana/dashboard:1.0.0 \
            arcana/task-worker:1.3.0 | gzip > /tmp/arcana-flow-images.tgz
tar czf /tmp/arcana-flow-assets.tgz \
    docker-compose.bluesea.yml deploy-bluesea.sh kogito-pg-init data-index-protobufs bpmn
scp /tmp/arcana-flow-*.tgz bluesea:/data/projects/arcana-ai-agent-flow/
```

`./bpmn/` must contain ALL three `.bpmn2` (the read-API serves them to bpmn-js
via `BPMN_DIR=/app/bpmn`) — they live in the engine source AND in `./bpmn/`.

---

## 3 — Compose up

On bluesea (John `!`): `gunzip -c … | docker load`, `tar xzf …`, create `.env`
(PG_PASSWORD, JWT_SECRET ≥32 chars, KAFKA_BOOTSTRAP, JENKINS_URL/USER/TOKEN,
AGENT_TASK_URL, DASHBOARD_PORT), then `./deploy-bluesea.sh [--with-worker]`.

Worker env that matters (see compose):
- `MODE=real`, `AGENT_TASK_URL=http://agent-task-node:8090`
- `DATAINDEX_PG=…/dataindex` + `RECONCILE_SECS=300` — the reconciler repairs
  Data-Index drift from engine truth (kafka outages).
- `RECONCILE_PROCESS_IDS=ci-flow,merge-flow` (ci-maintenance completes in
  seconds, no zombie risk) and `RECONCILE_GROUPS=ai,jenkins,human` (human keeps
  parked handoff tasks visible).

---

## 4 — agent-task-node prerequisites

The agent container (separate project, `claude-agents-workflow/agent-task-node`)
must have:
- `claude` CLI **with session persistence** (no `--no-session-persistence`),
  `--output-format json`; `/root/.claude` is a **host bind mount**
  (`/data/projects/daily-ci-agent/claude-home`) so sessions survive recreate.
- endpoints `/task/diagnose|fix|decide|merge|analyze` (Claude) and
  `/task/release` (**deterministic** — runs `npx release-please@16`); for
  release it needs **`GH_TOKEN` + node/npx** in the container, plus `gh` for
  merge.
- headless `claude -p` runs tools WITHOUT `--dangerously-skip-permissions` via
  settings.json `permissions.allow`.

Human handoff operation: a parked run shows `currentNode=HumanFix` + an amber
dashboard banner; take over with
`docker exec -it agent-task-node claude --resume <sid>`, then complete the task
`out=verify` (re-Build) or `out=giveup`.

---

## 5 — B2 Jenkins trigger (v7)

Install `bluesea-jenkins/ci-bpmn-trigger.groovy` (v7) to
`jenkins:/var/jenkins_home/init.groovy.d/ci-routine-trigger.groovy` (restart
persistence) and hot-apply via `/jenkins/scriptText` (admin token):
- **red build** → POST `http://aaf-kogito-bpmn:8080/ci-flow {subject,job,buildUrl,result}`
  with a **6h per-job cooldown**;
- **green PR build**, fleet-wide gate `job ==~ /.*-app(-pipeline)?-mb\/.*/` +
  CHANGE_URL set → POST `/merge-flow {job,prUrl}`.

`aaf-kogito-bpmn:8080` is reachable only inside `devops_default` (host curl
gets 000) — test POSTs from a container on that network.

---

## 6 — Expose + end-to-end verify

- Authelia subdomain: per-host cert (`certbot certonly --nginx --cert-name
  workflow.arcana.boo`); Authelia unchanged if its session cookie domain is
  `arcana.boo` + `default_policy: two_factor`.
- Verify: red build → ci-flow instance visible live, ai/jenkins nodes complete,
  green→End / unfixable→parked HumanFix banner. Green PR → merge-flow →
  squash-merged + Release var (`released=…` or `skipped`). Hourly
  ci-maintenance instance with scan/analysis/remediate/verify vars.

## Upgrade / rollback notes

- Engine rebuild: `mvn -DskipTests package` (central-only mirror) → `docker
  build` → `docker compose … up -d --force-recreate --no-deps kogito-bpmn` —
  safe at 0 ACTIVE instances; state survives in kogito-pg. **Then `docker
  restart aaf-task-worker`** (stale in-memory ready cache after engine
  recreate).
- Keep rollback tags (`:pre-stage2`, `:pre-human-handoff` style) before risky
  bumps.
- Mac is the full source of truth; bluesea `/data/projects/arcana-ai-agent-flow`
  is a deploy copy (sync via scp/rsync; neither is git-tracked).
