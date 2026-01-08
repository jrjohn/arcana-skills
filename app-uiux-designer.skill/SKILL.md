---
name: app-uiux-designer
description: |
  Enterprise UI/UX design expert. SRS/SDD → HTML UI Flow + Coverage Validation. Features: App Theme Style Designer, Visual Style Extraction, Multi-platform Assets, Motion Design, Dark Mode, i18n. Platform: iOS HIG / Material Design 3 / WCAG.

  【心理學整合】
  本 Skill 整合專業設計心理學知識：
  • 格式塔心理學 (Gestalt) - 接近性、相似性、連續性、閉合性、圖地關係等 7 原則
  • 美學設計原則 - 黃金比例、視覺層級、對齊、對比、留白、視覺平衡
  • 情感設計 (Don Norman) - 本能層、行為層、反思層三層次設計
  • 認知心理學 - 認知負荷、Fitts' Law、Hick's Law、漸進式揭露
  • 色彩心理學 - 色彩情感對照、文化差異、60-30-10 配色法則
---

# UI/UX Designer Skill

Enterprise-grade App & Web UI/UX design guide.

**Core:** SRS/SDD → HTML UI Flow + 100% Coverage Validation
**Features:** App Theme Style Designer | Visual Style Extraction | Motion Design | Dark Mode | i18n
**Platforms:** iOS HIG | Android Material 3 | Web WCAG | Figma

---

## Quick Reference

### Default Platform
- **Device:** iPhone 14 Pro (390×844) / Android Medium (360×800)
- **Format:** HTML + Tailwind CSS
- **Dual Platform:** iPad (1194×834) + iPhone (393×852)

### Critical Rules

1. **App Theme Style → Ask Discovery Questions First**
   See: `references/app-theme-style-designer.md`

2. **After UI Flow Complete → Auto SRS/SDD Feedback**
   See: `references/sdd-feedback.md`

3. **UI Flow Request → Auto Generate HTML**
   Triggers: "UI Flow", "Screen", "Wireframe", "Prototype"

4. **Screenshot 取代 Wireframe → 刪除 ASCII Wireframe**
   - 有截圖後，必須刪除對應的 `**Wireframe：**` 區塊
   - 原因：ASCII 在 DOCX 轉換會產生行號 bug
   - See: `references/sdd-feedback.md#截圖取代-wireframe-規則`

---

## Template Location

> **MANDATORY:** All UI Flow output must use templates from `templates/ui-flow/`

### Directory Structure
```
generated-ui/
├── index.html              # Screen overview
├── device-preview.html     # Multi-device preview (iPad/Mini/iPhone)
├── docs/
│   └── ui-flow-diagram.html  # Flow diagram (onclick → device-preview)
├── shared/
│   ├── project-theme.css   # Design System
│   └── notify-parent.js    # iframe sync
├── screenshots/            # For SDD embedding
├── auth/, dash/, etc.      # iPad screens
└── iphone/                 # iPhone screens
```

### Key Pattern - UI Flow Click Behavior
```html
<!-- CORRECT: onclick opens device-preview -->
<div class="screen-card" onclick="openScreen('auth/SCR-AUTH-001.html')">
  <img src="../screenshots/auth/SCR-AUTH-001.png">
</div>

<script>
function openScreen(screen) {
  window.open('../device-preview.html?screen=' + screen, '_blank');
}
</script>
```

---

## Reference Documents

| Category | Document | Description |
|----------|----------|-------------|
| **Core** | `ui-generation.md` | HTML/React/Angular/SwiftUI generation |
| **Core** | `spec-driven-generation.md` | SRS/SDD → UI mapping |
| **Core** | `coverage-validation.md` | 100% RTM coverage |
| **Theme** | `app-theme-style-designer.md` | Age-specific design, color psychology |
| **Theme** | `style-extraction.md` | Visual style extraction |
| **Theme** | `design-system.md` | Design tokens, components |
| **Assets** | `asset-extraction.md` | iOS/Android/Web assets |
| **Flow** | `flow-prediction.md` | User flow prediction |
| **Flow** | `sdd-feedback.md` | SRS/SDD feedback rules |
| **Platform** | `ios-guidelines.md` | Apple HIG |
| **Platform** | `android-guidelines.md` | Material Design 3 |
| **Platform** | `web-guidelines.md` | WCAG accessibility |
| **Platform** | `figma-guidelines.md` | Figma integration |
| **Advanced** | `motion-design.md` | Micro-interactions, Lottie |
| **Advanced** | `dark-mode.md` | Dark mode support |
| **Advanced** | `localization.md` | i18n, RTL |
| **Advanced** | `ux-writing.md` | Microcopy guidelines |
| **Advanced** | `data-visualization.md` | Charts, graphs |
| **QA** | `accessibility.md` | WCAG compliance |
| **QA** | `psychology-validation.md` | UX psychology validation |
| **QA** | `design-review.md` | Nielsen heuristics |
| **Psychology** | `gestalt-psychology.md` | 格式塔視覺心理學 (7 原則) |
| **Psychology** | `aesthetic-design.md` | 美學設計原則 (黃金比例、視覺層級) |
| **Psychology** | `emotional-design.md` | 情感設計理論 (Don Norman 三層次) |
| **Research** | `ux-research.md` | User research methods |
| **Templates** | `standard-app-screens.md` | 標準 App 畫面參考 (60+ 畫面) |

---

## Screen ID Format

| Type | Format | Example |
|------|--------|---------|
| Screen | `SCR-{MODULE}-{NNN}-{name}` | `SCR-AUTH-001-login` |
| Requirement | `REQ-{MODULE}-{NNN}` | `REQ-AUTH-001` |

### Module Codes
AUTH, ONBOARD, DASH, VOCAB, TRAIN, REPORT, SETTING, DEVICE, REWARD

---

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/generate-app-icons.sh` | Generate iOS/Android app icons |
| `scripts/generate-mermaid-flow.js` | Generate Mermaid flowcharts |
| `templates/ui-flow/capture-screenshots.js` | Puppeteer screenshot capture |

---

## Workflow Summary

```
1. Receive UI/UX Request
   ↓
2. If Theme Design → Ask App Theme Discovery Questions
   ↓
3. Generate HTML UI Flow (templates/ui-flow/)
   - index.html, device-preview.html, ui-flow-diagram.html
   - iPad screens + iPhone screens
   ↓
4. Generate Screenshots (capture-screenshots.js)
   ↓
5. SRS/SDD Feedback (MANDATORY)
   - Update SDD with screenshots
   - Update SRS with Screen References
   ↓
6. Regenerate DOCX
```

> **Detailed workflows in reference documents**
