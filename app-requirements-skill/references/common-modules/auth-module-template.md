# AUTH 模組模板 (Authentication Module Template)

認證模組的標準畫面定義，適用於所有需要用戶登入的 App。

---

## 模組概述

| 項目 | 值 |
|------|-----|
| 模組代碼 | AUTH |
| 必要性 | **必要** |
| 最少畫面數 | 3 |
| 完整畫面數 | 8 |
| 相關需求 | REQ-AUTH-* |

---

## 標準畫面清單

| 畫面 ID | 名稱 | 必要性 | 優先級 | 說明 |
|---------|------|--------|--------|------|
| SCR-AUTH-001-welcome | 歡迎頁 | 選配 | P1 | 首次開啟引導頁 |
| SCR-AUTH-002-login | 登入頁 | **必要** | P0 | Email/Social 登入 |
| SCR-AUTH-003-register | 註冊頁 | **必要** | P0 | 新用戶註冊 |
| SCR-AUTH-004-forgot | 忘記密碼 | **必要** | P0 | 密碼重設入口 |
| SCR-AUTH-005-verify | 驗證碼輸入 | 選配 | P1 | Email/SMS 驗證 |
| SCR-AUTH-006-reset-sent | 重設郵件已發送 | 選配 | P2 | 確認訊息頁 |
| SCR-AUTH-007-role | 角色選擇 | 選配 | P1 | 多角色 App 使用 |
| SCR-AUTH-008-pin | PIN 碼驗證 | 選配 | P1 | 家長/管理員驗證 |

---

## 畫面詳細設計

### SCR-AUTH-001-welcome: 歡迎頁

**必要性：** 選配（建議首次安裝使用）

**畫面說明：**
首次開啟 App 時的引導頁面，展示產品特色和價值主張。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| app_logo | Image | App Logo 圖示 |
| welcome_title | Text | 歡迎標題 |
| welcome_description | Text | 產品說明文字 |
| btn_start | Button | 開始使用按鈕 |
| lnk_login | Link | 已有帳號？登入 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_start | 開始使用 | Button | SCR-AUTH-003-register | - |
| lnk_login | 已有帳號？登入 | Link | SCR-AUTH-002-login | - |

---

### SCR-AUTH-002-login: 登入頁 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
用戶登入頁面，支援 Email/密碼登入及社群帳號登入。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| txt_email | TextField | Email 輸入框 |
| txt_password | SecureField | 密碼輸入框（遮罩） |
| btn_login | Button | 登入按鈕 |
| btn_apple | Button | Apple ID 登入 |
| btn_google | Button | Google 登入（選配） |
| lnk_forgot | Link | 忘記密碼？ |
| lnk_register | Link | 立即註冊 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | 登入 | Button | SCR-HOME-001-main | 驗證成功 |
| btn_apple | Apple 登入 | Button | SCR-HOME-001-main | Apple 登入成功 |
| btn_google | Google 登入 | Button | SCR-HOME-001-main | Google 登入成功 |
| lnk_forgot | 忘記密碼？ | Link | SCR-AUTH-004-forgot | - |
| lnk_register | 立即註冊 | Link | SCR-AUTH-003-register | - |

---

### SCR-AUTH-003-register: 註冊頁 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
新用戶註冊頁面，收集必要的帳戶資訊。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| txt_name | TextField | 名稱輸入框 |
| txt_email | TextField | Email 輸入框 |
| txt_password | SecureField | 密碼輸入框 |
| txt_confirm | SecureField | 確認密碼輸入框 |
| chk_terms | Checkbox | 同意條款 |
| btn_register | Button | 註冊按鈕 |
| lnk_login | Link | 已有帳號？登入 |
| lnk_terms | Link | 使用條款 |
| lnk_privacy | Link | 隱私政策 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_register | 註冊 | Button | SCR-AUTH-005-verify | 需要驗證 |
| btn_register | 註冊 | Button | SCR-HOME-001-main | 直接通過 |
| lnk_login | 已有帳號？登入 | Link | SCR-AUTH-002-login | - |
| lnk_terms | 使用條款 | Link | SCR-SETTING-*-terms | - |
| lnk_privacy | 隱私政策 | Link | SCR-SETTING-*-privacy | - |

---

### SCR-AUTH-004-forgot: 忘記密碼 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
密碼重設申請頁面。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| txt_email | TextField | Email 輸入框 |
| btn_send | Button | 發送重設郵件 |
| btn_back | Button | 返回登入 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_send | 發送重設郵件 | Button | SCR-AUTH-006-reset-sent | 發送成功 |
| btn_back | 返回登入 | Button | SCR-AUTH-002-login | - |

---

### SCR-AUTH-005-verify: 驗證碼輸入

**必要性：** 選配

**畫面說明：**
Email 或 SMS 驗證碼輸入頁面。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| lbl_instruction | Text | 驗證說明文字 |
| txt_code | TextField | 驗證碼輸入（6位數） |
| btn_verify | Button | 驗證按鈕 |
| btn_resend | Button | 重新發送 |
| btn_back | Button | 返回 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_verify | 驗證 | Button | SCR-HOME-001-main | 驗證成功 |
| btn_resend | 重新發送 | Button | (current) | 顯示倒數計時 |
| btn_back | 返回 | Button | history.back() | - |

---

### SCR-AUTH-006-reset-sent: 重設郵件已發送

**必要性：** 選配

**畫面說明：**
密碼重設郵件發送成功的確認頁面。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| icon_success | Image | 成功圖示 |
| lbl_title | Text | 郵件已發送 |
| lbl_instruction | Text | 請檢查您的信箱 |
| btn_login | Button | 返回登入 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_login | 返回登入 | Button | SCR-AUTH-002-login | - |

---

### SCR-AUTH-007-role: 角色選擇

**必要性：** 選配（多角色 App 使用）

**畫面說明：**
登入後選擇使用角色（如：學生/家長、買家/賣家）。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| lbl_title | Text | 請選擇您的身份 |
| btn_role_1 | Button | 角色 1（如：學生） |
| btn_role_2 | Button | 角色 2（如：家長） |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_role_1 | 學生 | Button | SCR-HOME-001-student | - |
| btn_role_2 | 家長 | Button | SCR-HOME-001-parent | 可能需要 PIN |

---

### SCR-AUTH-008-pin: PIN 碼驗證

**必要性：** 選配（家長控制或管理員功能）

**畫面說明：**
PIN 碼驗證頁面，用於保護敏感功能。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| lbl_title | Text | 請輸入 PIN 碼 |
| txt_pin | SecureField | 4-6 位數 PIN |
| btn_verify | Button | 確認 |
| btn_cancel | Button | 取消 |
| lnk_forgot | Link | 忘記 PIN？ |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_verify | 確認 | Button | (目標畫面) | PIN 正確 |
| btn_cancel | 取消 | Button | history.back() | - |
| lnk_forgot | 忘記 PIN？ | Link | (重設流程) | - |

---

## 參考來源

本模板基於 VocabMaster 專案的 AUTH 模組設計，經過驗證可支援：
- Email/密碼登入
- Apple ID 登入
- Google 登入（選配）
- 多角色切換
- 家長 PIN 保護
