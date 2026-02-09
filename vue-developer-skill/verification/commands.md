# Verification Commands

Quick reference for diagnosing common issues in Arcana Vue projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Empty response | `grep -rn "= \[\]\|return \[\]" src/data/repositories/*.impl.ts` | Empty |
| Build error | `npx vue-tsc --noEmit` | No errors |
| Navigation crash | Compare router paths vs component imports | Match |
| DI error | Check `core/di/container.ts` bindings and tokens | All bound |
| Type error | `npx vue-tsc --noEmit` | No errors |
| Reactivity lost | `grep -rn "toRefs\|toRef" src/` | Check destructuring |

---

## 1. Code Quality Checks

### Check for unimplemented methods
```bash
# Must return empty for production-ready code
grep -rn "throw new Error.*NotImplemented\|TODO.*implement\|// TODO" src/
```

### Check for empty handlers
```bash
grep -rn "@click=\"\"\|@click=\"undefined\"\|@change=\"\"" src/
```

### TypeScript type checking
```bash
npx vue-tsc --noEmit
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
grep -c "path:" src/router/*.ts 2>/dev/null || echo 0

echo "Components imported:"
grep -c "component:" src/router/*.ts 2>/dev/null || echo 0
```

### Check for placeholder components
```bash
grep -rn "PlaceholderComponent\|Coming Soon\|NotImplemented" src/
```

### Verify async component loading
```bash
grep -rn "() => import(" src/router/
```

---

## 3. ViewModel & Composable Verification

### ViewModel composables defined
```bash
echo "=== ViewModel Composables Defined ==="
grep -rh "export function use.*ViewModel" src/presentation/view-models/*.ts | sort -u
```

### ViewModel composables used in components
```bash
echo "=== ViewModel Composables Used ==="
grep -rh "use.*ViewModel()" src/presentation/features/**/*.vue | sort -u
```

### Check for missing effect handlers
```bash
echo "=== Effects not handled ==="
grep -rn "onEffect\|emitEffect" src/presentation/**/*.vue | grep -v "onEffect("
```

---

## 4. DI Container Verification

### Check DI tokens defined
```bash
echo "=== TOKENS Defined ==="
grep -rh "Symbol.for" src/core/di/tokens.ts | sort -u
```

### Check DI bindings
```bash
echo "=== Container Bindings ==="
grep -rh "container.bind" src/core/di/container.ts | sort -u
```

### Check useInject usage
```bash
echo "=== useInject Calls ==="
grep -rh "useInject<" src/ | sort -u
```

---

## 5. Repository Verification

### Repository interface methods
```bash
echo "=== Repository Interface Methods ==="
grep -rh "[a-zA-Z]*(" src/domain/services/*repository*.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

### Check for empty array returns
```bash
grep -rn "= \[\]\|return \[\]" src/data/repositories/*.impl.ts
```

### Check mock data quality
```bash
grep -rn "= \[\]\|return \[\]" src/data/repositories/mock/
```

---

## 6. Security Checks

### Check for hardcoded secrets
```bash
grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"\|token.*=.*\"" src/
```

### Check for console.log in production code
```bash
grep -rn "console\.log\|console\.error\|console\.warn" src/ --include="*.ts" --include="*.vue" | grep -v "test\|spec\|__tests__"
```

---

## 7. Test Verification

### Run all tests
```bash
npx vitest run
```

### Run with coverage
```bash
npx vitest run --coverage
```

### Run specific test file
```bash
npx vitest run src/__tests__/useLoginViewModel.test.ts
```

---

## 8. Build Verification

### TypeScript compile
```bash
npx vue-tsc --noEmit
```

### Production build
```bash
npx vite build
```

### Analyze bundle size
```bash
npx vite-bundle-visualizer
```

---

## 9. Complete Verification Script

```bash
#!/bin/bash
set -e

echo "=== Running Complete Verification ==="

echo "1. TypeScript Check..."
npx vue-tsc --noEmit

echo "2. Lint Check..."
npm run lint

echo "3. Tests..."
npx vitest run --coverage

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

echo "6. Checking for empty array returns..."
EMPTY_ARRAYS=$(grep -rn "return \[\]\|= \[\]" src/data/repositories/*.impl.ts || true)
if [ -n "$EMPTY_ARRAYS" ]; then
    echo "WARNING: Found empty array returns:"
    echo "$EMPTY_ARRAYS"
fi

echo "7. Building..."
npx vite build

echo "8. Bundle size check..."
du -sh dist/

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`
