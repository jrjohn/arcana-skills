const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
        ImageRun, TableOfContents, LevelFormat, convertInchesToTwip } = require('docx');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

// ============================================
// 字型設定 - 中文使用微軟正黑體，英文使用 Arial
// ============================================
const FONT_CN = '微軟正黑體';  // 中文字體 (繁體/簡體中文統一使用)
const FONT_EN = 'Arial';       // 英文字體
const FONT_CODE = 'Consolas';  // 程式碼字體 (等寬字體，較易閱讀)

// 字型大小設定 (單位: half-points, 24 = 12pt)
// 針對 A4 頁面與 IEC 62304 文件可讀性優化
const FONT_SIZE = {
  H1: 36,        // 18pt - 主標題
  H2: 32,        // 16pt - 大章節
  H3: 28,        // 14pt - 小節
  H4: 26,        // 13pt - 子節
  H5: 24,        // 12pt - 細節
  BODY: 22,      // 11pt - 內文
  TABLE: 22,     // 11pt - 表格內文 (從 10pt 調整為 11pt，提高可讀性)
  TABLE_HEADER: 22, // 11pt - 表格標題 (粗體，與內文一致)
  SMALL: 18,     // 9pt - 小字
  FOOTER: 18     // 9pt - 頁尾
};

/**
 * 檢測文字是否包含中文
 */
function containsChinese(text) {
  return /[\u4e00-\u9fff]/.test(text);
}

/**
 * 取得適合的字體物件（根據文字內容）
 * 返回 docx 庫需要的字型物件格式，確保中英文字型正確分離
 */
function getFont(text) {
  // 無論內容如何，都使用統一的字型設定：
  // - 英文/半形字元使用 Arial
  // - 中文/全形字元使用微軟正黑體 (繁體/簡體中文統一)
  return {
    ascii: FONT_EN,      // 英文字元
    eastAsia: FONT_CN,   // 中文字元 (東亞語系) - 微軟正黑體
    hAnsi: FONT_EN,      // 高位 ANSI 字元
    cs: FONT_EN          // 複雜腳本字元
  };
}

/**
 * 取得純英文字型（用於明確只需要英文的場合）
 */
function getFontEnglishOnly() {
  return FONT_EN;
}

// ============================================
// Mermaid 圖表渲染器
// ============================================

/**
 * 判斷 Mermaid 圖表類型，決定渲染寬度
 * block-beta (UI wireframe) 使用較窄寬度，其他圖表使用較寬寬度
 */
function getMermaidRenderWidth(mermaidCode) {
  const firstLine = mermaidCode.trim().split('\n')[0].toLowerCase();

  // block-beta 是 UI wireframe，通常是垂直手機畫面，用窄寬度
  if (firstLine.includes('block-beta')) {
    return 500;  // 窄寬度適合手機 wireframe
  }

  // 其他圖表類型使用標準寬度
  return 1200;
}

/**
 * 建立 Mermaid 配置檔案
 * 設定 htmlLabels: false 以使用原生 SVG <text> 元素，確保 Word 相容性
 *
 * 問題背景：Mermaid 預設使用 foreignObject 內嵌 HTML 文字，
 * Word/Inkscape 等應用無法正確渲染 foreignObject 中的文字。
 * 解決方案：設定 htmlLabels: false 改用原生 SVG text 元素。
 *
 * 參考：https://github.com/mermaid-js/mermaid/issues/2688
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
      "edgeLabelBackground": "#FFC107",
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
 * 從 Mermaid 代碼中解析樣式定義
 * 解析 style NodeId fill:#xxx,stroke:#xxx,color:#xxx 格式
 * @param {string} mermaidCode - Mermaid 圖表代碼
 * @returns {Map<string, {fill: string, color: string}>} - 節點ID對應的樣式
 */
function parseMermaidStyles(mermaidCode) {
  const styles = new Map();

  // 匹配 style NodeId fill:#xxx,stroke:#xxx,color:#xxx
  const styleRegex = /style\s+(\w+)\s+fill:(#[0-9A-Fa-f]{3,6})[^,]*(?:,stroke:[^,]*)?(?:,color:(#[0-9A-Fa-f]{3,6}|#\w+))?/g;
  let match;

  while ((match = styleRegex.exec(mermaidCode)) !== null) {
    const nodeId = match[1];
    const fill = match[2];
    const color = match[3] || null;
    styles.set(nodeId, { fill, color });
  }

  // 也解析 classDef 定義
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
 * 根據背景色決定適當的文字顏色
 * 使用 WCAG 對比度演算法
 * @param {string} bgColor - 背景色 (hex 格式)
 * @returns {string} - 建議的文字顏色
 */
function getContrastTextColor(bgColor) {
  // 定義顏色對應表 (依據參考圖片的配色)
  const colorMap = {
    '#2196F3': '#ffffff',  // 藍色 → 白字
    '#2196f3': '#ffffff',
    '#1976D2': '#ffffff',  // 深藍 → 白字
    '#1976d2': '#ffffff',
    '#FFC107': '#5D4037',  // 金色 → 深棕字
    '#ffc107': '#5D4037',
    '#FFA000': '#5D4037',  // 深金 → 深棕字
    '#ffa000': '#5D4037',
    '#A8E6CF': '#2E7D32',  // 薄荷綠 → 深綠字
    '#a8e6cf': '#2E7D32',
    '#81C784': '#1B5E20',  // 綠色 → 深綠字
    '#81c784': '#1B5E20',
    '#9E9E9E': '#ffffff',  // 灰色 → 白字
    '#9e9e9e': '#ffffff',
    '#757575': '#ffffff',  // 深灰 → 白字
    '#FFCDD2': '#5D4037',  // 粉紅 → 深棕字
    '#ffcdd2': '#5D4037',
    '#B3E5FC': '#01579B',  // 淺藍 → 深藍字
    '#b3e5fc': '#01579B',
    '#FFF9C4': '#5D4037',  // 淺黃 → 深棕字
    '#fff9c4': '#5D4037',
    '#ECEFF1': '#546E7A',  // 淺灰 → 深灰字
    '#eceff1': '#546E7A',
    '#EF5350': '#ffffff',  // 紅色 → 白字
    '#ef5350': '#ffffff',
    '#26A69A': '#ffffff',  // 青綠 → 白字
    '#26a69a': '#ffffff',
    '#FFA726': '#5D4037',  // 橙色 → 深棕字
    '#ffa726': '#5D4037',
    '#64B5F6': '#0D47A1',  // 天藍 → 深藍字
    '#64b5f6': '#0D47A1',
  };

  if (colorMap[bgColor]) {
    return colorMap[bgColor];
  }

  // 未知顏色，使用亮度計算
  const hex = bgColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.5 ? '#333333' : '#ffffff';
}

/**
 * 後處理 SVG 文字顏色
 * 根據背景色設定適當的文字顏色
 * @param {string} svgContent - SVG 內容
 * @param {string} mermaidCode - 原始 Mermaid 代碼
 * @returns {string} - 處理後的 SVG 內容
 */
function postProcessSvgTextColors(svgContent, mermaidCode) {
  const styles = parseMermaidStyles(mermaidCode);

  // 為每個已定義樣式的節點，注入 CSS 樣式
  let cssRules = [];

  styles.forEach((style, key) => {
    if (key.startsWith('class:')) {
      return; // classDef 稍後處理
    }

    const textColor = style.color || getContrastTextColor(style.fill);
    // Mermaid 產生的 SVG 中，節點文字通常在 .nodeLabel 或直接是 text 元素
    cssRules.push(`#${key} .nodeLabel { fill: ${textColor} !important; color: ${textColor} !important; }`);
    cssRules.push(`#${key} text { fill: ${textColor} !important; }`);
    cssRules.push(`#${key} tspan { fill: ${textColor} !important; }`);
    // 也處理 foreignObject 內的 div
    cssRules.push(`#${key} foreignObject div { color: ${textColor} !important; }`);
  });

  // 處理 classDef
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

  // 注入 CSS 樣式到 SVG
  const styleTag = `<style type="text/css">\n${cssRules.join('\n')}\n</style>`;

  // 在 <svg> 標籤後插入 style
  if (svgContent.includes('</defs>')) {
    svgContent = svgContent.replace('</defs>', `</defs>\n${styleTag}`);
  } else if (svgContent.includes('<svg')) {
    svgContent = svgContent.replace(/<svg([^>]*)>/, `<svg$1>\n${styleTag}`);
  }

  return svgContent;
}

/**
 * 解析 SVG transformation matrix 並計算實際座標
 * @param {string} transform - transformation 字串，如 "matrix(a,b,c,d,e,f)"
 * @param {number} x - 原始 x 座標
 * @param {number} y - 原始 y 座標
 * @returns {{x: number, y: number}} - 轉換後的座標
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
 * 從 path 的 d 屬性提取邊界框
 * @param {string} d - path 的 d 屬性
 * @returns {{minX: number, minY: number, maxX: number, maxY: number}|null}
 */
function getPathBounds(d) {
  // 矩形 path 格式: "M x1 y1 H x2 V y2 H x3 Z" (可能沒有空格)
  // 例如: "M-84.11719-39H84.11719V39H-84.11719Z"
  // 提取所有數字（包括負數和小數）
  const numbers = d.match(/-?\d+\.?\d*/g);
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
 * 後處理 mutool 產生的 SVG，修正藍色方框內的文字顏色
 * @param {string} svgContent - SVG 內容
 * @returns {string} - 處理後的 SVG 內容
 */
function postProcessMutoolSvg(svgContent) {
  // 需要白色文字的背景色列表（藍色系）
  const blueBackgrounds = ['#2196f3', '#42a5f5', '#1976d2'];
  // 需要白色文字的其他背景色（深色）
  const darkBackgrounds = ['#ffa726', '#26a69a', '#00897b'];
  const allWhiteTextBackgrounds = [...blueBackgrounds, ...darkBackgrounds];

  // 找到所有藍色/深色方框的位置
  const boxBounds = [];

  // 匹配 path 元素（方框）
  const pathRegex = /<path\s+transform="([^"]+)"\s+d="([^"]+)"\s+fill="(#[0-9a-fA-F]{6})"/g;
  let match;
  while ((match = pathRegex.exec(svgContent)) !== null) {
    const [, transform, d, fill] = match;
    if (allWhiteTextBackgrounds.includes(fill.toLowerCase())) {
      const bounds = getPathBounds(d);
      if (bounds) {
        // 應用 transform 到邊界
        const topLeft = applyTransform(transform, bounds.minX, bounds.minY);
        const bottomRight = applyTransform(transform, bounds.maxX, bounds.maxY);
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

  // 如果沒有找到藍色方框，直接返回
  if (boxBounds.length === 0) {
    return svgContent;
  }

  // 找到所有文字元素並檢查是否在藍色方框內
  // 文字元素格式: <use data-text="X" xlink:href="..." transform="matrix(...)" fill="#ababab"/>
  // 或: <path transform="matrix(...)" d="..." fill="#ababab"/>（字形路徑）

  const textRegex = /<(use|path)\s+([^>]*transform="matrix\(([^)]+)\)"[^>]*fill="#ababab"[^>]*)\/>/g;

  svgContent = svgContent.replace(textRegex, (fullMatch, tag, attrs, matrixValues) => {
    // 從 transform 提取位置
    const [a, b, c, d, e, f] = matrixValues.split(',').map(parseFloat);
    const textX = e;
    const textY = f;

    // 檢查文字是否在任何藍色方框內
    const isInBox = boxBounds.some(box =>
      textX >= box.minX && textX <= box.maxX &&
      textY >= box.minY && textY <= box.maxY
    );

    if (isInBox) {
      // 將 fill="#ababab" 替換為 fill="#ffffff"
      return fullMatch.replace('fill="#ababab"', 'fill="#ffffff"');
    }

    return fullMatch;
  });

  return svgContent;
}

/**
 * 將 Mermaid 代碼渲染為 SVG + PNG (SVG 為主，PNG 作為 fallback)
 * 使用 htmlLabels: false 確保 SVG 文字使用原生 <text> 元素，Word 可正確顯示
 *
 * @param {string} mermaidCode - Mermaid 圖表代碼
 * @param {string} outputDir - 輸出目錄
 * @returns {{svg: string|null, png: string|null}} - SVG 和 PNG 圖片路徑
 */
function renderMermaidToSvgAndPng(mermaidCode, outputDir) {
  const hash = crypto.createHash('md5').update(mermaidCode).digest('hex').substring(0, 8);
  const tempDir = path.join(outputDir, '.mermaid-temp');
  const inputFile = path.join(tempDir, `mermaid-${hash}.mmd`);
  const svgFile = path.join(tempDir, `mermaid-${hash}.svg`);
  const pngFile = path.join(tempDir, `mermaid-${hash}.png`);

  // 建立暫存目錄
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  // 如果已存在快取，直接回傳
  const hasSvg = fs.existsSync(svgFile);
  const hasPng = fs.existsSync(pngFile);
  if (hasSvg && hasPng) {
    return { svg: svgFile, png: pngFile };
  }

  // 建立 Mermaid 配置檔 (htmlLabels: false)
  const configPath = createMermaidConfig(tempDir);

  // 寫入 Mermaid 代碼
  fs.writeFileSync(inputFile, mermaidCode);

  // 根據圖表類型決定渲染寬度
  const renderWidth = getMermaidRenderWidth(mermaidCode);

  let svgPath = null;
  let pngPath = null;

  // 使用 PDF→mutool 路徑（文字轉為向量路徑，確保 Word 相容性）
  // 這是 Mermaid 官方建議的解決方案，因為直接產生的 SVG 節點標籤會使用 foreignObject
  // Word 不支援 foreignObject，所以需要將文字轉為路徑
  // 參考：https://github.com/mermaid-js/mermaid/issues/2688
  const pdfFile = path.join(tempDir, `mermaid-${hash}.pdf`);
  try {
    // Step 1: 產生 PDF (Mermaid 的 PDF 輸出會將文字轉為路徑，並套用 style 指定的顏色)
    execSync(`mmdc -i "${inputFile}" -o "${pdfFile}" -c "${configPath}" --pdfFit 2>/dev/null`, {
      stdio: 'pipe',
      timeout: 60000
    });

    if (fs.existsSync(pdfFile)) {
      // Step 2: 使用 mutool 將 PDF 轉換為 SVG (文字會轉為路徑，確保相容性)
      // 需要先檢查是否有 mutool
      // 注意：mutool 會在輸出檔名加上頁碼，如 output.svg -> output1.svg
      const mutoolOutputBase = path.join(tempDir, `svg-${hash}`);
      const mutoolSvgFile = `${mutoolOutputBase}1.svg`;  // mutool 會產生這個檔名
      try {
        execSync(`which mutool`, { stdio: 'pipe' });
        execSync(`mutool draw -F svg -o "${mutoolOutputBase}.svg" "${pdfFile}" 2>/dev/null`, {
          stdio: 'pipe',
          timeout: 60000
        });
        // mutool 產生的檔名帶頁碼，需要重命名
        if (fs.existsSync(mutoolSvgFile)) {
          fs.renameSync(mutoolSvgFile, svgFile);
          // 後處理 SVG：修正藍色方框內的文字顏色
          let svgContent = fs.readFileSync(svgFile, 'utf-8');
          svgContent = postProcessMutoolSvg(svgContent);
          fs.writeFileSync(svgFile, svgContent);
          svgPath = svgFile;
        }
      } catch (mutoolError) {
        // 沒有 mutool，fallback 到直接 SVG (文字可能不顯示)
        console.warn(`  ⚠ mutool 未安裝，使用直接 SVG 輸出 (Word 中文字可能不顯示)`);
        console.warn(`    安裝方式: brew install mupdf-tools`);
        execSync(`mmdc -i "${inputFile}" -o "${svgFile}" -c "${configPath}" -b white 2>/dev/null`, {
          stdio: 'pipe',
          timeout: 60000
        });
        if (fs.existsSync(svgFile)) {
          svgPath = svgFile;
        }
      }
      // 清理 PDF 暫存檔
      if (fs.existsSync(pdfFile)) {
        fs.unlinkSync(pdfFile);
      }
    }
  } catch (error) {
    // PDF 產生失敗，fallback 到直接 SVG
    console.warn(`PDF 渲染失敗 [${hash}]: ${error.message}`);
    try {
      execSync(`mmdc -i "${inputFile}" -o "${svgFile}" -c "${configPath}" -b white 2>/dev/null`, {
        stdio: 'pipe',
        timeout: 60000
      });
      if (fs.existsSync(svgFile)) {
        svgPath = svgFile;
      }
    } catch (svgError) {
      console.warn(`SVG 渲染也失敗 [${hash}]: ${svgError.message}`);
    }
  }

  // 2. 渲染 PNG (作為 fallback，供舊版 Word 使用)
  try {
    execSync(`mmdc -i "${inputFile}" -o "${pngFile}" -c "${configPath}" -b white -w ${renderWidth} -s 2`, {
      stdio: 'pipe',
      timeout: 60000
    });
    if (fs.existsSync(pngFile)) {
      pngPath = pngFile;
    }
  } catch (error) {
    console.warn(`PNG 渲染失敗 [${hash}]: ${error.message}`);
  }

  return { svg: svgPath, png: pngPath };
}

/**
 * 向下相容函數：將 Mermaid 代碼渲染為 PNG 圖片
 * @deprecated 請使用 renderMermaidToSvgAndPng
 */
function renderMermaidToPng(mermaidCode, outputDir) {
  const result = renderMermaidToSvgAndPng(mermaidCode, outputDir);
  return result.png;
}

/**
 * 讀取 PNG 圖片尺寸
 * PNG 檔案格式：前 8 bytes 為簽名，IHDR chunk 包含寬高資訊
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
 * 從 SVG 內容解析 viewBox 或 width/height 來取得尺寸
 */
function getSvgDimensions(svgContent) {
  // 嘗試從 viewBox 解析
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

  // 嘗試從 width/height 屬性解析
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
 * 建立 Mermaid 圖片段落 - 使用 SVG with PNG fallback
 * SVG 為向量格式，確保任意縮放不失真 (需 Office 2019+ 或 Microsoft 365)
 * PNG 作為舊版 Word 的 fallback
 * 保持原始比例，最大寬度 550px (A4 頁面寬度約 6 吋 = 576px)
 * 圖片置中顯示
 */
function createMermaidImageWithSvg(svgPath, pngPath) {
  const svgBuffer = fs.readFileSync(svgPath);
  const pngBuffer = fs.readFileSync(pngPath);
  const svgContent = svgBuffer.toString('utf-8');

  // 從 SVG 或 PNG 取得尺寸
  let dimensions = getSvgDimensions(svgContent);
  if (!dimensions) {
    dimensions = getPngDimensions(pngBuffer);
  }

  let displayWidth, displayHeight;
  const maxWidth = 550;  // 最大寬度限制，A4 頁面寬度 (含邊距) 約 6 吋
  const maxHeight = 600; // 最大高度限制，避免超出單頁

  if (dimensions) {
    const { width, height } = dimensions;
    const aspectRatio = width / height;

    // 根據最大限制計算縮放後的尺寸
    if (width > maxWidth) {
      displayWidth = maxWidth;
      displayHeight = Math.round(maxWidth / aspectRatio);
    } else {
      displayWidth = width;
      displayHeight = height;
    }

    // 如果高度仍超過限制，再次縮放
    if (displayHeight > maxHeight) {
      displayHeight = maxHeight;
      displayWidth = Math.round(maxHeight * aspectRatio);
    }

    // 確保圖片有最小尺寸 (避免過小圖片)
    const minWidth = 200;
    if (displayWidth < minWidth && width >= minWidth) {
      displayWidth = minWidth;
      displayHeight = Math.round(minWidth / aspectRatio);
    }
  } else {
    // 無法讀取尺寸時使用預設值
    displayWidth = 450;
    displayHeight = 350;
  }

  // 使用 SVG with PNG fallback (docx 庫 v9.x 支援)
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
 * 建立 Mermaid 圖片段落 - 僅使用 PNG (向下相容)
 * @deprecated 請使用 createMermaidImageWithSvg
 */
function createMermaidImage(imagePath) {
  const imageBuffer = fs.readFileSync(imagePath);

  // 讀取實際圖片尺寸
  const dimensions = getPngDimensions(imageBuffer);

  let displayWidth, displayHeight;
  const maxWidth = 550;  // 最大寬度限制，A4 頁面寬度 (含邊距) 約 6 吋
  const maxHeight = 600; // 最大高度限制，避免超出單頁

  if (dimensions) {
    const { width, height } = dimensions;
    const aspectRatio = width / height;

    // 根據最大限制計算縮放後的尺寸
    if (width > maxWidth) {
      displayWidth = maxWidth;
      displayHeight = Math.round(maxWidth / aspectRatio);
    } else {
      displayWidth = width;
      displayHeight = height;
    }

    // 如果高度仍超過限制，再次縮放
    if (displayHeight > maxHeight) {
      displayHeight = maxHeight;
      displayWidth = Math.round(maxHeight * aspectRatio);
    }

    // 確保圖片有最小尺寸 (避免過小圖片)
    const minWidth = 200;
    if (displayWidth < minWidth && width >= minWidth) {
      displayWidth = minWidth;
      displayHeight = Math.round(minWidth / aspectRatio);
    }
  } else {
    // 無法讀取尺寸時使用預設值
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
 * 清理 Mermaid 暫存檔案
 */
function cleanupMermaidTemp(outputDir) {
  const tempDir = path.join(outputDir, '.mermaid-temp');
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

// ============================================
// 需求項目表格化轉換器
// ============================================

/**
 * 檢測是否為需求項目標題
 * 支援格式：
 *   - #### SRS-AUTH-001 使用者註冊 (舊格式)
 *   - ##### REQ-FUNC-001 使用者登入 (新格式，空格分隔)
 *   - #### REQ-FUNC-001: 使用者登入 (新格式，冒號分隔)
 */
function isRequirementHeading(line) {
  // 支援 SRS/SWD/SDD/STC/REQ 前綴，3-5個#
  return line.match(/^#{3,5}\s+(SRS|SWD|SDD|STC|REQ)-[A-Z]+-\d+/);
}

/**
 * 解析需求項目區塊，轉換為表格式結構
 * 支援多種輸入格式：
 *
 * 舊格式 (中文欄位)：
 *   #### SRS-AUTH-001 使用者註冊
 *   **描述：** 系統必須...
 *   **優先級：** 必要
 *   **驗收標準：**
 *   - AC1: Given...
 *
 * 新格式 (英文欄位)：
 *   ##### REQ-FUNC-001 使用者登入
 *   **Statement:** 系統應...
 *   **Rationale:** 理由...
 *   **Acceptance Criteria:**
 *   - AC1: Given...
 *   **Verification Method:** Test
 */
function parseRequirementBlock(lines, startIndex) {
  const headerLine = lines[startIndex];

  // 嘗試匹配：ID + 空格 + 名稱，或 ID + 冒號 + 名稱
  let match = headerLine.match(/^#{3,5}\s+((SRS|SWD|SDD|STC|REQ)-[A-Z]+-\d+)[:：]?\s*(.+)/);

  if (!match) return null;

  const reqId = match[1];
  const reqName = match[3] ? match[3].trim() : '';

  const requirement = {
    id: reqId,
    name: reqName,
    // 支援中英文欄位
    description: '',      // 描述 (舊)
    statement: '',        // Statement (新)
    rationale: '',        // Rationale (新)
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

    // 遇到下一個標題或分隔線則結束
    if (line.startsWith('#') || line.match(/^-{3,}$/)) {
      break;
    }

    // 解析 **欄位：** 值 或 **欄位:** 值 格式
    const fieldMatch = line.match(/^\*\*(.+?)[:：]\*\*\s*(.*)$/);

    if (fieldMatch) {
      const fieldName = fieldMatch[1].trim();
      const fieldValue = fieldMatch[2].trim();

      // 中文欄位
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
      // 英文欄位
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
      // 驗收標準項目
      requirement.acceptanceCriteria.push(line.substring(2));
    } else if (line && currentField) {
      // 延續上一個欄位的內容
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
 * 建立需求項目表格
 * 自動判斷使用中文或英文欄位標籤，並套用適當字體
 */
function createRequirementTable(req) {
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

  const labelWidth = 2200;  // 標籤欄寬度（加寬以容納中文）
  const valueWidth = 7160;  // 值欄寬度

  const rows = [];

  // 標題列 (合併儲存格效果用背景色區分)
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

  // 新格式欄位 (Statement/Rationale)
  if (req.statement) {
    rows.push(createFieldRow('Statement', req.statement, labelWidth, valueWidth, cellBorders));
  }

  if (req.rationale) {
    rows.push(createFieldRow('Rationale', req.rationale, labelWidth, valueWidth, cellBorders));
  }

  // 舊格式欄位 (描述)
  if (req.description) {
    rows.push(createFieldRow('描述', req.description, labelWidth, valueWidth, cellBorders));
  }

  // 優先級
  if (req.priority) {
    rows.push(createFieldRow('優先級', req.priority, labelWidth, valueWidth, cellBorders));
  }

  // 安全分類
  if (req.safetyClass) {
    rows.push(createFieldRow('安全分類', req.safetyClass, labelWidth, valueWidth, cellBorders));
  }

  // 其他欄位
  for (const [key, value] of Object.entries(req.otherFields)) {
    rows.push(createFieldRow(key, value, labelWidth, valueWidth, cellBorders));
  }

  // 驗收標準 (Acceptance Criteria)
  if (req.acceptanceCriteria.length > 0) {
    // 判斷使用中文還是英文標籤
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

  // Verification Method (新格式)
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
// 主要解析函式
// ============================================

/**
 * 檢查是否為「孤立標題群」的第一個標題
 * 當連續多個標題（沒有中間內容）最後接著需求表格時，只在第一個標題前分頁
 * 避免標題群落在頁尾，但又不會每個標題都分頁造成空頁
 */
function shouldBreakBeforeHeading(lines, currentIndex) {
  const currentLine = lines[currentIndex];

  // 檢查前一個非空行是否也是標題
  let prevIndex = currentIndex - 1;
  while (prevIndex >= 0 && lines[prevIndex].trim() === '') {
    prevIndex--;
  }

  // 如果前面也是標題，則不分頁（讓標題群保持在一起）
  if (prevIndex >= 0 && lines[prevIndex].startsWith('#')) {
    return false;
  }

  // 往後看，找到這個標題群的結尾
  let j = currentIndex + 1;
  let headingCount = 1;

  while (j < lines.length) {
    const line = lines[j].trim();

    if (line === '') {
      j++;
      continue;
    }

    // 如果是另一個標題，繼續往後看
    if (line.startsWith('#') && !isRequirementHeading(lines[j])) {
      headingCount++;
      j++;
      continue;
    }

    // 如果是需求項目或其他內容，停止
    break;
  }

  // 只有當有連續多個標題（標題群）時，才在第一個標題前分頁
  // 這樣可以避免標題群被分頁切開
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

    // 處理程式碼區塊
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // 結束程式碼區塊
        if (codeBlockLang === 'mermaid') {
          // Mermaid 圖表 - 渲染為 SVG + PNG (SVG 為主)
          const mermaidCode = codeBlockContent.join('\n');
          const { svg: svgPath, png: pngPath } = renderMermaidToSvgAndPng(mermaidCode, outputDir);
          if (svgPath && pngPath) {
            // 使用 SVG with PNG fallback (向量品質)
            elements.push(createMermaidImageWithSvg(svgPath, pngPath));
          } else if (pngPath) {
            // SVG 失敗，僅使用 PNG
            elements.push(createMermaidImage(pngPath));
          } else {
            // 渲染完全失敗，fallback 為程式碼區塊
            console.warn('Mermaid 渲染失敗，使用程式碼區塊顯示');
            elements.push(...createCodeBlock(mermaidCode));
          }
        } else {
          // 一般程式碼區塊 (傳入語言參數以支援語法高亮)
          elements.push(...createCodeBlock(codeBlockContent.join('\n'), codeBlockLang));
        }
        codeBlockContent = [];
        codeBlockLang = '';
        inCodeBlock = false;
      } else {
        // 開始程式碼區塊，擷取語言
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

    // 處理 Markdown 表格
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

    // 檢查是否為需求項目標題 - 轉換為表格式
    if (isRequirementHeading(line)) {
      const result = parseRequirementBlock(lines, i);
      if (result) {
        elements.push(new Paragraph({ spacing: { before: 240 }, children: [] })); // 間距
        elements.push(createRequirementTable(result.requirement));
        elements.push(new Paragraph({ spacing: { after: 120 }, children: [] })); // 間距
        i = result.endIndex + 1;
        continue;
      }
    }

    // 標題處理
    // Heading 1 (# ) - 主標題 (封面標題不編號)
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      const headingText = line.substring(2);
      // 封面標題（Software Requirements Specification, Software Design Description 等）不使用自動編號
      const isCoverTitle = headingText.match(/^(Software|For\s)/i);
      elements.push(createHeading(headingText, HeadingLevel.HEADING_1, true, !isCoverTitle)); // 分頁
      i++;
      continue;
    }
    // Heading 2 (## ) - 大章節，每個大章節前分頁
    if (line.startsWith('## ')) {
      const headingText = line.substring(3);
      // 檢查是否為主要章節（如 "Introduction", "Product Overview" 等，已移除手動編號）
      // 特殊標題（Table of Contents, Revision History, 目錄, 修訂歷史）不使用自動編號
      const isSpecialSection = headingText.match(/^(Table of Contents|Revision History|目錄|修訂歷史|For\s)/i);
      const isMainSection = !isSpecialSection; // 非特殊章節則在前面分頁
      elements.push(createHeading(headingText, HeadingLevel.HEADING_2, isMainSection, !isSpecialSection));
      i++;
      continue;
    }
    // Heading 3 (### ) - 小節
    if (line.startsWith('### ')) {
      // 檢查標題後是否緊接需求表格或只有空行，若是則在標題前分頁避免標題落單
      const shouldPageBreak = shouldBreakBeforeHeading(lines, i);
      elements.push(createHeading(line.substring(4), HeadingLevel.HEADING_3, shouldPageBreak, true));
      i++;
      continue;
    }
    // Heading 4 (#### )
    if (line.startsWith('#### ')) {
      // 檢查標題後是否緊接需求表格或只有空行，若是則在標題前分頁避免標題落單
      const shouldPageBreak = shouldBreakBeforeHeading(lines, i);
      elements.push(createHeading(line.substring(5), HeadingLevel.HEADING_4, shouldPageBreak, true));
      i++;
      continue;
    }
    // Heading 5 (##### )
    if (line.startsWith('##### ')) {
      elements.push(createHeading(line.substring(6), HeadingLevel.HEADING_5, false, true));
      i++;
      continue;
    }

    // 分隔線
    if (line.match(/^-{3,}$/) || line.match(/^\*{3,}$/)) {
      i++;
      continue;
    }

    // 空白行
    if (line.trim() === '') {
      i++;
      continue;
    }

    // 一般段落
    elements.push(createParagraph(line));
    i++;
  }

  // 關閉未結束的表格
  if (inTable && tableHeaders.length > 0) {
    elements.push(createTable(tableHeaders, tableRows));
  }

  return elements;
}

function parseTableRow(line) {
  return line.split('|').slice(1, -1).map(cell => cell.trim());
}

/**
 * 根據標題層級取得字型大小
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
 * 建立標題段落
 * @param {string} text - 標題文字
 * @param {HeadingLevel} level - 標題層級
 * @param {boolean} pageBreakBefore - 是否在標題前分頁（用於大章節）
 * @param {boolean} useNumbering - 是否使用自動編號（預設 true）
 */
function createHeading(text, level, pageBreakBefore = false, useNumbering = true) {
  const trimmedText = text.trim();
  const fontSize = getHeadingSize(level);

  // 將 HeadingLevel 轉換為 numbering level (0-based)
  // 注意：對於 IEC 62304 文件 (SRS/SDD/SWD 等)：
  //   - # (H1) 用於封面標題（不編號）
  //   - ## (H2) 用於主章節 → 編號 1., 2., 3. (level 0)
  //   - ### (H3) 用於子章節 → 編號 1.1, 1.2 (level 1)
  //   - #### (H4) → 編號 1.1.1 (level 2)
  //   - ##### (H5) → 編號 1.1.1.1 (level 3)
  // 因此 H1 不使用編號，H2~H5 對應 level 0~3
  const numberingLevel = {
    [HeadingLevel.HEADING_1]: undefined,  // H1 封面標題不編號
    [HeadingLevel.HEADING_2]: 0,  // ## → 1., 2., 3.
    [HeadingLevel.HEADING_3]: 1,  // ### → 1.1, 1.2
    [HeadingLevel.HEADING_4]: 2,  // #### → 1.1.1
    [HeadingLevel.HEADING_5]: 3   // ##### → 1.1.1.1
  }[level];

  const paragraphOptions = {
    heading: level,
    spacing: { before: pageBreakBefore ? 0 : 240, after: 120 },
    pageBreakBefore: pageBreakBefore,  // 大章節前分頁
    keepNext: true,  // 標題與下一段落保持在同一頁（避免標題落單）
    keepLines: true, // 標題本身不拆行
    children: [new TextRun({ text: trimmedText, bold: true, size: fontSize, font: getFont(trimmedText) })]
  };

  // 如果啟用自動編號，且 level 有對應的 numbering level
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

  // 判斷是否為「小標題段落」：以 `:` 或 `：` 結尾的粗體段落
  // 例如：「**iOS 架構分層：**」、「**互動行為**」
  // 這類段落應與下一個內容（圖片、程式碼區塊）保持在同一頁
  const isSubHeading = /\*\*[^*]+[：:]\*\*\s*$/.test(text.trim()) ||
                       /\*\*[^*]+\*\*\s*$/.test(text.trim());

  return new Paragraph({
    spacing: { after: 120 },
    keepNext: isSubHeading,  // 小標題段落與下一內容保持同頁
    children: runs
  });
}

/**
 * 解析行內格式（粗體、程式碼）
 * @param {string} text - 原始文字
 * @param {number} fontSize - 字型大小，預設為 BODY 大小
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
// 語法高亮配色 (基於 VSCode Light+ / GitHub 標準)
// 參考: https://code.visualstudio.com/api/extension-guides/color-theme
// ============================================
const SYNTAX_COLORS = {
  keyword: '0000FF',      // 藍色 - 關鍵字 (function, class, if, return, async, etc.)
  string: 'A31515',       // 深紅色 - 字串
  comment: '008000',      // 綠色 - 註解
  number: '098658',       // 深青色 - 數字
  type: '267F99',         // 青藍色 - 類型/類別名稱
  property: '001080',     // 深藍色 - 屬性/變數
  decorator: 'AF00DB',    // 紫色 - 裝飾器/註解 (@xxx)
  operator: '000000',     // 黑色 - 運算子
  punctuation: '000000',  // 黑色 - 標點符號
  default: '000000'       // 黑色 - 預設
};

/**
 * 簡化版語法高亮解析器
 * 支援多種程式語言的基本語法高亮
 * @param {string} line - 程式碼行
 * @param {string} lang - 程式語言 (javascript, python, swift, kotlin, typescript, etc.)
 * @returns {Array} TextRun 陣列
 */
function tokenizeLine(line, lang, fontSize) {
  const tokens = [];

  // 各語言的關鍵字定義
  const keywords = {
    javascript: /\b(function|const|let|var|if|else|for|while|return|class|extends|new|this|async|await|import|export|from|default|try|catch|throw|typeof|instanceof|null|undefined|true|false)\b/g,
    typescript: /\b(function|const|let|var|if|else|for|while|return|class|extends|new|this|async|await|import|export|from|default|try|catch|throw|typeof|instanceof|null|undefined|true|false|interface|type|enum|implements|public|private|protected|readonly|abstract|static)\b/g,
    python: /\b(def|class|if|elif|else|for|while|return|import|from|as|try|except|raise|with|lambda|yield|async|await|None|True|False|and|or|not|in|is|pass|break|continue|global|nonlocal|self)\b/g,
    swift: /\b(func|class|struct|enum|protocol|extension|var|let|if|else|guard|for|while|return|import|self|Self|nil|true|false|async|await|throws|try|catch|throw|public|private|internal|fileprivate|open|static|override|init|deinit|mutating|some|any)\b/g,
    kotlin: /\b(fun|class|object|interface|val|var|if|else|when|for|while|return|import|this|null|true|false|suspend|async|await|try|catch|throw|public|private|protected|internal|override|open|abstract|sealed|data|companion|init|lateinit|by|lazy)\b/g
  };

  // 通用 regex 模式
  const patterns = [
    { regex: /(\/\/.*$|#.*$)/gm, type: 'comment' },           // 單行註解
    { regex: /(\/\*[\s\S]*?\*\/)/g, type: 'comment' },        // 多行註解
    { regex: /("""[\s\S]*?"""|'''[\s\S]*?''')/g, type: 'string' },  // Python 多行字串
    { regex: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g, type: 'string' },  // 字串
    { regex: /(@\w+)/g, type: 'decorator' },                  // 裝飾器
    { regex: /\b(\d+\.?\d*)\b/g, type: 'number' },            // 數字
    { regex: /\b([A-Z][a-zA-Z0-9_]*)\b/g, type: 'type' },     // 類型名稱 (首字母大寫)
  ];

  // 簡化處理：逐字元分析
  let result = [];
  let remaining = line;
  let lastIndex = 0;

  // 取得該語言的關鍵字 regex
  const keywordRegex = keywords[lang] || keywords.javascript;

  // Token 收集
  const allMatches = [];

  // 收集所有匹配
  patterns.forEach(({ regex, type }) => {
    regex.lastIndex = 0;
    let match;
    while ((match = regex.exec(line)) !== null) {
      allMatches.push({ start: match.index, end: match.index + match[0].length, text: match[0], type });
    }
  });

  // 關鍵字匹配
  keywordRegex.lastIndex = 0;
  let match;
  while ((match = keywordRegex.exec(line)) !== null) {
    allMatches.push({ start: match.index, end: match.index + match[0].length, text: match[0], type: 'keyword' });
  }

  // 按位置排序
  allMatches.sort((a, b) => a.start - b.start);

  // 移除重疊的匹配 (優先保留較早開始或較長的)
  const filteredMatches = [];
  let lastEnd = 0;
  for (const m of allMatches) {
    if (m.start >= lastEnd) {
      filteredMatches.push(m);
      lastEnd = m.end;
    }
  }

  // 建立 TextRun
  let pos = 0;
  for (const m of filteredMatches) {
    // 加入匹配前的普通文字
    if (m.start > pos) {
      const text = line.substring(pos, m.start).replace(/^ +/, match => '\u00A0'.repeat(match.length));
      if (text) {
        result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
      }
    }
    // 加入匹配的 token
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

  // 加入剩餘的普通文字
  if (pos < line.length) {
    const text = line.substring(pos).replace(/^ +/, match => '\u00A0'.repeat(match.length));
    if (text) {
      result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
    }
  }

  // 如果沒有任何 token，返回整行
  if (result.length === 0) {
    const text = line.replace(/^ +/, match => '\u00A0'.repeat(match.length)) || '\u00A0';
    result.push(new TextRun({ text, font: FONT_CODE, size: fontSize, color: SYNTAX_COLORS.default }));
  }

  return result;
}

/**
 * 建立程式碼區塊
 * 參考: https://bo-sgoldhouse.blogspot.com/2021/07/word-editormd.html
 * - 使用 Consolas 等寬字體 (較易閱讀程式碼)
 * - 固定行高 (緊湊顯示)
 * - 行號 + 斑馬條紋背景 (奇偶行不同色)
 * - 語法高亮 (基於 VSCode Light+ 配色)
 */
function createCodeBlock(content, lang = '') {
  const CODE_FONT_SIZE = 20;  // 10pt - 程式碼字型大小
  const LINE_NUMBER_SIZE = 18;  // 9pt - 行號字型大小
  const CODE_LINE_HEIGHT = 280;  // 固定行高 14pt

  // 斑馬條紋背景色
  const BG_ODD = 'FFFFFF';   // 奇數行：白色
  const BG_EVEN = 'F5F5F5';  // 偶數行：淺灰色
  const LINE_NUM_COLOR = '999999';  // 行號顏色：灰色

  const lines = content.split('\n');

  // 建立每行的表格列 (行號 | 程式碼)
  const codeRows = lines.map((line, index) => {
    const lineNum = index + 1;
    const isEven = lineNum % 2 === 0;
    const bgColor = isEven ? BG_EVEN : BG_ODD;

    // 語法高亮解析
    const tokenizedRuns = tokenizeLine(line, lang, CODE_FONT_SIZE);

    return new TableRow({
      children: [
        // 行號欄位
        new TableCell({
          width: { size: 600, type: WidthType.DXA },  // 固定寬度約 0.4 吋
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.CENTER,
          margins: {
            top: 20, bottom: 20,
            left: 80, right: 80
          },
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            spacing: { after: 0, line: CODE_LINE_HEIGHT, lineRule: 'exact' },
            children: [new TextRun({
              text: String(lineNum) + '.',
              font: FONT_CODE,
              size: LINE_NUMBER_SIZE,
              color: LINE_NUM_COLOR
            })]
          })]
        }),
        // 程式碼欄位 (含語法高亮)
        new TableCell({
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.CENTER,
          margins: {
            top: 20, bottom: 20,
            left: 120, right: 80
          },
          children: [new Paragraph({
            spacing: { after: 0, line: CODE_LINE_HEIGHT, lineRule: 'exact' },
            children: tokenizedRuns
          })]
        })
      ]
    });
  });

  // 建立程式碼表格
  const codeTable = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
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
 * 計算表格欄寬 - 根據內容長度智慧分配
 * 針對 SDD 文件優化，確保表格在 A4 頁面中適當顯示
 * @param {string[]} headers - 表格標題
 * @param {string[][]} rows - 表格資料列
 * @param {number} totalWidth - 總表格寬度 (DXA 單位)
 * @param {boolean[]} noWrapColumns - 各欄是否為不換行欄位（ID 欄位）
 */
function calculateColumnWidths(headers, rows, totalWidth = 9360, noWrapColumns = []) {
  const numCols = headers.length;

  // 計算每欄最大內容長度 (考慮中文字元佔用較多空間)
  const maxLengths = headers.map((h, i) => {
    let max = getTextDisplayLength(h);
    rows.forEach(row => {
      if (row[i]) {
        // 移除粗體標記後計算長度
        const cleanText = row[i].replace(/\*\*/g, '');
        max = Math.max(max, getTextDisplayLength(cleanText));
      }
    });
    return max;
  });

  const totalLength = maxLengths.reduce((a, b) => a + b, 0);

  // 根據欄數設定不同的最小/最大寬度策略
  let minWidth, maxWidth;
  if (numCols <= 2) {
    minWidth = 2000;  // 2 欄表格：較寬的欄位
    maxWidth = 7000;
  } else if (numCols <= 4) {
    minWidth = 1500;  // 3-4 欄表格：適中
    maxWidth = 5000;
  } else {
    minWidth = 1000;  // 5+ 欄表格：較窄的欄位
    maxWidth = 3500;
  }

  // ID 欄位需要更大的最小寬度（SDD-TRAIN-008 約需 1800 DXA）
  const idMinWidth = 1800;

  // 根據內容長度比例分配寬度
  let widths = maxLengths.map((len, i) => {
    const ratio = totalLength > 0 ? len / totalLength : 1 / numCols;
    let width = Math.floor(ratio * totalWidth);
    // ID 欄位使用更大的最小寬度
    const colMinWidth = (noWrapColumns[i]) ? idMinWidth : minWidth;
    return Math.max(colMinWidth, Math.min(maxWidth, width));
  });

  // 調整總寬度以符合頁面寬度
  let currentTotal = widths.reduce((a, b) => a + b, 0);

  if (currentTotal > totalWidth) {
    // 超過總寬度時，先保護 ID 欄位，縮減其他欄位
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

  // 最後調整差異
  currentTotal = widths.reduce((a, b) => a + b, 0);
  if (currentTotal !== totalWidth) {
    const diff = totalWidth - currentTotal;
    // 將差異分配給最寬的非 ID 欄位
    const nonIdWidths = widths.map((w, i) => noWrapColumns[i] ? 0 : w);
    const maxNonIdIndex = nonIdWidths.indexOf(Math.max(...nonIdWidths));
    if (maxNonIdIndex >= 0) {
      widths[maxNonIdIndex] += diff;
    } else {
      // 全都是 ID 欄位時，調整最後一欄
      widths[widths.length - 1] += diff;
    }
  }

  return widths;
}

/**
 * 計算文字顯示長度 (中文字算 2 個單位)
 */
function getTextDisplayLength(text) {
  let length = 0;
  for (const char of text) {
    if (/[\u4e00-\u9fff]/.test(char)) {
      length += 2;  // 中文字
    } else {
      length += 1;  // 英文/數字/符號
    }
  }
  return length;
}

/**
 * 檢測是否為 ID 欄位（不應換行）
 * ID 格式：SRS-XXX-NNN, SDD-XXX-NNN, REQ-XXX-NNN, SCR-XXX-NNN 等
 */
function isIdColumn(headerText, cellText) {
  // 檢查標題是否為 ID 相關（忽略大小寫和空格）
  const headerNormalized = headerText.toLowerCase().replace(/\s+/g, '');
  const idHeaders = ['id', '設計id', '需求id', '編號', 'identifier', 'designid', 'requirementid'];
  if (idHeaders.some(h => headerNormalized.includes(h))) {
    return true;
  }
  // 檢查內容是否符合 ID 格式（移除 ** 粗體標記後檢查）
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

  // 判斷哪些欄位是 ID 欄位（不應換行）
  const noWrapColumns = headers.map((header, i) => {
    // 檢查標題或第一列資料是否為 ID
    const firstRowCell = rows.length > 0 ? rows[0][i] : '';
    return isIdColumn(header, firstRowCell);
  });

  // 計算欄寬時考慮 ID 欄位需要更大的最小寬度
  const columnWidths = calculateColumnWidths(headers, rows, 9360, noWrapColumns);

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
          keepLines: noWrapColumns[i],  // ID 欄位不換行
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
          keepLines: noWrapColumns[i],  // ID 欄位不換行
          children: parseInlineFormatting(cell, FONT_SIZE.TABLE)
        })]
      }))
    }))
  ];

  return new Table({ columnWidths: columnWidths, rows: tableRows });
}

/**
 * 解析文件結構，分離封面、目錄、修訂歷史與主要內容
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

    // 檢測封面資訊（文件開頭到 Table of Contents 之前）
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

    // 檢測目錄區塊
    if (section === 'toc') {
      if (trimmed.startsWith('## Revision History') || trimmed.toLowerCase().includes('revision history') || trimmed === '## 修訂歷史') {
        section = 'revision';
        i++;
        continue;
      } else if (trimmed.startsWith('## 1') || trimmed.startsWith('## 1.') || trimmed === '---') {
        // 跳過目錄，進入主要內容 (如果遇到分隔線 --- 也可能表示目錄結束)
        if (trimmed === '---') {
          i++;
          continue;
        }
        section = 'main';
        continue;  // 不 i++，讓 main section 處理這行
      }
      structure.tocLines.push(line);
      i++;
      continue;
    }

    // 檢測修訂歷史
    if (section === 'revision') {
      if (trimmed.startsWith('## 1') || trimmed === '---' || (trimmed.startsWith('## ') && !trimmed.toLowerCase().includes('revision') && !trimmed.includes('修訂'))) {
        if (trimmed === '---') {
          i++;
          continue;
        }
        section = 'main';
        continue;  // 不 i++，讓 main section 處理這行
      }
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        structure.revisionHistory.push(line);
      }
      i++;
      continue;
    }

    // 主要內容
    if (section === 'main') {
      structure.mainContent.push(line);
    }
    i++;
  }

  return structure;
}

/**
 * 建立封面頁元素
 */
function createCoverPage(coverInfo) {
  const elements = [];

  // 空白間距
  for (let i = 0; i < 6; i++) {
    elements.push(new Paragraph({ children: [] }));
  }

  // 主標題
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

  // 副標題
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

  // 空白間距
  for (let i = 0; i < 4; i++) {
    elements.push(new Paragraph({ children: [] }));
  }

  // 版本
  if (coverInfo.version) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: `Version ${coverInfo.version}`, size: 28, font: FONT_EN })]
    }));
  }

  // 作者
  if (coverInfo.author) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: `Prepared by ${coverInfo.author}`, size: 28, font: FONT_EN })]
    }));
  }

  // 組織
  if (coverInfo.organization) {
    elements.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: coverInfo.organization, size: 28, font: FONT_EN })]
    }));
  }

  // 日期
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
 * 建立目錄頁元素
 * 使用 Word 原生 TOC 功能，開啟文件後需按 F9 或右鍵「更新欄位」以顯示頁碼
 */
function createTocPage() {
  const elements = [];

  // 目錄標題
  elements.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 300 },
    children: [new TextRun({ text: 'Table of Contents', bold: true, size: FONT_SIZE.H1, font: FONT_EN })]
  }));

  // 使用 Word 原生目錄功能（包含頁碼）
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

  // 提示訊息
  elements.push(new Paragraph({
    spacing: { before: 400 },
    children: [new TextRun({
      text: '※ 請在 Word 中按 F9 或右鍵選擇「更新欄位」以顯示目錄內容與頁碼',
      italics: true,
      size: FONT_SIZE.SMALL,
      color: '888888',
      font: FONT_CN
    })]
  }));

  return elements;
}

/**
 * 建立修訂歷史頁
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

  // 解析文件結構
  const structure = parseDocumentStructure(content, outputDir);

  // 解析主要內容
  const mainContentText = structure.mainContent.join('\n');
  const mainElements = parseMarkdown(mainContentText, outputDir).flat();

  // 頁面邊距設定
  const pageMargins = { top: 1440, right: 1440, bottom: 1440, left: 1440 };

  // 建立頁首頁尾
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
    features: { updateFields: true },  // 自動更新目錄
    // 標題自動編號設定
    // IEC 62304 文件結構：## → 1., ### → 1.1, #### → 1.1.1, ##### → 1.1.1.1
    numbering: {
      config: [
        {
          reference: 'heading-numbering',
          levels: [
            {
              level: 0,  // ## 主章節 → 1., 2., 3.
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
              level: 1,  // ### 子章節 → 1.1, 1.2
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
              level: 2,  // #### → 1.1.1
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
              level: 3,  // ##### → 1.1.1.1
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
              ascii: FONT_EN,       // 英文字使用 Arial
              eastAsia: FONT_CN,    // 中文字使用圓黑體
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
          paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 4 } }
      ]
    },
    sections: [
      // Section 1: 封面頁 (無頁首頁尾)
      {
        properties: { page: { margin: pageMargins } },
        children: createCoverPage(structure.coverInfo)
      },
      // Section 2: 目錄頁
      {
        properties: { page: { margin: pageMargins } },
        headers: { default: defaultHeader },
        footers: { default: defaultFooter },
        children: createTocPage()
      },
      // Section 3: 修訂歷史頁
      {
        properties: { page: { margin: pageMargins } },
        headers: { default: defaultHeader },
        footers: { default: defaultFooter },
        children: createRevisionHistoryPage(structure.revisionHistory)
      },
      // Section 4: 主要內容
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

  // 清理 Mermaid 暫存檔案
  // cleanupMermaidTemp(outputDir);  // DEBUG
}

// ============================================
// 命令列介面
// ============================================

// 使用方式: node md-to-docx.js <input.md> [output.docx]
// 範例: node md-to-docx.js SRS-SomniLand-1.0.md
// 範例: node md-to-docx.js SDD-Project.md SDD-Project-v1.docx

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
