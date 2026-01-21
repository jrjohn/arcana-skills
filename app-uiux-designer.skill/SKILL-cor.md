---
name: app-uiux-designer
description: |
  Enterprise UI/UX design expert using Chain of Repository (CoR) architecture.
  SRS/SDD → HTML UI Flow + 100% Coverage Validation.
  Platform: iOS HIG / Material Design 3 / WCAG.
---

# UI/UX Designer Skill (Chain of Repository)

**Core:** SRS/SDD → HTML UI Flow + 100% Coverage Validation
**Architecture:** Chain of Repository - 按需載入節點，減少 token 使用

---

## Quick Start

1. **檢查狀態**: 讀取 `workspace/current-process.json`
2. **進入節點**: 讀取對應的 `process/XX/README.md`
3. **執行步驟**: 依照 README.md 執行
4. **更新狀態**: 完成後更新 `current-process.json`

---

## Process Chain

| Step | Process | 進入條件 | 退出條件 |
|------|---------|----------|----------|
| 00 | init | SDD 完整 + 智慧預測完成 | 模板已複製、變數已替換 |
| 03 | generation | 00 完成 | **iPad + iPhone HTML 已產生、index.html 變數已替換** (BLOCKING) |
| 04 | validation | 03 完成 | **覆蓋率 = 100%** (BLOCKING) |
| 05 | diagram | 04 通過 | ui-flow-diagram-ipad/iphone.html 完成 |
| 06 | screenshot | 05 完成 | 截圖已產生 |
| 07 | feedback | 06 完成 | SDD/SRS 已更新 |
| 08 | finalize | 07 完成 | 驗證通過 + 完成報告 |

> ⚠️ **注意**: 01-discovery 和 02-planning 已由 `app-requirements-skill` 完成，本 Skill 從 00-init 直接進入 03-generation

---

## Node Loading Protocol

```
Claude 收到 skill 啟用時：
1. 讀取此 SKILL.md (本檔案)
2. 讀取 workspace/current-process.json
   - 若 current_process 存在 → 恢復到該節點
   - 若 current_process = null → 從 00-init 開始
3. 讀取 process/{current}/README.md
4. 執行節點步驟
5. 完成後執行 Node Transition Protocol (NTP)
6. 進入下一節點
```

---

## Node Transition Protocol (NTP) ⭐ NEW

> **節點轉換時自動產生 Phase Summary，支援 Context Compact**

### 轉換流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. Exit Validation    - 驗證當前節點完成                      │
│  2. Generate Summary   - 產生 Phase Summary                   │
│  3. Save to Workspace  - 保存到 phase-summary.md              │
│  4. Update State       - 更新 current-process.json            │
│  5. Output Prompt      - 輸出下一節點指引                       │
└─────────────────────────────────────────────────────────────┘
```

### 執行命令

```bash
node node-transition.js <from-node> <to-node> [project-path]

# 範例
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/node-transition.js 03-generation 04-validation /path/to/04-ui-flow
```

### Phase Summary 保存位置

| 檔案 | 說明 |
|------|------|
| `workspace/phase-summary.md` | 當前 Phase Summary (最新) |
| `workspace/phase-history.md` | 所有 Phase Summary 歷史 |

### Claude 在 Compaction 後

1. 讀取 `workspace/phase-summary.md` 恢復上下文
2. 讀取 `workspace/current-process.json` 確認當前節點
3. 繼續執行當前節點的剩餘工作

---

## Workspace Management

| 檔案 | 說明 |
|------|------|
| `workspace/current-process.json` | 目前流程狀態 |
| `workspace/context/` | 已載入的節點檔案 |
| `workspace/state/` | Compaction 保存點 |

### Compaction 保護 (AFP)

**節點轉換時**（使用 NTP）：
```bash
node node-transition.js <from> <to> [path]
# 自動產生 phase-summary.md + 更新 current-process.json
```

**手動保存**：
```bash
cp workspace/current-process.json workspace/state/process-state.json
```

**Compaction 後恢復**：
```bash
# 1. 快速健康檢查
bash quick-health-check.sh [project-path]

# 2. 讀取 Phase Summary 恢復上下文
cat workspace/phase-summary.md

# 3. 繼續當前節點
```

---

## Blocking Checkpoints

以下節點為 **阻斷點**，必須滿足退出條件才能繼續：

| 節點 | 阻斷條件 |
|------|----------|
| 00-init | 模板必須完整複製、變數必須替換 |
| **03-generation** | **iPad 與 iPhone 畫面數量必須一致**、**index.html 變數必須全部替換** ⚠️ |
| 04-validation | **覆蓋率必須 = 100%** |
| 07-feedback | SDD/SRS 必須更新完成 |

### 03-generation 阻斷驗證

```bash
# 必須通過以下驗證才能進入 04-validation
IPAD=$(find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l)
IPHONE=$(find iphone -name "SCR-*.html" | wc -l)
VARS=$(grep -c '{{.*}}' index.html)

[ "$IPAD" -eq "$IPHONE" ] && [ "$VARS" -eq 0 ] && echo "✅ 通過" || echo "❌ 阻斷"
```

---

## Device Specifications

| Device | Viewport | Body Style |
|--------|----------|------------|
| iPad Pro 11" | 1194 x 834 | `width: 1194px; height: 834px;` |
| iPhone 15/16 Pro | 393 x 852 | `width: 393px; height: 852px;` |

---

## Key Scripts

| 腳本 | 位置 | 說明 |
|------|------|------|
| **node-transition.js** | `templates/ui-flow/` | **節點轉換 + Phase Summary (NTP)** ⭐ |
| **exit-gate.js** | `templates/ui-flow/` | **統一驗證入口** |
| **quick-health-check.sh** | `templates/ui-flow/` | **Compaction 後快速檢查** |
| init-project.sh | `process/00-init/templates/` | 專案初始化 |
| validate-navigation.js | `templates/ui-flow/` | 導航驗證 |
| capture-screenshots.js | `templates/ui-flow/` | 截圖生成 + Error Recovery |
| convert-to-iphone.sh | `templates/ui-flow/scripts/` | iPad→iPhone 轉換 |
| update-index-counts.sh | `templates/ui-flow/scripts/` | index.html 變數替換 |

### Script Dependencies (MANDATORY)

03-generation 階段**必須**執行以下腳本：
1. `convert-to-iphone.sh` - 產生所有 iPhone 版本 HTML
2. `update-index-counts.sh` - 替換 index.html 中的所有變數

**⚠️ 若未執行這些腳本，04-validation 將會失敗！**

---

## References (按需載入)

| 類別 | 檔案 |
|------|------|
| 平台 | `references/platforms/{ios-hig,material-design,wcag}.md` |
| 心理學 | `references/psychology/{gestalt,cognitive,emotional}.md` |
| 程式碼生成 | `references/code-gen/{react,angular,swiftui,compose}.md` |

---

## Commands

| 指令 | 動作 |
|------|------|
| `進入節點 XX` | 讀取 `process/XX/README.md` |
| `下一步` | 自動判斷並進入下一節點 |
| `保存狀態` | 複製 current-process.json 到 state/ |
| `恢復狀態` | 從 state/ 讀取並恢復 |
| `顯示進度` | 讀取 current-process.json 的 progress |

---

## Screen ID Format

| 類型 | 格式 | 範例 |
|------|------|------|
| 畫面 | `SCR-{MODULE}-{NNN}-{name}` | SCR-AUTH-001-login |
| 需求 | `REQ-{MODULE}-{NNN}` | REQ-AUTH-001 |

**Module Codes:** AUTH, ONBOARD, HOME, VOCAB, TRAIN, REPORT, SETTING, PARENT, PROFILE

---

## Architecture Benefits

1. **減少 Token 使用** - 只載入當前節點相關檔案
2. **Compaction 恢復** - 狀態保存在 workspace/
3. **清晰流程** - 每個節點有明確進入/退出條件
4. **模組化** - 可獨立更新各節點內容
