# Production Readiness Checklist

## Pre-Release Checklist

### 🔴 CRITICAL (Must Pass)
- [ ] **Tests pass** - `npm test`
- [ ] **TypeScript compiles** - `npm run type-check`
- [ ] **No placeholder code** - `grep -rn "NotImplemented\|TODO" src/`
- [ ] **No hardcoded secrets** - `grep -rn "password.*=.*\"\|secret.*=.*\"" src/`
- [ ] **All DI bindings exist** - Check container.ts

### 🟡 IMPORTANT (Should Pass)
- [ ] **Input validation** - Zod schemas for requests
- [ ] **Error handling** - Global exception handlers
- [ ] **Logging** - Structured logging configured
- [ ] **API documentation** - OpenAPI/Swagger enabled

### 🟢 RECOMMENDED (Nice to Have)
- [ ] **Rate limiting** - API rate limits
- [ ] **Caching** - Redis caching enabled
- [ ] **Monitoring** - Prometheus metrics
- [ ] **Health checks** - /health endpoint

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Service | 90%+ | ___ |
| Repository | 80%+ | ___ |
| Controller | 75%+ | ___ |
| Overall | 85%+ | 90% |

---

## API Wiring Verification

### Controller → Service Wiring
```bash
# List service methods called in controllers
grep -roh "this\.\w*Service\.\w*(" src/controller/*.ts | sort -u

# List service methods defined
grep -rh "async \w*(" src/service/*.ts | grep -oE "async \w+\(" | sort -u

# Every method called MUST exist!
```

### Service → Repository Wiring
```bash
# List repository methods called in services
grep -roh "this\.\w*Repository\.\w*(" src/service/*.ts | sort -u

# List repository methods defined
grep -rh "async \w*(" src/repository/*.ts | grep -oE "async \w+\(" | sort -u
```

### DI Container Bindings
```bash
# List all bindings
grep -rn "container\.bind\|bind<" src/container/*.ts

# List all injections
grep -rn "@inject(" src/
```

---

## Security Checklist

- [ ] JWT secret is from environment variable
- [ ] Password hashing uses bcrypt with cost >= 10
- [ ] SQL injection prevented (using Prisma)
- [ ] XSS prevention in place
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Sensitive data not in logs
- [ ] HTTPS enforced in production

---

## Performance Checklist

- [ ] Database indexes on frequently queried columns
- [ ] Connection pooling configured
- [ ] Redis caching for hot data
- [ ] gRPC for internal communication
- [ ] Async/await properly used
- [ ] No N+1 queries
- [ ] Response compression enabled

---

## Deployment Checklist

### Environment Variables
```bash
# Required
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
NODE_ENV=production

# Optional
PORT=3000
GRPC_PORT=50051
LOG_LEVEL=info
```

### Docker
```bash
# Build
docker build -t arcana-nodejs:X.Y.Z .

# Test locally
docker run -p 3000:3000 --env-file .env arcana-nodejs:X.Y.Z

# Push
docker push arcana-nodejs:X.Y.Z
```

### Kubernetes
```bash
# Apply manifests
kubectl apply -f deploy/k8s/

# Verify
kubectl get pods -l app=arcana-nodejs
kubectl logs -f deployment/arcana-nodejs
```

---

## Monitoring Checklist

- [ ] Health endpoint: GET /health
- [ ] Readiness endpoint: GET /ready
- [ ] Prometheus metrics: GET /metrics
- [ ] Error tracking (Sentry, etc.)
- [ ] Log aggregation configured
- [ ] Alerting rules defined

---

## Release Commands

```bash
# Run all checks
npm run lint
npm run type-check
npm test

# Build
npm run build

# Docker
docker build -t myapp:X.Y.Z .
docker push myapp:X.Y.Z

# Deploy (Kubernetes)
kubectl set image deployment/myapp myapp=myapp:X.Y.Z
```

---

## Post-Deployment Verification

1. [ ] Health endpoint returns 200
2. [ ] Can authenticate (login endpoint)
3. [ ] Can perform CRUD operations
4. [ ] Logs are being collected
5. [ ] Metrics are being scraped
6. [ ] No error spikes in monitoring
