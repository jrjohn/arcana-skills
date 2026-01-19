# Settings Screens Generation Guide

當生成設定主頁 (SCR-SETTING-001) 時，**必須同時生成**所有設定列項目對應的子畫面。

---

## 強制規則

### 1. 禁止使用 Alert

```html
<!-- ❌ 禁止 -->
<button onclick="alert('個人資料')">個人資料</button>

<!-- ✅ 正確 -->
<button onclick="location.href='SCR-SETTING-002-profile.html'">個人資料</button>
```

### 2. 設定列必須導航到實際畫面

每個帶有 chevron (>) 圖示的設定列，都必須有對應的目標畫面。

---

## 標準設定子畫面清單

| ID | 名稱 | 檔案名稱 | 觸發行 |
|----|------|----------|--------|
| SCR-SETTING-002 | 個人資料 | SCR-SETTING-002-profile.html | 個人資料 |
| SCR-SETTING-003 | 帳號安全 | SCR-SETTING-003-security.html | 帳號安全 |
| SCR-SETTING-004 | 隱私設定 | SCR-SETTING-004-privacy.html | 隱私設定 |
| SCR-SETTING-005 | 資料管理 | SCR-SETTING-005-data.html | 資料管理 |
| SCR-SETTING-006 | 通知設定 | SCR-SETTING-006-notification.html | 通知設定 |
| SCR-SETTING-007 | 主題外觀 | SCR-SETTING-007-appearance.html | 主題外觀 |
| SCR-SETTING-008 | 語音設定 | SCR-SETTING-008-voice.html | 語音設定 |
| SCR-SETTING-009 | 語言設定 | SCR-SETTING-009-language.html | 語言設定 |
| SCR-SETTING-010 | 服務條款 | SCR-SETTING-010-terms.html | 服務條款 |
| SCR-SETTING-011 | 隱私政策 | SCR-SETTING-011-privacy-policy.html | 隱私權政策 |
| SCR-SETTING-012 | 關於 App | SCR-SETTING-012-about.html | 關於/版本資訊 |

---

## 設定行文字與目標畫面對照

### 帳號類
| 設定行文字 | 目標畫面 ID | 說明 |
|-----------|-------------|------|
| 個人資料 | SCR-SETTING-002 | 編輯用戶基本資料 |
| 編輯個人資料 | SCR-SETTING-002 | 同上 |
| 帳號安全 | SCR-SETTING-003 | 密碼、雙重驗證 |
| 變更密碼 | SCR-SETTING-003 | 同上 |
| 隱私設定 | SCR-SETTING-004 | 資料分享、可見性 |
| 資料管理 | SCR-SETTING-005 | 下載/刪除資料 |

### 偏好設定類
| 設定行文字 | 目標畫面 ID | 說明 |
|-----------|-------------|------|
| 通知設定 | SCR-SETTING-006 | 推播通知開關 |
| 通知 | SCR-SETTING-006 | 同上 |
| 主題外觀 | SCR-SETTING-007 | 淺色/深色模式 |
| 深色模式 | SCR-SETTING-007 | 同上 |
| 語音設定 | SCR-SETTING-008 | 發音速度、音量 |
| 語言設定 | SCR-SETTING-009 | 介面語言 |
| 語言 | SCR-SETTING-009 | 同上 |

### 法律與關於類
| 設定行文字 | 目標畫面 ID | 說明 |
|-----------|-------------|------|
| 服務條款 | SCR-SETTING-010 | 法律文件 |
| 使用條款 | SCR-SETTING-010 | 同上 |
| 隱私權政策 | SCR-SETTING-011 | 法律文件 |
| 隱私政策 | SCR-SETTING-011 | 同上 |
| 關於 | SCR-SETTING-012 | App 資訊 |
| 版本資訊 | SCR-SETTING-012 | 同上 |
| 關於我們 | SCR-SETTING-012 | 同上 |

---

## 生成流程

### Step 1: 生成設定主頁

建立 `SCR-SETTING-001-settings.html`，列出所有設定項目。

### Step 2: 識別需要的子畫面

根據設定行文字，對照上表確定需要生成的子畫面。

### Step 3: 生成所有子畫面

為每個設定行建立對應的詳情畫面。

### Step 4: 連結設定行到子畫面

```html
<!-- 設定主頁中 -->
<button onclick="location.href='SCR-SETTING-002-profile.html'"
        class="w-full px-5 py-4 flex items-center justify-between hover:bg-slate-50 transition">
  <div class="flex items-center gap-3">
    <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
      <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    </div>
    <span class="text-gray-700 font-medium">個人資料</span>
  </div>
  <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
  </svg>
</button>
```

---

## 子畫面模板

### SCR-SETTING-002 個人資料編輯

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1194, height=834, initial-scale=1.0">
  <title>個人資料 - VocabKids</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="../shared/vocabkids-theme.css">
</head>
<body class="bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100">
  <div class="w-[1194px] h-[834px] mx-auto relative overflow-hidden flex flex-col">
    <!-- Header -->
    <header class="bg-white/90 backdrop-blur-lg border-b border-slate-200 px-8 py-4 flex-shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button onclick="location.href='SCR-SETTING-001-settings.html'" class="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition">
            <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <h1 class="text-2xl font-bold text-gray-800">個人資料</h1>
        </div>
        <button onclick="alert('已儲存')" class="px-5 py-2.5 bg-cyan-500 text-white rounded-xl font-medium hover:bg-cyan-600 transition">
          儲存
        </button>
      </div>
    </header>

    <!-- Content -->
    <main class="flex-1 overflow-auto p-6">
      <div class="max-w-[600px] mx-auto space-y-6">
        <!-- Avatar Section -->
        <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 text-center">
          <div class="w-24 h-24 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white font-bold text-4xl mx-auto mb-4">
            小
          </div>
          <button onclick="alert('更換頭像')" class="text-cyan-600 font-medium">更換頭像</button>
        </div>

        <!-- Form Fields -->
        <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">姓名</label>
            <input type="text" value="小明" class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">Email</label>
            <input type="email" value="student@vocabkids.com" class="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50" disabled>
            <p class="text-xs text-gray-400 mt-1">Email 無法修改</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">年級</label>
            <select class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 transition">
              <option>一年級</option>
              <option>二年級</option>
              <option selected>三年級</option>
              <option>四年級</option>
              <option>五年級</option>
              <option>六年級</option>
            </select>
          </div>
        </div>
      </div>
    </main>
  </div>
  <script src="../shared/notify-parent.js"></script>
</body>
</html>
```

### SCR-SETTING-006 通知設定

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1194, height=834, initial-scale=1.0">
  <title>通知設定 - VocabKids</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100">
  <div class="w-[1194px] h-[834px] mx-auto relative overflow-hidden flex flex-col">
    <header class="bg-white/90 backdrop-blur-lg border-b border-slate-200 px-8 py-4 flex-shrink-0">
      <div class="flex items-center gap-4">
        <button onclick="location.href='SCR-SETTING-001-settings.html'" class="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition">
          <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-800">通知設定</h1>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6">
      <div class="max-w-[600px] mx-auto space-y-6">
        <!-- Master Toggle -->
        <div class="bg-white rounded-2xl p-5 shadow-lg border border-gray-100">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-bold text-gray-800">推播通知</h3>
              <p class="text-sm text-gray-500">開啟以接收所有通知</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked class="sr-only peer">
              <div class="w-14 h-8 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-cyan-500"></div>
            </label>
          </div>
        </div>

        <!-- Notification Types -->
        <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="font-bold text-gray-800">通知類型</h3>
          </div>
          <div class="divide-y divide-gray-100">
            <div class="px-5 py-4 flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-700">學習提醒</p>
                <p class="text-sm text-gray-400">每日學習時間到時提醒</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" checked class="sr-only peer">
                <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>
            <div class="px-5 py-4 flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-700">成就通知</p>
                <p class="text-sm text-gray-400">獲得成就時通知</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" checked class="sr-only peer">
                <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>
            <div class="px-5 py-4 flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-700">系統公告</p>
                <p class="text-sm text-gray-400">App 更新與重要通知</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" class="sr-only peer">
                <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-1 after:left-1 after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
  <script src="../shared/notify-parent.js"></script>
</body>
</html>
```

### SCR-SETTING-007 主題外觀

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1194, height=834, initial-scale=1.0">
  <title>主題外觀 - VocabKids</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100">
  <div class="w-[1194px] h-[834px] mx-auto relative overflow-hidden flex flex-col">
    <header class="bg-white/90 backdrop-blur-lg border-b border-slate-200 px-8 py-4 flex-shrink-0">
      <div class="flex items-center gap-4">
        <button onclick="location.href='SCR-SETTING-001-settings.html'" class="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition">
          <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-800">主題外觀</h1>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6">
      <div class="max-w-[600px] mx-auto space-y-6">
        <!-- Theme Selection -->
        <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="font-bold text-gray-800">主題模式</h3>
          </div>
          <div class="p-5 space-y-3">
            <label class="flex items-center gap-4 p-4 rounded-xl border-2 border-cyan-500 bg-cyan-50 cursor-pointer">
              <input type="radio" name="theme" checked class="w-5 h-5 text-cyan-500">
              <div class="w-12 h-12 rounded-xl bg-white border border-gray-200 flex items-center justify-center">☀️</div>
              <div>
                <p class="font-medium text-gray-800">淺色模式</p>
                <p class="text-sm text-gray-500">明亮的白色背景</p>
              </div>
            </label>
            <label class="flex items-center gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-gray-300 cursor-pointer">
              <input type="radio" name="theme" class="w-5 h-5 text-cyan-500">
              <div class="w-12 h-12 rounded-xl bg-gray-800 flex items-center justify-center">🌙</div>
              <div>
                <p class="font-medium text-gray-800">深色模式</p>
                <p class="text-sm text-gray-500">護眼的深色背景</p>
              </div>
            </label>
            <label class="flex items-center gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-gray-300 cursor-pointer">
              <input type="radio" name="theme" class="w-5 h-5 text-cyan-500">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-white to-gray-800 flex items-center justify-center">⚙️</div>
              <div>
                <p class="font-medium text-gray-800">跟隨系統</p>
                <p class="text-sm text-gray-500">自動配合系統設定</p>
              </div>
            </label>
          </div>
        </div>
      </div>
    </main>
  </div>
  <script src="../shared/notify-parent.js"></script>
</body>
</html>
```

---

## 雙平台支援 (iPad + iPhone)

### 強制規則

當專案同時支援 iPad 和 iPhone 時，**必須同時生成兩個版本的設定子畫面**：

```
04-ui-flow/
├── setting/                    # iPad 版本 (1194×834)
│   ├── SCR-SETTING-001-settings.html
│   ├── SCR-SETTING-002-profile.html
│   └── ...
└── iphone/                     # iPhone 版本 (393×852)
    ├── SCR-SETTING-001-settings.html
    ├── SCR-SETTING-002-profile.html
    └── ...
```

### 關鍵差異

| 項目 | iPad | iPhone |
|------|------|--------|
| 視窗尺寸 | 1194×834 | 393×852 |
| 字型大小 | 較大 | 較小 |
| 間距 | 較寬 | 較緊 |
| CSS 路徑 | `../shared/` | `../../shared/` |

### 驗證腳本

生成後必須執行兩個版本的導航測試：

```bash
# iPad 版本測試
python test-settings-navigation.py

# iPhone 版本測試
python test-iphone-settings-navigation.py
```

---

## 驗證檢查

生成設定畫面後，執行以下驗證：

```bash
node validate-navigation.js setting/
node validate-navigation.js iphone/
```

確保：
- **兩個版本**的所有設定行都有 `onclick` 導航
- 所有目標畫面都存在（iPad 和 iPhone 版本）
- 沒有使用 `alert()` 作為設定行的動作

---

## 版本記錄

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| 1.1 | 2026/01/09 | 新增雙平台支援 (iPad + iPhone) 章節 |
| 1.0 | 2026/01 | 初版建立 |
