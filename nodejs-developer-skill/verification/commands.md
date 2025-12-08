# Verification Commands

Quick reference for diagnosing common issues in Arcana Cloud Node.js projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Empty response | `grep -rn "= \[\]\|return \[\]" src/repository/*Impl.ts` | Empty |
| 500 error | `grep -rn "throw new Error\|NotImplemented" src/` | Empty |
| gRPC UNIMPLEMENTED | Compare rpc count in .proto vs servicer | Match |
| DI error | Check `@injectable()` and `container.bind()` | All bound |
| Type error | `npm run type-check` | No errors |

---

## 1. Code Quality Checks

### Check for unimplemented methods
```bash
# Must return empty for production-ready code
grep -rn "throw new Error.*NotImplemented\|TODO.*implement\|// TODO" src/
```

### Check for empty route handlers
```bash
grep -rn "async.*Request.*Response.*{}" src/controller/
```

### TypeScript type checking
```bash
npm run type-check
```

### ESLint
```bash
npm run lint
```

---

## 2. Route & Handler Verification

### Count routes defined vs handlers
```bash
echo "Routes defined:"
grep -c "router\.\(get\|post\|put\|delete\|patch\)" src/controller/*.ts 2>/dev/null || echo 0

echo "Handler functions:"
grep -c "async.*req.*res" src/controller/*.ts 2>/dev/null || echo 0
```

### Check for placeholder returns
```bash
grep -rn "router\.\(get\|post\|put\|delete\)" -A10 src/controller/*.ts | \
grep -E "Coming Soon\|TODO\|NotImplemented"
```

---

## 3. Service Layer Verification

### Service methods called in Controllers
```bash
echo "=== Service Methods Called in Controllers ==="
grep -roh "this\.\w*Service\.\w*(" src/controller/*.ts | sort -u

echo "=== Service Methods Defined ==="
grep -rh "async \w*(" src/service/*.ts | grep -oE "async \w+\(" | sort -u
```

### Verify Service→Repository wiring
```bash
echo "=== Repository Methods Called in Services ==="
grep -roh "this\.\w*Repository\.\w*(" src/service/*.ts | sort -u

echo "=== Repository Class Methods ==="
grep -rh "async \w*(" src/repository/*.ts | grep -oE "async \w+\(" | sort -u
```

---

## 4. gRPC Verification

### Count proto methods vs implementation
```bash
echo "gRPC methods defined in proto:"
grep -c "rpc " src/grpc/protos/*.proto 2>/dev/null || echo 0

echo "gRPC methods implemented:"
grep -c "async.*call.*callback\|async.*request" src/grpc/*Servicer.ts 2>/dev/null || echo 0
```

---

## 5. Dependency Injection Verification

### Check DI container bindings
```bash
echo "=== DI Container Bindings ==="
grep -rn "container\.bind\|bind<" src/container/*.ts
```

### Check injectable decorators
```bash
echo "=== Injectable Classes ==="
grep -rn "@injectable()" src/
```

### Check inject decorators
```bash
echo "=== Injected Dependencies ==="
grep -rn "@inject(" src/
```

---

## 6. Mock Data Verification

### Check for empty array returns
```bash
# Must return empty for production-ready stubs
grep -rn "= \[\]\|return \[\]" src/repository/*Impl.ts
```

### Verify chart-related data
```bash
grep -rn "dailyReports\|weeklyData\|chartData" src/repository/ | \
grep -E "= \[\]|return \[\]"
```

---

## 7. Security Checks

### Check for hardcoded secrets
```bash
grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"" src/
```

### Check for console.log in production code
```bash
grep -rn "console\.log" src/ --include="*.ts" | grep -v "test\|spec"
```

---

## 8. Test Verification

### Run all tests
```bash
npm test
```

### Run with coverage
```bash
npm run test:coverage
```

### Run specific test file
```bash
npm test -- src/service/__tests__/UserService.test.ts
```

### Run tests in watch mode
```bash
npm test -- --watch
```

---

## 9. Database Verification

### Check Prisma schema
```bash
npx prisma validate
```

### Check migrations status
```bash
npx prisma migrate status
```

### Generate Prisma client
```bash
npx prisma generate
```

---

## 10. Build Verification

### TypeScript compile
```bash
npm run build
```

### Check for build errors
```bash
npx tsc --noEmit
```

---

## 11. Runtime Health Checks

### Start development server
```bash
npm run dev
```

### Check health endpoint
```bash
curl http://localhost:3000/health
```

### Check API response
```bash
curl http://localhost:3000/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 12. Docker Verification

### Build image
```bash
docker build -t arcana-nodejs:test .
```

### Run container
```bash
docker run -p 3000:3000 --env-file .env arcana-nodejs:test
```

### Check container logs
```bash
docker logs -f $(docker ps -q --filter ancestor=arcana-nodejs:test)
```

---

## Complete Verification Script

```bash
#!/bin/bash
set -e

echo "=== Running Complete Verification ==="

echo "1. TypeScript Check..."
npm run type-check

echo "2. Lint Check..."
npm run lint

echo "3. Tests..."
npm test

echo "4. Checking for unimplemented code..."
UNIMPLEMENTED=$(grep -rn "NotImplemented\|TODO.*implement" src/ || true)
if [ -n "$UNIMPLEMENTED" ]; then
    echo "WARNING: Found unimplemented code:"
    echo "$UNIMPLEMENTED"
fi

echo "5. Checking for hardcoded secrets..."
SECRETS=$(grep -rn "password.*=.*\"\|secret.*=.*\"" src/ || true)
if [ -n "$SECRETS" ]; then
    echo "WARNING: Possible hardcoded secrets:"
    echo "$SECRETS"
fi

echo "6. Building..."
npm run build

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`
