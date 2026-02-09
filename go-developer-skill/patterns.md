# Go Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Service Layer Patterns](#service-layer-patterns)
3. [Data Access Patterns](#data-access-patterns)
4. [API Design Patterns](#api-design-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Testing Patterns](#testing-patterns)
7. [Event-Driven Patterns](#event-driven-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
+---------------------------------------------------------------+
|                         Controllers                            |
|  +-------------------------+  +----------------------------+   |
|  |   Gin HTTP Handlers     |  |      gRPC Servers          |   |
|  |   (REST API)            |  |      (Protobuf)            |   |
|  +------------+------------+  +--------------+-------------+   |
|               |                              |                  |
|               +---------------+--------------+                  |
|                               |                                 |
+-------------------------------+---------------------------------+
|                         Services                                |
|  +-------------------------------------------------------------+
|  |  Business Logic | Validation | Logging                      |
|  |                                                              |
|  |  Pure Go interfaces + structs, no framework deps             |
|  +-------------------------------------------------------------+
|                               |                                 |
+-------------------------------+---------------------------------+
|                       Repositories / DAO                        |
|  +----------------+ +----------------+ +-----------------------+|
|  | GORM           | | Redis Cache    | | External API Clients  ||
|  | (MySQL/PG)     | | Repository     | | (gRPC/REST)           ||
|  +----------------+ +----------------+ +-----------------------+|
+---------------------------------------------------------------+
```

### Implementation

```go
// Controller Layer - HTTP concerns only
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

// Service Layer - Business logic
type userServiceImpl struct {
    repo   repository.UserRepository
    cache  *redis.Client
    logger *zap.Logger
}

func (s *userServiceImpl) GetUser(ctx context.Context, userID string) (*entity.UserDTO, error) {
    // Try cache first
    cacheKey := fmt.Sprintf("user:%s", userID)
    cached, err := s.cache.Get(ctx, cacheKey).Result()
    if err == nil && cached != "" {
        var dto entity.UserDTO
        json.Unmarshal([]byte(cached), &dto)
        return &dto, nil
    }

    // Load from database
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, nil
    }

    dto := entity.ToUserDTO(user)
    data, _ := json.Marshal(dto)
    s.cache.Set(ctx, cacheKey, data, 30*time.Minute)

    return dto, nil
}

// Repository Layer - Data access
type userRepositoryImpl struct {
    db *gorm.DB
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
```

### fx Dependency Injection Container

```go
// internal/di/module.go
package di

import (
    "go.uber.org/fx"

    "arcana-cloud-go/internal/config"
    httpctrl "arcana-cloud-go/internal/controller/http"
    "arcana-cloud-go/internal/domain/repository"
    "arcana-cloud-go/internal/domain/service"
    "arcana-cloud-go/internal/middleware"
    "arcana-cloud-go/internal/security"
)

var Module = fx.Options(
    // Infrastructure
    fx.Provide(config.NewConfig),
    fx.Provide(NewDatabase),
    fx.Provide(NewRedisClient),
    fx.Provide(NewLogger),

    // Security
    fx.Provide(security.NewJWTService),

    // Repositories
    fx.Provide(
        fx.Annotate(
            repository.NewUserRepository,
            fx.As(new(repository.UserRepository)),
        ),
    ),

    // Services
    fx.Provide(
        fx.Annotate(
            service.NewUserService,
            fx.As(new(service.UserService)),
        ),
    ),

    // Middleware
    fx.Provide(middleware.NewAuthMiddleware),

    // Controllers
    fx.Provide(httpctrl.NewUserController),
    fx.Provide(httpctrl.NewAuthController),

    // Router
    fx.Provide(httpctrl.NewRouter),
    fx.Invoke(StartServer),
)

// Usage in main.go
// func main() {
//     fx.New(di.Module).Run()
// }
```

---

## Service Layer Patterns

### Strategy Pattern

```go
// Pricing strategy interface
type PricingStrategy interface {
    Calculate(basePrice float64, quantity int) float64
}

type RegularPricing struct{}

func (p *RegularPricing) Calculate(basePrice float64, quantity int) float64 {
    return basePrice * float64(quantity)
}

type BulkPricing struct {
    Threshold    int
    DiscountRate float64
}

func (p *BulkPricing) Calculate(basePrice float64, quantity int) float64 {
    total := basePrice * float64(quantity)
    if quantity >= p.Threshold {
        return total * (1 - p.DiscountRate)
    }
    return total
}

type PremiumPricing struct {
    DiscountRate float64
}

func (p *PremiumPricing) Calculate(basePrice float64, quantity int) float64 {
    return basePrice * float64(quantity) * (1 - p.DiscountRate)
}

// Strategy factory
func NewPricingStrategy(strategyType string) (PricingStrategy, error) {
    switch strategyType {
    case "regular":
        return &RegularPricing{}, nil
    case "bulk":
        return &BulkPricing{Threshold: 10, DiscountRate: 0.10}, nil
    case "premium":
        return &PremiumPricing{DiscountRate: 0.15}, nil
    default:
        return nil, fmt.Errorf("unknown pricing strategy: %s", strategyType)
    }
}

// Usage in service
type orderServiceImpl struct {
    repo repository.OrderRepository
}

func (s *orderServiceImpl) CalculateOrderTotal(items []OrderItem, customerType string) (float64, error) {
    strategy, err := NewPricingStrategy(customerType)
    if err != nil {
        return 0, err
    }

    var total float64
    for _, item := range items {
        total += strategy.Calculate(item.Price, item.Quantity)
    }
    return total, nil
}
```

### Command Pattern

```go
// Command interface
type Command[T any] interface {
    Execute(ctx context.Context) (T, error)
}

// Commands
type CreateUserCommand struct {
    DTO    *CreateUserDTO
    Repo   repository.UserRepository
    Logger *zap.Logger
}

func (c *CreateUserCommand) Execute(ctx context.Context) (*entity.User, error) {
    existing, err := c.Repo.FindByEmail(ctx, c.DTO.Email)
    if err != nil {
        return nil, fmt.Errorf("failed to check email: %w", err)
    }
    if existing != nil {
        return nil, entity.ErrConflictError("Email already exists")
    }

    hash, _ := bcrypt.GenerateFromPassword([]byte(c.DTO.Password), bcrypt.DefaultCost)
    user := &entity.User{
        Name:         c.DTO.Name,
        Email:        c.DTO.Email,
        PasswordHash: string(hash),
        SyncStatus:   entity.SyncStatusSynced,
    }

    if err := c.Repo.Save(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to save user: %w", err)
    }

    c.Logger.Info("user created", zap.String("userID", user.ID))
    return user, nil
}

// Command bus
type CommandBus struct{}

func (b *CommandBus) Dispatch[T any](ctx context.Context, cmd Command[T]) (T, error) {
    return cmd.Execute(ctx)
}

// Usage
// bus := &CommandBus{}
// user, err := bus.Dispatch(ctx, &CreateUserCommand{DTO: dto, Repo: repo, Logger: logger})
```

### Unit of Work Pattern with GORM Transactions

```go
type UnitOfWork struct {
    db *gorm.DB
}

func NewUnitOfWork(db *gorm.DB) *UnitOfWork {
    return &UnitOfWork{db: db}
}

func (uow *UnitOfWork) Execute(ctx context.Context, fn func(tx *gorm.DB) error) error {
    return uow.db.WithContext(ctx).Transaction(fn)
}

// Usage in service
type orderServiceImpl struct {
    db     *gorm.DB
    logger *zap.Logger
}

func (s *orderServiceImpl) CreateOrder(ctx context.Context, userID string, items []OrderItemDTO) (*Order, error) {
    uow := NewUnitOfWork(s.db)

    var order *Order
    err := uow.Execute(ctx, func(tx *gorm.DB) error {
        // Create order
        order = &Order{
            UserID: userID,
            Status: OrderStatusPending,
        }
        if err := tx.Create(order).Error; err != nil {
            return err
        }

        var totalAmount float64
        for _, item := range items {
            // Check stock
            var product Product
            if err := tx.Where("id = ?", item.ProductID).First(&product).Error; err != nil {
                return err
            }
            if product.Stock < item.Quantity {
                return fmt.Errorf("insufficient stock for product %s", item.ProductID)
            }

            // Create order item
            orderItem := &OrderItem{
                OrderID:   order.ID,
                ProductID: item.ProductID,
                Quantity:  item.Quantity,
                Price:     product.Price,
            }
            if err := tx.Create(orderItem).Error; err != nil {
                return err
            }

            // Update stock
            if err := tx.Model(&Product{}).
                Where("id = ?", item.ProductID).
                Update("stock", gorm.Expr("stock - ?", item.Quantity)).Error; err != nil {
                return err
            }

            totalAmount += product.Price * float64(item.Quantity)
        }

        // Update order total
        return tx.Model(order).Update("total_amount", totalAmount).Error
    })

    if err != nil {
        return nil, fmt.Errorf("failed to create order: %w", err)
    }

    return order, nil
}
```

---

## Data Access Patterns

### Repository Pattern with Generics

```go
// Base repository interface using Go generics
type Repository[T any] interface {
    FindByID(ctx context.Context, id string) (*T, error)
    FindAll(ctx context.Context, page, size int) ([]*T, int64, error)
    Save(ctx context.Context, entity *T) error
    Update(ctx context.Context, entity *T) error
    Delete(ctx context.Context, entity *T) error
}

// Generic GORM implementation
type GORMRepository[T any] struct {
    db *gorm.DB
}

func NewGORMRepository[T any](db *gorm.DB) *GORMRepository[T] {
    return &GORMRepository[T]{db: db}
}

func (r *GORMRepository[T]) FindByID(ctx context.Context, id string) (*T, error) {
    var entity T
    if err := r.db.WithContext(ctx).Where("id = ?", id).First(&entity).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &entity, nil
}

func (r *GORMRepository[T]) FindAll(ctx context.Context, page, size int) ([]*T, int64, error) {
    var entities []*T
    var total int64

    r.db.WithContext(ctx).Model(new(T)).Count(&total)

    offset := page * size
    if err := r.db.WithContext(ctx).
        Order("created_at DESC").
        Offset(offset).Limit(size).
        Find(&entities).Error; err != nil {
        return nil, 0, err
    }
    return entities, total, nil
}

func (r *GORMRepository[T]) Save(ctx context.Context, entity *T) error {
    return r.db.WithContext(ctx).Create(entity).Error
}

func (r *GORMRepository[T]) Update(ctx context.Context, entity *T) error {
    return r.db.WithContext(ctx).Save(entity).Error
}

func (r *GORMRepository[T]) Delete(ctx context.Context, entity *T) error {
    return r.db.WithContext(ctx).Delete(entity).Error
}

// Specific repository with custom methods
type userRepositoryImpl struct {
    *GORMRepository[entity.User]
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) UserRepository {
    return &userRepositoryImpl{
        GORMRepository: NewGORMRepository[entity.User](db),
        db:             db,
    }
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

func (r *userRepositoryImpl) FindPendingSync(ctx context.Context) ([]*entity.User, error) {
    var users []*entity.User
    if err := r.db.WithContext(ctx).
        Where("sync_status = ?", entity.SyncStatusPending).
        Find(&users).Error; err != nil {
        return nil, err
    }
    return users, nil
}
```

### Cache-Aside Pattern

```go
type CacheAside struct {
    redis      *redis.Client
    defaultTTL time.Duration
    prefix     string
}

func NewCacheAside(redis *redis.Client, prefix string, ttl time.Duration) *CacheAside {
    return &CacheAside{
        redis:      redis,
        defaultTTL: ttl,
        prefix:     prefix,
    }
}

func (c *CacheAside) makeKey(key string) string {
    return c.prefix + key
}

func (c *CacheAside) Get(ctx context.Context, key string, dest interface{}) error {
    data, err := c.redis.Get(ctx, c.makeKey(key)).Bytes()
    if err == redis.Nil {
        return redis.Nil
    }
    if err != nil {
        return err
    }
    return json.Unmarshal(data, dest)
}

func (c *CacheAside) Set(ctx context.Context, key string, value interface{}, ttl ...time.Duration) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }

    duration := c.defaultTTL
    if len(ttl) > 0 {
        duration = ttl[0]
    }

    return c.redis.Set(ctx, c.makeKey(key), data, duration).Err()
}

func (c *CacheAside) Delete(ctx context.Context, key string) error {
    return c.redis.Del(ctx, c.makeKey(key)).Err()
}

func (c *CacheAside) GetOrLoad(
    ctx context.Context,
    key string,
    dest interface{},
    loader func() (interface{}, error),
    ttl ...time.Duration,
) error {
    if err := c.Get(ctx, key, dest); err == nil {
        return nil // Cache hit
    }

    value, err := loader()
    if err != nil {
        return err
    }

    if value != nil {
        if err := c.Set(ctx, key, value, ttl...); err != nil {
            // Log but don't fail on cache write error
            return nil
        }
    }

    // Assign loaded value to dest
    data, _ := json.Marshal(value)
    return json.Unmarshal(data, dest)
}

// Usage in service
type userServiceImpl struct {
    repo  repository.UserRepository
    cache *CacheAside
}

func (s *userServiceImpl) GetUser(ctx context.Context, userID string) (*entity.UserDTO, error) {
    var dto entity.UserDTO
    err := s.cache.GetOrLoad(ctx, userID, &dto, func() (interface{}, error) {
        user, err := s.repo.FindByID(ctx, userID)
        if err != nil {
            return nil, err
        }
        if user == nil {
            return nil, nil
        }
        return entity.ToUserDTO(user), nil
    }, 30*time.Minute)

    if err != nil {
        return nil, err
    }
    return &dto, nil
}
```

---

## API Design Patterns

### Router Factory Pattern

```go
// internal/controller/http/router.go
package http

import (
    "github.com/gin-gonic/gin"

    "arcana-cloud-go/internal/middleware"
)

type Router struct {
    engine         *gin.Engine
    authMiddleware *middleware.AuthMiddleware
    userCtrl       *UserController
    authCtrl       *AuthController
    productCtrl    *ProductController
}

func NewRouter(
    authMW *middleware.AuthMiddleware,
    userCtrl *UserController,
    authCtrl *AuthController,
    productCtrl *ProductController,
) *Router {
    engine := gin.Default()
    engine.Use(middleware.ErrorHandler(nil))
    engine.Use(middleware.CORS())

    r := &Router{
        engine:         engine,
        authMiddleware: authMW,
        userCtrl:       userCtrl,
        authCtrl:       authCtrl,
        productCtrl:    productCtrl,
    }

    r.setupRoutes()
    return r
}

func (r *Router) setupRoutes() {
    // Health check
    r.engine.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "ok"})
    })

    // API v1
    v1 := r.engine.Group("/api/v1")

    authMW := r.authMiddleware.RequireAuth()
    adminMW := r.authMiddleware.RequireRole("admin")

    r.authCtrl.RegisterRoutes(v1, authMW)
    r.userCtrl.RegisterRoutes(v1, authMW)
    r.productCtrl.RegisterRoutes(v1, authMW, adminMW)
}

func (r *Router) Run(port int) error {
    return r.engine.Run(fmt.Sprintf(":%d", port))
}
```

### Request/Response DTO Pattern

```go
// pkg/response/response.go
package response

import (
    "math"
    "time"
)

type APIResponse struct {
    Data      interface{} `json:"data"`
    Message   string      `json:"message"`
    Timestamp string      `json:"timestamp"`
}

type PaginatedResponse struct {
    Data        interface{} `json:"data"`
    Page        int         `json:"page"`
    Size        int         `json:"size"`
    Total       int64       `json:"total"`
    TotalPages  int         `json:"totalPages"`
    HasNext     bool        `json:"hasNext"`
    HasPrevious bool        `json:"hasPrevious"`
}

type ErrorResponse struct {
    Code      string      `json:"code"`
    Message   string      `json:"message"`
    Details   interface{} `json:"details,omitempty"`
    Timestamp string      `json:"timestamp"`
}

func Success(data interface{}, message string) APIResponse {
    if message == "" {
        message = "Success"
    }
    return APIResponse{
        Data:      data,
        Message:   message,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
    }
}

func Paginated(data interface{}, page, size int, total int64) PaginatedResponse {
    totalPages := int(math.Ceil(float64(total) / float64(size)))
    return PaginatedResponse{
        Data:        data,
        Page:        page,
        Size:        size,
        Total:       total,
        TotalPages:  totalPages,
        HasNext:     page < totalPages-1,
        HasPrevious: page > 0,
    }
}

func Error(code, message string, details interface{}) ErrorResponse {
    return ErrorResponse{
        Code:      code,
        Message:   message,
        Details:   details,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
    }
}
```

### Middleware Chain Pattern

```go
// internal/middleware/logger.go
package middleware

import (
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

func RequestLogger(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path

        c.Next()

        latency := time.Since(start)
        statusCode := c.Writer.Status()

        logger.Info("request",
            zap.String("method", c.Request.Method),
            zap.String("path", path),
            zap.Int("status", statusCode),
            zap.Duration("latency", latency),
            zap.String("ip", c.ClientIP()),
            zap.String("user-agent", c.Request.UserAgent()),
        )
    }
}

// internal/middleware/cors.go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func CORS() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        c.Header("Access-Control-Max-Age", "86400")

        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }

        c.Next()
    }
}

// internal/middleware/rate_limiter.go
package middleware

import (
    "net/http"
    "sync"
    "time"

    "github.com/gin-gonic/gin"
)

type RateLimiter struct {
    mu       sync.Mutex
    requests map[string][]time.Time
    limit    int
    window   time.Duration
}

func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
    return &RateLimiter{
        requests: make(map[string][]time.Time),
        limit:    limit,
        window:   window,
    }
}

func (rl *RateLimiter) Middleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        ip := c.ClientIP()

        rl.mu.Lock()
        now := time.Now()
        windowStart := now.Add(-rl.window)

        // Clean old requests
        if reqs, exists := rl.requests[ip]; exists {
            filtered := make([]time.Time, 0)
            for _, t := range reqs {
                if t.After(windowStart) {
                    filtered = append(filtered, t)
                }
            }
            rl.requests[ip] = filtered
        }

        if len(rl.requests[ip]) >= rl.limit {
            rl.mu.Unlock()
            c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
                "code":    "RATE_LIMITED",
                "message": "Too many requests",
            })
            return
        }

        rl.requests[ip] = append(rl.requests[ip], now)
        rl.mu.Unlock()

        c.Next()
    }
}
```

---

## Error Handling Patterns

### Custom Error Hierarchy

```go
// internal/domain/entity/errors.go
package entity

import (
    "fmt"
    "net/http"
)

type ErrorCode string

const (
    ErrNetworkUnavailable ErrorCode = "NETWORK_UNAVAILABLE"
    ErrTimeout            ErrorCode = "TIMEOUT"
    ErrServiceUnavailable ErrorCode = "SERVICE_UNAVAILABLE"
    ErrUnauthorized       ErrorCode = "UNAUTHORIZED"
    ErrTokenExpired       ErrorCode = "TOKEN_EXPIRED"
    ErrInvalidCredentials ErrorCode = "INVALID_CREDENTIALS"
    ErrNotFound           ErrorCode = "NOT_FOUND"
    ErrValidationFailed   ErrorCode = "VALIDATION_FAILED"
    ErrConflict           ErrorCode = "CONFLICT"
    ErrInternal           ErrorCode = "INTERNAL_ERROR"
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
        Code: ErrValidationFailed, Message: message,
        HTTPStatus: http.StatusBadRequest, Details: details,
    }
}

func ErrConflictError(message string) *AppError {
    return NewAppError(ErrConflict, message, http.StatusConflict)
}

func ErrInternalError(message string) *AppError {
    return NewAppError(ErrInternal, message, http.StatusInternalServerError)
}

// Sentinel errors for specific entities
type UserNotFoundError struct {
    UserID string
}

func (e *UserNotFoundError) Error() string {
    return fmt.Sprintf("user not found: %s", e.UserID)
}

type EmailAlreadyExistsError struct {
    Email string
}

func (e *EmailAlreadyExistsError) Error() string {
    return fmt.Sprintf("email already registered: %s", e.Email)
}

// Error checking helpers
func IsNotFound(err error) bool {
    if appErr, ok := err.(*AppError); ok {
        return appErr.Code == ErrNotFound
    }
    return false
}

func IsValidation(err error) bool {
    if appErr, ok := err.(*AppError); ok {
        return appErr.Code == ErrValidationFailed
    }
    return false
}

func IsUnauthorized(err error) bool {
    if appErr, ok := err.(*AppError); ok {
        return appErr.Code == ErrUnauthorized
    }
    return false
}
```

### Error Wrapping Pattern

```go
// Always wrap errors with context using %w
func (s *userServiceImpl) GetUser(ctx context.Context, userID string) (*entity.UserDTO, error) {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("userService.GetUser(%s): %w", userID, err)
    }
    if user == nil {
        return nil, nil
    }
    return entity.ToUserDTO(user), nil
}

// Check wrapped errors with errors.Is and errors.As
func (ctrl *UserController) GetUser(c *gin.Context) {
    user, err := ctrl.userService.GetUser(c.Request.Context(), c.Param("id"))
    if err != nil {
        var appErr *entity.AppError
        if errors.As(err, &appErr) {
            c.JSON(appErr.HTTPStatus, appErr)
            return
        }
        c.JSON(500, gin.H{"error": "Internal server error"})
        return
    }
    if user == nil {
        c.JSON(404, gin.H{"error": "User not found"})
        return
    }
    c.JSON(200, user)
}
```

---

## Testing Patterns

### Test Fixtures

```go
// tests/fixtures/fixtures.go
package fixtures

import (
    "time"

    "github.com/google/uuid"

    "arcana-cloud-go/internal/domain/entity"
)

func NewMockUser(overrides ...func(*entity.User)) *entity.User {
    user := &entity.User{
        ID:           uuid.New().String(),
        Name:         "Test User",
        Email:        "test@example.com",
        PasswordHash: "$2a$10$hashedpassword",
        SyncStatus:   entity.SyncStatusSynced,
        CreatedAt:    time.Now(),
        UpdatedAt:    time.Now(),
    }
    for _, fn := range overrides {
        fn(user)
    }
    return user
}

func NewMockUsers(count int) []*entity.User {
    users := make([]*entity.User, count)
    for i := 0; i < count; i++ {
        users[i] = NewMockUser(func(u *entity.User) {
            u.ID = fmt.Sprintf("user-%d", i)
            u.Name = fmt.Sprintf("User %d", i)
            u.Email = fmt.Sprintf("user%d@example.com", i)
        })
    }
    return users
}
```

### Service Layer Tests with testify

```go
// internal/domain/service/user_service_test.go
package service

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/suite"
    "go.uber.org/zap"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/tests/fixtures"
)

type UserServiceTestSuite struct {
    suite.Suite
    svc      UserService
    mockRepo *MockUserRepository
    logger   *zap.Logger
}

func (s *UserServiceTestSuite) SetupTest() {
    s.mockRepo = new(MockUserRepository)
    s.logger, _ = zap.NewDevelopment()
    s.svc = NewUserService(s.mockRepo, s.logger)
}

func (s *UserServiceTestSuite) TestGetUser_Found() {
    mockUser := fixtures.NewMockUser()
    s.mockRepo.On("FindByID", mock.Anything, mockUser.ID).Return(mockUser, nil)

    result, err := s.svc.GetUser(context.Background(), mockUser.ID)

    s.NoError(err)
    s.NotNil(result)
    s.Equal(mockUser.ID, result.ID)
    s.mockRepo.AssertExpectations(s.T())
}

func (s *UserServiceTestSuite) TestGetUser_NotFound() {
    s.mockRepo.On("FindByID", mock.Anything, "nonexistent").Return(nil, nil)

    result, err := s.svc.GetUser(context.Background(), "nonexistent")

    s.NoError(err)
    s.Nil(result)
    s.mockRepo.AssertExpectations(s.T())
}

func (s *UserServiceTestSuite) TestCreateUser_Success() {
    s.mockRepo.On("FindByEmail", mock.Anything, "john@example.com").Return(nil, nil)
    s.mockRepo.On("Save", mock.Anything, mock.AnythingOfType("*entity.User")).Return(nil)

    result, err := s.svc.CreateUser(context.Background(), &CreateUserRequest{
        Name:     "John Doe",
        Email:    "john@example.com",
        Password: "Password123",
    })

    s.NoError(err)
    s.NotNil(result)
    s.Equal("John Doe", result.Name)
    s.mockRepo.AssertExpectations(s.T())
}

func (s *UserServiceTestSuite) TestCreateUser_EmailExists() {
    existingUser := fixtures.NewMockUser(func(u *entity.User) {
        u.Email = "john@example.com"
    })
    s.mockRepo.On("FindByEmail", mock.Anything, "john@example.com").Return(existingUser, nil)

    result, err := s.svc.CreateUser(context.Background(), &CreateUserRequest{
        Name:     "John Doe",
        Email:    "john@example.com",
        Password: "Password123",
    })

    s.Error(err)
    s.Nil(result)
    s.mockRepo.AssertExpectations(s.T())
}

func TestUserServiceSuite(t *testing.T) {
    suite.Run(t, new(UserServiceTestSuite))
}
```

### Integration Tests

```go
// tests/integration/user_controller_test.go
package integration

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/suite"
)

type UserControllerTestSuite struct {
    suite.Suite
    router *gin.Engine
    token  string
}

func (s *UserControllerTestSuite) SetupSuite() {
    gin.SetMode(gin.TestMode)
    s.router = setupTestRouter()
    s.token = getTestAuthToken()
}

func (s *UserControllerTestSuite) TestGetUsers_Success() {
    req, _ := http.NewRequest("GET", "/api/v1/users?page=0&size=10", nil)
    req.Header.Set("Authorization", "Bearer "+s.token)

    w := httptest.NewRecorder()
    s.router.ServeHTTP(w, req)

    assert.Equal(s.T(), http.StatusOK, w.Code)

    var response map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &response)
    assert.Contains(s.T(), response, "data")
    assert.Contains(s.T(), response, "total")
}

func (s *UserControllerTestSuite) TestGetUsers_Unauthorized() {
    req, _ := http.NewRequest("GET", "/api/v1/users", nil)

    w := httptest.NewRecorder()
    s.router.ServeHTTP(w, req)

    assert.Equal(s.T(), http.StatusUnauthorized, w.Code)
}

func (s *UserControllerTestSuite) TestCreateUser_Success() {
    body, _ := json.Marshal(map[string]string{
        "name":     "New User",
        "email":    "new@test.com",
        "password": "Password123",
    })

    req, _ := http.NewRequest("POST", "/api/v1/users", bytes.NewBuffer(body))
    req.Header.Set("Authorization", "Bearer "+s.token)
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()
    s.router.ServeHTTP(w, req)

    assert.Equal(s.T(), http.StatusCreated, w.Code)

    var response map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &response)
    assert.Equal(s.T(), "New User", response["name"])
}

func (s *UserControllerTestSuite) TestCreateUser_InvalidData() {
    body, _ := json.Marshal(map[string]string{
        "name":     "",
        "email":    "invalid",
        "password": "short",
    })

    req, _ := http.NewRequest("POST", "/api/v1/users", bytes.NewBuffer(body))
    req.Header.Set("Authorization", "Bearer "+s.token)
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()
    s.router.ServeHTTP(w, req)

    assert.Equal(s.T(), http.StatusBadRequest, w.Code)
}

func TestUserControllerSuite(t *testing.T) {
    suite.Run(t, new(UserControllerTestSuite))
}
```

### Table-Driven Tests (Go Idiomatic)

```go
func TestValidatePassword(t *testing.T) {
    tests := []struct {
        name     string
        password string
        wantErr  bool
    }{
        {"valid password", "Password123", false},
        {"too short", "Pass1", true},
        {"no uppercase", "password123", true},
        {"no lowercase", "PASSWORD123", true},
        {"no digit", "PasswordABC", true},
        {"minimum valid", "Abcdefg1", false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validatePassword(tt.password)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

---

## Event-Driven Patterns

### Domain Events with Redis Pub/Sub

```go
// pkg/events/publisher.go
package events

import (
    "context"
    "encoding/json"
    "time"

    "github.com/go-redis/redis/v8"
    "github.com/google/uuid"
    "go.uber.org/zap"
)

type DomainEvent struct {
    ID        string                 `json:"id"`
    Type      string                 `json:"type"`
    Data      map[string]interface{} `json:"data"`
    Timestamp string                 `json:"timestamp"`
    Source    string                 `json:"source"`
}

type EventPublisher interface {
    Publish(ctx context.Context, eventType string, data map[string]interface{}) (string, error)
}

type redisEventPublisher struct {
    redis  *redis.Client
    prefix string
    logger *zap.Logger
}

func NewRedisEventPublisher(redis *redis.Client, logger *zap.Logger) EventPublisher {
    return &redisEventPublisher{
        redis:  redis,
        prefix: "events:",
        logger: logger,
    }
}

func (p *redisEventPublisher) Publish(
    ctx context.Context, eventType string, data map[string]interface{},
) (string, error) {
    event := DomainEvent{
        ID:        uuid.New().String(),
        Type:      eventType,
        Data:      data,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
        Source:    "arcana-cloud-go",
    }

    payload, err := json.Marshal(event)
    if err != nil {
        return "", err
    }

    channel := p.prefix + eventType
    if err := p.redis.Publish(ctx, channel, payload).Err(); err != nil {
        return "", err
    }

    p.logger.Info("event published",
        zap.String("type", eventType),
        zap.String("id", event.ID),
    )

    return event.ID, nil
}

// pkg/events/consumer.go
package events

import (
    "context"
    "encoding/json"

    "github.com/go-redis/redis/v8"
    "go.uber.org/zap"
)

type EventHandler func(ctx context.Context, event DomainEvent) error

type EventConsumer struct {
    redis    *redis.Client
    handlers map[string]EventHandler
    logger   *zap.Logger
    done     chan struct{}
}

func NewEventConsumer(redis *redis.Client, logger *zap.Logger) *EventConsumer {
    return &EventConsumer{
        redis:    redis,
        handlers: make(map[string]EventHandler),
        logger:   logger,
        done:     make(chan struct{}),
    }
}

func (c *EventConsumer) Register(eventType string, handler EventHandler) {
    c.handlers[eventType] = handler
}

func (c *EventConsumer) Start(ctx context.Context) error {
    channels := make([]string, 0, len(c.handlers))
    for eventType := range c.handlers {
        channels = append(channels, "events:"+eventType)
    }

    pubsub := c.redis.Subscribe(ctx, channels...)
    c.logger.Info("event consumer started", zap.Strings("channels", channels))

    go func() {
        ch := pubsub.Channel()
        for {
            select {
            case <-c.done:
                pubsub.Close()
                return
            case msg := <-ch:
                var event DomainEvent
                if err := json.Unmarshal([]byte(msg.Payload), &event); err != nil {
                    c.logger.Error("failed to unmarshal event", zap.Error(err))
                    continue
                }

                handler, ok := c.handlers[event.Type]
                if !ok {
                    continue
                }

                c.logger.Info("processing event",
                    zap.String("type", event.Type),
                    zap.String("id", event.ID),
                )

                if err := handler(ctx, event); err != nil {
                    c.logger.Error("event handler failed",
                        zap.String("type", event.Type),
                        zap.Error(err),
                    )
                }
            }
        }
    }()

    return nil
}

func (c *EventConsumer) Stop() {
    close(c.done)
}

// Register handlers
func RegisterEventHandlers(consumer *EventConsumer) {
    consumer.Register("auth.user_registered", func(ctx context.Context, event DomainEvent) error {
        // Queue welcome email
        return nil
    })

    consumer.Register("auth.password_changed", func(ctx context.Context, event DomainEvent) error {
        // Send security alert
        return nil
    })

    consumer.Register("product.out_of_stock", func(ctx context.Context, event DomainEvent) error {
        // Notify admin
        return nil
    })
}
```
