#!/bin/bash
# Node 00: init - Exit Validation
# Validates prerequisites and initialization

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
INIT_FILE="${DEVOPS_DIR}/init.json"

echo "=== Node 00: init Exit Validation ==="
echo ""

# Check 1: Docker is running
echo -n "Checking Docker daemon... "
if ! docker info > /dev/null 2>&1; then
    echo "FAILED"
    echo "  Error: Docker daemon is not running"
    echo "  Fix: Start Docker Desktop or run 'sudo systemctl start docker'"
    exit 1
fi
echo "OK"

# Check 2: docker compose available
echo -n "Checking docker compose... "
if ! docker compose version > /dev/null 2>&1; then
    echo "FAILED"
    echo "  Error: docker compose is not available"
    echo "  Fix: Install Docker Compose V2"
    exit 1
fi
echo "OK"

# Check 3: .devops directory exists
echo -n "Checking .devops directory... "
if [ ! -d "${DEVOPS_DIR}" ]; then
    echo "FAILED"
    echo "  Error: ${DEVOPS_DIR} not found"
    exit 1
fi
echo "OK"

# Check 4: init.json exists
echo -n "Checking init.json... "
if [ ! -f "${INIT_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${INIT_FILE} not found"
    exit 1
fi
echo "OK"

# Check 5: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${INIT_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in init.json"
    exit 1
fi
echo "OK"

# Check 6: project_name not empty
echo -n "Checking project_name... "
PROJECT_NAME=$(jq -r '.project_name // empty' "${INIT_FILE}")
if [ -z "$PROJECT_NAME" ]; then
    echo "FAILED"
    echo "  Error: project_name is required"
    exit 1
fi
echo "OK ($PROJECT_NAME)"

# Check 7: project_types not empty
echo -n "Checking project_types... "
TYPE_COUNT=$(jq '.project_types | length' "${INIT_FILE}")
if [ "$TYPE_COUNT" -eq 0 ]; then
    echo "FAILED"
    echo "  Error: At least one project type must be selected"
    exit 1
fi
echo "OK ($TYPE_COUNT types)"

# Check 8: deploy_targets not empty
echo -n "Checking deploy_targets... "
TARGET_COUNT=$(jq '.deploy_targets | length' "${INIT_FILE}")
if [ "$TARGET_COUNT" -eq 0 ]; then
    echo "FAILED"
    echo "  Error: At least one deploy target must be selected"
    exit 1
fi
echo "OK ($TARGET_COUNT targets)"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Summary:"
echo "  Project: $PROJECT_NAME"
echo "  Types: $TYPE_COUNT language(s)/framework(s)"
echo "  Targets: $TARGET_COUNT deploy target(s)"
echo ""
echo "Ready to proceed to Node 01: infra"
exit 0
