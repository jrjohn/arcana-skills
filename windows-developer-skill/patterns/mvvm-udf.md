# MVVM UDF (Unidirectional Data Flow) Pattern

## Overview

The MVVM UDF pattern provides a clear, unidirectional data flow for ViewModels in WinUI 3.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ViewModel                                 │
│  ┌─────────┐    ┌──────────────┐    ┌──────────┐               │
│  │  Input  │ →  │   Process    │ →  │  Output  │               │
│  │ (Intent)│    │  (Business)  │    │ (State)  │               │
│  └─────────┘    └──────────────┘    └──────────┘               │
│        ↑                                  │                     │
│        │                                  ↓                     │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                      View                            │       │
│  │   User Action → Input    |    Output → UI           │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Template

```csharp
public partial class FeatureViewModel : ObservableObject
{
    // === INPUT: Intent records ===
    public abstract record Intent;
    public record Load : Intent;
    public record Refresh : Intent;
    public record ItemClicked(string Id) : Intent;
    public record Retry : Intent;

    // === OUTPUT: Observable properties ===
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string? _error;
    [ObservableProperty] private List<Item> _items = new();

    // === EFFECT: One-time events ===
    public abstract record Effect;
    public record NavigateToDetail(string Id) : Effect;
    public record ShowToast(string Message) : Effect;

    public Subject<Effect> Fx { get; } = new();

    private readonly IItemRepository _repository;

    public FeatureViewModel(IItemRepository repository)
    {
        _repository = repository;
        OnIntent(new Load());
    }

    public void OnIntent(Intent intent)
    {
        switch (intent)
        {
            case Load: LoadData(); break;
            case Refresh: RefreshData(); break;
            case ItemClicked i: HandleItemClick(i.Id); break;
            case Retry: LoadData(); break;
        }
    }

    private async void LoadData()
    {
        IsLoading = true;
        Error = null;
        try
        {
            Items = await _repository.GetAllAsync();
        }
        catch (Exception ex)
        {
            Error = ex.Message;
        }
        finally
        {
            IsLoading = false;
        }
    }

    private void HandleItemClick(string id)
    {
        Fx.OnNext(new NavigateToDetail(id));
    }
}
```

## View Integration

```csharp
public sealed partial class FeaturePage : Page
{
    private readonly FeatureViewModel _viewModel;
    private readonly INavGraph _navGraph;

    public FeaturePage(FeatureViewModel viewModel, INavGraph navGraph)
    {
        _viewModel = viewModel;
        _navGraph = navGraph;
        DataContext = _viewModel;
        InitializeComponent();

        _viewModel.Fx.Subscribe(HandleEffect);
    }

    private void HandleEffect(FeatureViewModel.Effect effect)
    {
        switch (effect)
        {
            case FeatureViewModel.NavigateToDetail e:
                _navGraph.ToItemDetail(e.Id);
                break;
            case FeatureViewModel.ShowToast e:
                // Show toast
                break;
        }
    }
}
```
