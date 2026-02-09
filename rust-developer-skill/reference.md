# Rust Developer Skill - Technical Reference

## Table of Contents
1. [Cargo Workspace Structure](#cargo-workspace-structure)
2. [Key Dependencies](#key-dependencies)
3. [Configuration Reference](#configuration-reference)
4. [Proto Definitions](#proto-definitions)
5. [SQL Migrations](#sql-migrations)
6. [Environment Variables](#environment-variables)
7. [Docker Configuration](#docker-configuration)
8. [API Reference](#api-reference)
9. [Error Codes](#error-codes)
10. [Performance Tuning](#performance-tuning)

---

## Cargo Workspace Structure

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "crates/core",
    "crates/server",
    "crates/migration",
]
resolver = "2"

[workspace.package]
edition = "2021"
rust-version = "1.75"
license = "MIT"

[workspace.dependencies]
tokio = { version = "1.43", features = ["full"] }
axum = { version = "0.7", features = ["macros"] }
tonic = { version = "0.12" }
tonic-build = { version = "0.12" }
sqlx = { version = "0.8", features = ["runtime-tokio-rustls", "postgres", "mysql", "uuid", "chrono"] }
redis = { version = "0.27", features = ["aio", "tokio-comp"] }
wasmtime = "27"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1.0", features = ["v4", "serde"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
metrics = "0.24"
metrics-exporter-prometheus = "0.16"
jsonwebtoken = "9"
argon2 = "0.5"
thiserror = "2.0"
async-trait = "0.1"
tower = { version = "0.5", features = ["full"] }
tower-http = { version = "0.6", features = ["cors", "compression-gzip", "trace"] }
rustls = "0.23"
config = "0.14"

[workspace.dev-dependencies]
mockall = "0.13"
axum-test = "16"
tokio-test = "0.4"
```

```toml
# crates/core/Cargo.toml
[package]
name = "arcana-core"
version.workspace = true
edition.workspace = true

[dependencies]
tokio = { workspace = true }
sqlx = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
chrono = { workspace = true }
uuid = { workspace = true }
thiserror = { workspace = true }
async-trait = { workspace = true }
tracing = { workspace = true }
argon2 = { workspace = true }

[dev-dependencies]
mockall = { workspace = true }
tokio-test = { workspace = true }
```

```toml
# crates/server/Cargo.toml
[package]
name = "arcana-server"
version.workspace = true
edition.workspace = true

[[bin]]
name = "arcana-server"
path = "src/main.rs"

[dependencies]
arcana-core = { path = "../core" }
tokio = { workspace = true }
axum = { workspace = true }
tonic = { workspace = true }
sqlx = { workspace = true }
redis = { workspace = true }
wasmtime = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
chrono = { workspace = true }
uuid = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
metrics = { workspace = true }
metrics-exporter-prometheus = { workspace = true }
jsonwebtoken = { workspace = true }
tower = { workspace = true }
tower-http = { workspace = true }
rustls = { workspace = true }
config = { workspace = true }

[build-dependencies]
tonic-build = { workspace = true }

[dev-dependencies]
mockall = { workspace = true }
axum-test = { workspace = true }
```

---

## Key Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `tokio` | 1.43+ | Async runtime |
| `axum` | 0.7+ | REST HTTP framework |
| `tonic` | 0.12+ | gRPC framework |
| `sqlx` | 0.8+ | Async SQL toolkit (compile-time checked) |
| `redis` | 0.27+ | Redis client |
| `wasmtime` | 27+ | WASM runtime for plugins |
| `serde` | 1.0+ | Serialization/deserialization |
| `chrono` | 0.4+ | Date/time handling |
| `uuid` | 1.0+ | UUID generation |
| `tracing` | 0.1+ | Structured logging + distributed tracing |
| `metrics` | 0.24+ | Prometheus metrics |
| `jsonwebtoken` | 9+ | JWT encode/decode |
| `argon2` | 0.5+ | Password hashing |
| `thiserror` | 2.0+ | Error derive macro |
| `async-trait` | 0.1+ | Async trait support |
| `mockall` | 0.13+ | Mock generation for testing |
| `tower` | 0.5+ | Middleware framework |
| `tower-http` | 0.6+ | HTTP middleware (CORS, compression, tracing) |
| `rustls` | 0.23+ | TLS implementation (mTLS) |
| `config` | 0.14+ | Configuration management |

---

## Configuration Reference

```yaml
# config/default.yaml
server:
  host: "0.0.0.0"
  http_port: 8080
  grpc_port: 9090

database:
  url: "postgres://arcana:arcana@localhost:5432/arcana_db"
  max_connections: 20
  min_connections: 5
  connect_timeout_secs: 30

redis:
  url: "redis://localhost:6379"
  pool_size: 10

jwt:
  secret: "change-me-in-production"
  access_token_expiry_secs: 86400
  refresh_token_expiry_secs: 604800

tls:
  enabled: false
  cert_path: "certs/server.crt"
  key_path: "certs/server.key"
  ca_path: "certs/ca.crt"

plugins:
  enabled: true
  plugin_paths:
    - "plugins/arcana-audit-plugin/target/wasm32-wasi/release/arcana_audit_plugin.wasm"

telemetry:
  log_level: "info"
  metrics_enabled: true
  tracing_enabled: true

resilience:
  circuit_breaker:
    failure_threshold: 5
    success_threshold: 3
    timeout_secs: 30
  retry:
    max_retries: 3
    base_delay_ms: 100
    max_delay_ms: 5000
  rate_limit:
    max_requests: 100
    window_secs: 60
```

```yaml
# config/production.yaml
server:
  host: "0.0.0.0"
  http_port: 8080
  grpc_port: 9090

database:
  url: "${DATABASE_URL}"
  max_connections: 50
  min_connections: 10

redis:
  url: "${REDIS_URL}"

jwt:
  secret: "${JWT_SECRET}"

tls:
  enabled: true
  cert_path: "/etc/certs/server.crt"
  key_path: "/etc/certs/server.key"
  ca_path: "/etc/certs/ca.crt"

telemetry:
  log_level: "warn"
```

---

## Proto Definitions

```protobuf
// proto/user.proto
syntax = "proto3";
package arcana.user;

service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
  rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
  rpc UpdateUser (UpdateUserRequest) returns (UserResponse);
  rpc DeleteUser (DeleteUserRequest) returns (Empty);
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  uint32 page = 1;
  uint32 size = 2;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
  string password = 3;
}

message UpdateUserRequest {
  string id = 1;
  optional string name = 2;
  optional string email = 3;
}

message DeleteUserRequest {
  string id = 1;
}

message UserResponse {
  string id = 1;
  string name = 2;
  string email = 3;
  string created_at = 4;
  string updated_at = 5;
}

message ListUsersResponse {
  repeated UserResponse users = 1;
  int64 total = 2;
  uint32 page = 3;
  uint32 size = 4;
  bool has_next = 5;
}

message Empty {}
```

```protobuf
// proto/health.proto
syntax = "proto3";
package arcana.health;

service HealthService {
  rpc Check (HealthCheckRequest) returns (HealthCheckResponse);
}

message HealthCheckRequest {
  string service = 1;
}

message HealthCheckResponse {
  enum Status {
    UNKNOWN = 0;
    SERVING = 1;
    NOT_SERVING = 2;
  }
  Status status = 1;
}
```

### build.rs (tonic-build)

```rust
// build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .out_dir("src/proto")
        .compile(
            &["proto/user.proto", "proto/health.proto"],
            &["proto/"],
        )?;
    Ok(())
}
```

---

## SQL Migrations

```sql
-- migrations/001_create_users.sql
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

-- migrations/002_create_refresh_tokens.sql
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(500) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- migrations/003_create_products.sql
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DOUBLE PRECISION NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_status ON products(status);
```

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgres://arcana:arcana@localhost:5432/arcana_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-key-change-in-production
RUST_LOG=info

# Optional
SERVER_HOST=0.0.0.0
HTTP_PORT=8080
GRPC_PORT=9090
DB_MAX_CONNECTIONS=20
TLS_ENABLED=false
TLS_CERT_PATH=/etc/certs/server.crt
TLS_KEY_PATH=/etc/certs/server.key
TLS_CA_PATH=/etc/certs/ca.crt
PLUGINS_ENABLED=true
```

---

## Docker Configuration

```dockerfile
# Dockerfile (multi-stage build)
FROM rust:1.75-bookworm AS builder

WORKDIR /app
COPY . .

RUN cargo build --release --bin arcana-server

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/arcana-server /app/arcana-server
COPY --from=builder /app/config /app/config
COPY --from=builder /app/migrations /app/migrations

EXPOSE 8080 9090

ENV RUST_LOG=info

CMD ["./arcana-server"]
```

```yaml
# deployment/docker/docker-compose.yaml
version: "3.8"

services:
  app:
    build: ../..
    ports:
      - "8080:8080"
      - "9090:9090"
    environment:
      - DATABASE_URL=postgres://arcana:arcana@postgres:5432/arcana_db
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=dev-secret-key
      - RUST_LOG=info
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: arcana
      POSTGRES_PASSWORD: arcana
      POSTGRES_DB: arcana_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

## API Reference

### REST Endpoints (Port 8080)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/register | No | Register new user |
| POST | /api/v1/auth/login | No | Login, get tokens |
| POST | /api/v1/auth/refresh | No | Refresh access token |
| POST | /api/v1/auth/logout | No | Revoke refresh token |
| POST | /api/v1/auth/logout-all | JWT | Revoke all tokens |
| POST | /api/v1/auth/change-password | JWT | Change password |
| GET | /api/v1/auth/me | JWT | Get current user |
| GET | /api/v1/users | JWT | List users (paginated) |
| GET | /api/v1/users/:id | JWT | Get user by ID |
| POST | /api/v1/users | JWT | Create user |
| PUT | /api/v1/users/:id | JWT | Update user |
| DELETE | /api/v1/users/:id | JWT | Delete user |
| GET | /api/v1/products | Public | List products |
| GET | /api/v1/products/:id | Public | Get product |
| POST | /api/v1/products | JWT+Admin | Create product |
| PUT | /api/v1/products/:id | JWT+Admin | Update product |
| PATCH | /api/v1/products/:id/stock | JWT+Admin | Update stock |
| DELETE | /api/v1/products/:id | JWT+Admin | Delete product |
| GET | /health | Public | Health check |
| GET | /metrics | Public | Prometheus metrics |

### gRPC Services (Port 9090)

| Service | Method | Description |
|---------|--------|-------------|
| UserService | GetUser | Get user by ID |
| UserService | ListUsers | List users (paginated) |
| UserService | CreateUser | Create user |
| UserService | UpdateUser | Update user |
| UserService | DeleteUser | Delete user |
| HealthService | Check | Health check |

---

## Error Codes

| Code | HTTP Status | gRPC Code | Description |
|------|-------------|-----------|-------------|
| NOT_FOUND | 404 | NotFound | Resource not found |
| UNAUTHORIZED | 401 | Unauthenticated | Missing/invalid auth |
| TOKEN_EXPIRED | 401 | Unauthenticated | JWT token expired |
| INVALID_CREDENTIALS | 401 | Unauthenticated | Wrong email/password |
| FORBIDDEN | 403 | PermissionDenied | Insufficient permissions |
| VALIDATION_FAILED | 400 | InvalidArgument | Input validation error |
| CONFLICT | 409 | AlreadyExists | Duplicate resource |
| TIMEOUT | 408 | DeadlineExceeded | Request timeout |
| SERVICE_UNAVAILABLE | 503 | Unavailable | Service down / circuit open |
| INTERNAL_ERROR | 500 | Internal | Unexpected server error |
| DATABASE_ERROR | 500 | Internal | Database operation failed |
| CACHE_ERROR | 500 | Internal | Redis operation failed |

---

## Performance Tuning

### Connection Pool Settings

| Setting | Development | Production | Notes |
|---------|-------------|------------|-------|
| DB max_connections | 5 | 20-50 | Per pod/instance |
| DB min_connections | 1 | 5-10 | Keep warm |
| DB connect_timeout | 30s | 10s | Fail fast in prod |
| Redis pool_size | 5 | 10-20 | Per pod/instance |

### Tokio Runtime Tuning

```rust
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    // Worker threads = num_cpus is default
    // Adjust for I/O-heavy vs CPU-heavy workloads
}
```

### Axum Concurrency

| Parameter | Default | Recommended |
|-----------|---------|-------------|
| `tower::limit::ConcurrencyLimit` | Unlimited | 1000 |
| `tower::timeout::Timeout` | None | 30s |
| `tower_http::compression::CompressionLayer` | Off | gzip |

### gRPC Tuning

| Parameter | Default | Recommended |
|-----------|---------|-------------|
| `tonic::transport::Server::concurrency_limit_per_connection` | 32 | 64 |
| `tonic::transport::Server::tcp_keepalive` | None | 60s |
| `tonic::transport::Server::http2_keepalive_interval` | None | 30s |

### Compile-Time Optimizations

```toml
# Cargo.toml [profile.release]
[profile.release]
opt-level = 3
lto = "thin"
codegen-units = 1
strip = true

[profile.dev]
opt-level = 0
debug = true
incremental = true
```

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| http_request_duration_seconds (p99) | < 100ms | > 500ms |
| grpc_request_duration_seconds (p99) | < 50ms | > 200ms |
| db_query_duration_seconds (p99) | < 20ms | > 100ms |
| active_connections | < max_pool | > 80% of max |
| error_rate | < 0.1% | > 1% |
| circuit_breaker_open | 0 | > 0 |
| job_queue_length | < 100 | > 1000 |
