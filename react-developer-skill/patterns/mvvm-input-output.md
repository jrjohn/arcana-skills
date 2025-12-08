# MVVM Input/Output/Effect Pattern for React

Deep dive into the MVVM Input/Output/Effect pattern implementation using React hooks.

---

## Overview

The Input/Output/Effect pattern provides a unidirectional data flow architecture for React components:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Component                                    │
│                                                                  │
│   User Actions ──→ onInput() ──→ ViewModel Hook                 │
│                                       │                          │
│                                       ├──→ Update State (Output) │
│                                       │                          │
│                                       └──→ Emit Effect           │
│                                              │                   │
│   UI Render ←── output ←───────────────────┘                    │
│                                                                  │
│   Side Effects ←── effect$ ←────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Input (Actions)

Discriminated union types that define all possible user actions:

```typescript
export type UserInput =
  | { type: 'UPDATE_NAME'; name: string }
  | { type: 'UPDATE_EMAIL'; email: string }
  | { type: 'SUBMIT' }
  | { type: 'RESET' };
```

### Output (State)

Immutable state container exposed as a memoized object:

```typescript
export interface UserOutput {
  name: string;
  email: string;
  isLoading: boolean;
  error: string | null;
  canSubmit: boolean;
}
```

### Effect (Side Effects)

One-time events that trigger navigation, toasts, dialogs, etc.:

```typescript
export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_TOAST'; message: string }
  | { type: 'OPEN_DIALOG'; dialogType: 'confirm' | 'error' };
```

---

## Implementation Pattern

### Basic ViewModel Hook

```typescript
import { useState, useCallback, useMemo, useRef } from 'react';
import { Subject } from 'rxjs';

// Types
export type UserInput =
  | { type: 'UPDATE_NAME'; name: string }
  | { type: 'UPDATE_EMAIL'; email: string }
  | { type: 'SUBMIT' };

export interface UserOutput {
  name: string;
  email: string;
  isLoading: boolean;
  error: string | null;
}

export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_TOAST'; message: string };

// Hook
export function useUserViewModel(userService: UserService) {
  // State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Effect stream
  const effectRef = useRef(new Subject<UserEffect>());
  const effect$ = effectRef.current.asObservable();

  // Output (memoized)
  const output = useMemo<UserOutput>(() => ({
    name,
    email,
    isLoading,
    error,
  }), [name, email, isLoading, error]);

  // Emit effect helper
  const emit = useCallback((effect: UserEffect) => {
    effectRef.current.next(effect);
  }, []);

  // Submit handler
  const handleSubmit = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await userService.updateUser({ name, email });
      emit({ type: 'SHOW_TOAST', message: 'User updated successfully' });
      emit({ type: 'NAVIGATE_BACK' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [name, email, userService, emit]);

  // Input handler
  const onInput = useCallback((input: UserInput) => {
    switch (input.type) {
      case 'UPDATE_NAME':
        setName(input.name);
        break;
      case 'UPDATE_EMAIL':
        setEmail(input.email);
        break;
      case 'SUBMIT':
        handleSubmit();
        break;
    }
  }, [handleSubmit]);

  return { output, effect$, onInput };
}
```

### Component Usage

```typescript
import React, { memo, useEffect } from 'react';
import { useUserViewModel } from './useUserViewModel';
import { useUserService } from '../../../core/hooks/useUserService';
import { useNavGraph } from '../../../core/hooks/useNavGraph';
import { useToast } from '../../../shared/hooks/useToast';

export const UserForm = memo(() => {
  const userService = useUserService();
  const navGraph = useNavGraph();
  const toast = useToast();
  const { output, effect$, onInput } = useUserViewModel(userService);

  // Handle effects
  useEffect(() => {
    const subscription = effect$.subscribe((effect) => {
      switch (effect.type) {
        case 'NAVIGATE_BACK':
          navGraph.back();
          break;
        case 'SHOW_TOAST':
          toast.success(effect.message);
          break;
      }
    });

    return () => subscription.unsubscribe();
  }, [effect$, navGraph, toast]);

  return (
    <form onSubmit={(e) => { e.preventDefault(); onInput({ type: 'SUBMIT' }); }}>
      <input
        value={output.name}
        onChange={(e) => onInput({ type: 'UPDATE_NAME', name: e.target.value })}
      />
      <input
        value={output.email}
        onChange={(e) => onInput({ type: 'UPDATE_EMAIL', email: e.target.value })}
      />
      {output.error && <div className="error">{output.error}</div>}
      <button type="submit" disabled={output.isLoading}>
        {output.isLoading ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
});

UserForm.displayName = 'UserForm';
```

---

## Advanced Patterns

### With Validation

```typescript
export function useFormViewModel() {
  const [email, setEmail] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);

  // Validation (memoized)
  const emailError = useMemo(() => {
    if (!emailTouched) return null;
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
    return null;
  }, [email, emailTouched]);

  const canSubmit = useMemo(() => {
    return email.length > 0 && !emailError;
  }, [email, emailError]);

  const output = useMemo(() => ({
    email,
    emailError,
    canSubmit,
  }), [email, emailError, canSubmit]);

  const onInput = useCallback((input: FormInput) => {
    switch (input.type) {
      case 'SET_EMAIL':
        setEmail(input.email);
        setEmailTouched(true);
        break;
    }
  }, []);

  return { output, onInput };
}
```

### With Derived State

```typescript
export function useProductListViewModel(repository: IProductRepository) {
  const [products, setProducts] = useState<Product[]>([]);
  const [filters, setFilters] = useState<Filters>({ category: null, minPrice: 0 });
  const [sortBy, setSortBy] = useState<string>('name');

  // Derived state (memoized)
  const filteredProducts = useMemo(() => {
    return products
      .filter((p) => {
        if (filters.category && p.category !== filters.category) return false;
        if (p.price < filters.minPrice) return false;
        return true;
      })
      .sort((a, b) => {
        const aVal = a[sortBy as keyof Product];
        const bVal = b[sortBy as keyof Product];
        return String(aVal).localeCompare(String(bVal));
      });
  }, [products, filters, sortBy]);

  const totalValue = useMemo(
    () => filteredProducts.reduce((sum, p) => sum + p.price, 0),
    [filteredProducts]
  );

  const output = useMemo(() => ({
    products: filteredProducts,
    totalValue,
    filters,
    sortBy,
  }), [filteredProducts, totalValue, filters, sortBy]);

  return { output, onInput };
}
```

### With Async Loading

```typescript
export function useDataViewModel<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectRef = useRef(new Subject<DataEffect>());
  const effect$ = effectRef.current.asObservable();

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await loader();
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data';
      setError(message);
      effectRef.current.next({ type: 'SHOW_ERROR', message });
    } finally {
      setIsLoading(false);
    }
  }, [loader]);

  // Initial load
  useEffect(() => {
    load();
  }, [load]);

  const output = useMemo(() => ({
    data,
    isLoading,
    error,
    hasData: data !== null,
  }), [data, isLoading, error]);

  const onInput = useCallback((input: DataInput) => {
    switch (input.type) {
      case 'REFRESH':
        load();
        break;
    }
  }, [load]);

  return { output, effect$, onInput };
}
```

---

## Effect Handling Patterns

### Using RxJS Subject

```typescript
// ViewModel
const effectRef = useRef(new Subject<UserEffect>());
const effect$ = effectRef.current.asObservable();

const emit = useCallback((effect: UserEffect) => {
  effectRef.current.next(effect);
}, []);

// Component
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
```

### Using Callback Props (Alternative)

```typescript
// ViewModel with callbacks
export function useUserViewModel(
  userService: UserService,
  onNavigateBack: () => void,
  onShowToast: (message: string) => void
) {
  const handleSubmit = useCallback(async () => {
    try {
      await userService.updateUser({ name, email });
      onShowToast('User updated successfully');
      onNavigateBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [name, email, userService, onNavigateBack, onShowToast]);

  // ...
}

// Component usage
const UserFormPage: React.FC = () => {
  const navGraph = useNavGraph();
  const toast = useToast();

  const { output, onInput } = useUserViewModel(
    userService,
    navGraph.back,
    toast.success
  );

  // No effect subscription needed
  return <UserForm output={output} onInput={onInput} />;
};
```

---

## Testing ViewModel Hooks

### Basic Test Structure

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useUserViewModel } from './useUserViewModel';

describe('useUserViewModel', () => {
  const mockUserService = {
    updateUser: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should update name on SET_NAME input', () => {
    const { result } = renderHook(() => useUserViewModel(mockUserService));

    act(() => {
      result.current.onInput({ type: 'UPDATE_NAME', name: 'John' });
    });

    expect(result.current.output.name).toBe('John');
  });

  it('should set loading state during submit', async () => {
    mockUserService.updateUser.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useUserViewModel(mockUserService));

    act(() => {
      result.current.onInput({ type: 'UPDATE_NAME', name: 'John' });
      result.current.onInput({ type: 'UPDATE_EMAIL', email: 'john@example.com' });
    });

    act(() => {
      result.current.onInput({ type: 'SUBMIT' });
    });

    expect(result.current.output.isLoading).toBe(true);
  });

  it('should emit NAVIGATE_BACK effect on success', async () => {
    mockUserService.updateUser.mockResolvedValue(undefined);
    const effects: UserEffect[] = [];

    const { result } = renderHook(() => useUserViewModel(mockUserService));

    result.current.effect$.subscribe((e) => effects.push(e));

    act(() => {
      result.current.onInput({ type: 'UPDATE_NAME', name: 'John' });
      result.current.onInput({ type: 'UPDATE_EMAIL', email: 'john@example.com' });
    });

    await act(async () => {
      result.current.onInput({ type: 'SUBMIT' });
    });

    await waitFor(() => {
      expect(effects).toContainEqual({ type: 'NAVIGATE_BACK' });
    });
  });

  it('should set error on failure', async () => {
    mockUserService.updateUser.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useUserViewModel(mockUserService));

    act(() => {
      result.current.onInput({ type: 'UPDATE_NAME', name: 'John' });
      result.current.onInput({ type: 'UPDATE_EMAIL', email: 'john@example.com' });
    });

    await act(async () => {
      result.current.onInput({ type: 'SUBMIT' });
    });

    await waitFor(() => {
      expect(result.current.output.error).toBe('Network error');
    });
  });
});
```

---

## Best Practices

### 1. Keep Input Types Exhaustive

```typescript
// Define all possible actions upfront
export type FormInput =
  | { type: 'SET_FIELD'; field: string; value: string }
  | { type: 'VALIDATE_FIELD'; field: string }
  | { type: 'SUBMIT' }
  | { type: 'RESET' }
  | { type: 'CANCEL' };
```

### 2. Memoize Output Object

```typescript
// Always wrap output in useMemo
const output = useMemo<UserOutput>(() => ({
  name,
  email,
  isLoading,
  error,
}), [name, email, isLoading, error]);
```

### 3. Use Discriminated Unions for Effects

```typescript
// Each effect type should be distinct and typed
export type UserEffect =
  | { type: 'NAVIGATE_TO'; path: string }
  | { type: 'SHOW_TOAST'; message: string; severity: 'success' | 'error' }
  | { type: 'OPEN_MODAL'; modalId: string; data?: unknown };
```

### 4. Handle All Input Types in Switch

```typescript
const onInput = useCallback((input: UserInput) => {
  switch (input.type) {
    case 'UPDATE_NAME':
      setName(input.name);
      break;
    case 'UPDATE_EMAIL':
      setEmail(input.email);
      break;
    case 'SUBMIT':
      handleSubmit();
      break;
    // TypeScript will warn if any case is missing
  }
}, [handleSubmit]);
```

### 5. Separate Concerns

```typescript
// Validation logic
const validation = useValidation({ name, email });

// Loading state
const loading = useLoadingState();

// Effects
const effects = useEffects();

// Combine in output
const output = useMemo(() => ({
  ...validation,
  ...loading,
  name,
  email,
}), [validation, loading, name, email]);
```

---

## Migration from useState to Input/Output/Effect

### Before (Traditional React)

```typescript
function UserForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setLoading(true);
    await userService.update({ name, email });
    setLoading(false);
    navigate('/users');
  };

  return (
    <form>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <button onClick={handleSubmit} disabled={loading}>
        Save
      </button>
    </form>
  );
}
```

### After (Input/Output/Effect)

```typescript
// ViewModel Hook
function useUserFormViewModel(userService: UserService) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const effectRef = useRef(new Subject<UserEffect>());

  const output = useMemo(() => ({ name, email, isLoading }), [name, email, isLoading]);
  const effect$ = effectRef.current.asObservable();

  const onInput = useCallback((input: UserInput) => {
    switch (input.type) {
      case 'SET_NAME': setName(input.name); break;
      case 'SET_EMAIL': setEmail(input.email); break;
      case 'SUBMIT':
        setIsLoading(true);
        userService.update({ name, email }).then(() => {
          setIsLoading(false);
          effectRef.current.next({ type: 'NAVIGATE_TO_USERS' });
        });
        break;
    }
  }, [name, email, userService]);

  return { output, effect$, onInput };
}

// Component
function UserForm() {
  const { output, effect$, onInput } = useUserFormViewModel(userService);
  const navigate = useNavigate();

  useEffect(() => {
    const sub = effect$.subscribe((e) => {
      if (e.type === 'NAVIGATE_TO_USERS') navigate('/users');
    });
    return () => sub.unsubscribe();
  }, [effect$, navigate]);

  return (
    <form onSubmit={(e) => { e.preventDefault(); onInput({ type: 'SUBMIT' }); }}>
      <input
        value={output.name}
        onChange={(e) => onInput({ type: 'SET_NAME', name: e.target.value })}
      />
      <input
        value={output.email}
        onChange={(e) => onInput({ type: 'SET_EMAIL', email: e.target.value })}
      />
      <button type="submit" disabled={output.isLoading}>Save</button>
    </form>
  );
}
```

---

## Benefits

1. **Testability**: ViewModels can be tested in isolation without rendering
2. **Predictability**: All state changes flow through `onInput`
3. **Type Safety**: Discriminated unions ensure exhaustive handling
4. **Separation of Concerns**: Logic separated from presentation
5. **Reusability**: ViewModel hooks can be reused across components
6. **Debugging**: Single entry point for all actions makes debugging easier
