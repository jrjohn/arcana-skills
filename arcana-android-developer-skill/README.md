# Android Developer Skill

Professional Android development skill based on [Arcana Android](https://github.com/jrjohn/arcana-android) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any Android project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
arcana-android-developer-skill/
├── SKILL.md                    # Main skill file (core rules & patterns)
├── README.md                   # This file
├── verification/
│   └── commands.md             # All verification bash commands
├── patterns/
│   ├── patterns.md             # Design patterns (original)
│   └── mvvm-input-output.md    # MVVM Input/Output pattern details
├── checklists/
│   └── production-ready.md     # Production & code review checklists
├── reference.md                # Technical reference
└── examples.md                 # Code examples
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| 🔴 CRITICAL | Zero-Null Policy | Repository stubs never return null/empty |
| 🔴 CRITICAL | Navigation Wiring | All NavRoutes must have composable |
| 🔴 CRITICAL | ID Consistency | Cross-repository IDs must match |
| 🔴 CRITICAL | Onboarding Flow | Register/Login must check Onboarding |
| 🟡 IMPORTANT | UI States | Loading/Error/Empty for all screens |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | Animations | Smooth transitions |
| 🟢 RECOMMENDED | Accessibility | Content descriptions |

## Quick Reference Card

### New Screen:
```
1. Add route → NavRoutes.kt
2. Add composable → NavGraph.kt
3. Create ViewModel (Input/Output)
4. Implement Loading/Error/Empty states
5. Verify mock data is non-empty
```

### New Repository:
```
1. Interface → domain/repository/
2. Implementation → data/repository/
3. Hilt binding → di/
4. Mock data (NEVER empty!)
5. Verify ID consistency
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "emptyList()" *RepositoryImpl.kt` |
| Navigation crash | `grep "NavRoutes\." NavGraph.kt` |
| Click does nothing | `grep "onClick = { }" *.kt` |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         Compose UI + MVVM + Input/Output            │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + Room + API          │
└─────────────────────────────────────────────────────┘
```

## Key Features

- **Clean Architecture** - Three-layer architecture
- **MVVM Input/Output** - Unidirectional data flow
- **Offline-First Design** - Room as single source of truth
- **Spec Gap Prediction** - Auto-detect missing UI states/flows
- **Error Handling Pattern** - Unified error model
- **Verification Commands** - 20+ diagnostic bash commands

## Tech Stack

| Technology | Version |
|------------|---------|
| Kotlin | 2.0+ |
| Jetpack Compose | 1.6+ |
| Room | 2.6+ |
| Hilt | 2.50+ |
| Ktor | 2.3+ |
| Coroutines | 1.8+ |

## Documentation Files

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions & architecture |
| [verification/commands.md](verification/commands.md) | All diagnostic commands |
| [patterns/mvvm-input-output.md](patterns/mvvm-input-output.md) | ViewModel pattern details |
| [checklists/production-ready.md](checklists/production-ready.md) | Release & review checklists |
| [reference.md](reference.md) | Technical API reference |
| [examples.md](examples.md) | Practical code examples |

## When to Use This Skill

- Android project development
- Architecture design and review
- Code review
- Offline-first features
- Jetpack Compose UI development
- Debugging blank screens / navigation issues
