# Workflow Details

This document contains the detailed workflow description for app-requirements-skill.

## 🧠 Psychology Auto-Application Flow

### Step 1: Read Psychology Guidelines

Before executing any document operation, the following files must be read first:

```bash
# 1. Design Psychology
cat ~/.claude/skills/app-requirements-skill/references/design-psychology.md

# 2. Cognitive Psychology
cat ~/.claude/skills/app-requirements-skill/references/cognitive-psychology.md

# 3. Document Layout Psychology
cat ~/.claude/skills/app-requirements-skill/references/document-layout-psychology.md
```

### Step 2: Apply Psychology Based on Task Type

| Task Type | Design Psychology | Cognitive Psychology | Document Layout Psychology |
|-----------|:-----------------:|:--------------------:|:--------------------------:|
| Create/Modify SRS | ✅ | ✅ | ✅ |
| Create/Modify SDD | ✅ | ✅ | ✅ |
| Create/Modify SWD | - | ✅ | ✅ |
| Create/Modify STP/STC | - | - | ✅ |
| Review/Audit Documents | ✅ | ✅ | ✅ |
| Generate DOCX | - | - | ✅ |

### Step 3: Output Psychology Compliance Report

```markdown
## Psychology Compliance Review

### Design Psychology ✅/⚠️/❌
- Cognitive Load: [Assessment]
- Progressive Disclosure: [Assessment]
- Fitts' Law: [Assessment]

### Cognitive Psychology ✅/⚠️/❌
- Mental Model: [Assessment]
- Working Memory: [Assessment]
- Error Prevention: [Assessment]

### Document Layout Psychology ✅/⚠️/❌
- Reader Role Analysis: [Assessment]
- F-Pattern Layout: [Assessment]
- Table Readability: [Assessment]
```

---

## Complete Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                Medical Software Development Workflow            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Phase 1: Requirements Gathering                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1.1 Project Vision Interview → Output: Project Vision    │ │
│  │ 1.2 Stakeholder Analysis    → Output: Stakeholder Analysis│ │
│  │ 1.3 Functional Requirements → Output: Functional Reqs    │ │
│  │ 1.4 Non-Functional Analysis → Output: Non-Functional Reqs│ │
│  │ 1.5 Software Safety Class   → Output: Safety Classification│ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  Phase 2: Document Generation                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 2.1 SRS Software Requirements Spec (+ Design/Cognitive   │ │
│  │     Psychology)                                          │ │
│  │ 2.2 SDD Software Design Spec (+ UI/UX + AI Assets)      │ │
│  │ 2.3 SWD Software Detailed Design                        │ │
│  │ 2.4 STP Software Test Plan                              │ │
│  │ 2.5 STC Software Test Cases                             │ │
│  │ 2.6 SVV Software Verification & Validation Report       │ │
│  │ 2.7 RTM Requirements Traceability Matrix (100% coverage)│ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  Phase 3: UI Flow Generation (Auto-triggered)                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 3.1 Enable app-uiux-designer.skill                      │ │
│  │ 3.2 Generate HTML Interactive Prototype                  │ │
│  │ 3.3 Generate UI Screenshots (Puppeteer)                 │ │
│  │ 3.4 Backfill SDD (UI Prototype + Images)                │ │
│  │ 3.5 Backfill SRS (Screen References + Inferred Reqs)    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  Phase 4: DOCX Generation                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 4.1 Remove MD Manual Numbering                          │ │
│  │ 4.2 Execute md-to-docx.js Conversion                    │ │
│  │ 4.3 Verify Image Embedding                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Phase 1.1: Project Vision Interview

### Interview Question Template

| Category | Question |
|----------|----------|
| Product Vision | What problem does this product solve? |
| Target Users | Who are the primary users? |
| Success Metrics | How do we measure product success? |
| Technical Constraints | What technical or regulatory constraints exist? |

---

## Phase 1.2: Stakeholder Analysis

### Stakeholder Matrix

| Role | Concerns | Influence | Communication Frequency |
|------|----------|-----------|------------------------|
| Product Owner | Feature Priority | High | Daily |
| Regulatory Specialist | IEC 62304 Compliance | High | Weekly |
| Clinical Expert | Clinical Use Scenarios | Medium | Biweekly |
| IT Personnel | System Integration | Medium | As Needed |

---

## Phase 1.5: Software Safety Classification Assessment

### IEC 62304 Software Safety Classification

| Class | Definition | Documentation Requirements |
|-------|------------|---------------------------|
| Class A | No harm possible | Basic documentation |
| Class B | May cause non-serious injury | Complete documentation + Risk analysis |
| Class C | May cause death or serious injury | Complete documentation + Risk analysis + Detailed traceability |

---

## ID Numbering System

### Document ID Format

| Document Type | ID Format | Example |
|---------------|-----------|---------|
| SRS Requirement | REQ-{MODULE}-{NNN} | REQ-AUTH-001 |
| SDD Design | SDD-{MODULE}-{NNN} | SDD-AUTH-001 |
| SDD Screen | SCR-{MODULE}-{NNN} | SCR-AUTH-001-login |
| SWD Component | SWD-{MODULE}-{NNN} | SWD-AUTH-001 |
| STC Test | STC-{REQ-ID} | STC-REQ-AUTH-001 |

### Module Codes

| Code | Module Name |
|------|-------------|
| AUTH | Authentication Module |
| DASH | Dashboard |
| TRAIN | Training Module |
| REPORT | Report Module |
| SETTING | Settings Module |
| DEVICE | Device Module |
| VOCAB | Vocabulary Module |

---

## MD to DOCX Simultaneous Generation

### Converter (md-to-docx.js)

**Location:** `~/.claude/skills/app-requirements-skill/md-to-docx.js`

```bash
# Install dependencies (first time use)
cd ~/.claude/skills/app-requirements-skill
npm install docx
npm install -g @mermaid-js/mermaid-cli  # If Mermaid diagram rendering is needed

# Convert documents
node ~/.claude/skills/app-requirements-skill/md-to-docx.js <input.md>

# Examples
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-VocabKids-1.0.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-VocabKids-1.0.md
```

### Converter Features

- ✅ Auto-parse Markdown document structure (supports English and Chinese titles)
- ✅ Auto-render Mermaid diagrams to SVG
- ✅ SVG images auto-embedded in DOCX and centered
- ✅ Support for tables, code blocks, heading hierarchy
- ✅ Auto-generate cover, table of contents, headers and footers
- ✅ Auto heading numbering (1., 1.1, 1.1.1, etc.)
- ✅ Code block formatting: line numbers, zebra stripe background
- ✅ Syntax highlighting: based on VSCode Light+ color scheme
- ✅ Local image embedding: supports PNG/JPEG

---

## Project Directory Structure

```
📁 {project-name}/
├── 📁 01-requirements/
│   └── SRS-{ProjectName}-{Version}.md/.docx
├── 📁 02-design/
│   ├── SDD-{ProjectName}-{Version}.md/.docx
│   └── SDD/images/
│       ├── iphone/
│       └── ipad/
├── 📁 03-assets/
│   ├── app-icon/
│   ├── icons/
│   └── images/
├── 📁 04-ui-flow/
│   ├── generated-ui/
│   ├── capture-screenshots.js
│   └── package.json
├── 📁 05-development/
│   └── SWD-{ProjectName}-{Version}.md/.docx
├── 📁 06-testing/
│   ├── STP-{ProjectName}-{Version}.md/.docx
│   └── STC-{ProjectName}-{Version}.md/.docx
├── 📁 07-verification/
│   └── SVV-{ProjectName}-{Version}.md/.docx
└── 📁 08-traceability/
    └── RTM-{ProjectName}-{Version}.md/.docx
```
