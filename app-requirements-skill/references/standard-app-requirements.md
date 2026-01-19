# 標準 App 功能需求清單

本文件提供業界標準 App 功能需求清單，供需求分析時參考，確保不遺漏基礎功能。

---

## Quick Reference - 需求估算

### 標準 App 基礎需求數量

| 模組 | 需求數量 | 必要性 |
|------|----------|--------|
| 認證 (AUTH) | 8-12 | ★★★ |
| 個人檔案 (PROFILE) | 4-6 | ★★★ |
| 設定 (SETTING) | 6-10 | ★★★ |
| Onboarding | 2-4 | ★★☆ |
| 通知 | 3-5 | ★★☆ |
| 幫助支援 | 3-5 | ★☆☆ |
| 法律合規 | 2-3 | ★★★ |
| 非功能需求 | 8-15 | ★★★ |
| **基礎總計** | **36-60** | - |

### App 類型追加需求

| App 類型 | 追加需求 | 說明 |
|----------|----------|------|
| 電商類 | +30~50 | 購物車、結帳、訂單、支付 |
| 社群類 | +20~40 | 好友、貼文、互動、訊息 |
| 內容類 | +15~25 | 瀏覽、收藏、搜尋、推薦 |
| 預約類 | +15~30 | 預約、行事曆、提醒 |
| 工具類 | +10~20 | 核心功能 (依 App) |

---

## 1. 認證需求 (REQ-AUTH-*)

### 1.1 基本認證

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-AUTH-001 | 用戶登入 | 使用 Email/密碼登入系統 | P0 |
| REQ-AUTH-002 | 用戶註冊 | 建立新帳號 (Email, 密碼, 基本資料) | P0 |
| REQ-AUTH-003 | 忘記密碼 | 透過 Email 發送密碼重設連結 | P0 |
| REQ-AUTH-004 | 密碼重設 | 透過連結設定新密碼 | P0 |
| REQ-AUTH-005 | Email 驗證 | 驗證用戶 Email 真實性 | P1 |
| REQ-AUTH-006 | 登出 | 結束登入 Session | P0 |
| REQ-AUTH-007 | Session 管理 | Token 過期、自動登出、保持登入 | P0 |

### 1.2 社群登入

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-AUTH-010 | Apple Sign-In | iOS App Store 強制要求 (若有其他社群登入) | P0 (iOS) |
| REQ-AUTH-011 | Google Sign-In | Google 帳號登入 | P1 |
| REQ-AUTH-012 | Facebook Login | Facebook 帳號登入 | P2 |
| REQ-AUTH-013 | LINE Login | LINE 帳號登入 (台灣市場) | P2 |

> ⚠️ **iOS App Store 規定**: 若提供任何第三方登入，必須同時提供 Sign in with Apple

### 1.3 進階認證

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-AUTH-020 | 生物辨識登入 | Face ID / Touch ID / 指紋辨識快速登入 | P1 |
| REQ-AUTH-021 | 雙重驗證 (MFA) | SMS OTP / Email OTP / Authenticator App | P1 |
| REQ-AUTH-022 | 備用碼 | MFA 備用驗證碼 | P2 |
| REQ-AUTH-023 | App 鎖定 | 開啟 App 需驗證身份 | P2 |
| REQ-AUTH-024 | 登入裝置管理 | 查看/登出已登入裝置 | P2 |
| REQ-AUTH-025 | 登入記錄 | 登入歷史紀錄 (時間、裝置、位置) | P3 |

### 1.4 驗收標準 (ACC)

```markdown
REQ-AUTH-001 用戶登入:
- ACC-001: 輸入正確 Email/密碼後成功登入並跳轉至首頁
- ACC-002: 輸入錯誤密碼顯示錯誤提示並保留 Email 欄位內容
- ACC-003: 帳號不存在時顯示 "此帳號尚未註冊" 錯誤
- ACC-004: 密碼輸入框支援顯示/隱藏切換
- ACC-005: 5 次連續失敗後鎖定帳號 15 分鐘

REQ-AUTH-002 用戶註冊:
- ACC-001: 填寫必填欄位後成功建立帳號
- ACC-002: Email 格式錯誤時即時顯示驗證錯誤
- ACC-003: 密碼強度不足時顯示提示並禁止送出
- ACC-004: Email 已存在時顯示 "此 Email 已註冊"
- ACC-005: 同意服務條款勾選後才可送出
```

---

## 2. 個人檔案需求 (REQ-PROFILE-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-PROFILE-001 | 查看個人資料 | 顯示用戶基本資料 | P0 |
| REQ-PROFILE-002 | 編輯個人資料 | 修改名稱、電話等可編輯欄位 | P0 |
| REQ-PROFILE-003 | 上傳頭像 | 從相簿選擇或拍照上傳頭像 | P1 |
| REQ-PROFILE-004 | 頭像裁切 | 裁切、縮放頭像圖片 | P2 |
| REQ-PROFILE-005 | 變更 Email | 修改登入 Email (需驗證) | P1 |
| REQ-PROFILE-006 | 變更密碼 | 修改登入密碼 | P0 |
| REQ-PROFILE-007 | 刪除帳號 | 永久刪除帳號及所有資料 | P1 |

### 2.1 驗收標準 (ACC)

```markdown
REQ-PROFILE-002 編輯個人資料:
- ACC-001: 修改名稱後儲存成功並顯示更新後資料
- ACC-002: 必填欄位為空時顯示錯誤提示
- ACC-003: 欄位長度超過限制時顯示錯誤
- ACC-004: 儲存成功後顯示成功提示

REQ-PROFILE-007 刪除帳號:
- ACC-001: 刪除前顯示確認對話框
- ACC-002: 需輸入密碼確認身份
- ACC-003: 刪除後清除本地資料並跳轉至登入頁
- ACC-004: 刪除後 30 天內可聯繫客服恢復 (可選)
```

---

## 3. 設定需求 (REQ-SETTING-*)

### 3.1 通知設定

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-SETTING-001 | 推播通知總開關 | 啟用/停用所有推播通知 | P0 |
| REQ-SETTING-002 | 通知類型設定 | 分類設定各類通知開關 | P1 |
| REQ-SETTING-003 | 免打擾時段 | 設定夜間免打擾時段 | P2 |
| REQ-SETTING-004 | Email 通知 | 設定 Email 通知偏好 | P2 |

### 3.2 隱私設定

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-SETTING-010 | 個人檔案可見性 | 設定個人資料公開範圍 | P2 |
| REQ-SETTING-011 | 資料收集同意 | 分析資料收集偏好設定 | P1 |
| REQ-SETTING-012 | 廣告追蹤設定 | 個人化廣告偏好 | P2 |
| REQ-SETTING-013 | 下載我的資料 | GDPR 要求 - 匯出個人資料 | P1 |
| REQ-SETTING-014 | 封鎖名單管理 | 查看/解除封鎖用戶 (社群類) | P2 |

### 3.3 外觀設定

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-SETTING-020 | 主題切換 | 淺色/深色/跟隨系統 | P1 |
| REQ-SETTING-021 | 文字大小 | 調整 App 文字大小 | P2 |
| REQ-SETTING-022 | 語言設定 | 切換 App 介面語言 | P1 |

### 3.4 帳號安全

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-SETTING-030 | 變更密碼 | 同 REQ-PROFILE-006 | P0 |
| REQ-SETTING-031 | 雙重驗證管理 | 啟用/停用/管理 MFA | P1 |
| REQ-SETTING-032 | 生物辨識設定 | 啟用/停用 Face ID/Touch ID | P1 |
| REQ-SETTING-033 | App 鎖定設定 | 設定 App 開啟驗證 | P2 |

---

## 4. Onboarding 需求 (REQ-ONBOARD-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-ONBOARD-001 | 歡迎畫面 | 首次使用顯示功能介紹 (3-5 頁) | P1 |
| REQ-ONBOARD-002 | 跳過 Onboarding | 允許跳過介紹直接進入 | P1 |
| REQ-ONBOARD-003 | 權限請求說明 | 請求權限前說明用途 | P0 |
| REQ-ONBOARD-004 | 個人化設定 | 首次設定偏好 (可選) | P2 |

### 4.1 權限請求

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-ONBOARD-010 | 通知權限請求 | 請求推播通知權限 | P0 |
| REQ-ONBOARD-011 | 位置權限請求 | 請求位置存取權限 (若需要) | P1 |
| REQ-ONBOARD-012 | 相機權限請求 | 請求相機存取權限 (若需要) | P1 |
| REQ-ONBOARD-013 | 相簿權限請求 | 請求相簿存取權限 (若需要) | P1 |
| REQ-ONBOARD-014 | 追蹤權限請求 | ATT 權限 (iOS 14.5+) | P0 (iOS) |

> ⚠️ **iOS App Tracking Transparency (ATT)**: iOS 14.5+ 需請求追蹤權限才能使用 IDFA

---

## 5. 通知需求 (REQ-NOTIFY-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-NOTIFY-001 | 通知列表 | 顯示所有通知記錄 | P1 |
| REQ-NOTIFY-002 | 未讀標記 | 區分已讀/未讀通知 | P1 |
| REQ-NOTIFY-003 | 全部已讀 | 一鍵標記所有通知為已讀 | P2 |
| REQ-NOTIFY-004 | 刪除通知 | 刪除單一或多筆通知 | P2 |
| REQ-NOTIFY-005 | 通知分類 | 按類型分類顯示通知 | P3 |
| REQ-NOTIFY-006 | 通知 Badge | App Icon 顯示未讀數量 | P1 |

---

## 6. 幫助支援需求 (REQ-HELP-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-HELP-001 | 幫助中心 | 常見問題分類入口 | P1 |
| REQ-HELP-002 | FAQ 搜尋 | 搜尋常見問題 | P2 |
| REQ-HELP-003 | 聯繫客服 | 客服聯繫方式 (線上/Email/電話) | P1 |
| REQ-HELP-004 | 意見回饋 | 提交意見或問題回報 | P1 |
| REQ-HELP-005 | App 評分 | 引導至 App Store/Play Store 評分 | P2 |

---

## 7. 法律合規需求 (REQ-LEGAL-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-LEGAL-001 | 服務條款顯示 | 可查看完整服務條款 | P0 |
| REQ-LEGAL-002 | 隱私權政策顯示 | 可查看完整隱私權政策 | P0 |
| REQ-LEGAL-003 | 同意條款記錄 | 記錄用戶同意時間與版本 | P0 |
| REQ-LEGAL-004 | 條款更新通知 | 條款更新時通知用戶 | P1 |
| REQ-LEGAL-005 | Cookie 政策 | Web 版 Cookie 使用說明 | P1 (Web) |

### 7.1 GDPR/CCPA 合規 (若適用)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-LEGAL-010 | 資料攜出權 | 用戶可下載其所有資料 | P1 |
| REQ-LEGAL-011 | 被遺忘權 | 用戶可要求刪除所有資料 | P1 |
| REQ-LEGAL-012 | 資料處理同意 | 明確資料處理目的與同意機制 | P0 |
| REQ-LEGAL-013 | 撤回同意 | 用戶可隨時撤回資料處理同意 | P1 |

---

## 8. 非功能需求 (REQ-NFR-*)

### 8.1 效能需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-001 | 畫面載入時間 | 首次載入 < 3s，後續 < 2s | P0 |
| REQ-NFR-002 | API 回應時間 | 95% 請求 < 500ms | P0 |
| REQ-NFR-003 | 啟動時間 | 冷啟動 < 3s，熱啟動 < 1s | P1 |
| REQ-NFR-004 | 捲動流暢度 | 60 fps | P1 |
| REQ-NFR-005 | 記憶體使用 | 背景 < 50MB | P2 |
| REQ-NFR-006 | 電池消耗 | 背景無持續耗電 | P1 |

### 8.2 安全需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-010 | HTTPS 通訊 | 所有 API 使用 TLS 1.2+ | P0 |
| REQ-NFR-011 | Token 安全 | JWT Token 存於安全儲存 | P0 |
| REQ-NFR-012 | 密碼加密 | 伺服器端 bcrypt/Argon2 | P0 |
| REQ-NFR-013 | 敏感資料加密 | 本地敏感資料加密儲存 | P0 |
| REQ-NFR-014 | Certificate Pinning | 防止中間人攻擊 | P1 |
| REQ-NFR-015 | 防止截圖 | 敏感畫面禁止截圖 (可選) | P3 |
| REQ-NFR-016 | 越獄/Root 檢測 | 提示安全風險 | P2 |

### 8.3 可用性需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-020 | 離線模式 | 基本功能離線可用 | P1 |
| REQ-NFR-021 | 網路錯誤處理 | 友善錯誤提示 + 重試機制 | P0 |
| REQ-NFR-022 | 伺服器錯誤處理 | 友善錯誤提示 | P0 |
| REQ-NFR-023 | 載入狀態顯示 | 適當的 Loading 指示 | P0 |
| REQ-NFR-024 | 空狀態顯示 | 無資料時的引導畫面 | P1 |

### 8.4 無障礙需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-030 | VoiceOver 支援 | iOS 螢幕閱讀器支援 | P1 |
| REQ-NFR-031 | TalkBack 支援 | Android 螢幕閱讀器支援 | P1 |
| REQ-NFR-032 | 動態字型支援 | 支援系統字型大小設定 | P1 |
| REQ-NFR-033 | 色彩對比度 | WCAG 2.1 AA 標準 (4.5:1) | P1 |
| REQ-NFR-034 | 點擊區域大小 | 最小 44x44pt / 48x48dp | P1 |

### 8.5 相容性需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-040 | iOS 版本 | iOS 15.0+ (建議 14.0+) | P0 |
| REQ-NFR-041 | Android 版本 | Android 8.0+ (API 26+) | P0 |
| REQ-NFR-042 | 裝置支援 | iPhone, iPad, Android Phone/Tablet | P0 |
| REQ-NFR-043 | 螢幕適配 | 支援各種螢幕尺寸與方向 | P0 |

### 8.6 國際化需求

| REQ ID | 需求名稱 | 規格 | 優先級 |
|--------|----------|------|--------|
| REQ-NFR-050 | 多語言支援 | 繁中、簡中、英文 (依需求) | P1 |
| REQ-NFR-051 | 日期格式 | 依據語系顯示當地格式 | P1 |
| REQ-NFR-052 | 數字格式 | 依據語系顯示千分位/小數點 | P2 |
| REQ-NFR-053 | RTL 支援 | 阿拉伯文/希伯來文 (若需要) | P3 |

---

## 9. 搜尋需求 (REQ-SEARCH-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-SEARCH-001 | 基本搜尋 | 關鍵字搜尋功能 | P1 |
| REQ-SEARCH-002 | 搜尋建議 | 輸入時顯示自動完成建議 | P2 |
| REQ-SEARCH-003 | 搜尋歷史 | 記錄並顯示搜尋歷史 | P2 |
| REQ-SEARCH-004 | 熱門搜尋 | 顯示熱門搜尋關鍵字 | P3 |
| REQ-SEARCH-005 | 篩選排序 | 搜尋結果篩選與排序 | P1 |
| REQ-SEARCH-006 | 清除歷史 | 清除搜尋歷史記錄 | P2 |

---

## 10. 狀態畫面需求 (REQ-STATE-*)

| REQ ID | 需求名稱 | 說明 | 優先級 |
|--------|----------|------|--------|
| REQ-STATE-001 | Loading 狀態 | 載入中顯示 Spinner/Skeleton | P0 |
| REQ-STATE-002 | Empty 狀態 | 無資料時顯示引導畫面 | P0 |
| REQ-STATE-003 | Error 狀態 | 錯誤時顯示友善提示 + 重試 | P0 |
| REQ-STATE-004 | 網路錯誤 | 無網路時顯示離線提示 | P0 |
| REQ-STATE-005 | 伺服器錯誤 | 5xx 錯誤時顯示系統忙碌提示 | P0 |
| REQ-STATE-006 | Pull to Refresh | 下拉重新載入 | P1 |
| REQ-STATE-007 | 無限捲動 | 滾動至底部自動載入更多 | P1 |

---

## 附錄 A: 需求與畫面對應表

| REQ ID | 對應畫面 (SCR ID) |
|--------|-------------------|
| REQ-AUTH-001 | SCR-AUTH-001-login |
| REQ-AUTH-002 | SCR-AUTH-002-register |
| REQ-AUTH-003 | SCR-AUTH-003-forgot-password |
| REQ-AUTH-004 | SCR-AUTH-004-reset-password |
| REQ-AUTH-005 | SCR-AUTH-005-verify-email |
| REQ-AUTH-010 | SCR-AUTH-001-login (社群登入區塊) |
| REQ-AUTH-020 | SCR-AUTH-008-biometric |
| REQ-AUTH-021 | SCR-AUTH-006-mfa |
| REQ-PROFILE-001 | SCR-PROFILE-001-view |
| REQ-PROFILE-002 | SCR-PROFILE-002-edit |
| REQ-PROFILE-003 | SCR-PROFILE-003-avatar |
| REQ-SETTING-001~004 | SCR-SETTING-002-notifications |
| REQ-SETTING-010~014 | SCR-SETTING-003-privacy |
| REQ-SETTING-020~022 | SCR-SETTING-004-appearance |
| REQ-ONBOARD-001~002 | SCR-ONBOARD-001~003 |
| REQ-ONBOARD-010~014 | SCR-ONBOARD-004-permissions |
| REQ-NOTIFY-001~006 | SCR-NOTIFY-001-list |
| REQ-HELP-001~002 | SCR-HELP-001-center |
| REQ-HELP-003 | SCR-HELP-003-contact |
| REQ-HELP-004 | SCR-HELP-004-feedback |
| REQ-LEGAL-001 | SCR-LEGAL-001-terms |
| REQ-LEGAL-002 | SCR-LEGAL-002-privacy |
| REQ-STATE-001 | SCR-STATE-001-loading |
| REQ-STATE-002 | SCR-STATE-002-empty |
| REQ-STATE-003~005 | SCR-STATE-003-no-internet, SCR-STATE-004-server-error |

---

## 附錄 B: 優先級定義

| 優先級 | 定義 | 說明 |
|--------|------|------|
| P0 | Critical | 無此功能無法上架/使用 |
| P1 | High | 標準功能，強烈建議實作 |
| P2 | Medium | 提升使用者體驗 |
| P3 | Low | Nice to have |

---

## 附錄 C: 需求檢核清單

### C.1 上架前必備檢核

- [ ] REQ-AUTH-001~007 基本認證流程完整
- [ ] REQ-AUTH-010 Apple Sign-In (若有社群登入)
- [ ] REQ-PROFILE-001~002 個人檔案基本功能
- [ ] REQ-LEGAL-001~003 法律文件與同意記錄
- [ ] REQ-NFR-010~013 基本安全需求
- [ ] REQ-NFR-030~034 無障礙基本支援
- [ ] REQ-STATE-001~005 狀態畫面完整

### C.2 GDPR 合規檢核 (歐盟用戶)

- [ ] REQ-LEGAL-010 資料攜出權
- [ ] REQ-LEGAL-011 被遺忘權
- [ ] REQ-LEGAL-012 資料處理同意
- [ ] REQ-LEGAL-013 撤回同意
- [ ] REQ-SETTING-013 下載我的資料
- [ ] REQ-PROFILE-007 刪除帳號

### C.3 iOS App Store 審核檢核

- [ ] REQ-AUTH-010 Apple Sign-In (若有第三方登入)
- [ ] REQ-ONBOARD-014 ATT 權限請求 (若追蹤用戶)
- [ ] REQ-ONBOARD-003 權限請求說明清楚
- [ ] REQ-LEGAL-001~002 法律文件完整

---

## 附錄 D: 需求數量估算範例

### D.1 簡單工具 App

| 類別 | 需求數 |
|------|--------|
| 認證 | 8 |
| 個人檔案 | 4 |
| 設定 | 6 |
| 幫助支援 | 3 |
| 法律 | 3 |
| 非功能 | 10 |
| 核心功能 | 15 |
| **總計** | **~49** |

### D.2 標準消費 App (電商)

| 類別 | 需求數 |
|------|--------|
| 認證 | 12 |
| 個人檔案 | 6 |
| 設定 | 10 |
| Onboarding | 4 |
| 通知 | 5 |
| 幫助支援 | 5 |
| 法律 | 5 |
| 非功能 | 15 |
| 商品瀏覽 | 10 |
| 購物車 | 8 |
| 結帳支付 | 12 |
| 訂單管理 | 10 |
| **總計** | **~102** |

### D.3 社群 App

| 類別 | 需求數 |
|------|--------|
| 認證 | 12 |
| 個人檔案 | 8 |
| 設定 | 12 |
| Onboarding | 4 |
| 通知 | 6 |
| 幫助支援 | 5 |
| 法律 | 5 |
| 非功能 | 15 |
| 內容發布 | 8 |
| 社群互動 | 12 |
| 好友系統 | 8 |
| 即時訊息 | 10 |
| **總計** | **~105** |

---

## 版本記錄

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| 1.0 | 2024/01 | 初版建立 |
