# 畫面與需求對應表 (Screen-Requirement Mapping)

本文件定義如何建立畫面 (UI) 與需求 (SRS) 之間的追溯關係。

## 畫面編號規則

### 畫面 ID 格式

```
SCR-{模組代碼}-{序號}

模組代碼:
- AUTH: 認證模組 (Authentication)
- HOME: 首頁模組 (Home/Dashboard)
- PAT:  病患模組 (Patient)
- CLN:  臨床模組 (Clinical)
- RPT:  報表模組 (Report)
- SET:  設定模組 (Settings)
- COM:  共用元件 (Common)

範例:
- SCR-AUTH-001: 登入畫面
- SCR-PAT-010:  病患列表
- SCR-CLN-020:  用藥紀錄
```

## 對應表範本

### 畫面清單

```markdown
| 畫面 ID | 畫面名稱 | 模組 | 對應需求 | Figma | 狀態 |
|---------|----------|------|----------|-------|------|
| SCR-AUTH-001 | 登入畫面 | AUTH | SRS-001, SRS-002 | [連結]() | ✅ |
| SCR-AUTH-002 | 註冊畫面 | AUTH | SRS-003~005 | [連結]() | ✅ |
| SCR-AUTH-003 | 忘記密碼 | AUTH | SRS-006 | [連結]() | 🔄 |
| SCR-HOME-001 | 首頁 | HOME | SRS-010~015 | [連結]() | 📝 |
```

### 詳細對應表

針對每個畫面建立詳細對應：

```markdown
## SCR-AUTH-001 登入畫面

### 基本資訊
- **畫面名稱:** 登入畫面 (Login Screen)
- **模組:** Authentication
- **Figma:** [連結](https://figma.com/...)
- **設計版本:** v1.2
- **最後更新:** 2024-01-15

### 需求追溯

| 需求編號 | 需求描述 | UI 元素 | 驗收標準 |
|----------|----------|---------|----------|
| SRS-001 | 帳號密碼登入 | 帳號輸入框, 密碼輸入框, 登入按鈕 | AC1, AC2 |
| SRS-002 | 記住帳號功能 | 記住我核取方塊 | AC1 |
| SRS-003 | 生物辨識登入 | Face ID/指紋按鈕 | AC1, AC2 |

### UI 元素清單

| 元素 ID | 元素類型 | 說明 | 對應需求 |
|---------|----------|------|----------|
| txt_account | TextField | 帳號輸入框 | SRS-001 |
| txt_password | TextField | 密碼輸入框 | SRS-001 |
| btn_login | Button | 登入按鈕 | SRS-001 |
| chk_remember | Checkbox | 記住我 | SRS-002 |
| btn_biometric | IconButton | 生物辨識 | SRS-003 |
| lnk_forgot | TextLink | 忘記密碼連結 | SRS-006 |

### 使用的資產

| 資產類型 | 檔案名稱 | 路徑 |
|----------|----------|------|
| Icon | ic_visibility.svg | 03-assets/icons/svg/ |
| Icon | ic_fingerprint.svg | 03-assets/icons/svg/ |
| Icon | ic_face_id.svg | 03-assets/icons/svg/ |
| Image | bg_login.png | 03-assets/images/source/ |

### 畫面狀態

| 狀態 | 說明 | 截圖 |
|------|------|------|
| Default | 預設狀態 | [圖片]() |
| Loading | 登入中 | [圖片]() |
| Error | 登入失敗 | [圖片]() |
| Biometric | 生物辨識提示 | [圖片]() |

### 按鈕導航 (Button Navigation)

定義每個可互動元素的目標畫面，供 UI 生成工具建立正確的流程連結：

| 元素 ID | 元素文字 | 動作類型 | 目標畫面 | 條件/備註 |
|---------|----------|----------|----------|-----------|
| btn_login | 登入 | navigate | SCR-HOME-001 | 驗證成功時 |
| btn_login | 登入 | navigate | SCR-AUTH-001 (Error) | 驗證失敗時 |
| lnk_forgot | 忘記密碼 | navigate | SCR-AUTH-003 | - |
| lnk_register | 註冊 | navigate | SCR-AUTH-002 | - |
| btn_biometric | 生物辨識 | navigate | SCR-HOME-001 | 驗證成功時 |
| btn_back | 返回 | back | history.back() | 上一頁 |

**動作類型說明：**
- `navigate`: 導航到指定畫面
- `back`: 返回上一頁 (history.back)
- `modal`: 開啟彈窗 (指定 Modal ID)
- `external`: 開啟外部連結
- `action`: 觸發動作 (無導航，如提交表單)

**目標畫面格式：**
- 標準畫面: `SCR-{模組}-{序號}` (如 SCR-AUTH-001)
- 狀態變體: `SCR-{模組}-{序號} ({狀態})` (如 SCR-AUTH-001 (Error))
- 返回上頁: `history.back()`
- 彈窗: `MODAL-{模組}-{序號}` (如 MODAL-AUTH-001)
```

## 追溯矩陣整合

### 與 RTM 的對應

```markdown
需求追溯矩陣 (RTM) 擴展:

| SRS ID | SDD ID | SWD ID | Screen ID | STC ID | SVV ID |
|--------|--------|--------|-----------|--------|--------|
| SRS-001 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-001 | SVV-001 |
| SRS-002 | SDD-001 | SWD-001 | SCR-AUTH-001 | STC-002 | SVV-001 |
| SRS-010 | SDD-010 | SWD-010 | SCR-HOME-001 | STC-010 | SVV-002 |
```

### 完整追溯路徑

```
SRS-001 (需求: 帳號密碼登入)
    │
    ├── SDD-001 (設計: 認證模組)
    │       │
    │       └── SWD-001 (詳細設計: AuthenticationService)
    │
    ├── SCR-AUTH-001 (畫面: 登入畫面)
    │       │
    │       ├── Figma Frame: "SCR-AUTH-001 - Login"
    │       │
    │       ├── UI Elements:
    │       │   ├── txt_account
    │       │   ├── txt_password
    │       │   └── btn_login
    │       │
    │       └── Assets:
    │           ├── ic_visibility.svg
    │           └── bg_login.png
    │
    └── STC-001 (測試: 登入功能測試)
            │
            └── SVV-001 (驗證: 認證模組驗證)
```

## 資產與畫面對應

### 資產使用矩陣

追蹤每個資產被哪些畫面使用：

```markdown
| 資產名稱 | 類型 | 使用畫面 | 對應需求 |
|----------|------|----------|----------|
| ic_home.svg | Icon | SCR-HOME-001, SCR-COM-001 | SRS-010 |
| ic_patient.svg | Icon | SCR-PAT-001~010 | SRS-020~030 |
| ic_alert_critical.svg | Icon | SCR-CLN-*, SCR-HOME-001 | SRS-040 |
| bg_login.png | Image | SCR-AUTH-001 | SRS-001 |
| app_icon.png | AppIcon | 全域 | - |
```

### 元件使用矩陣

追蹤共用元件的使用情況：

```markdown
| 元件名稱 | Figma Component | 使用畫面 | 說明 |
|----------|-----------------|----------|------|
| PatientCard | Card/Patient/Default | SCR-PAT-001, SCR-HOME-001 | 病患資訊卡片 |
| AlertBanner | Alert/Critical/Default | SCR-CLN-*, SCR-HOME-001 | 危急值警示 |
| VitalSign | Display/VitalSign | SCR-PAT-002, SCR-CLN-010 | 生命徵象顯示 |
```

## 醫療特定考量

### 臨床安全相關畫面標記

```markdown
| 畫面 ID | 安全等級 | 說明 | 特殊要求 |
|---------|----------|------|----------|
| SCR-CLN-001 | ⚠️ High | 用藥畫面 | 雙重確認、大字體 |
| SCR-CLN-010 | 🔴 Critical | 劑量計算 | 不可編輯結果、稽核紀錄 |
| SCR-PAT-001 | ⚠️ High | 病患辨識 | 照片+文字雙確認 |
```

### 無障礙需求標記

```markdown
| 畫面 ID | WCAG 等級 | 對比度 | 字體大小 | 備註 |
|---------|-----------|--------|----------|------|
| SCR-AUTH-001 | AA | ✅ 7:1 | 16px+ | 支援放大 200% |
| SCR-CLN-001 | AAA | ✅ 10:1 | 18px+ | 臨床環境需求 |
```

## 版本控制

### 畫面版本紀錄

```markdown
## SCR-AUTH-001 版本歷史

| 版本 | 日期 | 變更說明 | 影響需求 | 設計師 |
|------|------|----------|----------|--------|
| v1.0 | 2024-01-01 | 初版設計 | SRS-001 | @designer |
| v1.1 | 2024-01-10 | 新增生物辨識 | SRS-003 | @designer |
| v1.2 | 2024-01-15 | 調整按鈕位置 | - | @designer |
```

## 與 app-uiux-designer.skill 整合

### 整合流程

本 Skill 產出的 SRS/SDD 畫面規格可與 `app-uiux-designer.skill` 雙向同步：

```
┌─────────────────────────────────────────────────────────────┐
│            medical-software-requirements-skill              │
│                                                             │
│  SRS.md                          SDD.md                     │
│  ├── 功能需求                    ├── UI/UX 設計章節          │
│  ├── 驗收標準 (AC)               ├── 畫面規格 (SCR-*)        │
│  └── 畫面對應                    └── Button Navigation      │
│        │                               │                    │
│        │ ① 讀取需求                    │ ② 讀取規格          │
│        ▼                               ▼                    │
│   ┌─────────────────────────────────────────────┐           │
│   │         app-uiux-designer.skill             │           │
│   │  ③ 生成 UI + 推斷缺失流程 + 推斷新需求       │           │
│   └─────────────────────────────────────────────┘           │
│                          │                                  │
│                          ▼                                  │
│   generated-ui/                                             │
│   ├── HTML UI 檔案                                          │
│   ├── screenshots/                                          │
│   ├── ui-flow-diagram.html                                  │
│   └── flow-diagram.md (Mermaid)                             │
│                          │                                  │
│           ┌──────────────┴──────────────┐                   │
│           │ ④ 回補更新                   │                   │
│           ▼                              ▼                   │
│   SRS.md (更新)                  SDD.md (更新)               │
│   ├── 新增功能需求 (推斷)        ├── Button Navigation       │
│   ├── 驗收標準 (AC)             ├── 嵌入 UI 截圖             │
│   └── RTM 對應                  ├── Mermaid 流程圖           │
│           │                     └── 心理學驗證結果           │
│           ▼                              │                   │
│   ┌──────────────────────────────────────┐                  │
│   │ ⑤ 重新產生文件                        │                  │
│   │ ├── SRS.docx (含新需求)               │                  │
│   │ ├── SDD.docx (含截圖)                 │                  │
│   │ └── RTM.md (100% 追溯)               │                  │
│   └──────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 整合命令

```bash
# 1. 從 SDD 生成 UI (app-uiux-designer.skill)
生成 UI ./docs/SDD.md --output ./generated-ui/

# 2. 產生 Mermaid 流程圖 (可嵌入 SDD/SRS)
node ~/.claude/skills/app-uiux-designer.skill/scripts/generate-mermaid-flow.js ./generated-ui/ ./docs/flow-diagram.md

# 3. 截圖嵌入 SDD
node ~/.claude/skills/app-uiux-designer.skill/scripts/embed-screenshots-to-sdd.js ./docs/SDD.md ./generated-ui/screenshots --copy-to ./docs/images

# 4. 心理學驗證
驗證心理學 ./generated-ui/ --output ./reports/psychology-report.md

# 5. 回補 SDD (Button Navigation 推斷結果)
回補 SDD ./docs/SDD.md --from ./generated-ui/

# 6. 回補 SRS (推斷新需求 + 驗收標準)
回補 SRS ./docs/SRS.md --from ./generated-ui/

# 7. 重新產生 DOCX
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js ./docs/SRS.md
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js ./docs/SDD.md

# 8. 驗證 RTM 100% 追溯
驗證 RTM ./docs/RTM.md
```

### ID 格式一致性

兩個 Skill 統一使用 **SCR-{模組}-{序號}** 格式：

| Skill | ID 格式 | 範例 |
|-------|---------|------|
| medical-software-requirements-skill | SCR-AUTH-001 | SCR-AUTH-001 登入畫面 |
| app-uiux-designer.skill | SCR-AUTH-001 | SCR-AUTH-001-login.html |

### 資料同步項目

| 項目 | 方向 | 說明 |
|------|------|------|
| Button Navigation | 雙向 | SDD 定義 → UI 實作 → 推斷回補 SDD |
| UI 截圖 | UI→SDD | 自動嵌入 SDD 畫面章節 |
| Mermaid 流程圖 | UI→SDD/SRS | 自動更新流程圖章節 |
| 心理學驗證 | UI→SDD | 更新 SDD 心理學符合度章節 |
| **功能需求 (推斷)** | UI→SRS | 從按鈕推斷缺失的功能需求 |
| **驗收標準 (AC)** | UI→SRS | 從導航產生驗收標準 |
| **畫面對應** | UI→SRS | 更新需求的 SCR 對應 |
| 追溯矩陣 | 雙向 | SRS/SDD/SCR/STC 100% 追溯 |

### SRS 回補規則

從 UI 流程推斷 SRS 需求時遵循以下規則：

| 按鈕類型 | 推斷需求 | 信心度 |
|----------|----------|--------|
| 儲存/提交/確認 | 資料處理功能 | 🟢 高 |
| 建立/新增 | 新增功能 | 🟢 高 |
| 返回/取消 | 返回機制 | 🟢 高 |
| 下一步/繼續 | 流程導航 | 🟡 中 |
| 登入/登出 | 認證功能 | 🟢 高 |
| 刪除/移除 | 刪除功能 | 🟢 高 |

### 驗收標準 (AC) 產生規則

```markdown
# 按鈕導航 → 驗收標準

1. **存在性 AC:**
   Given 使用者在 {來源畫面}
   Then 應能看到「{按鈕文字}」按鈕

2. **功能 AC:**
   When 點擊「{按鈕文字}」按鈕
   Then 應 {執行動作} / 導航至 {目標畫面}

3. **條件 AC (若有):**
   Given {前置條件}
   When 點擊「{按鈕文字}」按鈕
   Then 應 {條件結果}
```

### 回補報告

執行回補後會產生以下報告：

| 報告 | 路徑 | 說明 |
|------|------|------|
| SRS 回補報告 | `./reports/srs-feedback-report.md` | 新增需求、AC、RTM 更新 |
| SDD 回補報告 | `./reports/sdd-feedback-report.md` | Navigation、截圖、流程圖 |
| RTM 驗證報告 | `./reports/rtm-verification.md` | 追溯完整性檢查 |
```
