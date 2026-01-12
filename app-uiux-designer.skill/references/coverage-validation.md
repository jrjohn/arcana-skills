# UI/UX Coverage Validation and Traceability Guide

## Overview

This guide provides a complete UI/UX coverage validation mechanism for specification documents (SRS/SDD/PRD/FSD), ensuring every generated screen can be traced back to original requirements, achieving **100% Coverage**.

---

## 1. Requirements Traceability Matrix (RTM)

### 1.1 RTM Structure

```markdown
# Requirements Traceability Matrix - {ProjectName}

| Req ID | Requirement Description | Source Document | Mapped Screen | UI Components | Status | Validation Date |
|--------|------------------------|-----------------|---------------|---------------|--------|-----------------|
| FR-001 | User login feature | SRS 3.1.1 | login.html | LoginForm, PasswordInput | Covered | 2024-01-15 |
| FR-002 | Social account login | SRS 3.1.2 | login.html | SocialLoginButtons | Covered | 2024-01-15 |
| FR-003 | Forgot password flow | SRS 3.1.3 | forgot-password.html | ForgotPasswordForm | Covered | 2024-01-15 |
| FR-004 | User registration | SRS 3.2.1 | register.html | RegisterForm | In Progress | - |
| FR-005 | Email verification | SRS 3.2.2 | - | - | Not Covered | - |
```

### 1.2 Status Definitions

| Status | Symbol | Description |
|--------|--------|-------------|
| Covered | Done | UI completed and verified |
| In Progress | WIP | UI currently in development |
| Not Covered | TODO | No corresponding UI yet |
| Partial | Partial | UI exists but doesn't fully satisfy requirements |
| N/A | N/A | Requirement doesn't need UI |

---

## 2. Coverage Analysis

### 2.1 Coverage Calculation Formulas

```
Feature Coverage = (Covered Requirements / Total Requirements) x 100%
Screen Coverage = (Generated Screens / Planned Screens) x 100%
Component Coverage = (Implemented Components / Planned Components) x 100%
Overall Coverage = (Feature Coverage + Screen Coverage + Component Coverage) / 3
```

### 2.2 Coverage Report Template

```markdown
# Coverage Validation Report

**Project Name:** {ProjectName}
**Validation Date:** {Date}
**Validation Version:** v{Version}

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Feature Coverage | 95% | 100% | Warning |
| Screen Coverage | 100% | 100% | Pass |
| Component Coverage | 98% | 100% | Warning |
| **Overall Coverage** | **97.67%** | **100%** | Warning |

## Detailed Analysis

### Feature Requirements Coverage
- Total Requirements: 120
- Covered: 114
- Partial Coverage: 4
- Not Covered: 2

### Uncovered Items List
| Req ID | Description | Priority | Expected Completion |
|--------|-------------|----------|---------------------|
| FR-045 | Multi-language switch | High | 2024-02-01 |
| FR-089 | Dark mode | Medium | 2024-02-15 |

### Partial Coverage Items List
| Req ID | Description | Coverage Level | Missing Items |
|--------|-------------|----------------|---------------|
| FR-023 | Search feature | 70% | Advanced filter UI |
| FR-056 | Notification settings | 80% | Schedule options |
```

---

## 3. Automated Validation Workflow

### 3.1 Validation Workflow

```
+-------------------------------------------------------------------+
|                    Coverage Validation Workflow                    |
+-------------------------------------------------------------------+
                              |
                              v
                 +------------------------+
                 |  1. Load Specification |
                 |  (SRS/SDD/PRD/FSD)    |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  2. Parse Requirements |
                 |  - Functional (FR)     |
                 |  - Non-functional (NFR)|
                 |  - Use Cases (UC)      |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  3. Scan Output UI     |
                 |  - HTML/React/Angular  |
                 |  - SwiftUI/Compose     |
                 |  - Figma JSON          |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  4. Build Mapping      |
                 |  Req ID <-> UI Element |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  5. Calculate Coverage |
                 |  - Feature/Screen/Comp |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  6. Generate Report    |
                 |  - RTM / Gap Report    |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |  7. 100% Achieved?     |
                 +------------------------+
                        |         |
                   Yes  |         | No
                        v         v
              +--------------+  +--------------+
              | Validation   |  | List Gaps    |
              | Passed       |  | Create Fix   |
              | Issue Cert   |  | Plan         |
              +--------------+  +--------------+
```

### 3.2 Requirement ID Annotation Standards

Annotate corresponding requirement IDs in generated UI files:

#### HTML/React/Angular

```html
<!--
  @requirement FR-001: User login feature
  @requirement FR-002: Social account login
  @source SRS-ProjectName-1.0.md Section 3.1
-->
<div class="login-container" data-requirement="FR-001,FR-002">
  <!-- Login form implementation -->
</div>
```

#### React Component

```tsx
/**
 * LoginForm Component
 *
 * @requirements
 * - FR-001: User login feature
 * - FR-002: Social account login
 * - NFR-003: Login response time < 2 seconds
 *
 * @source SRS-ProjectName-1.0.md Section 3.1.1-3.1.2
 * @coverage 100%
 */
export const LoginForm: React.FC<LoginFormProps> = ({ ... }) => {
  // Implementation
};
```

#### Angular Component

```typescript
/**
 * LoginPageComponent
 *
 * @requirements
 * - FR-001: User login feature
 * - FR-002: Social account login
 *
 * @source SRS-ProjectName-1.0.md Section 3.1
 * @coverage 100%
 */
@Component({
  selector: 'app-login-page',
  templateUrl: './login-page.component.html',
  styleUrls: ['./login-page.component.scss']
})
export class LoginPageComponent { }
```

#### SwiftUI

```swift
/// LoginView
///
/// - Requirements:
///   - FR-001: User login feature
///   - FR-002: Social account login
/// - Source: SRS-ProjectName-1.0.md Section 3.1
/// - Coverage: 100%
struct LoginView: View {
    var body: some View {
        // Implementation
    }
}
```

#### Jetpack Compose

```kotlin
/**
 * LoginScreen
 *
 * Requirements:
 * - FR-001: User login feature
 * - FR-002: Social account login
 *
 * Source: SRS-ProjectName-1.0.md Section 3.1
 * Coverage: 100%
 */
@Composable
fun LoginScreen(
    onLoginClick: () -> Unit,
    onSocialLoginClick: (SocialProvider) -> Unit
) {
    // Implementation
}
```

---

## 4. Gap Analysis and Remediation

### 4.1 Gap Identification

```markdown
# Gap Analysis Report

**Analysis Date:** {Date}
**Analysis Scope:** SRS v1.0 vs UI v0.9

## Identified Gaps

### Critical Gaps (Must Fix)
| Gap ID | Requirement | Description | Impact Scope | Recommended Solution |
|--------|-------------|-------------|--------------|---------------------|
| GAP-001 | FR-045 | Missing multi-language switch UI | Global | Add LanguageSwitcher component |
| GAP-002 | FR-078 | Missing error prompt screen | Global | Add ErrorBoundary component |

### Major Gaps (Should Fix)
| Gap ID | Requirement | Description | Impact Scope | Recommended Solution |
|--------|-------------|-------------|--------------|---------------------|
| GAP-003 | FR-089 | Dark mode not implemented | Global | Add ThemeProvider |

### Minor Gaps (Can Defer)
| Gap ID | Requirement | Description | Impact Scope | Recommended Solution |
|--------|-------------|-------------|--------------|---------------------|
| GAP-004 | FR-102 | Animation effects incomplete | Partial | Add micro-interactions |
```

### 4.2 Remediation Plan Template

```markdown
# Gap Remediation Plan

## GAP-001: Multi-language Switch UI

### Requirements Traceability
- **Requirement ID:** FR-045
- **Source:** SRS-ProjectName-1.0.md Section 4.5
- **Original Description:** "System should support Traditional Chinese/Simplified Chinese/English language switching"

### Remediation Content
1. Add `LanguageSwitcher` component
2. Add `LanguageProvider` Context
3. Modify Header to include language switch entry
4. Add i18n resource file structure

### Affected Screens
- [ ] header.html
- [ ] settings.html
- [ ] All pages with text content

### Estimated Effort
- UI Design: 2hr
- Component Development: 4hr
- Integration Testing: 2hr

### Acceptance Criteria
- [ ] Can switch between three languages
- [ ] Immediate effect after switching
- [ ] Remember user preference
```

---

## 5. Coverage Validation Output

### 5.1 Output Directory Structure

```
generated-ui/{ProjectName}/
+-- README.md
+-- COVERAGE-REPORT.md          # Coverage report
+-- TRACEABILITY-MATRIX.md      # Requirements traceability matrix
+-- GAP-ANALYSIS.md             # Gap analysis report
+-- validation/
|   +-- requirements-map.json   # Requirements mapping JSON
|   +-- coverage-summary.json   # Coverage summary JSON
|   +-- gaps.json               # Gap list JSON
+-- html/
+-- react/
+-- angular/
+-- swiftui/
+-- compose/
```

### 5.2 requirements-map.json Structure

```json
{
  "project": "ProjectName",
  "version": "1.0.0",
  "source_documents": [
    {
      "type": "SRS",
      "filename": "SRS-ProjectName-1.0.md",
      "version": "1.0",
      "parsed_date": "2024-01-15T10:30:00Z"
    },
    {
      "type": "SDD",
      "filename": "SDD-ProjectName-1.0.md",
      "version": "1.0",
      "parsed_date": "2024-01-15T10:30:00Z"
    }
  ],
  "requirements": [
    {
      "id": "FR-001",
      "type": "functional",
      "description": "User login feature",
      "source": "SRS 3.1.1",
      "priority": "high",
      "mapped_screens": ["login"],
      "mapped_components": ["LoginForm", "PasswordInput", "RememberMeCheckbox"],
      "status": "covered",
      "coverage_percentage": 100,
      "validation_date": "2024-01-15T14:20:00Z"
    },
    {
      "id": "FR-002",
      "type": "functional",
      "description": "Social account login",
      "source": "SRS 3.1.2",
      "priority": "high",
      "mapped_screens": ["login"],
      "mapped_components": ["SocialLoginButtons", "GoogleLoginButton", "AppleLoginButton"],
      "status": "covered",
      "coverage_percentage": 100,
      "validation_date": "2024-01-15T14:20:00Z"
    }
  ],
  "screens": [
    {
      "id": "login",
      "name": "Login Page",
      "files": {
        "html": "html/login.html",
        "react": "react/pages/LoginPage.tsx",
        "angular": "angular/pages/auth/login/login-page.component.ts",
        "swiftui": "swiftui/Views/Auth/LoginView.swift",
        "compose": "compose/ui/auth/LoginScreen.kt"
      },
      "requirements_covered": ["FR-001", "FR-002", "FR-003"],
      "components_used": ["LoginForm", "SocialLoginButtons", "ForgotPasswordLink"]
    }
  ]
}
```

### 5.3 coverage-summary.json Structure

```json
{
  "project": "ProjectName",
  "generated_at": "2024-01-15T14:30:00Z",
  "summary": {
    "overall_coverage": 97.5,
    "functional_coverage": 95.0,
    "screen_coverage": 100.0,
    "component_coverage": 97.5,
    "target_coverage": 100.0,
    "status": "in_progress"
  },
  "by_category": {
    "authentication": {
      "total": 10,
      "covered": 10,
      "percentage": 100
    },
    "user_management": {
      "total": 15,
      "covered": 14,
      "percentage": 93.3
    },
    "dashboard": {
      "total": 8,
      "covered": 8,
      "percentage": 100
    }
  },
  "by_priority": {
    "critical": {
      "total": 20,
      "covered": 20,
      "percentage": 100
    },
    "high": {
      "total": 35,
      "covered": 34,
      "percentage": 97.1
    },
    "medium": {
      "total": 40,
      "covered": 38,
      "percentage": 95.0
    },
    "low": {
      "total": 25,
      "covered": 22,
      "percentage": 88.0
    }
  },
  "uncovered_requirements": [
    {
      "id": "FR-045",
      "description": "Multi-language switch",
      "priority": "high",
      "category": "global"
    },
    {
      "id": "FR-089",
      "description": "Dark mode",
      "priority": "medium",
      "category": "global"
    }
  ]
}
```

---

## 6. Validation Checklists

### 6.1 Functional Requirements Validation Checklist

```markdown
# Functional Requirements Validation Checklist

## Authentication Module
- [x] FR-001: User login -> login.html Done
- [x] FR-002: Social login -> login.html Done
- [x] FR-003: Forgot password -> forgot-password.html Done
- [x] FR-004: User registration -> register.html Done
- [x] FR-005: Email verification -> verify-email.html Done
- [x] FR-006: Two-factor authentication -> 2fa-setup.html Done

## User Management
- [x] FR-010: Profile view -> profile.html Done
- [x] FR-011: Profile edit -> profile-edit.html Done
- [x] FR-012: Avatar upload -> profile-edit.html Done
- [ ] FR-013: Account deletion -> Not Covered

## Core Features
- [x] FR-020: Dashboard -> dashboard.html Done
- [x] FR-021: Data list -> list.html Done
- [x] FR-022: Data details -> detail.html Done
- [x] FR-023: Search feature -> search.html Partial (missing advanced filter)
```

### 6.2 Non-Functional Requirements Validation Checklist

```markdown
# Non-Functional Requirements Validation Checklist

## Usability
- [x] NFR-001: WCAG 2.1 AA compliant Done
- [x] NFR-002: Keyboard navigation support Done
- [x] NFR-003: Clear error messages Done

## Responsive Design
- [x] NFR-010: Mobile support (320px+) Done
- [x] NFR-011: Tablet support (768px+) Done
- [x] NFR-012: Desktop support (1024px+) Done

## Performance
- [x] NFR-020: Initial load < 3 seconds Done
- [x] NFR-021: Interaction response < 100ms Done

## Security
- [x] NFR-030: Password field masked Done
- [x] NFR-031: Sensitive data not in URL Done
```

---

## 7. 100% Coverage Achievement Confirmation

### 7.1 Achievement Confirmation Flow

```
+-------------------------------------------------------------------+
|                100% Coverage Achievement Confirmation Flow          |
+-------------------------------------------------------------------+

Step 1: Run coverage analysis
        |
Step 2: Review COVERAGE-REPORT.md
        |
Step 3: Overall coverage = 100%?
        |
        +-- Yes -> Step 4: Generate coverage certificate
        |          |
        |          Step 5: Sign-off confirmation
        |          |
        |          Validation Complete
        |
        +-- No  -> Step 4: Review GAP-ANALYSIS.md
                   |
                   Step 5: Execute gap remediation
                   |
                   Step 6: Regenerate UI
                   |
                   Return to Step 1
```

### 7.2 Coverage Certificate Template

```markdown
# UI/UX Coverage Validation Certificate

---

**Project Name:** {ProjectName}
**Validation Version:** v{Version}
**Validation Date:** {Date}

---

## Validation Results

| Item | Result |
|------|--------|
| Feature Coverage | 100% (120/120) |
| Screen Coverage | 100% (45/45) |
| Component Coverage | 100% (89/89) |
| **Overall Coverage** | **100%** |

---

## Validation Scope

### Source Documents
- SRS-{ProjectName}-1.0.md (v1.0, 2024-01-10)
- SDD-{ProjectName}-1.0.md (v1.0, 2024-01-12)

### Generated UI
- HTML/Tailwind: 45 screens
- React Components: 89 components
- Angular Components: 89 components
- SwiftUI Views: 45 screens
- Jetpack Compose Screens: 45 screens

---

## Confirmation Statement

This certificate confirms that all functional requirements, non-functional requirements, and use cases defined in the specification documents have been fully implemented in the generated UI/UX design, achieving 100% coverage.

---

**Validator:** _________________
**Validation Date:** _________________
**Approving Manager:** _________________

---

_This certificate was auto-generated by App UI/UX Designer Skill_
```

---

## 8. Integration Commands

### 8.1 Coverage Validation Command

When user provides specification documents and UI files, execute the following validation:

```
Input:
- Specification Documents: SRS-{Project}.md, SDD-{Project}.md
- UI Directory: generated-ui/{Project}/

Output:
1. TRACEABILITY-MATRIX.md - Complete traceability matrix
2. COVERAGE-REPORT.md - Coverage report
3. GAP-ANALYSIS.md - Gap analysis (if any)
4. validation/*.json - Machine-readable formats

Validation Standards:
- Every FR/NFR/UC must map to at least one UI element
- Every UI screen must annotate corresponding requirement IDs
- Overall coverage must reach 100%
```

### 8.2 Auto-Annotation Command

Automatically add requirement traceability annotations in code when generating UI:

```
Every generated UI file must include:
1. Requirement list comment in file header
2. @requirements JSDoc/DocBlock for components
3. data-requirement attributes for HTML
4. Source document and section references
```

---

## 9. Best Practices

### 9.1 Best Practices for Ensuring 100% Coverage

1. **Preparation**
   - Ensure specification documents have clear requirement IDs
   - Establish unified requirement ID naming conventions
   - Confirm all requirements have clear acceptance criteria

2. **Generation Process**
   - Update traceability matrix for each generated screen
   - Immediately annotate requirement IDs in code
   - Periodically run coverage checks

3. **Validation Phase**
   - Use automated tools to scan annotations
   - Manually review Critical/High priority requirements
   - Confirm all Gaps have remediation plans

4. **Maintenance Phase**
   - Sync update UI and traceability matrix when specs change
   - Version control coverage reports
   - Periodically revalidate coverage

### 9.2 Common Issue Handling

| Issue | Solution |
|-------|----------|
| Specification documents have no IDs | Help establish requirement ID system |
| Requirements are too vague | Request clarification before generating UI |
| One requirement maps to multiple screens | Annotate in all related screens |
| One screen satisfies multiple requirements | List all corresponding requirement IDs |
| Specification gaps discovered | Record in Gap analysis, recommend spec supplement |

---

## Appendix: Quick Reference

### Requirement ID Formats

| Prefix | Type | Example |
|--------|------|---------|
| FR- | Functional Requirement | FR-001 |
| NFR- | Non-Functional Requirement | NFR-001 |
| UC- | Use Case | UC-001 |
| US- | User Story | US-001 |
| BR- | Business Rule | BR-001 |

### Coverage Level Grades

| Grade | Coverage | Status |
|-------|----------|--------|
| A | 100% | Fully Covered |
| B | 95-99% | Near Complete |
| C | 80-94% | Needs Improvement |
| D | 60-79% | Seriously Lacking |
| F | <60% | Needs Replanning |

---

## 10. Clickable Element Coverage Validation (可點擊元素覆蓋驗證)

### 10.1 Overview

Every clickable element in UI Flow MUST have a corresponding target screen. This ensures complete navigation flow and prevents dead-end buttons.

### 10.2 Clickable Element Types

| Element Type | Description | Validation Required |
|--------------|-------------|---------------------|
| Button | Primary/Secondary action buttons | Target screen must exist |
| Link | Text links, navigation links | Target screen or URL must exist |
| Tab | Tab bar items | Each tab must have a screen |
| Icon | Clickable icons (settings, notifications) | Target action/screen must exist |
| Card | Tappable cards/list items | Detail screen must exist |
| Navigation | Back, Close, Menu buttons | Navigation action must work |

### 10.3 Validation Rules

```markdown
# Clickable Element Validation Checklist

## Required Checks

1. **Button Target Validation**
   - [ ] Every button has onclick handler
   - [ ] onclick target screen (SCR-*) exists
   - [ ] No placeholder/dummy targets

2. **Tab Bar Validation**
   - [ ] Each tab has corresponding screen
   - [ ] Tab selection state works correctly
   - [ ] Current tab is highlighted

3. **Navigation Flow**
   - [ ] Every screen (except Home/Login) has back navigation
   - [ ] Modal/Sheet has close mechanism
   - [ ] Form submit leads to success/error screen

4. **Link Integrity**
   - [ ] Internal links point to existing screens
   - [ ] External links are valid URLs
   - [ ] No broken href attributes
```

### 10.4 Validation Script

Add to `capture-screenshots.js`:

```javascript
// Clickable Element Coverage Validation
function validateClickableElements(htmlContent, screenId) {
  const errors = [];

  // Extract all onclick targets
  const onclickMatches = htmlContent.matchAll(/onclick="[^"]*openScreen\(['"]([^'"]+)['"]\)"/g);
  for (const match of onclickMatches) {
    const targetScreen = match[1];
    if (!fs.existsSync(targetScreen)) {
      errors.push({
        screen: screenId,
        element: 'onclick',
        target: targetScreen,
        error: 'Target screen does not exist'
      });
    }
  }

  // Extract all href targets
  const hrefMatches = htmlContent.matchAll(/href="([^"#][^"]*)"/g);
  for (const match of hrefMatches) {
    const target = match[1];
    if (!target.startsWith('http') && !fs.existsSync(target)) {
      errors.push({
        screen: screenId,
        element: 'href',
        target: target,
        error: 'Link target does not exist'
      });
    }
  }

  // ⚠️ NEW: Check for href="#" (broken links)
  const brokenHrefMatches = htmlContent.matchAll(/href="#"/g);
  for (const match of brokenHrefMatches) {
    errors.push({
      screen: screenId,
      element: 'href',
      target: '#',
      error: 'Broken link: href="#" has no target'
    });
  }

  // ⚠️ NEW: Check for type="submit" buttons without onclick
  const submitButtonMatches = htmlContent.matchAll(/<button[^>]*type="submit"[^>]*>/g);
  for (const match of submitButtonMatches) {
    const buttonTag = match[0];
    if (!buttonTag.includes('onclick=')) {
      errors.push({
        screen: screenId,
        element: 'button[type="submit"]',
        target: null,
        error: 'Submit button has no onclick navigation handler'
      });
    }
  }

  // ⚠️ NEW: Check for social login buttons without onclick
  const socialBtnMatches = htmlContent.matchAll(/<button[^>]*class="[^"]*social[^"]*"[^>]*>/gi);
  for (const match of socialBtnMatches) {
    const buttonTag = match[0];
    if (!buttonTag.includes('onclick=')) {
      errors.push({
        screen: screenId,
        element: 'button.social-btn',
        target: null,
        error: 'Social login button has no onclick navigation handler'
      });
    }
  }

  return errors;
}
```

### 10.5 Coverage Report Enhancement

Add clickable element coverage to COVERAGE-REPORT.md:

```markdown
## Clickable Element Coverage

| Screen ID | Total Clickable | Valid Targets | Coverage |
|-----------|-----------------|---------------|----------|
| SCR-AUTH-001-login | 5 | 5 | 100% |
| SCR-DASH-001-home | 12 | 12 | 100% |
| SCR-SETTING-001 | 8 | 8 | 100% |
| **Total** | **25** | **25** | **100%** |

### Orphan Elements (No Target)
None - All clickable elements have valid targets.

### Navigation Completeness
- Screens with Back Button: 18/20 (Home and Login excluded)
- Tab Bar Coverage: 5/5 (100%)
- Modal Close Coverage: 3/3 (100%)
```

### 10.6 Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Dead Button | Button onclick targets non-existent screen | Create target screen or remove button |
| Missing Back | Screen has no way to go back | Add back button or navigation |
| Broken Tab | Tab points to wrong screen | Fix tab onclick target |
| Orphan Modal | Modal has no close button | Add close/cancel button |
| Form Dead-End | Submit leads nowhere | Add success/error result screen |

### 10.7 Pre-Generation Checklist

Before generating UI Flow, verify:

```markdown
## Pre-Generation Validation

### Screen Inventory
- [ ] All screens in SDD have corresponding HTML files planned
- [ ] Navigation flow diagram shows all connections
- [ ] No isolated screens (except explicit dead-ends like logout confirmation)

### Button Mapping
- [ ] Primary actions mapped to target screens
- [ ] Cancel/Back actions return to previous screen
- [ ] Submit actions lead to confirmation/result

### Tab Bar Planning
- [ ] All tabs have designated screens
- [ ] Tab icons and labels defined
- [ ] Current tab indication logic planned
```

---

## 11. Mandatory Auto-Scan Validation (強制自動掃描驗證)

### 11.1 Overview

⚠️ **CRITICAL REQUIREMENT**: After generating UI Flow HTML files, the system MUST automatically scan all screens to validate clickable element coverage. This is NOT optional.

### 11.2 Validation Trigger Points

| Trigger | Action Required |
|---------|-----------------|
| After generating ANY screen HTML | Run validation on that screen |
| After generating navigation table | Auto-scan ALL screens |
| Before generating UI Flow Diagram | Validation MUST pass (100%) |
| Before SRS/SDD feedback | Validation MUST pass (100%) |

### 11.3 Auto-Scan Validation Script

Use the provided `validate-navigation.js` script:

```bash
# Basic validation
node validate-navigation.js

# With fix suggestions
node validate-navigation.js --fix

# Generate Markdown report
node validate-navigation.js --report
```

Location: `templates/ui-flow/validate-navigation.js`

### 11.4 Validation Workflow (Mandatory Steps)

```
Step 1: Generate Screen HTML Files
        ↓
Step 2: Generate Navigation Validation Table (手動或自動)
        ↓
Step 3: ⚠️ AUTO-SCAN ALL SCREENS (強制)
        │
        ├─→ Run: node validate-navigation.js
        │
        ├─→ Coverage = 100%?
        │     │
        │     ├─ YES → Continue to Step 4
        │     │
        │     └─ NO  → FIX ALL ISSUES
        │              │
        │              ├─→ Add missing onclick handlers
        │              ├─→ Fix broken href targets
        │              ├─→ Remove empty onclick/href
        │              │
        │              └─→ Re-run validation (loop until 100%)
        ↓
Step 4: Generate UI Flow Diagram
        ↓
Step 5: SRS/SDD Feedback
```

### 11.5 Issue Detection Patterns

The auto-scan validates these patterns:

| Pattern | Issue | Fix Required |
|---------|-------|--------------|
| `onclick=""` | Empty onclick | Add navigation handler |
| `href="#"` | Empty href | Replace with onclick navigation |
| `<button>` without onclick | No handler | Add onclick handler |
| `onclick="location.href='X.html'"` where X.html missing | Broken link | Create target or fix path |
| `type="submit"` without onclick | Form dead-end | Add result navigation |
| **X/Close button without onclick** | ⚠️ CRITICAL | Must navigate back |

### 11.5.1 Close Button Detection (關閉按鈕檢測)

⚠️ **CRITICAL**: Close/Exit buttons are detected and flagged as high-priority issues.

**Detection Patterns:**

```html
<!-- SVG X Path Patterns -->
<path d="M6 18L18 6M6 6l12 12"/>  <!-- Standard X -->
<path d="M18 6L6 18"/>             <!-- Reverse X -->
<path d="M4 4L20 20M20 4L4 20"/>   <!-- Large X -->

<!-- Class Name Patterns -->
class="close-btn"
class="dismiss-button"
class="exit-icon"

<!-- Symbol Patterns -->
× ✕ ✖ ╳ &times;

<!-- Aria Label -->
aria-label="close"
aria-label="關閉"
aria-label="離開"
```

**Script Output:**
```
❌ Line 58: ⚠️ CRITICAL: Close/Exit button has no onclick handler (must navigate back)
```

**Required Fix:**
```html
<!-- BEFORE -->
<button class="w-12 h-12 rounded-xl bg-gray-100">
  <svg><path d="M6 18L18 6M6 6l12 12"/></svg>
</button>

<!-- AFTER -->
<button onclick="location.href='SCR-TRAIN-001-select.html'" class="w-12 h-12 rounded-xl bg-gray-100">
  <svg><path d="M6 18L18 6M6 6l12 12"/></svg>
</button>
```

### 11.5.2 Settings Row Detection (設定列表行檢測)

⚠️ **CRITICAL**: Settings list rows with chevron icons are detected and flagged as high-priority issues.

**Detection Patterns:**

```html
<!-- Chevron-right SVG Path Patterns -->
<path d="M9 5l7 7-7 7"/>           <!-- Standard chevron-right -->
<path d="M8.59 16.59L13.17 12 8.59 7.41"/>  <!-- Material Design -->

<!-- Chevron Class Name Patterns -->
class="chevron-right"
class="arrow-right"
class="icon-right"

<!-- Symbol Patterns -->
› → &gt;

<!-- Detection Condition -->
Button/div with active:bg-* or hover:bg-* + chevron icon
```

**Script Output:**
```
❌ Line 91: ⚠️ CRITICAL: Settings row has no onclick handler (must navigate or show alert)
```

**Required Fix (Option 1 - when target screen exists):**
```html
<!-- BEFORE -->
<button class="w-full flex items-center justify-between p-4 bg-white rounded-xl shadow-sm active:bg-gray-100">
  <span>個人資料</span>
  <svg><path d="M9 5l7 7-7 7"/></svg>
</button>

<!-- AFTER -->
<button onclick="location.href='SCR-SETTING-002-profile.html'" class="w-full flex items-center justify-between p-4 bg-white rounded-xl shadow-sm active:bg-gray-100">
  <span>個人資料</span>
  <svg><path d="M9 5l7 7-7 7"/></svg>
</button>
```

**Required Fix (Option 2 - when target screen does NOT exist):**
```html
<!-- Use alert() to describe the function -->
<button onclick="alert('個人資料設定：編輯您的個人資訊')" class="w-full flex items-center justify-between p-4 bg-white rounded-xl shadow-sm active:bg-gray-100">
  <span>個人資料</span>
  <svg><path d="M9 5l7 7-7 7"/></svg>
</button>
```

⚠️ **NEVER leave a settings row without onclick!** Using `alert()` is acceptable when the target screen doesn't exist yet, but having NO onclick is not acceptable.

### 11.6 Validation Output Format

The script outputs a table for easy review:

```markdown
## Navigation Validation Report

| Screen | Elements | Valid | Issues |
|--------|----------|-------|--------|
| ✅ auth/SCR-AUTH-001-login.html | 5 | 5 | 0 |
| ⚠️ vocab/SCR-VOCAB-002-detail.html | 8 | 6 | 2 |
| ✅ train/SCR-TRAIN-001-select.html | 7 | 7 | 0 |

**Coverage: 92.3%** ← MUST be 100% to proceed
```

### 11.7 Common Fixes Applied

When issues are found, apply these fixes:

```html
<!-- BEFORE: Empty button -->
<button class="btn">Back</button>

<!-- AFTER: With onclick handler -->
<button onclick="location.href='previous-screen.html'" class="btn">Back</button>
```

```html
<!-- BEFORE: Empty href -->
<a href="#">Settings</a>

<!-- AFTER: With onclick navigation -->
<button onclick="location.href='settings.html'" class="btn-link">Settings</button>
```

```html
<!-- BEFORE: Nested clickable without stopPropagation -->
<div onclick="goToDetail()">
  <button onclick="goToAction()">Action</button>
</div>

<!-- AFTER: With event.stopPropagation() -->
<div onclick="location.href='detail.html'">
  <button onclick="event.stopPropagation(); location.href='action.html'">Action</button>
</div>
```

### 11.8 Platform-Specific Path Rules

| Platform | Path Pattern | Example |
|----------|--------------|---------|
| iPad | `../module/SCR-*.html` | `../vocab/SCR-VOCAB-001-list.html` |
| iPhone | `SCR-*.html` (same folder) | `SCR-VOCAB-001-list.html` |
| Cross-module | `../auth/SCR-AUTH-001-login.html` | Logout → Login |

### 11.9 Prohibited Patterns

❌ These patterns are FORBIDDEN:

```html
<!-- FORBIDDEN: Empty handlers -->
onclick=""
href="#"

<!-- FORBIDDEN: Placeholder targets -->
onclick="location.href='TODO.html'"
onclick="location.href='placeholder.html'"

<!-- FORBIDDEN: JavaScript void -->
href="javascript:void(0)"

<!-- FORBIDDEN: Missing target screens -->
onclick="location.href='SCR-DOES-NOT-EXIST.html'"
```

### 11.10 Completion Criteria

Validation is complete when:

- [ ] All screens scanned
- [ ] Coverage = 100%
- [ ] Zero issues in report
- [ ] Report saved to `NAVIGATION-VALIDATION-REPORT.md`

---

## 12. UI Flow Diagram Arrow Connection Validation (連線驗證)

### 12.1 Overview

UI Flow Diagram 中的箭頭連線必須正確表達畫面間的導航關係。所有連線必須經過驗證，確保：
1. 每個畫面（除首頁外）至少有一個進入箭頭
2. 每個畫面至少有一個離開箭頭
3. 關鍵流程的連線完整

### 12.2 Arrow Types and Colors

| Arrow Type | Color | Stroke | Use Case |
|------------|-------|--------|----------|
| AUTH flow | `#6366F1` (Indigo) | Solid | Login → Register → Role |
| HOME flow | `#6366F1` (Indigo) | Solid/Dashed | Role → Student/Parent Home |
| VOCAB flow | `#10B981` (Emerald) | Solid | Vocabulary learning screens |
| TRAIN flow | `#F59E0B` (Amber) | Solid | Training/quiz screens |
| PROG flow | `#6366F1` (Indigo) | Solid | Progress report screens |
| SETTING flow | `#64748B` (Slate) | Solid | Settings sub-screens |

### 12.3 Required Connection Patterns

#### 12.3.1 AUTH Module Connections

```
AUTH-001 (Login)
    ↓ solid
AUTH-002 (Register)
    ↓ solid
AUTH-004 (Role Select)
    ├─→ HOME-001 (Student) [solid L-shaped path]
    └─→ HOME-002 (Parent)  [dashed L-shaped path]
```

**SVG Path Examples:**

```html
<!-- Linear: AUTH-001 → AUTH-002 -->
<path d="M 550 150 L 550 250" stroke="#6366F1" stroke-width="2.5"
      fill="none" marker-end="url(#arrow-auth)"/>

<!-- L-shaped: AUTH-004 → HOME-001 (crosses rows) -->
<path d="M 680 340 L 680 430 L 160 430 L 160 470"
      stroke="#6366F1" stroke-width="2.5" fill="none"
      marker-end="url(#arrow-home)"/>

<!-- Dashed: AUTH-004 → HOME-002 (alternate path) -->
<path d="M 700 340 L 700 410 L 420 410 L 420 470"
      stroke="#6366F1" stroke-width="2" fill="none"
      marker-end="url(#arrow-home)" stroke-dasharray="6,4"/>
```

#### 12.3.2 HOME Module Connections

```
HOME-001 (Student)
    ├─→ VOCAB-001 (Vocabulary)
    └─→ HOME-002 (Parent, role switch)

HOME-002 (Parent)
    ├─→ TRAIN-001 (Training)
    └─→ HOME-001 (Student, role switch)
```

#### 12.3.3 SETTING Module Connections

```
SETTING-001 (Settings Main)
    ├─→ SETTING-002 (Profile)
    ├─→ SETTING-003 (Notifications)
    ├─→ SETTING-004 (Appearance)
    ├─→ SETTING-005 (Language)
    ├─→ SETTING-006 (Privacy)
    ├─→ SETTING-007 (Sync)
    ├─→ SETTING-008 (Feedback)
    ├─→ SETTING-010 (Help)
    └─→ SETTING-012 (About)
```

### 12.4 Arrow Path Patterns

| Pattern | Use Case | SVG Path |
|---------|----------|----------|
| **Vertical** | Same column, adjacent rows | `M x1 y1 L x1 y2` |
| **Horizontal** | Same row, different columns | `M x1 y1 L x2 y1` |
| **L-shaped** | Cross rows/columns | `M x1 y1 L x1 mid L x2 mid L x2 y2` |
| **Curved** | Avoiding overlaps | Use `Q` or `C` bezier curves |

### 12.5 Validation Rules

```markdown
## Arrow Validation Checklist

### Required Connections
- [ ] AUTH-001 → AUTH-002 (Login → Register)
- [ ] AUTH-002 → AUTH-004 (Register → Role)
- [ ] AUTH-004 → HOME-001 (Role → Student) [L-shaped]
- [ ] AUTH-004 → HOME-002 (Role → Parent) [L-shaped, dashed]
- [ ] HOME-001 → VOCAB-001 (Student → Vocabulary)
- [ ] HOME-002 → TRAIN-001 (Parent → Training)
- [ ] SETTING-001 → [sub-screens] (Settings → Details)

### Connection Integrity
- [ ] Every screen has at least 1 incoming OR outgoing arrow
- [ ] No orphan screens (no connections at all)
- [ ] No broken arrows (pointing to non-existent screens)
- [ ] L-shaped paths used for cross-row navigation
- [ ] Dashed lines for alternate/optional paths
```

### 12.6 Validation Script

Use `validate-ui-flow-arrows.py` for automated validation:

```python
#!/usr/bin/env python3
"""
Validate UI Flow Diagram Arrow Connections

Rules:
1. Every screen should have at least one incoming or outgoing arrow
2. AUTH-004 (Role Select) should connect to HOME screens
3. No orphan screens (screens with no connections)
4. No broken arrows (arrows pointing to non-existent screens)
"""

from playwright.sync_api import sync_playwright
import re

# Expected flow connections
EXPECTED_FLOWS = {
    'AUTH': {
        'AUTH-001': ['AUTH-002'],
        'AUTH-002': ['AUTH-004'],
        'AUTH-004': ['HOME-001', 'HOME-002'],
    },
    'HOME': {
        'HOME-001': ['VOCAB-001', 'HOME-002'],
        'HOME-002': ['TRAIN-001', 'HOME-001'],
    },
    'SETTING': {
        'SETTING-001': ['SETTING-002', 'SETTING-003', '...'],
    }
}

def validate_arrows():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load UI Flow Diagram
        page.goto('file:///path/to/ui-flow-diagram.html?device=ipad')
        page.wait_for_load_state('networkidle')

        # Get all arrows and screen positions
        arrows = page.locator('.connection-svg path').all()
        cards = page.locator('.screen-card').all()

        # Validate connections...
        # (see validate-ui-flow-arrows.py for full implementation)

        browser.close()
```

### 12.7 Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing AUTH-004 → HOME arrows | Role select has no outgoing connection | Add L-shaped paths to both HOME screens |
| Arrow from wrong source | Vertical arrow appears at wrong X position | Check path start coordinates match source screen |
| Overlapping arrows | Multiple arrows cross each other | Use L-shaped paths with different Y midpoints |
| Wrong arrow color | Arrow uses incorrect module color | Match stroke color to target module |
| Dashed where solid needed | Primary path appears dashed | Remove `stroke-dasharray` for main flow |

### 12.8 SVG Arrow Marker Definition

```html
<defs>
  <!-- AUTH arrows (Indigo) -->
  <marker id="arrow-auth" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#6366F1"/>
  </marker>

  <!-- HOME arrows (Indigo) -->
  <marker id="arrow-home" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#6366F1"/>
  </marker>

  <!-- VOCAB arrows (Emerald) -->
  <marker id="arrow-vocab" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#10B981"/>
  </marker>

  <!-- SETTING arrows (Slate) -->
  <marker id="arrow-setting" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#64748B"/>
  </marker>
</defs>
```

### 12.9 Coordinate Calculation Guide

For positioning arrows correctly:

```javascript
// Screen card typical dimensions
const iPadCard = { width: 200, height: 140 };
const iPhoneCard = { width: 120, height: 260 };

// Center point calculation
function getCardCenter(left, top, isIpad = true) {
  const card = isIpad ? iPadCard : iPhoneCard;
  return {
    x: left + card.width / 2,
    y: top + card.height / 2
  };
}

// Arrow endpoint (bottom of source card)
function getArrowStart(left, top, isIpad = true) {
  const card = isIpad ? iPadCard : iPhoneCard;
  return {
    x: left + card.width / 2,
    y: top + card.height
  };
}

// Arrow endpoint (top of target card)
function getArrowEnd(left, top, isIpad = true) {
  const card = isIpad ? iPadCard : iPhoneCard;
  return {
    x: left + card.width / 2,
    y: top
  };
}
```

---

## 13. Integration with app-requirements-skill

### 11.1 Mandatory UI Flow Generation

When called from `app-requirements-skill`:

1. **SDD Complete → UI Flow Generation Required**
   - Cannot skip UI Flow generation
   - Must generate for all platforms (iPad + iPhone)

2. **Clickable Coverage = 100%**
   - Every button must work
   - Every navigation must be complete

3. **SRS/SDD Feedback Required**
   - Update SDD with screenshots
   - Update SRS with Screen References
   - Update SRS with Inferred Navigation Requirements (REQ-NAV-*)

### 11.2 Validation Gate

UI Flow generation is NOT complete until:

```markdown
## Completion Criteria

- [ ] All screens generated (HTML files exist)
- [ ] All screenshots captured (PNG files exist)
- [ ] Clickable Element Coverage = 100%
- [ ] Navigation Integrity validated
- [ ] SDD feedback complete
- [ ] SRS feedback complete
- [ ] DOCX regenerated
```

---

## 14. Playwright Click Validation (強制點擊驗證)

### 14.1 Overview

⚠️ **MANDATORY**: After generating UI Flow HTML files, you MUST run Playwright-based validation that **actually clicks** every clickable element to verify navigation works correctly.

This goes beyond checking if `onclick` attributes exist - it tests **real navigation**.

### 14.2 Why Click Validation is Required

| Static Check | Playwright Click Validation |
|--------------|----------------------------|
| Only checks if `onclick` exists | Actually clicks the element |
| Cannot verify target file exists | Verifies navigation succeeds |
| Cannot detect broken paths | Detects `../` path resolution issues |
| Cannot test dynamic navigation | Tests real browser behavior |

### 14.3 Validation Script

Save as `validate-clickable-elements.py` in the UI Flow directory:

```bash
# Installation (one-time)
pip install playwright
playwright install chromium

# Run validation
python validate-clickable-elements.py

# With fix suggestions
python validate-clickable-elements.py --fix

# Verbose output
python validate-clickable-elements.py --verbose
```

### 14.4 What Gets Validated

| Element Type | Detection Method | Validation |
|--------------|------------------|------------|
| Close/X buttons | SVG path `M6 18L18 6` | Must have onclick → previous screen |
| Back buttons | SVG path `M15 19l-7-7` | Must have onclick → previous screen |
| Chevron buttons | SVG path `M9 5l7 7` | Must have onclick → target screen |
| Settings rows | Button with chevron | Must have onclick → detail screen |
| Submit buttons | `type="submit"` | Must have onclick → result screen |
| Links | `a[href]` | href target must exist |

### 14.5 Validation Workflow (Mandatory)

```
Step 1: Generate Screen HTML Files
        ↓
Step 2: Run Static Validation
        node validate-navigation.js
        ↓
Step 3: ⚠️ RUN PLAYWRIGHT CLICK VALIDATION (強制)
        python validate-clickable-elements.py
        │
        ├─→ Coverage = 100%?
        │     │
        │     ├─ YES → Continue to Step 4
        │     │
        │     └─ NO  → FIX ALL ISSUES
        │              ├─→ Add missing onclick handlers
        │              ├─→ Fix broken href targets
        │              └─→ Re-run validation (loop until 100%)
        ↓
Step 4: Generate UI Flow Diagram
        ↓
Step 5: SRS/SDD Feedback
```

### 14.6 Output Example

**Success:**
```
======================================================================
PLAYWRIGHT CLICKABLE ELEMENT VALIDATION
======================================================================

Scanning 58 HTML files...

✅ auth/SCR-AUTH-001-login.html
✅ auth/SCR-AUTH-002-register.html
✅ train/SCR-TRAIN-001-select.html
...

======================================================================
VALIDATION REPORT
======================================================================

Files scanned:      58
Total elements:     219
Valid clicks:       219
Broken links:       0
Missing onclick:    0

COVERAGE: 100.0%

======================================================================
✅ ALL CLICKABLE ELEMENTS VALIDATED!
======================================================================
```

**Failure:**
```
======================================================================
⛔ VALIDATION FAILED: 35 issues found
======================================================================

📁 train/SCR-TRAIN-003-speaking.html:
   🔴 [MISSING_ONCLICK] Button has no onclick handler
   🔴 [MISSING_ONCLICK] Button has no onclick handler

📁 vocab/SCR-VOCAB-002-detail.html:
   🔴 [MISSING_ONCLICK] Button has no onclick handler
```

### 14.7 Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `MISSING_ONCLICK` on X button | Close button has no handler | Add `onclick="location.href='PREVIOUS.html'"` |
| `MISSING_ONCLICK` on chevron | Settings row has no handler | Add `onclick="location.href='DETAIL.html'"` |
| `BROKEN_LINK` | Target file doesn't exist | Create target file or fix path |
| `BROKEN_HREF` | Link points to missing file | Fix href or create file |

### 14.8 Navigation Checklist Output

The script generates `NAVIGATION-VALIDATION-CHECKLIST.md`:

```markdown
# Navigation Validation Checklist

## Summary
- Total Files: 58
- Total Clickable Elements: 219
- Valid: 184
- Issues: 35

## Issues to Fix

### train/SCR-TRAIN-003-speaking.html
- [ ] **MISSING_ONCLICK**: Button has no onclick handler
- [ ] **MISSING_ONCLICK**: Button has no onclick handler

### vocab/SCR-VOCAB-002-detail.html
- [ ] **MISSING_ONCLICK**: Button has no onclick handler
```

### 14.9 Integration with CI/CD

Add to your build pipeline:

```yaml
# .github/workflows/ui-validation.yml
- name: Validate Clickable Elements
  run: |
    pip install playwright
    playwright install chromium
    python 04-ui-flow/validate-clickable-elements.py
```

### 14.10 Prohibited Patterns (Re-enforced)

After Playwright validation, these patterns are **FORBIDDEN**:

```html
<!-- FORBIDDEN: Buttons without onclick -->
<button class="w-12 h-12">
  <svg><path d="M6 18L18 6M6 6l12 12"/></svg>
</button>

<!-- REQUIRED: Buttons with onclick -->
<button onclick="location.href='previous.html'" class="w-12 h-12">
  <svg><path d="M6 18L18 6M6 6l12 12"/></svg>
</button>
```

### 14.11 Dual-Platform Validation

Both iPad and iPhone screens MUST pass validation:

```bash
# Validate all (includes both platforms)
python validate-clickable-elements.py

# Or validate specific platform
python validate-clickable-elements.py --module iphone
python validate-clickable-elements.py --module train
```

---

## 15. Screen Count and Flow Synchronization Validation (畫面總數與流程同步驗證)

### 15.1 Overview

⚠️ **CRITICAL REQUIREMENT**: When new screens are created, they MUST be synchronized across multiple files to ensure the UI Flow system remains consistent.

### 15.2 Required Synchronization Points

| File | Update Required | Description |
|------|-----------------|-------------|
| `device-preview.html` | Sidebar menu | Add screen entry to module section |
| `device-preview.html` | Module count | Update `MODULE (N)` count |
| `device-preview.html` | Total count | Update `SCREENS (N)` total |
| `docs/ui-flow-diagram.html` | Screen cards | Add screen card with iframe |
| `docs/ui-flow-diagram.html` | Device badge | Update `N Screens` badge |
| `docs/ui-flow-diagram.html` | Connection arrows | Add navigation arrows if needed |

### 15.3 Post-Screen Creation Checklist

When creating a new screen (e.g., `SCR-SETTING-003a-password.html`):

```markdown
## New Screen Synchronization Checklist

### Screen Files Created
- [ ] iPad version: `setting/SCR-SETTING-003a-password.html`
- [ ] iPhone version: `iphone/SCR-SETTING-003a-password.html`

### device-preview.html Updates
- [ ] Added to sidebar under correct module (e.g., SETTING)
- [ ] Module count updated (e.g., SETTING (11) → SETTING (12))
- [ ] Total screen count updated (e.g., SCREENS (30) → SCREENS (31))
- [ ] `data-iphone` attribute set correctly

### ui-flow-diagram.html Updates
- [ ] Device badge count updated (e.g., "30 Screens" → "31 Screens")
- [ ] Screen card added with correct position
- [ ] iframe src points to correct HTML file
- [ ] Connection arrow added from parent screen
```

### 15.4 Sub-Screen Naming Convention

For child screens (detail pages, sub-settings), use alphabetical suffixes:

| Pattern | Use Case | Example |
|---------|----------|---------|
| `SCR-MODULE-NNN` | Main screen | `SCR-SETTING-003-security` |
| `SCR-MODULE-NNNa` | First sub-screen | `SCR-SETTING-003a-password` |
| `SCR-MODULE-NNNb` | Second sub-screen | `SCR-SETTING-003b-devices` |
| `SCR-MODULE-NNNc` | Third sub-screen | `SCR-SETTING-003c-linked-accounts` |

### 15.5 Sidebar Entry Template

```html
<!-- device-preview.html sidebar entry -->
<div class="screen-item px-3 py-2.5 rounded-lg cursor-pointer"
     onclick="loadScreen('setting/SCR-SETTING-003a-password.html', this)"
     data-iphone="iphone/SCR-SETTING-003a-password.html">
  <span class="text-sm text-gray-700">SCR-SETTING-003a 變更密碼</span>
</div>
```

### 15.6 Screen Card Template

```html
<!-- ui-flow-diagram.html screen card -->
<div class="screen-card module-setting"
     style="left: 1100px; top: 1880px;"
     onclick="openScreen('setting/SCR-SETTING-003a-password.html')">
  <div class="ipad-frame">
    <div class="screen-id">SETTING-003a</div>
    <iframe class="screen-iframe" src="../setting/SCR-SETTING-003a-password.html"></iframe>
  </div>
  <div class="screen-label">SCR-SETTING-003a 變更密碼</div>
</div>
```

### 15.7 Connection Arrow Template

```html
<!-- ui-flow-diagram.html connection arrow -->
<!-- Parent → Child sub-screen (use dashed line for sub-screens) -->
<path d="M 420 1740 L 420 1810 L 1150 1810 L 1150 1880"
      stroke="#64748B" stroke-width="2" fill="none"
      marker-end="url(#arrow-setting)" stroke-dasharray="6,3"/>
```

### 15.8 Automated Count Validation Script

Save as `validate-screen-count.js`:

```javascript
#!/usr/bin/env node
/**
 * Screen Count and Flow Synchronization Validator
 *
 * Validates that:
 * 1. All HTML files in modules are in device-preview.html sidebar
 * 2. Screen counts match actual file counts
 * 3. All screens in sidebar exist in ui-flow-diagram.html
 */

const fs = require('fs');
const path = require('path');

const UI_FLOW_DIR = process.cwd();
const MODULES = ['auth', 'vocab', 'train', 'report', 'setting', 'dash', 'home'];

function countScreenFiles() {
  const counts = {};
  let total = 0;

  for (const module of MODULES) {
    const moduleDir = path.join(UI_FLOW_DIR, module);
    if (fs.existsSync(moduleDir)) {
      const files = fs.readdirSync(moduleDir).filter(f => f.endsWith('.html'));
      counts[module.toUpperCase()] = files.length;
      total += files.length;
    }
  }

  // Count iPhone screens (should match)
  const iphoneDir = path.join(UI_FLOW_DIR, 'iphone');
  if (fs.existsSync(iphoneDir)) {
    counts['IPHONE'] = fs.readdirSync(iphoneDir).filter(f => f.endsWith('.html')).length;
  }

  counts['TOTAL'] = total;
  return counts;
}

function checkDevicePreviewCounts() {
  const previewPath = path.join(UI_FLOW_DIR, 'device-preview.html');
  const content = fs.readFileSync(previewPath, 'utf8');

  const errors = [];
  const fileCounts = countScreenFiles();

  // Check module counts
  for (const [module, count] of Object.entries(fileCounts)) {
    if (module === 'TOTAL' || module === 'IPHONE') continue;

    const regex = new RegExp(`${module}\\s*\\((\\d+)\\)`);
    const match = content.match(regex);

    if (match) {
      const declaredCount = parseInt(match[1]);
      if (declaredCount !== count) {
        errors.push({
          type: 'MODULE_COUNT_MISMATCH',
          module: module,
          declared: declaredCount,
          actual: count,
          fix: `Update "${module} (${declaredCount})" to "${module} (${count})"`
        });
      }
    }
  }

  // Check total screen count
  const totalRegex = /SCREENS\s*\((\d+)\)/;
  const totalMatch = content.match(totalRegex);
  if (totalMatch) {
    const declaredTotal = parseInt(totalMatch[1]);
    if (declaredTotal !== fileCounts.TOTAL) {
      errors.push({
        type: 'TOTAL_COUNT_MISMATCH',
        declared: declaredTotal,
        actual: fileCounts.TOTAL,
        fix: `Update "SCREENS (${declaredTotal})" to "SCREENS (${fileCounts.TOTAL})"`
      });
    }
  }

  return errors;
}

function checkUiFlowDiagramCounts() {
  const diagramPath = path.join(UI_FLOW_DIR, 'docs', 'ui-flow-diagram.html');
  if (!fs.existsSync(diagramPath)) return [];

  const content = fs.readFileSync(diagramPath, 'utf8');
  const errors = [];
  const fileCounts = countScreenFiles();

  // Check screen count in badge
  const badgeRegex = /(\d+)\s*Screens/g;
  let match;
  while ((match = badgeRegex.exec(content)) !== null) {
    const declaredCount = parseInt(match[1]);
    if (declaredCount !== fileCounts.TOTAL) {
      errors.push({
        type: 'DIAGRAM_COUNT_MISMATCH',
        declared: declaredCount,
        actual: fileCounts.TOTAL,
        fix: `Update "${declaredCount} Screens" to "${fileCounts.TOTAL} Screens"`
      });
    }
  }

  return errors;
}

function main() {
  console.log('======================================================================');
  console.log('SCREEN COUNT AND FLOW SYNCHRONIZATION VALIDATION');
  console.log('======================================================================\n');

  const fileCounts = countScreenFiles();
  console.log('File Counts by Module:');
  for (const [module, count] of Object.entries(fileCounts)) {
    console.log(`  ${module}: ${count}`);
  }
  console.log('');

  const previewErrors = checkDevicePreviewCounts();
  const diagramErrors = checkUiFlowDiagramCounts();
  const allErrors = [...previewErrors, ...diagramErrors];

  if (allErrors.length === 0) {
    console.log('✅ All screen counts are synchronized!\n');
    process.exit(0);
  } else {
    console.log(`⛔ Found ${allErrors.length} synchronization issues:\n`);
    for (const error of allErrors) {
      console.log(`  🔴 ${error.type}`);
      console.log(`     Declared: ${error.declared}, Actual: ${error.actual}`);
      console.log(`     Fix: ${error.fix}\n`);
    }
    process.exit(1);
  }
}

main();
```

### 15.9 Validation Workflow

```
Step 1: Create New Screen HTML Files
        ↓
Step 2: Run Screen Count Validation
        node validate-screen-count.js
        │
        ├─→ All counts match?
        │     │
        │     ├─ YES → Continue to Step 3
        │     │
        │     └─ NO  → Fix synchronization issues
        │              ├─→ Update device-preview.html sidebar
        │              ├─→ Update module counts
        │              ├─→ Update total count
        │              └─→ Re-run validation
        ↓
Step 3: Add Screen Card to UI Flow Diagram
        ↓
Step 4: Add Connection Arrows (if applicable)
        ↓
Step 5: Run Clickable Element Validation
        node capture-screenshots.js --validate-only
```

### 15.10 Common Synchronization Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Module count mismatch | New screen added but count not updated | Update `MODULE (N)` in sidebar |
| Total count mismatch | New screen added but total not updated | Update `SCREENS (N)` in header |
| Missing sidebar entry | Screen file exists but not in sidebar | Add `screen-item` div to sidebar |
| Missing screen card | Screen in sidebar but not in diagram | Add screen card to ui-flow-diagram |
| Missing connection | Screen card exists but no arrow | Add SVG path connection |

### 15.11 Verification Commands

```bash
# Count all screens by module
find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l

# List all screens in a module
ls -la setting/SCR-*.html

# Check if screen is in sidebar
grep "SCR-SETTING-003a" device-preview.html

# Check if screen card exists in diagram
grep "SCR-SETTING-003a" docs/ui-flow-diagram.html
```

---

## 16. Index.html Synchronization Validation (首頁同步驗證)

### 16.1 Overview

⚠️ **CRITICAL REQUIREMENT**: The `index.html` file serves as the main overview page for the UI Flow system. When new screens are created, `index.html` MUST be updated to reflect accurate screen counts and screen lists.

### 16.2 Required Synchronization Points

| Element | Location | Update Required |
|---------|----------|-----------------|
| Module screen counts | Module header badges | Update `N 畫面` count |
| Total iPad count | Header badge | Update iPad total |
| Total iPhone count | Header badge | Update iPhone total |
| Screen list items | Module screen lists | Add/remove screen entries |
| Screen links | `onclick` handlers | Verify links work |

### 16.3 Files That Require index.html Updates

When any of these files change, `index.html` MUST be updated:

```markdown
## Trigger Files

### New Screen Added
- [ ] auth/SCR-AUTH-*.html → Update AUTH module count and list
- [ ] home/SCR-HOME-*.html → Update HOME module count and list
- [ ] vocab/SCR-VOCAB-*.html → Update VOCAB module count and list
- [ ] train/SCR-TRAIN-*.html → Update TRAIN module count and list
- [ ] report/SCR-PROG-*.html → Update PROG module count and list
- [ ] setting/SCR-SETTING-*.html → Update SETTING module count and list

### Synchronization Required
- [ ] device-preview.html updated → index.html must match
- [ ] ui-flow-diagram.html updated → index.html must match
```

### 16.4 index.html Structure

```html
<!-- Module Card Structure -->
<div class="module-card module-auth">
  <div class="module-header">
    <span class="module-icon">🔐</span>
    <div>
      <h3>AUTH 認證模組</h3>
      <p>登入、註冊、角色選擇</p>
    </div>
    <span class="module-count">5 畫面</span>  <!-- ⚠️ Must match actual count -->
  </div>
  <div class="screen-list">
    <div class="screen-item" onclick="openScreen('auth/SCR-AUTH-001-login.html')">
      <span class="dot"></span>
      <span>SCR-AUTH-001</span>
      <span>登入頁面</span>
    </div>
    <!-- All screens in module must be listed -->
  </div>
</div>

<!-- Header Badge Structure -->
<div class="badge">
  iPad <span class="count">33</span>  <!-- ⚠️ Must match total iPad screens -->
  iPhone <span class="count">33</span>  <!-- ⚠️ Must match total iPhone screens -->
</div>
```

### 16.5 Validation Script

Add to `validate-screen-count.js`:

```javascript
function checkIndexHtml() {
  const indexPath = path.join(UI_FLOW_DIR, 'index.html');
  if (!fs.existsSync(indexPath)) return [];

  const content = fs.readFileSync(indexPath, 'utf8');
  const errors = [];
  const fileCounts = countScreenFiles();

  // Check each module count
  const modulePatterns = {
    'AUTH': /AUTH[^<]*?(\d+)\s*畫面/,
    'HOME': /HOME[^<]*?(\d+)\s*畫面/,
    'VOCAB': /VOCAB[^<]*?(\d+)\s*畫面/,
    'TRAIN': /TRAIN[^<]*?(\d+)\s*畫面/,
    'PROG': /PROG[^<]*?(\d+)\s*畫面/,
    'SETTING': /SETTING[^<]*?(\d+)\s*畫面/
  };

  for (const [module, pattern] of Object.entries(modulePatterns)) {
    const match = content.match(pattern);
    if (match) {
      const declaredCount = parseInt(match[1]);
      const actualCount = fileCounts[module] || 0;
      if (declaredCount !== actualCount) {
        errors.push({
          type: 'INDEX_MODULE_COUNT_MISMATCH',
          file: 'index.html',
          module: module,
          declared: declaredCount,
          actual: actualCount,
          fix: `Update "${module}...${declaredCount} 畫面" to "${module}...${actualCount} 畫面"`
        });
      }
    }
  }

  // Check total iPad/iPhone counts
  const iPadMatch = content.match(/iPad\s*.*?(\d+)/);
  const iPhoneMatch = content.match(/iPhone\s*.*?(\d+)/);

  if (iPadMatch) {
    const declaredIPad = parseInt(iPadMatch[1]);
    if (declaredIPad !== fileCounts.TOTAL) {
      errors.push({
        type: 'INDEX_IPAD_COUNT_MISMATCH',
        declared: declaredIPad,
        actual: fileCounts.TOTAL,
        fix: `Update iPad count from ${declaredIPad} to ${fileCounts.TOTAL}`
      });
    }
  }

  return errors;
}
```

### 16.6 Post-Screen Creation Checklist (Updated)

When creating a new screen, update ALL of these files:

```markdown
## Complete Synchronization Checklist

### Screen Files Created
- [ ] iPad version: `{module}/SCR-{MODULE}-{NNN}-{name}.html`
- [ ] iPhone version: `iphone/SCR-{MODULE}-{NNN}-{name}.html`

### index.html Updates ⚠️ NEW
- [ ] Module count updated (e.g., "3 畫面" → "5 畫面")
- [ ] Screen item added to module's screen-list
- [ ] iPad total count updated in header
- [ ] iPhone total count updated in header

### device-preview.html Updates
- [ ] Added to sidebar under correct module
- [ ] Module count updated
- [ ] Total screen count updated
- [ ] `data-iphone` attribute set correctly

### ui-flow-diagram.html Updates
- [ ] Device badge count updated
- [ ] Screen card added with correct position
- [ ] iframe src points to correct HTML file
- [ ] Connection arrow added from parent screen
```

### 16.7 Common Synchronization Errors

| Error | File | Fix |
|-------|------|-----|
| Module count mismatch | index.html | Update `N 畫面` badge |
| Missing screen item | index.html | Add `<div class="screen-item">` entry |
| iPad/iPhone count mismatch | index.html | Update header badge counts |
| Broken onclick | index.html | Fix screen path in onclick handler |
| Description mismatch | index.html | Update module description text |

### 16.8 Verification Commands

```bash
# Count screens per module and compare with index.html
for module in auth home vocab train report setting; do
  count=$(ls -1 $module/SCR-*.html 2>/dev/null | wc -l)
  echo "$module: $count screens"
done

# Check if all screens are in index.html
for file in */SCR-*.html; do
  screen_id=$(basename "$file" .html)
  if ! grep -q "$screen_id" index.html; then
    echo "MISSING in index.html: $screen_id"
  fi
done
```

---

## 17. Device-Aware Link Validation (index.html)

### 17.1 Problem Statement

Screen links in `index.html` must navigate to `device-preview.html` with the correct device path:
- **iPhone selected** → `device-preview.html?screen=iphone/SCR-XXX.html`
- **iPad selected** → `device-preview.html?screen={module}/SCR-XXX.html`

### 17.2 Mandatory Rule

```
⚠️ CRITICAL: index.html screen links MUST be device-aware
   - Links must dynamically change based on selected device toggle
   - Static hardcoded links are NOT allowed
   - Use JavaScript onclick handlers with device state variable
```

### 17.3 Correct Implementation Pattern

```html
<!-- Device Toggle (stores current device state) -->
<script>
  let currentDevice = 'iphone'; // Default device

  function switchDevice(device) {
    currentDevice = device;
    // Update toggle button states
    document.getElementById('btn-iphone').classList.toggle('active', device === 'iphone');
    document.getElementById('btn-ipad').classList.toggle('active', device === 'ipad');
    // Update iframe if exists
    const iframe = document.getElementById('flow-iframe');
    if (iframe) {
      iframe.src = 'docs/ui-flow-diagram.html?device=' + device;
    }
  }

  // Navigate to device-preview with correct device path
  function openScreen(ipadPath, iphonePath) {
    const screenPath = currentDevice === 'iphone' ? iphonePath : ipadPath;
    window.location.href = 'device-preview.html?screen=' + screenPath;
  }
</script>

<!-- Screen Links - CORRECT (device-aware) -->
<a onclick="openScreen('auth/SCR-AUTH-001-login.html', 'iphone/SCR-AUTH-001-login.html')"
   class="screen-link cursor-pointer ...">
  <span>SCR-AUTH-001</span>
  <span>登入頁面</span>
</a>

<!-- INCORRECT - hardcoded path (DO NOT USE) -->
<a href="device-preview.html?screen=auth/SCR-AUTH-001-login.html" ...>
```

### 17.4 Screen Link Template

```html
<!-- Module Screen List Item Template -->
<div onclick="openScreen('{module}/SCR-{MODULE}-{NNN}-{name}.html', 'iphone/SCR-{MODULE}-{NNN}-{name}.html')"
     class="screen-link flex items-center justify-between p-3 rounded-lg border border-gray-100 cursor-pointer">
  <div class="flex items-center gap-3">
    <span class="w-2 h-2 rounded-full status-done"></span>
    <span class="font-medium text-gray-700">SCR-{MODULE}-{NNN}</span>
  </div>
  <span class="text-sm text-gray-500">{Screen Name}</span>
</div>
```

### 17.5 Validation Script

```javascript
// Validate device-aware links in index.html
function validateDeviceAwareLinks(indexContent) {
  const errors = [];

  // Check for hardcoded href links to device-preview
  const hardcodedLinks = indexContent.match(/href="device-preview\.html\?screen=[^"]+"/g);
  if (hardcodedLinks && hardcodedLinks.length > 0) {
    errors.push({
      type: 'HARDCODED_DEVICE_LINKS',
      count: hardcodedLinks.length,
      message: 'Found hardcoded device-preview links. Use onclick with openScreen() instead.',
      examples: hardcodedLinks.slice(0, 3)
    });
  }

  // Check for openScreen function definition
  if (!indexContent.includes('function openScreen(')) {
    errors.push({
      type: 'MISSING_OPENSCREEN_FUNCTION',
      message: 'Missing openScreen() function for device-aware navigation'
    });
  }

  // Check for currentDevice variable
  if (!indexContent.includes('currentDevice')) {
    errors.push({
      type: 'MISSING_DEVICE_STATE',
      message: 'Missing currentDevice state variable'
    });
  }

  return errors;
}
```

### 17.6 Migration Checklist

When fixing existing hardcoded links:

```markdown
## Device-Aware Link Migration Checklist

### JavaScript Setup
- [ ] Add `currentDevice` variable (default: 'iphone')
- [ ] Add `switchDevice(device)` function
- [ ] Add `openScreen(ipadPath, iphonePath)` function

### Screen Links Migration
- [ ] Change all `<a href="device-preview.html?screen=...">` to `<div onclick="openScreen(...)"`
- [ ] Each openScreen() call must have TWO paths:
      - First argument: iPad path (e.g., 'auth/SCR-AUTH-001.html')
      - Second argument: iPhone path (e.g., 'iphone/SCR-AUTH-001.html')
- [ ] Add `cursor-pointer` class to clickable elements
- [ ] Remove href attribute (use onclick instead)

### Testing
- [ ] Toggle to iPhone → Click screen → Verify loads iPhone version
- [ ] Toggle to iPad → Click screen → Verify loads iPad version
- [ ] All modules tested (AUTH, VOCAB, TRAIN, HOME, PROG, SETTING)
```

---

