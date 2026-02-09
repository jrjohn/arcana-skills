# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)
- [ ] **Tests pass** - `cargo test`
- [ ] **Clippy clean** - `cargo clippy -- -D warnings`
- [ ] **Format check** - `cargo fmt -- --check`
- [ ] **No placeholder code** - `grep -rn "unimplemented!\|todo!" crates/*/src/`
- [ ] **No unwrap() in production** - `grep -rn "\.unwrap()" crates/*/src/ | grep -v test`
- [ ] **No unsafe without justification** - `grep -rn "unsafe " crates/*/src/`
- [ ] **No hardcoded secrets** - `grep -rn "secret.*=.*\"\|password.*=.*\"" crates/*/src/`
- [ ] **All dependencies wired** - Check AppState construction

### IMPORTANT (Should Pass)
- [ ] **Input validation** - serde + custom validators on all request types
- [ ] **Error handling** - AppError with thiserror, mapped to HTTP + gRPC status
- [ ] **Logging** - Structured logging via tracing crate
- [ ] **API documentation** - utoipa/OpenAPI annotations

### RECOMMENDED (Nice to Have)
- [ ] **Rate limiting** - Tower rate limiting middleware
- [ ] **Caching** - Redis caching enabled
- [ ] **Monitoring** - Prometheus metrics via /metrics
- [ ] **Health checks** - /health endpoint

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Service | 90%+ | ___ |
| Repository | 80%+ | ___ |
| Handler | 75%+ | ___ |
| Overall | 80%+ | 80% |

---

## API Wiring Verification

### Handler -> Service Wiring
```bash
# List service methods called in handlers
grep -roh "self\.\w*service\.\w*\|state\.\w*service\.\w*" crates/*/src/api/handlers/*.rs | sort -u

# List service trait methods
grep -rh "async fn \w*" crates/*/src/domain/services/*.rs | sort -u

# Every method called MUST exist in the trait!
```

### Service -> Repository Wiring
```bash
# List repository methods called in services
grep -roh "self\.\w*repo\w*\.\w*" crates/*/src/domain/services/*.rs | sort -u

# List repository trait methods
grep -rh "async fn \w*" crates/*/src/domain/repositories/*.rs | sort -u
```

### AppState Dependency Injection
```bash
# List all fields in AppState
grep -A 30 "pub struct AppState" crates/*/src/state.rs

# Verify all Arc<dyn Trait> are constructed in AppState::new()
grep -n "Arc::new" crates/*/src/state.rs
```

---

## Security Checklist

- [ ] JWT secret is from environment variable (not hardcoded)
- [ ] Password hashing uses Argon2id with recommended params
- [ ] SQL injection prevented (using SQLx compile-time queries)
- [ ] CORS configured correctly (tower-http)
- [ ] Rate limiting enabled (tower middleware)
- [ ] Input validation on all endpoints
- [ ] Sensitive data not in logs (password, tokens)
- [ ] mTLS enabled for service-to-service communication
- [ ] No unsafe blocks in production code

---

## Performance Checklist

- [ ] Database indexes on frequently queried columns
- [ ] Connection pooling configured (SQLx pool)
- [ ] Redis caching for hot data
- [ ] gRPC for internal communication (2.1x faster)
- [ ] Async/await properly used (no blocking in async)
- [ ] No unnecessary .clone() on large types
- [ ] Response compression enabled (tower-http gzip)
- [ ] Release profile optimized (LTO, codegen-units=1)

---

## Deployment Checklist

### Environment Variables
```bash
# Required
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
RUST_LOG=info

# Optional
HTTP_PORT=8080
GRPC_PORT=9090
TLS_ENABLED=true
```

### Docker
```bash
# Build
docker build -t arcana-rust:X.Y.Z .

# Test locally
docker run -p 8080:8080 -p 9090:9090 --env-file .env arcana-rust:X.Y.Z

# Push
docker push arcana-rust:X.Y.Z
```

### Kubernetes
```bash
# Apply manifests
kubectl apply -f deployment/k8s/

# Verify
kubectl get pods -l app=arcana-rust
kubectl logs -f deployment/arcana-rust
```

---

## Monitoring Checklist

- [ ] Health endpoint: GET /health
- [ ] Prometheus metrics: GET /metrics
- [ ] Structured JSON logs via tracing
- [ ] Error tracking configured
- [ ] Log aggregation configured
- [ ] Alerting rules defined (error rate, latency, circuit breaker)

---

## Release Commands

```bash
# Run all checks
cargo fmt -- --check
cargo clippy -- -D warnings
cargo test
cargo build --release

# Docker
docker build -t arcana-rust:X.Y.Z .
docker push arcana-rust:X.Y.Z

# Deploy (Kubernetes)
kubectl set image deployment/arcana-rust arcana-rust=arcana-rust:X.Y.Z
```

---

## Post-Deployment Verification

1. [ ] Health endpoint returns 200
2. [ ] Can authenticate (login endpoint)
3. [ ] Can perform CRUD operations
4. [ ] gRPC health check passes
5. [ ] Logs are being collected
6. [ ] Metrics are being scraped by Prometheus
7. [ ] No error spikes in monitoring
8. [ ] Circuit breakers are closed
