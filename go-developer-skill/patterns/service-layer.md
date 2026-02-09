# Service Layer Patterns

Deep dive into service layer patterns for Go enterprise applications.

---

## Core Principles

1. **Single Responsibility**: Each service handles one domain
2. **Dependency Injection**: Use fx (Uber) for IoC
3. **Interface Segregation**: Define clear interfaces
4. **Pure Business Logic**: No HTTP/gRPC concerns
5. **Context Propagation**: Always pass context.Context

---

## Service Interface Pattern

```go
// Define interface first
type UserService interface {
    GetUser(ctx context.Context, userID string) (*entity.UserDTO, error)
    GetUsers(ctx context.Context, page, size int) ([]*entity.UserDTO, int64, error)
    CreateUser(ctx context.Context, req *CreateUserRequest) (*entity.UserDTO, error)
    UpdateUser(ctx context.Context, userID string, req *UpdateUserRequest) (*entity.UserDTO, error)
    DeleteUser(ctx context.Context, userID string) error
}

// Implement with unexported struct
type userServiceImpl struct {
    repo   repository.UserRepository
    cache  *redis.Client
    logger *zap.Logger
}

// Constructor returns interface type
func NewUserService(repo repository.UserRepository, cache *redis.Client, logger *zap.Logger) UserService {
    return &userServiceImpl{repo: repo, cache: cache, logger: logger}
}
```

---

## Repository Injection Pattern

```go
type orderServiceImpl struct {
    orderRepo   repository.OrderRepository
    productRepo repository.ProductRepository
    userRepo    repository.UserRepository
    logger      *zap.Logger
}

func NewOrderService(
    orderRepo repository.OrderRepository,
    productRepo repository.ProductRepository,
    userRepo repository.UserRepository,
    logger *zap.Logger,
) OrderService {
    return &orderServiceImpl{
        orderRepo:   orderRepo,
        productRepo: productRepo,
        userRepo:    userRepo,
        logger:      logger,
    }
}

func (s *orderServiceImpl) CreateOrder(ctx context.Context, userID string, items []OrderItemDTO) (*Order, error) {
    // Validate user exists
    user, err := s.userRepo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrNotFoundError("User not found")
    }

    // Validate products and stock
    for _, item := range items {
        product, err := s.productRepo.FindByID(ctx, item.ProductID)
        if err != nil {
            return nil, fmt.Errorf("failed to find product: %w", err)
        }
        if product == nil {
            return nil, entity.ErrNotFoundError(fmt.Sprintf("Product not found: %s", item.ProductID))
        }
        if product.Stock < item.Quantity {
            return nil, entity.ErrValidationError("Insufficient stock", map[string]interface{}{
                "productId": item.ProductID,
                "available": product.Stock,
                "requested": item.Quantity,
            })
        }
    }

    return s.orderRepo.CreateWithItems(ctx, userID, items)
}
```

---

## Caching Pattern

```go
type productServiceImpl struct {
    repo   repository.ProductRepository
    cache  *redis.Client
    logger *zap.Logger
}

const (
    cachePrefix = "product:"
    cacheTTL    = 1 * time.Hour
)

func (s *productServiceImpl) GetProduct(ctx context.Context, productID string) (*entity.ProductDTO, error) {
    cacheKey := cachePrefix + productID

    // Try cache first
    cached, err := s.cache.Get(ctx, cacheKey).Bytes()
    if err == nil {
        var dto entity.ProductDTO
        if json.Unmarshal(cached, &dto) == nil {
            return &dto, nil
        }
    }

    // Load from database
    product, err := s.repo.FindByID(ctx, productID)
    if err != nil {
        return nil, fmt.Errorf("failed to find product: %w", err)
    }
    if product == nil {
        return nil, nil
    }

    dto := entity.ToProductDTO(product)

    // Cache the result
    if data, err := json.Marshal(dto); err == nil {
        s.cache.Set(ctx, cacheKey, data, cacheTTL)
    }

    return dto, nil
}

func (s *productServiceImpl) UpdateProduct(ctx context.Context, productID string, req *UpdateProductRequest) (*entity.ProductDTO, error) {
    // ... update logic ...

    // Invalidate cache
    s.cache.Del(ctx, cachePrefix+productID)

    return entity.ToProductDTO(updated), nil
}
```

---

## Error Handling Pattern

```go
func (s *userServiceImpl) GetUser(ctx context.Context, userID string) (*entity.UserDTO, error) {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        // Wrap error with context for tracing
        s.logger.Error("failed to find user", zap.String("userID", userID), zap.Error(err))
        return nil, fmt.Errorf("userService.GetUser(%s): %w", userID, err)
    }
    if user == nil {
        return nil, nil // Let controller decide 404 vs nil
    }
    return entity.ToUserDTO(user), nil
}

func (s *userServiceImpl) UpdateUser(ctx context.Context, userID string, req *UpdateUserRequest) (*entity.UserDTO, error) {
    user, err := s.repo.FindByID(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("failed to find user: %w", err)
    }
    if user == nil {
        return nil, entity.ErrNotFoundError(fmt.Sprintf("User not found: %s", userID))
    }

    if req.Email != nil {
        existing, err := s.repo.FindByEmail(ctx, *req.Email)
        if err != nil {
            return nil, fmt.Errorf("failed to check email: %w", err)
        }
        if existing != nil && existing.ID != userID {
            return nil, entity.ErrConflictError("Email already in use")
        }
    }

    // Update and return
    if req.Name != nil {
        user.Name = *req.Name
    }
    if req.Email != nil {
        user.Email = *req.Email
    }

    if err := s.repo.Update(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to update user: %w", err)
    }

    return entity.ToUserDTO(user), nil
}
```

---

## Transaction Pattern

```go
type orderServiceImpl struct {
    db     *gorm.DB
    logger *zap.Logger
}

func (s *orderServiceImpl) CreateOrder(ctx context.Context, userID string, items []OrderItemDTO) (*Order, error) {
    var order *Order

    err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
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
            var product Product
            if err := tx.Where("id = ?", item.ProductID).First(&product).Error; err != nil {
                return fmt.Errorf("product not found: %s", item.ProductID)
            }
            if product.Stock < item.Quantity {
                return fmt.Errorf("insufficient stock for %s", item.ProductID)
            }

            // Create order item
            if err := tx.Create(&OrderItem{
                OrderID:   order.ID,
                ProductID: item.ProductID,
                Quantity:  item.Quantity,
                Price:     product.Price,
            }).Error; err != nil {
                return err
            }

            // Decrement stock
            if err := tx.Model(&Product{}).
                Where("id = ?", item.ProductID).
                Update("stock", gorm.Expr("stock - ?", item.Quantity)).Error; err != nil {
                return err
            }

            totalAmount += product.Price * float64(item.Quantity)
        }

        return tx.Model(order).Update("total_amount", totalAmount).Error
    })

    if err != nil {
        return nil, fmt.Errorf("failed to create order: %w", err)
    }

    s.logger.Info("order created",
        zap.String("orderID", order.ID),
        zap.String("userID", userID),
    )

    return order, nil
}
```

---

## Testing Service Layer

```go
func TestUserService_GetUser(t *testing.T) {
    mockRepo := new(MockUserRepository)
    logger, _ := zap.NewDevelopment()
    svc := NewUserService(mockRepo, nil, logger)

    t.Run("found", func(t *testing.T) {
        mockUser := &entity.User{ID: "123", Name: "Test User"}
        mockRepo.On("FindByID", mock.Anything, "123").Return(mockUser, nil).Once()

        result, err := svc.GetUser(context.Background(), "123")

        assert.NoError(t, err)
        assert.NotNil(t, result)
        assert.Equal(t, "123", result.ID)
    })

    t.Run("not found", func(t *testing.T) {
        mockRepo.On("FindByID", mock.Anything, "missing").Return(nil, nil).Once()

        result, err := svc.GetUser(context.Background(), "missing")

        assert.NoError(t, err)
        assert.Nil(t, result)
    })

    t.Run("create with duplicate email", func(t *testing.T) {
        existing := &entity.User{Email: "taken@example.com"}
        mockRepo.On("FindByEmail", mock.Anything, "taken@example.com").Return(existing, nil).Once()

        result, err := svc.CreateUser(context.Background(), &CreateUserRequest{
            Name:     "New User",
            Email:    "taken@example.com",
            Password: "Password123",
        })

        assert.Error(t, err)
        assert.Nil(t, result)
    })
}
```
