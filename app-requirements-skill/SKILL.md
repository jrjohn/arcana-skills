---
name: app-requirements-skill
description: |
  IEC 62304 軟體開發文件工具。所有 App 開發皆遵循 IEC 62304 標準流程，產出完整文件套件。
  當用戶提到以下任一關鍵字時，應主動啟用此 Skill：

  【通用 App 開發觸發詞】產生一個 App、開發 App、建立 App、製作 App、設計 App、
  開發一套 App、我要開發、我想開發、幫我開發、開發需求、App 需求、
  iOS App、Android App、跨平台 App、行動應用、手機應用、
  需求規格書、設計規格書、軟體規格、UI Flow、互動原型、使用者流程、
  學習 App、教育 App、電商 App、社群 App、工具 App、
  SRS 軟體需求規格書、SDD 軟體設計規格書。

  【IEC 62304 文件觸發詞】SRS、SDD、SWD、STP、STC、SVV、RTM、IEC 62304、
  check compliance、compliance check、追溯矩陣、軟體需求、軟體設計、
  測試計畫、測試案例、DOCX 產出、文件產出、需求收集、需求分析、架構設計、詳細設計。

  【設計相關觸發詞】UI/UX 設計、SCR 畫面、設計心理學、Design Psychology、
  認知負荷、Cognitive Load、漸進式揭露、Progressive Disclosure、
  Fitts' Law、Hick's Law、Dashboard、使用者流程、UX Flow、回補、feedback to docs。

  【App 類型自動識別】（所有類型皆遵循 IEC 62304 流程）
  偵測關鍵字自動載入對應需求模組：
  • 學習/教育/單字/測驗/課程 → education-requirements.md
  • 購物/電商/商品/購物車 → ecommerce-requirements.md
  • 社群/好友/貼文/聊天 → social-requirements.md
  • 醫療/健康/患者/處方 → healthcare-requirements.md
  • 筆記/待辦/生產力 → productivity-requirements.md
  • 其他 → standard-app-requirements.md

  所有類型統一產出：SRS → SDD → SWD → STP → STC → SVV → RTM（100% 追溯）

  【功能說明】
  第一階段 - 需求收集：
    ⚠️ 開始需求收集時，必須先啟用 app-uiux-designer.skill 詢問 UI 需求
    → 專案願景訪談、利害關係人分析
    → UI 需求收集（目標用戶、平台、畫面估算、設計偏好）
    → 功能/非功能需求收集、驗收標準定義
    → 參考 standard-app-requirements.md 確保不遺漏標準功能
  第二階段 - 文件產出：SRS/SDD/SWD/STP/STC/SVV/RTM 文件，SDD 階段整合 UI/UX 設計與 AI 資產產生。
  第三階段 - UI Flow 產生：
    → 依據第一階段收集的 UI 需求產生 Design Token + Theme CSS
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
  ⚠️ 需求收集階段 UI 需求：開始需求收集時，必須先啟用 app-uiux-designer.skill 詢問 UI 需求。
  ⚠️ UI Flow 必須產出：SDD 完成後，必須啟用 app-uiux-designer.skill 產生 HTML UI Flow，不可跳過。
  ⚠️ 可點擊元素覆蓋：UI Flow 中每個可點擊元素（按鈕、連結、Tab）必須有對應的目標畫面，確保導航完整。
  ⚠️ **模板格式強制**：SRS/SDD 必須使用本 Skill 的模板格式，否則 md-to-docx.js 轉換會失敗。禁止使用自訂中文標題結構。
     初始化專案請執行：`node [SKILL_DIR]/scripts/init-project.js [PROJECT_DIR]`
     （跨平台相容：Windows/macOS/Linux）

  【🚀 需求收集階段 - UI 需求詢問 (Critical - 最先執行)】
  當開始需求收集時，必須立即啟用 app-uiux-designer.skill 詢問以下 UI 需求：

  ⚠️ Step 0: 啟用 app-uiux-designer.skill 並詢問 UI 需求 (強制 - 需求收集開始時)
     ┌─────────────────────────────────────────────────────────┐
     │  📱 UI 需求收集 (Phase 1)                               │
     │  1️⃣ 目標平台？(iOS / Android / Both / Web)              │
     │  2️⃣ 目標裝置？(iPhone / iPad / Android Phone / Tablet)  │
     │  3️⃣ 預估畫面數量？(參考 standard-app-screens.md)        │
     │  4️⃣ 需要哪些標準模組？                                  │
     │     □ 認證 (登入/註冊/社群登入)                         │
     │     □ Onboarding (歡迎畫面/權限請求)                    │
     │     □ 個人檔案                                         │
     │     □ 設定 (通知/隱私/外觀/語言)                        │
     │     □ 幫助支援                                         │
     │     □ 搜尋                                             │
     │     □ 通知列表                                         │
     │     □ 交易/購物車 (電商類)                              │
     │     □ 訊息/聊天 (社群類)                               │
     └─────────────────────────────────────────────────────────┘

     ┌─────────────────────────────────────────────────────────┐
     │  🎨 App Theme Style Discovery (Phase 2)                │
     │  5️⃣ 目標使用者年齡層？                                  │
     │  6️⃣ APP 類型 / 產業？                                   │
     │  7️⃣ 期望的視覺風格？                                    │
     │  8️⃣ 品牌色彩偏好？                                      │
     │  9️⃣ 主要語言 / 地區？                                   │
     │  🔟 是否需要深色模式？                                  │
     └─────────────────────────────────────────────────────────┘

     收集後：
     - 記錄至 SRS 的 User Interface Requirements 章節
     - 產生初步畫面清單 (SCR-* 預估)
     - 計算需求數量估算 (參考 standard-app-requirements.md)

  【🚀 SDD 產出後 - UI Flow 產生規則 (Critical)】
  當 SDD 文件產出完成後，依據需求收集階段的 UI 需求：

  1. 產生 Design Token JSON、{project}-theme.css、Style Guide
  2. 依據 Theme Style 產生 HTML UI Flow (互動原型 + 截圖)
  3. 回補 SDD (UI 原型 + 圖片)
  4. 回補 SRS (Screen References + Inferred Requirements + User Flows) ⚠️強制

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
     - 前置: cd ~/.claude/skills/app-requirements-skill && npm install docx
     - SDD: node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-*.md
     - SRS: node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-*.md

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

# App 需求收集與文件產出 Skill (IEC 62304)

本 Skill 提供完整的 App 開發支援：從需求收集、IEC 62304 文件產出、到設計資產管理。
支援各類型 App：教育學習、電商、社群、生產力工具、醫療健康等。

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
| EDU | 教育學習 | ECOM | 電商 |
| SOCIAL | 社群 | PROD | 生產力 |
| HEALTH | 醫療健康 | SYNC | 同步 |

---

## MD 轉 DOCX 指令

```bash
# 安裝依賴 (首次)
cd ~/.claude/skills/app-requirements-skill
npm install docx

# 轉換文件
node ~/.claude/skills/app-requirements-skill/md-to-docx.js <input.md>

# 範例
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-VocabKids-1.0.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-VocabKids-1.0.md
```

### 移除 MD 手動編號

```bash
bash ~/.claude/skills/app-requirements-skill/remove-heading-numbers.sh <file.md>
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

### 需求參考
- `standard-app-requirements.md` - 標準 App 功能需求清單 (60+ 需求)

### App 類型需求
- `education-requirements.md` - 教育學習類 App 需求 (50+ 需求)
- `ecommerce-requirements.md` - 電商類 App 需求 (43+ 需求)
- `social-requirements.md` - 社群類 App 需求 (45+ 需求)
- `productivity-requirements.md` - 生產力工具類 App 需求 (43+ 需求)
- `healthcare-requirements.md` - 醫療健康類 App 需求 (41+ 需求)

### Skill 整合
- `skill-integration-guide.md` - 與 app-uiux-designer.skill 整合指南

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

## 驗證工具

### 追溯驗證

```bash
# 驗證追溯覆蓋率
node ~/.claude/skills/app-requirements-skill/scripts/verify-traceability.js [project-dir]

# 輸出：traceability-report.json
# Exit code: 0 = 通過, 1 = 失敗
```

### 合規檢查

```bash
# 執行完整合規檢查
node ~/.claude/skills/app-requirements-skill/scripts/compliance-checker.js [project-dir]

# 檢查項目：
# - TRACE-100: 追溯覆蓋率 100%
# - DOC-SYNC: 文件同步 (MD/DOCX)
# - UI-IMAGES: SDD 嵌入 UI 圖片
# - MERMAID: 圖表使用 Mermaid
# - NO-MANUAL-NUM: 禁止手動編號
# - SRS-FEEDBACK: SRS 回補完成
# - UI-FLOW: UI Flow 已產出
# - CLICK-COVER: 可點擊元素覆蓋

# 輸出：compliance-report.json
# Exit code: 0 = 合規, 1 = 不合規
```

### UI Flow 驗證

```bash
# 截圖 + 驗證
cd 04-ui-flow
node capture-screenshots.js

# 僅驗證
node capture-screenshots.js --validate-only

# 強制截圖 (跳過驗證)
node capture-screenshots.js --skip-validation
```

---

## Skill 整合

本 Skill 與 `app-uiux-designer.skill` 協作：

| 階段 | 主導 Skill | 協作 Skill | 動作 |
|------|-----------|-----------|------|
| 需求收集 | app-requirements-skill | app-uiux-designer.skill | 詢問 UI 需求 |
| SRS/SDD 產出 | app-requirements-skill | - | 文件產出 |
| UI Flow 產生 | app-uiux-designer.skill | - | HTML 產生 |
| 文件回補 | app-requirements-skill | app-uiux-designer.skill | SDD/SRS 更新 |
| 驗證 | app-requirements-skill | - | 追溯/合規檢查 |

> 詳細整合流程請參考：`references/skill-integration-guide.md`

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
