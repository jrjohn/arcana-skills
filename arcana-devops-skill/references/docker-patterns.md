# Docker Best Practices

> DevOps Skill Reference

## Multi-Stage Build Pattern

### Why Multi-Stage

- Smaller final images (no build tools in production)
- Separate build and runtime dependencies
- Better layer caching

### Pattern

```dockerfile
# Stage 1: Build
FROM <build-base> AS builder
COPY . .
RUN <build-command>

# Stage 2: Runtime
FROM <runtime-base>
COPY --from=builder <artifacts> .
CMD [<run-command>]
```

## Layer Caching Strategy

Order Dockerfile instructions from **least changed** to **most changed**:

```
1. Base image           (rarely changes)
2. System packages      (rarely changes)
3. Dependency files     (changes with new deps)
4. Install dependencies (cached if files unchanged)
5. Source code          (changes frequently)
6. Build command        (runs when source changes)
```

## Image Size Optimization

| Technique | Impact |
|-----------|--------|
| Multi-stage build | High |
| Alpine/slim base images | High |
| .dockerignore | Medium |
| Minimize layers (combine RUN) | Medium |
| Remove package cache | Low |
| Use `--no-install-recommends` | Low |

## Security Best Practices

| Rule | Priority | Example |
|------|----------|---------|
| Non-root user | 🟡 | `USER appuser` |
| No secrets in image | 🔴 | Use build args or secrets mount |
| Pin base image versions | 🟡 | `node:22.1.0-alpine` not `node:latest` |
| Scan for vulnerabilities | 🔴 | `trivy image myapp:1.0.0` |
| Read-only filesystem | 🟢 | `--read-only` flag |
| No unnecessary packages | 🟢 | Minimal base images |

## Health Check Patterns

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# TCP health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD nc -z localhost 8080 || exit 1

# Script health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD /app/healthcheck.sh || exit 1
```

## Rust Dependency Cache Trick

Pre-build dependencies with a dummy `main.rs` to maximize layer caching:

```dockerfile
# Copy only dependency manifests
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies (cached unless Cargo.toml changes)
RUN cargo build --release
RUN rm -rf src

# Now copy real source — only the final binary rebuild runs
COPY src ./src
RUN touch src/main.rs && cargo build --release
```

This avoids re-downloading and re-compiling all dependencies when only source code changes.

## Go Static Binary Build

Build a fully static binary with no CGO for minimal containers:

```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server
```

- `CGO_ENABLED=0` — Pure Go, no C dependencies
- `-ldflags="-w -s"` — Strip debug info for smaller binary
- Works with both Alpine and distroless runtime images

## .NET Multi-Stage Pattern

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS builder
WORKDIR /app
COPY *.csproj ./
RUN dotnet restore          # Cache NuGet packages
COPY . .
RUN dotnet publish -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine
COPY --from=builder /app/publish .
ENTRYPOINT ["dotnet", "MyApp.dll"]
```

For desktop apps (WinUI 3 / MSIX), use build-only:
```bash
docker build --target msix-output -o ./artifacts .
```

## Embedded Build Environment Pattern

Embedded Dockerfiles are **build-only** — they produce firmware artifacts, not deployable containers.

### ESP32 (ESP-IDF)

```dockerfile
FROM espressif/idf:v5.5.2 AS builder
WORKDIR /app
COPY . .
RUN . /opt/esp/idf/export.sh && idf.py set-target esp32 && idf.py build

# Extract artifacts
FROM builder AS artifacts
RUN mkdir -p /artifacts && cp build/*.bin /artifacts/
```

### STM32 (ARM GCC)

```dockerfile
FROM ubuntu:24.04 AS builder
RUN apt-get update && apt-get install -y cmake make gcc-arm-none-eabi
WORKDIR /app
COPY . .
RUN mkdir build && cd build && cmake .. && make -j$(nproc)

# Extract artifacts
FROM builder AS artifacts
RUN mkdir -p /artifacts && cp build/*.bin build/*.hex /artifacts/
```

Extract with:
```bash
docker build --target artifacts -o ./firmware-output .
```

See: `references/embedded-patterns.md` for full CI/CD patterns.

---

## .dockerignore Best Practices

Always exclude:
- `.git/` — Version control history
- `node_modules/` — Will be rebuilt in container
- `target/` — Build artifacts
- `*.md` — Documentation
- `docker-compose*.yml` — Compose files
- `.env*` — Environment files (secrets!)
- `test/`, `tests/` — Test files (unless needed)

## Consolidating Multiple Dockerfiles into One

### Problem: Dockerfile Proliferation

Many projects end up with separate Dockerfiles per environment or region:

```
cloud/
├── Dockerfile          # Production
├── Dockerfile_Dev      # Development/QA
└── Dockerfile_China    # Regional variant
```

This causes drift between environments, duplicated maintenance, and inconsistent builds.

### Solution: Single Parameterized Dockerfile

Use `ARG` to make one Dockerfile cover all environments:

```dockerfile
ARG BUILD_ENV=production
ARG NODE_MEM=6144
ARG NODE_VERSION=22
ARG APP_PORT=3000

# Stage 1: Build (parameterized)
FROM node:${NODE_VERSION}-alpine AS builder
ARG BUILD_ENV
ARG NODE_MEM
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN node --max_old_space_size=${NODE_MEM} \
    ./node_modules/@angular/cli/bin/ng build --configuration ${BUILD_ENV}

# Stage 2: Runtime (shared)
FROM node:${NODE_VERSION}-alpine
# ... same runtime for all environments
```

### Usage

```bash
# Development
docker build --build-arg BUILD_ENV=qa -t app:dev .

# Production
docker build --build-arg BUILD_ENV=production -t app:1.2.3 .

# Regional variant
docker build --build-arg BUILD_ENV=china -t app:1.2.3-cn .
```

### Benefits

| Aspect | Multiple Dockerfiles | Single Parameterized |
|--------|---------------------|---------------------|
| Maintenance | N files to update | 1 file |
| Drift risk | High | None |
| Build consistency | Variable | Guaranteed |
| CI/CD complexity | Per-env logic | Single `--build-arg` |

See template: `templates/docker/Dockerfile.unified`

---

## Docker Compose Patterns

### Service Dependencies

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy  # Wait for health check
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```
