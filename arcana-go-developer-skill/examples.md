# Go Developer Skill - Code Examples

## Table of Contents
1. [User Authentication Feature](#user-authentication-feature)
2. [CRUD with REST and gRPC](#crud-with-rest-and-grpc)
3. [Background Task Processing](#background-task-processing)
4. [Plugin Development](#plugin-development)
5. [Multi-Database DAO Pattern](#multi-database-dao-pattern)

---

## User Authentication Feature

### Domain Layer

```go
// internal/domain/entity/auth.go
package entity

import (
    "time"
)

type TokenType string

const (
    TokenTypeAccess  TokenType = "access"
    TokenTypeRefresh TokenType = "refresh"
)

type TokenPair struct {
    AccessToken  string `json:"accessToken"`
    RefreshToken string `json:"refreshToken"`
    TokenType    string `json:"tokenType"`
    ExpiresIn    int64  `json:"expiresIn"`
}

type RefreshToken struct {
    ID        string    `gorm:"type:char(36);primaryKey" json:"id"`
    Token     string    `gorm:"type:varchar(512);uniqueIndex;not null" json:"-"`
    UserID    string    `gorm:"type:char(36);index;not null" json:"userId"`
    ExpiresAt time.Time `gorm:"not null" json:"expiresAt"`
    Revoked   bool      `gorm:"default:false" json:"revoked"`
    RevokedAt *time.Time `json:"revokedAt,omitempty"`
    CreatedAt time.Time `gorm:"autoCreateTime" json:"createdAt"`
}

func (RefreshToken) TableName() string {
    return "refresh_tokens"
}

// internal/domain/entity/auth_dto.go
package entity

type LoginRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=1"`
}

type RegisterRequest struct {
    Name     string `json:"name" binding:"required,max=255"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}

type ChangePasswordRequest struct {
    CurrentPassword string `json:"currentPassword" binding:"required,min=1"`
    NewPassword     string `json:"newPassword" binding:"required,min=8"`
}

type RefreshTokenRequest struct {
    RefreshToken string `json:"refreshToken" binding:"required,min=1"`
}
```

### Repository Layer

```go
// internal/domain/repository/refresh_token_repository.go
package repository

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

type RefreshTokenRepository interface {
    FindByToken(ctx context.Context, token string) (*entity.RefreshToken, error)
    Save(ctx context.Context, rt *entity.RefreshToken) error
    Revoke(ctx context.Context, id string) error
    RevokeAllByUser(ctx context.Context, userID string) error
    DeleteExpired(ctx context.Context) (int64, error)
}

// internal/domain/repository/refresh_token_repository_impl.go
package repository

import (
    "context"
    "time"

    "gorm.io/gorm"

    "arcana-cloud-go/internal/domain/entity"
)

type refreshTokenRepoImpl struct {
    db *gorm.DB
}

func NewRefreshTokenRepository(db *gorm.DB) RefreshTokenRepository {
    return &refreshTokenRepoImpl{db: db}
}

func (r *refreshTokenRepoImpl) FindByToken(ctx context.Context, token string) (*entity.RefreshToken, error) {
    var rt entity.RefreshToken
    if err := r.db.WithContext(ctx).Where("token = ?", token).First(&rt).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &rt, nil
}

func (r *refreshTokenRepoImpl) Save(ctx context.Context, rt *entity.RefreshToken) error {
    return r.db.WithContext(ctx).Create(rt).Error
}

func (r *refreshTokenRepoImpl) Revoke(ctx context.Context, id string) error {
    now := time.Now()
    return r.db.WithContext(ctx).Model(&entity.RefreshToken{}).
        Where("id = ?", id).
        Updates(map[string]interface{}{
            "revoked":    true,
            "revoked_at": &now,
        }).Error
}

func (r *refreshTokenRepoImpl) RevokeAllByUser(ctx context.Context, userID string) error {
    now := time.Now()
    return r.db.WithContext(ctx).Model(&entity.RefreshToken{}).
        Where("user_id = ? AND revoked = ?", userID, false).
        Updates(map[string]interface{}{
            "revoked":    true,
            "revoked_at": &now,
        }).Error
}

func (r *refreshTokenRepoImpl) DeleteExpired(ctx context.Context) (int64, error) {
    result := r.db.WithContext(ctx).
        Where("expires_at < ?", time.Now()).
        Delete(&entity.RefreshToken{})
    return result.RowsAffected, result.Error
}
```

### Service Layer

```go
// internal/domain/service/auth_service.go
package service

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

type AuthService interface {
    Login(ctx context.Context, req *entity.LoginRequest) (*entity.TokenPair, error)
    Register(ctx context.Context, req *entity.RegisterRequest) (*entity.UserDTO, error)
    RefreshToken(ctx context.Context, req *entity.RefreshTokenRequest) (*entity.TokenPair, error)
    Logout(ctx context.Context, refreshToken string) error
    LogoutAll(ctx context.Context, userID string) error
    ChangePassword(ctx context.Context, userID string, req *entity.ChangePasswordRequest) error
}

// internal/domain/service/auth_service_impl.go
package service

import (
    "context"
    "fmt"
    "time"
    "unicode"

    "github.com/google/uuid"
    "go.uber.org/zap"
    "golang.org/x/crypto/bcrypt"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/repository"
    "arcana-cloud-go/internal/security"
)

type authServiceImpl struct {
    userRepo  repository.UserRepository
    tokenRepo repository.RefreshTokenRepository
    jwt       *security.JWTService
    logger    *zap.Logger
}

func NewAuthService(
    userRepo repository.UserRepository,
    tokenRepo repository.RefreshTokenRepository,
    jwt *security.JWTService,
    logger *zap.Logger,
) AuthService {
    return &authServiceImpl{
        userRepo:  userRepo,
        tokenRepo: tokenRepo,
        jwt:       jwt,
        logger:    logger,
    }
}

func (s *authServiceImpl) Login(ctx context.Context, req *entity.LoginRequest) (*entity.TokenPair, error) {
    user, err := s.userRepo.FindByEmail(ctx, req.Email)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrUnauthorizedError("Invalid email or password")
    }

    if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
        s.logger.Warn("login failed", zap.String("email", req.Email))
        return nil, entity.ErrUnauthorizedError("Invalid email or password")
    }

    roles := []string{"user"}
    accessToken, err := s.jwt.GenerateToken(user.ID, roles)
    if err != nil {
        return nil, fmt.Errorf("failed to generate access token: %w", err)
    }

    refreshToken, err := s.createRefreshToken(ctx, user.ID)
    if err != nil {
        return nil, fmt.Errorf("failed to create refresh token: %w", err)
    }

    s.logger.Info("login success", zap.String("userID", user.ID))

    return &entity.TokenPair{
        AccessToken:  accessToken,
        RefreshToken: refreshToken.Token,
        TokenType:    "Bearer",
        ExpiresIn:    86400,
    }, nil
}

func (s *authServiceImpl) Register(ctx context.Context, req *entity.RegisterRequest) (*entity.UserDTO, error) {
    existing, err := s.userRepo.FindByEmail(ctx, req.Email)
    if err != nil {
        return nil, fmt.Errorf("failed to check email: %w", err)
    }
    if existing != nil {
        return nil, entity.ErrValidationError("Email already registered", map[string]interface{}{
            "email": req.Email,
        })
    }

    if err := validatePassword(req.Password); err != nil {
        return nil, err
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

    if err := s.userRepo.Save(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to save user: %w", err)
    }

    s.logger.Info("user registered",
        zap.String("userID", user.ID),
        zap.String("email", user.Email),
    )

    return entity.ToUserDTO(user), nil
}

func (s *authServiceImpl) RefreshToken(ctx context.Context, req *entity.RefreshTokenRequest) (*entity.TokenPair, error) {
    storedToken, err := s.tokenRepo.FindByToken(ctx, req.RefreshToken)
    if err != nil {
        return nil, fmt.Errorf("failed to find refresh token: %w", err)
    }
    if storedToken == nil || storedToken.Revoked || storedToken.ExpiresAt.Before(time.Now()) {
        return nil, entity.NewAppError(entity.ErrTokenExpired, "Invalid or expired refresh token", 401)
    }

    // Revoke old token
    if err := s.tokenRepo.Revoke(ctx, storedToken.ID); err != nil {
        return nil, fmt.Errorf("failed to revoke old token: %w", err)
    }

    user, err := s.userRepo.FindByID(ctx, storedToken.UserID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrNotFoundError("User not found")
    }

    roles := []string{"user"}
    accessToken, err := s.jwt.GenerateToken(user.ID, roles)
    if err != nil {
        return nil, fmt.Errorf("failed to generate access token: %w", err)
    }

    newRefreshToken, err := s.createRefreshToken(ctx, user.ID)
    if err != nil {
        return nil, fmt.Errorf("failed to create refresh token: %w", err)
    }

    return &entity.TokenPair{
        AccessToken:  accessToken,
        RefreshToken: newRefreshToken.Token,
        TokenType:    "Bearer",
        ExpiresIn:    86400,
    }, nil
}

func (s *authServiceImpl) Logout(ctx context.Context, refreshToken string) error {
    storedToken, err := s.tokenRepo.FindByToken(ctx, refreshToken)
    if err != nil {
        return fmt.Errorf("failed to find refresh token: %w", err)
    }
    if storedToken != nil {
        return s.tokenRepo.Revoke(ctx, storedToken.ID)
    }
    return nil
}

func (s *authServiceImpl) LogoutAll(ctx context.Context, userID string) error {
    return s.tokenRepo.RevokeAllByUser(ctx, userID)
}

func (s *authServiceImpl) ChangePassword(ctx context.Context, userID string, req *entity.ChangePasswordRequest) error {
    user, err := s.userRepo.FindByID(ctx, userID)
    if err != nil {
        return fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return entity.ErrNotFoundError("User not found")
    }

    if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.CurrentPassword)); err != nil {
        return entity.ErrValidationError("Current password is incorrect", nil)
    }

    if err := validatePassword(req.NewPassword); err != nil {
        return err
    }

    hash, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
    if err != nil {
        return fmt.Errorf("failed to hash password: %w", err)
    }

    user.PasswordHash = string(hash)
    if err := s.userRepo.Update(ctx, user); err != nil {
        return fmt.Errorf("failed to update user: %w", err)
    }

    // Revoke all refresh tokens
    if err := s.tokenRepo.RevokeAllByUser(ctx, userID); err != nil {
        return fmt.Errorf("failed to revoke tokens: %w", err)
    }

    s.logger.Info("password changed", zap.String("userID", userID))
    return nil
}

func (s *authServiceImpl) createRefreshToken(ctx context.Context, userID string) (*entity.RefreshToken, error) {
    tokenStr, err := s.jwt.GenerateToken(userID, nil)
    if err != nil {
        return nil, err
    }

    rt := &entity.RefreshToken{
        ID:        uuid.New().String(),
        Token:     tokenStr,
        UserID:    userID,
        ExpiresAt: time.Now().Add(7 * 24 * time.Hour),
        Revoked:   false,
    }

    if err := s.tokenRepo.Save(ctx, rt); err != nil {
        return nil, err
    }

    return rt, nil
}

func validatePassword(password string) error {
    if len(password) < 8 {
        return entity.ErrValidationError("Password must be at least 8 characters", nil)
    }

    var hasUpper, hasLower, hasDigit bool
    for _, ch := range password {
        switch {
        case unicode.IsUpper(ch):
            hasUpper = true
        case unicode.IsLower(ch):
            hasLower = true
        case unicode.IsDigit(ch):
            hasDigit = true
        }
    }

    if !hasUpper {
        return entity.ErrValidationError("Password must contain uppercase letter", nil)
    }
    if !hasLower {
        return entity.ErrValidationError("Password must contain lowercase letter", nil)
    }
    if !hasDigit {
        return entity.ErrValidationError("Password must contain a number", nil)
    }

    return nil
}
```

### Controller Layer

```go
// internal/controller/http/auth_controller.go
package http

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/service"
)

type AuthController struct {
    authService service.AuthService
}

func NewAuthController(authService service.AuthService) *AuthController {
    return &AuthController{authService: authService}
}

func (ctrl *AuthController) RegisterRoutes(rg *gin.RouterGroup, authMiddleware gin.HandlerFunc) {
    auth := rg.Group("/auth")
    {
        auth.POST("/login", ctrl.Login)
        auth.POST("/register", ctrl.Register)
        auth.POST("/refresh", ctrl.RefreshToken)
        auth.POST("/logout", ctrl.Logout)
    }

    authed := rg.Group("/auth")
    authed.Use(authMiddleware)
    {
        authed.POST("/logout-all", ctrl.LogoutAll)
        authed.POST("/change-password", ctrl.ChangePassword)
        authed.GET("/me", ctrl.GetCurrentUser)
    }
}

func (ctrl *AuthController) Login(c *gin.Context) {
    var req entity.LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    tokenPair, err := ctrl.authService.Login(c.Request.Context(), &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, tokenPair)
}

func (ctrl *AuthController) Register(c *gin.Context) {
    var req entity.RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := ctrl.authService.Register(c.Request.Context(), &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusCreated, user)
}

func (ctrl *AuthController) RefreshToken(c *gin.Context) {
    var req entity.RefreshTokenRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    tokenPair, err := ctrl.authService.RefreshToken(c.Request.Context(), &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, tokenPair)
}

func (ctrl *AuthController) Logout(c *gin.Context) {
    var req entity.RefreshTokenRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    if err := ctrl.authService.Logout(c.Request.Context(), req.RefreshToken); err != nil {
        c.Error(err)
        return
    }

    c.Status(http.StatusNoContent)
}

func (ctrl *AuthController) LogoutAll(c *gin.Context) {
    userID := c.GetString("userID")

    if err := ctrl.authService.LogoutAll(c.Request.Context(), userID); err != nil {
        c.Error(err)
        return
    }

    c.Status(http.StatusNoContent)
}

func (ctrl *AuthController) ChangePassword(c *gin.Context) {
    userID := c.GetString("userID")

    var req entity.ChangePasswordRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    if err := ctrl.authService.ChangePassword(c.Request.Context(), userID, &req); err != nil {
        c.Error(err)
        return
    }

    c.Status(http.StatusNoContent)
}

func (ctrl *AuthController) GetCurrentUser(c *gin.Context) {
    userID := c.GetString("userID")
    // Delegate to user service if needed
    c.JSON(http.StatusOK, gin.H{"userId": userID})
}
```

---

## CRUD with REST and gRPC

### Product Entity and Service

```go
// internal/domain/entity/product.go
package entity

import (
    "time"
)

type ProductStatus string

const (
    ProductStatusDraft    ProductStatus = "DRAFT"
    ProductStatusActive   ProductStatus = "ACTIVE"
    ProductStatusInactive ProductStatus = "INACTIVE"
    ProductStatusArchived ProductStatus = "ARCHIVED"
)

type Product struct {
    ID          string        `gorm:"type:char(36);primaryKey" json:"id"`
    Name        string        `gorm:"type:varchar(255);not null" json:"name"`
    Description *string       `gorm:"type:text" json:"description,omitempty"`
    Price       float64       `gorm:"type:decimal(10,2);not null" json:"price"`
    Stock       int           `gorm:"default:0" json:"stock"`
    Category    *string       `gorm:"type:varchar(100)" json:"category,omitempty"`
    Status      ProductStatus `gorm:"type:varchar(20);default:DRAFT" json:"status"`
    CreatedAt   time.Time     `gorm:"autoCreateTime" json:"createdAt"`
    UpdatedAt   time.Time     `gorm:"autoUpdateTime" json:"updatedAt"`
}

func (Product) TableName() string {
    return "products"
}

type ProductDTO struct {
    ID          string  `json:"id"`
    Name        string  `json:"name"`
    Description *string `json:"description,omitempty"`
    Price       float64 `json:"price"`
    Stock       int     `json:"stock"`
    Category    *string `json:"category,omitempty"`
    Status      string  `json:"status"`
    CreatedAt   string  `json:"createdAt"`
    UpdatedAt   string  `json:"updatedAt"`
}

func ToProductDTO(p *Product) *ProductDTO {
    return &ProductDTO{
        ID:          p.ID,
        Name:        p.Name,
        Description: p.Description,
        Price:       p.Price,
        Stock:       p.Stock,
        Category:    p.Category,
        Status:      string(p.Status),
        CreatedAt:   p.CreatedAt.Format(time.RFC3339),
        UpdatedAt:   p.UpdatedAt.Format(time.RFC3339),
    }
}

// Request DTOs
type CreateProductRequest struct {
    Name        string  `json:"name" binding:"required,max=255"`
    Description *string `json:"description"`
    Price       float64 `json:"price" binding:"required,gte=0"`
    Stock       int     `json:"stock" binding:"gte=0"`
    Category    *string `json:"category" binding:"omitempty,max=100"`
}

type UpdateProductRequest struct {
    Name        *string `json:"name" binding:"omitempty,max=255"`
    Description *string `json:"description"`
    Price       *float64 `json:"price" binding:"omitempty,gte=0"`
    Stock       *int    `json:"stock" binding:"omitempty,gte=0"`
    Category    *string `json:"category" binding:"omitempty,max=100"`
    Status      *string `json:"status" binding:"omitempty,oneof=DRAFT ACTIVE INACTIVE ARCHIVED"`
}

type StockUpdateRequest struct {
    QuantityChange int `json:"quantityChange" binding:"required"`
}
```

### Service Implementation

```go
// internal/domain/service/product_service.go
package service

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

type ProductService interface {
    GetProduct(ctx context.Context, productID string) (*entity.ProductDTO, error)
    GetProducts(ctx context.Context, page, size int, category, status string) ([]*entity.ProductDTO, int64, error)
    SearchProducts(ctx context.Context, query string, opts *SearchOptions) ([]*entity.ProductDTO, error)
    CreateProduct(ctx context.Context, req *entity.CreateProductRequest) (*entity.ProductDTO, error)
    UpdateProduct(ctx context.Context, productID string, req *entity.UpdateProductRequest) (*entity.ProductDTO, error)
    UpdateStock(ctx context.Context, productID string, quantityChange int) (*entity.ProductDTO, error)
    DeleteProduct(ctx context.Context, productID string) error
}

type SearchOptions struct {
    Category string
    MinPrice float64
    MaxPrice float64
    Limit    int
}

// internal/domain/service/product_service_impl.go
package service

import (
    "context"
    "fmt"
    "time"

    "github.com/go-redis/redis/v8"
    "go.uber.org/zap"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/repository"
)

type productServiceImpl struct {
    repo   repository.ProductRepository
    cache  *redis.Client
    logger *zap.Logger
}

func NewProductService(
    repo repository.ProductRepository,
    cache *redis.Client,
    logger *zap.Logger,
) ProductService {
    return &productServiceImpl{
        repo:   repo,
        cache:  cache,
        logger: logger,
    }
}

func (s *productServiceImpl) GetProduct(ctx context.Context, productID string) (*entity.ProductDTO, error) {
    cacheKey := fmt.Sprintf("product:%s", productID)

    // Try cache first
    cached, err := s.cache.Get(ctx, cacheKey).Result()
    if err == nil && cached != "" {
        s.logger.Debug("cache hit", zap.String("key", cacheKey))
        // Deserialize from JSON (omitted for brevity)
    }

    product, err := s.repo.FindByID(ctx, productID)
    if err != nil {
        return nil, fmt.Errorf("failed to find product: %w", err)
    }
    if product == nil {
        return nil, nil
    }

    dto := entity.ToProductDTO(product)

    // Cache for 1 hour
    s.cache.Set(ctx, cacheKey, dto, 1*time.Hour)

    return dto, nil
}

func (s *productServiceImpl) GetProducts(
    ctx context.Context, page, size int, category, status string,
) ([]*entity.ProductDTO, int64, error) {
    products, total, err := s.repo.FindAll(ctx, page, size, category, status)
    if err != nil {
        return nil, 0, fmt.Errorf("failed to list products: %w", err)
    }

    dtos := make([]*entity.ProductDTO, len(products))
    for i, p := range products {
        dtos[i] = entity.ToProductDTO(p)
    }

    return dtos, total, nil
}

func (s *productServiceImpl) SearchProducts(
    ctx context.Context, query string, opts *SearchOptions,
) ([]*entity.ProductDTO, error) {
    products, err := s.repo.Search(ctx, query, opts.Category, opts.MinPrice, opts.MaxPrice, opts.Limit)
    if err != nil {
        return nil, fmt.Errorf("failed to search products: %w", err)
    }

    dtos := make([]*entity.ProductDTO, len(products))
    for i, p := range products {
        dtos[i] = entity.ToProductDTO(p)
    }

    return dtos, nil
}

func (s *productServiceImpl) CreateProduct(
    ctx context.Context, req *entity.CreateProductRequest,
) (*entity.ProductDTO, error) {
    product := &entity.Product{
        Name:        req.Name,
        Description: req.Description,
        Price:       req.Price,
        Stock:       req.Stock,
        Category:    req.Category,
        Status:      entity.ProductStatusDraft,
    }

    if err := s.repo.Save(ctx, product); err != nil {
        return nil, fmt.Errorf("failed to save product: %w", err)
    }

    s.logger.Info("product created", zap.String("productID", product.ID))

    return entity.ToProductDTO(product), nil
}

func (s *productServiceImpl) UpdateProduct(
    ctx context.Context, productID string, req *entity.UpdateProductRequest,
) (*entity.ProductDTO, error) {
    product, err := s.repo.FindByID(ctx, productID)
    if err != nil {
        return nil, fmt.Errorf("failed to find product: %w", err)
    }
    if product == nil {
        return nil, entity.ErrNotFoundError("Product not found")
    }

    if req.Name != nil {
        product.Name = *req.Name
    }
    if req.Description != nil {
        product.Description = req.Description
    }
    if req.Price != nil {
        product.Price = *req.Price
    }
    if req.Stock != nil {
        product.Stock = *req.Stock
    }
    if req.Category != nil {
        product.Category = req.Category
    }
    if req.Status != nil {
        product.Status = entity.ProductStatus(*req.Status)
    }

    if err := s.repo.Update(ctx, product); err != nil {
        return nil, fmt.Errorf("failed to update product: %w", err)
    }

    // Invalidate cache
    s.cache.Del(ctx, fmt.Sprintf("product:%s", productID))

    return entity.ToProductDTO(product), nil
}

func (s *productServiceImpl) UpdateStock(
    ctx context.Context, productID string, quantityChange int,
) (*entity.ProductDTO, error) {
    product, err := s.repo.FindByID(ctx, productID)
    if err != nil {
        return nil, fmt.Errorf("failed to find product: %w", err)
    }
    if product == nil {
        return nil, entity.ErrNotFoundError("Product not found")
    }

    newStock := product.Stock + quantityChange
    if newStock < 0 {
        return nil, entity.ErrValidationError(
            fmt.Sprintf("Insufficient stock. Available: %d", product.Stock),
            map[string]interface{}{
                "available": product.Stock,
                "requested": -quantityChange,
            },
        )
    }

    product.Stock = newStock
    if err := s.repo.Update(ctx, product); err != nil {
        return nil, fmt.Errorf("failed to update stock: %w", err)
    }

    // Invalidate cache
    s.cache.Del(ctx, fmt.Sprintf("product:%s", productID))

    if newStock == 0 {
        s.logger.Warn("product out of stock", zap.String("productID", productID))
    } else if newStock <= 10 {
        s.logger.Warn("product low stock",
            zap.String("productID", productID),
            zap.Int("stock", newStock),
        )
    }

    return entity.ToProductDTO(product), nil
}

func (s *productServiceImpl) DeleteProduct(ctx context.Context, productID string) error {
    product, err := s.repo.FindByID(ctx, productID)
    if err != nil {
        return fmt.Errorf("failed to find product: %w", err)
    }
    if product == nil {
        return entity.ErrNotFoundError("Product not found")
    }

    if err := s.repo.Delete(ctx, product); err != nil {
        return fmt.Errorf("failed to delete product: %w", err)
    }

    s.cache.Del(ctx, fmt.Sprintf("product:%s", productID))

    s.logger.Info("product deleted", zap.String("productID", productID))

    return nil
}
```

### REST Controller

```go
// internal/controller/http/product_controller.go
package http

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/service"
)

type ProductController struct {
    productService service.ProductService
}

func NewProductController(productService service.ProductService) *ProductController {
    return &ProductController{productService: productService}
}

func (ctrl *ProductController) RegisterRoutes(rg *gin.RouterGroup, authMW, adminMW gin.HandlerFunc) {
    products := rg.Group("/products")
    {
        products.GET("", ctrl.GetProducts)
        products.GET("/search", ctrl.SearchProducts)
        products.GET("/:id", ctrl.GetProduct)
    }

    admin := rg.Group("/products")
    admin.Use(authMW, adminMW)
    {
        admin.POST("", ctrl.CreateProduct)
        admin.PUT("/:id", ctrl.UpdateProduct)
        admin.PATCH("/:id/stock", ctrl.UpdateStock)
        admin.DELETE("/:id", ctrl.DeleteProduct)
    }
}

func (ctrl *ProductController) GetProducts(c *gin.Context) {
    page, _ := strconv.Atoi(c.DefaultQuery("page", "0"))
    size, _ := strconv.Atoi(c.DefaultQuery("size", "10"))
    category := c.Query("category")
    status := c.Query("status")

    products, total, err := ctrl.productService.GetProducts(
        c.Request.Context(), page, size, category, status,
    )
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "data":  products,
        "page":  page,
        "size":  size,
        "total": total,
    })
}

func (ctrl *ProductController) SearchProducts(c *gin.Context) {
    query := c.DefaultQuery("q", "")
    category := c.Query("category")
    minPrice, _ := strconv.ParseFloat(c.DefaultQuery("min_price", "0"), 64)
    maxPrice, _ := strconv.ParseFloat(c.DefaultQuery("max_price", "0"), 64)
    limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))

    products, err := ctrl.productService.SearchProducts(
        c.Request.Context(), query,
        &service.SearchOptions{
            Category: category,
            MinPrice: minPrice,
            MaxPrice: maxPrice,
            Limit:    limit,
        },
    )
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, products)
}

func (ctrl *ProductController) GetProduct(c *gin.Context) {
    productID := c.Param("id")

    product, err := ctrl.productService.GetProduct(c.Request.Context(), productID)
    if err != nil {
        c.Error(err)
        return
    }
    if product == nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
        return
    }

    c.JSON(http.StatusOK, product)
}

func (ctrl *ProductController) CreateProduct(c *gin.Context) {
    var req entity.CreateProductRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    product, err := ctrl.productService.CreateProduct(c.Request.Context(), &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusCreated, product)
}

func (ctrl *ProductController) UpdateProduct(c *gin.Context) {
    productID := c.Param("id")
    var req entity.UpdateProductRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    product, err := ctrl.productService.UpdateProduct(c.Request.Context(), productID, &req)
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, product)
}

func (ctrl *ProductController) UpdateStock(c *gin.Context) {
    productID := c.Param("id")
    var req entity.StockUpdateRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    product, err := ctrl.productService.UpdateStock(
        c.Request.Context(), productID, req.QuantityChange,
    )
    if err != nil {
        c.Error(err)
        return
    }

    c.JSON(http.StatusOK, product)
}

func (ctrl *ProductController) DeleteProduct(c *gin.Context) {
    productID := c.Param("id")

    if err := ctrl.productService.DeleteProduct(c.Request.Context(), productID); err != nil {
        c.Error(err)
        return
    }

    c.Status(http.StatusNoContent)
}
```

### gRPC Server Implementation

```go
// api/proto/product.proto
// syntax = "proto3";
// package arcana.product.v1;
// option go_package = "arcana-cloud-go/api/proto/product/v1";
//
// service ProductService {
//   rpc GetProduct(GetProductRequest) returns (ProductResponse);
//   rpc ListProducts(ListProductsRequest) returns (ListProductsResponse);
//   rpc CreateProduct(CreateProductRequest) returns (ProductResponse);
//   rpc UpdateProduct(UpdateProductRequest) returns (ProductResponse);
//   rpc UpdateStock(UpdateStockRequest) returns (ProductResponse);
//   rpc DeleteProduct(DeleteProductRequest) returns (DeleteProductResponse);
// }

// internal/controller/grpc/product_server.go
package grpc

import (
    "context"

    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"

    pb "arcana-cloud-go/api/proto/product/v1"
    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/service"
)

type ProductServer struct {
    pb.UnimplementedProductServiceServer
    productService service.ProductService
}

func NewProductServer(productService service.ProductService) *ProductServer {
    return &ProductServer{productService: productService}
}

func (s *ProductServer) GetProduct(
    ctx context.Context, req *pb.GetProductRequest,
) (*pb.ProductResponse, error) {
    product, err := s.productService.GetProduct(ctx, req.GetId())
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to get product: %v", err)
    }
    if product == nil {
        return nil, status.Errorf(codes.NotFound, "product not found")
    }

    return toProductProto(product), nil
}

func (s *ProductServer) ListProducts(
    ctx context.Context, req *pb.ListProductsRequest,
) (*pb.ListProductsResponse, error) {
    products, total, err := s.productService.GetProducts(
        ctx,
        int(req.GetPage()),
        int(req.GetSize()),
        req.GetCategory(),
        req.GetStatus(),
    )
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to list products: %v", err)
    }

    items := make([]*pb.ProductResponse, len(products))
    for i, p := range products {
        items[i] = toProductProto(p)
    }

    return &pb.ListProductsResponse{
        Products: items,
        Total:    int32(total),
        Page:     req.GetPage(),
        Size:     req.GetSize(),
        HasNext:  int64(len(products)) == int64(req.GetSize()),
    }, nil
}

func (s *ProductServer) CreateProduct(
    ctx context.Context, req *pb.CreateProductRequest,
) (*pb.ProductResponse, error) {
    desc := req.GetDescription()
    cat := req.GetCategory()

    product, err := s.productService.CreateProduct(ctx, &entity.CreateProductRequest{
        Name:        req.GetName(),
        Description: &desc,
        Price:       req.GetPrice(),
        Stock:       int(req.GetStock()),
        Category:    &cat,
    })
    if err != nil {
        return nil, status.Errorf(codes.InvalidArgument, "failed to create product: %v", err)
    }

    return toProductProto(product), nil
}

func (s *ProductServer) UpdateStock(
    ctx context.Context, req *pb.UpdateStockRequest,
) (*pb.ProductResponse, error) {
    product, err := s.productService.UpdateStock(
        ctx, req.GetProductId(), int(req.GetQuantityChange()),
    )
    if err != nil {
        return nil, status.Errorf(codes.InvalidArgument, "failed to update stock: %v", err)
    }

    return toProductProto(product), nil
}

func (s *ProductServer) DeleteProduct(
    ctx context.Context, req *pb.DeleteProductRequest,
) (*pb.DeleteProductResponse, error) {
    if err := s.productService.DeleteProduct(ctx, req.GetId()); err != nil {
        return nil, status.Errorf(codes.Internal, "failed to delete product: %v", err)
    }

    return &pb.DeleteProductResponse{Success: true}, nil
}

func toProductProto(dto *entity.ProductDTO) *pb.ProductResponse {
    resp := &pb.ProductResponse{
        Id:        dto.ID,
        Name:      dto.Name,
        Price:     dto.Price,
        Stock:     int32(dto.Stock),
        Status:    dto.Status,
        CreatedAt: dto.CreatedAt,
        UpdatedAt: dto.UpdatedAt,
    }
    if dto.Description != nil {
        resp.Description = *dto.Description
    }
    if dto.Category != nil {
        resp.Category = *dto.Category
    }
    return resp
}
```

---

## Background Task Processing

### Job System

```go
// internal/jobs/scheduler.go
package jobs

import (
    "context"
    "time"

    "go.uber.org/zap"
)

type JobScheduler struct {
    jobs   []ScheduledJob
    logger *zap.Logger
    done   chan struct{}
}

type ScheduledJob struct {
    Name     string
    Interval time.Duration
    Handler  func(ctx context.Context) error
}

func NewJobScheduler(logger *zap.Logger) *JobScheduler {
    return &JobScheduler{
        logger: logger,
        done:   make(chan struct{}),
    }
}

func (s *JobScheduler) Register(name string, interval time.Duration, handler func(ctx context.Context) error) {
    s.jobs = append(s.jobs, ScheduledJob{
        Name:     name,
        Interval: interval,
        Handler:  handler,
    })
}

func (s *JobScheduler) Start(ctx context.Context) {
    for _, job := range s.jobs {
        go s.runJob(ctx, job)
    }
    s.logger.Info("job scheduler started", zap.Int("jobs", len(s.jobs)))
}

func (s *JobScheduler) Stop() {
    close(s.done)
}

func (s *JobScheduler) runJob(ctx context.Context, job ScheduledJob) {
    ticker := time.NewTicker(job.Interval)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-s.done:
            return
        case <-ticker.C:
            s.logger.Info("running job", zap.String("name", job.Name))
            if err := job.Handler(ctx); err != nil {
                s.logger.Error("job failed",
                    zap.String("name", job.Name),
                    zap.Error(err),
                )
            } else {
                s.logger.Info("job completed", zap.String("name", job.Name))
            }
        }
    }
}

// internal/jobs/workers.go
package jobs

import (
    "context"
    "fmt"

    "go.uber.org/zap"

    "arcana-cloud-go/internal/domain/entity"
    "arcana-cloud-go/internal/domain/repository"
)

type SyncWorker struct {
    userRepo  repository.UserRepository
    tokenRepo repository.RefreshTokenRepository
    logger    *zap.Logger
}

func NewSyncWorker(
    userRepo repository.UserRepository,
    tokenRepo repository.RefreshTokenRepository,
    logger *zap.Logger,
) *SyncWorker {
    return &SyncWorker{
        userRepo:  userRepo,
        tokenRepo: tokenRepo,
        logger:    logger,
    }
}

func (w *SyncWorker) SyncPendingUsers(ctx context.Context) error {
    users, err := w.userRepo.FindPendingSync(ctx)
    if err != nil {
        return fmt.Errorf("failed to find pending users: %w", err)
    }

    w.logger.Info("syncing pending users", zap.Int("count", len(users)))

    for _, user := range users {
        if err := w.syncUser(ctx, user); err != nil {
            w.logger.Error("failed to sync user",
                zap.String("userID", user.ID),
                zap.Error(err),
            )
            user.SyncStatus = entity.SyncStatusFailed
        } else {
            user.SyncStatus = entity.SyncStatusSynced
            w.logger.Info("user synced", zap.String("userID", user.ID))
        }

        if err := w.userRepo.Update(ctx, user); err != nil {
            w.logger.Error("failed to update sync status",
                zap.String("userID", user.ID),
                zap.Error(err),
            )
        }
    }

    return nil
}

func (w *SyncWorker) CleanupExpiredTokens(ctx context.Context) error {
    count, err := w.tokenRepo.DeleteExpired(ctx)
    if err != nil {
        return fmt.Errorf("failed to cleanup tokens: %w", err)
    }

    w.logger.Info("cleaned up expired tokens", zap.Int64("count", count))
    return nil
}

func (w *SyncWorker) syncUser(ctx context.Context, user *entity.User) error {
    // Call external API to sync user data
    // This is a placeholder for actual sync logic
    return nil
}

// internal/jobs/setup.go
package jobs

import (
    "context"
    "time"

    "go.uber.org/zap"
)

func SetupScheduledJobs(
    scheduler *JobScheduler,
    syncWorker *SyncWorker,
    logger *zap.Logger,
) {
    // Sync pending users every 5 minutes
    scheduler.Register(
        "sync-pending-users",
        5*time.Minute,
        syncWorker.SyncPendingUsers,
    )

    // Cleanup expired tokens every hour
    scheduler.Register(
        "cleanup-expired-tokens",
        1*time.Hour,
        syncWorker.CleanupExpiredTokens,
    )

    logger.Info("scheduled jobs configured")
}

// Wire in fx DI:
// fx.Provide(jobs.NewJobScheduler)
// fx.Provide(jobs.NewSyncWorker)
// fx.Invoke(jobs.SetupScheduledJobs)
// fx.Invoke(func(lc fx.Lifecycle, scheduler *jobs.JobScheduler) {
//     lc.Append(fx.Hook{
//         OnStart: func(ctx context.Context) error {
//             scheduler.Start(ctx)
//             return nil
//         },
//         OnStop: func(ctx context.Context) error {
//             scheduler.Stop()
//             return nil
//         },
//     })
// })
```

### Redis-Backed Job Queue

```go
// internal/jobs/queue.go
package jobs

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/go-redis/redis/v8"
    "go.uber.org/zap"
)

type JobQueue struct {
    redis  *redis.Client
    logger *zap.Logger
}

type Job struct {
    ID        string                 `json:"id"`
    Type      string                 `json:"type"`
    Payload   map[string]interface{} `json:"payload"`
    Attempts  int                    `json:"attempts"`
    MaxRetry  int                    `json:"maxRetry"`
    CreatedAt time.Time              `json:"createdAt"`
}

func NewJobQueue(redis *redis.Client, logger *zap.Logger) *JobQueue {
    return &JobQueue{redis: redis, logger: logger}
}

func (q *JobQueue) Enqueue(ctx context.Context, jobType string, payload map[string]interface{}) error {
    job := &Job{
        ID:        fmt.Sprintf("%s-%d", jobType, time.Now().UnixNano()),
        Type:      jobType,
        Payload:   payload,
        Attempts:  0,
        MaxRetry:  3,
        CreatedAt: time.Now(),
    }

    data, err := json.Marshal(job)
    if err != nil {
        return fmt.Errorf("failed to marshal job: %w", err)
    }

    return q.redis.LPush(ctx, "job_queue:"+jobType, data).Err()
}

func (q *JobQueue) Dequeue(ctx context.Context, jobType string) (*Job, error) {
    result, err := q.redis.BRPop(ctx, 5*time.Second, "job_queue:"+jobType).Result()
    if err == redis.Nil {
        return nil, nil
    }
    if err != nil {
        return nil, fmt.Errorf("failed to dequeue job: %w", err)
    }

    var job Job
    if err := json.Unmarshal([]byte(result[1]), &job); err != nil {
        return nil, fmt.Errorf("failed to unmarshal job: %w", err)
    }

    return &job, nil
}

// Usage in service
func QueueWelcomeEmail(ctx context.Context, queue *JobQueue, userID, email, name string) error {
    return queue.Enqueue(ctx, "welcome-email", map[string]interface{}{
        "userId": userID,
        "email":  email,
        "name":   name,
    })
}
```

---

## Plugin Development

### Plugin Interface and Manager

```go
// internal/plugin/interface.go
package plugin

import (
    "context"
)

type Plugin interface {
    // Name returns the plugin name
    Name() string

    // Version returns the plugin version
    Version() string

    // Init initializes the plugin with configuration
    Init(ctx context.Context, config map[string]interface{}) error

    // Start starts the plugin
    Start(ctx context.Context) error

    // Stop gracefully stops the plugin
    Stop(ctx context.Context) error

    // Health returns the plugin health status
    Health(ctx context.Context) HealthStatus
}

type HealthStatus struct {
    Healthy bool   `json:"healthy"`
    Message string `json:"message,omitempty"`
}

type PluginMetadata struct {
    Name        string   `json:"name"`
    Version     string   `json:"version"`
    Description string   `json:"description"`
    Author      string   `json:"author"`
    Tags        []string `json:"tags"`
}

// internal/plugin/manager.go
package plugin

import (
    "context"
    "fmt"
    "sync"

    "go.uber.org/zap"
)

type PluginManager struct {
    plugins map[string]Plugin
    mu      sync.RWMutex
    logger  *zap.Logger
}

func NewPluginManager(logger *zap.Logger) *PluginManager {
    return &PluginManager{
        plugins: make(map[string]Plugin),
        logger:  logger,
    }
}

func (m *PluginManager) Register(p Plugin) error {
    m.mu.Lock()
    defer m.mu.Unlock()

    name := p.Name()
    if _, exists := m.plugins[name]; exists {
        return fmt.Errorf("plugin already registered: %s", name)
    }

    m.plugins[name] = p
    m.logger.Info("plugin registered",
        zap.String("name", name),
        zap.String("version", p.Version()),
    )

    return nil
}

func (m *PluginManager) Get(name string) (Plugin, bool) {
    m.mu.RLock()
    defer m.mu.RUnlock()
    p, ok := m.plugins[name]
    return p, ok
}

func (m *PluginManager) StartAll(ctx context.Context) error {
    m.mu.RLock()
    defer m.mu.RUnlock()

    for name, p := range m.plugins {
        if err := p.Start(ctx); err != nil {
            return fmt.Errorf("failed to start plugin %s: %w", name, err)
        }
        m.logger.Info("plugin started", zap.String("name", name))
    }

    return nil
}

func (m *PluginManager) StopAll(ctx context.Context) {
    m.mu.RLock()
    defer m.mu.RUnlock()

    for name, p := range m.plugins {
        if err := p.Stop(ctx); err != nil {
            m.logger.Error("failed to stop plugin",
                zap.String("name", name),
                zap.Error(err),
            )
        } else {
            m.logger.Info("plugin stopped", zap.String("name", name))
        }
    }
}

func (m *PluginManager) HealthCheck(ctx context.Context) map[string]HealthStatus {
    m.mu.RLock()
    defer m.mu.RUnlock()

    statuses := make(map[string]HealthStatus)
    for name, p := range m.plugins {
        statuses[name] = p.Health(ctx)
    }
    return statuses
}

func (m *PluginManager) List() []PluginMetadata {
    m.mu.RLock()
    defer m.mu.RUnlock()

    list := make([]PluginMetadata, 0, len(m.plugins))
    for _, p := range m.plugins {
        list = append(list, PluginMetadata{
            Name:    p.Name(),
            Version: p.Version(),
        })
    }
    return list
}
```

### Example Plugin: Metrics Collector

```go
// internal/plugin/metrics/metrics_plugin.go
package metrics

import (
    "context"
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    "go.uber.org/zap"

    "arcana-cloud-go/internal/plugin"
)

type MetricsPlugin struct {
    server  *http.Server
    logger  *zap.Logger
    port    string

    requestCount   *prometheus.CounterVec
    requestLatency *prometheus.HistogramVec
}

func New(logger *zap.Logger) *MetricsPlugin {
    requestCount := prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )

    requestLatency := prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path"},
    )

    prometheus.MustRegister(requestCount, requestLatency)

    return &MetricsPlugin{
        logger:         logger,
        port:           ":9090",
        requestCount:   requestCount,
        requestLatency: requestLatency,
    }
}

func (p *MetricsPlugin) Name() string    { return "metrics" }
func (p *MetricsPlugin) Version() string { return "1.0.0" }

func (p *MetricsPlugin) Init(ctx context.Context, config map[string]interface{}) error {
    if port, ok := config["port"].(string); ok {
        p.port = port
    }
    return nil
}

func (p *MetricsPlugin) Start(ctx context.Context) error {
    mux := http.NewServeMux()
    mux.Handle("/metrics", promhttp.Handler())

    p.server = &http.Server{
        Addr:    p.port,
        Handler: mux,
    }

    go func() {
        if err := p.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            p.logger.Error("metrics server error", zap.Error(err))
        }
    }()

    p.logger.Info("metrics plugin started", zap.String("port", p.port))
    return nil
}

func (p *MetricsPlugin) Stop(ctx context.Context) error {
    if p.server != nil {
        return p.server.Shutdown(ctx)
    }
    return nil
}

func (p *MetricsPlugin) Health(ctx context.Context) plugin.HealthStatus {
    return plugin.HealthStatus{Healthy: true, Message: "metrics collector running"}
}

func (p *MetricsPlugin) RecordRequest(method, path string, status int, duration time.Duration) {
    p.requestCount.WithLabelValues(method, path, http.StatusText(status)).Inc()
    p.requestLatency.WithLabelValues(method, path).Observe(duration.Seconds())
}
```

---

## Multi-Database DAO Pattern

### DAO Interface and Implementations

```go
// internal/domain/dao/user_dao.go
package dao

import (
    "context"
    "arcana-cloud-go/internal/domain/entity"
)

// UserDAO abstracts data access across different databases
type UserDAO interface {
    FindByID(ctx context.Context, id string) (*entity.User, error)
    FindByEmail(ctx context.Context, email string) (*entity.User, error)
    FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error)
    Save(ctx context.Context, user *entity.User) error
    Update(ctx context.Context, user *entity.User) error
    Delete(ctx context.Context, id string) error
}

// internal/domain/dao/user_dao_mysql.go
package dao

import (
    "context"
    "fmt"

    "gorm.io/gorm"

    "arcana-cloud-go/internal/domain/entity"
)

type mysqlUserDAO struct {
    db *gorm.DB
}

func NewMySQLUserDAO(db *gorm.DB) UserDAO {
    return &mysqlUserDAO{db: db}
}

func (d *mysqlUserDAO) FindByID(ctx context.Context, id string) (*entity.User, error) {
    var user entity.User
    if err := d.db.WithContext(ctx).Where("id = ?", id).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, fmt.Errorf("mysql: failed to find user by ID: %w", err)
    }
    return &user, nil
}

func (d *mysqlUserDAO) FindByEmail(ctx context.Context, email string) (*entity.User, error) {
    var user entity.User
    if err := d.db.WithContext(ctx).Where("email = ?", email).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, fmt.Errorf("mysql: failed to find user by email: %w", err)
    }
    return &user, nil
}

func (d *mysqlUserDAO) FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error) {
    var users []*entity.User
    var total int64

    d.db.WithContext(ctx).Model(&entity.User{}).Count(&total)

    offset := page * size
    if err := d.db.WithContext(ctx).
        Order("created_at DESC").
        Offset(offset).Limit(size).
        Find(&users).Error; err != nil {
        return nil, 0, fmt.Errorf("mysql: failed to find all users: %w", err)
    }

    return users, total, nil
}

func (d *mysqlUserDAO) Save(ctx context.Context, user *entity.User) error {
    return d.db.WithContext(ctx).Create(user).Error
}

func (d *mysqlUserDAO) Update(ctx context.Context, user *entity.User) error {
    return d.db.WithContext(ctx).Save(user).Error
}

func (d *mysqlUserDAO) Delete(ctx context.Context, id string) error {
    return d.db.WithContext(ctx).Where("id = ?", id).Delete(&entity.User{}).Error
}

// internal/domain/dao/user_dao_postgres.go
package dao

import (
    "context"
    "fmt"

    "gorm.io/gorm"

    "arcana-cloud-go/internal/domain/entity"
)

type postgresUserDAO struct {
    db *gorm.DB
}

func NewPostgresUserDAO(db *gorm.DB) UserDAO {
    return &postgresUserDAO{db: db}
}

func (d *postgresUserDAO) FindByID(ctx context.Context, id string) (*entity.User, error) {
    var user entity.User
    if err := d.db.WithContext(ctx).Where("id = ?", id).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, fmt.Errorf("postgres: failed to find user by ID: %w", err)
    }
    return &user, nil
}

func (d *postgresUserDAO) FindByEmail(ctx context.Context, email string) (*entity.User, error) {
    var user entity.User
    if err := d.db.WithContext(ctx).Where("email = ?", email).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, fmt.Errorf("postgres: failed to find user by email: %w", err)
    }
    return &user, nil
}

func (d *postgresUserDAO) FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error) {
    var users []*entity.User
    var total int64

    d.db.WithContext(ctx).Model(&entity.User{}).Count(&total)

    offset := page * size
    if err := d.db.WithContext(ctx).
        Order("created_at DESC").
        Offset(offset).Limit(size).
        Find(&users).Error; err != nil {
        return nil, 0, fmt.Errorf("postgres: failed to find all users: %w", err)
    }

    return users, total, nil
}

func (d *postgresUserDAO) Save(ctx context.Context, user *entity.User) error {
    return d.db.WithContext(ctx).Create(user).Error
}

func (d *postgresUserDAO) Update(ctx context.Context, user *entity.User) error {
    return d.db.WithContext(ctx).Save(user).Error
}

func (d *postgresUserDAO) Delete(ctx context.Context, id string) error {
    return d.db.WithContext(ctx).Where("id = ?", id).Delete(&entity.User{}).Error
}

// internal/domain/dao/user_dao_mongo.go
package dao

import (
    "context"
    "fmt"

    "go.mongodb.org/mongo-driver/bson"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"

    "arcana-cloud-go/internal/domain/entity"
)

type mongoUserDAO struct {
    collection *mongo.Collection
}

func NewMongoUserDAO(db *mongo.Database) UserDAO {
    return &mongoUserDAO{
        collection: db.Collection("users"),
    }
}

func (d *mongoUserDAO) FindByID(ctx context.Context, id string) (*entity.User, error) {
    var user entity.User
    err := d.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&user)
    if err == mongo.ErrNoDocuments {
        return nil, nil
    }
    if err != nil {
        return nil, fmt.Errorf("mongo: failed to find user by ID: %w", err)
    }
    return &user, nil
}

func (d *mongoUserDAO) FindByEmail(ctx context.Context, email string) (*entity.User, error) {
    var user entity.User
    err := d.collection.FindOne(ctx, bson.M{"email": email}).Decode(&user)
    if err == mongo.ErrNoDocuments {
        return nil, nil
    }
    if err != nil {
        return nil, fmt.Errorf("mongo: failed to find user by email: %w", err)
    }
    return &user, nil
}

func (d *mongoUserDAO) FindAll(ctx context.Context, page, size int) ([]*entity.User, int64, error) {
    total, err := d.collection.CountDocuments(ctx, bson.M{})
    if err != nil {
        return nil, 0, fmt.Errorf("mongo: failed to count users: %w", err)
    }

    opts := options.Find().
        SetSort(bson.D{{Key: "created_at", Value: -1}}).
        SetSkip(int64(page * size)).
        SetLimit(int64(size))

    cursor, err := d.collection.Find(ctx, bson.M{}, opts)
    if err != nil {
        return nil, 0, fmt.Errorf("mongo: failed to find users: %w", err)
    }
    defer cursor.Close(ctx)

    var users []*entity.User
    if err := cursor.All(ctx, &users); err != nil {
        return nil, 0, fmt.Errorf("mongo: failed to decode users: %w", err)
    }

    return users, total, nil
}

func (d *mongoUserDAO) Save(ctx context.Context, user *entity.User) error {
    _, err := d.collection.InsertOne(ctx, user)
    return err
}

func (d *mongoUserDAO) Update(ctx context.Context, user *entity.User) error {
    _, err := d.collection.ReplaceOne(ctx, bson.M{"_id": user.ID}, user)
    return err
}

func (d *mongoUserDAO) Delete(ctx context.Context, id string) error {
    _, err := d.collection.DeleteOne(ctx, bson.M{"_id": id})
    return err
}

// internal/domain/dao/factory.go
package dao

import (
    "fmt"

    "go.mongodb.org/mongo-driver/mongo"
    "gorm.io/gorm"
)

type DatabaseType string

const (
    DBMySQL    DatabaseType = "mysql"
    DBPostgres DatabaseType = "postgres"
    DBMongo    DatabaseType = "mongo"
)

type DAOFactory struct {
    dbType  DatabaseType
    gormDB  *gorm.DB
    mongoDB *mongo.Database
}

func NewDAOFactory(dbType DatabaseType, gormDB *gorm.DB, mongoDB *mongo.Database) *DAOFactory {
    return &DAOFactory{
        dbType:  dbType,
        gormDB:  gormDB,
        mongoDB: mongoDB,
    }
}

func (f *DAOFactory) NewUserDAO() UserDAO {
    switch f.dbType {
    case DBMySQL:
        return NewMySQLUserDAO(f.gormDB)
    case DBPostgres:
        return NewPostgresUserDAO(f.gormDB)
    case DBMongo:
        return NewMongoUserDAO(f.mongoDB)
    default:
        panic(fmt.Sprintf("unsupported database type: %s", f.dbType))
    }
}

// Wire in fx DI:
// fx.Provide(func(cfg *config.Config, gormDB *gorm.DB, mongoDB *mongo.Database) *dao.DAOFactory {
//     return dao.NewDAOFactory(dao.DatabaseType(cfg.Database.Type), gormDB, mongoDB)
// })
// fx.Provide(func(factory *dao.DAOFactory) dao.UserDAO {
//     return factory.NewUserDAO()
// })
```
