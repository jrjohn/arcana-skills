# Python Developer Skill

Professional Python/Flask development skill based on [Arcana Cloud Python](https://github.com/jrjohn/arcana-cloud-python) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any Python project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
arcana-python-developer-skill/
├── SKILL.md                    # Main skill file (core rules & patterns)
├── README.md                   # This file
├── verification/
│   └── commands.md             # All verification bash commands
├── patterns/
│   ├── patterns.md             # Design patterns (original)
│   └── service-layer.md        # Service layer pattern details
├── checklists/
│   └── production-ready.md     # Production & code review checklists
├── reference.md                # Technical reference
└── examples.md                 # Code examples
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| 🔴 CRITICAL | Zero-Empty Policy | Repository stubs never return empty lists |
| 🔴 CRITICAL | API Wiring | All routes must call existing Service methods |
| 🔴 CRITICAL | gRPC Implementation | All proto rpc methods must be implemented |
| 🟡 IMPORTANT | Type Hints | All functions have type annotations |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | API Documentation | OpenAPI annotations |
| 🟢 RECOMMENDED | Monitoring | Prometheus metrics |

## Quick Reference Card

### New Endpoint:
```
1. Add route with @bp.route decorator
2. Add Service interface method
3. Add Service implementation
4. Add Repository method if needed
5. Add Pydantic model for validation
6. Verify mock data is non-empty
```

### New gRPC Service:
```
1. Define service in .proto file
2. Run protoc to generate code
3. Create Servicer class
4. Implement all rpc methods
5. Wire to Service layer
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep "\\[\\]\\|list()" *_impl.py` |
| 500 error | `grep "NotImplementedError" app/` |
| gRPC error | Compare rpc count vs def count |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│         HTTP Endpoints + JWT Auth + Validation      │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│          Business Logic + Orchestration             │
├─────────────────────────────────────────────────────┤
│                  Repository Layer                    │
│         Database Operations + Caching               │
└─────────────────────────────────────────────────────┘
```

## Key Features

- **Clean Architecture** - Three-layer architecture
- **gRPC-First** - 2.78x speedup over REST
- **Dual-Protocol** - gRPC and REST support
- **Spec Gap Prediction** - Auto-detect missing endpoints
- **Error Handling Pattern** - Unified AppException model
- **Verification Commands** - 12+ diagnostic commands

## Tech Stack

| Technology | Version |
|------------|---------|
| Python | 3.13+ |
| Flask | 3.0+ |
| SQLAlchemy | 2.0+ |
| gRPC | 1.60+ |
| Pydantic | 2.0+ |
| Redis | 7.0+ |

## Documentation Files

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions & architecture |
| [verification/commands.md](verification/commands.md) | All diagnostic commands |
| [patterns/service-layer.md](patterns/service-layer.md) | Service layer pattern |
| [checklists/production-ready.md](checklists/production-ready.md) | Release checklists |
| [reference.md](reference.md) | Technical reference |
| [examples.md](examples.md) | Code examples |

## When to Use This Skill

- Python microservices development
- Architecture design and review
- Code review
- gRPC service implementation
- Debugging API issues
