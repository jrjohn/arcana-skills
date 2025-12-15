# Android / iOS Asset size specifications

This document defines Android and iOS standard資產Sizeand directory structure。

## Directory structure overview

```
03-assets/
├── design-tokens/              # Design Token
│   ├── colors.json
│   ├── typography.json
│   └── spacing.json
│
├── icons/                      # Icon resources
│   ├── svg/                    # Original SVG (Design source)
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
│           │   ├── ic_home.pdf      # or @1x, @2x, @3x PNG
│           │   ├── ic_home@2x.png
│           │   └── ic_home@3x.png
│           └── ic_patient.imageset/
│
├── app-icons/                  # App icons
│   ├── source/
│   │   └── app-icon-1024.png   # Original 1024x1024
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
├── images/                     # Image resources
│   ├── source/                 # Original design files
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
└── splash/                     # Launch screen
    ├── source/
    ├── android/
    └── ios/
```

---

## App Icon Complete size specifications

### Android App Icon

| Density | Directory | Size | Description |
|------|------|------|------|
| mdpi | `mipmap-mdpi/` | 48 × 48 | baseaccurateDensity (1x) |
| hdpi | `mipmap-hdpi/` | 72 × 72 | 1.5x |
| xhdpi | `mipmap-xhdpi/` | 96 × 96 | 2x |
| xxhdpi | `mipmap-xxhdpi/` | 144 × 144 | 3x |
| xxxhdpi | `mipmap-xxxhdpi/` | 192 × 192 | 4x |
| Play Store | `playstore/` | 512 × 512 | Google Play store |

**Adaptive Icon (Android 8.0+)：**
```
mipmap-xxxhdpi/
├── ic_launcher.png              # Traditional icon (192x192)
├── ic_launcher_foreground.png   # Foreground layer (432x432，including safe area)
├── ic_launcher_background.png   # Background layer (432x432)
└── ic_launcher.xml              # Adaptive Icon definition
```

### iOS App Icon

| Purpose | Size pt | @2x | @3x | Filename |
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

**iOS Contents.json Example：**
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

## Icons (圖標) Size規格

### Android Icons

**Recommendeded：Use vector drawable (XML)**

Convert from SVG to vector drawable，No need for multiple resolutions：
```
icons/android/drawable/
├── ic_home.xml
├── ic_patient.xml
└── ic_alert.xml
```

**If using PNG：**

| Density | Directory | System icon | Toolbar 圖標 |
|------|------|----------|--------------|
| mdpi | `drawable-mdpi/` | 24 × 24 | 24 × 24 |
| hdpi | `drawable-hdpi/` | 36 × 36 | 36 × 36 |
| xhdpi | `drawable-xhdpi/` | 48 × 48 | 48 × 48 |
| xxhdpi | `drawable-xxhdpi/` | 72 × 72 | 72 × 72 |
| xxxhdpi | `drawable-xxxhdpi/` | 96 × 96 | 96 × 96 |

### iOS Icons

**Recommendeded：Use PDF or SVG (iOS 13+)**

Single PDF file，System auto-scales：
```
Icons.xcassets/
└── ic_home.imageset/
    ├── Contents.json
    └── ic_home.pdf
```

**If using PNG：**

| Scale | System icon | Tab Bar | Toolbar |
|-------|----------|---------|---------|
| @1x | 22 × 22 | 25 × 25 | 22 × 22 |
| @2x | 44 × 44 | 50 × 50 | 44 × 44 |
| @3x | 66 × 66 | 75 × 75 | 66 × 66 |

**iOS Icon Contents.json Example (PNG)：**
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

**iOS Icon Contents.json Example (PDF)：**
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

## Images (Image) Size規格

### Android Images

| Density | Directory | Ratio | DPI |
|------|------|------|-----|
| mdpi | `drawable-mdpi/` | 1x | 160 dpi |
| hdpi | `drawable-hdpi/` | 1.5x | 240 dpi |
| xhdpi | `drawable-xhdpi/` | 2x | 320 dpi |
| xxhdpi | `drawable-xxhdpi/` | 3x | 480 dpi |
| xxxhdpi | `drawable-xxxhdpi/` | 4x | 640 dpi |

**Calculation example：**
```
Baseline image (mdpi): 100 × 100 px

hdpi:    100 × 1.5 = 150 × 150 px
xhdpi:   100 × 2   = 200 × 200 px
xxhdpi:  100 × 3   = 300 × 300 px
xxxhdpi: 100 × 4   = 400 × 400 px
```

### iOS Images

| Scale | Purpose | Calculate |
|-------|------|------|
| @1x | Not Retina (已淘汰) | baseaccurateSize |
| @2x | Retina Standard | baseaccurate × 2 |
| @3x | Retina HD (Plus/Max) | baseaccurate × 3 |

**Calculation example：**
```
DesignSize (pt): 100 × 100 pt

@1x:  100 × 100 px (Can omit)
@2x:  200 × 200 px
@3x:  300 × 300 px
```

---

## Splash / Launch Screen

### Android Splash

**Recommendeded：Use Android 12+ splash screen API**

```
res/
├── values/
│   └── splash.xml              # Splash Settings
├── drawable/
│   └── splash_background.xml   # Background
└── mipmap-*/
    └── splash_icon.png         # Center icon (288dp Visible area)
```

**Traditional method (drawable)：**

| Density | SizeRecommended |
|------|----------|
| mdpi | 320 × 480 |
| hdpi | 480 × 800 |
| xhdpi | 720 × 1280 |
| xxhdpi | 1080 × 1920 |
| xxxhdpi | 1440 × 2560 |

### iOS Launch Screen

**Recommendeded：Use LaunchScreen.storyboard**

No need to provide static image，Through Storyboard Auto-adapts。

**If using static image：**

| Device | Size |
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

## Naming convention

### Naming rules

```
{Type}_{Name}_{Status}.{Format}

Type prefix:
- ic_     : icon
- img_    : image
- bg_     : background
- btn_    : button
- logo_   : logo
- splash_ : splash screen

Status suffix (Optional):
- _normal, _pressed, _disabled, _selected, _focused

Example:
- ic_home_normal.svg
- ic_home_selected.svg
- bg_login.png
- btn_submit_pressed.png
```

### Android Special rules

- All lowercase，Separated by underscores
- Cannot start with numbers
- Cannot use uppercase, hyphens, or spaces

```
Correct: ic_home.xml, bg_login_screen.png
Error: IC_Home.xml, bg-login.png, 1_icon.png
```

### iOS Special rules

- Can use any naming (Inside asset catalog)
- Recommendedand Android maintain consistencyfor easier management

---

## Figma Export settings

### Export App Icon

1. Select 1024×1024 original design
2. UseExportpluginor手moveOutputeachSize

**Recommendededplugin：**
- **App Icon Generator** - 一鍵OutputplaceHaveSize
- **Icon Organizer** - Manage icons

### Export Icons

**SVG (Design source)：**
- Export → SVG
- Check "Include id attribute"

**Android Vector Drawable：**
- Use **Android Resources Export** plugin
- or export SVG then convert using Android Studio

**iOS PDF：**
- Export → PDF

### Export Images

**Multi-resolution export：**
1. Select image layer
2. Right panel export
3. AddmanypieceExport settings：
   - 1x (Android mdpi / iOS @1x)
   - 2x (Android xhdpi / iOS @2x)
   - 3x (Android xxhdpi / iOS @3x)
   - 4x (Android xxxhdpi)

---

## Quick checklist

### App Icon Checklist

- [ ] 1024×1024 Original image prepared
- [ ] Android eachDensity (mdpi ~ xxxhdpi) Exported
- [ ] Android Play Store 512×512 Exported
- [ ] iOS eachSize (@2x, @3x) Exported
- [ ] iOS App Store 1024×1024 Exported (No transparency、No rounded corners)
- [ ] Contents.json Created

### Icons Checklist

- [ ] SVG Original file saved
- [ ] Android Vector Drawable Converted
- [ ] iOS PDF or @2x/@3x PNG Exported
- [ ] Naming follows specification (ic_ prefix)

### Images Checklist

- [ ] Original design files已Save
- [ ] Android eachDensityExported
- [ ] iOS @2x, @3x Exported
- [ ] Naming follows specification
