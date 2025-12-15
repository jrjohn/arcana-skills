---
name: windows-developer-skill
description: Windows desktop development guide based on Arcana Windows enterprise architecture. Provides comprehensive support for Clean Architecture, WinUI 3, MVVM UDF pattern, Plugin System with 18 plugin types, CRDT-based offline sync, and enterprise security. Suitable for Windows desktop project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Windows Developer Skill

Professional Windows desktop development skill based on [Arcana Windows](https://github.com/jrjohn/arcana-windows) enterprise architecture.

---

## Quick Reference Card

### New View Checklist:
```
1. Add Page.xaml to Presentation/Views/
2. Create ViewModel with Input/Output/Effect pattern
3. Add navigation method to INavGraph interface
4. Implement navigation in NavGraph
5. Subscribe to ViewModel.Fx in code-behind
6. Verify mock data returns non-empty values
```

### New Repository Checklist:
```
1. Interface → Domain/Repositories/IXxxRepository.cs
2. Implementation → Data/Repositories/XxxRepository.cs
3. DI registration → Infrastructure/DependencyInjection.cs
4. Mock data (NEVER return empty collections!)
5. Verify ID consistency across repositories
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "new List<>\\|Empty\\|Array.Empty" src/**/Repositories/*.cs` |
| Navigation crash | Compare INavGraph methods vs NavGraph implementations |
| Button does nothing | Check Fx.Subscribe in View code-behind |

---

## Rules Priority

### 🔴 CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty collections | `grep "Empty\\|new List<>()" *.cs` |
| Navigation Wiring | ALL INavGraph methods MUST be in NavGraph | Compare interface vs impl |
| Effect Handling | ALL ViewModel Effects MUST be subscribed | Check Fx.Subscribe |
| ID Consistency | Cross-repository IDs must match | Check mock data IDs |

### 🟡 IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| UI States | Loading/Error/Empty for all views | Check ViewModel Output |
| Mock Data Quality | Realistic, varied values | Review mock data |
| Error Messages | User-friendly messages | Check AppError handling |
| Nullable | Proper null handling | Check ? annotations |

### 🟢 RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Animations | Smooth view transitions |
| Accessibility | AutomationProperties.Name |
| Dark Mode | Theme support |
| Telemetry | Analytics tracking |

---

## Error Handling Pattern

### AppException - Unified Error Model

```csharp
public class AppException : Exception
{
    public ErrorCode Code { get; }
    public Dictionary<string, object>? Details { get; }

    public enum ErrorCode
    {
        // Network errors
        NetworkUnavailable,
        Timeout,
        ServiceUnavailable,

        // Auth errors
        Unauthorized,
        TokenExpired,

        // Data errors
        NotFound,
        ValidationFailed,
        Conflict,

        // General
        InternalError
    }

    public static AppException NotFound(string message)
        => new(ErrorCode.NotFound, message);

    public static AppException Validation(string message, Dictionary<string, object> details)
        => new(ErrorCode.ValidationFailed, message) { Details = details };
}
```

### Error Handling in ViewModel

```csharp
private async Task LoadDataAsync()
{
    IsLoading = true;
    Error = null;

    try
    {
        Items = await _repository.GetAllAsync();
    }
    catch (AppException ex)
    {
        Error = ex.Message;
        if (ex.Code == ErrorCode.Unauthorized)
            Fx.OnNext(new Effect.NavigateToLogin());
    }
    finally
    {
        IsLoading = false;
    }
}
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| ViewModel | 90%+ | All intents, state transitions, effects |
| Service | 85%+ | Business logic, edge cases |
| Repository | 80%+ | Data mapping, error handling |

### Test Commands
```bash
# Run with coverage
dotnet test --collect:"XPlat Code Coverage"

# Generate report
reportgenerator -reports:coverage.xml -targetdir:coverage
```

---

## Spec Gap Prediction System

When implementing UI from incomplete specifications, PROACTIVELY predict missing screens and states:

### Screen Prediction Matrix

When a spec mentions a feature, predict ALL related screens:

| Feature | Predicted Screens | Check |
|---------|-------------------|-------|
| User Management | UserListPage | ✅ |
| User Management | UserDetailPage | ✅ |
| User Management | UserEditPage | ✅ |
| User Management | UserCreatePage | ✅ |
| User Management | UserDeleteConfirmDialog | ✅ |

### UI State Prediction

For every screen, predict required UI states:

```csharp
// Predicted states for UserListPage:
// ✅ Loading - Show ProgressRing while fetching
// ✅ Empty - Show "No users found" message
// ✅ Error - Show error message with retry button
// ✅ Success - Show user list
// ✅ Refreshing - Show pull-to-refresh indicator
```

### Navigation Prediction

When adding a new feature, predict navigation flow:

```csharp
// User Management Navigation:
// Home → UserList → UserDetail → UserEdit
//                 ↘ UserCreate
//                 ↘ DeleteConfirmDialog
```

### Dialog Prediction

CRUD operations need confirmation dialogs:

```csharp
// Predicted dialogs:
// ✅ DeleteConfirmDialog - "Are you sure you want to delete?"
// ✅ UnsavedChangesDialog - "You have unsaved changes"
// ✅ ErrorDialog - Show error details
// ✅ SuccessDialog - "Operation completed"
```

### Ask Clarification Prompt

When specs are incomplete, ASK before implementing:

```
The specification mentions "User Management" but doesn't specify:
1. Should the list support multi-select?
2. What fields are shown in the list vs detail view?
3. Are there bulk operations (delete multiple)?
4. What sorting/filtering options are needed?

Please clarify before I proceed with implementation.
```

---

## Core Architecture Principles

### Clean Architecture - Five Layers

```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                   │
│          WinUI 3 + MVVM UDF + Navigation            │
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│           DI + Security + Settings                  │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│          Business Entities + Services               │
├─────────────────────────────────────────────────────┤
│                    Data Layer                        │
│         Repository + Unit of Work + EF Core         │
├─────────────────────────────────────────────────────┤
│                    Sync Layer                        │
│            CRDT Engine + Vector Clocks              │
└─────────────────────────────────────────────────────┘
```

### Architecture Ratings
| Category | Score |
|----------|-------|
| Clean Architecture | 9.0/10 |
| Plugin System | 9.5/10 |
| MVVM Pattern | 9.5/10 |
| Security | 9.0/10 |
| **Overall** | **9.0/10** |

## Instructions

When handling Windows desktop development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented methods (MUST be empty)
grep -rn "throw.*NotImplementedException\|TODO.*implement" src/

# 2. Check for empty button click handlers (MUST be empty)
grep -rn "Click=\"\"\|Command=\"{x:Null}\"" src/

# 3. Check all navigation methods have corresponding pages
echo "NavGraph methods:" && grep -c "public void To\|public void Navigate" src/**/Navigation/NavGraph.cs 2>/dev/null || echo 0
echo "Pages registered:" && grep -c "typeof(.*Page)" src/**/Navigation/NavGraph.cs 2>/dev/null || echo 0

# 4. Verify all Views have ViewModels
echo "Views:" && find src -name "*View.xaml" 2>/dev/null | wc -l
echo "ViewModels:" && find src -name "*ViewModel.cs" 2>/dev/null | wc -l

# 5. Verify build compiles
dotnet build

# 6. Run tests
dotnet test

# 7. 🚨 Check INavGraph interface methods have NavGraph implementations (CRITICAL!)
echo "=== INavGraph Interface Methods ===" && \
grep -rh "void To[A-Z]\|Task To[A-Z]" src/**/INavGraph.cs | grep -oE "To[A-Za-z]+" | sort -u
echo "=== NavGraph Implemented Methods ===" && \
grep -rh "public void To[A-Z]\|public async Task To[A-Z]" src/**/NavGraph.cs | grep -oE "To[A-Za-z]+" | sort -u

# 8. 🚨 Check ViewModel Effects are handled in Views
echo "=== ViewModel Effect Types ===" && \
grep -rh "record Navigate\|record Show\|record Open" src/**/ViewModels/*.cs | grep -oE "record [A-Za-z]+" | sort -u
echo "=== Effect Subscriptions in Views ===" && \
grep -rn "Fx.Subscribe\|_viewModel.Fx" src/**/Views/*.cs

# 9. 🚨 Check for navigation callbacks in Views not wired to NavGraph
grep -rn "OnNavigate\|NavigateTo" src/**/Views/*.xaml.cs | grep -v "INavGraph\|_navGraph"

# 10. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "_repository\.[A-Za-z]*(\|_unitOfWork\.[A-Za-z]*\.[A-Za-z]*(" src/**/Services/*.cs | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "Task<\|[A-Z][a-zA-Z]* [A-Z]" src/**/IRepository.cs | grep -oE "[A-Z][a-zA-Z]+Async\(" | sort -u

# 11. 🚨 Verify ALL IRepository interface methods have implementations
echo "=== IRepository Interface Methods ===" && \
grep -rh "Task<\|void " src/**/Repositories/IRepository.cs | grep -oE "[A-Z][a-zA-Z]+\(" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "public.*async\|public.*override" src/**/Repositories/Repository.cs | grep -oE "[A-Z][a-zA-Z]+\(" | sort -u
```

⚠️ **CRITICAL**: All NavGraph navigation methods MUST have corresponding Page types registered. Missing pages cause runtime crashes.

⚠️ **NAVIGATION WIRING CRITICAL**: Commands #7-#9 detect INavGraph interface methods not implemented in NavGraph, ViewModel Effects not subscribed in Views, and navigation callbacks not wired. A ViewModel can emit `Fx.OnNext(new Effect.NavigateToSettings())` but if the View doesn't subscribe and call `_navGraph.ToSettings()`, nothing happens!

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty collections for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank WinUI charts)
- Line charts that skip rendering (e.g., `if (points.Count < 2) return;`)
- Empty state views even when data structure exists

### Mock Data Rules

**Rule 1: Collection data for charts MUST have at least 7 items**
```csharp
// ❌ BAD - Chart will be blank
public async Task<WeeklySummary> GetCurrentWeekSummaryAsync(string userId)
{
    return new WeeklySummary
    {
        DailyReports = new List<DailyReport>()  // ← Chart has no data to render!
    };
}

// ✅ GOOD - Chart has data to display
public async Task<WeeklySummary> GetCurrentWeekSummaryAsync(string userId)
{
    var scores = new[] { 72, 78, 85, 80, 76, 88, 82 };
    var durations = new[] { 390, 420, 450, 410, 380, 460, 435 };
    var mockDailyReports = Enumerable.Range(0, 7)
        .Select(i => CreateMockDailyReport(scores[i], durations[i]))
        .ToList();
    return new WeeklySummary { DailyReports = mockDailyReports };
}
```

**Rule 2: Use realistic, varied sample values**
```csharp
// ❌ BAD - Monotonous test data
var scores = Enumerable.Repeat(80, 7).ToArray();

// ✅ GOOD - Realistic variation
var scores = new[] { 72, 78, 85, 80, 76, 88, 82 };  // Shows trend
```

**Rule 3: Data must match entity/DTO class exactly**
```bash
# Before creating mock data, ALWAYS verify the class definition:
grep -A 20 "class TherapyData" src/**/Entities/*.cs
grep -A 20 "record TherapyData" src/**/DTOs/*.cs
```

**Rule 4: Create helper methods for complex mock data**
```csharp
// ✅ Create reusable mock factory
private DailyReport CreateMockDailyReport(int score, int duration)
{
    return new DailyReport
    {
        Id = Guid.NewGuid().ToString(),
        SleepScore = score,
        SleepDuration = new SleepDuration { TotalMinutes = duration, ... },
        // ... all required fields
    };
}
```

### Quick Verification Commands for Mock Data

```bash
# 12. 🚨 Check for empty collection returns in Repository stubs (MUST FIX)
grep -rn "new List<\|Enumerable.Empty<\|Array.Empty<" src/**/Repositories/*Repository.cs

# 13. 🚨 Verify chart-related data has mock values
grep -rn "DailyReports\|WeeklyData\|ChartData" src/**/Repositories/ | grep -E "new List<.*>\(\)|Empty<"
```

---

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested NuGet settings and library versions. **NEVER reconfigure project structure or modify .csproj / Directory.Build.props**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-windows.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-windows template"
```

**Step 3**: Modify project name and namespace
Only modify the following required items:
- `.sln` solution file name
- `<RootNamespace>` and `<AssemblyName>` in each `.csproj`
- Rename project directories under `src/`
- Update namespace declarations in code

**Step 4**: Clean up example code
The cloned project contains example UI (e.g., Arcana User Management). Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `src/Arcana.Infrastructure/` - DI, Security, Settings
- `src/Arcana.Domain/Services/` - Common Service base classes
- `src/Arcana.Data/DbContext/` - EF Core base configuration
- `src/Arcana.Data/Repositories/` - Repository base classes
- `src/Arcana.Plugins.Contracts/` - Plugin interface definitions
- `src/Arcana.Plugins/Runtime/` - Plugin runtime
- `src/Arcana.App/App.xaml` - App entry point
- `src/Arcana.App/Navigation/` - NavGraph configuration (modify routes)

**Example files to REPLACE**:
- `src/Arcana.App/Views/` - Delete all example screens, create new project Views
- `src/Arcana.App/ViewModels/` - Delete example ViewModel, create new ViewModel
- `src/Arcana.Domain/Entities/` - Delete example Entities, create new Domain Entities
- `src/Arcana.Data/Configurations/` - Modify EF Core configuration
- `plugins/` - Delete example Plugin, create new Plugin

**Step 5**: Verify build
```bash
dotnet restore
dotnet build
dotnet test
```

### ❌ Prohibited Actions
- **DO NOT** create new WinUI 3 project from scratch
- **DO NOT** modify NuGet package version numbers in `.csproj`
- **DO NOT** add or remove NuGet dependencies (unless explicitly required)
- **DO NOT** modify shared settings in `Directory.Build.props`
- **DO NOT** reconfigure WinUI 3, EF Core, CommunityToolkit, or other library settings

### ✅ Allowed Modifications
- Add business-related C# code (following existing architecture)
- Add Views, ViewModels
- Add Domain Entities, Repositories
- Modify XAML resource files
- Develop new Plugins (following 18 Plugin types)

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

⚠️ **CRITICAL**: All development MUST follow this TDD workflow. Every SRS/SDD requirement must have corresponding tests BEFORE implementation.

🚨 **ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Analyze Spec → Extract all SRS & SDD requirements      │
│  Step 2: Create Tests → Write tests for EACH Spec item          │
│  Step 3: Verify Coverage → Ensure 100% Spec coverage in tests   │
│  Step 4: Implement → Build features to pass tests  ⚠️ MANDATORY │
│  Step 5: Mock APIs → Use mock data for unfinished dependencies  │
│  Step 6: Run All Tests → ALL tests must pass before completion  │
│  Step 7: Verify 100% → Tests written = Features implemented     │
└─────────────────────────────────────────────────────────────────┘
```

#### ⛔ FORBIDDEN: Tests Without Implementation

```csharp
// ❌ WRONG - Test exists but no implementation
// Test file exists: LoginViewModelTests.cs (32 tests)
// Production file: LoginViewModel.cs → MISSING or throws NotImplementedException
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: LoginViewModelTests.cs (32 tests)
// Production file: LoginViewModel.cs (fully implemented)
// All 32 tests PASS
```

#### ⛔ Placeholder Page Policy

Placeholder pages are **ONLY** allowed as a temporary navigation target during active development. They are **FORBIDDEN** as a final state.

```csharp
// ❌ WRONG - Placeholder page left in production
case Route.Training:
    _frame.Navigate(typeof(PlaceholderPage), "Training Course"); // FORBIDDEN!
    break;

// ✅ CORRECT - Real page implementation
case Route.Training:
    _frame.Navigate(typeof(TrainingPage));
    break;
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderPage\|NotImplementedException\|TODO.*implement\|Coming Soon" src/
```

#### Step 1: Analyze Spec Documents (SRS & SDD)
Before writing any code, extract ALL requirements from both SRS and SDD:
```csharp
/**
 * Requirements extracted from specification documents:
 *
 * SRS (Software Requirements Specification):
 * - SRS-001: User must be able to login with email/password
 * - SRS-002: App must show splash screen on startup
 * - SRS-003: Dashboard must display user statistics
 *
 * SDD (Software Design Document):
 * - SDD-001: Use MVVM UDF pattern for ViewModels
 * - SDD-002: Implement CRDT-based offline sync
 * - SDD-003: Use PBKDF2-SHA256 for password hashing
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```csharp
// tests/Arcana.App.Tests/ViewModels/LoginViewModelTests.cs
using Xunit;
using Moq;
using FluentAssertions;

public class LoginViewModelTests
{
    private readonly Mock<IAuthService> _mockAuthService;
    private readonly LoginViewModel _viewModel;

    public LoginViewModelTests()
    {
        _mockAuthService = new Mock<IAuthService>();
        _viewModel = new LoginViewModel(_mockAuthService.Object);
    }

    // SRS-001: User must be able to login with email/password
    [Fact]
    public async Task Login_WithValidCredentials_ShouldSucceed()
    {
        // Given
        _mockAuthService
            .Setup(x => x.LoginAsync("test@test.com", "password123"))
            .ReturnsAsync(new AuthResult { Success = true });

        // When
        _viewModel.OnInput(new LoginViewModel.Input.UpdateEmail("test@test.com"));
        _viewModel.OnInput(new LoginViewModel.Input.UpdatePassword("password123"));
        await _viewModel.OnInput(new LoginViewModel.Input.Submit());

        // Then
        _viewModel.Out.IsLoginSuccess.Should().BeTrue();
        _viewModel.Out.Error.Should().BeNull();
    }

    // SRS-001: Invalid credentials should show error
    [Fact]
    public async Task Login_WithInvalidCredentials_ShouldShowError()
    {
        // Given
        _mockAuthService
            .Setup(x => x.LoginAsync(It.IsAny<string>(), It.IsAny<string>()))
            .ThrowsAsync(new AuthException("Invalid credentials"));

        // When
        await _viewModel.OnInput(new LoginViewModel.Input.Submit());

        // Then
        _viewModel.Out.IsLoginSuccess.Should().BeFalse();
        _viewModel.Out.Error.Should().NotBeNull();
    }

    // SDD-001: ViewModel must follow MVVM UDF pattern
    [Fact]
    public void ViewModel_ShouldFollowUDFPattern()
    {
        // Then - ViewModel has Input, Output, and Effect
        typeof(LoginViewModel).Should().HaveNestedType("Input");
        typeof(LoginViewModel).GetProperty("Out").Should().NotBeNull();
        typeof(LoginViewModel).GetProperty("Fx").Should().NotBeNull();
    }

    // SDD-003: Password must be hashed with PBKDF2-SHA256
    [Fact]
    public void PasswordHasher_ShouldUsePBKDF2SHA256()
    {
        // Given
        var hasher = new PasswordHasher();

        // When
        var hash = hasher.HashPassword("password123");

        // Then
        hash.Should().StartWith("pbkdf2:sha256:");
    }
}
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL SRS and SDD items have tests:
```csharp
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * SRS Requirements:
 * [x] SRS-001: Login with email/password - LoginViewModelTests
 * [x] SRS-002: Splash screen display - SplashViewModelTests
 * [x] SRS-003: Dashboard statistics - DashboardViewModelTests
 * [x] SRS-004: User registration - RegisterViewModelTests
 * [ ] SRS-005: Settings page - TODO
 *
 * SDD Design Requirements:
 * [x] SDD-001: MVVM UDF pattern - ViewModelTests
 * [x] SDD-002: CRDT offline sync - CrdtSyncManagerTests
 * [x] SDD-003: PBKDF2-SHA256 hashing - PasswordHasherTests
 * [ ] SDD-004: Plugin isolation - TODO
 */
```

#### Step 4: Mock External Dependencies - MANDATORY

⚠️ **CRITICAL**: Every Repository/Service method MUST return valid mock data. NEVER leave methods throwing `NotImplementedException`.

**Rules for Mock Classes:**
1. ALL methods must return valid mock data
2. Use `Task.Delay()` to simulate network latency (500-1000ms)
3. Mock data must match the entity structure exactly
4. Check enum values exist before using them
5. Include all required properties for records/classes

For external services or databases not yet available, implement mock classes:
```csharp
// tests/Arcana.App.Tests/Mocks/MockAuthService.cs
public class MockAuthService : IAuthService
{
    private static readonly List<MockUser> MockUsers = new()
    {
        new("1", "test@test.com", "pbkdf2:sha256:...", "Test User"),
        new("2", "demo@demo.com", "pbkdf2:sha256:...", "Demo User")
    };

    public async Task<AuthResult> LoginAsync(string email, string password)
    {
        await Task.Delay(500); // Simulate network delay

        var user = MockUsers.FirstOrDefault(u => u.Email == email);
        if (user != null && VerifyPassword(password, user.PasswordHash))
        {
            return new AuthResult
            {
                Success = true,
                AccessToken = $"mock_token_{DateTime.UtcNow.Ticks}",
                UserName = user.Name
            };
        }

        throw new AuthException("Invalid email or password");
    }

    public bool IsLoggedIn() => !string.IsNullOrEmpty(GetAccessToken());

    private string? GetAccessToken() =>
        Windows.Storage.ApplicationData.Current.LocalSettings.Values["access_token"] as string;
}

// src/Arcana.Infrastructure/DI/ServiceRegistration.cs - Switch between Mock and Real
public static class ServiceRegistration
{
    public static IServiceCollection AddAuthService(this IServiceCollection services)
    {
#if DEBUG
        services.AddSingleton<IAuthService, MockAuthService>();  // Development
#else
        services.AddSingleton<IAuthService, AuthService>();      // Production
#endif
        return services;
    }
}
```

#### Step 5: Run All Tests Before Completion
```bash
# Run all tests
dotnet test

# Run tests with coverage
dotnet test --collect:"XPlat Code Coverage"

# Run specific test project
dotnet test tests/Arcana.App.Tests/Arcana.App.Tests.csproj

# Run tests with detailed output
dotnet test --logger "console;verbosity=detailed"

# Verify all tests pass
dotnet test --no-build
```

#### Test Directory Structure
```
tests/
├── Arcana.App.Tests/
│   ├── ViewModels/
│   │   ├── LoginViewModelTests.cs
│   │   ├── RegisterViewModelTests.cs
│   │   ├── DashboardViewModelTests.cs
│   │   └── SplashViewModelTests.cs
│   ├── Services/
│   │   └── AuthServiceTests.cs
│   └── Mocks/
│       ├── MockAuthService.cs
│       └── MockUserRepository.cs
├── Arcana.Domain.Tests/
│   └── Services/
│       └── UserServiceTests.cs
├── Arcana.Data.Tests/
│   └── Repositories/
│       └── UserRepositoryTests.cs
└── Arcana.Infrastructure.Tests/
    └── Security/
        └── PasswordHasherTests.cs
```

### 2. Project Structure
```
arcana-windows/
├── src/
│   ├── Arcana.App/              # WinUI 3 presentation layer
│   │   ├── Views/               # XAML views
│   │   ├── ViewModels/          # MVVM UDF ViewModels
│   │   └── Navigation/          # NavGraph
│   ├── Arcana.Domain/           # Business entities & services
│   │   ├── Entities/
│   │   └── Services/
│   ├── Arcana.Data/             # Repository + Unit of Work
│   │   ├── Repositories/
│   │   └── DbContext/
│   ├── Arcana.Infrastructure/   # DI, Security, Settings
│   │   ├── Security/
│   │   └── Settings/
│   ├── Arcana.Plugins/          # Plugin runtime
│   │   └── Runtime/
│   └── Arcana.Plugins.Contracts/ # Plugin interfaces
│       └── Interfaces/
├── plugins/                     # Built-in plugins
│   └── FlowChartModule/
└── tests/                       # 507 unit tests
```

### 2. MVVM UDF Pattern (Unidirectional Data Flow)

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Reactive.Subjects;

public partial class UserViewModel : ObservableObject
{
    // MARK: - Input (vm.In): User actions dispatched as commands
    public sealed class Input
    {
        public record UpdateName(string Name);
        public record UpdateEmail(string Email);
        public record Submit;
    }

    // MARK: - Output (vm.Out): Read-only observable state
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private string _email = string.Empty;

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private string? _error;
    }

    // MARK: - Effect (vm.Fx): Side-effect subscriptions
    public sealed class Effect
    {
        public record NavigateBack;
        public record ShowSnackbar(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IUserService _userService;

    public UserViewModel(IUserService userService)
    {
        _userService = userService;
    }

    // Input handler - single entry point
    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.UpdateName updateName:
                Out.Name = updateName.Name;
                break;

            case Input.UpdateEmail updateEmail:
                Out.Email = updateEmail.Email;
                break;

            case Input.Submit:
                _ = SubmitAsync();
                break;
        }
    }

    private async Task SubmitAsync()
    {
        Out.IsLoading = true;
        Out.Error = null;

        try
        {
            await _userService.UpdateUserAsync(Out.Name, Out.Email);
            Fx.OnNext(new Effect.NavigateBack());
        }
        catch (Exception ex)
        {
            Out.Error = ex.Message;
        }
        finally
        {
            Out.IsLoading = false;
        }
    }
}
```

### 3. Type-Safe Navigation (NavGraph)

```csharp
public interface INavGraph
{
    void ToHome();
    void ToUserList();
    void ToUserDetail(string userId);
    void ToUserEdit(string userId);
    void ToOrderList();
    void ToOrderDetail(string orderId);
    void Back();
}

public class NavGraph : INavGraph
{
    private readonly Frame _frame;
    private readonly IServiceProvider _serviceProvider;

    public NavGraph(Frame frame, IServiceProvider serviceProvider)
    {
        _frame = frame;
        _serviceProvider = serviceProvider;
    }

    public void ToHome()
    {
        _frame.Navigate(typeof(HomePage));
    }

    public void ToUserList()
    {
        _frame.Navigate(typeof(UserListPage));
    }

    public void ToUserDetail(string userId)
    {
        _frame.Navigate(typeof(UserDetailPage), userId);
    }

    public void ToUserEdit(string userId)
    {
        _frame.Navigate(typeof(UserEditPage), userId);
    }

    public void ToOrderList()
    {
        _frame.Navigate(typeof(OrderListPage));
    }

    public void ToOrderDetail(string orderId)
    {
        _frame.Navigate(typeof(OrderDetailPage), orderId);
    }

    public void Back()
    {
        if (_frame.CanGoBack)
        {
            _frame.GoBack();
        }
    }
}

// Plugin-level navigation
public interface IPluginNavGraph
{
    void ToPluginView(string viewKey);
    void ToPluginView(string viewKey, object parameter);
}

public class FlowChartNavGraph : IPluginNavGraph
{
    public void ToNewEditor() => ToPluginView("flowchart-editor");
    public void ToEditor(string chartId) => ToPluginView("flowchart-editor", chartId);

    public void ToPluginView(string viewKey)
    {
        // Plugin navigation implementation
    }

    public void ToPluginView(string viewKey, object parameter)
    {
        // Plugin navigation with parameter
    }
}
```

### 4. Plugin System (18 Plugin Types)

```csharp
// Plugin interface
public interface IArcanaPlugin
{
    string Key { get; }
    string Name { get; }
    string Version { get; }
    PluginManifest Manifest { get; }
    Task OnActivateAsync(IPluginContext context);
    Task OnDeactivateAsync();
}

// Plugin manifest
public record PluginManifest
{
    public string Key { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string Version { get; init; } = "1.0.0";
    public string Description { get; init; } = string.Empty;
    public string Author { get; init; } = string.Empty;
    public string[] Dependencies { get; init; } = Array.Empty<string>();
    public PluginType Type { get; init; } = PluginType.Module;
    public string[] ActivationEvents { get; init; } = Array.Empty<string>();
}

// 18 Plugin types
public enum PluginType
{
    Menu,           // Menu extensions
    View,           // Custom views
    Module,         // Full feature modules
    Theme,          // UI themes
    Authentication, // Auth providers
    Data,           // Data sources
    Command,        // Custom commands
    Service,        // Background services
    Validator,      // Validation rules
    Storage,        // Storage providers
    Export,         // Export formats
    Import,         // Import formats
    Report,         // Report generators
    Notification,   // Notification channels
    Logging,        // Logging providers
    Cache,          // Cache providers
    Search,         // Search providers
    Analytics       // Analytics providers
}

// Plugin context with 12 shared services
public interface IPluginContext
{
    IMessageBus MessageBus { get; }
    IEventAggregator EventAggregator { get; }
    IStateStore StateStore { get; }
    IPluginNavGraph Navigation { get; }
    IDialogService DialogService { get; }
    INotificationService NotificationService { get; }
    ISettingsService SettingsService { get; }
    ILoggerFactory LoggerFactory { get; }
    IServiceProvider ServiceProvider { get; }
    IPluginStorage Storage { get; }
    ILocalizationService Localization { get; }
    IThemeService ThemeService { get; }
}

// Plugin implementation
[PluginManifest(
    Key = "flowchart-module",
    Name = "Flow Chart Module",
    Version = "1.0.0",
    Type = PluginType.Module
)]
public class FlowChartPlugin : IArcanaPlugin
{
    public string Key => "flowchart-module";
    public string Name => "Flow Chart Module";
    public string Version => "1.0.0";
    public PluginManifest Manifest { get; } = new()
    {
        Key = "flowchart-module",
        Name = "Flow Chart Module",
        Type = PluginType.Module,
        ActivationEvents = new[] { "onCommand:flowchart.new" }
    };

    private IPluginContext? _context;

    public async Task OnActivateAsync(IPluginContext context)
    {
        _context = context;

        // Register views
        context.Navigation.RegisterView("flowchart-editor", typeof(FlowChartEditorView));
        context.Navigation.RegisterView("flowchart-list", typeof(FlowChartListView));

        // Register commands
        context.MessageBus.Subscribe<NewFlowChartCommand>(OnNewFlowChart);

        // Register menu items
        context.EventAggregator.Publish(new RegisterMenuItemEvent
        {
            MenuId = "tools",
            Item = new MenuItem("Flow Chart", "flowchart.new")
        });

        await Task.CompletedTask;
    }

    public async Task OnDeactivateAsync()
    {
        // Cleanup
        await Task.CompletedTask;
    }

    private void OnNewFlowChart(NewFlowChartCommand command)
    {
        _context?.Navigation.ToPluginView("flowchart-editor");
    }
}

// Plugin runtime with assembly isolation
public class PluginRuntime
{
    private readonly Dictionary<string, AssemblyLoadContext> _loadContexts = new();
    private readonly Dictionary<string, IArcanaPlugin> _plugins = new();

    public async Task LoadPluginAsync(string pluginPath)
    {
        // Create isolated AssemblyLoadContext
        var loadContext = new PluginLoadContext(pluginPath);
        var assembly = loadContext.LoadFromAssemblyPath(pluginPath);

        // Find plugin type
        var pluginType = assembly.GetTypes()
            .FirstOrDefault(t => typeof(IArcanaPlugin).IsAssignableFrom(t));

        if (pluginType == null)
            throw new InvalidOperationException("No plugin found in assembly");

        var plugin = (IArcanaPlugin)Activator.CreateInstance(pluginType)!;

        _loadContexts[plugin.Key] = loadContext;
        _plugins[plugin.Key] = plugin;
    }

    public async Task UnloadPluginAsync(string key)
    {
        if (_plugins.TryGetValue(key, out var plugin))
        {
            await plugin.OnDeactivateAsync();
            _plugins.Remove(key);
        }

        if (_loadContexts.TryGetValue(key, out var context))
        {
            context.Unload();
            _loadContexts.Remove(key);
        }
    }
}
```

### 5. Repository + Unit of Work Pattern

```csharp
// Generic repository interface
public interface IRepository<T> where T : class, IEntity
{
    Task<T?> GetByIdAsync(string id);
    Task<IEnumerable<T>> GetAllAsync();
    Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate);
    Task AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(T entity);
    Task SoftDeleteAsync(T entity);
}

// Unit of Work interface
public interface IUnitOfWork : IDisposable
{
    IRepository<User> Users { get; }
    IRepository<Order> Orders { get; }
    IRepository<Product> Products { get; }
    IRepository<Customer> Customers { get; }
    Task<int> SaveChangesAsync();
    Task BeginTransactionAsync();
    Task CommitAsync();
    Task RollbackAsync();
}

// Repository implementation
public class Repository<T> : IRepository<T> where T : class, IEntity
{
    protected readonly AppDbContext _context;
    protected readonly DbSet<T> _dbSet;

    public Repository(AppDbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    public async Task<T?> GetByIdAsync(string id)
    {
        return await _dbSet.FindAsync(id);
    }

    public async Task<IEnumerable<T>> GetAllAsync()
    {
        return await _dbSet.ToListAsync();
    }

    public async Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate)
    {
        return await _dbSet.Where(predicate).ToListAsync();
    }

    public async Task AddAsync(T entity)
    {
        entity.CreatedAt = DateTime.UtcNow;
        entity.UpdatedAt = DateTime.UtcNow;
        await _dbSet.AddAsync(entity);
    }

    public async Task UpdateAsync(T entity)
    {
        entity.UpdatedAt = DateTime.UtcNow;
        _dbSet.Update(entity);
        await Task.CompletedTask;
    }

    public async Task DeleteAsync(T entity)
    {
        _dbSet.Remove(entity);
        await Task.CompletedTask;
    }

    public async Task SoftDeleteAsync(T entity)
    {
        entity.IsDeleted = true;
        entity.DeletedAt = DateTime.UtcNow;
        await UpdateAsync(entity);
    }
}

// Unit of Work implementation
public class UnitOfWork : IUnitOfWork
{
    private readonly AppDbContext _context;
    private IDbContextTransaction? _transaction;

    public IRepository<User> Users { get; }
    public IRepository<Order> Orders { get; }
    public IRepository<Product> Products { get; }
    public IRepository<Customer> Customers { get; }

    public UnitOfWork(AppDbContext context)
    {
        _context = context;
        Users = new Repository<User>(context);
        Orders = new Repository<Order>(context);
        Products = new Repository<Product>(context);
        Customers = new Repository<Customer>(context);
    }

    public async Task<int> SaveChangesAsync()
    {
        return await _context.SaveChangesAsync();
    }

    public async Task BeginTransactionAsync()
    {
        _transaction = await _context.Database.BeginTransactionAsync();
    }

    public async Task CommitAsync()
    {
        if (_transaction != null)
        {
            await _transaction.CommitAsync();
            await _transaction.DisposeAsync();
            _transaction = null;
        }
    }

    public async Task RollbackAsync()
    {
        if (_transaction != null)
        {
            await _transaction.RollbackAsync();
            await _transaction.DisposeAsync();
            _transaction = null;
        }
    }

    public void Dispose()
    {
        _transaction?.Dispose();
        _context.Dispose();
    }
}
```

### 6. CRDT Sync Engine

```csharp
// Vector clock for causal ordering
public class VectorClock
{
    private readonly Dictionary<string, long> _clock = new();

    public void Increment(string nodeId)
    {
        _clock[nodeId] = _clock.GetValueOrDefault(nodeId, 0) + 1;
    }

    public void Merge(VectorClock other)
    {
        foreach (var (nodeId, timestamp) in other._clock)
        {
            _clock[nodeId] = Math.Max(
                _clock.GetValueOrDefault(nodeId, 0),
                timestamp
            );
        }
    }

    public CausalOrdering Compare(VectorClock other)
    {
        bool thisGreater = false;
        bool otherGreater = false;

        var allKeys = _clock.Keys.Union(other._clock.Keys);

        foreach (var key in allKeys)
        {
            var thisValue = _clock.GetValueOrDefault(key, 0);
            var otherValue = other._clock.GetValueOrDefault(key, 0);

            if (thisValue > otherValue) thisGreater = true;
            if (otherValue > thisValue) otherGreater = true;
        }

        if (thisGreater && otherGreater) return CausalOrdering.Concurrent;
        if (thisGreater) return CausalOrdering.After;
        if (otherGreater) return CausalOrdering.Before;
        return CausalOrdering.Equal;
    }
}

public enum CausalOrdering
{
    Before,
    After,
    Equal,
    Concurrent
}

// Conflict resolution strategies
public enum ConflictStrategy
{
    LastWriteWins,      // LWW: Use timestamp
    FirstWriteWins,     // FWW: Keep original
    FieldLevelMerge,    // Merge at field level
    MultiValue,         // Keep all values (MV register)
    Custom              // Custom resolver
}

// CRDT Sync Manager
public class CrdtSyncManager
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly VectorClock _localClock;
    private readonly string _nodeId;
    private readonly ConflictStrategy _defaultStrategy;

    public CrdtSyncManager(
        IUnitOfWork unitOfWork,
        string nodeId,
        ConflictStrategy defaultStrategy = ConflictStrategy.LastWriteWins)
    {
        _unitOfWork = unitOfWork;
        _nodeId = nodeId;
        _localClock = new VectorClock();
        _defaultStrategy = defaultStrategy;
    }

    public async Task<T> ApplyChangeAsync<T>(
        T localEntity,
        T remoteEntity,
        ConflictStrategy? strategy = null) where T : class, ISyncableEntity
    {
        var ordering = localEntity.VectorClock.Compare(remoteEntity.VectorClock);
        var effectiveStrategy = strategy ?? _defaultStrategy;

        return ordering switch
        {
            CausalOrdering.Before => remoteEntity,
            CausalOrdering.After => localEntity,
            CausalOrdering.Equal => localEntity,
            CausalOrdering.Concurrent => ResolveConflict(
                localEntity, remoteEntity, effectiveStrategy),
            _ => localEntity
        };
    }

    private T ResolveConflict<T>(
        T local,
        T remote,
        ConflictStrategy strategy) where T : class, ISyncableEntity
    {
        return strategy switch
        {
            ConflictStrategy.LastWriteWins =>
                local.UpdatedAt > remote.UpdatedAt ? local : remote,

            ConflictStrategy.FirstWriteWins =>
                local.CreatedAt < remote.CreatedAt ? local : remote,

            ConflictStrategy.FieldLevelMerge =>
                MergeFields(local, remote),

            _ => local
        };
    }

    private T MergeFields<T>(T local, T remote) where T : class, ISyncableEntity
    {
        // Field-level merge: take newer value for each field
        var properties = typeof(T).GetProperties()
            .Where(p => p.CanRead && p.CanWrite);

        foreach (var prop in properties)
        {
            var localMeta = local.GetFieldMetadata(prop.Name);
            var remoteMeta = remote.GetFieldMetadata(prop.Name);

            if (remoteMeta.UpdatedAt > localMeta.UpdatedAt)
            {
                prop.SetValue(local, prop.GetValue(remote));
            }
        }

        // Merge vector clocks
        local.VectorClock.Merge(remote.VectorClock);
        return local;
    }

    public async Task MarkForSyncAsync<T>(T entity) where T : class, ISyncableEntity
    {
        _localClock.Increment(_nodeId);
        entity.VectorClock = _localClock;
        entity.SyncStatus = SyncStatus.Pending;
        entity.UpdatedAt = DateTime.UtcNow;

        await _unitOfWork.SaveChangesAsync();
    }
}
```

### 7. Security Architecture

```csharp
// Password hashing with PBKDF2-SHA256
public class PasswordHasher : IPasswordHasher
{
    private const int Iterations = 100_000;
    private const int SaltSize = 16;
    private const int HashSize = 32;

    public string HashPassword(string password)
    {
        var salt = RandomNumberGenerator.GetBytes(SaltSize);
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        var result = new byte[SaltSize + HashSize];
        Buffer.BlockCopy(salt, 0, result, 0, SaltSize);
        Buffer.BlockCopy(hash, 0, result, SaltSize, HashSize);

        return Convert.ToBase64String(result);
    }

    public bool VerifyPassword(string password, string hashedPassword)
    {
        var bytes = Convert.FromBase64String(hashedPassword);

        var salt = new byte[SaltSize];
        Buffer.BlockCopy(bytes, 0, salt, 0, SaltSize);

        var storedHash = new byte[HashSize];
        Buffer.BlockCopy(bytes, SaltSize, storedHash, 0, HashSize);

        var computedHash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        return CryptographicOperations.FixedTimeEquals(storedHash, computedHash);
    }
}

// RBAC (Role-Based Access Control)
public interface IAuthorizationService
{
    Task<bool> HasPermissionAsync(string userId, string permission);
    Task<bool> IsInRoleAsync(string userId, string role);
    Task<IEnumerable<string>> GetPermissionsAsync(string userId);
}

public class AuthorizationService : IAuthorizationService
{
    private readonly IUnitOfWork _unitOfWork;

    public AuthorizationService(IUnitOfWork unitOfWork)
    {
        _unitOfWork = unitOfWork;
    }

    public async Task<bool> HasPermissionAsync(string userId, string permission)
    {
        var permissions = await GetPermissionsAsync(userId);
        return permissions.Contains(permission);
    }

    public async Task<bool> IsInRoleAsync(string userId, string role)
    {
        var user = await _unitOfWork.Users.GetByIdAsync(userId);
        return user?.Roles.Any(r => r.Name == role) ?? false;
    }

    public async Task<IEnumerable<string>> GetPermissionsAsync(string userId)
    {
        var user = await _unitOfWork.Users.GetByIdAsync(userId);
        if (user == null) return Enumerable.Empty<string>();

        return user.Roles
            .SelectMany(r => r.Permissions)
            .Select(p => p.Name)
            .Distinct();
    }
}

// Audit logging
public class AuditService : IAuditService
{
    private readonly IUnitOfWork _unitOfWork;

    public async Task LogAsync(AuditEntry entry)
    {
        entry.Timestamp = DateTime.UtcNow;
        await _unitOfWork.AuditLogs.AddAsync(entry);
        await _unitOfWork.SaveChangesAsync();
    }
}

public record AuditEntry
{
    public string Id { get; init; } = Guid.NewGuid().ToString();
    public string UserId { get; init; } = string.Empty;
    public string Action { get; init; } = string.Empty;
    public string EntityType { get; init; } = string.Empty;
    public string EntityId { get; init; } = string.Empty;
    public string? OldValue { get; init; }
    public string? NewValue { get; init; }
    public DateTime Timestamp { get; set; }
}
```

## Navigation Wiring Verification Guide

### 🚨 The Navigation Wiring Blind Spot

WinUI 3 Views with ViewModels often have navigation Effects that need View subscription:

```csharp
// SettingsViewModel.cs
public partial class SettingsViewModel : ObservableObject
{
    public sealed class Effect
    {
        public record NavigateToAccountInfo;  // ⚠️ Needs View subscription!
        public record NavigateToChangePassword;  // ⚠️ Needs View subscription!
        public record NavigateToUserList;  // ⚠️ Needs View subscription!
    }

    public Subject<Effect> Fx { get; } = new();

    private void GoToAccountInfo()
    {
        Fx.OnNext(new Effect.NavigateToAccountInfo());  // Does nothing if View doesn't subscribe!
    }
}
```

**Problem**: If the View doesn't subscribe to `Fx` and handle the Effect by calling `INavGraph`, the button appears functional but does nothing when clicked!

### Detection Patterns

```bash
# Find ViewModel Effect types
grep -rn "record Navigate\|record Show\|record Open" src/**/ViewModels/*.cs

# Find View subscriptions to Fx
grep -rn "Fx.Subscribe\|_viewModel.Fx" src/**/Views/*.cs

# Find INavGraph interface methods
grep -rn "void To[A-Z]" src/**/INavGraph.cs

# Find NavGraph implementations
grep -rn "public void To[A-Z]" src/**/NavGraph.cs

# Compare: Every Effect.Navigate* MUST have View subscription AND NavGraph method
```

### Verification Checklist

1. **List Effect types in each ViewModel**:
   ```bash
   grep -h "record Navigate" src/Arcana.App/ViewModels/SettingsViewModel.cs
   ```

2. **List Effect handlers in corresponding View**:
   ```bash
   grep -h "NavigateTo\|Effect.Navigate" src/Arcana.App/Views/SettingsPage.xaml.cs
   ```

3. **Every Effect MUST have View handler AND NavGraph method!** Any missing = dead button

### Correct Wiring Example

```csharp
// SettingsViewModel.cs (emits Effects)
public partial class SettingsViewModel : ObservableObject
{
    public sealed class Effect
    {
        public record NavigateToAccountInfo;
        public record NavigateToChangePassword;
        public record NavigateToUserList;
    }

    public Subject<Effect> Fx { get; } = new();

    public void GoToAccountInfo() => Fx.OnNext(new Effect.NavigateToAccountInfo());
    public void GoToChangePassword() => Fx.OnNext(new Effect.NavigateToChangePassword());
    public void GoToUserList() => Fx.OnNext(new Effect.NavigateToUserList());
}

// SettingsPage.xaml.cs (subscribes and handles Effects)
public sealed partial class SettingsPage : Page
{
    private readonly SettingsViewModel _viewModel;
    private readonly INavGraph _navGraph;
    private readonly IDisposable _effectSubscription;

    public SettingsPage(SettingsViewModel viewModel, INavGraph navGraph)
    {
        _viewModel = viewModel;
        _navGraph = navGraph;
        InitializeComponent();

        _effectSubscription = _viewModel.Fx.Subscribe(effect =>  // ✅ Subscribed
        {
            switch (effect)
            {
                case SettingsViewModel.Effect.NavigateToAccountInfo:
                    _navGraph.ToAccountInfo();  // ✅ Calls NavGraph
                    break;
                case SettingsViewModel.Effect.NavigateToChangePassword:
                    _navGraph.ToChangePassword();  // ✅ Calls NavGraph
                    break;
                case SettingsViewModel.Effect.NavigateToUserList:
                    _navGraph.ToUserList();  // ✅ Calls NavGraph
                    break;
            }
        });
    }
}

// INavGraph.cs (interface declares methods)
public interface INavGraph
{
    void ToAccountInfo();  // ✅ Declared
    void ToChangePassword();  // ✅ Declared
    void ToUserList();  // ✅ Declared
}

// NavGraph.cs (implements methods)
public class NavGraph : INavGraph
{
    public void ToAccountInfo() => _frame.Navigate(typeof(AccountInfoPage));  // ✅ Implemented
    public void ToChangePassword() => _frame.Navigate(typeof(ChangePasswordPage));  // ✅ Implemented
    public void ToUserList() => _frame.Navigate(typeof(UserListPage));  // ✅ Implemented
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering (5 layers)
- [ ] ViewModel uses MVVM UDF pattern (Input/Output/Effect)
- [ ] Type-safe navigation via INavGraph
- [ ] Repository + Unit of Work pattern implemented
- [ ] CRDT sync for offline-first scenarios
- [ ] 🚨 ALL ViewModel Effects are subscribed in Views
- [ ] 🚨 ALL INavGraph methods have NavGraph implementations
- [ ] 🚨 ALL Service→Repository/UnitOfWork method calls exist in interfaces
- [ ] 🚨 ALL IRepository interface methods have Repository implementations

### Performance Checks
- [ ] Use async/await properly
- [ ] Implement lazy loading for plugins
- [ ] Cache frequently accessed data
- [ ] Optimize database queries with EF Core

### Security Checks
- [ ] PBKDF2-SHA256 for password hashing (100K iterations)
- [ ] RBAC properly configured
- [ ] Audit logging enabled
- [ ] Assembly isolation for plugins
- [ ] No hardcoded secrets

### Plugin Checks
- [ ] Plugin manifest complete
- [ ] Activation events configured
- [ ] Cleanup in OnDeactivateAsync
- [ ] Uses IPluginContext services

## Common Issues

### WinUI 3 Issues
1. Ensure Windows App SDK is properly installed
2. Check XAML compilation errors
3. Verify resource dictionary merging

### EF Core Issues
1. Run migrations: `dotnet ef database update`
2. Check connection string configuration
3. Review lazy loading settings

### Plugin Loading Issues
1. Verify AssemblyLoadContext configuration
2. Check plugin dependencies
3. Review manifest activation events

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| .NET | 10.0+ |
| C# | 14.0+ |
| WinUI 3 | 3.0+ |
| EF Core | 10.0+ |
| SQLite | Latest |
| xUnit | Latest |
| CommunityToolkit.Mvvm | Latest |
