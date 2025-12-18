---
name: app-uiux-designer
description: |
  Enterprise-grade UI/UX design expert. **SRS/SDD → Batch UI Generation** (HTML/React/Angular/SwiftUI/Compose) + **100% Coverage Validation** (RTM/Gap Analysis). Features: Visual Style Extraction, Production-Ready Assets (Android drawable-*/iOS Assets.xcassets/Web favicon), **Motion Design** (Micro-interactions/Lottie), **Dark Mode**, **UX Writing**, **Data Visualization**, **i18n/RTL Localization**, **Design Review** (Nielsen 10 Heuristics), HIG/Material Design 3/WCAG. 17 professional reference docs covering the complete design-to-delivery workflow.
---

# UI/UX Designer Skill

Enterprise-grade App & Web UI/UX design guide covering the complete design-to-delivery workflow.

**Core Capabilities:** SRS/SDD → Batch UI Generation + 100% Coverage Validation | Visual Style Extraction | Production-Ready Asset Output
**Advanced Features:** Motion Design | Dark Mode | UX Writing | Data Visualization | i18n Localization | Design Review
**Platform Guidelines:** iOS HIG | Android Material 3 | Web WCAG | Figma | 17 Professional Reference Docs

---

## Defaults

### Platform Defaults
- **Default Platform:** Mobile App UI/UX (iOS/Android guidelines prioritized)
- **Default Dimensions:** iPhone 14 Pro (390 x 844 pt) / Android Medium (360 x 800 dp)
- **Default Format:** HTML + Tailwind CSS (browser-previewable)

### UI Review Output Defaults
When performing UI/UX Review, default outputs include:
1. **Interactive HTML Prototype** - All screens as standalone HTML files
2. **index.html Entry Page** - Complete navigation directory
3. **ui-flow-diagram.html** - Interactive screen flow diagram (Wireflow)
4. **Full Page Links** - All Buttons & Links clickable with proper navigation
5. **Mobile Frame Preview** - Device frame simulation preview

### Screen ID Standard Format (Synced with medical-software-requirements-skill) 🆔

To ensure traceability with IEC 62304 documents (SDD/RTM), all screens must use the **SCR-* standard format**:

```
ID Format: SCR-{MODULE_CODE}-{3-DIGIT_NUMBER}

Module Code Reference:
├── AUTH    → Authentication (Login/Register/Forgot Password/Profile)
├── ONBOARD → Onboarding (Product Intro/Tutorial)
├── DASH    → Dashboard/Home
├── TRAIN   → Training Module
├── REWARD  → Rewards Module
├── REPORT  → Reports Module
├── DEVICE  → Device Module
├── SETTING → Settings Module
└── COM     → Common Components

Examples:
├── SCR-AUTH-001   → Login Screen
├── SCR-AUTH-007   → Create Profile
├── SCR-ONBOARD-001 → Product Introduction
├── SCR-DASH-001   → Home Screen
└── SCR-TRAIN-001  → Training Center
```

**File Naming Convention:**
```
HTML Files: SCR-{MODULE}-{NUMBER}-{description}.html
Screenshot Files: SCR-{MODULE}-{NUMBER}-{description}.png
SVG Files: SCR-{MODULE}-{NUMBER}-{description}.svg

Examples:
├── SCR-AUTH-001-login.html
├── SCR-AUTH-001-login.png
└── SCR-AUTH-001-login.svg
```

### Interactive Navigation Standards
Generated HTML UI must follow:
```
📁 generated-ui/
├── 📄 index.html              # Entry page - Screen overview & navigation (embeds ui-flow-diagram)
├── 📄 nav.html                # Shared navigation component (embeddable)
├── 📁 docs/
│   ├── ui-flow-diagram.html   # Interactive Wireflow diagram (zoomable, draggable)
│   └── flow-diagram.md        # Mermaid format flowchart (embeddable in SDD)
├── 📁 shared/
│   ├── theme.css              # Design System CSS
│   └── navigation.js          # Navigation logic
├── 📁 screenshots/            # Module screen captures (for ui-flow-diagram & SDD)
│   ├── auth/                  # SCR-AUTH-001-login.png...
│   ├── onboard/               # SCR-ONBOARD-001-product-intro.png...
│   └── [modules]/
├── 📁 auth/
│   ├── SCR-AUTH-001-login.html
│   ├── SCR-AUTH-002-register.html
│   └── SCR-AUTH-003-forgot-password.html
├── 📁 onboard/
│   ├── SCR-ONBOARD-001-product-intro.html → SCR-ONBOARD-002 → ... → SCR-DASH-001
└── 📁 [other-modules]/
    └── SCR-{MODULE}-{NUMBER}-{description}.html
```

### Button/Link Navigation Rules
All interactive elements must implement actual navigation:
- **Primary Button (Next/Confirm):** `onclick="location.href='next-page.html'"`
- **Secondary Button (Back):** `onclick="history.back()"` or explicit link
- **Text Link:** `<a href="target.html">Link text</a>`
- **Tab Bar / Bottom Nav:** Each tab links to corresponding page
- **Card Click:** Links to detail page
- **List Item:** Links to corresponding detail or action page

### Link Validation Workflow 🔗
After generating UI, link validation must be performed to ensure all navigation works:

**Step 1: Scan All Links**
```bash
# List all href and onclick links
grep -roh "href=['\"][^'\"]*\.html['\"]" --include="*.html" | sort | uniq -c | sort -rn
grep -roh "location.href=['\"][^'\"]*\.html['\"]" --include="*.html" | sort | uniq -c | sort -rn
```

**Step 2: Check Non-existent File Links**
```bash
# Search for common error patterns (non-existent filenames)
grep -r "href=.*DEVICE-004-list\|REPORT-002-sleep-log\|REPORT-004-weekly" --include="*.html"
```

**Step 3: Common Link Errors**
| Error Type | Example | Fix |
|------------|---------|-----|
| Wrong module path | `../report/DASH-002.html` | Change to `DASH-002.html` (same module) |
| Non-existent file | `DEVICE-004-list.html` | Change to `DEVICE-001-status.html` |
| Wrong number | `REPORT-004-weekly.html` | Change to `REPORT-002-weekly.html` |

**Step 4: Back Button Rules in iframes**
When UI is embedded in iframe (e.g., device-preview.html):
- ❌ Avoid: `<a href="../index.html">` (loads index inside iframe)
- ✅ Correct: `<button onclick="history.back()">Back</button>` (properly returns to previous page)

**Step 5: Image Path Validation**
Files in module folders (auth/, device/, dash/, etc.) referencing assets:
- ✅ Correct: `src="../assets/napi/cheers.png"` (one level up)
- ❌ Wrong: `src="../../assets/napi/cheers.png"` (two levels up - incorrect path)

```bash
# Check for incorrect image paths
grep -r 'src="../../assets/' --include="*.html"
```

**Step 6: Validation Checklist**
- [ ] All href targets exist
- [ ] All onclick location.href targets exist
- [ ] Back buttons in iframes use `history.back()`
- [ ] Cross-module link paths correct (../module/file.html)
- [ ] Same-module links have no extra path (file.html)
- [ ] Image path levels correct (../assets/ not ../../assets/)

## Core Capabilities

### 1. Spec-Driven Batch UI Generation 📋
Read SRS/SDD/PRD spec documents, auto-parse requirements and batch generate complete UI screen series. See [references/spec-driven-generation.md](references/spec-driven-generation.md)
- **Supported File Formats:** .md / .docx / .pdf / .txt
- **Parseable Document Types:** SRS (Software Requirements), SDD (Design Document), PRD (Product Requirements), FSD (Functional Spec)
- **Auto-extraction:** Functional requirements, user stories, use cases, screen specs, data models
- **Batch Generation:** Module-based, generate all screens at once
- **Output Directory:** Structured directory with README and screen list
- **Generation Report:** Auto-generate summary and follow-up recommendations

### 2. 100% Coverage Validation ✅
Validate UI/UX output against SRS/SDD spec documents for complete mapping, ensuring 100% Coverage. See [references/coverage-validation.md](references/coverage-validation.md)
- **Requirements Traceability Matrix (RTM):** Map each requirement ID to UI screens and components
- **Coverage Calculation:** Functional coverage, screen coverage, component coverage
- **Gap Analysis:** Auto-identify uncovered requirements, generate remediation plan
- **Code Annotation:** Annotate @requirements in generated UI code
- **Validation Reports:** COVERAGE-REPORT.md, TRACEABILITY-MATRIX.md, GAP-ANALYSIS.md
- **JSON Output:** requirements-map.json, coverage-summary.json
- **Coverage Certification:** Generate formal verification certificate upon 100% coverage

### 3. Auto UI Screen Generation 🖥️
Auto-generate complete executable UI screen code from requirements description. See [references/ui-generation.md](references/ui-generation.md)
- **HTML/Tailwind** - Browser-previewable interactive prototypes
- **React/Next.js** - Complete React components (styled-components/Tailwind)
- **Angular** - Complete Angular components (Standalone Components/SCSS)
- **iOS SwiftUI** - Native iOS/macOS UI code
- **Android Compose** - Native Android UI code
- **SVG** - Vector mockups (importable to Figma/Sketch)
- **Figma JSON** - Structured data directly importable to Figma
- Support 30+ page type templates (Login, Home, List, Detail, Cart...)
- Auto-apply extracted styles for consistent UI

### 4. Visual Style Extraction & Replication 🎨
Extract visual styles from reference images and auto-apply to UI generation. See [references/style-extraction.md](references/style-extraction.md)
- Color analysis and palette extraction
- Font identification and alternative suggestions
- Shape style analysis (border-radius, density)
- Effect extraction (Glassmorphism/Neumorphism/shadows)
- Auto-generate style tokens
- Figma Styles/Variables output

### 5. Asset Extraction & Production-Ready Output 📦
Identify and extract Icons, illustrations, UI components from images, generate platform-ready asset directories. See [references/asset-extraction.md](references/asset-extraction.md)
- Icon identification and style analysis (Outlined/Filled/Duotone)
- Illustration element extraction and categorization
- UI component spec extraction (Button/Card/Input)
- **Production-Ready Output:**
  - Android: drawable-ldpi/mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi + Vector Drawable + Adaptive Icon
  - iOS: Assets.xcassets (@1x/@2x/@3x) + AppIcon.appiconset + Contents.json
  - Web: SVG/PNG + Complete Favicon set + PWA manifest + OG Images
- Copy directly to project, ready to use
- Figma Asset Library creation
- React/iOS/Android Icon Component generation

### 6. Platform Design Guidelines
- **iOS**: Human Interface Guidelines (HIG), see [references/ios-guidelines.md](references/ios-guidelines.md)
- **Android**: Material Design 3, see [references/android-guidelines.md](references/android-guidelines.md)
- **Web**: Responsive Design & Web Standards, see [references/web-guidelines.md](references/web-guidelines.md)

### 7. Flow Prediction & Completion 🔮
Intelligently predict app flows when spec documents are incomplete. See [references/flow-prediction.md](references/flow-prediction.md)
- Spec gap analysis and identification
- **Button Navigation Auto-inference** (Button Flow Inference)
- Universal flow patterns (Auth, CRUD, Checkout, Settings)
- Industry-specific flow templates (E-commerce, Social, Finance, Health)
- Screen state prediction (Empty/Loading/Error/Success)
- Flow output (Mermaid, Figma, JSON)

### 8. Figma Design Output
Complete Figma workflow and output standards. See [references/figma-guidelines.md](references/figma-guidelines.md)
- Auto Layout setup and best practices
- Components and Variants architecture
- Design Tokens / Variables system
- Multi-format export (CSS, iOS Swift, Android Kotlin, JSON)

### 9. Design System
Build scalable design systems. See [references/design-system.md](references/design-system.md)
- Design Tokens (colors, fonts, spacing, border-radius)
- Component library architecture
- Design-to-code sync strategy

### 10. User Research
Complete UX research methodology. See [references/ux-research.md](references/ux-research.md)
- User interviews and Personas
- Competitive analysis
- User journey maps

### 11. Accessibility Design
WCAG 2.1 compliant. See [references/accessibility.md](references/accessibility.md)

### 12. Motion Design 🎬
Complete animation and micro-interactions design guide. See [references/motion-design.md](references/motion-design.md)
- Duration and easing standards
- Transition animation patterns
- Micro-interactions design
- Lottie/Rive animation output
- Reduced Motion accessibility

### 13. Dark Mode 🌙
Complete Dark Mode design system. See [references/dark-mode.md](references/dark-mode.md)
- Surface levels and color system
- Contrast and text opacity
- Component adaptation and image handling
- Tri-state toggle (Light/Dark/System)
- Platform implementation (iOS/Android/Web)

### 14. UX Writing ✍️
UX copy design guide. See [references/ux-writing.md](references/ux-writing.md)
- Voice & Tone brand voice
- Buttons, headings, forms, error messages
- Empty state, loading state copy
- Terminology consistency and glossary
- Character limits and i18n considerations

### 15. Data Visualization 📊
Charts and Dashboard design guide. See [references/data-visualization.md](references/data-visualization.md)
- Chart type selection guide
- Color usage and color-blind friendly design
- Dashboard layout patterns
- Interaction design and Tooltips
- Code output (Chart.js/SwiftUI/Compose)

### 16. Internationalization Design 🌍
i18n/L10n internationalization design guide. See [references/localization.md](references/localization.md)
- Text expansion strategies
- RTL layout support
- Date/number/currency formatting
- Cultural considerations and imagery
- Pseudo-localization testing

### 17. Design Review 🔍
Design quality and review workflow. See [references/design-review.md](references/design-review.md)
- Nielsen 10 Heuristic Evaluation
- Design QA checklist
- Design debt tracking
- Design Decision Records (DDR)
- Developer acceptance workflow

### 18. Psychology Validation 🧠 (Integrated with medical-software-requirements-skill)
Validate UI design against design psychology principles. See [references/psychology-validation.md](references/psychology-validation.md)

#### Validation Items
| Psychology Principle | Validation Content | Source |
|---------------------|-------------------|--------|
| **Cognitive Load** | Elements per page, options ≤7 | design-psychology.md |
| **Progressive Disclosure** | Step indicators, pagination | design-psychology.md |
| **Prerequisites** | Logical flow order (Dashboard first) | design-psychology.md |
| **Fitts' Law** | Button size ≥44px, reasonable position | design-psychology.md |
| **Hick's Law** | Primary options ≤7 | design-psychology.md |
| **Mental Model** | Platform conventions (iOS/Android) | cognitive-psychology.md |
| **Error Prevention** | Confirmation dialog for dangerous actions | cognitive-psychology.md |
| **Feedback** | Visual/text feedback after actions | cognitive-psychology.md |

#### Validation Commands
```bash
# Validate generated UI
validate-psychology ./generated-ui/

# Output report
validate-psychology ./generated-ui/ --output ./reports/psychology-report.md
```

#### Validation Report
```markdown
## Psychology Validation Report

### Summary
| Principle | Status | Issues |
|-----------|--------|--------|
| Cognitive Load | ✅ Pass | 0 |
| Fitts' Law | ⚠️ Warning | 2 |
| Error Prevention | ❌ Fail | 1 |

### Detailed Issues
1. **SCR-SETTING-001** - Fitts' Law Violation
   - Issue: Logout button too small (32px < 44px)
   - Recommendation: Increase button height to 44px or above

2. **SCR-DEVICE-002** - Error Prevention Violation
   - Issue: Device reset has no confirmation dialog
   - Recommendation: Add confirmation Modal
```

### 19. SRS/SDD Feedback 📝 (Integrated with medical-software-requirements-skill)
Auto-sync UI generation results back to SRS and SDD documents, ensuring IEC 62304 traceability completeness. See [references/sdd-feedback.md](references/sdd-feedback.md)

#### Feedback Items
| Item | Description | SRS | SDD | RTM |
|------|-------------|:---:|:---:|:---:|
| **Button Navigation** | Auto-inferred button navigation | ✅ | ✅ | ✅ |
| **User Flows** | Inferred screen transition flows | ✅ | ✅ | - |
| **UI Screenshots** | SCR-*.png/svg screen captures | - | ✅ | - |
| **Mermaid Flowcharts** | Screen flow diagrams | ✅ | ✅ | - |
| **Requirements Supplement** | Inferred new requirements | ✅ | - | ✅ |
| **Acceptance Criteria** | Button operation ACs | ✅ | - | - |
| **Traceability Updates** | SRS↔SCR ID mapping | - | - | ✅ |

#### Feedback Workflow
```
After UI generation completes:
1. Scan generated-ui/ outputs
2. Parse Button Navigation (with inference markers)
3. Collect screenshots/
4. Generate Mermaid flowcharts
5. Read SDD.md and locate target sections
6. Update SDD (screenshots, flowcharts, Button Navigation)
7. Read SRS.md and locate target sections
8. Update SRS (requirements, user flows, acceptance criteria)
9. Update RTM (SRS↔SDD↔SCR traceability)
10. Regenerate SRS.docx and SDD.docx
```

#### SRS Feedback Details

Inferred UI flows are fed back to the following SRS sections:

| SRS Section | Feedback Content | Example |
|-------------|------------------|---------|
| **Functional Requirements** | Add inferred requirements | `SRS-AUTH-015: Navigate to onboarding after profile creation` |
| **User Flows** | Update User Flow description | `Create file → Enter Onboarding flow` |
| **Acceptance Criteria** | Button operation ACs | `AC: Clicking "Create File" should navigate to ONBOARD-001` |
| **Screen Requirements** | SCR ID to SRS mapping | `SCR-AUTH-007 maps to SRS-AUTH-010~015` |

#### Feedback Commands
```bash
# Full feedback (SRS + SDD + RTM)
feedback-docs --srs ./docs/SRS.md --sdd ./docs/SDD.md --rtm ./docs/RTM.md --from ./generated-ui/

# SDD only
feedback-sdd ./docs/SDD.md --from ./generated-ui/

# SRS only (requirements and acceptance criteria)
feedback-srs ./docs/SRS.md --from ./generated-ui/

# Specific items only
feedback-sdd ./docs/SDD.md --screenshots-only
feedback-srs ./docs/SRS.md --requirements-only
feedback-srs ./docs/SRS.md --acceptance-criteria-only
```

#### Feedback Report
```markdown
## SRS/SDD Feedback Report

### Summary
- Updated: 2024-XX-XX HH:MM
- Source Directory: ./generated-ui/
- Target Documents: SRS.md, SDD.md, RTM.md

### SRS Updates
| Item | Status | Count |
|------|--------|-------|
| Requirements Supplement | ✅ Updated | 5 items |
| User Flows | ✅ Updated | 8 flows |
| Acceptance Criteria | ✅ Updated | 12 items |

### SDD Updates
| Item | Status | Count |
|------|--------|-------|
| Button Navigation | ✅ Updated | 45 items |
| UI Screenshots | ✅ Updated | 51 images |
| Mermaid Flowcharts | ✅ Updated | 8 modules |

### RTM Updates
| Item | Status | Count |
|------|--------|-------|
| SRS↔SCR Mapping | ✅ Updated | 51 items |
| New Traceability Items | ✅ Updated | 5 items |

### Inferred Items (Requires Manual Review)
| Screen | Button | Inferred Target | Suggested SRS | Confidence |
|--------|--------|-----------------|---------------|------------|
| SCR-AUTH-007 | Create File | SCR-ONBOARD-001 | SRS-AUTH-015 | 🟡 Medium |
| SCR-TRAIN-010 | Complete | SCR-DASH-001 | SRS-TRAIN-020 | 🟡 Medium |

### New SRS Requirement Template
Suggested requirements to add to SRS:

#### SRS-AUTH-015 (Suggested)
| Field | Content |
|-------|---------|
| Requirement ID | SRS-AUTH-015 |
| Description | After creating child profile, system should auto-navigate to onboarding flow |
| Source | UI Flow Inference (SCR-AUTH-007 → SCR-ONBOARD-001) |
| Acceptance Criteria | AC1: After clicking "Create File", auto-navigate to ONBOARD-001 |
| Traceability | SCR-AUTH-007, SDD-AUTH-007 |

### Follow-up Actions
- [ ] Confirm inferred Button Navigation
- [ ] Review and add suggested SRS requirements
- [ ] Regenerate SRS.docx and SDD.docx
- [ ] Verify RTM 100% traceability
```

---

## Visual Style Extraction 🎨

### Style Analysis Dimensions

```
Extract from reference images:

🎨 Colors → Primary/Palette/Semantic
🔤 Typography → Font family/Weight/Scale
📐 Shapes → Border-radius/Density/Spacing
✨ Effects → Shadows/Blur/Borders
🖼️ Imagery → Photography/Illustration/Icon style
🎭 Mood → Modern/Classic/Playful/Professional
```

### Supported Style Types

| Style | Characteristics | Extracted Elements |
|-------|-----------------|-------------------|
| **Flat** | Flat, no shadows | Color blocks, lines |
| **Material** | Layered, shadows | Elevation, Motion |
| **Glassmorphism** | Glass, blur | Transparency, backdrop-filter |
| **Neumorphism** | Raised, recessed | Dual-direction shadows |
| **Gradient** | Gradients, rich | Color transitions |
| **Dark Mode** | Dark backgrounds | Contrast, glow effects |
| **Minimal** | Minimalist, whitespace | Spacing, typography |

### Style Extraction Output Example

**Input:** Upload reference image

**Output:**
```
🎨 Style Extraction Report

Overall Style: Dark Glassmorphism + Gradient
Mood: Modern tech, Professional, Energetic

┌─────────────────────────────────────────┐
│ Color Extraction                         │
├─────────────────────────────────────────┤
│ Primary:   #6366F1 (Indigo)             │
│ Secondary: #EC4899 (Pink)               │
│ Background: #0F172A (Slate 900)         │
│ Surface:   #1E293B (Slate 800)          │
│ Text:      #F8FAFC (Slate 50)           │
│ Scheme:    Complementary (Blue-purple + Pink) │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Typography Extraction                    │
├─────────────────────────────────────────┤
│ Heading: Geometric Sans → Poppins       │
│ Body:    Neo-Grotesque → Inter          │
│ Scale:   1.25 (Major Third)             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Shape Extraction                         │
├─────────────────────────────────────────┤
│ Border-radius: Medium-Large (16-24px)   │
│ Buttons: Full-round (Pill)              │
│ Density: Standard (16-24px spacing)     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Effect Extraction                        │
├─────────────────────────────────────────┤
│ Type: Glassmorphism                      │
│ Background: rgba(255,255,255,0.1)       │
│ Blur: backdrop-filter: blur(10px)       │
│ Border: 1px solid rgba(255,255,255,0.2) │
│ Shadow: Colored glow (Primary color)    │
└─────────────────────────────────────────┘
```

### Generate Consistent Style UI

Auto-generate based on extraction results:

```
┌─────────────────────────────────────────┐
│ Figma Output                             │
├─────────────────────────────────────────┤
│ ✅ Color Styles (12)                     │
│ ✅ Text Styles (9)                       │
│ ✅ Effect Styles (5)                     │
│ ✅ Variables Collection                  │
│ ✅ Sample Components (Button, Card, Input) │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Code Output                              │
├─────────────────────────────────────────┤
│ ✅ CSS Variables                         │
│ ✅ Tailwind Config                       │
│ ✅ Design Token JSON                     │
│ ✅ iOS Swift Colors                      │
│ ✅ Android Compose Theme                 │
└─────────────────────────────────────────┘
```

---

## Flow Prediction

### Button Navigation Auto-inference (Button Flow Inference) 🔗

When SDD spec doesn't explicitly define button navigation, auto-infer targets based on button text and screen context:

#### Inference Rules

| Button Text | Inferred Target | Confidence | Notes |
|-------------|-----------------|------------|-------|
| Back, Previous | `history.back()` | 🟢 High | Return to previous page |
| Next, Continue | Next screen in module | 🟢 High | Flow step |
| Confirm, Submit | Complete flow → Success/Home | 🟢 High | Form submission |
| Cancel | `history.back()` or close Modal | 🟢 High | - |
| Sign In, Login | Home (DASH/HOME-001) | 🟢 High | Auth success |
| Sign Up, Register | Registration flow start | 🟢 High | - |
| Forgot Password | AUTH-*-forgot-password | 🟢 High | - |
| Create, Add, New | Next flow or Onboarding | 🟡 Medium | Context-dependent |
| Save | Return to list or detail | 🟡 Medium | Edit complete |
| Delete, Remove | Confirm Modal → Return to list | 🟡 Medium | Requires confirmation |
| Settings | SETTING-001-home | 🟡 Medium | - |
| Home | DASH-001-home | 🟢 High | - |

#### Inference Logic

```
1. Parse screen ID → Determine module and flow position
2. Scan all Button/Link elements
3. Match button text to inference rules
4. Adjust target based on screen context:
   - Onboarding flow → Continue to next step
   - Form page → Proceed to next stage on success
   - List page → Click item for detail
   - Detail page → Return to list or edit
5. Generate complete navigation links
```

#### Auto-completion Check Flow

Auto-execute after UI generation:

```bash
# 1. Scan buttons without navigation
grep -rh "button\|Button" --include="*.html" | grep -v "onclick\|href"

# 2. List all screen-to-screen links
grep -roh "location.href=['\"][^'\"]*" --include="*.html" | sort | uniq

# 3. Check orphan screens (no entry point)
# 4. Verify flow completeness (each flow has clear endpoint)
```

#### Inference Result Markers

Mark inference source in generated HTML:

```html
<!-- Explicit spec -->
<button onclick="location.href='next.html'">Next</button>

<!-- Auto-inferred (marked with data-inferred) -->
<button onclick="location.href='AUTH-006.html'" data-inferred="button-text:Back">
  Back
</button>
```

### Prediction Confidence Levels

```
🟢 High Confidence: Industry standard flows (Login, Register, Checkout)
🟡 Medium Confidence: Common UX patterns (Onboarding, Settings)
🟠 Low Confidence: Business logic related (needs confirmation)
```

### Spec Gap Auto-identification

```
Analyze input specs
     ↓
Identify gap types
├── Flow gaps (Entry/Branch/Exception)
├── Screen gaps (Undefined states)
├── Interaction gaps (Feedback/Gestures)
└── Platform gaps (iOS/Android differences)
     ↓
Apply flow templates
     ↓
Generate predictions
     ↓
Mark "Predicted" vs "Confirmed"
```

### Universal Flow Patterns

| Flow | Predicted Screens | Confidence |
|------|-------------------|------------|
| Auth (Login/Register) | 8-12 pages | 🟢 High |
| Onboarding | 3-5 pages | 🟢 High |
| CRUD (Create/Read/Update/Delete) | 6-10 pages | 🟢 High |
| Checkout/Purchase | 8-12 pages | 🟢 High |
| Settings | 5-8 pages | 🟡 Medium |
| Profile | 4-6 pages | 🟡 Medium |

### Industry-specific Flow Templates

| Industry | Core Flows | Predicted Screens |
|----------|------------|-------------------|
| E-commerce | Browse, Cart, Order, Membership | 25-35 pages |
| Social | Feed, Post, Interaction, Profile | 30-45 pages |
| Finance | Account, Transaction, History, Verification | 25-40 pages |
| Health | Dashboard, Records, Training, Analytics | 20-30 pages |
| Productivity | Workspace, Tasks, Calendar, Collaboration | 20-30 pages |

### Screen State Prediction

Auto-predict following states for each functional screen:

```
List Page:
├── Default (with data)
├── Empty (empty state)
├── Loading
├── Error
└── Load More

Form Page:
├── Default (blank)
├── Filled (with data)
├── Validation Error
├── Submitting
└── Submit Error

Detail Page:
├── Default (success)
├── Loading
└── Error (data not found)
```

### Prediction Output Example

**Input Spec (incomplete):**
```
Feature: User Login
- Support Email login
- Support Google login
```

**Prediction Output:**
```
🔮 Flow Prediction Report

Identified Gaps:
├── ⚠️ Forgot password flow undefined
├── ⚠️ Registration flow not mentioned
├── ⚠️ Error handling not specified
└── ⚠️ Session expiration handling undefined

Prediction (Confidence: 🟢 High):

Screen List:
├── Login Page
│   ├── Default
│   ├── Loading
│   ├── Error - Wrong password
│   └── Error - Account not found
├── Register Page [Predicted]
│   ├── Step 1: Account
│   ├── Step 2: Info
│   └── Step 3: Verification
├── Forgot Password [Predicted]
│   ├── Enter Email
│   ├── Email Sent
│   └── Reset Password
└── Google OAuth [Predicted]
    └── Authorization Confirm

Flowchart: (Mermaid)
...
```

---

## Figma Output Format

### Supported Output Types

| Output Type | Description |
|-------------|-------------|
| **Figma Structure** | Page organization, Frame naming, Layer conventions |
| **Auto Layout** | Spacing, alignment, resizing settings |
| **Components** | Component architecture, Variants, Properties |
| **Variables** | Design Tokens, Modes (theme switching) |
| **CSS** | CSS Variables, style specs |
| **iOS Swift** | SwiftUI / UIKit code |
| **Android Kotlin** | Jetpack Compose code |
| **JSON** | Figma API format, Token JSON |
| **Flow Diagram** | Predicted flowcharts |

### Figma Component Output Example

```
Button Component Spec:

Properties:
├── Size: Large (48px) | Medium (40px) | Small (32px)
├── Variant: Primary | Secondary | Outline | Ghost
├── State: Default | Hover | Focus | Active | Disabled
├── IconLeft: Boolean
└── IconRight: Boolean

Auto Layout:
├── Direction: Horizontal
├── Gap: 8px
├── Padding: 12px 16px
└── Alignment: Center

Variables:
├── bg-color: {semantic.interactive.primary}
├── text-color: {semantic.text.on-primary}
├── border-radius: {primitives.radius.md}
└── font: {typography.label.large}
```

---

## Design Process

```
Discover → Define → Design → Test → Deliver
            ↑
    Flow Prediction 🔮
```

### Phase 1: Discovery
1. Stakeholder interviews
2. User research
3. Competitive analysis
4. Technical constraints assessment

### Phase 2: Define
1. Persona creation
2. User journey maps
3. Information Architecture (IA)
4. Feature prioritization (MoSCoW)
5. **🔮 Spec gap analysis & prediction**

### Phase 3: Design
1. Low-fidelity Wireframes
2. High-fidelity Mockups (Figma)
3. Interactive Prototypes
4. Design System creation

### Phase 4: Test
1. Usability testing (5-user principle)
2. A/B testing
3. Heuristic evaluation
4. Iteration and refinement

### Phase 5: Handoff
1. Figma Dev Mode specs
2. Asset export (@1x, @2x, @3x)
3. Design Tokens export
4. Code specification docs

---

## Design Deliverables Checklist

### Flow Prediction Outputs
- [ ] Spec gap analysis report
- [ ] User Flow diagrams (Mermaid/Figma)
- [ ] Predicted screen list
- [ ] Items pending confirmation

### Figma Deliverables
- [ ] Component Library
- [ ] Design Tokens (Variables)
- [ ] Auto Layout specs
- [ ] Prototype interactions
- [ ] Dev Mode annotations

### App Deliverables
- [ ] Design mockups (@1x, @2x, @3x)
- [ ] Asset exports (PNG/SVG/PDF)
- [ ] Design specification docs
- [ ] Interactive prototype link
- [ ] Design Tokens documentation

### Web Deliverables
- [ ] Responsive designs (Mobile/Tablet/Desktop)
- [ ] Asset exports (SVG/WebP/PNG)
- [ ] CSS Variables / Design Tokens
- [ ] Component specification docs
- [ ] Interactive prototype link

---

## Quick Reference

### Platform Comparison

| Item | iOS | Android | Web |
|------|-----|---------|-----|
| Navigation | Tab Bar | Bottom Nav / Drawer | Navbar / Sidebar |
| Back | Top-left / Gesture | System back button | Browser back / Breadcrumb |
| Typography | SF Pro | Roboto | System / Custom |
| Icons | SF Symbols | Material Icons | Custom / Icon Library |
| Buttons | Rounded rectangle | FAB / Filled | Varied |
| Units | pt | dp/sp | px/rem/em |

### Common Dimensions

**iOS:**
- iPhone SE: 375 x 667 pt
- iPhone 14: 390 x 844 pt
- iPhone 14 Pro Max: 430 x 932 pt

**Android:**
- Compact: < 600 dp
- Medium: 600-839 dp
- Expanded: ≥ 840 dp

**Web Breakpoints:**
- Mobile: 320px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px - 1439px
- Large Desktop: ≥ 1440px

---

## Spec-Driven Batch UI Generation 📋

### Quick Start

Provide SRS or SDD spec documents, and I can auto-generate complete UI screen series:

```
Please read ./docs/SRS-MyProject-1.0.md
and generate complete UI screens

Output settings:
- Directory: ./generated-ui/MyProject/
- Format: HTML + React
- Style: Modern minimal, primary color #6366F1
```

### Supported Spec Documents

| Document Type | Extension | Extracted Content |
|---------------|-----------|-------------------|
| **SRS** | .md / .docx | Functional requirements, user stories, use cases |
| **SDD** | .md / .docx | Screen specs, navigation structure, data models |
| **PRD** | .md / .docx | Product vision, feature list, priorities |
| **FSD** | .md / .docx | Detailed functional specs, business rules |

### Output Directory Structure

```
📁 generated-ui/{ProjectName}/
├── 📄 README.md              # Generation report
├── 📄 SCREENS.md             # Screen specification list
├── 📁 html/                  # HTML + Tailwind
│   ├── auth/login.html
│   ├── auth/register.html
│   ├── home/home.html
│   └── ...
├── 📁 react/                 # React components
│   └── src/screens/...
├── 📁 swiftui/               # SwiftUI (optional)
└── 📁 compose/               # Compose (optional)
```

### Generation Flow

```
1. Parse spec documents → Extract functional requirements
2. Requirements analysis → Derive screen list
3. Scope confirmation → User confirmation
4. Batch generation → Generate screens by module
5. Output report → README + Screen list
```

---

## Auto UI Screen Generation 🖥️

### Quick Start

Tell me the page you want, and I can auto-generate complete executable UI code:

```
Please generate a login page with:
- Email/password inputs
- Google and Apple social login
- Forgot password link
- Register link

Style: Modern minimal, primary color #6366F1
Output format: React + Tailwind
```

### Supported Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **HTML + Tailwind** | Directly openable HTML files | Quick prototypes, Demos |
| **React** | Complete React components | Web frontend development |
| **Angular** | Complete Angular components (Standalone) | Web frontend development |
| **SwiftUI** | iOS/macOS native UI | iOS App development |
| **Jetpack Compose** | Android native UI | Android App development |
| **SVG** | Vector mockups | Import to design tools |
| **Figma JSON** | Figma structured data | Import to Figma |

### Supported Page Types

```
📱 Auth: Login, Register, Forgot Password, OTP Verification, Onboarding
🏠 Home: Dashboard, Feed, Explore, Search Results
📋 Lists: Product List, Article List, Card Grid, Message List
📄 Details: Product Detail, Article Detail, Profile, Settings
🛒 E-commerce: Cart, Checkout, Order Confirmation, Order History
📝 Forms: Data Edit, Multi-step Forms, Filters
💬 Social: Feed, Post Detail, Chat Room, Comments
⚙️ States: Empty State, Loading, Error Page, Success Page
```

### Style Integration

Combine with "Visual Style Extraction" to auto-apply styles from reference images:

```
1. Upload reference image first, extract style
2. When requesting UI generation, specify "apply extracted style"
3. Generated UI will automatically use extracted colors, fonts, border-radius, effects
```

---

## Reference Guide (17 Reference Documents)

### Specs & Generation
- 📋 [spec-driven-generation.md](references/spec-driven-generation.md) - SRS/SDD → Batch UI Generation
- ✅ [coverage-validation.md](references/coverage-validation.md) - 100% Coverage Validation
- 🖥️ [ui-generation.md](references/ui-generation.md) - Auto UI Screen Generation

### Visual & Assets
- 🎨 [style-extraction.md](references/style-extraction.md) - Visual Style Extraction
- 📦 [asset-extraction.md](references/asset-extraction.md) - Production-Ready Assets
- 🌙 [dark-mode.md](references/dark-mode.md) - Dark Mode Design

### Design Expertise
- 🎬 [motion-design.md](references/motion-design.md) - Motion Design
- ✍️ [ux-writing.md](references/ux-writing.md) - UX Writing
- 📊 [data-visualization.md](references/data-visualization.md) - Data Visualization
- 🌍 [localization.md](references/localization.md) - i18n/RTL Localization
- 🔍 [design-review.md](references/design-review.md) - Design Review

### Platform Guidelines
- 🍎 [ios-guidelines.md](references/ios-guidelines.md) - iOS HIG
- 🤖 [android-guidelines.md](references/android-guidelines.md) - Material Design 3
- 🌐 [web-guidelines.md](references/web-guidelines.md) - Web Responsive

### Systems & Workflows
- 🎨 [figma-guidelines.md](references/figma-guidelines.md) - Figma Output
- 🧱 [design-system.md](references/design-system.md) - Design System
- 🔮 [flow-prediction.md](references/flow-prediction.md) - Flow Prediction
- 🔬 [ux-research.md](references/ux-research.md) - User Research
- ♿ [accessibility.md](references/accessibility.md) - WCAG Accessibility
