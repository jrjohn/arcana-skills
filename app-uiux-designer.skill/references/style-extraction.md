# Visual Style Extraction and Replication Guide

This guide provides methodology for extracting visual styles from reference images and generating consistent UI/UX designs.

## Table of Contents
1. [Style Extraction Process](#style-extraction-process)
2. [Color Analysis](#color-analysis)
3. [Typography Analysis](#typography-analysis)
4. [Shape and Layout](#shape-and-layout)
5. [Effects and Textures](#effects-and-textures)
6. [Style Token Generation](#style-token-generation)
7. [Figma Style Output](#figma-style-output)
8. [Style Application Examples](#style-application-examples)

---

## Style Extraction Process

### Overall Flow

```
Input Reference Image
     ↓
┌─────────────────────────────────────────────┐
│              Visual Style Analysis           │
├─────────────┬─────────────┬─────────────────┤
│ Color       │ Typography  │ Shape           │
│ Analysis    │ Analysis    │ Analysis        │
├─────────────┼─────────────┼─────────────────┤
│ Effects     │ Layout      │ Imagery         │
│ Analysis    │ Analysis    │ Style           │
└─────────────┴─────────────┴─────────────────┘
     ↓
Style Token Generation
     ↓
Figma Style Output
     ↓
Generate Consistent Style UI
```

### Style Analysis Dimensions

```
7 Dimensions of Visual Style:

1. 🎨 Color
   ├── Primary colors
   ├── Color scheme
   └── Color mood

2. 🔤 Typography
   ├── Font families
   ├── Weight distribution
   └── Typographic style

3. 📐 Shape
   ├── Border radius
   ├── Geometric features
   └── Icon style

4. 📏 Spacing
   ├── Density feel
   ├── Whitespace ratio
   └── Grid system

5. ✨ Effects
   ├── Shadow style
   ├── Blur effects
   └── Border treatment

6. 🖼️ Imagery
   ├── Photography style
   ├── Illustration style
   └── Icon style

7. 🎭 Overall Mood
   ├── Modern/Classic
   ├── Minimal/Rich
   └── Professional/Playful
```

### Style Extraction Report Template

```markdown
# Style Extraction Report

## 📷 Reference Image
[Image description or link]

## 🎨 Overall Style Positioning

| Dimension | Analysis Result |
|-----------|-----------------|
| Style Type | [Minimal/Glassmorphism/Neumorphism/...] |
| Mood | [Professional/Playful/Elegant/Tech/...] |
| Target Audience | [Young/Business/...] |

## Extraction Results

### Colors
[Detailed color analysis]

### Typography
[Detailed typography analysis]

### Shape
[Detailed shape analysis]

### Effects
[Detailed effects analysis]

## Output Tokens
[Design Token JSON]

## Figma Styles
[Figma style settings]
```

---

## Color Analysis

### Color Extraction Methods

```
1. Primary Color Identification
   ├── Brand/Accent color
   ├── Largest color proportion
   └── Visual focal color

2. Color Scheme Determination
   ├── Monochromatic
   ├── Analogous
   ├── Complementary
   ├── Triadic
   └── Split-Complementary

3. Color Role Assignment
   ├── Primary: Main brand color
   ├── Secondary: Supporting color
   ├── Accent: Emphasis color
   ├── Background: Background color
   ├── Surface: Surface color
   └── Text: Text color
```

### Color Mood Mapping

```
Cool Tones:
├── Blue family: Professional, Trust, Tech
├── Green family: Natural, Health, Growth
└── Purple family: Creative, Luxury, Mystery

Warm Tones:
├── Red family: Passion, Urgency, Energy
├── Orange family: Vitality, Friendly, Innovation
└── Yellow family: Optimism, Warning, Warmth

Neutral Tones:
├── Black/White/Gray: Professional, Minimal, Modern
├── Beige family: Warm, Natural, Comfortable
└── Brown family: Stable, Traditional, Reliable
```

### Color Extraction Output

```json
{
  "colors": {
    "extracted": {
      "primary": {
        "value": "#6366F1",
        "hsl": "239, 84%, 67%",
        "name": "Indigo",
        "usage": "Main interactive elements, brand identity"
      },
      "secondary": {
        "value": "#EC4899",
        "hsl": "330, 81%, 60%",
        "name": "Pink",
        "usage": "Secondary emphasis, tags"
      },
      "background": {
        "value": "#0F172A",
        "hsl": "222, 47%, 11%",
        "name": "Slate 900",
        "usage": "Dark background"
      },
      "surface": {
        "value": "#1E293B",
        "hsl": "217, 33%, 17%",
        "name": "Slate 800",
        "usage": "Cards, containers"
      },
      "text": {
        "primary": "#F8FAFC",
        "secondary": "#94A3B8",
        "tertiary": "#64748B"
      }
    },
    "palette": {
      "type": "Complementary",
      "harmony": "Blue-purple + Pink contrast"
    },
    "mood": "Modern tech, professional, vibrant"
  }
}
```

### Color Proportion Analysis

```
60-30-10 Rule:

┌─────────────────────────────────────┐
│                                     │
│         60% Primary Background      │
│         (Background/Surface)        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│         30% Secondary Color         │
│         (Secondary/Containers)      │
│                                     │
├─────────────────────────────────────┤
│         10% Accent (Primary/Accent) │
└─────────────────────────────────────┘
```

---

## Typography Analysis

### Font Identification Methods

```
1. Font Category Determination
   ├── Sans-serif: Modern, Clean
   ├── Serif: Classic, Elegant
   ├── Monospace: Technical, Code
   ├── Display: Headlines, Special
   └── Handwriting: Friendly, Creative

2. Font Characteristics
   ├── x-height
   ├── Stroke contrast
   ├── Aperture openness
   ├── Terminal shapes
   └── Geometric vs Humanist

3. Common Font Matching
   [Image font] → [Suggested alternative]
```

### Common Font Style Reference

```
Modern Geometric:
├── Geometric Sans → Inter, Poppins, Montserrat
├── Features: Circular bowls, uniform strokes
└── Use for: Tech, modern brands

Humanist Style:
├── Humanist Sans → Open Sans, Lato, Source Sans
├── Features: Calligraphic feel, stroke variation
└── Use for: Friendly, readable content

Neo-Grotesque:
├── Neo-Grotesque → Helvetica, SF Pro, Roboto
├── Features: Neutral, functional
└── Use for: System interfaces, professional

Elegant Serif:
├── Modern Serif → Playfair, Didot, Bodoni
├── Features: High contrast, refined
└── Use for: Fashion, luxury

Classic Serif:
├── Traditional Serif → Georgia, Merriweather
├── Features: Readable, warm
└── Use for: Editorial, reading content
```

### Typography Style Output

```json
{
  "typography": {
    "fontFamily": {
      "heading": {
        "name": "Poppins",
        "fallback": "sans-serif",
        "style": "Geometric Sans",
        "weights": [600, 700]
      },
      "body": {
        "name": "Inter",
        "fallback": "sans-serif",
        "style": "Neo-Grotesque",
        "weights": [400, 500, 600]
      },
      "mono": {
        "name": "JetBrains Mono",
        "fallback": "monospace",
        "weights": [400, 500]
      }
    },
    "scale": {
      "ratio": 1.25,
      "baseSize": "16px",
      "sizes": {
        "xs": "12px",
        "sm": "14px",
        "base": "16px",
        "lg": "20px",
        "xl": "25px",
        "2xl": "31px",
        "3xl": "39px",
        "4xl": "49px"
      }
    },
    "style": {
      "letterSpacing": {
        "tight": "-0.025em",
        "normal": "0",
        "wide": "0.025em"
      },
      "lineHeight": {
        "heading": 1.2,
        "body": 1.6
      }
    }
  }
}
```

---

## Shape and Layout

### Border Radius Style Analysis

```
Border Radius Levels:

No radius (0px)
├── Style: Sharp, professional, technical
└── Use for: Data dashboards, enterprise software

Small radius (4-8px)
├── Style: Refined, modern, professional
└── Use for: SaaS, business applications

Medium radius (12-16px)
├── Style: Friendly, soft, balanced
└── Use for: Consumer apps, general purpose

Large radius (20-24px)
├── Style: Playful, modern, iOS-style
└── Use for: Social, entertainment apps

Full radius (9999px / Pill)
├── Style: Rounded, cute, button-like
└── Use for: Tags, chips, buttons
```

### Layout Density Analysis

```
Density Levels:

Compact:
├── Spacing: Mainly 4-8px
├── Dense elements
├── High information density
└── Use for: Data tables, professional tools

Default:
├── Spacing: Mainly 12-16px
├── Balanced whitespace
├── Comfortable reading
└── Use for: General applications

Comfortable:
├── Spacing: Mainly 24-32px
├── Generous whitespace
├── Content focused
└── Use for: Marketing pages, reading apps
```

### Shape Output

```json
{
  "shape": {
    "borderRadius": {
      "none": "0px",
      "sm": "4px",
      "md": "8px",
      "lg": "12px",
      "xl": "16px",
      "2xl": "24px",
      "full": "9999px"
    },
    "components": {
      "button": "8px",
      "card": "16px",
      "modal": "24px",
      "input": "8px",
      "chip": "9999px",
      "avatar": "9999px"
    },
    "density": "default",
    "style": "rounded-modern"
  }
}
```

---

## Effects and Textures

### Shadow Style Analysis

```
Shadow Types:

No shadow (Flat):
├── Style: Flat, modern
└── CSS: none

Subtle shadow:
├── Style: Refined, floating feel
└── CSS: 0 1px 3px rgba(0,0,0,0.1)

Default shadow:
├── Style: Layered, card-like
└── CSS: 0 4px 6px rgba(0,0,0,0.1)

Elevated shadow:
├── Style: Strong layering, popups
└── CSS: 0 10px 25px rgba(0,0,0,0.15)

Colored shadow:
├── Style: Trendy, neon
└── CSS: 0 4px 14px rgba(99,102,241,0.4)
```

### Special Effect Styles

```
Glassmorphism:
├── Features: Semi-transparent, blurred background
├── CSS:
│   background: rgba(255,255,255,0.1)
│   backdrop-filter: blur(10px)
│   border: 1px solid rgba(255,255,255,0.2)
└── Use for: Modern, tech-feel UI

Neumorphism:
├── Features: Raised/recessed, soft shadows
├── CSS:
│   background: #e0e0e0
│   box-shadow: 20px 20px 60px #bebebe,
│               -20px -20px 60px #ffffff
└── Use for: Minimal, premium feel

Gradient:
├── Features: Color transitions, richness
├── Types: Linear/Radial/Conic
└── Use for: Backgrounds, buttons, decorations

Grain/Noise:
├── Features: Retro, textured
└── Use for: Backgrounds, illustration style
```

### Effects Output

```json
{
  "effects": {
    "shadow": {
      "style": "subtle",
      "values": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.1)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.15)",
        "colored": "0 4px 14px rgba(99,102,241,0.4)"
      }
    },
    "blur": {
      "backdrop": "blur(10px)",
      "background": "blur(40px)"
    },
    "border": {
      "width": "1px",
      "style": "solid",
      "color": "rgba(255,255,255,0.1)"
    },
    "special": {
      "type": "glassmorphism",
      "settings": {
        "background": "rgba(255,255,255,0.1)",
        "backdropFilter": "blur(10px)",
        "border": "1px solid rgba(255,255,255,0.2)"
      }
    }
  }
}
```

---

## Style Token Generation

### Complete Style Token Structure

```json
{
  "styleExtraction": {
    "meta": {
      "source": "reference-image.png",
      "extractedAt": "2024-01-15",
      "version": "1.0"
    },

    "colors": {
      "primary": "#6366F1",
      "secondary": "#EC4899",
      "background": "#0F172A",
      "surface": "#1E293B",
      "text": {
        "primary": "#F8FAFC",
        "secondary": "#94A3B8"
      },
      "accent": "#22D3EE",
      "success": "#22C55E",
      "warning": "#F59E0B",
      "error": "#EF4444"
    },

    "typography": {
      "fontFamily": {
        "heading": "Poppins, sans-serif",
        "body": "Inter, sans-serif"
      },
      "fontSize": {
        "xs": "12px",
        "sm": "14px",
        "base": "16px",
        "lg": "20px",
        "xl": "24px",
        "2xl": "32px",
        "3xl": "40px"
      },
      "fontWeight": {
        "normal": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700
      },
      "lineHeight": {
        "tight": 1.2,
        "normal": 1.5,
        "relaxed": 1.75
      }
    },

    "spacing": {
      "unit": "4px",
      "scale": [0, 4, 8, 12, 16, 24, 32, 48, 64, 96],
      "density": "default"
    },

    "shape": {
      "borderRadius": {
        "none": "0px",
        "sm": "4px",
        "md": "8px",
        "lg": "16px",
        "xl": "24px",
        "full": "9999px"
      }
    },

    "effects": {
      "shadow": {
        "sm": "0 1px 2px rgba(0,0,0,0.1)",
        "md": "0 4px 6px rgba(0,0,0,0.1)",
        "lg": "0 10px 25px rgba(0,0,0,0.15)"
      },
      "blur": "10px",
      "opacity": {
        "muted": 0.6,
        "disabled": 0.4
      }
    },

    "animation": {
      "duration": {
        "fast": "150ms",
        "normal": "250ms",
        "slow": "400ms"
      },
      "easing": "cubic-bezier(0.4, 0, 0.2, 1)"
    }
  }
}
```

### CSS Variables Output

```css
:root {
  /* Colors */
  --color-primary: #6366F1;
  --color-secondary: #EC4899;
  --color-background: #0F172A;
  --color-surface: #1E293B;
  --color-text-primary: #F8FAFC;
  --color-text-secondary: #94A3B8;

  /* Typography */
  --font-heading: 'Poppins', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-size-base: 16px;
  --line-height-normal: 1.5;

  /* Spacing */
  --spacing-unit: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* Shape */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Effects */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);

  /* Animation */
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Figma Style Output

### Figma Style Settings

```
📁 Styles
├── 🎨 Colors
│   ├── Primary / Default
│   ├── Primary / Hover
│   ├── Primary / Active
│   ├── Secondary / Default
│   ├── Background / Primary
│   ├── Background / Secondary
│   ├── Surface / Default
│   ├── Surface / Elevated
│   ├── Text / Primary
│   ├── Text / Secondary
│   ├── Text / Muted
│   ├── Border / Default
│   └── Border / Focus
│
├── 🔤 Typography
│   ├── Heading / H1
│   ├── Heading / H2
│   ├── Heading / H3
│   ├── Body / Large
│   ├── Body / Default
│   ├── Body / Small
│   ├── Label / Large
│   ├── Label / Default
│   └── Caption
│
└── ✨ Effects
    ├── Shadow / Small
    ├── Shadow / Medium
    ├── Shadow / Large
    ├── Blur / Background
    └── Blur / Overlay
```

### Figma Variables Settings

```
📁 Variables
├── 📦 Primitives
│   ├── Colors
│   │   ├── indigo/50 - indigo/900
│   │   ├── pink/50 - pink/900
│   │   ├── slate/50 - slate/900
│   │   └── ...
│   ├── Spacing
│   │   ├── 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16
│   │   └── ...
│   └── Radius
│       ├── none, sm, md, lg, xl, full
│       └── ...
│
└── 📦 Semantic
    ├── Colors
    │   ├── bg/primary → {slate/900}
    │   ├── bg/secondary → {slate/800}
    │   ├── text/primary → {slate/50}
    │   ├── text/secondary → {slate/400}
    │   ├── interactive/primary → {indigo/500}
    │   └── ...
    └── Spacing
        ├── page/padding → {spacing/4}
        ├── card/padding → {spacing/4}
        └── ...
```

### Component Style Application Example

```
Button Component (applying extracted style):

┌─────────────────────────────────────────┐
│           Primary Button                │
└─────────────────────────────────────────┘

Auto Layout:
├── Padding: var(--spacing-sm) var(--spacing-md)
├── Gap: var(--spacing-sm)
└── Alignment: Center

Fill:
├── Default: var(--color-primary)
├── Hover: var(--color-primary-hover)
└── Active: var(--color-primary-active)

Corner Radius: var(--radius-md)

Typography:
├── Font: var(--font-body)
├── Size: var(--font-size-sm)
├── Weight: var(--font-weight-semibold)
└── Color: var(--color-text-on-primary)

Effects:
└── Shadow: var(--shadow-sm)
```

---

## Style Application Examples

### Reference Image Analysis

```markdown
## Reference Image Analysis

### Image Description
Dark theme tech dashboard interface using purple-blue gradient as accent color.

### Extraction Results

**Colors:**
- Primary: Indigo-purple (#6366F1 → #8B5CF6 gradient)
- Background: Deep blue-gray (#0F172A)
- Surface: Dark gray (#1E293B)
- Text: Light gray-white (#F1F5F9)
- Accent: Cyan (#22D3EE)

**Typography:**
- Headings: Geometric Sans (like Poppins)
- Body: Neo-Grotesque (like Inter)
- Data: Monospace (like JetBrains Mono)

**Shape:**
- Border radius: Medium (12-16px)
- Cards: Large radius (24px)
- Buttons: Full radius (Pill)

**Effects:**
- Style: Glassmorphism
- Shadows: Colored shadows (purple glow)
- Borders: Semi-transparent white

**Layout:**
- Density: Default
- Grid: 12 columns
- Spacing: Mainly 16-24px
```

### Generating Consistent Style UI Components

```
Components generated from extracted style:

┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Dashboard Card                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  background: rgba(30, 41, 59, 0.8)          │ │  │
│  │  │  backdrop-filter: blur(10px)                │ │  │
│  │  │  border: 1px solid rgba(255,255,255,0.1)    │ │  │
│  │  │  border-radius: 24px                        │ │  │
│  │  │  padding: 24px                              │ │  │
│  │  │                                             │ │  │
│  │  │  📊 Total Revenue                           │ │  │
│  │  │  $45,231.89                                 │ │  │
│  │  │  +20.1% from last month                     │ │  │
│  │  │                                             │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Primary Btn    │  │  Secondary Btn  │              │
│  │  bg: gradient   │  │  bg: transparent│              │
│  │  radius: full   │  │  border: 1px    │              │
│  │  shadow: glow   │  │  radius: full   │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Complete Page Style Application

```
Complete page with extracted style applied:

┌─────────────────────────────────────────────────────────┐
│ 🔮 Background: #0F172A (dark)                           │
│                                                         │
│ ┌─ Sidebar ──┐ ┌─ Main Content ────────────────────┐   │
│ │            │ │                                    │   │
│ │ Glass Card │ │  Header (Glass)                    │   │
│ │ Semi-trans │ │  ┌────────────────────────────┐   │   │
│ │ background │ │  │  Welcome back, User        │   │   │
│ │ Blur       │ │  │  Here's your dashboard     │   │   │
│ │ effect     │ │  └────────────────────────────┘   │   │
│ │            │ │                                    │   │
│ │ 🏠 Home    │ │  ┌──────────┐ ┌──────────┐        │   │
│ │ 📊 Stats   │ │  │ Card 1   │ │ Card 2   │        │   │
│ │ ⚙️ Settings│ │  │ Glass    │ │ Glass    │        │   │
│ │            │ │  │ + Glow   │ │ + Glow   │        │   │
│ │            │ │  └──────────┘ └──────────┘        │   │
│ │            │ │                                    │   │
│ │            │ │  ┌─────────────────────────────┐   │   │
│ │            │ │  │ Chart Area (Glass)          │   │   │
│ │            │ │  │ Gradient line chart         │   │   │
│ │            │ │  └─────────────────────────────┘   │   │
│ └────────────┘ └────────────────────────────────────┘   │
│                                                         │
│ Fonts: Poppins (headings) + Inter (body)                │
│ Accent: Indigo-Purple Gradient                          │
│ Radius: 24px (cards) / Full (buttons)                   │
│ Effects: Glassmorphism + Colored Shadow                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Style Extraction Checklist

### Analysis Completeness

```
Colors (Required)
□ Primary color identified
□ Color scheme determined
□ Background/surface colors
□ Text color scale
□ Accent/secondary colors
□ Semantic colors (success/warning/error)

Typography (Required)
□ Font families identified
□ Weight distribution
□ Font size scale
□ Line height settings
□ Letter spacing recommendations

Shape (Required)
□ Border radius levels
□ Component radius mapping
□ Density/spacing

Effects (Recommended)
□ Shadow style
□ Special effects (Glass/Neumorphism)
□ Border treatment
□ Animation style

Output (Required)
□ Token JSON
□ CSS Variables
□ Figma Styles
□ Figma Variables
□ Component examples
```
