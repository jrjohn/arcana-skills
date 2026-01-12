#!/usr/bin/env node
/**
 * MD 標題編號移除工具
 *
 * 移除 Markdown 標題中的手動編號（如 "1. Introduction" → "Introduction"）
 * 配合 md-to-docx.js 的自動編號功能使用
 *
 * 使用方式：
 *   node remove-heading-numbers.js <input.md> [output.md]
 *
 * 範例：
 *   node remove-heading-numbers.js SRS-SomniLand-1.0.md
 *   node remove-heading-numbers.js SDD-SomniLand-1.0.md SDD-SomniLand-1.0-nonum.md
 *
 * 支援的編號格式：
 *   - "1. Title" → "Title"
 *   - "1.1 Title" → "Title"
 *   - "1.1.1 Title" → "Title"
 *   - "1.1.1.1 Title" → "Title"
 *   - "1.1.1.1.1 Title" → "Title"
 *
 * 保留不變的標題：
 *   - 特殊標題（Table of Contents, Revision History, 目錄, 修訂歷史）
 *   - 需求 ID 標題（如 REQ-FUNC-001）
 *   - 封面標題（Software Requirements Specification 等）
 */

const fs = require('fs');
const path = require('path');

/**
 * 檢查標題是否應該保留編號
 * @param {string} headingText - 標題文字（不含 # 前綴）
 * @returns {boolean} - true 表示保留原樣，false 表示移除編號
 */
function shouldPreserveHeading(headingText) {
  const preservePatterns = [
    /^Table of Contents$/i,
    /^Revision History$/i,
    /^目錄$/,
    /^修訂歷史$/,
    /^Software /i,                    // 封面標題
    /^For /i,                         // 封面副標題
    /^(SRS|SDD|SWD|STC|REQ)-[A-Z]+-\d+/, // 需求 ID 標題
    /^\*\*/                           // 粗體標題（通常是特殊格式）
  ];

  return preservePatterns.some(pattern => pattern.test(headingText.trim()));
}

/**
 * 移除標題中的編號
 * @param {string} line - 完整的 Markdown 行
 * @returns {string} - 處理後的行
 */
function removeHeadingNumber(line) {
  // 匹配 Markdown 標題格式：#{1,6} + 空格 + 編號 + 標題
  const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);

  if (!headingMatch) {
    return line; // 非標題行，保持原樣
  }

  const [, hashes, content] = headingMatch;

  // 檢查是否應該保留
  if (shouldPreserveHeading(content)) {
    return line;
  }

  // 嘗試移除編號格式：
  // 格式 1: "1. Title" → "Title" (有尾點)
  // 格式 2: "1.1 Title" → "Title" (無尾點，空格分隔)
  // 格式 3: "1.1.1 Title" → "Title"
  // 格式 4: "1.1.1.1 Title" → "Title"
  // 格式 5: "1.1.1.1.1 Title" → "Title"

  // 正則說明：
  // ^(\d+\.)+ - 匹配 "1." 或 "1.1." 或 "1.1.1." 等（有尾點）
  // ^\d+(\.\d+)* - 匹配 "1" 或 "1.1" 或 "1.1.1" 等（可能無尾點）
  // \s+ - 編號後的空格
  // (.+)$ - 實際標題文字

  let newContent = content;

  // 嘗試匹配各種編號格式：
  // 格式 1: "1. Title" (單級編號，有尾點)
  // 格式 2: "1.1 Title" (多級編號，無尾點)
  // 格式 3: "1.1.1 Title" (三級編號)
  // 格式 4: "1.1.1.1 Title" (四級編號)

  // 統一正則：匹配 "數字" 後跟 "." 或 ".數字"，最後可選 "."，然後空格，然後標題
  // 例如：1. / 1.1 / 1.1. / 1.1.1 / 1.1.1. / 等等
  const numberingPattern = /^(\d+(?:\.\d+)*\.?)\s+(.+)$/;
  const match = content.match(numberingPattern);

  if (match) {
    newContent = match[2];
  }

  return `${hashes} ${newContent}`;
}

/**
 * 處理整個 Markdown 檔案
 * @param {string} inputPath - 輸入檔案路徑
 * @param {string} outputPath - 輸出檔案路徑
 */
function processMarkdownFile(inputPath, outputPath) {
  // 讀取檔案
  const content = fs.readFileSync(inputPath, 'utf-8');
  const lines = content.split('\n');

  let changedCount = 0;
  const processedLines = lines.map((line, index) => {
    const newLine = removeHeadingNumber(line);
    if (newLine !== line) {
      changedCount++;
      console.log(`Line ${index + 1}: "${line.trim()}" → "${newLine.trim()}"`);
    }
    return newLine;
  });

  // 寫入檔案
  const output = processedLines.join('\n');
  fs.writeFileSync(outputPath, output, 'utf-8');

  console.log(`\n處理完成！`);
  console.log(`- 輸入: ${inputPath}`);
  console.log(`- 輸出: ${outputPath}`);
  console.log(`- 修改標題數: ${changedCount}`);
}

/**
 * 更新目錄連結（TOC）
 * 當標題移除編號後，目錄中的錨點連結也需要更新
 * @param {string} content - Markdown 內容
 * @returns {string} - 更新後的內容
 */
function updateTocLinks(content) {
  // 目錄連結格式：[1. Introduction](#1-introduction) → [Introduction](#introduction)
  // 這個函數可以在未來擴展，目前 md-to-docx.js 會自動生成目錄
  return content;
}

// ============================================
// 命令列介面
// ============================================

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('MD 標題編號移除工具');
  console.log('');
  console.log('使用方式: node remove-heading-numbers.js <input.md> [output.md]');
  console.log('');
  console.log('說明:');
  console.log('  移除 Markdown 標題中的手動編號，配合 md-to-docx.js 的自動編號功能使用。');
  console.log('');
  console.log('範例:');
  console.log('  node remove-heading-numbers.js SRS-SomniLand-1.0.md');
  console.log('  node remove-heading-numbers.js SDD-SomniLand-1.0.md SDD-nonum.md');
  console.log('');
  console.log('支援的編號格式:');
  console.log('  - "## 1. Introduction" → "## Introduction"');
  console.log('  - "### 1.1 Purpose" → "### Purpose"');
  console.log('  - "#### 1.1.1 Overview" → "#### Overview"');
  console.log('');
  console.log('保留不變的標題:');
  console.log('  - 特殊標題 (Table of Contents, Revision History 等)');
  console.log('  - 需求 ID 標題 (REQ-FUNC-001 等)');
  console.log('  - 封面標題 (Software Requirements Specification 等)');
  process.exit(0);
}

const inputPath = args[0];

if (!fs.existsSync(inputPath)) {
  console.error(`錯誤: 找不到檔案 "${inputPath}"`);
  process.exit(1);
}

// 輸出路徑：如果沒指定，則覆蓋原檔案
const outputPath = args[1] || inputPath;

console.log(`正在處理: ${inputPath}`);
console.log('');

processMarkdownFile(inputPath, outputPath);
