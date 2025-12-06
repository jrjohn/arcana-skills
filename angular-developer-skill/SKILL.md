---
name: angular-developer-skill
description: Angular development guide based on Arcana Angular enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design with 4-layer caching, Angular Signals, MVVM Input/Output/Effect pattern, and enterprise security. Suitable for Angular project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Angular Developer Skill

Professional Angular development skill based on [Arcana Angular](https://github.com/jrjohn/arcana-angular) enterprise architecture.

---

## Quick Reference Card

### New Screen Checklist:
```
1. Add route → app.routes.ts (path + component)
2. Create Component with ChangeDetectionStrategy.OnPush
3. Create ViewModel (Input/Output/Effect with Signals)
4. Create template with Loading/Error/Empty states
5. Wire @Output events in parent template
6. Verify mock data returns non-empty values
```

### New Repository Checklist:
```
1. Interface → domain/repositories/xxx.repository.ts
2. Implementation → data/repositories/xxx.repository.impl.ts
3. Mock → data/repositories/mock/mock-xxx.repository.ts
4. Provider binding → core/providers/repository.providers.ts
5. Mock data (NEVER return [] or null!)
6. Verify ID consistency across repositories
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "\\[\\]\\|of\\(\\[\\]\\)" src/app/data/repositories/*.impl.ts` |
| Navigation crash | Compare `app.routes.ts` paths vs component imports |
| Button does nothing | `grep "(click)=\"\"" src/app/**/*.html` |
| Data not loading | `grep "throw.*NotImplemented\\|TODO" src/app/data/` |

---

## Rules Priority

### 🔴 CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty arrays | `grep "\\[\\]\\|of\\(\\[\\]\\)" *.impl.ts` |
| Navigation Wiring | ALL routes MUST have component imports | Count paths vs components |
| @Output Binding | ALL @Output events MUST be bound in parent | Check template bindings |
| ID Consistency | Cross-repository IDs must match | Check mock data IDs |

### 🟡 IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| UI States | Loading/Error/Empty for all screens | `grep -L "isLoading" *.component.ts` |
| Mock Data Quality | Realistic, varied values (not all same) | Review mock data arrays |
| Error Messages | User-friendly, not technical errors | Check error handling |
| OnPush Detection | All components use OnPush | Check changeDetection |

### 🟢 RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Animations | Smooth route transitions |
| Accessibility | ARIA labels for interactive elements |
| Dark Mode | Support system theme preference |
| PWA | Service worker for offline |

---

## Error Handling Pattern

### AppError - Unified Error Model

```typescript
// domain/models/app-error.ts
export type AppError =
  | { type: 'NETWORK_UNAVAILABLE' }
  | { type: 'TIMEOUT' }
  | { type: 'SERVER_ERROR'; statusCode: number }
  | { type: 'UNAUTHORIZED' }
  | { type: 'TOKEN_EXPIRED' }
  | { type: 'INVALID_CREDENTIALS' }
  | { type: 'NOT_FOUND' }
  | { type: 'VALIDATION_FAILED'; message: string }
  | { type: 'DATA_CORRUPTED' }
  | { type: 'UNKNOWN'; underlying: Error };

export function getErrorMessage(error: AppError): string {
  switch (error.type) {
    case 'NETWORK_UNAVAILABLE':
      return 'No internet connection. Please check your network.';
    case 'TIMEOUT':
      return 'Request timed out. Please try again.';
    case 'SERVER_ERROR':
      return `Server error (${error.statusCode}). Please try again later.`;
    case 'UNAUTHORIZED':
    case 'TOKEN_EXPIRED':
      return 'Session expired. Please login again.';
    case 'INVALID_CREDENTIALS':
      return 'Invalid email or password.';
    case 'NOT_FOUND':
      return 'The requested item was not found.';
    case 'VALIDATION_FAILED':
      return error.message;
    case 'DATA_CORRUPTED':
      return 'Data error. Please contact support.';
    case 'UNKNOWN':
      return 'An unexpected error occurred.';
  }
}

export function requiresReauth(error: AppError): boolean {
  return error.type === 'UNAUTHORIZED' || error.type === 'TOKEN_EXPIRED';
}
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Error Flow                                │
├─────────────────────────────────────────────────────────────────┤
│  Repository Layer:                                               │
│    - Catch HTTP errors                                           │
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
│    - Update _error signal with getErrorMessage()                 │
│    - Check requiresReauth() for auth redirect                    │
├─────────────────────────────────────────────────────────────────┤
│  Component Layer:                                                │
│    - Display error from output().error                           │
│    - Show retry button                                           │
│    - Handle auth redirect via effect                             │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling by Layer

**HTTP Interceptor:**
```typescript
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        let appError: AppError;

        if (error.status === 0) {
          appError = { type: 'NETWORK_UNAVAILABLE' };
        } else if (error.status === 401) {
          appError = { type: 'UNAUTHORIZED' };
        } else if (error.status === 404) {
          appError = { type: 'NOT_FOUND' };
        } else if (error.status >= 500) {
          appError = { type: 'SERVER_ERROR', statusCode: error.status };
        } else {
          appError = { type: 'UNKNOWN', underlying: error };
        }

        return throwError(() => appError);
      })
    );
  }
}
```

**ViewModel Layer:**
```typescript
private async loadData(): Promise<void> {
  this._isLoading.set(true);
  this._error.set(null);

  try {
    const items = await this.repository.getItems();
    this._items.set(items);
  } catch (error) {
    const appError = error as AppError;
    this._error.set(getErrorMessage(appError));
    if (requiresReauth(appError)) {
      this._effect.next({ type: 'NAVIGATE_TO_LOGIN' });
    }
  } finally {
    this._isLoading.set(false);
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
| Component | 60%+ | Template binding, user interactions |

### What to Test

**ViewModel Tests (Highest Priority):**
```typescript
describe('FeatureViewModel', () => {
  // Test each Input type
  it('should load items on LOAD input', async () => { });
  it('should set error on LOAD failure', async () => { });
  it('should emit toast on REFRESH success', async () => { });
  it('should navigate on ITEM_CLICKED', () => { });

  // Test state transitions
  it('should set isLoading true then false', async () => { });

  // Test edge cases
  it('should show empty state when no items', async () => { });
});
```

**Service Tests:**
```typescript
describe('UserService', () => {
  // Test business rules
  it('should validate email format', () => { });
  it('should calculate score correctly', () => { });
});
```

**Repository Tests:**
```typescript
describe('UserRepository', () => {
  // Test data mapping
  it('should map DTO to domain model', async () => { });

  // Test offline behavior
  it('should return cached data when offline', async () => { });
});
```

### Test Commands
```bash
# Run all tests with coverage
npm run test -- --code-coverage --watch=false --browsers=ChromeHeadless

# View coverage report
open coverage/[app-name]/index.html
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│      Components + MVVM + Input/Output/Effect        │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│   Offline-First Repository + IndexedDB + 4L Cache   │
└─────────────────────────────────────────────────────┘
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation → Domain → Data
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces

## Instructions

When handling Angular development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented services (MUST be empty)
grep -rn "throw.*NotImplemented\|TODO.*implement" src/app/

# 2. Check for empty click handlers (MUST be empty)
grep -rn "(click)=\"\"\|(click)=\"undefined\"" src/app/

# 3. Check for missing route components (compare routes vs components)
echo "Routes defined:" && grep -c "path:" src/app/app.routes.ts 2>/dev/null || echo 0
echo "Components imported:" && grep -c "component:" src/app/app.routes.ts 2>/dev/null || echo 0

# 4. Check NavGraphService has all navigation methods
grep -c "to\|navigate" src/app/core/services/nav-graph.service.ts 2>/dev/null || echo 0

# 5. Verify build compiles
npm run build

# 6. 🚨 Check for Output events with no parent binding (CRITICAL!)
echo "=== Component @Output Events ===" && \
grep -rh "@Output()" src/app/presentation/ | grep -oE "[a-zA-Z]+\s*=" | sed 's/\s*=//' | sort -u
echo "=== Bound Events in Templates ===" && \
grep -rh "([a-zA-Z]*Navigate[a-zA-Z]*)=" src/app/**/*.html 2>/dev/null | grep -oE "\([a-zA-Z]+\)" | tr -d '()' | sort -u

# 7. 🚨 Verify ALL routes have NavGraphService navigation methods
echo "=== Routes Defined ===" && \
grep -rh "path:" src/app/app.routes.ts | grep -oE "'[^']+'" | sort -u
echo "=== NavGraphService Methods ===" && \
grep -rh "to[A-Z][a-zA-Z]*\(" src/app/core/services/nav-graph.service.ts | grep -oE "to[A-Z][a-zA-Z]*" | sort -u

# 8. 🚨 Check for navigation callbacks in Components not wired in parent
grep -rn "onNavigate.*:\s*EventEmitter" src/app/presentation/

# 9. 🚨 Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "this\.[a-zA-Z]*Repository\.[a-zA-Z]*(" src/app/domain/services/*.ts | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/app/domain/repositories/*.repository.ts | grep -oE "[a-zA-Z]+\(" | sort -u

# 10. 🚨 Verify ALL Repository interface methods have implementations
echo "=== Repository Interface Methods ===" && \
grep -rh "abstract\|[a-zA-Z]*\(" src/app/domain/repositories/*.repository.ts | grep -oE "[a-zA-Z]+\(" | sort -u
echo "=== Repository Implementation Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/app/data/repositories/*.repository.impl.ts | grep -oE "[a-zA-Z]+\(" | sort -u
```

⚠️ **CRITICAL**: All routes in app.routes.ts MUST have corresponding component imports. Missing components cause runtime errors.

⚠️ **NAVIGATION WIRING CRITICAL**: Commands #6-#8 detect navigation @Output events that exist in Components but aren't bound in parent templates. A Component can declare `@Output() onNavigateToSettings = new EventEmitter()` but if the parent template doesn't bind `(onNavigateToSettings)="handler()"`, the event does nothing!

If any of these return results or counts don't match, FIX THEM before completing the task.

---

## 📊 Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty arrays for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank ng2-charts/D3 canvas)
- Line charts that skip rendering (e.g., `if (data.length < 2) return;`)
- Empty state components even when data structure exists

### Mock Data Rules

**Rule 1: Array data for charts MUST have at least 7 items**
```typescript
// ❌ BAD - Chart will be blank
getCurrentWeekSummary(): Observable<WeeklySummary> {
    return of({
        dailyReports: []  // ← Chart has no data to render!
    });
}

// ✅ GOOD - Chart has data to display
getCurrentWeekSummary(): Observable<WeeklySummary> {
    const mockDailyReports = Array.from({ length: 7 }, (_, i) =>
        this.createMockDailyReport(
            [72, 78, 85, 80, 76, 88, 82][i],
            [390, 420, 450, 410, 380, 460, 435][i]
        )
    );
    return of({ dailyReports: mockDailyReports });
}
```

**Rule 2: Use realistic, varied sample values**
```typescript
// ❌ BAD - Monotonous test data
const scores = Array(7).fill(80);

// ✅ GOOD - Realistic variation
const scores = [72, 78, 85, 80, 76, 88, 82];  // Shows trend
```

**Rule 3: Data must match interface exactly**
```bash
# Before creating mock data, ALWAYS verify the interface definition:
grep -A 20 "interface TherapyData" src/app/domain/models/*.ts
```

**Rule 4: Create helper functions for complex mock data**
```typescript
// ✅ Create reusable mock factory
private createMockDailyReport(score: number, duration: number): DailySleepReport {
    return {
        id: `mock_${Date.now()}`,
        sleepScore: score,
        sleepDuration: { totalMinutes: duration, ... },
        // ... all required fields
    };
}
```

### Quick Verification Commands for Mock Data

```bash
# 11. 🚨 Check for empty array returns in Repository stubs (MUST FIX)
grep -rn "\[\]" src/app/data/repositories/*.repository.impl.ts

# 12. 🚨 Verify chart-related data has mock values
grep -rn "dailyReports\|weeklyData\|chartData" src/app/data/repositories/ | grep -E "= \[\]|of\(\[\]\)"
```

---

### 0. Project Setup - CRITICAL

⚠️ **IMPORTANT**: This reference project has been validated with tested npm/Angular settings and library versions. **NEVER reconfigure project structure or modify package.json / angular.json**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-angular.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-angular template"
```

**Step 3**: Modify project name
Only modify the following required items:
- `name` field in `package.json`
- Project name in `angular.json`
- `<title>` in `src/index.html`
- Update related settings in environment configuration files

**Step 4**: Clean up example code
The cloned project contains example UI (e.g., Arcana User Management). Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `src/app/core/` - Common utilities (Guards, Interceptors, Services)
- `src/app/shared/` - Shared components and Pipes
- `src/app/data/local/` - IndexedDB (Dexie) base configuration
- `src/app/data/repositories/` - Repository base classes
- `src/app/app.component.ts` - App entry point
- `src/app/app.routes.ts` - Route configuration (modify routes)

**Example files to REPLACE**:
- `src/app/presentation/` - Delete all example screens, create new project Components
- `src/app/domain/models/` - Delete example Models, create new Domain Models
- `src/app/data/remote/` - Modify API endpoints
- `src/assets/` - Update resource files

**Step 5**: Install dependencies and verify build
```bash
npm install
npm run build
```

### ❌ Prohibited Actions
- **DO NOT** create new Angular project from scratch (ng new)
- **DO NOT** modify version numbers in `package.json`
- **DO NOT** add or remove npm dependencies (unless explicitly required)
- **DO NOT** modify build settings in `angular.json`
- **DO NOT** reconfigure Bootstrap, Dexie, ng-bootstrap, or other library settings

### ✅ Allowed Modifications
- Add business-related TypeScript code (following existing architecture)
- Add Components, Services, ViewModels
- Add Domain Models, Repository
- Modify resources in `src/assets/`
- Add routing modules

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

```typescript
// ❌ WRONG - Test exists but no implementation
// Test file exists: login.viewmodel.spec.ts (32 tests)
// Production file: login.viewmodel.ts → MISSING or throws NotImplementedError
// This is INCOMPLETE TDD!

// ✅ CORRECT - Test AND Implementation both exist
// Test file: login.viewmodel.spec.ts (32 tests)
// Production file: login.viewmodel.ts (fully implemented)
// All 32 tests PASS
```

#### ⛔ Placeholder Component Policy

Placeholder components are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```typescript
// ❌ WRONG - Placeholder component left in production
{ path: 'training', component: PlaceholderComponent } // FORBIDDEN!

// ✅ CORRECT - Real component implementation
{ path: 'training', component: TrainingComponent }
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderComponent\|throw.*NotImplemented\|TODO.*implement\|即將推出\|Coming Soon" src/app/
```

#### Step 1: Analyze Spec Documents (SRS & SDD)
Before writing any code, extract ALL requirements from both SRS and SDD:
```typescript
/**
 * Requirements extracted from specification documents:
 *
 * SRS (Software Requirements Specification):
 * - SRS-001: User must be able to login with email/password
 * - SRS-002: App must show splash screen for 2 seconds
 * - SRS-003: Dashboard must display user's stars and coins
 *
 * SDD (Software Design Document):
 * - SDD-001: Use Angular Signals for state management
 * - SDD-002: Implement MVVM Input/Output/Effect pattern
 * - SDD-003: Use IndexedDB (Dexie) for offline storage
 */
```

#### Step 2: Create Test Cases for Each Spec Item
```typescript
// src/app/presentation/auth/login.viewmodel.spec.ts
import { TestBed } from '@angular/core/testing';
import { LoginViewModel } from './login.viewmodel';
import { AuthRepository } from '../../domain/repositories/auth.repository';

describe('LoginViewModel', () => {
  let viewModel: LoginViewModel;
  let mockAuthRepository: jasmine.SpyObj<AuthRepository>;

  beforeEach(() => {
    mockAuthRepository = jasmine.createSpyObj('AuthRepository', ['login', 'isLoggedIn']);

    TestBed.configureTestingModule({
      providers: [
        LoginViewModel,
        { provide: AuthRepository, useValue: mockAuthRepository }
      ]
    });

    viewModel = TestBed.inject(LoginViewModel);
  });

  // SRS-001: User must be able to login with email/password
  it('should login successfully with valid credentials', async () => {
    // Given
    mockAuthRepository.login.and.returnValue(Promise.resolve());

    // When
    viewModel.onInput({ type: 'updateEmail', value: 'test@test.com' });
    viewModel.onInput({ type: 'updatePassword', value: 'password123' });
    await viewModel.onInput({ type: 'submit' });

    // Then
    expect(viewModel.output().isLoginSuccess).toBeTrue();
    expect(viewModel.output().error).toBeNull();
  });

  // SRS-001: Invalid credentials should show error
  it('should show error with invalid credentials', async () => {
    // Given
    mockAuthRepository.login.and.returnValue(Promise.reject(new Error('Invalid credentials')));

    // When
    await viewModel.onInput({ type: 'submit' });

    // Then
    expect(viewModel.output().isLoginSuccess).toBeFalse();
    expect(viewModel.output().error).toBeTruthy();
  });
});
```

#### Step 3: Spec Coverage Verification Checklist
Before implementation, verify ALL SRS and SDD items have tests:
```typescript
/**
 * Spec Coverage Checklist - [Project Name]
 *
 * SRS Requirements:
 * [x] SRS-001: Login with email/password - login.viewmodel.spec.ts
 * [x] SRS-002: Splash screen display - splash.component.spec.ts
 * [x] SRS-003: Register new account - register.viewmodel.spec.ts
 * [x] SRS-010: Display user stars - dashboard.viewmodel.spec.ts
 * [x] SRS-011: Display S-coins - dashboard.viewmodel.spec.ts
 * [ ] SRS-020: List training items - TODO
 *
 * SDD Design Requirements:
 * [x] SDD-001: Angular Signals state - viewmodel.spec.ts
 * [x] SDD-002: MVVM Input/Output/Effect - viewmodel.spec.ts
 * [x] SDD-003: IndexedDB offline storage - repository.spec.ts
 * [ ] SDD-004: 4-layer caching - TODO
 */
```

#### Step 4: Mock API Implementation - MANDATORY

⚠️ **CRITICAL**: Every Service/Repository method MUST return valid mock data. NEVER leave methods throwing `NotImplementedError`.

**Rules for Mock Services:**
1. ALL service methods must return valid mock data (Promise.resolve or Observable.of)
2. Use `setTimeout()` or `delay()` to simulate network latency (500-1000ms)
3. Mock data must match the interface structure exactly
4. Check TypeScript enums exist before using them
5. Include all required properties for interfaces

For APIs not yet available from Cloud team, implement mock services:
```typescript
// src/app/data/repositories/mock/mock-auth.repository.ts
import { Injectable } from '@angular/core';
import { AuthRepository } from '../../../domain/repositories/auth.repository';

interface MockUser {
  email: string;
  password: string;
  name: string;
}

@Injectable()
export class MockAuthRepository implements AuthRepository {

  // Mock user data for testing
  private static readonly MOCK_USERS: MockUser[] = [
    { email: 'test@test.com', password: 'password123', name: 'Test User' },
    { email: 'demo@demo.com', password: 'demo123', name: 'Demo User' }
  ];

  async login(email: string, password: string): Promise<void> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const user = MockAuthRepository.MOCK_USERS.find(
      u => u.email === email && u.password === password
    );

    if (user) {
      // Save mock token
      localStorage.setItem('access_token', `mock_token_${Date.now()}`);
      localStorage.setItem('user_name', user.name);
    } else {
      throw new Error('Invalid email or password');
    }
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('access_token');
  }
}

// src/app/core/providers/repository.providers.ts - Switch between Mock and Real
import { environment } from '../../../environments/environment';

export const repositoryProviders = [
  {
    provide: AuthRepository,
    useClass: environment.production
      ? AuthRepositoryImpl  // Production
      : MockAuthRepository  // Development/Testing
  }
];
```

#### Step 5: Run All Tests Before Completion
```bash
# Run all unit tests
npm run test

# Run tests with coverage report
npm run test -- --code-coverage

# Run tests in CI mode (single run)
npm run test -- --watch=false --browsers=ChromeHeadless

# Run e2e tests
npm run e2e

# Verify all tests pass
npm run test -- --watch=false && npm run e2e
```

#### Test Directory Structure
```
src/app/
├── presentation/
│   ├── auth/
│   │   ├── login.viewmodel.ts
│   │   ├── login.viewmodel.spec.ts      # Unit test
│   │   ├── login.component.ts
│   │   └── login.component.spec.ts      # Component test
│   └── dashboard/
│       ├── dashboard.viewmodel.spec.ts
│       └── dashboard.component.spec.ts
├── domain/
│   └── services/
│       ├── user.service.ts
│       └── user.service.spec.ts
├── data/
│   └── repositories/
│       ├── auth.repository.impl.ts
│       ├── auth.repository.spec.ts
│       └── mock/
│           └── mock-auth.repository.ts
e2e/
├── login.e2e-spec.ts
└── dashboard.e2e-spec.ts
```

### 2. Project Structure
```
src/
├── app/
│   ├── presentation/     # UI Layer
│   │   ├── components/   # Smart & Dumb Components
│   │   ├── layouts/      # Page Layouts
│   │   └── forms/        # Form Components
│   ├── domain/           # Domain Layer
│   │   ├── models/       # Domain Models
│   │   ├── services/     # Business Services
│   │   └── repositories/ # Repository Interfaces
│   └── data/             # Data Layer
│       ├── repositories/ # Repository Implementations
│       ├── local/        # IndexedDB (Dexie)
│       └── remote/       # API Client
├── assets/
└── styles/               # SCSS with Bootstrap
```

### 2. ViewModel Input/Output/Effect Pattern with Signals

```typescript
import { Injectable, signal, computed } from '@angular/core';
import { Subject } from 'rxjs';

// Input: Sealed type defining all events
export type UserInput =
  | { type: 'UPDATE_NAME'; name: string }
  | { type: 'UPDATE_EMAIL'; email: string }
  | { type: 'SUBMIT' };

// Output: State container
export interface UserOutput {
  name: string;
  email: string;
  isLoading: boolean;
  error: string | null;
}

// Effect: One-time events
export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_SNACKBAR'; message: string };

@Injectable()
export class UserViewModel {
  // Output: Read-only signals
  private readonly _name = signal('');
  private readonly _email = signal('');
  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);

  readonly output = computed<UserOutput>(() => ({
    name: this._name(),
    email: this._email(),
    isLoading: this._isLoading(),
    error: this._error(),
  }));

  // Effect: One-time events stream
  private readonly _effect = new Subject<UserEffect>();
  readonly effect$ = this._effect.asObservable();

  constructor(private readonly userService: UserService) {}

  // Input: Single entry point
  onInput(input: UserInput): void {
    switch (input.type) {
      case 'UPDATE_NAME':
        this._name.set(input.name);
        break;
      case 'UPDATE_EMAIL':
        this._email.set(input.email);
        break;
      case 'SUBMIT':
        this.submit();
        break;
    }
  }

  private async submit(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.userService.updateUser({
        name: this._name(),
        email: this._email(),
      });
      this._effect.next({ type: 'NAVIGATE_BACK' });
    } catch (error) {
      this._error.set(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      this._isLoading.set(false);
    }
  }
}
```

### 3. Four-Layer Offline-First Caching

```typescript
import { Injectable } from '@angular/core';
import Dexie from 'dexie';

interface CacheEntry<T> {
  value: T;
  timestamp: number;
}

@Injectable({ providedIn: 'root' })
export class CacheManager<T> {
  // L1: Memory cache (<1ms)
  private memoryCache = new Map<string, CacheEntry<T>>();

  // L2: LRU + TTL cache (~2ms)
  private lruCache = new Map<string, CacheEntry<T>>();
  private readonly maxLruSize = 100;
  private readonly ttlMs = 5 * 60 * 1000; // 5 minutes

  // L3: IndexedDB persistence (~10ms)
  private db: Dexie;

  // L4: Remote API fallback (~200ms)
  constructor(private readonly apiClient: ApiClient) {
    this.db = new Dexie('AppCache');
    this.db.version(1).stores({
      cache: 'key, value, timestamp',
    });
  }

  async get(key: string, loader: () => Promise<T>): Promise<T> {
    const now = Date.now();

    // Check L1: Memory cache
    const memEntry = this.memoryCache.get(key);
    if (memEntry && now - memEntry.timestamp < this.ttlMs) {
      return memEntry.value;
    }

    // Check L2: LRU cache
    const lruEntry = this.lruCache.get(key);
    if (lruEntry && now - lruEntry.timestamp < this.ttlMs) {
      this.memoryCache.set(key, lruEntry);
      return lruEntry.value;
    }

    // Check L3: IndexedDB
    const dbEntry = await this.db.table('cache').get(key);
    if (dbEntry && now - dbEntry.timestamp < this.ttlMs) {
      const entry = { value: dbEntry.value, timestamp: dbEntry.timestamp };
      this.memoryCache.set(key, entry);
      this.addToLru(key, entry);
      return dbEntry.value;
    }

    // L4: Load from remote
    const value = await loader();
    const entry = { value, timestamp: now };

    this.memoryCache.set(key, entry);
    this.addToLru(key, entry);
    await this.db.table('cache').put({ key, ...entry });

    return value;
  }

  private addToLru(key: string, entry: CacheEntry<T>): void {
    if (this.lruCache.size >= this.maxLruSize) {
      const oldestKey = this.lruCache.keys().next().value;
      if (oldestKey) this.lruCache.delete(oldestKey);
    }
    this.lruCache.set(key, entry);
  }
}
```

### 4. Offline-First Repository

```typescript
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import Dexie from 'dexie';

enum SyncStatus {
  SYNCED = 'synced',
  PENDING = 'pending',
  FAILED = 'failed',
}

@Injectable({ providedIn: 'root' })
export class UserRepository {
  private db: Dexie;
  private usersSubject = new BehaviorSubject<User[]>([]);

  constructor(
    private readonly apiClient: ApiClient,
    private readonly syncManager: SyncManager
  ) {
    this.db = new Dexie('UsersDB');
    this.db.version(1).stores({
      users: 'id, name, email, syncStatus, updatedAt',
    });
    this.loadFromLocal();
  }

  // IndexedDB as single source of truth
  getUsers(): Observable<User[]> {
    return this.usersSubject.asObservable();
  }

  // Local-first updates
  async updateUser(user: User): Promise<void> {
    // 1. Immediately update local database
    const entity = {
      ...user,
      syncStatus: SyncStatus.PENDING,
      updatedAt: Date.now(),
    };
    await this.db.table('users').put(entity);
    this.loadFromLocal();

    // 2. Schedule background sync
    this.syncManager.scheduleSync();
  }

  // Background sync processing
  async syncPendingChanges(): Promise<void> {
    const pendingUsers = await this.db
      .table('users')
      .where('syncStatus')
      .equals(SyncStatus.PENDING)
      .toArray();

    for (const user of pendingUsers) {
      try {
        await this.apiClient.updateUser(user);
        await this.db.table('users').update(user.id, {
          syncStatus: SyncStatus.SYNCED,
        });
      } catch {
        // Keep pending status for retry
      }
    }

    this.loadFromLocal();
  }

  private async loadFromLocal(): Promise<void> {
    const users = await this.db.table('users').toArray();
    this.usersSubject.next(users);
  }
}
```

### 5. Component with OnPush Change Detection

```typescript
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { UserViewModel, UserInput } from './user.viewmodel';

@Component({
  selector: 'app-user',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form (ngSubmit)="onSubmit()">
      <div class="form-group">
        <label for="name">Name</label>
        <input
          id="name"
          type="text"
          [value]="vm.output().name"
          (input)="onNameChange($event)"
        />
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          type="email"
          [value]="vm.output().email"
          (input)="onEmailChange($event)"
        />
      </div>

      @if (vm.output().error) {
        <div class="error">{{ vm.output().error }}</div>
      }

      <button type="submit" [disabled]="vm.output().isLoading">
        @if (vm.output().isLoading) {
          Loading...
        } @else {
          Submit
        }
      </button>
    </form>
  `,
  providers: [UserViewModel],
})
export class UserComponent {
  protected readonly vm = inject(UserViewModel);

  constructor() {
    // Handle effects
    this.vm.effect$.subscribe((effect) => {
      switch (effect.type) {
        case 'NAVIGATE_BACK':
          // Navigate back
          break;
        case 'SHOW_SNACKBAR':
          // Show snackbar
          break;
      }
    });
  }

  onNameChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.onInput({ type: 'UPDATE_NAME', name: input.value });
  }

  onEmailChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.onInput({ type: 'UPDATE_EMAIL', email: input.value });
  }

  onSubmit(): void {
    this.vm.onInput({ type: 'SUBMIT' });
  }
}
```

### 6. Type-Safe Navigation (NavGraphService)

```typescript
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class NavGraphService {
  private readonly router = inject(Router);

  // Type-safe navigation methods
  toHome(): Promise<boolean> {
    return this.router.navigate(['/']);
  }

  toUserList(): Promise<boolean> {
    return this.router.navigate(['/users']);
  }

  toUserDetail(userId: string): Promise<boolean> {
    return this.router.navigate(['/users', userId]);
  }

  toUserEdit(userId: string): Promise<boolean> {
    return this.router.navigate(['/users', userId, 'edit']);
  }

  toProjectList(): Promise<boolean> {
    return this.router.navigate(['/projects']);
  }

  toProjectDetail(projectId: string): Promise<boolean> {
    return this.router.navigate(['/projects', projectId]);
  }

  back(): void {
    window.history.back();
  }
}
```

### 7. Security - Input Sanitization

```typescript
import { Injectable } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Injectable({ providedIn: 'root' })
export class SanitizationService {
  constructor(private readonly sanitizer: DomSanitizer) {}

  // Sanitize HTML to prevent XSS
  sanitizeHtml(html: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(this.stripDangerousTags(html));
  }

  // Strip dangerous tags
  private stripDangerousTags(html: string): string {
    const dangerousTags = ['script', 'iframe', 'object', 'embed', 'form'];
    let result = html;

    for (const tag of dangerousTags) {
      const regex = new RegExp(`<${tag}[^>]*>.*?</${tag}>`, 'gi');
      result = result.replace(regex, '');
    }

    // Remove event handlers
    result = result.replace(/\s*on\w+="[^"]*"/gi, '');
    result = result.replace(/\s*on\w+='[^']*'/gi, '');

    return result;
  }

  // Sanitize user input
  sanitizeInput(input: string): string {
    return input
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  }
}
```

### 8. HTTP Interceptors

```typescript
import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';

// Auth Interceptor
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private readonly authService: AuthService) {}

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const token = this.authService.getToken();

    if (token) {
      req = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
    }

    return next.handle(req);
  }
}

// Error Interceptor
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      retry(1),
      catchError((error: HttpErrorResponse) => {
        let errorMessage = 'An unknown error occurred';

        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMessage = error.error.message;
        } else {
          // Server-side error
          errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }

        console.error(errorMessage);
        return throwError(() => new Error(errorMessage));
      })
    );
  }
}
```

### 9. Form Validation

```typescript
import { signal, computed } from '@angular/core';

export class FormState {
  private readonly _email = signal('');
  private readonly _emailTouched = signal(false);

  readonly email = this._email.asReadonly();

  readonly emailError = computed(() => {
    if (!this._emailTouched()) return null;

    const email = this._email();
    if (!email) return 'Email is required';
    if (!this.isValidEmail(email)) return 'Invalid email format';

    return null;
  });

  readonly isValid = computed(() => {
    const email = this._email();
    return !!email && this.isValidEmail(email);
  });

  setEmail(value: string): void {
    this._email.set(value);
  }

  markEmailTouched(): void {
    this._emailTouched.set(true);
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    return emailRegex.test(email);
  }
}
```

## Navigation Wiring Verification Guide

### 🚨 The Navigation Wiring Blind Spot

Angular Components often declare @Output navigation events that need parent binding:

```typescript
// settings.component.ts
@Component({...})
export class SettingsComponent {
  @Output() onNavigateToAccountInfo = new EventEmitter<void>();  // ⚠️ Needs parent binding!
  @Output() onNavigateToChangePassword = new EventEmitter<void>();  // ⚠️ Needs parent binding!
  @Output() onNavigateToUserList = new EventEmitter<void>();  // ⚠️ Needs parent binding!

  goToAccountInfo(): void {
    this.onNavigateToAccountInfo.emit();  // Does nothing if not bound in parent!
  }
}
```

**Problem**: If the parent Component's template doesn't bind these @Output events, the buttons appear functional but do nothing when clicked!

### Detection Patterns

```bash
# Find Components with @Output navigation events
grep -rn "@Output().*Navigate" src/app/presentation/

# Find bound events in templates
grep -rn "(onNavigate" src/app/**/*.html

# Find routes defined
grep -rn "path:" src/app/app.routes.ts

# Compare: Every @Output navigation event MUST have corresponding parent binding
```

### Verification Checklist

1. **Count @Output navigation events in each Component**:
   ```bash
   grep -c "@Output().*Navigate" src/app/presentation/settings/settings.component.ts
   ```

2. **Count bound events where Component is used**:
   ```bash
   grep -c "(onNavigate" src/app/presentation/home/home.component.html
   ```

3. **Counts MUST match!** Any mismatch = unwired navigation

### Correct Wiring Example

```typescript
// settings.component.ts (Child)
@Component({ selector: 'app-settings', ... })
export class SettingsComponent {
  @Output() onNavigateToAccountInfo = new EventEmitter<void>();
  @Output() onNavigateToChangePassword = new EventEmitter<void>();
  @Output() onNavigateToUserList = new EventEmitter<void>();
}

// home.component.html (Parent - correctly wired)
<app-settings
  (onNavigateToAccountInfo)="navGraph.toAccountInfo()"
  (onNavigateToChangePassword)="navGraph.toChangePassword()"
  (onNavigateToUserList)="navGraph.toUserList()">
</app-settings>

// app.routes.ts (routes exist)
export const routes: Routes = [
  { path: 'account-info', component: AccountInfoComponent },  // ✅ Route exists
  { path: 'change-password', component: ChangePasswordComponent },  // ✅ Route exists
  { path: 'user-list', component: UserListComponent },  // ✅ Route exists
];

// nav-graph.service.ts (methods exist)
toAccountInfo(): Promise<boolean> { return this.router.navigate(['/account-info']); }  // ✅
toChangePassword(): Promise<boolean> { return this.router.navigate(['/change-password']); }  // ✅
toUserList(): Promise<boolean> { return this.router.navigate(['/user-list']); }  // ✅
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output/Effect pattern with Signals
- [ ] Repository implements offline-first with IndexedDB
- [ ] Components use OnPush change detection
- [ ] Type-safe navigation via NavGraphService
- [ ] No implicit `any` types (strict mode)
- [ ] 🚨 ALL @Output navigation events are bound in parent templates
- [ ] 🚨 ALL routes have corresponding NavGraphService methods
- [ ] 🚨 ALL Service→Repository method calls exist in Repository interfaces
- [ ] 🚨 ALL Repository interface methods have implementations

### Performance Checks
- [ ] Use OnPush change detection across components
- [ ] Implement virtual scrolling for large datasets
- [ ] Use lazy loading and code splitting
- [ ] Leverage Angular Signals (99+ instances recommended)

### Security Checks
- [ ] Content Security Policy headers configured
- [ ] Input sanitization service used
- [ ] HTTP interceptors for auth and error handling
- [ ] XSS/CSRF protection enabled
- [ ] No hardcoded API keys

## Common Issues

### Signal Update Issues
1. Ensure signals are updated within the Angular zone
2. Use computed() for derived state
3. Avoid mutating signal values directly

### IndexedDB Issues
1. Handle version upgrades properly with Dexie
2. Use transactions for batch operations
3. Implement proper error handling

### Build Optimization
1. Enable production mode
2. Configure tree shaking
3. Use lazy loading for feature modules

---

## Spec Gap Prediction System

When Spec is incomplete, use these universal rules to predict and supplement missing UI/UX elements.

### Screen Type → Required States (Universal)

| Screen Type | Required States | Auto-Predict |
|-------------|-----------------|--------------|
| List Screen | Loading, Error, Empty, Content | Virtual scroll, Search/Filter |
| Detail Screen | Loading, Error, Content | Back navigation, Edit action |
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

```typescript
// If app.routes.ts has these paths:
export const routes: Routes = [
  { path: 'login', ... },      // → Predict: register, forgot-password
  { path: 'dashboard', ... },  // → Predict: settings, profile
  { path: 'items', ... },      // → Predict: items/:id (detail)
  { path: 'settings', ... },   // → Predict: account, change-password, about
];

// Auto-check: Every @Output navigation event must be bound in parent
```

### UI State Prediction Matrix

| Data Source | Success | Empty | Error | Loading |
|-------------|---------|-------|-------|---------|
| API Call | Content | Empty view + CTA | Error view + Retry | Spinner |
| IndexedDB | Content | Empty view + CTA | Error view + Retry | Spinner |
| User Input | Show result | Prompt input | Validation error | Submit loading |

### Spec Gap Detection Commands

```bash
# 1. Detect components missing loading state
grep -L "isLoading\|loading" src/app/presentation/**/*.viewmodel.ts

# 2. Detect components missing error state
grep -L "error\|Error" src/app/presentation/**/*.viewmodel.ts

# 3. Detect lists missing empty state
grep -l "ngFor\|*ngFor" src/app/presentation/**/*.html | \
xargs grep -L "empty\|Empty\|length === 0"

# 4. Detect forms missing validation
grep -l "formControl\|ngModel" src/app/presentation/**/*.html | \
xargs grep -L "invalid\|error\|valid"

# 5. Detect missing navigation flows
echo "=== Auth Flow Check ===" && \
grep -q "login" src/app/app.routes.ts && \
(grep -q "register" src/app/app.routes.ts || echo "⚠️ Missing: Register route") && \
(grep -q "forgot-password" src/app/app.routes.ts || echo "⚠️ Missing: Forgot Password route")

# 6. Detect missing CRUD operations
echo "=== CRUD Completeness ===" && \
grep -rh "get.*\|fetch.*\|load.*" src/app/domain/repositories/*.ts | head -5 && \
grep -rh "create.*\|add.*\|save.*" src/app/domain/repositories/*.ts | head -5 && \
grep -rh "update.*\|edit.*" src/app/domain/repositories/*.ts | head -5 && \
grep -rh "delete.*\|remove.*" src/app/domain/repositories/*.ts | head -5
```

### Prediction Implementation Example

When implementing a List screen from Spec:

```typescript
// Spec says: "Display user's items"
// Auto-predict required implementation:

@Component({
  selector: 'app-item-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- 1. LOADING - Always needed for API/DB calls -->
    @if (vm.output().isLoading) {
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    }

    <!-- 2. ERROR - Always needed for API/DB calls -->
    @else if (vm.output().error) {
      <div class="alert alert-danger">
        {{ vm.output().error }}
        <button class="btn btn-primary" (click)="onInput({ type: 'RETRY' })">
          Retry
        </button>
      </div>
    }

    <!-- 3. EMPTY - Always needed for list screens -->
    @else if (vm.output().items.length === 0) {
      <div class="empty-state text-center">
        <h3>No Items</h3>
        <p>Add your first item to get started</p>
        <button class="btn btn-primary" (click)="onInput({ type: 'ADD_CLICKED' })">
          Add Item
        </button>
      </div>
    }

    <!-- 4. CONTENT - The actual list -->
    @else {
      <ul class="list-group">
        @for (item of vm.output().items; track item.id) {
          <li class="list-group-item" (click)="onInput({ type: 'ITEM_CLICKED', id: item.id })">
            {{ item.name }}
          </li>
        }
      </ul>
    }
  `,
  providers: [ItemListViewModel],
})
export class ItemListComponent {
  protected readonly vm = inject(ItemListViewModel);

  protected onInput(input: ItemListInput): void {
    this.vm.onInput(input);
  }
}
```

---

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Angular | 20.3+ |
| TypeScript | 5.7+ |
| RxJS | 7.8+ |
| Bootstrap | 5.0+ |
| ng-bootstrap | 19.0+ |
| Dexie | 4.0+ |
| @ngx-translate | Latest |
