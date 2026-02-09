# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)
- [ ] **Tests pass** - `go test ./...`
- [ ] **Build succeeds** - `go build ./cmd/server/`
- [ ] **Vet passes** - `go vet ./...`
- [ ] **No placeholder code** - `grep -rn "panic.*not implemented\|TODO" internal/`
- [ ] **No hardcoded secrets** - `grep -rn "password.*=.*\"\|secret.*=.*\"" internal/`
- [ ] **All fx providers registered** - Check internal/di/module.go

### IMPORTANT (Should Pass)
- [ ] **Input validation** - Struct binding tags for requests
- [ ] **Error handling** - Global error handler middleware
- [ ] **Logging** - Structured zap logging configured
- [ ] **API documentation** - Swagger/OpenAPI enabled

### RECOMMENDED (Nice to Have)
- [ ] **Rate limiting** - API rate limits
- [ ] **Caching** - Redis caching enabled
- [ ] **Monitoring** - Prometheus metrics
- [ ] **Health checks** - /health and /ready endpoints

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Service | 90%+ | ___ |
| Repository/DAO | 80%+ | ___ |
| Controller | 75%+ | ___ |
| Overall | 80%+ | ___ |

---

## API Wiring Verification

### Controller -> Service Wiring
```bash
# List service methods called in controllers
grep -roh "ctrl\.\w*[Ss]ervice\.\w*(" internal/controller/ | sort -u

# List service interface methods
grep -rh "^\s*\w\+(" internal/domain/service/*.go | grep -v "func\|type\|struct" | sort -u

# Every method called MUST exist!
```

### Service -> Repository Wiring
```bash
# List repository methods called in services
grep -roh "s\.\w*[Rr]epo\w*\.\w*(" internal/domain/service/*.go | sort -u

# List repository interface methods
grep -rh "^\s*\w\+(" internal/domain/repository/*.go | grep -v "func\|type\|struct" | sort -u
```

### fx DI Bindings
```bash
# List all providers
grep -rn "fx\.Provide\|fx\.Invoke" internal/di/*.go
```

---

## Security Checklist

- [ ] JWT secret is from environment variable
- [ ] Password hashing uses bcrypt with DefaultCost (10)
- [ ] SQL injection prevented (using GORM parameterized queries)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Sensitive data not in logs
- [ ] TLS configured for production
- [ ] gRPC uses TLS in production

---

## Performance Checklist

- [ ] Database indexes on frequently queried columns
- [ ] Connection pooling configured (MaxIdleConns, MaxOpenConns)
- [ ] Redis caching for hot data
- [ ] gRPC for internal communication
- [ ] Context propagation throughout call chain
- [ ] No N+1 queries (use Preload/Joins)
- [ ] Response compression enabled

---

## Deployment Checklist

### Environment Variables
```bash
# Required
ARCANA_DATABASE_HOST=
ARCANA_DATABASE_PASSWORD=
ARCANA_REDIS_HOST=
ARCANA_JWT_SECRET=
ARCANA_SERVER_MODE=monolithic

# Optional
ARCANA_SERVER_PORT=8080
ARCANA_GRPC_PORT=50051
ARCANA_LOG_LEVEL=info
```

### Docker
```bash
# Build
docker build -t arcana-cloud-go:X.Y.Z .

# Test locally
docker run -p 8080:8080 --env-file .env arcana-cloud-go:X.Y.Z

# Push
docker push arcana-cloud-go:X.Y.Z
```

### Kubernetes
```bash
# Apply manifests
kubectl apply -f deployment/kubernetes/

# Verify
kubectl get pods -l app=arcana-cloud-go
kubectl logs -f deployment/arcana-cloud-go
```

---

## Monitoring Checklist

- [ ] Health endpoint: GET /health
- [ ] Readiness endpoint: GET /ready
- [ ] Prometheus metrics: GET /metrics
- [ ] Error tracking configured
- [ ] Log aggregation configured
- [ ] Alerting rules defined

---

## Release Commands

```bash
# Run all checks
go vet ./...
golangci-lint run
go test -race ./...

# Build
CGO_ENABLED=0 go build -ldflags="-w -s" -o server ./cmd/server/

# Docker
docker build -t arcana-cloud-go:X.Y.Z .
docker push arcana-cloud-go:X.Y.Z

# Deploy (Kubernetes)
kubectl set image deployment/arcana-cloud-go arcana-cloud-go=arcana-cloud-go:X.Y.Z
```

---

## Post-Deployment Verification

1. [ ] Health endpoint returns 200
2. [ ] Can authenticate (login endpoint)
3. [ ] Can perform CRUD operations
4. [ ] Logs are being collected
5. [ ] Metrics are being scraped
6. [ ] No error spikes in monitoring
7. [ ] gRPC connectivity verified
