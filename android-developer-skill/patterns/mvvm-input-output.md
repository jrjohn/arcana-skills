# MVVM Input/Output Pattern

## Overview

The Input/Output pattern provides a clear, unidirectional data flow for ViewModels.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ViewModel                                 │
│  ┌─────────┐    ┌──────────────┐    ┌──────────┐               │
│  │  Input  │ →  │   Process    │ →  │  Output  │               │
│  │ (Event) │    │  (Business)  │    │ (State)  │               │
│  └─────────┘    └──────────────┘    └──────────┘               │
│        ↑                                  │                     │
│        │                                  ↓                     │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                      Screen                          │       │
│  │   User Action → Input    |    Output → UI State     │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Template

```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: FeatureRepository
) : ViewModel() {

    // === INPUT: User actions ===
    sealed class Input {
        object Load : Input()
        object Refresh : Input()
        data class ItemClicked(val id: String) : Input()
        data class SearchChanged(val query: String) : Input()
        object Retry : Input()
    }

    // === OUTPUT: UI state ===
    data class Output(
        val isLoading: Boolean = false,
        val items: List<Item> = emptyList(),
        val error: String? = null,
        val searchQuery: String = "",
        val selectedItemId: String? = null
    )

    // === EFFECT: One-time events ===
    sealed class Effect {
        data class NavigateToDetail(val id: String) : Effect()
        data class ShowToast(val message: String) : Effect()
        object NavigateBack : Effect()
    }

    private val _output = MutableStateFlow(Output())
    val output: StateFlow<Output> = _output.asStateFlow()

    private val _effect = MutableSharedFlow<Effect>()
    val effect: SharedFlow<Effect> = _effect.asSharedFlow()

    init {
        onInput(Input.Load)
    }

    // === INPUT HANDLER ===
    fun onInput(input: Input) {
        when (input) {
            is Input.Load -> loadData()
            is Input.Refresh -> refreshData()
            is Input.ItemClicked -> handleItemClick(input.id)
            is Input.SearchChanged -> handleSearch(input.query)
            is Input.Retry -> loadData()
        }
    }

    private fun loadData() {
        viewModelScope.launch {
            _output.update { it.copy(isLoading = true, error = null) }

            repository.getItems()
                .onSuccess { items ->
                    _output.update { it.copy(isLoading = false, items = items) }
                }
                .onFailure { error ->
                    _output.update { it.copy(isLoading = false, error = error.message) }
                }
        }
    }

    private fun refreshData() {
        viewModelScope.launch {
            repository.getItems()
                .onSuccess { items ->
                    _output.update { it.copy(items = items) }
                    _effect.emit(Effect.ShowToast("更新成功"))
                }
                .onFailure { error ->
                    _effect.emit(Effect.ShowToast("更新失敗: ${error.message}"))
                }
        }
    }

    private fun handleItemClick(id: String) {
        viewModelScope.launch {
            _output.update { it.copy(selectedItemId = id) }
            _effect.emit(Effect.NavigateToDetail(id))
        }
    }

    private fun handleSearch(query: String) {
        _output.update { it.copy(searchQuery = query) }
        // Debounce search implementation
    }
}
```

## Screen Usage

```kotlin
@Composable
fun FeatureScreen(
    viewModel: FeatureViewModel = hiltViewModel(),
    onNavigateToDetail: (String) -> Unit,
    onNavigateBack: () -> Unit
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    // Handle one-time effects
    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is Effect.NavigateToDetail -> onNavigateToDetail(effect.id)
                is Effect.ShowToast -> { /* Show snackbar */ }
                is Effect.NavigateBack -> onNavigateBack()
            }
        }
    }

    // Render UI based on output
    when {
        output.isLoading -> LoadingState()
        output.error != null -> ErrorState(
            message = output.error!!,
            onRetry = { viewModel.onInput(Input.Retry) }
        )
        output.items.isEmpty() -> EmptyState()
        else -> ContentState(
            items = output.items,
            onItemClick = { id -> viewModel.onInput(Input.ItemClicked(id)) },
            onRefresh = { viewModel.onInput(Input.Refresh) }
        )
    }
}
```

## Key Principles

1. **Input is sealed class** - All user actions are explicit
2. **Output is data class** - Immutable state representation
3. **Effect is for one-time events** - Navigation, toasts, etc.
4. **Single onInput entry point** - All inputs go through one function
5. **StateFlow for Output** - Survives configuration changes
6. **SharedFlow for Effect** - Doesn't replay on new collectors
