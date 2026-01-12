# 社群類 App 追加需求 (REQ-SOCIAL-*)

本文件定義社群類 App 的追加需求模組，與 `standard-app-requirements.md` 配合使用。
適用於：社群平台、即時通訊、內容分享、社交網絡等 App 類型。

---

## 觸發關鍵字

當用戶描述中包含以下關鍵字時，自動載入本需求模組：

- 社群、社交、交友
- 好友、追蹤、關注
- 貼文、發文、動態
- 聊天、訊息、私訊
- 按讚、留言、分享

---

## 用戶關係模組 (REQ-SOCIAL-RELATION-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-RELATION-001 | 好友搜尋 | 透過名稱/ID 搜尋其他用戶 | P0 |
| REQ-SOCIAL-RELATION-002 | 好友請求 | 發送好友請求 | P0 |
| REQ-SOCIAL-RELATION-003 | 好友接受/拒絕 | 接受或拒絕好友請求 | P0 |
| REQ-SOCIAL-RELATION-004 | 好友列表 | 查看好友列表 | P0 |
| REQ-SOCIAL-RELATION-005 | 追蹤/取消追蹤 | 追蹤或取消追蹤用戶 | P1 |
| REQ-SOCIAL-RELATION-006 | 封鎖用戶 | 封鎖/解除封鎖用戶 | P1 |
| REQ-SOCIAL-RELATION-007 | 用戶推薦 | 推薦可能認識的用戶 | P2 |
| REQ-SOCIAL-RELATION-008 | 用戶標籤 | 為好友設定標籤/分組 | P2 |

---

## 內容發布模組 (REQ-SOCIAL-POST-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-POST-001 | 發布貼文 | 發布文字貼文 | P0 |
| REQ-SOCIAL-POST-002 | 圖片貼文 | 貼文附加圖片 | P0 |
| REQ-SOCIAL-POST-003 | 影片貼文 | 貼文附加影片 | P1 |
| REQ-SOCIAL-POST-004 | 編輯貼文 | 編輯已發布的貼文 | P1 |
| REQ-SOCIAL-POST-005 | 刪除貼文 | 刪除已發布的貼文 | P0 |
| REQ-SOCIAL-POST-006 | 隱私設定 | 設定貼文可見範圍（公開/好友/私密） | P1 |
| REQ-SOCIAL-POST-007 | 標記好友 | 在貼文中標記好友 | P1 |
| REQ-SOCIAL-POST-008 | 打卡定位 | 貼文附加地點資訊 | P2 |

---

## 動態牆模組 (REQ-SOCIAL-FEED-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-FEED-001 | 動態牆 | 顯示好友/追蹤者的貼文 | P0 |
| REQ-SOCIAL-FEED-002 | 按讚 | 對貼文按讚/取消讚 | P0 |
| REQ-SOCIAL-FEED-003 | 留言 | 對貼文發表留言 | P0 |
| REQ-SOCIAL-FEED-004 | 分享 | 分享貼文 | P1 |
| REQ-SOCIAL-FEED-005 | 下拉更新 | 下拉刷新動態牆 | P0 |
| REQ-SOCIAL-FEED-006 | 無限捲動 | 向下捲動載入更多內容 | P0 |
| REQ-SOCIAL-FEED-007 | 內容篩選 | 依類型/來源篩選動態 | P2 |
| REQ-SOCIAL-FEED-008 | 檢舉內容 | 檢舉不當內容 | P1 |

---

## 即時通訊模組 (REQ-SOCIAL-CHAT-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-CHAT-001 | 私訊對話 | 與好友私訊聊天 | P0 |
| REQ-SOCIAL-CHAT-002 | 訊息列表 | 查看所有對話列表 | P0 |
| REQ-SOCIAL-CHAT-003 | 文字訊息 | 發送文字訊息 | P0 |
| REQ-SOCIAL-CHAT-004 | 圖片訊息 | 發送圖片訊息 | P0 |
| REQ-SOCIAL-CHAT-005 | 語音訊息 | 發送語音訊息 | P1 |
| REQ-SOCIAL-CHAT-006 | 已讀狀態 | 顯示訊息已讀狀態 | P1 |
| REQ-SOCIAL-CHAT-007 | 輸入中提示 | 顯示對方正在輸入 | P2 |
| REQ-SOCIAL-CHAT-008 | 群組聊天 | 建立群組聊天室 | P1 |
| REQ-SOCIAL-CHAT-009 | 訊息通知 | 新訊息推播通知 | P0 |
| REQ-SOCIAL-CHAT-010 | 訊息搜尋 | 搜尋聊天記錄 | P2 |

---

## 個人主頁模組 (REQ-SOCIAL-PROFILE-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-PROFILE-001 | 個人主頁 | 查看個人/他人主頁 | P0 |
| REQ-SOCIAL-PROFILE-002 | 貼文歷史 | 在主頁查看貼文歷史 | P0 |
| REQ-SOCIAL-PROFILE-003 | 相片集 | 查看用戶相片集 | P1 |
| REQ-SOCIAL-PROFILE-004 | 好友數顯示 | 顯示好友/追蹤者數量 | P1 |
| REQ-SOCIAL-PROFILE-005 | 個人簡介 | 編輯個人簡介 | P1 |
| REQ-SOCIAL-PROFILE-006 | 封面照片 | 設定個人主頁封面 | P2 |

---

## 互動通知模組 (REQ-SOCIAL-NOTIFY-*)

| ID | 需求 | 描述 | 優先級 |
|----|------|------|--------|
| REQ-SOCIAL-NOTIFY-001 | 互動通知 | 按讚、留言、分享通知 | P0 |
| REQ-SOCIAL-NOTIFY-002 | 好友請求通知 | 新好友請求通知 | P0 |
| REQ-SOCIAL-NOTIFY-003 | 標記通知 | 被標記時通知 | P1 |
| REQ-SOCIAL-NOTIFY-004 | 通知設定 | 自訂通知類型開關 | P1 |
| REQ-SOCIAL-NOTIFY-005 | 靜音功能 | 靜音特定用戶/對話 | P2 |

---

## 需求數量估算

| 模組 | P0 | P1 | P2 | 小計 |
|------|----|----|----|----|
| 用戶關係 | 4 | 2 | 2 | 8 |
| 內容發布 | 3 | 4 | 1 | 8 |
| 動態牆 | 4 | 2 | 2 | 8 |
| 即時通訊 | 5 | 3 | 2 | 10 |
| 個人主頁 | 2 | 3 | 1 | 6 |
| 互動通知 | 2 | 2 | 1 | 5 |
| **總計** | **20** | **16** | **9** | **45** |

加上 `standard-app-requirements.md` 的通用需求（約 40-60 個），
社群類 App 總需求預估：**85-105 個需求**

---

## 畫面清單預估 (SCR-SOCIAL-*)

| 畫面類型 | 預估數量 | 說明 |
|----------|---------|------|
| 動態牆 | 2-3 | 主動態、好友動態 |
| 貼文相關 | 3-4 | 發布、詳情、留言 |
| 聊天功能 | 4-6 | 列表、對話、群組 |
| 個人主頁 | 3-4 | 主頁、編輯、相簿 |
| 好友管理 | 3-4 | 列表、搜尋、請求 |
| 通知中心 | 1-2 | 通知列表、設定 |
| **總計** | **16-23** | |

---

## 技術考量

### 即時通訊
- WebSocket / Socket.IO
- Firebase Realtime Database
- Apple Push Notification Service (APNs)

### 內容儲存
- 圖片/影片: AWS S3 / CloudKit
- 快取策略: 圖片 CDN + 本地快取

### 安全考量
- 端對端加密（聊天訊息）
- 內容審核機制
- 隱私設定控管
