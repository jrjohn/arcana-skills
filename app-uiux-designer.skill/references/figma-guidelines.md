# Figma Design Guide and Export Specifications

This document provides Figma design workflows, component architecture, and export format specifications.

## Table of Contents
1. [File Structure and Organization](#file-structure-and-organization)
2. [Auto Layout](#auto-layout)
3. [Components and Variants](#components-and-variants)
4. [Design Tokens](#design-tokens)
5. [Design Export Formats](#design-export-formats)
6. [Developer Handoff](#developer-handoff)
7. [Recommended Plugins](#recommended-plugins)
8. [Figma API](#figma-api)

---

## File Structure and Organization

### Project-Level Structure

```
📁 [Project Name]
├── 📄 🎨 Design System
│   ├── Foundation
│   ├── Components
│   └── Patterns
│
├── 📄 📱 Mobile App
│   ├── iOS
│   └── Android
│
├── 📄 🖥️ Web App
│   ├── Desktop
│   ├── Tablet
│   └── Mobile
│
├── 📄 🧪 Prototypes
│   └── User Flows
│
└── 📄 📦 Handoff
    └── Dev Specs
```

### Page Naming Conventions

```
📄 Cover
📄 📋 Index
📄 🎨 Foundations
    ├── Colors
    ├── Typography
    ├── Spacing
    ├── Effects
    └── Icons
📄 🧱 Components
    ├── Buttons
    ├── Inputs
    ├── Cards
    └── Navigation
📄 📱 Screens
    ├── Onboarding
    ├── Home
    ├── Profile
    └── Settings
📄 🔄 Flows
📄 ✅ Ready for Dev
📄 🗃️ Archive
```

### Frame Naming Conventions

```
Page: PageName / Variant / State
Component: ComponentName / Size / Variant / State
Layer: element-name (kebab-case)

Examples:
├── Login / Default
├── Login / Error
├── Login / Loading
├── Button / Large / Primary / Default
├── Button / Large / Primary / Hover
└── Button / Large / Primary / Disabled
```

### Layer Naming Rules

```
Frame: PascalCase (Login, UserCard, NavBar)
Group: PascalCase (ButtonGroup, IconSet)
Elements: kebab-case (icon-left, text-label, bg-overlay)
States: state=value (state=hover, state=active)

✅ Good naming:
├── Button
│   ├── icon-left
│   ├── label
│   └── icon-right

❌ Avoid:
├── Frame 123
│   ├── Rectangle 1
│   └── Text
```

---

## Auto Layout

### Basic Concepts

```
Auto Layout = Flexbox for Figma

Direction:
├── Horizontal → Row
└── Vertical → Column

Alignment:
├── Main Axis: Primary axis alignment
└── Cross Axis: Secondary axis alignment

Spacing:
├── Gap: Space between children
└── Padding: Inner spacing
```

### Auto Layout Settings

```
┌─────────────────────────────────────────┐
│  Direction: Horizontal ↔️ / Vertical ↕️  │
├─────────────────────────────────────────┤
│  Gap: 8px (spacing between elements)    │
├─────────────────────────────────────────┤
│  Padding:                               │
│  ┌──────┬──────────────────┬──────┐    │
│  │  16  │                  │  16  │    │
│  ├──────┤      Content     ├──────┤    │
│  │  12  │                  │  12  │    │
│  └──────┴──────────────────┴──────┘    │
│  Top: 12 | Right: 16 | Bottom: 12 | Left: 16 │
├─────────────────────────────────────────┤
│  Alignment: ⬛⬜⬜ | ⬜⬛⬜ | ⬜⬜⬛        │
│             ⬜⬜⬜ | ⬜⬜⬜ | ⬜⬜⬜        │
│             ⬜⬜⬜ | ⬜⬜⬜ | ⬜⬜⬜        │
└─────────────────────────────────────────┘
```

### Resizing Behavior

```
Child Resizing:
├── Fixed: Maintains set dimensions
├── Hug: Adjusts to content
└── Fill: Fills available space

Example - Button:
┌─────────────────────────────────────┐
│ [Icon]        Label        [Icon]   │
│  Fixed    Fill Container    Fixed   │
└─────────────────────────────────────┘
```

### Practical Tips

**Absolute Position:**
```
Use for: Badges, close buttons, floating elements
Setting: Click element → Right panel → Absolute Position
Position: Set relative position to parent (constraints)
```

**Negative Spacing:**
```
Use for: Overlapping avatars, stacked cards
Setting: Set Gap to negative value (e.g., -8)
```

**Space Between:**
```
Use for: Navigation bars with items at both ends
Setting: Select "Space between" alignment mode
```

---

## Components and Variants

### Component Structure

```
Main Component
├── Instance
│   ├── Override properties
│   └── Links to main component
└── Variant
    ├── Different states of same component
    └── Switch via Properties
```

### Component Creation Best Practices

```markdown
1. Select Frame
2. Right-click → Create Component (Ctrl/Cmd + Alt + K)
3. Use Auto Layout
4. Set Constraints
5. Define Variants
6. Add Component Properties
```

### Variant Naming Conventions

```
Property=Value format

Example - Button:
├── Size=Large, Variant=Primary, State=Default
├── Size=Large, Variant=Primary, State=Hover
├── Size=Large, Variant=Primary, State=Disabled
├── Size=Medium, Variant=Primary, State=Default
├── Size=Small, Variant=Secondary, State=Default
└── ...

Properties:
├── Size: Large, Medium, Small
├── Variant: Primary, Secondary, Outline, Ghost
├── State: Default, Hover, Focus, Active, Disabled
└── Icon: True, False
```

### Component Property Types

```
1. Variant
   Switch between predefined design variations
   Use for: Size, Type, State

2. Boolean
   Show/hide elements
   Use for: hasIcon, showBadge, isSelected

3. Instance Swap
   Replace nested components
   Use for: Swapping icons, avatars

4. Text
   Override text content
   Use for: Label, Title, Description
```

### Component Example

**Button Component:**
```
Button
├── Properties
│   ├── Size: Large | Medium | Small
│   ├── Variant: Primary | Secondary | Outline | Ghost
│   ├── State: Default | Hover | Focus | Active | Disabled
│   ├── IconLeft: Boolean
│   └── IconRight: Boolean
│
├── Structure (Auto Layout - Horizontal)
│   ├── icon-left (Instance Swap, Hidden by default)
│   ├── label (Text Property)
│   └── icon-right (Instance Swap, Hidden by default)
│
└── Variants Grid (60 variants total)
    ├── Large/Primary/Default
    ├── Large/Primary/Hover
    └── ...
```

### Slots Pattern

```
For components with replaceable content (e.g., Card)

Card
├── slot-header (Frame with Auto Layout)
│   └── .slot-header (Hidden placeholder)
├── slot-content
│   └── .slot-content
└── slot-footer
    └── .slot-footer

Paste content into corresponding slot and hide placeholder when using
```

---

## Design Tokens

### Token Structure in Figma

```
Figma Variables (Variable System)

Collections:
├── Primitives
│   ├── Colors
│   │   ├── blue/50: #EFF6FF
│   │   ├── blue/100: #DBEAFE
│   │   └── ...
│   ├── Spacing
│   │   ├── 1: 4
│   │   ├── 2: 8
│   │   └── ...
│   └── Radius
│       ├── sm: 4
│       ├── md: 8
│       └── ...
│
└── Semantic
    ├── Colors
    │   ├── bg/primary: {primitives.white}
    │   ├── bg/secondary: {primitives.gray/50}
    │   ├── text/primary: {primitives.gray/900}
    │   ├── text/secondary: {primitives.gray/600}
    │   ├── border/default: {primitives.gray/200}
    │   └── interactive/primary: {primitives.blue/500}
    │
    └── Spacing
        ├── page/padding: {primitives.spacing/4}
        ├── section/gap: {primitives.spacing/8}
        └── component/gap: {primitives.spacing/4}
```

### Creating Variables

```markdown
1. Open Variables Panel
   - Right panel → Local Variables
   - Or Figma Menu → Plugins → Variables

2. Create Collection
   - Click + Create Collection
   - Name: Primitives, Semantic, Component

3. Add Variables
   - Click + Create Variable
   - Select type: Color, Number, String, Boolean
   - Set value

4. Create Alias
   - Click variable value
   - Select another variable as reference
```

### Modes

```
Use for: Light/Dark themes, multi-brand support

Example - Theme switching:
Collection: Semantic Colors
├── Mode 1: Light
│   ├── bg/primary: #FFFFFF
│   └── text/primary: #111827
│
└── Mode 2: Dark
    ├── bg/primary: #111827
    └── text/primary: #F9FAFB

Usage: Select Frame → Right panel switch Mode
```

### Exporting Design Tokens

**Tokens Studio Plugin Format:**
```json
{
  "colors": {
    "primary": {
      "value": "#3B82F6",
      "type": "color"
    },
    "text": {
      "primary": {
        "value": "{colors.gray.900}",
        "type": "color"
      }
    }
  },
  "spacing": {
    "sm": {
      "value": "8",
      "type": "spacing"
    }
  }
}
```

**Style Dictionary Output:**
```css
/* CSS Variables */
:root {
  --color-primary: #3B82F6;
  --color-text-primary: #111827;
  --spacing-sm: 8px;
}
```

```swift
// iOS Swift
enum Colors {
    static let primary = UIColor(hex: "#3B82F6")
    static let textPrimary = UIColor(hex: "#111827")
}
```

```kotlin
// Android Kotlin
object Colors {
    val Primary = Color(0xFF3B82F6)
    val TextPrimary = Color(0xFF111827)
}
```

---

## Design Export Formats

### Exporting Image Assets

**Export Settings:**
```
Format Selection:
├── PNG: Raster images, screenshots, complex images
├── JPG: Photos, large backgrounds
├── SVG: Icons, vector graphics, logos
├── PDF: Vector assets, iOS icons
└── WebP: Web-optimized images

Resolution (Scale):
├── @1x: Base size
├── @2x: Retina (iOS @2x, Android xxhdpi)
├── @3x: Super Retina (iOS @3x, Android xxxhdpi)
└── @4x: High-resolution displays

Naming Convention:
├── icon-name.svg
├── icon-name@2x.png
├── icon-name@3x.png
└── illustration-hero.webp
```

**Batch Export Settings:**
```
1. Select element
2. Right panel → Export
3. Click + to add multiple export settings
4. Use Suffix to differentiate: @2x, @3x

Example:
├── 1x → icon-home.png
├── 2x → icon-home@2x.png
└── 3x → icon-home@3x.png
```

### Exporting CSS Styles

**Copy CSS Directly:**
```css
/* Select element → Right-click → Copy as CSS */

/* Frame */
.element {
  width: 320px;
  height: 48px;
  padding: 12px 16px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
}

/* Text */
.text {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  line-height: 24px;
  color: #111827;
}
```

### Exporting iOS/Android Code

**Copy as Code Plugin:**
```swift
// iOS SwiftUI
struct Button: View {
    var body: some View {
        HStack(spacing: 8) {
            Image("icon")
            Text("Label")
                .font(.system(size: 16, weight: .semibold))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.blue)
        .cornerRadius(8)
    }
}
```

```kotlin
// Android Jetpack Compose
@Composable
fun Button() {
    Row(
        modifier = Modifier
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .background(Color.Blue, RoundedCornerShape(8.dp)),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Icon(painter = painterResource(R.drawable.icon))
        Text(
            text = "Label",
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold
        )
    }
}
```

### Exporting JSON Specs

**Figma REST API Output:**
```json
{
  "id": "1:2",
  "name": "Button",
  "type": "FRAME",
  "absoluteBoundingBox": {
    "x": 0,
    "y": 0,
    "width": 120,
    "height": 48
  },
  "fills": [
    {
      "type": "SOLID",
      "color": {
        "r": 0.231,
        "g": 0.510,
        "b": 0.965,
        "a": 1
      }
    }
  ],
  "cornerRadius": 8,
  "paddingLeft": 16,
  "paddingRight": 16,
  "paddingTop": 12,
  "paddingBottom": 12,
  "itemSpacing": 8,
  "layoutMode": "HORIZONTAL"
}
```

---

## Developer Handoff

### Dev Mode

```
Figma Dev Mode Features:
├── Auto-annotate dimensions and spacing
├── Copy CSS/iOS/Android code
├── View Variables mapping
├── Compare design changes
└── VS Code integration
```

### Handoff Specification Document

**Component Specs:**
```markdown
## Button Component

### Visual Specifications
- Height: 48px (Large), 40px (Medium), 32px (Small)
- Border radius: 8px
- Padding: 16px (horizontal), 12px (vertical)
- Gap: 8px (between icon and label)

### Colors
| State | Background | Text | Border |
|-------|------------|------|--------|
| Default | primary-500 | white | - |
| Hover | primary-600 | white | - |
| Active | primary-700 | white | - |
| Disabled | gray-200 | gray-400 | - |

### Typography
- Font: Inter
- Size: 16px
- Weight: 600 (Semibold)
- Line Height: 24px

### Animation
- Transition: all 150ms ease-out
- Hover: scale(1.02)
- Active: scale(0.98)
```

### Annotation Best Practices

```
1. Use Auto Layout
   Spacing auto-annotates

2. Use Variables
   Show Token names instead of values

3. Consistent naming
   Ensure layer names are clear

4. Organized handoff
   ├── Ready
   ├── In Review
   └── In Progress

5. Version marking
   v1.0 → v1.1 → v2.0
```

---

## Recommended Plugins

### Design System Related

| Plugin | Purpose |
|--------|---------|
| Tokens Studio | Design Token management and sync |
| Style Organizer | Organize Styles |
| Design Lint | Check design consistency |
| Themer | Theme switching preview |

### Efficiency Tools

| Plugin | Purpose |
|--------|---------|
| Autoflow | Auto-generate flow lines |
| Content Reel | Placeholder data fill |
| Unsplash | Free images |
| Iconify | Icon library |
| Stark | Accessibility checker |

### Developer Collaboration

| Plugin | Purpose |
|--------|---------|
| Anima | Export to React/Vue/HTML |
| Locofy | Design to code |
| Zeplin | Design handoff platform |
| Storybook Connect | Link to Storybook |

### Content Generation

| Plugin | Purpose |
|--------|---------|
| Lorem ipsum | Placeholder text |
| User Profile | Fake user data |
| Charts | Chart generation |
| Mapsicle | Map embedding |

---

## Figma API

### REST API Basics

**Get File Information:**
```bash
GET https://api.figma.com/v1/files/:file_key

Headers:
X-Figma-Token: your-personal-access-token
```

**Response Example:**
```json
{
  "name": "My Design File",
  "lastModified": "2024-01-15T10:30:00Z",
  "version": "123456789",
  "document": {
    "id": "0:0",
    "name": "Document",
    "type": "DOCUMENT",
    "children": [...]
  },
  "components": {...},
  "styles": {...}
}
```

### Common API Endpoints

```
Files:
GET /v1/files/:key                    # Get file
GET /v1/files/:key/nodes?ids=...      # Get specific nodes
GET /v1/files/:key/images             # Export images

Components:
GET /v1/files/:key/components         # Get components
GET /v1/files/:key/component_sets     # Get component sets

Styles:
GET /v1/files/:key/styles             # Get styles

Variables:
GET /v1/files/:key/variables/local    # Get Variables

Projects:
GET /v1/projects/:id/files            # Get project files

Comments:
GET /v1/files/:key/comments           # Get comments
POST /v1/files/:key/comments          # Add comment
```

### Exporting Images

```bash
# Get image URLs
GET https://api.figma.com/v1/images/:file_key
  ?ids=1:2,1:3
  &scale=2
  &format=png

# Response
{
  "images": {
    "1:2": "https://s3-us-west-2.amazonaws.com/figma-alpha-api/img/...",
    "1:3": "https://s3-us-west-2.amazonaws.com/figma-alpha-api/img/..."
  }
}
```

### Webhook Integration

```json
// Webhook setup
POST https://api.figma.com/v2/webhooks

{
  "event_type": "FILE_UPDATE",
  "team_id": "123456",
  "endpoint": "https://your-server.com/figma-webhook",
  "passcode": "your-secret-passcode"
}

// Webhook event
{
  "event_type": "FILE_UPDATE",
  "file_key": "abc123",
  "file_name": "My Design",
  "timestamp": "2024-01-15T10:30:00Z",
  "triggered_by": {
    "id": "user123",
    "handle": "designer"
  }
}
```

### Automation Example

**Node.js - Export All Icons:**
```javascript
const axios = require('axios');

const FIGMA_TOKEN = 'your-token';
const FILE_KEY = 'your-file-key';
const ICONS_FRAME_ID = '1:234';

async function exportIcons() {
  // 1. Get all nodes in Frame
  const { data } = await axios.get(
    `https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${ICONS_FRAME_ID}`,
    { headers: { 'X-Figma-Token': FIGMA_TOKEN } }
  );

  // 2. Collect all icon IDs
  const iconIds = data.nodes[ICONS_FRAME_ID].document.children
    .map(child => child.id)
    .join(',');

  // 3. Export as SVG
  const { data: images } = await axios.get(
    `https://api.figma.com/v1/images/${FILE_KEY}?ids=${iconIds}&format=svg`,
    { headers: { 'X-Figma-Token': FIGMA_TOKEN } }
  );

  // 4. Download and save
  for (const [id, url] of Object.entries(images.images)) {
    const svg = await axios.get(url);
    // Save SVG files...
  }
}
```

---

## Figma Export Checklist

### Pre-Handoff Verification

```
File Organization
□ Pages named clearly
□ Frame naming follows conventions
□ Layer structure is clean
□ No unnecessary hidden layers

Component Quality
□ Using Auto Layout
□ Constraints set correctly
□ Variants complete
□ Properties defined clearly

Design Tokens
□ Variables defined
□ Colors use Variables
□ Spacing uses Variables
□ Dark mode support

Export Preparation
□ Image assets have Export settings
□ Multi-resolution export (@1x, @2x, @3x)
□ SVG icons optimized
□ Images compressed

Handoff Specs
□ Component specification documents
□ Interaction descriptions
□ Animation specifications
□ Responsive design notes
```
