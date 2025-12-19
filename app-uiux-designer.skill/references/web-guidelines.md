# Web UI/UX Design Guide

This document provides core specifications for Web application design, covering responsive design, component specifications, layout systems, and more.

## Table of Contents
1. [Design Principles](#design-principles)
2. [Responsive Design](#responsive-design)
3. [Layout System](#layout-system)
4. [Navigation Patterns](#navigation-patterns)
5. [Component Specifications](#component-specifications)
6. [Typography System](#typography-system)
7. [Color System](#color-system)
8. [Form Design](#form-design)
9. [Data Tables](#data-tables)
10. [Animation and Interaction](#animation-and-interaction)

---

## Design Principles

### Web Design Core Philosophy

1. **Mobile First**
   - Design from smallest screen first
   - Progressively enhance for larger screens

2. **Progressive Enhancement**
   - Basic functionality works in all browsers
   - Advanced features enabled based on browser capabilities

3. **Content First**
   - Content determines design
   - Reduce unnecessary decoration

4. **Performance**
   - Fast loading times
   - Optimize images and resources

5. **Accessibility**
   - Usable by everyone
   - Comply with WCAG standards

---

## Responsive Design

### Breakpoint System

```css
/* Standard breakpoints */
--breakpoint-xs: 0;        /* < 576px: Mobile portrait */
--breakpoint-sm: 576px;    /* ≥ 576px: Mobile landscape */
--breakpoint-md: 768px;    /* ≥ 768px: Tablet */
--breakpoint-lg: 1024px;   /* ≥ 1024px: Small desktop */
--breakpoint-xl: 1280px;   /* ≥ 1280px: Desktop */
--breakpoint-2xl: 1536px;  /* ≥ 1536px: Large desktop */
```

### Common Design Sizes

| Device | Width | Design Recommendation |
|--------|-------|----------------------|
| Mobile S | 320px | Minimum supported width |
| Mobile M | 375px | iPhone standard |
| Mobile L | 425px | Large phones |
| Tablet | 768px | iPad portrait |
| Laptop | 1024px | Small laptop |
| Desktop | 1440px | Standard desktop |
| 4K | 2560px | Large monitors |

### Design Strategies

**Fluid Layout:**
```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

@media (min-width: 768px) {
  .container {
    padding: 0 24px;
  }
}

@media (min-width: 1024px) {
  .container {
    padding: 0 32px;
  }
}
```

**Content Adaptation Strategy:**
```
Mobile: Single column layout, stacked content
Tablet: Two column layout, collapsible sidebar
Desktop: Multi-column layout, fixed sidebar
```

---

## Layout System

### Grid System

**12-Column Grid:**
```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px; /* Gutter */
}

/* Responsive columns */
.col-12 { grid-column: span 12; }  /* Full width */
.col-6 { grid-column: span 6; }    /* Half width */
.col-4 { grid-column: span 4; }    /* 1/3 width */
.col-3 { grid-column: span 3; }    /* 1/4 width */
```

### Spacing Scale

```css
/* 8px base unit */
--space-1: 4px;    /* 0.5x */
--space-2: 8px;    /* 1x */
--space-3: 12px;   /* 1.5x */
--space-4: 16px;   /* 2x */
--space-5: 24px;   /* 3x */
--space-6: 32px;   /* 4x */
--space-7: 48px;   /* 6x */
--space-8: 64px;   /* 8x */
--space-9: 96px;   /* 12x */
--space-10: 128px; /* 16x */
```

### Common Layout Patterns

**Holy Grail Layout:**
```
┌─────────────────────────────────────┐
│              Header                 │
├────────┬─────────────────┬──────────┤
│        │                 │          │
│  Nav   │     Main        │  Aside   │
│        │                 │          │
├────────┴─────────────────┴──────────┤
│              Footer                 │
└─────────────────────────────────────┘
```

**Dashboard Layout:**
```
┌──────┬──────────────────────────────┐
│      │           Topbar             │
│      ├──────────────────────────────┤
│ Side │                              │
│ bar  │         Content              │
│      │                              │
└──────┴──────────────────────────────┘
```

**Card Grid Layout:**
```
┌─────────┬─────────┬─────────┐
│  Card   │  Card   │  Card   │
├─────────┼─────────┼─────────┤
│  Card   │  Card   │  Card   │
└─────────┴─────────┴─────────┘
```

---

## Navigation Patterns

### Top Navigation Bar

```
Desktop:
┌─────────────────────────────────────────────────┐
│ Logo    Nav1  Nav2  Nav3  Nav4     Search  User │
└─────────────────────────────────────────────────┘
Height: 64px (desktop) / 56px (tablet) / 48px (mobile)

Mobile:
┌─────────────────────────────────────────────────┐
│ ☰ Hamburger        Logo               Search 🔍 │
└─────────────────────────────────────────────────┘
```

### Side Navigation

```
Expanded state (width: 240-280px):
┌────────────────────┐
│ Logo               │
├────────────────────┤
│ 🏠 Dashboard       │
│ 📊 Analytics       │
│ 👥 Users           │
│ ⚙️ Settings        │
├────────────────────┤
│ 👤 Profile         │
│ 🚪 Logout          │
└────────────────────┘

Collapsed state (width: 64-72px):
┌────┐
│ 🏠 │
│ 📊 │
│ 👥 │
│ ⚙️ │
└────┘
```

### Breadcrumb

```
Home > Category > Subcategory > Current Page
└─────┴──────────┴─────────────┴────────────┘
  Clickable links              Current page (not clickable)
```

### Tab Navigation

```
┌──────────┬──────────┬──────────┬──────────┐
│  Tab 1   │  Tab 2   │  Tab 3   │  Tab 4   │
│ (active) │          │          │          │
├──────────┴──────────┴──────────┴──────────┤
│                                            │
│              Tab Content                   │
│                                            │
└────────────────────────────────────────────┘
```

---

## Component Specifications

### Buttons

**Sizes:**
| Type | Height | Padding | Font Size |
|------|--------|---------|-----------|
| Small | 32px | 12px 16px | 14px |
| Medium | 40px | 10px 20px | 16px |
| Large | 48px | 12px 24px | 18px |

**Types and usage:**
```
Primary: Main action (submit, confirm)
Secondary: Secondary action (cancel, back)
Outline: Auxiliary action (more options)
Ghost: Subtle action (close, skip)
Danger: Destructive action (delete, remove)
```

**States:**
```css
Default: Normal state
Hover: Mouse hover (brightness +10%)
Focus: Keyboard focus (show outline)
Active: Clicking (brightness -10%)
Disabled: Disabled (opacity: 0.5)
Loading: Loading (show spinner)
```

### Cards

```
┌─────────────────────────────────┐
│         Image (optional)        │
├─────────────────────────────────┤
│ Title                           │
│ Subtitle (optional)             │
│                                 │
│ Body content goes here...       │
│                                 │
├─────────────────────────────────┤
│ [Action 1]         [Action 2]   │
└─────────────────────────────────┘

Border radius: 8px - 16px
Shadow: 0 2px 8px rgba(0,0,0,0.1)
Padding: 16px - 24px
```

### Modal / Dialog

```
Background overlay: rgba(0,0,0,0.5)

┌─────────────────────────────────┐
│ Title                       ✕   │ Header
├─────────────────────────────────┤
│                                 │
│         Content Area            │ Body
│                                 │
├─────────────────────────────────┤
│           [Cancel]  [Confirm]   │ Footer
└─────────────────────────────────┘

Width: 400px (small) / 600px (medium) / 800px (large)
Max height: 90vh
```

### Toast / Notification

```
Position: Top right / Bottom right / Top center

┌────────────────────────────────┐
│ ✓ Success message here     ✕   │
└────────────────────────────────┘

Types: Success (green), Error (red), Warning (yellow), Info (blue)
Duration: 3-5 seconds auto dismiss
```

### Tooltip

```
Trigger: Hover / Focus
Delay: 300ms to show / 0ms to hide
Position: Top / Bottom / Left / Right
Max width: 250px

      ┌───────────────────┐
      │ Tooltip content   │
      └─────────┬─────────┘
                ▼
           [Element]
```

### Dropdown Menu

```
┌─────────────────────┐
│ Select option    ▼  │
├─────────────────────┤
│ Option 1            │
│ Option 2 ✓          │ (selected)
│ Option 3            │
│ ─────────────────── │ (divider)
│ Option 4            │
└─────────────────────┘

Max height: 300px (scrollable)
Item height: 36px - 44px
```

---

## Typography System

### Font Stack

```css
/* System fonts */
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI",
             Roboto, "Helvetica Neue", Arial, sans-serif;

/* Monospace fonts */
--font-mono: "SF Mono", "Fira Code", "Consolas", monospace;

/* Chinese fonts */
--font-chinese: "PingFang TC", "Microsoft JhengHei",
                "Noto Sans TC", sans-serif;
```

### Font Size (Type Scale)

```css
--text-xs: 12px;    /* Helper text */
--text-sm: 14px;    /* Secondary content */
--text-base: 16px;  /* Body text */
--text-lg: 18px;    /* Large body */
--text-xl: 20px;    /* H5 */
--text-2xl: 24px;   /* H4 */
--text-3xl: 30px;   /* H3 */
--text-4xl: 36px;   /* H2 */
--text-5xl: 48px;   /* H1 */
--text-6xl: 60px;   /* Display */
```

### Line Height

```css
--leading-tight: 1.25;   /* Headings */
--leading-snug: 1.375;   /* Subheadings */
--leading-normal: 1.5;   /* Body text */
--leading-relaxed: 1.625; /* Large paragraphs */
--leading-loose: 2;      /* Special use */
```

### Font Weight

```css
--font-light: 300;
--font-normal: 400;    /* Body text */
--font-medium: 500;    /* Emphasis */
--font-semibold: 600;  /* Subheadings */
--font-bold: 700;      /* Headings */
```

---

## Color System

### Neutral Colors

```css
--gray-50: #FAFAFA;   /* Background */
--gray-100: #F5F5F5;  /* Secondary background */
--gray-200: #EEEEEE;  /* Borders */
--gray-300: #E0E0E0;  /* Dividers */
--gray-400: #BDBDBD;  /* Placeholder */
--gray-500: #9E9E9E;  /* Disabled text */
--gray-600: #757575;  /* Helper text */
--gray-700: #616161;  /* Secondary text */
--gray-800: #424242;  /* Primary text */
--gray-900: #212121;  /* Heading text */
```

### Semantic Colors

```css
/* Primary color */
--primary-50 to --primary-900

/* Success */
--success: #22C55E;
--success-light: #DCFCE7;

/* Warning */
--warning: #F59E0B;
--warning-light: #FEF3C7;

/* Error */
--error: #EF4444;
--error-light: #FEE2E2;

/* Info */
--info: #3B82F6;
--info-light: #DBEAFE;
```

### Dark Mode

```css
/* Light mode */
--bg-primary: #FFFFFF;
--bg-secondary: #F5F5F5;
--text-primary: #212121;
--text-secondary: #757575;

/* Dark mode */
--bg-primary-dark: #121212;
--bg-secondary-dark: #1E1E1E;
--text-primary-dark: #FFFFFF;
--text-secondary-dark: #A0A0A0;
```

---

## Form Design

### Input Fields

```
┌─ Label ──────────────────────────┐
│                                  │
│ Placeholder text                 │
│                                  │
└──────────────────────────────────┘
  Helper text or error message

Height: 40px (medium) / 48px (large)
Border radius: 4px - 8px
Padding: 12px 16px
```

**States:**
```
Default: Gray border (#E0E0E0)
Hover: Dark gray border (#BDBDBD)
Focus: Primary color border + shadow
Error: Red border + error message
Disabled: Gray background + 50% opacity
```

### Checkbox & Radio

```
☐ Unchecked          ○ Unselected
☑ Checked            ● Selected
☒ Indeterminate
□ Disabled           ○ Disabled

Size: 16px (small) / 20px (medium) / 24px (large)
Label spacing: 8px
```

### Select Dropdown

```
┌──────────────────────────────┐
│ Selected option           ▼  │
└──────────────────────────────┘
```

### Form Layout

```
Vertical stack (recommended):
┌─────────────────────────────┐
│ Label                       │
│ [Input field]               │
│                             │
│ Label                       │
│ [Input field]               │
│                             │
│ [Submit]                    │
└─────────────────────────────┘

Horizontal layout (short forms):
┌─────────────────────────────────────────┐
│ Label    [Input]    Label    [Input]    │
└─────────────────────────────────────────┘
```

---

## Data Tables

### Basic Structure

```
┌────────┬────────────┬──────────┬──────────┐
│ ☐      │ Name       │ Status   │ Actions  │ Header
├────────┼────────────┼──────────┼──────────┤
│ ☐      │ Item 1     │ Active   │ ⋮        │ Row
├────────┼────────────┼──────────┼──────────┤
│ ☑      │ Item 2     │ Inactive │ ⋮        │ Row (selected)
├────────┼────────────┼──────────┼──────────┤
│ ☐      │ Item 3     │ Active   │ ⋮        │ Row
└────────┴────────────┴──────────┴──────────┘
  Showing 1-10 of 100        < 1 2 3 ... 10 >
```

### Specifications

```
Row height: 48px - 56px
Header background: #F5F5F5
Hover background: #FAFAFA
Selected background: Primary color 5%
Border: 1px #E0E0E0
```

### Responsive Tables

**Small screen handling:**
1. Horizontal scrolling
2. Card-style stacking
3. Priority column display

---

## Animation and Interaction

### Timing Curves

```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Duration

```css
--duration-fast: 150ms;    /* Micro-interactions */
--duration-normal: 250ms;  /* Standard transitions */
--duration-slow: 350ms;    /* Complex animations */
```

### Common Animations

```css
/* Fade */
opacity: 0 → 1

/* Slide */
transform: translateY(10px) → translateY(0)

/* Scale */
transform: scale(0.95) → scale(1)

/* Skeleton Loading */
background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
animation: shimmer 1.5s infinite;
```

### Interaction Feedback

```
Button Hover: Background color lightens
Button Active: Background color darkens
Link Hover: Underline or color change
Card Hover: Shadow deepens or slight lift
```

---

## Design Checklist

### Pre-launch Verification

- [ ] Support major browsers (Chrome, Firefox, Safari, Edge)
- [ ] Responsive design (320px - 2560px)
- [ ] Support dark mode
- [ ] Touch-friendly (44x44px minimum touch targets)
- [ ] Keyboard navigation support
- [ ] Screen reader compatible
- [ ] Load time < 3 seconds
- [ ] Image optimization (WebP, lazy loading)
- [ ] Form validation and error handling
- [ ] Basic SEO optimization
