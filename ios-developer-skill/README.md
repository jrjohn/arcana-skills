# iOS Developer Skill

Professional iOS development skill based on [Arcana iOS](https://github.com/jrjohn/arcana-ios) enterprise architecture.

## Overview

This skill provides comprehensive guidance for iOS development following enterprise-grade architectural patterns. It supports Clean Architecture, Offline-First design, SwiftUI, SwiftData, and the MVVM Input/Output/Effect pattern.

## Key Features

- **Clean Architecture** - Three-layer architecture (Presentation, Domain, Data)
- **MVVM Input/Output/Effect** - Unidirectional data flow pattern with SwiftUI
- **Offline-First Design** - Local database as single source of truth
- **SwiftData Integration** - Modern persistence with Apple's SwiftData framework
- **@Observable Macro** - Reactive state management with Swift 5.9+
- **Type-Safe Navigation** - Strongly-typed navigation with NavGraph pattern

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         SwiftUI + MVVM + Input/Output/Effect        │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + SwiftData + API     │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Technology | Version |
|------------|---------|
| Swift | 5.9+ |
| SwiftUI | 5.0+ |
| SwiftData | 1.0+ |
| iOS | 17.0+ |
| Xcode | 15.0+ |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- iOS project development from scratch
- Architecture design and review
- Code review for iOS applications
- Debugging iOS-specific issues
- Implementing offline-first features
- Setting up SwiftUI with proper MVVM patterns

## Quick Start

### ViewModel Pattern

```swift
@Observable
final class UserViewModel {
    enum Input {
        case updateName(String)
        case submit
    }

    struct Output {
        var name: String = ""
        var isLoading: Bool = false
    }

    enum Effect {
        case navigateBack
        case showError(String)
    }

    private(set) var output = Output()
    var effect: Effect?

    func onInput(_ input: Input) {
        switch input {
        case .updateName(let name):
            output.name = name
        case .submit:
            Task { await submit() }
        }
    }
}
```

### Offline-First Repository

```swift
final class UserRepository: UserRepositoryProtocol {
    func getUsers() async throws -> [User] {
        // 1. Return cached data immediately
        let cached = try await localDataSource.getUsers()

        // 2. Fetch fresh data in background
        Task {
            let remote = try await remoteDataSource.getUsers()
            try await localDataSource.saveUsers(remote)
        }

        return cached
    }
}
```

## License

This skill is part of the Arcana enterprise architecture series.
