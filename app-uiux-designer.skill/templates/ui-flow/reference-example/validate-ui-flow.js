#!/usr/bin/env node
/**
 * UI Flow Diagram Validation Script
 *
 * 驗證 app-uiux-designer.skill 產出的 UI Flow 是否完整
 *
 * 驗證項目：
 * 1. 畫面檔案存在性
 * 2. index.html 模組卡片完整性
 * 3. 畫面連結有效性
 * 4. 覆蓋率計算
 * 5. 模組圖例同步
 *
 * Usage:
 *   node validate-ui-flow.js
 */

const fs = require('fs');
const path = require('path');

// Configuration - Expected screens by module
const EXPECTED_MODULES = {
  'AUTH': {
    count: 4,
    screens: ['SCR-AUTH-001-splash', 'SCR-AUTH-002-login', 'SCR-AUTH-003-register', 'SCR-AUTH-004-forgot-password'],
    color: '#6366F1',
    icon: '🔐'
  },
  'ONBOARD': {
    count: 3,
    screens: ['SCR-ONBOARD-001-welcome', 'SCR-ONBOARD-002-role-select', 'SCR-ONBOARD-003-setup-complete'],
    color: '#8B5CF6',
    icon: '👋'
  },
  'HOME': {
    count: 2,
    screens: ['SCR-HOME-001-student-home', 'SCR-HOME-002-parent-home'],
    color: '#F59E0B',
    icon: '🏠'
  },
  'VOCAB': {
    count: 8,
    screens: ['SCR-VOCAB-001-bank-list', 'SCR-VOCAB-002-bank-detail', 'SCR-VOCAB-003-word-detail', 'SCR-VOCAB-004-add-word', 'SCR-VOCAB-005-import', 'SCR-VOCAB-006-export', 'SCR-VOCAB-007-ocr-scan', 'SCR-VOCAB-008-community'],
    color: '#10B981',
    icon: '📖'
  },
  'TRAIN': {
    count: 10,
    screens: ['SCR-TRAIN-001-mode-select', 'SCR-TRAIN-002-listening', 'SCR-TRAIN-003-listening-result', 'SCR-TRAIN-004-pronunciation', 'SCR-TRAIN-005-pronunciation-result', 'SCR-TRAIN-006-spelling', 'SCR-TRAIN-007-spelling-result', 'SCR-TRAIN-008-sentence-fill', 'SCR-TRAIN-009-matching', 'SCR-TRAIN-010-session-complete'],
    color: '#3B82F6',
    icon: '🎯'
  },
  'REPORT': {
    count: 4,
    screens: ['SCR-REPORT-001-overview', 'SCR-REPORT-002-daily', 'SCR-REPORT-003-weekly', 'SCR-REPORT-004-word-analysis'],
    color: '#EC4899',
    icon: '📊'
  },
  'SETTING': {
    count: 5,
    screens: ['SCR-SETTING-001-main', 'SCR-SETTING-002-tts', 'SCR-SETTING-003-pronunciation', 'SCR-SETTING-004-notification', 'SCR-SETTING-005-account'],
    color: '#64748B',
    icon: '⚙️'
  },
  'PARENT': {
    count: 4,
    screens: ['SCR-PARENT-001-dashboard', 'SCR-PARENT-002-assign-vocab', 'SCR-PARENT-003-child-progress', 'SCR-PARENT-004-sentence-manage'],
    color: '#14B8A6',
    icon: '👨‍👩‍👧'
  },
  'COMMON': {
    count: 2,
    screens: ['SCR-COMMON-001-loading', 'SCR-COMMON-002-error'],
    color: '#78716C',
    icon: '🔧'
  }
};

const TOTAL_EXPECTED = Object.values(EXPECTED_MODULES).reduce((sum, m) => sum + m.count, 0);

// Results
const results = {
  totalExpected: TOTAL_EXPECTED,
  totalFound: 0,
  missingScreens: [],
  extraScreens: [],
  indexHtml: {
    exists: false,
    coverage: null,
    moduleCount: 0,
    screenLinks: 0,
    brokenLinks: [],
    moduleIssues: []
  },
  diagramFiles: {
    main: false,
    ipad: false,
    iphone: false,
    templateVars: []
  },
  modules: {}
};

// Get base directory
const baseDir = process.cwd();

console.log('═'.repeat(60));
console.log('  UI Flow Diagram Validation');
console.log('  app-uiux-designer.skill Validation Script');
console.log('═'.repeat(60));
console.log(`\nBase Directory: ${baseDir}\n`);

// Step 1: Check screen files exist
console.log('─'.repeat(60));
console.log('1️⃣  Screen Files Validation');
console.log('─'.repeat(60));

const moduleDirectories = {
  'AUTH': 'auth',
  'ONBOARD': 'onboard',
  'HOME': 'home',
  'VOCAB': 'vocab',
  'TRAIN': 'train',
  'REPORT': 'report',
  'SETTING': 'setting',
  'PARENT': 'parent',
  'COMMON': 'common'
};

for (const [module, config] of Object.entries(EXPECTED_MODULES)) {
  const dir = moduleDirectories[module];
  const dirPath = path.join(baseDir, dir);

  results.modules[module] = {
    expected: config.count,
    found: 0,
    missing: [],
    files: []
  };

  if (!fs.existsSync(dirPath)) {
    console.log(`❌ ${module}: Directory not found (${dir}/)`);
    results.modules[module].missing = config.screens;
    results.missingScreens.push(...config.screens.map(s => `${dir}/${s}.html`));
    continue;
  }

  for (const screenId of config.screens) {
    const screenPath = path.join(dirPath, `${screenId}.html`);
    if (fs.existsSync(screenPath)) {
      results.modules[module].found++;
      results.modules[module].files.push(screenId);
      results.totalFound++;
    } else {
      results.modules[module].missing.push(screenId);
      results.missingScreens.push(`${dir}/${screenId}.html`);
    }
  }

  const status = results.modules[module].found === config.count ? '✅' : '⚠️';
  console.log(`${status} ${module}: ${results.modules[module].found}/${config.count} screens`);

  if (results.modules[module].missing.length > 0) {
    console.log(`   Missing: ${results.modules[module].missing.join(', ')}`);
  }
}

// Step 2: Check index.html
console.log('\n' + '─'.repeat(60));
console.log('2️⃣  index.html Validation');
console.log('─'.repeat(60));

const indexPath = path.join(baseDir, 'index.html');
if (fs.existsSync(indexPath)) {
  results.indexHtml.exists = true;
  console.log('✅ index.html exists');

  const indexContent = fs.readFileSync(indexPath, 'utf-8');

  // Check coverage percentage
  const coverageMatch = indexContent.match(/覆蓋率<\/p>\s*<p[^>]*>(\d+)%/);
  if (coverageMatch) {
    results.indexHtml.coverage = parseInt(coverageMatch[1]);
    const status = results.indexHtml.coverage === 100 ? '✅' : '⚠️';
    console.log(`${status} Coverage: ${results.indexHtml.coverage}%`);
  } else {
    console.log('⚠️ Coverage percentage not found');
  }

  // Check module cards count
  const moduleCardMatches = indexContent.match(/module-card/g);
  results.indexHtml.moduleCount = moduleCardMatches ? moduleCardMatches.length : 0;
  const expectedModules = Object.keys(EXPECTED_MODULES).length;
  const moduleStatus = results.indexHtml.moduleCount === expectedModules ? '✅' : '⚠️';
  console.log(`${moduleStatus} Module cards: ${results.indexHtml.moduleCount}/${expectedModules}`);

  // Check screen links
  const screenLinkMatches = indexContent.match(/href="[^"]*SCR-[^"]*\.html"/g) || [];
  results.indexHtml.screenLinks = screenLinkMatches.length;
  const linkStatus = results.indexHtml.screenLinks >= TOTAL_EXPECTED ? '✅' : '⚠️';
  console.log(`${linkStatus} Screen links: ${results.indexHtml.screenLinks}/${TOTAL_EXPECTED}`);

  // Check for broken links
  for (const linkMatch of screenLinkMatches) {
    const href = linkMatch.match(/href="([^"]*)"/)[1];
    const linkPath = path.join(baseDir, href);
    if (!fs.existsSync(linkPath)) {
      results.indexHtml.brokenLinks.push(href);
    }
  }

  if (results.indexHtml.brokenLinks.length > 0) {
    console.log(`❌ Broken links: ${results.indexHtml.brokenLinks.length}`);
    results.indexHtml.brokenLinks.forEach(link => console.log(`   - ${link}`));
  } else {
    console.log('✅ All screen links valid');
  }

  // Check for placeholder text
  if (indexContent.includes('尚未產生畫面')) {
    console.log('⚠️ Placeholder text found ("尚未產生畫面")');
    results.indexHtml.moduleIssues.push('Contains placeholder text');
  }

  // Check module legend
  const legendMatches = indexContent.match(/模組圖例[\s\S]*?<\/div>\s*<div class="mt-4/);
  if (legendMatches) {
    const legendModules = (legendMatches[0].match(/[A-Z]+\s*\(\d+\)/g) || []).length;
    const legendStatus = legendModules === expectedModules ? '✅' : '⚠️';
    console.log(`${legendStatus} Module legend: ${legendModules}/${expectedModules} modules`);
  }

} else {
  console.log('❌ index.html not found');
}

// Step 3: Check diagram files
console.log('\n' + '─'.repeat(60));
console.log('3️⃣  UI Flow Diagram Files Validation');
console.log('─'.repeat(60));

const diagramFiles = [
  { name: 'ui-flow-diagram.html', key: 'main', required: true, type: 'iphone' },
  { name: 'ui-flow-diagram-ipad.html', key: 'ipad', required: true, type: 'ipad' },
  { name: 'ui-flow-diagram-iphone.html', key: 'iphone', required: false, type: 'iphone' }
];

for (const { name, key, required, type } of diagramFiles) {
  const filePath = path.join(baseDir, 'docs', name);
  if (fs.existsSync(filePath)) {
    results.diagramFiles[key] = true;
    const content = fs.readFileSync(filePath, 'utf-8');

    // Check for template variables
    const templateVars = content.match(/\{\{[A-Z_]+\}\}/g) || [];
    if (templateVars.length > 0) {
      console.log(`⚠️ ${name}: Contains ${templateVars.length} unresolved template variables`);
      results.diagramFiles.templateVars.push({ file: name, vars: [...new Set(templateVars)] });
    } else {
      // Check for proper flow diagram structure
      const iframeCount = (content.match(/<iframe[^>]*src="[^"]*SCR-[^"]*\.html"/g) || []).length;
      const screenCardCount = (content.match(/class="screen-card/g) || []).length;
      const hasFlowContainer = content.includes('class="flow-container"');

      if (type === 'ipad') {
        // iPad-specific standalone diagram validation
        const checks = [];
        if (iframeCount >= 42) checks.push(`${iframeCount} iframes`);
        else checks.push(`⚠️ ${iframeCount}/42 iframes`);
        if (screenCardCount >= 42) checks.push(`${screenCardCount} screen-cards`);
        else checks.push(`⚠️ ${screenCardCount}/42 screen-cards`);
        if (hasFlowContainer) checks.push('flow-container');
        else checks.push('⚠️ flow-container');

        // iPad template checks (200x140, 1194x834, camera dot)
        const hasiPadWidth = content.includes('width: 200px');
        const hasiPadHeight = content.includes('height: 140px');
        const hasiPadViewport = content.includes('1194px') && content.includes('834px');
        const hasiPadScale = content.includes('scale(0.168)');
        const hasiPadCamera = content.includes('border-radius: 50%') && content.includes('width: 6px');

        if (hasiPadWidth && hasiPadHeight) checks.push('iPad-frame');
        else checks.push('⚠️ iPad-frame');
        if (hasiPadViewport && hasiPadScale) checks.push('iPad-scale');
        else checks.push('⚠️ iPad-scale');
        if (hasiPadCamera) checks.push('camera');
        else checks.push('⚠️ camera');

        // Check for device switcher link to iPhone
        const hasSwitcher = content.includes('device-switcher') && content.includes('ui-flow-diagram.html');
        if (hasSwitcher) checks.push('switcher');

        const valid = iframeCount >= 42 && screenCardCount >= 42 && hasFlowContainer && hasiPadWidth && hasiPadHeight;
        console.log(`${valid ? '✅' : '⚠️'} ${name}: ${checks.join(', ')}`);

      } else if (type === 'iphone') {
        // iPhone-specific diagram validation (main or standalone)
        const checks = [];
        if (iframeCount >= 42) checks.push(`${iframeCount} iframes`);
        else checks.push(`⚠️ ${iframeCount}/42 iframes`);
        if (screenCardCount >= 42) checks.push(`${screenCardCount} screen-cards`);
        else checks.push(`⚠️ ${screenCardCount}/42 screen-cards`);
        if (hasFlowContainer) checks.push('flow-container');
        else checks.push('⚠️ flow-container');

        // iPhone template checks (120x260, 393x852, notch bar)
        const hasiPhoneWidth = content.includes('width: 120px');
        const hasiPhoneHeight = content.includes('height: 260px');
        const hasiPhoneViewport = content.includes('393px') && content.includes('852px');
        const hasiPhoneScale = content.includes('scale(0.305)');
        const hasiPhoneNotch = content.includes('width: 40px') && content.includes('border-radius: 3px');

        if (hasiPhoneWidth && hasiPhoneHeight) checks.push('iPhone-frame');
        else checks.push('⚠️ iPhone-frame');
        if (hasiPhoneViewport && hasiPhoneScale) checks.push('iPhone-scale');
        else checks.push('⚠️ iPhone-scale');
        if (hasiPhoneNotch) checks.push('notch');
        else checks.push('⚠️ notch');

        // Check for device switcher link to iPad (for main file)
        if (key === 'main') {
          const hasSwitcher = content.includes('device-switcher') && content.includes('ui-flow-diagram-ipad.html');
          if (hasSwitcher) checks.push('switcher');
        }

        const valid = iframeCount >= 42 && screenCardCount >= 42 && hasFlowContainer && hasiPhoneWidth && hasiPhoneHeight && hasiPhoneNotch;
        console.log(`${valid ? '✅' : '⚠️'} ${name}: ${checks.join(', ')}`);
      }
    }
  } else {
    if (required) {
      console.log(`❌ ${name}: Not found (REQUIRED)`);
    } else {
      console.log(`ℹ️ ${name}: Not found (optional)`);
    }
  }
}

// Step 4: Check device-preview.html
console.log('\n' + '─'.repeat(60));
console.log('4️⃣  device-preview.html Validation');
console.log('─'.repeat(60));

const previewPath = path.join(baseDir, 'device-preview.html');
if (fs.existsSync(previewPath)) {
  console.log('✅ device-preview.html exists');

  const previewContent = fs.readFileSync(previewPath, 'utf-8');

  // Check sidebar screen items
  const screenItems = (previewContent.match(/screen-item/g) || []).length;
  const sidebarStatus = screenItems >= TOTAL_EXPECTED ? '✅' : '⚠️';
  console.log(`${sidebarStatus} Sidebar screen items: ${screenItems}/${TOTAL_EXPECTED}`);

  // Check for loadScreen functions
  const loadScreenCalls = (previewContent.match(/loadScreen\(/g) || []).length;
  console.log(`   loadScreen calls: ${loadScreenCalls}`);

} else {
  console.log('❌ device-preview.html not found');
}

// Step 5: Check shared resources
console.log('\n' + '─'.repeat(60));
console.log('5️⃣  Shared Resources Validation');
console.log('─'.repeat(60));

const sharedFiles = [
  'shared/project-theme.css',
  'shared/notify-parent.js'
];

for (const file of sharedFiles) {
  const filePath = path.join(baseDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} not found`);
  }
}

// Summary
console.log('\n' + '═'.repeat(60));
console.log('📊 VALIDATION SUMMARY');
console.log('═'.repeat(60));

const screenCoverage = (results.totalFound / TOTAL_EXPECTED * 100).toFixed(1);
console.log(`\nScreen Coverage: ${results.totalFound}/${TOTAL_EXPECTED} (${screenCoverage}%)`);

// Module breakdown
console.log('\nModule Breakdown:');
for (const [module, data] of Object.entries(results.modules)) {
  const icon = EXPECTED_MODULES[module].icon;
  const status = data.found === data.expected ? '✅' : '❌';
  console.log(`  ${status} ${icon} ${module}: ${data.found}/${data.expected}`);
}

// Issues
const issues = [];
if (results.missingScreens.length > 0) {
  issues.push(`${results.missingScreens.length} missing screens`);
}
if (!results.indexHtml.exists) {
  issues.push('index.html missing');
} else if (results.indexHtml.coverage < 100) {
  issues.push(`Coverage shows ${results.indexHtml.coverage}% (should be 100%)`);
}
if (results.indexHtml.brokenLinks.length > 0) {
  issues.push(`${results.indexHtml.brokenLinks.length} broken links in index.html`);
}
if (results.diagramFiles.templateVars.length > 0) {
  issues.push('Unresolved template variables in diagram files');
}

console.log('\n' + '─'.repeat(60));
if (issues.length === 0) {
  console.log('✅ UI FLOW VALIDATION PASSED');
  console.log('   All screens present, index.html valid, no broken links');
} else {
  console.log('⚠️  UI FLOW VALIDATION ISSUES FOUND:');
  issues.forEach((issue, i) => console.log(`   ${i + 1}. ${issue}`));
}
console.log('─'.repeat(60));

// Exit code
process.exit(issues.length === 0 ? 0 : 1);
