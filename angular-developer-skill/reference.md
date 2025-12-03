# Angular Developer Skill - Technical Reference

## Table of Contents
1. [Project Structure](#project-structure)
2. [Clean Architecture Layers](#clean-architecture-layers)
3. [Angular Signals](#angular-signals)
4. [MVVM Input/Output/Effect Pattern](#mvvm-inputoutputeffect-pattern)
5. [Offline-First with IndexedDB](#offline-first-with-indexeddb)
6. [Four-Layer Caching](#four-layer-caching)
7. [Dependency Injection](#dependency-injection)
8. [HTTP Client & Interceptors](#http-client--interceptors)
9. [Routing & Navigation](#routing--navigation)
10. [Forms & Validation](#forms--validation)
11. [Security](#security)
12. [Testing](#testing)
13. [Performance Optimization](#performance-optimization)

---

## Project Structure

```
src/
├── app/
│   ├── presentation/           # UI Layer
│   │   ├── components/         # Smart & Dumb Components
│   │   │   ├── smart/          # Container components with logic
│   │   │   └── dumb/           # Presentational components
│   │   ├── layouts/            # Page layouts
│   │   ├── forms/              # Form components
│   │   ├── directives/         # Custom directives
│   │   └── pipes/              # Custom pipes
│   ├── domain/                 # Domain Layer
│   │   ├── models/             # Domain models & interfaces
│   │   ├── services/           # Business logic services
│   │   └── repositories/       # Repository interfaces
│   ├── data/                   # Data Layer
│   │   ├── repositories/       # Repository implementations
│   │   ├── local/              # IndexedDB (Dexie) storage
│   │   │   ├── database.ts     # Database configuration
│   │   │   └── entities/       # Local entities
│   │   └── remote/             # API client
│   │       ├── api-client.ts   # HTTP client wrapper
│   │       ├── interceptors/   # HTTP interceptors
│   │       └── dto/            # Data transfer objects
│   ├── core/                   # Core module
│   │   ├── guards/             # Route guards
│   │   ├── interceptors/       # Global interceptors
│   │   └── services/           # Core services
│   └── shared/                 # Shared module
│       ├── components/         # Shared components
│       ├── directives/         # Shared directives
│       └── pipes/              # Shared pipes
├── assets/                     # Static assets
├── environments/               # Environment configurations
└── styles/                     # Global SCSS styles
```

---

## Clean Architecture Layers

### Layer Responsibilities

| Layer | Responsibility | Dependencies |
|-------|----------------|--------------|
| **Presentation** | UI components, ViewModels, user interaction | Domain |
| **Domain** | Business logic, models, repository interfaces | None |
| **Data** | Repository implementations, API, local storage | Domain |

### Dependency Rules
```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│   Components ←→ ViewModel ←→ Services   │
├─────────────────────────────────────────┤
│              Domain Layer               │
│      Models + Services + Interfaces     │
├─────────────────────────────────────────┤
│               Data Layer                │
│   Repository Impl + API + IndexedDB     │
└─────────────────────────────────────────┘
          ↓ Dependencies flow down ↓
```

### Interface Segregation Example
```typescript
// domain/repositories/user-repository.interface.ts
export interface IUserRepository {
  getUsers(): Observable<User[]>;
  getUserById(id: string): Observable<User | null>;
  saveUser(user: User): Promise<void>;
  deleteUser(id: string): Promise<void>;
}

// data/repositories/user-repository.impl.ts
@Injectable({ providedIn: 'root' })
export class UserRepository implements IUserRepository {
  // Implementation details...
}
```

---

## Angular Signals

### Signal Basics
```typescript
import { signal, computed, effect } from '@angular/core';

// Writable signal
const count = signal(0);
count.set(5);           // Set value
count.update(v => v + 1); // Update based on previous

// Read-only signal
const readonlyCount = count.asReadonly();

// Computed signal (derived state)
const doubled = computed(() => count() * 2);

// Effect (side effects)
effect(() => {
  console.log('Count changed:', count());
});
```

### Signal Best Practices
```typescript
@Injectable()
export class StateService {
  // Private writable signals
  private readonly _items = signal<Item[]>([]);
  private readonly _loading = signal(false);
  private readonly _error = signal<string | null>(null);

  // Public read-only signals
  readonly items = this._items.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();

  // Computed signals for derived state
  readonly itemCount = computed(() => this._items().length);
  readonly hasItems = computed(() => this._items().length > 0);
  readonly isEmpty = computed(() => this._items().length === 0);

  // Methods to update state
  setItems(items: Item[]): void {
    this._items.set(items);
  }

  addItem(item: Item): void {
    this._items.update(items => [...items, item]);
  }

  removeItem(id: string): void {
    this._items.update(items => items.filter(i => i.id !== id));
  }
}
```

### Signal in Components
```typescript
@Component({
  selector: 'app-item-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (loading()) {
      <app-loading-spinner />
    } @else if (error()) {
      <app-error-message [message]="error()" />
    } @else {
      <ul>
        @for (item of items(); track item.id) {
          <li>{{ item.name }}</li>
        }
        @empty {
          <li>No items found</li>
        }
      </ul>
    }
  `
})
export class ItemListComponent {
  private readonly stateService = inject(StateService);

  readonly items = this.stateService.items;
  readonly loading = this.stateService.loading;
  readonly error = this.stateService.error;
}
```

---

## MVVM Input/Output/Effect Pattern

### Pattern Overview
```
┌──────────────────────────────────────────────────────┐
│                     Component                         │
│  ┌─────────────────────────────────────────────────┐ │
│  │                   ViewModel                      │ │
│  │                                                  │ │
│  │  Input ────────→ Process ────────→ Output       │ │
│  │    │                                    │        │ │
│  │    │                                    │        │ │
│  │    └──────────→ Effect ←────────────────┘       │ │
│  │                   │                              │ │
│  └───────────────────│──────────────────────────────┘│
│                      ↓                               │
│              One-time Events                         │
│         (Navigation, Snackbar, etc.)                 │
└──────────────────────────────────────────────────────┘
```

### Type Definitions
```typescript
// Input: Union type of all possible user actions
export type LoginInput =
  | { type: 'SET_EMAIL'; email: string }
  | { type: 'SET_PASSWORD'; password: string }
  | { type: 'TOGGLE_REMEMBER_ME' }
  | { type: 'SUBMIT' }
  | { type: 'FORGOT_PASSWORD' };

// Output: State container (immutable)
export interface LoginOutput {
  readonly email: string;
  readonly password: string;
  readonly rememberMe: boolean;
  readonly isLoading: boolean;
  readonly emailError: string | null;
  readonly passwordError: string | null;
  readonly canSubmit: boolean;
}

// Effect: One-time side effects
export type LoginEffect =
  | { type: 'NAVIGATE_TO_HOME' }
  | { type: 'NAVIGATE_TO_FORGOT_PASSWORD' }
  | { type: 'SHOW_ERROR'; message: string }
  | { type: 'SHOW_SUCCESS'; message: string };
```

### ViewModel Implementation
```typescript
@Injectable()
export class LoginViewModel {
  // Private state signals
  private readonly _email = signal('');
  private readonly _password = signal('');
  private readonly _rememberMe = signal(false);
  private readonly _isLoading = signal(false);
  private readonly _emailTouched = signal(false);
  private readonly _passwordTouched = signal(false);

  // Computed validation
  private readonly emailError = computed(() => {
    if (!this._emailTouched()) return null;
    const email = this._email();
    if (!email) return 'Email is required';
    if (!this.isValidEmail(email)) return 'Invalid email format';
    return null;
  });

  private readonly passwordError = computed(() => {
    if (!this._passwordTouched()) return null;
    const password = this._password();
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    return null;
  });

  private readonly canSubmit = computed(() => {
    return (
      this._email().length > 0 &&
      this._password().length > 0 &&
      !this.emailError() &&
      !this.passwordError() &&
      !this._isLoading()
    );
  });

  // Output: Aggregated state
  readonly output = computed<LoginOutput>(() => ({
    email: this._email(),
    password: this._password(),
    rememberMe: this._rememberMe(),
    isLoading: this._isLoading(),
    emailError: this.emailError(),
    passwordError: this.passwordError(),
    canSubmit: this.canSubmit(),
  }));

  // Effect stream
  private readonly _effect = new Subject<LoginEffect>();
  readonly effect$ = this._effect.asObservable();

  constructor(private readonly authService: AuthService) {}

  // Input: Single entry point for all actions
  onInput(input: LoginInput): void {
    switch (input.type) {
      case 'SET_EMAIL':
        this._email.set(input.email);
        this._emailTouched.set(true);
        break;
      case 'SET_PASSWORD':
        this._password.set(input.password);
        this._passwordTouched.set(true);
        break;
      case 'TOGGLE_REMEMBER_ME':
        this._rememberMe.update(v => !v);
        break;
      case 'SUBMIT':
        this.handleSubmit();
        break;
      case 'FORGOT_PASSWORD':
        this._effect.next({ type: 'NAVIGATE_TO_FORGOT_PASSWORD' });
        break;
    }
  }

  private async handleSubmit(): Promise<void> {
    if (!this.canSubmit()) return;

    this._isLoading.set(true);
    try {
      await this.authService.login({
        email: this._email(),
        password: this._password(),
        rememberMe: this._rememberMe(),
      });
      this._effect.next({ type: 'NAVIGATE_TO_HOME' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      this._effect.next({ type: 'SHOW_ERROR', message });
    } finally {
      this._isLoading.set(false);
    }
  }

  private isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}
```

---

## Offline-First with IndexedDB

### Dexie Database Setup
```typescript
import Dexie, { Table } from 'dexie';

export enum SyncStatus {
  SYNCED = 'synced',
  PENDING = 'pending',
  FAILED = 'failed',
}

export interface UserEntity {
  id: string;
  name: string;
  email: string;
  syncStatus: SyncStatus;
  updatedAt: number;
  version: number;
}

export class AppDatabase extends Dexie {
  users!: Table<UserEntity>;
  projects!: Table<ProjectEntity>;

  constructor() {
    super('AppDatabase');

    this.version(1).stores({
      users: 'id, email, syncStatus, updatedAt',
      projects: 'id, userId, syncStatus, updatedAt',
    });

    // Version upgrade
    this.version(2).stores({
      users: 'id, email, syncStatus, updatedAt, [syncStatus+updatedAt]',
      projects: 'id, userId, syncStatus, updatedAt',
    }).upgrade(tx => {
      // Migration logic
      return tx.table('users').toCollection().modify(user => {
        user.version = user.version ?? 1;
      });
    });
  }
}

export const db = new AppDatabase();
```

### Offline-First Repository
```typescript
@Injectable({ providedIn: 'root' })
export class UserRepositoryImpl implements IUserRepository {
  private readonly usersSubject = new BehaviorSubject<User[]>([]);

  constructor(
    private readonly apiClient: ApiClient,
    private readonly syncManager: SyncManager,
    private readonly connectivity: ConnectivityService
  ) {
    this.initializeFromLocal();
    this.setupConnectivityListener();
  }

  // Read from local database (single source of truth)
  getUsers(): Observable<User[]> {
    return this.usersSubject.asObservable();
  }

  async getUserById(id: string): Observable<User | null> {
    const entity = await db.users.get(id);
    return entity ? this.mapToUser(entity) : null;
  }

  // Write locally first, then sync
  async saveUser(user: User): Promise<void> {
    const entity: UserEntity = {
      ...user,
      syncStatus: SyncStatus.PENDING,
      updatedAt: Date.now(),
      version: (await db.users.get(user.id))?.version ?? 0 + 1,
    };

    await db.users.put(entity);
    await this.refreshFromLocal();

    // Schedule background sync
    this.syncManager.scheduleSync('users');
  }

  async deleteUser(id: string): Promise<void> {
    // Soft delete with pending sync
    await db.users.update(id, {
      syncStatus: SyncStatus.PENDING,
      deletedAt: Date.now(),
    });
    await this.refreshFromLocal();
    this.syncManager.scheduleSync('users');
  }

  // Background sync
  async syncWithRemote(): Promise<void> {
    if (!this.connectivity.isOnline()) return;

    // Pull remote changes
    try {
      const remoteUsers = await this.apiClient.getUsers();
      await db.transaction('rw', db.users, async () => {
        for (const remote of remoteUsers) {
          const local = await db.users.get(remote.id);
          if (!local || remote.version > local.version) {
            await db.users.put({
              ...remote,
              syncStatus: SyncStatus.SYNCED,
            });
          }
        }
      });
    } catch (error) {
      console.error('Pull sync failed:', error);
    }

    // Push local changes
    const pendingChanges = await db.users
      .where('syncStatus')
      .equals(SyncStatus.PENDING)
      .toArray();

    for (const entity of pendingChanges) {
      try {
        await this.apiClient.updateUser(entity);
        await db.users.update(entity.id, {
          syncStatus: SyncStatus.SYNCED,
        });
      } catch (error) {
        await db.users.update(entity.id, {
          syncStatus: SyncStatus.FAILED,
        });
      }
    }

    await this.refreshFromLocal();
  }

  private async initializeFromLocal(): Promise<void> {
    await this.refreshFromLocal();
    // Initial sync if online
    if (this.connectivity.isOnline()) {
      this.syncWithRemote();
    }
  }

  private async refreshFromLocal(): Promise<void> {
    const entities = await db.users
      .filter(u => !u.deletedAt)
      .toArray();
    this.usersSubject.next(entities.map(this.mapToUser));
  }

  private setupConnectivityListener(): void {
    this.connectivity.online$.subscribe(isOnline => {
      if (isOnline) {
        this.syncWithRemote();
      }
    });
  }

  private mapToUser(entity: UserEntity): User {
    return {
      id: entity.id,
      name: entity.name,
      email: entity.email,
    };
  }
}
```

---

## Four-Layer Caching

### Cache Architecture
```
┌────────────────────────────────────────────────────────────┐
│                    Cache Hierarchy                          │
├────────────────────────────────────────────────────────────┤
│  L1: Memory Cache     │ Map<K,V>        │ <1ms   │ 100 items│
│  L2: LRU + TTL Cache  │ Map<K,V>        │ ~2ms   │ 1K items │
│  L3: IndexedDB        │ Dexie           │ ~10ms  │ 100MB    │
│  L4: Remote API       │ HTTP            │ ~200ms │ ∞        │
└────────────────────────────────────────────────────────────┘
```

### Generic Cache Manager
```typescript
interface CacheConfig {
  l1MaxSize: number;      // Default: 100
  l2MaxSize: number;      // Default: 1000
  ttlMs: number;          // Default: 5 minutes
  tableName: string;
}

@Injectable({ providedIn: 'root' })
export class CacheManager<T> {
  // L1: In-memory cache (fastest)
  private l1Cache = new Map<string, CacheEntry<T>>();

  // L2: LRU cache with TTL
  private l2Cache = new Map<string, CacheEntry<T>>();
  private l2AccessOrder: string[] = [];

  constructor(
    private readonly config: CacheConfig,
    private readonly db: AppDatabase
  ) {}

  async get(key: string, loader: () => Promise<T>): Promise<T> {
    const now = Date.now();

    // L1: Memory cache
    const l1Entry = this.l1Cache.get(key);
    if (l1Entry && this.isValid(l1Entry, now)) {
      return l1Entry.value;
    }

    // L2: LRU cache
    const l2Entry = this.l2Cache.get(key);
    if (l2Entry && this.isValid(l2Entry, now)) {
      this.promoteToL1(key, l2Entry);
      return l2Entry.value;
    }

    // L3: IndexedDB
    const dbEntry = await this.db.table(this.config.tableName).get(key);
    if (dbEntry && this.isValid(dbEntry, now)) {
      const entry = { value: dbEntry.value, timestamp: dbEntry.timestamp };
      this.promoteToL1(key, entry);
      this.addToL2(key, entry);
      return dbEntry.value;
    }

    // L4: Remote loader
    const value = await loader();
    await this.set(key, value);
    return value;
  }

  async set(key: string, value: T): Promise<void> {
    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
    };

    this.promoteToL1(key, entry);
    this.addToL2(key, entry);
    await this.db.table(this.config.tableName).put({
      key,
      value,
      timestamp: entry.timestamp,
    });
  }

  async invalidate(key: string): Promise<void> {
    this.l1Cache.delete(key);
    this.l2Cache.delete(key);
    this.l2AccessOrder = this.l2AccessOrder.filter(k => k !== key);
    await this.db.table(this.config.tableName).delete(key);
  }

  async clear(): Promise<void> {
    this.l1Cache.clear();
    this.l2Cache.clear();
    this.l2AccessOrder = [];
    await this.db.table(this.config.tableName).clear();
  }

  private isValid(entry: CacheEntry<T>, now: number): boolean {
    return now - entry.timestamp < this.config.ttlMs;
  }

  private promoteToL1(key: string, entry: CacheEntry<T>): void {
    if (this.l1Cache.size >= this.config.l1MaxSize) {
      const firstKey = this.l1Cache.keys().next().value;
      if (firstKey) this.l1Cache.delete(firstKey);
    }
    this.l1Cache.set(key, entry);
  }

  private addToL2(key: string, entry: CacheEntry<T>): void {
    // Remove from access order if exists
    const existingIndex = this.l2AccessOrder.indexOf(key);
    if (existingIndex > -1) {
      this.l2AccessOrder.splice(existingIndex, 1);
    }

    // Evict if at capacity
    while (this.l2Cache.size >= this.config.l2MaxSize) {
      const lruKey = this.l2AccessOrder.shift();
      if (lruKey) this.l2Cache.delete(lruKey);
    }

    this.l2Cache.set(key, entry);
    this.l2AccessOrder.push(key);
  }
}
```

---

## Dependency Injection

### Provider Patterns
```typescript
// Root-level singleton
@Injectable({ providedIn: 'root' })
export class GlobalService {}

// Component-level (new instance per component)
@Component({
  providers: [ComponentScopedService],
})
export class MyComponent {}

// Factory provider
export const USER_REPOSITORY = new InjectionToken<IUserRepository>('UserRepository');

export const userRepositoryProvider: Provider = {
  provide: USER_REPOSITORY,
  useFactory: (http: HttpClient, db: AppDatabase) => {
    return new UserRepositoryImpl(http, db);
  },
  deps: [HttpClient, AppDatabase],
};

// Value provider
export const API_CONFIG = new InjectionToken<ApiConfig>('ApiConfig');

export const apiConfigProvider: Provider = {
  provide: API_CONFIG,
  useValue: {
    baseUrl: environment.apiUrl,
    timeout: 30000,
  },
};

// Class provider with interface
export const authServiceProvider: Provider = {
  provide: AUTH_SERVICE,
  useClass: environment.production ? AuthService : MockAuthService,
};
```

### Inject Function (Modern Approach)
```typescript
@Component({
  selector: 'app-user',
  standalone: true,
})
export class UserComponent {
  // Modern inject() function
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
  private readonly config = inject(API_CONFIG);

  // Optional injection
  private readonly analytics = inject(AnalyticsService, { optional: true });
}
```

---

## HTTP Client & Interceptors

### API Client Service
```typescript
@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);
  private readonly config = inject(API_CONFIG);

  get<T>(endpoint: string, params?: HttpParams): Observable<T> {
    return this.http.get<T>(`${this.config.baseUrl}${endpoint}`, { params });
  }

  post<T>(endpoint: string, body: unknown): Observable<T> {
    return this.http.post<T>(`${this.config.baseUrl}${endpoint}`, body);
  }

  put<T>(endpoint: string, body: unknown): Observable<T> {
    return this.http.put<T>(`${this.config.baseUrl}${endpoint}`, body);
  }

  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${this.config.baseUrl}${endpoint}`);
  }
}
```

### Functional Interceptors (Angular 17+)
```typescript
// Auth interceptor
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req);
};

// Error interceptor
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};

// Retry interceptor
export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    retry({
      count: 3,
      delay: (error, retryCount) => {
        if (error.status >= 500) {
          return timer(1000 * retryCount);
        }
        return throwError(() => error);
      },
    })
  );
};

// Register in app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(
      withInterceptors([
        authInterceptor,
        retryInterceptor,
        errorInterceptor,
      ])
    ),
  ],
};
```

---

## Routing & Navigation

### Route Configuration
```typescript
export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'home',
    loadComponent: () => import('./home/home.component').then(m => m.HomeComponent),
  },
  {
    path: 'users',
    loadChildren: () => import('./users/users.routes').then(m => m.USER_ROUTES),
    canActivate: [authGuard],
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes').then(m => m.ADMIN_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] },
  },
  {
    path: '**',
    loadComponent: () => import('./not-found/not-found.component').then(m => m.NotFoundComponent),
  },
];
```

### Type-Safe Navigation Service
```typescript
@Injectable({ providedIn: 'root' })
export class NavGraphService {
  private readonly router = inject(Router);

  // Home
  toHome(): Promise<boolean> {
    return this.router.navigate(['/home']);
  }

  // Users
  toUserList(): Promise<boolean> {
    return this.router.navigate(['/users']);
  }

  toUserDetail(userId: string): Promise<boolean> {
    return this.router.navigate(['/users', userId]);
  }

  toUserEdit(userId: string): Promise<boolean> {
    return this.router.navigate(['/users', userId, 'edit']);
  }

  toUserCreate(): Promise<boolean> {
    return this.router.navigate(['/users', 'new']);
  }

  // Projects with query params
  toProjectList(filters?: { status?: string; category?: string }): Promise<boolean> {
    return this.router.navigate(['/projects'], {
      queryParams: filters,
    });
  }

  toProjectDetail(projectId: string): Promise<boolean> {
    return this.router.navigate(['/projects', projectId]);
  }

  // Navigation utilities
  back(): void {
    window.history.back();
  }

  replaceUrl(commands: string[]): Promise<boolean> {
    return this.router.navigate(commands, { replaceUrl: true });
  }
}
```

### Route Guards (Functional)
```typescript
// Auth guard
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url },
  });
};

// Role guard
export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const requiredRoles = route.data['roles'] as string[];

  return requiredRoles.some(role => authService.hasRole(role));
};

// Unsaved changes guard
export const unsavedChangesGuard: CanDeactivateFn<{ hasUnsavedChanges: () => boolean }> = (
  component,
  route,
  state
) => {
  if (component.hasUnsavedChanges()) {
    return window.confirm('You have unsaved changes. Leave anyway?');
  }
  return true;
};
```

---

## Forms & Validation

### Signal-Based Form State
```typescript
export class FormState<T extends Record<string, unknown>> {
  private readonly _values = signal<T>({} as T);
  private readonly _touched = signal<Set<keyof T>>(new Set());
  private readonly _errors = signal<Partial<Record<keyof T, string>>>({});
  private readonly _validators: Map<keyof T, ValidatorFn<T>[]>;

  constructor(
    initialValues: T,
    validators: Partial<Record<keyof T, ValidatorFn<T>[]>>
  ) {
    this._values.set(initialValues);
    this._validators = new Map(Object.entries(validators) as any);
  }

  // Read-only access
  readonly values = this._values.asReadonly();
  readonly touched = this._touched.asReadonly();
  readonly errors = this._errors.asReadonly();

  readonly isValid = computed(() => {
    const errors = this._errors();
    return Object.keys(errors).length === 0;
  });

  readonly isDirty = computed(() => {
    return this._touched().size > 0;
  });

  // Field-level access
  getValue<K extends keyof T>(field: K): T[K] {
    return this._values()[field];
  }

  getError<K extends keyof T>(field: K): string | null {
    return this._errors()[field] ?? null;
  }

  isTouched<K extends keyof T>(field: K): boolean {
    return this._touched().has(field);
  }

  // Mutations
  setValue<K extends keyof T>(field: K, value: T[K]): void {
    this._values.update(v => ({ ...v, [field]: value }));
    this.validateField(field);
  }

  markTouched<K extends keyof T>(field: K): void {
    this._touched.update(t => new Set(t).add(field));
    this.validateField(field);
  }

  markAllTouched(): void {
    const allFields = new Set(Object.keys(this._values()) as (keyof T)[]);
    this._touched.set(allFields);
    this.validateAll();
  }

  reset(values?: T): void {
    this._values.set(values ?? ({} as T));
    this._touched.set(new Set());
    this._errors.set({});
  }

  private validateField<K extends keyof T>(field: K): void {
    const validators = this._validators.get(field) ?? [];
    const value = this._values()[field];

    for (const validator of validators) {
      const error = validator(value, this._values());
      if (error) {
        this._errors.update(e => ({ ...e, [field]: error }));
        return;
      }
    }

    this._errors.update(e => {
      const { [field]: _, ...rest } = e;
      return rest as Partial<Record<keyof T, string>>;
    });
  }

  private validateAll(): void {
    for (const field of this._validators.keys()) {
      this.validateField(field);
    }
  }
}

type ValidatorFn<T> = (value: unknown, allValues: T) => string | null;
```

### Built-in Validators
```typescript
export const Validators = {
  required: (message = 'This field is required') =>
    (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return message;
      }
      return null;
    },

  email: (message = 'Invalid email address') =>
    (value: unknown) => {
      if (typeof value !== 'string') return null;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value) ? null : message;
    },

  minLength: (min: number, message?: string) =>
    (value: unknown) => {
      if (typeof value !== 'string') return null;
      return value.length >= min ? null : (message ?? `Minimum ${min} characters`);
    },

  maxLength: (max: number, message?: string) =>
    (value: unknown) => {
      if (typeof value !== 'string') return null;
      return value.length <= max ? null : (message ?? `Maximum ${max} characters`);
    },

  pattern: (regex: RegExp, message: string) =>
    (value: unknown) => {
      if (typeof value !== 'string') return null;
      return regex.test(value) ? null : message;
    },

  match: <T>(otherField: keyof T, message = 'Fields do not match') =>
    (value: unknown, allValues: T) => {
      return value === allValues[otherField] ? null : message;
    },
};
```

---

## Security

### Content Security Policy
```typescript
// In index.html or server config
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.example.com;
">
```

### XSS Prevention
```typescript
@Injectable({ providedIn: 'root' })
export class SanitizationService {
  private readonly sanitizer = inject(DomSanitizer);

  // Sanitize user input for display
  escapeHtml(input: string): string {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
  }

  // Sanitize URL
  sanitizeUrl(url: string): SafeUrl {
    // Allow only safe protocols
    if (!/^(https?|mailto|tel):/.test(url)) {
      return this.sanitizer.bypassSecurityTrustUrl('about:blank');
    }
    return this.sanitizer.bypassSecurityTrustUrl(url);
  }

  // Strip dangerous HTML tags
  stripDangerousTags(html: string): string {
    const dangerous = ['script', 'iframe', 'object', 'embed', 'form', 'input'];
    let result = html;

    for (const tag of dangerous) {
      const regex = new RegExp(`<${tag}[^>]*>.*?</${tag}>`, 'gis');
      result = result.replace(regex, '');
      // Self-closing
      result = result.replace(new RegExp(`<${tag}[^>]*/>`, 'gi'), '');
    }

    // Remove event handlers
    result = result.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');

    return result;
  }
}
```

### CSRF Protection
```typescript
// CSRF token interceptor
export const csrfInterceptor: HttpInterceptorFn = (req, next) => {
  // Skip for GET requests
  if (req.method === 'GET') {
    return next(req);
  }

  // Get CSRF token from cookie
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('XSRF-TOKEN='))
    ?.split('=')[1];

  if (csrfToken) {
    req = req.clone({
      setHeaders: { 'X-XSRF-TOKEN': csrfToken },
    });
  }

  return next(req);
};
```

---

## Testing

### Component Testing
```typescript
describe('UserComponent', () => {
  let component: UserComponent;
  let fixture: ComponentFixture<UserComponent>;
  let mockUserService: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    mockUserService = jasmine.createSpyObj('UserService', ['getUser', 'updateUser']);

    await TestBed.configureTestingModule({
      imports: [UserComponent],
      providers: [
        { provide: UserService, useValue: mockUserService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserComponent);
    component = fixture.componentInstance;
  });

  it('should display user name', () => {
    mockUserService.getUser.and.returnValue(of({ id: '1', name: 'John' }));
    fixture.detectChanges();

    const nameElement = fixture.nativeElement.querySelector('.user-name');
    expect(nameElement.textContent).toContain('John');
  });

  it('should call updateUser on form submit', fakeAsync(() => {
    mockUserService.updateUser.and.returnValue(of(void 0));

    component.onSubmit();
    tick();

    expect(mockUserService.updateUser).toHaveBeenCalled();
  }));
});
```

### ViewModel Testing
```typescript
describe('LoginViewModel', () => {
  let viewModel: LoginViewModel;
  let mockAuthService: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    mockAuthService = jasmine.createSpyObj('AuthService', ['login']);

    TestBed.configureTestingModule({
      providers: [
        LoginViewModel,
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    viewModel = TestBed.inject(LoginViewModel);
  });

  it('should update email on input', () => {
    viewModel.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });

    expect(viewModel.output().email).toBe('test@example.com');
  });

  it('should validate email format', () => {
    viewModel.onInput({ type: 'SET_EMAIL', email: 'invalid' });

    expect(viewModel.output().emailError).toBeTruthy();
  });

  it('should emit navigation effect on successful login', fakeAsync(() => {
    mockAuthService.login.and.returnValue(Promise.resolve());
    const effects: LoginEffect[] = [];
    viewModel.effect$.subscribe(e => effects.push(e));

    viewModel.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });
    viewModel.onInput({ type: 'SET_PASSWORD', password: 'password123' });
    viewModel.onInput({ type: 'SUBMIT' });
    tick();

    expect(effects).toContain(jasmine.objectContaining({ type: 'NAVIGATE_TO_HOME' }));
  }));
});
```

### Service Testing with HttpClientTestingModule
```typescript
describe('ApiClient', () => {
  let apiClient: ApiClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ApiClient,
        { provide: API_CONFIG, useValue: { baseUrl: 'http://test.api' } },
      ],
    });

    apiClient = TestBed.inject(ApiClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should make GET request', () => {
    const mockData = [{ id: '1', name: 'Test' }];

    apiClient.get<User[]>('/users').subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('http://test.api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockData);
  });
});
```

---

## Performance Optimization

### OnPush Change Detection
```typescript
@Component({
  selector: 'app-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @for (item of items(); track item.id) {
      <app-list-item [item]="item" />
    }
  `,
})
export class ListComponent {
  readonly items = input.required<Item[]>();
}
```

### Virtual Scrolling
```typescript
import { CdkVirtualScrollViewport, ScrollingModule } from '@angular/cdk/scrolling';

@Component({
  selector: 'app-virtual-list',
  standalone: true,
  imports: [ScrollingModule],
  template: `
    <cdk-virtual-scroll-viewport itemSize="50" class="viewport">
      <div *cdkVirtualFor="let item of items; trackBy: trackById" class="item">
        {{ item.name }}
      </div>
    </cdk-virtual-scroll-viewport>
  `,
  styles: [`
    .viewport {
      height: 400px;
      width: 100%;
    }
    .item {
      height: 50px;
    }
  `],
})
export class VirtualListComponent {
  items = input.required<Item[]>();

  trackById(index: number, item: Item): string {
    return item.id;
  }
}
```

### Lazy Loading Routes
```typescript
export const routes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./dashboard/dashboard.component').then(m => m.DashboardComponent),
  },
  {
    path: 'admin',
    loadChildren: () =>
      import('./admin/admin.routes').then(m => m.ADMIN_ROUTES),
  },
];
```

### Defer Blocks (Angular 17+)
```typescript
@Component({
  template: `
    @defer (on viewport) {
      <app-heavy-component />
    } @placeholder {
      <div class="skeleton">Loading...</div>
    } @loading (minimum 500ms) {
      <app-spinner />
    } @error {
      <p>Failed to load</p>
    }
  `,
})
export class PageComponent {}
```

### Image Optimization
```typescript
@Component({
  template: `
    <img
      ngSrc="/images/hero.jpg"
      width="800"
      height="400"
      priority
      placeholder="blur"
    />
  `,
  imports: [NgOptimizedImage],
})
export class HeroComponent {}
```
