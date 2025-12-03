# Angular Developer Skill - Design Patterns

## Table of Contents
1. [Architecture Patterns](#architecture-patterns)
2. [State Management Patterns](#state-management-patterns)
3. [Component Patterns](#component-patterns)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Performance Patterns](#performance-patterns)
7. [Testing Patterns](#testing-patterns)

---

## Architecture Patterns

### Clean Architecture Pattern

```
┌──────────────────────────────────────────────────────────────┐
│                    Presentation Layer                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Components ←──→ ViewModel ←──→ Domain Services         │ │
│  │     │                              │                     │ │
│  │     └──── Signals ────────────────→│                     │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                      Domain Layer                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Models │ Services │ Repository Interfaces              │ │
│  │         │          │                                     │ │
│  │  Pure business logic, no framework dependencies         │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                       Data Layer                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Repository Impl │ API Client │ IndexedDB (Dexie)       │ │
│  │                  │            │                          │ │
│  │  Implements domain interfaces, handles data persistence │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### Implementation Example
```typescript
// Domain Layer - Pure business logic
// domain/models/order.model.ts
export interface Order {
  id: string;
  items: OrderItem[];
  status: OrderStatus;
  total: number;
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered';

// domain/services/order.service.ts
@Injectable({ providedIn: 'root' })
export class OrderService {
  private readonly repository = inject(ORDER_REPOSITORY);

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

// Data Layer - Implementation details
// data/repositories/order-repository.impl.ts
@Injectable({ providedIn: 'root' })
export class OrderRepositoryImpl implements IOrderRepository {
  private readonly apiClient = inject(ApiClient);
  private readonly localDb = inject(OrderDatabase);

  async create(order: Omit<Order, 'id'>): Promise<Order> {
    // Offline-first: save locally first
    const localOrder = await this.localDb.orders.add({
      ...order,
      id: uuidv4(),
      syncStatus: SyncStatus.PENDING,
    });

    // Schedule background sync
    this.syncManager.scheduleSync('orders');

    return localOrder;
  }
}
```

### Feature Module Pattern

```typescript
// features/users/users.routes.ts
export const USER_ROUTES: Routes = [
  {
    path: '',
    component: UserLayoutComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./list/user-list.component')
          .then(m => m.UserListComponent),
      },
      {
        path: ':id',
        loadComponent: () => import('./detail/user-detail.component')
          .then(m => m.UserDetailComponent),
      },
      {
        path: ':id/edit',
        loadComponent: () => import('./edit/user-edit.component')
          .then(m => m.UserEditComponent),
        canDeactivate: [unsavedChangesGuard],
      },
    ],
  },
];

// features/users/index.ts - Public API
export { USER_ROUTES } from './users.routes';
export { UserService } from './services/user.service';
export { User } from './models/user.model';
```

---

## State Management Patterns

### Signal-Based State Pattern

```typescript
// Centralized feature state with signals
@Injectable()
export class FeatureState<T extends Record<string, unknown>> {
  private readonly _state: WritableSignal<T>;

  constructor(initialState: T) {
    this._state = signal(initialState);
  }

  // Read-only access
  readonly state = computed(() => this._state());

  // Selector pattern
  select<K extends keyof T>(key: K): Signal<T[K]> {
    return computed(() => this._state()[key]);
  }

  // Update patterns
  set(newState: Partial<T>): void {
    this._state.update(state => ({ ...state, ...newState }));
  }

  update(updater: (state: T) => Partial<T>): void {
    this._state.update(state => ({ ...state, ...updater(state) }));
  }

  reset(initialState: T): void {
    this._state.set(initialState);
  }
}

// Usage
interface UserListState {
  users: User[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
}

@Injectable()
export class UserListState extends FeatureState<UserListState> {
  constructor() {
    super({
      users: [],
      loading: false,
      error: null,
      selectedId: null,
    });
  }

  // Derived state
  readonly selectedUser = computed(() => {
    const state = this.state();
    return state.users.find(u => u.id === state.selectedId) ?? null;
  });

  readonly activeUsers = computed(() =>
    this.state().users.filter(u => u.status === 'active')
  );
}
```

### Input/Output/Effect Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      ViewModel                               │
│                                                              │
│   Input (Actions)          Output (State)      Effect        │
│   ┌───────────┐           ┌────────────┐    ┌──────────┐    │
│   │ SET_NAME  │──────────→│ name       │    │ NAVIGATE │    │
│   │ SET_EMAIL │   Process │ email      │───→│ TOAST    │    │
│   │ SUBMIT    │──────────→│ isLoading  │    │ DIALOG   │    │
│   │ RESET     │           │ errors     │    └──────────┘    │
│   └───────────┘           └────────────┘         │          │
│        │                        │                 │          │
│        └────────────────────────┼─────────────────┘          │
│                                 │                            │
└─────────────────────────────────│────────────────────────────┘
                                  │
                                  ↓
                            Component subscribes
```

```typescript
// Generic ViewModel base class
export abstract class BaseViewModel<
  TInput,
  TOutput,
  TEffect = never
> {
  protected abstract readonly _state: WritableSignal<TOutput>;
  protected readonly _effect = new Subject<TEffect>();

  readonly output: Signal<TOutput> = computed(() => this._state());
  readonly effect$ = this._effect.asObservable();

  abstract onInput(input: TInput): void;

  protected emit(effect: TEffect): void {
    this._effect.next(effect);
  }
}

// Concrete implementation
@Injectable()
export class ProductViewModel extends BaseViewModel<
  ProductInput,
  ProductOutput,
  ProductEffect
> {
  protected readonly _state = signal<ProductOutput>({
    product: null,
    isLoading: false,
    error: null,
  });

  private readonly productService = inject(ProductService);

  onInput(input: ProductInput): void {
    switch (input.type) {
      case 'LOAD':
        this.loadProduct(input.id);
        break;
      case 'ADD_TO_CART':
        this.addToCart();
        break;
      case 'SHARE':
        this.emit({ type: 'OPEN_SHARE_DIALOG' });
        break;
    }
  }

  private async loadProduct(id: string): Promise<void> {
    this._state.update(s => ({ ...s, isLoading: true, error: null }));

    try {
      const product = await this.productService.getById(id);
      this._state.update(s => ({ ...s, product, isLoading: false }));
    } catch (error) {
      this._state.update(s => ({
        ...s,
        error: error instanceof Error ? error.message : 'Failed to load',
        isLoading: false,
      }));
    }
  }

  private addToCart(): void {
    const product = this._state().product;
    if (!product) return;

    this.cartService.add(product);
    this.emit({ type: 'SHOW_TOAST', message: 'Added to cart' });
  }
}
```

---

## Component Patterns

### Smart/Dumb Component Pattern

```typescript
// Smart Component (Container) - has logic, injects services
@Component({
  selector: 'app-user-list-container',
  standalone: true,
  imports: [UserListComponent, LoadingSpinnerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (loading()) {
      <app-loading-spinner />
    } @else {
      <app-user-list
        [users]="users()"
        [selectedId]="selectedId()"
        (userSelect)="onUserSelect($event)"
        (userDelete)="onUserDelete($event)"
      />
    }
  `,
})
export class UserListContainerComponent {
  private readonly userService = inject(UserService);

  readonly users = this.userService.users;
  readonly loading = this.userService.loading;
  readonly selectedId = signal<string | null>(null);

  onUserSelect(userId: string): void {
    this.selectedId.set(userId);
  }

  onUserDelete(userId: string): void {
    this.userService.delete(userId);
  }
}

// Dumb Component (Presentational) - pure input/output
@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ul class="user-list">
      @for (user of users(); track user.id) {
        <li
          [class.selected]="user.id === selectedId()"
          (click)="userSelect.emit(user.id)"
        >
          <span class="name">{{ user.name }}</span>
          <span class="email">{{ user.email }}</span>
          <button (click)="onDelete($event, user.id)">Delete</button>
        </li>
      }
    </ul>
  `,
})
export class UserListComponent {
  readonly users = input.required<User[]>();
  readonly selectedId = input<string | null>(null);

  readonly userSelect = output<string>();
  readonly userDelete = output<string>();

  onDelete(event: Event, userId: string): void {
    event.stopPropagation();
    this.userDelete.emit(userId);
  }
}
```

### Compound Component Pattern

```typescript
// Parent component that manages shared state
@Component({
  selector: 'app-accordion',
  standalone: true,
  template: `<ng-content />`,
  providers: [AccordionService],
})
export class AccordionComponent {
  readonly multiple = input(false);
}

@Injectable()
export class AccordionService {
  private readonly accordion = inject(AccordionComponent);
  private readonly expandedItems = signal<Set<string>>(new Set());

  isExpanded(id: string): Signal<boolean> {
    return computed(() => this.expandedItems().has(id));
  }

  toggle(id: string): void {
    this.expandedItems.update(items => {
      const newItems = new Set(items);

      if (newItems.has(id)) {
        newItems.delete(id);
      } else {
        if (!this.accordion.multiple()) {
          newItems.clear();
        }
        newItems.add(id);
      }

      return newItems;
    });
  }
}

// Child component
@Component({
  selector: 'app-accordion-item',
  standalone: true,
  template: `
    <div class="accordion-item">
      <button
        class="accordion-header"
        (click)="toggle()"
        [attr.aria-expanded]="isExpanded()"
      >
        <ng-content select="[header]" />
        <span class="icon">{{ isExpanded() ? '−' : '+' }}</span>
      </button>

      @if (isExpanded()) {
        <div class="accordion-content" @slideDown>
          <ng-content />
        </div>
      }
    </div>
  `,
})
export class AccordionItemComponent {
  private readonly accordionService = inject(AccordionService);
  private readonly id = input.required<string>();

  readonly isExpanded = computed(() =>
    this.accordionService.isExpanded(this.id())()
  );

  toggle(): void {
    this.accordionService.toggle(this.id());
  }
}

// Usage
@Component({
  template: `
    <app-accordion>
      <app-accordion-item id="item1">
        <span header>Section 1</span>
        Content for section 1
      </app-accordion-item>
      <app-accordion-item id="item2">
        <span header>Section 2</span>
        Content for section 2
      </app-accordion-item>
    </app-accordion>
  `,
})
export class MyPageComponent {}
```

### Render Props Pattern (with Template)

```typescript
@Component({
  selector: 'app-data-loader',
  standalone: true,
  template: `
    @if (loading()) {
      <ng-container *ngTemplateOutlet="loadingTemplate || defaultLoading" />
    } @else if (error()) {
      <ng-container
        *ngTemplateOutlet="errorTemplate || defaultError; context: { $implicit: error() }"
      />
    } @else {
      <ng-container
        *ngTemplateOutlet="contentTemplate; context: { $implicit: data() }"
      />
    }

    <ng-template #defaultLoading>
      <div class="loading">Loading...</div>
    </ng-template>

    <ng-template #defaultError let-error>
      <div class="error">{{ error }}</div>
    </ng-template>
  `,
})
export class DataLoaderComponent<T> {
  readonly loader = input.required<() => Promise<T>>();
  readonly loadingTemplate = input<TemplateRef<void>>();
  readonly errorTemplate = input<TemplateRef<{ $implicit: string }>>();
  readonly contentTemplate = input.required<TemplateRef<{ $implicit: T }>>();

  readonly data = signal<T | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  constructor() {
    effect(() => {
      this.load();
    });
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);

    try {
      const result = await this.loader()();
      this.data.set(result);
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      this.loading.set(false);
    }
  }
}

// Usage
@Component({
  template: `
    <app-data-loader
      [loader]="loadUsers"
      [contentTemplate]="content"
      [loadingTemplate]="loading"
    >
    </app-data-loader>

    <ng-template #loading>
      <app-skeleton-loader />
    </ng-template>

    <ng-template #content let-users>
      <app-user-list [users]="users" />
    </ng-template>
  `,
})
export class UsersPageComponent {
  private readonly userService = inject(UserService);

  loadUsers = () => this.userService.getAll();
}
```

---

## Data Flow Patterns

### Offline-First Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Component   │───→│  Repository  │───→│   IndexedDB  │  │
│  │              │←───│              │←───│   (Dexie)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                              │
│                              │ Background Sync              │
│                              ↓                              │
│                      ┌──────────────┐                       │
│                      │ Sync Manager │                       │
│                      └──────────────┘                       │
│                              │                              │
└──────────────────────────────│──────────────────────────────┘
                               │
                               ↓
                      ┌──────────────┐
                      │  Remote API  │
                      └──────────────┘
```

```typescript
// Sync Manager Pattern
@Injectable({ providedIn: 'root' })
export class SyncManager {
  private readonly syncHandlers = new Map<string, () => Promise<void>>();
  private readonly pendingSync = signal<Set<string>>(new Set());
  private syncTimeout: ReturnType<typeof setTimeout> | null = null;

  readonly isSyncing = signal(false);
  readonly hasPendingChanges = computed(() => this.pendingSync().size > 0);

  register(key: string, handler: () => Promise<void>): void {
    this.syncHandlers.set(key, handler);
  }

  scheduleSync(key: string, delayMs = 1000): void {
    this.pendingSync.update(set => new Set(set).add(key));

    // Debounce sync
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }

    this.syncTimeout = setTimeout(() => {
      this.executeSync();
    }, delayMs);
  }

  async forceSync(): Promise<void> {
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }
    await this.executeSync();
  }

  private async executeSync(): Promise<void> {
    const keysToSync = Array.from(this.pendingSync());
    if (keysToSync.length === 0) return;

    this.isSyncing.set(true);

    try {
      for (const key of keysToSync) {
        const handler = this.syncHandlers.get(key);
        if (handler) {
          try {
            await handler();
            this.pendingSync.update(set => {
              const newSet = new Set(set);
              newSet.delete(key);
              return newSet;
            });
          } catch (error) {
            console.error(`Sync failed for ${key}:`, error);
          }
        }
      }
    } finally {
      this.isSyncing.set(false);
    }
  }
}
```

### Four-Layer Cache Pattern

```typescript
interface CacheEntry<T> {
  value: T;
  timestamp: number;
  ttl: number;
}

@Injectable({ providedIn: 'root' })
export class FourLayerCache<T> {
  // L1: Memory (instant)
  private l1 = new Map<string, CacheEntry<T>>();

  // L2: LRU with eviction
  private l2 = new Map<string, CacheEntry<T>>();
  private l2Order: string[] = [];
  private readonly l2MaxSize = 1000;

  // L3: IndexedDB
  private readonly db: Dexie;
  private readonly tableName: string;

  constructor(tableName: string) {
    this.tableName = tableName;
    this.db = new Dexie(`Cache_${tableName}`);
    this.db.version(1).stores({
      cache: 'key, value, timestamp, ttl',
    });
  }

  async get(
    key: string,
    loader: () => Promise<T>,
    ttl = 5 * 60 * 1000
  ): Promise<T> {
    const now = Date.now();

    // L1 Check
    const l1Entry = this.l1.get(key);
    if (l1Entry && this.isValid(l1Entry, now)) {
      return l1Entry.value;
    }

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

    // L4: Load from remote
    const value = await loader();
    const entry: CacheEntry<T> = { value, timestamp: now, ttl };

    // Populate all layers
    this.promoteToL1(key, entry);
    this.promoteToL2(key, entry);
    await this.db.table(this.tableName).put({ key, ...entry });

    return value;
  }

  private isValid(entry: CacheEntry<T>, now: number): boolean {
    return now - entry.timestamp < entry.ttl;
  }

  private promoteToL1(key: string, entry: CacheEntry<T>): void {
    // Simple FIFO for L1
    if (this.l1.size >= 100) {
      const firstKey = this.l1.keys().next().value;
      if (firstKey) this.l1.delete(firstKey);
    }
    this.l1.set(key, entry);
  }

  private promoteToL2(key: string, entry: CacheEntry<T>): void {
    // LRU eviction for L2
    const existingIndex = this.l2Order.indexOf(key);
    if (existingIndex > -1) {
      this.l2Order.splice(existingIndex, 1);
    }

    while (this.l2.size >= this.l2MaxSize) {
      const lruKey = this.l2Order.shift();
      if (lruKey) this.l2.delete(lruKey);
    }

    this.l2.set(key, entry);
    this.l2Order.push(key);
  }
}
```

---

## Error Handling Patterns

### Global Error Handler

```typescript
// core/error-handler.ts
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private readonly injector = inject(Injector);

  handleError(error: unknown): void {
    // Avoid circular dependency
    const errorService = this.injector.get(ErrorService);
    const logger = this.injector.get(LoggerService);

    // Log error
    logger.error('Unhandled error', error);

    // Classify and handle
    if (error instanceof HttpErrorResponse) {
      errorService.handleHttpError(error);
    } else if (error instanceof Error) {
      errorService.handleError(error);
    } else {
      errorService.handleUnknown(error);
    }

    // Re-throw in development for debugging
    if (!environment.production) {
      console.error(error);
    }
  }
}

@Injectable({ providedIn: 'root' })
export class ErrorService {
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  handleHttpError(error: HttpErrorResponse): void {
    switch (error.status) {
      case 401:
        this.router.navigate(['/login']);
        break;
      case 403:
        this.toast.error('You do not have permission to perform this action');
        break;
      case 404:
        this.toast.error('Resource not found');
        break;
      case 500:
        this.toast.error('Server error. Please try again later.');
        break;
      default:
        this.toast.error(error.message || 'An error occurred');
    }
  }

  handleError(error: Error): void {
    this.toast.error(error.message);
  }

  handleUnknown(error: unknown): void {
    this.toast.error('An unexpected error occurred');
  }
}

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
  ],
};
```

### Result Type Pattern

```typescript
// Discriminated union for operation results
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

// Helper functions
function ok<T>(data: T): Result<T> {
  return { success: true, data };
}

function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

// Usage in service
@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly apiClient = inject(ApiClient);

  async createUser(data: CreateUserData): Promise<Result<User, string>> {
    // Validation
    if (!data.email) {
      return err('Email is required');
    }

    if (!this.isValidEmail(data.email)) {
      return err('Invalid email format');
    }

    try {
      const user = await firstValueFrom(
        this.apiClient.post<User>('/users', data)
      );
      return ok(user);
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        if (error.status === 409) {
          return err('User already exists');
        }
        return err(error.message);
      }
      return err('Failed to create user');
    }
  }
}

// Usage in component
async onSubmit(): Promise<void> {
  const result = await this.userService.createUser(this.formData());

  if (result.success) {
    this.toast.success('User created successfully');
    this.navGraph.toUserDetail(result.data.id);
  } else {
    this.form.setError(result.error);
  }
}
```

---

## Performance Patterns

### OnPush Change Detection Strategy

```typescript
// Always use OnPush for optimal performance
@Component({
  selector: 'app-list-item',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="list-item">
      <h3>{{ item().title }}</h3>
      <p>{{ item().description }}</p>
    </div>
  `,
})
export class ListItemComponent {
  readonly item = input.required<Item>();
}
```

### Virtual Scrolling Pattern

```typescript
@Component({
  selector: 'app-virtual-list',
  standalone: true,
  imports: [ScrollingModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <cdk-virtual-scroll-viewport
      [itemSize]="itemHeight"
      [minBufferPx]="400"
      [maxBufferPx]="800"
      class="viewport"
    >
      <div
        *cdkVirtualFor="let item of items(); trackBy: trackById"
        class="item"
        [style.height.px]="itemHeight"
      >
        <app-list-item [item]="item" />
      </div>
    </cdk-virtual-scroll-viewport>
  `,
  styles: [`
    .viewport {
      height: 100%;
      width: 100%;
    }
  `],
})
export class VirtualListComponent {
  readonly items = input.required<Item[]>();
  readonly itemHeight = 72;

  trackById(index: number, item: Item): string {
    return item.id;
  }
}
```

### Defer Loading Pattern

```typescript
@Component({
  template: `
    <!-- Immediate load for above-the-fold content -->
    <app-header />
    <app-hero-banner />

    <!-- Defer below-the-fold content -->
    @defer (on viewport) {
      <app-featured-products />
    } @placeholder {
      <div class="skeleton" style="height: 300px"></div>
    }

    @defer (on viewport; prefetch on idle) {
      <app-reviews />
    } @placeholder {
      <div class="skeleton" style="height: 200px"></div>
    }

    <!-- Defer heavy components -->
    @defer (on interaction) {
      <app-rich-text-editor />
    } @placeholder {
      <button>Click to load editor</button>
    }

    <!-- Defer with loading state -->
    @defer (when showChart()) {
      <app-analytics-chart />
    } @loading (minimum 200ms) {
      <app-chart-skeleton />
    } @error {
      <app-error-message message="Failed to load chart" />
    }
  `,
})
export class ProductPageComponent {
  readonly showChart = signal(false);

  loadChart(): void {
    this.showChart.set(true);
  }
}
```

### Memoization Pattern

```typescript
// Computed signals are automatically memoized
@Injectable()
export class CalculationService {
  private readonly items = signal<Item[]>([]);

  // Automatically memoized - only recalculates when items change
  readonly totalValue = computed(() =>
    this.items().reduce((sum, item) => sum + item.value, 0)
  );

  readonly groupedByCategory = computed(() => {
    const items = this.items();
    return items.reduce((groups, item) => {
      const key = item.category;
      groups[key] = groups[key] || [];
      groups[key].push(item);
      return groups;
    }, {} as Record<string, Item[]>);
  });

  // Derived computed from other computed
  readonly averageValue = computed(() =>
    this.items().length > 0
      ? this.totalValue() / this.items().length
      : 0
  );
}
```

---

## Testing Patterns

### Component Testing with Testing Library

```typescript
import { render, screen, fireEvent } from '@testing-library/angular';
import { userEvent } from '@testing-library/user-event';

describe('LoginComponent', () => {
  it('should show validation errors on blur', async () => {
    await render(LoginComponent, {
      providers: [
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.click(emailInput);
    await userEvent.tab(); // Blur

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it('should call login on valid submit', async () => {
    const mockLogin = jest.fn().mockResolvedValue(undefined);
    mockAuthService.login = mockLogin;

    await render(LoginComponent, {
      providers: [
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
      rememberMe: false,
    });
  });

  it('should disable submit button while loading', async () => {
    mockAuthService.login = () => new Promise(() => {}); // Never resolves

    await render(LoginComponent, {
      providers: [
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/signing in/i)).toBeInTheDocument();
  });
});
```

### ViewModel Testing

```typescript
describe('LoginViewModel', () => {
  let viewModel: LoginViewModel;
  let mockAuthService: jest.Mocked<AuthService>;

  beforeEach(() => {
    mockAuthService = {
      login: jest.fn(),
    } as any;

    TestBed.configureTestingModule({
      providers: [
        LoginViewModel,
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    viewModel = TestBed.inject(LoginViewModel);
  });

  describe('input handling', () => {
    it('should update email on SET_EMAIL input', () => {
      viewModel.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });

      expect(viewModel.output().email).toBe('test@example.com');
    });

    it('should validate email format', () => {
      viewModel.onInput({ type: 'SET_EMAIL', email: 'invalid' });

      expect(viewModel.output().emailError).toBe('Invalid email format');
    });

    it('should clear email error for valid email', () => {
      viewModel.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });

      expect(viewModel.output().emailError).toBeNull();
    });
  });

  describe('submit handling', () => {
    beforeEach(() => {
      viewModel.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });
      viewModel.onInput({ type: 'SET_PASSWORD', password: 'password123' });
    });

    it('should set loading state during submit', fakeAsync(() => {
      mockAuthService.login.mockImplementation(() => new Promise(() => {}));

      viewModel.onInput({ type: 'SUBMIT' });

      expect(viewModel.output().isLoading).toBe(true);
    }));

    it('should emit NAVIGATE_TO_HOME on success', fakeAsync(() => {
      mockAuthService.login.mockResolvedValue(undefined);
      const effects: LoginEffect[] = [];
      viewModel.effect$.subscribe(e => effects.push(e));

      viewModel.onInput({ type: 'SUBMIT' });
      tick();

      expect(effects).toContainEqual({ type: 'NAVIGATE_TO_HOME' });
    }));

    it('should emit SHOW_ERROR on failure', fakeAsync(() => {
      mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));
      const effects: LoginEffect[] = [];
      viewModel.effect$.subscribe(e => effects.push(e));

      viewModel.onInput({ type: 'SUBMIT' });
      tick();

      expect(effects).toContainEqual({
        type: 'SHOW_ERROR',
        message: 'Invalid credentials',
      });
    }));
  });
});
```

### Integration Testing with Cypress

```typescript
// cypress/e2e/login.cy.ts
describe('Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('should login successfully', () => {
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: { access_token: 'token', refresh_token: 'refresh' },
    }).as('login');

    cy.get('[data-testid="email-input"]').type('user@example.com');
    cy.get('[data-testid="password-input"]').type('password123');
    cy.get('[data-testid="submit-button"]').click();

    cy.wait('@login');
    cy.url().should('include', '/home');
  });

  it('should show error for invalid credentials', () => {
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: { message: 'Invalid credentials' },
    }).as('login');

    cy.get('[data-testid="email-input"]').type('user@example.com');
    cy.get('[data-testid="password-input"]').type('wrongpassword');
    cy.get('[data-testid="submit-button"]').click();

    cy.wait('@login');
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid credentials');
  });

  it('should validate form before submit', () => {
    cy.get('[data-testid="submit-button"]').should('be.disabled');

    cy.get('[data-testid="email-input"]').type('invalid-email');
    cy.get('[data-testid="email-input"]').blur();
    cy.get('[data-testid="email-error"]').should('be.visible');

    cy.get('[data-testid="email-input"]').clear().type('valid@email.com');
    cy.get('[data-testid="email-error"]').should('not.exist');
  });
});
```
