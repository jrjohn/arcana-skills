# Rust Developer Skill - Code Examples

## Table of Contents
1. [User Authentication Feature](#user-authentication-feature)
2. [CRUD with REST and gRPC](#crud-with-rest-and-grpc)
3. [WASM Plugin Integration](#wasm-plugin-integration)
4. [Distributed Job Queue](#distributed-job-queue)
5. [Event-Driven Architecture](#event-driven-architecture)

---

## User Authentication Feature

### Domain Layer

```rust
// crates/core/src/domain/models/auth.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenPair {
    pub access_token: String,
    pub refresh_token: String,
    pub token_type: String,
    pub expires_in: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct RefreshToken {
    pub id: Uuid,
    pub token: String,
    pub user_id: Uuid,
    pub expires_at: DateTime<Utc>,
    pub revoked: bool,
    pub revoked_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub email: String,
    pub password: String,
}

#[derive(Debug, Deserialize)]
pub struct RegisterRequest {
    pub name: String,
    pub email: String,
    pub password: String,
}

#[derive(Debug, Deserialize)]
pub struct ChangePasswordRequest {
    pub current_password: String,
    pub new_password: String,
}

#[derive(Debug, Deserialize)]
pub struct RefreshTokenRequest {
    pub refresh_token: String,
}
```

### Service Layer

```rust
// crates/core/src/domain/services/auth_service.rs
use async_trait::async_trait;
use chrono::Utc;
use std::sync::Arc;
use uuid::Uuid;

use crate::domain::models::auth::*;
use crate::domain::models::user::{User, SyncStatus};
use crate::domain::repositories::user_repository::UserRepository;
use crate::domain::repositories::token_repository::RefreshTokenRepository;
use crate::error::AppError;

#[async_trait]
pub trait AuthService: Send + Sync {
    async fn login(&self, req: LoginRequest) -> Result<TokenPair, AppError>;
    async fn register(&self, req: RegisterRequest) -> Result<User, AppError>;
    async fn refresh_token(&self, req: RefreshTokenRequest) -> Result<TokenPair, AppError>;
    async fn logout(&self, refresh_token: &str) -> Result<(), AppError>;
    async fn logout_all(&self, user_id: Uuid) -> Result<(), AppError>;
    async fn change_password(&self, user_id: Uuid, req: ChangePasswordRequest) -> Result<(), AppError>;
    async fn verify_token(&self, token: &str) -> Result<Claims, AppError>;
}

pub struct AuthServiceImpl {
    user_repo: Arc<dyn UserRepository>,
    token_repo: Arc<dyn RefreshTokenRepository>,
    jwt_secret: String,
    access_token_expiry: u64,   // seconds
    refresh_token_expiry: i64,  // seconds
}

impl AuthServiceImpl {
    pub fn new(
        user_repo: Arc<dyn UserRepository>,
        token_repo: Arc<dyn RefreshTokenRepository>,
        jwt_secret: String,
    ) -> Self {
        Self {
            user_repo,
            token_repo,
            jwt_secret,
            access_token_expiry: 86400,         // 24 hours
            refresh_token_expiry: 7 * 86400,    // 7 days
        }
    }

    fn validate_password_strength(&self, password: &str) -> Result<(), AppError> {
        let mut errors = Vec::new();

        if password.len() < 8 {
            errors.push("Password must be at least 8 characters");
        }
        if !password.chars().any(|c| c.is_uppercase()) {
            errors.push("Password must contain uppercase letter");
        }
        if !password.chars().any(|c| c.is_lowercase()) {
            errors.push("Password must contain lowercase letter");
        }
        if !password.chars().any(|c| c.is_ascii_digit()) {
            errors.push("Password must contain a number");
        }

        if !errors.is_empty() {
            return Err(AppError::ValidationFailed(errors.join("; ")));
        }
        Ok(())
    }
}

#[async_trait]
impl AuthService for AuthServiceImpl {
    async fn login(&self, req: LoginRequest) -> Result<TokenPair, AppError> {
        let user = self
            .user_repo
            .find_by_email(&req.email)
            .await?
            .ok_or(AppError::InvalidCredentials)?;

        let valid = argon2::verify_encoded(&user.password_hash, req.password.as_bytes())
            .unwrap_or(false);

        if !valid {
            tracing::warn!(email = %req.email, "Failed login attempt");
            return Err(AppError::InvalidCredentials);
        }

        let roles = vec!["user".to_string()];
        let access_token = crate::api::middleware::auth::create_access_token(
            &user.id.to_string(),
            roles,
            &self.jwt_secret,
        )?;

        let refresh_token = self.create_refresh_token(user.id).await?;

        tracing::info!(user_id = %user.id, "Login successful");

        Ok(TokenPair {
            access_token,
            refresh_token: refresh_token.token,
            token_type: "Bearer".to_string(),
            expires_in: self.access_token_expiry,
        })
    }

    async fn register(&self, req: RegisterRequest) -> Result<User, AppError> {
        // Check email uniqueness
        if self.user_repo.find_by_email(&req.email).await?.is_some() {
            return Err(AppError::Conflict("Email already registered".into()));
        }

        // Validate password strength
        self.validate_password_strength(&req.password)?;

        // Hash password with Argon2
        let password_hash = crate::security::hash_password(&req.password)?;

        let user = User {
            id: Uuid::new_v4(),
            name: req.name,
            email: req.email,
            password_hash,
            sync_status: SyncStatus::Synced,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let saved = self.user_repo.save(&user).await?;

        tracing::info!(user_id = %saved.id, email = %saved.email, "User registered");
        Ok(saved)
    }

    async fn refresh_token(&self, req: RefreshTokenRequest) -> Result<TokenPair, AppError> {
        let stored = self
            .token_repo
            .find_by_token(&req.refresh_token)
            .await?
            .ok_or(AppError::TokenExpired)?;

        if stored.revoked || stored.expires_at < Utc::now() {
            return Err(AppError::TokenExpired);
        }

        // Revoke old token
        self.token_repo.revoke(stored.id).await?;

        // Generate new tokens
        let user = self
            .user_repo
            .find_by_id(stored.user_id)
            .await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        let roles = vec!["user".to_string()];
        let access_token = crate::api::middleware::auth::create_access_token(
            &user.id.to_string(),
            roles,
            &self.jwt_secret,
        )?;

        let new_refresh = self.create_refresh_token(user.id).await?;

        Ok(TokenPair {
            access_token,
            refresh_token: new_refresh.token,
            token_type: "Bearer".to_string(),
            expires_in: self.access_token_expiry,
        })
    }

    async fn logout(&self, refresh_token: &str) -> Result<(), AppError> {
        if let Some(stored) = self.token_repo.find_by_token(refresh_token).await? {
            self.token_repo.revoke(stored.id).await?;
        }
        Ok(())
    }

    async fn logout_all(&self, user_id: Uuid) -> Result<(), AppError> {
        self.token_repo.revoke_all_by_user(user_id).await?;
        Ok(())
    }

    async fn change_password(
        &self,
        user_id: Uuid,
        req: ChangePasswordRequest,
    ) -> Result<(), AppError> {
        let mut user = self
            .user_repo
            .find_by_id(user_id)
            .await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        let valid = argon2::verify_encoded(&user.password_hash, req.current_password.as_bytes())
            .unwrap_or(false);

        if !valid {
            return Err(AppError::InvalidCredentials);
        }

        self.validate_password_strength(&req.new_password)?;

        user.password_hash = crate::security::hash_password(&req.new_password)?;
        self.user_repo.update(&user).await?;

        // Revoke all refresh tokens
        self.token_repo.revoke_all_by_user(user_id).await?;

        tracing::info!(user_id = %user_id, "Password changed");
        Ok(())
    }

    async fn verify_token(&self, token: &str) -> Result<Claims, AppError> {
        crate::api::middleware::auth::verify_token(token, &self.jwt_secret)
    }
}

impl AuthServiceImpl {
    async fn create_refresh_token(&self, user_id: Uuid) -> Result<RefreshToken, AppError> {
        let token_str = Uuid::new_v4().to_string();
        let refresh_token = RefreshToken {
            id: Uuid::new_v4(),
            token: token_str,
            user_id,
            expires_at: Utc::now() + chrono::Duration::seconds(self.refresh_token_expiry),
            revoked: false,
            revoked_at: None,
            created_at: Utc::now(),
        };

        self.token_repo.save(&refresh_token).await
    }
}
```

### Controller Layer (Axum Handlers)

```rust
// crates/server/src/api/handlers/auth_handler.rs
use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use crate::api::middleware::auth::Claims;
use crate::AppState;
use arcana_core::domain::models::auth::*;
use arcana_core::error::AppError;

pub async fn login(
    State(state): State<AppState>,
    Json(req): Json<LoginRequest>,
) -> Result<impl IntoResponse, AppError> {
    let token_pair = state.auth_service.login(req).await?;
    Ok(Json(token_pair))
}

pub async fn register(
    State(state): State<AppState>,
    Json(req): Json<RegisterRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user = state.auth_service.register(req).await?;
    Ok((
        StatusCode::CREATED,
        Json(serde_json::json!({
            "id": user.id.to_string(),
            "name": user.name,
            "email": user.email,
        })),
    ))
}

pub async fn refresh(
    State(state): State<AppState>,
    Json(req): Json<RefreshTokenRequest>,
) -> Result<impl IntoResponse, AppError> {
    let token_pair = state.auth_service.refresh_token(req).await?;
    Ok(Json(token_pair))
}

pub async fn logout(
    State(state): State<AppState>,
    Json(req): Json<RefreshTokenRequest>,
) -> Result<impl IntoResponse, AppError> {
    state.auth_service.logout(&req.refresh_token).await?;
    Ok(StatusCode::NO_CONTENT)
}

pub async fn logout_all(
    State(state): State<AppState>,
    claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    let user_id = uuid::Uuid::parse_str(&claims.sub)
        .map_err(|_| AppError::Internal("Invalid user ID in token".into()))?;
    state.auth_service.logout_all(user_id).await?;
    Ok(StatusCode::NO_CONTENT)
}

pub async fn change_password(
    State(state): State<AppState>,
    claims: Claims,
    Json(req): Json<ChangePasswordRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = uuid::Uuid::parse_str(&claims.sub)
        .map_err(|_| AppError::Internal("Invalid user ID in token".into()))?;
    state.auth_service.change_password(user_id, req).await?;
    Ok(StatusCode::NO_CONTENT)
}

pub async fn me(
    State(state): State<AppState>,
    claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    let user_id = uuid::Uuid::parse_str(&claims.sub)
        .map_err(|_| AppError::Internal("Invalid user ID in token".into()))?;
    let user = state.user_service.get_user(user_id).await?;
    match user {
        Some(dto) => Ok(Json(dto)),
        None => Err(AppError::NotFound("User not found".into())),
    }
}

// Router setup for auth
pub fn auth_routes() -> axum::Router<AppState> {
    use axum::routing::post;

    axum::Router::new()
        .route("/login", post(login))
        .route("/register", post(register))
        .route("/refresh", post(refresh))
        .route("/logout", post(logout))
        .route("/logout-all", post(logout_all))
        .route("/change-password", post(change_password))
        .route("/me", axum::routing::get(me))
}
```

---

## CRUD with REST and gRPC

### Product Service

```rust
// crates/core/src/domain/models/product.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "product_status", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ProductStatus {
    Draft,
    Active,
    Inactive,
    Archived,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Product {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub price: f64,
    pub stock: i32,
    pub category: Option<String>,
    pub status: ProductStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductDto {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub price: f64,
    pub stock: i32,
    pub category: Option<String>,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
}

impl From<Product> for ProductDto {
    fn from(p: Product) -> Self {
        Self {
            id: p.id.to_string(),
            name: p.name,
            description: p.description,
            price: p.price,
            stock: p.stock,
            category: p.category,
            status: format!("{:?}", p.status),
            created_at: p.created_at.to_rfc3339(),
            updated_at: p.updated_at.to_rfc3339(),
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct CreateProductRequest {
    pub name: String,
    pub description: Option<String>,
    pub price: f64,
    pub stock: Option<i32>,
    pub category: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateProductRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub price: Option<f64>,
    pub stock: Option<i32>,
    pub category: Option<String>,
    pub status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct StockUpdateRequest {
    pub quantity_change: i32,
}
```

### Service Implementation

```rust
// crates/core/src/domain/services/product_service.rs
use async_trait::async_trait;
use std::sync::Arc;
use uuid::Uuid;

use crate::domain::models::product::*;
use crate::domain::repositories::product_repository::ProductRepository;
use crate::error::AppError;

#[async_trait]
pub trait ProductService: Send + Sync {
    async fn get_product(&self, id: Uuid) -> Result<Option<ProductDto>, AppError>;
    async fn get_products(
        &self,
        page: u32,
        size: u32,
        category: Option<&str>,
        status: Option<&str>,
    ) -> Result<PaginatedResponse<ProductDto>, AppError>;
    async fn create_product(&self, req: CreateProductRequest) -> Result<ProductDto, AppError>;
    async fn update_product(&self, id: Uuid, req: UpdateProductRequest) -> Result<Option<ProductDto>, AppError>;
    async fn update_stock(&self, id: Uuid, quantity_change: i32) -> Result<ProductDto, AppError>;
    async fn delete_product(&self, id: Uuid) -> Result<bool, AppError>;
}

pub struct ProductServiceImpl {
    repo: Arc<dyn ProductRepository>,
    cache: Arc<dyn CacheService>,
}

impl ProductServiceImpl {
    pub fn new(repo: Arc<dyn ProductRepository>, cache: Arc<dyn CacheService>) -> Self {
        Self { repo, cache }
    }
}

#[async_trait]
impl ProductService for ProductServiceImpl {
    async fn get_product(&self, id: Uuid) -> Result<Option<ProductDto>, AppError> {
        let cache_key = format!("product:{}", id);

        // Try cache first
        if let Some(cached) = self.cache.get::<ProductDto>(&cache_key).await? {
            return Ok(Some(cached));
        }

        // Load from database
        let product = self.repo.find_by_id(id).await?;
        if let Some(ref p) = product {
            let dto = ProductDto::from(p.clone());
            self.cache.set(&cache_key, &dto, 3600).await?;
            return Ok(Some(dto));
        }

        Ok(None)
    }

    async fn get_products(
        &self,
        page: u32,
        size: u32,
        category: Option<&str>,
        status: Option<&str>,
    ) -> Result<PaginatedResponse<ProductDto>, AppError> {
        let (products, total) = self.repo.find_all(page, size, category, status).await?;
        Ok(PaginatedResponse {
            data: products.into_iter().map(ProductDto::from).collect(),
            page,
            size,
            total,
        })
    }

    async fn create_product(&self, req: CreateProductRequest) -> Result<ProductDto, AppError> {
        let product = Product {
            id: Uuid::new_v4(),
            name: req.name,
            description: req.description,
            price: req.price,
            stock: req.stock.unwrap_or(0),
            category: req.category,
            status: ProductStatus::Draft,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };

        let saved = self.repo.save(&product).await?;
        tracing::info!(product_id = %saved.id, "Product created");
        Ok(ProductDto::from(saved))
    }

    async fn update_product(
        &self,
        id: Uuid,
        req: UpdateProductRequest,
    ) -> Result<Option<ProductDto>, AppError> {
        let mut product = match self.repo.find_by_id(id).await? {
            Some(p) => p,
            None => return Ok(None),
        };

        if let Some(name) = req.name {
            product.name = name;
        }
        if let Some(desc) = req.description {
            product.description = Some(desc);
        }
        if let Some(price) = req.price {
            product.price = price;
        }
        if let Some(stock) = req.stock {
            product.stock = stock;
        }
        if let Some(category) = req.category {
            product.category = Some(category);
        }

        let updated = self.repo.update(&product).await?;

        // Invalidate cache
        self.cache.delete(&format!("product:{}", id)).await?;

        tracing::info!(product_id = %id, "Product updated");
        Ok(Some(ProductDto::from(updated)))
    }

    async fn update_stock(&self, id: Uuid, quantity_change: i32) -> Result<ProductDto, AppError> {
        let mut product = self
            .repo
            .find_by_id(id)
            .await?
            .ok_or_else(|| AppError::NotFound("Product not found".into()))?;

        let new_stock = product.stock + quantity_change;
        if new_stock < 0 {
            return Err(AppError::ValidationFailed(format!(
                "Insufficient stock. Available: {}, Requested: {}",
                product.stock,
                -quantity_change
            )));
        }

        product.stock = new_stock;
        let updated = self.repo.update(&product).await?;

        // Invalidate cache
        self.cache.delete(&format!("product:{}", id)).await?;

        if new_stock == 0 {
            tracing::warn!(product_id = %id, "Product out of stock");
        } else if new_stock <= 10 {
            tracing::warn!(product_id = %id, stock = new_stock, "Product low stock");
        }

        Ok(ProductDto::from(updated))
    }

    async fn delete_product(&self, id: Uuid) -> Result<bool, AppError> {
        match self.repo.find_by_id(id).await? {
            Some(_) => {
                self.repo.delete(id).await?;
                self.cache.delete(&format!("product:{}", id)).await?;
                tracing::info!(product_id = %id, "Product deleted");
                Ok(true)
            }
            None => Ok(false),
        }
    }
}
```

### REST Controller

```rust
// crates/server/src/api/handlers/product_handler.rs
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use uuid::Uuid;
use crate::api::middleware::auth::Claims;
use crate::AppState;
use arcana_core::domain::models::product::*;
use arcana_core::error::AppError;

pub async fn list_products(
    State(state): State<AppState>,
    Query(params): Query<ProductQueryParams>,
) -> Result<impl IntoResponse, AppError> {
    let page = params.page.unwrap_or(0);
    let size = params.size.unwrap_or(10);
    let result = state
        .product_service
        .get_products(page, size, params.category.as_deref(), params.status.as_deref())
        .await?;
    Ok(Json(result))
}

pub async fn get_product(
    State(state): State<AppState>,
    Path(product_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    match state.product_service.get_product(product_id).await? {
        Some(dto) => Ok(Json(dto)),
        None => Err(AppError::NotFound("Product not found".into())),
    }
}

pub async fn create_product(
    State(state): State<AppState>,
    claims: Claims,
    Json(req): Json<CreateProductRequest>,
) -> Result<impl IntoResponse, AppError> {
    crate::api::middleware::rbac::require_role("admin", &claims).await?;
    let product = state.product_service.create_product(req).await?;
    Ok((StatusCode::CREATED, Json(product)))
}

pub async fn update_product(
    State(state): State<AppState>,
    Path(product_id): Path<Uuid>,
    claims: Claims,
    Json(req): Json<UpdateProductRequest>,
) -> Result<impl IntoResponse, AppError> {
    crate::api::middleware::rbac::require_role("admin", &claims).await?;
    match state.product_service.update_product(product_id, req).await? {
        Some(dto) => Ok(Json(dto)),
        None => Err(AppError::NotFound("Product not found".into())),
    }
}

pub async fn update_stock(
    State(state): State<AppState>,
    Path(product_id): Path<Uuid>,
    claims: Claims,
    Json(req): Json<StockUpdateRequest>,
) -> Result<impl IntoResponse, AppError> {
    crate::api::middleware::rbac::require_role("admin", &claims).await?;
    let product = state
        .product_service
        .update_stock(product_id, req.quantity_change)
        .await?;
    Ok(Json(product))
}

pub async fn delete_product(
    State(state): State<AppState>,
    Path(product_id): Path<Uuid>,
    claims: Claims,
) -> Result<impl IntoResponse, AppError> {
    crate::api::middleware::rbac::require_role("admin", &claims).await?;
    let deleted = state.product_service.delete_product(product_id).await?;
    if deleted {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(AppError::NotFound("Product not found".into()))
    }
}

#[derive(Debug, Deserialize)]
pub struct ProductQueryParams {
    pub page: Option<u32>,
    pub size: Option<u32>,
    pub category: Option<String>,
    pub status: Option<String>,
}
```

### gRPC Servicer (Tonic)

```rust
// crates/server/src/grpc/product_service.rs
use tonic::{Request, Response, Status};
use std::sync::Arc;
use uuid::Uuid;

use crate::proto::product::{
    product_service_server::ProductService as GrpcProductService,
    GetProductRequest, ListProductsRequest, CreateProductRequest,
    UpdateStockRequest, DeleteProductRequest,
    ProductResponse, ListProductsResponse,
};
use arcana_core::domain::services::product_service::ProductService;
use arcana_core::error::AppError;

pub struct ProductGrpcService {
    service: Arc<dyn ProductService>,
}

impl ProductGrpcService {
    pub fn new(service: Arc<dyn ProductService>) -> Self {
        Self { service }
    }
}

#[tonic::async_trait]
impl GrpcProductService for ProductGrpcService {
    async fn get_product(
        &self,
        request: Request<GetProductRequest>,
    ) -> Result<Response<ProductResponse>, Status> {
        let req = request.into_inner();
        let id = Uuid::parse_str(&req.id)
            .map_err(|_| Status::invalid_argument("Invalid UUID"))?;

        let product = self
            .service
            .get_product(id)
            .await
            .map_err(|e| Status::from(e))?
            .ok_or_else(|| Status::not_found("Product not found"))?;

        Ok(Response::new(ProductResponse {
            id: product.id,
            name: product.name,
            description: product.description.unwrap_or_default(),
            price: product.price,
            stock: product.stock,
            category: product.category.unwrap_or_default(),
            status: product.status,
        }))
    }

    async fn list_products(
        &self,
        request: Request<ListProductsRequest>,
    ) -> Result<Response<ListProductsResponse>, Status> {
        let req = request.into_inner();
        let result = self
            .service
            .get_products(
                req.page,
                req.size,
                if req.category.is_empty() { None } else { Some(&req.category) },
                if req.status.is_empty() { None } else { Some(&req.status) },
            )
            .await
            .map_err(|e| Status::from(e))?;

        let products: Vec<ProductResponse> = result
            .data
            .into_iter()
            .map(|p| ProductResponse {
                id: p.id,
                name: p.name,
                description: p.description.unwrap_or_default(),
                price: p.price,
                stock: p.stock,
                category: p.category.unwrap_or_default(),
                status: p.status,
            })
            .collect();

        Ok(Response::new(ListProductsResponse {
            products,
            total: result.total,
            page: req.page,
            size: req.size,
            has_next: result.data.len() as u32 == req.size,
        }))
    }

    async fn create_product(
        &self,
        request: Request<CreateProductRequest>,
    ) -> Result<Response<ProductResponse>, Status> {
        let req = request.into_inner();
        let product = self
            .service
            .create_product(arcana_core::domain::models::product::CreateProductRequest {
                name: req.name,
                description: if req.description.is_empty() { None } else { Some(req.description) },
                price: req.price,
                stock: Some(req.stock),
                category: if req.category.is_empty() { None } else { Some(req.category) },
            })
            .await
            .map_err(|e| Status::from(e))?;

        Ok(Response::new(ProductResponse {
            id: product.id,
            name: product.name,
            description: product.description.unwrap_or_default(),
            price: product.price,
            stock: product.stock,
            category: product.category.unwrap_or_default(),
            status: product.status,
        }))
    }

    async fn update_stock(
        &self,
        request: Request<UpdateStockRequest>,
    ) -> Result<Response<ProductResponse>, Status> {
        let req = request.into_inner();
        let id = Uuid::parse_str(&req.product_id)
            .map_err(|_| Status::invalid_argument("Invalid UUID"))?;

        let product = self
            .service
            .update_stock(id, req.quantity_change)
            .await
            .map_err(|e| Status::from(e))?;

        Ok(Response::new(ProductResponse {
            id: product.id,
            name: product.name,
            description: product.description.unwrap_or_default(),
            price: product.price,
            stock: product.stock,
            category: product.category.unwrap_or_default(),
            status: product.status,
        }))
    }

    async fn delete_product(
        &self,
        request: Request<DeleteProductRequest>,
    ) -> Result<Response<()>, Status> {
        let req = request.into_inner();
        let id = Uuid::parse_str(&req.id)
            .map_err(|_| Status::invalid_argument("Invalid UUID"))?;

        let deleted = self
            .service
            .delete_product(id)
            .await
            .map_err(|e| Status::from(e))?;

        if deleted {
            Ok(Response::new(()))
        } else {
            Err(Status::not_found("Product not found"))
        }
    }
}
```

---

## WASM Plugin Integration

### Plugin Host with Wasmtime

```rust
// crates/server/src/plugins/host.rs
use wasmtime::*;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEvent {
    pub event_type: String,
    pub user_id: String,
    pub resource: String,
    pub action: String,
    pub timestamp: String,
    pub metadata: HashMap<String, serde_json::Value>,
}

pub struct PluginHost {
    engine: Engine,
    plugins: Arc<RwLock<Vec<PluginInstance>>>,
}

struct PluginInstance {
    name: String,
    module: Module,
}

impl PluginHost {
    pub async fn new(config: &PluginConfig) -> Result<Self, AppError> {
        let mut engine_config = wasmtime::Config::new();
        engine_config.wasm_component_model(true);
        engine_config.async_support(true);

        let engine = Engine::new(&engine_config)
            .map_err(|e| AppError::Internal(format!("WASM engine init failed: {}", e)))?;

        let mut plugins = Vec::new();

        for path in &config.plugin_paths {
            let module = Module::from_file(&engine, path)
                .map_err(|e| AppError::Internal(format!("Failed to load plugin {}: {}", path, e)))?;

            let name = PathBuf::from(path)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| "unknown".to_string());

            tracing::info!(plugin = %name, path = %path, "Loaded WASM plugin");
            plugins.push(PluginInstance { name, module });
        }

        Ok(Self {
            engine,
            plugins: Arc::new(RwLock::new(plugins)),
        })
    }

    pub async fn execute_audit(&self, event: &AuditEvent) -> Result<Vec<PluginResult>, AppError> {
        let plugins = self.plugins.read().await;
        let mut results = Vec::new();

        let event_json = serde_json::to_vec(event)
            .map_err(|e| AppError::Internal(e.to_string()))?;

        for plugin in plugins.iter() {
            let mut store = Store::new(&self.engine, ());
            let instance = Instance::new(&mut store, &plugin.module, &[])
                .map_err(|e| AppError::Internal(format!(
                    "Plugin {} instantiation failed: {}", plugin.name, e
                )))?;

            // Call the audit function in the WASM module
            if let Ok(func) = instance.get_typed_func::<(i32, i32), i32>(&mut store, "on_audit_event") {
                let mem = instance
                    .get_memory(&mut store, "memory")
                    .ok_or_else(|| AppError::Internal("Plugin has no memory export".into()))?;

                // Write event data to WASM memory
                mem.write(&mut store, 0, &event_json)
                    .map_err(|e| AppError::Internal(e.to_string()))?;

                let result = func
                    .call(&mut store, (0, event_json.len() as i32))
                    .map_err(|e| AppError::Internal(format!(
                        "Plugin {} execution failed: {}", plugin.name, e
                    )))?;

                results.push(PluginResult {
                    plugin_name: plugin.name.clone(),
                    return_code: result,
                });

                tracing::debug!(
                    plugin = %plugin.name,
                    event_type = %event.event_type,
                    result = result,
                    "Plugin audit executed"
                );
            }
        }

        Ok(results)
    }

    pub async fn reload_plugins(&self, config: &PluginConfig) -> Result<usize, AppError> {
        let mut plugins = self.plugins.write().await;
        plugins.clear();

        let mut count = 0;
        for path in &config.plugin_paths {
            let module = Module::from_file(&self.engine, path)
                .map_err(|e| AppError::Internal(format!("Failed to reload plugin {}: {}", path, e)))?;

            let name = PathBuf::from(path)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| "unknown".to_string());

            plugins.push(PluginInstance { name, module });
            count += 1;
        }

        tracing::info!(count, "Plugins reloaded");
        Ok(count)
    }
}

#[derive(Debug, Clone)]
pub struct PluginResult {
    pub plugin_name: String,
    pub return_code: i32,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PluginConfig {
    pub enabled: bool,
    pub plugin_paths: Vec<String>,
}
```

### Building a WASM Plugin

```rust
// plugins/arcana-audit-plugin/src/lib.rs
// Build with: cargo build --target wasm32-wasi --release
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct AuditEvent {
    event_type: String,
    user_id: String,
    resource: String,
    action: String,
    timestamp: String,
}

#[no_mangle]
pub extern "C" fn on_audit_event(ptr: i32, len: i32) -> i32 {
    let bytes = unsafe {
        std::slice::from_raw_parts(ptr as *const u8, len as usize)
    };

    let event: AuditEvent = match serde_json::from_slice(bytes) {
        Ok(e) => e,
        Err(_) => return -1, // Parse error
    };

    match event.event_type.as_str() {
        "user.login" => {
            // Log login event
            0 // Success
        }
        "user.data_access" => {
            // Check data access policy
            if event.action == "export" {
                1 // Flag for review
            } else {
                0
            }
        }
        "admin.config_change" => {
            // Always flag admin config changes
            1
        }
        _ => 0,
    }
}

#[no_mangle]
pub extern "C" fn get_plugin_version() -> i32 {
    1 // Version 1
}
```

```toml
# plugins/arcana-audit-plugin/Cargo.toml
[package]
name = "arcana-audit-plugin"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[profile.release]
opt-level = "s"
lto = true
```

---

## Distributed Job Queue

### Job Types and Handlers

```rust
// crates/server/src/infrastructure/queue/jobs.rs
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::infrastructure::queue::job_queue::{Job, JobHandler, JobPriority, JobQueue};
use arcana_core::error::AppError;

// Email jobs
#[derive(Debug, Serialize, Deserialize)]
pub struct WelcomeEmailPayload {
    pub user_id: String,
    pub email: String,
    pub name: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PasswordResetPayload {
    pub email: String,
    pub reset_token: String,
}

pub struct EmailJobHandler;

#[async_trait]
impl JobHandler for EmailJobHandler {
    async fn handle(&self, job: &Job) -> Result<(), AppError> {
        match job.job_type.as_str() {
            "email.welcome" => {
                let payload: WelcomeEmailPayload = serde_json::from_value(job.payload.clone())
                    .map_err(|e| AppError::Internal(e.to_string()))?;
                tracing::info!(email = %payload.email, "Sending welcome email");
                // Send email logic here
                Ok(())
            }
            "email.password_reset" => {
                let payload: PasswordResetPayload = serde_json::from_value(job.payload.clone())
                    .map_err(|e| AppError::Internal(e.to_string()))?;
                tracing::info!(email = %payload.email, "Sending password reset email");
                // Send password reset email
                Ok(())
            }
            _ => {
                tracing::warn!(job_type = %job.job_type, "Unknown email job type");
                Ok(())
            }
        }
    }
}

// Sync jobs
pub struct SyncJobHandler {
    user_service: Arc<dyn arcana_core::domain::services::user_service::UserService>,
}

impl SyncJobHandler {
    pub fn new(user_service: Arc<dyn arcana_core::domain::services::user_service::UserService>) -> Self {
        Self { user_service }
    }
}

#[async_trait]
impl JobHandler for SyncJobHandler {
    async fn handle(&self, job: &Job) -> Result<(), AppError> {
        match job.job_type.as_str() {
            "sync.pending_users" => {
                tracing::info!("Syncing pending users");
                // Sync logic
                Ok(())
            }
            "sync.cleanup_tokens" => {
                tracing::info!("Cleaning up expired tokens");
                // Cleanup logic
                Ok(())
            }
            _ => {
                tracing::warn!(job_type = %job.job_type, "Unknown sync job type");
                Ok(())
            }
        }
    }
}

// Helper functions for enqueuing jobs
pub async fn queue_welcome_email(
    queue: &JobQueue,
    user_id: &str,
    email: &str,
    name: &str,
) -> Result<String, AppError> {
    let job = Job {
        id: uuid::Uuid::new_v4().to_string(),
        job_type: "email.welcome".to_string(),
        payload: serde_json::to_value(WelcomeEmailPayload {
            user_id: user_id.to_string(),
            email: email.to_string(),
            name: name.to_string(),
        })
        .map_err(|e| AppError::Internal(e.to_string()))?,
        priority: JobPriority::Normal,
        max_retries: 3,
        retry_count: 0,
        created_at: chrono::Utc::now(),
        scheduled_at: None,
    };

    queue.enqueue(job).await
}

pub async fn queue_password_reset(
    queue: &JobQueue,
    email: &str,
    reset_token: &str,
) -> Result<String, AppError> {
    let job = Job {
        id: uuid::Uuid::new_v4().to_string(),
        job_type: "email.password_reset".to_string(),
        payload: serde_json::to_value(PasswordResetPayload {
            email: email.to_string(),
            reset_token: reset_token.to_string(),
        })
        .map_err(|e| AppError::Internal(e.to_string()))?,
        priority: JobPriority::High, // Password resets are high priority
        max_retries: 3,
        retry_count: 0,
        created_at: chrono::Utc::now(),
        scheduled_at: None,
    };

    queue.enqueue(job).await
}
```

### Scheduled Jobs

```rust
// crates/server/src/infrastructure/queue/scheduler.rs
use std::sync::Arc;
use tokio::time::{interval, Duration};

use crate::infrastructure::queue::job_queue::{Job, JobPriority, JobQueue};
use arcana_core::error::AppError;

pub struct JobScheduler {
    queue: Arc<JobQueue>,
}

impl JobScheduler {
    pub fn new(queue: Arc<JobQueue>) -> Self {
        Self { queue }
    }

    pub async fn start(&self) {
        let queue = self.queue.clone();

        // Sync pending users every 5 minutes
        let sync_queue = queue.clone();
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(300));
            loop {
                interval.tick().await;
                let job = Job {
                    id: uuid::Uuid::new_v4().to_string(),
                    job_type: "sync.pending_users".to_string(),
                    payload: serde_json::json!({}),
                    priority: JobPriority::Low,
                    max_retries: 1,
                    retry_count: 0,
                    created_at: chrono::Utc::now(),
                    scheduled_at: None,
                };
                if let Err(e) = sync_queue.enqueue(job).await {
                    tracing::error!(error = %e, "Failed to enqueue sync job");
                }
            }
        });

        // Cleanup expired tokens every hour
        let cleanup_queue = queue.clone();
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(3600));
            loop {
                interval.tick().await;
                let job = Job {
                    id: uuid::Uuid::new_v4().to_string(),
                    job_type: "sync.cleanup_tokens".to_string(),
                    payload: serde_json::json!({}),
                    priority: JobPriority::Low,
                    max_retries: 1,
                    retry_count: 0,
                    created_at: chrono::Utc::now(),
                    scheduled_at: None,
                };
                if let Err(e) = cleanup_queue.enqueue(job).await {
                    tracing::error!(error = %e, "Failed to enqueue cleanup job");
                }
            }
        });

        tracing::info!("Job scheduler started");
    }
}
```

---

## Event-Driven Architecture

### Domain Events with Redis Pub/Sub

```rust
// crates/server/src/infrastructure/events/publisher.rs
use async_trait::async_trait;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainEvent {
    pub id: String,
    pub event_type: String,
    pub data: serde_json::Value,
    pub timestamp: String,
    pub source: String,
}

#[async_trait]
pub trait EventPublisher: Send + Sync {
    async fn publish(&self, event_type: &str, data: serde_json::Value) -> Result<String, AppError>;
}

pub struct RedisEventPublisher {
    redis: Arc<redis::Client>,
    channel_prefix: String,
}

impl RedisEventPublisher {
    pub fn new(redis: Arc<redis::Client>) -> Self {
        Self {
            redis,
            channel_prefix: "events:".to_string(),
        }
    }
}

#[async_trait]
impl EventPublisher for RedisEventPublisher {
    async fn publish(&self, event_type: &str, data: serde_json::Value) -> Result<String, AppError> {
        let event = DomainEvent {
            id: Uuid::new_v4().to_string(),
            event_type: event_type.to_string(),
            data,
            timestamp: chrono::Utc::now().to_rfc3339(),
            source: "arcana-rust".to_string(),
        };

        let channel = format!("{}{}", self.channel_prefix, event_type);
        let event_json = serde_json::to_string(&event)
            .map_err(|e| AppError::Internal(e.to_string()))?;

        let mut conn = self.redis.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        conn.publish::<_, _, ()>(&channel, &event_json).await
            .map_err(|e| AppError::Cache(e.to_string()))?;

        tracing::info!(event_type = %event_type, event_id = %event.id, "Published domain event");
        Ok(event.id)
    }
}
```

### Event Consumer

```rust
// crates/server/src/infrastructure/events/consumer.rs
use async_trait::async_trait;
use redis::AsyncCommands;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

pub type EventHandler = Arc<dyn Fn(DomainEvent) -> BoxFuture<'static, Result<(), AppError>> + Send + Sync>;

pub struct RedisEventConsumer {
    redis: Arc<redis::Client>,
    handlers: Arc<RwLock<HashMap<String, EventHandler>>>,
    running: Arc<std::sync::atomic::AtomicBool>,
}

impl RedisEventConsumer {
    pub fn new(redis: Arc<redis::Client>) -> Self {
        Self {
            redis,
            handlers: Arc::new(RwLock::new(HashMap::new())),
            running: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }

    pub async fn register<F, Fut>(&self, event_type: &str, handler: F)
    where
        F: Fn(DomainEvent) -> Fut + Send + Sync + 'static,
        Fut: std::future::Future<Output = Result<(), AppError>> + Send + 'static,
    {
        let handler = Arc::new(move |event: DomainEvent| {
            Box::pin(handler(event)) as BoxFuture<'static, Result<(), AppError>>
        });

        self.handlers
            .write()
            .await
            .insert(event_type.to_string(), handler);
    }

    pub async fn start(&self) -> Result<(), AppError> {
        self.running.store(true, std::sync::atomic::Ordering::SeqCst);

        let mut pubsub = self.redis.get_async_connection().await
            .map_err(|e| AppError::Cache(e.to_string()))?
            .into_pubsub();

        let handlers = self.handlers.read().await;
        for event_type in handlers.keys() {
            let channel = format!("events:{}", event_type);
            pubsub.subscribe(&channel).await
                .map_err(|e| AppError::Cache(e.to_string()))?;
        }

        tracing::info!("Event consumer started, listening on {} channels", handlers.len());

        let handlers = self.handlers.clone();
        let running = self.running.clone();

        tokio::spawn(async move {
            let mut stream = pubsub.on_message();
            while running.load(std::sync::atomic::Ordering::SeqCst) {
                if let Some(msg) = stream.next().await {
                    let payload: String = msg.get_payload().unwrap_or_default();
                    match serde_json::from_str::<DomainEvent>(&payload) {
                        Ok(event) => {
                            let handlers = handlers.read().await;
                            if let Some(handler) = handlers.get(&event.event_type) {
                                if let Err(e) = handler(event.clone()).await {
                                    tracing::error!(
                                        event_type = %event.event_type,
                                        error = %e,
                                        "Event handler failed"
                                    );
                                }
                            }
                        }
                        Err(e) => {
                            tracing::error!(error = %e, "Failed to parse event");
                        }
                    }
                }
            }
        });

        Ok(())
    }

    pub fn stop(&self) {
        self.running.store(false, std::sync::atomic::Ordering::SeqCst);
    }
}
```

### Event Handler Registration

```rust
// crates/server/src/infrastructure/events/handlers.rs
use super::consumer::RedisEventConsumer;
use super::publisher::DomainEvent;
use crate::infrastructure::queue::jobs;
use arcana_core::error::AppError;
use std::sync::Arc;

pub async fn register_event_handlers(
    consumer: &RedisEventConsumer,
    job_queue: Arc<crate::infrastructure::queue::job_queue::JobQueue>,
) {
    let queue = job_queue.clone();
    consumer
        .register("auth.user_registered", move |event: DomainEvent| {
            let queue = queue.clone();
            async move {
                let user_id = event.data["userId"].as_str().unwrap_or_default();
                let email = event.data["email"].as_str().unwrap_or_default();
                let name = event.data["name"].as_str().unwrap_or_default();

                jobs::queue_welcome_email(&queue, user_id, email, name).await?;
                tracing::info!(user_id = %user_id, "Queued welcome email");
                Ok(())
            }
        })
        .await;

    consumer
        .register("auth.password_changed", |event: DomainEvent| async move {
            let user_id = event.data["userId"].as_str().unwrap_or_default();
            tracing::info!(user_id = %user_id, "Password changed event processed");
            Ok(())
        })
        .await;

    consumer
        .register("product.out_of_stock", |event: DomainEvent| async move {
            let product_id = event.data["productId"].as_str().unwrap_or_default();
            tracing::warn!(product_id = %product_id, "Product out of stock notification");
            Ok(())
        })
        .await;
}
```
