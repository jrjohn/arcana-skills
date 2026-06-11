# Spring Boot Developer Skill - Code Examples

## Table of Contents
1. [User Authentication Feature](#user-authentication-feature)
2. [CRUD with gRPC and REST](#crud-with-grpc-and-rest)
3. [Plugin Development Example](#plugin-development-example)
4. [Event-Driven Architecture](#event-driven-architecture)
5. [File Upload with Progress](#file-upload-with-progress)

---

## User Authentication Feature

### Domain Layer

```java
// model/entity/UserAccount.java
@Entity
@Table(name = "user_accounts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserAccount {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String passwordHash;

    @Column(nullable = false)
    private String name;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "user_roles")
    @Enumerated(EnumType.STRING)
    @Builder.Default
    private Set<Role> roles = new HashSet<>();

    @Column(nullable = false)
    @Builder.Default
    private boolean enabled = true;

    @Column(nullable = false)
    @Builder.Default
    private boolean locked = false;

    private Instant lastLoginAt;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}

public enum Role {
    ROLE_USER,
    ROLE_ADMIN,
    ROLE_MODERATOR
}

// model/entity/RefreshToken.java
@Entity
@Table(name = "refresh_tokens")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, unique = true)
    private String token;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private UserAccount user;

    @Column(nullable = false)
    private Instant expiresAt;

    @Column(nullable = false)
    @Builder.Default
    private boolean revoked = false;

    @CreatedDate
    private Instant createdAt;
}
```

### Service Layer

```java
// service/AuthService.java
public interface AuthService {
    TokenPair login(LoginRequest request);
    TokenPair refresh(String refreshToken);
    void logout(String refreshToken);
    void logoutAll(String userId);
    UserAccount register(RegisterRequest request);
    void changePassword(String userId, ChangePasswordRequest request);
    void resetPassword(String email);
}

// service/impl/AuthServiceImpl.java
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthServiceImpl implements AuthService {

    private final UserAccountRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    @Transactional
    public TokenPair login(LoginRequest request) {
        UserAccount user = userRepository.findByEmail(request.getEmail())
            .orElseThrow(() -> new AuthenticationException("Invalid credentials"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            eventPublisher.publishEvent(new LoginFailedEvent(request.getEmail()));
            throw new AuthenticationException("Invalid credentials");
        }

        if (!user.isEnabled()) {
            throw new AuthenticationException("Account is disabled");
        }

        if (user.isLocked()) {
            throw new AuthenticationException("Account is locked");
        }

        // Update last login
        user.setLastLoginAt(Instant.now());
        userRepository.save(user);

        // Generate tokens
        TokenPair tokens = jwtTokenProvider.createTokenPair(toUserDetails(user));

        // Store refresh token
        RefreshToken refreshToken = RefreshToken.builder()
            .token(tokens.getRefreshToken())
            .user(user)
            .expiresAt(Instant.now().plusSeconds(jwtTokenProvider.getRefreshTokenExpiration()))
            .build();
        refreshTokenRepository.save(refreshToken);

        eventPublisher.publishEvent(new LoginSuccessEvent(user.getId()));

        return tokens;
    }

    @Override
    @Transactional
    public TokenPair refresh(String refreshTokenValue) {
        RefreshToken refreshToken = refreshTokenRepository.findByToken(refreshTokenValue)
            .orElseThrow(() -> new AuthenticationException("Invalid refresh token"));

        if (refreshToken.isRevoked()) {
            throw new AuthenticationException("Refresh token has been revoked");
        }

        if (refreshToken.getExpiresAt().isBefore(Instant.now())) {
            throw new AuthenticationException("Refresh token has expired");
        }

        UserAccount user = refreshToken.getUser();

        // Revoke old refresh token
        refreshToken.setRevoked(true);
        refreshTokenRepository.save(refreshToken);

        // Generate new tokens
        TokenPair tokens = jwtTokenProvider.createTokenPair(toUserDetails(user));

        // Store new refresh token
        RefreshToken newRefreshToken = RefreshToken.builder()
            .token(tokens.getRefreshToken())
            .user(user)
            .expiresAt(Instant.now().plusSeconds(jwtTokenProvider.getRefreshTokenExpiration()))
            .build();
        refreshTokenRepository.save(newRefreshToken);

        return tokens;
    }

    @Override
    @Transactional
    public void logout(String refreshTokenValue) {
        refreshTokenRepository.findByToken(refreshTokenValue)
            .ifPresent(token -> {
                token.setRevoked(true);
                refreshTokenRepository.save(token);
            });
    }

    @Override
    @Transactional
    public void logoutAll(String userId) {
        refreshTokenRepository.revokeAllByUserId(userId);
    }

    @Override
    @Transactional
    public UserAccount register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new DuplicateEmailException(request.getEmail());
        }

        UserAccount user = UserAccount.builder()
            .email(request.getEmail())
            .passwordHash(passwordEncoder.encode(request.getPassword()))
            .name(request.getName())
            .roles(Set.of(Role.ROLE_USER))
            .build();

        user = userRepository.save(user);

        eventPublisher.publishEvent(new UserRegisteredEvent(user));

        return user;
    }

    @Override
    @Transactional
    public void changePassword(String userId, ChangePasswordRequest request) {
        UserAccount user = userRepository.findById(userId)
            .orElseThrow(() -> new EntityNotFoundException("User not found"));

        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPasswordHash())) {
            throw new AuthenticationException("Current password is incorrect");
        }

        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);

        // Revoke all refresh tokens
        refreshTokenRepository.revokeAllByUserId(userId);

        eventPublisher.publishEvent(new PasswordChangedEvent(userId));
    }

    private UserDetails toUserDetails(UserAccount user) {
        return User.builder()
            .username(user.getEmail())
            .password(user.getPasswordHash())
            .authorities(user.getRoles().stream()
                .map(role -> new SimpleGrantedAuthority(role.name()))
                .toList())
            .disabled(!user.isEnabled())
            .accountLocked(user.isLocked())
            .build();
    }
}
```

### Controller Layer

```java
// controller/rest/AuthController.java
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "Authentication API")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    @Operation(summary = "User login")
    public ResponseEntity<TokenResponse> login(@Valid @RequestBody LoginRequest request) {
        TokenPair tokens = authService.login(request);
        return ResponseEntity.ok(TokenResponse.from(tokens));
    }

    @PostMapping("/register")
    @Operation(summary = "User registration")
    public ResponseEntity<UserResponse> register(@Valid @RequestBody RegisterRequest request) {
        UserAccount user = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(UserResponse.from(user));
    }

    @PostMapping("/refresh")
    @Operation(summary = "Refresh access token")
    public ResponseEntity<TokenResponse> refresh(@Valid @RequestBody RefreshRequest request) {
        TokenPair tokens = authService.refresh(request.getRefreshToken());
        return ResponseEntity.ok(TokenResponse.from(tokens));
    }

    @PostMapping("/logout")
    @Operation(summary = "Logout")
    public ResponseEntity<Void> logout(@Valid @RequestBody LogoutRequest request) {
        authService.logout(request.getRefreshToken());
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/logout-all")
    @Operation(summary = "Logout from all devices")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Void> logoutAll(@AuthenticationPrincipal UserDetails user) {
        authService.logoutAll(user.getUsername());
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/change-password")
    @Operation(summary = "Change password")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Void> changePassword(
            @AuthenticationPrincipal UserDetails user,
            @Valid @RequestBody ChangePasswordRequest request) {
        authService.changePassword(user.getUsername(), request);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/me")
    @Operation(summary = "Get current user")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserResponse> getCurrentUser(@AuthenticationPrincipal UserDetails user) {
        return ResponseEntity.ok(UserResponse.builder()
            .email(user.getUsername())
            .roles(user.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .toList())
            .build());
    }
}

// dto/request/LoginRequest.java
@Data
public class LoginRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;

    @NotBlank(message = "Password is required")
    private String password;
}

// dto/request/RegisterRequest.java
@Data
public class RegisterRequest {

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100)
    private String name;

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, message = "Password must be at least 8 characters")
    @Pattern(
        regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).*$",
        message = "Password must contain uppercase, lowercase, and number"
    )
    private String password;
}

// dto/response/TokenResponse.java
@Data
@Builder
public class TokenResponse {
    private String accessToken;
    private String refreshToken;
    private String tokenType;
    private long expiresIn;

    public static TokenResponse from(TokenPair tokens) {
        return TokenResponse.builder()
            .accessToken(tokens.getAccessToken())
            .refreshToken(tokens.getRefreshToken())
            .tokenType("Bearer")
            .expiresIn(tokens.getExpiresIn())
            .build();
    }
}
```

---

## CRUD with gRPC and REST

### Complete Product Management

```protobuf
// product.proto
syntax = "proto3";

package com.arcana.grpc.product;

option java_multiple_files = true;
option java_package = "com.arcana.grpc.product";

import "google/protobuf/empty.proto";
import "google/protobuf/timestamp.proto";
import "google/protobuf/wrappers.proto";

service ProductService {
    rpc GetProduct (GetProductRequest) returns (ProductResponse);
    rpc ListProducts (ListProductsRequest) returns (ListProductsResponse);
    rpc CreateProduct (CreateProductRequest) returns (ProductResponse);
    rpc UpdateProduct (UpdateProductRequest) returns (ProductResponse);
    rpc DeleteProduct (DeleteProductRequest) returns (google.protobuf.Empty);
    rpc SearchProducts (SearchProductsRequest) returns (stream ProductResponse);
    rpc BatchUpdateStock (stream StockUpdateRequest) returns (BatchStockUpdateResponse);
}

message Product {
    string id = 1;
    string name = 2;
    string description = 3;
    double price = 4;
    int32 stock = 5;
    string category = 6;
    repeated string tags = 7;
    ProductStatus status = 8;
    google.protobuf.Timestamp created_at = 9;
    google.protobuf.Timestamp updated_at = 10;
}

enum ProductStatus {
    DRAFT = 0;
    ACTIVE = 1;
    INACTIVE = 2;
    ARCHIVED = 3;
}

message GetProductRequest {
    string id = 1;
}

message ListProductsRequest {
    int32 page = 1;
    int32 size = 2;
    optional string category = 3;
    optional ProductStatus status = 4;
    optional string sort_by = 5;
    optional string sort_order = 6;
}

message ListProductsResponse {
    repeated ProductResponse products = 1;
    int32 total = 2;
    int32 page = 3;
    int32 size = 4;
    bool has_next = 5;
}

message CreateProductRequest {
    string name = 1;
    string description = 2;
    double price = 3;
    int32 stock = 4;
    string category = 5;
    repeated string tags = 6;
}

message UpdateProductRequest {
    string id = 1;
    google.protobuf.StringValue name = 2;
    google.protobuf.StringValue description = 3;
    google.protobuf.DoubleValue price = 4;
    google.protobuf.Int32Value stock = 5;
    google.protobuf.StringValue category = 6;
    repeated string tags = 7;
    optional ProductStatus status = 8;
}

message DeleteProductRequest {
    string id = 1;
}

message SearchProductsRequest {
    string query = 1;
    optional string category = 2;
    optional double min_price = 3;
    optional double max_price = 4;
    int32 limit = 5;
}

message StockUpdateRequest {
    string product_id = 1;
    int32 quantity_change = 2;
}

message BatchStockUpdateResponse {
    int32 success_count = 1;
    int32 failure_count = 2;
    repeated StockUpdateError errors = 3;
}

message StockUpdateError {
    string product_id = 1;
    string error_message = 2;
}

message ProductResponse {
    string id = 1;
    string name = 2;
    string description = 3;
    double price = 4;
    int32 stock = 5;
    string category = 6;
    repeated string tags = 7;
    ProductStatus status = 8;
    google.protobuf.Timestamp created_at = 9;
    google.protobuf.Timestamp updated_at = 10;
}
```

### Service Implementation

```java
// service/ProductService.java
public interface ProductService {
    Optional<Product> findById(String id);
    Page<Product> findAll(Pageable pageable);
    Page<Product> findByCategory(String category, Pageable pageable);
    List<Product> search(String query, String category, Double minPrice, Double maxPrice, int limit);
    Product create(Product product);
    Optional<Product> update(String id, Product product);
    Optional<Product> patch(String id, Map<String, Object> updates);
    void delete(String id);
    void updateStock(String productId, int quantityChange);
}

// service/impl/ProductServiceImpl.java
@Service
@RequiredArgsConstructor
@Slf4j
public class ProductServiceImpl implements ProductService {

    private final ProductRepository productRepository;
    private final ProductSearchRepository searchRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    @Cacheable(value = "products", key = "#id")
    public Optional<Product> findById(String id) {
        return productRepository.findById(id);
    }

    @Override
    @Cacheable(value = "product-lists", key = "'page:' + #pageable.pageNumber")
    public Page<Product> findAll(Pageable pageable) {
        return productRepository.findAll(pageable);
    }

    @Override
    public List<Product> search(String query, String category, Double minPrice, Double maxPrice, int limit) {
        // Use Elasticsearch for full-text search
        return searchRepository.search(query, category, minPrice, maxPrice, limit);
    }

    @Override
    @Transactional
    @CacheEvict(value = "product-lists", allEntries = true)
    public Product create(Product product) {
        product.setStatus(ProductStatus.DRAFT);
        Product saved = productRepository.save(product);

        // Index in Elasticsearch
        searchRepository.index(saved);

        eventPublisher.publishEvent(new ProductCreatedEvent(saved));

        return saved;
    }

    @Override
    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "products", key = "#id"),
        @CacheEvict(value = "product-lists", allEntries = true)
    })
    public Optional<Product> update(String id, Product product) {
        return productRepository.findById(id)
            .map(existing -> {
                existing.setName(product.getName());
                existing.setDescription(product.getDescription());
                existing.setPrice(product.getPrice());
                existing.setStock(product.getStock());
                existing.setCategory(product.getCategory());
                existing.setTags(product.getTags());
                if (product.getStatus() != null) {
                    existing.setStatus(product.getStatus());
                }

                Product saved = productRepository.save(existing);
                searchRepository.index(saved);

                eventPublisher.publishEvent(new ProductUpdatedEvent(saved));

                return saved;
            });
    }

    @Override
    @Transactional
    @CacheEvict(value = "products", key = "#productId")
    public void updateStock(String productId, int quantityChange) {
        Product product = productRepository.findById(productId)
            .orElseThrow(() -> new EntityNotFoundException("Product not found: " + productId));

        int newStock = product.getStock() + quantityChange;
        if (newStock < 0) {
            throw new InsufficientStockException(productId, product.getStock(), -quantityChange);
        }

        product.setStock(newStock);
        productRepository.save(product);

        if (newStock == 0) {
            eventPublisher.publishEvent(new ProductOutOfStockEvent(productId));
        } else if (newStock <= 10) {
            eventPublisher.publishEvent(new ProductLowStockEvent(productId, newStock));
        }
    }

    @Override
    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "products", key = "#id"),
        @CacheEvict(value = "product-lists", allEntries = true)
    })
    public void delete(String id) {
        productRepository.findById(id).ifPresent(product -> {
            productRepository.delete(product);
            searchRepository.delete(id);
            eventPublisher.publishEvent(new ProductDeletedEvent(id));
        });
    }
}
```

### gRPC Service

```java
// controller/grpc/ProductGrpcService.java
@GrpcService
@RequiredArgsConstructor
@Slf4j
public class ProductGrpcService extends ProductServiceGrpc.ProductServiceImplBase {

    private final ProductService productService;
    private final ProductMapper mapper;

    @Override
    public void getProduct(GetProductRequest request, StreamObserver<ProductResponse> responseObserver) {
        productService.findById(request.getId())
            .map(mapper::toProto)
            .ifPresentOrElse(
                product -> {
                    responseObserver.onNext(product);
                    responseObserver.onCompleted();
                },
                () -> responseObserver.onError(
                    Status.NOT_FOUND
                        .withDescription("Product not found: " + request.getId())
                        .asRuntimeException()
                )
            );
    }

    @Override
    public void listProducts(ListProductsRequest request, StreamObserver<ListProductsResponse> responseObserver) {
        Sort sort = Sort.by(
            request.getSortOrder().equals("desc") ? Sort.Direction.DESC : Sort.Direction.ASC,
            request.hasSortBy() ? request.getSortBy() : "createdAt"
        );
        Pageable pageable = PageRequest.of(request.getPage(), request.getSize(), sort);

        Page<Product> page = request.hasCategory()
            ? productService.findByCategory(request.getCategory(), pageable)
            : productService.findAll(pageable);

        ListProductsResponse response = ListProductsResponse.newBuilder()
            .addAllProducts(page.getContent().stream().map(mapper::toProto).toList())
            .setTotal((int) page.getTotalElements())
            .setPage(page.getNumber())
            .setSize(page.getSize())
            .setHasNext(page.hasNext())
            .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void searchProducts(SearchProductsRequest request, StreamObserver<ProductResponse> responseObserver) {
        List<Product> products = productService.search(
            request.getQuery(),
            request.hasCategory() ? request.getCategory() : null,
            request.hasMinPrice() ? request.getMinPrice() : null,
            request.hasMaxPrice() ? request.getMaxPrice() : null,
            request.getLimit()
        );

        products.stream()
            .map(mapper::toProto)
            .forEach(responseObserver::onNext);

        responseObserver.onCompleted();
    }

    @Override
    public void createProduct(CreateProductRequest request, StreamObserver<ProductResponse> responseObserver) {
        try {
            Product product = productService.create(mapper.fromProto(request));
            responseObserver.onNext(mapper.toProto(product));
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("Error creating product", e);
            responseObserver.onError(
                Status.INTERNAL
                    .withDescription(e.getMessage())
                    .asRuntimeException()
            );
        }
    }

    @Override
    public StreamObserver<StockUpdateRequest> batchUpdateStock(
            StreamObserver<BatchStockUpdateResponse> responseObserver) {

        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger failureCount = new AtomicInteger(0);
        List<StockUpdateError> errors = new CopyOnWriteArrayList<>();

        return new StreamObserver<>() {
            @Override
            public void onNext(StockUpdateRequest request) {
                try {
                    productService.updateStock(request.getProductId(), request.getQuantityChange());
                    successCount.incrementAndGet();
                } catch (Exception e) {
                    failureCount.incrementAndGet();
                    errors.add(StockUpdateError.newBuilder()
                        .setProductId(request.getProductId())
                        .setErrorMessage(e.getMessage())
                        .build());
                }
            }

            @Override
            public void onError(Throwable t) {
                log.error("Client error in batchUpdateStock", t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(BatchStockUpdateResponse.newBuilder()
                    .setSuccessCount(successCount.get())
                    .setFailureCount(failureCount.get())
                    .addAllErrors(errors)
                    .build());
                responseObserver.onCompleted();
            }
        };
    }
}
```

### REST Controller

```java
// controller/rest/ProductController.java
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Tag(name = "Products", description = "Product management API")
public class ProductController {

    private final ProductService productService;
    private final ProductMapper mapper;

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getProduct(@PathVariable String id) {
        return productService.findById(id)
            .map(mapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<PageResponse<ProductResponse>> listProducts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String category,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String sortOrder) {

        Pageable pageable = PageRequest.of(page, size,
            Sort.by(sortOrder.equals("desc") ? Sort.Direction.DESC : Sort.Direction.ASC, sortBy));

        Page<Product> result = category != null
            ? productService.findByCategory(category, pageable)
            : productService.findAll(pageable);

        return ResponseEntity.ok(PageResponse.of(result, mapper::toResponse));
    }

    @GetMapping("/search")
    public ResponseEntity<List<ProductResponse>> searchProducts(
            @RequestParam String query,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Double minPrice,
            @RequestParam(required = false) Double maxPrice,
            @RequestParam(defaultValue = "20") int limit) {

        List<Product> products = productService.search(query, category, minPrice, maxPrice, limit);
        return ResponseEntity.ok(products.stream().map(mapper::toResponse).toList());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ProductResponse> createProduct(
            @Valid @RequestBody CreateProductRequest request) {

        Product product = productService.create(mapper.fromRequest(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(mapper.toResponse(product));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ProductResponse> updateProduct(
            @PathVariable String id,
            @Valid @RequestBody UpdateProductRequest request) {

        return productService.update(id, mapper.fromRequest(request))
            .map(mapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}/stock")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> updateStock(
            @PathVariable String id,
            @Valid @RequestBody StockUpdateRequest request) {

        productService.updateStock(id, request.getQuantityChange());
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteProduct(@PathVariable String id) {
        productService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

---

## Plugin Development Example

### Analytics Plugin

```java
// AnalyticsPlugin.java
@ArcanaPluginManifest(
    key = "analytics",
    name = "Analytics Plugin",
    version = "1.0.0",
    description = "Provides analytics and reporting capabilities",
    requiredServices = {"UserService", "ProductService"}
)
public class AnalyticsPlugin implements ArcanaPlugin {

    private PluginContext context;
    private AnalyticsService analyticsService;
    private ScheduledExecutorService scheduler;

    @Override
    public String getKey() { return "analytics"; }

    @Override
    public String getName() { return "Analytics Plugin"; }

    @Override
    public String getVersion() { return "1.0.0"; }

    @Override
    public void onStart(PluginContext context) {
        this.context = context;
        Logger log = context.getLogger();
        log.info("Starting Analytics Plugin");

        // Get required services
        UserService userService = context.getService(UserService.class);
        ProductService productService = context.getService(ProductService.class);

        // Create plugin services
        MetricsCollector metricsCollector = new MetricsCollector();
        ReportGenerator reportGenerator = new ReportGenerator();
        this.analyticsService = new AnalyticsService(userService, productService, metricsCollector);

        // Register beans
        context.registerBean("analyticsService", analyticsService);
        context.registerBean("metricsCollector", metricsCollector);
        context.registerBean("reportGenerator", reportGenerator);

        // Register REST endpoints
        context.registerRestEndpoint("/api/v1/analytics", new AnalyticsController(analyticsService));
        context.registerRestEndpoint("/api/v1/reports", new ReportController(reportGenerator));

        // Subscribe to events
        context.subscribe(UserCreatedEvent.class, event -> {
            analyticsService.trackUserCreated(event.getUser());
        });

        context.subscribe(ProductViewedEvent.class, event -> {
            analyticsService.trackProductView(event.getProductId(), event.getUserId());
        });

        context.subscribe(OrderCompletedEvent.class, event -> {
            analyticsService.trackOrder(event.getOrder());
        });

        // Start scheduled tasks
        scheduler = Executors.newScheduledThreadPool(2);
        scheduler.scheduleAtFixedRate(
            this::aggregateMetrics,
            1, 1, TimeUnit.HOURS
        );
        scheduler.scheduleAtFixedRate(
            this::generateDailyReport,
            getNextDailyReportTime(), 24, TimeUnit.HOURS
        );

        log.info("Analytics Plugin started successfully");
    }

    @Override
    public void onStop() {
        Logger log = context.getLogger();
        log.info("Stopping Analytics Plugin");

        // Shutdown scheduler
        if (scheduler != null) {
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(10, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
            }
        }

        // Cleanup
        analyticsService.flush();

        log.info("Analytics Plugin stopped");
    }

    @Override
    public HealthStatus healthCheck() {
        try {
            if (analyticsService.isHealthy()) {
                return HealthStatus.UP;
            }
            return HealthStatus.DEGRADED;
        } catch (Exception e) {
            return HealthStatus.DOWN;
        }
    }

    private void aggregateMetrics() {
        try {
            analyticsService.aggregateHourlyMetrics();
        } catch (Exception e) {
            context.getLogger().error("Failed to aggregate metrics", e);
        }
    }

    private void generateDailyReport() {
        try {
            analyticsService.generateDailyReport();
        } catch (Exception e) {
            context.getLogger().error("Failed to generate daily report", e);
        }
    }

    private long getNextDailyReportTime() {
        // Calculate time until next 2 AM
        return Duration.between(
            Instant.now(),
            Instant.now().atZone(ZoneId.systemDefault())
                .plusDays(1)
                .withHour(2)
                .withMinute(0)
                .toInstant()
        ).toHours();
    }
}

// AnalyticsService.java
public class AnalyticsService {

    private final UserService userService;
    private final ProductService productService;
    private final MetricsCollector metricsCollector;
    private final Map<String, AtomicLong> counters = new ConcurrentHashMap<>();

    public AnalyticsService(UserService userService, ProductService productService,
                           MetricsCollector metricsCollector) {
        this.userService = userService;
        this.productService = productService;
        this.metricsCollector = metricsCollector;
    }

    public void trackUserCreated(User user) {
        incrementCounter("users.created");
        metricsCollector.recordEvent("user.created", Map.of(
            "userId", user.getId(),
            "timestamp", Instant.now().toString()
        ));
    }

    public void trackProductView(String productId, String userId) {
        incrementCounter("products.views");
        incrementCounter("products.views." + productId);
        metricsCollector.recordEvent("product.viewed", Map.of(
            "productId", productId,
            "userId", userId != null ? userId : "anonymous",
            "timestamp", Instant.now().toString()
        ));
    }

    public void trackOrder(Order order) {
        incrementCounter("orders.completed");
        metricsCollector.recordMetric("orders.revenue", order.getTotal());
        metricsCollector.recordEvent("order.completed", Map.of(
            "orderId", order.getId(),
            "userId", order.getUserId(),
            "total", order.getTotal().toString(),
            "itemCount", String.valueOf(order.getItems().size()),
            "timestamp", Instant.now().toString()
        ));
    }

    public DashboardStats getDashboardStats() {
        return DashboardStats.builder()
            .totalUsers(getCounter("users.created"))
            .totalProductViews(getCounter("products.views"))
            .totalOrders(getCounter("orders.completed"))
            .hourlyStats(metricsCollector.getHourlyStats())
            .build();
    }

    public List<ProductStats> getTopProducts(int limit) {
        return counters.entrySet().stream()
            .filter(e -> e.getKey().startsWith("products.views."))
            .sorted((a, b) -> Long.compare(b.getValue().get(), a.getValue().get()))
            .limit(limit)
            .map(e -> {
                String productId = e.getKey().replace("products.views.", "");
                return ProductStats.builder()
                    .productId(productId)
                    .viewCount(e.getValue().get())
                    .product(productService.findById(productId).orElse(null))
                    .build();
            })
            .toList();
    }

    public void aggregateHourlyMetrics() {
        metricsCollector.aggregateHourly();
    }

    public void generateDailyReport() {
        // Generate and store daily report
        DailyReport report = DailyReport.builder()
            .date(LocalDate.now().minusDays(1))
            .totalUsers(getCounter("users.created"))
            .totalViews(getCounter("products.views"))
            .totalOrders(getCounter("orders.completed"))
            .topProducts(getTopProducts(10))
            .hourlyBreakdown(metricsCollector.getDailyBreakdown())
            .build();

        metricsCollector.storeDailyReport(report);
    }

    public void flush() {
        metricsCollector.flush();
    }

    public boolean isHealthy() {
        return metricsCollector.isConnected();
    }

    private void incrementCounter(String key) {
        counters.computeIfAbsent(key, k -> new AtomicLong(0)).incrementAndGet();
    }

    private long getCounter(String key) {
        return counters.getOrDefault(key, new AtomicLong(0)).get();
    }
}

// AnalyticsController.java
@RestController
@RequiredArgsConstructor
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/dashboard")
    public ResponseEntity<DashboardStats> getDashboard() {
        return ResponseEntity.ok(analyticsService.getDashboardStats());
    }

    @GetMapping("/top-products")
    public ResponseEntity<List<ProductStats>> getTopProducts(
            @RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(analyticsService.getTopProducts(limit));
    }
}
```

---

## Event-Driven Architecture

### Event System

```java
// event/DomainEvent.java
public abstract class DomainEvent {
    private final String id;
    private final Instant timestamp;
    private final String aggregateId;

    protected DomainEvent(String aggregateId) {
        this.id = UUID.randomUUID().toString();
        this.timestamp = Instant.now();
        this.aggregateId = aggregateId;
    }

    public String getId() { return id; }
    public Instant getTimestamp() { return timestamp; }
    public String getAggregateId() { return aggregateId; }
}

// event/OrderEvents.java
public class OrderCreatedEvent extends DomainEvent {
    private final Order order;

    public OrderCreatedEvent(Order order) {
        super(order.getId());
        this.order = order;
    }

    public Order getOrder() { return order; }
}

public class OrderPaidEvent extends DomainEvent {
    private final String orderId;
    private final BigDecimal amount;
    private final String paymentId;

    public OrderPaidEvent(String orderId, BigDecimal amount, String paymentId) {
        super(orderId);
        this.orderId = orderId;
        this.amount = amount;
        this.paymentId = paymentId;
    }
}

public class OrderShippedEvent extends DomainEvent {
    private final String orderId;
    private final String trackingNumber;
    private final String carrier;

    public OrderShippedEvent(String orderId, String trackingNumber, String carrier) {
        super(orderId);
        this.orderId = orderId;
        this.trackingNumber = trackingNumber;
        this.carrier = carrier;
    }
}

// event/listener/OrderEventListener.java
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderEventListener {

    private final NotificationService notificationService;
    private final InventoryService inventoryService;
    private final AnalyticsService analyticsService;

    @EventListener
    @Async
    public void handleOrderCreated(OrderCreatedEvent event) {
        log.info("Order created: {}", event.getOrder().getId());

        // Reserve inventory
        event.getOrder().getItems().forEach(item ->
            inventoryService.reserve(item.getProductId(), item.getQuantity())
        );

        // Send notification
        notificationService.sendOrderConfirmation(event.getOrder());

        // Track analytics
        analyticsService.trackOrder(event.getOrder());
    }

    @EventListener
    @Async
    public void handleOrderPaid(OrderPaidEvent event) {
        log.info("Order paid: {}", event.getOrderId());

        // Confirm inventory reservation
        inventoryService.confirmReservation(event.getOrderId());

        // Send payment confirmation
        notificationService.sendPaymentConfirmation(event.getOrderId(), event.getAmount());
    }

    @EventListener
    @Async
    public void handleOrderShipped(OrderShippedEvent event) {
        log.info("Order shipped: {}", event.getOrderId());

        // Send shipping notification
        notificationService.sendShippingNotification(
            event.getOrderId(),
            event.getTrackingNumber(),
            event.getCarrier()
        );
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleOrderCreatedAfterCommit(OrderCreatedEvent event) {
        // Actions that should only run after transaction commits
        log.info("Order {} committed to database", event.getOrder().getId());
    }
}

// service/OrderService.java
@Service
@RequiredArgsConstructor
@Transactional
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    public Order createOrder(CreateOrderRequest request) {
        Order order = Order.builder()
            .userId(request.getUserId())
            .items(request.getItems())
            .status(OrderStatus.PENDING)
            .total(calculateTotal(request.getItems()))
            .build();

        order = orderRepository.save(order);

        eventPublisher.publishEvent(new OrderCreatedEvent(order));

        return order;
    }

    @Override
    public void markAsPaid(String orderId, PaymentConfirmation payment) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new EntityNotFoundException("Order not found"));

        order.setStatus(OrderStatus.PAID);
        order.setPaymentId(payment.getPaymentId());
        orderRepository.save(order);

        eventPublisher.publishEvent(new OrderPaidEvent(
            orderId,
            payment.getAmount(),
            payment.getPaymentId()
        ));
    }

    @Override
    public void markAsShipped(String orderId, ShippingInfo shipping) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new EntityNotFoundException("Order not found"));

        order.setStatus(OrderStatus.SHIPPED);
        order.setTrackingNumber(shipping.getTrackingNumber());
        order.setCarrier(shipping.getCarrier());
        orderRepository.save(order);

        eventPublisher.publishEvent(new OrderShippedEvent(
            orderId,
            shipping.getTrackingNumber(),
            shipping.getCarrier()
        ));
    }
}
```

### Kafka Event Publishing

```java
// config/KafkaConfig.java
@Configuration
@EnableKafka
public class KafkaConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        config.put(ProducerConfig.ACKS_CONFIG, "all");
        config.put(ProducerConfig.RETRIES_CONFIG, 3);
        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    @Bean
    public ConsumerFactory<String, Object> consumerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ConsumerConfig.GROUP_ID_CONFIG, "arcana-group");
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        return new DefaultKafkaConsumerFactory<>(config);
    }
}

// event/KafkaEventPublisher.java
@Component
@RequiredArgsConstructor
@Slf4j
public class KafkaEventPublisher {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Async
    public void publish(String topic, String key, Object event) {
        CompletableFuture<SendResult<String, Object>> future =
            kafkaTemplate.send(topic, key, event);

        future.whenComplete((result, ex) -> {
            if (ex != null) {
                log.error("Failed to publish event to {}: {}", topic, ex.getMessage());
            } else {
                log.debug("Event published to {} partition {} offset {}",
                    topic,
                    result.getRecordMetadata().partition(),
                    result.getRecordMetadata().offset());
            }
        });
    }

    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        publish("orders", event.getOrder().getId(), OrderCreatedMessage.from(event));
    }

    @EventListener
    public void handleOrderPaid(OrderPaidEvent event) {
        publish("orders", event.getOrderId(), OrderPaidMessage.from(event));
    }
}

// event/KafkaEventConsumer.java
@Component
@RequiredArgsConstructor
@Slf4j
public class KafkaEventConsumer {

    private final WarehouseService warehouseService;
    private final ShippingService shippingService;

    @KafkaListener(topics = "orders", groupId = "warehouse-group")
    public void handleOrderForWarehouse(ConsumerRecord<String, OrderMessage> record) {
        log.info("Received order event for warehouse: {}", record.key());

        OrderMessage message = record.value();
        if (message instanceof OrderPaidMessage paidMessage) {
            warehouseService.prepareOrder(paidMessage.getOrderId());
        }
    }

    @KafkaListener(topics = "inventory-updates", groupId = "arcana-group")
    public void handleInventoryUpdate(ConsumerRecord<String, InventoryUpdateMessage> record) {
        log.info("Received inventory update: {}", record.key());

        InventoryUpdateMessage message = record.value();
        // Process inventory update
    }
}
```

---

## File Upload with Progress

### File Upload Service

```java
// service/FileUploadService.java
@Service
@RequiredArgsConstructor
@Slf4j
public class FileUploadService {

    private final FileStorageRepository storageRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Value("${file.upload.max-size}")
    private long maxFileSize;

    @Value("${file.upload.allowed-types}")
    private List<String> allowedTypes;

    public Mono<FileUploadResult> uploadFile(FilePart filePart, String userId) {
        return validateFile(filePart)
            .flatMap(file -> {
                String fileId = UUID.randomUUID().toString();
                String extension = getExtension(file.filename());
                String storagePath = generateStoragePath(fileId, extension);

                AtomicLong uploadedBytes = new AtomicLong(0);
                AtomicLong totalBytes = new AtomicLong(0);

                return file.content()
                    .doOnNext(dataBuffer -> {
                        long bytes = dataBuffer.readableByteCount();
                        uploadedBytes.addAndGet(bytes);
                        totalBytes.addAndGet(bytes);

                        // Publish progress event
                        eventPublisher.publishEvent(new FileUploadProgressEvent(
                            fileId,
                            uploadedBytes.get(),
                            -1 // Total unknown during streaming
                        ));
                    })
                    .reduce(DataBufferUtils.join())
                    .flatMap(dataBuffer ->
                        storageRepository.store(storagePath, dataBuffer)
                            .map(url -> FileUploadResult.builder()
                                .fileId(fileId)
                                .fileName(file.filename())
                                .fileSize(totalBytes.get())
                                .contentType(file.headers().getContentType().toString())
                                .url(url)
                                .uploadedAt(Instant.now())
                                .uploadedBy(userId)
                                .build())
                    )
                    .doOnSuccess(result -> {
                        eventPublisher.publishEvent(new FileUploadCompletedEvent(result));
                        log.info("File uploaded: {} ({} bytes)", result.getFileId(), result.getFileSize());
                    });
            });
    }

    public Flux<FileUploadResult> uploadMultipleFiles(Flux<FilePart> files, String userId) {
        return files.flatMap(file -> uploadFile(file, userId), 3); // Max 3 concurrent uploads
    }

    private Mono<FilePart> validateFile(FilePart file) {
        return Mono.just(file)
            .flatMap(f -> {
                String contentType = f.headers().getContentType() != null
                    ? f.headers().getContentType().toString()
                    : "application/octet-stream";

                if (!allowedTypes.contains(contentType)) {
                    return Mono.error(new InvalidFileTypeException(contentType, allowedTypes));
                }

                return Mono.just(f);
            });
    }

    private String getExtension(String filename) {
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1) : "";
    }

    private String generateStoragePath(String fileId, String extension) {
        LocalDate now = LocalDate.now();
        return String.format("%d/%02d/%02d/%s.%s",
            now.getYear(), now.getMonthValue(), now.getDayOfMonth(),
            fileId, extension);
    }
}

// controller/FileUploadController.java
@RestController
@RequestMapping("/api/v1/files")
@RequiredArgsConstructor
public class FileUploadController {

    private final FileUploadService fileUploadService;

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("isAuthenticated()")
    public Mono<ResponseEntity<FileUploadResult>> uploadFile(
            @RequestPart("file") FilePart file,
            @AuthenticationPrincipal UserDetails user) {

        return fileUploadService.uploadFile(file, user.getUsername())
            .map(result -> ResponseEntity.status(HttpStatus.CREATED).body(result));
    }

    @PostMapping(value = "/batch", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("isAuthenticated()")
    public Flux<FileUploadResult> uploadMultipleFiles(
            @RequestPart("files") Flux<FilePart> files,
            @AuthenticationPrincipal UserDetails user) {

        return fileUploadService.uploadMultipleFiles(files, user.getUsername());
    }

    @GetMapping(value = "/progress/{fileId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<FileUploadProgress>> getUploadProgress(
            @PathVariable String fileId) {

        return Flux.create(sink -> {
            // Listen to progress events
            ApplicationListener<FileUploadProgressEvent> listener = event -> {
                if (event.getFileId().equals(fileId)) {
                    sink.next(ServerSentEvent.<FileUploadProgress>builder()
                        .data(FileUploadProgress.from(event))
                        .build());
                }
            };

            // Register listener...
        });
    }
}

// dto/FileUploadResult.java
@Data
@Builder
public class FileUploadResult {
    private String fileId;
    private String fileName;
    private long fileSize;
    private String contentType;
    private String url;
    private Instant uploadedAt;
    private String uploadedBy;
}

// dto/FileUploadProgress.java
@Data
@Builder
public class FileUploadProgress {
    private String fileId;
    private long uploadedBytes;
    private long totalBytes;
    private int percentComplete;

    public static FileUploadProgress from(FileUploadProgressEvent event) {
        int percent = event.getTotalBytes() > 0
            ? (int) ((event.getUploadedBytes() * 100) / event.getTotalBytes())
            : -1;

        return FileUploadProgress.builder()
            .fileId(event.getFileId())
            .uploadedBytes(event.getUploadedBytes())
            .totalBytes(event.getTotalBytes())
            .percentComplete(percent)
            .build();
    }
}
```
