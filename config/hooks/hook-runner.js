#!/usr/bin/env node
/**
 * Universal Hook Runner
 * 自動偵測平台和路徑，執行對應的 hook 腳本
 *
 * 此檔案應放在 ~/.claude/hooks/ 目錄下
 * Usage: node hook-runner.js <hook-name>
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get hook name from argument
const hookName = process.argv[2];

if (!hookName) {
  process.exit(0);
}

// Find hooks directory (same directory as this script)
const hooksDir = __dirname;

// Find the hook script
const jsHook = path.join(hooksDir, `${hookName}.js`);

if (!fs.existsSync(jsHook)) {
  // No hook found, exit silently
  process.exit(0);
}

// Read stdin
let inputData = '';
process.stdin.setEncoding('utf8');

process.stdin.on('readable', () => {
  let chunk;
  while ((chunk = process.stdin.read()) !== null) {
    inputData += chunk;
  }
});

process.stdin.on('end', () => {
  // Run the hook with the collected input
  const child = spawn('node', [jsHook], {
    stdio: ['pipe', 'inherit', 'inherit'],
    env: process.env
  });

  child.stdin.write(inputData);
  child.stdin.end();

  child.on('close', (code) => {
    process.exit(code || 0);
  });

  child.on('error', () => {
    process.exit(0);
  });
});

// Handle case where stdin is empty or times out
setTimeout(() => {
  if (!inputData && !process.stdin.readableEnded) {
    process.exit(0);
  }
}, 5000);
