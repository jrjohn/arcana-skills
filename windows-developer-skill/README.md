# Windows Developer Skill

Professional Windows desktop development skill based on [Arcana Windows](https://github.com/jrjohn/arcana-windows) enterprise architecture.

## Overview

This skill provides comprehensive guidance for Windows desktop development following enterprise-grade architectural patterns. It supports Clean Architecture with 5 layers, WinUI 3, MVVM UDF pattern, Plugin System with 18 plugin types, and CRDT-based offline sync.

## Key Features

- **Clean Architecture** - Five-layer architecture (Presentation, Infrastructure, Domain, Data, Sync)
- **WinUI 3** - Modern Windows UI framework
- **MVVM UDF Pattern** - Unidirectional data flow with CommunityToolkit.Mvvm
- **Plugin System** - 18 plugin types with assembly isolation
- **CRDT Sync** - Conflict-free replicated data types for offline sync
- **Enterprise Security** - PBKDF2-SHA256, RBAC, audit logging

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

## Architecture Ratings

| Category | Score |
|----------|-------|
| Clean Architecture | 9.0/10 |
| Plugin System | 9.5/10 |
| MVVM Pattern | 9.5/10 |
| Security | 9.0/10 |
| **Overall** | **9.0/10** |

## Tech Stack

| Technology | Version |
|------------|---------|
| .NET | 10.0+ |
| C# | 14.0+ |
| WinUI 3 | 3.0+ |
| EF Core | 10.0+ |
| SQLite | Latest |
| CommunityToolkit.Mvvm | Latest |
| xUnit | Latest |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- Windows desktop application development
- WinUI 3 application architecture
- Plugin-based extensible applications
- Offline-first desktop applications with sync
- Enterprise Windows development
- Code review for Windows applications

## Quick Start

### MVVM UDF ViewModel

```csharp
public partial class UserViewModel : ObservableObject
{
    // Input: User actions as commands
    public sealed class Input
    {
        public record UpdateName(string Name);
        public record Submit;
    }

    // Output: Observable state
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private bool _isLoading;
    }

    // Effect: Side effects
    public sealed class Effect
    {
        public record NavigateBack;
        public record ShowError(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.UpdateName update:
                Out.Name = update.Name;
                break;
            case Input.Submit:
                _ = SubmitAsync();
                break;
        }
    }
}
```

### Plugin Development

```csharp
[PluginManifest(
    Key = "analytics-module",
    Name = "Analytics Module",
    Type = PluginType.Analytics)]
public class AnalyticsPlugin : IArcanaPlugin
{
    public async Task OnActivateAsync(IPluginContext context)
    {
        // Register views
        context.Navigation.RegisterView("dashboard", typeof(DashboardView));

        // Subscribe to events
        context.MessageBus.Subscribe<TrackEventCommand>(OnTrackEvent);
    }

    public async Task OnDeactivateAsync()
    {
        // Cleanup resources
    }
}
```

### CRDT Sync

```csharp
var syncManager = new CrdtSyncManager(unitOfWork, nodeId, ConflictStrategy.FieldLevelMerge);

// Apply remote change with automatic conflict resolution
var resolved = await syncManager.ApplyChangeAsync(localEntity, remoteEntity);
```

## 18 Plugin Types

| Type | Description |
|------|-------------|
| Menu | Menu extensions |
| View | Custom views |
| Module | Full feature modules |
| Theme | UI themes |
| Authentication | Auth providers |
| Data | Data sources |
| Command | Custom commands |
| Service | Background services |
| Validator | Validation rules |
| Storage | Storage providers |
| Export | Export formats |
| Import | Import formats |
| Report | Report generators |
| Notification | Notification channels |
| Logging | Logging providers |
| Cache | Cache providers |
| Search | Search providers |
| Analytics | Analytics providers |

## License

This skill is part of the Arcana enterprise architecture series.
