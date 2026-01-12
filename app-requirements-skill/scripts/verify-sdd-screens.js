#!/usr/bin/env node
/**
 * SDD Screen Coverage Verification Script
 *
 * Verifies that all screens in UI Flow are documented in SDD.
 *
 * Usage:
 *   node verify-sdd-screens.js [project-dir]
 *
 * Checks:
 *   1. UI Flow screens (04-ui-flow/) vs SDD screens (02-design/SDD-*.md)
 *   2. Screenshots exist for all screens
 *   3. Button Navigation tables exist for all screens
 */

const fs = require('fs');
const path = require('path');

// Default project directory
const projectDir = process.argv[2] || process.cwd();

/**
 * Get all SCR IDs from UI Flow HTML files
 */
function getUIFlowScreens(uiFlowDir) {
  const screens = new Map();
  const modules = ['auth', 'vocab', 'train', 'home', 'report', 'setting', 'onboard', 'dash'];

  for (const module of modules) {
    const moduleDir = path.join(uiFlowDir, module);
    if (!fs.existsSync(moduleDir)) continue;

    const files = fs.readdirSync(moduleDir).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
    for (const file of files) {
      const scrId = file.replace('.html', '');
      screens.set(scrId, { module, file, inSDD: false, hasScreenshot: false, hasNavTable: false });
    }
  }

  // Also check iphone directory
  const iphoneDir = path.join(uiFlowDir, 'iphone');
  if (fs.existsSync(iphoneDir)) {
    const files = fs.readdirSync(iphoneDir).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
    // Don't add duplicates, just note iPhone versions exist
  }

  return screens;
}

/**
 * Get all SCR sections from SDD markdown file
 */
function getSDDScreens(sddPath) {
  if (!fs.existsSync(sddPath)) return new Set();

  const content = fs.readFileSync(sddPath, 'utf-8');
  const screens = new Set();

  // Match ### SCR-xxx patterns
  const regex = /^### (SCR-[A-Z]+-\d+[a-z]?)(?:-[\w-]+)?/gm;
  let match;
  while ((match = regex.exec(content)) !== null) {
    screens.add(match[1]);
  }

  return screens;
}

/**
 * Check if screenshots exist
 */
function checkScreenshots(imagesDir, screens) {
  if (!fs.existsSync(imagesDir)) return;

  const modules = fs.readdirSync(imagesDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  for (const module of modules) {
    const moduleDir = path.join(imagesDir, module);
    const files = fs.readdirSync(moduleDir).filter(f => f.endsWith('.png'));

    for (const file of files) {
      const scrId = file.replace('.png', '').replace(/-[\w]+$/, ''); // SCR-AUTH-001-login.png -> SCR-AUTH-001
      // Find matching screen
      for (const [id, info] of screens) {
        if (id.startsWith(scrId) || scrId.startsWith(id.split('-').slice(0,3).join('-'))) {
          info.hasScreenshot = true;
        }
      }
    }
  }
}

/**
 * Check if Button Navigation tables exist in SDD
 */
function checkNavTables(sddPath, screens) {
  if (!fs.existsSync(sddPath)) return;

  const content = fs.readFileSync(sddPath, 'utf-8');

  for (const [scrId, info] of screens) {
    // Check if there's a Button Navigation table after the SCR section
    const scrPattern = new RegExp(`### ${scrId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[\\s\\S]*?\\*\\*按鈕導航`, 'i');
    if (scrPattern.test(content)) {
      info.hasNavTable = true;
    }
  }
}

/**
 * Main verification
 */
function main() {
  console.log('\n=== SDD Screen Coverage Verification ===\n');
  console.log(`Project: ${projectDir}\n`);

  const uiFlowDir = path.join(projectDir, '04-ui-flow');
  const designDir = path.join(projectDir, '02-design');
  const imagesDir = path.join(designDir, 'images');

  // Find SDD file
  let sddPath = null;
  if (fs.existsSync(designDir)) {
    const sddFiles = fs.readdirSync(designDir).filter(f => f.startsWith('SDD-') && f.endsWith('.md'));
    if (sddFiles.length > 0) {
      sddPath = path.join(designDir, sddFiles[0]);
    }
  }

  if (!sddPath) {
    console.error('ERROR: SDD file not found in 02-design/');
    process.exit(1);
  }

  console.log(`SDD File: ${path.basename(sddPath)}`);
  console.log(`UI Flow Dir: ${uiFlowDir}\n`);

  // Get screens from both sources
  const uiScreens = getUIFlowScreens(uiFlowDir);
  const sddScreens = getSDDScreens(sddPath);

  // Mark screens found in SDD
  for (const [scrId, info] of uiScreens) {
    // Check various ID formats
    const baseId = scrId.split('-').slice(0, 3).join('-');
    if (sddScreens.has(scrId) || sddScreens.has(baseId)) {
      info.inSDD = true;
    }
  }

  // Check screenshots and nav tables
  checkScreenshots(imagesDir, uiScreens);
  checkNavTables(sddPath, uiScreens);

  // Generate report
  console.log('--- Screen Coverage Report ---\n');

  const moduleStats = {};
  let totalUI = 0;
  let totalSDD = 0;
  let totalScreenshot = 0;
  let totalNavTable = 0;
  const missing = [];
  const noScreenshot = [];
  const noNavTable = [];

  for (const [scrId, info] of uiScreens) {
    totalUI++;
    if (info.inSDD) totalSDD++;
    if (info.hasScreenshot) totalScreenshot++;
    if (info.hasNavTable) totalNavTable++;

    if (!info.inSDD) missing.push(scrId);
    if (!info.hasScreenshot) noScreenshot.push(scrId);
    if (!info.hasNavTable) noNavTable.push(scrId);

    // Module stats
    const module = info.module.toUpperCase();
    if (!moduleStats[module]) {
      moduleStats[module] = { ui: 0, sdd: 0 };
    }
    moduleStats[module].ui++;
    if (info.inSDD) moduleStats[module].sdd++;
  }

  // Print module summary
  console.log('Module Summary:');
  console.log('| Module | UI Flow | SDD | Coverage |');
  console.log('|--------|---------|-----|----------|');
  for (const [module, stats] of Object.entries(moduleStats).sort()) {
    const coverage = stats.ui > 0 ? Math.round(stats.sdd / stats.ui * 100) : 100;
    const status = coverage === 100 ? '✅' : '❌';
    console.log(`| ${module.padEnd(6)} | ${String(stats.ui).padEnd(7)} | ${String(stats.sdd).padEnd(3)} | ${status} ${coverage}% |`);
  }

  console.log('\n--- Overall Statistics ---\n');
  console.log(`UI Flow Screens:     ${totalUI}`);
  console.log(`SDD Documented:      ${totalSDD}`);
  console.log(`With Screenshots:    ${totalScreenshot}`);
  console.log(`With Nav Tables:     ${totalNavTable}`);
  console.log(`Coverage:            ${Math.round(totalSDD/totalUI*100)}%`);

  // List missing screens
  if (missing.length > 0) {
    console.log('\n--- Missing from SDD ---\n');
    for (const scrId of missing.sort()) {
      console.log(`  ❌ ${scrId}`);
    }
  }

  // Final status
  console.log('\n--- Verification Result ---\n');
  if (totalSDD === totalUI && totalScreenshot === totalUI) {
    console.log('✅ PASSED: All screens documented with screenshots');
    process.exit(0);
  } else {
    console.log('❌ FAILED: Screen coverage incomplete');
    console.log(`   Missing from SDD: ${missing.length}`);
    console.log(`   Missing screenshots: ${noScreenshot.length}`);
    process.exit(1);
  }
}

main();
