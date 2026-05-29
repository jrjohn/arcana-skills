# Pre-Deployment Checklist

> Run through this checklist before every deployment

## Build Verification

- [ ] All automated tests pass (unit + integration)
- [ ] Code coverage meets threshold (≥ 80%)
- [ ] SonarQube Quality Gate: PASSED
- [ ] No blocker or critical issues in SonarQube
- [ ] Docker image builds successfully
- [ ] Docker image size within acceptable range

## Security Verification (🔴)

- [ ] Trivy scan: No CRITICAL vulnerabilities
- [ ] Trivy scan: No HIGH vulnerabilities (or accepted risk)
- [ ] No secrets in Docker image (C1)
- [ ] No `latest` tag used for deployment (C2)
- [ ] Non-root user configured in Dockerfile (I1)
- [ ] Image pulled from trusted registry only

## Configuration Verification

- [ ] Environment variables configured correctly
- [ ] Database migrations applied (if applicable)
- [ ] External service dependencies verified
- [ ] Config files validated (compose/K8s manifests)
- [ ] TLS/SSL certificates valid (production)

## Deployment Readiness

- [ ] Health check endpoints defined (C3)
  - [ ] Liveness: `/health`
  - [ ] Readiness: `/ready`
- [ ] Resource limits set (C5 for K8s)
- [ ] Rollback script exists and tested (C4)
- [ ] Monitoring configured (Prometheus targets)
- [ ] Alert rules configured (AlertManager)

## Communication

- [ ] Team notified of upcoming deployment
- [ ] Deployment window confirmed
- [ ] On-call engineer identified
- [ ] Rollback plan communicated

## Post-Deploy

- [ ] Health check passes after deployment
- [ ] Smoke test passes
- [ ] Monitoring dashboards show normal metrics
- [ ] No error spike in logs
