# Verification Commands

Quick reference for diagnosing common issues in Arcana Cloud Rust projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Empty response | `grep -rn "Vec::new()\|vec!\[\]" crates/*/src/repository/` | Empty |
| 500 error | `grep -rn "unimplemented!\|todo!" crates/*/src/` | Empty |
| gRPC UNIMPLEMENTED | Compare rpc count in .proto vs impl methods | Match |
| Borrow checker | `cargo check 2>&1 \| head -50` | No errors |
| Type error | `cargo check` | No errors |
| Clippy warning | `cargo clippy -- -D warnings` | No warnings |

---

## 1. Code Quality Checks

### Check for unimplemented methods
```bash
# Must return empty for production-ready code
grep -rn "unimplemented!\|todo!\|// TODO" crates/*/src/
```

### Check for unwrap() in production code
```bash
# Must return empty (unwrap in tests is OK)
grep -rn "\.unwrap()" crates/*/src/ | grep -v "test" | grep -v "#\[cfg(test)\]"
```

### Check for unsafe blocks
```bash
grep -rn "unsafe " crates/*/src/ | grep -v "test"
```

### Clippy lint check
```bash
cargo clippy -- -D warnings
```

### Format check
```bash
cargo fmt -- --check
```

### Type checking
```bash
cargo check
```

---

## 2. Route & Handler Verification

### Count routes defined vs handlers
```bash
echo "Routes defined:"
grep -c "\.route\|\.get\|\.post\|\.put\|\.delete\|\.patch" crates/*/src/api/router.rs 2>/dev/null || echo 0

echo "Handler functions:"
grep -c "pub async fn" crates/*/src/api/handlers/*.rs 2>/dev/null || echo 0
```

### Check for placeholder returns
```bash
grep -rn "Coming Soon\|TODO\|NotImplemented" crates/*/src/api/handlers/*.rs
```

---

## 3. Service Layer Verification

### Service methods called in Handlers
```bash
echo "=== Service Methods Called in Handlers ==="
grep -roh "state\.\w*_service\.\w*\|self\.\w*service\.\w*" crates/*/src/api/handlers/*.rs | sort -u

echo "=== Service Trait Methods ==="
grep -rh "async fn \w*" crates/*/src/domain/services/*.rs | sort -u
```

### Verify Service -> Repository wiring
```bash
echo "=== Repository Methods Called in Services ==="
grep -roh "self\.\w*repo\w*\.\w*" crates/*/src/domain/services/*.rs | sort -u

echo "=== Repository Trait Methods ==="
grep -rh "async fn \w*" crates/*/src/domain/repositories/*.rs | sort -u
```

---

## 4. gRPC Verification

### Count proto methods vs implementation
```bash
echo "gRPC methods defined in proto:"
grep -c "rpc " proto/*.proto 2>/dev/null || echo 0

echo "gRPC methods implemented:"
grep -c "async fn" crates/*/src/grpc/*.rs 2>/dev/null | grep -v "test" || echo 0
```

---

## 5. Dependency Injection Verification

### Check AppState structure
```bash
echo "=== AppState Fields ==="
grep -A 30 "pub struct AppState" crates/*/src/state.rs
```

### Check all Arc<dyn Trait> constructed
```bash
echo "=== Service Constructions ==="
grep -n "Arc::new\|Arc<dyn" crates/*/src/state.rs
```

---

## 6. Mock Data Verification

### Check for empty Vec returns in Repository stubs
```bash
# Must return empty for production-ready stubs
grep -rn "Vec::new()\|vec!\[\]" crates/*/src/infrastructure/db/*_impl.rs
```

### Verify chart-related data
```bash
grep -rn "daily_reports\|weekly_data\|chart_data" crates/*/src/ | grep -E "Vec::new|vec!\[\]"
```

---

## 7. Security Checks

### Check for hardcoded secrets
```bash
grep -rn "password.*=.*\"\|secret.*=.*\"\|api_key.*=.*\"" crates/*/src/
```

### Check for debug prints in production code
```bash
grep -rn "println!\|dbg!" crates/*/src/ | grep -v "test" | grep -v "#\[cfg(test)\]"
```

---

## 8. Test Verification

### Run all tests
```bash
cargo test
```

### Run with output
```bash
cargo test -- --nocapture
```

### Run specific test
```bash
cargo test --package arcana-core -- service::user::tests
```

### Run with coverage
```bash
cargo tarpaulin --out html
open tarpaulin-report.html
```

---

## 9. Database Verification

### Check migration status
```bash
sqlx migrate info --database-url $DATABASE_URL
```

### Run migrations
```bash
sqlx migrate run --database-url $DATABASE_URL
```

### Prepare offline mode data (for CI)
```bash
cargo sqlx prepare --database-url $DATABASE_URL
```

---

## 10. Build Verification

### Debug build
```bash
cargo build
```

### Release build
```bash
cargo build --release
```

### Check binary size
```bash
ls -lh target/release/arcana-server
```

---

## 11. Runtime Health Checks

### Start development server
```bash
cargo run
```

### Check health endpoint
```bash
curl http://localhost:8080/health
```

### Check REST API response
```bash
curl http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check gRPC health
```bash
grpcurl -plaintext localhost:9090 arcana.health.HealthService/Check
```

### Check Prometheus metrics
```bash
curl http://localhost:8080/metrics
```

---

## 12. Docker Verification

### Build image
```bash
docker build -t arcana-rust:test .
```

### Run container
```bash
docker run -p 8080:8080 -p 9090:9090 --env-file .env arcana-rust:test
```

### Check container logs
```bash
docker logs -f $(docker ps -q --filter ancestor=arcana-rust:test)
```

---

## 13. WASM Plugin Verification

### Build plugin
```bash
cd plugins/arcana-audit-plugin
cargo build --target wasm32-wasi --release
```

### Verify plugin binary
```bash
ls -lh plugins/arcana-audit-plugin/target/wasm32-wasi/release/*.wasm
```

---

## Complete Verification Script

```bash
#!/bin/bash
set -e

echo "=== Running Complete Verification ==="

echo "1. Format Check..."
cargo fmt -- --check

echo "2. Clippy Check..."
cargo clippy -- -D warnings

echo "3. Type Check..."
cargo check

echo "4. Tests..."
cargo test

echo "5. Checking for unimplemented code..."
UNIMPLEMENTED=$(grep -rn "unimplemented!\|todo!" crates/*/src/ || true)
if [ -n "$UNIMPLEMENTED" ]; then
    echo "WARNING: Found unimplemented code:"
    echo "$UNIMPLEMENTED"
fi

echo "6. Checking for unwrap() in production..."
UNWRAPS=$(grep -rn "\.unwrap()" crates/*/src/ | grep -v "test" | grep -v "#\[cfg(test)\]" || true)
if [ -n "$UNWRAPS" ]; then
    echo "WARNING: Found unwrap() in production code:"
    echo "$UNWRAPS"
fi

echo "7. Checking for hardcoded secrets..."
SECRETS=$(grep -rn "secret.*=.*\"\|password.*=.*\"" crates/*/src/ || true)
if [ -n "$SECRETS" ]; then
    echo "WARNING: Possible hardcoded secrets:"
    echo "$SECRETS"
fi

echo "8. Checking for unsafe blocks..."
UNSAFE=$(grep -rn "unsafe " crates/*/src/ | grep -v "test" || true)
if [ -n "$UNSAFE" ]; then
    echo "WARNING: Found unsafe blocks:"
    echo "$UNSAFE"
fi

echo "9. Release Build..."
cargo build --release

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`
