/**
 * task-execution.js
 * Task execution workflow for Tascade AI
 * Based on superior implementations from MCP Shrimp Task Manager
 */

import chalk from 'chalk';
import inquirer from 'inquirer';
import ora from 'ora';
import gradient from 'gradient-string';
import boxen from 'boxen';
import { assessTaskComplexity } from '../utils/enhanced_task_complexity.js';
import * as ui from '../cli/ui.js';
import { displayComplexityAssessment } from '../cli/ui/enhanced-complexity.js';
import fs from 'fs/promises';
import path from 'path';

/**
 * Execute a task with dependency checking and complexity assessment
 * @param {Object} task - The task to execute
 * @param {Object} options - Execution options
 * @param {boolean} options.interactive - Whether to run in interactive mode
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Execution results
 */
export async function executeTask(task, options = {}, client) {
  const spinner = ui.startSpinner(`Preparing to execute task ${task.id}...`);
  
  try {
    // Check if task can be executed (all dependencies completed)
    const canExecute = await checkTaskDependencies(task, client);
    
    if (!canExecute.executable) {
      ui.stopSpinner(spinner, `Task cannot be executed: ${canExecute.reason}`, 'error');
      
      if (canExecute.blockedBy && canExecute.blockedBy.length > 0) {
        console.log('\n' + chalk.bold('Blocked by:'));
        canExecute.blockedBy.forEach(dependency => {
          console.log(`  ${chalk.red('•')} ${dependency.name} (ID: ${dependency.id})`);
        });
      }
      
      return {
        success: false,
        reason: canExecute.reason,
        blockedBy: canExecute.blockedBy
      };
    }
    
    // Assess task complexity if not already assessed
    if (!task.complexity) {
      const complexityAssessment = assessTaskComplexity(task);
      task.complexity = {
        level: complexityAssessment.level,
        score: complexityAssessment.overallScore,
        assessedAt: new Date().toISOString()
      };
      
      // Update task with complexity assessment if connected to server
      if (client) {
        try {
          await client.send('update-task', {
            id: task.id,
            complexity: task.complexity
          });
        } catch (error) {
          console.warn(chalk.yellow(`Warning: Could not update task complexity on server: ${error.message}`));
        }
      }
    }
    
    // Load related files if available
    let relatedFiles = [];
    if (task.relatedFiles && task.relatedFiles.length > 0) {
      ui.stopSpinner(spinner, 'Loading related files...', 'info');
      relatedFiles = await loadRelatedFiles(task.relatedFiles);
      spinner = ui.startSpinner('Preparing to execute task...');
    }
    
    // Update task status to IN_PROGRESS if connected to server
    if (client) {
      try {
        await client.send('update-task-status', {
          id: task.id,
          status: 'in_progress'
        });
      } catch (error) {
        console.warn(chalk.yellow(`Warning: Could not update task status on server: ${error.message}`));
      }
    }
    
    ui.stopSpinner(spinner, `Ready to execute task: ${task.title}`, 'success');
    
    // Display task details and complexity assessment
    console.log('\n' + gradient.pastel.multiline(boxen(
      chalk.bold(`Task: ${task.title}`),
      {
        padding: 1,
        margin: 0,
        borderStyle: 'round',
        borderColor: 'cyan'
      }
    )));
    
    console.log('\n' + chalk.bold('Description:'));
    console.log(task.description);
    
    if (task.notes) {
      console.log('\n' + chalk.bold('Notes:'));
      console.log(task.notes);
    }
    
    if (task.implementationGuide) {
      console.log('\n' + chalk.bold('Implementation Guide:'));
      console.log(task.implementationGuide);
    }
    
    if (task.complexity) {
      console.log('\n' + chalk.bold('Complexity Assessment:'));
      console.log(displayComplexityAssessment(task.complexity));
    }
    
    if (relatedFiles.length > 0) {
      console.log('\n' + chalk.bold('Related Files:'));
      relatedFiles.forEach(file => {
        console.log(`  ${chalk.cyan('•')} ${file.path} (${file.type})`);
        if (file.content) {
          console.log(`    ${chalk.dim('Preview:')} ${file.content.substring(0, 100)}...`);
        }
      });
    }
    
    // Interactive mode - prompt for execution confirmation
    if (options.interactive) {
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: 'Do you want to proceed with task execution?',
          default: true
        }
      ]);
      
      if (!confirm) {
        return {
          success: false,
          reason: 'Execution cancelled by user'
        };
      }
    }
    
    return {
      success: true,
      task,
      relatedFiles
    };
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to execute task: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Check if a task can be executed based on its dependencies
 * @param {Object} task - The task to check
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Check results
 */
async function checkTaskDependencies(task, client) {
  if (!task.dependencies || task.dependencies.length === 0) {
    return { executable: true };
  }
  
  const blockedBy = [];
  
  if (client) {
    try {
      // Get dependency status from server
      const result = await client.send('check-dependencies', {
        taskId: task.id
      });
      
      if (!result.canExecute) {
        return {
          executable: false,
          reason: 'Task has unmet dependencies',
          blockedBy: result.blockedBy
        };
      }
      
      return { executable: true };
    } catch (error) {
      console.warn(chalk.yellow(`Warning: Could not check dependencies on server: ${error.message}`));
      // Fall back to local checking
    }
  }
  
  // Local dependency checking (simplified)
  return { executable: true };
}

/**
 * Load related files for a task
 * @param {Array} relatedFiles - Array of related file objects
 * @returns {Promise<Array>} Array of related files with content
 */
async function loadRelatedFiles(relatedFiles) {
  const loadedFiles = [];
  
  for (const file of relatedFiles) {
    try {
      const stats = await fs.stat(file.path);
      
      if (stats.isFile()) {
        const content = await fs.readFile(file.path, 'utf-8');
        loadedFiles.push({
          ...file,
          content,
          size: stats.size,
          lastModified: stats.mtime
        });
      } else {
        loadedFiles.push({
          ...file,
          content: null,
          isDirectory: true
        });
      }
    } catch (error) {
      loadedFiles.push({
        ...file,
        content: null,
        error: error.message
      });
    }
  }
  
  return loadedFiles;
}

export default {
  executeTask
};
