# Process 02: 智慧畫面規劃 (Intelligent Screen Planning)

## 設計理念

> **目標是 100% 完成 UI/UX，透過智慧預測確保沒有遺漏任何畫面！**

---

## 進入條件

- [ ] 00-init 已完成
- [ ] 01-discovery 已完成（UI 需求已收集）
- [ ] SRS 和 SDD 文件可讀取

## 退出條件 (BLOCKING)

- [ ] **100% 畫面識別** - 所有需要的畫面都已列出
- [ ] **導航完整性** - 每個畫面的進出路徑都已定義
- [ ] **無遺漏** - 智慧預測已檢查所有可能的畫面

---

## 執行步驟

### Step 1: 讀取 SRS/SDD 定義的畫面

從 SDD 中提取所有 `SCR-*` 定義：

```bash
# 搜尋 SDD 中的 SCR-* 定義
grep -E 'SCR-[A-Z]+-[0-9]+' 02-design/SDD-*.md | sort -u
```

### Step 2: 智慧預測遺漏的畫面

> ⚠️ **關鍵步驟：根據 App 類型和標準模組預測可能遺漏的畫面**

#### 2.1 標準模組檢查表

| 模組 | 必要畫面 | 說明 |
|------|----------|------|
| **AUTH** | login, register, forgot-password, role-select | 認證流程 |
| **ONBOARD** | welcome, tutorial-1/2/3, permission | 新用戶引導 |
| **DASH/HOME** | student-home, teacher-home, parent-home | 主頁（按角色） |
| **SETTING** | main, profile, notification, privacy, about | 設定相關 |
| **COMMON** | loading, error, empty-state, success | 通用狀態畫面 |

#### 2.2 導航預測規則

分析每個畫面的按鈕，預測導航目標：

| 按鈕類型 | 預測目標畫面 |
|----------|--------------|
| 登入按鈕 | → SCR-DASH-001 或 SCR-HOME-001 |
| 註冊連結 | → SCR-AUTH-002-register |
| 忘記密碼 | → SCR-AUTH-003-forgot-password |
| 設定按鈕 | → SCR-SETTING-001-main |
| 返回按鈕 | → 上一個畫面 |
| Tab Bar 項目 | → 對應模組首頁 |

#### 2.3 自動補充遺漏畫面

```
檢查邏輯：
1. 遍歷所有 onclick 目標
2. 若目標畫面不在清單中 → 自動加入
3. 若畫面有「返回」按鈕但無來源 → 預測來源畫面
```

### Step 3: 建立完整畫面清單

輸出格式：

```json
{
  "screens": [
    {
      "id": "SCR-AUTH-001-login",
      "module": "AUTH",
      "name": "登入畫面",
      "source": "SDD",
      "navigation": {
        "from": ["SCR-AUTH-000-splash"],
        "to": ["SCR-AUTH-002-register", "SCR-AUTH-003-forgot", "SCR-DASH-001"]
      }
    },
    {
      "id": "SCR-AUTH-002-register",
      "module": "AUTH",
      "name": "註冊畫面",
      "source": "PREDICTED",
      "reason": "login 頁有註冊連結",
      "navigation": {
        "from": ["SCR-AUTH-001-login"],
        "to": ["SCR-AUTH-001-login", "SCR-DASH-001"]
      }
    }
  ],
  "stats": {
    "from_sdd": 15,
    "predicted": 10,
    "total": 25
  }
}
```

### Step 4: 驗證導航完整性

```
驗證規則：
1. 每個畫面至少有一個進入路徑（除了首頁/登入頁）
2. 每個畫面至少有一個離開路徑
3. 所有 onclick 目標都指向存在的畫面
4. 無孤立畫面（無法到達或無法離開）
```

### Step 5: 更新 workspace 狀態

```json
{
  "current_process": "02-planning",
  "status": "completed",
  "context": {
    "screens_from_sdd": 15,
    "screens_predicted": 10,
    "screens_total": 25,
    "navigation_complete": true
  }
}
```

---

## 智慧預測規則

### App 類型特定畫面

| App 類型 | 額外預測畫面 |
|----------|--------------|
| 教育類 | lesson-list, lesson-detail, quiz, result, progress |
| 電商類 | product-list, product-detail, cart, checkout, order-history |
| 社群類 | feed, post-detail, profile, chat, notification |
| 工具類 | main, settings, history, export |

### 標準流程畫面

| 流程 | 必要畫面序列 |
|------|--------------|
| 認證 | splash → login → (register/forgot) → role-select → home |
| 設定 | home → setting-main → setting-detail → home |
| 列表詳情 | list → detail → (edit/delete) → list |
| 表單 | form → confirm → success → list |

### 角色特定畫面

若 App 有多角色，每個角色需要獨立的：
- 首頁 (SCR-DASH-001-student, SCR-DASH-002-teacher)
- 設定頁 (角色特定選項)
- 個人資料頁

---

## 阻斷條件

| 條件 | 說明 |
|------|------|
| 畫面清單為空 | **禁止進入 03-generation** |
| 有孤立畫面 | 必須補充導航路徑 |
| onclick 目標不存在 | 必須補充目標畫面 |

---

## 下一節點

→ `process/03-generation/README.md` (HTML 生成)

**注意**: 只有在畫面清單 100% 完整時才能進入下一節點！
