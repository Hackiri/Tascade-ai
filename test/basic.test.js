/**
 * Basic tests for Tascade AI
 * 
 * These tests verify that the core functionality of Tascade AI works properly.
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { spawnSync } from 'child_process';
import assert from 'assert';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');
const binPath = join(rootDir, 'bin', 'tascade-cli.js');

console.log('Running basic tests for Tascade AI...');

// Test 1: Verify that the CLI script exists
try {
  const { statSync } = await import('fs');
  const stats = statSync(binPath);
  assert(stats.isFile(), 'CLI script does not exist');
  console.log('✓ CLI script exists');
} catch (error) {
  console.error('✗ CLI script does not exist:', error.message);
  process.exit(1);
}

// Test 2: Verify that the CLI script is executable
try {
  const result = spawnSync('node', [binPath, '--help'], { encoding: 'utf8' });
  assert(result.status === 0, 'CLI script is not executable');
  console.log('✓ CLI script is executable');
} catch (error) {
  console.error('✗ CLI script is not executable:', error.message);
  process.exit(1);
}

// Test 3: Verify that the help command works
try {
  const result = spawnSync('node', [binPath, '--help'], { encoding: 'utf8' });
  assert(result.status === 0, 'Help command failed');
  assert(result.stdout.includes('Usage:'), 'Help output is incorrect');
  console.log('✓ Help command works');
} catch (error) {
  console.error('✗ Help command failed:', error.message);
  process.exit(1);
}

// Test 4: Verify that the complexity module is available
try {
  const { complexityWorkflow } = await import('../src/workflow/complexity-workflow.js');
  assert(typeof complexityWorkflow === 'object', 'Complexity workflow module is not available');
  console.log('✓ Complexity workflow module is available');
} catch (error) {
  console.error('✗ Complexity workflow module is not available:', error.message);
  process.exit(1);
}

// Test 5: Verify that the task execution module is available
try {
  const { executeTask } = await import('../src/workflow/task-execution.js');
  assert(typeof executeTask === 'function', 'Task execution module is not available');
  console.log('✓ Task execution module is available');
} catch (error) {
  console.error('✗ Task execution module is not available:', error.message);
  process.exit(1);
}

// Test 6: Verify that the task verification module is available
try {
  const { verifyTask } = await import('../src/workflow/task-verification.js');
  assert(typeof verifyTask === 'function', 'Task verification module is not available');
  console.log('✓ Task verification module is available');
} catch (error) {
  console.error('✗ Task verification module is not available:', error.message);
  process.exit(1);
}

console.log('All basic tests passed!');
