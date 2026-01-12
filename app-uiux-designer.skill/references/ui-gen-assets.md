# UI 生成資產參考

## SVG 視覺稿

### 基礎結構

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 390 844" width="390" height="844">
  <defs>
    <style>
      .background { fill: #FFFFFF; }
      .primary { fill: #6366F1; }
      .text-primary { fill: #1F2937; font-family: system-ui, sans-serif; }
      .text-secondary { fill: #6B7280; font-family: system-ui, sans-serif; }
      .surface { fill: #F8FAFC; }
      .border { stroke: #E5E7EB; stroke-width: 1; fill: none; }
    </style>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.1"/>
    </filter>
  </defs>

  <!-- 背景 -->
  <rect class="background" width="390" height="844"/>

  <!-- Status Bar -->
  <g transform="translate(0, 0)">
    <rect fill="#FFFFFF" width="390" height="44"/>
    <text x="24" y="28" class="text-primary" font-size="14" font-weight="600">9:41</text>
  </g>

  <!-- 內容區域 -->
  <g transform="translate(24, 100)">
    <!-- 元件放置於此 -->
  </g>

  <!-- Home Indicator -->
  <rect x="128" y="822" width="134" height="5" rx="3" fill="#000000"/>
</svg>
```

### SVG 元件

#### Button

```svg
<!-- Primary Button -->
<g transform="translate(0, 0)">
  <rect width="342" height="52" rx="12" fill="#6366F1" filter="url(#shadow)"/>
  <text x="171" y="32" fill="#FFFFFF" font-size="16" font-weight="600" text-anchor="middle">按鈕文字</text>
</g>

<!-- Secondary Button -->
<g transform="translate(0, 0)">
  <rect width="342" height="52" rx="12" fill="#F8FAFC"/>
  <rect width="342" height="52" rx="12" stroke="#E5E7EB" fill="none"/>
  <text x="171" y="32" fill="#1F2937" font-size="16" font-weight="500" text-anchor="middle">次要按鈕</text>
</g>
```

#### Input

```svg
<g transform="translate(0, 0)">
  <text x="0" y="0" class="text-primary" font-size="14" font-weight="500">標籤</text>
  <rect x="0" y="12" width="342" height="52" rx="12" fill="#F8FAFC"/>
  <rect x="0" y="12" width="342" height="52" rx="12" stroke="#E5E7EB" fill="none"/>
  <text x="16" y="46" fill="#9CA3AF" font-size="16">placeholder</text>
</g>
```

---

## Figma 匯入 JSON

### 基礎結構

```json
{
  "name": "Screen Name",
  "type": "FRAME",
  "width": 390,
  "height": 844,
  "fills": [{"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1}}],
  "children": []
}
```

### 元件範例

#### Button

```json
{
  "name": "Primary Button",
  "type": "COMPONENT",
  "width": 342,
  "height": 52,
  "cornerRadius": 12,
  "fills": [{"type": "SOLID", "color": {"r": 0.388, "g": 0.4, "b": 0.945}}],
  "effects": [{
    "type": "DROP_SHADOW",
    "offset": {"x": 0, "y": 4},
    "radius": 16,
    "color": {"r": 0.388, "g": 0.4, "b": 0.945, "a": 0.25}
  }],
  "children": [{
    "type": "TEXT",
    "characters": "按鈕文字",
    "fontSize": 16,
    "fontWeight": 600,
    "fills": [{"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1}}],
    "textAlignHorizontal": "CENTER",
    "textAlignVertical": "CENTER"
  }]
}
```

#### Input Field

```json
{
  "name": "Input Field",
  "type": "COMPONENT",
  "layoutMode": "VERTICAL",
  "itemSpacing": 8,
  "children": [
    {
      "name": "Label",
      "type": "TEXT",
      "characters": "標籤",
      "fontSize": 14,
      "fontWeight": 500,
      "fills": [{"type": "SOLID", "color": {"r": 0.122, "g": 0.161, "b": 0.216}}]
    },
    {
      "name": "Field",
      "type": "FRAME",
      "width": 342,
      "height": 52,
      "cornerRadius": 12,
      "fills": [{"type": "SOLID", "color": {"r": 0.973, "g": 0.98, "b": 0.988}}],
      "strokes": [{"type": "SOLID", "color": {"r": 0.898, "g": 0.906, "b": 0.922}}],
      "strokeWeight": 1,
      "children": [{
        "type": "TEXT",
        "characters": "Placeholder",
        "fontSize": 16,
        "fills": [{"type": "SOLID", "color": {"r": 0.612, "g": 0.639, "b": 0.686}}]
      }]
    }
  ]
}
```

#### Card

```json
{
  "name": "Card",
  "type": "COMPONENT",
  "cornerRadius": 16,
  "fills": [{"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1}}],
  "effects": [{
    "type": "DROP_SHADOW",
    "offset": {"x": 0, "y": 2},
    "radius": 8,
    "color": {"r": 0, "g": 0, "b": 0, "a": 0.05}
  }],
  "layoutMode": "VERTICAL",
  "children": [
    {
      "name": "Image",
      "type": "RECTANGLE",
      "width": 342,
      "height": 192,
      "fills": [{"type": "IMAGE", "imageRef": "placeholder"}]
    },
    {
      "name": "Content",
      "type": "FRAME",
      "layoutMode": "VERTICAL",
      "padding": 16,
      "itemSpacing": 8,
      "children": [
        {"type": "TEXT", "characters": "標題", "fontSize": 18, "fontWeight": 600},
        {"type": "TEXT", "characters": "描述文字", "fontSize": 14}
      ]
    }
  ]
}
```

---

## 頁面範本庫

### 認證相關

| 頁面 | 說明 |
|------|------|
| Login | 登入頁 (Email/密碼、社群登入) |
| Sign Up | 註冊頁 (多步驟流程) |
| Forgot Password | 忘記密碼 (Email 輸入) |
| Reset Password | 重設密碼 (新密碼輸入) |
| OTP Verification | OTP 驗證 (6 位數輸入) |
| Onboarding | 引導頁 (多步驟圖文) |

### 首頁相關

| 頁面 | 說明 |
|------|------|
| Dashboard | 儀表板 (卡片統計) |
| Home Feed | 首頁動態 (垂直列表) |
| Explore | 探索頁 (網格瀏覽) |
| Search Results | 搜尋結果 (列表/網格) |

### 列表相關

| 頁面 | 說明 |
|------|------|
| Product List | 商品列表 (圖片+價格) |
| Article List | 文章列表 (標題+摘要) |
| Card Grid | 卡片網格 (2-3 欄) |
| Message List | 訊息列表 (頭像+預覽) |
| Notification List | 通知列表 (圖示+時間) |

### 詳細頁相關

| 頁面 | 說明 |
|------|------|
| Product Detail | 商品詳情 (圖片輪播+資訊) |
| Article Detail | 文章詳情 (圖文排版) |
| Profile | 個人檔案 (頭像+資訊+操作) |
| Settings | 設定頁 (列表項目) |

### 電商相關

| 頁面 | 說明 |
|------|------|
| Shopping Cart | 購物車 (商品列表+結算) |
| Checkout | 結帳頁 (地址+付款) |
| Order Confirmation | 訂單確認 (成功狀態) |
| Order History | 訂單列表 (狀態篩選) |
| Order Detail | 訂單詳情 (完整資訊) |

### 表單相關

| 頁面 | 說明 |
|------|------|
| Edit Form | 資料編輯 (表單輸入) |
| Multi-step Form | 多步驟表單 (進度指示) |
| Filter | 篩選器 (選項勾選) |
| Survey | 問卷調查 (問答流程) |

### 社群相關

| 頁面 | 說明 |
|------|------|
| Feed | 動態牆 (貼文列表) |
| Post Detail | 貼文詳情 (內容+留言) |
| Chat | 聊天室 (訊息對話) |
| Comments | 評論區 (留言列表) |
| Following | 追蹤列表 (用戶列表) |

### 狀態頁面

| 頁面 | 說明 |
|------|------|
| Empty State | 空狀態 (圖示+文字+操作) |
| Loading | 載入中 (骨架屏/Spinner) |
| Error | 錯誤頁 (圖示+重試) |
| Success | 成功頁 (圖示+繼續) |
| 404 | 找不到 (圖示+返回) |

---

## 色彩轉換工具

### HEX to RGB

```javascript
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16) / 255,
    g: parseInt(result[2], 16) / 255,
    b: parseInt(result[3], 16) / 255
  } : null;
}
```

### 常用色彩對照

| 名稱 | HEX | Figma RGB |
|------|-----|-----------|
| Primary | #6366F1 | 0.388, 0.4, 0.945 |
| Secondary | #EC4899 | 0.925, 0.282, 0.6 |
| Background | #FFFFFF | 1, 1, 1 |
| Surface | #F8FAFC | 0.973, 0.98, 0.988 |
| Text Primary | #1F2937 | 0.122, 0.161, 0.216 |
| Text Secondary | #6B7280 | 0.42, 0.451, 0.502 |
| Border | #E5E7EB | 0.898, 0.906, 0.922 |
| Error | #EF4444 | 0.937, 0.267, 0.267 |
| Success | #10B981 | 0.063, 0.725, 0.506 |
