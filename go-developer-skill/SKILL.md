---
name: go-developer-skill
description: Go development guide based on Arcana Cloud Go enterprise architecture. Provides comprehensive support for Clean Architecture, fx (Uber) DI, gRPC-first communication (1.80x faster), dual-protocol support (gRPC/REST via Gin), multi-database DAO layer (MySQL/PostgreSQL/MongoDB via GORM), Viper config, zap logging, Plugin System, SSR Engine, Background Jobs, and 5 deployment modes. Suitable for Go microservices development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Go Developer Skill

Professional Go development skill based on [Arcana Cloud Go](https://github.com/jrjohn/arcana-cloud-go) enterprise architecture.

---

## Quick Reference Card

### New Endpoint Checklist:
```
1. Define route in controller/http with gin.RouterGroup
2. Add method to Service interface
3. Implement method in serviceImpl struct
4. Add Repository/DAO method if data access needed
5. Add request validation struct with binding tags
6. Register route in router setup (internal/controller/http/router.go)
7. Wire dependencies via fx in internal/di/
8. Verify mock data returns non-empty values
```

### New gRPC Service Checklist:
```
1. Define service in api/proto/*.proto
2. Run protoc to generate Go code
3. Create server struct implementing generated interface
4. Implement ALL rpc methods (count must match)
5. Register service in gRPC server setup
6. Wire to existing Service layer via fx DI
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep -rn "return nil\|return \[\]" internal/domain/repository/` |
| 500 error | `grep -rn "panic\|TODO.*implement" internal/` |
| gRPC UNIMPLEMENTED | Compare `rpc ` count in .proto vs methods in server struct |
| DI error | Check fx.Provide/fx.Invoke registrations in internal/di/ |
| Build failure | `go vet ./...` |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return nil slices for list data | `grep -rn "return nil" internal/domain/repository/` |
| API Wiring | ALL routes must call existing Service methods | Check handler->service calls |
| gRPC Implementation | ALL proto rpc methods MUST be implemented | Count rpc vs method definitions |
| Error Handling | ALL errors must be checked and handled | `go vet ./...` |
| DI Registration | ALL services registered in fx container | Check fx.Provide() calls |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| Input Validation | Struct tags for all request bindings | Check `binding:"required"` tags |
| Mock Data Quality | Realistic, varied values | Review mock data |
| Error Wrapping | Wrap errors with context using fmt.Errorf | Check `%w` usage |
| Logging | Structured logging with zap | Check logger.Info/Error calls |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| API Documentation | Swagger/OpenAPI annotations |
| Monitoring | Prometheus metrics |
| Caching | Redis caching for hot data |
| Rate Limiting | API rate limits |

---

## Error Handling Pattern

### AppError - Unified Error Model

```go
// internal/domain/entity/errors.go
package entity

import (
    "fmt"
    "net/http"
)

type ErrorCode string

const (
    // Network errors
    ErrNetworkUnavailable ErrorCode = "NETWORK_UNAVAILABLE"
    ErrTimeout            ErrorCode = "TIMEOUT"
    ErrServiceUnavailable ErrorCode = "SERVICE_UNAVAILABLE"

    // Auth errors
    ErrUnauthorized       ErrorCode = "UNAUTHORIZED"
    ErrTokenExpired       ErrorCode = "TOKEN_EXPIRED"
    ErrInvalidCredentials ErrorCode = "INVALID_CREDENTIALS"

    // Data errors
    ErrNotFound         ErrorCode = "NOT_FOUND"
    ErrValidationFailed ErrorCode = "VALIDATION_FAILED"
    ErrConflict         ErrorCode = "CONFLICT"

    // General errors
    ErrInternal ErrorCode = "INTERNAL_ERROR"
)

type AppError struct {
    Code       ErrorCode              `json:"code"`
    Message    string                 `json:"message"`
    HTTPStatus int                    `json:"-"`
    Details    map[string]interface{} `json:"details,omitempty"`
}

func (e *AppError) Error() string {
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func NewAppError(code ErrorCode, message string, httpStatus int) *AppError {
    return &AppError{Code: code, Message: message, HTTPStatus: httpStatus}
}

func ErrNotFoundError(message string) *AppError {
    return NewAppError(ErrNotFound, message, http.StatusNotFound)
}

func ErrUnauthorizedError(message string) *AppError {
    return NewAppError(ErrUnauthorized, message, http.StatusUnauthorized)
}

func ErrValidationError(message string, details map[string]interface{}) *AppError {
    return &AppError{
        Code:       ErrValidationFailed,
        Message:    message,
        HTTPStatus: http.StatusBadRequest,
        Details:    details,
    }
}

func ErrConflictError(message string) *AppError {
    return NewAppError(ErrConflict, message, http.StatusConflict)
}

func ErrInternalError(message string) *AppError {
    return NewAppError(ErrInternal, message, http.StatusInternalServerError)
}
```

### Global Error Handler Middleware (Gin)

```go
// internal/middleware/error_handler.go
package middleware

import (
    "net/http"
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"

    "arcana-cloud-go/internal/domain/entity"
)

func ErrorHandler(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()

        if len(c.Errors) > 0 {
            err := c.Errors.Last().Err

            if appErr, ok := err.(*entity.AppError); ok {
                c.JSON(appErr.HTTPStatus, gin.H{
                    "code":      appErr.Code,
                    "message":   appErr.Message,
                    "details":   appErr.Details,
                    "timestamp": time.Now().UTC().Format(time.RFC3339),
                })
                return
            }

            logger.Error("unexpected error", zap.Error(err))
            c.JSON(http.StatusInternalServerError, gin.H{
                "code":      entity.ErrInternal,
                "message":   "An internal error occurred",
                "timestamp": time.Now().UTC().Format(time.RFC3339),
            })
        }
    }
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| Service | 90%+ | Business logic, edge cases |
| Repository/DAO | 80%+ | Data mapping, error handling |
| Controller | 75%+ | Request handling, validation |

### Test Commands
```bash
# Run all tests
go test ./...

# Run with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# Run specific package tests
go test ./internal/domain/service/...

# Run with verbose output
go test -v ./...

# Run with race detection
go test -race ./...

# View coverage summary
go tool cover -func=coverage.out
```

---

## Spec Gap Prediction System

When implementing API from incomplete specifications, PROACTIVELY predict missing requirements:

### CRUD Prediction Matrix

When a spec mentions "User management API", predict ALL CRUD operations:

| Entity | Predicted Endpoints | Status |
|--------|---------------------|--------|
| User | GET /api/v1/users | Check |
| User | GET /api/v1/users/:id | Check |
| User | POST /api/v1/users | Check |
| User | PUT /api/v1/users/:id | Check |
| User | DELETE /api/v1/users/:id | Check |

### Response State Prediction

For every endpoint, predict required response states:

```go
// Predicted states for GET /api/v1/users/:id:
// 200 OK - User found
// 404 Not Found - User doesn't exist
// 401 Unauthorized - Not logged in
// 403 Forbidden - No permission
// 500 Internal Server Error - Server error
```

### Pagination Prediction

List endpoints SHOULD support pagination:

```go
// GET /api/v1/users
// Predicted query parameters:
// - page: int = 0
// - size: int = 10
// - sort: string = "created_at"
// - order: "asc" | "desc" = "desc"
```

### Filtering Prediction

List endpoints SHOULD support filtering:

```go
// GET /api/v1/users
// Predicted filters:
// - status: string - Filter by status
// - created_after: time.Time - Created after date
// - search: string - Search in name/email
```

### Ask Clarification Prompt

When specs are incomplete, ASK before implementing:

```
The specification mentions "User API" but doesn't specify:
1. Should DELETE be soft-delete or hard-delete?
2. What fields are required for user creation?
3. Is email verification required?
4. What roles/permissions exist?

Please clarify before I proceed with implementation.
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
+-----------------------------------------------------+
|                  Controller Layer                     |
|       Gin (REST) + gRPC Server + Middleware          |
|            HTTP :8080  |  gRPC :50051                |
+-----------------------------------------------------+
|                   Service Layer                       |
|       Business Logic + Domain Events                  |
|       Interfaces define contracts                     |
+-----------------------------------------------------+
|                  Repository/DAO Layer                  |
|       GORM (MySQL/PostgreSQL/MongoDB) + Redis        |
|       Multi-database support via DAO abstraction     |
+-----------------------------------------------------+
```

### Layer Dependency Rules

```
Controller --> Service --> Repository/DAO
    |              |              |
    v              v              v
  gin.H      interfaces       GORM/DB
  proto       entities        Redis
  HTTP       AppError         queries

FORBIDDEN:
  Controller --> Repository (skip service)
  Service    --> gin/proto   (HTTP concerns)
  Repository --> Service     (circular)
```

### Deployment Modes

| Mode | Description | Communication | Use Case |
|------|-------------|---------------|----------|
| Monolithic | Single binary | Direct function calls | Development |
| Layered | Separate containers per layer | gRPC between layers | Staging |
| Microservices | Fine-grained services | gRPC + message queue | Production |
| Hybrid | Mixed deployment | gRPC + REST | Migration |
| Serverless | Cloud functions | HTTP triggers | Edge/API Gateway |

```
Monolithic Mode:
+-------------------------------------------+
|  Single Binary                            |
|  +----------+  +--------+  +----------+  |
|  |Controller|->|Service |->|Repository|  |
|  +----------+  +--------+  +----------+  |
+-------------------------------------------+

Layered Mode:
+-----------+     +---------+     +----------+
|Controller |---->| Service |---->|Repository|
| Container | gRPC| Container| gRPC| Container|
+-----------+     +---------+     +----------+

Microservices Mode:
+---------+  +---------+  +---------+  +---------+
|  User   |  | Product |  |  Order  |  |  Auth   |
| Service |  | Service |  | Service |  | Service |
+---------+  +---------+  +---------+  +---------+
     |            |            |            |
     +------+-----+-----+-----+-----+------+
            |           |           |
       +--------+  +--------+  +--------+
       | MySQL  |  | Postgres|  |  Redis |
       +--------+  +--------+  +--------+
```

### Performance
- gRPC delivers **1.80x average speedup** over HTTP REST
- Monolithic mode: **60K ops/sec**
- Memory footprint: **~50MB**
- Startup time: **~100ms**

## Instructions

When handling Go development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented methods (MUST be empty)
grep -rn "panic(\"not implemented\")\|TODO.*implement\|// TODO" internal/

# 2. Check for empty handler functions (MUST be empty)
grep -rn "func.*gin.Context.*{}" internal/controller/

# 3. Check all routes have handlers
echo "Routes defined:" && grep -c "\.GET\|\.POST\|\.PUT\|\.DELETE\|\.PATCH" internal/controller/http/*.go 2>/dev/null || echo 0
echo "Handler functions:" && grep -c "func.*\*gin.Context" internal/controller/http/*.go 2>/dev/null || echo 0

# 4. Check gRPC services are implemented
echo "gRPC methods defined in proto:" && grep -c "rpc " api/proto/*.proto 2>/dev/null || echo 0
echo "gRPC methods implemented:" && grep -c "func.*Server).*context.Context" internal/controller/grpc/*.go 2>/dev/null || echo 0

# 5. Verify tests pass
go test ./...

# 6. Check Controller routes call existing Service methods (CRITICAL!)
echo "=== Service Methods Called in Controllers ===" && \
grep -roh "s\.\w*Service\.\w*(" internal/controller/ | sort -u
echo "=== Service Methods Defined ===" && \
grep -rh "func.*Service).*(" internal/domain/service/*.go | grep -oE "\) \w+\(" | sort -u

# 7. Verify ALL Controller endpoints have Service layer implementation
echo "=== Service Interface Definitions ===" && \
grep -rn "type.*Service interface" internal/domain/service/*.go
echo "=== Service Struct Definitions ===" && \
grep -rn "type.*serviceImpl struct" internal/domain/service/*.go

# 8. Check for placeholder returns in route handlers
grep -rn "c\.JSON.*Coming Soon\|TODO\|NotImplemented" internal/controller/http/*.go

# 9. Check Service->Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "s\.\w*[Rr]epo\w*\.\w*(" internal/domain/service/*.go | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "^\s*\w\+(" internal/domain/repository/*.go | sort -u

# 10. Check fx DI provider registrations
echo "=== fx.Provide Registrations ===" && \
grep -rn "fx\.Provide\|fx\.Invoke" internal/di/*.go

# 11. Go vet and build check
go vet ./...
go build ./...
```

CRITICAL: All routes MUST have corresponding handler functions. All gRPC methods defined in .proto files MUST be implemented in server structs.

API WIRING CRITICAL: Commands #6-#8 detect Controller routes that call Service methods that don't exist. A Controller can call `s.userService.GetAccountInfo()` but if the Service interface doesn't have this method, the route fails at compile time in Go (unlike dynamic languages).

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return nil or empty slices for data that powers UI charts or API responses**. This causes:
- Frontend charts that render but show nothing
- API responses with empty data arrays
- Client applications showing "No data" even when structure exists

### Mock Data Rules

**Rule 1: List data for charts MUST have at least 7 items**
```go
// BAD - Chart will be blank
func (r *userRepoImpl) GetWeeklySummary(userID string) ([]DailySummary, error) {
    return nil, nil // Chart has no data to render!
}

// GOOD - Chart has data to display
func (r *userRepoImpl) GetWeeklySummary(userID string) ([]DailySummary, error) {
    scores := []int{72, 78, 85, 80, 76, 88, 82}
    summaries := make([]DailySummary, 7)
    for i, score := range scores {
        summaries[i] = DailySummary{
            Date:  time.Now().AddDate(0, 0, -6+i),
            Score: score,
        }
    }
    return summaries, nil
}
```

**Rule 2: Use realistic, varied sample values**
```go
// BAD - Monotonous test data
scores := make([]int, 7)
for i := range scores { scores[i] = 80 }

// GOOD - Realistic variation
scores := []int{72, 78, 85, 80, 76, 88, 82} // Shows trend
```

**Rule 3: Data must match struct definition exactly**
```bash
# Before creating mock data, ALWAYS verify the struct:
grep -A 20 "type DailySummary struct" internal/domain/entity/*.go
```

**Rule 4: Create helper functions for complex mock data**
```go
// Create reusable mock factory
func newMockDailySummary(date time.Time, score int) DailySummary {
    return DailySummary{
        ID:        uuid.New().String(),
        Date:      date,
        Score:     score,
        Duration:  time.Duration(score*5) * time.Minute,
        CreatedAt: time.Now(),
    }
}
```

### Quick Verification Commands for Mock Data

```bash
# 12. Check for nil/empty returns in Repository stubs (MUST FIX)
grep -rn "return nil, nil\|return \[\]" internal/domain/repository/*_impl.go

# 13. Verify chart-related data has mock values
grep -rn "Summary\|Weekly\|Chart" internal/domain/repository/ | grep -E "return nil"
```

---

### 0. Project Setup - CRITICAL

IMPORTANT: This reference project has been validated with tested go.mod and gRPC settings. **NEVER reconfigure project structure or modify go.mod dependencies arbitrarily**, or it will cause build errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-cloud-go.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-cloud-go template"
```

**Step 3**: Modify project name
Only modify the following required items:
- `module` path in `go.mod`
- Application name in `internal/config/`
- Service names in Docker-related configuration files
- Update settings in `.env.example` file

**Step 4**: Clean up example code
The cloned project contains example API (e.g., Arcana User Management). Clean up and replace with new project business logic:

**Core architecture files to KEEP** (do not delete):
- `internal/config/` - Viper configuration
- `internal/middleware/` - Middleware (Auth, Error handling, CORS)
- `internal/di/` - fx dependency injection modules
- `internal/security/` - JWT, bcrypt, TLS utilities
- `pkg/` - Shared packages
- `deployment/` - Docker & K8s manifests
- `scripts/` - Build and deployment scripts

**Example files to REPLACE**:
- `internal/controller/http/` - Delete example controllers, create new HTTP endpoints
- `internal/controller/grpc/` - Delete example gRPC servers, create new implementations
- `internal/domain/service/` - Delete example services, create new business logic
- `internal/domain/repository/` - Delete example repositories, create new data access
- `internal/domain/entity/` - Delete example entities, create new domain models
- `internal/domain/dao/` - Delete example DAOs, create new data access objects
- `api/proto/*.proto` - Modify gRPC proto definitions
- `tests/` - Update test cases

**Step 5**: Install dependencies and verify
```bash
go mod tidy
go test ./...
go build ./cmd/server/
```

### Prohibited Actions
- **DO NOT** create new Go project from scratch with `go mod init`
- **DO NOT** arbitrarily add or remove dependencies in `go.mod`
- **DO NOT** modify protobuf compilation settings
- **DO NOT** reconfigure GORM, fx, or other library settings
- **DO NOT** change the internal package structure layout

### Allowed Modifications
- Add business-related Go code (following existing architecture)
- Add Controller handlers, Service implementations, Repository/DAO implementations
- Add Domain Entities, DTOs
- Add GORM migration scripts
- Modify gRPC proto files (and regenerate)

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

CRITICAL: All development MUST follow this TDD workflow. Every SRS/SDD requirement must have corresponding tests BEFORE implementation.

ABSOLUTE RULE: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
+---------------------------------------------------------------+
|                    TDD Development Workflow                     |
+---------------------------------------------------------------+
|  Step 1: Analyze Spec -> Extract all SRS & SDD requirements    |
|  Step 2: Create Tests -> Write tests for EACH Spec item        |
|  Step 3: Verify Coverage -> Ensure 100% Spec coverage in tests |
|  Step 4: Implement -> Build features to pass tests  MANDATORY  |
|  Step 5: Mock APIs -> Use mock data for unfinished deps        |
|  Step 6: Run All Tests -> ALL tests must pass before done      |
|  Step 7: Verify 100% -> Tests written = Features implemented   |
+---------------------------------------------------------------+
```

#### FORBIDDEN: Tests Without Implementation

```go
// WRONG - Test exists but no implementation
// Test file exists: user_service_test.go (32 tests)
// Production file: user_service.go -> MISSING or panics
// This is INCOMPLETE TDD!

// CORRECT - Test AND Implementation both exist
// Test file: user_service_test.go (32 tests)
// Production file: user_service.go (fully implemented)
// All 32 tests PASS
```

#### Placeholder Endpoint Policy

Placeholder endpoints are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```go
// WRONG - Placeholder endpoint left in production
r.GET("/training", func(c *gin.Context) {
    c.JSON(200, gin.H{"message": "Coming Soon"}) // FORBIDDEN!
})

// CORRECT - Real endpoint implementation
r.GET("/training", func(c *gin.Context) {
    data, err := trainingService.GetAll(c.Request.Context())
    if err != nil {
        c.Error(err)
        return
    }
    c.JSON(200, data)
})
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "Coming Soon\|panic.*not implemented\|TODO.*implement" internal/
```

### 2. Project Structure
```
arcana-cloud-go/
├── api/proto/              # gRPC protobuf definitions
│   └── user.proto
├── cmd/server/             # Application entry point
│   └── main.go
├── config/                 # Configuration files (YAML)
│   ├── config.yaml
│   ├── config.dev.yaml
│   └── config.prod.yaml
├── deployment/
│   └── docker/kubernetes/
├── internal/
│   ├── config/             # Viper configuration loader
│   │   └── config.go
│   ├── controller/
│   │   ├── http/           # Gin REST controllers
│   │   │   ├── router.go
│   │   │   ├── user_controller.go
│   │   │   └── auth_controller.go
│   │   └── grpc/           # gRPC server implementations
│   │       └── user_server.go
│   ├── domain/
│   │   ├── dao/            # Data Access Objects (multi-DB)
│   │   │   ├── user_dao.go
│   │   │   └── user_dao_impl.go
│   │   ├── entity/         # Domain entities
│   │   │   ├── user.go
│   │   │   └── errors.go
│   │   ├── repository/     # Repository interfaces
│   │   │   └── user_repository.go
│   │   └── service/        # Business logic
│   │       ├── user_service.go
│   │       └── user_service_impl.go
│   ├── di/                 # fx dependency injection
│   │   ├── module.go
│   │   └── providers.go
│   ├── grpc/client/        # gRPC client stubs
│   ├── jobs/               # Background job system
│   │   ├── scheduler.go
│   │   └── workers.go
│   ├── middleware/         # Gin middleware
│   │   ├── auth.go
│   │   ├── cors.go
│   │   ├── error_handler.go
│   │   └── logger.go
│   ├── plugin/             # Plugin system
│   │   ├── manager.go
│   │   └── interface.go
│   ├── security/           # JWT, bcrypt, TLS
│   │   ├── jwt.go
│   │   └── bcrypt.go
│   └── ssr/                # Server-side rendering
│       └── engine.go
├── pkg/                    # Shared packages
│   ├── logger/
│   ├── validator/
│   └── utils/
├── tests/integration/      # Integration tests
├── scripts/                # Build/deploy scripts
├── go.mod
└── go.sum
```

### 3. Domain Entity

```go
// internal/domain/entity/user.go
package entity

import (
    "time"

    "github.com/google/uuid"
    "gorm.io/gorm"
)

type SyncStatus string

const (
    SyncStatusSynced  SyncStatus = "SYNCED"
    SyncStatusPending SyncStatus = "PENDING"
    SyncStatusFailed  SyncStatus = "FAILED"
)

type User struct {
    ID           string     `gorm:"type:char(36);primaryKey" json:"id"`
    Name         string     `gorm:"type:varchar(255);not null" json:"name"`
    Email        string     `gorm:"type:varchar(255);uniqueIndex;not null" json:"email"`
    PasswordHash string     `gorm:"column:password_hash;type:varchar(255);not null" json:"-"`
    SyncStatus   SyncStatus `gorm:"column:sync_status;type:varchar(20);default:SYNCED" json:"syncStatus"`
    CreatedAt    time.Time  `gorm:"autoCreateTime" json:"createdAt"`
    UpdatedAt    time.Time  `gorm:"autoUpdateTime" json:"updatedAt"`
}

func (User) TableName() string {
    return "users"
}

func (u *User) BeforeCreate(tx *gorm.DB) error {
    if u.ID == "" {
        u.ID = uuid.New().String()
    }
    return nil
}

// UserDTO - Data Transfer Object
type UserDTO struct {
    ID        string `json:"id"`
    Name      string `json:"name"`
    Email     string `json:"email"`
    CreatedAt string `json:"createdAt"`
    UpdatedAt string `json:"updatedAt"`
}

func ToUserDTO(user *User) *UserDTO {
    return &UserDTO{
        ID:        user.ID,
        Name:      user.Name,
        Email:     user.Email,
        CreatedAt: user.CreatedAt.Format(time.RFC3339),
        UpdatedAt: user.UpdatedAt.Format(time.RFC3339),
    }
}
```

### 4. Repository Layer

```go
// internal/domain/repository/user_repository.go
package repository

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

type UserRepository interface {
    FindByID(ctx context.Context, userID string) (*entity.User, error)
    FindByEmail(ctx context.Context, email string) (*entity.User, error)
    FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error)
    FindPendingSync(ctx context.Context) ([]*entity.User, error)
    Save(ctx context.Context, user *entity.User) error
    Update(ctx context.Context, user *entity.User) error
    Delete(ctx context.Context, user *entity.User) error
}

// internal/domain/repository/user_repository_impl.go
package repository

import (
    "context"

    "gorm.io/gorm"

    "arcana-cloud-go/internal/domain/entity"
)

type userRepositoryImpl struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) UserRepository {
    return &userRepositoryImpl{db: db}
}

func (r *userRepositoryImpl) FindByID(ctx context.Context, userID string) (*entity.User, error) {
    var user entity.User
    if err := r.db.WithContext(ctx).Where("id = ?", userID).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &user, nil
}

func (r *userRepositoryImpl) FindByEmail(ctx context.Context, email string) (*entity.User, error) {
    var user entity.User
    if err := r.db.WithContext(ctx).Where("email = ?", email).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &user, nil
}

func (r *userRepositoryImpl) FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error) {
    var users []*entity.User
    var total int64

    r.db.WithContext(ctx).Model(&entity.User{}).Count(&total)

    offset := page * size
    if err := r.db.WithContext(ctx).
        Order("created_at DESC").
        Offset(offset).Limit(size).
        Find(&users).Error; err != nil {
        return nil, 0, err
    }
    return users, total, nil
}

func (r *userRepositoryImpl) FindPendingSync(ctx context.Context) ([]*entity.User, error) {
    var users []*entity.User
    if err := r.db.WithContext(ctx).
        Where("sync_status = ?", entity.SyncStatusPending).
        Find(&users).Error; err != nil {
        return nil, err
    }
    return users, nil
}

func (r *userRepositoryImpl) Save(ctx context.Context, user *entity.User) error {
    return r.db.WithContext(ctx).Create(user).Error
}

func (r *userRepositoryImpl) Update(ctx context.Context, user *entity.User) error {
    return r.db.WithContext(ctx).Save(user).Error
}

func (r *userRepositoryImpl) Delete(ctx context.Context, user *entity.User) error {
    return r.db.WithContext(ctx).Delete(user).Error
}
```

### 5. Service Layer

```go
// internal/domain/service/user_service.go
package service

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

type UserService interface {
    GetUser(ctx context.Context, userID string) (*entity.UserDTO, error)
    GetUsers(ctx context.Context, page, size int) ([]*entity.UserDTO, int64, error)
    CreateUser(ctx context.Context, req *CreateUserRequest) (*entity.UserDTO, error)
    UpdateUser(ctx context.Context, userID string, req *UpdateUserRequest) (*entity.UserDTO, error)
    DeleteUser(ctx context.Context, userID string) error
    Authenticate(ctx context.Context, email, password string) (*entity.User, error)
}

type CreateUserRequest struct {
    Name     string `json:"name" binding:"required,max=255"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}

type UpdateUserRequest struct {
    Name  *string `json:"name" binding:"omitempty,max=255"`
    Email *string `json:"email" binding:"omitempty,email"`
}

// internal/domain/service/user_service_impl.go
package service

import (
    "context"
    "fmt"

    "go.uber.org/zap"
    "golang.org/x/crypto/bcrypt"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/repository"
)

type userServiceImpl struct {
    repo   repository.UserRepository
    logger *zap.Logger
}

func NewUserService(repo repository.UserRepository, logger *zap.Logger) UserService {
    return &userServiceImpl{repo: repo, logger: logger}
}

func (s *userServiceImpl) GetUser(ctx context.Context, userID string) (*entity.UserDTO, error) {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, nil
    }
    return entity.ToUserDTO(user), nil
}

func (s *userServiceImpl) GetUsers(ctx context.Context, page, size int) ([]*entity.UserDTO, int64, error) {
    users, total, err := s.repo.FindAll(ctx, page, size)
    if err != nil {
        return nil, 0, fmt.Errorf("failed to list users: %w", err)
    }
    dtos := make([]*entity.UserDTO, len(users))
    for i, u := range users {
        dtos[i] = entity.ToUserDTO(u)
    }
    return dtos, total, nil
}

func (s *userServiceImpl) CreateUser(ctx context.Context, req *CreateUserRequest) (*entity.UserDTO, error) {
    existing, err := s.repo.FindByEmail(ctx, req.Email)
    if err != nil {
        return nil, fmt.Errorf("failed to check email: %w", err)
    }
    if existing != nil {
        return nil, entity.ErrValidationError("Email already registered", map[string]interface{}{
            "email": req.Email,
        })
    }

    hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
    if err != nil {
        return nil, fmt.Errorf("failed to hash password: %w", err)
    }

    user := &entity.User{
        Name:         req.Name,
        Email:        req.Email,
        PasswordHash: string(hash),
        SyncStatus:   entity.SyncStatusSynced,
    }

    if err := s.repo.Save(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to save user: %w", err)
    }

    s.logger.Info("user created", zap.String("userID", user.ID), zap.String("email", user.Email))

    return entity.ToUserDTO(user), nil
}

func (s *userServiceImpl) UpdateUser(ctx context.Context, userID string, req *UpdateUserRequest) (*entity.UserDTO, error) {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrNotFoundError("User not found")
    }

    if req.Name != nil {
        user.Name = *req.Name
    }
    if req.Email != nil {
        existing, err := s.repo.FindByEmail(ctx, *req.Email)
        if err != nil {
            return nil, fmt.Errorf("failed to check email: %w", err)
        }
        if existing != nil && existing.ID != userID {
            return nil, entity.ErrValidationError("Email already registered", map[string]interface{}{
                "email": *req.Email,
            })
        }
        user.Email = *req.Email
    }

    if err := s.repo.Update(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to update user: %w", err)
    }

    return entity.ToUserDTO(user), nil
}

func (s *userServiceImpl) DeleteUser(ctx context.Context, userID string) error {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return entity.ErrNotFoundError("User not found")
    }
    return s.repo.Delete(ctx, user)
}

func (s *userServiceImpl) Authenticate(ctx context.Context, email, password string) (*entity.User, error) {
    user, err := s.repo.FindByEmail(ctx, email)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrUnauthorizedError("Invalid email or password")
    }

    if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
        return nil, entity.ErrUnauthorizedError("Invalid email or password")
    }

    return user, nil
}
```

### 6. Controller Layer (Gin)

```go
// internal/controller/http/user_controller.go
package http

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/service"
)

type UserController struct {
    userService service.UserService
}

func NewUserController(userService service.UserService) *UserController {
    return &UserController{userService: userService}
}

func (ctrl *UserController) RegisterRoutes(rg *gin.RouterGroup, authMiddleware gin.HandlerFunc) {
    users := rg.Group("/users")
    users.Use(authMiddleware)
    {
        users.GET("", ctrl.GetUsers)
        users.GET("/:id", ctrl.GetUser)
        users.POST("", ctrl.CreateUser)
        users.PUT("/:id", ctrl.UpdateUser)
        users.DELETE("/:id", ctrl.DeleteUser)
    }
}

func (ctrl *UserController) GetUser(c *gin.Context) {
    userID := c.Param("id")
    user, err := ctrl.userService.GetUser(c.Request.Context(), userID)
    if err != nil {
        c.Error(err)
        return
    }
    if user == nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
        return
    }
    c.JSON(http.StatusOK, user)
}

func (ctrl *UserController) GetUsers(c *gin.Context) {
    page, _ := strconv.Atoi(c.DefaultQuery("page", "0"))
    size, _ := strconv.Atoi(c.DefaultQuery("size", "10"))

    users, total, err := ctrl.userService.GetUsers(c.Request.Context(), page, size)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "data":  users,
        "page":  page,
        "size":  size,
        "total": total,
    })
}

func (ctrl *UserController) CreateUser(c *gin.Context) {
    var req service.CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := ctrl.userService.CreateUser(c.Request.Context(), &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusCreated, user)
}

func (ctrl *UserController) UpdateUser(c *gin.Context) {
    userID := c.Param("id")
    var req service.UpdateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := ctrl.userService.UpdateUser(c.Request.Context(), userID, &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, user)
}

func (ctrl *UserController) DeleteUser(c *gin.Context) {
    userID := c.Param("id")
    if err := ctrl.userService.DeleteUser(c.Request.Context(), userID); err != nil {
        c.Error(err)
        return
    }
    c.Status(http.StatusNoContent)
}
```

### 7. fx Dependency Injection (Uber)

```go
// internal/di/module.go
package di

import (
    "go.uber.org/fx"
    "go.uber.org/zap"
    "gorm.io/gorm"

    "arcana-cloud-go/internal/config"
    httpctrl "arcana-cloud-go/internal/controller/http"
    "arcana-cloud-go/internal/domain/repository"
    "arcana-cloud-go/internal/domain/service"
    "arcana-cloud-go/internal/middleware"
)

var Module = fx.Options(
    // Infrastructure
    fx.Provide(config.NewConfig),
    fx.Provide(NewDatabase),
    fx.Provide(NewRedisClient),
    fx.Provide(NewLogger),

    // Repositories
    fx.Provide(repository.NewUserRepository),
    fx.Provide(repository.NewRefreshTokenRepository),

    // Services
    fx.Provide(service.NewUserService),
    fx.Provide(service.NewAuthService),

    // Controllers
    fx.Provide(httpctrl.NewUserController),
    fx.Provide(httpctrl.NewAuthController),

    // Middleware
    fx.Provide(middleware.NewAuthMiddleware),

    // Server
    fx.Provide(httpctrl.NewRouter),
    fx.Invoke(StartServer),
)

func NewLogger() (*zap.Logger, error) {
    return zap.NewProduction()
}

func NewDatabase(cfg *config.Config) (*gorm.DB, error) {
    return config.InitDatabase(cfg)
}

func StartServer(lc fx.Lifecycle, router *httpctrl.Router, cfg *config.Config, logger *zap.Logger) {
    lc.Append(fx.Hook{
        OnStart: func(ctx context.Context) error {
            go router.Run(cfg.Server.Port)
            logger.Info("server started", zap.Int("port", cfg.Server.Port))
            return nil
        },
        OnStop: func(ctx context.Context) error {
            logger.Info("server stopping")
            return nil
        },
    })
}
```

### 8. JWT Authentication Middleware

```go
// internal/security/jwt.go
package security

import (
    "errors"
    "time"

    "github.com/golang-jwt/jwt/v5"
)

type JWTClaims struct {
    UserID string   `json:"sub"`
    Roles  []string `json:"roles"`
    jwt.RegisteredClaims
}

type JWTService struct {
    secret    []byte
    expiresIn time.Duration
}

func NewJWTService(secret string, expiresIn time.Duration) *JWTService {
    return &JWTService{
        secret:    []byte(secret),
        expiresIn: expiresIn,
    }
}

func (s *JWTService) GenerateToken(userID string, roles []string) (string, error) {
    claims := &JWTClaims{
        UserID: userID,
        Roles:  roles,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(s.expiresIn)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secret)
}

func (s *JWTService) ValidateToken(tokenString string) (*JWTClaims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, errors.New("unexpected signing method")
        }
        return s.secret, nil
    })
    if err != nil {
        return nil, err
    }

    claims, ok := token.Claims.(*JWTClaims)
    if !ok || !token.Valid {
        return nil, errors.New("invalid token")
    }

    return claims, nil
}

// internal/middleware/auth.go
package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"

    "arcana-cloud-go/internal/security"
)

type AuthMiddleware struct {
    jwtService *security.JWTService
}

func NewAuthMiddleware(jwtService *security.JWTService) *AuthMiddleware {
    return &AuthMiddleware{jwtService: jwtService}
}

func (m *AuthMiddleware) RequireAuth() gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "code":    "UNAUTHORIZED",
                "message": "Missing or invalid authorization header",
            })
            return
        }

        tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
        claims, err := m.jwtService.ValidateToken(tokenStr)
        if err != nil {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "code":    "UNAUTHORIZED",
                "message": "Invalid or expired token",
            })
            return
        }

        c.Set("userID", claims.UserID)
        c.Set("userRoles", claims.Roles)
        c.Next()
    }
}

func (m *AuthMiddleware) RequireRole(roles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRoles, exists := c.Get("userRoles")
        if !exists {
            c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
                "code":    "FORBIDDEN",
                "message": "Insufficient permissions",
            })
            return
        }

        roleSlice := userRoles.([]string)
        for _, required := range roles {
            for _, userRole := range roleSlice {
                if userRole == required {
                    c.Next()
                    return
                }
            }
        }

        c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
            "code":    "FORBIDDEN",
            "message": "Insufficient permissions",
        })
    }
}
```

### 9. Database Migration with GORM

```bash
# GORM AutoMigrate (development)
# Called in application startup:
# db.AutoMigrate(&entity.User{}, &entity.RefreshToken{})

# Manual migration with golang-migrate
migrate -source file://migrations -database "mysql://user:pass@tcp(localhost:3306)/arcana" up
migrate -source file://migrations -database "mysql://user:pass@tcp(localhost:3306)/arcana" down 1

# Create new migration
migrate create -ext sql -dir migrations -seq add_users_table
```

### 10. Testing with Go testing package

```go
// internal/domain/service/user_service_test.go
package service

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "go.uber.org/zap"

    "arcana-cloud-go/internal/domain/entity"
)

// MockUserRepository
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) FindByID(ctx context.Context, userID string) (*entity.User, error) {
    args := m.Called(ctx, userID)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*entity.User), args.Error(1)
}

func (m *MockUserRepository) FindByEmail(ctx context.Context, email string) (*entity.User, error) {
    args := m.Called(ctx, email)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*entity.User), args.Error(1)
}

func (m *MockUserRepository) FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error) {
    args := m.Called(ctx, page, size)
    return args.Get(0).([]*entity.User), args.Get(1).(int64), args.Error(2)
}

func (m *MockUserRepository) FindPendingSync(ctx context.Context) ([]*entity.User, error) {
    args := m.Called(ctx)
    return args.Get(0).([]*entity.User), args.Error(1)
}

func (m *MockUserRepository) Save(ctx context.Context, user *entity.User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) Update(ctx context.Context, user *entity.User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) Delete(ctx context.Context, user *entity.User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func TestGetUser_Found(t *testing.T) {
    mockRepo := new(MockUserRepository)
    logger, _ := zap.NewDevelopment()
    svc := NewUserService(mockRepo, logger)

    mockUser := &entity.User{
        ID:    "123",
        Name:  "John Doe",
        Email: "john@example.com",
    }
    mockRepo.On("FindByID", mock.Anything, "123").Return(mockUser, nil)

    result, err := svc.GetUser(context.Background(), "123")

    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Equal(t, "123", result.ID)
    mockRepo.AssertExpectations(t)
}

func TestGetUser_NotFound(t *testing.T) {
    mockRepo := new(MockUserRepository)
    logger, _ := zap.NewDevelopment()
    svc := NewUserService(mockRepo, logger)

    mockRepo.On("FindByID", mock.Anything, "nonexistent").Return(nil, nil)

    result, err := svc.GetUser(context.Background(), "nonexistent")

    assert.NoError(t, err)
    assert.Nil(t, result)
    mockRepo.AssertExpectations(t)
}

func TestCreateUser_Success(t *testing.T) {
    mockRepo := new(MockUserRepository)
    logger, _ := zap.NewDevelopment()
    svc := NewUserService(mockRepo, logger)

    mockRepo.On("FindByEmail", mock.Anything, "john@example.com").Return(nil, nil)
    mockRepo.On("Save", mock.Anything, mock.AnythingOfType("*entity.User")).Return(nil)

    result, err := svc.CreateUser(context.Background(), &CreateUserRequest{
        Name:     "John Doe",
        Email:    "john@example.com",
        Password: "password123",
    })

    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Equal(t, "John Doe", result.Name)
    mockRepo.AssertExpectations(t)
}

func TestCreateUser_EmailExists(t *testing.T) {
    mockRepo := new(MockUserRepository)
    logger, _ := zap.NewDevelopment()
    svc := NewUserService(mockRepo, logger)

    existingUser := &entity.User{ID: "existing", Email: "john@example.com"}
    mockRepo.On("FindByEmail", mock.Anything, "john@example.com").Return(existingUser, nil)

    result, err := svc.CreateUser(context.Background(), &CreateUserRequest{
        Name:     "John Doe",
        Email:    "john@example.com",
        Password: "password123",
    })

    assert.Error(t, err)
    assert.Nil(t, result)
    mockRepo.AssertExpectations(t)
}
```

## API Wiring Verification Guide

### The API Wiring Advantage in Go

Unlike dynamic languages, Go catches most wiring issues at compile time. However, runtime issues can still occur:

```go
// internal/controller/http/settings_controller.go
func (ctrl *SettingsController) GetAccountInfo(c *gin.Context) {
    userID := c.GetString("userID")
    data, err := ctrl.settingsService.GetAccountInfo(c.Request.Context(), userID)
    if err != nil {
        c.Error(err)
        return
    }
    c.JSON(200, data)
}
```

**Problem**: If the Service interface doesn't declare GetAccountInfo, it fails at compile time. But if the method is declared but panics at runtime, that is still a critical issue.

### Detection Patterns

```bash
# Find methods called on Service in Controllers
grep -roh "ctrl\.\w*[Ss]ervice\.\w*(" internal/controller/ | sort -u

# Find methods defined in Service interfaces
grep -rh "^\s*\w\+(" internal/domain/service/*.go | grep -v "func\|type\|struct\|//\|package" | sort -u

# Find unimplemented methods
grep -rn "panic.*not implemented\|// TODO" internal/domain/service/*.go

# Compare: Every Service method called in Controller MUST exist and be implemented
```

### Correct Wiring Example

```go
// internal/controller/http/settings_controller.go
func (ctrl *SettingsController) GetAccountInfo(c *gin.Context) {
    userID := c.GetString("userID")
    data, err := ctrl.settingsService.GetAccountInfo(c.Request.Context(), userID)
    if err != nil {
        c.Error(err)
        return
    }
    c.JSON(200, data)
}

// internal/domain/service/settings_service.go
type SettingsService interface {
    GetAccountInfo(ctx context.Context, userID string) (*entity.UserDTO, error)
    ChangePassword(ctx context.Context, userID string, req *ChangePasswordRequest) error
}

// internal/domain/service/settings_service_impl.go
type settingsServiceImpl struct {
    userRepo repository.UserRepository
    logger   *zap.Logger
}

func (s *settingsServiceImpl) GetAccountInfo(ctx context.Context, userID string) (*entity.UserDTO, error) {
    user, err := s.userRepo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrNotFoundError("User not found")
    }
    return entity.ToUserDTO(user), nil
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] gRPC service implemented for internal communication
- [ ] Repository pattern properly implemented
- [ ] JWT authentication complete
- [ ] Input validation with struct binding tags
- [ ] ALL Controller Service method calls have corresponding Service implementations
- [ ] ALL gRPC proto methods have server implementations
- [ ] ALL Service->Repository method calls exist in Repository interfaces
- [ ] ALL dependencies registered in fx container

### Performance Checks
- [ ] Use gRPC for internal communication (1.80x faster)
- [ ] Database queries optimized with indexes
- [ ] Connection pooling configured (GORM default)
- [ ] Caching strategy implemented with Redis
- [ ] Context propagation throughout call chain

### Security Checks
- [ ] JWT token validation
- [ ] Role-based access control
- [ ] Input validation complete
- [ ] Password hashing with bcrypt (cost >= 10)
- [ ] No hardcoded secrets
- [ ] TLS configured for production

### Code Quality
- [ ] `go vet` passes
- [ ] `golangci-lint` passes
- [ ] 428+ tests passing (80%+ coverage)
- [ ] Error wrapping with `%w` for tracing
- [ ] Context used consistently

## Common Issues

### gRPC Connection Issues
1. Check protobuf compilation (`protoc` version)
2. Verify service registration in gRPC server
3. Ensure proper error handling with status codes
4. Check TLS certificate configuration

### Database Issues
1. Run GORM AutoMigrate or manual migrations
2. Check connection pool settings (MaxIdleConns, MaxOpenConns)
3. Review query performance with `db.Debug()`
4. Check multi-database DAO configuration

### Testing Issues
1. Use testify mock properly
2. Mock external dependencies with interfaces
3. Test error paths and edge cases
4. Use `context.Background()` in tests

### DI Issues
1. Check `fx.Provide()` registrations
2. Verify constructor function signatures match
3. Check for circular dependencies (fx reports these)
4. Ensure interface types match in providers

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Go | 1.23+ |
| gRPC | 1.60+ |
| Gin | 1.10+ |
| GORM | 2.x |
| fx (Uber) | 1.x |
| Viper | 1.x |
| zap | 1.x |
| Protocol Buffers | 3.x |
| MySQL | 8.0+ |
| PostgreSQL | 15+ |
| MongoDB | 7.0+ |
| Redis | 7.0+ |
| Docker | 24+ |
| Kubernetes | 1.28+ |
| golang-jwt | v5 |
| testify | 1.9+ |
| golangci-lint | 1.55+ |
