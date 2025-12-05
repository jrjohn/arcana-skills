---
name: android-developer-skill
description: Android development guide based on Arcana Android enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design, Jetpack Compose, Hilt DI, and MVVM Input/Output pattern. Suitable for Android project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Android Developer Skill

Professional Android development skill based on [Arcana Android](https://github.com/jrjohn/arcana-android) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         Compose UI + MVVM + Input/Output            │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + Room + API          │
└─────────────────────────────────────────────────────┘
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation → Domain → Data
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces

## Instructions

When handling Android development tasks, follow these principles:

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested Gradle settings and library versions. **NEVER reconfigure project structure or modify build.gradle / libs.versions.toml**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-android.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-android template"
```

**Step 3**: Modify project name and package
Only modify the following required items:
- `rootProject.name` in `settings.gradle.kts`
- `namespace` and `applicationId` in `app/build.gradle.kts`
- Rename package directory structure under `app/src/main/java/`
- Update package-related settings in `AndroidManifest.xml`

**Step 4**: Clean up example code
The cloned project contains example UI (e.g., Arcana User Management). Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `core/` - Common utilities (analytics, common, cache)
- `di/` - Hilt DI modules
- `sync/` - Sync management
- `data/local/AppDatabase.kt` - Room database base configuration
- `data/repository/` - Repository base classes
- `MainActivity.kt` - Entry Activity
- `MyApplication.kt` - Application class
- `nav/NavGraph.kt` - Navigation configuration (modify routes)

**Example files to REPLACE**:
- `ui/screens/` - Delete all example screens, create new project UI
- `ui/theme/` - Modify Theme colors and styles
- `data/model/` - Delete example Models, create new Domain Models
- `data/local/dao/` - Delete example DAO, create new DAO
- `data/local/entity/` - Delete example Entity, create new Entity
- `data/network/` - Modify API endpoints
- `domain/` - Delete example Service, create new business logic

**Step 5**: Verify build
```bash
./gradlew clean build
```

### ❌ Prohibited Actions
- **DO NOT** create new build.gradle.kts from scratch
- **DO NOT** modify version numbers in `gradle/libs.versions.toml`
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify Gradle wrapper version
- **DO NOT** reconfigure Compose, Hilt, Room, or other library settings

### ✅ Allowed Modifications
- Add business-related Kotlin code (following existing architecture)
- Add UI screens (using existing Compose settings)
- Add Domain Models, Repository, ViewModel
- Modify strings.xml, colors.xml, and other resource files
- Add navigation routes

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

⚠️ **CRITICAL**: All development MUST follow this TDD workflow. Every Spec requirement must have corresponding tests BEFORE implementation.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests               │
│  Step 5: Mock APIs → Use mock data for unfinished Cloud APIs    │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 1: Analyze Spec Documents (SRS & SDD)
Before writing any code, extract ALL requirements from both SRS and SDD:
```kotlin
/**
 * Requirements extracted from specification documents:
 *
 * SRS (Software Requirements Specification):
 * - SRS-001: User must be able to login with email/password
 * - SRS-002: App must show splash screen for 2 seconds
 * - SRS-003: Dashboard must display user's stars and coins
 *
 * SDD (Software Design Document):
 * - SDD-001: Use Hilt for dependency injection
 * - SDD-002: Implement MVVM Input/Output pattern
 * - SDD-003: Store tokens in encrypted SharedPreferences
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```kotlin
// test/java/.../ui/screens/auth/LoginViewModelTest.kt
@HiltAndroidTest
class LoginViewModelTest {

    @get:Rule
    val hiltRule = HiltAndroidRule(this)

    private lateinit var viewModel: LoginViewModel
    private lateinit var mockAuthRepository: AuthRepository

    @Before
    fun setup() {
        mockAuthRepository = mockk()
        viewModel = LoginViewModel(mockAuthRepository)
    }

    // SRS-001: User must be able to login with email/password
    @Test
    fun `login with valid credentials should succeed`() = runTest {
        // Given
        coEvery { mockAuthRepository.login("test@test.com", "password123") } returns Result.success(Unit)

        // When
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@test.com"))
        viewModel.onInput(LoginViewModel.Input.UpdatePassword("password123"))
        viewModel.onInput(LoginViewModel.Input.Submit)

        // Then
        assertTrue(viewModel.output.value.isLoginSuccess)
    }

    // SRS-001: Invalid credentials should show error
    @Test
    fun `login with invalid credentials should show error`() = runTest {
        // Given
        coEvery { mockAuthRepository.login(any(), any()) } returns Result.failure(Exception("Invalid credentials"))

        // When
        viewModel.onInput(LoginViewModel.Input.Submit)

        // Then
        assertNotNull(viewModel.output.value.loginError)
    }
}
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL SRS and SDD items have tests:
```kotlin
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * SRS Requirements:
 * [x] SRS-001: Login with email/password - LoginViewModelTest
 * [x] SRS-002: Splash screen display - SplashScreenTest
 * [x] SRS-003: Register new account - RegisterViewModelTest
 * [x] SRS-010: Display user stars - DashboardViewModelTest
 * [x] SRS-011: Display S-coins - DashboardViewModelTest
 * [ ] SRS-020: List training items - TODO
 *
 * SDD Design Requirements:
 * [x] SDD-001: Hilt DI configuration - AppModuleTest
 * [x] SDD-002: MVVM Input/Output pattern - ViewModelTest
 * [x] SDD-003: Encrypted token storage - AuthRepositoryTest
 * [ ] SDD-004: Offline-first caching - TODO
 */
```

#### Step 4: Mock API Implementation
For APIs not yet available from Cloud team, implement mock repositories:
```kotlin
// data/repository/mock/MockAuthRepository.kt
class MockAuthRepository @Inject constructor(
    private val sharedPreferences: SharedPreferences
) : AuthRepository {

    companion object {
        // Mock user data for testing
        private val MOCK_USERS = listOf(
            MockUser("test@test.com", "password123", "Test User"),
            MockUser("demo@demo.com", "demo123", "Demo User")
        )
    }

    override suspend fun login(email: String, password: String): Result<Unit> {
        // Simulate network delay
        delay(1000)

        val user = MOCK_USERS.find { it.email == email && it.password == password }
        return if (user != null) {
            // Save mock token
            sharedPreferences.edit()
                .putString("access_token", "mock_token_${System.currentTimeMillis()}")
                .putString("user_name", user.name)
                .apply()
            Result.success(Unit)
        } else {
            Result.failure(Exception("Invalid email or password"))
        }
    }

    override suspend fun isLoggedIn(): Boolean {
        return sharedPreferences.getString("access_token", null) != null
    }
}

// di/RepositoryModule.kt - Switch between Mock and Real
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        // Use MockAuthRepository until Cloud API is ready
        // impl: AuthRepositoryImpl  // Production
        impl: MockAuthRepository     // Development/Testing
    ): AuthRepository
}
```

#### Step 5: Run All Tests Before Completion
```bash
# Run all unit tests
./gradlew test

# Run all instrumented tests
./gradlew connectedAndroidTest

# Generate test coverage report
./gradlew jacocoTestReport

# Verify all tests pass
./gradlew check
```

#### Test Directory Structure
```
app/src/
├── main/java/...                    # Production code
├── test/java/...                    # Unit tests
│   ├── ui/screens/
│   │   ├── auth/
│   │   │   ├── LoginViewModelTest.kt
│   │   │   └── RegisterViewModelTest.kt
│   │   ├── dashboard/
│   │   │   └── DashboardViewModelTest.kt
│   │   └── splash/
│   │       └── SplashViewModelTest.kt
│   ├── domain/
│   │   └── service/
│   │       └── UserServiceTest.kt
│   └── data/
│       └── repository/
│           └── AuthRepositoryTest.kt
└── androidTest/java/...             # Instrumented tests
    └── ui/screens/
        ├── LoginScreenTest.kt
        └── DashboardScreenTest.kt
```

### 2. Project Structure
```
app/
├── presentation/          # UI Layer
│   ├── ui/               # Compose Composables
│   ├── viewmodel/        # Input/Output ViewModel
│   └── navigation/       # Navigation Logic
├── domain/               # Domain Layer
│   ├── model/            # Domain Models
│   ├── service/          # Business Services
│   └── repository/       # Repository Interfaces
└── data/                 # Data Layer
    ├── repository/       # Repository Implementations
    ├── local/            # Room Database
    │   ├── entity/       # Database Entities
    │   └── dao/          # Data Access Objects
    └── remote/           # API Client
        ├── api/          # API Interfaces
        └── dto/          # Data Transfer Objects
```

### 2. ViewModel Input/Output Pattern

```kotlin
class UserViewModel @Inject constructor(
    private val userService: UserService
) : ViewModel() {

    // Input: Sealed interface defining all events
    sealed interface Input {
        data class UpdateName(val name: String) : Input
        data class UpdateEmail(val email: String) : Input
        data object Submit : Input
    }

    // Output: State container
    data class Output(
        val name: String = "",
        val email: String = "",
        val isLoading: Boolean = false,
        val error: String? = null
    )

    private val _output = MutableStateFlow(Output())
    val output: StateFlow<Output> = _output.asStateFlow()

    // Effect flow (one-time events)
    private val _effect = Channel<Effect>()
    val effect = _effect.receiveAsFlow()

    sealed interface Effect {
        data object NavigateBack : Effect
        data class ShowSnackbar(val message: String) : Effect
    }

    fun onInput(input: Input) {
        when (input) {
            is Input.UpdateName -> updateName(input.name)
            is Input.UpdateEmail -> updateEmail(input.email)
            is Input.Submit -> submit()
        }
    }
}
```

### 3. Offline-First Strategy

```kotlin
class UserRepository @Inject constructor(
    private val userDao: UserDao,
    private val userApi: UserApi,
    private val syncManager: SyncManager
) : IUserRepository {

    // Room as single source of truth
    override fun getUsers(): Flow<List<User>> = userDao.getAllUsers()
        .map { entities -> entities.map { it.toDomain() } }

    // Local-first updates
    override suspend fun updateUser(user: User): Result<Unit> {
        // 1. Immediately update local database
        userDao.update(user.toEntity().copy(syncStatus = SyncStatus.PENDING))

        // 2. Schedule background sync
        syncManager.scheduleSyncWork()

        return Result.success(Unit)
    }

    // Background sync processing
    suspend fun syncPendingChanges() {
        val pendingUsers = userDao.getPendingSync()
        pendingUsers.forEach { entity ->
            try {
                userApi.updateUser(entity.toDto())
                userDao.update(entity.copy(syncStatus = SyncStatus.SYNCED))
            } catch (e: Exception) {
                // Keep pending status for retry
            }
        }
    }
}
```

### 4. Three-Layer Cache Strategy

```kotlin
class CacheManager<K, V>(
    private val maxMemorySize: Int = 100,
    private val ttlMillis: Long = 5 * 60 * 1000 // 5 minutes
) {
    // L1: Memory cache (<1ms)
    private val memoryCache = LruCache<K, CacheEntry<V>>(maxMemorySize)

    // L2: LRU + TTL cache
    private val lruCache = LinkedHashMap<K, CacheEntry<V>>(16, 0.75f, true)

    // L3: Room persistence (via Repository)

    data class CacheEntry<V>(
        val value: V,
        val timestamp: Long = System.currentTimeMillis()
    ) {
        fun isExpired(ttl: Long) = System.currentTimeMillis() - timestamp > ttl
    }

    suspend fun get(key: K, loader: suspend () -> V): V {
        // Check L1
        memoryCache.get(key)?.takeIf { !it.isExpired(ttlMillis) }?.let {
            return it.value
        }

        // Check L2
        lruCache[key]?.takeIf { !it.isExpired(ttlMillis) }?.let {
            memoryCache.put(key, it)
            return it.value
        }

        // Load from data source
        val value = loader()
        val entry = CacheEntry(value)
        memoryCache.put(key, entry)
        lruCache[key] = entry
        return value
    }
}
```

### 5. Compose UI Best Practices

```kotlin
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    // Handle one-time effects
    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is UserViewModel.Effect.NavigateBack -> navController.popBackStack()
                is UserViewModel.Effect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    UserContent(
        output = output,
        onInput = viewModel::onInput
    )
}

// Stateless composable for easy testing
@Composable
private fun UserContent(
    output: UserViewModel.Output,
    onInput: (UserViewModel.Input) -> Unit
) {
    Column {
        OutlinedTextField(
            value = output.name,
            onValueChange = { onInput(UserViewModel.Input.UpdateName(it)) },
            label = { Text("Name") }
        )
        // ...
    }
}
```

### 6. Hilt Dependency Injection

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DataModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideUserDao(database: AppDatabase): UserDao = database.userDao()

    @Provides
    @Singleton
    fun provideHttpClient(): HttpClient = HttpClient(OkHttp) {
        install(ContentNegotiation) { json() }
        install(Logging) { level = LogLevel.BODY }
    }
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindUserRepository(impl: UserRepository): IUserRepository
}
```

### 7. Form Validation

```kotlin
// Use derivedStateOf for efficient validation state calculation
class FormState {
    var email by mutableStateOf("")
    var emailTouched by mutableStateOf(false)

    val emailError by derivedStateOf {
        when {
            !emailTouched -> null
            email.isBlank() -> "Email is required"
            !email.isValidEmail() -> "Invalid email format"
            else -> null
        }
    }

    val isValid by derivedStateOf {
        email.isNotBlank() && email.isValidEmail()
    }
}

fun String.isValidEmail(): Boolean =
    android.util.Patterns.EMAIL_ADDRESS.matcher(this).matches()
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output pattern
- [ ] Repository implements offline-first
- [ ] Compose functions have no side effects
- [ ] Properly handle Coroutine lifecycle
- [ ] Hilt modules configured correctly

### Performance Checks
- [ ] Avoid unnecessary Compose recomposition
- [ ] Use remember and derivedStateOf
- [ ] Images use Coil with caching
- [ ] Lists use LazyColumn + key

### Security Checks
- [ ] Sensitive data not stored in plain text
- [ ] API keys not hardcoded
- [ ] Input validation complete
- [ ] Network requests use HTTPS

## Common Issues

### Gradle Build Issues
1. Check `gradle/libs.versions.toml` for version conflicts
2. Run `./gradlew --refresh-dependencies`
3. Clear cache with `./gradlew clean`

### Compose Preview Failures
1. Ensure `@Preview` functions have no required parameters or have default values
2. Check Hilt ViewModel uses `@HiltViewModel`
3. Use mock data in Preview instead of real ViewModel

### Room Migration Issues
1. Define Migration objects
2. Consider `fallbackToDestructiveMigration()` during development
3. Test migration paths

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Kotlin | 1.9+ |
| Compose BOM | 2024.01+ |
| Hilt | 2.50+ |
| Room | 2.6+ |
| Ktor | 2.3+ |
| Coroutines | 1.8+ |
