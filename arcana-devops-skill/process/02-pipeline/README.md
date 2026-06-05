# Node 02: pipeline（CI/CD 流水線）

> **COR Node**: Jenkins Pipeline configuration

## Purpose

Generate Jenkinsfile(s) and configure Jenkins jobs for the project's CI/CD pipeline.

## Entry Conditions

- Node 01 (infra) completed
- Jenkins running and accessible
- init.json available with project types

## Pipeline Stages

```
Checkout → Build → Test → SonarQube → Docker Build → Push → Deploy → Notify
```

### Stage Details

| Stage | Description | Failure Action |
|-------|-------------|----------------|
| Checkout | Clone repo from SCM | Abort pipeline |
| Build | Compile/package per language | Abort + notify |
| Test | Run unit + integration tests | Abort + notify |
| SonarQube | Code quality analysis | Abort if Quality Gate fails |
| Docker Build | Build Docker image | Abort + notify |
| Push | Push image to registry | Abort + notify |
| Deploy | Deploy to target environment | Abort + rollback |
| Notify | Send status notification | Log only |

## Actions

1. **Read init.json** for project types
2. **Select Jenkinsfile template(s)** based on project types
3. **Generate Jenkinsfile(s)** customized for the project
4. **Generate jenkins-casc.yml** for Jenkins Configuration as Code
5. **Validate Jenkinsfile syntax**

## Template Selection

| Project Type | Template |
|-------------|----------|
| Java/Spring Boot | `templates/jenkins/Jenkinsfile.springboot` |
| Node.js/Express | `templates/jenkins/Jenkinsfile.node` |
| Python/Flask | `templates/jenkins/Jenkinsfile.template` (generic) |
| React/Angular | `templates/jenkins/Jenkinsfile.node` (adapted) |
| iOS/Android | `templates/jenkins/Jenkinsfile.mobile` |

## Output

Create `{project-root}/.devops/pipeline.json`:

```json
{
  "jenkinsfiles": ["Jenkinsfile"],
  "casc_file": "jenkins-casc.yml",
  "pipeline_stages": ["checkout", "build", "test", "sonarqube", "docker-build", "push", "deploy", "notify"],
  "configured_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/02-pipeline/exit-validation.sh {project-root}`

### Success Criteria

- [ ] Jenkinsfile exists in project root
- [ ] Jenkinsfile contains all required stages
- [ ] jenkins-casc.yml is valid YAML (if generated)
- [ ] pipeline.json created

## Next Node

On success → `03-build`

## Error Handling

| Error | Action |
|-------|--------|
| Unknown project type | Use generic Jenkinsfile.template |
| Jenkins not accessible | Re-run Node 01 infra |
| Syntax error in Jenkinsfile | Auto-fix common issues, re-validate |
