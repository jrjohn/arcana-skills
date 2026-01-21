# Standard App Requirements Checklist

This document provides an industry-standard App requirements checklist for reference during requirements analysis, ensuring no basic functionality is overlooked.

---

## Quick Reference - Requirements Estimation

### Standard App Base Requirements Count

| Module | Requirement Count | Necessity |
|--------|-------------------|-----------|
| Authentication (AUTH) | 8-12 | ★★★ |
| Profile (PROFILE) | 4-6 | ★★★ |
| Settings (SETTING) | 6-10 | ★★★ |
| Onboarding | 2-4 | ★★☆ |
| Notifications | 3-5 | ★★☆ |
| Help & Support | 3-5 | ★☆☆ |
| Legal Compliance | 2-3 | ★★★ |
| Non-Functional Requirements | 8-15 | ★★★ |
| **Base Total** | **36-60** | - |

### Additional Requirements by App Type

| App Type | Additional Reqs | Description |
|----------|-----------------|-------------|
| E-commerce | +30~50 | Shopping cart, checkout, orders, payment |
| Social | +20~40 | Friends, posts, interactions, messaging |
| Content | +15~25 | Browse, favorites, search, recommendations |
| Booking | +15~30 | Reservations, calendar, reminders |
| Utility | +10~20 | Core features (varies by App) |

---

## 1. Authentication Requirements (REQ-AUTH-*)

### 1.1 Basic Authentication

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-AUTH-001 | User Login | Login using Email/password | P0 |
| REQ-AUTH-002 | User Registration | Create new account (Email, password, basic info) | P0 |
| REQ-AUTH-003 | Forgot Password | Send password reset link via Email | P0 |
| REQ-AUTH-004 | Password Reset | Set new password via link | P0 |
| REQ-AUTH-005 | Email Verification | Verify user Email authenticity | P1 |
| REQ-AUTH-006 | Logout | End login session | P0 |
| REQ-AUTH-007 | Session Management | Token expiration, auto-logout, stay logged in | P0 |

### 1.2 Social Login

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-AUTH-010 | Apple Sign-In | iOS App Store required (if other social logins exist) | P0 (iOS) |
| REQ-AUTH-011 | Google Sign-In | Google account login | P1 |
| REQ-AUTH-012 | Facebook Login | Facebook account login | P2 |
| REQ-AUTH-013 | LINE Login | LINE account login (Taiwan market) | P2 |

> ⚠️ **iOS App Store Rule**: If providing any third-party login, Sign in with Apple must also be provided

### 1.3 Advanced Authentication

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-AUTH-020 | Biometric Login | Face ID / Touch ID / Fingerprint quick login | P1 |
| REQ-AUTH-021 | Two-Factor Auth (MFA) | SMS OTP / Email OTP / Authenticator App | P1 |
| REQ-AUTH-022 | Backup Codes | MFA backup verification codes | P2 |
| REQ-AUTH-023 | App Lock | Require identity verification to open App | P2 |
| REQ-AUTH-024 | Device Management | View/logout logged-in devices | P2 |
| REQ-AUTH-025 | Login History | Login history records (time, device, location) | P3 |

### 1.4 Acceptance Criteria (ACC)

```markdown
REQ-AUTH-001 User Login:
- ACC-001: After entering correct Email/password, successfully login and redirect to home
- ACC-002: Incorrect password shows error prompt and retains Email field content
- ACC-003: Non-existent account shows "This account is not registered" error
- ACC-004: Password input field supports show/hide toggle
- ACC-005: After 5 consecutive failures, lock account for 15 minutes

REQ-AUTH-002 User Registration:
- ACC-001: Successfully create account after filling required fields
- ACC-002: Invalid Email format shows real-time validation error
- ACC-003: Weak password shows prompt and prevents submission
- ACC-004: Existing Email shows "This Email is already registered"
- ACC-005: Terms of service must be checked before submission
```

---

## 2. Profile Requirements (REQ-PROFILE-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-PROFILE-001 | View Profile | Display user basic info | P0 |
| REQ-PROFILE-002 | Edit Profile | Modify name, phone, and other editable fields | P0 |
| REQ-PROFILE-003 | Upload Avatar | Select from gallery or take photo to upload avatar | P1 |
| REQ-PROFILE-004 | Crop Avatar | Crop and scale avatar image | P2 |
| REQ-PROFILE-005 | Change Email | Modify login Email (requires verification) | P1 |
| REQ-PROFILE-006 | Change Password | Modify login password | P0 |
| REQ-PROFILE-007 | Delete Account | Permanently delete account and all data | P1 |

### 2.1 Acceptance Criteria (ACC)

```markdown
REQ-PROFILE-002 Edit Profile:
- ACC-001: After modifying name and saving, show updated info
- ACC-002: Empty required field shows error prompt
- ACC-003: Field exceeding length limit shows error
- ACC-004: Successful save shows success prompt

REQ-PROFILE-007 Delete Account:
- ACC-001: Show confirmation dialog before deletion
- ACC-002: Require password input to confirm identity
- ACC-003: After deletion, clear local data and redirect to login page
- ACC-004: Account recoverable within 30 days by contacting support (optional)
```

---

## 3. Settings Requirements (REQ-SETTING-*)

### 3.1 Notification Settings

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-SETTING-001 | Push Notification Master Toggle | Enable/disable all push notifications | P0 |
| REQ-SETTING-002 | Notification Type Settings | Individual toggles for each notification type | P1 |
| REQ-SETTING-003 | Do Not Disturb | Set nighttime do-not-disturb period | P2 |
| REQ-SETTING-004 | Email Notifications | Set Email notification preferences | P2 |

### 3.2 Privacy Settings

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-SETTING-010 | Profile Visibility | Set profile public visibility scope | P2 |
| REQ-SETTING-011 | Data Collection Consent | Analytics data collection preferences | P1 |
| REQ-SETTING-012 | Ad Tracking Settings | Personalized ad preferences | P2 |
| REQ-SETTING-013 | Download My Data | GDPR requirement - Export personal data | P1 |
| REQ-SETTING-014 | Block List Management | View/unblock users (social apps) | P2 |

### 3.3 Appearance Settings

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-SETTING-020 | Theme Toggle | Light/Dark/Follow system | P1 |
| REQ-SETTING-021 | Text Size | Adjust App text size | P2 |
| REQ-SETTING-022 | Language Setting | Switch App interface language | P1 |

### 3.4 Account Security

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-SETTING-030 | Change Password | Same as REQ-PROFILE-006 | P0 |
| REQ-SETTING-031 | MFA Management | Enable/disable/manage MFA | P1 |
| REQ-SETTING-032 | Biometric Settings | Enable/disable Face ID/Touch ID | P1 |
| REQ-SETTING-033 | App Lock Settings | Set App open verification | P2 |

---

## 4. Onboarding Requirements (REQ-ONBOARD-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-ONBOARD-001 | Welcome Screens | Show feature introduction on first use (3-5 pages) | P1 |
| REQ-ONBOARD-002 | Skip Onboarding | Allow skipping introduction to enter directly | P1 |
| REQ-ONBOARD-003 | Permission Request Explanation | Explain purpose before requesting permissions | P0 |
| REQ-ONBOARD-004 | Personalization Setup | First-time preference setup (optional) | P2 |

### 4.1 Permission Requests

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-ONBOARD-010 | Notification Permission | Request push notification permission | P0 |
| REQ-ONBOARD-011 | Location Permission | Request location access (if needed) | P1 |
| REQ-ONBOARD-012 | Camera Permission | Request camera access (if needed) | P1 |
| REQ-ONBOARD-013 | Photo Library Permission | Request photo library access (if needed) | P1 |
| REQ-ONBOARD-014 | Tracking Permission | ATT permission (iOS 14.5+) | P0 (iOS) |

> ⚠️ **iOS App Tracking Transparency (ATT)**: iOS 14.5+ requires tracking permission to use IDFA

---

## 5. Notification Requirements (REQ-NOTIFY-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-NOTIFY-001 | Notification List | Display all notification records | P1 |
| REQ-NOTIFY-002 | Read/Unread Marking | Distinguish read/unread notifications | P1 |
| REQ-NOTIFY-003 | Mark All Read | One-click mark all notifications as read | P2 |
| REQ-NOTIFY-004 | Delete Notifications | Delete single or multiple notifications | P2 |
| REQ-NOTIFY-005 | Notification Categories | Display notifications by category | P3 |
| REQ-NOTIFY-006 | Notification Badge | Show unread count on App icon | P1 |

---

## 6. Help & Support Requirements (REQ-HELP-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-HELP-001 | Help Center | FAQ category entry | P1 |
| REQ-HELP-002 | FAQ Search | Search frequently asked questions | P2 |
| REQ-HELP-003 | Contact Support | Support contact methods (online/Email/phone) | P1 |
| REQ-HELP-004 | Feedback | Submit feedback or bug reports | P1 |
| REQ-HELP-005 | App Rating | Guide to App Store/Play Store rating | P2 |

---

## 7. Legal Compliance Requirements (REQ-LEGAL-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-LEGAL-001 | Terms of Service Display | View complete terms of service | P0 |
| REQ-LEGAL-002 | Privacy Policy Display | View complete privacy policy | P0 |
| REQ-LEGAL-003 | Consent Record | Record user consent time and version | P0 |
| REQ-LEGAL-004 | Terms Update Notification | Notify users of terms updates | P1 |
| REQ-LEGAL-005 | Cookie Policy | Web version cookie usage description | P1 (Web) |

### 7.1 GDPR/CCPA Compliance (if applicable)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-LEGAL-010 | Data Portability | User can download all their data | P1 |
| REQ-LEGAL-011 | Right to be Forgotten | User can request deletion of all data | P1 |
| REQ-LEGAL-012 | Data Processing Consent | Clear data processing purpose and consent mechanism | P0 |
| REQ-LEGAL-013 | Withdraw Consent | User can withdraw data processing consent anytime | P1 |

---

## 8. Non-Functional Requirements (REQ-NFR-*)

### 8.1 Performance Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-001 | Screen Load Time | First load < 3s, subsequent < 2s | P0 |
| REQ-NFR-002 | API Response Time | 95% requests < 500ms | P0 |
| REQ-NFR-003 | Launch Time | Cold start < 3s, warm start < 1s | P1 |
| REQ-NFR-004 | Scroll Smoothness | 60 fps | P1 |
| REQ-NFR-005 | Memory Usage | Background < 50MB | P2 |
| REQ-NFR-006 | Battery Consumption | No continuous drain in background | P1 |

### 8.2 Security Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-010 | HTTPS Communication | All API use TLS 1.2+ | P0 |
| REQ-NFR-011 | Token Security | JWT Token stored in secure storage | P0 |
| REQ-NFR-012 | Password Encryption | Server-side bcrypt/Argon2 | P0 |
| REQ-NFR-013 | Sensitive Data Encryption | Local sensitive data encrypted | P0 |
| REQ-NFR-014 | Certificate Pinning | Prevent man-in-the-middle attacks | P1 |
| REQ-NFR-015 | Prevent Screenshots | Prohibit screenshots on sensitive screens (optional) | P3 |
| REQ-NFR-016 | Jailbreak/Root Detection | Alert security risk | P2 |

### 8.3 Availability Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-020 | Offline Mode | Basic features available offline | P1 |
| REQ-NFR-021 | Network Error Handling | Friendly error prompt + retry mechanism | P0 |
| REQ-NFR-022 | Server Error Handling | Friendly error prompt | P0 |
| REQ-NFR-023 | Loading State Display | Appropriate loading indicators | P0 |
| REQ-NFR-024 | Empty State Display | Guidance screen when no data | P1 |

### 8.4 Accessibility Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-030 | VoiceOver Support | iOS screen reader support | P1 |
| REQ-NFR-031 | TalkBack Support | Android screen reader support | P1 |
| REQ-NFR-032 | Dynamic Type Support | Support system font size settings | P1 |
| REQ-NFR-033 | Color Contrast Ratio | WCAG 2.1 AA standard (4.5:1) | P1 |
| REQ-NFR-034 | Touch Target Size | Minimum 44x44pt / 48x48dp | P1 |

### 8.5 Compatibility Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-040 | iOS Version | iOS 15.0+ (recommend 14.0+) | P0 |
| REQ-NFR-041 | Android Version | Android 8.0+ (API 26+) | P0 |
| REQ-NFR-042 | Device Support | iPhone, iPad, Android Phone/Tablet | P0 |
| REQ-NFR-043 | Screen Adaptation | Support various screen sizes and orientations | P0 |

### 8.6 Internationalization Requirements

| REQ ID | Requirement Name | Specification | Priority |
|--------|------------------|---------------|----------|
| REQ-NFR-050 | Multi-language Support | Traditional Chinese, Simplified Chinese, English (as needed) | P1 |
| REQ-NFR-051 | Date Format | Display local format based on locale | P1 |
| REQ-NFR-052 | Number Format | Display thousands separator/decimal based on locale | P2 |
| REQ-NFR-053 | RTL Support | Arabic/Hebrew (if needed) | P3 |

---

## 9. Search Requirements (REQ-SEARCH-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-SEARCH-001 | Basic Search | Keyword search functionality | P1 |
| REQ-SEARCH-002 | Search Suggestions | Show autocomplete suggestions while typing | P2 |
| REQ-SEARCH-003 | Search History | Record and display search history | P2 |
| REQ-SEARCH-004 | Popular Searches | Display popular search keywords | P3 |
| REQ-SEARCH-005 | Filter & Sort | Search result filtering and sorting | P1 |
| REQ-SEARCH-006 | Clear History | Clear search history | P2 |

---

## 10. State Screen Requirements (REQ-STATE-*)

| REQ ID | Requirement Name | Description | Priority |
|--------|------------------|-------------|----------|
| REQ-STATE-001 | Loading State | Display Spinner/Skeleton while loading | P0 |
| REQ-STATE-002 | Empty State | Display guidance screen when no data | P0 |
| REQ-STATE-003 | Error State | Display friendly prompt + retry on error | P0 |
| REQ-STATE-004 | Network Error | Display offline prompt when no network | P0 |
| REQ-STATE-005 | Server Error | Display system busy prompt on 5xx errors | P0 |
| REQ-STATE-006 | Pull to Refresh | Pull down to reload | P1 |
| REQ-STATE-007 | Infinite Scroll | Auto-load more when scrolling to bottom | P1 |

---

## Appendix A: Requirements to Screen Mapping

| REQ ID | Corresponding Screen (SCR ID) |
|--------|-------------------------------|
| REQ-AUTH-001 | SCR-AUTH-001-login |
| REQ-AUTH-002 | SCR-AUTH-002-register |
| REQ-AUTH-003 | SCR-AUTH-003-forgot-password |
| REQ-AUTH-004 | SCR-AUTH-004-reset-password |
| REQ-AUTH-005 | SCR-AUTH-005-verify-email |
| REQ-AUTH-010 | SCR-AUTH-001-login (social login section) |
| REQ-AUTH-020 | SCR-AUTH-008-biometric |
| REQ-AUTH-021 | SCR-AUTH-006-mfa |
| REQ-PROFILE-001 | SCR-PROFILE-001-view |
| REQ-PROFILE-002 | SCR-PROFILE-002-edit |
| REQ-PROFILE-003 | SCR-PROFILE-003-avatar |
| REQ-SETTING-001~004 | SCR-SETTING-002-notifications |
| REQ-SETTING-010~014 | SCR-SETTING-003-privacy |
| REQ-SETTING-020~022 | SCR-SETTING-004-appearance |
| REQ-ONBOARD-001~002 | SCR-ONBOARD-001~003 |
| REQ-ONBOARD-010~014 | SCR-ONBOARD-004-permissions |
| REQ-NOTIFY-001~006 | SCR-NOTIFY-001-list |
| REQ-HELP-001~002 | SCR-HELP-001-center |
| REQ-HELP-003 | SCR-HELP-003-contact |
| REQ-HELP-004 | SCR-HELP-004-feedback |
| REQ-LEGAL-001 | SCR-LEGAL-001-terms |
| REQ-LEGAL-002 | SCR-LEGAL-002-privacy |
| REQ-STATE-001 | SCR-STATE-001-loading |
| REQ-STATE-002 | SCR-STATE-002-empty |
| REQ-STATE-003~005 | SCR-STATE-003-no-internet, SCR-STATE-004-server-error |

---

## Appendix B: Priority Definitions

| Priority | Definition | Description |
|----------|------------|-------------|
| P0 | Critical | Cannot publish/use without this feature |
| P1 | High | Standard feature, strongly recommended |
| P2 | Medium | Improves user experience |
| P3 | Low | Nice to have |

---

## Appendix C: Requirements Checklist

### C.1 Pre-launch Required Checklist

- [ ] REQ-AUTH-001~007 Complete basic authentication flow
- [ ] REQ-AUTH-010 Apple Sign-In (if social login exists)
- [ ] REQ-PROFILE-001~002 Basic profile features
- [ ] REQ-LEGAL-001~003 Legal documents and consent records
- [ ] REQ-NFR-010~013 Basic security requirements
- [ ] REQ-NFR-030~034 Basic accessibility support
- [ ] REQ-STATE-001~005 Complete state screens

### C.2 GDPR Compliance Checklist (EU Users)

- [ ] REQ-LEGAL-010 Data Portability
- [ ] REQ-LEGAL-011 Right to be Forgotten
- [ ] REQ-LEGAL-012 Data Processing Consent
- [ ] REQ-LEGAL-013 Withdraw Consent
- [ ] REQ-SETTING-013 Download My Data
- [ ] REQ-PROFILE-007 Delete Account

### C.3 iOS App Store Review Checklist

- [ ] REQ-AUTH-010 Apple Sign-In (if third-party login exists)
- [ ] REQ-ONBOARD-014 ATT Permission Request (if tracking users)
- [ ] REQ-ONBOARD-003 Clear permission request explanations
- [ ] REQ-LEGAL-001~002 Complete legal documents

---

## Appendix D: Requirements Count Examples

### D.1 Simple Utility App

| Category | Req Count |
|----------|-----------|
| Authentication | 8 |
| Profile | 4 |
| Settings | 6 |
| Help & Support | 3 |
| Legal | 3 |
| Non-Functional | 10 |
| Core Features | 15 |
| **Total** | **~49** |

### D.2 Standard Consumer App (E-commerce)

| Category | Req Count |
|----------|-----------|
| Authentication | 12 |
| Profile | 6 |
| Settings | 10 |
| Onboarding | 4 |
| Notifications | 5 |
| Help & Support | 5 |
| Legal | 5 |
| Non-Functional | 15 |
| Product Browsing | 10 |
| Shopping Cart | 8 |
| Checkout & Payment | 12 |
| Order Management | 10 |
| **Total** | **~102** |

### D.3 Social App

| Category | Req Count |
|----------|-----------|
| Authentication | 12 |
| Profile | 8 |
| Settings | 12 |
| Onboarding | 4 |
| Notifications | 6 |
| Help & Support | 5 |
| Legal | 5 |
| Non-Functional | 15 |
| Content Posting | 8 |
| Social Interaction | 12 |
| Friend System | 8 |
| Instant Messaging | 10 |
| **Total** | **~105** |

---

## Version History

| Version | Date | Updates |
|---------|------|---------|
| 1.0 | 2024/01 | Initial release |
