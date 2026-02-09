# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)

- [ ] **Build succeeds** - `hvigorw assembleHap --mode module -p product=default -p module=entry`
- [ ] **All tests pass** - `hdc shell aa test -b com.example.app -m entry_test`
- [ ] **No ArkTS violations** - `grep -rn ": any\|: unknown" entry/src/main/ets/`
- [ ] **No spread operators** - `grep -rn "\.\.\." entry/src/main/ets/ | grep -v node_modules`
- [ ] **No empty handlers** - `grep -rn "() => {}" entry/src/main/ets/pages/`
- [ ] **Navigation complete** - All routes registered in module.json5 router_map
- [ ] **No placeholder pages** - `grep -rn "PlaceholderPage\|Coming Soon\|TODO" entry/src/main/ets/pages/`
- [ ] **No hardcoded secrets** - `grep -rn "api_key\|password\|secret" entry/src/main/ets/`
- [ ] **DI bindings complete** - All services and repositories registered
- [ ] **Sync status tracked** - All data mutations set SyncStatus

### IMPORTANT (Should Pass)

- [ ] **Loading states** - All data pages show LoadingProgress
- [ ] **Error states** - All pages handle and display errors with retry
- [ ] **Empty states** - All lists handle empty data with guidance
- [ ] **Offline support** - App works without network (reads from local DB)
- [ ] **Back navigation** - All pages can navigate back
- [ ] **Input validation** - All forms validate before submit
- [ ] **i18n strings** - All user-facing text uses $r() resource references
- [ ] **Result<T,E> usage** - No throw for business logic errors

### RECOMMENDED (Nice to Have)

- [ ] **Animations** - Page transitions are smooth
- [ ] **Pull-to-refresh** - Lists support Refresh component
- [ ] **Skeleton loading** - Loading shows content placeholder shape
- [ ] **Dark mode** - App supports system theme via design tokens
- [ ] **HUKS encryption** - Sensitive data encrypted at rest
- [ ] **WorkScheduler** - Background sync configured
- [ ] **Accessibility** - Labels for all interactive elements

---

## Code Review Checklist

### Architecture
- [ ] No layer violations (Domain has zero SDK imports)
- [ ] Repository interfaces in domain/repository/
- [ ] Repository implementations in data/repository/
- [ ] ViewModels use Input/Output/Effect pattern
- [ ] No business logic in @Component pages
- [ ] All injectables registered in DI container

### State Management
- [ ] @State for local reactive state in pages
- [ ] Factory methods for immutable Output updates
- [ ] Effect callback for one-time events
- [ ] State survives page lifecycle (aboutToAppear/aboutToDisappear)

### Error Handling
- [ ] All async calls return Result<T, AppError>
- [ ] Errors mapped to user-friendly messages
- [ ] Auth errors trigger re-login flow
- [ ] Retry mechanism for network failures
- [ ] No uncaught Promise rejections

### Performance
- [ ] LazyForEach for lists with 20+ items
- [ ] LRU cache for frequently accessed data
- [ ] Images loaded with proper sizing
- [ ] Minimal @State variables (avoid unnecessary re-renders)
- [ ] RelationalStore queries use indexes

### Security
- [ ] HUKS for sensitive data encryption
- [ ] No hardcoded API keys or tokens
- [ ] Input sanitized before database queries
- [ ] HTTPS for all network requests
- [ ] Auth tokens stored via SecurityService

---

## Verification Commands

```bash
# Run complete verification
echo "=== PRODUCTION READINESS CHECK ===" && \

echo "1. Build..." && \
hvigorw assembleHap --mode module -p product=default -p module=entry && \
echo "Build passed" || echo "Build FAILED" && \

echo "2. ArkTS strict mode..." && \
(grep -rqn ": any\|: unknown" entry/src/main/ets/ && echo "VIOLATION: any/unknown found" || echo "OK: No any/unknown") && \
(grep -rn "\.\.\." entry/src/main/ets/ | grep -v node_modules | grep -qv .json && echo "VIOLATION: spread operators found" || echo "OK: No spread operators") && \

echo "3. Empty handlers..." && \
(grep -rqn "() => {}" entry/src/main/ets/pages/ && echo "WARNING: Empty handlers found" || echo "OK: No empty handlers") && \

echo "4. Placeholder pages..." && \
(grep -rqn "PlaceholderPage\|Coming Soon" entry/src/main/ets/pages/ && echo "VIOLATION: Placeholders found" || echo "OK: No placeholders") && \

echo "5. Hardcoded secrets..." && \
(grep -rqn "api_key.*=.*'\|password.*=.*'\|secret.*=.*'" entry/src/main/ets/ && echo "VIOLATION: Hardcoded secrets" || echo "OK: No hardcoded secrets") && \

echo "=== CHECK COMPLETE ==="
```
