#!/usr/bin/env node
/**
 * ============================================================================
 * Node Transition Protocol (NTP)
 * ============================================================================
 * Purpose: Manage context-efficient node transitions with auto-summarization
 *
 * Flow:
 *   1. Validate current node completion (exit-validation)
 *   2. Generate Phase Summary for context preservation
 *   3. Update workspace state
 *   4. Output transition prompt for Claude
 *
 * Usage:
 *   node node-transition.js <from-node> <to-node> [project-path]
 *
 * Example:
 *   node node-transition.js 03-generation 04-validation /path/to/04-ui-flow
 * ============================================================================
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

// Colors
const C = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m'
};

// Node definitions with summary templates
const NODE_DEFINITIONS = {
  '00-init': {
    name: 'Initialization',
    summaryTemplate: (ctx) => `
## Completed: 00-init (Initialization)
- Project: ${ctx.project_name}
- Path: ${ctx.ui_flow_path}
- Templates: Copied and configured
- Workspace: Initialized

## Next: 03-generation
- Action: Generate all screen HTML files
- Expected: ${ctx.screens_total || 'TBD'} screens (iPad + iPhone)
`
  },
  '03-generation': {
    name: 'HTML Generation',
    summaryTemplate: (ctx) => `
## Completed: 03-generation (HTML Generation)
- iPad screens: ${ctx.ipad_count || 0}
- iPhone screens: ${ctx.iphone_count || 0}
- Modules: ${(ctx.modules || []).join(', ')}
- index.html: Variables replaced
- device-preview.html: Sidebar populated

## Next: 04-validation
- Action: Validate 100% navigation coverage
- Blocking: No empty onclick, no alert placeholders
`
  },
  '04-validation': {
    name: 'Navigation Validation',
    summaryTemplate: (ctx) => `
## Completed: 04-validation (Navigation Validation)
- Coverage: ${ctx.navigation_coverage || '100%'}
- Empty onclick: ${ctx.empty_onclick || 0}
- Alert placeholders: ${ctx.alert_placeholders || 0}
- Consistency: PASSED

## Next: 05-diagram
- Action: Generate UI Flow Diagram (iPad + iPhone)
- Expected: docs/ui-flow-diagram-ipad.html, docs/ui-flow-diagram-iphone.html
`
  },
  '05-diagram': {
    name: 'Diagram Generation',
    summaryTemplate: (ctx) => `
## Completed: 05-diagram (Diagram Generation)
- iPad diagram: docs/ui-flow-diagram-ipad.html
- iPhone diagram: docs/ui-flow-diagram-iphone.html
- Screen cards: ${ctx.ipad_count || 0}
- Navigation arrows: Generated

## Next: 06-screenshot
- Action: Capture PNG screenshots
- Expected: screenshots/ipad/*.png, screenshots/iphone/*.png
`
  },
  '06-screenshot': {
    name: 'Screenshot Capture',
    summaryTemplate: (ctx) => `
## Completed: 06-screenshot (Screenshot Capture)
- iPad screenshots: ${ctx.ipad_screenshots || 0}
- iPhone screenshots: ${ctx.iphone_screenshots || 0}
- Location: screenshots/ipad/, screenshots/iphone/

## Next: 07-feedback
- Action: Update SDD/SRS with UI prototype references
- Expected: SDD images embedded, SRS Screen References added
`
  },
  '07-feedback': {
    name: 'Document Feedback',
    summaryTemplate: (ctx) => `
## Completed: 07-feedback (Document Feedback)
- SDD: UI prototype references added
- SRS: Screen References section added
- DOCX: Regenerated

## Next: 08-finalize
- Action: Final verification and completion report
`
  },
  '08-finalize': {
    name: 'Finalization',
    summaryTemplate: (ctx) => `
## Completed: 08-finalize (UI Flow Complete!)
- Total screens: ${ctx.screens_total || 0}
- Navigation: 100% coverage
- Diagrams: Generated
- Screenshots: Captured
- Documents: Updated

🎉 UI Flow generation complete!
`
  }
};

const NODES_ORDER = ['00-init', '03-generation', '04-validation', '05-diagram', '06-screenshot', '07-feedback', '08-finalize'];

class NodeTransition {
  constructor(fromNode, toNode, projectPath) {
    this.fromNode = fromNode;
    this.toNode = toNode;
    this.projectPath = projectPath || process.cwd();
    this.skillDir = path.join(process.env.HOME, '.claude/skills/app-uiux-designer.skill');
    this.context = {};
  }

  // Load current context from workspace
  loadContext() {
    const processFile = path.join(this.projectPath, 'workspace/current-process.json');
    if (fs.existsSync(processFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(processFile, 'utf8'));
        this.context = {
          ...data.context,
          ...data.project,
          progress: data.progress,
          validation_state: data.validation_state
        };
      } catch (e) {
        console.error(`${C.yellow}Warning: Could not parse current-process.json${C.reset}`);
      }
    }

    // Gather additional context from file system
    this.gatherFileSystemContext();
  }

  // Gather context from actual files
  gatherFileSystemContext() {
    // Count screens
    try {
      const ipadFiles = execSync(`find "${this.projectPath}" -name "SCR-*.html" -not -path "*/iphone/*" -not -path "*/docs/*" 2>/dev/null | wc -l`, { encoding: 'utf8' });
      this.context.ipad_count = parseInt(ipadFiles.trim()) || 0;

      const iphoneFiles = execSync(`find "${this.projectPath}/iphone" -name "SCR-*.html" 2>/dev/null | wc -l`, { encoding: 'utf8' });
      this.context.iphone_count = parseInt(iphoneFiles.trim()) || 0;

      this.context.screens_total = this.context.ipad_count;
    } catch (e) {
      // Ignore errors
    }

    // Detect modules
    const moduleDirs = ['auth', 'common', 'dash', 'home', 'onboard', 'parent', 'profile', 'progress', 'report', 'setting', 'train', 'vocab'];
    this.context.modules = moduleDirs.filter(m => {
      const dirPath = path.join(this.projectPath, m);
      return fs.existsSync(dirPath) && fs.readdirSync(dirPath).some(f => f.startsWith('SCR-'));
    });

    // Count screenshots
    try {
      const ipadScreenshots = execSync(`find "${this.projectPath}/screenshots/ipad" -name "*.png" 2>/dev/null | wc -l`, { encoding: 'utf8' });
      this.context.ipad_screenshots = parseInt(ipadScreenshots.trim()) || 0;

      const iphoneScreenshots = execSync(`find "${this.projectPath}/screenshots/iphone" -name "*.png" 2>/dev/null | wc -l`, { encoding: 'utf8' });
      this.context.iphone_screenshots = parseInt(iphoneScreenshots.trim()) || 0;
    } catch (e) {
      // Ignore errors
    }
  }

  // Run exit validation for current node
  runExitValidation() {
    const validationScript = path.join(this.skillDir, 'process', this.fromNode, 'exit-validation.sh');

    if (!fs.existsSync(validationScript)) {
      console.log(`${C.yellow}Warning: exit-validation.sh not found for ${this.fromNode}${C.reset}`);
      return true;
    }

    console.log(`${C.cyan}▶ Running exit validation for ${this.fromNode}...${C.reset}`);
    const result = spawnSync('bash', [validationScript, this.projectPath], {
      stdio: 'inherit',
      encoding: 'utf8'
    });

    return result.status === 0;
  }

  // Generate Phase Summary
  generatePhaseSummary() {
    const nodeDef = NODE_DEFINITIONS[this.fromNode];
    if (!nodeDef) {
      return `## Completed: ${this.fromNode}\n\n## Next: ${this.toNode}`;
    }

    return nodeDef.summaryTemplate(this.context).trim();
  }

  // Save Phase Summary to workspace
  savePhaseSummary(summary) {
    const summaryFile = path.join(this.projectPath, 'workspace/phase-summary.md');
    const historyFile = path.join(this.projectPath, 'workspace/phase-history.md');

    // Ensure workspace exists
    const workspaceDir = path.dirname(summaryFile);
    if (!fs.existsSync(workspaceDir)) {
      fs.mkdirSync(workspaceDir, { recursive: true });
    }

    // Save current summary
    fs.writeFileSync(summaryFile, summary);

    // Append to history
    const timestamp = new Date().toISOString();
    const historyEntry = `\n---\n### ${timestamp}\n${summary}\n`;
    fs.appendFileSync(historyFile, historyEntry);

    return summaryFile;
  }

  // Update current-process.json for transition
  updateProcessState() {
    const processFile = path.join(this.projectPath, 'workspace/current-process.json');

    let data = {
      skill: 'app-uiux-designer',
      version: '2.1-cor-afp',
      architecture: 'chain-of-repository',
      progress: {},
      validation_state: {},
      recovery_hints: {},
      context: {}
    };

    if (fs.existsSync(processFile)) {
      try {
        data = JSON.parse(fs.readFileSync(processFile, 'utf8'));
      } catch (e) {}
    }

    const timestamp = new Date().toISOString();

    // Update progress
    data.progress[this.fromNode] = 'completed';
    data.progress[this.toNode] = 'in_progress';
    data.current_process = this.toNode;
    data.updated_at = timestamp;

    // Update validation state
    if (!data.validation_state) data.validation_state = {};
    data.validation_state[this.fromNode] = {
      passed: true,
      timestamp: timestamp,
      checks: ['exit-validation.sh']
    };

    // Update recovery hints
    data.recovery_hints = {
      last_action: `Transitioned from ${this.fromNode} to ${this.toNode}`,
      last_completed_node: this.fromNode,
      current_node: this.toNode,
      transition_timestamp: timestamp,
      pending_fixes: [],
      files_modified: []
    };

    // Update context
    data.context = {
      ...data.context,
      screens_completed: this.context.ipad_count,
      screens_total: this.context.ipad_count,
      modules: this.context.modules
    };

    fs.writeFileSync(processFile, JSON.stringify(data, null, 2));
  }

  // Generate Claude transition prompt
  generateTransitionPrompt(summary) {
    const nextNodeDef = NODE_DEFINITIONS[this.toNode];
    const nextNodeName = nextNodeDef ? nextNodeDef.name : this.toNode;

    return `
${C.bgGreen}${C.bold} CONTEXT COMPACT POINT ${C.reset}

${C.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C.reset}
${C.bold}PHASE SUMMARY (Preserve this information)${C.reset}
${C.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C.reset}

${summary}

${C.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C.reset}
${C.bold}NEXT NODE: ${this.toNode} (${nextNodeName})${C.reset}
${C.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C.reset}

${C.yellow}📋 Claude Instructions:${C.reset}
1. ${C.bold}Read${C.reset}: process/${this.toNode}/README.md
2. ${C.bold}Plan${C.reset}: List specific tasks for this node
3. ${C.bold}Execute${C.reset}: Perform tasks one by one
4. ${C.bold}Validate${C.reset}: Run exit-validation.sh when done

${C.dim}Saved to: workspace/phase-summary.md${C.reset}
${C.dim}History: workspace/phase-history.md${C.reset}
`;
  }

  // Main execution
  async run() {
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║           NODE TRANSITION PROTOCOL (NTP)                   ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log(`${C.cyan}From:${C.reset} ${this.fromNode}`);
    console.log(`${C.cyan}To:${C.reset}   ${this.toNode}`);
    console.log(`${C.cyan}Path:${C.reset} ${this.projectPath}`);
    console.log('');

    // Step 1: Load context
    this.loadContext();

    // Step 2: Run exit validation
    const validationPassed = this.runExitValidation();
    if (!validationPassed) {
      console.log('');
      console.log(`${C.red}${C.bold}⛔ TRANSITION BLOCKED${C.reset}`);
      console.log(`${C.red}   Exit validation failed for ${this.fromNode}${C.reset}`);
      console.log(`${C.red}   Fix the issues and run again.${C.reset}`);
      return false;
    }

    // Step 3: Generate Phase Summary
    console.log('');
    console.log(`${C.cyan}▶ Generating Phase Summary...${C.reset}`);
    const summary = this.generatePhaseSummary();
    const summaryFile = this.savePhaseSummary(summary);
    console.log(`${C.green}✅ Saved to: ${summaryFile}${C.reset}`);

    // Step 4: Update process state
    console.log('');
    console.log(`${C.cyan}▶ Updating process state...${C.reset}`);
    this.updateProcessState();
    console.log(`${C.green}✅ current-process.json updated${C.reset}`);

    // Step 5: Output transition prompt
    const prompt = this.generateTransitionPrompt(summary);
    console.log(prompt);

    return true;
  }
}

// Main
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node node-transition.js <from-node> <to-node> [project-path]');
    console.log('');
    console.log('Nodes: 00-init, 03-generation, 04-validation, 05-diagram, 06-screenshot, 07-feedback, 08-finalize');
    console.log('');
    console.log('Example:');
    console.log('  node node-transition.js 03-generation 04-validation /path/to/04-ui-flow');
    process.exit(1);
  }

  const fromNode = args[0];
  const toNode = args[1];
  const projectPath = args[2] || process.cwd();

  if (!NODES_ORDER.includes(fromNode) || !NODES_ORDER.includes(toNode)) {
    console.error(`${C.red}Error: Invalid node${C.reset}`);
    console.error(`Valid nodes: ${NODES_ORDER.join(', ')}`);
    process.exit(1);
  }

  const transition = new NodeTransition(fromNode, toNode, projectPath);
  const success = await transition.run();

  process.exit(success ? 0 : 1);
}

main().catch(err => {
  console.error(`${C.red}Error: ${err.message}${C.reset}`);
  process.exit(1);
});
