#!/usr/bin/env node
/**
 * MD TitleNumberingRemoveTool
 *
 * Remove manual numbering from Markdown headings (e.g., "1. Introduction" → "Introduction")
 * Works with md-to-docx.js auto-numbering feature
 *
 * Usage:
 *   node remove-heading-numbers.js <input.md> [output.md]
 *
 * Example:
 *   node remove-heading-numbers.js SRS-SomniLand-1.0.md
 *   node remove-heading-numbers.js SDD-SomniLand-1.0.md SDD-SomniLand-1.0-nonum.md
 *
 * Supported numbering formats:
 *   - "1. Title" → "Title"
 *   - "1.1 Title" → "Title"
 *   - "1.1.1 Title" → "Title"
 *   - "1.1.1.1 Title" → "Title"
 *   - "1.1.1.1.1 Title" → "Title"
 *
 * Preserved headings (unchanged):
 *   - Special headings (Table of Contents, Revision History, Directory)
 *   - Requirement ID headings (e.g., REQ-FUNC-001)
 *   - Cover titles (e.g., Software Requirements Specification)
 */

const fs = require('fs');
const path = require('path');

/**
 * Check if heading should preserve numbering
 * @param {string} headingText - Heading text (without # prefix)
 * @returns {boolean} - true means preserve original, false means remove numbering
 */
function shouldPreserveHeading(headingText) {
  const preservePatterns = [
    /^Table of Contents$/i,
    /^Revision History$/i,
    /^Directory$/,
    /^Revision History$/,
    /^Software /i,                    // Cover title
    /^For /i,                         // Cover subtitle
    /^(SRS|SDD|SWD|STC|REQ)-[A-Z]+-\d+/, // Requirement ID heading
    /^\*\*/                           // Bold headings (usually special format)
  ];

  return preservePatterns.some(pattern => pattern.test(headingText.trim()));
}

/**
 * Remove numbering from heading
 * @param {string} line - Complete Markdown line
 * @returns {string} - Processed line
 */
function removeHeadingNumber(line) {
  // Match Markdown heading format: #{1,6} + space + numbering + title
  const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);

  if (!headingMatch) {
    return line; // Not a heading line, keep original
  }

  const [, hashes, content] = headingMatch;

  // Check if should preserve
  if (shouldPreserveHeading(content)) {
    return line;
  }

  // Try to remove numbering formats:
  // Format 1: "1. Title" → "Title" (with period)
  // Format 2: "1.1 Title" → "Title" (no period, space separated)
  // Format 3: "1.1.1 Title" → "Title"
  // Format 4: "1.1.1.1 Title" → "Title"
  // Format 5: "1.1.1.1.1 Title" → "Title"

  // Regex explanation:
  // ^(\d+\.)+ - Match "1." or "1.1." or "1.1.1." etc (with period)
  // ^\d+(\.\d+)* - Match "1" or "1.1" or "1.1.1" etc (may not have period)
  // \s+ - Space after numbering
  // (.+)$ - Actual heading text

  let newContent = content;

  // Try to match various numbering formats:
  // Format 1: "1. Title" (single level, with period)
  // Format 2: "1.1 Title" (multi-level, no period)
  // Format 3: "1.1.1 Title" (three levels)
  // Format 4: "1.1.1.1 Title" (four levels)

  // Unified regex: Match "digits" followed by "." or ".digits", may end with ".", then space, then title
  // Examples: 1. / 1.1 / 1.1. / 1.1.1 / 1.1.1. / etc
  const numberingPattern = /^(\d+(?:\.\d+)*\.?)\s+(.+)$/;
  const match = content.match(numberingPattern);

  if (match) {
    newContent = match[2];
  }

  return `${hashes} ${newContent}`;
}

/**
 * Process a Markdown file
 * @param {string} inputPath - Input file path
 * @param {string} outputPath - Output file path
 */
function processMarkdownFile(inputPath, outputPath) {
  // Read file
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

  // Write file
  const output = processedLines.join('\n');
  fs.writeFileSync(outputPath, output, 'utf-8');

  console.log(`\nProcess complete!`);
  console.log(`- Input: ${inputPath}`);
  console.log(`- Output: ${outputPath}`);
  console.log(`- Modified headings: ${changedCount}`);
}

/**
 * Update table of contents links (TOC)
 * When headings have numbering removed, TOC anchor links also need to be updated
 * @param {string} content - Markdown content
 * @returns {string} - Updated content
 */
function updateTocLinks(content) {
  // TOC link format: [1. Introduction](#1-introduction) → [Introduction](#introduction)
  // This function can be expanded in the future, currently md-to-docx.js auto-generates TOC
  return content;
}

// ============================================
// Command Line Interface
// ============================================

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('MD Heading Numbering Removal Tool');
  console.log('');
  console.log('Usage: node remove-heading-numbers.js <input.md> [output.md]');
  console.log('');
  console.log('Description:');
  console.log('  Remove manual numbering from Markdown headings, works with md-to-docx.js auto-numbering.');
  console.log('');
  console.log('Example:');
  console.log('  node remove-heading-numbers.js SRS-SomniLand-1.0.md');
  console.log('  node remove-heading-numbers.js SDD-SomniLand-1.0.md SDD-nonum.md');
  console.log('');
  console.log('Supported numbering formats:');
  console.log('  - "## 1. Introduction" → "## Introduction"');
  console.log('  - "### 1.1 Purpose" → "### Purpose"');
  console.log('  - "#### 1.1.1 Overview" → "#### Overview"');
  console.log('');
  console.log('Preserved headings (unchanged):');
  console.log('  - Special headings (Table of Contents, Revision History, etc.)');
  console.log('  - Requirement ID headings (REQ-FUNC-001, etc.)');
  console.log('  - Cover titles (Software Requirements Specification, etc.)');
  process.exit(0);
}

const inputPath = args[0];

if (!fs.existsSync(inputPath)) {
  console.error(`Error: Cannot find file "${inputPath}"`);
  process.exit(1);
}

// Output path: If not specified, overwrite original file
const outputPath = args[1] || inputPath;

console.log(`Processing: ${inputPath}`);
console.log('');

processMarkdownFile(inputPath, outputPath);
