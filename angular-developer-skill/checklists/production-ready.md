# Production Readiness Checklist

## Pre-Release Checklist

### 🔴 CRITICAL (Must Pass)

- [ ] **Build succeeds** - `npm run build -- --configuration production`
- [ ] **All tests pass** - `npm run test -- --watch=false`
- [ ] **No empty handlers** - `grep -rn "(click)=\"\"" src/app/`
- [ ] **Navigation complete** - All routes have component imports
- [ ] **No placeholder components** - `grep -rn "PlaceholderComponent\|Coming Soon" src/app/`
- [ ] **No hardcoded secrets** - `grep -rn "api_key\|password\|secret" src/app/`
- [ ] **No NotImplementedError** - `grep -rn "throw.*NotImplemented" src/app/`

### 🟡 IMPORTANT (Should Pass)

- [ ] **Loading states** - All data components show spinner
- [ ] **Error states** - All components handle and display errors
- [ ] **Empty states** - All lists handle empty data
- [ ] **Offline support** - App works without network (IndexedDB)
- [ ] **Back navigation** - All routes can navigate back
- [ ] **Input validation** - All forms validate input
- [ ] **Accessibility** - ARIA labels for interactive elements

### 🟢 RECOMMENDED (Nice to Have)

- [ ] **Animations** - Route transitions are smooth
- [ ] **Skeleton loading** - Loading shows content shape
- [ ] **Dark mode** - App supports system theme
- [ ] **Responsive design** - UI adapts to all screen sizes
- [ ] **PWA support** - Service worker configured
- [ ] **i18n** - Multi-language support

---

## Code Review Checklist

### Architecture
- [ ] No layer violations (Domain doesn't import Data/Presentation)
- [ ] Repository interfaces in domain/repositories/
- [ ] Repository implementations in data/repositories/
- [ ] ViewModels use Input/Output/Effect pattern
- [ ] No business logic in Components

### State Management
- [ ] Angular Signals for ViewModel state
- [ ] RxJS Subject for one-time effects
- [ ] State survives route navigation
- [ ] Proper subscription cleanup (takeUntilDestroyed)

### Error Handling
- [ ] All async calls wrapped in try-catch
- [ ] Errors mapped to user-friendly messages
- [ ] Auth errors redirect to login
- [ ] HTTP interceptor handles common errors

### Performance
- [ ] OnPush change detection on all components
- [ ] Virtual scrolling for large lists (cdk-virtual-scroll)
- [ ] Lazy loading for feature modules
- [ ] trackBy for ngFor loops
- [ ] Images use lazy loading

### Security
- [ ] No hardcoded API keys
- [ ] HTTP interceptor adds auth token
- [ ] Input sanitization for user content
- [ ] CSP headers configured
- [ ] No console.log in production

---

## Verification Commands

```bash
# Run complete verification
echo "=== PRODUCTION READINESS CHECK ===" && \

# Critical
echo "1. Build..." && \
npm run build -- --configuration production && echo "✅ Build passed" || exit 1 && \

echo "2. Tests..." && \
npm run test -- --watch=false --browsers=ChromeHeadless && echo "✅ Tests passed" || echo "⚠️ Tests failed" && \

echo "3. Empty handlers..." && \
(grep -rqn "(click)=\"\"" src/app/ && echo "❌ Empty handlers found" || echo "✅ No empty handlers") && \

echo "4. Placeholder components..." && \
(grep -rqn "PlaceholderComponent\|Coming Soon\|即將推出" src/app/ && echo "❌ Placeholders found" || echo "✅ No placeholders") && \

echo "5. Hardcoded secrets..." && \
(grep -rqn "api_key.*=.*'\|password.*=.*'\|secret.*=.*'" src/app/ && echo "❌ Hardcoded secrets found" || echo "✅ No hardcoded secrets") && \

echo "=== CHECK COMPLETE ==="
```

---

## Release Preparation

### Version Bump
```json
// package.json
{
  "version": "X.Y.Z"
}
```

### Build for Production
```bash
# Clean build folder
rm -rf dist/

# Build with production configuration
npm run build -- --configuration production

# Analyze bundle size
npm run build -- --configuration production --stats-json
npx webpack-bundle-analyzer dist/[app-name]/stats.json
```

### Environment Configuration
```typescript
// environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.production.com',
  // Never include secrets in frontend code
};
```

### Deployment Checklist
- [ ] Environment variables configured
- [ ] SSL certificate valid
- [ ] CDN configured for static assets
- [ ] Gzip/Brotli compression enabled
- [ ] Cache headers configured
- [ ] Error tracking (Sentry, etc.) configured
