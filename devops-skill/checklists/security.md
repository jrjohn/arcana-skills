# Security Audit Checklist

> Comprehensive security review for DevOps infrastructure

## Docker Security

- [ ] All images use specific version tags (not `latest`)
- [ ] All images scanned with Trivy
- [ ] No CRITICAL/HIGH vulnerabilities (or documented exceptions)
- [ ] Containers run as non-root user
- [ ] No secrets stored in image layers
- [ ] `.dockerignore` excludes sensitive files
- [ ] Multi-stage builds used (no build tools in runtime)
- [ ] Base images from trusted registries only

## Kubernetes Security

- [ ] RBAC configured (no cluster-admin for workloads)
- [ ] ServiceAccounts created per service
- [ ] Network Policies defined
- [ ] Pod Security Standards enforced
- [ ] Resource limits set on all containers
- [ ] Secrets encrypted at rest
- [ ] No privileged containers
- [ ] Read-only root filesystem where possible

## CI/CD Pipeline Security

- [ ] Jenkins access restricted (authentication required)
- [ ] Credentials stored in Jenkins Credential Store
- [ ] Pipeline scripts reviewed before execution
- [ ] No plaintext secrets in Jenkinsfile
- [ ] Build agents isolated (no persistent state)
- [ ] Artifact signing enabled (optional)

## Network Security

- [ ] Internal services not exposed publicly
- [ ] TLS/SSL for all external endpoints
- [ ] Registry access restricted
- [ ] SonarQube access restricted
- [ ] Jenkins access restricted

## Secrets Management

- [ ] No secrets in source code
- [ ] No secrets in Docker images
- [ ] No secrets in docker-compose files (use .env or secrets)
- [ ] K8s Secrets not committed to Git
- [ ] Secrets rotated periodically
- [ ] Access to secrets audited

## Monitoring & Alerting

- [ ] Security alerts configured
- [ ] Failed login attempts monitored
- [ ] Unusual traffic patterns detected
- [ ] Container restart alerts enabled
- [ ] Image vulnerability alerts enabled
