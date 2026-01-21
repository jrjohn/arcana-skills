# PROFILE Module Template (Profile Module)

Standard screen definitions for the Profile module, applicable to all Apps requiring user data management.

---

## Module Overview

| Item | Value |
|------|-------|
| Module Code | PROFILE |
| Necessity | **Required** |
| Minimum Screens | 2 |
| Complete Screens | 3 |
| Related Requirements | REQ-PROFILE-* |

---

## Standard Screen List

| Screen ID | Name | Necessity | Priority | Description |
|-----------|------|-----------|----------|-------------|
| SCR-PROFILE-001-view | Profile View | **Required** | P0 | Display user data |
| SCR-PROFILE-002-edit | Profile Edit | **Required** | P0 | Edit user data |
| SCR-PROFILE-003-avatar | Avatar Selection | Optional | P1 | Change avatar |

---

## Detailed Screen Design

### SCR-PROFILE-001-view: Profile View ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Displays user's profile information including avatar, name, and basic info.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_avatar | Image | User avatar |
| lbl_name | Text | User name |
| lbl_email | Text | Email (partially hidden) |
| lbl_join_date | Text | Join date |
| section_stats | Section | Statistics section |
| btn_edit | Button | Edit button |
| btn_back | Button | Back button |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_edit | Edit | Button | SCR-PROFILE-002-edit | - |
| btn_back | Back | Button | history.back() | - |
| img_avatar | (Tap avatar) | Image | SCR-PROFILE-003-avatar | - |

---

### SCR-PROFILE-002-edit: Profile Edit ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Edit user's profile information including name, avatar, preferences, etc.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_avatar | Image | User avatar (tappable to change) |
| btn_change_avatar | Button | Change avatar button |
| txt_name | TextField | Name input field |
| txt_nickname | TextField | Nickname input field (optional) |
| txt_bio | TextArea | Bio (optional) |
| picker_birthday | DatePicker | Birthday picker (optional) |
| picker_gender | Picker | Gender picker (optional) |
| btn_save | Button | Save button |
| btn_cancel | Button | Cancel button |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_change_avatar | Change Avatar | Button | SCR-PROFILE-003-avatar | - |
| btn_save | Save | Button | SCR-PROFILE-001-view | Save success |
| btn_cancel | Cancel | Button | history.back() | - |

---

### SCR-PROFILE-003-avatar: Avatar Selection

**Necessity:** Optional

**Screen Description:**
Select or upload user avatar.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_current | Image | Current avatar |
| grid_presets | Grid | Preset avatar options |
| btn_camera | Button | Take Photo |
| btn_gallery | Button | Choose from Gallery |
| btn_save | Button | Confirm Selection |
| btn_cancel | Button | Cancel |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_camera | Take Photo | Button | (System Camera) | - |
| btn_gallery | Choose from Gallery | Button | (System Gallery) | - |
| btn_save | Confirm | Button | history.back() | Avatar updated |
| btn_cancel | Cancel | Button | history.back() | - |

---

## Extension Screens (Optional)

Based on App type, the following screens can be extended:

| Screen ID | Name | Applicable Scenario |
|-----------|------|---------------------|
| SCR-PROFILE-004-settings | Personal Preferences | Education Apps |
| SCR-PROFILE-005-security | Security Settings | Finance/Healthcare Apps |
| SCR-PROFILE-006-badges | Achievement Badges | Gamified Apps |
| SCR-PROFILE-007-history | Activity History | E-commerce/Social Apps |

---

## Reference Source

This template is based on the PROFILE module design from the VocabMaster project.
