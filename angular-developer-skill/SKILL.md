---
name: angular-developer-skill
description: Angular development guide based on Arcana Angular enterprise architecture. Provides comprehensive support for Clean Architecture, Offline-First design with 4-layer caching, Angular Signals, MVVM Input/Output/Effect pattern, and enterprise security. Suitable for Angular project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Angular Developer Skill

Professional Angular development skill based on [Arcana Angular](https://github.com/jrjohn/arcana-angular) enterprise architecture.

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

### 1. Project Structure
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

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering
- [ ] ViewModel uses Input/Output/Effect pattern with Signals
- [ ] Repository implements offline-first with IndexedDB
- [ ] Components use OnPush change detection
- [ ] Type-safe navigation via NavGraphService
- [ ] No implicit `any` types (strict mode)

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
