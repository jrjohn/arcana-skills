# Design System Building Guide

This document provides a complete methodology for building scalable design systems, applicable to App and Web projects.

> **本專案實例(Arcana dashboard)**:本檔是**泛用方法論**;實際 token 值定義在 app 的 `dashboard/src/app/shared/styles/_tokens.scss`(`:root` CSS 變數,疊在 Bootstrap `--bs-*` 上)。實作**一律 `var(--…)`,禁止裸 hex/px**。版面怎麼用這些 token(欄數、原型、漸進揭露)見 **`layout-workspace-patterns.md`**。

## Table of Contents
1. [Design System Overview](#design-system-overview)
2. [Design Tokens](#design-tokens)
3. [Component Architecture](#component-architecture)
4. [Documentation and Specifications](#documentation-and-specifications)
5. [Design and Development Collaboration](#design-and-development-collaboration)
6. [Maintenance and Evolution](#maintenance-and-evolution)

---

## Design System Overview

### What is a Design System?

A design system is a complete set of design standards, component libraries, and guiding principles that ensure consistency in visual appearance and user experience across products.

### Core Components

```
Design System
├── Design Tokens
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   ├── Shadows
│   └── Border Radius
│
├── Components
│   ├── Atoms
│   ├── Molecules
│   ├── Organisms
│   └── Templates
│
├── Patterns
│   ├── Navigation
│   ├── Forms
│   ├── Data Display
│   └── Feedback
│
└── Guidelines
    ├── Brand
    ├── Voice & Tone
    ├── Accessibility
    └── Motion
```

### Design System Benefits

| Aspect | Benefit |
|--------|---------|
| Consistency | Unified visual language and user experience |
| Efficiency | Reduce repetitive design and development work |
| Scalability | Easy to add components and maintain |
| Collaboration | Common language for designers and engineers |
| Quality | Built-in best practices and accessibility considerations |

---

## Design Tokens

### What are Design Tokens?

Design Tokens are the smallest units of design decisions, used to store visual design properties.

### Token Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Semantic Tokens                       │
│  (Semantic layer: primary-color, text-body, spacing-page)│
├─────────────────────────────────────────────────────────┤
│                    Alias Tokens                          │
│  (Alias layer: blue-500, gray-900, size-16)             │
├─────────────────────────────────────────────────────────┤
│                    Primitive Tokens                      │
│  (Primitive layer: #3B82F6, 16px, 400)                  │
└─────────────────────────────────────────────────────────┘
```

### Color Tokens

```json
{
  "color": {
    "primitive": {
      "blue": {
        "50": "#EFF6FF",
        "100": "#DBEAFE",
        "200": "#BFDBFE",
        "300": "#93C5FD",
        "400": "#60A5FA",
        "500": "#3B82F6",
        "600": "#2563EB",
        "700": "#1D4ED8",
        "800": "#1E40AF",
        "900": "#1E3A8A"
      },
      "gray": {
        "50": "#F9FAFB",
        "100": "#F3F4F6",
        "200": "#E5E7EB",
        "300": "#D1D5DB",
        "400": "#9CA3AF",
        "500": "#6B7280",
        "600": "#4B5563",
        "700": "#374151",
        "800": "#1F2937",
        "900": "#111827"
      }
    },
    "semantic": {
      "primary": "{color.primitive.blue.500}",
      "primary-hover": "{color.primitive.blue.600}",
      "primary-active": "{color.primitive.blue.700}",
      "text-primary": "{color.primitive.gray.900}",
      "text-secondary": "{color.primitive.gray.600}",
      "text-disabled": "{color.primitive.gray.400}",
      "background-primary": "#FFFFFF",
      "background-secondary": "{color.primitive.gray.50}",
      "border-default": "{color.primitive.gray.200}",
      "success": "#22C55E",
      "warning": "#F59E0B",
      "error": "#EF4444",
      "info": "#3B82F6"
    }
  }
}
```

### Typography Tokens

```json
{
  "typography": {
    "fontFamily": {
      "sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      "mono": "'SF Mono', 'Fira Code', Consolas, monospace"
    },
    "fontSize": {
      "xs": "12px",
      "sm": "14px",
      "base": "16px",
      "lg": "18px",
      "xl": "20px",
      "2xl": "24px",
      "3xl": "30px",
      "4xl": "36px",
      "5xl": "48px"
    },
    "fontWeight": {
      "normal": "400",
      "medium": "500",
      "semibold": "600",
      "bold": "700"
    },
    "lineHeight": {
      "tight": "1.25",
      "normal": "1.5",
      "relaxed": "1.75"
    },
    "semantic": {
      "heading-1": {
        "fontSize": "{typography.fontSize.4xl}",
        "fontWeight": "{typography.fontWeight.bold}",
        "lineHeight": "{typography.lineHeight.tight}"
      },
      "heading-2": {
        "fontSize": "{typography.fontSize.3xl}",
        "fontWeight": "{typography.fontWeight.bold}",
        "lineHeight": "{typography.lineHeight.tight}"
      },
      "body": {
        "fontSize": "{typography.fontSize.base}",
        "fontWeight": "{typography.fontWeight.normal}",
        "lineHeight": "{typography.lineHeight.normal}"
      },
      "caption": {
        "fontSize": "{typography.fontSize.sm}",
        "fontWeight": "{typography.fontWeight.normal}",
        "lineHeight": "{typography.lineHeight.normal}"
      }
    }
  }
}
```

### Spacing Tokens

```json
{
  "spacing": {
    "0": "0",
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
    "16": "64px",
    "20": "80px",
    "24": "96px"
  },
  "semantic": {
    "page-padding": "{spacing.4}",
    "section-gap": "{spacing.8}",
    "component-gap": "{spacing.4}",
    "element-gap": "{spacing.2}"
  }
}
```

### Other Tokens

```json
{
  "borderRadius": {
    "none": "0",
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "full": "9999px"
  },
  "shadow": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.15)"
  },
  "duration": {
    "fast": "150ms",
    "normal": "250ms",
    "slow": "400ms"
  },
  "easing": {
    "easeInOut": "cubic-bezier(0.4, 0, 0.2, 1)",
    "easeOut": "cubic-bezier(0, 0, 0.2, 1)",
    "easeIn": "cubic-bezier(0.4, 0, 1, 1)"
  }
}
```

### Token Transformation Tools

| Tool | Description |
|------|-------------|
| Style Dictionary | Amazon open source, industry standard |
| Tokens Studio | Figma plugin, supports export |
| Theo | Salesforce open source |
| Diez | Cross-platform token tool |

---

## Component Architecture

### Atomic Design Methodology

```
┌──────────────────────────────────────────────────────────┐
│ Pages                                                    │
│   Complete pages, templates filled with real content     │
├──────────────────────────────────────────────────────────┤
│ Templates                                                │
│   Page structure, defining content area layouts          │
├──────────────────────────────────────────────────────────┤
│ Organisms                                                │
│   Complex components: Header, Footer, Card Grid, Form    │
├──────────────────────────────────────────────────────────┤
│ Molecules                                                │
│   Combined components: Search Bar, Nav Item, Form Field  │
├──────────────────────────────────────────────────────────┤
│ Atoms                                                    │
│   Basic components: Button, Input, Label, Icon           │
└──────────────────────────────────────────────────────────┘
```

### Component Design Principles

1. **Single Responsibility**: Each component does one thing
2. **Composability**: Small components compose larger ones
3. **Customizability**: Adjust via Props/Variants
4. **Accessibility**: Built-in a11y support
5. **Well Documented**: Includes usage instructions and examples

### Component Specification Document Example

```markdown
# Button

## Overview
Buttons are used to trigger actions or submit forms.

## Variants
- Primary: Main action
- Secondary: Secondary action
- Outline: Auxiliary action
- Ghost: Subtle action
- Danger: Destructive action

## Sizes
- Small: 32px height
- Medium: 40px height (default)
- Large: 48px height

## States
- Default
- Hover
- Focus
- Active
- Disabled
- Loading

## Props
| Name | Type | Default | Description |
|------|------|---------|-------------|
| variant | string | 'primary' | Button variant |
| size | string | 'medium' | Button size |
| disabled | boolean | false | Whether disabled |
| loading | boolean | false | Whether loading |
| leftIcon | ReactNode | - | Left icon |
| rightIcon | ReactNode | - | Right icon |

## Usage Examples
[Code examples]

## Accessibility Considerations
- Use `<button>` element
- Provide clear focus state
- Set aria-disabled when disabled
```

### Component Library Tools

| Tool | Platform | Description |
|------|----------|-------------|
| Storybook | Web | Industry standard component documentation tool |
| Figma | Design | Design component library |
| SwiftUI | iOS | Native components |
| Jetpack Compose | Android | Native components |
| React Native | Cross-platform | Shared component library |

---

## Documentation and Specifications

### Design System Documentation Structure

```
design-system-docs/
├── getting-started/
│   ├── introduction.md
│   ├── installation.md
│   └── usage.md
│
├── foundations/
│   ├── colors.md
│   ├── typography.md
│   ├── spacing.md
│   ├── icons.md
│   └── motion.md
│
├── components/
│   ├── buttons.md
│   ├── inputs.md
│   ├── cards.md
│   ├── modals.md
│   └── ...
│
├── patterns/
│   ├── forms.md
│   ├── navigation.md
│   ├── data-tables.md
│   └── empty-states.md
│
└── guidelines/
    ├── accessibility.md
    ├── responsive.md
    └── localization.md
```

### Component Documentation Template

```markdown
# [Component Name]

## Purpose
Describe use cases for this component.

## Design Specifications
- Size
- Colors
- Spacing
- States

## Interaction Behavior
Describe various interaction states and animations.

## Variants
List all variants and when to use them.

## Best Practices
✅ Do: Correct usage
❌ Don't: Incorrect usage

## Accessibility
- Keyboard operation
- Screen reader
- Color contrast

## Related Components
Links to related components.
```

---

## Design and Development Collaboration

### Design Handoff Process

```
Design → Design Tokens → Component Development → Quality Acceptance
   ↓           ↓              ↓                      ↓
 Figma    Style Dictionary  Storybook         Visual Regression Testing
```

### Figma Collaboration Standards

**File structure:**
```
📁 Design System
├── 📄 🎨 Foundations
│   ├── Colors
│   ├── Typography
│   └── Icons
│
├── 📄 🧱 Components
│   ├── Buttons
│   ├── Inputs
│   └── Cards
│
├── 📄 📐 Patterns
│   ├── Forms
│   └── Navigation
│
└── 📄 📱 Templates
    ├── Mobile
    └── Desktop
```

**Naming conventions:**
```
Components: ComponentName/Variant/State
Example: Button/Primary/Hover

Layers: element-name
Example: icon-left, label, container

Frame: Use Auto Layout
```

### Design to Code Sync

**Token sync flow:**
```
Figma Tokens Studio
        ↓
    tokens.json
        ↓
   Style Dictionary
        ↓
┌───────┬────────┬─────────┐
│  CSS  │  iOS   │ Android │
│ vars  │ Swift  │ Kotlin  │
└───────┴────────┴─────────┘
```

### Version Control

**Semantic versioning:**
```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes
MINOR: New features (backward compatible)
PATCH: Bug fixes

Example: 2.1.0 → 2.1.1 (fix) → 2.2.0 (new feature) → 3.0.0 (breaking)
```

**Changelog:**
```markdown
# Changelog

## [2.2.0] - 2024-01-15
### Added
- Added Tooltip component
- Button now supports loading state

### Changed
- Updated primary color palette

### Fixed
- Fixed Input alignment issue in Safari
```

---

## Maintenance and Evolution

### Component Lifecycle

```
Proposal → Design → Development → Testing → Release → Maintenance → Deprecation
   ↓         ↓         ↓           ↓         ↓          ↓            ↓
  RFC      Figma      Code         QA      Release    Iterate    Deprecated
```

### New Component Process

1. **Proposal**: Submit RFC describing requirements
2. **Review**: Design system team evaluation
3. **Design**: Create component in Figma
4. **Development**: Implement code
5. **Testing**: Visual regression, accessibility testing
6. **Documentation**: Write usage instructions
7. **Release**: Include in version release

### Deprecation Strategy

```markdown
## Deprecation Notice

### Deprecated Component: OldButton
- Deprecated version: v2.5.0
- Removal version: v3.0.0
- Alternative: Use new Button component

### Migration Guide
[Provide migration steps]
```

### Design System Maturity Model

| Level | Characteristics |
|-------|-----------------|
| Level 1: Starting | Basic color and typography standards |
| Level 2: Growing | Component library and basic documentation |
| Level 3: Mature | Design Tokens, version control, CI/CD |
| Level 4: Scaling | Cross-team adoption, contribution process, governance |

### Metrics

| Metric | Description |
|--------|-------------|
| Adoption Rate | Percentage of projects using design system |
| Component Coverage | Design system components vs custom components |
| Contributions | Number of components contributed by teams |
| Issues Reported | Bug count and resolution time |
| Satisfaction | Designer/developer satisfaction surveys |

---

## Useful Resources

### Design System Examples

| Name | Company | Link |
|------|---------|------|
| Material Design | Google | material.io |
| Human Interface | Apple | developer.apple.com/design |
| Carbon | IBM | carbondesignsystem.com |
| Polaris | Shopify | polaris.shopify.com |
| Spectrum | Adobe | spectrum.adobe.com |
| Fluent | Microsoft | fluent2.microsoft.design |
| Lightning | Salesforce | lightningdesignsystem.com |
| Atlassian | Atlassian | atlassian.design |

### Tool List

| Category | Tools |
|----------|-------|
| Design | Figma, Sketch, Adobe XD |
| Token Management | Tokens Studio, Style Dictionary |
| Component Documentation | Storybook, Docusaurus, Zeroheight |
| Visual Testing | Chromatic, Percy, BackstopJS |
| Accessibility Testing | axe, WAVE, Lighthouse |
