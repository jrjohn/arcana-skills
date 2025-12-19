# iOS Human Interface Guidelines Design Guide

This document is based on Apple Human Interface Guidelines, providing core specifications for iOS App design.

## Table of Contents
1. [Design Principles](#design-principles)
2. [Layout and Spacing](#layout-and-spacing)
3. [Navigation Patterns](#navigation-patterns)
4. [Component Specifications](#component-specifications)
5. [Typography System](#typography-system)
6. [Color System](#color-system)
7. [Icon Specifications](#icon-specifications)
8. [Animation and Transitions](#animation-and-transitions)
9. [Gesture Operations](#gesture-operations)
10. [Safe Area and Adaptation](#safe-area-and-adaptation)

---

## Design Principles

### Apple Design Core Philosophy

1. **Aesthetic Integrity**
   - Appearance aligns with functionality
   - Visual design enhances user understanding of content

2. **Consistency**
   - Follow system standard components
   - Match user's existing mental model

3. **Direct Manipulation**
   - Content can be directly touched and interacted with
   - Immediate visual feedback

4. **Feedback**
   - Every action has a clear response
   - Use haptic feedback (Haptics)

5. **Metaphors**
   - Apply real-world concepts
   - Reduce learning curve

6. **User Control**
   - User-driven interactions
   - Provide cancel/undo mechanisms

---

## Layout and Spacing

### Basic Grid System

```
Base unit: 8pt
Minimum spacing: 8pt
Standard spacing: 16pt
Large spacing: 24pt / 32pt
```

### Screen Margins

| Device | Margin |
|--------|--------|
| iPhone | 16pt |
| iPhone Max | 20pt |
| iPad | 20pt |

### Content Width

```swift
// Readable Content Width
iPhone: Screen width - 32pt (16pt on each side)
iPad: Maximum 672pt (centered)
```

### Safe Area Insets

```
iPhone (no notch): Top 20pt, Bottom 0pt
iPhone (Dynamic Island): Top 59pt, Bottom 34pt
iPhone (notch): Top 47pt, Bottom 34pt
```

---

## Navigation Patterns

### Tab Bar

- **Position**: Bottom of screen
- **Count**: 3-5 items
- **Height**: 49pt (excluding Safe Area)
- **Icons**: 25x25pt (selected/unselected states)

```
Tab item structure:
┌─────────────────────────────────────┐
│  🏠     🔍     ➕     💬     👤    │
│  Home  Search  Add   Messages  Me   │
└─────────────────────────────────────┘
Height: 49pt + Safe Area Bottom
```

### Navigation Bar

- **Height**: 44pt (excluding status bar)
- **Title**: Large Title 34pt / Standard 17pt
- **Buttons**: Left side back, right side actions

```
Large Title mode:
┌─────────────────────────────────────┐
│ Status Bar                 44pt      │
├─────────────────────────────────────┤
│ ← Back                      Edit     │ 44pt
├─────────────────────────────────────┤
│ Title                                │ 52pt
│ Title                                │
└─────────────────────────────────────┘

After scrolling (Inline Title):
┌─────────────────────────────────────┐
│ ← Back       Title          Edit     │ 44pt
└─────────────────────────────────────┘
```

### Back Button Specifications

```
Text: Previous page title (max 12 characters, show "Back" if exceeded)
Icon: chevron.left (SF Symbol)
Hit area: 44x44pt minimum
```

### Modal Modes

| Type | Use Case | Style |
|------|----------|-------|
| Sheet | Supplementary content | Slides in from bottom, swipe down to dismiss |
| Full Screen | Independent task | Full screen overlay |
| Page Sheet | Forms/Settings | Centered card on iPad |

---

## Component Specifications

### Buttons

**System button sizes:**

| Type | Height | Padding |
|------|--------|---------|
| Large | 50pt | Horizontal 20pt |
| Medium | 44pt | Horizontal 16pt |
| Small | 34pt | Horizontal 12pt |

**Button types:**

```
Filled (Primary): Filled background color
Tinted (Secondary): Light background + accent color text
Gray (Neutral): Gray background
Plain (Text): Text only, no background
```

**Button states:**

```css
Normal: 100% opacity
Highlighted: 70% opacity
Disabled: 30% opacity
```

### Lists

**List item heights:**

| Content Type | Height |
|--------------|--------|
| Single line text | 44pt |
| Two line text | 60pt |
| Three line text | 76pt |

**List structure:**

```
┌─────────────────────────────────────────────┐
│ 🖼️ │ Title text                      │ > │
│ 48 │ Subtitle description text       │   │
│ pt │                                  │   │
└─────────────────────────────────────────────┘
Left: 16pt | Icon: 48pt | Gap: 12pt | Right: 16pt
```

### Text Fields

```
Height: 44pt (single line) / Dynamic (multi-line)
Border radius: 10pt
Padding: Horizontal 12pt, Vertical 11pt
Border: 1pt (gray when unfocused, blue when focused)
```

**States:**
- Default: Gray border
- Focused: Blue border
- Error: Red border + error message
- Disabled: 50% opacity

### Toggle/Switch

```
Size: 51 x 31pt
Track radius: Full rounded
Knob: 27pt circle
On: Green (#34C759)
Off: Gray background
```

### Slider

```
Track height: 4pt
Knob: 28pt
Minimum touch area: 44x44pt
```

### Segmented Control

```
Height: 32pt
Border radius: 8pt
Minimum: 2 segments
Maximum: 5 segments
```

---

## Typography System

### SF Pro Font Family

**Dynamic Type sizes:**

| Style | Size | Weight |
|-------|------|--------|
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

**Line height recommendations:**

```
Titles: Font size × 1.2
Body text: Font size × 1.4 ~ 1.5
```

**Typography usage principles:**
1. Prefer system fonts (SF Pro)
2. Support Dynamic Type adjustable sizing
3. Use bold for emphasis, avoid overuse
4. Use PingFang TC/SC for Chinese text

---

## Color System

### System Colors

| Name | Light Mode | Dark Mode |
|------|------------|-----------|
| systemBlue | #007AFF | #0A84FF |
| systemGreen | #34C759 | #30D158 |
| systemRed | #FF3B30 | #FF453A |
| systemOrange | #FF9500 | #FF9F0A |
| systemYellow | #FFCC00 | #FFD60A |
| systemPink | #FF2D55 | #FF375F |
| systemPurple | #AF52DE | #BF5AF2 |
| systemTeal | #5AC8FA | #64D2FF |

### Semantic Colors

| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| label | #000000 | #FFFFFF |
| secondaryLabel | #3C3C43 (60%) | #EBEBF5 (60%) |
| tertiaryLabel | #3C3C43 (30%) | #EBEBF5 (30%) |
| systemBackground | #FFFFFF | #000000 |
| secondaryBackground | #F2F2F7 | #1C1C1E |
| separator | #3C3C43 (29%) | #545458 (65%) |

### Color Usage Principles

1. **Brand color**: Use as accent color, not exceeding 10%
2. **Semantic colors**: Use system-provided semantic colors
3. **Dark mode**: Must support, adjust color brightness
4. **Contrast**: Text to background at least 4.5:1

---

## Icon Specifications

### SF Symbols

Apple's official icon library, supporting 5000+ vector icons.

**Icon sizes:**

| Usage | Size |
|-------|------|
| Tab Bar | 25pt |
| Navigation Bar | 22pt |
| List items | 24-28pt |
| Inside buttons | 17-20pt |

**Icon styles:**

```
Hierarchical: Multi-level grayscale
Palette: Two-tone
Multicolor: Full color
```

**Icon rendering modes:**

```swift
.renderingMode(.template)  // Tintable
.renderingMode(.original)  // Keep original colors
```

### App Icon

**Size requirements:**

| Usage | Size |
|-------|------|
| App Store | 1024 x 1024px |
| iPhone @3x | 180 x 180px |
| iPhone @2x | 120 x 120px |
| iPad @2x | 152 x 152px |
| iPad Pro | 167 x 167px |

**Design principles:**
- Simple and recognizable
- Avoid text
- Use distinctive shapes
- Support dark mode variant

---

## Animation and Transitions

### Standard Timing Curves

```swift
easeInOut: 0.25s  // Standard interaction
easeOut: 0.2s     // Element appearing
easeIn: 0.15s     // Element disappearing
spring: 0.5s      // Spring effect
```

### Transition Animations

| Type | Duration | Usage |
|------|----------|-------|
| Push | 0.35s | Page push |
| Modal | 0.3s | Modal window |
| Fade | 0.2s | Fade in/out |
| Sheet | 0.3s | Bottom slide in |

### Haptic Feedback

```swift
.selection      // Selection
.light          // Light tap
.medium         // Medium
.heavy          // Heavy tap
.success        // Success
.warning        // Warning
.error          // Error
```

---

## Gesture Operations

### Standard Gestures

| Gesture | Action |
|---------|--------|
| Tap | Select, trigger |
| Long Press | Preview, context menu |
| Swipe | Delete, more actions |
| Drag | Move, reorder |
| Pinch | Zoom |
| Rotate | Rotate content |

### Edge Gestures

```
Left edge swipe right: Go back to previous page
Bottom swipe up: Go to home screen
Bottom swipe up and hold: App switcher
```

### Swipe Actions

```
Swipe left: Show primary actions (delete, more)
Swipe right: Show secondary actions (mark, archive)
Action button width: 80pt
```

---

## Safe Area and Adaptation

### Device Adaptation Strategy

1. **Use Auto Layout**
   - Relative constraints over absolute values
   - Use Safe Area constraints

2. **Support all sizes**
   - iPhone SE (small screen)
   - iPhone Max (large screen)
   - iPad (tablet)

3. **Orientation support**
   - Portrait
   - Landscape (as needed)

### Safe Area Handling

```swift
// Content should be within Safe Area
safeAreaInsets.top
safeAreaInsets.bottom
safeAreaInsets.left
safeAreaInsets.right

// Background can extend outside Safe Area
ignoresSafeArea(.all)
```

### Dynamic Island Adaptation

```
Avoid: Placing interactive elements in Dynamic Island area
Allowed: Background extending, animations interacting with Dynamic Island
```

---

## Design Checklist

### Pre-launch Verification

- [ ] Support all iPhone sizes
- [ ] Support dark mode
- [ ] Support Dynamic Type
- [ ] Touch targets at least 44x44pt
- [ ] Properly handle Safe Area
- [ ] Provide haptic feedback
- [ ] Support VoiceOver
- [ ] App Icon all sizes
- [ ] Launch Screen
- [ ] Comply with App Store Review Guidelines
