# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check layer violations
grep -rn "import.*data" src/app/domain/ && echo "❌ Domain importing Data!"
grep -rn "import.*presentation" src/app/domain/ && echo "❌ Domain importing Presentation!"

# 2. Check interface implementations
echo "=== Repository Interfaces ===" && \
ls src/app/domain/repositories/*.repository.ts 2>/dev/null | wc -l
echo "=== Repository Implementations ===" && \
ls src/app/data/repositories/*.repository.impl.ts 2>/dev/null | wc -l

# 3. Check for unimplemented code
grep -rn "throw.*NotImplemented\|TODO.*implement" src/app/
```

## 🚨 Layer Wiring Verification (CRITICAL)

```bash
# === COMPONENT/VIEWMODEL → SERVICE → REPOSITORY PATTERN ===

# 4. 🚨 Check Component should NOT inject Repository directly
echo "=== Component→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "Repository" src/app/presentation/**/*.component.ts 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS Components inject Repository directly!"; \
    echo "Components should inject Service, not Repository."; \
    grep -rln "Repository" src/app/presentation/**/*.component.ts 2>/dev/null; \
else \
    echo "✅ All Components correctly inject Service"; \
fi

# 5. 🚨 Check ViewModel should NOT inject Repository directly (if using MVVM)
echo "=== ViewModel→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "Repository" src/app/presentation/**/*.viewmodel.ts 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS ViewModels inject Repository directly!"; \
    grep -rln "Repository" src/app/presentation/**/*.viewmodel.ts 2>/dev/null; \
else \
    echo "✅ All ViewModels correctly inject Service"; \
fi

# 6. 🚨 Check Service layer exists
echo "=== Service Layer Existence Check ===" && \
SERVICE_COUNT=$(find src/app -path "*/domain/services/*.service.ts" 2>/dev/null | wc -l) && \
IMPL_COUNT=$(find src/app -path "*/domain/services/*.service.impl.ts" -o -path "*/data/services/*.service.impl.ts" 2>/dev/null | wc -l) && \
echo "Service interfaces: $SERVICE_COUNT" && \
echo "Service implementations: $IMPL_COUNT" && \
if [ "$SERVICE_COUNT" -eq 0 ]; then \
    echo "❌ CRITICAL: No Service layer found! Architecture violation."; \
else \
    echo "✅ Service layer exists"; \
fi

# 7. 🚨 Verify ALL Service interfaces have implementations
echo "=== Service Interface/Implementation Parity ===" && \
INTERFACES=$(find src/app -path "*/domain/services/*.service.ts" ! -name "*.impl.ts" 2>/dev/null | wc -l) && \
IMPLS=$(find src/app -path "*/*.service.impl.ts" 2>/dev/null | wc -l) && \
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
# 4. Check Routes vs Components completeness
echo "=== Navigation Completeness ===" && \
ROUTES=$(grep -c "path:" src/app/app.routes.ts 2>/dev/null || echo 0) && \
COMPONENTS=$(grep -c "component:" src/app/app.routes.ts 2>/dev/null || echo 0) && \
echo "Routes defined: $ROUTES" && \
echo "Components registered: $COMPONENTS" && \
if [ "$ROUTES" -ne "$COMPONENTS" ]; then echo "❌ MISMATCH!"; fi

# 5. Check NavGraphService has all navigation methods
echo "=== NavGraphService Methods ===" && \
grep -rh "to[A-Z][a-zA-Z]*\(" src/app/core/services/nav-graph.service.ts | grep -oE "to[A-Z][a-zA-Z]*" | sort -u

# 6. Check empty click handlers
grep -rn "(click)=\"\"\|(click)=\"undefined\"" src/app/**/*.html && echo "⚠️ Empty click handlers found"

# 7. Check unwired @Output events (CRITICAL!)
echo "=== Component @Output Events ===" && \
grep -rh "@Output()" src/app/presentation/ | grep -oE "[a-zA-Z]+\s*=" | sed 's/\s*=//' | sort -u
```

## Mock Data Verification

```bash
# 8. Check for empty array returns
grep -rn "\[\]" src/app/data/repositories/*.repository.impl.ts && \
echo "⚠️ Found empty arrays - verify this is intentional"

# 9. Check for null/undefined returns
grep -rn "return null\|return undefined" src/app/data/repositories/*.repository.impl.ts && \
echo "⚠️ Found null/undefined returns - consider returning mock data"

# 10. Verify chart-related data has mock values
grep -rn "dailyData\|weeklyData\|chartData" src/app/data/repositories/ | grep -E "= \[\]|of\(\[\]\)"
```

## UI State Verification

```bash
# 11. Check for loading states
grep -L "isLoading\|loading" src/app/presentation/**/*.component.ts 2>/dev/null | \
head -5 && echo "(components may be missing loading state)"

# 12. Check for empty states
grep -l "ngFor\|*ngFor" src/app/presentation/**/*.html | \
xargs grep -L "empty\|Empty\|ngIf.*length" 2>/dev/null | head -5 && echo "(lists may be missing empty state)"

# 13. Check for error states
grep -L "error\|Error" src/app/presentation/**/*.component.ts 2>/dev/null | \
head -5 && echo "(components may be missing error state)"

# 14. Check for placeholder text
grep -rn "TODO\|Coming Soon\|即將推出\|Placeholder" src/app/presentation/ && \
echo "⚠️ Found placeholder text"
```

## Service→Repository Wiring

```bash
# 15. Check Service→Repository method calls
echo "=== Repository Methods Called in Services ===" && \
grep -roh "this\.[a-zA-Z]*Repository\.[a-zA-Z]*(" src/app/domain/services/*.ts | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/app/domain/repositories/*.repository.ts | grep -oE "[a-zA-Z]+\(" | sort -u

# 16. Verify ALL Repository interface methods have implementations
echo "=== Repository Interface Methods ===" && \
grep -rh "abstract\|[a-zA-Z]*\(" src/app/domain/repositories/*.repository.ts | grep -oE "[a-zA-Z]+\(" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/app/data/repositories/*.repository.impl.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

## Build & Test Commands

```bash
# 17. Quick build check
npm run build 2>&1 | tail -20

# 18. Run unit tests
npm run test -- --watch=false --browsers=ChromeHeadless

# 19. Run tests with coverage
npm run test -- --code-coverage --watch=false --browsers=ChromeHeadless

# 20. Run e2e tests
npm run e2e
```

## Pre-PR Checklist Commands

```bash
# Run all these before creating a PR
echo "=== PRE-PR VERIFICATION ===" && \

echo "1. Build check..." && \
npm run build --quiet && echo "✅ Build passed" || echo "❌ Build failed" && \

echo "2. Empty handlers..." && \
(grep -rqn "(click)=\"\"" src/app/ && echo "⚠️ Empty handlers found" || echo "✅ No empty handlers") && \

echo "3. Navigation wiring..." && \
ROUTES=$(grep -c "path:" src/app/app.routes.ts 2>/dev/null || echo 0) && \
COMPONENTS=$(grep -c "component:" src/app/app.routes.ts 2>/dev/null || echo 0) && \
([ "$ROUTES" -eq "$COMPONENTS" ] && echo "✅ Navigation complete" || echo "⚠️ Navigation mismatch: $ROUTES routes, $COMPONENTS components") && \

echo "4. Mock data..." && \
(grep -rqn "\[\]" src/app/data/repositories/*.repository.impl.ts && echo "⚠️ Empty arrays in repository" || echo "✅ No empty arrays") && \

echo "=== VERIFICATION COMPLETE ==="
```

## User Journey Flow Verification

```bash
# 21. Check login flow
echo "=== User Journey Flow ===" && \
LOGIN_ROUTE=$(grep -A5 "path: 'login'" src/app/app.routes.ts) && \
echo "Login route: $LOGIN_ROUTE"

# 22. Check onboarding flow
ONBOARDING=$(grep "onboarding\|Onboarding" src/app/app.routes.ts) && \
if [ -z "$ONBOARDING" ]; then echo "⚠️ Onboarding route not defined"; else echo "✅ Onboarding route exists"; fi

# 23. Check register to onboarding flow
REGISTER_NAV=$(grep -A5 "register\|Register" src/app/core/services/nav-graph.service.ts | grep "navigate\|router") && \
echo "Register navigates to: $REGISTER_NAV" && \
if echo "$REGISTER_NAV" | grep -q "dashboard\|Dashboard\|home\|Home"; then \
    echo "⚠️ WARNING: Register goes directly to Dashboard - Onboarding may be skipped!"; \
fi
```
