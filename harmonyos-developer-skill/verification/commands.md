# Verification Commands Reference

All verification commands for HarmonyOS development in one place.

## ArkTS Strict Mode Verification

```bash
# 1. Check for any/unknown types (MUST be empty)
grep -rn ": any\|: unknown\|as any\|as unknown" entry/src/main/ets/ | grep -v node_modules

# 2. Check for spread operators (MUST be empty)
grep -rn "\.\.\." entry/src/main/ets/ | grep -v node_modules | grep -v ".json"

# 3. Check for computed properties (MUST be empty)
grep -rn "\[.*\]:" entry/src/main/ets/ | grep -v "Array\|Map\|Set\|resultSet\|getColumnIndex"

# 4. Check for object literal constants (should use classes)
grep -rn "const.*=\s*{" entry/src/main/ets/ | grep -v "ValuesBucket\|StoreConfig\|HuksOptions\|WorkInfo"
```

## Architecture Verification

```bash
# 5. Check domain layer purity (MUST have zero SDK imports)
grep -rn "import.*@ohos\|import.*@kit\|import.*@system" entry/src/main/ets/domain/
# If ANY results -> VIOLATION: Domain layer must be pure

# 6. Check layer dependencies
echo "=== Data layer should NOT import Presentation ===" && \
grep -rn "import.*presentation\|import.*pages" entry/src/main/ets/data/ || echo "OK"

echo "=== Domain layer should NOT import Data or Presentation ===" && \
grep -rn "import.*data\|import.*presentation\|import.*pages\|import.*core" entry/src/main/ets/domain/ || echo "OK"

# 7. Check DI bindings completeness
echo "=== DI Bindings ===" && \
echo "Registered:" && \
grep -c "container.bind\|bindSingleton" entry/src/main/ets/core/di/*.ets && \
echo "ServiceIdentifiers:" && \
grep -c "static readonly" entry/src/main/ets/core/di/Container.ets
```

## Navigation Verification

```bash
# 8. Check routes registered in module.json5
echo "=== Routes in module.json5 ===" && \
grep -c "\"name\":" entry/src/main/module.json5 | head -5

# 9. Check NavigationRoutes constants vs actual page files
echo "=== NavigationRoutes defined ===" && \
grep -oh "'pages/[A-Za-z]*'" entry/src/main/ets/core/navigation/NavigationRoutes.ets | sort -u

echo "=== Page files exist ===" && \
ls entry/src/main/ets/pages/*.ets 2>/dev/null | sort
```

## Mock Data Verification

```bash
# 10. Check for empty arrays in repository stubs (MUST FIX)
grep -rn "new Array()" entry/src/main/ets/data/repository/ | grep -v "push\|length"

# 11. Check for undefined returns in repository
grep -rn "return undefined" entry/src/main/ets/data/repository/

# 12. Check sync status usage
echo "=== Sync Status in Repositories ===" && \
grep -rn "SyncStatus\." entry/src/main/ets/data/repository/ | head -20
```

## UI State Verification

```bash
# 13. Check for loading states in pages
grep -L "LoadingProgress\|isLoading\|Loading" entry/src/main/ets/pages/*.ets 2>/dev/null
# If ANY files listed -> pages may be missing loading state

# 14. Check for error states in pages
grep -L "error\|Error\|onRetry\|retry" entry/src/main/ets/pages/*.ets 2>/dev/null
# If ANY files listed -> pages may be missing error state

# 15. Check for empty click handlers
grep -rn "() => {}" entry/src/main/ets/pages/ entry/src/main/ets/presentation/
```

## Build and Test Commands

```bash
# 16. Build HAP package
hvigorw assembleHap --mode module -p product=default -p module=entry

# 17. Clean build
hvigorw clean && hvigorw assembleHap --mode module -p product=default -p module=entry

# 18. Install on device
hdc install entry/build/default/outputs/default/entry-default-signed.hap

# 19. Run all tests
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test

# 20. View device logs
hdc hilog | grep -i "arcana\|error\|exception"

# 21. Install dependencies
ohpm install

# 22. List connected devices
hdc list targets
```

## Pre-PR Checklist Commands

```bash
# Run all of these before creating a PR
echo "=== PRE-PR VERIFICATION ===" && \

echo "1. ArkTS strict mode..." && \
(grep -rqn ": any\|: unknown" entry/src/main/ets/ | grep -v node_modules && echo "FAIL: any/unknown" || echo "OK") && \
(grep -rn "\.\.\." entry/src/main/ets/ | grep -v node_modules | grep -qv .json && echo "FAIL: spread" || echo "OK") && \

echo "2. Domain purity..." && \
(grep -rqn "import.*@ohos\|import.*@kit" entry/src/main/ets/domain/ && echo "FAIL: SDK in domain" || echo "OK") && \

echo "3. Empty handlers..." && \
(grep -rqn "() => {}" entry/src/main/ets/pages/ && echo "WARNING: empty handlers" || echo "OK") && \

echo "4. Unimplemented methods..." && \
(grep -rqn "throw new Error\|NotImplemented\|TODO.*implement" entry/src/main/ets/ && echo "FAIL: unimplemented" || echo "OK") && \

echo "5. Build..." && \
hvigorw assembleHap --mode module -p product=default -p module=entry && echo "OK" || echo "FAIL" && \

echo "=== VERIFICATION COMPLETE ==="
```
