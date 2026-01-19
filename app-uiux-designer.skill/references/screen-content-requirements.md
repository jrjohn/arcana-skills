# Screen Content Requirements (畫面內容最小要求)

每個 SCR-* 畫面 HTML 必須包含完整的 UI 內容，禁止使用 placeholder。

---

## 1. 畫面 HTML 最小必要元素

### 1.1 基本結構

每個畫面 HTML 必須包含：

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SCR-{MODULE}-{NNN} {Screen Name}</title>
  <!-- 必須引用 Design System CSS -->
  <link rel="stylesheet" href="../shared/{{PROJECT_ID}}-theme.css">
</head>
<body>
  <!--
  @screen-id: SCR-{MODULE}-{NNN}
  @screen-name: {Screen Name}
  @requirements: REQ-{MODULE}-{NNN}, REQ-{MODULE}-{NNN}
  @acceptance-criteria: AC-{MODULE}-{NNN}
  -->

  <!-- 導航列 (Navigation Bar) -->
  <header>...</header>

  <!-- 主內容區 (Main Content) -->
  <main>...</main>

  <!-- 底部導航/Tab Bar (如適用) -->
  <nav>...</nav>

  <!-- 必須引用父窗口通知腳本 -->
  <script src="../shared/notify-parent.js"></script>
</body>
</html>
```

### 1.2 必須包含的 Meta 資訊

| 項目 | 格式 | 範例 |
|------|------|------|
| Screen ID | `@screen-id: SCR-{MODULE}-{NNN}` | `@screen-id: SCR-AUTH-001` |
| Screen Name | `@screen-name: {Name}` | `@screen-name: Login` |
| Requirements | `@requirements: REQ-*` | `@requirements: REQ-AUTH-001, REQ-AUTH-002` |
| Acceptance Criteria | `@acceptance-criteria: AC-*` | `@acceptance-criteria: AC-AUTH-001` |

---

## 2. 可點擊元素規範

### 2.1 必須滿足的條件

| 元素類型 | 必須包含 | 禁止 |
|----------|----------|------|
| **Button** | `onclick` 指向存在的 SCR-* | 空 onclick 或 placeholder (`#`) |
| **Tab Bar** | 每個 Tab 有對應畫面 | Tab 指向不存在的畫面 |
| **Form Submit** | success/error 畫面 | 表單無回饋畫面 |
| **Back Button** | `history.back()` 或指定畫面 | 無返回機制 |
| **Link** | 有效的 href | 懸空連結 (`href="#"`) |
| **Icon Button** | onclick 或 href | 無互動的圖標 |

### 2.2 onclick 正確模式

```html
<!-- 正確：導航到存在的畫面 -->
<button onclick="location.href='../dash/SCR-DASH-001-home.html'">
  進入首頁
</button>

<!-- 正確：返回上一頁 -->
<button onclick="history.back()">
  返回
</button>

<!-- 正確：打開 Modal -->
<button onclick="showModal('confirm-dialog')">
  確認
</button>

<!-- 錯誤：空的 onclick -->
<button onclick="">點擊</button>

<!-- 錯誤：placeholder -->
<button onclick="javascript:void(0)">TODO</button>
```

### 2.3 href 正確模式

```html
<!-- 正確：導航到存在的畫面 -->
<a href="../setting/SCR-SETTING-001-profile.html">設定</a>

<!-- 錯誤：懸空連結 -->
<a href="#">設定</a>

<!-- 錯誤：不存在的目標 -->
<a href="../nonexistent/page.html">連結</a>
```

---

## 3. 畫面類型內容要求

### 3.1 登入頁 (Login)

**必須元素：**
- Logo 或 App 名稱
- 帳號輸入框 (email/phone)
- 密碼輸入框
- 登入按鈕 → 成功: DASH-001, 失敗: 顯示錯誤
- 忘記密碼連結 → AUTH-forgot-password
- 註冊連結 → AUTH-register
- 社群登入按鈕 (如適用)

**模板：** `templates/screen-types/auth/login.html`

### 3.2 註冊頁 (Register)

**必須元素：**
- 帳號輸入框
- 密碼輸入框
- 確認密碼輸入框
- 條款同意 checkbox
- 註冊按鈕 → 成功: verification/onboarding
- 返回登入連結

**模板：** `templates/screen-types/auth/register.html`

### 3.3 列表頁 (List)

**必須元素：**
- 頁面標題
- 搜尋框 (如適用)
- 列表項目 (至少 3-5 個示例)
- 每個項目可點擊 → detail 頁
- 空狀態處理 → empty-state
- 載入中狀態 → loading-state

**模板：** `templates/screen-types/common/list-page.html`

### 3.4 詳情頁 (Detail)

**必須元素：**
- 返回按鈕 → history.back()
- 標題
- 內容區塊
- 操作按鈕 (編輯/刪除/分享)

**模板：** `templates/screen-types/common/detail-page.html`

### 3.5 表單頁 (Form)

**必須元素：**
- 返回/取消按鈕
- 表單標題
- 輸入欄位 (含驗證)
- 提交按鈕 → success 或 error
- 表單驗證錯誤顯示

**模板：** `templates/screen-types/common/form-page.html`

### 3.6 設定頁 (Settings)

**必須元素：**
- 頁面標題
- 設定項目分組
- 每個可點擊項目有對應目標
- 版本資訊
- 登出按鈕 → AUTH-001

**模板：** `templates/screen-types/common/settings.html`

### 3.7 Dashboard (儀表板)

**必須元素：**
- 歡迎訊息/用戶名
- 數據卡片/統計
- 快捷操作按鈕
- Tab Bar (如適用)

**模板：** `templates/screen-types/common/dashboard.html`

---

## 4. 狀態畫面要求

### 4.1 空狀態 (Empty State)

```html
<div class="empty-state">
  <img src="./assets/empty-icon.svg" alt="Empty">
  <h3>目前沒有資料</h3>
  <p>點擊下方按鈕開始新增</p>
  <button onclick="location.href='../form/create.html'">
    新增第一筆資料
  </button>
</div>
```

**模板：** `templates/screen-types/states/empty-state.html`

### 4.2 載入中 (Loading)

```html
<div class="loading-state">
  <div class="spinner"></div>
  <p>載入中...</p>
</div>
```

**模板：** `templates/screen-types/states/loading-state.html`

### 4.3 錯誤狀態 (Error)

```html
<div class="error-state">
  <img src="./assets/error-icon.svg" alt="Error">
  <h3>發生錯誤</h3>
  <p>請稍後再試</p>
  <button onclick="location.reload()">重試</button>
  <button onclick="history.back()">返回</button>
</div>
```

**模板：** `templates/screen-types/states/error-state.html`

### 4.4 成功狀態 (Success)

```html
<div class="success-state">
  <img src="./assets/success-icon.svg" alt="Success">
  <h3>操作成功</h3>
  <p>您的資料已儲存</p>
  <button onclick="location.href='../dash/SCR-DASH-001.html'">
    返回首頁
  </button>
</div>
```

**模板：** `templates/screen-types/states/success-state.html`

---

## 5. 導航元件要求

### 5.1 Navigation Bar (頂部導航)

```html
<header class="nav-bar">
  <!-- 返回按鈕 (非首頁時必須) -->
  <button class="nav-back" onclick="history.back()">
    <svg><!-- back icon --></svg>
  </button>

  <!-- 標題 -->
  <h1 class="nav-title">頁面標題</h1>

  <!-- 右側操作 (如適用) -->
  <div class="nav-actions">
    <button onclick="...">操作</button>
  </div>
</header>
```

**模板：** `templates/screen-types/components/navigation-bar.html`

### 5.2 Tab Bar (底部導航)

```html
<nav class="tab-bar">
  <a href="../dash/SCR-DASH-001.html" class="tab-item active">
    <svg><!-- icon --></svg>
    <span>首頁</span>
  </a>
  <a href="../feature/SCR-FEATURE-001.html" class="tab-item">
    <svg><!-- icon --></svg>
    <span>功能</span>
  </a>
  <a href="../setting/SCR-SETTING-001.html" class="tab-item">
    <svg><!-- icon --></svg>
    <span>設定</span>
  </a>
</nav>
```

**每個 Tab 必須：**
- 有對應的 SCR-* 畫面
- href 指向存在的 HTML 檔案
- 標示當前頁面 (`class="active"`)

**模板：** `templates/screen-types/components/tab-bar.html`

### 5.3 Modal (彈窗)

```html
<div id="confirm-modal" class="modal hidden">
  <div class="modal-backdrop" onclick="closeModal()"></div>
  <div class="modal-content">
    <h3>確認操作</h3>
    <p>確定要執行此操作嗎？</p>
    <div class="modal-actions">
      <button onclick="closeModal()">取消</button>
      <button onclick="confirmAction()">確認</button>
    </div>
  </div>
</div>

<script>
function showModal(id) {
  document.getElementById(id).classList.remove('hidden');
}
function closeModal() {
  document.querySelector('.modal:not(.hidden)').classList.add('hidden');
}
</script>
```

**模板：** `templates/screen-types/components/modal.html`

---

## 6. 驗證檢查清單

### 生成畫面前必須確認：

- [ ] 所有 `onclick` 目標畫面存在
- [ ] 所有 `href` 指向存在的 HTML
- [ ] 每個畫面有返回機制（除首頁/登入頁）
- [ ] Tab Bar 的每個 Tab 有對應畫面
- [ ] 表單有 success/error 回饋畫面
- [ ] Modal 有關閉機制
- [ ] 包含 `@screen-id` 等 meta 資訊
- [ ] 引用了 `notify-parent.js`
- [ ] 引用了 Design System CSS

### 驗證命令

```bash
# 執行可點擊元素驗證
node capture-screenshots.js --validate-only

# 預期輸出
# ✅ Coverage: 100%
# ✅ All clickable elements have valid targets
```

---

## 7. 禁止事項

| 禁止項目 | 原因 | 正確做法 |
|----------|------|----------|
| `onclick=""` 空字串 | 無效互動 | 指定有效目標或 alert |
| `href="#"` | 懸空連結 | 指定存在的畫面 |
| 只有圖標沒有 onclick | 無法互動 | 添加 onclick 事件 |
| 文字說「點此進入」但無連結 | 誤導用戶 | 添加 href 或 onclick |
| 按鈕文字是「...」 | Placeholder | 使用真實文字 |
| **`type="submit"` 無 onclick** | 表單送出但無導航 | 改為 `type="button"` + onclick |
| **社群登入按鈕無 onclick** | 點擊無反應 | 必須指定登入後目標畫面 |
| **可點擊列表行無 onclick** | 點擊無反應 | 必須有 onclick (見 7.3) |

### ⚠️ 7.0.1 CRITICAL RULE: 所有可點擊元素必須有功能

**每個視覺上看起來可點擊的元素都必須有 onclick 處理器，無例外。**

當目標畫面存在時：
```html
onclick="location.href='SCR-SETTING-002-profile.html'"
```

當目標畫面尚未建立時，使用功能說明 alert：
```html
onclick="alert('個人資料設定：編輯您的個人資訊')"
```

⚠️ **禁止完全省略 onclick** - 這比使用 alert 更糟糕！

### 7.1 特別注意：表單按鈕

⚠️ **Critical Rule: Form Submit Button**

```html
<!-- ❌ 錯誤：type="submit" 無 onclick，只會觸發表單送出 -->
<form>
  <button type="submit">登入</button>
</form>

<!-- ✅ 正確：改為 type="button" 並加上 onclick 導航 -->
<form>
  <button type="button" onclick="location.href='SCR-AUTH-004-role.html'">
    登入
  </button>
</form>
```

### 7.2 特別注意：社群登入按鈕

⚠️ **Critical Rule: Social Login Buttons**

所有社群登入按鈕（Apple, Google, Facebook 等）**必須**有 onclick 導航：

```html
<!-- ❌ 錯誤：社群登入按鈕無 onclick -->
<button class="social-btn">
  Apple 登入
</button>

<!-- ✅ 正確：社群登入按鈕有 onclick 導航 -->
<button type="button" onclick="location.href='SCR-AUTH-004-role.html'" class="social-btn">
  Apple 登入
</button>
```

### 7.3 特別注意：設定列表行 (Settings Row)

⚠️ **Critical Rule: Clickable Settings Rows**

設定頁面中的每個可點擊列表行 **必須** 有 onclick 處理器：

**可點擊列表行的特徵：**
- 有 hover/active 效果 (如 `active:bg-*`, `hover:bg-*`)
- 有右側箭頭圖標 (`>` 或 chevron SVG)
- 視覺上看起來像可點擊的項目

```html
<!-- ❌ 錯誤：設定列表行無 onclick -->
<button class="w-full px-4 py-3 flex items-center justify-between active:bg-slate-50">
  <span>個人資料</span>
  <svg><!-- chevron right --></svg>
</button>

<!-- ✅ 正確：設定列表行有 onclick (目標存在) -->
<button onclick="location.href='SCR-SETTING-002-profile.html'" class="w-full px-4 py-3 flex items-center justify-between active:bg-slate-50">
  <span>個人資料</span>
  <svg><!-- chevron right --></svg>
</button>

<!-- ✅ 正確：設定列表行有 onclick (目標不存在，使用 alert) -->
<button onclick="alert('個人資料設定：編輯姓名、頭像、電子郵件等個人資訊')" class="w-full px-4 py-3 flex items-center justify-between active:bg-slate-50">
  <span>個人資料</span>
  <svg><!-- chevron right --></svg>
</button>
```

**設定頁必須處理的列表行類型：**

| 列表行 | onclick 目標或功能說明 |
|--------|------------------------|
| 個人資料 | `SCR-SETTING-002-profile.html` 或 alert 說明 |
| 帳號安全 | `SCR-SETTING-003-security.html` 或 alert 說明 |
| 通知設定 | `SCR-SETTING-004-notification.html` 或 alert 說明 |
| 主題外觀 | alert('主題外觀：選擇淺色/深色模式') |
| 語音設定 | alert('語音設定：調整發音速度和音量') |
| 隱私設定 | `SCR-SETTING-005-privacy.html` 或 alert 說明 |
| 資料管理 | alert('資料管理：匯出或刪除您的資料') |
| 服務條款 | 外部連結或 alert 說明 |
| 版本資訊 | alert('VocabKids v1.2.0 - 已是最新版本') |
| 登出 | `SCR-AUTH-001-login.html` |

---

## 8. 模板使用指南

### 複製模板

```bash
# 複製特定類型的模板
cp ~/.claude/skills/app-uiux-designer.skill/templates/screen-types/auth/login.html \
   ./04-ui-flow/auth/SCR-AUTH-001-login.html

# 複製所有模板
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/screen-types/* \
   ./04-ui-flow/templates/
```

### 替換變數

模板中的變數需要替換：

| 變數 | 說明 |
|------|------|
| `{{PROJECT_NAME}}` | 專案名稱 |
| `{{PROJECT_ID}}` | 專案代碼 |
| `{{SCREEN_ID}}` | 畫面 ID (SCR-*) |
| `{{SCREEN_NAME}}` | 畫面名稱 |
| `{{MODULE}}` | 模組代碼 |

---

## 9. 雙平台目錄結構 (Dual Platform Directory)

### 9.1 目錄結構

```
04-ui-flow/
├── auth/                 # iPad 版認證畫面
│   ├── SCR-AUTH-001-login.html
│   ├── SCR-AUTH-002-register.html
│   └── SCR-AUTH-004-role.html
├── vocab/                # iPad 版字庫畫面
├── train/                # iPad 版訓練畫面
├── home/                 # iPad 版首頁畫面
├── report/               # iPad 版報表畫面
├── setting/              # iPad 版設定畫面
├── iphone/               # ⚠️ iPhone 版統一目錄
│   ├── SCR-AUTH-001-login.html
│   ├── SCR-AUTH-002-register.html
│   ├── SCR-VOCAB-001-list.html
│   └── ... (所有 iPhone 畫面)
└── docs/
    └── ui-flow-diagram.html
```

### 9.2 路徑規則

| 平台 | 路徑模式 | 範例 |
|------|----------|------|
| iPad | `../{module}/SCR-*.html` | `../auth/SCR-AUTH-001-login.html` |
| iPhone | `../iphone/SCR-*.html` | `../iphone/SCR-AUTH-001-login.html` |

### 9.3 UI Flow Diagram 裝置切換

**禁止**：iPhone 模式載入 iPad 畫面
**必須**：根據 `?device=` 參數動態切換 iframe src

```javascript
// ⚠️ 必須在 ui-flow-diagram.html 中實作
if (currentDevice === 'iphone') {
  switchIframeSourcesToIPhone();
}

function switchIframeSourcesToIPhone() {
  document.querySelectorAll('.screen-iframe').forEach(iframe => {
    const src = iframe.getAttribute('src');
    // ../auth/SCR-*.html → ../iphone/SCR-*.html
    const newSrc = src.replace(/\.\.\/(auth|vocab|train|home|report|setting)\//, '../iphone/');
    iframe.setAttribute('src', newSrc);
  });
}
```

---

> **See also:**
> - `ui-flow-generation-workflow.md` - 完整生成流程
> - `coverage-validation.md` - 可點擊元素驗證
> - `templates/screen-types/README.md` - 模板詳細說明
