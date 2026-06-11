# Arcana Vue - Enterprise Vue 3 Architecture

Enterprise-grade Vue 3 application architecture with Clean Architecture, Offline-First design, MVVM Input/Output/Effect pattern, InversifyJS DI, and 4-layer progressive caching.

## Architecture Overview

```
+-------------------------------------------------------------------+
|                      Presentation Layer                            |
|  +---------------------------------------------------------------+|
|  |  Vue SFCs <-> ViewModel Composables <-> Domain Services        ||
|  |     |            (Models/Outputs/Inputs/Effects)               ||
|  |     +--- Reactive State (ref/computed) ----------------------> ||
|  +---------------------------------------------------------------+|
+-------------------------------------------------------------------+
|                        Domain Layer                                |
|  +---------------------------------------------------------------+|
|  |  Entities | Services | Validators | Repository Interfaces      ||
|  |           |          |                                         ||
|  |  Pure business logic, no framework dependencies                ||
|  +---------------------------------------------------------------+|
+-------------------------------------------------------------------+
|                         Data Layer                                 |
|  +---------------------------------------------------------------+|
|  |  Repository Impl | API Client | IndexedDB (Dexie) | Cache     ||
|  |                  |   (Axios)  | Mappers | DTOs                 ||
|  |  Implements domain interfaces, handles data persistence        ||
|  +---------------------------------------------------------------+|
+-------------------------------------------------------------------+
```

## Key Features

- **Clean Architecture**: Three-layer separation (Presentation, Domain, Data)
- **MVVM + I/O/E Pattern**: Models, Outputs, Inputs, Effects in composables
- **4-Layer Progressive Caching**: Memory <1ms, LRU 2-5ms, IndexedDB 10-50ms, API 100-500ms+
- **Type-Safe Navigation**: NavGraph with compile-time route safety
- **InversifyJS DI**: Interface-based dependency injection
- **Offline-First**: Sync queue with conflict resolution
- **Security**: XSS, SQL injection, path traversal prevention
- **i18n**: 6 languages (en, zh, zh-TW, es, fr, de)
- **792 Tests**: 97.44% statement coverage, Architecture Rating 10/10

## Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | Vue | 3.5+ |
| Language | TypeScript | 5.7+ |
| Build Tool | Vite | 6.3+ |
| State | Pinia | 3.0 |
| Routing | Vue Router | 4.5 |
| HTTP Client | Axios | 1.7 |
| DI | InversifyJS | 7.10 |
| Local Storage | Dexie (IndexedDB) | 4.2 |
| Styling | Bootstrap | 5.3 |
| i18n | vue-i18n | Latest |
| Testing | Vitest + Vue Test Utils | 3.1 |

## Quick Start

```bash
git clone https://github.com/jrjohn/arcana-vue.git my-project
cd my-project
rm -rf .git && git init
npm install
npm run dev
```

## Testing

```bash
npx vitest run --coverage    # Full coverage report
npx vitest                   # Watch mode
```
