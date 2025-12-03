---
name: windows-developer-skill
description: Windows desktop development guide based on Arcana Windows enterprise architecture. Provides comprehensive support for Clean Architecture, WinUI 3, MVVM UDF pattern, Plugin System with 18 plugin types, CRDT-based offline sync, and enterprise security. Suitable for Windows desktop project development, architecture design, code review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Windows Developer Skill

Professional Windows desktop development skill based on [Arcana Windows](https://github.com/jrjohn/arcana-windows) enterprise architecture.

## Core Architecture Principles

### Clean Architecture - Five Layers

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

### Architecture Ratings
| Category | Score |
|----------|-------|
| Clean Architecture | 9.0/10 |
| Plugin System | 9.5/10 |
| MVVM Pattern | 9.5/10 |
| Security | 9.0/10 |
| **Overall** | **9.0/10** |

## Instructions

When handling Windows desktop development tasks, follow these principles:

### 1. Project Structure
```
arcana-windows/
├── src/
│   ├── Arcana.App/              # WinUI 3 presentation layer
│   │   ├── Views/               # XAML views
│   │   ├── ViewModels/          # MVVM UDF ViewModels
│   │   └── Navigation/          # NavGraph
│   ├── Arcana.Domain/           # Business entities & services
│   │   ├── Entities/
│   │   └── Services/
│   ├── Arcana.Data/             # Repository + Unit of Work
│   │   ├── Repositories/
│   │   └── DbContext/
│   ├── Arcana.Infrastructure/   # DI, Security, Settings
│   │   ├── Security/
│   │   └── Settings/
│   ├── Arcana.Plugins/          # Plugin runtime
│   │   └── Runtime/
│   └── Arcana.Plugins.Contracts/ # Plugin interfaces
│       └── Interfaces/
├── plugins/                     # Built-in plugins
│   └── FlowChartModule/
└── tests/                       # 507 unit tests
```

### 2. MVVM UDF Pattern (Unidirectional Data Flow)

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Reactive.Subjects;

public partial class UserViewModel : ObservableObject
{
    // MARK: - Input (vm.In): User actions dispatched as commands
    public sealed class Input
    {
        public record UpdateName(string Name);
        public record UpdateEmail(string Email);
        public record Submit;
    }

    // MARK: - Output (vm.Out): Read-only observable state
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private string _email = string.Empty;

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private string? _error;
    }

    // MARK: - Effect (vm.Fx): Side-effect subscriptions
    public sealed class Effect
    {
        public record NavigateBack;
        public record ShowSnackbar(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IUserService _userService;

    public UserViewModel(IUserService userService)
    {
        _userService = userService;
    }

    // Input handler - single entry point
    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.UpdateName updateName:
                Out.Name = updateName.Name;
                break;

            case Input.UpdateEmail updateEmail:
                Out.Email = updateEmail.Email;
                break;

            case Input.Submit:
                _ = SubmitAsync();
                break;
        }
    }

    private async Task SubmitAsync()
    {
        Out.IsLoading = true;
        Out.Error = null;

        try
        {
            await _userService.UpdateUserAsync(Out.Name, Out.Email);
            Fx.OnNext(new Effect.NavigateBack());
        }
        catch (Exception ex)
        {
            Out.Error = ex.Message;
        }
        finally
        {
            Out.IsLoading = false;
        }
    }
}
```

### 3. Type-Safe Navigation (NavGraph)

```csharp
public interface INavGraph
{
    void ToHome();
    void ToUserList();
    void ToUserDetail(string userId);
    void ToUserEdit(string userId);
    void ToOrderList();
    void ToOrderDetail(string orderId);
    void Back();
}

public class NavGraph : INavGraph
{
    private readonly Frame _frame;
    private readonly IServiceProvider _serviceProvider;

    public NavGraph(Frame frame, IServiceProvider serviceProvider)
    {
        _frame = frame;
        _serviceProvider = serviceProvider;
    }

    public void ToHome()
    {
        _frame.Navigate(typeof(HomePage));
    }

    public void ToUserList()
    {
        _frame.Navigate(typeof(UserListPage));
    }

    public void ToUserDetail(string userId)
    {
        _frame.Navigate(typeof(UserDetailPage), userId);
    }

    public void ToUserEdit(string userId)
    {
        _frame.Navigate(typeof(UserEditPage), userId);
    }

    public void ToOrderList()
    {
        _frame.Navigate(typeof(OrderListPage));
    }

    public void ToOrderDetail(string orderId)
    {
        _frame.Navigate(typeof(OrderDetailPage), orderId);
    }

    public void Back()
    {
        if (_frame.CanGoBack)
        {
            _frame.GoBack();
        }
    }
}

// Plugin-level navigation
public interface IPluginNavGraph
{
    void ToPluginView(string viewKey);
    void ToPluginView(string viewKey, object parameter);
}

public class FlowChartNavGraph : IPluginNavGraph
{
    public void ToNewEditor() => ToPluginView("flowchart-editor");
    public void ToEditor(string chartId) => ToPluginView("flowchart-editor", chartId);

    public void ToPluginView(string viewKey)
    {
        // Plugin navigation implementation
    }

    public void ToPluginView(string viewKey, object parameter)
    {
        // Plugin navigation with parameter
    }
}
```

### 4. Plugin System (18 Plugin Types)

```csharp
// Plugin interface
public interface IArcanaPlugin
{
    string Key { get; }
    string Name { get; }
    string Version { get; }
    PluginManifest Manifest { get; }
    Task OnActivateAsync(IPluginContext context);
    Task OnDeactivateAsync();
}

// Plugin manifest
public record PluginManifest
{
    public string Key { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string Version { get; init; } = "1.0.0";
    public string Description { get; init; } = string.Empty;
    public string Author { get; init; } = string.Empty;
    public string[] Dependencies { get; init; } = Array.Empty<string>();
    public PluginType Type { get; init; } = PluginType.Module;
    public string[] ActivationEvents { get; init; } = Array.Empty<string>();
}

// 18 Plugin types
public enum PluginType
{
    Menu,           // Menu extensions
    View,           // Custom views
    Module,         // Full feature modules
    Theme,          // UI themes
    Authentication, // Auth providers
    Data,           // Data sources
    Command,        // Custom commands
    Service,        // Background services
    Validator,      // Validation rules
    Storage,        // Storage providers
    Export,         // Export formats
    Import,         // Import formats
    Report,         // Report generators
    Notification,   // Notification channels
    Logging,        // Logging providers
    Cache,          // Cache providers
    Search,         // Search providers
    Analytics       // Analytics providers
}

// Plugin context with 12 shared services
public interface IPluginContext
{
    IMessageBus MessageBus { get; }
    IEventAggregator EventAggregator { get; }
    IStateStore StateStore { get; }
    IPluginNavGraph Navigation { get; }
    IDialogService DialogService { get; }
    INotificationService NotificationService { get; }
    ISettingsService SettingsService { get; }
    ILoggerFactory LoggerFactory { get; }
    IServiceProvider ServiceProvider { get; }
    IPluginStorage Storage { get; }
    ILocalizationService Localization { get; }
    IThemeService ThemeService { get; }
}

// Plugin implementation
[PluginManifest(
    Key = "flowchart-module",
    Name = "Flow Chart Module",
    Version = "1.0.0",
    Type = PluginType.Module
)]
public class FlowChartPlugin : IArcanaPlugin
{
    public string Key => "flowchart-module";
    public string Name => "Flow Chart Module";
    public string Version => "1.0.0";
    public PluginManifest Manifest { get; } = new()
    {
        Key = "flowchart-module",
        Name = "Flow Chart Module",
        Type = PluginType.Module,
        ActivationEvents = new[] { "onCommand:flowchart.new" }
    };

    private IPluginContext? _context;

    public async Task OnActivateAsync(IPluginContext context)
    {
        _context = context;

        // Register views
        context.Navigation.RegisterView("flowchart-editor", typeof(FlowChartEditorView));
        context.Navigation.RegisterView("flowchart-list", typeof(FlowChartListView));

        // Register commands
        context.MessageBus.Subscribe<NewFlowChartCommand>(OnNewFlowChart);

        // Register menu items
        context.EventAggregator.Publish(new RegisterMenuItemEvent
        {
            MenuId = "tools",
            Item = new MenuItem("Flow Chart", "flowchart.new")
        });

        await Task.CompletedTask;
    }

    public async Task OnDeactivateAsync()
    {
        // Cleanup
        await Task.CompletedTask;
    }

    private void OnNewFlowChart(NewFlowChartCommand command)
    {
        _context?.Navigation.ToPluginView("flowchart-editor");
    }
}

// Plugin runtime with assembly isolation
public class PluginRuntime
{
    private readonly Dictionary<string, AssemblyLoadContext> _loadContexts = new();
    private readonly Dictionary<string, IArcanaPlugin> _plugins = new();

    public async Task LoadPluginAsync(string pluginPath)
    {
        // Create isolated AssemblyLoadContext
        var loadContext = new PluginLoadContext(pluginPath);
        var assembly = loadContext.LoadFromAssemblyPath(pluginPath);

        // Find plugin type
        var pluginType = assembly.GetTypes()
            .FirstOrDefault(t => typeof(IArcanaPlugin).IsAssignableFrom(t));

        if (pluginType == null)
            throw new InvalidOperationException("No plugin found in assembly");

        var plugin = (IArcanaPlugin)Activator.CreateInstance(pluginType)!;

        _loadContexts[plugin.Key] = loadContext;
        _plugins[plugin.Key] = plugin;
    }

    public async Task UnloadPluginAsync(string key)
    {
        if (_plugins.TryGetValue(key, out var plugin))
        {
            await plugin.OnDeactivateAsync();
            _plugins.Remove(key);
        }

        if (_loadContexts.TryGetValue(key, out var context))
        {
            context.Unload();
            _loadContexts.Remove(key);
        }
    }
}
```

### 5. Repository + Unit of Work Pattern

```csharp
// Generic repository interface
public interface IRepository<T> where T : class, IEntity
{
    Task<T?> GetByIdAsync(string id);
    Task<IEnumerable<T>> GetAllAsync();
    Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate);
    Task AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(T entity);
    Task SoftDeleteAsync(T entity);
}

// Unit of Work interface
public interface IUnitOfWork : IDisposable
{
    IRepository<User> Users { get; }
    IRepository<Order> Orders { get; }
    IRepository<Product> Products { get; }
    IRepository<Customer> Customers { get; }
    Task<int> SaveChangesAsync();
    Task BeginTransactionAsync();
    Task CommitAsync();
    Task RollbackAsync();
}

// Repository implementation
public class Repository<T> : IRepository<T> where T : class, IEntity
{
    protected readonly AppDbContext _context;
    protected readonly DbSet<T> _dbSet;

    public Repository(AppDbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    public async Task<T?> GetByIdAsync(string id)
    {
        return await _dbSet.FindAsync(id);
    }

    public async Task<IEnumerable<T>> GetAllAsync()
    {
        return await _dbSet.ToListAsync();
    }

    public async Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate)
    {
        return await _dbSet.Where(predicate).ToListAsync();
    }

    public async Task AddAsync(T entity)
    {
        entity.CreatedAt = DateTime.UtcNow;
        entity.UpdatedAt = DateTime.UtcNow;
        await _dbSet.AddAsync(entity);
    }

    public async Task UpdateAsync(T entity)
    {
        entity.UpdatedAt = DateTime.UtcNow;
        _dbSet.Update(entity);
        await Task.CompletedTask;
    }

    public async Task DeleteAsync(T entity)
    {
        _dbSet.Remove(entity);
        await Task.CompletedTask;
    }

    public async Task SoftDeleteAsync(T entity)
    {
        entity.IsDeleted = true;
        entity.DeletedAt = DateTime.UtcNow;
        await UpdateAsync(entity);
    }
}

// Unit of Work implementation
public class UnitOfWork : IUnitOfWork
{
    private readonly AppDbContext _context;
    private IDbContextTransaction? _transaction;

    public IRepository<User> Users { get; }
    public IRepository<Order> Orders { get; }
    public IRepository<Product> Products { get; }
    public IRepository<Customer> Customers { get; }

    public UnitOfWork(AppDbContext context)
    {
        _context = context;
        Users = new Repository<User>(context);
        Orders = new Repository<Order>(context);
        Products = new Repository<Product>(context);
        Customers = new Repository<Customer>(context);
    }

    public async Task<int> SaveChangesAsync()
    {
        return await _context.SaveChangesAsync();
    }

    public async Task BeginTransactionAsync()
    {
        _transaction = await _context.Database.BeginTransactionAsync();
    }

    public async Task CommitAsync()
    {
        if (_transaction != null)
        {
            await _transaction.CommitAsync();
            await _transaction.DisposeAsync();
            _transaction = null;
        }
    }

    public async Task RollbackAsync()
    {
        if (_transaction != null)
        {
            await _transaction.RollbackAsync();
            await _transaction.DisposeAsync();
            _transaction = null;
        }
    }

    public void Dispose()
    {
        _transaction?.Dispose();
        _context.Dispose();
    }
}
```

### 6. CRDT Sync Engine

```csharp
// Vector clock for causal ordering
public class VectorClock
{
    private readonly Dictionary<string, long> _clock = new();

    public void Increment(string nodeId)
    {
        _clock[nodeId] = _clock.GetValueOrDefault(nodeId, 0) + 1;
    }

    public void Merge(VectorClock other)
    {
        foreach (var (nodeId, timestamp) in other._clock)
        {
            _clock[nodeId] = Math.Max(
                _clock.GetValueOrDefault(nodeId, 0),
                timestamp
            );
        }
    }

    public CausalOrdering Compare(VectorClock other)
    {
        bool thisGreater = false;
        bool otherGreater = false;

        var allKeys = _clock.Keys.Union(other._clock.Keys);

        foreach (var key in allKeys)
        {
            var thisValue = _clock.GetValueOrDefault(key, 0);
            var otherValue = other._clock.GetValueOrDefault(key, 0);

            if (thisValue > otherValue) thisGreater = true;
            if (otherValue > thisValue) otherGreater = true;
        }

        if (thisGreater && otherGreater) return CausalOrdering.Concurrent;
        if (thisGreater) return CausalOrdering.After;
        if (otherGreater) return CausalOrdering.Before;
        return CausalOrdering.Equal;
    }
}

public enum CausalOrdering
{
    Before,
    After,
    Equal,
    Concurrent
}

// Conflict resolution strategies
public enum ConflictStrategy
{
    LastWriteWins,      // LWW: Use timestamp
    FirstWriteWins,     // FWW: Keep original
    FieldLevelMerge,    // Merge at field level
    MultiValue,         // Keep all values (MV register)
    Custom              // Custom resolver
}

// CRDT Sync Manager
public class CrdtSyncManager
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly VectorClock _localClock;
    private readonly string _nodeId;
    private readonly ConflictStrategy _defaultStrategy;

    public CrdtSyncManager(
        IUnitOfWork unitOfWork,
        string nodeId,
        ConflictStrategy defaultStrategy = ConflictStrategy.LastWriteWins)
    {
        _unitOfWork = unitOfWork;
        _nodeId = nodeId;
        _localClock = new VectorClock();
        _defaultStrategy = defaultStrategy;
    }

    public async Task<T> ApplyChangeAsync<T>(
        T localEntity,
        T remoteEntity,
        ConflictStrategy? strategy = null) where T : class, ISyncableEntity
    {
        var ordering = localEntity.VectorClock.Compare(remoteEntity.VectorClock);
        var effectiveStrategy = strategy ?? _defaultStrategy;

        return ordering switch
        {
            CausalOrdering.Before => remoteEntity,
            CausalOrdering.After => localEntity,
            CausalOrdering.Equal => localEntity,
            CausalOrdering.Concurrent => ResolveConflict(
                localEntity, remoteEntity, effectiveStrategy),
            _ => localEntity
        };
    }

    private T ResolveConflict<T>(
        T local,
        T remote,
        ConflictStrategy strategy) where T : class, ISyncableEntity
    {
        return strategy switch
        {
            ConflictStrategy.LastWriteWins =>
                local.UpdatedAt > remote.UpdatedAt ? local : remote,

            ConflictStrategy.FirstWriteWins =>
                local.CreatedAt < remote.CreatedAt ? local : remote,

            ConflictStrategy.FieldLevelMerge =>
                MergeFields(local, remote),

            _ => local
        };
    }

    private T MergeFields<T>(T local, T remote) where T : class, ISyncableEntity
    {
        // Field-level merge: take newer value for each field
        var properties = typeof(T).GetProperties()
            .Where(p => p.CanRead && p.CanWrite);

        foreach (var prop in properties)
        {
            var localMeta = local.GetFieldMetadata(prop.Name);
            var remoteMeta = remote.GetFieldMetadata(prop.Name);

            if (remoteMeta.UpdatedAt > localMeta.UpdatedAt)
            {
                prop.SetValue(local, prop.GetValue(remote));
            }
        }

        // Merge vector clocks
        local.VectorClock.Merge(remote.VectorClock);
        return local;
    }

    public async Task MarkForSyncAsync<T>(T entity) where T : class, ISyncableEntity
    {
        _localClock.Increment(_nodeId);
        entity.VectorClock = _localClock;
        entity.SyncStatus = SyncStatus.Pending;
        entity.UpdatedAt = DateTime.UtcNow;

        await _unitOfWork.SaveChangesAsync();
    }
}
```

### 7. Security Architecture

```csharp
// Password hashing with PBKDF2-SHA256
public class PasswordHasher : IPasswordHasher
{
    private const int Iterations = 100_000;
    private const int SaltSize = 16;
    private const int HashSize = 32;

    public string HashPassword(string password)
    {
        var salt = RandomNumberGenerator.GetBytes(SaltSize);
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        var result = new byte[SaltSize + HashSize];
        Buffer.BlockCopy(salt, 0, result, 0, SaltSize);
        Buffer.BlockCopy(hash, 0, result, SaltSize, HashSize);

        return Convert.ToBase64String(result);
    }

    public bool VerifyPassword(string password, string hashedPassword)
    {
        var bytes = Convert.FromBase64String(hashedPassword);

        var salt = new byte[SaltSize];
        Buffer.BlockCopy(bytes, 0, salt, 0, SaltSize);

        var storedHash = new byte[HashSize];
        Buffer.BlockCopy(bytes, SaltSize, storedHash, 0, HashSize);

        var computedHash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        return CryptographicOperations.FixedTimeEquals(storedHash, computedHash);
    }
}

// RBAC (Role-Based Access Control)
public interface IAuthorizationService
{
    Task<bool> HasPermissionAsync(string userId, string permission);
    Task<bool> IsInRoleAsync(string userId, string role);
    Task<IEnumerable<string>> GetPermissionsAsync(string userId);
}

public class AuthorizationService : IAuthorizationService
{
    private readonly IUnitOfWork _unitOfWork;

    public AuthorizationService(IUnitOfWork unitOfWork)
    {
        _unitOfWork = unitOfWork;
    }

    public async Task<bool> HasPermissionAsync(string userId, string permission)
    {
        var permissions = await GetPermissionsAsync(userId);
        return permissions.Contains(permission);
    }

    public async Task<bool> IsInRoleAsync(string userId, string role)
    {
        var user = await _unitOfWork.Users.GetByIdAsync(userId);
        return user?.Roles.Any(r => r.Name == role) ?? false;
    }

    public async Task<IEnumerable<string>> GetPermissionsAsync(string userId)
    {
        var user = await _unitOfWork.Users.GetByIdAsync(userId);
        if (user == null) return Enumerable.Empty<string>();

        return user.Roles
            .SelectMany(r => r.Permissions)
            .Select(p => p.Name)
            .Distinct();
    }
}

// Audit logging
public class AuditService : IAuditService
{
    private readonly IUnitOfWork _unitOfWork;

    public async Task LogAsync(AuditEntry entry)
    {
        entry.Timestamp = DateTime.UtcNow;
        await _unitOfWork.AuditLogs.AddAsync(entry);
        await _unitOfWork.SaveChangesAsync();
    }
}

public record AuditEntry
{
    public string Id { get; init; } = Guid.NewGuid().ToString();
    public string UserId { get; init; } = string.Empty;
    public string Action { get; init; } = string.Empty;
    public string EntityType { get; init; } = string.Empty;
    public string EntityId { get; init; } = string.Empty;
    public string? OldValue { get; init; }
    public string? NewValue { get; init; }
    public DateTime Timestamp { get; set; }
}
```

## Code Review Checklist

### Required Items
- [ ] Follow Clean Architecture layering (5 layers)
- [ ] ViewModel uses MVVM UDF pattern (Input/Output/Effect)
- [ ] Type-safe navigation via INavGraph
- [ ] Repository + Unit of Work pattern implemented
- [ ] CRDT sync for offline-first scenarios

### Performance Checks
- [ ] Use async/await properly
- [ ] Implement lazy loading for plugins
- [ ] Cache frequently accessed data
- [ ] Optimize database queries with EF Core

### Security Checks
- [ ] PBKDF2-SHA256 for password hashing (100K iterations)
- [ ] RBAC properly configured
- [ ] Audit logging enabled
- [ ] Assembly isolation for plugins
- [ ] No hardcoded secrets

### Plugin Checks
- [ ] Plugin manifest complete
- [ ] Activation events configured
- [ ] Cleanup in OnDeactivateAsync
- [ ] Uses IPluginContext services

## Common Issues

### WinUI 3 Issues
1. Ensure Windows App SDK is properly installed
2. Check XAML compilation errors
3. Verify resource dictionary merging

### EF Core Issues
1. Run migrations: `dotnet ef database update`
2. Check connection string configuration
3. Review lazy loading settings

### Plugin Loading Issues
1. Verify AssemblyLoadContext configuration
2. Check plugin dependencies
3. Review manifest activation events

## Tech Stack Reference

| Technology | Recommended Version |
|------------|---------------------|
| .NET | 10.0+ |
| C# | 14.0+ |
| WinUI 3 | 3.0+ |
| EF Core | 10.0+ |
| SQLite | Latest |
| xUnit | Latest |
| CommunityToolkit.Mvvm | Latest |
