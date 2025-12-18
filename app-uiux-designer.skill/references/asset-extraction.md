# 視覺素材截取與輸出指南

本指南提供從參考圖片中識別、截取特殊物件、Icon、插畫等視覺元素，並輸出為可用設計素材的方法。

## 目錄
1. [素材截取流程](#素材截取流程)
2. [Icon 識別與分析](#icon-識別與分析)
3. [插畫元素截取](#插畫元素截取)
4. [UI 元件截取](#ui-元件截取)
5. [素材分類與命名](#素材分類與命名)
6. [輸出格式規範](#輸出格式規範)
7. [Figma 素材庫建立](#figma-素材庫建立)
8. [Icon Library 產生](#icon-library-產生)

---

## 素材截取流程

### 整體流程

```
輸入參考圖片
     ↓
┌─────────────────────────────────────────────┐
│              視覺元素識別                     │
├─────────────┬─────────────┬─────────────────┤
│   Icon      │   插畫      │   UI 元件       │
├─────────────┼─────────────┼─────────────────┤
│   圖形      │   裝飾      │   照片元素      │
└─────────────┴─────────────┴─────────────────┘
     ↓
元素分析與描述
     ↓
風格特徵記錄
     ↓
素材規格輸出
     ↓
Figma/Code 資產產生
```

### 可截取的素材類型

```
📁 素材類型總覽

├── 🔷 Icon (圖標)
│   ├── 系統圖標 (Navigation, Action)
│   ├── 功能圖標 (Feature Icons)
│   ├── 社群圖標 (Social Icons)
│   └── 品牌圖標 (Brand Icons)
│
├── 🎨 插畫 (Illustrations)
│   ├── 人物插畫
│   ├── 場景插畫
│   ├── 物件插畫
│   └── 抽象圖形
│
├── 🖼️ 圖形元素 (Graphics)
│   ├── 形狀 (Shapes)
│   ├── 裝飾線條
│   ├── 背景紋理
│   └── 漸層效果
│
├── 📦 UI 元件 (Components)
│   ├── 按鈕樣式
│   ├── 卡片樣式
│   ├── 輸入框樣式
│   └── 導航元素
│
└── 📷 照片元素 (Photo Elements)
    ├── 人物剪影
    ├── 產品圖
    └── 背景圖
```

---

## Icon 識別與分析

### Icon 風格分類

```
┌─────────────────────────────────────────────────────────┐
│                    Icon 風格類型                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Outlined (線性)          Filled (填滿)                  │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   ╭───╮     │         │   ████████  │               │
│  │   │   │     │         │   ████████  │               │
│  │   ╰───╯     │         │   ████████  │               │
│  └─────────────┘         └─────────────┘               │
│  特徵: 線條、透明         特徵: 實心、無線條             │
│                                                         │
│  Two-tone (雙色)          Duotone (雙調)                 │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   ▓▓▓▓▓▓▓   │         │   ░░████░░  │               │
│  │   ▓▓░░░▓▓   │         │   ░░████░░  │               │
│  │   ▓▓▓▓▓▓▓   │         │   ░░████░░  │               │
│  └─────────────┘         └─────────────┘               │
│  特徵: 主色+次色          特徵: 深淺兩色                 │
│                                                         │
│  3D / Isometric           Gradient (漸層)               │
│  ┌─────────────┐         ┌─────────────┐               │
│  │    ╱▔▔╲     │         │   ▒▒▓▓██   │               │
│  │   ╱    ╲    │         │   ▒▒▓▓██   │               │
│  │  ╱──────╲   │         │   ▒▒▓▓██   │               │
│  └─────────────┘         └─────────────┘               │
│  特徵: 立體、透視         特徵: 色彩過渡                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Icon 特徵分析

```json
{
  "iconAnalysis": {
    "style": {
      "type": "outlined",
      "strokeWidth": "1.5px",
      "cornerStyle": "rounded",
      "cornerRadius": "2px"
    },
    "size": {
      "designSize": "24x24",
      "strokeRatio": "1.5/24",
      "opticalBalance": true
    },
    "color": {
      "primary": "#1F2937",
      "secondary": null,
      "gradient": null
    },
    "characteristics": {
      "lineEndings": "round",
      "consistency": "uniform-stroke",
      "detailLevel": "medium",
      "metaphor": "literal"
    }
  }
}
```

### Icon 截取輸出

```markdown
## Icon 截取報告

### 識別到的 Icon (12 個)

| # | 名稱 | 類型 | 尺寸 | 風格 |
|---|------|------|------|------|
| 1 | home | Navigation | 24px | Outlined |
| 2 | search | Action | 24px | Outlined |
| 3 | user | Navigation | 24px | Outlined |
| 4 | settings | Action | 24px | Outlined |
| 5 | bell | Notification | 24px | Outlined |
| 6 | heart | Action | 24px | Filled |
| 7 | share | Action | 20px | Outlined |
| 8 | more | Menu | 24px | Outlined |
| 9 | arrow-left | Navigation | 24px | Outlined |
| 10 | check | Status | 16px | Outlined |
| 11 | close | Action | 24px | Outlined |
| 12 | plus | Action | 24px | Outlined |

### Icon 風格規格

```
風格: Outlined (線性)
線條粗細: 1.5px
圓角: Rounded (2px)
網格: 24x24px
安全區: 2px padding
筆觸端點: Round cap
筆觸連接: Round join
```

### 建議的 Icon 庫

基於截取風格，建議使用:
- Heroicons (https://heroicons.com) - 風格最接近
- Feather Icons - 備選
- Phosphor Icons - 備選
```

---

## 插畫元素截取

### 插畫風格分類

```
插畫風格類型:

┌─────────────────────────────────────────────┐
│ Flat Illustration (扁平插畫)                │
├─────────────────────────────────────────────┤
│ • 無陰影或極少陰影                          │
│ • 純色塊組成                                │
│ • 簡化的形狀                                │
│ • 幾何感強                                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Isometric Illustration (等距插畫)           │
├─────────────────────────────────────────────┤
│ • 30° 角度                                  │
│ • 3D 立體感                                 │
│ • 統一視角                                  │
│ • 技術/產品常用                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Hand-drawn (手繪風格)                       │
├─────────────────────────────────────────────┤
│ • 不規則線條                                │
│ • 紋理質感                                  │
│ • 有機形狀                                  │
│ • 親切溫暖                                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Gradient / 3D (漸層/3D)                     │
├─────────────────────────────────────────────┤
│ • 豐富的色彩過渡                            │
│ • 光影效果                                  │
│ • 現代科技感                                │
│ • 視覺衝擊強                                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Line Art (線條藝術)                         │
├─────────────────────────────────────────────┤
│ • 純線條構成                                │
│ • 簡約優雅                                  │
│ • 可單色或多色                              │
│ • 適合小尺寸                                │
└─────────────────────────────────────────────┘
```

### 插畫元素分析

```json
{
  "illustrationAnalysis": {
    "style": "flat-illustration",
    "colorPalette": [
      "#6366F1",
      "#EC4899",
      "#F59E0B",
      "#10B981",
      "#F8FAFC"
    ],
    "characteristics": {
      "shadowStyle": "none",
      "outlineStyle": "none",
      "shapeStyle": "geometric",
      "detailLevel": "simplified"
    },
    "elements": [
      {
        "type": "character",
        "description": "坐著使用筆電的人物",
        "colors": ["#6366F1", "#F8FAFC", "#1F2937"],
        "position": "center"
      },
      {
        "type": "object",
        "description": "植物裝飾",
        "colors": ["#10B981", "#065F46"],
        "position": "background"
      },
      {
        "type": "shape",
        "description": "抽象幾何背景",
        "colors": ["#EEF2FF", "#C7D2FE"],
        "position": "background"
      }
    ],
    "mood": "professional, friendly, modern",
    "usage": "hero section, empty state, onboarding"
  }
}
```

### 插畫截取輸出

```markdown
## 插畫元素截取報告

### 識別到的插畫元素 (5 個)

| # | 類型 | 描述 | 風格 | 建議用途 |
|---|------|------|------|----------|
| 1 | 人物 | 使用筆電的人 | Flat | Hero/Empty State |
| 2 | 場景 | 辦公桌場景 | Flat | Onboarding |
| 3 | 物件 | 植物裝飾 | Flat | 裝飾元素 |
| 4 | 形狀 | 圓形 blob | Gradient | 背景裝飾 |
| 5 | 形狀 | 抽象線條 | Line | 分隔裝飾 |

### 插畫風格規格

```
風格: Flat Illustration
色彩: 6 色限定調色盤
陰影: 無 (純色塊)
輪廓: 無描邊
形狀: 幾何圓角
人物: 簡化無五官
比例: 誇張可愛
```

### 插畫資源建議

基於截取風格，建議:
- unDraw (https://undraw.co) - 免費可商用
- Blush (https://blush.design) - 可客製顏色
- Humaaans - 人物組合
```

---

## UI 元件截取

### 可截取的 UI 元件

```
UI 元件類型:

┌─────────────────────────────────────────────┐
│ 按鈕 (Buttons)                              │
├─────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐            │
│ │   Primary   │  │  Secondary  │            │
│ └─────────────┘  └─────────────┘            │
│                                             │
│ 截取: 尺寸、圓角、色彩、陰影、字型           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 卡片 (Cards)                                │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │  ┌─────────────────────────────────┐    │ │
│ │  │         Image                   │    │ │
│ │  ├─────────────────────────────────┤    │ │
│ │  │  Title                          │    │ │
│ │  │  Description text here...       │    │ │
│ │  │                     [Button]    │    │ │
│ │  └─────────────────────────────────┘    │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 截取: 結構、圓角、陰影、間距、排版           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 輸入框 (Inputs)                             │
├─────────────────────────────────────────────┤
│ Label                                       │
│ ┌─────────────────────────────────────────┐ │
│ │ Placeholder text                        │ │
│ └─────────────────────────────────────────┘ │
│ Helper text                                 │
│                                             │
│ 截取: 高度、圓角、邊框、標籤位置、狀態色     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 導航 (Navigation)                           │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Logo    Nav1   Nav2   Nav3      [CTA]   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 截取: 佈局、間距、高度、背景處理             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 標籤/徽章 (Tags/Badges)                     │
├─────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐           │
│ │  Tag   │ │ Badge  │ │  Chip  │           │
│ └────────┘ └────────┘ └────────┘           │
│                                             │
│ 截取: 尺寸、圓角、色彩、字型                │
└─────────────────────────────────────────────┘
```

### UI 元件截取輸出

```json
{
  "componentExtraction": {
    "button": {
      "primary": {
        "height": "44px",
        "paddingX": "24px",
        "borderRadius": "8px",
        "background": "#6366F1",
        "backgroundHover": "#4F46E5",
        "textColor": "#FFFFFF",
        "fontSize": "16px",
        "fontWeight": "600",
        "shadow": "0 4px 6px rgba(99, 102, 241, 0.25)"
      },
      "secondary": {
        "height": "44px",
        "paddingX": "24px",
        "borderRadius": "8px",
        "background": "transparent",
        "border": "1px solid #E5E7EB",
        "textColor": "#374151",
        "fontSize": "16px",
        "fontWeight": "500"
      }
    },
    "card": {
      "borderRadius": "16px",
      "padding": "24px",
      "background": "#FFFFFF",
      "shadow": "0 4px 6px rgba(0, 0, 0, 0.05)",
      "border": "1px solid #F3F4F6"
    },
    "input": {
      "height": "48px",
      "paddingX": "16px",
      "borderRadius": "8px",
      "border": "1px solid #D1D5DB",
      "borderFocus": "2px solid #6366F1",
      "background": "#FFFFFF",
      "fontSize": "16px",
      "labelPosition": "top",
      "labelGap": "8px"
    },
    "tag": {
      "height": "28px",
      "paddingX": "12px",
      "borderRadius": "14px",
      "background": "#EEF2FF",
      "textColor": "#4F46E5",
      "fontSize": "14px",
      "fontWeight": "500"
    }
  }
}
```

---

## 素材分類與命名

### 命名規範

```
素材命名規則:

[類型]-[名稱]-[變體]-[尺寸].[格式]

範例:
├── icon-home-outline-24.svg
├── icon-home-filled-24.svg
├── icon-search-outline-20.svg
├── illust-hero-working-lg.svg
├── illust-empty-nodata-md.svg
├── shape-blob-gradient-01.svg
├── avatar-placeholder-sm.png
└── bg-pattern-grid-01.png
```

### 素材目錄結構

```
📁 assets/
├── 📁 icons/
│   ├── 📁 navigation/
│   │   ├── home.svg
│   │   ├── search.svg
│   │   └── menu.svg
│   ├── 📁 action/
│   │   ├── edit.svg
│   │   ├── delete.svg
│   │   └── share.svg
│   ├── 📁 status/
│   │   ├── check.svg
│   │   ├── warning.svg
│   │   └── error.svg
│   └── 📁 social/
│       ├── facebook.svg
│       ├── twitter.svg
│       └── instagram.svg
│
├── 📁 illustrations/
│   ├── 📁 hero/
│   ├── 📁 empty-states/
│   ├── 📁 onboarding/
│   └── 📁 error-pages/
│
├── 📁 shapes/
│   ├── 📁 blobs/
│   ├── 📁 patterns/
│   └── 📁 decorations/
│
├── 📁 photos/
│   ├── 📁 avatars/
│   ├── 📁 backgrounds/
│   └── 📁 products/
│
└── 📁 components/
    ├── buttons.json
    ├── cards.json
    └── inputs.json
```

### 素材清單輸出

```markdown
## 素材清單

### Icons (24 個)
| 名稱 | 類別 | 格式 | 尺寸 |
|------|------|------|------|
| home | navigation | SVG | 24x24 |
| search | action | SVG | 24x24 |
| user | navigation | SVG | 24x24 |
| ... | ... | ... | ... |

### Illustrations (6 個)
| 名稱 | 類別 | 用途 | 尺寸 |
|------|------|------|------|
| hero-working | hero | 首頁橫幅 | 800x600 |
| empty-inbox | empty | 空收件匣 | 400x300 |
| ... | ... | ... | ... |

### Shapes (8 個)
| 名稱 | 類型 | 顏色 | 格式 |
|------|------|------|------|
| blob-01 | blob | gradient | SVG |
| pattern-grid | pattern | mono | SVG |
| ... | ... | ... | ... |
```

---

## 輸出格式規範

### Icon 輸出格式

```
SVG 輸出規格:

┌─────────────────────────────────────────────┐
│ <svg                                        │
│   width="24"                                │
│   height="24"                               │
│   viewBox="0 0 24 24"                       │
│   fill="none"                               │
│   xmlns="http://www.w3.org/2000/svg"        │
│ >                                           │
│   <path                                     │
│     d="M12 2L..."                           │
│     stroke="currentColor"                   │
│     stroke-width="1.5"                      │
│     stroke-linecap="round"                  │
│     stroke-linejoin="round"                 │
│   />                                        │
│ </svg>                                      │
└─────────────────────────────────────────────┘

重點:
├── 使用 currentColor 便於變色
├── viewBox 保持原始比例
├── 移除不必要的 group/id
└── 優化路徑數據
```

### 多尺寸輸出

```
Icon 尺寸輸出:

├── 16x16 (Small)
│   └── icon-name-16.svg
├── 20x20 (Default)
│   └── icon-name-20.svg
├── 24x24 (Medium)
│   └── icon-name-24.svg
└── 32x32 (Large)
    └── icon-name-32.svg

PNG 輸出 (@1x, @2x, @3x):
├── icon-name.png      (24x24)
├── icon-name@2x.png   (48x48)
└── icon-name@3x.png   (72x72)
```

### 插畫輸出格式

```
插畫輸出規格:

SVG (向量):
├── 可縮放
├── 檔案小
├── 可修改顏色
└── 適合: Logo、簡單插畫

PNG (點陣):
├── @1x: 原始尺寸
├── @2x: 2 倍尺寸
├── @3x: 3 倍尺寸
└── 適合: 複雜插畫、照片

WebP (優化):
├── 壓縮率高
├── 支援透明
└── 適合: Web 使用
```

---

## Figma 素材庫建立

### Figma 素材組織

```
📄 Asset Library
│
├── 📑 Icons
│   ├── Frame: Icon Grid (展示所有 icons)
│   ├── Component Set: Navigation Icons
│   ├── Component Set: Action Icons
│   ├── Component Set: Status Icons
│   └── Component Set: Social Icons
│
├── 📑 Illustrations
│   ├── Frame: Hero Illustrations
│   ├── Frame: Empty States
│   ├── Frame: Onboarding
│   └── Frame: Error Pages
│
├── 📑 Shapes & Decorations
│   ├── Frame: Blobs
│   ├── Frame: Patterns
│   └── Frame: Background Elements
│
└── 📑 Photos & Avatars
    ├── Frame: Avatar Placeholders
    └── Frame: Background Photos
```

### Icon Component 設定

```
Icon Component 結構:

Component: icon/[name]
├── Properties
│   ├── Size: 16 | 20 | 24 | 32
│   └── Color: currentColor (可覆寫)
│
├── Variants
│   ├── Style=Outline, Size=24
│   ├── Style=Outline, Size=20
│   ├── Style=Filled, Size=24
│   └── Style=Filled, Size=20
│
└── Auto Layout
    ├── Constraints: Scale
    └── Resizing: Hug contents
```

### 發布為 Library

```markdown
## Figma Library 發布清單

### Icons
- [ ] 所有 icons 已建立為 Component
- [ ] 命名遵循規範 (icon/category/name)
- [ ] 設定正確的 Variants
- [ ] 使用 currentColor
- [ ] 加入描述與關鍵字

### Illustrations
- [ ] 組織為 Frames
- [ ] 設定 Export 規格
- [ ] 加入使用說明

### 發布
- [ ] 加入 Library 描述
- [ ] 設定版本號
- [ ] 發布更新
```

---

## Icon Library 產生

### React Icon Component

```tsx
// Icon component 模板
import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const HomeIcon: React.FC<IconProps> = ({
  size = 24,
  color = 'currentColor',
  className,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);
```

### Icon Index 產生

```tsx
// icons/index.ts
export { HomeIcon } from './HomeIcon';
export { SearchIcon } from './SearchIcon';
export { UserIcon } from './UserIcon';
export { SettingsIcon } from './SettingsIcon';
export { BellIcon } from './BellIcon';
export { HeartIcon } from './HeartIcon';
// ... 其他 icons

// 類型定義
export type IconName =
  | 'home'
  | 'search'
  | 'user'
  | 'settings'
  | 'bell'
  | 'heart';
```

### iOS Swift Icon Set

```swift
// Icons.swift
import SwiftUI

enum AppIcon: String, CaseIterable {
    case home
    case search
    case user
    case settings
    case bell
    case heart

    var image: Image {
        Image(self.rawValue)
    }
}

// 使用
AppIcon.home.image
    .foregroundColor(.primary)
    .frame(width: 24, height: 24)
```

### Android Icon Resources

```kotlin
// Icons.kt
object AppIcons {
    val Home = R.drawable.ic_home
    val Search = R.drawable.ic_search
    val User = R.drawable.ic_user
    val Settings = R.drawable.ic_settings
    val Bell = R.drawable.ic_bell
    val Heart = R.drawable.ic_heart
}

// 使用
Icon(
    painter = painterResource(AppIcons.Home),
    contentDescription = "Home",
    modifier = Modifier.size(24.dp)
)
```

---

## 素材截取報告模板

```markdown
# 素材截取報告

## 📷 來源圖片
[圖片描述]

## 📊 截取摘要

| 類型 | 數量 | 格式 |
|------|------|------|
| Icons | 24 | SVG |
| Illustrations | 6 | SVG/PNG |
| Shapes | 8 | SVG |
| UI Components | 5 | JSON Spec |

## 🔷 Icons

### 風格規格
- 類型: Outlined
- 線寬: 1.5px
- 網格: 24x24
- 圓角: Rounded

### Icon 清單
[詳細清單]

### 相似 Icon 庫推薦
- Heroicons
- Feather Icons

## 🎨 Illustrations

### 風格規格
- 類型: Flat Illustration
- 調色盤: 6 色
- 特徵: 無陰影、幾何形狀

### 元素清單
[詳細清單]

### 相似插畫資源
- unDraw
- Blush

## 📦 輸出檔案

### Figma
- [ ] Icon Components
- [ ] Illustration Frames
- [ ] Shape Library

### Code
- [ ] SVG 檔案
- [ ] React Components
- [ ] iOS Assets
- [ ] Android Resources

### Design Tokens
- [ ] Icon 規格 JSON
- [ ] Component 規格 JSON
```

---

## Production-Ready 素材輸出

本節說明如何產生各平台可直接使用的素材，包含標準目錄結構，直接複製到專案即可使用。

### Android 素材輸出

#### Drawable 目錄結構 (Icon/Image)

```
📁 app/src/main/res/
├── 📁 drawable-ldpi/        # 120 DPI (0.75x)
│   ├── ic_home.png          # 36x36 px
│   ├── ic_search.png        # 36x36 px
│   └── ic_user.png          # 36x36 px
│
├── 📁 drawable-mdpi/        # 160 DPI (1x) - 基準
│   ├── ic_home.png          # 48x48 px
│   ├── ic_search.png        # 48x48 px
│   └── ic_user.png          # 48x48 px
│
├── 📁 drawable-hdpi/        # 240 DPI (1.5x)
│   ├── ic_home.png          # 72x72 px
│   ├── ic_search.png        # 72x72 px
│   └── ic_user.png          # 72x72 px
│
├── 📁 drawable-xhdpi/       # 320 DPI (2x)
│   ├── ic_home.png          # 96x96 px
│   ├── ic_search.png        # 96x96 px
│   └── ic_user.png          # 96x96 px
│
├── 📁 drawable-xxhdpi/      # 480 DPI (3x)
│   ├── ic_home.png          # 144x144 px
│   ├── ic_search.png        # 144x144 px
│   └── ic_user.png          # 144x144 px
│
├── 📁 drawable-xxxhdpi/     # 640 DPI (4x)
│   ├── ic_home.png          # 192x192 px
│   ├── ic_search.png        # 192x192 px
│   └── ic_user.png          # 192x192 px
│
└── 📁 drawable/             # Vector Drawable (SVG 轉換)
    ├── ic_home.xml
    ├── ic_search.xml
    └── ic_user.xml
```

#### Android 尺寸對照表

| 密度 | DPI | 倍率 | 基準 48px 尺寸 | 基準 24px 尺寸 |
|------|-----|------|----------------|----------------|
| ldpi | 120 | 0.75x | 36x36 px | 18x18 px |
| mdpi | 160 | 1x | 48x48 px | 24x24 px |
| hdpi | 240 | 1.5x | 72x72 px | 36x36 px |
| xhdpi | 320 | 2x | 96x96 px | 48x48 px |
| xxhdpi | 480 | 3x | 144x144 px | 72x72 px |
| xxxhdpi | 640 | 4x | 192x192 px | 96x96 px |

#### Android Mipmap (App Icon)

```
📁 app/src/main/res/
├── 📁 mipmap-mdpi/
│   ├── ic_launcher.png              # 48x48 px
│   ├── ic_launcher_round.png        # 48x48 px
│   └── ic_launcher_foreground.png   # 108x108 px
│
├── 📁 mipmap-hdpi/
│   ├── ic_launcher.png              # 72x72 px
│   ├── ic_launcher_round.png        # 72x72 px
│   └── ic_launcher_foreground.png   # 162x162 px
│
├── 📁 mipmap-xhdpi/
│   ├── ic_launcher.png              # 96x96 px
│   ├── ic_launcher_round.png        # 96x96 px
│   └── ic_launcher_foreground.png   # 216x216 px
│
├── 📁 mipmap-xxhdpi/
│   ├── ic_launcher.png              # 144x144 px
│   ├── ic_launcher_round.png        # 144x144 px
│   └── ic_launcher_foreground.png   # 324x324 px
│
├── 📁 mipmap-xxxhdpi/
│   ├── ic_launcher.png              # 192x192 px
│   ├── ic_launcher_round.png        # 192x192 px
│   └── ic_launcher_foreground.png   # 432x432 px
│
└── 📁 mipmap-anydpi-v26/
    ├── ic_launcher.xml              # Adaptive Icon 設定
    └── ic_launcher_round.xml
```

#### Android Adaptive Icon

```xml
<!-- res/mipmap-anydpi-v26/ic_launcher.xml -->
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
    <monochrome android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
```

---

### iOS 素材輸出

#### Asset Catalog 結構

```
📁 Assets.xcassets/
├── 📁 Icons/
│   ├── 📁 home.imageset/
│   │   ├── home.png           # 24x24 px (@1x)
│   │   ├── home@2x.png        # 48x48 px (@2x)
│   │   ├── home@3x.png        # 72x72 px (@3x)
│   │   └── Contents.json
│   │
│   ├── 📁 search.imageset/
│   │   ├── search.png
│   │   ├── search@2x.png
│   │   ├── search@3x.png
│   │   └── Contents.json
│   │
│   └── 📁 user.imageset/
│       ├── user.png
│       ├── user@2x.png
│       ├── user@3x.png
│       └── Contents.json
│
├── 📁 Illustrations/
│   └── 📁 hero-image.imageset/
│       ├── hero-image.png
│       ├── hero-image@2x.png
│       ├── hero-image@3x.png
│       └── Contents.json
│
├── 📁 AppIcon.appiconset/
│   ├── Icon-20.png            # 20x20 (iPad Notification @1x)
│   ├── Icon-20@2x.png         # 40x40 (iPhone Notification @2x)
│   ├── Icon-20@3x.png         # 60x60 (iPhone Notification @3x)
│   ├── Icon-29.png            # 29x29 (iPad Settings @1x)
│   ├── Icon-29@2x.png         # 58x58 (Settings @2x)
│   ├── Icon-29@3x.png         # 87x87 (Settings @3x)
│   ├── Icon-40@2x.png         # 80x80 (Spotlight @2x)
│   ├── Icon-40@3x.png         # 120x120 (Spotlight @3x)
│   ├── Icon-60@2x.png         # 120x120 (iPhone App @2x)
│   ├── Icon-60@3x.png         # 180x180 (iPhone App @3x)
│   ├── Icon-76.png            # 76x76 (iPad App @1x)
│   ├── Icon-76@2x.png         # 152x152 (iPad App @2x)
│   ├── Icon-83.5@2x.png       # 167x167 (iPad Pro @2x)
│   ├── Icon-1024.png          # 1024x1024 (App Store)
│   └── Contents.json
│
└── Contents.json
```

#### iOS Contents.json 範例

```json
{
  "images": [
    {
      "filename": "home.png",
      "idiom": "universal",
      "scale": "1x"
    },
    {
      "filename": "home@2x.png",
      "idiom": "universal",
      "scale": "2x"
    },
    {
      "filename": "home@3x.png",
      "idiom": "universal",
      "scale": "3x"
    }
  ],
  "info": {
    "author": "xcode",
    "version": 1
  }
}
```

#### iOS App Icon Contents.json

```json
{
  "images": [
    {
      "filename": "Icon-20@2x.png",
      "idiom": "iphone",
      "scale": "2x",
      "size": "20x20"
    },
    {
      "filename": "Icon-20@3x.png",
      "idiom": "iphone",
      "scale": "3x",
      "size": "20x20"
    },
    {
      "filename": "Icon-29@2x.png",
      "idiom": "iphone",
      "scale": "2x",
      "size": "29x29"
    },
    {
      "filename": "Icon-29@3x.png",
      "idiom": "iphone",
      "scale": "3x",
      "size": "29x29"
    },
    {
      "filename": "Icon-40@2x.png",
      "idiom": "iphone",
      "scale": "2x",
      "size": "40x40"
    },
    {
      "filename": "Icon-40@3x.png",
      "idiom": "iphone",
      "scale": "3x",
      "size": "40x40"
    },
    {
      "filename": "Icon-60@2x.png",
      "idiom": "iphone",
      "scale": "2x",
      "size": "60x60"
    },
    {
      "filename": "Icon-60@3x.png",
      "idiom": "iphone",
      "scale": "3x",
      "size": "60x60"
    },
    {
      "filename": "Icon-1024.png",
      "idiom": "ios-marketing",
      "scale": "1x",
      "size": "1024x1024"
    }
  ],
  "info": {
    "author": "xcode",
    "version": 1
  }
}
```

#### iOS 尺寸對照表

| 用途 | @1x | @2x | @3x |
|------|-----|-----|-----|
| 小型 Icon (16pt) | 16px | 32px | 48px |
| 標準 Icon (24pt) | 24px | 48px | 72px |
| 大型 Icon (32pt) | 32px | 64px | 96px |
| Tab Bar (25pt) | 25px | 50px | 75px |
| Tab Bar (30pt) | 30px | 60px | 90px |
| Navigation Bar (22pt) | 22px | 44px | 66px |
| Toolbar (22pt) | 22px | 44px | 66px |

---

### Web 素材輸出

#### Web 專案結構

```
📁 public/
├── 📁 icons/
│   ├── 📁 svg/                    # 向量 (最佳選擇)
│   │   ├── home.svg
│   │   ├── search.svg
│   │   └── user.svg
│   │
│   ├── 📁 png/
│   │   ├── 📁 16/                 # 小型
│   │   │   ├── home.png
│   │   │   └── search.png
│   │   ├── 📁 24/                 # 標準
│   │   │   ├── home.png
│   │   │   └── search.png
│   │   ├── 📁 32/                 # 大型
│   │   │   ├── home.png
│   │   │   └── search.png
│   │   └── 📁 48/                 # 特大
│   │       ├── home.png
│   │       └── search.png
│   │
│   └── 📁 sprite/                 # Sprite Sheet
│       ├── icons.svg              # SVG Sprite
│       └── icons.png              # PNG Sprite
│
├── 📁 images/
│   ├── 📁 illustrations/
│   │   ├── hero.svg
│   │   ├── hero.webp              # WebP (優化)
│   │   └── hero.png               # Fallback
│   │
│   └── 📁 backgrounds/
│       ├── pattern.svg
│       └── gradient.webp
│
├── 📁 favicons/                   # 瀏覽器/裝置圖示
│   ├── favicon.ico                # 16x16, 32x32, 48x48 (多尺寸)
│   ├── favicon-16x16.png          # 16x16
│   ├── favicon-32x32.png          # 32x32
│   ├── favicon-96x96.png          # 96x96
│   ├── favicon-192x192.png        # 192x192 (Android Chrome)
│   ├── favicon-512x512.png        # 512x512 (PWA)
│   ├── apple-touch-icon.png       # 180x180 (iOS Safari)
│   ├── apple-touch-icon-152x152.png
│   ├── apple-touch-icon-167x167.png
│   ├── apple-touch-icon-180x180.png
│   ├── safari-pinned-tab.svg      # Safari Pinned Tab (單色 SVG)
│   ├── mstile-144x144.png         # Windows Tile
│   ├── mstile-150x150.png
│   ├── mstile-310x310.png
│   └── browserconfig.xml          # Windows 設定
│
├── 📁 og/                         # Open Graph / Social
│   ├── og-image.png               # 1200x630 (Facebook/LinkedIn)
│   ├── og-image-square.png        # 1200x1200 (通用)
│   ├── twitter-card.png           # 1200x600 (Twitter)
│   └── twitter-card-summary.png   # 800x800 (Twitter Summary)
│
├── manifest.json                  # PWA Manifest
└── browserconfig.xml              # Windows Tile 設定
```

#### Web Favicon 尺寸規格

| 檔案名稱 | 尺寸 | 用途 |
|----------|------|------|
| favicon.ico | 16, 32, 48 | 瀏覽器標籤 (多尺寸 ICO) |
| favicon-16x16.png | 16x16 | 瀏覽器標籤 |
| favicon-32x32.png | 32x32 | 瀏覽器標籤 (高 DPI) |
| favicon-96x96.png | 96x96 | 桌面捷徑 |
| apple-touch-icon.png | 180x180 | iOS Safari (必要) |
| favicon-192x192.png | 192x192 | Android Chrome |
| favicon-512x512.png | 512x512 | PWA Splash |
| safari-pinned-tab.svg | 向量 | Safari 釘選標籤 |
| mstile-144x144.png | 144x144 | Windows 8/10 Tile |
| og-image.png | 1200x630 | Facebook/LinkedIn 分享 |
| twitter-card.png | 1200x600 | Twitter 分享 |

#### Web manifest.json

```json
{
  "name": "App Name",
  "short_name": "App",
  "icons": [
    {
      "src": "/favicons/favicon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/favicons/favicon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/favicons/favicon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "theme_color": "#6366F1",
  "background_color": "#FFFFFF",
  "display": "standalone"
}
```

#### HTML Head 設定

```html
<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="/favicons/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicons/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicons/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="96x96" href="/favicons/favicon-96x96.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" href="/favicons/apple-touch-icon.png">
<link rel="apple-touch-icon" sizes="152x152" href="/favicons/apple-touch-icon-152x152.png">
<link rel="apple-touch-icon" sizes="167x167" href="/favicons/apple-touch-icon-167x167.png">
<link rel="apple-touch-icon" sizes="180x180" href="/favicons/apple-touch-icon-180x180.png">

<!-- Safari Pinned Tab -->
<link rel="mask-icon" href="/favicons/safari-pinned-tab.svg" color="#6366F1">

<!-- Windows Tile -->
<meta name="msapplication-TileColor" content="#6366F1">
<meta name="msapplication-TileImage" content="/favicons/mstile-144x144.png">
<meta name="msapplication-config" content="/browserconfig.xml">

<!-- PWA -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#6366F1">

<!-- Open Graph -->
<meta property="og:image" content="https://example.com/og/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/twitter-card.png">
```

---

### 跨平台素材輸出腳本

#### 輸出目錄結構總覽

```
📁 production-assets/
│
├── 📁 android/
│   └── 📁 app/src/main/res/
│       ├── drawable-ldpi/
│       ├── drawable-mdpi/
│       ├── drawable-hdpi/
│       ├── drawable-xhdpi/
│       ├── drawable-xxhdpi/
│       ├── drawable-xxxhdpi/
│       ├── drawable/              # Vector XML
│       └── mipmap-*/              # App Icon
│
├── 📁 ios/
│   └── 📁 Assets.xcassets/
│       ├── Icons/
│       ├── Illustrations/
│       └── AppIcon.appiconset/
│
├── 📁 web/
│   └── 📁 public/
│       ├── icons/
│       ├── images/
│       ├── favicons/
│       ├── og/
│       └── manifest.json
│
└── 📁 figma/
    ├── icons.fig                  # Figma Icon Library
    └── export-settings.json       # 匯出設定
```

#### 素材匯出清單

```markdown
## Production Assets 匯出清單

### Android ✓
- [ ] drawable-ldpi/ (36px icons)
- [ ] drawable-mdpi/ (48px icons)
- [ ] drawable-hdpi/ (72px icons)
- [ ] drawable-xhdpi/ (96px icons)
- [ ] drawable-xxhdpi/ (144px icons)
- [ ] drawable-xxxhdpi/ (192px icons)
- [ ] drawable/ (Vector XMLs)
- [ ] mipmap-*/ (App Icons)
- [ ] Adaptive Icon XMLs

### iOS ✓
- [ ] *.imageset/ (@1x, @2x, @3x)
- [ ] Contents.json for each asset
- [ ] AppIcon.appiconset/ (all sizes)
- [ ] SF Symbol 替代建議

### Web ✓
- [ ] SVG icons (優化)
- [ ] PNG icons (16/24/32/48)
- [ ] Favicon set (ico, png, svg)
- [ ] Apple Touch Icons
- [ ] manifest.json
- [ ] browserconfig.xml
- [ ] OG Images (1200x630, 1200x1200)
- [ ] Twitter Cards

### 品質檢查
- [ ] 所有尺寸正確
- [ ] 檔案已壓縮優化
- [ ] 命名符合規範
- [ ] Contents.json 正確
- [ ] 透明度正確處理
```

---

## 素材截取檢查清單

```
Icon 截取
□ 識別所有 icons
□ 分析風格特徵
□ 記錄尺寸規格
□ 建議替代資源
□ 輸出 SVG 規格

插畫截取
□ 識別插畫元素
□ 分析風格類型
□ 記錄色彩調色盤
□ 標註用途建議
□ 建議相似資源

UI 元件截取
□ 識別元件類型
□ 截取規格數值
□ 記錄狀態變化
□ 輸出 JSON 規格
□ 產生 Figma Component

輸出完整性
□ SVG 檔案優化
□ PNG 多倍率輸出
□ Figma Library 建立
□ Code Components 產生
□ 素材清單文件
```
