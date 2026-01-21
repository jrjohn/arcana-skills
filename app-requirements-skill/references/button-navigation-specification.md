# Button Navigation Specification

## Overview

This specification defines the standard format for Button Navigation Tables in SDD and how they integrate with `app-uiux-designer.skill` templates.

**Goal:** SDD provides Button Navigation as the **primary source**, reducing prediction needs for UI Flow.

### Navigation Resolution Priority

```
1️⃣ SDD Button Navigation Table (Priority)
   → If Target Screen exists, use directly

2️⃣ app-uiux-designer.skill Smart Prediction (Fallback)
   → If SDD doesn't provide, predict based on naming conventions

3️⃣ Default Values (Last Resort)
   → Use # or (current) when unable to determine
```

**Note:** Prediction functionality is retained as fallback mechanism, ensuring UI Flow can still be generated when SDD is incomplete.

---

## SDD Button Navigation Table Format

### Standard Format (Mandatory)

Each SCR-* screen section **must** include the following Button Navigation table:

```markdown
### Button Navigation

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Login | Button | SCR-AUTH-004-role | Validation success |
| btn_register | Register Now | Link | SCR-AUTH-002-register | - |
| btn_forgot | Forgot Password? | Link | SCR-AUTH-003-forgot-password | - |
| btn_apple | Apple | Button | SCR-AUTH-004-role | Apple login success |
| btn_google | Google | Button | SCR-AUTH-004-role | Google login success |
| btn_back | < | Button | history.back() | - |
```

### Column Descriptions

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| **Element ID** | Unique element identifier | Yes | `btn_login` |
| **Element Text** | Display text | Yes | `Login` |
| **Type** | Element type | Yes | `Button`, `Link`, `Icon`, `Tab`, `Row` |
| **Target Screen** | Navigation target | Yes | `SCR-AUTH-004-role` |
| **Condition** | Trigger condition | Optional | `Validation success`, `-` |

### Target Screen Formats

| Format | Usage | Example |
|--------|-------|---------|
| `SCR-MODULE-NNN-name` | Navigate to specified screen | `SCR-AUTH-004-role` |
| `history.back()` | Return to previous page | For Back/Close buttons |
| `(close modal)` | Close Modal | For close buttons in Modal |
| `(submit form)` | Navigate after form submission | Need Condition to specify success/failure targets |

---

## UI Flow Template Variable Mapping

### SDD → HTML Variable Mapping Table

| SDD Button Navigation | HTML Template Variable | HTML Output |
|-----------------------|------------------------|-------------|
| `Target Screen: SCR-AUTH-002-register` | `{{TARGET_REGISTER}}` | `onclick="location.href='SCR-AUTH-002-register.html'"` |
| `Target Screen: SCR-AUTH-004-role` | `{{TARGET_AFTER_LOGIN}}` | `onclick="location.href='SCR-AUTH-004-role.html'"` |
| `Target Screen: SCR-DASH-001-home` | `{{TARGET_HOME}}` | `onclick="location.href='SCR-DASH-001-home.html'"` |
| `Target Screen: SCR-SETTING-001-settings` | `{{TARGET_SETTINGS}}` | `onclick="location.href='SCR-SETTING-001-settings.html'"` |
| `Target Screen: history.back()` | `{{TARGET_BACK}}` | `onclick="history.back()"` |

### Standard Variable List

```
{{TARGET_BACK}}              - Return to previous page (usually history.back())
{{TARGET_HOME}}              - Home page
{{TARGET_SETTINGS}}          - Settings page
{{TARGET_PROFILE}}           - Profile page
{{TARGET_AFTER_LOGIN}}       - Navigation target after login success
{{TARGET_REGISTER}}          - Registration page
{{TARGET_FORGOT_PASSWORD}}   - Forgot password page
{{TARGET_SECURITY}}          - Account security page
{{TARGET_NOTIFICATION}}      - Notification settings page
{{TARGET_APPEARANCE}}        - Appearance settings page
{{TARGET_PRIVACY}}           - Privacy settings page
{{TARGET_DATA}}              - Data management page
{{TARGET_TERMS}}             - Terms of service page
{{TARGET_ABOUT}}             - About page
{{TARGET_LOGOUT}}            - Logout (usually returns to login page)
```

---

## SDD Pre-Generation Checklist

Before calling `app-uiux-designer.skill` to generate UI Flow, the following checks **must** be completed:

### ⚠️ Button Navigation Completeness Check (100% Required)

- [ ] Every SCR-* section has a `### Button Navigation` table
- [ ] Every clickable element has a Target Screen
- [ ] All Target Screens point to existing SCR-* IDs
- [ ] No dangling Target Screens (pointing to non-existent screens)
- [ ] `history.back()` used for all back buttons
- [ ] Modal/Sheet has clear close mechanism

### Validation Script

```bash
# Execute Button Navigation validation
node ~/.claude/skills/app-requirements-skill/scripts/validate-button-navigation.js [SDD_FILE]
```

---

## Integration Workflow

### Complete Flow (Spec-Driven, No Prediction)

```
Phase 1: Requirements Gathering (app-requirements-skill)
├── Gather functional requirements
├── Define REQ-* list
└── Output: SRS

Phase 2: Screen Design Specification (app-requirements-skill)
├── Define all SCR-* screens
├── Create Button Navigation Table for each screen ⚠️ Complete filling
├── Validate Navigation completeness (100% coverage)
└── Output: SDD (spec-complete)

Phase 3: UI Flow Generation (app-uiux-designer.skill)
├── Read SDD's Button Navigation Table
├── Convert Target Screen to {{TARGET_*}} variables
├── Copy templates and replace variables
├── **No navigation target prediction needed**
└── Output: HTML UI Flow

Phase 4: SRS/SDD Backfill (app-uiux-designer.skill → app-requirements-skill)
├── Embed screenshots in SDD
├── Update SRS Screen References
├── Verify RTM coverage
└── Output: Updated SRS/SDD
```

---

## Examples

### Example 1: Login Screen (SCR-AUTH-001)

**SDD Definition:**

```markdown
#### SCR-AUTH-001: Login Screen

**Module:** AUTH
**Priority:** P0
**Related Requirements:** REQ-AUTH-001, REQ-AUTH-002

##### Screen Description
User login screen, supports Email/password login and social login.

##### UI Component Table

| Component | Type | Description | Requirement |
|-----------|------|-------------|-------------|
| txt_email | TextField | Email input field | REQ-AUTH-001 |
| txt_password | PasswordField | Password input field | REQ-AUTH-001 |
| btn_login | Button | Login button | REQ-AUTH-001 |
| btn_apple | Button | Apple login | REQ-AUTH-002 |
| btn_google | Button | Google login | REQ-AUTH-002 |
| lnk_forgot | Link | Forgot password link | REQ-AUTH-003 |
| lnk_register | Link | Register link | REQ-AUTH-004 |

##### Button Navigation ⚠️ MANDATORY

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Login | Button | SCR-AUTH-004-role | Validation success |
| btn_apple | Apple | Button | SCR-AUTH-004-role | Apple login success |
| btn_google | Google | Button | SCR-AUTH-004-role | Google login success |
| lnk_forgot | Forgot Password? | Link | SCR-AUTH-003-forgot-password | - |
| lnk_register | Register Now | Link | SCR-AUTH-002-register | - |
```

**UI Flow Template Variable Mapping:**

```html
<!-- login-ipad.html template -->
<button onclick="location.href='{{TARGET_AFTER_LOGIN}}'">Login</button>
<a href="{{TARGET_FORGOT_PASSWORD}}">Forgot Password?</a>
<a href="{{TARGET_REGISTER}}">Register Now</a>

<!-- After replacement -->
<button onclick="location.href='SCR-AUTH-004-role.html'">Login</button>
<a href="SCR-AUTH-003-forgot-password.html">Forgot Password?</a>
<a href="SCR-AUTH-002-register.html">Register Now</a>
```

### Example 2: Settings Screen (SCR-SETTING-001)

**SDD Definition:**

```markdown
##### Button Navigation ⚠️ MANDATORY

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_back | < | Icon | history.back() | - |
| row_profile | Profile | Row | SCR-SETTING-002-profile | - |
| row_security | Account Security | Row | SCR-SETTING-003-security | - |
| row_privacy | Privacy Settings | Row | SCR-SETTING-004-privacy | - |
| row_data | Data Management | Row | SCR-SETTING-005-data | - |
| row_notification | Notification Settings | Row | SCR-SETTING-006-notification | - |
| row_appearance | Theme Appearance | Row | SCR-SETTING-007-appearance | - |
| row_voice | Voice Settings | Row | SCR-SETTING-008-voice | - |
| row_terms | Terms of Service | Row | SCR-SETTING-010-terms | - |
| row_about | About | Row | SCR-SETTING-012-about | - |
| btn_logout | Logout | Button | SCR-AUTH-001-login | Confirm logout |
```

---

## Validation Rules

### Rule 1: No Empty Targets

```
❌ Wrong: Target Screen is empty
| btn_login | Login | Button |  | - |

✅ Correct: Target Screen has clear target
| btn_login | Login | Button | SCR-AUTH-004-role | Validation success |
```

### Rule 2: All Targets Must Exist

```
❌ Wrong: Target Screen points to non-existent screen
| btn_login | Login | Button | SCR-AUTH-999-unknown | - |

✅ Correct: Target Screen exists in SDD
| btn_login | Login | Button | SCR-AUTH-004-role | - |
```

### Rule 3: Settings Rows Must Navigate

```
❌ Wrong: Settings row uses alert()
| row_profile | Profile | Row | alert('Feature coming soon') | - |

✅ Correct: Settings row navigates to sub-screen
| row_profile | Profile | Row | SCR-SETTING-002-profile | - |
```

### Rule 4: Consistent Format

```
❌ Wrong: Target includes file extension
| btn_login | Login | Button | SCR-AUTH-004-role.html | - |

✅ Correct: Target is only Screen ID
| btn_login | Login | Button | SCR-AUTH-004-role | - |
```

---

## Summary

| Before (Prediction-Based) | After (Spec-Driven) |
|---------------------------|---------------------|
| SDD only has screen names | SDD includes complete Button Navigation |
| UI Flow has to "guess" navigation targets | UI Flow directly reads SDD definitions |
| May have navigation gaps | 100% navigation coverage guaranteed |
| May find inconsistencies during backfill | Spec consistent, no corrections needed |
