# Angular Developer Skill

Professional Angular development skill based on [Arcana Angular](https://github.com/jrjohn/arcana-angular) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any Angular project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
angular-developer-skill/
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
| 🔴 CRITICAL | Zero-Empty Policy | Repository stubs never return empty arrays |
| 🔴 CRITICAL | Navigation Wiring | All routes must have component imports |
| 🔴 CRITICAL | ID Consistency | Cross-repository IDs must match |
| 🔴 CRITICAL | Onboarding Flow | Register/Login must check Onboarding |
| 🟡 IMPORTANT | UI States | Loading/Error/Empty for all screens |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | Animations | Smooth transitions |
| 🟢 RECOMMENDED | Accessibility | ARIA labels |

## Quick Reference Card

### New Screen:
```
1. Add route → app.routes.ts
2. Create Component with ChangeDetectionStrategy.OnPush
3. Create ViewModel (Input/Output/Effect with Signals)
4. Implement Loading/Error/Empty states
5. Verify mock data is non-empty
```

### New Repository:
```
1. Interface → domain/repositories/
2. Implementation → data/repositories/
3. Provider binding → core/providers/
4. Mock data (NEVER return []!)
5. Verify ID consistency
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "\\[\\]" *repository.impl.ts` |
| Navigation crash | `grep "path:" app.routes.ts` vs component imports |
| Button does nothing | `grep "(click)=\"\"" *.html` |

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

## Key Features

- **Clean Architecture** - Three-layer architecture
- **MVVM Input/Output/Effect** - Unidirectional data flow with Signals
- **4-Layer Caching** - Memory → LRU → IndexedDB → Remote
- **Offline-First Design** - IndexedDB as single source of truth
- **Spec Gap Prediction** - Auto-detect missing UI states/flows
- **Error Handling Pattern** - Unified AppError model
- **Verification Commands** - 23+ diagnostic bash commands

## Tech Stack

| Technology | Version |
|------------|---------|
| Angular | 20.3+ |
| TypeScript | 5.7+ |
| RxJS | 7.8+ |
| Bootstrap | 5.0+ |
| ng-bootstrap | 19.0+ |
| Dexie | 4.0+ |

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

- Angular project development
- Architecture design and review
- Code review
- Offline-first features
- Enterprise web application development
- Debugging blank screens / navigation issues
