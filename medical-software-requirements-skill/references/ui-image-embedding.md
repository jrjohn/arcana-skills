# UI Image Embedding in SDD Specification

This document defines how to embed UI/UX design images into SDD (Software Design Specification) documents.

## Why Embed Images?

| Method | Advantages | Disadvantages |
|-----|------|------|
| **External Link (URL)** | Small file size, easy to update | Link can break, requires network, cannot view offline |
| **Direct Embedding** | Document is self-contained, can view offline, regulatory review friendly | Larger file size |

**IEC 62304 Regulatory Consideration:** During regulatory review, documents must be self-contained and should not depend on external links. Therefore, it is recommended to directly embed UI design images into the SDD document.

---

## Image Specifications

### Format Requirements

| Property | Recommended Value | Description |
|-----|-------|------|
| **Format** | PNG (recommended) | Supports transparency, lossless compression |
| | JPG | Suitable for photo images |
| **Resolution** | @2x (recommended) | Ensures clarity in DOCX output |
| | @1x | Only for draft or low resolution requirements |
| | @3x | High resolution requirements |
| **Color Mode** | sRGB | Ensures cross-platform consistency |
| **Maximum Size** | 2MB/image | Avoid documents being too large |

### Naming Specification

```
SCR-{Module}-{Number}-{Description}.png
```

**Examples:**
- `SCR-AUTH-001-login.png` - Login Screen
- `SCR-AUTH-002-signup.png` - Registration Screen
- `SCR-HOME-001-dashboard.png` - Home Dashboard
- `SCR-TRAIN-001-game-selection.png` - Game Selection Screen
- `SCR-REPORT-001-daily.png` - Daily Report Screen

### Directory Structure

```
{project}/
├── 02-design/
│   └── SDD/
│       ├── SDD-{project}-{version}.md
│       └── images/                    ← UI Image Storage Location
│           ├── SCR-AUTH-001-login.png
│           ├── SCR-AUTH-002-signup.png
│           ├── SCR-HOME-001-dashboard.png
│           └── ...
│
└── 03-assets/
    └── ui-screens/                    ← Backup Location (source files)
        ├── @1x/
        ├── @2x/
        └── @3x/
```

---

## Markdown Embedding Syntax

### Basic Syntax

```markdown
![{Image Description}](./images/{filename}.png)
```

### Example

```markdown
### 6.1 Authentication Module Screen Design

#### SCR-AUTH-001 Login Screen

![SCR-AUTH-001 Login Screen](./images/SCR-AUTH-001-login.png)

**Screen Description:**
- Top: App Logo
- Middle: Email and Password Input Fields
- Bottom: Login Button, Forgot Password Link, Social Login Options

**Corresponding Requirements:** SRS-AUTH-001, SRS-AUTH-002
```

### Multiple State Screens

```markdown
#### SCR-AUTH-001 Login Screen

**Default State:**
![SCR-AUTH-001 Login Screen - Default](./images/SCR-AUTH-001-login-default.png)

**Input State:**
![SCR-AUTH-001 Login Screen - Input](./images/SCR-AUTH-001-login-input.png)

**Error State:**
![SCR-AUTH-001 Login Screen - Error](./images/SCR-AUTH-001-login-error.png)
```

---

## Export from Design Tools

### Figma

1. Select the Frame you want to export
2. Right panel → Export
3. Settings:
   - Format: PNG
   - Scale: 2x
   - Include "id" attribute: Uncheck
4. Click Export

### Sketch

1. Select Artboard
2. File → Export → Export Selected...
3. Settings:
   - Format: PNG
   - Scale: 2x
4. Export

### Adobe XD

1. Select Artboard
2. File → Export → Selected...
3. Settings:
   - Format: PNG
   - Export for: Design (2x)
4. Export

### Penpot

1. Select Frame
2. Right-click → Export selection
3. Settings:
   - Type: PNG
   - Scale: 2
4. Export

---

## DOCX Conversion Support

The converter in `md-to-docx-converter.md` already supports automatic image embedding.

### Conversion Flow

```
1. Read Markdown file
2. Parse image syntax ![alt](path)
3. Read corresponding image file
4. Embed image into DOCX
5. Output complete DOCX document
```

### Supported Image Paths

| Path Type | Example | Supported |
|---------|------|------|
| Relative path | `./images/xxx.png` | ✓ |
| Relative path (no ./) | `images/xxx.png` | ✓ |
| Absolute path | `/path/to/xxx.png` | ✓ |
| URL | `https://...` | ✗ (Not recommended) |

---

## Best Practices

### Do's ✓

- Use @2x resolution to ensure clarity
- Use PNG format to maintain quality
- Follow naming specification `SCR-{Module}-{Number}-{Description}.png`
- Place images in `02-design/SDD/images/` directory
- Add text description for each image
- Mark corresponding SRS requirement numbers

### Don'ts ✗

- Don't use external URL links
- Don't use images that are too large (>2MB)
- Don't include sensitive information in images
- Don't use Chinese or special characters in filenames
- Don't omit image alt descriptions

---

## Checklist

When completing SDD UI sections, confirm the following items:

- [ ] All screens have corresponding images
- [ ] Image naming follows specification
- [ ] Image resolution is @2x
- [ ] Image format is PNG
- [ ] Images are placed in `images/` directory
- [ ] Images are correctly embedded in Markdown
- [ ] Each image has text description
- [ ] Corresponding SRS requirement numbers are marked
- [ ] DOCX conversion displays images correctly
