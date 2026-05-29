#!/bin/bash
# Node 03: build - Exit Validation
# Validates Dockerfile generation and build

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
BUILD_FILE="${DEVOPS_DIR}/build.json"

echo "=== Node 03: build Exit Validation ==="
echo ""

# Check 1: At least one Dockerfile exists
echo -n "Checking Dockerfile(s)... "
DOCKERFILE_COUNT=$(find "${PROJECT_ROOT}" -maxdepth 2 -name "Dockerfile*" -not -path "*/.devops/*" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
if [ "$DOCKERFILE_COUNT" -eq 0 ]; then
    echo "FAILED"
    echo "  Error: No Dockerfile found in project"
    exit 1
fi
echo "OK ($DOCKERFILE_COUNT found)"

# Check 2: .dockerignore exists
echo -n "Checking .dockerignore... "
if [ ! -f "${PROJECT_ROOT}/.dockerignore" ]; then
    echo "FAILED"
    echo "  Error: .dockerignore not found"
    exit 1
fi
echo "OK"

# Check 3: Dockerfile has USER directive (non-root)
echo -n "Checking non-root USER directive... "
MAIN_DOCKERFILE="${PROJECT_ROOT}/Dockerfile"
if [ -f "$MAIN_DOCKERFILE" ]; then
    if ! grep -q "^USER " "$MAIN_DOCKERFILE"; then
        echo "WARNING"
        echo "  Warning: No USER directive found — running as root (rule I1)"
    else
        echo "OK"
    fi
else
    echo "SKIP (no main Dockerfile)"
fi

# Check 4: Dockerfile has HEALTHCHECK
echo -n "Checking HEALTHCHECK directive... "
if [ -f "$MAIN_DOCKERFILE" ]; then
    if ! grep -q "HEALTHCHECK" "$MAIN_DOCKERFILE"; then
        echo "WARNING"
        echo "  Warning: No HEALTHCHECK directive — consider adding one (rule C3)"
    else
        echo "OK"
    fi
else
    echo "SKIP"
fi

# Check 5: build.json exists
echo -n "Checking build.json... "
if [ ! -f "${BUILD_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${BUILD_FILE} not found"
    exit 1
fi
echo "OK"

# Check 6: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${BUILD_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in build.json"
    exit 1
fi
echo "OK"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Build Summary:"
echo "  Dockerfiles: $DOCKERFILE_COUNT"
jq -r '.dockerfiles | to_entries[] | "  \(.key): \(.value.base) (\(.value.size_mb // "?")MB)"' "${BUILD_FILE}" 2>/dev/null || true
echo ""
echo "Ready to proceed to Node 04: test"
exit 0
