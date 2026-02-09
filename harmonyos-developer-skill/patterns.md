# HarmonyOS Design Patterns

Design patterns and best practices based on Arcana HarmonyOS architecture. All patterns use ArkTS strict mode (no any, no unknown, no spread operators, no computed properties).

## Table of Contents

1. [Architecture Patterns](#architecture-patterns)
2. [ArkTS Workaround Patterns](#arkts-workaround-patterns)
3. [UI Patterns](#ui-patterns)
4. [Data Patterns](#data-patterns)
5. [Concurrency Patterns](#concurrency-patterns)
6. [Error Handling Patterns](#error-handling-patterns)
7. [Navigation Patterns](#navigation-patterns)
8. [DI Patterns](#di-patterns)
9. [Offline-First Patterns](#offline-first-patterns)

---

## Architecture Patterns

### MVVM Input/Output/Effect Pattern

**Purpose**: Establish clear unidirectional data flow with type-safe event handling using discriminated unions.

```
+---------------------------------------------------------------+
|                        ViewModel                                |
|  +----------+    +---------------+    +-----------+            |
|  |  Input   | -> |   Process     | -> |  Output   |            |
|  | (Event)  |    |  (Business)   |    |  (State)  |            |
|  +----------+    +---------------+    +-----------+            |
|        ^                                   |                    |
|        |                                   v                    |
|  +---------------------------------------------------------+   |
|  |                      Page/Component                      |   |
|  |  User Action -> Input    |    Output -> UI State         |   |
|  +---------------------------------------------------------+   |
|                                                                 |
|  +-----------+                                                  |
|  |  Effect   |  One-time events (navigation, toast, etc.)      |
|  +-----------+                                                  |
+---------------------------------------------------------------+
```

**Key Rules**:
1. Input is a discriminated union (class with static type constants)
2. Output is immutable (use factory methods, no spread)
3. Effect is for one-time events only (navigation, toast)
4. Single onInput() entry point for all user actions
5. ViewModel never imports ArkUI or HarmonyOS SDK

See `patterns/mvvm-input-output.md` for detailed implementation.

---

### Repository Pattern (Offline-First)

**Purpose**: Unify data access with local-first strategy.

```
+---------------------------------------------------------------+
| Domain Layer: Repository Interface                              |
|   interface UserRepository {                                    |
|     getUsers(): Promise<Result<Array<User>, AppError>>         |
|     createUser(user: User): Promise<Result<User, AppError>>   |
|   }                                                             |
+---------------------------------------------------------------+
| Data Layer: Repository Implementation                           |
|   class UserRepositoryImpl implements UserRepository {          |
|     READ  -> Local DB (single source of truth)                 |
|     WRITE -> Local DB first + schedule sync                    |
|     SYNC  -> Upload pending + download remote                  |
|   }                                                             |
+---------------------------------------------------------------+
```

**Structure**:
```typescript
@injectable()
export class ItemRepositoryImpl implements ItemRepository {
  private localSource: ItemLocalSource
  private apiService: ItemApiService
  private networkMonitor: NetworkMonitor

  constructor(
    localSource: ItemLocalSource,
    apiService: ItemApiService,
    networkMonitor: NetworkMonitor
  ) {
    this.localSource = localSource
    this.apiService = apiService
    this.networkMonitor = networkMonitor
  }

  // Read: always from local (single source of truth)
  async getItems(): Promise<Result<Array<Item>, AppError>> {
    const entities = await this.localSource.getAll()
    const items = entities.map((entity: ItemEntity) => entity.toDomain())
    return Result.success(items)
  }

  // Write: local first, then schedule sync
  async createItem(item: Item): Promise<Result<Item, AppError>> {
    const entity = ItemEntity.fromDomain(item)
    entity.syncStatus = SyncStatus.PENDING_CREATE
    entity.updatedAt = Date.now()
    await this.localSource.insert(entity)

    if (this.networkMonitor.isOnline()) {
      await this.syncPendingChanges()
    }

    return Result.success(item)
  }

  // Sync: upload pending, download remote
  async syncPendingChanges(): Promise<void> {
    const pendingItems = await this.localSource.getPendingSync()

    for (const item of pendingItems) {
      switch (item.syncStatus) {
        case SyncStatus.PENDING_CREATE:
          await this.syncCreate(item)
          break
        case SyncStatus.PENDING_UPDATE:
          await this.syncUpdate(item)
          break
        case SyncStatus.PENDING_DELETE:
          await this.syncDelete(item)
          break
        default:
          break
      }
    }
  }

  private async syncCreate(entity: ItemEntity): Promise<void> {
    const result = await this.apiService.create(entity.toDto())
    result.fold(
      (response: ItemDto) => {
        this.localSource.updateSyncStatus(entity.id, SyncStatus.SYNCED)
      },
      (error: AppError) => {
        this.localSource.updateSyncStatus(entity.id, SyncStatus.SYNC_FAILED)
      }
    )
  }

  private async syncUpdate(entity: ItemEntity): Promise<void> {
    const result = await this.apiService.update(entity.id, entity.toDto())
    result.fold(
      (response: ItemDto) => {
        this.localSource.updateSyncStatus(entity.id, SyncStatus.SYNCED)
      },
      (error: AppError) => {
        this.localSource.updateSyncStatus(entity.id, SyncStatus.SYNC_FAILED)
      }
    )
  }

  private async syncDelete(entity: ItemEntity): Promise<void> {
    const result = await this.apiService.delete(entity.id)
    result.fold(
      (success: boolean) => {
        this.localSource.delete(entity.id)
      },
      (error: AppError) => {
        if (error.code === AppError.NOT_FOUND) {
          this.localSource.delete(entity.id)
        } else {
          this.localSource.updateSyncStatus(entity.id, SyncStatus.SYNC_FAILED)
        }
      }
    )
  }
}
```

---

### Service Layer Pattern

**Purpose**: Encapsulate business logic, coordinate multiple repositories.

```typescript
@injectable()
export class UserService {
  private userRepository: UserRepository
  private authRepository: AuthRepository
  private analyticsService: AnalyticsService

  constructor(
    userRepository: UserRepository,
    authRepository: AuthRepository,
    analyticsService: AnalyticsService
  ) {
    this.userRepository = userRepository
    this.authRepository = authRepository
    this.analyticsService = analyticsService
  }

  async createUserWithValidation(
    name: string,
    email: string
  ): Promise<Result<User, AppError>> {
    // 1. Validate business rules
    const nameResult = UserValidator.validateName(name)
    if (nameResult.isFailure()) {
      return Result.failure(nameResult.getErrorOrNull() as AppError)
    }

    const emailResult = AuthValidator.validateEmail(email)
    if (emailResult.isFailure()) {
      return Result.failure(emailResult.getErrorOrNull() as AppError)
    }

    // 2. Check auth
    const isLoggedIn = await this.authRepository.isLoggedIn()
    if (!isLoggedIn) {
      return Result.failure(new AppError(AppError.UNAUTHORIZED, 'Must be logged in'))
    }

    // 3. Create user
    const user = new User(
      this.generateId(),
      name.trim(),
      email.toLowerCase().trim(),
      undefined,
      Date.now()
    )

    const result = await this.userRepository.createUser(user)

    // 4. Track analytics on success
    if (result.isSuccess()) {
      this.analyticsService.track('user_created', user.id)
    }

    return result
  }

  private generateId(): string {
    return `user_${Date.now()}_${Math.floor(Math.random() * 10000)}`
  }
}
```

---

## ArkTS Workaround Patterns

### Pattern: Class-Based Constants (No Object Literals)

```typescript
// WRONG - Object literal
const STATUS = { ACTIVE: 'active', INACTIVE: 'inactive' }

// CORRECT - Class-based constants
export class Status {
  static readonly ACTIVE = 'active'
  static readonly INACTIVE = 'inactive'
  static readonly SUSPENDED = 'suspended'

  // Validation helper
  static isValid(status: string): boolean {
    return status === Status.ACTIVE ||
           status === Status.INACTIVE ||
           status === Status.SUSPENDED
  }

  // All values (for iteration)
  static allValues(): Array<string> {
    const values = new Array<string>()
    values.push(Status.ACTIVE)
    values.push(Status.INACTIVE)
    values.push(Status.SUSPENDED)
    return values
  }
}
```

### Pattern: Factory Methods (No Spread Operator)

```typescript
// WRONG - Spread for immutable update
const updated = { ...state, isLoading: true }

// CORRECT - Factory method on class
export class FormState {
  readonly name: string
  readonly email: string
  readonly isLoading: boolean
  readonly errors: Map<string, string>

  constructor(
    name: string,
    email: string,
    isLoading: boolean,
    errors: Map<string, string>
  ) {
    this.name = name
    this.email = email
    this.isLoading = isLoading
    this.errors = errors
  }

  static initial(): FormState {
    return new FormState('', '', false, new Map<string, string>())
  }

  withName(name: string): FormState {
    return new FormState(name, this.email, this.isLoading, this.errors)
  }

  withEmail(email: string): FormState {
    return new FormState(this.name, email, this.isLoading, this.errors)
  }

  withLoading(loading: boolean): FormState {
    return new FormState(this.name, this.email, loading, this.errors)
  }

  withError(field: string, message: string): FormState {
    const newErrors = new Map<string, string>(this.errors)
    newErrors.set(field, message)
    return new FormState(this.name, this.email, this.isLoading, newErrors)
  }

  withoutError(field: string): FormState {
    const newErrors = new Map<string, string>(this.errors)
    newErrors.delete(field)
    return new FormState(this.name, this.email, this.isLoading, newErrors)
  }
}
```

### Pattern: Builder for Declarative APIs

```typescript
export class HttpRequestBuilder {
  private _url: string = ''
  private _method: string = 'GET'
  private _headers: Map<string, string> = new Map<string, string>()
  private _body: string | undefined = undefined
  private _timeoutMs: number = 30000

  url(url: string): HttpRequestBuilder {
    this._url = url
    return this
  }

  method(method: string): HttpRequestBuilder {
    this._method = method
    return this
  }

  header(key: string, value: string): HttpRequestBuilder {
    this._headers.set(key, value)
    return this
  }

  body(body: string): HttpRequestBuilder {
    this._body = body
    return this
  }

  timeout(ms: number): HttpRequestBuilder {
    this._timeoutMs = ms
    return this
  }

  build(): HttpRequest {
    return new HttpRequest(
      this._url,
      this._method,
      this._headers,
      this._body,
      this._timeoutMs
    )
  }
}

// Usage:
const request = new HttpRequestBuilder()
  .url('https://api.example.com/users')
  .method('POST')
  .header('Content-Type', 'application/json')
  .header('Authorization', `Bearer ${token}`)
  .body(JSON.stringify(userData))
  .timeout(10000)
  .build()
```

### Pattern: Discriminated Unions (No Sealed Classes)

```typescript
// ArkTS has no sealed class. Use discriminated union with string literal type field.

export class ActionType {
  static readonly INCREMENT = 'INCREMENT'
  static readonly DECREMENT = 'DECREMENT'
  static readonly RESET = 'RESET'
  static readonly SET_VALUE = 'SET_VALUE'
}

export class Action {
  readonly type: string
  readonly value: number | undefined

  private constructor(type: string, value: number | undefined) {
    this.type = type
    this.value = value
  }

  static increment(): Action {
    return new Action(ActionType.INCREMENT, undefined)
  }

  static decrement(): Action {
    return new Action(ActionType.DECREMENT, undefined)
  }

  static reset(): Action {
    return new Action(ActionType.RESET, undefined)
  }

  static setValue(value: number): Action {
    return new Action(ActionType.SET_VALUE, value)
  }
}

// Handler with exhaustive switch
function reduce(state: number, action: Action): number {
  switch (action.type) {
    case ActionType.INCREMENT:
      return state + 1
    case ActionType.DECREMENT:
      return state - 1
    case ActionType.RESET:
      return 0
    case ActionType.SET_VALUE:
      return action.value as number
    default:
      return state
  }
}
```

### Pattern: String Literal Keys for Maps

```typescript
// WRONG - Computed property
const obj = { [dynamicKey]: value }

// CORRECT - Map with string literal keys
export class PreferenceKeys {
  static readonly THEME = 'pref_theme'
  static readonly LANGUAGE = 'pref_language'
  static readonly NOTIFICATIONS = 'pref_notifications'
  static readonly LAST_SYNC = 'pref_last_sync'
}

export class PreferenceManager {
  private preferences: Map<string, string> = new Map<string, string>()

  get(key: string): string | undefined {
    return this.preferences.get(key)
  }

  set(key: string, value: string): void {
    this.preferences.set(key, value)
  }

  getTheme(): string {
    return this.get(PreferenceKeys.THEME) ?? 'system'
  }

  setTheme(theme: string): void {
    this.set(PreferenceKeys.THEME, theme)
  }
}
```

---

## UI Patterns

### Loading/Error/Empty State Pattern

```typescript
// Reusable state components for ArkUI

@Component
export struct LoadingState {
  @Prop message: string = ''

  build() {
    Column() {
      LoadingProgress()
        .width(48)
        .height(48)
      if (this.message.length > 0) {
        Text(this.message)
          .fontSize(14)
          .fontColor(Color.Gray)
          .margin({ top: 16 })
      }
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
  }
}

@Component
export struct ErrorState {
  @Prop message: string = ''
  onRetry: () => void = () => {}

  build() {
    Column() {
      Image($r('app.media.ic_error'))
        .width(64)
        .height(64)
        .fillColor(Color.Red)
      Text(this.message)
        .fontSize(16)
        .fontColor(Color.Gray)
        .margin({ top: 16 })
        .textAlign(TextAlign.Center)
      Button($r('app.string.retry'))
        .margin({ top: 24 })
        .onClick(() => {
          this.onRetry()
        })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
    .padding(32)
  }
}

@Component
export struct EmptyState {
  @Prop title: string = ''
  @Prop description: string = ''
  @Prop actionLabel: string = ''
  onAction: () => void = () => {}

  build() {
    Column() {
      Image($r('app.media.ic_empty'))
        .width(96)
        .height(96)
      Text(this.title)
        .fontSize(18)
        .fontWeight(FontWeight.Medium)
        .margin({ top: 24 })
      Text(this.description)
        .fontSize(14)
        .fontColor(Color.Gray)
        .margin({ top: 8 })
        .textAlign(TextAlign.Center)
      if (this.actionLabel.length > 0) {
        Button(this.actionLabel)
          .margin({ top: 24 })
          .onClick(() => {
            this.onAction()
          })
      }
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
    .padding(32)
  }
}
```

### Stateless Component Pattern

```typescript
// Separate stateful page from stateless content component

// Stateful page (connects to ViewModel)
@Entry
@Component
struct FeaturePage {
  @State private output: FeatureOutput = FeatureOutput.initial()
  private viewModel: FeatureViewModel = AppContainer.resolve(ServiceIdentifiers.FEATURE_VIEW_MODEL)

  aboutToAppear(): void {
    this.viewModel.setEffectCallback((effect: FeatureEffect) => {
      this.handleEffect(effect)
    })
    this.viewModel.onInput(FeatureInput.load())
    this.syncOutput()
  }

  private syncOutput(): void {
    this.output = this.viewModel.output
  }

  build() {
    // Delegate to stateless content
    FeatureContent({
      output: this.output,
      onInput: (input: FeatureInput) => {
        this.viewModel.onInput(input)
        this.syncOutput()
      }
    })
  }
}

// Stateless content (pure UI, easy to test and preview)
@Component
struct FeatureContent {
  @Prop output: FeatureOutput = FeatureOutput.initial()
  onInput: (input: FeatureInput) => void = (input: FeatureInput) => {}

  build() {
    Column() {
      if (this.output.isLoading) {
        LoadingState()
      } else if (this.output.error !== undefined) {
        ErrorState({
          message: this.output.error,
          onRetry: () => { this.onInput(FeatureInput.retry()) }
        })
      } else if (this.output.isEmpty) {
        EmptyState({
          title: 'No items yet',
          description: 'Add your first item to get started',
          actionLabel: 'Add Item',
          onAction: () => { this.onInput(FeatureInput.addItem()) }
        })
      } else {
        // Content
        List() {
          LazyForEach(new ItemDataSource(this.output.items), (item: Item) => {
            ListItem() {
              this.ItemRow(item)
            }
          }, (item: Item) => item.id)
        }
      }
    }
    .width('100%')
    .height('100%')
  }
}
```

---

## Data Patterns

### Data Class Layer Transformation

```typescript
// Domain Model (pure, no SDK dependencies)
export class User {
  readonly id: string
  readonly name: string
  readonly email: string
  readonly avatarUrl: string | undefined
  readonly createdAt: number

  constructor(id: string, name: string, email: string, avatarUrl: string | undefined, createdAt: number) {
    this.id = id
    this.name = name
    this.email = email
    this.avatarUrl = avatarUrl
    this.createdAt = createdAt
  }
}

// Entity (RelationalStore persistence)
export class UserEntity {
  id: string = ''
  name: string = ''
  email: string = ''
  avatarUrl: string | undefined = undefined
  syncStatus: string = SyncStatus.SYNCED
  createdAt: number = 0
  updatedAt: number = 0

  toDomain(): User {
    return new User(this.id, this.name, this.email, this.avatarUrl, this.createdAt)
  }

  static fromDomain(user: User): UserEntity {
    const entity = new UserEntity()
    entity.id = user.id
    entity.name = user.name
    entity.email = user.email
    entity.avatarUrl = user.avatarUrl
    entity.createdAt = user.createdAt
    entity.updatedAt = Date.now()
    return entity
  }

  toDto(): UserDto {
    return new UserDto(this.id, this.name, this.email, this.avatarUrl)
  }

  static fromResultSet(resultSet: relationalStore.ResultSet): UserEntity {
    const entity = new UserEntity()
    entity.id = resultSet.getString(resultSet.getColumnIndex('id'))
    entity.name = resultSet.getString(resultSet.getColumnIndex('name'))
    entity.email = resultSet.getString(resultSet.getColumnIndex('email'))
    entity.avatarUrl = resultSet.getString(resultSet.getColumnIndex('avatar_url'))
    entity.syncStatus = resultSet.getString(resultSet.getColumnIndex('sync_status'))
    entity.createdAt = resultSet.getLong(resultSet.getColumnIndex('created_at'))
    entity.updatedAt = resultSet.getLong(resultSet.getColumnIndex('updated_at'))
    return entity
  }
}

// DTO (API communication)
export class UserDto {
  readonly id: string
  readonly name: string
  readonly email: string
  readonly avatarUrl: string | undefined

  constructor(id: string, name: string, email: string, avatarUrl: string | undefined) {
    this.id = id
    this.name = name
    this.email = email
    this.avatarUrl = avatarUrl
  }

  toDomain(): User {
    return new User(this.id, this.name, this.email, this.avatarUrl, Date.now())
  }

  toEntity(): UserEntity {
    const entity = new UserEntity()
    entity.id = this.id
    entity.name = this.name
    entity.email = this.email
    entity.avatarUrl = this.avatarUrl
    entity.syncStatus = SyncStatus.SYNCED
    entity.createdAt = Date.now()
    entity.updatedAt = Date.now()
    return entity
  }
}
```

---

## Concurrency Patterns

### Async Operation with Timeout

```typescript
export class AsyncHelper {
  static async withTimeout<T>(
    operation: () => Promise<T>,
    timeoutMs: number
  ): Promise<Result<T, AppError>> {
    return new Promise<Result<T, AppError>>((resolve) => {
      let completed = false

      const timer = setTimeout(() => {
        if (!completed) {
          completed = true
          resolve(Result.failure(new AppError(AppError.TIMEOUT, 'Operation timed out')))
        }
      }, timeoutMs)

      operation().then((value: T) => {
        if (!completed) {
          completed = true
          clearTimeout(timer)
          resolve(Result.success(value))
        }
      }).catch((error: Error) => {
        if (!completed) {
          completed = true
          clearTimeout(timer)
          resolve(Result.failure(new AppError(AppError.UNKNOWN, error.message)))
        }
      })
    })
  }
}
```

### Retry with Exponential Backoff

```typescript
export class RetryHelper {
  static async withBackoff<T>(
    operation: () => Promise<Result<T, AppError>>,
    maxRetries: number,
    initialDelayMs: number
  ): Promise<Result<T, AppError>> {
    let currentDelay = initialDelayMs
    let lastError: AppError | undefined = undefined

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const result = await operation()
      if (result.isSuccess()) {
        return result
      }

      lastError = result.getErrorOrNull() as AppError

      // Do not retry auth errors
      if (lastError.requiresReauth) {
        return result
      }

      if (attempt < maxRetries) {
        await new Promise<void>((resolve) => setTimeout(resolve, currentDelay))
        currentDelay = Math.min(currentDelay * 2, 30000) // Max 30 seconds
      }
    }

    return Result.failure(lastError as AppError)
  }
}
```

---

## Error Handling Patterns

### Railway-Oriented Programming with Result<T, E>

```typescript
// Chain operations that can fail
async function processUserRegistration(
  name: string,
  email: string,
  password: string
): Promise<Result<User, AppError>> {
  // Step 1: Validate name
  const nameResult = UserValidator.validateName(name)
  if (nameResult.isFailure()) {
    return Result.failure(nameResult.getErrorOrNull() as AppError)
  }

  // Step 2: Validate email
  const emailResult = AuthValidator.validateEmail(email)
  if (emailResult.isFailure()) {
    return Result.failure(emailResult.getErrorOrNull() as AppError)
  }

  // Step 3: Validate password
  const passwordResult = AuthValidator.validatePassword(password)
  if (passwordResult.isFailure()) {
    return Result.failure(passwordResult.getErrorOrNull() as AppError)
  }

  // Step 4: Create user
  const user = new User(
    generateId(),
    nameResult.getOrNull() as string,
    emailResult.getOrNull() as string,
    undefined,
    Date.now()
  )

  // Step 5: Save to repository
  return await userRepository.createUser(user)
}
```

### Safe API Call Wrapper

```typescript
export class SafeCall {
  static async execute<T>(
    operation: () => Promise<T>
  ): Promise<Result<T, AppError>> {
    try {
      const value = await operation()
      return Result.success(value)
    } catch (error) {
      if (error instanceof Error) {
        const message = error.message
        if (message.includes('network') || message.includes('timeout')) {
          return Result.failure(new AppError(AppError.NETWORK, message))
        }
        if (message.includes('401') || message.includes('unauthorized')) {
          return Result.failure(new AppError(AppError.UNAUTHORIZED, message))
        }
        return Result.failure(new AppError(AppError.UNKNOWN, message))
      }
      return Result.failure(new AppError(AppError.UNKNOWN, 'Unknown error occurred'))
    }
  }
}
```

---

## Navigation Patterns

### Type-Safe Navigation with Params

```typescript
// core/navigation/NavigationRoutes.ets
export class NavigationRoutes {
  static readonly HOME = 'pages/HomePage'
  static readonly LOGIN = 'pages/LoginPage'
  static readonly USER_LIST = 'pages/UserListPage'
  static readonly USER_DETAIL = 'pages/UserDetailPage'
  static readonly SETTINGS = 'pages/SettingsPage'
}

// core/navigation/NavigationParams.ets
export class NavigationParamKeys {
  static readonly USER_ID = 'userId'
  static readonly ITEM_ID = 'itemId'
  static readonly EDIT_MODE = 'editMode'
}

// Usage in ViewModel effect handler
private handleEffect(effect: Effect): void {
  switch (effect.type) {
    case EffectType.NAVIGATE:
      NavigationHelper.pushUrl(effect.payload as string, undefined)
      break
    case EffectType.NAVIGATE_WITH_PARAMS:
      const params = new Map<string, string>()
      params.set(NavigationParamKeys.USER_ID, effect.payload as string)
      NavigationHelper.pushUrl(NavigationRoutes.USER_DETAIL, params)
      break
    case EffectType.NAVIGATE_BACK:
      NavigationHelper.back()
      break
    default:
      break
  }
}

// Receiving params in destination page
@Entry
@Component
struct UserDetailPage {
  @State private userId: string = ''

  aboutToAppear(): void {
    const params = NavigationHelper.getParams<Record<string, string>>()
    if (params !== undefined) {
      this.userId = params[NavigationParamKeys.USER_ID] ?? ''
    }
  }
}
```

---

## DI Patterns

### Container Registration Strategy

```typescript
// Singletons: Core services, repositories, network monitor
// Transient: ViewModels (new instance per page)

export class AppContainer {
  static initialize(): void {
    const c = this.container

    // SINGLETONS - shared across app lifecycle
    c.bindSingleton(ServiceIdentifiers.NETWORK_MONITOR, () => new NetworkMonitor())
    c.bindSingleton(ServiceIdentifiers.SECURITY_SERVICE, () => new SecurityService())
    c.bindSingleton(ServiceIdentifiers.SYNC_MANAGER, () => {
      return new SyncManager(c.resolve(ServiceIdentifiers.NETWORK_MONITOR))
    })

    // SINGLETONS - Repositories (one instance, manages DB connection)
    c.bindSingleton(ServiceIdentifiers.USER_REPOSITORY, () => {
      return new UserRepositoryImpl(
        new UserLocalSource(),
        new UserApiService(),
        c.resolve(ServiceIdentifiers.NETWORK_MONITOR)
      )
    })

    // TRANSIENT - ViewModels (new per page, avoids stale state)
    c.bind(ServiceIdentifiers.USER_LIST_VIEW_MODEL, () => {
      return new UserListViewModel(
        c.resolve(ServiceIdentifiers.USER_REPOSITORY)
      )
    })
  }
}
```

### Lifecycle Management Pattern

```typescript
// @postConstruct equivalent: aboutToAppear in @Component
// @preDestroy equivalent: aboutToDisappear in @Component

@Entry
@Component
struct FeaturePage {
  private viewModel: FeatureViewModel = AppContainer.resolve(ServiceIdentifiers.FEATURE_VIEW_MODEL)

  // Equivalent to @postConstruct
  aboutToAppear(): void {
    this.viewModel.initialize()
  }

  // Equivalent to @preDestroy
  aboutToDisappear(): void {
    this.viewModel.cleanup()
  }
}
```

---

## Offline-First Patterns

### Three-Layer Cache Strategy

```typescript
// L1: Memory (LRU Cache) - <1ms access
// L2: Local DB (RelationalStore) - <10ms access
// L3: Remote API - network latency

export class CacheManager<V> {
  private memoryCache: Map<string, CacheEntry<V>> = new Map()
  private maxSize: number
  private ttlMs: number

  constructor(maxSize: number, ttlMs: number) {
    this.maxSize = maxSize
    this.ttlMs = ttlMs
  }

  get(key: string): V | undefined {
    const entry = this.memoryCache.get(key)
    if (entry !== undefined && !entry.isExpired(this.ttlMs)) {
      return entry.value
    }
    if (entry !== undefined) {
      this.memoryCache.delete(key) // Clean expired
    }
    return undefined
  }

  set(key: string, value: V): void {
    if (this.memoryCache.size >= this.maxSize) {
      // Evict oldest entry
      const firstKey = this.memoryCache.keys().next().value
      if (firstKey !== undefined) {
        this.memoryCache.delete(firstKey)
      }
    }
    this.memoryCache.set(key, new CacheEntry(value, Date.now()))
  }

  invalidate(key: string): void {
    this.memoryCache.delete(key)
  }

  invalidateAll(): void {
    this.memoryCache.clear()
  }
}

class CacheEntry<V> {
  readonly value: V
  readonly timestamp: number

  constructor(value: V, timestamp: number) {
    this.value = value
    this.timestamp = timestamp
  }

  isExpired(ttlMs: number): boolean {
    return Date.now() - this.timestamp > ttlMs
  }
}
```

### Optimistic Update Pattern

```typescript
// User sees immediate update, sync happens in background

async updateUserName(userId: string, newName: string): Promise<void> {
  // 1. Optimistic update: immediately update local + UI
  const user = await this.localSource.getById(userId)
  if (user !== undefined) {
    user.name = newName
    user.syncStatus = SyncStatus.PENDING_UPDATE
    user.updatedAt = Date.now()
    await this.localSource.update(user)
  }

  // 2. UI automatically reflects change (reads from local)

  // 3. Background sync
  if (this.networkMonitor.isOnline()) {
    const result = await this.apiService.updateUser(userId, user.toDto())
    result.fold(
      (response: UserDto) => {
        this.localSource.updateSyncStatus(userId, SyncStatus.SYNCED)
      },
      (error: AppError) => {
        // Keep PENDING_UPDATE for retry
        this.localSource.updateSyncStatus(userId, SyncStatus.SYNC_FAILED)
      }
    )
  }
  // If offline, WorkScheduler will retry later
}
```
