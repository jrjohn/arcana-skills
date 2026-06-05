#!/bin/bash
# Node 08: verify - Exit Validation
# End-to-end verification of the entire DevOps setup

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
VERIFY_FILE="${DEVOPS_DIR}/verify.json"
SKILL_DIR="$HOME/.claude/skills/arcana-devops-skill"

echo "=== Node 08: verify Exit Validation ==="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

check_pass() {
    echo "OK"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo "FAILED"
    echo "  Error: $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_warn() {
    echo "WARNING"
    echo "  Warning: $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

# === Node Output Verification ===
echo "--- Node Output Verification ---"

for node_output in init.json infra.json pipeline.json build.json test.json deploy.json release.json monitor.json; do
    echo -n "Checking $node_output... "
    if [ -f "${DEVOPS_DIR}/${node_output}" ]; then
        if jq empty "${DEVOPS_DIR}/${node_output}" 2>/dev/null; then
            check_pass
        else
            check_fail "Invalid JSON in $node_output"
        fi
    else
        check_warn "$node_output not found"
    fi
done

echo ""

# === Configuration Verification ===
echo "--- Configuration Verification ---"

# Jenkinsfile
echo -n "Checking Jenkinsfile... "
if [ -f "${PROJECT_ROOT}/Jenkinsfile" ]; then
    check_pass
else
    check_warn "Jenkinsfile not found"
fi

# Dockerfile
echo -n "Checking Dockerfile... "
DOCKERFILE_COUNT=$(find "${PROJECT_ROOT}" -maxdepth 2 -name "Dockerfile*" -not -path "*/.devops/*" | wc -l | tr -d ' ')
if [ "$DOCKERFILE_COUNT" -gt 0 ]; then
    echo "OK ($DOCKERFILE_COUNT found)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    check_warn "No Dockerfiles found"
fi

# .dockerignore
echo -n "Checking .dockerignore... "
if [ -f "${PROJECT_ROOT}/.dockerignore" ]; then
    check_pass
else
    check_warn ".dockerignore not found"
fi

echo ""

# === Security Verification ===
echo "--- Security Verification ---"

# No :latest tag in production configs
echo -n "Checking no :latest in production... "
LATEST_FOUND=false
for f in "${PROJECT_ROOT}"/docker-compose.prod.yml "${PROJECT_ROOT}"/docker-compose.staging.yml; do
    if [ -f "$f" ] && grep -q ":latest" "$f" 2>/dev/null; then
        LATEST_FOUND=true
    fi
done
if [ -d "${PROJECT_ROOT}/k8s" ]; then
    for f in "${PROJECT_ROOT}"/k8s/*.yml; do
        if [ -f "$f" ] && grep -q ":latest" "$f" 2>/dev/null; then
            LATEST_FOUND=true
        fi
    done
fi
if [ "$LATEST_FOUND" = true ]; then
    check_fail ":latest tag found in production configs (rule C2)"
else
    check_pass
fi

# Rollback script exists
echo -n "Checking rollback strategy... "
if [ -f "${PROJECT_ROOT}/scripts/rollback.sh" ]; then
    check_pass
else
    check_warn "rollback.sh not found (rule C4)"
fi

echo ""

# === verify.json ===
echo -n "Checking verify.json... "
if [ -f "${VERIFY_FILE}" ]; then
    check_pass
else
    check_warn "verify.json not found"
fi

echo ""
echo "============================================"
echo "=== Verification Summary ==="
echo "============================================"
echo ""
echo "  Passed:   $PASS_COUNT"
echo "  Failed:   $FAIL_COUNT"
echo "  Warnings: $WARN_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "Status: FAILED ($FAIL_COUNT critical issues)"
    echo "Fix the failed checks before proceeding."
    exit 1
fi

if [ "$WARN_COUNT" -gt 0 ]; then
    echo "Status: PASSED WITH WARNINGS ($WARN_COUNT warnings)"
else
    echo "Status: ALL PASSED"
fi

echo ""
echo "🎉 DevOps setup verification complete!"
exit 0
