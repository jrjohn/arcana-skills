# Kubernetes Deployment Strategies

> DevOps Skill Reference

## Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Extra pods during update
    maxUnavailable: 0  # Always maintain full capacity
```

**Pros**: Zero downtime, gradual rollout
**Cons**: Both versions coexist briefly

### Blue-Green

Deploy new version alongside old, then switch traffic.

```bash
# Deploy green (new)
kubectl apply -f deployment-green.yml
# Verify green
kubectl rollout status deployment/app-green
# Switch service selector
kubectl patch svc app -p '{"spec":{"selector":{"version":"green"}}}'
# Remove blue (old)
kubectl delete deployment app-blue
```

### Canary

Route small percentage of traffic to new version.

```yaml
# Canary deployment (10% traffic)
spec:
  replicas: 1  # vs 9 replicas in stable
  template:
    metadata:
      labels:
        app: myapp
        version: canary
```

## Resource Management

### Resource Requests & Limits (🔴 C5)

```yaml
resources:
  requests:    # Scheduling guarantee
    cpu: 100m
    memory: 128Mi
  limits:      # Maximum allowed
    cpu: 500m
    memory: 512Mi
```

### Guidelines

| Service Type | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------------|------------|-----------|----------------|-------------|
| API (light) | 100m | 500m | 128Mi | 512Mi |
| API (heavy) | 500m | 2000m | 512Mi | 2Gi |
| Worker | 250m | 1000m | 256Mi | 1Gi |
| Frontend | 50m | 200m | 64Mi | 256Mi |

## Health Probes (🔴 C3)

### Liveness Probe
Determines if container is running. Failure → restart container.

### Readiness Probe
Determines if container can accept traffic. Failure → remove from service.

### Startup Probe
Determines if application has started. Failure during startup → no liveness check.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
startupProbe:
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30
  periodSeconds: 5
```

## HPA (Horizontal Pod Autoscaler)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## PodDisruptionBudget

Ensures minimum availability during voluntary disruptions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  minAvailable: 1  # or maxUnavailable: 1
  selector:
    matchLabels:
      app: myapp
```

## Secrets Management (🔴 C1)

**Never** commit secrets to version control. Use:
- `kubectl create secret generic`
- External Secrets Operator
- HashiCorp Vault
- Sealed Secrets

## Rollback

```bash
# View rollout history
kubectl rollout history deployment/myapp

# Rollback to previous version
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout undo deployment/myapp --to-revision=3
```
