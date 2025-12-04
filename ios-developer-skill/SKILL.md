---
name: ios-developer-skill
description: iOS development guide based on Arcana iOS enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design, SwiftUI, SwiftData, and MVVM Input/Output/Effect pattern. Suitable for iOS project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# iOS Developer Skill

Professional iOS development skill based on [Arcana iOS](https://github.com/jrjohn/arcana-ios) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         SwiftUI + MVVM + Input/Output/Effect        │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + SwiftData + API     │
└─────────────────────────────────────────────────────┘
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation → Domain → Data
- **Interface Segregation**: Decouple layers through protocols
- **Dependency Inversion**: Data layer implements Domain layer interfaces

## Instructions

When handling iOS development tasks, follow these principles:

### 0. Reference Project Setup
**IMPORTANT**: Before starting any iOS development task, clone the reference project from GitHub:
```bash
git clone https://github.com/jrjohn/arcana-ios.git
```
Use this reference project to:
- Understand the architecture patterns and code structure
- Copy and adapt code examples for the current task
- Ensure consistency with enterprise architecture standards

### 1. Project Structure
```
arcana-ios/
├── Presentation/          # UI Layer
│   ├── Views/            # SwiftUI Views
│   ├── ViewModels/       # Input/Output/Effect ViewModel
│   └── Navigation/       # Navigation Logic
├── Domain/               # Domain Layer
│   ├── Models/           # Domain Models
│   ├── Services/         # Business Services
│   └── Repositories/     # Repository Protocols
└── Data/                 # Data Layer
    ├── Repositories/     # Repository Implementations
    ├── Local/            # SwiftData Local Storage
    │   └── Entities/     # Database Entities
    └── Remote/           # API Client
        ├── APIs/         # API Interfaces
        └── DTOs/         # Data Transfer Objects
```

### 2. ViewModel Input/Output/Effect Pattern

```swift
import SwiftUI
import Observation

@Observable
final class UserViewModel {

    // MARK: - Input: Sealed enum defining all events
    enum Input {
        case updateName(String)
        case updateEmail(String)
        case submit
    }

    // MARK: - Output: State container
    struct Output {
        var name: String = ""
        var email: String = ""
        var isLoading: Bool = false
        var error: String?
    }

    // MARK: - Effect: One-time events
    enum Effect {
        case navigateBack
        case showSnackbar(String)
    }

    private(set) var output = Output()
    var effect: Effect?

    private let userService: UserServiceProtocol

    init(userService: UserServiceProtocol) {
        self.userService = userService
    }

    // MARK: - Input Handler
    func onInput(_ input: Input) {
        switch input {
        case .updateName(let name):
            output.name = name
        case .updateEmail(let email):
            output.email = email
        case .submit:
            submit()
        }
    }

    private func submit() {
        Task {
            output.isLoading = true
            defer { output.isLoading = false }

            do {
                try await userService.updateUser(name: output.name, email: output.email)
                effect = .navigateBack
            } catch {
                output.error = error.localizedDescription
            }
        }
    }
}
```

### 3. Offline-First Strategy

```swift
import SwiftData

@MainActor
final class UserRepository: UserRepositoryProtocol {

    private let modelContext: ModelContext
    private let apiClient: APIClient
    private let syncManager: SyncManager

    init(modelContext: ModelContext, apiClient: APIClient, syncManager: SyncManager) {
        self.modelContext = modelContext
        self.apiClient = apiClient
        self.syncManager = syncManager
    }

    // SwiftData as single source of truth
    func getUsers() -> [User] {
        let descriptor = FetchDescriptor<UserEntity>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        let entities = (try? modelContext.fetch(descriptor)) ?? []
        return entities.map { $0.toDomain() }
    }

    // Local-first updates
    func updateUser(_ user: User) async throws {
        // 1. Immediately update local database
        let entity = user.toEntity()
        entity.syncStatus = .pending
        modelContext.insert(entity)
        try modelContext.save()

        // 2. Schedule background sync
        await syncManager.scheduleSyncWork()
    }

    // Background sync processing
    func syncPendingChanges() async {
        let descriptor = FetchDescriptor<UserEntity>(
            predicate: #Predicate { $0.syncStatus == .pending }
        )

        guard let pendingUsers = try? modelContext.fetch(descriptor) else { return }

        for entity in pendingUsers {
            do {
                try await apiClient.updateUser(entity.toDTO())
                entity.syncStatus = .synced
                try modelContext.save()
            } catch {
                // Keep pending status for retry
            }
        }
    }
}
```

### 4. Three-Layer Cache Strategy

```swift
actor CacheManager<Key: Hashable, Value> {

    private struct CacheEntry {
        let value: Value
        let timestamp: Date

        func isExpired(ttl: TimeInterval) -> Bool {
            Date().timeIntervalSince(timestamp) > ttl
        }
    }

    private let maxMemorySize: Int
    private let ttl: TimeInterval

    // L1: Memory cache (<1ms)
    private var memoryCache: [Key: CacheEntry] = [:]

    // L2: LRU + TTL cache
    private var lruCache: [Key: CacheEntry] = [:]
    private var lruOrder: [Key] = []

    // L3: SwiftData persistence (via Repository)

    init(maxMemorySize: Int = 100, ttl: TimeInterval = 300) {
        self.maxMemorySize = maxMemorySize
        self.ttl = ttl
    }

    func get(key: Key, loader: () async throws -> Value) async throws -> Value {
        // Check L1
        if let entry = memoryCache[key], !entry.isExpired(ttl: ttl) {
            return entry.value
        }

        // Check L2
        if let entry = lruCache[key], !entry.isExpired(ttl: ttl) {
            memoryCache[key] = entry
            return entry.value
        }

        // Load from data source
        let value = try await loader()
        let entry = CacheEntry(value: value, timestamp: Date())
        memoryCache[key] = entry
        addToLRU(key: key, entry: entry)

        return value
    }

    private func addToLRU(key: Key, entry: CacheEntry) {
        if lruOrder.count >= maxMemorySize {
            if let oldest = lruOrder.first {
                lruCache.removeValue(forKey: oldest)
                lruOrder.removeFirst()
            }
        }
        lruCache[key] = entry
        lruOrder.append(key)
    }
}
```

### 5. SwiftUI Best Practices

```swift
import SwiftUI

struct UserScreen: View {
    @State private var viewModel: UserViewModel

    init(userService: UserServiceProtocol) {
        _viewModel = State(initialValue: UserViewModel(userService: userService))
    }

    var body: some View {
        UserContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onChange(of: viewModel.effect) { _, effect in
            handleEffect(effect)
        }
    }

    private func handleEffect(_ effect: UserViewModel.Effect?) {
        guard let effect else { return }

        switch effect {
        case .navigateBack:
            // Navigate back
            break
        case .showSnackbar(let message):
            // Show snackbar
            break
        }

        viewModel.effect = nil
    }
}

// Stateless view for easy testing
struct UserContent: View {
    let output: UserViewModel.Output
    let onInput: (UserViewModel.Input) -> Void

    var body: some View {
        Form {
            TextField("Name", text: Binding(
                get: { output.name },
                set: { onInput(.updateName($0)) }
            ))

            TextField("Email", text: Binding(
                get: { output.email },
                set: { onInput(.updateEmail($0)) }
            ))

            if let error = output.error {
                Text(error)
                    .foregroundStyle(.red)
            }

            Button("Submit") {
                onInput(.submit)
            }
            .disabled(output.isLoading)
        }
    }
}
```

### 6. Dependency Injection (swift-dependencies)

```swift
import Dependencies

// Define dependency key
struct UserServiceKey: DependencyKey {
    static let liveValue: UserServiceProtocol = UserService()
    static let testValue: UserServiceProtocol = MockUserService()
}

extension DependencyValues {
    var userService: UserServiceProtocol {
        get { self[UserServiceKey.self] }
        set { self[UserServiceKey.self] = newValue }
    }
}

// Use in ViewModel
@Observable
final class UserViewModel {
    @ObservationIgnored
    @Dependency(\.userService) private var userService

    // ...
}
```

### 7. Form Validation

```swift
import SwiftUI

@Observable
final class FormState {
    var email: String = ""
    var emailTouched: Bool = false

    var emailError: String? {
        guard emailTouched else { return nil }

        if email.isEmpty {
            return "Email is required"
        }

        if !email.isValidEmail {
            return "Invalid email format"
        }

        return nil
    }

    var isValid: Bool {
        !email.isEmpty && email.isValidEmail
    }
}

extension String {
    var isValidEmail: Bool {
        let emailRegex = #"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"#
        return range(of: emailRegex, options: .regularExpression) != nil
    }
}
```

### 8. Pagination and Lazy Loading

```swift
@Observable
final class PaginatedListViewModel<T> {

    struct Output {
        var items: [T] = []
        var isLoading: Bool = false
        var hasMore: Bool = true
        var currentPage: Int = 0
        var totalCount: Int = 0
    }

    private(set) var output = Output()

    private let pageSize: Int = 10
    private let loader: (Int, Int) async throws -> (items: [T], total: Int)

    init(loader: @escaping (Int, Int) async throws -> (items: [T], total: Int)) {
        self.loader = loader
    }

    func loadNextPage() async {
        guard !output.isLoading, output.hasMore else { return }

        output.isLoading = true
        defer { output.isLoading = false }

        do {
            let result = try await loader(output.currentPage, pageSize)
            output.items.append(contentsOf: result.items)
            output.totalCount = result.total
            output.currentPage += 1
            output.hasMore = output.items.count < result.total
        } catch {
            // Handle error
        }
    }

    func onItemAppear(_ item: T) async where T: Identifiable {
        if let lastItem = output.items.last as? any Identifiable,
           (item as any Identifiable).id == lastItem.id {
            await loadNextPage()
        }
    }
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output/Effect pattern
- [ ] Repository implements offline-first
- [ ] SwiftUI views have no side effects
- [ ] Properly handle Swift Concurrency lifecycle
- [ ] Dependency injection configured correctly

### Performance Checks
- [ ] Avoid unnecessary SwiftUI redraws
- [ ] Use @Observable instead of Combine
- [ ] Images use appropriate caching strategy
- [ ] Lists use LazyVStack/LazyHStack

### Security Checks
- [ ] Sensitive data uses Keychain
- [ ] API keys not hardcoded
- [ ] Input validation complete
- [ ] Network requests use HTTPS

## Common Issues

### Swift Concurrency Issues
1. Ensure Actor isolation is correct
2. Use @MainActor for UI-related code
3. Avoid Data Race

### SwiftData Migration Issues
1. Define VersionedSchema
2. Configure SchemaMigrationPlan
3. Test migration paths

### Preview Failures
1. Ensure dependencies are properly mocked
2. Use #Preview macro
3. Use mock data in Preview

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Swift | 6.0+ |
| SwiftUI | iOS 17+ |
| SwiftData | iOS 17+ |
| Alamofire | 5.9+ |
| swift-dependencies | 1.0+ |
