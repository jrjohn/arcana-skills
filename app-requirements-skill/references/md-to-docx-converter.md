# MD to DOCX Converter

This document explains how to convert Markdown documents to professionally formatted Word (.docx) files.

**Key Features:**
- Automatically recognizes SRS/SWD requirement item formats and converts them to professional table presentation
- Supports headings, tables, code blocks, inline formatting
- **Supports Mermaid diagram auto-rendering to images**
- Automatically generates headers/footers

## Usage

### 1. Install Dependencies

```bash
npm install docx
npm install -g @mermaid-js/mermaid-cli
```

> **Note:** Mermaid CLI (`mmdc`) needs to be installed globally for rendering Mermaid code to PNG images.

### 2. Conversion Script

Create `md-to-docx.js` file:

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
        ImageRun, TableOfContents } = require('docx');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

// ============================================
// Font Settings - Chinese uses Yuan Gothic, English uses Arial
// ============================================
const FONT_CN = 'Yuan Gothic';  // Chinese font (can be changed to 'Microsoft JhengHei' or 'Noto Sans TC')
const FONT_EN = 'Arial';        // English font
const FONT_CODE = 'Courier New';  // Code font

// Font size settings (unit: half-points, 24 = 12pt)
const FONT_SIZE = {
  H1: 36,        // 18pt - Main title
  H2: 32,        // 16pt - Major section
  H3: 28,        // 14pt - Subsection
  H4: 26,        // 13pt - Sub-subsection
  H5: 24,        // 12pt - Detail
  BODY: 22,      // 11pt - Body text
  TABLE: 20,     // 10pt - Table content
  TABLE_HEADER: 20, // 10pt - Table header (bold)
  SMALL: 18,     // 9pt - Small text
  FOOTER: 18     // 9pt - Footer
};

/**
 * Detect if text contains Chinese characters
 */
function containsChinese(text) {
  return /[\u4e00-\u9fff]/.test(text);
}

/**
 * Get appropriate font (based on text content)
 */
function getFont(text) {
  return containsChinese(text) ? FONT_CN : FONT_EN;
}

// ============================================
// Mermaid Diagram Renderer
// ============================================

/**
 * Render Mermaid code to PNG image
 * @param {string} mermaidCode - Mermaid diagram code
 * @param {string} outputDir - Output directory
 * @returns {string|null} - Image path or null (on failure)
 */
function renderMermaidToPng(mermaidCode, outputDir) {
  const hash = crypto.createHash('md5').update(mermaidCode).digest('hex').substring(0, 8);
  const tempDir = path.join(outputDir, '.mermaid-temp');
  const inputFile = path.join(tempDir, `mermaid-${hash}.mmd`);
  const outputFile = path.join(tempDir, `mermaid-${hash}.png`);

  // Create temp directory
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  // If cached image exists, return directly
  if (fs.existsSync(outputFile)) {
    return outputFile;
  }

  // Write Mermaid code
  fs.writeFileSync(inputFile, mermaidCode);

  try {
    // Use mermaid-cli to render
    execSync(`mmdc -i "${inputFile}" -o "${outputFile}" -b transparent -w 800`, {
      stdio: 'pipe',
      timeout: 30000
    });

    if (fs.existsSync(outputFile)) {
      return outputFile;
    }
  } catch (error) {
    console.warn(`Mermaid rendering failed: ${error.message}`);
  }

  return null;
}

/**
 * Read PNG image dimensions
 * PNG file format: first 8 bytes are signature, IHDR chunk contains width/height info
 */
function getPngDimensions(buffer) {
  // PNG signature: 89 50 4E 47 0D 0A 1A 0A
  // IHDR chunk starts at byte 8, width at 16-19, height at 20-23
  if (buffer.length < 24) return null;

  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);

  return { width, height };
}

/**
 * Create Mermaid image paragraph
 * Maintain original aspect ratio, max width 450px, prevent image distortion
 */
function createMermaidImage(imagePath) {
  const imageBuffer = fs.readFileSync(imagePath);

  // Read actual image dimensions
  const dimensions = getPngDimensions(imageBuffer);

  let displayWidth, displayHeight;
  const maxWidth = 450;  // Max width limit, preserve adequate margin
  const maxHeight = 500; // Max height limit

  if (dimensions) {
    const { width, height } = dimensions;
    const aspectRatio = width / height;

    // Calculate scaled dimensions based on max limits
    if (width > maxWidth) {
      displayWidth = maxWidth;
      displayHeight = Math.round(maxWidth / aspectRatio);
    } else {
      displayWidth = width;
      displayHeight = height;
    }

    // If height still exceeds limit, scale again
    if (displayHeight > maxHeight) {
      displayHeight = maxHeight;
      displayWidth = Math.round(maxHeight * aspectRatio);
    }
  } else {
    // Use default values when dimensions cannot be read
    displayWidth = 400;
    displayHeight = 300;
  }

  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 240 },
    children: [
      new ImageRun({
        data: imageBuffer,
        transformation: {
          width: displayWidth,
          height: displayHeight
        },
        type: 'png'
      })
    ]
  });
}

/**
 * Clean up Mermaid temp files
 */
function cleanupMermaidTemp(outputDir) {
  const tempDir = path.join(outputDir, '.mermaid-temp');
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

// ============================================
// Requirement Item Table Converter
// ============================================

/**
 * Detect if line is a requirement item heading
 * Supported formats:
 *   - #### SRS-AUTH-001 User Registration (old format)
 *   - ##### REQ-FUNC-001 User Login (new format, space separated)
 *   - #### REQ-FUNC-001: User Login (new format, colon separated)
 */
function isRequirementHeading(line) {
  // Support SRS/SWD/SDD/STC/REQ prefixes, 3-5 # symbols
  return line.match(/^#{3,5}\s+(SRS|SWD|SDD|STC|REQ)-[A-Z]+-\d+/);
}

/**
 * Parse requirement item block, convert to table structure
 * Supports multiple input formats:
 *
 * Chinese format:
 *   #### SRS-AUTH-001 User Registration
 *   **Description:** The system must...
 *   **Priority:** Required
 *   **Acceptance Criteria:**
 *   - AC1: Given user opens app for first time, clicks register, Then system displays registration form
 *   - AC2: Given user fills complete info, clicks submit, Then system validates data format and creates account
 *
 * English format:
 *   ##### REQ-FUNC-001 User Login
 *   **Statement:** The system shall...
 *   **Rationale:** To ensure...
 *   **Acceptance Criteria:**
 *   - AC1: Given the user has valid credentials, When submitting login, Then the system authenticates and redirects to home
 *   **Verification Method:** Test
 *
 * Acceptance Criteria format comparison:
 *   Chinese: Given [precondition], [action], Then [expected result]
 *   English: Given [precondition], When [action], Then [expected result]
 */
function parseRequirementBlock(lines, startIndex) {
  const headerLine = lines[startIndex];

  // Try to match: ID + space + name, or ID + colon + name
  let match = headerLine.match(/^#{3,5}\s+((SRS|SWD|SDD|STC|REQ)-[A-Z]+-\d+)[:：]?\s*(.+)/);

  if (!match) return null;

  const reqId = match[1];
  const reqName = match[3] ? match[3].trim() : '';

  const requirement = {
    id: reqId,
    name: reqName,
    // Support Chinese and English fields
    description: '',      // Description (old)
    statement: '',        // Statement (new)
    rationale: '',        // Rationale (new)
    priority: '',
    safetyClass: '',
    verificationMethod: '',
    acceptanceCriteria: [],
    otherFields: {}
  };

  let i = startIndex + 1;
  let inAcceptanceCriteria = false;
  let currentField = null;

  while (i < lines.length) {
    const line = lines[i].trim();

    // End when encountering next heading or separator
    if (line.startsWith('#') || line.match(/^-{3,}$/)) {
      break;
    }

    // Parse **Field:** value or **Field:** value format
    const fieldMatch = line.match(/^\*\*(.+?)[:：]\*\*\s*(.*)$/);

    if (fieldMatch) {
      const fieldName = fieldMatch[1].trim();
      const fieldValue = fieldMatch[2].trim();

      // Chinese fields
      if (fieldName === 'Description' || fieldName === '描述') {
        requirement.description = fieldValue;
        currentField = 'description';
        inAcceptanceCriteria = false;
      } else if (fieldName === 'Priority' || fieldName === '優先級') {
        requirement.priority = fieldValue;
        currentField = 'priority';
        inAcceptanceCriteria = false;
      } else if (fieldName === 'Safety Class' || fieldName === '安全分類') {
        requirement.safetyClass = fieldValue;
        currentField = 'safetyClass';
        inAcceptanceCriteria = false;
      } else if (fieldName === 'Acceptance Criteria' || fieldName === '驗收標準') {
        inAcceptanceCriteria = true;
        currentField = 'acceptanceCriteria';
      }
      // English fields
      else if (fieldName === 'Statement') {
        requirement.statement = fieldValue;
        currentField = 'statement';
        inAcceptanceCriteria = false;
      } else if (fieldName === 'Rationale') {
        requirement.rationale = fieldValue;
        currentField = 'rationale';
        inAcceptanceCriteria = false;
      } else if (fieldName === 'Verification Method') {
        requirement.verificationMethod = fieldValue;
        currentField = 'verificationMethod';
        inAcceptanceCriteria = false;
      } else {
        requirement.otherFields[fieldName] = fieldValue;
        currentField = fieldName;
        inAcceptanceCriteria = false;
      }
    } else if (inAcceptanceCriteria && line.startsWith('- ')) {
      // Acceptance criteria items
      requirement.acceptanceCriteria.push(line.substring(2));
    } else if (line && currentField) {
      // Continue previous field content
      if (currentField === 'description') {
        requirement.description += ' ' + line;
      } else if (currentField === 'statement') {
        requirement.statement += ' ' + line;
      } else if (currentField === 'rationale') {
        requirement.rationale += ' ' + line;
      }
    }

    i++;
  }

  return { requirement, endIndex: i - 1 };
}

/**
 * Create requirement item table
 * Automatically determine Chinese or English field labels and apply appropriate fonts
 */
function createRequirementTable(req) {
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

  const labelWidth = 2200;  // Label column width (widened for Chinese)
  const valueWidth = 7160;  // Value column width

  const rows = [];

  // Header row (merged cell effect using background color)
  rows.push(new TableRow({
    children: [
      new TableCell({
        borders: cellBorders,
        width: { size: labelWidth, type: WidthType.DXA },
        shading: { fill: '4472C4', type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: [new TextRun({ text: req.id, bold: true, color: 'FFFFFF', size: FONT_SIZE.TABLE_HEADER, font: FONT_EN })]
        })]
      }),
      new TableCell({
        borders: cellBorders,
        width: { size: valueWidth, type: WidthType.DXA },
        shading: { fill: '4472C4', type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: [new TextRun({ text: req.name, bold: true, color: 'FFFFFF', size: FONT_SIZE.TABLE_HEADER, font: getFont(req.name) })]
        })]
      })
    ]
  }));

  // New format fields (Statement/Rationale)
  if (req.statement) {
    rows.push(createFieldRow('Statement', req.statement, labelWidth, valueWidth, cellBorders));
  }

  if (req.rationale) {
    rows.push(createFieldRow('Rationale', req.rationale, labelWidth, valueWidth, cellBorders));
  }

  // Old format fields (Description)
  if (req.description) {
    rows.push(createFieldRow('Description', req.description, labelWidth, valueWidth, cellBorders));
  }

  // Priority
  if (req.priority) {
    rows.push(createFieldRow('Priority', req.priority, labelWidth, valueWidth, cellBorders));
  }

  // Safety Class
  if (req.safetyClass) {
    rows.push(createFieldRow('Safety Class', req.safetyClass, labelWidth, valueWidth, cellBorders));
  }

  // Other fields
  for (const [key, value] of Object.entries(req.otherFields)) {
    rows.push(createFieldRow(key, value, labelWidth, valueWidth, cellBorders));
  }

  // Acceptance Criteria
  if (req.acceptanceCriteria.length > 0) {
    // Determine Chinese or English label
    const acLabel = req.statement ? 'Acceptance Criteria' : 'Acceptance Criteria';
    const acParagraphs = req.acceptanceCriteria.map(ac =>
      new Paragraph({
        spacing: { after: 80 },
        children: [new TextRun({ text: '• ' + ac, size: FONT_SIZE.TABLE, font: getFont(ac) })]
      })
    );

    rows.push(new TableRow({
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: labelWidth, type: WidthType.DXA },
          shading: { fill: 'F2F2F2', type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.TOP,
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({
            children: [new TextRun({ text: acLabel, bold: true, size: FONT_SIZE.TABLE_HEADER, font: getFont(acLabel) })]
          })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: valueWidth, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: acParagraphs
        })
      ]
    }));
  }

  // Verification Method (new format)
  if (req.verificationMethod) {
    rows.push(createFieldRow('Verification', req.verificationMethod, labelWidth, valueWidth, cellBorders));
  }

  return new Table({
    columnWidths: [labelWidth, valueWidth],
    rows: rows
  });
}

function createFieldRow(label, value, labelWidth, valueWidth, cellBorders) {
  return new TableRow({
    children: [
      new TableCell({
        borders: cellBorders,
        width: { size: labelWidth, type: WidthType.DXA },
        shading: { fill: 'F2F2F2', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: [new TextRun({ text: label, bold: true, size: FONT_SIZE.TABLE_HEADER, font: getFont(label) })]
        })]
      }),
      new TableCell({
        borders: cellBorders,
        width: { size: valueWidth, type: WidthType.DXA },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          spacing: { after: 0 },
          children: [new TextRun({ text: value, size: FONT_SIZE.TABLE, font: getFont(value) })]
        })]
      })
    ]
  });
}

// ============================================
// Main Parser Functions
// ============================================

/**
 * Check if this is the first heading in an "isolated heading group"
 * When multiple consecutive headings (with no content between) end with a requirement table,
 * only page break before the first heading. This prevents heading groups from being split at page end,
 * but doesn't create page breaks for every heading causing empty pages.
 */
function shouldBreakBeforeHeading(lines, currentIndex) {
  const currentLine = lines[currentIndex];

  // Check if previous non-empty line is also a heading
  let prevIndex = currentIndex - 1;
  while (prevIndex >= 0 && lines[prevIndex].trim() === '') {
    prevIndex--;
  }

  // If previous is also a heading, don't page break (keep heading group together)
  if (prevIndex >= 0 && lines[prevIndex].startsWith('#')) {
    return false;
  }

  // Look ahead to find end of this heading group
  let j = currentIndex + 1;
  let headingCount = 1;

  while (j < lines.length) {
    const line = lines[j].trim();

    if (line === '') {
      j++;
      continue;
    }

    // If another heading, continue looking ahead
    if (line.startsWith('#') && !isRequirementHeading(lines[j])) {
      headingCount++;
      j++;
      continue;
    }

    // If requirement item or other content, stop
    break;
  }

  // Only page break before first heading when there are multiple consecutive headings (heading group)
  // This prevents heading groups from being split by page breaks
  return headingCount > 1;
}

function parseMarkdown(content, outputDir = '.') {
  const lines = content.split('\n');
  const elements = [];
  let inCodeBlock = false;
  let codeBlockContent = [];
  let codeBlockLang = '';
  let inTable = false;
  let tableRows = [];
  let tableHeaders = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Handle code blocks
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        if (codeBlockLang === 'mermaid') {
          // Mermaid diagram - render to image
          const mermaidCode = codeBlockContent.join('\n');
          const imagePath = renderMermaidToPng(mermaidCode, outputDir);
          if (imagePath) {
            elements.push(createMermaidImage(imagePath));
          } else {
            // On render failure, fallback to code block
            console.warn('Mermaid rendering failed, displaying as code block');
            elements.push(createCodeBlock(mermaidCode));
          }
        } else {
          // Regular code block
          elements.push(createCodeBlock(codeBlockContent.join('\n')));
        }
        codeBlockContent = [];
        codeBlockLang = '';
        inCodeBlock = false;
      } else {
        // Start code block, extract language
        codeBlockLang = line.substring(3).trim().toLowerCase();
        inCodeBlock = true;
      }
      i++;
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      i++;
      continue;
    }

    // Handle Markdown tables
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        tableHeaders = parseTableRow(line);
      } else if (line.includes('---')) {
        // Skip separator
      } else {
        tableRows.push(parseTableRow(line));
      }
      i++;
      continue;
    } else if (inTable) {
      if (tableHeaders.length > 0) {
        elements.push(createTable(tableHeaders, tableRows));
      }
      tableHeaders = [];
      tableRows = [];
      inTable = false;
    }

    // Check if requirement item heading - convert to table
    if (isRequirementHeading(line)) {
      const result = parseRequirementBlock(lines, i);
      if (result) {
        elements.push(new Paragraph({ spacing: { before: 240 }, children: [] })); // Spacing
        elements.push(createRequirementTable(result.requirement));
        elements.push(new Paragraph({ spacing: { after: 120 }, children: [] })); // Spacing
        i = result.endIndex + 1;
        continue;
      }
    }

    // Heading handling
    // Heading 1 (# ) - Main title
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      elements.push(createHeading(line.substring(2), HeadingLevel.HEADING_1, true)); // Page break
      i++;
      continue;
    }
    // Heading 2 (## ) - Major section, page break before each major section
    if (line.startsWith('## ')) {
      // Check if main section (e.g., "1. Introduction", "2. Product Overview")
      const isMainSection = line.match(/^##\s+\d+[\.\s]/);
      elements.push(createHeading(line.substring(3), HeadingLevel.HEADING_2, isMainSection));
      i++;
      continue;
    }
    // Heading 3 (### ) - Subsection
    if (line.startsWith('### ')) {
      // Check if heading is followed immediately by requirement table or only empty lines, if so page break before to prevent orphaned heading
      const shouldPageBreak = shouldBreakBeforeHeading(lines, i);
      elements.push(createHeading(line.substring(4), HeadingLevel.HEADING_3, shouldPageBreak));
      i++;
      continue;
    }
    // Heading 4 (#### )
    if (line.startsWith('#### ')) {
      // Check if heading is followed immediately by requirement table or only empty lines, if so page break before to prevent orphaned heading
      const shouldPageBreak = shouldBreakBeforeHeading(lines, i);
      elements.push(createHeading(line.substring(5), HeadingLevel.HEADING_4, shouldPageBreak));
      i++;
      continue;
    }
    // Heading 5 (##### )
    if (line.startsWith('##### ')) {
      elements.push(createHeading(line.substring(6), HeadingLevel.HEADING_5, false));
      i++;
      continue;
    }

    // Separator line
    if (line.match(/^-{3,}$/) || line.match(/^\*{3,}$/)) {
      i++;
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Regular paragraph
    elements.push(createParagraph(line));
    i++;
  }

  // Close unclosed table
  if (inTable && tableHeaders.length > 0) {
    elements.push(createTable(tableHeaders, tableRows));
  }

  return elements;
}

function parseTableRow(line) {
  return line.split('|').slice(1, -1).map(cell => cell.trim());
}

/**
 * Get font size based on heading level
 */
function getHeadingSize(level) {
  switch (level) {
    case HeadingLevel.HEADING_1: return FONT_SIZE.H1;
    case HeadingLevel.HEADING_2: return FONT_SIZE.H2;
    case HeadingLevel.HEADING_3: return FONT_SIZE.H3;
    case HeadingLevel.HEADING_4: return FONT_SIZE.H4;
    case HeadingLevel.HEADING_5: return FONT_SIZE.H5;
    default: return FONT_SIZE.BODY;
  }
}

/**
 * Create heading paragraph
 * @param {string} text - Heading text
 * @param {HeadingLevel} level - Heading level
 * @param {boolean} pageBreakBefore - Whether to page break before heading (for major sections)
 */
function createHeading(text, level, pageBreakBefore = false) {
  const trimmedText = text.trim();
  const fontSize = getHeadingSize(level);

  return new Paragraph({
    heading: level,
    spacing: { before: pageBreakBefore ? 0 : 240, after: 120 },
    pageBreakBefore: pageBreakBefore,  // Page break before major section
    keepNext: true,  // Keep heading with next paragraph on same page (prevent orphaned heading)
    keepLines: true, // Don't split heading itself across lines
    children: [new TextRun({ text: trimmedText, bold: true, size: fontSize, font: getFont(trimmedText) })]
  });
}

function createParagraph(text) {
  const runs = parseInlineFormatting(text);
  return new Paragraph({ spacing: { after: 120 }, children: runs });
}

/**
 * Parse inline formatting (bold, code)
 * @param {string} text - Raw text
 * @param {number} fontSize - Font size, defaults to BODY size
 */
function parseInlineFormatting(text, fontSize = FONT_SIZE.BODY) {
  const runs = [];
  const boldRegex = /\*\*(.+?)\*\*/g;
  const codeRegex = /`([^`]+)`/g;
  const matches = [];
  let match;

  boldRegex.lastIndex = 0;
  while ((match = boldRegex.exec(text)) !== null) {
    matches.push({ index: match.index, end: match.index + match[0].length, text: match[1], type: 'bold' });
  }

  codeRegex.lastIndex = 0;
  while ((match = codeRegex.exec(text)) !== null) {
    matches.push({ index: match.index, end: match.index + match[0].length, text: match[1], type: 'code' });
  }

  matches.sort((a, b) => a.index - b.index);

  let lastIndex = 0;
  for (const m of matches) {
    if (m.index > lastIndex) {
      const segment = text.substring(lastIndex, m.index);
      runs.push(new TextRun({ text: segment, size: fontSize, font: getFont(segment) }));
    }
    if (m.type === 'bold') {
      runs.push(new TextRun({ text: m.text, bold: true, size: fontSize, font: getFont(m.text) }));
    } else if (m.type === 'code') {
      runs.push(new TextRun({ text: m.text, size: fontSize, font: FONT_CODE }));
    }
    lastIndex = m.end;
  }

  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex);
    runs.push(new TextRun({ text: remaining, size: fontSize, font: getFont(remaining) }));
  }

  if (runs.length === 0) {
    runs.push(new TextRun({ text, size: fontSize, font: getFont(text) }));
  }

  return runs;
}

function createCodeBlock(content) {
  return content.split('\n').map(line =>
    new Paragraph({
      spacing: { after: 0 },
      shading: { fill: 'F5F5F5', type: ShadingType.CLEAR },
      children: [new TextRun({ text: line || ' ', font: FONT_CODE, size: FONT_SIZE.TABLE })]
    })
  );
}

/**
 * Calculate table column widths - intelligently allocate based on content length
 */
function calculateColumnWidths(headers, rows, totalWidth = 9360) {
  const numCols = headers.length;

  // Calculate max content length for each column
  const maxLengths = headers.map((h, i) => {
    let max = h.length;
    rows.forEach(row => {
      if (row[i]) {
        max = Math.max(max, row[i].length);
      }
    });
    return max;
  });

  const totalLength = maxLengths.reduce((a, b) => a + b, 0);

  // Allocate width based on content length ratio, but set minimum width
  const minWidth = 1200;  // Minimum column width
  let widths = maxLengths.map(len => Math.max(minWidth, Math.floor((len / totalLength) * totalWidth)));

  // Adjust total width
  const currentTotal = widths.reduce((a, b) => a + b, 0);
  if (currentTotal !== totalWidth) {
    const diff = totalWidth - currentTotal;
    widths[widths.length - 1] += diff;  // Last column absorbs difference
  }

  return widths;
}

function createTable(headers, rows) {
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
  const numCols = headers.length;
  const columnWidths = calculateColumnWidths(headers, rows);

  const tableRows = [
    new TableRow({
      tableHeader: true,
      children: headers.map((header, i) => new TableCell({
        borders: cellBorders,
        width: { size: columnWidths[i], type: WidthType.DXA },
        shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: header, bold: true, size: FONT_SIZE.TABLE_HEADER, font: getFont(header) })]
        })]
      }))
    }),
    ...rows.map(row => new TableRow({
      children: row.map((cell, i) => new TableCell({
        borders: cellBorders,
        width: { size: columnWidths[i], type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          spacing: { after: 0 },
          children: parseInlineFormatting(cell, FONT_SIZE.TABLE)
        })]
      }))
    }))
  ];

  return new Table({ columnWidths: columnWidths, rows: tableRows });
}

/**
 * Parse document structure, separate cover, TOC, revision history, and main content
 */
function parseDocumentStructure(content, outputDir) {
  const lines = content.split('\n');
  const structure = {
    coverInfo: { title: '', subtitle: '', version: '', author: '', organization: '', date: '' },
    tocLines: [],
    revisionHistory: [],
    mainContent: []
  };

  let section = 'cover';  // cover, toc, revision, main
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect cover info (document start to Table of Contents)
    if (section === 'cover') {
      if (trimmed.startsWith('# ')) {
        structure.coverInfo.title = trimmed.substring(2).trim();
      } else if (trimmed.startsWith('## For ') || trimmed.startsWith('**For ')) {
        structure.coverInfo.subtitle = trimmed.replace(/^##\s*For\s*|^\*\*For\s*|\*\*$/g, '').trim();
      } else if (trimmed.toLowerCase().includes('version')) {
        structure.coverInfo.version = trimmed.replace(/^Version\s*/i, '').trim();
      } else if (trimmed.toLowerCase().includes('prepared by')) {
        structure.coverInfo.author = trimmed.replace(/^Prepared by\s*/i, '').trim();
      } else if (trimmed.match(/^[A-Z].*\s+(Inc\.|Corp\.|Ltd\.|Co\.)$/i) || trimmed.match(/^SOMNICS/i)) {
        structure.coverInfo.organization = trimmed;
      } else if (trimmed.match(/^\d{4}-\d{2}-\d{2}$/)) {
        structure.coverInfo.date = trimmed;
      } else if (trimmed.toLowerCase().includes('table of contents') || trimmed.startsWith('## Table of Contents')) {
        section = 'toc';
      }
      i++;
      continue;
    }

    // Detect TOC section
    if (section === 'toc') {
      if (trimmed.startsWith('## Revision History') || trimmed.toLowerCase().includes('revision history')) {
        section = 'revision';
        i++;
        continue;
      } else if (trimmed.startsWith('## 1') || trimmed.startsWith('## 1.')) {
        // Skip TOC, enter main content
        section = 'main';
        continue;  // Don't i++, let main section handle this line
      }
      structure.tocLines.push(line);
      i++;
      continue;
    }

    // Detect revision history
    if (section === 'revision') {
      if (trimmed.startsWith('## 1') || (trimmed.startsWith('## ') && !trimmed.toLowerCase().includes('revision'))) {
        section = 'main';
        continue;  // Don't i++, let main section handle this line
      }
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        structure.revisionHistory.push(line);
      }
      i++;
      continue;
    }

    // Main content
    if (section === 'main') {
      structure.mainContent.push(line);
    }
    i++;
  }

  return structure;
}

/**
 * Create cover page elements
 */
function createCoverPage(coverInfo) {
  const elements = [];

  // Empty spacing
  for (let i = 0; i < 6; i++) {
    elements.push(new Paragraph({ children: [] }));
  }

  // Main title
  elements.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [new TextRun({
      text: coverInfo.title || 'Document Title',
      bold: true,
      size: 56,
      font: getFont(coverInfo.title)
    })]
  }));

  // Subtitle
  if (coverInfo.subtitle) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [new TextRun({
        text: `For ${coverInfo.subtitle}`,
        size: 36,
        font: getFont(coverInfo.subtitle)
      })]
    }));
  }

  // Empty spacing
  for (let i = 0; i < 4; i++) {
    elements.push(new Paragraph({ children: [] }));
  }

  // Version
  if (coverInfo.version) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: `Version ${coverInfo.version}`, size: 28, font: FONT_EN })]
    }));
  }

  // Author
  if (coverInfo.author) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: `Prepared by ${coverInfo.author}`, size: 28, font: FONT_EN })]
    }));
  }

  // Organization
  if (coverInfo.organization) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: coverInfo.organization, size: 28, font: FONT_EN })]
    }));
  }

  // Date
  if (coverInfo.date) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: coverInfo.date, size: 28, font: FONT_EN })]
    }));
  }

  return elements;
}

/**
 * Extract heading structure from main content
 */
function extractHeadings(mainContent) {
  const headings = [];
  const lines = mainContent.split('\n');

  for (const line of lines) {
    // Match ## to #### headings (excluding requirement item headings)
    const h2Match = line.match(/^##\s+(.+)$/);
    const h3Match = line.match(/^###\s+(.+)$/);
    const h4Match = line.match(/^####\s+(.+)$/);

    if (h2Match && !isRequirementHeading(line)) {
      headings.push({ level: 2, text: h2Match[1].trim() });
    } else if (h3Match && !isRequirementHeading(line)) {
      headings.push({ level: 3, text: h3Match[1].trim() });
    } else if (h4Match && !isRequirementHeading(line)) {
      headings.push({ level: 4, text: h4Match[1].trim() });
    }
  }

  return headings;
}

/**
 * Create TOC page elements
 * Uses Word native TOC feature, need to press F9 or right-click "Update Field" to show page numbers after opening document
 */
function createTocPage() {
  const elements = [];

  // TOC title
  elements.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 300 },
    children: [new TextRun({ text: 'Table of Contents', bold: true, size: FONT_SIZE.H1, font: FONT_EN })]
  }));

  // Use Word native TOC feature (includes page numbers)
  elements.push(new TableOfContents('Table of Contents', {
    hyperlink: true,
    headingStyleRange: '1-4',
    stylesWithLevels: [
      { styleName: 'Heading 1', level: 1 },
      { styleName: 'Heading 2', level: 2 },
      { styleName: 'Heading 3', level: 3 },
      { styleName: 'Heading 4', level: 4 }
    ]
  }));

  // Hint message
  elements.push(new Paragraph({
    spacing: { before: 400 },
    children: [new TextRun({
      text: '※ Please press F9 in Word or right-click and select "Update Field" to display TOC contents and page numbers',
      italics: true,
      size: FONT_SIZE.SMALL,
      color: '888888',
      font: FONT_EN
    })]
  }));

  return elements;
}

/**
 * Create revision history page
 */
function createRevisionHistoryPage(revisionLines) {
  const elements = [];

  elements.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 300 },
    children: [new TextRun({ text: 'Revision History', bold: true, size: 32, font: FONT_EN })]
  }));

  if (revisionLines.length > 0) {
    // Parse revision history table
    const headers = [];
    const rows = [];
    let isHeader = true;

    for (const line of revisionLines) {
      if (line.includes('---')) {
        isHeader = false;
        continue;
      }
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      if (isHeader && headers.length === 0) {
        headers.push(...cells);
        isHeader = false;
      } else if (cells.length > 0) {
        rows.push(cells);
      }
    }

    if (headers.length > 0) {
      elements.push(createTable(headers, rows));
    }
  }

  return elements;
}

async function convertMdToDocx(inputPath, outputPath, docTitle) {
  console.log(`Converting ${inputPath}...`);
  const content = fs.readFileSync(inputPath, 'utf8');
  const outputDir = path.dirname(outputPath);

  // Parse document structure
  const structure = parseDocumentStructure(content, outputDir);

  // Parse main content
  const mainContentText = structure.mainContent.join('\n');
  const mainElements = parseMarkdown(mainContentText, outputDir).flat();

  // Page margin settings
  const pageMargins = { top: 1440, right: 1440, bottom: 1440, left: 1440 };

  // Create headers and footers
  const defaultHeader = new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: docTitle, italics: true, size: FONT_SIZE.FOOTER, color: '666666', font: FONT_EN })]
    })]
  });

  const defaultFooter = new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: 'Page ', size: FONT_SIZE.FOOTER, font: FONT_EN }),
        new TextRun({ children: [PageNumber.CURRENT], size: FONT_SIZE.FOOTER }),
        new TextRun({ text: ' of ', size: FONT_SIZE.FOOTER, font: FONT_EN }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: FONT_SIZE.FOOTER })
      ]
    })]
  });

  const doc = new Document({
    features: { updateFields: true },  // Auto-update TOC
    styles: {
      default: { document: { run: { font: FONT_EN, size: 24 } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 32, bold: true }, paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 28, bold: true }, paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 26, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
        { id: 'Heading4', name: 'Heading 4', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 24, bold: true }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 3 } },
        { id: 'Heading5', name: 'Heading 5', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 22, bold: true }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 4 } }
      ]
    },
    sections: [
      // Section 1: Cover page (no header/footer)
      {
        properties: { page: { margin: pageMargins } },
        children: createCoverPage(structure.coverInfo)
      },
      // Section 2: TOC page
      {
        properties: { page: { margin: pageMargins } },
        headers: { default: defaultHeader },
        footers: { default: defaultFooter },
        children: createTocPage()
      },
      // Section 3: Revision history page
      {
        properties: { page: { margin: pageMargins } },
        headers: { default: defaultHeader },
        footers: { default: defaultFooter },
        children: createRevisionHistoryPage(structure.revisionHistory)
      },
      // Section 4: Main content
      {
        properties: { page: { margin: pageMargins } },
        headers: { default: defaultHeader },
        footers: { default: defaultFooter },
        children: mainElements
      }
    ]
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created ${outputPath} (${Math.round(buffer.length/1024)} KB)`);

  // Clean up Mermaid temp files
  cleanupMermaidTemp(outputDir);
}

// Usage example
// convertMdToDocx('SRS-Project-1.0.md', 'SRS-Project-1.0.docx', 'SRS-Project-1.0');

module.exports = { convertMdToDocx, cleanupMermaidTemp };
```

### 3. Batch Conversion

Create batch conversion script `convert-all.js`:

```javascript
const { convertMdToDocx } = require('./md-to-docx');
const path = require('path');
const fs = require('fs');

const basePath = process.cwd();

const files = [
  { dir: '01-requirements/SRS', prefix: 'SRS' },
  { dir: '02-design/SDD', prefix: 'SDD' },
  { dir: '02-design/SWD', prefix: 'SWD' },
  { dir: '04-testing/STP', prefix: 'STP' },
  { dir: '04-testing/STC', prefix: 'STC' },
  { dir: '05-validation/SVV', prefix: 'SVV' },
  { dir: '05-validation/RTM', prefix: 'RTM' }
];

async function convertAll() {
  for (const file of files) {
    const dirPath = path.join(basePath, file.dir);
    if (!fs.existsSync(dirPath)) continue;

    const mdFiles = fs.readdirSync(dirPath).filter(f => f.endsWith('.md') && f.startsWith(file.prefix));

    for (const mdFile of mdFiles) {
      const mdPath = path.join(dirPath, mdFile);
      const docxPath = mdPath.replace('.md', '.docx');
      const docTitle = mdFile.replace('.md', '');

      // Check if update needed
      if (fs.existsSync(docxPath)) {
        const mdStat = fs.statSync(mdPath);
        const docxStat = fs.statSync(docxPath);
        if (docxStat.mtime >= mdStat.mtime) {
          console.log(`Skip ${mdFile} (in sync)`);
          continue;
        }
      }

      await convertMdToDocx(mdPath, docxPath, docTitle);
    }
  }
}

convertAll();
```

## Sync Status Check

Check if MD and DOCX are in sync:

```bash
# Check single file
ls -la {document}.md {document}.docx

# Batch check
find . -name "*.md" -exec sh -c 'docx="${1%.md}.docx"; if [ -f "$docx" ]; then if [ "$1" -nt "$docx" ]; then echo "Needs update: $docx"; fi; else echo "Missing: $docx"; fi' _ {} \;
```

## Document Format Specification

Generated DOCX documents include:

| Element | Format |
|---------|--------|
| Heading 1 (H1) | 18pt Bold (Chinese: Yuan Gothic, English: Arial) |
| Heading 2 (H2) | 16pt Bold |
| Heading 3 (H3) | 14pt Bold |
| Heading 4 (H4) | 13pt Bold |
| Heading 5 (H5) | 12pt Bold |
| Body | 11pt |
| Table content | 10pt |
| Table header | 10pt Bold, light blue background |
| Code | Courier New 10pt, gray background |
| Header/Footer | 9pt |
| Margins | 1 inch (all sides) |
| **Mermaid diagrams** | PNG image, centered, maintain original aspect ratio (max width 450px) |

## Mermaid Diagram Support

The converter automatically renders Mermaid code blocks in Markdown to PNG images and embeds them in the DOCX file.

### Supported Mermaid Diagram Types

| Type | Example |
|------|---------|
| Flowchart | `flowchart TD`, `flowchart LR`, `graph TB` |
| Sequence diagram | `sequenceDiagram` |
| Class diagram | `classDiagram` |
| State diagram | `stateDiagram-v2` |
| Gantt chart | `gantt` |
| Pie chart | `pie` |
| ER diagram | `erDiagram` |

### Usage Example

In Markdown file:

````markdown
```mermaid
flowchart TD
    A[Start] --> B{Condition}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```
````

After conversion, it will display as an image in the DOCX.

### Notes

1. **Dependency Installation**: Need to globally install `@mermaid-js/mermaid-cli`
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Render Failure Handling**: If Mermaid rendering fails (syntax error or environment issues), will fallback to display as code block

3. **Temp Files**: Conversion process creates `.mermaid-temp` folder in output directory, automatically cleaned up after completion

4. **Image Size**: Automatically reads original dimensions and maintains aspect ratio, max width 450px, max height 500px, prevents image distortion

---

## Alternative: Pandoc + SVG (Recommended)

For documents with many Mermaid diagrams, the Pandoc approach is recommended, which produces higher quality vector graphics.

### Issue: SVG Text Not Displaying

Mermaid's default SVG output uses `<foreignObject>` to embed HTML for text rendering, but **Microsoft Word doesn't support foreignObject**, causing text in diagrams to not display.

### Solution: PDF→SVG Conversion Pipeline

By using PDF as an intermediate format, text is converted to vector paths, allowing Word to display correctly:

```
Mermaid Code → PDF (mmdc --pdfFit) → SVG (pdf2svg) → Word Compatible
```

### Dependency Installation

```bash
# macOS
brew install pdf2svg
npm install -g @mermaid-js/mermaid-cli

# Ubuntu/Debian
sudo apt install pdf2svg
npm install -g @mermaid-js/mermaid-cli
```

### Hybrid Conversion Script (convert-hybrid.py)

This script automatically selects the best format based on diagram type:
- **block-beta** diagrams → PNG (better layout rendering)
- **Other diagrams** → SVG via PDF (vector text, scalable)

```python
#!/usr/bin/env python3
"""
MD to DOCX Converter with Hybrid Image Format.
- block-beta diagrams → PNG (better layout rendering)
- Other diagrams → SVG via PDF (native text for Word)
"""
import re
import subprocess
import os
from pathlib import Path

# PNG settings for block-beta wireframes (mobile wireframe size)
PNG_WIDTH = 375   # Mobile screen width
PNG_HEIGHT = 812  # Mobile screen height (iPhone X ratio)
PNG_SCALE = 3     # 3x for retina quality

def get_diagram_type(mermaid_code):
    """Detect mermaid diagram type."""
    code = mermaid_code.strip()
    if code.startswith('block-beta'):
        return 'block-beta'
    elif code.startswith('flowchart') or code.startswith('graph'):
        return 'flowchart'
    elif code.startswith('sequenceDiagram'):
        return 'sequence'
    elif code.startswith('classDiagram'):
        return 'class'
    elif code.startswith('stateDiagram'):
        return 'state'
    elif code.startswith('erDiagram'):
        return 'er'
    else:
        return 'other'

def extract_and_convert_mermaid(md_file, output_dir):
    """Extract mermaid blocks and convert based on diagram type."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'```mermaid\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    print(f"Found {len(matches)} mermaid diagrams")
    print(f"Strategy: block-beta → PNG, others → SVG (via PDF)")
    print("-" * 50)

    results = []  # Store (index, format, success)

    for i, mermaid_code in enumerate(matches, 1):
        diagram_type = get_diagram_type(mermaid_code)
        mmd_file = os.path.join(output_dir, f'diagram_{i:03d}.mmd')

        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_code.strip())

        if diagram_type == 'block-beta':
            # Use PNG for block-beta (wireframes)
            success = convert_to_png(mmd_file, output_dir, i)
            results.append((i, 'png', success))
        else:
            # Use SVG via PDF for other diagrams
            success = convert_to_svg_via_pdf(mmd_file, output_dir, i)
            results.append((i, 'svg', success))

        # Cleanup temp file
        if os.path.exists(mmd_file):
            os.remove(mmd_file)

    # Summary
    png_count = sum(1 for r in results if r[1] == 'png' and r[2])
    svg_count = sum(1 for r in results if r[1] == 'svg' and r[2])
    failed = sum(1 for r in results if not r[2])

    print("-" * 50)
    print(f"Results: {png_count} PNG + {svg_count} SVG = {png_count + svg_count} success, {failed} failed")

    return results

def convert_to_png(mmd_file, output_dir, index):
    """Convert mermaid to high-res PNG."""
    png_file = os.path.join(output_dir, f'diagram_{index:03d}.png')

    try:
        result = subprocess.run(
            [
                'mmdc', '-i', mmd_file, '-o', png_file,
                '-w', str(PNG_WIDTH),
                '-H', str(PNG_HEIGHT),
                '-s', str(PNG_SCALE),
                '-b', 'white'
            ],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0 and os.path.exists(png_file):
            size_kb = os.path.getsize(png_file) / 1024
            print(f"  [{index:03d}] ✓ PNG ({size_kb:.0f} KB) - block-beta")
            return True
        else:
            error = result.stderr[:50] if result.stderr else 'Unknown'
            print(f"  [{index:03d}] ✗ PNG failed: {error}")
            return False
    except Exception as e:
        print(f"  [{index:03d}] ✗ PNG error: {e}")
        return False

def convert_to_svg_via_pdf(mmd_file, output_dir, index):
    """Convert mermaid to SVG via PDF (native text)."""
    pdf_file = os.path.join(output_dir, f'diagram_{index:03d}.pdf')
    svg_file = os.path.join(output_dir, f'diagram_{index:03d}.svg')

    try:
        # Step 1: Generate PDF with pdfFit and larger page size for tall diagrams
        result = subprocess.run(
            ['mmdc', '-i', mmd_file, '-o', pdf_file, '-b', 'white',
             '-w', '800', '-H', '2000', '-f', '--pdfFit'],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0 or not os.path.exists(pdf_file):
            error = result.stderr[:50] if result.stderr else 'Unknown'
            print(f"  [{index:03d}] ✗ PDF failed: {error}")
            return False

        # Step 2: Convert PDF to SVG
        result2 = subprocess.run(
            ['pdf2svg', pdf_file, svg_file],
            capture_output=True, text=True, timeout=30
        )

        if result2.returncode == 0 and os.path.exists(svg_file):
            size_kb = os.path.getsize(svg_file) / 1024
            print(f"  [{index:03d}] ✓ SVG ({size_kb:.0f} KB)")
            os.remove(pdf_file)  # Cleanup PDF
            return True
        else:
            print(f"  [{index:03d}] ✗ SVG conversion failed")
            return False

    except Exception as e:
        print(f"  [{index:03d}] ✗ Error: {e}")
        return False

def replace_mermaid_with_images(md_file, output_dir, output_md, results):
    """Replace mermaid blocks with image references."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'```mermaid\n(.*?)```'
    result_iter = iter(results)

    def replace_with_image(match):
        try:
            idx, fmt, success = next(result_iter)
        except StopIteration:
            return match.group(0)

        if not success:
            return f'```\n[Diagram {idx}: Conversion failed]\n```'

        img_file = f'mermaid-images/diagram_{idx:03d}.{fmt}'

        # Check file exists
        full_path = os.path.join(os.path.dirname(md_file), 'mermaid-images', f'diagram_{idx:03d}.{fmt}')
        if not os.path.exists(full_path):
            return f'```\n[Diagram {idx}: File not found]\n```'

        # Set appropriate width based on format
        if fmt == 'png':
            # PNG wireframes: mobile size (3 inches)
            return f'![Diagram {idx}]({img_file}){{ width=3in }}'
        else:
            # SVG diagrams: check aspect ratio and set appropriate size
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(full_path)
                root = tree.getroot()
                width = root.get('width', '100pt').replace('pt', '')
                height = root.get('height', '100pt').replace('pt', '')
                w, h = float(width), float(height)
                aspect = h / w if w > 0 else 1

                if aspect > 2:
                    # Tall diagram: use smaller width to fit page
                    return f'![Diagram {idx}]({img_file}){{ width=3in }}'
                elif aspect > 1.2:
                    # Medium tall: moderate width
                    return f'![Diagram {idx}]({img_file}){{ width=4in }}'
                else:
                    # Wide or square: full width
                    return f'![Diagram {idx}]({img_file}){{ width=5.5in }}'
            except:
                return f'![Diagram {idx}]({img_file}){{ width=5in }}'

    modified_content = re.sub(pattern, replace_with_image, content, flags=re.DOTALL)

    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    print(f"Created {output_md}")

def convert_to_docx(input_md, output_docx):
    """Convert markdown to docx using pandoc."""
    print(f"Converting to DOCX...")

    try:
        result = subprocess.run(
            [
                'pandoc', input_md,
                '-o', output_docx,
                '--from', 'markdown',
                '--to', 'docx',
                '--resource-path', os.path.dirname(input_md),
                '--standalone',
                '--toc',
                '--toc-depth=3'
            ],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            size_mb = os.path.getsize(output_docx) / (1024 * 1024)
            print(f"✅ Created: {output_docx} ({size_mb:.1f} MB)")

            # Remove quarantine on macOS
            subprocess.run(
                ['xattr', '-d', 'com.apple.quarantine', output_docx],
                capture_output=True
            )
        else:
            print(f"❌ Pandoc error: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python convert-hybrid.py <markdown_file>")
        sys.exit(1)

    md_file = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(md_file))
    base_name = os.path.splitext(os.path.basename(md_file))[0]

    output_dir = os.path.join(base_dir, 'mermaid-images')
    temp_md = os.path.join(base_dir, f'{base_name}_temp.md')
    output_docx = os.path.join(base_dir, f'{base_name}.docx')

    # Step 1: Convert mermaid diagrams
    print("=" * 60)
    print("Step 1: Converting Mermaid Diagrams (Hybrid Format)")
    print("=" * 60)
    results = extract_and_convert_mermaid(md_file, output_dir)

    # Step 2: Create modified markdown
    print("\n" + "=" * 60)
    print("Step 2: Creating Markdown with Image References")
    print("=" * 60)
    replace_mermaid_with_images(md_file, output_dir, temp_md, results)

    # Step 3: Convert to DOCX
    print("\n" + "=" * 60)
    print("Step 3: Converting to DOCX")
    print("=" * 60)
    convert_to_docx(temp_md, output_docx)

    # Cleanup
    if os.path.exists(temp_md):
        os.remove(temp_md)

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
    print(f"   Images: {output_dir}/")
    print(f"   DOCX: {output_docx}")

if __name__ == '__main__':
    main()
```

### Usage

```bash
# Convert single document
python convert-hybrid.py SDD-Project-1.0.md

# Output:
#   mermaid-images/diagram_001.svg
#   mermaid-images/diagram_002.png
#   ...
#   SDD-Project-1.0.docx
```

---

## Mermaid Diagram Best Practices

### 1. Avoid ASCII Art

**Don't use plain text ASCII diagrams:**
```
┌─────────────┐     ┌─────────────┐
│   State A   │────>│   State B   │
└─────────────┘     └─────────────┘
```

**Use Mermaid syntax instead:**
```mermaid
stateDiagram-v2
    StateA --> StateB
```

### 2. Use stateDiagram-v2 for State Machines

```mermaid
stateDiagram-v2
    [*] --> Initial
    Initial --> Loading: initState()

    Loading --> Error: Network Error
    Loading --> Success: Load Success
    Loading --> Empty: No Data

    Error --> Loading: Retry
    Success --> Loading: Pull to Refresh

    state Playing {
        [*] --> Waiting
        Waiting --> Active: Start
        Active --> Waiting: Complete
    }
```

### 3. Use Horizontal Layout for Tab Navigation

**Avoid vertical stretching:**
```mermaid
flowchart LR
    subgraph MainTabNavigator["Main Tab Navigator"]
        direction LR
        HomeTab["🏠 Home"]
        TrainTab["🎮 Train"]
        TherapyTab["🌙 Therapy"]
        DeviceTab["⚡ Device"]
        SettingTab["⚙️ Setting"]
    end
```

### 4. Block-Beta Wireframe Best Practices

```mermaid
block-beta
    columns 1

    block:header
        columns 3
        back["←"] title["Screen Title"] menu["⋮"]
    end

    block:content
        columns 1
        space
        card1["Content Card 1"]
        card2["Content Card 2"]
        space
    end

    block:footer
        columns 5
        tab1["🏠"] tab2["🎮"] tab3["🌙"] tab4["⚡"] tab5["⚙️"]
    end
```

### 5. Recommended Diagram Widths

| Diagram Type | Recommended Width | Description |
|--------------|-------------------|-------------|
| block-beta (wireframe) | 3 inches | Simulates mobile screen width |
| Tall diagram (aspect > 2) | 3 inches | Prevents excessive width causing truncation |
| Medium diagram (aspect 1.2-2) | 4 inches | Balances readability |
| Wide diagram (aspect < 1.2) | 5.5 inches | Utilizes page width |

---

## Troubleshooting

### Q1: SVG Displays Blank in Word

**Cause:** Mermaid defaults to using `<foreignObject>` for text rendering, which Word doesn't support.

**Solution:** Use PDF→SVG conversion pipeline (see convert-hybrid.py above).

### Q2: Diagram Gets Cropped or Stretched

**Cause:** Diagram is too tall or wide, exceeding page bounds.

**Solution:**
1. Specify appropriate width in Pandoc image syntax
2. Use `--pdfFit` parameter to let mmdc auto-adjust PDF size
3. For tall diagrams, use smaller width (3-4 inches)

### Q3: macOS Cannot Open DOCX (Quarantine Warning)

**Solution:**
```bash
xattr -d com.apple.quarantine <file>.docx
```

### Q4: block-beta Diagram Layout Issues

**Cause:** block-beta is sensitive to columns settings.

**Solution:**
1. Ensure columns settings are consistent within each block
2. Avoid using too many columns in header (recommend 3-5)
3. Use PNG format for block-beta diagrams
