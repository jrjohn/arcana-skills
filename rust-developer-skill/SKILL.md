---
name: rust-developer-skill
description: Rust microservices development guide based on Arcana Cloud Rust enterprise architecture. Provides comprehensive support for Clean Architecture, dual-protocol (REST via Axum 0.7 on :8080, gRPC via Tonic 0.12 on :9090), WASM Plugin System (Wasmtime 27), Distributed Job Queue (Redis-backed with 4-level priority), resilience patterns (circuit breaker, retry, rate limiting), JWT + Argon2 + RBAC + mTLS, Prometheus metrics, distributed tracing, and 150 tests. Suitable for Rust microservices development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Rust Developer Skill

Professional Rust microservices development skill based on [Arcana Cloud Rust](https://github.com/jrjohn/arcana-cloud-rust) enterprise architecture. Architecture Rating 8.95/10.

---

## Quick Reference Card

### New REST Endpoint Checklist:
```
1. Add handler function in src/api/handlers/ with Axum extractors
2. Add method to Service trait in src/domain/services/
3. Implement method in ServiceImpl
4. Add Repository trait method if data access needed
5. Add serde Deserialize struct for request validation
6. Register route in src/api/router.rs
7. Verify mock data returns non-empty values
```

### New gRPC Service Checklist:
```
1. Define service in proto/*.proto
2. Run cargo build to generate Rust code via tonic-build
3. Create impl block for generated trait (e.g., impl UserService for UserServiceImpl)
4. Implement ALL rpc methods (count must match proto definitions)
5. Wire to existing Service layer via dependency injection
6. Register with tonic::transport::Server in src/grpc/server.rs
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep -rn "Vec::new()\|return Ok(vec!\[\])" crates/*/src/repository/` |
| 500 error | `grep -rn "unimplemented!\|todo!" crates/*/src/` |
| gRPC UNIMPLEMENTED | Compare `rpc ` count in .proto vs impl methods |
| DI error | Check Arc<dyn Trait> wiring in AppState |
| Borrow checker | `cargo check 2>&1 \| head -50` |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty Vec | `grep -rn "Vec::new()\|vec!\[\]" crates/*/src/repository/` |
| API Wiring | ALL routes must call existing Service methods | Check handler -> service calls |
| gRPC Implementation | ALL proto rpc methods MUST be implemented | Count rpc vs impl methods |
| Type Safety | ALL functions have explicit return types | `cargo clippy -- -D warnings` |
| Ownership Safety | No unsafe blocks without justification | `grep -rn "unsafe " crates/*/src/` |
| Error Propagation | Use Result<T, E> with ? operator, never unwrap() in production | `grep -rn "\.unwrap()" crates/*/src/` |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| Input Validation | Validate all request payloads with serde + custom validators | Check request structs |
| Error Types | Use thiserror for domain errors, map to HTTP/gRPC status | Check error enums |
| Logging | Structured logging via tracing crate | Check tracing::info!/warn!/error! |
| Clippy Clean | Zero clippy warnings | `cargo clippy -- -D warnings` |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| API Documentation | utoipa/OpenAPI annotations |
| Monitoring | Prometheus metrics via metrics crate |
| Caching | Redis caching for hot data |
| Rate Limiting | Tower rate limiting middleware |

---

## Error Handling Pattern

### AppError - Unified Error Model

```rust
// crates/core/src/error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    // Network errors
    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),

    #[error("Request timeout")]
    Timeout,

    // Auth errors
    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Token expired")]
    TokenExpired,

    #[error("Invalid credentials")]
    InvalidCredentials,

    #[error("Forbidden: {0}")]
    Forbidden(String),

    // Data errors
    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Validation failed: {0}")]
    ValidationFailed(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    // General errors
    #[error("Internal error: {0}")]
    Internal(String),

    // Database errors
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    // Redis errors
    #[error("Cache error: {0}")]
    Cache(String),
}

impl AppError {
    pub fn status_code(&self) -> u16 {
        match self {
            AppError::Unauthorized(_) | AppError::TokenExpired | AppError::InvalidCredentials => 401,
            AppError::Forbidden(_) => 403,
            AppError::NotFound(_) => 404,
            AppError::ValidationFailed(_) => 400,
            AppError::Conflict(_) => 409,
            AppError::Timeout => 408,
            AppError::ServiceUnavailable(_) => 503,
            _ => 500,
        }
    }

    pub fn error_code(&self) -> &str {
        match self {
            AppError::Unauthorized(_) => "UNAUTHORIZED",
            AppError::TokenExpired => "TOKEN_EXPIRED",
            AppError::InvalidCredentials => "INVALID_CREDENTIALS",
            AppError::Forbidden(_) => "FORBIDDEN",
            AppError::NotFound(_) => "NOT_FOUND",
            AppError::ValidationFailed(_) => "VALIDATION_FAILED",
            AppError::Conflict(_) => "CONFLICT",
            AppError::Timeout => "TIMEOUT",
            AppError::ServiceUnavailable(_) => "SERVICE_UNAVAILABLE",
            _ => "INTERNAL_ERROR",
        }
    }
}
```

### Axum IntoResponse Implementation

```rust
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde_json::json;

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let status = StatusCode::from_u16(self.status_code())
            .unwrap_or(StatusCode::INTERNAL_SERVER_ERROR);

        let body = json!({
            "code": self.error_code(),
            "message": self.to_string(),
            "timestamp": chrono::Utc::now().to_rfc3339(),
        });

        (status, Json(body)).into_response()
    }
}
```

### gRPC Status Mapping

```rust
impl From<AppError> for tonic::Status {
    fn from(err: AppError) -> Self {
        let code = match &err {
            AppError::NotFound(_) => tonic::Code::NotFound,
            AppError::Unauthorized(_) | AppError::TokenExpired => tonic::Code::Unauthenticated,
            AppError::Forbidden(_) => tonic::Code::PermissionDenied,
            AppError::ValidationFailed(_) => tonic::Code::InvalidArgument,
            AppError::Conflict(_) => tonic::Code::AlreadyExists,
            AppError::Timeout => tonic::Code::DeadlineExceeded,
            AppError::ServiceUnavailable(_) => tonic::Code::Unavailable,
            _ => tonic::Code::Internal,
        };
        tonic::Status::new(code, err.to_string())
    }
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| Service | 90%+ | Business logic, edge cases, error paths |
| Repository | 80%+ | Data mapping, SQL correctness |
| Handler | 75%+ | Request parsing, validation, status codes |
| Integration | 70%+ | End-to-end flows, auth, gRPC |

### Test Commands
```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test module
cargo test --package arcana-core -- service::user::tests

# Run integration tests
cargo test --test integration

# View coverage (requires cargo-tarpaulin)
cargo tarpaulin --out html
open tarpaulin-report.html
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
| User | PATCH /api/v1/users/:id | Check |

### Response State Prediction

For every endpoint, predict required response states:

```rust
// Predicted states for GET /api/v1/users/:id:
// 200 OK - User found -> Ok(Json(user_dto))
// 404 Not Found - User doesn't exist -> Err(AppError::NotFound(...))
// 401 Unauthorized - Not logged in -> Err(AppError::Unauthorized(...))
// 403 Forbidden - No permission -> Err(AppError::Forbidden(...))
// 500 Internal Server Error -> Err(AppError::Internal(...))
```

### Pagination Prediction

List endpoints SHOULD support pagination:

```rust
// GET /api/v1/users
// Predicted query parameters:
#[derive(Debug, Deserialize)]
pub struct PaginationParams {
    pub page: Option<u32>,    // default = 0
    pub size: Option<u32>,    // default = 10
    pub sort: Option<String>, // default = "created_at"
    pub order: Option<String>, // "asc" | "desc", default = "desc"
}
```

### Ask Clarification Prompt

When specs are incomplete, ASK before implementing:

```
The specification mentions "User API" but doesn't specify:
1. Should DELETE be soft-delete or hard-delete?
2. What fields are required for user creation?
3. Is email verification required?
4. What roles/permissions exist?
5. Should we use UUID or auto-increment IDs?

Please clarify before I proceed with implementation.
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
+-----------------------------------------------------+
|                  API Layer (Handlers)                 |
|       Axum 0.7 (REST :8080) + Tonic 0.12 (gRPC :9090)|
|       JWT Auth + Request Validation                  |
+-----------------------------------------------------+
|                  Domain Layer (Services)              |
|       Business Logic + Domain Events                 |
|       Trait-based interfaces + async/await            |
+-----------------------------------------------------+
|              Infrastructure Layer (Repos)             |
|       SQLx (MySQL/PostgreSQL) + Redis                |
|       WASM Plugin Host + Job Queue                   |
+-----------------------------------------------------+
```

### Deployment Modes

1. **Monolithic**: Single binary, direct function calls (development) - 0.5ms latency
2. **Layered**: Separate containers per layer with gRPC between layers
3. **Microservices**: Fine-grained services with independent scaling (Kubernetes)
4. **Hybrid gRPC+REST**: REST for external, gRPC for internal (production default)
5. **WASM Plugin**: Extend via hot-loaded WASM modules (Wasmtime 27)

### Performance Benchmarks

| Protocol | Latency | Throughput | Use Case |
|----------|---------|------------|----------|
| Direct call | ~0.5ms | Maximum | Monolithic |
| gRPC (Tonic) | ~1.2ms | 2.1x vs HTTP | Internal services |
| HTTP/JSON (Axum) | ~2.5ms | Baseline | External APIs |

---

## Instructions

When handling Rust microservices development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented methods (MUST be empty)
grep -rn "unimplemented!\|todo!\|// TODO" crates/*/src/

# 2. Check for unwrap() in production code (MUST be empty)
grep -rn "\.unwrap()" crates/*/src/ | grep -v "test" | grep -v "#\[cfg(test)\]"

# 3. Check all routes have handlers
echo "Routes defined:" && grep -c "\.route\|\.get\|\.post\|\.put\|\.delete" crates/*/src/api/*.rs 2>/dev/null || echo 0
echo "Handler functions:" && grep -c "pub async fn" crates/*/src/api/handlers/*.rs 2>/dev/null || echo 0

# 4. Check gRPC services are implemented
echo "gRPC methods defined in proto:" && grep -c "rpc " proto/*.proto 2>/dev/null || echo 0
echo "gRPC methods implemented:" && grep -c "async fn" crates/*/src/grpc/*.rs 2>/dev/null || echo 0

# 5. Verify tests pass
cargo test

# 6. Check Handler routes call existing Service methods (CRITICAL!)
echo "=== Service Methods Called in Handlers ===" && \
grep -roh "self\.\w*service\.\w*(" crates/*/src/api/handlers/*.rs | sort -u
echo "=== Service Trait Methods ===" && \
grep -rh "async fn \w*(" crates/*/src/domain/services/*.rs | sort -u

# 7. Check for unsafe code blocks
grep -rn "unsafe " crates/*/src/ | grep -v "test"

# 8. Clippy lint check
cargo clippy -- -D warnings

# 9. Check Service -> Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "self\.\w*repo\w*\.\w*(" crates/*/src/domain/services/*.rs | sort -u
echo "=== Repository Trait Methods ===" && \
grep -rh "async fn \w*(" crates/*/src/domain/repositories/*.rs | sort -u

# 10. Check AppState dependency injection
echo "=== AppState Fields ===" && \
grep -A 20 "pub struct AppState" crates/*/src/

# 11. Type checking
cargo check

# 12. Format check
cargo fmt -- --check
```

**CRITICAL**: All routes MUST have corresponding handler functions. All gRPC methods defined in .proto files MUST be implemented. Every `.unwrap()` in non-test code is a potential panic.

**API WIRING CRITICAL**: Commands #6 and #9 detect handlers that call service methods that don't exist. A handler can call `self.user_service.get_account_info()` but if the service trait doesn't have this method, it fails at compile time in Rust -- but if using dynamic dispatch with `dyn Any`, it may fail at runtime.

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty Vecs for data that powers UI charts or API responses**. This causes:
- Frontend charts that render but show nothing
- API responses with empty data arrays
- Client applications showing "No data" even when structure exists

### Mock Data Rules

**Rule 1: List data for charts MUST have at least 7 items**
```rust
// BAD - Chart will be blank
async fn get_weekly_summary(&self, user_id: &str) -> Result<WeeklySummary, AppError> {
    Ok(WeeklySummary {
        daily_reports: vec![], // Chart has no data!
    })
}

// GOOD - Chart has data to display
async fn get_weekly_summary(&self, user_id: &str) -> Result<WeeklySummary, AppError> {
    let scores = [72, 78, 85, 80, 76, 88, 82];
    let durations = [390, 420, 450, 410, 380, 460, 435];
    let daily_reports: Vec<DailyReport> = scores
        .iter()
        .zip(durations.iter())
        .map(|(&score, &duration)| DailyReport::mock(score, duration))
        .collect();
    Ok(WeeklySummary { daily_reports })
}
```

**Rule 2: Use realistic, varied sample values**
```rust
// BAD - Monotonous test data
let scores = vec![80; 7];

// GOOD - Realistic variation
let scores = vec![72, 78, 85, 80, 76, 88, 82]; // Shows trend
```

**Rule 3: Data must match struct exactly**
```bash
# Before creating mock data, ALWAYS verify the struct:
grep -A 20 "pub struct WeeklySummary" crates/*/src/domain/models/*.rs
```

**Rule 4: Create builder/mock methods for complex data**
```rust
impl DailyReport {
    pub fn mock(score: i32, duration: i32) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            score,
            duration_minutes: duration,
            created_at: chrono::Utc::now(),
            ..Default::default()
        }
    }
}
```

### Quick Verification Commands for Mock Data

```bash
# Check for empty Vec returns in Repository stubs (MUST FIX)
grep -rn "Vec::new()\|vec!\[\]" crates/*/src/repository/*_impl.rs

# Verify chart-related data has mock values
grep -rn "daily_reports\|weekly_data\|chart_data" crates/*/src/repository/ | grep -E "Vec::new|vec!\[\]"
```

---

### 0. Project Setup - CRITICAL

**IMPORTANT**: This reference project has been validated with a tested Cargo.toml workspace and gRPC/protobuf settings. **NEVER reconfigure project structure or modify Cargo.toml dependencies**, or it will cause build errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-cloud-rust.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-cloud-rust template"
```

**Step 3**: Modify project name
Only modify the following required items:
- Workspace name in root `Cargo.toml`
- Application name in `crates/server/src/config.rs`
- Service names in Docker-related configuration files
- Update settings in `.env.example` file
- Proto package names in `proto/*.proto`

**Step 4**: Clean up example code
The cloned project contains example API. Clean up and replace with new project business logic:

**Core architecture files to KEEP** (do not delete):
- `config/` - YAML configuration files
- `crates/core/src/error.rs` - Error types
- `crates/core/src/config.rs` - Configuration loading
- `crates/server/src/middleware/` - Auth, tracing, metrics middleware
- `crates/server/src/grpc/` - gRPC server configuration
- `deployment/` - Docker & K8s manifests
- `migrations/` - SQLx migrations
- `scripts/` - Build and deployment scripts

**Example files to REPLACE**:
- `crates/server/src/api/handlers/` - Delete example handlers, create new ones
- `crates/core/src/domain/services/` - Delete example services, create new business logic
- `crates/core/src/domain/repositories/` - Delete example repos, create new data access
- `crates/core/src/domain/models/` - Delete example models, create new domain models
- `proto/*.proto` - Modify gRPC proto definitions
- `crates/core/tests/` - Update test cases

**Step 5**: Build and verify
```bash
cargo build
cargo test
cargo clippy -- -D warnings
```

### Prohibited Actions
- **DO NOT** create new Rust project from scratch (`cargo new`)
- **DO NOT** modify version numbers in `Cargo.toml` workspace
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify tonic-build or protobuf compilation settings
- **DO NOT** reconfigure SQLx, Wasmtime, or other library settings
- **DO NOT** use `unsafe` without explicit justification

### Allowed Modifications
- Add business-related Rust code (following existing architecture)
- Add handlers, services, repositories
- Add domain models and DTOs
- Add SQLx migration scripts
- Modify gRPC proto files (and rebuild)
- Add WASM plugin modules

---

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

**CRITICAL**: All development MUST follow this TDD workflow. Every SRS/SDD requirement must have corresponding tests BEFORE implementation.

**ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
+---------------------------------------------------------------+
|                    TDD Development Workflow                     |
+---------------------------------------------------------------+
|  Step 1: Analyze Spec -> Extract all SRS & SDD requirements    |
|  Step 2: Create Tests -> Write tests for EACH Spec item        |
|  Step 3: Verify Coverage -> Ensure 100% Spec coverage in tests |
|  Step 4: Implement -> Build features to pass tests  MANDATORY  |
|  Step 5: Mock APIs -> Use mock data for unfinished deps        |
|  Step 6: Run All Tests -> ALL tests must pass before completion|
|  Step 7: Verify 100% -> Tests written = Features implemented   |
+---------------------------------------------------------------+
```

#### FORBIDDEN: Tests Without Implementation

```rust
// WRONG - Test exists but no implementation
// Test file exists: user_service_test.rs (32 tests)
// Production file: user_service.rs -> uses unimplemented!()
// This is INCOMPLETE TDD!

// CORRECT - Test AND Implementation both exist
// Test file: user_service_test.rs (32 tests)
// Production file: user_service.rs (fully implemented)
// All 32 tests PASS
```

#### Placeholder Endpoint Policy

Placeholder endpoints are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```rust
// WRONG - Placeholder endpoint left in production
async fn get_training() -> impl IntoResponse {
    Json(json!({"message": "Coming Soon"})) // FORBIDDEN!
}

// CORRECT - Real endpoint implementation
async fn get_training(
    State(state): State<AppState>,
) -> Result<Json<Vec<TrainingDto>>, AppError> {
    let data = state.training_service.get_all().await?;
    Ok(Json(data))
}
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "unimplemented!\|todo!\|Coming Soon" crates/*/src/
```

---

### 2. Project Structure

```
arcana-cloud-rust/
+-- config/                    # YAML configuration files
|   +-- default.yaml
|   +-- production.yaml
+-- crates/                    # Rust workspace crates
|   +-- core/                  # Domain logic crate
|   |   +-- src/
|   |   |   +-- domain/
|   |   |   |   +-- models/    # Domain models
|   |   |   |   +-- services/  # Business logic (traits + impls)
|   |   |   |   +-- repositories/ # Repository traits
|   |   |   +-- error.rs       # AppError enum
|   |   |   +-- config.rs      # Configuration structs
|   |   +-- tests/             # Unit tests
|   +-- server/                # Server crate (binary)
|   |   +-- src/
|   |   |   +-- api/
|   |   |   |   +-- handlers/  # Axum route handlers
|   |   |   |   +-- router.rs  # Route definitions
|   |   |   |   +-- middleware/ # Tower middleware
|   |   |   +-- grpc/          # Tonic gRPC services
|   |   |   +-- infrastructure/
|   |   |   |   +-- db/        # SQLx repository implementations
|   |   |   |   +-- cache/     # Redis cache
|   |   |   |   +-- queue/     # Job queue (Redis-backed)
|   |   |   +-- plugins/       # WASM plugin host
|   |   |   +-- main.rs        # Entry point
|   +-- migration/             # SQLx migration crate
+-- deployment/                # Docker & K8s manifests
|   +-- docker/
|   +-- k8s/
+-- migrations/                # SQL migration files
+-- plugins/
|   +-- arcana-audit-plugin/   # WASM audit plugin
+-- proto/                     # Protocol Buffer definitions
|   +-- user.proto
|   +-- health.proto
+-- scripts/                   # Build and deploy scripts
+-- Cargo.toml                 # Workspace root
+-- build.rs                   # tonic-build proto compilation
```

---

### 3. Domain Model

```rust
// crates/core/src/domain/models/user.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "sync_status", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SyncStatus {
    Synced,
    Pending,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub name: String,
    pub email: String,
    pub password_hash: String,
    pub sync_status: SyncStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserDto {
    pub id: String,
    pub name: String,
    pub email: String,
    pub created_at: String,
    pub updated_at: String,
}

impl From<User> for UserDto {
    fn from(user: User) -> Self {
        Self {
            id: user.id.to_string(),
            name: user.name,
            email: user.email,
            created_at: user.created_at.to_rfc3339(),
            updated_at: user.updated_at.to_rfc3339(),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateUserRequest {
    pub name: String,
    pub email: String,
    pub password: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UpdateUserRequest {
    pub name: Option<String>,
    pub email: Option<String>,
}
```

---

### 4. Repository Layer

```rust
// crates/core/src/domain/repositories/user_repository.rs
use async_trait::async_trait;
use uuid::Uuid;
use crate::domain::models::user::{User, SyncStatus};
use crate::error::AppError;

#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, AppError>;
    async fn find_by_email(&self, email: &str) -> Result<Option<User>, AppError>;
    async fn find_all(&self, page: u32, size: u32) -> Result<(Vec<User>, i64), AppError>;
    async fn find_pending_sync(&self) -> Result<Vec<User>, AppError>;
    async fn save(&self, user: &User) -> Result<User, AppError>;
    async fn update(&self, user: &User) -> Result<User, AppError>;
    async fn delete(&self, id: Uuid) -> Result<(), AppError>;
}

// crates/server/src/infrastructure/db/user_repository_impl.rs
use async_trait::async_trait;
use sqlx::PgPool;
use uuid::Uuid;
use arcana_core::domain::models::user::{User, SyncStatus};
use arcana_core::domain::repositories::user_repository::UserRepository;
use arcana_core::error::AppError;

pub struct PgUserRepository {
    pool: PgPool,
}

impl PgUserRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl UserRepository for PgUserRepository {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, AppError> {
        let user = sqlx::query_as::<_, User>(
            "SELECT * FROM users WHERE id = $1"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;
        Ok(user)
    }

    async fn find_by_email(&self, email: &str) -> Result<Option<User>, AppError> {
        let user = sqlx::query_as::<_, User>(
            "SELECT * FROM users WHERE email = $1"
        )
        .bind(email)
        .fetch_optional(&self.pool)
        .await?;
        Ok(user)
    }

    async fn find_all(&self, page: u32, size: u32) -> Result<(Vec<User>, i64), AppError> {
        let offset = (page * size) as i64;
        let limit = size as i64;

        let users = sqlx::query_as::<_, User>(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2"
        )
        .bind(limit)
        .bind(offset)
        .fetch_all(&self.pool)
        .await?;

        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
            .fetch_one(&self.pool)
            .await?;

        Ok((users, total.0))
    }

    async fn find_pending_sync(&self) -> Result<Vec<User>, AppError> {
        let users = sqlx::query_as::<_, User>(
            "SELECT * FROM users WHERE sync_status = 'PENDING'"
        )
        .fetch_all(&self.pool)
        .await?;
        Ok(users)
    }

    async fn save(&self, user: &User) -> Result<User, AppError> {
        let saved = sqlx::query_as::<_, User>(
            r#"INSERT INTO users (id, name, email, password_hash, sync_status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING *"#
        )
        .bind(user.id)
        .bind(&user.name)
        .bind(&user.email)
        .bind(&user.password_hash)
        .bind(&user.sync_status)
        .bind(user.created_at)
        .bind(user.updated_at)
        .fetch_one(&self.pool)
        .await?;
        Ok(saved)
    }

    async fn update(&self, user: &User) -> Result<User, AppError> {
        let updated = sqlx::query_as::<_, User>(
            r#"UPDATE users SET name = $2, email = $3, password_hash = $4,
               sync_status = $5, updated_at = $6
               WHERE id = $1 RETURNING *"#
        )
        .bind(user.id)
        .bind(&user.name)
        .bind(&user.email)
        .bind(&user.password_hash)
        .bind(&user.sync_status)
        .bind(chrono::Utc::now())
        .fetch_one(&self.pool)
        .await?;
        Ok(updated)
    }

    async fn delete(&self, id: Uuid) -> Result<(), AppError> {
        sqlx::query("DELETE FROM users WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;
        Ok(())
    }
}
```

---

### 5. Service Layer

```rust
// crates/core/src/domain/services/user_service.rs
use async_trait::async_trait;
use uuid::Uuid;
use crate::domain::models::user::*;
use crate::domain::repositories::user_repository::UserRepository;
use crate::error::AppError;
use std::sync::Arc;

#[async_trait]
pub trait UserService: Send + Sync {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError>;
    async fn get_users(&self, page: u32, size: u32) -> Result<PaginatedResponse<UserDto>, AppError>;
    async fn create_user(&self, req: CreateUserRequest) -> Result<UserDto, AppError>;
    async fn update_user(&self, id: Uuid, req: UpdateUserRequest) -> Result<Option<UserDto>, AppError>;
    async fn delete_user(&self, id: Uuid) -> Result<bool, AppError>;
    async fn authenticate(&self, email: &str, password: &str) -> Result<Option<User>, AppError>;
}

pub struct UserServiceImpl {
    repo: Arc<dyn UserRepository>,
}

impl UserServiceImpl {
    pub fn new(repo: Arc<dyn UserRepository>) -> Self {
        Self { repo }
    }
}

#[async_trait]
impl UserService for UserServiceImpl {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError> {
        let user = self.repo.find_by_id(id).await?;
        Ok(user.map(UserDto::from))
    }

    async fn get_users(&self, page: u32, size: u32) -> Result<PaginatedResponse<UserDto>, AppError> {
        let (users, total) = self.repo.find_all(page, size).await?;
        Ok(PaginatedResponse {
            data: users.into_iter().map(UserDto::from).collect(),
            page,
            size,
            total,
        })
    }

    async fn create_user(&self, req: CreateUserRequest) -> Result<UserDto, AppError> {
        // Check if email already exists
        if let Some(_) = self.repo.find_by_email(&req.email).await? {
            return Err(AppError::Conflict("Email already registered".into()));
        }

        let password_hash = argon2::hash_encoded(
            req.password.as_bytes(),
            &uuid::Uuid::new_v4().as_bytes()[..16],
            &argon2::Config::default(),
        ).map_err(|e| AppError::Internal(e.to_string()))?;

        let user = User {
            id: Uuid::new_v4(),
            name: req.name,
            email: req.email,
            password_hash,
            sync_status: SyncStatus::Synced,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };

        let saved = self.repo.save(&user).await?;
        Ok(UserDto::from(saved))
    }

    async fn update_user(&self, id: Uuid, req: UpdateUserRequest) -> Result<Option<UserDto>, AppError> {
        let mut user = match self.repo.find_by_id(id).await? {
            Some(u) => u,
            None => return Ok(None),
        };

        if let Some(name) = req.name {
            user.name = name;
        }
        if let Some(email) = req.email {
            if let Some(existing) = self.repo.find_by_email(&email).await? {
                if existing.id != id {
                    return Err(AppError::Conflict("Email already registered".into()));
                }
            }
            user.email = email;
        }

        let updated = self.repo.update(&user).await?;
        Ok(Some(UserDto::from(updated)))
    }

    async fn delete_user(&self, id: Uuid) -> Result<bool, AppError> {
        match self.repo.find_by_id(id).await? {
            Some(_) => {
                self.repo.delete(id).await?;
                Ok(true)
            }
            None => Ok(false),
        }
    }

    async fn authenticate(&self, email: &str, password: &str) -> Result<Option<User>, AppError> {
        let user = match self.repo.find_by_email(email).await? {
            Some(u) => u,
            None => return Ok(None),
        };

        let valid = argon2::verify_encoded(&user.password_hash, password.as_bytes())
            .unwrap_or(false);

        if valid {
            Ok(Some(user))
        } else {
            Ok(None)
        }
    }
}
```

---

### 6. Handler Layer (Axum)

```rust
// crates/server/src/api/handlers/user_handler.rs
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use uuid::Uuid;
use crate::api::middleware::auth::Claims;
use crate::AppState;
use arcana_core::domain::models::user::*;
use arcana_core::error::AppError;

pub async fn get_user(
    State(state): State<AppState>,
    Path(user_id): Path<Uuid>,
    _claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    let user = state.user_service.get_user(user_id).await?;
    match user {
        Some(dto) => Ok(Json(dto)),
        None => Err(AppError::NotFound("User not found".into())),
    }
}

pub async fn list_users(
    State(state): State<AppState>,
    Query(params): Query<PaginationParams>,
    _claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    let page = params.page.unwrap_or(0);
    let size = params.size.unwrap_or(10);
    let result = state.user_service.get_users(page, size).await?;
    Ok(Json(result))
}

pub async fn create_user(
    State(state): State<AppState>,
    _claims: Claims,
    Json(req): Json<CreateUserRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user = state.user_service.create_user(req).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

pub async fn update_user(
    State(state): State<AppState>,
    Path(user_id): Path<Uuid>,
    _claims: Claims,
    Json(req): Json<UpdateUserRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user = state.user_service.update_user(user_id, req).await?;
    match user {
        Some(dto) => Ok(Json(dto)),
        None => Err(AppError::NotFound("User not found".into())),
    }
}

pub async fn delete_user(
    State(state): State<AppState>,
    Path(user_id): Path<Uuid>,
    _claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    let deleted = state.user_service.delete_user(user_id).await?;
    if deleted {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(AppError::NotFound("User not found".into()))
    }
}
```

### Router Setup

```rust
// crates/server/src/api/router.rs
use axum::{
    routing::{get, post, put, delete},
    Router,
};
use crate::api::handlers::user_handler;
use crate::api::middleware::auth::jwt_layer;
use crate::AppState;

pub fn create_router(state: AppState) -> Router {
    let api_v1 = Router::new()
        .route("/users", get(user_handler::list_users).post(user_handler::create_user))
        .route(
            "/users/:id",
            get(user_handler::get_user)
                .put(user_handler::update_user)
                .delete(user_handler::delete_user),
        )
        .layer(jwt_layer(state.jwt_secret.clone()));

    Router::new()
        .nest("/api/v1", api_v1)
        .route("/health", get(|| async { "OK" }))
        .route("/metrics", get(crate::api::handlers::metrics_handler))
        .with_state(state)
}
```

---

### 7. Dependency Injection (AppState)

```rust
// crates/server/src/state.rs
use std::sync::Arc;
use arcana_core::domain::services::user_service::UserService;
use arcana_core::domain::services::auth_service::AuthService;
use crate::infrastructure::cache::RedisCache;
use crate::plugins::PluginHost;
use crate::infrastructure::queue::JobQueue;

#[derive(Clone)]
pub struct AppState {
    pub user_service: Arc<dyn UserService>,
    pub auth_service: Arc<dyn AuthService>,
    pub cache: Arc<RedisCache>,
    pub plugin_host: Arc<PluginHost>,
    pub job_queue: Arc<JobQueue>,
    pub jwt_secret: String,
}

impl AppState {
    pub async fn new(config: &Config) -> Result<Self, AppError> {
        // Database pool
        let pool = PgPoolOptions::new()
            .max_connections(config.database.max_connections)
            .connect(&config.database.url)
            .await?;

        // Redis
        let redis = redis::Client::open(config.redis.url.as_str())?;
        let cache = Arc::new(RedisCache::new(redis));

        // Repositories
        let user_repo = Arc::new(PgUserRepository::new(pool.clone()));
        let token_repo = Arc::new(PgRefreshTokenRepository::new(pool.clone()));

        // Services
        let user_service = Arc::new(UserServiceImpl::new(user_repo.clone()));
        let auth_service = Arc::new(AuthServiceImpl::new(
            user_repo.clone(),
            token_repo,
            config.jwt.secret.clone(),
        ));

        // WASM Plugin Host
        let plugin_host = Arc::new(PluginHost::new(&config.plugins).await?);

        // Job Queue
        let job_queue = Arc::new(JobQueue::new(cache.clone()));

        Ok(Self {
            user_service,
            auth_service,
            cache,
            plugin_host,
            job_queue,
            jwt_secret: config.jwt.secret.clone(),
        })
    }
}
```

---

### 8. JWT Authentication Middleware

```rust
// crates/server/src/api/middleware/auth.rs
use axum::{
    extract::FromRequestParts,
    http::{header, request::Parts, StatusCode},
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use arcana_core::error::AppError;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,       // user id
    pub roles: Vec<String>,
    pub exp: usize,        // expiration timestamp
    pub iat: usize,        // issued at
}

impl Claims {
    pub fn new(user_id: &str, roles: Vec<String>, expires_in_secs: u64) -> Self {
        let now = chrono::Utc::now().timestamp() as usize;
        Self {
            sub: user_id.to_string(),
            roles,
            exp: now + expires_in_secs as usize,
            iat: now,
        }
    }

    pub fn has_role(&self, role: &str) -> bool {
        self.roles.iter().any(|r| r == role)
    }
}

pub fn create_access_token(user_id: &str, roles: Vec<String>, secret: &str) -> Result<String, AppError> {
    let claims = Claims::new(user_id, roles, 86400); // 24 hours
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| AppError::Internal(format!("Token creation failed: {}", e)))
}

pub fn verify_token(token: &str, secret: &str) -> Result<Claims, AppError> {
    decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::default(),
    )
    .map(|data| data.claims)
    .map_err(|e| match e.kind() {
        jsonwebtoken::errors::ErrorKind::ExpiredSignature => AppError::TokenExpired,
        _ => AppError::Unauthorized(format!("Invalid token: {}", e)),
    })
}

#[axum::async_trait]
impl<S> FromRequestParts<S> for Claims
where
    S: Send + Sync,
{
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let auth_header = parts
            .headers
            .get(header::AUTHORIZATION)
            .and_then(|value| value.to_str().ok())
            .ok_or_else(|| AppError::Unauthorized("Missing authorization header".into()))?;

        if !auth_header.starts_with("Bearer ") {
            return Err(AppError::Unauthorized("Invalid authorization scheme".into()));
        }

        let token = &auth_header[7..];
        let secret = parts
            .extensions
            .get::<String>()
            .ok_or_else(|| AppError::Internal("JWT secret not configured".into()))?;

        verify_token(token, secret)
    }
}
```

---

### 9. Database Migrations with SQLx

```bash
# Create new migration
sqlx migrate add create_users_table

# Apply migrations
sqlx migrate run --database-url $DATABASE_URL

# Revert last migration
sqlx migrate revert --database-url $DATABASE_URL

# Check migration status
sqlx migrate info --database-url $DATABASE_URL

# Prepare offline query data (for CI builds)
cargo sqlx prepare --database-url $DATABASE_URL
```

```sql
-- migrations/001_create_users_table.sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    sync_status VARCHAR(20) NOT NULL DEFAULT 'SYNCED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_sync_status ON users(sync_status);
```

---

### 10. Testing

```rust
// crates/core/tests/service/user_service_test.rs
#[cfg(test)]
mod tests {
    use super::*;
    use async_trait::async_trait;
    use mockall::predicate::*;
    use mockall::mock;
    use std::sync::Arc;
    use uuid::Uuid;

    mock! {
        pub UserRepo {}

        #[async_trait]
        impl UserRepository for UserRepo {
            async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, AppError>;
            async fn find_by_email(&self, email: &str) -> Result<Option<User>, AppError>;
            async fn find_all(&self, page: u32, size: u32) -> Result<(Vec<User>, i64), AppError>;
            async fn find_pending_sync(&self) -> Result<Vec<User>, AppError>;
            async fn save(&self, user: &User) -> Result<User, AppError>;
            async fn update(&self, user: &User) -> Result<User, AppError>;
            async fn delete(&self, id: Uuid) -> Result<(), AppError>;
        }
    }

    fn mock_user() -> User {
        User {
            id: Uuid::new_v4(),
            name: "John Doe".to_string(),
            email: "john@example.com".to_string(),
            password_hash: "hashed".to_string(),
            sync_status: SyncStatus::Synced,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        }
    }

    #[tokio::test]
    async fn test_get_user_found() {
        let mut mock_repo = MockUserRepo::new();
        let user = mock_user();
        let user_id = user.id;

        mock_repo
            .expect_find_by_id()
            .with(eq(user_id))
            .times(1)
            .returning(move |_| Ok(Some(user.clone())));

        let service = UserServiceImpl::new(Arc::new(mock_repo));
        let result = service.get_user(user_id).await.unwrap();

        assert!(result.is_some());
        assert_eq!(result.unwrap().name, "John Doe");
    }

    #[tokio::test]
    async fn test_get_user_not_found() {
        let mut mock_repo = MockUserRepo::new();

        mock_repo
            .expect_find_by_id()
            .times(1)
            .returning(|_| Ok(None));

        let service = UserServiceImpl::new(Arc::new(mock_repo));
        let result = service.get_user(Uuid::new_v4()).await.unwrap();

        assert!(result.is_none());
    }

    #[tokio::test]
    async fn test_create_user_duplicate_email() {
        let mut mock_repo = MockUserRepo::new();

        mock_repo
            .expect_find_by_email()
            .with(eq("john@example.com"))
            .times(1)
            .returning(|_| Ok(Some(mock_user())));

        let service = UserServiceImpl::new(Arc::new(mock_repo));
        let result = service
            .create_user(CreateUserRequest {
                name: "John Doe".to_string(),
                email: "john@example.com".to_string(),
                password: "password123".to_string(),
            })
            .await;

        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), AppError::Conflict(_)));
    }
}
```

---

## WASM Plugin System

### Plugin Architecture (Wasmtime 27)

```
+------------------+     +-------------------+     +------------------+
|  Plugin Host     | --> |  WASM Runtime     | --> |  Plugin Module   |
|  (Rust native)   |     |  (Wasmtime 27)    |     |  (.wasm binary)  |
+------------------+     +-------------------+     +------------------+
        |                         |                         |
   Plugin API              Sandboxed exec            Plugin logic
   Registration            Memory isolation          Audit, Transform
   Hot-reloading           Resource limits           Custom business
```

### Plugin Host

```rust
// crates/server/src/plugins/host.rs
use wasmtime::*;
use std::path::Path;

pub struct PluginHost {
    engine: Engine,
    plugins: Vec<LoadedPlugin>,
}

pub struct LoadedPlugin {
    pub name: String,
    pub module: Module,
    pub instance: Instance,
}

impl PluginHost {
    pub async fn new(config: &PluginConfig) -> Result<Self, AppError> {
        let engine = Engine::default();
        let mut plugins = Vec::new();

        for plugin_path in &config.paths {
            let module = Module::from_file(&engine, plugin_path)
                .map_err(|e| AppError::Internal(format!("Failed to load plugin: {}", e)))?;

            let mut store = Store::new(&engine, ());
            let instance = Instance::new(&mut store, &module, &[])
                .map_err(|e| AppError::Internal(format!("Failed to instantiate plugin: {}", e)))?;

            plugins.push(LoadedPlugin {
                name: Path::new(plugin_path)
                    .file_stem()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string(),
                module,
                instance,
            });
        }

        Ok(Self { engine, plugins })
    }

    pub fn execute_audit(&self, event: &AuditEvent) -> Result<(), AppError> {
        for plugin in &self.plugins {
            // Call plugin audit function
            tracing::info!(plugin = %plugin.name, "Executing audit plugin");
        }
        Ok(())
    }
}
```

### WASM Plugin Example

```rust
// plugins/arcana-audit-plugin/src/lib.rs
#[no_mangle]
pub extern "C" fn on_audit_event(event_ptr: *const u8, event_len: usize) -> i32 {
    // Parse event data from shared memory
    let event_bytes = unsafe { std::slice::from_raw_parts(event_ptr, event_len) };
    let event: AuditEvent = match serde_json::from_slice(event_bytes) {
        Ok(e) => e,
        Err(_) => return -1,
    };

    // Process audit event
    match event.event_type.as_str() {
        "user.login" => handle_login_audit(&event),
        "user.data_access" => handle_data_access_audit(&event),
        "admin.config_change" => handle_config_change_audit(&event),
        _ => 0,
    }
}
```

---

## Distributed Job Queue

### Redis-backed Job Queue with 4-level Priority

```rust
// crates/server/src/infrastructure/queue/job_queue.rs
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum JobPriority {
    Critical = 0,  // Process immediately
    High = 1,      // Process within seconds
    Normal = 2,    // Process within minutes
    Low = 3,       // Process when idle
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Job {
    pub id: String,
    pub job_type: String,
    pub payload: serde_json::Value,
    pub priority: JobPriority,
    pub max_retries: u32,
    pub retry_count: u32,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub scheduled_at: Option<chrono::DateTime<chrono::Utc>>,
}

pub struct JobQueue {
    redis: Arc<redis::Client>,
}

impl JobQueue {
    pub fn new(redis: Arc<redis::Client>) -> Self {
        Self { redis }
    }

    pub async fn enqueue(&self, job: Job) -> Result<String, AppError> {
        let mut conn = self.redis.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        let queue_key = format!("jobs:queue:{}", job.priority as u8);
        let job_data = serde_json::to_string(&job)
            .map_err(|e| AppError::Internal(e.to_string()))?;

        conn.lpush::<_, _, ()>(&queue_key, &job_data).await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        tracing::info!(job_id = %job.id, job_type = %job.job_type, priority = ?job.priority, "Job enqueued");
        Ok(job.id)
    }

    pub async fn dequeue(&self) -> Result<Option<Job>, AppError> {
        let mut conn = self.redis.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        // Try queues in priority order: Critical -> High -> Normal -> Low
        for priority in 0..=3u8 {
            let queue_key = format!("jobs:queue:{}", priority);
            let result: Option<String> = conn.rpop(&queue_key, None).await
                .map_err(|e| AppError::Cache(e.to_string()))?;

            if let Some(job_data) = result {
                let job: Job = serde_json::from_str(&job_data)
                    .map_err(|e| AppError::Internal(e.to_string()))?;
                return Ok(Some(job));
            }
        }

        Ok(None)
    }
}
```

### Job Worker

```rust
// crates/server/src/infrastructure/queue/worker.rs
pub struct JobWorker {
    queue: Arc<JobQueue>,
    handlers: HashMap<String, Box<dyn JobHandler>>,
}

#[async_trait]
pub trait JobHandler: Send + Sync {
    async fn handle(&self, job: &Job) -> Result<(), AppError>;
}

impl JobWorker {
    pub async fn run(&self) -> Result<(), AppError> {
        loop {
            match self.queue.dequeue().await? {
                Some(job) => {
                    if let Some(handler) = self.handlers.get(&job.job_type) {
                        match handler.handle(&job).await {
                            Ok(()) => {
                                tracing::info!(job_id = %job.id, "Job completed");
                            }
                            Err(e) if job.retry_count < job.max_retries => {
                                tracing::warn!(job_id = %job.id, error = %e, "Job failed, retrying");
                                let mut retry_job = job.clone();
                                retry_job.retry_count += 1;
                                self.queue.enqueue(retry_job).await?;
                            }
                            Err(e) => {
                                tracing::error!(job_id = %job.id, error = %e, "Job failed permanently");
                            }
                        }
                    }
                }
                None => {
                    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                }
            }
        }
    }
}
```

---

## Resilience Patterns

### Circuit Breaker

```rust
// crates/server/src/infrastructure/resilience/circuit_breaker.rs
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CircuitState {
    Closed,    // Normal operation
    Open,      // Failing, reject requests
    HalfOpen,  // Testing recovery
}

pub struct CircuitBreaker {
    state: Arc<RwLock<CircuitState>>,
    failure_count: AtomicU32,
    success_count: AtomicU32,
    failure_threshold: u32,
    success_threshold: u32,
    timeout: Duration,
    last_failure: Arc<RwLock<Option<Instant>>>,
}

impl CircuitBreaker {
    pub fn new(failure_threshold: u32, success_threshold: u32, timeout: Duration) -> Self {
        Self {
            state: Arc::new(RwLock::new(CircuitState::Closed)),
            failure_count: AtomicU32::new(0),
            success_count: AtomicU32::new(0),
            failure_threshold,
            success_threshold,
            timeout,
            last_failure: Arc::new(RwLock::new(None)),
        }
    }

    pub async fn call<F, T, E>(&self, f: F) -> Result<T, AppError>
    where
        F: std::future::Future<Output = Result<T, E>>,
        E: std::fmt::Display,
    {
        let state = *self.state.read().await;

        match state {
            CircuitState::Open => {
                if let Some(last) = *self.last_failure.read().await {
                    if last.elapsed() > self.timeout {
                        *self.state.write().await = CircuitState::HalfOpen;
                    } else {
                        return Err(AppError::ServiceUnavailable("Circuit breaker open".into()));
                    }
                }
            }
            _ => {}
        }

        match f.await {
            Ok(result) => {
                self.on_success().await;
                Ok(result)
            }
            Err(e) => {
                self.on_failure().await;
                Err(AppError::ServiceUnavailable(e.to_string()))
            }
        }
    }

    async fn on_success(&self) {
        let state = *self.state.read().await;
        if state == CircuitState::HalfOpen {
            let count = self.success_count.fetch_add(1, Ordering::SeqCst) + 1;
            if count >= self.success_threshold {
                *self.state.write().await = CircuitState::Closed;
                self.failure_count.store(0, Ordering::SeqCst);
                self.success_count.store(0, Ordering::SeqCst);
            }
        }
    }

    async fn on_failure(&self) {
        let count = self.failure_count.fetch_add(1, Ordering::SeqCst) + 1;
        if count >= self.failure_threshold {
            *self.state.write().await = CircuitState::Open;
            *self.last_failure.write().await = Some(Instant::now());
        }
    }
}
```

### Retry with Exponential Backoff

```rust
// crates/server/src/infrastructure/resilience/retry.rs
pub struct RetryPolicy {
    pub max_retries: u32,
    pub base_delay: Duration,
    pub max_delay: Duration,
}

impl RetryPolicy {
    pub async fn execute<F, Fut, T, E>(&self, mut f: F) -> Result<T, E>
    where
        F: FnMut() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
        E: std::fmt::Display,
    {
        let mut attempt = 0;
        loop {
            match f().await {
                Ok(result) => return Ok(result),
                Err(e) => {
                    attempt += 1;
                    if attempt > self.max_retries {
                        tracing::error!(attempts = attempt, error = %e, "All retries exhausted");
                        return Err(e);
                    }

                    let delay = std::cmp::min(
                        self.base_delay * 2u32.pow(attempt - 1),
                        self.max_delay,
                    );
                    tracing::warn!(attempt, delay = ?delay, error = %e, "Retrying after failure");
                    tokio::time::sleep(delay).await;
                }
            }
        }
    }
}
```

### Rate Limiter (Tower Middleware)

```rust
// crates/server/src/api/middleware/rate_limit.rs
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use std::time::{Duration, Instant};

pub struct RateLimiter {
    requests: Arc<RwLock<HashMap<String, Vec<Instant>>>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    pub fn new(max_requests: usize, window: Duration) -> Self {
        Self {
            requests: Arc::new(RwLock::new(HashMap::new())),
            max_requests,
            window,
        }
    }

    pub async fn check(&self, key: &str) -> Result<(), AppError> {
        let mut requests = self.requests.write().await;
        let entry = requests.entry(key.to_string()).or_insert_with(Vec::new);

        let now = Instant::now();
        entry.retain(|&t| now.duration_since(t) < self.window);

        if entry.len() >= self.max_requests {
            return Err(AppError::ServiceUnavailable(
                "Rate limit exceeded".into(),
            ));
        }

        entry.push(now);
        Ok(())
    }
}
```

---

## Security

### Argon2 Password Hashing

```rust
use argon2::{self, Config, Variant, Version};

pub fn hash_password(password: &str) -> Result<String, AppError> {
    let salt = uuid::Uuid::new_v4();
    let config = Config {
        variant: Variant::Argon2id,
        version: Version::Version13,
        mem_cost: 65536,
        time_cost: 3,
        lanes: 4,
        ..Config::default()
    };

    argon2::hash_encoded(password.as_bytes(), salt.as_bytes(), &config)
        .map_err(|e| AppError::Internal(format!("Password hashing failed: {}", e)))
}

pub fn verify_password(hash: &str, password: &str) -> Result<bool, AppError> {
    argon2::verify_encoded(hash, password.as_bytes())
        .map_err(|e| AppError::Internal(format!("Password verification failed: {}", e)))
}
```

### RBAC Middleware

```rust
// crates/server/src/api/middleware/rbac.rs
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};

pub async fn require_role(
    role: &str,
    claims: &Claims,
) -> Result<(), AppError> {
    if !claims.has_role(role) {
        return Err(AppError::Forbidden(format!(
            "Required role: {}, user roles: {:?}",
            role, claims.roles
        )));
    }
    Ok(())
}

// Usage in handler
pub async fn admin_only_handler(
    State(state): State<AppState>,
    claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    require_role("admin", &claims).await?;
    // ... handler logic
    Ok(Json(json!({"status": "ok"})))
}
```

### mTLS Configuration

```rust
// crates/server/src/infrastructure/tls.rs
use rustls::ServerConfig;
use std::fs;
use std::sync::Arc;

pub fn configure_mtls(config: &TlsConfig) -> Result<Arc<ServerConfig>, AppError> {
    let cert_pem = fs::read(&config.cert_path)
        .map_err(|e| AppError::Internal(format!("Failed to read cert: {}", e)))?;
    let key_pem = fs::read(&config.key_path)
        .map_err(|e| AppError::Internal(format!("Failed to read key: {}", e)))?;
    let ca_pem = fs::read(&config.ca_path)
        .map_err(|e| AppError::Internal(format!("Failed to read CA: {}", e)))?;

    let certs = rustls_pemfile::certs(&mut cert_pem.as_slice())
        .map(|c| c.unwrap())
        .collect::<Vec<_>>();

    let key = rustls_pemfile::private_key(&mut key_pem.as_slice())
        .map_err(|e| AppError::Internal(format!("Failed to parse key: {}", e)))?
        .ok_or_else(|| AppError::Internal("No private key found".into()))?;

    let mut root_store = rustls::RootCertStore::empty();
    for cert in rustls_pemfile::certs(&mut ca_pem.as_slice()) {
        root_store.add(cert.unwrap()).ok();
    }

    let server_config = ServerConfig::builder()
        .with_client_cert_verifier(
            rustls::server::WebPkiClientVerifier::builder(Arc::new(root_store))
                .build()
                .map_err(|e| AppError::Internal(e.to_string()))?,
        )
        .with_single_cert(certs, key.into())
        .map_err(|e| AppError::Internal(e.to_string()))?;

    Ok(Arc::new(server_config))
}
```

---

## Observability

### Distributed Tracing (tracing + OpenTelemetry)

```rust
// crates/server/src/infrastructure/telemetry.rs
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

pub fn init_tracing(config: &TelemetryConfig) -> Result<(), AppError> {
    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(&config.log_level));

    let fmt_layer = tracing_subscriber::fmt::layer()
        .json()
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true);

    tracing_subscriber::registry()
        .with(env_filter)
        .with(fmt_layer)
        .init();

    tracing::info!("Tracing initialized at level: {}", config.log_level);
    Ok(())
}
```

### Prometheus Metrics

```rust
// crates/server/src/api/middleware/metrics.rs
use metrics::{counter, histogram};
use std::time::Instant;

pub async fn metrics_middleware(
    request: axum::extract::Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    let method = request.method().to_string();
    let path = request.uri().path().to_string();
    let start = Instant::now();

    let response = next.run(request).await;

    let duration = start.elapsed().as_secs_f64();
    let status = response.status().as_u16().to_string();

    counter!("http_requests_total", "method" => method.clone(), "path" => path.clone(), "status" => status);
    histogram!("http_request_duration_seconds", "method" => method, "path" => path).record(duration);

    response
}
```

---

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] gRPC service implemented for internal communication
- [ ] Repository pattern properly implemented with async_trait
- [ ] JWT authentication complete
- [ ] Input validation with serde + custom validators
- [ ] ALL Handler service method calls have corresponding Service trait methods
- [ ] ALL gRPC proto methods have trait implementations
- [ ] ALL Service -> Repository method calls exist in Repository traits
- [ ] ALL dependencies wired in AppState
- [ ] No unwrap() in production code
- [ ] No unsafe blocks without justification

### Performance Checks
- [ ] Use gRPC for internal communication (2.1x faster)
- [ ] Database queries optimized with indexes
- [ ] Connection pooling configured (SQLx pool)
- [ ] Caching strategy implemented with Redis
- [ ] Async/await properly used (no blocking in async context)
- [ ] No unnecessary clones

### Security Checks
- [ ] JWT token validation
- [ ] Role-based access control (RBAC)
- [ ] Input validation complete
- [ ] Password hashing with Argon2
- [ ] No hardcoded secrets
- [ ] mTLS for service-to-service communication

### Code Quality
- [ ] cargo clippy -- -D warnings (zero warnings)
- [ ] cargo fmt -- --check (properly formatted)
- [ ] 150+ tests passing (80%+ coverage)
- [ ] No `unwrap()` in production code
- [ ] Proper lifetime annotations where needed
- [ ] Error types use thiserror

## Common Issues

### Borrow Checker Issues
1. Use `Arc<T>` for shared ownership across async boundaries
2. Use `Clone` derive for types passed between tasks
3. Prefer `&str` over `String` in function parameters
4. Use `'static` bounds for spawned tasks

### gRPC Connection Issues
1. Check protobuf compilation (`build.rs` and `tonic-build`)
2. Verify service registration in `main.rs`
3. Ensure proper error mapping to `tonic::Status`
4. Check port configuration (default :9090)

### Database Issues
1. Run SQLx migrations (`sqlx migrate run`)
2. Check connection pool settings (`max_connections`)
3. Review query performance (`EXPLAIN ANALYZE`)
4. Verify offline mode query data (`cargo sqlx prepare`)

### Async Runtime Issues
1. Use `#[tokio::main]` for entry point
2. Never block in async context (use `tokio::task::spawn_blocking`)
3. Use `tokio::select!` for concurrent operations
4. Handle graceful shutdown with `tokio::signal`

### WASM Plugin Issues
1. Verify plugin compiled to `wasm32-wasi` target
2. Check Wasmtime version compatibility (27.x)
3. Review memory limits in plugin configuration
4. Test plugins in isolation before integration

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Rust | 1.75+ (2021 edition) |
| Tokio | 1.43+ |
| Axum | 0.7+ |
| Tonic | 0.12+ |
| SQLx | 0.8+ |
| Wasmtime | 27+ |
| Redis (crate) | 0.27+ |
| jsonwebtoken | 9+ |
| argon2 | 0.5+ |
| serde | 1.0+ |
| chrono | 0.4+ |
| uuid | 1.0+ |
| tracing | 0.1+ |
| metrics | 0.24+ |
| thiserror | 2.0+ |
| async-trait | 0.1+ |
| mockall | 0.13+ |
| MySQL | 8.0+ |
| PostgreSQL | 15+ |
| Redis (server) | 7.0+ |
