# MVVM Input/Output/Effect Pattern for Vue 3

Deep dive into the MVVM Input/Output/Effect (I/O/E) pattern implementation using Vue 3 Composition API composables.

---

## Overview

The I/O/E pattern provides a unidirectional data flow architecture for Vue components. ViewModels expose four key properties:

```
+-------------------------------------------------------------------+
|                     Component (SFC)                                |
|                                                                    |
|   v-model bindings --> models (refs) --> ViewModel Composable      |
|                                              |                     |
|                                              +-> Update outputs    |
|                                              |   (computed)        |
|                                              +-> Emit effects      |
|                                                    |               |
|   Template <-- outputs (computed) <--------------+                |
|   Effect handler <-- onEffect callback <----------+               |
+-------------------------------------------------------------------+
```

---

## Core Concepts

### Models (Two-Way Bindable Refs)

Reactive `ref` values that components bind to via `v-model`:

```typescript
const name = ref('');
const email = ref('');
// Used in template: v-model="vm.models.name.value"
```

### Outputs (Read-Only Computed State)

Computed properties exposing derived or internal state:

```typescript
const outputs = {
  isLoading: computed(() => isLoading.value),
  error: computed(() => error.value),
  canSubmit: computed(() => name.value.length > 0 && !isLoading.value),
};
```

### Inputs (Action Methods)

Functions that handle user actions and trigger state changes:

```typescript
const inputs = {
  async submit() { /* handle submission */ },
  reset() { name.value = ''; email.value = ''; },
  touchEmail() { emailTouched.value = true; },
};
```

### Effects (Side Effect Emitters)

One-time events for navigation, toasts, dialogs:

```typescript
export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_TOAST'; message: string }
  | { type: 'OPEN_DIALOG'; dialogType: 'confirm' | 'error' };

const effectCallbacks: Array<(effect: UserEffect) => void> = [];
const onEffect = (cb: (effect: UserEffect) => void) => { effectCallbacks.push(cb); };
const emitEffect = (effect: UserEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };
```

---

## Complete Implementation Pattern

```typescript
// presentation/view-models/useUserViewModel.ts
import { ref, computed } from 'vue';
import { useInject } from '@/core/di/use-inject';
import { TOKENS } from '@/core/di/tokens';
import type { IUserService } from '@/domain/services/user.service';

export type UserEffect =
  | { type: 'NAVIGATE_BACK' }
  | { type: 'SHOW_TOAST'; message: string };

export function useUserViewModel() {
  const userService = useInject<IUserService>(TOKENS.UserService);

  // Models
  const name = ref('');
  const email = ref('');

  // Internal state
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Effects
  const effectCallbacks: Array<(effect: UserEffect) => void> = [];
  const onEffect = (cb: (effect: UserEffect) => void) => { effectCallbacks.push(cb); };
  const emitEffect = (effect: UserEffect) => { effectCallbacks.forEach((cb) => cb(effect)); };

  // Outputs
  const outputs = {
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    canSubmit: computed(() => name.value.length > 0 && email.value.length > 0 && !isLoading.value),
  };

  // Inputs
  const inputs = {
    async submit() {
      if (!outputs.canSubmit.value) return;
      isLoading.value = true;
      error.value = null;
      try {
        await userService.updateUser({ name: name.value, email: email.value });
        emitEffect({ type: 'SHOW_TOAST', message: 'Updated successfully' });
        emitEffect({ type: 'NAVIGATE_BACK' });
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Unknown error';
      } finally {
        isLoading.value = false;
      }
    },
  };

  return { models: { name, email }, outputs, inputs, onEffect };
}
```

### Component Usage

```vue
<script setup lang="ts">
import { useUserViewModel } from '@/presentation/view-models/useUserViewModel';
import { useNavGraph } from '@/router/nav-graph';
import { useToast } from '@/presentation/composables/useToast';

const vm = useUserViewModel();
const navGraph = useNavGraph();
const toast = useToast();

vm.onEffect((effect) => {
  switch (effect.type) {
    case 'NAVIGATE_BACK': navGraph.back(); break;
    case 'SHOW_TOAST': toast.success(effect.message); break;
  }
});
</script>

<template>
  <form @submit.prevent="vm.inputs.submit()">
    <input v-model="vm.models.name.value" class="form-control" />
    <input v-model="vm.models.email.value" class="form-control" />
    <div v-if="vm.outputs.error.value" class="alert alert-danger">{{ vm.outputs.error.value }}</div>
    <button type="submit" class="btn btn-primary" :disabled="!vm.outputs.canSubmit.value">
      {{ vm.outputs.isLoading.value ? 'Saving...' : 'Save' }}
    </button>
  </form>
</template>
```

---

## Benefits

1. **Testability**: ViewModels are plain functions testable without mounting components
2. **Predictability**: All state changes flow through explicit inputs and models
3. **Type Safety**: Discriminated union effects ensure exhaustive handling
4. **Separation of Concerns**: Logic fully separated from Vue templates
5. **Reusability**: ViewModel composables can be shared across components
6. **Debugging**: Clear data flow makes state changes traceable
