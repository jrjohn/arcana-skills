# MVVM Input/Output/Effect Pattern

## Overview

The Input/Output/Effect pattern provides a clear, unidirectional data flow for ViewModels in SwiftUI.

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
│  │                      View                            │       │
│  │   User Action → Input    |    Output → UI State     │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Template

```swift
import SwiftUI
import Observation

@Observable
final class FeatureViewModel {

    // === INPUT: User actions ===
    enum Input {
        case load
        case refresh
        case itemTapped(id: String)
        case searchChanged(query: String)
        case retry
    }

    // === OUTPUT: UI state ===
    struct Output {
        var isLoading: Bool = false
        var items: [Item] = []
        var error: String? = nil
        var searchQuery: String = ""
        var selectedItemId: String? = nil
    }

    // === EFFECT: One-time events ===
    enum Effect: Equatable {
        case navigateToDetail(id: String)
        case showToast(message: String)
        case navigateBack
    }

    private(set) var output = Output()
    var effect: Effect?

    private let repository: FeatureRepositoryProtocol

    init(repository: FeatureRepositoryProtocol) {
        self.repository = repository
        onInput(.load)
    }

    // === INPUT HANDLER ===
    func onInput(_ input: Input) {
        switch input {
        case .load:
            loadData()
        case .refresh:
            refreshData()
        case .itemTapped(let id):
            handleItemTap(id)
        case .searchChanged(let query):
            handleSearch(query)
        case .retry:
            loadData()
        }
    }

    private func loadData() {
        Task { @MainActor in
            output.isLoading = true
            output.error = nil

            do {
                let items = try await repository.getItems()
                output.items = items
                output.isLoading = false
            } catch {
                output.error = error.localizedDescription
                output.isLoading = false
            }
        }
    }

    private func refreshData() {
        Task { @MainActor in
            do {
                let items = try await repository.getItems()
                output.items = items
                effect = .showToast(message: "Updated successfully")
            } catch {
                effect = .showToast(message: "Update failed: \(error.localizedDescription)")
            }
        }
    }

    private func handleItemTap(_ id: String) {
        output.selectedItemId = id
        effect = .navigateToDetail(id: id)
    }

    private func handleSearch(_ query: String) {
        output.searchQuery = query
        // Debounce search implementation
    }
}
```

## View Usage

```swift
struct FeatureScreen: View {
    @State private var viewModel: FeatureViewModel

    var onNavigateToDetail: (String) -> Void = {}
    var onNavigateBack: () -> Void = {}

    init(repository: FeatureRepositoryProtocol) {
        _viewModel = State(initialValue: FeatureViewModel(repository: repository))
    }

    var body: some View {
        FeatureContent(
            output: viewModel.output,
            onInput: viewModel.onInput
        )
        .onChange(of: viewModel.effect) { _, effect in
            handleEffect(effect)
        }
    }

    private func handleEffect(_ effect: FeatureViewModel.Effect?) {
        guard let effect else { return }

        switch effect {
        case .navigateToDetail(let id):
            onNavigateToDetail(id)
        case .showToast(let message):
            // Show toast/snackbar
            print(message)
        case .navigateBack:
            onNavigateBack()
        }

        viewModel.effect = nil
    }
}

// Stateless content view for easy testing
struct FeatureContent: View {
    let output: FeatureViewModel.Output
    let onInput: (FeatureViewModel.Input) -> Void

    var body: some View {
        Group {
            if output.isLoading {
                ProgressView()
            } else if let error = output.error {
                ErrorView(
                    message: error,
                    onRetry: { onInput(.retry) }
                )
            } else if output.items.isEmpty {
                EmptyStateView()
            } else {
                ContentView(
                    items: output.items,
                    onItemTap: { id in onInput(.itemTapped(id: id)) },
                    onRefresh: { onInput(.refresh) }
                )
            }
        }
    }
}
```

## Key Principles

1. **Input is enum** - All user actions are explicit and type-safe
2. **Output is struct** - Immutable state representation
3. **Effect is for one-time events** - Navigation, toasts, etc.
4. **Single onInput entry point** - All inputs go through one function
5. **@Observable for Output** - Automatic SwiftUI updates
6. **Effect is optional** - Set to nil after handling

## Testing

```swift
final class FeatureViewModelTests: XCTestCase {
    var viewModel: FeatureViewModel!
    var mockRepository: MockFeatureRepository!

    override func setUp() {
        mockRepository = MockFeatureRepository()
        viewModel = FeatureViewModel(repository: mockRepository)
    }

    func testLoadData_Success() async {
        // Given
        mockRepository.items = [Item(id: "1", name: "Test")]

        // When
        viewModel.onInput(.load)
        await Task.yield()

        // Then
        XCTAssertEqual(viewModel.output.items.count, 1)
        XCTAssertFalse(viewModel.output.isLoading)
        XCTAssertNil(viewModel.output.error)
    }

    func testItemTapped_NavigatesToDetail() {
        // When
        viewModel.onInput(.itemTapped(id: "123"))

        // Then
        XCTAssertEqual(viewModel.effect, .navigateToDetail(id: "123"))
    }
}
```
