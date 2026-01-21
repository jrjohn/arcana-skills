# COMMON States Module Template (Common States Module)

Standard definitions for shared state screens. **All Apps must include** these state screens to provide a complete user experience.

---

## Module Overview

| Item | Value |
|------|-------|
| Module Code | COMMON |
| Necessity | **Required** |
| Minimum Screens | 4 |
| Complete Screens | 5 |
| Related Requirements | REQ-COMMON-* |

---

## Standard Screen List

| Screen ID | Name | Necessity | Priority | Usage |
|-----------|------|-----------|----------|-------|
| SCR-COMMON-001-loading | Loading State | **Required** | P0 | API call waiting |
| SCR-COMMON-002-empty | Empty State | **Required** | P0 | Display when no data |
| SCR-COMMON-003-error | Error State | **Required** | P0 | Operation failed |
| SCR-COMMON-004-no-network | No Network State | **Required** | P0 | Display when offline |
| SCR-COMMON-005-confirm | Confirmation Dialog | Optional | P1 | Important action confirmation |

---

## Detailed Screen Design

### SCR-COMMON-001-loading: Loading State ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Displayed during API calls or data loading, providing visual feedback to let users know the system is processing.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| spinner | ActivityIndicator | Spinning loading animation |
| lbl_message | Text | Loading hint text (optional) |
| progress_bar | ProgressBar | Progress bar (optional) |

**Design Specifications:**

| Item | Specification |
|------|---------------|
| Background | Semi-transparent overlay or full screen |
| Animation | Rotation or pulse effect |
| Hint Text | "Loading..." or specific description |
| Timeout Handling | Show retry option after 10 seconds |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_cancel | Cancel | Button | history.back() | Cancellable operation |

**CSS Animation Example:**

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

---

### SCR-COMMON-002-empty: Empty State ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Displayed when a list or content area has no data, guiding users to take action.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_illustration | Image | Empty state illustration |
| lbl_title | Text | Title (e.g., "No Data Yet") |
| lbl_description | Text | Description text |
| btn_action | Button | Primary action button |

**Design Specifications:**

| Item | Specification |
|------|---------------|
| Illustration | Friendly, lightweight SVG illustration |
| Title | Briefly describe current state |
| Description | Guide user to next step |
| Button | Provide solution (e.g., "Add") |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_action | Add | Button | (Add screen) | Based on content type |
| btn_refresh | Refresh | Button | (current) | Refresh list |

**Empty State Copy Examples:**

| Scenario | Title | Description | Button |
|----------|-------|-------------|--------|
| Vocabulary List | No Vocabularies Yet | Create your first vocabulary to start learning | Add Vocabulary |
| Friends List | No Friends Yet | Invite friends to learn together | Invite Friends |
| Search Results | No Results Found | Try different keywords | Clear Search |
| Notification List | No Notifications | New messages will appear here | - |

---

### SCR-COMMON-003-error: Error State ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Displayed when an operation fails or an error occurs, providing retry or report options.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_error | Image | Error illustration |
| lbl_title | Text | Error title |
| lbl_message | Text | Error description |
| btn_retry | Button | Retry button |
| btn_back | Button | Back button |
| lnk_report | Link | Report issue (optional) |

**Design Specifications:**

| Item | Specification |
|------|---------------|
| Illustration | Friendly but conveys the problem |
| Title | Don't just say "Error", explain what happened |
| Description | Provide possible solutions |
| Button | Retry or go back |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_retry | Retry | Button | (current) | Re-execute operation |
| btn_back | Back | Button | history.back() | - |
| lnk_report | Report Issue | Link | SCR-SETTING-012-feedback | - |

**Error Types and Copy:**

| Error Type | Title | Description |
|------------|-------|-------------|
| Server Error | System Temporarily Unavailable | Please try again later |
| Permission Denied | Cannot Access This Content | Please verify your account permissions |
| Validation Failed | Operation Cannot Be Completed | Please log in again and retry |
| Unknown Error | Something Went Wrong | Please retry or contact support |

---

### SCR-COMMON-004-no-network: No Network State ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Displayed when the device is offline or network connection is interrupted.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| img_offline | Image | Offline illustration (cloud with X) |
| lbl_title | Text | "Network Connection Lost" |
| lbl_message | Text | Description text |
| btn_retry | Button | Retry Connection |
| lbl_offline_mode | Text | Offline mode description (optional) |

**Design Specifications:**

| Item | Specification |
|------|---------------|
| Illustration | Clearly conveys network issue |
| Offline Features | Describe which features work offline |
| Retry | Provide retry button |
| Auto Detection | Auto refresh when network recovers |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_retry | Retry Connection | Button | (current) | Check network then retry |
| btn_offline | Offline Mode | Button | (offline home) | When offline features supported |

---

### SCR-COMMON-005-confirm: Confirmation Dialog

**Necessity:** Optional (recommended to include)

**Screen Description:**
Confirmation dialog before important operations like delete, logout, etc.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| lbl_title | Text | Confirmation title |
| lbl_message | Text | Confirmation description |
| btn_confirm | Button | Confirm button (red for dangerous actions) |
| btn_cancel | Button | Cancel button |

**Design Specifications:**

| Item | Specification |
|------|---------------|
| Title | Clearly state the action to confirm |
| Description | Remind of action consequences |
| Button Order | Cancel on left, Confirm on right |
| Dangerous Action | Confirm button in red |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_confirm | Confirm | Button | (post-action target) | Operation complete |
| btn_cancel | Cancel | Button | (close modal) | - |

**Common Confirmation Scenarios:**

| Scenario | Title | Description | Confirm Button |
|----------|-------|-------------|----------------|
| Delete Item | Are you sure you want to delete? | This action cannot be undone | Delete (red) |
| Logout | Are you sure you want to logout? | You will need to log in again | Logout |
| Cancel Edit | Discard changes? | Unsaved changes will be lost | Discard |
| Purchase Confirmation | Confirm purchase? | Will deduct XX coins | Confirm Purchase |

---

## State Screen Usage Guide

### When to Use

| State | When to Use |
|-------|-------------|
| Loading | API calls, Data loading, File uploads |
| Empty | Empty lists, No search results, First-time use |
| Error | API errors, Operation failures, Validation failures |
| No Network | Network interruption, Offline state |
| Confirm | Delete, Logout, Irreversible operations |

### Design Principles

1. **Friendly Tone** - Don't blame the user
2. **Clear Explanation** - Tell users what happened
3. **Provide Exit** - Give users next action
4. **Consistent Style** - All state screens have consistent style

---

## Reference Source

This template is based on the COMMON module design from the VocabMaster project, compliant with iOS Human Interface Guidelines and Material Design 3 state screen specifications.
