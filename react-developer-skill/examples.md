# React Developer Skill - Code Examples

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
export class AuthService {
  private user: User | null = null;
  private token: AuthToken | null = null;

  constructor(private readonly repository: IAuthRepository) {}

  get currentUser(): User | null {
    return this.user;
  }

  get isAuthenticated(): boolean {
    return !!this.token && !this.isTokenExpired();
  }

  get roles(): string[] {
    return this.user?.roles ?? [];
  }

  async login(credentials: LoginCredentials): Promise<void> {
    const token = await this.repository.login(credentials);
    this.token = token;

    if (credentials.rememberMe) {
      localStorage.setItem('refreshToken', token.refreshToken);
    }

    this.user = await this.repository.getCurrentUser();
  }

  async logout(): Promise<void> {
    await this.repository.logout();
    this.token = null;
    this.user = null;
    localStorage.removeItem('refreshToken');
  }

  getToken(): string | null {
    return this.token?.accessToken ?? null;
  }

  hasRole(role: string): boolean {
    return this.roles.includes(role);
  }

  private isTokenExpired(): boolean {
    if (!this.token) return true;
    return Date.now() >= this.token.expiresAt;
  }

  async tryRestoreSession(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return;

    try {
      const token = await this.repository.refreshToken(refreshToken);
      this.token = token;
      this.user = await this.repository.getCurrentUser();
    } catch {
      localStorage.removeItem('refreshToken');
    }
  }
}
```

### Data Layer

```typescript
// data/repositories/auth-repository.impl.ts
import { AxiosInstance } from 'axios';
import { IAuthRepository, LoginCredentials, AuthToken, User } from '../../domain';

interface AuthTokenDto {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface UserDto {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export class AuthRepositoryImpl implements IAuthRepository {
  constructor(private readonly apiClient: AxiosInstance) {}

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await this.apiClient.post<AuthTokenDto>('/auth/login', credentials);
    return this.mapToAuthToken(response.data);
  }

  async logout(): Promise<void> {
    await this.apiClient.post('/auth/logout', {});
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    const response = await this.apiClient.post<AuthTokenDto>('/auth/refresh', { refreshToken });
    return this.mapToAuthToken(response.data);
  }

  async getCurrentUser(): Promise<User | null> {
    const response = await this.apiClient.get<UserDto>('/auth/me');
    return this.mapToUser(response.data);
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
// presentation/pages/auth/useLoginViewModel.ts
import { useState, useCallback, useMemo, useRef } from 'react';
import { Subject } from 'rxjs';
import { AuthService } from '../../../domain/services/auth.service';

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

export function useLoginViewModel(authService: AuthService) {
  // State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);

  // Effect stream
  const effectRef = useRef(new Subject<LoginEffect>());
  const effect$ = effectRef.current.asObservable();

  // Validation
  const emailError = useMemo(() => {
    if (!emailTouched) return null;
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
    return null;
  }, [email, emailTouched]);

  const passwordError = useMemo(() => {
    if (!passwordTouched) return null;
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    return null;
  }, [password, passwordTouched]);

  const canSubmit = useMemo(() => {
    return (
      email.length > 0 &&
      password.length > 0 &&
      !emailError &&
      !passwordError &&
      !isLoading
    );
  }, [email, password, emailError, passwordError, isLoading]);

  // Output
  const output = useMemo<LoginOutput>(() => ({
    email,
    password,
    rememberMe,
    isLoading,
    emailError,
    passwordError,
    canSubmit,
  }), [email, password, rememberMe, isLoading, emailError, passwordError, canSubmit]);

  // Handlers
  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;

    setIsLoading(true);
    try {
      await authService.login({ email, password, rememberMe });
      effectRef.current.next({ type: 'NAVIGATE_TO_HOME' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      effectRef.current.next({ type: 'SHOW_ERROR', message });
    } finally {
      setIsLoading(false);
    }
  }, [authService, email, password, rememberMe, canSubmit]);

  // Input handler
  const onInput = useCallback((input: LoginInput) => {
    switch (input.type) {
      case 'SET_EMAIL':
        setEmail(input.email);
        setEmailTouched(true);
        break;
      case 'SET_PASSWORD':
        setPassword(input.password);
        setPasswordTouched(true);
        break;
      case 'TOGGLE_REMEMBER_ME':
        setRememberMe(prev => !prev);
        break;
      case 'SUBMIT':
        handleSubmit();
        break;
      case 'FORGOT_PASSWORD':
        effectRef.current.next({ type: 'NAVIGATE_TO_FORGOT_PASSWORD' });
        break;
    }
  }, [handleSubmit]);

  return { output, effect$, onInput };
}

// presentation/pages/auth/LoginPage.tsx
import React, { memo, useEffect } from 'react';
import { useLoginViewModel, LoginInput } from './useLoginViewModel';
import { useAuthService } from '../../../core/hooks/useAuthService';
import { useNavGraph } from '../../../core/hooks/useNavGraph';
import { useToast } from '../../../shared/hooks/useToast';

export const LoginPage = memo(() => {
  const authService = useAuthService();
  const navGraph = useNavGraph();
  const toast = useToast();
  const { output, effect$, onInput } = useLoginViewModel(authService);

  // Handle effects
  useEffect(() => {
    const subscription = effect$.subscribe((effect) => {
      switch (effect.type) {
        case 'NAVIGATE_TO_HOME':
          navGraph.toHome();
          break;
        case 'NAVIGATE_TO_FORGOT_PASSWORD':
          navGraph.toForgotPassword();
          break;
        case 'SHOW_ERROR':
          toast.error(effect.message);
          break;
      }
    });

    return () => subscription.unsubscribe();
  }, [effect$, navGraph, toast]);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onInput({ type: 'SET_EMAIL', email: e.target.value });
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onInput({ type: 'SET_PASSWORD', password: e.target.value });
  };

  const handleRememberMeChange = () => {
    onInput({ type: 'TOGGLE_REMEMBER_ME' });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onInput({ type: 'SUBMIT' });
  };

  const handleForgotPassword = (e: React.MouseEvent) => {
    e.preventDefault();
    onInput({ type: 'FORGOT_PASSWORD' });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>

        <form onSubmit={handleSubmit}>
          {/* Email Field */}
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={output.email}
              onChange={handleEmailChange}
              className={`w-full px-3 py-2 border rounded-md ${
                output.emailError ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter your email"
              autoComplete="email"
            />
            {output.emailError && (
              <span className="text-red-500 text-sm">{output.emailError}</span>
            )}
          </div>

          {/* Password Field */}
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={output.password}
              onChange={handlePasswordChange}
              className={`w-full px-3 py-2 border rounded-md ${
                output.passwordError ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
            {output.passwordError && (
              <span className="text-red-500 text-sm">{output.passwordError}</span>
            )}
          </div>

          {/* Remember Me */}
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={output.rememberMe}
                onChange={handleRememberMeChange}
                className="mr-2"
              />
              <span className="text-sm text-gray-600">Remember me</span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!output.canSubmit}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {output.isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>

          {/* Forgot Password Link */}
          <a
            href="#"
            onClick={handleForgotPassword}
            className="block text-center text-sm text-blue-600 hover:underline mt-4"
          >
            Forgot your password?
          </a>
        </form>
      </div>
    </div>
  );
});

LoginPage.displayName = 'LoginPage';
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
// presentation/pages/users/useUserListViewModel.ts
import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { IUserRepository, SearchParams, User, PaginatedResult } from '../../../domain';

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

export function useUserListViewModel(repository: IUserRepository) {
  // State
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounced search
  const searchSubject = useRef(new Subject<string>());
  const effectRef = useRef(new Subject<UserListEffect>());
  const effect$ = effectRef.current.asObservable();

  // Computed
  const totalPages = useMemo(() => Math.ceil(totalCount / pageSize), [totalCount, pageSize]);
  const hasNextPage = useMemo(() => pageIndex < totalPages - 1, [pageIndex, totalPages]);
  const hasPreviousPage = useMemo(() => pageIndex > 0, [pageIndex]);

  // Output
  const output = useMemo<UserListOutput>(() => ({
    users,
    searchQuery,
    pageIndex,
    pageSize,
    totalCount,
    totalPages,
    hasNextPage,
    hasPreviousPage,
    sortBy,
    sortOrder,
    isLoading,
    error,
  }), [users, searchQuery, pageIndex, pageSize, totalCount, totalPages, hasNextPage, hasPreviousPage, sortBy, sortOrder, isLoading, error]);

  // Load users
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await repository.searchUsers({
        query: searchQuery,
        pageIndex,
        pageSize,
        sortBy: sortBy ?? undefined,
        sortOrder,
      });

      setUsers(result.items);
      setTotalCount(result.totalCount);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  }, [repository, searchQuery, pageIndex, pageSize, sortBy, sortOrder]);

  // Setup debounced search
  useEffect(() => {
    const subscription = searchSubject.current
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((query) => {
        setSearchQuery(query);
        setPageIndex(0);
      });

    return () => subscription.unsubscribe();
  }, []);

  // Load on params change
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Input handler
  const onInput = useCallback((input: UserListInput) => {
    switch (input.type) {
      case 'SET_SEARCH_QUERY':
        searchSubject.current.next(input.query);
        break;
      case 'SET_PAGE':
        setPageIndex(input.pageIndex);
        break;
      case 'SET_PAGE_SIZE':
        setPageSize(input.pageSize);
        setPageIndex(0);
        break;
      case 'SET_SORT':
        setSortBy(input.sortBy);
        setSortOrder(input.sortOrder);
        break;
      case 'REFRESH':
        loadUsers();
        break;
      case 'SELECT_USER':
        effectRef.current.next({ type: 'NAVIGATE_TO_USER_DETAIL', userId: input.userId });
        break;
    }
  }, [loadUsers]);

  return { output, effect$, onInput };
}

// presentation/pages/users/UserListPage.tsx
import React, { memo, useEffect } from 'react';
import { useUserListViewModel } from './useUserListViewModel';
import { useUserRepository } from '../../../core/hooks/useUserRepository';
import { useNavGraph } from '../../../core/hooks/useNavGraph';
import { Pagination } from '../../../shared/components/Pagination';
import { SearchInput } from '../../../shared/components/SearchInput';
import { SortHeader } from '../../../shared/components/SortHeader';

export const UserListPage = memo(() => {
  const repository = useUserRepository();
  const navGraph = useNavGraph();
  const { output, effect$, onInput } = useUserListViewModel(repository);

  // Handle effects
  useEffect(() => {
    const subscription = effect$.subscribe((effect) => {
      if (effect.type === 'NAVIGATE_TO_USER_DETAIL') {
        navGraph.toUserDetail(effect.userId);
      }
    });

    return () => subscription.unsubscribe();
  }, [effect$, navGraph]);

  return (
    <div className="p-6">
      <header className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Users</h1>

        <SearchInput
          value={output.searchQuery}
          placeholder="Search users..."
          onChange={(query) => onInput({ type: 'SET_SEARCH_QUERY', query })}
        />
      </header>

      {output.error && (
        <div className="bg-red-100 text-red-700 p-4 rounded mb-4">
          {output.error}
          <button
            className="ml-4 underline"
            onClick={() => onInput({ type: 'REFRESH' })}
          >
            Retry
          </button>
        </div>
      )}

      <div className={`relative ${output.isLoading ? 'opacity-50' : ''}`}>
        {output.isLoading && output.users.length === 0 ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-gray-200 animate-pulse rounded" />
            ))}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-3">
                  <SortHeader
                    label="Name"
                    field="name"
                    activeField={output.sortBy}
                    sortOrder={output.sortOrder}
                    onSort={(field, order) =>
                      onInput({ type: 'SET_SORT', sortBy: field, sortOrder: order })
                    }
                  />
                </th>
                <th className="text-left p-3">
                  <SortHeader
                    label="Email"
                    field="email"
                    activeField={output.sortBy}
                    sortOrder={output.sortOrder}
                    onSort={(field, order) =>
                      onInput({ type: 'SET_SORT', sortBy: field, sortOrder: order })
                    }
                  />
                </th>
                <th className="text-left p-3">Department</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">
                  <SortHeader
                    label="Created"
                    field="createdAt"
                    activeField={output.sortBy}
                    sortOrder={output.sortOrder}
                    onSort={(field, order) =>
                      onInput({ type: 'SET_SORT', sortBy: field, sortOrder: order })
                    }
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              {output.users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center p-8 text-gray-500">
                    {output.searchQuery
                      ? `No users found matching "${output.searchQuery}"`
                      : 'No users available'}
                  </td>
                </tr>
              ) : (
                output.users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => onInput({ type: 'SELECT_USER', userId: user.id })}
                  >
                    <td className="p-3">{user.name}</td>
                    <td className="p-3">{user.email}</td>
                    <td className="p-3">{user.department}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-1 rounded text-sm ${
                          user.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.status}
                      </span>
                    </td>
                    <td className="p-3">
                      {new Date(user.createdAt).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      <footer className="flex justify-between items-center mt-6">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Show:</label>
          <select
            value={output.pageSize}
            onChange={(e) =>
              onInput({ type: 'SET_PAGE_SIZE', pageSize: parseInt(e.target.value, 10) })
            }
            className="border rounded px-2 py-1"
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>

        <Pagination
          pageIndex={output.pageIndex}
          totalPages={output.totalPages}
          hasNext={output.hasNextPage}
          hasPrevious={output.hasPreviousPage}
          onPageChange={(pageIndex) => onInput({ type: 'SET_PAGE', pageIndex })}
        />

        <div className="text-sm text-gray-600">
          {output.totalCount} total users
        </div>
      </footer>
    </div>
  );
});

UserListPage.displayName = 'UserListPage';
```

---

## Form with Validation

### Complete Registration Form

```typescript
// presentation/pages/auth/useRegisterViewModel.ts
import { useState, useCallback, useMemo, useRef } from 'react';
import { Subject } from 'rxjs';
import { AuthService } from '../../../domain/services/auth.service';

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

export function useRegisterViewModel(authService: AuthService) {
  // State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [department, setDepartment] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Touched state
  const [nameTouched, setNameTouched] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);
  const [departmentTouched, setDepartmentTouched] = useState(false);
  const [termsTouched, setTermsTouched] = useState(false);

  // Effect stream
  const effectRef = useRef(new Subject<RegisterEffect>());
  const effect$ = effectRef.current.asObservable();

  // Validation
  const nameError = useMemo(() => {
    if (!nameTouched) return null;
    if (!name) return 'Name is required';
    if (name.length < 2) return 'Name must be at least 2 characters';
    if (name.length > 50) return 'Name cannot exceed 50 characters';
    return null;
  }, [name, nameTouched]);

  const emailError = useMemo(() => {
    if (!emailTouched) return null;
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
    return null;
  }, [email, emailTouched]);

  const passwordStrength = useMemo<'weak' | 'medium' | 'strong'>(() => {
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
  }, [password]);

  const passwordError = useMemo(() => {
    if (!passwordTouched) return null;
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[a-z]/.test(password)) return 'Password must contain lowercase letter';
    if (!/[A-Z]/.test(password)) return 'Password must contain uppercase letter';
    if (!/[0-9]/.test(password)) return 'Password must contain a number';
    return null;
  }, [password, passwordTouched]);

  const confirmPasswordError = useMemo(() => {
    if (!confirmPasswordTouched) return null;
    if (!confirmPassword) return 'Please confirm your password';
    if (confirmPassword !== password) return 'Passwords do not match';
    return null;
  }, [confirmPassword, password, confirmPasswordTouched]);

  const departmentError = useMemo(() => {
    if (!departmentTouched) return null;
    if (!department) return 'Please select a department';
    return null;
  }, [department, departmentTouched]);

  const termsError = useMemo(() => {
    if (!termsTouched) return null;
    if (!termsAccepted) return 'You must accept the terms and conditions';
    return null;
  }, [termsAccepted, termsTouched]);

  const canSubmit = useMemo(() => {
    return (
      name.length >= 2 &&
      email.length > 0 &&
      password.length >= 8 &&
      confirmPassword === password &&
      department.length > 0 &&
      termsAccepted &&
      !nameError &&
      !emailError &&
      !passwordError &&
      !confirmPasswordError &&
      !departmentError &&
      !isLoading
    );
  }, [name, email, password, confirmPassword, department, termsAccepted, nameError, emailError, passwordError, confirmPasswordError, departmentError, isLoading]);

  // Output
  const output = useMemo<RegisterOutput>(() => ({
    name,
    email,
    password,
    confirmPassword,
    department,
    termsAccepted,
    isLoading,
    nameError,
    emailError,
    passwordError,
    confirmPasswordError,
    departmentError,
    termsError,
    canSubmit,
    passwordStrength,
  }), [name, email, password, confirmPassword, department, termsAccepted, isLoading, nameError, emailError, passwordError, confirmPasswordError, departmentError, termsError, canSubmit, passwordStrength]);

  // Handlers
  const handleSubmit = useCallback(async () => {
    // Mark all fields as touched
    setNameTouched(true);
    setEmailTouched(true);
    setPasswordTouched(true);
    setConfirmPasswordTouched(true);
    setDepartmentTouched(true);
    setTermsTouched(true);

    if (!canSubmit) return;

    setIsLoading(true);
    try {
      await authService.register({ name, email, password, department });
      effectRef.current.next({
        type: 'SHOW_SUCCESS',
        message: 'Registration successful! Please check your email.',
      });
      effectRef.current.next({ type: 'NAVIGATE_TO_LOGIN' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      effectRef.current.next({ type: 'SHOW_ERROR', message });
    } finally {
      setIsLoading(false);
    }
  }, [authService, name, email, password, department, canSubmit]);

  // Input handler
  const onInput = useCallback((input: RegisterInput) => {
    switch (input.type) {
      case 'SET_NAME':
        setName(input.name);
        setNameTouched(true);
        break;
      case 'SET_EMAIL':
        setEmail(input.email);
        setEmailTouched(true);
        break;
      case 'SET_PASSWORD':
        setPassword(input.password);
        setPasswordTouched(true);
        break;
      case 'SET_CONFIRM_PASSWORD':
        setConfirmPassword(input.confirmPassword);
        setConfirmPasswordTouched(true);
        break;
      case 'SET_DEPARTMENT':
        setDepartment(input.department);
        setDepartmentTouched(true);
        break;
      case 'TOGGLE_TERMS_ACCEPTED':
        setTermsAccepted(prev => !prev);
        setTermsTouched(true);
        break;
      case 'SUBMIT':
        handleSubmit();
        break;
    }
  }, [handleSubmit]);

  return { output, effect$, onInput };
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
import { v4 as uuidv4 } from 'uuid';
import { taskDb, TaskEntity, SyncStatus } from '../local/task-database';
import { ITaskRepository, Task, CreateTaskDto } from '../../domain';
import { apiClient } from '../remote/api-client';

export class TaskRepositoryImpl implements ITaskRepository {
  private listeners: Set<(tasks: Task[]) => void> = new Set();

  constructor(private readonly syncManager: SyncManager) {
    this.initialize();
  }

  private async initialize(): Promise<void> {
    // Register with sync manager
    this.syncManager.register('tasks', () => this.syncWithRemote());
  }

  // Subscribe to task changes
  subscribe(callback: (tasks: Task[]) => void): () => void {
    this.listeners.add(callback);
    this.refreshFromLocal();
    return () => this.listeners.delete(callback);
  }

  // Create - local first
  async createTask(data: CreateTaskDto): Promise<Task> {
    const now = Date.now();
    const entity: TaskEntity = {
      id: uuidv4(),
      title: data.title,
      description: data.description,
      completed: false,
      dueDate: data.dueDate?.getTime() ?? null,
      priority: data.priority,
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
      syncStatus:
        existing.syncStatus === SyncStatus.PENDING_CREATE
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
    try {
      await this.pushLocalChanges();
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
        await apiClient.post('/tasks', this.mapToDto(entity));
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
        await apiClient.put(`/tasks/${entity.id}`, this.mapToDto(entity));
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
        await apiClient.delete(`/tasks/${entity.id}`);
        await taskDb.tasks.delete(entity.id);
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

    const response = await apiClient.get<TaskDto[]>('/tasks', {
      params: { since },
    });

    await taskDb.transaction('rw', taskDb.tasks, async () => {
      for (const dto of response.data) {
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
    const entities = await taskDb.tasks.filter((t) => !t.deletedAt).toArray();
    const tasks = entities.map(this.mapToTask);
    this.listeners.forEach((callback) => callback(tasks));
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

### WebSocket Hook with Reconnection

```typescript
// core/hooks/useWebSocket.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { Subject, Observable, timer, retry } from 'rxjs';

export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: number;
}

interface UseWebSocketResult {
  connected: boolean;
  send: <T>(type: string, payload: T) => void;
  onMessage: <T>(type: string) => Observable<T>;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(url: string, token: string | null): UseWebSocketResult {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef(new Subject<WebSocketMessage>());
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (socketRef.current || !token) return;

    const wsUrl = `${url}?token=${token}`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      socketRef.current = null;

      // Schedule reconnect
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        messagesRef.current.next(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    socketRef.current = socket;
  }, [url, token]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    socketRef.current?.close();
    socketRef.current = null;
    setConnected(false);
  }, []);

  const send = useCallback(<T,>(type: string, payload: T) => {
    if (!socketRef.current || !connected) {
      console.warn('WebSocket not connected');
      return;
    }

    socketRef.current.send(
      JSON.stringify({
        type,
        payload,
        timestamp: Date.now(),
      })
    );
  }, [connected]);

  const onMessage = useCallback(<T,>(type: string): Observable<T> => {
    return new Observable((observer) => {
      const subscription = messagesRef.current.subscribe((message) => {
        if (message.type === type) {
          observer.next(message.payload as T);
        }
      });

      return () => subscription.unsubscribe();
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { connected, send, onMessage, connect, disconnect };
}

// presentation/pages/tasks/TaskBoardPage.tsx
import React, { memo, useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../../core/hooks/useWebSocket';
import { useTaskRepository } from '../../../core/hooks/useTaskRepository';
import { useAuth } from '../../../core/hooks/useAuth';
import { Task } from '../../../domain';
import { TaskCard } from './components/TaskCard';

interface TaskUpdate {
  type: 'created' | 'updated' | 'deleted';
  task?: Task;
  taskId?: string;
}

export const TaskBoardPage = memo(() => {
  const { token } = useAuth();
  const taskRepository = useTaskRepository();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [updatingTasks, setUpdatingTasks] = useState<Set<string>>(new Set());

  const { connected, send, onMessage, connect } = useWebSocket(
    import.meta.env.VITE_WS_URL,
    token
  );

  // Load initial tasks
  useEffect(() => {
    const unsubscribe = taskRepository.subscribe(setTasks);
    return unsubscribe;
  }, [taskRepository]);

  // Connect to WebSocket
  useEffect(() => {
    if (token) {
      connect();
    }
  }, [token, connect]);

  // Handle real-time updates
  useEffect(() => {
    const createdSub = onMessage<Task>('task.created').subscribe((task) => {
      setTasks((prev) => [...prev, task]);
    });

    const updatedSub = onMessage<Task>('task.updated').subscribe((task) => {
      setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)));
      setUpdatingTasks((prev) => {
        const newSet = new Set(prev);
        newSet.delete(task.id);
        return newSet;
      });
    });

    const deletedSub = onMessage<{ id: string }>('task.deleted').subscribe(({ id }) => {
      setTasks((prev) => prev.filter((t) => t.id !== id));
    });

    return () => {
      createdSub.unsubscribe();
      updatedSub.unsubscribe();
      deletedSub.unsubscribe();
    };
  }, [onMessage]);

  const handleToggleTask = useCallback(
    async (task: Task) => {
      // Optimistic update
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, completed: !t.completed } : t))
      );

      // Mark as updating
      setUpdatingTasks((prev) => new Set(prev).add(task.id));

      try {
        await taskRepository.updateTask({
          ...task,
          completed: !task.completed,
        });
      } catch {
        // Revert on failure
        setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)));
        setUpdatingTasks((prev) => {
          const newSet = new Set(prev);
          newSet.delete(task.id);
          return newSet;
        });
      }
    },
    [taskRepository]
  );

  const handleDeleteTask = useCallback(
    async (taskId: string) => {
      // Optimistic removal
      const originalTasks = tasks;
      setTasks((prev) => prev.filter((t) => t.id !== taskId));

      try {
        await taskRepository.deleteTask(taskId);
      } catch {
        // Revert on failure
        setTasks(originalTasks);
      }
    },
    [taskRepository, tasks]
  );

  return (
    <div className="p-6">
      <header className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Task Board</h1>
        <div
          className={`flex items-center gap-2 ${
            connected ? 'text-green-600' : 'text-gray-500'
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-green-600' : 'bg-gray-500'
            }`}
          />
          {connected ? 'Connected' : 'Offline'}
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            isUpdating={updatingTasks.has(task.id)}
            onToggle={() => handleToggleTask(task)}
            onDelete={() => handleDeleteTask(task.id)}
          />
        ))}
      </div>
    </div>
  );
});

TaskBoardPage.displayName = 'TaskBoardPage';
```
