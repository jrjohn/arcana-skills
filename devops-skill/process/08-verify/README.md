# Node 08: verify（端對端驗證）

> **COR Node**: End-to-end pipeline verification

## Purpose

Verify the entire CI/CD pipeline works end-to-end: from code commit through build, test, deploy, to monitoring.

## Entry Conditions

- All previous nodes (00–07) completed
- All infrastructure running
- All configurations generated

## Verification Checklist

### Infrastructure Verification

| Check | Command | Expected |
|-------|---------|----------|
| Jenkins running | `curl -s http://localhost:8080/login` | HTTP 200 |
| SonarQube running | `curl -s http://localhost:9000/api/system/status` | `{"status":"UP"}` |
| Registry running | `curl -s http://localhost:5000/v2/` | `{}` |
| Prometheus running | `curl -s http://localhost:9090/-/healthy` | `Prometheus Server is Healthy` |
| Grafana running | `curl -s http://localhost:3000/api/health` | `{"status":"ok"}` |

### Pipeline Verification

| Check | Description | Expected |
|-------|-------------|----------|
| Jenkinsfile valid | Syntax check | No errors |
| Docker build | Build test image | Success |
| Docker push | Push to registry | Success |
| Docker pull | Pull from registry | Success |
| Deploy dev | docker-compose up | All services healthy |
| K8s dry-run | kubectl apply --dry-run | No errors |

### Configuration Verification

| Check | File | Validation |
|-------|------|------------|
| Compose files | docker-compose.*.yml | `docker compose config` |
| K8s manifests | k8s/*.yml | `kubectl apply --dry-run=client` |
| Prometheus config | prometheus.yml | `promtool check config` |
| Jenkinsfile | Jenkinsfile | Jenkins Pipeline linter |

### Security Verification

| Check | Rule | Method |
|-------|------|--------|
| No secrets in images | 🔴 C1 | Scan Dockerfile for ENV secrets |
| No latest tag | 🔴 C2 | Grep for `:latest` in configs |
| Health checks present | 🔴 C3 | Check Dockerfile + K8s probes |
| Rollback exists | 🔴 C4 | Verify rollback.sh exists and is executable |
| Resource limits | 🔴 C5 | Check K8s deployment limits |
| Image scanned | 🔴 C6 | Trivy scan report exists |

## Actions

1. **Run all exit-validation scripts** (00–07)
2. **Execute infrastructure health checks**
3. **Validate all configuration files**
4. **Run security checks**
5. **Generate verification report**

## Output

Create `{project-root}/.devops/verify.json`:

```json
{
  "verification_results": {
    "infrastructure": { "passed": 5, "failed": 0, "warnings": 0 },
    "pipeline": { "passed": 6, "failed": 0, "warnings": 0 },
    "configuration": { "passed": 4, "failed": 0, "warnings": 0 },
    "security": { "passed": 6, "failed": 0, "warnings": 0 }
  },
  "overall_status": "PASSED",
  "verified_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/devops-skill/process/08-verify/exit-validation.sh {project-root}`

### Success Criteria

- [ ] All node exit validations pass (00–07)
- [ ] Infrastructure health checks pass
- [ ] No critical security violations
- [ ] verify.json created with overall PASSED status

## Completion

On success → **DevOps setup complete!**

Present final summary:
- Services running and their URLs
- Pipeline configuration summary
- Deployment targets configured
- Monitoring endpoints
- Security compliance status

## Error Handling

| Error | Action |
|-------|--------|
| Previous node validation fails | Identify failed node, guide re-execution |
| Infrastructure down | Re-run Node 01 infra |
| Security violation | Block completion, guide fix |
