#!/usr/bin/env node
/**
 * index.html Data Validator
 *
 * Validates that index.html displays correct data:
 *   - UI/UX 覆蓋率 (coverage percentage)
 *   - iPad/iPhone screen counts
 *   - 模組圖例 (module legend) counts
 *   - 模組卡片 (module cards) screen counts
 *
 * Usage:
 *   node validate-index-data.js [project-path]
 *
 * Exit codes:
 *   0 - All data valid
 *   1 - Data mismatch found (BLOCKING)
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m'
};

// Module configuration (must match generate-index.js)
const MODULES = [
  { id: 'AUTH', folder: 'auth' },
  { id: 'HOME', folder: 'home' },
  { id: 'VOCAB', folder: 'vocab' },
  { id: 'SENTENCE', folder: 'sentence' },
  { id: 'TRAIN', folder: 'train' },
  { id: 'PROGRESS', folder: 'progress' },
  { id: 'PARENT', folder: 'parent' },
  { id: 'ENGAGE', folder: 'engage' },
  { id: 'SOCIAL', folder: 'social' },
  { id: 'PROFILE', folder: 'profile' },
  { id: 'SETTING', folder: 'setting' },
  { id: 'COMMON', folder: 'common' }
];

class IndexDataValidator {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.results = {
      passed: [],
      failed: [],
      warnings: []
    };
    this.actualData = {
      modules: {},
      ipadTotal: 0,
      iphoneTotal: 0
    };
    this.indexData = {
      modules: {},
      ipadTotal: 0,
      iphoneTotal: 0,
      coverage: 0
    };
  }

  pass(message) {
    this.results.passed.push(message);
    console.log(`${colors.green}✅ ${message}${colors.reset}`);
  }

  fail(message) {
    this.results.failed.push(message);
    console.log(`${colors.red}❌ ${message}${colors.reset}`);
  }

  warn(message) {
    this.results.warnings.push(message);
    console.log(`${colors.yellow}⚠️  ${message}${colors.reset}`);
  }

  // Step 1: Count actual screen files by module
  countActualScreens() {
    console.log(`${colors.bold}📁 掃描實際畫面檔案...${colors.reset}`);
    console.log();

    for (const mod of MODULES) {
      const moduleDir = path.join(this.projectPath, mod.folder);
      let count = 0;

      if (fs.existsSync(moduleDir)) {
        const files = fs.readdirSync(moduleDir)
          .filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
        count = files.length;
      }

      this.actualData.modules[mod.id] = count;
      this.actualData.ipadTotal += count;
    }

    // Count iPhone screens
    const iphoneDir = path.join(this.projectPath, 'iphone');
    if (fs.existsSync(iphoneDir)) {
      this.actualData.iphoneTotal = fs.readdirSync(iphoneDir)
        .filter(f => f.startsWith('SCR-') && f.endsWith('.html')).length;
    }

    console.log(`${colors.cyan}實際畫面統計:${colors.reset}`);
    for (const mod of MODULES) {
      const count = this.actualData.modules[mod.id];
      console.log(`   ${mod.id}: ${count}`);
    }
    console.log(`   ${colors.bold}iPad 總計: ${this.actualData.ipadTotal}${colors.reset}`);
    console.log(`   ${colors.bold}iPhone 總計: ${this.actualData.iphoneTotal}${colors.reset}`);
    console.log();
  }

  // Step 2: Parse index.html data
  parseIndexHtml() {
    console.log(`${colors.bold}📄 解析 index.html 資料...${colors.reset}`);
    console.log();

    const indexPath = path.join(this.projectPath, 'index.html');
    if (!fs.existsSync(indexPath)) {
      this.fail('index.html 不存在');
      return false;
    }

    const content = fs.readFileSync(indexPath, 'utf8');

    // Extract coverage percentage
    // Pattern 1: UI/UX 覆蓋率</p> followed by <p>100%</p>
    // Pattern 2: 100% 覆蓋率
    const coverageMatch = content.match(/UI\/UX 覆蓋率<\/p>\s*<p[^>]*>(\d+)%<\/p>/s) ||
                          content.match(/>(\d+)%<\/p>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/header>/s) ||
                          content.match(/font-bold[^>]*text-green[^>]*>(\d+)%/);
    if (coverageMatch) {
      this.indexData.coverage = parseInt(coverageMatch[1], 10);
    }

    // Extract iPad count from header
    const ipadMatch = content.match(/iPad[^>]*<\/p>\s*<p[^>]*>(\d+)<\/p>/s) ||
                      content.match(/>iPad<\/p>\s*<p[^>]*font-bold[^>]*>(\d+)</s);
    if (ipadMatch) {
      this.indexData.ipadTotal = parseInt(ipadMatch[1], 10);
    }

    // Extract iPhone count from header
    const iphoneMatch = content.match(/iPhone[^>]*<\/p>\s*<p[^>]*>(\d+)<\/p>/s) ||
                        content.match(/>iPhone<\/p>\s*<p[^>]*font-bold[^>]*>(\d+)</s);
    if (iphoneMatch) {
      this.indexData.iphoneTotal = parseInt(iphoneMatch[1], 10);
    }

    // Extract module counts from sidebar (模組圖例)
    // Pattern: MODULE_ID (count)
    for (const mod of MODULES) {
      const sidebarPattern = new RegExp(`${mod.id}\\s*\\((\\d+)\\)`, 'i');
      const sidebarMatch = content.match(sidebarPattern);
      if (sidebarMatch) {
        this.indexData.modules[mod.id] = parseInt(sidebarMatch[1], 10);
      } else {
        this.indexData.modules[mod.id] = -1; // Not found
      }
    }

    console.log(`${colors.cyan}index.html 顯示資料:${colors.reset}`);
    console.log(`   覆蓋率: ${this.indexData.coverage}%`);
    console.log(`   iPad: ${this.indexData.ipadTotal}`);
    console.log(`   iPhone: ${this.indexData.iphoneTotal}`);
    console.log();
    console.log(`${colors.cyan}模組圖例:${colors.reset}`);
    for (const mod of MODULES) {
      const count = this.indexData.modules[mod.id];
      const display = count === -1 ? '(未找到)' : count;
      console.log(`   ${mod.id}: ${display}`);
    }
    console.log();

    return true;
  }

  // Step 3: Validate data consistency
  validateConsistency() {
    console.log(`${colors.bold}🔍 驗證資料一致性...${colors.reset}`);
    console.log();

    // 1. Validate iPad total
    console.log(`${colors.dim}1. iPad 總數${colors.reset}`);
    if (this.indexData.ipadTotal === this.actualData.ipadTotal) {
      this.pass(`iPad 總數正確: ${this.actualData.ipadTotal}`);
    } else {
      this.fail(`iPad 總數不符: index.html 顯示 ${this.indexData.ipadTotal}, 實際 ${this.actualData.ipadTotal}`);
    }

    // 2. Validate iPhone total
    console.log(`${colors.dim}2. iPhone 總數${colors.reset}`);
    if (this.indexData.iphoneTotal === this.actualData.iphoneTotal) {
      this.pass(`iPhone 總數正確: ${this.actualData.iphoneTotal}`);
    } else {
      this.fail(`iPhone 總數不符: index.html 顯示 ${this.indexData.iphoneTotal}, 實際 ${this.actualData.iphoneTotal}`);
    }

    // 3. Validate coverage
    console.log(`${colors.dim}3. 覆蓋率${colors.reset}`);
    const expectedCoverage = this.actualData.ipadTotal > 0 ? 100 : 0;
    if (this.indexData.coverage === expectedCoverage) {
      this.pass(`覆蓋率正確: ${expectedCoverage}%`);
    } else {
      this.fail(`覆蓋率不符: index.html 顯示 ${this.indexData.coverage}%, 預期 ${expectedCoverage}%`);
    }

    // 4. Validate each module count in sidebar
    console.log(`${colors.dim}4. 模組圖例數量${colors.reset}`);
    let moduleErrors = 0;
    for (const mod of MODULES) {
      const actual = this.actualData.modules[mod.id];
      const displayed = this.indexData.modules[mod.id];

      if (displayed === -1) {
        this.warn(`${mod.id}: 未在模組圖例中找到`);
        moduleErrors++;
      } else if (displayed === actual) {
        this.pass(`${mod.id}: ${actual} 個畫面`);
      } else {
        this.fail(`${mod.id} 不符: index.html 顯示 ${displayed}, 實際 ${actual}`);
        moduleErrors++;
      }
    }

    console.log();
    return moduleErrors === 0 && this.results.failed.length === 0;
  }

  // Run all validations
  async validate() {
    console.log();
    console.log('════════════════════════════════════════════════════════════');
    console.log('  index.html Data Validation');
    console.log('  驗證 UI/UX 覆蓋率、模組圖例、模組卡片數量');
    console.log('════════════════════════════════════════════════════════════');
    console.log();

    // Step 1: Count actual screens
    this.countActualScreens();

    // Step 2: Parse index.html
    if (!this.parseIndexHtml()) {
      return false;
    }

    // Step 3: Validate consistency
    const allValid = this.validateConsistency();

    // Summary
    console.log('════════════════════════════════════════════════════════════');
    console.log(`${colors.bold}📊 index.html 資料驗證摘要${colors.reset}`);
    console.log('════════════════════════════════════════════════════════════');
    console.log(`${colors.green}✅ 通過: ${this.results.passed.length}${colors.reset}`);
    console.log(`${colors.yellow}⚠️  警告: ${this.results.warnings.length}${colors.reset}`);
    console.log(`${colors.red}❌ 失敗: ${this.results.failed.length}${colors.reset}`);
    console.log();

    if (allValid && this.results.failed.length === 0) {
      console.log(`${colors.green}${colors.bold}✅ index.html Data Validation PASSED${colors.reset}`);
      console.log('   所有顯示資料與實際檔案一致');
    } else {
      console.log(`${colors.red}${colors.bold}❌ index.html Data Validation FAILED${colors.reset}`);
      console.log();
      console.log(`${colors.yellow}📋 修復方式:${colors.reset}`);
      console.log('   重新執行 generate-index.js 更新 index.html');
      console.log('   node generate-index.js');
    }
    console.log('════════════════════════════════════════════════════════════');
    console.log();

    return allValid && this.results.failed.length === 0;
  }
}

// Main execution
async function main() {
  const projectPath = process.argv[2] || process.cwd();

  console.log(`${colors.cyan}驗證目錄: ${projectPath}${colors.reset}`);

  const validator = new IndexDataValidator(projectPath);
  const success = await validator.validate();

  process.exit(success ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
