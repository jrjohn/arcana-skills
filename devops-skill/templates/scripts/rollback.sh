#!/bin/bash
# ============================================
# Rollback Script
# DevOps Skill Template
# ============================================
# Supports: dev, staging, prod/remote, k8s
#
# Production default: SSH remote rollback using .rollback-tag
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

ENVIRONMENT="${1:-staging}"
PROJECT_NAME="${PROJECT_NAME:-{{PROJECT_NAME}}}"

# Remote rollback settings (used by prod and remote modes)
SSH_USER="${SSH_USER:-{{SSH_USER}}}"
SSH_HOST="${SSH_HOST:-{{SSH_HOST}}}"
REMOTE_COMPOSE_DIR="${REMOTE_COMPOSE_DIR:-{{REMOTE_COMPOSE_DIR}}}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"

echo "============================================"
echo "  Rollback: $PROJECT_NAME ($ENVIRONMENT)"
echo "============================================"
echo ""

ROLLBACK_REMOTE=false
case $ENVIRONMENT in
    dev|development)
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    prod|production|remote)
        ROLLBACK_REMOTE=true
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    k8s|kubernetes)
        log_info "Rolling back Kubernetes deployment..."
        kubectl rollout undo deployment/${PROJECT_NAME} -n ${NAMESPACE:-{{NAMESPACE}}}
        kubectl rollout status deployment/${PROJECT_NAME} -n ${NAMESPACE:-{{NAMESPACE}}} --timeout=300s
        log_info "Kubernetes rollback complete"
        exit 0
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [dev|staging|prod|remote|k8s]"
        exit 1
        ;;
esac

# ============================================
# Rollback: Remote SSH + Docker Compose
# ============================================
if [ "$ROLLBACK_REMOTE" = "true" ]; then
    log_info "Rolling back remote: ${SSH_USER}@${SSH_HOST}:${REMOTE_COMPOSE_DIR}"

    if [[ "$SSH_HOST" == *"{{"* ]] || [ -z "$SSH_HOST" ]; then
        log_error "SSH_HOST not configured. Set SSH_HOST environment variable."
        exit 1
    fi

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s <<REMOTE_ROLLBACK
        set -euo pipefail
        cd ${REMOTE_COMPOSE_DIR}

        # Read previous version from rollback tag
        PREV_TAG=\$(cat .rollback-tag 2>/dev/null || echo "")
        if [ -z "\$PREV_TAG" ] || [ "\$PREV_TAG" = "unknown" ]; then
            echo "[REMOTE] ERROR: No rollback version found (.rollback-tag missing or empty)"
            echo "[REMOTE] Manual intervention required."
            exit 1
        fi

        CURRENT_TAG=\$(grep -oP 'IMAGE_TAG=\K[^ ]+' .env 2>/dev/null || echo "unknown")
        echo "[REMOTE] Rolling back: \$CURRENT_TAG → \$PREV_TAG"

        # Restore previous version
        sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=\$PREV_TAG/" .env
        sudo docker compose pull
        sudo docker compose up -d --remove-orphans

        # Health check after rollback
        echo "[REMOTE] Running health check (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
        HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:\${APP_PORT:-3000}/health}"
        ATTEMPTS=\$(( ${HEALTH_CHECK_TIMEOUT} / 5 ))
        for i in \$(seq 1 \$ATTEMPTS); do
            if curl -sf "\$HEALTH_URL" > /dev/null 2>&1; then
                echo "[REMOTE] Health check PASSED — rolled back to \$PREV_TAG"
                exit 0
            fi
            echo "[REMOTE] Waiting for health check... (\$i/\$ATTEMPTS)"
            sleep 5
        done

        echo "[REMOTE] Health check FAILED after rollback — manual intervention required"
        exit 1
REMOTE_ROLLBACK

    ROLLBACK_STATUS=$?
    if [ $ROLLBACK_STATUS -ne 0 ]; then
        log_error "Remote rollback FAILED"
        exit 1
    fi
    log_info "Remote rollback successful"

# ============================================
# Rollback: Local Docker Compose (dev/staging)
# ============================================
else
    log_info "Rolling back Docker Compose deployment ($COMPOSE_FILE)..."

    # Read previous version from rollback tag
    PREV_TAG=""
    if [ -f ".devops/.rollback-tag" ]; then
        PREV_TAG=$(cat .devops/.rollback-tag)
    fi

    if [ -n "$PREV_TAG" ] && [ "$PREV_TAG" != "unknown" ]; then
        log_info "Restoring previous version: $PREV_TAG"
        docker compose -f "$COMPOSE_FILE" down
        IMAGE_TAG="$PREV_TAG" docker compose -f "$COMPOSE_FILE" up -d
        log_info "Rollback complete (restored version: $PREV_TAG)"
    elif [ -f ".devops/pre-deploy-state.json" ]; then
        log_warn "No rollback tag found. Restarting from pre-deploy state..."
        docker compose -f "$COMPOSE_FILE" down
        docker compose -f "$COMPOSE_FILE" up -d
        log_info "Rollback complete (restarted current config)"
    else
        log_error "No rollback data found (.devops/.rollback-tag or .devops/pre-deploy-state.json)"
        log_error "Manual intervention required."
        exit 1
    fi

    # Health check after rollback
    log_info "Running health check after rollback..."
    bash scripts/health-check.sh "$ENVIRONMENT" "$HEALTH_CHECK_TIMEOUT"
fi

echo ""
log_info "Rollback complete for $PROJECT_NAME ($ENVIRONMENT)"
