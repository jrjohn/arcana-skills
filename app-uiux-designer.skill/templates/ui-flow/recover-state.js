#!/usr/bin/env node
/**
 * ============================================================================
 * Recover State - Compaction Recovery Protocol
 * ============================================================================
 * Purpose: Restore and validate project state after Claude compaction
 * Usage: node recover-state.js [project-04-ui-flow-path]
 * ============================================================================
 */

const fs = require('fs');
const path = require('path');

// Configuration
const PROJECT_PATH = process.argv[2] || process.cwd();
const WORKSPACE_PATH = path.join(PROJECT_PATH, 'workspace');

// ANSI color codes
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, symbol, message) {
  console.log(`  ${colors[color]}${symbol}${colors.reset} ${message}`);
}

function logHeader(text) {
  console.log(`\n${colors.blue}[${text}]${colors.reset}`);
}

// ============================================================================
// Main Recovery Logic
// ============================================================================

async function recoverState() {
  console.log('\n' + colors.blue + '============================================' + colors.reset);
  console.log(colors.blue + '       State Recovery Protocol' + colors.reset);
  console.log(colors.blue + '============================================' + colors.reset);

  const result = {
    success: true,
    recovered: [],
    created: [],
    errors: []
  };

  // 1. Ensure workspace exists
  logHeader('1. Workspace Check');
  if (!fs.existsSync(WORKSPACE_PATH)) {
    fs.mkdirSync(WORKSPACE_PATH, { recursive: true });
    fs.mkdirSync(path.join(WORKSPACE_PATH, 'context'), { recursive: true });
    fs.mkdirSync(path.join(WORKSPACE_PATH, 'state'), { recursive: true });
    log('yellow', '⚠️', 'Created workspace directory');
    result.created.push('workspace/');
  } else {
    log('green', '✅', 'workspace/ exists');
  }

  // 2. Analyze actual file state
  logHeader('2. Analyzing File State');
  const fileState = analyzeFileState();
  log('blue', '📊', `iPad screens: ${fileState.ipadCount}`);
  log('blue', '📊', `iPhone screens: ${fileState.iphoneCount}`);
  log('blue', '📊', `Modules: ${fileState.modules.join(', ')}`);

  // 3. Load or create current-process.json
  logHeader('3. Process State');
  const processFile = path.join(WORKSPACE_PATH, 'current-process.json');
  let processData;

  if (fs.existsSync(processFile)) {
    try {
      processData = JSON.parse(fs.readFileSync(processFile, 'utf8'));
      log('green', '✅', `Loaded current-process.json (node: ${processData.current_process})`);
      result.recovered.push('current-process.json');
    } catch (e) {
      log('red', '❌', 'current-process.json corrupted, recreating...');
      processData = null;
    }
  }

  if (!processData) {
    processData = createInitialProcessState(fileState);
    fs.writeFileSync(processFile, JSON.stringify(processData, null, 2));
    log('yellow', '⚠️', 'Created new current-process.json');
    result.created.push('current-process.json');
  }

  // 4. Validate and update process state based on file reality
  logHeader('4. State Validation');
  const validatedState = validateProcessState(processData, fileState);

  if (validatedState.needsUpdate) {
    processData = validatedState.processData;
    processData.last_updated = new Date().toISOString();
    fs.writeFileSync(processFile, JSON.stringify(processData, null, 2));
    log('yellow', '⚠️', `Updated process state: ${validatedState.reason}`);
    result.recovered.push('process state corrected');
  } else {
    log('green', '✅', 'Process state is consistent with file reality');
  }

  // 5. Load or create validation-chain.json
  logHeader('5. Validation Chain');
  const chainFile = path.join(WORKSPACE_PATH, 'validation-chain.json');
  let chainData;

  if (fs.existsSync(chainFile)) {
    try {
      chainData = JSON.parse(fs.readFileSync(chainFile, 'utf8'));
      log('green', '✅', `Loaded validation-chain.json (${chainData.chain.length} entries)`);
      result.recovered.push('validation-chain.json');
    } catch (e) {
      log('red', '❌', 'validation-chain.json corrupted, recreating...');
      chainData = null;
    }
  }

  if (!chainData) {
    chainData = createInitialChain(processData, fileState);
    fs.writeFileSync(chainFile, JSON.stringify(chainData, null, 2));
    log('yellow', '⚠️', 'Created validation-chain.json from inferred state');
    result.created.push('validation-chain.json');
  }

  // 6. Summary
  logHeader('Summary');
  console.log('');
  log('blue', '📍', `Current Node: ${colors.yellow}${processData.current_process}${colors.reset}`);
  log('blue', '📊', `Total Screens: ${colors.yellow}${fileState.ipadCount}${colors.reset}`);
  log('blue', '🎯', `Last Checkpoint: ${colors.yellow}${chainData.last_valid_checkpoint}${colors.reset}`);

  if (result.errors.length > 0) {
    console.log('');
    log('red', '❌', `Errors: ${result.errors.length}`);
    result.errors.forEach(e => console.log(`      - ${e}`));
    result.success = false;
  }

  if (result.created.length > 0) {
    console.log('');
    log('yellow', '📝', `Created: ${result.created.join(', ')}`);
  }

  if (result.recovered.length > 0) {
    console.log('');
    log('green', '✅', `Recovered: ${result.recovered.join(', ')}`);
  }

  console.log('\n' + colors.blue + '============================================' + colors.reset);
  console.log(`${colors.green}Recovery complete!${colors.reset}`);
  console.log(`Continue from node: ${colors.yellow}${processData.current_process}${colors.reset}`);
  console.log(colors.blue + '============================================' + colors.reset + '\n');

  return result;
}

// ============================================================================
// Helper Functions
// ============================================================================

function analyzeFileState() {
  const state = {
    ipadCount: 0,
    iphoneCount: 0,
    modules: new Set(),
    hasIndex: false,
    hasDevicePreview: false,
    hasDiagramIpad: false,
    hasDiagramIphone: false
  };

  // Count iPad screens
  const ipadDirs = ['auth', 'common', 'dash', 'parent', 'profile', 'progress', 'setting', 'train', 'vocab'];
  ipadDirs.forEach(dir => {
    const dirPath = path.join(PROJECT_PATH, dir);
    if (fs.existsSync(dirPath)) {
      const files = fs.readdirSync(dirPath).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
      state.ipadCount += files.length;
      if (files.length > 0) state.modules.add(dir);
    }
  });

  // Count iPhone screens
  ipadDirs.forEach(dir => {
    const dirPath = path.join(PROJECT_PATH, 'iphone', dir);
    if (fs.existsSync(dirPath)) {
      const files = fs.readdirSync(dirPath).filter(f => f.startsWith('SCR-') && f.endsWith('.html'));
      state.iphoneCount += files.length;
    }
  });

  // Check critical files
  state.hasIndex = fs.existsSync(path.join(PROJECT_PATH, 'index.html'));
  state.hasDevicePreview = fs.existsSync(path.join(PROJECT_PATH, 'device-preview.html'));
  state.hasDiagramIpad = fs.existsSync(path.join(PROJECT_PATH, 'docs', 'ui-flow-diagram-ipad.html'));
  state.hasDiagramIphone = fs.existsSync(path.join(PROJECT_PATH, 'docs', 'ui-flow-diagram-iphone.html'));

  state.modules = Array.from(state.modules);

  return state;
}

function createInitialProcessState(fileState) {
  // Infer progress from file state
  const progress = {
    '00-init': 'pending',
    '03-generation': 'pending',
    '04-validation': 'pending',
    '05-diagram': 'pending',
    '06-screenshot': 'pending',
    '07-feedback': 'pending',
    '08-finalize': 'pending'
  };

  let currentProcess = '00-init';

  // If we have screens, init is done
  if (fileState.ipadCount > 0) {
    progress['00-init'] = 'completed';
    currentProcess = '03-generation';
  }

  // If iPad and iPhone match, generation likely done
  if (fileState.ipadCount > 0 && fileState.ipadCount === fileState.iphoneCount) {
    progress['03-generation'] = 'completed';
    currentProcess = '04-validation';
  }

  // If diagrams exist, assume validation passed
  if (fileState.hasDiagramIpad && fileState.hasDiagramIphone) {
    progress['04-validation'] = 'completed';
    progress['05-diagram'] = 'completed';
    currentProcess = '06-screenshot';
  }

  return {
    project_name: path.basename(path.dirname(PROJECT_PATH)),
    current_process: currentProcess,
    last_updated: new Date().toISOString(),
    progress: progress,
    validation_state: {},
    recovery_hints: {
      last_action: 'State recovered from file analysis',
      pending_fixes: [],
      files_modified: []
    },
    context: {
      total_screens: fileState.ipadCount,
      modules: fileState.modules
    }
  };
}

function validateProcessState(processData, fileState) {
  let needsUpdate = false;
  let reason = '';

  // Check if claimed state matches reality
  if (processData.progress['03-generation'] === 'completed' && fileState.ipadCount === 0) {
    processData.progress['03-generation'] = 'pending';
    processData.current_process = '03-generation';
    needsUpdate = true;
    reason = 'No screens found but generation marked complete';
  }

  // Update context if screen count changed
  if (processData.context && processData.context.total_screens !== fileState.ipadCount) {
    processData.context.total_screens = fileState.ipadCount;
    processData.context.modules = fileState.modules;
    needsUpdate = true;
    reason = reason || 'Screen count updated';
  }

  return { needsUpdate, reason, processData };
}

function createInitialChain(processData, fileState) {
  const chain = [];
  let lastCheckpoint = null;

  // Infer chain from progress
  if (processData.progress['00-init'] === 'completed') {
    chain.push({
      node: '00-init',
      validation: 'exit-validation',
      result: 'PASSED',
      timestamp: new Date().toISOString(),
      details: { inferred: true, templates_copied: true }
    });
    lastCheckpoint = '00-init';
  }

  if (processData.progress['03-generation'] === 'completed' && fileState.ipadCount > 0) {
    chain.push({
      node: '03-generation',
      validation: 'template-compliance-gate',
      result: 'PASSED',
      timestamp: new Date().toISOString(),
      details: {
        inferred: true,
        ipad_screens: fileState.ipadCount,
        iphone_screens: fileState.iphoneCount
      }
    });
    lastCheckpoint = '03-generation';
  }

  if (processData.progress['04-validation'] === 'completed') {
    chain.push({
      node: '04-validation',
      validation: 'navigation-validation',
      result: 'PASSED',
      timestamp: new Date().toISOString(),
      details: { inferred: true }
    });
    lastCheckpoint = '04-validation';
  }

  if (processData.progress['05-diagram'] === 'completed' && fileState.hasDiagramIpad) {
    chain.push({
      node: '05-diagram',
      validation: 'diagram-validation',
      result: 'PASSED',
      timestamp: new Date().toISOString(),
      details: { inferred: true }
    });
    lastCheckpoint = '05-diagram';
  }

  return {
    chain: chain,
    last_valid_checkpoint: lastCheckpoint || 'none'
  };
}

// Run
recoverState().then(result => {
  process.exit(result.success ? 0 : 1);
}).catch(err => {
  console.error('Recovery failed:', err);
  process.exit(1);
});
