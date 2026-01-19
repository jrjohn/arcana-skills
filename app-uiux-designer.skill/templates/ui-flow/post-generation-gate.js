#!/usr/bin/env node
/**
 * Post-Generation Gate (BLOCKING)
 *
 * This script MUST be executed after generating:
 *   - index.html
 *   - device-preview.html
 *   - docs/ui-flow-diagram-ipad.html
 *   - docs/ui-flow-diagram-iphone.html
 *
 * It runs all validation scripts and blocks proceeding if any fail.
 *
 * Usage:
 *   node post-generation-gate.js [project-path]
 *
 * Exit codes:
 *   0 - All validations passed, can proceed to next phase
 *   1 - Validation failed, BLOCKED from proceeding
 */

const { execSync, spawnSync } = require('child_process');
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
  dim: '\x1b[2m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m'
};

class PostGenerationGate {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.skillDir = path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill');
    this.validationResults = [];
    this.passed = true;
  }

  log(message) {
    console.log(message);
  }

  // Run a validation script
  runValidation(name, scriptPath, args = []) {
    this.log(`${colors.cyan}▶ 執行 ${name}...${colors.reset}`);

    const result = spawnSync('node', [scriptPath, ...args], {
      cwd: this.projectPath,
      stdio: 'inherit',
      encoding: 'utf8'
    });

    const success = result.status === 0;
    this.validationResults.push({ name, success, exitCode: result.status });

    if (!success) {
      this.passed = false;
    }

    return success;
  }

  // Check required files exist
  checkRequiredFiles() {
    this.log(`${colors.bold}📁 檢查必要檔案...${colors.reset}`);

    const requiredFiles = [
      'index.html',
      'device-preview.html',
      'docs/ui-flow-diagram-ipad.html',
      'docs/ui-flow-diagram-iphone.html'
    ];

    const missing = [];
    for (const file of requiredFiles) {
      const filePath = path.join(this.projectPath, file);
      if (fs.existsSync(filePath)) {
        this.log(`${colors.green}   ✅ ${file}${colors.reset}`);
      } else {
        this.log(`${colors.red}   ❌ ${file} (缺失)${colors.reset}`);
        missing.push(file);
      }
    }

    if (missing.length > 0) {
      this.passed = false;
      this.validationResults.push({
        name: 'Required Files Check',
        success: false,
        missing
      });
      return false;
    }

    this.validationResults.push({ name: 'Required Files Check', success: true });
    this.log('');
    return true;
  }

  // Update current-process.json based on result
  updateProcessStatus(success) {
    const processFile = path.join(this.projectPath, 'workspace/current-process.json');

    if (!fs.existsSync(processFile)) {
      this.log(`${colors.yellow}⚠️ workspace/current-process.json 不存在${colors.reset}`);
      return;
    }

    try {
      const data = JSON.parse(fs.readFileSync(processFile, 'utf8'));

      if (success) {
        data.context.last_action = 'Post-Generation Gate PASSED';
        data.context.validation_passed = true;
        data.context.validation_time = new Date().toISOString();
      } else {
        data.context.last_action = 'Post-Generation Gate FAILED - BLOCKED';
        data.context.validation_passed = false;
        data.context.validation_time = new Date().toISOString();
        // Reset progress if failed
        if (data.progress['03-generation'] === 'completed') {
          data.progress['03-generation'] = 'in_progress';
        }
        if (data.progress['05-diagram'] === 'completed') {
          data.progress['05-diagram'] = 'in_progress';
        }
      }

      fs.writeFileSync(processFile, JSON.stringify(data, null, 2));
    } catch (err) {
      this.log(`${colors.yellow}⚠️ 無法更新 current-process.json: ${err.message}${colors.reset}`);
    }
  }

  // Write validation report
  writeReport() {
    const reportPath = path.join(this.projectPath, 'workspace/validation-report.json');

    const report = {
      timestamp: new Date().toISOString(),
      passed: this.passed,
      results: this.validationResults,
      action: this.passed ? 'PROCEED' : 'BLOCKED'
    };

    // Ensure workspace exists
    const workspaceDir = path.dirname(reportPath);
    if (!fs.existsSync(workspaceDir)) {
      fs.mkdirSync(workspaceDir, { recursive: true });
    }

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    this.log(`${colors.dim}報告已寫入: workspace/validation-report.json${colors.reset}`);
  }

  // Main gate execution
  async run() {
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║           POST-GENERATION GATE (BLOCKING)                  ║');
    console.log('║    產生 index.html / device-preview.html 後自動驗證         ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log(`${colors.cyan}專案目錄: ${this.projectPath}${colors.reset}`);
    console.log('');

    // Step 1: Check required files
    if (!this.checkRequiredFiles()) {
      this.log(`${colors.red}${colors.bold}⛔ 必要檔案缺失，無法繼續驗證${colors.reset}`);
      this.printFinalResult();
      return false;
    }

    // Step 2: Run iframe src validation
    const iframeSrcScript = path.join(this.skillDir, 'templates/ui-flow/validate-iframe-src.js');
    if (fs.existsSync(iframeSrcScript)) {
      this.runValidation('iframe src Path Validation', iframeSrcScript, [this.projectPath]);
    } else {
      this.log(`${colors.yellow}⚠️ validate-iframe-src.js 不存在${colors.reset}`);
    }

    // Step 3: Run consistency validation
    const consistencyScript = path.join(this.skillDir, 'templates/ui-flow/validate-consistency.js');
    if (fs.existsSync(consistencyScript)) {
      this.runValidation('Consistency Validation', consistencyScript, [this.projectPath]);
    }

    // Step 4: Run navigation validation (optional, may not exist)
    const navigationScript = path.join(this.skillDir, 'templates/ui-flow/validate-navigation.js');
    if (fs.existsSync(navigationScript)) {
      // Navigation validation requires screen files, run it
      this.runValidation('Navigation Validation', navigationScript, [this.projectPath]);
    }

    // Step 5: Run index.html data validation (UI/UX 覆蓋率, 模組圖例, 模組卡片數量)
    const indexDataScript = path.join(this.skillDir, 'templates/ui-flow/validate-index-data.js');
    if (fs.existsSync(indexDataScript)) {
      this.runValidation('index.html Data Validation', indexDataScript, [this.projectPath]);
    }

    // Print final result
    this.printFinalResult();

    // Update process status and write report
    this.updateProcessStatus(this.passed);
    this.writeReport();

    return this.passed;
  }

  printFinalResult() {
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');

    if (this.passed) {
      console.log(`║  ${colors.bgGreen}${colors.bold}  ✅ POST-GENERATION GATE PASSED  ${colors.reset}                        ║`);
      console.log('╠════════════════════════════════════════════════════════════╣');
      console.log('║  所有驗證通過，可以進入下一階段                              ║');
      console.log('║                                                            ║');
      console.log('║  下一步:                                                   ║');
      console.log('║  • 若在 03-generation → 進入 04-validation                 ║');
      console.log('║  • 若在 05-diagram → 進入 06-screenshot                    ║');
    } else {
      console.log(`║  ${colors.bgRed}${colors.bold}  ⛔ POST-GENERATION GATE FAILED  ${colors.reset}                         ║`);
      console.log('╠════════════════════════════════════════════════════════════╣');
      console.log('║  驗證失敗，禁止進入下一階段！                                ║');
      console.log('║                                                            ║');
      console.log('║  修復步驟:                                                  ║');
      console.log('║  1. 檢查 workspace/validation-report.json 了解詳情          ║');
      console.log('║  2. 修復所有缺失的路徑                                      ║');
      console.log('║  3. 重新執行此驗證腳本                                      ║');
    }

    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
  }
}

// Main execution
async function main() {
  const projectPath = process.argv[2] || process.cwd();

  const gate = new PostGenerationGate(projectPath);
  const success = await gate.run();

  process.exit(success ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
