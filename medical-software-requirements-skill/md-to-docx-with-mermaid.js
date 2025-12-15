#!/usr/bin/env node
/**
 * MD to DOCX Converter with Mermaid Support
 *
 * Features:
 * 1. Parse Markdown documents
 * 2. Render Mermaid diagrams as PNG images
 * 3. Generate DOCX documents with embedded images
 *
 * Usage:
 *   node md-to-docx-with-mermaid.js SDD-SomniLand-1.0.md
 *
 * Dependencies:
 *   npm install docx
 *   npm install -g @mermaid-js/mermaid-cli
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, ShadingType, PageNumber, LevelFormat, PageBreak,
        TableOfContents, ImageRun } = require('docx');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const INPUT_FILE = process.argv[2] || 'SDD-SomniLand-1.0.md';
const OUTPUT_FILE = process.argv[3] || INPUT_FILE.replace('.md', '.docx');
const MERMAID_OUTPUT_DIR = './mermaid-images';
const DRAWIO_OUTPUT_DIR = './drawio-diagrams';

// Image settings - ULTRA HIGH RESOLUTION for print quality
// Strategy: Render at VERY HIGH resolution, display at normal size in DOCX
// This ensures sharp images even when zoomed to 400% or printed
const MERMAID_WIDTH = 2400;      // PNG render width (super high resolution)
const MERMAID_HEIGHT = 1800;     // PNG render height (super high resolution)
const MERMAID_SCALE = 3;         // 3x scaling (print quality)
const DOCX_IMAGE_WIDTH = 480;    // DOCX display width (A4 suitable, approx 6.5 inches)
const DOCX_IMAGE_HEIGHT = 360;   // DOCX display height (auto aspect ratio adjustment)
const USE_SVG_DEFAULT = true;    // Also generate SVG (for future editing)
// Note: docx npm library currently doesn't support native SVG embedding
// SVG files for future editing with draw.io/Inkscape, DOCX embeds high resolution PNG

// Styles
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const headerShading = { fill: "2c5282", type: ShadingType.CLEAR };

// Ensure output directories exist
if (!fs.existsSync(MERMAID_OUTPUT_DIR)) {
    fs.mkdirSync(MERMAID_OUTPUT_DIR, { recursive: true });
}
if (!fs.existsSync(DRAWIO_OUTPUT_DIR)) {
    fs.mkdirSync(DRAWIO_OUTPUT_DIR, { recursive: true });
}

// Generate draw.io XML from Mermaid code
function generateDrawioXml(mermaidCode, index) {
    const drawioPath = path.join(DRAWIO_OUTPUT_DIR, `diagram-${index}.drawio`);

    // Parse mermaid to extract nodes and edges
    const nodes = [];
    const edges = [];
    let nodeId = 1;
    const nodeMap = {};

    const lines = mermaidCode.split('\n');
    for (const line of lines) {
        // Match node definitions: A["Label"] or A[Label]
        const nodeMatch = line.match(/^\s*(\w+)\s*\[\s*["']?([^"'\]]+)["']?\s*\]/);
        if (nodeMatch) {
            const [, id, label] = nodeMatch;
            if (!nodeMap[id]) {
                nodeMap[id] = nodeId++;
                nodes.push({ id: nodeMap[id], label: label.trim() });
            }
        }

        // Match edges: A --> B or A -->|label| B
        const edgeMatch = line.match(/(\w+)\s*--?>?\|?([^|]*)\|?\s*(\w+)/);
        if (edgeMatch) {
            const [, from, label, to] = edgeMatch;
            if (!nodeMap[from]) { nodeMap[from] = nodeId++; nodes.push({ id: nodeMap[from], label: from }); }
            if (!nodeMap[to]) { nodeMap[to] = nodeId++; nodes.push({ id: nodeMap[to], label: to }); }
            edges.push({ from: nodeMap[from], to: nodeMap[to], label: label?.trim() || '' });
        }
    }

    // Generate draw.io XML
    const cellsXml = [];
    let x = 80, y = 80;

    for (const node of nodes) {
        cellsXml.push(`      <mxCell id="${node.id + 1}" value="${escapeXml(node.label)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
        <mxGeometry x="${x}" y="${y}" width="120" height="60" as="geometry"/>
      </mxCell>`);
        x += 160;
        if (x > 600) { x = 80; y += 100; }
    }

    for (let i = 0; i < edges.length; i++) {
        const edge = edges[i];
        cellsXml.push(`      <mxCell id="${nodes.length + i + 2}" value="${escapeXml(edge.label)}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="${edge.from + 1}" target="${edge.to + 1}">
        <mxGeometry relative="1" as="geometry"/>
      </mxCell>`);
    }

    const drawioXml = `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="${new Date().toISOString()}" type="device">
  <diagram name="Diagram ${index + 1}" id="diagram-${index}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
${cellsXml.join('\n')}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;

    fs.writeFileSync(drawioPath, drawioXml);
}

function escapeXml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

console.log(`Reading ${INPUT_FILE}...`);
const markdown = fs.readFileSync(INPUT_FILE, 'utf-8');

// Extract and render all Mermaid diagrams
const mermaidRegex = /```mermaid\n([\s\S]*?)```/g;
const mermaidDiagrams = [];
let match;
let diagramIndex = 0;

console.log('Extracting Mermaid diagrams...');
while ((match = mermaidRegex.exec(markdown)) !== null) {
    const mermaidCode = match[1].trim();
    const outputPath = path.join(MERMAID_OUTPUT_DIR, `diagram-${diagramIndex}.png`);
    const inputPath = path.join(MERMAID_OUTPUT_DIR, `diagram-${diagramIndex}.mmd`);

    mermaidDiagrams.push({
        index: diagramIndex,
        code: mermaidCode,
        fullMatch: match[0],
        outputPath: outputPath,
        inputPath: inputPath
    });
    diagramIndex++;
}

console.log(`Found ${mermaidDiagrams.length} Mermaid diagrams. Rendering...`);

// Render each Mermaid diagram to SVG (default) and PNG
const renderedImages = {};
for (const diagram of mermaidDiagrams) {
    try {
        // Write mermaid code to temp file
        fs.writeFileSync(diagram.inputPath, diagram.code);

        const svgPath = diagram.outputPath.replace('.png', '.svg');
        const pngPath = diagram.outputPath;

        // Always generate SVG first (for editing in draw.io/Inkscape)
        const svgCmd = `mmdc -i "${diagram.inputPath}" -o "${svgPath}" -b white 2>/dev/null`;
        try {
            execSync(svgCmd, { stdio: 'pipe' });
        } catch (e) {
            console.log(`  ⚠ SVG generation failed for diagram ${diagram.index + 1}`);
        }

        // Generate PNG for DOCX embedding (reasonable size, not enlarged)
        const pngCmd = `mmdc -i "${diagram.inputPath}" -o "${pngPath}" -w ${MERMAID_WIDTH} -H ${MERMAID_HEIGHT} -s ${MERMAID_SCALE} -b white 2>/dev/null`;
        execSync(pngCmd, { stdio: 'pipe' });

        // Generate draw.io XML for editing
        generateDrawioXml(diagram.code, diagram.index);

        if (fs.existsSync(pngPath)) {
            renderedImages[diagram.fullMatch] = pngPath;
            const svgExists = fs.existsSync(svgPath) ? ' + SVG' : '';
            console.log(`  ✓ Rendered diagram ${diagram.index + 1}/${mermaidDiagrams.length}${svgExists}`);
        } else {
            console.log(`  ✗ Failed to render diagram ${diagram.index + 1}`);
        }

        // Clean up temp file
        if (fs.existsSync(diagram.inputPath)) {
            fs.unlinkSync(diagram.inputPath);
        }
    } catch (error) {
        console.log(`  ✗ Error rendering diagram ${diagram.index + 1}: ${error.message}`);
    }
}

console.log(`\nSuccessfully rendered ${Object.keys(renderedImages).length} diagrams.`);

// Parse Markdown and build DOCX
console.log('\nBuilding DOCX...');

const lines = markdown.split('\n');
const children = [];

// Helper: Create paragraph with text runs
function createParagraph(text, options = {}) {
    const runs = [];

    // Handle bold text **text**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    for (const part of parts) {
        if (part.startsWith('**') && part.endsWith('**')) {
            runs.push(new TextRun({ text: part.slice(2, -2), bold: true }));
        } else if (part) {
            runs.push(new TextRun({ text: part }));
        }
    }

    return new Paragraph({
        ...options,
        children: runs.length > 0 ? runs : [new TextRun(text)]
    });
}

// Helper: Create code block
function createCodeBlock(code) {
    return new Table({
        columnWidths: [9000],
        rows: [new TableRow({
            children: [new TableCell({
                borders: cellBorders,
                shading: { fill: "f7fafc", type: ShadingType.CLEAR },
                children: code.split('\n').map(line => new Paragraph({
                    spacing: { before: 20, after: 20 },
                    children: [new TextRun({ text: line, font: "Courier New", size: 18 })]
                }))
            })]
        })]
    });
}

// Helper: Get image dimensions from PNG file
function getImageDimensions(imagePath) {
    try {
        const buffer = fs.readFileSync(imagePath);
        // PNG header: width at bytes 16-19, height at bytes 20-23 (big-endian)
        if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
            const width = buffer.readUInt32BE(16);
            const height = buffer.readUInt32BE(20);
            return { width, height };
        }
    } catch (e) {}
    return null;
}

// Helper: Create image from file (auto-scale to fit A4, no enlargement)
function createImage(imagePath, caption = '') {
    try {
        const imageBuffer = fs.readFileSync(imagePath);
        const elements = [];

        // Get actual image dimensions
        const dims = getImageDimensions(imagePath);
        let displayWidth = DOCX_IMAGE_WIDTH;
        let displayHeight = DOCX_IMAGE_HEIGHT;

        if (dims) {
            const aspectRatio = dims.width / dims.height;
            const maxWidth = DOCX_IMAGE_WIDTH;  // A4 max width (~6 inches)
            const maxHeight = 400;               // Max height to prevent page overflow

            // Scale down if needed, but never scale up
            if (dims.width > maxWidth) {
                displayWidth = maxWidth;
                displayHeight = Math.round(maxWidth / aspectRatio);
            } else {
                // Use original size (scaled for DOCX points)
                displayWidth = Math.min(dims.width * 0.6, maxWidth);
                displayHeight = Math.round(displayWidth / aspectRatio);
            }

            // Ensure height doesn't exceed max
            if (displayHeight > maxHeight) {
                displayHeight = maxHeight;
                displayWidth = Math.round(maxHeight * aspectRatio);
            }
        }

        elements.push(new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 200, after: 100 },
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
        }));

        if (caption) {
            elements.push(new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 },
                children: [new TextRun({ text: caption, italics: true, size: 18, color: "666666" })]
            }));
        }

        return elements;
    } catch (error) {
        return [new Paragraph({
            shading: { fill: "fff3cd", type: ShadingType.CLEAR },
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: `[Image Load Failed: ${path.basename(imagePath)}]`, italics: true, color: "856404" })]
        })];
    }
}

// Helper: Parse markdown table
function parseMarkdownTable(tableLines) {
    const rows = [];
    let isHeader = true;

    for (const line of tableLines) {
        if (line.startsWith('|---') || line.startsWith('| ---')) {
            isHeader = false;
            continue;
        }

        const cells = line.split('|')
            .filter((cell, i, arr) => i > 0 && i < arr.length - 1)
            .map(cell => cell.trim());

        if (cells.length > 0) {
            rows.push({ cells, isHeader: isHeader && rows.length === 0 });
        }

        if (isHeader && rows.length > 0) isHeader = false;
    }

    return rows;
}

// Helper: Create table from parsed rows
function createTable(parsedRows) {
    if (parsedRows.length === 0) return null;

    const colCount = parsedRows[0].cells.length;
    const colWidth = Math.floor(9000 / colCount);

    return new Table({
        columnWidths: Array(colCount).fill(colWidth),
        rows: parsedRows.map((row, rowIdx) => new TableRow({
            tableHeader: row.isHeader,
            children: row.cells.map((text, cellIdx) => new TableCell({
                borders: cellBorders,
                shading: row.isHeader ? headerShading : undefined,
                children: [new Paragraph({
                    alignment: AlignmentType.LEFT,
                    children: [new TextRun({
                        text: text,
                        bold: row.isHeader || cellIdx === 0,
                        color: row.isHeader ? "FFFFFF" : undefined,
                        size: 20
                    })]
                })]
            }))
        }))
    });
}

// Process markdown line by line
let i = 0;
let inCodeBlock = false;
let inMermaidBlock = false;
let codeBlockContent = [];
let mermaidContent = [];
let inTable = false;
let tableLines = [];
let currentMermaidIndex = 0;

// Add title page
children.push(
    new Paragraph({
        heading: HeadingLevel.TITLE,
        alignment: AlignmentType.CENTER,
        spacing: { before: 2000, after: 400 },
        children: [new TextRun({ text: "Software Design Specification (SDD)", size: 56, bold: true, color: "1a365d" })]
    }),
    new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Software Design Description", italics: true, size: 28 })]
    }),
    new Paragraph({ spacing: { before: 400 } })
);

// Document Information from YAML front matter or defaults
const docInformation = {
    docId: 'SDD-SomniLand-1.0',
    project: 'SomniLand (iNAP Kids App)',
    version: '2.0',
    date: new Date().toISOString().split('T')[0],
    status: 'Draft',
    classification: 'Class B'
};

// Add document info table
children.push(new Table({
    columnWidths: [2500, 6500],
    rows: [
        ["Document ID", docInformation.docId],
        ["Project Name", docInformation.project],
        ["Version", docInformation.version],
        ["Date", docInformation.date],
        ["Status", docInformation.status],
        ["Safety Classification", docInformation.classification]
    ].map(([label, value]) => new TableRow({
        children: [
            new TableCell({
                borders: cellBorders,
                shading: { fill: "e8f4f8", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: label, bold: true })] })]
            }),
            new TableCell({
                borders: cellBorders,
                children: [new Paragraph({ children: [new TextRun(value)] })]
            })
        ]
    }))
}));

children.push(new Paragraph({ children: [new PageBreak()] }));

// Add Table of Contents
children.push(
    new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Table of Contents")] }),
    new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
    new Paragraph({ children: [new PageBreak()] })
);

// Process each line
while (i < lines.length) {
    const line = lines[i];

    // Skip YAML front matter
    if (i === 0 && line === '---') {
        while (i < lines.length && lines[++i] !== '---') {}
        i++;
        continue;
    }

    // Handle Mermaid code blocks
    if (line.trim() === '```mermaid') {
        inMermaidBlock = true;
        mermaidContent = [];
        i++;
        continue;
    }

    if (inMermaidBlock) {
        if (line.trim() === '```') {
            inMermaidBlock = false;

            // Find the corresponding rendered image
            const mermaidCode = mermaidContent.join('\n');
            const diagramPath = path.join(MERMAID_OUTPUT_DIR, `diagram-${currentMermaidIndex}.png`);

            if (fs.existsSync(diagramPath)) {
                const imageElements = createImage(diagramPath, `Diagram ${currentMermaidIndex + 1}`);
                children.push(...imageElements);
            } else {
                // Fallback: show code block placeholder
                children.push(new Paragraph({
                    shading: { fill: "e2e8f0", type: ShadingType.CLEAR },
                    alignment: AlignmentType.CENTER,
                    spacing: { before: 100, after: 100 },
                    children: [new TextRun({ text: `[Mermaid Diagram ${currentMermaidIndex + 1}]`, italics: true, color: "4a5568" })]
                }));
            }

            currentMermaidIndex++;
            mermaidContent = [];
        } else {
            mermaidContent.push(line);
        }
        i++;
        continue;
    }

    // Handle regular code blocks
    if (line.startsWith('```') && !inCodeBlock) {
        inCodeBlock = true;
        codeBlockContent = [];
        i++;
        continue;
    }

    if (inCodeBlock) {
        if (line.trim() === '```') {
            inCodeBlock = false;
            if (codeBlockContent.length > 0) {
                children.push(createCodeBlock(codeBlockContent.join('\n')));
            }
            codeBlockContent = [];
        } else {
            codeBlockContent.push(line);
        }
        i++;
        continue;
    }

    // Handle tables
    if (line.startsWith('|')) {
        if (!inTable) {
            inTable = true;
            tableLines = [];
        }
        tableLines.push(line);
        i++;
        continue;
    } else if (inTable) {
        inTable = false;
        const parsedRows = parseMarkdownTable(tableLines);
        const table = createTable(parsedRows);
        if (table) {
            children.push(table);
            children.push(new Paragraph({ spacing: { after: 200 } }));
        }
        tableLines = [];
    }

    // Handle headings
    if (line.startsWith('#')) {
        const headingMatch = line.match(/^(#{1,6})\s+(.+)/);
        if (headingMatch) {
            const level = headingMatch[1].length;
            const text = headingMatch[2];

            let headingLevel;
            switch (level) {
                case 1: headingLevel = HeadingLevel.HEADING_1; break;
                case 2: headingLevel = HeadingLevel.HEADING_2; break;
                case 3: headingLevel = HeadingLevel.HEADING_3; break;
                case 4: headingLevel = HeadingLevel.HEADING_4; break;
                default: headingLevel = HeadingLevel.HEADING_5;
            }

            children.push(new Paragraph({
                heading: headingLevel,
                children: [new TextRun(text)]
            }));
        }
        i++;
        continue;
    }

    // Handle blockquotes
    if (line.startsWith('>')) {
        const quoteText = line.replace(/^>\s*/, '');
        children.push(new Paragraph({
            shading: { fill: "f0f7ff", type: ShadingType.CLEAR },
            spacing: { before: 100, after: 100 },
            indent: { left: 400 },
            children: [new TextRun({ text: quoteText, italics: true })]
        }));
        i++;
        continue;
    }

    // Handle bullet points
    if (line.match(/^[-*]\s+/)) {
        const bulletText = line.replace(/^[-*]\s+/, '');
        children.push(new Paragraph({
            numbering: { reference: "bullet-list", level: 0 },
            children: [new TextRun(bulletText)]
        }));
        i++;
        continue;
    }

    // Handle numbered lists
    if (line.match(/^\d+\.\s+/)) {
        const listText = line.replace(/^\d+\.\s+/, '');
        children.push(new Paragraph({
            numbering: { reference: "number-list", level: 0 },
            children: [new TextRun(listText)]
        }));
        i++;
        continue;
    }

    // Handle horizontal rules
    if (line.match(/^---+$/)) {
        children.push(new Paragraph({
            spacing: { before: 200, after: 200 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" } }
        }));
        i++;
        continue;
    }

    // Handle page breaks (custom marker)
    if (line.includes('<!-- pagebreak -->') || line.includes('<div class="page-break">')) {
        children.push(new Paragraph({ children: [new PageBreak()] }));
        i++;
        continue;
    }

    // Handle regular paragraphs
    if (line.trim()) {
        children.push(createParagraph(line));
    } else {
        // Empty line = paragraph spacing
        children.push(new Paragraph({ spacing: { after: 100 } }));
    }

    i++;
}

// Handle any remaining table
if (inTable && tableLines.length > 0) {
    const parsedRows = parseMarkdownTable(tableLines);
    const table = createTable(parsedRows);
    if (table) children.push(table);
}

// Add document footer
children.push(
    new Paragraph({ spacing: { before: 600 } }),
    new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "— End of Document —", italics: true, color: "666666" })]
    })
);

// Create document
const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 22 } } },
        paragraphStyles: [
            { id: "Title", name: "Title", basedOn: "Normal",
                run: { size: 56, bold: true, color: "1a365d", font: "Arial" },
                paragraph: { spacing: { after: 300 }, alignment: AlignmentType.CENTER } },
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 32, bold: true, color: "1a365d", font: "Arial" },
                paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 28, bold: true, color: "2c5282", font: "Arial" },
                paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
            { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 24, bold: true, color: "2b6cb0", font: "Arial" },
                paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
            { id: "Heading4", name: "Heading 4", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 22, bold: true, color: "3182ce", font: "Arial" },
                paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 3 } },
            { id: "Heading5", name: "Heading 5", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: 20, bold: true, color: "4299e1", font: "Arial" },
                paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 4 } }
        ]
    },
    numbering: {
        config: [
            { reference: "bullet-list",
                levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
            { reference: "number-list",
                levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
        ]
    },
    sections: [{
        properties: {
            page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [new TextRun({ text: `${docInformation.docId} | v${docInformation.version}`, size: 18, color: "666666" })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "Page ", size: 18 }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
                        new TextRun({ text: " of ", size: 18 }),
                        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18 })
                    ]
                })]
            })
        },
        children: children
    }]
});

// Generate DOCX
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(OUTPUT_FILE, buffer);
    console.log(`\n✅ ${OUTPUT_FILE} created successfully!`);
    console.log(`   - Total diagrams rendered: ${Object.keys(renderedImages).length}`);
    console.log(`   - File size: ${(buffer.length / 1024).toFixed(1)} KB`);

    // Cleanup mermaid images (optional - comment out to keep)
    // console.log('\nCleaning up temporary files...');
    // fs.rmSync(MERMAID_OUTPUT_DIR, { recursive: true, force: true });
}).catch(error => {
    console.error('Error generating DOCX:', error);
    process.exit(1);
});
