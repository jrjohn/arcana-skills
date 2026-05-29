#!/bin/bash
# Node 02: pipeline - Exit Validation
# Validates Jenkins Pipeline configuration

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
PIPELINE_FILE="${DEVOPS_DIR}/pipeline.json"

echo "=== Node 02: pipeline Exit Validation ==="
echo ""

# Check 1: Jenkinsfile exists
echo -n "Checking Jenkinsfile... "
if [ ! -f "${PROJECT_ROOT}/Jenkinsfile" ]; then
    echo "FAILED"
    echo "  Error: Jenkinsfile not found in project root"
    exit 1
fi
echo "OK"

# Check 2: Jenkinsfile has required stages
echo -n "Checking pipeline stages... "
REQUIRED_STAGES=("Checkout" "Build" "Test" "Docker Build")
for stage in "${REQUIRED_STAGES[@]}"; do
    if ! grep -q "$stage" "${PROJECT_ROOT}/Jenkinsfile"; then
        echo "FAILED"
        echo "  Error: Missing stage '$stage' in Jenkinsfile"
        exit 1
    fi
done
echo "OK (all required stages present)"

# Check 3: pipeline.json exists
echo -n "Checking pipeline.json... "
if [ ! -f "${PIPELINE_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${PIPELINE_FILE} not found"
    exit 1
fi
echo "OK"

# Check 4: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${PIPELINE_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in pipeline.json"
    exit 1
fi
echo "OK"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Pipeline Configuration:"
STAGES=$(jq -r '.pipeline_stages | join(" → ")' "${PIPELINE_FILE}" 2>/dev/null || echo "N/A")
echo "  Stages: $STAGES"
echo ""
echo "Ready to proceed to Node 03: build"
exit 0
