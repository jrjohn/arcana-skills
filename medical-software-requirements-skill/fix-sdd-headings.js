#!/usr/bin/env node
/**
 * SDD 標題修復腳本
 *
 * 修復被錯誤移除編號的 SDD 標題，恢復原始章節編號格式
 * 然後再使用 remove-heading-numbers.js 正確移除
 */

const fs = require('fs');

// SDD 的原始標題結構（根據 IEC 62304 SDD 範本）
const SDD_STRUCTURE = {
  // 主標題 (不編號)
  'Software Design Description': { level: 1, number: null },
  'For SomniLand (iNAP Kids App)': { level: 2, number: null },
  'Table of Contents': { level: 2, number: null },
  'Revision History': { level: 2, number: null },

  // 1. Introduction
  'Introduction': { level: 2, number: '1.' },
  'Document Purpose': { level: 3, number: '1.1' },
  'Subject Scope': { level: 3, number: '1.2' },
  'Definitions, Acronyms, and Abbreviations': { level: 3, number: '1.3' },
  'References': { level: 3, number: '1.4' },
  'Document Overview': { level: 3, number: '1.5' },

  // 2. Design Overview
  'Design Overview': { level: 2, number: '2.' },
  'Stakeholder Concerns': { level: 3, number: '2.1' },
  'Design Principles': { level: 3, number: '2.2' },
  'Software Architecture Principles': { level: 4, number: '2.2.1' },
  'Cognitive Psychology Principles': { level: 4, number: '2.2.2' },
  "Norman's Design Principles": { level: 4, number: '2.2.3' },
  'Selected Viewpoints': { level: 3, number: '2.3' },

  // 3. System Architecture
  'System Architecture': { level: 2, number: '3.' },
  'Context View': { level: 3, number: '3.1' },
  'Composition View': { level: 3, number: '3.2' },
  'Account & Profile Architecture': { level: 3, number: '3.2.1' },
  'Technology Stack': { level: 3, number: '3.3' },
  'App Client': { level: 4, number: '3.3.1' },
  'Backend Server': { level: 4, number: '3.3.2' },
  'SomniLand Portal': { level: 4, number: '3.3.3' },

  // 4. Module Design
  'Module Design': { level: 2, number: '4.' },
  'AUTH Module': { level: 3, number: '4.1' },
  'ONBOARD Module': { level: 3, number: '4.2' },
  'DASHBOARD Module': { level: 3, number: '4.3' },
  'DEVICE Module': { level: 3, number: '4.4' },
  'TRAIN Module': { level: 3, number: '4.5' },
  'REPORT Module': { level: 3, number: '4.6' },
  'REWARD Module': { level: 3, number: '4.7' },
  'SETTING Module': { level: 3, number: '4.8' },
  'PLATFORM Module': { level: 3, number: '4.9' },

  // 5. Data Design
  'Data Design': { level: 2, number: '5.' },
  'Data Model Overview': { level: 3, number: '5.1' },
  'Entity Definitions': { level: 3, number: '5.2' },
  'Parent Account': { level: 4, number: '5.2.1' },
  'Child Profile': { level: 4, number: '5.2.2' },
  'Local Database (SwiftData / Room)': { level: 3, number: '5.3' },
  'Cloud Database (MySQL)': { level: 3, number: '5.4' },

  // 6. Interface Design
  'Interface Design': { level: 2, number: '6.' },
  'External Interfaces': { level: 3, number: '6.1' },
  'Internal Interfaces': { level: 3, number: '6.2' },
  'BLE Interface': { level: 3, number: '6.3' },
  'GATT Services': { level: 4, number: '6.3.1' },
  'Therapy Data Characteristics': { level: 4, number: '6.3.2' },
  'REST API': { level: 3, number: '6.4' },
  'Authentication API': { level: 4, number: '6.4.1' },
  'Profile API': { level: 4, number: '6.4.2' },
  'Training API': { level: 4, number: '6.4.3' },
  'Therapy API': { level: 4, number: '6.4.4' },

  // 7. Security Design
  'Security Design': { level: 2, number: '7.' },
  'Authentication & Authorization': { level: 3, number: '7.1' },
  'Data Protection': { level: 3, number: '7.2' },
  'Account Security': { level: 3, number: '7.3' },

  // 8. Non-Functional Requirements Mapping
  'Non-Functional Requirements Mapping': { level: 2, number: '8.' },

  // 9. Requirements Traceability
  'Requirements Traceability': { level: 2, number: '9.' },
  'SRS → SDD Traceability Matrix': { level: 3, number: '9.1' },
  'Traceability Summary': { level: 3, number: '9.2' },
};

// 模組子標題編號對應 (每個模組的子標題)
// 格式: 模組編號.子標題序號
const MODULE_SUBSECTIONS = {
  // 每個模組通用的子標題
  'Design Overview': '.1',
  'Architecture Design': '.2',
  'Onboarding Flow': '.2',
  'Dashboard Architecture': '.2',
  'BLE Connection State Machine': '.2',
  'Training Flow Architecture': '.2',
  'Seal Training Class Design': '.3',
  'Report Data Flow': '.2',
  'Reward System Architecture': '.2',
  'Backend Architecture': '.2',
  'Organization Hierarchy': '.3',
};

// 特殊標題模式 (不修改)
const PRESERVE_PATTERNS = [
  /^Screen Design:/,
  /^SCR-/,
  /^(SRS|SDD|SWD|STC|REQ)-[A-Z]+-\d+/,
];

// 當前模組上下文
let currentModuleNumber = null;
let currentModuleSubIndex = 0;

function fixHeadingLine(line) {
  // 匹配標題格式
  const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
  if (!headingMatch) return line;

  const [, hashes, content] = headingMatch;
  const level = hashes.length;
  const trimmedContent = content.trim();

  // 檢查是否為保留格式
  if (PRESERVE_PATTERNS.some(p => p.test(trimmedContent))) {
    return line;
  }

  // 移除錯誤的數字前綴或原有編號
  // 例如: "1 Document Purpose" → "Document Purpose"
  // 例如: "2. Design Overview" → "Design Overview"
  const cleanContent = trimmedContent.replace(/^(\d+\.?\s+|\d+\.\d+\.?\s+|\d+\.\d+\.\d+\.?\s+)/, '');

  // 查找正確的編號
  const structure = SDD_STRUCTURE[cleanContent];
  if (structure && structure.number) {
    // 更新當前模組上下文
    if (cleanContent.includes('Module') && level === 3) {
      currentModuleNumber = structure.number.replace('.', '');
      currentModuleSubIndex = 0;
    }
    return `${hashes} ${structure.number} ${cleanContent}`;
  }

  // 檢查是否為模組子標題
  const subsection = MODULE_SUBSECTIONS[cleanContent];
  if (subsection && currentModuleNumber && level === 4) {
    currentModuleSubIndex++;
    const number = `${currentModuleNumber}.${currentModuleSubIndex}`;
    return `${hashes} ${number} ${cleanContent}`;
  }

  // 如果沒找到，返回清理後的版本 (保持無編號)
  return `${hashes} ${cleanContent}`;
}

function processFile(inputPath, outputPath) {
  const content = fs.readFileSync(inputPath, 'utf-8');
  const lines = content.split('\n');

  let changedCount = 0;
  const processedLines = lines.map((line, index) => {
    const newLine = fixHeadingLine(line);
    if (newLine !== line) {
      changedCount++;
      console.log(`Line ${index + 1}: "${line.trim()}" → "${newLine.trim()}"`);
    }
    return newLine;
  });

  fs.writeFileSync(outputPath, processedLines.join('\n'), 'utf-8');

  console.log(`\n修復完成！`);
  console.log(`- 輸入: ${inputPath}`);
  console.log(`- 輸出: ${outputPath}`);
  console.log(`- 修改標題數: ${changedCount}`);
}

// 執行
const args = process.argv.slice(2);
if (args.length === 0) {
  console.log('使用方式: node fix-sdd-headings.js <input.md> [output.md]');
  process.exit(0);
}

const inputPath = args[0];
const outputPath = args[1] || inputPath;

if (!fs.existsSync(inputPath)) {
  console.error(`錯誤: 找不到檔案 "${inputPath}"`);
  process.exit(1);
}

processFile(inputPath, outputPath);
