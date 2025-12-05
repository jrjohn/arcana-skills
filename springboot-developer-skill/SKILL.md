---
name: springboot-developer-skill
description: Spring Boot development guide based on Arcana Cloud SpringBoot enterprise architecture. Provides comprehensive support for Clean Architecture, dual-protocol (gRPC/REST), OSGi Plugin System, Server-Side Rendering, and enterprise security. Suitable for Spring Boot project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Spring Boot Developer Skill

Professional Spring Boot development skill based on [Arcana Cloud SpringBoot](https://github.com/jrjohn/arcana-cloud-springboot) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│            REST/gRPC Endpoints + Auth               │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│          Business Logic + Orchestration             │
├─────────────────────────────────────────────────────┤
│                  Repository Layer                    │
│           Data Access + Caching + Sync              │
└─────────────────────────────────────────────────────┘
```

### Deployment Modes
1. **Monolithic**: All layers colocated (development)
2. **Layered + HTTP**: Separate containers with HTTP
3. **Layered + gRPC**: Separate containers with gRPC (2.5x faster)
4. **Kubernetes + HTTP**: K8s deployment with HTTP
5. **Kubernetes + gRPC**: K8s deployment with TLS-secured gRPC

## Instructions

When handling Spring Boot development tasks, follow these principles:

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested Gradle settings and library versions. **NEVER reconfigure project structure or modify build.gradle / gradle.properties**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-cloud-springboot.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-cloud-springboot template"
```

**Step 3**: Modify project name and package
Only modify the following required items:
- `rootProject.name` in `settings.gradle`
- `group` and `archivesBaseName` in `build.gradle`
- Rename package directory structure under `src/main/java/`
- Update application name in `application.yml`

**Step 4**: Clean up example code
The cloned project contains example API (e.g., Arcana User Management). Clean up and replace with new project business logic:

**Core architecture files to KEEP** (do not delete):
- `src/main/java/.../config/` - Common configuration (Security, gRPC, Database)
- `src/main/java/.../common/` - Common utilities
- `src/main/java/.../exception/` - Exception handling
- `arcana-plugin-api/` - Plugin interface definitions
- `arcana-plugin-runtime/` - OSGi runtime
- `deployment/` - Docker & K8s manifests

**Example files to REPLACE**:
- `src/main/java/.../controller/` - Delete example Controller, create new REST/gRPC endpoints
- `src/main/java/.../service/` - Delete example Service, create new business logic
- `src/main/java/.../repository/` - Delete example Repository, create new data access
- `src/main/java/.../model/` - Delete example Models, create new Domain Models
- `src/main/java/.../dto/` - Delete example DTOs, create new DTOs
- `src/main/proto/` - Modify gRPC proto definitions

**Step 5**: Verify build
```bash
./gradlew clean build
```

### ❌ Prohibited Actions
- **DO NOT** create new Spring Boot project from scratch (Spring Initializr)
- **DO NOT** modify version numbers in `gradle.properties` or `libs.versions.toml`
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify Gradle wrapper version
- **DO NOT** reconfigure gRPC, OSGi, Spring Security, or other library settings

### ✅ Allowed Modifications
- Add business-related Java code (following existing architecture)
- Add Controller, Service, Repository
- Add Domain Models, DTOs
- Modify settings in `application.yml`
- Add gRPC proto files (and recompile)
- Develop new Plugins

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

⚠️ **CRITICAL**: All development MUST follow this TDD workflow. Every SRS/SDD requirement must have corresponding tests BEFORE implementation.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests               │
│  Step 5: Mock APIs → Use mock data for unfinished dependencies  │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Analyze Spec Documents (SRS & SDD)
Before writing any code, extract ALL requirements from both SRS and SDD:
```java
/**
 * Requirements extracted from specification documents:
 *
 * SRS (Software Requirements Specification):
 * - SRS-001: User must be able to login with email/password
 * - SRS-002: System must return JWT token upon successful login
 * - SRS-003: API must support both REST and gRPC protocols
 *
 * SDD (Software Design Document):
 * - SDD-001: Authentication uses JWT with RS256 algorithm
 * - SDD-002: Token expiration set to 24 hours
 * - SDD-003: Password hashed using BCrypt with strength 12
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```java
// src/test/java/.../service/AuthServiceTest.java
@SpringBootTest
@Transactional
class AuthServiceTest {

    @Autowired
    private AuthService authService;

    @MockBean
    private UserRepository userRepository;

    @MockBean
    private PasswordEncoder passwordEncoder;

    // SRS-001: User must be able to login with email/password
    @Test
    void login_WithValidCredentials_ShouldSucceed() {
        // Given
        User mockUser = new User("1", "test@test.com", "hashedPassword", "Test User");
        when(userRepository.findByEmail("test@test.com")).thenReturn(Optional.of(mockUser));
        when(passwordEncoder.matches("password123", "hashedPassword")).thenReturn(true);

        // When
        AuthResponse response = authService.login("test@test.com", "password123");

        // Then
        assertNotNull(response);
        assertNotNull(response.getAccessToken());
    }

    // SRS-001: Invalid credentials should throw exception
    @Test
    void login_WithInvalidCredentials_ShouldThrowException() {
        // Given
        when(userRepository.findByEmail(any())).thenReturn(Optional.empty());

        // When/Then
        assertThrows(AuthenticationException.class, () -> {
            authService.login("invalid@test.com", "wrong");
        });
    }

    // SDD-001: JWT must use RS256 algorithm
    @Test
    void login_ShouldReturnJwtWithRS256Algorithm() {
        // Given
        User mockUser = new User("1", "test@test.com", "hashedPassword", "Test User");
        when(userRepository.findByEmail(any())).thenReturn(Optional.of(mockUser));
        when(passwordEncoder.matches(any(), any())).thenReturn(true);

        // When
        AuthResponse response = authService.login("test@test.com", "password123");

        // Then
        String token = response.getAccessToken();
        DecodedJWT jwt = JWT.decode(token);
        assertEquals("RS256", jwt.getAlgorithm());
    }

    // SDD-002: Token expiration must be 24 hours
    @Test
    void login_TokenShouldExpireIn24Hours() {
        // Given
        User mockUser = new User("1", "test@test.com", "hashedPassword", "Test User");
        when(userRepository.findByEmail(any())).thenReturn(Optional.of(mockUser));
        when(passwordEncoder.matches(any(), any())).thenReturn(true);

        // When
        AuthResponse response = authService.login("test@test.com", "password123");

        // Then
        DecodedJWT jwt = JWT.decode(response.getAccessToken());
        long expirationHours = ChronoUnit.HOURS.between(
            jwt.getIssuedAt().toInstant(),
            jwt.getExpiresAt().toInstant()
        );
        assertEquals(24, expirationHours);
    }
}
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL SRS and SDD items have tests:
```java
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * SRS Requirements:
 * [x] SRS-001: Login with email/password - AuthServiceTest
 * [x] SRS-002: Return JWT token - AuthServiceTest
 * [x] SRS-003: Support REST and gRPC - AuthControllerTest, AuthGrpcServiceTest
 * [x] SRS-004: User registration - UserServiceTest
 * [ ] SRS-005: Password reset - TODO
 *
 * SDD Design Requirements:
 * [x] SDD-001: JWT RS256 algorithm - AuthServiceTest
 * [x] SDD-002: 24-hour token expiration - AuthServiceTest
 * [x] SDD-003: BCrypt password hashing - UserServiceTest
 * [ ] SDD-004: Rate limiting - TODO
 */
```

#### Step 4: Mock External Dependencies
For external services or databases not yet available, implement mock classes:
```java
// src/test/java/.../mock/MockUserRepository.java
@Repository
@Profile("test")
public class MockUserRepository implements UserRepository {

    private static final List<User> MOCK_USERS = List.of(
        new User("1", "test@test.com", "$2a$12$...", "Test User"),
        new User("2", "demo@demo.com", "$2a$12$...", "Demo User")
    );

    @Override
    public Optional<User> findByEmail(String email) {
        return MOCK_USERS.stream()
            .filter(u -> u.getEmail().equals(email))
            .findFirst();
    }

    @Override
    public Optional<User> findById(String id) {
        return MOCK_USERS.stream()
            .filter(u -> u.getId().equals(id))
            .findFirst();
    }

    @Override
    public User save(User user) {
        // Simulate save operation
        return user;
    }
}

// src/main/resources/application-test.yml
spring:
  profiles: test
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
```

#### Step 5: Run All Tests Before Completion
```bash
# Run all unit tests
./gradlew test

# Run all tests with coverage report
./gradlew test jacocoTestReport

# Run integration tests
./gradlew integrationTest

# Run specific test class
./gradlew test --tests "com.example.service.AuthServiceTest"

# Verify all tests pass
./gradlew check
```

#### Test Directory Structure
```
src/
├── main/java/...                    # Production code
├── test/java/...                    # Unit & Integration tests
│   ├── controller/
│   │   ├── AuthControllerTest.java
│   │   └── UserControllerTest.java
│   ├── service/
│   │   ├── AuthServiceTest.java
│   │   └── UserServiceTest.java
│   ├── repository/
│   │   └── UserRepositoryTest.java
│   ├── grpc/
│   │   └── AuthGrpcServiceTest.java
│   └── mock/
│       ├── MockUserRepository.java
│       └── MockExternalApiClient.java
└── testFixtures/java/...            # Shared test utilities
    └── TestDataFactory.java
```

### 2. Project Structure
```
arcana-cloud-springboot/
├── arcana-plugin-api/        # Plugin interface definitions
├── arcana-plugin-runtime/    # OSGi runtime management
├── arcana-ssr-engine/        # Server-side rendering
├── arcana-web/               # React/Angular apps
├── src/
│   └── main/
│       ├── java/
│       │   └── com/arcana/
│       │       ├── controller/    # REST/gRPC endpoints
│       │       ├── service/       # Business logic
│       │       ├── repository/    # Data access
│       │       ├── model/         # Domain models
│       │       ├── dto/           # Data transfer objects
│       │       ├── config/        # Configuration
│       │       └── security/      # Security config
│       └── resources/
├── config/                   # External configuration
├── deployment/               # Docker & K8s manifests
└── plugins/                  # Sample plugins
```

### 2. Dual-Protocol Support (gRPC + REST)

#### gRPC Service Definition
```protobuf
syntax = "proto3";

package com.arcana.user;

option java_multiple_files = true;
option java_package = "com.arcana.grpc.user";

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

message UserResponse {
  string id = 1;
  string name = 2;
  string email = 3;
  int64 created_at = 4;
}

message ListUsersRequest {
  int32 page = 1;
  int32 size = 2;
}

message ListUsersResponse {
  repeated UserResponse users = 1;
  int32 total = 2;
}
```

#### gRPC Service Implementation
```java
@GrpcService
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final UserService userService;

    public UserGrpcService(UserService userService) {
        this.userService = userService;
    }

    @Override
    public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
        try {
            User user = userService.findById(request.getId())
                .orElseThrow(() -> new UserNotFoundException(request.getId()));

            responseObserver.onNext(toProto(user));
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(
                Status.NOT_FOUND
                    .withDescription(e.getMessage())
                    .asRuntimeException()
            );
        }
    }

    @Override
    public void listUsers(ListUsersRequest request, StreamObserver<ListUsersResponse> responseObserver) {
        Page<User> page = userService.findAll(
            PageRequest.of(request.getPage(), request.getSize())
        );

        ListUsersResponse response = ListUsersResponse.newBuilder()
            .addAllUsers(page.getContent().stream().map(this::toProto).toList())
            .setTotal((int) page.getTotalElements())
            .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    private UserResponse toProto(User user) {
        return UserResponse.newBuilder()
            .setId(user.getId())
            .setName(user.getName())
            .setEmail(user.getEmail())
            .setCreatedAt(user.getCreatedAt().toEpochMilli())
            .build();
    }
}
```

#### REST Controller
```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable String id) {
        return userService.findById(id)
            .map(UserDto::from)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<PageResponse<UserDto>> listUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<User> result = userService.findAll(PageRequest.of(page, size));
        return ResponseEntity.ok(PageResponse.from(result, UserDto::from));
    }

    @PostMapping
    public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
        User user = userService.create(request.toEntity());
        return ResponseEntity.status(HttpStatus.CREATED).body(UserDto.from(user));
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserDto> updateUser(
            @PathVariable String id,
            @Valid @RequestBody UpdateUserRequest request) {
        return userService.update(id, request.toEntity())
            .map(UserDto::from)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable String id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 3. OSGi Plugin System

#### Plugin Interface
```java
public interface ArcanaPlugin {
    String getKey();
    String getName();
    String getVersion();
    void onStart(PluginContext context);
    void onStop();
}

public interface PluginContext {
    <T> T getService(Class<T> serviceClass);
    void registerBean(String name, Object bean);
    void registerEndpoint(String path, Object controller);
    void registerEventListener(String event, EventListener listener);
}
```

#### Plugin Implementation
```java
@ArcanaPluginManifest(
    key = "user-analytics",
    name = "User Analytics Plugin",
    version = "1.0.0",
    description = "Provides user analytics and reporting"
)
public class UserAnalyticsPlugin implements ArcanaPlugin {

    private PluginContext context;
    private AnalyticsService analyticsService;

    @Override
    public String getKey() { return "user-analytics"; }

    @Override
    public String getName() { return "User Analytics Plugin"; }

    @Override
    public String getVersion() { return "1.0.0"; }

    @Override
    public void onStart(PluginContext context) {
        this.context = context;

        // Get core services
        UserService userService = context.getService(UserService.class);

        // Create plugin services
        this.analyticsService = new AnalyticsService(userService);
        context.registerBean("analyticsService", analyticsService);

        // Register REST endpoint
        context.registerEndpoint("/api/v1/analytics", new AnalyticsController(analyticsService));

        // Register event listener
        context.registerEventListener("user.created", event -> {
            analyticsService.trackUserCreated((User) event.getData());
        });
    }

    @Override
    public void onStop() {
        // Cleanup resources
    }
}
```

#### Plugin Runtime Manager
```java
@Service
@RequiredArgsConstructor
public class PluginRuntimeManager {

    private final BundleContext bundleContext;
    private final ApplicationContext applicationContext;
    private final RedisTemplate<String, String> redisTemplate;

    private final Map<String, Bundle> installedPlugins = new ConcurrentHashMap<>();

    public void installPlugin(Path jarPath) throws BundleException {
        // Verify JAR signature
        if (!verifySignature(jarPath)) {
            throw new SecurityException("Invalid plugin signature");
        }

        String location = jarPath.toUri().toString();
        Bundle bundle = bundleContext.installBundle(location);

        // Start bundle
        bundle.start();

        String pluginKey = getPluginKey(bundle);
        installedPlugins.put(pluginKey, bundle);

        // Sync to cluster via Redis
        syncToCluster(pluginKey, "INSTALLED");
    }

    public void enablePlugin(String pluginKey) throws BundleException {
        Bundle bundle = installedPlugins.get(pluginKey);
        if (bundle != null && bundle.getState() != Bundle.ACTIVE) {
            bundle.start();
            syncToCluster(pluginKey, "ENABLED");
        }
    }

    public void disablePlugin(String pluginKey) throws BundleException {
        Bundle bundle = installedPlugins.get(pluginKey);
        if (bundle != null && bundle.getState() == Bundle.ACTIVE) {
            bundle.stop();
            syncToCluster(pluginKey, "DISABLED");
        }
    }

    public void uninstallPlugin(String pluginKey) throws BundleException {
        Bundle bundle = installedPlugins.remove(pluginKey);
        if (bundle != null) {
            bundle.uninstall();
            syncToCluster(pluginKey, "UNINSTALLED");
        }
    }

    private void syncToCluster(String pluginKey, String status) {
        redisTemplate.convertAndSend("plugin-events",
            String.format("{\"key\":\"%s\",\"status\":\"%s\"}", pluginKey, status));
    }
}
```

### 4. Security Configuration

```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtTokenProvider jwtTokenProvider;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/public/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtTokenProvider),
                UsernamePasswordAuthenticationFilter.class
            )
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}

@Component
@RequiredArgsConstructor
public class JwtTokenProvider {

    @Value("${jwt.secret}")
    private String secretKey;

    @Value("${jwt.expiration}")
    private long validityInMilliseconds;

    public String createToken(String username, List<String> roles) {
        Claims claims = Jwts.claims().setSubject(username);
        claims.put("roles", roles);

        Date now = new Date();
        Date validity = new Date(now.getTime() + validityInMilliseconds);

        return Jwts.builder()
            .setClaims(claims)
            .setIssuedAt(now)
            .setExpiration(validity)
            .signWith(SignatureAlgorithm.HS256, secretKey)
            .compact();
    }

    public Authentication getAuthentication(String token) {
        UserDetails userDetails = loadUserByUsername(getUsername(token));
        return new UsernamePasswordAuthenticationToken(
            userDetails, "", userDetails.getAuthorities());
    }

    public String getUsername(String token) {
        return Jwts.parser()
            .setSigningKey(secretKey)
            .parseClaimsJws(token)
            .getBody()
            .getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(secretKey).parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
}
```

### 5. Resilience with Circuit Breaker

```java
@Service
@RequiredArgsConstructor
public class ExternalApiService {

    private final RestTemplate restTemplate;
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    @CircuitBreaker(name = "externalApi", fallbackMethod = "fallback")
    @Retry(name = "externalApi")
    @RateLimiter(name = "externalApi")
    public ExternalData fetchData(String id) {
        return restTemplate.getForObject(
            "https://external-api.com/data/{id}",
            ExternalData.class,
            id
        );
    }

    private ExternalData fallback(String id, Exception e) {
        // Return cached data or default value
        return ExternalData.defaultValue();
    }
}

// application.yml
/*
resilience4j:
  circuitbreaker:
    instances:
      externalApi:
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        failureRateThreshold: 50
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 3
  retry:
    instances:
      externalApi:
        maxAttempts: 3
        waitDuration: 500ms
  ratelimiter:
    instances:
      externalApi:
        limitForPeriod: 100
        limitRefreshPeriod: 1s
*/
```

### 6. Server-Side Rendering

```java
@Service
@RequiredArgsConstructor
public class SSREngine {

    private final GraalJSRuntime jsRuntime;
    private final CacheManager<String, String> renderCache;

    public String renderReact(String component, Map<String, Object> props) {
        String cacheKey = component + ":" + props.hashCode();

        return renderCache.get(cacheKey, () -> {
            String script = String.format(
                "ReactDOMServer.renderToString(React.createElement(%s, %s))",
                component,
                new ObjectMapper().writeValueAsString(props)
            );

            String html = jsRuntime.execute(script);

            // Inject hydration script
            return html + generateHydrationScript(component, props);
        });
    }

    private String generateHydrationScript(String component, Map<String, Object> props) {
        return String.format(
            "<script>ReactDOM.hydrate(React.createElement(%s, %s), document.getElementById('root'))</script>",
            component,
            new ObjectMapper().writeValueAsString(props)
        );
    }
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] Dual-protocol support (gRPC + REST)
- [ ] Plugin system uses OSGi properly
- [ ] Security configuration complete (JWT, RBAC)
- [ ] Circuit breaker configured for external calls

### Performance Checks
- [ ] gRPC for internal communication (2.5x faster)
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Database queries optimized

### Security Checks
- [ ] JWT token validation
- [ ] Role-based access control
- [ ] Input validation complete
- [ ] TLS/mTLS for gRPC in production
- [ ] Plugin signature verification

## Common Issues

### gRPC Connection Issues
1. Check TLS certificate configuration
2. Verify service discovery settings
3. Ensure proper channel management

### Plugin Loading Issues
1. Verify OSGi bundle manifest
2. Check dependency resolution
3. Review Spring-OSGi bridge configuration

### Performance Issues
1. Enable gRPC for internal calls
2. Configure connection pooling
3. Review circuit breaker settings

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Java | 25+ (OpenJDK) |
| Spring Boot | 4.0+ |
| gRPC | 1.60+ |
| Apache Felix | 7.0+ |
| MySQL | 8.0+ |
| Redis | 7.0+ |
| Gradle | 9.2+ |
