# iOS Development Examples

Practical development examples based on Arcana iOS architecture.

## Table of Contents

1. [Complete Feature Implementation Examples](#complete-feature-implementation-examples)
2. [Common Problem Solutions](#common-problem-solutions)
3. [Code Refactoring Examples](#code-refactoring-examples)
4. [Testing Examples](#testing-examples)

---

## Complete Feature Implementation Examples

### Example 1: User Authentication Feature

Complete login feature implementation with form validation, error handling, and Keychain storage.

#### Domain Layer

```swift
// Domain/Models/AuthResult.swift
enum AuthResult {
    case success(user: User, token: String)
    case failure(AuthError)
}

enum AuthError: Error, LocalizedError {
    case invalidCredentials
    case networkError
    case userNotFound
    case accountLocked
    case unknown

    var errorDescription: String? {
        switch self {
        case .invalidCredentials:
            return "Invalid email or password"
        case .networkError:
            return "Network error. Please check your connection"
        case .userNotFound:
            return "Account not found"
        case .accountLocked:
            return "Account is locked. Please contact support"
        case .unknown:
            return "An unexpected error occurred"
        }
    }
}

// Domain/Repositories/AuthRepositoryProtocol.swift
protocol AuthRepositoryProtocol: Sendable {
    func login(email: String, password: String) async throws -> AuthResult
    func logout() async
    func isLoggedIn() -> Bool
    func getCurrentUser() async -> User?
}

// Domain/Services/AuthService.swift
actor AuthService {
    private let repository: AuthRepositoryProtocol
    private let tokenManager: TokenManager

    init(repository: AuthRepositoryProtocol, tokenManager: TokenManager) {
        self.repository = repository
        self.tokenManager = tokenManager
    }

    func login(email: String, password: String) async throws -> User {
        // Validate input
        guard !email.isEmpty else {
            throw AuthError.invalidCredentials
        }
        guard email.isValidEmail else {
            throw AuthError.invalidCredentials
        }
        guard password.count >= 6 else {
            throw AuthError.invalidCredentials
        }

        let result = try await repository.login(email: email, password: password)

        switch result {
        case .success(let user, let token):
            await tokenManager.saveToken(token)
            return user
        case .failure(let error):
            throw error
        }
    }

    func logout() async {
        await tokenManager.clearToken()
        await repository.logout()
    }
}
```

#### Data Layer

```swift
// Data/Repositories/AuthRepository.swift
final class AuthRepository: AuthRepositoryProtocol, @unchecked Sendable {
    private let apiClient: APIClient
    private let userDao: UserDAO
    private let sessionDao: SessionDAO

    init(apiClient: APIClient, userDao: UserDAO, sessionDao: SessionDAO) {
        self.apiClient = apiClient
        self.userDao = userDao
        self.sessionDao = sessionDao
    }

    func login(email: String, password: String) async throws -> AuthResult {
        do {
            let response: LoginResponse = try await apiClient.request(
                AuthEndpoint.login(email: email, password: password),
                responseType: LoginResponse.self
            )

            let user = response.user.toDomain()

            // Save user locally
            try await userDao.insert(user.toEntity())

            // Save session
            try await sessionDao.insert(SessionEntity(
                token: response.token,
                userId: user.id,
                expiresAt: response.expiresAt
            ))

            return .success(user: user, token: response.token)

        } catch let error as APIError {
            switch error {
            case .unauthorized:
                return .failure(.invalidCredentials)
            case .notFound:
                return .failure(.userNotFound)
            case .serverError(let code, _) where code == 423:
                return .failure(.accountLocked)
            case .networkError:
                return .failure(.networkError)
            default:
                return .failure(.unknown)
            }
        }
    }

    func logout() async {
        try? await sessionDao.clearAll()
    }

    func isLoggedIn() -> Bool {
        guard let session = try? sessionDao.getActiveSession() else {
            return false
        }
        return !session.isExpired
    }

    func getCurrentUser() async -> User? {
        guard let session = try? await sessionDao.getActiveSession() else {
            return nil
        }
        return try? await userDao.getUser(id: session.userId)?.toDomain()
    }
}
```

#### Presentation Layer

```swift
// Presentation/ViewModels/LoginViewModel.swift
import SwiftUI
import Observation

@Observable
@MainActor
final class LoginViewModel {

    // MARK: - Input
    enum Input {
        case updateEmail(String)
        case updatePassword(String)
        case togglePasswordVisibility
        case submit
    }

    // MARK: - Output
    struct Output {
        var email: String = ""
        var password: String = ""
        var isPasswordVisible: Bool = false
        var isLoading: Bool = false
        var emailError: String?
        var passwordError: String?

        var isValid: Bool {
            !email.isEmpty && email.isValidEmail && password.count >= 6
        }
    }

    // MARK: - Effect
    enum Effect: Equatable {
        case navigateToHome
        case showError(String)
    }

    private(set) var output = Output()
    var effect: Effect?

    private var emailTouched = false
    private var passwordTouched = false

    private let authService: AuthService

    init(authService: AuthService) {
        self.authService = authService
    }

    func onInput(_ input: Input) {
        switch input {
        case .updateEmail(let email):
            emailTouched = true
            output.email = email
            output.emailError = validateEmail(email)

        case .updatePassword(let password):
            passwordTouched = true
            output.password = password
            output.passwordError = validatePassword(password)

        case .togglePasswordVisibility:
            output.isPasswordVisible.toggle()

        case .submit:
            submit()
        }
    }

    private func validateEmail(_ email: String) -> String? {
        guard emailTouched else { return nil }
        if email.isEmpty { return "Email is required" }
        if !email.isValidEmail { return "Invalid email format" }
        return nil
    }

    private func validatePassword(_ password: String) -> String? {
        guard passwordTouched else { return nil }
        if password.isEmpty { return "Password is required" }
        if password.count < 6 { return "Password must be at least 6 characters" }
        return nil
    }

    private func submit() {
        guard output.isValid else {
            emailTouched = true
            passwordTouched = true
            output.emailError = validateEmail(output.email)
            output.passwordError = validatePassword(output.password)
            return
        }

        output.isLoading = true

        Task {
            do {
                _ = try await authService.login(
                    email: output.email,
                    password: output.password
                )
                effect = .navigateToHome
            } catch let error as AuthError {
                output.isLoading = false
                effect = .showError(error.localizedDescription)
            } catch {
                output.isLoading = false
                effect = .showError("An unexpected error occurred")
            }
        }
    }
}

// Presentation/Views/Login/LoginView.swift
struct LoginView: View {
    @State private var viewModel: LoginViewModel
    @Environment(AppRouter.self) private var router

    init(authService: AuthService) {
        _viewModel = State(initialValue: LoginViewModel(authService: authService))
    }

    var body: some View {
        LoginContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onChange(of: viewModel.effect) { _, effect in
            handleEffect(effect)
        }
    }

    private func handleEffect(_ effect: LoginViewModel.Effect?) {
        guard let effect else { return }

        switch effect {
        case .navigateToHome:
            router.navigateToHome()
        case .showError(let message):
            // Show alert or snackbar
            break
        }

        viewModel.effect = nil
    }
}

struct LoginContent: View {
    let output: LoginViewModel.Output
    let onInput: (LoginViewModel.Input) -> Void

    var body: some View {
        VStack(spacing: 24) {
            Text("Welcome Back")
                .font(.largeTitle)
                .fontWeight(.bold)

            VStack(spacing: 16) {
                // Email field
                VStack(alignment: .leading, spacing: 4) {
                    TextField("Email", text: Binding(
                        get: { output.email },
                        set: { onInput(.updateEmail($0)) }
                    ))
                    .textFieldStyle(.roundedBorder)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                    if let error = output.emailError {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }

                // Password field
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        if output.isPasswordVisible {
                            TextField("Password", text: Binding(
                                get: { output.password },
                                set: { onInput(.updatePassword($0)) }
                            ))
                        } else {
                            SecureField("Password", text: Binding(
                                get: { output.password },
                                set: { onInput(.updatePassword($0)) }
                            ))
                        }

                        Button {
                            onInput(.togglePasswordVisibility)
                        } label: {
                            Image(systemName: output.isPasswordVisible ? "eye.slash" : "eye")
                                .foregroundStyle(.secondary)
                        }
                    }
                    .textFieldStyle(.roundedBorder)

                    if let error = output.passwordError {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
            }

            // Submit button
            Button {
                onInput(.submit)
            } label: {
                HStack {
                    if output.isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    }
                    Text("Sign In")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.accentColor)
                .foregroundStyle(.white)
                .cornerRadius(10)
            }
            .disabled(output.isLoading)
        }
        .padding()
    }
}
```

---

### Example 2: List with Search and Pagination

```swift
// Presentation/ViewModels/UserListViewModel.swift
@Observable
@MainActor
final class UserListViewModel {

    enum Input {
        case loadInitial
        case loadMore
        case refresh
        case search(String)
        case selectUser(String)
    }

    struct Output {
        var users: [User] = []
        var searchQuery: String = ""
        var isLoading: Bool = false
        var isRefreshing: Bool = false
        var isLoadingMore: Bool = false
        var hasMorePages: Bool = true
        var error: String?
    }

    enum Effect: Equatable {
        case navigateToDetail(userId: String)
    }

    private(set) var output = Output()
    var effect: Effect?

    private var currentPage = 0
    private let pageSize = 20
    private var searchTask: Task<Void, Never>?

    private let userService: UserServiceProtocol

    init(userService: UserServiceProtocol) {
        self.userService = userService
    }

    func onInput(_ input: Input) {
        switch input {
        case .loadInitial:
            loadInitial()
        case .loadMore:
            loadMore()
        case .refresh:
            refresh()
        case .search(let query):
            search(query)
        case .selectUser(let userId):
            effect = .navigateToDetail(userId: userId)
        }
    }

    private func loadInitial() {
        output.isLoading = true
        output.error = nil
        currentPage = 0

        Task {
            do {
                let result = try await userService.getUsers(
                    page: 0,
                    size: pageSize,
                    query: output.searchQuery.isEmpty ? nil : output.searchQuery
                )
                output.users = result.users
                output.hasMorePages = result.hasMore
                output.isLoading = false
            } catch {
                output.error = error.localizedDescription
                output.isLoading = false
            }
        }
    }

    private func loadMore() {
        guard !output.isLoadingMore, output.hasMorePages else { return }

        output.isLoadingMore = true
        currentPage += 1

        Task {
            do {
                let result = try await userService.getUsers(
                    page: currentPage,
                    size: pageSize,
                    query: output.searchQuery.isEmpty ? nil : output.searchQuery
                )
                output.users.append(contentsOf: result.users)
                output.hasMorePages = result.hasMore
                output.isLoadingMore = false
            } catch {
                currentPage -= 1
                output.isLoadingMore = false
            }
        }
    }

    private func refresh() {
        output.isRefreshing = true
        currentPage = 0

        Task {
            do {
                let result = try await userService.getUsers(
                    page: 0,
                    size: pageSize,
                    query: output.searchQuery.isEmpty ? nil : output.searchQuery
                )
                output.users = result.users
                output.hasMorePages = result.hasMore
                output.isRefreshing = false
            } catch {
                output.isRefreshing = false
            }
        }
    }

    private func search(_ query: String) {
        output.searchQuery = query

        // Cancel previous search
        searchTask?.cancel()

        // Debounce
        searchTask = Task {
            try? await Task.sleep(for: .milliseconds(300))

            guard !Task.isCancelled else { return }

            loadInitial()
        }
    }
}

// Presentation/Views/UserList/UserListView.swift
struct UserListView: View {
    @State private var viewModel: UserListViewModel
    @Environment(AppRouter.self) private var router

    init(userService: UserServiceProtocol) {
        _viewModel = State(initialValue: UserListViewModel(userService: userService))
    }

    var body: some View {
        UserListContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onAppear {
            if viewModel.output.users.isEmpty {
                viewModel.onInput(.loadInitial)
            }
        }
        .onChange(of: viewModel.effect) { _, effect in
            guard let effect else { return }

            switch effect {
            case .navigateToDetail(let userId):
                router.navigate(to: .userDetail(userId: userId))
            }

            viewModel.effect = nil
        }
    }
}

struct UserListContent: View {
    let output: UserListViewModel.Output
    let onInput: (UserListViewModel.Input) -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            SearchBar(
                text: Binding(
                    get: { output.searchQuery },
                    set: { onInput(.search($0)) }
                )
            )
            .padding()

            // Content
            if output.isLoading && output.users.isEmpty {
                Spacer()
                ProgressView()
                Spacer()
            } else if let error = output.error, output.users.isEmpty {
                ErrorView(message: error) {
                    onInput(.loadInitial)
                }
            } else if output.users.isEmpty {
                EmptyStateView(
                    title: "No Users",
                    description: output.searchQuery.isEmpty
                        ? "No users available"
                        : "No users match your search",
                    systemImage: "person.3"
                )
            } else {
                List {
                    ForEach(output.users) { user in
                        UserRow(user: user)
                            .onTapGesture {
                                onInput(.selectUser(user.id))
                            }
                            .onAppear {
                                // Load more when reaching end
                                if user.id == output.users.last?.id {
                                    onInput(.loadMore)
                                }
                            }
                    }

                    if output.isLoadingMore {
                        HStack {
                            Spacer()
                            ProgressView()
                            Spacer()
                        }
                        .listRowSeparator(.hidden)
                    }
                }
                .listStyle(.plain)
                .refreshable {
                    onInput(.refresh)
                    // Wait for refresh to complete
                    try? await Task.sleep(for: .milliseconds(500))
                }
            }
        }
        .navigationTitle("Users")
    }
}

struct SearchBar: View {
    @Binding var text: String

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            TextField("Search users...", text: $text)
                .textFieldStyle(.plain)

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(10)
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}
```

---

## Common Problem Solutions

### Problem 1: @Observable ViewModel with @Environment

**Problem**: Cannot use @Environment with @Observable ViewModel

**Solution**: Use @State for ViewModel and pass dependencies through init

```swift
// Wrong - Won't work
struct UserView: View {
    @Environment(UserService.self) private var userService
    @State private var viewModel = UserViewModel() // Can't inject userService
}

// Correct - Pass through init
struct UserView: View {
    @State private var viewModel: UserViewModel

    init(userService: UserServiceProtocol) {
        _viewModel = State(initialValue: UserViewModel(userService: userService))
    }

    var body: some View {
        // ...
    }
}

// Or use a factory
struct UserView: View {
    @Environment(\.userServiceFactory) private var makeUserService
    @State private var viewModel: UserViewModel?

    var body: some View {
        Group {
            if let viewModel {
                UserContent(viewModel: viewModel)
            } else {
                ProgressView()
            }
        }
        .onAppear {
            if viewModel == nil {
                viewModel = UserViewModel(userService: makeUserService())
            }
        }
    }
}
```

### Problem 2: Task Cancellation on View Disappear

**Problem**: Tasks continue running after view disappears

**Solution**: Store and cancel tasks properly

```swift
struct UserDetailView: View {
    let userId: String
    @State private var user: User?
    @State private var loadTask: Task<Void, Never>?

    var body: some View {
        Group {
            if let user {
                UserDetailContent(user: user)
            } else {
                ProgressView()
            }
        }
        .onAppear {
            loadTask = Task {
                await loadUser()
            }
        }
        .onDisappear {
            loadTask?.cancel()
        }
    }

    private func loadUser() async {
        // Check for cancellation
        guard !Task.isCancelled else { return }

        do {
            user = try await userService.getUser(id: userId)
        } catch {
            // Handle error
        }
    }
}

// Better approach with ViewModel
@Observable
@MainActor
final class UserDetailViewModel {
    private var loadTask: Task<Void, Never>?

    func load(userId: String) {
        loadTask?.cancel()
        loadTask = Task {
            await loadUserData(userId: userId)
        }
    }

    func cancel() {
        loadTask?.cancel()
    }

    deinit {
        loadTask?.cancel()
    }
}
```

### Problem 3: SwiftData Context Thread Safety

**Problem**: ModelContext must be used on same actor/thread

**Solution**: Use @MainActor or create background context

```swift
// Main context for UI operations
@MainActor
final class UserRepository {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func getUsers() throws -> [UserEntity] {
        try modelContext.fetch(FetchDescriptor<UserEntity>())
    }
}

// Background operations
actor BackgroundDataManager {
    private let modelContainer: ModelContainer

    init(modelContainer: ModelContainer) {
        self.modelContainer = modelContainer
    }

    func performBackgroundTask<T>(_ work: @Sendable (ModelContext) throws -> T) async throws -> T {
        let context = ModelContext(modelContainer)
        return try work(context)
    }

    func syncUsers(_ users: [UserDTO]) async throws {
        try await performBackgroundTask { context in
            for dto in users {
                let entity = dto.toEntity()
                context.insert(entity)
            }
            try context.save()
        }
    }
}
```

### Problem 4: Memory Leaks in Closures

**Problem**: Strong reference cycles in async closures

**Solution**: Use weak/unowned references or Task-based approach

```swift
// Problem - potential retain cycle
class DataManager {
    var data: [String] = []

    func loadData() {
        APIClient.shared.fetch { result in
            self.data = result // Strong reference to self
        }
    }
}

// Solution 1 - weak self
class DataManager {
    var data: [String] = []

    func loadData() {
        APIClient.shared.fetch { [weak self] result in
            self?.data = result
        }
    }
}

// Solution 2 - async/await (preferred)
class DataManager {
    var data: [String] = []

    func loadData() async {
        data = await APIClient.shared.fetch()
    }
}

// Solution 3 - Task with actor isolation
@MainActor
class DataManager {
    var data: [String] = []

    func loadData() {
        Task { @MainActor in
            data = await APIClient.shared.fetch()
        }
    }
}
```

---

## Code Refactoring Examples

### Refactoring 1: Callback to async/await

**Before**:

```swift
class UserService {
    func getUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
        URLSession.shared.dataTask(with: makeRequest(id)) { data, response, error in
            if let error {
                completion(.failure(error))
                return
            }

            guard let data else {
                completion(.failure(NetworkError.noData))
                return
            }

            do {
                let user = try JSONDecoder().decode(User.self, from: data)
                completion(.success(user))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

// Usage
userService.getUser(id: "123") { result in
    DispatchQueue.main.async {
        switch result {
        case .success(let user):
            self.user = user
        case .failure(let error):
            self.error = error
        }
    }
}
```

**After**:

```swift
actor UserService {
    func getUser(id: String) async throws -> User {
        let (data, _) = try await URLSession.shared.data(for: makeRequest(id))
        return try JSONDecoder().decode(User.self, from: data)
    }
}

// Usage
Task {
    do {
        user = try await userService.getUser(id: "123")
    } catch {
        self.error = error
    }
}
```

### Refactoring 2: Combine to async/await

**Before**:

```swift
import Combine

class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false

    private var cancellables = Set<AnyCancellable>()
    private let userService: UserService

    func loadUsers() {
        isLoading = true

        userService.getUsersPublisher()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        // Handle error
                    }
                },
                receiveValue: { [weak self] users in
                    self?.users = users
                }
            )
            .store(in: &cancellables)
    }
}
```

**After**:

```swift
import Observation

@Observable
@MainActor
final class UserViewModel {
    var users: [User] = []
    var isLoading = false

    private let userService: UserServiceProtocol

    func loadUsers() {
        isLoading = true

        Task {
            defer { isLoading = false }

            do {
                users = try await userService.getUsers()
            } catch {
                // Handle error
            }
        }
    }
}
```

---

## Testing Examples

### Complete ViewModel Test

```swift
import Testing
@testable import MyApp

@Suite("LoginViewModel Tests")
struct LoginViewModelTests {

    @Test("Initial state is correct")
    func initialState() {
        let viewModel = LoginViewModel(authService: MockAuthService())

        #expect(viewModel.output.email.isEmpty)
        #expect(viewModel.output.password.isEmpty)
        #expect(!viewModel.output.isLoading)
        #expect(viewModel.output.emailError == nil)
        #expect(viewModel.output.passwordError == nil)
    }

    @Test("Email validation shows error for invalid email")
    func emailValidation() async {
        let viewModel = LoginViewModel(authService: MockAuthService())

        await viewModel.onInput(.updateEmail("invalid"))

        #expect(viewModel.output.emailError == "Invalid email format")
    }

    @Test("Password validation shows error for short password")
    func passwordValidation() async {
        let viewModel = LoginViewModel(authService: MockAuthService())

        await viewModel.onInput(.updatePassword("123"))

        #expect(viewModel.output.passwordError == "Password must be at least 6 characters")
    }

    @Test("Successful login navigates to home")
    func successfulLogin() async throws {
        let mockService = MockAuthService(shouldSucceed: true)
        let viewModel = LoginViewModel(authService: mockService)

        await viewModel.onInput(.updateEmail("test@example.com"))
        await viewModel.onInput(.updatePassword("password123"))
        await viewModel.onInput(.submit)

        // Wait for async operation
        try await Task.sleep(for: .milliseconds(100))

        #expect(viewModel.effect == .navigateToHome)
    }

    @Test("Failed login shows error")
    func failedLogin() async throws {
        let mockService = MockAuthService(shouldSucceed: false)
        let viewModel = LoginViewModel(authService: mockService)

        await viewModel.onInput(.updateEmail("test@example.com"))
        await viewModel.onInput(.updatePassword("password123"))
        await viewModel.onInput(.submit)

        try await Task.sleep(for: .milliseconds(100))

        #expect(!viewModel.output.isLoading)
        if case .showError = viewModel.effect {
            // Success
        } else {
            Issue.record("Expected showError effect")
        }
    }
}

// Mock Service
actor MockAuthService: AuthService {
    let shouldSucceed: Bool

    init(shouldSucceed: Bool = true) {
        self.shouldSucceed = shouldSucceed
    }

    func login(email: String, password: String) async throws -> User {
        if shouldSucceed {
            return User.sample
        } else {
            throw AuthError.invalidCredentials
        }
    }
}

extension User {
    static let sample = User(
        id: "1",
        name: "Test User",
        email: "test@example.com",
        avatarURL: nil,
        createdAt: Date(),
        updatedAt: Date()
    )
}
```
