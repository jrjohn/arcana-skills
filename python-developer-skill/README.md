# Python Developer Skill

Professional Python/Flask development skill based on [Arcana Cloud Python](https://github.com/jrjohn/arcana-cloud-python) enterprise architecture.

## Overview

This skill provides comprehensive guidance for Python/Flask development following enterprise-grade architectural patterns. It supports Clean Architecture, gRPC-first communication (2.78x faster), dual-protocol support, and multiple deployment modes.

## Key Features

- **Clean Architecture** - Three-layer architecture (Controller, Service, Repository)
- **gRPC-First Design** - 2.78x average speedup over HTTP REST
- **Dual-Protocol Support** - Both gRPC and REST endpoints
- **SQLAlchemy ORM** - Robust data access layer
- **Celery Integration** - Background task processing
- **Redis Caching** - High-performance caching layer

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

## Performance Benchmarks

| Operation | HTTP REST | gRPC | Speedup |
|-----------|-----------|------|---------|
| Point Query | 12.5ms | 1.98ms | **6.30x** |
| List Query | 45.2ms | 18.3ms | **2.47x** |
| Create | 23.1ms | 9.8ms | **2.36x** |
| **Average** | - | - | **2.78x** |

## Tech Stack

| Technology | Version |
|------------|---------|
| Python | 3.11+ |
| Flask | 3.0+ |
| SQLAlchemy | 2.0+ |
| gRPC | 1.60+ |
| Celery | 5.3+ |
| Redis | 7.0+ |
| PostgreSQL | 15+ |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- Python microservices development
- Flask API development
- gRPC service implementation
- Background task processing with Celery
- Database design with SQLAlchemy
- Enterprise backend development

## Quick Start

### Repository Pattern

```python
class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, user_id: str) -> User | None:
        return self._session.query(User).filter(User.id == user_id).first()

    def find_by_email(self, email: str) -> User | None:
        return self._session.query(User).filter(User.email == email).first()

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user
```

### gRPC Service

```python
class UserServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    def GetUser(self, request, context):
        user = self._user_service.get_by_id(request.id)
        if not user:
            context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
        return user_pb2.UserResponse(
            id=user.id,
            name=user.name,
            email=user.email
        )
```

### Celery Task

```python
@celery.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id: str):
    try:
        user = user_service.get_by_id(user_id)
        email_service.send_welcome(user.email, user.name)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

## License

This skill is part of the Arcana enterprise architecture series.
