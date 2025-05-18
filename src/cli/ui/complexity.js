/**
 * complexity.js
 * UI components for visualizing task complexity
 */

import chalk from 'chalk';
import gradient from 'gradient-string';
import boxen from 'boxen';
import { COMPLEXITY_LEVEL, formatComplexityLevel } from '../../utils/task_complexity.js';

/**
 * Get color for a complexity level
 * @param {string} level - Complexity level
 * @returns {Function} Chalk color function
 */
export function getComplexityColor(level) {
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      return chalk.green;
    case COMPLEXITY_LEVEL.MEDIUM:
      return chalk.yellow;
    case COMPLEXITY_LEVEL.HIGH:
      return chalk.red;
    case COMPLEXITY_LEVEL.VERY_HIGH:
      return chalk.bgRed.white;
    default:
      return chalk.white;
  }
}

/**
 * Create a visual complexity indicator
 * @param {string} level - Complexity level
 * @returns {string} Visual complexity indicator
 */
export function createComplexityIndicator(level) {
  const color = getComplexityColor(level);
  const formattedLevel = formatComplexityLevel(level);
  
  // Create visual bars based on complexity
  let bars;
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      bars = '▮▯▯▯';
      break;
    case COMPLEXITY_LEVEL.MEDIUM:
      bars = '▮▮▯▯';
      break;
    case COMPLEXITY_LEVEL.HIGH:
      bars = '▮▮▮▯';
      break;
    case COMPLEXITY_LEVEL.VERY_HIGH:
      bars = '▮▮▮▮';
      break;
    default:
      bars = '▯▯▯▯';
  }
  
  return `${color(bars)} ${color(formattedLevel)}`;
}

/**
 * Display task complexity assessment
 * @param {Object} complexity - Complexity assessment result
 * @returns {string} Formatted complexity display
 */
export function displayComplexityAssessment(complexity) {
  const { level, metrics, scores, recommendations } = complexity;
  const color = getComplexityColor(level);
  
  let output = '';
  
  // Header with consistent style
  output += '\n' + chalk.bold('Task Complexity Assessment:');
  output += '\n' + chalk.dim('─'.repeat(50)) + '\n';
  
  // Complexity level with color
  output += `${chalk.bold('Complexity:')} ${color(formatComplexityLevel(level))}\n`;
  
  // Overall score
  output += `${chalk.bold('Score:')} ${formatScore(complexity.overallScore)}\n`;
  
  // Metrics section with consistent formatting
  output += '\n' + chalk.bold('Metrics:');
  output += `\n  ${chalk.bold('Description:')} ${metrics.descriptionLength} characters ${getScoreIndicator(scores.description)}`;
  output += `\n  ${chalk.bold('Subtasks:')} ${metrics.subtasksCount} ${getScoreIndicator(scores.subtasks)}`;
  output += `\n  ${chalk.bold('Dependencies:')} ${metrics.dependenciesCount} ${getScoreIndicator(scores.dependencies)}`;
  
  // Recommendations section with consistent formatting
  if (recommendations && recommendations.length > 0) {
    output += '\n\n' + chalk.bold('Recommendations:');
    recommendations.forEach(rec => {
      output += `\n  ${chalk.cyan('•')} ${rec}`;
    });
  }
  
  output += '\n' + chalk.dim('─'.repeat(50));
  
  return output;
}

/**
 * Format a complexity score for display
 * @param {number} score - Complexity score
 * @returns {string} Formatted score
 */
function formatScore(score) {
  const formattedScore = score.toFixed(2);
  
  if (score >= 2.5) {
    return chalk.bgRed.white(` ${formattedScore} `);
  } else if (score >= 1.7) {
    return chalk.red(formattedScore);
  } else if (score >= 0.8) {
    return chalk.yellow(formattedScore);
  } else {
    return chalk.green(formattedScore);
  }
}

/**
 * Get visual indicator for a score
 * @param {number} score - Score (0-3)
 * @returns {string} Visual score indicator
 */
function getScoreIndicator(score) {
  switch (score) {
    case 0:
      return chalk.green('(Low)');
    case 1:
      return chalk.yellow('(Medium)');
    case 2:
      return chalk.red('(High)');
    case 3:
      return chalk.bgRed.white('(Very High)');
    default:
      return '';
  }
}
