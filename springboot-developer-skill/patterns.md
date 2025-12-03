# Spring Boot Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Service Layer Patterns](#service-layer-patterns)
3. [Data Access Patterns](#data-access-patterns)
4. [API Design Patterns](#api-design-patterns)
5. [Security Patterns](#security-patterns)
6. [Resilience Patterns](#resilience-patterns)
7. [Testing Patterns](#testing-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                         Controllers                              │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │   REST Controllers   │     │      gRPC Services          │   │
│  │   (HTTP/JSON)        │     │      (Protobuf)             │   │
│  └──────────┬──────────┘     └──────────────┬──────────────┘   │
│             │                                │                   │
│             └───────────────┬────────────────┘                   │
│                             ↓                                    │
├─────────────────────────────────────────────────────────────────┤
│                         Services                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Business Logic │ Use Cases │ Domain Services │ Validation  ││
│  │                                                              ││
│  │  @Service @Transactional                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                             │                                    │
│                             ↓                                    │
├─────────────────────────────────────────────────────────────────┤
│                       Repositories                               │
│  ┌──────────────┐ ┌───────────────┐ ┌────────────────────────┐ │
│  │ JPA Repos    │ │ Cache Repos   │ │ External API Clients   │ │
│  │ (MySQL)      │ │ (Redis)       │ │ (REST/gRPC)            │ │
│  └──────────────┘ └───────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation
```java
// Controller Layer - Only handles HTTP concerns
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;
    private final OrderMapper mapper;

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody CreateOrderRequest request) {
        // Delegate to service, no business logic here
        Order order = orderService.create(mapper.toDomain(request));
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(mapper.toResponse(order));
    }
}

// Service Layer - Business logic
@Service
@RequiredArgsConstructor
@Transactional
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;
    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    public Order create(Order order) {
        // Business validation
        validateOrder(order);

        // Check inventory
        for (OrderItem item : order.getItems()) {
            if (!inventoryService.isAvailable(item.getProductId(), item.getQuantity())) {
                throw new InsufficientInventoryException(item.getProductId());
            }
        }

        // Reserve inventory
        inventoryService.reserve(order);

        // Calculate totals
        order.calculateTotals();

        // Save order
        Order saved = orderRepository.save(order);

        // Publish event
        eventPublisher.publishEvent(new OrderCreatedEvent(saved));

        return saved;
    }

    private void validateOrder(Order order) {
        if (order.getItems().isEmpty()) {
            throw new InvalidOrderException("Order must have at least one item");
        }
        // More validations...
    }
}

// Repository Layer - Data access
@Repository
public interface OrderRepository extends JpaRepository<Order, String> {

    @Query("SELECT o FROM Order o WHERE o.userId = :userId ORDER BY o.createdAt DESC")
    Page<Order> findByUserId(@Param("userId") String userId, Pageable pageable);

    @Query("SELECT o FROM Order o WHERE o.status = :status AND o.createdAt < :before")
    List<Order> findPendingOrdersBefore(
        @Param("status") OrderStatus status,
        @Param("before") Instant before
    );
}
```

### Hexagonal Architecture (Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Core                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Domain Model                             ││
│  │  Entities │ Value Objects │ Domain Services │ Domain Events ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Use Cases                                ││
│  │  Application Services │ Command Handlers │ Query Handlers   ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      Ports (Interfaces)                      ││
│  │  ┌────────────────┐              ┌────────────────────────┐ ││
│  │  │ Inbound Ports  │              │    Outbound Ports      │ ││
│  │  │ (Use Cases)    │              │ (Repository Interfaces)│ ││
│  │  └────────────────┘              └────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼───────┐                       ┌───────▼───────┐
│   Adapters    │                       │   Adapters    │
│   (Inbound)   │                       │   (Outbound)  │
│               │                       │               │
│ REST API      │                       │ JPA Repos     │
│ gRPC API      │                       │ Redis Cache   │
│ CLI           │                       │ Kafka         │
│ Scheduled     │                       │ External APIs │
└───────────────┘                       └───────────────┘
```

```java
// Inbound Port (Use Case Interface)
public interface CreateOrderUseCase {
    OrderResult execute(CreateOrderCommand command);
}

// Outbound Port (Repository Interface)
public interface OrderRepositoryPort {
    Order save(Order order);
    Optional<Order> findById(String id);
    Page<Order> findByUser(String userId, Pageable pageable);
}

// Use Case Implementation
@Service
@RequiredArgsConstructor
public class CreateOrderUseCaseImpl implements CreateOrderUseCase {

    private final OrderRepositoryPort orderRepository;
    private final InventoryPort inventoryPort;
    private final EventPublisherPort eventPublisher;

    @Override
    @Transactional
    public OrderResult execute(CreateOrderCommand command) {
        // Domain logic
        Order order = Order.create(command.getUserId(), command.getItems());

        // Check inventory via port
        inventoryPort.reserveItems(order.getItems());

        // Save via port
        Order saved = orderRepository.save(order);

        // Publish event via port
        eventPublisher.publish(new OrderCreatedEvent(saved));

        return OrderResult.success(saved);
    }
}

// Outbound Adapter (JPA Implementation)
@Repository
@RequiredArgsConstructor
public class JpaOrderRepository implements OrderRepositoryPort {

    private final OrderJpaRepository jpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public Order save(Order order) {
        OrderEntity entity = mapper.toEntity(order);
        OrderEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    public Optional<Order> findById(String id) {
        return jpaRepository.findById(id).map(mapper::toDomain);
    }
}

// Inbound Adapter (REST Controller)
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderRestAdapter {

    private final CreateOrderUseCase createOrderUseCase;

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody CreateOrderRequest request) {

        CreateOrderCommand command = CreateOrderCommand.builder()
            .userId(request.getUserId())
            .items(request.getItems())
            .build();

        OrderResult result = createOrderUseCase.execute(command);

        return ResponseEntity.status(HttpStatus.CREATED)
            .body(OrderResponse.from(result.getOrder()));
    }
}
```

---

## Service Layer Patterns

### Strategy Pattern for Business Rules

```java
// Strategy Interface
public interface PricingStrategy {
    BigDecimal calculatePrice(Order order);
    boolean supports(CustomerType customerType);
}

// Concrete Strategies
@Component
public class RegularPricingStrategy implements PricingStrategy {

    @Override
    public BigDecimal calculatePrice(Order order) {
        return order.getItems().stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    @Override
    public boolean supports(CustomerType customerType) {
        return customerType == CustomerType.REGULAR;
    }
}

@Component
public class PremiumPricingStrategy implements PricingStrategy {

    private static final BigDecimal DISCOUNT = new BigDecimal("0.10"); // 10% discount

    @Override
    public BigDecimal calculatePrice(Order order) {
        BigDecimal basePrice = order.getItems().stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        return basePrice.multiply(BigDecimal.ONE.subtract(DISCOUNT));
    }

    @Override
    public boolean supports(CustomerType customerType) {
        return customerType == CustomerType.PREMIUM;
    }
}

@Component
public class WholesalePricingStrategy implements PricingStrategy {

    private static final int BULK_THRESHOLD = 100;
    private static final BigDecimal BULK_DISCOUNT = new BigDecimal("0.20");

    @Override
    public BigDecimal calculatePrice(Order order) {
        int totalQuantity = order.getItems().stream()
            .mapToInt(OrderItem::getQuantity)
            .sum();

        BigDecimal basePrice = order.getItems().stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        if (totalQuantity >= BULK_THRESHOLD) {
            return basePrice.multiply(BigDecimal.ONE.subtract(BULK_DISCOUNT));
        }

        return basePrice;
    }

    @Override
    public boolean supports(CustomerType customerType) {
        return customerType == CustomerType.WHOLESALE;
    }
}

// Strategy Selector
@Component
@RequiredArgsConstructor
public class PricingStrategySelector {

    private final List<PricingStrategy> strategies;

    public PricingStrategy select(CustomerType customerType) {
        return strategies.stream()
            .filter(strategy -> strategy.supports(customerType))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException(
                "No pricing strategy for customer type: " + customerType));
    }
}

// Usage in Service
@Service
@RequiredArgsConstructor
public class OrderPricingService {

    private final PricingStrategySelector strategySelector;
    private final CustomerService customerService;

    public BigDecimal calculateOrderPrice(Order order) {
        Customer customer = customerService.getById(order.getUserId());
        PricingStrategy strategy = strategySelector.select(customer.getType());
        return strategy.calculatePrice(order);
    }
}
```

### Template Method Pattern

```java
// Abstract template
public abstract class OrderProcessor {

    private final OrderRepository orderRepository;
    private final ApplicationEventPublisher eventPublisher;

    protected OrderProcessor(OrderRepository orderRepository,
                            ApplicationEventPublisher eventPublisher) {
        this.orderRepository = orderRepository;
        this.eventPublisher = eventPublisher;
    }

    // Template method
    @Transactional
    public final OrderResult process(Order order) {
        try {
            // Step 1: Validate
            validate(order);

            // Step 2: Pre-process (abstract - subclass implements)
            preProcess(order);

            // Step 3: Calculate
            calculateTotals(order);

            // Step 4: Process (abstract - subclass implements)
            doProcess(order);

            // Step 5: Save
            Order saved = orderRepository.save(order);

            // Step 6: Post-process (abstract - subclass implements)
            postProcess(saved);

            // Step 7: Publish event
            eventPublisher.publishEvent(createEvent(saved));

            return OrderResult.success(saved);

        } catch (Exception e) {
            return OrderResult.failure(e.getMessage());
        }
    }

    // Common implementation
    protected void validate(Order order) {
        if (order.getItems().isEmpty()) {
            throw new ValidationException("Order must have items");
        }
    }

    protected void calculateTotals(Order order) {
        BigDecimal total = order.getItems().stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        order.setTotal(total);
    }

    // Abstract methods for subclasses
    protected abstract void preProcess(Order order);
    protected abstract void doProcess(Order order);
    protected abstract void postProcess(Order order);
    protected abstract DomainEvent createEvent(Order order);
}

// Concrete implementation for online orders
@Component
public class OnlineOrderProcessor extends OrderProcessor {

    private final InventoryService inventoryService;
    private final PaymentService paymentService;

    public OnlineOrderProcessor(OrderRepository orderRepository,
                               ApplicationEventPublisher eventPublisher,
                               InventoryService inventoryService,
                               PaymentService paymentService) {
        super(orderRepository, eventPublisher);
        this.inventoryService = inventoryService;
        this.paymentService = paymentService;
    }

    @Override
    protected void preProcess(Order order) {
        // Reserve inventory
        inventoryService.reserve(order);
    }

    @Override
    protected void doProcess(Order order) {
        // Process payment
        PaymentResult result = paymentService.processPayment(order);
        order.setPaymentId(result.getPaymentId());
        order.setStatus(OrderStatus.PAID);
    }

    @Override
    protected void postProcess(Order order) {
        // Confirm inventory reservation
        inventoryService.confirmReservation(order.getId());
    }

    @Override
    protected DomainEvent createEvent(Order order) {
        return new OnlineOrderCompletedEvent(order);
    }
}

// Concrete implementation for in-store orders
@Component
public class InStoreOrderProcessor extends OrderProcessor {

    private final InventoryService inventoryService;

    public InStoreOrderProcessor(OrderRepository orderRepository,
                                ApplicationEventPublisher eventPublisher,
                                InventoryService inventoryService) {
        super(orderRepository, eventPublisher);
        this.inventoryService = inventoryService;
    }

    @Override
    protected void preProcess(Order order) {
        // Verify items are in stock at store
        inventoryService.verifyStoreStock(order.getStoreId(), order.getItems());
    }

    @Override
    protected void doProcess(Order order) {
        // Mark as ready for pickup
        order.setStatus(OrderStatus.READY_FOR_PICKUP);
    }

    @Override
    protected void postProcess(Order order) {
        // Deduct from store inventory
        inventoryService.deductStoreInventory(order.getStoreId(), order.getItems());
    }

    @Override
    protected DomainEvent createEvent(Order order) {
        return new InStoreOrderCompletedEvent(order);
    }
}
```

---

## Data Access Patterns

### Repository Pattern with Specification

```java
// Specification builder
public class OrderSpecifications {

    public static Specification<Order> hasUserId(String userId) {
        return (root, query, cb) -> cb.equal(root.get("userId"), userId);
    }

    public static Specification<Order> hasStatus(OrderStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }

    public static Specification<Order> createdBetween(Instant start, Instant end) {
        return (root, query, cb) -> cb.between(root.get("createdAt"), start, end);
    }

    public static Specification<Order> totalGreaterThan(BigDecimal amount) {
        return (root, query, cb) -> cb.greaterThan(root.get("total"), amount);
    }

    public static Specification<Order> containsProduct(String productId) {
        return (root, query, cb) -> {
            Join<Order, OrderItem> items = root.join("items");
            return cb.equal(items.get("productId"), productId);
        };
    }
}

// Usage
@Service
@RequiredArgsConstructor
public class OrderQueryService {

    private final OrderRepository orderRepository;

    public Page<Order> findOrders(OrderSearchCriteria criteria, Pageable pageable) {
        Specification<Order> spec = Specification.where(null);

        if (criteria.getUserId() != null) {
            spec = spec.and(OrderSpecifications.hasUserId(criteria.getUserId()));
        }

        if (criteria.getStatus() != null) {
            spec = spec.and(OrderSpecifications.hasStatus(criteria.getStatus()));
        }

        if (criteria.getStartDate() != null && criteria.getEndDate() != null) {
            spec = spec.and(OrderSpecifications.createdBetween(
                criteria.getStartDate(), criteria.getEndDate()));
        }

        if (criteria.getMinTotal() != null) {
            spec = spec.and(OrderSpecifications.totalGreaterThan(criteria.getMinTotal()));
        }

        return orderRepository.findAll(spec, pageable);
    }
}
```

### Cache-Aside Pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class CachedProductService {

    private final ProductRepository productRepository;
    private final RedisTemplate<String, Product> redisTemplate;

    private static final String CACHE_PREFIX = "product:";
    private static final Duration CACHE_TTL = Duration.ofMinutes(30);

    public Optional<Product> findById(String id) {
        String cacheKey = CACHE_PREFIX + id;

        // Try cache first
        Product cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            log.debug("Cache hit for product: {}", id);
            return Optional.of(cached);
        }

        log.debug("Cache miss for product: {}", id);

        // Load from database
        Optional<Product> product = productRepository.findById(id);

        // Populate cache
        product.ifPresent(p -> {
            redisTemplate.opsForValue().set(cacheKey, p, CACHE_TTL);
            log.debug("Cached product: {}", id);
        });

        return product;
    }

    @Transactional
    public Product save(Product product) {
        Product saved = productRepository.save(product);

        // Update cache
        String cacheKey = CACHE_PREFIX + saved.getId();
        redisTemplate.opsForValue().set(cacheKey, saved, CACHE_TTL);

        return saved;
    }

    @Transactional
    public void delete(String id) {
        productRepository.deleteById(id);

        // Invalidate cache
        String cacheKey = CACHE_PREFIX + id;
        redisTemplate.delete(cacheKey);
    }

    // Batch load with cache
    public List<Product> findByIds(List<String> ids) {
        List<String> cacheKeys = ids.stream()
            .map(id -> CACHE_PREFIX + id)
            .toList();

        // Multi-get from cache
        List<Product> cached = redisTemplate.opsForValue().multiGet(cacheKeys);

        // Find missing
        List<String> missingIds = new ArrayList<>();
        Map<String, Product> result = new HashMap<>();

        for (int i = 0; i < ids.size(); i++) {
            if (cached.get(i) != null) {
                result.put(ids.get(i), cached.get(i));
            } else {
                missingIds.add(ids.get(i));
            }
        }

        // Load missing from database
        if (!missingIds.isEmpty()) {
            List<Product> fromDb = productRepository.findAllById(missingIds);

            // Cache loaded products
            Map<String, Product> toCache = new HashMap<>();
            for (Product p : fromDb) {
                result.put(p.getId(), p);
                toCache.put(CACHE_PREFIX + p.getId(), p);
            }

            redisTemplate.opsForValue().multiSet(toCache);
            toCache.keySet().forEach(key ->
                redisTemplate.expire(key, CACHE_TTL));
        }

        // Return in original order
        return ids.stream()
            .map(result::get)
            .filter(Objects::nonNull)
            .toList();
    }
}
```

### Write-Behind (Write-Back) Pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class WriteBehindProductService {

    private final ProductRepository productRepository;
    private final RedisTemplate<String, Product> redisTemplate;
    private final RedisTemplate<String, String> stringRedisTemplate;

    private static final String CACHE_PREFIX = "product:";
    private static final String DIRTY_SET = "products:dirty";
    private static final Duration CACHE_TTL = Duration.ofHours(1);

    // Write to cache immediately, database later
    public Product save(Product product) {
        String cacheKey = CACHE_PREFIX + product.getId();

        // Update cache immediately
        redisTemplate.opsForValue().set(cacheKey, product, CACHE_TTL);

        // Mark as dirty for later persistence
        stringRedisTemplate.opsForSet().add(DIRTY_SET, product.getId());

        log.debug("Product {} cached and marked dirty", product.getId());

        return product;
    }

    // Scheduled job to flush dirty entries
    @Scheduled(fixedDelay = 5000) // Every 5 seconds
    @Transactional
    public void flushDirtyEntries() {
        Set<String> dirtyIds = stringRedisTemplate.opsForSet().members(DIRTY_SET);

        if (dirtyIds == null || dirtyIds.isEmpty()) {
            return;
        }

        log.info("Flushing {} dirty products to database", dirtyIds.size());

        for (String id : dirtyIds) {
            try {
                String cacheKey = CACHE_PREFIX + id;
                Product product = redisTemplate.opsForValue().get(cacheKey);

                if (product != null) {
                    productRepository.save(product);
                    stringRedisTemplate.opsForSet().remove(DIRTY_SET, id);
                    log.debug("Flushed product {} to database", id);
                }
            } catch (Exception e) {
                log.error("Failed to flush product {}: {}", id, e.getMessage());
            }
        }
    }

    // Read from cache, fallback to database
    public Optional<Product> findById(String id) {
        String cacheKey = CACHE_PREFIX + id;

        Product cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return Optional.of(cached);
        }

        Optional<Product> product = productRepository.findById(id);
        product.ifPresent(p ->
            redisTemplate.opsForValue().set(cacheKey, p, CACHE_TTL));

        return product;
    }
}
```

---

## API Design Patterns

### Dual-Protocol Pattern (gRPC + REST)

```java
// Shared service interface
public interface UserService {
    Optional<User> findById(String id);
    Page<User> findAll(Pageable pageable);
    User create(User user);
    Optional<User> update(String id, User user);
    void delete(String id);
}

// Single service implementation
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {
    // Implementation shared by both REST and gRPC
}

// REST Adapter
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserRestController {

    private final UserService userService;
    private final UserRestMapper mapper;

    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable String id) {
        return userService.findById(id)
            .map(mapper::toDto)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
        User user = userService.create(mapper.toDomain(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(mapper.toDto(user));
    }
}

// gRPC Adapter
@GrpcService
@RequiredArgsConstructor
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final UserService userService;
    private final UserGrpcMapper mapper;

    @Override
    public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
        userService.findById(request.getId())
            .map(mapper::toProto)
            .ifPresentOrElse(
                user -> {
                    responseObserver.onNext(user);
                    responseObserver.onCompleted();
                },
                () -> responseObserver.onError(
                    Status.NOT_FOUND.withDescription("User not found").asRuntimeException()
                )
            );
    }

    @Override
    public void createUser(CreateUserRequest request, StreamObserver<UserResponse> responseObserver) {
        try {
            User user = userService.create(mapper.toDomain(request));
            responseObserver.onNext(mapper.toProto(user));
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(Status.INTERNAL.withDescription(e.getMessage()).asRuntimeException());
        }
    }
}
```

### HATEOAS Pattern

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderHateoasController {

    private final OrderService orderService;

    @GetMapping("/{id}")
    public ResponseEntity<EntityModel<OrderDto>> getOrder(@PathVariable String id) {
        return orderService.findById(id)
            .map(order -> {
                OrderDto dto = OrderDto.from(order);

                EntityModel<OrderDto> model = EntityModel.of(dto,
                    linkTo(methodOn(OrderHateoasController.class).getOrder(id)).withSelfRel(),
                    linkTo(methodOn(OrderHateoasController.class).getOrderItems(id)).withRel("items"),
                    linkTo(methodOn(UserController.class).getUser(order.getUserId())).withRel("customer")
                );

                // Add action links based on state
                if (order.getStatus() == OrderStatus.PENDING) {
                    model.add(linkTo(methodOn(OrderHateoasController.class).cancelOrder(id))
                        .withRel("cancel"));
                    model.add(linkTo(methodOn(OrderHateoasController.class).payOrder(id, null))
                        .withRel("pay"));
                }

                if (order.getStatus() == OrderStatus.PAID) {
                    model.add(linkTo(methodOn(OrderHateoasController.class).shipOrder(id, null))
                        .withRel("ship"));
                }

                if (order.getStatus() == OrderStatus.SHIPPED) {
                    model.add(linkTo(methodOn(OrderHateoasController.class).trackOrder(id))
                        .withRel("track"));
                }

                return ResponseEntity.ok(model);
            })
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<CollectionModel<EntityModel<OrderDto>>> listOrders(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        Page<Order> orders = orderService.findAll(PageRequest.of(page, size));

        List<EntityModel<OrderDto>> orderModels = orders.getContent().stream()
            .map(order -> EntityModel.of(
                OrderDto.from(order),
                linkTo(methodOn(OrderHateoasController.class).getOrder(order.getId())).withSelfRel()
            ))
            .toList();

        CollectionModel<EntityModel<OrderDto>> collection = CollectionModel.of(
            orderModels,
            linkTo(methodOn(OrderHateoasController.class).listOrders(page, size)).withSelfRel()
        );

        if (orders.hasNext()) {
            collection.add(linkTo(methodOn(OrderHateoasController.class)
                .listOrders(page + 1, size)).withRel("next"));
        }

        if (orders.hasPrevious()) {
            collection.add(linkTo(methodOn(OrderHateoasController.class)
                .listOrders(page - 1, size)).withRel("prev"));
        }

        return ResponseEntity.ok(collection);
    }
}
```

---

## Security Patterns

### Role-Based Access Control (RBAC)

```java
// Permission enum
public enum Permission {
    USER_READ,
    USER_WRITE,
    USER_DELETE,
    ORDER_READ,
    ORDER_WRITE,
    ORDER_DELETE,
    ADMIN_ACCESS
}

// Role with permissions
public enum Role {
    USER(Permission.USER_READ, Permission.ORDER_READ, Permission.ORDER_WRITE),
    MODERATOR(Permission.USER_READ, Permission.USER_WRITE, Permission.ORDER_READ,
              Permission.ORDER_WRITE, Permission.ORDER_DELETE),
    ADMIN(Permission.values());

    private final Set<Permission> permissions;

    Role(Permission... permissions) {
        this.permissions = Set.of(permissions);
    }

    public Set<Permission> getPermissions() {
        return permissions;
    }

    public boolean hasPermission(Permission permission) {
        return permissions.contains(permission);
    }
}

// Custom security annotation
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@PreAuthorize("@permissionEvaluator.hasPermission(authentication, #root)")
public @interface RequirePermission {
    Permission value();
}

// Permission evaluator
@Component("permissionEvaluator")
public class CustomPermissionEvaluator {

    public boolean hasPermission(Authentication auth, MethodInvocation invocation) {
        RequirePermission annotation = invocation.getMethod()
            .getAnnotation(RequirePermission.class);

        if (annotation == null) {
            return true;
        }

        Permission required = annotation.value();

        return auth.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .filter(a -> a.startsWith("ROLE_"))
            .map(a -> Role.valueOf(a.substring(5)))
            .anyMatch(role -> role.hasPermission(required));
    }
}

// Usage in controller
@RestController
@RequestMapping("/api/v1/admin/users")
public class AdminUserController {

    @GetMapping
    @RequirePermission(Permission.USER_READ)
    public ResponseEntity<List<UserDto>> listUsers() {
        // ...
    }

    @DeleteMapping("/{id}")
    @RequirePermission(Permission.USER_DELETE)
    public ResponseEntity<Void> deleteUser(@PathVariable String id) {
        // ...
    }
}
```

### Resource-Based Access Control

```java
// Security expression for resource ownership
@Component("resourceSecurity")
public class ResourceSecurityExpressions {

    private final OrderRepository orderRepository;
    private final ProjectRepository projectRepository;

    public boolean isOrderOwner(Authentication auth, String orderId) {
        return orderRepository.findById(orderId)
            .map(order -> order.getUserId().equals(auth.getName()))
            .orElse(false);
    }

    public boolean isProjectMember(Authentication auth, String projectId) {
        return projectRepository.findById(projectId)
            .map(project -> project.getMembers().stream()
                .anyMatch(member -> member.getUserId().equals(auth.getName())))
            .orElse(false);
    }

    public boolean isProjectAdmin(Authentication auth, String projectId) {
        return projectRepository.findById(projectId)
            .map(project -> project.getMembers().stream()
                .anyMatch(member ->
                    member.getUserId().equals(auth.getName()) &&
                    member.getRole() == ProjectRole.ADMIN))
            .orElse(false);
    }
}

// Usage in controller
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @resourceSecurity.isOrderOwner(authentication, #id)")
    public ResponseEntity<OrderDto> getOrder(@PathVariable String id) {
        // ...
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @resourceSecurity.isOrderOwner(authentication, #id)")
    public ResponseEntity<Void> cancelOrder(@PathVariable String id) {
        // ...
    }
}

@RestController
@RequestMapping("/api/v1/projects/{projectId}")
public class ProjectController {

    @GetMapping
    @PreAuthorize("@resourceSecurity.isProjectMember(authentication, #projectId)")
    public ResponseEntity<ProjectDto> getProject(@PathVariable String projectId) {
        // ...
    }

    @DeleteMapping
    @PreAuthorize("@resourceSecurity.isProjectAdmin(authentication, #projectId)")
    public ResponseEntity<Void> deleteProject(@PathVariable String projectId) {
        // ...
    }
}
```

---

## Resilience Patterns

### Circuit Breaker Pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class PaymentGatewayService {

    private final WebClient webClient;
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    @CircuitBreaker(name = "paymentGateway", fallbackMethod = "paymentFallback")
    @Retry(name = "paymentGateway")
    @Bulkhead(name = "paymentGateway", type = Bulkhead.Type.THREADPOOL)
    public Mono<PaymentResult> processPayment(PaymentRequest request) {
        return webClient.post()
            .uri("/payments")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PaymentResult.class)
            .timeout(Duration.ofSeconds(5));
    }

    public Mono<PaymentResult> paymentFallback(PaymentRequest request, Throwable t) {
        log.warn("Payment gateway unavailable, queuing for retry: {}", t.getMessage());

        // Queue for later retry
        return Mono.just(PaymentResult.builder()
            .status(PaymentStatus.PENDING)
            .message("Payment queued for processing")
            .retryAfter(Duration.ofMinutes(5))
            .build());
    }

    // Manual circuit breaker control
    public CircuitBreaker.State getCircuitState() {
        return circuitBreakerRegistry.circuitBreaker("paymentGateway").getState();
    }

    public void resetCircuit() {
        circuitBreakerRegistry.circuitBreaker("paymentGateway").reset();
    }
}
```

### Retry with Backoff Pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class NotificationService {

    private final EmailClient emailClient;
    private final SmsClient smsClient;

    @Retryable(
        value = {TransientException.class, TimeoutException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2, maxDelay = 10000)
    )
    public void sendEmail(String to, String subject, String body) {
        log.info("Sending email to {}", to);
        emailClient.send(to, subject, body);
    }

    @Recover
    public void recoverEmail(Exception e, String to, String subject, String body) {
        log.error("Failed to send email to {} after retries: {}", to, e.getMessage());
        // Queue for manual review or alternative notification
        queueForManualReview(to, subject, body);
    }

    // Programmatic retry with exponential backoff
    public <T> T executeWithRetry(Supplier<T> operation, int maxRetries) {
        int attempt = 0;
        Exception lastException = null;

        while (attempt < maxRetries) {
            try {
                return operation.get();
            } catch (Exception e) {
                lastException = e;
                attempt++;

                if (attempt < maxRetries) {
                    long delay = (long) (1000 * Math.pow(2, attempt - 1));
                    delay = Math.min(delay, 30000); // Max 30 seconds

                    log.warn("Attempt {} failed, retrying in {}ms: {}",
                        attempt, delay, e.getMessage());

                    try {
                        Thread.sleep(delay);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Retry interrupted", ie);
                    }
                }
            }
        }

        throw new RuntimeException("All retry attempts failed", lastException);
    }
}
```

---

## Testing Patterns

### Test Fixtures Pattern

```java
public class UserFixtures {

    public static User.UserBuilder defaultUser() {
        return User.builder()
            .id(UUID.randomUUID().toString())
            .name("John Doe")
            .email("john.doe@example.com")
            .department("Engineering")
            .roles(List.of("ROLE_USER"))
            .createdAt(Instant.now())
            .updatedAt(Instant.now());
    }

    public static User adminUser() {
        return defaultUser()
            .name("Admin User")
            .email("admin@example.com")
            .roles(List.of("ROLE_ADMIN"))
            .build();
    }

    public static User premiumUser() {
        return defaultUser()
            .name("Premium User")
            .email("premium@example.com")
            .roles(List.of("ROLE_USER", "ROLE_PREMIUM"))
            .build();
    }

    public static List<User> userList(int count) {
        return IntStream.range(0, count)
            .mapToObj(i -> defaultUser()
                .name("User " + i)
                .email("user" + i + "@example.com")
                .build())
            .toList();
    }
}

public class OrderFixtures {

    public static Order.OrderBuilder defaultOrder() {
        return Order.builder()
            .id(UUID.randomUUID().toString())
            .userId(UUID.randomUUID().toString())
            .items(List.of(defaultOrderItem().build()))
            .status(OrderStatus.PENDING)
            .total(new BigDecimal("99.99"))
            .createdAt(Instant.now());
    }

    public static OrderItem.OrderItemBuilder defaultOrderItem() {
        return OrderItem.builder()
            .productId(UUID.randomUUID().toString())
            .productName("Test Product")
            .quantity(1)
            .unitPrice(new BigDecimal("99.99"));
    }

    public static Order paidOrder() {
        return defaultOrder()
            .status(OrderStatus.PAID)
            .paymentId(UUID.randomUUID().toString())
            .build();
    }

    public static Order shippedOrder() {
        return defaultOrder()
            .status(OrderStatus.SHIPPED)
            .paymentId(UUID.randomUUID().toString())
            .trackingNumber("TRACK123")
            .build();
    }
}
```

### Integration Test Base Class

```java
@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
@ActiveProfiles("test")
public abstract class IntegrationTestBase {

    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7")
        .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
        registry.add("spring.datasource.username", mysql::getUsername);
        registry.add("spring.datasource.password", mysql::getPassword);
        registry.add("spring.redis.host", redis::getHost);
        registry.add("spring.redis.port", redis::getFirstMappedPort);
    }

    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    protected ObjectMapper objectMapper;

    @Autowired
    protected JdbcTemplate jdbcTemplate;

    @BeforeEach
    void cleanDatabase() {
        // Clean tables in correct order for foreign keys
        jdbcTemplate.execute("SET FOREIGN_KEY_CHECKS = 0");
        jdbcTemplate.execute("TRUNCATE TABLE order_items");
        jdbcTemplate.execute("TRUNCATE TABLE orders");
        jdbcTemplate.execute("TRUNCATE TABLE users");
        jdbcTemplate.execute("SET FOREIGN_KEY_CHECKS = 1");
    }

    protected String toJson(Object obj) throws Exception {
        return objectMapper.writeValueAsString(obj);
    }

    protected <T> T fromJson(String json, Class<T> clazz) throws Exception {
        return objectMapper.readValue(json, clazz);
    }

    protected ResultActions performGet(String url) throws Exception {
        return mockMvc.perform(get(url)
            .contentType(MediaType.APPLICATION_JSON));
    }

    protected ResultActions performPost(String url, Object body) throws Exception {
        return mockMvc.perform(post(url)
            .contentType(MediaType.APPLICATION_JSON)
            .content(toJson(body)));
    }

    protected ResultActions performAuthenticatedGet(String url, String token) throws Exception {
        return mockMvc.perform(get(url)
            .header("Authorization", "Bearer " + token)
            .contentType(MediaType.APPLICATION_JSON));
    }
}

// Usage
class OrderControllerIntegrationTest extends IntegrationTestBase {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    private String userToken;
    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = userRepository.save(UserFixtures.defaultUser().build());
        userToken = jwtTokenProvider.createAccessToken(
            User.builder()
                .username(testUser.getEmail())
                .authorities(List.of(new SimpleGrantedAuthority("ROLE_USER")))
                .build()
        );
    }

    @Test
    void createOrder_WithValidData_ReturnsCreated() throws Exception {
        CreateOrderRequest request = CreateOrderRequest.builder()
            .items(List.of(OrderItemRequest.builder()
                .productId("prod-1")
                .quantity(2)
                .build()))
            .build();

        performAuthenticatedPost("/api/v1/orders", request, userToken)
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").isNotEmpty())
            .andExpect(jsonPath("$.status").value("PENDING"));
    }
}
```
