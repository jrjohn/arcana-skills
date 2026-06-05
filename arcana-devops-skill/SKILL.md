---
skill_name: arcana-devops-skill
skill_version: 1.1.0
created_date: 2026-02-11
skill_type: complex
protocols:
  - COR
  - AFP
  - NTP
allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
dependencies:
  - app-requirements-skill
  - springboot-developer-skill
  - nodejs-developer-skill
  - python-developer-skill
  - ios-developer-skill
  - android-developer-skill
  - react-developer-skill
  - angular-developer-skill
  - windows-developer-skill
---

# DevOps Skill

> **COR-AFP-NTP Compliant DevOps Automation Skill**
>
> Unified CI/CD infrastructure for multi-language tech stacks with Docker-first approach.

## Purpose

Guides users from zero to a complete DevOps environment covering:
- **Jenkins CI/CD** — Docker-based pipeline automation
- **Docker Build** — Multi-stage optimized builds for all supported languages
- **Multi-Environment Deploy** — Docker Compose + SSH (primary) / K8s (optional) / Cloud / On-Premise
- **App Store/Play Store** — Automated submission via Fastlane
- **SonarQube Quality Gate** — Code quality enforcement
- **IEC 62304 Compliance** — Automated documentation output
- **Monitoring** — Prometheus + Grafana + AlertManager

## Quick Start

```
User: /arcana-devops-skill
User: 幫我建立 CI/CD 環境
User: 設定 Docker 部署
User: 建立 Jenkins Pipeline
```

## Activation Keywords

- `devops`, `CI/CD`, `pipeline`, `Jenkins`, `Docker 部署`
- `K8s 部署`, `Kubernetes`, `容器化`, `容器部署`
- `自動部署`, `自動建構`, `自動送審`, `Fastlane`
- `SonarQube`, `品質門檻`, `Trivy`, `image scan`
- `Prometheus`, `Grafana`, `監控`, `可觀測性`
- `Docker Compose`, `docker-compose`, `Dockerfile`
- `/arcana-devops-skill`, `/devops`

---

## Quick Reference Card

### Common Commands

| Command | Description |
|---------|-------------|
| `docker compose -f docker-compose.infra.yml up -d` | Start DevOps infrastructure |
| `docker compose -f docker-compose.infra.yml ps` | Check infrastructure status |
| `docker build -t app:v1.0.0 .` | Build Docker image |
| `docker compose -f docker-compose.staging.yml up -d` | Deploy to staging |
| `kubectl apply -f k8s/` | Deploy to K8s |
| `fastlane ios release` | Submit to App Store |
| `fastlane android release` | Submit to Play Store |

### Port Reference

| Service | Port | URL | Host |
|---------|------|-----|------|
| Jenkins | 8080 | http://localhost:8080 | Rocky VM (local) |
| SonarQube | 9000 | http://localhost:9000 | Rocky VM (local) |
| **Docker Registry** | **443** | **https://arcana.boo** | **Bluesea (Oracle Cloud)** |
| Nexus | 8081 | http://localhost:8081 | Rocky VM (local) |
| Prometheus | 9090 | http://localhost:9090 | Rocky VM (local) |
| Grafana | 3000 | http://localhost:3000 | Rocky VM (local) |
| AlertManager | 9093 | http://localhost:9093 | Rocky VM (local) |

### Private Docker Registry (Bluesea)

- **Domain**: `arcana.boo` (DNS → `161.118.206.170`)
- **TLS**: Let's Encrypt (auto-renew via certbot), nginx reverse proxy → `registry:2` on localhost:5000
- **Container**: `registry:2` with `registry-data` volume on `/data` (99GB)
- **Namespace**: `arcana/` (e.g., `arcana/go-app`, `arcana/react-app`)
- **API**: `curl https://arcana.boo/v2/_catalog`

> HTTPS registry 不需要 `insecure-registries` 設定。Rocky 9 需設定 SELinux: `setsebool -P httpd_can_network_connect 1`

#### Oracle Cloud Networking
> Oracle Cloud 有**兩層獨立防火牆**，port 80/443 需在兩層都開放：
> 1. **Security Group** — `add_port` CLI 或 Console
> 2. **Subnet Security List** — OCI CLI 或 Console（容易遺漏）

### Jenkins Agent Infrastructure

| Agent | Host | IP | Labels | Platform | 用途 |
|-------|------|-----|--------|----------|------|
| Built-in Node | Rocky VM | localhost | `(built-in)` | Linux ARM64 | Docker pipeline (所有語言) |
| Mac Mini | Mac Mini | 192.168.11.104 | `macos`, `ios` | macOS (Apple Silicon) | iOS / macOS pipeline |
| Windows MSI | Windows 11 | 192.168.11.115 | `windows` | Windows x64 | WinUI 3 / .NET desktop pipeline |

#### Mac Mini Agent 設定

| 項目 | 值 |
|------|-----|
| Jenkins Credentials ID | `macmini-ssh` |
| SSH User | `jrjohn` |
| SSH Key | Rocky VM `~/.ssh/macmini.key` |
| Java Path | `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java` |
| Xcode | 26.2 (App Store) |
| Homebrew | `/opt/homebrew/bin` |
| Fastlane | `gem install fastlane` |
| Remote Root Dir | `/Users/jrjohn/jenkins-agent` |

> **Pipeline 選擇**：iOS/macOS pipeline 使用 `agent { label "macos" }`，其餘使用 `agent any`（Built-in Node）

### Docker Image Naming

```
{registry}/{namespace}/{service}:{version}
arcana.boo/arcana/api:1.2.3
```

---

## Rules Priority

### 🔴 Critical (MUST Follow)

| # | Rule |
|---|------|
| C1 | **No secrets in Docker images** — Use K8s Secrets / Docker Secrets / Vault |
| C2 | **No `latest` tag in production** — Use semantic versioning (x.y.z) |
| C3 | **All services must have health checks** — liveness + readiness probes |
| C4 | **Rollback strategy required before deploy** — rollback.sh must exist and be tested |
| C5 | **K8s Deployments must set resource limits** — CPU/Memory limits mandatory |
| C6 | **Docker images must pass security scan** — Trivy scan before deploy |
| C7 | **Exit validation must pass before proceeding** — NTP gate enforcement |

### 🟡 Important (SHOULD Follow)

| # | Rule |
|---|------|
| I1 | Use non-root user in containers — `USER` directive in Dockerfile |
| I2 | Enable RBAC access control — K8s ServiceAccount + RBAC |
| I3 | Multi-stage Docker builds — Minimize image size |
| I4 | Pin dependency versions — No floating versions in production |
| I5 | Use `.dockerignore` — Exclude unnecessary files from build context |

### 🟢 Recommended (NICE to Have)

| # | Rule |
|---|------|
| R1 | Regular base image updates — Track CVEs |
| R2 | Docker layer caching optimization — Order layers by change frequency |
| R3 | Structured logging (JSON) — For ELK Stack integration |
| R4 | Distributed tracing — OpenTelemetry integration |

---

## COR Process Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  00-init → 01-infra → 02-pipeline → 03-build → 04-test                  │
│                                                       ↓                  │
│            08-verify ← 07-monitor ← 06-release ← 05-deploy              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Node Summary

| Node | Purpose | Gate |
|------|---------|------|
| `00-init` | Prerequisites & project initialization | Docker daemon running, directory structure created |
| `01-infra` | DevOps toolchain via Docker Compose | All services health check passed |
| `02-pipeline` | Jenkins Pipeline setup | Jenkinsfile syntax validated |
| `03-build` | Optimized Dockerfiles per language | Docker build success, image size reasonable |
| `04-test` | Containerized testing + quality gates | Coverage ≥ 80%, SonarQube Quality Gate passed |
| `05-deploy` | Multi-environment deployment (Compose + SSH remote) | Deploy configs validated, health endpoint defined |
| `06-release` | Automated submission & compliance | Fastlane validated, compliance docs complete |
| `07-monitor` | Monitoring & observability | Prometheus scraping, Grafana dashboard loaded |
| `08-verify` | End-to-end pipeline verification | Full pipeline run success |

---

## Supported Language Matrix

| Language | Build Tool | Test Framework | Docker Base | Deploy |
|----------|-----------|----------------|-------------|--------|
| Java/Spring Boot | Gradle 9.2.1 | JUnit 5 | eclipse-temurin:25-jdk → :25-jre | JAR in container |
| Python/Flask | pip | pytest | python:3.14-slim | gunicorn |
| Node.js/Express | npm | Jest/Mocha | node:22-alpine + Prisma | node server |
| React | npm (Vite) | Jest + RTL | node:22 → nginx:1.27-alpine | nginx static |
| Angular | npm (ng CLI 20) | Karma/Jest | node:22 → nginx:1.27-alpine | nginx static |
| Vue.js | npm (Vite) | Vitest/Jest | node:22 → nginx:1.27-alpine | nginx static |
| Rust | Cargo | cargo test | rust:latest → debian:bookworm-slim | Binary in container |
| Go | go build | go test | golang:1.24-alpine → alpine:3.21 | Static binary in container |
| .NET (API) | dotnet | xUnit/NUnit | dotnet/sdk:10.0 (CI only) | ASP.NET in container |
| .NET (Desktop) | dotnet | xUnit/NUnit | Windows agent (native) | EXE + MSIX |
| Swift/iOS | Xcode 26.2 | XCTest | macOS agent (Mac Mini) | Fastlane → TestFlight |
| Android/Kotlin | Gradle (gradlew) | JUnit + Espresso | eclipse-temurin:21 + Android SDK 36 (amd64) | Fastlane → Play Console |
| HarmonyOS | hvigorw | hvigorw test | ubuntu:22.04 + JDK 17 + OHOS SDK 6.0.0.858 (amd64) | Fastlane → AppGallery |
| ESP32 (Firmware) | idf.py (CMake) | Unity/QEMU | espressif/idf:v5.5.2 (build only) | esptool.py / OTA |
| STM32 (Firmware) | CMake + Make | Unity/CTest | ubuntu:24.04 + arm-gcc (build only) | OpenOCD / J-Link / OTA |

---

## Deployment Strategy Matrix

> **重要：正式環境預設使用 Docker Compose + SSH Remote Deploy，K8s 為選用方案**

| 環境 | 工具 | 策略 | 備註 |
|------|------|------|------|
| 開發 | Docker Compose（本地） | 直接替換 | `deploy.sh dev` |
| 測試 | Docker Compose（本地/遠端） | Blue-Green | `deploy.sh staging` |
| **正式** | **Docker Compose + SSH Remote Deploy** | **版本固定 + Health Check + 自動回滾** | `deploy.sh prod` / `deploy.sh remote` |
| 正式 (K8s) | kubectl / Helm（選用） | Rolling Update / Canary | `deploy.sh k8s` |
| Cloud | Terraform + K8s | Infrastructure as Code | 依雲端平台決定 |
| On-Premise | Docker Compose / K8s | 依架構決定 | SSH remote deploy |
| iOS | Fastlane | TestFlight → App Store | Mac Mini agent, Xcode build + sign |
| 嵌入式韌體 | esptool.py / OpenOCD / OTA | Flash or OTA update | ESP32 / STM32, 無 Docker deploy |
| 桌面應用 (.NET) | MSIX 封裝 | Store / Sideload / Direct | WinUI 3 desktop, 無 Docker deploy |
| HarmonyOS | AppGallery Connect API | internal → beta → production | 類似 Play Store 流程 |

### Production Deploy Flow (Docker Compose + SSH)

```
Jenkins Build → Docker Push to arcana.boo (version-pinned, HTTPS)
  → SSH to Target VM → Save rollback state
  → Pull new image from registry → docker compose up -d
  → Health Check (60s timeout) → Pass: Done / Fail: Auto-rollback
```

See: `templates/jenkins/Jenkinsfile.cloud`, `templates/scripts/deploy.sh`

---

## AFP State Management

### Workspace Location
```
{project-root}/.devops/current-process.json
```

### State Schema
```json
{
  "session_id": "uuid",
  "current_node": "00-init",
  "project_name": "",
  "project_type": [],
  "deploy_targets": [],
  "started_at": "ISO8601",
  "updated_at": "ISO8601",
  "completed_nodes": [],
  "node_outputs": {},
  "metadata": {
    "skill_version": "1.1.0",
    "protocol": "COR-AFP-NTP"
  }
}
```

---

## NTP Gate Validation

Each node must pass exit validation before proceeding:

```bash
bash ~/.claude/skills/arcana-devops-skill/process/00-init/exit-validation.sh {project-root}
```

---

## File Index

### Core Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — COR entry point + quick reference |
| `CLAUDE.md` | Skill-specific rules for Claude |
| `README.md` | User documentation |

### Process Nodes

| Node | README | Validation |
|------|--------|------------|
| 00-init | `process/00-init/README.md` | `exit-validation.sh` |
| 01-infra | `process/01-infra/README.md` | `exit-validation.sh` |
| 02-pipeline | `process/02-pipeline/README.md` | `exit-validation.sh` |
| 03-build | `process/03-build/README.md` | `exit-validation.sh` |
| 04-test | `process/04-test/README.md` | `exit-validation.sh` |
| 05-deploy | `process/05-deploy/README.md` | `exit-validation.sh` |
| 06-release | `process/06-release/README.md` | `exit-validation.sh` |
| 07-monitor | `process/07-monitor/README.md` | `exit-validation.sh` |
| 08-verify | `process/08-verify/README.md` | `exit-validation.sh` |

### Templates

| Category | Location | Contents |
|----------|----------|----------|
| Docker | `templates/docker/` | `Dockerfile.springboot`, `Dockerfile.flask`, `Dockerfile.node`, `Dockerfile.react`, `Dockerfile.angular`, `Dockerfile.vue`, `Dockerfile.rust`, `Dockerfile.go`, `Dockerfile.dotnet`, `Dockerfile.android`, `Dockerfile.harmonyos`, `Dockerfile.esp32`, `Dockerfile.stm32`, `Dockerfile.unified`, `.dockerignore`, `.gitignore.template` |
| Compose | `templates/compose/` | `docker-compose.ci.yml` (generic), `docker-compose.ci.android.yml`, `docker-compose.ci.harmonyos.yml`, `docker-compose.ci.esp32.yml`, `docker-compose.ci.stm32.yml`, `docker-compose.dev.yml`, `docker-compose.infra.yml`, `docker-compose.prod.yml`, `docker-compose.staging.yml`, `.env.template` |
| Jenkins | `templates/jenkins/` | `Jenkinsfile.go`, `Jenkinsfile.rust`, `Jenkinsfile.node`, `Jenkinsfile.springboot`, `Jenkinsfile.dotnet`, `Jenkinsfile.android`, `Jenkinsfile.harmonyos`, `Jenkinsfile.embedded`, `Jenkinsfile.ios`, `Jenkinsfile.windows`, `Jenkinsfile.vue`, `Jenkinsfile.react`, `Jenkinsfile.python`, `Jenkinsfile.angular`, `Jenkinsfile.mobile`, `Jenkinsfile.cloud`, `Jenkinsfile.template` + JCasC + `shared-library-vars/` |
| K8s | `templates/k8s/` | Kubernetes manifests |
| Mobile | `templates/mobile/` | `Fastfile.ios`, `Fastfile.android`, `Fastfile.harmonyos`, `Appfile.template` |
| Monitoring | `templates/monitoring/` | Prometheus/Grafana configs |
| Scripts | `templates/scripts/` | `setup.sh` (one-click init), `deploy.sh`, `rollback.sh`, `health-check.sh` |

### Production-Tested Status (15/15 pipelines SUCCESS)

> All templates below are derived from production configs that ran successfully on Rocky VM (ARM64).
> See: `references/production-validation.md` for full validation records.

| Pipeline | Jenkinsfile | Dockerfile | CI Compose | Build Time | Status |
|----------|-------------|------------|------------|------------|--------|
| Go | `Jenkinsfile.go` | `Dockerfile.go` | `docker-compose.ci.yml` | ~3s (cached) | TESTED |
| Rust | `Jenkinsfile.rust` | `Dockerfile.rust` | `docker-compose.ci.yml` | ~4s (cached) | TESTED |
| Node.js | `Jenkinsfile.node` | `Dockerfile.node` | `docker-compose.ci.yml` | 97s | TESTED |
| Spring Boot | `Jenkinsfile.springboot` | `Dockerfile.springboot` | `docker-compose.ci.yml` | 245s | TESTED |
| Python/Flask | `Jenkinsfile.python` | `Dockerfile.flask` | `docker-compose.ci.yml` | 373s | TESTED |
| .NET (Linux CI) | `Jenkinsfile.dotnet` | `Dockerfile.dotnet` | `docker-compose.ci.yml` | ~2s (cached) | TESTED |
| Vue | `Jenkinsfile.vue` | `Dockerfile.vue` | `docker-compose.ci.yml` | ~2s (cached) | TESTED |
| React | `Jenkinsfile.react` | `Dockerfile.react` | `docker-compose.ci.yml` | 89s | TESTED |
| Angular | `Jenkinsfile.angular` | `Dockerfile.angular` | `docker-compose.ci.yml` | 262s | TESTED |
| Android | `Jenkinsfile.android` | `Dockerfile.android` | `docker-compose.ci.android.yml` | 94s | TESTED |
| HarmonyOS | `Jenkinsfile.harmonyos` | `Dockerfile.harmonyos` | `docker-compose.ci.harmonyos.yml` | 68s | TESTED |
| ESP32 | `Jenkinsfile.embedded` | `Dockerfile.esp32` | `docker-compose.ci.esp32.yml` | 370s | TESTED |
| STM32 | `Jenkinsfile.embedded` | `Dockerfile.stm32` | `docker-compose.ci.stm32.yml` | 471s | TESTED |
| iOS | `Jenkinsfile.ios` | — (native Xcode) | — | 159s | TESTED |
| Windows | `Jenkinsfile.windows` | — (native dotnet) | — | 46s | TESTED |

### References

| File | Topic |
|------|-------|
| `references/docker-patterns.md` | Docker best practices (incl. Rust/Go/.NET/embedded patterns) |
| `references/jenkins-patterns.md` | Jenkins Pipeline patterns |
| `references/kubernetes-patterns.md` | K8s deployment strategies |
| `references/cicd-patterns.md` | CI/CD flow patterns |
| `references/migration-patterns.md` | Freestyle → Pipeline migration & real-world CI/CD improvements |
| `references/mobile-release.md` | App Store/Play Store submission |
| `references/embedded-patterns.md` | Embedded firmware CI/CD (ESP32 + STM32 build/test/deploy/security) |
| `references/iec62304-compliance.md` | IEC 62304 compliance automation |
| `references/monitoring-patterns.md` | Monitoring & observability |
| `references/security-patterns.md` | DevOps security best practices |
| `references/production-validation.md` | 15 pipelines production validation records (date, platform, build time) |

### Checklists

| File | Purpose |
|------|---------|
| `checklists/pre-deploy.md` | Pre-deployment checklist |
| `checklists/security.md` | Security audit checklist |
| `checklists/k8s-readiness.md` | K8s readiness checklist |
| `checklists/release.md` | Release checklist |

### Frameworks

| Framework | Location |
|-----------|----------|
| COR | `frameworks/cor/README.md` |
| AFP | `frameworks/afp/README.md` |
| NTP | `frameworks/ntp/README.md` |

---

## Integration with Other Skills

| Skill | Integration Point |
|-------|-------------------|
| `app-requirements-skill` | IEC 62304 docs → compliance traceability |
| `springboot-developer-skill` | Spring Boot build templates |
| `nodejs-developer-skill` | Node.js build templates |
| `python-developer-skill` | Python/Flask build templates |
| `ios-developer-skill` | iOS Fastlane submission |
| `android-developer-skill` | Android Fastlane submission |
| `react-developer-skill` | React frontend build templates |
| `angular-developer-skill` | Angular frontend build templates |
| `windows-developer-skill` | Windows/.NET MSIX packaging |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Docker daemon not running | `sudo systemctl start docker` or open Docker Desktop |
| User not in docker group | `sudo usermod -aG docker $(whoami)` then `newgrp docker` |
| Jenkins container fails to start | Check port 8080 not in use: `lsof -i :8080` |
| Jenkins `docker: not found` | Mount Docker CLI: `-v /usr/bin/docker:/usr/bin/docker:ro` |
| Jenkins `AccessDeniedException` on docker.sock | Use `group_add` with host docker GID: `stat -c '%g' /var/run/docker.sock` |
| Jenkins `AccessDeniedException` on host path | Mount project dir into Jenkins container volume |
| Jenkins Pipeline stuck in queue | Check built-in node is NORMAL mode, not EXCLUSIVE |
| Jenkins API `403 No valid crumb` | Use cookie jar + `Jenkins-Crumb` header (see jenkins-patterns.md) |
| Jenkins Pipeline XML newlines stripped | Use `--data-binary` (not `-d`) + `CDATA` wrapper |
| Jenkins admin warnings (CSP/node) | Dismiss via Groovy console (see jenkins-patterns.md) |
| SonarQube OOM | Increase `vm.max_map_count`: `sudo sysctl -w vm.max_map_count=262144` |
| Docker build cache issues | `docker builder prune` to clean build cache |
| K8s pod CrashLoopBackOff | `kubectl logs <pod>` + `kubectl describe pod <pod>` |
| Registry push fails | 確認 `docker push arcana.boo/arcana/...` 使用 HTTPS 域名；若 TLS 錯誤檢查 certbot 憑證是否過期 |
| Registry 502 Bad Gateway | SELinux 問題：`sudo setsebool -P httpd_can_network_connect 1`；或檢查 registry container 是否在運行 |
| Registry unreachable | Oracle Cloud 需同時開放 Security Group **和** Subnet Security List 的 port 80/443 |
| Fastlane auth failure | Re-run `fastlane match` or `fastlane spaceauth` |
| Pipeline timeout | Increase Jenkins job timeout in Jenkinsfile |
| Health check failing | Verify endpoint path and container port mapping |
| Image too large | Review multi-stage build, check `.dockerignore` |
| Jenkins `docker compose: unknown flag` | Mount compose plugin: `-v /usr/libexec/docker/cli-plugins:/usr/libexec/docker/cli-plugins:ro` |
| Jenkins node offline (disk space) | `docker system prune -af`, remove unused images; min 1GB free for jenkins_home |
| ESP32 image pull slow (~11GB ARM64) | Pre-pull with `docker pull espressif/idf:v5.4.1`; use docker compose for cached builds |
| STM32 CMake compiler test fails | Add `set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)` to toolchain cmake |
| Android aapt2 `Syntax error: "(" unexpected` on ARM64 | aapt2 is x86_64 only; use `platform: linux/amd64` in docker-compose.yml + install binfmt: `docker run --rm --privileged tonistiigi/binfmt --install amd64` |
| Android aapt2 `Could not open ld-linux-x86-64.so.2` | Must use full amd64 image (not just binfmt on ARM64 image); set `platforms: [linux/amd64]` in compose build config |
| HarmonyOS `.npmrc` registry errors | Must have dual registry: `registry=https://registry.npmjs.org/` (default) + `@ohos:registry=https://repo.harmonyos.com/npm/` (scoped) |
| HarmonyOS `modelVersion` mismatch | `modelVersion: "6.0.0"` must be in BOTH `hvigor/hvigor-config.json5` AND root `oh-package.json5` |
| HarmonyOS `analyzeEnabled` invalid | Use `analyze: "normal"` (not `analyzeEnabled: true/false`) in hvigor-config.json5 `execution` section |
| HarmonyOS HAP packaging fails (no Java) | JDK 17 required for HAP packaging: `openjdk-17-jdk-headless` in Dockerfile |
| Mac Mini SSH `Too many authentication failures` | SSH agent 嘗試過多 key；使用專用 key：`ssh -i ~/.ssh/macmini.key jrjohn@192.168.11.104` |
| Mac Mini Xcode not found | 需從 App Store 安裝完整 Xcode（Command Line Tools 不夠）；安裝後執行 `sudo xcode-select -s /Applications/Xcode.app` |
| Mac Mini Jenkins agent `java not found` | 設定 Java Path: `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java` |
| iOS pipeline `swift build` fails with `no destinations` | 確認 Xcode 已安裝且 `xcode-select -p` 指向正確路徑 |
| Mac Mini Homebrew permission denied | 設定 NOPASSWD sudo：`echo 'jrjohn ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/jrjohn` |
