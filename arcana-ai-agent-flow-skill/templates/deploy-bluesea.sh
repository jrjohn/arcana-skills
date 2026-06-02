#!/usr/bin/env bash
#
# deploy-bluesea.sh — bring up the Arcana workflow platform on bluesea.
#
# Run ON bluesea, from the deploy dir (/data/projects/arcana-ai-agent-flow),
# AFTER the images are loaded + assets present (deploy.sh checks both).
#
# Secrets are NEVER embedded here — they come from a local `.env` you create
# (chmod 600). This script only reads it.
#
#   cd /data/projects/arcana-ai-agent-flow
#   umask 077; cat > .env <<'ENV'
#   JWT_SECRET=<at least 32 random chars>
#   DASHBOARD_PORT=8095
#   KAFKA_BOOTSTRAP=kafka:9092
#   # --- only if enabling flow automation (--with-worker) ---
#   WORKER_MODE=real
#   AGENT_TASK_URL=http://agent-task-node:8090
#   JENKINS_URL=http://jenkins:8080/jenkins
#   JENKINS_USER=admin
#   JENKINS_TOKEN=<jenkins token>
#   ENV
#   chmod 600 .env
#
#   ./deploy-bluesea.sh              # monitoring stack only (no CI triggering)
#   ./deploy-bluesea.sh --with-worker  # also run task-worker (fires real CI)
#
set -euo pipefail

COMPOSE_FILE="docker-compose.bluesea.yml"
ENV_FILE=".env"
WITH_WORKER=0
[[ "${1:-}" == "--with-worker" ]] && WITH_WORKER=1

MON_SERVICES=(kogito-pg kogito-bpmn kogito-swf data-index arcana-cloud-rust dashboard)
IMAGES=(arcana/kogito-bpmn:1.0.0 arcana/kogito-swf:1.0.0 \
        arcana/arcana-cloud-rust:1.0.0 arcana/dashboard:1.0.0 arcana/task-worker:1.0.0)

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
info()  { printf '\033[36m==> %s\033[0m\n' "$*"; }
die()   { red "ERROR: $*"; exit 1; }

# ---------------------------------------------------------------- pre-flight
info "Pre-flight checks"
command -v docker >/dev/null || die "docker not found"
docker compose version >/dev/null 2>&1 || die "docker compose v2+ required"
[[ -f "$COMPOSE_FILE" ]] || die "$COMPOSE_FILE not found (run from the deploy dir)"
[[ -f "$ENV_FILE" ]]     || die "$ENV_FILE not found — create it first (see header)"

# required assets
for d in kogito-pg-init data-index-protobufs bpmn; do
  [[ -d "$d" ]] || die "missing asset dir: $d"
done
[[ -f kogito-pg-init/01-dataindex-db.sql && -f kogito-pg-init/02-arcana-db.sql ]] \
  || die "kogito-pg-init SQL missing"

# required images loaded
for img in "${IMAGES[@]}"; do
  docker image inspect "$img" >/dev/null 2>&1 || die "image not loaded: $img (docker load it first)"
done

# JWT_SECRET present + long enough
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a
[[ -n "${JWT_SECRET:-}" && ${#JWT_SECRET} -ge 32 ]] || die "JWT_SECRET must be >= 32 chars in $ENV_FILE"
DASHBOARD_PORT="${DASHBOARD_PORT:-8095}"
KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP:-kafka:9092}"

# devops_default network + kafka reachability
docker network inspect devops_default >/dev/null 2>&1 || die "devops_default network missing"
kafka_host="${KAFKA_BOOTSTRAP%%:*}"
docker run --rm --network devops_default busybox nslookup "$kafka_host" >/dev/null 2>&1 \
  || red "WARN: '$kafka_host' did not resolve on devops_default — check KAFKA_BOOTSTRAP"

# disk headroom
avail=$(df -P /data 2>/dev/null | awk 'NR==2{print $4}')
[[ -z "$avail" || "$avail" -gt 2000000 ]] || red "WARN: low disk on /data (<2GB) — consider docker image prune"

if (( WITH_WORKER )); then
  [[ -n "${AGENT_TASK_URL:-}" ]] || die "--with-worker needs AGENT_TASK_URL in $ENV_FILE"
  green "Pre-flight OK (will ALSO start task-worker → real CI triggering)"
else
  green "Pre-flight OK (monitoring stack only — no CI triggering)"
fi

# ---------------------------------------------------------------- deploy
SERVICES=("${MON_SERVICES[@]}")
(( WITH_WORKER )) && SERVICES+=(task-worker)

info "Deploying: ${SERVICES[*]}"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d "${SERVICES[@]}"

# ---------------------------------------------------------------- health
info "Waiting for health (up to ~150s)"
ready=0
for i in $(seq 1 50); do
  proxy=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${DASHBOARD_PORT}/api/v1/workflows/processes" 2>/dev/null || echo 000)
  if [[ "$proxy" == "200" ]]; then ready=1; break; fi
  sleep 3
done

echo
info "Container status"
docker compose -f "$COMPOSE_FILE" ps

echo
if (( ready )); then
  green "✓ read-API reachable via dashboard proxy (http://localhost:${DASHBOARD_PORT})"
  echo "  sample:"; curl -s "http://localhost:${DASHBOARD_PORT}/api/v1/workflows/processes" | head -c 300; echo
  echo
  green "Deploy complete. Front the dashboard (127.0.0.1:${DASHBOARD_PORT}) with Authelia for external access."
else
  red "✗ read-API not reachable yet on :${DASHBOARD_PORT}. Check logs:"
  echo "  docker logs aaf-arcana-cloud-rust --tail 40"
  echo "  docker logs aaf-data-index --tail 40"
  exit 1
fi
