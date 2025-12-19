# Visual Asset Extraction and Export Guide

This guide provides methods for identifying and extracting special objects, icons, illustrations, and other visual elements from reference images, then exporting them as usable design assets.

## Table of Contents
1. [Asset Extraction Workflow](#asset-extraction-workflow)
2. [Icon Identification and Analysis](#icon-identification-and-analysis)
3. [Illustration Element Extraction](#illustration-element-extraction)
4. [UI Component Extraction](#ui-component-extraction)
5. [Asset Classification and Naming](#asset-classification-and-naming)
6. [Export Format Specifications](#export-format-specifications)
7. [Figma Asset Library Creation](#figma-asset-library-creation)
8. [Icon Library Generation](#icon-library-generation)

---

## Asset Extraction Workflow

### Overall Workflow

```
Input Reference Image
     |
+---------------------------------------------+
|          Visual Element Identification       |
+-------------+-------------+-----------------+
|   Icons     | Illustrations|  UI Components |
+-------------+-------------+-----------------+
|   Graphics  | Decorations  | Photo Elements |
+-------------+-------------+-----------------+
     |
Element Analysis and Description
     |
Style Characteristics Recording
     |
Asset Specification Export
     |
Figma/Code Asset Generation
```

### Extractable Asset Types

```
Asset Type Overview

+-- Icons
|   +-- System Icons (Navigation, Action)
|   +-- Feature Icons
|   +-- Social Icons
|   +-- Brand Icons
|
+-- Illustrations
|   +-- Character Illustrations
|   +-- Scene Illustrations
|   +-- Object Illustrations
|   +-- Abstract Graphics
|
+-- Graphic Elements
|   +-- Shapes
|   +-- Decorative Lines
|   +-- Background Textures
|   +-- Gradient Effects
|
+-- UI Components
|   +-- Button Styles
|   +-- Card Styles
|   +-- Input Field Styles
|   +-- Navigation Elements
|
+-- Photo Elements
    +-- Character Silhouettes
    +-- Product Images
    +-- Background Images
```

---

## Icon Identification and Analysis

### Icon Style Classification

```
+-----------------------------------------------------------+
|                    Icon Style Types                        |
+-----------------------------------------------------------+
|                                                           |
|  Outlined                      Filled                     |
|  +-------------+              +-------------+             |
|  |   [___]     |              |   ########  |             |
|  |   |   |     |              |   ########  |             |
|  |   [___]     |              |   ########  |             |
|  +-------------+              +-------------+             |
|  Features: Lines, transparent  Features: Solid, no stroke |
|                                                           |
|  Two-tone                      Duotone                    |
|  +-------------+              +-------------+             |
|  |   #######   |              |   ..####..  |             |
|  |   ##...##   |              |   ..####..  |             |
|  |   #######   |              |   ..####..  |             |
|  +-------------+              +-------------+             |
|  Features: Primary + secondary Features: Light/dark tones |
|                                                           |
|  3D / Isometric                Gradient                   |
|  +-------------+              +-------------+             |
|  |    /--\     |              |   ..##@@   |             |
|  |   /    \    |              |   ..##@@   |             |
|  |  /------\   |              |   ..##@@   |             |
|  +-------------+              +-------------+             |
|  Features: 3D, perspective    Features: Color transitions |
|                                                           |
+-----------------------------------------------------------+
```

### Icon Feature Analysis

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

### Icon Extraction Output

```markdown
## Icon Extraction Report

### Identified Icons (12 total)

| # | Name | Type | Size | Style |
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

### Icon Style Specifications

```
Style: Outlined
Stroke Width: 1.5px
Corners: Rounded (2px)
Grid: 24x24px
Safe Area: 2px padding
Stroke Cap: Round cap
Stroke Join: Round join
```

### Recommended Icon Libraries

Based on extracted style, recommended:
- Heroicons (https://heroicons.com) - Closest match
- Feather Icons - Alternative
- Phosphor Icons - Alternative
```

---

## Illustration Element Extraction

### Illustration Style Classification

```
Illustration Style Types:

+---------------------------------------------+
| Flat Illustration                           |
+---------------------------------------------+
| - No shadows or minimal shadows             |
| - Composed of solid color blocks            |
| - Simplified shapes                         |
| - Strong geometric feel                     |
+---------------------------------------------+

+---------------------------------------------+
| Isometric Illustration                      |
+---------------------------------------------+
| - 30-degree angles                          |
| - 3D dimensional feel                       |
| - Unified perspective                       |
| - Common for tech/products                  |
+---------------------------------------------+

+---------------------------------------------+
| Hand-drawn Style                            |
+---------------------------------------------+
| - Irregular lines                           |
| - Textured quality                          |
| - Organic shapes                            |
| - Warm and friendly                         |
+---------------------------------------------+

+---------------------------------------------+
| Gradient / 3D                               |
+---------------------------------------------+
| - Rich color transitions                    |
| - Light and shadow effects                  |
| - Modern tech aesthetic                     |
| - Strong visual impact                      |
+---------------------------------------------+

+---------------------------------------------+
| Line Art                                    |
+---------------------------------------------+
| - Pure line composition                     |
| - Simple and elegant                        |
| - Single or multi-color                     |
| - Suitable for small sizes                  |
+---------------------------------------------+
```

### Illustration Element Analysis

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
        "description": "Person sitting using laptop",
        "colors": ["#6366F1", "#F8FAFC", "#1F2937"],
        "position": "center"
      },
      {
        "type": "object",
        "description": "Plant decoration",
        "colors": ["#10B981", "#065F46"],
        "position": "background"
      },
      {
        "type": "shape",
        "description": "Abstract geometric background",
        "colors": ["#EEF2FF", "#C7D2FE"],
        "position": "background"
      }
    ],
    "mood": "professional, friendly, modern",
    "usage": "hero section, empty state, onboarding"
  }
}
```

### Illustration Extraction Output

```markdown
## Illustration Element Extraction Report

### Identified Illustration Elements (5 total)

| # | Type | Description | Style | Suggested Use |
|---|------|-------------|-------|---------------|
| 1 | Character | Person using laptop | Flat | Hero/Empty State |
| 2 | Scene | Office desk scene | Flat | Onboarding |
| 3 | Object | Plant decoration | Flat | Decorative element |
| 4 | Shape | Circular blob | Gradient | Background decoration |
| 5 | Shape | Abstract lines | Line | Separator decoration |

### Illustration Style Specifications

```
Style: Flat Illustration
Colors: 6-color limited palette
Shadows: None (solid color blocks)
Outlines: No strokes
Shapes: Geometric rounded
Characters: Simplified, no facial features
Proportions: Exaggerated, cute
```

### Illustration Resource Recommendations

Based on extracted style, recommended:
- unDraw (https://undraw.co) - Free for commercial use
- Blush (https://blush.design) - Customizable colors
- Humaaans - Character combinations
```

---

## UI Component Extraction

### Extractable UI Components

```
UI Component Types:

+---------------------------------------------+
| Buttons                                     |
+---------------------------------------------+
| +-------------+  +-------------+            |
| |   Primary   |  |  Secondary  |            |
| +-------------+  +-------------+            |
|                                             |
| Extract: Size, radius, colors, shadow, font |
+---------------------------------------------+

+---------------------------------------------+
| Cards                                       |
+---------------------------------------------+
| +-------------------------------------+     |
| |  +-----------------------------+    |     |
| |  |         Image               |    |     |
| |  +-----------------------------+    |     |
| |  |  Title                      |    |     |
| |  |  Description text here...   |    |     |
| |  |                     [Button]|    |     |
| |  +-----------------------------+    |     |
| +-------------------------------------+     |
|                                             |
| Extract: Structure, radius, shadow, spacing |
+---------------------------------------------+

+---------------------------------------------+
| Inputs                                      |
+---------------------------------------------+
| Label                                       |
| +-------------------------------------+     |
| | Placeholder text                    |     |
| +-------------------------------------+     |
| Helper text                                 |
|                                             |
| Extract: Height, radius, border, states     |
+---------------------------------------------+

+---------------------------------------------+
| Navigation                                  |
+---------------------------------------------+
| +-------------------------------------+     |
| | Logo    Nav1   Nav2   Nav3   [CTA]  |     |
| +-------------------------------------+     |
|                                             |
| Extract: Layout, spacing, height, bg        |
+---------------------------------------------+

+---------------------------------------------+
| Tags/Badges                                 |
+---------------------------------------------+
| +--------+ +--------+ +--------+            |
| |  Tag   | | Badge  | |  Chip  |            |
| +--------+ +--------+ +--------+            |
|                                             |
| Extract: Size, radius, colors, font         |
+---------------------------------------------+
```

### UI Component Extraction Output

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

## Asset Classification and Naming

### Naming Convention

```
Asset Naming Rules:

[type]-[name]-[variant]-[size].[format]

Examples:
+-- icon-home-outline-24.svg
+-- icon-home-filled-24.svg
+-- icon-search-outline-20.svg
+-- illust-hero-working-lg.svg
+-- illust-empty-nodata-md.svg
+-- shape-blob-gradient-01.svg
+-- avatar-placeholder-sm.png
+-- bg-pattern-grid-01.png
```

### Asset Directory Structure

```
assets/
+-- icons/
|   +-- navigation/
|   |   +-- home.svg
|   |   +-- search.svg
|   |   +-- menu.svg
|   +-- action/
|   |   +-- edit.svg
|   |   +-- delete.svg
|   |   +-- share.svg
|   +-- status/
|   |   +-- check.svg
|   |   +-- warning.svg
|   |   +-- error.svg
|   +-- social/
|       +-- facebook.svg
|       +-- twitter.svg
|       +-- instagram.svg
|
+-- illustrations/
|   +-- hero/
|   +-- empty-states/
|   +-- onboarding/
|   +-- error-pages/
|
+-- shapes/
|   +-- blobs/
|   +-- patterns/
|   +-- decorations/
|
+-- photos/
|   +-- avatars/
|   +-- backgrounds/
|   +-- products/
|
+-- components/
    +-- buttons.json
    +-- cards.json
    +-- inputs.json
```

### Asset List Output

```markdown
## Asset List

### Icons (24 total)
| Name | Category | Format | Size |
|------|----------|--------|------|
| home | navigation | SVG | 24x24 |
| search | action | SVG | 24x24 |
| user | navigation | SVG | 24x24 |
| ... | ... | ... | ... |

### Illustrations (6 total)
| Name | Category | Usage | Size |
|------|----------|-------|------|
| hero-working | hero | Homepage banner | 800x600 |
| empty-inbox | empty | Empty inbox | 400x300 |
| ... | ... | ... | ... |

### Shapes (8 total)
| Name | Type | Color | Format |
|------|------|-------|--------|
| blob-01 | blob | gradient | SVG |
| pattern-grid | pattern | mono | SVG |
| ... | ... | ... | ... |
```

---

## Export Format Specifications

### Icon Export Format

```
SVG Export Specifications:

+---------------------------------------------+
| <svg                                        |
|   width="24"                                |
|   height="24"                               |
|   viewBox="0 0 24 24"                       |
|   fill="none"                               |
|   xmlns="http://www.w3.org/2000/svg"        |
| >                                           |
|   <path                                     |
|     d="M12 2L..."                           |
|     stroke="currentColor"                   |
|     stroke-width="1.5"                      |
|     stroke-linecap="round"                  |
|     stroke-linejoin="round"                 |
|   />                                        |
| </svg>                                      |
+---------------------------------------------+

Key Points:
+-- Use currentColor for easy color changes
+-- viewBox preserves original ratio
+-- Remove unnecessary groups/IDs
+-- Optimize path data
```

### Multi-Size Export

```
Icon Size Export:

+-- 16x16 (Small)
|   +-- icon-name-16.svg
+-- 20x20 (Default)
|   +-- icon-name-20.svg
+-- 24x24 (Medium)
|   +-- icon-name-24.svg
+-- 32x32 (Large)
    +-- icon-name-32.svg

PNG Export (@1x, @2x, @3x):
+-- icon-name.png      (24x24)
+-- icon-name@2x.png   (48x48)
+-- icon-name@3x.png   (72x72)
```

### Illustration Export Format

```
Illustration Export Specifications:

SVG (Vector):
+-- Scalable
+-- Small file size
+-- Color customizable
+-- Best for: Logos, simple illustrations

PNG (Raster):
+-- @1x: Original size
+-- @2x: 2x size
+-- @3x: 3x size
+-- Best for: Complex illustrations, photos

WebP (Optimized):
+-- High compression rate
+-- Supports transparency
+-- Best for: Web usage
```

---

## Figma Asset Library Creation

### Figma Asset Organization

```
Asset Library
|
+-- Icons
|   +-- Frame: Icon Grid (display all icons)
|   +-- Component Set: Navigation Icons
|   +-- Component Set: Action Icons
|   +-- Component Set: Status Icons
|   +-- Component Set: Social Icons
|
+-- Illustrations
|   +-- Frame: Hero Illustrations
|   +-- Frame: Empty States
|   +-- Frame: Onboarding
|   +-- Frame: Error Pages
|
+-- Shapes & Decorations
|   +-- Frame: Blobs
|   +-- Frame: Patterns
|   +-- Frame: Background Elements
|
+-- Photos & Avatars
    +-- Frame: Avatar Placeholders
    +-- Frame: Background Photos
```

### Icon Component Setup

```
Icon Component Structure:

Component: icon/[name]
+-- Properties
|   +-- Size: 16 | 20 | 24 | 32
|   +-- Color: currentColor (overridable)
|
+-- Variants
|   +-- Style=Outline, Size=24
|   +-- Style=Outline, Size=20
|   +-- Style=Filled, Size=24
|   +-- Style=Filled, Size=20
|
+-- Auto Layout
    +-- Constraints: Scale
    +-- Resizing: Hug contents
```

### Publish as Library

```markdown
## Figma Library Publishing Checklist

### Icons
- [ ] All icons created as Components
- [ ] Naming follows convention (icon/category/name)
- [ ] Correct Variants configured
- [ ] Using currentColor
- [ ] Descriptions and keywords added

### Illustrations
- [ ] Organized as Frames
- [ ] Export settings configured
- [ ] Usage instructions added

### Publishing
- [ ] Library description added
- [ ] Version number set
- [ ] Update published
```

---

## Icon Library Generation

### React Icon Component

```tsx
// Icon component template
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

### Icon Index Generation

```tsx
// icons/index.ts
export { HomeIcon } from './HomeIcon';
export { SearchIcon } from './SearchIcon';
export { UserIcon } from './UserIcon';
export { SettingsIcon } from './SettingsIcon';
export { BellIcon } from './BellIcon';
export { HeartIcon } from './HeartIcon';
// ... other icons

// Type definitions
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

// Usage
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

// Usage
Icon(
    painter = painterResource(AppIcons.Home),
    contentDescription = "Home",
    modifier = Modifier.size(24.dp)
)
```

---

## Asset Extraction Report Template

```markdown
# Asset Extraction Report

## Source Image
[Image description]

## Extraction Summary

| Type | Count | Format |
|------|-------|--------|
| Icons | 24 | SVG |
| Illustrations | 6 | SVG/PNG |
| Shapes | 8 | SVG |
| UI Components | 5 | JSON Spec |

## Icons

### Style Specifications
- Type: Outlined
- Stroke Width: 1.5px
- Grid: 24x24
- Corners: Rounded

### Icon List
[Detailed list]

### Similar Icon Library Recommendations
- Heroicons
- Feather Icons

## Illustrations

### Style Specifications
- Type: Flat Illustration
- Palette: 6 colors
- Features: No shadows, geometric shapes

### Element List
[Detailed list]

### Similar Illustration Resources
- unDraw
- Blush

## Output Files

### Figma
- [ ] Icon Components
- [ ] Illustration Frames
- [ ] Shape Library

### Code
- [ ] SVG Files
- [ ] React Components
- [ ] iOS Assets
- [ ] Android Resources

### Design Tokens
- [ ] Icon Specification JSON
- [ ] Component Specification JSON
```

---

## Production-Ready Asset Export

This section explains how to generate production-ready assets for each platform, including standard directory structures that can be directly copied into projects.

### Android Asset Export

#### Drawable Directory Structure (Icon/Image)

```
app/src/main/res/
+-- drawable-ldpi/        # 120 DPI (0.75x)
|   +-- ic_home.png          # 36x36 px
|   +-- ic_search.png        # 36x36 px
|   +-- ic_user.png          # 36x36 px
|
+-- drawable-mdpi/        # 160 DPI (1x) - Baseline
|   +-- ic_home.png          # 48x48 px
|   +-- ic_search.png        # 48x48 px
|   +-- ic_user.png          # 48x48 px
|
+-- drawable-hdpi/        # 240 DPI (1.5x)
|   +-- ic_home.png          # 72x72 px
|   +-- ic_search.png        # 72x72 px
|   +-- ic_user.png          # 72x72 px
|
+-- drawable-xhdpi/       # 320 DPI (2x)
|   +-- ic_home.png          # 96x96 px
|   +-- ic_search.png        # 96x96 px
|   +-- ic_user.png          # 96x96 px
|
+-- drawable-xxhdpi/      # 480 DPI (3x)
|   +-- ic_home.png          # 144x144 px
|   +-- ic_search.png        # 144x144 px
|   +-- ic_user.png          # 144x144 px
|
+-- drawable-xxxhdpi/     # 640 DPI (4x)
|   +-- ic_home.png          # 192x192 px
|   +-- ic_search.png        # 192x192 px
|   +-- ic_user.png          # 192x192 px
|
+-- drawable/             # Vector Drawable (SVG converted)
    +-- ic_home.xml
    +-- ic_search.xml
    +-- ic_user.xml
```

#### Android Size Reference Table

| Density | DPI | Scale | 48px Base Size | 24px Base Size |
|---------|-----|-------|----------------|----------------|
| ldpi | 120 | 0.75x | 36x36 px | 18x18 px |
| mdpi | 160 | 1x | 48x48 px | 24x24 px |
| hdpi | 240 | 1.5x | 72x72 px | 36x36 px |
| xhdpi | 320 | 2x | 96x96 px | 48x48 px |
| xxhdpi | 480 | 3x | 144x144 px | 72x72 px |
| xxxhdpi | 640 | 4x | 192x192 px | 96x96 px |

#### Android Mipmap (App Icon)

```
app/src/main/res/
+-- mipmap-mdpi/
|   +-- ic_launcher.png              # 48x48 px
|   +-- ic_launcher_round.png        # 48x48 px
|   +-- ic_launcher_foreground.png   # 108x108 px
|
+-- mipmap-hdpi/
|   +-- ic_launcher.png              # 72x72 px
|   +-- ic_launcher_round.png        # 72x72 px
|   +-- ic_launcher_foreground.png   # 162x162 px
|
+-- mipmap-xhdpi/
|   +-- ic_launcher.png              # 96x96 px
|   +-- ic_launcher_round.png        # 96x96 px
|   +-- ic_launcher_foreground.png   # 216x216 px
|
+-- mipmap-xxhdpi/
|   +-- ic_launcher.png              # 144x144 px
|   +-- ic_launcher_round.png        # 144x144 px
|   +-- ic_launcher_foreground.png   # 324x324 px
|
+-- mipmap-xxxhdpi/
|   +-- ic_launcher.png              # 192x192 px
|   +-- ic_launcher_round.png        # 192x192 px
|   +-- ic_launcher_foreground.png   # 432x432 px
|
+-- mipmap-anydpi-v26/
    +-- ic_launcher.xml              # Adaptive Icon config
    +-- ic_launcher_round.xml
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

### iOS Asset Export

#### Asset Catalog Structure

```
Assets.xcassets/
+-- Icons/
|   +-- home.imageset/
|   |   +-- home.png           # 24x24 px (@1x)
|   |   +-- home@2x.png        # 48x48 px (@2x)
|   |   +-- home@3x.png        # 72x72 px (@3x)
|   |   +-- Contents.json
|   |
|   +-- search.imageset/
|   |   +-- search.png
|   |   +-- search@2x.png
|   |   +-- search@3x.png
|   |   +-- Contents.json
|   |
|   +-- user.imageset/
|       +-- user.png
|       +-- user@2x.png
|       +-- user@3x.png
|       +-- Contents.json
|
+-- Illustrations/
|   +-- hero-image.imageset/
|       +-- hero-image.png
|       +-- hero-image@2x.png
|       +-- hero-image@3x.png
|       +-- Contents.json
|
+-- AppIcon.appiconset/
|   +-- Icon-20.png            # 20x20 (iPad Notification @1x)
|   +-- Icon-20@2x.png         # 40x40 (iPhone Notification @2x)
|   +-- Icon-20@3x.png         # 60x60 (iPhone Notification @3x)
|   +-- Icon-29.png            # 29x29 (iPad Settings @1x)
|   +-- Icon-29@2x.png         # 58x58 (Settings @2x)
|   +-- Icon-29@3x.png         # 87x87 (Settings @3x)
|   +-- Icon-40@2x.png         # 80x80 (Spotlight @2x)
|   +-- Icon-40@3x.png         # 120x120 (Spotlight @3x)
|   +-- Icon-60@2x.png         # 120x120 (iPhone App @2x)
|   +-- Icon-60@3x.png         # 180x180 (iPhone App @3x)
|   +-- Icon-76.png            # 76x76 (iPad App @1x)
|   +-- Icon-76@2x.png         # 152x152 (iPad App @2x)
|   +-- Icon-83.5@2x.png       # 167x167 (iPad Pro @2x)
|   +-- Icon-1024.png          # 1024x1024 (App Store)
|   +-- Contents.json
|
+-- Contents.json
```

#### iOS Contents.json Example

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

#### iOS Size Reference Table

| Usage | @1x | @2x | @3x |
|-------|-----|-----|-----|
| Small Icon (16pt) | 16px | 32px | 48px |
| Standard Icon (24pt) | 24px | 48px | 72px |
| Large Icon (32pt) | 32px | 64px | 96px |
| Tab Bar (25pt) | 25px | 50px | 75px |
| Tab Bar (30pt) | 30px | 60px | 90px |
| Navigation Bar (22pt) | 22px | 44px | 66px |
| Toolbar (22pt) | 22px | 44px | 66px |

---

### Web Asset Export

#### Web Project Structure

```
public/
+-- icons/
|   +-- svg/                    # Vector (best choice)
|   |   +-- home.svg
|   |   +-- search.svg
|   |   +-- user.svg
|   |
|   +-- png/
|   |   +-- 16/                 # Small
|   |   |   +-- home.png
|   |   |   +-- search.png
|   |   +-- 24/                 # Standard
|   |   |   +-- home.png
|   |   |   +-- search.png
|   |   +-- 32/                 # Large
|   |   |   +-- home.png
|   |   |   +-- search.png
|   |   +-- 48/                 # Extra large
|   |       +-- home.png
|   |       +-- search.png
|   |
|   +-- sprite/                 # Sprite Sheet
|       +-- icons.svg              # SVG Sprite
|       +-- icons.png              # PNG Sprite
|
+-- images/
|   +-- illustrations/
|   |   +-- hero.svg
|   |   +-- hero.webp              # WebP (optimized)
|   |   +-- hero.png               # Fallback
|   |
|   +-- backgrounds/
|       +-- pattern.svg
|       +-- gradient.webp
|
+-- favicons/                   # Browser/Device Icons
|   +-- favicon.ico                # 16x16, 32x32, 48x48 (multi-size)
|   +-- favicon-16x16.png          # 16x16
|   +-- favicon-32x32.png          # 32x32
|   +-- favicon-96x96.png          # 96x96
|   +-- favicon-192x192.png        # 192x192 (Android Chrome)
|   +-- favicon-512x512.png        # 512x512 (PWA)
|   +-- apple-touch-icon.png       # 180x180 (iOS Safari)
|   +-- apple-touch-icon-152x152.png
|   +-- apple-touch-icon-167x167.png
|   +-- apple-touch-icon-180x180.png
|   +-- safari-pinned-tab.svg      # Safari Pinned Tab (mono SVG)
|   +-- mstile-144x144.png         # Windows Tile
|   +-- mstile-150x150.png
|   +-- mstile-310x310.png
|   +-- browserconfig.xml          # Windows config
|
+-- og/                         # Open Graph / Social
|   +-- og-image.png               # 1200x630 (Facebook/LinkedIn)
|   +-- og-image-square.png        # 1200x1200 (Universal)
|   +-- twitter-card.png           # 1200x600 (Twitter)
|   +-- twitter-card-summary.png   # 800x800 (Twitter Summary)
|
+-- manifest.json                  # PWA Manifest
+-- browserconfig.xml              # Windows Tile config
```

#### Web Favicon Size Specifications

| Filename | Size | Usage |
|----------|------|-------|
| favicon.ico | 16, 32, 48 | Browser tab (multi-size ICO) |
| favicon-16x16.png | 16x16 | Browser tab |
| favicon-32x32.png | 32x32 | Browser tab (high DPI) |
| favicon-96x96.png | 96x96 | Desktop shortcut |
| apple-touch-icon.png | 180x180 | iOS Safari (required) |
| favicon-192x192.png | 192x192 | Android Chrome |
| favicon-512x512.png | 512x512 | PWA Splash |
| safari-pinned-tab.svg | Vector | Safari Pinned Tab |
| mstile-144x144.png | 144x144 | Windows 8/10 Tile |
| og-image.png | 1200x630 | Facebook/LinkedIn share |
| twitter-card.png | 1200x600 | Twitter share |

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

#### HTML Head Configuration

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

### Cross-Platform Asset Export Script

#### Export Directory Structure Overview

```
production-assets/
|
+-- android/
|   +-- app/src/main/res/
|       +-- drawable-ldpi/
|       +-- drawable-mdpi/
|       +-- drawable-hdpi/
|       +-- drawable-xhdpi/
|       +-- drawable-xxhdpi/
|       +-- drawable-xxxhdpi/
|       +-- drawable/              # Vector XML
|       +-- mipmap-*/              # App Icon
|
+-- ios/
|   +-- Assets.xcassets/
|       +-- Icons/
|       +-- Illustrations/
|       +-- AppIcon.appiconset/
|
+-- web/
|   +-- public/
|       +-- icons/
|       +-- images/
|       +-- favicons/
|       +-- og/
|       +-- manifest.json
|
+-- figma/
    +-- icons.fig                  # Figma Icon Library
    +-- export-settings.json       # Export settings
```

#### Asset Export Checklist

```markdown
## Production Assets Export Checklist

### Android
- [ ] drawable-ldpi/ (36px icons)
- [ ] drawable-mdpi/ (48px icons)
- [ ] drawable-hdpi/ (72px icons)
- [ ] drawable-xhdpi/ (96px icons)
- [ ] drawable-xxhdpi/ (144px icons)
- [ ] drawable-xxxhdpi/ (192px icons)
- [ ] drawable/ (Vector XMLs)
- [ ] mipmap-*/ (App Icons)
- [ ] Adaptive Icon XMLs

### iOS
- [ ] *.imageset/ (@1x, @2x, @3x)
- [ ] Contents.json for each asset
- [ ] AppIcon.appiconset/ (all sizes)
- [ ] SF Symbol alternative suggestions

### Web
- [ ] SVG icons (optimized)
- [ ] PNG icons (16/24/32/48)
- [ ] Favicon set (ico, png, svg)
- [ ] Apple Touch Icons
- [ ] manifest.json
- [ ] browserconfig.xml
- [ ] OG Images (1200x630, 1200x1200)
- [ ] Twitter Cards

### Quality Check
- [ ] All sizes correct
- [ ] Files compressed and optimized
- [ ] Naming follows convention
- [ ] Contents.json correct
- [ ] Transparency handled correctly
```

---

## Asset Extraction Checklist

```
Icon Extraction
[ ] Identify all icons
[ ] Analyze style characteristics
[ ] Record size specifications
[ ] Recommend alternative resources
[ ] Output SVG specifications

Illustration Extraction
[ ] Identify illustration elements
[ ] Analyze style type
[ ] Record color palette
[ ] Note usage recommendations
[ ] Recommend similar resources

UI Component Extraction
[ ] Identify component types
[ ] Extract specification values
[ ] Record state changes
[ ] Output JSON specifications
[ ] Generate Figma Components

Output Completeness
[ ] SVG files optimized
[ ] PNG multi-resolution output
[ ] Figma Library created
[ ] Code Components generated
[ ] Asset list documentation
```
