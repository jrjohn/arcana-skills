# Production Readiness Checklist

## Pre-Release Checklist

### 🔴 CRITICAL (Must Pass)

- [ ] **Build succeeds** - `xcodebuild -scheme [Scheme] build`
- [ ] **All tests pass** - `xcodebuild test -scheme [Scheme]`
- [ ] **No empty handlers** - `grep -rn "action:\s*{\s*}" Sources/`
- [ ] **Navigation complete** - All Route cases have view destinations
- [ ] **No placeholder views** - `grep -rn "PlaceholderView\|Coming Soon" Sources/`
- [ ] **No hardcoded secrets** - `grep -rn "api_key\|password\|secret" Sources/`
- [ ] **No fatalError in production code** - `grep -rn "fatalError" Sources/`

### 🟡 IMPORTANT (Should Pass)

- [ ] **Loading states** - All data views show ProgressView
- [ ] **Error states** - All views handle and display errors
- [ ] **Empty states** - All lists handle empty data
- [ ] **Offline support** - App works without network
- [ ] **Back navigation** - All views can navigate back
- [ ] **Input validation** - All forms validate input
- [ ] **Accessibility** - VoiceOver labels for interactive elements

### 🟢 RECOMMENDED (Nice to Have)

- [ ] **Animations** - View transitions are smooth
- [ ] **Pull-to-refresh** - Lists support refresh gesture
- [ ] **Skeleton loading** - Loading shows content shape
- [ ] **Dark mode** - App supports system appearance
- [ ] **iPad layout** - UI adapts to larger screens
- [ ] **Dynamic Type** - Text scales with user preferences

---

## Code Review Checklist

### Architecture
- [ ] No layer violations (Domain doesn't import Data/Presentation)
- [ ] Repository protocols in Domain/Repositories/
- [ ] Repository implementations in Data/Repositories/
- [ ] ViewModels use Input/Output/Effect pattern
- [ ] No business logic in Views

### State Management
- [ ] @Observable for ViewModel state
- [ ] Effect for one-time events
- [ ] State survives app backgrounding
- [ ] No memory leaks (proper Task cancellation)

### Error Handling
- [ ] All async calls wrapped in do-catch
- [ ] Errors mapped to user-friendly messages
- [ ] Auth errors redirect to login
- [ ] Retry mechanism for failed requests

### Performance
- [ ] No blocking calls on main thread
- [ ] Images loaded with AsyncImage or proper caching
- [ ] Lists use LazyVStack/LazyHStack
- [ ] Identifiable items for ForEach
- [ ] Minimize unnecessary view updates

### Security
- [ ] No hardcoded API keys
- [ ] Sensitive data uses Keychain
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
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' build -quiet && echo "✅ Build passed" || exit 1 && \

echo "2. Tests..." && \
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' -quiet && echo "✅ Tests passed" || echo "⚠️ Tests failed" && \

echo "3. Empty handlers..." && \
(grep -rqn "action:\s*{\s*}" Sources/ && echo "❌ Empty handlers found" || echo "✅ No empty handlers") && \

echo "4. Placeholder views..." && \
(grep -rqn "PlaceholderView\|Coming Soon\|即將推出" Sources/ && echo "❌ Placeholders found" || echo "✅ No placeholders") && \

echo "5. Hardcoded secrets..." && \
(grep -rqn "api_key.*=.*\"\|password.*=.*\"\|secret.*=.*\"" Sources/ && echo "❌ Hardcoded secrets found" || echo "✅ No hardcoded secrets") && \

echo "=== CHECK COMPLETE ==="
```

---

## Release Preparation

### Version Bump
```swift
// Update in project settings or Info.plist
CFBundleShortVersionString = "X.Y.Z"  // User-facing version
CFBundleVersion = "N"                  // Build number (increment each release)
```

### Build Release Archive
```bash
# Clean build folder
xcodebuild clean -scheme [YourScheme]

# Build archive for App Store
xcodebuild archive \
  -scheme [YourScheme] \
  -archivePath ./build/[AppName].xcarchive \
  -destination 'generic/platform=iOS'

# Export for App Store
xcodebuild -exportArchive \
  -archivePath ./build/[AppName].xcarchive \
  -exportPath ./build \
  -exportOptionsPlist ExportOptions.plist
```

### App Store Submission Checklist
- [ ] Screenshots for all required device sizes
- [ ] App icon in all required sizes
- [ ] Privacy policy URL
- [ ] App description and keywords
- [ ] Contact information
- [ ] Age rating questionnaire completed
