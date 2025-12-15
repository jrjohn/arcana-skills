# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check layer violations
grep -rn "import.*data\." app/src/main/java/**/domain/ && echo "❌ Domain importing Data!"
grep -rn "import.*presentation\." app/src/main/java/**/domain/ && echo "❌ Domain importing Presentation!"

# 2. Check interface implementations
echo "=== Repository Interfaces ===" && \
ls app/src/main/java/**/domain/repository/*.kt 2>/dev/null | wc -l
echo "=== Repository Implementations ===" && \
ls app/src/main/java/**/data/repository/*Impl.kt 2>/dev/null | wc -l

# 3. Check Hilt bindings
grep -rn "@Binds" app/src/main/java/**/di/*.kt | wc -l
```

## 🚨 Layer Wiring Verification (CRITICAL)

```bash
# === VIEWMODEL → SERVICE → REPOSITORY PATTERN ===

# 4. 🚨 Check ViewModel should NOT inject Repository directly
echo "=== ViewModel→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "Repository" app/src/main/java/**/ui/screens/**/*ViewModel.kt 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS ViewModels inject Repository directly!"; \
    echo "ViewModels should inject Service, not Repository."; \
    grep -rln "Repository" app/src/main/java/**/ui/screens/**/*ViewModel.kt 2>/dev/null; \
else \
    echo "✅ All ViewModels correctly inject Service"; \
fi

# 5. 🚨 Check Service layer exists
echo "=== Service Layer Existence Check ===" && \
SERVICE_DIR="app/src/main/java/**/domain/service" && \
SERVICE_COUNT=$(find app/src/main/java -path "*/domain/service/*Service.kt" 2>/dev/null | wc -l) && \
IMPL_COUNT=$(find app/src/main/java -path "*/domain/service/*ServiceImpl.kt" 2>/dev/null | wc -l) && \
echo "Service interfaces: $SERVICE_COUNT" && \
echo "Service implementations: $IMPL_COUNT" && \
if [ "$SERVICE_COUNT" -eq 0 ]; then \
    echo "❌ CRITICAL: No Service layer found! Architecture violation."; \
else \
    echo "✅ Service layer exists"; \
fi

# 6. 🚨 Check Service→Repository wiring
echo "=== Service→Repository Wiring Check ===" && \
echo "Repository methods called in Services:" && \
grep -roh "repository\.[a-zA-Z]*(" app/src/main/java/**/domain/service/*.kt 2>/dev/null | sort -u || echo "(no services found)"
echo "Repository interface methods:" && \
grep -rh "suspend fun [a-zA-Z]*(\|fun [a-zA-Z]*(" app/src/main/java/**/domain/repository/*.kt 2>/dev/null | grep -oE "fun [a-zA-Z]+\(" | sort -u

# 7. 🚨 Verify ALL Service interfaces have implementations
echo "=== Service Interface/Implementation Parity ===" && \
INTERFACES=$(find app/src/main/java -path "*/domain/service/*Service.kt" ! -name "*Impl.kt" 2>/dev/null | wc -l) && \
IMPLS=$(find app/src/main/java -path "*/domain/service/*ServiceImpl.kt" 2>/dev/null | wc -l) && \
echo "Service interfaces: $INTERFACES" && \
echo "Service implementations: $IMPLS" && \
if [ "$INTERFACES" -ne "$IMPLS" ]; then \
    echo "❌ MISMATCH! Missing $(($INTERFACES - $IMPLS)) ServiceImpl"; \
else \
    echo "✅ All Service interfaces have implementations"; \
fi
```

## Navigation Verification

```bash
# 4. Check NavRoutes vs NavGraph completeness
echo "=== Navigation Completeness ===" && \
ROUTES=$(grep -c "data object" app/src/main/java/**/nav/NavRoutes.kt) && \
COMPOSABLES=$(grep -c "composable(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt) && \
echo "Routes defined: $ROUTES" && \
echo "Composables registered: $COMPOSABLES" && \
if [ "$ROUTES" -ne "$COMPOSABLES" ]; then echo "❌ MISMATCH!"; fi

# 5. Find orphan routes
grep "data object" app/src/main/java/**/nav/NavRoutes.kt | \
grep -oh "[A-Z][a-zA-Z]*" | while read route; do \
    grep -q "NavRoutes.$route" app/src/main/java/**/nav/*NavGraph.kt || \
    echo "⚠️ $route has no composable destination"; \
done

# 6. Check empty click handlers
grep -rn "onClick = { }" app/src/main/java/**/ui/ && echo "⚠️ Empty click handlers found"
grep -rn "onClick = { /\*" app/src/main/java/**/ui/ && echo "⚠️ TODO click handlers found"
```

## Mock Data Verification

```bash
# 7. Check for empty list returns
grep -rn "emptyList()" app/src/main/java/**/data/repository/*RepositoryImpl.kt && \
echo "⚠️ Found emptyList() - verify this is intentional"

# 8. Check for null returns
grep -rn "return null" app/src/main/java/**/data/repository/*RepositoryImpl.kt && \
echo "⚠️ Found null returns - consider returning mock data"

# 9. Check ID consistency across repositories
echo "=== Entity IDs across Repositories ===" && \
grep -oh "id = \"[a-z_]*[0-9]*\"" app/src/main/java/**/data/repository/*.kt | sort -u
```

## UI State Verification

```bash
# 10. Check for loading states
grep -L "Loading\|isLoading\|CircularProgress" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | \
head -5 && echo "(screens may be missing loading state)"

# 11. Check for empty states
grep -l "LazyColumn\|LazyRow" app/src/main/java/**/ui/screens/*.kt | \
xargs grep -L "empty\|Empty" 2>/dev/null | head -5 && echo "(lists may be missing empty state)"

# 12. Check for error states
grep -L "Error\|error" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | \
head -5 && echo "(screens may be missing error state)"

# 13. Check for placeholder text
grep -rn "Coming Soon\|TODO\|Placeholder" app/src/main/java/**/ui/ && \
echo "⚠️ Found placeholder text"
```

## User Journey Verification

```bash
# 14. Check onboarding flow
echo "=== User Journey Flow ===" && \
REGISTER_NAV=$(grep -A5 "onRegisterSuccess" app/src/main/java/**/nav/*NavGraph.kt | grep "navigate(") && \
echo "Register navigates to: $REGISTER_NAV" && \
if echo "$REGISTER_NAV" | grep -q "Dashboard"; then \
    echo "⚠️ WARNING: Register goes directly to Dashboard - Onboarding may be skipped!"; \
fi

# 15. Check login flow
LOGIN_NAV=$(grep -A5 "onLoginSuccess" app/src/main/java/**/nav/*NavGraph.kt | grep "navigate(") && \
echo "Login navigates to: $LOGIN_NAV"

# 16. Check onboarding registration
grep "Onboarding" app/src/main/java/**/nav/NavRoutes.kt || \
echo "⚠️ Onboarding route not defined"
```

## Build & Test Commands

```bash
# 17. Quick build check
./gradlew assembleDebug 2>&1 | tail -20

# 18. Run unit tests
./gradlew test

# 19. Run all verification at once
./gradlew assembleDebug && \
echo "=== Build passed, checking code ===" && \
grep -rn "emptyList()" app/src/main/java/**/data/repository/*RepositoryImpl.kt | head -5 && \
grep -rn "onClick = { }" app/src/main/java/**/ui/ | head -5 && \
echo "=== Verification complete ==="
```

## Pre-PR Checklist Commands

```bash
# Run all these before creating a PR
echo "=== PRE-PR VERIFICATION ===" && \

echo "1. Build check..." && \
./gradlew assembleDebug --quiet && echo "✅ Build passed" || echo "❌ Build failed" && \

echo "2. Empty handlers..." && \
(grep -rqn "onClick = { }" app/src/main/java/**/ui/ && echo "⚠️ Empty handlers found" || echo "✅ No empty handlers") && \

echo "3. Navigation wiring..." && \
ROUTES=$(grep -c "data object" app/src/main/java/**/nav/NavRoutes.kt 2>/dev/null || echo 0) && \
COMPOSABLES=$(grep -c "composable(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt 2>/dev/null || echo 0) && \
([ "$ROUTES" -eq "$COMPOSABLES" ] && echo "✅ Navigation complete" || echo "⚠️ Navigation mismatch: $ROUTES routes, $COMPOSABLES composables") && \

echo "4. Mock data..." && \
(grep -rqn "emptyList()" app/src/main/java/**/data/repository/*RepositoryImpl.kt && echo "⚠️ Empty lists in repository" || echo "✅ No empty lists") && \

echo "=== VERIFICATION COMPLETE ==="
```
