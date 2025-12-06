---
name: springboot-developer-skill
description: Spring Boot development guide based on Arcana Cloud SpringBoot enterprise architecture. Provides comprehensive support for Clean Architecture, dual-protocol (gRPC/REST), OSGi Plugin System, Server-Side Rendering, and enterprise security. Suitable for Spring Boot project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Spring Boot Developer Skill

Professional Spring Boot development skill based on [Arcana Cloud SpringBoot](https://github.com/jrjohn/arcana-cloud-springboot) enterprise architecture.

---

## Quick Reference Card

### New REST Endpoint Checklist:
```
1. Add method to Controller with @GetMapping/@PostMapping
2. Add method signature to Service interface
3. Implement method in ServiceImpl with @Override
4. Add Repository method if data access needed
5. Add @Valid for RequestBody validation
6. Add @PreAuthorize for security if needed
7. Verify mock data returns non-empty values
```

### New gRPC Service Checklist:
```
1. Define service in src/main/proto/*.proto
2. Run ./gradlew generateProto
3. Create GrpcService class extending generated ImplBase
4. Add @GrpcService annotation
5. Implement ALL rpc methods (count must match)
6. Wire to existing Service layer
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Empty response | `grep "List.of()\\|emptyList()" src/main/java/**/repository/*Impl.java` |
| 404 on endpoint | Check Service method exists for Controller call |
| gRPC UNIMPLEMENTED | Compare `rpc ` count in .proto vs `@Override` in GrpcService |
| 500 error | `grep "throw.*UnsupportedOperationException" src/main/java/` |

---

## Rules Priority

### 🔴 CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty lists | `grep "emptyList\\|List.of()" *Impl.java` |
| API Wiring | ALL Controller methods must call existing Service methods | Check Controller→Service calls |
| gRPC Implementation | ALL proto rpc methods MUST be implemented | Count rpc vs @Override |
| Security | ALL non-public endpoints MUST have authentication | Check @PreAuthorize usage |

### 🟡 IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| Input Validation | All endpoints use @Valid | `grep "@RequestBody" *.java | grep -v "@Valid"` |
| Mock Data Quality | Realistic, varied values (not all same) | Review mock data |
| Error Handling | Global exception handler configured | Check @ControllerAdvice |
| Transaction Management | Service methods have @Transactional | Check ServiceImpl classes |

### 🟢 RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| API Documentation | OpenAPI/Swagger annotations |
| Monitoring | Actuator endpoints enabled |
| Caching | Redis/Caffeine caching for hot data |
| Rate Limiting | API rate limits configured |

---

## Error Handling Pattern

### ApiException - Unified Error Model

```java
// exception/ApiException.java
@Getter
public class ApiException extends RuntimeException {
    private final ErrorCode errorCode;
    private final HttpStatus httpStatus;
    private final Map<String, Object> details;

    public enum ErrorCode {
        // Network errors
        NETWORK_UNAVAILABLE,
        TIMEOUT,
        SERVICE_UNAVAILABLE,

        // Auth errors
        UNAUTHORIZED,
        TOKEN_EXPIRED,
        INVALID_CREDENTIALS,
        ACCESS_DENIED,

        // Data errors
        NOT_FOUND,
        VALIDATION_FAILED,
        CONFLICT,
        DATA_INTEGRITY_ERROR,

        // General errors
        INTERNAL_ERROR
    }

    public static ApiException notFound(String message) {
        return new ApiException(ErrorCode.NOT_FOUND, HttpStatus.NOT_FOUND, message);
    }

    public static ApiException unauthorized(String message) {
        return new ApiException(ErrorCode.UNAUTHORIZED, HttpStatus.UNAUTHORIZED, message);
    }

    public static ApiException validation(String message, Map<String, Object> details) {
        return new ApiException(ErrorCode.VALIDATION_FAILED, HttpStatus.BAD_REQUEST, message, details);
    }
}
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Error Flow                                │
├─────────────────────────────────────────────────────────────────┤
│  Repository Layer:                                               │
│    - Catch database exceptions                                   │
│    - Map to ApiException with appropriate code                   │
│    - Throw ApiException                                          │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer:                                                  │
│    - Catch repository exceptions                                 │
│    - Add business context if needed                              │
│    - Re-throw as ApiException                                    │
├─────────────────────────────────────────────────────────────────┤
│  Controller Layer:                                               │
│    - Let exceptions propagate to GlobalExceptionHandler          │
│    - Or handle specific cases with try-catch                     │
├─────────────────────────────────────────────────────────────────┤
│  GlobalExceptionHandler (@ControllerAdvice):                     │
│    - Map ApiException to ErrorResponse                           │
│    - Set appropriate HTTP status                                 │
│    - Return consistent error format                              │
└─────────────────────────────────────────────────────────────────┘
```

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handleApiException(ApiException ex) {
        log.error("API error: {} - {}", ex.getErrorCode(), ex.getMessage());

        ErrorResponse response = ErrorResponse.builder()
            .code(ex.getErrorCode().name())
            .message(ex.getMessage())
            .details(ex.getDetails())
            .timestamp(Instant.now())
            .build();

        return ResponseEntity.status(ex.getHttpStatus()).body(response);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(MethodArgumentNotValidException ex) {
        Map<String, String> errors = ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                FieldError::getDefaultMessage,
                (a, b) -> a
            ));

        ErrorResponse response = ErrorResponse.builder()
            .code("VALIDATION_FAILED")
            .message("Validation failed")
            .details(Map.of("fields", errors))
            .timestamp(Instant.now())
            .build();

        return ResponseEntity.badRequest().body(response);
    }
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| Controller | 80%+ | Request mapping, validation, response codes |
| Service | 90%+ | Business logic, edge cases, transactions |
| Repository | 75%+ | Query methods, data mapping |
| Integration | 60%+ | End-to-end flows |

### What to Test

**Controller Tests (MockMvc):**
```java
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean UserService userService;

    @Test
    void getUser_WhenExists_Returns200() throws Exception {
        when(userService.findById("123")).thenReturn(Optional.of(testUser));

        mockMvc.perform(get("/api/users/123"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("123"));
    }

    @Test
    void createUser_WhenInvalid_Returns400() throws Exception {
        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }
}
```

**Service Tests (Unit):**
```java
@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {
    @Mock UserRepository userRepository;
    @InjectMocks UserServiceImpl userService;

    @Test
    void create_WhenEmailExists_ThrowsValidationException() {
        when(userRepository.existsByEmail("test@test.com")).thenReturn(true);

        assertThatThrownBy(() -> userService.create(request))
            .isInstanceOf(ApiException.class)
            .hasFieldOrPropertyWithValue("errorCode", ErrorCode.CONFLICT);
    }
}
```

### Test Commands
```bash
# Run all tests with coverage
./gradlew test jacocoTestReport

# View coverage report
open build/reports/jacoco/test/html/index.html
```

---

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

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented methods (MUST be empty)
grep -rn "throw.*UnsupportedOperationException\|TODO.*implement\|throw.*NotImplementedException" src/main/java/

# 2. Check all REST endpoints have handlers
echo "REST endpoints:" && grep -c "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@RequestMapping" src/main/java/**/controller/*.java 2>/dev/null || echo 0

# 3. Check all gRPC services are implemented
echo "gRPC methods in proto:" && grep -c "rpc " src/main/proto/*.proto 2>/dev/null || echo 0
echo "gRPC methods implemented:" && grep -c "@Override" src/main/java/**/grpc/*GrpcService.java 2>/dev/null || echo 0

# 4. Verify build compiles
./gradlew clean build

# 5. Run tests
./gradlew test

# 6. 🚨 Check Controller endpoints call existing Service methods (CRITICAL!)
echo "=== Service Methods Called in Controllers ===" && \
grep -roh "[a-zA-Z]*Service\.[a-zA-Z]*(" src/main/java/**/controller/*.java | sort -u
echo "=== Service Methods Defined ===" && \
grep -rh "public.*(" src/main/java/**/service/*.java | grep -oE "[a-zA-Z]+\(" | sort -u

# 7. 🚨 Verify ALL Controller endpoints have Service layer implementation
echo "=== Controller Injection Points ===" && \
grep -rn "private.*final.*Service" src/main/java/**/controller/*.java
echo "=== Service Implementation Check ===" && \
grep -rn "@Service" src/main/java/**/service/*.java

# 8. 🚨 Check for empty endpoint handlers
grep -rn "@.*Mapping" -A5 src/main/java/**/controller/*.java | grep -E "return null|return ResponseEntity.ok\(\)|// TODO"

# 9. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "[a-zA-Z]*Repository\.[a-zA-Z]*(" src/main/java/**/service/*.java | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[A-Za-z]* [a-zA-Z]*(" src/main/java/**/repository/*Repository.java | grep -oE "[a-zA-Z]+\(" | sort -u

# 10. 🚨 Verify ALL Repository interface methods have implementations
echo "=== Repository Interface Methods ===" && \
grep -rh "[A-Za-z]* [a-zA-Z]*(" src/main/java/**/repository/*Repository.java | grep -oE "[a-zA-Z]+\(" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "@Override\|public.*(" src/main/java/**/repository/*RepositoryImpl.java | grep -oE "[a-zA-Z]+\(" | sort -u
```

⚠️ **CRITICAL**: All gRPC methods defined in .proto files MUST be implemented in GrpcService classes. Missing implementations cause runtime errors.

⚠️ **API WIRING CRITICAL**: Commands #6-#8 detect Controller endpoints that call Service methods that don't exist or are not implemented. A Controller can call `userService.getAccountInfo()` but if the Service class doesn't have this method or throws UnsupportedOperationException, the endpoint fails at runtime!

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty lists for data that powers UI charts or API responses**. This causes:
- Frontend charts that render but show nothing
- API responses with empty data arrays
- Client applications showing "No data" even when structure exists

### Mock Data Rules

**Rule 1: List data for charts MUST have at least 7 items**
```java
// ❌ BAD - Chart will be blank
public WeeklySummary getCurrentWeekSummary(String userId) {
    return new WeeklySummary(
        List.of()  // ← Chart has no data to render!
    );
}

// ✅ GOOD - Chart has data to display
public WeeklySummary getCurrentWeekSummary(String userId) {
    List<DailyReport> mockDailyReports = IntStream.range(0, 7)
        .mapToObj(i -> createMockDailyReport(
            new int[]{72, 78, 85, 80, 76, 88, 82}[i],
            new int[]{390, 420, 450, 410, 380, 460, 435}[i]
        ))
        .collect(Collectors.toList());
    return new WeeklySummary(mockDailyReports);
}
```

**Rule 2: Use realistic, varied sample values**
```java
// ❌ BAD - Monotonous test data
List<Integer> scores = Collections.nCopies(7, 80);

// ✅ GOOD - Realistic variation
int[] scores = {72, 78, 85, 80, 76, 88, 82};  // Shows trend
```

**Rule 3: Data must match DTO/Entity exactly**
```bash
# Before creating mock data, ALWAYS verify the class definition:
grep -A 20 "class TherapyData" src/main/java/**/dto/*.java
grep -A 20 "class TherapyData" src/main/java/**/model/*.java
```

**Rule 4: Create helper methods for complex mock data**
```java
// ✅ Create reusable mock factory
private DailyReport createMockDailyReport(int score, int duration) {
    return DailyReport.builder()
        .id(UUID.randomUUID().toString())
        .sleepScore(score)
        .sleepDuration(new SleepDuration(duration, ...))
        // ... all required fields
        .build();
}
```

### Quick Verification Commands for Mock Data

```bash
# 11. 🚨 Check for empty list returns in Repository stubs (MUST FIX)
grep -rn "List.of()\|Collections.emptyList()\|new ArrayList<>()" src/main/java/**/repository/*RepositoryImpl.java

# 12. 🚨 Verify chart-related data has mock values
grep -rn "dailyReports\|weeklyData\|chartData" src/main/java/**/repository/ | grep -E "emptyList|List\.of\(\)"
```

---

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

🚨 **ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests  ⚠️ MANDATORY │
│  Step 5: Mock APIs → Use mock data for unfinished dependencies  │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
│  Step 7: Verify 100% → Tests written = Features implemented     │
└─────────────────────────────────────────────────────────────────┘
```

#### ⛔ FORBIDDEN: Tests Without Implementation

```java
// ❌ WRONG - Test exists but no implementation
// Test file exists: AuthServiceTest.java (32 tests)
// Production file: AuthService.java → MISSING or throws UnsupportedOperationException
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: AuthServiceTest.java (32 tests)
// Production file: AuthService.java (fully implemented)
// All 32 tests PASS
```

#### ⛔ Placeholder Endpoint Policy

Placeholder endpoints are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```java
// ❌ WRONG - Placeholder endpoint left in production
@GetMapping("/training")
public ResponseEntity<?> training() {
    return ResponseEntity.ok(Map.of("message", "Coming Soon")); // FORBIDDEN!
}

// ✅ CORRECT - Real endpoint implementation
@GetMapping("/training")
public ResponseEntity<List<TrainingDto>> training() {
    return ResponseEntity.ok(trainingService.getAll());
}
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "UnsupportedOperationException\|NotImplementedException\|TODO.*implement\|Coming Soon" src/main/java/
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

#### Step 4: Mock External Dependencies - MANDATORY

⚠️ **CRITICAL**: Every Repository/Service method MUST return valid mock data. NEVER leave methods throwing `UnsupportedOperationException` or `NotImplementedException`.

**Rules for Mock Classes:**
1. ALL methods must return valid mock data
2. Use `Thread.sleep()` or `@Async` with delay to simulate latency (500-1000ms)
3. Mock data must match the entity/DTO structure exactly
4. Check Enum values exist before using them
5. Include all required fields for entities

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

## API Wiring Verification Guide

### 🚨 The API Wiring Blind Spot

Spring Boot Controllers often inject Services and call methods that may not exist or are not implemented:

```java
// SettingsController.java
@RestController
@RequestMapping("/api/v1/settings")
@RequiredArgsConstructor
public class SettingsController {
    private final SettingsService settingsService;

    @GetMapping("/account-info")
    public ResponseEntity<AccountInfoDto> getAccountInfo() {
        return ResponseEntity.ok(settingsService.getAccountInfo());  // ⚠️ Does this method exist?
    }

    @PostMapping("/change-password")
    public ResponseEntity<Void> changePassword(@RequestBody ChangePasswordRequest req) {
        settingsService.changePassword(req);  // ⚠️ Is this implemented or throws UnsupportedOperationException?
        return ResponseEntity.ok().build();
    }
}
```

**Problem**: If the Service class doesn't have the method or it throws `UnsupportedOperationException`, the endpoint compiles but fails at runtime!

### Detection Patterns

```bash
# Find methods called on Service classes in Controllers
grep -roh "[a-zA-Z]*Service\.[a-zA-Z]*(" src/main/java/**/controller/*.java | sort -u

# Find methods defined in Service classes
grep -rh "public.*(" src/main/java/**/service/*.java | grep -oE "[a-zA-Z]+\(" | sort -u

# Find unimplemented methods
grep -rn "throw.*UnsupportedOperationException\|TODO.*implement" src/main/java/**/service/*.java

# Compare: Every Service method called in Controller MUST exist and be implemented
```

### Verification Checklist

1. **List Service methods called in each Controller**:
   ```bash
   grep -oh "settingsService\.[a-zA-Z]*(" src/main/java/**/controller/SettingsController.java | sort -u
   ```

2. **List methods implemented in corresponding Service**:
   ```bash
   grep -h "public.*(" src/main/java/**/service/SettingsService.java | grep -oE "[a-zA-Z]+\("
   ```

3. **Every method called MUST exist in the Service!** Any missing method = runtime failure

### Correct Wiring Example

```java
// SettingsController.java (calls Service methods)
@RestController
@RequestMapping("/api/v1/settings")
@RequiredArgsConstructor
public class SettingsController {
    private final SettingsService settingsService;

    @GetMapping("/account-info")
    public ResponseEntity<AccountInfoDto> getAccountInfo() {
        return ResponseEntity.ok(settingsService.getAccountInfo());  // ✅ Method exists
    }

    @PostMapping("/change-password")
    public ResponseEntity<Void> changePassword(@RequestBody ChangePasswordRequest req) {
        settingsService.changePassword(req.getCurrentPassword(), req.getNewPassword());  // ✅ Method exists
        return ResponseEntity.ok().build();
    }
}

// SettingsService.java (fully implemented)
@Service
@RequiredArgsConstructor
public class SettingsService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AccountInfoDto getAccountInfo() {  // ✅ Implemented
        // Real implementation, NOT throwing UnsupportedOperationException
        User user = getCurrentUser();
        return AccountInfoDto.from(user);
    }

    public void changePassword(String currentPassword, String newPassword) {  // ✅ Implemented
        // Real implementation, NOT throwing UnsupportedOperationException
        User user = getCurrentUser();
        if (!passwordEncoder.matches(currentPassword, user.getPassword())) {
            throw new BadCredentialsException("Invalid current password");
        }
        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);
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
- [ ] 🚨 ALL Controller Service method calls have corresponding Service implementations
- [ ] 🚨 ALL gRPC proto methods have GrpcService implementations
- [ ] 🚨 ALL Service→Repository method calls exist in Repository interfaces
- [ ] 🚨 ALL Repository interface methods have RepositoryImpl implementations

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

---

## Spec Gap Prediction System

When Spec is incomplete, use these universal rules to predict and supplement missing API endpoints.

### Endpoint Type → Required Elements (Universal)

| Endpoint Type | Required Elements | Auto-Predict |
|---------------|-------------------|--------------|
| List endpoint | Pagination, Sorting, Filtering | Search endpoint, Count endpoint |
| Detail endpoint | ID validation, 404 handling | Related data endpoints |
| Create endpoint | Validation, 201 response | Duplicate check |
| Update endpoint | Validation, 404 handling | Partial update (PATCH) |
| Delete endpoint | 404 handling, Cascade rules | Soft delete option |
| Auth endpoint | JWT response, Refresh token | Logout, Password reset |

### Flow Completion Prediction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flow Completion Rules                         │
├─────────────────────────────────────────────────────────────────┤
│  IF Spec has Login endpoint:                                     │
│    → PREDICT: Register, Logout, Refresh token, Forgot password   │
│                                                                  │
│  IF Spec has Register endpoint:                                  │
│    → PREDICT: Email verification, Onboarding data endpoint       │
│                                                                  │
│  IF Spec has List endpoint:                                      │
│    → PREDICT: Detail endpoint (GET /{id})                        │
│    → PREDICT: Search endpoint (GET /search)                      │
│    → PREDICT: Count endpoint (GET /count)                        │
│                                                                  │
│  IF Spec has Create endpoint:                                    │
│    → PREDICT: Update endpoint (PUT /{id})                        │
│    → PREDICT: Delete endpoint (DELETE /{id})                     │
│    → PREDICT: Batch create endpoint                              │
│                                                                  │
│  IF Spec has User management:                                    │
│    → PREDICT: Profile endpoint                                   │
│    → PREDICT: Change password endpoint                           │
│    → PREDICT: Settings endpoint                                  │
└─────────────────────────────────────────────────────────────────┘
```

### CRUD Prediction Matrix

| Spec Mentions | Auto-Predict Endpoints |
|---------------|------------------------|
| "List items" | GET /items, GET /items/{id}, GET /items/count |
| "Create item" | POST /items with @Valid, 201 response |
| "Update item" | PUT /items/{id}, PATCH /items/{id} |
| "Delete item" | DELETE /items/{id}, soft delete option |
| "Search items" | GET /items/search with query params |
| "Filter items" | Query parameters with Specification pattern |

### Response Format Prediction

| Operation | Success Response | Error Response |
|-----------|-----------------|----------------|
| GET list | 200 + Page<T> | 400 (bad params) |
| GET detail | 200 + T | 404 (not found) |
| POST create | 201 + T + Location header | 400 (validation) |
| PUT update | 200 + T | 404, 400 |
| DELETE | 204 No Content | 404 |
| Auth login | 200 + JWT | 401 |

### Spec Gap Detection Commands

```bash
# 1. Detect missing CRUD endpoints
echo "=== CRUD Completeness ===" && \
echo "GET endpoints:" && grep -c "@GetMapping" src/main/java/**/controller/*.java && \
echo "POST endpoints:" && grep -c "@PostMapping" src/main/java/**/controller/*.java && \
echo "PUT endpoints:" && grep -c "@PutMapping" src/main/java/**/controller/*.java && \
echo "DELETE endpoints:" && grep -c "@DeleteMapping" src/main/java/**/controller/*.java

# 2. Detect endpoints missing validation
grep -l "@RequestBody" src/main/java/**/controller/*.java | \
xargs grep -L "@Valid" 2>/dev/null && echo "(endpoints may be missing validation)"

# 3. Detect missing error handling
grep -L "ResponseEntity.notFound\|ResponseEntity.badRequest" src/main/java/**/controller/*.java

# 4. Detect missing auth flow
echo "=== Auth Flow Check ===" && \
grep -q "login\|Login" src/main/java/**/controller/*.java || echo "⚠️ Missing: Login endpoint"
grep -q "register\|Register" src/main/java/**/controller/*.java || echo "⚠️ Missing: Register endpoint"
grep -q "logout\|Logout" src/main/java/**/controller/*.java || echo "⚠️ Missing: Logout endpoint"
grep -q "refresh\|Refresh" src/main/java/**/controller/*.java || echo "⚠️ Missing: Refresh token endpoint"

# 5. Detect missing pagination
grep -l "@GetMapping" src/main/java/**/controller/*.java | \
xargs grep -L "Pageable\|Page<" 2>/dev/null && echo "(list endpoints may be missing pagination)"
```

### Prediction Implementation Example

When implementing a resource API from Spec:

```java
// Spec says: "Manage user items"
// Auto-predict required implementation:

@RestController
@RequestMapping("/api/items")
@RequiredArgsConstructor
public class ItemController {

    private final ItemService itemService;

    // 1. LIST - Always needed with pagination
    @GetMapping
    public ResponseEntity<Page<ItemResponse>> list(Pageable pageable) {
        return ResponseEntity.ok(itemService.findAll(pageable).map(this::toResponse));
    }

    // 2. GET - Detail endpoint for list items
    @GetMapping("/{id}")
    public ResponseEntity<ItemResponse> get(@PathVariable String id) {
        return itemService.findById(id)
            .map(item -> ResponseEntity.ok(toResponse(item)))
            .orElse(ResponseEntity.notFound().build());
    }

    // 3. CREATE - With validation
    @PostMapping
    public ResponseEntity<ItemResponse> create(@Valid @RequestBody CreateItemRequest request) {
        Item item = itemService.create(request);
        return ResponseEntity
            .created(URI.create("/api/items/" + item.getId()))
            .body(toResponse(item));
    }

    // 4. UPDATE - Full update
    @PutMapping("/{id}")
    public ResponseEntity<ItemResponse> update(
            @PathVariable String id,
            @Valid @RequestBody UpdateItemRequest request) {
        return itemService.findById(id)
            .map(existing -> {
                Item updated = itemService.update(id, request);
                return ResponseEntity.ok(toResponse(updated));
            })
            .orElse(ResponseEntity.notFound().build());
    }

    // 5. DELETE - With 404 handling
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        if (!itemService.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        itemService.delete(id);
        return ResponseEntity.noContent().build();
    }

    // 6. SEARCH - Predicted for list endpoints
    @GetMapping("/search")
    public ResponseEntity<Page<ItemResponse>> search(
            @RequestParam(required = false) String query,
            Pageable pageable) {
        return ResponseEntity.ok(
            itemService.search(query, pageable).map(this::toResponse)
        );
    }
}
```

---

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
