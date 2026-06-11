# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check for unimplemented methods
grep -rn "throw.*NotImplementedException\|TODO.*implement" src/

# 2. Check empty button handlers
grep -rn "Click=\"\"\|Command=\"{x:Null}\"" src/

# 3. Check NavGraph completeness
echo "NavGraph methods:" && grep -c "public void To\|public Task To" src/**/NavGraph.cs
echo "Pages registered:" && grep -c "typeof(.*Page)" src/**/NavGraph.cs
```

## 🚨 Layer Wiring Verification (CRITICAL)

```bash
# === VIEWMODEL → SERVICE → REPOSITORY PATTERN ===

# 4. 🚨 Check ViewModel should NOT inject Repository directly
echo "=== ViewModel→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "IRepository\|Repository" src/**/ViewModels/*.cs 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS ViewModels inject Repository directly!"; \
    echo "ViewModels should inject Service, not Repository."; \
    grep -rln "IRepository\|Repository" src/**/ViewModels/*.cs 2>/dev/null; \
else \
    echo "✅ All ViewModels correctly inject Service"; \
fi

# 5. 🚨 Check Service layer exists
echo "=== Service Layer Existence Check ===" && \
SERVICE_COUNT=$(find src -name "*Service.cs" -path "*/Services/*" 2>/dev/null | wc -l) && \
INTERFACE_COUNT=$(find src -name "I*Service.cs" -path "*/Services/*" 2>/dev/null | wc -l) && \
echo "Service interfaces (I*Service): $INTERFACE_COUNT" && \
echo "Service implementations: $SERVICE_COUNT" && \
if [ "$SERVICE_COUNT" -eq 0 ]; then \
    echo "❌ CRITICAL: No Service layer found! Architecture violation."; \
else \
    echo "✅ Service layer exists"; \
fi

# 6. 🚨 Check Service→Repository wiring
echo "=== Service→Repository Wiring Check ===" && \
echo "Repository methods called in Services:" && \
grep -roh "_repository\.[A-Za-z]*(\|repository\.[A-Za-z]*(" src/**/Services/*.cs 2>/dev/null | sort -u || echo "(no repository calls found)"
echo "Repository interface methods:" && \
grep -rh "[A-Za-z]* [A-Za-z]*(" src/**/Repositories/I*Repository.cs 2>/dev/null | grep -oE "[A-Za-z]+\(" | sort -u

# 7. 🚨 Verify ALL Service interfaces have implementations
echo "=== Service Interface/Implementation Parity ===" && \
INTERFACES=$(find src -name "I*Service.cs" -path "*/Services/*" 2>/dev/null | wc -l) && \
IMPLS=$(find src -name "*Service.cs" -path "*/Services/*" ! -name "I*" 2>/dev/null | wc -l) && \
echo "Service interfaces: $INTERFACES" && \
echo "Service implementations: $IMPLS" && \
if [ "$INTERFACES" -ne "$IMPLS" ]; then \
    echo "❌ MISMATCH! Missing $(($INTERFACES - $IMPLS)) Service implementations"; \
else \
    echo "✅ All Service interfaces have implementations"; \
fi

# 8. 🚨 Verify ALL Repository interfaces have implementations
echo "=== Repository Interface/Implementation Parity ===" && \
REPO_INTERFACES=$(find src -name "I*Repository.cs" 2>/dev/null | wc -l) && \
REPO_IMPLS=$(find src -name "*Repository.cs" ! -name "I*" 2>/dev/null | wc -l) && \
echo "Repository interfaces: $REPO_INTERFACES" && \
echo "Repository implementations: $REPO_IMPLS" && \
if [ "$REPO_INTERFACES" -ne "$REPO_IMPLS" ]; then \
    echo "❌ MISMATCH! Missing Repository implementations"; \
else \
    echo "✅ All Repository interfaces have implementations"; \
fi
```

## Navigation Verification

```bash
# 4. Check INavGraph vs NavGraph
echo "=== INavGraph Methods ===" && \
grep -rh "void To[A-Z]\|Task To[A-Z]" src/**/INavGraph.cs | grep -oE "To[A-Za-z]+" | sort -u
echo "=== NavGraph Implementations ===" && \
grep -rh "public.*void To[A-Z]\|public.*Task To[A-Z]" src/**/NavGraph.cs | grep -oE "To[A-Za-z]+" | sort -u

# 5. Check Effect subscriptions
echo "=== ViewModel Effects ===" && \
grep -rh "record.*Effect" src/**/ViewModels/*.cs
echo "=== Effect Handlers ===" && \
grep -rn "Fx.Subscribe" src/**/Views/*.cs
```

## Mock Data Verification

```bash
# 6. Check for empty collections
grep -rn "new List<>\|Enumerable.Empty\|Array.Empty" src/**/Repositories/*.cs && \
echo "⚠️ Found empty collections"

# 7. Check for null returns
grep -rn "return null" src/**/Repositories/*.cs && \
echo "⚠️ Found null returns"
```

## Build & Test Commands

```bash
# 8. Build
dotnet build

# 9. Run tests
dotnet test

# 10. Run with coverage
dotnet test --collect:"XPlat Code Coverage"
```

## Pre-PR Checklist

```bash
echo "=== PRE-PR VERIFICATION ===" && \
echo "1. Build..." && dotnet build -q && echo "✅ Passed" || echo "❌ Failed" && \
echo "2. Tests..." && dotnet test -q && echo "✅ Passed" || echo "❌ Failed" && \
echo "3. Placeholders..." && (grep -rqn "NotImplementedException" src/ && echo "⚠️ Found" || echo "✅ None") && \
echo "=== COMPLETE ==="
```
