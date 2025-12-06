# MVVM Input/Output/Effect Pattern with Angular Signals

## Overview

The Input/Output/Effect pattern provides a clear, unidirectional data flow for ViewModels using Angular Signals.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ViewModel                                 │
│  ┌─────────┐    ┌──────────────┐    ┌──────────┐               │
│  │  Input  │ →  │   Process    │ →  │  Output  │               │
│  │ (Event) │    │  (Business)  │    │ (Signal) │               │
│  └─────────┘    └──────────────┘    └──────────┘               │
│        ↑                                  │                     │
│        │                                  ↓                     │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                    Component                         │       │
│  │   User Action → Input    |    Output → Template     │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Template

```typescript
import { Injectable, signal, computed } from '@angular/core';
import { Subject } from 'rxjs';

// === INPUT: Union type defining all events ===
export type FeatureInput =
  | { type: 'LOAD' }
  | { type: 'REFRESH' }
  | { type: 'ITEM_CLICKED'; id: string }
  | { type: 'SEARCH_CHANGED'; query: string }
  | { type: 'RETRY' };

// === OUTPUT: State interface ===
export interface FeatureOutput {
  isLoading: boolean;
  items: Item[];
  error: string | null;
  searchQuery: string;
  selectedItemId: string | null;
}

// === EFFECT: Union type for one-time events ===
export type FeatureEffect =
  | { type: 'NAVIGATE_TO_DETAIL'; id: string }
  | { type: 'SHOW_TOAST'; message: string }
  | { type: 'NAVIGATE_BACK' };

@Injectable()
export class FeatureViewModel {
  // Private signals for state
  private readonly _isLoading = signal(false);
  private readonly _items = signal<Item[]>([]);
  private readonly _error = signal<string | null>(null);
  private readonly _searchQuery = signal('');
  private readonly _selectedItemId = signal<string | null>(null);

  // Public computed output
  readonly output = computed<FeatureOutput>(() => ({
    isLoading: this._isLoading(),
    items: this._items(),
    error: this._error(),
    searchQuery: this._searchQuery(),
    selectedItemId: this._selectedItemId(),
  }));

  // Effect stream for one-time events
  private readonly _effect = new Subject<FeatureEffect>();
  readonly effect$ = this._effect.asObservable();

  constructor(private readonly repository: FeatureRepository) {
    this.onInput({ type: 'LOAD' });
  }

  // === INPUT HANDLER ===
  onInput(input: FeatureInput): void {
    switch (input.type) {
      case 'LOAD':
        this.loadData();
        break;
      case 'REFRESH':
        this.refreshData();
        break;
      case 'ITEM_CLICKED':
        this.handleItemClick(input.id);
        break;
      case 'SEARCH_CHANGED':
        this.handleSearch(input.query);
        break;
      case 'RETRY':
        this.loadData();
        break;
    }
  }

  private async loadData(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const items = await this.repository.getItems();
      this._items.set(items);
    } catch (error) {
      this._error.set(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      this._isLoading.set(false);
    }
  }

  private async refreshData(): Promise<void> {
    try {
      const items = await this.repository.getItems();
      this._items.set(items);
      this._effect.next({ type: 'SHOW_TOAST', message: 'Updated successfully' });
    } catch (error) {
      this._effect.next({
        type: 'SHOW_TOAST',
        message: `Update failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    }
  }

  private handleItemClick(id: string): void {
    this._selectedItemId.set(id);
    this._effect.next({ type: 'NAVIGATE_TO_DETAIL', id });
  }

  private handleSearch(query: string): void {
    this._searchQuery.set(query);
    // Debounce search implementation
  }
}
```

## Component Usage

```typescript
import { Component, ChangeDetectionStrategy, inject, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FeatureViewModel, FeatureInput } from './feature.viewmodel';
import { NavGraphService } from '../../core/services/nav-graph.service';

@Component({
  selector: 'app-feature',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (vm.output().isLoading) {
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    } @else if (vm.output().error) {
      <div class="alert alert-danger">
        {{ vm.output().error }}
        <button (click)="onInput({ type: 'RETRY' })">Retry</button>
      </div>
    } @else if (vm.output().items.length === 0) {
      <div class="empty-state">
        <p>No items found</p>
      </div>
    } @else {
      <ul class="list-group">
        @for (item of vm.output().items; track item.id) {
          <li
            class="list-group-item"
            (click)="onInput({ type: 'ITEM_CLICKED', id: item.id })">
            {{ item.name }}
          </li>
        }
      </ul>
    }
  `,
  providers: [FeatureViewModel],
})
export class FeatureComponent {
  protected readonly vm = inject(FeatureViewModel);
  private readonly navGraph = inject(NavGraphService);
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    // Handle effects
    this.vm.effect$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((effect) => {
        switch (effect.type) {
          case 'NAVIGATE_TO_DETAIL':
            this.navGraph.toItemDetail(effect.id);
            break;
          case 'SHOW_TOAST':
            // Show toast notification
            console.log(effect.message);
            break;
          case 'NAVIGATE_BACK':
            this.navGraph.back();
            break;
        }
      });
  }

  protected onInput(input: FeatureInput): void {
    this.vm.onInput(input);
  }
}
```

## Key Principles

1. **Input is union type** - All user actions are explicit and type-safe
2. **Output is computed signal** - Immutable state representation
3. **Effect is RxJS Subject** - For one-time events (navigation, toasts)
4. **Single onInput entry point** - All inputs go through one function
5. **Signals for state** - Automatic change detection with OnPush
6. **takeUntilDestroyed for cleanup** - Proper subscription management

## Testing

```typescript
import { TestBed } from '@angular/core/testing';
import { FeatureViewModel } from './feature.viewmodel';
import { FeatureRepository } from '../../domain/repositories/feature.repository';

describe('FeatureViewModel', () => {
  let viewModel: FeatureViewModel;
  let mockRepository: jasmine.SpyObj<FeatureRepository>;

  beforeEach(() => {
    mockRepository = jasmine.createSpyObj('FeatureRepository', ['getItems']);

    TestBed.configureTestingModule({
      providers: [
        FeatureViewModel,
        { provide: FeatureRepository, useValue: mockRepository },
      ],
    });

    mockRepository.getItems.and.returnValue(Promise.resolve([]));
    viewModel = TestBed.inject(FeatureViewModel);
  });

  it('should load items on init', async () => {
    // Given
    const items = [{ id: '1', name: 'Test' }];
    mockRepository.getItems.and.returnValue(Promise.resolve(items));

    // When
    viewModel.onInput({ type: 'LOAD' });
    await new Promise(resolve => setTimeout(resolve, 0));

    // Then
    expect(viewModel.output().items).toEqual(items);
    expect(viewModel.output().isLoading).toBeFalse();
  });

  it('should emit navigate effect on item click', (done) => {
    // Given
    viewModel.effect$.subscribe((effect) => {
      // Then
      expect(effect.type).toBe('NAVIGATE_TO_DETAIL');
      if (effect.type === 'NAVIGATE_TO_DETAIL') {
        expect(effect.id).toBe('123');
      }
      done();
    });

    // When
    viewModel.onInput({ type: 'ITEM_CLICKED', id: '123' });
  });
});
```
