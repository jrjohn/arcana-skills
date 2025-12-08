---
name: react-developer-skill
description: React development guide based on Arcana React enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design with 4-layer caching, React 19 hooks, MVVM Input/Output/Effect pattern, and enterprise security. Suitable for React project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# React Developer Skill

Professional React development skill based on [Arcana React](https://github.com/jrjohn/arcana-react) enterprise architecture.

---

## Quick Reference Card

### New Screen Checklist:
```
1. Add route → router/routes.tsx (path + element)
2. Create Component with React.memo for optimization
3. Create useViewModel hook (Input/Output/Effect pattern)
4. Create template with Loading/Error/Empty states
5. Wire navigation callbacks in parent component
6. Verify mock data returns non-empty values
```

### New Repository Checklist:
```
1. Interface → domain/repositories/xxx.repository.ts
2. Implementation → data/repositories/xxx.repository.impl.ts
3. Mock → data/repositories/mock/mock-xxx.repository.ts
4. Provider binding → core/providers/RepositoryProvider.tsx
5. Mock data (NEVER return [] or null!)
6. Verify ID consistency across repositories
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep -rn "\[\]\\|return \[\]" src/data/repositories/*.impl.ts` |
| Navigation crash | Compare routes.tsx paths vs component imports |
| Button does nothing | `grep -rn "onClick={undefined}\\|onClick={() => {}}" src/` |
| Data not loading | `grep -rn "throw.*NotImplemented\\|TODO" src/data/` |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Empty Policy | Repository stubs NEVER return empty arrays | `grep "\[\]" *.impl.ts` |
| Route Wiring | ALL routes MUST have component imports | Count paths vs components |
| Callback Binding | ALL navigation callbacks MUST be bound | Check props drilling |
| ID Consistency | Cross-repository IDs must match | Check mock data IDs |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| UI States | Loading/Error/Empty for all screens | `grep -L "isLoading" *.viewmodel.ts` |
| Mock Data Quality | Realistic, varied values (not all same) | Review mock data arrays |
| Error Messages | User-friendly, not technical errors | Check error handling |
| React.memo | Performance-critical components memoized | Check component exports |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Animations | Smooth route transitions with Framer Motion |
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
│    - Catch HTTP errors (Axios interceptors)                      │
│    - Map to AppError                                             │
│    - Throw AppError                                              │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer:                                                  │
│    - Catch repository errors                                     │
│    - Add business context if needed                              │
│    - Re-throw as AppError                                        │
├─────────────────────────────────────────────────────────────────┤
│  ViewModel Hook:                                                 │
│    - Catch all errors                                            │
│    - Update error state with getErrorMessage()                   │
│    - Check requiresReauth() for auth redirect                    │
├─────────────────────────────────────────────────────────────────┤
│  Component Layer:                                                │
│    - Display error from output.error                             │
│    - Show retry button                                           │
│    - Handle auth redirect via useEffect                          │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling by Layer

**Axios Interceptor:**
```typescript
// core/api/axios-interceptor.ts
import axios, { AxiosError } from 'axios';
import { AppError } from '../../domain/models/app-error';

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

**ViewModel Hook:**
```typescript
const loadData = useCallback(async () => {
  setIsLoading(true);
  setError(null);

  try {
    const items = await repository.getItems();
    setItems(items);
  } catch (error) {
    const appError = error as AppError;
    setError(getErrorMessage(appError));
    if (requiresReauth(appError)) {
      emitEffect({ type: 'NAVIGATE_TO_LOGIN' });
    }
  } finally {
    setIsLoading(false);
  }
}, [repository]);
```

---

## Test Coverage Targets

### Coverage by Layer

| Layer | Target | Focus Areas |
|-------|--------|-------------|
| ViewModel Hooks | 90%+ | All Input handlers, state transitions, effects |
| Service | 85%+ | Business logic, edge cases |
| Repository | 80%+ | Data mapping, error handling |
| Component | 60%+ | Template binding, user interactions |

### What to Test

**ViewModel Hook Tests (Highest Priority):**
```typescript
describe('useFeatureViewModel', () => {
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
npm run test -- --coverage

# Run tests in watch mode
npm run test

# View coverage report
open coverage/index.html
```

---

## Core Architecture Principles

### Clean Architecture - Three Layers

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│    Components + Custom Hooks + Input/Output/Effect  │
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

When handling React development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for unimplemented services (MUST be empty)
grep -rn "throw.*NotImplemented\|TODO.*implement" src/

# 2. Check for empty click handlers (MUST be empty)
grep -rn "onClick={undefined}\|onClick={() => {}}" src/

# 3. Check for missing route components (compare routes vs components)
echo "Routes defined:" && grep -c "path:" src/router/routes.tsx 2>/dev/null || echo 0
echo "Components imported:" && grep -c "element:" src/router/routes.tsx 2>/dev/null || echo 0

# 4. Check NavGraph has all navigation methods
grep -c "to\|navigate" src/core/services/nav-graph.service.ts 2>/dev/null || echo 0

# 5. Verify build compiles
npm run build

# 6. Check for navigation callbacks not wired (CRITICAL!)
echo "=== Navigation Props Defined ===" && \
grep -rh "onNavigate" src/presentation/ | grep -oE "onNavigate[A-Za-z]*" | sort -u
echo "=== Navigation Props Used ===" && \
grep -rh "onNavigate.*=" src/presentation/**/*.tsx 2>/dev/null | grep -oE "onNavigate[A-Za-z]*" | sort -u

# 7. Verify ALL routes have NavGraph navigation methods
echo "=== Routes Defined ===" && \
grep -rh "path:" src/router/routes.tsx | grep -oE "'[^']+'" | sort -u
echo "=== NavGraph Methods ===" && \
grep -rh "to[A-Z][a-zA-Z]*\(" src/core/services/nav-graph.service.ts | grep -oE "to[A-Z][a-zA-Z]*" | sort -u

# 8. Check Service→Repository wiring (CRITICAL!)
echo "=== Repository Methods Called in Services ===" && \
grep -roh "this\.[a-zA-Z]*Repository\.[a-zA-Z]*(" src/domain/services/*.ts | sort -u
echo "=== Repository Interface Methods ===" && \
grep -rh "[a-zA-Z]*\(" src/domain/repositories/*.repository.ts | grep -oE "[a-zA-Z]+\(" | sort -u

# 9. Check for empty array returns in Repository stubs (MUST FIX)
grep -rn "\[\]" src/data/repositories/*.repository.impl.ts

# 10. TypeScript type checking
npm run type-check
```

**CRITICAL**: All routes in routes.tsx MUST have corresponding component imports. Missing components cause runtime errors.

---

## Mock Data Requirements for Repository Stubs

### The Chart Data Problem

When implementing Repository stubs, **NEVER return empty arrays for data that powers UI charts or visualizations**. This causes:
- Charts that render but show nothing (blank Recharts/Chart.js canvas)
- Line charts that skip rendering (e.g., `if (data.length < 2) return;`)
- Empty state components even when data structure exists

### Mock Data Rules

**Rule 1: Array data for charts MUST have at least 7 items**
```typescript
// BAD - Chart will be blank
getCurrentWeekSummary(): Promise<WeeklySummary> {
    return Promise.resolve({
        dailyReports: []  // ← Chart has no data to render!
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

**Rule 3: Data must match interface exactly**
```bash
# Before creating mock data, ALWAYS verify the interface definition:
grep -A 20 "interface TherapyData" src/domain/models/*.ts
```

**Rule 4: Create helper functions for complex mock data**
```typescript
// Create reusable mock factory
private createMockDailyReport(score: number, duration: number): DailySleepReport {
    return {
        id: `mock_${Date.now()}`,
        sleepScore: score,
        sleepDuration: { totalMinutes: duration, ... },
        // ... all required fields
    };
}
```

---

### 0. Project Setup - CRITICAL

**IMPORTANT**: This reference project has been validated with tested npm/React settings and library versions. **NEVER reconfigure project structure or modify package.json / vite.config.ts**, or it will cause compilation errors.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-react.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git (remove original repo history)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-react template"
```

**Step 3**: Modify project name
Only modify the following required items:
- `name` field in `package.json`
- `<title>` in `index.html`
- Update related settings in environment configuration files

**Step 4**: Clean up example code
The cloned project contains example UI. Clean up and replace with new project screens:

**Core architecture files to KEEP** (do not delete):
- `src/core/` - Common utilities (Guards, Interceptors, Services)
- `src/shared/` - Shared components and hooks
- `src/data/local/` - IndexedDB (Dexie) base configuration
- `src/data/repositories/` - Repository base classes
- `src/App.tsx` - App entry point
- `src/router/routes.tsx` - Route configuration (modify routes)

**Example files to REPLACE**:
- `src/presentation/` - Delete all example screens, create new project Components
- `src/domain/models/` - Delete example Models, create new Domain Models
- `src/data/remote/` - Modify API endpoints
- `src/assets/` - Update resource files

**Step 5**: Install dependencies and verify build
```bash
npm install
npm run build
```

### Prohibited Actions
- **DO NOT** create new React project from scratch (create-react-app/vite create)
- **DO NOT** modify version numbers in `package.json`
- **DO NOT** add or remove npm dependencies (unless explicitly required)
- **DO NOT** modify build settings in `vite.config.ts`
- **DO NOT** reconfigure Tailwind, React Router, or other library settings

### Allowed Modifications
- Add business-related TypeScript code (following existing architecture)
- Add Components, Services, Custom Hooks
- Add Domain Models, Repository
- Modify resources in `src/assets/`
- Add route configurations

### 1. TDD & Spec-Driven Development Workflow - MANDATORY

**CRITICAL**: All development MUST follow this TDD workflow. Every Spec requirement must have corresponding tests BEFORE implementation.

**ABSOLUTE RULE**: TDD = Tests + Implementation. Writing tests without implementation is **INCOMPLETE**. Every test file MUST have corresponding production code that passes the tests.

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

#### Placeholder Component Policy

Placeholder components are **ONLY** allowed as a temporary route during active development. They are **FORBIDDEN** as a final state.

```typescript
// WRONG - Placeholder component left in production
{ path: 'training', element: <PlaceholderComponent /> } // FORBIDDEN!

// CORRECT - Real component implementation
{ path: 'training', element: <TrainingPage /> }
```

**Placeholder Check Command:**
```bash
# This command MUST return empty for production-ready code
grep -rn "PlaceholderComponent\|throw.*NotImplemented\|TODO.*implement\|Coming Soon" src/
```

### 2. Project Structure
```
src/
├── presentation/     # UI Layer
│   ├── components/   # Smart & Dumb Components
│   ├── layouts/      # Page Layouts
│   └── pages/        # Page Components
├── domain/           # Domain Layer
│   ├── models/       # Domain Models
│   ├── services/     # Business Services
│   └── repositories/ # Repository Interfaces
├── data/             # Data Layer
│   ├── repositories/ # Repository Implementations
│   ├── local/        # IndexedDB (Dexie)
│   └── remote/       # API Client (Axios)
├── core/             # Core utilities
│   ├── providers/    # Context Providers
│   ├── hooks/        # Shared hooks
│   └── services/     # Core services
├── shared/           # Shared components
├── router/           # React Router config
└── assets/
```

### 3. ViewModel Input/Output/Effect Pattern with Hooks

```typescript
import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { Subject } from 'rxjs';

// Input: Discriminated union defining all events
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
  | { type: 'SHOW_TOAST'; message: string };

export function useUserViewModel(userService: UserService) {
  // State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Effect stream (using RxJS Subject)
  const effectRef = useRef(new Subject<UserEffect>());
  const effect$ = effectRef.current.asObservable();

  // Output (memoized)
  const output = useMemo<UserOutput>(() => ({
    name,
    email,
    isLoading,
    error,
  }), [name, email, isLoading, error]);

  // Input handler
  const onInput = useCallback(async (input: UserInput) => {
    switch (input.type) {
      case 'UPDATE_NAME':
        setName(input.name);
        break;
      case 'UPDATE_EMAIL':
        setEmail(input.email);
        break;
      case 'SUBMIT':
        await handleSubmit();
        break;
    }
  }, [name, email]);

  const handleSubmit = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await userService.updateUser({ name, email });
      effectRef.current.next({ type: 'NAVIGATE_BACK' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [name, email, userService]);

  return { output, effect$, onInput };
}
```

### 4. Four-Layer Offline-First Caching

```typescript
import Dexie from 'dexie';

interface CacheEntry<T> {
  value: T;
  timestamp: number;
}

export class CacheManager<T> {
  // L1: Memory cache (<1ms)
  private memoryCache = new Map<string, CacheEntry<T>>();

  // L2: LRU + TTL cache (~2ms)
  private lruCache = new Map<string, CacheEntry<T>>();
  private readonly maxLruSize = 100;
  private readonly ttlMs = 5 * 60 * 1000; // 5 minutes

  // L3: IndexedDB persistence (~10ms)
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

### 5. Component with React.memo

```typescript
import React, { memo, useEffect } from 'react';
import { useUserViewModel, UserInput } from './useUserViewModel';
import { useNavGraph } from '../../core/hooks/useNavGraph';
import { useToast } from '../../shared/hooks/useToast';

interface UserFormProps {
  userService: UserService;
}

export const UserForm = memo<UserFormProps>(({ userService }) => {
  const { output, effect$, onInput } = useUserViewModel(userService);
  const navGraph = useNavGraph();
  const toast = useToast();

  // Handle effects
  useEffect(() => {
    const subscription = effect$.subscribe((effect) => {
      switch (effect.type) {
        case 'NAVIGATE_BACK':
          navGraph.back();
          break;
        case 'SHOW_TOAST':
          toast.show(effect.message);
          break;
      }
    });

    return () => subscription.unsubscribe();
  }, [effect$, navGraph, toast]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onInput({ type: 'UPDATE_NAME', name: e.target.value });
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onInput({ type: 'UPDATE_EMAIL', email: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onInput({ type: 'SUBMIT' });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="name">Name</label>
        <input
          id="name"
          type="text"
          value={output.name}
          onChange={handleNameChange}
        />
      </div>

      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={output.email}
          onChange={handleEmailChange}
        />
      </div>

      {output.error && (
        <div className="error">{output.error}</div>
      )}

      <button type="submit" disabled={output.isLoading}>
        {output.isLoading ? 'Loading...' : 'Submit'}
      </button>
    </form>
  );
});

UserForm.displayName = 'UserForm';
```

### 6. Type-Safe Navigation (NavGraph Service)

```typescript
// core/services/nav-graph.service.ts
import { useNavigate } from 'react-router-dom';
import { useCallback, useMemo } from 'react';

export function useNavGraph() {
  const navigate = useNavigate();

  return useMemo(() => ({
    toHome: () => navigate('/'),
    toUserList: () => navigate('/users'),
    toUserDetail: (userId: string) => navigate(`/users/${userId}`),
    toUserEdit: (userId: string) => navigate(`/users/${userId}/edit`),
    toProjectList: () => navigate('/projects'),
    toProjectDetail: (projectId: string) => navigate(`/projects/${projectId}`),
    toLogin: () => navigate('/login'),
    toForgotPassword: () => navigate('/forgot-password'),
    back: () => navigate(-1),
  }), [navigate]);
}
```

### 7. Context-Based Dependency Injection

```typescript
// core/providers/RepositoryProvider.tsx
import React, { createContext, useContext, useMemo } from 'react';

interface Repositories {
  userRepository: IUserRepository;
  projectRepository: IProjectRepository;
  authRepository: IAuthRepository;
}

const RepositoryContext = createContext<Repositories | null>(null);

interface RepositoryProviderProps {
  children: React.ReactNode;
  useMock?: boolean;
}

export function RepositoryProvider({ children, useMock = false }: RepositoryProviderProps) {
  const repositories = useMemo<Repositories>(() => {
    if (useMock || import.meta.env.DEV) {
      return {
        userRepository: new MockUserRepository(),
        projectRepository: new MockProjectRepository(),
        authRepository: new MockAuthRepository(),
      };
    }
    return {
      userRepository: new UserRepositoryImpl(),
      projectRepository: new ProjectRepositoryImpl(),
      authRepository: new AuthRepositoryImpl(),
    };
  }, [useMock]);

  return (
    <RepositoryContext.Provider value={repositories}>
      {children}
    </RepositoryContext.Provider>
  );
}

export function useRepositories(): Repositories {
  const context = useContext(RepositoryContext);
  if (!context) {
    throw new Error('useRepositories must be used within RepositoryProvider');
  }
  return context;
}

// Individual repository hooks
export function useUserRepository(): IUserRepository {
  return useRepositories().userRepository;
}

export function useProjectRepository(): IProjectRepository {
  return useRepositories().projectRepository;
}

export function useAuthRepository(): IAuthRepository {
  return useRepositories().authRepository;
}
```

### 8. HTTP Interceptors with Axios

```typescript
// core/api/axios-config.ts
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

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
        // Handle token expiry
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
      return Promise.reject(error);
    }
  );

  return client;
}
```

---

## Navigation Wiring Verification Guide

### The Navigation Wiring Blind Spot

React Components often have navigation callback props that need parent binding:

```typescript
// SettingsPanel.tsx
interface SettingsPanelProps {
  onNavigateToAccountInfo?: () => void;  // Needs parent binding!
  onNavigateToChangePassword?: () => void;  // Needs parent binding!
  onNavigateToUserList?: () => void;  // Needs parent binding!
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  onNavigateToAccountInfo,
  onNavigateToChangePassword,
  onNavigateToUserList,
}) => {
  // If props are not provided, buttons do nothing!
  return (
    <button onClick={onNavigateToAccountInfo}>Account Info</button>
  );
};
```

**Problem**: If the parent Component doesn't pass these props, the buttons appear functional but do nothing when clicked!

### Correct Wiring Example

```typescript
// SettingsPage.tsx (Parent - correctly wired)
import { useNavGraph } from '../../core/hooks/useNavGraph';
import { SettingsPanel } from './SettingsPanel';

export const SettingsPage: React.FC = () => {
  const navGraph = useNavGraph();

  return (
    <SettingsPanel
      onNavigateToAccountInfo={navGraph.toAccountInfo}
      onNavigateToChangePassword={navGraph.toChangePassword}
      onNavigateToUserList={navGraph.toUserList}
    />
  );
};

// routes.tsx (routes exist)
export const routes: RouteObject[] = [
  { path: '/account-info', element: <AccountInfoPage /> },  // Route exists
  { path: '/change-password', element: <ChangePasswordPage /> },  // Route exists
  { path: '/user-list', element: <UserListPage /> },  // Route exists
];
```

---

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output/Effect pattern with hooks
- [ ] Repository implements offline-first with IndexedDB
- [ ] Components use React.memo for optimization
- [ ] Type-safe navigation via useNavGraph hook
- [ ] No implicit `any` types (strict mode)
- [ ] ALL navigation callbacks are bound in parent components
- [ ] ALL routes have corresponding NavGraph methods
- [ ] ALL Service→Repository method calls exist in Repository interfaces
- [ ] ALL Repository interface methods have implementations

### Performance Checks
- [ ] Use React.memo across presentational components
- [ ] Use useMemo/useCallback for expensive computations
- [ ] Implement virtual scrolling for large datasets (react-window)
- [ ] Use lazy loading and code splitting (React.lazy)

### Security Checks
- [ ] Content Security Policy headers configured
- [ ] Input sanitization (DOMPurify for HTML)
- [ ] Axios interceptors for auth and error handling
- [ ] XSS/CSRF protection enabled
- [ ] No hardcoded API keys

---

## Common Issues

### Hook Dependency Issues
1. Include all dependencies in useEffect/useCallback/useMemo
2. Use ESLint react-hooks/exhaustive-deps rule
3. Avoid stale closures by proper dependency management

### IndexedDB Issues
1. Handle version upgrades properly with Dexie
2. Use transactions for batch operations
3. Implement proper error handling

### Build Optimization
1. Enable production mode
2. Configure tree shaking in Vite
3. Use lazy loading for route components

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

### Prediction Implementation Example

When implementing a List screen from Spec:

```typescript
// Spec says: "Display user's items"
// Auto-predict required implementation:

export const ItemList: React.FC = () => {
  const { output, onInput } = useItemListViewModel();

  // 1. LOADING - Always needed for API/DB calls
  if (output.isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  // 2. ERROR - Always needed for API/DB calls
  if (output.error) {
    return (
      <div className="text-center p-8">
        <p className="text-red-500">{output.error}</p>
        <button
          className="btn-primary mt-4"
          onClick={() => onInput({ type: 'RETRY' })}
        >
          Retry
        </button>
      </div>
    );
  }

  // 3. EMPTY - Always needed for list screens
  if (output.items.length === 0) {
    return (
      <div className="text-center p-8">
        <h3 className="text-xl font-semibold">No Items</h3>
        <p className="text-gray-500">Add your first item to get started</p>
        <button
          className="btn-primary mt-4"
          onClick={() => onInput({ type: 'ADD_CLICKED' })}
        >
          Add Item
        </button>
      </div>
    );
  }

  // 4. CONTENT - The actual list
  return (
    <ul className="divide-y">
      {output.items.map((item) => (
        <li
          key={item.id}
          className="p-4 hover:bg-gray-50 cursor-pointer"
          onClick={() => onInput({ type: 'ITEM_CLICKED', id: item.id })}
        >
          {item.name}
        </li>
      ))}
    </ul>
  );
};
```

---

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| React | 19.1+ |
| TypeScript | 5.8+ |
| Vite | 6.3+ |
| React Router | 7.0+ |
| Axios | Latest |
| RxJS | 7.8+ |
| Tailwind CSS | 4.0+ |
| Dexie | 4.0+ |
| react-i18next | Latest |
| Vitest | Latest |
| React Testing Library | Latest |
