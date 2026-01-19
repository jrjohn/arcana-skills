#!/usr/bin/env node
/**
 * Validate UI Flow Hook (Cross-Platform Node.js)
 * Triggered after Write|Edit operations on files
 * Validates HTML UI Flow files for common issues
 *
 * Works on: Windows, Mac, Linux
 */

const fs = require('fs');
const path = require('path');

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

    // Only validate UI Flow HTML files
    if (!filePath.endsWith('.html')) {
      process.exit(0);
    }

    if (!/(ui-flow|uiflow|screen|04-ui-flow)/i.test(filePath)) {
      process.exit(0);
    }

    // Check if file exists
    if (!fs.existsSync(filePath)) {
      process.exit(0);
    }

    // Read and validate
    const content = fs.readFileSync(filePath, 'utf8');
    const errors = [];
    const warnings = [];

    // Check for empty href attributes
    if (/href=""/.test(content)) {
      errors.push('Empty href attributes found - navigation links may be broken');
    }

    // Check for empty id attributes
    if (/id=""/.test(content)) {
      errors.push('Empty id attributes found - screen references may be incomplete');
    }

    // Check for empty onclick handlers (CRITICAL)
    if (/onclick=""/.test(content)) {
      errors.push('Empty onclick handlers found - buttons without navigation');
    }

    // Check for alert placeholder onclick (CRITICAL)
    if (/onclick=["']alert\(/.test(content)) {
      errors.push('Alert placeholder found in onclick - should use actual navigation');
    }

    // Check for TODO markers
    if (/TODO|FIXME|XXX/i.test(content)) {
      warnings.push('TODO/FIXME markers found - review before finalizing');
    }

    // Check for placeholder images
    if (/src=["'](placeholder|TODO|)["']/.test(content)) {
      warnings.push('Placeholder or empty image sources found');
    }

    // Output validation results
    if (errors.length > 0) {
      console.log('UI Flow Validation ERRORS:');
      errors.forEach(err => console.log(`  [X] ${err}`));
    }

    if (warnings.length > 0) {
      console.log('UI Flow Validation Warnings:');
      warnings.forEach(warn => console.log(`  [!] ${warn}`));
    }

    // Run full validation when editing key files
    if (/(index\.html|device-preview\.html|ui-flow-diagram)/i.test(filePath)) {
      let uiFlowDir = path.dirname(filePath);

      // Go up one level if in docs folder
      if (uiFlowDir.endsWith('docs')) {
        uiFlowDir = path.dirname(uiFlowDir);
      }

      const gateScript = path.join(
        process.env.HOME || process.env.USERPROFILE,
        '.claude/skills/app-uiux-designer.skill/templates/ui-flow/post-generation-gate.js'
      );

      if (fs.existsSync(gateScript) && fs.existsSync(uiFlowDir)) {
        console.log('');
        console.log('Running Post-Generation Gate validation...');
        try {
          const { execSync } = require('child_process');
          const result = execSync(`node "${gateScript}" "${uiFlowDir}"`, {
            encoding: 'utf8',
            timeout: 30000
          });
          console.log(result);
        } catch (e) {
          console.log('Gate validation completed with issues');
        }
      }
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
