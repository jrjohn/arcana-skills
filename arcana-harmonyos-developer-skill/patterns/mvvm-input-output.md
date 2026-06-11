# MVVM Input/Output/Effect Pattern for ArkTS

## Overview

The Input/Output/Effect pattern provides a clear, unidirectional data flow for ViewModels in HarmonyOS ArkTS. Since ArkTS strict mode forbids sealed classes, spread operators, and runtime reflection, this pattern uses discriminated unions via class-based constants and factory methods for immutable state updates.

```
+---------------------------------------------------------------+
|                        ViewModel                                |
|  +----------+    +---------------+    +-----------+            |
|  |  Input   | -> |   Process     | -> |  Output   |            |
|  | (Event)  |    |  (Business)   |    |  (State)  |            |
|  +----------+    +---------------+    +-----------+            |
|        ^                                   |                    |
|        |                                   v                    |
|  +---------------------------------------------------------+   |
|  |                      Page (@Entry)                       |   |
|  |  User Action -> Input    |    Output -> UI State         |   |
|  +---------------------------------------------------------+   |
|                                                                 |
|  +-----------+                                                  |
|  |  Effect   |  One-time events: navigation, toast, dialog     |
|  +-----------+                                                  |
+---------------------------------------------------------------+
```

## Template

### Input (Discriminated Union)

```typescript
export class FeatureInputType {
  static readonly LOAD = 'LOAD'
  static readonly REFRESH = 'REFRESH'
  static readonly ITEM_TAPPED = 'ITEM_TAPPED'
  static readonly SEARCH = 'SEARCH'
  static readonly RETRY = 'RETRY'
}

export class FeatureInput {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static load(): FeatureInput {
    return new FeatureInput(FeatureInputType.LOAD, undefined)
  }

  static refresh(): FeatureInput {
    return new FeatureInput(FeatureInputType.REFRESH, undefined)
  }

  static itemTapped(id: string): FeatureInput {
    return new FeatureInput(FeatureInputType.ITEM_TAPPED, id)
  }

  static search(query: string): FeatureInput {
    return new FeatureInput(FeatureInputType.SEARCH, query)
  }

  static retry(): FeatureInput {
    return new FeatureInput(FeatureInputType.RETRY, undefined)
  }
}
```

### Output (Immutable State with Factory Methods)

```typescript
export class FeatureOutput {
  readonly items: Array<Item>
  readonly isLoading: boolean
  readonly error: string | undefined
  readonly searchQuery: string

  private constructor(items: Array<Item>, isLoading: boolean, error: string | undefined, searchQuery: string) {
    this.items = items
    this.isLoading = isLoading
    this.error = error
    this.searchQuery = searchQuery
  }

  static initial(): FeatureOutput {
    return new FeatureOutput(new Array<Item>(), false, undefined, '')
  }

  get isEmpty(): boolean {
    return this.items.length === 0 && !this.isLoading && this.error === undefined
  }

  // Factory methods replace spread operator
  withLoading(isLoading: boolean): FeatureOutput {
    return new FeatureOutput(this.items, isLoading, isLoading ? undefined : this.error, this.searchQuery)
  }

  withItems(items: Array<Item>): FeatureOutput {
    return new FeatureOutput(items, false, undefined, this.searchQuery)
  }

  withError(error: string): FeatureOutput {
    return new FeatureOutput(this.items, false, error, this.searchQuery)
  }
}
```

### Effect (One-Time Events)

```typescript
export class FeatureEffectType {
  static readonly NAVIGATE = 'NAVIGATE'
  static readonly SHOW_TOAST = 'SHOW_TOAST'
  static readonly NAVIGATE_BACK = 'NAVIGATE_BACK'
}

export class FeatureEffect {
  readonly type: string
  readonly payload: string | undefined

  private constructor(type: string, payload: string | undefined) {
    this.type = type
    this.payload = payload
  }

  static navigate(route: string): FeatureEffect {
    return new FeatureEffect(FeatureEffectType.NAVIGATE, route)
  }

  static showToast(message: string): FeatureEffect {
    return new FeatureEffect(FeatureEffectType.SHOW_TOAST, message)
  }

  static navigateBack(): FeatureEffect {
    return new FeatureEffect(FeatureEffectType.NAVIGATE_BACK, undefined)
  }
}
```

### ViewModel

```typescript
@injectable()
export class FeatureViewModel {
  private repository: FeatureRepository
  private _output: FeatureOutput = FeatureOutput.initial()
  private _effectCallback: ((effect: FeatureEffect) => void) | undefined = undefined

  constructor(repository: FeatureRepository) {
    this.repository = repository
  }

  get output(): FeatureOutput { return this._output }

  setEffectCallback(callback: (effect: FeatureEffect) => void): void {
    this._effectCallback = callback
  }

  onInput(input: FeatureInput): void {
    switch (input.type) {
      case FeatureInputType.LOAD:
        this.loadData()
        break
      case FeatureInputType.REFRESH:
        this.refreshData()
        break
      case FeatureInputType.ITEM_TAPPED:
        this.handleItemTap(input.payload as string)
        break
      case FeatureInputType.SEARCH:
        this.handleSearch(input.payload as string)
        break
      case FeatureInputType.RETRY:
        this.loadData()
        break
      default:
        break
    }
  }

  private emitEffect(effect: FeatureEffect): void {
    if (this._effectCallback !== undefined) {
      this._effectCallback(effect)
    }
  }
}
```

## Page Usage

```typescript
@Entry
@Component
struct FeaturePage {
  @State private output: FeatureOutput = FeatureOutput.initial()
  private viewModel: FeatureViewModel = AppContainer.resolve(ServiceIdentifiers.FEATURE_VIEW_MODEL)

  aboutToAppear(): void {
    this.viewModel.setEffectCallback((effect: FeatureEffect) => {
      this.handleEffect(effect)
    })
    this.viewModel.onInput(FeatureInput.load())
    this.output = this.viewModel.output
  }

  private handleEffect(effect: FeatureEffect): void {
    switch (effect.type) {
      case FeatureEffectType.NAVIGATE:
        NavigationHelper.pushUrl(effect.payload as string, undefined)
        break
      case FeatureEffectType.SHOW_TOAST:
        promptAction.showToast({ message: effect.payload as string })
        break
      case FeatureEffectType.NAVIGATE_BACK:
        NavigationHelper.back()
        break
      default:
        break
    }
  }

  private handleInput(input: FeatureInput): void {
    this.viewModel.onInput(input)
    this.output = this.viewModel.output // Trigger @State re-render
  }

  build() {
    // Render based on output state
    if (this.output.isLoading) {
      LoadingState()
    } else if (this.output.error !== undefined) {
      ErrorState({ message: this.output.error, onRetry: () => { this.handleInput(FeatureInput.retry()) } })
    } else if (this.output.isEmpty) {
      EmptyState({ title: 'No data', description: 'Nothing here yet' })
    } else {
      // Content
    }
  }
}
```

## Key Principles

1. **Input uses discriminated union** - Class with static type constants and private constructor
2. **Output is immutable** - All updates via factory methods (no spread operator)
3. **Effect is for one-time events** - Navigation, toasts, dialogs
4. **Single onInput entry point** - All inputs dispatched through one function
5. **ViewModel has no ArkUI imports** - Pure business logic, testable without UI
6. **@State triggers re-render** - Reassign output reference to trigger UI update
