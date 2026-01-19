# Responsive Design Guide for UI Flow

## Device Specifications

| Device | Width | Height | Orientation |
|--------|-------|--------|-------------|
| iPad Pro 11" | 1194px | 834px | Landscape |
| iPhone 15 Pro | 393px | 852px | Portrait |

## CSS Media Queries

```css
/* iPad (default) */
body { width: 1194px; height: 834px; }

/* iPhone */
@media (max-width: 500px) {
  body { width: 393px; height: 852px; }
}
```

## Tailwind Responsive Utilities

```html
<!-- Text sizes -->
<h1 class="text-lg tablet:text-2xl">Title</h1>
<p class="text-sm tablet:text-base">Body text</p>

<!-- Spacing -->
<div class="p-4 tablet:p-6">Content</div>
<div class="gap-3 tablet:gap-6">Items</div>

<!-- Layout direction -->
<div class="flex flex-col tablet:flex-row">Items</div>
```

## Common Responsive Patterns

### 1. Card Grid Layout

```html
<!-- 2 columns on iPad, 1 on iPhone -->
<div class="grid grid-cols-1 tablet:grid-cols-2 gap-4">
  <div class="card">Card 1</div>
  <div class="card">Card 2</div>
</div>

<!-- 3 columns on iPad, 1 on iPhone -->
<div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
  <div class="card">Card 1</div>
  <div class="card">Card 2</div>
  <div class="card">Card 3</div>
</div>
```

### 2. Role Selection (Horizontal → Vertical)

**iPad (Horizontal):**
```html
<div class="flex flex-row gap-8 justify-center">
  <div class="w-[300px] p-8">Student Card</div>
  <div class="w-[300px] p-8">Parent Card</div>
</div>
```

**Responsive:**
```html
<div class="flex flex-col tablet:flex-row gap-4 tablet:gap-8 px-4 tablet:px-0 tablet:justify-center">
  <div class="tablet:w-[300px] p-4 tablet:p-8">Student Card</div>
  <div class="tablet:w-[300px] p-4 tablet:p-8">Parent Card</div>
</div>
```

### 3. List Item (Compact on iPhone)

```html
<div class="flex items-center gap-3 tablet:gap-4 p-3 tablet:p-4">
  <div class="w-10 h-10 tablet:w-14 tablet:h-14 rounded-full bg-blue-500">
    <span class="text-xl tablet:text-3xl">Icon</span>
  </div>
  <div class="flex-1">
    <h3 class="text-sm tablet:text-lg font-bold">Title</h3>
    <p class="text-xs tablet:text-sm text-gray-500">Description</p>
  </div>
  <button class="px-3 py-1.5 tablet:px-4 tablet:py-2 text-sm">Action</button>
</div>
```

### 4. Header Navigation

```html
<header class="px-4 py-3 tablet:px-6 tablet:py-4">
  <div class="flex items-center gap-2 tablet:gap-4">
    <button class="w-8 h-8 tablet:w-10 tablet:h-10">Back</button>
    <h1 class="text-base tablet:text-xl font-bold">Title</h1>
  </div>
</header>
```

### 5. Bottom Navigation

```html
<nav class="h-14 tablet:h-20">
  <div class="flex justify-around items-center h-full">
    <a class="flex flex-col items-center gap-0.5 tablet:gap-1">
      <svg class="w-5 h-5 tablet:w-6 tablet:h-6">Icon</svg>
      <span class="text-[10px] tablet:text-xs">Label</span>
    </a>
  </div>
</nav>
```

### 6. Form Inputs

```html
<input class="h-10 tablet:h-12 px-3 tablet:px-4 text-sm tablet:text-base rounded-lg" />
<button class="h-10 tablet:h-12 px-4 tablet:px-6 text-sm tablet:text-base rounded-xl">
  Submit
</button>
```

### 7. Modal / Dialog

```html
<!-- Full screen on iPhone, centered modal on iPad -->
<div class="fixed inset-0 tablet:inset-auto tablet:top-1/2 tablet:left-1/2
            tablet:-translate-x-1/2 tablet:-translate-y-1/2
            w-full h-full tablet:w-[500px] tablet:h-auto tablet:max-h-[80vh]
            tablet:rounded-2xl bg-white">
  <div class="p-4 tablet:p-6">Modal content</div>
</div>
```

### 8. Statistics Cards

```html
<div class="grid grid-cols-2 tablet:grid-cols-4 gap-3 tablet:gap-4">
  <div class="bg-white rounded-xl p-3 tablet:p-4 text-center">
    <p class="text-2xl tablet:text-4xl font-bold">42</p>
    <p class="text-xs tablet:text-sm text-gray-500">Words</p>
  </div>
</div>
```

## Device-Specific Elements

```html
<!-- Show only on iPad -->
<div class="hidden tablet:block">iPad sidebar</div>

<!-- Show only on iPhone -->
<div class="tablet:hidden">iPhone bottom sheet</div>
```

## Navigation Links

**iPad paths:** `auth/SCR-AUTH-001.html`
**iPhone paths:** `../iphone/SCR-AUTH-001.html`

```html
<!-- Responsive navigation (same file works for both) -->
<script>
function navigateTo(screenId) {
  // Get current viewport width to determine device
  const isPhone = window.innerWidth <= 500;
  const basePath = isPhone ? '../iphone/' : '';
  location.href = basePath + screenId + '.html';
}
</script>
```

## Quick Reference

| Element | iPhone | iPad |
|---------|--------|------|
| Title | text-lg | text-2xl |
| Body | text-sm | text-base |
| Caption | text-xs | text-sm |
| Padding | p-4 | p-6 |
| Gap | gap-3 | gap-6 |
| Button height | h-10 | h-12 |
| Icon size | w-5 h-5 | w-6 h-6 |
| Avatar | w-10 h-10 | w-14 h-14 |
| Card radius | rounded-xl | rounded-2xl |
