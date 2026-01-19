# Screen Types Templates (畫面內容模板)

提供常見畫面類型的 HTML 內容模板，確保每個畫面都包含完整的 UI 元件和有效的導航。

---

## 目錄結構

```
templates/screen-types/
├── README.md                    # 本說明文件
├── auth/                        # 認證相關畫面 (4)
│   ├── login.html               # 登入頁
│   ├── register.html            # 註冊頁
│   ├── forgot-password.html     # 忘記密碼
│   └── role-selection.html      # 角色選擇
├── onboarding/                  # Onboarding 流程 (1)
│   └── onboarding.html          # 歡迎/功能介紹滑動頁
├── common/                      # 通用畫面類型 (7)
│   ├── list-page.html           # 列表頁
│   ├── detail-page.html         # 詳情頁
│   ├── form-page.html           # 表單頁
│   ├── dashboard.html           # 儀表板
│   ├── settings.html            # 設定頁
│   ├── profile.html             # 個人檔案頁
│   └── search.html              # 搜尋頁
├── states/                      # 狀態畫面 (4)
│   ├── empty-state.html         # 空狀態
│   ├── loading-state.html       # 載入中
│   ├── error-state.html         # 錯誤
│   └── success-state.html       # 成功
└── components/                  # 可重用組件 (3)
    ├── tab-bar.html             # Tab Bar
    ├── navigation-bar.html      # 導航列 (多種變體)
    └── modal.html               # Modal/Action Sheet/Bottom Sheet

總計: 19 模板
```

---

## 使用方式

### 1. 複製模板

```bash
# 複製單一模板
cp ~/.claude/skills/app-uiux-designer.skill/templates/screen-types/auth/login.html \
   ./04-ui-flow/auth/SCR-AUTH-001-login.html

# 複製整個類型
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/screen-types/auth/* \
   ./04-ui-flow/auth/
```

### 2. 替換變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{PROJECT_NAME}}` | 專案名稱 | `MyApp` |
| `{{PROJECT_ID}}` | 專案代碼 | `myapp` |
| `{{SCREEN_ID}}` | 畫面 ID | `SCR-AUTH-001` |
| `{{SCREEN_NAME}}` | 畫面名稱 | `Login` |
| `{{MODULE}}` | 模組代碼 | `AUTH` |

```bash
sed -i 's/{{PROJECT_NAME}}/MyApp/g' ./04-ui-flow/auth/SCR-AUTH-001-login.html
sed -i 's/{{SCREEN_ID}}/SCR-AUTH-001/g' ./04-ui-flow/auth/SCR-AUTH-001-login.html
```

### 3. 自訂導航目標

模板中的導航使用佔位符，需要替換為實際的畫面路徑：

```html
<!-- 模板中 -->
<button onclick="location.href='{{TARGET_DASH_HOME}}'">進入首頁</button>

<!-- 替換後 -->
<button onclick="location.href='../dash/SCR-DASH-001-home.html'">進入首頁</button>
```

---

## 模板規範

### 必須包含

1. **Meta 資訊**
```html
<!--
@screen-id: {{SCREEN_ID}}
@screen-name: {{SCREEN_NAME}}
@requirements: REQ-*
-->
```

2. **Design System CSS**
```html
<link rel="stylesheet" href="../shared/{{PROJECT_ID}}-theme.css">
```

3. **父窗口通知腳本**
```html
<script src="../shared/notify-parent.js"></script>
```

4. **有效的導航**
- 所有按鈕有 onclick
- 所有連結有 href
- 返回機制（除首頁/登入頁）

### 禁止事項

- ❌ `onclick=""` 空字串
- ❌ `href="#"` 懸空連結
- ❌ Placeholder 文字如「TODO」
- ❌ 空的 div 容器

---

## 模板清單

### Auth 模板 (4)

| 模板 | 用途 | 必須導航 |
|------|------|----------|
| `login.html` | 登入頁 | → Dashboard, → Register, → Forgot Password |
| `register.html` | 註冊頁 | → Onboarding/Verification, ← Login |
| `forgot-password.html` | 忘記密碼 | → Reset Confirm, ← Login |
| `role-selection.html` | 角色選擇 | → Dashboard, ← Back |

### Onboarding 模板 (1)

| 模板 | 用途 | 必須導航 |
|------|------|----------|
| `onboarding.html` | 歡迎/功能介紹滑動頁 | → Login, → Register, 可跳過 |

### Common 模板 (7)

| 模板 | 用途 | 必須導航 |
|------|------|----------|
| `list-page.html` | 列表頁 | → Detail, Tab Bar |
| `detail-page.html` | 詳情頁 | ← Back, → Edit |
| `form-page.html` | 表單頁 | → Success/Error, ← Cancel |
| `dashboard.html` | 儀表板 | Tab Bar, → Features |
| `settings.html` | 設定頁 | ← Back, → Sub-settings, → Logout |
| `profile.html` | 個人檔案頁 | Tab Bar, → Settings, → Edit Profile |
| `search.html` | 搜尋頁 | Tab Bar, → Results, → Filters |

### States 模板 (4)

| 模板 | 用途 | 必須導航 |
|------|------|----------|
| `empty-state.html` | 空狀態 | → Create Action |
| `loading-state.html` | 載入中 | 無（自動跳轉） |
| `error-state.html` | 錯誤 | → Retry, ← Back |
| `success-state.html` | 成功 | → Home, → Next Action |

### Components 模板 (3)

| 模板 | 用途 | 說明 |
|------|------|------|
| `tab-bar.html` | Tab Bar | 每個 Tab 必須有對應畫面 |
| `navigation-bar.html` | 導航列 | 5 種變體：標準、首頁、搜尋、透明、大標題 |
| `modal.html` | Modal/彈窗 | 5 種變體：確認、警告、表單、Bottom Sheet、Action Sheet |

---

## 自訂模板

如需建立新模板，請遵循以下結構：

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{SCREEN_ID}} {{SCREEN_NAME}}</title>
  <link rel="stylesheet" href="../shared/{{PROJECT_ID}}-theme.css">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
  <!--
  @screen-id: {{SCREEN_ID}}
  @screen-name: {{SCREEN_NAME}}
  @requirements: REQ-{{MODULE}}-*
  -->

  <!-- Navigation Bar -->
  <header class="fixed top-0 left-0 right-0 h-14 bg-white border-b flex items-center px-4 z-50">
    <button onclick="history.back()" class="p-2">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
    </button>
    <h1 class="flex-1 text-center font-semibold">{{SCREEN_NAME}}</h1>
    <div class="w-10"></div>
  </header>

  <!-- Main Content -->
  <main class="pt-14 pb-20 px-4">
    <!-- Your content here -->
  </main>

  <!-- Tab Bar (if applicable) -->
  <nav class="fixed bottom-0 left-0 right-0 h-16 bg-white border-t flex">
    <!-- Tab items -->
  </nav>

  <script src="../shared/notify-parent.js"></script>
</body>
</html>
```

---

> **See also:**
> - `references/screen-content-requirements.md` - 畫面內容詳細要求
> - `references/ui-flow-generation-workflow.md` - 生成流程
