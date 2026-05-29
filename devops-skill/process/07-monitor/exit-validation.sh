#!/bin/bash
# Node 07: monitor - Exit Validation
# Validates monitoring configuration

set -e

PROJECT_ROOT="${1:-.}"
DEVOPS_DIR="${PROJECT_ROOT}/.devops"
MONITOR_FILE="${DEVOPS_DIR}/monitor.json"

echo "=== Node 07: monitor Exit Validation ==="
echo ""

# Check 1: prometheus.yml exists
echo -n "Checking prometheus.yml... "
PROM_FILE=$(find "${PROJECT_ROOT}" -maxdepth 2 -name "prometheus.yml" -not -path "*/node_modules/*" | head -1)
if [ -z "$PROM_FILE" ]; then
    echo "FAILED"
    echo "  Error: prometheus.yml not found"
    exit 1
fi
echo "OK ($PROM_FILE)"

# Check 2: grafana-dashboard.json exists
echo -n "Checking grafana-dashboard.json... "
GRAFANA_FILE=$(find "${PROJECT_ROOT}" -maxdepth 2 -name "grafana-dashboard.json" -not -path "*/node_modules/*" | head -1)
if [ -z "$GRAFANA_FILE" ]; then
    echo "WARNING"
    echo "  Warning: grafana-dashboard.json not found"
else
    echo "OK"
fi

# Check 3: alertmanager.yml exists
echo -n "Checking alertmanager.yml... "
ALERT_FILE=$(find "${PROJECT_ROOT}" -maxdepth 2 -name "alertmanager.yml" -not -path "*/node_modules/*" | head -1)
if [ -z "$ALERT_FILE" ]; then
    echo "WARNING"
    echo "  Warning: alertmanager.yml not found"
else
    echo "OK"
fi

# Check 4: monitor.json exists
echo -n "Checking monitor.json... "
if [ ! -f "${MONITOR_FILE}" ]; then
    echo "FAILED"
    echo "  Error: ${MONITOR_FILE} not found"
    exit 1
fi
echo "OK"

# Check 5: Valid JSON
echo -n "Checking valid JSON... "
if ! jq empty "${MONITOR_FILE}" 2>/dev/null; then
    echo "FAILED"
    echo "  Error: Invalid JSON in monitor.json"
    exit 1
fi
echo "OK"

echo ""
echo "=== All validations passed ==="
echo ""
echo "Monitoring Configuration:"
jq -r '.prometheus.url // "not set"' "${MONITOR_FILE}" 2>/dev/null | xargs -I{} echo "  Prometheus: {}"
jq -r '.grafana.url // "not set"' "${MONITOR_FILE}" 2>/dev/null | xargs -I{} echo "  Grafana: {}"
jq -r '.alertmanager.url // "not set"' "${MONITOR_FILE}" 2>/dev/null | xargs -I{} echo "  AlertManager: {}"
echo ""
echo "Ready to proceed to Node 08: verify"
exit 0
