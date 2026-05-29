# Node 03: build（Docker 建構）

> **COR Node**: Optimized Dockerfile generation per language

## Purpose

Generate multi-stage, optimized Dockerfiles for each language/framework in the project.

## Entry Conditions

- Node 02 (pipeline) completed
- init.json available with project types

## Dockerfile Strategy

| Language | Template | Base Image | Build Strategy |
|----------|----------|-----------|----------------|
| Java/Spring Boot | `Dockerfile.springboot` | eclipse-temurin:21-jdk → eclipse-temurin:21-jre | Maven multi-stage, layer caching, distroless option |
| Python/Flask | `Dockerfile.flask` | python:3.13-slim | pip install + gunicorn, virtual env |
| Node.js/Express | `Dockerfile.node` | node:22-alpine | npm ci + multi-stage, prune dev deps |
| React | `Dockerfile.react` | node:22-alpine → nginx:alpine | npm build + nginx serve static |
| Angular | `Dockerfile.angular` | node:22-alpine → nginx:alpine | ng build + nginx serve static |
| Vue.js | `Dockerfile.vue` | node:22-alpine → nginx:1.27-alpine | Vite build + nginx serve static |
| Rust | `Dockerfile.rust` | rust:1.83-slim → debian:bookworm-slim | Cargo dependency cache trick + release build |
| Go | `Dockerfile.go` | golang:1.23-alpine → alpine:3.20 | CGO_ENABLED=0 static build, distroless alternative |
| .NET (API) | `Dockerfile.dotnet` | dotnet/sdk:9.0 → dotnet/aspnet:9.0-alpine | dotnet restore cache + publish |
| ESP32 | `Dockerfile.esp32` | espressif/idf:v5.5.2 | **Build env only** — idf.py build → extract .bin |
| STM32 | `Dockerfile.stm32` | ubuntu:24.04 + arm-none-eabi-gcc | **Build env only** — cmake + make → extract .bin/.hex |
| Multi-env (unified) | `Dockerfile.unified` | Parameterized via `ARG` | Single Dockerfile for all environments |

## Actions

1. **Read init.json** for project types
2. **Generate Dockerfile(s)** from templates
   - Apply multi-stage build pattern
   - Set non-root user (Important rule I1)
   - Configure health check
   - Optimize layer ordering for caching
3. **Generate .dockerignore** from template
4. **Test Docker build**
   ```bash
   docker build -t {project-name}:{version} .
   ```
5. **Check image size** — warn if exceeding thresholds

### Image Size Thresholds

| Language | Warning | Critical |
|----------|---------|----------|
| Java/Spring Boot | > 300MB | > 500MB |
| Python/Flask | > 200MB | > 400MB |
| Node.js/Express | > 150MB | > 300MB |
| React (nginx) | > 50MB | > 100MB |
| Angular (nginx) | > 50MB | > 100MB |
| Vue.js (nginx) | > 50MB | > 100MB |
| Rust | > 100MB | > 200MB |
| Go | > 30MB | > 80MB |
| .NET (API) | > 200MB | > 400MB |
| ESP32 (firmware .bin) | > 1MB | > 3MB |
| STM32 (firmware .bin) | > 512KB | > 1MB |

### Embedded Build Environment

For ESP32 and STM32 projects, Docker is used as a **build environment only**, not a deployment container:

1. **Build firmware** inside Docker container using platform-specific toolchain
2. **Extract artifacts** (`.bin`, `.hex`, `.elf`) from container to host
3. **No Docker push** — firmware is archived in Jenkins or deployed via OTA

```bash
# Extract firmware from Docker build
docker build --target artifacts -o ./firmware-output -f Dockerfile.esp32 .
```

See: `references/embedded-patterns.md` for detailed CI/CD patterns.

### .NET CI Build

For .NET API projects, standard Docker multi-stage build applies. For desktop apps (WinUI 3):

1. **Build in Docker** using dotnet/sdk:9.0
2. **Package as MSIX** — `dotnet publish -p:AppxPackageDir=./msix/`
3. **No Docker push** — MSIX is archived and distributed via Store or sideload

## Output

Create `{project-root}/.devops/build.json`:

```json
{
  "dockerfiles": {
    "api": { "path": "Dockerfile", "base": "eclipse-temurin:21", "size_mb": 245 }
  },
  "dockerignore": ".dockerignore",
  "built_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/devops-skill/process/03-build/exit-validation.sh {project-root}`

### Success Criteria

- [ ] Dockerfile(s) exist for each project type
- [ ] .dockerignore exists
- [ ] Docker build succeeds (dry-run or actual)
- [ ] Image size within thresholds
- [ ] Non-root USER directive present
- [ ] HEALTHCHECK directive present

## Next Node

On success → `04-test`

## Error Handling

| Error | Action |
|-------|--------|
| Build failure | Check Dockerfile syntax, review build output |
| Image too large | Review .dockerignore, optimize layers |
| Missing base image | docker pull base image first |
