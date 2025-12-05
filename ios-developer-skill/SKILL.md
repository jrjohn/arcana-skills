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

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested SPM settings and library versions. **NEVER reconfigure project structure or modify Package.swift / project settings**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-ios.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-ios template"
```

**Step 3**: Modify project name and Bundle ID
Only modify the following required items:
- Xcode project name (Rename Project)
- Bundle Identifier in `Info.plist`
- Rename main target and scheme
- Update module name imports in code

**Step 4**: Clean up example code
The cloned project contains example UI (e.g., Arcana User Management). Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `Core/` - Common utilities (Analytics, Common, Cache)
- `Infrastructure/` - DI configuration, Security
- `Data/Local/` - SwiftData base configuration
- `Data/Repositories/` - Repository base classes
- `AppEntry.swift` - App entry point
- `Navigation/` - Navigation configuration (modify routes)

**Example files to REPLACE**:
- `Presentation/Views/` - Delete all example screens, create new project UI
- `Presentation/ViewModels/` - Delete example ViewModel, create new ViewModel
- `Domain/Models/` - Delete example Models, create new Domain Models
- `Data/Local/Entities/` - Delete example Entity, create new Entity
- `Data/Remote/` - Modify API endpoints

**Step 5**: Verify build
```bash
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' build
```

### ❌ Prohibited Actions
- **DO NOT** create new Xcode project from scratch
- **DO NOT** modify version numbers in `Package.swift`
- **DO NOT** add or remove SPM dependencies (unless explicitly required)
- **DO NOT** modify Xcode project Build Settings
- **DO NOT** reconfigure SwiftUI, SwiftData, Alamofire, or other library settings

### ✅ Allowed Modifications
- Add business-related Swift code (following existing architecture)
- Add UI screens (using existing SwiftUI settings)
- Add Domain Models, Repository, ViewModel
- Modify resources in Assets.xcassets
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
```swift
/**
 * Requirements extracted from specification documents:
 *
 * SRS (Software Requirements Specification):
 * - SRS-001: User must be able to login with email/password
 * - SRS-002: App must show splash screen for 2 seconds
 * - SRS-003: Dashboard must display user's stars and coins
 *
 * SDD (Software Design Document):
 * - SDD-001: Use SwiftData for local persistence
 * - SDD-002: Implement MVVM Input/Output/Effect pattern
 * - SDD-003: Store tokens in Keychain
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```swift
// Tests/ViewModels/LoginViewModelTests.swift
import XCTest
@testable import YourApp

final class LoginViewModelTests: XCTestCase {

    var viewModel: LoginViewModel!
    var mockAuthRepository: MockAuthRepository!

    override func setUp() {
        super.setUp()
        mockAuthRepository = MockAuthRepository()
        viewModel = LoginViewModel(authRepository: mockAuthRepository)
    }

    // SRS-001: User must be able to login with email/password
    func testLoginWithValidCredentials_ShouldSucceed() async {
        // Given
        mockAuthRepository.loginResult = .success(())

        // When
        viewModel.onInput(.updateEmail("test@test.com"))
        viewModel.onInput(.updatePassword("password123"))
        await viewModel.onInput(.submit)

        // Then
        XCTAssertTrue(viewModel.output.isLoginSuccess)
        XCTAssertNil(viewModel.output.error)
    }

    // SRS-001: Invalid credentials should show error
    func testLoginWithInvalidCredentials_ShouldShowError() async {
        // Given
        mockAuthRepository.loginResult = .failure(AuthError.invalidCredentials)

        // When
        await viewModel.onInput(.submit)

        // Then
        XCTAssertFalse(viewModel.output.isLoginSuccess)
        XCTAssertNotNil(viewModel.output.error)
    }
}
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL SRS and SDD items have tests:
```swift
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * SRS Requirements:
 * [x] SRS-001: Login with email/password - LoginViewModelTests
 * [x] SRS-002: Splash screen display - SplashViewModelTests
 * [x] SRS-003: Register new account - RegisterViewModelTests
 * [x] SRS-010: Display user stars - DashboardViewModelTests
 * [x] SRS-011: Display S-coins - DashboardViewModelTests
 * [ ] SRS-020: List training items - TODO
 *
 * SDD Design Requirements:
 * [x] SDD-001: SwiftData persistence - RepositoryTests
 * [x] SDD-002: MVVM Input/Output/Effect pattern - ViewModelTests
 * [x] SDD-003: Keychain token storage - KeychainServiceTests
 * [ ] SDD-004: Offline-first sync - TODO
 */
```

#### Step 4: Mock API Implementation
For APIs not yet available from Cloud team, implement mock repositories:
```swift
// Data/Repositories/Mock/MockAuthRepository.swift
final class MockAuthRepository: AuthRepositoryProtocol {

    // Mock user data for testing
    private static let mockUsers = [
        MockUser(email: "test@test.com", password: "password123", name: "Test User"),
        MockUser(email: "demo@demo.com", password: "demo123", name: "Demo User")
    ]

    // Injectable result for testing
    var loginResult: Result<Void, Error> = .success(())

    func login(email: String, password: String) async throws {
        // Simulate network delay
        try await Task.sleep(nanoseconds: 1_000_000_000)

        if let user = Self.mockUsers.first(where: { $0.email == email && $0.password == password }) {
            // Save mock token
            UserDefaults.standard.set("mock_token_\(Date().timeIntervalSince1970)", forKey: "access_token")
            UserDefaults.standard.set(user.name, forKey: "user_name")
        } else {
            throw AuthError.invalidCredentials
        }
    }

    func isLoggedIn() -> Bool {
        UserDefaults.standard.string(forKey: "access_token") != nil
    }
}

// Infrastructure/DI/RepositoryContainer.swift - Switch between Mock and Real
struct RepositoryContainer {
    static func makeAuthRepository() -> AuthRepositoryProtocol {
        #if DEBUG
        return MockAuthRepository()  // Development/Testing
        #else
        return AuthRepository()      // Production
        #endif
    }
}
```

#### Step 5: Run All Tests Before Completion
```bash
# Run all tests via command line
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15'

# Run tests with coverage
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' -enableCodeCoverage YES

# Run specific test class
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=iPhone 15' -only-testing:YourAppTests/LoginViewModelTests
```

#### Test Directory Structure
```
YourApp/
├── Sources/                         # Production code
├── Tests/
│   ├── ViewModels/
│   │   ├── LoginViewModelTests.swift
│   │   ├── RegisterViewModelTests.swift
│   │   ├── DashboardViewModelTests.swift
│   │   └── SplashViewModelTests.swift
│   ├── Services/
│   │   └── UserServiceTests.swift
│   ├── Repositories/
│   │   └── AuthRepositoryTests.swift
│   └── Mocks/
│       ├── MockAuthRepository.swift
│       └── MockUserService.swift
└── UITests/
    ├── LoginUITests.swift
    └── DashboardUITests.swift
```

### 2. Project Structure
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
