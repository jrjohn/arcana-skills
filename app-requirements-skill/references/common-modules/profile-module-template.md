# PROFILE 模組模板 (Profile Module Template)

個人檔案模組的標準畫面定義，適用於所有需要用戶資料管理的 App。

---

## 模組概述

| 項目 | 值 |
|------|-----|
| 模組代碼 | PROFILE |
| 必要性 | **必要** |
| 最少畫面數 | 2 |
| 完整畫面數 | 3 |
| 相關需求 | REQ-PROFILE-* |

---

## 標準畫面清單

| 畫面 ID | 名稱 | 必要性 | 優先級 | 說明 |
|---------|------|--------|--------|------|
| SCR-PROFILE-001-view | 個人檔案查看 | **必要** | P0 | 顯示用戶資料 |
| SCR-PROFILE-002-edit | 個人檔案編輯 | **必要** | P0 | 編輯用戶資料 |
| SCR-PROFILE-003-avatar | 頭像選擇 | 選配 | P1 | 更換頭像 |

---

## 畫面詳細設計

### SCR-PROFILE-001-view: 個人檔案查看 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
顯示用戶的個人資料，包含頭像、名稱、基本資訊等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_avatar | Image | 用戶頭像 |
| lbl_name | Text | 用戶名稱 |
| lbl_email | Text | Email（可隱藏部分） |
| lbl_join_date | Text | 加入日期 |
| section_stats | Section | 統計資訊區塊 |
| btn_edit | Button | 編輯按鈕 |
| btn_back | Button | 返回按鈕 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_edit | 編輯 | Button | SCR-PROFILE-002-edit | - |
| btn_back | 返回 | Button | history.back() | - |
| img_avatar | (點擊頭像) | Image | SCR-PROFILE-003-avatar | - |

---

### SCR-PROFILE-002-edit: 個人檔案編輯 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
編輯用戶的個人資料，包含名稱、頭像、偏好設定等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_avatar | Image | 用戶頭像（可點擊更換） |
| btn_change_avatar | Button | 更換頭像按鈕 |
| txt_name | TextField | 名稱輸入框 |
| txt_nickname | TextField | 暱稱輸入框（選配） |
| txt_bio | TextArea | 自我介紹（選配） |
| picker_birthday | DatePicker | 生日選擇（選配） |
| picker_gender | Picker | 性別選擇（選配） |
| btn_save | Button | 儲存按鈕 |
| btn_cancel | Button | 取消按鈕 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_change_avatar | 更換頭像 | Button | SCR-PROFILE-003-avatar | - |
| btn_save | 儲存 | Button | SCR-PROFILE-001-view | 儲存成功 |
| btn_cancel | 取消 | Button | history.back() | - |

---

### SCR-PROFILE-003-avatar: 頭像選擇

**必要性：** 選配

**畫面說明：**
選擇或上傳用戶頭像。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_current | Image | 目前頭像 |
| grid_presets | Grid | 預設頭像選項 |
| btn_camera | Button | 拍照 |
| btn_gallery | Button | 從相簿選擇 |
| btn_save | Button | 確認選擇 |
| btn_cancel | Button | 取消 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_camera | 拍照 | Button | (系統相機) | - |
| btn_gallery | 從相簿選擇 | Button | (系統相簿) | - |
| btn_save | 確認 | Button | history.back() | 頭像已更新 |
| btn_cancel | 取消 | Button | history.back() | - |

---

## 擴展畫面（選配）

根據 App 類型可擴展以下畫面：

| 畫面 ID | 名稱 | 適用場景 |
|---------|------|----------|
| SCR-PROFILE-004-settings | 個人偏好設定 | 學習類 App |
| SCR-PROFILE-005-security | 安全設定 | 金融/醫療類 App |
| SCR-PROFILE-006-badges | 成就徽章 | 遊戲化 App |
| SCR-PROFILE-007-history | 活動歷史 | 電商/社群 App |

---

## 參考來源

本模板基於 VocabMaster 專案的 PROFILE 模組設計。
