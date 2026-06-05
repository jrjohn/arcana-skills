#!/bin/bash
# Node 01: infra - Exit Validation
# Validates DevOps infrastructure is running

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
INFRA_FILE="${DEVOPS_DIR}/infra.json"

echo "=== Node 01: infra Exit Validation ==="
echo ""

# Check 1: docker-compose.infra.yml exists
echo -n "Checking docker-compose.infra.yml... "
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.infra.yml"
if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "FAILED"
    echo "  Error: docker-compose.infra.yml not found"
    exit 1
fi
echo "OK"

# Check 2: Compose file is valid
echo -n "Validating compose file... "
if ! docker compose -f "${COMPOSE_FILE}" config > /dev/null 2>&1; then
    echo "FAILED"
    echo "  Error: Invalid docker-compose.infra.yml"
    exit 1
fi
echo "OK"

# Check 3: Jenkins is accessible
echo -n "Checking Jenkins (port 8080)... "
if ! curl -sf http://localhost:8080/login > /dev/null 2>&1; then
    echo "FAILED"
    echo "  Error: Jenkins not responding on port 8080"
    echo "  Fix: docker compose -f docker-compose.infra.yml up -d jenkins"
    exit 1
fi
echo "OK"

# Check 4: SonarQube is accessible
echo -n "Checking SonarQube (port 9000)... "
SONAR_STATUS=$(curl -sf http://localhost:9000/api/system/status 2>/dev/null | jq -r '.status // empty')
if [ "$SONAR_STATUS" != "UP" ]; then
    echo "FAILED"
    echo "  Error: SonarQube not ready (status: ${SONAR_STATUS:-unreachable})"
    echo "  Fix: Wait for SonarQube to finish starting up"
    exit 1
fi
echo "OK (status: UP)"

# Check 5: Registry is accessible
echo -n "Checking Docker Registry (port 5000)... "
if ! curl -sf http://localhost:5000/v2/ > /dev/null 2>&1; then
    echo "FAILED"
    echo "  Error: Docker Registry not responding on port 5000"
    exit 1
fi
echo "OK"

# Check 6: infra.json exists
echo -n "Checking infra.json... "
if [ ! -f "${INFRA_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${INFRA_FILE} not found"
    exit 1
fi
echo "OK"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Infrastructure Status:"
echo "  Jenkins:  http://localhost:8080  ✓"
echo "  SonarQube: http://localhost:9000 ✓"
echo "  Registry: http://localhost:5000  ✓"
echo ""
echo "Ready to proceed to Node 02: pipeline"
exit 0
