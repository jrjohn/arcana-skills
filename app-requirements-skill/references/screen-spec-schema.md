# Screen Specification Schema

This document defines the structured format for SCR-* blocks in SDD, allowing app-uiux-designer.skill to directly apply templates for UI Flow generation without prediction.

---

## Quick Reference

### SDD SCR-* Block Minimum Format

```markdown
## SCR-{MODULE}-{NNN}-{name}: {Screen Name}

**Screen Type:** {screen_type}
**Template:** {template_path}
**Module:** {MODULE}
**Priority:** P{0-2}

### Navigation
| Source | Target | Trigger |
|--------|--------|---------|
| SCR-AUTH-001 | this | Click register link |
| this | SCR-DASH-001 | Registration success |
| this | SCR-AUTH-001 | Click back |

### UI Elements
| ID | Type | Label | Action | Target |
|----|------|-------|--------|--------|
| email | TextField | Email | - | - |
| password | SecureField | Password | - | - |
| submit | Button.Primary | Register | Submit | SCR-DASH-001 |
| back | Button.Text | Back to Login | Navigate | SCR-AUTH-001 |
```

---

## Screen Types

Each Screen Type corresponds to a specific template in app-uiux-designer.skill.

| Screen Type | Template Path | Description | Required Elements |
|-------------|---------------|-------------|-------------------|
| `auth.login` | `screen-types/auth/login.html` | Login page | email, password, submit, forgot, register |
| `auth.register` | `screen-types/auth/register.html` | Registration page | name, email, password, confirm, terms, submit |
| `auth.forgot-password` | `screen-types/auth/forgot-password.html` | Forgot password | email, submit, back |
| `auth.forgot-sent` | `screen-types/auth/forgot-sent.html` | Sent confirmation | icon, message, resend, back |
| `auth.reset-password` | `screen-types/auth/reset-password.html` | Reset password | password, confirm, submit |
| `auth.verify-email` | `screen-types/auth/verify-email.html` | Email verification | icon, message, resend, change |
| `auth.role-select` | `screen-types/auth/role-select.html` | Role selection | roles[], submit |
| `dash.home` | `screen-types/dash/home.html` | Home page | header, content, tabbar |
| `dash.dashboard` | `screen-types/dash/dashboard.html` | Dashboard | stats[], charts[], actions[] |
| `list.standard` | `screen-types/list/standard.html` | Standard list | header, items[], empty_state |
| `list.grid` | `screen-types/list/grid.html` | Grid list | header, items[], filter |
| `detail.standard` | `screen-types/detail/standard.html` | Detail page | header, image, content, cta |
| `form.standard` | `screen-types/form/standard.html` | Standard form | header, fields[], submit |
| `form.multi-step` | `screen-types/form/multi-step.html` | Multi-step form | steps[], progress, nav |
| `setting.main` | `screen-types/setting/main.html` | Settings main page | sections[], items[], logout |
| `setting.toggle-list` | `screen-types/setting/toggle-list.html` | Toggle list | items[] with toggles |
| `setting.radio-list` | `screen-types/setting/radio-list.html` | Radio list | items[] with radio |
| `profile.view` | `screen-types/profile/view.html` | Profile view | avatar, info, actions[] |
| `profile.edit` | `screen-types/profile/edit.html` | Profile edit | avatar_upload, fields[] |
| `state.empty` | `screen-types/state/empty.html` | Empty state | icon, title, description, cta |
| `state.error` | `screen-types/state/error.html` | Error state | icon, title, description, retry |
| `state.loading` | `screen-types/state/loading.html` | Loading | spinner, message |
| `state.success` | `screen-types/state/success.html` | Success state | icon, title, description, cta |

---

## UI Element Types

### Input Elements

| Type | HTML Mapping | Properties |
|------|--------------|------------|
| `TextField` | `<input type="text">` | placeholder, validation |
| `TextField.Email` | `<input type="email">` | placeholder, validation |
| `TextField.Phone` | `<input type="tel">` | placeholder, format |
| `SecureField` | `<input type="password">` | placeholder, showToggle |
| `TextArea` | `<textarea>` | placeholder, rows |
| `NumberField` | `<input type="number">` | min, max, step |
| `DatePicker` | Date picker | minDate, maxDate |
| `TimePicker` | Time picker | format |
| `Select` | `<select>` | options[] |
| `Checkbox` | `<input type="checkbox">` | label |
| `Radio` | `<input type="radio">` | options[] |
| `Toggle` | Toggle switch | - |
| `Slider` | Range slider | min, max, step |
| `SearchField` | Search input | placeholder |

### Button Elements

| Type | Style | Use Case |
|------|-------|----------|
| `Button.Primary` | Primary button (filled) | Main CTA |
| `Button.Secondary` | Secondary button (bordered) | Secondary action |
| `Button.Text` | Text button | Link style |
| `Button.Icon` | Icon button | Toolbar |
| `Button.Floating` | FAB | Main add action |
| `Button.Social.Apple` | Apple login | Social login |
| `Button.Social.Google` | Google login | Social login |
| `Button.Social.Facebook` | Facebook login | Social login |

### Display Elements

| Type | Description |
|------|-------------|
| `Text.Title` | Large title |
| `Text.Subtitle` | Subtitle |
| `Text.Body` | Body text |
| `Text.Caption` | Caption text |
| `Text.Link` | Clickable link |
| `Image` | Image |
| `Icon` | SF Symbol / Material Icon |
| `Avatar` | Circular avatar |
| `Badge` | Badge/tag |
| `Divider` | Divider line |
| `Spacer` | Spacing |

### Container Elements

| Type | Description |
|------|-------------|
| `Card` | Card container |
| `Section` | Section |
| `List` | List container |
| `ListItem` | List item |
| `Grid` | Grid container |
| `TabBar` | Bottom tab bar |
| `Header` | Top navigation bar |
| `BottomSheet` | Bottom sheet |
| `Modal` | Dialog |

---

## Action Types

| Action | Description | Parameters |
|--------|-------------|------------|
| `Navigate` | Navigate to screen | Target: SCR-* |
| `Submit` | Submit form | Target: SCR-* (on success) |
| `Back` | Go back to previous page | - |
| `Dismiss` | Close Modal/Sheet | - |
| `External` | Open external link | URL |
| `Call` | Make phone call | PhoneNumber |
| `Email` | Send email | EmailAddress |
| `Share` | Share | - |
| `Copy` | Copy to clipboard | - |
| `Refresh` | Reload | - |
| `LoadMore` | Load more | - |
| `Toggle` | Toggle state | - |
| `Select` | Select item | - |
| `Delete` | Delete | Confirm: true/false |
| `Logout` | Logout | Target: SCR-AUTH-001 |

---

## Complete SDD Screen Spec Example

### Complete Example: Login Screen

```markdown
## SCR-AUTH-001-login: Login Screen

**Screen Type:** auth.login
**Template:** screen-types/auth/login.html
**Module:** AUTH
**Priority:** P0
**Related Requirements:** REQ-AUTH-001, REQ-AUTH-002

### Description
User login screen supporting Email/password login and social login.

### Navigation

| Direction | Screen | Trigger | Condition |
|-----------|--------|---------|-----------|
| ← From | SCR-LAUNCH-001 | App launch | Not logged in |
| → To | SCR-DASH-001 | Login success | Verification passed |
| → To | SCR-AUTH-002 | Click register | - |
| → To | SCR-AUTH-003 | Click forgot password | - |
| ↔ State | Error | Login failed | Verification error |

### UI Elements

| ID | Type | Label | Placeholder | Validation | Action | Target |
|----|------|-------|-------------|------------|--------|--------|
| logo | Image | - | - | - | - | - |
| title | Text.Title | Welcome Back | - | - | - | - |
| email | TextField.Email | Email | Enter your email | email_format | - | - |
| password | SecureField | Password | Enter your password | min_length:8 | - | - |
| remember | Checkbox | Remember me | - | - | - | - |
| submit | Button.Primary | Login | - | - | Submit | SCR-DASH-001 |
| forgot | Button.Text | Forgot password? | - | - | Navigate | SCR-AUTH-003 |
| divider | Divider | Or login with | - | - | - | - |
| apple | Button.Social.Apple | Sign in with Apple | - | - | Submit | SCR-DASH-001 |
| google | Button.Social.Google | Sign in with Google | - | - | Submit | SCR-DASH-001 |
| register | Button.Text | Don't have an account? Register | - | - | Navigate | SCR-AUTH-002 |

### Layout Structure

```
┌─────────────────────────────────────────┐
│                 HEADER                   │ (Logo + Title)
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ email                               │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ password                     [👁]  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [remember]              [forgot →]     │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │           Login (submit)           │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ──────────── or ────────────           │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ 🍎 Sign in with Apple             │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ G  Sign in with Google            │ │
│  └────────────────────────────────────┘ │
│                                          │
│      Don't have an account? Register    │
│                                          │
└─────────────────────────────────────────┘
```

### States

| State | Trigger | UI Changes |
|-------|---------|------------|
| Default | Initial load | All fields empty |
| Loading | Click login | submit button disabled + spinner |
| Error | Verification failed | Show error message, email/password red border |
| Success | Verification passed | Navigate to SCR-DASH-001 |

### Error Messages

| Error | Message |
|-------|---------|
| INVALID_EMAIL | Please enter a valid email address |
| WRONG_PASSWORD | Incorrect password, please try again |
| USER_NOT_FOUND | This account is not registered |
| ACCOUNT_LOCKED | Account locked, please try again later |
| NETWORK_ERROR | Network connection failed, please check your connection |
```

---

## Integration Workflow

### When app-requirements-skill Generates SDD

1. **Identify screen type** → Select from Screen Types table
2. **Specify template** → Corresponding template path
3. **Define navigation** → Source/target screens
4. **List UI elements** → Use standard Types
5. **Specify actions** → Use standard Action Types
6. **Describe states** → Loading/Error/Success

### When app-uiux-designer.skill Generates UI Flow

1. **Read Screen Type** → Load corresponding template
2. **Apply UI Elements** → Replace template variables
3. **Set Navigation** → Generate onclick/href
4. **Generate States** → Generate state variants
5. **Apply Theme** → Use project Design Token

```
app-requirements-skill                app-uiux-designer.skill
┌────────────────────┐               ┌────────────────────┐
│ SDD with           │               │                    │
│ Screen Spec Schema │ ─────────────▶│ Load Template      │
│                    │               │ ↓                  │
│ Screen Type: X     │               │ Replace Variables  │
│ Template: path     │               │ ↓                  │
│ UI Elements: [...]  │               │ Set Navigation     │
│ Navigation: [...]   │               │ ↓                  │
│ States: [...]       │               │ Generate HTML      │
└────────────────────┘               └────────────────────┘
                                              ↓
                                     ┌────────────────────┐
                                     │ 04-ui-flow/        │
                                     │ ├ auth/            │
                                     │ │ └ SCR-AUTH-001.html│
                                     │ └ iphone/          │
                                     │   └ SCR-AUTH-001.html│
                                     └────────────────────┘
```

---

## Validation Checklist

Validate before app-requirements-skill generates SDD:

```
☐ Each SCR-* block has a Screen Type
☐ Each SCR-* block has a Template path
☐ Each UI Element uses a standard Type
☐ Each Action uses a standard Action Type
☐ Each Navigate Action has a valid Target SCR-*
☐ Navigation table covers all entry/exit screens
☐ States include Default/Loading/Error (if applicable)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial version - Screen Spec Schema definition |
