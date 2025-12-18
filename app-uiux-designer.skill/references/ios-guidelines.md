# iOS Human Interface Guidelines 設計指南

本文件基於 Apple Human Interface Guidelines，提供 iOS App 設計的核心規範。

## 目錄
1. [設計原則](#設計原則)
2. [佈局與間距](#佈局與間距)
3. [導航模式](#導航模式)
4. [元件規範](#元件規範)
5. [字型系統](#字型系統)
6. [顏色系統](#顏色系統)
7. [圖標規範](#圖標規範)
8. [動畫與轉場](#動畫與轉場)
9. [手勢操作](#手勢操作)
10. [Safe Area 與適配](#safe-area-與適配)

---

## 設計原則

### Apple 設計核心理念

1. **美學完整性 (Aesthetic Integrity)**
   - 外觀與功能一致
   - 視覺設計強化使用者對內容的理解

2. **一致性 (Consistency)**
   - 遵循系統標準元件
   - 符合使用者既有心智模型

3. **直接操控 (Direct Manipulation)**
   - 內容可直接觸控互動
   - 即時視覺回饋

4. **回饋 (Feedback)**
   - 每個操作都有明確回應
   - 使用觸覺回饋 (Haptics)

5. **隱喻 (Metaphors)**
   - 運用真實世界概念
   - 降低學習成本

6. **使用者控制 (User Control)**
   - 使用者主導操作
   - 提供取消/復原機制

---

## 佈局與間距

### 基礎網格系統

```
基礎單位: 8pt
最小間距: 8pt
標準間距: 16pt
大間距: 24pt / 32pt
```

### 螢幕邊距 (Margins)

| 裝置 | 邊距 |
|------|------|
| iPhone | 16pt |
| iPhone Max | 20pt |
| iPad | 20pt |

### 內容寬度

```swift
// Readable Content Width
iPhone: 螢幕寬度 - 32pt (左右各 16pt)
iPad: 最大 672pt (置中)
```

### Safe Area Insets

```
iPhone (無瀏海): 上 20pt, 下 0pt
iPhone (Dynamic Island): 上 59pt, 下 34pt
iPhone (瀏海): 上 47pt, 下 34pt
```

---

## 導航模式

### Tab Bar (標籤列)

- **位置**: 螢幕底部
- **數量**: 3-5 個項目
- **高度**: 49pt (不含 Safe Area)
- **圖標**: 25x25pt (選中/未選中狀態)

```
標籤項目結構:
┌─────────────────────────────────────┐
│  🏠     🔍     ➕     💬     👤    │
│  首頁   搜尋   新增   訊息   我的   │
└─────────────────────────────────────┘
高度: 49pt + Safe Area Bottom
```

### Navigation Bar (導航列)

- **高度**: 44pt (不含狀態列)
- **標題**: Large Title 34pt / Standard 17pt
- **按鈕**: 左側返回，右側操作

```
Large Title 模式:
┌─────────────────────────────────────┐
│ 狀態列                    44pt      │
├─────────────────────────────────────┤
│ ← 返回                    編輯      │ 44pt
├─────────────────────────────────────┤
│ 標題                                │ 52pt
│ Title                               │
└─────────────────────────────────────┘

捲動後 (Inline Title):
┌─────────────────────────────────────┐
│ ← 返回      標題          編輯      │ 44pt
└─────────────────────────────────────┘
```

### 返回按鈕規範

```
文字: 前一頁標題 (最多 12 字元，超過顯示 "返回")
圖標: chevron.left (SF Symbol)
熱區: 44x44pt 最小
```

### Modal 模式

| 類型 | 用途 | 樣式 |
|------|------|------|
| Sheet | 補充內容 | 底部滑入，可下滑關閉 |
| Full Screen | 獨立任務 | 全螢幕覆蓋 |
| Page Sheet | 表單/設定 | iPad 居中卡片 |

---

## 元件規範

### 按鈕 (Buttons)

**系統按鈕尺寸:**

| 類型 | 高度 | 內距 |
|------|------|------|
| Large | 50pt | 水平 20pt |
| Medium | 44pt | 水平 16pt |
| Small | 34pt | 水平 12pt |

**按鈕類型:**

```
Filled (主要): 填滿背景色
Tinted (次要): 淺色背景 + 強調色文字
Gray (中性): 灰色背景
Plain (文字): 僅文字，無背景
```

**按鈕狀態:**

```css
Normal: 100% 不透明度
Highlighted: 70% 不透明度
Disabled: 30% 不透明度
```

### 列表 (Lists)

**列表項目高度:**

| 內容類型 | 高度 |
|----------|------|
| 單行文字 | 44pt |
| 雙行文字 | 60pt |
| 三行文字 | 76pt |

**列表結構:**

```
┌─────────────────────────────────────────────┐
│ 🖼️ │ 標題文字                        │ > │
│ 48 │ 副標題說明文字                   │   │
│ pt │                                  │   │
└─────────────────────────────────────────────┘
左側: 16pt | 圖標: 48pt | 間距: 12pt | 右側: 16pt
```

### 輸入框 (Text Fields)

```
高度: 44pt (單行) / 動態 (多行)
圓角: 10pt
內距: 水平 12pt, 垂直 11pt
邊框: 1pt (未聚焦灰色, 聚焦藍色)
```

**狀態:**
- Default: 灰色邊框
- Focused: 藍色邊框
- Error: 紅色邊框 + 錯誤訊息
- Disabled: 50% 不透明度

### 開關 (Toggle/Switch)

```
尺寸: 51 x 31pt
軌道圓角: 全圓角
圓點: 27pt 圓形
開啟: 綠色 (#34C759)
關閉: 灰色背景
```

### Slider (滑桿)

```
軌道高度: 4pt
圓點: 28pt
最小觸控區: 44x44pt
```

### Segmented Control (分段控制)

```
高度: 32pt
圓角: 8pt
最少: 2 段
最多: 5 段
```

---

## 字型系統

### SF Pro 字型家族

**動態字型大小 (Dynamic Type):**

| 樣式 | 字級 | 字重 |
|------|------|------|
| Large Title | 34pt | Bold |
| Title 1 | 28pt | Bold |
| Title 2 | 22pt | Bold |
| Title 3 | 20pt | Semibold |
| Headline | 17pt | Semibold |
| Body | 17pt | Regular |
| Callout | 16pt | Regular |
| Subheadline | 15pt | Regular |
| Footnote | 13pt | Regular |
| Caption 1 | 12pt | Regular |
| Caption 2 | 11pt | Regular |

**行高建議:**

```
標題: 字級 × 1.2
內文: 字級 × 1.4 ~ 1.5
```

**字型使用原則:**
1. 優先使用系統字型 (SF Pro)
2. 支援 Dynamic Type 可調整大小
3. 粗體用於強調，避免過度使用
4. 中文使用 PingFang TC/SC

---

## 顏色系統

### 系統顏色

| 名稱 | 淺色模式 | 深色模式 |
|------|----------|----------|
| systemBlue | #007AFF | #0A84FF |
| systemGreen | #34C759 | #30D158 |
| systemRed | #FF3B30 | #FF453A |
| systemOrange | #FF9500 | #FF9F0A |
| systemYellow | #FFCC00 | #FFD60A |
| systemPink | #FF2D55 | #FF375F |
| systemPurple | #AF52DE | #BF5AF2 |
| systemTeal | #5AC8FA | #64D2FF |

### 語義顏色

| 用途 | 淺色模式 | 深色模式 |
|------|----------|----------|
| label | #000000 | #FFFFFF |
| secondaryLabel | #3C3C43 (60%) | #EBEBF5 (60%) |
| tertiaryLabel | #3C3C43 (30%) | #EBEBF5 (30%) |
| systemBackground | #FFFFFF | #000000 |
| secondaryBackground | #F2F2F7 | #1C1C1E |
| separator | #3C3C43 (29%) | #545458 (65%) |

### 顏色使用原則

1. **品牌色**: 作為強調色使用，不超過 10%
2. **語義顏色**: 使用系統提供的語義顏色
3. **深色模式**: 必須支援，顏色需調整亮度
4. **對比度**: 文字與背景至少 4.5:1

---

## 圖標規範

### SF Symbols

Apple 官方圖標庫，支援 5000+ 個向量圖標。

**圖標尺寸:**

| 用途 | 尺寸 |
|------|------|
| Tab Bar | 25pt |
| Navigation Bar | 22pt |
| 列表項目 | 24-28pt |
| 按鈕內 | 17-20pt |

**圖標樣式:**

```
Hierarchical: 多層次灰階
Palette: 雙色調
Multicolor: 多彩色
```

**圖標渲染模式:**

```swift
.renderingMode(.template)  // 可調色
.renderingMode(.original)  // 保持原色
```

### App Icon

**尺寸需求:**

| 用途 | 尺寸 |
|------|------|
| App Store | 1024 x 1024px |
| iPhone @3x | 180 x 180px |
| iPhone @2x | 120 x 120px |
| iPad @2x | 152 x 152px |
| iPad Pro | 167 x 167px |

**設計原則:**
- 簡潔辨識
- 避免文字
- 使用獨特形狀
- 支援深色模式變體

---

## 動畫與轉場

### 標準時間曲線

```swift
easeInOut: 0.25s  // 標準互動
easeOut: 0.2s     // 元素出現
easeIn: 0.15s     // 元素消失
spring: 0.5s      // 彈性效果
```

### 轉場動畫

| 類型 | 時長 | 用途 |
|------|------|------|
| Push | 0.35s | 頁面推進 |
| Modal | 0.3s | 模態視窗 |
| Fade | 0.2s | 淡入淡出 |
| Sheet | 0.3s | 底部滑入 |

### 觸覺回饋 (Haptics)

```swift
.selection      // 選取
.light          // 輕觸
.medium         // 中等
.heavy          // 重擊
.success        // 成功
.warning        // 警告
.error          // 錯誤
```

---

## 手勢操作

### 標準手勢

| 手勢 | 操作 |
|------|------|
| 點擊 (Tap) | 選取、觸發 |
| 長按 (Long Press) | 預覽、上下文選單 |
| 滑動 (Swipe) | 刪除、更多操作 |
| 拖曳 (Drag) | 移動、重排 |
| 捏合 (Pinch) | 縮放 |
| 旋轉 (Rotate) | 旋轉內容 |

### 邊緣手勢

```
左邊緣右滑: 返回上一頁
底部上滑: 回主畫面
底部上滑停住: App 切換器
```

### 滑動操作 (Swipe Actions)

```
左滑: 顯示主要操作 (刪除、更多)
右滑: 顯示次要操作 (標記、封存)
操作按鈕寬度: 80pt
```

---

## Safe Area 與適配

### 裝置適配策略

1. **使用 Auto Layout**
   - 相對約束優於絕對數值
   - 使用 Safe Area 約束

2. **支援所有尺寸**
   - iPhone SE (小螢幕)
   - iPhone Max (大螢幕)
   - iPad (平板)

3. **方向支援**
   - Portrait (直向)
   - Landscape (橫向，視需求)

### Safe Area 處理

```swift
// 內容應在 Safe Area 內
safeAreaInsets.top
safeAreaInsets.bottom
safeAreaInsets.left
safeAreaInsets.right

// 背景可延伸至 Safe Area 外
ignoresSafeArea(.all)
```

### Dynamic Island 適配

```
避免: 在 Dynamic Island 區域放置互動元素
可以: 背景延伸、動畫效果與 Dynamic Island 互動
```

---

## 設計檢查清單

### 上架前確認

- [ ] 支援所有 iPhone 尺寸
- [ ] 支援深色模式
- [ ] 支援 Dynamic Type
- [ ] 觸控目標至少 44x44pt
- [ ] 正確處理 Safe Area
- [ ] 提供觸覺回饋
- [ ] 支援 VoiceOver
- [ ] App Icon 所有尺寸
- [ ] 啟動畫面 (Launch Screen)
- [ ] 符合 App Store 審查指南
