#!/bin/bash
# Node 04: test - Exit Validation
# Validates testing configuration and quality gates

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
TEST_FILE="${DEVOPS_DIR}/test.json"

echo "=== Node 04: test Exit Validation ==="
echo ""

# Check 1: sonar-project.properties exists
echo -n "Checking sonar-project.properties... "
if [ ! -f "${PROJECT_ROOT}/sonar-project.properties" ]; then
    echo "WARNING"
    echo "  Warning: sonar-project.properties not found (SonarQube may use defaults)"
else
    echo "OK"
fi

# Check 2: test.json exists
echo -n "Checking test.json... "
if [ ! -f "${TEST_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${TEST_FILE} not found"
    exit 1
fi
echo "OK"

# Check 3: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${TEST_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in test.json"
    exit 1
fi
echo "OK"

# Check 4: Coverage threshold
echo -n "Checking coverage threshold... "
COVERAGE=$(jq -r '.coverage_threshold // 0' "${TEST_FILE}")
if [ "$COVERAGE" -lt 80 ]; then
    echo "WARNING"
    echo "  Warning: Coverage threshold is $COVERAGE% (recommended: ≥ 80%)"
else
    echo "OK ($COVERAGE%)"
fi

# Check 5: SonarQube is configured
echo -n "Checking SonarQube configuration... "
SONAR_KEY=$(jq -r '.sonarqube.project_key // empty' "${TEST_FILE}")
if [ -z "$SONAR_KEY" ]; then
    echo "WARNING"
    echo "  Warning: SonarQube project key not configured"
else
    echo "OK (project: $SONAR_KEY)"
fi

echo ""
echo "=== All validations passed ==="
echo ""
echo "Test Configuration:"
echo "  Coverage Threshold: $COVERAGE%"
echo "  SonarQube Project: ${SONAR_KEY:-not configured}"
jq -r '.test_frameworks | to_entries[] | "  \(.key): \(.value)"' "${TEST_FILE}" 2>/dev/null || true
echo ""
echo "Ready to proceed to Node 05: deploy"
exit 0
