# Kubernetes Readiness Checklist

> Verify before deploying to Kubernetes

## Manifest Validation

- [ ] All manifests pass `kubectl apply --dry-run=client`
- [ ] Namespace defined and created
- [ ] Labels consistent across all resources
- [ ] Resource names follow naming convention

## Deployment Configuration

- [ ] Image tag uses semantic versioning (not `latest`)
- [ ] `imagePullPolicy` set appropriately
- [ ] Replicas configured (min 2 for production)
- [ ] Rolling update strategy defined
- [ ] Revision history limit set

## Resource Management (🔴 C5)

- [ ] CPU requests defined
- [ ] CPU limits defined
- [ ] Memory requests defined
- [ ] Memory limits defined
- [ ] HPA configured (if auto-scaling needed)
- [ ] PDB configured (for HA)

## Health Probes (🔴 C3)

- [ ] Liveness probe configured
- [ ] Readiness probe configured
- [ ] Startup probe configured (for slow-starting apps)
- [ ] Probe timeouts appropriate
- [ ] Initial delay accounts for startup time

## Configuration

- [ ] ConfigMaps created for non-sensitive config
- [ ] Secrets created for sensitive data (🔴 C1)
- [ ] Environment variables referenced correctly
- [ ] Volume mounts configured (if needed)

## Networking

- [ ] Service defined with correct ports
- [ ] Ingress configured with TLS
- [ ] Network policies defined (if applicable)
- [ ] DNS resolution works

## Security

- [ ] SecurityContext configured
- [ ] runAsNonRoot: true
- [ ] ServiceAccount created with minimal permissions
- [ ] RBAC roles defined

## Observability

- [ ] Prometheus annotations set on pods
- [ ] Metrics endpoint exposed
- [ ] Structured logging configured
- [ ] Log aggregation configured
