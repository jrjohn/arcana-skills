# Unified Document Format / 統一文件格式規範

> **Important:** All IEC 62304 documents (SRS/SDD/SWD/STP/STC/SVV/RTM) must use the same cover page and Revision History format to ensure consistency.

## Standard Cover Format / 標準封面格式

All document Markdown cover pages must follow this format:

```markdown
# {Document Title}
## For {Project Name}

Version {X.X}
Prepared by {Author}
{Organization}
{Date}

## Table of Contents
<!-- TOC -->
* [1. Introduction](#1-introduction)
* [2. ...](#2-...)
<!-- TOC -->

## Revision History

| Name | Date | Reason For Changes | Version |
|------|------|--------------------|---------|
|      |      |                    |         |

---
```

## Standard Document Titles

| Document | Title |
|----------|-------|
| SRS | `# Software Requirements Specification` |
| SDD | `# Software Design Description` |
| SWD | `# Software Detailed Design` |
| STP | `# Software Test Plan` |
| STC | `# Software Test Cases` |
| SVV | `# Software Verification & Validation Report` |
| RTM | `# Requirements Traceability Matrix` |

## Revision History Format

**Unified column order:**

| Name | Date | Reason For Changes | Version |
|------|------|--------------------|---------|

**Forbidden old formats:**
- ❌ `| Version | Date | Changes | Author |`
- ❌ `| Version | Date | Author | Description |`
- ❌ Table-style cover (document info table)
- ❌ `## Table of Contents (Detailed)` or any duplicate TOC sections
- ❌ `## 1. Document Information` table-style info block

## Mandatory Format Elements

> **Important:** All documents must strictly follow these elements, no omissions or order changes:

1. **Standard Cover** - Must include:
   - H1 title (`# {Document Title}`)
   - H2 project name (`## For {Project Name}`)
   - Version info (Version X.X)
   - Author (Prepared by)
   - Organization name
   - Date (YYYY-MM-DD)

2. **Table of Contents** - Must:
   - Use `## Table of Contents` heading
   - Wrap with `<!-- TOC -->` markers
   - List all major chapters

3. **Revision History** - Must:
   - Use `## Revision History` heading
   - Column order: `Name | Date | Reason For Changes | Version`
   - Use `---` separator to end section

4. **Main chapters** - Start from `## 1. Introduction`

## Font Settings (DOCX Output)

| Character Type | Font |
|----------------|------|
| English/ASCII | Arial |
| Chinese/East Asian | Microsoft JhengHei (微軟正黑體) |
| Headings | Arial + Microsoft JhengHei (mixed) |
| Code | Consolas |

## Code Block Formatting

DOCX output code blocks have these features:

| Feature | Description |
|---------|-------------|
| **Line Numbers** | Left-side line numbers for code location |
| **Zebra Striping** | Odd rows white (FFFFFF), even rows light gray (F5F5F5) |
| **Fixed Line Height** | 14pt line height for alignment |
| **Syntax Highlighting** | Based on VSCode Light+ color scheme |
| **Fixed Table Layout** | Uses `layout: fixed` to prevent column width changes |
| **Explicit Column Width** | Line number column 720 DXA, code column 8640 DXA |
| **Text Direction Lock** | `textDirection: lrTb` ensures horizontal text flow |

> **⚠️ Google Drive Editing Compatibility**
>
> When DOCX is edited directly in Google Drive, code blocks may display vertically.
> This is due to Google Docs' limited compatibility with Word table formats.
>
> **Solutions:**
> 1. Regenerate DOCX using latest `md-to-docx.js` (includes fixed table layout)
> 2. Download DOCX and edit in Microsoft Word, avoid Google Docs
> 3. For online collaboration, edit MD files then reconvert
