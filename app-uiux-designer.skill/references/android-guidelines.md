# Android Material Design 3 Design Guide

This document is based on Google Material Design 3 (Material You), providing core specifications for Android App design.

## Table of Contents
1. [Design Principles](#design-principles)
2. [Layout and Spacing](#layout-and-spacing)
3. [Navigation Patterns](#navigation-patterns)
4. [Component Specifications](#component-specifications)
5. [Typography System](#typography-system)
6. [Color System](#color-system)
7. [Icon Specifications](#icon-specifications)
8. [Animation and Motion](#animation-and-motion)
9. [Gesture Operations](#gesture-operations)
10. [Adaptive Layouts](#adaptive-layouts)

---

## Design Principles

### Material Design 3 Core Philosophy

1. **Personal**
   - Dynamic Color
   - Extract color themes from user's wallpaper

2. **Adaptive**
   - Respond to different screen sizes
   - Phone, tablet, foldable devices, desktop

3. **Expressive**
   - Larger border radius
   - More dynamic animations

4. **Accessible**
   - High contrast options
   - Clear visual hierarchy

---

## Layout and Spacing

### Base Units

```
Base unit: 8dp
Minimum touch target: 48dp
Recommended touch target: 48dp x 48dp
```

### Spacing System

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

### Screen Margins

| Screen Width | Margin |
|--------------|--------|
| < 600dp (Compact) | 16dp |
| 600-839dp (Medium) | 24dp |
| ≥ 840dp (Expanded) | 24dp |

### Window Size Classes

```
Compact: < 600dp (phones)
Medium: 600-839dp (foldables/small tablets)
Expanded: ≥ 840dp (large tablets/desktop)
```

---

## Navigation Patterns

### Navigation Bar (Bottom Navigation)

- **Use for**: 3-5 primary destinations
- **Height**: 80dp
- **Icon**: 24dp
- **Labels**: Always visible

```
┌─────────────────────────────────────────┐
│                                         │
│              Content Area               │
│                                         │
├─────────────────────────────────────────┤
│   🏠      📋      ➕      💬      👤    │
│  Home   Tasks    Add   Messages  Profile │
└─────────────────────────────────────────┘
Height: 80dp
```

### Navigation Rail

- **Use for**: Medium/Expanded screens
- **Width**: 80dp (standard) / 360dp (with labels)

```
┌──────┬──────────────────────────────────┐
│  ☰   │                                  │
│      │                                  │
│  🏠  │                                  │
│ Home │           Content Area           │
│      │                                  │
│  📋  │                                  │
│Tasks │                                  │
│      │                                  │
│  ⚙️  │                                  │
└──────┴──────────────────────────────────┘
```

### Navigation Drawer

**Modal Drawer:**
```
┌────────────────────┬────────────────────┐
│     Header         │                    │
│                    │                    │
├────────────────────┤    Masked          │
│ 🏠 Home            │    Content Area    │
│ 📋 Tasks           │                    │
│ 💬 Messages        │                    │
├────────────────────┤                    │
│ ⚙️ Settings        │                    │
│ ❓ Help            │                    │
└────────────────────┴────────────────────┘
Width: 360dp (maximum)
```

### Top App Bar

**Types:**

```
Center-aligned:
┌─────────────────────────────────────┐
│  ←            Title            ⋮   │
└─────────────────────────────────────┘

Small:
┌─────────────────────────────────────┐
│  ←   Title                     ⋮   │
└─────────────────────────────────────┘

Medium:
┌─────────────────────────────────────┐
│  ←                             ⋮   │
│  Title                              │
└─────────────────────────────────────┘

Large:
┌─────────────────────────────────────┐
│  ←                             ⋮   │
│                                     │
│  Title                              │
└─────────────────────────────────────┘

Height: Small 64dp / Medium 112dp / Large 152dp
```

---

## Component Specifications

### Buttons

**Types and hierarchy:**

| Type | Emphasis | Use Case |
|------|----------|----------|
| Filled | Highest | Primary action |
| Filled Tonal | High | Secondary important action |
| Outlined | Medium | Auxiliary action |
| Text | Low | Lowest priority action |
| Elevated | High | Action requiring separation |

**Sizes:**
```
Height: 40dp
Minimum width: 48dp
Horizontal padding: 24dp
Border radius: 20dp (full rounded)
```

**FAB (Floating Action Button):**
```
Small FAB: 40dp
FAB: 56dp
Large FAB: 96dp
Extended FAB: Height 56dp, variable width

Position: Bottom right
Distance from edge: 16dp
```

### Cards

**Types:**

| Type | Description |
|------|-------------|
| Elevated | With shadow |
| Filled | Filled background color |
| Outlined | With border |

**Specifications:**
```
Border radius: 12dp
Padding: 16dp
Shadow (Elevated): Elevation 1 (1dp)
Border (Outlined): 1dp
```

### Chips

**Types:**

```
Assist: Smart action suggestions
Filter: Filter options (multi-select)
Input: User-entered content
Suggestion: Dynamic suggestions
```

**Specifications:**
```
Height: 32dp
Border radius: 8dp
Padding: Horizontal 16dp
Icon: 18dp
```

### Lists

**List item heights:**

| Content | Height |
|---------|--------|
| Single line | 56dp |
| Two lines | 72dp |
| Three lines | 88dp |

**Structure:**
```
┌─────────────────────────────────────────────┐
│ 🖼️ │ Headline                       │  ⋮  │
│ 40 │ Supporting text                │     │
│ dp │                                │     │
└─────────────────────────────────────────────┘
Leading: Icon/Avatar  |  Content  |  Trailing: Action
```

### Text Fields

**Types:**
```
Filled: Filled background (recommended)
Outlined: Border style
```

**States:**
```
Enabled: Default state
Focused: Focused (label floats up)
Hovered: Hover
Error: Error (red)
Disabled: Disabled
```

**Specifications:**
```
Height: 56dp
Border radius: Top 4dp (Filled) / All 4dp (Outlined)
Label: Floating label animation
Helper text: Below input field
```

### Dialogs

**Types:**

```
Basic Dialog:
┌─────────────────────────────────────┐
│           Icon (optional)           │
│                                     │
│            Headline                 │
│                                     │
│        Supporting text              │
│                                     │
├─────────────────────────────────────┤
│              [Cancel]  [Confirm]    │
└─────────────────────────────────────┘

Full-screen Dialog (complex content):
┌─────────────────────────────────────┐
│ ✕  Title                     Save   │
├─────────────────────────────────────┤
│                                     │
│           Full content              │
│                                     │
└─────────────────────────────────────┘
```

**Specifications:**
```
Minimum width: 280dp
Maximum width: 560dp
Border radius: 28dp
Padding: 24dp
```

### Bottom Sheets

**Types:**
```
Standard: Coexists with content
Modal: With overlay, requires dismissal
```

**Specifications:**
```
Border radius: Top 28dp
Drag indicator: 32dp x 4dp, centered
Maximum height: 90% of screen height
```

### Snackbar

```
┌─────────────────────────────────────────────┐
│  Message text                      [Action] │
└─────────────────────────────────────────────┘

Position: Bottom, above FAB
Duration: 4-10 seconds
Border radius: 4dp
```

---

## Typography System

### Type Scale (MD3)

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
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

### Roboto Font

```
Weights: 100 Thin, 300 Light, 400 Regular,
         500 Medium, 700 Bold, 900 Black
Recommended: Regular (body), Medium (emphasis), Bold (headings)
```

---

## Color System

### Dynamic Color

Material You extracts colors from user's wallpaper:

```
Primary: Main color
Secondary: Secondary color
Tertiary: Third color
Neutral: Neutral color
Error: Error color
```

### Tonal Palettes

Each color has 13 tonal levels:

```
0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100

Example Primary:
primary0: #000000
primary10: #21005D
primary20: #381E72
primary30: #4F378B
primary40: #6750A4  ← Primary
primary50: #7F67BE
...
primary100: #FFFFFF
```

### Color Roles

**Light Theme:**
| Role | Usage |
|------|-------|
| Primary | Main components |
| On Primary | Content on Primary |
| Primary Container | Main container background |
| On Primary Container | Content on container |
| Surface | Page background |
| On Surface | Content on page |
| Surface Variant | Secondary background |
| Outline | Borders |
| Error | Error states |

### Dark Theme

Dark theme uses the same tonal palette but selects different tones:

```
Light Primary: primary40
Dark Primary: primary80

Light Surface: neutral99
Dark Surface: neutral10
```

---

## Icon Specifications

### Material Symbols

Google's official icon library, supporting 3 styles:

```
Outlined: Line style
Rounded: Rounded corners
Sharp: Sharp corners
```

**Variable properties:**
```
Fill: 0-1 (fill amount)
Weight: 100-700 (stroke thickness)
Grade: -25 to 200 (contrast)
Optical Size: 20-48 (optical size)
```

**Sizes:**
| Usage | Size |
|-------|------|
| Navigation | 24dp |
| Action | 24dp |
| List icons | 24dp |
| FAB | 24dp |
| Small icons | 18dp |

### App Icon

**Size requirements:**
```
Adaptive Icon:
- Foreground: 108dp x 108dp
- Background: 108dp x 108dp
- Safe zone: 66dp (circular mask)

Legacy:
- xxxhdpi: 192px
- xxhdpi: 144px
- xhdpi: 96px
- hdpi: 72px
- mdpi: 48px
```

**Adaptive Icon structure:**
```
┌─────────────────────┐
│    Background       │  ← Can be solid color or image
│  ┌───────────────┐  │
│  │  Foreground   │  │  ← Main icon
│  │               │  │
│  └───────────────┘  │
└─────────────────────┘
```

---

## Animation and Motion

### Animation Principles

1. **Informative**
   - Animation conveys state changes

2. **Focused**
   - Guide user attention

3. **Expressive**
   - Express brand personality

### Easing Curves

```kotlin
// Standard easing (most animations)
emphasized = CubicBezierEasing(0.2f, 0f, 0f, 1f)
emphasizedDecelerate = CubicBezierEasing(0.05f, 0.7f, 0.1f, 1f)
emphasizedAccelerate = CubicBezierEasing(0.3f, 0f, 0.8f, 0.15f)

// Standard curves
standard = CubicBezierEasing(0.2f, 0f, 0f, 1f)
standardDecelerate = CubicBezierEasing(0f, 0f, 0f, 1f)
standardAccelerate = CubicBezierEasing(0.3f, 0f, 1f, 1f)
```

### Duration

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

### Transition Animations

**Container Transform:**
```
Element morphs into another element
Use for: Card → Detail page, FAB → Page
```

**Shared Axis:**
```
Move along X, Y, or Z axis
Use for: Step navigation, Tab switching
```

**Fade Through:**
```
Fade out then fade in
Use for: Bottom navigation switching
```

**Fade:**
```
Simple fade in/out
Use for: Dialog, Snackbar
```

---

## Gesture Operations

### Standard Gestures

| Gesture | Action |
|---------|--------|
| Tap | Select, trigger |
| Long Press | Select, drag preparation |
| Swipe | Delete, action, navigate |
| Drag | Move, reorder |
| Pinch | Zoom |

### Gesture Navigation

```
Left edge swipe right: Back
Bottom swipe up: Home screen
Bottom swipe up and hold: Recent apps
Bottom horizontal swipe: Switch apps
```

### Predictive Back

Android 13+ supports back gesture preview:
```
Show previous screen preview while swiping
Support custom animations
```

---

## Adaptive Layouts

### Canonical Layouts

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
Compact: Single column
Expanded: 2-3 column grid
```

### Foldable Device Adaptation

```
Unfolded: Use Expanded layout
Folded: Use Compact layout
Desktop mode: Similar to tablet layout
```

---

## Design Checklist

### Pre-launch Verification

- [ ] Support all screen sizes (Compact/Medium/Expanded)
- [ ] Support dark theme
- [ ] Support Dynamic Color (Android 12+)
- [ ] Touch targets at least 48x48dp
- [ ] Support gesture navigation
- [ ] Support TalkBack (screen reader)
- [ ] Adaptive Icon displays correctly
- [ ] Animation performance smooth (60fps)
- [ ] Follow Material Design 3 specifications
- [ ] Pass Google Play Store review
