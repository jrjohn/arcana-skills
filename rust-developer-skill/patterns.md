# Rust Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Service Layer Patterns](#service-layer-patterns)
3. [Data Access Patterns](#data-access-patterns)
4. [API Design Patterns](#api-design-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Concurrency Patterns](#concurrency-patterns)
7. [Testing Patterns](#testing-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
+---------------------------------------------------------------+
|                          Handlers                               |
|  +-------------------------+   +----------------------------+  |
|  |   Axum REST Handlers    |   |   Tonic gRPC Services      |  |
|  |   (Port :8080)          |   |   (Port :9090)             |  |
|  +------------+------------+   +-------------+--------------+  |
|               |                              |                  |
|               +-------------+----------------+                  |
|                             v                                   |
+-----------------------------------------------------------------+
|                         Services                                 |
|  +-------------------------------------------------------------+|
|  |  Business Logic | Validation | Event Publishing              ||
|  |                                                               ||
|  |  Trait-based interfaces, no framework dependencies           ||
|  +-------------------------------------------------------------+|
|                             |                                    |
|                             v                                    |
+-----------------------------------------------------------------+
|                       Repositories                               |
|  +--------------+ +--------------+ +---------------------------+|
|  | SQLx (PG/MY) | | Redis Cache  | | External Services         ||
|  | Repositories | | Repository   | | (gRPC clients)            ||
|  +--------------+ +--------------+ +---------------------------+|
+-----------------------------------------------------------------+
```

### Implementation

```rust
// Handler Layer - HTTP concerns only
async fn get_user(
    State(state): State<AppState>,
    Path(user_id): Path<Uuid>,
    _claims: Claims,
) -> Result<Json<UserDto>, AppError> {
    let user = state.user_service.get_user(user_id).await?;
    user.map(Json).ok_or_else(|| AppError::NotFound("User not found".into()))
}

// Service Layer - Business logic (trait-based)
#[async_trait]
pub trait UserService: Send + Sync {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError>;
}

pub struct UserServiceImpl {
    repo: Arc<dyn UserRepository>,
    cache: Arc<dyn CacheService>,
    events: Arc<dyn EventPublisher>,
}

#[async_trait]
impl UserService for UserServiceImpl {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError> {
        // Try cache
        let cache_key = format!("user:{}", id);
        if let Some(cached) = self.cache.get::<UserDto>(&cache_key).await? {
            return Ok(Some(cached));
        }

        // Load from database
        let user = self.repo.find_by_id(id).await?;
        if let Some(ref u) = user {
            let dto = UserDto::from(u.clone());
            self.cache.set(&cache_key, &dto, 1800).await?;
            return Ok(Some(dto));
        }

        Ok(None)
    }
}

// Repository Layer - Data access (trait-based)
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, AppError>;
}

pub struct PgUserRepository {
    pool: PgPool,
}

#[async_trait]
impl UserRepository for PgUserRepository {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, AppError> {
        sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
            .bind(id)
            .fetch_optional(&self.pool)
            .await
            .map_err(AppError::from)
    }
}
```

### Dependency Injection via AppState

```rust
// crates/server/src/state.rs
use std::sync::Arc;

#[derive(Clone)]
pub struct AppState {
    // Services (trait objects for testability)
    pub user_service: Arc<dyn UserService>,
    pub auth_service: Arc<dyn AuthService>,
    pub product_service: Arc<dyn ProductService>,

    // Infrastructure
    pub cache: Arc<dyn CacheService>,
    pub events: Arc<dyn EventPublisher>,
    pub plugin_host: Arc<PluginHost>,
    pub job_queue: Arc<JobQueue>,

    // Config
    pub jwt_secret: String,
}

impl AppState {
    pub async fn new(config: &AppConfig) -> Result<Self, AppError> {
        let pool = PgPoolOptions::new()
            .max_connections(config.db.max_connections)
            .connect(&config.db.url)
            .await?;

        let redis = Arc::new(redis::Client::open(config.redis.url.as_str())?);
        let cache: Arc<dyn CacheService> = Arc::new(RedisCache::new(redis.clone()));
        let events: Arc<dyn EventPublisher> = Arc::new(RedisEventPublisher::new(redis.clone()));

        let user_repo: Arc<dyn UserRepository> = Arc::new(PgUserRepository::new(pool.clone()));
        let token_repo: Arc<dyn RefreshTokenRepository> = Arc::new(PgRefreshTokenRepository::new(pool.clone()));
        let product_repo: Arc<dyn ProductRepository> = Arc::new(PgProductRepository::new(pool.clone()));

        let user_service: Arc<dyn UserService> = Arc::new(UserServiceImpl::new(
            user_repo.clone(),
            cache.clone(),
            events.clone(),
        ));
        let auth_service: Arc<dyn AuthService> = Arc::new(AuthServiceImpl::new(
            user_repo,
            token_repo,
            config.jwt.secret.clone(),
        ));
        let product_service: Arc<dyn ProductService> = Arc::new(ProductServiceImpl::new(
            product_repo,
            cache.clone(),
        ));

        let plugin_host = Arc::new(PluginHost::new(&config.plugins).await?);
        let job_queue = Arc::new(JobQueue::new(redis));

        Ok(Self {
            user_service,
            auth_service,
            product_service,
            cache,
            events,
            plugin_host,
            job_queue,
            jwt_secret: config.jwt.secret.clone(),
        })
    }
}
```

---

## Service Layer Patterns

### Strategy Pattern

```rust
use async_trait::async_trait;

#[async_trait]
trait PricingStrategy: Send + Sync {
    fn calculate(&self, base_price: f64, quantity: u32) -> f64;
}

struct RegularPricing;

impl PricingStrategy for RegularPricing {
    fn calculate(&self, base_price: f64, quantity: u32) -> f64 {
        base_price * quantity as f64
    }
}

struct BulkPricing {
    threshold: u32,
    discount_rate: f64,
}

impl PricingStrategy for BulkPricing {
    fn calculate(&self, base_price: f64, quantity: u32) -> f64 {
        let total = base_price * quantity as f64;
        if quantity >= self.threshold {
            total * (1.0 - self.discount_rate)
        } else {
            total
        }
    }
}

struct PremiumPricing {
    discount_rate: f64,
}

impl PricingStrategy for PremiumPricing {
    fn calculate(&self, base_price: f64, quantity: u32) -> f64 {
        base_price * quantity as f64 * (1.0 - self.discount_rate)
    }
}

// Strategy factory
fn create_pricing_strategy(customer_type: &str) -> Box<dyn PricingStrategy> {
    match customer_type {
        "bulk" => Box::new(BulkPricing {
            threshold: 10,
            discount_rate: 0.10,
        }),
        "premium" => Box::new(PremiumPricing {
            discount_rate: 0.15,
        }),
        _ => Box::new(RegularPricing),
    }
}

// Usage in service
struct OrderService;

impl OrderService {
    fn calculate_total(&self, items: &[OrderItem], customer_type: &str) -> f64 {
        let strategy = create_pricing_strategy(customer_type);
        items
            .iter()
            .map(|item| strategy.calculate(item.price, item.quantity))
            .sum()
    }
}
```

### Command Pattern

```rust
use async_trait::async_trait;

#[async_trait]
trait Command<T> {
    async fn execute(&self) -> Result<T, AppError>;
}

struct CreateUserCommand {
    dto: CreateUserRequest,
    repo: Arc<dyn UserRepository>,
    events: Arc<dyn EventPublisher>,
}

#[async_trait]
impl Command<User> for CreateUserCommand {
    async fn execute(&self) -> Result<User, AppError> {
        // Validation
        if self.repo.find_by_email(&self.dto.email).await?.is_some() {
            return Err(AppError::Conflict("Email already exists".into()));
        }

        // Create user
        let password_hash = crate::security::hash_password(&self.dto.password)?;
        let user = User {
            id: Uuid::new_v4(),
            name: self.dto.name.clone(),
            email: self.dto.email.clone(),
            password_hash,
            sync_status: SyncStatus::Synced,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };

        let saved = self.repo.save(&user).await?;

        // Publish event
        self.events
            .publish("user.created", serde_json::json!({"userId": saved.id.to_string()}))
            .await?;

        Ok(saved)
    }
}

struct UpdateUserCommand {
    user_id: Uuid,
    dto: UpdateUserRequest,
    repo: Arc<dyn UserRepository>,
}

#[async_trait]
impl Command<User> for UpdateUserCommand {
    async fn execute(&self) -> Result<User, AppError> {
        let mut user = self
            .repo
            .find_by_id(self.user_id)
            .await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        if let Some(ref name) = self.dto.name {
            user.name = name.clone();
        }
        if let Some(ref email) = self.dto.email {
            user.email = email.clone();
        }

        self.repo.update(&user).await
    }
}

// Command bus
struct CommandBus;

impl CommandBus {
    async fn dispatch<T>(&self, command: &dyn Command<T>) -> Result<T, AppError> {
        command.execute().await
    }
}
```

### Builder Pattern for Complex Types

```rust
#[derive(Debug, Clone)]
pub struct ServerConfig {
    pub host: String,
    pub http_port: u16,
    pub grpc_port: u16,
    pub max_connections: u32,
    pub tls_enabled: bool,
    pub metrics_enabled: bool,
}

pub struct ServerConfigBuilder {
    host: String,
    http_port: u16,
    grpc_port: u16,
    max_connections: u32,
    tls_enabled: bool,
    metrics_enabled: bool,
}

impl ServerConfigBuilder {
    pub fn new() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            http_port: 8080,
            grpc_port: 9090,
            max_connections: 100,
            tls_enabled: false,
            metrics_enabled: true,
        }
    }

    pub fn host(mut self, host: &str) -> Self {
        self.host = host.to_string();
        self
    }

    pub fn http_port(mut self, port: u16) -> Self {
        self.http_port = port;
        self
    }

    pub fn grpc_port(mut self, port: u16) -> Self {
        self.grpc_port = port;
        self
    }

    pub fn max_connections(mut self, max: u32) -> Self {
        self.max_connections = max;
        self
    }

    pub fn with_tls(mut self) -> Self {
        self.tls_enabled = true;
        self
    }

    pub fn without_metrics(mut self) -> Self {
        self.metrics_enabled = false;
        self
    }

    pub fn build(self) -> ServerConfig {
        ServerConfig {
            host: self.host,
            http_port: self.http_port,
            grpc_port: self.grpc_port,
            max_connections: self.max_connections,
            tls_enabled: self.tls_enabled,
            metrics_enabled: self.metrics_enabled,
        }
    }
}

// Usage
let config = ServerConfigBuilder::new()
    .host("127.0.0.1")
    .http_port(3000)
    .grpc_port(50051)
    .with_tls()
    .build();
```

---

## Data Access Patterns

### Repository Pattern with Generic Trait

```rust
use async_trait::async_trait;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct PaginationOptions {
    pub page: Option<u32>,
    pub size: Option<u32>,
    pub order_by: Option<String>,
    pub order: Option<String>,
}

#[async_trait]
pub trait Repository<T: Send + Sync>: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<T>, AppError>;
    async fn find_all(&self, opts: &PaginationOptions) -> Result<(Vec<T>, i64), AppError>;
    async fn save(&self, entity: &T) -> Result<T, AppError>;
    async fn update(&self, entity: &T) -> Result<T, AppError>;
    async fn delete(&self, id: Uuid) -> Result<(), AppError>;
}

// Specific repository extending the base
#[async_trait]
pub trait UserRepository: Repository<User> {
    async fn find_by_email(&self, email: &str) -> Result<Option<User>, AppError>;
    async fn find_pending_sync(&self) -> Result<Vec<User>, AppError>;
    async fn exists_by_email(&self, email: &str) -> Result<bool, AppError>;
}
```

### Cache-Aside Pattern

```rust
use async_trait::async_trait;
use redis::AsyncCommands;
use serde::{de::DeserializeOwned, Serialize};

#[async_trait]
pub trait CacheService: Send + Sync {
    async fn get<T: DeserializeOwned + Send>(&self, key: &str) -> Result<Option<T>, AppError>;
    async fn set<T: Serialize + Send + Sync>(&self, key: &str, value: &T, ttl_secs: u64) -> Result<(), AppError>;
    async fn delete(&self, key: &str) -> Result<(), AppError>;
    async fn get_or_load<T, F, Fut>(
        &self,
        key: &str,
        loader: F,
        ttl_secs: u64,
    ) -> Result<T, AppError>
    where
        T: Serialize + DeserializeOwned + Send + Sync,
        F: FnOnce() -> Fut + Send,
        Fut: std::future::Future<Output = Result<T, AppError>> + Send;
}

pub struct RedisCache {
    client: Arc<redis::Client>,
    prefix: String,
}

impl RedisCache {
    pub fn new(client: Arc<redis::Client>) -> Self {
        Self {
            client,
            prefix: String::new(),
        }
    }

    pub fn with_prefix(client: Arc<redis::Client>, prefix: &str) -> Self {
        Self {
            client,
            prefix: prefix.to_string(),
        }
    }

    fn make_key(&self, key: &str) -> String {
        format!("{}{}", self.prefix, key)
    }
}

#[async_trait]
impl CacheService for RedisCache {
    async fn get<T: DeserializeOwned + Send>(&self, key: &str) -> Result<Option<T>, AppError> {
        let mut conn = self.client.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        let data: Option<String> = conn.get(self.make_key(key)).await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        match data {
            Some(json) => {
                let value = serde_json::from_str(&json)
                    .map_err(|e| AppError::Internal(e.to_string()))?;
                Ok(Some(value))
            }
            None => Ok(None),
        }
    }

    async fn set<T: Serialize + Send + Sync>(
        &self,
        key: &str,
        value: &T,
        ttl_secs: u64,
    ) -> Result<(), AppError> {
        let mut conn = self.client.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        let json = serde_json::to_string(value)
            .map_err(|e| AppError::Internal(e.to_string()))?;

        conn.set_ex(self.make_key(key), json, ttl_secs).await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        Ok(())
    }

    async fn delete(&self, key: &str) -> Result<(), AppError> {
        let mut conn = self.client.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        conn.del(self.make_key(key)).await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        Ok(())
    }

    async fn get_or_load<T, F, Fut>(
        &self,
        key: &str,
        loader: F,
        ttl_secs: u64,
    ) -> Result<T, AppError>
    where
        T: Serialize + DeserializeOwned + Send + Sync,
        F: FnOnce() -> Fut + Send,
        Fut: std::future::Future<Output = Result<T, AppError>> + Send,
    {
        if let Some(cached) = self.get::<T>(key).await? {
            return Ok(cached);
        }

        let value = loader().await?;
        self.set(key, &value, ttl_secs).await?;
        Ok(value)
    }
}
```

---

## API Design Patterns

### Router Factory Pattern

```rust
use axum::{
    routing::{get, post, put, delete},
    Router,
};

fn crud_routes<S: Clone + Send + Sync + 'static>(
    list_handler: impl axum::handler::Handler<(), S> + Clone,
    get_handler: impl axum::handler::Handler<(Path<Uuid>,), S> + Clone,
    create_handler: impl axum::handler::Handler<(), S> + Clone,
    update_handler: impl axum::handler::Handler<(Path<Uuid>,), S> + Clone,
    delete_handler: impl axum::handler::Handler<(Path<Uuid>,), S> + Clone,
) -> Router<S> {
    Router::new()
        .route("/", get(list_handler).post(create_handler))
        .route("/:id", get(get_handler).put(update_handler).delete(delete_handler))
}

// Usage
pub fn api_routes(state: AppState) -> Router {
    Router::new()
        .nest("/api/v1/users", crud_routes(
            user_handler::list_users,
            user_handler::get_user,
            user_handler::create_user,
            user_handler::update_user,
            user_handler::delete_user,
        ))
        .nest("/api/v1/products", crud_routes(
            product_handler::list_products,
            product_handler::get_product,
            product_handler::create_product,
            product_handler::update_product,
            product_handler::delete_product,
        ))
        .with_state(state)
}
```

### Request/Response DTO Pattern

```rust
use serde::{Deserialize, Serialize};

// Request DTOs with serde validation
#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    #[serde(deserialize_with = "non_empty_string")]
    pub name: String,
    #[serde(deserialize_with = "valid_email")]
    pub email: String,
    #[serde(deserialize_with = "min_length_8")]
    pub password: String,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUserRequest {
    pub name: Option<String>,
    pub email: Option<String>,
}

// Response DTOs
#[derive(Debug, Serialize)]
pub struct ApiResponse<T: Serialize> {
    pub data: T,
    pub message: String,
    pub timestamp: String,
}

#[derive(Debug, Serialize)]
pub struct PaginatedResponse<T: Serialize> {
    pub data: Vec<T>,
    pub page: u32,
    pub size: u32,
    pub total: i64,
    pub total_pages: u32,
    pub has_next: bool,
    pub has_previous: bool,
}

impl<T: Serialize> PaginatedResponse<T> {
    pub fn new(data: Vec<T>, page: u32, size: u32, total: i64) -> Self {
        let total_pages = ((total as f64) / (size as f64)).ceil() as u32;
        Self {
            data,
            page,
            size,
            total,
            total_pages,
            has_next: page < total_pages.saturating_sub(1),
            has_previous: page > 0,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
    pub timestamp: String,
}

// Response helpers
pub fn success_response<T: Serialize>(data: T) -> ApiResponse<T> {
    ApiResponse {
        data,
        message: "Success".to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
    }
}
```

---

## Error Handling Patterns

### Custom Error Hierarchy with thiserror

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Forbidden: {0}")]
    Forbidden(String),

    #[error("Validation failed: {0}")]
    ValidationFailed(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Cache error: {0}")]
    Cache(String),

    #[error("Token expired")]
    TokenExpired,

    #[error("Invalid credentials")]
    InvalidCredentials,

    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),
}

// Entity-specific errors using From trait
#[derive(Debug, Error)]
pub enum UserError {
    #[error("User not found: {0}")]
    NotFound(Uuid),

    #[error("Email already registered: {0}")]
    EmailExists(String),

    #[error("Weak password: {0}")]
    WeakPassword(String),
}

impl From<UserError> for AppError {
    fn from(err: UserError) -> Self {
        match err {
            UserError::NotFound(id) => AppError::NotFound(format!("User not found: {}", id)),
            UserError::EmailExists(email) => AppError::Conflict(format!("Email already registered: {}", email)),
            UserError::WeakPassword(reason) => AppError::ValidationFailed(reason),
        }
    }
}

// Axum IntoResponse for automatic HTTP error mapping
impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, code) = match &self {
            AppError::NotFound(_) => (StatusCode::NOT_FOUND, "NOT_FOUND"),
            AppError::Unauthorized(_) | AppError::TokenExpired | AppError::InvalidCredentials => {
                (StatusCode::UNAUTHORIZED, "UNAUTHORIZED")
            }
            AppError::Forbidden(_) => (StatusCode::FORBIDDEN, "FORBIDDEN"),
            AppError::ValidationFailed(_) => (StatusCode::BAD_REQUEST, "VALIDATION_FAILED"),
            AppError::Conflict(_) => (StatusCode::CONFLICT, "CONFLICT"),
            AppError::ServiceUnavailable(_) => (StatusCode::SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE"),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, "INTERNAL_ERROR"),
        };

        let body = serde_json::json!({
            "code": code,
            "message": self.to_string(),
            "timestamp": chrono::Utc::now().to_rfc3339(),
        });

        (status, Json(body)).into_response()
    }
}
```

### Result Extension Trait

```rust
pub trait ResultExt<T> {
    fn not_found(self, msg: &str) -> Result<T, AppError>;
    fn or_internal(self, msg: &str) -> Result<T, AppError>;
}

impl<T, E: std::fmt::Display> ResultExt<T> for Result<T, E> {
    fn not_found(self, msg: &str) -> Result<T, AppError> {
        self.map_err(|_| AppError::NotFound(msg.to_string()))
    }

    fn or_internal(self, msg: &str) -> Result<T, AppError> {
        self.map_err(|e| AppError::Internal(format!("{}: {}", msg, e)))
    }
}

impl<T> ResultExt<T> for Option<T> {
    fn not_found(self, msg: &str) -> Result<T, AppError> {
        self.ok_or_else(|| AppError::NotFound(msg.to_string()))
    }

    fn or_internal(self, msg: &str) -> Result<T, AppError> {
        self.ok_or_else(|| AppError::Internal(msg.to_string()))
    }
}

// Usage
let user = repo
    .find_by_id(id)
    .await?
    .not_found("User not found")?;
```

---

## Concurrency Patterns

### Tokio Task Spawning

```rust
use tokio::task;

// Spawn a background task
pub async fn process_in_background(
    service: Arc<dyn UserService>,
    user_id: Uuid,
) {
    task::spawn(async move {
        match service.sync_user(user_id).await {
            Ok(()) => tracing::info!(user_id = %user_id, "Background sync completed"),
            Err(e) => tracing::error!(user_id = %user_id, error = %e, "Background sync failed"),
        }
    });
}

// Blocking operation in async context
pub async fn compute_hash(password: String) -> Result<String, AppError> {
    task::spawn_blocking(move || {
        crate::security::hash_password(&password)
    })
    .await
    .map_err(|e| AppError::Internal(e.to_string()))?
}

// Concurrent operations with join
pub async fn get_dashboard(
    user_service: &dyn UserService,
    product_service: &dyn ProductService,
    user_id: Uuid,
) -> Result<DashboardDto, AppError> {
    let (user, recent_products, stats) = tokio::try_join!(
        user_service.get_user(user_id),
        product_service.get_products(0, 5, None, None),
        user_service.get_stats(user_id),
    )?;

    Ok(DashboardDto {
        user: user.ok_or_else(|| AppError::NotFound("User not found".into()))?,
        recent_products: recent_products.data,
        stats,
    })
}
```

### Graceful Shutdown

```rust
// crates/server/src/main.rs
use tokio::signal;
use tokio::sync::watch;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    init_tracing(&config.telemetry)?;

    // Build application state
    let state = AppState::new(&config).await?;

    // Create shutdown channel
    let (shutdown_tx, shutdown_rx) = watch::channel(false);

    // Start HTTP server
    let http_addr = format!("{}:{}", config.server.host, config.server.http_port);
    let router = create_router(state.clone());
    let http_server = axum::Server::bind(&http_addr.parse()?)
        .serve(router.into_make_service())
        .with_graceful_shutdown(shutdown_signal(shutdown_rx.clone()));

    // Start gRPC server
    let grpc_addr = format!("{}:{}", config.server.host, config.server.grpc_port);
    let grpc_server = create_grpc_server(state.clone(), &grpc_addr, shutdown_rx.clone());

    // Start job worker
    let worker = JobWorker::new(state.job_queue.clone(), state.clone());
    let worker_handle = tokio::spawn(async move { worker.run().await });

    // Start scheduler
    let scheduler = JobScheduler::new(state.job_queue.clone());
    scheduler.start().await;

    tracing::info!(http = %http_addr, grpc = %grpc_addr, "Server started");

    // Wait for shutdown signal
    tokio::select! {
        _ = http_server => tracing::info!("HTTP server stopped"),
        _ = grpc_server => tracing::info!("gRPC server stopped"),
        _ = signal::ctrl_c() => {
            tracing::info!("Shutdown signal received");
            let _ = shutdown_tx.send(true);
        }
    }

    // Graceful shutdown
    worker_handle.abort();
    tracing::info!("Graceful shutdown complete");

    Ok(())
}

async fn shutdown_signal(mut rx: watch::Receiver<bool>) {
    while !*rx.borrow() {
        if rx.changed().await.is_err() {
            break;
        }
    }
}
```

---

## Testing Patterns

### Mock Repository with mockall

```rust
use mockall::mock;
use mockall::predicate::*;

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

mock! {
    pub Cache {}

    #[async_trait]
    impl CacheService for Cache {
        async fn get<T: DeserializeOwned + Send>(&self, key: &str) -> Result<Option<T>, AppError>;
        async fn set<T: Serialize + Send + Sync>(&self, key: &str, value: &T, ttl: u64) -> Result<(), AppError>;
        async fn delete(&self, key: &str) -> Result<(), AppError>;
    }
}
```

### Test Fixtures

```rust
// tests/fixtures/mod.rs
use arcana_core::domain::models::user::*;
use chrono::Utc;
use uuid::Uuid;

pub fn mock_user() -> User {
    User {
        id: Uuid::new_v4(),
        name: "Test User".to_string(),
        email: "test@example.com".to_string(),
        password_hash: "hashed_password".to_string(),
        sync_status: SyncStatus::Synced,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    }
}

pub fn mock_user_with(overrides: impl FnOnce(&mut User)) -> User {
    let mut user = mock_user();
    overrides(&mut user);
    user
}

pub fn mock_users(count: usize) -> Vec<User> {
    (0..count)
        .map(|i| {
            mock_user_with(|u| {
                u.id = Uuid::new_v4();
                u.name = format!("User {}", i);
                u.email = format!("user{}@example.com", i);
            })
        })
        .collect()
}
```

### Service Layer Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::fixtures::*;
    use std::sync::Arc;

    fn setup() -> (UserServiceImpl, MockUserRepo, MockCache, MockEventPublisher) {
        let mock_repo = MockUserRepo::new();
        let mock_cache = MockCache::new();
        let mock_events = MockEventPublisher::new();
        let service = UserServiceImpl::new(
            Arc::new(mock_repo),
            Arc::new(mock_cache),
            Arc::new(mock_events),
        );
        (service, mock_repo, mock_cache, mock_events)
    }

    #[tokio::test]
    async fn test_get_user_returns_cached() {
        let mut mock_cache = MockCache::new();
        let cached_dto = UserDto {
            id: "123".to_string(),
            name: "Cached User".to_string(),
            email: "cached@example.com".to_string(),
            created_at: Utc::now().to_rfc3339(),
            updated_at: Utc::now().to_rfc3339(),
        };

        mock_cache
            .expect_get::<UserDto>()
            .returning(move |_| Ok(Some(cached_dto.clone())));

        let mock_repo = MockUserRepo::new();
        // repo should NOT be called when cache hits
        mock_repo.expect_find_by_id().times(0);

        let service = UserServiceImpl::new(
            Arc::new(mock_repo),
            Arc::new(mock_cache),
            Arc::new(MockEventPublisher::new()),
        );

        let result = service.get_user(Uuid::new_v4()).await.unwrap();
        assert!(result.is_some());
        assert_eq!(result.unwrap().name, "Cached User");
    }

    #[tokio::test]
    async fn test_create_user_publishes_event() {
        let mut mock_repo = MockUserRepo::new();
        let mut mock_events = MockEventPublisher::new();

        mock_repo
            .expect_find_by_email()
            .returning(|_| Ok(None));

        mock_repo
            .expect_save()
            .returning(|user| Ok(user.clone()));

        mock_events
            .expect_publish()
            .withf(|event_type, _| event_type == "user.registered")
            .times(1)
            .returning(|_, _| Ok("event-id".to_string()));

        let service = UserServiceImpl::new(
            Arc::new(mock_repo),
            Arc::new(MockCache::new()),
            Arc::new(mock_events),
        );

        let result = service
            .create_user(CreateUserRequest {
                name: "New User".to_string(),
                email: "new@example.com".to_string(),
                password: "Password123".to_string(),
            })
            .await;

        assert!(result.is_ok());
    }
}
```

### Integration Tests

```rust
// tests/integration/user_api_test.rs
use axum::http::StatusCode;
use axum_test::TestServer;

#[tokio::test]
async fn test_user_crud_flow() {
    let app = setup_test_app().await;
    let server = TestServer::new(app).unwrap();
    let token = get_test_auth_token(&server).await;

    // Create user
    let create_response = server
        .post("/api/v1/users")
        .add_header("Authorization", format!("Bearer {}", token))
        .json(&serde_json::json!({
            "name": "Integration User",
            "email": "integration@test.com",
            "password": "Password123"
        }))
        .await;

    assert_eq!(create_response.status_code(), StatusCode::CREATED);
    let user: serde_json::Value = create_response.json();
    let user_id = user["id"].as_str().unwrap();

    // Get user
    let get_response = server
        .get(&format!("/api/v1/users/{}", user_id))
        .add_header("Authorization", format!("Bearer {}", token))
        .await;

    assert_eq!(get_response.status_code(), StatusCode::OK);
    let fetched: serde_json::Value = get_response.json();
    assert_eq!(fetched["name"].as_str().unwrap(), "Integration User");

    // Delete user
    let delete_response = server
        .delete(&format!("/api/v1/users/{}", user_id))
        .add_header("Authorization", format!("Bearer {}", token))
        .await;

    assert_eq!(delete_response.status_code(), StatusCode::NO_CONTENT);

    // Verify deleted
    let verify_response = server
        .get(&format!("/api/v1/users/{}", user_id))
        .add_header("Authorization", format!("Bearer {}", token))
        .await;

    assert_eq!(verify_response.status_code(), StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn test_auth_flow() {
    let app = setup_test_app().await;
    let server = TestServer::new(app).unwrap();

    // Register
    let register_resp = server
        .post("/api/v1/auth/register")
        .json(&serde_json::json!({
            "name": "Auth Test",
            "email": "auth@test.com",
            "password": "Password123"
        }))
        .await;

    assert_eq!(register_resp.status_code(), StatusCode::CREATED);

    // Login
    let login_resp = server
        .post("/api/v1/auth/login")
        .json(&serde_json::json!({
            "email": "auth@test.com",
            "password": "Password123"
        }))
        .await;

    assert_eq!(login_resp.status_code(), StatusCode::OK);
    let tokens: serde_json::Value = login_resp.json();
    assert!(tokens["access_token"].is_string());
    assert!(tokens["refresh_token"].is_string());

    // Access protected route
    let me_resp = server
        .get("/api/v1/auth/me")
        .add_header("Authorization", format!("Bearer {}", tokens["access_token"].as_str().unwrap()))
        .await;

    assert_eq!(me_resp.status_code(), StatusCode::OK);

    // Unauthorized without token
    let unauth_resp = server
        .get("/api/v1/auth/me")
        .await;

    assert_eq!(unauth_resp.status_code(), StatusCode::UNAUTHORIZED);
}
```
