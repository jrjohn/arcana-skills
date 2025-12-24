/**
 * Screenshot Embedding Script for SDD
 *
 * 自動將 generated-ui/screenshots 中的截圖嵌入 SDD.md 文件
 *
 * Usage:
 *   node embed-screenshots-to-sdd.js <sdd-path> <screenshots-path> [--copy-to <images-dir>]
 *
 * Example:
 *   node embed-screenshots-to-sdd.js ./docs/SDD.md ./generated-ui/screenshots --copy-to ./docs/images
 */

const fs = require('fs');
const path = require('path');

/**
 * 掃描截圖目錄
 */
function scanScreenshots(screenshotsPath) {
  const screenshots = [];

  function scanDir(dirPath, module = '') {
    if (!fs.existsSync(dirPath)) return;

    const items = fs.readdirSync(dirPath);
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        scanDir(fullPath, item.toUpperCase());
      } else if (item.endsWith('.png') || item.endsWith('.svg')) {
        const screenId = extractScreenId(item);
        if (screenId) {
          screenshots.push({
            id: screenId,
            module: module,
            filename: item,
            path: fullPath,
            format: item.endsWith('.svg') ? 'svg' : 'png'
          });
        }
      }
    }
  }

  scanDir(screenshotsPath);
  return screenshots;
}

/**
 * 從檔名提取 Screen ID
 */
function extractScreenId(filename) {
  // 支援格式: SCR-AUTH-001-login.png 或 AUTH-001-login.png
  const match = filename.match(/^(SCR-)?([A-Z]+)-(\d{3})/);
  if (match) {
    return `SCR-${match[2]}-${match[3]}`;
  }
  return null;
}

/**
 * 讀取 SDD 並解析畫面章節
 */
function parseSDD(sddPath) {
  const content = fs.readFileSync(sddPath, 'utf8');

  // 找出所有 SCR-* 的章節
  const screenSections = [];
  const regex = /^(#{2,4})\s+(SCR-[A-Z]+-\d{3})[^\n]*$/gm;
  let match;

  while ((match = regex.exec(content)) !== null) {
    screenSections.push({
      level: match[1].length,
      id: match[2],
      position: match.index,
      fullMatch: match[0]
    });
  }

  return { content, screenSections };
}

/**
 * 產生截圖 Markdown
 */
function generateScreenshotMarkdown(screenshot, relativePath) {
  const altText = `${screenshot.id} 畫面截圖`;

  if (screenshot.format === 'svg') {
    // SVG 使用 img 標籤以控制大小
    return `<img src="${relativePath}" alt="${altText}" width="300"/>`;
  } else {
    // PNG 使用標準 Markdown
    return `![${altText}](${relativePath})`;
  }
}

/**
 * 更新 SDD 內容
 */
function updateSDD(sddContent, screenSections, screenshots, imagesDir) {
  let updatedContent = sddContent;
  let offset = 0;

  // 建立截圖對照表
  const screenshotMap = new Map();
  for (const screenshot of screenshots) {
    screenshotMap.set(screenshot.id, screenshot);
  }

  // 處理每個畫面章節
  for (const section of screenSections) {
    const screenshot = screenshotMap.get(section.id);
    if (!screenshot) continue;

    // 計算相對路徑
    const relativePath = path.join(imagesDir, screenshot.filename).replace(/\\/g, '/');

    // 檢查是否已有截圖
    const sectionEnd = findSectionEnd(updatedContent, section.position + offset);
    const sectionContent = updatedContent.substring(section.position + offset, sectionEnd);

    if (sectionContent.includes(screenshot.filename) || sectionContent.includes(section.id + '.png') || sectionContent.includes(section.id + '.svg')) {
      // 已有截圖，跳過
      continue;
    }

    // 在標題後插入截圖
    const insertPosition = section.position + offset + section.fullMatch.length;
    const screenshotMd = `\n\n${generateScreenshotMarkdown(screenshot, relativePath)}\n`;

    updatedContent =
      updatedContent.substring(0, insertPosition) +
      screenshotMd +
      updatedContent.substring(insertPosition);

    offset += screenshotMd.length;
  }

  return updatedContent;
}

/**
 * 找出章節結束位置
 */
function findSectionEnd(content, startPosition) {
  // 找下一個同級或更高級標題
  const afterStart = content.substring(startPosition);
  const nextHeadingMatch = afterStart.match(/\n#{2,4}\s+/);

  if (nextHeadingMatch) {
    return startPosition + nextHeadingMatch.index;
  }

  return content.length;
}

/**
 * 複製截圖到目標目錄
 */
function copyScreenshots(screenshots, targetDir) {
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  const copied = [];
  for (const screenshot of screenshots) {
    const targetPath = path.join(targetDir, screenshot.filename);

    // 優先 SVG
    if (screenshot.format === 'svg') {
      fs.copyFileSync(screenshot.path, targetPath);
      copied.push(screenshot.filename);

      // 如果有同名 PNG，檢查是否需要刪除
      const pngPath = targetPath.replace('.svg', '.png');
      if (fs.existsSync(pngPath)) {
        fs.unlinkSync(pngPath);
        console.log(`  Removed: ${path.basename(pngPath)} (SVG preferred)`);
      }
    } else if (screenshot.format === 'png') {
      // 檢查是否已有 SVG
      const svgPath = targetPath.replace('.png', '.svg');
      if (!fs.existsSync(svgPath)) {
        fs.copyFileSync(screenshot.path, targetPath);
        copied.push(screenshot.filename);
      }
    }
  }

  return copied;
}

/**
 * 產生報告
 */
function generateReport(screenshots, screenSections, updatedScreens) {
  const lines = [];
  lines.push('# 截圖嵌入報告');
  lines.push('');
  lines.push(`執行時間: ${new Date().toISOString()}`);
  lines.push('');
  lines.push('## 統計');
  lines.push('');
  lines.push(`| 項目 | 數量 |`);
  lines.push(`|------|------|`);
  lines.push(`| 截圖總數 | ${screenshots.length} |`);
  lines.push(`| SDD 畫面章節 | ${screenSections.length} |`);
  lines.push(`| 已嵌入截圖 | ${updatedScreens} |`);
  lines.push('');

  // 檢查缺少截圖的章節
  const screenshotIds = new Set(screenshots.map(s => s.id));
  const missingSections = screenSections.filter(s => !screenshotIds.has(s.id));

  if (missingSections.length > 0) {
    lines.push('## 缺少截圖的章節');
    lines.push('');
    lines.push('| 章節 ID | 建議動作 |');
    lines.push('|---------|----------|');
    for (const section of missingSections) {
      lines.push(`| ${section.id} | 補充截圖 |`);
    }
  }

  // 檢查多餘的截圖
  const sectionIds = new Set(screenSections.map(s => s.id));
  const extraScreenshots = screenshots.filter(s => !sectionIds.has(s.id));

  if (extraScreenshots.length > 0) {
    lines.push('');
    lines.push('## 未對應的截圖');
    lines.push('');
    lines.push('| 截圖 | 建議動作 |');
    lines.push('|------|----------|');
    for (const screenshot of extraScreenshots) {
      lines.push(`| ${screenshot.filename} | 新增 SDD 章節或移除 |`);
    }
  }

  return lines.join('\n');
}

/**
 * 主程式
 */
function main() {
  const args = process.argv.slice(2);

  // 解析參數
  let sddPath = null;
  let screenshotsPath = null;
  let copyTo = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--copy-to' && args[i + 1]) {
      copyTo = args[++i];
    } else if (!sddPath) {
      sddPath = args[i];
    } else if (!screenshotsPath) {
      screenshotsPath = args[i];
    }
  }

  if (!sddPath || !screenshotsPath) {
    console.log('Usage: node embed-screenshots-to-sdd.js <sdd-path> <screenshots-path> [--copy-to <images-dir>]');
    console.log('');
    console.log('Example:');
    console.log('  node embed-screenshots-to-sdd.js ./docs/SDD.md ./generated-ui/screenshots --copy-to ./docs/images');
    process.exit(1);
  }

  // 預設 images 目錄
  if (!copyTo) {
    copyTo = path.join(path.dirname(sddPath), 'images');
  }

  console.log(`SDD Path: ${sddPath}`);
  console.log(`Screenshots Path: ${screenshotsPath}`);
  console.log(`Images Dir: ${copyTo}`);
  console.log('');

  // 掃描截圖
  console.log('Scanning screenshots...');
  const screenshots = scanScreenshots(screenshotsPath);
  console.log(`Found ${screenshots.length} screenshots`);

  // 複製截圖
  if (screenshots.length > 0) {
    console.log(`Copying screenshots to ${copyTo}...`);
    const copied = copyScreenshots(screenshots, copyTo);
    console.log(`Copied ${copied.length} files`);
  }

  // 解析 SDD
  console.log('Parsing SDD...');
  const { content, screenSections } = parseSDD(sddPath);
  console.log(`Found ${screenSections.length} screen sections`);

  // 計算相對路徑
  const sddDir = path.dirname(sddPath);
  const imagesRelative = path.relative(sddDir, copyTo);

  // 更新 SDD
  console.log('Updating SDD...');
  const originalLength = content.length;
  const updatedContent = updateSDD(content, screenSections, screenshots, imagesRelative);
  const addedChars = updatedContent.length - originalLength;

  // 計算更新的章節數
  const updatedScreens = Math.floor(addedChars / 50); // 估算

  // 寫入更新的 SDD
  fs.writeFileSync(sddPath, updatedContent);
  console.log(`Updated: ${sddPath}`);

  // 產生報告
  const report = generateReport(screenshots, screenSections, updatedScreens);
  const reportPath = sddPath.replace('.md', '-screenshot-report.md');
  fs.writeFileSync(reportPath, report);
  console.log(`Report: ${reportPath}`);

  console.log('');
  console.log('Done!');
}

main();
