---
name: vue-developer-skill
description: Vue 3 development guide based on Arcana Vue enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design with 4-layer progressive caching, Vue 3 Composition API with script setup, MVVM Input/Output/Effect pattern, InversifyJS DI, type-safe NavGraph navigation, and enterprise security. Suitable for Vue project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Vue Developer Skill

Professional Vue 3 development skill based on [Arcana Vue](https://github.com/jrjohn/arcana-vue) enterprise architecture.

---

## Quick Reference Card

### New Component Checklist:
```
1. Add route -> router/ (path + component)
2. Create .vue SFC with <script setup lang="ts">
3. Create useXxxViewModel composable (Models/Outputs/Inputs/Effects)
4. Create template with Loading/Error/Empty states
5. Wire navigation via NavGraph composable
6. Verify mock data returns non-empty values
```

### New Feature Checklist:
```
1. Entity         -> domain/entities/xxx.entity.ts
2. Validator      -> domain/validators/xxx.validator.ts
3. Service Interface -> domain/services/xxx.service.ts
4. Service Impl   -> domain/services/xxx.service.impl.ts
5. Repository Interface -> domain/services/ or data/repositories/
6. Repository Impl -> data/repositories/xxx.repository.impl.ts
7. Mapper         -> data/mappers/xxx.mapper.ts
8. DTO            -> data/dtos/xxx.dto.ts
9. Mock Repository -> data/repositories/mock/mock-xxx.repository.ts
10. DI Token      -> core/di/tokens.ts
11. DI Binding    -> core/di/container.ts
12. ViewModel     -> presentation/view-models/useXxxViewModel.ts
13. Component     -> presentation/features/xxx/XxxView.vue
14. Route         -> router/
15. Tests         -> __tests__/
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep -rn "\[\]\\|return \[\]" src/data/repositories/*.impl.ts` |
| Navigation crash | Compare router paths vs component imports |
| Button does nothing | `grep -rn "@click=\"\"\\|@click=\"undefined\"" src/` |
| Data not loading | `grep -rn "throw.*NotImplemented\\|TODO" src/data/` |
| DI error | Check `core/di/container.ts` bindings and tokens |
| Pinia state stale | Verify store is properly registered in `main.ts` |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty arrays | `grep "\[\]" *.impl.ts` |
| Route Wiring | ALL routes MUST have component imports | Count paths vs components |
| DI Binding | ALL services/repos MUST be bound in container | Check `container.ts` |
| NavGraph Coverage | ALL routes MUST have NavGraph methods | Check navGraph composable |
| ID Consistency | Cross-repository IDs must match | Check mock data IDs |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| UI States | Loading/Error/Empty for all screens | `grep -L "isLoading" *.viewmodel.ts` |
| Mock Data Quality | Realistic, varied values (not all same) | Review mock data arrays |
| Error Messages | User-friendly, not technical errors | Check error handling |
| Type Safety | No implicit any, strict TypeScript | `npx vue-tsc --noEmit` |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Animations | Smooth route transitions with Vue Transition |
| Accessibility | ARIA labels for interactive elements |
| Dark Mode | Support system theme preference via Bootstrap |
| PWA | Service worker for offline |

---

## Error Handling Pattern

### AppError - Unified Error Model

```typescript
// domain/entities/app-error.ts
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
+-------------------------------------------------------------------+
|                        Error Flow                                  |
+-------------------------------------------------------------------+
|  Repository Layer:                                                 |
|    - Catch HTTP errors (Axios interceptors)                        |
|    - Map to AppError via mappers                                   |
|    - Throw AppError                                                |
+-------------------------------------------------------------------+
|  Service Layer:                                                    |
|    - Catch repository errors                                       |
|    - Add business context if needed                                |
|    - Re-throw as AppError                                          |
+-------------------------------------------------------------------+
|  ViewModel Composable:                                             |
|    - Catch all errors                                              |
|    - Update error ref with getErrorMessage()                       |
|    - Check requiresReauth() for auth redirect                      |
|    - Emit effect for navigation if needed                          |
+-------------------------------------------------------------------+
|  Component Layer:                                                  |
|    - Display error from output.error                               |
|    - Show retry button                                             |
|    - Handle auth redirect via effect watcher                       |
+-------------------------------------------------------------------+
```

### Error Handling by Layer

**Axios Interceptor:**
```typescript
// data/api/axios-interceptor.ts
import axios, { type AxiosError } from 'axios';
import type { AppError } from '@/domain/entities/app-error';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    let appError: AppError;

    if (!error.response) {
      appError = { type: 'NETWORK_UNAVAILABLE' };
    } else if (error.response.status === 401) {
      appError = { type: 'UNAUTHORIZED' };
    } else if (error.response.status === 404) {
      appError = { type: 'NOT_FOUND' };
    } else if (error.response.status >= 500) {
      appError = { type: 'SERVER_ERROR', statusCode: error.response.status };
    } else {
      appError = { type: 'UNKNOWN', underlying: error };
    }

    return Promise.reject(appError);
  }
);
```

**ViewModel Composable:**
```typescript
const loadData = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const result = await service.getItems();
    items.value = result;
  } catch (err) {
    const appError = err as AppError;
    error.value = getErrorMessage(appError);
    if (requiresReauth(appError)) {
      emitEffect({ type: 'NAVIGATE_TO_LOGIN' });
    }
  } finally {
    isLoading.value = false;
  }
};
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| ViewModel Composables | 90%+ | All Input handlers, state transitions, effects |
| Service | 85%+ | Business logic, edge cases |
| Repository | 80%+ | Data mapping, error handling |
| Component | 60%+ | Template binding, user interactions |

### Arcana Vue Achieved Coverage

| Metric | Value | Threshold |
|--------|-------|-----------|
| Statements | 97.44% | 95% |
| Branches | 93.34% | 90% |
| Functions | 87.41% | 85% |
| Lines | 97.44% | 95% |
| Total Tests | 792 | - |

### What to Test

**ViewModel Composable Tests (Highest Priority):**
```typescript
describe('useFeatureViewModel', () => {
  // Test each Input
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
  it('should validate email format', () => { });
  it('should calculate score correctly', () => { });
});
```

**Repository Tests:**
```typescript
describe('UserRepository', () => {
  it('should map DTO to domain entity', async () => { });
  it('should return cached data when offline', async () => { });
});
```

### Test Commands
```bash
# Run all tests with coverage
npx vitest run --coverage

# Run tests in watch mode
npx vitest

# Run specific test file
npx vitest run src/__tests__/useLoginViewModel.test.ts

# View coverage report
open coverage/index.html
```

---

## Spec Gap Prediction System

When Spec is incomplete, use these universal rules to predict and supplement missing UI/UX elements.

### Screen Type -> Required States (Universal)

| Screen Type | Required States | Auto-Predict |
|-------------|-----------------|--------------|
| List Screen | Loading, Error, Empty, Content | Virtual scroll, Search/Filter |
| Detail Screen | Loading, Error, Content | Back navigation, Edit action |
| Form Screen | Validation, Submit Loading, Success, Error | Input validation, Cancel action |
| Dashboard | Loading, Error, Content | Refresh, Section navigation |
| Settings | Content | Back navigation, Section headers |
| Auth Screen | Loading, Error, Success | Forgot password link, Terms link |

### Prediction Implementation Example

When implementing a List screen from Spec:

```vue
<!-- Spec says: "Display user's items" -->
<!-- Auto-predict required implementation: -->
<template>
  <!-- 1. LOADING - Always needed for API/DB calls -->
  <div v-if="vm.outputs.isLoading" class="d-flex justify-content-center p-5">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>

  <!-- 2. ERROR - Always needed for API/DB calls -->
  <div v-else-if="vm.outputs.error" class="text-center p-4">
    <p class="text-danger">{{ vm.outputs.error }}</p>
    <button class="btn btn-primary mt-2" @click="vm.inputs.retry()">
      Retry
    </button>
  </div>

  <!-- 3. EMPTY - Always needed for list screens -->
  <div v-else-if="vm.outputs.items.length === 0" class="text-center p-4">
    <h3 class="fw-semibold">No Items</h3>
    <p class="text-muted">Add your first item to get started</p>
    <button class="btn btn-primary mt-2" @click="vm.inputs.addClicked()">
      Add Item
    </button>
  </div>

  <!-- 4. CONTENT - The actual list -->
  <ul v-else class="list-group">
    <li
      v-for="item in vm.outputs.items"
      :key="item.id"
      class="list-group-item list-group-item-action"
      @click="vm.inputs.itemClicked(item.id)"
    >
      {{ item.name }}
    </li>
  </ul>
</template>
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
+-----------------------------------------------------+
|                 Presentation Layer                    |
|   Vue Components + ViewModel Composables + Effects   |
+-----------------------------------------------------+
|                   Domain Layer                        |
|        Business Logic + Services + Entities           |
|              + Validators + Interfaces                |
+-----------------------------------------------------+
|                    Data Layer                         |
|  Offline-First Repository + IndexedDB + 4L Cache     |
|        + Mappers + DTOs + API Client                 |
+-----------------------------------------------------+
```

### Dependency Rules
- **Unidirectional Dependencies**: Presentation -> Domain -> Data
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces
- **InversifyJS**: All cross-layer dependencies injected via DI container

## Instructions

When handling Vue development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented services (MUST be empty)
grep -rn "throw.*NotImplemented\|TODO.*implement" src/

# 2. Check for empty click handlers (MUST be empty)
grep -rn "@click=\"\"\|@click=\"undefined\"" src/

# 3. Check for missing route components (compare routes vs components)
echo "Routes defined:" && grep -c "path:" src/router/*.ts 2>/dev/null || echo 0
echo "Components imported:" && grep -c "component:" src/router/*.ts 2>/dev/null || echo 0

# 4. Check NavGraph has all navigation methods
grep -c "navigate\|to[A-Z]" src/router/nav-graph.ts 2>/dev/null || echo 0

# 5. Verify build compiles
npx vue-tsc --noEmit && npx vite build

# 6. Verify ALL routes have NavGraph navigation methods
echo "=== Routes Defined ===" && \
grep -rh "path:" src/router/ | grep -oE "'[^']+'" | sort -u
echo "=== NavGraph Methods ===" && \
grep -rh "to[A-Z][a-zA-Z]*\|navigate" src/router/nav-graph*.ts | sort -u

# 7. Check Service->Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "this\.[a-zA-Z]*Repository\.[a-zA-Z]*(" src/domain/services/*.ts | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/domain/services/*repository*.ts | grep -oE "[a-zA-Z]+\(" | sort -u

# 8. Check for empty array returns in Repository stubs (MUST FIX)
grep -rn "\[\]" src/data/repositories/*.repository.impl.ts

# 9. Check DI container bindings
grep -rn "bind\|TOKENS" src/core/di/container.ts

# 10. TypeScript type checking
npx vue-tsc --noEmit
```

**CRITICAL**: All routes in router must have corresponding component imports. Missing components cause runtime errors.

---

## Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty arrays for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank canvas)
- Line charts that skip rendering (e.g., `if (data.length < 2) return;`)
- Empty state components even when data structure exists

### Mock Data Rules

**Rule 1: Array data for charts MUST have at least 7 items**
```typescript
// BAD - Chart will be blank
getCurrentWeekSummary(): Promise<WeeklySummary> {
    return Promise.resolve({
        dailyReports: []  // Chart has no data to render!
    });
}

// GOOD - Chart has data to display
getCurrentWeekSummary(): Promise<WeeklySummary> {
    const mockDailyReports = Array.from({ length: 7 }, (_, i) =>
        this.createMockDailyReport(
            [72, 78, 85, 80, 76, 88, 82][i],
            [390, 420, 450, 410, 380, 460, 435][i]
        )
    );
    return Promise.resolve({ dailyReports: mockDailyReports });
}
```

**Rule 2: Use realistic, varied sample values**
```typescript
// BAD - Monotonous test data
const scores = Array(7).fill(80);

// GOOD - Realistic variation
const scores = [72, 78, 85, 80, 76, 88, 82];  // Shows trend
```

**Rule 3: Data must match entity interface exactly**
```bash
# Before creating mock data, ALWAYS verify the entity definition:
grep -A 20 "interface TherapyData" src/domain/entities/*.ts
```

**Rule 4: Create helper functions for complex mock data**
```typescript
private createMockDailyReport(score: number, duration: number): DailySleepReport {
    return {
        id: `mock_${Date.now()}`,
        sleepScore: score,
        sleepDuration: { totalMinutes: duration },
        // ... all required fields
    };
}
```

---

### 0. Project Setup - CRITICAL

**IMPORTANT**: This reference project has been validated with tested npm/Vue settings and library versions. **NEVER reconfigure project structure or modify package.json / vite.config.ts**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-vue.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-vue template"
```

**Step 3**: Modify project name
Only modify the following required items:
- `name` field in `package.json`
- `<title>` in `index.html`
- Update related settings in environment configuration files

**Step 4**: Clean up example code
The cloned project contains example UI. Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `src/core/` - DI container, plugins, common utilities
- `src/domain/` - Base entities, validators, service interfaces
- `src/data/cache/` - 4-layer caching infrastructure
- `src/data/repositories/` - Repository base classes
- `src/router/` - NavGraph and route configuration (modify routes)
- `src/App.vue` - App entry point
- `src/main.ts` - Bootstrap with DI, Pinia, Router

**Example files to REPLACE**:
- `src/presentation/features/` - Delete example features, create new Components
- `src/domain/entities/` - Delete example entities, create new Domain Entities
- `src/data/api/` - Modify API endpoints
- `src/data/dtos/` - Replace DTOs to match new API
- `src/data/mappers/` - Update mappers for new DTOs
- `src/styles/` - Update theme and styles

**Step 5**: Install dependencies and verify build
```bash
npm install
npm run build
```

### Prohibited Actions
- **DO NOT** create new Vue project from scratch (create-vue / vite create)
- **DO NOT** modify version numbers in `package.json`
- **DO NOT** add or remove npm dependencies (unless explicitly required)
- **DO NOT** modify build settings in `vite.config.ts`
- **DO NOT** reconfigure Bootstrap, Vue Router, Pinia, or InversifyJS settings

### Allowed Modifications
- Add business-related TypeScript code (following existing architecture)
- Add Vue SFC Components, Services, ViewModel Composables
- Add Domain Entities, Validators, Repository implementations
- Modify resources in `src/styles/`
- Add route configurations
- Register new DI bindings in `core/di/container.ts`

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

**CRITICAL**: All development MUST follow this TDD workflow. Every Spec requirement must have corresponding tests BEFORE implementation.

**ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

```
+-------------------------------------------------------------------+
|                    TDD Development Workflow                         |
+-------------------------------------------------------------------+
|  Step 1: Analyze Spec -> Extract all SRS & SDD requirements        |
|  Step 2: Create Tests -> Write tests for EACH Spec item            |
|  Step 3: Verify Coverage -> Ensure 100% Spec coverage in tests     |
|  Step 4: Implement -> Build features to pass tests  (!) MANDATORY  |
|  Step 5: Mock APIs -> Use mock data for unfinished Cloud APIs      |
|  Step 6: Run All Tests -> ALL tests must pass before completion    |
|  Step 7: Verify 100% -> Tests written = Features implemented       |
+-------------------------------------------------------------------+
```

#### Placeholder Component Policy

Placeholder components are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```typescript
// WRONG - Placeholder component left in production
{ path: 'training', component: PlaceholderComponent } // FORBIDDEN!

// CORRECT - Real component implementation
{ path: 'training', component: () => import('@/presentation/features/training/TrainingView.vue') }
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderComponent\|throw.*NotImplemented\|TODO.*implement\|Coming Soon" src/
```

### 2. Project Structure
```
src/
+-- core/                # Core Infrastructure
|   +-- di/              # InversifyJS container & tokens
|   +-- plugins/         # Vue plugins (i18n, etc.)
+-- domain/              # Domain Layer
|   +-- entities/        # Domain entities & interfaces
|   +-- services/        # Service interfaces & implementations
|   +-- validators/      # Input validators
+-- data/                # Data Layer
|   +-- api/             # Axios client & interceptors
|   +-- repositories/    # Repository implementations + mocks
|   +-- mappers/         # DTO <-> Entity mappers
|   +-- dtos/            # Data Transfer Objects
|   +-- cache/           # 4-layer progressive cache
+-- presentation/        # Presentation Layer
|   +-- layouts/         # Layout components (MainLayout, AuthLayout)
|   +-- features/        # Feature modules (auth/, users/, dashboard/)
|   +-- components/      # Shared UI components
|   +-- view-models/     # ViewModel composables
+-- router/              # Vue Router config & NavGraph
+-- styles/              # Global styles, Bootstrap overrides
+-- App.vue
+-- main.ts
```

### 3. MVVM Input/Output/Effect Pattern with Composables

```typescript
// presentation/view-models/useUserViewModel.ts
import { ref, computed, type Ref } from 'vue';
import type { IUserService } from '@/domain/services/user.service';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';

// Effect types
export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_TOAST'; message: string };

export function useUserViewModel() {
  const userService = useInject<IUserService>(TOKENS.UserService);

  // --- Models (two-way bindable refs) ---
  const name = ref('');
  const email = ref('');

  // --- Internal state ---
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Effects ---
  const effectCallbacks: Array<(effect: UserEffect) => void> = [];

  const onEffect = (callback: (effect: UserEffect) => void) => {
    effectCallbacks.push(callback);
  };

  const emitEffect = (effect: UserEffect) => {
    effectCallbacks.forEach((cb) => cb(effect));
  };

  // --- Outputs (read-only computed) ---
  const outputs = {
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    canSubmit: computed(() =>
      name.value.length > 0 && email.value.length > 0 && !isLoading.value
    ),
  };

  // --- Inputs (action methods) ---
  const inputs = {
    async submit() {
      if (!outputs.canSubmit.value) return;

      isLoading.value = true;
      error.value = null;

      try {
        await userService.updateUser({ name: name.value, email: email.value });
        emitEffect({ type: 'SHOW_TOAST', message: 'User updated successfully' });
        emitEffect({ type: 'NAVIGATE_BACK' });
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Unknown error';
      } finally {
        isLoading.value = false;
      }
    },
  };

  return {
    models: { name, email },
    outputs,
    inputs,
    onEffect,
  };
}
```

### 4. Four-Layer Progressive Caching

```typescript
// data/cache/cache-manager.ts
import Dexie from 'dexie';

interface CacheEntry<T> {
  value: T;
  timestamp: number;
}

export class CacheManager<T> {
  // L1: Memory cache (<1ms, 50 items FIFO)
  private memoryCache = new Map<string, CacheEntry<T>>();
  private readonly maxMemorySize = 50;

  // L2: LRU + TTL cache (~2-5ms, 100 items)
  private lruCache = new Map<string, CacheEntry<T>>();
  private readonly maxLruSize = 100;
  private readonly ttlMs = 5 * 60 * 1000; // 5 minutes

  // L3: IndexedDB persistence (~10-50ms)
  private db: Dexie;

  constructor(private readonly tableName: string) {
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

    // L4: Load from remote API (100-500ms+)
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

  invalidate(key: string): void {
    this.memoryCache.delete(key);
    this.lruCache.delete(key);
    this.db.table('cache').delete(key);
  }

  invalidateAll(): void {
    this.memoryCache.clear();
    this.lruCache.clear();
    this.db.table('cache').clear();
  }
}
```

### 5. Type-Safe Navigation (NavGraph)

```typescript
// router/nav-graph.ts
import { useRouter, type Router } from 'vue-router';

export interface NavGraph {
  home: { navigate: () => void };
  users: {
    navigate: () => void;
    toDetail: (userId: string) => void;
    toEdit: (userId: string) => void;
  };
  auth: {
    toLogin: () => void;
    toRegister: () => void;
    toForgotPassword: () => void;
  };
  settings: { navigate: () => void };
  back: () => void;
}

export function useNavGraph(): NavGraph {
  const router: Router = useRouter();

  return {
    home: {
      navigate: () => router.push({ name: 'home' }),
    },
    users: {
      navigate: () => router.push({ name: 'users' }),
      toDetail: (userId: string) => router.push({ name: 'user-detail', params: { id: userId } }),
      toEdit: (userId: string) => router.push({ name: 'user-edit', params: { id: userId } }),
    },
    auth: {
      toLogin: () => router.push({ name: 'login' }),
      toRegister: () => router.push({ name: 'register' }),
      toForgotPassword: () => router.push({ name: 'forgot-password' }),
    },
    settings: {
      navigate: () => router.push({ name: 'settings' }),
    },
    back: () => router.back(),
  };
}
```

### 6. InversifyJS Dependency Injection

```typescript
// core/di/tokens.ts
export const TOKENS = {
  // Services
  AuthService: Symbol.for('AuthService'),
  UserService: Symbol.for('UserService'),

  // Repositories
  AuthRepository: Symbol.for('AuthRepository'),
  UserRepository: Symbol.for('UserRepository'),

  // Infrastructure
  ApiClient: Symbol.for('ApiClient'),
  CacheManager: Symbol.for('CacheManager'),
} as const;

// core/di/container.ts
import { Container } from 'inversify';
import { TOKENS } from './tokens';
import type { IAuthService } from '@/domain/services/auth.service';
import type { IUserService } from '@/domain/services/user.service';
import { AuthServiceImpl } from '@/domain/services/auth.service.impl';
import { UserServiceImpl } from '@/domain/services/user.service.impl';
import { UserRepositoryImpl } from '@/data/repositories/user.repository.impl';
import { MockUserRepository } from '@/data/repositories/mock/mock-user.repository';

const container = new Container();

// Bind repositories (swap mock/real based on env)
if (import.meta.env.DEV) {
  container.bind(TOKENS.UserRepository).to(MockUserRepository).inSingletonScope();
} else {
  container.bind(TOKENS.UserRepository).to(UserRepositoryImpl).inSingletonScope();
}

// Bind services
container.bind(TOKENS.UserService).to(UserServiceImpl).inSingletonScope();
container.bind(TOKENS.AuthService).to(AuthServiceImpl).inSingletonScope();

export { container };

// core/di/use-inject.ts
import { container } from './container';

export function useInject<T>(token: symbol): T {
  return container.get<T>(token);
}
```

### 7. Offline-First Architecture with Sync Queue

```typescript
// data/repositories/base-offline.repository.ts
import Dexie, { type Table } from 'dexie';

export enum SyncStatus {
  SYNCED = 'synced',
  PENDING_CREATE = 'pending_create',
  PENDING_UPDATE = 'pending_update',
  PENDING_DELETE = 'pending_delete',
  FAILED = 'failed',
}

export interface SyncableEntity {
  id: string;
  syncStatus: SyncStatus;
  version: number;
  updatedAt: number;
  deletedAt: number | null;
}

export class SyncQueue {
  private handlers = new Map<string, () => Promise<void>>();
  private pending = new Set<string>();
  private syncTimeout: ReturnType<typeof setTimeout> | null = null;

  register(key: string, handler: () => Promise<void>): void {
    this.handlers.set(key, handler);
  }

  scheduleSync(key: string, delayMs = 1000): void {
    this.pending.add(key);
    if (this.syncTimeout) clearTimeout(this.syncTimeout);
    this.syncTimeout = setTimeout(() => this.executeSync(), delayMs);
  }

  private async executeSync(): Promise<void> {
    for (const key of this.pending) {
      const handler = this.handlers.get(key);
      if (handler) {
        try {
          await handler();
          this.pending.delete(key);
        } catch (error) {
          console.error(`Sync failed for ${key}:`, error);
        }
      }
    }
  }
}
```

### 8. Security - XSS Prevention & Input Sanitization

```typescript
// domain/validators/security.validator.ts

/** Encode HTML entities to prevent XSS */
export function encodeHtmlEntities(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/** Remove dangerous patterns (script tags, event handlers) */
export function removeDangerousPatterns(input: string): string {
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/javascript\s*:/gi, '');
}

/** Detect SQL injection patterns */
export function hasSqlInjection(input: string): boolean {
  const patterns = [
    /('\s*(OR|AND)\s*')/i,
    /(;\s*(DROP|DELETE|UPDATE|INSERT|ALTER))/i,
    /(UNION\s+SELECT)/i,
    /(--\s*$)/,
  ];
  return patterns.some((p) => p.test(input));
}

/** Sanitize filename to prevent path traversal */
export function sanitizeFilename(filename: string): string {
  return filename
    .replace(/\.\./g, '')
    .replace(/[/\\]/g, '')
    .replace(/[^a-zA-Z0-9._-]/g, '_');
}

/** Validate URL with protocol whitelist */
export function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:', 'mailto:', 'tel:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

/** Remove control characters from input */
export function sanitizeInput(input: string): string {
  return input.replace(/[\x00-\x1F\x7F]/g, '').trim();
}
```

### 9. Internationalization (i18n)

```typescript
// core/plugins/i18n.ts
import { createI18n } from 'vue-i18n';
import en from '@/locales/en.json';
import zh from '@/locales/zh.json';
import zhTW from '@/locales/zh-TW.json';
import es from '@/locales/es.json';
import fr from '@/locales/fr.json';
import de from '@/locales/de.json';

export const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, zh, 'zh-TW': zhTW, es, fr, de },
});

// Usage in <script setup>
// import { useI18n } from 'vue-i18n';
// const { t } = useI18n();
// <h1>{{ t('common.welcome') }}</h1>
```

Supported languages: English (en), Chinese Simplified (zh), Chinese Traditional (zh-TW), Spanish (es), French (fr), German (de).

---

## Navigation Wiring Verification Guide

### The Navigation Wiring Blind Spot

Vue Components often emit navigation events that need parent handling:

```vue
<!-- SettingsPanel.vue -->
<script setup lang="ts">
const emit = defineEmits<{
  navigateToAccountInfo: [];
  navigateToChangePassword: [];
  navigateToUserList: [];
}>();
</script>

<template>
  <button @click="emit('navigateToAccountInfo')">Account Info</button>
  <button @click="emit('navigateToChangePassword')">Change Password</button>
</template>
```

**Problem**: If the parent Component does not listen for these emits, the buttons appear functional but do nothing when clicked!

### Correct Wiring Example

```vue
<!-- SettingsView.vue (Parent - correctly wired) -->
<script setup lang="ts">
import { useNavGraph } from '@/router/nav-graph';
import SettingsPanel from './SettingsPanel.vue';

const navGraph = useNavGraph();
</script>

<template>
  <SettingsPanel
    @navigate-to-account-info="navGraph.settings.toAccountInfo()"
    @navigate-to-change-password="navGraph.settings.toChangePassword()"
    @navigate-to-user-list="navGraph.users.navigate()"
  />
</template>
```

---

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering (Presentation -> Domain -> Data)
- [ ] ViewModel uses Models/Outputs/Inputs/Effects pattern
- [ ] Repository implements offline-first with IndexedDB (Dexie)
- [ ] Components use `<script setup lang="ts">`
- [ ] Type-safe navigation via useNavGraph composable
- [ ] No implicit `any` types (TypeScript strict mode)
- [ ] ALL navigation emits are listened to in parent components
- [ ] ALL routes have corresponding NavGraph methods
- [ ] ALL Service->Repository method calls exist in Repository interfaces
- [ ] ALL Repository interface methods have implementations
- [ ] ALL DI tokens have container bindings

### Performance Checks
- [ ] Use `computed` for derived state (not methods in template)
- [ ] Use `shallowRef` for large non-reactive objects
- [ ] Implement virtual scrolling for large datasets
- [ ] Use async component loading for routes
- [ ] Avoid unnecessary watchers; prefer computed

### Security Checks
- [ ] Content Security Policy headers configured
- [ ] Input sanitization via security validators
- [ ] Axios interceptors for auth and error handling
- [ ] XSS prevention with HTML entity encoding
- [ ] SQL injection detection on user inputs
- [ ] Path traversal prevention on file operations
- [ ] No hardcoded API keys or secrets
- [ ] URL validation with protocol whitelist

---

## Common Issues

### Reactivity Issues
1. Destructuring reactive objects loses reactivity - use `toRefs()`
2. Adding new properties to reactive objects - use `reactive()` not plain objects
3. Replacing entire ref value vs mutating - `ref.value = newVal` works, `ref = newVal` does not
4. Watchers not triggering - ensure watched source is actually reactive

### IndexedDB Issues
1. Handle version upgrades properly with Dexie
2. Use transactions for batch operations
3. Implement proper error handling for storage quota
4. Test with private browsing mode (limited storage)

### InversifyJS Issues
1. Missing `@injectable()` decorator on class
2. Circular dependency - use `@lazyInject()` or restructure
3. Token not bound in container - check `core/di/container.ts`
4. Singleton vs transient scope mismatch

### Build Optimization
1. Enable production mode (`NODE_ENV=production`)
2. Configure tree shaking in Vite
3. Use async components for route-level code splitting
4. Analyze bundle with `npx vite-bundle-visualizer`

---

## Component with script setup

```vue
<!-- presentation/features/users/UserFormView.vue -->
<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useUserViewModel } from '@/presentation/view-models/useUserViewModel';
import { useNavGraph } from '@/router/nav-graph';
import { useToast } from '@/presentation/composables/useToast';

const vm = useUserViewModel();
const navGraph = useNavGraph();
const toast = useToast();

// Handle effects
vm.onEffect((effect) => {
  switch (effect.type) {
    case 'NAVIGATE_BACK':
      navGraph.back();
      break;
    case 'SHOW_TOAST':
      toast.show(effect.message);
      break;
  }
});
</script>

<template>
  <form @submit.prevent="vm.inputs.submit()">
    <div class="mb-3">
      <label for="name" class="form-label">Name</label>
      <input
        id="name"
        v-model="vm.models.name.value"
        type="text"
        class="form-control"
      />
    </div>

    <div class="mb-3">
      <label for="email" class="form-label">Email</label>
      <input
        id="email"
        v-model="vm.models.email.value"
        type="email"
        class="form-control"
      />
    </div>

    <div v-if="vm.outputs.error.value" class="alert alert-danger">
      {{ vm.outputs.error.value }}
    </div>

    <button
      type="submit"
      class="btn btn-primary"
      :disabled="!vm.outputs.canSubmit.value"
    >
      <span v-if="vm.outputs.isLoading.value">
        <span class="spinner-border spinner-border-sm me-1" role="status"></span>
        Saving...
      </span>
      <span v-else>Save</span>
    </button>
  </form>
</template>
```

### 10. HTTP Interceptors with Axios

```typescript
// data/api/api-client.ts
import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios';

export function createApiClient(getToken: () => string | null): AxiosInstance {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 30000,
  });

  // Request interceptor - Add auth token
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - Handle errors
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
      return Promise.reject(error);
    }
  );

  return client;
}
```

---

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| Vue | 3.5+ (Composition API, script setup) |
| TypeScript | 5.7+ (strict mode) |
| Vite | 6.3+ |
| Pinia | 3.0 |
| Vue Router | 4.5 |
| Axios | 1.7 |
| InversifyJS | 7.10 |
| Dexie | 4.2 (IndexedDB) |
| Bootstrap | 5.3 + Bootstrap Icons |
| vue-i18n | Latest |
| Vitest | 3.1 |
| Vue Test Utils | Latest |
| Architecture Rating | 10/10 |
