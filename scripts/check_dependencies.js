#!/usr/bin/env node

/**
 * Dependency Check Script for Tascade AI
 * 
 * This script checks if all required npm dependencies are installed.
 * It's used by the Tascade AI CLI to ensure all dependencies are available
 * before attempting to run commands.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Required dependencies for Tascade AI
const requiredDependencies = [
  'commander',
  'inquirer',
  'chalk',
  'ora',
  'ws',
  'node-fetch'
];

/**
 * Check if a package is installed
 * @param {string} packageName - The name of the package to check
 * @returns {Promise<boolean>} - True if the package is installed, false otherwise
 */
async function isPackageInstalled(packageName) {
  try {
    // Try to require the package
    await import(packageName);
    return true;
  } catch (error) {
    // If the error is not a module not found error, it might be installed but have other issues
    if (error.code !== 'ERR_MODULE_NOT_FOUND') {
      console.warn(`Warning: Error importing ${packageName}: ${error.message}`);
      return true;
    }
    return false;
  }
}

/**
 * Install missing dependencies
 * @param {string[]} missingDependencies - Array of missing dependency names
 * @returns {Promise<boolean>} - True if installation was successful, false otherwise
 */
async function installDependencies(missingDependencies) {
  return new Promise((resolve) => {
    console.log(`Installing missing dependencies: ${missingDependencies.join(', ')}...`);
    
    const npmInstall = spawn('npm', ['install', ...missingDependencies], {
      cwd: projectRoot,
      stdio: 'inherit'
    });
    
    npmInstall.on('close', (code) => {
      if (code === 0) {
        console.log('Dependencies installed successfully.');
        resolve(true);
      } else {
        console.error(`Error installing dependencies. npm exited with code ${code}`);
        resolve(false);
      }
    });
  });
}

/**
 * Main function to check and install dependencies
 */
async function checkDependencies() {
  console.log('Checking Tascade AI dependencies...');
  
  const missingDependencies = [];
  
  // Check each required dependency
  for (const dependency of requiredDependencies) {
    const isInstalled = await isPackageInstalled(dependency);
    if (!isInstalled) {
      missingDependencies.push(dependency);
    }
  }
  
  // If there are missing dependencies, try to install them
  if (missingDependencies.length > 0) {
    console.log(`Missing dependencies: ${missingDependencies.join(', ')}`);
    
    // Check if package.json exists
    const packageJsonPath = path.join(projectRoot, 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
      console.error('Error: package.json not found. Cannot install dependencies.');
      return false;
    }
    
    // Install missing dependencies
    const installSuccess = await installDependencies(missingDependencies);
    return installSuccess;
  }
  
  console.log('All dependencies are installed.');
  return true;
}

// If this script is run directly, check dependencies
if (import.meta.url === `file://${process.argv[1]}`) {
  checkDependencies().then((success) => {
    process.exit(success ? 0 : 1);
  });
}

export default checkDependencies;
