# Android / iOS 資產尺寸規格

本文件定義 Android 與 iOS 的標準資產尺寸與目錄結構。

## 目錄結構總覽

```
03-assets/
├── design-tokens/              # 設計 Token
│   ├── colors.json
│   ├── typography.json
│   └── spacing.json
│
├── icons/                      # 圖標資源
│   ├── svg/                    # 原始 SVG (設計來源)
│   │   ├── ic_home.svg
│   │   └── ic_patient.svg
│   │
│   ├── android/                # Android Vector Drawable
│   │   └── drawable/
│   │       ├── ic_home.xml
│   │       └── ic_patient.xml
│   │
│   └── ios/                    # iOS Asset Catalog
│       └── Icons.xcassets/
│           ├── ic_home.imageset/
│           │   ├── Contents.json
│           │   ├── ic_home.pdf      # 或 @1x, @2x, @3x PNG
│           │   ├── ic_home@2x.png
│           │   └── ic_home@3x.png
│           └── ic_patient.imageset/
│
├── app-icons/                  # App 圖標
│   ├── source/
│   │   └── app-icon-1024.png   # 原始 1024x1024
│   │
│   ├── android/
│   │   ├── mipmap-mdpi/        # 48x48
│   │   │   └── ic_launcher.png
│   │   ├── mipmap-hdpi/        # 72x72
│   │   │   └── ic_launcher.png
│   │   ├── mipmap-xhdpi/       # 96x96
│   │   │   └── ic_launcher.png
│   │   ├── mipmap-xxhdpi/      # 144x144
│   │   │   └── ic_launcher.png
│   │   ├── mipmap-xxxhdpi/     # 192x192
│   │   │   └── ic_launcher.png
│   │   └── playstore/          # Play Store
│   │       └── ic_launcher-512.png
│   │
│   └── ios/
│       └── AppIcon.appiconset/
│           ├── Contents.json
│           ├── Icon-20@2x.png      # 40x40
│           ├── Icon-20@3x.png      # 60x60
│           ├── Icon-29@2x.png      # 58x58
│           ├── Icon-29@3x.png      # 87x87
│           ├── Icon-40@2x.png      # 80x80
│           ├── Icon-40@3x.png      # 120x120
│           ├── Icon-60@2x.png      # 120x120
│           ├── Icon-60@3x.png      # 180x180
│           └── Icon-1024.png       # 1024x1024 (App Store)
│
├── images/                     # 圖片資源
│   ├── source/                 # 原始設計檔
│   │   ├── bg_login.png
│   │   └── img_onboarding_1.png
│   │
│   ├── android/
│   │   ├── drawable-mdpi/      # 1x
│   │   ├── drawable-hdpi/      # 1.5x
│   │   ├── drawable-xhdpi/     # 2x
│   │   ├── drawable-xxhdpi/    # 3x
│   │   └── drawable-xxxhdpi/   # 4x
│   │
│   └── ios/
│       └── Images.xcassets/
│           └── bg_login.imageset/
│               ├── Contents.json
│               ├── bg_login.png        # @1x
│               ├── bg_login@2x.png     # @2x
│               └── bg_login@3x.png     # @3x
│
└── splash/                     # 啟動畫面
    ├── source/
    ├── android/
    └── ios/
```

---

## App Icon 完整尺寸規格

### Android App Icon

| 密度 | 目錄 | 尺寸 | 說明 |
|------|------|------|------|
| mdpi | `mipmap-mdpi/` | 48 × 48 | 基準密度 (1x) |
| hdpi | `mipmap-hdpi/` | 72 × 72 | 1.5x |
| xhdpi | `mipmap-xhdpi/` | 96 × 96 | 2x |
| xxhdpi | `mipmap-xxhdpi/` | 144 × 144 | 3x |
| xxxhdpi | `mipmap-xxxhdpi/` | 192 × 192 | 4x |
| Play Store | `playstore/` | 512 × 512 | Google Play 商店 |

**Adaptive Icon (Android 8.0+)：**
```
mipmap-xxxhdpi/
├── ic_launcher.png              # 傳統圖標 (192x192)
├── ic_launcher_foreground.png   # 前景層 (432x432，含安全區)
├── ic_launcher_background.png   # 背景層 (432x432)
└── ic_launcher.xml              # Adaptive Icon 定義
```

### iOS App Icon

| 用途 | 尺寸 pt | @2x | @3x | 檔名 |
|------|---------|-----|-----|------|
| iPhone Notification | 20pt | 40×40 | 60×60 | Icon-20@2x/3x.png |
| iPhone Settings | 29pt | 58×58 | 87×87 | Icon-29@2x/3x.png |
| iPhone Spotlight | 40pt | 80×80 | 120×120 | Icon-40@2x/3x.png |
| iPhone App | 60pt | 120×120 | 180×180 | Icon-60@2x/3x.png |
| iPad Notification | 20pt | 20×20 | 40×40 | Icon-20.png, Icon-20@2x.png |
| iPad Settings | 29pt | 29×29 | 58×58 | Icon-29.png, Icon-29@2x.png |
| iPad Spotlight | 40pt | 40×40 | 80×80 | Icon-40.png, Icon-40@2x.png |
| iPad Pro App | 83.5pt | - | 167×167 | Icon-83.5@2x.png |
| iPad App | 76pt | 76×76 | 152×152 | Icon-76.png, Icon-76@2x.png |
| App Store | 1024pt | - | - | Icon-1024.png |

**iOS Contents.json 範例：**
```json
{
  "images": [
    { "size": "20x20", "idiom": "iphone", "scale": "2x", "filename": "Icon-20@2x.png" },
    { "size": "20x20", "idiom": "iphone", "scale": "3x", "filename": "Icon-20@3x.png" },
    { "size": "29x29", "idiom": "iphone", "scale": "2x", "filename": "Icon-29@2x.png" },
    { "size": "29x29", "idiom": "iphone", "scale": "3x", "filename": "Icon-29@3x.png" },
    { "size": "40x40", "idiom": "iphone", "scale": "2x", "filename": "Icon-40@2x.png" },
    { "size": "40x40", "idiom": "iphone", "scale": "3x", "filename": "Icon-40@3x.png" },
    { "size": "60x60", "idiom": "iphone", "scale": "2x", "filename": "Icon-60@2x.png" },
    { "size": "60x60", "idiom": "iphone", "scale": "3x", "filename": "Icon-60@3x.png" },
    { "size": "1024x1024", "idiom": "ios-marketing", "scale": "1x", "filename": "Icon-1024.png" }
  ],
  "info": { "version": 1, "author": "xcode" }
}
```

---

## Icons (圖標) 尺寸規格

### Android Icons

**推薦：使用 Vector Drawable (XML)**

從 SVG 轉換為 Vector Drawable，不需要多解析度：
```
icons/android/drawable/
├── ic_home.xml
├── ic_patient.xml
└── ic_alert.xml
```

**若使用 PNG：**

| 密度 | 目錄 | 系統圖標 | Toolbar 圖標 |
|------|------|----------|--------------|
| mdpi | `drawable-mdpi/` | 24 × 24 | 24 × 24 |
| hdpi | `drawable-hdpi/` | 36 × 36 | 36 × 36 |
| xhdpi | `drawable-xhdpi/` | 48 × 48 | 48 × 48 |
| xxhdpi | `drawable-xxhdpi/` | 72 × 72 | 72 × 72 |
| xxxhdpi | `drawable-xxxhdpi/` | 96 × 96 | 96 × 96 |

### iOS Icons

**推薦：使用 PDF 或 SVG (iOS 13+)**

單一 PDF 檔案，系統自動縮放：
```
Icons.xcassets/
└── ic_home.imageset/
    ├── Contents.json
    └── ic_home.pdf
```

**若使用 PNG：**

| Scale | 系統圖標 | Tab Bar | Toolbar |
|-------|----------|---------|---------|
| @1x | 22 × 22 | 25 × 25 | 22 × 22 |
| @2x | 44 × 44 | 50 × 50 | 44 × 44 |
| @3x | 66 × 66 | 75 × 75 | 66 × 66 |

**iOS Icon Contents.json 範例 (PNG)：**
```json
{
  "images": [
    { "idiom": "universal", "scale": "1x", "filename": "ic_home.png" },
    { "idiom": "universal", "scale": "2x", "filename": "ic_home@2x.png" },
    { "idiom": "universal", "scale": "3x", "filename": "ic_home@3x.png" }
  ],
  "info": { "version": 1, "author": "xcode" }
}
```

**iOS Icon Contents.json 範例 (PDF)：**
```json
{
  "images": [
    { "idiom": "universal", "filename": "ic_home.pdf" }
  ],
  "info": { "version": 1, "author": "xcode" },
  "properties": { "preserves-vector-representation": true }
}
```

---

## Images (圖片) 尺寸規格

### Android Images

| 密度 | 目錄 | 比例 | DPI |
|------|------|------|-----|
| mdpi | `drawable-mdpi/` | 1x | 160 dpi |
| hdpi | `drawable-hdpi/` | 1.5x | 240 dpi |
| xhdpi | `drawable-xhdpi/` | 2x | 320 dpi |
| xxhdpi | `drawable-xxhdpi/` | 3x | 480 dpi |
| xxxhdpi | `drawable-xxxhdpi/` | 4x | 640 dpi |

**計算範例：**
```
基準圖片 (mdpi): 100 × 100 px

hdpi:    100 × 1.5 = 150 × 150 px
xhdpi:   100 × 2   = 200 × 200 px
xxhdpi:  100 × 3   = 300 × 300 px
xxxhdpi: 100 × 4   = 400 × 400 px
```

### iOS Images

| Scale | 用途 | 計算 |
|-------|------|------|
| @1x | 非 Retina (已淘汰) | 基準尺寸 |
| @2x | Retina 標準 | 基準 × 2 |
| @3x | Retina HD (Plus/Max) | 基準 × 3 |

**計算範例：**
```
設計尺寸 (pt): 100 × 100 pt

@1x:  100 × 100 px (可省略)
@2x:  200 × 200 px
@3x:  300 × 300 px
```

---

## Splash / Launch Screen

### Android Splash

**推薦：使用 Android 12+ Splash Screen API**

```
res/
├── values/
│   └── splash.xml              # Splash 設定
├── drawable/
│   └── splash_background.xml   # 背景
└── mipmap-*/
    └── splash_icon.png         # 中央圖標 (288dp 可見區域)
```

**傳統方式 (drawable)：**

| 密度 | 尺寸建議 |
|------|----------|
| mdpi | 320 × 480 |
| hdpi | 480 × 800 |
| xhdpi | 720 × 1280 |
| xxhdpi | 1080 × 1920 |
| xxxhdpi | 1440 × 2560 |

### iOS Launch Screen

**推薦：使用 LaunchScreen.storyboard**

不需要提供靜態圖片，透過 Storyboard 自動適配。

**若使用靜態圖片：**

| 裝置 | 尺寸 |
|------|------|
| iPhone SE | 640 × 1136 |
| iPhone 8 | 750 × 1334 |
| iPhone 8 Plus | 1242 × 2208 |
| iPhone 11 Pro | 1125 × 2436 |
| iPhone 11 Pro Max | 1242 × 2688 |
| iPhone 12/13/14 | 1170 × 2532 |
| iPhone 12/13/14 Pro Max | 1284 × 2778 |
| iPhone 14 Pro | 1179 × 2556 |
| iPhone 14 Pro Max | 1290 × 2796 |
| iPhone 15/16 Pro Max | 1320 × 2868 |

---

## 命名規範

### 通用規則

```
{類型}_{名稱}_{狀態}.{格式}

類型前綴:
- ic_     : icon (圖標)
- img_    : image (圖片)
- bg_     : background (背景)
- btn_    : button (按鈕)
- logo_   : logo (標誌)
- splash_ : splash screen

狀態後綴 (可選):
- _normal, _pressed, _disabled, _selected, _focused

範例:
- ic_home_normal.svg
- ic_home_selected.svg
- bg_login.png
- btn_submit_pressed.png
```

### Android 特定

- 全小寫，底線分隔
- 不可使用數字開頭
- 不可使用大寫、連字號、空格

```
正確: ic_home.xml, bg_login_screen.png
錯誤: IC_Home.xml, bg-login.png, 1_icon.png
```

### iOS 特定

- 可使用任何命名 (Asset Catalog 內部)
- 建議與 Android 保持一致以便管理

---

## Figma 匯出設定

### 匯出 App Icon

1. 選擇 1024×1024 原始設計
2. 使用匯出外掛或手動產出各尺寸

**推薦外掛：**
- **App Icon Generator** - 一鍵產出所有尺寸
- **Icon Organizer** - 管理圖標

### 匯出 Icons

**SVG (設計來源)：**
- Export → SVG
- 勾選 "Include id attribute"

**Android Vector Drawable：**
- 使用 **Android Resources Export** 外掛
- 或匯出 SVG 後用 Android Studio 轉換

**iOS PDF：**
- Export → PDF

### 匯出 Images

**多解析度匯出：**
1. 選擇圖層
2. 右側 Export 面板
3. 新增多個匯出設定：
   - 1x (Android mdpi / iOS @1x)
   - 2x (Android xhdpi / iOS @2x)
   - 3x (Android xxhdpi / iOS @3x)
   - 4x (Android xxxhdpi)

---

## 快速檢核表

### App Icon 檢核

- [ ] 1024×1024 原始圖準備完成
- [ ] Android 各密度 (mdpi ~ xxxhdpi) 已匯出
- [ ] Android Play Store 512×512 已匯出
- [ ] iOS 各尺寸 (@2x, @3x) 已匯出
- [ ] iOS App Store 1024×1024 已匯出 (無透明、無圓角)
- [ ] Contents.json 已建立

### Icons 檢核

- [ ] SVG 原始檔已儲存
- [ ] Android Vector Drawable 已轉換
- [ ] iOS PDF 或 @2x/@3x PNG 已匯出
- [ ] 命名符合規範 (ic_ 前綴)

### Images 檢核

- [ ] 原始設計檔已儲存
- [ ] Android 各密度已匯出
- [ ] iOS @2x, @3x 已匯出
- [ ] 命名符合規範
