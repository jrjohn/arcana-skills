# React Developer Skill - Design Patterns

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
│  │  Components ←──→ ViewModel Hooks ←──→ Domain Services   │ │
│  │     │                              │                     │ │
│  │     └──── React State ────────────→│                     │ │
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
│  │                  │   (Axios)  │                          │ │
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
export class OrderService {
  constructor(private readonly repository: IOrderRepository) {}

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
export class OrderRepositoryImpl implements IOrderRepository {
  constructor(
    private readonly apiClient: AxiosInstance,
    private readonly localDb: OrderDatabase
  ) {}

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
// features/users/index.ts - Public API
export { UserRoutes } from './routes';
export { useUserService } from './hooks/useUserService';
export type { User } from './models/user.model';

// features/users/routes.tsx
export const UserRoutes: RouteObject[] = [
  {
    path: 'users',
    element: <UserLayout />,
    children: [
      {
        index: true,
        lazy: () => import('./pages/UserListPage'),
      },
      {
        path: ':id',
        lazy: () => import('./pages/UserDetailPage'),
      },
      {
        path: ':id/edit',
        lazy: () => import('./pages/UserEditPage'),
      },
    ],
  },
];
```

---

## State Management Patterns

### Hook-Based State Pattern

```typescript
// Centralized feature state with hooks
interface FeatureState<T extends Record<string, unknown>> {
  state: T;
  setState: React.Dispatch<React.SetStateAction<T>>;
}

function useFeatureState<T extends Record<string, unknown>>(
  initialState: T
): FeatureState<T> {
  const [state, setState] = useState<T>(initialState);
  return { state, setState };
}

// Usage
interface UserListState {
  users: User[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
}

function useUserListState() {
  const [state, setState] = useState<UserListState>({
    users: [],
    loading: false,
    error: null,
    selectedId: null,
  });

  // Derived state
  const selectedUser = useMemo(
    () => state.users.find(u => u.id === state.selectedId) ?? null,
    [state.users, state.selectedId]
  );

  const activeUsers = useMemo(
    () => state.users.filter(u => u.status === 'active'),
    [state.users]
  );

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  }, []);

  const setUsers = useCallback((users: User[]) => {
    setState(prev => ({ ...prev, users }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const selectUser = useCallback((selectedId: string | null) => {
    setState(prev => ({ ...prev, selectedId }));
  }, []);

  return {
    ...state,
    selectedUser,
    activeUsers,
    setLoading,
    setUsers,
    setError,
    selectUser,
  };
}
```

### Input/Output/Effect Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      ViewModel Hook                          │
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
// Generic ViewModel hook pattern
interface ViewModelResult<TInput, TOutput, TEffect> {
  output: TOutput;
  effect$: Observable<TEffect>;
  onInput: (input: TInput) => void;
}

function useViewModel<TInput, TOutput, TEffect>(
  initialState: TOutput,
  handlers: {
    onInput: (
      input: TInput,
      state: TOutput,
      setState: React.Dispatch<React.SetStateAction<TOutput>>,
      emit: (effect: TEffect) => void
    ) => void;
  }
): ViewModelResult<TInput, TOutput, TEffect> {
  const [state, setState] = useState<TOutput>(initialState);
  const effectRef = useRef(new Subject<TEffect>());

  const emit = useCallback((effect: TEffect) => {
    effectRef.current.next(effect);
  }, []);

  const onInput = useCallback(
    (input: TInput) => {
      handlers.onInput(input, state, setState, emit);
    },
    [state, handlers, emit]
  );

  return {
    output: state,
    effect$: effectRef.current.asObservable(),
    onInput,
  };
}
```

---

## Component Patterns

### Smart/Dumb Component Pattern

```typescript
// Smart Component (Container) - has logic, uses hooks
interface UserListContainerProps {
  initialFilters?: UserFilters;
}

export const UserListContainer: React.FC<UserListContainerProps> = ({
  initialFilters,
}) => {
  const { output, onInput } = useUserListViewModel(initialFilters);
  const navGraph = useNavGraph();

  if (output.isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <UserList
      users={output.users}
      selectedId={output.selectedId}
      onUserSelect={(userId) => onInput({ type: 'SELECT_USER', userId })}
      onUserDelete={(userId) => onInput({ type: 'DELETE_USER', userId })}
      onUserClick={(userId) => navGraph.toUserDetail(userId)}
    />
  );
};

// Dumb Component (Presentational) - pure props
interface UserListProps {
  users: User[];
  selectedId: string | null;
  onUserSelect: (userId: string) => void;
  onUserDelete: (userId: string) => void;
  onUserClick: (userId: string) => void;
}

export const UserList = memo<UserListProps>(({
  users,
  selectedId,
  onUserSelect,
  onUserDelete,
  onUserClick,
}) => (
  <ul className="user-list">
    {users.map((user) => (
      <li
        key={user.id}
        className={user.id === selectedId ? 'selected' : ''}
        onClick={() => onUserClick(user.id)}
      >
        <span className="name">{user.name}</span>
        <span className="email">{user.email}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onUserDelete(user.id);
          }}
        >
          Delete
        </button>
      </li>
    ))}
  </ul>
));

UserList.displayName = 'UserList';
```

### Compound Component Pattern

```typescript
// Parent component that manages shared state
interface AccordionContextValue {
  expandedItems: Set<string>;
  toggle: (id: string) => void;
  multiple: boolean;
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

interface AccordionProps {
  children: React.ReactNode;
  multiple?: boolean;
}

export const Accordion: React.FC<AccordionProps> = ({
  children,
  multiple = false,
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggle = useCallback(
    (id: string) => {
      setExpandedItems((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(id)) {
          newSet.delete(id);
        } else {
          if (!multiple) {
            newSet.clear();
          }
          newSet.add(id);
        }
        return newSet;
      });
    },
    [multiple]
  );

  return (
    <AccordionContext.Provider value={{ expandedItems, toggle, multiple }}>
      <div className="accordion">{children}</div>
    </AccordionContext.Provider>
  );
};

// Child component
interface AccordionItemProps {
  id: string;
  header: React.ReactNode;
  children: React.ReactNode;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  id,
  header,
  children,
}) => {
  const context = useContext(AccordionContext);
  if (!context) throw new Error('AccordionItem must be inside Accordion');

  const isExpanded = context.expandedItems.has(id);

  return (
    <div className="accordion-item">
      <button
        className="accordion-header"
        onClick={() => context.toggle(id)}
        aria-expanded={isExpanded}
      >
        {header}
        <span className="icon">{isExpanded ? '−' : '+'}</span>
      </button>

      {isExpanded && (
        <div className="accordion-content">
          {children}
        </div>
      )}
    </div>
  );
};

// Usage
const MyPage: React.FC = () => (
  <Accordion>
    <AccordionItem id="item1" header="Section 1">
      Content for section 1
    </AccordionItem>
    <AccordionItem id="item2" header="Section 2">
      Content for section 2
    </AccordionItem>
  </Accordion>
);
```

### Render Props Pattern

```typescript
interface DataLoaderProps<T> {
  loader: () => Promise<T>;
  children: (data: T) => React.ReactNode;
  loading?: React.ReactNode;
  error?: (error: string) => React.ReactNode;
}

export function DataLoader<T>({
  loader,
  children,
  loading = <div>Loading...</div>,
  error = (msg) => <div className="error">{msg}</div>,
}: DataLoaderProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setIsLoading(true);
      setErrorMsg(null);

      try {
        const result = await loader();
        if (mounted) {
          setData(result);
        }
      } catch (e) {
        if (mounted) {
          setErrorMsg(e instanceof Error ? e.message : 'Unknown error');
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, [loader]);

  if (isLoading) return <>{loading}</>;
  if (errorMsg) return <>{error(errorMsg)}</>;
  if (data === null) return null;

  return <>{children(data)}</>;
}

// Usage
const UsersPage: React.FC = () => {
  const userService = useUserService();
  const loadUsers = useCallback(() => userService.getAll(), [userService]);

  return (
    <DataLoader
      loader={loadUsers}
      loading={<SkeletonLoader />}
      error={(msg) => <ErrorBanner message={msg} />}
    >
      {(users) => <UserList users={users} />}
    </DataLoader>
  );
};
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
export class SyncManager {
  private syncHandlers = new Map<string, () => Promise<void>>();
  private pendingSync = new Set<string>();
  private syncTimeout: ReturnType<typeof setTimeout> | null = null;
  private _isSyncing = false;

  get isSyncing(): boolean {
    return this._isSyncing;
  }

  get hasPendingChanges(): boolean {
    return this.pendingSync.size > 0;
  }

  register(key: string, handler: () => Promise<void>): void {
    this.syncHandlers.set(key, handler);
  }

  scheduleSync(key: string, delayMs = 1000): void {
    this.pendingSync.add(key);

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
    const keysToSync = Array.from(this.pendingSync);
    if (keysToSync.length === 0) return;

    this._isSyncing = true;

    try {
      for (const key of keysToSync) {
        const handler = this.syncHandlers.get(key);
        if (handler) {
          try {
            await handler();
            this.pendingSync.delete(key);
          } catch (error) {
            console.error(`Sync failed for ${key}:`, error);
          }
        }
      }
    } finally {
      this._isSyncing = false;
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
    if (this.l1.size >= 100) {
      const firstKey = this.l1.keys().next().value;
      if (firstKey) this.l1.delete(firstKey);
    }
    this.l1.set(key, entry);
  }

  private promoteToL2(key: string, entry: CacheEntry<T>): void {
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

### Global Error Boundary

```typescript
// core/components/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode | ((error: Error, reset: () => void) => React.ReactNode);
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to service
    console.error('Error caught by boundary:', error, errorInfo);
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): React.ReactNode {
    if (this.state.hasError && this.state.error) {
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(this.state.error, this.reset);
      }
      return this.props.fallback ?? <DefaultErrorFallback error={this.state.error} reset={this.reset} />;
    }

    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error: Error; reset: () => void }> = ({
  error,
  reset,
}) => (
  <div className="error-fallback">
    <h2>Something went wrong</h2>
    <p>{error.message}</p>
    <button onClick={reset}>Try again</button>
  </div>
);
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
export class UserService {
  constructor(private readonly repository: IUserRepository) {}

  async createUser(data: CreateUserData): Promise<Result<User, string>> {
    // Validation
    if (!data.email) {
      return err('Email is required');
    }

    if (!this.isValidEmail(data.email)) {
      return err('Invalid email format');
    }

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

  private isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}

// Usage in component
const handleSubmit = async () => {
  const result = await userService.createUser(formData);

  if (result.success) {
    toast.success('User created successfully');
    navGraph.toUserDetail(result.data.id);
  } else {
    setError(result.error);
  }
};
```

---

## Performance Patterns

### Memoization Pattern

```typescript
// React.memo for components
export const UserCard = memo<UserCardProps>(({ user, onSelect }) => (
  <div className="user-card" onClick={() => onSelect(user.id)}>
    <img src={user.avatar} alt={user.name} />
    <h3>{user.name}</h3>
    <p>{user.email}</p>
  </div>
));

// useMemo for expensive computations
function useFilteredUsers(users: User[], filters: Filters) {
  return useMemo(() => {
    let filtered = [...users];

    if (filters.status) {
      filtered = filtered.filter(u => u.status === filters.status);
    }

    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(
        u =>
          u.name.toLowerCase().includes(query) ||
          u.email.toLowerCase().includes(query)
      );
    }

    if (filters.sortBy) {
      filtered.sort((a, b) => {
        const aVal = a[filters.sortBy!];
        const bVal = b[filters.sortBy!];
        return filters.sortOrder === 'desc'
          ? String(bVal).localeCompare(String(aVal))
          : String(aVal).localeCompare(String(bVal));
      });
    }

    return filtered;
  }, [users, filters]);
}

// useCallback for event handlers
function useUserActions(repository: IUserRepository) {
  const selectUser = useCallback((userId: string) => {
    // Handle selection
  }, []);

  const deleteUser = useCallback(
    async (userId: string) => {
      await repository.delete(userId);
    },
    [repository]
  );

  return { selectUser, deleteUser };
}
```

### Virtual Scrolling Pattern

```typescript
import { FixedSizeList as List } from 'react-window';

interface VirtualListProps {
  items: Item[];
  itemHeight: number;
  onItemClick: (id: string) => void;
}

export const VirtualList: React.FC<VirtualListProps> = ({
  items,
  itemHeight,
  onItemClick,
}) => {
  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => {
      const item = items[index];
      return (
        <div
          style={style}
          className="virtual-list-item"
          onClick={() => onItemClick(item.id)}
        >
          <ListItem item={item} />
        </div>
      );
    },
    [items, onItemClick]
  );

  return (
    <List
      height={600}
      itemCount={items.length}
      itemSize={itemHeight}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

### Lazy Loading Pattern

```typescript
// router/routes.tsx
import { lazy, Suspense } from 'react';

const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const UsersPage = lazy(() => import('../pages/UsersPage'));
const SettingsPage = lazy(() => import('../pages/SettingsPage'));

const PageLoader: React.FC = () => (
  <div className="page-loader">
    <Spinner />
  </div>
);

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageLoader />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: 'users',
        element: (
          <Suspense fallback={<PageLoader />}>
            <UsersPage />
          </Suspense>
        ),
      },
      {
        path: 'settings',
        element: (
          <Suspense fallback={<PageLoader />}>
            <SettingsPage />
          </Suspense>
        ),
      },
    ],
  },
];
```

---

## Testing Patterns

### Component Testing with React Testing Library

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginPage } from './LoginPage';

describe('LoginPage', () => {
  const mockLogin = vi.fn();
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show validation errors on blur', async () => {
    render(<LoginPage onLogin={mockLogin} />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.click(emailInput);
    await userEvent.tab(); // Blur

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it('should call login on valid submit', async () => {
    mockLogin.mockResolvedValue(undefined);

    render(<LoginPage onLogin={mockLogin} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        rememberMe: false,
      });
    });
  });

  it('should disable submit button while loading', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<LoginPage onLogin={mockLogin} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/signing in/i)).toBeInTheDocument();
  });
});
```

### ViewModel Hook Testing

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLoginViewModel } from './useLoginViewModel';

describe('useLoginViewModel', () => {
  const mockAuthService = {
    login: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should update email on SET_EMAIL input', () => {
    const { result } = renderHook(() => useLoginViewModel(mockAuthService));

    act(() => {
      result.current.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });
    });

    expect(result.current.output.email).toBe('test@example.com');
  });

  it('should validate email format', () => {
    const { result } = renderHook(() => useLoginViewModel(mockAuthService));

    act(() => {
      result.current.onInput({ type: 'SET_EMAIL', email: 'invalid' });
    });

    expect(result.current.output.emailError).toBe('Invalid email format');
  });

  it('should set loading state during submit', async () => {
    mockAuthService.login.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useLoginViewModel(mockAuthService));

    act(() => {
      result.current.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });
      result.current.onInput({ type: 'SET_PASSWORD', password: 'password123' });
    });

    act(() => {
      result.current.onInput({ type: 'SUBMIT' });
    });

    expect(result.current.output.isLoading).toBe(true);
  });

  it('should emit NAVIGATE_TO_HOME on success', async () => {
    mockAuthService.login.mockResolvedValue(undefined);
    const effects: any[] = [];

    const { result } = renderHook(() => useLoginViewModel(mockAuthService));

    result.current.effect$.subscribe((e) => effects.push(e));

    act(() => {
      result.current.onInput({ type: 'SET_EMAIL', email: 'test@example.com' });
      result.current.onInput({ type: 'SET_PASSWORD', password: 'password123' });
    });

    await act(async () => {
      result.current.onInput({ type: 'SUBMIT' });
    });

    await waitFor(() => {
      expect(effects).toContainEqual({ type: 'NAVIGATE_TO_HOME' });
    });
  });
});
```
