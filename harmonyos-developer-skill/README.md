# HarmonyOS Developer Skill

Professional HarmonyOS 5 (NEXT) development skill based on [Arcana HarmonyOS](https://github.com/jrjohn/arcana-harmonyos) enterprise architecture.

## Version

**v1.0** - Initial Release
- Full four-layer Clean Architecture support
- ArkTS strict mode compliance patterns
- Offline-First with RelationalStore + WorkScheduler sync
- MVVM Input/Output/Effect with discriminated unions
- InversifyJS-style DI Container
- HUKS AES-256-GCM security integration
- 555+ test patterns with @ohos/hypium

## Structure

```
harmonyos-developer-skill/
+-- SKILL.md                          # Main skill file (core rules & patterns)
+-- README.md                         # This file
+-- examples.md                       # ArkTS/ArkUI code examples
+-- patterns.md                       # HarmonyOS design patterns
+-- reference.md                      # Technical reference (APIs, HUKS, WorkScheduler)
+-- verification/
|   +-- commands.md                   # DevEco Studio / hdc verification commands
+-- patterns/
|   +-- mvvm-input-output.md          # MVVM I/O/E pattern for ArkTS
+-- checklists/
    +-- production-ready.md           # HarmonyOS-specific production checklist
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| CRITICAL | ArkTS Strict Mode | No any/unknown/spread/computed properties |
| CRITICAL | Zero-Null Policy | Repository stubs never return null/empty |
| CRITICAL | Navigation Wiring | All routes must have registered page destinations |
| CRITICAL | Offline Sync Integrity | PENDING status tracked and resolved |
| IMPORTANT | UI States | Loading/Error/Empty for all pages |
| IMPORTANT | Result<T,E> | Railway-oriented error handling |
| RECOMMENDED | i18n | All strings via $r() resource references |
| RECOMMENDED | HUKS Security | Sensitive data encrypted |

## Architecture

```
+---------------------------------------------------------------+
|                     Presentation Layer                          |
|          ArkUI Pages + Components + MVVM ViewModels            |
+---------------------------------------------------------------+
|                       Domain Layer (PURE)                       |
|     Models + Validators + Services + Repository Interfaces     |
+---------------------------------------------------------------+
|                        Data Layer                               |
|   API Service + RelationalStore + Repository Impl + Sync       |
+---------------------------------------------------------------+
|                        Core Layer                               |
|  DI Container + Network + Security + Scheduling + Analytics    |
+---------------------------------------------------------------+
```

## Key Features

- **Clean Architecture** - Four-layer with pure Domain
- **MVVM Input/Output/Effect** - Unidirectional data flow with discriminated unions
- **Offline-First Design** - RelationalStore as single source of truth
- **ArkTS Strict Mode** - Full compliance with workaround patterns
- **InversifyJS-style DI** - Explicit IoC container with decorators
- **HUKS Security** - AES-256-GCM hardware-backed encryption
- **WorkScheduler Sync** - Background periodic synchronization
- **Spec Gap Prediction** - Auto-detect missing UI states/flows

## Tech Stack

| Technology | Version |
|------------|---------|
| HarmonyOS NEXT | 5.0+ |
| ArkTS | Strict Mode |
| ArkUI | Declarative |
| API Level | Target 21 / Min 12 |
| DevEco Studio | 6.0.1.260+ |
| @ohos/hypium | Latest |

## When to Use This Skill

- HarmonyOS NEXT project development
- ArkTS strict mode architecture design
- Offline-first feature implementation
- Code review for HarmonyOS apps
- ArkUI declarative UI development
- HUKS security integration
- Debugging blank screens / navigation / DI issues
