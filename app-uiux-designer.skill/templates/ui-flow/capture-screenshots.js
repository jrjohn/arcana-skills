/**
 * {{PROJECT_NAME}} UI Flow Screenshot Capture Script
 *
 * This script uses Puppeteer to capture screenshots of all screens
 * for both iPad and iPhone devices. Screenshots are used in ui-flow-diagram.html.
 *
 * Usage:
 *   npm install puppeteer
 *   node capture-screenshots.js
 *
 * Output:
 *   screenshots/auth/SCR-AUTH-001-login.png
 *   screenshots/onboard/SCR-ONBOARD-001-intro.png
 *   ...
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

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

// Run
captureScreenshots().catch(console.error);
