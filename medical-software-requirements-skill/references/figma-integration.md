# Figma Integration and Design Assets Management Guide

## Figma Project Structure

### Recommended Figma File Organization

```
{Project Name} - Medical App
│
├── 📄 Cover                          # Cover Page
├── 📄 Design System                  # Design System
│   ├── Colors                        # Color System
│   ├── Typography                    # Font System
│   ├── Spacing & Grid                # Spacing and Grid Lines
│   ├── Icons                         # Icon Library
│   ├── Components                    # Component Library
│   └── Patterns                      # Design Patterns
│
├── 📄 App Icons                      # App Icon Design
├── 📄 Splash & Onboarding           # Start Screen
│
├── 📄 Authentication                 # Authentication Module
│   ├── SCR-001 - Login
│   ├── SCR-002 - Register
│   └── SCR-003 - Forgot Password
│
├── 📄 Home & Dashboard              # Home Module
│   ├── SCR-010 - Home Dashboard
│   └── SCR-011 - Quick Actions
│
├── 📄 Patient Management            # Patient Management Module
│   ├── SCR-020 - Patient List
│   ├── SCR-021 - Patient Detail
│   └── SCR-022 - Patient History
│
├── 📄 Clinical Features             # Clinical Function Module
│   └── ...
│
└── 📄 Settings & Profile            # Settings Module
    └── ...
```

## Design System Design Specification

### Color System (Colors)

#### Medical Software Recommended Colors

```
Primary Colors
├── primary-50:  #E3F2FD    (Lightest)
├── primary-100: #BBDEFB
├── primary-200: #90CAF9
├── primary-300: #64B5F6
├── primary-400: #42A5F5
├── primary-500: #2196F3    (Primary)
├── primary-600: #1E88E5
├── primary-700: #1976D2
├── primary-800: #1565C0
└── primary-900: #0D47A1    (Darkest)

Semantic Colors
├── success:  #4CAF50       (Success/Normal)
├── warning:  #FF9800       (Warning)
├── error:    #F44336       (Error/Critical)
├── info:     #2196F3       (Information)

Clinical Colors (Clinical Specific)
├── critical: #D32F2F       (Critical Value)
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

### Font System (Typography)

#### Recommended Fonts

```
iOS:      SF Pro Text / SF Pro Display
Android:  Roboto
Web:      Inter / Noto Sans TC

Chinese Backup:  Noto Sans TC / PingFang TC
```

#### Font Scale Levels

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

### Spacing System (Spacing)

```
4px  foundation unit (xs)
8px  (sm)
12px
16px (md) - Commonly Used
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
md:     8px    (Commonly Used)
lg:     12px
xl:     16px
full:   9999px (round)
```

## Figma and Requirement Traceability

### Frame Naming Specification

Every Screen Frame must include Requirement Traceability information:

```
Frame Name: SCR-{Number} - {Screen Name}
Description (Description) Include:
- Corresponding Requirement: SRS-XXX, SRS-YYY
- Design Version: v1.0
- Last Update: 2024-01-15
- Designer: @designer_name
```

### Component Naming Specification

```
{Category}/{Name}/{Status}

Example:
Button/Primary/Default
Button/Primary/Pressed
Button/Primary/Disabled
Input/Text/Default
Input/Text/Focused
Input/Text/Error
Card/Patient/Default
Alert/Critical/Default
```

### Design Comments (Annotations)

Add comments to important elements in Figma:

```
📌 Requirement Relationship
SRS-001: This button triggers login validation flow

⚠️ Clinical Safety
This alert must be displayed within 200ms

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

SVG (Design Use/Web):
- Format: SVG
- Check "Include 'id' attribute"

Android Vector Drawable:
- Use Figma plugin: "Android Resources Export"
- Or export SVG then use Android Studio to convert

iOS PDF/PNG:
- Format: PDF (Vector) or PNG @1x, @2x, @3x
- iOS recommended to use PDF format
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
- App Store:           1024 × 1024 (No transparency)
```

### Image Export

```
Android (drawable):
- mdpi:    1x (base resolution)
- hdpi:    1.5x
- xhdpi:   2x
- xxhdpi:  3x
- xxxhdpi: 4x

iOS (xcassets):
- @1x: base resolution
- @2x: 2 times
- @3x: 3 times
```

## Figma Plugin Recommendations

### Asset Export
- **Android Resources Export** - Directly export Android format
- **iOS Export Settings** - Export iOS xcassets
- **SVGO Compressor** - SVG Optimization

### Design Token
- **Design Tokens** - Export JSON format tokens
- **Token Studio** - Manage design tokens

### Collaboration and Documentation
- **Figma to Markdown** - Export design specifications
- **Autoflow** - Auto-generate flow arrows
- **Contrast** - Check color contrast ratio (Accessibility)

### Development Handoff
- **Figma to Code** - Generate code
- **Locofy** - Convert to React/Flutter code

## Development Team Collaboration

### Design Handoff Flow

```
1. Design Complete
   └── Designer marks "Ready for Dev"

2. Design Review
   └── Confirm requirement traceability (SRS-XXX)
   └── Confirm accessibility specifications
   └── Confirm clinical safety specifications

3. Asset Export
   └── Export Design Tokens (colors.json, typography.json)
   └── Export Icons (SVG → Android/iOS)
   └── Export Images (each resolution)

4. Development Handoff
   └── Update 03-assets/ directory
   └── Update screen and requirement mapping table
   └── Update traceability relationships in RTM

5. Implementation Validation
   └── Screenshot comparison with Figma design
   └── Record differences and adjust
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
|------|-----------|------|
| Authentication | [Auth](https://figma.com/...) | ✅ Complete |
| Dashboard | [Home](https://figma.com/...) | 🔄 In Progress |
| Patient | [Patient](https://figma.com/...) | 📝 Planning |
```
