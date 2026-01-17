# COMMON 狀態模組模板 (Common States Module Template)

共用狀態畫面的標準定義，**所有 App 必須包含**這些狀態畫面以提供完整的用戶體驗。

---

## 模組概述

| 項目 | 值 |
|------|-----|
| 模組代碼 | COMMON |
| 必要性 | **必要** |
| 最少畫面數 | 4 |
| 完整畫面數 | 5 |
| 相關需求 | REQ-COMMON-* |

---

## 標準畫面清單

| 畫面 ID | 名稱 | 必要性 | 優先級 | 用途 |
|---------|------|--------|--------|------|
| SCR-COMMON-001-loading | 載入中狀態 | **必要** | P0 | API 呼叫等待 |
| SCR-COMMON-002-empty | 空狀態 | **必要** | P0 | 無資料時顯示 |
| SCR-COMMON-003-error | 錯誤狀態 | **必要** | P0 | 操作失敗 |
| SCR-COMMON-004-no-network | 無網路狀態 | **必要** | P0 | 離線時顯示 |
| SCR-COMMON-005-confirm | 確認對話框 | 選配 | P1 | 重要操作確認 |

---

## 畫面詳細設計

### SCR-COMMON-001-loading: 載入中狀態 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
顯示於 API 呼叫或資料載入期間，提供視覺回饋讓用戶知道系統正在處理。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| spinner | ActivityIndicator | 旋轉載入動畫 |
| lbl_message | Text | 載入提示文字（選配） |
| progress_bar | ProgressBar | 進度條（選配） |

**設計規範：**

| 項目 | 規範 |
|------|------|
| 背景 | 半透明遮罩或全螢幕 |
| 動畫 | 旋轉或脈衝效果 |
| 提示文字 | 「載入中...」或具體說明 |
| 超時處理 | 超過 10 秒顯示重試選項 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_cancel | 取消 | Button | history.back() | 可取消的操作 |

**CSS 動畫範例：**

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

---

### SCR-COMMON-002-empty: 空狀態 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
當列表或內容區域沒有資料時顯示，引導用戶採取行動。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_illustration | Image | 空狀態插圖 |
| lbl_title | Text | 標題（如「尚無資料」） |
| lbl_description | Text | 說明文字 |
| btn_action | Button | 主要行動按鈕 |

**設計規範：**

| 項目 | 規範 |
|------|------|
| 插圖 | 友善、輕量的 SVG 插圖 |
| 標題 | 簡潔說明目前狀態 |
| 說明 | 引導用戶下一步 |
| 按鈕 | 提供解決方案（如「新增」） |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_action | 新增 | Button | (新增畫面) | 根據內容類型 |
| btn_refresh | 重新整理 | Button | (current) | 刷新列表 |

**空狀態文案範例：**

| 場景 | 標題 | 說明 | 按鈕 |
|------|------|------|------|
| 字庫列表 | 尚無字庫 | 建立您的第一個字庫開始學習 | 新增字庫 |
| 好友列表 | 還沒有好友 | 邀請好友一起學習 | 邀請好友 |
| 搜尋結果 | 找不到結果 | 試試其他關鍵字 | 清除搜尋 |
| 通知列表 | 沒有通知 | 有新消息時會在這裡顯示 | - |

---

### SCR-COMMON-003-error: 錯誤狀態 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
當操作失敗或發生錯誤時顯示，提供重試或回報選項。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_error | Image | 錯誤插圖 |
| lbl_title | Text | 錯誤標題 |
| lbl_message | Text | 錯誤說明 |
| btn_retry | Button | 重試按鈕 |
| btn_back | Button | 返回按鈕 |
| lnk_report | Link | 回報問題（選配） |

**設計規範：**

| 項目 | 規範 |
|------|------|
| 插圖 | 友善但能傳達問題的圖示 |
| 標題 | 不要只說「錯誤」，要說明發生什麼 |
| 說明 | 提供可能的解決方案 |
| 按鈕 | 重試或返回 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_retry | 重試 | Button | (current) | 重新執行操作 |
| btn_back | 返回 | Button | history.back() | - |
| lnk_report | 回報問題 | Link | SCR-SETTING-012-feedback | - |

**錯誤類型與文案：**

| 錯誤類型 | 標題 | 說明 |
|----------|------|------|
| 伺服器錯誤 | 系統暫時無法使用 | 請稍後再試 |
| 權限不足 | 無法存取此內容 | 請確認您的帳戶權限 |
| 驗證失敗 | 操作無法完成 | 請重新登入後再試 |
| 未知錯誤 | 發生了一些問題 | 請重試或聯繫客服 |

---

### SCR-COMMON-004-no-network: 無網路狀態 ⚠️ 必要

**必要性：** **必要**

**畫面說明：**
當裝置離線或網路連線中斷時顯示。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| img_offline | Image | 離線插圖（雲朵+叉叉） |
| lbl_title | Text | 「網路連線中斷」 |
| lbl_message | Text | 說明文字 |
| btn_retry | Button | 重試連線 |
| lbl_offline_mode | Text | 離線模式說明（選配） |

**設計規範：**

| 項目 | 規範 |
|------|------|
| 插圖 | 清楚傳達網路問題 |
| 離線功能 | 說明哪些功能可離線使用 |
| 重試 | 提供重試按鈕 |
| 自動偵測 | 網路恢復時自動刷新 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_retry | 重試連線 | Button | (current) | 檢查網路後重試 |
| btn_offline | 離線模式 | Button | (離線首頁) | 支援離線功能時 |

---

### SCR-COMMON-005-confirm: 確認對話框

**必要性：** 選配（建議包含）

**畫面說明：**
重要操作前的確認對話框，如刪除、登出等。

**UI 元件：**

| 元件 | 類型 | 說明 |
|------|------|------|
| lbl_title | Text | 確認標題 |
| lbl_message | Text | 確認說明 |
| btn_confirm | Button | 確認按鈕（危險操作用紅色） |
| btn_cancel | Button | 取消按鈕 |

**設計規範：**

| 項目 | 規範 |
|------|------|
| 標題 | 清楚說明要確認的操作 |
| 說明 | 提醒操作後果 |
| 按鈕順序 | 取消在左，確認在右 |
| 危險操作 | 確認按鈕使用紅色 |

**Button Navigation：**

| Element ID | Element Text | Type | Target Screen | Condition |
|------------|--------------|------|---------------|-----------|
| btn_confirm | 確認 | Button | (執行後目標) | 操作完成 |
| btn_cancel | 取消 | Button | (close modal) | - |

**常見確認場景：**

| 場景 | 標題 | 說明 | 確認按鈕 |
|------|------|------|----------|
| 刪除項目 | 確定要刪除嗎？ | 此操作無法復原 | 刪除（紅） |
| 登出 | 確定要登出嗎？ | 您需要重新登入 | 登出 |
| 取消編輯 | 放棄變更？ | 未儲存的變更將會遺失 | 放棄 |
| 購買確認 | 確認購買？ | 將扣除 XX 金幣 | 確認購買 |

---

## 狀態畫面使用指南

### 使用時機

| 狀態 | 使用時機 |
|------|----------|
| Loading | API 呼叫、資料載入、檔案上傳 |
| Empty | 列表為空、搜尋無結果、首次使用 |
| Error | API 錯誤、操作失敗、驗證失敗 |
| No Network | 網路中斷、離線狀態 |
| Confirm | 刪除、登出、不可逆操作 |

### 設計原則

1. **友善語氣** - 不要責怪用戶
2. **清楚說明** - 告訴用戶發生什麼
3. **提供出路** - 給用戶下一步行動
4. **一致風格** - 所有狀態畫面風格一致

---

## 參考來源

本模板基於 VocabMaster 專案的 COMMON 模組設計，符合 iOS Human Interface Guidelines 和 Material Design 3 的狀態畫面規範。
