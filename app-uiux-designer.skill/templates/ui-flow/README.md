# UI Flow Template

Enterprise-grade UI Flow 產出模板，提供完整的互動式原型導覽系統。

---

## Pre-Generation Checklist (生成前必檢清單)

### 1. 畫面清單確認

在生成 UI Flow 之前，必須先確認所有畫面已規劃完成：

| 檢查項目 | 必須 | 說明 |
|----------|------|------|
| 所有 SDD 中的 SCR-* 已列出 | ★★★ | 確保每個需求都有對應畫面 |
| Tab Bar 的每個 Tab 有對應畫面 | ★★★ | 例：首頁、搜尋、通知、我的 |
| 表單 submit 有 success/error 畫面 | ★★★ | 表單提交需有回饋畫面 |
| 列表項目 click 有 detail 畫面 | ★★★ | 列表項目需有詳情頁 |
| Modal/Popup 有對應 trigger 按鈕 | ★★☆ | 彈窗需有觸發機制 |

### 2. 導航流程確認

```
✅ 必須確認的導航流向：

Login ──→ Dashboard (成功)
     ──→ Error State (失敗)
     ──→ Forgot Password
     ──→ Register

Register ──→ Verification
        ──→ Error State

Dashboard ──→ Feature Pages (via Tab Bar)
         ──→ Profile
         ──→ Settings
         ──→ Notifications

Settings ──→ Sub-settings (每個選項)
        ──→ Logout → Login

Every Screen ──→ Back (除 Login/Dashboard)
```

### 3. 可點擊元素映射表 (Critical)

**生成任何畫面前，必須填寫此映射表：**

| 來源畫面 | 可點擊元素 | 目標畫面 | 驗證狀態 |
|----------|-----------|----------|----------|
| SCR-AUTH-001 | 登入按鈕 | SCR-DASH-001 | ☐ |
| SCR-AUTH-001 | 忘記密碼連結 | SCR-AUTH-003 | ☐ |
| SCR-AUTH-001 | 註冊連結 | SCR-AUTH-002 | ☐ |
| SCR-DASH-001 | Tab: 首頁 | SCR-DASH-001 | ☐ |
| SCR-DASH-001 | Tab: 搜尋 | SCR-SEARCH-001 | ☐ |
| SCR-DASH-001 | Tab: 通知 | SCR-NOTIFY-001 | ☐ |
| SCR-DASH-001 | Tab: 我的 | SCR-PROFILE-001 | ☐ |
| ... | ... | ... | ☐ |

### 4. 模板使用確認

從 `templates/screen-types/` 複製對應模板：

| 畫面類型 | 模板路徑 | 必要導航 |
|----------|----------|----------|
| 登入頁 | `auth/login.html` | → Dashboard, → Register, → Forgot Password |
| 註冊頁 | `auth/register.html` | → Verification, ← Login |
| 列表頁 | `common/list-page.html` | → Detail, Tab Bar |
| 詳情頁 | `common/detail-page.html` | ← Back, → Edit |
| 表單頁 | `common/form-page.html` | → Success/Error, ← Cancel |
| 設定頁 | `common/settings.html` | → Sub-settings, → Logout |
| Dashboard | `common/dashboard.html` | Tab Bar, → Features |
| Profile | `common/profile.html` | Tab Bar, → Settings, → Edit |
| 搜尋頁 | `common/search.html` | Tab Bar, → Results |
| Onboarding | `onboarding/onboarding.html` | → Login/Register |
| 空狀態 | `states/empty-state.html` | → Create Action |
| 載入中 | `states/loading-state.html` | 自動跳轉 |
| 錯誤狀態 | `states/error-state.html` | → Retry, ← Back |
| 成功狀態 | `states/success-state.html` | → Home, → Next Action |

### 5. 禁止事項 (生成前確認)

| 禁止項目 | 原因 | 檢查方式 |
|----------|------|----------|
| `onclick=""` 空字串 | 無效互動 | grep 'onclick=""' |
| `href="#"` 懸空連結 | 無效導航 | grep 'href="#"' |
| `onclick="javascript:void(0)"` | Placeholder | grep 'void(0)' |
| Tab 無對應畫面 | 斷開流程 | 檢查 Tab Bar 所有 href |
| 按鈕文字「...」或「TODO」 | Placeholder | 視覺檢查 |

### 6. 生成後驗證

```bash
# 執行可點擊元素驗證
node capture-screenshots.js --validate-only

# 預期輸出
# ✅ Coverage: 100%
# ✅ All clickable elements have valid targets
# ✅ No orphan screens detected

# 若驗證失敗，顯示：
# ❌ Coverage: 85%
# ❌ Missing targets for:
#    - SCR-AUTH-001: forgot-password-link → ???
#    - SCR-DASH-001: tab-notifications → ???
# ❌ Validation FAILED - fix issues before proceeding
```

---

## 目錄結構

```
📁 ui-flow/
├── 📄 README.md                         # 本說明文件
├── 📄 index.html                        # 畫面總覽導覽頁 (含 iPhone/iPad 切換)
├── 📄 device-preview.html               # 裝置模擬器預覽頁
├── 📁 docs/
│   ├── ui-flow-diagram-iphone.html      # iPhone 互動式流程圖
│   └── ui-flow-diagram-ipad.html        # iPad 互動式流程圖
└── 📁 shared/
    └── {{project}}-theme.css            # Design System CSS
```

## 使用方式

### 1. 複製 Template 到專案

```bash
cp -r templates/ui-flow/ ./generated-ui/{{PROJECT_ID}}/
```

### 2. 替換 Template 變數

所有 `{{VARIABLE}}` 格式的變數需替換為專案實際值：

| 變數名 | 說明 | 範例 |
|--------|------|------|
| `{{PROJECT_NAME}}` | 專案顯示名稱 | `MyApp UI/UX` |
| `{{PROJECT_ID}}` | 專案代碼 (小寫) | `myapp` |
| `{{COVERAGE}}` | UI 覆蓋率百分比 | `100` |
| `{{TOTAL_SCREENS}}` | 總畫面數 | `45` |
| `{{MODULE_COUNT}}` | 模組數量 | `8` |
| `{{IPAD_SCREENS}}` | iPad 畫面數 | `45` |
| `{{IPHONE_SCREENS}}` | iPhone 畫面數 | `45` |
| `{{GENERATED_DATE}}` | 產生日期 | `2025-12-19` |
| `{{AUTH_COUNT}}` | AUTH 模組畫面數 | `8` |
| `{{AUTH_PERCENT}}` | AUTH 覆蓋率 | `100` |
| ... | 其他模組同理 | ... |

### 3. 建立畫面目錄結構

```
📁 generated-ui/{{PROJECT_ID}}/
├── 📄 index.html
├── 📄 device-preview.html
├── 📁 docs/
│   ├── ui-flow-diagram-iphone.html
│   └── ui-flow-diagram-ipad.html
├── 📁 shared/
│   └── {{project}}-theme.css
├── 📁 screenshots/
│   ├── auth/                    # iPad 版截圖
│   ├── iphone/                  # iPhone 版截圖
│   └── [modules]/
├── 📁 auth/                     # iPad 版畫面
│   ├── SCR-AUTH-001-login.html
│   └── ...
├── 📁 iphone/                   # iPhone 版畫面
│   ├── SCR-AUTH-001-login.html
│   └── ...
└── 📁 [other-modules]/
```

## 功能特色

### index.html - 畫面總覽

- **UI Flow Diagram 嵌入**: 直接在首頁查看完整流程圖
- **iPhone/iPad 切換**: 可在 Flow Diagram 下方切換裝置模式
- **模組卡片**: 按模組分類顯示所有畫面
- **覆蓋率統計**: 即時顯示 UI/UX 完成進度
- **快速導航**: 點擊畫面直接跳轉到 Device Preview

### device-preview.html - 裝置預覽

- **三種裝置**: iPad Pro / iPad Mini / iPhone 16 Pro
- **即時切換**: 一鍵切換裝置類型
- **側邊欄導航**: 按模組分類的畫面清單
- **iframe 同步**: 導航時自動同步側邊欄狀態
- **URL 參數**: 支援 `?screen=auth/SCR-AUTH-001.html` 直連

### ui-flow-diagram - 互動式流程圖

- **iPhone 版**: 縱向卡片佈局，適合展示手機畫面
- **iPad 版**: 橫向卡片佈局，適合展示平板畫面
- **縮放拖曳**: 支援滑鼠滾輪縮放和拖曳平移
- **模組顏色**: 不同模組使用不同顏色標識
- **連接線**: SVG 箭頭顯示畫面流向
- **點擊導航**: 點擊畫面卡片直接預覽

## 模組顏色對照

| 模組 | 色碼 | Tailwind |
|------|------|----------|
| AUTH | `#6366F1` | `indigo-500` |
| ONBOARD | `#8B5CF6` | `purple-500` |
| DASH | `#F59E0B` | `amber-500` |
| FEATURE | `#10B981` | `emerald-500` |
| PROFILE | `#EC4899` | `pink-500` |
| REPORT | `#3B82F6` | `blue-500` |
| SETTING | `#64748B` | `slate-500` |

## 畫面命名規範

```
檔案格式: SCR-{MODULE}-{XXX}-{description}.html
截圖格式: SCR-{MODULE}-{XXX}-{description}.png

範例:
├── SCR-AUTH-001-login.html
├── SCR-AUTH-002-register.html
├── SCR-ONBOARD-001-welcome.html
├── SCR-DASH-001-home.html
└── SCR-SETTING-001-profile.html
```

## 客製化

### 新增模組

1. 在 `index.html` 新增模組卡片
2. 在 `device-preview.html` 新增模組區塊
3. 在 `ui-flow-diagram-*.html` 新增畫面卡片和連接線
4. 更新 Legend 顏色說明

### 修改裝置尺寸

在 `device-preview.html` 中調整以下 CSS：

```css
/* iPad Pro */
.ipad-screen { width: 1024px; height: 768px; }

/* iPhone 16 Pro */
.iphone-screen { width: 393px; height: 852px; }
```

### 新增連接線

在 `ui-flow-diagram-*.html` 的 SVG 中新增 path：

```html
<path d="M {startX} {startY} L {endX} {endY}"
      stroke="#6366F1"
      stroke-width="2.5"
      fill="none"
      marker-end="url(#arrow-auth)"/>
```

## 注意事項

1. **相對路徑**: 畫面 HTML 中使用 `../shared/` 引用共用資源
2. **截圖尺寸**: iPad 截圖建議 1194x834，iPhone 截圖建議 393x852
3. **iframe 通訊**: 使用 `history.back()` 而非 `href="../index.html"`
4. **跨模組連結**: 使用 `../module/SCR-XXX.html` 格式

---

*Generated by app-uiux-designer skill*

## 重要設計規範 (2024-12 更新)

### 1. Legend 位置與收合功能

**必須放在右上角 (`right: 24px`)，避免遮擋左側流程圖**

```css
.legend { position: fixed; top: 24px; right: 24px; }
.legend.collapsed .legend-content { display: none; }
```

```javascript
function toggleLegend() {
  const legend = document.getElementById('legend');
  legend.classList.toggle('collapsed');
  document.getElementById('legendToggle').textContent =
    legend.classList.contains('collapsed') ? '▶' : '▼';
}
```

### 2. 箭頭座標計算公式

**箭頭必須根據 screen-card 實際 CSS 位置計算，避免指向空白區域**

| 裝置 | 卡片尺寸 | 水平連線公式 | 垂直連線公式 |
|------|---------|-------------|-------------|
| iPhone | 120x260px | X: left+120 → next.left, Y: top+130 | X: left+60, Y: top+260 → next.top |
| iPad | 200x140px | X: left+200 → next.left, Y: top+70 | X: left+100, Y: top+140 → next.top |

### 3. iframe 即時預覽

可用 iframe 取代 screenshot 實現即時預覽：
- iPhone: `transform: scale(0.305)` (120/393)
- iPad: `transform: scale(0.168)` (200/1194)
