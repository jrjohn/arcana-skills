#!/usr/bin/env node
/**
 * Enforce UI/UX Designer Skill Hook (Cross-Platform Node.js)
 * Triggered after Write|Edit operations on SDD files
 * Reminds to use app-uiux-designer.skill for UI Flow generation
 *
 * Works on: Windows, Mac, Linux
 */

const fs = require('fs');

// Read hook input from stdin
let inputData = '';

process.stdin.setEncoding('utf8');
process.stdin.on('readable', () => {
  let chunk;
  while ((chunk = process.stdin.read()) !== null) {
    inputData += chunk;
  }
});

process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(inputData);
    const filePath = hookData?.tool_input?.file_path;

    if (!filePath) {
      process.exit(0);
    }

    // Only check SDD files
    if (!/SDD.*\.md$/i.test(filePath)) {
      process.exit(0);
    }

    // Check if file exists
    if (!fs.existsSync(filePath)) {
      process.exit(0);
    }

    // Read content
    const content = fs.readFileSync(filePath, 'utf8');

    // Check if SDD has screen designs section
    if (/## Screen Designs|## Design Views|SCR-/i.test(content)) {
      console.log('');
      console.log('========================================');
      console.log('[REMINDER] SDD with screen designs detected!');
      console.log('----------------------------------------');
      console.log('According to IEC 62304 workflow:');
      console.log('  1. Use \'app-uiux-designer.skill\' to generate UI Flow');
      console.log('  2. Generate Design Tokens + Theme CSS');
      console.log('  3. Create HTML UI Flow prototype');
      console.log('  4. Capture screenshots');
      console.log('  5. Update SDD with UI references');
      console.log('  6. Update SRS with Screen References');
      console.log('========================================');
      console.log('');
    }

    process.exit(0);
  } catch (e) {
    // Silent fail for non-JSON input
    process.exit(0);
  }
});

// Handle case where stdin is empty
setTimeout(() => {
  if (!inputData) {
    process.exit(0);
  }
}, 100);
