# Windows Developer Skill - Technical Reference

## Project Structure

```
arcana-windows/
├── src/
│   ├── Arcana.App/              # WinUI 3 presentation layer
│   │   ├── Views/               # XAML views
│   │   ├── ViewModels/          # MVVM UDF ViewModels
│   │   ├── Controls/            # Custom controls
│   │   └── Navigation/          # NavGraph
│   ├── Arcana.Domain/           # Business entities & services
│   │   ├── Entities/
│   │   ├── Services/
│   │   └── Interfaces/
│   ├── Arcana.Data/             # Repository + Unit of Work
│   │   ├── Repositories/
│   │   ├── DbContext/
│   │   └── Migrations/
│   ├── Arcana.Infrastructure/   # DI, Security, Settings
│   │   ├── Security/
│   │   ├── Settings/
│   │   └── DependencyInjection/
│   ├── Arcana.Sync/             # CRDT Sync Engine
│   │   ├── VectorClocks/
│   │   └── Conflicts/
│   ├── Arcana.Plugins/          # Plugin runtime
│   │   └── Runtime/
│   └── Arcana.Plugins.Contracts/ # Plugin interfaces
│       └── Interfaces/
├── plugins/                     # Built-in plugins
│   └── FlowChartModule/
└── tests/                       # 507 unit tests
    ├── Arcana.App.Tests/
    ├── Arcana.Domain.Tests/
    └── Arcana.Data.Tests/
```

## Clean Architecture - Five Layers

### Layer Dependency Rules

```
Presentation → Infrastructure → Domain → Data → Sync
     ↓              ↓            ↓        ↓
  WinUI 3         DI/Config   Entities  EF Core  CRDT
```

**Key Rules:**
- Each layer can only depend on layers below it
- Domain layer contains pure business logic with no framework dependencies
- Data layer implements repository interfaces defined in Domain
- Sync layer handles CRDT operations independently

### 1. Presentation Layer (Arcana.App)

```csharp
// ViewModel registration
public static class ViewModelExtensions
{
    public static IServiceCollection AddViewModels(this IServiceCollection services)
    {
        services.AddTransient<HomeViewModel>();
        services.AddTransient<UserListViewModel>();
        services.AddTransient<UserDetailViewModel>();
        services.AddTransient<OrderListViewModel>();
        services.AddTransient<SettingsViewModel>();
        return services;
    }
}

// View-ViewModel binding
public sealed partial class UserListPage : Page
{
    public UserListViewModel ViewModel { get; }

    public UserListPage()
    {
        ViewModel = App.GetService<UserListViewModel>();
        InitializeComponent();
        DataContext = ViewModel;
    }

    protected override void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        ViewModel.OnInput(new UserListViewModel.Input.Load());
    }
}
```

### 2. Infrastructure Layer (Arcana.Infrastructure)

```csharp
// Dependency injection setup
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services)
    {
        // Security
        services.AddSingleton<IPasswordHasher, PasswordHasher>();
        services.AddSingleton<IAuthorizationService, AuthorizationService>();
        services.AddSingleton<IAuditService, AuditService>();

        // Settings
        services.AddSingleton<ISettingsService, SettingsService>();
        services.AddSingleton<IThemeService, ThemeService>();

        // Logging
        services.AddLogging(builder =>
        {
            builder.AddDebug();
            builder.AddFile("logs/app.log");
        });

        return services;
    }
}
```

### 3. Domain Layer (Arcana.Domain)

```csharp
// Entity base class
public abstract class Entity : IEntity
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public bool IsDeleted { get; set; }
    public DateTime? DeletedAt { get; set; }
}

// Domain service interface
public interface IUserService
{
    Task<User?> GetByIdAsync(string id);
    Task<IEnumerable<User>> GetAllAsync();
    Task<User> CreateAsync(CreateUserDto dto);
    Task<User> UpdateAsync(string id, UpdateUserDto dto);
    Task DeleteAsync(string id);
    Task<bool> ValidateCredentialsAsync(string email, string password);
}
```

### 4. Data Layer (Arcana.Data)

```csharp
// DbContext configuration
public class AppDbContext : DbContext
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }

    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<Entity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
            }
        }
        return base.SaveChangesAsync(cancellationToken);
    }
}
```

### 5. Sync Layer (Arcana.Sync)

```csharp
// Syncable entity interface
public interface ISyncableEntity : IEntity
{
    VectorClock VectorClock { get; set; }
    SyncStatus SyncStatus { get; set; }
    FieldMetadata GetFieldMetadata(string fieldName);
}

public enum SyncStatus
{
    Synced,
    Pending,
    Conflict,
    Failed
}
```

## MVVM UDF Pattern

### Input/Output/Effect Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      View (XAML)                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │   Bindings   │    │   Commands   │    │  Events  │  │
│  └──────┬───────┘    └──────┬───────┘    └────┬─────┘  │
└─────────┼────────────────────┼──────────────────┼───────┘
          │                    │                  │
          ▼                    ▼                  │
┌─────────────────────────────────────────────────┼───────┐
│                  ViewModel                      │       │
│  ┌────────────────────────────────────────────┐ │       │
│  │  Output (ObservableObject)                 │ │       │
│  │  - Properties for UI binding               │◄┘       │
│  │  - Read-only state                         │         │
│  └────────────────────────────────────────────┘         │
│                                                         │
│  ┌────────────────────────────────────────────┐         │
│  │  Input (Records)                           │         │
│  │  - User actions as command objects         │◄── OnInput()
│  │  - Single entry point                      │         │
│  └────────────────────────────────────────────┘         │
│                                                         │
│  ┌────────────────────────────────────────────┐         │
│  │  Effect (Subject<Effect>)                  │         │
│  │  - Side effects (navigation, dialogs)      │───► Subscribe
│  │  - One-time events                         │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### CommunityToolkit.Mvvm Integration

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

public partial class ProductViewModel : ObservableObject
{
    // Generated: public string Name { get; set; }
    // Generated: partial void OnNameChanging(string value);
    // Generated: partial void OnNameChanged(string value);
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FullName))]
    private string _name = string.Empty;

    [ObservableProperty]
    private decimal _price;

    public string FullName => $"Product: {Name}";

    // Generated: public IRelayCommand SaveCommand { get; }
    [RelayCommand]
    private async Task SaveAsync()
    {
        // Save logic
    }

    // Generated: public IRelayCommand<string> DeleteCommand { get; }
    [RelayCommand]
    private async Task DeleteAsync(string id)
    {
        // Delete logic
    }
}
```

## WinUI 3 Components

### XAML Data Binding

```xml
<!-- Two-way binding with UpdateSourceTrigger -->
<TextBox
    Text="{x:Bind ViewModel.Out.Name, Mode=TwoWay, UpdateSourceTrigger=PropertyChanged}"
    PlaceholderText="Enter name" />

<!-- Command binding -->
<Button
    Content="Save"
    Command="{x:Bind ViewModel.SaveCommand}"
    IsEnabled="{x:Bind ViewModel.Out.CanSave, Mode=OneWay}" />

<!-- Collection binding with ItemsSource -->
<ListView ItemsSource="{x:Bind ViewModel.Out.Items, Mode=OneWay}">
    <ListView.ItemTemplate>
        <DataTemplate x:DataType="models:Product">
            <StackPanel Orientation="Horizontal">
                <TextBlock Text="{x:Bind Name}" />
                <TextBlock Text="{x:Bind Price}" />
            </StackPanel>
        </DataTemplate>
    </ListView.ItemTemplate>
</ListView>
```

### Resource Dictionaries

```xml
<!-- App.xaml -->
<Application.Resources>
    <ResourceDictionary>
        <ResourceDictionary.MergedDictionaries>
            <XamlControlsResources xmlns="using:Microsoft.UI.Xaml.Controls" />
            <ResourceDictionary Source="Themes/Light.xaml" />
            <ResourceDictionary Source="Themes/Dark.xaml" />
            <ResourceDictionary Source="Styles/Common.xaml" />
        </ResourceDictionary.MergedDictionaries>

        <!-- Global styles -->
        <Style x:Key="PageTitleStyle" TargetType="TextBlock">
            <Setter Property="FontSize" Value="28" />
            <Setter Property="FontWeight" Value="SemiBold" />
            <Setter Property="Margin" Value="0,0,0,16" />
        </Style>
    </ResourceDictionary>
</Application.Resources>
```

### Custom Controls

```csharp
public sealed class LoadingOverlay : ContentControl
{
    public static readonly DependencyProperty IsLoadingProperty =
        DependencyProperty.Register(
            nameof(IsLoading),
            typeof(bool),
            typeof(LoadingOverlay),
            new PropertyMetadata(false, OnIsLoadingChanged));

    public bool IsLoading
    {
        get => (bool)GetValue(IsLoadingProperty);
        set => SetValue(IsLoadingProperty, value);
    }

    public static readonly DependencyProperty MessageProperty =
        DependencyProperty.Register(
            nameof(Message),
            typeof(string),
            typeof(LoadingOverlay),
            new PropertyMetadata("Loading..."));

    public string Message
    {
        get => (string)GetValue(MessageProperty);
        set => SetValue(MessageProperty, value);
    }

    private static void OnIsLoadingChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        var control = (LoadingOverlay)d;
        control.Visibility = (bool)e.NewValue ? Visibility.Visible : Visibility.Collapsed;
    }
}
```

## Navigation System

### Type-Safe NavGraph

```csharp
public interface INavGraph
{
    // Main navigation
    void ToHome();
    void ToUserList();
    void ToUserDetail(string userId);
    void ToUserEdit(string userId);
    void ToOrderList();
    void ToOrderDetail(string orderId);
    void ToSettings();

    // Navigation control
    void Back();
    bool CanGoBack { get; }

    // Navigation events
    event EventHandler<NavigatedEventArgs>? Navigated;
}

public class NavigatedEventArgs : EventArgs
{
    public Type PageType { get; }
    public object? Parameter { get; }
    public NavigationMode Mode { get; }

    public NavigatedEventArgs(Type pageType, object? parameter, NavigationMode mode)
    {
        PageType = pageType;
        Parameter = parameter;
        Mode = mode;
    }
}
```

### Navigation with Parameters

```csharp
// ViewModel receiving navigation parameter
public partial class UserDetailViewModel : ObservableObject
{
    private readonly IUserService _userService;

    public Output Out { get; } = new();

    public void Initialize(string userId)
    {
        OnInput(new Input.LoadUser(userId));
    }

    public sealed class Input
    {
        public record LoadUser(string UserId);
        public record Edit;
        public record Delete;
    }
}

// View handling navigation
public sealed partial class UserDetailPage : Page
{
    protected override void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        if (e.Parameter is string userId)
        {
            ViewModel.Initialize(userId);
        }
    }
}
```

## Plugin System

### 18 Plugin Types

| Type | Description | Use Case |
|------|-------------|----------|
| Menu | Menu extensions | Add custom menu items |
| View | Custom views | Add new UI pages |
| Module | Full feature modules | Complete features with UI and logic |
| Theme | UI themes | Custom visual themes |
| Authentication | Auth providers | OAuth, SSO, etc. |
| Data | Data sources | External data integrations |
| Command | Custom commands | Keyboard shortcuts, actions |
| Service | Background services | Long-running tasks |
| Validator | Validation rules | Custom validation logic |
| Storage | Storage providers | Cloud storage, custom backends |
| Export | Export formats | PDF, Excel, etc. |
| Import | Import formats | Data import handlers |
| Report | Report generators | Custom reports |
| Notification | Notification channels | Email, SMS, push |
| Logging | Logging providers | Custom log sinks |
| Cache | Cache providers | Redis, custom caching |
| Search | Search providers | Elasticsearch, custom search |
| Analytics | Analytics providers | Usage tracking |

### Plugin Context Services (12 Services)

```csharp
public interface IPluginContext
{
    // Communication
    IMessageBus MessageBus { get; }           // Pub/sub messaging
    IEventAggregator EventAggregator { get; } // Event aggregation

    // State
    IStateStore StateStore { get; }           // Shared state store

    // Navigation
    IPluginNavGraph Navigation { get; }       // Plugin navigation

    // UI Services
    IDialogService DialogService { get; }     // Dialog display
    INotificationService NotificationService { get; } // Notifications

    // Configuration
    ISettingsService SettingsService { get; } // App settings
    IPluginStorage Storage { get; }           // Plugin-specific storage

    // Utility
    ILoggerFactory LoggerFactory { get; }     // Logging
    IServiceProvider ServiceProvider { get; } // DI container
    ILocalizationService Localization { get; } // i18n
    IThemeService ThemeService { get; }       // Theme management
}
```

### Plugin Lifecycle

```
┌────────────────┐    ┌─────────────────┐    ┌──────────────┐
│    Discover    │───►│      Load       │───►│   Activate   │
│  (Scan DLLs)   │    │ (AssemblyLoad)  │    │ (Initialize) │
└────────────────┘    └─────────────────┘    └──────────────┘
                                                     │
                                                     ▼
┌────────────────┐    ┌─────────────────┐    ┌──────────────┐
│    Unload      │◄───│   Deactivate    │◄───│    Active    │
│  (GC Context)  │    │    (Cleanup)    │    │  (Running)   │
└────────────────┘    └─────────────────┘    └──────────────┘
```

## Entity Framework Core

### Entity Configuration

```csharp
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("Users");

        builder.HasKey(u => u.Id);

        builder.Property(u => u.Email)
            .IsRequired()
            .HasMaxLength(255);

        builder.HasIndex(u => u.Email)
            .IsUnique();

        builder.Property(u => u.PasswordHash)
            .IsRequired()
            .HasMaxLength(500);

        builder.HasMany(u => u.Orders)
            .WithOne(o => o.User)
            .HasForeignKey(o => o.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        // Soft delete filter
        builder.HasQueryFilter(u => !u.IsDeleted);
    }
}
```

### Migrations

```bash
# Add migration
dotnet ef migrations add InitialCreate -p Arcana.Data -s Arcana.App

# Update database
dotnet ef database update -p Arcana.Data -s Arcana.App

# Generate SQL script
dotnet ef migrations script -p Arcana.Data -s Arcana.App -o migration.sql
```

### Query Optimization

```csharp
// Eager loading
var users = await _context.Users
    .Include(u => u.Orders)
        .ThenInclude(o => o.OrderItems)
    .ToListAsync();

// Projection for performance
var userDtos = await _context.Users
    .Select(u => new UserDto
    {
        Id = u.Id,
        Email = u.Email,
        OrderCount = u.Orders.Count
    })
    .ToListAsync();

// AsNoTracking for read-only
var readOnlyUsers = await _context.Users
    .AsNoTracking()
    .ToListAsync();
```

## CRDT Sync Engine

### Vector Clock Operations

```csharp
// Compare two vector clocks
public enum CausalOrdering
{
    Before,     // This happened before other
    After,      // This happened after other
    Equal,      // Same state
    Concurrent  // Conflict - happened independently
}
```

### Conflict Resolution Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| LastWriteWins | Use latest timestamp | Simple data, low conflict |
| FirstWriteWins | Keep original value | Immutable once created |
| FieldLevelMerge | Merge per field | Complex objects |
| MultiValue | Keep all values | User resolution |
| Custom | Custom logic | Domain-specific |

### Sync Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Local     │◄───────►│    Sync     │◄───────►│   Remote    │
│  Changes    │         │   Engine    │         │   Server    │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   SQLite    │         │   Vector    │         │   Cloud     │
│     DB      │         │   Clocks    │         │     DB      │
└─────────────┘         └─────────────┘         └─────────────┘
```

## Security

### Password Hashing (PBKDF2-SHA256)

```csharp
// Configuration
private const int Iterations = 100_000;  // 100K iterations
private const int SaltSize = 16;         // 128-bit salt
private const int HashSize = 32;         // 256-bit hash
```

### RBAC Structure

```csharp
public class User
{
    public string Id { get; set; }
    public ICollection<Role> Roles { get; set; }
}

public class Role
{
    public string Id { get; set; }
    public string Name { get; set; }
    public ICollection<Permission> Permissions { get; set; }
}

public class Permission
{
    public string Id { get; set; }
    public string Name { get; set; }  // e.g., "users:read", "orders:write"
}
```

## Testing

### xUnit with Moq

```csharp
public class UserServiceTests
{
    private readonly Mock<IUnitOfWork> _mockUnitOfWork;
    private readonly Mock<IPasswordHasher> _mockPasswordHasher;
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _mockUnitOfWork = new Mock<IUnitOfWork>();
        _mockPasswordHasher = new Mock<IPasswordHasher>();
        _sut = new UserService(_mockUnitOfWork.Object, _mockPasswordHasher.Object);
    }

    [Fact]
    public async Task GetByIdAsync_WhenUserExists_ReturnsUser()
    {
        // Arrange
        var expectedUser = new User { Id = "1", Email = "test@example.com" };
        _mockUnitOfWork.Setup(u => u.Users.GetByIdAsync("1"))
            .ReturnsAsync(expectedUser);

        // Act
        var result = await _sut.GetByIdAsync("1");

        // Assert
        Assert.NotNull(result);
        Assert.Equal("test@example.com", result.Email);
    }
}
```

### ViewModel Testing

```csharp
public class UserListViewModelTests
{
    [Fact]
    public async Task Load_PopulatesUserList()
    {
        // Arrange
        var mockService = new Mock<IUserService>();
        mockService.Setup(s => s.GetAllAsync())
            .ReturnsAsync(new[] { new User { Id = "1", Email = "test@test.com" } });

        var viewModel = new UserListViewModel(mockService.Object);

        // Act
        viewModel.OnInput(new UserListViewModel.Input.Load());
        await Task.Delay(100); // Wait for async operation

        // Assert
        Assert.Single(viewModel.Out.Users);
        Assert.Equal("test@test.com", viewModel.Out.Users.First().Email);
    }
}
```

## Common Commands

```bash
# Build project
dotnet build

# Run application
dotnet run --project src/Arcana.App

# Run tests
dotnet test

# Run tests with coverage
dotnet test --collect:"XPlat Code Coverage"

# Package application
dotnet publish -c Release -r win-x64 --self-contained

# Create MSIX package
msbuild /p:Configuration=Release /p:Platform=x64 /p:AppxPackageDir=./publish/

# EF Core commands
dotnet ef migrations add <MigrationName> -p Arcana.Data -s Arcana.App
dotnet ef database update -p Arcana.Data -s Arcana.App
```
