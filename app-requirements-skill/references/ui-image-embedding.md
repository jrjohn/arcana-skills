# UI Image Embedding in SDD Specification

This document defines how to embed UI/UX design images in SDD (Software Design Description) documents.

## Why Embed Images?

| Method | Advantages | Disadvantages |
|--------|------------|---------------|
| **External Links (URL)** | Small file size, real-time updates | Links may break, requires network, cannot view offline |
| **Direct Image Embedding** | Document is self-contained, works offline, regulatory submission friendly | Larger file size |

**IEC 62304 Compliance Consideration:** For regulatory submissions, documents must be self-contained and should not depend on external links. Therefore, it is recommended to directly embed UI design images in SDD documents.

---

## Image Specifications

### Format Requirements

| Attribute | Recommended Value | Description |
|-----------|-------------------|-------------|
| **Format** | PNG (Recommended) | Supports transparent background, lossless compression |
| | JPG | Suitable for photo-type images |
| **Resolution** | @2x (Recommended) | Ensures clarity in DOCX output |
| | @1x | For drafts or low-resolution needs only |
| | @3x | For high-resolution requirements |
| **Color Mode** | sRGB | Ensures consistent display across platforms |
| **Maximum Size** | 2MB/image | Prevents document from becoming too large |

### Naming Convention

```
SCR-{Module}-{Number}-{description}.png
```

**Examples:**
- `SCR-AUTH-001-login.png` - Login screen
- `SCR-AUTH-002-signup.png` - Signup screen
- `SCR-HOME-001-dashboard.png` - Home dashboard
- `SCR-TRAIN-001-game-selection.png` - Game selection screen
- `SCR-REPORT-001-daily.png` - Daily report screen

### Directory Structure

```
{project}/
├── 02-design/
│   └── SDD/
│       ├── SDD-{project}-{version}.md
│       └── images/                    ← UI images location
│           ├── SCR-AUTH-001-login.png
│           ├── SCR-AUTH-002-signup.png
│           ├── SCR-HOME-001-dashboard.png
│           └── ...
│
└── 03-assets/
    └── ui-screens/                    ← Backup location (source files)
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
- Middle: Email and password input fields
- Bottom: Login button, forgot password link, social login options

**Related Requirements:** SRS-AUTH-001, SRS-AUTH-002
```

### Multi-State Screens

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

## Exporting from Design Tools

### Figma

1. Select the Frame to export
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

The converter in `md-to-docx-converter.md` supports automatic image embedding.

### Conversion Process

```
1. Read Markdown file
2. Parse image syntax ![alt](path)
3. Read corresponding image files
4. Embed images into DOCX
5. Output complete DOCX document
```

### Supported Image Paths

| Path Type | Example | Supported |
|-----------|---------|-----------|
| Relative path | `./images/xxx.png` | ✓ |
| Relative path (no ./) | `images/xxx.png` | ✓ |
| Absolute path | `/path/to/xxx.png` | ✓ |
| URL | `https://...` | ✗ (Not recommended) |

---

## Best Practices

### Do's ✓

- Use @2x resolution to ensure clarity
- Use PNG format to maintain quality
- Follow naming convention `SCR-{Module}-{Number}-{description}.png`
- Place images in `02-design/SDD/images/` directory
- Add text description for each image
- Label corresponding SRS requirement IDs

### Don'ts ✗

- Don't use external URL links
- Don't use oversized images (>2MB)
- Don't include sensitive information in images
- Don't use Chinese characters or spaces in filenames
- Don't omit alt descriptions for images

---

## Checklist

When completing the SDD UI section, confirm the following items:

- [ ] All screens have corresponding images
- [ ] Image naming follows convention
- [ ] Image resolution is @2x
- [ ] Image format is PNG
- [ ] Images are placed in `images/` directory
- [ ] Images are correctly embedded in Markdown
- [ ] Each image has a text description
- [ ] Corresponding SRS requirement IDs are labeled
- [ ] Images display correctly after DOCX conversion
