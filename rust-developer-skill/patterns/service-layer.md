# Service Layer Patterns

Deep dive into service layer patterns for Rust enterprise applications.

---

## Core Principles

1. **Single Responsibility**: Each service handles one domain
2. **Trait-based DI**: Use `Arc<dyn Trait>` for dependency injection
3. **Interface Segregation**: Define clear async traits
4. **Pure Business Logic**: No HTTP/gRPC concerns, no framework types

---

## Service Trait Pattern

```rust
// Define trait first (interface)
#[async_trait]
pub trait UserService: Send + Sync {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError>;
    async fn get_users(&self, page: u32, size: u32) -> Result<PaginatedResponse<UserDto>, AppError>;
    async fn create_user(&self, req: CreateUserRequest) -> Result<UserDto, AppError>;
    async fn update_user(&self, id: Uuid, req: UpdateUserRequest) -> Result<Option<UserDto>, AppError>;
    async fn delete_user(&self, id: Uuid) -> Result<bool, AppError>;
}

// Implement with concrete struct
pub struct UserServiceImpl {
    repo: Arc<dyn UserRepository>,
    cache: Arc<dyn CacheService>,
    events: Arc<dyn EventPublisher>,
}

impl UserServiceImpl {
    pub fn new(
        repo: Arc<dyn UserRepository>,
        cache: Arc<dyn CacheService>,
        events: Arc<dyn EventPublisher>,
    ) -> Self {
        Self { repo, cache, events }
    }
}

#[async_trait]
impl UserService for UserServiceImpl {
    // Implementation...
}
```

---

## Repository Injection Pattern

```rust
pub struct OrderServiceImpl {
    order_repo: Arc<dyn OrderRepository>,
    product_repo: Arc<dyn ProductRepository>,
    user_repo: Arc<dyn UserRepository>,
}

#[async_trait]
impl OrderService for OrderServiceImpl {
    async fn create_order(&self, user_id: Uuid, items: Vec<OrderItemDto>) -> Result<Order, AppError> {
        // Validate user exists
        let _user = self.user_repo.find_by_id(user_id).await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        // Validate products and stock
        for item in &items {
            let product = self.product_repo.find_by_id(item.product_id).await?
                .ok_or_else(|| AppError::NotFound(format!("Product not found: {}", item.product_id)))?;

            if product.stock < item.quantity as i32 {
                return Err(AppError::ValidationFailed(format!(
                    "Insufficient stock for product {}. Available: {}, Requested: {}",
                    item.product_id, product.stock, item.quantity
                )));
            }
        }

        // Create order
        self.order_repo.create_with_items(user_id, &items).await
    }
}
```

---

## Caching Pattern

```rust
pub struct ProductServiceImpl {
    repo: Arc<dyn ProductRepository>,
    cache: Arc<dyn CacheService>,
}

const CACHE_PREFIX: &str = "product:";
const CACHE_TTL: u64 = 3600; // 1 hour

#[async_trait]
impl ProductService for ProductServiceImpl {
    async fn get_product(&self, id: Uuid) -> Result<Option<ProductDto>, AppError> {
        let cache_key = format!("{}{}", CACHE_PREFIX, id);

        // Try cache first
        if let Some(cached) = self.cache.get::<ProductDto>(&cache_key).await? {
            return Ok(Some(cached));
        }

        // Load from database
        let product = self.repo.find_by_id(id).await?;
        if let Some(ref p) = product {
            let dto = ProductDto::from(p.clone());
            self.cache.set(&cache_key, &dto, CACHE_TTL).await?;
            return Ok(Some(dto));
        }

        Ok(None)
    }

    async fn update_product(&self, id: Uuid, req: UpdateProductRequest) -> Result<Option<ProductDto>, AppError> {
        let mut product = match self.repo.find_by_id(id).await? {
            Some(p) => p,
            None => return Ok(None),
        };

        // Update fields...
        if let Some(name) = req.name { product.name = name; }
        let updated = self.repo.update(&product).await?;

        // Invalidate cache
        self.cache.delete(&format!("{}{}", CACHE_PREFIX, id)).await?;

        Ok(Some(ProductDto::from(updated)))
    }
}
```

---

## Event Publishing Pattern

```rust
pub struct UserServiceImpl {
    repo: Arc<dyn UserRepository>,
    events: Arc<dyn EventPublisher>,
}

#[async_trait]
impl UserService for UserServiceImpl {
    async fn create_user(&self, req: CreateUserRequest) -> Result<UserDto, AppError> {
        let password_hash = crate::security::hash_password(&req.password)?;
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

        // Publish domain event
        self.events.publish("user.registered", serde_json::json!({
            "userId": saved.id.to_string(),
            "email": saved.email,
            "name": saved.name,
        })).await?;

        Ok(UserDto::from(saved))
    }

    async fn change_password(&self, user_id: Uuid, req: ChangePasswordRequest) -> Result<(), AppError> {
        let mut user = self.repo.find_by_id(user_id).await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        // Validate current password...
        user.password_hash = crate::security::hash_password(&req.new_password)?;
        self.repo.update(&user).await?;

        // Publish security event
        self.events.publish("user.password_changed", serde_json::json!({
            "userId": user_id.to_string(),
            "timestamp": chrono::Utc::now().to_rfc3339(),
        })).await?;

        Ok(())
    }
}
```

---

## Transaction Pattern (SQLx)

```rust
pub struct OrderServiceImpl {
    pool: PgPool,
    events: Arc<dyn EventPublisher>,
}

#[async_trait]
impl OrderService for OrderServiceImpl {
    async fn create_order(&self, user_id: Uuid, items: Vec<OrderItemDto>) -> Result<Order, AppError> {
        // Use SQLx transaction
        let mut tx = self.pool.begin().await?;

        // Create order
        let order = sqlx::query_as::<_, Order>(
            "INSERT INTO orders (id, user_id, status, total_amount) VALUES ($1, $2, $3, $4) RETURNING *"
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind("PENDING")
        .bind(0.0f64)
        .fetch_one(&mut *tx)
        .await?;

        let mut total_amount = 0.0;

        for item in &items {
            let product = sqlx::query_as::<_, Product>(
                "SELECT * FROM products WHERE id = $1 FOR UPDATE"
            )
            .bind(item.product_id)
            .fetch_optional(&mut *tx)
            .await?
            .ok_or_else(|| AppError::NotFound("Product not found".into()))?;

            if product.stock < item.quantity as i32 {
                // Transaction will be rolled back on drop
                return Err(AppError::ValidationFailed("Insufficient stock".into()));
            }

            sqlx::query(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)"
            )
            .bind(order.id)
            .bind(item.product_id)
            .bind(item.quantity as i32)
            .bind(product.price)
            .execute(&mut *tx)
            .await?;

            sqlx::query("UPDATE products SET stock = stock - $1 WHERE id = $2")
                .bind(item.quantity as i32)
                .bind(item.product_id)
                .execute(&mut *tx)
                .await?;

            total_amount += product.price * item.quantity as f64;
        }

        // Update order total
        let final_order = sqlx::query_as::<_, Order>(
            "UPDATE orders SET total_amount = $1 WHERE id = $2 RETURNING *"
        )
        .bind(total_amount)
        .bind(order.id)
        .fetch_one(&mut *tx)
        .await?;

        // Commit transaction
        tx.commit().await?;

        // Publish event after successful transaction
        self.events.publish("order.created", serde_json::json!({
            "orderId": final_order.id.to_string(),
            "userId": user_id.to_string(),
            "totalAmount": total_amount,
        })).await?;

        Ok(final_order)
    }
}
```

---

## Validation Pattern

```rust
pub struct AuthServiceImpl {
    user_repo: Arc<dyn UserRepository>,
}

#[async_trait]
impl AuthService for AuthServiceImpl {
    async fn register(&self, req: RegisterRequest) -> Result<User, AppError> {
        // Business validation (beyond serde deserialization)
        if self.user_repo.find_by_email(&req.email).await?.is_some() {
            return Err(AppError::Conflict("Email already registered".into()));
        }

        // Password strength validation
        validate_password_strength(&req.password)?;

        // Create user
        let password_hash = crate::security::hash_password(&req.password)?;
        let user = User {
            id: Uuid::new_v4(),
            name: req.name,
            email: req.email,
            password_hash,
            sync_status: SyncStatus::Synced,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };

        self.user_repo.save(&user).await
    }
}

fn validate_password_strength(password: &str) -> Result<(), AppError> {
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
```

---

## Error Handling Pattern

```rust
#[async_trait]
impl UserService for UserServiceImpl {
    async fn get_user(&self, id: Uuid) -> Result<Option<UserDto>, AppError> {
        // Let AppError::Database propagate via ? operator
        let user = self.repo.find_by_id(id).await?;
        Ok(user.map(UserDto::from))
    }

    async fn update_user(&self, id: Uuid, req: UpdateUserRequest) -> Result<UserDto, AppError> {
        let mut user = self.repo.find_by_id(id).await?
            .ok_or_else(|| AppError::NotFound(format!("User not found: {}", id)))?;

        if let Some(ref email) = req.email {
            if let Some(existing) = self.repo.find_by_email(email).await? {
                if existing.id != id {
                    return Err(AppError::Conflict("Email already in use".into()));
                }
            }
        }

        if let Some(name) = req.name { user.name = name; }
        if let Some(email) = req.email { user.email = email; }

        let updated = self.repo.update(&user).await?;
        Ok(UserDto::from(updated))
    }
}
```

---

## Testing Service Layer

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use std::sync::Arc;

    fn mock_user() -> User {
        User {
            id: Uuid::new_v4(),
            name: "Test User".to_string(),
            email: "test@example.com".to_string(),
            password_hash: "hashed".to_string(),
            sync_status: SyncStatus::Synced,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        }
    }

    #[tokio::test]
    async fn test_get_user_cache_hit() {
        let mut mock_cache = MockCache::new();
        let dto = UserDto::from(mock_user());

        mock_cache
            .expect_get::<UserDto>()
            .returning(move |_| Ok(Some(dto.clone())));

        let mock_repo = MockUserRepo::new();
        mock_repo.expect_find_by_id().times(0); // Should NOT hit DB

        let service = UserServiceImpl::new(
            Arc::new(mock_repo),
            Arc::new(mock_cache),
            Arc::new(MockEventPublisher::new()),
        );

        let result = service.get_user(Uuid::new_v4()).await.unwrap();
        assert!(result.is_some());
    }

    #[tokio::test]
    async fn test_create_user_duplicate_email() {
        let mut mock_repo = MockUserRepo::new();

        mock_repo
            .expect_find_by_email()
            .with(eq("existing@example.com"))
            .returning(|_| Ok(Some(mock_user())));

        let service = UserServiceImpl::new(
            Arc::new(mock_repo),
            Arc::new(MockCache::new()),
            Arc::new(MockEventPublisher::new()),
        );

        let result = service
            .create_user(CreateUserRequest {
                name: "New User".to_string(),
                email: "existing@example.com".to_string(),
                password: "Password123".to_string(),
            })
            .await;

        assert!(matches!(result, Err(AppError::Conflict(_))));
    }
}
```
