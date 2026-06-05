#!/bin/bash
# Node 05: deploy - Exit Validation
# Validates deployment configurations

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
DEPLOY_FILE="${DEVOPS_DIR}/deploy.json"

echo "=== Node 05: deploy Exit Validation ==="
echo ""

# Check 1: At least one compose file exists
echo -n "Checking deployment compose files... "
COMPOSE_COUNT=$(find "${PROJECT_ROOT}" -maxdepth 1 -name "docker-compose.*.yml" -not -name "docker-compose.infra.yml" | wc -l | tr -d ' ')
if [ "$COMPOSE_COUNT" -eq 0 ]; then
    echo "FAILED"
    echo "  Error: No docker-compose.*.yml deployment files found"
    exit 1
fi
echo "OK ($COMPOSE_COUNT found)"

# Check 2: Validate compose files
echo -n "Validating compose files... "
for f in "${PROJECT_ROOT}"/docker-compose.*.yml; do
    [ -f "$f" ] || continue
    if ! docker compose -f "$f" config > /dev/null 2>&1; then
        echo "FAILED"
        echo "  Error: Invalid compose file: $(basename $f)"
        exit 1
    fi
done
echo "OK"

# Check 3: K8s manifests (if k8s directory exists)
if [ -d "${PROJECT_ROOT}/k8s" ]; then
    echo -n "Checking K8s manifests... "
    K8S_COUNT=$(find "${PROJECT_ROOT}/k8s" -name "*.yml" | wc -l | tr -d ' ')
    if [ "$K8S_COUNT" -eq 0 ]; then
        echo "WARNING (k8s/ directory exists but no manifests)"
    else
        echo "OK ($K8S_COUNT manifests)"
    fi

    # Check resource limits (🔴 C5)
    echo -n "Checking K8s resource limits... "
    if [ -f "${PROJECT_ROOT}/k8s/deployment.yml" ]; then
        if ! grep -q "limits" "${PROJECT_ROOT}/k8s/deployment.yml"; then
            echo "FAILED"
            echo "  Error: K8s deployment missing resource limits (rule C5)"
            exit 1
        fi
        echo "OK"
    else
        echo "SKIP (no deployment.yml)"
    fi

    # Check no latest tag (🔴 C2)
    echo -n "Checking for 'latest' tag usage... "
    if grep -rq ":latest" "${PROJECT_ROOT}/k8s/"*.yml 2>/dev/null; then
        echo "FAILED"
        echo "  Error: 'latest' tag found in K8s manifests (rule C2)"
        exit 1
    fi
    echo "OK (no :latest found)"
fi

# Check 4: Deploy script exists (🔴 C4)
echo -n "Checking deploy.sh... "
if [ ! -f "${PROJECT_ROOT}/scripts/deploy.sh" ]; then
    echo "WARNING"
    echo "  Warning: scripts/deploy.sh not found"
else
    echo "OK"
fi

# Check 5: Rollback script exists (🔴 C4)
echo -n "Checking rollback.sh... "
if [ ! -f "${PROJECT_ROOT}/scripts/rollback.sh" ]; then
    echo "FAILED"
    echo "  Error: scripts/rollback.sh not found (rule C4: rollback strategy required)"
    exit 1
fi
echo "OK"

# Check 6: deploy.json exists
echo -n "Checking deploy.json... "
if [ ! -f "${DEPLOY_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${DEPLOY_FILE} not found"
    exit 1
fi
echo "OK"

# Check 7: Remote deploy configuration (if prod uses docker-compose-remote)
if jq -e '.environments.prod.tool == "docker-compose-remote"' "${DEPLOY_FILE}" > /dev/null 2>&1; then
    echo -n "Checking remote deploy config... "
    REMOTE_HOST=$(jq -r '.environments.prod.ssh_host // ""' "${DEPLOY_FILE}" 2>/dev/null)
    REMOTE_DIR=$(jq -r '.environments.prod.remote_dir // ""' "${DEPLOY_FILE}" 2>/dev/null)

    if [ -z "$REMOTE_HOST" ] || [[ "$REMOTE_HOST" == *"{{"* ]]; then
        echo "WARNING"
        echo "  Warning: SSH host not configured in deploy.json (placeholder detected)"
        echo "  Set SSH_HOST before running 'deploy.sh prod'"
    elif [ -z "$REMOTE_DIR" ] || [[ "$REMOTE_DIR" == *"{{"* ]]; then
        echo "WARNING"
        echo "  Warning: Remote compose dir not configured in deploy.json (placeholder detected)"
        echo "  Set REMOTE_COMPOSE_DIR before running 'deploy.sh prod'"
    else
        echo "OK (host: $REMOTE_HOST, dir: $REMOTE_DIR)"
    fi
fi

# Check 8: .env.template exists
echo -n "Checking .env.template... "
if [ -f "${PROJECT_ROOT}/.env.template" ]; then
    echo "OK"
else
    echo "WARNING"
    echo "  Warning: .env.template not found — users may not know which env vars to set"
fi

# Check 9: No :latest in compose prod file
echo -n "Checking for 'latest' tag in compose files... "
if grep -rq ":latest" "${PROJECT_ROOT}"/docker-compose.prod.yml 2>/dev/null; then
    echo "FAILED"
    echo "  Error: ':latest' tag found in docker-compose.prod.yml (rule C2)"
    exit 1
fi
echo "OK"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Deployment Summary:"
echo "  Compose files: $COMPOSE_COUNT"
jq -r '.environments | to_entries[] | "  \(.key): \(.value.tool)"' "${DEPLOY_FILE}" 2>/dev/null || true
echo ""
echo "Ready to proceed to Node 06: release"
exit 0
