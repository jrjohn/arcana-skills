# UI 畫面自動生成指南

本指南提供自動生成 UI 畫面的完整方法，支援多種輸出格式，從互動式 HTML 原型到各平台原生程式碼。

## 預設設定

| 項目 | 預設值 |
|------|--------|
| **平台** | Mobile App UI/UX |
| **尺寸** | iPhone 14 Pro (390 x 844 pt) |
| **格式** | HTML + Tailwind CSS |
| **入口** | index.html |
| **互動** | 所有 Button/Link 皆可點擊導航 |

## 目錄
1. [互動導航系統](#互動導航系統) ⭐ NEW
2. [生成模式總覽](#生成模式總覽)
3. [HTML/CSS 原型生成](#htmlcss-原型生成)
4. [React 元件生成](#react-元件生成)
5. [iOS SwiftUI 生成](#ios-swiftui-生成)
6. [Android Compose 生成](#android-compose-生成)
7. [SVG 視覺稿生成](#svg-視覺稿生成)
8. [Figma 匯入 JSON](#figma-匯入-json)
9. [完整頁面範本庫](#完整頁面範本庫)
10. [生成提示詞模板](#生成提示詞模板)

---

## 互動導航系統

### 設計原則

所有生成的 HTML UI 必須：
1. **可完整走訪** - 從 index.html 開始，可透過點擊瀏覽所有頁面
2. **真實導航** - 所有 Button/Link 必須有實際連結
3. **流程連貫** - 遵循真實 App 的導航邏輯

### 目錄結構 (必須)

```
📁 generated-ui/
├── 📄 index.html                 # ⭐ 入口頁 - 畫面總覽與導航中心
├── 📁 shared/
│   ├── theme.css                 # Design System CSS Variables
│   ├── navigation.js             # 共用導航邏輯
│   └── components.css            # 共用元件樣式
├── 📁 auth/
│   ├── login.html
│   ├── register.html
│   ├── forgot-password.html
│   ├── verify-otp.html
│   └── reset-password.html
├── 📁 onboard/
│   ├── step-1.html
│   ├── step-2.html
│   └── step-3.html
├── 📁 main/
│   ├── home.html
│   ├── explore.html
│   └── profile.html
└── 📁 [module]/
    └── [pages].html
```

### index.html 入口頁模板

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}} - UI Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="shared/theme.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <header class="text-center mb-12">
            <h1 class="text-4xl font-bold text-gray-900 mb-2">{{PROJECT_NAME}}</h1>
            <p class="text-gray-600">UI/UX Preview - 點擊任一畫面開始瀏覽</p>
            <div class="mt-4 flex justify-center gap-4">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {{SCREEN_COUNT}} 個畫面
                </span>
                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                    Mobile App
                </span>
            </div>
        </header>

        <!-- Quick Start -->
        <section class="mb-12">
            <h2 class="text-xl font-semibold mb-4">🚀 快速開始</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a href="auth/login.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <div class="text-3xl mb-2">🔐</div>
                    <h3 class="font-semibold">從登入開始</h3>
                    <p class="text-sm text-gray-500">體驗完整認證流程</p>
                </a>
                <a href="onboard/step-1.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <div class="text-3xl mb-2">👋</div>
                    <h3 class="font-semibold">從引導流程開始</h3>
                    <p class="text-sm text-gray-500">新用戶體驗</p>
                </a>
                <a href="main/home.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <div class="text-3xl mb-2">🏠</div>
                    <h3 class="font-semibold">直接進入首頁</h3>
                    <p class="text-sm text-gray-500">瀏覽主要功能</p>
                </a>
            </div>
        </section>

        <!-- Screen List by Module -->
        <section>
            <h2 class="text-xl font-semibold mb-4">📱 所有畫面</h2>

            <!-- Auth Module -->
            <div class="mb-6">
                <h3 class="text-lg font-medium text-gray-700 mb-3">認證 (Auth)</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {{#each AUTH_SCREENS}}
                    <a href="{{this.path}}" class="group">
                        <div class="bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-all">
                            <div class="aspect-[9/16] bg-gray-100 rounded mb-2 overflow-hidden">
                                <img src="{{this.thumbnail}}" alt="{{this.name}}" class="w-full h-full object-cover">
                            </div>
                            <p class="text-xs font-medium truncate group-hover:text-blue-600">{{this.name}}</p>
                        </div>
                    </a>
                    {{/each}}
                </div>
            </div>

            <!-- Repeat for other modules... -->
        </section>

        <!-- Flow Diagram -->
        <section class="mt-12">
            <h2 class="text-xl font-semibold mb-4">🔀 導航流程</h2>
            <div class="bg-white rounded-xl p-6 shadow-sm">
                <pre class="text-sm text-gray-600">
index.html
    │
    ├── auth/login.html ─────┬── auth/register.html
    │       │                └── auth/forgot-password.html
    │       ▼
    ├── onboard/step-1.html → step-2.html → step-3.html
    │       │
    │       ▼
    └── main/home.html ──┬── main/explore.html
                         ├── main/profile.html
                         └── [其他功能頁面]
                </pre>
            </div>
        </section>
    </div>
</body>
</html>
```

### 頁面間導航實作

#### 1. Primary Button (下一步)
```html
<!-- 連結至下一個頁面 -->
<button onclick="location.href='../main/home.html'"
        class="w-full bg-primary text-white py-3 rounded-xl font-semibold">
    登入
</button>

<!-- 或使用 <a> 標籤 -->
<a href="../main/home.html"
   class="block w-full bg-primary text-white py-3 rounded-xl font-semibold text-center">
    登入
</a>
```

#### 2. Secondary Button (返回)
```html
<!-- 返回上一頁 -->
<button onclick="history.back()"
        class="w-full bg-gray-100 text-gray-700 py-3 rounded-xl font-semibold">
    返回
</button>

<!-- 或明確指定返回頁面 -->
<button onclick="location.href='login.html'"
        class="w-full bg-gray-100 text-gray-700 py-3 rounded-xl font-semibold">
    返回登入
</button>
```

#### 3. Text Link
```html
<p class="text-center text-gray-600">
    還沒有帳號？
    <a href="register.html" class="text-primary font-semibold hover:underline">
        立即註冊
    </a>
</p>
```

#### 4. Top Navigation Bar
```html
<nav class="flex items-center justify-between px-4 py-3 bg-white border-b">
    <!-- Back Button -->
    <button onclick="history.back()" class="w-10 h-10 flex items-center justify-center">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
    </button>

    <!-- Title -->
    <h1 class="text-lg font-semibold">頁面標題</h1>

    <!-- Action Button (可選) -->
    <button onclick="location.href='settings.html'" class="w-10 h-10 flex items-center justify-center">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01"/>
        </svg>
    </button>
</nav>
```

#### 5. Bottom Tab Bar
```html
<nav class="fixed bottom-0 left-0 right-0 bg-white border-t px-6 pb-6 pt-2">
    <div class="flex items-center justify-around">
        <a href="../main/home.html" class="flex flex-col items-center gap-1 text-primary">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
            </svg>
            <span class="text-xs font-medium">首頁</span>
        </a>
        <a href="../main/explore.html" class="flex flex-col items-center gap-1 text-gray-400">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <span class="text-xs">探索</span>
        </a>
        <a href="../main/profile.html" class="flex flex-col items-center gap-1 text-gray-400">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
            <span class="text-xs">我的</span>
        </a>
    </div>
</nav>
```

#### 6. Card 點擊
```html
<a href="../detail/item-1.html" class="block bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
    <img src="thumbnail.jpg" alt="" class="w-full h-40 object-cover rounded-lg mb-3">
    <h3 class="font-semibold">項目標題</h3>
    <p class="text-sm text-gray-500">描述文字</p>
</a>
```

#### 7. List Item 點擊
```html
<a href="../detail/setting-account.html"
   class="flex items-center gap-4 px-4 py-3 bg-white hover:bg-gray-50 transition-colors">
    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
        <svg class="w-5 h-5 text-blue-600">...</svg>
    </div>
    <div class="flex-1">
        <h4 class="font-medium">帳號設定</h4>
        <p class="text-sm text-gray-500">管理您的帳號資訊</p>
    </div>
    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
    </svg>
</a>
```

### 共用導航 JavaScript (navigation.js)

```javascript
// shared/navigation.js

// 返回上一頁
function goBack() {
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        history.back();
    } else {
        // 預設返回首頁
        location.href = '../index.html';
    }
}

// 導航至指定頁面
function navigateTo(path) {
    location.href = path;
}

// Onboarding 流程導航
function nextOnboardingStep(currentStep, totalSteps) {
    if (currentStep < totalSteps) {
        location.href = `step-${currentStep + 1}.html`;
    } else {
        location.href = '../main/home.html';
    }
}

// 跳過 Onboarding
function skipOnboarding() {
    location.href = '../main/home.html';
}

// Tab Bar 高亮當前頁面
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const tabs = document.querySelectorAll('[data-tab]');

    tabs.forEach(tab => {
        if (currentPath.includes(tab.dataset.tab)) {
            tab.classList.add('text-primary');
            tab.classList.remove('text-gray-400');
        }
    });
});
```

### 導航檢查清單

生成 UI 後，確認以下項目：

```
□ index.html 存在且包含所有頁面連結
□ 所有 Primary Button 有 onclick 或 href
□ 所有 Secondary/Back Button 可返回
□ Text Link 使用正確的 <a> 標籤
□ Tab Bar 每個項目都有連結
□ 可從 index.html 走訪所有頁面
□ 流程頁面 (Onboarding) 可依序導航
□ 詳情頁可返回列表頁
□ 相對路徑正確 (../ 處理正確)
```

---

## 生成模式總覽

### 支援的輸出格式

```
┌─────────────────────────────────────────────────────────────────┐
│                     UI 生成輸出格式                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📄 HTML/CSS        → 可直接瀏覽器預覽的互動原型                  │
│  ⚛️  React/Next.js   → 可直接使用的 React 元件                   │
│  🍎 SwiftUI         → iOS/macOS 原生 UI 程式碼                   │
│  🤖 Jetpack Compose → Android 原生 UI 程式碼                     │
│  🎨 SVG             → 向量視覺稿 (可匯入設計工具)                 │
│  📐 Figma JSON      → 可直接匯入 Figma 的結構化資料              │
│  🖼️  PNG/Screenshot  → 透過 HTML 轉換產生靜態圖片                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 生成流程

```
用戶需求描述
     ↓
┌─────────────────┐
│   需求分析       │
│  - 頁面類型      │
│  - 功能需求      │
│  - 風格偏好      │
└────────┬────────┘
         ↓
┌─────────────────┐
│   風格確認       │
│  - 套用萃取風格  │
│  - 或選擇預設    │
└────────┬────────┘
         ↓
┌─────────────────┐
│   結構規劃       │
│  - 元件拆解      │
│  - 佈局設計      │
└────────┬────────┘
         ↓
┌─────────────────┐
│   程式碼生成     │
│  - 選擇輸出格式  │
│  - 產生完整程式碼│
└────────┬────────┘
         ↓
    可執行的 UI
```

---

## HTML/CSS 原型生成

### 基礎模板結構

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PAGE_TITLE}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '{{PRIMARY_COLOR}}',
                        secondary: '{{SECONDARY_COLOR}}',
                        background: '{{BG_COLOR}}',
                        surface: '{{SURFACE_COLOR}}',
                        'on-primary': '{{ON_PRIMARY}}',
                        'on-surface': '{{ON_SURFACE}}',
                    },
                    fontFamily: {
                        sans: ['{{FONT_FAMILY}}', 'system-ui', 'sans-serif'],
                    },
                    borderRadius: {
                        'theme': '{{BORDER_RADIUS}}',
                    }
                }
            }
        }
    </script>
    <style>
        /* Custom styles */
        {{CUSTOM_STYLES}}
    </style>
</head>
<body class="bg-background min-h-screen">
    {{CONTENT}}
</body>
</html>
```

### 手機框架模板 (iPhone 模擬)

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Preview - {{PAGE_TITLE}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .phone-frame {
            width: 390px;
            height: 844px;
            background: #000;
            border-radius: 50px;
            padding: 12px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .phone-screen {
            width: 100%;
            height: 100%;
            background: #fff;
            border-radius: 40px;
            overflow: hidden;
            position: relative;
        }
        .phone-notch {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 150px;
            height: 34px;
            background: #000;
            border-radius: 0 0 20px 20px;
            z-index: 100;
        }
        .phone-content {
            padding-top: 44px;
            height: 100%;
            overflow-y: auto;
        }
        .home-indicator {
            position: absolute;
            bottom: 8px;
            left: 50%;
            transform: translateX(-50%);
            width: 134px;
            height: 5px;
            background: #000;
            border-radius: 3px;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-8">
    <div class="phone-frame">
        <div class="phone-screen">
            <div class="phone-notch"></div>
            <div class="phone-content">
                {{MOBILE_CONTENT}}
            </div>
            <div class="home-indicator"></div>
        </div>
    </div>
</body>
</html>
```

### 常用 UI 元件 (Tailwind)

#### Button 元件

```html
<!-- Primary Button -->
<button class="w-full bg-primary text-on-primary font-semibold py-3 px-6 rounded-theme
               hover:opacity-90 active:scale-[0.98] transition-all duration-150
               shadow-lg shadow-primary/25">
    按鈕文字
</button>

<!-- Secondary Button -->
<button class="w-full bg-surface text-on-surface font-medium py-3 px-6 rounded-theme
               border border-gray-200 hover:bg-gray-50 active:scale-[0.98]
               transition-all duration-150">
    次要按鈕
</button>

<!-- Outline Button -->
<button class="w-full bg-transparent text-primary font-medium py-3 px-6 rounded-theme
               border-2 border-primary hover:bg-primary/5 active:scale-[0.98]
               transition-all duration-150">
    外框按鈕
</button>

<!-- Icon Button -->
<button class="w-12 h-12 flex items-center justify-center rounded-full
               bg-surface hover:bg-gray-100 active:scale-95 transition-all">
    <svg class="w-6 h-6 text-on-surface" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
</button>
```

#### Input 元件

```html
<!-- Text Input -->
<div class="space-y-2">
    <label class="block text-sm font-medium text-gray-700">標籤</label>
    <input type="text"
           class="w-full px-4 py-3 rounded-theme border border-gray-300
                  focus:border-primary focus:ring-2 focus:ring-primary/20
                  placeholder-gray-400 transition-all outline-none"
           placeholder="請輸入...">
</div>

<!-- Input with Icon -->
<div class="relative">
    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
    </div>
    <input type="text"
           class="w-full pl-12 pr-4 py-3 rounded-theme border border-gray-300
                  focus:border-primary focus:ring-2 focus:ring-primary/20
                  placeholder-gray-400 transition-all outline-none"
           placeholder="搜尋...">
</div>

<!-- Password Input with Toggle -->
<div class="relative">
    <input type="password" id="password"
           class="w-full px-4 py-3 pr-12 rounded-theme border border-gray-300
                  focus:border-primary focus:ring-2 focus:ring-primary/20
                  placeholder-gray-400 transition-all outline-none"
           placeholder="密碼">
    <button type="button" onclick="togglePassword()"
            class="absolute inset-y-0 right-0 pr-4 flex items-center">
        <svg class="w-5 h-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        </svg>
    </button>
</div>
```

#### Card 元件

```html
<!-- Basic Card -->
<div class="bg-surface rounded-theme p-6 shadow-sm border border-gray-100">
    <h3 class="text-lg font-semibold text-on-surface">標題</h3>
    <p class="mt-2 text-gray-600">卡片內容描述文字</p>
</div>

<!-- Image Card -->
<div class="bg-surface rounded-theme overflow-hidden shadow-sm border border-gray-100">
    <img src="{{IMAGE_URL}}" alt="" class="w-full h-48 object-cover">
    <div class="p-4">
        <h3 class="font-semibold text-on-surface">標題</h3>
        <p class="mt-1 text-sm text-gray-600">描述文字</p>
        <div class="mt-4 flex items-center justify-between">
            <span class="text-primary font-bold">$99</span>
            <button class="text-sm text-primary font-medium">查看詳情</button>
        </div>
    </div>
</div>

<!-- List Item Card -->
<div class="bg-surface rounded-theme p-4 shadow-sm border border-gray-100
            flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer">
    <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
        <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
    </div>
    <div class="flex-1">
        <h4 class="font-medium text-on-surface">項目標題</h4>
        <p class="text-sm text-gray-500">副標題或描述</p>
    </div>
    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
    </svg>
</div>
```

#### Navigation 元件

```html
<!-- Top Navigation Bar -->
<nav class="bg-surface border-b border-gray-200 px-4 py-3 flex items-center justify-between">
    <button class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
    </button>
    <h1 class="text-lg font-semibold">頁面標題</h1>
    <button class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
        </svg>
    </button>
</nav>

<!-- Bottom Tab Bar -->
<nav class="fixed bottom-0 left-0 right-0 bg-surface border-t border-gray-200
            px-6 pb-6 pt-2 flex items-center justify-around">
    <button class="flex flex-col items-center gap-1 text-primary">
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span class="text-xs font-medium">首頁</span>
    </button>
    <button class="flex flex-col items-center gap-1 text-gray-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <span class="text-xs">搜尋</span>
    </button>
    <button class="flex flex-col items-center gap-1 text-gray-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        <span class="text-xs">我的</span>
    </button>
</nav>
```

---

## React 元件生成

### 專案結構

```
📁 src/
├── 📁 components/
│   ├── 📁 ui/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   └── index.ts
│   ├── 📁 layout/
│   │   ├── Header.tsx
│   │   ├── TabBar.tsx
│   │   └── Container.tsx
│   └── 📁 screens/
│       ├── LoginScreen.tsx
│       ├── HomeScreen.tsx
│       └── ProfileScreen.tsx
├── 📁 styles/
│   └── theme.ts
└── 📁 types/
    └── index.ts
```

### Theme 設定

```typescript
// styles/theme.ts
export const theme = {
  colors: {
    primary: '#6366F1',
    primaryHover: '#4F46E5',
    secondary: '#EC4899',
    background: '#FFFFFF',
    surface: '#F8FAFC',
    surfaceHover: '#F1F5F9',
    text: {
      primary: '#1F2937',
      secondary: '#6B7280',
      muted: '#9CA3AF',
      inverse: '#FFFFFF',
    },
    border: '#E5E7EB',
    error: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  borderRadius: {
    sm: '6px',
    md: '12px',
    lg: '16px',
    full: '9999px',
  },
  fontSize: {
    xs: '12px',
    sm: '14px',
    md: '16px',
    lg: '18px',
    xl: '24px',
    xxl: '32px',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  shadow: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(0, 0, 0, 0.05)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  },
} as const;

export type Theme = typeof theme;
```

### Button 元件

```tsx
// components/ui/Button.tsx
import React from 'react';
import styled, { css } from 'styled-components';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const sizeStyles = {
  sm: css`
    padding: 8px 16px;
    font-size: 14px;
    min-height: 36px;
  `,
  md: css`
    padding: 12px 24px;
    font-size: 16px;
    min-height: 44px;
  `,
  lg: css`
    padding: 16px 32px;
    font-size: 18px;
    min-height: 52px;
  `,
};

const variantStyles = {
  primary: css`
    background: ${({ theme }) => theme.colors.primary};
    color: ${({ theme }) => theme.colors.text.inverse};
    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.primaryHover};
    }
  `,
  secondary: css`
    background: ${({ theme }) => theme.colors.surface};
    color: ${({ theme }) => theme.colors.text.primary};
    border: 1px solid ${({ theme }) => theme.colors.border};
    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.surfaceHover};
    }
  `,
  outline: css`
    background: transparent;
    color: ${({ theme }) => theme.colors.primary};
    border: 2px solid ${({ theme }) => theme.colors.primary};
    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.primary}10;
    }
  `,
  ghost: css`
    background: transparent;
    color: ${({ theme }) => theme.colors.text.primary};
    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.surfaceHover};
    }
  `,
};

const StyledButton = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  width: ${({ fullWidth }) => (fullWidth ? '100%' : 'auto')};

  ${({ size = 'md' }) => sizeStyles[size]}
  ${({ variant = 'primary' }) => variantStyles[variant]}

  &:active:not(:disabled) {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  leftIcon,
  rightIcon,
  disabled,
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Spinner />
      ) : (
        <>
          {leftIcon}
          {children}
          {rightIcon}
        </>
      )}
    </StyledButton>
  );
};

const Spinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;
```

### 完整頁面範例 - 登入頁

```tsx
// components/screens/LoginScreen.tsx
import React, { useState } from 'react';
import styled from 'styled-components';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

export const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Login logic here
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <Container>
      <Header>
        <Logo>AppName</Logo>
        <Title>歡迎回來</Title>
        <Subtitle>登入以繼續使用服務</Subtitle>
      </Header>

      <Form onSubmit={handleLogin}>
        <Input
          label="電子郵件"
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<EmailIcon />}
        />

        <Input
          label="密碼"
          type="password"
          placeholder="輸入密碼"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<LockIcon />}
        />

        <ForgotPassword href="#">忘記密碼？</ForgotPassword>

        <Button type="submit" fullWidth loading={loading}>
          登入
        </Button>

        <Divider>
          <span>或</span>
        </Divider>

        <SocialButtons>
          <Button variant="outline" fullWidth leftIcon={<GoogleIcon />}>
            使用 Google 登入
          </Button>
          <Button variant="outline" fullWidth leftIcon={<AppleIcon />}>
            使用 Apple 登入
          </Button>
        </SocialButtons>
      </Form>

      <Footer>
        還沒有帳號？<SignUpLink href="#">立即註冊</SignUpLink>
      </Footer>
    </Container>
  );
};

const Container = styled.div`
  min-height: 100vh;
  padding: 48px 24px;
  display: flex;
  flex-direction: column;
  background: ${({ theme }) => theme.colors.background};
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: 40px;
`;

const Logo = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  font-size: 16px;
  color: ${({ theme }) => theme.colors.text.secondary};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const ForgotPassword = styled.a`
  align-self: flex-end;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.primary};
  text-decoration: none;
  margin-top: -8px;
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  color: ${({ theme }) => theme.colors.text.muted};
  font-size: 14px;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: ${({ theme }) => theme.colors.border};
  }
`;

const SocialButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Footer = styled.footer`
  margin-top: auto;
  text-align: center;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.text.secondary};
`;

const SignUpLink = styled.a`
  color: ${({ theme }) => theme.colors.primary};
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
`;
```

---

## Angular 元件生成

### 專案結構

```
📁 src/
├── 📁 app/
│   ├── 📁 components/
│   │   ├── 📁 ui/
│   │   │   ├── button/
│   │   │   │   ├── button.component.ts
│   │   │   │   ├── button.component.html
│   │   │   │   ├── button.component.scss
│   │   │   │   └── button.component.spec.ts
│   │   │   ├── input/
│   │   │   ├── card/
│   │   │   └── index.ts
│   │   │
│   │   └── 📁 layout/
│   │       ├── header/
│   │       ├── tab-bar/
│   │       └── container/
│   │
│   ├── 📁 pages/
│   │   ├── 📁 auth/
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── forgot-password/
│   │   │
│   │   ├── 📁 home/
│   │   ├── 📁 product/
│   │   └── 📁 profile/
│   │
│   ├── 📁 shared/
│   │   ├── 📁 models/
│   │   ├── 📁 services/
│   │   └── 📁 pipes/
│   │
│   └── 📁 styles/
│       ├── _variables.scss
│       ├── _mixins.scss
│       └── _theme.scss
│
└── 📁 assets/
    ├── 📁 icons/
    └── 📁 images/
```

### Theme 設定 (SCSS Variables)

```scss
// styles/_variables.scss
:root {
  // Colors
  --color-primary: #6366F1;
  --color-primary-hover: #4F46E5;
  --color-secondary: #EC4899;
  --color-background: #FFFFFF;
  --color-surface: #F8FAFC;
  --color-surface-hover: #F1F5F9;
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-muted: #9CA3AF;
  --color-text-inverse: #FFFFFF;
  --color-border: #E5E7EB;
  --color-error: #EF4444;
  --color-success: #10B981;
  --color-warning: #F59E0B;

  // Spacing
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;

  // Border Radius
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  // Font Size
  --font-xs: 12px;
  --font-sm: 14px;
  --font-md: 16px;
  --font-lg: 18px;
  --font-xl: 24px;
  --font-xxl: 32px;

  // Shadow
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

### Button 元件

```typescript
// components/ui/button/button.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss']
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() fullWidth = false;
  @Input() loading = false;
  @Input() disabled = false;
  @Input() type: 'button' | 'submit' | 'reset' = 'button';

  @Output() clicked = new EventEmitter<void>();

  get buttonClasses(): string {
    return [
      'app-button',
      `app-button--${this.variant}`,
      `app-button--${this.size}`,
      this.fullWidth ? 'app-button--full-width' : '',
      this.loading ? 'app-button--loading' : '',
    ].filter(Boolean).join(' ');
  }

  onClick(): void {
    if (!this.disabled && !this.loading) {
      this.clicked.emit();
    }
  }
}
```

```html
<!-- components/ui/button/button.component.html -->
<button
  [type]="type"
  [class]="buttonClasses"
  [disabled]="disabled || loading"
  (click)="onClick()"
>
  <span class="app-button__spinner" *ngIf="loading"></span>
  <ng-content *ngIf="!loading"></ng-content>
</button>
```

```scss
// components/ui/button/button.component.scss
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;

  &:active:not(:disabled) {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  // Sizes
  &--sm {
    padding: 8px 16px;
    font-size: var(--font-sm);
    min-height: 36px;
  }

  &--md {
    padding: 12px 24px;
    font-size: var(--font-md);
    min-height: 44px;
  }

  &--lg {
    padding: 16px 32px;
    font-size: var(--font-lg);
    min-height: 52px;
  }

  // Variants
  &--primary {
    background: var(--color-primary);
    color: var(--color-text-inverse);

    &:hover:not(:disabled) {
      background: var(--color-primary-hover);
    }
  }

  &--secondary {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);

    &:hover:not(:disabled) {
      background: var(--color-surface-hover);
    }
  }

  &--outline {
    background: transparent;
    color: var(--color-primary);
    border: 2px solid var(--color-primary);

    &:hover:not(:disabled) {
      background: rgba(99, 102, 241, 0.1);
    }
  }

  &--ghost {
    background: transparent;
    color: var(--color-text-primary);

    &:hover:not(:disabled) {
      background: var(--color-surface-hover);
    }
  }

  &--full-width {
    width: 100%;
  }

  // Loading spinner
  &__spinner {
    width: 20px;
    height: 20px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

### Input 元件

```typescript
// components/ui/input/input.component.ts
import { Component, Input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NG_VALUE_ACCESSOR, ControlValueAccessor } from '@angular/forms';

@Component({
  selector: 'app-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InputComponent),
      multi: true
    }
  ]
})
export class InputComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() placeholder = '';
  @Input() type: 'text' | 'email' | 'password' | 'number' = 'text';
  @Input() error = '';
  @Input() hint = '';
  @Input() required = false;

  value = '';
  showPassword = false;
  disabled = false;

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  get inputType(): string {
    if (this.type === 'password') {
      return this.showPassword ? 'text' : 'password';
    }
    return this.type;
  }

  writeValue(value: string): void {
    this.value = value || '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  onInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.value = target.value;
    this.onChange(this.value);
  }

  onBlur(): void {
    this.onTouched();
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }
}
```

```html
<!-- components/ui/input/input.component.html -->
<div class="app-input" [class.app-input--error]="error" [class.app-input--disabled]="disabled">
  <label *ngIf="label" class="app-input__label">
    {{ label }}
    <span *ngIf="required" class="app-input__required">*</span>
  </label>

  <div class="app-input__wrapper">
    <input
      [type]="inputType"
      [placeholder]="placeholder"
      [value]="value"
      [disabled]="disabled"
      (input)="onInput($event)"
      (blur)="onBlur()"
      class="app-input__field"
    />

    <button
      *ngIf="type === 'password'"
      type="button"
      class="app-input__toggle"
      (click)="togglePassword()"
    >
      <svg *ngIf="!showPassword" class="app-input__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
      <svg *ngIf="showPassword" class="app-input__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
      </svg>
    </button>
  </div>

  <span *ngIf="error" class="app-input__error">{{ error }}</span>
  <span *ngIf="hint && !error" class="app-input__hint">{{ hint }}</span>
</div>
```

```scss
// components/ui/input/input.component.scss
.app-input {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);

  &__label {
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--color-text-primary);
  }

  &__required {
    color: var(--color-error);
  }

  &__wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  &__field {
    width: 100%;
    padding: 12px 16px;
    font-size: var(--font-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-background);
    color: var(--color-text-primary);
    transition: all 0.15s ease;
    outline: none;

    &::placeholder {
      color: var(--color-text-muted);
    }

    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    &:disabled {
      background: var(--color-surface);
      cursor: not-allowed;
    }
  }

  &__toggle {
    position: absolute;
    right: 12px;
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: var(--color-text-muted);

    &:hover {
      color: var(--color-text-secondary);
    }
  }

  &__icon {
    width: 20px;
    height: 20px;
  }

  &__error {
    font-size: var(--font-sm);
    color: var(--color-error);
  }

  &__hint {
    font-size: var(--font-sm);
    color: var(--color-text-muted);
  }

  &--error &__field {
    border-color: var(--color-error);

    &:focus {
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
  }

  &--disabled {
    opacity: 0.6;
  }
}
```

### 完整頁面範例 - 登入頁

```typescript
// pages/auth/login/login.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonComponent } from '../../../components/ui/button/button.component';
import { InputComponent } from '../../../components/ui/input/input.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, InputComponent],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  email = '';
  password = '';
  isLoading = false;
  errorMessage = '';

  constructor(private router: Router) {}

  async onSubmit(): Promise<void> {
    if (!this.email || !this.password) {
      this.errorMessage = '請填寫所有欄位';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      this.router.navigate(['/home']);
    } catch (error) {
      this.errorMessage = '登入失敗，請檢查帳號密碼';
    } finally {
      this.isLoading = false;
    }
  }

  onGoogleLogin(): void {
    console.log('Google login');
  }

  onAppleLogin(): void {
    console.log('Apple login');
  }

  goToRegister(): void {
    this.router.navigate(['/register']);
  }

  goToForgotPassword(): void {
    this.router.navigate(['/forgot-password']);
  }
}
```

```html
<!-- pages/auth/login/login.component.html -->
<div class="login-page">
  <div class="login-page__container">
    <!-- Header -->
    <header class="login-page__header">
      <h1 class="login-page__logo">AppName</h1>
      <h2 class="login-page__title">歡迎回來</h2>
      <p class="login-page__subtitle">登入以繼續使用服務</p>
    </header>

    <!-- Form -->
    <form class="login-page__form" (ngSubmit)="onSubmit()">
      <app-input
        label="電子郵件"
        type="email"
        placeholder="your@email.com"
        [(ngModel)]="email"
        name="email"
        [required]="true"
      ></app-input>

      <app-input
        label="密碼"
        type="password"
        placeholder="輸入密碼"
        [(ngModel)]="password"
        name="password"
        [required]="true"
      ></app-input>

      <a class="login-page__forgot" (click)="goToForgotPassword()">
        忘記密碼？
      </a>

      <div *ngIf="errorMessage" class="login-page__error">
        {{ errorMessage }}
      </div>

      <app-button
        type="submit"
        [fullWidth]="true"
        [loading]="isLoading"
      >
        登入
      </app-button>
    </form>

    <!-- Divider -->
    <div class="login-page__divider">
      <span>或</span>
    </div>

    <!-- Social Login -->
    <div class="login-page__social">
      <app-button
        variant="outline"
        [fullWidth]="true"
        (clicked)="onGoogleLogin()"
      >
        <svg width="20" height="20" viewBox="0 0 24 24">
          <!-- Google icon SVG -->
        </svg>
        使用 Google 登入
      </app-button>

      <app-button
        variant="outline"
        [fullWidth]="true"
        (clicked)="onAppleLogin()"
      >
        <svg width="20" height="20" viewBox="0 0 24 24">
          <!-- Apple icon SVG -->
        </svg>
        使用 Apple 登入
      </app-button>
    </div>

    <!-- Footer -->
    <footer class="login-page__footer">
      還沒有帳號？
      <a (click)="goToRegister()">立即註冊</a>
    </footer>
  </div>
</div>
```

```scss
// pages/auth/login/login.component.scss
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: var(--color-background);

  &__container {
    width: 100%;
    max-width: 400px;
  }

  &__header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
  }

  &__logo {
    font-size: var(--font-xxl);
    font-weight: 700;
    color: var(--color-primary);
    margin-bottom: var(--spacing-lg);
  }

  &__title {
    font-size: var(--font-xxl);
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: var(--spacing-sm);
  }

  &__subtitle {
    font-size: var(--font-md);
    color: var(--color-text-secondary);
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  &__forgot {
    align-self: flex-end;
    font-size: var(--font-sm);
    color: var(--color-primary);
    cursor: pointer;
    margin-top: calc(var(--spacing-sm) * -1);

    &:hover {
      text-decoration: underline;
    }
  }

  &__error {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(239, 68, 68, 0.1);
    border-radius: var(--radius-sm);
    color: var(--color-error);
    font-size: var(--font-sm);
  }

  &__divider {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin: var(--spacing-lg) 0;
    color: var(--color-text-muted);
    font-size: var(--font-sm);

    &::before,
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--color-border);
    }
  }

  &__social {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  &__footer {
    text-align: center;
    margin-top: var(--spacing-xl);
    font-size: var(--font-sm);
    color: var(--color-text-secondary);

    a {
      color: var(--color-primary);
      font-weight: 600;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }
  }
}
```

### 路由配置

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./pages/auth/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () =>
      import('./pages/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    path: 'home',
    loadComponent: () =>
      import('./pages/home/home.component').then(m => m.HomeComponent),
    // canActivate: [AuthGuard]
  },
  {
    path: '**',
    redirectTo: 'login'
  }
];
```

---

## iOS SwiftUI 生成

### 完整頁面範例 - 登入頁

```swift
// LoginView.swift
import SwiftUI

struct LoginView: View {
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var showPassword = false

    var body: some View {
        ScrollView {
            VStack(spacing: 32) {
                // Header
                VStack(spacing: 8) {
                    Text("AppName")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.accentColor)

                    Text("歡迎回來")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.primary)

                    Text("登入以繼續使用服務")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 48)

                // Form
                VStack(spacing: 20) {
                    // Email Input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("電子郵件")
                            .font(.subheadline)
                            .fontWeight(.medium)

                        HStack {
                            Image(systemName: "envelope")
                                .foregroundColor(.secondary)
                            TextField("your@email.com", text: $email)
                                .textContentType(.emailAddress)
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                    }

                    // Password Input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("密碼")
                            .font(.subheadline)
                            .fontWeight(.medium)

                        HStack {
                            Image(systemName: "lock")
                                .foregroundColor(.secondary)

                            if showPassword {
                                TextField("輸入密碼", text: $password)
                            } else {
                                SecureField("輸入密碼", text: $password)
                            }

                            Button(action: { showPassword.toggle() }) {
                                Image(systemName: showPassword ? "eye.slash" : "eye")
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                    }

                    // Forgot Password
                    HStack {
                        Spacer()
                        Button("忘記密碼？") {
                            // Handle forgot password
                        }
                        .font(.subheadline)
                    }

                    // Login Button
                    Button(action: handleLogin) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Text("登入")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.accentColor)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(isLoading)

                    // Divider
                    HStack {
                        Rectangle()
                            .fill(Color(.systemGray4))
                            .frame(height: 1)
                        Text("或")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        Rectangle()
                            .fill(Color(.systemGray4))
                            .frame(height: 1)
                    }

                    // Social Login
                    VStack(spacing: 12) {
                        SocialLoginButton(
                            icon: "g.circle.fill",
                            text: "使用 Google 登入"
                        )
                        SocialLoginButton(
                            icon: "apple.logo",
                            text: "使用 Apple 登入"
                        )
                    }
                }

                Spacer()

                // Footer
                HStack(spacing: 4) {
                    Text("還沒有帳號？")
                        .foregroundColor(.secondary)
                    Button("立即註冊") {
                        // Handle sign up
                    }
                    .fontWeight(.semibold)
                }
                .font(.subheadline)
            }
            .padding(.horizontal, 24)
        }
    }

    private func handleLogin() {
        isLoading = true
        // Simulate login
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isLoading = false
        }
    }
}

struct SocialLoginButton: View {
    let icon: String
    let text: String

    var body: some View {
        Button(action: {}) {
            HStack {
                Image(systemName: icon)
                Text(text)
                    .fontWeight(.medium)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemGray6))
            .foregroundColor(.primary)
            .cornerRadius(12)
        }
    }
}

#Preview {
    LoginView()
}
```

### SwiftUI 元件庫

```swift
// Components/AppButton.swift
import SwiftUI

enum AppButtonStyle {
    case primary
    case secondary
    case outline
    case ghost
}

struct AppButton: View {
    let title: String
    let style: AppButtonStyle
    let isLoading: Bool
    let action: () -> Void

    init(
        _ title: String,
        style: AppButtonStyle = .primary,
        isLoading: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.style = style
        self.isLoading = isLoading
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: foregroundColor))
                } else {
                    Text(title)
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(backgroundColor)
            .foregroundColor(foregroundColor)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(borderColor, lineWidth: style == .outline ? 2 : 0)
            )
        }
        .disabled(isLoading)
    }

    private var backgroundColor: Color {
        switch style {
        case .primary: return .accentColor
        case .secondary: return Color(.systemGray6)
        case .outline, .ghost: return .clear
        }
    }

    private var foregroundColor: Color {
        switch style {
        case .primary: return .white
        case .secondary: return .primary
        case .outline: return .accentColor
        case .ghost: return .primary
        }
    }

    private var borderColor: Color {
        style == .outline ? .accentColor : .clear
    }
}
```

---

## Android Compose 生成

### 完整頁面範例 - 登入頁

```kotlin
// LoginScreen.kt
package com.example.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*

@Composable
fun LoginScreen(
    onLoginClick: (String, String) -> Unit,
    onForgotPasswordClick: () -> Unit,
    onSignUpClick: () -> Unit,
    onGoogleLoginClick: () -> Unit,
    onAppleLoginClick: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(modifier = Modifier.height(48.dp))

        // Header
        Text(
            text = "AppName",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = "歡迎回來",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = "登入以繼續使用服務",
            fontSize = 16.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(40.dp))

        // Email Field
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("電子郵件") },
            placeholder = { Text("your@email.com") },
            leadingIcon = {
                Icon(Icons.Outlined.Email, contentDescription = null)
            },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Password Field
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("密碼") },
            placeholder = { Text("輸入密碼") },
            leadingIcon = {
                Icon(Icons.Outlined.Lock, contentDescription = null)
            },
            trailingIcon = {
                IconButton(onClick = { passwordVisible = !passwordVisible }) {
                    Icon(
                        if (passwordVisible) Icons.Outlined.VisibilityOff
                        else Icons.Outlined.Visibility,
                        contentDescription = null
                    )
                }
            },
            visualTransformation = if (passwordVisible)
                VisualTransformation.None
            else
                PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Forgot Password
        TextButton(
            onClick = onForgotPasswordClick,
            modifier = Modifier.align(Alignment.End)
        ) {
            Text("忘記密碼？")
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Login Button
        Button(
            onClick = {
                isLoading = true
                onLoginClick(email, password)
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            shape = MaterialTheme.shapes.medium,
            enabled = !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text(
                    text = "登入",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Divider
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            HorizontalDivider(modifier = Modifier.weight(1f))
            Text(
                text = "或",
                modifier = Modifier.padding(horizontal = 16.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontSize = 14.sp
            )
            HorizontalDivider(modifier = Modifier.weight(1f))
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Social Login Buttons
        OutlinedButton(
            onClick = onGoogleLoginClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            shape = MaterialTheme.shapes.medium
        ) {
            Icon(
                Icons.Outlined.AccountCircle,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("使用 Google 登入")
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedButton(
            onClick = onAppleLoginClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            shape = MaterialTheme.shapes.medium
        ) {
            Icon(
                Icons.Outlined.Phone,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("使用 Apple 登入")
        }

        Spacer(modifier = Modifier.weight(1f))

        // Footer
        Row(
            modifier = Modifier.padding(bottom = 32.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "還沒有帳號？",
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            TextButton(onClick = onSignUpClick) {
                Text(
                    text = "立即註冊",
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}
```

---

## SVG 視覺稿生成

### SVG UI Mockup 結構

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 390 844" width="390" height="844">
  <defs>
    <!-- 定義可重用的樣式 -->
    <style>
      .background { fill: #FFFFFF; }
      .primary { fill: #6366F1; }
      .text-primary { fill: #1F2937; font-family: system-ui, sans-serif; }
      .text-secondary { fill: #6B7280; font-family: system-ui, sans-serif; }
      .surface { fill: #F8FAFC; }
      .border { stroke: #E5E7EB; stroke-width: 1; fill: none; }
    </style>

    <!-- 陰影效果 -->
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.1"/>
    </filter>

    <!-- 圓角矩形 -->
    <rect id="button" width="342" height="52" rx="12"/>
    <rect id="input" width="342" height="52" rx="12"/>
    <rect id="card" width="342" height="auto" rx="16"/>
  </defs>

  <!-- 背景 -->
  <rect class="background" width="390" height="844"/>

  <!-- Status Bar -->
  <g transform="translate(0, 0)">
    <rect fill="#FFFFFF" width="390" height="44"/>
    <text x="24" y="28" class="text-primary" font-size="14" font-weight="600">9:41</text>
    <!-- 電池、訊號等圖示 -->
  </g>

  <!-- 內容區域 -->
  <g transform="translate(24, 100)">
    <!-- Logo -->
    <text x="171" y="0" class="text-primary" font-size="28" font-weight="700"
          text-anchor="middle" fill="#6366F1">AppName</text>

    <!-- 標題 -->
    <text x="171" y="50" class="text-primary" font-size="28" font-weight="700"
          text-anchor="middle">歡迎回來</text>
    <text x="171" y="78" class="text-secondary" font-size="16"
          text-anchor="middle">登入以繼續使用服務</text>

    <!-- Email Input -->
    <g transform="translate(0, 120)">
      <text x="0" y="0" class="text-primary" font-size="14" font-weight="500">電子郵件</text>
      <rect x="0" y="12" width="342" height="52" rx="12" class="surface"/>
      <rect x="0" y="12" width="342" height="52" rx="12" class="border"/>
      <text x="48" y="46" class="text-secondary" font-size="16">your@email.com</text>
    </g>

    <!-- Password Input -->
    <g transform="translate(0, 210)">
      <text x="0" y="0" class="text-primary" font-size="14" font-weight="500">密碼</text>
      <rect x="0" y="12" width="342" height="52" rx="12" class="surface"/>
      <rect x="0" y="12" width="342" height="52" rx="12" class="border"/>
      <text x="48" y="46" class="text-secondary" font-size="16">輸入密碼</text>
    </g>

    <!-- Forgot Password -->
    <text x="342" y="290" class="primary" font-size="14" text-anchor="end" fill="#6366F1">忘記密碼？</text>

    <!-- Login Button -->
    <g transform="translate(0, 320)">
      <rect width="342" height="52" rx="12" fill="#6366F1" filter="url(#shadow)"/>
      <text x="171" y="32" fill="#FFFFFF" font-size="16" font-weight="600"
            text-anchor="middle">登入</text>
    </g>

    <!-- Divider -->
    <g transform="translate(0, 400)">
      <line x1="0" y1="0" x2="140" y2="0" stroke="#E5E7EB"/>
      <text x="171" y="5" class="text-secondary" font-size="14" text-anchor="middle">或</text>
      <line x1="202" y1="0" x2="342" y2="0" stroke="#E5E7EB"/>
    </g>

    <!-- Social Buttons -->
    <g transform="translate(0, 440)">
      <rect width="342" height="52" rx="12" class="surface"/>
      <rect width="342" height="52" rx="12" class="border"/>
      <text x="171" y="32" class="text-primary" font-size="16" font-weight="500"
            text-anchor="middle">使用 Google 登入</text>
    </g>

    <g transform="translate(0, 504)">
      <rect width="342" height="52" rx="12" class="surface"/>
      <rect width="342" height="52" rx="12" class="border"/>
      <text x="171" y="32" class="text-primary" font-size="16" font-weight="500"
            text-anchor="middle">使用 Apple 登入</text>
    </g>
  </g>

  <!-- Footer -->
  <g transform="translate(0, 780)">
    <text x="195" y="0" class="text-secondary" font-size="14" text-anchor="middle">
      還沒有帳號？<tspan fill="#6366F1" font-weight="600">立即註冊</tspan>
    </text>
  </g>

  <!-- Home Indicator -->
  <rect x="128" y="822" width="134" height="5" rx="3" fill="#000000"/>
</svg>
```

---

## Figma 匯入 JSON

### Figma Plugin API 格式

```json
{
  "name": "Login Screen",
  "type": "FRAME",
  "width": 390,
  "height": 844,
  "fills": [{"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1}}],
  "children": [
    {
      "name": "Header",
      "type": "FRAME",
      "layoutMode": "VERTICAL",
      "itemSpacing": 8,
      "paddingTop": 48,
      "primaryAxisAlignItems": "CENTER",
      "children": [
        {
          "name": "Logo",
          "type": "TEXT",
          "characters": "AppName",
          "fontSize": 28,
          "fontWeight": 700,
          "fills": [{"type": "SOLID", "color": {"r": 0.388, "g": 0.4, "b": 0.945}}]
        },
        {
          "name": "Title",
          "type": "TEXT",
          "characters": "歡迎回來",
          "fontSize": 28,
          "fontWeight": 700,
          "fills": [{"type": "SOLID", "color": {"r": 0.122, "g": 0.161, "b": 0.216}}]
        },
        {
          "name": "Subtitle",
          "type": "TEXT",
          "characters": "登入以繼續使用服務",
          "fontSize": 16,
          "fills": [{"type": "SOLID", "color": {"r": 0.42, "g": 0.451, "b": 0.502}}]
        }
      ]
    },
    {
      "name": "Form",
      "type": "FRAME",
      "layoutMode": "VERTICAL",
      "itemSpacing": 20,
      "paddingLeft": 24,
      "paddingRight": 24,
      "children": [
        {
          "name": "Email Input",
          "type": "COMPONENT",
          "componentId": "input-field",
          "overrides": {
            "label": "電子郵件",
            "placeholder": "your@email.com",
            "icon": "email"
          }
        },
        {
          "name": "Password Input",
          "type": "COMPONENT",
          "componentId": "input-field",
          "overrides": {
            "label": "密碼",
            "placeholder": "輸入密碼",
            "icon": "lock",
            "type": "password"
          }
        },
        {
          "name": "Login Button",
          "type": "COMPONENT",
          "componentId": "button-primary",
          "overrides": {
            "label": "登入"
          }
        }
      ]
    }
  ]
}
```

---

## 完整頁面範本庫

### 可生成的頁面類型

```
📱 認證相關
├── 登入頁 (Login)
├── 註冊頁 (Sign Up)
├── 忘記密碼 (Forgot Password)
├── 重設密碼 (Reset Password)
├── OTP 驗證 (OTP Verification)
└── 歡迎/引導頁 (Onboarding)

🏠 首頁相關
├── 儀表板 (Dashboard)
├── 首頁摘要 (Home Feed)
├── 探索頁 (Explore/Discover)
└── 搜尋結果 (Search Results)

📋 列表相關
├── 商品列表 (Product List)
├── 文章列表 (Article List)
├── 卡片網格 (Card Grid)
├── 訊息列表 (Message List)
└── 通知列表 (Notification List)

📄 詳細頁相關
├── 商品詳情 (Product Detail)
├── 文章詳情 (Article Detail)
├── 個人檔案 (Profile)
└── 設定頁 (Settings)

🛒 電商相關
├── 購物車 (Shopping Cart)
├── 結帳頁 (Checkout)
├── 訂單確認 (Order Confirmation)
├── 訂單列表 (Order History)
└── 訂單詳情 (Order Detail)

📝 表單相關
├── 資料編輯 (Edit Form)
├── 多步驟表單 (Multi-step Form)
├── 篩選器 (Filter)
└── 問卷調查 (Survey)

💬 社群相關
├── 動態牆 (Feed)
├── 貼文詳情 (Post Detail)
├── 聊天室 (Chat)
├── 評論區 (Comments)
└── 追蹤列表 (Following/Followers)

⚙️ 狀態頁面
├── 空狀態 (Empty State)
├── 載入中 (Loading)
├── 錯誤頁 (Error)
├── 成功頁 (Success)
└── 404 找不到 (Not Found)
```

### 頁面生成請求格式

```markdown
## UI 生成請求

**頁面類型:** 登入頁
**平台:** iOS / Android / Web
**輸出格式:** HTML + Tailwind / React / SwiftUI / Compose

### 風格設定
- 主色: #6366F1
- 風格: 現代簡約
- 圓角: 中等 (12px)
- 密度: 標準

### 功能需求
- [x] Email 登入
- [x] 密碼輸入 (含顯示/隱藏)
- [x] 忘記密碼連結
- [x] Google 登入
- [x] Apple 登入
- [x] 註冊連結
- [ ] 記住我選項
- [ ] 手機號碼登入

### 特殊要求
- 深色模式支援
- 表單驗證
- 載入狀態
```

---

## 生成提示詞模板

### 基礎生成提示詞

```
請幫我生成 [頁面類型] 的 UI，規格如下：

平台: [iOS/Android/Web/全平台]
輸出格式: [HTML+Tailwind/React/SwiftUI/Compose/SVG]

設計風格:
- 主色: [色碼]
- 風格: [現代/經典/活潑/專業]
- 圓角: [小/中/大/全圓]

功能需求:
- [功能1]
- [功能2]
- [功能3]

請產生完整可執行的程式碼。
```

### 進階生成提示詞 (含風格萃取)

```
請根據以下萃取的風格，生成 [頁面類型] 的 UI：

## 已萃取風格
[貼上 style-extraction 的結果]

## 頁面需求
- 頁面類型: [類型]
- 平台: [平台]
- 輸出格式: [格式]

## 功能清單
- [功能1]
- [功能2]

請確保:
1. 使用萃取的色彩配置
2. 應用萃取的字型規格
3. 採用萃取的圓角/陰影效果
4. 維持整體風格一致性

產生完整可執行的程式碼。
```

### 批次生成提示詞

```
請幫我生成以下多個頁面的 UI，保持風格一致：

共用風格:
- 主色: #6366F1
- 風格: 現代簡約
- 圓角: 12px

輸出格式: React + Styled Components

頁面清單:
1. 登入頁 - 含 Email/密碼、社群登入
2. 註冊頁 - 三步驟流程
3. 首頁 - 儀表板樣式
4. 個人檔案 - 含編輯功能

請為每個頁面產生獨立的元件檔案。
```

---

## 生成檢查清單

```
UI 生成品質檢查

□ 視覺一致性
  □ 色彩符合設計系統
  □ 字型大小/粗細一致
  □ 間距符合規範
  □ 圓角統一

□ 功能完整性
  □ 所有需求功能皆有對應 UI
  □ 互動狀態完整 (hover/focus/active/disabled)
  □ 空狀態/載入/錯誤狀態
  □ 表單驗證回饋

□ 響應式/適應性
  □ 不同螢幕尺寸適配
  □ 安全區域處理 (iOS notch)
  □ 橫向模式考量

□ 無障礙
  □ 對比度符合 WCAG
  □ 觸控目標大小 ≥ 44pt
  □ 語義化標籤

□ 程式碼品質
  □ 可直接執行
  □ 命名清晰
  □ 結構合理
  □ 無錯誤警告
```
