---
name: medical-software-requirements-skill
description: |
  Medical Device Software IEC 62304 Documentation Tool
  醫療器材軟體 IEC 62304 開發文件工具

  【Trigger Keywords / 自動觸發關鍵字】
  SRS, SDD, SWD, STP, STC, SVV, RTM, IEC 62304, medical software, requirements specification,
  design specification, test plan, test case, traceability matrix, DOCX export, compliance check,
  Design Psychology, Cognitive Load, Progressive Disclosure, Fitts' Law, Hick's Law, UX Flow,
  Cognitive Psychology, Mental Model, Affordance, Error Prevention, Document Layout

  【Workflow Phases / 功能說明】
  Phase 1 - Requirements: Project vision, stakeholder analysis, functional/non-functional requirements
  Phase 2 - Documentation: SRS/SDD/SWD/STP/STC/SVV/RTM with UI/UX design integration
  Phase 3 - Asset Export: UI/UX tool collaboration, AI image generation, multi-size icon export
  Phase 4 - Psychology Analysis: Design + Cognitive psychology for optimal UX
  Phase 5 - Document Layout: Reading psychology optimization for SA/SD/PG/QA roles

  【Mandatory Rules / 強制規則】
  ⚠️ Traceability: 100% coverage required (SRS→SDD→SWD→STC)
  ⚠️ File Sync: .md and .docx must stay synchronized
  ⚠️ UI Images: SDD must embed UI design images (SVG preferred)
  ⚠️ Diagrams: Use Mermaid syntax only (no ASCII art)
  ⚠️ Headings: No manual numbering in MD (auto-generated in DOCX)
  ⚠️ Tech Stack: Reference platform-specific developer skills for SDD

  【Psychology Auto-Apply / 心理學自動套用】
  1. Design Psychology (references/design-psychology.md) - Cognitive Load, Progressive Disclosure, Fitts'/Hick's Law
  2. Cognitive Psychology (references/cognitive-psychology.md) - Mental Model, Working Memory, Gestalt, Affordance
  3. Document Layout Psychology (references/document-layout-psychology.md) - F-pattern, Visual Hierarchy, ID consistency

  【When to Apply / 執行時機】
  SRS/SDD: All 3 psychology guides | SWD: Cognitive + Layout | STP/STC: Layout only
---

# Medical Device Software Requirements & Documentation Skill

This skill provides comprehensive support for medical software development: from requirements gathering, IEC 62304 documentation, to design asset management.

---

## Quick Start Guide / 快速入門

### 1. Choose Your Task

| Task | Command Example | Output |
|------|-----------------|--------|
| **Create SRS** | "Help me create SRS for my medical device software" | SRS document |
| **Create SDD** | "Generate SDD with UI/UX design" | SDD with UI screens |
| **Create Test Cases** | "Generate STC test cases for SRS" | STC with traceability |
| **Generate RTM** | "Create traceability matrix" | RTM showing 100% coverage |
| **Export DOCX** | "Convert SRS.md to DOCX" | Professional Word document |
| **Check Compliance** | "Check IEC 62304 compliance" | Compliance report |

### 2. Document Types

| Document | Purpose | Safety Class |
|----------|---------|--------------|
| **SRS** | Define WHAT the software does | A, B, C |
| **SDD** | Define HOW to build it | B, C |
| **SWD** | Implementation details | C |
| **STP** | Testing strategy | B, C |
| **STC** | Specific test scenarios | B, C |
| **SVV** | Verification results | B, C |
| **RTM** | Track all relationships | A, B, C |

### 3. Essential Rules (6 Key Points)

| # | Rule | Why |
|---|------|-----|
| 1 | **100% Traceability** | Every SRS→SDD→SWD→STC must link |
| 2 | **MD + DOCX Sync** | Regenerate DOCX after MD changes |
| 3 | **Embed UI Images** | SDD must include screenshots (SVG preferred) |
| 4 | **Mermaid Only** | All diagrams use Mermaid, no ASCII art |
| 5 | **No Manual Numbering** | Write `## Title` not `## 1. Title` |
| 6 | **Reference Tech Skills** | Use platform skills for tech choices |

### 4. Quick Commands

```bash
# Install dependencies (first time)
cd ~/.claude/skills/medical-software-requirements-skill && npm install

# Convert MD to DOCX
node md-to-docx.js <input.md> <output.docx>

# Remove heading numbers from MD
bash remove-heading-numbers.sh <file.md>
```

### 5. ID Naming Convention

```
Format: [PREFIX]-[MODULE]-[NUMBER]

Examples:
  SRS-AUTH-001    → Authentication requirement #1
  SDD-CORE-002    → Core feature design #2
  STC-DATA-003    → Data management test #3
  SCR-HOME-001    → Home screen #1

Modules: AUTH, HOME, CORE, DATA, COMM, ALERT, REPORT, SETTING, NFR
```

---

## Psychology Auto-Apply Workflow

**When this skill is triggered, automatically read and apply:**

| Task Type | Design | Cognitive | Layout |
|-----------|:------:|:---------:|:------:|
| Create/Edit SRS | ✅ | ✅ | ✅ |
| Create/Edit SDD | ✅ | ✅ | ✅ |
| Create/Edit SWD | - | ✅ | ✅ |
| Create/Edit STP/STC | - | - | ✅ |
| Review Documents | ✅ | ✅ | ✅ |
| Generate DOCX | - | - | ✅ |

**Psychology Compliance Checklist:**
- Design: Cognitive Load, Progressive Disclosure, Prerequisites
- Cognitive: Mental Model, Working Memory (≤7 steps), Error Prevention
- Layout: Reader Role, ID Consistency, Trace Fields

---

## Traceability Requirements

| Direction | Coverage |
|-----------|----------|
| SRS → SDD | 100% |
| SRS → SWD | 100% |
| SRS → STC | 100% |
| SRS → UI (SCR) | 100% |
| SDD → SWD | 100% |
| SWD → STC | 100% |

**RTM must show 100% coverage in all directions.**

---

## Phase 1: Requirements Gathering

**Interview Questions:** See [references/interview-questions.md](references/interview-questions.md)

1. **Project Vision** - Clinical problem, target users, usage environment, regulatory requirements
2. **Stakeholder Analysis** - Clinical users, patients, administrators, regulatory, technical team
3. **Functional Requirements** - FURPS+ model with medical considerations
4. **Non-Functional Requirements** - See [references/medical-nfr-checklist.md](references/medical-nfr-checklist.md)
5. **Safety Classification** - Class A (no harm) / B (non-serious) / C (death/serious injury)

---

## Phase 2: Documentation

### Document Templates

| Document | Template | Bare Template |
|----------|----------|---------------|
| SRS | [srs-template/srs-template.md](srs-template/srs-template.md) | [srs-template-bare.md](srs-template/srs-template-bare.md) |
| SDD | [sdd-template/sdd-template.md](sdd-template/sdd-template.md) | [sdd-template-bare.md](sdd-template/sdd-template-bare.md) |
| SWD | [references/swd-template.md](references/swd-template.md) | - |
| STP | [references/stp-template.md](references/stp-template.md) | - |
| STC | [references/stc-template.md](references/stc-template.md) | - |
| SVV | [references/svv-template.md](references/svv-template.md) | - |
| RTM | [references/rtm-template.md](references/rtm-template.md) | - |

### Format Standards

- **Document Format:** See [references/document-format.md](references/document-format.md)
- **Mermaid Guidelines:** See [references/mermaid-guidelines.md](references/mermaid-guidelines.md)
- **Color Standards:** See [references/color-standards.md](references/color-standards.md)
- **SDD Screen Flow:** See [references/sdd-screen-flow.md](references/sdd-screen-flow.md)

---

## Phase 3: Design Asset Management

### Project Directory Structure

```
{project}/
├── 01-requirements/          # Phase 1 outputs
│   ├── SRS.md               # Software Requirements Spec
│   └── SRS.docx
├── 02-design/               # Phase 2 outputs
│   ├── SDD/
│   │   ├── SDD.md
│   │   ├── SDD.docx
│   │   └── images/          # UI screen images (SVG preferred)
│   └── SWD/
├── 03-assets/               # Phase 3 outputs
│   ├── app-icons/
│   ├── icons/
│   └── images/
├── 04-testing/              # Test documents
│   ├── STP.md
│   ├── STC.md
│   └── SVV.md
└── 05-traceability/         # RTM
    └── RTM.md
```

### Asset Guidelines

- **UI Image Embedding:** See [references/ui-image-embedding.md](references/ui-image-embedding.md)
- **App Icon Export:** See [references/app-icon-export.md](references/app-icon-export.md)
- **Asset Scripts:** See [references/asset-scripts.md](references/asset-scripts.md)
- **AI Prompt Templates:** See [references/ai-prompt-templates.md](references/ai-prompt-templates.md)

---

## Reference Files Index

### Psychology Guides
| File | Purpose |
|------|---------|
| [design-psychology.md](references/design-psychology.md) | Cognitive Load, Progressive Disclosure, Fitts'/Hick's Law |
| [cognitive-psychology.md](references/cognitive-psychology.md) | Mental Model, Working Memory, Gestalt, Affordance |
| [document-layout-psychology.md](references/document-layout-psychology.md) | F-pattern, Visual Hierarchy, Reader Roles |

### Document Standards
| File | Purpose |
|------|---------|
| [document-format.md](references/document-format.md) | Cover page, revision history, fonts |
| [mermaid-guidelines.md](references/mermaid-guidelines.md) | Diagram syntax, adaptive layout |
| [color-standards.md](references/color-standards.md) | Peter Coad UML, state machine colors |
| [sdd-screen-flow.md](references/sdd-screen-flow.md) | Module order, navigation flow |

### Templates
| File | Purpose |
|------|---------|
| [srs-template.md](references/srs-template.md) | SRS document structure |
| [sdd-template.md](references/sdd-template.md) | SDD with UI/UX sections |
| [swd-template.md](references/swd-template.md) | Detailed design template |
| [stp-template.md](references/stp-template.md) | Test plan template |
| [stc-template.md](references/stc-template.md) | Test cases template |
| [svv-template.md](references/svv-template.md) | Verification report template |
| [rtm-template.md](references/rtm-template.md) | Traceability matrix template |

### Assets & Tools
| File | Purpose |
|------|---------|
| [interview-questions.md](references/interview-questions.md) | Requirements interview questions |
| [medical-nfr-checklist.md](references/medical-nfr-checklist.md) | Non-functional requirements checklist |
| [screen-requirement-mapping.md](references/screen-requirement-mapping.md) | SCR to SRS mapping |
| [ui-image-embedding.md](references/ui-image-embedding.md) | Embedding UI images in SDD |
| [asset-specifications.md](references/asset-specifications.md) | Icon/image specifications |
| [ai-prompt-templates.md](references/ai-prompt-templates.md) | AI image generation prompts |

### Tech Stack References
When writing SDD Technology Stack section, reference platform-specific skills:
- Android → android-developer-skill
- iOS → ios-developer-skill
- Python Backend → python-developer-skill
- Node.js Backend → nodejs-developer-skill
- Angular Frontend → angular-developer-skill
- React Frontend → react-developer-skill
- Windows Desktop → windows-developer-skill
- Spring Boot → springboot-developer-skill
