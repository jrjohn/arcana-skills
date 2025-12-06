# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check layer violations
grep -rn "import.*controller" src/main/java/**/service/ && echo "❌ Service importing Controller!"
grep -rn "import.*controller" src/main/java/**/repository/ && echo "❌ Repository importing Controller!"

# 2. Check interface implementations
echo "=== Repository Interfaces ===" && \
ls src/main/java/**/repository/*Repository.java 2>/dev/null | wc -l
echo "=== Repository Implementations ===" && \
ls src/main/java/**/repository/*RepositoryImpl.java 2>/dev/null | wc -l

# 3. Check for unimplemented code
grep -rn "throw.*UnsupportedOperationException\|TODO.*implement\|throw.*NotImplementedException" src/main/java/
```

## 🚨 Layer Wiring Verification (CRITICAL)

```bash
# === CONTROLLER → SERVICE → REPOSITORY PATTERN ===

# 4. 🚨 Check Controller should NOT inject Repository directly
echo "=== Controller→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "Repository" src/main/java/**/controller/*.java 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS Controllers inject Repository directly!"; \
    echo "Controllers should inject Service, not Repository."; \
    grep -rln "Repository" src/main/java/**/controller/*.java 2>/dev/null; \
else \
    echo "✅ All Controllers correctly inject Service"; \
fi

# 5. 🚨 Check Service layer exists
echo "=== Service Layer Existence Check ===" && \
SERVICE_COUNT=$(find src/main/java -name "*Service.java" -path "*/service/*" 2>/dev/null | wc -l) && \
IMPL_COUNT=$(find src/main/java -name "*ServiceImpl.java" -path "*/service/*" 2>/dev/null | wc -l) && \
echo "Service interfaces: $SERVICE_COUNT" && \
echo "Service implementations: $IMPL_COUNT" && \
if [ "$SERVICE_COUNT" -eq 0 ]; then \
    echo "❌ CRITICAL: No Service layer found! Architecture violation."; \
else \
    echo "✅ Service layer exists"; \
fi

# 6. 🚨 Verify ALL Service interfaces have implementations
echo "=== Service Interface/Implementation Parity ===" && \
INTERFACES=$(find src/main/java -name "*Service.java" -path "*/service/*" ! -name "*Impl.java" 2>/dev/null | wc -l) && \
IMPLS=$(find src/main/java -name "*ServiceImpl.java" 2>/dev/null | wc -l) && \
echo "Service interfaces: $INTERFACES" && \
echo "Service implementations: $IMPLS" && \
if [ "$INTERFACES" -ne "$IMPLS" ]; then \
    echo "❌ MISMATCH! Missing $(($INTERFACES - $IMPLS)) ServiceImpl"; \
else \
    echo "✅ All Service interfaces have implementations"; \
fi
```

## API Endpoint Verification

```bash
# 4. Check REST endpoints vs handlers
echo "=== REST Endpoints ===" && \
grep -c "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" src/main/java/**/controller/*.java 2>/dev/null || echo 0

# 5. Check gRPC service implementation
echo "=== gRPC Methods in Proto ===" && \
grep -c "rpc " src/main/proto/*.proto 2>/dev/null || echo 0
echo "=== gRPC Methods Implemented ===" && \
grep -c "@Override" src/main/java/**/grpc/*GrpcService.java 2>/dev/null || echo 0

# 6. Check empty endpoint handlers (CRITICAL!)
grep -rn "@.*Mapping" -A5 src/main/java/**/controller/*.java | grep -E "return null|return ResponseEntity.ok\(\)|// TODO"

# 7. Check Controller→Service wiring
echo "=== Service Methods Called in Controllers ===" && \
grep -roh "[a-zA-Z]*Service\.[a-zA-Z]*(" src/main/java/**/controller/*.java | sort -u
```

## Mock Data Verification

```bash
# 8. Check for empty list returns
grep -rn "List.of()\|Collections.emptyList()\|new ArrayList<>()" src/main/java/**/repository/*RepositoryImpl.java && \
echo "⚠️ Found empty lists - verify this is intentional"

# 9. Check for null returns
grep -rn "return null" src/main/java/**/repository/*.java && \
echo "⚠️ Found null returns - consider returning mock data"

# 10. Verify chart-related data has mock values
grep -rn "dailyData\|weeklyData\|chartData" src/main/java/**/repository/ | grep -E "emptyList|List\.of\(\)"
```

## Service→Repository Wiring

```bash
# 11. Check Service→Repository method calls
echo "=== Repository Methods Called in Services ===" && \
grep -roh "[a-zA-Z]*Repository\.[a-zA-Z]*(" src/main/java/**/service/*.java | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[A-Za-z]* [a-zA-Z]*(" src/main/java/**/repository/*Repository.java | grep -oE "[a-zA-Z]+\(" | sort -u

# 12. Verify ALL Repository interface methods have implementations
echo "=== Repository Interface Methods ===" && \
grep -rh "[A-Za-z]* [a-zA-Z]*(" src/main/java/**/repository/*Repository.java | grep -oE "[a-zA-Z]+\(" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "@Override\|public.*(" src/main/java/**/repository/*RepositoryImpl.java | grep -oE "[a-zA-Z]+\(" | sort -u
```

## Security Verification

```bash
# 13. Check for hardcoded secrets
grep -rn "password.*=.*\"\|secret.*=.*\"\|api_key.*=.*\"" src/main/java/ && \
echo "⚠️ Potential hardcoded secrets found"

# 14. Check security configuration
grep -rn "@PreAuthorize\|@Secured\|@RolesAllowed" src/main/java/**/controller/*.java | wc -l
echo "endpoints with security annotations"

# 15. Check for SQL injection vulnerabilities
grep -rn "\"SELECT.*\" +\|\"UPDATE.*\" +\|\"DELETE.*\" +" src/main/java/ && \
echo "⚠️ Potential SQL injection risk - use parameterized queries"
```

## Build & Test Commands

```bash
# 16. Quick build check
./gradlew clean build 2>&1 | tail -20

# 17. Run unit tests
./gradlew test

# 18. Run tests with coverage
./gradlew test jacocoTestReport

# 19. Run integration tests
./gradlew integrationTest
```

## Pre-PR Checklist Commands

```bash
# Run all these before creating a PR
echo "=== PRE-PR VERIFICATION ===" && \

echo "1. Build check..." && \
./gradlew clean build --quiet && echo "✅ Build passed" || echo "❌ Build failed" && \

echo "2. Tests..." && \
./gradlew test --quiet && echo "✅ Tests passed" || echo "⚠️ Tests failed" && \

echo "3. Empty handlers..." && \
(grep -rqn "return null" src/main/java/**/controller/*.java && echo "⚠️ Null returns in controller" || echo "✅ No null returns") && \

echo "4. Mock data..." && \
(grep -rqn "List.of()\|emptyList()" src/main/java/**/repository/*RepositoryImpl.java && echo "⚠️ Empty lists in repository" || echo "✅ No empty lists") && \

echo "5. Placeholder code..." && \
(grep -rqn "TODO.*implement\|Coming Soon" src/main/java/ && echo "⚠️ Placeholder code found" || echo "✅ No placeholders") && \

echo "=== VERIFICATION COMPLETE ==="
```

## API Documentation Verification

```bash
# 20. Check OpenAPI/Swagger annotations
echo "=== API Documentation ===" && \
grep -c "@Operation\|@ApiResponse\|@Schema" src/main/java/**/controller/*.java 2>/dev/null || echo "0 annotations"

# 21. Check for missing request validation
grep -l "@RequestBody\|@RequestParam" src/main/java/**/controller/*.java | \
xargs grep -L "@Valid\|@Validated" 2>/dev/null && echo "(endpoints may be missing validation)"
```

## User Journey Flow Verification

```bash
# 22. Check auth flow endpoints
echo "=== Auth Flow Check ===" && \
grep -q "login\|Login" src/main/java/**/controller/*.java && echo "✅ Login endpoint exists" || echo "⚠️ Missing: Login endpoint"
grep -q "register\|Register" src/main/java/**/controller/*.java && echo "✅ Register endpoint exists" || echo "⚠️ Missing: Register endpoint"
grep -q "logout\|Logout" src/main/java/**/controller/*.java && echo "✅ Logout endpoint exists" || echo "⚠️ Missing: Logout endpoint"
```
