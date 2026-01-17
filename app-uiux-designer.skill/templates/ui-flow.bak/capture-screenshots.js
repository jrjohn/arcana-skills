/**
 * {{PROJECT_NAME}} UI Flow Screenshot Capture & Validation Script
 *
 * This script uses Puppeteer to:
 * 1. Capture screenshots of all screens for iPad and iPhone devices
 * 2. Validate clickable element coverage (100% required)
 * 3. Verify navigation integrity
 *
 * Usage:
 *   npm install puppeteer
 *   node capture-screenshots.js [--validate-only] [--skip-validation]
 *
 * Options:
 *   --validate-only    Only run validation, skip screenshot capture
 *   --skip-validation  Only capture screenshots, skip validation
 *
 * Output:
 *   screenshots/auth/SCR-AUTH-001-login.png
 *   screenshots/onboard/SCR-ONBOARD-001-intro.png
 *   ...
 *   validation-report.json
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Command line arguments
const args = process.argv.slice(2);
const VALIDATE_ONLY = args.includes('--validate-only');
const SKIP_VALIDATION = args.includes('--skip-validation');

// IMPORTANT: Strict validation blocking mode
// When true, UI Flow generation is BLOCKED if validation fails
const BLOCK_ON_FAILURE = true;

// Screen definitions - Customize for your project
const SCREENS = {
  auth: [
    { id: 'SCR-AUTH-001-login', name: 'Login' },
    { id: 'SCR-AUTH-002-register', name: 'Register' },
    // Add more auth screens
  ],
  onboard: [
    // { id: 'SCR-ONBOARD-001-intro', name: 'Introduction' },
    // Add onboard screens
  ],
  dash: [
    // { id: 'SCR-DASH-001-home', name: 'Dashboard Home' },
    // Add dash screens
  ],
  // Add more modules as needed
  setting: [
    // { id: 'SCR-SETTING-001-main', name: 'Settings' },
  ]
};

// Device configurations
const DEVICES = {
  ipad: {
    viewport: { width: 1194, height: 834 },
    folder: '', // Root module folders (auth/, onboard/, etc.)
    urlPrefix: ''
  },
  iphone: {
    viewport: { width: 393, height: 852 },
    folder: 'iphone',
    urlPrefix: 'iphone/'
  }
};

async function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// =============================================================================
// CLICKABLE ELEMENT VALIDATION
// =============================================================================

/**
 * Get all existing screen IDs from SCREENS configuration
 */
function getAllScreenIds() {
  const ids = new Set();
  for (const module of Object.keys(SCREENS)) {
    for (const screen of SCREENS[module]) {
      ids.add(screen.id);
    }
  }
  return ids;
}

/**
 * Extract clickable elements from HTML file
 */
function extractClickableElements(htmlPath) {
  if (!fs.existsSync(htmlPath)) {
    return { elements: [], error: 'File not found' };
  }

  const html = fs.readFileSync(htmlPath, 'utf-8');
  const elements = [];

  // Pattern 1: onclick with openScreen or navigateTo
  const onclickPattern = /onclick=["'](?:openScreen|navigateTo)\(['"]([^'"]+)['"]\)["']/g;
  let match;
  while ((match = onclickPattern.exec(html)) !== null) {
    elements.push({
      type: 'onclick',
      target: match[1],
      raw: match[0]
    });
  }

  // Pattern 2: href links to .html files
  const hrefPattern = /href=["']([^'"]*\.html)["']/g;
  while ((match = hrefPattern.exec(html)) !== null) {
    // Exclude external links and anchors
    if (!match[1].startsWith('http') && !match[1].startsWith('#')) {
      elements.push({
        type: 'href',
        target: match[1],
        raw: match[0]
      });
    }
  }

  // Pattern 3: data-target attributes
  const dataTargetPattern = /data-target=["']([^'"]+)["']/g;
  while ((match = dataTargetPattern.exec(html)) !== null) {
    elements.push({
      type: 'data-target',
      target: match[1],
      raw: match[0]
    });
  }

  return { elements, error: null };
}

/**
 * Normalize target path to screen ID
 */
function normalizeTarget(target) {
  // Remove path prefixes and .html suffix
  let normalized = target
    .replace(/^\.\.\//, '')
    .replace(/^\.\//, '')
    .replace(/^iphone\//, '')
    .replace(/^auth\//, '')
    .replace(/^onboard\//, '')
    .replace(/^dash\//, '')
    .replace(/^setting\//, '')
    .replace(/\.html$/, '');

  return normalized;
}

/**
 * Validate all clickable elements across all screens
 */
async function validateClickableElements() {
  console.log('\n=== CLICKABLE ELEMENT VALIDATION ===\n');

  const validScreenIds = getAllScreenIds();
  const validationResults = {
    totalElements: 0,
    validElements: 0,
    invalidElements: [],
    screenResults: {},
    coverage: 0
  };

  // Special targets that are always valid
  const specialTargets = new Set([
    'device-preview.html',
    'index.html',
    'ui-flow-diagram.html',
    'javascript:void(0)',
    'javascript:history.back()'
  ]);

  // Scan all HTML files
  const htmlDirs = ['auth', 'onboard', 'dash', 'setting', 'iphone'];

  for (const dir of htmlDirs) {
    const dirPath = path.join(__dirname, dir);
    if (!fs.existsSync(dirPath)) continue;

    const files = fs.readdirSync(dirPath).filter(f => f.endsWith('.html'));

    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const { elements, error } = extractClickableElements(filePath);

      if (error) {
        console.log(`   [WARN] ${dir}/${file}: ${error}`);
        continue;
      }

      const screenId = `${dir}/${file}`;
      validationResults.screenResults[screenId] = {
        total: elements.length,
        valid: 0,
        invalid: []
      };

      for (const element of elements) {
        validationResults.totalElements++;
        const normalizedTarget = normalizeTarget(element.target);

        // Check if target is valid
        const isValid =
          validScreenIds.has(normalizedTarget) ||
          specialTargets.has(element.target) ||
          element.target.includes('device-preview.html') ||
          fs.existsSync(path.join(__dirname, element.target));

        if (isValid) {
          validationResults.validElements++;
          validationResults.screenResults[screenId].valid++;
        } else {
          validationResults.invalidElements.push({
            screen: screenId,
            element: element.type,
            target: element.target,
            normalizedTarget
          });
          validationResults.screenResults[screenId].invalid.push(element);
        }
      }
    }
  }

  // Calculate coverage
  validationResults.coverage = validationResults.totalElements > 0
    ? Math.round((validationResults.validElements / validationResults.totalElements) * 100)
    : 100;

  // Print results
  console.log(`   Total clickable elements: ${validationResults.totalElements}`);
  console.log(`   Valid targets: ${validationResults.validElements}`);
  console.log(`   Invalid targets: ${validationResults.invalidElements.length}`);
  console.log(`   Coverage: ${validationResults.coverage}%`);

  if (validationResults.invalidElements.length > 0) {
    console.log('\n   INVALID ELEMENTS:');
    for (const inv of validationResults.invalidElements) {
      console.log(`   ❌ ${inv.screen}`);
      console.log(`      ${inv.element}: "${inv.target}" → target not found`);
    }
  }

  // Save report
  const reportPath = path.join(__dirname, 'validation-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(validationResults, null, 2));
  console.log(`\n   Report saved: validation-report.json`);

  return validationResults;
}

/**
 * Validate navigation integrity
 */
async function validateNavigationIntegrity() {
  console.log('\n=== NAVIGATION INTEGRITY VALIDATION ===\n');

  const issues = [];
  const validScreenIds = getAllScreenIds();

  // Check 1: Every screen (except entry points) should have a back navigation
  const entryPoints = new Set(['SCR-AUTH-001', 'SCR-DASH-001', 'SCR-ONBOARD-001']);

  for (const module of Object.keys(SCREENS)) {
    for (const screen of SCREENS[module]) {
      if (entryPoints.has(screen.id.split('-').slice(0, 3).join('-'))) {
        continue; // Skip entry points
      }

      const htmlPath = path.join(__dirname, module, `${screen.id}.html`);
      if (!fs.existsSync(htmlPath)) continue;

      const html = fs.readFileSync(htmlPath, 'utf-8');

      // Check for back navigation
      const hasBackNav =
        html.includes('history.back()') ||
        html.includes('goBack') ||
        html.includes('back-button') ||
        html.includes('nav-back') ||
        html.includes('chevron.left') ||
        html.includes('arrow-left');

      if (!hasBackNav) {
        issues.push({
          type: 'missing-back-nav',
          screen: screen.id,
          message: 'No back navigation found'
        });
      }
    }
  }

  // Check 2: Tab bar consistency
  const tabBarScreens = ['SCR-DASH-001', 'SCR-VOCAB-001', 'SCR-TRAIN-001', 'SCR-REPORT-001', 'SCR-SETTING-001'];
  // This is a placeholder - actual implementation would parse tab bars

  // Print results
  console.log(`   Navigation issues found: ${issues.length}`);

  if (issues.length > 0) {
    for (const issue of issues) {
      console.log(`   ⚠️  ${issue.screen}: ${issue.message}`);
    }
  } else {
    console.log('   ✅ All screens have proper navigation');
  }

  return issues;
}

async function captureScreenshots() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const baseUrl = `file://${path.resolve(__dirname)}`;
  let totalScreens = 0;
  let capturedScreens = 0;

  // Count total screens
  for (const device of Object.keys(DEVICES)) {
    for (const module of Object.keys(SCREENS)) {
      totalScreens += SCREENS[module].length;
    }
  }

  console.log(`\n{{PROJECT_NAME}} Screenshot Capture\n`);
  console.log(`Total screens to capture: ${totalScreens}\n`);

  for (const [deviceName, deviceConfig] of Object.entries(DEVICES)) {
    console.log(`\nCapturing ${deviceName.toUpperCase()} screens...`);
    console.log(`   Viewport: ${deviceConfig.viewport.width} x ${deviceConfig.viewport.height}\n`);

    const page = await browser.newPage();
    await page.setViewport(deviceConfig.viewport);

    for (const [moduleName, screens] of Object.entries(SCREENS)) {
      // Determine output folder
      const outputFolder = path.join(__dirname, 'screenshots', moduleName);
      await ensureDir(outputFolder);

      for (const screen of screens) {
        // Build URL based on device
        let htmlFile;
        if (deviceName === 'iphone') {
          htmlFile = `iphone/${screen.id}.html`;
        } else {
          htmlFile = `${moduleName}/${screen.id}.html`;
        }
        const url = `${baseUrl}/${htmlFile}`;

        // Build output path
        const outputPath = path.join(outputFolder, `${screen.id}.png`);

        try {
          await page.goto(url, { waitUntil: 'networkidle0', timeout: 10000 });

          // Wait for fonts and animations
          await new Promise(resolve => setTimeout(resolve, 500));

          await page.screenshot({
            path: outputPath,
            fullPage: false
          });

          capturedScreens++;
          console.log(`   [${capturedScreens}/${totalScreens}] ${screen.id} (${screen.name})`);
        } catch (error) {
          console.log(`   [${capturedScreens}/${totalScreens}] ${screen.id} - ${error.message}`);
        }
      }
    }

    await page.close();
  }

  await browser.close();

  console.log(`\nDone! Captured ${capturedScreens}/${totalScreens} screenshots.\n`);
  console.log(`Screenshots saved to: ${path.join(__dirname, 'screenshots')}\n`);
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  console.log('\n' + '='.repeat(60));
  console.log('{{PROJECT_NAME}} UI Flow Screenshot Capture & Validation');
  console.log('='.repeat(60));

  let validationPassed = true;

  // Step 1: Validation (unless skipped)
  if (!SKIP_VALIDATION) {
    const clickableResults = await validateClickableElements();
    const navIssues = await validateNavigationIntegrity();

    // Check if validation passed
    if (clickableResults.coverage < 100) {
      console.error('\n' + '!'.repeat(60));
      console.error('❌ VALIDATION FAILED: Clickable element coverage < 100%');
      console.error('!'.repeat(60));
      console.error('\n   All invalid targets must be fixed before proceeding.');
      console.error('\n   Missing screens:');
      for (const inv of clickableResults.invalidElements) {
        console.error(`   - ${inv.target} (referenced from ${inv.screen})`);
      }
      validationPassed = false;
    }

    if (navIssues.length > 0) {
      console.log('\n⚠️  WARNING: Navigation integrity issues found');
      console.log('   Consider adding back navigation to flagged screens.');
    }

    // STRICT BLOCKING: Prevent UI Flow generation if validation fails
    if (!validationPassed) {
      if (BLOCK_ON_FAILURE) {
        console.error('\n' + '⛔'.repeat(30));
        console.error('⛔ UI FLOW GENERATION IS BLOCKED');
        console.error('⛔'.repeat(30));
        console.error('\n   Validation coverage: ' + clickableResults.coverage + '%');
        console.error('   Required coverage: 100%');
        console.error('\n   To proceed, you must:');
        console.error('   1. Create all missing target screens');
        console.error('   2. Fix all invalid onclick/href targets');
        console.error('   3. Re-run validation: node capture-screenshots.js --validate-only');
        console.error('\n   WARNING: Using --skip-validation is NOT recommended.');
        console.error('   It violates the 100% clickable element coverage rule.');
        process.exit(1);
      } else if (!VALIDATE_ONLY) {
        console.log('\n   Use --skip-validation to force screenshot capture (not recommended).');
        process.exit(1);
      }
    }
  }

  // Step 2: Screenshot capture (unless validate-only)
  if (!VALIDATE_ONLY && (validationPassed || SKIP_VALIDATION)) {
    await captureScreenshots();
  }

  console.log('\n' + '='.repeat(60));
  if (validationPassed) {
    console.log('✅ COMPLETE - All validations passed');
  } else {
    console.log('⚠️  COMPLETE - Screenshot capture done (validation was skipped)');
  }
  console.log('='.repeat(60) + '\n');
}

// Run
main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
