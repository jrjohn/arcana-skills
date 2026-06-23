---
name: arcana-android-developer-skill
description: Android development guide based on Arcana Android enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design, Jetpack Compose, Hilt DI, and MVVM Input/Output pattern. Suitable for Android project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Android Developer Skill

Professional Android development skill based on [Arcana Android](https://github.com/jrjohn/arcana-android) enterprise architecture.

## ⚡ Workflow — Always Start From the Reference Project

**Every task starts by cloning the complete reference project — NEVER scaffold a new Android project from scratch:**

```bash
git clone https://github.com/jrjohn/arcana-android.git [new-project-directory]
```

1. **Clone** the reference project (command above).
2. **Build + test the UNTOUCHED clone first** to establish a green baseline (`./gradlew clean build` then `./gradlew test`) before changing anything.
3. **Follow [0. Project Setup](#0-project-setup---critical)** to rename the project/package and strip the demo screens — while KEEPING the infrastructure: auth/security layers (encrypted SharedPreferences token storage), caching (`core/cache`), offline/sync (`sync/` + Room `AppDatabase`), the DI container (`di/` Hilt modules), and deployment/build configs (Gradle setup, `gradle/libs.versions.toml`).
4. **Add features by copying the nearest working feature, then adapting** (see [🔁 Adding a feature](#-adding-a-feature--copy-the-nearest-working-feature-not-from-scratch)) — the recipe below is the completeness checklist. ([File-by-File Feature Recipe](#file-by-file-feature-recipe))

### 🔁 Adding a feature = copy the nearest working feature (NOT from scratch)

**When you add a new feature/screen, do NOT re-create it from memory by walking the File-by-File Recipe on a blank slate. Copy the nearest already-working feature in the cloned reference, then adapt it.**

1. **Find the closest conformant feature** already in the reference — e.g. the example **Orders** list/detail feature, which already demonstrates the full Model → Repository → Service/UseCase → ViewModel (Input/Output/Effect) → View chain wired through DI.
2. **Duplicate its ENTIRE file set** (domain model, repository interface, service, Room entity, DAO + AppDatabase registration, DTO + API, repository implementation, mock repository, DI registration, ViewModel, screens, route + NavGraph, unit tests, UI tests) 1:1, keeping every layer.
3. **Rename + adapt** to the new domain (types, navigation, endpoints, DI bindings).
4. **Diff against the original** to confirm nothing was dropped — same layer split, same ViewModel/use-case/repository boundary, same error model, same tests.

**Why this is mandatory:** the File-by-File Recipe is a *checklist of what must exist*, not a from-scratch build order. Re-deriving the pattern each time makes every step a chance to skip a layer (the ViewModel, the repository), wire a shortcut (view → data/API directly), or drop the tests — the "vibe-coding" deviations that compile and pass coverage but fail architecture review. Copying a known-good feature carries conformance in *by construction*; the recipe is then only your verification that nothing is missing.

### Supporting files — load on demand

| File | When to read |
|------|--------------|
| `reference.md` | Deep-dive architecture reference — layer responsibilities and project conventions |
| `patterns.md` | Extended code patterns beyond those inlined in this file |
| `patterns/mvvm-input-output.md` | Detailed MVVM Input/Output ViewModel walkthrough |
| `examples.md` | Complete end-to-end feature examples to copy from |
| `checklists/production-ready.md` | Pre-release checklist before declaring a feature done |
| `verification/commands.md` | Full verification command set (superset of Quick Verification below) |

---

## File-by-File Feature Recipe

Ordered file-by-file recipe for adding a complete feature (example: **Orders**) through all layers. Create files in this order — each step compiles against the previous ones. Paths are relative to `app/src/main/java/<your/package>/`.

1. **Domain model** → `domain/model/Order.kt`
   — Immutable data class, all fields from Spec.
2. **Repository interface** → `domain/repository/OrderRepository.kt`
   — `suspend fun` methods returning `Result<T>` / `Flow<T>` of Domain models.
3. **Service** → `domain/service/OrderService.kt`
   — Business rules and validation; only calls methods that exist on the repository interface.
4. **Room entity** → `data/local/entity/OrderEntity.kt`
   — With `toDomain()` / `toEntity()` mapping and `syncStatus` field.
5. **DAO** → `data/local/dao/OrderDao.kt` — then register the entity + DAO in `data/local/AppDatabase.kt`.
6. **DTO + API** → `data/remote/dto/OrderDto.kt`, `data/remote/api/OrderApi.kt`.
7. **Repository implementation** → `data/repository/OrderRepositoryImpl.kt`
   — Offline-first: Room as single source of truth, schedule background sync.
8. **Mock repository** → `data/repository/mock/MockOrderRepository.kt`
   — NEVER return `emptyList()`/null; 5-10 varied items, `delay()` latency, IDs consistent with other repositories.
9. **DI registration** → `di/RepositoryModule.kt` — `@Binds` the mock (development) or real implementation.
10. **ViewModel** → `ui/screens/orders/OrderListViewModel.kt`
    — `@HiltViewModel`, Input/Output pattern + Effect channel.
11. **Screen** → `ui/screens/orders/OrderListScreen.kt` (+ `OrderDetailScreen.kt`)
    — Loading/Error/Empty/Content states; stateless content composable.
12. **Route** → `nav/NavRoutes.kt` — add `Orders` / `OrderDetail` route objects.
13. **NavGraph** → `nav/NavGraph.kt` — `composable()` for each route; wire ALL `onNavigate*` callbacks (no default `= {}` left unwired).
14. **Unit tests** → `app/src/test/.../ui/screens/orders/OrderListViewModelTest.kt`, `app/src/test/.../data/repository/OrderRepositoryTest.kt`.
15. **UI tests** → `app/src/androidTest/.../ui/screens/OrderListScreenTest.kt`.

Then run the Quick Verification Commands — route count must match composable count, and no empty mock lists may remain.

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         Compose UI + MVVM + Input/Output            │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + Room + API          │
└─────────────────────────────────────────────────────┘
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation → Domain → Data
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces

---

## 📋 Quick Reference Card

### When Creating New Screen:
```
1. [ ] Add route to NavRoutes.kt
2. [ ] Add composable to NavGraph.kt
3. [ ] Create ViewModel with Input/Output pattern
4. [ ] Implement Loading/Error/Empty states
5. [ ] Add navigation wiring (back, forward)
6. [ ] Verify mock data is non-empty
```

### When Creating New Repository:
```
1. [ ] Define interface in domain/repository/
2. [ ] Implement in data/repository/
3. [ ] Register in Hilt module (@Binds)
4. [ ] Add mock data (NEVER empty!)
5. [ ] Verify ID consistency with other repositories
```

### When Creating New Feature:
```
1. [ ] Check Spec for all related screens
2. [ ] Apply Spec Gap Prediction (List→Detail, Create→Edit)
3. [ ] Implement all UI states (Loading/Error/Empty/Success)
4. [ ] Run verification commands before PR
```

### Quick Diagnosis:
| Symptom | Likely Cause | Check Command |
|---------|--------------|---------------|
| Blank screen | Empty mock data | `grep "emptyList()" *RepositoryImpl.kt` |
| Navigation crash | Missing composable | `grep "NavRoutes\." NavGraph.kt` |
| Data not loading | ID mismatch | `grep "id = \"" *RepositoryImpl.kt` |
| Click does nothing | Empty handler | `grep "onClick = { }" *.kt` |

---

## 🚦 Rules Priority

### 🔴 CRITICAL (Must follow, violations cause Bug/Crash)
- Zero-Null Policy - Repository stubs must not return null/empty
- Navigation Wiring - All NavRoutes must have composable destinations
- ID Consistency - IDs must be consistent across Repositories
- Onboarding Flow - Must check Onboarding status after Register/Login

### 🟡 IMPORTANT (Strongly recommended, affects quality)
- UI State Handling - Loading/Error/Empty states
- Mock Data Quality - Use realistic mock data
- MVVM Input/Output - Follow standard pattern
- Offline-First - Local-first strategy

### 🟢 RECOMMENDED (Suggested, improves UX)
- Animation Standards - Transition animations
- Accessibility - Accessibility support
- Pull-to-Refresh - List pull-to-refresh
- Skeleton Loading - Skeleton screen loading

---

## 🚨 Error Handling Pattern

### Unified Error Model
```kotlin
// domain/model/AppError.kt
sealed class AppError {
    // Network errors
    data class Network(
        val code: Int,
        val message: String
    ) : AppError()

    // Validation errors
    data class Validation(
        val field: String,
        val reason: String
    ) : AppError()

    // Authentication errors
    sealed class Auth : AppError() {
        object SessionExpired : Auth()
        object InvalidCredentials : Auth()
        object Unauthorized : Auth()
    }

    // Not found
    data class NotFound(val resource: String) : AppError()

    // Unknown
    data class Unknown(val cause: Throwable? = null) : AppError()
}
```

### Error Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Repository │ → │  ViewModel  │ → │  UiState    │ → │   Screen    │
│  Result<T>  │    │ Handle Err  │    │  .Error     │    │ ErrorUI     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Repository Layer
```kotlin
// Return Result with AppError
suspend fun getData(): Result<Data> {
    return try {
        val response = api.getData()
        if (response.isSuccessful) {
            Result.success(response.body()!!)
        } else {
            Result.failure(AppError.Network(response.code(), response.message()))
        }
    } catch (e: IOException) {
        Result.failure(AppError.Network(-1, "Network unavailable"))
    } catch (e: Exception) {
        Result.failure(AppError.Unknown(e))
    }
}
```

### ViewModel Layer
```kotlin
// Handle errors and map to UiState
private fun handleResult(result: Result<Data>) {
    result.fold(
        onSuccess = { data ->
            _output.update { it.copy(isLoading = false, data = data) }
        },
        onFailure = { error ->
            val message = when (error) {
                is AppError.Network -> "Network connection failed, please try again later"
                is AppError.Auth.SessionExpired -> "Session expired, please login again"
                is AppError.NotFound -> "Data not found"
                else -> "An unknown error occurred"
            }
            _output.update { it.copy(isLoading = false, error = message) }

            // Handle auth errors globally
            if (error is AppError.Auth.SessionExpired) {
                _effect.emit(Effect.NavigateToLogin)
            }
        }
    )
}
```

### Screen Layer
```kotlin
@Composable
fun DataScreen(viewModel: DataViewModel = hiltViewModel()) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    when {
        output.isLoading -> LoadingState()
        output.error != null -> ErrorState(
            message = output.error!!,
            onRetry = { viewModel.onInput(Input.Retry) }
        )
        output.data != null -> DataContent(output.data!!)
        else -> EmptyState()
    }
}

@Composable
private fun ErrorState(message: String, onRetry: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(Icons.Default.Error, null, tint = MaterialTheme.colorScheme.error)
        Spacer(modifier = Modifier.height(16.dp))
        Text(message, style = MaterialTheme.typography.bodyLarge)
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onRetry) {
            Text("Retry")
        }
    }
}
```

### Global Error Handling
```kotlin
// For unhandled exceptions
@HiltViewModel
class MainViewModel @Inject constructor() : ViewModel() {

    private val exceptionHandler = CoroutineExceptionHandler { _, throwable ->
        // Log to crash reporting
        Logger.e("Unhandled exception", throwable)
        // Show generic error
        _globalError.value = "An error occurred, please try again later"
    }

    fun launchSafely(block: suspend () -> Unit) {
        viewModelScope.launch(exceptionHandler) {
            block()
        }
    }
}
```

---

## 🧪 Test Coverage Targets

### Coverage Goals by Layer
| Layer | Target | Focus Areas |
|-------|--------|-------------|
| **Domain (UseCase/Service)** | 90%+ | Business logic, edge cases |
| **Data (Repository)** | 80%+ | Data transformation, error handling |
| **Presentation (ViewModel)** | 85%+ | State management, input handling |
| **UI (Compose)** | 60%+ | Critical user flows |

### Test Types Required
```kotlin
/**
 * Test Requirements Checklist:
 *
 * Unit Tests (test/):
 * - [ ] ViewModel: All Input → Output transformations
 * - [ ] Repository: Success and failure paths
 * - [ ] Service: Business logic with edge cases
 *
 * Integration Tests (androidTest/):
 * - [ ] Repository + Room: Data persistence
 * - [ ] Repository + API: Network responses (mock server)
 *
 * UI Tests (androidTest/):
 * - [ ] Critical flows: Login, Registration, Core features
 * - [ ] Error states: Network error, Empty state
 */
```

### Test Naming Convention
```kotlin
@Test
fun `methodName should expectedBehavior when condition`() {
    // Given - Arrange
    // When - Act
    // Then - Assert
}

// Examples:
fun `login should emit success when credentials are valid`()
fun `loadData should emit error when network fails`()
fun `submitForm should show validation error when email is invalid`()
```

### Minimum Tests Before PR
```bash
# Run before creating PR
./gradlew test                    # Unit tests
./gradlew connectedAndroidTest    # Instrumented tests
./gradlew jacocoTestReport        # Coverage report

# Coverage check
MIN_COVERAGE=70
ACTUAL=$(cat build/reports/jacoco/test/html/index.html | grep -oP 'Total.*?\K\d+(?=%)')
if [ "$ACTUAL" -lt "$MIN_COVERAGE" ]; then
    echo "❌ Coverage $ACTUAL% < $MIN_COVERAGE% required"
    exit 1
fi
```

---

## Instructions

When handling Android development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented repositories (MUST be empty)
grep -rn "NotImplementedError\|Result.failure.*Not.*implement" app/src/main/java/

# 2. Check for empty click handlers (MUST be empty)
grep -rn "onClick\s*=\s*{\s*}\|onClick\s*=\s*{.*TODO" app/src/main/java/

# 3. Check for missing navigation destinations (compare route count vs composable count)
echo "Routes defined:" && grep -c "data object" app/src/main/java/**/nav/NavRoutes.kt
echo "Composables registered:" && grep -c "composable(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt

# 4. Verify build compiles
./gradlew :app:compileDebugKotlin

# 5. 🚨 Check for PlaceholderScreen (MUST be empty for production)
grep -rn "PlaceholderScreen\|即將推出\|Coming Soon" app/src/main/java/

# 6. 🚨 Run all tests (ALL must pass)
./gradlew test

# 7. 🚨 Check for unwired navigation callbacks (CRITICAL!)
# Find Screen functions with default empty navigation callbacks
grep -rn "onNavigate[A-Za-z]*:\s*(\s*)\s*->\s*Unit\s*=\s*{}" app/src/main/java/**/ui/screens/

# 8. 🚨 Verify NavGraph wires ALL Screen navigation callbacks
# For each Screen with onNavigate* parameters, ensure NavGraph passes real callbacks
# Example: SettingsScreen has onNavigateToAccountInfo, NavGraph must pass { navController.navigate(...) }
echo "=== Screen Navigation Callbacks ===" && \
grep -rh "onNavigateTo[A-Za-z]*:" app/src/main/java/**/ui/screens/*.kt | grep -oE "onNavigateTo[A-Za-z]+" | sort -u
echo "=== NavGraph Wired Callbacks ===" && \
grep -rh "onNavigateTo[A-Za-z]*\s*=" app/src/main/java/**/nav/*NavGraph.kt | grep -oE "onNavigateTo[A-Za-z]+" | sort -u
# Compare the two lists - they should match for each Screen!

# 9. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "repository\.[a-zA-Z]*(" app/src/main/java/**/domain/service/*.kt | sort -u
echo "=== Repository Methods Defined ===" && \
grep -rh "suspend fun [a-zA-Z]*(\|fun [a-zA-Z]*(" app/src/main/java/**/domain/repository/*.kt | grep -oE "fun [a-zA-Z]+\(" | sort -u

# 10. 🚨 Verify ALL Repository interface methods have implementations
echo "=== Repository Interface Methods ===" && \
grep -rh "suspend fun\|fun " app/src/main/java/**/domain/repository/*Repository.kt | grep -oE "fun [a-zA-Z]+" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "override.*suspend fun\|override.*fun " app/src/main/java/**/data/repository/*RepositoryImpl.kt | grep -oE "fun [a-zA-Z]+" | sort -u

# ═══════════════════════════════════════════════════════════════
# 🎨 UX COMPLETENESS VERIFICATION (NEW - Predictive Feature Check)
# ═══════════════════════════════════════════════════════════════

# 11. 🎨 Check for blank/empty UI content areas
grep -rn "尚無\|暫無\|No.*data\|Empty\|即將推出" app/src/main/java/**/ui/

# 12. 🎨 Check Tab content has actual implementation (not blank)
grep -rn -B2 -A5 "Tab(" app/src/main/java/**/ui/screens/ | grep -E "Tab\(|when.*selectedTab|HorizontalPager"

# 13. 🎨 Check for Chart/Visualization (required for data apps)
grep -rn "Canvas\|Chart\|Graph\|drawLine\|drawRect" app/src/main/java/**/ui/ || echo "⚠️ No charts found"

# 14. 🎨 Check for animation usage (if required by Spec)
grep -rn "LottieAnimation\|rememberLottieComposition\|animate" app/src/main/java/**/ui/ || echo "⚠️ No animations found - verify if required by Spec"

# 15. 🎨 Check for Text placeholders that should be graphics
grep -rn 'Text(.*fontSize.*=.*[4-9][0-9]\.sp)' app/src/main/java/**/ui/screens/ && echo "⚠️ Found large text - verify not placeholder for graphics"

# 16. 🎨 Check mock data quality (avoid generic test data)
grep -rn '"Test\|"Item \|"Example\|"User \|lorem\|ipsum' app/src/main/java/ && echo "⚠️ Found generic test data"
```

⚠️ **CRITICAL**: Route count MUST equal Composable count. If not, you have missing navigation destinations that will cause runtime crashes.

🚨 **ABSOLUTE REQUIREMENT**:
- PlaceholderScreen check MUST return empty
- "即將推出" / "Coming Soon" MUST NOT exist in production code
- ALL tests MUST pass (not just be written)
- **ALL Screen navigation callbacks MUST be wired in NavGraph** (not using default empty `= {}`)
- **Screen callbacks list MUST match NavGraph wired callbacks list**
- **ALL Repository methods called by Services MUST exist in Repository interfaces**
- **ALL Repository interface methods MUST have implementations in RepositoryImpl**

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 🚦 User Journey Flow Verification (PROACTIVE)

### The Problem

Navigation issues like "Onboarding skipped after login" are only discovered when users test the app manually. This section enables **proactive detection** of incomplete user flows.

### User Flow Checkpoint System

**CRITICAL**: Before completing any feature, verify ALL user journeys are complete.

```bash
# 32. 🚦 USER JOURNEY FLOW CHECK (Run BEFORE user testing!)

echo "=== User Journey Flow Verification ===" && \
echo ""

# Check 1: First-Time User Flow
echo "--- First-Time User Flow ---" && \
echo "Expected: Splash → Login/Register → Onboarding → Dashboard" && \
REGISTER_TARGET=$(grep -A5 "onRegisterSuccess" app/src/main/java/**/nav/*NavGraph.kt | grep "navigate(" | head -1) && \
echo "Register navigates to: $REGISTER_TARGET" && \
if echo "$REGISTER_TARGET" | grep -q "Dashboard"; then \
    echo "⚠️ WARNING: Register goes directly to Dashboard - Onboarding may be skipped!"; \
fi

# Check 2: Returning User Flow
echo "" && echo "--- Returning User Flow ---" && \
echo "Expected: Splash → (check session) → Dashboard OR Login" && \
LOGIN_TARGET=$(grep -A5 "onLoginSuccess" app/src/main/java/**/nav/*NavGraph.kt | grep "navigate(" | head -1) && \
echo "Login navigates to: $LOGIN_TARGET"

# Check 3: Onboarding Exists in NavGraph
echo "" && echo "--- Onboarding Registration ---" && \
ONBOARDING_ROUTE=$(grep "Onboarding" app/src/main/java/**/nav/NavRoutes.kt) && \
ONBOARDING_COMPOSABLE=$(grep "NavRoutes.Onboarding" app/src/main/java/**/nav/*NavGraph.kt) && \
if [ -z "$ONBOARDING_ROUTE" ]; then \
    echo "❌ MISSING: Onboarding route not defined in NavRoutes"; \
elif [ -z "$ONBOARDING_COMPOSABLE" ]; then \
    echo "❌ MISSING: Onboarding composable not registered in NavGraph"; \
else \
    echo "✅ Onboarding route and composable exist"; \
fi

# Check 4: Feature Gate Flows (Onboarding completion, subscription, etc.)
echo "" && echo "--- Feature Gate Checks ---" && \
grep -rn "isOnboardingCompleted\|isSubscribed\|isPremium\|isVerified" app/src/main/java/**/nav/ || \
echo "⚠️ No feature gates found in navigation - consider adding completion checks"
```

### Required User Journey Patterns

Every app should verify these flows exist and work:

| Flow Type | Pattern | Checkpoint |
|-----------|---------|------------|
| **First Launch** | Splash → Onboarding → Dashboard | Onboarding must show for new users |
| **New Registration** | Register → Onboarding → Dashboard | Never skip onboarding for new accounts |
| **Returning User (completed)** | Login → Dashboard | Only if onboarding was completed |
| **Returning User (incomplete)** | Login → Onboarding → Dashboard | Resume onboarding if not completed |
| **Session Expired** | Any Screen → Login | Redirect to login on auth failure |
| **Logout** | Settings → Login | Clear session and return to login |
| **Deep Link** | External → Specific Screen | Handle auth state before showing content |

### Flow Verification Checklist

```kotlin
/**
 * User Journey Verification Checklist
 *
 * First-Time Experience:
 * [ ] Splash checks if user is logged in
 * [ ] Splash checks if onboarding is completed
 * [ ] New users ALWAYS see onboarding before dashboard
 * [ ] Onboarding cannot be bypassed (no skip without completing)
 * [ ] Onboarding completion is persisted
 *
 * Authentication Flows:
 * [ ] Login success checks onboarding status
 * [ ] Register ALWAYS routes to onboarding
 * [ ] Logout clears all session data
 * [ ] Session expiry redirects to login
 *
 * Feature Gates:
 * [ ] Premium features check subscription status
 * [ ] Device-required features check connection status
 * [ ] Sensitive features require re-authentication
 *
 * Navigation Guards:
 * [ ] Protected routes redirect to login if not authenticated
 * [ ] Deep links handle unauthenticated state
 * [ ] Back navigation doesn't bypass required flows
 */
```

### Implementation Pattern for Feature Gates

```kotlin
// ✅ CORRECT: Check feature gates in navigation
composable(NavRoutes.Login.route) {
    val onboardingRepository: OnboardingRepository = hiltViewModel<LoginViewModel>().onboardingRepository

    LoginScreen(
        onLoginSuccess = { userId ->
            // Check if onboarding is completed
            viewModelScope.launch {
                val isCompleted = onboardingRepository.isOnboardingCompleted(userId)
                    .getOrDefault(false)

                if (isCompleted) {
                    navController.navigate(NavRoutes.Dashboard.route) {
                        popUpTo(NavRoutes.Login.route) { inclusive = true }
                    }
                } else {
                    navController.navigate(NavRoutes.Onboarding.route) {
                        popUpTo(NavRoutes.Login.route) { inclusive = true }
                    }
                }
            }
        }
    )
}

// ❌ WRONG: Direct navigation without checking gates
onLoginSuccess = {
    navController.navigate(NavRoutes.Dashboard.route)  // Skips onboarding check!
}
```

### Quick Flow Detection Commands

```bash
# 33. 🚦 Find all navigation decision points
grep -rn "navController.navigate\|navigate(" app/src/main/java/**/nav/ | \
grep -v "popBackStack" | head -20

# 34. 🚦 Find potential bypassed gates
echo "=== Potential Bypassed Feature Gates ===" && \
grep -B5 "NavRoutes.Dashboard" app/src/main/java/**/nav/*NavGraph.kt | \
grep -v "isOnboardingCompleted\|isCompleted\|checkOnboarding" && \
echo "⚠️ Review above - Dashboard navigation may bypass required flows"

# 35. 🚦 Verify onboarding status is checked
grep -rn "isOnboardingCompleted" app/src/main/java/ | wc -l | \
xargs -I {} sh -c 'if [ {} -eq 0 ]; then echo "❌ No onboarding completion check found!"; fi'
```

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty lists for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank Canvas)
- Line charts that skip rendering (e.g., `if (points.size < 2) return`)
- Empty state screens even when data structure exists

### Mock Data Rules

**Rule 1: List data for charts MUST have at least 7 items**
```kotlin
// ❌ BAD - Chart will be blank
override suspend fun getWeeklySummary(...): Result<WeeklySummary> {
    return Result.success(
        WeeklySummary(
            dailyReports = emptyList()  // ← Chart has no data to render!
        )
    )
}

// ✅ GOOD - Chart has data to display
override suspend fun getWeeklySummary(...): Result<WeeklySummary> {
    val mockDailyReports = (0 until 7).map { dayOffset ->
        createMockDailyReport(
            score = listOf(72, 78, 85, 80, 76, 88, 82)[dayOffset],
            duration = listOf(390, 420, 450, 410, 380, 460, 435)[dayOffset]
        )
    }
    return Result.success(
        WeeklySummary(dailyReports = mockDailyReports)
    )
}
```

**Rule 2: Use realistic, varied sample values**
```kotlin
// ❌ BAD - Monotonous test data
scores = listOf(80, 80, 80, 80, 80, 80, 80)

// ✅ GOOD - Realistic variation
scores = listOf(72, 78, 85, 80, 76, 88, 82)  // Shows trend
```

**Rule 3: Data must match domain model exactly**
```kotlin
// Before creating mock data, ALWAYS verify the data class structure:
grep -A 20 "data class TherapyData" app/src/main/java/**/domain/model/*.kt
```

**Rule 4: Create helper functions for complex mock data**
```kotlin
// ✅ Create reusable mock factory for your domain models
private fun createMockEntity(param1: Int, param2: Int): YourDomainEntity {
    return YourDomainEntity(
        id = "mock_${System.currentTimeMillis()}",
        field1 = param1,
        field2 = NestedObject(value = param2, ...),
        // ... all required fields from Spec
    )
}
```

### Quick Verification Commands for Mock Data

```bash
# 17. 🚨 Check for empty list returns in Repository stubs (MUST FIX)
grep -rn "emptyList()\|listOf()" app/src/main/java/**/data/repository/*RepositoryImpl.kt

# 18. 🚨 Verify chart-related data has mock values
grep -rn "dailyReports\|weeklyData\|chartData" app/src/main/java/**/data/repository/ | grep -E "emptyList|= listOf\(\)"
```

---

## 🔗 Cross-Repository ID Consistency

### The ID Mismatch Problem

When multiple repositories reference the same entities, **IDs MUST be consistent across all repositories**. Mismatched IDs cause:
- `getById()` returns null/failure even though data exists
- Navigation to detail screens fails silently
- Empty UI despite having mock data in the system

### ID Consistency Rules

**Rule 1: Use identical IDs across all Repository stubs**
```kotlin
// ❌ BAD - IDs don't match between repositories
// RepositoryA:
createMockEntity(id = "entity_1", name = "Item A")

// RepositoryB:
Entity(id = "entity_001", ...)  // ← ID mismatch!

// ✅ GOOD - Consistent IDs across repositories
// RepositoryA:
createMockEntity(id = "entity_1", name = "Item A")

// RepositoryB:
Entity(id = "entity_1", ...)  // ← Same ID!
```

**Rule 2: Verify IDs before implementing cross-repository features**
```bash
# Check all entity IDs used across repositories
grep -rn "id = \"[a-z]*_" app/src/main/java/**/data/repository/
```

**Rule 3: Create ID constants for shared entities**
```kotlin
// ✅ Best practice - use constants
object MockIds {
    const val ENTITY_A = "entity_1"
    const val ENTITY_B = "entity_2"
    const val ENTITY_C = "entity_3"
}
```

### Quick Verification Commands for ID Consistency

```bash
# 19. 🚨 Check cross-repository ID references (compare values)
echo "=== Entity IDs across Repositories ===" && \
grep -oh "[a-z]*_[0-9a-zA-Z_]*" app/src/main/java/**/data/repository/*RepositoryImpl.kt | sort -u

# 20. 🚨 Check for ID format inconsistencies
grep -rn "id = \"[a-z]*_[0-9]" app/src/main/java/**/data/repository/ | head -20
```

---

## 🤖 Advanced Mock Data Prediction System

### The Zero-Null Policy

**CRITICAL RULE: Repository stub methods should NEVER return null or empty data.**

When implementing Repository stubs, assume the app is being used by an active user with existing data. An empty app provides no value for UX testing.

### Auto-Detection: Screen Type → Required Data

Before implementing any screen, identify its type and predict required data:

| Screen Type | Detection Pattern | Required Mock Data |
|-------------|-------------------|-------------------|
| **List Screen** | `LazyColumn`, `items()`, `forEach` | List with 5-10 items, varied data |
| **Detail Screen** | `getById()`, `Single item display` | Complete entity with all fields |
| **Chart/Report** | `Canvas`, `Chart`, progress bars | 7+ data points with realistic variance |
| **Form Screen** | `TextField`, `Button("Submit")` | Pre-filled sample values |
| **Dashboard** | Multiple `Card`, summary stats | All metric cards populated |
| **Empty State** | `if (list.isEmpty())` | NEVER trigger - always have data |

### Prediction Matrix: Return Type → Mock Strategy

```kotlin
// 🎯 PREDICTION MATRIX
// When implementing Repository methods, predict what mock data is needed:

// Result<T?> where T is single entity → Return non-null mock
override suspend fun getLatestReport(userId: String): Result<Report?> {
    return Result.success(createMockReport())  // ✅ Never null
}

// Result<List<T>> → Return list with 5-10 items
override suspend fun getHistory(userId: String): Result<List<Record>> {
    return Result.success((1..7).map { createMockRecord(it) })  // ✅ Never empty
}

// Result<Map<K,V>> → Return map with realistic entries
override suspend fun getStats(): Result<Map<String, Int>> {
    return Result.success(mapOf("score" to 85, "streak" to 7))  // ✅ Never empty
}

// Flow<T?> → Emit non-null initial value
override fun observeStatus(): Flow<Status?> {
    return flowOf(Status.Active)  // ✅ Never emit null initially
}
```

### Domain-Aware Mock Generation

Generate mock data that makes sense for your specific domain (defined by Spec):

```kotlin
// ❌ Generic - doesn't help UX testing
score = 50
items = emptyList()

// ✅ Domain-aware - realistic for your app's domain
// Consult Spec for realistic value ranges and data formats
score = 85  // Within expected range for domain
items = listOf(item1, item2, item3)  // Non-empty with variation
```

**Principle:** Mock data should simulate a real user experience, not just compile successfully.

### Pre-Flight Automated Checks

Run these before testing to catch empty UI issues:

```bash
# 21. 🚨 ZERO-NULL CHECK: Find all Repository methods returning null
grep -rn "return Result.success(null)" app/src/main/java/**/data/repository/
# If ANY results → FIX immediately

# 22. 🚨 EMPTY-LIST CHECK: Find all Repository methods returning empty
grep -rn "return Result.success(emptyList\|return Result.success(listOf()" app/src/main/java/**/data/repository/
# If ANY results → FIX immediately

# 23. 🚨 FLOW-NULL CHECK: Find Flows emitting null
grep -rn "flowOf(null)\|MutableStateFlow(null)" app/src/main/java/**/data/repository/
# If ANY results → Review if this causes empty UI

# 24. 🚨 TODO-RETURN CHECK: Find TODO comments with placeholder returns
grep -rn "// TODO" -A1 app/src/main/java/**/data/repository/ | grep "return"
# Review all - likely candidates for empty data

# 25. 🤖 AUTO-PREDICT: List all Repository interface methods
echo "=== Repository Methods Needing Mock Data ===" && \
grep -rh "suspend fun\|fun " app/src/main/java/**/domain/repository/*.kt | \
grep -E "Result<|Flow<" | \
grep -oE "[a-zA-Z]+\([^)]*\).*Result<[^>]+>|[a-zA-Z]+\([^)]*\).*Flow<[^>]+>"
```

### Mock Data Completeness Checklist

Before marking a Repository stub as "done", verify:

- [ ] All `Result<T?>` methods return non-null mock data
- [ ] All `Result<List<T>>` methods return 5+ items with varied data
- [ ] All chart-related data has 7+ data points
- [ ] Mock IDs are consistent across repositories
- [ ] Mock data is domain-appropriate (not generic "test" values)
- [ ] Date/time values are realistic (not epoch 0 or far future)
- [ ] Numeric values are within realistic domain ranges

---

## 🎨 Universal UI/UX Production Standards

#### Animation Requirements (Apply to ALL Apps)

```kotlin
// ✅ REQUIRED: Screen transitions
navController.navigate(route) {
    // Fade + slide animation
    enterTransition = fadeIn() + slideInHorizontally()
    exitTransition = fadeOut() + slideOutHorizontally()
}

// ✅ REQUIRED: List item animations
LazyColumn {
    itemsIndexed(items) { index, item ->
        AnimatedVisibility(
            enter = fadeIn() + slideInVertically(initialOffsetY = { it * (index + 1) })
        ) {
            ItemCard(item)
        }
    }
}

// ✅ REQUIRED: Loading states
// Never show blank screen - always show:
// 1. Skeleton/shimmer placeholders
// 2. Or circular progress with message

// ✅ REQUIRED: Pull-to-refresh for lists
SwipeRefresh(state = rememberSwipeRefreshState(isRefreshing)) {
    LazyColumn { ... }
}

// ✅ REQUIRED: Error states with retry
if (error != null) {
    ErrorState(
        message = error,
        onRetry = { viewModel.retry() }  // Must have retry action
    )
}
```

#### Accessibility Requirements

```kotlin
// ✅ REQUIRED: Content descriptions
Icon(
    imageVector = Icons.Default.Star,
    contentDescription = "Rating: ${rating} stars"  // Not null!
)

// ✅ REQUIRED: Touch targets
Modifier
    .size(48.dp)  // Minimum 48dp for touch targets
    .clickable { }

// ✅ REQUIRED: Semantic grouping
Row(Modifier.semantics(mergeDescendants = true) { }) {
    Icon(...)
    Text(...)  // Announced together
}
```

#### Edge Case Handling

```kotlin
// ✅ REQUIRED: Handle ALL states
when {
    isLoading -> LoadingState()       // Shimmer/skeleton
    error != null -> ErrorState()      // With retry button
    data.isEmpty() -> EmptyState()     // Friendly message + action
    else -> ContentState(data)         // Normal content
}

// ✅ REQUIRED: Empty states must have action
@Composable
fun EmptyState() {
    Column(horizontalAlignment = CenterHorizontally) {
        Image(emptyStateIllustration)
        Text("No data yet")
        Text("Data will appear here after you start using the app")
        Button(onClick = onAction) {  // MUST have action
            Text("Get Started")  // Or "Add", "Explore", etc.
        }
    }
}
```

---

### 🔍 Production Completeness Verification

```bash
# 26. 🎯 Check ALL screens have loading state
grep -rL "isLoading\|CircularProgressIndicator\|Shimmer" app/src/main/java/**/ui/screens/*.kt
# If ANY files listed → Add loading state

# 27. 🎯 Check ALL screens have error handling
grep -rL "error\|Error\|onRetry" app/src/main/java/**/ui/screens/*.kt
# If ANY files listed → Add error handling

# 28. 🎯 Check ALL lists have empty state
grep -rn "LazyColumn\|LazyRow" app/src/main/java/**/ui/screens/*.kt | while read line; do
    file=$(echo $line | cut -d: -f1)
    grep -L "isEmpty\|EmptyState\|empty" "$file"
done
# If ANY files listed → Add empty state handling

# 29. 🎯 Check ALL clickables have content description
grep -rn "clickable\|Button\|IconButton" app/src/main/java/**/ui/ | \
grep -v "contentDescription"
# Review all - should have descriptions

# 30. 🎯 Check for placeholder text/images
grep -rn "TODO\|FIXME\|placeholder\|Lorem\|Test" app/src/main/java/**/ui/
# If ANY results → Replace with production content

# 31. 🎯 Verify animation presence in key screens
grep -rL "animat\|transition\|Animat" app/src/main/java/**/ui/screens/*.kt
# Key screens should have animations
```

### Production Readiness Checklist

Before release, verify each screen has:

- [ ] **Loading State**: Shimmer/skeleton, not blank
- [ ] **Error State**: Message + retry button
- [ ] **Empty State**: Illustration + message + action button
- [ ] **Content State**: Full data display
- [ ] **Animations**: Entry, exit, state changes
- [ ] **Pull-to-refresh**: For list screens
- [ ] **Touch feedback**: Ripple on all clickables
- [ ] **Accessibility**: Content descriptions, 48dp touch targets
- [ ] **Offline support**: Cached data display, sync indicator
- [ ] **Deep linking**: Navigate directly to screen

---

### 🔍 Navigation Wiring Verification Guide

**Problem**: A Screen may define `onNavigateToSettings: () -> Unit = {}`, but if NavGraph doesn't pass a real callback, clicking does nothing.

**Detection Pattern**:
```kotlin
// ❌ UNWIRED - Screen has callback but NavGraph uses default
// Screen definition:
fun SettingsScreen(
    onNavigateToAccountInfo: () -> Unit = {},  // ← Default empty!
    onNavigateToChangePassword: () -> Unit = {}
)

// NavGraph only passes some callbacks:
SettingsScreen(
    onNavigateBack = { navController.popBackStack() }
    // Missing: onNavigateToAccountInfo, onNavigateToChangePassword!
)

// ✅ PROPERLY WIRED - NavGraph passes ALL callbacks
SettingsScreen(
    onNavigateBack = { navController.popBackStack() },
    onNavigateToAccountInfo = { navController.navigate(NavRoutes.AccountInfo.route) },
    onNavigateToChangePassword = { navController.navigate(NavRoutes.ChangePassword.route) }
)
```

**Verification Script**:
```bash
# Run this to find unwired callbacks
echo "=== Checking Navigation Wiring ===" && \
for screen in $(grep -rl "fun [A-Z][a-zA-Z]*Screen(" app/src/main/java/**/ui/screens/*.kt); do
    SCREEN_NAME=$(basename "$screen" .kt)
    echo "--- $SCREEN_NAME ---"
    echo "Declared callbacks:"
    grep -oE "onNavigateTo[A-Za-z]+" "$screen" | sort -u
    echo "Wired in NavGraph:"
    grep -A 20 "${SCREEN_NAME}(" app/src/main/java/**/nav/*NavGraph.kt 2>/dev/null | grep -oE "onNavigateTo[A-Za-z]+" | sort -u
    echo ""
done
```

### 🔍 Service→Repository Wiring Verification Guide

**Problem**: A Service may call `repository.getAccountInfo()`, but if the Repository interface doesn't have this method or RepositoryImpl doesn't implement it, the app crashes at runtime.

**Detection Pattern**:
```kotlin
// ❌ UNWIRED - Service calls method that doesn't exist in Repository
// Service:
class SettingsService(private val repository: SettingsRepository) {
    suspend fun getAccountInfo() = repository.getAccountInfo()  // ← Method doesn't exist!
}

// Repository interface:
interface SettingsRepository {
    suspend fun getSettings(): Settings  // Missing getAccountInfo()!
}

// ✅ PROPERLY WIRED - All methods exist and are implemented
// Service:
class SettingsService(private val repository: SettingsRepository) {
    suspend fun getAccountInfo() = repository.getAccountInfo()  // ✅ Exists
}

// Repository interface:
interface SettingsRepository {
    suspend fun getSettings(): Settings
    suspend fun getAccountInfo(): AccountInfo  // ✅ Declared
}

// Repository implementation:
class SettingsRepositoryImpl : SettingsRepository {
    override suspend fun getSettings() = ...  // ✅ Implemented
    override suspend fun getAccountInfo() = ...  // ✅ Implemented
}
```

**Verification Script**:
```bash
# Run this to find unwired Service→Repository calls
echo "=== Checking Service→Repository Wiring ===" && \
for service in $(find app/src/main/java -name "*Service.kt" -path "*/domain/service/*"); do
    SERVICE_NAME=$(basename "$service" .kt)
    echo "--- $SERVICE_NAME ---"
    echo "Repository methods called:"
    grep -oE "repository\.[a-zA-Z]+\(" "$service" | sed 's/repository\.//' | sed 's/($//' | sort -u
done
```

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested Gradle settings and library versions. **NEVER reconfigure project structure or modify build.gradle / libs.versions.toml**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-android.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-android template"
```

**Step 3**: Modify project name and package
Only modify the following required items:
- `rootProject.name` in `settings.gradle.kts`
- `namespace` and `applicationId` in `app/build.gradle.kts`
- Rename package directory structure under `app/src/main/java/`
- Update package-related settings in `AndroidManifest.xml`

⚠️ Renaming the package touches every `import` statement, `AndroidManifest.xml`, and the Hilt DI modules — do it via IDE refactor (Android Studio: Refactor > Rename on the package), NOT with `sed`/text replacement.

**Step 4**: Clean up example code
The cloned project contains example UI (e.g., Arcana User Management). Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `core/` - Common utilities (analytics, common, cache)
- `di/` - Hilt DI modules
- `sync/` - Sync management
- `data/local/AppDatabase.kt` - Room database base configuration
- `data/repository/` - Repository base classes
- `MainActivity.kt` - Entry Activity
- `MyApplication.kt` - Application class
- `nav/NavGraph.kt` - Navigation configuration (modify routes)

**Example files to REPLACE**:
- `ui/screens/` - Delete all example screens, create new project UI
- `ui/theme/` - Modify Theme colors and styles
- `data/model/` - Delete example Models, create new Domain Models
- `data/local/dao/` - Delete example DAO, create new DAO
- `data/local/entity/` - Delete example Entity, create new Entity
- `data/network/` - Modify API endpoints
- `domain/` - Delete example Service, create new business logic

**Step 5**: Verify build
```bash
./gradlew clean build
```

### ❌ Prohibited Actions
- **DO NOT** create new build.gradle.kts from scratch
- **DO NOT** modify version numbers in `gradle/libs.versions.toml`
- **DO NOT** add or remove dependencies (unless explicitly required)
- **DO NOT** modify Gradle wrapper version
- **DO NOT** reconfigure Compose, Hilt, Room, or other library settings

### ✅ Allowed Modifications
- Add business-related Kotlin code (following existing architecture)
- Add UI screens (using existing Compose settings)
- Add Domain Models, Repository, ViewModel
- Modify strings.xml, colors.xml, and other resource files
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

```kotlin
// ❌ WRONG - Test exists but no implementation
// Test file exists: LoginViewModelTest.kt (32 tests)
// Production file: LoginViewModel.kt → MISSING or PLACEHOLDER
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: LoginViewModelTest.kt (32 tests)
// Production file: LoginViewModel.kt (fully implemented)
// All 32 tests PASS
```

#### Implementation Completion Checklist

Before marking ANY module complete, verify:
```bash
# Count test files vs implementation files (MUST match)
echo "=== TDD Completion Check ===" && \
TEST_COUNT=$(find app/src/test -name "*Test.kt" | wc -l) && \
IMPL_COUNT=$(find app/src/main -name "*.kt" | grep -E "(ViewModel|Repository|Service|Screen)" | wc -l) && \
echo "Test files: $TEST_COUNT" && \
echo "Implementation files: $IMPL_COUNT" && \
echo "If test count > impl count, you have INCOMPLETE TDD!"
```

**Completion Criteria:**
| Criteria | Required |
|----------|----------|
| Test file exists | ✅ |
| Implementation file exists | ✅ |
| All tests pass | ✅ |
| No PlaceholderScreen in NavGraph | ✅ |
| No "即將推出" / "Coming Soon" text | ✅ |
| No NotImplementedError | ✅ |
| No empty onClick handlers | ✅ |

#### ⛔ PlaceholderScreen Policy

PlaceholderScreen is **ONLY** allowed as a temporary navigation target during active development. It is **FORBIDDEN** as a final state.

```kotlin
// ❌ WRONG - PlaceholderScreen left in production
composable(NavRoutes.Feature.route) {
    PlaceholderScreen(title = "Feature") // FORBIDDEN!
}

// ✅ CORRECT - Real screen implementation
composable(NavRoutes.Feature.route) {
    FeatureScreen(
        viewModel = hiltViewModel(),
        onNavigateBack = { navController.popBackStack() }
    )
}
```

**PlaceholderScreen Cleanup Check:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderScreen\|即將推出\|Coming Soon" app/src/main/java/
```

#### Step 1: Analyze Spec Documents
Before writing any code, extract ALL requirements from specification documents:
```kotlin
/**
 * Requirements extracted from specification documents:
 *
 * Functional Requirements:
 * - REQ-001: User must be able to login with email/password
 * - REQ-002: App must show splash screen for 2 seconds
 * - REQ-003: Dashboard must display user progress data
 *
 * Technical Requirements:
 * - TECH-001: Use Hilt for dependency injection
 * - TECH-002: Implement MVVM Input/Output pattern
 * - TECH-003: Store tokens in encrypted SharedPreferences
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```kotlin
// test/java/.../ui/screens/auth/LoginViewModelTest.kt
@HiltAndroidTest
class LoginViewModelTest {

    @get:Rule
    val hiltRule = HiltAndroidRule(this)

    private lateinit var viewModel: LoginViewModel
    private lateinit var mockAuthRepository: AuthRepository

    @Before
    fun setup() {
        mockAuthRepository = mockk()
        viewModel = LoginViewModel(mockAuthRepository)
    }

    // REQ-001: User must be able to login with email/password
    @Test
    fun `login with valid credentials should succeed`() = runTest {
        // Given
        coEvery { mockAuthRepository.login("test@test.com", "password123") } returns Result.success(Unit)

        // When
        viewModel.onInput(LoginViewModel.Input.UpdateEmail("test@test.com"))
        viewModel.onInput(LoginViewModel.Input.UpdatePassword("password123"))
        viewModel.onInput(LoginViewModel.Input.Submit)

        // Then
        assertTrue(viewModel.output.value.isLoginSuccess)
    }

    // REQ-001: Invalid credentials should show error
    @Test
    fun `login with invalid credentials should show error`() = runTest {
        // Given
        coEvery { mockAuthRepository.login(any(), any()) } returns Result.failure(Exception("Invalid credentials"))

        // When
        viewModel.onInput(LoginViewModel.Input.Submit)

        // Then
        assertNotNull(viewModel.output.value.loginError)
    }
}
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL requirements have tests:
```kotlin
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * Functional Requirements:
 * [x] REQ-001: Login with email/password - LoginViewModelTest
 * [x] REQ-002: Splash screen display - SplashScreenTest
 * [x] REQ-003: Register new account - RegisterViewModelTest
 * [x] REQ-010: Display user progress - DashboardViewModelTest
 * [x] REQ-011: Display rewards - DashboardViewModelTest
 * [ ] REQ-020: List items - TODO
 *
 * Technical Requirements:
 * [x] TECH-001: Hilt DI configuration - AppModuleTest
 * [x] TECH-002: MVVM Input/Output pattern - ViewModelTest
 * [x] TECH-003: Encrypted token storage - AuthRepositoryTest
 * [ ] TECH-004: Offline-first caching - TODO
 */
```

#### Step 4: Mock API Implementation - MANDATORY

⚠️ **CRITICAL**: Every Repository method MUST return valid mock data. NEVER leave methods returning `NotImplementedError` or `TODO`.

**Rules for Mock Repositories:**
1. ALL repository methods must return `Result.success(...)` with realistic mock data
2. Use `delay()` to simulate network latency (500-1000ms)
3. Mock data must match the domain model structure exactly
4. Check enum values exist before using them (e.g., `TrendDirection.IMPROVING` not `TrendDirection.UP`)
5. Include all required constructor parameters for data classes

For APIs not yet available from Cloud team, implement mock repositories:
```kotlin
// data/repository/mock/MockAuthRepository.kt
class MockAuthRepository @Inject constructor(
    private val sharedPreferences: SharedPreferences
) : AuthRepository {

    companion object {
        // Mock user data for testing
        private val MOCK_USERS = listOf(
            MockUser("test@test.com", "password123", "Test User"),
            MockUser("demo@demo.com", "demo123", "Demo User")
        )
    }

    override suspend fun login(email: String, password: String): Result<Unit> {
        // Simulate network delay
        delay(1000)

        val user = MOCK_USERS.find { it.email == email && it.password == password }
        return if (user != null) {
            // Save mock token
            sharedPreferences.edit()
                .putString("access_token", "mock_token_${System.currentTimeMillis()}")
                .putString("user_name", user.name)
                .apply()
            Result.success(Unit)
        } else {
            Result.failure(Exception("Invalid email or password"))
        }
    }

    override suspend fun isLoggedIn(): Boolean {
        return sharedPreferences.getString("access_token", null) != null
    }
}

// di/RepositoryModule.kt - Switch between Mock and Real
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        // Use MockAuthRepository until Cloud API is ready
        // impl: AuthRepositoryImpl  // Production
        impl: MockAuthRepository     // Development/Testing
    ): AuthRepository
}
```

#### Step 5: UI Completeness Check - MANDATORY

⚠️ **CRITICAL**: Before completing any screen, verify ALL interactive elements work.

**UI Checklist for Each Screen:**
```kotlin
/**
 * UI Completeness Checklist - [ScreenName]
 *
 * Click Handlers:
 * [x] All Button onClick handlers implemented (not empty {})
 * [x] All IconButton onClick handlers implemented
 * [x] All Card onClick handlers implemented (if clickable)
 * [x] All TextButton onClick handlers implemented
 * [x] All navigation callbacks wired in NavGraph
 *
 * ViewModel Connection:
 * [x] Screen uses hiltViewModel() or receives ViewModel
 * [x] UI state collected with collectAsStateWithLifecycle()
 * [x] All UI elements bound to ViewModel state (no hardcoded values)
 * [x] Loading/Error states handled
 *
 * Navigation:
 * [x] All navigation callbacks added to Screen parameters
 * [x] NavGraph passes all required callbacks
 * [x] NavRoutes defined for all destinations
 * [x] All NavRoutes have corresponding composable() in NavGraph
 */
```

#### Step 5.1: Navigation Graph Verification - MANDATORY

⚠️ **CRITICAL**: Every route in NavRoutes MUST have a corresponding `composable()` destination in the NavGraph. Missing routes cause runtime crashes.

**Quick Check Commands:**
```bash
# 1. List all routes defined in NavRoutes
grep -E "data object|NavRoutes\(" app/src/main/java/**/nav/NavRoutes.kt

# 2. List all composable destinations in NavGraph
grep -E "composable\(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt

# 3. List all navController.navigate calls
grep -rn "navController.navigate\(NavRoutes\." app/src/main/java/**/nav/
```

**Verification Checklist:**
```kotlin
/**
 * Navigation Completeness Checklist
 *
 * For each route in NavRoutes.kt, verify:
 * [x] Route has composable() destination in NavGraph
 * [x] If route has arguments, composable() includes navArgument()
 * [x] composable() has proper screen or placeholder
 *
 * Example verification:
 * NavRoutes.kt                    NavGraph.kt
 * ─────────────────────────────────────────────────────
 * ScreenA("screen_a")         →  composable(NavRoutes.ScreenA.route) { ... }
 * ScreenB("screen_b")         →  composable(NavRoutes.ScreenB.route) { ... }
 * Detail("detail/{id}")       →  composable(NavRoutes.Detail.route, arguments=[...]) { ... }
 */
```

**Common Navigation Errors:**
```kotlin
// ❌ WRONG - Route defined but no composable destination
// NavRoutes.kt
data object ScreenA : NavRoutes("screen_a")

// NavGraph.kt - MISSING composable for ScreenA!
// This will crash: "Navigation destination that matches route screen_a cannot be found"

// ✅ CORRECT - Every route has a composable destination
// NavRoutes.kt
data object ScreenA : NavRoutes("screen_a")

// NavGraph.kt
composable(NavRoutes.ScreenA.route) {
    ScreenAScreen(
        onNavigateBack = { navController.popBackStack() }
    )
}

// Or use placeholder if screen not yet implemented:
composable(NavRoutes.ScreenA.route) {
    PlaceholderScreen(
        title = "Screen A",
        onNavigateBack = { navController.popBackStack() }
    )
}
```

**Placeholder Screen Template:**
```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PlaceholderScreen(
    title: String,
    onNavigateBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(title) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentAlignment = Alignment.Center
        ) {
            Text("Coming Soon", style = MaterialTheme.typography.bodyLarge)
        }
    }
}
```

**Common Empty Handler Patterns to Avoid:**
```kotlin
// ❌ WRONG - Empty handlers
onClick = { }
onClick = { /* TODO */ }
onClick = { /* TODO: Navigate */ }

// ✅ CORRECT - Implemented handlers
onClick = onNavigateToSettings
onClick = { viewModel.performAction() }
onClick = { navController.navigate(NavRoutes.Settings.route) }
```

#### Step 6: Run All Tests Before Completion
```bash
# Run all unit tests
./gradlew test

# Run all instrumented tests
./gradlew connectedAndroidTest

# Generate test coverage report
./gradlew jacocoTestReport

# Verify all tests pass
./gradlew check
```

#### Step 7: Final Verification - MANDATORY

⚠️ **CRITICAL**: Before marking any feature complete, perform these checks:

```bash
# 1. Verify build compiles
./gradlew :app:compileDebugKotlin

# 2. Check for NotImplementedError in repositories
grep -r "NotImplementedError\|TODO.*implement" app/src/main/java/**/repository/

# 3. Check for empty onClick handlers
grep -r "onClick\s*=\s*{\s*}" app/src/main/java/**/ui/

# 4. Verify all screens use ViewModel (not hardcoded data)
grep -r "hiltViewModel()" app/src/main/java/**/ui/screens/

# 5. Verify navigation completeness (counts MUST match)
echo "=== Navigation Verification ===" && \
ROUTES=$(grep -c "data object" app/src/main/java/**/nav/NavRoutes.kt 2>/dev/null || echo 0) && \
COMPOSABLES=$(grep -c "composable(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt 2>/dev/null || echo 0) && \
echo "Routes defined: $ROUTES" && \
echo "Composables registered: $COMPOSABLES" && \
if [ "$ROUTES" -ne "$COMPOSABLES" ]; then echo "❌ MISMATCH! Missing $(($ROUTES - $COMPOSABLES)) composable destinations"; else echo "✅ All routes have destinations"; fi
```

**Final Checklist:**
- [ ] Build compiles without errors
- [ ] No `NotImplementedError` in any repository
- [ ] No empty `onClick = { }` handlers
- [ ] All screens connected to ViewModels
- [ ] All repository methods return mock data
- [ ] **All NavRoutes have corresponding composable() destinations**
- [ ] App launches and displays data correctly
- [ ] All clickable elements navigate without crashes
- [ ] **🚨 No PlaceholderScreen in production code**
- [ ] **🚨 No "即將推出" / "Coming Soon" text**
- [ ] **🚨 All test files have corresponding implementations**
- [ ] **🚨 All tests PASS (not just written)**
- [ ] **🚨 All Screen navigation callbacks wired in NavGraph** (no `onNavigate*: () -> Unit = {}` left unwired)
- [ ] **🚨 Screen callbacks count = NavGraph wired callbacks count** (per Screen)

#### 🚨 100% Implementation Verification - MANDATORY

Before completing ANY task, run this comprehensive check:

```bash
# === FULL TDD COMPLETION CHECK ===

echo "=== 1. PlaceholderScreen Check (MUST be empty) ===" && \
grep -rn "PlaceholderScreen\|即將推出\|Coming Soon" app/src/main/java/ || echo "✅ No placeholders found"

echo "" && echo "=== 2. NotImplementedError Check (MUST be empty) ===" && \
grep -rn "NotImplementedError\|TODO.*implement\|throw.*NotImplemented" app/src/main/java/ || echo "✅ No NotImplementedError found"

echo "" && echo "=== 3. Empty Handler Check (MUST be empty) ===" && \
grep -rn "onClick\s*=\s*{\s*}\|onClick\s*=\s*{.*TODO" app/src/main/java/ || echo "✅ No empty handlers found"

echo "" && echo "=== 4. Test vs Implementation Parity ===" && \
echo "Test ViewModels:" && find app/src/test -name "*ViewModelTest.kt" 2>/dev/null | wc -l && \
echo "Impl ViewModels:" && find app/src/main -name "*ViewModel.kt" 2>/dev/null | wc -l && \
echo "(Counts should be equal or impl > test)"

echo "" && echo "=== 5. Build Verification ===" && \
./gradlew :app:compileDebugKotlin --quiet && echo "✅ Build successful" || echo "❌ Build failed"

echo "" && echo "=== 6. Run All Tests ===" && \
./gradlew test --quiet && echo "✅ All tests passed" || echo "❌ Tests failed"

echo "" && echo "=== 7. 🚨 Navigation Wiring Check (CRITICAL!) ===" && \
echo "Screen navigation callbacks:" && \
SCREEN_CALLBACKS=$(grep -roh "onNavigateTo[A-Za-z]*:" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | grep -oE "onNavigateTo[A-Za-z]+" | sort -u | wc -l) && \
echo "  Declared: $SCREEN_CALLBACKS" && \
WIRED_CALLBACKS=$(grep -roh "onNavigateTo[A-Za-z]*\s*=" app/src/main/java/**/nav/*NavGraph.kt 2>/dev/null | grep -oE "onNavigateTo[A-Za-z]+" | sort -u | wc -l) && \
echo "  Wired: $WIRED_CALLBACKS" && \
if [ "$SCREEN_CALLBACKS" -ne "$WIRED_CALLBACKS" ]; then \
    echo "❌ MISMATCH! $(($SCREEN_CALLBACKS - $WIRED_CALLBACKS)) callbacks not wired in NavGraph"; \
    echo "Unwired callbacks:"; \
    comm -23 <(grep -roh "onNavigateTo[A-Za-z]*:" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | grep -oE "onNavigateTo[A-Za-z]+" | sort -u) \
             <(grep -roh "onNavigateTo[A-Za-z]*\s*=" app/src/main/java/**/nav/*NavGraph.kt 2>/dev/null | grep -oE "onNavigateTo[A-Za-z]+" | sort -u); \
else \
    echo "✅ All navigation callbacks properly wired"; \
fi
```

**❌ Task is NOT complete if ANY of these checks fail:**
1. PlaceholderScreen found in code
2. "即將推出" or "Coming Soon" text found
3. NotImplementedError found
4. Empty onClick handlers found
5. Test count > Implementation count
6. Build fails
7. Tests fail
8. **Navigation callbacks declared > callbacks wired in NavGraph** (clicking does nothing!)

#### Test Directory Structure
```
app/src/
├── main/java/...                    # Production code
├── test/java/...                    # Unit tests
│   ├── ui/screens/
│   │   ├── auth/
│   │   │   ├── LoginViewModelTest.kt
│   │   │   └── RegisterViewModelTest.kt
│   │   ├── dashboard/
│   │   │   └── DashboardViewModelTest.kt
│   │   └── splash/
│   │       └── SplashViewModelTest.kt
│   ├── domain/
│   │   └── service/
│   │       └── UserServiceTest.kt
│   └── data/
│       └── repository/
│           └── AuthRepositoryTest.kt
└── androidTest/java/...             # Instrumented tests
    └── ui/screens/
        ├── LoginScreenTest.kt
        └── DashboardScreenTest.kt
```

### 2. Project Structure
```
app/
├── presentation/          # UI Layer
│   ├── ui/               # Compose Composables
│   ├── viewmodel/        # Input/Output ViewModel
│   └── navigation/       # Navigation Logic
├── domain/               # Domain Layer
│   ├── model/            # Domain Models
│   ├── service/          # Business Services
│   └── repository/       # Repository Interfaces
└── data/                 # Data Layer
    ├── repository/       # Repository Implementations
    ├── local/            # Room Database
    │   ├── entity/       # Database Entities
    │   └── dao/          # Data Access Objects
    └── remote/           # API Client
        ├── api/          # API Interfaces
        └── dto/          # Data Transfer Objects
```

### 2. ViewModel Input/Output Pattern

```kotlin
class UserViewModel @Inject constructor(
    private val userService: UserService
) : ViewModel() {

    // Input: Sealed interface defining all events
    sealed interface Input {
        data class UpdateName(val name: String) : Input
        data class UpdateEmail(val email: String) : Input
        data object Submit : Input
    }

    // Output: State container
    data class Output(
        val name: String = "",
        val email: String = "",
        val isLoading: Boolean = false,
        val error: String? = null
    )

    private val _output = MutableStateFlow(Output())
    val output: StateFlow<Output> = _output.asStateFlow()

    // Effect flow (one-time events)
    private val _effect = Channel<Effect>()
    val effect = _effect.receiveAsFlow()

    sealed interface Effect {
        data object NavigateBack : Effect
        data class ShowSnackbar(val message: String) : Effect
    }

    fun onInput(input: Input) {
        when (input) {
            is Input.UpdateName -> updateName(input.name)
            is Input.UpdateEmail -> updateEmail(input.email)
            is Input.Submit -> submit()
        }
    }
}
```

### 3. Offline-First Strategy

```kotlin
class UserRepository @Inject constructor(
    private val userDao: UserDao,
    private val userApi: UserApi,
    private val syncManager: SyncManager
) : IUserRepository {

    // Room as single source of truth
    override fun getUsers(): Flow<List<User>> = userDao.getAllUsers()
        .map { entities -> entities.map { it.toDomain() } }

    // Local-first updates
    override suspend fun updateUser(user: User): Result<Unit> {
        // 1. Immediately update local database
        userDao.update(user.toEntity().copy(syncStatus = SyncStatus.PENDING))

        // 2. Schedule background sync
        syncManager.scheduleSyncWork()

        return Result.success(Unit)
    }

    // Background sync processing
    suspend fun syncPendingChanges() {
        val pendingUsers = userDao.getPendingSync()
        pendingUsers.forEach { entity ->
            try {
                userApi.updateUser(entity.toDto())
                userDao.update(entity.copy(syncStatus = SyncStatus.SYNCED))
            } catch (e: Exception) {
                // Keep pending status for retry
            }
        }
    }
}
```

### 4. Three-Layer Cache Strategy

```kotlin
class CacheManager<K, V>(
    private val maxMemorySize: Int = 100,
    private val ttlMillis: Long = 5 * 60 * 1000 // 5 minutes
) {
    // L1: Memory cache (<1ms)
    private val memoryCache = LruCache<K, CacheEntry<V>>(maxMemorySize)

    // L2: LRU + TTL cache
    private val lruCache = LinkedHashMap<K, CacheEntry<V>>(16, 0.75f, true)

    // L3: Room persistence (via Repository)

    data class CacheEntry<V>(
        val value: V,
        val timestamp: Long = System.currentTimeMillis()
    ) {
        fun isExpired(ttl: Long) = System.currentTimeMillis() - timestamp > ttl
    }

    suspend fun get(key: K, loader: suspend () -> V): V {
        // Check L1
        memoryCache.get(key)?.takeIf { !it.isExpired(ttlMillis) }?.let {
            return it.value
        }

        // Check L2
        lruCache[key]?.takeIf { !it.isExpired(ttlMillis) }?.let {
            memoryCache.put(key, it)
            return it.value
        }

        // Load from data source
        val value = loader()
        val entry = CacheEntry(value)
        memoryCache.put(key, entry)
        lruCache[key] = entry
        return value
    }
}
```

### 5. Compose UI Best Practices

```kotlin
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    // Handle one-time effects
    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is UserViewModel.Effect.NavigateBack -> navController.popBackStack()
                is UserViewModel.Effect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    UserContent(
        output = output,
        onInput = viewModel::onInput
    )
}

// Stateless composable for easy testing
@Composable
private fun UserContent(
    output: UserViewModel.Output,
    onInput: (UserViewModel.Input) -> Unit
) {
    Column {
        OutlinedTextField(
            value = output.name,
            onValueChange = { onInput(UserViewModel.Input.UpdateName(it)) },
            label = { Text("Name") }
        )
        // ...
    }
}
```

### 6. Hilt Dependency Injection

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DataModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideUserDao(database: AppDatabase): UserDao = database.userDao()

    @Provides
    @Singleton
    fun provideHttpClient(): HttpClient = HttpClient(OkHttp) {
        install(ContentNegotiation) { json() }
        install(Logging) { level = LogLevel.BODY }
    }
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindUserRepository(impl: UserRepository): IUserRepository
}
```

### 7. Form Validation

```kotlin
// Use derivedStateOf for efficient validation state calculation
class FormState {
    var email by mutableStateOf("")
    var emailTouched by mutableStateOf(false)

    val emailError by derivedStateOf {
        when {
            !emailTouched -> null
            email.isBlank() -> "Email is required"
            !email.isValidEmail() -> "Invalid email format"
            else -> null
        }
    }

    val isValid by derivedStateOf {
        email.isNotBlank() && email.isValidEmail()
    }
}

fun String.isValidEmail(): Boolean =
    android.util.Patterns.EMAIL_ADDRESS.matcher(this).matches()
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output pattern
- [ ] Repository implements offline-first
- [ ] Compose functions have no side effects
- [ ] Properly handle Coroutine lifecycle
- [ ] Hilt modules configured correctly
- [ ] 🚨 ALL Screen navigation callbacks are wired in NavGraph
- [ ] 🚨 ALL Service→Repository method calls exist in Repository interface
- [ ] 🚨 ALL Repository interface methods have RepositoryImpl implementations

### Performance Checks
- [ ] Avoid unnecessary Compose recomposition
- [ ] Use remember and derivedStateOf
- [ ] Images use Coil with caching
- [ ] Lists use LazyColumn + key

### Security Checks
- [ ] Sensitive data not stored in plain text
- [ ] API keys not hardcoded
- [ ] Input validation complete
- [ ] Network requests use HTTPS

## Common Issues

### Gradle Build Issues
1. Check `gradle/libs.versions.toml` for version conflicts
2. Run `./gradlew --refresh-dependencies`
3. Clear cache with `./gradlew clean`

### Compose Preview Failures
1. Ensure `@Preview` functions have no required parameters or have default values
2. Check Hilt ViewModel uses `@HiltViewModel`
3. Use mock data in Preview instead of real ViewModel

### Room Migration Issues
1. Define Migration objects
2. Consider `fallbackToDestructiveMigration()` during development
3. Test migration paths

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Kotlin | 2.x (K2) |
| Compose BOM | see `gradle/libs.versions.toml` in the reference repo for current versions |
| Hilt | 2.50+ |
| Room | 2.6+ |
| Ktor | 2.3+ |
| Coroutines | 1.8+ |

---

## 🔮 Spec Gap Prediction System (Universal)

### Overview

When Spec is incomplete, use these **universal UI/UX rules** to predict missing elements. This is NOT about adding domain-specific features, but ensuring **logical completeness** of what's already defined.

```
┌─────────────────────────────────────────────────────────────────┐
│                   Spec Gap Prediction System                     │
├─────────────────────────────────────────────────────────────────┤
│  Input: Existing Spec (screens, features, data models)          │
│                                                                  │
│  Output: Predicted gaps based on universal UI/UX patterns       │
│                                                                  │
│  Principle: If Spec defines A, universally A requires B         │
└─────────────────────────────────────────────────────────────────┘
```

### Screen Type → Required States (Universal)

When Spec defines a screen type, these states are **universally required**:

| Screen Type | Required States | Prediction Rule |
|-------------|-----------------|-----------------|
| **List Screen** | Loading, Empty, Error, Data, Pull-to-refresh | Lists must have empty state |
| **Detail Screen** | Loading, Error, Data, Not Found | Details must have loading state |
| **Form Screen** | Input, Validation, Submitting, Success, Error | Forms must have validation |
| **Dashboard** | Loading skeleton, Partial data, Full data | Dashboards must have skeleton |
| **Settings** | Current values, Save confirmation | Settings must have confirmation |

```kotlin
/**
 * Screen State Prediction
 *
 * If Spec defines: "User List Screen"
 * Automatically predict these are needed:
 * - [ ] Loading state (shimmer/skeleton)
 * - [ ] Empty state ("尚無資料" + guidance)
 * - [ ] Error state (retry button)
 * - [ ] Pull-to-refresh
 * - [ ] Item click → Detail navigation
 */
```

### Flow Completion Prediction

When Spec defines a feature, predict **related flows**:

| If Spec Has | Predict Also Needed | Reasoning |
|-------------|---------------------|-----------|
| Login | Register, Forgot Password | Login requires register |
| Register | Onboarding, Email Verification | Register requires onboarding |
| List | Detail, Search, Filter | List requires detail |
| Detail | Edit (if editable), Share, Delete | Detail often has edit |
| Create | Edit, Delete, Duplicate | Create requires modify |
| Profile | Edit Profile, Logout | Profile requires logout |
| Notification List | Notification Detail, Mark Read | Notifications require read status |
| Cart | Checkout, Remove Item | Cart requires checkout |

```bash
# 🔮 Flow Completion Check
echo "=== Flow Completion Prediction ===" && \

# If Login exists, check for Register
grep -l "Login" app/src/main/java/**/nav/NavRoutes.kt && \
(grep -l "Register\|SignUp" app/src/main/java/**/nav/NavRoutes.kt || \
echo "⚠️ Login exists but Register not found - predict needed")

# If Register exists, check for Onboarding
grep -l "Register" app/src/main/java/**/nav/NavRoutes.kt && \
(grep -l "Onboarding" app/src/main/java/**/nav/NavRoutes.kt || \
echo "⚠️ Register exists but Onboarding not found - predict needed")

# If List exists, check for Detail
for list in $(grep -oh "[A-Z][a-z]*List" app/src/main/java/**/nav/NavRoutes.kt); do
    detail="${list%List}Detail"
    grep -q "$detail" app/src/main/java/**/nav/NavRoutes.kt || \
    echo "⚠️ $list exists but $detail not found - predict needed"
done
```

### Data Operation Prediction (CRUD)

When Spec defines data operations, predict the **complete CRUD cycle**:

| If Spec Has | Predict Also Needed |
|-------------|---------------------|
| Create only | Read, Update, Delete |
| Read only | (May be intentional - verify with Spec) |
| List + Create | Detail, Edit, Delete |
| Detail only | List (how to navigate here?) |

```kotlin
/**
 * CRUD Completeness Check
 *
 * If Repository has: createEntity()
 * Predict these are also needed:
 * - [ ] getEntity(id) / getEntities()
 * - [ ] updateEntity(entity)
 * - [ ] deleteEntity(id)
 *
 * If Repository has: getEntities()
 * Predict UI needs:
 * - [ ] List Screen
 * - [ ] Detail Screen (on item click)
 * - [ ] Empty state handling
 */
```

### Navigation Completeness Prediction

| Pattern | Prediction |
|---------|------------|
| Forward navigation exists | Back navigation required |
| Deep link target | Auth check required |
| Tab navigation | Content for ALL tabs |
| Bottom nav item | Screen for each item |
| Drawer menu item | Screen for each item |

```bash
# 🔮 Navigation Completeness Check

# Check all NavRoutes have composable destinations
echo "=== Navigation Completeness ===" && \
ROUTES=$(grep -oh "data object [A-Za-z]* :" app/src/main/java/**/nav/NavRoutes.kt | wc -l) && \
DESTINATIONS=$(grep -c "composable(NavRoutes\." app/src/main/java/**/nav/*NavGraph.kt) && \
echo "Routes defined: $ROUTES" && \
echo "Destinations implemented: $DESTINATIONS" && \
if [ "$ROUTES" -ne "$DESTINATIONS" ]; then \
    echo "⚠️ Mismatch! Some routes may be missing destinations"; \
fi

# Check BottomNav items have screens
grep -A 20 "BottomNavigation\|NavigationBar" app/src/main/java/**/ui/ | \
grep -oh "NavRoutes\.[A-Za-z]*" | sort -u
```

### UI State Prediction Matrix

For any screen, predict required UI states:

```kotlin
/**
 * Universal UI State Prediction
 *
 * For ANY data-displaying screen:
 *
 * sealed class UiState<T> {
 *     object Loading : UiState<Nothing>      // ← Always needed
 *     data class Success<T>(val data: T)     // ← Always needed
 *     data class Error(val message: String)  // ← Always needed
 *     object Empty : UiState<Nothing>        // ← If data can be empty
 * }
 *
 * For ANY form screen:
 *
 * data class FormState(
 *     val fields: Map<String, String>,       // ← Input values
 *     val errors: Map<String, String>,       // ← Validation errors
 *     val isSubmitting: Boolean,             // ← Submit in progress
 *     val isSuccess: Boolean                 // ← Submit succeeded
 * )
 */
```

### Spec Gap Detection Commands

```bash
# 🔮 RUN THIS to find Spec gaps

echo "=== 1. Missing Screen States ===" && \
# Check for screens without loading state
grep -L "Loading\|isLoading\|CircularProgress" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | \
head -5 && echo "(screens may be missing loading state)"

echo "" && echo "=== 2. Missing Empty States ===" && \
# Check for lists without empty state
grep -l "LazyColumn\|LazyRow" app/src/main/java/**/ui/screens/*.kt | \
xargs grep -L "empty\|Empty\|尚無\|暫無" 2>/dev/null | \
head -5 && echo "(lists may be missing empty state)"

echo "" && echo "=== 3. Missing Error States ===" && \
# Check for screens without error handling
grep -L "Error\|error\|錯誤\|失敗" app/src/main/java/**/ui/screens/*.kt 2>/dev/null | \
head -5 && echo "(screens may be missing error state)"

echo "" && echo "=== 4. Incomplete Navigation Flows ===" && \
# Check for orphan routes
grep "data object" app/src/main/java/**/nav/NavRoutes.kt | \
grep -oh "[A-Z][a-zA-Z]*" | while read route; do \
    grep -q "NavRoutes.$route" app/src/main/java/**/nav/*NavGraph.kt || \
    echo "⚠️ $route has no composable destination"; \
done
```

### Prediction Summary Template

When analyzing Spec, generate this checklist:

```markdown
## Spec Gap Analysis for [Feature Name]

### Defined in Spec:
- [ ] List: [ScreenName]List
- [ ] Detail: [ScreenName]Detail
- [ ] Create: Create[ScreenName]

### Predicted Gaps (based on universal patterns):

#### Screen States:
- [ ] Loading state for all screens
- [ ] Empty state for list screens
- [ ] Error state with retry for all screens
- [ ] Pull-to-refresh for list screens

#### Flow Completeness:
- [ ] [ScreenName]List → [ScreenName]Detail navigation
- [ ] Create → success → navigate to list/detail
- [ ] Edit capability if data is user-generated
- [ ] Delete with confirmation dialog

#### Navigation:
- [ ] Back navigation from all screens
- [ ] Deep link support for detail screens

### Recommended Actions:
1. Confirm with stakeholders if Edit/Delete are needed
2. Implement Loading/Empty/Error states
3. Add navigation wiring for predicted flows
```

---

## 🧠 UX Completeness Verification (Universal)

### Overview

This section provides **universal** verification commands that apply to ALL app types. Domain-specific features should be defined in the Spec, not in this SKILL.

```
┌─────────────────────────────────────────────────────────────────┐
│              UX Completeness Verification System                 │
├─────────────────────────────────────────────────────────────────┤
│  Level 1: Code Verification                                      │
│    - Compile errors, empty handlers, navigation wiring          │
│                                                                  │
│  Level 2: Visual Completeness                                    │
│    - Empty states, blank content areas, placeholder text        │
│                                                                  │
│  Level 3: User Flow Completeness                                 │
│    - Ensure all user journeys have logical endpoints            │
└─────────────────────────────────────────────────────────────────┘
```

### Quick UX Verification Commands

```bash
# 11. 🎨 Check for empty/placeholder UI content
grep -rn "尚無\|暫無\|即將\|Coming Soon\|No data\|Empty\|TODO.*UI" app/src/main/java/**/ui/

# 12. 🎨 Check for hardcoded empty lists in ViewModel Output
grep -rn "emptyList()\|listOf()" app/src/main/java/**/ui/screens/**/.*ViewModel.kt

# 13. 🎨 Check for missing image resources (placeholder icons)
grep -rn "Icons.Default\|Icons.Filled" app/src/main/java/**/ui/screens/ | grep -v "ArrowBack\|Close\|Menu"

# 14. 🎨 Check TabRow/Tabs with missing content
grep -rn -A 10 "TabRow\|Tab(" app/src/main/java/**/ui/screens/
```

### 📋 Screen-by-Screen UX Checklist

For EVERY screen, verify these items:

```kotlin
/**
 * UX Completeness Checklist Template
 *
 * Visual Content:
 * [ ] Has meaningful content (not empty/placeholder text)
 * [ ] Has appropriate graphics/icons (not just default Material icons)
 * [ ] Loading state shows skeleton or progress indicator
 * [ ] Empty state provides actionable guidance
 * [ ] Error state shows retry option
 *
 * Data Display:
 * [ ] Mock data looks realistic (not "Test 1", "Test 2")
 * [ ] Dates use proper format (not epoch timestamps)
 * [ ] Numbers have appropriate units and formatting
 * [ ] Lists have appropriate item count (3-10 items)
 *
 * Interaction:
 * [ ] All tabs have corresponding content
 * [ ] All list items are tappable (if expected)
 * [ ] Swipe gestures work (if applicable)
 * [ ] Pull-to-refresh implemented (if applicable)
 *
 * Navigation:
 * [ ] Back button works correctly
 * [ ] Deep links work (if applicable)
 * [ ] All buttons lead somewhere meaningful
 */
```

