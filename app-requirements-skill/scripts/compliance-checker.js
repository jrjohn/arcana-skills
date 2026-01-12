#!/usr/bin/env node
/**
 * IEC 62304 Compliance Checker
 *
 * Verifies compliance with all mandatory rules defined in app-requirements-skill:
 *
 * 1. 追溯要求：所有追溯方向必須達到 100% 覆蓋率
 * 2. 文件同步：.md 與 .docx 必須同步
 * 3. UI 圖片：SDD 必須嵌入 UI 設計圖片
 * 4. 圖表格式：所有圖表必須使用 Mermaid 語法
 * 5. 標題編號：MD 檔案禁止包含手動編號
 * 6. SRS 回補強制：UI Flow 回補 SDD 後，必須同時回補 SRS
 * 7. UI Flow 必須產出：SDD 完成後，必須產生 HTML UI Flow
 * 8. 可點擊元素覆蓋：每個可點擊元素必須有對應的目標畫面
 * 9. 需求收集階段 UI 需求：開始需求收集時，必須先啟用 app-uiux-designer.skill 詢問 UI 需求
 *
 * Usage:
 *   node compliance-checker.js [project-dir]
 *
 * Exit codes:
 *   0 - All checks passed
 *   1 - Compliance failures found
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
  planningDir: '01-planning',
  designDir: '02-design',
  uiFlowDir: '04-ui-flow',
  traceabilityDir: '07-traceability'
};

const RULES = [
  { id: 'TRACE-100', name: '追溯覆蓋率 100%', critical: true },
  { id: 'DOC-SYNC', name: '文件同步 (MD/DOCX)', critical: true },
  { id: 'UI-IMAGES', name: 'SDD 嵌入 UI 圖片', critical: true },
  { id: 'MERMAID', name: '圖表使用 Mermaid', critical: false },
  { id: 'NO-MANUAL-NUM', name: '禁止手動編號', critical: false },
  { id: 'SRS-FEEDBACK', name: 'SRS 回補完成', critical: true },
  { id: 'UI-FLOW', name: 'UI Flow 已產出', critical: true },
  { id: 'CLICK-COVER', name: '可點擊元素覆蓋', critical: true }
];

// =============================================================================
// CHECK FUNCTIONS
// =============================================================================

/**
 * Check 1: 追溯覆蓋率 100%
 */
function checkTraceability(projectDir) {
  const result = { passed: true, details: [] };

  // Run verify-traceability.js if exists
  const verifyScript = path.join(__dirname, 'verify-traceability.js');
  if (fs.existsSync(verifyScript)) {
    try {
      execSync(`node "${verifyScript}" "${projectDir}"`, { stdio: 'pipe' });
      result.details.push('Traceability verification passed');
    } catch (error) {
      result.passed = false;
      result.details.push('Traceability verification failed - run verify-traceability.js for details');
    }
  } else {
    // Manual check - look for RTM file
    const rtmDir = path.join(projectDir, CONFIG.traceabilityDir);
    if (!fs.existsSync(rtmDir)) {
      result.passed = false;
      result.details.push('RTM directory not found');
    } else {
      const rtmFiles = fs.readdirSync(rtmDir).filter(f => f.startsWith('RTM-'));
      if (rtmFiles.length === 0) {
        result.passed = false;
        result.details.push('No RTM file found');
      }
    }
  }

  return result;
}

/**
 * Check 2: 文件同步 (MD/DOCX)
 */
function checkDocSync(projectDir) {
  const result = { passed: true, details: [] };
  const dirsToCheck = [CONFIG.planningDir, CONFIG.designDir, CONFIG.traceabilityDir];

  for (const dir of dirsToCheck) {
    const fullPath = path.join(projectDir, dir);
    if (!fs.existsSync(fullPath)) continue;

    const files = fs.readdirSync(fullPath);
    const mdFiles = files.filter(f => f.endsWith('.md') && (f.startsWith('SRS-') || f.startsWith('SDD-') || f.startsWith('RTM-')));

    for (const mdFile of mdFiles) {
      const docxFile = mdFile.replace('.md', '.docx');
      const mdPath = path.join(fullPath, mdFile);
      const docxPath = path.join(fullPath, docxFile);

      if (!fs.existsSync(docxPath)) {
        result.passed = false;
        result.details.push(`Missing DOCX: ${dir}/${docxFile}`);
      } else {
        // Check modification times
        const mdStat = fs.statSync(mdPath);
        const docxStat = fs.statSync(docxPath);

        if (mdStat.mtime > docxStat.mtime) {
          result.passed = false;
          result.details.push(`DOCX outdated: ${dir}/${docxFile} (MD modified after DOCX)`);
        }
      }
    }
  }

  if (result.details.length === 0) {
    result.details.push('All MD/DOCX pairs synchronized');
  }

  return result;
}

/**
 * Check 3: SDD 嵌入 UI 圖片
 */
function checkUiImages(projectDir) {
  const result = { passed: true, details: [] };
  const designDir = path.join(projectDir, CONFIG.designDir);

  if (!fs.existsSync(designDir)) {
    result.details.push('Design directory not found');
    return result;
  }

  const sddFiles = fs.readdirSync(designDir).filter(f => f.startsWith('SDD-') && f.endsWith('.md'));

  for (const sddFile of sddFiles) {
    const sddPath = path.join(designDir, sddFile);
    const content = fs.readFileSync(sddPath, 'utf-8');

    // Check for SCR- sections
    const scrSections = content.match(/##\s+SCR-[A-Z]+-\d+/g) || [];

    if (scrSections.length > 0) {
      // Check for image references
      const imageRefs = content.match(/!\[.*?\]\(.*?\.png\)/g) || [];
      const imagesDir = path.join(designDir, 'images');

      if (imageRefs.length === 0) {
        result.passed = false;
        result.details.push(`${sddFile}: No UI images found (${scrSections.length} screens defined)`);
      } else {
        // Verify images exist
        let missingImages = 0;
        for (const ref of imageRefs) {
          const imagePath = ref.match(/\(([^)]+)\)/)?.[1];
          if (imagePath && !fs.existsSync(path.join(designDir, imagePath))) {
            missingImages++;
          }
        }
        if (missingImages > 0) {
          result.passed = false;
          result.details.push(`${sddFile}: ${missingImages} referenced images not found`);
        }
      }
    }
  }

  if (result.passed) {
    result.details.push('All SDD files have UI images');
  }

  return result;
}

/**
 * Check 4: 圖表使用 Mermaid
 */
function checkMermaid(projectDir) {
  const result = { passed: true, details: [] };
  const dirsToCheck = [CONFIG.planningDir, CONFIG.designDir];

  for (const dir of dirsToCheck) {
    const fullPath = path.join(projectDir, dir);
    if (!fs.existsSync(fullPath)) continue;

    const mdFiles = fs.readdirSync(fullPath).filter(f => f.endsWith('.md'));

    for (const mdFile of mdFiles) {
      const content = fs.readFileSync(path.join(fullPath, mdFile), 'utf-8');

      // Check for ASCII art diagrams (lines with +-|)
      const asciiBoxPattern = /^\s*[+\-|]+[+\-|]+\s*$/gm;
      const asciiMatches = content.match(asciiBoxPattern) || [];

      if (asciiMatches.length > 3) { // Allow some table separators
        result.passed = false;
        result.details.push(`${dir}/${mdFile}: Possible ASCII diagram detected (use Mermaid instead)`);
      }
    }
  }

  if (result.passed) {
    result.details.push('No ASCII diagrams detected');
  }

  return result;
}

/**
 * Check 5: 禁止手動編號
 */
function checkNoManualNumbering(projectDir) {
  const result = { passed: true, details: [] };
  const dirsToCheck = [CONFIG.planningDir, CONFIG.designDir];

  for (const dir of dirsToCheck) {
    const fullPath = path.join(projectDir, dir);
    if (!fs.existsSync(fullPath)) continue;

    const mdFiles = fs.readdirSync(fullPath).filter(f => f.endsWith('.md'));

    for (const mdFile of mdFiles) {
      const content = fs.readFileSync(path.join(fullPath, mdFile), 'utf-8');

      // Check for manually numbered headings (## 1.2.3 Title)
      const manualNumberPattern = /^#{1,6}\s+\d+(\.\d+)*\s+/gm;
      const matches = content.match(manualNumberPattern) || [];

      if (matches.length > 0) {
        result.passed = false;
        result.details.push(`${dir}/${mdFile}: ${matches.length} manually numbered headings`);
      }
    }
  }

  if (result.passed) {
    result.details.push('No manual numbering detected');
  }

  return result;
}

/**
 * Check 6: SRS 回補完成
 */
function checkSrsFeedback(projectDir) {
  const result = { passed: true, details: [] };
  const planningDir = path.join(projectDir, CONFIG.planningDir);

  if (!fs.existsSync(planningDir)) {
    result.details.push('Planning directory not found');
    return result;
  }

  const srsFiles = fs.readdirSync(planningDir).filter(f => f.startsWith('SRS-') && f.endsWith('.md'));

  for (const srsFile of srsFiles) {
    const content = fs.readFileSync(path.join(planningDir, srsFile), 'utf-8');

    // Check for Screen References section
    if (!content.includes('Screen References') && !content.includes('畫面參考')) {
      result.passed = false;
      result.details.push(`${srsFile}: Missing Screen References section`);
    }

    // Check for Inferred Requirements section
    if (!content.includes('Inferred Requirements') && !content.includes('推導需求')) {
      result.passed = false;
      result.details.push(`${srsFile}: Missing Inferred Requirements section`);
    }

    // Check for User Flows section
    if (!content.includes('User Flows') && !content.includes('使用者流程')) {
      result.passed = false;
      result.details.push(`${srsFile}: Missing User Flows section`);
    }
  }

  if (result.passed) {
    result.details.push('SRS feedback sections complete');
  }

  return result;
}

/**
 * Check 7: UI Flow 已產出
 */
function checkUiFlow(projectDir) {
  const result = { passed: true, details: [] };
  const uiFlowDir = path.join(projectDir, CONFIG.uiFlowDir);

  if (!fs.existsSync(uiFlowDir)) {
    result.passed = false;
    result.details.push('UI Flow directory not found');
    return result;
  }

  // Check for required files
  const requiredFiles = ['index.html', 'device-preview.html'];
  for (const file of requiredFiles) {
    if (!fs.existsSync(path.join(uiFlowDir, file))) {
      result.passed = false;
      result.details.push(`Missing: ${file}`);
    }
  }

  // Check for screen HTML files
  const screenDirs = ['auth', 'onboard', 'dash', 'setting'];
  let totalScreens = 0;

  for (const dir of screenDirs) {
    const dirPath = path.join(uiFlowDir, dir);
    if (fs.existsSync(dirPath)) {
      const htmlFiles = fs.readdirSync(dirPath).filter(f => f.endsWith('.html'));
      totalScreens += htmlFiles.length;
    }
  }

  if (totalScreens === 0) {
    result.passed = false;
    result.details.push('No screen HTML files found');
  } else {
    result.details.push(`${totalScreens} screen files found`);
  }

  // Check for screenshots
  const screenshotsDir = path.join(uiFlowDir, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    result.passed = false;
    result.details.push('Screenshots not captured');
  }

  return result;
}

/**
 * Check 8: 可點擊元素覆蓋
 */
function checkClickableCoverage(projectDir) {
  const result = { passed: true, details: [] };
  const uiFlowDir = path.join(projectDir, CONFIG.uiFlowDir);
  const validationReport = path.join(uiFlowDir, 'validation-report.json');

  if (!fs.existsSync(validationReport)) {
    result.passed = false;
    result.details.push('Validation report not found - run capture-screenshots.js');
    return result;
  }

  try {
    const report = JSON.parse(fs.readFileSync(validationReport, 'utf-8'));

    if (report.coverage < 100) {
      result.passed = false;
      result.details.push(`Coverage: ${report.coverage}% (100% required)`);
      result.details.push(`Invalid elements: ${report.invalidElements?.length || 0}`);
    } else {
      result.details.push(`Coverage: ${report.coverage}%`);
    }
  } catch (error) {
    result.passed = false;
    result.details.push('Failed to parse validation report');
  }

  return result;
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  const projectDir = process.argv[2] || process.cwd();

  console.log('\n' + '='.repeat(70));
  console.log('IEC 62304 COMPLIANCE CHECKER');
  console.log('='.repeat(70));
  console.log(`\nProject: ${projectDir}`);
  console.log(`Timestamp: ${new Date().toISOString()}\n`);

  const results = {
    timestamp: new Date().toISOString(),
    projectDir,
    checks: {},
    summary: {
      total: 0,
      passed: 0,
      failed: 0,
      criticalFailed: 0
    }
  };

  // Run all checks
  const checks = [
    { id: 'TRACE-100', fn: checkTraceability },
    { id: 'DOC-SYNC', fn: checkDocSync },
    { id: 'UI-IMAGES', fn: checkUiImages },
    { id: 'MERMAID', fn: checkMermaid },
    { id: 'NO-MANUAL-NUM', fn: checkNoManualNumbering },
    { id: 'SRS-FEEDBACK', fn: checkSrsFeedback },
    { id: 'UI-FLOW', fn: checkUiFlow },
    { id: 'CLICK-COVER', fn: checkClickableCoverage }
  ];

  for (const check of checks) {
    const rule = RULES.find(r => r.id === check.id);
    const result = check.fn(projectDir);

    results.checks[check.id] = {
      name: rule.name,
      critical: rule.critical,
      ...result
    };

    results.summary.total++;
    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
      if (rule.critical) {
        results.summary.criticalFailed++;
      }
    }

    // Print result
    const status = result.passed ? '✓' : '✗';
    const criticalTag = rule.critical ? ' [CRITICAL]' : '';
    console.log(`[${status}] ${rule.name}${criticalTag}`);
    for (const detail of result.details) {
      console.log(`    ${detail}`);
    }
    console.log('');
  }

  // Summary
  console.log('='.repeat(70));
  console.log('SUMMARY');
  console.log('='.repeat(70));
  console.log(`Total checks: ${results.summary.total}`);
  console.log(`Passed: ${results.summary.passed}`);
  console.log(`Failed: ${results.summary.failed}`);
  console.log(`Critical failures: ${results.summary.criticalFailed}`);
  console.log('');

  const overallPassed = results.summary.criticalFailed === 0;
  console.log(`OVERALL: ${overallPassed ? '✓ COMPLIANT' : '✗ NON-COMPLIANT'}`);
  console.log('='.repeat(70) + '\n');

  // Save report
  const reportPath = path.join(projectDir, 'compliance-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`Report saved: ${reportPath}\n`);

  process.exit(overallPassed ? 0 : 1);
}

main();
