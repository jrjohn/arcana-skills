#!/usr/bin/env node
/**
 * UI Flow Complete Validator
 *
 * Runs all validation scripts in sequence:
 * 1. validate-ui-flow.js      - Screen files existence and module structure
 * 2. validate-navigation.js   - Navigation links and click handlers
 * 3. validate-consistency.js  - Reference standard consistency
 *
 * Usage:
 *   node validate-all.js [project-path]
 *
 * If project-path is not provided, uses current directory.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  dim: '\x1b[2m'
};

const validators = [
  {
    name: 'UI Flow Structure',
    script: 'validate-ui-flow.js',
    description: 'Validates screen files and module structure'
  },
  {
    name: 'Navigation',
    script: 'validate-navigation.js',
    description: 'Validates navigation links and click handlers'
  },
  {
    name: 'Consistency',
    script: 'validate-consistency.js',
    description: 'Validates against reference-example standards'
  }
];

function runValidator(scriptPath, projectPath) {
  return new Promise((resolve) => {
    const child = spawn('node', [scriptPath, projectPath], {
      stdio: 'inherit',
      cwd: projectPath
    });

    child.on('close', (code) => {
      resolve(code === 0);
    });

    child.on('error', (err) => {
      console.error(`${colors.red}Error running validator: ${err.message}${colors.reset}`);
      resolve(false);
    });
  });
}

async function main() {
  const projectPath = process.argv[2] || process.cwd();

  console.log();
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║           UI FLOW COMPLETE VALIDATION                        ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log();
  console.log(`${colors.cyan}Project: ${projectPath}${colors.reset}`);
  console.log();

  const results = [];
  let allPassed = true;

  for (let i = 0; i < validators.length; i++) {
    const validator = validators[i];

    console.log(`${colors.magenta}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}`);
    console.log(`${colors.bold}[${i + 1}/${validators.length}] ${validator.name}${colors.reset}`);
    console.log(`${colors.dim}${validator.description}${colors.reset}`);
    console.log(`${colors.magenta}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}`);
    console.log();

    // Find the script - check multiple locations
    const scriptLocations = [
      path.join(projectPath, validator.script),
      path.join(__dirname, validator.script),
      path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill/templates/ui-flow', validator.script)
    ];

    let scriptPath = null;
    for (const loc of scriptLocations) {
      if (fs.existsSync(loc)) {
        scriptPath = loc;
        break;
      }
    }

    if (!scriptPath) {
      console.log(`${colors.yellow}⚠️  ${validator.script} not found, skipping${colors.reset}`);
      results.push({ name: validator.name, status: 'skipped' });
      console.log();
      continue;
    }

    const success = await runValidator(scriptPath, projectPath);
    results.push({ name: validator.name, status: success ? 'passed' : 'failed' });

    if (!success) {
      allPassed = false;
    }

    console.log();
  }

  // Summary
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║           VALIDATION SUMMARY                                 ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log();

  for (const result of results) {
    let statusIcon, statusColor;
    switch (result.status) {
      case 'passed':
        statusIcon = '✅';
        statusColor = colors.green;
        break;
      case 'failed':
        statusIcon = '❌';
        statusColor = colors.red;
        break;
      case 'skipped':
        statusIcon = '⏭️ ';
        statusColor = colors.yellow;
        break;
    }
    console.log(`${statusIcon} ${statusColor}${result.name}: ${result.status.toUpperCase()}${colors.reset}`);
  }

  console.log();

  if (allPassed) {
    console.log(`${colors.green}${colors.bold}╔══════════════════════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.green}${colors.bold}║  ✅ ALL VALIDATIONS PASSED                                   ║${colors.reset}`);
    console.log(`${colors.green}${colors.bold}╚══════════════════════════════════════════════════════════════╝${colors.reset}`);
  } else {
    console.log(`${colors.red}${colors.bold}╔══════════════════════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.red}${colors.bold}║  ❌ SOME VALIDATIONS FAILED                                  ║${colors.reset}`);
    console.log(`${colors.red}${colors.bold}╚══════════════════════════════════════════════════════════════╝${colors.reset}`);
  }

  console.log();

  process.exit(allPassed ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
