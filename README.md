# Arcana Skills for Claude Code

A collection of enterprise development skills for [Claude Code](https://claude.com/claude-code) based on the Arcana architecture framework.

## Overview

These skills provide Claude Code with comprehensive guidance for enterprise-grade development across 8 major platforms. Each skill encapsulates best practices, architectural patterns, and code templates based on the Arcana enterprise architecture.

## Available Skills

| Skill | Platform | Key Features |
|-------|----------|--------------|
| [ios-developer-skill](./ios-developer-skill/) | iOS | SwiftUI, SwiftData, MVVM Input/Output/Effect, Offline-First |
| [android-developer-skill](./android-developer-skill/) | Android | Jetpack Compose, Room, Hilt DI, MVVM Input/Output |
| [angular-developer-skill](./angular-developer-skill/) | Angular | Signals, IndexedDB, 4-Layer Caching, OnPush |
| [react-developer-skill](./react-developer-skill/) | React | React 19 Hooks, 4-Layer Caching, MVVM Input/Output/Effect, Offline-First |
| [springboot-developer-skill](./springboot-developer-skill/) | Spring Boot | gRPC/REST, OSGi Plugins, SSR, Circuit Breaker |
| [python-developer-skill](./python-developer-skill/) | Python/Flask | gRPC (2.78x faster), SQLAlchemy, JWT Auth |
| [nodejs-developer-skill](./nodejs-developer-skill/) | Node.js/Express | InversifyJS DI, gRPC (1.80x faster), Prisma ORM, Dual-Protocol |
| [windows-developer-skill](./windows-developer-skill/) | Windows | WinUI 3, 18 Plugin Types, CRDT Sync, EF Core |

## Architecture Principles

All skills follow consistent enterprise architecture principles:

### Clean Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                 │
│              UI + MVVM + Navigation                 │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                     │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                      │
│         Offline-First Repository + Storage          │
└─────────────────────────────────────────────────────┘
```

### Common Patterns

- **MVVM Input/Output/Effect**: Unidirectional data flow with sealed types
- **Offline-First**: Local database as single source of truth
- **Multi-Layer Caching**: Memory → LRU → Persistent storage
- **Repository Pattern**: Abstracted data access
- **Dependency Injection**: Loose coupling between layers

## Installation

### Method 1: Copy to Claude Code Skills Directory

Copy individual skill folders to your Claude Code user skills directory:

```bash
# macOS/Linux
cp -r ios-developer-skill ~/.claude/skills/

# Windows
copy android-developer-skill %USERPROFILE%\.claude\skills\
```

### Method 2: Project-Level Skills

Copy skill folders to your project's `.claude/skills/` directory for project-specific access.

## Usage

Once installed, skills are automatically available in Claude Code. Use them by referencing the skill name:

```
/skill ios-developer-skill
```

Or Claude will automatically apply the relevant skill when working on platform-specific code.

### Example Prompts

**iOS Development:**
```
Create a UserViewModel following the Input/Output/Effect pattern with offline-first data sync
```

**Android Development:**
```
Implement a repository with Room database and background sync using WorkManager
```

**Angular Development:**
```
Build a component with OnPush change detection and Signal-based state management
```

**React Development:**
```
Create a component with useViewModel hook following Input/Output/Effect pattern and offline-first caching
```

**Spring Boot Development:**
```
Create a gRPC service with REST fallback and circuit breaker resilience
```

**Python/Flask Development:**
```
Implement a user service with JWT authentication and SQLAlchemy repository
```

**Node.js/Express Development:**
```
Create a gRPC service with Express REST fallback using InversifyJS dependency injection
```

**Windows Development:**
```
Create a plugin module with MVVM UDF pattern and type-safe navigation
```

## Skill Structure

Each skill contains:

```
*-developer-skill/
├── SKILL.md                      # Main skill definition with patterns and examples
├── README.md                     # Skill-specific documentation
├── reference.md                  # API reference and tech stack details
├── examples.md                   # Code examples and templates
├── patterns.md                   # Design patterns and best practices
├── checklists/
│   └── production-ready.md       # Production readiness checklist
├── patterns/
│   └── [pattern].md              # Platform-specific pattern guides
│       • mvvm-input-output.md    # iOS, Android, Angular
│       • service-layer.md        # Spring Boot, Python
│       • mvvm-udf.md             # Windows
└── verification/
    └── commands.md               # Verification commands and tests
```

## Tech Stack Summary

| Platform | Language | UI Framework | Database | DI |
|----------|----------|--------------|----------|-----|
| iOS | Swift 6+ | SwiftUI | SwiftData | swift-dependencies |
| Android | Kotlin 1.9+ | Compose | Room | Hilt |
| Angular | TypeScript 5.7+ | Angular 20+ | IndexedDB (Dexie) | Angular DI |
| React | TypeScript 5.7+ | React 19+ | IndexedDB (Dexie) | React Context |
| Spring Boot | Java 25+ | - | MySQL | Spring |
| Python | Python 3.14+ Flask| - | SQLAlchemy/MySQL | Manual |
| Node.js | TypeScript 5.7+ | Express | Prisma/MySQL | InversifyJS |
| Windows | C# 14+ | WinUI 3 | EF Core/SQLite | Microsoft.Extensions.DI |

## Related Projects

- [Arcana iOS](https://github.com/jrjohn/arcana-ios)
- [Arcana Android](https://github.com/jrjohn/arcana-android)
- [Arcana Angular](https://github.com/jrjohn/arcana-angular)
- [Arcana React](https://github.com/jrjohn/arcana-react)
- [Arcana Cloud SpringBoot](https://github.com/jrjohn/arcana-cloud-springboot)
- [Arcana Cloud Python](https://github.com/jrjohn/arcana-cloud-python)
- [Arcana Cloud Node.js](https://github.com/jrjohn/arcana-cloud-nodejs)
- [Arcana Windows](https://github.com/jrjohn/arcana-windows)

## License

MIT
