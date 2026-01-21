# Figma Integration and Design Asset Management Guide

## Figma Project Structure

### Recommended Figma File Organization

```
{Project Name} - Medical App
│
├── 📄 Cover                          # Cover page
├── 📄 Design System                  # Design system
│   ├── Colors                        # Color system
│   ├── Typography                    # Typography system
│   ├── Spacing & Grid                # Spacing and grid
│   ├── Icons                         # Icon library
│   ├── Components                    # Component library
│   └── Patterns                      # Design patterns
│
├── 📄 App Icons                      # App icon designs
├── 📄 Splash & Onboarding           # Launch screens
│
├── 📄 Authentication                 # Authentication module
│   ├── SCR-001 - Login
│   ├── SCR-002 - Register
│   └── SCR-003 - Forgot Password
│
├── 📄 Home & Dashboard              # Home module
│   ├── SCR-010 - Home Dashboard
│   └── SCR-011 - Quick Actions
│
├── 📄 Patient Management            # Patient management module
│   ├── SCR-020 - Patient List
│   ├── SCR-021 - Patient Detail
│   └── SCR-022 - Patient History
│
├── 📄 Clinical Features             # Clinical features module
│   └── ...
│
└── 📄 Settings & Profile            # Settings module
    └── ...
```

## Design System Specifications

### Color System

#### Recommended Colors for Medical Software

```
Primary Colors
├── primary-50:  #E3F2FD    (lightest)
├── primary-100: #BBDEFB
├── primary-200: #90CAF9
├── primary-300: #64B5F6
├── primary-400: #42A5F5
├── primary-500: #2196F3    (primary)
├── primary-600: #1E88E5
├── primary-700: #1976D2
├── primary-800: #1565C0
└── primary-900: #0D47A1    (darkest)

Semantic Colors
├── success:  #4CAF50       (Success/Normal)
├── warning:  #FF9800       (Warning)
├── error:    #F44336       (Error/Critical)
├── info:     #2196F3       (Information)

Clinical Colors
├── critical: #D32F2F       (Critical values)
├── abnormal: #FF5722       (Abnormal)
├── normal:   #4CAF50       (Normal)
├── pending:  #9E9E9E       (Pending)

Neutral Colors
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

### Typography System

#### Recommended Fonts

```
iOS:      SF Pro Text / SF Pro Display
Android:  Roboto
Web:      Inter / Noto Sans TC

CJK Fallback:  Noto Sans TC / PingFang TC
```

#### Type Scale

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

### Spacing System

```
4px  Base unit (xs)
8px  (sm)
12px
16px (md) - commonly used
20px
24px (lg)
32px (xl)
40px
48px (2xl)
64px (3xl)
```

### Border Radius

```
none:   0px
sm:     4px
md:     8px    (common)
lg:     12px
xl:     16px
full:   9999px (circular)
```

## Figma and Requirements Traceability

### Frame Naming Convention

Each screen Frame must include requirements traceability information:

```
Frame name: SCR-{number} - {screen name}
Description includes:
- Related requirements: SRS-XXX, SRS-YYY
- Design version: v1.0
- Last updated: 2024-01-15
- Designer: @designer_name
```

### Component Naming Convention

```
{Category}/{Name}/{State}

Examples:
Button/Primary/Default
Button/Primary/Pressed
Button/Primary/Disabled
Input/Text/Default
Input/Text/Focused
Input/Text/Error
Card/Patient/Default
Alert/Critical/Default
```

### Design Annotations

Add annotations to important elements in Figma:

```
📌 Requirement Link
SRS-001: This button triggers the login verification flow

⚠️ Clinical Safety
This alert must display within 200ms

♿ Accessibility
Contrast ratio complies with WCAG AA (4.5:1)

📐 Specifications
- Width: 100% - 32px padding
- Height: 48px
- Border radius: 8px
```

## Asset Export Settings

### Icons Export

```
Figma Export Settings:

SVG (Design/Web):
- Format: SVG
- Check "Include 'id' attribute"

Android Vector Drawable:
- Use Figma plugin: "Android Resources Export"
- Or export SVG and convert in Android Studio

iOS PDF/PNG:
- Format: PDF (vector) or PNG @1x, @2x, @3x
- PDF format recommended for iOS
```

### App Icon Export

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
- App Store:           1024 × 1024 (no transparency)
```

### Images Export

```
Android (drawable):
- mdpi:    1x (base)
- hdpi:    1.5x
- xhdpi:   2x
- xxhdpi:  3x
- xxxhdpi: 4x

iOS (xcassets):
- @1x: base
- @2x: 2x
- @3x: 3x
```

## Recommended Figma Plugins

### Asset Export
- **Android Resources Export** - Export directly to Android format
- **iOS Export Settings** - Export iOS xcassets
- **SVGO Compressor** - SVG optimization

### Design Tokens
- **Design Tokens** - Export JSON format tokens
- **Token Studio** - Manage design tokens

### Collaboration & Documentation
- **Figma to Markdown** - Export design specs
- **Autoflow** - Auto-generate flow arrows
- **Contrast** - Check color contrast (accessibility)

### Developer Handoff
- **Figma to Code** - Generate code
- **Locofy** - Convert to React/Flutter code

## Collaboration with Development Team

### Design Handoff Process

```
1. Design Complete
   └── Designer marks "Ready for Dev"

2. Design Review
   └── Confirm requirements traceability (SRS-XXX)
   └── Confirm accessibility compliance
   └── Confirm clinical safety compliance

3. Asset Export
   └── Export Design Tokens (colors.json, typography.json)
   └── Export Icons (SVG → Android/iOS)
   └── Export Images (all resolutions)

4. Development Handoff
   └── Update 03-assets/ directory
   └── Update screen-to-requirements mapping
   └── Update traceability in RTM

5. Implementation Verification
   └── Screenshot comparison with Figma design
   └── Document differences and adjustments
```

### Figma Link Management

Maintain `figma-links.md` in the project:

```markdown
# Figma Project Links

## Main Files
- Design System: [Link](https://figma.com/...)
- App Screens: [Link](https://figma.com/...)
- Prototype: [Link](https://figma.com/...)

## Module Links
| Module | Figma Page | Status |
|--------|-----------|--------|
| Authentication | [Auth](https://figma.com/...) | ✅ Complete |
| Dashboard | [Home](https://figma.com/...) | 🔄 In Progress |
| Patient | [Patient](https://figma.com/...) | 📝 Planning |
```
