# Screen and Requirement Mapping Table

This document defines how to create traceability relationships between screens (UI) and requirements (SRS).

## Screen Numbering Rules

### Screen ID Format

```
SCR-{ModuleCode}-{Number}

ModuleCode:
- AUTH: Authentication Module
- HOME: Home Module (Home/Dashboard)
- PAT:  Patient Module
- CLN:  Clinical Module
- RPT:  Report Module
- SET:  Settings Module
- COM:  Common Component

Example:
- SCR-AUTH-001: Login Screen
- SCR-PAT-010:  Patients List
- SCR-CLN-020:  Medication Record
```

## Mapping Table Template

### Screen List

```markdown
| Screen ID | Screen Name | Module | Corresponding Requirement | Figma | Status |
|---------|----------|------|----------|-------|------|
| SCR-AUTH-001 | Login Screen | AUTH | SRS-001, SRS-002 | [Link]() | ✅ |
| SCR-AUTH-002 | Register Screen | AUTH | SRS-003~005 | [Link]() | ✅ |
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
- **Last Update:** 2024-01-15

### Requirement Traceability

| Requirement ID | Requirement Description | UI Element | Verification Standard |
|----------|----------|---------|----------|
| SRS-001 | Account Password Login | Account input field, Password input field, Login button | AC1, AC2 |
| SRS-002 | Remember Account Function | Remember me checkbox | AC1 |
| SRS-003 | Biometric Login | Face ID/Fingerprint button | AC1, AC2 |

### UI Element List

| Element ID | Element Type | Description | Corresponding Requirement |
|---------|----------|------|----------|
| txt_account | TextField | Account input field | SRS-001 |
| txt_password | TextField | Password input field | SRS-001 |
| btn_login | Button | Login button | SRS-001 |
| chk_remember | Checkbox | Remember me | SRS-002 |
| btn_biometric | IconButton | Biometric | SRS-003 |
| lnk_forgot | TextLink | Forgot password link | SRS-006 |

### Used Assets

| Asset Type | File Name | Path |
|----------|----------|------|
| Icon | ic_visibility.svg | 03-assets/icons/svg/ |
| Icon | ic_fingerprint.svg | 03-assets/icons/svg/ |
| Icon | ic_face_id.svg | 03-assets/icons/svg/ |
| Image | bg_login.png | 03-assets/images/source/ |

### Screen States

| State | Description | Screenshot |
|------|------|------|
| Default | Default state | [Image]() |
| Loading | Login in progress | [Image]() |
| Error | Login failed | [Image]() |
| Biometric | Biometric prompt | [Image]() |
```

## Traceability Matrix Integration

### RTM Mapping

```markdown
Requirement Traceability Matrix (RTM) expansion:

| SRS ID | SDD ID | SWD ID | Screen ID | STC ID | SVV ID |
|--------|--------|--------|-----------|--------|--------|
| SRS-001 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-001 | SVV-001 |
| SRS-002 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-002 | SVV-001 |
| SRS-010 | SDD-010 | SWD-010 | SCR-HOME-001 | STC-010 | SVV-002 |
```

### Complete Traceability Path

```
SRS-001 (Requirement: Account Password Login)
    │
    ├── SDD-001 (Design: Authentication Module)
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
    └── STC-001 (Test: Login Function Test)
            │
            └── SVV-001 (Validation: Authentication Module Validation)
```

## Asset and Screen Mapping

### Asset Usage Matrix

Track which screens use each asset:

```markdown
| Asset Name | Type | Used in Screens | Corresponding Requirement |
|----------|------|----------|----------|
| ic_home.svg | Icon | SCR-HOME-001, SCR-COM-001 | SRS-010 |
| ic_patient.svg | Icon | SCR-PAT-001~010 | SRS-020~030 |
| ic_alert_critical.svg | Icon | SCR-CLN-*, SCR-HOME-001 | SRS-040 |
| bg_login.png | Image | SCR-AUTH-001 | SRS-001 |
| app_icon.png | AppIcon | All | - |
```

### Component Usage Matrix

Track common component usage:

```markdown
| Component Name | Figma Component | Used in Screens | Description |
|----------|-----------------|----------|------|
| PatientCard | Card/Patient/Default | SCR-PAT-001, SCR-HOME-001 | Patient information card |
| AlertBanner | Alert/Critical/Default | SCR-CLN-*, SCR-HOME-001 | Critical value alert |
| VitalSign | Display/VitalSign | SCR-PAT-002, SCR-CLN-010 | Vital signs display |
```

## Medical-Specific Considerations

### Clinical Safety Related Screen Labels

```markdown
| Screen ID | Safety Level | Description | Special Requirements |
|---------|----------|------|----------|
| SCR-CLN-001 | ⚠️ High | Medication Screen | Double confirmation, large font |
| SCR-CLN-010 | 🔴 Critical | Dosage Calculation | Non-editable results, audit log |
| SCR-PAT-001 | ⚠️ High | Patient Identification | Photo + text double confirmation |
```

### Accessibility Requirement Labels

```markdown
| Screen ID | WCAG Level | Contrast Ratio | Font Size | Note |
|---------|-----------|--------|----------|------|
| SCR-AUTH-001 | AA | ✅ 7:1 | 16px+ | Support zoom 200% |
| SCR-CLN-001 | AAA | ✅ 10:1 | 18px+ | Clinical environment requirement |
```

## Version Control

### Screen Version History

```markdown
## SCR-AUTH-001 Version History

| Version | Date | Change Description | Affected Requirement | Designer |
|------|------|----------|----------|--------|
| v1.0 | 2024-01-01 | Initial design | SRS-001 | @designer |
| v1.1 | 2024-01-10 | Add biometric authentication | SRS-003 | @designer |
| v1.2 | 2024-01-15 | Adjust button position | - | @designer |
```
