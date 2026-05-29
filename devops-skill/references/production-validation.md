# Production Validation Records

> 15/15 pipelines tested and passed on Rocky VM infrastructure.
> Date: 2026-02-23 ~ 2026-02-24

## Test Infrastructure

| Component | Details |
|-----------|---------|
| Jenkins Host | Rocky VM, ARM64 (aarch64), Rocky Linux 10.1 |
| Jenkins URL | `http://rockyvm.local:8080` |
| Docker Registry | `arcana.boo` (HTTPS, Let's Encrypt) / `localhost:5000` (internal) |
| Mac Mini Agent | `192.168.11.104`, Apple Silicon, macOS 15.6, Xcode 26.2 |
| Windows Agent | `192.168.11.115`, Windows 11 Pro x64, i7-1165G7, 8GB RAM, .NET 10 |

## Pipeline Validation Matrix

| # | Pipeline | Jenkins Job | Build Time | Platform | Docker Pattern | Status |
|---|----------|-------------|------------|----------|----------------|--------|
| 1 | Go | `go-app-pipeline` | ~3s (cached) | ARM64 | compose build+push | SUCCESS |
| 2 | Rust | `rust-app-pipeline` | ~4s (cached) | ARM64 | compose build+push | SUCCESS |
| 3 | Vue | `vue-app-pipeline` | ~2s (cached) | ARM64 | compose build+push | SUCCESS |
| 4 | .NET (Linux) | `dotnet-app-pipeline` | ~2s (cached) | ARM64 | compose build+push | SUCCESS |
| 5 | Spring Boot | `springboot-app-pipeline` | 245s | ARM64 | compose build+push | SUCCESS |
| 6 | Python/Flask | `python-app-pipeline` | 373s | ARM64 | compose build+push | SUCCESS |
| 7 | Node.js | `node-app-pipeline` | 97s | ARM64 | compose build+push | SUCCESS |
| 8 | React | `react-app-pipeline` | 89s | ARM64 | compose build+push | SUCCESS |
| 9 | Angular | `angular-app-pipeline` | 262s | ARM64 | compose build+push | SUCCESS |
| 10 | ESP32 | `esp32-app-pipeline` | 370s | ARM64 | docker pull + compose run | SUCCESS |
| 11 | STM32 | `stm32-app-pipeline` | 471s | ARM64 | compose build | SUCCESS |
| 12 | Android | `android-app-pipeline` | 94s | ARM64 (QEMU amd64) | compose build+run | SUCCESS |
| 13 | HarmonyOS | `harmonyos-app-pipeline` | 68s | ARM64 (QEMU amd64) | compose build+run | SUCCESS |
| 14 | iOS | `ios-app` | 159s | Mac Mini (Apple Silicon) | native xcodebuild | SUCCESS |
| 15 | Windows | `windows-app-pipeline` | 46s | Windows x64 | native dotnet | SUCCESS |

## Key Observations

### Build Patterns

1. **Web/Cloud Apps (9 pipelines)**: All use identical `docker compose -f docker-compose.ci.yml build` + tag + push pattern
2. **Embedded (2 pipelines)**: ESP32 uses pre-pulled image + compose run; STM32 uses compose build
3. **Mobile (2 pipelines)**: Android/HarmonyOS require `platform: linux/amd64` for QEMU emulation on ARM64
4. **Native Agent (2 pipelines)**: iOS uses Mac Mini agent with `xcodebuild`; Windows uses Windows agent with `dotnet`/`bat`

### Version Highlights

| Component | Version |
|-----------|---------|
| Go | 1.24 |
| Rust | latest (nightly-compatible) |
| Node.js | 22 (alpine) |
| Java/Spring Boot | JDK 25, Gradle 9.2.1 |
| Python | 3.14 |
| .NET | SDK 10.0 |
| Angular CLI | 20 |
| React (Vite) | 19 |
| Vue (Vite) | 3 |
| Android SDK | API 36, AGP 8.13.1 |
| HarmonyOS SDK | 6.0.0.858 |
| ESP-IDF | v5.5.2 |
| Xcode | 26.2 |
| nginx | 1.27-alpine |

### ARM64 Specific Notes

- ESP32 IDF image is ~11GB on ARM64 (QEMU layer overhead) — always pre-pull
- Android and HarmonyOS build-tools are x86_64 only — require `platform: linux/amd64` + binfmt
- All other Docker builds run natively on ARM64 without emulation
- Build times shown are second-run (cached) where applicable

### Windows Agent Notes

- Uses `bat` commands (not `sh`) — all stages wrapped in `dir("${PROJECT_DIR}")`
- `-maxcpucount:1` required for stable builds on 8GB RAM
- Dual output: EXE (self-contained win-x64) + MSIX (unsigned, for Store sideload)
- 507 unit tests passed (`dotnet test -c Release -p:Platform=x64`)
- WinUI 3 projects excluded from Linux CI build (removed from .sln)

### Mac Mini Agent Notes

- Jenkins SSH agent with dedicated key (`macmini-ssh` credentials)
- Java path: `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java`
- PATH must include `/opt/homebrew/bin` for Homebrew tools
- `CODE_SIGNING_ALLOWED=NO` for CI builds (no provisioning profile)
- Simulator target: `platform=iOS Simulator,name=iPhone 16`
