# Android Design Patterns

Design patterns and best practices based on Arcana Android architecture.

## Table of Contents

1. [Architecture Patterns](#architecture-patterns)
2. [UI Patterns](#ui-patterns)
3. [Data Patterns](#data-patterns)
4. [Concurrency Patterns](#concurrency-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Navigation Patterns](#navigation-patterns)

---

## Architecture Patterns

### Input/Output ViewModel Pattern

**Purpose**: Establish clear unidirectional data flow, separating user events and UI state.

**Structure**:

```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: FeatureRepository
) : ViewModel() {

    // ═══════════════════════════════════════════════════════════════
    // INPUT: Define all possible user events
    // ═══════════════════════════════════════════════════════════════
    sealed interface Input {
        data object Initialize : Input
        data class UpdateField(val value: String) : Input
        data object Submit : Input
        data object Retry : Input
    }

    // ═══════════════════════════════════════════════════════════════
    // OUTPUT: UI state container
    // ═══════════════════════════════════════════════════════════════
    data class Output(
        val data: List<Item> = emptyList(),
        val fieldValue: String = "",
        val isLoading: Boolean = false,
        val error: UiError? = null
    ) {
        // Derived state
        val isSubmitEnabled: Boolean
            get() = fieldValue.isNotBlank() && !isLoading

        val isEmpty: Boolean
            get() = data.isEmpty() && !isLoading && error == null
    }

    // ═══════════════════════════════════════════════════════════════
    // EFFECT: One-time events (navigation, Toast, Snackbar)
    // ═══════════════════════════════════════════════════════════════
    sealed interface Effect {
        data object NavigateBack : Effect
        data class ShowSnackbar(val message: String) : Effect
        data class Navigate(val route: String) : Effect
    }

    // ═══════════════════════════════════════════════════════════════
    // STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════
    private val _output = MutableStateFlow(Output())
    val output: StateFlow<Output> = _output.asStateFlow()

    private val _effect = Channel<Effect>(Channel.BUFFERED)
    val effect: Flow<Effect> = _effect.receiveAsFlow()

    // ═══════════════════════════════════════════════════════════════
    // INPUT HANDLER
    // ═══════════════════════════════════════════════════════════════
    fun onInput(input: Input) {
        when (input) {
            is Input.Initialize -> initialize()
            is Input.UpdateField -> updateField(input.value)
            is Input.Submit -> submit()
            is Input.Retry -> retry()
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ═══════════════════════════════════════════════════════════════
    private fun initialize() = viewModelScope.launch {
        _output.update { it.copy(isLoading = true) }
        // ...
    }

    private fun updateField(value: String) {
        _output.update { it.copy(fieldValue = value) }
    }

    private fun submit() = viewModelScope.launch {
        // ...
        _effect.send(Effect.NavigateBack)
    }

    private fun retry() = initialize()
}
```

**Usage**:

```kotlin
@Composable
fun FeatureScreen(
    viewModel: FeatureViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    // Handle one-time effects
    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is FeatureViewModel.Effect.NavigateBack -> navController.popBackStack()
                is FeatureViewModel.Effect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
                is FeatureViewModel.Effect.Navigate -> navController.navigate(effect.route)
            }
        }
    }

    FeatureContent(
        output = output,
        onInput = viewModel::onInput
    )
}
```

---

### Repository Pattern (Offline-First)

**Purpose**: Unify data access, implement offline-first strategy.

**Structure**:

```kotlin
// ═══════════════════════════════════════════════════════════════
// DOMAIN LAYER - Define interface
// ═══════════════════════════════════════════════════════════════
interface IItemRepository {
    fun getItems(): Flow<List<Item>>
    fun getItemById(id: String): Flow<Item?>
    suspend fun createItem(item: Item): Result<Item>
    suspend fun updateItem(item: Item): Result<Unit>
    suspend fun deleteItem(id: String): Result<Unit>
    suspend fun syncWithRemote(): Result<Unit>
}

// ═══════════════════════════════════════════════════════════════
// DATA LAYER - Implementation
// ═══════════════════════════════════════════════════════════════
class ItemRepository @Inject constructor(
    private val itemDao: ItemDao,
    private val itemApi: ItemApi,
    private val networkMonitor: NetworkMonitor,
    @IoDispatcher private val dispatcher: CoroutineDispatcher
) : IItemRepository {

    // Read - directly from local database (single source of truth)
    override fun getItems(): Flow<List<Item>> =
        itemDao.getAllItems()
            .map { entities -> entities.map { it.toDomain() } }
            .flowOn(dispatcher)

    override fun getItemById(id: String): Flow<Item?> =
        itemDao.getItemById(id)
            .map { it?.toDomain() }
            .flowOn(dispatcher)

    // Write - local first, schedule sync
    override suspend fun createItem(item: Item): Result<Item> = withContext(dispatcher) {
        runCatching {
            val entity = item.toEntity().copy(syncStatus = SyncStatus.PENDING)
            itemDao.insert(entity)

            // If online, sync immediately
            if (networkMonitor.isOnline.value) {
                syncItem(entity)
            }

            item
        }
    }

    override suspend fun updateItem(item: Item): Result<Unit> = withContext(dispatcher) {
        runCatching {
            val entity = item.toEntity().copy(
                syncStatus = SyncStatus.PENDING,
                updatedAt = System.currentTimeMillis()
            )
            itemDao.update(entity)

            if (networkMonitor.isOnline.value) {
                syncItem(entity)
            }
        }
    }

    override suspend fun deleteItem(id: String): Result<Unit> = withContext(dispatcher) {
        runCatching {
            // Mark as pending deletion
            itemDao.markAsDeleted(id)

            if (networkMonitor.isOnline.value) {
                try {
                    itemApi.deleteItem(id)
                    itemDao.deleteById(id)
                } catch (e: Exception) {
                    // Keep mark, delete on next sync
                }
            }
        }
    }

    // Sync logic
    override suspend fun syncWithRemote(): Result<Unit> = withContext(dispatcher) {
        runCatching {
            // 1. Upload pending local changes
            uploadPendingChanges()

            // 2. Download latest remote data
            downloadRemoteChanges()
        }
    }

    private suspend fun uploadPendingChanges() {
        val pendingItems = itemDao.getPendingSync()
        val deletedItems = itemDao.getDeletedItems()

        // Upload create/update
        pendingItems.forEach { entity ->
            try {
                if (entity.serverId == null) {
                    val response = itemApi.createItem(entity.toDto())
                    itemDao.update(entity.copy(
                        serverId = response.id,
                        syncStatus = SyncStatus.SYNCED
                    ))
                } else {
                    itemApi.updateItem(entity.serverId, entity.toDto())
                    itemDao.update(entity.copy(syncStatus = SyncStatus.SYNCED))
                }
            } catch (e: Exception) {
                // Keep pending, retry next time
            }
        }

        // Delete
        deletedItems.forEach { entity ->
            try {
                entity.serverId?.let { itemApi.deleteItem(it) }
                itemDao.deleteById(entity.id)
            } catch (e: Exception) {
                // Keep mark, retry next time
            }
        }
    }

    private suspend fun downloadRemoteChanges() {
        val remoteItems = itemApi.getItems()
        val localItems = itemDao.getAllItemsSnapshot()

        // Merge strategy: remote priority (unless local has unsynced changes)
        remoteItems.forEach { dto ->
            val local = localItems.find { it.serverId == dto.id }
            if (local == null || local.syncStatus == SyncStatus.SYNCED) {
                itemDao.insert(dto.toEntity())
            }
        }
    }

    private suspend fun syncItem(entity: ItemEntity) {
        try {
            if (entity.serverId == null) {
                val response = itemApi.createItem(entity.toDto())
                itemDao.update(entity.copy(
                    serverId = response.id,
                    syncStatus = SyncStatus.SYNCED
                ))
            } else {
                itemApi.updateItem(entity.serverId, entity.toDto())
                itemDao.update(entity.copy(syncStatus = SyncStatus.SYNCED))
            }
        } catch (e: Exception) {
            // Keep pending status
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// SYNC STATUS
// ═══════════════════════════════════════════════════════════════
enum class SyncStatus {
    SYNCED,     // Synced
    PENDING,    // Pending upload
    DELETED     // Pending deletion
}
```

---

### Service Layer Pattern

**Purpose**: Encapsulate business logic, coordinate multiple repositories.

```kotlin
class OrderService @Inject constructor(
    private val orderRepository: IOrderRepository,
    private val userRepository: IUserRepository,
    private val paymentRepository: IPaymentRepository,
    private val notificationService: NotificationService,
    private val analyticsService: AnalyticsService
) {
    suspend fun createOrder(items: List<CartItem>): Result<Order> {
        // 1. Validate user
        val user = userRepository.getCurrentUser() ?: return Result.failure(
            BusinessException("User not logged in")
        )

        // 2. Calculate price
        val total = items.sumOf { it.price * it.quantity }
        if (total <= 0) return Result.failure(
            BusinessException("Invalid order total")
        )

        // 3. Create order
        val order = Order(
            id = UUID.randomUUID().toString(),
            userId = user.id,
            items = items.map { it.toOrderItem() },
            total = total,
            status = OrderStatus.PENDING,
            createdAt = Instant.now()
        )

        return orderRepository.createOrder(order)
            .onSuccess {
                analyticsService.track("order_created", mapOf(
                    "orderId" to order.id,
                    "total" to total.toString(),
                    "itemCount" to items.size.toString()
                ))
            }
    }

    suspend fun processPayment(orderId: String, paymentMethod: PaymentMethod): Result<Payment> {
        // 1. Get order
        val order = orderRepository.getOrderById(orderId)
            ?: return Result.failure(BusinessException("Order not found"))

        // 2. Validate order status
        if (order.status != OrderStatus.PENDING) {
            return Result.failure(BusinessException("Order already processed"))
        }

        // 3. Process payment
        return paymentRepository.processPayment(
            orderId = orderId,
            amount = order.total,
            method = paymentMethod
        ).onSuccess { payment ->
            // 4. Update order status
            orderRepository.updateOrderStatus(orderId, OrderStatus.PAID)

            // 5. Send notification
            notificationService.sendOrderConfirmation(order)

            analyticsService.track("payment_completed", mapOf(
                "orderId" to orderId,
                "paymentId" to payment.id
            ))
        }
    }
}
```

---

## UI Patterns

### Stateless Composable Pattern

**Purpose**: Separate UI logic from state management, improve testability and reusability.

```kotlin
// ═══════════════════════════════════════════════════════════════
// STATEFUL CONTAINER - Connect ViewModel
// ═══════════════════════════════════════════════════════════════
@Composable
fun ProfileScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: ProfileViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is ProfileViewModel.Effect.NavigateToSettings -> onNavigateToSettings()
            }
        }
    }

    ProfileContent(
        output = output,
        onInput = viewModel::onInput
    )
}

// ═══════════════════════════════════════════════════════════════
// STATELESS CONTENT - Pure UI
// ═══════════════════════════════════════════════════════════════
@Composable
private fun ProfileContent(
    output: ProfileViewModel.Output,
    onInput: (ProfileViewModel.Input) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.fillMaxSize()) {
        ProfileHeader(
            user = output.user,
            onEditClick = { onInput(ProfileViewModel.Input.EditProfile) }
        )

        ProfileStats(
            stats = output.stats
        )

        ProfileActions(
            onSettingsClick = { onInput(ProfileViewModel.Input.OpenSettings) },
            onLogoutClick = { onInput(ProfileViewModel.Input.Logout) }
        )
    }
}

// ═══════════════════════════════════════════════════════════════
// REUSABLE COMPONENTS - Smaller UI units
// ═══════════════════════════════════════════════════════════════
@Composable
private fun ProfileHeader(
    user: User?,
    onEditClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        AsyncImage(
            model = user?.avatarUrl,
            contentDescription = "Profile picture",
            modifier = Modifier
                .size(72.dp)
                .clip(CircleShape)
        )

        Spacer(Modifier.width(16.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = user?.name ?: "Loading...",
                style = MaterialTheme.typography.headlineSmall
            )
            Text(
                text = user?.email ?: "",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        IconButton(onClick = onEditClick) {
            Icon(Icons.Default.Edit, contentDescription = "Edit profile")
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// PREVIEW - Preview with fake data
// ═══════════════════════════════════════════════════════════════
@Preview
@Composable
private fun ProfileContentPreview() {
    MaterialTheme {
        ProfileContent(
            output = ProfileViewModel.Output(
                user = User(
                    id = "1",
                    name = "John Doe",
                    email = "john@example.com",
                    avatarUrl = null,
                    createdAt = Instant.now()
                ),
                stats = ProfileStats(posts = 42, followers = 1234, following = 567)
            ),
            onInput = {}
        )
    }
}
```

---

### Loading/Error/Empty State Pattern

**Purpose**: Unified handling of various UI states.

```kotlin
// ═══════════════════════════════════════════════════════════════
// UI STATE WRAPPER
// ═══════════════════════════════════════════════════════════════
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String, val retry: (() -> Unit)? = null) : UiState<Nothing>()
    data object Empty : UiState<Nothing>()
}

// ═══════════════════════════════════════════════════════════════
// STATE HANDLER COMPOSABLE
// ═══════════════════════════════════════════════════════════════
@Composable
fun <T> UiStateHandler(
    state: UiState<T>,
    onRetry: () -> Unit = {},
    emptyContent: @Composable () -> Unit = { DefaultEmptyState() },
    loadingContent: @Composable () -> Unit = { DefaultLoadingState() },
    errorContent: @Composable (String) -> Unit = { DefaultErrorState(it, onRetry) },
    successContent: @Composable (T) -> Unit
) {
    when (state) {
        is UiState.Loading -> loadingContent()
        is UiState.Empty -> emptyContent()
        is UiState.Error -> errorContent(state.message)
        is UiState.Success -> successContent(state.data)
    }
}

@Composable
private fun DefaultLoadingState() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator()
    }
}

@Composable
private fun DefaultEmptyState() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.Inbox,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "No items",
            style = MaterialTheme.typography.titleLarge
        )
        Text(
            text = "There's nothing here yet",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun DefaultErrorState(
    message: String,
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.ErrorOutline,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.error
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "Something went wrong",
            style = MaterialTheme.typography.titleLarge
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = onRetry) {
            Text("Try again")
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// USAGE
// ═══════════════════════════════════════════════════════════════
@Composable
fun ItemListScreen(viewModel: ItemListViewModel = hiltViewModel()) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    val uiState = when {
        output.isLoading -> UiState.Loading
        output.error != null -> UiState.Error(output.error!!)
        output.items.isEmpty() -> UiState.Empty
        else -> UiState.Success(output.items)
    }

    UiStateHandler(
        state = uiState,
        onRetry = { viewModel.onInput(ItemListViewModel.Input.Retry) }
    ) { items ->
        LazyColumn {
            items(items, key = { it.id }) { item ->
                ItemCard(item = item)
            }
        }
    }
}
```

---

## Data Patterns

### Data Class Layer Transformation

**Purpose**: Transform data formats between different layers.

```kotlin
// ═══════════════════════════════════════════════════════════════
// DOMAIN MODEL - Used by business logic
// ═══════════════════════════════════════════════════════════════
data class User(
    val id: String,
    val name: String,
    val email: String,
    val avatarUrl: String?,
    val role: UserRole,
    val createdAt: Instant,
    val updatedAt: Instant
)

enum class UserRole { ADMIN, MEMBER, GUEST }

// ═══════════════════════════════════════════════════════════════
// ENTITY - Room database
// ═══════════════════════════════════════════════════════════════
@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "server_id") val serverId: String? = null,
    val name: String,
    val email: String,
    @ColumnInfo(name = "avatar_url") val avatarUrl: String?,
    val role: String,
    @ColumnInfo(name = "created_at") val createdAt: Long,
    @ColumnInfo(name = "updated_at") val updatedAt: Long,
    @ColumnInfo(name = "sync_status") val syncStatus: SyncStatus = SyncStatus.SYNCED
)

// ═══════════════════════════════════════════════════════════════
// DTO - API communication
// ═══════════════════════════════════════════════════════════════
@Serializable
data class UserDto(
    val id: String,
    val name: String,
    val email: String,
    @SerialName("avatar_url")
    val avatarUrl: String? = null,
    val role: String,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("updated_at")
    val updatedAt: String
)

// ═══════════════════════════════════════════════════════════════
// MAPPERS
// ═══════════════════════════════════════════════════════════════
// Entity → Domain
fun UserEntity.toDomain() = User(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    role = UserRole.valueOf(role),
    createdAt = Instant.ofEpochMilli(createdAt),
    updatedAt = Instant.ofEpochMilli(updatedAt)
)

// Domain → Entity
fun User.toEntity(syncStatus: SyncStatus = SyncStatus.SYNCED) = UserEntity(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    role = role.name,
    createdAt = createdAt.toEpochMilli(),
    updatedAt = updatedAt.toEpochMilli(),
    syncStatus = syncStatus
)

// DTO → Domain
fun UserDto.toDomain() = User(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    role = UserRole.valueOf(role.uppercase()),
    createdAt = Instant.parse(createdAt),
    updatedAt = Instant.parse(updatedAt)
)

// DTO → Entity
fun UserDto.toEntity() = UserEntity(
    id = UUID.randomUUID().toString(),
    serverId = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    role = role.uppercase(),
    createdAt = Instant.parse(createdAt).toEpochMilli(),
    updatedAt = Instant.parse(updatedAt).toEpochMilli(),
    syncStatus = SyncStatus.SYNCED
)

// Domain → DTO
fun User.toDto() = UserDto(
    id = id,
    name = name,
    email = email,
    avatarUrl = avatarUrl,
    role = role.name.lowercase(),
    createdAt = createdAt.toString(),
    updatedAt = updatedAt.toString()
)
```

---

## Concurrency Patterns

### Structured Concurrency Pattern

**Purpose**: Safely manage Coroutine lifecycle.

```kotlin
// ═══════════════════════════════════════════════════════════════
// VIEWMODEL SCOPE - Automatically follows ViewModel lifecycle
// ═══════════════════════════════════════════════════════════════
@HiltViewModel
class DataViewModel @Inject constructor(
    private val repository: DataRepository
) : ViewModel() {

    init {
        // This coroutine is automatically cancelled when ViewModel is cleared
        viewModelScope.launch {
            repository.getData().collect { data ->
                _output.update { it.copy(data = data) }
            }
        }
    }

    fun loadData() = viewModelScope.launch {
        // Automatic cancellation management
    }
}

// ═══════════════════════════════════════════════════════════════
// PARALLEL OPERATIONS
// ═══════════════════════════════════════════════════════════════
suspend fun loadDashboard(): DashboardData = coroutineScope {
    // Execute multiple operations in parallel
    val userDeferred = async { userRepository.getCurrentUser() }
    val statsDeferred = async { statsRepository.getStats() }
    val notificationsDeferred = async { notificationRepository.getUnread() }

    // Wait for all results
    DashboardData(
        user = userDeferred.await(),
        stats = statsDeferred.await(),
        notifications = notificationsDeferred.await()
    )
}

// ═══════════════════════════════════════════════════════════════
// TIMEOUT HANDLING
// ═══════════════════════════════════════════════════════════════
suspend fun fetchWithTimeout(): Result<Data> = try {
    withTimeout(10_000) {
        Result.success(api.fetchData())
    }
} catch (e: TimeoutCancellationException) {
    Result.failure(NetworkException("Request timed out"))
}

// ═══════════════════════════════════════════════════════════════
// RETRY WITH EXPONENTIAL BACKOFF
// ═══════════════════════════════════════════════════════════════
suspend fun <T> retryWithBackoff(
    times: Int = 3,
    initialDelay: Long = 100,
    maxDelay: Long = 10_000,
    factor: Double = 2.0,
    block: suspend () -> T
): T {
    var currentDelay = initialDelay
    repeat(times - 1) {
        try {
            return block()
        } catch (e: Exception) {
            // Can filter which exceptions to retry here
        }
        delay(currentDelay)
        currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
    }
    return block() // Last attempt
}

// Usage
suspend fun syncData() = retryWithBackoff(times = 3) {
    api.sync()
}

// ═══════════════════════════════════════════════════════════════
// FLOW OPERATORS
// ═══════════════════════════════════════════════════════════════
class SearchViewModel @Inject constructor(
    private val searchRepository: SearchRepository
) : ViewModel() {

    private val searchQuery = MutableStateFlow("")

    val searchResults: StateFlow<List<SearchResult>> = searchQuery
        .debounce(300) // Debounce
        .distinctUntilChanged() // Avoid duplicate searches
        .flatMapLatest { query ->
            if (query.isBlank()) {
                flowOf(emptyList())
            } else {
                searchRepository.search(query)
                    .catch { emit(emptyList()) } // Error handling
            }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    fun onSearchQueryChange(query: String) {
        searchQuery.value = query
    }
}
```

---

## Error Handling Patterns

### Result Pattern

**Purpose**: Unified error handling, avoid scattered try-catch.

```kotlin
// ═══════════════════════════════════════════════════════════════
// CUSTOM ERROR TYPES
// ═══════════════════════════════════════════════════════════════
sealed class AppError : Exception() {
    // Network errors
    sealed class Network : AppError() {
        data object NoConnection : Network()
        data object Timeout : Network()
        data class ServerError(val code: Int) : Network()
    }

    // Business errors
    sealed class Business : AppError() {
        data object UserNotFound : Business()
        data object InvalidInput : Business()
        data class Validation(override val message: String) : Business()
    }

    // Local errors
    sealed class Local : AppError() {
        data object DatabaseError : Local()
        data object FileNotFound : Local()
    }
}

// ═══════════════════════════════════════════════════════════════
// SAFE API CALL WRAPPER
// ═══════════════════════════════════════════════════════════════
suspend fun <T> safeApiCall(call: suspend () -> T): Result<T> = try {
    Result.success(call())
} catch (e: ClientRequestException) {
    when (e.response.status.value) {
        401 -> Result.failure(AppError.Business.UserNotFound)
        in 400..499 -> Result.failure(AppError.Network.ServerError(e.response.status.value))
        else -> Result.failure(AppError.Network.ServerError(e.response.status.value))
    }
} catch (e: ServerResponseException) {
    Result.failure(AppError.Network.ServerError(e.response.status.value))
} catch (e: IOException) {
    Result.failure(AppError.Network.NoConnection)
} catch (e: TimeoutCancellationException) {
    Result.failure(AppError.Network.Timeout)
}

// ═══════════════════════════════════════════════════════════════
// RESULT EXTENSIONS
// ═══════════════════════════════════════════════════════════════
inline fun <T> Result<T>.onSuccessSuspend(action: suspend (T) -> Unit): Result<T> {
    if (isSuccess) {
        runBlocking { action(getOrThrow()) }
    }
    return this
}

fun <T> Result<T>.toUiMessage(): String = when (val error = exceptionOrNull()) {
    is AppError.Network.NoConnection -> "No internet connection"
    is AppError.Network.Timeout -> "Request timed out"
    is AppError.Network.ServerError -> "Server error (${error.code})"
    is AppError.Business.UserNotFound -> "User not found"
    is AppError.Business.InvalidInput -> "Invalid input"
    is AppError.Business.Validation -> error.message
    is AppError.Local.DatabaseError -> "Database error"
    is AppError.Local.FileNotFound -> "File not found"
    else -> "An unexpected error occurred"
}

// ═══════════════════════════════════════════════════════════════
// USAGE IN VIEWMODEL
// ═══════════════════════════════════════════════════════════════
fun submit() = viewModelScope.launch {
    _output.update { it.copy(isLoading = true, error = null) }

    repository.submitData(data)
        .onSuccess {
            _effect.send(Effect.NavigateBack)
        }
        .onFailure { error ->
            _output.update {
                it.copy(
                    isLoading = false,
                    error = Result.failure<Unit>(error).toUiMessage()
                )
            }
        }
}
```

---

## Navigation Patterns

### Type-Safe Navigation

**Purpose**: Build a type-safe navigation system.

```kotlin
// ═══════════════════════════════════════════════════════════════
// ROUTE DEFINITIONS
// ═══════════════════════════════════════════════════════════════
sealed class Route(val route: String) {
    data object Home : Route("home")
    data object Settings : Route("settings")

    data object UserList : Route("users")
    data class UserDetail(val userId: String) : Route("users/$userId") {
        companion object {
            const val ROUTE_PATTERN = "users/{userId}"
            const val ARG_USER_ID = "userId"
        }
    }

    data class EditUser(val userId: String) : Route("users/$userId/edit") {
        companion object {
            const val ROUTE_PATTERN = "users/{userId}/edit"
            const val ARG_USER_ID = "userId"
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// NAV GRAPH
// ═══════════════════════════════════════════════════════════════
@Composable
fun AppNavGraph(
    navController: NavHostController = rememberNavController()
) {
    NavHost(
        navController = navController,
        startDestination = Route.Home.route
    ) {
        composable(Route.Home.route) {
            HomeScreen(
                onNavigateToUsers = { navController.navigate(Route.UserList.route) },
                onNavigateToSettings = { navController.navigate(Route.Settings.route) }
            )
        }

        composable(Route.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Route.UserList.route) {
            UserListScreen(
                onNavigateToDetail = { userId ->
                    navController.navigate(Route.UserDetail(userId).route)
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(
            route = Route.UserDetail.ROUTE_PATTERN,
            arguments = listOf(
                navArgument(Route.UserDetail.ARG_USER_ID) { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val userId = backStackEntry.arguments?.getString(Route.UserDetail.ARG_USER_ID) ?: return@composable
            UserDetailScreen(
                userId = userId,
                onNavigateToEdit = {
                    navController.navigate(Route.EditUser(userId).route)
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(
            route = Route.EditUser.ROUTE_PATTERN,
            arguments = listOf(
                navArgument(Route.EditUser.ARG_USER_ID) { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val userId = backStackEntry.arguments?.getString(Route.EditUser.ARG_USER_ID) ?: return@composable
            EditUserScreen(
                userId = userId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// NAVIGATION EXTENSIONS
// ═══════════════════════════════════════════════════════════════
fun NavController.navigateWithPopUp(
    route: String,
    popUpTo: String,
    inclusive: Boolean = false
) {
    navigate(route) {
        popUpTo(popUpTo) {
            this.inclusive = inclusive
        }
    }
}

fun NavController.navigateSingleTop(route: String) {
    navigate(route) {
        launchSingleTop = true
    }
}

// Usage: Clear back stack after login
fun NavController.navigateToHomeAfterLogin() {
    navigateWithPopUp(
        route = Route.Home.route,
        popUpTo = Route.Home.route,
        inclusive = true
    )
}
```
