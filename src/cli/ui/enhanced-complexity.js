/**
 * enhanced-complexity.js
 * Enhanced UI components for displaying task complexity in Tascade AI
 * Incorporates visual styling from Claude Task Master
 */

import chalk from 'chalk';
import boxen from 'boxen';
import gradient from 'gradient-string';
import { COMPLEXITY_LEVEL, getComplexityColor } from '../../utils/enhanced_task_complexity.js';

/**
 * Create a visual complexity badge
 * @param {string} level - Complexity level
 * @returns {string} Formatted complexity badge
 */
export function createComplexityBadge(level) {
  const color = getComplexityColor(level);
  const formattedLevel = level.toUpperCase().replace('_', ' ');
  
  return color(`[${formattedLevel} COMPLEXITY]`);
}

/**
 * Create a visual complexity indicator
 * @param {string} level - Complexity level
 * @returns {string} Visual complexity indicator
 */
export function createComplexityIndicator(level) {
  const color = getComplexityColor(level);
  let indicator = '';
  
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      indicator = '●';
      break;
    case COMPLEXITY_LEVEL.MEDIUM:
      indicator = '●●';
      break;
    case COMPLEXITY_LEVEL.HIGH:
      indicator = '●●●';
      break;
    case COMPLEXITY_LEVEL.VERY_HIGH:
      indicator = '●●●●';
      break;
    default:
      indicator = '○';
  }
  
  return color(indicator);
}

/**
 * Create a progress bar
 * @param {number} percentage - Percentage value (0-100)
 * @param {number} width - Width of the progress bar
 * @returns {string} Formatted progress bar
 */
export function createProgressBar(percentage, width = 30) {
  const filledWidth = Math.round((percentage / 100) * width);
  const emptyWidth = width - filledWidth;
  
  let color;
  if (percentage < 30) {
    color = chalk.red;
  } else if (percentage < 70) {
    color = chalk.yellow;
  } else {
    color = chalk.green;
  }
  
  const filled = color('█'.repeat(filledWidth));
  const empty = chalk.gray('░'.repeat(emptyWidth));
  
  return `${filled}${empty} ${percentage.toFixed(0)}%`;
}

/**
 * Display complexity assessment in a visually appealing way
 * @param {Object} assessment - Complexity assessment object
 * @returns {string} Formatted complexity assessment
 */
export function displayComplexityAssessment(assessment) {
  const { level, overallScore, metrics, recommendations } = assessment;
  const color = getComplexityColor(level);
  
  // Create header
  const header = gradient.pastel.multiline(boxen(
    chalk.bold(`Task Complexity Assessment: ${color(level.toUpperCase().replace('_', ' '))}`),
    {
      padding: 1,
      margin: 0,
      borderStyle: 'round',
      borderColor: 'cyan'
    }
  ));
  
  // Format metrics
  const formattedMetrics = [
    `${chalk.bold('Overall Score:')} ${createProgressBar(overallScore)}`,
    `${chalk.bold('Description Length:')} ${metrics.descriptionLength} characters`,
    `${chalk.bold('Dependencies:')} ${metrics.dependenciesCount}`,
    `${chalk.bold('Subtasks:')} ${metrics.subtasksCount}`
  ];
  
  if (metrics.notesLength > 0) {
    formattedMetrics.push(`${chalk.bold('Notes Length:')} ${metrics.notesLength} characters`);
  }
  
  if (metrics.implementationGuideLength > 0) {
    formattedMetrics.push(`${chalk.bold('Implementation Guide Length:')} ${metrics.implementationGuideLength} characters`);
  }
  
  if (metrics.verificationCriteriaLength > 0) {
    formattedMetrics.push(`${chalk.bold('Verification Criteria Length:')} ${metrics.verificationCriteriaLength} characters`);
  }
  
  // Format recommendations
  const formattedRecommendations = recommendations.map((rec, index) => {
    return `${chalk.cyan(`${index + 1}.`)} ${rec}`;
  });
  
  // Combine all sections
  return [
    header,
    '',
    chalk.bold('Metrics:'),
    ...formattedMetrics,
    '',
    chalk.bold('Recommendations:'),
    ...formattedRecommendations
  ].join('\n');
}

/**
 * Display complexity distribution in a task list
 * @param {Array} tasks - Array of tasks
 * @returns {string} Formatted complexity distribution
 */
export function displayComplexityDistribution(tasks) {
  // Count tasks by complexity level
  const counts = {
    [COMPLEXITY_LEVEL.LOW]: 0,
    [COMPLEXITY_LEVEL.MEDIUM]: 0,
    [COMPLEXITY_LEVEL.HIGH]: 0,
    [COMPLEXITY_LEVEL.VERY_HIGH]: 0,
    unknown: 0
  };
  
  tasks.forEach(task => {
    if (task.complexity && task.complexity.level) {
      counts[task.complexity.level]++;
    } else {
      counts.unknown++;
    }
  });
  
  // Create distribution display
  const total = tasks.length;
  const distribution = [];
  
  Object.entries(counts).forEach(([level, count]) => {
    if (count > 0 && level !== 'unknown') {
      const color = getComplexityColor(level);
      const percentage = ((count / total) * 100).toFixed(0);
      const formattedLevel = level.toUpperCase().replace('_', ' ');
      distribution.push(`${color(`${formattedLevel}:`)} ${count} (${percentage}%)`);
    }
  });
  
  if (counts.unknown > 0) {
    const percentage = ((counts.unknown / total) * 100).toFixed(0);
    distribution.push(`${chalk.gray('UNKNOWN:')} ${counts.unknown} (${percentage}%)`);
  }
  
  return boxen(
    [
      chalk.bold('Complexity Distribution:'),
      ...distribution
    ].join('\n'),
    {
      padding: 1,
      margin: 0,
      borderStyle: 'round',
      borderColor: 'cyan'
    }
  );
}

/**
 * Create a compact complexity indicator for task lists
 * @param {Object} task - Task object
 * @returns {string} Compact complexity indicator
 */
export function createCompactComplexityIndicator(task) {
  if (!task.complexity || !task.complexity.level) {
    return chalk.gray('○');
  }
  
  const level = task.complexity.level;
  const color = getComplexityColor(level);
  
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      return color('●');
    case COMPLEXITY_LEVEL.MEDIUM:
      return color('●●');
    case COMPLEXITY_LEVEL.HIGH:
      return color('●●●');
    case COMPLEXITY_LEVEL.VERY_HIGH:
      return color('●●●●');
    default:
      return chalk.gray('○');
  }
}

export default {
  createComplexityBadge,
  createComplexityIndicator,
  createProgressBar,
  displayComplexityAssessment,
  displayComplexityDistribution,
  createCompactComplexityIndicator
};
