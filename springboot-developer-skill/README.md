# Spring Boot Developer Skill

Professional Spring Boot development skill based on [Arcana Cloud SpringBoot](https://github.com/jrjohn/arcana-cloud-springboot) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any Spring Boot project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
springboot-developer-skill/
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
| 🔴 CRITICAL | API Wiring | All Controller endpoints must call existing Service methods |
| 🔴 CRITICAL | gRPC Implementation | All proto rpc methods must be implemented |
| 🔴 CRITICAL | Security | All endpoints must have proper authentication |
| 🟡 IMPORTANT | Input Validation | All endpoints use @Valid annotation |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | API Documentation | OpenAPI/Swagger annotations |
| 🟢 RECOMMENDED | Monitoring | Actuator & metrics enabled |

## Quick Reference Card

### New REST Endpoint:
```
1. Add Controller method with @GetMapping/@PostMapping
2. Add Service interface method
3. Add Service implementation
4. Add Repository method if needed
5. Add @Valid for request body validation
6. Verify mock data is non-empty
```

### New gRPC Service:
```
1. Define service in .proto file
2. Run ./gradlew generateProto
3. Create GrpcService extending generated base
4. Implement all rpc methods
5. Add @GrpcService annotation
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep "List.of()\\|emptyList()" *RepositoryImpl.java` |
| 404 error | Check Service method exists for Controller call |
| gRPC error | Compare .proto rpc count vs @Override count |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│            REST/gRPC Endpoints + Auth               │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│          Business Logic + Orchestration             │
├─────────────────────────────────────────────────────┤
│                  Repository Layer                    │
│           Data Access + Caching + Sync              │
└─────────────────────────────────────────────────────┘
```

## Key Features

- **Clean Architecture** - Three-layer architecture
- **Dual-Protocol** - gRPC (2.5x faster) and REST support
- **OSGi Plugin System** - Hot-swappable modular architecture
- **Spec Gap Prediction** - Auto-detect missing API endpoints
- **Error Handling Pattern** - Unified ApiException model
- **Verification Commands** - 22+ diagnostic bash commands

## Tech Stack

| Technology | Version |
|------------|---------|
| Java | 25+ (OpenJDK) |
| Spring Boot | 4.0+ |
| gRPC | 1.60+ |
| Apache Felix | 7.0+ |
| MySQL | 8.0+ |
| Redis | 7.0+ |

## Documentation Files

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions & architecture |
| [verification/commands.md](verification/commands.md) | All diagnostic commands |
| [patterns/service-layer.md](patterns/service-layer.md) | Service layer pattern details |
| [checklists/production-ready.md](checklists/production-ready.md) | Release & review checklists |
| [reference.md](reference.md) | Technical API reference |
| [examples.md](examples.md) | Practical code examples |

## When to Use This Skill

- Spring Boot microservices development
- Architecture design and review
- Code review
- gRPC service implementation
- Plugin-based modular applications
- Debugging API issues
