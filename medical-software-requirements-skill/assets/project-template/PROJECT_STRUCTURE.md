# Medical Software Project Directory Structure

This structure ensures Requirement Documents (SRS) and Design Assets (UI/UX) and Development Assets (Android/iOS) can achieve complete traceability.

## Complete Directory Structure

```
{project-name}/
│
├── 01-requirements/                    # Requirement Documents (Phase 1 Output)
│   ├── SRS/                           # Software Requirements Specification
│   │   ├── SRS-v1.0.md
│   │   └── attachments/               # SRS Attachments (Flow diagrams, Wireframes)
│   ├── interviews/                    # Interview Records
│   │   ├── 2024-01-15-stakeholder-A.md
│   │   └── 2024-01-16-clinical-team.md
│   └── analysis/                      # Analysis Documents
│       ├── stakeholder-analysis.md
│       ├── risk-analysis.md           # ISO 14971 Risk Analysis
│       └── safety-classification.md   # IEC 62304 Safety Classification
│
├── 02-design/                         # Design Documents (Phase 2 Output)
│   ├── SDD/                           # Software Design Specification
│   │   └── SDD-v1.0.md
│   ├── SWD/                           # Software Detailed Design
│   │   └── SWD-v1.0.md
│   ├── architecture/                  # Architecture Design
│   │   ├── system-architecture.md
│   │   ├── data-model.md
│   │   └── api-design.md
│   └── ui-ux/                         # UI/UX Design
│       ├── design-system.md           # Design System Description
│       ├── figma-links.md             # Figma Link List
│       └── screen-mapping.md          # Screen and Requirement Mapping Table
│
├── 03-assets/                         # Design Assets (with Figma Synchronization)
│   │
│   ├── design-tokens/                 # Design Tokens (Exported from Figma)
│   │   ├── colors.json                # Color Definitions
│   │   ├── typography.json            # Font Definitions
│   │   ├── spacing.json               # Spacing Definitions
│   │   └── shadows.json               # Shadow Definitions
│   │
│   ├── icons/                         # Icon Resources
│   │   ├── svg/                       # Original SVG (for Design)
│   │   │   ├── ic_home.svg
│   │   │   ├── ic_patient.svg
│   │   │   └── ic_alert.svg
│   │   ├── android/                   # Android Format
│   │   │   └── drawable/
│   │   │       ├── ic_home.xml        # Vector Drawable
│   │   │       └── ic_patient.xml
│   │   └── ios/                       # iOS Format
│   │       └── Icons.xcassets/
│   │           ├── ic_home.imageset/
│   │           └── ic_patient.imageset/
│   │
│   ├── app-icons/                     # App Icons
│   │   ├── source/                    # Original Design Files
│   │   │   └── app-icon-1024.png      # 1024x1024 Original
│   │   ├── android/                   # Android All Sizes
│   │   │   ├── mipmap-mdpi/           # 48x48
│   │   │   ├── mipmap-hdpi/           # 72x72
│   │   │   ├── mipmap-xhdpi/          # 96x96
│   │   │   ├── mipmap-xxhdpi/         # 144x144
│   │   │   ├── mipmap-xxxhdpi/        # 192x192
│   │   │   └── playstore-icon.png     # 512x512 (Play Store)
│   │   └── ios/                       # iOS All Sizes
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
│   ├── images/                        # Image Resources
│   │   ├── source/                    # Original Design Files
│   │   ├── android/                   # Android Format
│   │   │   ├── drawable-mdpi/
│   │   │   ├── drawable-hdpi/
│   │   │   ├── drawable-xhdpi/
│   │   │   ├── drawable-xxhdpi/
│   │   │   └── drawable-xxxhdpi/
│   │   └── ios/                       # iOS Format
│   │       └── Images.xcassets/
│   │
│   ├── splash/                        # Splash Screen
│   │   ├── source/
│   │   ├── android/
│   │   └── ios/
│   │
│   └── screenshots/                   # Screenshots (for Documents/Store)
│       ├── android/
│       └── ios/
│
├── 04-testing/                        # Test Documents
│   ├── STP/                           # Software Test Plan
│   │   └── STP-v1.0.md
│   ├── STC/                           # Software Test Cases
│   │   └── STC-v1.0.md
│   └── test-reports/                  # Test Reports
│
├── 05-validation/                     # Validation Documents
│   ├── SVV/                           # Software Verification & Validation
│   │   └── SVV-v1.0.md
│   └── RTM/                           # Requirement Traceability Matrix
│       └── RTM-v1.0.md
│
├── 06-regulatory/                     # Regulatory Documents
│   ├── risk-management/               # ISO 14971 Risk Management
│   ├── cybersecurity/                 # Cybersecurity Documents
│   └── submissions/                   # Submission Documents
│
└── _config/                           # Project Configuration
    ├── figma-config.md                # Figma Project Configuration
    ├── asset-export-guide.md          # Asset Export Guide
    └── naming-conventions.md          # Naming Conventions
```

## Requirement and Asset Traceability Mapping

### Traceability Relationship Diagram

```
SRS-001 (Requirement)
    │
    ├──→ SDD-001 (Design)
    │        │
    │        └──→ UI Screen: SCR-001 (Screen)
    │                  │
    │                  ├──→ Figma Frame: "Login Screen"
    │                  │
    │                  └──→ Assets:
    │                        ├── icons/ic_login.svg
    │                        ├── images/bg_login.png
    │                        └── design-tokens/colors.json
    │
    └──→ STC-001 (Test)
             │
             └──→ Screenshots: login_success.png
```

### Screen and Requirement Mapping Table Example

| Screen ID | Screen Name | Related Requirements | Figma Frame | Related Assets |
|---------|----------|----------|-------------|----------|
| SCR-001 | Login Screen | SRS-001, SRS-002 | [Login Screen](figma-link) | ic_login, bg_login |
| SCR-002 | Home Dashboard | SRS-010~015 | [Home Dashboard](figma-link) | ic_home, ic_patient |
| SCR-003 | Patient Data | SRS-020~025 | [Patient Detail](figma-link) | ic_patient, ic_alert |

## Naming Conventions

### Document Naming

```
{DocumentType}-v{Version}.md

Example:
- SRS-v1.0.md
- SRS-v1.1.md (minor version)
- SRS-v2.0.md (major version)
```

### Asset Naming

```
{Type}_{Description}_{Status}.{Format}

Type:
- ic_ : Icon
- bg_ : Background
- img_: Image
- btn_: Button
- logo_: Logo

Status (Optional):
- _normal
- _pressed
- _disabled
- _selected

Example:
- ic_home_normal.svg
- btn_submit_pressed.png
- bg_login.png
```

### Figma 命名

```
Page: {ModuleName}
Frame: {ScreenID} - {Screen Name}
Component: {Type}/{Name}/{Status}

Example:
Page: Authentication
Frame: SCR-001 - Login Screen
Component: Button/Primary/Normal
```

---

## Android / iOS Asset Size Specifications

For detailed size specifications, please refer to [references/asset-specifications.md](../../references/asset-specifications.md)

### Quick Reference

#### App Icon Sizes

**Android (mipmap):**
| Density | Directory | Size |
|------|------|------|
| mdpi | `mipmap-mdpi/` | 48 × 48 |
| hdpi | `mipmap-hdpi/` | 72 × 72 |
| xhdpi | `mipmap-xhdpi/` | 96 × 96 |
| xxhdpi | `mipmap-xxhdpi/` | 144 × 144 |
| xxxhdpi | `mipmap-xxxhdpi/` | 192 × 192 |
| Play Store | - | 512 × 512 |

**iOS (AppIcon.appiconset):**
| Purpose | @2x | @3x |
|------|-----|-----|
| Notification (20pt) | 40×40 | 60×60 |
| Settings (29pt) | 58×58 | 87×87 |
| Spotlight (40pt) | 80×80 | 120×120 |
| App (60pt) | 120×120 | 180×180 |
| App Store | 1024×1024 | - |

#### Icon Sizes

**Android: Recommend Using Vector Drawable (.xml)**
- Converted from SVG, no need for multiple resolutions

**iOS: Recommend Using PDF**
- Single PDF, system auto-scales

If Using PNG:
| Density/Scale | Android | iOS |
|------------|---------|-----|
| 1x / mdpi | 24×24 | 22×22 |
| 2x / xhdpi / @2x | 48×48 | 44×44 |
| 3x / xxhdpi / @3x | 72×72 | 66×66 |
| 4x / xxxhdpi | 96×96 | - |

#### Image Sizes

**Android (drawable):**
| Density | Ratio | Example (100pt Design) |
|------|------|-------------------|
| mdpi | 1x | 100×100 px |
| hdpi | 1.5x | 150×150 px |
| xhdpi | 2x | 200×200 px |
| xxhdpi | 3x | 300×300 px |
| xxxhdpi | 4x | 400×400 px |

**iOS (xcassets):**
| Scale | Example (100pt Design) |
|-------|-------------------|
| @1x | 100×100 px (Can Omit) |
| @2x | 200×200 px |
| @3x | 300×300 px |

---

## Asset Directory Detailed Structure

```
03-assets/
│
├── design-tokens/                      # Design Tokens
│   ├── colors.json
│   ├── typography.json
│   └── spacing.json
│
├── icons/                              # Icons
│   ├── svg/                            # Original SVG
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
│           │   └── ic_home.pdf         # or PNG @1x/@2x/@3x
│           └── ic_patient.imageset/
│
├── app-icons/                          # App Icons
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
├── images/                             # Images
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
│               ├── bg_login.png        # @1x (Can Omit)
│               ├── bg_login@2x.png     # @2x
│               └── bg_login@3x.png     # @3x
│
└── splash/                             # Splash Screen
    ├── source/
    ├── android/                        # Recommend Using Splash Screen API
    └── ios/                            # Recommend Using LaunchScreen.storyboard
```
