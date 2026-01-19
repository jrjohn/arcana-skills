# Button Navigation Specification

## Overview

本規格定義了 SDD 中 Button Navigation Table 的標準格式，以及如何與 `app-uiux-designer.skill` 的模板整合。

**目標：** SDD 提供 Button Navigation 作為**優先來源**，減少 UI Flow 的預測需求。

### 導航解析優先順序

```
1️⃣ SDD Button Navigation 表格 (優先)
   → 如果有 Target Screen，直接使用

2️⃣ app-uiux-designer.skill 智慧預測 (備用)
   → 如果 SDD 沒有提供，根據命名約定預測

3️⃣ 預設值 (最後)
   → 無法判斷時使用 # 或 (current)
```

**注意：** 預測功能保留作為備用機制，確保 UI Flow 在 SDD 不完整時仍可產出。

---

## SDD Button Navigation Table Format

### 標準格式（必須）

每個 SCR-* 畫面區塊**必須**包含以下 Button Navigation 表格：

```markdown
### Button Navigation

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | 登入 | Button | SCR-AUTH-004-role | 驗證成功 |
| btn_register | 立即註冊 | Link | SCR-AUTH-002-register | - |
| btn_forgot | 忘記密碼? | Link | SCR-AUTH-003-forgot-password | - |
| btn_apple | Apple | Button | SCR-AUTH-004-role | Apple 登入成功 |
| btn_google | Google | Button | SCR-AUTH-004-role | Google 登入成功 |
| btn_back | < | Button | history.back() | - |
```

### 欄位說明

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| **Element ID** | 元素唯一識別碼 | Yes | `btn_login` |
| **Element Text** | 顯示文字 | Yes | `登入` |
| **Type** | 元素類型 | Yes | `Button`, `Link`, `Icon`, `Tab`, `Row` |
| **Target Screen** | 導航目標 | Yes | `SCR-AUTH-004-role` |
| **Condition** | 觸發條件 | Optional | `驗證成功`, `-` |

### Target Screen 格式

| Format | Usage | Example |
|--------|-------|---------|
| `SCR-MODULE-NNN-name` | 導航到指定畫面 | `SCR-AUTH-004-role` |
| `history.back()` | 返回上一頁 | 用於 Back/Close 按鈕 |
| `(close modal)` | 關閉 Modal | 用於 Modal 內的關閉按鈕 |
| `(submit form)` | 提交表單後導航 | 需搭配 Condition 指定成功/失敗目標 |

---

## UI Flow Template Variable Mapping

### SDD → HTML 變數對應表

| SDD Button Navigation | HTML Template Variable | HTML Output |
|-----------------------|------------------------|-------------|
| `Target Screen: SCR-AUTH-002-register` | `{{TARGET_REGISTER}}` | `onclick="location.href='SCR-AUTH-002-register.html'"` |
| `Target Screen: SCR-AUTH-004-role` | `{{TARGET_AFTER_LOGIN}}` | `onclick="location.href='SCR-AUTH-004-role.html'"` |
| `Target Screen: SCR-DASH-001-home` | `{{TARGET_HOME}}` | `onclick="location.href='SCR-DASH-001-home.html'"` |
| `Target Screen: SCR-SETTING-001-settings` | `{{TARGET_SETTINGS}}` | `onclick="location.href='SCR-SETTING-001-settings.html'"` |
| `Target Screen: history.back()` | `{{TARGET_BACK}}` | `onclick="history.back()"` |

### 標準變數列表

```
{{TARGET_BACK}}              - 返回上一頁 (通常是 history.back())
{{TARGET_HOME}}              - 首頁
{{TARGET_SETTINGS}}          - 設定頁
{{TARGET_PROFILE}}           - 個人資料頁
{{TARGET_AFTER_LOGIN}}       - 登入成功後導航目標
{{TARGET_REGISTER}}          - 註冊頁
{{TARGET_FORGOT_PASSWORD}}   - 忘記密碼頁
{{TARGET_SECURITY}}          - 帳號安全頁
{{TARGET_NOTIFICATION}}      - 通知設定頁
{{TARGET_APPEARANCE}}        - 外觀設定頁
{{TARGET_PRIVACY}}           - 隱私設定頁
{{TARGET_DATA}}              - 資料管理頁
{{TARGET_TERMS}}             - 服務條款頁
{{TARGET_ABOUT}}             - 關於頁
{{TARGET_LOGOUT}}            - 登出 (通常回到登入頁)
```

---

## SDD Pre-Generation Checklist

在呼叫 `app-uiux-designer.skill` 產生 UI Flow 之前，**必須**完成以下檢查：

### ⚠️ Button Navigation 完整性檢查 (100% 必須)

- [ ] 每個 SCR-* 區塊都有 `### Button Navigation` 表格
- [ ] 每個可點擊元素都有 Target Screen
- [ ] 所有 Target Screen 指向存在的 SCR-* ID
- [ ] 沒有懸空的 Target Screen（指向不存在的畫面）
- [ ] `history.back()` 用於所有返回按鈕
- [ ] Modal/Sheet 有明確的關閉機制

### 驗證腳本

```bash
# 執行 Button Navigation 驗證
node ~/.claude/skills/app-requirements-skill/scripts/validate-button-navigation.js [SDD_FILE]
```

---

## Integration Workflow

### 完整流程（規格驅動，無預測）

```
Phase 1: 需求收集 (app-requirements-skill)
├── 收集功能需求
├── 定義 REQ-* 清單
└── 輸出: SRS

Phase 2: 畫面設計規格 (app-requirements-skill)
├── 定義所有 SCR-* 畫面
├── 為每個畫面建立 Button Navigation Table ⚠️ 完整填寫
├── 驗證 Navigation 完整性 (100% 覆蓋)
└── 輸出: SDD (spec-complete)

Phase 3: UI Flow 生成 (app-uiux-designer.skill)
├── 讀取 SDD 的 Button Navigation Table
├── 將 Target Screen 轉換為 {{TARGET_*}} 變數
├── 複製模板並替換變數
├── **不需要預測任何導航目標**
└── 輸出: HTML UI Flow

Phase 4: SRS/SDD 回補 (app-uiux-designer.skill → app-requirements-skill)
├── 截圖嵌入 SDD
├── 更新 SRS Screen References
├── 驗證 RTM 覆蓋率
└── 輸出: 更新後的 SRS/SDD
```

---

## Examples

### Example 1: Login Screen (SCR-AUTH-001)

**SDD 定義：**

```markdown
#### SCR-AUTH-001: Login Screen

**模組：** AUTH
**優先級：** P0
**相關需求：** REQ-AUTH-001, REQ-AUTH-002

##### 畫面說明
使用者登入畫面，支援 Email/密碼登入及社群登入。

##### UI 元件表

| Component | Type | Description | Requirement |
|-----------|------|-------------|-------------|
| txt_email | TextField | Email 輸入框 | REQ-AUTH-001 |
| txt_password | PasswordField | 密碼輸入框 | REQ-AUTH-001 |
| btn_login | Button | 登入按鈕 | REQ-AUTH-001 |
| btn_apple | Button | Apple 登入 | REQ-AUTH-002 |
| btn_google | Button | Google 登入 | REQ-AUTH-002 |
| lnk_forgot | Link | 忘記密碼連結 | REQ-AUTH-003 |
| lnk_register | Link | 註冊連結 | REQ-AUTH-004 |

##### Button Navigation ⚠️ MANDATORY

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | 登入 | Button | SCR-AUTH-004-role | 驗證成功 |
| btn_apple | Apple | Button | SCR-AUTH-004-role | Apple 登入成功 |
| btn_google | Google | Button | SCR-AUTH-004-role | Google 登入成功 |
| lnk_forgot | 忘記密碼? | Link | SCR-AUTH-003-forgot-password | - |
| lnk_register | 立即註冊 | Link | SCR-AUTH-002-register | - |
```

**UI Flow 模板變數對應：**

```html
<!-- login-ipad.html 模板 -->
<button onclick="location.href='{{TARGET_AFTER_LOGIN}}'">登入</button>
<a href="{{TARGET_FORGOT_PASSWORD}}">忘記密碼?</a>
<a href="{{TARGET_REGISTER}}">立即註冊</a>

<!-- 替換後 -->
<button onclick="location.href='SCR-AUTH-004-role.html'">登入</button>
<a href="SCR-AUTH-003-forgot-password.html">忘記密碼?</a>
<a href="SCR-AUTH-002-register.html">立即註冊</a>
```

### Example 2: Settings Screen (SCR-SETTING-001)

**SDD 定義：**

```markdown
##### Button Navigation ⚠️ MANDATORY

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_back | < | Icon | history.back() | - |
| row_profile | 個人資料 | Row | SCR-SETTING-002-profile | - |
| row_security | 帳號安全 | Row | SCR-SETTING-003-security | - |
| row_privacy | 隱私設定 | Row | SCR-SETTING-004-privacy | - |
| row_data | 資料管理 | Row | SCR-SETTING-005-data | - |
| row_notification | 通知設定 | Row | SCR-SETTING-006-notification | - |
| row_appearance | 主題外觀 | Row | SCR-SETTING-007-appearance | - |
| row_voice | 語音設定 | Row | SCR-SETTING-008-voice | - |
| row_terms | 服務條款 | Row | SCR-SETTING-010-terms | - |
| row_about | 關於 | Row | SCR-SETTING-012-about | - |
| btn_logout | 登出 | Button | SCR-AUTH-001-login | 確認登出 |
```

---

## Validation Rules

### Rule 1: No Empty Targets

```
❌ 錯誤: Target Screen 為空
| btn_login | 登入 | Button |  | - |

✅ 正確: Target Screen 有明確目標
| btn_login | 登入 | Button | SCR-AUTH-004-role | 驗證成功 |
```

### Rule 2: All Targets Must Exist

```
❌ 錯誤: Target Screen 指向不存在的畫面
| btn_login | 登入 | Button | SCR-AUTH-999-unknown | - |

✅ 正確: Target Screen 存在於 SDD 中
| btn_login | 登入 | Button | SCR-AUTH-004-role | - |
```

### Rule 3: Settings Rows Must Navigate

```
❌ 錯誤: 設定列使用 alert()
| row_profile | 個人資料 | Row | alert('功能開發中') | - |

✅ 正確: 設定列導航到子畫面
| row_profile | 個人資料 | Row | SCR-SETTING-002-profile | - |
```

### Rule 4: Consistent Format

```
❌ 錯誤: Target 包含副檔名
| btn_login | 登入 | Button | SCR-AUTH-004-role.html | - |

✅ 正確: Target 只有 Screen ID
| btn_login | 登入 | Button | SCR-AUTH-004-role | - |
```

---

## Summary

| Before (Prediction-Based) | After (Spec-Driven) |
|---------------------------|---------------------|
| SDD 只有畫面名稱 | SDD 包含完整 Button Navigation |
| UI Flow 要「猜」導航目標 | UI Flow 直接讀取 SDD 定義 |
| 可能有導航缺失 | 100% 導航覆蓋保證 |
| 回補時可能發現不一致 | 規格一致，無需修正 |
