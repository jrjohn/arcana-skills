# 醫療軟體專案目錄結構

此結構確保需求文件 (SRS) 與設計資產 (UI/UX) 和開發資產 (Android/iOS) 能完整串連追溯。

## 完整目錄結構

```
{project-name}/
│
├── 01-requirements/                    # 需求文件 (第一階段產出)
│   ├── SRS/                           # 軟體需求規格書
│   │   ├── SRS-v1.0.md
│   │   └── attachments/               # SRS 附件 (流程圖、Wireframe)
│   ├── interviews/                    # 訪談紀錄
│   │   ├── 2024-01-15-stakeholder-A.md
│   │   └── 2024-01-16-clinical-team.md
│   └── analysis/                      # 分析文件
│       ├── stakeholder-analysis.md
│       ├── risk-analysis.md           # ISO 14971 風險分析
│       └── safety-classification.md   # IEC 62304 安全分類
│
├── 02-design/                         # 設計文件 (第二階段產出)
│   ├── SDD/                           # 軟體設計規格書
│   │   └── SDD-v1.0.md
│   ├── SWD/                           # 軟體詳細設計書
│   │   └── SWD-v1.0.md
│   ├── architecture/                  # 架構設計
│   │   ├── system-architecture.md
│   │   ├── data-model.md
│   │   └── api-design.md
│   └── ui-ux/                         # UI/UX 設計
│       ├── design-system.md           # 設計系統說明
│       ├── figma-links.md             # Figma 連結清單
│       └── screen-mapping.md          # 畫面與需求對應表
│
├── 03-assets/                         # 設計資產 (與 Figma 同步)
│   │
│   ├── design-tokens/                 # 設計 Token (從 Figma 匯出)
│   │   ├── colors.json                # 色彩定義
│   │   ├── typography.json            # 字型定義
│   │   ├── spacing.json               # 間距定義
│   │   └── shadows.json               # 陰影定義
│   │
│   ├── icons/                         # 圖標資源
│   │   ├── svg/                       # 原始 SVG (設計用)
│   │   │   ├── ic_home.svg
│   │   │   ├── ic_patient.svg
│   │   │   └── ic_alert.svg
│   │   ├── android/                   # Android 格式
│   │   │   └── drawable/
│   │   │       ├── ic_home.xml        # Vector Drawable
│   │   │       └── ic_patient.xml
│   │   └── ios/                       # iOS 格式
│   │       └── Icons.xcassets/
│   │           ├── ic_home.imageset/
│   │           └── ic_patient.imageset/
│   │
│   ├── app-icons/                     # App 圖標
│   │   ├── source/                    # 原始設計檔
│   │   │   └── app-icon-1024.png      # 1024x1024 原圖
│   │   ├── android/                   # Android 各尺寸
│   │   │   ├── mipmap-mdpi/           # 48x48
│   │   │   ├── mipmap-hdpi/           # 72x72
│   │   │   ├── mipmap-xhdpi/          # 96x96
│   │   │   ├── mipmap-xxhdpi/         # 144x144
│   │   │   ├── mipmap-xxxhdpi/        # 192x192
│   │   │   └── playstore-icon.png     # 512x512 (Play Store)
│   │   └── ios/                       # iOS 各尺寸
│   │       └── AppIcon.appiconset/
│   │           ├── Contents.json
│   │           ├── Icon-20@2x.png     # 40x40
│   │           ├── Icon-20@3x.png     # 60x60
│   │           ├── Icon-29@2x.png     # 58x58
│   │           ├── Icon-29@3x.png     # 87x87
│   │           ├── Icon-40@2x.png     # 80x80
│   │           ├── Icon-40@3x.png     # 120x120
│   │           ├── Icon-60@2x.png     # 120x120
│   │           ├── Icon-60@3x.png     # 180x180
│   │           └── Icon-1024.png      # 1024x1024 (App Store)
│   │
│   ├── images/                        # 圖片資源
│   │   ├── source/                    # 原始設計檔
│   │   ├── android/                   # Android 格式
│   │   │   ├── drawable-mdpi/
│   │   │   ├── drawable-hdpi/
│   │   │   ├── drawable-xhdpi/
│   │   │   ├── drawable-xxhdpi/
│   │   │   └── drawable-xxxhdpi/
│   │   └── ios/                       # iOS 格式
│   │       └── Images.xcassets/
│   │
│   ├── splash/                        # 啟動畫面
│   │   ├── source/
│   │   ├── android/
│   │   └── ios/
│   │
│   └── screenshots/                   # 螢幕截圖 (用於文件/商店)
│       ├── android/
│       └── ios/
│
├── 04-testing/                        # 測試文件
│   ├── STP/                           # 軟體測試計畫
│   │   └── STP-v1.0.md
│   ├── STC/                           # 軟體測試案例
│   │   └── STC-v1.0.md
│   └── test-reports/                  # 測試報告
│
├── 05-validation/                     # 驗證文件
│   ├── SVV/                           # 軟體驗證與確認
│   │   └── SVV-v1.0.md
│   └── RTM/                           # 需求追溯矩陣
│       └── RTM-v1.0.md
│
├── 06-regulatory/                     # 法規文件
│   ├── risk-management/               # ISO 14971 風險管理
│   ├── cybersecurity/                 # 網路安全文件
│   └── submissions/                   # 送審文件
│
└── _config/                           # 專案設定
    ├── figma-config.md                # Figma 專案設定
    ├── asset-export-guide.md          # 資產匯出指南
    └── naming-conventions.md          # 命名規範
```

## 需求與資產追溯對應

### 追溯關係圖

```
SRS-001 (需求)
    │
    ├──→ SDD-001 (設計)
    │        │
    │        └──→ UI Screen: SCR-001 (畫面)
    │                  │
    │                  ├──→ Figma Frame: "Login Screen"
    │                  │
    │                  └──→ Assets:
    │                        ├── icons/ic_login.svg
    │                        ├── images/bg_login.png
    │                        └── design-tokens/colors.json
    │
    └──→ STC-001 (測試)
             │
             └──→ Screenshots: login_success.png
```

### 畫面與需求對應表範例

| 畫面 ID | 畫面名稱 | 對應需求 | Figma Frame | 相關資產 |
|---------|----------|----------|-------------|----------|
| SCR-001 | 登入畫面 | SRS-001, SRS-002 | [Login Screen](figma-link) | ic_login, bg_login |
| SCR-002 | 首頁 | SRS-010~015 | [Home Dashboard](figma-link) | ic_home, ic_patient |
| SCR-003 | 病患資料 | SRS-020~025 | [Patient Detail](figma-link) | ic_patient, ic_alert |

## 命名規範

### 文件命名

```
{文件類型}-v{版本號}.md

範例:
- SRS-v1.0.md
- SRS-v1.1.md (小改版)
- SRS-v2.0.md (大改版)
```

### 資產命名

```
{類型}_{描述}_{狀態}.{格式}

類型:
- ic_ : 圖標 (icon)
- bg_ : 背景 (background)
- img_: 圖片 (image)
- btn_: 按鈕 (button)
- logo_: 標誌

狀態 (可選):
- _normal
- _pressed
- _disabled
- _selected

範例:
- ic_home_normal.svg
- btn_submit_pressed.png
- bg_login.png
```

### Figma 命名

```
頁面: {模組名稱}
Frame: {畫面ID} - {畫面名稱}
Component: {類型}/{名稱}/{狀態}

範例:
頁面: Authentication
Frame: SCR-001 - Login Screen
Component: Button/Primary/Normal
```

---

## Android / iOS 資產尺寸規格

詳細尺寸規格請參考 [references/asset-specifications.md](../../references/asset-specifications.md)

### 快速參考

#### App Icon 尺寸

**Android (mipmap):**
| 密度 | 目錄 | 尺寸 |
|------|------|------|
| mdpi | `mipmap-mdpi/` | 48 × 48 |
| hdpi | `mipmap-hdpi/` | 72 × 72 |
| xhdpi | `mipmap-xhdpi/` | 96 × 96 |
| xxhdpi | `mipmap-xxhdpi/` | 144 × 144 |
| xxxhdpi | `mipmap-xxxhdpi/` | 192 × 192 |
| Play Store | - | 512 × 512 |

**iOS (AppIcon.appiconset):**
| 用途 | @2x | @3x |
|------|-----|-----|
| Notification (20pt) | 40×40 | 60×60 |
| Settings (29pt) | 58×58 | 87×87 |
| Spotlight (40pt) | 80×80 | 120×120 |
| App (60pt) | 120×120 | 180×180 |
| App Store | 1024×1024 | - |

#### Icons 尺寸

**Android：推薦使用 Vector Drawable (.xml)**
- 從 SVG 轉換，無需多解析度

**iOS：推薦使用 PDF**
- 單一 PDF，系統自動縮放

若使用 PNG：
| 密度/Scale | Android | iOS |
|------------|---------|-----|
| 1x / mdpi | 24×24 | 22×22 |
| 2x / xhdpi / @2x | 48×48 | 44×44 |
| 3x / xxhdpi / @3x | 72×72 | 66×66 |
| 4x / xxxhdpi | 96×96 | - |

#### Images 尺寸

**Android (drawable):**
| 密度 | 比例 | 範例 (100pt 設計) |
|------|------|-------------------|
| mdpi | 1x | 100×100 px |
| hdpi | 1.5x | 150×150 px |
| xhdpi | 2x | 200×200 px |
| xxhdpi | 3x | 300×300 px |
| xxxhdpi | 4x | 400×400 px |

**iOS (xcassets):**
| Scale | 範例 (100pt 設計) |
|-------|-------------------|
| @1x | 100×100 px (可省略) |
| @2x | 200×200 px |
| @3x | 300×300 px |

---

## 資產目錄詳細結構

```
03-assets/
│
├── design-tokens/                      # 設計 Token
│   ├── colors.json
│   ├── typography.json
│   └── spacing.json
│
├── icons/                              # 圖標
│   ├── svg/                            # 原始 SVG
│   │   ├── ic_home.svg
│   │   └── ic_patient.svg
│   │
│   ├── android/
│   │   └── drawable/                   # Vector Drawable
│   │       ├── ic_home.xml
│   │       └── ic_patient.xml
│   │
│   └── ios/
│       └── Icons.xcassets/
│           ├── ic_home.imageset/
│           │   ├── Contents.json
│           │   └── ic_home.pdf         # 或 PNG @1x/@2x/@3x
│           └── ic_patient.imageset/
│
├── app-icons/                          # App 圖標
│   ├── source/
│   │   └── app-icon-1024.png
│   │
│   ├── android/
│   │   ├── mipmap-mdpi/
│   │   │   └── ic_launcher.png         # 48×48
│   │   ├── mipmap-hdpi/
│   │   │   └── ic_launcher.png         # 72×72
│   │   ├── mipmap-xhdpi/
│   │   │   └── ic_launcher.png         # 96×96
│   │   ├── mipmap-xxhdpi/
│   │   │   └── ic_launcher.png         # 144×144
│   │   ├── mipmap-xxxhdpi/
│   │   │   └── ic_launcher.png         # 192×192
│   │   └── playstore/
│   │       └── ic_launcher-512.png     # 512×512
│   │
│   └── ios/
│       └── AppIcon.appiconset/
│           ├── Contents.json
│           ├── Icon-20@2x.png          # 40×40
│           ├── Icon-20@3x.png          # 60×60
│           ├── Icon-29@2x.png          # 58×58
│           ├── Icon-29@3x.png          # 87×87
│           ├── Icon-40@2x.png          # 80×80
│           ├── Icon-40@3x.png          # 120×120
│           ├── Icon-60@2x.png          # 120×120
│           ├── Icon-60@3x.png          # 180×180
│           └── Icon-1024.png           # 1024×1024
│
├── images/                             # 圖片
│   ├── source/
│   │   └── bg_login.png
│   │
│   ├── android/
│   │   ├── drawable-mdpi/              # 1x
│   │   │   └── bg_login.png
│   │   ├── drawable-hdpi/              # 1.5x
│   │   │   └── bg_login.png
│   │   ├── drawable-xhdpi/             # 2x
│   │   │   └── bg_login.png
│   │   ├── drawable-xxhdpi/            # 3x
│   │   │   └── bg_login.png
│   │   └── drawable-xxxhdpi/           # 4x
│   │       └── bg_login.png
│   │
│   └── ios/
│       └── Images.xcassets/
│           └── bg_login.imageset/
│               ├── Contents.json
│               ├── bg_login.png        # @1x (可省略)
│               ├── bg_login@2x.png     # @2x
│               └── bg_login@3x.png     # @3x
│
└── splash/                             # 啟動畫面
    ├── source/
    ├── android/                        # 建議用 Splash Screen API
    └── ios/                            # 建議用 LaunchScreen.storyboard
```
