# Windows Developer Skill - Design Patterns

## Architecture Patterns

### Clean Architecture (Five Layers)

```
┌─────────────────────────────────────────────────────────┐
│                 Presentation Layer                       │
│              WinUI 3 + MVVM UDF + NavGraph               │
├─────────────────────────────────────────────────────────┤
│               Infrastructure Layer                       │
│             DI + Security + Settings                     │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer                           │
│            Business Entities + Services                  │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                            │
│           Repository + Unit of Work + EF Core            │
├─────────────────────────────────────────────────────────┤
│                    Sync Layer                            │
│              CRDT Engine + Vector Clocks                 │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**
- Dependency flows inward (outer layers depend on inner layers)
- Domain layer has no external dependencies
- Data layer implements interfaces defined in Domain
- Presentation layer only interacts with Domain services

### MVVM UDF (Unidirectional Data Flow)

```
┌─────────────────────────────────────────────────────────┐
│                      View (XAML)                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐   │
│  │   Bindings   │◄───│    Output    │    │  Events  │   │
│  └──────────────┘    └──────────────┘    └────┬─────┘   │
│                                               │         │
│                           ▲                   │         │
│                           │                   │         │
│                           │                   ▼         │
│                      ┌────┴────────────────────┐        │
│                      │       OnInput()         │        │
│                      └─────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     ViewModel                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Input (Records)                                   │  │
│  │ - User actions as immutable command objects       │  │
│  │ - Single entry point via OnInput()                │  │
│  └───────────────────────────────────────────────────┘  │
│                              │                          │
│                              ▼                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ State Processing                                  │  │
│  │ - Pattern matching on Input type                  │  │
│  │ - Business logic execution                        │  │
│  │ - Service calls                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                              │                          │
│                 ┌────────────┴────────────┐             │
│                 ▼                         ▼             │
│  ┌─────────────────────────┐  ┌─────────────────────┐   │
│  │ Output (Observable)     │  │ Effect (Subject)    │   │
│  │ - Read-only state       │  │ - Navigation        │   │
│  │ - UI bindings           │  │ - Dialogs           │   │
│  │ - Property changes      │  │ - One-time events   │   │
│  └─────────────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**

```csharp
public partial class ExampleViewModel : ObservableObject
{
    // Input: Immutable command records
    public sealed class Input
    {
        public record Load;
        public record UpdateField(string Value);
        public record Submit;
    }

    // Output: Observable state
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string _field = string.Empty;

        [ObservableProperty]
        private bool _isLoading;
    }

    // Effect: Side effects
    public sealed class Effect
    {
        public record NavigateBack;
        public record ShowMessage(string Text);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    // Single entry point
    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.Load:
                _ = LoadAsync();
                break;
            case Input.UpdateField update:
                Out.Field = update.Value;
                break;
            case Input.Submit:
                _ = SubmitAsync();
                break;
        }
    }
}
```

---

## Plugin Architecture Patterns

### Plugin Lifecycle Pattern

```
     ┌──────────┐
     │ Discover │ ── Scan directories for plugin DLLs
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │   Load   │ ── Create AssemblyLoadContext, load assembly
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ Validate │ ── Check manifest, dependencies, compatibility
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ Activate │ ── Call OnActivateAsync, register services
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │  Active  │ ── Plugin running, handling events
     └────┬─────┘
          │
          ▼
     ┌────────────┐
     │ Deactivate │ ── Call OnDeactivateAsync, cleanup
     └────┬───────┘
          │
          ▼
     ┌──────────┐
     │  Unload  │ ── Unload AssemblyLoadContext, GC
     └──────────┘
```

### Assembly Isolation Pattern

```csharp
public class PluginLoadContext : AssemblyLoadContext
{
    private readonly AssemblyDependencyResolver _resolver;

    public PluginLoadContext(string pluginPath) : base(isCollectible: true)
    {
        _resolver = new AssemblyDependencyResolver(pluginPath);
    }

    protected override Assembly? Load(AssemblyName assemblyName)
    {
        // Try to resolve from plugin directory first
        string? assemblyPath = _resolver.ResolveAssemblyToPath(assemblyName);
        if (assemblyPath != null)
        {
            return LoadFromAssemblyPath(assemblyPath);
        }

        // Fall back to default context for shared assemblies
        return null;
    }

    protected override IntPtr LoadUnmanagedDll(string unmanagedDllName)
    {
        string? libraryPath = _resolver.ResolveUnmanagedDllToPath(unmanagedDllName);
        if (libraryPath != null)
        {
            return LoadUnmanagedDllFromPath(libraryPath);
        }
        return IntPtr.Zero;
    }
}
```

### Plugin Communication Pattern (Message Bus)

```csharp
public interface IMessageBus
{
    void Publish<T>(T message);
    IDisposable Subscribe<T>(Action<T> handler);
    IDisposable Subscribe<T>(Func<T, Task> handler);
}

public class MessageBus : IMessageBus
{
    private readonly ConcurrentDictionary<Type, List<object>> _handlers = new();
    private readonly object _lock = new();

    public void Publish<T>(T message)
    {
        if (_handlers.TryGetValue(typeof(T), out var handlers))
        {
            foreach (var handler in handlers.ToArray())
            {
                switch (handler)
                {
                    case Action<T> action:
                        action(message);
                        break;
                    case Func<T, Task> asyncFunc:
                        _ = asyncFunc(message);
                        break;
                }
            }
        }
    }

    public IDisposable Subscribe<T>(Action<T> handler)
    {
        var handlers = _handlers.GetOrAdd(typeof(T), _ => new List<object>());
        lock (_lock)
        {
            handlers.Add(handler);
        }
        return new Subscription(() => RemoveHandler(typeof(T), handler));
    }

    public IDisposable Subscribe<T>(Func<T, Task> handler)
    {
        var handlers = _handlers.GetOrAdd(typeof(T), _ => new List<object>());
        lock (_lock)
        {
            handlers.Add(handler);
        }
        return new Subscription(() => RemoveHandler(typeof(T), handler));
    }

    private void RemoveHandler(Type type, object handler)
    {
        if (_handlers.TryGetValue(type, out var handlers))
        {
            lock (_lock)
            {
                handlers.Remove(handler);
            }
        }
    }

    private class Subscription : IDisposable
    {
        private readonly Action _dispose;
        public Subscription(Action dispose) => _dispose = dispose;
        public void Dispose() => _dispose();
    }
}
```

---

## Data Access Patterns

### Repository Pattern with Specification

```csharp
// Specification base
public abstract class Specification<T> where T : class
{
    public abstract Expression<Func<T, bool>> ToExpression();

    public bool IsSatisfiedBy(T entity)
    {
        return ToExpression().Compile()(entity);
    }

    public Specification<T> And(Specification<T> other)
    {
        return new AndSpecification<T>(this, other);
    }

    public Specification<T> Or(Specification<T> other)
    {
        return new OrSpecification<T>(this, other);
    }

    public Specification<T> Not()
    {
        return new NotSpecification<T>(this);
    }
}

// Concrete specifications
public class ProductByNameSpec : Specification<Product>
{
    private readonly string _name;
    public ProductByNameSpec(string name) => _name = name;

    public override Expression<Func<Product, bool>> ToExpression()
    {
        return p => p.Name.Contains(_name, StringComparison.OrdinalIgnoreCase);
    }
}

public class ProductByCategorySpec : Specification<Product>
{
    private readonly string _categoryId;
    public ProductByCategorySpec(string categoryId) => _categoryId = categoryId;

    public override Expression<Func<Product, bool>> ToExpression()
    {
        return p => p.CategoryId == _categoryId;
    }
}

public class ProductInPriceRangeSpec : Specification<Product>
{
    private readonly decimal _min;
    private readonly decimal _max;

    public ProductInPriceRangeSpec(decimal min, decimal max)
    {
        _min = min;
        _max = max;
    }

    public override Expression<Func<Product, bool>> ToExpression()
    {
        return p => p.Price >= _min && p.Price <= _max;
    }
}

// Repository with specification support
public interface IRepository<T> where T : class, IEntity
{
    Task<IEnumerable<T>> FindAsync(Specification<T> spec);
    Task<T?> FindOneAsync(Specification<T> spec);
    Task<int> CountAsync(Specification<T> spec);
}

// Usage
var spec = new ProductByNameSpec("phone")
    .And(new ProductByCategorySpec("electronics"))
    .And(new ProductInPriceRangeSpec(100, 1000));

var products = await _repository.FindAsync(spec);
```

### Unit of Work Pattern

```csharp
public interface IUnitOfWork : IDisposable, IAsyncDisposable
{
    // Repositories
    IRepository<User> Users { get; }
    IRepository<Product> Products { get; }
    IRepository<Order> Orders { get; }
    IRepository<T> GetRepository<T>() where T : class, IEntity;

    // Transaction management
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    Task BeginTransactionAsync(CancellationToken cancellationToken = default);
    Task CommitAsync(CancellationToken cancellationToken = default);
    Task RollbackAsync(CancellationToken cancellationToken = default);
}

// Transaction usage
public async Task TransferAsync(string fromUserId, string toUserId, decimal amount)
{
    await _unitOfWork.BeginTransactionAsync();

    try
    {
        var fromUser = await _unitOfWork.Users.GetByIdAsync(fromUserId);
        var toUser = await _unitOfWork.Users.GetByIdAsync(toUserId);

        if (fromUser == null || toUser == null)
            throw new InvalidOperationException("User not found");

        if (fromUser.Balance < amount)
            throw new InvalidOperationException("Insufficient balance");

        fromUser.Balance -= amount;
        toUser.Balance += amount;

        await _unitOfWork.Users.UpdateAsync(fromUser);
        await _unitOfWork.Users.UpdateAsync(toUser);

        await _unitOfWork.SaveChangesAsync();
        await _unitOfWork.CommitAsync();
    }
    catch
    {
        await _unitOfWork.RollbackAsync();
        throw;
    }
}
```

### Soft Delete Pattern

```csharp
public interface ISoftDeletable
{
    bool IsDeleted { get; set; }
    DateTime? DeletedAt { get; set; }
    string? DeletedBy { get; set; }
}

public abstract class SoftDeletableEntity : Entity, ISoftDeletable
{
    public bool IsDeleted { get; set; }
    public DateTime? DeletedAt { get; set; }
    public string? DeletedBy { get; set; }
}

// EF Core configuration
public class SoftDeleteQueryFilter
{
    public static void Apply(ModelBuilder modelBuilder)
    {
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            if (typeof(ISoftDeletable).IsAssignableFrom(entityType.ClrType))
            {
                var parameter = Expression.Parameter(entityType.ClrType, "e");
                var property = Expression.Property(parameter, nameof(ISoftDeletable.IsDeleted));
                var filter = Expression.Lambda(Expression.Not(property), parameter);

                entityType.SetQueryFilter(filter);
            }
        }
    }
}

// DbContext
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);
    SoftDeleteQueryFilter.Apply(modelBuilder);
}

// Repository soft delete
public async Task SoftDeleteAsync(T entity)
{
    if (entity is ISoftDeletable softDeletable)
    {
        softDeletable.IsDeleted = true;
        softDeletable.DeletedAt = DateTime.UtcNow;
        await UpdateAsync(entity);
    }
    else
    {
        await DeleteAsync(entity);
    }
}
```

---

## CRDT Patterns

### Vector Clock Pattern

```csharp
public class VectorClock
{
    private readonly Dictionary<string, long> _clock;

    public VectorClock()
    {
        _clock = new Dictionary<string, long>();
    }

    public VectorClock(Dictionary<string, long> clock)
    {
        _clock = new Dictionary<string, long>(clock);
    }

    // Increment local counter
    public void Increment(string nodeId)
    {
        _clock[nodeId] = _clock.GetValueOrDefault(nodeId, 0) + 1;
    }

    // Merge with another clock (take max for each node)
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

    // Compare causality
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

        return (thisGreater, otherGreater) switch
        {
            (true, true) => CausalOrdering.Concurrent,
            (true, false) => CausalOrdering.After,
            (false, true) => CausalOrdering.Before,
            (false, false) => CausalOrdering.Equal
        };
    }
}
```

### Last-Write-Wins Register (LWW)

```csharp
public class LwwRegister<T>
{
    public T Value { get; private set; }
    public DateTime Timestamp { get; private set; }
    public string NodeId { get; private set; }

    public LwwRegister(T value, string nodeId)
    {
        Value = value;
        Timestamp = DateTime.UtcNow;
        NodeId = nodeId;
    }

    public bool Update(T value, DateTime timestamp, string nodeId)
    {
        // LWW: Accept if newer, or same time but higher node ID (for determinism)
        if (timestamp > Timestamp || (timestamp == Timestamp && string.Compare(nodeId, NodeId) > 0))
        {
            Value = value;
            Timestamp = timestamp;
            NodeId = nodeId;
            return true;
        }
        return false;
    }

    public void Merge(LwwRegister<T> other)
    {
        Update(other.Value, other.Timestamp, other.NodeId);
    }
}
```

### Field-Level Merge Pattern

```csharp
public class FieldLevelMerger
{
    public T Merge<T>(T local, T remote) where T : class, ISyncableEntity
    {
        var properties = typeof(T).GetProperties()
            .Where(p => p.CanRead && p.CanWrite && !IsSystemProperty(p.Name));

        foreach (var prop in properties)
        {
            var localMeta = local.GetFieldMetadata(prop.Name);
            var remoteMeta = remote.GetFieldMetadata(prop.Name);

            // Take the newer value
            if (remoteMeta.UpdatedAt > localMeta.UpdatedAt)
            {
                var remoteValue = prop.GetValue(remote);
                prop.SetValue(local, remoteValue);
            }
        }

        // Merge vector clocks
        local.VectorClock.Merge(remote.VectorClock);

        return local;
    }

    private bool IsSystemProperty(string name)
    {
        return name switch
        {
            "Id" or "CreatedAt" or "UpdatedAt" or "VectorClock" or "SyncStatus" => true,
            _ => false
        };
    }
}
```

---

## Security Patterns

### RBAC (Role-Based Access Control)

```csharp
// Attribute for permission checking
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public class RequirePermissionAttribute : Attribute
{
    public string Permission { get; }

    public RequirePermissionAttribute(string permission)
    {
        Permission = permission;
    }
}

// Permission constants
public static class Permissions
{
    public const string UsersRead = "users:read";
    public const string UsersWrite = "users:write";
    public const string UsersDelete = "users:delete";
    public const string OrdersRead = "orders:read";
    public const string OrdersWrite = "orders:write";
    public const string ProductsManage = "products:manage";
    public const string SettingsAdmin = "settings:admin";
}

// Authorization service
public class AuthorizationService : IAuthorizationService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ICurrentUserService _currentUser;

    public async Task<bool> AuthorizeAsync(string permission)
    {
        var userId = _currentUser.UserId;
        if (string.IsNullOrEmpty(userId)) return false;

        var permissions = await GetUserPermissionsAsync(userId);
        return permissions.Contains(permission);
    }

    public async Task<bool> AuthorizeAsync(string permission, string resourceId)
    {
        // Resource-level permission check
        var hasPermission = await AuthorizeAsync(permission);
        if (!hasPermission) return false;

        // Additional resource ownership check if needed
        return await CheckResourceOwnershipAsync(resourceId);
    }

    private async Task<HashSet<string>> GetUserPermissionsAsync(string userId)
    {
        var user = await _unitOfWork.Users
            .FindAsync(u => u.Id == userId)
            .ContinueWith(t => t.Result.FirstOrDefault());

        if (user == null) return new HashSet<string>();

        return user.Roles
            .SelectMany(r => r.Permissions)
            .Select(p => p.Name)
            .ToHashSet();
    }
}
```

### Secure Password Storage

```csharp
public class PasswordHasher : IPasswordHasher
{
    // PBKDF2 configuration
    private const int Iterations = 100_000;  // 100K iterations
    private const int SaltSize = 16;         // 128-bit salt
    private const int HashSize = 32;         // 256-bit hash

    public string HashPassword(string password)
    {
        // Generate random salt
        var salt = RandomNumberGenerator.GetBytes(SaltSize);

        // Derive key using PBKDF2-SHA256
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        // Combine salt + hash
        var result = new byte[SaltSize + HashSize];
        Buffer.BlockCopy(salt, 0, result, 0, SaltSize);
        Buffer.BlockCopy(hash, 0, result, SaltSize, HashSize);

        return Convert.ToBase64String(result);
    }

    public bool VerifyPassword(string password, string hashedPassword)
    {
        var bytes = Convert.FromBase64String(hashedPassword);

        // Extract salt
        var salt = new byte[SaltSize];
        Buffer.BlockCopy(bytes, 0, salt, 0, SaltSize);

        // Extract stored hash
        var storedHash = new byte[HashSize];
        Buffer.BlockCopy(bytes, SaltSize, storedHash, 0, HashSize);

        // Compute hash with same salt
        var computedHash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize
        );

        // Constant-time comparison to prevent timing attacks
        return CryptographicOperations.FixedTimeEquals(storedHash, computedHash);
    }
}
```

### Audit Logging Pattern

```csharp
public interface IAuditService
{
    Task LogAsync(AuditEntry entry);
    Task LogAsync(string action, object? details = null);
}

public class AuditService : IAuditService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ICurrentUserService _currentUser;

    public async Task LogAsync(AuditEntry entry)
    {
        entry.UserId = _currentUser.UserId ?? "system";
        entry.Timestamp = DateTime.UtcNow;
        entry.IpAddress = _currentUser.IpAddress;

        await _unitOfWork.AuditLogs.AddAsync(entry);
        await _unitOfWork.SaveChangesAsync();
    }

    public async Task LogAsync(string action, object? details = null)
    {
        await LogAsync(new AuditEntry
        {
            Action = action,
            Details = details != null ? JsonSerializer.Serialize(details) : null
        });
    }
}

// Auto-audit via interceptor
public class AuditInterceptor : SaveChangesInterceptor
{
    private readonly ICurrentUserService _currentUser;

    public override async ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken cancellationToken = default)
    {
        var context = eventData.Context;
        if (context == null) return result;

        foreach (var entry in context.ChangeTracker.Entries())
        {
            if (entry.Entity is IAuditable auditable)
            {
                switch (entry.State)
                {
                    case EntityState.Added:
                        auditable.CreatedBy = _currentUser.UserId;
                        auditable.CreatedAt = DateTime.UtcNow;
                        break;
                    case EntityState.Modified:
                        auditable.ModifiedBy = _currentUser.UserId;
                        auditable.ModifiedAt = DateTime.UtcNow;
                        break;
                }
            }
        }

        return result;
    }
}
```

---

## UI Patterns

### Converters Pattern

```csharp
// Bool to Visibility
public class BoolToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        bool invert = parameter?.ToString() == "Invert";
        bool boolValue = value is bool b && b;

        if (invert) boolValue = !boolValue;

        return boolValue ? Visibility.Visible : Visibility.Collapsed;
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
    {
        throw new NotImplementedException();
    }
}

// Null to Bool
public class NotNullToBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        return value != null;
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
    {
        throw new NotImplementedException();
    }
}

// String format
public class StringFormatConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        if (parameter is string format)
        {
            return string.Format(format, value);
        }
        return value?.ToString() ?? string.Empty;
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
    {
        throw new NotImplementedException();
    }
}

// Registration in App.xaml
<Application.Resources>
    <converters:BoolToVisibilityConverter x:Key="BoolToVisibilityConverter" />
    <converters:NotNullToBoolConverter x:Key="NotNullToBoolConverter" />
    <converters:StringFormatConverter x:Key="StringFormatConverter" />
</Application.Resources>
```

### Dialog Service Pattern

```csharp
public interface IDialogService
{
    Task<bool> ConfirmAsync(string title, string message);
    Task AlertAsync(string title, string message);
    Task<string?> PromptAsync(string title, string placeholder);
    Task<T?> ShowDialogAsync<T>(object parameter = null);
}

public class DialogService : IDialogService
{
    private readonly XamlRoot _xamlRoot;

    public DialogService(XamlRoot xamlRoot)
    {
        _xamlRoot = xamlRoot;
    }

    public async Task<bool> ConfirmAsync(string title, string message)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            PrimaryButtonText = "Yes",
            SecondaryButtonText = "No",
            DefaultButton = ContentDialogButton.Secondary,
            XamlRoot = _xamlRoot
        };

        var result = await dialog.ShowAsync();
        return result == ContentDialogResult.Primary;
    }

    public async Task AlertAsync(string title, string message)
    {
        var dialog = new ContentDialog
        {
            Title = title,
            Content = message,
            CloseButtonText = "OK",
            XamlRoot = _xamlRoot
        };

        await dialog.ShowAsync();
    }

    public async Task<string?> PromptAsync(string title, string placeholder)
    {
        var textBox = new TextBox { PlaceholderText = placeholder };

        var dialog = new ContentDialog
        {
            Title = title,
            Content = textBox,
            PrimaryButtonText = "OK",
            SecondaryButtonText = "Cancel",
            XamlRoot = _xamlRoot
        };

        var result = await dialog.ShowAsync();
        return result == ContentDialogResult.Primary ? textBox.Text : null;
    }
}
```

---

## Testing Patterns

### ViewModel Testing with Mock

```csharp
public class UserListViewModelTests
{
    private readonly Mock<IUserService> _mockUserService;
    private readonly UserListViewModel _viewModel;

    public UserListViewModelTests()
    {
        _mockUserService = new Mock<IUserService>();
        _viewModel = new UserListViewModel(_mockUserService.Object);
    }

    [Fact]
    public async Task Load_WhenSuccessful_PopulatesUsers()
    {
        // Arrange
        var users = new List<User>
        {
            new() { Id = "1", Email = "user1@test.com" },
            new() { Id = "2", Email = "user2@test.com" }
        };
        _mockUserService.Setup(s => s.GetAllAsync())
            .ReturnsAsync(users);

        // Act
        _viewModel.OnInput(new UserListViewModel.Input.Load());
        await Task.Delay(100); // Wait for async

        // Assert
        Assert.Equal(2, _viewModel.Out.Users.Count);
        Assert.False(_viewModel.Out.IsLoading);
    }

    [Fact]
    public async Task Load_WhenFails_SetsError()
    {
        // Arrange
        _mockUserService.Setup(s => s.GetAllAsync())
            .ThrowsAsync(new Exception("Network error"));

        // Act
        _viewModel.OnInput(new UserListViewModel.Input.Load());
        await Task.Delay(100);

        // Assert
        Assert.NotNull(_viewModel.Out.Error);
        Assert.Contains("Network error", _viewModel.Out.Error);
    }
}
```

### Repository Testing with In-Memory Database

```csharp
public class UserRepositoryTests : IDisposable
{
    private readonly AppDbContext _context;
    private readonly Repository<User> _repository;

    public UserRepositoryTests()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        _context = new AppDbContext(options);
        _repository = new Repository<User>(_context);
    }

    [Fact]
    public async Task AddAsync_CreatesNewUser()
    {
        // Arrange
        var user = new User { Email = "test@test.com" };

        // Act
        await _repository.AddAsync(user);
        await _context.SaveChangesAsync();

        // Assert
        var saved = await _repository.GetByIdAsync(user.Id);
        Assert.NotNull(saved);
        Assert.Equal("test@test.com", saved.Email);
    }

    [Fact]
    public async Task SoftDeleteAsync_SetsIsDeletedFlag()
    {
        // Arrange
        var user = new User { Email = "test@test.com" };
        await _repository.AddAsync(user);
        await _context.SaveChangesAsync();

        // Act
        await _repository.SoftDeleteAsync(user);
        await _context.SaveChangesAsync();

        // Assert
        var deleted = await _context.Users
            .IgnoreQueryFilters()
            .FirstOrDefaultAsync(u => u.Id == user.Id);

        Assert.True(deleted?.IsDeleted);
        Assert.NotNull(deleted?.DeletedAt);
    }

    public void Dispose()
    {
        _context.Dispose();
    }
}
```

### Integration Testing

```csharp
public class SyncServiceIntegrationTests : IAsyncLifetime
{
    private IHost _host = null!;
    private ISyncService _syncService = null!;
    private IUnitOfWork _unitOfWork = null!;

    public async Task InitializeAsync()
    {
        _host = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddDbContext<AppDbContext>(options =>
                    options.UseInMemoryDatabase("TestDb"));
                services.AddScoped<IUnitOfWork, UnitOfWork>();
                services.AddScoped<ISyncService, SyncService>();
            })
            .Build();

        await _host.StartAsync();

        var scope = _host.Services.CreateScope();
        _syncService = scope.ServiceProvider.GetRequiredService<ISyncService>();
        _unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();
    }

    [Fact]
    public async Task Sync_WhenOffline_ReturnsPendingStatus()
    {
        // Arrange
        var user = new User { Email = "test@test.com", SyncStatus = SyncStatus.Pending };
        await _unitOfWork.Users.AddAsync(user);
        await _unitOfWork.SaveChangesAsync();

        // Act (offline mode)
        var result = await _syncService.SyncAsync<User>();

        // Assert
        Assert.Equal(SyncStatus.Offline, result.Status);
    }

    public async Task DisposeAsync()
    {
        await _host.StopAsync();
        _host.Dispose();
    }
}
```

---

## Performance Patterns

### Lazy Loading for Plugins

```csharp
public class LazyPluginLoader
{
    private readonly ConcurrentDictionary<string, Lazy<IArcanaPlugin>> _plugins = new();
    private readonly IPluginDiscovery _discovery;

    public LazyPluginLoader(IPluginDiscovery discovery)
    {
        _discovery = discovery;
    }

    public async Task DiscoverPluginsAsync()
    {
        var manifests = await _discovery.DiscoverAsync();

        foreach (var manifest in manifests)
        {
            _plugins[manifest.Key] = new Lazy<IArcanaPlugin>(
                () => LoadPlugin(manifest.PluginPath),
                LazyThreadSafetyMode.ExecutionAndPublication
            );
        }
    }

    public IArcanaPlugin? GetPlugin(string key)
    {
        return _plugins.TryGetValue(key, out var lazy) ? lazy.Value : null;
    }

    public IEnumerable<string> GetAvailablePlugins()
    {
        return _plugins.Keys;
    }

    private IArcanaPlugin LoadPlugin(string path)
    {
        var loadContext = new PluginLoadContext(path);
        var assembly = loadContext.LoadFromAssemblyPath(path);
        var pluginType = assembly.GetTypes()
            .First(t => typeof(IArcanaPlugin).IsAssignableFrom(t));
        return (IArcanaPlugin)Activator.CreateInstance(pluginType)!;
    }
}
```

### Caching Pattern

```csharp
public interface ICacheService
{
    Task<T?> GetAsync<T>(string key);
    Task SetAsync<T>(string key, T value, TimeSpan? expiry = null);
    Task RemoveAsync(string key);
    Task<T> GetOrCreateAsync<T>(string key, Func<Task<T>> factory, TimeSpan? expiry = null);
}

public class MemoryCacheService : ICacheService
{
    private readonly IMemoryCache _cache;
    private readonly ILogger<MemoryCacheService> _logger;

    public MemoryCacheService(IMemoryCache cache, ILogger<MemoryCacheService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public Task<T?> GetAsync<T>(string key)
    {
        _cache.TryGetValue(key, out T? value);
        return Task.FromResult(value);
    }

    public Task SetAsync<T>(string key, T value, TimeSpan? expiry = null)
    {
        var options = new MemoryCacheEntryOptions();
        if (expiry.HasValue)
        {
            options.AbsoluteExpirationRelativeToNow = expiry;
        }
        _cache.Set(key, value, options);
        return Task.CompletedTask;
    }

    public Task RemoveAsync(string key)
    {
        _cache.Remove(key);
        return Task.CompletedTask;
    }

    public async Task<T> GetOrCreateAsync<T>(string key, Func<Task<T>> factory, TimeSpan? expiry = null)
    {
        if (_cache.TryGetValue(key, out T? cached))
        {
            return cached!;
        }

        var value = await factory();
        await SetAsync(key, value, expiry);
        return value;
    }
}

// Usage with repository
public class CachedProductRepository : IRepository<Product>
{
    private readonly IRepository<Product> _inner;
    private readonly ICacheService _cache;
    private readonly TimeSpan _cacheExpiry = TimeSpan.FromMinutes(5);

    public async Task<Product?> GetByIdAsync(string id)
    {
        var key = $"product:{id}";
        return await _cache.GetOrCreateAsync(
            key,
            () => _inner.GetByIdAsync(id),
            _cacheExpiry
        );
    }
}
```
