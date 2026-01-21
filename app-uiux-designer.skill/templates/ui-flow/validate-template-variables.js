#!/usr/bin/env node
/**
 * Template Variables Validation
 *
 * Detects unreplaced template placeholders like {{VARIABLE_NAME}} in generated files.
 * These placeholders should have been replaced during initialization.
 *
 * Files checked:
 *   - index.html
 *   - device-preview.html
 *   - docs/ui-flow-diagram-ipad.html
 *   - docs/ui-flow-diagram-iphone.html
 *   - All SCR-*.html files
 *
 * Usage:
 *   node validate-template-variables.js [project-path]
 *
 * Exit codes:
 *   0 - No unreplaced variables found
 *   1 - Unreplaced variables detected (BLOCKING)
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

class TemplateVariablesValidator {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.errors = [];
    this.warnings = [];
    this.filesChecked = 0;
    this.variablesFound = [];
  }

  log(message) {
    console.log(message);
  }

  // Find all unreplaced {{...}} variables in content
  findUnreplacedVariables(content, filePath) {
    const pattern = /\{\{([A-Z_][A-Z0-9_]*)\}\}/g;
    const matches = [];
    let match;

    while ((match = pattern.exec(content)) !== null) {
      matches.push({
        file: filePath,
        variable: match[0],
        name: match[1],
        position: match.index,
        line: content.substring(0, match.index).split('\n').length
      });
    }

    return matches;
  }

  // Check a single file
  checkFile(relativePath) {
    const filePath = path.join(this.projectPath, relativePath);

    if (!fs.existsSync(filePath)) {
      return; // Skip non-existent files
    }

    this.filesChecked++;
    const content = fs.readFileSync(filePath, 'utf-8');
    const variables = this.findUnreplacedVariables(content, relativePath);

    if (variables.length > 0) {
      this.variablesFound.push(...variables);
      this.errors.push({
        file: relativePath,
        variables: variables
      });
    }
  }

  // Find all SCR-*.html files
  findScreenFiles() {
    const screenFiles = [];
    const moduleDirs = ['auth', 'home', 'onboard', 'vocab', 'train', 'progress', 'parent', 'social', 'profile', 'setting', 'common'];

    for (const dir of moduleDirs) {
      const dirPath = path.join(this.projectPath, dir);
      if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
        for (const file of files) {
          screenFiles.push(path.join(dir, file));
        }
      }
    }

    // Also check iphone directory
    const iphoneDir = path.join(this.projectPath, 'iphone');
    if (fs.existsSync(iphoneDir)) {
      const files = fs.readdirSync(iphoneDir).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
      for (const file of files) {
        screenFiles.push(path.join('iphone', file));
      }
    }

    return screenFiles;
  }

  // Run validation
  run() {
    console.log('');
    console.log(`${colors.bold}🔍 Template Variables Validation${colors.reset}`);
    console.log(`${colors.dim}   檢測未替換的模板變數 {{...}}${colors.reset}`);
    console.log('');

    // Core files to check
    const coreFiles = [
      'index.html',
      'device-preview.html',
      'docs/ui-flow-diagram-ipad.html',
      'docs/ui-flow-diagram-iphone.html'
    ];

    this.log(`${colors.cyan}📁 檢查核心檔案...${colors.reset}`);
    for (const file of coreFiles) {
      this.checkFile(file);
    }

    // Check screen files
    this.log(`${colors.cyan}📱 檢查畫面檔案...${colors.reset}`);
    const screenFiles = this.findScreenFiles();
    for (const file of screenFiles) {
      this.checkFile(file);
    }

    // Print results
    this.printResults();

    return this.errors.length === 0;
  }

  printResults() {
    console.log('');
    console.log(`${colors.bold}📊 驗證結果${colors.reset}`);
    console.log(`   檔案檢查數: ${this.filesChecked}`);

    if (this.errors.length === 0) {
      console.log(`${colors.green}   ✅ 未發現未替換的模板變數${colors.reset}`);
      console.log('');
      return;
    }

    console.log(`${colors.red}   ❌ 發現 ${this.variablesFound.length} 個未替換變數${colors.reset}`);
    console.log('');

    // Group by file
    const byFile = {};
    for (const v of this.variablesFound) {
      if (!byFile[v.file]) {
        byFile[v.file] = [];
      }
      byFile[v.file].push(v);
    }

    console.log(`${colors.bold}📋 詳細清單:${colors.reset}`);
    for (const [file, vars] of Object.entries(byFile)) {
      console.log(`${colors.yellow}   ${file}${colors.reset}`);
      for (const v of vars) {
        console.log(`${colors.red}      Line ${v.line}: ${v.variable}${colors.reset}`);
      }
    }

    console.log('');
    console.log(`${colors.bold}🔧 常見未替換變數及修復方式:${colors.reset}`);
    console.log('');

    const knownVariables = {
      'FIRST_SCREEN_PATH': "初始畫面路徑，應為 'auth/SCR-AUTH-001-login.html'",
      'PROJECT_NAME': '專案名稱',
      'TOTAL_SCREENS': '畫面總數',
      'MODULE_COUNT': '模組數量',
      'PRIMARY_COLOR': '主色調',
      'ACCENT_COLOR': '強調色'
    };

    const uniqueVars = [...new Set(this.variablesFound.map(v => v.name))];
    for (const varName of uniqueVars) {
      const desc = knownVariables[varName] || '自定義變數';
      console.log(`   {{${varName}}}: ${desc}`);
    }

    console.log('');
    console.log(`${colors.red}${colors.bold}⛔ 驗證失敗！請修復上述未替換變數後重新執行驗證。${colors.reset}`);
    console.log('');
  }
}

// Main execution
function main() {
  const projectPath = process.argv[2] || process.cwd();

  const validator = new TemplateVariablesValidator(projectPath);
  const success = validator.run();

  process.exit(success ? 0 : 1);
}

main();
