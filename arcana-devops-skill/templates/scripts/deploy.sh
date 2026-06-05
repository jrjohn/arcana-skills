#!/bin/bash
# ============================================
# Deployment Script
# DevOps Skill Template
# ============================================
# Supports: dev, staging, prod, remote, k8s
#
# Production default: Docker Compose + SSH Remote Deploy
# K8s: Optional for teams with Kubernetes infrastructure
# ============================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Arguments
ENVIRONMENT="${1:-staging}"
VERSION="${VERSION:-latest}"
PROJECT_NAME="${PROJECT_NAME:-{{PROJECT_NAME}}}"
REGISTRY="${REGISTRY:-localhost:5000}"

# Remote deploy settings (used by prod and remote modes)
SSH_USER="${SSH_USER:-{{SSH_USER}}}"
SSH_HOST="${SSH_HOST:-{{SSH_HOST}}}"
REMOTE_COMPOSE_DIR="${REMOTE_COMPOSE_DIR:-{{REMOTE_COMPOSE_DIR}}}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"

echo "============================================"
echo "  Deploy: $PROJECT_NAME:$VERSION → $ENVIRONMENT"
echo "============================================"
echo ""

# Block :latest in production
if [[ "$ENVIRONMENT" =~ ^(prod|production|remote)$ ]] && [ "$VERSION" = "latest" ]; then
    log_error "🔴 Deploying :latest to production is FORBIDDEN."
    log_error "   Set VERSION to a specific version (e.g. VERSION=42 or VERSION=1.2.3)"
    exit 1
fi

# Validate environment
DEPLOY_K8S=false
DEPLOY_REMOTE=false
case $ENVIRONMENT in
    dev|development)
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    prod|production|remote)
        # Production: remote SSH deploy with Docker Compose
        DEPLOY_REMOTE=true
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    k8s|kubernetes)
        DEPLOY_K8S=true
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [dev|staging|prod|k8s]"
        echo ""
        echo "  dev      Local Docker Compose (direct replace)"
        echo "  staging  Local/Remote Docker Compose (blue-green)"
        echo "  prod     Remote SSH + Docker Compose (version-pinned + health check + auto-rollback)"
        echo "  k8s      Kubernetes deployment (kubectl apply)"
        exit 1
        ;;
esac

# Pre-deploy checks
log_info "Running pre-deploy checks..."

# Check image exists (local modes only)
if [ "$DEPLOY_K8S" != "true" ] && [ "$DEPLOY_REMOTE" != "true" ]; then
    log_info "Checking image: ${REGISTRY}/${PROJECT_NAME}:${VERSION}"
    if ! docker pull "${REGISTRY}/${PROJECT_NAME}:${VERSION}" 2>/dev/null; then
        log_warn "Could not pull image, it may exist locally"
    fi
fi

# Check rollback script exists
if [ ! -f "scripts/rollback.sh" ]; then
    log_error "rollback.sh not found! Rollback strategy required before deploy."
    exit 1
fi

# ============================================
# Deploy: Remote SSH + Docker Compose
# ============================================
if [ "$DEPLOY_REMOTE" = "true" ]; then
    log_info "Deploying to remote: ${SSH_USER}@${SSH_HOST}:${REMOTE_COMPOSE_DIR}"

    # Validate remote settings
    if [[ "$SSH_HOST" == *"{{"* ]] || [ -z "$SSH_HOST" ]; then
        log_error "SSH_HOST not configured. Set SSH_HOST environment variable."
        exit 1
    fi

    # Push image to registry first
    log_info "Pushing image to registry: ${REGISTRY}/${PROJECT_NAME}:${VERSION}"
    docker tag "${PROJECT_NAME}:${VERSION}" "${REGISTRY}/${PROJECT_NAME}:${VERSION}" 2>/dev/null || true
    docker push "${REGISTRY}/${PROJECT_NAME}:${VERSION}"

    # Deploy to remote via SSH
    log_info "Deploying via SSH..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" bash -s <<REMOTE_DEPLOY
        set -euo pipefail
        cd ${REMOTE_COMPOSE_DIR}

        echo "[REMOTE] Saving rollback state..."
        sudo docker compose ps --format json > .rollback-state.json 2>/dev/null || true
        CURRENT_TAG=\$(grep -oP 'IMAGE_TAG=\K[^ ]+' .env 2>/dev/null || echo "unknown")
        echo "\$CURRENT_TAG" > .rollback-tag
        echo "[REMOTE] Current version: \$CURRENT_TAG"

        echo "[REMOTE] Updating to version: ${VERSION}"
        sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${VERSION}/" .env

        echo "[REMOTE] Pulling new image..."
        sudo docker compose pull

        echo "[REMOTE] Starting services..."
        sudo docker compose up -d --remove-orphans

        # Health check
        echo "[REMOTE] Running health check (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
        HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:\${APP_PORT:-3000}/health}"
        ATTEMPTS=\$(( ${HEALTH_CHECK_TIMEOUT} / 5 ))
        for i in \$(seq 1 \$ATTEMPTS); do
            if curl -sf "\$HEALTH_URL" > /dev/null 2>&1; then
                echo "[REMOTE] Health check PASSED"
                exit 0
            fi
            echo "[REMOTE] Waiting for health check... (\$i/\$ATTEMPTS)"
            sleep 5
        done

        # Rollback on health check failure
        echo "[REMOTE] Health check FAILED — rolling back to \$CURRENT_TAG"
        sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=\$CURRENT_TAG/" .env
        sudo docker compose pull
        sudo docker compose up -d --remove-orphans
        echo "[REMOTE] Rolled back to version: \$CURRENT_TAG"
        exit 1
REMOTE_DEPLOY

    DEPLOY_STATUS=$?
    if [ $DEPLOY_STATUS -ne 0 ]; then
        log_error "Remote deploy FAILED (auto-rollback executed)"
        exit 1
    fi
    log_info "Remote deploy successful: $PROJECT_NAME:$VERSION → $SSH_HOST"

# ============================================
# Deploy: Kubernetes
# ============================================
elif [ "$DEPLOY_K8S" = "true" ]; then
    log_info "Deploying to Kubernetes..."
    kubectl apply -f k8s/namespace.yml
    kubectl apply -f k8s/configmap.yml
    kubectl apply -f k8s/secret.yml
    kubectl apply -f k8s/deployment.yml
    kubectl apply -f k8s/service.yml
    kubectl apply -f k8s/ingress.yml
    kubectl apply -f k8s/hpa.yml
    kubectl apply -f k8s/pdb.yml

    log_info "Waiting for rollout..."
    kubectl rollout status deployment/${PROJECT_NAME} -n ${NAMESPACE:-{{NAMESPACE}}} --timeout=300s

# ============================================
# Deploy: Local Docker Compose (dev/staging)
# ============================================
else
    log_info "Deploying with Docker Compose ($COMPOSE_FILE)..."

    # Save current state for rollback
    docker compose -f "$COMPOSE_FILE" ps --format json > .devops/pre-deploy-state.json 2>/dev/null || true

    # Save current IMAGE_TAG for rollback
    PREV_TAG="${IMAGE_TAG:-unknown}"
    echo "$PREV_TAG" > .devops/.rollback-tag
    log_info "Saved rollback tag: $PREV_TAG"

    # Deploy
    IMAGE_TAG="$VERSION" docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

    log_info "Waiting for services..."
    sleep 10
fi

# Health check (local modes — remote mode handles its own health check)
if [ "$DEPLOY_REMOTE" != "true" ]; then
    log_info "Running health check..."
    bash scripts/health-check.sh "$ENVIRONMENT" "$HEALTH_CHECK_TIMEOUT"
fi

echo ""
log_info "Deployment complete: $PROJECT_NAME:$VERSION → $ENVIRONMENT"
