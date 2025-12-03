# iOS Architecture Reference

Complete technical reference document based on Arcana iOS enterprise architecture.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Clean Architecture Details](#clean-architecture-details)
3. [SwiftUI Guide](#swiftui-guide)
4. [SwiftData Guide](#swiftdata-guide)
5. [Dependency Injection](#dependency-injection)
6. [Network Layer Design](#network-layer-design)
7. [Testing Strategy](#testing-strategy)
8. [Performance Optimization](#performance-optimization)

---

## Project Structure

### Recommended Modular Structure

```
Project/
├── App/
│   ├── ProjectApp.swift           # App entry point
│   ├── AppDelegate.swift          # App delegate (if needed)
│   └── ContentView.swift          # Root view
├── Presentation/                   # Presentation layer
│   ├── Views/
│   │   ├── Home/
│   │   │   ├── HomeView.swift
│   │   │   └── HomeViewModel.swift
│   │   ├── User/
│   │   │   ├── UserListView.swift
│   │   │   ├── UserDetailView.swift
│   │   │   └── UserViewModel.swift
│   │   └── Components/            # Reusable UI components
│   │       ├── LoadingView.swift
│   │       ├── ErrorView.swift
│   │       └── PrimaryButton.swift
│   ├── Navigation/
│   │   ├── AppRouter.swift
│   │   └── NavigationPath+Extensions.swift
│   └── Theme/
│       ├── Colors.swift
│       ├── Typography.swift
│       └── Spacing.swift
├── Domain/                         # Domain layer
│   ├── Models/
│   │   ├── User.swift
│   │   └── Result+Extensions.swift
│   ├── Repositories/              # Repository protocols
│   │   └── UserRepositoryProtocol.swift
│   └── Services/
│       └── UserService.swift
├── Data/                           # Data layer
│   ├── Repositories/              # Repository implementations
│   │   └── UserRepository.swift
│   ├── Local/
│   │   ├── SwiftDataContainer.swift
│   │   └── Entities/
│   │       └── UserEntity.swift
│   └── Remote/
│       ├── APIClient.swift
│       ├── Endpoints/
│       │   └── UserEndpoint.swift
│       └── DTOs/
│           └── UserDTO.swift
└── Core/                           # Shared utilities
    ├── Extensions/
    ├── Utilities/
    └── Constants/
```

---

## Clean Architecture Details

### Layer Responsibilities

#### Presentation Layer

**Responsibilities**:
- Handle UI logic and user interactions
- Manage UI state via ViewModel
- Convert user actions to domain layer calls

**Contains**:
- SwiftUI Views
- ViewModels (Input/Output/Effect pattern)
- Navigation logic
- UI components

```swift
// ViewModel with Input/Output/Effect Pattern
import SwiftUI
import Observation

@Observable
final class UserListViewModel {

    // MARK: - Input
    enum Input {
        case loadUsers
        case refresh
        case selectUser(String)
        case deleteUser(String)
    }

    // MARK: - Output
    struct Output {
        var users: [User] = []
        var isLoading: Bool = false
        var isRefreshing: Bool = false
        var error: String?

        var isEmpty: Bool {
            users.isEmpty && !isLoading && error == nil
        }
    }

    // MARK: - Effect
    enum Effect: Equatable {
        case navigateToDetail(userId: String)
        case showError(String)
    }

    private(set) var output = Output()
    var effect: Effect?

    private let userService: UserServiceProtocol

    init(userService: UserServiceProtocol) {
        self.userService = userService
    }

    @MainActor
    func onInput(_ input: Input) {
        switch input {
        case .loadUsers:
            loadUsers()
        case .refresh:
            refresh()
        case .selectUser(let userId):
            effect = .navigateToDetail(userId: userId)
        case .deleteUser(let userId):
            deleteUser(userId)
        }
    }

    @MainActor
    private func loadUsers() {
        output.isLoading = true
        output.error = nil

        Task {
            do {
                output.users = try await userService.getUsers()
                output.isLoading = false
            } catch {
                output.error = error.localizedDescription
                output.isLoading = false
            }
        }
    }
}
```

#### Domain Layer

**Responsibilities**:
- Encapsulate business logic
- Define domain models
- Declare Repository protocols
- Coordinate multiple data sources

```swift
// Domain Model
struct User: Identifiable, Equatable, Sendable {
    let id: String
    var name: String
    var email: String
    var avatarURL: URL?
    let createdAt: Date
    var updatedAt: Date
}

// Repository Protocol
protocol UserRepositoryProtocol: Sendable {
    func getUsers() async throws -> [User]
    func getUser(id: String) async throws -> User?
    func createUser(_ user: User) async throws -> User
    func updateUser(_ user: User) async throws
    func deleteUser(id: String) async throws
}

// Business Service
actor UserService: UserServiceProtocol {
    private let repository: UserRepositoryProtocol
    private let analyticsService: AnalyticsServiceProtocol

    init(repository: UserRepositoryProtocol, analyticsService: AnalyticsServiceProtocol) {
        self.repository = repository
        self.analyticsService = analyticsService
    }

    func getUsers() async throws -> [User] {
        try await repository.getUsers()
    }

    func createUser(name: String, email: String) async throws -> User {
        // Business validation
        guard !name.isEmpty else {
            throw ValidationError.emptyName
        }
        guard email.isValidEmail else {
            throw ValidationError.invalidEmail
        }

        let user = User(
            id: UUID().uuidString,
            name: name.trimmingCharacters(in: .whitespaces),
            email: email.lowercased().trimmingCharacters(in: .whitespaces),
            avatarURL: nil,
            createdAt: Date(),
            updatedAt: Date()
        )

        let created = try await repository.createUser(user)
        await analyticsService.track("user_created", properties: ["userId": created.id])
        return created
    }
}
```

#### Data Layer

**Responsibilities**:
- Implement Repository protocols
- Manage local (SwiftData) and remote (API) data sources
- Handle data synchronization and caching
- Data model conversion (DTO ↔ Entity ↔ Domain)

```swift
// Repository Implementation
final class UserRepository: UserRepositoryProtocol, @unchecked Sendable {
    private let modelContext: ModelContext
    private let apiClient: APIClient
    private let syncManager: SyncManager

    init(modelContext: ModelContext, apiClient: APIClient, syncManager: SyncManager) {
        self.modelContext = modelContext
        self.apiClient = apiClient
        self.syncManager = syncManager
    }

    func getUsers() async throws -> [User] {
        let descriptor = FetchDescriptor<UserEntity>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        let entities = try modelContext.fetch(descriptor)
        return entities.map { $0.toDomain() }
    }

    func createUser(_ user: User) async throws -> User {
        let entity = user.toEntity()
        entity.syncStatus = .pending
        modelContext.insert(entity)
        try modelContext.save()

        // Schedule background sync
        await syncManager.scheduleSync()

        return user
    }
}
```

---

## SwiftUI Guide

### State Management

```swift
// Use @Observable for ViewModels (iOS 17+)
@Observable
final class SettingsViewModel {
    var isDarkMode: Bool = false
    var notificationsEnabled: Bool = true

    func toggleDarkMode() {
        isDarkMode.toggle()
    }
}

// View with ViewModel
struct SettingsView: View {
    @State private var viewModel = SettingsViewModel()

    var body: some View {
        Form {
            Toggle("Dark Mode", isOn: $viewModel.isDarkMode)
            Toggle("Notifications", isOn: $viewModel.notificationsEnabled)
        }
    }
}

// Use @Bindable for two-way binding with @Observable
struct EditUserView: View {
    @Bindable var viewModel: EditUserViewModel

    var body: some View {
        Form {
            TextField("Name", text: $viewModel.output.name)
            TextField("Email", text: $viewModel.output.email)
        }
    }
}
```

### Navigation

```swift
// Type-safe navigation with NavigationPath
@Observable
final class AppRouter {
    var path = NavigationPath()

    enum Destination: Hashable {
        case userList
        case userDetail(userId: String)
        case userEdit(userId: String)
        case settings
    }

    func navigate(to destination: Destination) {
        path.append(destination)
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }

    func popToRoot() {
        path.removeLast(path.count)
    }
}

// Usage in ContentView
struct ContentView: View {
    @State private var router = AppRouter()

    var body: some View {
        NavigationStack(path: $router.path) {
            HomeView()
                .navigationDestination(for: AppRouter.Destination.self) { destination in
                    switch destination {
                    case .userList:
                        UserListView()
                    case .userDetail(let userId):
                        UserDetailView(userId: userId)
                    case .userEdit(let userId):
                        UserEditView(userId: userId)
                    case .settings:
                        SettingsView()
                    }
                }
        }
        .environment(router)
    }
}
```

### Reusable Components

```swift
// Loading Button
struct LoadingButton: View {
    let title: String
    let isLoading: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                }
                Text(title)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.accentColor)
            .foregroundColor(.white)
            .cornerRadius(10)
        }
        .disabled(isLoading)
    }
}

// Error View
struct ErrorView: View {
    let message: String
    let retryAction: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("Error", systemImage: "exclamationmark.triangle")
        } description: {
            Text(message)
        } actions: {
            Button("Try Again", action: retryAction)
                .buttonStyle(.bordered)
        }
    }
}

// Empty State View
struct EmptyStateView: View {
    let title: String
    let description: String
    let systemImage: String
    var action: (() -> Void)?
    var actionTitle: String?

    var body: some View {
        ContentUnavailableView {
            Label(title, systemImage: systemImage)
        } description: {
            Text(description)
        } actions: {
            if let action, let actionTitle {
                Button(actionTitle, action: action)
                    .buttonStyle(.bordered)
            }
        }
    }
}
```

---

## SwiftData Guide

### Model Definition

```swift
import SwiftData

@Model
final class UserEntity {
    @Attribute(.unique) var id: String
    var serverId: String?
    var name: String
    var email: String
    var avatarURL: URL?
    var createdAt: Date
    var updatedAt: Date
    var syncStatus: SyncStatus

    init(
        id: String = UUID().uuidString,
        serverId: String? = nil,
        name: String,
        email: String,
        avatarURL: URL? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        syncStatus: SyncStatus = .synced
    ) {
        self.id = id
        self.serverId = serverId
        self.name = name
        self.email = email
        self.avatarURL = avatarURL
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.syncStatus = syncStatus
    }
}

enum SyncStatus: String, Codable {
    case synced
    case pending
    case failed
}

// Domain mapping
extension UserEntity {
    func toDomain() -> User {
        User(
            id: id,
            name: name,
            email: email,
            avatarURL: avatarURL,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}

extension User {
    func toEntity() -> UserEntity {
        UserEntity(
            id: id,
            name: name,
            email: email,
            avatarURL: avatarURL,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}
```

### Container Setup

```swift
import SwiftData

@MainActor
final class SwiftDataContainer {
    static let shared = SwiftDataContainer()

    let container: ModelContainer

    private init() {
        let schema = Schema([
            UserEntity.self,
            // Add other models
        ])

        let configuration = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            cloudKitDatabase: .none
        )

        do {
            container = try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }

    var mainContext: ModelContext {
        container.mainContext
    }
}

// App setup
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(SwiftDataContainer.shared.container)
    }
}
```

### Queries and Mutations

```swift
// Query with predicate
func getActiveUsers() throws -> [UserEntity] {
    let predicate = #Predicate<UserEntity> { user in
        user.syncStatus != .failed
    }
    let descriptor = FetchDescriptor<UserEntity>(
        predicate: predicate,
        sortBy: [SortDescriptor(\.name)]
    )
    return try modelContext.fetch(descriptor)
}

// Query with pagination
func getUsersPaged(page: Int, pageSize: Int) throws -> [UserEntity] {
    var descriptor = FetchDescriptor<UserEntity>(
        sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
    )
    descriptor.fetchLimit = pageSize
    descriptor.fetchOffset = page * pageSize
    return try modelContext.fetch(descriptor)
}

// Batch update
func markAllAsSynced() throws {
    let users = try modelContext.fetch(FetchDescriptor<UserEntity>())
    for user in users {
        user.syncStatus = .synced
    }
    try modelContext.save()
}

// Delete with predicate
func deleteFailedSyncs() throws {
    try modelContext.delete(model: UserEntity.self, where: #Predicate { user in
        user.syncStatus == .failed
    })
}
```

---

## Dependency Injection

### Using swift-dependencies

```swift
import Dependencies

// Define dependency
struct UserRepositoryKey: DependencyKey {
    static let liveValue: any UserRepositoryProtocol = UserRepository(
        modelContext: SwiftDataContainer.shared.mainContext,
        apiClient: APIClient.shared,
        syncManager: SyncManager.shared
    )

    static let testValue: any UserRepositoryProtocol = MockUserRepository()
    static let previewValue: any UserRepositoryProtocol = PreviewUserRepository()
}

extension DependencyValues {
    var userRepository: any UserRepositoryProtocol {
        get { self[UserRepositoryKey.self] }
        set { self[UserRepositoryKey.self] = newValue }
    }
}

// Usage in ViewModel
@Observable
final class UserListViewModel {
    @ObservationIgnored
    @Dependency(\.userRepository) private var userRepository

    // ...
}

// Usage in tests
@Test
func testLoadUsers() async throws {
    await withDependencies {
        $0.userRepository = MockUserRepository(users: [.sample])
    } operation: {
        let viewModel = UserListViewModel()
        await viewModel.onInput(.loadUsers)

        #expect(viewModel.output.users.count == 1)
    }
}
```

---

## Network Layer Design

### API Client with Alamofire

```swift
import Alamofire

actor APIClient {
    static let shared = APIClient()

    private let session: Session
    private let baseURL: URL

    private init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60

        session = Session(configuration: configuration)
        baseURL = URL(string: "https://api.example.com/v1")!
    }

    func request<T: Decodable>(
        _ endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        let url = baseURL.appendingPathComponent(endpoint.path)

        let response = await session.request(
            url,
            method: endpoint.method,
            parameters: endpoint.parameters,
            encoding: endpoint.encoding,
            headers: endpoint.headers
        )
        .validate()
        .serializingDecodable(T.self)
        .response

        switch response.result {
        case .success(let value):
            return value
        case .failure(let error):
            throw APIError.from(error)
        }
    }
}

// Endpoint definition
protocol Endpoint {
    var path: String { get }
    var method: HTTPMethod { get }
    var parameters: Parameters? { get }
    var encoding: ParameterEncoding { get }
    var headers: HTTPHeaders? { get }
}

enum UserEndpoint: Endpoint {
    case getUsers
    case getUser(id: String)
    case createUser(UserDTO)
    case updateUser(id: String, UserDTO)
    case deleteUser(id: String)

    var path: String {
        switch self {
        case .getUsers:
            return "users"
        case .getUser(let id), .updateUser(let id, _), .deleteUser(let id):
            return "users/\(id)"
        case .createUser:
            return "users"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .getUsers, .getUser:
            return .get
        case .createUser:
            return .post
        case .updateUser:
            return .put
        case .deleteUser:
            return .delete
        }
    }

    var parameters: Parameters? {
        switch self {
        case .createUser(let dto), .updateUser(_, let dto):
            return dto.toDictionary()
        default:
            return nil
        }
    }

    var encoding: ParameterEncoding {
        switch method {
        case .get:
            return URLEncoding.default
        default:
            return JSONEncoding.default
        }
    }

    var headers: HTTPHeaders? {
        nil // Add auth headers if needed
    }
}
```

### Error Handling

```swift
enum APIError: Error, LocalizedError {
    case networkError(Error)
    case serverError(statusCode: Int, message: String?)
    case decodingError(Error)
    case unauthorized
    case notFound
    case unknown

    static func from(_ afError: AFError) -> APIError {
        switch afError {
        case .responseValidationFailed(let reason):
            if case .unacceptableStatusCode(let code) = reason {
                switch code {
                case 401:
                    return .unauthorized
                case 404:
                    return .notFound
                default:
                    return .serverError(statusCode: code, message: nil)
                }
            }
            return .unknown
        case .responseSerializationFailed:
            return .decodingError(afError)
        default:
            return .networkError(afError)
        }
    }

    var errorDescription: String? {
        switch self {
        case .networkError:
            return "Network connection error"
        case .serverError(let code, let message):
            return message ?? "Server error (\(code))"
        case .decodingError:
            return "Failed to process response"
        case .unauthorized:
            return "Session expired. Please log in again"
        case .notFound:
            return "Resource not found"
        case .unknown:
            return "An unexpected error occurred"
        }
    }
}
```

---

## Testing Strategy

### ViewModel Testing

```swift
import Testing
@testable import MyApp

@Suite("UserListViewModel Tests")
struct UserListViewModelTests {

    @Test("Initial state is correct")
    func initialState() {
        let viewModel = UserListViewModel(userService: MockUserService())

        #expect(viewModel.output.users.isEmpty)
        #expect(!viewModel.output.isLoading)
        #expect(viewModel.output.error == nil)
    }

    @Test("Load users updates state")
    func loadUsersSuccess() async {
        let mockUsers = [User.sample]
        let mockService = MockUserService(users: mockUsers)
        let viewModel = UserListViewModel(userService: mockService)

        await viewModel.onInput(.loadUsers)

        // Wait for async operation
        try? await Task.sleep(for: .milliseconds(100))

        #expect(viewModel.output.users == mockUsers)
        #expect(!viewModel.output.isLoading)
    }

    @Test("Load users handles error")
    func loadUsersError() async {
        let mockService = MockUserService(shouldFail: true)
        let viewModel = UserListViewModel(userService: mockService)

        await viewModel.onInput(.loadUsers)

        try? await Task.sleep(for: .milliseconds(100))

        #expect(viewModel.output.users.isEmpty)
        #expect(viewModel.output.error != nil)
    }

    @Test("Select user triggers navigation effect")
    func selectUser() async {
        let viewModel = UserListViewModel(userService: MockUserService())

        await viewModel.onInput(.selectUser("123"))

        #expect(viewModel.effect == .navigateToDetail(userId: "123"))
    }
}

// Mock Service
final class MockUserService: UserServiceProtocol, @unchecked Sendable {
    var users: [User]
    var shouldFail: Bool

    init(users: [User] = [], shouldFail: Bool = false) {
        self.users = users
        self.shouldFail = shouldFail
    }

    func getUsers() async throws -> [User] {
        if shouldFail {
            throw APIError.unknown
        }
        return users
    }
}
```

### SwiftUI View Testing

```swift
import Testing
import ViewInspector
@testable import MyApp

@Suite("UserListView Tests")
struct UserListViewTests {

    @Test("Shows loading indicator when loading")
    func showsLoadingIndicator() throws {
        let output = UserListViewModel.Output(isLoading: true)
        let view = UserListContent(output: output, onInput: { _ in })

        let progressView = try view.inspect().find(ViewType.ProgressView.self)
        #expect(progressView != nil)
    }

    @Test("Shows user list when loaded")
    func showsUserList() throws {
        let output = UserListViewModel.Output(users: [.sample])
        let view = UserListContent(output: output, onInput: { _ in })

        let list = try view.inspect().find(ViewType.List.self)
        #expect(list != nil)
    }

    @Test("Shows empty state when no users")
    func showsEmptyState() throws {
        let output = UserListViewModel.Output()
        let view = UserListContent(output: output, onInput: { _ in })

        let emptyView = try view.inspect().find(EmptyStateView.self)
        #expect(emptyView != nil)
    }
}
```

---

## Performance Optimization

### SwiftUI Optimization

```swift
// Use Equatable for better diffing
struct UserRow: View, Equatable {
    let user: User

    static func == (lhs: UserRow, rhs: UserRow) -> Bool {
        lhs.user.id == rhs.user.id &&
        lhs.user.name == rhs.user.name &&
        lhs.user.email == rhs.user.email
    }

    var body: some View {
        HStack {
            AsyncImage(url: user.avatarURL) { image in
                image.resizable()
            } placeholder: {
                Circle().fill(.gray.opacity(0.3))
            }
            .frame(width: 40, height: 40)
            .clipShape(Circle())

            VStack(alignment: .leading) {
                Text(user.name)
                    .font(.headline)
                Text(user.email)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

// Use id for stable list identity
struct UserListView: View {
    let users: [User]

    var body: some View {
        List(users) { user in
            UserRow(user: user)
        }
    }
}

// Lazy loading with LazyVStack
struct LazyUserList: View {
    let users: [User]

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(users) { user in
                    UserRow(user: user)
                }
            }
            .padding()
        }
    }
}
```

### Image Caching

```swift
import Kingfisher

struct CachedAsyncImage: View {
    let url: URL?
    let placeholder: Image

    var body: some View {
        KFImage(url)
            .placeholder { placeholder }
            .loadDiskFileSynchronously()
            .cacheMemoryOnly(false)
            .fade(duration: 0.25)
            .resizable()
    }
}

// Usage
CachedAsyncImage(
    url: user.avatarURL,
    placeholder: Image(systemName: "person.circle.fill")
)
.frame(width: 48, height: 48)
.clipShape(Circle())
```

### Memory Management

```swift
// Use weak references in closures
final class DataLoader {
    func load(completion: @escaping (Result<Data, Error>) -> Void) {
        // ...
    }
}

class MyViewController {
    let loader = DataLoader()

    func loadData() {
        loader.load { [weak self] result in
            guard let self else { return }
            // Handle result
        }
    }
}

// Cancel tasks when view disappears
struct UserDetailView: View {
    @State private var loadTask: Task<Void, Never>?

    var body: some View {
        Text("User Detail")
            .onAppear {
                loadTask = Task {
                    await loadUserData()
                }
            }
            .onDisappear {
                loadTask?.cancel()
            }
    }
}
```
