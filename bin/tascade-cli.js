#!/usr/bin/env node

/**
 * Tascade AI CLI
 * 
 * The official command-line interface for Tascade AI with visual elements
 * and command structure inspired by claude-task-master.
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';
import { runCLI } from '../src/cli/commands.js';
import * as ui from '../src/cli/ui.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Get package information
let version = '0.1.0';
let projectName = 'Tascade AI';
try {
  const packageJson = JSON.parse(readFileSync(join(__dirname, '../package.json'), 'utf8'));
  version = packageJson.version;
  if (packageJson.name) {
    projectName = packageJson.name;
  }
} catch (error) {
  console.warn('Warning: Could not read package.json for version info.');
}

// Display a welcome message if this is the first command
if (process.argv.length <= 2 || process.argv[2] === 'help') {
  ui.displayBanner(projectName, version, 'Command-Line Interface');
}

// Run the CLI with the provided arguments
runCLI(process.argv);
