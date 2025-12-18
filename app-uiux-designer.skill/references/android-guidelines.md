# Android Material Design 3 設計指南

本文件基於 Google Material Design 3 (Material You)，提供 Android App 設計的核心規範。

## 目錄
1. [設計原則](#設計原則)
2. [佈局與間距](#佈局與間距)
3. [導航模式](#導航模式)
4. [元件規範](#元件規範)
5. [字型系統](#字型系統)
6. [顏色系統](#顏色系統)
7. [圖標規範](#圖標規範)
8. [動畫與動態](#動畫與動態)
9. [手勢操作](#手勢操作)
10. [適應性佈局](#適應性佈局)

---

## 設計原則

### Material Design 3 核心理念

1. **Personal (個人化)**
   - Dynamic Color 動態顏色
   - 從使用者桌布提取色彩主題

2. **Adaptive (適應性)**
   - 響應不同螢幕尺寸
   - 手機、平板、摺疊設備、桌面

3. **Expressive (表達性)**
   - 更大的圓角
   - 更生動的動畫

4. **Accessible (無障礙)**
   - 高對比度選項
   - 清晰的視覺層級

---

## 佈局與間距

### 基礎單位

```
基礎單位: 8dp
最小觸控目標: 48dp
推薦觸控目標: 48dp x 48dp
```

### 間距系統

```kotlin
// Spacing scale
val spacing4 = 4.dp
val spacing8 = 8.dp
val spacing12 = 12.dp
val spacing16 = 16.dp
val spacing24 = 24.dp
val spacing32 = 32.dp
val spacing48 = 48.dp
val spacing64 = 64.dp
```

### 螢幕邊距

| 螢幕寬度 | 邊距 |
|----------|------|
| < 600dp (Compact) | 16dp |
| 600-839dp (Medium) | 24dp |
| ≥ 840dp (Expanded) | 24dp |

### Window Size Classes

```
Compact: < 600dp (手機)
Medium: 600-839dp (摺疊設備/小平板)
Expanded: ≥ 840dp (大平板/桌面)
```

---

## 導航模式

### Navigation Bar (底部導航)

- **適用**: 3-5 個主要目的地
- **高度**: 80dp
- **圖標**: 24dp
- **標籤**: 始終顯示

```
┌─────────────────────────────────────────┐
│                                         │
│              內容區域                    │
│                                         │
├─────────────────────────────────────────┤
│   🏠      📋      ➕      💬      👤    │
│  Home   Tasks    Add   Messages  Profile │
└─────────────────────────────────────────┘
高度: 80dp
```

### Navigation Rail (側邊導航)

- **適用**: Medium/Expanded 螢幕
- **寬度**: 80dp (標準) / 360dp (帶標籤)

```
┌──────┬──────────────────────────────────┐
│  ☰   │                                  │
│      │                                  │
│  🏠  │                                  │
│ Home │           內容區域                │
│      │                                  │
│  📋  │                                  │
│Tasks │                                  │
│      │                                  │
│  ⚙️  │                                  │
└──────┴──────────────────────────────────┘
```

### Navigation Drawer (抽屜導航)

**Modal Drawer (模態):**
```
┌────────────────────┬────────────────────┐
│     Header         │                    │
│                    │                    │
├────────────────────┤    被遮罩的        │
│ 🏠 Home            │    內容區域        │
│ 📋 Tasks           │                    │
│ 💬 Messages        │                    │
├────────────────────┤                    │
│ ⚙️ Settings        │                    │
│ ❓ Help            │                    │
└────────────────────┴────────────────────┘
寬度: 360dp (最大)
```

### Top App Bar

**類型:**

```
Center-aligned (居中):
┌─────────────────────────────────────┐
│  ←            Title            ⋮   │
└─────────────────────────────────────┘

Small (小型):
┌─────────────────────────────────────┐
│  ←   Title                     ⋮   │
└─────────────────────────────────────┘

Medium (中型):
┌─────────────────────────────────────┐
│  ←                             ⋮   │
│  Title                              │
└─────────────────────────────────────┘

Large (大型):
┌─────────────────────────────────────┐
│  ←                             ⋮   │
│                                     │
│  Title                              │
└─────────────────────────────────────┘

高度: Small 64dp / Medium 112dp / Large 152dp
```

---

## 元件規範

### Buttons 按鈕

**類型與層級:**

| 類型 | 強調程度 | 用途 |
|------|----------|------|
| Filled | 最高 | 主要動作 |
| Filled Tonal | 高 | 次要重要動作 |
| Outlined | 中 | 輔助動作 |
| Text | 低 | 最低優先級動作 |
| Elevated | 高 | 需要分離的動作 |

**尺寸:**
```
高度: 40dp
最小寬度: 48dp
水平內距: 24dp
圓角: 20dp (全圓角)
```

**FAB (Floating Action Button):**
```
Small FAB: 40dp
FAB: 56dp
Large FAB: 96dp
Extended FAB: 高度 56dp，寬度可變

位置: 右下角
距離邊緣: 16dp
```

### Cards 卡片

**類型:**

| 類型 | 描述 |
|------|------|
| Elevated | 有陰影 |
| Filled | 填滿背景色 |
| Outlined | 有邊框 |

**規格:**
```
圓角: 12dp
內距: 16dp
陰影 (Elevated): Elevation 1 (1dp)
邊框 (Outlined): 1dp
```

### Chips 標籤

**類型:**

```
Assist: 智慧建議動作
Filter: 篩選選項 (可多選)
Input: 使用者輸入的內容
Suggestion: 動態建議
```

**規格:**
```
高度: 32dp
圓角: 8dp
內距: 水平 16dp
圖標: 18dp
```

### Lists 列表

**列表項目高度:**

| 內容 | 高度 |
|------|------|
| 單行 | 56dp |
| 雙行 | 72dp |
| 三行 | 88dp |

**結構:**
```
┌─────────────────────────────────────────────┐
│ 🖼️ │ Headline                       │  ⋮  │
│ 40 │ Supporting text                │     │
│ dp │                                │     │
└─────────────────────────────────────────────┘
Leading: 圖標/頭像  |  Content  |  Trailing: 操作
```

### Text Fields 輸入框

**類型:**
```
Filled: 填滿背景 (推薦)
Outlined: 邊框樣式
```

**狀態:**
```
Enabled: 預設狀態
Focused: 聚焦 (標籤上浮)
Hovered: 懸停
Error: 錯誤 (紅色)
Disabled: 禁用
```

**規格:**
```
高度: 56dp
圓角: 頂部 4dp (Filled) / 全部 4dp (Outlined)
標籤: 浮動標籤動畫
輔助文字: 位於輸入框下方
```

### Dialogs 對話框

**類型:**

```
Basic Dialog:
┌─────────────────────────────────────┐
│           Icon (可選)               │
│                                     │
│            Headline                 │
│                                     │
│        Supporting text              │
│                                     │
├─────────────────────────────────────┤
│              [Cancel]  [Confirm]    │
└─────────────────────────────────────┘

Full-screen Dialog (複雜內容):
┌─────────────────────────────────────┐
│ ✕  Title                     Save   │
├─────────────────────────────────────┤
│                                     │
│           Full content              │
│                                     │
└─────────────────────────────────────┘
```

**規格:**
```
最小寬度: 280dp
最大寬度: 560dp
圓角: 28dp
內距: 24dp
```

### Bottom Sheets

**類型:**
```
Standard: 與內容共存
Modal: 帶遮罩，需關閉
```

**規格:**
```
圓角: 頂部 28dp
拖曳指示器: 32dp x 4dp, 居中
最大高度: 螢幕高度的 90%
```

### Snackbar

```
┌─────────────────────────────────────────────┐
│  Message text                      [Action] │
└─────────────────────────────────────────────┘

位置: 底部，FAB 之上
持續時間: 4-10 秒
圓角: 4dp
```

---

## 字型系統

### Type Scale (MD3)

| Role | 字級 | 字重 | 行高 |
|------|------|------|------|
| Display Large | 57sp | 400 | 64sp |
| Display Medium | 45sp | 400 | 52sp |
| Display Small | 36sp | 400 | 44sp |
| Headline Large | 32sp | 400 | 40sp |
| Headline Medium | 28sp | 400 | 36sp |
| Headline Small | 24sp | 400 | 32sp |
| Title Large | 22sp | 400 | 28sp |
| Title Medium | 16sp | 500 | 24sp |
| Title Small | 14sp | 500 | 20sp |
| Body Large | 16sp | 400 | 24sp |
| Body Medium | 14sp | 400 | 20sp |
| Body Small | 12sp | 400 | 16sp |
| Label Large | 14sp | 500 | 20sp |
| Label Medium | 12sp | 500 | 16sp |
| Label Small | 11sp | 500 | 16sp |

### Roboto 字型

```
字重: 100 Thin, 300 Light, 400 Regular,
      500 Medium, 700 Bold, 900 Black
推薦: Regular (內文), Medium (強調), Bold (標題)
```

---

## 顏色系統

### Dynamic Color (動態顏色)

Material You 從使用者桌布提取色彩：

```
Primary: 主色調
Secondary: 輔助色調
Tertiary: 第三色調
Neutral: 中性色
Error: 錯誤色
```

### Tonal Palettes (色調調色板)

每個顏色有 13 個色調層級：

```
0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100

例如 Primary:
primary0: #000000
primary10: #21005D
primary20: #381E72
primary30: #4F378B
primary40: #6750A4  ← Primary
primary50: #7F67BE
...
primary100: #FFFFFF
```

### 色彩角色 (Color Roles)

**Light Theme:**
| Role | 用途 |
|------|------|
| Primary | 主要元件 |
| On Primary | Primary 上的內容 |
| Primary Container | 主要容器背景 |
| On Primary Container | 容器上的內容 |
| Surface | 頁面背景 |
| On Surface | 頁面上的內容 |
| Surface Variant | 次要背景 |
| Outline | 邊框 |
| Error | 錯誤狀態 |

### 深色主題

深色主題使用相同的色調調色板，但選取不同色調：

```
Light Primary: primary40
Dark Primary: primary80

Light Surface: neutral99
Dark Surface: neutral10
```

---

## 圖標規範

### Material Symbols

Google 官方圖標庫，支援 3 種樣式：

```
Outlined: 線條風格
Rounded: 圓角風格
Sharp: 銳角風格
```

**可變屬性:**
```
Fill: 0-1 (填滿程度)
Weight: 100-700 (線條粗細)
Grade: -25 to 200 (對比度)
Optical Size: 20-48 (光學尺寸)
```

**尺寸:**
| 用途 | 尺寸 |
|------|------|
| Navigation | 24dp |
| Action | 24dp |
| 列表圖標 | 24dp |
| FAB | 24dp |
| 小圖標 | 18dp |

### App Icon

**尺寸需求:**
```
Adaptive Icon:
- Foreground: 108dp x 108dp
- Background: 108dp x 108dp
- Safe zone: 66dp (圓形遮罩)

Legacy:
- xxxhdpi: 192px
- xxhdpi: 144px
- xhdpi: 96px
- hdpi: 72px
- mdpi: 48px
```

**Adaptive Icon 結構:**
```
┌─────────────────────┐
│    Background       │  ← 可為純色或圖片
│  ┌───────────────┐  │
│  │  Foreground   │  │  ← 主圖標
│  │               │  │
│  └───────────────┘  │
└─────────────────────┘
```

---

## 動畫與動態

### 動畫原則

1. **Informative (資訊性)**
   - 動畫傳達狀態變化

2. **Focused (聚焦)**
   - 引導使用者注意力

3. **Expressive (表達性)**
   - 展現品牌個性

### Easing 曲線

```kotlin
// Standard easing (大多數動畫)
emphasized = CubicBezierEasing(0.2f, 0f, 0f, 1f)
emphasizedDecelerate = CubicBezierEasing(0.05f, 0.7f, 0.1f, 1f)
emphasizedAccelerate = CubicBezierEasing(0.3f, 0f, 0.8f, 0.15f)

// 標準曲線
standard = CubicBezierEasing(0.2f, 0f, 0f, 1f)
standardDecelerate = CubicBezierEasing(0f, 0f, 0f, 1f)
standardAccelerate = CubicBezierEasing(0.3f, 0f, 1f, 1f)
```

### 持續時間

```kotlin
// Duration tokens
short1 = 50.ms
short2 = 100.ms
short3 = 150.ms
short4 = 200.ms
medium1 = 250.ms
medium2 = 300.ms
medium3 = 350.ms
medium4 = 400.ms
long1 = 450.ms
long2 = 500.ms
long3 = 550.ms
long4 = 600.ms
```

### 轉場動畫

**Container Transform:**
```
元素變形為另一個元素
用於: 卡片 → 詳細頁、FAB → 頁面
```

**Shared Axis:**
```
沿 X、Y 或 Z 軸移動
用於: 步驟導航、Tab 切換
```

**Fade Through:**
```
淡出再淡入
用於: 底部導航切換
```

**Fade:**
```
簡單淡入淡出
用於: Dialog、Snackbar
```

---

## 手勢操作

### 標準手勢

| 手勢 | 操作 |
|------|------|
| Tap | 選取、觸發 |
| Long Press | 選取、拖曳準備 |
| Swipe | 刪除、操作、導航 |
| Drag | 移動、重排序 |
| Pinch | 縮放 |

### 手勢導航

```
從左邊緣右滑: 返回
從底部上滑: 回主畫面
從底部上滑停住: 最近應用程式
底部橫滑: 切換應用程式
```

### 可預測返回 (Predictive Back)

Android 13+ 支援返回手勢預覽：
```
滑動時顯示前一個畫面預覽
支援客製化動畫
```

---

## 適應性佈局

### Canonical Layouts (標準佈局)

**List-Detail:**
```
Compact:
┌─────────────────────┐    ┌─────────────────────┐
│ List                │ →  │ Detail              │
│ Item 1              │    │                     │
│ Item 2              │    │                     │
│ Item 3              │    │                     │
└─────────────────────┘    └─────────────────────┘

Expanded:
┌─────────────┬───────────────────────────────────┐
│ List        │            Detail                 │
│ Item 1      │                                   │
│ Item 2      │                                   │
│ Item 3      │                                   │
└─────────────┴───────────────────────────────────┘
```

**Supporting Pane:**
```
┌─────────────────────────────────┬───────────────┐
│                                 │  Supporting   │
│        Main Content             │    Pane       │
│                                 │               │
└─────────────────────────────────┴───────────────┘
```

**Feed:**
```
Compact: 單欄
Expanded: 2-3 欄網格
```

### 摺疊設備適配

```
展開: 使用 Expanded 佈局
摺疊: 使用 Compact 佈局
桌面模式: 類似平板佈局
```

---

## 設計檢查清單

### 上架前確認

- [ ] 支援所有螢幕尺寸 (Compact/Medium/Expanded)
- [ ] 支援深色主題
- [ ] 支援 Dynamic Color (Android 12+)
- [ ] 觸控目標至少 48x48dp
- [ ] 支援手勢導航
- [ ] 支援 TalkBack (螢幕閱讀器)
- [ ] Adaptive Icon 正確顯示
- [ ] 動畫效能流暢 (60fps)
- [ ] 遵循 Material Design 3 規範
- [ ] 通過 Google Play Store 審查
