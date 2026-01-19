# UI Flow Template Usage Guide

## Overview

本指南說明如何使用 VocabKids 風格的 UI Flow 模板來產生新專案的 UI Flow。

## Template Structure

```
templates/
├── ui-flow/                          # 主要 UI Flow 框架
│   ├── index.html                   # 畫面總覽頁面
│   ├── device-preview.html          # 多裝置預覽頁面
│   ├── screen-template-iphone.html  # iPhone 畫面基礎模板
│   ├── screen-template-ipad.html    # iPad 畫面基礎模板
│   ├── shared/
│   │   ├── project-theme.css        # 專案主題 CSS
│   │   └── notify-parent.js         # iframe 同步腳本
│   ├── validate-navigation.js       # 導航驗證腳本
│   └── capture-screenshots.js       # Puppeteer 截圖腳本
│
└── screen-types/                    # 可重用畫面模板
    ├── auth/
    │   ├── login-ipad.html          # iPad 登入模板
    │   ├── login-iphone.html        # iPhone 登入模板
    │   ├── register.html
    │   ├── forgot-password.html
    │   └── role-selection.html
    ├── common/
    │   ├── dashboard.html
    │   ├── list-page.html
    │   ├── detail-page.html
    │   ├── form-page.html
    │   ├── profile.html
    │   ├── search.html
    │   ├── settings-iphone.html     # iPhone 設定頁面模板
    │   └── settings-ipad.html       # iPad 設定頁面模板
    ├── components/
    │   ├── modal.html
    │   ├── navigation-bar.html
    │   └── tab-bar.html
    └── states/
        ├── loading-state.html
        ├── empty-state.html
        ├── error-state.html
        └── success-state.html
```

## Device Specifications

### iPad Pro 11"
- **Viewport**: 1194 x 834
- **Container**: `<div class="w-[1194px] h-[834px]">`
- **適用**: 較大的畫面空間，可使用左右分割布局

### iPhone 15 Pro / 16 Pro
- **Viewport**: 393 x 852
- **Container**: `<div class="w-[393px] h-[852px]">`
- **Status Bar**: `<div class="h-12 flex-shrink-0"></div>`
- **Home Indicator**: `<div class="w-32 h-1 bg-gray-800/20 rounded-full"></div>`

## Placeholder Variables

### Project-Level Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PROJECT_NAME}}` | 專案名稱 | VocabKids |
| `{{PROJECT_ID}}` | 專案 ID (小寫) | vocabkids |
| `{{PROJECT_ICON}}` | 專案圖標 (emoji) | 📚 |
| `{{PROJECT_TAGLINE}}` | 專案標語 | 和小智一起學英文! |
| `{{PROJECT_DESCRIPTION}}` | 專案描述 | 兒童英語單字學習 |
| `{{PROJECT_INITIAL}}` | 專案首字母 | V |

### Screen-Level Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SCREEN_ID}}` | 畫面 ID | SCR-AUTH-001 |
| `{{SCREEN_NAME}}` | 畫面名稱 | 登入頁面 |
| `{{SCREEN_TITLE}}` | 畫面標題 | 登入 |
| `{{SCREEN_DESCRIPTION}}` | 畫面描述 | 使用者登入介面 |
| `{{REQUIREMENTS}}` | 相關需求 | REQ-AUTH-001, REQ-AUTH-002 |

### Navigation Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{TARGET_BACK}}` | 返回目標 | SCR-HOME-001-student.html |
| `{{TARGET_HOME}}` | 首頁目標 | SCR-HOME-001-student.html |
| `{{TARGET_SETTINGS}}` | 設定頁目標 | SCR-SETTING-001-settings.html |
| `{{TARGET_AFTER_LOGIN}}` | 登入後目標 | SCR-AUTH-004-role.html |
| `{{TARGET_REGISTER}}` | 註冊頁目標 | SCR-AUTH-002-register.html |
| `{{TARGET_FORGOT_PASSWORD}}` | 忘記密碼目標 | SCR-AUTH-003-forgot-password.html |

### Theme Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `{{PRIMARY_50}}` | Primary 50 色 | #E0F7FA |
| `{{PRIMARY_100}}` | Primary 100 色 | #B2EBF2 |
| `{{PRIMARY_500}}` | Primary 500 色 | #00BCD4 |
| `{{PRIMARY_700}}` | Primary 700 色 | #0097A7 |

## Usage Flow

### Step 1: Copy Template Structure

```bash
# 複製 ui-flow 框架到專案
cp -r templates/ui-flow/ [PROJECT]/04-ui-flow/

# 複製需要的 screen-types
cp templates/screen-types/auth/login-ipad.html [PROJECT]/04-ui-flow/auth/SCR-AUTH-001-login.html
cp templates/screen-types/auth/login-iphone.html [PROJECT]/04-ui-flow/iphone/SCR-AUTH-001-login.html
```

### Step 2: Replace Placeholders

1. 開啟複製的 HTML 檔案
2. 使用 Find & Replace 替換所有 `{{VARIABLE}}` 為實際值
3. 確保所有 `onclick="location.href='...'"` 指向正確的目標畫面

### Step 3: Customize Theme

1. 編輯 `shared/[project-id]-theme.css`
2. 設定專案主色調和字型

### Step 4: Validate Navigation

```bash
cd [PROJECT]/04-ui-flow
node validate-navigation.js --fix
```

### Step 5: Generate Screenshots

```bash
cd [PROJECT]/04-ui-flow
npm install puppeteer --save-dev
node capture-screenshots.js
```

## Critical Rules

### 1. 每個畫面必須包含

```html
<!-- 檔案結尾必須包含 notify-parent.js -->
<script src="../shared/notify-parent.js"></script>
</body>
</html>

<!-- 檔案結尾必須包含 metadata -->
<!--
@requirements: REQ-XXX-001
@screen-id: SCR-XXX-001
@screen-name: 畫面名稱
@description: 畫面描述
@acceptance-criteria:
  - AC1: 驗收條件 1
  - AC2: 驗收條件 2
-->
```

### 2. Button Navigation 必須完整

每個可點擊元素必須有 `onclick` 或 `href`：

```html
<!-- ✅ 正確 -->
<button onclick="location.href='SCR-AUTH-002-register.html'">註冊</button>
<a href="SCR-AUTH-003-forgot-password.html">忘記密碼</a>

<!-- ❌ 錯誤 - 沒有導航目標 -->
<button>註冊</button>
<a href="#">忘記密碼</a>
```

### 3. iPad 和 iPhone 版本必須對應

| iPad 路徑 | iPhone 路徑 |
|-----------|-------------|
| `auth/SCR-AUTH-001-login.html` | `iphone/SCR-AUTH-001-login.html` |
| `home/SCR-HOME-001-student.html` | `iphone/SCR-HOME-001-student.html` |
| `setting/SCR-SETTING-001-settings.html` | `iphone/SCR-SETTING-001-settings.html` |

### 4. 目錄結構

```
04-ui-flow/
├── index.html
├── device-preview.html
├── validate-navigation.js
├── capture-screenshots.js
├── shared/
│   ├── [project-id]-theme.css
│   └── notify-parent.js
├── docs/
│   └── ui-flow-diagram.html
├── auth/                    # iPad Auth 畫面
│   ├── SCR-AUTH-001-login.html
│   └── SCR-AUTH-002-register.html
├── home/                    # iPad Home 畫面
│   └── SCR-HOME-001-student.html
├── setting/                 # iPad Setting 畫面
│   └── SCR-SETTING-001-settings.html
├── iphone/                  # 所有 iPhone 畫面
│   ├── SCR-AUTH-001-login.html
│   ├── SCR-AUTH-002-register.html
│   ├── SCR-HOME-001-student.html
│   └── SCR-SETTING-001-settings.html
└── screenshots/             # 截圖輸出
    ├── iphone/
    └── ipad/
```

## Best Practices

1. **先完成 SDD 的 Button Navigation Table**
   - 確保所有按鈕都有明確的 Target Screen
   - 這樣 UI Flow 就不需要「預測」導航目標

2. **使用 Design Token**
   - 在 theme CSS 中定義所有顏色
   - 使用 CSS Variables 讓主題可切換

3. **保持一致的命名**
   - Screen ID: `SCR-[MODULE]-[NUMBER]-[name].html`
   - 例如: `SCR-AUTH-001-login.html`

4. **定期驗證**
   - 每次修改後執行 `validate-navigation.js`
   - 確保 100% 導航覆蓋率
