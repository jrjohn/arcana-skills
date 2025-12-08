# Arcana React - Enterprise React Architecture

Enterprise-grade React application architecture with Clean Architecture, Offline-First design, and MVVM Input/Output/Effect pattern.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   Pages ←──→ Custom Hooks (ViewModel) ←──→ Services       │  │
│  │     │              │                          │            │  │
│  │     └──── State (useState/useMemo) ──────────→│            │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       Domain Layer                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Models │ Services │ Repository Interfaces                 │  │
│  │         │          │                                       │  │
│  │  Pure business logic, no framework dependencies           │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Data Layer                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Repository Impl │ API Client │ IndexedDB (Dexie)         │  │
│  │                  │   (Axios)  │                            │  │
│  │  Implements domain interfaces, handles data persistence   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Clean Architecture
- **Three-Layer Separation**: Presentation, Domain, Data
- **Dependency Inversion**: Domain defines interfaces, Data implements
- **Testability**: Each layer can be tested independently

### 2. MVVM Input/Output/Effect Pattern
- **Input**: Discriminated union for all user actions
- **Output**: Immutable state container
- **Effect**: One-time side effects (navigation, toasts)

### 3. Four-Layer Offline-First Caching
```
L1: Memory Cache     (~0.1ms) - Hot data
L2: LRU Cache        (~2ms)   - Frequently accessed
L3: IndexedDB        (~10ms)  - Persistent storage
L4: Remote API       (~200ms) - Source of truth
```

### 4. Type-Safe Navigation
- NavGraph service with typed methods
- React Router 7 integration
- No hardcoded route strings

## Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | React | 19.1+ |
| Language | TypeScript | 5.8+ |
| Build Tool | Vite | 6.3+ |
| Routing | React Router | 7.0+ |
| HTTP Client | Axios | Latest |
| Reactive | RxJS | 7.8+ |
| Styling | Tailwind CSS | 4.0+ |
| Local Storage | Dexie (IndexedDB) | 4.0+ |
| i18n | react-i18next | Latest |
| Testing | Vitest + RTL | Latest |

## Project Structure

```
src/
├── presentation/           # UI Layer
│   ├── components/         # Reusable UI components
│   ├── layouts/            # Page layouts
│   └── pages/              # Page components
│       ├── auth/           # Login, Register, etc.
│       ├── dashboard/      # Dashboard page
│       └── users/          # User management pages
├── domain/                 # Business Logic Layer
│   ├── models/             # Domain entities and types
│   │   ├── user.ts
│   │   ├── app-error.ts
│   │   └── sync-status.ts
│   ├── services/           # Business services
│   │   ├── auth.service.ts
│   │   └── user.service.ts
│   └── repositories/       # Repository interfaces
│       ├── user.repository.ts
│       └── auth.repository.ts
├── data/                   # Data Layer
│   ├── repositories/       # Repository implementations
│   │   ├── user.repository.impl.ts
│   │   └── mock/           # Mock implementations
│   ├── local/              # IndexedDB setup
│   │   └── database.ts
│   └── remote/             # API client
│       └── api-client.ts
├── core/                   # Core infrastructure
│   ├── providers/          # Context providers
│   │   ├── RepositoryProvider.tsx
│   │   └── AuthProvider.tsx
│   ├── hooks/              # Core hooks
│   │   ├── useNavGraph.ts
│   │   └── useAuth.ts
│   └── services/           # Core services
│       └── cache-manager.ts
├── shared/                 # Shared utilities
│   ├── components/         # Shared UI components
│   ├── hooks/              # Shared hooks
│   └── utils/              # Utility functions
├── router/                 # Routing configuration
│   ├── routes.tsx
│   └── guards/
├── assets/                 # Static assets
├── App.tsx
└── main.tsx
```

## Quick Start

### 1. Clone the Template
```bash
git clone https://github.com/jrjohn/arcana-react.git my-project
cd my-project
rm -rf .git
git init
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```

### 4. Run Tests
```bash
npm test
```

### 5. Build for Production
```bash
npm run build
```

## Development Workflow

### Adding a New Feature

1. **Create Domain Models** (`domain/models/`)
   ```typescript
   export interface Product {
     id: string;
     name: string;
     price: number;
   }
   ```

2. **Define Repository Interface** (`domain/repositories/`)
   ```typescript
   export interface IProductRepository {
     getProducts(): Promise<Product[]>;
     getProductById(id: string): Promise<Product | null>;
     createProduct(data: CreateProductDto): Promise<Product>;
   }
   ```

3. **Implement Repository** (`data/repositories/`)
   ```typescript
   export class ProductRepositoryImpl implements IProductRepository {
     async getProducts(): Promise<Product[]> {
       const response = await apiClient.get('/products');
       return response.data;
     }
   }
   ```

4. **Create ViewModel Hook** (`presentation/pages/products/`)
   ```typescript
   export function useProductListViewModel() {
     // Input/Output/Effect pattern
   }
   ```

5. **Create Page Component** (`presentation/pages/products/`)
   ```typescript
   export const ProductListPage: React.FC = () => {
     const { output, onInput } = useProductListViewModel();
     // Render UI
   };
   ```

6. **Add Route** (`router/routes.tsx`)
   ```typescript
   { path: '/products', element: <ProductListPage /> }
   ```

## Testing Strategy

### Test Coverage Targets

| Layer | Target |
|-------|--------|
| ViewModel Hooks | 90%+ |
| Services | 85%+ |
| Repositories | 80%+ |
| Components | 60%+ |
| **Overall** | **87%** |

### Test Commands

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- src/presentation/pages/auth/useLoginViewModel.test.ts

# Watch mode
npm test -- --watch
```

## Internationalization

The project supports 6 languages with 300+ translation keys:

- English (en)
- Chinese Traditional (zh-TW)
- Japanese (ja)
- Korean (ko)
- Spanish (es)
- French (fr)

```typescript
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();
return <h1>{t('common.welcome')}</h1>;
```

## Performance Optimizations

1. **React.memo** for presentational components
2. **useMemo/useCallback** for expensive computations
3. **Code Splitting** with React.lazy
4. **Virtual Scrolling** with react-window
5. **Four-Layer Caching** for API responses
6. **Optimistic Updates** for better UX

## Security Features

- JWT authentication with refresh tokens
- Axios interceptors for auth headers
- XSS protection with input sanitization
- CSRF tokens for form submissions
- Content Security Policy headers
- No hardcoded secrets (environment variables)

## License

MIT
