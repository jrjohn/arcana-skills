# Diagram Color Standards / 圖表顏色標準

Consistent color usage across all IEC 62304 documentation diagrams.

## Code Syntax Highlighting (VSCode Light+ Theme)

| Token Type | Color | Example |
|------------|-------|---------|
| Keyword | `#0000FF` Blue | `class`, `func`, `if`, `return` |
| String | `#A31515` Dark Red | `"Hello"`, `'text'` |
| Comment | `#008000` Green | `// comment`, `/* block */` |
| Number | `#098658` Dark Cyan | `123`, `3.14` |
| Type | `#267F99` Cyan Blue | `String`, `Int`, `Bool` |
| Decorator | `#AF00DB` Purple | `@State`, `@Published` |
| Default | `#000000` Black | Other identifiers |

### Supported Languages
- Swift / Kotlin / Java (Mobile)
- Python / JavaScript / TypeScript (Backend/Frontend)
- HTML / CSS / SQL

---

## Class Diagram Colors (Peter Coad Color UML)

Mermaid Class Diagrams use **Peter Coad's Four-Color Archetype** for visual classification:

| Archetype | Color | Hex | Usage | Mermaid Style |
|-----------|-------|-----|-------|---------------|
| **MI (Moment-Interval)** | Pink | `#FFCCCC` | Service, UseCase, Transaction | `style XXXService fill:#FFCCCC` |
| **Role** | Yellow | `#FFFFCC` | ViewModel, Presenter, Controller | `style XXXViewModel fill:#FFFFCC` |
| **Thing (Party/Place/Thing)** | Green | `#CCFFCC` | Entity, Model, Domain Object | `style XXXEntity fill:#CCFFCC` |
| **Description** | Blue | `#CCCCFF` | Repository, DTO, Configuration | `style XXXRepository fill:#CCCCFF` |

### Class Diagram Example

```mermaid
classDiagram
    class AuthService {
        <<MI-Service>>
        +login(credentials) Result
    }
    class LoginViewModel {
        <<Role-ViewModel>>
        +username: String
        +password: String
    }
    class User {
        <<Thing-Entity>>
        +id: UUID
        +email: String
    }
    class UserRepository {
        <<Description-Repository>>
        +save(user)
        +findById(id)
    }

    AuthService --> LoginViewModel
    LoginViewModel --> User
    UserRepository --> User

    style AuthService fill:#FFCCCC
    style LoginViewModel fill:#FFFFCC
    style User fill:#CCFFCC
    style UserRepository fill:#CCCCFF
```

---

## State Machine Colors

Mermaid State Diagrams use these colors to distinguish state types:

| State Type | Color | Hex Code | Text Color | Usage |
|------------|-------|----------|------------|-------|
| **Initial/Inactive** | Warm Gray | `#E8E0D8` | `#5D4037` | Not started (Idle, Disconnected) |
| **Processing/In Progress** | Warm Gold | `#F4A940` | `#5D4037` | Executing transition (Processing, Scanning) |
| **Success/Complete** | Grass Green | `#8BC34A` | `#fff` | Successfully completed (Authenticated, Connected) |
| **Error/Failed** | Warm Coral | `#E57373` | `#fff` | Error occurred (Failed, Error) |
| **Warning/Locked** | Amber Yellow | `#FFB74D` | `#5D4037` | Needs attention (Locked, Timeout) |

### State Machine Example

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Idle
    Idle --> Processing: start
    Processing --> Success: complete
    Processing --> Failed: error
    Failed --> Idle: retry
    Failed --> Locked: 5x failed

    classDef initial fill:#E8E0D8,stroke:#D4C8BC,color:#5D4037
    classDef processing fill:#F4A940,stroke:#E09830,color:#5D4037
    classDef success fill:#8BC34A,stroke:#7CB342,color:#fff
    classDef error fill:#E57373,stroke:#D32F2F,color:#fff
    classDef warning fill:#FFB74D,stroke:#FFA726,color:#5D4037

    class Idle initial
    class Processing processing
    class Success success
    class Failed error
    class Locked warning
```

---

## C4 Model Architecture Colors

Context View, Container View use **warm color palette** (friendly style):

| Element Type | Color | Hex Code | Text Color | Usage |
|--------------|-------|----------|------------|-------|
| **Person** | Deep Brown-Orange | `#A1664A` | `#fff` | Users, Roles |
| **Software System** | Orange | `#E67E22` | `#fff` | Main system (current development) |
| **Container** | Warm Gold | `#F4A940` | `#5D4037` | App, Database, Server |
| **Component** | Light Apricot | `#FDEBD0` | `#5D4037` | Internal components |
| **External System** | Warm Gray-Brown | `#8D7B6B` | `#fff` | External systems, third-party services |
