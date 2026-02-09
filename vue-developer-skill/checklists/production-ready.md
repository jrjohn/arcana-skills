# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)
- [ ] **Tests pass** - `npx vitest run`
- [ ] **TypeScript compiles** - `npx vue-tsc --noEmit`
- [ ] **No placeholder code** - `grep -rn "NotImplemented\|TODO" src/`
- [ ] **No hardcoded secrets** - `grep -rn "password.*=.*\"\|secret.*=.*\"\|apiKey.*=.*\"" src/`
- [ ] **All DI bindings exist** - Check `core/di/container.ts`
- [ ] **Build succeeds** - `npx vite build`

### IMPORTANT (Should Pass)
- [ ] **Input validation** - Security validators on all user inputs
- [ ] **Error handling** - ErrorBoundary components configured
- [ ] **Logging** - Structured logging configured
- [ ] **i18n complete** - All 6 languages have translations

### RECOMMENDED (Nice to Have)
- [ ] **Rate limiting** - API rate limits configured
- [ ] **Caching** - Four-layer progressive cache enabled
- [ ] **Monitoring** - Analytics/error tracking
- [ ] **Health checks** - Health endpoint available

---

## Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| ViewModel Composables | 90%+ | ___ |
| Services | 85%+ | ___ |
| Repositories | 80%+ | ___ |
| Components | 60%+ | ___ |
| Validators | 95%+ | ___ |
| **Overall** | **95%** | ___ |

---

## Security Checklist

- [ ] JWT secret is from environment variable
- [ ] XSS prevention with HTML entity encoding
- [ ] SQL injection detection on user inputs
- [ ] Path traversal prevention on file operations
- [ ] URL validation with protocol whitelist
- [ ] CORS configured correctly
- [ ] Input sanitization (control character removal)
- [ ] Sensitive data not in logs
- [ ] HTTPS enforced in production
- [ ] No secrets in source code
- [ ] Environment variables validated on startup
