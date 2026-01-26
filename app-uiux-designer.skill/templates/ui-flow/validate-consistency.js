#!/usr/bin/env node
/**
 * UI Flow Consistency Validator
 *
 * Validates that generated UI Flow matches reference-example standards.
 *
 * Usage:
 *   node validate-consistency.js [project-path]
 *
 * If project-path is not provided, uses current directory.
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

class ConsistencyValidator {
  constructor(projectPath) {
    this.projectPath = projectPath || process.cwd();
    this.standards = null;
    this.results = { passed: [], failed: [], warnings: [] };
  }

  loadStandards() {
    // Try multiple locations for standards.json
    const locations = [
      path.join(this.projectPath, 'standards.json'),
      path.join(__dirname, 'reference-example', 'standards.json'),
      path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill/templates/ui-flow/reference-example/standards.json')
    ];

    for (const loc of locations) {
      if (fs.existsSync(loc)) {
        this.standards = JSON.parse(fs.readFileSync(loc, 'utf8'));
        return true;
      }
    }

    console.error(`${colors.red}Error: standards.json not found${colors.reset}`);
    console.error('Searched locations:');
    locations.forEach(loc => console.error(`  - ${loc}`));
    return false;
  }

  pass(category, message) {
    this.results.passed.push({ category, message });
  }

  fail(category, message) {
    this.results.failed.push({ category, message });
  }

  warn(category, message) {
    this.results.warnings.push({ category, message });
  }

  // 1. File Structure Validation
  validateFileStructure() {
    const category = 'File Structure';
    const required = this.standards.requiredFiles;

    // Check root files
    for (const file of required.root) {
      const filePath = path.join(this.projectPath, file);
      if (fs.existsSync(filePath)) {
        this.pass(category, `${file} exists`);
      } else {
        this.fail(category, `${file} missing`);
      }
    }

    // Check docs files
    for (const file of required.docs) {
      const filePath = path.join(this.projectPath, 'docs', file);
      if (fs.existsSync(filePath)) {
        this.pass(category, `docs/${file} exists`);
      } else {
        this.fail(category, `docs/${file} missing`);
      }
    }

    // Check shared files
    for (const file of required.shared) {
      const filePath = path.join(this.projectPath, 'shared', file);
      if (fs.existsSync(filePath)) {
        this.pass(category, `shared/${file} exists`);
      } else {
        this.warn(category, `shared/${file} missing (optional)`);
      }
    }
  }

  // 2. Device Specifications Validation
  validateDeviceSpecs(device) {
    const category = `Device Specs (${device})`;
    const specs = this.standards.devices[device];
    const cssPatterns = this.standards.cssPatterns;

    // Determine which file to check
    const diagramFile = device === 'iphone'
      ? 'docs/ui-flow-diagram.html'
      : 'docs/ui-flow-diagram-ipad.html';

    const filePath = path.join(this.projectPath, diagramFile);
    if (!fs.existsSync(filePath)) {
      this.fail(category, `${diagramFile} not found`);
      return;
    }

    const content = fs.readFileSync(filePath, 'utf8');

    // Check frame size
    const frameKey = device === 'iphone' ? 'iphoneFrame' : 'ipadFrame';
    const expectedWidth = cssPatterns[frameKey].width;
    const expectedHeight = cssPatterns[frameKey].height;

    if (content.includes(`width: ${expectedWidth}`) || content.includes(`width:${expectedWidth}`)) {
      this.pass(category, `Frame width: ${expectedWidth}`);
    } else {
      this.fail(category, `Frame width should be ${expectedWidth}`);
    }

    if (content.includes(`height: ${expectedHeight}`) || content.includes(`height:${expectedHeight}`)) {
      this.pass(category, `Frame height: ${expectedHeight}`);
    } else {
      this.fail(category, `Frame height should be ${expectedHeight}`);
    }

    // Check scale factor
    const expectedScale = device === 'iphone' ? cssPatterns.iphoneScale : cssPatterns.ipadScale;
    if (content.includes(expectedScale)) {
      this.pass(category, `Scale factor: ${expectedScale}`);
    } else {
      this.fail(category, `Scale factor should be ${expectedScale}`);
    }

    // Check notch/camera
    if (device === 'iphone') {
      const notch = specs.notch;
      if (content.includes(`width: ${notch.width}px`) && content.includes(`height: ${notch.height}px`)) {
        this.pass(category, `Notch: ${notch.width}x${notch.height}px`);
      } else {
        this.warn(category, `Notch dimensions may differ`);
      }
    } else {
      const camera = specs.camera;
      if (content.includes('border-radius: 50%') || content.includes('border-radius:50%')) {
        this.pass(category, `Camera: circular (border-radius: 50%)`);
      } else {
        this.warn(category, `Camera style may differ`);
      }
    }
  }

  // 3. Required Elements Validation
  validateRequiredElements() {
    const category = 'Required Elements';
    const elements = this.standards.requiredElements;

    // Check UI Flow Diagram elements
    const diagramPath = path.join(this.projectPath, 'docs/ui-flow-diagram.html');
    if (fs.existsSync(diagramPath)) {
      const content = fs.readFileSync(diagramPath, 'utf8');

      // Check containers
      if (content.includes('flow-container')) {
        this.pass(category, 'flow-container present');
      } else {
        this.fail(category, 'flow-container missing');
      }

      // Count screen-cards
      const screenCardMatches = content.match(/class="[^"]*screen-card[^"]*"/g) || [];
      const screenCount = screenCardMatches.length;
      if (screenCount > 0) {
        this.pass(category, `screen-card count: ${screenCount}`);
      } else {
        this.fail(category, 'No screen-cards found');
      }

      // Check device-frame
      if (content.includes('device-frame')) {
        this.pass(category, 'device-frame present');
      } else {
        this.fail(category, 'device-frame missing');
      }

      // Check device-switcher
      if (content.includes('device-switcher') || content.includes('切換到')) {
        this.pass(category, 'device-switcher present');
      } else {
        this.warn(category, 'device-switcher may be missing');
      }

      // Check zoom-controls
      if (content.includes('zoom') || content.includes('縮放')) {
        this.pass(category, 'zoom-controls present');
      } else {
        this.warn(category, 'zoom-controls may be missing');
      }
    }

    // Check device-preview elements
    const previewPath = path.join(this.projectPath, 'device-preview.html');
    if (fs.existsSync(previewPath)) {
      const content = fs.readFileSync(previewPath, 'utf8');

      // Count screen items in sidebar
      const screenItemMatches = content.match(/class="[^"]*screen-item[^"]*"/g) || [];
      const sidebarCount = screenItemMatches.length;
      if (sidebarCount > 0) {
        this.pass(category, `device-preview sidebar: ${sidebarCount} screen items`);
      } else {
        this.fail(category, 'device-preview sidebar has no screen items');
      }
    }
  }

  // 4. Function Behavior Validation
  validateFunctionBehavior() {
    const category = 'Function Behavior';
    const funcs = this.standards.functions;

    // Check iPhone diagram openScreen function
    const iphoneDiagramPath = path.join(this.projectPath, 'docs/ui-flow-diagram.html');
    if (fs.existsSync(iphoneDiagramPath)) {
      const content = fs.readFileSync(iphoneDiagramPath, 'utf8');

      const pattern = new RegExp(funcs.openScreen.pattern);
      if (pattern.test(content)) {
        this.pass(category, 'openScreen() redirects to device-preview.html');
      } else if (content.includes('device-preview.html')) {
        this.pass(category, 'openScreen() uses device-preview.html');
      } else {
        this.fail(category, 'openScreen() should redirect to device-preview.html');
      }

      // Check device switcher link
      if (content.includes(funcs.deviceSwitcher.iphoneToIpad)) {
        this.pass(category, 'iPhone diagram links to iPad version');
      } else {
        this.warn(category, 'iPhone diagram may not link to iPad version');
      }
    }

    // Check iPad diagram openScreen function
    const ipadDiagramPath = path.join(this.projectPath, 'docs/ui-flow-diagram-ipad.html');
    if (fs.existsSync(ipadDiagramPath)) {
      const content = fs.readFileSync(ipadDiagramPath, 'utf8');

      // Check device switcher link
      if (content.includes(funcs.deviceSwitcher.ipadToIphone)) {
        this.pass(category, 'iPad diagram links to iPhone version');
      } else {
        this.warn(category, 'iPad diagram may not link to iPhone version');
      }
    }

    // Check device-preview URL parameter support
    const previewPath = path.join(this.projectPath, 'device-preview.html');
    if (fs.existsSync(previewPath)) {
      const content = fs.readFileSync(previewPath, 'utf8');

      if (content.includes('URLSearchParams') || content.includes('searchParams')) {
        this.pass(category, 'URL parameters supported (device + screen)');
      } else if (content.includes('device=') && content.includes('screen=')) {
        this.pass(category, 'URL parameters referenced');
      } else {
        this.warn(category, 'URL parameter handling may be incomplete');
      }
    }
  }

  // 5. CSS Consistency Validation
  validateCSSConsistency() {
    const category = 'CSS Consistency';
    const moduleColors = this.standards.moduleColors;
    const modules = Object.keys(moduleColors);

    // Check for module colors in any CSS or HTML file
    let colorsFound = 0;
    let badgesFound = 0;

    const filesToCheck = [
      'docs/ui-flow-diagram.html',
      'docs/ui-flow-diagram-ipad.html',
      'device-preview.html',
      'shared/project-theme.css'
    ];

    let combinedContent = '';
    for (const file of filesToCheck) {
      const filePath = path.join(this.projectPath, file);
      if (fs.existsSync(filePath)) {
        combinedContent += fs.readFileSync(filePath, 'utf8');
      }
    }

    // Check module colors
    for (const module of modules) {
      const color = moduleColors[module];
      if (combinedContent.includes(color)) {
        colorsFound++;
      }
    }

    if (colorsFound >= modules.length * 0.7) {
      this.pass(category, `Module colors defined: ${colorsFound}/${modules.length}`);
    } else if (colorsFound > 0) {
      this.warn(category, `Module colors partially defined: ${colorsFound}/${modules.length}`);
    } else {
      this.fail(category, 'Module colors not defined');
    }

    // Check badge classes
    for (const module of modules) {
      const badgePattern = new RegExp(`badge-${module.toLowerCase()}|badge-${module}`, 'i');
      if (badgePattern.test(combinedContent)) {
        badgesFound++;
      }
    }

    if (badgesFound >= modules.length * 0.7) {
      this.pass(category, `badge-{module} classes: ${badgesFound}/${modules.length}`);
    } else if (badgesFound > 0) {
      this.warn(category, `badge-{module} classes partially defined: ${badgesFound}/${modules.length}`);
    } else {
      this.warn(category, 'badge-{module} classes may use different naming');
    }
  }

  // 6. Diagram No Legend Validation (模組圖例不應出現在 Diagram 內)
  validateDiagramNoLegend() {
    const category = 'Diagram No Legend';

    const diagramFiles = [
      'docs/ui-flow-diagram.html',
      'docs/ui-flow-diagram-ipad.html',
      'docs/ui-flow-diagram-iphone.html'
    ];

    for (const file of diagramFiles) {
      const filePath = path.join(this.projectPath, file);
      if (!fs.existsSync(filePath)) continue;

      const content = fs.readFileSync(filePath, 'utf8');

      // Check for legend sidebar patterns
      const hasLegendDiv = content.includes('<div class="legend">') || content.includes('class="legend"');
      const hasLegendItem = content.includes('legend-item') || content.includes('legend-color');
      const hasModuleCounts = /AUTH\s*\(\d+\)|HOME\s*\(\d+\)|VOCAB\s*\(\d+\)/i.test(content);

      if (hasLegendDiv || hasLegendItem) {
        this.fail(category, `${file} 包含模組圖例 (legend div) - 應移除，由 index.html 提供`);
      } else if (hasModuleCounts) {
        this.warn(category, `${file} 可能包含模組計數 - 請確認是否為重複的圖例`);
      } else {
        this.pass(category, `${file} 無重複模組圖例`);
      }
    }
  }

  // Run all validations
  async validate() {
    console.log();
    console.log('════════════════════════════════════════════════════════════');
    console.log('  UI Flow Consistency Validation');
    console.log(`  Reference: reference-example (v${this.standards.version})`);
    console.log('════════════════════════════════════════════════════════════');
    console.log();

    // Run validations
    this.validateFileStructure();
    this.validateDeviceSpecs('iphone');
    this.validateDeviceSpecs('ipad');
    this.validateRequiredElements();
    this.validateFunctionBehavior();
    this.validateCSSConsistency();
    this.validateDiagramNoLegend();

    // Generate report
    this.generateReport();

    return this.results.failed.length === 0;
  }

  generateReport() {
    const { passed, failed, warnings } = this.results;

    // Group by category
    const categories = {};

    for (const item of [...passed, ...failed, ...warnings]) {
      if (!categories[item.category]) {
        categories[item.category] = { passed: [], failed: [], warnings: [] };
      }
    }

    for (const item of passed) {
      categories[item.category].passed.push(item.message);
    }
    for (const item of failed) {
      categories[item.category].failed.push(item.message);
    }
    for (const item of warnings) {
      categories[item.category].warnings.push(item.message);
    }

    // Print results by category
    let categoryIndex = 1;
    for (const [category, items] of Object.entries(categories)) {
      console.log(`${categoryIndex}️⃣  ${category}`);
      console.log('────────────────────────────────────────────────────────────');

      for (const msg of items.passed) {
        console.log(`${colors.green}✅ ${msg}${colors.reset}`);
      }
      for (const msg of items.warnings) {
        console.log(`${colors.yellow}⚠️  ${msg}${colors.reset}`);
      }
      for (const msg of items.failed) {
        console.log(`${colors.red}❌ ${msg}${colors.reset}`);
      }

      console.log();
      categoryIndex++;
    }

    // Summary
    console.log('════════════════════════════════════════════════════════════');
    console.log(`${colors.bold}📊 CONSISTENCY VALIDATION SUMMARY${colors.reset}`);
    console.log('════════════════════════════════════════════════════════════');
    console.log(`${colors.green}✅ PASSED: ${passed.length}${colors.reset}`);
    console.log(`${colors.yellow}⚠️  WARNINGS: ${warnings.length}${colors.reset}`);
    console.log(`${colors.red}❌ FAILED: ${failed.length}${colors.reset}`);
    console.log();

    if (failed.length === 0) {
      console.log(`${colors.green}${colors.bold}✅ UI FLOW CONSISTENCY VALIDATED${colors.reset}`);
      console.log('   Output matches reference-example standards');
    } else {
      console.log(`${colors.red}${colors.bold}❌ UI FLOW CONSISTENCY CHECK FAILED${colors.reset}`);
      console.log(`   ${failed.length} issue(s) need to be fixed`);
    }
    console.log('════════════════════════════════════════════════════════════');
    console.log();
  }
}

// Main execution
async function main() {
  const projectPath = process.argv[2] || process.cwd();

  console.log(`${colors.cyan}Validating: ${projectPath}${colors.reset}`);

  const validator = new ConsistencyValidator(projectPath);

  if (!validator.loadStandards()) {
    process.exit(1);
  }

  const success = await validator.validate();
  process.exit(success ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
