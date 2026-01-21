#!/usr/bin/env node
/**
 * ============================================================================
 * Exit Gate - Unified Validation Gate
 * ============================================================================
 * Purpose: Enforce exit validation before proceeding to next node
 * Usage: node exit-gate.js <node> [project-path]
 *
 * Examples:
 *   node exit-gate.js 00-init /path/to/04-ui-flow
 *   node exit-gate.js 03-generation
 *   node exit-gate.js 04-validation
 *
 * Exit codes:
 *   0 - Validation passed, can proceed
 *   1 - Validation failed, BLOCKED
 * ============================================================================
 */

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI colors
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m'
};

class ExitGate {
  constructor(node, projectPath) {
    this.node = node;
    this.projectPath = projectPath || process.cwd();
    this.skillDir = path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill');
    this.passed = false;
  }

  log(msg) { console.log(msg); }

  // Run exit-validation.sh for the node
  async validate() {
    this.log('');
    this.log('╔════════════════════════════════════════════════════════════╗');
    this.log(`║           EXIT GATE: ${this.node.padEnd(20)}                 ║`);
    this.log('║    Mandatory validation before proceeding to next node     ║');
    this.log('╚════════════════════════════════════════════════════════════╝');
    this.log('');
    this.log(`${colors.cyan}Project: ${this.projectPath}${colors.reset}`);
    this.log('');

    // Find exit-validation.sh for this node
    const validationScript = path.join(this.skillDir, 'process', this.node, 'exit-validation.sh');

    if (!fs.existsSync(validationScript)) {
      this.log(`${colors.red}❌ exit-validation.sh not found for ${this.node}${colors.reset}`);
      return false;
    }

    this.log(`${colors.cyan}▶ Running exit-validation.sh...${colors.reset}`);
    this.log('');

    // Run the validation script
    const result = spawnSync('bash', [validationScript, this.projectPath], {
      cwd: this.projectPath,
      stdio: 'inherit',
      encoding: 'utf8'
    });

    this.passed = result.status === 0;

    // Update current-process.json
    this.updateProcessState();

    // Print gate result
    this.printGateResult();

    return this.passed;
  }

  updateProcessState() {
    const processFile = path.join(this.projectPath, 'workspace/current-process.json');

    if (!fs.existsSync(processFile)) {
      this.log(`${colors.yellow}⚠️ workspace/current-process.json not found${colors.reset}`);
      return;
    }

    try {
      const data = JSON.parse(fs.readFileSync(processFile, 'utf8'));
      const timestamp = new Date().toISOString();

      // Update validation_state
      if (!data.validation_state) {
        data.validation_state = {};
      }

      data.validation_state[this.node] = {
        passed: this.passed,
        timestamp: timestamp,
        checks: this.passed ? ['exit-validation.sh'] : []
      };

      // Update progress if passed
      if (this.passed) {
        data.progress[this.node] = 'completed';
        data.recovery_hints = data.recovery_hints || {};
        data.recovery_hints.last_action = `Exit gate ${this.node} PASSED at ${timestamp}`;

        // Determine next node
        const nodes = ['00-init', '03-generation', '04-validation', '05-diagram', '06-screenshot', '07-feedback', '08-finalize'];
        const currentIdx = nodes.indexOf(this.node);
        if (currentIdx >= 0 && currentIdx < nodes.length - 1) {
          const nextNode = nodes[currentIdx + 1];
          data.current_process = nextNode;
          data.progress[nextNode] = 'in_progress';
        } else {
          data.current_process = null; // Completed
        }
      } else {
        data.progress[this.node] = 'in_progress';
        data.recovery_hints = data.recovery_hints || {};
        data.recovery_hints.last_action = `Exit gate ${this.node} FAILED at ${timestamp}`;
      }

      data.updated_at = timestamp;
      fs.writeFileSync(processFile, JSON.stringify(data, null, 2));

    } catch (err) {
      this.log(`${colors.yellow}⚠️ Could not update current-process.json: ${err.message}${colors.reset}`);
    }
  }

  printGateResult() {
    this.log('');
    this.log('════════════════════════════════════════════════════════════');

    if (this.passed) {
      this.log(`${colors.bgGreen}${colors.bold}  ✅ EXIT GATE PASSED: ${this.node}  ${colors.reset}`);
      this.log('');
      this.log('  You may proceed to the next node.');

      // Show next node
      const nodes = ['00-init', '03-generation', '04-validation', '05-diagram', '06-screenshot', '07-feedback', '08-finalize'];
      const currentIdx = nodes.indexOf(this.node);
      if (currentIdx >= 0 && currentIdx < nodes.length - 1) {
        this.log(`  Next: ${colors.cyan}${nodes[currentIdx + 1]}${colors.reset}`);
      } else {
        this.log(`  ${colors.green}UI Flow Generation Complete!${colors.reset}`);
      }
    } else {
      this.log(`${colors.bgRed}${colors.bold}  ⛔ EXIT GATE FAILED: ${this.node}  ${colors.reset}`);
      this.log('');
      this.log('  You are BLOCKED from proceeding to the next node.');
      this.log('  Fix the issues above and run this gate again.');
    }

    this.log('════════════════════════════════════════════════════════════');
    this.log('');
  }
}

// Main
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node exit-gate.js <node> [project-path]');
    console.log('');
    console.log('Nodes: 00-init, 03-generation, 04-validation, 05-diagram, 06-screenshot, 07-feedback, 08-finalize');
    console.log('');
    console.log('Examples:');
    console.log('  node exit-gate.js 03-generation /path/to/04-ui-flow');
    console.log('  node exit-gate.js 04-validation');
    process.exit(1);
  }

  const node = args[0];
  const projectPath = args[1] || process.cwd();

  const validNodes = ['00-init', '03-generation', '04-validation', '05-diagram', '06-screenshot', '07-feedback', '08-finalize'];

  if (!validNodes.includes(node)) {
    console.error(`${colors.red}Error: Invalid node "${node}"${colors.reset}`);
    console.error(`Valid nodes: ${validNodes.join(', ')}`);
    process.exit(1);
  }

  const gate = new ExitGate(node, projectPath);
  const passed = await gate.validate();

  process.exit(passed ? 0 : 1);
}

main().catch(err => {
  console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
  process.exit(1);
});
