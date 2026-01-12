const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
        ImageRun, TableOfContents, LevelFormat, convertInchesToTwip } = require('docx');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

// ============================================
// Font Settings - Chinese uses Microsoft JhengHei, English uses Arial
// ============================================
const FONT_CN = '微軟正黑體';  // Chinese font (Traditional/Simplified Chinese)
const FONT_EN = 'Arial';       // English font
const FONT_CODE = 'Consolas';  // Code font (monospace, better readability)

// Font size settings (unit: half-points, 24 = 12pt)
// Optimized for A4 pages and IEC 62304 document readability
const FONT_SIZE = {
  H1: 36,        // 18pt - Main title
  H2: 32,        // 16pt - Major section
  H3: 28,        // 14pt - Subsection
  H4: 26,        // 13pt - Sub-subsection
  H5: 24,        // 12pt - Details
  BODY: 22,      // 11pt - Body text
  TABLE: 22,     // 11pt - Table content (adjusted from 10pt for better readability)
  TABLE_HEADER: 22, // 11pt - Table header (bold, consistent with body)
  SMALL: 18,     // 9pt - Small text
  FOOTER: 18     // 9pt - Footer
};

/**
 * Check if text contains Chinese characters
 */
function containsChinese(text) {
  return /[\u4e00-\u9fff]/.test(text);
}

/**
 * Get appropriate font object (based on text content)
 * Returns font object format required by docx library, ensuring correct Chinese/English font separation
 */
function getFont(text) {
  // Use unified font settings regardless of content:
  // - English/half-width characters use Arial
  // - Chinese/full-width characters use Microsoft JhengHei
  return {
    ascii: FONT_EN,      // English characters
    eastAsia: FONT_CN,   // Chinese characters (East Asian) - Microsoft JhengHei
    hAnsi: FONT_EN,      // High ANSI characters
    cs: FONT_EN          // Complex script characters
  };
}

/**
 * Get English-only font (for cases explicitly requiring English font)
 */
function getFontEnglishOnly() {
  return FONT_EN;
}

// ============================================
// Mermaid Diagram Renderer
// ============================================

/**
 * Determine Mermaid diagram type and select render width
 * block-beta (UI wireframe) uses narrower width, other diagrams use wider width
 */
function getMermaidRenderWidth(mermaidCode) {
  const firstLine = mermaidCode.trim().split('\n')[0].toLowerCase();

  // block-beta is UI wireframe, typically vertical mobile screen, use narrow width
  if (firstLine.includes('block-beta')) {
    return 500;  // Narrow width for mobile wireframe
  }

  // Other diagram types use standard width
  return 1200;
}

/**
 * Create Mermaid configuration file
 * Set htmlLabels: false to use native SVG <text> elements for Word compatibility
 *
 * Background: Mermaid defaults to using foreignObject for embedded HTML text,
 * but Word/Inkscape cannot render text inside foreignObject correctly.
 * Solution: Set htmlLabels: false to use native SVG text elements.
 *
 * Reference: https://github.com/mermaid-js/mermaid/issues/2688
 */
function createMermaidConfig(tempDir) {
  const configPath = path.join(tempDir, 'mermaid-config.json');

  const config = {
    "theme": "base",
    "themeVariables": {
      "primaryColor": "#2196F3",
      "primaryTextColor": "#ffffff",
      "primaryBorderColor": "#1976D2",
      "lineColor": "#757575",
      "secondaryColor": "#FFC107",
      "secondaryTextColor": "#5D4037",
      "tertiaryColor": "#FFF9C4",
      "tertiaryTextColor": "#5D4037",
      "nodeBorder": "#1976D2",
      "clusterBkg": "#E3F2FD",
      "clusterBorder": "#90CAF9",
      "defaultLinkColor": "#757575",
      "titleColor": "#5D4037",
      "edgeLabelBackground": "transparent",
      "textColor": "#1565C0",
      "classText": "#1565C0"
    },
    "flowchart": {
      "htmlLabels": false,
      "useMaxWidth": true
    },
    "sequence": {
      "useMaxWidth": true
    },
    "gantt": {
      "useMaxWidth": true
    },
    "class": {
      "htmlLabels": false,
      "useMaxWidth": true
    },
    "state": {
      "htmlLabels": false,
      "useMaxWidth": true
    },
    "er": {
      "useMaxWidth": true
    },
    "pie": {
      "useMaxWidth": true
    },
    "journey": {
      "useMaxWidth": true
    }
  };

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  return configPath;
}

/**
 * Parse style definitions from Mermaid code
 * Parse style NodeId fill:#xxx,stroke:#xxx,color:#xxx format
 * @param {string} mermaidCode - Mermaid diagram code
 * @returns {Map<string, {fill: string, color: string}>} - Node ID to style mapping
 */
function parseMermaidStyles(mermaidCode) {
  const styles = new Map();

  // Match style NodeId fill:#xxx,stroke:#xxx,color:#xxx
  const styleRegex = /style\s+(\w+)\s+fill:(#[0-9A-Fa-f]{3,6})[^,]*(?:,stroke:[^,]*)?(?:,color:(#[0-9A-Fa-f]{3,6}|#\w+))?/g;
  let match;

  while ((match = styleRegex.exec(mermaidCode)) !== null) {
    const nodeId = match[1];
    const fill = match[2];
    const color = match[3] || null;
    styles.set(nodeId, { fill, color });
  }

  // Also parse classDef definitions
  const classDefRegex = /classDef\s+(\w+)\s+fill:(#[0-9A-Fa-f]{3,6})[^,]*(?:,stroke:[^,]*)?(?:,color:(#[0-9A-Fa-f]{3,6}|#\w+))?/g;
  while ((match = classDefRegex.exec(mermaidCode)) !== null) {
    const className = match[1];
    const fill = match[2];
    const color = match[3] || null;
    styles.set(`class:${className}`, { fill, color });
  }

  return styles;
}

/**
 * Determine appropriate text color based on background color
 * Uses WCAG contrast ratio algorithm
 * @param {string} bgColor - Background color (hex format)
 * @returns {string} - Recommended text color
 */
function getContrastTextColor(bgColor) {
  // Define color mapping table (based on reference image colors)
  const colorMap = {
    '#2196F3': '#ffffff',  // Blue -> White text
    '#2196f3': '#ffffff',
    '#1976D2': '#ffffff',  // Dark blue -> White text
    '#1976d2': '#ffffff',
    '#FFC107': '#5D4037',  // Gold -> Dark brown text
    '#ffc107': '#5D4037',
    '#FFA000': '#5D4037',  // Dark gold -> Dark brown text
    '#ffa000': '#5D4037',
    '#A8E6CF': '#2E7D32',  // Mint green -> Dark green text
    '#a8e6cf': '#2E7D32',
    '#81C784': '#1B5E20',  // Green -> Dark green text
    '#81c784': '#1B5E20',
    '#9E9E9E': '#ffffff',  // Gray -> White text
    '#9e9e9e': '#ffffff',
    '#757575': '#ffffff',  // Dark gray -> White text
    '#FFCDD2': '#5D4037',  // Pink -> Dark brown text
    '#ffcdd2': '#5D4037',
    '#B3E5FC': '#01579B',  // Light blue -> Dark blue text
    '#b3e5fc': '#01579B',
    '#FFF9C4': '#5D4037',  // Light yellow -> Dark brown text
    '#fff9c4': '#5D4037',
    '#ECEFF1': '#546E7A',  // Light gray -> Dark gray text
    '#eceff1': '#546E7A',
    '#EF5350': '#ffffff',  // Red -> White text
    '#ef5350': '#ffffff',
    '#26A69A': '#ffffff',  // Teal -> White text
    '#26a69a': '#ffffff',
    '#FFA726': '#5D4037',  // Orange -> Dark brown text
    '#ffa726': '#5D4037',
    '#64B5F6': '#0D47A1',  // Sky blue -> Dark blue text
    '#64b5f6': '#0D47A1',
  };

  if (colorMap[bgColor]) {
    return colorMap[bgColor];
  }

  // Unknown color, calculate using luminance
  const hex = bgColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.5 ? '#333333' : '#ffffff';
}

/**
 * Post-process SVG text colors
 * Set appropriate text color based on background color
 * @param {string} svgContent - SVG content
 * @param {string} mermaidCode - Original Mermaid code
 * @returns {string} - Processed SVG content
 */
function postProcessSvgTextColors(svgContent, mermaidCode) {
  const styles = parseMermaidStyles(mermaidCode);

  // Inject CSS styles for each node with defined styles
  let cssRules = [];

  styles.forEach((style, key) => {
    if (key.startsWith('class:')) {
      return; // classDef will be processed later
    }

    const textColor = style.color || getContrastTextColor(style.fill);
    // In Mermaid-generated SVG, node text is usually in .nodeLabel or directly in text elements
    cssRules.push(`#${key} .nodeLabel { fill: ${textColor} !important; color: ${textColor} !important; }`);
    cssRules.push(`#${key} text { fill: ${textColor} !important; }`);
    cssRules.push(`#${key} tspan { fill: ${textColor} !important; }`);
    // Also handle div inside foreignObject
    cssRules.push(`#${key} foreignObject div { color: ${textColor} !important; }`);
  });

  // Process classDef
  styles.forEach((style, key) => {
    if (!key.startsWith('class:')) {
      return;
    }
    const className = key.replace('class:', '');
    const textColor = style.color || getContrastTextColor(style.fill);
    cssRules.push(`.${className} .nodeLabel { fill: ${textColor} !important; color: ${textColor} !important; }`);
    cssRules.push(`.${className} text { fill: ${textColor} !important; }`);
    cssRules.push(`.${className} tspan { fill: ${textColor} !important; }`);
    cssRules.push(`.${className} foreignObject div { color: ${textColor} !important; }`);
  });

  if (cssRules.length === 0) {
    return svgContent;
  }

  // Inject CSS styles into SVG
  const styleTag = `<style type="text/css">\n${cssRules.join('\n')}\n</style>`;

  // Insert style after <svg> tag
  if (svgContent.includes('</defs>')) {
    svgContent = svgContent.replace('</defs>', `</defs>\n${styleTag}`);
  } else if (svgContent.includes('<svg')) {
    svgContent = svgContent.replace(/<svg([^>]*)>/, `<svg$1>\n${styleTag}`);
  }

  return svgContent;
}

/**
 * Parse SVG transformation matrix and calculate actual coordinates
 * @param {string} transform - transformation string, e.g., "matrix(a,b,c,d,e,f)"
 * @param {number} x - Original x coordinate
 * @param {number} y - Original y coordinate
 * @returns {{x: number, y: number}} - Transformed coordinates
 */
function applyTransform(transform, x, y) {
  const matrixMatch = transform.match(/matrix\(([^)]+)\)/);
  if (matrixMatch) {
    const [a, b, c, d, e, f] = matrixMatch[1].split(',').map(parseFloat);
    return {
      x: a * x + c * y + e,
      y: b * x + d * y + f
    };
  }
  return { x, y };
}

/**
 * Extract bounding box from path's d attribute
 * @param {string} d - path's d attribute
 * @returns {{minX: number, minY: number, maxX: number, maxY: number}|null}
 */
function getPathBounds(d) {
  // Rectangle path format: "M x1 y1 H x2 V y2 H x3 Z" (may have no spaces)
  // Example: "M-84.11719-39H84.11719V39H-84.11719Z"
  // Extract all numbers (including negative and decimal) - using correct floating point regex
  const numbers = d.match(/-?\d+(?:\.\d+)?/g);
  if (numbers && numbers.length >= 4) {
    // numbers[0] = x1, numbers[1] = y1, numbers[2] = x2, numbers[3] = y2
    const x1 = parseFloat(numbers[0]);
    const y1 = parseFloat(numbers[1]);
    const x2 = parseFloat(numbers[2]);
    const y2 = parseFloat(numbers[3]);
    return {
      minX: Math.min(x1, x2),
      minY: Math.min(y1, y2),
      maxX: Math.max(x1, x2),
      maxY: Math.max(y1, y2)
    };
  }
  return null;
}

/**
 * Post-process SVG generated by mutool, fix text color inside blue boxes
 * @param {string} svgContent - SVG content
 * @returns {string} - Processed SVG content
 */
function postProcessMutoolSvg(svgContent) {
  // List of background colors requiring white text (dark blue series)
  const blueBackgrounds = ['#2196f3', '#42a5f5', '#1976d2'];
  // Other dark backgrounds requiring white text
  const darkBackgrounds = ['#26a69a', '#00897b'];
  // Note: Light backgrounds like #a8e6cf (light green), #ffa726 (light orange) don't need white text
  const allWhiteTextBackgrounds = [...blueBackgrounds, ...darkBackgrounds];

  // Find all dark node box positions (exclude large subgraph backgrounds)
  const boxBounds = [];

  // Match path elements (boxes)
  const pathRegex = /<path\s+transform="([^"]+)"\s+d="([^"]+)"\s+fill="(#[0-9a-fA-F]{6})"/g;
  let match;
  while ((match = pathRegex.exec(svgContent)) !== null) {
    const [, transform, d, fill] = match;
    if (allWhiteTextBackgrounds.includes(fill.toLowerCase())) {
      const bounds = getPathBounds(d);
      if (bounds) {
        // Apply transform to bounds
        const topLeft = applyTransform(transform, bounds.minX, bounds.minY);
        const bottomRight = applyTransform(transform, bounds.maxX, bounds.maxY);
        const width = Math.abs(bottomRight.x - topLeft.x);
        const height = Math.abs(bottomRight.y - topLeft.y);

        // Only consider small node boxes (width < 300, height < 150)
        // Exclude large subgraph backgrounds
        if (width < 300 && height < 150) {
          boxBounds.push({
            minX: Math.min(topLeft.x, bottomRight.x),
            minY: Math.min(topLeft.y, bottomRight.y),
            maxX: Math.max(topLeft.x, bottomRight.x),
            maxY: Math.max(topLeft.y, bottomRight.y),
            fill: fill.toLowerCase()
          });
        }
      }
    }
  }

  // If no dark boxes found, return directly
  if (boxBounds.length === 0) {
    return svgContent;
  }

  // Find all text elements and check if they're inside blue boxes
  // Text element format: <use data-text="X" xlink:href="..." transform="matrix(...)" fill="#ababab"/>
  // Or: <path transform="matrix(...)" d="..." fill="#ababab"/> (glyph path)

  // Match gray text (#ababab)
  const grayTextRegex = /<(use|path)\s+([^>]*transform="matrix\(([^)]+)\)"[^>]*fill="#ababab"[^>]*)\/>/g;
  // Match brown text (#5d4037) - edge labels and text inside light boxes
  const brownTextRegex = /<(use|path)\s+([^>]*transform="matrix\(([^)]+)\)"[^>]*fill="#5d4037"[^>]*)\/>/g;

  let whiteCount = 0, blueCount = 0;

  // Process gray text (#ababab) - text inside dark boxes
  svgContent = svgContent.replace(grayTextRegex, (fullMatch, tag, attrs, matrixValues) => {
    const [a, b, c, d, e, f] = matrixValues.split(',').map(parseFloat);
    const textX = e;
    const textY = f;

    const isInBox = boxBounds.some(box => {
      const margin = 5;
      return textX >= (box.minX + margin) && textX <= (box.maxX - margin) &&
             textY >= (box.minY + margin) && textY <= (box.maxY - margin);
    });

    if (isInBox) {
      whiteCount++;
      return fullMatch.replace('fill="#ababab"', 'fill="#ffffff"');
    } else {
      blueCount++;
      return fullMatch.replace('fill="#ababab"', 'fill="#1565C0"');
    }
  });

  // Process brown text (#5d4037) - edge labels and text inside light boxes
  // Convert all to dark blue
  svgContent = svgContent.replace(brownTextRegex, (fullMatch) => {
    blueCount++;
    return fullMatch.replace('fill="#5d4037"', 'fill="#1565C0"');
  });

  // Process #1976d2 text - ER diagram relationship labels
  // This color matches border color, hard to read on some backgrounds, convert to darker blue
  const borderBlueTextRegex = /<(use|path)\s+([^>]*transform="matrix\(([^)]+)\)"[^>]*fill="#1976d2"[^>]*)\/>/g;
  svgContent = svgContent.replace(borderBlueTextRegex, (fullMatch) => {
    blueCount++;
    return fullMatch.replace('fill="#1976d2"', 'fill="#1565C0"');
  });

  // Process white text (#ffffff) - white text outside dark boxes should become dark blue
  // This is because Mermaid's edge labels become white in PDF output
  const whiteTextRegex = /<(use|path)\s+([^>]*transform="matrix\(([^)]+)\)"[^>]*fill="#ffffff"[^>]*)\/>/g;
  svgContent = svgContent.replace(whiteTextRegex, (fullMatch, tag, attrs, matrixValues) => {
    const [a, b, c, d, e, f] = matrixValues.split(',').map(parseFloat);
    const textX = e;
    const textY = f;

    // Check if this is a background rectangle (large white box) - scale > 0.1 and contains M0 0H pattern
    if (Math.abs(a) > 0.1 && attrs.includes('d="M0 0H')) {
      return fullMatch; // Keep background rectangle as white
    }

    const isInBox = boxBounds.some(box => {
      const margin = 5;
      return textX >= (box.minX + margin) && textX <= (box.maxX - margin) &&
             textY >= (box.minY + margin) && textY <= (box.maxY - margin);
    });

    if (isInBox) {
      return fullMatch; // Keep white inside dark boxes
    } else {
      blueCount++;
      return fullMatch.replace('fill="#ffffff"', 'fill="#1565C0"');
    }
  });

  return svgContent;
}

/**
 * Render Mermaid code to SVG + PNG (SVG primary, PNG as fallback)
 * Use htmlLabels: false to ensure SVG text uses native <text> elements for Word compatibility
 *
 * @param {string} mermaidCode - Mermaid diagram code
 * @param {string} outputDir - Output directory
 * @returns {{svg: string|null, png: string|null}} - SVG and PNG image paths
 */
function renderMermaidToSvgAndPng(mermaidCode, outputDir) {
  const hash = crypto.createHash('md5').update(mermaidCode).digest('hex').substring(0, 8);
  const tempDir = path.join(outputDir, '.mermaid-temp');
  const inputFile = path.join(tempDir, `mermaid-${hash}.mmd`);
  const svgFile = path.join(tempDir, `mermaid-${hash}.svg`);
  const pngFile = path.join(tempDir, `mermaid-${hash}.png`);

  // Create temp directory
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  // If cache exists, return directly
  const hasSvg = fs.existsSync(svgFile);
  const hasPng = fs.existsSync(pngFile);
  if (hasSvg && hasPng) {
    return { svg: svgFile, png: pngFile };
  }

  // Create Mermaid config file (htmlLabels: false)
  const configPath = createMermaidConfig(tempDir);

  // Write Mermaid code
  fs.writeFileSync(inputFile, mermaidCode);

  // Determine render width based on diagram type
  const renderWidth = getMermaidRenderWidth(mermaidCode);

  let svgPath = null;
  let pngPath = null;

  // Use PDF->mutool path (text converted to vector paths for Word compatibility)
  // This is the Mermaid official recommended solution, as direct SVG output uses foreignObject for node labels
  // Word doesn't support foreignObject, so text needs to be converted to paths
  // Reference: https://github.com/mermaid-js/mermaid/issues/2688
  const pdfFile = path.join(tempDir, `mermaid-${hash}.pdf`);
  try {
    // Step 1: Generate PDF (Mermaid PDF output converts text to paths and applies style-specified colors)
    execSync(`mmdc -i "${inputFile}" -o "${pdfFile}" -c "${configPath}" --pdfFit 2>/dev/null`, {
      stdio: 'pipe',
      timeout: 60000
    });

    if (fs.existsSync(pdfFile)) {
      // Step 2: Use mutool to convert PDF to SVG (text becomes paths for compatibility)
      // Need to check if mutool is available first
      // Note: mutool adds page number to output filename, e.g., output.svg -> output1.svg
      const mutoolOutputBase = path.join(tempDir, `svg-${hash}`);
      const mutoolSvgFile = `${mutoolOutputBase}1.svg`;  // mutool generates this filename
      try {
        execSync(`which mutool`, { stdio: 'pipe' });
        execSync(`mutool draw -F svg -o "${mutoolOutputBase}.svg" "${pdfFile}" 2>/dev/null`, {
          stdio: 'pipe',
          timeout: 60000
        });
        // mutool output filename has page number, need to rename
        if (fs.existsSync(mutoolSvgFile)) {
          fs.renameSync(mutoolSvgFile, svgFile);
          // Post-process SVG: fix text color inside blue boxes
          let svgContent = fs.readFileSync(svgFile, 'utf-8');
          svgContent = postProcessMutoolSvg(svgContent);
          fs.writeFileSync(svgFile, svgContent);
          svgPath = svgFile;
        }
      } catch (mutoolError) {
        // No mutool, fallback to direct SVG (text may not display)
        console.warn(`  Warning: mutool not installed, using direct SVG output (text may not display in Word)`);
        console.warn(`    Install with: brew install mupdf-tools`);
        execSync(`mmdc -i "${inputFile}" -o "${svgFile}" -c "${configPath}" -b white 2>/dev/null`, {
          stdio: 'pipe',
          timeout: 60000
        });
        if (fs.existsSync(svgFile)) {
          svgPath = svgFile;
        }
      }
      // Clean up PDF temp file
      if (fs.existsSync(pdfFile)) {
        fs.unlinkSync(pdfFile);
      }
    }
  } catch (error) {
    // PDF generation failed, fallback to direct SVG
    console.warn(`PDF render failed [${hash}]: ${error.message}`);
    try {
      execSync(`mmdc -i "${inputFile}" -o "${svgFile}" -c "${configPath}" -b white 2>/dev/null`, {
        stdio: 'pipe',
        timeout: 60000
      });
      if (fs.existsSync(svgFile)) {
        svgPath = svgFile;
      }
    } catch (svgError) {
      console.warn(`SVG render also failed [${hash}]: ${svgError.message}`);
    }
  }

  // 2. Render PNG (as fallback for older Word versions)
  try {
    execSync(`mmdc -i "${inputFile}" -o "${pngFile}" -c "${configPath}" -b white -w ${renderWidth} -s 2`, {
      stdio: 'pipe',
      timeout: 60000
    });
    if (fs.existsSync(pngFile)) {
      pngPath = pngFile;
    }
  } catch (error) {
    console.warn(`PNG render failed [${hash}]: ${error.message}`);
  }

  return { svg: svgPath, png: pngPath };
}

/**
 * Backward compatible function: Render Mermaid code to PNG image
 * @deprecated Use renderMermaidToSvgAndPng instead
 */
function renderMermaidToPng(mermaidCode, outputDir) {
  const result = renderMermaidToSvgAndPng(mermaidCode, outputDir);
  return result.png;
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
 * Read JPEG image dimensions
 * JPEG uses SOF0 marker (0xFF 0xC0) to store dimensions
 */
function getJpgDimensions(buffer) {
  if (buffer.length < 2) return null;

  // Check JPEG signature (0xFF 0xD8)
  if (buffer[0] !== 0xFF || buffer[1] !== 0xD8) return null;

  let offset = 2;
  while (offset < buffer.length - 1) {
    if (buffer[offset] !== 0xFF) {
      offset++;
      continue;
    }

    const marker = buffer[offset + 1];

    // SOF0 (Start of Frame) markers: C0-C3, C5-C7, C9-CB, CD-CF
    if ((marker >= 0xC0 && marker <= 0xC3) ||
        (marker >= 0xC5 && marker <= 0xC7) ||
        (marker >= 0xC9 && marker <= 0xCB) ||
        (marker >= 0xCD && marker <= 0xCF)) {
      // SOF structure: marker(2) + length(2) + precision(1) + height(2) + width(2)
      if (offset + 9 <= buffer.length) {
        const height = buffer.readUInt16BE(offset + 5);
        const width = buffer.readUInt16BE(offset + 7);
        return { width, height };
      }
    }

    // Skip to next marker
    if (offset + 3 < buffer.length) {
      const length = buffer.readUInt16BE(offset + 2);
      offset += 2 + length;
    } else {
      break;
    }
  }

  return null;
}

/**
 * Get image dimensions based on file extension
 */
function getImageDimensions(buffer, ext) {
  ext = ext.toLowerCase();
  if (ext === '.png') {
    return getPngDimensions(buffer);
  } else if (ext === '.jpg' || ext === '.jpeg') {
    return getJpgDimensions(buffer);
  }
  return null;
}

/**
 * Create local image paragraph from file path
 * Supports PNG and JPEG formats
 */
function createLocalImage(imagePath, baseDir) {
  // Resolve relative path
  const fullPath = path.resolve(baseDir, imagePath);

  if (!fs.existsSync(fullPath)) {
    console.warn(`Image not found: ${fullPath}`);
    return new Paragraph({
      children: [new TextRun({ text: `[Image not found: ${imagePath}]`, italics: true, color: 'FF0000' })]
    });
  }

  const imageBuffer = fs.readFileSync(fullPath);
  const ext = path.extname(fullPath).toLowerCase();

  // Determine image type
  let imageType;
  if (ext === '.png') {
    imageType = 'png';
  } else if (ext === '.jpg' || ext === '.jpeg') {
    imageType = 'jpg';
  } else {
    console.warn(`Unsupported image format: ${ext}`);
    return new Paragraph({
      children: [new TextRun({ text: `[Unsupported image format: ${ext}]`, italics: true, color: 'FF0000' })]
    });
  }

  // Read image dimensions
  const dimensions = getImageDimensions(imageBuffer, ext);

  let displayWidth, displayHeight;
  const maxWidth = 500;  // Max width for UI screenshots
  const maxHeight = 650; // Max height

  if (dimensions) {
    const { width, height } = dimensions;
    const aspectRatio = width / height;

    // Calculate scaled dimensions
    if (width > maxWidth) {
      displayWidth = maxWidth;
      displayHeight = Math.round(maxWidth / aspectRatio);
    } else {
      displayWidth = width;
      displayHeight = height;
    }

    // Scale if height exceeds limit
    if (displayHeight > maxHeight) {
      displayHeight = maxHeight;
      displayWidth = Math.round(maxHeight * aspectRatio);
    }

    // Ensure minimum size
    const minWidth = 200;
    if (displayWidth < minWidth && width >= minWidth) {
      displayWidth = minWidth;
      displayHeight = Math.round(minWidth / aspectRatio);
    }
  } else {
    // Default dimensions
    displayWidth = 400;
    displayHeight = 300;
  }

  console.log(`Embedding image: ${imagePath} (${displayWidth}x${displayHeight})`);

  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    keepLines: true,   // Keep image on same page (don't split)
    keepNext: false,   // Image doesn't need to keep with next (end of chain)
    children: [
      new ImageRun({
        data: imageBuffer,
        transformation: {
          width: displayWidth,
          height: displayHeight
        },
        type: imageType
      })
    ]
  });
}

/**
 * Parse viewBox or width/height from SVG content to get dimensions
 */
function getSvgDimensions(svgContent) {
  // Try to parse from viewBox
  const viewBoxMatch = svgContent.match(/viewBox\s*=\s*["']([^"']+)["']/);
  if (viewBoxMatch) {
    const parts = viewBoxMatch[1].split(/[\s,]+/);
    if (parts.length >= 4) {
      return {
        width: parseFloat(parts[2]),
        height: parseFloat(parts[3])
      };
    }
  }

  // Try to parse from width/height attributes
  const widthMatch = svgContent.match(/width\s*=\s*["'](\d+)/);
  const heightMatch = svgContent.match(/height\s*=\s*["'](\d+)/);
  if (widthMatch && heightMatch) {
    return {
      width: parseFloat(widthMatch[1]),
      height: parseFloat(heightMatch[1])
    };
  }

  return null;
}

/**
 * Create Mermaid image paragraph - using SVG with PNG fallback
 * SVG is vector format, ensures no quality loss at any scale (requires Office 2019+ or Microsoft 365)
 * PNG as fallback for older Word versions
 * Maintains original aspect ratio, max width 550px (A4 page width ~6 inches = 576px)
 * Image centered
 */
function createMermaidImageWithSvg(svgPath, pngPath) {
  const svgBuffer = fs.readFileSync(svgPath);
  const pngBuffer = fs.readFileSync(pngPath);
  const svgContent = svgBuffer.toString('utf-8');

  // Get dimensions from SVG or PNG
  let dimensions = getSvgDimensions(svgContent);
  if (!dimensions) {
    dimensions = getPngDimensions(pngBuffer);
  }

  let displayWidth, displayHeight;
  const maxWidth = 550;  // Max width limit, A4 page width (with margins) ~6 inches
  const maxHeight = 600; // Max height limit, avoid exceeding single page

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

    // Ensure image has minimum size (avoid too small images)
    const minWidth = 200;
    if (displayWidth < minWidth && width >= minWidth) {
      displayWidth = minWidth;
      displayHeight = Math.round(minWidth / aspectRatio);
    }
  } else {
    // Use default values when dimensions cannot be read
    displayWidth = 450;
    displayHeight = 350;
  }

  // Use SVG with PNG fallback (docx library v9.x support)
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    children: [
      new ImageRun({
        type: 'svg',
        data: svgBuffer,
        transformation: {
          width: displayWidth,
          height: displayHeight
        },
        fallback: {
          type: 'png',
          data: pngBuffer
        }
      })
    ]
  });
}

/**
 * Create Mermaid image paragraph - PNG only (backward compatible)
 * @deprecated Use createMermaidImageWithSvg instead
 */
function createMermaidImage(imagePath) {
  const imageBuffer = fs.readFileSync(imagePath);

  // Read actual image dimensions
  const dimensions = getPngDimensions(imageBuffer);

  let displayWidth, displayHeight;
  const maxWidth = 550;  // Max width limit, A4 page width (with margins) ~6 inches
  const maxHeight = 600; // Max height limit, avoid exceeding single page

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

    // Ensure image has minimum size (avoid too small images)
    const minWidth = 200;
    if (displayWidth < minWidth && width >= minWidth) {
      displayWidth = minWidth;
      displayHeight = Math.round(minWidth / aspectRatio);
    }
  } else {
    // Use default values when dimensions cannot be read
    displayWidth = 450;
    displayHeight = 350;
  }

  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
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
 * Check if line is a requirement item heading
 * Supported formats:
 *   - #### SRS-AUTH-001 User Registration (old format)
 *   - ##### REQ-FUNC-001 User Login (new format, space separated)
 *   - #### REQ-FUNC-001: User Login (new format, colon separated)
 */
function isRequirementHeading(line) {
  // Support SRS/SWD/SDD/STC/REQ prefix, 3-5 # symbols
  return line.match(/^#{3,5}\s+(SRS|SWD|SDD|STC|REQ)-[A-Z]+-\d+/);
}

/**
 * Parse requirement item block, convert to table structure
 * Supports multiple input formats:
 *
 * Old format (Chinese fields):
 *   #### SRS-AUTH-001 User Registration
 *   **Description:** System must...
 *   **Priority:** Required
 *   **Acceptance Criteria:**
 *   - AC1: Given...
 *
 * New format (English fields):
 *   ##### REQ-FUNC-001 User Login
 *   **Statement:** System shall...
 *   **Rationale:** Reason...
 *   **Acceptance Criteria:**
 *   - AC1: Given...
 *   **Verification Method:** Test
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
    // Support both Chinese and English fields
    description: '',      // Description (old format)
    statement: '',        // Statement (new format)
    rationale: '',        // Rationale (new format)
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

    // End when encountering next heading or separator line
    if (line.startsWith('#') || line.match(/^-{3,}$/)) {
      break;
    }

    // Parse **Field:** value or **Field:** value format
    const fieldMatch = line.match(/^\*\*(.+?)[:：]\*\*\s*(.*)$/);

    if (fieldMatch) {
      const fieldName = fieldMatch[1].trim();
      const fieldValue = fieldMatch[2].trim();

      // Chinese fields
      if (fieldName === '描述') {
        requirement.description = fieldValue;
        currentField = 'description';
        inAcceptanceCriteria = false;
      } else if (fieldName === '優先級') {
        requirement.priority = fieldValue;
        currentField = 'priority';
        inAcceptanceCriteria = false;
      } else if (fieldName === '安全分類') {
        requirement.safetyClass = fieldValue;
        currentField = 'safetyClass';
        inAcceptanceCriteria = false;
      } else if (fieldName === '驗收標準') {
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
      } else if (fieldName === 'Acceptance Criteria') {
        inAcceptanceCriteria = true;
        currentField = 'acceptanceCriteria';
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
      // Acceptance criteria item
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
 * Auto-detect Chinese or English field labels and apply appropriate font
 */
function createRequirementTable(req) {
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

  const labelWidth = 2200;  // Label column width (wider for Chinese)
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

  // Old format field (Description)
  if (req.description) {
    rows.push(createFieldRow('描述', req.description, labelWidth, valueWidth, cellBorders));
  }

  // Priority
  if (req.priority) {
    rows.push(createFieldRow('優先級', req.priority, labelWidth, valueWidth, cellBorders));
  }

  // Safety Class
  if (req.safetyClass) {
    rows.push(createFieldRow('安全分類', req.safetyClass, labelWidth, valueWidth, cellBorders));
  }

  // Other fields
  for (const [key, value] of Object.entries(req.otherFields)) {
    rows.push(createFieldRow(key, value, labelWidth, valueWidth, cellBorders));
  }

  // Acceptance Criteria
  if (req.acceptanceCriteria.length > 0) {
    // Determine Chinese or English label
    const acLabel = req.statement ? 'Acceptance Criteria' : '驗收標準';
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
// Main Parsing Functions
// ============================================

/**
 * Check if this is the first heading in an "orphan heading group"
 * When multiple consecutive headings (no content in between) are followed by requirement tables,
 * only add page break before the first heading
 * Avoids headings at page bottom, but doesn't create empty pages with breaks before each heading
 */
function shouldBreakBeforeHeading(lines, currentIndex) {
  const currentLine = lines[currentIndex];

  // Check if previous non-empty line is also a heading
  let prevIndex = currentIndex - 1;
  while (prevIndex >= 0 && lines[prevIndex].trim() === '') {
    prevIndex--;
  }

  // If previous line is also a heading, don't break (keep heading group together)
  if (prevIndex >= 0 && lines[prevIndex].startsWith('#')) {
    return false;
  }

  // Look ahead to find the end of this heading group
  let j = currentIndex + 1;
  let headingCount = 1;

  while (j < lines.length) {
    const line = lines[j].trim();

    if (line === '') {
      j++;
      continue;
    }

    // If it's another heading, continue looking
    if (line.startsWith('#') && !isRequirementHeading(lines[j])) {
      headingCount++;
      j++;
      continue;
    }

    // Check if this is an image (![...](..)) - high risk of orphan heading
    if (line.match(/^!\[.*\]\(.*\)/)) {
      // If heading is followed by image, always add page break to prevent orphan
      return true;
    }

    // Check if this is a table start (|...|)
    if (line.startsWith('|') && line.endsWith('|')) {
      // If heading is followed by table, always add page break to prevent orphan
      return true;
    }

    // If it's a requirement item or other content, stop
    break;
  }

  // Break before first heading when:
  // 1. Multiple consecutive headings (heading group)
  // 2. Or heading is followed by large content (image/table) - checked above
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

    // Process code blocks
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        if (codeBlockLang === 'mermaid') {
          // Mermaid diagram - render to SVG + PNG (SVG primary)
          const mermaidCode = codeBlockContent.join('\n');
          const { svg: svgPath, png: pngPath } = renderMermaidToSvgAndPng(mermaidCode, outputDir);
          if (svgPath && pngPath) {
            // Use SVG with PNG fallback (vector quality)
            elements.push(createMermaidImageWithSvg(svgPath, pngPath));
          } else if (pngPath) {
            // SVG failed, use PNG only
            elements.push(createMermaidImage(pngPath));
          } else {
            // Render completely failed, fallback to code block
            console.warn('Mermaid render failed, displaying as code block');
            elements.push(...createCodeBlock(mermaidCode));
          }
        } else {
          // Regular code block (pass language param for syntax highlighting)
          elements.push(...createCodeBlock(codeBlockContent.join('\n'), codeBlockLang));
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

    // Process Markdown tables
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

    // Check if it's a requirement item heading - convert to table format
    if (isRequirementHeading(line)) {
      const result = parseRequirementBlock(lines, i);
      if (result) {
        elements.push(new Paragraph({ spacing: { before: 240 }, children: [] })); // spacing
        elements.push(createRequirementTable(result.requirement));
        elements.push(new Paragraph({ spacing: { after: 120 }, children: [] })); // spacing
        i = result.endIndex + 1;
        continue;
      }
    }

    // Heading processing
    // Heading 1 (# ) - Main title (cover title not numbered)
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      const headingText = line.substring(2);
      // Cover titles (Software Requirements Specification, Software Design Description, etc.) don't use auto numbering
      const isCoverTitle = headingText.match(/^(Software|For\s)/i);
      elements.push(createHeading(headingText, HeadingLevel.HEADING_1, true, !isCoverTitle)); // page break
      i++;
      continue;
    }
    // Heading 2 (## ) - Major section, page break before each major section
    if (line.startsWith('## ')) {
      const headingText = line.substring(3);
      // Check if it's a main section (e.g., "Introduction", "Product Overview", manual numbering removed)
      // Special titles (Table of Contents, Revision History, etc.) don't use auto numbering
      const isSpecialSection = headingText.match(/^(Table of Contents|Revision History|目錄|修訂歷史|For\s)/i);
      const isMainSection = !isSpecialSection; // Non-special sections get page break before
      elements.push(createHeading(headingText, HeadingLevel.HEADING_2, isMainSection, !isSpecialSection));
      i++;
      continue;
    }
    // Heading 3 (### ) - Subsection
    if (line.startsWith('### ')) {
      const headingText = line.substring(4);
      // Module section titles always start on new page (AUTH, ONBOARD, VOCAB, TRAIN, REPORT, SETTING, etc.)
      const isModuleSection = /^(AUTH|ONBOARD|DASH|VOCAB|TRAIN|REPORT|SETTING|DEVICE|REWARD|COM)\s/.test(headingText);
      // Check if heading is followed by requirement table or only empty lines, if so add page break to avoid orphan heading
      const shouldPageBreak = isModuleSection || shouldBreakBeforeHeading(lines, i);
      elements.push(createHeading(headingText, HeadingLevel.HEADING_3, shouldPageBreak, true));
      i++;
      continue;
    }
    // Heading 4 (#### )
    if (line.startsWith('#### ')) {
      const headingText = line.substring(5);
      // Screen Design sections - check if immediately following a module section H3
      const isScreenDesign = headingText.includes('Screen Design:') || headingText.includes('SCR-');

      // Check if previous non-empty line is an H3 module section heading
      // If so, don't add pageBreak to H4 (H3 already has it, and we want them together)
      let prevIdx = i - 1;
      while (prevIdx >= 0 && lines[prevIdx].trim() === '') {
        prevIdx--;
      }
      const prevLine = prevIdx >= 0 ? lines[prevIdx] : '';
      const prevIsModuleH3 = prevLine.startsWith('### ') &&
        /^### (AUTH|ONBOARD|DASH|VOCAB|TRAIN|REPORT|SETTING|DEVICE|REWARD|COM)\s/.test(prevLine);

      // Only add pageBreak if NOT immediately following a module H3
      const shouldPageBreak = !prevIsModuleH3 && (isScreenDesign || shouldBreakBeforeHeading(lines, i));
      elements.push(createHeading(headingText, HeadingLevel.HEADING_4, shouldPageBreak, true));
      i++;
      continue;
    }
    // Heading 5 (##### )
    if (line.startsWith('##### ')) {
      elements.push(createHeading(line.substring(6), HeadingLevel.HEADING_5, false, true));
      i++;
      continue;
    }

    // Markdown image syntax: ![alt](path)
    const imageMatch = line.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/);
    if (imageMatch) {
      const altText = imageMatch[1];
      const imagePath = imageMatch[2];
      elements.push(createLocalImage(imagePath, outputDir));
      i++;
      continue;
    }

    // Horizontal rule
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
 * @param {boolean} pageBreakBefore - Whether to add page break before heading (for major sections)
 * @param {boolean} useNumbering - Whether to use auto numbering (default true)
 */
function createHeading(text, level, pageBreakBefore = false, useNumbering = true) {
  const trimmedText = text.trim();
  const fontSize = getHeadingSize(level);

  // Convert HeadingLevel to numbering level (0-based)
  // Note: For IEC 62304 documents (SRS/SDD/SWD, etc.):
  //   - # (H1) used for cover title (not numbered)
  //   - ## (H2) used for main sections -> numbering 1., 2., 3. (level 0)
  //   - ### (H3) used for subsections -> numbering 1.1, 1.2 (level 1)
  //   - #### (H4) -> numbering 1.1.1 (level 2)
  //   - ##### (H5) -> numbering 1.1.1.1 (level 3)
  // Therefore H1 has no numbering, H2~H5 correspond to level 0~3
  const numberingLevel = {
    [HeadingLevel.HEADING_1]: undefined,  // H1 cover title not numbered
    [HeadingLevel.HEADING_2]: 0,  // ## -> 1., 2., 3.
    [HeadingLevel.HEADING_3]: 1,  // ### -> 1.1, 1.2
    [HeadingLevel.HEADING_4]: 2,  // #### -> 1.1.1
    [HeadingLevel.HEADING_5]: 3   // ##### -> 1.1.1.1
  }[level];

  const paragraphOptions = {
    heading: level,
    spacing: { before: pageBreakBefore ? 0 : 240, after: 120 },
    pageBreakBefore: pageBreakBefore,  // Page break before major sections
    keepNext: true,  // Keep heading with next paragraph on same page (avoid orphan headings)
    keepLines: true, // Don't split heading across lines
    children: [new TextRun({ text: trimmedText, bold: true, size: fontSize, font: getFont(trimmedText) })]
  };

  // If auto numbering enabled and level has corresponding numbering level
  if (useNumbering && numberingLevel !== undefined) {
    paragraphOptions.numbering = {
      reference: 'heading-numbering',
      level: numberingLevel
    };
  }

  return new Paragraph(paragraphOptions);
}

function createParagraph(text) {
  const runs = parseInlineFormatting(text);

  // Check if this is a "sub-heading paragraph": bold paragraph ending with `:` or `:`
  // Example: "**iOS Architecture Layers:**", "**Interaction Behavior**"
  // Such paragraphs should stay on same page with next content (images, code blocks)
  const isSubHeading = /\*\*[^*]+[：:]\*\*\s*$/.test(text.trim()) ||
                       /\*\*[^*]+\*\*\s*$/.test(text.trim());

  return new Paragraph({
    spacing: { after: 120 },
    keepNext: isSubHeading,  // Keep sub-heading paragraph with next content on same page
    children: runs
  });
}

/**
 * Parse inline formatting (bold, code)
 * @param {string} text - Original text
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

// ============================================
// Syntax Highlighting Colors (based on VSCode Light+ / GitHub standard)
// Reference: https://code.visualstudio.com/api/extension-guides/color-theme
// ============================================
const SYNTAX_COLORS = {
  keyword: '0000FF',      // Blue - keywords (function, class, if, return, async, etc.)
  string: 'A31515',       // Dark red - strings
  comment: '008000',      // Green - comments
  number: '098658',       // Dark cyan - numbers
  type: '267F99',         // Cyan blue - types/class names
  property: '001080',     // Dark blue - properties/variables
  decorator: 'AF00DB',    // Purple - decorators/annotations (@xxx)
  operator: '000000',     // Black - operators
  punctuation: '000000',  // Black - punctuation
  default: '000000'       // Black - default
};

/**
 * Simplified syntax highlighting parser
 * Supports basic syntax highlighting for multiple programming languages
 * @param {string} line - Code line
 * @param {string} lang - Programming language (javascript, python, swift, kotlin, typescript, etc.)
 * @returns {Array} TextRun array
 */
function tokenizeLine(line, lang, fontSize) {
  const tokens = [];

  // Keyword definitions for each language
  const keywords = {
    javascript: /\b(function|const|let|var|if|else|for|while|return|class|extends|new|this|async|await|import|export|from|default|try|catch|throw|typeof|instanceof|null|undefined|true|false)\b/g,
    typescript: /\b(function|const|let|var|if|else|for|while|return|class|extends|new|this|async|await|import|export|from|default|try|catch|throw|typeof|instanceof|null|undefined|true|false|interface|type|enum|implements|public|private|protected|readonly|abstract|static)\b/g,
    python: /\b(def|class|if|elif|else|for|while|return|import|from|as|try|except|raise|with|lambda|yield|async|await|None|True|False|and|or|not|in|is|pass|break|continue|global|nonlocal|self)\b/g,
    swift: /\b(func|class|struct|enum|protocol|extension|var|let|if|else|guard|for|while|return|import|self|Self|nil|true|false|async|await|throws|try|catch|throw|public|private|internal|fileprivate|open|static|override|init|deinit|mutating|some|any)\b/g,
    kotlin: /\b(fun|class|object|interface|val|var|if|else|when|for|while|return|import|this|null|true|false|suspend|async|await|try|catch|throw|public|private|protected|internal|override|open|abstract|sealed|data|companion|init|lateinit|by|lazy)\b/g
  };

  // Common regex patterns
  const patterns = [
    { regex: /(\/\/.*$|#.*$)/gm, type: 'comment' },           // Single-line comments
    { regex: /(\/\*[\s\S]*?\*\/)/g, type: 'comment' },        // Multi-line comments
    { regex: /("""[\s\S]*?"""|'''[\s\S]*?''')/g, type: 'string' },  // Python multi-line strings
    { regex: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g, type: 'string' },  // Strings
    { regex: /(@\w+)/g, type: 'decorator' },                  // Decorators
    { regex: /\b(\d+\.?\d*)\b/g, type: 'number' },            // Numbers
    { regex: /\b([A-Z][a-zA-Z0-9_]*)\b/g, type: 'type' },     // Type names (capitalized)
  ];

  // Simplified processing: character-by-character analysis
  let result = [];
  let remaining = line;
  let lastIndex = 0;

  // Get keyword regex for this language
  const keywordRegex = keywords[lang] || keywords.javascript;

  // Token collection
  const allMatches = [];

  // Collect all matches
  patterns.forEach(({ regex, type }) => {
    regex.lastIndex = 0;
    let match;
    while ((match = regex.exec(line)) !== null) {
      allMatches.push({ start: match.index, end: match.index + match[0].length, text: match[0], type });
    }
  });

  // Keyword matching
  keywordRegex.lastIndex = 0;
  let match;
  while ((match = keywordRegex.exec(line)) !== null) {
    allMatches.push({ start: match.index, end: match.index + match[0].length, text: match[0], type: 'keyword' });
  }

  // Sort by position
  allMatches.sort((a, b) => a.start - b.start);

  // Remove overlapping matches (prefer earlier start or longer match)
  const filteredMatches = [];
  let lastEnd = 0;
  for (const m of allMatches) {
    if (m.start >= lastEnd) {
      filteredMatches.push(m);
      lastEnd = m.end;
    }
  }

  // Create TextRuns
  let pos = 0;
  for (const m of filteredMatches) {
    // Add plain text before match
    if (m.start > pos) {
      const text = line.substring(pos, m.start).replace(/^ +/, match => '\u00A0'.repeat(match.length));
      if (text) {
        result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
      }
    }
    // Add matched token
    const tokenText = m.text.replace(/^ +/, match => '\u00A0'.repeat(match.length));
    const isBold = m.type === 'keyword';
    result.push(new TextRun({
      text: tokenText,
      font: FONT_CODE,
      size: fontSize,
      color: SYNTAX_COLORS[m.type] || SYNTAX_COLORS.default,
      bold: isBold
    }));
    pos = m.end;
  }

  // Add remaining plain text
  if (pos < line.length) {
    const text = line.substring(pos).replace(/^ +/, match => '\u00A0'.repeat(match.length));
    if (text) {
      result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
    }
  }

  // If no tokens, return whole line
  if (result.length === 0) {
    const text = line.replace(/^ +/, match => '\u00A0'.repeat(match.length)) || '\u00A0';
    result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
  }

  return result;
}

/**
 * Detect if content is ASCII art/wireframe
 * ASCII art typically contains box-drawing characters
 */
function isAsciiArt(content) {
  // Box-drawing characters (Unicode range U+2500 to U+257F)
  const boxDrawingChars = /[─│┌┐└┘├┤┬┴┼═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬]/;
  // Also check for common ASCII art patterns
  const asciiArtPatterns = /[+\-|\\\/\[\]{}()<>*#@█▓▒░▀▄▌▐]/;

  // If more than 10% of lines contain box-drawing or ASCII art characters, it's ASCII art
  const lines = content.split('\n');
  const artLineCount = lines.filter(line =>
    boxDrawingChars.test(line) ||
    (asciiArtPatterns.test(line) && line.includes('|') && line.includes('-'))
  ).length;

  return artLineCount > lines.length * 0.1;
}

/**
 * Create code block
 * Reference: https://bo-sgoldhouse.blogspot.com/2021/07/word-editormd.html
 * - Uses Consolas monospace font (better readability for code)
 * - Fixed line height (compact display)
 * - Line numbers + zebra stripe background (for programming code only)
 * - NO line numbers for ASCII art/wireframes
 * - Syntax highlighting (based on VSCode Light+ colors)
 */
function createCodeBlock(content, lang = '') {
  const CODE_FONT_SIZE = 20;  // 10pt - code font size
  const LINE_NUMBER_SIZE = 18;  // 9pt - line number font size
  const CODE_LINE_HEIGHT = 280;  // Fixed line height 14pt

  // Zebra stripe background colors
  const BG_ODD = 'FFFFFF';   // Odd rows: white
  const BG_EVEN = 'F5F5F5';  // Even rows: light gray
  const LINE_NUM_COLOR = '999999';  // Line number color: gray

  // Fixed column widths (DXA units) to prevent Google Drive editing issues
  // Total page width ~9360 DXA (6.5 inches)
  const LINE_NUM_COL_WIDTH = 720;   // Fixed width ~0.5 inches for line numbers
  const CODE_COL_WIDTH = 8640;      // Remaining width for code
  const FULL_WIDTH = 9360;          // Full width for ASCII art (no line numbers)

  const lines = content.split('\n');

  // Check if this is ASCII art/wireframe - skip line numbers
  const skipLineNumbers = isAsciiArt(content);

  // Create table row for each line
  const codeRows = lines.map((line, index) => {
    const lineNum = index + 1;
    const isEven = lineNum % 2 === 0;
    const bgColor = isEven ? BG_EVEN : BG_ODD;

    // Syntax highlighting parsing (skip for ASCII art)
    const tokenizedRuns = skipLineNumbers
      ? [new TextRun({ text: line || ' ', font: FONT_CODE, size: CODE_FONT_SIZE })]
      : tokenizeLine(line, lang, CODE_FONT_SIZE);

    if (skipLineNumbers) {
      // ASCII art: single column, no line numbers
      return new TableRow({
        tableHeader: false,
        cantSplit: true,
        children: [
          new TableCell({
            width: { size: FULL_WIDTH, type: WidthType.DXA },
            shading: { fill: bgColor, type: ShadingType.CLEAR },
            verticalAlign: VerticalAlign.CENTER,
            margins: {
              top: 20, bottom: 20,
              left: 120, right: 80
            },
            textDirection: 'lrTb',
            children: [new Paragraph({
              spacing: { after: 0, line: CODE_LINE_HEIGHT, lineRule: 'exact' },
              keepNext: true,
              children: tokenizedRuns
            })]
          })
        ]
      });
    }

    // Programming code: two columns with line numbers
    return new TableRow({
      tableHeader: false,
      cantSplit: true,  // Prevent row from splitting across pages
      children: [
        // Line number column - fixed width with explicit settings
        new TableCell({
          width: { size: LINE_NUM_COL_WIDTH, type: WidthType.DXA },
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.CENTER,
          margins: {
            top: 20, bottom: 20,
            left: 80, right: 80
          },
          // Set text direction to LR_TB to ensure horizontal text flow
          textDirection: 'lrTb',
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            spacing: { after: 0, line: CODE_LINE_HEIGHT, lineRule: 'exact' },
            keepNext: true,
            children: [new TextRun({
              text: String(lineNum) + '.',
              font: FONT_CODE,
              size: LINE_NUMBER_SIZE,
              color: LINE_NUM_COLOR
            })]
          })]
        }),
        // Code column (with syntax highlighting) - explicit width
        new TableCell({
          width: { size: CODE_COL_WIDTH, type: WidthType.DXA },
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.CENTER,
          margins: {
            top: 20, bottom: 20,
            left: 120, right: 80
          },
          // Set text direction to LR_TB to ensure horizontal text flow
          textDirection: 'lrTb',
          children: [new Paragraph({
            spacing: { after: 0, line: CODE_LINE_HEIGHT, lineRule: 'exact' },
            keepNext: true,
            children: tokenizedRuns
          })]
        })
      ]
    });
  });

  // Create code table with appropriate column settings
  const columnWidths = skipLineNumbers ? [FULL_WIDTH] : [LINE_NUM_COL_WIDTH, CODE_COL_WIDTH];

  const codeTable = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: columnWidths,
    layout: 'fixed',  // Fixed table layout prevents column resizing
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
      left: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
      right: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
      insideHorizontal: { style: BorderStyle.NONE },
      insideVertical: { style: BorderStyle.NONE }
    },
    rows: codeRows
  });

  return [codeTable];
}

/**
 * Calculate table column widths - smart allocation based on content length
 * Optimized for SDD documents, ensures proper display on A4 pages
 * @param {string[]} headers - Table headers
 * @param {string[][]} rows - Table data rows
 * @param {number} totalWidth - Total table width (DXA units)
 * @param {boolean[]} noWrapColumns - Whether each column is no-wrap (ID columns)
 */
function calculateColumnWidths(headers, rows, totalWidth = 9360, noWrapColumns = []) {
  const numCols = headers.length;

  // Calculate max content length per column (Chinese chars take more space)
  const maxLengths = headers.map((h, i) => {
    let max = getTextDisplayLength(h);
    rows.forEach(row => {
      if (row[i]) {
        // Remove bold markers before calculating length
        const cleanText = row[i].replace(/\*\*/g, '');
        max = Math.max(max, getTextDisplayLength(cleanText));
      }
    });
    return max;
  });

  const totalLength = maxLengths.reduce((a, b) => a + b, 0);

  // Set different min/max width strategy based on column count
  let minWidth, maxWidth;
  if (numCols <= 2) {
    minWidth = 2000;  // 2-column table: wider columns
    maxWidth = 7000;
  } else if (numCols <= 4) {
    minWidth = 1500;  // 3-4 column table: moderate
    maxWidth = 5000;
  } else {
    minWidth = 1000;  // 5+ column table: narrower columns
    maxWidth = 3500;
  }

  // ID columns need larger minimum width (SDD-TRAIN-008 needs ~1800 DXA)
  const idMinWidth = 1800;

  // Allocate width based on content length ratio
  let widths = maxLengths.map((len, i) => {
    const ratio = totalLength > 0 ? len / totalLength : 1 / numCols;
    let width = Math.floor(ratio * totalWidth);
    // ID columns use larger minimum width
    const colMinWidth = (noWrapColumns[i]) ? idMinWidth : minWidth;
    return Math.max(colMinWidth, Math.min(maxWidth, width));
  });

  // Adjust total width to fit page width
  let currentTotal = widths.reduce((a, b) => a + b, 0);

  if (currentTotal > totalWidth) {
    // When exceeding total width, protect ID columns, reduce other columns
    const nonIdIndices = widths.map((w, i) => i).filter(i => !noWrapColumns[i]);
    const idTotal = widths.filter((w, i) => noWrapColumns[i]).reduce((a, b) => a + b, 0);
    const nonIdTotal = widths.filter((w, i) => !noWrapColumns[i]).reduce((a, b) => a + b, 0);
    const targetNonIdTotal = totalWidth - idTotal;

    if (targetNonIdTotal > 0 && nonIdTotal > 0) {
      const scale = targetNonIdTotal / nonIdTotal;
      nonIdIndices.forEach(i => {
        widths[i] = Math.floor(widths[i] * scale);
      });
    }
  }

  // Final adjustment for difference
  currentTotal = widths.reduce((a, b) => a + b, 0);
  if (currentTotal !== totalWidth) {
    const diff = totalWidth - currentTotal;
    // Allocate difference to widest non-ID column
    const nonIdWidths = widths.map((w, i) => noWrapColumns[i] ? 0 : w);
    const maxNonIdIndex = nonIdWidths.indexOf(Math.max(...nonIdWidths));
    if (maxNonIdIndex >= 0) {
      widths[maxNonIdIndex] += diff;
    } else {
      // If all are ID columns, adjust the last column
      widths[widths.length - 1] += diff;
    }
  }

  return widths;
}

/**
 * Calculate text display length (Chinese chars count as 2 units)
 */
function getTextDisplayLength(text) {
  let length = 0;
  for (const char of text) {
    if (/[\u4e00-\u9fff]/.test(char)) {
      length += 2;  // Chinese character
    } else {
      length += 1;  // English/numbers/symbols
    }
  }
  return length;
}

/**
 * Check if column is an ID column (should not wrap)
 * ID formats: SRS-XXX-NNN, SDD-XXX-NNN, REQ-XXX-NNN, SCR-XXX-NNN, etc.
 */
function isIdColumn(headerText, cellText) {
  // Check if header is ID-related (case-insensitive, ignore spaces)
  const headerNormalized = headerText.toLowerCase().replace(/\s+/g, '');
  const idHeaders = ['id', '設計id', '需求id', '編號', 'identifier', 'designid', 'requirementid'];
  if (idHeaders.some(h => headerNormalized.includes(h))) {
    return true;
  }
  // Check if content matches ID format (remove ** bold markers before checking)
  const cleanCell = cellText ? cellText.replace(/\*\*/g, '').trim() : '';
  if (cleanCell && /^(SRS|SDD|SWD|STC|REQ|SCR)-[A-Z]+-\d+/.test(cleanCell)) {
    return true;
  }
  return false;
}

function createTable(headers, rows) {
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
  const numCols = headers.length;

  // Determine which columns are ID columns (should not wrap)
  const noWrapColumns = headers.map((header, i) => {
    // Check header or first row data for ID format
    const firstRowCell = rows.length > 0 ? rows[0][i] : '';
    return isIdColumn(header, firstRowCell);
  });

  // Calculate column widths considering ID columns need larger minimum width
  const columnWidths = calculateColumnWidths(headers, rows, 9360, noWrapColumns);

  const tableRows = [
    // Header row - keep with first data row to avoid orphan header
    new TableRow({
      tableHeader: true,
      cantSplit: true,  // Don't split header row across pages
      children: headers.map((header, i) => new TableCell({
        borders: cellBorders,
        width: { size: columnWidths[i], type: WidthType.DXA },
        shading: { fill: 'D5E8F0', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          keepLines: noWrapColumns[i],  // ID 欄位不換行
          keepNext: true,  // Keep header with first data row
          children: [new TextRun({ text: header, bold: true, size: FONT_SIZE.TABLE_HEADER, font: getFont(header) })]
        })]
      }))
    }),
    ...rows.map((row, rowIndex) => new TableRow({
      cantSplit: true,  // Don't split data rows across pages
      children: row.map((cell, i) => new TableCell({
        borders: cellBorders,
        width: { size: columnWidths[i], type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          spacing: { after: 0 },
          keepLines: noWrapColumns[i],  // ID 欄位不換行
          // First row keeps with header, others don't need keepNext
          keepNext: rowIndex === 0,
          children: parseInlineFormatting(cell, FONT_SIZE.TABLE)
        })]
      }))
    }))
  ];

  return new Table({ columnWidths: columnWidths, rows: tableRows });
}

/**
 * Parse document structure, separate cover, TOC, revision history and main content
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

    // Detect cover info (from document start to before Table of Contents)
    if (section === 'cover') {
      if (trimmed.startsWith('# ')) {
        structure.coverInfo.title = trimmed.substring(2).trim();
      } else if (trimmed.startsWith('## For ') || trimmed.startsWith('**For ')) {
        structure.coverInfo.subtitle = trimmed.replace(/^##\s*For\s*|^\*\*For\s*|\*\*$/g, '').trim();
      } else if (trimmed.toLowerCase().includes('version') || trimmed.includes('版本')) {
        structure.coverInfo.version = trimmed.replace(/^Version\s*/i, '').replace(/版本\s*/, '').trim();
      } else if (trimmed.toLowerCase().includes('prepared by') || trimmed.includes('作者')) {
        structure.coverInfo.author = trimmed.replace(/^Prepared by\s*/i, '').replace(/作者\s*/, '').trim();
      } else if (trimmed.match(/^[A-Z].*\s+(Inc\.|Corp\.|Ltd\.|Co\.)$/i) || trimmed.match(/^SOMNICS/i)) {
        structure.coverInfo.organization = trimmed;
      } else if (trimmed.match(/^\d{4}-\d{2}-\d{2}$/)) {
        structure.coverInfo.date = trimmed;
      } else if (trimmed.toLowerCase().includes('table of contents') || trimmed.startsWith('## Table of Contents') || trimmed === '## 目錄') {
        section = 'toc';
      }
      i++;
      continue;
    }

    // Detect TOC section
    if (section === 'toc') {
      if (trimmed.startsWith('## Revision History') || trimmed.toLowerCase().includes('revision history') || trimmed === '## 修訂歷史') {
        section = 'revision';
        i++;
        continue;
      } else if (trimmed.startsWith('## 1') || trimmed.startsWith('## 1.') || trimmed === '---') {
        // Skip TOC, enter main content (separator --- may also indicate TOC end)
        if (trimmed === '---') {
          i++;
          continue;
        }
        section = 'main';
        continue;  // Don't i++, let main section handle this line
      }
      structure.tocLines.push(line);
      i++;
      continue;
    }

    // Detect revision history
    if (section === 'revision') {
      if (trimmed.startsWith('## 1') || trimmed === '---' || (trimmed.startsWith('## ') && !trimmed.toLowerCase().includes('revision') && !trimmed.includes('修訂'))) {
        if (trimmed === '---') {
          i++;
          continue;
        }
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

  // Blank spacing
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

  // Blank spacing
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
 * Create TOC page elements
 * Uses Word native TOC feature, need to press F9 or right-click "Update Field" to show page numbers
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
      text: 'Note: Press F9 in Word or right-click and select "Update Field" to display TOC content and page numbers',
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
    children: [new TextRun({ text: 'Revision History', bold: true, size: FONT_SIZE.H1, font: FONT_EN })]
  }));

  if (revisionLines.length > 0) {
    // 解析修訂歷史表格
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

  // Create header and footer
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
    // Heading auto-numbering settings
    // IEC 62304 document structure: ## -> 1., ### -> 1.1, #### -> 1.1.1, ##### -> 1.1.1.1
    numbering: {
      config: [
        {
          reference: 'heading-numbering',
          levels: [
            {
              level: 0,  // ## Main section -> 1., 2., 3.
              format: LevelFormat.DECIMAL,
              text: '%1.',
              alignment: AlignmentType.START,
              style: {
                paragraph: {
                  indent: { left: 0, hanging: 0 }
                }
              }
            },
            {
              level: 1,  // ### Subsection -> 1.1, 1.2
              format: LevelFormat.DECIMAL,
              text: '%1.%2',
              alignment: AlignmentType.START,
              style: {
                paragraph: {
                  indent: { left: 0, hanging: 0 }
                }
              }
            },
            {
              level: 2,  // #### -> 1.1.1
              format: LevelFormat.DECIMAL,
              text: '%1.%2.%3',
              alignment: AlignmentType.START,
              style: {
                paragraph: {
                  indent: { left: 0, hanging: 0 }
                }
              }
            },
            {
              level: 3,  // ##### -> 1.1.1.1
              format: LevelFormat.DECIMAL,
              text: '%1.%2.%3.%4',
              alignment: AlignmentType.START,
              style: {
                paragraph: {
                  indent: { left: 0, hanging: 0 }
                }
              }
            }
          ]
        }
      ]
    },
    styles: {
      default: {
        document: {
          run: {
            font: {
              ascii: FONT_EN,       // English uses Arial
              eastAsia: FONT_CN,    // Chinese uses Microsoft JhengHei
              hAnsi: FONT_EN,
              cs: FONT_EN
            },
            size: FONT_SIZE.BODY
          }
        }
      },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: FONT_SIZE.H1, bold: true, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: FONT_SIZE.H2, bold: true, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: FONT_SIZE.H3, bold: true, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
        { id: 'Heading4', name: 'Heading 4', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: FONT_SIZE.H4, bold: true, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 3 } },
        { id: 'Heading5', name: 'Heading 5', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: FONT_SIZE.H5, bold: true, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 4 } },
        // TOC styles - increase spacing between TOC entries
        { id: 'Toc1', name: 'TOC 1', basedOn: 'Normal', next: 'Normal',
          run: { size: FONT_SIZE.BODY, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 120, after: 60 } } },
        { id: 'Toc2', name: 'TOC 2', basedOn: 'Normal', next: 'Normal',
          run: { size: FONT_SIZE.BODY, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 80, after: 40 }, indent: { left: 240 } } },
        { id: 'Toc3', name: 'TOC 3', basedOn: 'Normal', next: 'Normal',
          run: { size: FONT_SIZE.BODY, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 60, after: 30 }, indent: { left: 480 } } },
        { id: 'Toc4', name: 'TOC 4', basedOn: 'Normal', next: 'Normal',
          run: { size: FONT_SIZE.BODY, font: { ascii: FONT_EN, eastAsia: FONT_CN, hAnsi: FONT_EN } },
          paragraph: { spacing: { before: 40, after: 20 }, indent: { left: 720 } } }
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
  // cleanupMermaidTemp(outputDir);  // DEBUG
}

// ============================================
// Command Line Interface
// ============================================

// Usage: node md-to-docx.js <input.md> [output.docx]
// Example: node md-to-docx.js SRS-SomniLand-1.0.md
// Example: node md-to-docx.js SDD-Project.md SDD-Project-v1.docx

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('Usage: node md-to-docx.js <input.md> [output.docx]');
  console.log('');
  console.log('Examples:');
  console.log('  node md-to-docx.js SRS-SomniLand-1.0.md');
  console.log('  node md-to-docx.js SDD-Project.md SDD-Project-v1.docx');
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1] || inputFile.replace('.md', '.docx');
const docTitle = path.basename(outputFile, '.docx');

if (!fs.existsSync(inputFile)) {
  console.error(`Error: Input file not found: ${inputFile}`);
  process.exit(1);
}

convertMdToDocx(inputFile, outputFile, docTitle);
