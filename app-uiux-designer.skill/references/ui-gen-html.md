# HTML/Tailwind UI 生成參考

## 基礎模板

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
                    },
                    borderRadius: { 'theme': '{{BORDER_RADIUS}}' }
                }
            }
        }
    </script>
</head>
<body class="bg-background min-h-screen">
    {{CONTENT}}
</body>
</html>
```

## 手機框架模板

```html
<style>
    .phone-frame {
        width: 390px; height: 844px;
        background: #000; border-radius: 50px;
        padding: 12px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    .phone-screen {
        width: 100%; height: 100%;
        background: #fff; border-radius: 40px;
        overflow: hidden; position: relative;
    }
    .phone-notch {
        position: absolute; top: 0; left: 50%;
        transform: translateX(-50%);
        width: 150px; height: 34px;
        background: #000; border-radius: 0 0 20px 20px;
        z-index: 100;
    }
    .phone-content { padding-top: 44px; height: 100%; overflow-y: auto; }
    .home-indicator {
        position: absolute; bottom: 8px; left: 50%;
        transform: translateX(-50%);
        width: 134px; height: 5px;
        background: #000; border-radius: 3px;
    }
</style>
```

---

## UI 元件

### Button

```html
<!-- Primary -->
<button class="w-full bg-primary text-white font-semibold py-3 px-6 rounded-xl
               hover:opacity-90 active:scale-[0.98] transition-all shadow-lg shadow-primary/25">
    按鈕文字
</button>

<!-- Secondary -->
<button class="w-full bg-surface text-gray-800 font-medium py-3 px-6 rounded-xl
               border border-gray-200 hover:bg-gray-50 active:scale-[0.98] transition-all">
    次要按鈕
</button>

<!-- Outline -->
<button class="w-full bg-transparent text-primary font-medium py-3 px-6 rounded-xl
               border-2 border-primary hover:bg-primary/5 active:scale-[0.98] transition-all">
    外框按鈕
</button>

<!-- Icon Button -->
<button class="w-12 h-12 flex items-center justify-center rounded-full
               bg-surface hover:bg-gray-100 active:scale-95 transition-all">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
</button>
```

### Input

```html
<!-- Basic Input -->
<div class="space-y-2">
    <label class="block text-sm font-medium text-gray-700">標籤</label>
    <input type="text"
           class="w-full px-4 py-3 rounded-xl border border-gray-300
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
           class="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-300
                  focus:border-primary focus:ring-2 focus:ring-primary/20
                  placeholder-gray-400 transition-all outline-none"
           placeholder="搜尋...">
</div>

<!-- Password with Toggle -->
<div class="relative">
    <input type="password" id="password"
           class="w-full px-4 py-3 pr-12 rounded-xl border border-gray-300
                  focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none"
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

### Card

```html
<!-- Basic Card -->
<div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
    <h3 class="text-lg font-semibold">標題</h3>
    <p class="mt-2 text-gray-600">卡片內容描述文字</p>
</div>

<!-- Image Card -->
<div class="bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100">
    <img src="{{IMAGE_URL}}" alt="" class="w-full h-48 object-cover">
    <div class="p-4">
        <h3 class="font-semibold">標題</h3>
        <p class="mt-1 text-sm text-gray-600">描述文字</p>
        <div class="mt-4 flex items-center justify-between">
            <span class="text-primary font-bold">$99</span>
            <button class="text-sm text-primary font-medium">查看詳情</button>
        </div>
    </div>
</div>

<!-- List Item Card -->
<div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100
            flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer">
    <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
        <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
    </div>
    <div class="flex-1">
        <h4 class="font-medium">項目標題</h4>
        <p class="text-sm text-gray-500">副標題或描述</p>
    </div>
    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
    </svg>
</div>
```

---

## 導航元件

### Top Navigation Bar

```html
<nav class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
    <button onclick="history.back()" class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
    </button>
    <h1 class="text-lg font-semibold">頁面標題</h1>
    <button class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 5v.01M12 12v.01M12 19v.01"/>
        </svg>
    </button>
</nav>
```

### Bottom Tab Bar

```html
<nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200
            px-6 pb-6 pt-2 flex items-center justify-around">
    <a href="../main/home.html" class="flex flex-col items-center gap-1 text-primary">
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span class="text-xs font-medium">首頁</span>
    </a>
    <a href="../main/explore.html" class="flex flex-col items-center gap-1 text-gray-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <span class="text-xs">搜尋</span>
    </a>
    <a href="../main/profile.html" class="flex flex-col items-center gap-1 text-gray-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        <span class="text-xs">我的</span>
    </a>
</nav>
```

---

## 導航 JavaScript

```javascript
// shared/navigation.js

function goBack() {
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        history.back();
    } else {
        location.href = '../index.html';
    }
}

function navigateTo(path) {
    location.href = path;
}

function nextOnboardingStep(currentStep, totalSteps) {
    if (currentStep < totalSteps) {
        location.href = `step-${currentStep + 1}.html`;
    } else {
        location.href = '../main/home.html';
    }
}

function skipOnboarding() {
    location.href = '../main/home.html';
}

// Tab Bar 高亮當前頁面
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('[data-tab]').forEach(tab => {
        if (currentPath.includes(tab.dataset.tab)) {
            tab.classList.add('text-primary');
            tab.classList.remove('text-gray-400');
        }
    });
});
```

---

## index.html 入口頁模板

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}} - UI Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <header class="text-center mb-12">
            <h1 class="text-4xl font-bold text-gray-900 mb-2">{{PROJECT_NAME}}</h1>
            <p class="text-gray-600">UI/UX Preview - 點擊任一畫面開始瀏覽</p>
            <div class="mt-4 flex justify-center gap-4">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {{SCREEN_COUNT}} 個畫面
                </span>
            </div>
        </header>

        <!-- Quick Start -->
        <section class="mb-12">
            <h2 class="text-xl font-semibold mb-4">快速開始</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a href="auth/login.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md">
                    <h3 class="font-semibold">從登入開始</h3>
                    <p class="text-sm text-gray-500">體驗完整認證流程</p>
                </a>
                <a href="onboard/step-1.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md">
                    <h3 class="font-semibold">從引導流程開始</h3>
                    <p class="text-sm text-gray-500">新用戶體驗</p>
                </a>
                <a href="main/home.html" class="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md">
                    <h3 class="font-semibold">直接進入首頁</h3>
                    <p class="text-sm text-gray-500">瀏覽主要功能</p>
                </a>
            </div>
        </section>

        <!-- Screen List -->
        <section>
            <h2 class="text-xl font-semibold mb-4">所有畫面</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                <!-- 列出所有頁面縮圖 -->
            </div>
        </section>
    </div>
</body>
</html>
```

---

## index.html Device-Aware Screen Links (強制規則)

### ⚠️ 重要：禁止使用硬編碼連結

在 `index.html` 中的畫面連結**必須**是 device-aware，根據選擇的裝置 (iPad/iPhone) 導向對應的畫面。

### 錯誤寫法 (禁止)

```html
<!-- ❌ WRONG - 硬編碼連結，無法根據裝置切換 -->
<a href="device-preview.html?screen=auth/SCR-AUTH-001-login.html" class="screen-link">
  SCR-AUTH-001 登入頁
</a>
```

### 正確寫法 (必須)

```html
<!-- ✅ CORRECT - Device-aware 連結 -->
<div onclick="openScreen('auth/SCR-AUTH-001-login.html', 'iphone/SCR-AUTH-001-login.html')"
     class="screen-link cursor-pointer">
  SCR-AUTH-001 登入頁
</div>
```

### 必要的 JavaScript 函數

```javascript
// 必須在 index.html 中包含此函數
let currentDevice = 'iphone'; // 預設裝置

function switchDevice(device) {
  currentDevice = device;
  // Update toggle button states...
}

/**
 * Device-aware screen navigation
 * @param {string} ipadPath - iPad screen path (e.g., 'auth/SCR-AUTH-001.html')
 * @param {string} iphonePath - iPhone screen path (e.g., 'iphone/SCR-AUTH-001.html')
 */
function openScreen(ipadPath, iphonePath) {
  const screenPath = currentDevice === 'iphone' ? iphonePath : ipadPath;
  window.location.href = 'device-preview.html?screen=' + screenPath;
}
```

### 連結格式對照表

| 模組 | iPad Path | iPhone Path |
|------|-----------|-------------|
| AUTH | `auth/SCR-AUTH-{NNN}-{name}.html` | `iphone/SCR-AUTH-{NNN}-{name}.html` |
| VOCAB | `vocab/SCR-VOCAB-{NNN}-{name}.html` | `iphone/SCR-VOCAB-{NNN}-{name}.html` |
| TRAIN | `train/SCR-TRAIN-{NNN}-{name}.html` | `iphone/SCR-TRAIN-{NNN}-{name}.html` |
| HOME | `home/SCR-HOME-{NNN}-{name}.html` | `iphone/SCR-HOME-{NNN}-{name}.html` |
| PROG | `report/SCR-PROG-{NNN}-{name}.html` | `iphone/SCR-PROG-{NNN}-{name}.html` |
| SETTING | `setting/SCR-SETTING-{NNN}-{name}.html` | `iphone/SCR-SETTING-{NNN}-{name}.html` |

### 驗證檢查

產出 index.html 後，執行以下驗證：

```bash
# 檢查是否有硬編碼連結 (應該回傳 0)
grep -c 'href="device-preview.html?screen=' index.html

# 檢查 openScreen 函數是否存在 (應該回傳 1+)
grep -c 'function openScreen' index.html
```
