# AUTH Module Template (Authentication Module)

Standard screen definitions for the Authentication module, applicable to all Apps requiring user login.

---

## Module Overview

| Item | Value |
|------|-------|
| Module Code | AUTH |
| Necessity | **Required** |
| Minimum Screens | 3 |
| Complete Screens | 8 |
| Related Requirements | REQ-AUTH-* |

---

## Standard Screen List

| Screen ID | Name | Necessity | Priority | Description |
|-----------|------|-----------|----------|-------------|
| SCR-AUTH-001-welcome | Welcome Page | Optional | P1 | First-time onboarding page |
| SCR-AUTH-002-login | Login Page | **Required** | P0 | Email/Social login |
| SCR-AUTH-003-register | Register Page | **Required** | P0 | New user registration |
| SCR-AUTH-004-forgot | Forgot Password | **Required** | P0 | Password reset entry |
| SCR-AUTH-005-verify | Verification Code | Optional | P1 | Email/SMS verification |
| SCR-AUTH-006-reset-sent | Reset Email Sent | Optional | P2 | Confirmation message page |
| SCR-AUTH-007-role | Role Selection | Optional | P1 | For multi-role Apps |
| SCR-AUTH-008-pin | PIN Verification | Optional | P1 | Parent/Admin verification |

---

## Detailed Screen Design

### SCR-AUTH-001-welcome: Welcome Page

**Necessity:** Optional (recommended for first-time installation)

**Screen Description:**
Onboarding page displayed when the App is first opened, showcasing product features and value proposition.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| app_logo | Image | App Logo icon |
| welcome_title | Text | Welcome title |
| welcome_description | Text | Product description text |
| btn_start | Button | Get Started button |
| lnk_login | Link | Already have an account? Login |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_start | Get Started | Button | SCR-AUTH-003-register | - |
| lnk_login | Already have an account? Login | Link | SCR-AUTH-002-login | - |

---

### SCR-AUTH-002-login: Login Page ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
User login page supporting Email/password login and social account login.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| txt_email | TextField | Email input field |
| txt_password | SecureField | Password input field (masked) |
| btn_login | Button | Login button |
| btn_apple | Button | Apple ID login |
| btn_google | Button | Google login (optional) |
| lnk_forgot | Link | Forgot Password? |
| lnk_register | Link | Register Now |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Login | Button | SCR-HOME-001-main | Validation success |
| btn_apple | Apple Login | Button | SCR-HOME-001-main | Apple login success |
| btn_google | Google Login | Button | SCR-HOME-001-main | Google login success |
| lnk_forgot | Forgot Password? | Link | SCR-AUTH-004-forgot | - |
| lnk_register | Register Now | Link | SCR-AUTH-003-register | - |

---

### SCR-AUTH-003-register: Register Page ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
New user registration page, collecting necessary account information.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| txt_name | TextField | Name input field |
| txt_email | TextField | Email input field |
| txt_password | SecureField | Password input field |
| txt_confirm | SecureField | Confirm password input field |
| chk_terms | Checkbox | Agree to terms |
| btn_register | Button | Register button |
| lnk_login | Link | Already have an account? Login |
| lnk_terms | Link | Terms of Service |
| lnk_privacy | Link | Privacy Policy |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_register | Register | Button | SCR-AUTH-005-verify | Verification needed |
| btn_register | Register | Button | SCR-HOME-001-main | Direct pass |
| lnk_login | Already have an account? Login | Link | SCR-AUTH-002-login | - |
| lnk_terms | Terms of Service | Link | SCR-SETTING-*-terms | - |
| lnk_privacy | Privacy Policy | Link | SCR-SETTING-*-privacy | - |

---

### SCR-AUTH-004-forgot: Forgot Password ⚠️ Required

**Necessity:** **Required**

**Screen Description:**
Password reset request page.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| txt_email | TextField | Email input field |
| btn_send | Button | Send Reset Email |
| btn_back | Button | Back to Login |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_send | Send Reset Email | Button | SCR-AUTH-006-reset-sent | Send success |
| btn_back | Back to Login | Button | SCR-AUTH-002-login | - |

---

### SCR-AUTH-005-verify: Verification Code

**Necessity:** Optional

**Screen Description:**
Email or SMS verification code input page.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| lbl_instruction | Text | Verification instruction text |
| txt_code | TextField | Verification code input (6 digits) |
| btn_verify | Button | Verify button |
| btn_resend | Button | Resend |
| btn_back | Button | Back |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_verify | Verify | Button | SCR-HOME-001-main | Verification success |
| btn_resend | Resend | Button | (current) | Show countdown timer |
| btn_back | Back | Button | history.back() | - |

---

### SCR-AUTH-006-reset-sent: Reset Email Sent

**Necessity:** Optional

**Screen Description:**
Confirmation page after password reset email is successfully sent.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| icon_success | Image | Success icon |
| lbl_title | Text | Email Sent |
| lbl_instruction | Text | Please check your inbox |
| btn_login | Button | Back to Login |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Back to Login | Button | SCR-AUTH-002-login | - |

---

### SCR-AUTH-007-role: Role Selection

**Necessity:** Optional (for multi-role Apps)

**Screen Description:**
Select user role after login (e.g., Student/Parent, Buyer/Seller).

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| lbl_title | Text | Please select your identity |
| btn_role_1 | Button | Role 1 (e.g., Student) |
| btn_role_2 | Button | Role 2 (e.g., Parent) |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_role_1 | Student | Button | SCR-HOME-001-student | - |
| btn_role_2 | Parent | Button | SCR-HOME-001-parent | May require PIN |

---

### SCR-AUTH-008-pin: PIN Verification

**Necessity:** Optional (for parental control or admin features)

**Screen Description:**
PIN verification page to protect sensitive features.

**UI Components:**

| Component | Type | Description |
|-----------|------|-------------|
| lbl_title | Text | Please enter PIN |
| txt_pin | SecureField | 4-6 digit PIN |
| btn_verify | Button | Confirm |
| btn_cancel | Button | Cancel |
| lnk_forgot | Link | Forgot PIN? |

**Button Navigation:**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_verify | Confirm | Button | (target screen) | PIN correct |
| btn_cancel | Cancel | Button | history.back() | - |
| lnk_forgot | Forgot PIN? | Link | (reset flow) | - |

---

## Reference Source

This template is based on the AUTH module design from the VocabMaster project, verified to support:
- Email/password login
- Apple ID login
- Google login (optional)
- Multi-role switching
- Parental PIN protection
