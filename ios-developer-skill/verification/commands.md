# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check layer violations
grep -rn "import.*Data\." Sources/**/Domain/ && echo "❌ Domain importing Data!"
grep -rn "import.*Presentation\." Sources/**/Domain/ && echo "❌ Domain importing Presentation!"

# 2. Check interface implementations
echo "=== Repository Protocols ===" && \
ls Sources/**/Domain/Repositories/*.swift 2>/dev/null | wc -l
echo "=== Repository Implementations ===" && \
ls Sources/**/Data/Repositories/*Impl.swift 2>/dev/null | wc -l

# 3. Check for unimplemented code
grep -rn "fatalError\|TODO.*implement\|throw.*NotImplemented" Sources/
```

## Navigation Verification

```bash
# 4. Check Route vs NavigationRouter completeness
echo "=== Navigation Completeness ===" && \
ROUTES=$(grep -c "case\s" Sources/**/Route.swift 2>/dev/null || echo 0) && \
VIEWS=$(grep -c "destination:" Sources/**/NavigationRouter.swift 2>/dev/null || echo 0) && \
echo "Routes defined: $ROUTES" && \
echo "Views registered: $VIEWS" && \
if [ "$ROUTES" -ne "$VIEWS" ]; then echo "❌ MISMATCH!"; fi

# 5. Find orphan routes
grep "case\s" Sources/**/Route.swift | \
grep -oh "\.[a-zA-Z]*" | while read route; do \
    grep -q "$route" Sources/**/NavigationRouter.swift || \
    echo "⚠️ $route has no view destination"; \
done

# 6. Check empty button actions
grep -rn "action:\s*{\s*}\|Button.*{\s*}" Sources/**/Views/ && echo "⚠️ Empty button actions found"

# 7. Check unwired navigation closures (CRITICAL!)
grep -rn "onNavigate.*:\s*(\s*)\s*->\s*Void\s*=\s*{" Sources/**/Views/
```

## Mock Data Verification

```bash
# 8. Check for empty array returns
grep -rn "\[\]\|Array()" Sources/**/Repositories/*RepositoryImpl.swift && \
echo "⚠️ Found empty arrays - verify this is intentional"

# 9. Check for nil returns
grep -rn "return nil" Sources/**/Repositories/*RepositoryImpl.swift && \
echo "⚠️ Found nil returns - consider returning mock data"

# 10. Verify chart-related data has mock values
grep -rn "dailyData\|weeklyData\|chartData" Sources/**/Repositories/ | grep -E "= \[\]|\.init\(\)"
```

## UI State Verification

```bash
# 11. Check for loading states
grep -L "isLoading\|ProgressView" Sources/**/Views/*.swift 2>/dev/null | \
head -5 && echo "(views may be missing loading state)"

# 12. Check for empty states
grep -l "ForEach\|List" Sources/**/Views/*.swift | \
xargs grep -L "empty\|Empty" 2>/dev/null | head -5 && echo "(lists may be missing empty state)"

# 13. Check for error states
grep -L "error\|Error" Sources/**/Views/*.swift 2>/dev/null | \
head -5 && echo "(views may be missing error state)"

# 14. Check for placeholder text
grep -rn "TODO\|Coming Soon\|即將推出\|Placeholder" Sources/**/Views/ && \
echo "⚠️ Found placeholder text"
```

## Service→Repository Wiring

```bash
# 15. Check Service→Repository method calls
echo "=== Repository Methods Called in Services ===" && \
grep -roh "repository\.[a-zA-Z]*(" Sources/**/Services/*.swift | sort -u
echo "=== Repository Protocol Methods ===" && \
grep -rh "func [a-zA-Z]*(" Sources/**/Domain/Repositories/*Repository.swift | grep -oE "func [a-zA-Z]+\(" | sort -u

# 16. Verify ALL Repository protocol methods have implementations
echo "=== Repository Protocol Methods ===" && \
grep -rh "func " Sources/**/Domain/Repositories/*Repository.swift | grep -oE "func [a-zA-Z]+" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "func " Sources/**/Data/Repositories/*RepositoryImpl.swift | grep -oE "func [a-zA-Z]+" | sort -u
```

## Build & Test Commands

```bash
# 17. Quick build check
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' build 2>&1 | tail -20

# 18. Run unit tests
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15'

# 19. Run tests with coverage
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' -enableCodeCoverage YES
```

## Pre-PR Checklist Commands

```bash
# Run all these before creating a PR
echo "=== PRE-PR VERIFICATION ===" && \

echo "1. Build check..." && \
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' build -quiet && echo "✅ Build passed" || echo "❌ Build failed" && \

echo "2. Empty handlers..." && \
(grep -rqn "action:\s*{\s*}" Sources/**/Views/ && echo "⚠️ Empty handlers found" || echo "✅ No empty handlers") && \

echo "3. Navigation wiring..." && \
ROUTES=$(grep -c "case\s" Sources/**/Route.swift 2>/dev/null || echo 0) && \
VIEWS=$(grep -c "destination:" Sources/**/NavigationRouter.swift 2>/dev/null || echo 0) && \
([ "$ROUTES" -eq "$VIEWS" ] && echo "✅ Navigation complete" || echo "⚠️ Navigation mismatch: $ROUTES routes, $VIEWS views") && \

echo "4. Mock data..." && \
(grep -rqn "\[\]" Sources/**/Repositories/*RepositoryImpl.swift && echo "⚠️ Empty arrays in repository" || echo "✅ No empty arrays") && \

echo "=== VERIFICATION COMPLETE ==="
```

## User Journey Flow Verification

```bash
# 20. Check login flow
echo "=== User Journey Flow ===" && \
LOGIN_NAV=$(grep -A5 "case .login:" Sources/**/NavigationRouter.swift | grep "navigate\|destination") && \
echo "Login navigates to: $LOGIN_NAV"

# 21. Check onboarding flow
ONBOARDING=$(grep "onboarding\|Onboarding" Sources/**/Route.swift) && \
if [ -z "$ONBOARDING" ]; then echo "⚠️ Onboarding route not defined"; else echo "✅ Onboarding route exists"; fi

# 22. Check register to onboarding flow
REGISTER_NAV=$(grep -A5 "onRegisterSuccess" Sources/**/NavigationRouter.swift | grep "navigate") && \
echo "Register navigates to: $REGISTER_NAV" && \
if echo "$REGISTER_NAV" | grep -q "dashboard\|Dashboard\|home\|Home"; then \
    echo "⚠️ WARNING: Register goes directly to Dashboard - Onboarding may be skipped!"; \
fi
```
