#!/usr/bin/env node

/**
 * convert-to-iphone.js
 * iPad HTML -> iPhone HTML 轉換腳本 (Node.js 跨平台版本)
 *
 * 功能:
 *   - 保留模組子目錄結構 (iphone/auth/, iphone/vocab/, etc.)
 *   - 支援 CSS 變數替換 (--ipad-width → --iphone-width)
 *   - 支援硬編碼像素值替換 (1194px → 393px)
 *   - 跨平台支援 (Windows, macOS, Linux)
 *
 * 使用方式:
 *   cd {PROJECT}/04-ui-flow
 *   node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/scripts/convert-to-iphone.js
 *
 * @version 2.0
 */

const fs = require('fs');
const path = require('path');

// ANSI 顏色
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m'
};

// 排除的目錄
const EXCLUDE_DIRS = ['iphone', 'docs', 'shared', 'workspace', 'screenshots', 'node_modules'];

// 替換規則
const REPLACEMENTS = [
  // CSS 變數替換 (優先)
  { pattern: /width: var\(--ipad-width\);/g, replacement: 'width: var(--iphone-width);' },
  { pattern: /height: var\(--ipad-height\);/g, replacement: 'height: var(--iphone-height);' },
  // 硬編碼像素值替換
  { pattern: /width: 1194px;/g, replacement: 'width: 393px;' },
  { pattern: /height: 834px;/g, replacement: 'height: 852px;' },
  // viewport meta 替換
  { pattern: /width=1194, height=834/g, replacement: 'width=393, height=852' }
];

class IpadToIphoneConverter {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.modules = [];
    this.stats = {
      totalConverted: 0,
      totalErrors: 0,
      moduleStats: {}
    };
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  // 偵測模組目錄
  detectModules() {
    this.log('\n📁 偵測模組目錄...', 'cyan');

    const entries = fs.readdirSync(this.projectPath, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (EXCLUDE_DIRS.includes(entry.name)) continue;

      const modulePath = path.join(this.projectPath, entry.name);
      const files = fs.readdirSync(modulePath).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));

      if (files.length > 0) {
        this.modules.push({
          name: entry.name,
          path: modulePath,
          files: files
        });
        this.log(`   ✓ ${entry.name} (${files.length} 個畫面)`, 'green');
      }
    }

    return this.modules.length > 0;
  }

  // 轉換單一檔案
  convertFile(ipadPath, iphonePath) {
    try {
      let content = fs.readFileSync(ipadPath, 'utf8');

      // 執行所有替換
      for (const rule of REPLACEMENTS) {
        content = content.replace(rule.pattern, rule.replacement);
      }

      // 確保目標目錄存在
      const dir = path.dirname(iphonePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      fs.writeFileSync(iphonePath, content, 'utf8');
      return true;
    } catch (error) {
      console.error(`${colors.red}  ✗ 轉換失敗: ${path.basename(ipadPath)} - ${error.message}${colors.reset}`);
      return false;
    }
  }

  // 轉換所有模組
  convertAll() {
    this.log('\n📱 開始轉換...\n', 'cyan');

    for (const module of this.modules) {
      const iphoneModulePath = path.join(this.projectPath, 'iphone', module.name);

      // 創建 iPhone 模組目錄
      if (!fs.existsSync(iphoneModulePath)) {
        fs.mkdirSync(iphoneModulePath, { recursive: true });
      }

      let moduleConverted = 0;

      for (const file of module.files) {
        const ipadPath = path.join(module.path, file);
        const iphonePath = path.join(iphoneModulePath, file);

        if (this.convertFile(ipadPath, iphonePath)) {
          moduleConverted++;
          this.stats.totalConverted++;
        } else {
          this.stats.totalErrors++;
        }
      }

      this.stats.moduleStats[module.name] = moduleConverted;
      this.log(`   ✓ ${module.name}: ${moduleConverted} 個檔案`, 'green');
    }
  }

  // 驗證結果
  verify() {
    this.log('\n════════════════════════════════════════════════════════════');
    this.log(`${colors.bold}📊 轉換結果${colors.reset}`);
    this.log('════════════════════════════════════════════════════════════');

    // 統計 iPad 畫面
    let ipadCount = 0;
    for (const module of this.modules) {
      ipadCount += module.files.length;
    }

    // 統計 iPhone 畫面
    const iphonePath = path.join(this.projectPath, 'iphone');
    let iphoneCount = 0;
    if (fs.existsSync(iphonePath)) {
      const countFiles = (dir) => {
        let count = 0;
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory()) {
            count += countFiles(path.join(dir, entry.name));
          } else if (entry.name.startsWith('SCR-') && entry.name.endsWith('.html')) {
            count++;
          }
        }
        return count;
      };
      iphoneCount = countFiles(iphonePath);
    }

    console.log(`   iPad 畫面:   ${ipadCount}`);
    console.log(`   iPhone 畫面: ${iphoneCount}`);
    console.log(`   轉換成功:    ${this.stats.totalConverted}`);
    console.log(`   轉換失敗:    ${this.stats.totalErrors}`);
    console.log();

    if (iphoneCount === ipadCount) {
      this.log(`✅ 驗證通過：iPad (${ipadCount}) = iPhone (${iphoneCount})`, 'green');
    } else {
      this.log(`⚠️  警告：iPad (${ipadCount}) != iPhone (${iphoneCount})`, 'yellow');
    }

    // 抽樣檢查
    this.log('\n🔍 抽樣檢查...', 'cyan');
    if (fs.existsSync(iphonePath)) {
      const findSample = (dir) => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory()) {
            const found = findSample(path.join(dir, entry.name));
            if (found) return found;
          } else if (entry.name.startsWith('SCR-') && entry.name.endsWith('.html')) {
            return path.join(dir, entry.name);
          }
        }
        return null;
      };

      const sampleFile = findSample(iphonePath);
      if (sampleFile) {
        const content = fs.readFileSync(sampleFile, 'utf8');
        if (content.includes('var(--iphone-width)')) {
          this.log('   ✓ CSS 變數已正確替換', 'green');
        } else if (content.includes('width: 393px')) {
          this.log('   ✓ 硬編碼像素值已正確替換', 'green');
        } else {
          this.log('   ⚠ 尺寸替換可能未生效，請手動檢查', 'yellow');
        }
      }
    }

    return this.stats.totalErrors === 0;
  }

  // 執行轉換
  run() {
    console.log();
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║     iPad → iPhone HTML 轉換工具 v2.0 (Node.js)             ║');
    console.log('║     保留模組子目錄結構 + CSS 變數支援                       ║');
    console.log('╚════════════════════════════════════════════════════════════╝');

    // 確認當前目錄
    const indexPath = path.join(this.projectPath, 'index.html');
    if (!fs.existsSync(indexPath)) {
      this.log('\n錯誤：請在 04-ui-flow 目錄下執行此腳本', 'red');
      console.log('用法: cd {PROJECT}/04-ui-flow && node convert-to-iphone.js');
      process.exit(1);
    }

    // 偵測模組
    if (!this.detectModules()) {
      this.log('\n錯誤：未找到任何模組目錄', 'red');
      process.exit(1);
    }

    // 執行轉換
    this.convertAll();

    // 驗證結果
    const success = this.verify();

    // 完成訊息
    console.log();
    console.log('════════════════════════════════════════════════════════════');
    this.log('✅ 轉換完成！', 'green');
    console.log();
    console.log('下一步:');
    console.log('  1. 執行驗證腳本確認導航連結');
    console.log('  2. 更新 ui-flow-diagram-iphone.html');
    console.log('  3. 更新 device-preview.html 側邊欄');
    console.log('════════════════════════════════════════════════════════════');

    process.exit(success ? 0 : 1);
  }
}

// 主程式
const projectPath = process.argv[2] || process.cwd();
const converter = new IpadToIphoneConverter(projectPath);
converter.run();
