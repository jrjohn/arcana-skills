# Service Layer Pattern

## Overview

The Service Layer pattern provides business logic orchestration between Controllers and Repositories.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Request Flow                                 │
│  ┌─────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │Controller│ →  │   Service    │ →  │  Repository  │           │
│  │(REST/gRPC│    │  (Business)  │    │   (Data)     │           │
│  └─────────┘    └──────────────┘    └──────────────┘           │
│        ↑                                    │                   │
│        │                                    ↓                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                    Database                          │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Service Interface Template

```java
public interface UserService {

    /**
     * Find user by ID
     * @param id User ID
     * @return User or empty if not found
     */
    Optional<User> findById(String id);

    /**
     * Find all users with pagination
     * @param pageable Pagination parameters
     * @return Page of users
     */
    Page<User> findAll(Pageable pageable);

    /**
     * Create new user
     * @param request Create user request
     * @return Created user
     * @throws ValidationException if validation fails
     */
    User create(CreateUserRequest request);

    /**
     * Update existing user
     * @param id User ID
     * @param request Update user request
     * @return Updated user
     * @throws NotFoundException if user not found
     */
    User update(String id, UpdateUserRequest request);

    /**
     * Delete user
     * @param id User ID
     * @throws NotFoundException if user not found
     */
    void delete(String id);
}
```

## Service Implementation Template

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    @Transactional(readOnly = true)
    public Optional<User> findById(String id) {
        log.debug("Finding user by id: {}", id);
        return userRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public Page<User> findAll(Pageable pageable) {
        log.debug("Finding all users with pageable: {}", pageable);
        return userRepository.findAll(pageable);
    }

    @Override
    @Transactional
    public User create(CreateUserRequest request) {
        log.info("Creating user with email: {}", request.getEmail());

        // Validation
        validateEmailNotExists(request.getEmail());

        // Map to entity
        User user = User.builder()
            .id(UUID.randomUUID().toString())
            .email(request.getEmail())
            .name(request.getName())
            .password(passwordEncoder.encode(request.getPassword()))
            .createdAt(Instant.now())
            .build();

        // Save
        User saved = userRepository.save(user);

        // Publish event
        eventPublisher.publishEvent(new UserCreatedEvent(saved));

        log.info("Created user with id: {}", saved.getId());
        return saved;
    }

    @Override
    @Transactional
    public User update(String id, UpdateUserRequest request) {
        log.info("Updating user: {}", id);

        User user = userRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("User not found: " + id));

        // Update fields
        if (request.getName() != null) {
            user.setName(request.getName());
        }
        if (request.getEmail() != null && !request.getEmail().equals(user.getEmail())) {
            validateEmailNotExists(request.getEmail());
            user.setEmail(request.getEmail());
        }

        user.setUpdatedAt(Instant.now());
        return userRepository.save(user);
    }

    @Override
    @Transactional
    public void delete(String id) {
        log.info("Deleting user: {}", id);

        if (!userRepository.existsById(id)) {
            throw new NotFoundException("User not found: " + id);
        }

        userRepository.deleteById(id);
        eventPublisher.publishEvent(new UserDeletedEvent(id));
    }

    private void validateEmailNotExists(String email) {
        if (userRepository.existsByEmail(email)) {
            throw new ValidationException("Email already exists: " + email);
        }
    }
}
```

## Key Principles

1. **Interface Segregation** - Define clear interface contracts
2. **Transaction Management** - Use @Transactional appropriately
3. **Validation** - Validate business rules in service layer
4. **Event Publishing** - Publish domain events for side effects
5. **Logging** - Log at appropriate levels (debug, info, error)
6. **Exception Handling** - Throw domain-specific exceptions

## Controller Integration

```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable String id) {
        return userService.findById(id)
            .map(user -> ResponseEntity.ok(toResponse(user)))
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse createUser(@Valid @RequestBody CreateUserRequest request) {
        User user = userService.create(request);
        return toResponse(user);
    }

    @PutMapping("/{id}")
    public UserResponse updateUser(
            @PathVariable String id,
            @Valid @RequestBody UpdateUserRequest request) {
        User user = userService.update(id, request);
        return toResponse(user);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable String id) {
        userService.delete(id);
    }

    private UserResponse toResponse(User user) {
        return UserResponse.builder()
            .id(user.getId())
            .email(user.getEmail())
            .name(user.getName())
            .createdAt(user.getCreatedAt())
            .build();
    }
}
```

## Testing

```java
@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private ApplicationEventPublisher eventPublisher;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void findById_WhenExists_ReturnsUser() {
        // Given
        String id = "user-123";
        User user = User.builder().id(id).email("test@test.com").build();
        when(userRepository.findById(id)).thenReturn(Optional.of(user));

        // When
        Optional<User> result = userService.findById(id);

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getId()).isEqualTo(id);
    }

    @Test
    void create_WhenEmailExists_ThrowsValidationException() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@test.com", "Test", "pass");
        when(userRepository.existsByEmail("test@test.com")).thenReturn(true);

        // When/Then
        assertThatThrownBy(() -> userService.create(request))
            .isInstanceOf(ValidationException.class)
            .hasMessageContaining("Email already exists");
    }
}
```
