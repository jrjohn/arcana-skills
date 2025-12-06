# Verification Commands Reference

All verification commands in one place for easy reference.

## Quick Diagnosis Commands

```bash
# === ARCHITECTURE VERIFICATION ===

# 1. Check layer violations
grep -rn "from.*controller" app/service/ && echo "❌ Service importing Controller!"
grep -rn "from.*controller" app/repository/ && echo "❌ Repository importing Controller!"

# 2. Check for unimplemented methods
grep -rn "raise NotImplementedError\|TODO.*implement\|pass\s*#.*TODO" app/

# 3. Check empty route handlers
grep -rn "def.*():\s*pass$" app/controller/
```

## 🚨 Layer Wiring Verification (CRITICAL)

```bash
# === CONTROLLER → SERVICE → REPOSITORY PATTERN ===

# 4. 🚨 Check Controller should NOT inject Repository directly
echo "=== Controller→Repository Direct Injection Check ===" && \
VIOLATIONS=$(grep -rln "_repository\|Repository" app/controller/*.py 2>/dev/null | wc -l) && \
if [ "$VIOLATIONS" -gt 0 ]; then \
    echo "❌ VIOLATION: $VIOLATIONS Controllers inject Repository directly!"; \
    echo "Controllers should inject Service, not Repository."; \
    grep -rln "_repository\|Repository" app/controller/*.py 2>/dev/null; \
else \
    echo "✅ All Controllers correctly inject Service"; \
fi

# 5. 🚨 Check Service layer exists
echo "=== Service Layer Existence Check ===" && \
SERVICE_COUNT=$(find app -path "*/service/*_service.py" 2>/dev/null | wc -l) && \
IMPL_COUNT=$(find app -path "*/service/*_service_impl.py" -o -path "*/service/*_impl.py" 2>/dev/null | wc -l) && \
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
grep -roh "_repository\.[a-zA-Z_]*(" app/service/*.py 2>/dev/null | sort -u || echo "(no repository calls found)"
echo "Repository interface methods:" && \
grep -rh "def [a-zA-Z_]*(" app/repository/*.py 2>/dev/null | grep -oE "def [a-zA-Z_]+\(" | sort -u

# 7. 🚨 Verify ALL Service interfaces have implementations
echo "=== Service Interface/Implementation Parity ===" && \
INTERFACES=$(find app -path "*/service/*_service.py" ! -name "*_impl.py" 2>/dev/null | wc -l) && \
IMPLS=$(find app -path "*/*_service_impl.py" -o -path "*/service/*_impl.py" 2>/dev/null | wc -l) && \
echo "Service interfaces: $INTERFACES" && \
echo "Service implementations: $IMPLS" && \
if [ "$INTERFACES" -ne "$IMPLS" ]; then \
    echo "❌ MISMATCH! Missing implementations"; \
else \
    echo "✅ All Service interfaces have implementations"; \
fi
```

## API Endpoint Verification

```bash
# 4. Check routes vs handlers
echo "Routes defined:" && grep -c "@.*\.route\|@bp\.route" app/controller/*.py
echo "Handler functions:" && grep -c "^def " app/controller/*.py

# 5. Check gRPC service implementation
echo "gRPC methods in proto:" && grep -c "rpc " protos/*.proto 2>/dev/null || echo 0
echo "gRPC methods implemented:" && grep -c "def " app/grpc/*_servicer.py 2>/dev/null || echo 0

# 6. Check Controller→Service wiring
echo "=== Service Methods Called ===" && \
grep -roh "_service\.[a-zA-Z_]*(" app/controller/*.py | sort -u
```

## Mock Data Verification

```bash
# 7. Check for empty list returns
grep -rn "\[\]\|list()" app/repository/*_impl.py && \
echo "⚠️ Found empty lists - verify intentional"

# 8. Check for None returns
grep -rn "return None" app/repository/*.py && \
echo "⚠️ Found None returns"
```

## Build & Test Commands

```bash
# 9. Run tests
python -m pytest

# 10. Run with coverage
python -m pytest --cov=app --cov-report=html

# 11. Type checking
mypy app/

# 12. Linting
ruff check app/
```

## Pre-PR Checklist

```bash
echo "=== PRE-PR VERIFICATION ===" && \
echo "1. Tests..." && python -m pytest -q && echo "✅ Passed" || echo "❌ Failed" && \
echo "2. Type check..." && mypy app/ --quiet && echo "✅ Passed" || echo "⚠️ Issues" && \
echo "3. Placeholders..." && (grep -rqn "NotImplementedError\|TODO" app/ && echo "⚠️ Found" || echo "✅ None") && \
echo "=== COMPLETE ==="
```
