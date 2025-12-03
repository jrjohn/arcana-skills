# Android Developer Skill

Professional Android development skill based on [Arcana Android](https://github.com/jrjohn/arcana-android) enterprise architecture.

## Overview

This skill provides comprehensive guidance for Android development following enterprise-grade architectural patterns. It supports Clean Architecture, Offline-First design, Jetpack Compose, Hilt DI, and the MVVM Input/Output pattern.

## Key Features

- **Clean Architecture** - Three-layer architecture (Presentation, Domain, Data)
- **MVVM Input/Output** - Unidirectional data flow pattern with Kotlin sealed interfaces
- **Offline-First Design** - Room database as single source of truth
- **Jetpack Compose** - Modern declarative UI framework
- **Hilt Dependency Injection** - Type-safe DI with compile-time validation
- **Kotlin Coroutines & Flow** - Reactive state management

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│         Compose UI + MVVM + Input/Output            │
├─────────────────────────────────────────────────────┤
│                    Domain Layer                      │
│          Business Logic + Services + Models         │
├─────────────────────────────────────────────────────┤
│                     Data Layer                       │
│      Offline-First Repository + Room + API          │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Technology | Version |
|------------|---------|
| Kotlin | 1.9+ |
| Jetpack Compose | 1.5+ |
| Room | 2.6+ |
| Hilt | 2.48+ |
| Retrofit | 2.9+ |
| Coroutines | 1.7+ |
| Android SDK | 34+ |

## Documentation

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions and architecture overview |
| [reference.md](reference.md) | Technical reference for APIs and components |
| [examples.md](examples.md) | Practical code examples for common scenarios |
| [patterns.md](patterns.md) | Design patterns and best practices |

## When to Use This Skill

This skill is ideal for:

- Android project development from scratch
- Architecture design and review
- Code review for Android applications
- Implementing offline-first features
- Jetpack Compose UI development
- Dependency injection setup with Hilt

## Quick Start

### ViewModel Input/Output Pattern

```kotlin
@HiltViewModel
class UserViewModel @Inject constructor(
    private val userService: UserService
) : ViewModel() {

    // Input: Sealed interface defining all events
    sealed interface Input {
        data class UpdateName(val name: String) : Input
        data object Submit : Input
    }

    // Output: State container
    data class Output(
        val name: String = "",
        val isLoading: Boolean = false,
        val error: String? = null
    )

    // Effect: One-time events
    sealed interface Effect {
        data object NavigateBack : Effect
        data class ShowSnackbar(val message: String) : Effect
    }

    private val _output = MutableStateFlow(Output())
    val output: StateFlow<Output> = _output.asStateFlow()

    private val _effect = Channel<Effect>()
    val effect = _effect.receiveAsFlow()

    fun onInput(input: Input) {
        when (input) {
            is Input.UpdateName -> _output.update { it.copy(name = input.name) }
            is Input.Submit -> submit()
        }
    }
}
```

### Offline-First Repository

```kotlin
class UserRepositoryImpl @Inject constructor(
    private val userDao: UserDao,
    private val userApi: UserApi
) : UserRepository {

    override fun getUsers(): Flow<List<User>> = flow {
        // 1. Emit cached data first
        emit(userDao.getAll().map { it.toDomain() })

        // 2. Fetch fresh data from API
        try {
            val remote = userApi.getUsers()
            userDao.insertAll(remote.map { it.toEntity() })
            emit(userDao.getAll().map { it.toDomain() })
        } catch (e: Exception) {
            // Return cached data on error
        }
    }
}
```

### Compose UI with ViewModel

```kotlin
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel()
) {
    val output by viewModel.output.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is Effect.NavigateBack -> navController.popBackStack()
                is Effect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    UserContent(
        output = output,
        onNameChange = { viewModel.onInput(Input.UpdateName(it)) },
        onSubmit = { viewModel.onInput(Input.Submit) }
    )
}
```

## Dependency Rules

- **Unidirectional Dependencies**: Presentation → Domain → Data
- **Interface Segregation**: Decouple layers through interfaces
- **Dependency Inversion**: Data layer implements Domain layer interfaces

## License

This skill is part of the Arcana enterprise architecture series.
