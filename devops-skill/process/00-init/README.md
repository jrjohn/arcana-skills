# Node 00: init（初始化）

> **COR Node**: Prerequisites verification & project initialization

## Purpose

Verify all prerequisites are installed, collect project type selection, and initialize project directory structure.

## Entry Conditions

- User has invoked devops-skill
- No previous node required

## Questions to Ask

Use `AskUserQuestion` to gather:

### 1. Project Language/Framework

```
Question: Which languages/frameworks does your project use?
Header: Tech Stack
Options:
- Java/Spring Boot
- Python/Flask
- Node.js/Express
- React
- Angular
- Vue.js
- Rust
- Go
- Swift/iOS
- Android/Kotlin
- HarmonyOS
- Windows/.NET (API or Desktop)
- ESP32 (Embedded Firmware)
- STM32 (Embedded Firmware)
MultiSelect: true
```

### 2. Deployment Target

```
Question: Where do you want to deploy?
Header: Deploy Target
Options:
- Docker Compose + SSH Remote (Production) (Recommended)
- Kubernetes (Production, optional)
- Cloud (AWS/GCP/Azure)
- On-Premise
MultiSelect: true
```

### 3. Project Name

```
Question: What is your project name? (lowercase, dashes allowed)
Header: Project Name
Free text input
```

## Actions

1. **Check prerequisites**
   ```bash
   docker --version
   docker compose version
   kubectl version --client (if K8s selected)
   ```

2. **Create project DevOps directory**
   ```bash
   mkdir -p {project-root}/.devops
   ```

3. **Initialize AFP state**
   Create `{project-root}/.devops/current-process.json`

4. **Save init output**
   Create `{project-root}/.devops/init.json`

## Output

Create `{project-root}/.devops/init.json`:

```json
{
  "project_name": "my-project",
  "project_types": ["springboot", "react"],
  "deploy_targets": ["docker-compose", "k8s"],
  "prerequisites": {
    "docker": "24.0.7",
    "docker_compose": "2.23.0",
    "kubectl": "1.28.0"
  },
  "project_root": "/path/to/project",
  "initialized_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/devops-skill/process/00-init/exit-validation.sh {project-root}`

### Success Criteria

- [ ] Docker daemon is running
- [ ] .devops/ directory exists
- [ ] init.json exists with valid content
- [ ] project_name is not empty
- [ ] At least one project_type selected
- [ ] At least one deploy_target selected

## Next Node

On success → `01-infra`

## Error Handling

| Error | Action |
|-------|--------|
| Docker not installed | Guide user to install Docker Desktop |
| kubectl not found | Skip if K8s not in deploy targets |
| User cancels | Save partial state, allow resume |
