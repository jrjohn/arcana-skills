# Spring Boot Developer Skill

Professional Spring Boot development skill based on [Arcana Cloud SpringBoot](https://github.com/jrjohn/arcana-cloud-springboot) enterprise architecture.

## Overview

This skill provides comprehensive guidance for Spring Boot development following enterprise-grade architectural patterns. It supports Clean Architecture, dual-protocol communication (gRPC/REST), OSGi Plugin System, and multiple deployment modes.

## Key Features

- **Clean Architecture** - Three-layer architecture (Controller, Service, Repository)
- **Dual-Protocol Support** - gRPC (2.5x faster) and REST APIs
- **OSGi Plugin System** - Hot-swappable modular architecture
- **5 Deployment Modes** - From monolithic to Kubernetes with gRPC
- **Server-Side Rendering** - SSR engine for web applications
- **Enterprise Security** - JWT authentication, RBAC, audit logging

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

## Deployment Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Monolithic | All layers colocated | Development |
| Layered + HTTP | Separate containers with HTTP | Simple deployment |
| Layered + gRPC | Separate containers with gRPC | Performance-critical |
| Kubernetes + HTTP | K8s deployment with HTTP | Cloud production |
| Kubernetes + gRPC | K8s with TLS-secured gRPC | Enterprise production |

## Tech Stack

| Technology | Version |
|------------|---------|
| Java | 21+ |
| Spring Boot | 3.2+ |
| gRPC | 1.60+ |
| OSGi | Felix 7.0+ |
| PostgreSQL | 15+ |
| Redis | 7.0+ |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- Spring Boot microservices development
- Architecture design and review
- gRPC service implementation
- Plugin-based modular applications
- Kubernetes deployment configuration
- Enterprise backend development

## Quick Start

### gRPC Service

```protobuf
service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
  rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
}
```

```java
@GrpcService
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final UserService userService;

    @Override
    public void getUser(GetUserRequest request, StreamObserver<UserResponse> observer) {
        User user = userService.findById(request.getId());
        observer.onNext(toResponse(user));
        observer.onCompleted();
    }
}
```

### OSGi Plugin

```java
@Component(
    immediate = true,
    service = ArcanaPlugin.class,
    property = {
        "plugin.key=analytics-plugin",
        "plugin.name=Analytics Plugin"
    }
)
public class AnalyticsPlugin implements ArcanaPlugin {

    @Override
    public void activate(BundleContext context) {
        // Register services and handlers
    }

    @Override
    public void deactivate() {
        // Cleanup resources
    }
}
```

## License

This skill is part of the Arcana enterprise architecture series.
