# iOS Design Patterns

Design patterns and best practices based on Arcana iOS architecture.

## Table of Contents

1. [Architecture Patterns](#architecture-patterns)
2. [UI Patterns](#ui-patterns)
3. [Data Patterns](#data-patterns)
4. [Concurrency Patterns](#concurrency-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Navigation Patterns](#navigation-patterns)

---

## Architecture Patterns

### Input/Output/Effect ViewModel Pattern

**Purpose**: Establish clear unidirectional data flow, separating user events and UI state.

```swift
import SwiftUI
import Observation

@Observable
@MainActor
final class FeatureViewModel {

    // ═══════════════════════════════════════════════════════════════
    // INPUT: Define all possible user events
    // ═══════════════════════════════════════════════════════════════
    enum Input {
        case initialize
        case updateField(String)
        case submit
        case retry
    }

    // ═══════════════════════════════════════════════════════════════
    // OUTPUT: UI state container
    // ═══════════════════════════════════════════════════════════════
    struct Output {
        var data: [Item] = []
        var fieldValue: String = ""
        var isLoading: Bool = false
        var error: String?

        // Derived state
        var isSubmitEnabled: Bool {
            !fieldValue.isEmpty && !isLoading
        }

        var isEmpty: Bool {
            data.isEmpty && !isLoading && error == nil
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // EFFECT: One-time events (navigation, alerts, haptics)
    // ═══════════════════════════════════════════════════════════════
    enum Effect: Equatable {
        case navigateBack
        case showAlert(String)
        case hapticFeedback
    }

    // ═══════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════
    private(set) var output = Output()
    var effect: Effect?

    private let service: FeatureServiceProtocol

    init(service: FeatureServiceProtocol) {
        self.service = service
    }

    // ═══════════════════════════════════════════════════════════════
    // INPUT HANDLER
    // ═══════════════════════════════════════════════════════════════
    func onInput(_ input: Input) {
        switch input {
        case .initialize:
            initialize()
        case .updateField(let value):
            output.fieldValue = value
        case .submit:
            submit()
        case .retry:
            initialize()
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ═══════════════════════════════════════════════════════════════
    private func initialize() {
        output.isLoading = true
        output.error = nil

        Task {
            do {
                output.data = try await service.getData()
                output.isLoading = false
            } catch {
                output.error = error.localizedDescription
                output.isLoading = false
            }
        }
    }

    private func submit() {
        output.isLoading = true

        Task {
            do {
                try await service.submit(output.fieldValue)
                effect = .navigateBack
            } catch {
                output.isLoading = false
                effect = .showAlert(error.localizedDescription)
            }
        }
    }
}
```

**Usage in View**:

```swift
struct FeatureView: View {
    @State private var viewModel: FeatureViewModel
    @Environment(\.dismiss) private var dismiss

    init(service: FeatureServiceProtocol) {
        _viewModel = State(initialValue: FeatureViewModel(service: service))
    }

    var body: some View {
        FeatureContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onAppear {
            viewModel.onInput(.initialize)
        }
        .onChange(of: viewModel.effect) { _, effect in
            handleEffect(effect)
        }
    }

    private func handleEffect(_ effect: FeatureViewModel.Effect?) {
        guard let effect else { return }

        switch effect {
        case .navigateBack:
            dismiss()
        case .showAlert(let message):
            // Show alert
            break
        case .hapticFeedback:
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        }

        viewModel.effect = nil
    }
}
```

---

### Repository Pattern (Offline-First)

**Purpose**: Unify data access, implement offline-first strategy.

```swift
// ═══════════════════════════════════════════════════════════════
// PROTOCOL
// ═══════════════════════════════════════════════════════════════
protocol ItemRepositoryProtocol: Sendable {
    func getItems() async throws -> [Item]
    func getItem(id: String) async throws -> Item?
    func createItem(_ item: Item) async throws -> Item
    func updateItem(_ item: Item) async throws
    func deleteItem(id: String) async throws
    func syncWithRemote() async throws
}

// ═══════════════════════════════════════════════════════════════
// IMPLEMENTATION
// ═══════════════════════════════════════════════════════════════
@MainActor
final class ItemRepository: ItemRepositoryProtocol {
    private let modelContext: ModelContext
    private let apiClient: APIClient
    private let syncManager: SyncManager

    init(modelContext: ModelContext, apiClient: APIClient, syncManager: SyncManager) {
        self.modelContext = modelContext
        self.apiClient = apiClient
        self.syncManager = syncManager
    }

    // Read - directly from local database (single source of truth)
    func getItems() async throws -> [Item] {
        let descriptor = FetchDescriptor<ItemEntity>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        let entities = try modelContext.fetch(descriptor)
        return entities.map { $0.toDomain() }
    }

    // Write - local first, schedule sync
    func createItem(_ item: Item) async throws -> Item {
        let entity = item.toEntity()
        entity.syncStatus = .pending
        modelContext.insert(entity)
        try modelContext.save()

        // Schedule background sync
        await syncManager.scheduleSync()

        return item
    }

    func updateItem(_ item: Item) async throws {
        let predicate = #Predicate<ItemEntity> { $0.id == item.id }
        let descriptor = FetchDescriptor<ItemEntity>(predicate: predicate)

        guard let entity = try modelContext.fetch(descriptor).first else {
            throw RepositoryError.notFound
        }

        entity.name = item.name
        entity.updatedAt = Date()
        entity.syncStatus = .pending

        try modelContext.save()
        await syncManager.scheduleSync()
    }

    func deleteItem(id: String) async throws {
        let predicate = #Predicate<ItemEntity> { $0.id == id }
        let descriptor = FetchDescriptor<ItemEntity>(predicate: predicate)

        guard let entity = try modelContext.fetch(descriptor).first else {
            throw RepositoryError.notFound
        }

        entity.syncStatus = .deleted
        try modelContext.save()
        await syncManager.scheduleSync()
    }

    // Sync logic
    func syncWithRemote() async throws {
        // 1. Upload pending changes
        try await uploadPendingChanges()

        // 2. Download remote changes
        try await downloadRemoteChanges()
    }

    private func uploadPendingChanges() async throws {
        let predicate = #Predicate<ItemEntity> { $0.syncStatus == .pending }
        let descriptor = FetchDescriptor<ItemEntity>(predicate: predicate)
        let pendingItems = try modelContext.fetch(descriptor)

        for entity in pendingItems {
            do {
                if entity.serverId == nil {
                    let response = try await apiClient.createItem(entity.toDTO())
                    entity.serverId = response.id
                } else {
                    try await apiClient.updateItem(entity.serverId!, dto: entity.toDTO())
                }
                entity.syncStatus = .synced
            } catch {
                entity.syncStatus = .failed
            }
        }

        try modelContext.save()
    }

    private func downloadRemoteChanges() async throws {
        let remoteItems = try await apiClient.getItems()

        for dto in remoteItems {
            let predicate = #Predicate<ItemEntity> { $0.serverId == dto.id }
            let descriptor = FetchDescriptor<ItemEntity>(predicate: predicate)
            let existing = try modelContext.fetch(descriptor).first

            if let existing, existing.syncStatus == .synced {
                // Update local with remote data
                existing.name = dto.name
                existing.updatedAt = dto.updatedAt
            } else if existing == nil {
                // Insert new item
                let entity = dto.toEntity()
                modelContext.insert(entity)
            }
            // Skip if local has pending changes
        }

        try modelContext.save()
    }
}

enum SyncStatus: String, Codable {
    case synced
    case pending
    case failed
    case deleted
}
```

---

## UI Patterns

### Stateless View Pattern

**Purpose**: Separate UI from state management for better testability.

```swift
// ═══════════════════════════════════════════════════════════════
// STATEFUL CONTAINER
// ═══════════════════════════════════════════════════════════════
struct ProfileView: View {
    @State private var viewModel: ProfileViewModel

    init(userService: UserServiceProtocol) {
        _viewModel = State(initialValue: ProfileViewModel(userService: userService))
    }

    var body: some View {
        ProfileContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onAppear {
            viewModel.onInput(.load)
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// STATELESS CONTENT
// ═══════════════════════════════════════════════════════════════
struct ProfileContent: View {
    let output: ProfileViewModel.Output
    let onInput: (ProfileViewModel.Input) -> Void

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                ProfileHeader(
                    user: output.user,
                    onEditTap: { onInput(.editProfile) }
                )

                ProfileStats(stats: output.stats)

                ProfileActions(
                    onSettingsTap: { onInput(.openSettings) },
                    onLogoutTap: { onInput(.logout) }
                )
            }
            .padding()
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// REUSABLE COMPONENTS
// ═══════════════════════════════════════════════════════════════
struct ProfileHeader: View {
    let user: User?
    let onEditTap: () -> Void

    var body: some View {
        HStack {
            AsyncImage(url: user?.avatarURL) { image in
                image.resizable()
            } placeholder: {
                Circle().fill(.gray.opacity(0.3))
            }
            .frame(width: 72, height: 72)
            .clipShape(Circle())

            VStack(alignment: .leading) {
                Text(user?.name ?? "Loading...")
                    .font(.headline)
                Text(user?.email ?? "")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button(action: onEditTap) {
                Image(systemName: "pencil")
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// PREVIEW
// ═══════════════════════════════════════════════════════════════
#Preview {
    ProfileContent(
        output: ProfileViewModel.Output(
            user: .sample,
            stats: ProfileStats(posts: 42, followers: 1234, following: 567)
        ),
        onInput: { _ in }
    )
}
```

---

### Loading/Error/Empty State Pattern

**Purpose**: Unified handling of various UI states.

```swift
// ═══════════════════════════════════════════════════════════════
// UI STATE
// ═══════════════════════════════════════════════════════════════
enum UIState<T> {
    case loading
    case success(T)
    case error(String)
    case empty
}

// ═══════════════════════════════════════════════════════════════
// STATE VIEW
// ═══════════════════════════════════════════════════════════════
struct StateView<T, Content: View>: View {
    let state: UIState<T>
    let onRetry: () -> Void
    let emptyTitle: String
    let emptyDescription: String
    @ViewBuilder let content: (T) -> Content

    var body: some View {
        switch state {
        case .loading:
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)

        case .success(let data):
            content(data)

        case .error(let message):
            ContentUnavailableView {
                Label("Error", systemImage: "exclamationmark.triangle")
            } description: {
                Text(message)
            } actions: {
                Button("Try Again", action: onRetry)
                    .buttonStyle(.bordered)
            }

        case .empty:
            ContentUnavailableView {
                Label(emptyTitle, systemImage: "tray")
            } description: {
                Text(emptyDescription)
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// USAGE
// ═══════════════════════════════════════════════════════════════
struct ItemListView: View {
    @State private var viewModel = ItemListViewModel()

    var uiState: UIState<[Item]> {
        if viewModel.output.isLoading {
            return .loading
        } else if let error = viewModel.output.error {
            return .error(error)
        } else if viewModel.output.items.isEmpty {
            return .empty
        } else {
            return .success(viewModel.output.items)
        }
    }

    var body: some View {
        StateView(
            state: uiState,
            onRetry: { viewModel.onInput(.retry) },
            emptyTitle: "No Items",
            emptyDescription: "Add your first item to get started"
        ) { items in
            List(items) { item in
                ItemRow(item: item)
            }
        }
    }
}
```

---

## Data Patterns

### Data Model Layer Transformation

**Purpose**: Transform data between layers while maintaining separation.

```swift
// ═══════════════════════════════════════════════════════════════
// DOMAIN MODEL
// ═══════════════════════════════════════════════════════════════
struct User: Identifiable, Equatable, Sendable {
    let id: String
    var name: String
    var email: String
    var avatarURL: URL?
    var role: UserRole
    let createdAt: Date
    var updatedAt: Date
}

enum UserRole: String, Codable, Sendable {
    case admin, member, guest
}

// ═══════════════════════════════════════════════════════════════
// SWIFTDATA ENTITY
// ═══════════════════════════════════════════════════════════════
import SwiftData

@Model
final class UserEntity {
    @Attribute(.unique) var id: String
    var serverId: String?
    var name: String
    var email: String
    var avatarURL: URL?
    var role: String
    var createdAt: Date
    var updatedAt: Date
    var syncStatus: String

    init(/* ... */) { /* ... */ }
}

// ═══════════════════════════════════════════════════════════════
// DTO
// ═══════════════════════════════════════════════════════════════
struct UserDTO: Codable {
    let id: String
    let name: String
    let email: String
    let avatarUrl: String?
    let role: String
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, name, email, role
        case avatarUrl = "avatar_url"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// ═══════════════════════════════════════════════════════════════
// MAPPERS
// ═══════════════════════════════════════════════════════════════
extension UserEntity {
    func toDomain() -> User {
        User(
            id: id,
            name: name,
            email: email,
            avatarURL: avatarURL,
            role: UserRole(rawValue: role) ?? .guest,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}

extension User {
    func toEntity(syncStatus: SyncStatus = .synced) -> UserEntity {
        UserEntity(
            id: id,
            name: name,
            email: email,
            avatarURL: avatarURL,
            role: role.rawValue,
            createdAt: createdAt,
            updatedAt: updatedAt,
            syncStatus: syncStatus.rawValue
        )
    }
}

extension UserDTO {
    func toDomain() -> User {
        User(
            id: id,
            name: name,
            email: email,
            avatarURL: avatarUrl.flatMap(URL.init),
            role: UserRole(rawValue: role) ?? .guest,
            createdAt: ISO8601DateFormatter().date(from: createdAt) ?? Date(),
            updatedAt: ISO8601DateFormatter().date(from: updatedAt) ?? Date()
        )
    }

    func toEntity() -> UserEntity {
        UserEntity(
            id: UUID().uuidString,
            serverId: id,
            name: name,
            email: email,
            avatarURL: avatarUrl.flatMap(URL.init),
            role: role,
            createdAt: ISO8601DateFormatter().date(from: createdAt) ?? Date(),
            updatedAt: ISO8601DateFormatter().date(from: updatedAt) ?? Date(),
            syncStatus: SyncStatus.synced.rawValue
        )
    }
}
```

---

## Concurrency Patterns

### Structured Concurrency

**Purpose**: Safely manage async task lifecycle.

```swift
// ═══════════════════════════════════════════════════════════════
// TASK MANAGEMENT IN VIEWMODEL
// ═══════════════════════════════════════════════════════════════
@Observable
@MainActor
final class DataViewModel {
    private var loadTask: Task<Void, Never>?

    func load() {
        loadTask?.cancel()
        loadTask = Task {
            await loadData()
        }
    }

    func cancel() {
        loadTask?.cancel()
    }

    private func loadData() async {
        guard !Task.isCancelled else { return }
        // Load data
    }
}

// ═══════════════════════════════════════════════════════════════
// PARALLEL OPERATIONS
// ═══════════════════════════════════════════════════════════════
func loadDashboard() async throws -> Dashboard {
    async let user = userService.getCurrentUser()
    async let stats = statsService.getStats()
    async let notifications = notificationService.getUnread()

    return try await Dashboard(
        user: user,
        stats: stats,
        notifications: notifications
    )
}

// ═══════════════════════════════════════════════════════════════
// TASK GROUP FOR DYNAMIC TASKS
// ═══════════════════════════════════════════════════════════════
func loadAllUsers(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User?.self) { group in
        for id in ids {
            group.addTask {
                try? await self.userService.getUser(id: id)
            }
        }

        var users: [User] = []
        for try await user in group {
            if let user {
                users.append(user)
            }
        }
        return users
    }
}

// ═══════════════════════════════════════════════════════════════
// RETRY WITH BACKOFF
// ═══════════════════════════════════════════════════════════════
func withRetry<T>(
    maxAttempts: Int = 3,
    initialDelay: Duration = .milliseconds(100),
    maxDelay: Duration = .seconds(10),
    operation: () async throws -> T
) async throws -> T {
    var delay = initialDelay

    for attempt in 1...maxAttempts {
        do {
            return try await operation()
        } catch {
            if attempt == maxAttempts {
                throw error
            }

            try await Task.sleep(for: delay)
            delay = min(delay * 2, maxDelay)
        }
    }

    fatalError("Unreachable")
}

// Usage
let data = try await withRetry {
    try await apiClient.fetchData()
}
```

---

## Error Handling Patterns

### Result Pattern with Custom Errors

```swift
// ═══════════════════════════════════════════════════════════════
// CUSTOM ERROR TYPES
// ═══════════════════════════════════════════════════════════════
enum AppError: Error, LocalizedError {
    case network(NetworkError)
    case business(BusinessError)
    case local(LocalError)

    var errorDescription: String? {
        switch self {
        case .network(let error):
            return error.localizedDescription
        case .business(let error):
            return error.localizedDescription
        case .local(let error):
            return error.localizedDescription
        }
    }
}

enum NetworkError: Error, LocalizedError {
    case noConnection
    case timeout
    case serverError(Int)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .noConnection:
            return "No internet connection"
        case .timeout:
            return "Request timed out"
        case .serverError(let code):
            return "Server error (\(code))"
        case .unauthorized:
            return "Session expired"
        }
    }
}

enum BusinessError: Error, LocalizedError {
    case userNotFound
    case invalidInput(String)
    case permissionDenied

    var errorDescription: String? {
        switch self {
        case .userNotFound:
            return "User not found"
        case .invalidInput(let field):
            return "Invalid \(field)"
        case .permissionDenied:
            return "Permission denied"
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// ERROR MAPPING
// ═══════════════════════════════════════════════════════════════
extension APIError {
    func toAppError() -> AppError {
        switch self {
        case .networkError:
            return .network(.noConnection)
        case .unauthorized:
            return .network(.unauthorized)
        case .serverError(let code, _):
            return .network(.serverError(code))
        default:
            return .network(.serverError(500))
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// USAGE IN SERVICE
// ═══════════════════════════════════════════════════════════════
actor UserService {
    func getUser(id: String) async throws -> User {
        do {
            return try await repository.getUser(id: id)
        } catch let error as APIError {
            throw error.toAppError()
        } catch {
            throw AppError.local(.unknown)
        }
    }
}
```

---

## Navigation Patterns

### Type-Safe Navigation

```swift
// ═══════════════════════════════════════════════════════════════
// ROUTER
// ═══════════════════════════════════════════════════════════════
@Observable
final class AppRouter {
    var path = NavigationPath()
    var sheet: Sheet?
    var fullScreenCover: FullScreenCover?

    enum Destination: Hashable {
        case home
        case userList
        case userDetail(userId: String)
        case userEdit(userId: String)
        case settings
    }

    enum Sheet: Identifiable {
        case createUser
        case filter

        var id: String {
            switch self {
            case .createUser: return "createUser"
            case .filter: return "filter"
            }
        }
    }

    enum FullScreenCover: Identifiable {
        case imageViewer(URL)
        case onboarding

        var id: String {
            switch self {
            case .imageViewer: return "imageViewer"
            case .onboarding: return "onboarding"
            }
        }
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

    func present(_ sheet: Sheet) {
        self.sheet = sheet
    }

    func presentFullScreen(_ cover: FullScreenCover) {
        self.fullScreenCover = cover
    }

    func dismiss() {
        sheet = nil
        fullScreenCover = nil
    }
}

// ═══════════════════════════════════════════════════════════════
// ROOT VIEW
// ═══════════════════════════════════════════════════════════════
struct RootView: View {
    @State private var router = AppRouter()

    var body: some View {
        NavigationStack(path: $router.path) {
            HomeView()
                .navigationDestination(for: AppRouter.Destination.self) { destination in
                    destinationView(for: destination)
                }
        }
        .sheet(item: $router.sheet) { sheet in
            sheetView(for: sheet)
        }
        .fullScreenCover(item: $router.fullScreenCover) { cover in
            fullScreenView(for: cover)
        }
        .environment(router)
    }

    @ViewBuilder
    private func destinationView(for destination: AppRouter.Destination) -> some View {
        switch destination {
        case .home:
            HomeView()
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

    @ViewBuilder
    private func sheetView(for sheet: AppRouter.Sheet) -> some View {
        switch sheet {
        case .createUser:
            CreateUserView()
        case .filter:
            FilterView()
        }
    }

    @ViewBuilder
    private func fullScreenView(for cover: AppRouter.FullScreenCover) -> some View {
        switch cover {
        case .imageViewer(let url):
            ImageViewerView(url: url)
        case .onboarding:
            OnboardingView()
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// USAGE IN CHILD VIEW
// ═══════════════════════════════════════════════════════════════
struct UserListView: View {
    @Environment(AppRouter.self) private var router

    var body: some View {
        List {
            ForEach(users) { user in
                Button {
                    router.navigate(to: .userDetail(userId: user.id))
                } label: {
                    UserRow(user: user)
                }
            }
        }
        .toolbar {
            Button {
                router.present(.createUser)
            } label: {
                Image(systemName: "plus")
            }
        }
    }
}
```
