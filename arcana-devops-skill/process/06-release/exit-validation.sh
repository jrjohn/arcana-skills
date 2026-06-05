#!/bin/bash
# Node 06: release - Exit Validation
# Validates release and compliance configuration

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
RELEASE_FILE="${DEVOPS_DIR}/release.json"
INIT_FILE="${DEVOPS_DIR}/init.json"

echo "=== Node 06: release Exit Validation ==="
echo ""

# Check 1: release.json exists
echo -n "Checking release.json... "
if [ ! -f "${RELEASE_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${RELEASE_FILE} not found"
    exit 1
fi
echo "OK"

# Check 2: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${RELEASE_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in release.json"
    exit 1
fi
echo "OK"

# Check 3: Fastlane config (if mobile project)
if [ -f "${INIT_FILE}" ]; then
    HAS_IOS=$(jq -r '.project_types | index("ios") // empty' "${INIT_FILE}" 2>/dev/null)
    HAS_ANDROID=$(jq -r '.project_types | index("android") // empty' "${INIT_FILE}" 2>/dev/null)

    if [ -n "$HAS_IOS" ] || [ -n "$HAS_ANDROID" ]; then
        echo -n "Checking Fastlane configuration... "
        if [ ! -d "${PROJECT_ROOT}/fastlane" ]; then
            echo "WARNING"
            echo "  Warning: fastlane/ directory not found for mobile project"
        else
            echo "OK"
        fi
    fi
fi

# Check 4: Quality gates defined
echo -n "Checking quality gate criteria... "
QG_SONAR=$(jq -r '.quality_gates.sonarqube // false' "${RELEASE_FILE}")
QG_TRIVY=$(jq -r '.quality_gates.trivy // false' "${RELEASE_FILE}")
if [ "$QG_SONAR" != "true" ] && [ "$QG_TRIVY" != "true" ]; then
    echo "WARNING"
    echo "  Warning: No quality gates enabled"
else
    echo "OK (sonarqube: $QG_SONAR, trivy: $QG_TRIVY)"
fi

# Check 5: Versioning configured
echo -n "Checking version management... "
VERSIONING=$(jq -r '.versioning // empty' "${RELEASE_FILE}")
if [ -z "$VERSIONING" ]; then
    echo "WARNING"
    echo "  Warning: Version management not configured"
else
    echo "OK ($VERSIONING)"
fi

echo ""
echo "=== All validations passed ==="
echo ""
echo "Release Configuration:"
echo "  Versioning: ${VERSIONING:-not set}"
echo "  Quality Gates: SonarQube=$QG_SONAR, Trivy=$QG_TRIVY"
jq -r 'if .compliance.iec62304 then "  IEC 62304: Enabled" else "  IEC 62304: Disabled" end' "${RELEASE_FILE}" 2>/dev/null || true
echo ""
echo "Ready to proceed to Node 07: monitor"
exit 0
