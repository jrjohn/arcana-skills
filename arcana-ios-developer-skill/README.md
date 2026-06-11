# iOS Developer Skill

Professional iOS development skill based on [Arcana iOS](https://github.com/jrjohn/arcana-ios) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any iOS project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
arcana-ios-developer-skill/
├── SKILL.md                    # Main skill file (core rules & patterns)
├── README.md                   # This file
├── verification/
│   └── commands.md             # All verification bash commands
├── patterns/
│   ├── patterns.md             # Design patterns (original)
│   └── mvvm-input-output.md    # MVVM Input/Output/Effect pattern details
├── checklists/
│   └── production-ready.md     # Production & code review checklists
├── reference.md                # Technical reference
└── examples.md                 # Code examples
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| 🔴 CRITICAL | Zero-Null Policy | Repository stubs never return nil/empty |
| 🔴 CRITICAL | Navigation Wiring | All Route cases must have view destinations |
| 🔴 CRITICAL | ID Consistency | Cross-repository IDs must match |
| 🔴 CRITICAL | Onboarding Flow | Register/Login must check Onboarding |
| 🟡 IMPORTANT | UI States | Loading/Error/Empty for all screens |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | Animations | Smooth transitions |
| 🟢 RECOMMENDED | Accessibility | VoiceOver labels |

## Quick Reference Card

### New Screen:
```
1. Add route → Route.swift
2. Add destination → NavigationRouter.swift
3. Create ViewModel (Input/Output/Effect)
4. Implement Loading/Error/Empty states
5. Verify mock data is non-empty
```

### New Repository:
```
1. Protocol → Domain/Repositories/
2. Implementation → Data/Repositories/
3. DI binding → Infrastructure/DI/
4. Mock data (NEVER empty!)
5. Verify ID consistency
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "\\[\\]\\|Array()" *RepositoryImpl.swift` |
| Navigation crash | `grep "case\s" Route.swift` vs destinations |
| Button does nothing | `grep "action:\s*{\s*}" *.swift` |

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

## Key Features

- **Clean Architecture** - Three-layer architecture
- **MVVM Input/Output/Effect** - Unidirectional data flow
- **Offline-First Design** - SwiftData as single source of truth
- **Spec Gap Prediction** - Auto-detect missing UI states/flows
- **Error Handling Pattern** - Unified AppError model
- **Verification Commands** - 22+ diagnostic bash commands

## Tech Stack

| Technology | Version |
|------------|---------|
| Swift | 6.0+ |
| SwiftUI | iOS 17+ |
| SwiftData | iOS 17+ |
| Alamofire | 5.9+ |
| swift-dependencies | 1.0+ |

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

- iOS project development
- Architecture design and review
- Code review
- Offline-first features
- SwiftUI development
- Debugging blank screens / navigation issues
