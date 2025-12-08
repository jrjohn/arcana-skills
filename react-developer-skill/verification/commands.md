# Verification Commands

Quick reference for diagnosing common issues in Arcana React projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Empty response | `grep -rn "= \[\]\|return \[\]" src/data/repositories/*Impl.ts` | Empty |
| Build error | `npm run type-check` | No errors |
| Navigation crash | Compare routes.tsx paths vs component imports | Match |
| DI error | Check `RepositoryProvider.tsx` bindings | All bound |
| Type error | `npm run type-check` | No errors |

---

## 1. Code Quality Checks

### Check for unimplemented methods
```bash
# Must return empty for production-ready code
grep -rn "throw new Error.*NotImplemented\|TODO.*implement\|// TODO" src/
```

### Check for empty handlers
```bash
grep -rn "onClick={undefined}\|onClick={() => {}}\|onChange={() => {}}" src/
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

## 2. Route & Component Verification

### Count routes defined vs components
```bash
echo "Routes defined:"
grep -c "path:" src/router/routes.tsx 2>/dev/null || echo 0

echo "Components imported:"
grep -c "element:" src/router/routes.tsx 2>/dev/null || echo 0
```

### Check for placeholder components
```bash
grep -rn "PlaceholderComponent\|Coming Soon\|NotImplemented" src/
```

### Verify lazy loading
```bash
# List lazy-loaded components
grep -rn "React.lazy\|lazy(" src/router/
```

---

## 3. ViewModel & Hook Verification

### ViewModel hooks defined
```bash
echo "=== ViewModel Hooks Defined ==="
grep -rh "export function use.*ViewModel" src/presentation/**/*.ts | sort -u
```

### ViewModel hooks used in components
```bash
echo "=== ViewModel Hooks Used ==="
grep -rh "use.*ViewModel(" src/presentation/**/*.tsx | sort -u
```

### Check for missing effect subscriptions
```bash
echo "=== Effects not subscribed ==="
grep -rn "effect\$" src/presentation/**/*.tsx | grep -v "subscribe"
```

---

## 4. Repository Verification

### Repository interface methods
```bash
echo "=== Repository Interface Methods ==="
grep -rh "[a-zA-Z]*(" src/domain/repositories/*.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

### Repository implementation methods
```bash
echo "=== Repository Implementation Methods ==="
grep -rh "async [a-zA-Z]*(" src/data/repositories/*.impl.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

### Check for empty array returns
```bash
# Must return empty for production-ready stubs
grep -rn "= \[\]\|return \[\]" src/data/repositories/*Impl.ts
```

---

## 5. Provider Verification

### Check provider bindings
```bash
echo "=== Provider Bindings ==="
grep -rn "value=\|Provider" src/core/providers/*.tsx
```

### Check context usage
```bash
echo "=== Context Usage ==="
grep -rn "useContext\|createContext" src/
```

### Check for missing providers
```bash
# List all contexts created
echo "=== Contexts Created ==="
grep -rh "createContext" src/ | sort -u

# List all contexts used
echo "=== Contexts Used ==="
grep -rh "useContext" src/ | sort -u
```

---

## 6. Mock Data Verification

### Check for empty array returns in mocks
```bash
grep -rn "= \[\]\|return \[\]" src/data/repositories/mock/
```

### Verify chart-related data
```bash
grep -rn "dailyReports\|weeklyData\|chartData" src/data/repositories/ | \
grep -E "= \[\]|Promise.resolve\(\[\]\)"
```

### Check mock data consistency
```bash
# Look for hardcoded IDs
grep -rn "mock_\|test_\|fake_" src/data/repositories/mock/
```

---

## 7. Security Checks

### Check for hardcoded secrets
```bash
grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"\|token.*=.*\"" src/
```

### Check for console.log in production code
```bash
grep -rn "console\.log\|console\.error\|console\.warn" src/ --include="*.ts" --include="*.tsx" | grep -v "test\|spec\|__tests__"
```

### Check for exposed environment variables
```bash
grep -rn "process.env\|import.meta.env" src/ | grep -v "VITE_"
```

---

## 8. Test Verification

### Run all tests
```bash
npm test
```

### Run with coverage
```bash
npm test -- --coverage
```

### Run specific test file
```bash
npm test -- src/presentation/pages/auth/useLoginViewModel.test.ts
```

### Run tests in watch mode
```bash
npm test -- --watch
```

### Run tests for changed files
```bash
npm test -- --onlyChanged
```

---

## 9. Build Verification

### TypeScript compile
```bash
npm run build
```

### Check for build errors
```bash
npx tsc --noEmit
```

### Analyze bundle size
```bash
npm run build -- --analyze
# or
npx vite-bundle-visualizer
```

### Check for large dependencies
```bash
npx bundle-phobia
```

---

## 10. Runtime Health Checks

### Start development server
```bash
npm run dev
```

### Preview production build
```bash
npm run build && npm run preview
```

### Check for React errors
```bash
# In browser console
localStorage.setItem('debug', 'true');
# Then check React DevTools
```

---

## 11. Navigation Verification

### Check NavGraph methods
```bash
echo "=== NavGraph Methods ==="
grep -rh "to[A-Z][a-zA-Z]*" src/core/hooks/useNavGraph.ts | grep -oE "to[A-Z][a-zA-Z]*" | sort -u
```

### Check routes defined
```bash
echo "=== Routes Defined ==="
grep -rh "path:" src/router/routes.tsx | grep -oE "'[^']+'" | sort -u
```

### Verify navigation callbacks
```bash
echo "=== Navigation Props ==="
grep -rh "onNavigate" src/presentation/**/*.tsx | grep -oE "onNavigate[A-Za-z]*" | sort -u
```

---

## 12. Docker Verification

### Build image
```bash
docker build -t arcana-react:test .
```

### Run container
```bash
docker run -p 3000:80 arcana-react:test
```

### Check container logs
```bash
docker logs -f $(docker ps -q --filter ancestor=arcana-react:test)
```

### Check container size
```bash
docker images arcana-react:test --format "{{.Size}}"
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
npm test -- --coverage --watchAll=false

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

echo "6. Checking for empty handlers..."
EMPTY_HANDLERS=$(grep -rn "onClick={() => {}}\|onChange={() => {}}" src/ || true)
if [ -n "$EMPTY_HANDLERS" ]; then
    echo "WARNING: Found empty handlers:"
    echo "$EMPTY_HANDLERS"
fi

echo "7. Checking for empty array returns..."
EMPTY_ARRAYS=$(grep -rn "return \[\]\|= \[\]" src/data/repositories/*.impl.ts || true)
if [ -n "$EMPTY_ARRAYS" ]; then
    echo "WARNING: Found empty array returns:"
    echo "$EMPTY_ARRAYS"
fi

echo "8. Building..."
npm run build

echo "9. Bundle size check..."
du -sh dist/

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`

---

## CI/CD Pipeline Commands

### GitHub Actions Example
```yaml
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run type-check

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm test -- --coverage --watchAll=false

      - name: Build
        run: npm run build

      - name: Check bundle size
        run: |
          SIZE=$(du -sb dist/ | cut -f1)
          if [ $SIZE -gt 5000000 ]; then
            echo "Bundle too large: $SIZE bytes"
            exit 1
          fi
```

---

## Troubleshooting Common Issues

### "Module not found" error
```bash
# Check if file exists
ls -la src/path/to/module.ts

# Check import path
grep -rn "from.*module" src/

# Verify tsconfig paths
cat tsconfig.json | grep "paths" -A 10
```

### "Cannot read property of undefined"
```bash
# Check for optional chaining
grep -rn "\." src/ | grep -v "?." | grep -E "\.[a-zA-Z]+\("
```

### "Maximum update depth exceeded"
```bash
# Check for useEffect dependencies
grep -rn "useEffect" src/ -A 5 | grep -v "\[\]"
```

### "Rendered more hooks than during previous render"
```bash
# Check for conditional hooks
grep -rn "if.*use[A-Z]" src/
```
