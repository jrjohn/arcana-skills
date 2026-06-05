# Node 01: infra（基礎設施）

> **COR Node**: DevOps toolchain setup via Docker Compose

## Purpose

Deploy the DevOps infrastructure using Docker Compose: Jenkins, SonarQube, Docker Registry, and optionally Nexus.

## Entry Conditions

- Node 00 (init) completed
- Docker daemon running
- init.json available

## Actions

1. **Generate docker-compose.infra.yml**
   - Read init.json for project configuration
   - Generate from `templates/compose/docker-compose.infra.yml`
   - Customize ports and volumes based on project

2. **Create required directories**
   ```bash
   mkdir -p {project-root}/.devops/jenkins_home
   mkdir -p {project-root}/.devops/sonarqube/{data,logs,extensions}
   mkdir -p {project-root}/.devops/registry
   mkdir -p {project-root}/.devops/nexus-data  # if enabled
   ```

3. **Set permissions**
   ```bash
   chmod -R 777 {project-root}/.devops/sonarqube  # SonarQube requirement
   ```

4. **Start infrastructure**
   ```bash
   docker compose -f docker-compose.infra.yml up -d
   ```

5. **Wait for health checks**
   - Jenkins: `curl -s http://localhost:8080/login`
   - SonarQube: `curl -s http://localhost:9000/api/system/status`
   - Registry: `curl -s http://localhost:5000/v2/`

## Infrastructure Components

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| Jenkins | jenkins/jenkins:lts | 8080 | CI/CD engine with Docker-in-Docker |
| SonarQube | sonarqube:community | 9000 | Code quality analysis |
| Docker Registry | registry:2 | 5000 | Private image repository |
| Nexus | sonatype/nexus3 | 8081 | Maven/npm private registry (optional) |
| PostgreSQL | postgres:16-alpine | 5432 | SonarQube database |

## Output

Create `{project-root}/.devops/infra.json`:

```json
{
  "services": {
    "jenkins": { "url": "http://localhost:8080", "status": "running" },
    "sonarqube": { "url": "http://localhost:9000", "status": "running" },
    "registry": { "url": "http://localhost:5000", "status": "running" }
  },
  "compose_file": "docker-compose.infra.yml",
  "started_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/01-infra/exit-validation.sh {project-root}`

### Success Criteria

- [ ] docker-compose.infra.yml exists and is valid
- [ ] All services are running
- [ ] Jenkins responds on port 8080
- [ ] SonarQube responds on port 9000
- [ ] Registry responds on port 5000

## Next Node

On success → `02-pipeline`

## Error Handling

| Error | Action |
|-------|--------|
| Port conflict | Suggest alternative ports, update compose file |
| SonarQube OOM | Guide: `sysctl -w vm.max_map_count=262144` |
| Jenkins startup slow | Wait up to 120s, show progress |
| Disk space low | Warn user, suggest cleanup |
