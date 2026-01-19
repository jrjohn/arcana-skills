#!/usr/bin/env node
/**
 * Initialize project with IEC 62304 templates
 * Cross-platform compatible (Windows, macOS, Linux)
 *
 * Usage:
 *   node init-project.js [project-dir]
 *
 * This script copies SRS/SDD templates to the target project directory.
 */

const fs = require('fs');
const path = require('path');

// Get skill directory (where this script is located)
const SKILL_DIR = path.resolve(__dirname, '..');

// Template directories
const TEMPLATES = {
  srs: path.join(SKILL_DIR, 'srs-template'),
  sdd: path.join(SKILL_DIR, 'sdd-template')
};

// Target project directory
const projectDir = process.argv[2] || process.cwd();

/**
 * Copy directory recursively
 */
function copyDir(src, dest) {
  if (!fs.existsSync(src)) {
    console.error(`Source not found: ${src}`);
    return false;
  }

  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
      console.log(`  Copied: ${entry.name}`);
    }
  }

  return true;
}

/**
 * Create project directory structure
 */
function createProjectStructure(baseDir) {
  const dirs = [
    '01-requirements',
    '02-design',
    '03-assets',
    '04-ui-flow',
    '05-development',
    '06-testing',
    '07-verification',
    '08-traceability'
  ];

  for (const dir of dirs) {
    const fullPath = path.join(baseDir, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
      console.log(`  Created: ${dir}/`);
    }
  }
}

/**
 * Main
 */
function main() {
  console.log('\n=== IEC 62304 Project Initializer ===\n');
  console.log(`Skill directory: ${SKILL_DIR}`);
  console.log(`Project directory: ${projectDir}\n`);

  // Create project structure
  console.log('Creating project structure...');
  createProjectStructure(projectDir);

  // Copy SRS template
  console.log('\nCopying SRS template...');
  const srsTarget = path.join(projectDir, '01-requirements');
  if (fs.existsSync(TEMPLATES.srs)) {
    const files = fs.readdirSync(TEMPLATES.srs);
    for (const file of files) {
      if (file.endsWith('.md')) {
        fs.copyFileSync(
          path.join(TEMPLATES.srs, file),
          path.join(srsTarget, file)
        );
        console.log(`  Copied: ${file}`);
      }
    }
  }

  // Copy SDD template
  console.log('\nCopying SDD template...');
  const sddTarget = path.join(projectDir, '02-design');
  if (fs.existsSync(TEMPLATES.sdd)) {
    const files = fs.readdirSync(TEMPLATES.sdd);
    for (const file of files) {
      if (file.endsWith('.md')) {
        fs.copyFileSync(
          path.join(TEMPLATES.sdd, file),
          path.join(sddTarget, file)
        );
        console.log(`  Copied: ${file}`);
      }
    }
  }

  console.log('\n=== Initialization Complete ===');
  console.log('\nNext steps:');
  console.log('1. Rename template files (e.g., srs-template.md → SRS-YourProject-1.0.md)');
  console.log('2. Replace {{placeholders}} with actual project information');
  console.log('3. Start requirements gathering\n');
}

main();
