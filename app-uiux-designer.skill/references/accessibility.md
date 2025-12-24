# Accessibility Design Guide

This document provides accessibility design principles and implementation guidelines compliant with WCAG 2.1 standards.

## Table of Contents
1. [Accessibility Overview](#accessibility-overview)
2. [WCAG Principles](#wcag-principles)
3. [Visual Accessibility](#visual-accessibility)
4. [Auditory Accessibility](#auditory-accessibility)
5. [Motor Accessibility](#motor-accessibility)
6. [Cognitive Accessibility](#cognitive-accessibility)
7. [Platform-Specific Guidelines](#platform-specific-guidelines)
8. [Testing and Verification](#testing-and-verification)

---

## Accessibility Overview

### Why is Accessible Design Needed?

```
Approximately 15% of the global population has some form of disability
Accessibility benefits:
├── Permanent disabilities: Visual, hearing, motor impairments
├── Temporary disabilities: Broken arm, eye infection
├── Situational disabilities: Bright sunlight, noisy environment, one-handed use
└── Elderly users: Declining vision, slower movements
```

### Accessibility Benefits

| Aspect | Benefit |
|--------|---------|
| Users | More people can use your product |
| Legal | Comply with accessibility regulations |
| SEO | Improve search engine optimization |
| Quality | Overall user experience improves |
| Brand | Demonstrate social responsibility |

---

## WCAG Principles

### WCAG 2.1 Four Principles (POUR)

```
P - Perceivable
    Information must be perceivable by users

O - Operable
    Interface components must be operable

U - Understandable
    Information and operations must be understandable

R - Robust
    Content must be interpretable by various assistive technologies
```

### Conformance Levels

| Level | Description | Requirements |
|-------|-------------|--------------|
| A | Basic | Minimum threshold |
| AA | Standard | General website/App target |
| AAA | Highest | Specific needs |

---

## Visual Accessibility

### Color Contrast

**WCAG Contrast Requirements:**

| Level | Normal Text | Large Text |
|-------|-------------|------------|
| AA | 4.5:1 | 3:1 |
| AAA | 7:1 | 4.5:1 |

**Large Text Definition:**
```
≥ 18pt (24px) normal weight
≥ 14pt (18.5px) bold
```

**Contrast Examples:**
```
✅ Good: #000000 on #FFFFFF = 21:1
✅ Passes AA: #595959 on #FFFFFF = 7:1
⚠️ Large text only: #757575 on #FFFFFF = 4.48:1
❌ Fails: #AAAAAA on #FFFFFF = 2.32:1
```

**Recommended Tools:**
- WebAIM Contrast Checker
- Stark (Figma plugin)
- Color Contrast Analyzer

### Don't Rely on Color Alone

```
❌ Wrong: Only use red to indicate errors
✅ Correct: Red + icon + text description

❌ Wrong: Links distinguished only by blue color
✅ Correct: Blue + underline

❌ Wrong: Charts distinguished only by color
✅ Correct: Color + patterns/labels
```

### Text Size and Scaling

```
Minimum font size: 16px (body text)
Support 200% zoom without breaking layout
Use relative units: rem, em
Avoid fixed height containers

CSS example:
html { font-size: 100%; }  /* 16px */
body { font-size: 1rem; }
h1 { font-size: 2rem; }    /* 32px */
```

### Focus Indicators

```
❌ Remove: outline: none;
✅ Customize but keep visible:

:focus {
  outline: 2px solid #0066CC;
  outline-offset: 2px;
}

:focus-visible {
  /* Only show during keyboard navigation */
  outline: 2px solid #0066CC;
}
```

### Image Alternative Text

**Alt text principles:**
```
Informational images: Describe content and purpose
  <img alt="Line chart showing sales grew 50% from January to June">

Decorative images: Empty alt or CSS background
  <img alt="" role="presentation">

Functional images: Describe function
  <img alt="Search">

Complex charts: Provide long description
  <img alt="2024 Sales Report" aria-describedby="chart-desc">
  <p id="chart-desc">Detailed description...</p>
```

### Animation Safety

```css
/* Respect user preferences */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}

/* Avoid flashing */
Must not exceed 3 flashes per second
```

---

## Auditory Accessibility

### Video Captions

**Caption Types:**
| Type | Description |
|------|-------------|
| Closed Captions (CC) | Can be toggled, includes sound effect descriptions |
| Open Captions | Always displayed |
| Live Transcription | Generated in real-time |

**Caption Specifications:**
```
Display at once: 1-2 lines
Characters: Maximum 32 per line
Display time: At least 1 second
Sync: Synchronized with audio
Position: Don't obstruct important content
```

### Audio Alternatives

```
Provide:
- Video transcripts
- Audio text versions
- Audio descriptions (for visually impaired)
```

### No Auto-play

```
❌ Auto-play videos with sound
✅ Default muted or user-initiated
✅ Provide pause/stop controls
```

---

## Motor Accessibility

### Keyboard Navigation

**Keyboard-focusable elements:**
```html
<!-- Natively focusable -->
<button>Button</button>
<a href="#">Link</a>
<input type="text">
<select>...</select>
<textarea>...</textarea>

<!-- Custom elements need tabindex -->
<div role="button" tabindex="0">Custom button</div>
```

**Keyboard Operation Standards:**

| Key | Action |
|-----|--------|
| Tab | Move to next element |
| Shift + Tab | Move to previous element |
| Enter / Space | Activate button/link |
| Arrow Keys | Move within groups |
| Escape | Close Modal/Dropdown |
| Home / End | Move to first/last item |

**Focus Order:**
```
Logical order: Left to right, top to bottom
Avoid focus traps
Modal opens: Focus moves into Modal
Modal closes: Focus returns to trigger element
```

### Touch Targets

```
Minimum touch targets:
iOS: 44 × 44 pt
Android: 48 × 48 dp
Web: 44 × 44 px

Spacing: At least 8px between adjacent targets
```

### Gesture Alternatives

```
❌ Only support swipe gestures
✅ Provide button alternatives

❌ Only support pinch to zoom
✅ Provide +/- buttons

❌ Require precise dragging
✅ Provide other input methods
```

### Time Limits

```
❌ Timed operations cannot be extended
✅ Provide extend or disable options
✅ Auto-save user progress
✅ Warn before timeout
```

---

## Cognitive Accessibility

### Clear Structure

**Heading Hierarchy:**
```html
<h1>Page Main Title</h1>        <!-- Only one per page -->
  <h2>Section Title</h2>
    <h3>Subsection</h3>
    <h3>Subsection</h3>
  <h2>Section Title</h2>

❌ Skip levels: h1 → h3
❌ Use only for styling, not structure
```

**Landmark Regions:**
```html
<header role="banner">
  <nav role="navigation">...</nav>
</header>

<main role="main">
  <article>...</article>
</main>

<aside role="complementary">...</aside>

<footer role="contentinfo">...</footer>
```

### Consistent Navigation

```
✅ Navigation in same position on every page
✅ Consistent naming and icons
✅ Provide multiple navigation methods (menu, search, sitemap)
✅ Show current location (Breadcrumb, highlighting)
```

### Error Handling

**Form Validation:**
```html
<!-- Clear error messages -->
<label for="email">Email</label>
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<span id="email-error" role="alert">
  Please enter a valid email format, e.g.: name@example.com
</span>

✅ Specifically describe the error
✅ Provide correction suggestions
✅ Error message near the field
✅ Don't rely only on color
```

### Simple Language

```
✅ Use common vocabulary
✅ Short sentences (under 20 words)
✅ Active voice
✅ Avoid jargon and abbreviations
✅ Provide abbreviation explanations: <abbr title="World Wide Web">WWW</abbr>
```

---

## Platform-Specific Guidelines

### iOS Accessibility

**VoiceOver Support:**
```swift
// Set accessibility label
button.accessibilityLabel = "Add item"

// Set hint
button.accessibilityHint = "Double tap to add item to list"

// Set traits
button.accessibilityTraits = .button

// Group elements
view.accessibilityElements = [label, textField, button]
```

**Dynamic Type:**
```swift
label.font = UIFont.preferredFont(forTextStyle: .body)
label.adjustsFontForContentSizeCategory = true
```

**Reduce Motion:**
```swift
if UIAccessibility.isReduceMotionEnabled {
    // Use simple or no animations
}
```

### Android Accessibility

**TalkBack Support:**
```kotlin
// Set content description
button.contentDescription = "Add item"

// Importance
view.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES

// Custom actions
ViewCompat.setAccessibilityDelegate(view, object : AccessibilityDelegateCompat() {
    override fun onInitializeAccessibilityNodeInfo(
        host: View,
        info: AccessibilityNodeInfoCompat
    ) {
        super.onInitializeAccessibilityNodeInfo(host, info)
        info.addAction(
            AccessibilityNodeInfoCompat.AccessibilityActionCompat(
                AccessibilityNodeInfoCompat.ACTION_CLICK,
                "Add item"
            )
        )
    }
})
```

**Scalable Text:**
```kotlin
textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
```

### Web Accessibility (WAI-ARIA)

**ARIA Roles:**
```html
<!-- Landmarks -->
<div role="navigation">...</div>
<div role="main">...</div>
<div role="search">...</div>

<!-- Widgets -->
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>

<!-- Live regions -->
<div role="alert">Error message</div>
<div role="status" aria-live="polite">Loading...</div>
```

**ARIA Attributes:**
```html
<!-- States -->
aria-expanded="true|false"
aria-selected="true|false"
aria-checked="true|false|mixed"
aria-disabled="true"
aria-hidden="true"

<!-- Relationships -->
aria-labelledby="id"
aria-describedby="id"
aria-controls="id"
aria-owns="id"

<!-- Live regions -->
aria-live="polite|assertive|off"
aria-atomic="true|false"
```

**Example: Accordion:**
```html
<div class="accordion">
  <h3>
    <button
      aria-expanded="false"
      aria-controls="panel-1"
    >
      Section 1
    </button>
  </h3>
  <div
    id="panel-1"
    role="region"
    aria-labelledby="btn-1"
    hidden
  >
    Content...
  </div>
</div>
```

**Example: Modal:**
```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <h2 id="modal-title">Confirm Delete</h2>
  <p>Are you sure you want to delete this item?</p>
  <button>Cancel</button>
  <button>Confirm</button>
</div>
```

---

## Testing and Verification

### Automated Testing Tools

| Tool | Type | Description |
|------|------|-------------|
| axe | Browser extension | Auto-detect WCAG issues |
| WAVE | Browser extension | Visualize problems |
| Lighthouse | Chrome built-in | Accessibility score |
| Pa11y | CLI | CI/CD integration |
| jest-axe | Testing library | Automated testing |

### Manual Testing Checklist

**Keyboard Testing:**
```
□ All features operable via keyboard
□ Focus order is logical
□ Focus indicator is visible
□ No focus traps
□ Shortcuts don't conflict
```

**Screen Reader Testing:**
```
□ All content can be read
□ Images have alt text
□ Form fields have labels
□ Error messages are announced
□ Dynamic content updates are announced
```

**Visual Testing:**
```
□ Contrast meets standards
□ 200% zoom doesn't break layout
□ Don't rely only on color
□ Animations can be disabled
□ Text is resizable
```

**Cognitive Testing:**
```
□ Heading structure is correct
□ Link text is clear
□ Error messages are specific
□ Instructions are sufficient
□ Actions are reversible
```

### Screen Reader Testing

| Platform | Screen Reader |
|----------|---------------|
| macOS | VoiceOver (built-in) |
| Windows | NVDA (free), JAWS |
| iOS | VoiceOver (built-in) |
| Android | TalkBack (built-in) |

**VoiceOver Shortcuts (macOS):**
```
Toggle on/off: Cmd + F5
Navigate: VO + Left/Right arrows
Headings: VO + Cmd + H
Links: VO + Cmd + L
Forms: VO + Cmd + J
```

### Accessibility Statement Template

```markdown
# Accessibility Statement

## Commitment
[Company Name] is committed to ensuring that our [Product Name]
is accessible to everyone, including people with disabilities.

## Conformance Status
This product conforms to WCAG 2.1 Level AA standards.

## Known Limitations
- [List known issues and expected fix dates]

## Feedback
If you encounter any accessibility issues while using our product,
please contact us:
- Email: accessibility@example.com
- Phone: 1-800-XXX-XXXX

## Last Updated
January 15, 2024
```

---

## Quick Checklists

### Designer Checklist

```
Visual
□ Color contrast ≥ 4.5:1
□ Don't rely only on color to convey information
□ Minimum font size 16px
□ Touch targets ≥ 44px
□ Focus states are obvious

Interaction
□ All features keyboard operable
□ Focus order is logical
□ Provide gesture alternatives
□ Error messages are clear

Content
□ Heading hierarchy is correct
□ Link text is meaningful
□ Images have alt text
□ Forms have labels
```

### Developer Checklist

```
HTML
□ Use semantic tags
□ Heading hierarchy correct (h1-h6)
□ Forms have associated labels
□ Images have alt
□ Tables have caption and th

ARIA
□ Custom components have correct roles
□ States expressed with aria-*
□ Dynamic content uses aria-live
□ Modals have aria-modal

Keyboard
□ Can Tab navigate
□ Can Enter/Space activate
□ Can Escape close
□ Focus management is correct

Testing
□ axe checks pass
□ Keyboard testing passes
□ Screen reader testing
□ Zoom testing passes
```
