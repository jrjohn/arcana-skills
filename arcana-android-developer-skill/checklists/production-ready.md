# Production Readiness Checklist

## Pre-Release Checklist

### 🔴 CRITICAL (Must Pass)

- [ ] **Build succeeds** - `./gradlew assembleRelease`
- [ ] **All tests pass** - `./gradlew test connectedAndroidTest`
- [ ] **No empty handlers** - `grep -rn "onClick = { }" app/`
- [ ] **Navigation complete** - All NavRoutes have composable destinations
- [ ] **No placeholder screens** - `grep -rn "PlaceholderScreen\|Coming Soon" app/`
- [ ] **No hardcoded secrets** - `grep -rn "api_key\|password\|secret" app/`
- [ ] **ProGuard rules configured** - Check `proguard-rules.pro`

### 🟡 IMPORTANT (Should Pass)

- [ ] **Loading states** - All data screens show loading indicator
- [ ] **Error states** - All screens handle and display errors
- [ ] **Empty states** - All lists handle empty data
- [ ] **Offline support** - App works without network
- [ ] **Back navigation** - All screens can navigate back
- [ ] **Input validation** - All forms validate input
- [ ] **Accessibility** - Content descriptions for images

### 🟢 RECOMMENDED (Nice to Have)

- [ ] **Animations** - Screen transitions are smooth
- [ ] **Pull-to-refresh** - Lists support refresh gesture
- [ ] **Skeleton loading** - Loading shows content shape
- [ ] **Dark mode** - App supports system theme
- [ ] **Landscape mode** - UI adapts to orientation
- [ ] **Tablet layout** - Responsive for large screens

---

## Code Review Checklist

### Architecture
- [ ] No layer violations (Domain doesn't import Data/Presentation)
- [ ] Repository interfaces in domain/repository/
- [ ] Repository implementations in data/repository/
- [ ] ViewModels use Input/Output pattern
- [ ] No business logic in Composables

### State Management
- [ ] StateFlow for UI state
- [ ] SharedFlow for one-time effects
- [ ] State survives configuration change
- [ ] No memory leaks (proper scope)

### Error Handling
- [ ] All network calls wrapped in try-catch
- [ ] Errors mapped to user-friendly messages
- [ ] Auth errors redirect to login
- [ ] Retry mechanism for failed requests

### Performance
- [ ] No blocking calls on main thread
- [ ] Images loaded with proper library (Coil)
- [ ] Lists use LazyColumn/LazyRow
- [ ] Keys provided for list items
- [ ] No unnecessary recomposition

### Security
- [ ] No hardcoded API keys
- [ ] Sensitive data in encrypted storage
- [ ] Network calls use HTTPS
- [ ] Input sanitized before use
- [ ] No logging of sensitive data

---

## Verification Commands

```bash
# Run complete verification
echo "=== PRODUCTION READINESS CHECK ===" && \

# Critical
echo "1. Build..." && \
./gradlew assembleRelease --quiet && echo "✅ Build passed" || exit 1 && \

echo "2. Tests..." && \
./gradlew test --quiet && echo "✅ Tests passed" || echo "⚠️ Tests failed" && \

echo "3. Empty handlers..." && \
(grep -rqn "onClick = { }" app/src/main/java/ && echo "❌ Empty handlers found" || echo "✅ No empty handlers") && \

echo "4. Placeholder screens..." && \
(grep -rqn "PlaceholderScreen\|Coming Soon" app/src/main/java/ && echo "❌ Placeholders found" || echo "✅ No placeholders") && \

echo "5. Hardcoded secrets..." && \
(grep -rqn "api_key.*=.*\"\|password.*=.*\"\|secret.*=.*\"" app/src/main/java/ && echo "❌ Hardcoded secrets found" || echo "✅ No hardcoded secrets") && \

echo "=== CHECK COMPLETE ==="
```

---

## Release Preparation

### Version Bump
```gradle
// app/build.gradle.kts
android {
    defaultConfig {
        versionCode = X  // Increment for each release
        versionName = "X.Y.Z"  // Semantic versioning
    }
}
```

### Build Release APK/Bundle
```bash
# Clean build
./gradlew clean

# Build release bundle (for Play Store)
./gradlew bundleRelease

# Build release APK (for direct distribution)
./gradlew assembleRelease
```

### Sign Release
```bash
# Verify signing config in build.gradle.kts
# Never commit keystore password to version control
```
