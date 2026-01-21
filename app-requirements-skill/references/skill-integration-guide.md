# Skill Integration Guide (Cross-Skill Integration Guide)

This document defines the integration and collaboration workflow between `app-requirements-skill` and `app-uiux-designer.skill`.

---

## ⚠️ MANDATORY: UI Flow Must Be Generated Through app-uiux-designer.skill

> **This is a blocking rule! Do not manually create UI Flow HTML, must use skill to generate!**

### Mandatory Invocation Method

After SDD is completed, **must** use Skill tool to invoke app-uiux-designer.skill:

```
Tool: Skill
Parameters:
  skill: "app-uiux-designer.skill"
  args: "Please generate HTML UI Flow interactive prototype based on SDD document ({SDD_PATH}).
         Project Information:
         - Project Name: {PROJECT_NAME}
         - Target Device: {DEVICE}
         - Visual Style: {STYLE}
         - Brand Primary Color: {COLOR}
         - Target User: {TARGET_USER}
         Output Directory: {OUTPUT_DIR}"
```

### Prohibited Actions

| Prohibited Item | Reason |
|-----------------|--------|
| ❌ Manually create UI Flow HTML | Must use skill to ensure template compliance |
| ❌ Skip app-uiux-designer.skill | Cannot ensure 100% navigation coverage |
| ❌ Generate UI Flow without Button Navigation | Navigation targets unclear |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Complete App Development Flow                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐         │
│  │ app-requirements-skill│      │ app-uiux-designer.skill│       │
│  │                       │      │                       │        │
│  │  Phase 1: Requirements│      │                       │        │
│  │  Phase 2: SRS Output  │      │                       │        │
│  │  Phase 3: SDD Output  │─────▶│  Phase 4: UI Flow     │        │
│  │                       │      │  Phase 5: Screenshots  │        │
│  │  Phase 6: Doc Backfill│◀─────│  Phase 6: SDD/SRS     │        │
│  │  Phase 7: RTM Verify  │      │           Backfill    │        │
│  │  Phase 8: DOCX Output │      │                       │        │
│  └──────────────────────┘      └──────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Trigger Timing

### app-requirements-skill → app-uiux-designer.skill

| Trigger Condition | Action |
|-------------------|--------|
| Requirements gathering phase starts | Activate uiux skill to ask UI requirements (platform, device, modules, style) |
| SDD output completed | Activate uiux skill to generate HTML UI Flow |
| SDD contains SCR-* blocks | uiux skill generates corresponding screens for each SCR-* |

### app-uiux-designer.skill → app-requirements-skill

| Trigger Condition | Action |
|-------------------|--------|
| UI Flow output completed | Backfill SDD (screenshots, UI prototype references) |
| UI Flow output completed | Backfill SRS (Screen References, Inferred Requirements) |
| Missing screens discovered | Suggest adding REQ-NAV-* navigation requirements |

---

## Data Exchange Format

### SDD → UI Flow (app-requirements-skill output)

**⚠️ Critical: Button Navigation Table (MANDATORY)**

Each SCR-* block **must** contain a Button Navigation table, which is the sole data source for UI Flow navigation.

```markdown
## SCR-AUTH-001-login: Login Screen

**Module:** AUTH
**Priority:** P0
**Related Requirements:** REQ-AUTH-001, REQ-AUTH-002

### Screen Description
User login screen supporting Email/password login and social login.

### UI Component Specifications
| Component ID | Component Type | Specification | Related Requirement |
|--------------|----------------|---------------|---------------------|
| txt_email | TextField | Email input field | REQ-AUTH-001 |
| txt_password | PasswordField | Password input field | REQ-AUTH-001 |
| btn_login | Button | Login button | REQ-AUTH-001 |
| btn_register | Link | Register link | REQ-AUTH-002 |
| btn_forgot | Link | Forgot password link | REQ-AUTH-003 |

### Button Navigation ⚠️ MANDATORY
| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Login | Button | SCR-DASH-001 | Validation success |
| btn_register | Register Now | Link | SCR-AUTH-002-register | - |
| btn_forgot | Forgot Password | Link | SCR-AUTH-003-forgot | - |
| btn_apple | Apple Login | Button | SCR-DASH-001 | Apple auth success |
| btn_google | Google Login | Button | SCR-DASH-001 | Google auth success |
```

### Button Navigation → Template Variable Mapping

app-uiux-designer.skill uses Button Navigation table to auto-fill template variables:

| SDD Target Screen | Template Variable | Description |
|-------------------|-------------------|-------------|
| `SCR-AUTH-002-register` | `{{TARGET_REGISTER}}` | Registration page |
| `SCR-AUTH-003-forgot` | `{{TARGET_FORGOT_PASSWORD}}` | Forgot password page |
| `SCR-DASH-001` | `{{TARGET_AFTER_LOGIN}}` | Home page after login |
| `(current)` | `#` | Stay on current page |
| `(back)` | `{{TARGET_BACK}}` | Return to previous page |
| `(modal)` | `showModal('...')` | Show dialog |

### Navigation Resolution Priority

app-uiux-designer.skill resolves navigation targets in the following priority order:

```
1️⃣ SDD Button Navigation Table (Priority)
   ↓ If Target Screen field exists, use directly

2️⃣ Smart Prediction (Fallback)
   ↓ If SDD doesn't provide, predict based on naming conventions

3️⃣ Default Value (Last Resort)
   ↓ When unable to determine, use # or (current)
```

**Benefits:**
- Complete SDD → Zero prediction, 100% accurate
- Incomplete SDD → Prediction mechanism ensures UI Flow can still be generated
- Backward compatible → Old projects don't need to rewrite SDD

### UI Flow → SDD Backfill (app-uiux-designer.skill output)

```markdown
## SCR-AUTH-001-login: Login Screen

... (original content) ...

### UI Prototype Reference
| Platform | Screenshot | HTML Prototype |
|----------|------------|----------------|
| iPad | ![](images/ipad/SCR-AUTH-001-login.png) | [View](04-ui-flow/auth/SCR-AUTH-001-login.html) |
| iPhone | ![](images/iphone/SCR-AUTH-001-login.png) | [View](04-ui-flow/iphone/SCR-AUTH-001-login.html) |
```

### UI Flow → SRS Backfill (app-uiux-designer.skill output)

```markdown
## Screen References

| Requirement ID | Related Screens | Description |
|----------------|-----------------|-------------|
| REQ-AUTH-001 | SCR-AUTH-001-login | Login screen implementation |
| REQ-AUTH-002 | SCR-AUTH-002-register | Registration screen implementation |

## Inferred Requirements (UI-Derived Requirements)

| ID | Source | Description | Acceptance Criteria |
|----|--------|-------------|---------------------|
| REQ-NAV-001 | SCR-AUTH-001 Login button | Navigate to Dashboard after successful login | After credential verification, display SCR-DASH-001 |
| REQ-NAV-002 | SCR-AUTH-001 Register link | Click register navigates to registration page | Display SCR-AUTH-002 |
```

---

## Validation Checkpoints

### Checkpoint 1: After SDD Output (Before Starting UI Flow)

```
☑ SDD contains all SCR-* blocks
☑ Each SCR-* has UI element table
☑ Each UI element specifies target screen (if applicable)
☑ REQ ↔ SCR mapping complete
```

### Checkpoint 2: After UI Flow Output

```
☑ All SCR-* have corresponding HTML files
☑ iPad and iPhone versions both exist
☑ Clickable element coverage = 100%
☑ Navigation completeness verification passed
☑ Screenshots generated
```

### Checkpoint 3: After Backfill (Final Verification)

```
☑ SDD contains all screenshots
☑ SRS contains Screen References
☑ SRS contains Inferred Requirements
☑ RTM coverage = 100%
☑ DOCX regenerated
```

---

## ⚠️ Mandatory Specifications

### UI Flow Template Usage (MANDATORY)

app-uiux-designer.skill **must** follow when generating UI Flow:

| Rule | Description |
|------|-------------|
| ❌ **Prohibited** | Create custom HTML files from scratch |
| ✅ **Required** | Copy `~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/` templates |
| ✅ **Required** | Replace `{{VARIABLE}}` variables in templates |
| ✅ **Required** | Create screens according to template directory structure |

### Template Copy Commands

```bash
# Copy templates to project
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/* ./04-ui-flow/

# Templates include:
# - index.html (Screen overview)
# - device-preview.html (Multi-device preview)
# - screen-template-iphone.html (iPhone screen template)
# - screen-template-ipad.html (iPad screen template)
# - capture-screenshots.js (Screenshot script)
```

---

## Error Handling

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| UI Flow missing screens | SCR-* definitions incomplete in SDD | Supplement SDD SCR-* blocks |
| Clickable elements have no target | SDD didn't specify target screen | Update SDD UI element table |
| Screenshot embedding failed | Incorrect path | Verify images/ directory structure |
| RTM coverage insufficient | Requirements not mapped to screens | Supplement Screen References |

### Fallback Strategy

If app-uiux-designer.skill is unavailable:

1. **Basic UI Flow**: Manually create simplified UI Flow (text description only)
2. **ASCII Wireframe**: Use ASCII wireframes in SDD (note DOCX conversion limitations)
3. **External Tools**: Use Figma/Sketch to create designs, manually embed

---

## Execution Commands

### Complete Flow

```bash
# 1. Requirements Gathering (app-requirements-skill leads)
# UI requirements asked automatically at startup

# 2. SRS/SDD Output
# Auto-generate 01-planning/SRS-*.md and 02-design/SDD-*.md

# 3. UI Flow Output (app-uiux-designer.skill)
cd 04-ui-flow
# HTML files auto-generated

# 4. Screenshots and Verification
npm install puppeteer --save-dev
node capture-screenshots.js

# 5. Document Backfill
# uiux skill auto-backfills SDD and SRS

# 6. DOCX Output
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-*.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-*.md
```

### Verification Only

```bash
cd 04-ui-flow
node capture-screenshots.js --validate-only
```

---

## File Structure Mapping

```
project/
├── 01-planning/
│   ├── SRS-{project}.md          ← app-requirements-skill
│   └── SRS-{project}.docx        ← app-requirements-skill
├── 02-design/
│   ├── SDD-{project}.md          ← app-requirements-skill + uiux backfill
│   ├── SDD-{project}.docx        ← app-requirements-skill
│   └── images/
│       ├── ipad/*.png            ← app-uiux-designer.skill
│       └── iphone/*.png          ← app-uiux-designer.skill
├── 04-ui-flow/                   ← app-uiux-designer.skill
│   ├── index.html
│   ├── device-preview.html
│   ├── docs/ui-flow-diagram.html
│   ├── shared/
│   │   ├── project-theme.css
│   │   └── notify-parent.js
│   ├── auth/
│   ├── dash/
│   └── iphone/
└── 07-traceability/
    └── RTM-{project}.md          ← app-requirements-skill
```

---

## Version Compatibility

| app-requirements-skill | app-uiux-designer.skill | Status |
|------------------------|-------------------------|--------|
| v1.0+ | v1.0+ | Compatible |

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-09 | 1.1 | Added mandatory template usage specification |
| 2026-01-09 | 1.0 | Initial version, defined integration architecture and data exchange format |
