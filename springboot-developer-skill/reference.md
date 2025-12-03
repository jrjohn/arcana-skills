# Spring Boot Developer Skill - Technical Reference

## Table of Contents
1. [Project Structure](#project-structure)
2. [Clean Architecture Layers](#clean-architecture-layers)
3. [gRPC Service Development](#grpc-service-development)
4. [REST API Development](#rest-api-development)
5. [OSGi Plugin System](#osgi-plugin-system)
6. [Security Configuration](#security-configuration)
7. [Database & Caching](#database--caching)
8. [Resilience Patterns](#resilience-patterns)
9. [Server-Side Rendering](#server-side-rendering)
10. [Testing](#testing)
11. [Deployment Configurations](#deployment-configurations)

---

## Project Structure

```
arcana-cloud-springboot/
├── arcana-plugin-api/                # Plugin interface definitions
│   └── src/main/java/
│       └── com/arcana/plugin/
│           ├── ArcanaPlugin.java
│           ├── PluginContext.java
│           └── annotations/
├── arcana-plugin-runtime/            # OSGi runtime management
│   └── src/main/java/
│       └── com/arcana/runtime/
│           ├── PluginRuntimeManager.java
│           ├── PluginClassLoader.java
│           └── PluginEventBus.java
├── arcana-ssr-engine/                # Server-side rendering
│   └── src/main/java/
│       └── com/arcana/ssr/
│           ├── SSREngine.java
│           ├── GraalJSRuntime.java
│           └── RenderCache.java
├── arcana-web/                       # Frontend applications
│   ├── react-app/
│   └── angular-app/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/arcana/
│       │       ├── ArcanaApplication.java
│       │       ├── controller/       # REST/gRPC endpoints
│       │       │   ├── rest/
│       │       │   └── grpc/
│       │       ├── service/          # Business logic
│       │       │   ├── UserService.java
│       │       │   └── impl/
│       │       ├── repository/       # Data access
│       │       │   ├── UserRepository.java
│       │       │   └── cache/
│       │       ├── model/            # Domain models
│       │       │   ├── entity/
│       │       │   └── enums/
│       │       ├── dto/              # Data transfer objects
│       │       │   ├── request/
│       │       │   └── response/
│       │       ├── config/           # Configuration
│       │       │   ├── SecurityConfig.java
│       │       │   ├── GrpcConfig.java
│       │       │   └── CacheConfig.java
│       │       ├── security/         # Security components
│       │       │   ├── JwtTokenProvider.java
│       │       │   └── JwtAuthenticationFilter.java
│       │       └── exception/        # Exception handling
│       ├── proto/                    # Protobuf definitions
│       │   ├── user.proto
│       │   └── common.proto
│       └── resources/
│           ├── application.yml
│           ├── application-dev.yml
│           └── application-prod.yml
├── config/                           # External configuration
├── deployment/                       # Docker & K8s manifests
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── kubernetes/
│       ├── deployment.yaml
│       └── service.yaml
└── plugins/                          # Sample plugins
```

---

## Clean Architecture Layers

### Layer Responsibilities

| Layer | Responsibility | Components |
|-------|----------------|------------|
| **Controller** | HTTP/gRPC endpoints, request validation | REST Controllers, gRPC Services |
| **Service** | Business logic, orchestration, transactions | Service classes, Use cases |
| **Repository** | Data access, caching, persistence | JPA Repositories, Cache managers |

### Dependency Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    Controller Layer                          │
│  ┌───────────────────┐    ┌───────────────────┐            │
│  │  REST Controllers │    │   gRPC Services   │            │
│  └─────────┬─────────┘    └─────────┬─────────┘            │
│            │                        │                       │
│            └──────────┬─────────────┘                       │
│                       ↓                                     │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Business Services │ Transaction Management │ Events  │  │
│  └───────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ↓                                     │
├─────────────────────────────────────────────────────────────┤
│                    Repository Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │ JPA Repos    │ │ Cache Repos  │ │ External API Clients ││
│  └──────────────┘ └──────────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Interface Segregation Example
```java
// Service Interface (in service package)
public interface UserService {
    Optional<User> findById(String id);
    Page<User> findAll(Pageable pageable);
    User create(User user);
    Optional<User> update(String id, User user);
    void delete(String id);
}

// Service Implementation (in service.impl package)
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final UserCacheRepository cacheRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    public Optional<User> findById(String id) {
        // Try cache first
        return cacheRepository.findById(id)
            .or(() -> {
                Optional<User> user = userRepository.findById(id);
                user.ifPresent(cacheRepository::save);
                return user;
            });
    }

    @Override
    @Transactional
    public User create(User user) {
        User saved = userRepository.save(user);
        cacheRepository.save(saved);
        eventPublisher.publishEvent(new UserCreatedEvent(saved));
        return saved;
    }

    // ... other methods
}
```

---

## gRPC Service Development

### Protobuf Definition
```protobuf
// src/main/proto/user.proto
syntax = "proto3";

package com.arcana.grpc.user;

option java_multiple_files = true;
option java_package = "com.arcana.grpc.user";
option java_outer_classname = "UserProto";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

service UserService {
    // Unary RPCs
    rpc GetUser (GetUserRequest) returns (UserResponse);
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc UpdateUser (UpdateUserRequest) returns (UserResponse);
    rpc DeleteUser (DeleteUserRequest) returns (google.protobuf.Empty);

    // Server streaming
    rpc ListUsers (ListUsersRequest) returns (stream UserResponse);

    // Client streaming
    rpc BatchCreateUsers (stream CreateUserRequest) returns (BatchCreateResponse);

    // Bidirectional streaming
    rpc SyncUsers (stream UserSyncRequest) returns (stream UserSyncResponse);
}

message GetUserRequest {
    string id = 1;
}

message CreateUserRequest {
    string name = 1;
    string email = 2;
    string department = 3;
    repeated string roles = 4;
}

message UpdateUserRequest {
    string id = 1;
    optional string name = 2;
    optional string email = 3;
    optional string department = 4;
    repeated string roles = 5;
}

message DeleteUserRequest {
    string id = 1;
}

message ListUsersRequest {
    int32 page = 1;
    int32 size = 2;
    optional string sort_by = 3;
    optional string sort_order = 4;
    optional string filter = 5;
}

message UserResponse {
    string id = 1;
    string name = 2;
    string email = 3;
    string department = 4;
    repeated string roles = 5;
    google.protobuf.Timestamp created_at = 6;
    google.protobuf.Timestamp updated_at = 7;
}

message BatchCreateResponse {
    int32 success_count = 1;
    int32 failure_count = 2;
    repeated string created_ids = 3;
}

message UserSyncRequest {
    oneof action {
        UserResponse upsert = 1;
        string delete_id = 2;
    }
    int64 client_timestamp = 3;
}

message UserSyncResponse {
    string id = 1;
    SyncStatus status = 2;
    int64 server_timestamp = 3;
}

enum SyncStatus {
    SUCCESS = 0;
    CONFLICT = 1;
    ERROR = 2;
}
```

### gRPC Service Implementation
```java
@GrpcService
@RequiredArgsConstructor
@Slf4j
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final UserService userService;
    private final UserMapper mapper;

    @Override
    public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
        log.debug("gRPC getUser: {}", request.getId());

        userService.findById(request.getId())
            .map(mapper::toProto)
            .ifPresentOrElse(
                user -> {
                    responseObserver.onNext(user);
                    responseObserver.onCompleted();
                },
                () -> responseObserver.onError(
                    Status.NOT_FOUND
                        .withDescription("User not found: " + request.getId())
                        .asRuntimeException()
                )
            );
    }

    @Override
    public void createUser(CreateUserRequest request, StreamObserver<UserResponse> responseObserver) {
        try {
            User user = userService.create(mapper.fromProto(request));
            responseObserver.onNext(mapper.toProto(user));
            responseObserver.onCompleted();
        } catch (DuplicateEmailException e) {
            responseObserver.onError(
                Status.ALREADY_EXISTS
                    .withDescription(e.getMessage())
                    .asRuntimeException()
            );
        } catch (Exception e) {
            log.error("Error creating user", e);
            responseObserver.onError(
                Status.INTERNAL
                    .withDescription("Internal error")
                    .asRuntimeException()
            );
        }
    }

    @Override
    public void listUsers(ListUsersRequest request, StreamObserver<UserResponse> responseObserver) {
        // Server streaming - send users one by one
        Pageable pageable = PageRequest.of(
            request.getPage(),
            request.getSize(),
            Sort.by(request.getSortOrder().equals("desc") ? Sort.Direction.DESC : Sort.Direction.ASC,
                    request.getSortBy().isEmpty() ? "createdAt" : request.getSortBy())
        );

        Page<User> users = userService.findAll(pageable);

        users.getContent().stream()
            .map(mapper::toProto)
            .forEach(responseObserver::onNext);

        responseObserver.onCompleted();
    }

    @Override
    public StreamObserver<CreateUserRequest> batchCreateUsers(
            StreamObserver<BatchCreateResponse> responseObserver) {

        List<String> createdIds = new ArrayList<>();
        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger failureCount = new AtomicInteger(0);

        return new StreamObserver<>() {
            @Override
            public void onNext(CreateUserRequest request) {
                try {
                    User user = userService.create(mapper.fromProto(request));
                    createdIds.add(user.getId());
                    successCount.incrementAndGet();
                } catch (Exception e) {
                    log.warn("Failed to create user: {}", e.getMessage());
                    failureCount.incrementAndGet();
                }
            }

            @Override
            public void onError(Throwable t) {
                log.error("Client error in batchCreateUsers", t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(BatchCreateResponse.newBuilder()
                    .setSuccessCount(successCount.get())
                    .setFailureCount(failureCount.get())
                    .addAllCreatedIds(createdIds)
                    .build());
                responseObserver.onCompleted();
            }
        };
    }

    @Override
    public StreamObserver<UserSyncRequest> syncUsers(
            StreamObserver<UserSyncResponse> responseObserver) {

        return new StreamObserver<>() {
            @Override
            public void onNext(UserSyncRequest request) {
                UserSyncResponse response;

                try {
                    if (request.hasUpsert()) {
                        User user = mapper.fromProto(request.getUpsert());
                        userService.upsert(user);
                        response = UserSyncResponse.newBuilder()
                            .setId(user.getId())
                            .setStatus(SyncStatus.SUCCESS)
                            .setServerTimestamp(System.currentTimeMillis())
                            .build();
                    } else {
                        userService.delete(request.getDeleteId());
                        response = UserSyncResponse.newBuilder()
                            .setId(request.getDeleteId())
                            .setStatus(SyncStatus.SUCCESS)
                            .setServerTimestamp(System.currentTimeMillis())
                            .build();
                    }
                } catch (Exception e) {
                    response = UserSyncResponse.newBuilder()
                        .setId(request.hasUpsert() ? request.getUpsert().getId() : request.getDeleteId())
                        .setStatus(SyncStatus.ERROR)
                        .setServerTimestamp(System.currentTimeMillis())
                        .build();
                }

                responseObserver.onNext(response);
            }

            @Override
            public void onError(Throwable t) {
                log.error("Client error in syncUsers", t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onCompleted();
            }
        };
    }
}
```

### gRPC Configuration
```java
@Configuration
public class GrpcConfig {

    @Bean
    public GrpcServerInterceptor authInterceptor(JwtTokenProvider jwtTokenProvider) {
        return new ServerInterceptor() {
            @Override
            public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                    ServerCall<ReqT, RespT> call,
                    Metadata headers,
                    ServerCallHandler<ReqT, RespT> next) {

                String token = headers.get(Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER));

                if (token != null && token.startsWith("Bearer ")) {
                    token = token.substring(7);
                    if (jwtTokenProvider.validateToken(token)) {
                        Authentication auth = jwtTokenProvider.getAuthentication(token);
                        Context ctx = Context.current().withValue(
                            Context.key("auth"), auth
                        );
                        return Contexts.interceptCall(ctx, call, headers, next);
                    }
                }

                call.close(Status.UNAUTHENTICATED.withDescription("Invalid token"), new Metadata());
                return new ServerCall.Listener<>() {};
            }
        };
    }

    @Bean
    public GrpcServerInterceptor loggingInterceptor() {
        return new ServerInterceptor() {
            @Override
            public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                    ServerCall<ReqT, RespT> call,
                    Metadata headers,
                    ServerCallHandler<ReqT, RespT> next) {

                long startTime = System.currentTimeMillis();
                String methodName = call.getMethodDescriptor().getFullMethodName();

                ServerCall.Listener<ReqT> listener = next.startCall(call, headers);

                return new ForwardingServerCallListener.SimpleForwardingServerCallListener<>(listener) {
                    @Override
                    public void onComplete() {
                        long duration = System.currentTimeMillis() - startTime;
                        log.info("gRPC {} completed in {}ms", methodName, duration);
                        super.onComplete();
                    }
                };
            }
        };
    }
}
```

---

## REST API Development

### REST Controller
```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "Users", description = "User management API")
@Validated
public class UserController {

    private final UserService userService;
    private final UserMapper mapper;

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "User found"),
        @ApiResponse(responseCode = "404", description = "User not found")
    })
    public ResponseEntity<UserResponse> getUser(
            @PathVariable @NotBlank String id) {

        return userService.findById(id)
            .map(mapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    @Operation(summary = "List users with pagination")
    public ResponseEntity<PageResponse<UserResponse>> listUsers(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int size,
            @RequestParam(required = false) String sortBy,
            @RequestParam(defaultValue = "asc") String sortOrder,
            @RequestParam(required = false) String search) {

        Pageable pageable = PageRequest.of(page, size,
            Sort.by(sortOrder.equals("desc") ? Sort.Direction.DESC : Sort.Direction.ASC,
                    sortBy != null ? sortBy : "createdAt"));

        Page<User> result = search != null
            ? userService.search(search, pageable)
            : userService.findAll(pageable);

        return ResponseEntity.ok(PageResponse.of(result, mapper::toResponse));
    }

    @PostMapping
    @Operation(summary = "Create new user")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {

        User user = userService.create(mapper.fromRequest(request));
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(mapper.toResponse(user));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update user")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable @NotBlank String id,
            @Valid @RequestBody UpdateUserRequest request) {

        return userService.update(id, mapper.fromRequest(request))
            .map(mapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}")
    @Operation(summary = "Partially update user")
    public ResponseEntity<UserResponse> patchUser(
            @PathVariable @NotBlank String id,
            @Valid @RequestBody PatchUserRequest request) {

        return userService.patch(id, request)
            .map(mapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete user")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> deleteUser(
            @PathVariable @NotBlank String id) {

        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### DTOs and Validation
```java
// Request DTOs
@Data
@Builder
public class CreateUserRequest {

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    private String name;

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;

    @NotBlank(message = "Department is required")
    private String department;

    @NotEmpty(message = "At least one role is required")
    private List<@NotBlank String> roles;
}

@Data
@Builder
public class UpdateUserRequest {

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100)
    private String name;

    @NotBlank(message = "Email is required")
    @Email
    private String email;

    private String department;

    private List<String> roles;
}

@Data
public class PatchUserRequest {

    @Size(min = 2, max = 100)
    private String name;

    @Email
    private String email;

    private String department;

    private List<String> roles;
}

// Response DTO
@Data
@Builder
public class UserResponse {
    private String id;
    private String name;
    private String email;
    private String department;
    private List<String> roles;
    private Instant createdAt;
    private Instant updatedAt;

    public static UserResponse from(User user) {
        return UserResponse.builder()
            .id(user.getId())
            .name(user.getName())
            .email(user.getEmail())
            .department(user.getDepartment())
            .roles(user.getRoles())
            .createdAt(user.getCreatedAt())
            .updatedAt(user.getUpdatedAt())
            .build();
    }
}

// Page Response
@Data
@Builder
public class PageResponse<T> {
    private List<T> content;
    private int page;
    private int size;
    private long totalElements;
    private int totalPages;
    private boolean hasNext;
    private boolean hasPrevious;

    public static <T, E> PageResponse<T> of(Page<E> page, Function<E, T> mapper) {
        return PageResponse.<T>builder()
            .content(page.getContent().stream().map(mapper).toList())
            .page(page.getNumber())
            .size(page.getSize())
            .totalElements(page.getTotalElements())
            .totalPages(page.getTotalPages())
            .hasNext(page.hasNext())
            .hasPrevious(page.hasPrevious())
            .build();
    }
}
```

### Global Exception Handler
```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(EntityNotFoundException e) {
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(ErrorResponse.of(HttpStatus.NOT_FOUND, e.getMessage()));
    }

    @ExceptionHandler(DuplicateKeyException.class)
    public ResponseEntity<ErrorResponse> handleDuplicate(DuplicateKeyException e) {
        return ResponseEntity
            .status(HttpStatus.CONFLICT)
            .body(ErrorResponse.of(HttpStatus.CONFLICT, "Resource already exists"));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        Map<String, String> errors = e.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                fieldError -> fieldError.getDefaultMessage() != null
                    ? fieldError.getDefaultMessage()
                    : "Invalid value",
                (a, b) -> a
            ));

        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ErrorResponse.of(HttpStatus.BAD_REQUEST, "Validation failed", errors));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolation(ConstraintViolationException e) {
        Map<String, String> errors = e.getConstraintViolations().stream()
            .collect(Collectors.toMap(
                violation -> violation.getPropertyPath().toString(),
                ConstraintViolation::getMessage,
                (a, b) -> a
            ));

        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ErrorResponse.of(HttpStatus.BAD_REQUEST, "Validation failed", errors));
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDenied(AccessDeniedException e) {
        return ResponseEntity
            .status(HttpStatus.FORBIDDEN)
            .body(ErrorResponse.of(HttpStatus.FORBIDDEN, "Access denied"));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneral(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse.of(HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error"));
    }
}

@Data
@Builder
public class ErrorResponse {
    private int status;
    private String error;
    private String message;
    private Map<String, String> details;
    private Instant timestamp;

    public static ErrorResponse of(HttpStatus status, String message) {
        return ErrorResponse.builder()
            .status(status.value())
            .error(status.getReasonPhrase())
            .message(message)
            .timestamp(Instant.now())
            .build();
    }

    public static ErrorResponse of(HttpStatus status, String message, Map<String, String> details) {
        return ErrorResponse.builder()
            .status(status.value())
            .error(status.getReasonPhrase())
            .message(message)
            .details(details)
            .timestamp(Instant.now())
            .build();
    }
}
```

---

## OSGi Plugin System

### Plugin API
```java
// Core plugin interface
public interface ArcanaPlugin {
    String getKey();
    String getName();
    String getVersion();

    void onStart(PluginContext context);
    void onStop();

    default void onConfigChange(PluginConfig config) {}
    default HealthStatus healthCheck() { return HealthStatus.UP; }
}

// Plugin context for accessing core services
public interface PluginContext {
    // Service access
    <T> T getService(Class<T> serviceClass);
    <T> Optional<T> getOptionalService(Class<T> serviceClass);

    // Bean registration
    void registerBean(String name, Object bean);
    void unregisterBean(String name);

    // Endpoint registration
    void registerRestEndpoint(String basePath, Object controller);
    void registerGrpcService(BindableService service);

    // Event system
    void publishEvent(Object event);
    <T> void subscribe(Class<T> eventType, Consumer<T> handler);

    // Configuration
    PluginConfig getConfig();

    // Logging
    Logger getLogger();
}

// Plugin manifest annotation
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ArcanaPluginManifest {
    String key();
    String name();
    String version();
    String description() default "";
    String[] dependencies() default {};
    String[] requiredServices() default {};
}
```

### Plugin Runtime Manager
```java
@Service
@RequiredArgsConstructor
@Slf4j
public class PluginRuntimeManager implements ApplicationListener<ApplicationReadyEvent> {

    private final BundleContext bundleContext;
    private final ApplicationContext applicationContext;
    private final RedisTemplate<String, String> redisTemplate;
    private final PluginConfigRepository configRepository;

    private final Map<String, PluginInstance> plugins = new ConcurrentHashMap<>();
    private final PluginEventBus eventBus = new PluginEventBus();

    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        // Load enabled plugins from config
        configRepository.findAllEnabled()
            .forEach(this::loadPlugin);

        // Subscribe to cluster events
        redisTemplate.listenTo("plugin-events", this::handleClusterEvent);
    }

    public void installPlugin(Path jarPath) throws PluginException {
        // Verify JAR signature
        if (!verifySignature(jarPath)) {
            throw new SecurityException("Invalid plugin signature");
        }

        // Load manifest
        PluginManifest manifest = loadManifest(jarPath);

        // Check dependencies
        for (String dep : manifest.getDependencies()) {
            if (!plugins.containsKey(dep)) {
                throw new PluginException("Missing dependency: " + dep);
            }
        }

        try {
            // Install OSGi bundle
            String location = jarPath.toUri().toString();
            Bundle bundle = bundleContext.installBundle(location);

            // Create plugin instance
            PluginInstance instance = new PluginInstance(bundle, manifest);
            plugins.put(manifest.getKey(), instance);

            // Save to database
            configRepository.save(PluginConfig.builder()
                .key(manifest.getKey())
                .jarPath(jarPath.toString())
                .enabled(false)
                .build());

            log.info("Plugin installed: {}", manifest.getKey());

            // Sync to cluster
            syncToCluster(manifest.getKey(), PluginAction.INSTALLED);

        } catch (BundleException e) {
            throw new PluginException("Failed to install plugin", e);
        }
    }

    public void enablePlugin(String pluginKey) throws PluginException {
        PluginInstance instance = plugins.get(pluginKey);
        if (instance == null) {
            throw new PluginException("Plugin not found: " + pluginKey);
        }

        if (instance.isEnabled()) {
            return;
        }

        try {
            // Start OSGi bundle
            instance.getBundle().start();

            // Create plugin context
            PluginContextImpl context = new PluginContextImpl(
                applicationContext, eventBus, instance.getManifest().getKey()
            );

            // Initialize plugin
            ArcanaPlugin plugin = getPluginInstance(instance.getBundle());
            plugin.onStart(context);

            instance.setPlugin(plugin);
            instance.setContext(context);
            instance.setEnabled(true);

            // Update config
            configRepository.updateEnabled(pluginKey, true);

            log.info("Plugin enabled: {}", pluginKey);

            // Sync to cluster
            syncToCluster(pluginKey, PluginAction.ENABLED);

        } catch (Exception e) {
            throw new PluginException("Failed to enable plugin", e);
        }
    }

    public void disablePlugin(String pluginKey) throws PluginException {
        PluginInstance instance = plugins.get(pluginKey);
        if (instance == null || !instance.isEnabled()) {
            return;
        }

        try {
            // Stop plugin
            instance.getPlugin().onStop();

            // Cleanup context
            instance.getContext().cleanup();

            // Stop bundle
            instance.getBundle().stop();

            instance.setEnabled(false);

            // Update config
            configRepository.updateEnabled(pluginKey, false);

            log.info("Plugin disabled: {}", pluginKey);

            // Sync to cluster
            syncToCluster(pluginKey, PluginAction.DISABLED);

        } catch (Exception e) {
            throw new PluginException("Failed to disable plugin", e);
        }
    }

    public void uninstallPlugin(String pluginKey) throws PluginException {
        // First disable
        disablePlugin(pluginKey);

        PluginInstance instance = plugins.remove(pluginKey);
        if (instance != null) {
            try {
                instance.getBundle().uninstall();
            } catch (BundleException e) {
                throw new PluginException("Failed to uninstall plugin", e);
            }
        }

        // Remove config
        configRepository.delete(pluginKey);

        log.info("Plugin uninstalled: {}", pluginKey);

        // Sync to cluster
        syncToCluster(pluginKey, PluginAction.UNINSTALLED);
    }

    public List<PluginInfo> listPlugins() {
        return plugins.values().stream()
            .map(instance -> PluginInfo.builder()
                .key(instance.getManifest().getKey())
                .name(instance.getManifest().getName())
                .version(instance.getManifest().getVersion())
                .enabled(instance.isEnabled())
                .health(instance.isEnabled()
                    ? instance.getPlugin().healthCheck()
                    : HealthStatus.UNKNOWN)
                .build())
            .toList();
    }

    private void syncToCluster(String pluginKey, PluginAction action) {
        PluginEvent event = new PluginEvent(pluginKey, action, getInstanceId());
        redisTemplate.convertAndSend("plugin-events", event);
    }

    private void handleClusterEvent(PluginEvent event) {
        // Skip events from self
        if (event.getSourceInstance().equals(getInstanceId())) {
            return;
        }

        try {
            switch (event.getAction()) {
                case ENABLED -> enablePlugin(event.getPluginKey());
                case DISABLED -> disablePlugin(event.getPluginKey());
                // INSTALLED/UNINSTALLED require manual file sync
            }
        } catch (PluginException e) {
            log.error("Failed to handle cluster event", e);
        }
    }
}
```

---

## Security Configuration

### Spring Security Configuration
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtTokenProvider jwtTokenProvider;
    private final UserDetailsService userDetailsService;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                // Public endpoints
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/public/**").permitAll()
                .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                // Admin endpoints
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/v1/plugins/**").hasRole("ADMIN")
                // All other endpoints require authentication
                .anyRequest().authenticated()
            )
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(new JwtAuthenticationEntryPoint())
                .accessDeniedHandler(new JwtAccessDeniedHandler())
            )
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtTokenProvider, userDetailsService),
                UsernamePasswordAuthenticationFilter.class
            )
            .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(List.of("http://localhost:3000", "https://app.example.com"));
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", configuration);
        return source;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config)
            throws Exception {
        return config.getAuthenticationManager();
    }
}
```

### JWT Token Provider
```java
@Component
@RequiredArgsConstructor
@Slf4j
public class JwtTokenProvider {

    @Value("${jwt.secret}")
    private String secretKey;

    @Value("${jwt.access-token-expiration}")
    private long accessTokenExpiration;

    @Value("${jwt.refresh-token-expiration}")
    private long refreshTokenExpiration;

    private SecretKey key;

    @PostConstruct
    protected void init() {
        key = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
    }

    public TokenPair createTokenPair(UserDetails userDetails) {
        return TokenPair.builder()
            .accessToken(createAccessToken(userDetails))
            .refreshToken(createRefreshToken(userDetails))
            .expiresIn(accessTokenExpiration / 1000)
            .build();
    }

    public String createAccessToken(UserDetails userDetails) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + accessTokenExpiration);

        return Jwts.builder()
            .subject(userDetails.getUsername())
            .claim("roles", userDetails.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .toList())
            .claim("type", "access")
            .issuedAt(now)
            .expiration(validity)
            .signWith(key)
            .compact();
    }

    public String createRefreshToken(UserDetails userDetails) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + refreshTokenExpiration);

        return Jwts.builder()
            .subject(userDetails.getUsername())
            .claim("type", "refresh")
            .issuedAt(now)
            .expiration(validity)
            .signWith(key)
            .compact();
    }

    public Authentication getAuthentication(String token) {
        Claims claims = parseClaims(token);

        Collection<? extends GrantedAuthority> authorities =
            ((List<?>) claims.get("roles")).stream()
                .map(role -> new SimpleGrantedAuthority((String) role))
                .toList();

        User principal = new User(claims.getSubject(), "", authorities);
        return new UsernamePasswordAuthenticationToken(principal, token, authorities);
    }

    public String getUsername(String token) {
        return parseClaims(token).getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser().verifyWith(key).build().parseSignedClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            log.debug("Invalid JWT token: {}", e.getMessage());
            return false;
        }
    }

    public boolean isRefreshToken(String token) {
        return "refresh".equals(parseClaims(token).get("type"));
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
            .verifyWith(key)
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }
}

@Data
@Builder
public class TokenPair {
    private String accessToken;
    private String refreshToken;
    private long expiresIn;
}
```

---

## Database & Caching

### JPA Entity
```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_user_email", columnList = "email", unique = true),
    @Index(name = "idx_user_department", columnList = "department")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EntityListeners(AuditingEntityListener.class)
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false, length = 50)
    private String department;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "user_roles", joinColumns = @JoinColumn(name = "user_id"))
    @Column(name = "role")
    @Builder.Default
    private List<String> roles = new ArrayList<>();

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private Instant updatedAt;

    @Version
    private Long version;
}
```

### Repository
```java
public interface UserRepository extends JpaRepository<User, String>, JpaSpecificationExecutor<User> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.department = :department")
    Page<User> findByDepartment(@Param("department") String department, Pageable pageable);

    @Query("SELECT u FROM User u WHERE LOWER(u.name) LIKE LOWER(CONCAT('%', :search, '%')) " +
           "OR LOWER(u.email) LIKE LOWER(CONCAT('%', :search, '%'))")
    Page<User> search(@Param("search") String search, Pageable pageable);

    @Modifying
    @Query("UPDATE User u SET u.department = :newDept WHERE u.department = :oldDept")
    int updateDepartment(@Param("oldDept") String oldDept, @Param("newDept") String newDept);
}
```

### Cache Configuration
```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()));

        Map<String, RedisCacheConfiguration> cacheConfigs = Map.of(
            "users", defaultConfig.entryTtl(Duration.ofMinutes(15)),
            "user-lists", defaultConfig.entryTtl(Duration.ofMinutes(5)),
            "sessions", defaultConfig.entryTtl(Duration.ofHours(24))
        );

        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(defaultConfig)
            .withInitialCacheConfigurations(cacheConfigs)
            .build();
    }
}

// Service with caching
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;

    @Override
    @Cacheable(value = "users", key = "#id")
    public Optional<User> findById(String id) {
        return userRepository.findById(id);
    }

    @Override
    @Cacheable(value = "user-lists", key = "'all:' + #pageable.pageNumber + ':' + #pageable.pageSize")
    public Page<User> findAll(Pageable pageable) {
        return userRepository.findAll(pageable);
    }

    @Override
    @CachePut(value = "users", key = "#result.id")
    @CacheEvict(value = "user-lists", allEntries = true)
    @Transactional
    public User create(User user) {
        if (userRepository.existsByEmail(user.getEmail())) {
            throw new DuplicateEmailException(user.getEmail());
        }
        return userRepository.save(user);
    }

    @Override
    @CachePut(value = "users", key = "#id")
    @CacheEvict(value = "user-lists", allEntries = true)
    @Transactional
    public Optional<User> update(String id, User user) {
        return userRepository.findById(id)
            .map(existing -> {
                existing.setName(user.getName());
                existing.setEmail(user.getEmail());
                existing.setDepartment(user.getDepartment());
                existing.setRoles(user.getRoles());
                return userRepository.save(existing);
            });
    }

    @Override
    @Caching(evict = {
        @CacheEvict(value = "users", key = "#id"),
        @CacheEvict(value = "user-lists", allEntries = true)
    })
    @Transactional
    public void delete(String id) {
        userRepository.deleteById(id);
    }
}
```

---

## Resilience Patterns

### Circuit Breaker with Resilience4j
```java
@Service
@RequiredArgsConstructor
@Slf4j
public class ExternalApiService {

    private final WebClient webClient;
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    @CircuitBreaker(name = "externalApi", fallbackMethod = "fallbackGetData")
    @Retry(name = "externalApi")
    @Bulkhead(name = "externalApi")
    @RateLimiter(name = "externalApi")
    public Mono<ExternalData> getData(String id) {
        return webClient.get()
            .uri("/data/{id}", id)
            .retrieve()
            .bodyToMono(ExternalData.class)
            .timeout(Duration.ofSeconds(5))
            .doOnError(e -> log.warn("External API call failed: {}", e.getMessage()));
    }

    public Mono<ExternalData> fallbackGetData(String id, Throwable t) {
        log.warn("Circuit breaker fallback for id {}: {}", id, t.getMessage());
        return Mono.just(ExternalData.defaultValue());
    }

    // Programmatic circuit breaker
    public CompletableFuture<ExternalData> getDataWithCircuitBreaker(String id) {
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker("externalApi");

        return CompletableFuture.supplyAsync(() ->
            circuitBreaker.executeSupplier(() ->
                webClient.get()
                    .uri("/data/{id}", id)
                    .retrieve()
                    .bodyToMono(ExternalData.class)
                    .block(Duration.ofSeconds(5))
            )
        ).exceptionally(t -> ExternalData.defaultValue());
    }
}
```

### Configuration
```yaml
# application.yml
resilience4j:
  circuitbreaker:
    instances:
      externalApi:
        registerHealthIndicator: true
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
        waitDurationInOpenState: 10s
        failureRateThreshold: 50
        eventConsumerBufferSize: 10
        slowCallRateThreshold: 100
        slowCallDurationThreshold: 2s

  retry:
    instances:
      externalApi:
        maxAttempts: 3
        waitDuration: 500ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        retryExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException

  bulkhead:
    instances:
      externalApi:
        maxConcurrentCalls: 20
        maxWaitDuration: 500ms

  ratelimiter:
    instances:
      externalApi:
        limitForPeriod: 100
        limitRefreshPeriod: 1s
        timeoutDuration: 0s
```

---

## Testing

### Unit Testing with Mockito
```java
@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private UserCacheRepository cacheRepository;

    @Mock
    private ApplicationEventPublisher eventPublisher;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void findById_WhenCached_ReturnsCachedUser() {
        User cachedUser = User.builder().id("1").name("John").build();
        when(cacheRepository.findById("1")).thenReturn(Optional.of(cachedUser));

        Optional<User> result = userService.findById("1");

        assertThat(result).isPresent().contains(cachedUser);
        verify(userRepository, never()).findById(anyString());
    }

    @Test
    void findById_WhenNotCached_QueriesRepository() {
        User user = User.builder().id("1").name("John").build();
        when(cacheRepository.findById("1")).thenReturn(Optional.empty());
        when(userRepository.findById("1")).thenReturn(Optional.of(user));

        Optional<User> result = userService.findById("1");

        assertThat(result).isPresent().contains(user);
        verify(cacheRepository).save(user);
    }

    @Test
    void create_WithDuplicateEmail_ThrowsException() {
        User user = User.builder().email("john@example.com").build();
        when(userRepository.existsByEmail("john@example.com")).thenReturn(true);

        assertThatThrownBy(() -> userService.create(user))
            .isInstanceOf(DuplicateEmailException.class);
    }
}
```

### Integration Testing
```java
@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class UserControllerIntegrationTest {

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
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    @WithMockUser(roles = "USER")
    void createUser_WithValidData_ReturnsCreated() throws Exception {
        CreateUserRequest request = CreateUserRequest.builder()
            .name("John Doe")
            .email("john@example.com")
            .department("Engineering")
            .roles(List.of("ROLE_USER"))
            .build();

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("John Doe"))
            .andExpect(jsonPath("$.email").value("john@example.com"))
            .andExpect(jsonPath("$.id").isNotEmpty());
    }

    @Test
    @WithMockUser(roles = "USER")
    void getUser_WhenNotFound_Returns404() throws Exception {
        mockMvc.perform(get("/api/v1/users/nonexistent"))
            .andExpect(status().isNotFound());
    }
}
```

### gRPC Testing
```java
@SpringBootTest
@ExtendWith(GrpcCleanupExtension.class)
class UserGrpcServiceTest {

    @GrpcInProcessChannel
    private ManagedChannel channel;

    private UserServiceGrpc.UserServiceBlockingStub stub;

    @MockBean
    private UserService userService;

    @BeforeEach
    void setUp() {
        stub = UserServiceGrpc.newBlockingStub(channel);
    }

    @Test
    void getUser_WhenExists_ReturnsUser() {
        User user = User.builder()
            .id("1")
            .name("John")
            .email("john@example.com")
            .build();

        when(userService.findById("1")).thenReturn(Optional.of(user));

        UserResponse response = stub.getUser(
            GetUserRequest.newBuilder().setId("1").build()
        );

        assertThat(response.getId()).isEqualTo("1");
        assertThat(response.getName()).isEqualTo("John");
    }

    @Test
    void getUser_WhenNotFound_ThrowsNotFound() {
        when(userService.findById("1")).thenReturn(Optional.empty());

        assertThatThrownBy(() ->
            stub.getUser(GetUserRequest.newBuilder().setId("1").build())
        ).satisfies(t -> {
            StatusRuntimeException e = (StatusRuntimeException) t;
            assertThat(e.getStatus().getCode()).isEqualTo(Status.Code.NOT_FOUND);
        });
    }
}
```

---

## Deployment Configurations

### Docker Configuration
```dockerfile
# Dockerfile
FROM eclipse-temurin:25-jre-alpine AS builder

WORKDIR /app
COPY build/libs/*.jar app.jar

RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:25-jre-alpine

WORKDIR /app

# Copy layers in order of change frequency
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./

# Create non-root user
RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 8080 9090

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arcana-api
  labels:
    app: arcana-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arcana-api
  template:
    metadata:
      labels:
        app: arcana-api
    spec:
      containers:
        - name: arcana-api
          image: arcana/api:latest
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 9090
              name: grpc
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: "kubernetes"
            - name: JAVA_OPTS
              value: "-XX:+UseG1GC -XX:MaxRAMPercentage=75.0"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: arcana-api
spec:
  selector:
    app: arcana-api
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: grpc
      port: 9090
      targetPort: 9090
```
