# Phase F — Import the workflow platform to bluesea

Mac-first verification is green (A.2 / B / C / D / E). This runbook deploys the
same compose/images to **bluesea** (arcana.boo, aarch64, `devops_default`,
registry `localhost:5000`) and wires it to the real Jenkins / agent-task-node /
SonataFlow. Most steps need John's `!` (bluesea infra is classifier-gated).

Mac images are **arm64**, bluesea is **aarch64** → directly compatible (no
emulation, no cross-build).

---

## Open decisions (confirm before starting)

1. **Image delivery** — *recommended:* build on Mac (already built for bpmn/swf;
   add rust + dashboard), `docker save` → `scp` → `docker load` on bluesea.
   Avoids building on disk-tight bluesea. (Alt: rsync source + build on bluesea.)
2. **Kafka** — *recommended:* reuse the **existing** bluesea Kafka (the one the
   current SonataFlow uses), not a second broker. Point all engines + Data Index
   at it. Saves RAM and is required for the SonataFlow merge anyway.
3. **PostgreSQL** — *recommended:* one new `kogito-pg` container (DBs: `workflow`
   for engine persistence, `dataindex` for Data Index, `arcana` for read-API).
   Do **not** reuse sonarqube-db / archive PG.
4. **Dashboard exposure** — *recommended:* behind Authelia (2FA) like the other
   bluesea dashboards; publish only on `127.0.0.1:<port>`.

---

## F0 — Pre-flight (John `!`)

Disk is chronically 85–90% on `/data` (sdb). Reclaim first; the Data Index +
two engine + rust + nginx images need headroom.

```bash
# free space + GC (image/builder prune are normally classifier-blocked → John runs)
df -h /data; free -g
docker image prune -af && docker builder prune -af
# confirm the existing kafka + network names to reuse
docker ps --format '{{.Names}}\t{{.Image}}' | grep -iE 'kafka|sonataflow|jenkins|agent-task'
docker network ls | grep devops_default
```

Need (rough): ~2–3 GB disk for images, ~2–3 GB RAM for kogito-pg + 2 engines +
data-index + rust + nginx. Verify before proceeding.

---

## F1 — Build + transfer images (Mac, then John `!` on bluesea)

All five arm64 images are **already built on Mac** (verified):
`arcana/kogito-bpmn:1.0.0`, `arcana/kogito-swf:1.0.0`,
`arcana/arcana-cloud-rust:1.0.0` (via `arcana-cloud-rust/Dockerfile.flow`),
`arcana/dashboard:1.0.0`, `arcana/task-worker:1.0.0`.

On **Mac** (in `arcana-ai-agent-flow/`) — to rebuild any:
```bash
docker build -f arcana-cloud-rust/Dockerfile.flow -t arcana/arcana-cloud-rust:1.0.0 arcana-cloud-rust
docker build -t arcana/dashboard:1.0.0 ./dashboard
docker build -t arcana/task-worker:1.0.0 ./workflow-task-worker
```

Bundle images + deploy assets, transfer:
```bash
docker save arcana/kogito-bpmn:1.0.0 arcana/kogito-swf:1.0.0 \
            arcana/arcana-cloud-rust:1.0.0 arcana/dashboard:1.0.0 \
            arcana/task-worker:1.0.0 | gzip > /tmp/arcana-flow-images.tgz
tar czf /tmp/arcana-flow-assets.tgz \
    docker-compose.bluesea.yml kogito-pg-init data-index-protobufs bpmn
scp /tmp/arcana-flow-images.tgz /tmp/arcana-flow-assets.tgz bluesea:/data/projects/arcana-ai-agent-flow/
```

On **bluesea** (John `!`):
```bash
cd /data/projects/arcana-ai-agent-flow
gunzip -c arcana-flow-images.tgz | docker load
tar xzf arcana-flow-assets.tgz
docker pull docker.io/apache/incubator-kie-kogito-data-index-postgresql:10.0.x-20260329-linux-arm64
```

Build notes baked into the Dockerfiles (lessons from the Mac build):
- read-API (`Dockerfile.flow`) installs `protobuf-compiler` (arcana-grpc needs
  `protoc`); migrations are compile-time embedded (`sqlx::migrate!`), config is
  `default.toml` + `ARCANA__*` env (local.toml excluded).
- dashboard uses `npm install` on `node:24-alpine` (not `npm ci`) so musl/arm64
  optional native deps resolve.

---

## F2 — bluesea compose overlay

Create `docker-compose.bluesea.yml` from the Mac compose with these changes:
- **Network**: attach all services to external `devops_default`.
- **Kafka**: remove the local kafka service; set `KAFKA_BOOTSTRAP` /
  `KAFKA_BOOTSTRAP_SERVERS` to the existing bluesea kafka host:port.
- **kogito-pg**: keep, on a named volume under `/opt/arcana-state/kogito-pg`,
  not publishing 5432.
- **read-API**: `DATA_INDEX_URL=http://data-index:8080`,
  `ARCANA__DATABASE__URL=postgres://…@kogito-pg:5432/arcana`,
  `BPMN_DIR` mounted from the kogito-bpmn resources (or baked into the image),
  redis disabled, gRPC/REST ports internal.
- **dashboard**: nginx image; `proxy_pass` already → `arcana-cloud-rust:8080`;
  publish `127.0.0.1:<port>` only.
- **data-index**: mount the combined `data-index-protobufs/` (BPMN + any SWF
  protos).

Deploy (John `!`):
```bash
docker compose -f docker-compose.bluesea.yml up -d
# health
for s in kogito-pg kogito-bpmn kogito-swf data-index arcana-cloud-rust dashboard; do
  echo "$s: $(docker inspect -f '{{.State.Status}}' aaf-$s 2>/dev/null)"; done
```

---

## F3 — Wire real integrations (worker MODE=real)

Run `workflow-task-worker` (Phase C) in `real` mode so `ai` nodes are completed
by **agent-task-node** and `jenkins` nodes by **Jenkins**:

```bash
docker run -d --name aaf-task-worker --network devops_default \
  -e MODE=real \
  -e ENGINE_URL=http://kogito-bpmn:8080 \
  -e DATA_INDEX_URL=http://data-index:8080 \
  -e AGENT_TASK_URL=http://agent-task-node:8090 \
  -e JENKINS_URL=http://<jenkins>:8080/jenkins \
  -e JENKINS_USER=<user> -e JENKINS_TOKEN=<token> \
  arcana/task-worker:1.0.0   # build from workflow-task-worker/Dockerfile
```

Replace the demo `ci-flow` BPMN with the real CI-maintenance flow (ai = diagnose/
fix via agent-task-node, jenkins = build) once the wiring is verified.

---

## F4 — Merge the two SonataFlow containers (the Phase E decision #1 on bluesea)

Today bluesea runs **two** SonataFlow containers (sonataflow-engine JDK21 +
sf-ci JDK17) sharing a consumer group. Consolidate to **one**:
1. Decide the authoritative config (JDK21 vs JDK17 + `AGENT_TASK_URL`).
2. Add `kie-addons-quarkus-events-process` + the kafka connector + the four
   `kogito-*-events` outgoing channels + the MetricDecorator exclude (same recipe
   as the Mac kogito-swf — see [[reference-kogito-dataindex-stack]]) → rebuild.
3. Cut over carefully: drain in-flight, stop the second container, point the
   single engine at the shared Data Index's kafka topics.
4. Its CI flows then appear in the dashboard with `engine=swf`.

⚠️ Do this last and with care — in-flight CI runs must not be lost.

---

## F5 — Expose + end-to-end verify

- Put the dashboard behind Authelia (2FA), same pattern as the existing bluesea
  dashboards; external URL via the reverse proxy.
- Trigger a real red CI build → confirm a BPMN flow appears, the `ai` node is
  completed by agent-task-node, the `jenkins` node by a Jenkins build, and the
  flow reaches End — all visible live in the dashboard, alongside any SonataFlow
  (`swf`) CI-maintenance instances.

---

## Rollback

All new; nothing pre-existing is replaced until F4. To back out: `docker compose
-f docker-compose.bluesea.yml down` + remove `aaf-task-worker`. The SonataFlow
merge (F4) is the only step touching existing infra — keep the second container's
image/config to restore if needed.
