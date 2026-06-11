# Vue Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [Composition API Patterns](#composition-api-patterns)
3. [Component Patterns](#component-patterns)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Performance Patterns](#performance-patterns)
7. [Testing Patterns](#testing-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
+--------------------------------------------------------------+
|                    Presentation Layer                          |
|  +---------------------------------------------------------+ |
|  |  Vue SFCs <-> ViewModel Composables <-> Domain Services  | |
|  |     |             (Models/Outputs/Inputs/Effects)         | |
|  |     +--- Reactive State (ref/computed) -----------------> | |
|  +---------------------------------------------------------+ |
+--------------------------------------------------------------+
|                      Domain Layer                              |
|  +---------------------------------------------------------+ |
|  |  Entities | Services | Validators | Repository Interfaces | |
|  |           |          |                                     | |
|  |  Pure business logic, no framework dependencies            | |
|  +---------------------------------------------------------+ |
+--------------------------------------------------------------+
|                       Data Layer                               |
|  +---------------------------------------------------------+ |
|  |  Repository Impl | API Client | IndexedDB (Dexie)        | |
|  |  Mappers | DTOs   |   (Axios)  | Cache Manager            | |
|  |  Implements domain interfaces, handles data persistence   | |
|  +---------------------------------------------------------+ |
+--------------------------------------------------------------+
```

#### Implementation Example
```typescript
// Domain Layer - Pure business logic
// domain/entities/order.entity.ts
export interface Order {
  id: string;
  items: OrderItem[];
  status: OrderStatus;
  total: number;
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered';

// domain/services/order.service.ts
export interface IOrderService {
  calculateTotal(items: OrderItem[]): number;
  canCancel(order: Order): boolean;
  createOrder(items: OrderItem[]): Promise<Order>;
}

// domain/services/order.service.impl.ts
import { injectable, inject } from 'inversify';
import { TOKENS } from '@/core/di/tokens';

@injectable()
export class OrderServiceImpl implements IOrderService {
  constructor(
    @inject(TOKENS.OrderRepository) private readonly repository: IOrderRepository
  ) {}

  calculateTotal(items: OrderItem[]): number {
    return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }

  canCancel(order: Order): boolean {
    return order.status === 'pending' || order.status === 'confirmed';
  }

  async createOrder(items: OrderItem[]): Promise<Order> {
    const order: Omit<Order, 'id'> = {
      items,
      status: 'pending',
      total: this.calculateTotal(items),
    };
    return this.repository.create(order);
  }
}

// Data Layer - Implementation
// data/repositories/order.repository.impl.ts
import { injectable, inject } from 'inversify';
import { TOKENS } from '@/core/di/tokens';

@injectable()
export class OrderRepositoryImpl implements IOrderRepository {
  constructor(
    @inject(TOKENS.ApiClient) private readonly apiClient: AxiosInstance,
    @inject(TOKENS.OrderDatabase) private readonly localDb: OrderDatabase
  ) {}

  async create(order: Omit<Order, 'id'>): Promise<Order> {
    // Offline-first: save locally first
    const localOrder = await this.localDb.orders.add({
      ...order,
      id: uuidv4(),
      syncStatus: SyncStatus.PENDING,
    });

    this.syncQueue.scheduleSync('orders');
    return localOrder;
  }
}
```

### Feature Module Pattern

```typescript
// presentation/features/users/index.ts - Public API
export { default as UserListView } from './UserListView.vue';
export { default as UserDetailView } from './UserDetailView.vue';
export { default as UserEditView } from './UserEditView.vue';

// router/user.routes.ts
import type { RouteRecordRaw } from 'vue-router';

export const userRoutes: RouteRecordRaw[] = [
  {
    path: '/users',
    name: 'users',
    component: () => import('@/presentation/features/users/UserListView.vue'),
  },
  {
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('@/presentation/features/users/UserDetailView.vue'),
    props: true,
  },
  {
    path: '/users/:id/edit',
    name: 'user-edit',
    component: () => import('@/presentation/features/users/UserEditView.vue'),
    props: true,
  },
];
```

---

## Composition API Patterns

### Composable State Pattern

```typescript
// Centralized feature state with composables
import { ref, computed, type Ref, type ComputedRef } from 'vue';

interface FeatureState<T> {
  state: Ref<T>;
  readonly: ComputedRef<T>;
}

function useFeatureState<T>(initialValue: T): FeatureState<T> {
  const state = ref(initialValue) as Ref<T>;
  const readonly = computed(() => state.value);
  return { state, readonly };
}

// Usage
interface UserListState {
  users: User[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
}

function useUserListState() {
  const state = ref<UserListState>({
    users: [],
    loading: false,
    error: null,
    selectedId: null,
  });

  // Derived state
  const selectedUser = computed(
    () => state.value.users.find((u) => u.id === state.value.selectedId) ?? null
  );

  const activeUsers = computed(
    () => state.value.users.filter((u) => u.status === 'active')
  );

  const setLoading = (loading: boolean) => { state.value.loading = loading; };
  const setUsers = (users: User[]) => { state.value.users = users; };
  const setError = (error: string | null) => { state.value.error = error; };
  const selectUser = (id: string | null) => { state.value.selectedId = id; };

  return {
    ...toRefs(state.value),
    selectedUser,
    activeUsers,
    setLoading,
    setUsers,
    setError,
    selectUser,
  };
}
```

### MVVM Input/Output/Effect Pattern

```
+-------------------------------------------------------------------+
|                      ViewModel Composable                          |
|                                                                    |
|   Models (v-model)       Outputs (computed)     Effects            |
|   +-------------+       +--------------+     +------------+       |
|   | name (ref)  |       | canSubmit    |     | NAVIGATE   |       |
|   | email (ref) | ----> | isLoading    | --> | TOAST      |       |
|   +-------------+       | errors       |     | DIALOG     |       |
|                          +--------------+     +------------+       |
|   Inputs (methods)            |                    |               |
|   +-------------+             |                    |               |
|   | submit()    |             |                    |               |
|   | reset()     |             |                    |               |
|   +-------------+             v                    v               |
|                          Component            Effect Handler       |
+-------------------------------------------------------------------+
```

```typescript
// Generic ViewModel composable pattern
interface ViewModelResult<TModels, TOutputs, TInputs, TEffect> {
  models: TModels;
  outputs: TOutputs;
  inputs: TInputs;
  onEffect: (callback: (effect: TEffect) => void) => void;
}

// Implementation pattern
function useExampleViewModel(): ViewModelResult<...> {
  // Models - two-way bindable refs
  const name = ref('');
  const email = ref('');

  // Internal state
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Effects
  const effectCallbacks: Array<(effect: ExampleEffect) => void> = [];
  const onEffect = (cb: (effect: ExampleEffect) => void) => { effectCallbacks.push(cb); };
  const emitEffect = (effect: ExampleEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };

  // Outputs - read-only computed
  const outputs = {
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    canSubmit: computed(() => name.value.length > 0 && !isLoading.value),
  };

  // Inputs - action methods
  const inputs = {
    async submit() { /* ... */ },
    reset() { name.value = ''; email.value = ''; },
  };

  return { models: { name, email }, outputs, inputs, onEffect };
}
```

### Pinia Store Pattern

```typescript
// stores/auth.store.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@/domain/entities/auth.entity';

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  // Getters
  const isAuthenticated = computed(() => !!token.value);
  const userRoles = computed(() => user.value?.roles ?? []);

  // Actions
  function setAuth(newUser: User, newToken: string) {
    user.value = newUser;
    token.value = newToken;
  }

  function clearAuth() {
    user.value = null;
    token.value = null;
  }

  function hasRole(role: string): boolean {
    return userRoles.value.includes(role);
  }

  return { user, token, isAuthenticated, userRoles, setAuth, clearAuth, hasRole };
});
```

---

## Component Patterns

### Smart/Dumb Component Pattern

```vue
<!-- Smart Component (Container) - has logic, uses composables -->
<!-- UserListContainer.vue -->
<script setup lang="ts">
import { useUserListViewModel } from '@/presentation/view-models/useUserListViewModel';
import { useNavGraph } from '@/router/nav-graph';
import UserList from './UserList.vue';
import LoadingSpinner from '@/presentation/components/LoadingSpinner.vue';

const vm = useUserListViewModel();
const navGraph = useNavGraph();

vm.onEffect((effect) => {
  if (effect.type === 'NAVIGATE_TO_USER_DETAIL') {
    navGraph.users.toDetail(effect.userId);
  }
});
</script>

<template>
  <LoadingSpinner v-if="vm.outputs.isLoading.value" />
  <UserList
    v-else
    :users="vm.outputs.users.value"
    @user-select="vm.inputs.selectUser($event)"
    @user-delete="vm.inputs.deleteUser($event)"
  />
</template>
```

```vue
<!-- Dumb Component (Presentational) - pure props + emits -->
<!-- UserList.vue -->
<script setup lang="ts">
import type { User } from '@/domain/entities/user.entity';

defineProps<{
  users: User[];
}>();

const emit = defineEmits<{
  userSelect: [userId: string];
  userDelete: [userId: string];
}>();
</script>

<template>
  <ul class="list-group">
    <li
      v-for="user in users"
      :key="user.id"
      class="list-group-item list-group-item-action d-flex justify-content-between"
      @click="emit('userSelect', user.id)"
    >
      <div>
        <span class="fw-semibold">{{ user.name }}</span>
        <span class="text-muted ms-2">{{ user.email }}</span>
      </div>
      <button
        class="btn btn-sm btn-outline-danger"
        @click.stop="emit('userDelete', user.id)"
      >
        Delete
      </button>
    </li>
  </ul>
</template>
```

### Provide/Inject Pattern

```typescript
// core/plugins/provide-services.ts
import type { App, InjectionKey } from 'vue';
import type { IAuthService } from '@/domain/services/auth.service';

export const AuthServiceKey: InjectionKey<IAuthService> = Symbol('AuthService');

export function provideServices(app: App): void {
  const authService = container.get<IAuthService>(TOKENS.AuthService);
  app.provide(AuthServiceKey, authService);
}

// Usage in component
import { inject } from 'vue';
import { AuthServiceKey } from '@/core/plugins/provide-services';

const authService = inject(AuthServiceKey)!;
```

### Compound Component Pattern

```vue
<!-- Accordion.vue -->
<script setup lang="ts">
import { provide, reactive } from 'vue';

const props = withDefaults(defineProps<{
  multiple?: boolean;
}>(), { multiple: false });

const state = reactive({
  expandedItems: new Set<string>(),
});

const toggle = (id: string) => {
  if (state.expandedItems.has(id)) {
    state.expandedItems.delete(id);
  } else {
    if (!props.multiple) state.expandedItems.clear();
    state.expandedItems.add(id);
  }
};

const isExpanded = (id: string) => state.expandedItems.has(id);

provide('accordion', { toggle, isExpanded });
</script>

<template>
  <div class="accordion"><slot /></div>
</template>
```

```vue
<!-- AccordionItem.vue -->
<script setup lang="ts">
import { inject } from 'vue';

const props = defineProps<{ id: string; header: string }>();
const accordion = inject<{
  toggle: (id: string) => void;
  isExpanded: (id: string) => boolean;
}>('accordion')!;
</script>

<template>
  <div class="accordion-item">
    <h2 class="accordion-header">
      <button
        class="accordion-button"
        :class="{ collapsed: !accordion.isExpanded(id) }"
        @click="accordion.toggle(id)"
      >
        {{ header }}
      </button>
    </h2>
    <div v-show="accordion.isExpanded(id)" class="accordion-collapse">
      <div class="accordion-body"><slot /></div>
    </div>
  </div>
</template>
```

### Slot Pattern with Scoped Slots

```vue
<!-- DataLoader.vue -->
<script setup lang="ts" generic="T">
import { ref, onMounted } from 'vue';

const props = defineProps<{
  loader: () => Promise<T>;
}>();

const data = ref<T | null>(null) as Ref<T | null>;
const isLoading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    data.value = await props.loader();
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error';
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <slot v-if="isLoading" name="loading">
    <div class="spinner-border"></div>
  </slot>
  <slot v-else-if="error" name="error" :error="error">
    <div class="alert alert-danger">{{ error }}</div>
  </slot>
  <slot v-else-if="data" :data="data" />
</template>

<!-- Usage -->
<DataLoader :loader="loadUsers">
  <template #loading>
    <SkeletonLoader />
  </template>
  <template #error="{ error }">
    <ErrorBanner :message="error" />
  </template>
  <template #default="{ data: users }">
    <UserList :users="users" />
  </template>
</DataLoader>
```

---

## Data Flow Patterns

### Offline-First Pattern

```
+-------------------------------------------------------------------+
|                     Client Application                             |
|                                                                    |
|  +----------------+    +----------------+    +----------------+    |
|  |  Component     |--->|  Repository    |--->|   IndexedDB    |    |
|  |                |<---|                |<---|   (Dexie)      |    |
|  +----------------+    +----------------+    +----------------+    |
|                                |                                   |
|                                | Background Sync                   |
|                                v                                   |
|                        +----------------+                          |
|                        |  Sync Queue    |                          |
|                        +----------------+                          |
|                                |                                   |
+--------------------------------|-----------------------------------+
                                 |
                                 v
                        +----------------+
                        |  Remote API    |
                        +----------------+
```

### Four-Layer Cache Pattern

```typescript
interface CacheEntry<T> {
  value: T;
  timestamp: number;
  ttl: number;
}

export class FourLayerCache<T> {
  // L1: Memory (<1ms, FIFO, 50 items)
  private l1 = new Map<string, CacheEntry<T>>();

  // L2: LRU (2-5ms, 100 items, 5-min TTL)
  private l2 = new Map<string, CacheEntry<T>>();
  private l2Order: string[] = [];
  private readonly l2MaxSize = 100;

  // L3: IndexedDB (10-50ms, persistent)
  private readonly db: Dexie;
  private readonly tableName: string;

  constructor(tableName: string) {
    this.tableName = tableName;
    this.db = new Dexie(`Cache_${tableName}`);
    this.db.version(1).stores({ cache: 'key, value, timestamp, ttl' });
  }

  async get(key: string, loader: () => Promise<T>, ttl = 5 * 60 * 1000): Promise<T> {
    const now = Date.now();

    // L1 Check
    const l1Entry = this.l1.get(key);
    if (l1Entry && this.isValid(l1Entry, now)) return l1Entry.value;

    // L2 Check
    const l2Entry = this.l2.get(key);
    if (l2Entry && this.isValid(l2Entry, now)) {
      this.promoteToL1(key, l2Entry);
      return l2Entry.value;
    }

    // L3 Check (IndexedDB)
    const l3Entry = await this.db.table(this.tableName).get(key);
    if (l3Entry && this.isValid(l3Entry, now)) {
      this.promoteToL1(key, l3Entry);
      this.promoteToL2(key, l3Entry);
      return l3Entry.value;
    }

    // L4: Remote API (100-500ms+)
    const value = await loader();
    const entry: CacheEntry<T> = { value, timestamp: now, ttl };
    this.promoteToL1(key, entry);
    this.promoteToL2(key, entry);
    await this.db.table(this.tableName).put({ key, ...entry });

    return value;
  }

  private isValid(entry: CacheEntry<T>, now: number): boolean {
    return now - entry.timestamp < entry.ttl;
  }

  private promoteToL1(key: string, entry: CacheEntry<T>): void {
    if (this.l1.size >= 50) {
      const firstKey = this.l1.keys().next().value;
      if (firstKey) this.l1.delete(firstKey);
    }
    this.l1.set(key, entry);
  }

  private promoteToL2(key: string, entry: CacheEntry<T>): void {
    const idx = this.l2Order.indexOf(key);
    if (idx > -1) this.l2Order.splice(idx, 1);
    while (this.l2.size >= this.l2MaxSize) {
      const lruKey = this.l2Order.shift();
      if (lruKey) this.l2.delete(lruKey);
    }
    this.l2.set(key, entry);
    this.l2Order.push(key);
  }

  invalidate(key: string): void {
    this.l1.delete(key);
    this.l2.delete(key);
    this.db.table(this.tableName).delete(key);
  }

  invalidateAll(): void {
    this.l1.clear();
    this.l2.clear();
    this.l2Order = [];
    this.db.table(this.tableName).clear();
  }
}
```

---

## Error Handling Patterns

### Error Boundary Component

```vue
<!-- presentation/components/ErrorBoundary.vue -->
<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue';

const error = ref<Error | null>(null);
const hasError = ref(false);

onErrorCaptured((err: Error) => {
  error.value = err;
  hasError.value = true;
  console.error('Error caught by boundary:', err);
  return false; // prevent propagation
});

const reset = () => {
  error.value = null;
  hasError.value = false;
};
</script>

<template>
  <div v-if="hasError" class="alert alert-danger text-center p-5">
    <h2 class="h4 fw-bold">Something went wrong</h2>
    <p class="text-muted">{{ error?.message }}</p>
    <button class="btn btn-primary" @click="reset">Try again</button>
  </div>
  <slot v-else />
</template>
```

### Result Type Pattern

```typescript
// domain/entities/result.ts
export type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

export function ok<T>(data: T): Result<T> {
  return { success: true, data };
}

export function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

// Usage in service
@injectable()
export class UserService implements IUserService {
  async createUser(data: CreateUserData): Promise<Result<User, string>> {
    if (!data.email) return err('Email is required');
    if (!isValidEmail(data.email)) return err('Invalid email format');

    try {
      const user = await this.repository.create(data);
      return ok(user);
    } catch (error) {
      if (error instanceof Error && error.message.includes('duplicate')) {
        return err('User already exists');
      }
      return err('Failed to create user');
    }
  }
}

// Usage in ViewModel
const inputs = {
  async submit() {
    const result = await userService.createUser(formData);
    if (result.success) {
      emitEffect({ type: 'SHOW_TOAST', message: 'User created' });
      emitEffect({ type: 'NAVIGATE_TO_DETAIL', userId: result.data.id });
    } else {
      error.value = result.error;
    }
  },
};
```

---

## Performance Patterns

### Computed vs Methods

```vue
<script setup lang="ts">
import { computed } from 'vue';

// GOOD: Computed - cached, re-evaluated only when deps change
const filteredUsers = computed(() =>
  users.value.filter((u) => u.status === 'active')
);

// BAD: Method called in template - re-runs every render
function getFilteredUsers() {
  return users.value.filter((u) => u.status === 'active');
}
</script>

<template>
  <!-- GOOD -->
  <div v-for="user in filteredUsers" :key="user.id">{{ user.name }}</div>

  <!-- BAD -->
  <div v-for="user in getFilteredUsers()" :key="user.id">{{ user.name }}</div>
</template>
```

### ShallowRef for Large Objects

```typescript
import { shallowRef, triggerRef } from 'vue';

// For large arrays/objects that are replaced wholesale
const largeDataset = shallowRef<DataItem[]>([]);

// Only triggers reactivity on reassignment, not deep mutations
largeDataset.value = newData; // triggers update

// Deep mutation does NOT trigger (use triggerRef if needed)
largeDataset.value.push(item);
triggerRef(largeDataset); // manually trigger
```

### Virtual Scrolling Pattern

```vue
<!-- Using vue-virtual-scroller or manual implementation -->
<script setup lang="ts">
import { ref, computed } from 'vue';

const items = ref<Item[]>([]);
const scrollTop = ref(0);
const containerHeight = 600;
const itemHeight = 48;

const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / itemHeight);
  const end = Math.min(start + Math.ceil(containerHeight / itemHeight) + 1, items.value.length);
  return { start, end };
});

const visibleItems = computed(() =>
  items.value.slice(visibleRange.value.start, visibleRange.value.end)
);

const totalHeight = computed(() => items.value.length * itemHeight);
const offsetY = computed(() => visibleRange.value.start * itemHeight);

const onScroll = (e: Event) => {
  scrollTop.value = (e.target as HTMLElement).scrollTop;
};
</script>

<template>
  <div class="overflow-auto" :style="{ height: containerHeight + 'px' }" @scroll="onScroll">
    <div :style="{ height: totalHeight + 'px', position: 'relative' }">
      <div :style="{ transform: `translateY(${offsetY}px)` }">
        <div v-for="item in visibleItems" :key="item.id" :style="{ height: itemHeight + 'px' }">
          {{ item.name }}
        </div>
      </div>
    </div>
  </div>
</template>
```

### Async Component Loading

```typescript
// router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/presentation/layouts/MainLayout.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/presentation/features/dashboard/DashboardView.vue'),
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/presentation/features/users/UserListView.vue'),
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/presentation/features/settings/SettingsView.vue'),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
```

---

## Testing Patterns

### Component Testing with Vue Test Utils

```typescript
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import LoginView from '@/presentation/features/auth/LoginView.vue';

describe('LoginView', () => {
  const mockLogin = vi.fn();

  const createWrapper = () => {
    return mount(LoginView, {
      global: {
        provide: {
          // Mock DI
        },
        stubs: {
          teleport: true,
        },
      },
    });
  };

  it('should show validation errors on blur', async () => {
    const wrapper = createWrapper();

    const emailInput = wrapper.find('#email');
    await emailInput.trigger('focus');
    await emailInput.trigger('blur');

    expect(wrapper.text()).toContain('Email is required');
  });

  it('should call login on valid submit', async () => {
    mockLogin.mockResolvedValue(undefined);
    const wrapper = createWrapper();

    await wrapper.find('#email').setValue('test@example.com');
    await wrapper.find('#password').setValue('password123');
    await wrapper.find('form').trigger('submit');

    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
      rememberMe: false,
    });
  });

  it('should disable submit button while loading', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {}));
    const wrapper = createWrapper();

    await wrapper.find('#email').setValue('test@example.com');
    await wrapper.find('#password').setValue('password123');
    await wrapper.find('form').trigger('submit');

    const button = wrapper.find('button[type="submit"]');
    expect(button.attributes('disabled')).toBeDefined();
    expect(wrapper.text()).toContain('Signing in');
  });
});
```

### ViewModel Composable Testing

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useLoginViewModel } from '@/presentation/view-models/useLoginViewModel';

// Mock InversifyJS injection
vi.mock('@/core/di/use-inject', () => ({
  useInject: vi.fn(() => mockAuthService),
}));

const mockAuthService = {
  login: vi.fn(),
};

describe('useLoginViewModel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should update email model', () => {
    const vm = useLoginViewModel();
    vm.models.email.value = 'test@example.com';
    expect(vm.models.email.value).toBe('test@example.com');
  });

  it('should validate email format', () => {
    const vm = useLoginViewModel();
    vm.models.email.value = 'invalid';
    vm.inputs.touchEmail();
    expect(vm.outputs.emailError.value).toBe('Invalid email format');
  });

  it('should set loading state during submit', async () => {
    mockAuthService.login.mockImplementation(() => new Promise(() => {}));
    const vm = useLoginViewModel();

    vm.models.email.value = 'test@example.com';
    vm.models.password.value = 'password123';
    vm.inputs.touchEmail();
    vm.inputs.touchPassword();

    vm.inputs.submit(); // do not await

    expect(vm.outputs.isLoading.value).toBe(true);
  });

  it('should emit NAVIGATE_TO_HOME on success', async () => {
    mockAuthService.login.mockResolvedValue(undefined);
    const effects: any[] = [];
    const vm = useLoginViewModel();

    vm.onEffect((e) => effects.push(e));
    vm.models.email.value = 'test@example.com';
    vm.models.password.value = 'password123';
    vm.inputs.touchEmail();
    vm.inputs.touchPassword();

    await vm.inputs.submit();

    expect(effects).toContainEqual({ type: 'NAVIGATE_TO_HOME' });
  });

  it('should emit SHOW_ERROR on failure', async () => {
    mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));
    const effects: any[] = [];
    const vm = useLoginViewModel();

    vm.onEffect((e) => effects.push(e));
    vm.models.email.value = 'test@example.com';
    vm.models.password.value = 'password123';
    vm.inputs.touchEmail();
    vm.inputs.touchPassword();

    await vm.inputs.submit();

    expect(effects).toContainEqual({ type: 'SHOW_ERROR', message: 'Invalid credentials' });
  });
});
```

### Repository Testing with Mock DI

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Container } from 'inversify';
import { TOKENS } from '@/core/di/tokens';
import { UserRepositoryImpl } from '@/data/repositories/user.repository.impl';

describe('UserRepositoryImpl', () => {
  let container: Container;
  let mockApiClient: any;
  let repository: UserRepositoryImpl;

  beforeEach(() => {
    container = new Container();
    mockApiClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };
    container.bind(TOKENS.ApiClient).toConstantValue(mockApiClient);
    container.bind(TOKENS.UserRepository).to(UserRepositoryImpl);
    repository = container.get(TOKENS.UserRepository);
  });

  it('should map DTO to domain entity', async () => {
    mockApiClient.get.mockResolvedValue({
      data: { id: '1', name: 'John', email: 'john@test.com', roles: ['admin'] },
    });

    const user = await repository.getUserById('1');

    expect(user).toEqual({
      id: '1',
      name: 'John',
      email: 'john@test.com',
      roles: ['admin'],
    });
  });

  it('should return null for non-existent user', async () => {
    mockApiClient.get.mockRejectedValue({ response: { status: 404 } });
    const user = await repository.getUserById('nonexistent');
    expect(user).toBeNull();
  });
});
```

### Validator Testing

```typescript
import { describe, it, expect } from 'vitest';
import {
  encodeHtmlEntities,
  hasSqlInjection,
  sanitizeFilename,
  isValidUrl,
  sanitizeInput,
} from '@/domain/validators/security.validator';

describe('SecurityValidator', () => {
  describe('encodeHtmlEntities', () => {
    it('should encode HTML special characters', () => {
      expect(encodeHtmlEntities('<script>alert("xss")</script>')).toBe(
        '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
      );
    });
  });

  describe('hasSqlInjection', () => {
    it('should detect OR injection', () => {
      expect(hasSqlInjection("' OR '1'='1")).toBe(true);
    });

    it('should not flag normal input', () => {
      expect(hasSqlInjection("John's Cafe")).toBe(false);
    });
  });

  describe('sanitizeFilename', () => {
    it('should prevent path traversal', () => {
      expect(sanitizeFilename('../../etc/passwd')).toBe('etcpasswd');
    });
  });

  describe('isValidUrl', () => {
    it('should accept https URLs', () => {
      expect(isValidUrl('https://example.com')).toBe(true);
    });

    it('should reject javascript URLs', () => {
      expect(isValidUrl('javascript:alert(1)')).toBe(false);
    });
  });
});
```
