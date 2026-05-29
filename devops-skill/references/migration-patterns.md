# CI/CD Migration Patterns

> DevOps Skill Reference — Real-World Patterns & Improvements

## Overview

This document captures proven patterns from production CI/CD environments and provides
improvement strategies. All examples are sanitized and use generic placeholders.

---

## Existing Pattern: Freestyle Multi-Repo Build

### Architecture Found

```
[Jenkins Freestyle Job]
  ├── Multi-SCM Checkout
  │   ├── cloud-config.git     → cloud/       (Dockerfiles, compose)
  │   ├── web-backend.git      → backend/     (API server)
  │   ├── web-frontend.git     → frontend/    (Angular SPA)
  │   └── shared-config.git    → shared/      (Optional shared config)
  │
  ├── Angular Build (local)
  │   └── ng build --configuration {env}
  │
  ├── Docker Build
  │   ├── cp cloud/Dockerfile_{env} → Dockerfile
  │   └── docker build -t {name}:${BUILD_NUMBER}
  │
  ├── Tag & Push
  │   ├── docker tag → {registry}:{BUILD_NUMBER}
  │   └── docker tag → {registry}:latest
  │
  └── SSH Deploy (production only)
      └── ssh → compose down → pull latest → compose up -d
```

### Good Patterns (Keep)

| Pattern | Why It's Good |
|---------|---------------|
| `BUILD_NUMBER` as Docker tag | Unique, sequential, Jenkins-traceable |
| Workspace cleanup before build | Prevents stale artifacts |
| Multi-SCM checkout into subdirs | Logical separation of repos |
| Environment-specific Angular configs | QA/Prod/Regional build variants |
| Manual trigger for production | Prevents accidental prod deploys |
| SCM polling for dev env | Auto-deploy on commit for fast feedback |
| Private registry per deploy target | Environment isolation |
| docker-compose for orchestration | Simple, declarative service management |

### Problems to Fix

| Problem | Severity | Solution |
|---------|----------|----------|
| All Freestyle Jobs | 🟡 | Migrate to Declarative Pipeline (Jenkinsfile) |
| Multiple Dockerfiles per env | 🟡 | Single unified Dockerfile with build args |
| `:latest` tag in production | 🔴 | Deploy with `${BUILD_NUMBER}` or SemVer |
| No test stage | 🔴 | Add unit + integration tests |
| No quality gate | 🟡 | Add SonarQube analysis |
| No security scan | 🔴 | Add Trivy image scan |
| No health check after deploy | 🔴 | Add post-deploy health verification |
| No rollback strategy | 🔴 | Add rollback script + state tracking |
| SCM polling every minute | 🟡 | Switch to Webhook triggers |
| Hardcoded IPs in scripts | 🟡 | Use Jenkins Credentials + env vars |
| HTTP registries (no TLS) | 🟡 | Enable HTTPS or use insecure-registries config |
| No notification | 🟢 | Add Slack/Email on build/deploy events |

---

## Improvement: Unified Dockerfile

### Problem: Multiple Dockerfiles

```
cloud/
├── Dockerfile          # Production
├── Dockerfile_Dev      # Development/QA
└── Dockerfile_China    # Regional variant
```

### Solution: Single Parameterized Dockerfile

```dockerfile
ARG BUILD_ENV=production
ARG NODE_MEM=6144

# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder
ARG BUILD_ENV
ARG NODE_MEM
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN node --max_old_space_size=${NODE_MEM} \
    ./node_modules/@angular/cli/bin/ng build --configuration ${BUILD_ENV}

# Stage 2: Build backend
FROM node:22-alpine AS backend-builder
WORKDIR /app
COPY backend/package*.json ./
RUN npm ci --omit=dev
COPY backend/ .

# Stage 3: Runtime
FROM node:22-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=backend-builder /app ./
COPY --from=frontend-builder /app/dist ./public
USER appuser
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:${APP_PORT:-3000}/health || exit 1
EXPOSE ${APP_PORT:-3000}
CMD ["node", "server.js"]
```

**Usage:**
```bash
# Development (QA)
docker build --build-arg BUILD_ENV=qa --build-arg NODE_MEM=5120 -t app:dev .

# Production
docker build --build-arg BUILD_ENV=production --build-arg NODE_MEM=6144 -t app:1.2.3 .

# Regional
docker build --build-arg BUILD_ENV=china --build-arg NODE_MEM=6144 -t app:1.2.3-cn .
```

---

## Improvement: Freestyle → Declarative Pipeline

### Before (Freestyle Shell Script)

```bash
# No version control, no stages, no error handling
cd web
node --max_old_space_size=6144 ./node_modules/@angular/cli/bin/ng build --prod
cd ..
cp ./cloud/Dockerfile .
docker build -t app:${BUILD_NUMBER} .
docker tag app:${BUILD_NUMBER} registry:8080/app:latest
docker push registry:8080/app:latest
```

### After (Declarative Pipeline)

See template: `templates/jenkins/Jenkinsfile.cloud`

Key improvements:
- Version-controlled in Git
- Defined stages with clear boundaries
- Error handling and post-actions
- Credentials managed by Jenkins
- Environment-specific behavior via parameters
- Health check after deploy
- Rollback on failure

---

## Improvement: Version-Pinned Deployment

### Before (`:latest` pattern)

```bash
# On Jenkins
docker push registry/app:latest

# On target VM (SSH)
docker pull 127.0.0.1:8080/app:latest
docker-compose up -d
```

**Problems:**
- Can't tell which version is running
- Can't rollback to a specific version
- Race condition if two deploys happen simultaneously

### After (Version-pinned pattern)

```bash
# On Jenkins
docker push registry/app:${BUILD_NUMBER}

# On target VM (SSH)
export IMAGE_TAG=${BUILD_NUMBER}
docker pull 127.0.0.1:8080/app:${IMAGE_TAG}
IMAGE_TAG=${IMAGE_TAG} docker-compose up -d
```

**docker-compose.yml:**
```yaml
services:
  app:
    image: 127.0.0.1:8080/app:${IMAGE_TAG:?IMAGE_TAG is required}
    # ...
```

---

## Improvement: SSH Deploy with Health Check

### Before

```bash
ssh user@target "
  cd docker/app
  sudo docker-compose down
  sudo docker pull 127.0.0.1:8080/app:latest
  sudo docker-compose up -d
"
# No verification — hope for the best
```

### After

```bash
ssh user@target "
  cd docker/app
  # Save current state for rollback
  sudo docker-compose ps --format json > .rollback-state.json
  PREV_IMAGE=\$(sudo docker inspect --format='{{.Config.Image}}' app-container)
  echo \$PREV_IMAGE > .rollback-image

  # Deploy new version
  export IMAGE_TAG=${BUILD_NUMBER}
  sudo docker pull 127.0.0.1:8080/app:\${IMAGE_TAG}
  sudo docker-compose up -d

  # Health check (max 60s)
  for i in \$(seq 1 12); do
    if curl -sf http://localhost:\${APP_PORT}/health > /dev/null 2>&1; then
      echo 'Health check PASSED'
      exit 0
    fi
    echo 'Waiting for health check...'
    sleep 5
  done

  # Rollback on health check failure
  echo 'Health check FAILED — rolling back'
  export IMAGE_TAG=\$(cat .rollback-image | awk -F: '{print \$2}')
  sudo docker-compose up -d
  exit 1
"
```

---

## Improvement: Multi-Region Deploy

### Pattern

```
Jenkins Build
  ├── Angular Build (per region config)
  ├── Docker Build + Tag with BUILD_NUMBER
  │
  ├── Push to Region A Registry
  │   └── SSH Deploy to Region A VM
  │
  ├── Push to Region B Registry
  │   └── SSH Deploy to Region B VM
  │
  └── Push to Region C Registry
      └── SSH Deploy to Region C VM
```

### Implementation

Use Jenkins Credentials for each region:
```groovy
REGIONS = [
  [name: 'primary',  registryCred: 'reg-primary',  sshCred: 'ssh-primary',  config: 'production'],
  [name: 'china',    registryCred: 'reg-china',     sshCred: 'ssh-china',    config: 'china'],
]
```

Deploy in parallel or sequentially per region.

---

## Improvement: Webhook vs SCM Polling

### Before

```
# Jenkins SCM Trigger: * * * * *
# Checks every minute — wastes resources
```

### After (Bitbucket Webhook)

1. In Bitbucket: Repository Settings → Webhooks
2. URL: `http://jenkins:8080/git/notifyCommit?url=<repo-url>`
3. Event: Push

**Jenkins config:**
```groovy
triggers {
    // No SCM polling needed — webhook triggers build
}
```

Benefits:
- Instant builds on push (no 1-minute delay)
- No wasted polling cycles
- Reduced Jenkins load

---

## Migration Checklist

### Phase 1: Quick Wins (1-2 days)

- [ ] Add health check endpoint to application (`/health`)
- [ ] Create rollback script (`rollback.sh`)
- [ ] Stop using `:latest` in production compose files
- [ ] Add `HEALTHCHECK` to Dockerfiles

### Phase 2: Pipeline Migration (3-5 days)

- [ ] Convert Freestyle jobs to Jenkinsfile (Declarative Pipeline)
- [ ] Consolidate multiple Dockerfiles into single parameterized Dockerfile
- [ ] Move hardcoded IPs to Jenkins Credentials
- [ ] Add post-deploy health check step
- [ ] Add Slack/Email notifications

### Phase 3: Quality & Security (1-2 weeks)

- [ ] Add unit test stage to pipeline
- [ ] Integrate SonarQube for code quality
- [ ] Add Trivy image scan before push
- [ ] Set up Bitbucket Webhooks (remove SCM polling)
- [ ] Enable HTTPS on private registries

### Phase 4: Advanced (2-4 weeks)

- [ ] Add integration test stage
- [ ] Implement blue-green deployment
- [ ] Set up Prometheus + Grafana monitoring
- [ ] Automate rollback on health check failure
- [ ] Add coverage reporting (≥ 80% gate)
