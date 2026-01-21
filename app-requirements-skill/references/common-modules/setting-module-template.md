# SETTING Module Template (Settings Module)

Standard screen definitions for the Settings module, providing a complete system settings functionality framework.

---

## Module Overview

| Item | Value |
|------|-------|
| Module Code | SETTING |
| Necessity | **Required** |
| Minimum Screens | 4 |
| Complete Screens | 18 |
| Related Requirements | REQ-SETTING-* |

---

## Standard Screen List

### Required Screens (4)

| Screen ID | Name | Necessity | Priority |
|-----------|------|-----------|----------|
| SCR-SETTING-001-main | Settings Main | **Required** | P0 |
| SCR-SETTING-002-account | Account Settings | **Required** | P0 |
| SCR-SETTING-003-privacy | Privacy Settings | **Required** | P0 |
| SCR-SETTING-004-about | About | **Required** | P0 |

### Optional Screens (14)

| Screen ID | Name | Necessity | Priority | Description |
|-----------|------|-----------|----------|-------------|
| SCR-SETTING-005-notification | Notification Settings | Optional | P1 | Push notification preferences |
| SCR-SETTING-006-language | Language Settings | Optional | P1 | Multi-language support |
| SCR-SETTING-007-theme | Theme Settings | Optional | P1 | Light/Dark mode |
| SCR-SETTING-008-sound | Sound Settings | Optional | P2 | Sound effects/Volume control |
| SCR-SETTING-009-display | Display Settings | Optional | P2 | Font size, etc. |
| SCR-SETTING-010-sync | Sync Settings | Optional | P1 | Cloud sync options |
| SCR-SETTING-011-help | Help Center | Optional | P1 | FAQ/Support |
| SCR-SETTING-012-feedback | Feedback | Optional | P2 | User feedback |
| SCR-SETTING-013-terms | Terms of Service | Optional | P1 | Legal document |
| SCR-SETTING-014-privacy-policy | Privacy Policy | Optional | P1 | Legal document |
| SCR-SETTING-015-licenses | License Information | Optional | P2 | Open source licenses |
| SCR-SETTING-016-password | Password Change | Optional | P1 | Password modification |
| SCR-SETTING-017-delete-account | Delete Account | Optional | P1 | Account deletion |
| SCR-SETTING-018-logout-confirm | Logout Confirmation | Optional | P1 | Logout dialog |

---

## Detailed Screen Design

### SCR-SETTING-001-main: Settings Main ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Entry page for settings functionality, presenting all settings options in grouped sections.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| header | Header | Title "Settings" |
| section_account | Section | Account section |
| cell_profile | Cell | Profile |
| cell_account | Cell | Account Settings |
| section_preferences | Section | Preferences section |
| cell_notification | Cell | Notification Settings |
| cell_language | Cell | Language Settings |
| cell_theme | Cell | Theme Settings |
| section_support | Section | Support section |
| cell_help | Cell | Help Center |
| cell_feedback | Cell | Feedback |
| section_about | Section | About section |
| cell_about | Cell | About |
| cell_terms | Cell | Terms of Service |
| cell_privacy | Cell | Privacy Policy |
| btn_logout | Button | Logout button |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_profile | Profile | Cell | SCR-PROFILE-001-view | - |
| cell_account | Account Settings | Cell | SCR-SETTING-002-account | - |
| cell_notification | Notification Settings | Cell | SCR-SETTING-005-notification | - |
| cell_language | Language Settings | Cell | SCR-SETTING-006-language | - |
| cell_theme | Theme Settings | Cell | SCR-SETTING-007-theme | - |
| cell_help | Help Center | Cell | SCR-SETTING-011-help | - |
| cell_feedback | Feedback | Cell | SCR-SETTING-012-feedback | - |
| cell_about | About | Cell | SCR-SETTING-004-about | - |
| cell_terms | Terms of Service | Cell | SCR-SETTING-013-terms | - |
| cell_privacy | Privacy Policy | Cell | SCR-SETTING-014-privacy-policy | - |
| btn_logout | Logout | Button | SCR-SETTING-018-logout-confirm | - |

---

### SCR-SETTING-002-account: Account Settings ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Account-related settings including Email, password, linked accounts, etc.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| cell_email | Cell | Email (display current email) |
| cell_password | Cell | Password Change |
| cell_linked_accounts | Cell | Linked Accounts |
| cell_delete_account | Cell | Delete Account |
| btn_back | Button | Back |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_password | Password Change | Cell | SCR-SETTING-016-password | - |
| cell_delete_account | Delete Account | Cell | SCR-SETTING-017-delete-account | - |
| btn_back | Back | Button | history.back() | - |

---

### SCR-SETTING-003-privacy: Privacy Settings ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Privacy-related settings including data sharing, tracking, visibility, etc.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| toggle_analytics | Toggle | Analytics data collection |
| toggle_personalization | Toggle | Personalized recommendations |
| toggle_profile_visibility | Toggle | Public profile |
| cell_data_download | Cell | Download my data |
| cell_privacy_policy | Cell | Privacy Policy |
| btn_back | Button | Back |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_privacy_policy | Privacy Policy | Cell | SCR-SETTING-014-privacy-policy | - |
| btn_back | Back | Button | history.back() | - |

---

### SCR-SETTING-004-about: About ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
App information page including version number, development team, legal information, etc.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_logo | Image | App Logo |
| lbl_app_name | Text | App Name |
| lbl_version | Text | Version Number |
| cell_terms | Cell | Terms of Service |
| cell_privacy | Cell | Privacy Policy |
| cell_licenses | Cell | License Information |
| lbl_copyright | Text | Copyright notice |
| btn_back | Button | Back |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_terms | Terms of Service | Cell | SCR-SETTING-013-terms | - |
| cell_privacy | Privacy Policy | Cell | SCR-SETTING-014-privacy-policy | - |
| cell_licenses | License Information | Cell | SCR-SETTING-015-licenses | - |
| btn_back | Back | Button | history.back() | - |

---

## Settings Grouping Recommendations

### Standard Grouping Structure

```
Settings Main
├── 👤 Account
│   ├── Profile
│   └── Account Settings
├── ⚙️ Preferences
│   ├── Notification Settings
│   ├── Language Settings
│   ├── Theme Settings
│   └── Sound Settings
├── 🔒 Privacy & Security
│   ├── Privacy Settings
│   └── Security Settings
├── ❓ Support
│   ├── Help Center
│   └── Feedback
├── ℹ️ About
│   ├── About
│   ├── Terms of Service
│   └── Privacy Policy
└── 🚪 Logout
```

---

## App Type Specific Settings

| App Type | Recommended Additional Settings |
|----------|--------------------------------|
| Education | Learning reminders, Daily goals, Voice speed |
| E-commerce | Payment methods, Shipping addresses, Order notifications |
| Social | Who can see me, Block list, Tag settings |
| Healthcare | Health data sync, Emergency contacts, Data encryption |
| Productivity | Sync settings, Backup settings, Shortcuts |

---

## Reference Source

This template is based on the SETTING module design from the VocabMaster project (18 screens).
