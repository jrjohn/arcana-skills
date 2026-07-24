---
name: app-requirements-skill
description: |
  IEC 62304 Software Development Documentation Tool. All App development follows IEC 62304 standard process to produce complete documentation suite.
  This Skill should be activated when the user mentions any of the following keywords:

  [General App Development Triggers] Generate an App, Develop App, Create App, Build App, Design App,
  Develop an App, I want to develop, Help me develop, Development requirements, App requirements,
  iOS App, Android App, Cross-platform App, Mobile application,
  Requirements specification, Design specification, Software specification, UI Flow, Interactive prototype, User flow,
  Learning App, Education App, E-commerce App, Social App, Tool App,
  SRS Software Requirements Specification, SDD Software Design Specification.

  [IEC 62304 Document Triggers] SRS, SDD, SWD, STP, STC, SVV, RTM, IEC 62304,
  check compliance, compliance check, traceability matrix, software requirements, software design,
  test plan, test cases, DOCX output, document generation, requirements gathering, requirements analysis, architecture design, detailed design.

  [Design-related Triggers] UI/UX design, SCR screen, Design Psychology,
  Cognitive Load, Progressive Disclosure,
  Fitts' Law, Hick's Law, Dashboard, User flow, UX Flow, feedback, feedback to docs.

  [App Type Auto-detection] (All types follow IEC 62304 process)
  Detect keywords to automatically load corresponding requirements module:
  • Learning/Education/Vocabulary/Quiz/Course → education-requirements.md
  • Shopping/E-commerce/Product/Cart → ecommerce-requirements.md
  • Social/Friends/Posts/Chat → social-requirements.md
  • Medical/Health/Patient/Prescription → healthcare-requirements.md
  • Notes/Todo/Productivity → productivity-requirements.md
  • Others → standard-app-requirements.md
---

# App Requirements Gathering & Documentation Skill (IEC 62304)

This Skill provides comprehensive App development support: from requirements gathering, IEC 62304 document generation, to design asset management.
Supports various App types: Education/Learning, E-commerce, Social, Productivity Tools, Healthcare, etc.

---

## 🚀 Optimized Workflow (11 Steps)

```
═══════════════════════════════════════════════════════════════════
Phase 0: Requirements Interview Phase ⚠️ Mandatory First Step
═══════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│ Step 0: Requirements Interview (MANDATORY FIRST STEP)           │
│ ─────────────────────────────────────────────────────────────── │
│ • ⚠️ Must be completed before writing any documents             │
│ • Use AskUserQuestion tool for interactive interview            │
│ • Confirm: Target platform, Account architecture, Tech stack,   │
│   Core feature priorities                                       │
│ • Reference: references/interview-questions.md                  │
│ • Output: Interview summary (internal record for SRS writing)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ⚠️ Blocking Point: Interview must complete
                              ↓
═══════════════════════════════════════════════════════════════════
Phase 1: Requirements Phase
═══════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Write SRS Software Requirements Specification           │
│ ─────────────────────────────────────────────────────────────── │
│ • Write based on Step 0 interview results                       │
│ • UI requirements gathering (platform/device/module/visual)     │
│ • Functional/Non-functional requirements gathering              │
│ • Output: SRS-{Project}-1.0.md                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
═══════════════════════════════════════════════════════════════════
Phase 2: Design Phase (SDD + Smart Prediction Integrated) ⚠️ Key
═══════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Write SDD Software Design Specification                 │
│ ─────────────────────────────────────────────────────────────── │
│ • System architecture design, Data model design                 │
│ • Basic screen SCR-* design (with Button Navigation)            │
│ • Output: SDD-{Project}-1.0.md (initial version)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Add Settings Sub-page Design                            │
│ ─────────────────────────────────────────────────────────────── │
│ • Settings main page (SCR-SETTING-001-main)                     │
│ • Settings sub-pages (Account, Notifications, Privacy,          │
│   Language, Theme, About, etc.)                                 │
│ • Each sub-page must include complete Button Navigation         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Execute Smart Prediction to Find Missing Screens 🤖     │
│ ─────────────────────────────────────────────────────────────── │
│ • ⚠️ Keyword-triggered prediction (see keyword-trigger-         │
│   prediction.md)                                                │
│   - Scan original requirements for keywords (engagement→ENGAGE, │
│     public→SOCIAL, etc.)                                        │
│   - Auto-predict missing complete modules                       │
│ • Analyze Button Navigation to find navigation gaps             │
│ • Identify missing detail pages, edit pages, confirmation pages │
│ • Identify shared state screens (loading/empty/error/no-network)│
│ • Output: 04-ui-flow/workspace/screen-prediction.json           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Add Predicted Screen Designs                            │
│ ─────────────────────────────────────────────────────────────── │
│ • Add predicted screens to SDD                                  │
│ • Ensure Button Navigation is 100% complete                     │
│ • Update SDD.md                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: List Screen Inventory                                   │
│ ─────────────────────────────────────────────────────────────── │
│ • Update Appendix A complete screen list                        │
│ • Verify all navigation targets have corresponding screens      │
│ • Confirm total screen count is correct                         │
│ • Output: SDD-{Project}-1.0.md (complete version)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ⚠️ Blocking Point: Must complete to continue
                              ↓
═══════════════════════════════════════════════════════════════════
Phase 3: UI Flow Phase ⚠️ Always use app-uiux-designer.skill
═══════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: UI Flow Framework Initialization                        │
│ ─────────────────────────────────────────────────────────────── │
│ • Create 04-ui-flow/ directory structure                        │
│ • Copy templates, set project variables                         │
│ • Create workspace/current-process.json                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Generate Complete UI Flow HTML Screens                  │
│         (Always use app-uiux-designer.skill)                    │
│ ─────────────────────────────────────────────────────────────── │
│ • Generate all screens based on SDD Button Navigation           │
│ • Generate iPad version (04-ui-flow/ipad/*.html)                │
│ • Generate iPhone version (04-ui-flow/iphone/*.html)            │
│ • 100% screen coverage + navigation validation                  │
│ • Generate screenshots (screenshots/ipad/*.png,                 │
│   screenshots/iphone/*.png)                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Backfill SDD (Always use app-uiux-designer.skill)       │
│ ─────────────────────────────────────────────────────────────── │
│ • Add UI prototype references to each SCR-* section             │
│ • Embed images/ipad/*.png                                       │
│ • Embed images/iphone/*.png                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
═══════════════════════════════════════════════════════════════════
Phase 4: Document Completion Phase (One-time Generation)
═══════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│ Step 10: Generate DOCX Format Documents (Final)                 │
│ ─────────────────────────────────────────────────────────────── │
│ • node md-to-docx.js SRS-*.md → SRS.docx                        │
│ • node md-to-docx.js SDD-*.md → SDD.docx                        │
│ • Generate once, avoid repetition                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        ✅ Document Generation Complete
```

---

## ⚠️ Key Improvements

| Item | Old Process | New Process |
|------|-------------|-------------|
| **Requirements Interview** | **Missing or assumed** | **Step 0 Mandatory First Step (BLOCKING)** |
| Settings Sub-pages | Missing or added later | **Step 3 Dedicated step** |
| Smart Prediction Timing | Predict after SDD writing | **Step 4 Execute immediately** |
| Sub-page Addition | Manual discovery, added later | **Step 5 Auto-predict, one-time completion** |
| Screen List Confirmation | Mid-process | **Step 6 Confirm before UI Flow** |
| UI Flow Generation | Scattered processing | **Step 8 Always use app-uiux-designer.skill** |
| DOCX Generation | Multiple generations | **Step 10 Generate once at the end** |

---

## Mandatory Rules

⚠️ **Phase 0 Rules (BLOCKING - Highest Priority) - Step 0**
```
⚠️ Requirements interview must be completed before writing any documents
```
**Mandatory Actions:**
- [ ] **Do NOT write SRS directly**: After user requests App development, must use AskUserQuestion tool for requirements interview first
- [ ] **Interview Scope**: Target platform, Account architecture, Tech stack, Core features, Priority, Special requirements
- [ ] **Interview Tool**: Use AskUserQuestion tool, provide 2-4 options for user selection
- [ ] **Interview Reference**: See `references/interview-questions.md`
- [ ] **Interview Record**: Internal record of interview results, used as basis for SRS writing

**Interview Question Examples (Using AskUserQuestion):**
```
1. Target Platform: iPhone + iPad / iPad only / Full Apple ecosystem
2. Account Architecture: Family group / Independent accounts + linking / Single account role switching
3. AI Service: Claude API / OpenAI API / Either
4. Voice Technology: iOS native / Cloud service / Hybrid mode
5. Core Feature Priority: Which features are MVP essentials?
```

**Violation Consequences:**
- Skipping Step 0 and writing SRS directly may lead to mismatched requirements, rework, user dissatisfaction
- AI should proactively remind users that requirements interview is needed first

---

⚠️ **Phase 2 Rules (Critical) - Step 2~6**
```
Write SDD → Add Settings Sub-pages → Smart Prediction → Add Predicted Screens → List Screen Inventory
```
- Step 3 must add complete settings sub-page designs
- Step 4 must execute smart prediction to find all missing screens
- Step 6 Appendix A must include all screens before entering Phase 3

⚠️ **Phase 2 Validation (BLOCKING - Must pass before Step 6 completion)**
```bash
# SDD Screen Consistency Validation
SDD_FILE="02-design/SDD-*.md"

# 1. Count Appendix A total screens
APPENDIX_COUNT=$(grep -E "^\| .* \| [0-9]+ \| SCR-" $SDD_FILE | awk -F'|' '{sum+=$3} END {print sum}')

# 2. Count SDD body SCR-* section count
BODY_COUNT=$(grep -c "^#### SCR-" $SDD_FILE)

# 3. Validate consistency
if [ "$APPENDIX_COUNT" != "$BODY_COUNT" ]; then
  echo "❌ SDD screen inconsistency: Appendix A=$APPENDIX_COUNT, Body=$BODY_COUNT"
  echo "Please add the missing $(($APPENDIX_COUNT - $BODY_COUNT)) screen definitions"
  exit 1
fi
echo "✅ SDD screens consistent: $BODY_COUNT screens"
```
**Validation Items:**
- [ ] Appendix A total screen count = SDD body `#### SCR-*` section count
- [ ] Each SCR-* section has Button Navigation table
- [ ] Screen ID naming is consistent (module-number-name)

⚠️ **Required Module Validation (BLOCKING - Must pass after Step 4 completion)**
```bash
#!/bin/bash
# === Required Module Validation ===
REQUIRED_MODULES=("AUTH" "PROFILE" "SETTING" "COMMON")
SDD_FILE="02-design/SDD-*.md"

echo "🔍 Validating required modules..."

ERRORS=0
for MODULE in "${REQUIRED_MODULES[@]}"; do
  COUNT=$(grep -c "^#### SCR-${MODULE}-" $SDD_FILE 2>/dev/null || echo "0")
  if [ "$COUNT" -eq 0 ]; then
    echo "❌ Missing required module: $MODULE"
    ERRORS=$((ERRORS+1))
  else
    echo "✅ $MODULE: $COUNT screens"
  fi
done

# COMMON state screens special validation
echo ""
echo "🔍 Validating COMMON state screens..."
COMMON_STATES=("loading" "empty" "error" "no-network")
for STATE in "${COMMON_STATES[@]}"; do
  if grep -q "SCR-COMMON-.*-${STATE}" $SDD_FILE 2>/dev/null; then
    echo "✅ COMMON state: $STATE"
  else
    echo "❌ Missing COMMON state: $STATE"
    ERRORS=$((ERRORS+1))
  fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ Required module validation passed"
else
  echo "❌ Required module validation failed ($ERRORS errors)"
  echo "⚠️ Please refer to references/common-modules/ templates to add missing modules"
  exit 1
fi
```
**Required Module Minimum Requirements:**
- [ ] AUTH: login, register, forgot (3 screens)
- [ ] PROFILE: view, edit (2 screens)
- [ ] SETTING: main, account, privacy, about (4 screens)
- [ ] COMMON: loading, empty, error, no-network (4 screens)

⚠️ **Phase 3 Rules (Critical) - Step 7~9**
```
⚠️ UI Flow + SDD Backfill always use app-uiux-designer.skill
```
- Step 7 Framework Initialization: Create directory structure and state tracking
- Step 8 Generate HTML: 100% screen coverage + navigation validation + screenshot generation
- Step 9 Backfill SDD: Embed UI screenshots into SCR-* sections (executed by app-uiux-designer.skill)

⚠️ **Phase 4 Rules (Critical) - Step 10**
```
Generate DOCX (once)
```
- Step 10 Generate DOCX: SRS.docx + SDD.docx one-time generation

⚠️ **Button Navigation Mandatory**
- Each SDD SCR-* section must include Button Navigation table
- Target Screen field will be used directly for UI Flow generation
- See: `references/button-navigation-specification.md`

⚠️ **Markdown Format Rules (DOCX Conversion Compatible)**
- **Code Block (```) only for code**: SQL, JSON, Swift, Kotlin, etc.
- **Use Cases MUST NOT use Code Block**, use structured text instead:
  ```markdown
  # ❌ Wrong: Use Case in code block
  #### UC-001: User Login
  ```
  Preconditions: ...
  Main flow: 1. ... 2. ...
  ```

  # ✅ Correct: Use Case with bold labels + numbered list
  #### UC-001: User Login
  **Preconditions:** User has installed the App
  **Main Flow:**
  1. User opens the App
  2. System displays login screen
  **Postconditions:** User completes login
  ```
- **Mermaid Diagrams**: Must be marked as ```mermaid, otherwise treated as code block
- **Mermaid Direction**: Must use `flowchart TB` (vertical), `flowchart LR` (horizontal) is forbidden (text becomes too small)
- **Mermaid Multi-layer Architecture**: Use hybrid mode `flowchart TB` + `direction LR`, making diagram wider but shorter
- **ASCII Art**: Avoid, use Mermaid or images instead

⚠️ **SDD Use Case Completeness Validation (BLOCKING - Must pass before Step 2 completion)**

```bash
#!/bin/bash
# Use Case Completeness Validation
SDD_FILE="02-design/SDD-*.md"

echo "🔍 Validating use case completeness..."

# 1. Count UC in overview table
TABLE_COUNT=$(grep -E "^\| UC-" $SDD_FILE | wc -l | tr -d ' ')

# 2. Count detailed UC descriptions (#### UC-* format)
DETAIL_COUNT=$(grep -c "^#### UC-" $SDD_FILE)

echo ""
echo "📊 Statistics:"
echo "   Overview table UC count: $TABLE_COUNT"
echo "   Detailed description UC count: $DETAIL_COUNT"

# 3. Find UCs missing detailed descriptions
echo ""
if [ "$TABLE_COUNT" != "$DETAIL_COUNT" ]; then
  echo "❌ Validation failed: $(($TABLE_COUNT - $DETAIL_COUNT)) use cases missing detailed descriptions"
  echo ""
  echo "Use cases missing detailed descriptions:"
  grep -E "^\| UC-" $SDD_FILE | awk -F'|' '{print $2}' | tr -d ' ' | while read uc; do
    if ! grep -q "^#### $uc:" $SDD_FILE; then
      echo "  - $uc"
    fi
  done
  exit 1
fi

echo "✅ Validation passed: All $TABLE_COUNT use cases have detailed descriptions"
```

**Validation Items:**
- [ ] Each `UC-*` in overview table has corresponding `#### UC-*:` detailed section
- [ ] Each detailed section contains: Preconditions, Main flow, Postconditions

⚠️ **ASCII Art Prohibition Validation (BLOCKING - Must pass before document generation)**

```bash
#!/bin/bash
# ASCII Art Detection Validation
echo "🔍 Validating for prohibited ASCII Art..."

ERRORS=0

# Check code blocks in SRS and SDD
for FILE in 01-requirements/SRS-*.md 02-design/SDD-*.md; do
  if [ -f "$FILE" ]; then
    # Find non-mermaid code blocks containing ASCII drawing characters
    ASCII_BLOCKS=$(awk '/^```[^m]|^```$/{flag=1; next} /^```/{flag=0} flag && /[┌┐└┘│─├┤┬┴┼→←↑↓▶◀■□●○]/' "$FILE" | wc -l | tr -d ' ')
    if [ "$ASCII_BLOCKS" -gt 0 ]; then
      echo "❌ $FILE contains ASCII Art ($ASCII_BLOCKS lines)"
      ERRORS=$((ERRORS+1))
    fi
  fi
done

if [ $ERRORS -eq 0 ]; then
  echo "✅ No ASCII Art violations"
else
  echo ""
  echo "⚠️ Please convert ASCII Art to Mermaid diagram format"
  exit 1
fi
```

---

## ⚠️ Segmented Writing Rules (Critical - Prevent Token Overflow)

Due to AI output token limits (~32000 tokens), SRS/SDD documents **must be written in segments**.

### Mandatory Segmentation Strategy

| Document | Segmentation Method | Max Lines Per Segment |
|----------|---------------------|----------------------|
| SRS | By chapter | ≤ 500 lines/segment |
| SDD | By module | ≤ 400 lines/segment |

### SRS Segmentation Order (Step 1)

```
1️⃣ First Write: Document info + Product overview + Functional requirements overview
2️⃣ Second Edit: Append 3.2 Detailed requirements (AUTH + PROFILE)
3️⃣ Third Edit: Append detailed requirements (VOCAB + SENTENCE)
4️⃣ Fourth Edit: Append detailed requirements (TRAIN + PROGRESS)
5️⃣ Fifth Edit: Append detailed requirements (PARENT + ENGAGE + UX)
6️⃣ Sixth Edit: Append non-functional requirements + interface requirements
7️⃣ Seventh Edit: Append software safety classification + appendix
```

### SDD Segmentation Order (Step 2)

```
1️⃣ First Write: Document info + Use case design + System architecture
2️⃣ Second Edit: Append module design (AUTH module + screens)
3️⃣ Third Edit: Append module design (VOCAB module + screens)
4️⃣ Fourth Edit: Append module design (TRAIN module + screens)
5️⃣ Fifth Edit: Append module design (PROGRESS + PARENT modules)
6️⃣ Sixth Edit: Append module design (SETTING module + screens)
7️⃣ Seventh Edit: Append data design + interface design
8️⃣ Eighth Edit: Append shared design elements + security design + appendix
```

### Segmented Writing Example

```markdown
# ❌ Wrong: Output entire document at once
Write entire SRS document (5000+ lines) → Token overflow error

# ✅ Correct: Write in segments
Step 1: Write(SRS-xxx.md, Document info + Product overview, ~300 lines)
Step 2: Edit(SRS-xxx.md, append AUTH requirements, ~200 lines)
Step 3: Edit(SRS-xxx.md, append VOCAB requirements, ~200 lines)
...
```

### Content Limits Per Output

| Content Type | Max Lines | Description |
|--------------|-----------|-------------|
| Single module requirements | 200 lines | Including acceptance criteria |
| Single module design | 300 lines | Including all SCR screens |
| Single SCR screen | 80 lines | Including Button Navigation |
| Data model | 150 lines | Including entity definitions |

### Segmented Progress Tracking

After completing each segment, output progress summary:

```markdown
✅ SRS Writing Progress: 3/7 completed
   - [x] Document info + Product overview
   - [x] AUTH + PROFILE requirements
   - [x] VOCAB + SENTENCE requirements
   - [ ] TRAIN + PROGRESS requirements
   - [ ] PARENT + ENGAGE + UX requirements
   - [ ] Non-functional requirements + Interface requirements
   - [ ] Software safety classification + Appendix
```

---

## Quick Reference

### ID Numbering System

| Document Type | ID Format | Example |
|---------------|-----------|---------|
| SRS Requirement | REQ-{MODULE}-{NNN} | REQ-AUTH-001 |
| SDD Design | SDD-{MODULE}-{NNN} | SDD-AUTH-001 |
| SDD Screen | SCR-{MODULE}-{NNN}-{desc} | SCR-AUTH-001-login |
| SWD Component | SWD-{MODULE}-{NNN} | SWD-AUTH-001 |
| STC Test | STC-{REQ-ID} | STC-REQ-AUTH-001 |

### Module Codes

| Code | Module | Code | Module |
|------|--------|------|--------|
| AUTH | Authentication | DASH | Dashboard |
| VOCAB | Vocabulary | TRAIN | Training |
| REPORT | Report | SETTING | Settings |
| DEVICE | Device | COM | Shared Components |
| EDU | Education/Learning | ECOM | E-commerce |
| SOCIAL | Social | PROD | Productivity |
| HEALTH | Healthcare | SYNC | Sync |
| COMMON | Common States | PARENT | Parental Control |

---

## MD to DOCX Command

```bash
# Install dependencies (first time)
cd ~/.claude/skills/app-requirements-skill
npm install docx

# Convert documents (Execute at Phase 4 end)
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-*.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-*.md
```

---

## Smart Prediction (Phase 2 Core)

### Smart Prediction Sources (Priority Order)

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | **common-modules/** | **Required modules** (AUTH, PROFILE, SETTING, COMMON) |
| **2** | **🚨 Keyword-triggered Prediction** | **Scan requirement keywords, predict complete modules (ENGAGE, SOCIAL, etc.)** |
| 3 | App Type Requirements | education/ecommerce/social/healthcare/productivity |
| 4 | Button Navigation Analysis | Navigation gap analysis |
| 5 | Naming Convention Inference | Detail pages, Edit pages, Confirmation pages |

> 📁 **Required Module Template Location:** `references/common-modules/`
> - `common-modules-index.md` - Common module index
> - `auth-module-template.md` - AUTH module template (8 screens)
> - `profile-module-template.md` - PROFILE module template (3 screens)
> - `setting-module-template.md` - SETTING module template (18 screens)
> - `common-states-template.md` - COMMON states template (5 screens)

> 🚨 **Keyword-triggered Prediction:** `references/keyword-trigger-prediction.md`
> - Engagement/Gamification → ENGAGE module (6 screens)
> - Public/Share/Social → SOCIAL module (4 screens)
> - Merge/Group/Export → VOCAB extension (8 screens)
> - Report/Weekly/Calendar → PROGRESS extension (6 screens)

### Prediction Items

| Category | Prediction Content |
|----------|-------------------|
| **Required Modules** | AUTH (login/register/forgot), PROFILE (view/edit), SETTING (main/account/privacy/about), COMMON (loading/empty/error/no-network) |
| **🚨 Keyword-triggered** | ENGAGE (badges/rewards/pet), SOCIAL (share/public), VOCAB/PROGRESS/TRAIN extensions |
| Navigation Gaps | Screens where Button Navigation Target Screen doesn't exist |
| Sub-pages | Settings sub-pages, Detail pages, Edit pages |
| Flow Pages | Confirmation dialogs, Success/Failure result pages |

### Prediction Output

```json
{
  "prediction_date": "2026-01-15",
  "analysis": {
    "existing_screens": 38,
    "predicted_screens": 15,
    "total_screens": 53
  },
  "predicted_missing": [
    {
      "id": "SCR-COMMON-001-loading",
      "module": "COMMON",
      "name": "Loading State",
      "reason": "Required for all Apps",
      "priority": "P0"
    }
  ],
  "navigation_gaps": [
    {
      "source": "SCR-SETTING-001-main",
      "button": "cell_password",
      "missing_target": "SCR-SETTING-002-password"
    }
  ]
}
```

---

## SDD SCR Section Template (with Button Navigation)

```markdown
##### SCR-AUTH-001-login: Login Screen

| Attribute | Content |
|-----------|---------|
| **Screen ID** | SCR-AUTH-001-login |
| **Screen Name** | Login Screen |
| **Related Requirements** | REQ-AUTH-001, REQ-AUTH-002 |

**Functional Description**:
User login screen, supports Email/password login and social login.

**UI Component Specifications**:

| Component ID | Component Type | Specification | Related Requirement |
|--------------|----------------|---------------|---------------------|
| txt_email | TextField | Email input field | REQ-AUTH-001 |
| txt_password | SecureField | Password input field | REQ-AUTH-001 |
| btn_login | Button | Login button | REQ-AUTH-001 |

**Button Navigation**:

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | Login | Button | SCR-AUTH-004-role | Validation success |
| btn_apple | Apple | Button | SCR-AUTH-004-role | Apple login success |
| lnk_forgot | Forgot Password? | Link | SCR-AUTH-003-forgot | - |
| lnk_register | Register Now | Link | SCR-AUTH-002-register | - |

##### UI Prototype Reference

> ⚠️ **Format Specification:** Do not use tables, embed images directly, do not retain HTML links.

**iPad Version:**

![](images/ipad/SCR-AUTH-001-login.png)

**iPhone Version:**

![](images/iphone/SCR-AUTH-001-login.png)
```

---

## IEC 62304 Bidirectional Traceability

> ⚠️ **Mandatory Requirement**: SRS and SDD must establish bidirectional traceability to comply with IEC 62304

### SRS → SDD Traceability

Each SRS requirement must include `| **SDD Traceability** | SCR-xxx |` field:

```markdown
##### REQ-AUTH-001: Email/Password Login

| Attribute | Content |
|-----------|---------|
| **ID** | REQ-AUTH-001 |
| **Description** | System shall allow users to authenticate via Email and password |
| **Priority** | P0 |
| **Related Requirements** | REQ-AUTH-005, REQ-AUTH-006 |
| **SDD Traceability** | SCR-AUTH-001-login, SCR-AUTH-002-register |
```

### SDD → SRS Traceability

Each SDD screen must include `| **Related Requirements** | REQ-xxx |` field:

```markdown
##### SCR-AUTH-001-login: Login Screen

| Attribute | Content |
|-----------|---------|
| **Screen ID** | SCR-AUTH-001-login |
| **Screen Name** | Login Screen |
| **Related Requirements** | REQ-AUTH-001, REQ-AUTH-002 |
```

### Traceability Validation Script

```bash
#!/bin/bash
# IEC 62304 Bidirectional Traceability Validation
SRS_FILE="01-requirements/SRS-*.md"
SDD_FILE="02-design/SDD-*.md"

echo "🔍 Validating bidirectional traceability..."

# 1. SRS → SDD: Each REQ has SDD traceability
SRS_REQ_COUNT=$(grep -c "^##### REQ-" $SRS_FILE)
SRS_SDD_TRACK=$(grep -c "SDD Traceability" $SRS_FILE)
echo "SRS: $SRS_REQ_COUNT requirements, $SRS_SDD_TRACK have SDD traceability"

# 2. SDD → SRS: Each SCR has related requirements
SDD_SCR_COUNT=$(grep -c "^##### SCR-" $SDD_FILE)
SDD_REQ_TRACK=$(grep -c "Related Requirements" $SDD_FILE)
echo "SDD: $SDD_SCR_COUNT screens, $SDD_REQ_TRACK have related requirements"

# 3. Validate consistency
[ "$SRS_REQ_COUNT" == "$SRS_SDD_TRACK" ] && echo "✅ SRS traceability complete" || echo "❌ SRS traceability incomplete"
[ "$SDD_SCR_COUNT" -le "$SDD_REQ_TRACK" ] && echo "✅ SDD traceability complete" || echo "❌ SDD traceability incomplete"
```

---

## Project Directory Structure

```
📁 {project-name}/
├── 📁 01-requirements/     # SRS
├── 📁 02-design/           # SDD + images/
├── 📁 03-assets/           # App Icon, Icons, Images
├── 📁 04-ui-flow/          # HTML UI Flow
│   ├── 📁 workspace/       # State tracking
│   ├── 📁 ipad/            # iPad HTML
│   └── 📁 iphone/          # iPhone HTML
├── 📁 05-development/      # SWD
├── 📁 06-testing/          # STP, STC
├── 📁 07-verification/     # SVV
└── 📁 08-traceability/     # RTM
```

---

## Skill Integration & Step Mapping

| Step | Step Name | Leading Skill | Blocking |
|------|-----------|---------------|----------|
| **0** | **Requirements Interview (MANDATORY FIRST)** | **app-requirements-skill** | **⚠️ BLOCKING** |
| 1 | Write SRS Software Requirements Specification | app-requirements-skill | |
| 2 | Write SDD Software Design Specification | app-requirements-skill | |
| 3 | Add Settings Sub-page Design | app-requirements-skill | |
| 4 | Execute Smart Prediction for Missing Screens | app-requirements-skill | |
| 5 | Add Predicted Screen Designs | app-requirements-skill | |
| 6 | List Screen Inventory | app-requirements-skill | ⚠️ BLOCKING |
| 7 | UI Flow Framework Initialization | **app-uiux-designer.skill** | |
| 8 | Generate Complete UI Flow HTML Screens | **app-uiux-designer.skill** | |
| 9 | Backfill SDD | **app-uiux-designer.skill** | |
| 10 | Generate DOCX Format Documents | app-requirements-skill | |

⚠️ **Important: Step 0 requirements interview must be completed first**
⚠️ **Important: Steps 7~9 always use app-uiux-designer.skill**

---

## References Directory

### Common Module Templates (Smart Prediction Priority Load)
- `common-modules/common-modules-index.md` - **Common module index & validation scripts**
- `common-modules/auth-module-template.md` - AUTH module template (8 screens)
- `common-modules/profile-module-template.md` - PROFILE module template (3 screens)
- `common-modules/setting-module-template.md` - SETTING module template (18 screens)
- `common-modules/common-states-template.md` - COMMON states template (5 screens)

### 🚨 Keyword-triggered Prediction (New)
- `keyword-trigger-prediction.md` - **Keyword-triggered module prediction rules**
  - ENGAGE module triggers: engagement, gamification, badges, rewards, pet, leaderboard
  - SOCIAL module triggers: public, share, social, invite
  - Module extension triggers: merge, group, export, weekly report, calendar

### Workflow & Standards
- `workflow-details.md` - Complete workflow detailed description
- `iec62304-document-standards.md` - **IEC 62304 unified document standards** (applies to all documents)
- `sdd-standards.md` - SDD-specific supplementary specifications
- `button-navigation-specification.md` - Button Navigation specification

### Psychology Guidelines
- `design-psychology.md` - Design psychology principles
- `cognitive-psychology.md` - Cognitive psychology principles

### IEC 62304 Document Templates
- `srs-template.md` - SRS template
- `sdd-template.md` - SDD template
- `swd-template.md` - SWD template
- `stp-template.md` - STP template
- `stc-template.md` - STC template
- `svv-template.md` - SVV template
- `rtm-template.md` - RTM template

### App Type Requirements
- `education-requirements.md` - Education/Learning App requirements
- `ecommerce-requirements.md` - E-commerce App requirements
- `social-requirements.md` - Social App requirements
- `productivity-requirements.md` - Productivity Tool App requirements
- `healthcare-requirements.md` - Healthcare App requirements
- `standard-app-requirements.md` - Standard App functional requirements list

---

## Traceability Completeness Requirements (100%)

| Traceability Direction | Description | Requirement |
|------------------------|-------------|-------------|
| SRS → SDD | Each requirement has corresponding design | 100% |
| SDD → SWD | Each design has detailed implementation | 100% |
| SWD → STC | Each component has test cases | 100% |
| SRS → SCR | Each requirement has corresponding screen | 100% |

---

## Validation Tools

```bash
# Traceability validation
node ~/.claude/skills/app-requirements-skill/scripts/verify-traceability.js [project-dir]

# Compliance check
node ~/.claude/skills/app-requirements-skill/scripts/compliance-checker.js [project-dir]
```

---

## Backfill Report Template (Phase 4)

```markdown
## Backfill Completion Report

### SDD Backfill
| Item | Count | Status |
|------|-------|--------|
| SCR Screen Updates | 53 | ✅ Complete |
| Image Embeddings | 106 | ✅ Complete |

### SRS Backfill
| Item | Count | Status |
|------|-------|--------|
| Screen References | 53 | ✅ Complete |
| Inferred Requirements | 15 | ✅ Complete |
| User Flows Updates | 6 | ✅ Complete |

### DOCX Generation (One-time)
| Item | Status |
|------|--------|
| SRS.docx | ✅ Complete |
| SDD.docx | ✅ Complete |
```
