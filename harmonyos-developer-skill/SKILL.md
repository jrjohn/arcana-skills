---
name: harmonyos-developer-skill
description: HarmonyOS 5 (NEXT) development guide based on Arcana HarmonyOS enterprise architecture. Provides comprehensive support for Clean Architecture (four-layer), Offline-First design, ArkTS strict mode, ArkUI declarative UI, InversifyJS-style DI, MVVM Input/Output/Effect pattern, HUKS security, and WorkScheduler background sync. Suitable for HarmonyOS project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# HarmonyOS Developer Skill

Professional HarmonyOS 5 (NEXT) development skill based on [Arcana HarmonyOS](https://github.com/jrjohn/arcana-harmonyos) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Four Layers

```
+---------------------------------------------------------------+
|                     Presentation Layer                          |
|          ArkUI Pages + Components + ViewModels                 |
|          MVVM Input/Output/Effect Pattern                      |
+---------------------------------------------------------------+
|                       Domain Layer                              |
|     Models + Validators + Repository Interfaces + Services     |
|     PURE: Zero external dependencies                           |
+---------------------------------------------------------------+
|                        Data Layer                               |
|   API Service + Local Source + Repository Impl + Offline-First |
+---------------------------------------------------------------+
|                        Core Layer                               |
|  DI Container + Network Monitor + Sync Manager + Analytics     |
|  Security (HUKS) + Scheduling + i18n + Navigation              |
+---------------------------------------------------------------+
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation -> Domain -> Data -> Core
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces
- **Domain is PURE**: Zero external dependencies, no HarmonyOS SDK imports

---

## Quick Reference Card

### When Creating New Page:
```
1. [ ] Add route to NavigationRoutes (class-based constant)
2. [ ] Add page to router_map in module.json5
3. [ ] Create ViewModel with Input/Output/Effect pattern
4. [ ] Create Page component with @Entry decorator
5. [ ] Implement Loading/Error/Empty states
6. [ ] Add navigation wiring (pushUrl/back)
7. [ ] Register ViewModel in DI container
8. [ ] Verify mock data is non-empty
```

### When Creating New ViewModel:
```
1. [ ] Define Input sealed type (discriminated union)
2. [ ] Define Output interface with all state fields
3. [ ] Define Effect sealed type for one-time events
4. [ ] Use class-based constants (no object literals)
5. [ ] Implement onInput() dispatcher
6. [ ] Register as @injectable in DI container
7. [ ] Add factory method for immutable state updates
```

### When Creating New Repository:
```
1. [ ] Interface in domain/repository/ (PURE, no SDK imports)
2. [ ] Implementation in data/repository/ (offline-first)
3. [ ] Register in DI container (@injectable + bind)
4. [ ] Add mock data (NEVER empty!)
5. [ ] Verify ID consistency across repositories
6. [ ] Add sync status tracking (PENDING/SYNCED/SYNC_FAILED)
```

### Quick Diagnosis:
| Symptom | Likely Cause | Check Command |
|---------|--------------|---------------|
| Blank screen | Empty mock data | `grep "new Array()" entry/src/main/ets/data/` |
| Navigation crash | Missing route | Check router_map in module.json5 |
| Data not loading | ID mismatch | `grep "id:" entry/src/main/ets/data/repository/` |
| Click does nothing | Empty handler | `grep "() => {}" entry/src/main/ets/` |
| DI resolution fails | Missing binding | Check container.bind() calls |
| ArkTS compile error | Strict mode violation | Check for any/unknown/spread usage |

---

## Rules Priority

### CRITICAL (Must follow, violations cause Bug/Crash)
- ArkTS Strict Mode - No any, no unknown, no spread operators, no computed properties
- Zero-Null Policy - Repository stubs must not return null/empty
- Navigation Wiring - All routes must have registered page destinations
- ID Consistency - IDs must be consistent across repositories
- Offline Sync Integrity - PENDING status must be tracked and resolved
- DI Container Registration - All injectables must be explicitly bound

### IMPORTANT (Strongly recommended, affects quality)
- UI State Handling - Loading/Error/Empty states for all pages
- Mock Data Quality - Use realistic, varied mock data
- MVVM Input/Output/Effect - Follow standard pattern with discriminated unions
- Offline-First Strategy - Local DB as single source of truth
- Result<T,E> Error Handling - Railway-oriented, no throw

### RECOMMENDED (Suggested, improves UX)
- Animation Standards - Transition animations between pages
- Accessibility - Accessibility labels for all interactive elements
- Dark Mode Support - Proper color token adaptation
- i18n - All user-facing strings via $r('app.string.xxx')
- Background Sync - WorkScheduler for periodic sync

---

## Error Handling Pattern

### Result<T, E> - Railway-Oriented

```
+--------------+    +--------------+    +--------------+    +--------------+
|  Repository  | -> |  ViewModel   | -> |   Output     | -> |    Page      |
|  Result<T,E> |    | Handle Err   |    |  .error      |    | ErrorUI      |
+--------------+    +--------------+    +--------------+    +--------------+
```

### Unified Error Model
```typescript
// domain/models/AppError.ets
export class AppError {
  static readonly NETWORK = 'NETWORK'
  static readonly TIMEOUT = 'TIMEOUT'
  static readonly UNAUTHORIZED = 'UNAUTHORIZED'
  static readonly SESSION_EXPIRED = 'SESSION_EXPIRED'
  static readonly NOT_FOUND = 'NOT_FOUND'
  static readonly VALIDATION = 'VALIDATION'
  static readonly DATABASE = 'DATABASE'
  static readonly UNKNOWN = 'UNKNOWN'

  readonly code: string
  readonly message: string
  readonly requiresReauth: boolean

  constructor(code: string, message: string) {
    this.code = code
    this.message = message
    this.requiresReauth = code === AppError.UNAUTHORIZED || code === AppError.SESSION_EXPIRED
  }
}
```

### Result Type (No throw in ArkTS strict mode)
```typescript
// domain/models/Result.ets
export class Result<T, E> {
  private readonly value: T | undefined
  private readonly error: E | undefined
  private readonly isOk: boolean

  private constructor(value: T | undefined, error: E | undefined, isOk: boolean) {
    this.value = value
    this.error = error
    this.isOk = isOk
  }

  static success<T, E>(value: T): Result<T, E> {
    return new Result<T, E>(value, undefined, true)
  }

  static failure<T, E>(error: E): Result<T, E> {
    return new Result<T, E>(undefined, error, false)
  }

  isSuccess(): boolean {
    return this.isOk
  }

  isFailure(): boolean {
    return !this.isOk
  }

  getOrNull(): T | undefined {
    return this.value
  }

  getErrorOrNull(): E | undefined {
    return this.error
  }

  map<U>(transform: (value: T) => U): Result<U, E> {
    if (this.isOk && this.value !== undefined) {
      return Result.success<U, E>(transform(this.value))
    }
    return Result.failure<U, E>(this.error as E)
  }

  flatMap<U>(transform: (value: T) => Result<U, E>): Result<U, E> {
    if (this.isOk && this.value !== undefined) {
      return transform(this.value)
    }
    return Result.failure<U, E>(this.error as E)
  }

  fold<U>(onSuccess: (value: T) => U, onFailure: (error: E) => U): U {
    if (this.isOk && this.value !== undefined) {
      return onSuccess(this.value)
    }
    return onFailure(this.error as E)
  }
}
```

---

## Test Coverage Targets

### Coverage Goals by Layer
| Layer | Target | Focus Areas |
|-------|--------|-------------|
| **Domain (Validators/Services)** | 90%+ | Business logic, edge cases, pure functions |
| **Data (Repository)** | 80%+ | Data transformation, error handling, sync |
| **Presentation (ViewModel)** | 85%+ | State management, input handling, effects |
| **Core (DI/Network/Security)** | 75%+ | Container resolution, network status |
| **UI (Components)** | 60%+ | Critical user flows |

### Test Naming Convention
```typescript
// @ohos/hypium test format
describe('FeatureViewModel', () => {
  it('should update output when valid input received', () => {
    // Given - Arrange
    // When - Act
    // Then - Assert
  })

  it('should emit navigation effect when item tapped', () => { })
  it('should show error when network fails', () => { })
  it('should set loading true during async operation', () => { })
})
```

### Minimum Tests Before PR
```bash
# Run all tests
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test

# Or via DevEco Studio
# Run > Run All Tests
```

---

## Spec Gap Prediction

### Screen Type -> Required States
| Screen Type | Required States | Prediction Rule |
|-------------|-----------------|-----------------|
| **List Page** | Loading, Empty, Error, Data, Pull-to-refresh | Lists must have empty state |
| **Detail Page** | Loading, Error, Data, Not Found | Details must have loading state |
| **Form Page** | Input, Validation, Submitting, Success, Error | Forms must have validation |
| **Dashboard** | Loading skeleton, Partial data, Full data | Dashboards must have skeleton |
| **Settings** | Current values, Save confirmation | Settings must have confirmation |

### Flow Completion Prediction
| If Spec Has | Predict Also Needed | Reasoning |
|-------------|---------------------|-----------|
| Login | Register, Forgot Password | Login requires register |
| Register | Onboarding, Email Verification | Register requires onboarding |
| List | Detail, Search, Filter | List requires detail |
| Detail | Edit (if editable), Share, Delete | Detail often has edit |
| Create | Edit, Delete, Duplicate | Create requires modify |
| Profile | Edit Profile, Logout | Profile requires logout |

---

## Four-Layer Clean Architecture

### Layer Responsibilities

#### Presentation Layer
```
entry/src/main/ets/
  pages/            # @Entry page components
  presentation/
    components/     # Reusable ArkUI components
    viewmodel/      # MVVM Input/Output/Effect ViewModels
```
- ArkUI declarative components
- MVVM ViewModels with Input/Output/Effect
- UI state management
- Navigation routing

#### Domain Layer (PURE - Zero Dependencies)
```
entry/src/main/ets/domain/
  models/           # Domain models (immutable data classes)
  validators/       # Business validation rules
  services/         # Business logic coordination
  repository/       # Repository interfaces ONLY
```
- Domain Models with factory methods for immutable updates
- Validators as pure functions
- Repository interfaces (no implementation)
- ZERO external dependencies - no HarmonyOS SDK imports

#### Data Layer
```
entry/src/main/ets/data/
  api/dto/          # Data Transfer Objects for API
  cache/            # LRU cache implementation
  local/            # RelationalStore (SQLite) local source
  repository/       # Repository implementations (offline-first)
```
- Offline-first repository implementations
- RelationalStore for local persistence
- API DTOs and network calls
- Data mapping: DTO <-> Entity <-> Domain Model

#### Core Layer
```
entry/src/main/ets/core/
  di/               # InversifyJS-style IoC container
  analytics/        # Analytics tracking
  logging/          # Structured logging
  network/          # Network monitor (@kit.NetworkKit)
  sync/             # Sync manager (conflict resolution)
  scheduling/       # WorkScheduler background tasks
  security/         # HUKS AES-256-GCM encryption
  i18n/             # Internationalization
  navigation/       # Type-safe navigation
```
- DI Container with decorators
- Network monitoring
- Background sync scheduling
- Security (HUKS keystore)
- Cross-cutting concerns

---

## MVVM Input/Output/Effect Pattern

### Discriminated Unions for Type Safety

```typescript
// Discriminated union pattern for ArkTS (no sealed class)
export class InputType {
  static readonly LOAD = 'LOAD'
  static readonly REFRESH = 'REFRESH'
  static readonly ITEM_TAPPED = 'ITEM_TAPPED'
  static readonly SEARCH = 'SEARCH'
  static readonly RETRY = 'RETRY'
}

export class Input {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static load(): Input {
    return new Input(InputType.LOAD, undefined)
  }

  static refresh(): Input {
    return new Input(InputType.REFRESH, undefined)
  }

  static itemTapped(id: string): Input {
    return new Input(InputType.ITEM_TAPPED, id)
  }

  static search(query: string): Input {
    return new Input(InputType.SEARCH, query)
  }

  static retry(): Input {
    return new Input(InputType.RETRY, undefined)
  }
}
```

### ViewModel Template
```typescript
@injectable()
export class FeatureViewModel {
  private _output: Output = Output.initial()
  private _effectCallback: ((effect: Effect) => void) | undefined = undefined

  get output(): Output {
    return this._output
  }

  setEffectCallback(callback: (effect: Effect) => void): void {
    this._effectCallback = callback
  }

  onInput(input: Input): void {
    switch (input.type) {
      case InputType.LOAD:
        this.loadData()
        break
      case InputType.REFRESH:
        this.refresh()
        break
      case InputType.ITEM_TAPPED:
        this.handleItemTap(input.payload as string)
        break
      case InputType.SEARCH:
        this.handleSearch(input.payload as string)
        break
      case InputType.RETRY:
        this.loadData()
        break
      default:
        break
    }
  }

  private emitEffect(effect: Effect): void {
    if (this._effectCallback !== undefined) {
      this._effectCallback(effect)
    }
  }
}
```

### Output with Factory Methods (Immutable Updates)
```typescript
export class Output {
  readonly items: Array<Item>
  readonly isLoading: boolean
  readonly error: string | undefined
  readonly searchQuery: string

  private constructor(
    items: Array<Item>,
    isLoading: boolean,
    error: string | undefined,
    searchQuery: string
  ) {
    this.items = items
    this.isLoading = isLoading
    this.error = error
    this.searchQuery = searchQuery
  }

  static initial(): Output {
    return new Output(new Array<Item>(), false, undefined, '')
  }

  // Factory methods for immutable updates (no spread operator in ArkTS)
  withLoading(isLoading: boolean): Output {
    return new Output(this.items, isLoading, this.error, this.searchQuery)
  }

  withItems(items: Array<Item>): Output {
    return new Output(items, false, undefined, this.searchQuery)
  }

  withError(error: string): Output {
    return new Output(this.items, false, error, this.searchQuery)
  }

  withSearchQuery(query: string): Output {
    return new Output(this.items, this.isLoading, this.error, query)
  }
}
```

### Effect Types
```typescript
export class EffectType {
  static readonly NAVIGATE = 'NAVIGATE'
  static readonly SHOW_TOAST = 'SHOW_TOAST'
  static readonly NAVIGATE_BACK = 'NAVIGATE_BACK'
}

export class Effect {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static navigate(route: string): Effect {
    return new Effect(EffectType.NAVIGATE, route)
  }

  static showToast(message: string): Effect {
    return new Effect(EffectType.SHOW_TOAST, message)
  }

  static navigateBack(): Effect {
    return new Effect(EffectType.NAVIGATE_BACK, undefined)
  }
}
```

---

## DI Container (InversifyJS-style for ArkTS)

### Container Setup
```typescript
// core/di/Container.ets
export class Container {
  private bindings: Map<string, () => Object> = new Map()
  private singletons: Map<string, Object> = new Map()

  bind<T extends Object>(identifier: string, factory: () => T): void {
    this.bindings.set(identifier, factory)
  }

  bindSingleton<T extends Object>(identifier: string, factory: () => T): void {
    this.bindings.set(identifier, () => {
      const existing = this.singletons.get(identifier)
      if (existing !== undefined) {
        return existing
      }
      const instance = factory()
      this.singletons.set(identifier, instance)
      return instance
    })
  }

  resolve<T extends Object>(identifier: string): T {
    const factory = this.bindings.get(identifier)
    if (factory === undefined) {
      throw new Error(`No binding found for: ${identifier}`)
    }
    return factory() as T
  }
}

// Decorator identifiers (class-based constants, no symbols)
export class ServiceIdentifiers {
  static readonly USER_REPOSITORY = 'UserRepository'
  static readonly USER_SERVICE = 'UserService'
  static readonly USER_VIEW_MODEL = 'UserViewModel'
  static readonly AUTH_REPOSITORY = 'AuthRepository'
  static readonly SYNC_MANAGER = 'SyncManager'
  static readonly NETWORK_MONITOR = 'NetworkMonitor'
  static readonly SECURITY_SERVICE = 'SecurityService'
  static readonly ANALYTICS_SERVICE = 'AnalyticsService'
}
```

### Decorator Pattern
```typescript
// core/di/Decorators.ets
// ArkTS cannot use runtime reflection, so decorators are marker-only.
// Registration is explicit via container.bind().

// @injectable marker (documentation purpose)
export function injectable(): ClassDecorator {
  return (target: Function) => { /* marker only */ }
}

// @inject marker
export function inject(identifier: string): PropertyDecorator {
  return (target: Object, propertyKey: string) => { /* marker only */ }
}
```

---

## Offline-First Architecture

### Sync Flow
```
User Action
    |
    v
Optimistic Update (Local DB, status=PENDING)
    |
    v
Background Sync Triggered
    |
    +---> Online: API Call + Update status=SYNCED
    |
    +---> Offline: Queue + Retry via WorkScheduler
```

### Sync Status Tracking
```typescript
export class SyncStatus {
  static readonly SYNCED = 'SYNCED'
  static readonly PENDING_CREATE = 'PENDING_CREATE'
  static readonly PENDING_UPDATE = 'PENDING_UPDATE'
  static readonly PENDING_DELETE = 'PENDING_DELETE'
  static readonly SYNC_FAILED = 'SYNC_FAILED'
}
```

### Conflict Resolution: Last-Write-Wins
```typescript
// data/repository/UserRepositoryImpl.ets
async syncPendingChanges(): Promise<void> {
  const pendingItems = await this.localSource.getPendingSync()

  for (const item of pendingItems) {
    const result = await this.apiService.syncItem(item.toDto())
    result.fold(
      (response: ItemDto) => {
        // Success: mark as synced
        this.localSource.updateSyncStatus(item.id, SyncStatus.SYNCED)
      },
      (error: AppError) => {
        if (error.code === AppError.NOT_FOUND) {
          // Server deleted: remove local
          this.localSource.delete(item.id)
        } else {
          // Network error: keep pending for retry
          this.localSource.updateSyncStatus(item.id, SyncStatus.SYNC_FAILED)
        }
      }
    )
  }
}
```

### Repository Template (Offline-First)
```typescript
@injectable()
export class UserRepositoryImpl implements UserRepository {
  private localSource: UserLocalSource
  private apiService: UserApiService
  private networkMonitor: NetworkMonitor

  constructor(
    localSource: UserLocalSource,
    apiService: UserApiService,
    networkMonitor: NetworkMonitor
  ) {
    this.localSource = localSource
    this.apiService = apiService
    this.networkMonitor = networkMonitor
  }

  // Read: always from local (single source of truth)
  async getUsers(): Promise<Result<Array<User>, AppError>> {
    const entities = await this.localSource.getAll()
    const users = entities.map((entity: UserEntity) => entity.toDomain())
    return Result.success(users)
  }

  // Write: local first, then schedule sync
  async createUser(user: User): Promise<Result<User, AppError>> {
    const entity = UserEntity.fromDomain(user)
    entity.syncStatus = SyncStatus.PENDING_CREATE
    await this.localSource.insert(entity)

    if (this.networkMonitor.isOnline()) {
      await this.syncPendingChanges()
    }

    return Result.success(user)
  }

  async updateUser(user: User): Promise<Result<User, AppError>> {
    const entity = UserEntity.fromDomain(user)
    entity.syncStatus = SyncStatus.PENDING_UPDATE
    await this.localSource.update(entity)

    if (this.networkMonitor.isOnline()) {
      await this.syncPendingChanges()
    }

    return Result.success(user)
  }

  async deleteUser(id: string): Promise<Result<boolean, AppError>> {
    await this.localSource.updateSyncStatus(id, SyncStatus.PENDING_DELETE)

    if (this.networkMonitor.isOnline()) {
      await this.syncPendingChanges()
    }

    return Result.success(true)
  }
}
```

---

## ArkTS-Specific Patterns (Strict Mode Workarounds)

### Constraint: No any/unknown Types
```typescript
// WRONG - ArkTS strict mode forbids any/unknown
let data: any = fetchData()
let result: unknown = parse(input)

// CORRECT - Use explicit types
let data: UserData = fetchData()
let result: ParseResult = parse(input)
```

### Constraint: No Spread Operators
```typescript
// WRONG - Spread operators not allowed
const updated = { ...original, name: 'new' }

// CORRECT - Factory method pattern
const updated = original.withName('new')

// Implementation
export class UserData {
  readonly name: string
  readonly email: string

  constructor(name: string, email: string) {
    this.name = name
    this.email = email
  }

  withName(name: string): UserData {
    return new UserData(name, this.email)
  }

  withEmail(email: string): UserData {
    return new UserData(this.name, email)
  }
}
```

### Constraint: No Computed Properties
```typescript
// WRONG - Computed property keys not allowed
const key = 'name'
const obj = { [key]: 'value' }

// CORRECT - Use Map or explicit property assignment
const map: Map<string, string> = new Map()
map.set('name', 'value')
```

### Constraint: No Object Literals for Constants
```typescript
// WRONG - Object literal as constant
const ROUTES = {
  HOME: '/home',
  SETTINGS: '/settings'
}

// CORRECT - Class-based constants
export class Routes {
  static readonly HOME = '/home'
  static readonly SETTINGS = '/settings'
  static readonly USER_LIST = '/user/list'
  static readonly USER_DETAIL = '/user/detail'
}
```

### Constraint: Limited throw
```typescript
// AVOID - throw in business logic
function validate(input: string): string {
  if (input.length === 0) {
    throw new Error('Input required')
  }
  return input
}

// PREFER - Result type for error handling
function validate(input: string): Result<string, AppError> {
  if (input.length === 0) {
    return Result.failure(new AppError(AppError.VALIDATION, 'Input required'))
  }
  return Result.success(input)
}
```

### String Literal Keys Pattern
```typescript
// For Map-based lookups and type-safe string keys
export class CacheKeys {
  static readonly USER_LIST = 'cache_user_list'
  static readonly USER_DETAIL_PREFIX = 'cache_user_detail_'
  static readonly AUTH_TOKEN = 'cache_auth_token'
}
```

### Builder Pattern for Declarative APIs
```typescript
export class QueryBuilder {
  private tableName: string = ''
  private conditions: Array<string> = new Array<string>()
  private orderByField: string = ''
  private limitCount: number = 0

  table(name: string): QueryBuilder {
    this.tableName = name
    return this
  }

  where(condition: string): QueryBuilder {
    this.conditions.push(condition)
    return this
  }

  orderBy(field: string): QueryBuilder {
    this.orderByField = field
    return this
  }

  limit(count: number): QueryBuilder {
    this.limitCount = count
    return this
  }

  build(): string {
    let query = `SELECT * FROM ${this.tableName}`
    if (this.conditions.length > 0) {
      query += ` WHERE ${this.conditions.join(' AND ')}`
    }
    if (this.orderByField.length > 0) {
      query += ` ORDER BY ${this.orderByField}`
    }
    if (this.limitCount > 0) {
      query += ` LIMIT ${this.limitCount}`
    }
    return query
  }
}
```

---

## Security (HUKS AES-256-GCM)

### Key Generation and Storage
```typescript
// core/security/SecurityService.ets
import { huks } from '@kit.UniversalKeystoreKit'

@injectable()
export class SecurityService {
  private static readonly KEY_ALIAS = 'arcana_master_key'
  private static readonly AES_KEY_SIZE = 256

  async generateKey(): Promise<Result<boolean, AppError>> {
    const properties: Array<huks.HuksParam> = new Array<huks.HuksParam>()
    properties.push({ tag: huks.HuksTag.HUKS_TAG_ALGORITHM, value: huks.HuksKeyAlg.HUKS_ALG_AES })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_KEY_SIZE, value: huks.HuksKeySize.HUKS_AES_KEY_SIZE_256 })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PURPOSE, value: huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_ENCRYPT | huks.HuksKeyPurpose.HUKS_KEY_PURPOSE_DECRYPT })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_BLOCK_MODE, value: huks.HuksCipherMode.HUKS_MODE_GCM })
    properties.push({ tag: huks.HuksTag.HUKS_TAG_PADDING, value: huks.HuksKeyPadding.HUKS_PADDING_NONE })

    const options: huks.HuksOptions = {
      properties: properties
    }

    try {
      await huks.generateKeyItem(SecurityService.KEY_ALIAS, options)
      return Result.success(true)
    } catch (e) {
      return Result.failure(new AppError(AppError.UNKNOWN, 'Key generation failed'))
    }
  }

  async encrypt(plaintext: string): Promise<Result<Uint8Array, AppError>> {
    // ... HUKS encrypt implementation
  }

  async decrypt(ciphertext: Uint8Array): Promise<Result<string, AppError>> {
    // ... HUKS decrypt implementation
  }
}
```

---

## Navigation (Type-Safe)

### Route Definition
```typescript
// core/navigation/NavigationRoutes.ets
export class NavigationRoutes {
  static readonly HOME = 'pages/HomePage'
  static readonly LOGIN = 'pages/LoginPage'
  static readonly REGISTER = 'pages/RegisterPage'
  static readonly ONBOARDING = 'pages/OnboardingPage'
  static readonly USER_LIST = 'pages/UserListPage'
  static readonly USER_DETAIL = 'pages/UserDetailPage'
  static readonly SETTINGS = 'pages/SettingsPage'
  static readonly PROFILE = 'pages/ProfilePage'
}
```

### Navigation Helper
```typescript
// core/navigation/NavigationHelper.ets
import { router } from '@ohos.router'

export class NavigationHelper {
  static pushUrl(url: string, params: Map<string, string> | undefined): void {
    const options: router.RouterOptions = {
      url: url
    }
    if (params !== undefined) {
      const paramsObj: Record<string, string> = {}
      params.forEach((value: string, key: string) => {
        paramsObj[key] = value
      })
      options.params = paramsObj
    }
    router.pushUrl(options)
  }

  static back(): void {
    router.back()
  }

  static replaceUrl(url: string): void {
    router.replaceUrl({ url: url })
  }

  static getParams<T>(): T | undefined {
    const params = router.getParams()
    if (params !== undefined && params !== null) {
      return params as T
    }
    return undefined
  }
}
```

---

## Background Workers (WorkScheduler)

### WorkScheduler Setup
```typescript
// core/scheduling/SyncScheduler.ets
import { workScheduler } from '@ohos.WorkSchedulerExtensionAbility'

export class SyncScheduler {
  private static readonly SYNC_WORK_ID = 1001
  private static readonly SYNC_INTERVAL_MS = 15 * 60 * 1000 // 15 minutes

  static schedulePeriodic(): void {
    const workInfo: workScheduler.WorkInfo = {
      workId: SyncScheduler.SYNC_WORK_ID,
      networkType: workScheduler.NetworkType.NETWORK_TYPE_ANY,
      isRepeat: true,
      repeatCycleTime: SyncScheduler.SYNC_INTERVAL_MS,
      isPersisted: true
    }
    workScheduler.startWork(workInfo)
  }

  static scheduleOneTime(): void {
    const workInfo: workScheduler.WorkInfo = {
      workId: SyncScheduler.SYNC_WORK_ID + 1,
      networkType: workScheduler.NetworkType.NETWORK_TYPE_ANY,
      isRepeat: false,
      isPersisted: false
    }
    workScheduler.startWork(workInfo)
  }

  static cancel(): void {
    workScheduler.stopWork(SyncScheduler.SYNC_WORK_ID)
  }
}
```

### WorkSchedulerExtensionAbility
```typescript
// workers/SyncWorker.ets
import { WorkSchedulerExtensionAbility } from '@ohos.WorkSchedulerExtensionAbility'

export default class SyncWorker extends WorkSchedulerExtensionAbility {
  onWorkStart(workInfo: workScheduler.WorkInfo): void {
    // Resolve sync manager from DI container
    const syncManager = AppContainer.resolve<SyncManager>(ServiceIdentifiers.SYNC_MANAGER)
    syncManager.syncAll()
  }

  onWorkStop(workInfo: workScheduler.WorkInfo): void {
    // Cleanup
  }
}
```

---

## i18n

### Resource-Based Strings
```typescript
// All user-facing strings MUST use resource references
// resource/base/element/string.json
// resource/en/element/string.json
// resource/zh/element/string.json

// Usage in ArkUI components:
Text($r('app.string.login_title'))
Text($r('app.string.error_network', errorCode))

// NEVER hardcode user-facing strings
// WRONG:
Text('Login')
// CORRECT:
Text($r('app.string.login_title'))
```

---

## Code Review Checklist

### Required Items
- [ ] Follow four-layer Clean Architecture
- [ ] Domain layer has ZERO external dependencies
- [ ] ViewModel uses Input/Output/Effect pattern
- [ ] Repository implements offline-first
- [ ] ArkTS strict mode compliance (no any/unknown/spread)
- [ ] DI container bindings are explicit
- [ ] All navigation callbacks are wired
- [ ] Result<T,E> used instead of throw
- [ ] All user-facing strings use $r() resource references
- [ ] Sync status tracked for all data mutations

### Performance Checks
- [ ] LRU cache used for frequently accessed data
- [ ] LazyForEach used for lists (not ForEach for large lists)
- [ ] Images loaded with proper caching
- [ ] Avoid unnecessary @State recomposition
- [ ] Use @Observed and @ObjectLink for component state

### Security Checks
- [ ] Sensitive data encrypted with HUKS
- [ ] API keys not hardcoded
- [ ] Input validation complete
- [ ] Network requests use HTTPS
- [ ] Auth tokens stored securely

---

## Common Issues

### ArkTS Strict Mode Compilation Errors
1. Replace `any` with explicit types
2. Replace spread operators with factory methods
3. Replace object literals with class-based constants
4. Replace computed properties with Map
5. Replace throw with Result<T,E>

### DevEco Studio Build Issues
1. Check `oh-package.json5` for dependency conflicts
2. Run `ohpm install` to resolve dependencies
3. Clean build with `hvigorw clean`
4. Check `build-profile.json5` for correct API versions

### RelationalStore Migration Issues
1. Define migration SQL statements explicitly
2. Version database schema incrementally
3. Test migration paths from each version

### DI Container Resolution Failures
1. Verify all bindings registered before resolution
2. Check for circular dependencies
3. Ensure singleton vs transient binding is correct
4. Use ServiceIdentifiers constants consistently

---

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| HarmonyOS NEXT | 5.0+ |
| ArkTS | Strict Mode |
| ArkUI | Declarative |
| API Level | Target 21 / Min 12 |
| DevEco Studio | 6.0.1.260+ |
| @kit.NetworkKit | Latest |
| @kit.ArkData | RelationalStore |
| @kit.UniversalKeystoreKit | HUKS |
| @ohos/hypium | Latest |
| WorkSchedulerExtensionAbility | Latest |

---

## Instructions

When handling HarmonyOS development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented repositories (MUST be empty)
grep -rn "throw new Error\|NotImplemented\|TODO.*implement" entry/src/main/ets/

# 2. Check for empty click handlers (MUST be empty)
grep -rn "() => {}" entry/src/main/ets/pages/ entry/src/main/ets/presentation/

# 3. Check for any/unknown usage (MUST be empty - ArkTS strict mode)
grep -rn ": any\|: unknown\|as any\|as unknown" entry/src/main/ets/

# 4. Check for spread operators (MUST be empty - ArkTS strict mode)
grep -rn "\.\.\." entry/src/main/ets/ | grep -v "node_modules" | grep -v ".json"

# 5. Check for hardcoded strings (should use $r())
grep -rn "Text('" entry/src/main/ets/pages/ | grep -v "\$r(" | head -20

# 6. Verify DI container bindings
grep -rn "container.bind\|bindSingleton" entry/src/main/ets/core/di/

# 7. Check for empty arrays in repository stubs
grep -rn "new Array()\|Array<.*>()" entry/src/main/ets/data/repository/ | grep -v "push\|length"

# 8. Check sync status tracking
grep -rn "SyncStatus\." entry/src/main/ets/data/repository/

# 9. Run all tests
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test

# 10. Build verification
hvigorw assembleHap --mode module -p product=default -p module=entry
```

CRITICAL: ArkTS strict mode violations will cause compilation failures. Always verify no any/unknown/spread operators exist.

If any of these checks return results, FIX THEM before completing the task.

---

### 0. Project Setup - CRITICAL

IMPORTANT: This reference project has been validated with tested build settings and library versions. NEVER reconfigure project structure or modify build-profile.json5 / oh-package.json5, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-harmonyos.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-harmonyos template"
```

**Step 3**: Modify project name and Bundle ID
Only modify the following required items:
- `bundleName` in `AppScope/app.json5`
- `module.name` in `entry/src/main/module.json5`
- Package directory structure under `entry/src/main/ets/`

**Step 4**: Clean up example code

**Core architecture files to KEEP** (do not delete):
- `core/` - DI, Network, Security, Sync, Analytics
- `domain/models/Result.ets` - Result type
- `domain/models/AppError.ets` - Error model
- `data/local/` - RelationalStore base configuration
- Navigation configuration

**Example files to REPLACE**:
- `pages/` - Delete example pages, create new project UI
- `presentation/viewmodel/` - Delete example ViewModels
- `domain/models/` - Delete example Models (keep Result/AppError)
- `data/api/` - Modify API endpoints
- `data/repository/` - Delete example repositories

**Step 5**: Verify build
```bash
hvigorw assembleHap --mode module -p product=default -p module=entry
```

### Prohibited Actions
- **DO NOT** create new project from scratch
- **DO NOT** modify version numbers in `oh-package.json5`
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify `build-profile.json5` API versions
- **DO NOT** use any, unknown, spread operators, or computed properties

### Allowed Modifications
- Add business-related ArkTS code (following existing architecture)
- Add UI pages (using existing ArkUI patterns)
- Add Domain Models, Repository, ViewModel
- Modify resources in `resource/`
- Add navigation routes

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

CRITICAL: All development MUST follow this TDD workflow.

```
+---------------------------------------------------------------+
|                    TDD Development Workflow                      |
+---------------------------------------------------------------+
|  Step 1: Analyze Spec -> Extract all SRS & SDD requirements     |
|  Step 2: Create Tests -> Write tests for EACH Spec item         |
|  Step 3: Verify Coverage -> Ensure 100% Spec coverage in tests  |
|  Step 4: Implement -> Build features to pass tests  MANDATORY   |
|  Step 5: Mock APIs -> Use mock data for unfinished Cloud APIs   |
|  Step 6: Run All Tests -> ALL tests must pass before completion |
|  Step 7: Verify 100% -> Tests written = Features implemented    |
+---------------------------------------------------------------+
```

### 2. Project Structure
```
entry/src/main/ets/
+-- core/
|   +-- di/               # IoC Container + ServiceIdentifiers
|   +-- analytics/         # Analytics tracking
|   +-- logging/           # Structured logging
|   +-- network/           # Network monitor
|   +-- sync/              # Sync manager
|   +-- scheduling/        # WorkScheduler
|   +-- security/          # HUKS security
|   +-- i18n/              # Internationalization
|   +-- navigation/        # Type-safe navigation
+-- data/
|   +-- api/dto/           # Data Transfer Objects
|   +-- cache/             # LRU cache
|   +-- local/             # RelationalStore local source
|   +-- repository/        # Repository implementations
+-- domain/
|   +-- models/            # Domain models + Result<T,E>
|   +-- validators/        # Pure validation functions
|   +-- services/          # Business logic
|   +-- repository/        # Repository interfaces ONLY
+-- presentation/
|   +-- components/        # Reusable ArkUI components
|   +-- viewmodel/         # MVVM ViewModels
+-- pages/                 # @Entry page components
+-- workers/               # WorkSchedulerExtensionAbility
```

### Final Verification - MANDATORY

Before marking any feature complete:

```bash
# === FULL COMPLETION CHECK ===

echo "=== 1. ArkTS Strict Mode Check ===" && \
grep -rn ": any\|: unknown" entry/src/main/ets/ | grep -v node_modules || echo "OK: No any/unknown" && \
grep -rn "\.\.\." entry/src/main/ets/ | grep -v node_modules | grep -v .json || echo "OK: No spread operators"

echo "=== 2. Empty Handler Check ===" && \
grep -rn "() => {}" entry/src/main/ets/pages/ || echo "OK: No empty handlers"

echo "=== 3. Unimplemented Methods Check ===" && \
grep -rn "throw new Error\|NotImplemented\|TODO" entry/src/main/ets/ || echo "OK: No unimplemented methods"

echo "=== 4. DI Binding Check ===" && \
echo "Bindings registered:" && \
grep -c "container.bind\|bindSingleton" entry/src/main/ets/core/di/*.ets

echo "=== 5. Build Verification ===" && \
hvigorw assembleHap --mode module -p product=default -p module=entry && echo "OK: Build passed"

echo "=== 6. Test Verification ===" && \
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test
```

Task is NOT complete if ANY of these checks fail.
