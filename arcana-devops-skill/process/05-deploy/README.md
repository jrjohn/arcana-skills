# Node 05: deploy（多環境部署）

> **COR Node**: Multi-environment deployment configuration

## Purpose

Generate deployment configurations for multiple environments: Docker Compose (dev/staging), Docker Compose + SSH Remote Deploy (production), Kubernetes (optional), Cloud, and On-Premise.

## Entry Conditions

- Node 04 (test) completed
- Docker images built and tested
- init.json available with deploy targets

## Deployment Strategy Matrix

> **重要：正式環境預設使用 Docker Compose + SSH Remote Deploy，K8s 為選用方案**

| Environment | Tool | Strategy | Rollback |
|-------------|------|----------|----------|
| Development | Docker Compose（本地） | Direct replace | Previous image tag |
| Staging | Docker Compose（本地/遠端） | Blue-Green | Switch back to green/blue |
| **Production** | **Docker Compose + SSH Remote** | **版本固定 + Health Check + 自動回滾** | `rollback.sh remote` |
| Production (K8s) | kubectl / Helm（選用） | Rolling Update / Canary | `kubectl rollout undo` |
| Cloud | Terraform + K8s | Infrastructure as Code | Terraform state rollback |
| On-Premise | Docker Compose + SSH | Same as Production | `rollback.sh remote` |

## Actions

1. **Generate Docker Compose files**
   - `docker-compose.dev.yml` — Development environment
   - `docker-compose.staging.yml` — Staging with blue-green support
   - `docker-compose.prod.yml` — Production (used locally and on remote host)
   - `.env.template` — Required environment variables reference

2. **Configure Remote Deploy** (production default)
   - SSH credentials in Jenkins or `.env`
   - Remote compose directory on target VM
   - Health check URL and timeout
   - Auto-rollback on health check failure

3. **Generate K8s manifests** (if K8s in deploy targets, optional)
   - `k8s/namespace.yml`
   - `k8s/deployment.yml`
   - `k8s/service.yml`
   - `k8s/ingress.yml`
   - `k8s/hpa.yml` — Horizontal Pod Autoscaler
   - `k8s/configmap.yml`
   - `k8s/secret.yml` — Template only (🔴 C1)
   - `k8s/pdb.yml` — PodDisruptionBudget

4. **Generate deployment scripts**
   - `scripts/deploy.sh` — Supports: dev, staging, prod/remote, k8s
   - `scripts/rollback.sh` — Supports: dev, staging, prod/remote, k8s
   - `scripts/health-check.sh`

5. **Validate configurations**
   ```bash
   docker compose -f docker-compose.dev.yml config
   kubectl apply --dry-run=client -f k8s/  # if K8s selected
   ```

## K8s Resource Requirements (🔴 C5)

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 100m–500m | 500m–2000m |
| Memory | 128Mi–512Mi | 512Mi–2Gi |

## Embedded Firmware Deployment

Embedded firmware (ESP32/STM32) uses a fundamentally different deployment model:

| Method | Platform | Tool | Use Case |
|--------|----------|------|----------|
| USB/Serial flash | ESP32 | `esptool.py` | Development, initial flash |
| OTA (HTTP/HTTPS) | ESP32 | ESP-IDF OTA component | Field updates |
| ST-Link / J-Link | STM32 | `st-flash` / `JLinkExe` | Development |
| OpenOCD | STM32 | `openocd` | Flexible (multiple probes) |
| OTA (custom) | Both | Application-specific | Wireless field updates |

**No Docker Compose or K8s** — firmware runs on bare metal.

See: `references/embedded-patterns.md` for detailed deployment patterns.

## Desktop Application Deployment (Windows/.NET)

| Distribution | Method | Tool |
|-------------|--------|------|
| Microsoft Store | MSIX package upload | Partner Center |
| Enterprise Sideload | MSIX + certificate | Group Policy / SCCM |
| Direct download | MSIX / MSI installer | Website distribution |

**No Docker deploy** — desktop apps are packaged as MSIX.

## HarmonyOS Deployment

| Track | Method | Tool |
|-------|--------|------|
| Internal testing | HAP upload | AppGallery Connect API |
| Beta | Promote from internal | AppGallery Connect API |
| Production | Promote from beta + review | AppGallery Connect API |

Similar to Play Store workflow. Uses `hvigorw` for build and Fastlane for submission.

See: `templates/mobile/Fastfile.harmonyos`, `templates/jenkins/Jenkinsfile.harmonyos`

---

## Health Check Endpoints (🔴 C3)

Every service MUST expose:
- `GET /health` or `GET /actuator/health` — Liveness probe
- `GET /ready` or `GET /actuator/health/readiness` — Readiness probe

## Output

Create `{project-root}/.devops/deploy.json`:

```json
{
  "environments": {
    "dev": { "tool": "docker-compose", "file": "docker-compose.dev.yml" },
    "staging": { "tool": "docker-compose", "file": "docker-compose.staging.yml" },
    "prod": { "tool": "docker-compose-remote", "file": "docker-compose.prod.yml",
              "ssh_host": "{{SSH_HOST}}", "remote_dir": "{{REMOTE_COMPOSE_DIR}}" },
    "k8s": { "tool": "k8s", "manifests": "k8s/", "optional": true }
  },
  "scripts": ["deploy.sh", "rollback.sh", "health-check.sh"],
  "configured_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/05-deploy/exit-validation.sh {project-root}`

### Success Criteria

- [ ] At least one docker-compose.*.yml exists
- [ ] Remote deploy config valid (if prod uses remote): SSH_HOST, REMOTE_COMPOSE_DIR set
- [ ] K8s manifests exist (if K8s selected)
- [ ] K8s deployments have resource limits (🔴 C5)
- [ ] Health check endpoints defined (🔴 C3)
- [ ] deploy.sh and rollback.sh exist (🔴 C4)
- [ ] No secrets in plain text (🔴 C1)
- [ ] No `latest` tag usage (🔴 C2)
- [ ] `.env.template` exists with all required variables documented

## Next Node

On success → `06-release`

## Error Handling

| Error | Action |
|-------|--------|
| kubectl not available | Skip K8s validation, warn user |
| Invalid manifest | Show validation errors, auto-fix if possible |
| Missing health endpoint | Generate health endpoint scaffold |
