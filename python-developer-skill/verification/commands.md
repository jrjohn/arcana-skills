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
