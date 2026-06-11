---
name: arcana-ios-developer-skill
description: iOS development guide based on Arcana iOS enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design, SwiftUI, SwiftData, and MVVM Input/Output/Effect pattern. Suitable for iOS project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# iOS Developer Skill

Professional iOS development skill based on [Arcana iOS](https://github.com/jrjohn/arcana-ios) enterprise architecture.

---

## ⚡ Workflow — Always Start From the Reference Project

**Every task starts by cloning the complete reference project — NEVER scaffold a new Xcode project from scratch:**

```bash
git clone https://github.com/jrjohn/arcana-ios.git [new-project-directory]
```

1. **Clone** the reference project (command above).
2. **Build + test the UNTOUCHED clone first** to establish a green baseline (`xcodebuild build` then `xcodebuild test`) before changing anything.
3. **Follow [0. Project Setup](#0-project-setup---critical)** to rename the project and strip the demo screens — while KEEPING the infrastructure: auth/security layers (`Infrastructure/Security`, Keychain), caching (`Core/Cache`), offline/sync (SwiftData + SyncManager), the DI container (`Infrastructure/DI`), and deployment/build configs (Package.swift, project settings).
4. **Add features** one at a time following the [File-by-File Feature Recipe](#file-by-file-feature-recipe).

### Supporting files — load on demand

| File | When to read |
|------|--------------|
| `reference.md` | Deep-dive architecture reference — layer responsibilities and project conventions |
| `patterns.md` | Extended code patterns beyond those inlined in this file |
| `patterns/mvvm-input-output.md` | Detailed MVVM Input/Output/Effect ViewModel walkthrough |
| `examples.md` | Complete end-to-end feature examples to copy from |
| `checklists/production-ready.md` | Pre-release checklist before declaring a feature done |
| `verification/commands.md` | Full verification command set (superset of Quick Verification below) |

---

## File-by-File Feature Recipe

Ordered file-by-file recipe for adding a complete feature (example: **Orders**) through all layers. Create files in this order — each step compiles against the previous ones.

1. **Domain model** → `Domain/Models/Order.swift`
   — Immutable struct, `Identifiable`, all fields from Spec.
2. **Service protocol + implementation** → `Domain/Services/OrderService.swift`
   — `OrderServiceProtocol` + `OrderService`; business rules and input validation (see Form Validation pattern).
3. **Repository protocol** → `Domain/Repositories/OrderRepository.swift`
   — Protocol only; `async throws` methods returning Domain models.
4. **SwiftData entity** → `Data/Local/Entities/OrderEntity.swift`
   — `@Model` class with `toDomain()` / `toEntity()` mapping and `syncStatus` field.
5. **DTO** → `Data/Remote/DTOs/OrderDTO.swift`
   — `Codable` + `toDomain()` mapping; API endpoint in `Data/Remote/APIs/`.
6. **Repository implementation** → `Data/Repositories/OrderRepositoryImpl.swift`
   — Offline-first: SwiftData as single source of truth, schedule background sync.
7. **Mock repository** → `Data/Repositories/Mock/MockOrderRepository.swift`
   — NEVER return `[]`/nil; 5-10 varied items, `Task.sleep()` latency, IDs consistent with other repositories.
8. **DI registration** → `Infrastructure/DI/RepositoryContainer.swift`
   — `makeOrderRepository()` with `#if DEBUG` mock/real switch.
9. **ViewModel** → `Presentation/ViewModels/OrderListViewModel.swift`
   — `@Observable`, Input/Output/Effect pattern.
10. **Views** → `Presentation/Views/OrderListView.swift` (+ `OrderDetailView.swift`)
    — Loading/Error/Empty/Content states; stateless `Content` subview for testability.
11. **Route** → `Route.swift` — add `case orderList`, `case orderDetail(id: String)`.
12. **Navigation destination** → `NavigationRouter.swift` — switch cases for both routes; wire ALL `onNavigate*` callbacks.
13. **Unit tests** → `Tests/ViewModels/OrderListViewModelTests.swift`, `Tests/Repositories/OrderRepositoryTests.swift`.
14. **UI tests** → `UITests/OrderUITests.swift`.

Then run the Quick Verification Commands — route count must match destination count, and no empty mock arrays may remain.

---

## Quick Reference Card

### New Screen Checklist:
```
1. Add route → Route.swift (enum case)
2. Add destination → NavigationRouter.swift (switch case)
3. Create ViewModel (Input/Output/Effect pattern)
4. Create View with Loading/Error/Empty states
5. Wire navigation callbacks in parent
6. Verify mock data returns non-empty values
```

### New Repository Checklist:
```
1. Protocol → Domain/Repositories/XxxRepository.swift
2. Implementation → Data/Repositories/XxxRepositoryImpl.swift
3. Mock → Data/Repositories/Mock/MockXxxRepository.swift
4. DI binding → Infrastructure/DI/RepositoryContainer.swift
5. Mock data (NEVER return [] or nil!)
6. Verify ID consistency across repositories
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "\\[\\]\|Array()" Sources/**/Repositories/*Impl.swift` |
| Navigation crash | Compare `Route.swift` cases vs `NavigationRouter.swift` destinations |
| Button does nothing | `grep "action:\s*{\s*}" Sources/**/Views/` |
| Data not loading | `grep "fatalError\|TODO" Sources/**/Repositories/` |

---

## Rules Priority

### 🔴 CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Null Policy | Repository stubs NEVER return nil/empty | `grep "\\[\\]\|return nil" *Impl.swift` |
| Navigation Wiring | ALL Route cases MUST have destinations | Count routes vs destinations |
| ID Consistency | Cross-repository IDs must match | Check mock data IDs |
| Onboarding Flow | Register/Login must check onboarding status | Check navigation flow |

### 🟡 IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| UI States | Loading/Error/Empty for all screens | `grep -L "isLoading\|ProgressView"` |
| Mock Data Quality | Realistic, varied values (not all same) | Review mock data arrays |
| Error Messages | User-friendly, not technical errors | Check error handling |
| Input Validation | All forms validate before submit | Check form logic |

### 🟢 RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Animations | Smooth transitions between views |
| Accessibility | VoiceOver labels for all interactive elements |
| Dark Mode | Proper color adaptation |
| iPad Support | Responsive layouts for larger screens |

---

## Error Handling Pattern

### AppError - Unified Error Model

```swift
// Domain/Models/AppError.swift
enum AppError: LocalizedError {
    // Network errors
    case networkUnavailable
    case timeout
    case serverError(statusCode: Int)

    // Auth errors
    case unauthorized
    case tokenExpired
    case invalidCredentials

    // Data errors
    case notFound
    case validationFailed(message: String)
    case dataCorrupted

    // General errors
    case unknown(underlying: Error)

    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "No internet connection. Please check your network."
        case .timeout:
            return "Request timed out. Please try again."
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        case .unauthorized, .tokenExpired:
            return "Session expired. Please login again."
        case .invalidCredentials:
            return "Invalid email or password."
        case .notFound:
            return "The requested item was not found."
        case .validationFailed(let message):
            return message
        case .dataCorrupted:
            return "Data error. Please contact support."
        case .unknown:
            return "An unexpected error occurred."
        }
    }

    var requiresReauth: Bool {
        switch self {
        case .unauthorized, .tokenExpired:
            return true
        default:
            return false
        }
    }
}
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Error Flow                                │
├─────────────────────────────────────────────────────────────────┤
│  Repository Layer:                                               │
│    - Catch network/API errors                                    │
│    - Map to AppError                                             │
│    - Throw AppError                                              │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer:                                                  │
│    - Catch repository errors                                     │
│    - Add business context if needed                              │
│    - Re-throw as AppError                                        │
├─────────────────────────────────────────────────────────────────┤
│  ViewModel Layer:                                                │
│    - Catch all errors                                            │
│    - Update output.error = error.localizedDescription            │
│    - Check requiresReauth for auth redirect                      │
├─────────────────────────────────────────────────────────────────┤
│  View Layer:                                                     │
│    - Display error from output.error                             │
│    - Show retry button                                           │
│    - Handle auth redirect via effect                             │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling by Layer

**Repository Layer:**
```swift
func getItems() async throws -> [Item] {
    do {
        let response = try await apiClient.get("/items")
        return response.map { $0.toDomain() }
    } catch let error as URLError {
        switch error.code {
        case .notConnectedToInternet:
            throw AppError.networkUnavailable
        case .timedOut:
            throw AppError.timeout
        default:
            throw AppError.unknown(underlying: error)
        }
    } catch {
        throw AppError.unknown(underlying: error)
    }
}
```

**ViewModel Layer:**
```swift
private func loadData() {
    Task { @MainActor in
        output.isLoading = true
        output.error = nil

        do {
            let items = try await repository.getItems()
            output.items = items
        } catch let appError as AppError {
            output.error = appError.localizedDescription
            if appError.requiresReauth {
                effect = .navigateToLogin
            }
        } catch {
            output.error = AppError.unknown(underlying: error).localizedDescription
        }

        output.isLoading = false
    }
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| ViewModel | 90%+ | All Input handlers, state transitions, effects |
| Service | 85%+ | Business logic, edge cases |
| Repository | 80%+ | Data mapping, error handling |
| View | 60%+ | Snapshot tests, interaction tests |

### What to Test

**ViewModel Tests (Highest Priority):**
```swift
final class FeatureViewModelTests: XCTestCase {
    // Test each Input case
    func testLoad_Success_UpdatesItems() async { }
    func testLoad_Failure_SetsError() async { }
    func testRefresh_Success_ShowsToast() async { }
    func testItemTapped_NavigatesToDetail() { }

    // Test state transitions
    func testLoad_SetsLoadingTrue_ThenFalse() async { }

    // Test edge cases
    func testLoad_EmptyResult_ShowsEmptyState() async { }
}
```

**Service Tests:**
```swift
final class UserServiceTests: XCTestCase {
    // Test business rules
    func testValidateEmail_InvalidFormat_ReturnsFalse() { }
    func testCalculateScore_WithData_ReturnsCorrectValue() { }
}
```

**Repository Tests:**
```swift
final class UserRepositoryTests: XCTestCase {
    // Test data mapping
    func testGetUsers_MapsCorrectly() async { }

    // Test offline behavior
    func testGetUsers_NoNetwork_ReturnsCached() async { }
}
```

### Test Command
```bash
# Replace <SIMULATOR> with any installed simulator — list them with: xcrun simctl list devices
xcodebuild test \
  -scheme [YourScheme] \
  -destination 'platform=iOS Simulator,name=<SIMULATOR>' \
  -enableCodeCoverage YES

# View coverage report
xcrun xccov view --report Build/Logs/Test/*.xcresult
```

---

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

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented repositories (MUST be empty)
grep -rn "fatalError\|TODO.*implement\|throw.*NotImplemented" Sources/

# 2. Check for empty button actions (MUST be empty)
grep -rn "action:\s*{\s*}\|Button.*{\s*}" Sources/

# 3. Check for missing navigation destinations (compare route count vs view count)
echo "Routes defined:" && grep -c "case\s" Sources/**/Route.swift 2>/dev/null || echo 0
echo "Views registered:" && grep -c "destination:" Sources/**/NavigationRouter.swift 2>/dev/null || echo 0

# 4. Verify build compiles (use any installed simulator for <SIMULATOR> — list with: xcrun simctl list devices)
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=<SIMULATOR>' build

# 5. 🚨 Check for unwired navigation closures (CRITICAL!)
grep -rn "onNavigate.*:\s*(\s*)\s*->\s*Void\s*=\s*{" Sources/**/Views/

# 6. 🚨 Verify ALL Route cases have NavigationRouter destinations
echo "=== Route Cases Defined ===" && \
grep -rh "case\s\+[a-zA-Z]" Sources/**/Route.swift | grep -oE "case\s+[a-zA-Z]+" | sort -u
echo "=== NavigationRouter Destinations ===" && \
grep -rh "case\s\.\|case\slet\s\." Sources/**/NavigationRouter.swift | grep -oE "\.[a-zA-Z]+" | sort -u

# 7. 🚨 Check for navigation callbacks in Views not wired in parent/caller
echo "=== View Navigation Callbacks ===" && \
grep -rh "var onNavigate\|let onNavigate" Sources/**/Views/*.swift | grep -oE "onNavigate[A-Za-z]+" | sort -u

# 8. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "repository\.[a-zA-Z]*(" Sources/**/Services/*.swift | sort -u
echo "=== Repository Protocol Methods ===" && \
grep -rh "func [a-zA-Z]*(" Sources/**/Repositories/*Repository.swift | grep -oE "func [a-zA-Z]+\(" | sort -u

# 9. 🚨 Verify ALL Repository protocol methods have implementations
echo "=== Repository Protocol Methods ===" && \
grep -rh "func " Sources/**/Domain/Repositories/*Repository.swift | grep -oE "func [a-zA-Z]+" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "func " Sources/**/Data/Repositories/*RepositoryImpl.swift | grep -oE "func [a-zA-Z]+" | sort -u
```

⚠️ **CRITICAL**: Route count MUST equal View count. If not, you have missing navigation destinations that will cause runtime crashes.

⚠️ **NAVIGATION WIRING CRITICAL**: Commands #5-#7 detect navigation callbacks that exist in Views but aren't connected. A View can declare `var onNavigateToSettings: () -> Void = {}` with a default empty closure, but if the parent View doesn't pass a real implementation, the button does nothing!

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty arrays for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank Canvas/Chart views)
- Line charts that skip rendering (e.g., `guard points.count >= 2 else { return }`)
- Empty state views even when data structure exists

### Mock Data Rules

**Rule 1: Array data for charts MUST have at least 7 items**
```swift
// ❌ BAD - Chart will be blank
func getCurrentWeekSummary() async throws -> WeeklySummary {
    return WeeklySummary(
        dailyReports: []  // ← Chart has no data to render!
    )
}

// ✅ GOOD - Chart has data to display
func getCurrentWeekSummary() async throws -> WeeklySummary {
    let mockDailyReports = (0..<7).map { dayOffset in
        createMockDailyReport(
            score: [72, 78, 85, 80, 76, 88, 82][dayOffset],
            duration: [390, 420, 450, 410, 380, 460, 435][dayOffset]
        )
    }
    return WeeklySummary(dailyReports: mockDailyReports)
}
```

**Rule 2: Use realistic, varied sample values**
```swift
// ❌ BAD - Monotonous test data
let scores = Array(repeating: 80, count: 7)

// ✅ GOOD - Realistic variation
let scores = [72, 78, 85, 80, 76, 88, 82]  // Shows trend
```

**Rule 3: Data must match model struct exactly**
```bash
# Before creating mock data, ALWAYS verify the struct definition:
grep -A 20 "struct TherapyData" Sources/**/Models/*.swift
```

**Rule 4: Create helper functions for complex mock data**
```swift
// ✅ Create reusable mock factory
private func createMockDailyReport(score: Int, duration: Int) -> DailySleepReport {
    DailySleepReport(
        id: UUID().uuidString,
        sleepScore: score,
        sleepDuration: SleepDuration(totalMinutes: duration, ...),
        // ... all required fields
    )
}
```

### Quick Verification Commands for Mock Data

```bash
# 10. 🚨 Check for empty array returns in Repository stubs (MUST FIX)
grep -rn "\[\]\|Array()" Sources/**/Repositories/*RepositoryImpl.swift

# 11. 🚨 Verify chart-related data has mock values
grep -rn "dailyReports\|weeklyData\|chartData" Sources/**/Repositories/ | grep -E "= \[\]|\.init\(\)"
```

---

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
# <SIMULATOR> = any installed simulator; list with: xcrun simctl list devices
xcodebuild -scheme [YourScheme] -destination 'platform=iOS Simulator,name=<SIMULATOR>' build
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

🚨 **ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests  ⚠️ MANDATORY │
│  Step 5: Mock APIs → Use mock data for unfinished Cloud APIs    │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
│  Step 7: Verify 100% → Tests written = Features implemented     │
└─────────────────────────────────────────────────────────────────┘
```

#### ⛔ FORBIDDEN: Tests Without Implementation

```swift
// ❌ WRONG - Test exists but no implementation
// Test file exists: LoginViewModelTests.swift (32 tests)
// Production file: LoginViewModel.swift → MISSING or uses fatalError()
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: LoginViewModelTests.swift (32 tests)
// Production file: LoginViewModel.swift (fully implemented)
// All 32 tests PASS
```

#### ⛔ Placeholder View Policy

Placeholder views are **ONLY** allowed as a temporary navigation target during active development. They are **FORBIDDEN** as a final state.

```swift
// ❌ WRONG - Placeholder view left in production
case .training:
    PlaceholderView(title: "Training Courses") // FORBIDDEN!

// ✅ CORRECT - Real view implementation
case .training:
    TrainingView(viewModel: TrainingViewModel())
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderView\|fatalError\|TODO.*implement\|Coming Soon" Sources/
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

#### Step 4: Mock API Implementation - MANDATORY

⚠️ **CRITICAL**: Every Repository method MUST return valid mock data. NEVER leave methods with `fatalError()` or `throw NotImplementedError`.

**Rules for Mock Repositories:**
1. ALL repository methods must return valid mock data
2. Use `Task.sleep()` to simulate network latency (0.5-1 second)
3. Mock data must match the domain model structure exactly
4. Check enum cases exist before using them
5. Include all required properties for structs/classes

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
# <SIMULATOR> = any installed simulator; list with: xcrun simctl list devices

# Run all tests via command line
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=<SIMULATOR>'

# Run tests with coverage
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=<SIMULATOR>' -enableCodeCoverage YES

# Run specific test class
xcodebuild test -scheme [YourScheme] -destination 'platform=iOS Simulator,name=<SIMULATOR>' -only-testing:YourAppTests/LoginViewModelTests
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

### 3. ViewModel Input/Output/Effect Pattern

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

### 4. Offline-First Strategy

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

### 5. Three-Layer Cache Strategy

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

### 6. SwiftUI Best Practices

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

### 7. Dependency Injection (swift-dependencies)

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

### 8. Form Validation

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

### 9. Pagination and Lazy Loading

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

## Navigation Wiring Verification Guide

### 🚨 The Navigation Wiring Blind Spot

SwiftUI Views often declare navigation callbacks with default empty closures:

```swift
// SettingsView.swift
struct SettingsView: View {
    var onNavigateToAccountInfo: () -> Void = {}  // ⚠️ Default empty!
    var onNavigateToChangePassword: () -> Void = {}  // ⚠️ Default empty!
    var onNavigateToUserList: () -> Void = {}  // ⚠️ Default empty!

    var body: some View {
        List {
            Button("Account Info") { onNavigateToAccountInfo() }  // Does nothing if not wired!
            Button("Change Password") { onNavigateToChangePassword() }  // Does nothing if not wired!
        }
    }
}
```

**Problem**: If the parent View/NavigationRouter doesn't pass real implementations, buttons appear functional but do nothing when tapped!

### Detection Patterns

```bash
# Find Views with navigation callbacks
grep -rn "var onNavigate.*:\s*(\s*)\s*->\s*Void" Sources/**/Views/

# Find Route cases
grep -rn "case\s\+[a-zA-Z]" Sources/**/Route.swift

# Find NavigationRouter destinations
grep -rn "destination:" Sources/**/NavigationRouter.swift

# Compare: Every navigation callback in a View MUST have corresponding wiring
```

### Verification Checklist

1. **Count navigation callbacks in each View**:
   ```bash
   grep -c "onNavigateTo" Sources/Presentation/Views/SettingsView.swift
   ```

2. **Count wired callbacks where View is used**:
   ```bash
   grep -c "onNavigateTo.*:" Sources/Presentation/Navigation/NavigationRouter.swift | grep "SettingsView"
   ```

3. **Counts MUST match!** Any mismatch = unwired navigation

### Correct Wiring Example

```swift
// NavigationRouter.swift
@ViewBuilder
func destination(for route: Route) -> some View {
    switch route {
    case .settings:
        SettingsView(
            onNavigateToAccountInfo: { navigate(to: .accountInfo) },  // ✅ Wired
            onNavigateToChangePassword: { navigate(to: .changePassword) },  // ✅ Wired
            onNavigateToUserList: { navigate(to: .userList) }  // ✅ Wired
        )
    case .accountInfo:
        AccountInfoView()  // ✅ Route exists AND View exists
    case .changePassword:
        ChangePasswordView()  // ✅ Route exists AND View exists
    case .userList:
        UserListView()  // ✅ Route exists AND View exists
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
- [ ] 🚨 ALL navigation callbacks in Views are wired in NavigationRouter
- [ ] 🚨 ALL Route cases have corresponding View destinations
- [ ] 🚨 ALL Service→Repository method calls exist in Repository protocols
- [ ] 🚨 ALL Repository protocol methods have RepositoryImpl implementations

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

---

## Spec Gap Prediction System

When Spec is incomplete, use these universal rules to predict and supplement missing UI/UX elements.

### Screen Type → Required States (Universal)

| Screen Type | Required States | Auto-Predict |
|-------------|-----------------|--------------|
| List Screen | Loading, Error, Empty, Content | Pull-to-refresh, Pagination |
| Detail Screen | Loading, Error, Content | Back navigation, Share action |
| Form Screen | Validation, Submit Loading, Success, Error | Input validation, Cancel action |
| Dashboard | Loading, Error, Content | Refresh, Section navigation |
| Settings | Content | Back navigation, Section headers |
| Auth Screen | Loading, Error, Success | Forgot password link, Terms link |

### Flow Completion Prediction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flow Completion Rules                         │
├─────────────────────────────────────────────────────────────────┤
│  IF Spec has Login:                                              │
│    → PREDICT: Register, Forgot Password, Logout                  │
│                                                                  │
│  IF Spec has Register:                                           │
│    → PREDICT: Onboarding flow after registration                 │
│    → PREDICT: Email verification (if email-based)                │
│                                                                  │
│  IF Spec has List:                                               │
│    → PREDICT: Detail view for list items                         │
│    → PREDICT: Search/Filter functionality                        │
│    → PREDICT: Empty state when no items                          │
│                                                                  │
│  IF Spec has Settings:                                           │
│    → PREDICT: Account info edit                                  │
│    → PREDICT: Change password                                    │
│    → PREDICT: Notification preferences                           │
│    → PREDICT: Logout confirmation                                │
│                                                                  │
│  IF Spec has any data display:                                   │
│    → PREDICT: Offline cached view                                │
│    → PREDICT: Sync status indicator                              │
└─────────────────────────────────────────────────────────────────┘
```

### Data Operation Prediction (CRUD)

| Spec Mentions | Auto-Predict Operations |
|---------------|-------------------------|
| "Display items" | Read + Loading + Error + Empty states |
| "Add item" | Create + Validation + Success feedback |
| "Edit item" | Update + Validation + Optimistic UI |
| "Delete item" | Delete + Confirmation dialog + Undo option |
| "Search" | Debounced input + No results state |
| "Filter" | Filter UI + Clear filter + Active filter indicator |

### Navigation Completeness Prediction

```swift
// If Route has these cases:
enum Route {
    case login        // → Predict: register, forgotPassword
    case dashboard    // → Predict: settings, profile
    case itemList     // → Predict: itemDetail(id)
    case settings     // → Predict: accountInfo, changePassword, about
}

// Auto-check: Every navigation callback in Views must be wired
```

### UI State Prediction Matrix

| Data Source | Success | Empty | Error | Loading |
|-------------|---------|-------|-------|---------|
| API Call | Content view | Empty view + CTA | Error view + Retry | ProgressView |
| Local DB | Content view | Empty view + CTA | Error view + Retry | ProgressView |
| User Input | Show result | Prompt input | Validation error | Submit loading |

### Spec Gap Detection Commands

```bash
# 1. Detect screens missing loading state
grep -L "isLoading\|ProgressView" Sources/**/Views/*Screen.swift

# 2. Detect screens missing error state
grep -L "error\|Error" Sources/**/Views/*Screen.swift

# 3. Detect lists missing empty state
grep -l "ForEach\|List" Sources/**/Views/*.swift | \
xargs grep -L "isEmpty\|empty\|Empty"

# 4. Detect forms missing validation
grep -l "TextField\|SecureField" Sources/**/Views/*.swift | \
xargs grep -L "isValid\|validate\|error"

# 5. Detect missing navigation flows
echo "=== Auth Flow Check ===" && \
grep -q "login\|Login" Sources/**/Route.swift && \
(grep -q "register\|Register" Sources/**/Route.swift || echo "⚠️ Missing: Register screen") && \
(grep -q "forgotPassword\|ForgotPassword" Sources/**/Route.swift || echo "⚠️ Missing: Forgot Password screen")

# 6. Detect missing CRUD operations
echo "=== CRUD Completeness ===" && \
grep -rh "func get\|func fetch\|func load" Sources/**/Repositories/*.swift | head -5 && \
grep -rh "func create\|func add\|func save" Sources/**/Repositories/*.swift | head -5 && \
grep -rh "func update\|func edit" Sources/**/Repositories/*.swift | head -5 && \
grep -rh "func delete\|func remove" Sources/**/Repositories/*.swift | head -5
```

### Prediction Implementation Example

When implementing a List screen from Spec:

```swift
// Spec says: "Display user's items"
// Auto-predict required implementation:

struct ItemListScreen: View {
    @State private var viewModel: ItemListViewModel

    var body: some View {
        Group {
            // 1. LOADING - Always needed for API/DB calls
            if viewModel.output.isLoading {
                ProgressView()
            }
            // 2. ERROR - Always needed for API/DB calls
            else if let error = viewModel.output.error {
                ErrorView(
                    message: error,
                    onRetry: { viewModel.onInput(.retry) }
                )
            }
            // 3. EMPTY - Always needed for list screens
            else if viewModel.output.items.isEmpty {
                EmptyStateView(
                    title: "No Items",
                    message: "Add your first item to get started",
                    action: ("Add Item", { viewModel.onInput(.addTapped) })
                )
            }
            // 4. CONTENT - The actual list
            else {
                List(viewModel.output.items) { item in
                    ItemRow(item: item)
                        .onTapGesture {
                            viewModel.onInput(.itemTapped(id: item.id))
                        }
                }
                .refreshable {
                    viewModel.onInput(.refresh)
                }
            }
        }
    }
}
```

---

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Swift | 6.0+ |
| SwiftUI | iOS 17+ |
| SwiftData | iOS 17+ |
| Alamofire | 5.9+ |
| swift-dependencies | 1.0+ |
