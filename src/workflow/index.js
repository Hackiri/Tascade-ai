/**
 * index.js
 * Workflow integration for Tascade AI
 * 
 * This module integrates all workflow components with the Tascade AI CLI,
 * following a similar approach to Claude Task Master.
 */

import chalk from 'chalk';
import gradient from 'gradient-string';
import boxen from 'boxen';
import * as complexityWorkflow from './complexity-workflow.js';
import * as taskExecution from './task-execution.js';
import * as taskVerification from './task-verification.js';

/**
 * Register workflow commands with the CLI
 * @param {Object} program - Commander program instance
 * @param {Object} client - MCP client for server communication
 */
export function registerWorkflowCommands(program, client) {
  // Task complexity workflow command
  program
    .command('complexity')
    .description('Task complexity workflow')
    .option('-a, --analyze <id>', 'Analyze complexity of a task')
    .option('-s, --suggest-splitting <id>', 'Suggest how to split a complex task')
    .option('-v, --verify <id>', 'Generate verification criteria based on complexity')
    .option('-m, --metrics', 'Show project complexity metrics')
    .option('-d, --detailed', 'Show detailed information')
    .option('-i, --interactive', 'Run in interactive mode')
    .option('-n, --max-subtasks <number>', 'Maximum number of subtasks to create', '5')
    .action(async (options) => {
      try {
        // Display banner
        console.log('\n' + gradient.pastel.multiline(boxen(
          chalk.bold('Tascade AI - Complexity Workflow'),
          {
            padding: 1,
            margin: 0,
            borderStyle: 'round',
            borderColor: 'cyan'
          }
        )));
        
        // Connect to the server if not already connected
        if (!client.isConnected()) {
          try {
            await client.connect();
          } catch (error) {
            console.warn(chalk.yellow(`Warning: Could not connect to server: ${error.message}`));
            console.warn(chalk.yellow('Running in offline mode with limited functionality'));
          }
        }
        
        // Analyze task complexity
        if (options.analyze) {
          const taskId = options.analyze;
          
          try {
            // Get the task
            let task;
            
            if (client.isConnected()) {
              const result = await client.send('get-task', { id: taskId });
              task = result.task;
            } else {
              console.error(chalk.red('Error: Cannot get task in offline mode'));
              process.exit(1);
            }
            
            if (!task) {
              console.error(chalk.red(`Error: Task with ID ${taskId} not found`));
              process.exit(1);
            }
            
            // Analyze task complexity
            await complexityWorkflow.analyzeTaskComplexity(task, {
              detailed: options.detailed,
              interactive: options.interactive
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error analyzing task complexity: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Suggest task splitting
        else if (options.suggestSplitting) {
          const taskId = options.suggestSplitting;
          
          try {
            // Get the task
            let task;
            
            if (client.isConnected()) {
              const result = await client.send('get-task', { id: taskId });
              task = result.task;
            } else {
              console.error(chalk.red('Error: Cannot get task in offline mode'));
              process.exit(1);
            }
            
            if (!task) {
              console.error(chalk.red(`Error: Task with ID ${taskId} not found`));
              process.exit(1);
            }
            
            // Suggest task splitting
            await complexityWorkflow.suggestTaskSplitting(task, {
              maxSubtasks: parseInt(options.maxSubtasks, 10),
              interactive: options.interactive
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error suggesting task splitting: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Generate verification criteria
        else if (options.verify) {
          const taskId = options.verify;
          
          try {
            // Get the task
            let task;
            
            if (client.isConnected()) {
              const result = await client.send('get-task', { id: taskId });
              task = result.task;
            } else {
              console.error(chalk.red('Error: Cannot get task in offline mode'));
              process.exit(1);
            }
            
            if (!task) {
              console.error(chalk.red(`Error: Task with ID ${taskId} not found`));
              process.exit(1);
            }
            
            // Generate verification criteria
            await complexityWorkflow.generateVerificationCriteria(task, {
              interactive: options.interactive
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error generating verification criteria: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Show project complexity metrics
        else if (options.metrics) {
          try {
            // Get all tasks
            let tasks;
            
            if (client.isConnected()) {
              const result = await client.send('get-tasks', {});
              tasks = result.tasks || [];
            } else {
              console.error(chalk.red('Error: Cannot get tasks in offline mode'));
              process.exit(1);
            }
            
            // Display complexity metrics
            await complexityWorkflow.displayComplexityMetrics(tasks, {
              detailed: options.detailed
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error displaying complexity metrics: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Show help if no specific command is provided
        else {
          console.log('\n' + chalk.bold('Task Complexity Workflow Commands:'));
          console.log(`  ${chalk.cyan('--analyze <id>')}        Analyze complexity of a task`);
          console.log(`  ${chalk.cyan('--suggest-splitting <id>')} Suggest how to split a complex task`);
          console.log(`  ${chalk.cyan('--verify <id>')}         Generate verification criteria based on complexity`);
          console.log(`  ${chalk.cyan('--metrics')}             Show project complexity metrics`);
          console.log(`  ${chalk.cyan('--detailed')}            Show detailed information`);
          console.log(`  ${chalk.cyan('--interactive')}         Run in interactive mode`);
          console.log(`  ${chalk.cyan('--max-subtasks <number>')} Maximum number of subtasks to create (default: 5)`);
          
          console.log('\n' + chalk.bold('Examples:'));
          console.log(`  ${chalk.green('tascade-cli complexity --analyze TAS-123')}`);
          console.log(`  ${chalk.green('tascade-cli complexity --suggest-splitting TAS-123 --interactive')}`);
          console.log(`  ${chalk.green('tascade-cli complexity --metrics --detailed')}`);
        }
        
        // Disconnect from the server if connected
        if (client.isConnected()) {
          await client.disconnect();
        }
      } catch (error) {
        console.error(chalk.red(`An unexpected error occurred: ${error.message}`));
        process.exit(1);
      }
    });
  
  // Task execution workflow command
  program
    .command('execute')
    .description('Execute a task with dependency checking and complexity assessment')
    .option('-t, --task <id>', 'ID of the task to execute')
    .option('-i, --interactive', 'Run in interactive mode')
    .action(async (options) => {
      try {
        // Display banner
        console.log('\n' + gradient.pastel.multiline(boxen(
          chalk.bold('Tascade AI - Task Execution'),
          {
            padding: 1,
            margin: 0,
            borderStyle: 'round',
            borderColor: 'cyan'
          }
        )));
        
        // Connect to the server if not already connected
        if (!client.isConnected()) {
          try {
            await client.connect();
          } catch (error) {
            console.warn(chalk.yellow(`Warning: Could not connect to server: ${error.message}`));
            console.warn(chalk.yellow('Running in offline mode with limited functionality'));
          }
        }
        
        // Execute task
        if (options.task) {
          const taskId = options.task;
          
          try {
            // Get the task
            let task;
            
            if (client.isConnected()) {
              const result = await client.send('get-task', { id: taskId });
              task = result.task;
            } else {
              console.error(chalk.red('Error: Cannot get task in offline mode'));
              process.exit(1);
            }
            
            if (!task) {
              console.error(chalk.red(`Error: Task with ID ${taskId} not found`));
              process.exit(1);
            }
            
            // Execute task
            await taskExecution.executeTask(task, {
              interactive: options.interactive
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error executing task: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Show help if no specific command is provided
        else {
          console.log('\n' + chalk.bold('Task Execution Commands:'));
          console.log(`  ${chalk.cyan('--task <id>')}          ID of the task to execute`);
          console.log(`  ${chalk.cyan('--interactive')}         Run in interactive mode`);
          
          console.log('\n' + chalk.bold('Examples:'));
          console.log(`  ${chalk.green('tascade-cli execute --task TAS-123')}`);
          console.log(`  ${chalk.green('tascade-cli execute --task TAS-123 --interactive')}`);
        }
        
        // Disconnect from the server if connected
        if (client.isConnected()) {
          await client.disconnect();
        }
      } catch (error) {
        console.error(chalk.red(`An unexpected error occurred: ${error.message}`));
        process.exit(1);
      }
    });
  
  // Task verification workflow command
  program
    .command('verify')
    .description('Verify a task with scoring system')
    .option('-t, --task <id>', 'ID of the task to verify')
    .option('-i, --interactive', 'Run in interactive mode')
    .action(async (options) => {
      try {
        // Display banner
        console.log('\n' + gradient.pastel.multiline(boxen(
          chalk.bold('Tascade AI - Task Verification'),
          {
            padding: 1,
            margin: 0,
            borderStyle: 'round',
            borderColor: 'cyan'
          }
        )));
        
        // Connect to the server if not already connected
        if (!client.isConnected()) {
          try {
            await client.connect();
          } catch (error) {
            console.warn(chalk.yellow(`Warning: Could not connect to server: ${error.message}`));
            console.warn(chalk.yellow('Running in offline mode with limited functionality'));
          }
        }
        
        // Verify task
        if (options.task) {
          const taskId = options.task;
          
          try {
            // Get the task
            let task;
            
            if (client.isConnected()) {
              const result = await client.send('get-task', { id: taskId });
              task = result.task;
            } else {
              console.error(chalk.red('Error: Cannot get task in offline mode'));
              process.exit(1);
            }
            
            if (!task) {
              console.error(chalk.red(`Error: Task with ID ${taskId} not found`));
              process.exit(1);
            }
            
            // Verify task
            await taskVerification.verifyTask(task, {
              interactive: options.interactive
            }, client);
          } catch (error) {
            console.error(chalk.red(`Error verifying task: ${error.message}`));
            process.exit(1);
          }
        }
        
        // Show help if no specific command is provided
        else {
          console.log('\n' + chalk.bold('Task Verification Commands:'));
          console.log(`  ${chalk.cyan('--task <id>')}          ID of the task to verify`);
          console.log(`  ${chalk.cyan('--interactive')}         Run in interactive mode`);
          
          console.log('\n' + chalk.bold('Examples:'));
          console.log(`  ${chalk.green('tascade-cli verify --task TAS-123')}`);
          console.log(`  ${chalk.green('tascade-cli verify --task TAS-123 --interactive')}`);
        }
        
        // Disconnect from the server if connected
        if (client.isConnected()) {
          await client.disconnect();
        }
      } catch (error) {
        console.error(chalk.red(`An unexpected error occurred: ${error.message}`));
        process.exit(1);
      }
    });
  
  return program;
}

/**
 * Initialize workflow
 * @param {Object} options - Initialization options
 * @returns {Object} Initialized workflow
 */
export function initWorkflow(options = {}) {
  return {
    complexity: complexityWorkflow,
    execution: taskExecution,
    verification: taskVerification
  };
}

export default {
  registerWorkflowCommands,
  initWorkflow,
  complexityWorkflow,
  taskExecution,
  taskVerification
};
