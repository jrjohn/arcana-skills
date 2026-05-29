# DevOps Security Best Practices

> DevOps Skill Reference

## Critical Rules (🔴)

| Rule | Description | Enforcement |
|------|-------------|-------------|
| C1 | No secrets in Docker images | Trivy scan + Dockerfile lint |
| C2 | No `latest` tag in production | Pipeline validation |
| C3 | All services must have health checks | K8s probe validation |
| C4 | Rollback strategy required | Pre-deploy check |
| C5 | K8s resource limits mandatory | Manifest validation |
| C6 | Docker image security scan required | Trivy in pipeline |

## Secrets Management

### Where to Store Secrets

| Solution | Use Case | Complexity |
|----------|----------|------------|
| K8s Secrets | Basic K8s deployments | Low |
| Docker Secrets | Docker Swarm | Low |
| HashiCorp Vault | Enterprise, multi-cluster | High |
| AWS Secrets Manager | AWS deployments | Medium |
| External Secrets Operator | K8s + external store | Medium |
| Sealed Secrets | GitOps with K8s | Medium |

### Where NOT to Store Secrets

- Docker image ENV or ARG
- docker-compose.yml (in version control)
- Jenkinsfile (in version control)
- ConfigMaps
- Source code
- Git history

## Docker Image Security

### Scanning with Trivy

```bash
# Scan image for vulnerabilities
trivy image myapp:1.0.0

# Fail on CRITICAL severity
trivy image --exit-code 1 --severity CRITICAL myapp:1.0.0

# Scan with all severity levels
trivy image --severity CRITICAL,HIGH,MEDIUM myapp:1.0.0
```

### Image Hardening

| Practice | Priority |
|----------|----------|
| Use minimal base images (alpine/distroless) | 🟡 |
| Run as non-root user | 🟡 |
| Don't install unnecessary packages | 🟢 |
| Use multi-stage builds | 🟡 |
| Pin base image digests | 🟢 |
| Remove package manager cache | 🟢 |

## Network Security

### K8s Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-netpol
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8080
```

## RBAC

### K8s ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-rolebinding
subjects:
  - kind: ServiceAccount
    name: app-sa
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
```

## Supply Chain Security

| Practice | Tool |
|----------|------|
| Sign container images | cosign (Sigstore) |
| SBOM generation | syft |
| Dependency scanning | Trivy fs / npm audit |
| Base image tracking | Renovate / Dependabot |
