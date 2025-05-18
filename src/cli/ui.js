/**
 * ui.js
 * User interface functions for the Tascade AI CLI
 * Inspired by claude-task-master's UI approach
 */

import chalk from 'chalk';
import boxen from 'boxen';
import ora from 'ora';
import Table from 'cli-table3';
import gradient from 'gradient-string';
import path from 'path';
import fs from 'fs';
import * as complexityUI from './ui/complexity.js';

// Create color gradients for visual elements
const primaryGradient = gradient(['#00b4d8', '#0077b6', '#03045e']);
const secondaryGradient = gradient(['#fb8b24', '#e36414', '#9a031e']);

/**
 * Display a banner for the CLI
 * @param {string} title - Title to display in the banner
 * @param {string} version - Version number
 * @param {string} projectName - Current project name
 */
export function displayBanner(title = 'Tascade AI', version = '1.0.0', projectName = '') {
  console.clear();
  
  // Create banner text with gradient
  const bannerText = primaryGradient(title);
  console.log('\n' + bannerText);
  
  // Add version and project info in a box
  console.log(
    boxen(
      chalk.white(
        `${chalk.bold('Version:')} ${version}   ${chalk.bold('Project:')} ${projectName || 'Not set'}`
      ),
      {
        padding: 1,
        margin: { top: 1, bottom: 1 },
        borderStyle: 'round',
        borderColor: 'cyan'
      }
    )
  );
}

/**
 * Start a loading indicator with an animated spinner
 * @param {string} message - Message to display next to the spinner
 * @returns {Object} Spinner object
 */
export function startSpinner(message) {
  const spinner = ora({
    text: message,
    color: 'cyan'
  }).start();

  return spinner;
}

/**
 * Stop a loading indicator
 * @param {Object} spinner - Spinner object to stop
 * @param {string} finalMessage - Final message to display
 * @param {string} status - Status of the operation ('success', 'error', 'warn', 'info')
 */
export function stopSpinner(spinner, finalMessage = '', status = 'success') {
  if (spinner && spinner.stop) {
    if (finalMessage) {
      // Check if the status method exists, otherwise fall back to stop
      if (status === 'success' && typeof spinner.succeed === 'function') {
        spinner.succeed(finalMessage);
      } else if (status === 'error' && typeof spinner.fail === 'function') {
        spinner.fail(finalMessage);
      } else if (status === 'warn' && typeof spinner.warn === 'function') {
        spinner.warn(finalMessage);
      } else if (status === 'info' && typeof spinner.info === 'function') {
        spinner.info(finalMessage);
      } else {
        spinner.stop();
        console.log(`${finalMessage}`);
      }
    } else {
      spinner.stop();
    }
  }
}

/**
 * Create a colored progress bar
 * @param {number} percent - The completion percentage
 * @param {number} length - The total length of the progress bar in characters
 * @param {Object} statusBreakdown - Optional breakdown of statuses (e.g., {pending: 20, 'in-progress': 10})
 * @returns {string} The formatted progress bar
 */
export function createProgressBar(percent, length = 30, statusBreakdown = null) {
  // Calculate how many characters to fill
  const filled = Math.round((percent * length) / 100);
  const empty = length - filled;
  
  // Determine color based on percentage
  let barColor;
  if (percent < 25) {
    barColor = chalk.red;
  } else if (percent < 50) {
    barColor = chalk.hex('#FFA500'); // Orange
  } else if (percent < 75) {
    barColor = chalk.yellow;
  } else if (percent < 100) {
    barColor = chalk.green;
  } else {
    barColor = chalk.hex('#006400'); // Dark green
  }
  
  // Create the bar
  const completedSection = barColor('█'.repeat(filled));
  const emptySection = chalk.gray('░'.repeat(empty));
  
  return `${completedSection}${emptySection} ${percent}%`;
}

/**
 * Get a colored status string based on the status value
 * @param {string} status - Task status (e.g., "done", "pending", "in-progress")
 * @returns {string} Colored status string
 */
export function getStatusWithColor(status) {
  const statusConfig = {
    done: { color: chalk.green, symbol: '✓' },
    completed: { color: chalk.green, symbol: '✓' },
    pending: { color: chalk.yellow, symbol: '○' },
    'in-progress': { color: chalk.hex('#FFA500'), symbol: '◑' }, // Orange
    blocked: { color: chalk.red, symbol: '✗' },
    review: { color: chalk.magenta, symbol: '⟳' },
    deferred: { color: chalk.gray, symbol: '⊘' },
    cancelled: { color: chalk.gray, symbol: '⊗' }
  };
  
  const config = statusConfig[status.toLowerCase()] || { color: chalk.white, symbol: '?' };
  return config.color(`${config.symbol} ${status}`);
}

/**
 * Create a formatted table for displaying data
 * @param {Array} headers - Table headers
 * @param {Array} data - Table data (array of arrays)
 * @param {Object} options - Table options
 * @returns {string} Formatted table
 */
export function createTable(headers, data, options = {}) {
  const tableConfig = {
    head: headers.map(header => chalk.cyan(header)),
    chars: {
      'top': '─',
      'top-mid': '┬',
      'top-left': '┌',
      'top-right': '┐',
      'bottom': '─',
      'bottom-mid': '┴',
      'bottom-left': '└',
      'bottom-right': '┘',
      'left': '│',
      'left-mid': '├',
      'mid': '─',
      'mid-mid': '┼',
      'right': '│',
      'right-mid': '┤',
      'middle': '│'
    },
    ...options
  };
  
  const table = new Table(tableConfig);
  
  // Add rows to the table
  data.forEach(row => {
    table.push(row);
  });
  
  return table.toString();
}

/**
 * Display a boxed message
 * @param {string} message - Message to display
 * @param {string} type - Message type ('info', 'success', 'warning', 'error')
 */
export function displayBox(message, type = 'info') {
  const typeConfig = {
    info: { borderColor: 'blue', title: 'INFO' },
    success: { borderColor: 'green', title: 'SUCCESS' },
    warning: { borderColor: 'yellow', title: 'WARNING' },
    error: { borderColor: 'red', title: 'ERROR' }
  };
  
  const config = typeConfig[type] || typeConfig.info;
  
  console.log(
    boxen(message, {
      padding: 1,
      margin: 1,
      borderStyle: 'round',
      borderColor: config.borderColor,
      title: config.title,
      titleAlignment: 'center'
    })
  );
}

/**
 * Truncate a string to a maximum length and add ellipsis if needed
 * @param {string} str - The string to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
export function truncateString(str, maxLength = 80) {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

/**
 * Display task generation results in a visually appealing way
 * @param {Array} tasks - Array of generated tasks
 */
export function displayTaskGenerationResults(tasks) {
  if (!tasks || tasks.length === 0) {
    displayBox('No tasks were generated.', 'warning');
    return;
  }
  
  console.log('\n' + chalk.bold('Task Generation Results:'));
  console.log(chalk.dim('─'.repeat(50)));
  
  // Track task priorities for analytics
  const priorityCounts = { high: 0, medium: 0, low: 0 };
  
  tasks.forEach(task => {
    const priorityColor = {
      high: chalk.red,
      medium: chalk.yellow,
      low: chalk.green
    }[task.priority] || chalk.white;
    
    // Count priorities
    if (priorityCounts[task.priority] !== undefined) {
      priorityCounts[task.priority]++;
    }
    
    console.log(`${chalk.cyan(`#${task.id}`)} ${chalk.bold(task.title)}`);
    console.log(`  Priority: ${priorityColor(task.priority)}`);
    console.log(`  Dependencies: ${task.dependencies && task.dependencies.length ? task.dependencies.join(', ') : 'None'}`);
    
    // Show a truncated description if available
    if (task.description) {
      console.log(`  Description: ${chalk.dim(truncateString(task.description))}`);
    }
    
    console.log(chalk.dim('─'.repeat(50)));
  });
  
  // Display priority breakdown
  const total = tasks.length;
  console.log('\n' + chalk.bold('Priority Breakdown:'));
  console.log(`High: ${chalk.red(priorityCounts.high)} (${Math.round((priorityCounts.high / total) * 100)}%)`);
  console.log(`Medium: ${chalk.yellow(priorityCounts.medium)} (${Math.round((priorityCounts.medium / total) * 100)}%)`);
  console.log(`Low: ${chalk.green(priorityCounts.low)} (${Math.round((priorityCounts.low / total) * 100)}%)`);
}

/**
 * Display help information for a command
 * @param {string} command - Command name
 * @param {string} description - Command description
 * @param {Array} options - Command options
 * @param {Array} examples - Command examples
 */
export function displayCommandHelp(command, description, options = [], examples = []) {
  console.log('\n' + chalk.bold(`Command: ${chalk.cyan(command)}`));
  console.log(description + '\n');
  
  if (options.length > 0) {
    console.log(chalk.bold('Options:'));
    options.forEach(option => {
      console.log(`  ${chalk.cyan(option.flags.padEnd(20))} ${option.description}`);
    });
    console.log('');
  }
  
  if (examples.length > 0) {
    console.log(chalk.bold('Examples:'));
    examples.forEach(example => {
      console.log(`  ${chalk.cyan(example.command)}`);
      console.log(`  ${example.description}`);
      console.log('');
    });
  }
}

/**
 * Display a comprehensive help guide for all commands
 * @param {Array} commands - Array of command objects
 */
export function displayHelp(commands) {
  displayBanner();
  
  console.log(chalk.bold('\nAvailable Commands:'));
  console.log(chalk.dim('─'.repeat(50)));
  
  commands.forEach(cmd => {
    console.log(`${chalk.cyan(cmd.name.padEnd(20))} ${cmd.description}`);
  });
  
  console.log('\n' + chalk.bold('For command-specific help, use:'));
  console.log(chalk.cyan('  tascade-ai <command> --help'));
  
  console.log('\n' + chalk.bold('Examples:'));
  console.log(chalk.cyan('  tascade-ai generate-tasks --help'));
  console.log(chalk.cyan('  tascade-ai generate-tasks --input-file=prd.md --output-file=tasks.json'));
}

/**
 * Display error message
 * @param {string} message - Error message
 * @param {Error} error - Error object (optional)
 */
export function displayError(message, error = null) {
  console.error(chalk.red('\n✖ Error: ' + message));
  
  if (error && error.stack && process.env.DEBUG === 'true') {
    console.error(chalk.dim('\nStack trace:'));
    console.error(chalk.dim(error.stack));
  }
}

/**
 * Display success message
 * @param {string} message - Success message
 */
export function displaySuccess(message) {
  console.log(chalk.green('\n✓ Success: ' + message));
}

/**
 * Display warning message
 * @param {string} message - Warning message
 */
export function displayWarning(message) {
  console.log(chalk.yellow('\n⚠ Warning: ' + message));
}

/**
 * Display information message
 * @param {string} message - Information message
 */
export function displayInfo(message) {
  console.log(chalk.blue('\nℹ Info: ' + message));
}

/**
 * Display MCP connection status
 * @param {Object} status - Connection status object
 */
export function displayMCPStatus(status) {
  const { connected, url, contextId, reconnectAttempts } = status;
  
  const statusColor = connected ? chalk.green : chalk.red;
  const statusText = connected ? 'Connected' : 'Disconnected';
  
  console.log(
    boxen(
      `${chalk.bold('MCP Status:')} ${statusColor(statusText)}\n` +
      `${chalk.bold('URL:')} ${url}\n` +
      `${chalk.bold('Context ID:')} ${contextId || 'None'}\n` +
      `${chalk.bold('Reconnect Attempts:')} ${reconnectAttempts || 0}`,
      {
        padding: 1,
        margin: 1,
        borderStyle: 'round',
        borderColor: connected ? 'green' : 'red',
        title: 'MCP Connection',
        titleAlignment: 'center'
      }
    )
  );
}

/**
 * Format a duration in milliseconds to a human-readable string
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(ms) {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(2);
    return `${minutes}m ${seconds}s`;
  }
}

/**
 * Display performance metrics
 * @param {Object} metrics - Performance metrics object
 */
export function displayPerformanceMetrics(metrics) {
  const table = new Table({
    head: [chalk.cyan('Metric'), chalk.cyan('Value')],
    colWidths: [30, 20]
  });
  
  Object.entries(metrics).forEach(([key, value]) => {
    let formattedValue = value;
    
    // Format durations
    if (key.includes('time') || key.includes('duration')) {
      formattedValue = formatDuration(value);
    }
    
    // Format percentages
    if (key.includes('rate') || key.includes('percentage')) {
      formattedValue = `${value}%`;
    }
    
    table.push([key, formattedValue]);
  });
  
  console.log('\n' + chalk.bold('Performance Metrics:'));
  console.log(table.toString());
}

// Export all UI functions
export default {
  displayBanner,
  startSpinner,
  stopSpinner,
  createProgressBar,
  getStatusWithColor,
  createTable,
  displayBox,
  truncateString,
  displayTaskGenerationResults,
  displayCommandHelp,
  displayHelp,
  displayError,
  displaySuccess,
  displayWarning,
  displayInfo,
  displayMCPStatus,
  formatDuration,
  displayPerformanceMetrics,
  
  // Complexity visualization components
  getComplexityColor: complexityUI.getComplexityColor,
  createComplexityIndicator: complexityUI.createComplexityIndicator,
  displayComplexityAssessment: complexityUI.displayComplexityAssessment
};
