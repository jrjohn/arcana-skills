# HarmonyOS Architecture Reference

Complete technical reference document based on Arcana HarmonyOS enterprise architecture.

## Table of Contents

1. [Project Structure](#project-structure)
2. [ArkTS Strict Mode Reference](#arkts-strict-mode-reference)
3. [ArkUI Component Reference](#arkui-component-reference)
4. [RelationalStore Reference](#relationalstore-reference)
5. [HUKS Security Reference](#huks-security-reference)
6. [WorkScheduler Reference](#workscheduler-reference)
7. [NetworkKit Reference](#networkkit-reference)
8. [Testing Reference](#testing-reference)
9. [DevEco Studio Reference](#deveco-studio-reference)

---

## Project Structure

### Recommended Module Structure

```
project-root/
+-- AppScope/
|   +-- app.json5                    # Application configuration
|   +-- resources/                   # Application-level resources
+-- entry/                           # Main entry module
|   +-- src/main/
|   |   +-- ets/                     # ArkTS source code
|   |   |   +-- core/               # Core layer
|   |   |   |   +-- di/             # DI Container
|   |   |   |   +-- analytics/      # Analytics
|   |   |   |   +-- logging/        # Logging
|   |   |   |   +-- network/        # Network monitoring
|   |   |   |   +-- sync/           # Sync management
|   |   |   |   +-- scheduling/     # WorkScheduler
|   |   |   |   +-- security/       # HUKS security
|   |   |   |   +-- i18n/           # Internationalization
|   |   |   |   +-- navigation/     # Navigation helpers
|   |   |   +-- data/               # Data layer
|   |   |   |   +-- api/dto/        # API DTOs
|   |   |   |   +-- cache/          # LRU cache
|   |   |   |   +-- local/          # RelationalStore sources
|   |   |   |   +-- repository/     # Repository implementations
|   |   |   +-- domain/             # Domain layer (PURE)
|   |   |   |   +-- models/         # Domain models + Result<T,E>
|   |   |   |   +-- validators/     # Validation functions
|   |   |   |   +-- services/       # Business services
|   |   |   |   +-- repository/     # Repository interfaces
|   |   |   +-- presentation/       # Presentation layer
|   |   |   |   +-- components/     # Reusable components
|   |   |   |   +-- viewmodel/      # ViewModels
|   |   |   +-- pages/              # @Entry page components
|   |   |   +-- workers/            # WorkSchedulerExtensionAbility
|   |   +-- module.json5            # Module configuration
|   |   +-- resources/              # Module resources
|   +-- src/test/                   # Unit tests
|   +-- oh-package.json5            # Package dependencies
|   +-- build-profile.json5         # Build configuration
+-- oh-package.json5                # Root package config
+-- build-profile.json5             # Root build config
+-- hvigorfile.ts                   # Build script
```

---

## ArkTS Strict Mode Reference

### Forbidden Features

| Feature | Status | Workaround |
|---------|--------|------------|
| `any` type | FORBIDDEN | Use explicit types |
| `unknown` type | FORBIDDEN | Use explicit types or union types |
| Spread operators (`...`) | FORBIDDEN | Factory methods on classes |
| Computed properties (`[key]: value`) | FORBIDDEN | Use Map<string, T> |
| Object literals as constants | AVOID | Class-based constants |
| `throw` for control flow | AVOID | Return Result<T, E> |
| Runtime reflection | FORBIDDEN | Explicit DI registration |
| `eval()` | FORBIDDEN | N/A |
| Dynamic property access | RESTRICTED | Use typed accessors |
| Prototype modification | FORBIDDEN | Use class inheritance |

### Type System

```typescript
// Primitive types
let count: number = 0
let name: string = ''
let isActive: boolean = false

// Collection types
let items: Array<string> = new Array<string>()
let lookup: Map<string, number> = new Map<string, number>()
let uniqueIds: Set<string> = new Set<string>()

// Optional types (use | undefined, not ?)
let optionalValue: string | undefined = undefined

// Union types for discriminated unions
type StatusType = 'active' | 'inactive' | 'pending'

// Generic types
class Container<T> {
  private value: T
  constructor(value: T) { this.value = value }
  get(): T { return this.value }
}
```

### Decorator Support

| Decorator | Purpose | ArkTS Support |
|-----------|---------|---------------|
| `@Entry` | Page entry point | Built-in |
| `@Component` | ArkUI component | Built-in |
| `@State` | Local reactive state | Built-in |
| `@Prop` | Parent-to-child data | Built-in |
| `@Link` | Two-way binding | Built-in |
| `@Observed` | Observable class | Built-in |
| `@ObjectLink` | Reference to @Observed | Built-in |
| `@Builder` | UI builder function | Built-in |
| `@Styles` | Reusable styles | Built-in |
| `@Extend` | Component extension | Built-in |
| `@injectable` | DI marker (custom) | Custom implementation |
| `@inject` | DI marker (custom) | Custom implementation |

---

## ArkUI Component Reference

### Layout Components

| Component | Purpose | Key Properties |
|-----------|---------|----------------|
| `Column` | Vertical layout | `justifyContent`, `alignItems`, `space` |
| `Row` | Horizontal layout | `justifyContent`, `alignItems`, `space` |
| `Stack` | Overlay layout | `alignContent` |
| `Flex` | Flexible layout | `direction`, `wrap`, `justifyContent` |
| `Grid` | Grid layout | `columnsTemplate`, `rowsTemplate` |
| `List` | Scrollable list | `divider`, `scrollBar` |
| `Scroll` | Scrollable container | `scrollable`, `scrollBar` |
| `Tabs` | Tab layout | `barPosition`, `index` |

### Input Components

| Component | Purpose | Key Properties |
|-----------|---------|----------------|
| `TextInput` | Text field | `type`, `placeholder`, `text` |
| `TextArea` | Multi-line input | `placeholder`, `text` |
| `Button` | Clickable button | `type`, `stateEffect` |
| `Toggle` | Switch/checkbox | `type`, `isOn` |
| `Slider` | Range selector | `min`, `max`, `value`, `step` |
| `Select` | Dropdown | `options`, `selected` |
| `Search` | Search bar | `placeholder`, `value` |
| `DatePicker` | Date selector | `start`, `end`, `selected` |

### Display Components

| Component | Purpose | Key Properties |
|-----------|---------|----------------|
| `Text` | Text display | `fontSize`, `fontWeight`, `fontColor` |
| `Image` | Image display | `width`, `height`, `objectFit` |
| `LoadingProgress` | Loading indicator | `width`, `height`, `color` |
| `Progress` | Progress bar | `value`, `total`, `type` |
| `Badge` | Badge indicator | `count`, `maxCount`, `position` |
| `Divider` | Separator line | `color`, `strokeWidth` |

### Container Components

| Component | Purpose | Key Properties |
|-----------|---------|----------------|
| `Refresh` | Pull-to-refresh | `refreshing`, `onRefreshing` |
| `Swiper` | Carousel/pager | `autoPlay`, `indicator` |
| `Navigation` | Navigation container | `title`, `menus` |
| `Panel` | Bottom sheet | `show`, `type`, `mode` |
| `Dialog` | Modal dialog | Custom via `@CustomDialog` |

### List Optimization

```typescript
// Use LazyForEach for large lists (virtualized rendering)
List() {
  LazyForEach(dataSource, (item: ItemModel) => {
    ListItem() {
      // Item content
    }
  }, (item: ItemModel) => item.id)  // Key generator
}

// Use ForEach for small static lists only
ForEach(shortArray, (item: string) => {
  Text(item)
}, (item: string) => item)
```

---

## RelationalStore Reference

### Database Setup

```typescript
import { relationalStore } from '@kit.ArkData'

// Store configuration
const storeConfig: relationalStore.StoreConfig = {
  name: 'app_database.db',
  securityLevel: relationalStore.SecurityLevel.S1
}

// Get store instance
const store = await relationalStore.getRdbStore(context, storeConfig)
```

### Schema Management

```typescript
// Table creation
await store.executeSql(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    avatar_url TEXT,
    sync_status TEXT NOT NULL DEFAULT 'SYNCED',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
  )
`)

// Add index
await store.executeSql(`
  CREATE INDEX IF NOT EXISTS idx_users_sync_status ON users(sync_status)
`)
await store.executeSql(`
  CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)
`)
```

### CRUD Operations

```typescript
// INSERT
const values: relationalStore.ValuesBucket = {
  'id': user.id,
  'name': user.name,
  'email': user.email,
  'sync_status': SyncStatus.SYNCED,
  'created_at': Date.now(),
  'updated_at': Date.now()
}
await store.insert('users', values)

// QUERY
const predicates = new relationalStore.RdbPredicates('users')
predicates.equalTo('id', userId)
const resultSet = await store.query(predicates)

// QUERY with conditions
const predicates = new relationalStore.RdbPredicates('users')
predicates.notEqualTo('sync_status', SyncStatus.PENDING_DELETE)
predicates.orderByDesc('created_at')
predicates.limitAs(20)
predicates.offsetAs(0)
const resultSet = await store.query(predicates)

// UPDATE
const updateValues: relationalStore.ValuesBucket = {
  'name': newName,
  'updated_at': Date.now()
}
const updatePredicates = new relationalStore.RdbPredicates('users')
updatePredicates.equalTo('id', userId)
await store.update(updateValues, updatePredicates)

// DELETE
const deletePredicates = new relationalStore.RdbPredicates('users')
deletePredicates.equalTo('id', userId)
await store.delete(deletePredicates)
```

### ResultSet Navigation

```typescript
const resultSet = await store.query(predicates)
const items = new Array<UserEntity>()

while (resultSet.goToNextRow()) {
  const entity = new UserEntity()
  entity.id = resultSet.getString(resultSet.getColumnIndex('id'))
  entity.name = resultSet.getString(resultSet.getColumnIndex('name'))
  entity.email = resultSet.getString(resultSet.getColumnIndex('email'))
  entity.createdAt = resultSet.getLong(resultSet.getColumnIndex('created_at'))
  items.push(entity)
}

resultSet.close() // ALWAYS close ResultSet
```

### RdbPredicates API

| Method | Purpose | Example |
|--------|---------|---------|
| `equalTo(field, value)` | Equals | `predicates.equalTo('id', '123')` |
| `notEqualTo(field, value)` | Not equals | `predicates.notEqualTo('status', 'deleted')` |
| `greaterThan(field, value)` | Greater than | `predicates.greaterThan('age', 18)` |
| `lessThan(field, value)` | Less than | `predicates.lessThan('price', 100)` |
| `like(field, pattern)` | Pattern match | `predicates.like('name', '%john%')` |
| `in(field, values)` | In set | `predicates.in('status', ['active', 'pending'])` |
| `between(field, low, high)` | Range | `predicates.between('age', 18, 65)` |
| `isNull(field)` | Is null | `predicates.isNull('avatar_url')` |
| `isNotNull(field)` | Is not null | `predicates.isNotNull('email')` |
| `orderByAsc(field)` | Ascending sort | `predicates.orderByAsc('name')` |
| `orderByDesc(field)` | Descending sort | `predicates.orderByDesc('created_at')` |
| `limitAs(count)` | Limit results | `predicates.limitAs(20)` |
| `offsetAs(offset)` | Skip results | `predicates.offsetAs(40)` |
| `and()` | AND condition | Between predicate calls |
| `or()` | OR condition | Between predicate calls |

---

## HUKS Security Reference

### Key Algorithms

| Algorithm | Constants | Use Case |
|-----------|-----------|----------|
| AES | `HUKS_ALG_AES` | Symmetric encryption |
| RSA | `HUKS_ALG_RSA` | Asymmetric encryption, signing |
| ECC | `HUKS_ALG_ECC` | Key agreement, signing |
| ED25519 | `HUKS_ALG_ED25519` | Digital signatures |
| HMAC | `HUKS_ALG_HMAC` | Message authentication |

### AES Key Sizes

| Size | Constant |
|------|----------|
| 128-bit | `HUKS_AES_KEY_SIZE_128` |
| 192-bit | `HUKS_AES_KEY_SIZE_192` |
| 256-bit | `HUKS_AES_KEY_SIZE_256` |

### Block Modes

| Mode | Constant | Notes |
|------|----------|-------|
| GCM | `HUKS_MODE_GCM` | Recommended for authenticated encryption |
| CBC | `HUKS_MODE_CBC` | Requires IV |
| CTR | `HUKS_MODE_CTR` | Stream mode |
| ECB | `HUKS_MODE_ECB` | NOT recommended |

### HUKS Operations Flow

```
1. generateKeyItem(alias, options)  -> Create key in keystore
2. isKeyItemExist(alias, options)   -> Check key exists
3. initSession(alias, options)      -> Start crypto session -> returns handle
4. updateSession(handle, options)   -> Process data chunks (optional)
5. finishSession(handle, options)   -> Complete operation -> returns result
6. abortSession(handle, options)    -> Cancel operation
7. deleteKeyItem(alias, options)    -> Remove key from keystore
```

### Security Best Practices

| Practice | Description |
|----------|-------------|
| Use GCM mode | Provides both encryption and authentication |
| 256-bit keys | Maximum security for AES |
| Unique aliases | One key per purpose (auth, data, backup) |
| Key rotation | Regenerate keys periodically |
| Error handling | Always wrap HUKS calls in try-catch |
| Cleanup | Call abortSession on failure |

---

## WorkScheduler Reference

### WorkInfo Configuration

| Property | Type | Description |
|----------|------|-------------|
| `workId` | number | Unique work identifier |
| `networkType` | NetworkType | Required network type |
| `isCharging` | boolean | Require charging |
| `batteryLevel` | number | Minimum battery level |
| `storageRequest` | StorageRequest | Storage condition |
| `isRepeat` | boolean | Repeating work |
| `repeatCycleTime` | number | Repeat interval (ms) |
| `repeatCount` | number | Max repeat count |
| `isPersisted` | boolean | Survive reboot |

### NetworkType Options

| Type | Constant | Description |
|------|----------|-------------|
| Any | `NETWORK_TYPE_ANY` | Any network |
| WiFi | `NETWORK_TYPE_WIFI` | WiFi only |
| Mobile | `NETWORK_TYPE_MOBILE` | Mobile only |
| Bluetooth | `NETWORK_TYPE_BLUETOOTH` | Bluetooth |
| WiFi P2P | `NETWORK_TYPE_WIFI_P2P` | WiFi P2P |

### WorkScheduler API

```typescript
import { workScheduler } from '@ohos.WorkSchedulerExtensionAbility'

// Schedule work
workScheduler.startWork(workInfo)

// Cancel specific work
workScheduler.stopWork(workId)

// Cancel all work
workScheduler.stopAndClearWorks()

// Check if work is running
workScheduler.isLastWorkTimeOut(workId)

// Get work status
workScheduler.obtainAllWorks()
```

### WorkSchedulerExtensionAbility

```typescript
// module.json5 registration
{
  "extensionAbilities": [
    {
      "name": "SyncWorker",
      "type": "workScheduler",
      "srcEntry": "./ets/workers/SyncWorker.ets"
    }
  ]
}

// Worker implementation
import { WorkSchedulerExtensionAbility, workScheduler } from '@ohos.WorkSchedulerExtensionAbility'

export default class SyncWorker extends WorkSchedulerExtensionAbility {
  onWorkStart(workInfo: workScheduler.WorkInfo): void {
    // Execute sync work
  }

  onWorkStop(workInfo: workScheduler.WorkInfo): void {
    // Cleanup
  }
}
```

---

## NetworkKit Reference

### Network Status Monitoring

```typescript
import { connection } from '@kit.NetworkKit'

export class NetworkMonitor {
  private netConnection: connection.NetConnection | undefined = undefined
  private _isOnline: boolean = true

  isOnline(): boolean {
    return this._isOnline
  }

  startMonitoring(): void {
    this.netConnection = connection.createNetConnection()

    this.netConnection.on('netAvailable', () => {
      this._isOnline = true
    })

    this.netConnection.on('netUnavailable', () => {
      this._isOnline = false
    })

    this.netConnection.register(() => {})
  }

  stopMonitoring(): void {
    if (this.netConnection !== undefined) {
      this.netConnection.unregister(() => {})
      this.netConnection = undefined
    }
  }
}
```

### HTTP Requests

```typescript
import { http } from '@kit.NetworkKit'

export class HttpClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async get<T>(path: string): Promise<Result<T, AppError>> {
    const httpRequest = http.createHttp()

    try {
      const response = await httpRequest.request(
        this.baseUrl + path,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          },
          connectTimeout: 10000,
          readTimeout: 30000
        }
      )

      if (response.responseCode === 200) {
        const data = JSON.parse(response.result as string) as T
        return Result.success(data)
      } else if (response.responseCode === 401) {
        return Result.failure(new AppError(AppError.UNAUTHORIZED, 'Unauthorized'))
      } else {
        return Result.failure(new AppError(AppError.NETWORK, `HTTP ${response.responseCode}`))
      }
    } catch (e) {
      return Result.failure(new AppError(AppError.NETWORK, 'Network request failed'))
    } finally {
      httpRequest.destroy()
    }
  }

  async post<T>(path: string, body: string): Promise<Result<T, AppError>> {
    const httpRequest = http.createHttp()

    try {
      const response = await httpRequest.request(
        this.baseUrl + path,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: body,
          connectTimeout: 10000,
          readTimeout: 30000
        }
      )

      if (response.responseCode >= 200 && response.responseCode < 300) {
        const data = JSON.parse(response.result as string) as T
        return Result.success(data)
      } else {
        return Result.failure(new AppError(AppError.NETWORK, `HTTP ${response.responseCode}`))
      }
    } catch (e) {
      return Result.failure(new AppError(AppError.NETWORK, 'Network request failed'))
    } finally {
      httpRequest.destroy()
    }
  }
}
```

---

## Testing Reference

### @ohos/hypium Test Framework

```typescript
import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from '@ohos/hypium'

export default function featureTest() {
  describe('FeatureName', () => {
    beforeAll(() => {
      // Run once before all tests
    })

    beforeEach(() => {
      // Run before each test
    })

    afterEach(() => {
      // Run after each test
    })

    afterAll(() => {
      // Run once after all tests
    })

    it('should do something', () => {
      // Test body
    })
  })
}
```

### Assertion Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `assertEqual(expected)` | Equality | `expect(value).assertEqual(42)` |
| `assertDeepEquals(expected)` | Deep equality | `expect(obj).assertDeepEquals(expected)` |
| `assertTrue()` | Assert true | `expect(result).assertTrue()` |
| `assertFalse()` | Assert false | `expect(result).assertFalse()` |
| `assertNull()` | Assert null | `expect(value).assertNull()` |
| `assertUndefined()` | Assert undefined | `expect(value).assertUndefined()` |
| `assertNotUndefined()` | Assert not undefined | `expect(value).assertNotUndefined()` |
| `assertLarger(n)` | Greater than | `expect(count).assertLarger(0)` |
| `assertLess(n)` | Less than | `expect(count).assertLess(100)` |
| `assertContain(substr)` | Contains | `expect(str).assertContain('hello')` |
| `assertThrowError(msg)` | Throws | `expect(fn).assertThrowError('msg')` |

### Test Configuration

```json5
// entry/src/test/List.test.ets
import loginViewModelTest from './LoginViewModelTest'
import userRepositoryTest from './UserRepositoryTest'
import resultTest from './ResultTest'

export default function testsuite() {
  loginViewModelTest()
  userRepositoryTest()
  resultTest()
}
```

### Running Tests

```bash
# Via hdc (USB connected device)
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test

# Via DevEco Studio
# Right-click test file -> Run Tests
# Or: Run > Run All Tests

# Specific test
hdc shell aa test -b com.example.app -m entry_test -s unittest /ets/test/List.test -s class LoginViewModelTest
```

---

## DevEco Studio Reference

### Key Commands

| Action | Shortcut (macOS) | Shortcut (Windows) |
|--------|-------------------|---------------------|
| Build | Cmd+B | Ctrl+B |
| Run | Ctrl+R | Shift+F10 |
| Debug | Ctrl+D | Shift+F9 |
| Format code | Opt+Cmd+L | Ctrl+Alt+L |
| Quick fix | Opt+Enter | Alt+Enter |
| Find in files | Cmd+Shift+F | Ctrl+Shift+F |
| Go to definition | Cmd+Click | Ctrl+Click |

### Build Commands (CLI)

```bash
# Build HAP package
hvigorw assembleHap --mode module -p product=default -p module=entry

# Build APP package
hvigorw assembleApp --mode project -p product=default

# Clean build
hvigorw clean

# Install dependencies
ohpm install

# Update dependencies
ohpm update
```

### hdc Device Commands

```bash
# List connected devices
hdc list targets

# Install HAP
hdc install entry/build/default/outputs/default/entry-default-signed.hap

# Uninstall
hdc uninstall com.example.app

# View logs
hdc hilog

# Filter logs by tag
hdc hilog -t ArcanaApp

# Shell access
hdc shell

# File push/pull
hdc file send local_file /data/local/tmp/
hdc file recv /data/local/tmp/remote_file ./
```

### Configuration Files

| File | Purpose |
|------|---------|
| `AppScope/app.json5` | App-level config (bundleName, vendor, version) |
| `entry/src/main/module.json5` | Module config (abilities, permissions, routes) |
| `entry/oh-package.json5` | Module dependencies |
| `entry/build-profile.json5` | Build config (API version, signing) |
| `oh-package.json5` | Root package config |
| `build-profile.json5` | Root build config |
| `hvigorfile.ts` | Build script |
