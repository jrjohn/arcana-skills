#!/usr/bin/env node
/**
 * IEC 62304 Traceability Verification Tool
 *
 * Verifies 100% traceability coverage across:
 * - SRS (Software Requirements Specification)
 * - SDD (Software Design Document)
 * - RTM (Requirements Traceability Matrix)
 * - UI Flow (Screen implementations)
 *
 * Usage:
 *   node verify-traceability.js [project-dir]
 *
 * Exit codes:
 *   0 - All verifications passed
 *   1 - Verification failures found
 */

const fs = require('fs');
const path = require('path');

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
  srsPattern: /SRS-.*\.md$/,
  sddPattern: /SDD-.*\.md$/,
  rtmPattern: /RTM-.*\.md$/,
  reqPattern: /REQ-[A-Z]+-\d+/g,
  scrPattern: /SCR-[A-Z]+-\d+(-[a-z-]+)?/g,
  planningDir: '01-planning',
  designDir: '02-design',
  uiFlowDir: '04-ui-flow',
  traceabilityDir: '07-traceability'
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function findFile(dir, pattern) {
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir);
  const match = files.find(f => pattern.test(f));
  return match ? path.join(dir, match) : null;
}

function extractIds(content, pattern) {
  const matches = content.match(pattern) || [];
  return [...new Set(matches)];
}

function readFileContent(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return '';
  return fs.readFileSync(filePath, 'utf-8');
}

// =============================================================================
// EXTRACTION FUNCTIONS
// =============================================================================

function extractSrsRequirements(projectDir) {
  const srsPath = findFile(path.join(projectDir, CONFIG.planningDir), CONFIG.srsPattern);
  const content = readFileContent(srsPath);
  return {
    path: srsPath,
    requirements: extractIds(content, CONFIG.reqPattern),
    screens: extractIds(content, CONFIG.scrPattern)
  };
}

function extractSddDesigns(projectDir) {
  const sddPath = findFile(path.join(projectDir, CONFIG.designDir), CONFIG.sddPattern);
  const content = readFileContent(sddPath);
  return {
    path: sddPath,
    requirements: extractIds(content, CONFIG.reqPattern),
    screens: extractIds(content, CONFIG.scrPattern)
  };
}

function extractRtmMappings(projectDir) {
  const rtmPath = findFile(path.join(projectDir, CONFIG.traceabilityDir), CONFIG.rtmPattern);
  const content = readFileContent(rtmPath);

  // Extract REQ -> SCR mappings from RTM tables
  const mappings = {
    reqToScr: new Map(),
    scrToReq: new Map()
  };

  // Parse table rows (| REQ-XXX | SCR-XXX | ... |)
  const tableRowPattern = /\|\s*(REQ-[A-Z]+-\d+)\s*\|[^|]*\|\s*(SCR-[A-Z]+-\d+[^|]*)/g;
  let match;
  while ((match = tableRowPattern.exec(content)) !== null) {
    const req = match[1];
    const scr = match[2].trim();

    if (!mappings.reqToScr.has(req)) {
      mappings.reqToScr.set(req, []);
    }
    mappings.reqToScr.get(req).push(scr);

    if (!mappings.scrToReq.has(scr)) {
      mappings.scrToReq.set(scr, []);
    }
    mappings.scrToReq.get(scr).push(req);
  }

  return {
    path: rtmPath,
    requirements: extractIds(content, CONFIG.reqPattern),
    screens: extractIds(content, CONFIG.scrPattern),
    mappings
  };
}

function extractUiFlowScreens(projectDir) {
  const uiFlowDir = path.join(projectDir, CONFIG.uiFlowDir);
  const screens = [];

  if (!fs.existsSync(uiFlowDir)) return { screens: [] };

  const scanDir = (dir, prefix = '') => {
    if (!fs.existsSync(dir)) return;
    const items = fs.readdirSync(dir, { withFileTypes: true });

    for (const item of items) {
      if (item.isDirectory() && !['node_modules', 'shared', 'docs', 'screenshots'].includes(item.name)) {
        scanDir(path.join(dir, item.name), item.name);
      } else if (item.isFile() && item.name.endsWith('.html') && item.name.startsWith('SCR-')) {
        const screenId = item.name.replace('.html', '');
        screens.push({
          id: screenId,
          path: path.join(dir, item.name),
          module: prefix || 'root'
        });
      }
    }
  };

  scanDir(uiFlowDir);
  return { screens };
}

// =============================================================================
// VERIFICATION FUNCTIONS
// =============================================================================

function verifySrsToSdd(srs, sdd) {
  const results = {
    passed: true,
    coverage: 0,
    missing: [],
    extra: []
  };

  // Check all SRS requirements are in SDD
  for (const req of srs.requirements) {
    if (!sdd.requirements.includes(req)) {
      results.missing.push(req);
      results.passed = false;
    }
  }

  // Check for extra requirements in SDD not in SRS
  for (const req of sdd.requirements) {
    if (!srs.requirements.includes(req)) {
      results.extra.push(req);
    }
  }

  results.coverage = srs.requirements.length > 0
    ? Math.round(((srs.requirements.length - results.missing.length) / srs.requirements.length) * 100)
    : 100;

  return results;
}

function verifySddToUiFlow(sdd, uiFlow) {
  const results = {
    passed: true,
    coverage: 0,
    missing: [],
    extra: []
  };

  const uiFlowScreenIds = uiFlow.screens.map(s => s.id);

  // Check all SDD screens have UI Flow implementations
  for (const scr of sdd.screens) {
    // Normalize screen ID for comparison
    const normalizedScr = scr.replace(/-[a-z-]+$/, '');
    const found = uiFlowScreenIds.some(id =>
      id === scr || id.startsWith(normalizedScr)
    );

    if (!found) {
      results.missing.push(scr);
      results.passed = false;
    }
  }

  results.coverage = sdd.screens.length > 0
    ? Math.round(((sdd.screens.length - results.missing.length) / sdd.screens.length) * 100)
    : 100;

  return results;
}

function verifyRtmCompleteness(srs, sdd, rtm) {
  const results = {
    passed: true,
    coverage: 0,
    unmappedRequirements: [],
    unmappedScreens: []
  };

  // Check all SRS requirements are in RTM
  for (const req of srs.requirements) {
    if (!rtm.requirements.includes(req)) {
      results.unmappedRequirements.push(req);
      results.passed = false;
    }
  }

  // Check all SDD screens are in RTM
  for (const scr of sdd.screens) {
    if (!rtm.screens.includes(scr)) {
      results.unmappedScreens.push(scr);
      results.passed = false;
    }
  }

  const totalItems = srs.requirements.length + sdd.screens.length;
  const missingItems = results.unmappedRequirements.length + results.unmappedScreens.length;

  results.coverage = totalItems > 0
    ? Math.round(((totalItems - missingItems) / totalItems) * 100)
    : 100;

  return results;
}

// =============================================================================
// REPORT GENERATION
// =============================================================================

function generateReport(projectDir, srs, sdd, rtm, uiFlow, verifications) {
  const report = {
    timestamp: new Date().toISOString(),
    projectDir,
    files: {
      srs: srs.path,
      sdd: sdd.path,
      rtm: rtm.path
    },
    counts: {
      srsRequirements: srs.requirements.length,
      sddRequirements: sdd.requirements.length,
      sddScreens: sdd.screens.length,
      uiFlowScreens: uiFlow.screens.length,
      rtmRequirements: rtm.requirements.length,
      rtmScreens: rtm.screens.length
    },
    verifications,
    overallPassed: Object.values(verifications).every(v => v.passed),
    overallCoverage: Math.round(
      Object.values(verifications).reduce((sum, v) => sum + v.coverage, 0) /
      Object.keys(verifications).length
    )
  };

  return report;
}

function printReport(report) {
  console.log('\n' + '='.repeat(70));
  console.log('IEC 62304 TRACEABILITY VERIFICATION REPORT');
  console.log('='.repeat(70));
  console.log(`\nTimestamp: ${report.timestamp}`);
  console.log(`Project: ${report.projectDir}`);

  console.log('\n--- FILES ---');
  console.log(`SRS: ${report.files.srs || 'NOT FOUND'}`);
  console.log(`SDD: ${report.files.sdd || 'NOT FOUND'}`);
  console.log(`RTM: ${report.files.rtm || 'NOT FOUND'}`);

  console.log('\n--- COUNTS ---');
  console.log(`SRS Requirements: ${report.counts.srsRequirements}`);
  console.log(`SDD Requirements: ${report.counts.sddRequirements}`);
  console.log(`SDD Screens: ${report.counts.sddScreens}`);
  console.log(`UI Flow Screens: ${report.counts.uiFlowScreens}`);

  console.log('\n--- VERIFICATIONS ---');

  // SRS → SDD
  const srsToSdd = report.verifications.srsToSdd;
  console.log(`\n[${srsToSdd.passed ? '✓' : '✗'}] SRS → SDD Coverage: ${srsToSdd.coverage}%`);
  if (srsToSdd.missing.length > 0) {
    console.log(`    Missing in SDD: ${srsToSdd.missing.join(', ')}`);
  }

  // SDD → UI Flow
  const sddToUiFlow = report.verifications.sddToUiFlow;
  console.log(`\n[${sddToUiFlow.passed ? '✓' : '✗'}] SDD → UI Flow Coverage: ${sddToUiFlow.coverage}%`);
  if (sddToUiFlow.missing.length > 0) {
    console.log(`    Missing screens: ${sddToUiFlow.missing.join(', ')}`);
  }

  // RTM Completeness
  const rtmComplete = report.verifications.rtmCompleteness;
  console.log(`\n[${rtmComplete.passed ? '✓' : '✗'}] RTM Completeness: ${rtmComplete.coverage}%`);
  if (rtmComplete.unmappedRequirements.length > 0) {
    console.log(`    Unmapped requirements: ${rtmComplete.unmappedRequirements.join(', ')}`);
  }
  if (rtmComplete.unmappedScreens.length > 0) {
    console.log(`    Unmapped screens: ${rtmComplete.unmappedScreens.join(', ')}`);
  }

  console.log('\n' + '='.repeat(70));
  console.log(`OVERALL: ${report.overallPassed ? '✓ PASSED' : '✗ FAILED'} (${report.overallCoverage}% coverage)`);
  console.log('='.repeat(70) + '\n');

  return report.overallPassed;
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  const projectDir = process.argv[2] || process.cwd();

  console.log('\nVerifying traceability in:', projectDir);

  // Extract data from all sources
  const srs = extractSrsRequirements(projectDir);
  const sdd = extractSddDesigns(projectDir);
  const rtm = extractRtmMappings(projectDir);
  const uiFlow = extractUiFlowScreens(projectDir);

  // Run verifications
  const verifications = {
    srsToSdd: verifySrsToSdd(srs, sdd),
    sddToUiFlow: verifySddToUiFlow(sdd, uiFlow),
    rtmCompleteness: verifyRtmCompleteness(srs, sdd, rtm)
  };

  // Generate and print report
  const report = generateReport(projectDir, srs, sdd, rtm, uiFlow, verifications);
  const passed = printReport(report);

  // Save report as JSON
  const reportPath = path.join(projectDir, 'traceability-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`Report saved: ${reportPath}\n`);

  // Exit with appropriate code
  process.exit(passed ? 0 : 1);
}

main();
