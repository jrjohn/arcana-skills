# Path Definitions - app-uiux-designer.skill

This document defines all path variables used throughout the skill.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `$HOME` | User home directory | `/Users/<username>` |
| `$SKILL_DIR` | Skill installation directory | `$HOME/.claude/skills/app-uiux-designer.skill` |
| `$PROJECT_PATH` | Project root (contains 01-requirements, 02-design, etc.) | User specified |
| `$UI_FLOW_PATH` | UI Flow output directory | `$PROJECT_PATH/04-ui-flow` |

---

## Skill Directory Structure

```
$SKILL_DIR/
├── SKILL.md                    # Main skill instructions
├── SKILL-cor.md                # Chain of Repository index
├── PATHS.md                    # This file
├── CLAUDE.md                   # Skill-specific instructions
│
├── process/                    # Process node definitions
│   ├── 00-init/
│   │   ├── README.md           # Node instructions
│   │   └── exit-validation.sh  # Exit gate script
│   ├── 03-generation/
│   │   ├── README.md
│   │   └── exit-validation.sh
│   ├── 04-validation/
│   ├── 05-diagram/
│   ├── 06-screenshot/
│   ├── 07-feedback/
│   └── 08-finalize/
│
├── templates/                  # Templates and scripts
│   └── ui-flow/
│       ├── index-template.html
│       ├── device-preview-template.html
│       ├── screen-template.html
│       ├── screen-template-iphone.html
│       ├── project-theme.css
│       ├── notify-parent.js
│       ├── validate-navigation.js
│       ├── validate-consistency.js
│       ├── validate-iframe-src.js
│       ├── validate-all.js
│       ├── post-generation-gate.js
│       ├── exit-gate.js           # Unified exit validation
│       ├── recover-state.js
│       ├── quick-health-check.sh
│       ├── capture-screenshots.js
│       └── reference-example/
│           └── standards.json
│
├── references/                 # Reference documentation
│   ├── platforms/
│   │   ├── ios-hig.md
│   │   ├── material-design.md
│   │   └── wcag.md
│   └── psychology/
│       ├── gestalt.md
│       ├── cognitive.md
│       └── emotional.md
│
└── workspace-template/         # Template for new projects
    └── current-process.json
```

---

## Project Directory Structure

```
$PROJECT_PATH/
├── 01-requirements/
│   ├── SRS-*.md
│   └── SRS-*.docx
│
├── 02-design/
│   ├── SDD-*.md
│   ├── SDD-*.docx
│   └── images/
│       ├── ipad/
│       └── iphone/
│
├── 03-test/
│
└── 04-ui-flow/                 # $UI_FLOW_PATH
    ├── index.html              # Navigation index
    ├── device-preview.html     # Device preview with sidebar
    │
    ├── docs/
    │   ├── ui-flow-diagram.html       # Device selector
    │   ├── ui-flow-diagram-ipad.html
    │   └── ui-flow-diagram-iphone.html
    │
    ├── shared/
    │   ├── project-theme.css
    │   └── notify-parent.js
    │
    ├── workspace/              # AFP state management
    │   ├── current-process.json
    │   ├── validation-chain.json
    │   ├── validation-report.json
    │   ├── context/
    │   └── state/
    │       └── process-state.json
    │
    ├── {module}/               # iPad screens (auth, vocab, train, etc.)
    │   └── SCR-{MODULE}-{NNN}-{name}.html
    │
    ├── iphone/                 # iPhone screens
    │   └── SCR-*.html
    │
    └── screenshots/
        ├── ipad/
        │   └── SCR-*.png
        └── iphone/
            └── SCR-*.png
```

---

## Path Usage Examples

### In Bash Scripts

```bash
# Define paths
SKILL_DIR="$HOME/.claude/skills/app-uiux-designer.skill"
PROJECT_PATH="/path/to/project"
UI_FLOW_PATH="$PROJECT_PATH/04-ui-flow"

# Use validation scripts
node "$SKILL_DIR/templates/ui-flow/validate-navigation.js" "$UI_FLOW_PATH"
node "$SKILL_DIR/templates/ui-flow/exit-gate.js" 03-generation "$UI_FLOW_PATH"

# Run exit validation for a node
bash "$SKILL_DIR/process/04-validation/exit-validation.sh" "$UI_FLOW_PATH"
```

### In Node.js Scripts

```javascript
const path = require('path');

const SKILL_DIR = path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill');
const PROJECT_PATH = process.argv[2] || process.cwd();
const UI_FLOW_PATH = path.join(PROJECT_PATH, '04-ui-flow');

// Access templates
const templatesDir = path.join(SKILL_DIR, 'templates/ui-flow');
const processDir = path.join(SKILL_DIR, 'process');
```

### In Markdown Documentation

```markdown
<!-- Reference a skill file -->
See `$SKILL_DIR/process/03-generation/README.md`

<!-- Reference a project file -->
Output: `$UI_FLOW_PATH/index.html`

<!-- Actual command -->
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/exit-gate.js 04-validation
```

---

## Key Scripts Reference

| Script | Location | Usage |
|--------|----------|-------|
| `node-transition.js` | `$SKILL_DIR/templates/ui-flow/` | `node node-transition.js <from> <to> [path]` ⭐ NTP |
| `exit-gate.js` | `$SKILL_DIR/templates/ui-flow/` | `node exit-gate.js <node> [project-path]` |
| `post-generation-gate.js` | `$SKILL_DIR/templates/ui-flow/` | `node post-generation-gate.js [project-path]` |
| `validate-navigation.js` | `$SKILL_DIR/templates/ui-flow/` | `node validate-navigation.js [project-path]` |
| `validate-consistency.js` | `$SKILL_DIR/templates/ui-flow/` | `node validate-consistency.js [project-path]` |
| `recover-state.js` | `$SKILL_DIR/templates/ui-flow/` | `node recover-state.js [project-path]` |
| `quick-health-check.sh` | `$SKILL_DIR/templates/ui-flow/` | `bash quick-health-check.sh [project-path]` |
| `capture-screenshots.js` | `$SKILL_DIR/templates/ui-flow/` | `node capture-screenshots.js [project-path]` |

---

## Common Path Patterns

### Screen Files

| Type | Pattern | Example |
|------|---------|---------|
| iPad screen | `$UI_FLOW_PATH/{module}/SCR-*.html` | `auth/SCR-AUTH-001-login.html` |
| iPhone screen | `$UI_FLOW_PATH/iphone/SCR-*.html` | `iphone/SCR-AUTH-001-login.html` |
| iPad screenshot | `$UI_FLOW_PATH/screenshots/ipad/*.png` | `screenshots/ipad/SCR-AUTH-001-login.png` |
| iPhone screenshot | `$UI_FLOW_PATH/screenshots/iphone/*.png` | `screenshots/iphone/SCR-AUTH-001-login.png` |

### Module Directories

Standard modules: `auth`, `common`, `dash`, `home`, `onboard`, `parent`, `profile`, `progress`, `report`, `setting`, `train`, `vocab`

### Workspace Files

| File | Path | Purpose |
|------|------|---------|
| Process state | `$UI_FLOW_PATH/workspace/current-process.json` | 當前流程狀態 |
| **Phase summary** | `$UI_FLOW_PATH/workspace/phase-summary.md` | **最新 Phase Summary (NTP)** ⭐ |
| **Phase history** | `$UI_FLOW_PATH/workspace/phase-history.md` | **所有 Phase Summary 歷史** |
| Validation chain | `$UI_FLOW_PATH/workspace/validation-chain.json` | 驗證歷史記錄 |
| State backup | `$UI_FLOW_PATH/workspace/state/process-state.json` | Compaction 保存點 |
| Validation report | `$UI_FLOW_PATH/workspace/validation-report.json` | 驗證結果報告 |
| Screenshot errors | `$UI_FLOW_PATH/workspace/screenshot-error-log.json` | 截圖錯誤記錄 |

---

## Notes

1. Always use absolute paths in scripts to avoid directory context issues
2. Use `$SKILL_DIR` instead of hardcoding `~/.claude/skills/app-uiux-designer.skill`
3. Always pass project path as argument rather than relying on `cwd`
4. Screen files follow the pattern: `SCR-{MODULE}-{NNN}-{name}.html`
