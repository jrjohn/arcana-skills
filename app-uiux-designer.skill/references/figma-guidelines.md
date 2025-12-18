# Figma 設計指南與輸出規範

本文件提供 Figma 設計工作流程、元件架構、以及輸出格式規範。

## 目錄
1. [檔案結構與組織](#檔案結構與組織)
2. [Auto Layout](#auto-layout)
3. [元件與變體](#元件與變體)
4. [Design Tokens](#design-tokens)
5. [設計輸出格式](#設計輸出格式)
6. [開發交付](#開發交付)
7. [外掛推薦](#外掛推薦)
8. [Figma API](#figma-api)

---

## 檔案結構與組織

### 專案層級結構

```
📁 [專案名稱]
├── 📄 🎨 Design System
│   ├── Foundation (基礎)
│   ├── Components (元件)
│   └── Patterns (模式)
│
├── 📄 📱 Mobile App
│   ├── iOS
│   └── Android
│
├── 📄 🖥️ Web App
│   ├── Desktop
│   ├── Tablet
│   └── Mobile
│
├── 📄 🧪 Prototypes
│   └── User Flows
│
└── 📄 📦 Handoff
    └── Dev Specs
```

### 頁面命名規範

```
📄 Cover (封面)
📄 📋 Index (索引)
📄 🎨 Foundations
    ├── Colors
    ├── Typography
    ├── Spacing
    ├── Effects
    └── Icons
📄 🧱 Components
    ├── Buttons
    ├── Inputs
    ├── Cards
    └── Navigation
📄 📱 Screens
    ├── Onboarding
    ├── Home
    ├── Profile
    └── Settings
📄 🔄 Flows
📄 ✅ Ready for Dev
📄 🗃️ Archive
```

### Frame 命名規範

```
頁面: PageName / Variant / State
元件: ComponentName / Size / Variant / State
圖層: element-name (kebab-case)

範例:
├── Login / Default
├── Login / Error
├── Login / Loading
├── Button / Large / Primary / Default
├── Button / Large / Primary / Hover
└── Button / Large / Primary / Disabled
```

### 圖層命名規則

```
Frame: PascalCase (Login, UserCard, NavBar)
Group: PascalCase (ButtonGroup, IconSet)
元素: kebab-case (icon-left, text-label, bg-overlay)
狀態: state=value (state=hover, state=active)

✅ 良好命名:
├── Button
│   ├── icon-left
│   ├── label
│   └── icon-right

❌ 避免:
├── Frame 123
│   ├── Rectangle 1
│   └── Text
```

---

## Auto Layout

### 基礎概念

```
Auto Layout = Flexbox for Figma

方向:
├── Horizontal (水平) → Row
└── Vertical (垂直) → Column

對齊:
├── Main Axis: 主軸對齊
└── Cross Axis: 交叉軸對齊

間距:
├── Gap: 子元素間距
└── Padding: 內距
```

### Auto Layout 設定

```
┌─────────────────────────────────────────┐
│  Direction: Horizontal ↔️ / Vertical ↕️  │
├─────────────────────────────────────────┤
│  Gap: 8px (元素間距)                     │
├─────────────────────────────────────────┤
│  Padding:                               │
│  ┌──────┬──────────────────┬──────┐    │
│  │  16  │                  │  16  │    │
│  ├──────┤      Content     ├──────┤    │
│  │  12  │                  │  12  │    │
│  └──────┴──────────────────┴──────┘    │
│  Top: 12 | Right: 16 | Bottom: 12 | Left: 16 │
├─────────────────────────────────────────┤
│  Alignment: ⬛⬜⬜ | ⬜⬛⬜ | ⬜⬜⬛        │
│             ⬜⬜⬜ | ⬜⬜⬜ | ⬜⬜⬜        │
│             ⬜⬜⬜ | ⬜⬜⬜ | ⬜⬜⬜        │
└─────────────────────────────────────────┘
```

### Resizing 調整行為

```
子元素 Resizing:
├── Fixed (固定): 保持設定尺寸
├── Hug (適應): 依內容調整
└── Fill (填滿): 填滿可用空間

範例 - 按鈕:
┌─────────────────────────────────────┐
│ [Icon]        Label        [Icon]   │
│  Fixed    Fill Container    Fixed   │
└─────────────────────────────────────┘
```

### 實用技巧

**絕對定位 (Absolute Position):**
```
用於: Badge、關閉按鈕、浮動元素
設定: 點擊元素 → 右側面板 → Absolute Position
位置: 設定與父容器的相對位置 (constraints)
```

**負間距效果:**
```
用於: 重疊的頭像、堆疊卡片
設定: Gap 設為負數 (如 -8)
```

**Space Between:**
```
用於: 導航列兩端對齊
設定: 選擇 "Space between" 對齊模式
```

---

## 元件與變體

### 元件結構

```
Main Component (主元件)
├── Instance (實例)
│   ├── Override 屬性
│   └── 連結到主元件
└── Variant (變體)
    ├── 同一元件的不同狀態
    └── 透過 Properties 切換
```

### 建立元件最佳實踐

```markdown
1. 選取 Frame
2. 右鍵 → Create Component (Ctrl/Cmd + Alt + K)
3. 使用 Auto Layout
4. 設定 Constraints
5. 定義 Variants
6. 新增 Component Properties
```

### Variant 命名規範

```
Property=Value 格式

範例 - Button:
├── Size=Large, Variant=Primary, State=Default
├── Size=Large, Variant=Primary, State=Hover
├── Size=Large, Variant=Primary, State=Disabled
├── Size=Medium, Variant=Primary, State=Default
├── Size=Small, Variant=Secondary, State=Default
└── ...

Properties:
├── Size: Large, Medium, Small
├── Variant: Primary, Secondary, Outline, Ghost
├── State: Default, Hover, Focus, Active, Disabled
└── Icon: True, False
```

### Component Properties 類型

```
1. Variant (變體)
   切換預定義的設計變化
   用於: Size, Type, State

2. Boolean (布林)
   顯示/隱藏元素
   用於: hasIcon, showBadge, isSelected

3. Instance Swap (實例交換)
   替換嵌套元件
   用於: 更換圖標、頭像

4. Text (文字)
   覆寫文字內容
   用於: Label, Title, Description
```

### 元件範例

**Button Component:**
```
Button
├── Properties
│   ├── Size: Large | Medium | Small
│   ├── Variant: Primary | Secondary | Outline | Ghost
│   ├── State: Default | Hover | Focus | Active | Disabled
│   ├── IconLeft: Boolean
│   └── IconRight: Boolean
│
├── Structure (Auto Layout - Horizontal)
│   ├── icon-left (Instance Swap, Hidden by default)
│   ├── label (Text Property)
│   └── icon-right (Instance Swap, Hidden by default)
│
└── Variants Grid (共 60 個變體)
    ├── Large/Primary/Default
    ├── Large/Primary/Hover
    └── ...
```

### Slots Pattern

```
用於可替換內容的元件 (如 Card)

Card
├── slot-header (Frame with Auto Layout)
│   └── .slot-header (Hidden placeholder)
├── slot-content
│   └── .slot-content
└── slot-footer
    └── .slot-footer

使用時將內容貼入對應 slot 並隱藏 placeholder
```

---

## Design Tokens

### Token 結構 in Figma

```
Figma Variables (變數系統)

Collections (集合):
├── Primitives (原始值)
│   ├── Colors
│   │   ├── blue/50: #EFF6FF
│   │   ├── blue/100: #DBEAFE
│   │   └── ...
│   ├── Spacing
│   │   ├── 1: 4
│   │   ├── 2: 8
│   │   └── ...
│   └── Radius
│       ├── sm: 4
│       ├── md: 8
│       └── ...
│
└── Semantic (語義)
    ├── Colors
    │   ├── bg/primary: {primitives.white}
    │   ├── bg/secondary: {primitives.gray/50}
    │   ├── text/primary: {primitives.gray/900}
    │   ├── text/secondary: {primitives.gray/600}
    │   ├── border/default: {primitives.gray/200}
    │   └── interactive/primary: {primitives.blue/500}
    │
    └── Spacing
        ├── page/padding: {primitives.spacing/4}
        ├── section/gap: {primitives.spacing/8}
        └── component/gap: {primitives.spacing/4}
```

### 建立 Variables

```markdown
1. 開啟 Variables Panel
   - 右側欄 → Local Variables
   - 或 Figma Menu → Plugins → Variables

2. 建立 Collection
   - 點擊 + Create Collection
   - 命名: Primitives, Semantic, Component

3. 新增變數
   - 點擊 + Create Variable
   - 選擇類型: Color, Number, String, Boolean
   - 設定值

4. 建立 Alias (別名)
   - 點擊變數值
   - 選擇另一個變數作為參照
```

### Modes (模式)

```
用於: 淺色/深色主題、多品牌支援

範例 - 主題切換:
Collection: Semantic Colors
├── Mode 1: Light
│   ├── bg/primary: #FFFFFF
│   └── text/primary: #111827
│
└── Mode 2: Dark
    ├── bg/primary: #111827
    └── text/primary: #F9FAFB

使用: 選取 Frame → 右側面板切換 Mode
```

### 匯出 Design Tokens

**Tokens Studio 外掛格式:**
```json
{
  "colors": {
    "primary": {
      "value": "#3B82F6",
      "type": "color"
    },
    "text": {
      "primary": {
        "value": "{colors.gray.900}",
        "type": "color"
      }
    }
  },
  "spacing": {
    "sm": {
      "value": "8",
      "type": "spacing"
    }
  }
}
```

**Style Dictionary 輸出:**
```css
/* CSS Variables */
:root {
  --color-primary: #3B82F6;
  --color-text-primary: #111827;
  --spacing-sm: 8px;
}
```

```swift
// iOS Swift
enum Colors {
    static let primary = UIColor(hex: "#3B82F6")
    static let textPrimary = UIColor(hex: "#111827")
}
```

```kotlin
// Android Kotlin
object Colors {
    val Primary = Color(0xFF3B82F6)
    val TextPrimary = Color(0xFF111827)
}
```

---

## 設計輸出格式

### 匯出圖片資源

**匯出設定:**
```
格式選擇:
├── PNG: 點陣圖、截圖、複雜圖片
├── JPG: 照片、大型背景
├── SVG: 圖標、向量圖形、Logo
├── PDF: 向量資源、iOS 圖標
└── WebP: Web 優化圖片

解析度 (Scale):
├── @1x: 基準尺寸
├── @2x: Retina (iOS @2x, Android xxhdpi)
├── @3x: Super Retina (iOS @3x, Android xxxhdpi)
└── @4x: 高解析度螢幕

命名規範:
├── icon-name.svg
├── icon-name@2x.png
├── icon-name@3x.png
└── illustration-hero.webp
```

**批次匯出設定:**
```
1. 選取元素
2. 右側面板 → Export
3. 點擊 + 新增多個匯出設定
4. 使用 Suffix 區分: @2x, @3x

範例:
├── 1x → icon-home.png
├── 2x → icon-home@2x.png
└── 3x → icon-home@3x.png
```

### 匯出 CSS 樣式

**直接複製 CSS:**
```css
/* 選取元素 → 右鍵 → Copy as CSS */

/* Frame */
.element {
  width: 320px;
  height: 48px;
  padding: 12px 16px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
}

/* Text */
.text {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  line-height: 24px;
  color: #111827;
}
```

### 匯出 iOS/Android 程式碼

**Copy as Code 外掛:**
```swift
// iOS SwiftUI
struct Button: View {
    var body: some View {
        HStack(spacing: 8) {
            Image("icon")
            Text("Label")
                .font(.system(size: 16, weight: .semibold))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.blue)
        .cornerRadius(8)
    }
}
```

```kotlin
// Android Jetpack Compose
@Composable
fun Button() {
    Row(
        modifier = Modifier
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .background(Color.Blue, RoundedCornerShape(8.dp)),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Icon(painter = painterResource(R.drawable.icon))
        Text(
            text = "Label",
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold
        )
    }
}
```

### 匯出 JSON 規格

**Figma REST API 輸出:**
```json
{
  "id": "1:2",
  "name": "Button",
  "type": "FRAME",
  "absoluteBoundingBox": {
    "x": 0,
    "y": 0,
    "width": 120,
    "height": 48
  },
  "fills": [
    {
      "type": "SOLID",
      "color": {
        "r": 0.231,
        "g": 0.510,
        "b": 0.965,
        "a": 1
      }
    }
  ],
  "cornerRadius": 8,
  "paddingLeft": 16,
  "paddingRight": 16,
  "paddingTop": 12,
  "paddingBottom": 12,
  "itemSpacing": 8,
  "layoutMode": "HORIZONTAL"
}
```

---

## 開發交付

### Dev Mode

```
Figma Dev Mode 功能:
├── 自動標註尺寸與間距
├── 複製 CSS/iOS/Android 程式碼
├── 查看 Variables 對應
├── 比較設計變更
└── VS Code 整合
```

### 交付規格文件

**元件規格:**
```markdown
## Button Component

### 視覺規格
- 高度: 48px (Large), 40px (Medium), 32px (Small)
- 圓角: 8px
- 內距: 16px (水平), 12px (垂直)
- 間距: 8px (icon 與 label)

### 顏色
| 狀態 | 背景 | 文字 | 邊框 |
|------|------|------|------|
| Default | primary-500 | white | - |
| Hover | primary-600 | white | - |
| Active | primary-700 | white | - |
| Disabled | gray-200 | gray-400 | - |

### 字型
- Font: Inter
- Size: 16px
- Weight: 600 (Semibold)
- Line Height: 24px

### 動畫
- Transition: all 150ms ease-out
- Hover: scale(1.02)
- Active: scale(0.98)
```

### 標註最佳實踐

```
1. 使用 Auto Layout
   讓間距自動標註

2. 使用 Variables
   顯示 Token 名稱而非數值

3. 統一命名
   確保圖層命名清晰

4. 分組交付
   ├── 已驗收 (Ready)
   ├── 審核中 (Review)
   └── 開發中 (In Progress)

5. 版本標記
   v1.0 → v1.1 → v2.0
```

---

## 外掛推薦

### Design System 相關

| 外掛 | 用途 |
|------|------|
| Tokens Studio | Design Tokens 管理與同步 |
| Style Organizer | 整理 Styles |
| Design Lint | 檢查設計一致性 |
| Themer | 主題切換預覽 |

### 效率工具

| 外掛 | 用途 |
|------|------|
| Autoflow | 自動產生流程線 |
| Content Reel | 假資料填充 |
| Unsplash | 免費圖片 |
| Iconify | 圖標庫 |
| Stark | 無障礙檢查 |

### 開發協作

| 外掛 | 用途 |
|------|------|
| Anima | 匯出 React/Vue/HTML |
| Locofy | 設計轉程式碼 |
| Zeplin | 設計交付平台 |
| Storybook Connect | 連結 Storybook |

### 內容生成

| 外掛 | 用途 |
|------|------|
| Lorem ipsum | 假文字 |
| User Profile | 假用戶資料 |
| Charts | 圖表產生 |
| Mapsicle | 地圖嵌入 |

---

## Figma API

### REST API 基礎

**取得檔案資訊:**
```bash
GET https://api.figma.com/v1/files/:file_key

Headers:
X-Figma-Token: your-personal-access-token
```

**回應範例:**
```json
{
  "name": "My Design File",
  "lastModified": "2024-01-15T10:30:00Z",
  "version": "123456789",
  "document": {
    "id": "0:0",
    "name": "Document",
    "type": "DOCUMENT",
    "children": [...]
  },
  "components": {...},
  "styles": {...}
}
```

### 常用 API Endpoints

```
檔案:
GET /v1/files/:key                    # 取得檔案
GET /v1/files/:key/nodes?ids=...      # 取得特定節點
GET /v1/files/:key/images             # 匯出圖片

元件:
GET /v1/files/:key/components         # 取得元件
GET /v1/files/:key/component_sets     # 取得元件集

樣式:
GET /v1/files/:key/styles             # 取得樣式

變數:
GET /v1/files/:key/variables/local    # 取得 Variables

專案:
GET /v1/projects/:id/files            # 取得專案檔案

註解:
GET /v1/files/:key/comments           # 取得註解
POST /v1/files/:key/comments          # 新增註解
```

### 匯出圖片

```bash
# 取得圖片 URL
GET https://api.figma.com/v1/images/:file_key
  ?ids=1:2,1:3
  &scale=2
  &format=png

# 回應
{
  "images": {
    "1:2": "https://s3-us-west-2.amazonaws.com/figma-alpha-api/img/...",
    "1:3": "https://s3-us-west-2.amazonaws.com/figma-alpha-api/img/..."
  }
}
```

### Webhook 整合

```json
// Webhook 設定
POST https://api.figma.com/v2/webhooks

{
  "event_type": "FILE_UPDATE",
  "team_id": "123456",
  "endpoint": "https://your-server.com/figma-webhook",
  "passcode": "your-secret-passcode"
}

// Webhook 事件
{
  "event_type": "FILE_UPDATE",
  "file_key": "abc123",
  "file_name": "My Design",
  "timestamp": "2024-01-15T10:30:00Z",
  "triggered_by": {
    "id": "user123",
    "handle": "designer"
  }
}
```

### 自動化範例

**Node.js - 匯出所有圖標:**
```javascript
const axios = require('axios');

const FIGMA_TOKEN = 'your-token';
const FILE_KEY = 'your-file-key';
const ICONS_FRAME_ID = '1:234';

async function exportIcons() {
  // 1. 取得 Frame 內所有節點
  const { data } = await axios.get(
    `https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${ICONS_FRAME_ID}`,
    { headers: { 'X-Figma-Token': FIGMA_TOKEN } }
  );

  // 2. 收集所有圖標 ID
  const iconIds = data.nodes[ICONS_FRAME_ID].document.children
    .map(child => child.id)
    .join(',');

  // 3. 匯出為 SVG
  const { data: images } = await axios.get(
    `https://api.figma.com/v1/images/${FILE_KEY}?ids=${iconIds}&format=svg`,
    { headers: { 'X-Figma-Token': FIGMA_TOKEN } }
  );

  // 4. 下載並儲存
  for (const [id, url] of Object.entries(images.images)) {
    const svg = await axios.get(url);
    // 儲存 SVG 檔案...
  }
}
```

---

## Figma 輸出檢查清單

### 設計交付前確認

```
檔案組織
□ 頁面命名清楚
□ Frame 命名規範
□ 圖層結構整潔
□ 無多餘隱藏圖層

元件品質
□ 使用 Auto Layout
□ Constraints 正確設定
□ Variants 完整
□ Properties 定義清楚

Design Tokens
□ Variables 已定義
□ 顏色使用 Variables
□ 間距使用 Variables
□ 支援深色模式

匯出準備
□ 圖片資源已設定 Export
□ 多倍率匯出 (@1x, @2x, @3x)
□ SVG 圖標已優化
□ 圖片已壓縮

交付規格
□ 元件規格文件
□ 互動說明
□ 動畫規格
□ 響應式說明
```
