---
name: medical-software-requirements-skill
description: |
  醫療器材軟體 IEC 62304 開發文件工具。當用戶提到以下任一關鍵字時，應主動啟用此 Skill：

  【自動觸發關鍵字】SRS、SDD、SWD、STP、STC、SVV、RTM、軟體需求、軟體設計、需求規格、設計規格、
  測試計畫、測試案例、追溯矩陣、IEC 62304、醫療軟體、DOCX 產出、文件產出、check compliance、
  compliance check、需求收集、需求分析、架構設計、詳細設計、UI/UX 設計、SCR 畫面、
  設計心理學、Design Psychology、認知負荷、Cognitive Load、漸進式揭露、Progressive Disclosure、
  Fitts' Law、Hick's Law、Dashboard、使用者流程、UX Flow、回補、feedback to docs。

  【功能說明】
  第一階段 - 需求收集：專案願景訪談、利害關係人分析、功能/非功能需求收集、驗收標準定義。
  第二階段 - 文件產出：SRS/SDD/SWD/STP/STC/SVV/RTM 文件，SDD 階段整合 UI/UX 設計與 AI 資產產生。
  第三階段 - UI Flow 產生：
    ⚠️ 強制先啟用 app-uiux-designer.skill 詢問 UI 設計偏好（App Theme Style Discovery）
    → 收集使用者年齡層、APP類型、視覺風格、品牌色彩、語言地區、深色模式偏好
    → 產生 Design Token + Theme CSS + Style Guide
    → 依據 Theme Style 產生 HTML UI Flow
    → 回補 SDD 和 SRS
  第四階段 - DOCX 產生：MD 轉 DOCX，自動編號，圖片嵌入。

  【強制規則】
  ⚠️ 追溯要求：所有追溯方向必須達到 100% 覆蓋率。
  ⚠️ 文件同步：.md 與 .docx 必須同步，更新 MD 時必須重新產生 DOCX。
  ⚠️ UI 圖片：SDD 必須嵌入 UI 設計圖片，不可僅參考外部連結。
  ⚠️ 圖表格式：所有圖表必須使用 Mermaid 語法，禁止使用 ASCII 文字製圖。
  ⚠️ 標題編號：MD 檔案禁止包含手動編號，DOCX 轉換時自動產生階層式編號。
  ⚠️ SRS 回補強制：UI Flow 回補 SDD 後，必須同時回補 SRS (Screen References + Inferred Requirements)。
  ⚠️ UI 設計偏好收集：產生 UI Flow 前，必須先啟用 app-uiux-designer.skill 詢問使用者 UI 設計偏好。

  【🚀 SDD 產出後自動 UI Flow 產生規則 (Critical)】
  當 SDD 文件產出完成後，必須自動執行：

  ⚠️ Step 0: 啟用 app-uiux-designer.skill 並詢問 UI 設計偏好 (強制)
     在產生任何 UI 之前，必須先使用 app-uiux-designer.skill 的
     「App Theme Style Designer」功能詢問使用者以下問題：
     ┌─────────────────────────────────────────────────────────┐
     │  🎨 App Theme Style Discovery                          │
     │  1️⃣ 目標使用者年齡層？                                  │
     │  2️⃣ APP 類型 / 產業？                                   │
     │  3️⃣ 期望的視覺風格？                                    │
     │  4️⃣ 品牌色彩偏好？                                      │
     │  5️⃣ 主要語言 / 地區？                                   │
     │  6️⃣ 是否需要深色模式？                                  │
     └─────────────────────────────────────────────────────────┘
     收集回答後產生：Design Token JSON、{project}-theme.css、
     Style Guide Documentation、Color Psychology Explanation

  1. 依據 Theme Style 產生 HTML UI Flow (互動原型 + 截圖)
  2. 回補 SDD (UI 原型 + 圖片)
  3. 回補 SRS (Screen References + Inferred Requirements + User Flows) ⚠️強制

  【🔄 UI Flow 回補接收規則 (Critical)】
  當 app-uiux-designer.skill 完成 UI Flow 產生後：

  📌 Step 1: 接收 SDD 更新
     - 各 SCR-* 區塊的 UI 原型參考
     - 圖片參考路徑 (images/ipad/, images/iphone/)
     - 更新 SDD Revision History

  📌 Step 2: 接收 SRS 更新 (⚠️ 強制 - 不可跳過!)
     ┌─────────────────────────────────────────────────────────┐
     │ 1. Screen References 章節                               │
     │    - 每個功能需求對應到實作畫面 SCR-*                    │
     │                                                         │
     │ 2. Inferred Requirements 章節                           │
     │    - REQ-NAV-*: 導航需求 (按鈕點擊後的畫面切換)          │
     │    - 每個需求需包含: ID, 來源, 描述, 驗收條件, 追溯      │
     │                                                         │
     │ 3. User Flows 章節 (Mermaid flowchart)                  │
     │    - 使用實際 SCR-* ID 標示每個節點                      │
     │    - 標示所有按鈕導航路徑                               │
     └─────────────────────────────────────────────────────────┘

  📌 Step 3: 更新 RTM
     - 將 SRS ↔ SCR 對應更新到 RTM
     - 驗證 100% 追溯覆蓋率

  📌 Step 4: 產生 UI 截圖
     - 安裝: cd 04-ui-flow && npm install puppeteer --save-dev
     - 執行: node capture-screenshots.js
     - 輸出: 02-design/SDD/images/iphone/*.png, images/ipad/*.png

  📌 Step 5: 重新產生 DOCX
     - 前置: cd ~/.claude/skills/medical-software-requirements-skill && npm install docx
     - SDD: node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SDD-*.md
     - SRS: node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SRS-*.md

  📌 回補完成驗證清單
     - [ ] SDD.md 所有 SCR-* 區塊已更新
     - [ ] SRS.md Screen References 章節已新增
     - [ ] SRS.md Inferred Requirements 已新增
     - [ ] SRS.md User Flows 已更新
     - [ ] SDD 和 SRS Revision History 都已更新
     - [ ] SDD.docx 和 SRS.docx 都已重新產生

  【🧠 心理學自動套用規則】
  執行文件操作時，自動讀取並套用：
  1️⃣ 設計心理學：references/design-psychology.md
  2️⃣ 認知心理學：references/cognitive-psychology.md
  3️⃣ 文件編排心理學：references/document-layout-psychology.md

  【技術堆疊參考】
  SDD 撰寫技術選型時，優先參考對應平台的開發者 Skill：
  • Android → android-developer-skill
  • iOS → ios-developer-skill
  • Python Backend → python-developer-skill
  • Node.js Backend → nodejs-developer-skill
---

# 醫療器材軟體需求收集與文件產出 Skill

本 Skill 提供完整的醫療軟體開發支援：從需求收集、IEC 62304 文件產出、到設計資產管理。

> **📖 詳細說明請參考 references/ 目錄下的文件**

---

## 快速參考

### ID 編號系統

| 文件類型 | ID 格式 | 範例 |
|---------|--------|------|
| SRS 需求 | REQ-{MODULE}-{NNN} | REQ-AUTH-001 |
| SDD 設計 | SDD-{MODULE}-{NNN} | SDD-AUTH-001 |
| SDD 畫面 | SCR-{MODULE}-{NNN}-{desc} | SCR-AUTH-001-login |
| SWD 元件 | SWD-{MODULE}-{NNN} | SWD-AUTH-001 |
| STC 測試 | STC-{REQ-ID} | STC-REQ-AUTH-001 |

### 模組代碼

| 代碼 | 模組 | 代碼 | 模組 |
|------|------|------|------|
| AUTH | 認證 | DASH | Dashboard |
| VOCAB | 字庫 | TRAIN | 訓練 |
| REPORT | 報告 | SETTING | 設定 |
| DEVICE | 設備 | COM | 共用元件 |

---

## MD 轉 DOCX 指令

```bash
# 安裝依賴 (首次)
cd ~/.claude/skills/medical-software-requirements-skill
npm install docx

# 轉換文件
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js <input.md>

# 範例
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SRS-VocabKids-1.0.md
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SDD-VocabKids-1.0.md
```

### 移除 MD 手動編號

```bash
bash ~/.claude/skills/medical-software-requirements-skill/remove-heading-numbers.sh <file.md>
```

---

## 文件範本

### srs-template/ (SRS 模板目錄)

| 檔案 | 說明 |
|------|------|
| `srs-template.md` | SRS 完整範本 (含說明) |
| `srs-template-bare.md` | SRS 精簡範本 |

### sdd-template/ (SDD 模板目錄)

| 檔案 | 說明 |
|------|------|
| `sdd-template.md` | SDD 完整範本 (含 15 種設計觀點) |
| `sdd-template-bare.md` | SDD 精簡範本 |

---

## References 目錄

### 工作流程與標準
- `workflow-details.md` - 完整工作流程詳細說明
- `sdd-standards.md` - SDD 格式與規範標準
- `md-to-docx-converter.md` - MD 轉 DOCX 轉換器說明

### 心理學指南
- `design-psychology.md` - 設計心理學原則
- `cognitive-psychology.md` - 認知心理學原則
- `document-layout-psychology.md` - 文件編排心理學

### IEC 62304 文件範本
- `srs-template.md` - SRS 範本
- `sdd-template.md` - SDD 範本
- `swd-template.md` - SWD 範本
- `stp-template.md` - STP 範本
- `stc-template.md` - STC 範本
- `svv-template.md` - SVV 範本
- `rtm-template.md` - RTM 範本

### UI/UX 設計
- `figma-integration.md` - UI/UX 設計工具整合
- `screen-requirement-mapping.md` - 畫面與需求對應
- `asset-specifications.md` - Android/iOS 資產尺寸規格
- `ui-image-embedding.md` - UI 圖片嵌入 SDD 規範

### 需求收集
- `medical-nfr-checklist.md` - 醫療軟體非功能需求檢核清單
- `interview-questions.md` - 需求訪談問題庫

---

## 專案目錄結構

```
📁 {project-name}/
├── 📁 01-requirements/     # SRS
├── 📁 02-design/           # SDD + images/
├── 📁 03-assets/           # App Icon, Icons, Images
├── 📁 04-ui-flow/          # HTML UI Flow + capture-screenshots.js
├── 📁 05-development/      # SWD
├── 📁 06-testing/          # STP, STC
├── 📁 07-verification/     # SVV
└── 📁 08-traceability/     # RTM
```

---

## 追溯完整度要求 (100%)

| 追溯方向 | 說明 | 要求 |
|---------|------|------|
| SRS → SDD | 每個需求有對應設計 | 100% |
| SDD → SWD | 每個設計有詳細實作 | 100% |
| SWD → STC | 每個元件有測試案例 | 100% |
| SRS → SCR | 每個需求有對應畫面 | 100% |

---

## 文件編碼規則

### 標題格式 (重要!)

| 格式 | 範例 | 說明 |
|------|------|------|
| ✅ 正確 | `## Introduction` | 無手動編號 |
| ❌ 錯誤 | `## 1. Introduction` | 有手動編號 (會導致重複) |

DOCX 轉換時會自動產生：`1. Introduction`

### 圖表格式

| 格式 | 說明 |
|------|------|
| ✅ Mermaid | 使用 Mermaid 語法繪製 |
| ❌ ASCII | 禁止使用 ASCII 文字製圖 |

---

## 回補報告範本

```markdown
## 回補完成報告

### SDD 回補
| 項目 | 數量 | 狀態 |
|------|------|------|
| SCR 畫面更新 | 18 | ✅ 完成 |
| 圖片嵌入 | 36 | ✅ 完成 |

### SRS 回補 (⚠️ 強制)
| 項目 | 數量 | 狀態 |
|------|------|------|
| Screen References | 18 | ✅ 完成 |
| Inferred Requirements | 5 | ✅ 完成 |
| User Flows 更新 | 6 | ✅ 完成 |

### DOCX 產生
| 項目 | 狀態 |
|------|------|
| SDD.docx | ✅ 完成 |
| SRS.docx | ✅ 完成 |
```
