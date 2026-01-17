# SETTING 模組模板 (Setting Module Template)

設定模組的標準畫面定義，提供完整的系統設定功能架構。

---

## 模組概述

| 項目 | 值 |
|------|-----|
| 模組代碼 | SETTING |
| 必要性 | **必要** |
| 最少畫面數 | 4 |
| 完整畫面數 | 18 |
| 相關需求 | REQ-SETTING-* |

---

## 標準畫面清單

### 必要畫面（4 個）

| 畫面 ID | 名稱 | 必要性 | 優先級 |
|---------|------|--------|--------|
| SCR-SETTING-001-main | 設定主頁 | **必要** | P0 |
| SCR-SETTING-002-account | 帳戶設定 | **必要** | P0 |
| SCR-SETTING-003-privacy | 隱私設定 | **必要** | P0 |
| SCR-SETTING-004-about | 關於 | **必要** | P0 |

### 選配畫面（14 個）

| 畫面 ID | 名稱 | 必要性 | 優先級 | 說明 |
|---------|------|--------|--------|------|
| SCR-SETTING-005-notification | 通知設定 | 選配 | P1 | 推播通知偏好 |
| SCR-SETTING-006-language | 語言設定 | 選配 | P1 | 多語系支援 |
| SCR-SETTING-007-theme | 主題設定 | 選配 | P1 | 明亮/深色模式 |
| SCR-SETTING-008-sound | 音效設定 | 選配 | P2 | 音效/音量控制 |
| SCR-SETTING-009-display | 顯示設定 | 選配 | P2 | 字體大小等 |
| SCR-SETTING-010-sync | 同步設定 | 選配 | P1 | 雲端同步選項 |
| SCR-SETTING-011-help | 幫助中心 | 選配 | P1 | FAQ/客服 |
| SCR-SETTING-012-feedback | 意見回饋 | 選配 | P2 | 用戶反饋 |
| SCR-SETTING-013-terms | 使用條款 | 選配 | P1 | 法律文件 |
| SCR-SETTING-014-privacy-policy | 隱私政策 | 選配 | P1 | 法律文件 |
| SCR-SETTING-015-licenses | 授權資訊 | 選配 | P2 | 開源授權 |
| SCR-SETTING-016-password | 密碼變更 | 選配 | P1 | 密碼修改 |
| SCR-SETTING-017-delete-account | 刪除帳戶 | 選配 | P1 | 帳戶刪除 |
| SCR-SETTING-018-logout-confirm | 登出確認 | 選配 | P1 | 登出對話框 |

---

## 畫面詳細設計

### SCR-SETTING-001-main: 設定主頁 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
設定功能的入口頁面，以分組方式呈現所有設定選項。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| header | Header | 標題「設定」 |
| section_account | Section | 帳戶區塊 |
| cell_profile | Cell | 個人檔案 |
| cell_account | Cell | 帳戶設定 |
| section_preferences | Section | 偏好設定區塊 |
| cell_notification | Cell | 通知設定 |
| cell_language | Cell | 語言設定 |
| cell_theme | Cell | 主題設定 |
| section_support | Section | 支援區塊 |
| cell_help | Cell | 幫助中心 |
| cell_feedback | Cell | 意見回饋 |
| section_about | Section | 關於區塊 |
| cell_about | Cell | 關於 |
| cell_terms | Cell | 使用條款 |
| cell_privacy | Cell | 隱私政策 |
| btn_logout | Button | 登出按鈕 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_profile | 個人檔案 | Cell | SCR-PROFILE-001-view | - |
| cell_account | 帳戶設定 | Cell | SCR-SETTING-002-account | - |
| cell_notification | 通知設定 | Cell | SCR-SETTING-005-notification | - |
| cell_language | 語言設定 | Cell | SCR-SETTING-006-language | - |
| cell_theme | 主題設定 | Cell | SCR-SETTING-007-theme | - |
| cell_help | 幫助中心 | Cell | SCR-SETTING-011-help | - |
| cell_feedback | 意見回饋 | Cell | SCR-SETTING-012-feedback | - |
| cell_about | 關於 | Cell | SCR-SETTING-004-about | - |
| cell_terms | 使用條款 | Cell | SCR-SETTING-013-terms | - |
| cell_privacy | 隱私政策 | Cell | SCR-SETTING-014-privacy-policy | - |
| btn_logout | 登出 | Button | SCR-SETTING-018-logout-confirm | - |

---

### SCR-SETTING-002-account: 帳戶設定 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
帳戶相關設定，包含 Email、密碼、連結帳號等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| cell_email | Cell | Email（顯示目前 Email） |
| cell_password | Cell | 密碼變更 |
| cell_linked_accounts | Cell | 已連結帳號 |
| cell_delete_account | Cell | 刪除帳戶 |
| btn_back | Button | 返回 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_password | 密碼變更 | Cell | SCR-SETTING-016-password | - |
| cell_delete_account | 刪除帳戶 | Cell | SCR-SETTING-017-delete-account | - |
| btn_back | 返回 | Button | history.back() | - |

---

### SCR-SETTING-003-privacy: 隱私設定 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
隱私相關設定，包含資料分享、追蹤、可見性等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| toggle_analytics | Toggle | 分析數據收集 |
| toggle_personalization | Toggle | 個人化推薦 |
| toggle_profile_visibility | Toggle | 公開個人檔案 |
| cell_data_download | Cell | 下載我的資料 |
| cell_privacy_policy | Cell | 隱私政策 |
| btn_back | Button | 返回 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_privacy_policy | 隱私政策 | Cell | SCR-SETTING-014-privacy-policy | - |
| btn_back | 返回 | Button | history.back() | - |

---

### SCR-SETTING-004-about: 關於 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
App 資訊頁面，包含版本號、開發團隊、法律資訊等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_logo | Image | App Logo |
| lbl_app_name | Text | App 名稱 |
| lbl_version | Text | 版本號 |
| cell_terms | Cell | 使用條款 |
| cell_privacy | Cell | 隱私政策 |
| cell_licenses | Cell | 授權資訊 |
| lbl_copyright | Text | 版權聲明 |
| btn_back | Button | 返回 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| cell_terms | 使用條款 | Cell | SCR-SETTING-013-terms | - |
| cell_privacy | 隱私政策 | Cell | SCR-SETTING-014-privacy-policy | - |
| cell_licenses | 授權資訊 | Cell | SCR-SETTING-015-licenses | - |
| btn_back | 返回 | Button | history.back() | - |

---

## 設定分組建議

### 標準分組結構

```
設定主頁
├── 👤 帳戶
│   ├── 個人檔案
│   └── 帳戶設定
├── ⚙️ 偏好設定
│   ├── 通知設定
│   ├── 語言設定
│   ├── 主題設定
│   └── 音效設定
├── 🔒 隱私與安全
│   ├── 隱私設定
│   └── 安全設定
├── ❓ 支援
│   ├── 幫助中心
│   └── 意見回饋
├── ℹ️ 關於
│   ├── 關於
│   ├── 使用條款
│   └── 隱私政策
└── 🚪 登出
```

---

## App 類型特定設定

| App 類型 | 建議增加的設定 |
|----------|----------------|
| 教育類 | 學習提醒、每日目標、語音語速 |
| 電商類 | 付款方式、收貨地址、訂單通知 |
| 社群類 | 誰可以看我、封鎖名單、標記設定 |
| 醫療類 | 健康資料同步、緊急聯絡人、資料加密 |
| 生產力類 | 同步設定、備份設定、快捷鍵 |

---

## 參考來源

本模板基於 VocabMaster 專案的 SETTING 模組設計（18 個畫面）。
