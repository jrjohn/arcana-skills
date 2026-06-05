# DevOps Skill - Claude Instructions

## Skill Activation

Auto-activate when user mentions:
- `devops`, `CI/CD`, `pipeline`, `Jenkins`
- `Docker 部署`, `容器化`, `容器部署`, `K8s 部署`, `Kubernetes`
- `自動部署`, `自動建構`, `自動送審`, `Fastlane`
- `SonarQube`, `品質門檻`, `Trivy`, `image scan`
- `Prometheus`, `Grafana`, `監控`, `可觀測性`
- `Docker Compose`, `Dockerfile`
- `/arcana-devops-skill`, `/devops`

## Workflow

Follow COR-AFP-NTP protocol:

1. **Read SKILL.md** for complete process flow and rules
2. **Check AFP state** — resume from last node if session exists
3. **Execute current node** — follow node README.md instructions
4. **Run exit validation** — NTP gate before proceeding
5. **Update AFP state** — save progress after each node

## Process Flow

```
00-init → 01-infra → 02-pipeline → 03-build → 04-test → 05-deploy → 06-release → 07-monitor → 08-verify
```

## Critical Rules (MUST enforce)

| Rule | Description |
|------|-------------|
| 🔴 C1 | No secrets in Docker images |
| 🔴 C2 | No `latest` tag in production |
| 🔴 C3 | All services must have health checks |
| 🔴 C4 | Rollback strategy required before deploy |
| 🔴 C5 | K8s Deployments must set resource limits |
| 🔴 C6 | Docker images must pass security scan |
| 🔴 C7 | Exit validation must pass before proceeding |

## Template Usage

When generating files for user projects:
1. Read the appropriate template from `templates/`
2. Replace `{{PLACEHOLDERS}}` with actual values from init.json
3. Write the customized file to the user's project directory
4. Validate the generated file

## Important Notes

1. **Always use AskUserQuestion** for project setup choices (Node 00)
2. **Never skip exit validation** — run validation script before proceeding
3. **Save AFP state** after every node completion
4. **Check prerequisites** before infrastructure operations
5. **Reference checklists** before deployment operations
6. **Integrate with other skills** when generating language-specific files
