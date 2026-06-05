#!/bin/bash
# ============================================
# Health Check Script
# DevOps Skill Template
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT="${1:-staging}"
MAX_WAIT="${2:-60}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
APP_PORT="${APP_PORT:-8080}"

echo "Health check: $ENVIRONMENT (timeout: ${MAX_WAIT}s)"

case $ENVIRONMENT in
    dev|development)
        HOST="localhost"
        ;;
    staging)
        HOST="localhost"
        ;;
    prod|production|remote)
        HOST="localhost"
        ;;
    k8s|kubernetes)
        HOST="${K8S_SERVICE_HOST:-localhost}"
        ;;
    *)
        HOST="localhost"
        ;;
esac

URL="http://${HOST}:${APP_PORT}${HEALTH_ENDPOINT}"
WAITED=0

echo -n "Checking $URL"
while [ $WAITED -lt $MAX_WAIT ]; do
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e " ${GREEN}healthy${NC} (${WAITED}s)"
        exit 0
    fi
    echo -n "."
    sleep 5
    WAITED=$((WAITED + 5))
done

echo -e " ${RED}unhealthy${NC} (timeout after ${MAX_WAIT}s)"
echo "Last HTTP status: $HTTP_CODE"
exit 1
