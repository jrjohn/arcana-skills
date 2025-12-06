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
