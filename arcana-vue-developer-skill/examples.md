# Vue Developer Skill - Code Examples

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
// domain/entities/auth.entity.ts
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

// domain/services/auth.service.ts
export interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<AuthToken>;
  logout(): Promise<void>;
  refreshToken(refreshToken: string): Promise<AuthToken>;
  getCurrentUser(): Promise<User | null>;
}

export interface IAuthService {
  readonly currentUser: User | null;
  readonly isAuthenticated: boolean;
  login(credentials: LoginCredentials): Promise<void>;
  logout(): Promise<void>;
  getToken(): string | null;
  tryRestoreSession(): Promise<void>;
}

// domain/services/auth.service.impl.ts
import { injectable, inject } from 'inversify';
import { TOKENS } from '@/core/di/tokens';

@injectable()
export class AuthServiceImpl implements IAuthService {
  private user: User | null = null;
  private token: AuthToken | null = null;

  constructor(
    @inject(TOKENS.AuthRepository) private readonly repository: IAuthRepository
  ) {}

  get currentUser(): User | null {
    return this.user;
  }

  get isAuthenticated(): boolean {
    return !!this.token && !this.isTokenExpired();
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

  private isTokenExpired(): boolean {
    if (!this.token) return true;
    return Date.now() >= this.token.expiresAt;
  }
}
```

### Data Layer

```typescript
// data/dtos/auth.dto.ts
export interface AuthTokenDto {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface UserDto {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

// data/mappers/auth.mapper.ts
import type { AuthToken, User } from '@/domain/entities/auth.entity';
import type { AuthTokenDto, UserDto } from '@/data/dtos/auth.dto';

export class AuthMapper {
  static toAuthToken(dto: AuthTokenDto): AuthToken {
    return {
      accessToken: dto.access_token,
      refreshToken: dto.refresh_token,
      expiresAt: Date.now() + dto.expires_in * 1000,
    };
  }

  static toUser(dto: UserDto): User {
    return {
      id: dto.id,
      email: dto.email,
      name: dto.name,
      roles: dto.roles,
    };
  }
}

// data/repositories/auth.repository.impl.ts
import { injectable, inject } from 'inversify';
import type { AxiosInstance } from 'axios';
import { TOKENS } from '@/core/di/tokens';
import type { IAuthRepository, LoginCredentials, AuthToken, User } from '@/domain/services/auth.service';
import type { AuthTokenDto, UserDto } from '@/data/dtos/auth.dto';
import { AuthMapper } from '@/data/mappers/auth.mapper';

@injectable()
export class AuthRepositoryImpl implements IAuthRepository {
  constructor(
    @inject(TOKENS.ApiClient) private readonly apiClient: AxiosInstance
  ) {}

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await this.apiClient.post<AuthTokenDto>('/auth/login', credentials);
    return AuthMapper.toAuthToken(response.data);
  }

  async logout(): Promise<void> {
    await this.apiClient.post('/auth/logout', {});
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    const response = await this.apiClient.post<AuthTokenDto>('/auth/refresh', { refreshToken });
    return AuthMapper.toAuthToken(response.data);
  }

  async getCurrentUser(): Promise<User | null> {
    const response = await this.apiClient.get<UserDto>('/auth/me');
    return AuthMapper.toUser(response.data);
  }
}
```

### Presentation Layer

```typescript
// presentation/view-models/useLoginViewModel.ts
import { ref, computed } from 'vue';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';
import type { IAuthService } from '@/domain/services/auth.service';

export type LoginEffect =
  | { type: 'NAVIGATE_TO_HOME' }
  | { type: 'NAVIGATE_TO_FORGOT_PASSWORD' }
  | { type: 'SHOW_ERROR'; message: string };

export function useLoginViewModel() {
  const authService = useInject<IAuthService>(TOKENS.AuthService);

  // --- Models ---
  const email = ref('');
  const password = ref('');
  const rememberMe = ref(false);

  // --- Internal state ---
  const isLoading = ref(false);
  const emailTouched = ref(false);
  const passwordTouched = ref(false);

  // --- Effects ---
  const effectCallbacks: Array<(effect: LoginEffect) => void> = [];
  const onEffect = (cb: (effect: LoginEffect) => void) => { effectCallbacks.push(cb); };
  const emitEffect = (effect: LoginEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };

  // --- Outputs ---
  const emailError = computed(() => {
    if (!emailTouched.value) return null;
    if (!email.value) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return 'Invalid email format';
    return null;
  });

  const passwordError = computed(() => {
    if (!passwordTouched.value) return null;
    if (!password.value) return 'Password is required';
    if (password.value.length < 8) return 'Password must be at least 8 characters';
    return null;
  });

  const canSubmit = computed(() =>
    email.value.length > 0 &&
    password.value.length > 0 &&
    !emailError.value &&
    !passwordError.value &&
    !isLoading.value
  );

  const outputs = {
    isLoading: computed(() => isLoading.value),
    emailError,
    passwordError,
    canSubmit,
  };

  // --- Inputs ---
  const inputs = {
    touchEmail() { emailTouched.value = true; },
    touchPassword() { passwordTouched.value = true; },
    toggleRememberMe() { rememberMe.value = !rememberMe.value; },

    async submit() {
      emailTouched.value = true;
      passwordTouched.value = true;
      if (!canSubmit.value) return;

      isLoading.value = true;
      try {
        await authService.login({
          email: email.value,
          password: password.value,
          rememberMe: rememberMe.value,
        });
        emitEffect({ type: 'NAVIGATE_TO_HOME' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Login failed';
        emitEffect({ type: 'SHOW_ERROR', message });
      } finally {
        isLoading.value = false;
      }
    },

    forgotPassword() {
      emitEffect({ type: 'NAVIGATE_TO_FORGOT_PASSWORD' });
    },
  };

  return { models: { email, password, rememberMe }, outputs, inputs, onEffect };
}
```

```vue
<!-- presentation/features/auth/LoginView.vue -->
<script setup lang="ts">
import { useLoginViewModel } from '@/presentation/view-models/useLoginViewModel';
import { useNavGraph } from '@/router/nav-graph';
import { useToast } from '@/presentation/composables/useToast';

const vm = useLoginViewModel();
const navGraph = useNavGraph();
const toast = useToast();

vm.onEffect((effect) => {
  switch (effect.type) {
    case 'NAVIGATE_TO_HOME':
      navGraph.home.navigate();
      break;
    case 'NAVIGATE_TO_FORGOT_PASSWORD':
      navGraph.auth.toForgotPassword();
      break;
    case 'SHOW_ERROR':
      toast.error(effect.message);
      break;
  }
});
</script>

<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light p-4">
    <div class="card shadow" style="max-width: 28rem; width: 100%;">
      <div class="card-body p-4">
        <h1 class="card-title text-center mb-4 h4 fw-bold">Sign In</h1>

        <form @submit.prevent="vm.inputs.submit()">
          <!-- Email -->
          <div class="mb-3">
            <label for="email" class="form-label">Email</label>
            <input
              id="email"
              v-model="vm.models.email.value"
              type="email"
              class="form-control"
              :class="{ 'is-invalid': vm.outputs.emailError.value }"
              placeholder="Enter your email"
              autocomplete="email"
              @blur="vm.inputs.touchEmail()"
            />
            <div v-if="vm.outputs.emailError.value" class="invalid-feedback">
              {{ vm.outputs.emailError.value }}
            </div>
          </div>

          <!-- Password -->
          <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input
              id="password"
              v-model="vm.models.password.value"
              type="password"
              class="form-control"
              :class="{ 'is-invalid': vm.outputs.passwordError.value }"
              placeholder="Enter your password"
              autocomplete="current-password"
              @blur="vm.inputs.touchPassword()"
            />
            <div v-if="vm.outputs.passwordError.value" class="invalid-feedback">
              {{ vm.outputs.passwordError.value }}
            </div>
          </div>

          <!-- Remember Me -->
          <div class="mb-3 form-check">
            <input
              id="rememberMe"
              type="checkbox"
              class="form-check-input"
              :checked="vm.models.rememberMe.value"
              @change="vm.inputs.toggleRememberMe()"
            />
            <label for="rememberMe" class="form-check-label text-muted">
              Remember me
            </label>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            class="btn btn-primary w-100"
            :disabled="!vm.outputs.canSubmit.value"
          >
            <span v-if="vm.outputs.isLoading.value">
              <span class="spinner-border spinner-border-sm me-1" role="status"></span>
              Signing in...
            </span>
            <span v-else>Sign In</span>
          </button>

          <!-- Forgot Password -->
          <div class="text-center mt-3">
            <a href="#" class="text-decoration-none" @click.prevent="vm.inputs.forgotPassword()">
              Forgot your password?
            </a>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
```

---

## List with Search and Pagination

### Domain Layer

```typescript
// domain/entities/pagination.entity.ts
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

// domain/entities/user.entity.ts
export interface User {
  id: string;
  name: string;
  email: string;
  department: string;
  status: 'active' | 'inactive';
  createdAt: Date;
}

// domain/services/user.service.ts
export interface IUserRepository {
  searchUsers(params: SearchParams): Promise<PaginatedResult<User>>;
  getUserById(id: string): Promise<User | null>;
}
```

### Presentation Layer

```typescript
// presentation/view-models/useUserListViewModel.ts
import { ref, computed, watch } from 'vue';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';
import type { IUserRepository, User, SearchParams } from '@/domain/services/user.service';
import { useDebouncedRef } from '@/presentation/composables/useDebouncedRef';

export type UserListEffect =
  | { type: 'NAVIGATE_TO_USER_DETAIL'; userId: string };

export function useUserListViewModel() {
  const repository = useInject<IUserRepository>(TOKENS.UserRepository);

  // --- Models ---
  const searchQuery = useDebouncedRef('', 300);

  // --- Internal state ---
  const users = ref<User[]>([]);
  const pageIndex = ref(0);
  const pageSize = ref(10);
  const totalCount = ref(0);
  const sortBy = ref<string | null>(null);
  const sortOrder = ref<'asc' | 'desc'>('asc');
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Effects ---
  const effectCallbacks: Array<(effect: UserListEffect) => void> = [];
  const onEffect = (cb: (effect: UserListEffect) => void) => { effectCallbacks.push(cb); };
  const emitEffect = (effect: UserListEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };

  // --- Outputs ---
  const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value));
  const hasNextPage = computed(() => pageIndex.value < totalPages.value - 1);
  const hasPreviousPage = computed(() => pageIndex.value > 0);

  const outputs = {
    users: computed(() => users.value),
    searchQuery: computed(() => searchQuery.value),
    pageIndex: computed(() => pageIndex.value),
    pageSize: computed(() => pageSize.value),
    totalCount: computed(() => totalCount.value),
    totalPages,
    hasNextPage,
    hasPreviousPage,
    sortBy: computed(() => sortBy.value),
    sortOrder: computed(() => sortOrder.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
  };

  // --- Data loading ---
  const loadUsers = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const result = await repository.searchUsers({
        query: searchQuery.value,
        pageIndex: pageIndex.value,
        pageSize: pageSize.value,
        sortBy: sortBy.value ?? undefined,
        sortOrder: sortOrder.value,
      });

      users.value = result.items;
      totalCount.value = result.totalCount;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load users';
    } finally {
      isLoading.value = false;
    }
  };

  // Watch for parameter changes and reload
  watch(
    [() => searchQuery.value, pageIndex, pageSize, sortBy, sortOrder],
    () => { loadUsers(); },
    { immediate: true }
  );

  // Reset page on search
  watch(() => searchQuery.value, () => { pageIndex.value = 0; });

  // --- Inputs ---
  const inputs = {
    setPage(index: number) { pageIndex.value = index; },
    setPageSize(size: number) { pageSize.value = size; pageIndex.value = 0; },
    setSort(field: string, order: 'asc' | 'desc') { sortBy.value = field; sortOrder.value = order; },
    refresh() { loadUsers(); },
    selectUser(userId: string) { emitEffect({ type: 'NAVIGATE_TO_USER_DETAIL', userId }); },
  };

  return { models: { searchQuery }, outputs, inputs, onEffect };
}
```

```vue
<!-- presentation/features/users/UserListView.vue -->
<script setup lang="ts">
import { useUserListViewModel } from '@/presentation/view-models/useUserListViewModel';
import { useNavGraph } from '@/router/nav-graph';

const vm = useUserListViewModel();
const navGraph = useNavGraph();

vm.onEffect((effect) => {
  if (effect.type === 'NAVIGATE_TO_USER_DETAIL') {
    navGraph.users.toDetail(effect.userId);
  }
});
</script>

<template>
  <div class="container-fluid p-4">
    <header class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h3 fw-bold mb-0">Users</h1>
      <div class="input-group" style="max-width: 300px;">
        <span class="input-group-text"><i class="bi bi-search"></i></span>
        <input
          v-model="vm.models.searchQuery.value"
          type="text"
          class="form-control"
          placeholder="Search users..."
        />
      </div>
    </header>

    <!-- Error -->
    <div v-if="vm.outputs.error.value" class="alert alert-danger d-flex align-items-center">
      {{ vm.outputs.error.value }}
      <button class="btn btn-link ms-auto" @click="vm.inputs.refresh()">Retry</button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="vm.outputs.isLoading.value && vm.outputs.users.value.length === 0">
      <div v-for="i in 5" :key="i" class="placeholder-glow mb-3">
        <span class="placeholder col-12" style="height: 48px;"></span>
      </div>
    </div>

    <!-- Table -->
    <div v-else :class="{ 'opacity-50': vm.outputs.isLoading.value }">
      <table class="table table-hover">
        <thead>
          <tr>
            <th class="cursor-pointer" @click="vm.inputs.setSort('name', 'asc')">Name</th>
            <th class="cursor-pointer" @click="vm.inputs.setSort('email', 'asc')">Email</th>
            <th>Department</th>
            <th>Status</th>
            <th class="cursor-pointer" @click="vm.inputs.setSort('createdAt', 'desc')">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="vm.outputs.users.value.length === 0">
            <td colspan="5" class="text-center text-muted p-5">
              {{ vm.outputs.searchQuery.value
                ? `No users found matching "${vm.outputs.searchQuery.value}"`
                : 'No users available' }}
            </td>
          </tr>
          <tr
            v-for="user in vm.outputs.users.value"
            :key="user.id"
            class="cursor-pointer"
            @click="vm.inputs.selectUser(user.id)"
          >
            <td>{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.department }}</td>
            <td>
              <span
                class="badge"
                :class="user.status === 'active' ? 'bg-success' : 'bg-danger'"
              >
                {{ user.status }}
              </span>
            </td>
            <td>{{ new Date(user.createdAt).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <footer class="d-flex justify-content-between align-items-center mt-4">
      <div class="d-flex align-items-center gap-2">
        <label class="form-label mb-0 text-muted small">Show:</label>
        <select
          class="form-select form-select-sm"
          style="width: auto;"
          :value="vm.outputs.pageSize.value"
          @change="vm.inputs.setPageSize(Number(($event.target as HTMLSelectElement).value))"
        >
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>

      <nav aria-label="Page navigation">
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item" :class="{ disabled: !vm.outputs.hasPreviousPage.value }">
            <a class="page-link" href="#" @click.prevent="vm.inputs.setPage(vm.outputs.pageIndex.value - 1)">Previous</a>
          </li>
          <li class="page-item active">
            <span class="page-link">{{ vm.outputs.pageIndex.value + 1 }} / {{ vm.outputs.totalPages.value }}</span>
          </li>
          <li class="page-item" :class="{ disabled: !vm.outputs.hasNextPage.value }">
            <a class="page-link" href="#" @click.prevent="vm.inputs.setPage(vm.outputs.pageIndex.value + 1)">Next</a>
          </li>
        </ul>
      </nav>

      <div class="text-muted small">
        {{ vm.outputs.totalCount.value }} total users
      </div>
    </footer>
  </div>
</template>
```

---

## Form with Validation

### Complete Registration Form

```typescript
// presentation/view-models/useRegisterViewModel.ts
import { ref, computed } from 'vue';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';
import type { IAuthService } from '@/domain/services/auth.service';

export type RegisterEffect =
  | { type: 'NAVIGATE_TO_LOGIN' }
  | { type: 'SHOW_SUCCESS'; message: string }
  | { type: 'SHOW_ERROR'; message: string };

export function useRegisterViewModel() {
  const authService = useInject<IAuthService>(TOKENS.AuthService);

  // --- Models ---
  const name = ref('');
  const email = ref('');
  const password = ref('');
  const confirmPassword = ref('');
  const department = ref('');
  const termsAccepted = ref(false);

  // --- Touched state ---
  const nameTouched = ref(false);
  const emailTouched = ref(false);
  const passwordTouched = ref(false);
  const confirmPasswordTouched = ref(false);
  const departmentTouched = ref(false);
  const termsTouched = ref(false);

  // --- Internal state ---
  const isLoading = ref(false);

  // --- Effects ---
  const effectCallbacks: Array<(effect: RegisterEffect) => void> = [];
  const onEffect = (cb: (effect: RegisterEffect) => void) => { effectCallbacks.push(cb); };
  const emitEffect = (effect: RegisterEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };

  // --- Validation ---
  const nameError = computed(() => {
    if (!nameTouched.value) return null;
    if (!name.value) return 'Name is required';
    if (name.value.length < 2) return 'Name must be at least 2 characters';
    if (name.value.length > 50) return 'Name cannot exceed 50 characters';
    return null;
  });

  const emailError = computed(() => {
    if (!emailTouched.value) return null;
    if (!email.value) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return 'Invalid email format';
    return null;
  });

  const passwordStrength = computed<'weak' | 'medium' | 'strong'>(() => {
    if (!password.value) return 'weak';
    let score = 0;
    if (password.value.length >= 8) score++;
    if (password.value.length >= 12) score++;
    if (/[a-z]/.test(password.value)) score++;
    if (/[A-Z]/.test(password.value)) score++;
    if (/[0-9]/.test(password.value)) score++;
    if (/[^a-zA-Z0-9]/.test(password.value)) score++;
    if (score >= 5) return 'strong';
    if (score >= 3) return 'medium';
    return 'weak';
  });

  const passwordError = computed(() => {
    if (!passwordTouched.value) return null;
    if (!password.value) return 'Password is required';
    if (password.value.length < 8) return 'Password must be at least 8 characters';
    if (!/[a-z]/.test(password.value)) return 'Password must contain a lowercase letter';
    if (!/[A-Z]/.test(password.value)) return 'Password must contain an uppercase letter';
    if (!/[0-9]/.test(password.value)) return 'Password must contain a number';
    return null;
  });

  const confirmPasswordError = computed(() => {
    if (!confirmPasswordTouched.value) return null;
    if (!confirmPassword.value) return 'Please confirm your password';
    if (confirmPassword.value !== password.value) return 'Passwords do not match';
    return null;
  });

  const departmentError = computed(() => {
    if (!departmentTouched.value) return null;
    if (!department.value) return 'Please select a department';
    return null;
  });

  const termsError = computed(() => {
    if (!termsTouched.value) return null;
    if (!termsAccepted.value) return 'You must accept the terms and conditions';
    return null;
  });

  const canSubmit = computed(() =>
    name.value.length >= 2 &&
    email.value.length > 0 &&
    password.value.length >= 8 &&
    confirmPassword.value === password.value &&
    department.value.length > 0 &&
    termsAccepted.value &&
    !nameError.value &&
    !emailError.value &&
    !passwordError.value &&
    !confirmPasswordError.value &&
    !departmentError.value &&
    !isLoading.value
  );

  // --- Outputs ---
  const outputs = {
    isLoading: computed(() => isLoading.value),
    nameError,
    emailError,
    passwordError,
    confirmPasswordError,
    departmentError,
    termsError,
    canSubmit,
    passwordStrength,
  };

  // --- Inputs ---
  const inputs = {
    touchName() { nameTouched.value = true; },
    touchEmail() { emailTouched.value = true; },
    touchPassword() { passwordTouched.value = true; },
    touchConfirmPassword() { confirmPasswordTouched.value = true; },
    touchDepartment() { departmentTouched.value = true; },
    toggleTerms() { termsAccepted.value = !termsAccepted.value; termsTouched.value = true; },

    async submit() {
      // Mark all touched
      nameTouched.value = true;
      emailTouched.value = true;
      passwordTouched.value = true;
      confirmPasswordTouched.value = true;
      departmentTouched.value = true;
      termsTouched.value = true;

      if (!canSubmit.value) return;

      isLoading.value = true;
      try {
        await authService.register({
          name: name.value,
          email: email.value,
          password: password.value,
          department: department.value,
        });
        emitEffect({ type: 'SHOW_SUCCESS', message: 'Registration successful! Please check your email.' });
        emitEffect({ type: 'NAVIGATE_TO_LOGIN' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Registration failed';
        emitEffect({ type: 'SHOW_ERROR', message });
      } finally {
        isLoading.value = false;
      }
    },
  };

  return {
    models: { name, email, password, confirmPassword, department, termsAccepted },
    outputs,
    inputs,
    onEffect,
  };
}
```

```vue
<!-- presentation/features/auth/RegisterView.vue -->
<script setup lang="ts">
import { useRegisterViewModel } from '@/presentation/view-models/useRegisterViewModel';
import { useNavGraph } from '@/router/nav-graph';
import { useToast } from '@/presentation/composables/useToast';

const vm = useRegisterViewModel();
const navGraph = useNavGraph();
const toast = useToast();

vm.onEffect((effect) => {
  switch (effect.type) {
    case 'NAVIGATE_TO_LOGIN': navGraph.auth.toLogin(); break;
    case 'SHOW_SUCCESS': toast.success(effect.message); break;
    case 'SHOW_ERROR': toast.error(effect.message); break;
  }
});

const strengthClass = (s: string) =>
  s === 'strong' ? 'bg-success' : s === 'medium' ? 'bg-warning' : 'bg-danger';
</script>

<template>
  <form @submit.prevent="vm.inputs.submit()" class="card p-4 mx-auto" style="max-width: 32rem;">
    <h2 class="mb-4">Create Account</h2>

    <!-- Name -->
    <div class="mb-3">
      <label for="name" class="form-label">Name</label>
      <input id="name" v-model="vm.models.name.value" class="form-control"
        :class="{ 'is-invalid': vm.outputs.nameError.value }"
        @blur="vm.inputs.touchName()" />
      <div class="invalid-feedback">{{ vm.outputs.nameError.value }}</div>
    </div>

    <!-- Email -->
    <div class="mb-3">
      <label for="regEmail" class="form-label">Email</label>
      <input id="regEmail" v-model="vm.models.email.value" type="email" class="form-control"
        :class="{ 'is-invalid': vm.outputs.emailError.value }"
        @blur="vm.inputs.touchEmail()" />
      <div class="invalid-feedback">{{ vm.outputs.emailError.value }}</div>
    </div>

    <!-- Password with strength meter -->
    <div class="mb-3">
      <label for="regPassword" class="form-label">Password</label>
      <input id="regPassword" v-model="vm.models.password.value" type="password" class="form-control"
        :class="{ 'is-invalid': vm.outputs.passwordError.value }"
        @blur="vm.inputs.touchPassword()" />
      <div class="invalid-feedback">{{ vm.outputs.passwordError.value }}</div>
      <div v-if="vm.models.password.value" class="progress mt-1" style="height: 4px;">
        <div class="progress-bar" :class="strengthClass(vm.outputs.passwordStrength.value)"
          :style="{ width: vm.outputs.passwordStrength.value === 'strong' ? '100%' : vm.outputs.passwordStrength.value === 'medium' ? '66%' : '33%' }"></div>
      </div>
    </div>

    <!-- Confirm Password -->
    <div class="mb-3">
      <label for="confirmPassword" class="form-label">Confirm Password</label>
      <input id="confirmPassword" v-model="vm.models.confirmPassword.value" type="password" class="form-control"
        :class="{ 'is-invalid': vm.outputs.confirmPasswordError.value }"
        @blur="vm.inputs.touchConfirmPassword()" />
      <div class="invalid-feedback">{{ vm.outputs.confirmPasswordError.value }}</div>
    </div>

    <!-- Department -->
    <div class="mb-3">
      <label for="department" class="form-label">Department</label>
      <select id="department" v-model="vm.models.department.value" class="form-select"
        :class="{ 'is-invalid': vm.outputs.departmentError.value }"
        @blur="vm.inputs.touchDepartment()">
        <option value="">Select department...</option>
        <option value="engineering">Engineering</option>
        <option value="product">Product</option>
        <option value="design">Design</option>
        <option value="marketing">Marketing</option>
      </select>
      <div class="invalid-feedback">{{ vm.outputs.departmentError.value }}</div>
    </div>

    <!-- Terms -->
    <div class="mb-3 form-check">
      <input id="terms" type="checkbox" class="form-check-input"
        :class="{ 'is-invalid': vm.outputs.termsError.value }"
        :checked="vm.models.termsAccepted.value"
        @change="vm.inputs.toggleTerms()" />
      <label for="terms" class="form-check-label">I accept the terms and conditions</label>
      <div class="invalid-feedback">{{ vm.outputs.termsError.value }}</div>
    </div>

    <!-- Submit -->
    <button type="submit" class="btn btn-primary w-100" :disabled="!vm.outputs.canSubmit.value">
      <span v-if="vm.outputs.isLoading.value">
        <span class="spinner-border spinner-border-sm me-1"></span> Registering...
      </span>
      <span v-else>Create Account</span>
    </button>
  </form>
</template>
```

---

## Offline-First CRUD Operations

### Task Management with Offline Support

```typescript
// data/cache/task-database.ts
import Dexie, { type Table } from 'dexie';
import { SyncStatus } from '@/data/repositories/base-offline.repository';

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

// data/repositories/task.repository.impl.ts
import { injectable, inject } from 'inversify';
import { v4 as uuidv4 } from 'uuid';
import { taskDb, type TaskEntity } from '@/data/cache/task-database';
import { SyncStatus, SyncQueue } from '@/data/repositories/base-offline.repository';
import { TOKENS } from '@/core/di/tokens';
import type { ITaskRepository, Task, CreateTaskDto } from '@/domain/services/task.service';
import type { AxiosInstance } from 'axios';

@injectable()
export class TaskRepositoryImpl implements ITaskRepository {
  private listeners: Set<(tasks: Task[]) => void> = new Set();

  constructor(
    @inject(TOKENS.ApiClient) private readonly apiClient: AxiosInstance,
    @inject(TOKENS.SyncQueue) private readonly syncQueue: SyncQueue
  ) {
    this.syncQueue.register('tasks', () => this.syncWithRemote());
  }

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
    this.syncQueue.scheduleSync('tasks');

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
    this.syncQueue.scheduleSync('tasks');
  }

  // Delete - soft delete locally
  async deleteTask(id: string): Promise<void> {
    const existing = await taskDb.tasks.get(id);
    if (!existing) return;

    if (existing.syncStatus === SyncStatus.PENDING_CREATE) {
      await taskDb.tasks.delete(id);
    } else {
      await taskDb.tasks.update(id, {
        syncStatus: SyncStatus.PENDING_DELETE,
        deletedAt: Date.now(),
        updatedAt: Date.now(),
      });
    }

    await this.refreshFromLocal();
    this.syncQueue.scheduleSync('tasks');
  }

  // Sync
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
    const pendingCreates = await taskDb.tasks
      .where('syncStatus').equals(SyncStatus.PENDING_CREATE).toArray();
    for (const entity of pendingCreates) {
      try {
        await this.apiClient.post('/tasks', this.mapToDto(entity));
        await taskDb.tasks.update(entity.id, { syncStatus: SyncStatus.SYNCED });
      } catch {
        await taskDb.tasks.update(entity.id, { syncStatus: SyncStatus.FAILED });
      }
    }

    const pendingUpdates = await taskDb.tasks
      .where('syncStatus').equals(SyncStatus.PENDING_UPDATE).toArray();
    for (const entity of pendingUpdates) {
      try {
        await this.apiClient.put(`/tasks/${entity.id}`, this.mapToDto(entity));
        await taskDb.tasks.update(entity.id, { syncStatus: SyncStatus.SYNCED });
      } catch {
        await taskDb.tasks.update(entity.id, { syncStatus: SyncStatus.FAILED });
      }
    }

    const pendingDeletes = await taskDb.tasks
      .where('syncStatus').equals(SyncStatus.PENDING_DELETE).toArray();
    for (const entity of pendingDeletes) {
      try {
        await this.apiClient.delete(`/tasks/${entity.id}`);
        await taskDb.tasks.delete(entity.id);
      } catch {
        await taskDb.tasks.update(entity.id, { syncStatus: SyncStatus.FAILED });
      }
    }
  }

  private async pullRemoteChanges(): Promise<void> {
    const lastSync = localStorage.getItem('tasks_last_sync');
    const since = lastSync ? parseInt(lastSync, 10) : 0;

    const response = await this.apiClient.get('/tasks', { params: { since } });

    await taskDb.transaction('rw', taskDb.tasks, async () => {
      for (const dto of response.data) {
        const local = await taskDb.tasks.get(dto.id);
        if (local && local.syncStatus !== SyncStatus.SYNCED) continue;

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
    const tasks = entities.map((e) => this.mapToTask(e));
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

  private mapToDto(entity: TaskEntity): Record<string, unknown> {
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

### WebSocket Composable with Reconnection

```typescript
// presentation/composables/useWebSocket.ts
import { ref, onUnmounted } from 'vue';

export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: number;
}

export function useWebSocket(url: string, token: () => string | null) {
  const connected = ref(false);
  let socket: WebSocket | null = null;
  let reconnectTimeout: ReturnType<typeof setTimeout> | undefined;
  const listeners = new Map<string, Array<(payload: unknown) => void>>();

  const connect = () => {
    const tokenValue = token();
    if (!tokenValue || socket) return;

    const wsUrl = `${url}?token=${tokenValue}`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => { connected.value = true; };
    socket.onclose = () => {
      connected.value = false;
      socket = null;
      reconnectTimeout = setTimeout(connect, 5000);
    };
    socket.onerror = (error) => { console.error('WebSocket error:', error); };
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        const handlers = listeners.get(message.type);
        handlers?.forEach((handler) => handler(message.payload));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  };

  const disconnect = () => {
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    socket?.close();
    socket = null;
    connected.value = false;
  };

  const send = <T>(type: string, payload: T) => {
    if (!socket || !connected.value) return;
    socket.send(JSON.stringify({ type, payload, timestamp: Date.now() }));
  };

  const onMessage = <T>(type: string, handler: (payload: T) => void) => {
    if (!listeners.has(type)) listeners.set(type, []);
    listeners.get(type)!.push(handler as (payload: unknown) => void);
  };

  onUnmounted(disconnect);

  return { connected, connect, disconnect, send, onMessage };
}
```

```vue
<!-- presentation/features/tasks/TaskBoardView.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useWebSocket } from '@/presentation/composables/useWebSocket';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';
import type { ITaskRepository, Task } from '@/domain/services/task.service';
import type { IAuthService } from '@/domain/services/auth.service';
import TaskCard from './components/TaskCard.vue';

const taskRepository = useInject<ITaskRepository>(TOKENS.TaskRepository);
const authService = useInject<IAuthService>(TOKENS.AuthService);

const tasks = ref<Task[]>([]);
const updatingTasks = ref<Set<string>>(new Set());

const ws = useWebSocket(
  import.meta.env.VITE_WS_URL,
  () => authService.getToken()
);

// Load initial tasks
onMounted(() => {
  taskRepository.subscribe((t) => { tasks.value = t; });
  ws.connect();
});

// Real-time updates
ws.onMessage<Task>('task.created', (task) => {
  tasks.value = [...tasks.value, task];
});

ws.onMessage<Task>('task.updated', (task) => {
  tasks.value = tasks.value.map((t) => (t.id === task.id ? task : t));
  updatingTasks.value.delete(task.id);
});

ws.onMessage<{ id: string }>('task.deleted', ({ id }) => {
  tasks.value = tasks.value.filter((t) => t.id !== id);
});

const handleToggle = async (task: Task) => {
  // Optimistic update
  tasks.value = tasks.value.map((t) =>
    t.id === task.id ? { ...t, completed: !t.completed } : t
  );
  updatingTasks.value.add(task.id);

  try {
    await taskRepository.updateTask({ ...task, completed: !task.completed });
  } catch {
    tasks.value = tasks.value.map((t) => (t.id === task.id ? task : t));
    updatingTasks.value.delete(task.id);
  }
};

const handleDelete = async (taskId: string) => {
  const original = [...tasks.value];
  tasks.value = tasks.value.filter((t) => t.id !== taskId);

  try {
    await taskRepository.deleteTask(taskId);
  } catch {
    tasks.value = original;
  }
};
</script>

<template>
  <div class="container-fluid p-4">
    <header class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h3 fw-bold">Task Board</h1>
      <div class="d-flex align-items-center gap-2" :class="ws.connected.value ? 'text-success' : 'text-muted'">
        <span class="rounded-circle d-inline-block" :class="ws.connected.value ? 'bg-success' : 'bg-secondary'"
          style="width: 8px; height: 8px;"></span>
        {{ ws.connected.value ? 'Connected' : 'Offline' }}
      </div>
    </header>

    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3">
      <div v-for="task in tasks" :key="task.id" class="col">
        <TaskCard
          :task="task"
          :is-updating="updatingTasks.has(task.id)"
          @toggle="handleToggle(task)"
          @delete="handleDelete(task.id)"
        />
      </div>
    </div>
  </div>
</template>
```

---

## Debounced Ref Composable

```typescript
// presentation/composables/useDebouncedRef.ts
import { ref, watch, type Ref } from 'vue';

export function useDebouncedRef<T>(initialValue: T, delay: number): Ref<T> {
  const value = ref(initialValue) as Ref<T>;
  const debouncedValue = ref(initialValue) as Ref<T>;
  let timeout: ReturnType<typeof setTimeout>;

  watch(value, (newVal) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      debouncedValue.value = newVal;
    }, delay);
  });

  return value;
}
```

---

## Toast Composable

```typescript
// presentation/composables/useToast.ts
import { ref } from 'vue';

export interface ToastMessage {
  id: number;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

const toasts = ref<ToastMessage[]>([]);
let nextId = 0;

export function useToast() {
  const show = (message: string, type: ToastMessage['type'] = 'info', duration = 3000) => {
    const id = nextId++;
    toasts.value.push({ id, message, type });
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id);
    }, duration);
  };

  return {
    toasts,
    show,
    success: (msg: string) => show(msg, 'success'),
    error: (msg: string) => show(msg, 'error'),
    warning: (msg: string) => show(msg, 'warning'),
    info: (msg: string) => show(msg, 'info'),
  };
}
```
