# Android Development Examples

Practical development examples based on Arcana Android architecture.

## Table of Contents

1. [Complete Feature Implementation Examples](#complete-feature-implementation-examples)
2. [Common Problem Solutions](#common-problem-solutions)
3. [Code Refactoring Examples](#code-refactoring-examples)
4. [Testing Examples](#testing-examples)

---

## Complete Feature Implementation Examples

### Example 1: User Login Feature

Complete login feature implementation including form validation, error handling, and offline support.

#### Domain Layer

```kotlin
// domain/model/AuthResult.kt
sealed class AuthResult {
    data class Success(val user: User, val token: String) : AuthResult()
    data class Error(val type: AuthErrorType) : AuthResult()
}

enum class AuthErrorType {
    INVALID_CREDENTIALS,
    NETWORK_ERROR,
    USER_NOT_FOUND,
    ACCOUNT_LOCKED,
    UNKNOWN
}

// domain/repository/IAuthRepository.kt
interface IAuthRepository {
    suspend fun login(email: String, password: String): AuthResult
    suspend fun logout()
    fun isLoggedIn(): Flow<Boolean>
    fun getCurrentUser(): Flow<User?>
}

// domain/service/AuthService.kt
class AuthService @Inject constructor(
    private val authRepository: IAuthRepository,
    private val tokenManager: TokenManager
) {
    suspend fun login(email: String, password: String): AuthResult {
        // Validate input
        if (email.isBlank()) return AuthResult.Error(AuthErrorType.INVALID_CREDENTIALS)
        if (!email.isValidEmail()) return AuthResult.Error(AuthErrorType.INVALID_CREDENTIALS)
        if (password.length < 6) return AuthResult.Error(AuthErrorType.INVALID_CREDENTIALS)

        return when (val result = authRepository.login(email, password)) {
            is AuthResult.Success -> {
                tokenManager.saveToken(result.token)
                result
            }
            is AuthResult.Error -> result
        }
    }

    suspend fun logout() {
        tokenManager.clearToken()
        authRepository.logout()
    }

    fun isLoggedIn(): Flow<Boolean> = authRepository.isLoggedIn()
}
```

#### Data Layer

```kotlin
// data/repository/AuthRepository.kt
class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val userDao: UserDao,
    private val sessionDao: SessionDao,
    @IoDispatcher private val dispatcher: CoroutineDispatcher
) : IAuthRepository {

    override suspend fun login(email: String, password: String): AuthResult =
        withContext(dispatcher) {
            try {
                val response = authApi.login(LoginRequest(email, password))
                val user = response.user.toDomain()

                // Save user locally
                userDao.insert(user.toEntity())

                // Save session
                sessionDao.insert(SessionEntity(
                    token = response.token,
                    userId = user.id,
                    expiresAt = response.expiresAt
                ))

                AuthResult.Success(user, response.token)
            } catch (e: ClientRequestException) {
                when (e.response.status.value) {
                    401 -> AuthResult.Error(AuthErrorType.INVALID_CREDENTIALS)
                    404 -> AuthResult.Error(AuthErrorType.USER_NOT_FOUND)
                    423 -> AuthResult.Error(AuthErrorType.ACCOUNT_LOCKED)
                    else -> AuthResult.Error(AuthErrorType.UNKNOWN)
                }
            } catch (e: IOException) {
                AuthResult.Error(AuthErrorType.NETWORK_ERROR)
            }
        }

    override suspend fun logout() {
        sessionDao.clearAll()
    }

    override fun isLoggedIn(): Flow<Boolean> =
        sessionDao.getActiveSession()
            .map { it != null && !it.isExpired() }

    override fun getCurrentUser(): Flow<User?> =
        sessionDao.getActiveSession()
            .flatMapLatest { session ->
                session?.let { userDao.getUserById(it.userId) } ?: flowOf(null)
            }
            .map { it?.toDomain() }
}
```

#### Presentation Layer

```kotlin
// presentation/viewmodel/LoginViewModel.kt
@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authService: AuthService
) : ViewModel() {

    sealed interface Input {
        data class UpdateEmail(val email: String) : Input
        data class UpdatePassword(val password: String) : Input
        data object TogglePasswordVisibility : Input
        data object Submit : Input
    }

    data class Output(
        val email: String = "",
        val password: String = "",
        val isPasswordVisible: Boolean = false,
        val isLoading: Boolean = false,
        val emailError: String? = null,
        val passwordError: String? = null
    ) {
        val isValid: Boolean
            get() = email.isNotBlank() &&
                    email.isValidEmail() &&
                    password.length >= 6
    }

    sealed interface Effect {
        data object NavigateToHome : Effect
        data class ShowError(val message: String) : Effect
    }

    private val _output = MutableStateFlow(Output())
    val output = _output.asStateFlow()

    private val _effect = Channel<Effect>()
    val effect = _effect.receiveAsFlow()

    // Track whether fields have been touched
    private var emailTouched = false
    private var passwordTouched = false

    fun onInput(input: Input) {
        when (input) {
            is Input.UpdateEmail -> {
                emailTouched = true
                _output.update {
                    it.copy(
                        email = input.email,
                        emailError = validateEmail(input.email)
                    )
                }
            }
            is Input.UpdatePassword -> {
                passwordTouched = true
                _output.update {
                    it.copy(
                        password = input.password,
                        passwordError = validatePassword(input.password)
                    )
                }
            }
            is Input.TogglePasswordVisibility -> {
                _output.update { it.copy(isPasswordVisible = !it.isPasswordVisible) }
            }
            is Input.Submit -> submit()
        }
    }

    private fun validateEmail(email: String): String? = when {
        !emailTouched -> null
        email.isBlank() -> "Email is required"
        !email.isValidEmail() -> "Invalid email format"
        else -> null
    }

    private fun validatePassword(password: String): String? = when {
        !passwordTouched -> null
        password.isBlank() -> "Password is required"
        password.length < 6 -> "Password must be at least 6 characters"
        else -> null
    }

    private fun submit() = viewModelScope.launch {
        val currentOutput = _output.value
        if (!currentOutput.isValid) {
            emailTouched = true
            passwordTouched = true
            _output.update {
                it.copy(
                    emailError = validateEmail(it.email),
                    passwordError = validatePassword(it.password)
                )
            }
            return@launch
        }

        _output.update { it.copy(isLoading = true) }

        when (val result = authService.login(currentOutput.email, currentOutput.password)) {
            is AuthResult.Success -> {
                _effect.send(Effect.NavigateToHome)
            }
            is AuthResult.Error -> {
                _output.update { it.copy(isLoading = false) }
                val message = when (result.type) {
                    AuthErrorType.INVALID_CREDENTIALS -> "Invalid email or password"
                    AuthErrorType.USER_NOT_FOUND -> "Account not found"
                    AuthErrorType.ACCOUNT_LOCKED -> "Account is locked. Please contact support"
                    AuthErrorType.NETWORK_ERROR -> "Network error. Please check your connection"
                    AuthErrorType.UNKNOWN -> "An error occurred. Please try again"
                }
                _effect.send(Effect.ShowError(message))
            }
        }
    }
}

// presentation/ui/screens/login/LoginScreen.kt
@Composable
fun LoginScreen(
    onNavigateToHome: () -> Unit,
    onNavigateToRegister: () -> Unit,
    viewModel: LoginViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is LoginViewModel.Effect.NavigateToHome -> onNavigateToHome()
                is LoginViewModel.Effect.ShowError -> {
                    snackbarHostState.showSnackbar(effect.message)
                }
            }
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        LoginContent(
            output = output,
            onInput = viewModel::onInput,
            onRegisterClick = onNavigateToRegister,
            modifier = Modifier.padding(padding)
        )
    }
}

@Composable
private fun LoginContent(
    output: LoginViewModel.Output,
    onInput: (LoginViewModel.Input) -> Unit,
    onRegisterClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Welcome Back",
            style = MaterialTheme.typography.headlineLarge
        )

        Spacer(Modifier.height(32.dp))

        // Email input
        OutlinedTextField(
            value = output.email,
            onValueChange = { onInput(LoginViewModel.Input.UpdateEmail(it)) },
            label = { Text("Email") },
            isError = output.emailError != null,
            supportingText = output.emailError?.let { { Text(it) } },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(16.dp))

        // Password input
        OutlinedTextField(
            value = output.password,
            onValueChange = { onInput(LoginViewModel.Input.UpdatePassword(it)) },
            label = { Text("Password") },
            isError = output.passwordError != null,
            supportingText = output.passwordError?.let { { Text(it) } },
            visualTransformation = if (output.isPasswordVisible) {
                VisualTransformation.None
            } else {
                PasswordVisualTransformation()
            },
            trailingIcon = {
                IconButton(
                    onClick = { onInput(LoginViewModel.Input.TogglePasswordVisibility) }
                ) {
                    Icon(
                        imageVector = if (output.isPasswordVisible) {
                            Icons.Default.VisibilityOff
                        } else {
                            Icons.Default.Visibility
                        },
                        contentDescription = "Toggle password visibility"
                    )
                }
            },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(24.dp))

        // Login button
        Button(
            onClick = { onInput(LoginViewModel.Input.Submit) },
            enabled = !output.isLoading,
            modifier = Modifier.fillMaxWidth()
        ) {
            if (output.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                    color = MaterialTheme.colorScheme.onPrimary
                )
                Spacer(Modifier.width(8.dp))
            }
            Text("Sign In")
        }

        Spacer(Modifier.height(16.dp))

        TextButton(onClick = onRegisterClick) {
            Text("Don't have an account? Sign up")
        }
    }
}
```

---

### Example 2: List + Search + Pagination

Complete list functionality with search, pull-to-refresh, and infinite scroll.

```kotlin
// presentation/viewmodel/UserListViewModel.kt
@HiltViewModel
class UserListViewModel @Inject constructor(
    private val userService: UserService
) : ViewModel() {

    sealed interface Input {
        data object LoadInitial : Input
        data object LoadMore : Input
        data object Refresh : Input
        data class Search(val query: String) : Input
        data class SelectUser(val userId: String) : Input
    }

    data class Output(
        val users: List<User> = emptyList(),
        val searchQuery: String = "",
        val isLoading: Boolean = false,
        val isRefreshing: Boolean = false,
        val isLoadingMore: Boolean = false,
        val hasMorePages: Boolean = true,
        val error: String? = null
    )

    sealed interface Effect {
        data class NavigateToDetail(val userId: String) : Effect
    }

    private val _output = MutableStateFlow(Output())
    val output = _output.asStateFlow()

    private val _effect = Channel<Effect>()
    val effect = _effect.receiveAsFlow()

    private var currentPage = 0
    private val pageSize = 20

    init {
        onInput(Input.LoadInitial)
    }

    fun onInput(input: Input) {
        when (input) {
            is Input.LoadInitial -> loadInitial()
            is Input.LoadMore -> loadMore()
            is Input.Refresh -> refresh()
            is Input.Search -> search(input.query)
            is Input.SelectUser -> selectUser(input.userId)
        }
    }

    private fun loadInitial() = viewModelScope.launch {
        _output.update { it.copy(isLoading = true, error = null) }
        currentPage = 0

        userService.getUsers(page = 0, size = pageSize)
            .onSuccess { result ->
                _output.update {
                    it.copy(
                        users = result.users,
                        isLoading = false,
                        hasMorePages = result.hasMore
                    )
                }
            }
            .onFailure { error ->
                _output.update { it.copy(isLoading = false, error = error.message) }
            }
    }

    private fun loadMore() = viewModelScope.launch {
        val current = _output.value
        if (current.isLoadingMore || !current.hasMorePages) return@launch

        _output.update { it.copy(isLoadingMore = true) }
        currentPage++

        userService.getUsers(
            page = currentPage,
            size = pageSize,
            query = current.searchQuery.takeIf { it.isNotBlank() }
        ).onSuccess { result ->
            _output.update {
                it.copy(
                    users = it.users + result.users,
                    isLoadingMore = false,
                    hasMorePages = result.hasMore
                )
            }
        }.onFailure {
            currentPage--
            _output.update { it.copy(isLoadingMore = false) }
        }
    }

    private fun refresh() = viewModelScope.launch {
        _output.update { it.copy(isRefreshing = true, error = null) }
        currentPage = 0

        val query = _output.value.searchQuery.takeIf { it.isNotBlank() }
        userService.getUsers(page = 0, size = pageSize, query = query)
            .onSuccess { result ->
                _output.update {
                    it.copy(
                        users = result.users,
                        isRefreshing = false,
                        hasMorePages = result.hasMore
                    )
                }
            }
            .onFailure { error ->
                _output.update { it.copy(isRefreshing = false, error = error.message) }
            }
    }

    private fun search(query: String) = viewModelScope.launch {
        _output.update { it.copy(searchQuery = query, isLoading = true) }
        currentPage = 0

        // Debounce delay
        delay(300)

        userService.getUsers(page = 0, size = pageSize, query = query.takeIf { it.isNotBlank() })
            .onSuccess { result ->
                _output.update {
                    it.copy(
                        users = result.users,
                        isLoading = false,
                        hasMorePages = result.hasMore
                    )
                }
            }
            .onFailure { error ->
                _output.update { it.copy(isLoading = false, error = error.message) }
            }
    }

    private fun selectUser(userId: String) = viewModelScope.launch {
        _effect.send(Effect.NavigateToDetail(userId))
    }
}

// presentation/ui/screens/userlist/UserListScreen.kt
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UserListScreen(
    onNavigateToDetail: (String) -> Unit,
    viewModel: UserListViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is UserListViewModel.Effect.NavigateToDetail -> {
                    onNavigateToDetail(effect.userId)
                }
            }
        }
    }

    val pullRefreshState = rememberPullToRefreshState()

    PullToRefreshBox(
        isRefreshing = output.isRefreshing,
        onRefresh = { viewModel.onInput(UserListViewModel.Input.Refresh) },
        state = pullRefreshState
    ) {
        UserListContent(
            output = output,
            onInput = viewModel::onInput
        )
    }
}

@Composable
private fun UserListContent(
    output: UserListViewModel.Output,
    onInput: (UserListViewModel.Input) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        // Search bar
        SearchBar(
            query = output.searchQuery,
            onQueryChange = { onInput(UserListViewModel.Input.Search(it)) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        )

        when {
            output.isLoading && output.users.isEmpty() -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            output.error != null && output.users.isEmpty() -> {
                ErrorState(
                    message = output.error,
                    onRetry = { onInput(UserListViewModel.Input.LoadInitial) }
                )
            }
            output.users.isEmpty() -> {
                EmptyState(
                    title = "No users found",
                    description = if (output.searchQuery.isNotBlank()) {
                        "Try a different search term"
                    } else {
                        "No users available"
                    }
                )
            }
            else -> {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(
                        items = output.users,
                        key = { it.id }
                    ) { user ->
                        UserCard(
                            user = user,
                            onClick = { onInput(UserListViewModel.Input.SelectUser(user.id)) }
                        )
                    }

                    // Load more indicator
                    if (output.hasMorePages) {
                        item {
                            LaunchedEffect(Unit) {
                                onInput(UserListViewModel.Input.LoadMore)
                            }
                            if (output.isLoadingMore) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    CircularProgressIndicator(modifier = Modifier.size(24.dp))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier,
        placeholder = { Text("Search users...") },
        leadingIcon = {
            Icon(Icons.Default.Search, contentDescription = "Search")
        },
        trailingIcon = {
            if (query.isNotBlank()) {
                IconButton(onClick = { onQueryChange("") }) {
                    Icon(Icons.Default.Clear, contentDescription = "Clear")
                }
            }
        },
        singleLine = true
    )
}

@Composable
private fun UserCard(
    user: User,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            AsyncImage(
                model = user.avatarUrl,
                contentDescription = "Avatar",
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape),
                placeholder = painterResource(R.drawable.placeholder_avatar)
            )
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = user.name,
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = user.email,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
```

---

## Common Problem Solutions

### Problem 1: Compose Preview Cannot Display Hilt ViewModel

**Problem Description**: Composables using `hiltViewModel()` cannot be previewed

**Solution**: Separate UI content into independent stateless Composables

```kotlin
// Bad approach - Preview will fail
@Preview
@Composable
fun UserScreenPreview() {
    UserScreen() // Requires Hilt, cannot preview
}

// Good approach - Separate UI content
@Composable
fun UserScreen(viewModel: UserViewModel = hiltViewModel()) {
    val output by viewModel.output.collectAsStateWithLifecycle()
    UserContent(output = output, onInput = viewModel::onInput)
}

@Composable
private fun UserContent(
    output: UserViewModel.Output,
    onInput: (UserViewModel.Input) -> Unit
) {
    // UI implementation
}

@Preview
@Composable
private fun UserContentPreview() {
    UserContent(
        output = UserViewModel.Output(
            users = listOf(
                User("1", "Preview User", "preview@example.com", null, Instant.now())
            )
        ),
        onInput = {}
    )
}
```

### Problem 2: StateFlow Loses State After Configuration Change

**Problem Description**: State resets after screen rotation

**Solution**: Use `SavedStateHandle` or correct ViewModel scope

```kotlin
@HiltViewModel
class FormViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {

    // Use SavedStateHandle to save form state
    var email by mutableStateOf(savedStateHandle.get<String>("email") ?: "")
        private set

    var password by mutableStateOf(savedStateHandle.get<String>("password") ?: "")
        private set

    fun updateEmail(value: String) {
        email = value
        savedStateHandle["email"] = value
    }

    fun updatePassword(value: String) {
        password = value
        savedStateHandle["password"] = value
    }
}
```

### Problem 3: LaunchedEffect Executes Repeatedly

**Problem Description**: LaunchedEffect executes on every recomposition

**Solution**: Use correct key

```kotlin
// Wrong - Executes on every recomposition
@Composable
fun BadExample(userId: String) {
    LaunchedEffect(Unit) {
        viewModel.loadUser(userId) // Won't reload when userId changes
    }
}

// Correct - Only executes when userId changes
@Composable
fun GoodExample(userId: String) {
    LaunchedEffect(userId) {
        viewModel.loadUser(userId)
    }
}

// Correct - Only executes once
@Composable
fun OneTimeEffect() {
    LaunchedEffect(Unit) {
        viewModel.trackScreenView()
    }
}
```

### Problem 4: Room Database Migration Failure

**Problem Description**: App crashes after updating Entity

**Solution**: Provide correct Migration

```kotlin
// Migration for adding a column
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN phone TEXT")
    }
}

// Migration for renaming a column
val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // Create new table
        db.execSQL("""
            CREATE TABLE users_new (
                id TEXT PRIMARY KEY NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)
        // Copy data
        db.execSQL("""
            INSERT INTO users_new (id, full_name, email)
            SELECT id, name, email FROM users
        """)
        // Drop old table
        db.execSQL("DROP TABLE users")
        // Rename new table
        db.execSQL("ALTER TABLE users_new RENAME TO users")
    }
}

// Use in Database
@Database(
    entities = [UserEntity::class],
    version = 3,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {
    companion object {
        fun build(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
                .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
                .build()
    }
}
```

---

## Code Refactoring Examples

### Refactoring 1: Convert Callback to Flow

**Before**:

```kotlin
class LocationManager(private val fusedLocationClient: FusedLocationProviderClient) {

    fun startLocationUpdates(callback: (Location) -> Unit) {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 10000).build()

        fusedLocationClient.requestLocationUpdates(
            request,
            object : LocationCallback() {
                override fun onLocationResult(result: LocationResult) {
                    result.lastLocation?.let { callback(it) }
                }
            },
            Looper.getMainLooper()
        )
    }
}

// Usage
locationManager.startLocationUpdates { location ->
    updateUI(location)
}
```

**After**:

```kotlin
class LocationManager @Inject constructor(
    private val fusedLocationClient: FusedLocationProviderClient
) {
    fun locationUpdates(): Flow<Location> = callbackFlow {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 10000).build()

        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { trySend(it) }
            }
        }

        fusedLocationClient.requestLocationUpdates(request, callback, Looper.getMainLooper())

        awaitClose {
            fusedLocationClient.removeLocationUpdates(callback)
        }
    }
}

// Usage
viewModelScope.launch {
    locationManager.locationUpdates()
        .collect { location -> updateUI(location) }
}
```

### Refactoring 2: Convert Activity Result to suspend function

**Before**:

```kotlin
class ImagePickerActivity : AppCompatActivity() {

    private val launcher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { handleImage(it) }
    }

    fun pickImage() {
        launcher.launch("image/*")
    }
}
```

**After**:

```kotlin
// Create reusable extension
suspend fun ActivityResultCaller.pickImage(): Uri? = suspendCancellableCoroutine { cont ->
    val launcher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        cont.resume(uri)
    }
    launcher.launch("image/*")
}

// Better approach with Compose using rememberLauncherForActivityResult

@Composable
fun ImagePickerScreen(viewModel: ImagePickerViewModel = hiltViewModel()) {
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { viewModel.onImageSelected(it) }
    }

    Button(onClick = { launcher.launch("image/*") }) {
        Text("Pick Image")
    }
}
```

---

## Testing Examples

### Complete ViewModel Test

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class LoginViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var viewModel: LoginViewModel
    private lateinit var fakeAuthService: FakeAuthService

    @Before
    fun setup() {
        fakeAuthService = FakeAuthService()
        viewModel = LoginViewModel(fakeAuthService)
    }

    @Test
    fun `initial state is correct`() {
        val output = viewModel.output.value
        assertThat(output.email).isEmpty()
        assertThat(output.password).isEmpty()
        assertThat(output.isLoading).isFalse()
        assertThat(output.emailError).isNull()
        assertThat(output.passwordError).isNull()
    }

    @Test
    fun `updating email updates state`() {
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@example.com"))

        assertThat(viewModel.output.value.email).isEqualTo("test@example.com")
    }

    @Test
    fun `invalid email shows error after touch`() {
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("invalid"))

        assertThat(viewModel.output.value.emailError).isEqualTo("Invalid email format")
    }

    @Test
    fun `submit with valid credentials navigates to home`() = runTest {
        // Given
        fakeAuthService.setLoginResult(AuthResult.Success(createTestUser(), "token"))
        val effects = mutableListOf<LoginViewModel.Effect>()
        val job = launch {
            viewModel.effect.toList(effects)
        }

        // When
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@example.com"))
        viewModel.onInput(LoginViewModel.Input.UpdatePassword("password123"))
        viewModel.onInput(LoginViewModel.Input.Submit)

        advanceUntilIdle()

        // Then
        assertThat(effects).contains(LoginViewModel.Effect.NavigateToHome)
        job.cancel()
    }

    @Test
    fun `submit with invalid credentials shows error`() = runTest {
        // Given
        fakeAuthService.setLoginResult(AuthResult.Error(AuthErrorType.INVALID_CREDENTIALS))
        val effects = mutableListOf<LoginViewModel.Effect>()
        val job = launch {
            viewModel.effect.toList(effects)
        }

        // When
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@example.com"))
        viewModel.onInput(LoginViewModel.Input.UpdatePassword("password123"))
        viewModel.onInput(LoginViewModel.Input.Submit)

        advanceUntilIdle()

        // Then
        assertThat(effects.filterIsInstance<LoginViewModel.Effect.ShowError>())
            .hasSize(1)
        assertThat(viewModel.output.value.isLoading).isFalse()
        job.cancel()
    }

    @Test
    fun `submit shows loading state`() = runTest {
        // Given
        fakeAuthService.setDelay(1000)
        fakeAuthService.setLoginResult(AuthResult.Success(createTestUser(), "token"))

        // When
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@example.com"))
        viewModel.onInput(LoginViewModel.Input.UpdatePassword("password123"))
        viewModel.onInput(LoginViewModel.Input.Submit)

        // Then - loading should be true immediately
        assertThat(viewModel.output.value.isLoading).isTrue()

        advanceUntilIdle()

        // After completion, loading should be false
        assertThat(viewModel.output.value.isLoading).isFalse()
    }
}

// Fake implementation
class FakeAuthService : AuthService {
    private var loginResult: AuthResult = AuthResult.Error(AuthErrorType.UNKNOWN)
    private var delayMs: Long = 0

    fun setLoginResult(result: AuthResult) {
        loginResult = result
    }

    fun setDelay(ms: Long) {
        delayMs = ms
    }

    override suspend fun login(email: String, password: String): AuthResult {
        if (delayMs > 0) delay(delayMs)
        return loginResult
    }
}

fun createTestUser() = User(
    id = "test-id",
    name = "Test User",
    email = "test@example.com",
    avatarUrl = null,
    createdAt = Instant.now()
)
```
