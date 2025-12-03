# Angular Developer Skill

Professional Angular development skill based on [Arcana Angular](https://github.com/jrjohn/arcana-angular) enterprise architecture.

## Overview

This skill provides comprehensive guidance for Angular development following enterprise-grade architectural patterns. It supports Clean Architecture, Offline-First design with 4-layer caching, Angular Signals, and the MVVM Input/Output/Effect pattern.

## Key Features

- **Clean Architecture** - Three-layer architecture (Presentation, Domain, Data)
- **Angular Signals** - Modern reactive state management
- **4-Layer Caching** - Memory, LRU+TTL, IndexedDB, Remote API
- **Offline-First Design** - IndexedDB (Dexie.js) as single source of truth
- **OnPush Change Detection** - Optimized performance with immutable data
- **MVVM Input/Output/Effect** - Unidirectional data flow pattern

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│      Components + MVVM + Input/Output/Effect        │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│   Offline-First Repository + IndexedDB + 4L Cache   │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Technology | Version |
|------------|---------|
| Angular | 17+ |
| TypeScript | 5.0+ |
| RxJS | 7.8+ |
| Dexie.js | 3.2+ |
| Bootstrap | 5.3+ |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- Angular project development from scratch
- Architecture design and review
- Code review for Angular applications
- Implementing offline-first features
- Performance optimization with Signals and OnPush
- Enterprise web application development

## Quick Start

### ViewModel with Signals

```typescript
@Injectable()
export class UserViewModel {
  // Output: Read-only signals
  private readonly _name = signal('');
  private readonly _isLoading = signal(false);

  readonly output = computed(() => ({
    name: this._name(),
    isLoading: this._isLoading(),
  }));

  // Effect: One-time events
  private readonly _effect = new Subject<UserEffect>();
  readonly effect$ = this._effect.asObservable();

  // Input handler
  onInput(input: UserInput): void {
    switch (input.type) {
      case 'UPDATE_NAME':
        this._name.set(input.name);
        break;
      case 'SUBMIT':
        this.submit();
        break;
    }
  }
}
```

### 4-Layer Cache

```typescript
@Injectable({ providedIn: 'root' })
export class CacheService {
  // L1: In-memory cache (fastest)
  private readonly memoryCache = new Map<string, CacheEntry>();

  // L2: LRU cache with TTL
  private readonly lruCache = new LRUCache<string, any>(100);

  // L3: IndexedDB (persistent)
  private readonly db = new Dexie('AppCache');

  // L4: Remote API (slowest, source of truth)

  async get<T>(key: string): Promise<T | null> {
    // Check each layer in order
    return this.checkMemory(key)
        ?? this.checkLRU(key)
        ?? await this.checkIndexedDB(key)
        ?? await this.fetchRemote(key);
  }
}
```

## License

This skill is part of the Arcana enterprise architecture series.
