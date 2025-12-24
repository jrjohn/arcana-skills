# Figma 整合與設計資產管理指南

## Figma 專案結構

### 建議的 Figma 檔案組織

```
{專案名稱} - Medical App
│
├── 📄 Cover                          # 封面頁
├── 📄 Design System                  # 設計系統
│   ├── Colors                        # 色彩系統
│   ├── Typography                    # 字型系統
│   ├── Spacing & Grid                # 間距與格線
│   ├── Icons                         # 圖標庫
│   ├── Components                    # 元件庫
│   └── Patterns                      # 設計模式
│
├── 📄 App Icons                      # App 圖標設計
├── 📄 Splash & Onboarding           # 啟動畫面
│
├── 📄 Authentication                 # 認證模組
│   ├── SCR-001 - Login
│   ├── SCR-002 - Register
│   └── SCR-003 - Forgot Password
│
├── 📄 Home & Dashboard              # 首頁模組
│   ├── SCR-010 - Home Dashboard
│   └── SCR-011 - Quick Actions
│
├── 📄 Patient Management            # 病患管理模組
│   ├── SCR-020 - Patient List
│   ├── SCR-021 - Patient Detail
│   └── SCR-022 - Patient History
│
├── 📄 Clinical Features             # 臨床功能模組
│   └── ...
│
└── 📄 Settings & Profile            # 設定模組
    └── ...
```

## Design System 設計規範

### 色彩系統 (Colors)

#### 醫療軟體建議色彩

```
Primary Colors (主色)
├── primary-50:  #E3F2FD    (最淺)
├── primary-100: #BBDEFB
├── primary-200: #90CAF9
├── primary-300: #64B5F6
├── primary-400: #42A5F5
├── primary-500: #2196F3    (主要)
├── primary-600: #1E88E5
├── primary-700: #1976D2
├── primary-800: #1565C0
└── primary-900: #0D47A1    (最深)

Semantic Colors (語意色彩)
├── success:  #4CAF50       (成功/正常)
├── warning:  #FF9800       (警告)
├── error:    #F44336       (錯誤/危急)
├── info:     #2196F3       (資訊)

Clinical Colors (臨床專用)
├── critical: #D32F2F       (危急值)
├── abnormal: #FF5722       (異常)
├── normal:   #4CAF50       (正常)
├── pending:  #9E9E9E       (待處理)

Neutral Colors (中性色)
├── gray-50:  #FAFAFA
├── gray-100: #F5F5F5
├── gray-200: #EEEEEE
├── gray-300: #E0E0E0
├── gray-400: #BDBDBD
├── gray-500: #9E9E9E
├── gray-600: #757575
├── gray-700: #616161
├── gray-800: #424242
└── gray-900: #212121
```

### 字型系統 (Typography)

#### 建議字型

```
iOS:      SF Pro Text / SF Pro Display
Android:  Roboto
Web:      Inter / Noto Sans TC

中文備用:  Noto Sans TC / PingFang TC
```

#### 字型級距

```
Display Large:   57px / 64px line-height
Display Medium:  45px / 52px
Display Small:   36px / 44px

Headline Large:  32px / 40px
Headline Medium: 28px / 36px
Headline Small:  24px / 32px

Title Large:     22px / 28px
Title Medium:    16px / 24px (Medium weight)
Title Small:     14px / 20px (Medium weight)

Body Large:      16px / 24px
Body Medium:     14px / 20px
Body Small:      12px / 16px

Label Large:     14px / 20px (Medium weight)
Label Medium:    12px / 16px (Medium weight)
Label Small:     11px / 16px (Medium weight)
```

### 間距系統 (Spacing)

```
4px  基礎單位 (xs)
8px  (sm)
12px
16px (md) - 常用
20px
24px (lg)
32px (xl)
40px
48px (2xl)
64px (3xl)
```

### 圓角 (Border Radius)

```
none:   0px
sm:     4px
md:     8px    (常用)
lg:     12px
xl:     16px
full:   9999px (圓形)
```

## Figma 與需求追溯

### Frame 命名規範

每個畫面 Frame 必須包含需求追溯資訊：

```
Frame 名稱: SCR-{編號} - {畫面名稱}
描述 (Description) 包含:
- 對應需求: SRS-XXX, SRS-YYY
- 設計版本: v1.0
- 最後更新: 2024-01-15
- 設計師: @designer_name
```

### Component 命名規範

```
{類別}/{名稱}/{狀態}

範例:
Button/Primary/Default
Button/Primary/Pressed
Button/Primary/Disabled
Input/Text/Default
Input/Text/Focused
Input/Text/Error
Card/Patient/Default
Alert/Critical/Default
```

### 設計註解 (Annotations)

在 Figma 中為重要元素加入註解：

```
📌 需求關聯
SRS-001: 此按鈕觸發登入驗證流程

⚠️ 臨床安全
此警示必須在 200ms 內顯示

♿ 無障礙
對比度符合 WCAG AA (4.5:1)

📐 規格
- 寬度: 100% - 32px padding
- 高度: 48px
- 圓角: 8px
```

## 資產匯出設定

### Icons 匯出

```
Figma Export Settings:

SVG (設計用/Web):
- Format: SVG
- 勾選 "Include 'id' attribute"

Android Vector Drawable:
- 使用 Figma 插件: "Android Resources Export"
- 或匯出 SVG 後用 Android Studio 轉換

iOS PDF/PNG:
- Format: PDF (向量) 或 PNG @1x, @2x, @3x
- iOS 建議使用 PDF 格式
```

### App Icon 匯出

```
Android (mipmap):
- mdpi:    48 × 48
- hdpi:    72 × 72
- xhdpi:   96 × 96
- xxhdpi:  144 × 144
- xxxhdpi: 192 × 192
- Play Store: 512 × 512

iOS (AppIcon.appiconset):
- iPhone Notification: 20pt @2x, @3x
- iPhone Settings:     29pt @2x, @3x
- iPhone Spotlight:    40pt @2x, @3x
- iPhone App:          60pt @2x, @3x
- App Store:           1024 × 1024 (無透明)
```

### 圖片匯出

```
Android (drawable):
- mdpi:    1x (基準)
- hdpi:    1.5x
- xhdpi:   2x
- xxhdpi:  3x
- xxxhdpi: 4x

iOS (xcassets):
- @1x: 基準
- @2x: 2倍
- @3x: 3倍
```

## Figma 外掛推薦

### 資產匯出
- **Android Resources Export** - 直接匯出 Android 格式
- **iOS Export Settings** - 匯出 iOS xcassets
- **SVGO Compressor** - SVG 優化

### Design Token
- **Design Tokens** - 匯出 JSON 格式 Token
- **Token Studio** - 管理設計 Token

### 協作與文件
- **Figma to Markdown** - 匯出設計規格
- **Autoflow** - 自動產生流程箭頭
- **Contrast** - 檢查色彩對比度 (無障礙)

### 開發交接
- **Figma to Code** - 產生程式碼
- **Locofy** - 轉換為 React/Flutter 程式碼

## 與開發團隊協作

### Design Handoff 流程

```
1. 設計完成
   └── 設計師標記 "Ready for Dev"

2. 設計審查
   └── 確認需求追溯 (SRS-XXX)
   └── 確認無障礙規範
   └── 確認臨床安全規範

3. 資產匯出
   └── 匯出 Design Tokens (colors.json, typography.json)
   └── 匯出 Icons (SVG → Android/iOS)
   └── 匯出 Images (各解析度)

4. 開發對接
   └── 更新 03-assets/ 目錄
   └── 更新畫面與需求對應表
   └── 在 RTM 更新追溯關係

5. 實作驗證
   └── 截圖比對 Figma 設計
   └── 記錄差異與調整
```

### Figma 連結管理

在專案中維護 `figma-links.md`：

```markdown
# Figma 專案連結

## 主要檔案
- Design System: [連結](https://figma.com/...)
- App Screens: [連結](https://figma.com/...)
- Prototype: [連結](https://figma.com/...)

## 模組連結
| 模組 | Figma 頁面 | 狀態 |
|------|-----------|------|
| Authentication | [Auth](https://figma.com/...) | ✅ 完成 |
| Dashboard | [Home](https://figma.com/...) | 🔄 進行中 |
| Patient | [Patient](https://figma.com/...) | 📝 規劃中 |
```
