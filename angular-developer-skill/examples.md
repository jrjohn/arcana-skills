# Angular Developer Skill - Code Examples

## Table of Contents
1. [Login Feature Implementation](#login-feature-implementation)
2. [List with Search and Pagination](#list-with-search-and-pagination)
3. [Form with Validation](#form-with-validation)
4. [Offline-First CRUD Operations](#offline-first-crud-operations)
5. [Real-Time Updates with WebSocket](#real-time-updates-with-websocket)

---

## Login Feature Implementation

### Domain Layer

```typescript
// domain/models/auth.model.ts
export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

// domain/repositories/auth-repository.interface.ts
export interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<AuthToken>;
  logout(): Promise<void>;
  refreshToken(refreshToken: string): Promise<AuthToken>;
  getCurrentUser(): Promise<User | null>;
}

// domain/services/auth.service.ts
import { Injectable, signal, computed, inject } from '@angular/core';
import { AUTH_REPOSITORY } from '../repositories/auth-repository.interface';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly repository = inject(AUTH_REPOSITORY);

  private readonly _user = signal<User | null>(null);
  private readonly _token = signal<AuthToken | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => !!this._token() && !this.isTokenExpired());
  readonly roles = computed(() => this._user()?.roles ?? []);

  async login(credentials: LoginCredentials): Promise<void> {
    const token = await this.repository.login(credentials);
    this._token.set(token);

    if (credentials.rememberMe) {
      localStorage.setItem('refreshToken', token.refreshToken);
    }

    const user = await this.repository.getCurrentUser();
    this._user.set(user);
  }

  async logout(): Promise<void> {
    await this.repository.logout();
    this._token.set(null);
    this._user.set(null);
    localStorage.removeItem('refreshToken');
  }

  getToken(): string | null {
    return this._token()?.accessToken ?? null;
  }

  hasRole(role: string): boolean {
    return this.roles().includes(role);
  }

  private isTokenExpired(): boolean {
    const token = this._token();
    if (!token) return true;
    return Date.now() >= token.expiresAt;
  }

  async tryRestoreSession(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return;

    try {
      const token = await this.repository.refreshToken(refreshToken);
      this._token.set(token);
      const user = await this.repository.getCurrentUser();
      this._user.set(user);
    } catch {
      localStorage.removeItem('refreshToken');
    }
  }
}
```

### Data Layer

```typescript
// data/repositories/auth-repository.impl.ts
import { Injectable, inject } from '@angular/core';
import { IAuthRepository } from '../../domain/repositories/auth-repository.interface';
import { ApiClient } from '../remote/api-client';

@Injectable({ providedIn: 'root' })
export class AuthRepositoryImpl implements IAuthRepository {
  private readonly apiClient = inject(ApiClient);

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await firstValueFrom(
      this.apiClient.post<AuthTokenDto>('/auth/login', credentials)
    );
    return this.mapToAuthToken(response);
  }

  async logout(): Promise<void> {
    await firstValueFrom(this.apiClient.post('/auth/logout', {}));
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    const response = await firstValueFrom(
      this.apiClient.post<AuthTokenDto>('/auth/refresh', { refreshToken })
    );
    return this.mapToAuthToken(response);
  }

  async getCurrentUser(): Promise<User | null> {
    const response = await firstValueFrom(
      this.apiClient.get<UserDto>('/auth/me')
    );
    return this.mapToUser(response);
  }

  private mapToAuthToken(dto: AuthTokenDto): AuthToken {
    return {
      accessToken: dto.access_token,
      refreshToken: dto.refresh_token,
      expiresAt: Date.now() + dto.expires_in * 1000,
    };
  }

  private mapToUser(dto: UserDto): User {
    return {
      id: dto.id,
      email: dto.email,
      name: dto.name,
      roles: dto.roles,
    };
  }
}
```

### Presentation Layer

```typescript
// presentation/login/login.viewmodel.ts
import { Injectable, signal, computed, inject } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from '../../domain/services/auth.service';

export type LoginInput =
  | { type: 'SET_EMAIL'; email: string }
  | { type: 'SET_PASSWORD'; password: string }
  | { type: 'TOGGLE_REMEMBER_ME' }
  | { type: 'SUBMIT' }
  | { type: 'FORGOT_PASSWORD' };

export interface LoginOutput {
  email: string;
  password: string;
  rememberMe: boolean;
  isLoading: boolean;
  emailError: string | null;
  passwordError: string | null;
  canSubmit: boolean;
}

export type LoginEffect =
  | { type: 'NAVIGATE_TO_HOME' }
  | { type: 'NAVIGATE_TO_FORGOT_PASSWORD' }
  | { type: 'SHOW_ERROR'; message: string };

@Injectable()
export class LoginViewModel {
  private readonly authService = inject(AuthService);

  // State
  private readonly _email = signal('');
  private readonly _password = signal('');
  private readonly _rememberMe = signal(false);
  private readonly _isLoading = signal(false);
  private readonly _emailTouched = signal(false);
  private readonly _passwordTouched = signal(false);

  // Validation
  private readonly emailError = computed(() => {
    if (!this._emailTouched()) return null;
    const email = this._email();
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
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
    const email = this._email();
    const password = this._password();
    return (
      email.length > 0 &&
      password.length > 0 &&
      !this.emailError() &&
      !this.passwordError() &&
      !this._isLoading()
    );
  });

  // Output
  readonly output = computed<LoginOutput>(() => ({
    email: this._email(),
    password: this._password(),
    rememberMe: this._rememberMe(),
    isLoading: this._isLoading(),
    emailError: this.emailError(),
    passwordError: this.passwordError(),
    canSubmit: this.canSubmit(),
  }));

  // Effect
  private readonly _effect = new Subject<LoginEffect>();
  readonly effect$ = this._effect.asObservable();

  // Input handler
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
}

// presentation/login/login.component.ts
import { Component, ChangeDetectionStrategy, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LoginViewModel, LoginInput } from './login.viewmodel';
import { NavGraphService } from '../../core/services/nav-graph.service';
import { ToastService } from '../../shared/services/toast.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [LoginViewModel],
  template: `
    <div class="login-container">
      <div class="login-card">
        <h1>Sign In</h1>

        <form (ngSubmit)="onSubmit()">
          <!-- Email Field -->
          <div class="form-group">
            <label for="email">Email</label>
            <input
              id="email"
              type="email"
              [value]="vm.output().email"
              (input)="onEmailChange($event)"
              (blur)="onEmailBlur()"
              [class.error]="vm.output().emailError"
              placeholder="Enter your email"
              autocomplete="email"
            />
            @if (vm.output().emailError) {
              <span class="error-message">{{ vm.output().emailError }}</span>
            }
          </div>

          <!-- Password Field -->
          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              type="password"
              [value]="vm.output().password"
              (input)="onPasswordChange($event)"
              (blur)="onPasswordBlur()"
              [class.error]="vm.output().passwordError"
              placeholder="Enter your password"
              autocomplete="current-password"
            />
            @if (vm.output().passwordError) {
              <span class="error-message">{{ vm.output().passwordError }}</span>
            }
          </div>

          <!-- Remember Me -->
          <div class="form-group checkbox">
            <label>
              <input
                type="checkbox"
                [checked]="vm.output().rememberMe"
                (change)="onRememberMeChange()"
              />
              Remember me
            </label>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="btn-primary"
            [disabled]="!vm.output().canSubmit"
          >
            @if (vm.output().isLoading) {
              <span class="spinner"></span>
              Signing in...
            } @else {
              Sign In
            }
          </button>

          <!-- Forgot Password Link -->
          <a href="#" class="forgot-password" (click)="onForgotPassword($event)">
            Forgot your password?
          </a>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 1rem;
    }

    .login-card {
      width: 100%;
      max-width: 400px;
      padding: 2rem;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .form-group {
      margin-bottom: 1rem;
    }

    .error-message {
      color: #dc3545;
      font-size: 0.875rem;
    }

    input.error {
      border-color: #dc3545;
    }
  `],
})
export class LoginComponent {
  protected readonly vm = inject(LoginViewModel);
  private readonly navGraph = inject(NavGraphService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    this.vm.effect$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(effect => {
        switch (effect.type) {
          case 'NAVIGATE_TO_HOME':
            this.navGraph.toHome();
            break;
          case 'NAVIGATE_TO_FORGOT_PASSWORD':
            this.navGraph.toForgotPassword();
            break;
          case 'SHOW_ERROR':
            this.toast.error(effect.message);
            break;
        }
      });
  }

  onEmailChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.onInput({ type: 'SET_EMAIL', email: input.value });
  }

  onEmailBlur(): void {
    // Trigger validation on blur
    this.vm.onInput({ type: 'SET_EMAIL', email: this.vm.output().email });
  }

  onPasswordChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.vm.onInput({ type: 'SET_PASSWORD', password: input.value });
  }

  onPasswordBlur(): void {
    this.vm.onInput({ type: 'SET_PASSWORD', password: this.vm.output().password });
  }

  onRememberMeChange(): void {
    this.vm.onInput({ type: 'TOGGLE_REMEMBER_ME' });
  }

  onSubmit(): void {
    this.vm.onInput({ type: 'SUBMIT' });
  }

  onForgotPassword(event: Event): void {
    event.preventDefault();
    this.vm.onInput({ type: 'FORGOT_PASSWORD' });
  }
}
```

---

## List with Search and Pagination

### Domain Layer

```typescript
// domain/models/pagination.model.ts
export interface PaginatedResult<T> {
  items: T[];
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export interface SearchParams {
  query: string;
  pageIndex: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// domain/models/user.model.ts
export interface User {
  id: string;
  name: string;
  email: string;
  department: string;
  status: 'active' | 'inactive';
  createdAt: Date;
}

// domain/repositories/user-repository.interface.ts
export interface IUserRepository {
  searchUsers(params: SearchParams): Promise<PaginatedResult<User>>;
  getUserById(id: string): Promise<User | null>;
}
```

### Presentation Layer

```typescript
// presentation/users/user-list.viewmodel.ts
import { Injectable, signal, computed, inject, effect } from '@angular/core';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { USER_REPOSITORY } from '../../domain/repositories/user-repository.interface';

export type UserListInput =
  | { type: 'SET_SEARCH_QUERY'; query: string }
  | { type: 'SET_PAGE'; pageIndex: number }
  | { type: 'SET_PAGE_SIZE'; pageSize: number }
  | { type: 'SET_SORT'; sortBy: string; sortOrder: 'asc' | 'desc' }
  | { type: 'REFRESH' }
  | { type: 'SELECT_USER'; userId: string };

export interface UserListOutput {
  users: User[];
  searchQuery: string;
  pageIndex: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  sortBy: string | null;
  sortOrder: 'asc' | 'desc';
  isLoading: boolean;
  error: string | null;
}

export type UserListEffect =
  | { type: 'NAVIGATE_TO_USER_DETAIL'; userId: string };

@Injectable()
export class UserListViewModel {
  private readonly repository = inject(USER_REPOSITORY);

  // State
  private readonly _users = signal<User[]>([]);
  private readonly _searchQuery = signal('');
  private readonly _pageIndex = signal(0);
  private readonly _pageSize = signal(10);
  private readonly _totalCount = signal(0);
  private readonly _sortBy = signal<string | null>(null);
  private readonly _sortOrder = signal<'asc' | 'desc'>('asc');
  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);

  // Debounced search
  private readonly searchSubject = new Subject<string>();

  // Computed
  private readonly totalPages = computed(() =>
    Math.ceil(this._totalCount() / this._pageSize())
  );

  private readonly hasNextPage = computed(() =>
    this._pageIndex() < this.totalPages() - 1
  );

  private readonly hasPreviousPage = computed(() =>
    this._pageIndex() > 0
  );

  // Output
  readonly output = computed<UserListOutput>(() => ({
    users: this._users(),
    searchQuery: this._searchQuery(),
    pageIndex: this._pageIndex(),
    pageSize: this._pageSize(),
    totalCount: this._totalCount(),
    totalPages: this.totalPages(),
    hasNextPage: this.hasNextPage(),
    hasPreviousPage: this.hasPreviousPage(),
    sortBy: this._sortBy(),
    sortOrder: this._sortOrder(),
    isLoading: this._isLoading(),
    error: this._error(),
  }));

  // Effect
  private readonly _effect = new Subject<UserListEffect>();
  readonly effect$ = this._effect.asObservable();

  constructor() {
    // Setup debounced search
    this.searchSubject
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntilDestroyed()
      )
      .subscribe(query => {
        this._searchQuery.set(query);
        this._pageIndex.set(0); // Reset to first page
        this.loadUsers();
      });

    // Initial load
    this.loadUsers();
  }

  onInput(input: UserListInput): void {
    switch (input.type) {
      case 'SET_SEARCH_QUERY':
        this.searchSubject.next(input.query);
        break;
      case 'SET_PAGE':
        this._pageIndex.set(input.pageIndex);
        this.loadUsers();
        break;
      case 'SET_PAGE_SIZE':
        this._pageSize.set(input.pageSize);
        this._pageIndex.set(0);
        this.loadUsers();
        break;
      case 'SET_SORT':
        this._sortBy.set(input.sortBy);
        this._sortOrder.set(input.sortOrder);
        this.loadUsers();
        break;
      case 'REFRESH':
        this.loadUsers();
        break;
      case 'SELECT_USER':
        this._effect.next({ type: 'NAVIGATE_TO_USER_DETAIL', userId: input.userId });
        break;
    }
  }

  private async loadUsers(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const result = await this.repository.searchUsers({
        query: this._searchQuery(),
        pageIndex: this._pageIndex(),
        pageSize: this._pageSize(),
        sortBy: this._sortBy() ?? undefined,
        sortOrder: this._sortOrder(),
      });

      this._users.set(result.items);
      this._totalCount.set(result.totalCount);
    } catch (error) {
      this._error.set(error instanceof Error ? error.message : 'Failed to load users');
    } finally {
      this._isLoading.set(false);
    }
  }
}

// presentation/users/user-list.component.ts
import { Component, ChangeDetectionStrategy, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { UserListViewModel } from './user-list.viewmodel';
import { NavGraphService } from '../../core/services/nav-graph.service';
import { PaginationComponent } from '../../shared/components/pagination.component';
import { SearchInputComponent } from '../../shared/components/search-input.component';
import { SortHeaderComponent } from '../../shared/components/sort-header.component';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PaginationComponent,
    SearchInputComponent,
    SortHeaderComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [UserListViewModel],
  template: `
    <div class="user-list-container">
      <header class="list-header">
        <h1>Users</h1>

        <app-search-input
          [value]="vm.output().searchQuery"
          placeholder="Search users..."
          (valueChange)="onSearchChange($event)"
        />
      </header>

      @if (vm.output().error) {
        <div class="error-banner">
          {{ vm.output().error }}
          <button (click)="onRefresh()">Retry</button>
        </div>
      }

      <div class="table-container" [class.loading]="vm.output().isLoading">
        @if (vm.output().isLoading && vm.output().users.length === 0) {
          <div class="loading-skeleton">
            @for (i of [1,2,3,4,5]; track i) {
              <div class="skeleton-row"></div>
            }
          </div>
        } @else {
          <table class="data-table">
            <thead>
              <tr>
                <th>
                  <app-sort-header
                    label="Name"
                    field="name"
                    [activeField]="vm.output().sortBy"
                    [sortOrder]="vm.output().sortOrder"
                    (sort)="onSort($event)"
                  />
                </th>
                <th>
                  <app-sort-header
                    label="Email"
                    field="email"
                    [activeField]="vm.output().sortBy"
                    [sortOrder]="vm.output().sortOrder"
                    (sort)="onSort($event)"
                  />
                </th>
                <th>Department</th>
                <th>Status</th>
                <th>
                  <app-sort-header
                    label="Created"
                    field="createdAt"
                    [activeField]="vm.output().sortBy"
                    [sortOrder]="vm.output().sortOrder"
                    (sort)="onSort($event)"
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              @for (user of vm.output().users; track user.id) {
                <tr (click)="onUserClick(user.id)" class="clickable">
                  <td>{{ user.name }}</td>
                  <td>{{ user.email }}</td>
                  <td>{{ user.department }}</td>
                  <td>
                    <span class="status-badge" [class]="user.status">
                      {{ user.status }}
                    </span>
                  </td>
                  <td>{{ user.createdAt | date:'short' }}</td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="5" class="empty-state">
                    @if (vm.output().searchQuery) {
                      No users found matching "{{ vm.output().searchQuery }}"
                    } @else {
                      No users available
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        }
      </div>

      <footer class="list-footer">
        <div class="page-size-selector">
          <label>Show:</label>
          <select [value]="vm.output().pageSize" (change)="onPageSizeChange($event)">
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>

        <app-pagination
          [pageIndex]="vm.output().pageIndex"
          [totalPages]="vm.output().totalPages"
          [hasNext]="vm.output().hasNextPage"
          [hasPrevious]="vm.output().hasPreviousPage"
          (pageChange)="onPageChange($event)"
        />

        <div class="total-count">
          {{ vm.output().totalCount }} total users
        </div>
      </footer>
    </div>
  `,
  styles: [`
    .user-list-container {
      padding: 1.5rem;
    }

    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
    }

    .table-container {
      position: relative;
      min-height: 400px;
    }

    .table-container.loading::after {
      content: '';
      position: absolute;
      inset: 0;
      background: rgba(255, 255, 255, 0.7);
    }

    .data-table {
      width: 100%;
      border-collapse: collapse;
    }

    .clickable {
      cursor: pointer;
    }

    .clickable:hover {
      background-color: #f5f5f5;
    }

    .status-badge {
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
    }

    .status-badge.active {
      background-color: #d4edda;
      color: #155724;
    }

    .status-badge.inactive {
      background-color: #f8d7da;
      color: #721c24;
    }

    .list-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1.5rem;
    }
  `],
})
export class UserListComponent {
  protected readonly vm = inject(UserListViewModel);
  private readonly navGraph = inject(NavGraphService);
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    this.vm.effect$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(effect => {
        if (effect.type === 'NAVIGATE_TO_USER_DETAIL') {
          this.navGraph.toUserDetail(effect.userId);
        }
      });
  }

  onSearchChange(query: string): void {
    this.vm.onInput({ type: 'SET_SEARCH_QUERY', query });
  }

  onPageChange(pageIndex: number): void {
    this.vm.onInput({ type: 'SET_PAGE', pageIndex });
  }

  onPageSizeChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.vm.onInput({ type: 'SET_PAGE_SIZE', pageSize: parseInt(select.value, 10) });
  }

  onSort(event: { field: string; order: 'asc' | 'desc' }): void {
    this.vm.onInput({ type: 'SET_SORT', sortBy: event.field, sortOrder: event.order });
  }

  onUserClick(userId: string): void {
    this.vm.onInput({ type: 'SELECT_USER', userId });
  }

  onRefresh(): void {
    this.vm.onInput({ type: 'REFRESH' });
  }
}
```

---

## Form with Validation

### Complete Registration Form

```typescript
// presentation/register/register.viewmodel.ts
import { Injectable, signal, computed, inject } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from '../../domain/services/auth.service';

export type RegisterInput =
  | { type: 'SET_NAME'; name: string }
  | { type: 'SET_EMAIL'; email: string }
  | { type: 'SET_PASSWORD'; password: string }
  | { type: 'SET_CONFIRM_PASSWORD'; confirmPassword: string }
  | { type: 'SET_DEPARTMENT'; department: string }
  | { type: 'TOGGLE_TERMS_ACCEPTED' }
  | { type: 'SUBMIT' };

export interface RegisterOutput {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  department: string;
  termsAccepted: boolean;
  isLoading: boolean;
  nameError: string | null;
  emailError: string | null;
  passwordError: string | null;
  confirmPasswordError: string | null;
  departmentError: string | null;
  termsError: string | null;
  canSubmit: boolean;
  passwordStrength: 'weak' | 'medium' | 'strong';
}

export type RegisterEffect =
  | { type: 'NAVIGATE_TO_LOGIN' }
  | { type: 'SHOW_SUCCESS'; message: string }
  | { type: 'SHOW_ERROR'; message: string };

@Injectable()
export class RegisterViewModel {
  private readonly authService = inject(AuthService);

  // State
  private readonly _name = signal('');
  private readonly _email = signal('');
  private readonly _password = signal('');
  private readonly _confirmPassword = signal('');
  private readonly _department = signal('');
  private readonly _termsAccepted = signal(false);
  private readonly _isLoading = signal(false);

  // Touched state
  private readonly _nameTouched = signal(false);
  private readonly _emailTouched = signal(false);
  private readonly _passwordTouched = signal(false);
  private readonly _confirmPasswordTouched = signal(false);
  private readonly _departmentTouched = signal(false);
  private readonly _termsTouched = signal(false);

  // Validation
  private readonly nameError = computed(() => {
    if (!this._nameTouched()) return null;
    const name = this._name();
    if (!name) return 'Name is required';
    if (name.length < 2) return 'Name must be at least 2 characters';
    if (name.length > 50) return 'Name cannot exceed 50 characters';
    return null;
  });

  private readonly emailError = computed(() => {
    if (!this._emailTouched()) return null;
    const email = this._email();
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
    return null;
  });

  private readonly passwordStrength = computed<'weak' | 'medium' | 'strong'>(() => {
    const password = this._password();
    if (!password) return 'weak';

    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score >= 5) return 'strong';
    if (score >= 3) return 'medium';
    return 'weak';
  });

  private readonly passwordError = computed(() => {
    if (!this._passwordTouched()) return null;
    const password = this._password();
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[a-z]/.test(password)) return 'Password must contain lowercase letter';
    if (!/[A-Z]/.test(password)) return 'Password must contain uppercase letter';
    if (!/[0-9]/.test(password)) return 'Password must contain a number';
    return null;
  });

  private readonly confirmPasswordError = computed(() => {
    if (!this._confirmPasswordTouched()) return null;
    const confirmPassword = this._confirmPassword();
    if (!confirmPassword) return 'Please confirm your password';
    if (confirmPassword !== this._password()) return 'Passwords do not match';
    return null;
  });

  private readonly departmentError = computed(() => {
    if (!this._departmentTouched()) return null;
    if (!this._department()) return 'Please select a department';
    return null;
  });

  private readonly termsError = computed(() => {
    if (!this._termsTouched()) return null;
    if (!this._termsAccepted()) return 'You must accept the terms and conditions';
    return null;
  });

  private readonly canSubmit = computed(() => {
    return (
      this._name().length >= 2 &&
      this._email().length > 0 &&
      this._password().length >= 8 &&
      this._confirmPassword() === this._password() &&
      this._department().length > 0 &&
      this._termsAccepted() &&
      !this.nameError() &&
      !this.emailError() &&
      !this.passwordError() &&
      !this.confirmPasswordError() &&
      !this.departmentError() &&
      !this._isLoading()
    );
  });

  // Output
  readonly output = computed<RegisterOutput>(() => ({
    name: this._name(),
    email: this._email(),
    password: this._password(),
    confirmPassword: this._confirmPassword(),
    department: this._department(),
    termsAccepted: this._termsAccepted(),
    isLoading: this._isLoading(),
    nameError: this.nameError(),
    emailError: this.emailError(),
    passwordError: this.passwordError(),
    confirmPasswordError: this.confirmPasswordError(),
    departmentError: this.departmentError(),
    termsError: this.termsError(),
    canSubmit: this.canSubmit(),
    passwordStrength: this.passwordStrength(),
  }));

  // Effect
  private readonly _effect = new Subject<RegisterEffect>();
  readonly effect$ = this._effect.asObservable();

  onInput(input: RegisterInput): void {
    switch (input.type) {
      case 'SET_NAME':
        this._name.set(input.name);
        this._nameTouched.set(true);
        break;
      case 'SET_EMAIL':
        this._email.set(input.email);
        this._emailTouched.set(true);
        break;
      case 'SET_PASSWORD':
        this._password.set(input.password);
        this._passwordTouched.set(true);
        break;
      case 'SET_CONFIRM_PASSWORD':
        this._confirmPassword.set(input.confirmPassword);
        this._confirmPasswordTouched.set(true);
        break;
      case 'SET_DEPARTMENT':
        this._department.set(input.department);
        this._departmentTouched.set(true);
        break;
      case 'TOGGLE_TERMS_ACCEPTED':
        this._termsAccepted.update(v => !v);
        this._termsTouched.set(true);
        break;
      case 'SUBMIT':
        this.handleSubmit();
        break;
    }
  }

  private async handleSubmit(): Promise<void> {
    // Mark all fields as touched
    this._nameTouched.set(true);
    this._emailTouched.set(true);
    this._passwordTouched.set(true);
    this._confirmPasswordTouched.set(true);
    this._departmentTouched.set(true);
    this._termsTouched.set(true);

    if (!this.canSubmit()) return;

    this._isLoading.set(true);
    try {
      await this.authService.register({
        name: this._name(),
        email: this._email(),
        password: this._password(),
        department: this._department(),
      });
      this._effect.next({
        type: 'SHOW_SUCCESS',
        message: 'Registration successful! Please check your email.',
      });
      this._effect.next({ type: 'NAVIGATE_TO_LOGIN' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      this._effect.next({ type: 'SHOW_ERROR', message });
    } finally {
      this._isLoading.set(false);
    }
  }
}
```

---

## Offline-First CRUD Operations

### Task Management with Offline Support

```typescript
// data/local/task-database.ts
import Dexie, { Table } from 'dexie';

export enum SyncStatus {
  SYNCED = 'synced',
  PENDING_CREATE = 'pending_create',
  PENDING_UPDATE = 'pending_update',
  PENDING_DELETE = 'pending_delete',
  FAILED = 'failed',
}

export interface TaskEntity {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  dueDate: number | null;
  priority: 'low' | 'medium' | 'high';
  syncStatus: SyncStatus;
  version: number;
  createdAt: number;
  updatedAt: number;
  deletedAt: number | null;
}

export class TaskDatabase extends Dexie {
  tasks!: Table<TaskEntity>;

  constructor() {
    super('TaskDatabase');
    this.version(1).stores({
      tasks: 'id, syncStatus, updatedAt, deletedAt, [syncStatus+updatedAt]',
    });
  }
}

export const taskDb = new TaskDatabase();

// data/repositories/task-repository.impl.ts
import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { v4 as uuidv4 } from 'uuid';
import { taskDb, TaskEntity, SyncStatus } from '../local/task-database';
import { ApiClient } from '../remote/api-client';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { SyncManager } from '../../core/services/sync-manager.service';

@Injectable({ providedIn: 'root' })
export class TaskRepositoryImpl implements ITaskRepository {
  private readonly apiClient = inject(ApiClient);
  private readonly connectivity = inject(ConnectivityService);
  private readonly syncManager = inject(SyncManager);

  private readonly tasksSubject = new BehaviorSubject<Task[]>([]);

  constructor() {
    this.initialize();
  }

  private async initialize(): Promise<void> {
    await this.refreshFromLocal();

    // Listen for connectivity changes
    this.connectivity.online$.subscribe(isOnline => {
      if (isOnline) {
        this.syncWithRemote();
      }
    });

    // Register with sync manager
    this.syncManager.register('tasks', () => this.syncWithRemote());
  }

  // Read operations - always from local
  getTasks(): Observable<Task[]> {
    return this.tasksSubject.asObservable();
  }

  async getTaskById(id: string): Promise<Task | null> {
    const entity = await taskDb.tasks.get(id);
    if (!entity || entity.deletedAt) return null;
    return this.mapToTask(entity);
  }

  // Create - local first
  async createTask(task: Omit<Task, 'id'>): Promise<Task> {
    const now = Date.now();
    const entity: TaskEntity = {
      id: uuidv4(),
      title: task.title,
      description: task.description,
      completed: task.completed,
      dueDate: task.dueDate?.getTime() ?? null,
      priority: task.priority,
      syncStatus: SyncStatus.PENDING_CREATE,
      version: 1,
      createdAt: now,
      updatedAt: now,
      deletedAt: null,
    };

    await taskDb.tasks.add(entity);
    await this.refreshFromLocal();
    this.syncManager.scheduleSync('tasks');

    return this.mapToTask(entity);
  }

  // Update - local first
  async updateTask(task: Task): Promise<void> {
    const existing = await taskDb.tasks.get(task.id);
    if (!existing) throw new Error('Task not found');

    const entity: TaskEntity = {
      ...existing,
      title: task.title,
      description: task.description,
      completed: task.completed,
      dueDate: task.dueDate?.getTime() ?? null,
      priority: task.priority,
      syncStatus: existing.syncStatus === SyncStatus.PENDING_CREATE
        ? SyncStatus.PENDING_CREATE
        : SyncStatus.PENDING_UPDATE,
      version: existing.version + 1,
      updatedAt: Date.now(),
    };

    await taskDb.tasks.put(entity);
    await this.refreshFromLocal();
    this.syncManager.scheduleSync('tasks');
  }

  // Delete - soft delete locally
  async deleteTask(id: string): Promise<void> {
    const existing = await taskDb.tasks.get(id);
    if (!existing) return;

    if (existing.syncStatus === SyncStatus.PENDING_CREATE) {
      // Never synced, can hard delete
      await taskDb.tasks.delete(id);
    } else {
      // Mark for deletion
      await taskDb.tasks.update(id, {
        syncStatus: SyncStatus.PENDING_DELETE,
        deletedAt: Date.now(),
        updatedAt: Date.now(),
      });
    }

    await this.refreshFromLocal();
    this.syncManager.scheduleSync('tasks');
  }

  // Sync operations
  async syncWithRemote(): Promise<void> {
    if (!this.connectivity.isOnline()) return;

    try {
      // Push local changes
      await this.pushLocalChanges();

      // Pull remote changes
      await this.pullRemoteChanges();

      await this.refreshFromLocal();
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }

  private async pushLocalChanges(): Promise<void> {
    // Handle creates
    const pendingCreates = await taskDb.tasks
      .where('syncStatus')
      .equals(SyncStatus.PENDING_CREATE)
      .toArray();

    for (const entity of pendingCreates) {
      try {
        const response = await firstValueFrom(
          this.apiClient.post<TaskDto>('/tasks', this.mapToDto(entity))
        );
        await taskDb.tasks.update(entity.id, {
          syncStatus: SyncStatus.SYNCED,
        });
      } catch {
        await taskDb.tasks.update(entity.id, {
          syncStatus: SyncStatus.FAILED,
        });
      }
    }

    // Handle updates
    const pendingUpdates = await taskDb.tasks
      .where('syncStatus')
      .equals(SyncStatus.PENDING_UPDATE)
      .toArray();

    for (const entity of pendingUpdates) {
      try {
        await firstValueFrom(
          this.apiClient.put(`/tasks/${entity.id}`, this.mapToDto(entity))
        );
        await taskDb.tasks.update(entity.id, {
          syncStatus: SyncStatus.SYNCED,
        });
      } catch {
        await taskDb.tasks.update(entity.id, {
          syncStatus: SyncStatus.FAILED,
        });
      }
    }

    // Handle deletes
    const pendingDeletes = await taskDb.tasks
      .where('syncStatus')
      .equals(SyncStatus.PENDING_DELETE)
      .toArray();

    for (const entity of pendingDeletes) {
      try {
        await firstValueFrom(this.apiClient.delete(`/tasks/${entity.id}`));
        await taskDb.tasks.delete(entity.id); // Hard delete after sync
      } catch {
        await taskDb.tasks.update(entity.id, {
          syncStatus: SyncStatus.FAILED,
        });
      }
    }
  }

  private async pullRemoteChanges(): Promise<void> {
    const lastSync = localStorage.getItem('tasks_last_sync');
    const since = lastSync ? parseInt(lastSync, 10) : 0;

    const remoteTasks = await firstValueFrom(
      this.apiClient.get<TaskDto[]>('/tasks', {
        params: new HttpParams().set('since', since.toString()),
      })
    );

    await taskDb.transaction('rw', taskDb.tasks, async () => {
      for (const dto of remoteTasks) {
        const local = await taskDb.tasks.get(dto.id);

        // Skip if local has pending changes
        if (local && local.syncStatus !== SyncStatus.SYNCED) {
          continue;
        }

        // Update or insert from remote
        await taskDb.tasks.put({
          id: dto.id,
          title: dto.title,
          description: dto.description,
          completed: dto.completed,
          dueDate: dto.due_date ? new Date(dto.due_date).getTime() : null,
          priority: dto.priority,
          syncStatus: SyncStatus.SYNCED,
          version: dto.version,
          createdAt: new Date(dto.created_at).getTime(),
          updatedAt: new Date(dto.updated_at).getTime(),
          deletedAt: dto.deleted_at ? new Date(dto.deleted_at).getTime() : null,
        });
      }
    });

    localStorage.setItem('tasks_last_sync', Date.now().toString());
  }

  private async refreshFromLocal(): Promise<void> {
    const entities = await taskDb.tasks
      .filter(t => !t.deletedAt)
      .toArray();

    const tasks = entities.map(this.mapToTask);
    this.tasksSubject.next(tasks);
  }

  private mapToTask(entity: TaskEntity): Task {
    return {
      id: entity.id,
      title: entity.title,
      description: entity.description,
      completed: entity.completed,
      dueDate: entity.dueDate ? new Date(entity.dueDate) : null,
      priority: entity.priority,
      syncStatus: entity.syncStatus,
    };
  }

  private mapToDto(entity: TaskEntity): TaskDto {
    return {
      id: entity.id,
      title: entity.title,
      description: entity.description,
      completed: entity.completed,
      due_date: entity.dueDate ? new Date(entity.dueDate).toISOString() : null,
      priority: entity.priority,
      version: entity.version,
    };
  }
}
```

---

## Real-Time Updates with WebSocket

### WebSocket Service with Reconnection

```typescript
// core/services/websocket.service.ts
import { Injectable, inject, signal } from '@angular/core';
import { Subject, Observable, timer, retry, share } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { AuthService } from '../../domain/services/auth.service';

export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: number;
}

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private readonly authService = inject(AuthService);

  private socket$: WebSocketSubject<WebSocketMessage> | null = null;
  private readonly _connected = signal(false);
  private readonly _messages = new Subject<WebSocketMessage>();

  readonly connected = this._connected.asReadonly();
  readonly messages$ = this._messages.asObservable();

  connect(): void {
    if (this.socket$) return;

    const token = this.authService.getToken();
    const wsUrl = `wss://api.example.com/ws?token=${token}`;

    this.socket$ = webSocket<WebSocketMessage>({
      url: wsUrl,
      openObserver: {
        next: () => {
          console.log('WebSocket connected');
          this._connected.set(true);
        },
      },
      closeObserver: {
        next: () => {
          console.log('WebSocket disconnected');
          this._connected.set(false);
          this.scheduleReconnect();
        },
      },
    });

    this.socket$
      .pipe(
        retry({
          count: 5,
          delay: (error, retryCount) => timer(Math.min(1000 * Math.pow(2, retryCount), 30000)),
        }),
        share()
      )
      .subscribe({
        next: message => this._messages.next(message),
        error: error => {
          console.error('WebSocket error:', error);
          this._connected.set(false);
        },
      });
  }

  disconnect(): void {
    this.socket$?.complete();
    this.socket$ = null;
    this._connected.set(false);
  }

  send<T>(type: string, payload: T): void {
    if (!this.socket$ || !this._connected()) {
      console.warn('WebSocket not connected');
      return;
    }

    this.socket$.next({
      type,
      payload,
      timestamp: Date.now(),
    });
  }

  onMessage<T>(type: string): Observable<T> {
    return new Observable(observer => {
      const subscription = this._messages.subscribe(message => {
        if (message.type === type) {
          observer.next(message.payload as T);
        }
      });

      return () => subscription.unsubscribe();
    });
  }

  private scheduleReconnect(): void {
    timer(5000).subscribe(() => {
      if (!this._connected()) {
        console.log('Attempting to reconnect...');
        this.socket$ = null;
        this.connect();
      }
    });
  }
}

// Real-time task updates
@Injectable({ providedIn: 'root' })
export class TaskRealtimeService {
  private readonly wsService = inject(WebSocketService);
  private readonly taskRepository = inject(TaskRepositoryImpl);

  private readonly _taskUpdates = new Subject<TaskUpdate>();
  readonly taskUpdates$ = this._taskUpdates.asObservable();

  constructor() {
    this.setupListeners();
  }

  private setupListeners(): void {
    // Task created
    this.wsService.onMessage<TaskDto>('task.created').subscribe(dto => {
      this._taskUpdates.next({ type: 'created', task: this.mapToTask(dto) });
    });

    // Task updated
    this.wsService.onMessage<TaskDto>('task.updated').subscribe(dto => {
      this._taskUpdates.next({ type: 'updated', task: this.mapToTask(dto) });
    });

    // Task deleted
    this.wsService.onMessage<{ id: string }>('task.deleted').subscribe(data => {
      this._taskUpdates.next({ type: 'deleted', taskId: data.id });
    });
  }

  subscribeToTask(taskId: string): void {
    this.wsService.send('task.subscribe', { taskId });
  }

  unsubscribeFromTask(taskId: string): void {
    this.wsService.send('task.unsubscribe', { taskId });
  }

  private mapToTask(dto: TaskDto): Task {
    return {
      id: dto.id,
      title: dto.title,
      description: dto.description,
      completed: dto.completed,
      dueDate: dto.due_date ? new Date(dto.due_date) : null,
      priority: dto.priority,
    };
  }
}

interface TaskUpdate {
  type: 'created' | 'updated' | 'deleted';
  task?: Task;
  taskId?: string;
}
```

### Component with Real-Time Updates

```typescript
// presentation/tasks/task-board.component.ts
@Component({
  selector: 'app-task-board',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="task-board">
      <header>
        <h1>Task Board</h1>
        <div class="connection-status" [class.connected]="wsConnected()">
          {{ wsConnected() ? 'Connected' : 'Offline' }}
        </div>
      </header>

      @for (task of tasks(); track task.id) {
        <app-task-card
          [task]="task"
          [isUpdating]="updatingTasks().has(task.id)"
          (toggle)="onToggleTask($event)"
          (delete)="onDeleteTask($event)"
        />
      }
    </div>
  `,
})
export class TaskBoardComponent implements OnInit, OnDestroy {
  private readonly taskRepository = inject(TaskRepositoryImpl);
  private readonly realtimeService = inject(TaskRealtimeService);
  private readonly wsService = inject(WebSocketService);
  private readonly destroyRef = inject(DestroyRef);

  readonly tasks = signal<Task[]>([]);
  readonly wsConnected = this.wsService.connected;
  readonly updatingTasks = signal<Set<string>>(new Set());

  ngOnInit(): void {
    // Load initial tasks
    this.taskRepository.getTasks()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(tasks => this.tasks.set(tasks));

    // Handle real-time updates
    this.realtimeService.taskUpdates$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(update => this.handleTaskUpdate(update));

    // Connect to WebSocket
    this.wsService.connect();
  }

  ngOnDestroy(): void {
    // Cleanup handled by takeUntilDestroyed
  }

  private handleTaskUpdate(update: TaskUpdate): void {
    switch (update.type) {
      case 'created':
        if (update.task) {
          this.tasks.update(tasks => [...tasks, update.task!]);
        }
        break;
      case 'updated':
        if (update.task) {
          this.tasks.update(tasks =>
            tasks.map(t => t.id === update.task!.id ? update.task! : t)
          );
          // Remove from updating set
          this.updatingTasks.update(set => {
            const newSet = new Set(set);
            newSet.delete(update.task!.id);
            return newSet;
          });
        }
        break;
      case 'deleted':
        if (update.taskId) {
          this.tasks.update(tasks => tasks.filter(t => t.id !== update.taskId));
        }
        break;
    }
  }

  async onToggleTask(task: Task): Promise<void> {
    // Optimistic update
    this.tasks.update(tasks =>
      tasks.map(t => t.id === task.id ? { ...t, completed: !t.completed } : t)
    );

    // Mark as updating
    this.updatingTasks.update(set => new Set(set).add(task.id));

    try {
      await this.taskRepository.updateTask({
        ...task,
        completed: !task.completed,
      });
    } catch {
      // Revert on failure
      this.tasks.update(tasks =>
        tasks.map(t => t.id === task.id ? task : t)
      );
      this.updatingTasks.update(set => {
        const newSet = new Set(set);
        newSet.delete(task.id);
        return newSet;
      });
    }
  }

  async onDeleteTask(taskId: string): Promise<void> {
    // Optimistic removal
    const originalTasks = this.tasks();
    this.tasks.update(tasks => tasks.filter(t => t.id !== taskId));

    try {
      await this.taskRepository.deleteTask(taskId);
    } catch {
      // Revert on failure
      this.tasks.set(originalTasks);
    }
  }
}
```
