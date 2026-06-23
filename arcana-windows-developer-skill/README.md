# Windows Developer Skill

Professional Windows desktop development skill based on [Arcana Windows](https://github.com/jrjohn/arcana-windows) enterprise architecture.

## 🔁 Adding a feature = copy the nearest working feature

When adding a new feature, **don't build it from scratch off the recipe — copy the nearest existing conformant feature in the cloned reference, then rename + adapt it.** Re-deriving the pattern each time invites skipped layers (ViewModel / repository), shortcut wiring (component → data/API directly), and dropped tests — the "vibe-coding" deviations that compile and pass coverage but fail architecture review. Copying a known-good feature carries conformance in *by construction*; the File-by-File Recipe is then your completeness checklist, not a from-scratch build order. (Full rule in `SKILL.md`.)

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
arcana-windows-developer-skill/
├── SKILL.md                    # Main skill file (core rules & patterns)
├── README.md                   # This file
├── verification/
│   └── commands.md             # All verification bash commands
├── patterns/
│   ├── patterns.md             # Design patterns (original)
│   └── mvvm-udf.md             # MVVM UDF pattern details
├── checklists/
│   └── production-ready.md     # Production & code review checklists
├── reference.md                # Technical reference
└── examples.md                 # Code examples
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
| [verification/commands.md](verification/commands.md) | All diagnostic commands |
| [patterns/mvvm-udf.md](patterns/mvvm-udf.md) | MVVM UDF pattern |
| [checklists/production-ready.md](checklists/production-ready.md) | Release checklists |
| [reference.md](reference.md) | Technical reference |
| [examples.md](examples.md) | Code examples |

## When to Use This Skill

- Windows desktop application development
- Architecture design and review
- Code review
- Plugin-based extensible applications
- Debugging UI/navigation issues
