# Windows Developer Skill - Code Examples

## Example 1: User Authentication Feature

Complete login/logout implementation with MVVM UDF pattern.

### LoginViewModel

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using System.Reactive.Subjects;

public partial class LoginViewModel : ObservableObject
{
    // MARK: - Input
    public sealed class Input
    {
        public record UpdateEmail(string Email);
        public record UpdatePassword(string Password);
        public record Login;
        public record ForgotPassword;
    }

    // MARK: - Output
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string _email = string.Empty;

        [ObservableProperty]
        private string _password = string.Empty;

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private string? _error;

        [ObservableProperty]
        private bool _canLogin;

        partial void OnEmailChanged(string value) => UpdateCanLogin();
        partial void OnPasswordChanged(string value) => UpdateCanLogin();

        private void UpdateCanLogin()
        {
            CanLogin = !string.IsNullOrWhiteSpace(Email) &&
                       !string.IsNullOrWhiteSpace(Password) &&
                       !IsLoading;
        }
    }

    // MARK: - Effect
    public sealed class Effect
    {
        public record NavigateToHome;
        public record NavigateToForgotPassword;
        public record ShowError(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IAuthService _authService;
    private readonly INavGraph _navGraph;

    public LoginViewModel(IAuthService authService, INavGraph navGraph)
    {
        _authService = authService;
        _navGraph = navGraph;
    }

    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.UpdateEmail update:
                Out.Email = update.Email;
                break;

            case Input.UpdatePassword update:
                Out.Password = update.Password;
                break;

            case Input.Login:
                _ = LoginAsync();
                break;

            case Input.ForgotPassword:
                Fx.OnNext(new Effect.NavigateToForgotPassword());
                break;
        }
    }

    private async Task LoginAsync()
    {
        Out.IsLoading = true;
        Out.Error = null;

        try
        {
            var result = await _authService.LoginAsync(Out.Email, Out.Password);

            if (result.IsSuccess)
            {
                Fx.OnNext(new Effect.NavigateToHome());
            }
            else
            {
                Out.Error = result.Error;
                Fx.OnNext(new Effect.ShowError(result.Error));
            }
        }
        catch (Exception ex)
        {
            Out.Error = "An unexpected error occurred";
            Fx.OnNext(new Effect.ShowError(ex.Message));
        }
        finally
        {
            Out.IsLoading = false;
        }
    }
}
```

### LoginPage.xaml

```xml
<Page
    x:Class="Arcana.App.Views.LoginPage"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:controls="using:Arcana.App.Controls">

    <Grid Padding="40" HorizontalAlignment="Center" VerticalAlignment="Center">
        <StackPanel Width="400" Spacing="16">

            <!-- Logo and Title -->
            <TextBlock
                Text="Welcome Back"
                Style="{StaticResource TitleLargeTextBlockStyle}"
                HorizontalAlignment="Center" />

            <!-- Error Message -->
            <InfoBar
                x:Name="ErrorInfoBar"
                IsOpen="{x:Bind ViewModel.Out.Error, Mode=OneWay, Converter={StaticResource NotNullToBoolConverter}}"
                Severity="Error"
                Title="Login Failed"
                Message="{x:Bind ViewModel.Out.Error, Mode=OneWay}" />

            <!-- Email Input -->
            <TextBox
                Header="Email"
                PlaceholderText="Enter your email"
                Text="{x:Bind ViewModel.Out.Email, Mode=TwoWay, UpdateSourceTrigger=PropertyChanged}"
                TextChanged="OnEmailTextChanged"
                IsEnabled="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay, Converter={StaticResource InverseBoolConverter}}" />

            <!-- Password Input -->
            <PasswordBox
                Header="Password"
                PlaceholderText="Enter your password"
                Password="{x:Bind ViewModel.Out.Password, Mode=TwoWay}"
                PasswordChanged="OnPasswordChanged"
                IsEnabled="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay, Converter={StaticResource InverseBoolConverter}}" />

            <!-- Forgot Password Link -->
            <HyperlinkButton
                Content="Forgot password?"
                Click="OnForgotPasswordClick"
                HorizontalAlignment="Right" />

            <!-- Login Button -->
            <Button
                Content="Sign In"
                Style="{StaticResource AccentButtonStyle}"
                HorizontalAlignment="Stretch"
                Click="OnLoginClick"
                IsEnabled="{x:Bind ViewModel.Out.CanLogin, Mode=OneWay}" />

            <!-- Loading Indicator -->
            <ProgressRing
                IsActive="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay}"
                Visibility="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay}" />

        </StackPanel>
    </Grid>
</Page>
```

### LoginPage.xaml.cs

```csharp
public sealed partial class LoginPage : Page
{
    public LoginViewModel ViewModel { get; }

    public LoginPage()
    {
        ViewModel = App.GetService<LoginViewModel>();
        InitializeComponent();
        DataContext = ViewModel;

        // Subscribe to effects
        ViewModel.Fx.Subscribe(OnEffect);
    }

    private void OnEffect(LoginViewModel.Effect effect)
    {
        switch (effect)
        {
            case LoginViewModel.Effect.NavigateToHome:
                App.GetService<INavGraph>().ToHome();
                break;

            case LoginViewModel.Effect.NavigateToForgotPassword:
                App.GetService<INavGraph>().ToForgotPassword();
                break;

            case LoginViewModel.Effect.ShowError error:
                // InfoBar handles display via binding
                break;
        }
    }

    private void OnEmailTextChanged(object sender, TextChangedEventArgs e)
    {
        ViewModel.OnInput(new LoginViewModel.Input.UpdateEmail(((TextBox)sender).Text));
    }

    private void OnPasswordChanged(object sender, RoutedEventArgs e)
    {
        ViewModel.OnInput(new LoginViewModel.Input.UpdatePassword(((PasswordBox)sender).Password));
    }

    private void OnLoginClick(object sender, RoutedEventArgs e)
    {
        ViewModel.OnInput(new LoginViewModel.Input.Login());
    }

    private void OnForgotPasswordClick(object sender, RoutedEventArgs e)
    {
        ViewModel.OnInput(new LoginViewModel.Input.ForgotPassword());
    }
}
```

### AuthService

```csharp
public class AuthService : IAuthService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly IPasswordHasher _passwordHasher;
    private readonly ITokenService _tokenService;

    public AuthService(
        IUnitOfWork unitOfWork,
        IPasswordHasher passwordHasher,
        ITokenService tokenService)
    {
        _unitOfWork = unitOfWork;
        _passwordHasher = passwordHasher;
        _tokenService = tokenService;
    }

    public async Task<AuthResult> LoginAsync(string email, string password)
    {
        var user = await _unitOfWork.Users
            .FindAsync(u => u.Email == email)
            .ContinueWith(t => t.Result.FirstOrDefault());

        if (user == null)
        {
            return AuthResult.Failure("Invalid email or password");
        }

        if (!_passwordHasher.VerifyPassword(password, user.PasswordHash))
        {
            return AuthResult.Failure("Invalid email or password");
        }

        var token = _tokenService.GenerateToken(user);
        return AuthResult.Success(token, user);
    }

    public async Task LogoutAsync()
    {
        await _tokenService.RevokeCurrentTokenAsync();
    }
}

public record AuthResult
{
    public bool IsSuccess { get; init; }
    public string? Error { get; init; }
    public string? Token { get; init; }
    public User? User { get; init; }

    public static AuthResult Success(string token, User user) =>
        new() { IsSuccess = true, Token = token, User = user };

    public static AuthResult Failure(string error) =>
        new() { IsSuccess = false, Error = error };
}
```

---

## Example 2: Product List with Search, Filter, and Pagination

### ProductListViewModel

```csharp
public partial class ProductListViewModel : ObservableObject
{
    // MARK: - Input
    public sealed class Input
    {
        public record Load;
        public record Search(string Query);
        public record FilterByCategory(string? CategoryId);
        public record SortBy(SortOption Option);
        public record LoadMore;
        public record Refresh;
        public record SelectProduct(string ProductId);
    }

    // MARK: - Output
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private ObservableCollection<ProductItemViewModel> _products = new();

        [ObservableProperty]
        private string _searchQuery = string.Empty;

        [ObservableProperty]
        private string? _selectedCategoryId;

        [ObservableProperty]
        private SortOption _sortOption = SortOption.NameAsc;

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private bool _isRefreshing;

        [ObservableProperty]
        private bool _hasMore = true;

        [ObservableProperty]
        private int _totalCount;

        [ObservableProperty]
        private string? _error;

        [ObservableProperty]
        private ObservableCollection<Category> _categories = new();
    }

    // MARK: - Effect
    public sealed class Effect
    {
        public record NavigateToDetail(string ProductId);
        public record ShowError(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IProductService _productService;
    private readonly ICategoryService _categoryService;
    private int _currentPage = 1;
    private const int PageSize = 20;

    public ProductListViewModel(IProductService productService, ICategoryService categoryService)
    {
        _productService = productService;
        _categoryService = categoryService;
    }

    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.Load:
                _ = LoadInitialAsync();
                break;

            case Input.Search search:
                Out.SearchQuery = search.Query;
                _ = SearchAsync();
                break;

            case Input.FilterByCategory filter:
                Out.SelectedCategoryId = filter.CategoryId;
                _ = SearchAsync();
                break;

            case Input.SortBy sort:
                Out.SortOption = sort.Option;
                _ = SearchAsync();
                break;

            case Input.LoadMore:
                if (Out.HasMore && !Out.IsLoading)
                {
                    _ = LoadMoreAsync();
                }
                break;

            case Input.Refresh:
                _ = RefreshAsync();
                break;

            case Input.SelectProduct select:
                Fx.OnNext(new Effect.NavigateToDetail(select.ProductId));
                break;
        }
    }

    private async Task LoadInitialAsync()
    {
        Out.IsLoading = true;
        Out.Error = null;

        try
        {
            // Load categories for filter
            var categories = await _categoryService.GetAllAsync();
            Out.Categories = new ObservableCollection<Category>(categories);

            // Load first page of products
            await SearchAsync();
        }
        catch (Exception ex)
        {
            Out.Error = ex.Message;
            Fx.OnNext(new Effect.ShowError(ex.Message));
        }
        finally
        {
            Out.IsLoading = false;
        }
    }

    private async Task SearchAsync()
    {
        Out.IsLoading = true;
        _currentPage = 1;

        try
        {
            var result = await _productService.SearchAsync(new ProductSearchRequest
            {
                Query = Out.SearchQuery,
                CategoryId = Out.SelectedCategoryId,
                SortBy = Out.SortOption,
                Page = _currentPage,
                PageSize = PageSize
            });

            Out.Products = new ObservableCollection<ProductItemViewModel>(
                result.Items.Select(p => new ProductItemViewModel(p)));
            Out.TotalCount = result.TotalCount;
            Out.HasMore = result.HasMore;
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

    private async Task LoadMoreAsync()
    {
        Out.IsLoading = true;
        _currentPage++;

        try
        {
            var result = await _productService.SearchAsync(new ProductSearchRequest
            {
                Query = Out.SearchQuery,
                CategoryId = Out.SelectedCategoryId,
                SortBy = Out.SortOption,
                Page = _currentPage,
                PageSize = PageSize
            });

            foreach (var product in result.Items)
            {
                Out.Products.Add(new ProductItemViewModel(product));
            }

            Out.HasMore = result.HasMore;
        }
        catch (Exception ex)
        {
            Out.Error = ex.Message;
            _currentPage--;
        }
        finally
        {
            Out.IsLoading = false;
        }
    }

    private async Task RefreshAsync()
    {
        Out.IsRefreshing = true;
        _currentPage = 1;

        try
        {
            var result = await _productService.SearchAsync(new ProductSearchRequest
            {
                Query = Out.SearchQuery,
                CategoryId = Out.SelectedCategoryId,
                SortBy = Out.SortOption,
                Page = _currentPage,
                PageSize = PageSize
            });

            Out.Products = new ObservableCollection<ProductItemViewModel>(
                result.Items.Select(p => new ProductItemViewModel(p)));
            Out.TotalCount = result.TotalCount;
            Out.HasMore = result.HasMore;
        }
        catch (Exception ex)
        {
            Out.Error = ex.Message;
        }
        finally
        {
            Out.IsRefreshing = false;
        }
    }
}

public enum SortOption
{
    NameAsc,
    NameDesc,
    PriceAsc,
    PriceDesc,
    Newest,
    Oldest
}
```

### ProductListPage.xaml

```xml
<Page
    x:Class="Arcana.App.Views.ProductListPage"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:controls="using:CommunityToolkit.WinUI.UI.Controls">

    <Grid>
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto" />
            <RowDefinition Height="Auto" />
            <RowDefinition Height="*" />
        </Grid.RowDefinitions>

        <!-- Search and Filter Bar -->
        <Grid Grid.Row="0" Padding="16" ColumnSpacing="16">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*" />
                <ColumnDefinition Width="200" />
                <ColumnDefinition Width="150" />
            </Grid.ColumnDefinitions>

            <AutoSuggestBox
                Grid.Column="0"
                QueryIcon="Find"
                PlaceholderText="Search products..."
                Text="{x:Bind ViewModel.Out.SearchQuery, Mode=TwoWay}"
                QuerySubmitted="OnSearchQuerySubmitted" />

            <ComboBox
                Grid.Column="1"
                PlaceholderText="Category"
                ItemsSource="{x:Bind ViewModel.Out.Categories, Mode=OneWay}"
                DisplayMemberPath="Name"
                SelectedValuePath="Id"
                SelectedValue="{x:Bind ViewModel.Out.SelectedCategoryId, Mode=TwoWay}"
                SelectionChanged="OnCategorySelectionChanged" />

            <ComboBox
                Grid.Column="2"
                PlaceholderText="Sort by"
                SelectedIndex="0"
                SelectionChanged="OnSortSelectionChanged">
                <ComboBoxItem Content="Name (A-Z)" Tag="NameAsc" />
                <ComboBoxItem Content="Name (Z-A)" Tag="NameDesc" />
                <ComboBoxItem Content="Price (Low-High)" Tag="PriceAsc" />
                <ComboBoxItem Content="Price (High-Low)" Tag="PriceDesc" />
                <ComboBoxItem Content="Newest" Tag="Newest" />
                <ComboBoxItem Content="Oldest" Tag="Oldest" />
            </ComboBox>
        </Grid>

        <!-- Results Count -->
        <TextBlock
            Grid.Row="1"
            Padding="16,0"
            Text="{x:Bind ViewModel.Out.TotalCount, Mode=OneWay, Converter={StaticResource CountToTextConverter}}"
            Style="{StaticResource CaptionTextBlockStyle}" />

        <!-- Product List -->
        <RefreshContainer
            Grid.Row="2"
            RefreshRequested="OnRefreshRequested">
            <ListView
                ItemsSource="{x:Bind ViewModel.Out.Products, Mode=OneWay}"
                SelectionMode="None"
                IsItemClickEnabled="True"
                ItemClick="OnProductClick">

                <ListView.ItemTemplate>
                    <DataTemplate x:DataType="viewmodels:ProductItemViewModel">
                        <Grid Padding="16" ColumnSpacing="16">
                            <Grid.ColumnDefinitions>
                                <ColumnDefinition Width="80" />
                                <ColumnDefinition Width="*" />
                                <ColumnDefinition Width="Auto" />
                            </Grid.ColumnDefinitions>

                            <Image
                                Grid.Column="0"
                                Source="{x:Bind ImageUrl}"
                                Width="80"
                                Height="80"
                                Stretch="UniformToFill" />

                            <StackPanel Grid.Column="1" VerticalAlignment="Center">
                                <TextBlock
                                    Text="{x:Bind Name}"
                                    Style="{StaticResource SubtitleTextBlockStyle}" />
                                <TextBlock
                                    Text="{x:Bind Category}"
                                    Style="{StaticResource CaptionTextBlockStyle}"
                                    Foreground="{ThemeResource TextFillColorSecondaryBrush}" />
                            </StackPanel>

                            <TextBlock
                                Grid.Column="2"
                                Text="{x:Bind FormattedPrice}"
                                Style="{StaticResource BodyStrongTextBlockStyle}"
                                VerticalAlignment="Center" />
                        </Grid>
                    </DataTemplate>
                </ListView.ItemTemplate>

                <!-- Load More Footer -->
                <ListView.Footer>
                    <StackPanel HorizontalAlignment="Center" Padding="16">
                        <Button
                            Content="Load More"
                            Click="OnLoadMoreClick"
                            Visibility="{x:Bind ViewModel.Out.HasMore, Mode=OneWay}" />
                        <ProgressRing
                            IsActive="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay}"
                            Visibility="{x:Bind ViewModel.Out.IsLoading, Mode=OneWay}" />
                    </StackPanel>
                </ListView.Footer>
            </ListView>
        </RefreshContainer>
    </Grid>
</Page>
```

---

## Example 3: Form Validation with Unit of Work

### EditProductViewModel

```csharp
public partial class EditProductViewModel : ObservableObject
{
    // MARK: - Input
    public sealed class Input
    {
        public record Load(string? ProductId);
        public record UpdateName(string Name);
        public record UpdateDescription(string Description);
        public record UpdatePrice(string Price);
        public record UpdateCategory(string CategoryId);
        public record AddImage(StorageFile File);
        public record RemoveImage(int Index);
        public record Save;
        public record Cancel;
    }

    // MARK: - Output
    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private string? _productId;

        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private string? _nameError;

        [ObservableProperty]
        private string _description = string.Empty;

        [ObservableProperty]
        private string _price = string.Empty;

        [ObservableProperty]
        private string? _priceError;

        [ObservableProperty]
        private string? _selectedCategoryId;

        [ObservableProperty]
        private string? _categoryError;

        [ObservableProperty]
        private ObservableCollection<string> _imageUrls = new();

        [ObservableProperty]
        private ObservableCollection<Category> _categories = new();

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private bool _isSaving;

        [ObservableProperty]
        private bool _isValid;

        [ObservableProperty]
        private bool _isDirty;

        public bool IsEditMode => !string.IsNullOrEmpty(ProductId);
        public string Title => IsEditMode ? "Edit Product" : "New Product";
    }

    // MARK: - Effect
    public sealed class Effect
    {
        public record NavigateBack;
        public record ShowSaveSuccess;
        public record ShowError(string Message);
        public record ConfirmDiscard;
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IUnitOfWork _unitOfWork;
    private readonly ICategoryService _categoryService;
    private readonly IImageService _imageService;

    public EditProductViewModel(
        IUnitOfWork unitOfWork,
        ICategoryService categoryService,
        IImageService imageService)
    {
        _unitOfWork = unitOfWork;
        _categoryService = categoryService;
        _imageService = imageService;
    }

    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.Load load:
                _ = LoadAsync(load.ProductId);
                break;

            case Input.UpdateName update:
                Out.Name = update.Name;
                Out.IsDirty = true;
                ValidateName();
                break;

            case Input.UpdateDescription update:
                Out.Description = update.Description;
                Out.IsDirty = true;
                break;

            case Input.UpdatePrice update:
                Out.Price = update.Price;
                Out.IsDirty = true;
                ValidatePrice();
                break;

            case Input.UpdateCategory update:
                Out.SelectedCategoryId = update.CategoryId;
                Out.IsDirty = true;
                ValidateCategory();
                break;

            case Input.AddImage add:
                _ = AddImageAsync(add.File);
                break;

            case Input.RemoveImage remove:
                Out.ImageUrls.RemoveAt(remove.Index);
                Out.IsDirty = true;
                break;

            case Input.Save:
                if (Out.IsValid)
                {
                    _ = SaveAsync();
                }
                break;

            case Input.Cancel:
                if (Out.IsDirty)
                {
                    Fx.OnNext(new Effect.ConfirmDiscard());
                }
                else
                {
                    Fx.OnNext(new Effect.NavigateBack());
                }
                break;
        }
    }

    private async Task LoadAsync(string? productId)
    {
        Out.IsLoading = true;

        try
        {
            // Load categories
            var categories = await _categoryService.GetAllAsync();
            Out.Categories = new ObservableCollection<Category>(categories);

            // Load product if editing
            if (!string.IsNullOrEmpty(productId))
            {
                Out.ProductId = productId;
                var product = await _unitOfWork.Products.GetByIdAsync(productId);

                if (product != null)
                {
                    Out.Name = product.Name;
                    Out.Description = product.Description;
                    Out.Price = product.Price.ToString("F2");
                    Out.SelectedCategoryId = product.CategoryId;
                    Out.ImageUrls = new ObservableCollection<string>(product.ImageUrls);
                }
            }

            Out.IsDirty = false;
            ValidateAll();
        }
        catch (Exception ex)
        {
            Fx.OnNext(new Effect.ShowError(ex.Message));
        }
        finally
        {
            Out.IsLoading = false;
        }
    }

    private async Task SaveAsync()
    {
        Out.IsSaving = true;

        try
        {
            await _unitOfWork.BeginTransactionAsync();

            var product = Out.IsEditMode
                ? await _unitOfWork.Products.GetByIdAsync(Out.ProductId!)
                : new Product { Id = Guid.NewGuid().ToString() };

            if (product == null)
            {
                throw new InvalidOperationException("Product not found");
            }

            product.Name = Out.Name;
            product.Description = Out.Description;
            product.Price = decimal.Parse(Out.Price);
            product.CategoryId = Out.SelectedCategoryId!;
            product.ImageUrls = Out.ImageUrls.ToList();

            if (Out.IsEditMode)
            {
                await _unitOfWork.Products.UpdateAsync(product);
            }
            else
            {
                await _unitOfWork.Products.AddAsync(product);
            }

            await _unitOfWork.SaveChangesAsync();
            await _unitOfWork.CommitAsync();

            Fx.OnNext(new Effect.ShowSaveSuccess());
            Fx.OnNext(new Effect.NavigateBack());
        }
        catch (Exception ex)
        {
            await _unitOfWork.RollbackAsync();
            Fx.OnNext(new Effect.ShowError(ex.Message));
        }
        finally
        {
            Out.IsSaving = false;
        }
    }

    private async Task AddImageAsync(StorageFile file)
    {
        try
        {
            var url = await _imageService.UploadAsync(file);
            Out.ImageUrls.Add(url);
            Out.IsDirty = true;
        }
        catch (Exception ex)
        {
            Fx.OnNext(new Effect.ShowError($"Failed to upload image: {ex.Message}"));
        }
    }

    private void ValidateName()
    {
        Out.NameError = string.IsNullOrWhiteSpace(Out.Name)
            ? "Name is required"
            : Out.Name.Length < 3
                ? "Name must be at least 3 characters"
                : null;
        UpdateIsValid();
    }

    private void ValidatePrice()
    {
        if (string.IsNullOrWhiteSpace(Out.Price))
        {
            Out.PriceError = "Price is required";
        }
        else if (!decimal.TryParse(Out.Price, out var price))
        {
            Out.PriceError = "Invalid price format";
        }
        else if (price <= 0)
        {
            Out.PriceError = "Price must be greater than 0";
        }
        else
        {
            Out.PriceError = null;
        }
        UpdateIsValid();
    }

    private void ValidateCategory()
    {
        Out.CategoryError = string.IsNullOrEmpty(Out.SelectedCategoryId)
            ? "Category is required"
            : null;
        UpdateIsValid();
    }

    private void ValidateAll()
    {
        ValidateName();
        ValidatePrice();
        ValidateCategory();
    }

    private void UpdateIsValid()
    {
        Out.IsValid = Out.NameError == null &&
                      Out.PriceError == null &&
                      Out.CategoryError == null;
    }
}
```

---

## Example 4: Plugin Development - Analytics Module

### AnalyticsPlugin

```csharp
[PluginManifest(
    Key = "analytics-module",
    Name = "Analytics Module",
    Version = "1.0.0",
    Type = PluginType.Analytics,
    Description = "Provides usage analytics and reporting")]
public class AnalyticsPlugin : IArcanaPlugin
{
    public string Key => "analytics-module";
    public string Name => "Analytics Module";
    public string Version => "1.0.0";

    public PluginManifest Manifest { get; } = new()
    {
        Key = "analytics-module",
        Name = "Analytics Module",
        Type = PluginType.Analytics,
        ActivationEvents = new[] { "onStartup" }
    };

    private IPluginContext? _context;
    private IDisposable? _eventSubscription;
    private readonly List<AnalyticsEvent> _eventBuffer = new();
    private Timer? _flushTimer;

    public async Task OnActivateAsync(IPluginContext context)
    {
        _context = context;
        var logger = context.LoggerFactory.CreateLogger<AnalyticsPlugin>();
        logger.LogInformation("Analytics plugin activating");

        // Register views
        context.Navigation.RegisterView("analytics-dashboard", typeof(AnalyticsDashboardView));
        context.Navigation.RegisterView("analytics-reports", typeof(AnalyticsReportsView));

        // Register menu item
        context.EventAggregator.Publish(new RegisterMenuItemEvent
        {
            MenuId = "tools",
            Item = new MenuItem("Analytics Dashboard", "analytics.show")
        });

        // Subscribe to all events for tracking
        _eventSubscription = context.EventAggregator
            .GetEvent<IApplicationEvent>()
            .Subscribe(OnApplicationEvent);

        // Set up periodic flush
        _flushTimer = new Timer(FlushEvents, null, TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));

        // Register command handlers
        context.MessageBus.Subscribe<ShowAnalyticsCommand>(OnShowAnalytics);

        await Task.CompletedTask;
    }

    public async Task OnDeactivateAsync()
    {
        _eventSubscription?.Dispose();
        _flushTimer?.Dispose();

        // Flush remaining events
        await FlushEventsAsync();

        _context = null;
    }

    private void OnApplicationEvent(IApplicationEvent appEvent)
    {
        var analyticsEvent = new AnalyticsEvent
        {
            EventType = appEvent.GetType().Name,
            Timestamp = DateTime.UtcNow,
            Properties = ExtractProperties(appEvent)
        };

        lock (_eventBuffer)
        {
            _eventBuffer.Add(analyticsEvent);
        }
    }

    private void FlushEvents(object? state)
    {
        _ = FlushEventsAsync();
    }

    private async Task FlushEventsAsync()
    {
        List<AnalyticsEvent> eventsToFlush;

        lock (_eventBuffer)
        {
            if (_eventBuffer.Count == 0) return;
            eventsToFlush = new List<AnalyticsEvent>(_eventBuffer);
            _eventBuffer.Clear();
        }

        try
        {
            var storage = _context?.Storage;
            if (storage != null)
            {
                await storage.SaveAsync("events", eventsToFlush);
            }
        }
        catch (Exception ex)
        {
            var logger = _context?.LoggerFactory.CreateLogger<AnalyticsPlugin>();
            logger?.LogError(ex, "Failed to flush analytics events");
        }
    }

    private void OnShowAnalytics(ShowAnalyticsCommand command)
    {
        _context?.Navigation.ToPluginView("analytics-dashboard");
    }

    private Dictionary<string, object> ExtractProperties(IApplicationEvent appEvent)
    {
        var properties = new Dictionary<string, object>();
        var type = appEvent.GetType();

        foreach (var prop in type.GetProperties())
        {
            var value = prop.GetValue(appEvent);
            if (value != null)
            {
                properties[prop.Name] = value;
            }
        }

        return properties;
    }
}

// Analytics event model
public class AnalyticsEvent
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string EventType { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public Dictionary<string, object> Properties { get; set; } = new();
}

// Commands
public record ShowAnalyticsCommand;
public record TrackEventCommand(string EventName, Dictionary<string, object>? Properties = null);
```

### AnalyticsDashboardViewModel

```csharp
public partial class AnalyticsDashboardViewModel : ObservableObject
{
    public sealed class Input
    {
        public record Load;
        public record SelectDateRange(DateTime Start, DateTime End);
        public record ExportReport(ReportFormat Format);
    }

    public sealed partial class Output : ObservableObject
    {
        [ObservableProperty]
        private int _totalEvents;

        [ObservableProperty]
        private int _uniqueUsers;

        [ObservableProperty]
        private ObservableCollection<EventSummary> _topEvents = new();

        [ObservableProperty]
        private ObservableCollection<DailyStats> _dailyStats = new();

        [ObservableProperty]
        private DateTime _startDate = DateTime.Today.AddDays(-30);

        [ObservableProperty]
        private DateTime _endDate = DateTime.Today;

        [ObservableProperty]
        private bool _isLoading;
    }

    public sealed class Effect
    {
        public record ExportComplete(string FilePath);
        public record ShowError(string Message);
    }

    public Output Out { get; } = new();
    public Subject<Effect> Fx { get; } = new();

    private readonly IPluginStorage _storage;

    public AnalyticsDashboardViewModel(IPluginStorage storage)
    {
        _storage = storage;
    }

    public void OnInput(object input)
    {
        switch (input)
        {
            case Input.Load:
                _ = LoadAsync();
                break;

            case Input.SelectDateRange range:
                Out.StartDate = range.Start;
                Out.EndDate = range.End;
                _ = LoadAsync();
                break;

            case Input.ExportReport export:
                _ = ExportAsync(export.Format);
                break;
        }
    }

    private async Task LoadAsync()
    {
        Out.IsLoading = true;

        try
        {
            var events = await _storage.LoadAsync<List<AnalyticsEvent>>("events") ?? new();

            var filteredEvents = events
                .Where(e => e.Timestamp >= Out.StartDate && e.Timestamp <= Out.EndDate)
                .ToList();

            Out.TotalEvents = filteredEvents.Count;

            Out.TopEvents = new ObservableCollection<EventSummary>(
                filteredEvents
                    .GroupBy(e => e.EventType)
                    .Select(g => new EventSummary { EventType = g.Key, Count = g.Count() })
                    .OrderByDescending(s => s.Count)
                    .Take(10));

            Out.DailyStats = new ObservableCollection<DailyStats>(
                filteredEvents
                    .GroupBy(e => e.Timestamp.Date)
                    .Select(g => new DailyStats { Date = g.Key, EventCount = g.Count() })
                    .OrderBy(s => s.Date));
        }
        catch (Exception ex)
        {
            Fx.OnNext(new Effect.ShowError(ex.Message));
        }
        finally
        {
            Out.IsLoading = false;
        }
    }

    private async Task ExportAsync(ReportFormat format)
    {
        // Export implementation
    }
}

public class EventSummary
{
    public string EventType { get; set; } = string.Empty;
    public int Count { get; set; }
}

public class DailyStats
{
    public DateTime Date { get; set; }
    public int EventCount { get; set; }
}

public enum ReportFormat
{
    Csv,
    Excel,
    Pdf
}
```

---

## Example 5: CRDT Offline Sync Implementation

### SyncableEntity Base

```csharp
public abstract class SyncableEntity : Entity, ISyncableEntity
{
    public VectorClock VectorClock { get; set; } = new();
    public SyncStatus SyncStatus { get; set; } = SyncStatus.Synced;

    private readonly Dictionary<string, FieldMetadata> _fieldMetadata = new();

    public FieldMetadata GetFieldMetadata(string fieldName)
    {
        if (!_fieldMetadata.TryGetValue(fieldName, out var metadata))
        {
            metadata = new FieldMetadata { FieldName = fieldName };
            _fieldMetadata[fieldName] = metadata;
        }
        return metadata;
    }

    protected void SetFieldWithMetadata<T>(ref T field, T value, string fieldName)
    {
        if (!EqualityComparer<T>.Default.Equals(field, value))
        {
            field = value;
            _fieldMetadata[fieldName] = new FieldMetadata
            {
                FieldName = fieldName,
                UpdatedAt = DateTime.UtcNow
            };
        }
    }
}

public class FieldMetadata
{
    public string FieldName { get; set; } = string.Empty;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
```

### SyncService

```csharp
public class SyncService : ISyncService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly IRemoteSyncApi _remoteSyncApi;
    private readonly CrdtSyncManager _crdtManager;
    private readonly IConnectivityService _connectivityService;
    private readonly IEventAggregator _eventAggregator;

    public SyncService(
        IUnitOfWork unitOfWork,
        IRemoteSyncApi remoteSyncApi,
        string nodeId,
        IConnectivityService connectivityService,
        IEventAggregator eventAggregator)
    {
        _unitOfWork = unitOfWork;
        _remoteSyncApi = remoteSyncApi;
        _crdtManager = new CrdtSyncManager(unitOfWork, nodeId, ConflictStrategy.FieldLevelMerge);
        _connectivityService = connectivityService;
        _eventAggregator = eventAggregator;
    }

    public async Task<SyncResult> SyncAsync<T>() where T : class, ISyncableEntity
    {
        var result = new SyncResult();

        if (!_connectivityService.IsConnected)
        {
            result.Status = SyncStatus.Offline;
            return result;
        }

        try
        {
            // Get pending local changes
            var pendingEntities = await GetPendingEntitiesAsync<T>();

            // Push local changes
            foreach (var entity in pendingEntities)
            {
                var pushResult = await _remoteSyncApi.PushAsync(entity);
                if (pushResult.IsSuccess)
                {
                    entity.SyncStatus = SyncStatus.Synced;
                    await _unitOfWork.SaveChangesAsync();
                    result.PushedCount++;
                }
                else if (pushResult.HasConflict)
                {
                    // Handle conflict
                    var remoteEntity = pushResult.ConflictingEntity as T;
                    if (remoteEntity != null)
                    {
                        var resolved = await _crdtManager.ApplyChangeAsync(entity, remoteEntity);
                        await SaveResolvedEntityAsync(resolved);
                        result.ConflictsResolved++;
                    }
                }
            }

            // Pull remote changes
            var lastSyncTime = await GetLastSyncTimeAsync<T>();
            var remoteChanges = await _remoteSyncApi.PullAsync<T>(lastSyncTime);

            foreach (var remoteEntity in remoteChanges)
            {
                var localEntity = await _unitOfWork.GetRepository<T>().GetByIdAsync(remoteEntity.Id);

                if (localEntity == null)
                {
                    // New entity from remote
                    await _unitOfWork.GetRepository<T>().AddAsync(remoteEntity);
                    result.PulledCount++;
                }
                else
                {
                    // Merge with local
                    var resolved = await _crdtManager.ApplyChangeAsync(localEntity, remoteEntity);
                    await SaveResolvedEntityAsync(resolved);
                    result.MergedCount++;
                }
            }

            await _unitOfWork.SaveChangesAsync();
            await UpdateLastSyncTimeAsync<T>();

            result.Status = SyncStatus.Synced;
            _eventAggregator.Publish(new SyncCompletedEvent(result));
        }
        catch (Exception ex)
        {
            result.Status = SyncStatus.Failed;
            result.Error = ex.Message;
            _eventAggregator.Publish(new SyncFailedEvent(ex));
        }

        return result;
    }

    private async Task<List<T>> GetPendingEntitiesAsync<T>() where T : class, ISyncableEntity
    {
        return (await _unitOfWork.GetRepository<T>()
            .FindAsync(e => e.SyncStatus == SyncStatus.Pending))
            .ToList();
    }

    private async Task<DateTime> GetLastSyncTimeAsync<T>()
    {
        var key = $"LastSync_{typeof(T).Name}";
        var settings = App.GetService<ISettingsService>();
        return await settings.GetAsync<DateTime>(key);
    }

    private async Task UpdateLastSyncTimeAsync<T>()
    {
        var key = $"LastSync_{typeof(T).Name}";
        var settings = App.GetService<ISettingsService>();
        await settings.SetAsync(key, DateTime.UtcNow);
    }

    private async Task SaveResolvedEntityAsync<T>(T entity) where T : class, ISyncableEntity
    {
        entity.SyncStatus = SyncStatus.Synced;
        await _unitOfWork.GetRepository<T>().UpdateAsync(entity);
    }
}

public class SyncResult
{
    public SyncStatus Status { get; set; }
    public int PushedCount { get; set; }
    public int PulledCount { get; set; }
    public int MergedCount { get; set; }
    public int ConflictsResolved { get; set; }
    public string? Error { get; set; }
}

// Sync events
public record SyncCompletedEvent(SyncResult Result);
public record SyncFailedEvent(Exception Error);
```

### Background Sync Worker

```csharp
public class BackgroundSyncWorker : IHostedService
{
    private readonly ISyncService _syncService;
    private readonly IConnectivityService _connectivityService;
    private readonly ILogger<BackgroundSyncWorker> _logger;
    private Timer? _timer;
    private readonly TimeSpan _syncInterval = TimeSpan.FromMinutes(5);

    public BackgroundSyncWorker(
        ISyncService syncService,
        IConnectivityService connectivityService,
        ILogger<BackgroundSyncWorker> logger)
    {
        _syncService = syncService;
        _connectivityService = connectivityService;
        _logger = logger;
    }

    public Task StartAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Background sync worker starting");

        _connectivityService.ConnectivityChanged += OnConnectivityChanged;
        _timer = new Timer(DoSync, null, TimeSpan.Zero, _syncInterval);

        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Background sync worker stopping");

        _connectivityService.ConnectivityChanged -= OnConnectivityChanged;
        _timer?.Change(Timeout.Infinite, 0);

        return Task.CompletedTask;
    }

    private async void OnConnectivityChanged(object? sender, bool isConnected)
    {
        if (isConnected)
        {
            _logger.LogInformation("Connection restored, triggering sync");
            await SyncAllAsync();
        }
    }

    private async void DoSync(object? state)
    {
        await SyncAllAsync();
    }

    private async Task SyncAllAsync()
    {
        try
        {
            // Sync all entity types
            await _syncService.SyncAsync<User>();
            await _syncService.SyncAsync<Product>();
            await _syncService.SyncAsync<Order>();

            _logger.LogInformation("Background sync completed");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Background sync failed");
        }
    }
}
```
