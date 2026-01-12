# UI 畫面自動生成指南

自動生成 UI 畫面的快速參考，詳細程式碼範例見各平台參考檔案。

## 預設設定

| 項目 | 預設值 |
|------|--------|
| 平台 | Mobile App UI/UX |
| 尺寸 | iPhone 14 Pro (390 x 844 pt) |
| 格式 | HTML + Tailwind CSS |
| 入口 | index.html |
| 互動 | 所有 Button/Link 皆可點擊導航 |

## 參考檔案索引

| 檔案 | 內容 |
|------|------|
| `ui-gen-html.md` | HTML/Tailwind 模板、元件 |
| `ui-gen-react.md` | React + Styled Components |
| `ui-gen-angular.md` | Angular Standalone Components |
| `ui-gen-swiftui.md` | iOS SwiftUI |
| `ui-gen-compose.md` | Android Jetpack Compose |
| `ui-gen-assets.md` | SVG/Figma JSON/頁面範本庫 |

---

## 互動導航系統

### 設計原則

1. **可完整走訪** - 從 index.html 開始，可透過點擊瀏覽所有頁面
2. **真實導航** - 所有 Button/Link 必須有實際連結
3. **流程連貫** - 遵循真實 App 的導航邏輯

### 目錄結構 (必須)

```
📁 generated-ui/
├── 📄 index.html              # 入口頁 - 畫面總覽與導航中心
├── 📁 shared/
│   ├── theme.css              # Design System CSS Variables
│   ├── navigation.js          # 共用導航邏輯
│   └── components.css         # 共用元件樣式
├── 📁 auth/                   # 認證模組
├── 📁 onboard/                # 引導流程
├── 📁 main/                   # 主要功能
└── 📁 [module]/               # 其他模組
```

### 導航實作速查

| 元素類型 | 實作方式 |
|---------|---------|
| Primary Button | `onclick="location.href='path.html'"` 或 `<a href>` |
| Back Button | `onclick="history.back()"` |
| Text Link | `<a href="path.html" class="text-primary">` |
| Tab Bar Item | `<a href="../main/page.html">` |
| Card 點擊 | 整個 `<a>` 包裹 card 內容 |
| List Item | `<a>` 包裹，含右箭頭圖示 |

### 導航檢查清單

- [ ] index.html 存在且包含所有頁面連結
- [ ] 所有 Primary Button 有 onclick 或 href
- [ ] 所有 Back Button 可返回
- [ ] Tab Bar 每個項目都有連結
- [ ] 可從 index.html 走訪所有頁面
- [ ] 相對路徑正確 (../ 處理正確)

---

## 生成模式總覽

### 支援的輸出格式

| 格式 | 用途 |
|------|------|
| HTML/CSS | 可直接瀏覽器預覽的互動原型 |
| React | 可直接使用的 React 元件 |
| SwiftUI | iOS/macOS 原生 UI |
| Compose | Android 原生 UI |
| SVG | 向量視覺稿 (可匯入設計工具) |
| Figma JSON | 可匯入 Figma 的結構化資料 |

### 生成流程

```
用戶需求 → 需求分析 → 風格確認 → 結構規劃 → 程式碼生成 → 可執行 UI
```

---

## 頁面類型速查

### 認證相關
- 登入頁、註冊頁、忘記密碼、重設密碼、OTP 驗證、引導頁

### 首頁相關
- 儀表板、首頁摘要、探索頁、搜尋結果

### 列表相關
- 商品列表、文章列表、卡片網格、訊息列表、通知列表

### 詳細頁相關
- 商品詳情、文章詳情、個人檔案、設定頁

### 電商相關
- 購物車、結帳頁、訂單確認、訂單列表、訂單詳情

### 表單相關
- 資料編輯、多步驟表單、篩選器、問卷調查

### 社群相關
- 動態牆、貼文詳情、聊天室、評論區、追蹤列表

### 狀態頁面
- 空狀態、載入中、錯誤頁、成功頁、404

---

## UI 生成請求格式

```markdown
## UI 生成請求

**頁面類型:** [類型]
**平台:** iOS / Android / Web
**輸出格式:** HTML+Tailwind / React / SwiftUI / Compose

### 風格設定
- 主色: [色碼]
- 風格: [現代/經典/活潑/專業]
- 圓角: [小 6px / 中 12px / 大 16px]

### 功能需求
- [x] 功能1
- [x] 功能2
- [ ] 可選功能

### 特殊要求
- [深色模式/表單驗證/載入狀態...]
```

---

## 生成提示詞模板

### 基礎生成

```
請幫我生成 [頁面類型] 的 UI：
- 平台: [平台]
- 格式: [格式]
- 主色: [色碼]
- 風格: [風格]
- 功能: [功能清單]
```

### 含風格萃取

```
請根據以下萃取的風格，生成 [頁面類型] 的 UI：

## 已萃取風格
[貼上 style-extraction 結果]

## 頁面需求
[需求描述]

請確保使用萃取的色彩、字型、圓角，維持整體風格一致性。
```

---

## 生成檢查清單

### 視覺一致性
- [ ] 色彩符合設計系統
- [ ] 字型大小/粗細一致
- [ ] 間距符合規範
- [ ] 圓角統一

### 功能完整性
- [ ] 所有需求功能皆有對應 UI
- [ ] 互動狀態完整 (hover/focus/active/disabled)
- [ ] 空狀態/載入/錯誤狀態
- [ ] 表單驗證回饋

### 響應式/適應性
- [ ] 不同螢幕尺寸適配
- [ ] 安全區域處理 (iOS notch)
- [ ] 橫向模式考量

### 無障礙
- [ ] 對比度符合 WCAG
- [ ] 觸控目標 ≥ 44pt
- [ ] 語義化標籤

### 程式碼品質
- [ ] 可直接執行
- [ ] 命名清晰
- [ ] 結構合理
