# Screen-Requirement Mapping

This document defines how to establish traceability between screens (UI) and requirements (SRS).

## Screen Numbering Rules

### Screen ID Format

```
SCR-{MODULE_CODE}-{SEQUENCE}

Module Codes:
- AUTH: Authentication Module
- HOME: Home/Dashboard Module
- PAT:  Patient Module
- CLN:  Clinical Module
- RPT:  Report Module
- SET:  Settings Module
- COM:  Common Components

Examples:
- SCR-AUTH-001: Login Screen
- SCR-PAT-010:  Patient List
- SCR-CLN-020:  Medication Records
```

## Mapping Table Template

### Screen List

```markdown
| Screen ID | Screen Name | Module | Related Requirements | Figma | Status |
|-----------|-------------|--------|---------------------|-------|--------|
| SCR-AUTH-001 | Login Screen | AUTH | SRS-001, SRS-002 | [Link]() | ✅ |
| SCR-AUTH-002 | Registration Screen | AUTH | SRS-003~005 | [Link]() | ✅ |
| SCR-AUTH-003 | Forgot Password | AUTH | SRS-006 | [Link]() | 🔄 |
| SCR-HOME-001 | Home | HOME | SRS-010~015 | [Link]() | 📝 |
```

### Detailed Mapping Table

Create detailed mapping for each screen:

```markdown
## SCR-AUTH-001 Login Screen

### Basic Information
- **Screen Name:** Login Screen
- **Module:** Authentication
- **Figma:** [Link](https://figma.com/...)
- **Design Version:** v1.2
- **Last Updated:** 2024-01-15

### Requirements Traceability

| Requirement ID | Requirement Description | UI Elements | Acceptance Criteria |
|----------------|------------------------|-------------|---------------------|
| SRS-001 | Email/password login | Account input, Password input, Login button | AC1, AC2 |
| SRS-002 | Remember account feature | Remember me checkbox | AC1 |
| SRS-003 | Biometric login | Face ID/Fingerprint button | AC1, AC2 |

### UI Elements List

| Element ID | Element Type | Description | Related Requirement |
|------------|--------------|-------------|---------------------|
| txt_account | TextField | Account input | SRS-001 |
| txt_password | TextField | Password input | SRS-001 |
| btn_login | Button | Login button | SRS-001 |
| chk_remember | Checkbox | Remember me | SRS-002 |
| btn_biometric | IconButton | Biometric | SRS-003 |
| lnk_forgot | TextLink | Forgot password link | SRS-006 |

### Assets Used

| Asset Type | Filename | Path |
|------------|----------|------|
| Icon | ic_visibility.svg | 03-assets/icons/svg/ |
| Icon | ic_fingerprint.svg | 03-assets/icons/svg/ |
| Icon | ic_face_id.svg | 03-assets/icons/svg/ |
| Image | bg_login.png | 03-assets/images/source/ |

### Screen States

| State | Description | Screenshot |
|-------|-------------|------------|
| Default | Initial state | [Image]() |
| Loading | Logging in | [Image]() |
| Error | Login failed | [Image]() |
| Biometric | Biometric prompt | [Image]() |

### Button Navigation

Define target screens for each interactive element, enabling UI generation tools to build correct flow links:

| Element ID | Element Text | Action Type | Target Screen | Condition/Notes |
|------------|--------------|-------------|---------------|-----------------|
| btn_login | Login | navigate | SCR-HOME-001 | On successful verification |
| btn_login | Login | navigate | SCR-AUTH-001 (Error) | On verification failure |
| lnk_forgot | Forgot Password | navigate | SCR-AUTH-003 | - |
| lnk_register | Register | navigate | SCR-AUTH-002 | - |
| btn_biometric | Biometric | navigate | SCR-HOME-001 | On successful verification |
| btn_back | Back | back | history.back() | Previous page |

**Action Type Definitions:**
- `navigate`: Navigate to specified screen
- `back`: Go back to previous page (history.back)
- `modal`: Open modal dialog (specify Modal ID)
- `external`: Open external link
- `action`: Trigger action (no navigation, e.g., submit form)

**Target Screen Formats:**
- Standard screen: `SCR-{MODULE}-{SEQUENCE}` (e.g., SCR-AUTH-001)
- State variant: `SCR-{MODULE}-{SEQUENCE} ({STATE})` (e.g., SCR-AUTH-001 (Error))
- Go back: `history.back()`
- Modal: `MODAL-{MODULE}-{SEQUENCE}` (e.g., MODAL-AUTH-001)
```

## RTM Integration

### RTM Correspondence

```markdown
Requirements Traceability Matrix (RTM) Extension:

| SRS ID | SDD ID | SWD ID | Screen ID | STC ID | SVV ID |
|--------|--------|--------|-----------|--------|--------|
| SRS-001 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-001 | SVV-001 |
| SRS-002 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-002 | SVV-001 |
| SRS-010 | SDD-010 | SWD-010 | SCR-HOME-001 | STC-010 | SVV-002 |
```

### Complete Traceability Path

```
SRS-001 (Requirement: Email/password login)
    │
    ├── SDD-001 (Design: Authentication module)
    │       │
    │       └── SWD-001 (Detailed Design: AuthenticationService)
    │
    ├── SCR-AUTH-001 (Screen: Login Screen)
    │       │
    │       ├── Figma Frame: "SCR-AUTH-001 - Login"
    │       │
    │       ├── UI Elements:
    │       │   ├── txt_account
    │       │   ├── txt_password
    │       │   └── btn_login
    │       │
    │       └── Assets:
    │           ├── ic_visibility.svg
    │           └── bg_login.png
    │
    └── STC-001 (Test: Login function test)
            │
            └── SVV-001 (Verification: Authentication module verification)
```

## Asset and Screen Mapping

### Asset Usage Matrix

Track which screens use each asset:

```markdown
| Asset Name | Type | Used In Screens | Related Requirements |
|------------|------|-----------------|---------------------|
| ic_home.svg | Icon | SCR-HOME-001, SCR-COM-001 | SRS-010 |
| ic_patient.svg | Icon | SCR-PAT-001~010 | SRS-020~030 |
| ic_alert_critical.svg | Icon | SCR-CLN-*, SCR-HOME-001 | SRS-040 |
| bg_login.png | Image | SCR-AUTH-001 | SRS-001 |
| app_icon.png | AppIcon | Global | - |
```

### Component Usage Matrix

Track shared component usage:

```markdown
| Component Name | Figma Component | Used In Screens | Description |
|----------------|-----------------|-----------------|-------------|
| PatientCard | Card/Patient/Default | SCR-PAT-001, SCR-HOME-001 | Patient info card |
| AlertBanner | Alert/Critical/Default | SCR-CLN-*, SCR-HOME-001 | Critical value alert |
| VitalSign | Display/VitalSign | SCR-PAT-002, SCR-CLN-010 | Vital signs display |
```

## Medical-Specific Considerations

### Clinical Safety Screen Marking

```markdown
| Screen ID | Safety Level | Description | Special Requirements |
|-----------|--------------|-------------|---------------------|
| SCR-CLN-001 | ⚠️ High | Medication screen | Double confirmation, large font |
| SCR-CLN-010 | 🔴 Critical | Dosage calculation | Non-editable results, audit trail |
| SCR-PAT-001 | ⚠️ High | Patient identification | Photo+text double confirmation |
```

### Accessibility Requirements Marking

```markdown
| Screen ID | WCAG Level | Contrast | Font Size | Notes |
|-----------|------------|----------|-----------|-------|
| SCR-AUTH-001 | AA | ✅ 7:1 | 16px+ | Supports 200% zoom |
| SCR-CLN-001 | AAA | ✅ 10:1 | 18px+ | Clinical environment requirements |
```

## Version Control

### Screen Version History

```markdown
## SCR-AUTH-001 Version History

| Version | Date | Change Description | Affected Requirements | Designer |
|---------|------|-------------------|-----------------------|----------|
| v1.0 | 2024-01-01 | Initial design | SRS-001 | @designer |
| v1.1 | 2024-01-10 | Added biometric login | SRS-003 | @designer |
| v1.2 | 2024-01-15 | Adjusted button positions | - | @designer |
```

## Integration with app-uiux-designer.skill

### Integration Workflow

SRS/SDD screen specifications produced by this Skill can be bidirectionally synced with `app-uiux-designer.skill`:

```
┌─────────────────────────────────────────────────────────────┐
│            app-requirements-skill                           │
│                                                             │
│  SRS.md                          SDD.md                     │
│  ├── Functional Requirements     ├── UI/UX Design Section  │
│  ├── Acceptance Criteria (AC)    ├── Screen Specs (SCR-*)  │
│  └── Screen Mapping              └── Button Navigation     │
│        │                               │                    │
│        │ ① Read Requirements          │ ② Read Specs       │
│        ▼                               ▼                    │
│   ┌─────────────────────────────────────────────┐           │
│   │         app-uiux-designer.skill             │           │
│   │  ③ Generate UI + Infer Missing + Infer Reqs │           │
│   └─────────────────────────────────────────────┘           │
│                          │                                  │
│                          ▼                                  │
│   generated-ui/                                             │
│   ├── HTML UI Files                                         │
│   ├── screenshots/                                          │
│   ├── ui-flow-diagram.html                                  │
│   └── flow-diagram.md (Mermaid)                             │
│                          │                                  │
│           ┌──────────────┴──────────────┐                   │
│           │ ④ Backfill Updates          │                   │
│           ▼                              ▼                   │
│   SRS.md (Updated)                SDD.md (Updated)          │
│   ├── New Requirements (Inferred) ├── Button Navigation     │
│   ├── Acceptance Criteria (AC)    ├── Embedded Screenshots  │
│   └── RTM Mapping                 ├── Mermaid Flow Diagram  │
│           │                       └── Psychology Validation │
│           ▼                              │                   │
│   ┌──────────────────────────────────────┐                  │
│   │ ⑤ Regenerate Documents               │                  │
│   │ ├── SRS.docx (with new requirements) │                  │
│   │ ├── SDD.docx (with screenshots)      │                  │
│   │ └── RTM.md (100% traceability)      │                  │
│   └──────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Integration Commands

```bash
# 1. Generate UI from SDD (app-uiux-designer.skill)
Generate UI ./docs/SDD.md --output ./generated-ui/

# 2. Generate Mermaid flow diagram (embeddable in SDD/SRS)
node ~/.claude/skills/app-uiux-designer.skill/scripts/generate-mermaid-flow.js ./generated-ui/ ./docs/flow-diagram.md

# 3. Embed screenshots in SDD
node ~/.claude/skills/app-uiux-designer.skill/scripts/embed-screenshots-to-sdd.js ./docs/SDD.md ./generated-ui/screenshots --copy-to ./docs/images

# 4. Psychology validation
Validate Psychology ./generated-ui/ --output ./reports/psychology-report.md

# 5. Backfill SDD (Button Navigation inference results)
Backfill SDD ./docs/SDD.md --from ./generated-ui/

# 6. Backfill SRS (Inferred new requirements + acceptance criteria)
Backfill SRS ./docs/SRS.md --from ./generated-ui/

# 7. Regenerate DOCX
node ~/.claude/skills/app-requirements-skill/md-to-docx.js ./docs/SRS.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js ./docs/SDD.md

# 8. Verify RTM 100% traceability
Verify RTM ./docs/RTM.md
```

### ID Format Consistency

Both Skills use unified **SCR-{MODULE}-{SEQUENCE}** format:

| Skill | ID Format | Example |
|-------|-----------|---------|
| app-requirements-skill | SCR-AUTH-001 | SCR-AUTH-001 Login Screen |
| app-uiux-designer.skill | SCR-AUTH-001 | SCR-AUTH-001-login.html |

### Data Synchronization Items

| Item | Direction | Description |
|------|-----------|-------------|
| Button Navigation | Bidirectional | SDD defines → UI implements → Inference backfills SDD |
| UI Screenshots | UI→SDD | Auto-embed in SDD screen sections |
| Mermaid Flow Diagram | UI→SDD/SRS | Auto-update flow diagram sections |
| Psychology Validation | UI→SDD | Update SDD psychology compliance section |
| **Functional Requirements (Inferred)** | UI→SRS | Infer missing functional requirements from buttons |
| **Acceptance Criteria (AC)** | UI→SRS | Generate acceptance criteria from navigation |
| **Screen Mapping** | UI→SRS | Update requirement SCR mappings |
| Traceability Matrix | Bidirectional | SRS/SDD/SCR/STC 100% traceability |

### SRS Backfill Rules

When inferring SRS requirements from UI flow, follow these rules:

| Button Type | Inferred Requirement | Confidence |
|-------------|---------------------|------------|
| Save/Submit/Confirm | Data processing function | 🟢 High |
| Create/Add | Create function | 🟢 High |
| Back/Cancel | Return mechanism | 🟢 High |
| Next/Continue | Flow navigation | 🟡 Medium |
| Login/Logout | Authentication function | 🟢 High |
| Delete/Remove | Delete function | 🟢 High |

### Acceptance Criteria (AC) Generation Rules

```markdown
# Button Navigation → Acceptance Criteria

1. **Existence AC:**
   Given user is on {source screen}
   Then should see "{button text}" button

2. **Function AC:**
   When clicking "{button text}" button
   Then should {execute action} / navigate to {target screen}

3. **Conditional AC (if applicable):**
   Given {precondition}
   When clicking "{button text}" button
   Then should {conditional result}
```

### Backfill Reports

After executing backfill, the following reports are generated:

| Report | Path | Description |
|--------|------|-------------|
| SRS Backfill Report | `./reports/srs-feedback-report.md` | New requirements, AC, RTM updates |
| SDD Backfill Report | `./reports/sdd-feedback-report.md` | Navigation, screenshots, flow diagrams |
| RTM Verification Report | `./reports/rtm-verification.md` | Traceability completeness check |
```
