/**
 * task-verification.js
 * Task verification workflow for Tascade AI
 * Based on superior implementations from MCP Shrimp Task Manager
 */

import chalk from 'chalk';
import inquirer from 'inquirer';
import ora from 'ora';
import gradient from 'gradient-string';
import boxen from 'boxen';
import * as ui from '../cli/ui.js';
import { generateVerificationCriteria } from '../utils/verification_generator.js';

/**
 * Verify a task with scoring system
 * @param {Object} task - The task to verify
 * @param {Object} options - Verification options
 * @param {boolean} options.interactive - Whether to run in interactive mode
 * @param {Object} client - MCP client for server communication
 * @returns {Promise<Object>} Verification results
 */
export async function verifyTask(task, options = {}, client) {
  const spinner = ui.startSpinner(`Preparing to verify task ${task.id}...`);
  
  try {
    // Generate verification criteria if not already available
    let verificationCriteria;
    if (task.verificationCriteria && task.verificationCriteria.length > 0) {
      verificationCriteria = task.verificationCriteria;
    } else {
      // Generate criteria locally
      const { generateVerificationCriteria: generateCriteria } = await import('../utils/verification_generator.js');
      verificationCriteria = generateCriteria(task);
      
      // Update task with verification criteria if connected to server
      if (client) {
        try {
          await client.send('update-task', {
            id: task.id,
            verificationCriteria
          });
        } catch (error) {
          console.warn(chalk.yellow(`Warning: Could not update task verification criteria on server: ${error.message}`));
        }
      }
    }
    
    ui.stopSpinner(spinner, `Ready to verify task: ${task.title}`, 'success');
    
    // Display task details and verification criteria
    console.log('\n' + gradient.pastel.multiline(boxen(
      chalk.bold(`Task Verification: ${task.title}`),
      {
        padding: 1,
        margin: 0,
        borderStyle: 'round',
        borderColor: 'cyan'
      }
    )));
    
    console.log('\n' + chalk.bold('Verification Criteria:'));
    verificationCriteria.forEach((criterion, index) => {
      const requirementLabel = criterion.required ? chalk.red('[Required]') : chalk.blue('[Optional]');
      console.log(`${chalk.cyan(`${index + 1}.`)} ${criterion.description} ${requirementLabel} ${chalk.dim(`[${criterion.type}]`)}`);
    });
    
    // Interactive mode - prompt for verification
    if (options.interactive) {
      // Collect verification results for each criterion
      const verificationResults = [];
      
      for (const criterion of verificationCriteria) {
        const { satisfied, notes } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'satisfied',
            message: `Is criterion satisfied: ${criterion.description}?`,
            default: true
          },
          {
            type: 'input',
            name: 'notes',
            message: 'Notes (optional):',
            when: (answers) => !answers.satisfied || criterion.required
          }
        ]);
        
        verificationResults.push({
          criterion,
          satisfied,
          notes: notes || ''
        });
      }
      
      // Calculate overall score
      const totalPoints = verificationCriteria.reduce((total, criterion) => {
        return total + (criterion.required ? 2 : 1);
      }, 0);
      
      const earnedPoints = verificationResults.reduce((total, result) => {
        if (result.satisfied) {
          return total + (result.criterion.required ? 2 : 1);
        }
        return total;
      }, 0);
      
      const score = Math.round((earnedPoints / totalPoints) * 100);
      
      // Display verification summary
      console.log('\n' + chalk.bold('Verification Summary:'));
      console.log(`${chalk.bold('Score:')} ${getScoreColor(score)(`${score}%`)}`);
      console.log(`${chalk.bold('Status:')} ${score >= 80 ? chalk.green('PASSED') : chalk.red('FAILED')}`);
      
      // Prompt for summary
      const { summary } = await inquirer.prompt([
        {
          type: 'input',
          name: 'summary',
          message: score >= 80 ? 'Enter completion summary:' : 'Enter failure summary:',
          validate: (input) => {
            if (input.length < 30) {
              return 'Summary must be at least 30 characters';
            }
            return true;
          }
        }
      ]);
      
      // Update task status and summary if connected to server
      if (client) {
        try {
          if (score >= 80) {
            await client.send('update-task-status', {
              id: task.id,
              status: 'completed',
              summary
            });
            
            console.log(chalk.green('\nTask marked as completed!'));
          } else {
            await client.send('update-task', {
              id: task.id,
              verificationNotes: summary
            });
            
            console.log(chalk.yellow('\nTask verification failed. Please address the issues and try again.'));
          }
        } catch (error) {
          console.error(chalk.red(`Error updating task: ${error.message}`));
        }
      }
      
      return {
        success: score >= 80,
        score,
        summary,
        results: verificationResults
      };
    }
    
    return {
      success: true,
      verificationCriteria
    };
  } catch (error) {
    ui.stopSpinner(spinner, `Failed to verify task: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Get color function for score
 * @param {number} score - Score value
 * @returns {Function} Chalk color function
 */
function getScoreColor(score) {
  if (score >= 90) {
    return chalk.green;
  } else if (score >= 80) {
    return chalk.greenBright;
  } else if (score >= 70) {
    return chalk.yellow;
  } else if (score >= 60) {
    return chalk.yellowBright;
  } else {
    return chalk.red;
  }
}

export default {
  verifyTask
};
