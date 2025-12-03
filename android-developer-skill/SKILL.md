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

### 1. Project Structure
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
