# Verification Commands

Quick reference for diagnosing common issues in Arcana Cloud Go projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Empty response | `grep -rn "return nil, nil\|return \[\]" internal/domain/repository/` | Empty |
| 500 error | `grep -rn "panic\|TODO.*implement" internal/` | Empty |
| gRPC UNIMPLEMENTED | Compare rpc count in .proto vs server methods | Match |
| DI error | Check `fx.Provide` and constructor signatures | All bound |
| Build error | `go vet ./...` | No errors |

---

## 1. Code Quality Checks

### Check for unimplemented methods
```bash
# Must return empty for production-ready code
grep -rn "panic(\"not implemented\")\|TODO.*implement\|// TODO" internal/
```

### Check for empty handler functions
```bash
grep -rn "func.*\*gin.Context.*{}" internal/controller/
```

### Go vet
```bash
go vet ./...
```

### Lint
```bash
golangci-lint run
```

---

## 2. Route & Handler Verification

### Count routes defined vs handlers
```bash
echo "Routes defined:"
grep -c "\.GET\|\.POST\|\.PUT\|\.DELETE\|\.PATCH" internal/controller/http/*.go 2>/dev/null || echo 0

echo "Handler functions:"
grep -c "func.*\*gin.Context" internal/controller/http/*.go 2>/dev/null || echo 0
```

### Check for placeholder returns
```bash
grep -rn "Coming Soon\|TODO\|NotImplemented" internal/controller/http/*.go
```

---

## 3. Service Layer Verification

### Service methods called in Controllers
```bash
echo "=== Service Methods Called in Controllers ==="
grep -roh "ctrl\.\w*[Ss]ervice\.\w*(" internal/controller/ | sort -u

echo "=== Service Interface Methods ==="
grep -rh "^\s*\w\+(" internal/domain/service/*.go | grep -v "func\|type\|struct\|//\|package" | sort -u
```

### Verify Service -> Repository wiring
```bash
echo "=== Repository Methods Called in Services ==="
grep -roh "s\.\w*[Rr]epo\w*\.\w*(" internal/domain/service/*.go | sort -u

echo "=== Repository Interface Methods ==="
grep -rh "^\s*\w\+(" internal/domain/repository/*.go | grep -v "func\|type\|struct\|//\|package" | sort -u
```

---

## 4. gRPC Verification

### Count proto methods vs implementation
```bash
echo "gRPC methods defined in proto:"
grep -c "rpc " api/proto/*.proto 2>/dev/null || echo 0

echo "gRPC methods implemented:"
grep -c "func.*Server).*context.Context" internal/controller/grpc/*.go 2>/dev/null || echo 0
```

---

## 5. Dependency Injection Verification

### Check fx providers
```bash
echo "=== fx.Provide Registrations ==="
grep -rn "fx\.Provide" internal/di/*.go

echo "=== fx.Invoke Registrations ==="
grep -rn "fx\.Invoke" internal/di/*.go
```

### Check constructor functions
```bash
echo "=== Constructor Functions (New*) ==="
grep -rn "func New" internal/ | grep -v "_test.go"
```

---

## 6. Mock Data Verification

### Check for nil/empty returns
```bash
# Must return empty for production-ready stubs
grep -rn "return nil, nil\|return \[\]" internal/domain/repository/*_impl.go
```

### Verify chart-related data
```bash
grep -rn "Summary\|Weekly\|Chart" internal/domain/repository/ | grep -E "return nil"
```

---

## 7. Security Checks

### Check for hardcoded secrets
```bash
grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"" internal/ | grep -v "_test.go"
```

### Check for fmt.Println in production code
```bash
grep -rn "fmt\.Print" internal/ | grep -v "_test.go"
```

---

## 8. Test Verification

### Run all tests
```bash
go test ./...
```

### Run with coverage
```bash
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
```

### Run specific package tests
```bash
go test ./internal/domain/service/...
```

### Run with race detection
```bash
go test -race ./...
```

---

## 9. Database Verification

### Check GORM models
```bash
grep -rn "type.*struct" internal/domain/entity/*.go | grep -v DTO
```

### Check table names
```bash
grep -rn "TableName()" internal/domain/entity/*.go
```

---

## 10. Build Verification

### Standard build
```bash
go build ./cmd/server/
```

### Production build
```bash
CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server/
```

---

## 11. Runtime Health Checks

### Start development server
```bash
go run ./cmd/server/
```

### Check health endpoint
```bash
curl http://localhost:8080/health
```

### Check API response
```bash
curl http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 12. Docker Verification

### Build image
```bash
docker build -t arcana-cloud-go:test .
```

### Run container
```bash
docker run -p 8080:8080 --env-file .env arcana-cloud-go:test
```

### Check container logs
```bash
docker logs -f $(docker ps -q --filter ancestor=arcana-cloud-go:test)
```

---

## Complete Verification Script

```bash
#!/bin/bash
set -e

echo "=== Running Complete Verification ==="

echo "1. Go Vet..."
go vet ./...

echo "2. Lint Check..."
golangci-lint run || echo "WARN: golangci-lint not installed"

echo "3. Tests..."
go test ./...

echo "4. Race Detection..."
go test -race ./...

echo "5. Checking for unimplemented code..."
UNIMPLEMENTED=$(grep -rn "panic.*not implemented\|TODO.*implement" internal/ || true)
if [ -n "$UNIMPLEMENTED" ]; then
    echo "WARNING: Found unimplemented code:"
    echo "$UNIMPLEMENTED"
fi

echo "6. Checking for hardcoded secrets..."
SECRETS=$(grep -rn "password.*=.*\"\|secret.*=.*\"" internal/ | grep -v "_test.go" || true)
if [ -n "$SECRETS" ]; then
    echo "WARNING: Possible hardcoded secrets:"
    echo "$SECRETS"
fi

echo "7. Building..."
CGO_ENABLED=0 go build -ldflags="-w -s" -o server ./cmd/server/

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`
