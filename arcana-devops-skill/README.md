# DevOps Skill

A comprehensive DevOps automation skill for Claude Code, providing unified CI/CD infrastructure for multi-language tech stacks. Ships **15 language pipeline templates** (all production-tested).

> **Reference deployment (2026-05-29):** the live reference (bluesea / arcana.boo) now runs these as **multibranch pipelines** (`*-app-pipeline-mb` — auto-discovers `main` + open PR branches, gates each on tests / SonarQube quality gate / Architecture Qube). The 15 legacy single-branch jobs were retired, and the cross-platform `.NET` pipeline (`dotnet-app-pipeline`) was consolidated into the native Windows pipeline — so the live controller runs **14 multibranch jobs** from the 15 templates. Job configs + a full plugin freeze are version-controlled in `arcana-devops` (`jobs/*.xml`, `jenkins/plugins-installed.txt`) as the disaster-recovery backup.

## Features

- **15 Language Pipelines**: Go, Rust, Node.js, Spring Boot, Python/Flask, .NET, Vue, React, Angular, Android, HarmonyOS, ESP32, STM32, iOS, Windows
- **Jenkins CI/CD**: Docker-based pipeline automation with JCasC
- **Docker Build**: Multi-stage optimized builds for all supported languages
- **Private Registry**: HTTPS registry (`arcana.boo`) with Let's Encrypt TLS
- **Multi-Agent**: Rocky VM (Linux ARM64) + Mac Mini (macOS) + Windows 11 (x64)
- **Multi-Environment Deploy**: Docker Compose + SSH Remote / Kubernetes / Cloud
- **Quality Gates**: SonarQube code quality + Trivy security scanning
- **Mobile Release**: Fastlane integration for App Store, Play Store, AppGallery
- **Monitoring**: Prometheus + Grafana + AlertManager

## Quick Start

```
User: /arcana-devops-skill
User: 幫我建立 CI/CD 環境
User: 設定 Docker 部署
User: 建立 Jenkins Pipeline
```

## Infrastructure

| Component | Details |
|-----------|---------|
| **Jenkins** | `http://rockyvm.local:8080` — Rocky VM (ARM64, Rocky Linux 10.1) |
| **SonarQube** | `http://rockyvm.local:9000` |
| **Docker Registry** | `https://arcana.boo` — Bluesea (Oracle Cloud, 24GB RAM, 99GB /data) |
| **Mac Mini Agent** | `192.168.11.104` — Apple Silicon, macOS 15.6, Xcode 26.2 |
| **Windows Agent** | `192.168.11.115` — Windows 11 Pro x64, .NET 10 |

## Production-Tested Pipelines (15/15 SUCCESS)

| # | Pipeline | Build Time | Platform | Pattern |
|---|----------|------------|----------|---------|
| 1 | Go | ~3s (cached) | ARM64 | Docker compose build+push |
| 2 | Rust | ~4s (cached) | ARM64 | Docker compose build+push |
| 3 | Vue | ~2s (cached) | ARM64 | Docker compose build+push |
| 4 | .NET | ~2s (cached) | ARM64 | Docker compose build+push |
| 5 | Spring Boot | 245s | ARM64 | Docker compose build+push |
| 6 | Python/Flask | 373s | ARM64 | Docker compose build+push |
| 7 | Node.js | 97s | ARM64 | Docker compose build+push |
| 8 | React | 89s | ARM64 | Docker compose build+push |
| 9 | Angular | 262s | ARM64 | Docker compose build+push |
| 10 | ESP32 | 370s | ARM64 | docker pull + compose run |
| 11 | STM32 | 471s | ARM64 | docker compose build |
| 12 | Android | 94s | ARM64 (QEMU amd64) | docker compose build+run |
| 13 | HarmonyOS | 68s | ARM64 (QEMU amd64) | docker compose build+run |
| 14 | iOS | 159s | Mac Mini (Apple Silicon) | native xcodebuild |
| 15 | Windows | 46s | Windows x64 | native dotnet |

## Supported Languages & Versions

| Language | Version | Build Tool | Docker Base |
|----------|---------|-----------|-------------|
| Go | 1.24 | go build | golang:1.24-alpine → alpine:3.21 |
| Rust | latest | Cargo | rust:latest → debian:bookworm-slim |
| Node.js | 22 | npm | node:22-alpine + Prisma |
| Spring Boot | JDK 25 | Gradle 9.2.1 | eclipse-temurin:25-jdk → :25-jre |
| Python/Flask | 3.14 | pip | python:3.14-slim + gunicorn |
| .NET | SDK 10.0 | dotnet | dotnet/sdk:10.0 |
| Vue | 3 (Vite) | npm | node:22 → nginx:1.27-alpine |
| React | 19 (Vite) | npm | node:22 → nginx:1.27-alpine |
| Angular | CLI 20 | npm | node:22 → nginx:1.27-alpine |
| Android | SDK 36 | Gradle (gradlew) | eclipse-temurin:21 + Android SDK 36 |
| HarmonyOS | SDK 6.0.0.858 | hvigorw | ubuntu:22.04 + JDK 17 + OHOS SDK |
| ESP32 | IDF v5.5.2 | idf.py (CMake) | espressif/idf:v5.5.2 |
| STM32 | arm-gcc | CMake + Make | ubuntu:24.04 + arm-none-eabi-gcc |
| iOS | Xcode 26.2 | xcodebuild | macOS native (Mac Mini agent) |
| Windows/.NET | .NET 10 | dotnet | Windows native (Windows agent) |

## Process Flow

```
00-init → 01-infra → 02-pipeline → 03-build → 04-test
                                                  ↓
           08-verify ← 07-monitor ← 06-release ← 05-deploy
```

1. **init** — Prerequisites & project initialization
2. **infra** — DevOps infrastructure (Jenkins, SonarQube, Registry)
3. **pipeline** — Jenkins Pipeline configuration
4. **build** — Optimized Dockerfile generation
5. **test** — Testing & quality gate setup
6. **deploy** — Multi-environment deployment
7. **release** — Automated submission & compliance
8. **monitor** — Monitoring & observability
9. **verify** — End-to-end verification

## File Structure

```
~/.claude/skills/arcana-devops-skill/
├── SKILL.md                    # Main entry point
├── CLAUDE.md                   # Skill rules
├── README.md                   # This file
├── process/                    # 9 COR process nodes (00-init ~ 08-verify)
├── templates/
│   ├── jenkins/                # 17 Jenkinsfiles (15 tested + template + cloud)
│   ├── docker/                 # 14 Dockerfiles (multi-stage, production-tested)
│   ├── compose/                # 5 CI compose files + deploy compose
│   ├── k8s/                    # Kubernetes manifests
│   ├── monitoring/             # Prometheus + Grafana configs
│   └── scripts/                # deploy.sh, rollback.sh
├── references/                 # 11 best practices docs
│   └── production-validation.md  # 15 pipelines validation records
├── checklists/                 # Pre-deploy, security, K8s, release
├── frameworks/                 # COR/AFP/NTP docs
└── workspace-template/         # AFP state template
```

## Template Index

### Jenkins Pipelines (`templates/jenkins/`)

| File | Pipeline | Agent |
|------|----------|-------|
| `Jenkinsfile.go` | Go compose build+push | `agent any` |
| `Jenkinsfile.rust` | Rust compose build+push | `agent any` |
| `Jenkinsfile.node` | Node.js compose build+push | `agent any` |
| `Jenkinsfile.springboot` | Spring Boot compose build+push | `agent any` |
| `Jenkinsfile.python` | Python/Flask compose build+push | `agent any` |
| `Jenkinsfile.dotnet` | .NET compose build+push | `agent any` |
| `Jenkinsfile.vue` | Vue compose build+push | `agent any` |
| `Jenkinsfile.react` | React compose build+push | `agent any` |
| `Jenkinsfile.angular` | Angular compose build+push | `agent any` |
| `Jenkinsfile.android` | Android QEMU build | `agent any` |
| `Jenkinsfile.harmonyos` | HarmonyOS QEMU build | `agent any` |
| `Jenkinsfile.embedded` | ESP32 / STM32 firmware | `agent any` |
| `Jenkinsfile.ios` | iOS xcodebuild + test | `agent { label 'macos' }` |
| `Jenkinsfile.windows` | Windows .NET build+test | `agent { label 'windows' }` |
| `Jenkinsfile.template` | Generic base template | `agent any` |
| `Jenkinsfile.cloud` | Remote deploy + rollback | `agent any` |
| `Jenkinsfile.mobile` | Fastlane generic | `agent any` |

### Dockerfiles (`templates/docker/`)

| File | Base Image | Output |
|------|-----------|--------|
| `Dockerfile.go` | golang:1.24-alpine → alpine:3.21 | Static binary |
| `Dockerfile.rust` | rust:latest → debian:bookworm-slim | Binary |
| `Dockerfile.node` | node:22-alpine | Node server |
| `Dockerfile.springboot` | eclipse-temurin:25-jdk → :25-jre | JAR |
| `Dockerfile.flask` | python:3.14-slim | gunicorn |
| `Dockerfile.vue` | node:22 → nginx:1.27-alpine | nginx static |
| `Dockerfile.react` | node:22 → nginx:1.27-alpine | nginx static |
| `Dockerfile.angular` | node:22 → nginx:1.27-alpine | nginx static |
| `Dockerfile.dotnet` | dotnet/sdk:10.0 | CI build |
| `Dockerfile.android` | eclipse-temurin:21 + SDK 36 | APK |
| `Dockerfile.harmonyos` | ubuntu:22.04 + OHOS SDK | HAP |
| `Dockerfile.esp32` | espressif/idf:v5.5.2 | .bin/.elf |
| `Dockerfile.stm32` | ubuntu:24.04 + arm-gcc | .bin/.hex/.elf |
| `Dockerfile.nginx` | nginx:1.27-alpine | Reverse proxy |

### CI Compose (`templates/compose/`)

| File | Pattern |
|------|---------|
| `docker-compose.ci.yml` | Generic build+push (web/cloud apps) |
| `docker-compose.ci.android.yml` | `platform: linux/amd64` (QEMU) |
| `docker-compose.ci.harmonyos.yml` | `platform: linux/amd64` (QEMU) |
| `docker-compose.ci.esp32.yml` | Pre-pulled IDF image + volume |
| `docker-compose.ci.stm32.yml` | Standard Dockerfile.ci build |

## Dependencies

This skill integrates with:

| Skill | Purpose |
|-------|---------|
| `app-requirements-skill` | IEC 62304 compliance |
| `arcana-springboot-developer-skill` | Spring Boot projects |
| `arcana-nodejs-developer-skill` | Node.js projects |
| `arcana-python-developer-skill` | Python projects |
| `arcana-ios-developer-skill` | iOS projects |
| `arcana-android-developer-skill` | Android projects |
| `arcana-react-developer-skill` | React projects |
| `arcana-angular-developer-skill` | Angular projects |
| `arcana-windows-developer-skill` | Windows desktop projects |
