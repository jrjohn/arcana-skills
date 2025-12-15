# SDD Screen Flow Standards / SDD 標準畫面流程規範

> **Important:** All SDD document module design chapters must follow **standard app navigation flow** to ensure developers can read and implement in logical order.

## Standard App Navigation Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Standard App Navigation Flow                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Splash Screen                                               │
│         │                                                       │
│         ▼                                                       │
│  2. Auth Check ─────┬─── Logged In ──────► Direct to Dashboard  │
│         │           │                                           │
│         │           └─── Not Logged In ──► Login Screen         │
│         │                                   ├─ Register         │
│         │                                   ├─ Forgot Password  │
│         │                                   └─ Social Login     │
│         │                                                       │
│         ▼                                                       │
│  3. First Use Check ──┬─── First Time ───► Onboarding Flow      │
│         │             │                    (3-6 screens)        │
│         │             │                                         │
│         │             └─── Returning ────► Dashboard            │
│         │                                                       │
│         ▼                                                       │
│  4. Dashboard (Home)                                            │
│         │                                                       │
│         ▼                                                       │
│  5. Tab Navigation (Bottom)                                     │
│     ┌──────┬──────┬──────┬──────┬──────┐                        │
│     │ Home │ Tab2 │ Tab3 │ Tab4 │Setting│                       │
│     └──────┴──────┴──────┴──────┴──────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## SDD Module Design Chapter Order / 模組設計章節順序規範

Module design chapters should follow this order, aligned with app navigation flow and **design psychology principles**:

| Order | Module | Required Screens | Description | Psychology Basis |
|-------|--------|------------------|-------------|------------------|
| 1 | **AUTH** | Login→Register→Password Reset→Social Login | App entry point | Security establishment |
| 2 | **HOME/DASHBOARD** | Status Overview→Progress→Navigation | **Mental buffer zone** | Cognitive Load, Orientation |
| 3 | **CORE** (primary features) | Prerequisite Check→Feature Flow | Main business features | Progressive Disclosure |
| 4 | **DATA** | Data List→Detail→Export | Data management | Information Architecture |
| 5 | **COMM** (if applicable) | Device/Connection→Status | Hardware connectivity | Prerequisite Design |
| 6 | **ALERT** | Notifications→Alert Settings | Alert management | Feedback Design |
| 7 | **REPORT** | Overview→Detailed Report→Export | Analytics & reporting | Achievement Design |
| 8 | **SETTING** | Profile→Notifications→Language→Logout | Always last | Hick's Law |
| 9 | **PLATFORM** (backend) | Backend service design | Non-UI, placed last | - |

> **⚠️ Key Order Principles:**
> 1. **Dashboard must appear immediately after auth** - Mental buffer zone, cannot be skipped
> 2. **Prerequisites before dependent features** - Hardware/connectivity before features that need them
> 3. **Settings always last** - Matches user mental model

## Module Internal Structure / 模組內部結構規範

Each module must organize sub-chapters in this order:

```markdown
### 3.X Module Name (MODULE_CODE)

| Design ID | Name | Related Requirement | Related Screen | Description |
|-----------|------|---------------------|----------------|-------------|
| SDD-XXX-001 | ... | SRS-XXX-001 | SCR-XXX-001 | ... |

#### 3.X.1 Module Architecture Design
- State Machine
- Service Interface
- Data Flow

#### 3.X.2 Screen Design: SCR-XXX-001 First Screen
- Screen properties table
- Wireframe (Mermaid block-beta)
- Interaction behavior table

#### 3.X.3 Screen Design: SCR-XXX-002 Second Screen
...
```

## AUTH Module Standard Structure (Example)

```markdown
### 3.1 Authentication Module (AUTH)

#### 3.1.1 Authentication Service Architecture Design
- Authentication flow state machine
- AuthService interface

#### 3.1.2 Screen Design: SCR-AUTH-001 Login Screen
#### 3.1.3 Screen Design: SCR-AUTH-002 Register Screen
#### 3.1.4 Screen Design: SCR-AUTH-003 Forgot Password
#### 3.1.5 Social Login Integration Design
#### 3.1.6 Profile Management Design (if applicable)
#### 3.1.7 Screen Design: SCR-AUTH-004 Profile Selection
#### 3.1.8 Screen Design: SCR-AUTH-005 Profile Edit
```

## Screen Design Chapter Standard Format

```markdown
#### 3.X.N Screen Design: SCR-XXX-NNN Screen Name

| Item | Content |
|------|---------|
| Screen ID | SCR-XXX-NNN |
| Related Design | SDD-XXX-NNN |
| Related Requirement | SRS-XXX-NNN |

**Wireframe**

\`\`\`mermaid
block-beta
    columns 1

    block:header:1
        columns 1
        title["Screen Title"]
    end

    block:content:1
        columns 1
        element["Main Content"]
    end

    block:actions:1
        columns 1
        button["[ Primary Button ]"]
    end
\`\`\`

**Interaction Behavior**

| Element | Behavior | Result |
|---------|----------|--------|
| Button | Click | Navigate to next screen |
```

## Forbidden Module Structures

- ❌ Auth module starting from Profile, skipping Login/Register
- ❌ Screen designs scattered across different chapters
- ❌ Module with only architecture design, no screen design
- ❌ Screen order not matching actual navigation flow
- ❌ Duplicate chapter numbers (e.g., two 3.3.1)
