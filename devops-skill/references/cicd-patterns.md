# CI/CD Flow Patterns

> DevOps Skill Reference

## Standard CI/CD Pipeline

```
Code Commit → Build → Test → Quality Gate → Docker Build → Security Scan → Push → Deploy → Monitor
```

## Branching Strategy

### Git Flow

| Branch | Purpose | Deploy To |
|--------|---------|-----------|
| `main` | Production-ready code | Production |
| `develop` | Integration branch | Staging |
| `feature/*` | New features | Dev (optional) |
| `release/*` | Release preparation | Staging |
| `hotfix/*` | Emergency fixes | Production |

### Trunk-Based Development

| Branch | Purpose | Deploy To |
|--------|---------|-----------|
| `main` | Single source of truth | Production |
| `feature/*` | Short-lived branches | Dev (optional) |

## Environment Promotion

```
Dev → Staging → Production

feature/* → develop → release/* → main
     ↓          ↓          ↓        ↓
    Dev      Staging    Staging   Production
```

## Quality Gates

| Gate | Tool | Criteria |
|------|------|----------|
| Code Quality | SonarQube | No blocker/critical issues |
| Test Coverage | JaCoCo/Jest | ≥ 80% coverage |
| Security Scan | Trivy | No CRITICAL vulnerabilities |
| Manual Review | PR Review | Approved by reviewer |
| Performance | Load Test | Latency < threshold |

## Versioning Strategy

### Semantic Versioning (SemVer)

```
MAJOR.MINOR.PATCH
  1.2.3

MAJOR: Breaking changes
MINOR: New features (backward compatible)
PATCH: Bug fixes
```

### Docker Tag Strategy

```
{registry}/{project}/{service}:{version}
{registry}/{project}/{service}:{build-number}-{git-sha}

Example:
localhost:5000/myapp/api:1.2.3
localhost:5000/myapp/api:42-abc1234
```

## Artifact Management

| Artifact | Storage | Retention |
|----------|---------|-----------|
| Docker images | Docker Registry | Last 10 versions |
| JAR/WAR | Nexus | Last 10 versions |
| npm packages | Nexus/npm | Last 10 versions |
| Test reports | Jenkins | Last 10 builds |
| Build logs | Jenkins | Last 10 builds |

## Notification Channels

| Event | Channel | Urgency |
|-------|---------|---------|
| Build success | Slack/Teams | Low |
| Build failure | Slack/Teams + Email | High |
| Deploy success | Slack/Teams | Medium |
| Deploy failure | Slack/Teams + Email + PagerDuty | Critical |
| Security alert | Email + PagerDuty | Critical |

---

## Freestyle → Pipeline Migration

### Why Migrate

| Aspect | Freestyle Job | Declarative Pipeline |
|--------|--------------|---------------------|
| Version control | Config in Jenkins UI | Jenkinsfile in Git |
| Code review | Not possible | PR-based review |
| Reproducibility | Manual recreation | `git clone` + run |
| Stages | Implicit (shell script) | Explicit `stage()` blocks |
| Error handling | Manual | `post { failure { } }` |
| Parallelism | Separate jobs | `parallel { }` in one pipeline |
| Credentials | Global/Job-level | `credentials()` + `withCredentials()` |
| Rollback | Manual | Automated in `post { failure { } }` |

### Migration Steps

1. **Extract shell commands** from Freestyle job's "Execute Shell" build steps
2. **Create Jenkinsfile** with `pipeline { }` declarative syntax
3. **Map build steps to stages**: Checkout → Build → Test → Docker → Push → Deploy
4. **Move credentials** from hardcoded values to Jenkins Credentials store
5. **Add `post` blocks** for notifications and rollback
6. **Add parameters** to replace manual job configuration
7. **Test on a branch** before replacing the Freestyle job

### Example: Before & After

**Before (Freestyle shell):**
```bash
cd web && npm run build && cd ..
cp cloud/Dockerfile . && docker build -t app:${BUILD_NUMBER} .
docker push registry/app:latest
ssh user@host "docker compose down && docker compose up -d"
```

**After (Declarative Pipeline):**
```groovy
pipeline {
    agent any
    stages {
        stage('Build')  { steps { sh 'npm ci && npm run build' } }
        stage('Docker') { steps { sh "docker build -t app:${BUILD_NUMBER} ." } }
        stage('Push')   { steps { sh "docker push registry/app:${BUILD_NUMBER}" } }
        stage('Deploy') { steps { deployRemote(tag: env.BUILD_NUMBER) } }
    }
    post {
        failure { rollbackRemote() }
    }
}
```

See: `templates/jenkins/Jenkinsfile.cloud` for a complete multi-repo example.
See: `references/migration-patterns.md` for detailed analysis.

---

## SCM Polling → Webhook Migration

### Problem

SCM polling (e.g. `* * * * *`) wastes resources by checking for changes every minute, even when no commits occur. This adds unnecessary load to both Jenkins and the Git server.

### Solution: Webhook Triggers

| Aspect | SCM Polling | Webhook |
|--------|------------|---------|
| Trigger speed | Up to 1 min delay | Instant on push |
| Resource usage | Constant polling load | Event-driven (zero idle cost) |
| Git server load | High (repeated `git ls-remote`) | None |
| Configuration | Jenkins-only | Git server + Jenkins |

### Setup by Git Provider

**Bitbucket Server:**
1. Repository Settings → Webhooks
2. URL: `http://<jenkins>/git/notifyCommit?url=<repo-url>`
3. Event: Push

**GitHub:**
1. Repository Settings → Webhooks
2. URL: `http://<jenkins>/github-webhook/`
3. Content type: `application/json`
4. Event: Push

**GitLab:**
1. Settings → Integrations
2. URL: `http://<jenkins>/project/<job-name>`
3. Trigger: Push events

### Jenkins Configuration

```groovy
// Remove SCM polling — webhook handles it
triggers {
    // No pollSCM needed
}
```

For Jenkins jobs that still need polling as a fallback:
```groovy
triggers {
    pollSCM('H/15 * * * *')  // Every 15 min as fallback, not every minute
}
