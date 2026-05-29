#!/bin/bash
# ============================================
# DevOps Environment Setup Script
# One-click initialization
# ============================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================"
echo "  DevOps Environment Setup"
echo "============================================"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

# Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi
log_info "Docker: $(docker --version)"

# Docker Compose
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose V2 is not available."
    exit 1
fi
log_info "Docker Compose: $(docker compose version --short)"

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi
log_info "Docker daemon: running"

# kubectl (optional)
if command -v kubectl &> /dev/null; then
    log_info "kubectl: $(kubectl version --client --short 2>/dev/null || echo 'available')"
else
    log_warn "kubectl not found (optional, needed for K8s deployment)"
fi

echo ""

# Create directory structure
log_info "Creating directory structure..."
mkdir -p .devops
mkdir -p scripts
mkdir -p k8s

# Set vm.max_map_count for SonarQube (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURRENT_MAP_COUNT=$(sysctl -n vm.max_map_count 2>/dev/null || echo "0")
    if [ "$CURRENT_MAP_COUNT" -lt 262144 ]; then
        log_warn "SonarQube requires vm.max_map_count >= 262144 (current: $CURRENT_MAP_COUNT)"
        if command -v sudo &> /dev/null; then
            log_info "Setting vm.max_map_count=262144..."
            sudo sysctl -w vm.max_map_count=262144
            # Persist across reboots
            echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.d/99-sonarqube.conf > /dev/null
        else
            log_error "Run: sudo sysctl -w vm.max_map_count=262144"
        fi
    fi
fi

# Ensure current user is in docker group
if ! groups | grep -q docker 2>/dev/null; then
    log_warn "Current user is not in docker group"
    if command -v sudo &> /dev/null; then
        log_info "Adding user to docker group..."
        sudo usermod -aG docker "$(whoami)"
        log_warn "You may need to log out and back in, or run: newgrp docker"
    fi
fi

# Start infrastructure
log_info "Starting DevOps infrastructure..."
docker compose -f docker-compose.infra.yml up -d

# Wait for services
log_info "Waiting for services to start..."

wait_for_service() {
    local name=$1
    local url=$2
    local max_wait=${3:-120}
    local waited=0

    echo -n "  Waiting for $name"
    while [ $waited -lt $max_wait ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC} (${waited}s)"
            return 0
        fi
        echo -n "."
        sleep 5
        waited=$((waited + 5))
    done
    echo -e " ${RED}timeout${NC}"
    return 1
}

wait_for_service "Jenkins" "http://localhost:8080/login" 120
wait_for_service "SonarQube" "http://localhost:9000/api/system/status" 180
wait_for_service "Registry" "http://localhost:5000/v2/" 30

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Services:"
echo "    Jenkins:   http://localhost:8080"
echo "    SonarQube: http://localhost:9000"
echo "    Registry:  http://localhost:5000"
echo ""
echo "  Jenkins initial admin password:"
echo "    docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
echo ""
echo "  SonarQube default credentials:"
echo "    Username: admin"
echo "    Password: admin"
echo ""

# Post-setup: dismiss Jenkins admin monitors & configure docker access
log_info "Configuring Jenkins post-startup settings..."
JENKINS_URL="http://localhost:8080"
JENKINS_USER="${JENKINS_ADMIN_USER:-admin}"
JENKINS_PASS="${JENKINS_ADMIN_PASS:-}"

dismiss_jenkins_monitors() {
    if [ -z "$JENKINS_PASS" ]; then
        # Try initial admin password
        JENKINS_PASS=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "")
    fi
    if [ -z "$JENKINS_PASS" ]; then
        log_warn "Cannot auto-configure Jenkins (no password). Configure manually after first login."
        return
    fi

    local CREDS="${JENKINS_USER}:${JENKINS_PASS}"

    # Get CSRF crumb (required for Jenkins API calls)
    local COOKIE_JAR=$(mktemp)
    local CRUMB_JSON=$(curl -s -c "$COOKIE_JAR" -u "$CREDS" "${JENKINS_URL}/crumbIssuer/api/json" 2>/dev/null)
    local CRUMB=$(echo "$CRUMB_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])" 2>/dev/null || echo "")

    if [ -z "$CRUMB" ]; then
        log_warn "Cannot get Jenkins CSRF crumb. Configure manually."
        rm -f "$COOKIE_JAR"
        return
    fi

    # Dismiss admin monitors via Groovy Script Console
    curl -s -b "$COOKIE_JAR" -X POST "${JENKINS_URL}/manage/script" \
        -u "$CREDS" -H "Jenkins-Crumb:${CRUMB}" \
        --data-urlencode 'script=
import jenkins.model.Jenkins
def monitors = Jenkins.instance.getExtensionList(hudson.model.AdministrativeMonitor.class)
def targets = ["ControllerExecutorsNoAgents","ControllerExecutorsAgents","CspRecommendation","ResourceDomainRecommendation"]
monitors.each { m -> targets.each { t -> if (m.getClass().getName().contains(t)) m.disable(true) } }
println "OK"
' > /dev/null 2>&1

    rm -f "$COOKIE_JAR"
    log_info "Jenkins admin monitors configured"
}

# Wait a bit for Jenkins to be fully ready, then configure
(sleep 10 && dismiss_jenkins_monitors) &
