# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)
- [ ] **Tests pass** - `npm test`
- [ ] **TypeScript compiles** - `npm run type-check`
- [ ] **No placeholder code** - `grep -rn "NotImplemented\|TODO" src/`
- [ ] **No hardcoded secrets** - `grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"" src/`
- [ ] **All repository bindings exist** - Check RepositoryProvider.tsx
- [ ] **Build succeeds** - `npm run build`

### IMPORTANT (Should Pass)
- [ ] **Input validation** - Zod/Yup schemas for forms
- [ ] **Error handling** - Error boundaries configured
- [ ] **Logging** - Structured logging configured
- [ ] **API documentation** - OpenAPI/Swagger enabled

### RECOMMENDED (Nice to Have)
- [ ] **Rate limiting** - API rate limits configured
- [ ] **Caching** - Four-layer cache enabled
- [ ] **Monitoring** - Analytics/error tracking
- [ ] **Health checks** - Health endpoint available

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| ViewModel Hooks | 90%+ | ___ |
| Services | 85%+ | ___ |
| Repositories | 80%+ | ___ |
| Components | 60%+ | ___ |
| **Overall** | **87%** | ___ |

---

## API Wiring Verification

### Component → ViewModel Wiring
```bash
# List ViewModel hooks used in components
grep -rh "useViewModel\|use.*ViewModel" src/presentation/**/*.tsx | sort -u

# List ViewModel hooks defined
grep -rh "export function use.*ViewModel" src/presentation/**/*.ts | sort -u

# Every hook used MUST exist!
```

### Service → Repository Wiring
```bash
# List repository methods called in services
grep -roh "this\..*Repository\.[a-zA-Z]*(" src/domain/services/*.ts | sort -u

# List repository interface methods
grep -rh "[a-zA-Z]*\(" src/domain/repositories/*.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

### DI Container Bindings
```bash
# List all repository providers
grep -rn "useValue\|useClass" src/core/providers/*.tsx

# List all repository hooks
grep -rn "use.*Repository" src/core/hooks/*.ts
```

---

## Security Checklist

- [ ] JWT secret is from environment variable
- [ ] Password hashing uses bcrypt with cost >= 10
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevention with input sanitization (DOMPurify)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Sensitive data not in logs
- [ ] HTTPS enforced in production
- [ ] No secrets in source code
- [ ] Environment variables validated on startup

---

## Performance Checklist

- [ ] React.memo on presentational components
- [ ] useMemo/useCallback for expensive computations
- [ ] Virtual scrolling for large lists (react-window)
- [ ] Lazy loading for routes (React.lazy)
- [ ] Code splitting configured
- [ ] Image optimization
- [ ] Bundle size analyzed (< 500KB initial)
- [ ] Four-layer caching implemented
- [ ] No N+1 API calls
- [ ] Response compression enabled

---

## Deployment Checklist

### Environment Variables
```bash
# Required
VITE_API_URL=
VITE_WS_URL=
VITE_ENV=production

# Optional
VITE_SENTRY_DSN=
VITE_GA_ID=
VITE_LOG_LEVEL=info
```

### Build Verification
```bash
# Clean build
rm -rf dist node_modules/.vite
npm install
npm run build

# Verify bundle size
du -sh dist/

# Preview production build
npm run preview
```

### Docker
```bash
# Build
docker build -t arcana-react:X.Y.Z .

# Test locally
docker run -p 3000:80 arcana-react:X.Y.Z

# Push
docker push arcana-react:X.Y.Z
```

### Kubernetes
```bash
# Apply manifests
kubectl apply -f deploy/k8s/

# Verify
kubectl get pods -l app=arcana-react
kubectl logs -f deployment/arcana-react
```

---

## Monitoring Checklist

- [ ] Error tracking configured (Sentry)
- [ ] Performance monitoring (Web Vitals)
- [ ] Analytics configured (Google Analytics/Mixpanel)
- [ ] Log aggregation configured
- [ ] Alerting rules defined
- [ ] Uptime monitoring

---

## Code Quality Checks

### Lint and Format
```bash
# ESLint
npm run lint

# Prettier
npm run format:check

# TypeScript strict mode
npm run type-check
```

### Bundle Analysis
```bash
# Analyze bundle
npm run build -- --analyze

# Check for duplicate dependencies
npx depcheck
```

### Dependency Audit
```bash
# Security audit
npm audit

# Update dependencies
npm update

# Check outdated
npm outdated
```

---

## Release Commands

```bash
# Run all checks
npm run lint
npm run type-check
npm test -- --coverage
npm run build

# Version bump
npm version patch|minor|major

# Create release
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z

# Docker
docker build -t arcana-react:X.Y.Z .
docker push arcana-react:X.Y.Z

# Deploy (Kubernetes)
kubectl set image deployment/arcana-react arcana-react=arcana-react:X.Y.Z
```

---

## Post-Deployment Verification

1. [ ] Application loads without errors
2. [ ] Can authenticate (login endpoint)
3. [ ] Can perform CRUD operations
4. [ ] Navigation works correctly
5. [ ] Forms validate and submit
6. [ ] Error boundaries catch errors gracefully
7. [ ] No console errors in production
8. [ ] Performance metrics within targets
9. [ ] Analytics events firing
10. [ ] Error tracking receiving events

---

## Rollback Procedure

```bash
# Kubernetes rollback
kubectl rollout undo deployment/arcana-react

# Verify rollback
kubectl rollout status deployment/arcana-react

# Check previous versions
kubectl rollout history deployment/arcana-react
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
SECRETS=$(grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"" src/ || true)
if [ -n "$SECRETS" ]; then
    echo "WARNING: Possible hardcoded secrets:"
    echo "$SECRETS"
fi

echo "6. Checking for empty returns..."
EMPTY=$(grep -rn "return \[\]\|= \[\]" src/data/repositories/*.impl.ts || true)
if [ -n "$EMPTY" ]; then
    echo "WARNING: Found empty array returns:"
    echo "$EMPTY"
fi

echo "7. Building..."
npm run build

echo "8. Bundle size check..."
du -sh dist/

echo "=== All Checks Passed ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`

---

## Accessibility Checklist

- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Focus management for modals/dialogs
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader compatibility tested
- [ ] Skip links for navigation
- [ ] ARIA labels where needed

---

## Internationalization Checklist

- [ ] All user-facing strings use i18n
- [ ] Date/time formatting localized
- [ ] Number formatting localized
- [ ] RTL layout support (if needed)
- [ ] Language switcher works
- [ ] Default language fallback configured
- [ ] Translation files complete for all languages
