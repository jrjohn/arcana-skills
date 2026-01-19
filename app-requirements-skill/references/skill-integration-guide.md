# Skill 整合指南 (Cross-Skill Integration Guide)

本文件定義 `app-requirements-skill` 與 `app-uiux-designer.skill` 之間的整合協作流程。

---

## ⚠️ MANDATORY: UI Flow 必須透過 app-uiux-designer.skill 產生

> **這是阻斷規則！禁止手動建立 UI Flow HTML，必須使用 skill 產生！**

### 強制呼叫方式

當 SDD 完成後，**必須**使用 Skill tool 呼叫 app-uiux-designer.skill：

```
工具：Skill
參數：
  skill: "app-uiux-designer.skill"
  args: "請根據 SDD 文件 ({SDD_PATH}) 產生 HTML UI Flow 互動式原型。
         專案資訊：
         - 專案名稱：{PROJECT_NAME}
         - 目標裝置：{DEVICE}
         - 視覺風格：{STYLE}
         - 品牌主色：{COLOR}
         - 目標使用者：{TARGET_USER}
         輸出目錄：{OUTPUT_DIR}"
```

### 禁止行為

| 禁止項目 | 原因 |
|----------|------|
| ❌ 手動建立 UI Flow HTML | 必須透過 skill 確保模板合規 |
| ❌ 跳過 app-uiux-designer.skill | 無法確保 100% 導航覆蓋 |
| ❌ 無 Button Navigation 就產生 UI Flow | 導航目標不明確 |

---

## 整合架構

```
┌─────────────────────────────────────────────────────────────────┐
│                      App 開發完整流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐         │
│  │ app-requirements-skill│      │ app-uiux-designer.skill│       │
│  │                       │      │                       │        │
│  │  Phase 1: 需求收集    │      │                       │        │
│  │  Phase 2: SRS 產出    │      │                       │        │
│  │  Phase 3: SDD 產出    │─────▶│  Phase 4: UI Flow     │        │
│  │                       │      │  Phase 5: Screenshots  │        │
│  │  Phase 6: 文件回補   │◀─────│  Phase 6: SDD/SRS 回補 │        │
│  │  Phase 7: RTM 驗證    │      │                       │        │
│  │  Phase 8: DOCX 產出   │      │                       │        │
│  └──────────────────────┘      └──────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 觸發時機

### app-requirements-skill → app-uiux-designer.skill

| 觸發條件 | 動作 |
|---------|------|
| 需求收集階段開始 | 啟用 uiux skill 詢問 UI 需求（平台、裝置、模組、風格） |
| SDD 產出完成 | 啟用 uiux skill 產生 HTML UI Flow |
| SDD 包含 SCR-* 區塊 | uiux skill 為每個 SCR-* 產生對應畫面 |

### app-uiux-designer.skill → app-requirements-skill

| 觸發條件 | 動作 |
|---------|------|
| UI Flow 產出完成 | 回補 SDD（截圖、UI 原型參考） |
| UI Flow 產出完成 | 回補 SRS（Screen References、Inferred Requirements） |
| 發現缺失畫面 | 建議新增 REQ-NAV-* 導航需求 |

---

## 資料交換格式

### SDD → UI Flow（app-requirements-skill 產出）

**⚠️ 關鍵：Button Navigation 表格（MANDATORY）**

每個 SCR-* 區塊**必須**包含 Button Navigation 表格，這是 UI Flow 導航的唯一資料來源。

```markdown
## SCR-AUTH-001-login: 登入畫面

**模組：** AUTH
**優先級：** P0
**相關需求：** REQ-AUTH-001, REQ-AUTH-002

### 畫面說明
使用者登入畫面，支援 Email/密碼登入與社群登入。

### UI 元件規格
| 元件 ID | 元件類型 | 規格 | 對應需求 |
|---------|---------|------|----------|
| txt_email | TextField | Email 輸入框 | REQ-AUTH-001 |
| txt_password | PasswordField | 密碼輸入框 | REQ-AUTH-001 |
| btn_login | Button | 登入按鈕 | REQ-AUTH-001 |
| btn_register | Link | 註冊連結 | REQ-AUTH-002 |
| btn_forgot | Link | 忘記密碼連結 | REQ-AUTH-003 |

### Button Navigation ⚠️ MANDATORY
| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | 登入 | Button | SCR-DASH-001 | 驗證成功 |
| btn_register | 立即註冊 | Link | SCR-AUTH-002-register | - |
| btn_forgot | 忘記密碼 | Link | SCR-AUTH-003-forgot | - |
| btn_apple | Apple 登入 | Button | SCR-DASH-001 | Apple 驗證成功 |
| btn_google | Google 登入 | Button | SCR-DASH-001 | Google 驗證成功 |
```

### Button Navigation → 模板變數對應

app-uiux-designer.skill 使用 Button Navigation 表格自動填入模板變數：

| SDD Target Screen | 模板變數 | 說明 |
|-------------------|----------|------|
| `SCR-AUTH-002-register` | `{{TARGET_REGISTER}}` | 註冊頁面 |
| `SCR-AUTH-003-forgot` | `{{TARGET_FORGOT_PASSWORD}}` | 忘記密碼頁 |
| `SCR-DASH-001` | `{{TARGET_AFTER_LOGIN}}` | 登入後首頁 |
| `(current)` | `#` | 留在當前頁面 |
| `(back)` | `{{TARGET_BACK}}` | 返回上一頁 |
| `(modal)` | `showModal('...')` | 彈出對話框 |

### 導航解析優先順序

app-uiux-designer.skill 解析導航目標時，依照以下優先順序：

```
1️⃣ SDD Button Navigation 表格 (優先)
   ↓ 如果有 Target Screen 欄位，直接使用

2️⃣ 智慧預測 (備用)
   ↓ 如果 SDD 沒有提供，根據命名約定預測

3️⃣ 預設值 (最後)
   ↓ 無法判斷時使用 # 或 (current)
```

**好處：**
- SDD 完整時 → 零預測，100% 準確
- SDD 不完整時 → 預測機制確保 UI Flow 仍可產出
- 向後相容 → 舊專案不需重寫 SDD

### UI Flow → SDD 回補（app-uiux-designer.skill 產出）

```markdown
## SCR-AUTH-001-login: 登入畫面

... (原有內容) ...

### UI 原型參考
| 平台 | 截圖 | HTML 原型 |
|------|------|-----------|
| iPad | ![](images/ipad/SCR-AUTH-001-login.png) | [查看](04-ui-flow/auth/SCR-AUTH-001-login.html) |
| iPhone | ![](images/iphone/SCR-AUTH-001-login.png) | [查看](04-ui-flow/iphone/SCR-AUTH-001-login.html) |
```

### UI Flow → SRS 回補（app-uiux-designer.skill 產出）

```markdown
## Screen References

| 需求 ID | 相關畫面 | 說明 |
|---------|---------|------|
| REQ-AUTH-001 | SCR-AUTH-001-login | 登入畫面實作 |
| REQ-AUTH-002 | SCR-AUTH-002-register | 註冊畫面實作 |

## Inferred Requirements (UI 推導需求)

| ID | 來源 | 描述 | 驗收條件 |
|----|------|------|---------|
| REQ-NAV-001 | SCR-AUTH-001 登入按鈕 | 登入成功後導向 Dashboard | 驗證憑證後顯示 SCR-DASH-001 |
| REQ-NAV-002 | SCR-AUTH-001 註冊連結 | 點擊註冊導向註冊頁 | 顯示 SCR-AUTH-002 |
```

---

## 驗證檢查點

### Checkpoint 1: SDD 產出後（啟動 UI Flow 前）

```
☑ SDD 包含所有 SCR-* 區塊
☑ 每個 SCR-* 有 UI 元素表格
☑ 每個 UI 元素指定目標畫面（如適用）
☑ REQ ↔ SCR 對應完整
```

### Checkpoint 2: UI Flow 產出後

```
☑ 所有 SCR-* 有對應 HTML 檔案
☑ iPad 和 iPhone 版本都存在
☑ 可點擊元素覆蓋率 = 100%
☑ 導航完整性驗證通過
☑ 截圖已產生
```

### Checkpoint 3: 回補後（最終驗證）

```
☑ SDD 包含所有截圖
☑ SRS 包含 Screen References
☑ SRS 包含 Inferred Requirements
☑ RTM 覆蓋率 = 100%
☑ DOCX 已重新產生
```

---

## ⚠️ 強制規範

### UI Flow 模板使用 (MANDATORY)

app-uiux-designer.skill 產出 UI Flow 時**必須**遵守：

| 規則 | 說明 |
|------|------|
| ❌ **禁止** | 從頭建立自訂 HTML 檔案 |
| ✅ **必須** | 複製 `~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/` 模板 |
| ✅ **必須** | 替換模板中的 `{{VARIABLE}}` 變數 |
| ✅ **必須** | 按照模板目錄結構建立畫面 |

### 模板複製指令

```bash
# 複製模板到專案
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/* ./04-ui-flow/

# 模板包含：
# - index.html (畫面總覽)
# - device-preview.html (多裝置預覽)
# - screen-template-iphone.html (iPhone 畫面模板)
# - screen-template-ipad.html (iPad 畫面模板)
# - capture-screenshots.js (截圖腳本)
```

---

## 錯誤處理

### 常見問題與解決方案

| 問題 | 原因 | 解決方案 |
|------|------|----------|
| UI Flow 缺少畫面 | SDD 中 SCR-* 定義不完整 | 補充 SDD 的 SCR-* 區塊 |
| 可點擊元素無目標 | SDD 未指定目標畫面 | 更新 SDD UI 元素表格 |
| 截圖嵌入失敗 | 路徑不正確 | 確認 images/ 目錄結構 |
| RTM 覆蓋不足 | 需求未對應畫面 | 補充 Screen References |

### 回退策略

若 app-uiux-designer.skill 無法使用：

1. **基礎 UI Flow**：手動建立簡化版 UI Flow（純文字描述）
2. **ASCII Wireframe**：在 SDD 中使用 ASCII 線框圖（注意 DOCX 轉換限制）
3. **外部工具**：使用 Figma/Sketch 產出設計，手動嵌入

---

## 執行命令

### 完整流程

```bash
# 1. 需求收集（app-requirements-skill 主導）
# 啟動時自動詢問 UI 需求

# 2. SRS/SDD 產出
# 自動產出 01-planning/SRS-*.md 和 02-design/SDD-*.md

# 3. UI Flow 產出（app-uiux-designer.skill）
cd 04-ui-flow
# HTML 檔案自動產生

# 4. 截圖與驗證
npm install puppeteer --save-dev
node capture-screenshots.js

# 5. 文件回補
# uiux skill 自動回補 SDD 和 SRS

# 6. DOCX 產出
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SRS-*.md
node ~/.claude/skills/app-requirements-skill/md-to-docx.js SDD-*.md
```

### 僅驗證

```bash
cd 04-ui-flow
node capture-screenshots.js --validate-only
```

---

## 檔案結構對應

```
project/
├── 01-planning/
│   ├── SRS-{project}.md          ← app-requirements-skill
│   └── SRS-{project}.docx        ← app-requirements-skill
├── 02-design/
│   ├── SDD-{project}.md          ← app-requirements-skill + uiux 回補
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

## 版本相容性

| app-requirements-skill | app-uiux-designer.skill | 狀態 |
|------------------------|-------------------------|------|
| v1.0+ | v1.0+ | 相容 |

---

## 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-01-09 | 1.1 | 新增強制使用模板規範 (MANDATORY Template Usage) |
| 2026-01-09 | 1.0 | 初版，定義整合架構與資料交換格式 |
