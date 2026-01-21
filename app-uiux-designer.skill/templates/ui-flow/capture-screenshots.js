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
const RETRY_FAILED = args.includes('--retry-failed');
const PROJECT_PATH = args.find(a => !a.startsWith('--')) || process.cwd();

// IMPORTANT: Strict validation blocking mode
// When true, UI Flow generation is BLOCKED if validation fails
const BLOCK_ON_FAILURE = true;

// Error Recovery Configuration
const ERROR_LOG_FILE = 'workspace/screenshot-error-log.json';
const MAX_RETRIES = 3;

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

async function captureScreenshots(basePath, screensToCapture, retryOnly = false) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const baseUrl = `file://${path.resolve(basePath)}`;
  let totalScreens = 0;
  let capturedScreens = 0;
  let failedScreens = 0;

  // Use discovered screens or predefined SCREENS
  const screens = screensToCapture || discoverScreens(basePath);

  // Load error log for retry mode
  const errorLog = loadErrorLog();
  const failedScreenIds = new Set(errorLog.errors.map(e => `${e.device}/${e.screenId}`));

  // Count total screens
  for (const device of Object.keys(DEVICES)) {
    for (const module of Object.keys(screens)) {
      if (screens[module]) {
        if (retryOnly) {
          totalScreens += screens[module].filter(s => failedScreenIds.has(`${device}/${s.id}`)).length;
        } else {
          totalScreens += screens[module].length;
        }
      }
    }
  }

  if (totalScreens === 0) {
    console.log('\n   No screens to capture.');
    await browser.close();
    return { captured: 0, failed: 0 };
  }

  console.log(`\n   Screenshot Capture\n`);
  console.log(`   Total screens to capture: ${totalScreens}\n`);

  // Reset error log for new run
  if (!retryOnly) {
    errorLog.errors = [];
  }
  errorLog.lastRun = new Date().toISOString();

  for (const [deviceName, deviceConfig] of Object.entries(DEVICES)) {
    console.log(`\n   Capturing ${deviceName.toUpperCase()} screens...`);
    console.log(`   Viewport: ${deviceConfig.viewport.width} x ${deviceConfig.viewport.height}\n`);

    const page = await browser.newPage();
    await page.setViewport(deviceConfig.viewport);

    for (const [moduleName, moduleScreens] of Object.entries(screens)) {
      if (!moduleScreens) continue;

      // Determine output folder
      const outputFolder = path.join(basePath, 'screenshots', deviceName);
      await ensureDir(outputFolder);

      for (const screen of moduleScreens) {
        const screenKey = `${deviceName}/${screen.id}`;

        // Skip if retry mode and this wasn't a failed screen
        if (retryOnly && !failedScreenIds.has(screenKey)) {
          continue;
        }

        // Build URL based on device
        let htmlFile;
        if (deviceName === 'iphone') {
          htmlFile = `iphone/${screen.id}.html`;
        } else {
          htmlFile = `${moduleName}/${screen.id}.html`;
        }

        const fullHtmlPath = path.join(basePath, htmlFile);

        // Check if file exists before trying to capture
        if (!fs.existsSync(fullHtmlPath)) {
          failedScreens++;
          recordError(errorLog, screen.id, deviceName, 'HTML file not found', fullHtmlPath);
          console.log(`   ❌ [${capturedScreens + failedScreens}/${totalScreens}] ${screen.id} - FILE NOT FOUND`);
          continue;
        }

        const url = `${baseUrl}/${htmlFile}`;

        // Build output path
        const outputPath = path.join(outputFolder, `${screen.id}.png`);

        let retryCount = 0;
        let success = false;

        while (retryCount < MAX_RETRIES && !success) {
          try {
            await page.goto(url, { waitUntil: 'networkidle0', timeout: 15000 });

            // Wait for fonts and animations
            await new Promise(resolve => setTimeout(resolve, 500));

            await page.screenshot({
              path: outputPath,
              fullPage: false
            });

            capturedScreens++;
            success = true;
            console.log(`   ✅ [${capturedScreens + failedScreens}/${totalScreens}] ${screen.id}`);
          } catch (error) {
            retryCount++;
            if (retryCount >= MAX_RETRIES) {
              failedScreens++;
              recordError(errorLog, screen.id, deviceName, error.message, fullHtmlPath);
              console.log(`   ❌ [${capturedScreens + failedScreens}/${totalScreens}] ${screen.id} - ${error.message}`);
            } else {
              console.log(`   ⚠️  ${screen.id} - Retry ${retryCount}/${MAX_RETRIES}...`);
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
          }
        }
      }
    }

    await page.close();
  }

  await browser.close();

  // Save error log
  saveErrorLog(errorLog);

  console.log(`\n   Done!`);
  console.log(`   ✅ Captured: ${capturedScreens}`);
  console.log(`   ❌ Failed: ${failedScreens}`);
  console.log(`   📁 Output: ${path.join(basePath, 'screenshots')}`);

  if (failedScreens > 0) {
    console.log(`\n   ⚠️ Error log saved to: ${ERROR_LOG_FILE}`);
    console.log(`   📌 To retry failed screens: node capture-screenshots.js --retry-failed ${basePath}`);
  }

  return { captured: capturedScreens, failed: failedScreens, errorLog };
}

// =============================================================================
// ERROR RECOVERY SYSTEM
// =============================================================================

/**
 * Load error log from previous run
 */
function loadErrorLog() {
  const logPath = path.join(PROJECT_PATH, ERROR_LOG_FILE);
  if (fs.existsSync(logPath)) {
    try {
      return JSON.parse(fs.readFileSync(logPath, 'utf-8'));
    } catch (e) {
      return { errors: [], lastRun: null };
    }
  }
  return { errors: [], lastRun: null };
}

/**
 * Save error log
 */
function saveErrorLog(errorLog) {
  const logPath = path.join(PROJECT_PATH, ERROR_LOG_FILE);
  const workspaceDir = path.dirname(logPath);
  if (!fs.existsSync(workspaceDir)) {
    fs.mkdirSync(workspaceDir, { recursive: true });
  }
  fs.writeFileSync(logPath, JSON.stringify(errorLog, null, 2));
}

/**
 * Record a screenshot error
 */
function recordError(errorLog, screenId, device, errorMessage, htmlPath) {
  errorLog.errors.push({
    screenId,
    device,
    error: errorMessage,
    htmlPath,
    timestamp: new Date().toISOString(),
    success: false,
    retryCount: 0
  });
}

/**
 * Auto-discover all screens from file system
 */
function discoverScreens(basePath) {
  const screens = {};
  const moduleDirs = ['auth', 'common', 'dash', 'home', 'onboard', 'parent', 'profile', 'progress', 'report', 'setting', 'train', 'vocab', 'feature', 'engage'];

  for (const module of moduleDirs) {
    const modulePath = path.join(basePath, module);
    if (fs.existsSync(modulePath)) {
      const files = fs.readdirSync(modulePath).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
      if (files.length > 0) {
        screens[module] = files.map(f => ({
          id: f.replace('.html', ''),
          name: f.replace('.html', '').split('-').slice(2).join('-')
        }));
      }
    }
  }

  return screens;
}

/**
 * Pre-validation: Check all HTML files exist before taking screenshots
 */
async function preValidateScreens(basePath) {
  console.log('\n=== PRE-VALIDATION: Screen File Check ===\n');

  const screens = discoverScreens(basePath);
  const errors = [];
  let totalScreens = 0;
  let existingScreens = 0;

  for (const [module, moduleScreens] of Object.entries(screens)) {
    for (const screen of moduleScreens) {
      totalScreens++;

      // Check iPad version
      const ipadPath = path.join(basePath, module, `${screen.id}.html`);
      if (fs.existsSync(ipadPath)) {
        existingScreens++;
      } else {
        errors.push({
          screenId: screen.id,
          device: 'ipad',
          path: ipadPath,
          error: 'File not found'
        });
      }

      // Check iPhone version
      const iphonePath = path.join(basePath, 'iphone', `${screen.id}.html`);
      if (!fs.existsSync(iphonePath)) {
        errors.push({
          screenId: screen.id,
          device: 'iphone',
          path: iphonePath,
          error: 'iPhone version not found'
        });
      }
    }
  }

  console.log(`   Total screens: ${totalScreens}`);
  console.log(`   Existing iPad files: ${existingScreens}`);
  console.log(`   Missing files: ${errors.length}`);

  if (errors.length > 0) {
    console.log('\n   Missing files:');
    const uniqueErrors = [...new Set(errors.map(e => `${e.device}/${e.screenId}`))];
    uniqueErrors.slice(0, 10).forEach(e => console.log(`   - ${e}`));
    if (uniqueErrors.length > 10) {
      console.log(`   ... and ${uniqueErrors.length - 10} more`);
    }
  }

  return { screens, errors, totalScreens, existingScreens };
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  const basePath = PROJECT_PATH;

  console.log('\n' + '='.repeat(60));
  console.log('  UI Flow Screenshot Capture & Validation');
  console.log('  with Error Recovery Support');
  console.log('='.repeat(60));
  console.log(`\n   Project: ${basePath}`);

  let validationPassed = true;

  // Handle retry mode
  if (RETRY_FAILED) {
    console.log('\n   Mode: RETRY FAILED SCREENSHOTS');
    const errorLog = loadErrorLog();
    if (errorLog.errors.length === 0) {
      console.log('   No failed screenshots to retry.');
      process.exit(0);
    }
    console.log(`   Retrying ${errorLog.errors.length} failed screenshot(s)...`);
    const screens = discoverScreens(basePath);
    const result = await captureScreenshots(basePath, screens, true);
    process.exit(result.failed > 0 ? 1 : 0);
  }

  // Step 0: Pre-validation - check all HTML files exist
  const preValidation = await preValidateScreens(basePath);
  if (preValidation.errors.length > 0) {
    console.log('\n   ⚠️ Some screen files are missing.');
    console.log('   Screenshot capture may fail for missing files.');
    console.log('   Consider returning to 03-generation to create missing screens.');
  }

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
      for (const inv of clickableResults.invalidElements.slice(0, 10)) {
        console.error(`   - ${inv.target} (referenced from ${inv.screen})`);
      }
      if (clickableResults.invalidElements.length > 10) {
        console.error(`   ... and ${clickableResults.invalidElements.length - 10} more`);
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
    const screens = discoverScreens(basePath);
    const result = await captureScreenshots(basePath, screens, false);

    // Check for failures and provide recovery instructions
    if (result.failed > 0) {
      console.log('\n' + '='.repeat(60));
      console.log('  ERROR RECOVERY INSTRUCTIONS');
      console.log('='.repeat(60));
      console.log(`\n   ${result.failed} screenshot(s) failed.`);
      console.log('\n   Options:');
      console.log('   1. Return to 03-generation to create missing HTML files');
      console.log(`   2. Retry failed screenshots: node capture-screenshots.js --retry-failed ${basePath}`);
      console.log(`   3. Check error log: ${ERROR_LOG_FILE}`);
      console.log('\n   ⚠️ If HTML files are missing, you MUST return to 03-generation!');
      process.exit(1);
    }
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
