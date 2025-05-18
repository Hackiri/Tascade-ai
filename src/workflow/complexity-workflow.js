/**
 * complexity-workflow.js
 * Task complexity workflow for Tascade AI
 * 
 * This module implements a workflow similar to Claude Task Master
 * for managing task complexity in Tascade AI.
 */

import chalk from 'chalk';
import inquirer from 'inquirer';
import ora from 'ora';
import gradient from 'gradient-string';
import boxen from 'boxen';
import { assessTaskComplexity, COMPLEXITY_LEVEL, getComplexityColor } from '../utils/enhanced_task_complexity.js';
import * as ui from '../cli/ui.js';
import { suggestTaskSplitting } from '../utils/task_splitter.js';
import { generateVerificationCriteria, formatVerificationCriteria } from '../utils/verification_generator.js';
import { 
  integrateComplexityWithTask,
  analyzeDependenciesByComplexity,
  calculateComplexityBasedProgress
} from '../utils/feature_integration.js';

/**
 * Analyze task complexity and provide recommendations
 * @param {Object} task - The task to analyze
 * @param {Object} options - Analysis options
 * @param {boolean} options.detailed - Whether to show detailed analysis
 * @param {boolean} options.interactive - Whether to run in interactive mode
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Analysis results
 */
export async function analyzeTaskComplexity(task, options = {}, client) {
  const spinner = ui.startSpinner(`Analyzing complexity of task ${task.id}...`);
  
  try {
    // Assess task complexity
    const complexityAssessment = assessTaskComplexity(task);
    
    // Update task with complexity assessment if connected to server
    if (client) {
      try {
        await client.send('update-task', {
          id: task.id,
          complexity: {
            level: complexityAssessment.level,
            score: complexityAssessment.overallScore,
            assessedAt: new Date().toISOString()
          }
        });
      } catch (error) {
        console.warn(chalk.yellow(`Warning: Could not update task on server: ${error.message}`));
      }
    }
    
    ui.stopSpinner(spinner, 'Complexity analysis completed', 'success');
    
    // Display complexity assessment
    console.log(ui.displayComplexityAssessment(complexityAssessment));
    
    // Provide recommendations based on complexity
    const recommendations = [];
    
    // Check if task should be split based on complexity level
    if (complexityAssessment.level === COMPLEXITY_LEVEL.HIGH || 
        complexityAssessment.level === COMPLEXITY_LEVEL.VERY_HIGH) {
      recommendations.push({
        type: 'split',
        message: 'This task is complex and should be split into smaller subtasks',
        command: `tascade-cli tasks --suggest-splitting ${task.id}`
      });
    }
    
    // Generate verification criteria
    const criteria = generateVerificationCriteria(task);
    if (criteria.length > 0) {
      recommendations.push({
        type: 'verify',
        message: 'Add verification criteria based on complexity',
        command: `tascade-cli tasks --add-verification ${task.id}`
      });
    }
    
    // Display recommendations
    if (recommendations.length > 0) {
      console.log('\n' + chalk.bold('Recommendations:'));
      recommendations.forEach(rec => {
        console.log(`  ${chalk.cyan('•')} ${rec.message}`);
        console.log(`    ${chalk.dim('Run:')} ${chalk.green(rec.command)}`);
      });
    }
    
    // Interactive mode - prompt for next actions
    if (options.interactive && recommendations.length > 0) {
      const { action } = await inquirer.prompt([
        {
          type: 'list',
          name: 'action',
          message: 'What would you like to do next?',
          choices: [
            ...recommendations.map(rec => ({ name: rec.message, value: rec.type })),
            { name: 'Nothing, return to main menu', value: 'none' }
          ]
        }
      ]);
      
      if (action === 'split') {
        return await suggestTaskSplitting(task, options, client);
      } else if (action === 'verify') {
        return await generateVerificationCriteria(task, options, client);
      }
    }
    
    return {
      task,
      complexity: complexityAssessment,
      recommendations
    };
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to analyze task complexity: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Suggest how to split a complex task into smaller subtasks
 * @param {Object} task - The task to split
 * @param {Object} options - Splitting options
 * @param {number} options.maxSubtasks - Maximum number of subtasks to create
 * @param {boolean} options.interactive - Whether to run in interactive mode
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Splitting results
 */
export async function suggestTaskSplittingWorkflow(task, options = {}, client) {
  const spinner = ui.startSpinner(`Generating splitting suggestions for task ${task.id}...`);
  
  try {
    // Ensure task has complexity assessment
    if (!task.complexity) {
      const complexityAssessment = assessTaskComplexity(task);
      task.complexity = {
        level: complexityAssessment.level,
        score: complexityAssessment.overallScore,
        assessedAt: new Date().toISOString()
      };
    }
    
    // Only suggest splitting for high or very high complexity tasks
    if (task.complexity.level !== COMPLEXITY_LEVEL.HIGH && 
        task.complexity.level !== COMPLEXITY_LEVEL.VERY_HIGH) {
      ui.stopSpinner(spinner, `Task complexity (${task.complexity.level}) is not high enough to warrant splitting`, 'info');
      return {
        canSplit: false,
        reason: `Task complexity (${task.complexity.level}) is not high enough to warrant splitting`
      };
    }
    
    // Generate subtask suggestions
    let subtaskSuggestions;
    
    if (client) {
      try {
        // Try to get suggestions from server
        const result = await client.send('suggest-task-splitting', {
          taskId: task.id,
          maxSubtasks: options.maxSubtasks || 5
        });
        subtaskSuggestions = result.subtaskSuggestions;
      } catch (error) {
        // Fall back to local generation
        console.warn(chalk.yellow(`Warning: Could not get suggestions from server: ${error.message}`));
        const { default: taskSplitter } = await import('../utils/task_splitter.js');
        subtaskSuggestions = taskSplitter.suggestTaskSplitting(task, { maxSubtasks: options.maxSubtasks || 5 });
      }
    } else {
      // Local generation using our enhanced task splitter
      const { default: taskSplitter } = await import('../utils/task_splitter.js');
      subtaskSuggestions = taskSplitter.suggestTaskSplitting(task, { maxSubtasks: options.maxSubtasks || 5 });
    }
    
    ui.stopSpinner(spinner, 'Splitting suggestions generated', 'success');
    
    // Display subtask suggestions
    console.log('\n' + chalk.bold('Suggested Subtasks:'));
    subtaskSuggestions.forEach((subtask, index) => {
      console.log(`\n${chalk.cyan(`${index + 1}.`)} ${chalk.bold(subtask.title)}`);
      console.log(`   ${chalk.dim('Description:')} ${subtask.description}`);
      console.log(`   ${chalk.dim('Priority:')} ${subtask.priority}`);
      console.log(`   ${chalk.dim('Estimated Hours:')} ${subtask.estimatedHours}`);
    });
    
    // Interactive mode - prompt for applying suggestions
    if (options.interactive) {
      const { apply } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'apply',
          message: 'Would you like to apply these subtask suggestions?',
          default: false
        }
      ]);
      
      if (apply && client) {
        const applySpinner = ui.startSpinner('Applying subtask suggestions...');
        
        try {
          // Clear existing subtasks if any
          if (task.subtasks && task.subtasks.length > 0) {
            await client.send('clear-subtasks', { taskId: task.id });
          }
          
          // Add new subtasks
          for (const subtask of subtaskSuggestions) {
            await client.send('add-subtask', {
              taskId: task.id,
              subtask
            });
          }
          
          ui.stopSpinner(applySpinner, 'Subtasks applied successfully', 'success');
        } catch (error) {
          ui.stopSpinner(applySpinner, `Failed to apply subtasks: ${error.message}`, 'error');
        }
      }
    }
    
    return {
      canSplit: true,
      task,
      subtaskSuggestions
    };
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to generate splitting suggestions: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Generate verification criteria based on task complexity
 * @param {Object} task - The task to generate criteria for
 * @param {Object} options - Generation options
 * @param {boolean} options.interactive - Whether to run in interactive mode
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Generation results
 */
export async function generateVerificationCriteriaWorkflow(task, options = {}, client) {
  const spinner = ui.startSpinner(`Generating verification criteria for task ${task.id}...`);
  
  try {
    // Ensure task has complexity assessment
    if (!task.complexity) {
      const complexityAssessment = assessTaskComplexity(task);
      task.complexity = {
        level: complexityAssessment.level,
        score: complexityAssessment.overallScore,
        assessedAt: new Date().toISOString()
      };
    }
    
    // Generate verification criteria
    let verificationCriteria;
    
    if (client) {
      try {
        // Try to get criteria from server
        const result = await client.send('verify-by-complexity', {
          taskId: task.id
        });
        verificationCriteria = result.verificationCriteria;
      } catch (error) {
        // Fall back to local generation
        console.warn(chalk.yellow(`Warning: Could not get criteria from server: ${error.message}`));
        const { default: verificationGenerator } = await import('../utils/verification_generator.js');
        verificationCriteria = verificationGenerator.generateVerificationCriteria(task);
      }
    } else {
      // Local generation using our enhanced verification generator
      const { default: verificationGenerator } = await import('../utils/verification_generator.js');
      verificationCriteria = verificationGenerator.generateVerificationCriteria(task);
    }
    
    ui.stopSpinner(spinner, 'Verification criteria generated', 'success');
    
    // Display verification criteria
    console.log('\n' + chalk.bold('Suggested Verification Criteria:'));
    verificationCriteria.forEach((criterion, index) => {
      const requirementLabel = criterion.required ? chalk.red('[Required]') : chalk.blue('[Optional]');
      console.log(`${chalk.cyan(`${index + 1}.`)} ${criterion.description} ${requirementLabel} ${chalk.dim(`[${criterion.type}]`)}`);
    });
    
    // Interactive mode - prompt for applying criteria
    if (options.interactive) {
      const { apply } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'apply',
          message: 'Would you like to apply these verification criteria?',
          default: false
        }
      ]);
      
      if (apply && client) {
        const applySpinner = ui.startSpinner('Applying verification criteria...');
        
        try {
          // Clear existing criteria if any
          if (task.verificationCriteria && task.verificationCriteria.length > 0) {
            await client.send('clear-verification-criteria', { taskId: task.id });
          }
          
          // Add new criteria
          for (const criterion of verificationCriteria) {
            await client.send('add-verification-criterion', {
              taskId: task.id,
              criterion
            });
          }
          
          ui.stopSpinner(applySpinner, 'Verification criteria applied successfully', 'success');
        } catch (error) {
          ui.stopSpinner(applySpinner, `Failed to apply verification criteria: ${error.message}`, 'error');
        }
      }
    }
    
    return {
      task,
      verificationCriteria
    };
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to generate verification criteria: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Calculate and display project complexity metrics
 * @param {Array} tasks - Array of tasks
 * @param {Object} options - Display options
 * @param {boolean} options.detailed - Whether to show detailed metrics
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Metrics results
 */
export async function displayComplexityMetrics(tasks, options = {}, client) {
  const spinner = ui.startSpinner('Calculating project complexity metrics...');
  
  try {
    // Ensure all tasks have complexity assessment
    const enhancedTasks = tasks.map(task => {
      if (!task.complexity) {
        const complexityAssessment = assessTaskComplexity(task);
        task.complexity = {
          level: complexityAssessment.level,
          score: complexityAssessment.overallScore,
          assessedAt: new Date().toISOString()
        };
      }
      return task;
    });
    
    // Calculate complexity metrics
    const metrics = calculateComplexityBasedProgress(enhancedTasks);
    
    ui.stopSpinner(spinner, 'Complexity metrics calculated', 'success');
    
    // Display complexity metrics
    console.log('\n' + gradient.pastel.multiline(boxen(
      chalk.bold('Project Complexity Metrics'),
      {
        padding: 1,
        margin: 0,
        borderStyle: 'round',
        borderColor: 'cyan'
      }
    )));
    
    console.log('\n' + chalk.bold('Task Count by Complexity:'));
    Object.entries(metrics.tasksByComplexity).forEach(([level, levelTasks]) => {
      const levelFormatted = level.charAt(0).toUpperCase() + level.slice(1).replace('_', ' ');
      const color = ui.getComplexityColor(level);
      console.log(`${color(levelFormatted)}: ${levelTasks.length} tasks`);
    });
    
    console.log('\n' + chalk.bold('Completion by Complexity:'));
    Object.entries(metrics.completionByComplexity).forEach(([level, data]) => {
      if (data.total > 0) {
        const levelFormatted = level.charAt(0).toUpperCase() + level.slice(1).replace('_', ' ');
        const color = ui.getComplexityColor(level);
        console.log(`${color(levelFormatted)}: ${data.completed}/${data.total} (${Math.round(data.percentage)}%)`);
      }
    });
    
    console.log('\n' + chalk.bold(`Weighted Progress: ${Math.round(metrics.weightedProgress)}%`));
    console.log(ui.createProgressBar(metrics.weightedProgress));
    
    // Display detailed metrics if requested
    if (options.detailed) {
      console.log('\n' + chalk.bold('Complexity Distribution:'));
      Object.entries(metrics.complexityDistribution).forEach(([level, percentage]) => {
        const levelFormatted = level.charAt(0).toUpperCase() + level.slice(1).replace('_', ' ');
        const color = ui.getComplexityColor(level);
        console.log(`${color(levelFormatted)}: ${Math.round(percentage)}%`);
      });
      
      console.log('\n' + chalk.bold(`Average Complexity Score: ${metrics.avgComplexityScore.toFixed(2)}`));
    }
    
    return metrics;
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to calculate complexity metrics: ${error.message}`, 'error');
    throw error;
  }
}

// Note: We've removed the local subtask suggestion and key phrase extraction functions
// as they're now handled by our enhanced task_splitter.js utility

export default {
  analyzeTaskComplexity,
  suggestTaskSplitting: suggestTaskSplittingWorkflow,
  generateVerificationCriteria: generateVerificationCriteriaWorkflow,
  displayComplexityMetrics
};
