# UI Flow Reference Example

此目錄包含已驗證通過的 UI Flow 範本，用於驗證新專案產生的 UI Flow 是否正確。

## 專案資訊

- **專案名稱**: 單字小達人 (VocabKids)
- **總畫面數**: 42
- **模組數**: 9
- **驗證日期**: 2026-01-15

## 模組結構

| Module | Count | Screens |
|--------|-------|---------|
| AUTH | 4 | splash, login, register, forgot-password |
| ONBOARD | 3 | welcome, role-select, setup-complete |
| HOME | 2 | student-home, parent-home |
| VOCAB | 8 | bank-list, bank-detail, word-detail, add-word, import, export, ocr-scan, community |
| TRAIN | 10 | mode-select, listening, listening-result, pronunciation, pronunciation-result, spelling, spelling-result, sentence-fill, matching, session-complete |
| REPORT | 4 | overview, daily, weekly, word-analysis |
| SETTING | 5 | main, tts, pronunciation, notification, account |
| PARENT | 4 | dashboard, assign-vocab, child-progress, sentence-manage |
| COMMON | 2 | loading, error |

## 檔案說明

### 核心檔案

| 檔案 | 說明 |
|------|------|
| `index.html` | 主入口頁面，顯示模組卡片和嵌入式 UI Flow |
| `device-preview.html` | 裝置預覽頁面，支援 iPad / iPad Mini / iPhone 切換 |
| `validate-ui-flow.js` | 驗證腳本，檢查畫面完整性和連結有效性 |

### docs/ 目錄

| 檔案 | 說明 |
|------|------|
| `ui-flow-diagram.html` | iPhone UI Flow (預設) |
| `ui-flow-diagram-ipad.html` | iPad UI Flow |
| `ui-flow-diagram-iphone.html` | iPhone UI Flow (備用) |

### shared/ 目錄

| 檔案 | 說明 |
|------|------|
| `project-theme.css` | 專案主題樣式 |
| `notify-parent.js` | iframe 通訊腳本 |

## 驗證標準

### UI Flow Diagram 必要元素

1. **iPhone 版本** (ui-flow-diagram.html)
   - `flow-container` 容器
   - 42 個 `screen-card`
   - 42 個 `iframe` 預覽
   - iPhone 框架: `width: 120px; height: 260px`
   - iframe 縮放: `scale(0.305)` (393x852 → 120x260)
   - notch: `width: 40px; height: 6px; border-radius: 3px`
   - `device-switcher` 連結至 iPad 版本

2. **iPad 版本** (ui-flow-diagram-ipad.html)
   - `flow-container` 容器
   - 42 個 `screen-card`
   - 42 個 `iframe` 預覽
   - iPad 框架: `width: 200px; height: 140px`
   - iframe 縮放: `scale(0.168)` (1194x834 → 200x140)
   - camera: `width: 6px; height: 6px; border-radius: 50%`
   - `device-switcher` 連結至 iPhone 版本

### device-preview.html 必要元素

- 三種裝置切換: iPad / iPad Mini / iPhone
- 完整的畫面清單 (sidebar)
- URL 參數支援: `?device=ipad&screen=auth/SCR-AUTH-001-splash.html`
- iframe 自動同步 sidebar 選中狀態

### 畫面點擊行為

UI Flow Diagram 中的畫面點擊應導向 device-preview.html：
```javascript
function openScreen(path) {
  // iPhone 版本
  window.open('../device-preview.html?device=iphone&screen=' + path, '_blank');

  // iPad 版本
  window.open('../device-preview.html?device=ipad&screen=' + path, '_blank');
}
```

## 使用方式

### 複製範本到新專案

```bash
# 複製範本結構
cp -r reference-example/docs /path/to/project/04-ui-flow/
cp reference-example/device-preview.html /path/to/project/04-ui-flow/
cp reference-example/index.html /path/to/project/04-ui-flow/
cp reference-example/validate-ui-flow.js /path/to/project/04-ui-flow/
cp -r reference-example/shared /path/to/project/04-ui-flow/
```

### 執行驗證

```bash
cd /path/to/project/04-ui-flow
node validate-ui-flow.js
```

### 預期輸出

```
✅ UI FLOW VALIDATION PASSED
   All screens present, index.html valid, no broken links
```

## 一致性驗證 (Consistency Validation)

驗證產出的 UI Flow 是否符合 reference-example 標準。

### 驗證腳本

| 腳本 | 說明 |
|------|------|
| `validate-ui-flow.js` | 驗證畫面檔案和模組結構 |
| `validate-navigation.js` | 驗證導航連結和點擊處理 |
| `validate-consistency.js` | 驗證與 reference-example 標準一致性 |
| `validate-all.js` | 整合執行所有驗證 |

### 執行一致性驗證

```bash
cd /path/to/project/04-ui-flow

# 方法 1: 直接執行 (會自動尋找 standards.json)
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-consistency.js

# 方法 2: 複製腳本到專案執行
cp ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-consistency.js .
cp ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/reference-example/standards.json .
node validate-consistency.js

# 方法 3: 執行完整驗證
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-all.js
```

### 驗證項目

1️⃣ **檔案結構** - 必要檔案存在性
2️⃣ **裝置規格 (iPhone)** - 框架尺寸、縮放比例、notch
3️⃣ **裝置規格 (iPad)** - 框架尺寸、縮放比例、camera
4️⃣ **必要元素** - flow-container、screen-card、device-frame
5️⃣ **功能行為** - openScreen()、device-switcher、URL 參數
6️⃣ **CSS 一致性** - 模組顏色、badge classes

### 標準規格檔案

`standards.json` 定義了所有驗證標準：

```json
{
  "devices": {
    "iphone": { "frame": {"width": 120, "height": 260}, "scale": 0.305 },
    "ipad": { "frame": {"width": 200, "height": 140}, "scale": 0.168 }
  },
  "moduleColors": {
    "AUTH": "#6366F1", "ONBOARD": "#8B5CF6", ...
  }
}
```

## 模組顏色對照

| Module | Color | Hex |
|--------|-------|-----|
| AUTH | Indigo | #6366F1 |
| ONBOARD | Purple | #8B5CF6 |
| HOME | Amber | #F59E0B |
| VOCAB | Emerald | #10B981 |
| TRAIN | Blue | #3B82F6 |
| REPORT | Pink | #EC4899 |
| SETTING | Slate | #64748B |
| PARENT | Teal | #14B8A6 |
| COMMON | Stone | #78716C |

## 注意事項

1. 此範本基於 42 畫面的專案結構，新專案需根據 SDD 調整畫面數量
2. 模組名稱和畫面 ID 需符合 `SCR-{MODULE}-{NNN}-{name}` 格式
3. 驗證腳本 `validate-ui-flow.js` 需根據新專案的模組結構調整 `EXPECTED_MODULES`
