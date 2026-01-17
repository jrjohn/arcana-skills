# 06-screenshot: iPhone Version & Screenshot Generation

## 進入條件

- [ ] 05-diagram 已完成
- [ ] ui-flow-diagram.html 已產生且包含所有畫面
- [ ] ui-flow-diagram.html 包含 iPhone 切換功能
- [ ] device-preview.html sidebar 已填入所有畫面

## 退出條件

- [ ] **iPhone HTML 畫面已產生** (推薦) **或** 已設定 fallback
- [ ] device-preview.html 在 iPhone 模式下可正常運作
- [ ] ui-flow-diagram.html?device=iphone 可正常顯示

---

## ⚠️ 重要：預設應產生 iPhone 版本

> **RECOMMENDED**: 為每個 iPad 畫面產生對應的 iPhone 版本
>
> iPad fallback 只應在用戶明確要求「不需要 iPhone 版本」時使用

**為什麼需要 iPhone 版本？**
1. iPhone 和 iPad 的 UI 布局不同（直式 vs 橫式）
2. 按鈕大小、間距需要針對不同螢幕調整
3. Grid 列數需要調整（iPad grid-cols-3 → iPhone grid-cols-1/2）
4. 提供完整的跨裝置 UI 體驗

---

## Option A: 產生 iPhone 版本 (RECOMMENDED - 預設執行)

### Step A1: 讀取 iPhone 畫面模板

模板位置：`[SKILL_DIR]/templates/ui-flow/screen-template-iphone.html`

**iPhone 模板規格：**
```html
<meta name="viewport" content="width=393, height=852">
<style>
  body {
    width: 393px;
    height: 852px;
    overflow: hidden;
  }
</style>
```

### Step A2: 為每個 iPad 畫面建立 iPhone 版本

**轉換規則：**

| iPad 設定 | iPhone 設定 |
|----------|-------------|
| `width=1194, height=834` | `width=393, height=852` |
| `body { width: 1194px; height: 834px }` | `body { width: 393px; height: 852px }` |
| `grid-cols-3` | `grid-cols-1` 或 `grid-cols-2` |
| `px-8` / `px-12` | `px-4` / `px-6` |
| `text-3xl` / `text-4xl` | `text-xl` / `text-2xl` |
| Side-by-side layout | Stacked/scrollable layout |

**檔案對應關係：**
```
auth/SCR-AUTH-001-splash.html     → iphone/SCR-AUTH-001-splash.html
auth/SCR-AUTH-002-login.html      → iphone/SCR-AUTH-002-login.html
vocab/SCR-VOCAB-001-set-list.html → iphone/SCR-VOCAB-001-set-list.html
train/SCR-TRAIN-001-mode-select.html → iphone/SCR-TRAIN-001-mode-select.html
...
```

### Step A3: iPhone 畫面布局調整指南

**登入/註冊畫面：**
- iPad: 左右分割（圖片+表單）
- iPhone: 上下堆疊（小圖標+表單）

**列表畫面：**
- iPad: `grid-cols-3` 卡片
- iPhone: `grid-cols-1` 或 `grid-cols-2` 卡片

**詳情畫面：**
- iPad: 側邊欄+主內容
- iPhone: 全屏主內容，底部 Tab 或返回按鈕

**設定畫面：**
- iPad: 較大間距和字體
- iPhone: 緊湊間距，標準行高

### Step A4: 驗證 iPhone 版本

```bash
# 檢查 iPhone 畫面數量
ls -1 iphone/*.html | wc -l

# 應該等於 iPad 畫面總數
ls -1 auth/*.html vocab/*.html train/*.html setting/*.html parent/*.html progress/*.html | wc -l

# 兩個數字應該相等
```

### Step A5: 測試 iPhone 切換

1. 開啟 `index.html`
2. 點擊 iPhone 切換按鈕
3. 確認 ui-flow-diagram 顯示 iPhone 框架
4. 點擊任一卡片，確認 device-preview.html 載入 `iphone/` 路徑

---

## Option B: iPad Fallback (僅在用戶明確要求時使用)

> ⚠️ **只有在用戶明確說「不需要 iPhone 版本」或「時間有限」時才使用此選項**

### Step B1: 修改 device-preview.html

確保 `updateIframeSrc()` 函數使用 iPad 路徑給 iPhone：

```javascript
function updateIframeSrc() {
  // Use iPad URL for all devices (iPhone screens not yet generated)
  let ipadUrl = currentScreen;

  // If currentScreen starts with 'iphone/', convert back to iPad path
  if (currentScreen.startsWith('iphone/')) {
    if (currentElement) {
      const onclick = currentElement.getAttribute('onclick');
      if (onclick) {
        const match = onclick.match(/loadScreen\('([^']+)'/);
        if (match) {
          ipadUrl = match[1];
        }
      }
    }
  }

  // Set all iframes to iPad URL
  document.getElementById('preview-iframe-ipad').src = ipadUrl;
  document.getElementById('preview-iframe-ipad-mini').src = ipadUrl;
  document.getElementById('preview-iframe-iphone').src = ipadUrl;  // ← Use ipadUrl
}
```

### Step B2: 修改 ui-flow-diagram.html

修改 `switchIframeSourcesToIPhone()` 不要切換路徑：

```javascript
function switchIframeSourcesToIPhone() {
  // Fallback: Don't change paths, use iPad version in iPhone frame
  // iPhone screens not generated, iPad version will be scaled
  console.log('Using iPad fallback for iPhone display');
}
```

### Step B3: 驗證 Fallback

1. 開啟 `docs/ui-flow-diagram.html?device=iphone`
2. 確認卡片顯示（雖然是 iPad 內容縮放）
3. 開啟 `device-preview.html`
4. 切換到 iPhone 模式
5. 確認有內容顯示

---

## 截圖產生 (選用)

如果需要產生 PNG 截圖用於 SDD 文件：

### Step 1: 安裝依賴

```bash
cd 04-ui-flow
npm install puppeteer --save-dev
```

### Step 2: 執行截圖腳本

```bash
node capture-screenshots.js
```

### Step 3: 驗證截圖

```bash
ls -la screenshots/ipad/
ls -la screenshots/iphone/
```

---

## 輸出檔案

**如果執行 Option A (推薦)：**
```
04-ui-flow/
├── iphone/
│   ├── SCR-AUTH-001-splash.html
│   ├── SCR-AUTH-002-login.html
│   ├── SCR-AUTH-003-register.html
│   ├── ... (所有 40 個畫面的 iPhone 版本)
│   └── SCR-SETTING-012-feedback.html
└── screenshots/ (選用)
    ├── ipad/
    │   └── *.png
    └── iphone/
        └── *.png
```

**如果執行 Option B (Fallback)：**
```
04-ui-flow/
├── iphone/                    # 空資料夾
├── device-preview.html        # 已修改使用 fallback
└── docs/ui-flow-diagram.html  # 已修改使用 fallback
```

---

## 阻斷條件 (BLOCKING)

> ⛔ **以下情況禁止進入下一節點**

1. device-preview.html iPhone 模式完全空白
2. ui-flow-diagram.html?device=iphone 完全空白
3. iPhone iframe src 指向不存在的檔案且無 fallback

**驗證指令：**
```bash
# 檢查是否有 iPhone 畫面
ls iphone/*.html 2>/dev/null | wc -l

# 如果 = 0，檢查是否有設定 fallback
grep -c 'iPad fallback\|ipadUrl' device-preview.html

# 至少一個條件要滿足
```

---

## 下一節點

→ `process/07-feedback/README.md` (SDD/SRS 回饋)
