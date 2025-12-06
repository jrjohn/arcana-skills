# Windows Developer Skill

Professional Windows desktop development skill based on [Arcana Windows](https://github.com/jrjohn/arcana-windows) enterprise architecture.

## Version

**v2.0** - Generalized & Enhanced
- Removed domain-specific content (usable for any Windows project)
- Added Quick Reference Card
- Added Error Handling Pattern
- Added Priority Labels (🔴/🟡/🟢)
- Added Test Coverage Targets
- Added Spec Gap Prediction System
- Split into multiple files for better organization

## Structure

```
windows-developer-skill/
├── SKILL.md                    # Main skill file (core rules & patterns)
├── README.md                   # This file
├── patterns.md                 # Design patterns overview
├── reference.md                # Technical reference
├── examples.md                 # Code examples
├── verification/
│   └── commands.md             # All verification bash commands
├── patterns/
│   └── mvvm-udf.md             # MVVM UDF pattern details
└── checklists/
    └── production-ready.md     # Production & code review checklists
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| 🔴 CRITICAL | Zero-Empty Policy | Repository stubs never return empty collections |
| 🔴 CRITICAL | Navigation Wiring | All NavGraph methods must be implemented |
| 🔴 CRITICAL | Effect Handling | All ViewModel Effects must be subscribed |
| 🟡 IMPORTANT | UI States | Loading/Error/Empty for all views |
| 🟡 IMPORTANT | Mock Data Quality | Realistic data ranges |
| 🟢 RECOMMENDED | Animations | Smooth transitions |
| 🟢 RECOMMENDED | Accessibility | Screen reader support |

## Quick Reference Card

### New View:
```
1. Add Page to Presentation layer
2. Create ViewModel with Input/Output/Effect
3. Add navigation method to INavGraph
4. Implement in NavGraph
5. Subscribe to Effects in code-behind
6. Verify mock data is non-empty
```

### New Repository:
```
1. Interface → Domain/Repositories/
2. Implementation → Data/Repositories/
3. DI registration → Infrastructure/
4. Mock data (NEVER return empty!)
5. Verify ID consistency
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Blank screen | `grep "new List<>\\|Empty" *Repository.cs` |
| Navigation crash | Check INavGraph vs NavGraph methods |
| Button does nothing | Check Effect subscriptions |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                   │
│          WinUI 3 + MVVM UDF + Navigation            │
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│           DI + Security + Settings                  │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│          Business Entities + Services               │
├─────────────────────────────────────────────────────┤
│                    Data Layer                        │
│         Repository + Unit of Work + EF Core         │
├─────────────────────────────────────────────────────┤
│                    Sync Layer                        │
│            CRDT Engine + Vector Clocks              │
└─────────────────────────────────────────────────────┘
```

## Key Features

- **Clean Architecture** - Five-layer architecture
- **MVVM UDF** - Unidirectional data flow
- **Plugin System** - 18 plugin types
- **CRDT Sync** - Offline-first with conflict resolution
- **Spec Gap Prediction** - Auto-detect missing UI states
- **Verification Commands** - 11+ diagnostic commands

## Tech Stack

| Technology | Version |
|------------|---------|
| .NET | 10.0+ |
| C# | 14.0+ |
| WinUI 3 | 3.0+ |
| EF Core | 10.0+ |
| CommunityToolkit.Mvvm | Latest |

## Documentation Files

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions & architecture |
| [patterns.md](patterns.md) | Design patterns overview |
| [reference.md](reference.md) | Technical reference |
| [examples.md](examples.md) | Code examples |
| [verification/commands.md](verification/commands.md) | All diagnostic commands |
| [patterns/mvvm-udf.md](patterns/mvvm-udf.md) | MVVM UDF pattern |
| [checklists/production-ready.md](checklists/production-ready.md) | Release checklists |

## When to Use This Skill

- Windows desktop application development
- Architecture design and review
- Code review
- Plugin-based extensible applications
- Debugging UI/navigation issues
