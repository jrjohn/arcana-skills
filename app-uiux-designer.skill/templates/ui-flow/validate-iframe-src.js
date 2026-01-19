#!/usr/bin/env node
/**
 * iframe src Path Validator
 *
 * Validates that all iframe src paths in UI Flow files point to existing HTML files.
 * This is a BLOCKING validation - if any path is missing, the process cannot continue.
 *
 * Usage:
 *   node validate-iframe-src.js [project-path]
 *
 * Validates:
 *   - docs/ui-flow-diagram-ipad.html
 *   - docs/ui-flow-diagram-iphone.html
 *   - device-preview.html
 *
 * Exit codes:
 *   0 - All paths valid
 *   1 - Missing paths found (BLOCKING)
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

class IframeSrcValidator {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.results = {
      ipadDiagram: { total: 0, valid: 0, missing: [] },
      iphoneDiagram: { total: 0, valid: 0, missing: [] },
      devicePreview: { total: 0, valid: 0, missing: [] },
      devicePreviewIframes: { total: 0, valid: 0, missing: [] },
      dataIphoneAttrs: { total: 0, valid: 0, missing: [] }
    };
    this.actualScreens = { ipad: [], iphone: [] };
  }

  // Find all actual screen files
  findActualScreens() {
    const findScreens = (dir, excludePaths = []) => {
      const screens = [];
      const searchDir = path.join(this.projectPath, dir);

      if (!fs.existsSync(searchDir)) return screens;

      const walk = (currentDir) => {
        const files = fs.readdirSync(currentDir);
        for (const file of files) {
          const filePath = path.join(currentDir, file);
          const relativePath = path.relative(this.projectPath, filePath);

          // Skip excluded paths
          if (excludePaths.some(ex => relativePath.startsWith(ex))) continue;

          const stat = fs.statSync(filePath);
          if (stat.isDirectory()) {
            walk(filePath);
          } else if (file.match(/^SCR-.*\.html$/)) {
            screens.push(relativePath);
          }
        }
      };

      walk(searchDir);
      return screens;
    };

    // iPad screens (exclude iphone/ and docs/)
    this.actualScreens.ipad = findScreens('.', ['iphone', 'docs']).filter(f => f.match(/^(?!iphone\/).*SCR-.*\.html$/));

    // iPhone screens
    this.actualScreens.iphone = findScreens('iphone', []);

    console.log(`${colors.cyan}📁 實際畫面檔案:${colors.reset}`);
    console.log(`   iPad: ${this.actualScreens.ipad.length} 個`);
    console.log(`   iPhone: ${this.actualScreens.iphone.length} 個`);
    console.log();
  }

  // Extract iframe src paths from HTML file
  extractIframeSrc(filePath, pattern) {
    if (!fs.existsSync(filePath)) {
      return null;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const matches = content.match(pattern) || [];

    // Clean up matches
    return matches.map(m => {
      // Handle different src patterns
      let src = m;
      if (m.includes('src="')) {
        src = m.replace(/.*src="([^"]+)".*/, '$1');
      } else if (m.includes("src='")) {
        src = m.replace(/.*src='([^']+)'.*/, '$1');
      } else if (m.includes('loadScreen(')) {
        src = m.replace(/.*loadScreen\(['"]([^'"]+)['"]\).*/, '$1');
      }
      // Remove ../ prefix for relative paths
      return src.replace(/^\.\.\//, '');
    }).filter(Boolean);
  }

  // Validate iPad Diagram
  validateIpadDiagram() {
    const filePath = path.join(this.projectPath, 'docs/ui-flow-diagram-ipad.html');
    console.log(`${colors.bold}📱 驗證 ui-flow-diagram-ipad.html${colors.reset}`);

    if (!fs.existsSync(filePath)) {
      console.log(`${colors.red}❌ 檔案不存在: docs/ui-flow-diagram-ipad.html${colors.reset}`);
      this.results.ipadDiagram.missing.push('FILE_NOT_FOUND');
      return;
    }

    const content = fs.readFileSync(filePath, 'utf8');

    // Extract iframe src paths (pattern: src="../{module}/SCR-*.html")
    const srcPattern = /src="\.\.\/([^"]+\.html)"/g;
    const matches = [...content.matchAll(srcPattern)].map(m => m[1]);

    this.results.ipadDiagram.total = matches.length;

    for (const src of matches) {
      const fullPath = path.join(this.projectPath, src);
      if (fs.existsSync(fullPath)) {
        this.results.ipadDiagram.valid++;
      } else {
        this.results.ipadDiagram.missing.push(src);
      }
    }

    // Report
    if (this.results.ipadDiagram.missing.length === 0) {
      console.log(`${colors.green}✅ 全部 ${this.results.ipadDiagram.total} 個路徑正確${colors.reset}`);
    } else {
      console.log(`${colors.red}❌ ${this.results.ipadDiagram.missing.length} 個路徑缺失:${colors.reset}`);
      for (const missing of this.results.ipadDiagram.missing) {
        console.log(`   ${colors.red}- ${missing}${colors.reset}`);
      }
    }
    console.log();
  }

  // Validate iPhone Diagram
  validateIphoneDiagram() {
    const filePath = path.join(this.projectPath, 'docs/ui-flow-diagram-iphone.html');
    console.log(`${colors.bold}📱 驗證 ui-flow-diagram-iphone.html${colors.reset}`);

    if (!fs.existsSync(filePath)) {
      console.log(`${colors.red}❌ 檔案不存在: docs/ui-flow-diagram-iphone.html${colors.reset}`);
      this.results.iphoneDiagram.missing.push('FILE_NOT_FOUND');
      return;
    }

    const content = fs.readFileSync(filePath, 'utf8');

    // Extract iframe src paths
    const srcPattern = /src="\.\.\/([^"]+\.html)"/g;
    const matches = [...content.matchAll(srcPattern)].map(m => m[1]);

    this.results.iphoneDiagram.total = matches.length;

    for (const src of matches) {
      const fullPath = path.join(this.projectPath, src);
      if (fs.existsSync(fullPath)) {
        this.results.iphoneDiagram.valid++;
      } else {
        this.results.iphoneDiagram.missing.push(src);
      }
    }

    // Report
    if (this.results.iphoneDiagram.missing.length === 0) {
      console.log(`${colors.green}✅ 全部 ${this.results.iphoneDiagram.total} 個路徑正確${colors.reset}`);
    } else {
      console.log(`${colors.red}❌ ${this.results.iphoneDiagram.missing.length} 個路徑缺失:${colors.reset}`);
      for (const missing of this.results.iphoneDiagram.missing) {
        console.log(`   ${colors.red}- ${missing}${colors.reset}`);
      }
    }
    console.log();
  }

  // Validate device-preview.html
  validateDevicePreview() {
    const filePath = path.join(this.projectPath, 'device-preview.html');
    console.log(`${colors.bold}📱 驗證 device-preview.html${colors.reset}`);

    if (!fs.existsSync(filePath)) {
      console.log(`${colors.red}❌ 檔案不存在: device-preview.html${colors.reset}`);
      this.results.devicePreview.missing.push('FILE_NOT_FOUND');
      return;
    }

    const content = fs.readFileSync(filePath, 'utf8');

    // 1. Validate loadScreen paths (sidebar screen items)
    console.log(`${colors.dim}   檢查 loadScreen() 呼叫...${colors.reset}`);
    const loadPattern = /loadScreen\(['"]([^'"]+\.html)['"]/g;
    const matches = [...content.matchAll(loadPattern)].map(m => m[1]);

    // Get unique paths
    const uniquePaths = [...new Set(matches)];
    this.results.devicePreview.total = uniquePaths.length;

    for (const src of uniquePaths) {
      const fullPath = path.join(this.projectPath, src);
      if (fs.existsSync(fullPath)) {
        this.results.devicePreview.valid++;
      } else {
        this.results.devicePreview.missing.push(src);
      }
    }

    // Report loadScreen
    if (this.results.devicePreview.missing.length === 0) {
      console.log(`${colors.green}   ✅ loadScreen: ${this.results.devicePreview.total} 個路徑正確${colors.reset}`);
    } else {
      console.log(`${colors.red}   ❌ loadScreen: ${this.results.devicePreview.missing.length} 個路徑缺失${colors.reset}`);
    }

    // 2. Validate initial iframe src attributes (iPad, iPad mini, iPhone)
    console.log(`${colors.dim}   檢查 iframe src 屬性...${colors.reset}`);
    const iframeIds = ['preview-iframe-ipad', 'preview-iframe-ipad-mini', 'preview-iframe-iphone'];
    const iframeSrcPattern = /id="(preview-iframe-(?:ipad|ipad-mini|iphone))"\s+src="([^"]+)"/g;
    const iframeSrcs = [...content.matchAll(iframeSrcPattern)];

    this.results.devicePreviewIframes.total = iframeSrcs.length;

    for (const [, id, src] of iframeSrcs) {
      const fullPath = path.join(this.projectPath, src);
      if (fs.existsSync(fullPath)) {
        this.results.devicePreviewIframes.valid++;
      } else {
        this.results.devicePreviewIframes.missing.push(`${id}: ${src}`);
      }
    }

    // Report iframe src
    if (this.results.devicePreviewIframes.missing.length === 0) {
      console.log(`${colors.green}   ✅ iframe src: ${this.results.devicePreviewIframes.total} 個裝置正確 (iPad/iPad mini/iPhone)${colors.reset}`);
    } else {
      console.log(`${colors.red}   ❌ iframe src: ${this.results.devicePreviewIframes.missing.length} 個缺失:${colors.reset}`);
      for (const missing of this.results.devicePreviewIframes.missing) {
        console.log(`      ${colors.red}- ${missing}${colors.reset}`);
      }
    }

    // 3. Validate data-iphone attributes
    console.log(`${colors.dim}   檢查 data-iphone 屬性...${colors.reset}`);
    const dataIphonePattern = /data-iphone="([^"]+)"/g;
    const dataIphoneMatches = [...content.matchAll(dataIphonePattern)].map(m => m[1]);

    const uniqueIphonePaths = [...new Set(dataIphoneMatches)];
    this.results.dataIphoneAttrs.total = uniqueIphonePaths.length;

    for (const src of uniqueIphonePaths) {
      const fullPath = path.join(this.projectPath, src);
      if (fs.existsSync(fullPath)) {
        this.results.dataIphoneAttrs.valid++;
      } else {
        this.results.dataIphoneAttrs.missing.push(src);
      }
    }

    // Report data-iphone
    if (this.results.dataIphoneAttrs.missing.length === 0) {
      console.log(`${colors.green}   ✅ data-iphone: ${this.results.dataIphoneAttrs.total} 個 iPhone 路徑正確${colors.reset}`);
    } else {
      console.log(`${colors.red}   ❌ data-iphone: ${this.results.dataIphoneAttrs.missing.length} 個路徑缺失:${colors.reset}`);
      for (const missing of this.results.dataIphoneAttrs.missing) {
        console.log(`      ${colors.red}- ${missing}${colors.reset}`);
      }
    }

    console.log();
  }

  // Validate screen count consistency
  validateScreenCountConsistency() {
    console.log(`${colors.bold}📊 驗證畫面數量一致性${colors.reset}`);

    const actualCount = this.actualScreens.ipad.length;
    const ipadDiagramCount = this.results.ipadDiagram.total;
    const iphoneDiagramCount = this.results.iphoneDiagram.total;
    const previewCount = this.results.devicePreview.total;

    console.log(`   實際 iPad 畫面: ${actualCount}`);
    console.log(`   iPad Diagram: ${ipadDiagramCount}`);
    console.log(`   iPhone Diagram: ${iphoneDiagramCount}`);
    console.log(`   device-preview: ${previewCount}`);

    const allMatch = actualCount === ipadDiagramCount &&
                     actualCount === iphoneDiagramCount &&
                     actualCount === previewCount;

    if (allMatch) {
      console.log(`${colors.green}✅ 畫面數量一致: ${actualCount} 個${colors.reset}`);
    } else {
      console.log(`${colors.red}❌ 畫面數量不一致！${colors.reset}`);
    }
    console.log();

    return allMatch;
  }

  // Run all validations
  async validate() {
    console.log();
    console.log('════════════════════════════════════════════════════════════');
    console.log('  iframe src Path Validation (BLOCKING)');
    console.log('════════════════════════════════════════════════════════════');
    console.log();

    // Find actual screens first
    this.findActualScreens();

    // Validate each file
    this.validateIpadDiagram();
    this.validateIphoneDiagram();
    this.validateDevicePreview();

    // Check consistency
    const consistencyOk = this.validateScreenCountConsistency();

    // Calculate totals
    const totalMissing =
      this.results.ipadDiagram.missing.length +
      this.results.iphoneDiagram.missing.length +
      this.results.devicePreview.missing.length +
      this.results.devicePreviewIframes.missing.length +
      this.results.dataIphoneAttrs.missing.length;

    // Summary
    console.log('════════════════════════════════════════════════════════════');
    console.log(`${colors.bold}📊 iframe src 驗證摘要${colors.reset}`);
    console.log('════════════════════════════════════════════════════════════');

    if (totalMissing === 0 && consistencyOk) {
      console.log(`${colors.green}${colors.bold}✅ iframe src Path Validation PASSED${colors.reset}`);
      console.log('   所有路徑指向存在的檔案');
      console.log('   可以進入下一階段');
      console.log('════════════════════════════════════════════════════════════');
      console.log();
      return true;
    } else {
      console.log(`${colors.red}${colors.bold}❌ iframe src Path Validation FAILED${colors.reset}`);
      console.log(`   缺失路徑: ${totalMissing} 個`);
      console.log(`   數量一致: ${consistencyOk ? '是' : '否'}`);
      console.log();
      console.log(`${colors.yellow}📋 修復方式:${colors.reset}`);
      console.log('   1. 確認所有畫面已正確生成');
      console.log('   2. 更新 Diagram 檔案使用正確的畫面路徑');
      console.log('   3. 更新 device-preview.html 側邊欄');
      console.log();
      console.log(`${colors.red}⚠️ 禁止進入下一階段！${colors.reset}`);
      console.log('════════════════════════════════════════════════════════════');
      console.log();

      // Write error log
      this.writeErrorLog();

      return false;
    }
  }

  // Write error log for recovery
  writeErrorLog() {
    const errorLog = {
      timestamp: new Date().toISOString(),
      phase: 'iframe-src-validation',
      results: this.results,
      actualScreenCount: {
        ipad: this.actualScreens.ipad.length,
        iphone: this.actualScreens.iphone.length
      },
      recovery_action: 'fix-diagram-and-preview-files'
    };

    const logPath = path.join(this.projectPath, 'workspace/iframe-src-error-log.json');

    // Ensure workspace directory exists
    const workspaceDir = path.dirname(logPath);
    if (!fs.existsSync(workspaceDir)) {
      fs.mkdirSync(workspaceDir, { recursive: true });
    }

    fs.writeFileSync(logPath, JSON.stringify(errorLog, null, 2));
    console.log(`${colors.dim}錯誤日誌: workspace/iframe-src-error-log.json${colors.reset}`);
  }
}

// Main execution
async function main() {
  const projectPath = process.argv[2] || process.cwd();

  console.log(`${colors.cyan}驗證目錄: ${projectPath}${colors.reset}`);

  const validator = new IframeSrcValidator(projectPath);
  const success = await validator.validate();

  process.exit(success ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
