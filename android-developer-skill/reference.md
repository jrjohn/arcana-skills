# Android Architecture Reference

Complete technical reference document based on Arcana Android enterprise architecture.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Clean Architecture Details](#clean-architecture-details)
3. [Jetpack Compose Guide](#jetpack-compose-guide)
4. [Hilt Dependency Injection](#hilt-dependency-injection)
5. [Data Layer Design](#data-layer-design)
6. [Network Layer Design](#network-layer-design)
7. [Testing Strategy](#testing-strategy)
8. [Performance Optimization](#performance-optimization)

---

## Project Structure

### Recommended Modular Structure

```
project-root/
├── app/                              # Main application module
│   ├── src/main/
│   │   ├── java/com/example/app/
│   │   │   ├── ArcanaApplication.kt  # Application class
│   │   │   ├── MainActivity.kt       # Single Activity
│   │   │   ├── presentation/         # Presentation layer
│   │   │   ├── domain/               # Domain layer
│   │   │   ├── data/                 # Data layer
│   │   │   └── di/                   # Hilt modules
│   │   └── res/
│   └── build.gradle.kts
├── core/                             # Core shared modules
│   ├── common/                       # Common utilities
│   ├── ui/                           # Shared UI components
│   ├── network/                      # Network layer
│   └── database/                     # Database layer
├── feature/                          # Feature modules
│   ├── auth/                         # Authentication feature
│   ├── user/                         # User feature
│   └── settings/                     # Settings feature
├── gradle/
│   └── libs.versions.toml            # Version catalog
├── build.gradle.kts
└── settings.gradle.kts
```

### Single Module Structure (Small Projects)

```
app/src/main/java/com/example/app/
├── ArcanaApplication.kt
├── MainActivity.kt
├── presentation/
│   ├── ui/
│   │   ├── theme/
│   │   │   ├── Color.kt
│   │   │   ├── Theme.kt
│   │   │   └── Type.kt
│   │   ├── components/               # Reusable components
│   │   │   ├── LoadingIndicator.kt
│   │   │   ├── ErrorMessage.kt
│   │   │   └── PrimaryButton.kt
│   │   └── screens/
│   │       ├── home/
│   │       │   ├── HomeScreen.kt
│   │       │   └── HomeViewModel.kt
│   │       └── user/
│   │           ├── UserScreen.kt
│   │           └── UserViewModel.kt
│   └── navigation/
│       ├── NavGraph.kt
│       └── Routes.kt
├── domain/
│   ├── model/
│   │   ├── User.kt
│   │   └── Result.kt
│   ├── repository/
│   │   └── IUserRepository.kt
│   └── service/
│       └── UserService.kt
├── data/
│   ├── repository/
│   │   └── UserRepository.kt
│   ├── local/
│   │   ├── AppDatabase.kt
│   │   ├── entity/
│   │   │   └── UserEntity.kt
│   │   └── dao/
│   │       └── UserDao.kt
│   └── remote/
│       ├── api/
│       │   └── UserApi.kt
│       └── dto/
│           └── UserDto.kt
└── di/
    ├── AppModule.kt
    ├── DataModule.kt
    └── NetworkModule.kt
```

---

## Clean Architecture Details

### Layer Responsibilities

#### Presentation Layer

**Responsibilities**:
- Handle UI logic and user interactions
- Manage UI state
- Convert user actions to domain layer calls

**Contains**:
- Compose UI components
- ViewModel
- UI state classes
- Navigation

```kotlin
// ViewModel Example
@HiltViewModel
class UserListViewModel @Inject constructor(
    private val userService: UserService
) : ViewModel() {

    sealed interface Input {
        data object LoadUsers : Input
        data class DeleteUser(val userId: String) : Input
        data object Refresh : Input
    }

    data class Output(
        val users: List<User> = emptyList(),
        val isLoading: Boolean = false,
        val isRefreshing: Boolean = false,
        val error: String? = null
    )

    private val _output = MutableStateFlow(Output())
    val output = _output.asStateFlow()

    init {
        onInput(Input.LoadUsers)
    }

    fun onInput(input: Input) = viewModelScope.launch {
        when (input) {
            is Input.LoadUsers -> loadUsers()
            is Input.DeleteUser -> deleteUser(input.userId)
            is Input.Refresh -> refresh()
        }
    }

    private suspend fun loadUsers() {
        _output.update { it.copy(isLoading = true, error = null) }
        userService.getUsers()
            .onSuccess { users ->
                _output.update { it.copy(users = users, isLoading = false) }
            }
            .onFailure { error ->
                _output.update { it.copy(error = error.message, isLoading = false) }
            }
    }
}
```

#### Domain Layer

**Responsibilities**:
- Encapsulate business logic
- Define domain models
- Declare Repository interfaces
- Coordinate multiple data sources

**Contains**:
- Domain Models
- Repository Interfaces
- Business Services
- Use Cases (optional)

```kotlin
// Domain Model
data class User(
    val id: String,
    val name: String,
    val email: String,
    val avatarUrl: String?,
    val createdAt: Instant
)

// Repository Interface
interface IUserRepository {
    fun getUsers(): Flow<List<User>>
    fun getUserById(id: String): Flow<User?>
    suspend fun createUser(user: User): Result<User>
    suspend fun updateUser(user: User): Result<Unit>
    suspend fun deleteUser(id: String): Result<Unit>
}

// Business Service
class UserService @Inject constructor(
    private val userRepository: IUserRepository,
    private val analyticsService: AnalyticsService
) {
    fun getUsers(): Flow<List<User>> = userRepository.getUsers()

    suspend fun createUser(name: String, email: String): Result<User> {
        // Business validation
        if (name.isBlank()) return Result.failure(ValidationException("Name required"))
        if (!email.isValidEmail()) return Result.failure(ValidationException("Invalid email"))

        val user = User(
            id = UUID.randomUUID().toString(),
            name = name.trim(),
            email = email.lowercase().trim(),
            avatarUrl = null,
            createdAt = Instant.now()
        )

        return userRepository.createUser(user).also {
            if (it.isSuccess) {
                analyticsService.track("user_created", mapOf("userId" to user.id))
            }
        }
    }
}
```

#### Data Layer

**Responsibilities**:
- Implement Repository interfaces
- Manage local and remote data sources
- Handle data synchronization and caching
- Data model conversion (DTO ↔ Entity ↔ Domain)

**Contains**:
- Repository implementations
- Room Database & DAOs
- Remote API Clients
- DTOs & Entities
- Mappers

```kotlin
// Repository Implementation
class UserRepository @Inject constructor(
    private val userDao: UserDao,
    private val userApi: UserApi,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) : IUserRepository {

    override fun getUsers(): Flow<List<User>> =
        userDao.getAllUsers()
            .map { entities -> entities.map { it.toDomain() } }
            .flowOn(dispatcher)

    override suspend fun createUser(user: User): Result<User> = withContext(dispatcher) {
        runCatching {
            // Save locally first
            val entity = user.toEntity().copy(syncStatus = SyncStatus.PENDING)
            userDao.insert(entity)

            // Try to sync to remote
            try {
                val response = userApi.createUser(user.toDto())
                userDao.update(entity.copy(
                    serverId = response.id,
                    syncStatus = SyncStatus.SYNCED
                ))
            } catch (e: Exception) {
                // Keep pending status when offline
            }

            user
        }
    }
}

// Entity
@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val serverId: String? = null,
    val name: String,
    val email: String,
    val avatarUrl: String?,
    val createdAt: Long,
    @ColumnInfo(name = "sync_status")
    val syncStatus: SyncStatus = SyncStatus.SYNCED
)

// DTO
@Serializable
data class UserDto(
    val id: String,
    val name: String,
    val email: String,
    @SerialName("avatar_url")
    val avatarUrl: String?,
    @SerialName("created_at")
    val createdAt: String
)

// Mappers
fun UserEntity.toDomain() = User(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    createdAt = Instant.ofEpochMilli(createdAt)
)

fun User.toEntity() = UserEntity(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    createdAt = createdAt.toEpochMilli()
)

fun UserDto.toDomain() = User(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    createdAt = Instant.parse(createdAt)
)
```

---

## Jetpack Compose Guide

### State Management

```kotlin
// Use StateFlow + collectAsStateWithLifecycle
@Composable
fun UserScreen(viewModel: UserViewModel = hiltViewModel()) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    UserContent(
        output = output,
        onInput = viewModel::onInput
    )
}

// Use remember for local UI state
@Composable
fun ExpandableCard(title: String, content: @Composable () -> Unit) {
    var expanded by remember { mutableStateOf(false) }

    Card(onClick = { expanded = !expanded }) {
        Text(title)
        AnimatedVisibility(visible = expanded) {
            content()
        }
    }
}

// Use derivedStateOf for complex calculations
@Composable
fun SearchScreen(items: List<Item>) {
    var query by remember { mutableStateOf("") }

    val filteredItems by remember(items) {
        derivedStateOf {
            if (query.isBlank()) items
            else items.filter { it.name.contains(query, ignoreCase = true) }
        }
    }

    // ...
}
```

### Side Effect Handling

```kotlin
@Composable
fun UserDetailScreen(
    userId: String,
    viewModel: UserDetailViewModel = hiltViewModel()
) {
    // One-time load
    LaunchedEffect(userId) {
        viewModel.loadUser(userId)
    }

    // Handle one-time events
    val context = LocalContext.current
    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is Effect.ShowToast -> Toast.makeText(context, effect.message, Toast.LENGTH_SHORT).show()
                is Effect.Navigate -> navController.navigate(effect.route)
            }
        }
    }

    // Lifecycle-aware
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                viewModel.refresh()
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }
}
```

### Reusable Component Design

```kotlin
// Button Component
@Composable
fun PrimaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    isLoading: Boolean = false
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled && !isLoading
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(16.dp),
                strokeWidth = 2.dp,
                color = MaterialTheme.colorScheme.onPrimary
            )
            Spacer(Modifier.width(8.dp))
        }
        Text(text)
    }
}

// Error State Component
@Composable
fun ErrorState(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.Warning,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.error
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = message,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(16.dp))
        OutlinedButton(onClick = onRetry) {
            Text("Retry")
        }
    }
}

// Empty State Component
@Composable
fun EmptyState(
    title: String,
    description: String,
    action: (@Composable () -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.headlineSmall
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = description,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        action?.let {
            Spacer(Modifier.height(24.dp))
            it()
        }
    }
}
```

---

## Hilt Dependency Injection

### Module Organization

```kotlin
// AppModule - Global singletons
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideCoroutineDispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
        encodeDefaults = true
    }
}

// DatabaseModule - Database related
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
            .build()

    @Provides
    fun provideUserDao(database: AppDatabase): UserDao = database.userDao()

    @Provides
    fun provideSettingsDao(database: AppDatabase): SettingsDao = database.settingsDao()
}

// NetworkModule - Network related
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideHttpClient(json: Json): HttpClient = HttpClient(OkHttp) {
        install(ContentNegotiation) {
            json(json)
        }
        install(Logging) {
            logger = Logger.DEFAULT
            level = LogLevel.HEADERS
        }
        install(HttpTimeout) {
            requestTimeoutMillis = 30_000
            connectTimeoutMillis = 10_000
        }
        defaultRequest {
            contentType(ContentType.Application.Json)
        }
    }

    @Provides
    @Singleton
    fun provideUserApi(client: HttpClient): UserApi =
        Ktorfit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .httpClient(client)
            .build()
            .create()
}

// RepositoryModule - Use @Binds to bind interfaces
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindUserRepository(impl: UserRepository): IUserRepository

    @Binds
    @Singleton
    abstract fun bindSettingsRepository(impl: SettingsRepository): ISettingsRepository
}
```

### Qualifier Usage

```kotlin
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class MainDispatcher

@Module
@InstallIn(SingletonComponent::class)
object DispatcherModule {

    @IoDispatcher
    @Provides
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO

    @MainDispatcher
    @Provides
    fun provideMainDispatcher(): CoroutineDispatcher = Dispatchers.Main
}

// Usage
class UserRepository @Inject constructor(
    private val userDao: UserDao,
    @IoDispatcher private val dispatcher: CoroutineDispatcher
) : IUserRepository {
    // ...
}
```

---

## Data Layer Design

### Room Database

```kotlin
@Database(
    entities = [UserEntity::class, SettingsEntity::class],
    version = 3,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun settingsDao(): SettingsDao
}

// TypeConverters
class Converters {
    @TypeConverter
    fun fromTimestamp(value: Long?): Instant? = value?.let { Instant.ofEpochMilli(it) }

    @TypeConverter
    fun toTimestamp(instant: Instant?): Long? = instant?.toEpochMilli()

    @TypeConverter
    fun fromSyncStatus(status: SyncStatus): String = status.name

    @TypeConverter
    fun toSyncStatus(value: String): SyncStatus = SyncStatus.valueOf(value)
}

// DAO
@Dao
interface UserDao {
    @Query("SELECT * FROM users ORDER BY created_at DESC")
    fun getAllUsers(): Flow<List<UserEntity>>

    @Query("SELECT * FROM users WHERE id = :id")
    fun getUserById(id: String): Flow<UserEntity?>

    @Query("SELECT * FROM users WHERE sync_status = 'PENDING'")
    suspend fun getPendingSync(): List<UserEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(user: UserEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(users: List<UserEntity>)

    @Update
    suspend fun update(user: UserEntity)

    @Query("DELETE FROM users WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM users")
    suspend fun deleteAll()

    @Transaction
    suspend fun replaceAll(users: List<UserEntity>) {
        deleteAll()
        insertAll(users)
    }
}

// Migration
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'SYNCED'")
    }
}
```

### DataStore Preferences

```kotlin
@Singleton
class PreferencesManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val Context.dataStore by preferencesDataStore(name = "settings")

    private object Keys {
        val THEME_MODE = stringPreferencesKey("theme_mode")
        val NOTIFICATIONS_ENABLED = booleanPreferencesKey("notifications_enabled")
        val LAST_SYNC_TIME = longPreferencesKey("last_sync_time")
    }

    val themeMode: Flow<ThemeMode> = context.dataStore.data
        .map { preferences ->
            preferences[Keys.THEME_MODE]?.let { ThemeMode.valueOf(it) } ?: ThemeMode.SYSTEM
        }

    val notificationsEnabled: Flow<Boolean> = context.dataStore.data
        .map { preferences -> preferences[Keys.NOTIFICATIONS_ENABLED] ?: true }

    suspend fun setThemeMode(mode: ThemeMode) {
        context.dataStore.edit { preferences ->
            preferences[Keys.THEME_MODE] = mode.name
        }
    }

    suspend fun setNotificationsEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[Keys.NOTIFICATIONS_ENABLED] = enabled
        }
    }

    suspend fun updateLastSyncTime() {
        context.dataStore.edit { preferences ->
            preferences[Keys.LAST_SYNC_TIME] = System.currentTimeMillis()
        }
    }
}

enum class ThemeMode { LIGHT, DARK, SYSTEM }
```

---

## Network Layer Design

### Ktor Client + Ktorfit

```kotlin
// API Interface Definition
interface UserApi {
    @GET("users")
    suspend fun getUsers(): List<UserDto>

    @GET("users/{id}")
    suspend fun getUserById(@Path("id") id: String): UserDto

    @POST("users")
    suspend fun createUser(@Body user: UserDto): UserDto

    @PUT("users/{id}")
    suspend fun updateUser(@Path("id") id: String, @Body user: UserDto): UserDto

    @DELETE("users/{id}")
    suspend fun deleteUser(@Path("id") id: String)
}

// Error Handling
sealed class ApiError : Exception() {
    data class HttpError(val code: Int, override val message: String) : ApiError()
    data class NetworkError(override val cause: Throwable) : ApiError()
    data class ParseError(override val cause: Throwable) : ApiError()
    data object UnknownError : ApiError()
}

suspend fun <T> safeApiCall(call: suspend () -> T): Result<T> = try {
    Result.success(call())
} catch (e: ClientRequestException) {
    Result.failure(ApiError.HttpError(e.response.status.value, e.message))
} catch (e: ServerResponseException) {
    Result.failure(ApiError.HttpError(e.response.status.value, e.message))
} catch (e: IOException) {
    Result.failure(ApiError.NetworkError(e))
} catch (e: SerializationException) {
    Result.failure(ApiError.ParseError(e))
} catch (e: Exception) {
    Result.failure(ApiError.UnknownError)
}
```

### Network Status Monitoring

```kotlin
@Singleton
class NetworkMonitor @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    val isOnline: StateFlow<Boolean> = callbackFlow {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                trySend(true)
            }

            override fun onLost(network: Network) {
                trySend(false)
            }
        }

        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()

        connectivityManager.registerNetworkCallback(request, callback)

        // Initial state
        trySend(connectivityManager.activeNetwork != null)

        awaitClose {
            connectivityManager.unregisterNetworkCallback(callback)
        }
    }.stateIn(
        scope = CoroutineScope(Dispatchers.IO),
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = true
    )
}
```

---

## Testing Strategy

### ViewModel Testing

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class UserListViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var viewModel: UserListViewModel
    private lateinit var userService: FakeUserService

    @Before
    fun setup() {
        userService = FakeUserService()
        viewModel = UserListViewModel(userService)
    }

    @Test
    fun `loadUsers success updates state with users`() = runTest {
        // Given
        val users = listOf(
            User("1", "John", "john@example.com", null, Instant.now())
        )
        userService.setUsers(users)

        // When
        viewModel.onInput(UserListViewModel.Input.LoadUsers)

        // Then
        val output = viewModel.output.value
        assertThat(output.users).isEqualTo(users)
        assertThat(output.isLoading).isFalse()
        assertThat(output.error).isNull()
    }

    @Test
    fun `loadUsers failure updates state with error`() = runTest {
        // Given
        userService.setShouldFail(true)

        // When
        viewModel.onInput(UserListViewModel.Input.LoadUsers)

        // Then
        val output = viewModel.output.value
        assertThat(output.error).isNotNull()
        assertThat(output.isLoading).isFalse()
    }
}

// Test Dispatcher Rule
class MainDispatcherRule(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

### Repository Testing

```kotlin
class UserRepositoryTest {

    private lateinit var repository: UserRepository
    private lateinit var fakeDao: FakeUserDao
    private lateinit var fakeApi: FakeUserApi

    @Before
    fun setup() {
        fakeDao = FakeUserDao()
        fakeApi = FakeUserApi()
        repository = UserRepository(fakeDao, fakeApi, UnconfinedTestDispatcher())
    }

    @Test
    fun `getUsers returns flow from dao`() = runTest {
        // Given
        val entities = listOf(createUserEntity("1", "John"))
        fakeDao.insertAll(entities)

        // When
        val users = repository.getUsers().first()

        // Then
        assertThat(users).hasSize(1)
        assertThat(users[0].name).isEqualTo("John")
    }

    @Test
    fun `createUser saves to local first then syncs`() = runTest {
        // Given
        val user = createUser("1", "John")

        // When
        repository.createUser(user)

        // Then
        assertThat(fakeDao.getAllUsers().first()).hasSize(1)
        assertThat(fakeApi.createCalled).isTrue()
    }
}
```

### Compose UI Testing

```kotlin
class UserScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `displays user list when loaded`() {
        // Given
        val output = UserListViewModel.Output(
            users = listOf(
                User("1", "John", "john@example.com", null, Instant.now())
            ),
            isLoading = false
        )

        // When
        composeTestRule.setContent {
            UserListContent(
                output = output,
                onInput = {}
            )
        }

        // Then
        composeTestRule.onNodeWithText("John").assertIsDisplayed()
    }

    @Test
    fun `displays loading indicator when loading`() {
        // Given
        val output = UserListViewModel.Output(isLoading = true)

        // When
        composeTestRule.setContent {
            UserListContent(
                output = output,
                onInput = {}
            )
        }

        // Then
        composeTestRule.onNodeWithContentDescription("Loading").assertIsDisplayed()
    }

    @Test
    fun `calls onInput when user clicks item`() {
        // Given
        var capturedInput: UserListViewModel.Input? = null
        val output = UserListViewModel.Output(
            users = listOf(
                User("1", "John", "john@example.com", null, Instant.now())
            )
        )

        // When
        composeTestRule.setContent {
            UserListContent(
                output = output,
                onInput = { capturedInput = it }
            )
        }
        composeTestRule.onNodeWithText("John").performClick()

        // Then
        assertThat(capturedInput).isInstanceOf(UserListViewModel.Input.SelectUser::class.java)
    }
}
```

---

## Performance Optimization

### Compose Recomposition Optimization

```kotlin
// Use key to stabilize list items
@Composable
fun UserList(users: List<User>) {
    LazyColumn {
        items(
            items = users,
            key = { it.id } // Stable key avoids unnecessary recomposition
        ) { user ->
            UserItem(user = user)
        }
    }
}

// Use remember to cache calculation results
@Composable
fun ExpensiveCalculation(data: List<Int>) {
    val result = remember(data) {
        data.map { it * 2 }.sum() // Only recalculates when data changes
    }
    Text("Result: $result")
}

// Use derivedStateOf for derived state
@Composable
fun FilteredList(items: List<Item>, query: String) {
    val filteredItems by remember(items) {
        derivedStateOf {
            items.filter { it.name.contains(query) }
        }
    }
    // filteredItems only recalculates when needed
}

// Use Immutable annotation
@Immutable
data class UserUiState(
    val name: String,
    val email: String
)

// Avoid creating lambdas in Composable
@Composable
fun BadExample(viewModel: ViewModel) {
    // Creates new lambda on every recomposition
    Button(onClick = { viewModel.doSomething() }) { }
}

@Composable
fun GoodExample(viewModel: ViewModel) {
    // Stable reference
    Button(onClick = viewModel::doSomething) { }
}
```

### Image Loading Optimization

```kotlin
@Composable
fun UserAvatar(
    imageUrl: String?,
    modifier: Modifier = Modifier
) {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(imageUrl)
            .crossfade(true)
            .memoryCachePolicy(CachePolicy.ENABLED)
            .diskCachePolicy(CachePolicy.ENABLED)
            .build(),
        contentDescription = "User avatar",
        placeholder = painterResource(R.drawable.placeholder_avatar),
        error = painterResource(R.drawable.error_avatar),
        modifier = modifier
            .size(48.dp)
            .clip(CircleShape)
    )
}
```

### Database Query Optimization

```kotlin
@Dao
interface UserDao {
    // Use index
    @Query("SELECT * FROM users WHERE email = :email")
    suspend fun findByEmail(email: String): UserEntity?

    // Paginated query
    @Query("SELECT * FROM users ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
    suspend fun getUsersPaged(limit: Int, offset: Int): List<UserEntity>

    // Query only needed fields
    @Query("SELECT id, name FROM users")
    fun getUserSummaries(): Flow<List<UserSummary>>
}

// Entity with index
@Entity(
    tableName = "users",
    indices = [
        Index(value = ["email"], unique = true),
        Index(value = ["sync_status"])
    ]
)
data class UserEntity(...)
```
