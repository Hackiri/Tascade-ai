#!/usr/bin/env node

/**
 * Tascade AI CLI
 * 
 * This is the main entry point for the Tascade AI npm package.
 * It provides a command-line interface for interacting with Tascade AI.
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import { WebSocket } from 'ws';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { spawn } from 'child_process';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import config from '../src/config/index.js';
import parsePRD from '../src/ai/parse-prd.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packageJson = JSON.parse(readFileSync(join(__dirname, '../package.json'), 'utf8'));

// Create a new command program
const program = new Command();

// Set up the program
program
  .name('tascade-ai')
  .description('AI-powered task management system for project planning and execution')
  .version(packageJson.version);

// Add commands
program
  .command('start')
  .description('Start the Tascade AI server')
  .option('-p, --port <port>', 'Port to run the server on', '8765')
  .action(async (options) => {
    const spinner = ora('Starting Tascade AI server...').start();
    
    try {
      // Check if the port is available
      const isPortAvailable = await checkPort(options.port);
      
      if (!isPortAvailable) {
        spinner.fail(`Port ${options.port} is already in use. Please specify a different port.`);
        return;
      }
      
      // Start the server
      const server = startServer(options.port);
      
      spinner.succeed(`Tascade AI server started on port ${options.port}`);
      console.log(chalk.green(`\nServer is running at ${chalk.bold(`ws://localhost:${options.port}`)}`));
      console.log(chalk.yellow('\nPress Ctrl+C to stop the server'));
      
      // Handle server exit
      process.on('SIGINT', () => {
        console.log(chalk.yellow('\nStopping Tascade AI server...'));
        server.kill();
        process.exit(0);
      });
    } catch (error) {
      spinner.fail(`Failed to start Tascade AI server: ${error.message}`);
    }
  });

program
  .command('tasks')
  .description('Manage tasks')
  .option('-l, --list', 'List all tasks')
  .option('-a, --add', 'Add a new task')
  .option('-s, --status <status>', 'Filter tasks by status')
  .action(async (options) => {
    if (options.list) {
      const spinner = ora('Fetching tasks...').start();
      
      try {
        // Connect to the server
        const client = await connectToServer();
        
        // Get tasks
        const result = await sendCommand(client, 'get-tasks', {
          status: options.status
        });
        
        spinner.succeed('Tasks fetched successfully');
        
        // Display tasks
        if (result.tasks && result.tasks.length > 0) {
          console.log(chalk.bold('\nTasks:'));
          
          result.tasks.forEach((task) => {
            console.log(`\n${chalk.bold(task.title)} ${chalk.gray(`(${task.id})`)}`);
            console.log(`${chalk.blue('Status:')} ${task.status}`);
            console.log(`${chalk.blue('Priority:')} ${task.priority}`);
            
            if (task.description) {
              console.log(`${chalk.blue('Description:')} ${task.description}`);
            }
          });
        } else {
          console.log(chalk.yellow('\nNo tasks found'));
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        spinner.fail(`Failed to fetch tasks: ${error.message}`);
      }
    } else if (options.add) {
      // Prompt for task details
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'title',
          message: 'Task title:',
          validate: (input) => input.trim() !== '' ? true : 'Title is required'
        },
        {
          type: 'input',
          name: 'description',
          message: 'Task description:'
        },
        {
          type: 'list',
          name: 'priority',
          message: 'Task priority:',
          choices: ['high', 'medium', 'low'],
          default: 'medium'
        }
      ]);
      
      const spinner = ora('Adding task...').start();
      
      try {
        // Connect to the server
        const client = await connectToServer();
        
        // Add task
        const result = await sendCommand(client, 'add-task', {
          title: answers.title,
          description: answers.description,
          priority: answers.priority
        });
        
        spinner.succeed('Task added successfully');
        
        // Display task
        if (result.id) {
          console.log(chalk.green(`\nTask added with ID: ${chalk.bold(result.id)}`));
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        spinner.fail(`Failed to add task: ${error.message}`);
      }
    } else {
      console.log(chalk.yellow('Please specify an action (--list or --add)'));
      program.help();
    }
  });

program
  .command('track')
  .description('Track time for tasks')
  .option('-s, --start <taskId>', 'Start tracking time for a task')
  .option('-p, --stop <sessionId>', 'Stop tracking time')
  .option('-l, --list', 'List time entries')
  .action(async (options) => {
    if (options.start) {
      // Prompt for tracking details
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'description',
          message: 'What are you working on?'
        }
      ]);
      
      const spinner = ora('Starting time tracking...').start();
      
      try {
        // Connect to the server
        const client = await connectToServer();
        
        // Start tracking
        const result = await sendCommand(client, 'start-tracking', {
          task_id: options.start,
          description: answers.description
        });
        
        spinner.succeed('Time tracking started');
        
        // Display session
        if (result.session_id) {
          console.log(chalk.green(`\nSession started with ID: ${chalk.bold(result.session_id)}`));
          console.log(chalk.yellow('\nRemember this session ID to stop tracking later'));
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        spinner.fail(`Failed to start tracking: ${error.message}`);
      }
    } else if (options.stop) {
      const spinner = ora('Stopping time tracking...').start();
      
      try {
        // Connect to the server
        const client = await connectToServer();
        
        // Stop tracking
        const result = await sendCommand(client, 'stop-tracking', {
          session_id: options.stop
        });
        
        spinner.succeed('Time tracking stopped');
        
        // Display result
        if (result.success) {
          console.log(chalk.green(`\nSession stopped successfully`));
          
          if (result.duration_seconds) {
            const minutes = Math.floor(result.duration_seconds / 60);
            const seconds = result.duration_seconds % 60;
            console.log(chalk.blue(`Duration: ${minutes}m ${seconds}s`));
          }
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        spinner.fail(`Failed to stop tracking: ${error.message}`);
      }
    } else if (options.list) {
      const spinner = ora('Fetching time entries...').start();
      
      try {
        // Connect to the server
        const client = await connectToServer();
        
        // Get time entries
        const result = await sendCommand(client, 'get-time-entries', {});
        
        spinner.succeed('Time entries fetched successfully');
        
        // Display time entries
        if (result.entries && result.entries.length > 0) {
          console.log(chalk.bold('\nTime Entries:'));
          
          result.entries.forEach((entry) => {
            console.log(`\n${chalk.bold(entry.description || 'No description')} ${chalk.gray(`(${entry.id})`)}`);
            console.log(`${chalk.blue('Task:')} ${entry.task_id}`);
            
            if (entry.start_time) {
              console.log(`${chalk.blue('Start Time:')} ${new Date(entry.start_time).toLocaleString()}`);
            }
            
            if (entry.end_time) {
              console.log(`${chalk.blue('End Time:')} ${new Date(entry.end_time).toLocaleString()}`);
            }
            
            if (entry.duration_seconds) {
              const minutes = Math.floor(entry.duration_seconds / 60);
              const seconds = entry.duration_seconds % 60;
              console.log(`${chalk.blue('Duration:')} ${minutes}m ${seconds}s`);
            }
          });
        } else {
          console.log(chalk.yellow('\nNo time entries found'));
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        spinner.fail(`Failed to fetch time entries: ${error.message}`);
      }
    } else {
      console.log(chalk.yellow('Please specify an action (--start, --stop, or --list)'));
      program.help();
    }
  });

program
  .command('generate')
  .description('Generate tasks from a PRD file using AI')
  .option('-i, --input <file>', 'Path to the PRD file')
  .option('-o, --output <file>', 'Path to save the generated tasks')
  .option('-n, --num-tasks <number>', 'Number of tasks to generate')
  .option('-p, --provider <provider>', 'AI provider to use (anthropic, openai, perplexity)', 'anthropic')
  .option('-f, --force', 'Overwrite existing tasks file', false)
  .option('--priority <priority>', 'Default priority for generated tasks (high, medium, low)')
  .action(async (options) => {
    // Check if input and output files are specified
    if (!options.input) {
      console.log(chalk.red('Error: Input file is required'));
      console.log(chalk.yellow('Usage: tascade-ai generate --input <file> --output <file>'));
      return;
    }
    
    if (!options.output) {
      console.log(chalk.red('Error: Output file is required'));
      console.log(chalk.yellow('Usage: tascade-ai generate --input <file> --output <file>'));
      return;
    }
    
    const spinner = ora('Generating tasks from PRD...').start();
    
    try {
      // Parse the PRD file and generate tasks
      const result = await parsePRD(
        options.input,
        options.output,
        options.numTasks ? parseInt(options.numTasks) : null,
        {
          provider: options.provider,
          force: options.force,
          priority: options.priority || config.ai.task_generation.default_priority
        }
      );
      
      spinner.succeed(`Successfully generated ${result.tasks.length} tasks`);
      
      // Display a summary of the generated tasks
      console.log('\n' + chalk.bold('Task Summary:'));
      console.log(chalk.dim('─'.repeat(50)));
      
      result.tasks.forEach(task => {
        const priorityColor = {
          high: chalk.red,
          medium: chalk.yellow,
          low: chalk.green
        }[task.priority] || chalk.white;
        
        console.log(`${chalk.cyan(`#${task.id}`)} ${chalk.bold(task.title)}`);
        console.log(`  Priority: ${priorityColor(task.priority)}`);
        console.log(`  Dependencies: ${task.dependencies.length ? task.dependencies.join(', ') : 'None'}`);
        console.log(chalk.dim('─'.repeat(50)));
      });
      
      console.log(chalk.green(`\nTasks saved to ${options.output}`));
    } catch (error) {
      spinner.fail(`Failed to generate tasks: ${error.message}`);
    }
  });

program
  .command('mcp')
  .description('Start the Tascade AI MCP server')
  .option('-p, --port <port>', 'Port to run the server on', '8765')
  .action(async (options) => {
    const spinner = ora('Starting Tascade AI MCP server...').start();
    
    try {
      // Check if the port is available
      const isPortAvailable = await checkPort(options.port);
      
      if (!isPortAvailable) {
        spinner.fail(`Port ${options.port} is already in use. Please specify a different port.`);
        return;
      }
      
      // Start the MCP server
      const server = startMCPServer(options.port);
      
      spinner.succeed(`Tascade AI MCP server started on port ${options.port}`);
      console.log(chalk.green(`\nMCP server is running at ${chalk.bold(`ws://localhost:${options.port}`)}`));
      console.log(chalk.yellow('\nPress Ctrl+C to stop the server'));
      
      // Handle server exit
      process.on('SIGINT', () => {
        console.log(chalk.yellow('\nStopping Tascade AI MCP server...'));
        server.kill();
        process.exit(0);
      });
    } catch (error) {
      spinner.fail(`Failed to start Tascade AI MCP server: ${error.message}`);
    }
  });

// Helper functions

/**
 * Check if a port is available
 * 
 * @param {string} port - The port to check
 * @returns {Promise<boolean>} - True if the port is available, false otherwise
 */
function checkPort(port) {
  return new Promise((resolve) => {
    const server = createServer();
    
    server.once('error', () => {
      resolve(false);
    });
    
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    
    server.listen(port);
  });
}

/**
 * Start the Tascade AI server
 * 
 * @param {string} port - The port to run the server on
 * @returns {ChildProcess} - The server process
 */
function startServer(port) {
  // Check if we're running from the installed package or from the source
  const serverPath = join(__dirname, '../src/server.js');
  const serverExists = existsSync(serverPath);
  
  if (serverExists) {
    // Running from source
    return spawn('node', [serverPath, '--port', port], {
      stdio: 'inherit'
    });
  } else {
    // Running from installed package
    return spawn('node', [join(__dirname, 'server.js'), '--port', port], {
      stdio: 'inherit'
    });
  }
}

/**
 * Start the Tascade AI MCP server
 * 
 * @param {string} port - The port to run the server on
 * @returns {ChildProcess} - The server process
 */
function startMCPServer(port) {
  // Check if we're running from the installed package or from the source
  const serverPath = join(__dirname, '../src/mcp/simple_server.py');
  const serverExists = existsSync(serverPath);
  
  if (serverExists) {
    // Running from source
    return spawn('python', [serverPath, '--port', port], {
      stdio: 'inherit'
    });
  } else {
    // Running from installed package
    return spawn('python', [join(__dirname, 'mcp_server.py'), '--port', port], {
      stdio: 'inherit'
    });
  }
}

/**
 * Connect to the Tascade AI server
 * 
 * @param {string} port - The port to connect to
 * @returns {Promise<WebSocket>} - The WebSocket client
 */
async function connectToServer(port = '8765') {
  return new Promise((resolve, reject) => {
    const client = new WebSocket(`ws://localhost:${port}`);
    
    client.on('open', () => {
      resolve(client);
    });
    
    client.on('error', (error) => {
      reject(new Error(`Failed to connect to server: ${error.message}`));
    });
  });
}

/**
 * Send a command to the Tascade AI server
 * 
 * @param {WebSocket} client - The WebSocket client
 * @param {string} command - The command to send
 * @param {object} params - The command parameters
 * @returns {Promise<object>} - The command result
 */
async function sendCommand(client, command, params) {
  return new Promise((resolve, reject) => {
    const id = Math.random().toString(36).substring(2, 15);
    
    const message = {
      command,
      params,
      id
    };
    
    const responseHandler = (data) => {
      const response = JSON.parse(data);
      
      if (response.id === id) {
        client.removeEventListener('message', responseHandler);
        
        if (response.error) {
          reject(new Error(response.error.message));
        } else {
          resolve(response.result);
        }
      }
    };
    
    client.on('message', responseHandler);
    
    client.send(JSON.stringify(message));
  });
}

/**
 * Check if all required dependencies are available
 * @returns {boolean} - True if all dependencies are available, false otherwise
 */
function checkDependencies() {
  const requiredDependencies = [
    'commander',
    'inquirer',
    'chalk',
    'ora',
    'ws'
  ];
  
  let missingDependencies = [];
  
  // We can't dynamically import in this context, so we'll just check if we can access the modules
  for (const dep of requiredDependencies) {
    try {
      // If we're here, the module was imported successfully at the top
      // This is just a placeholder to avoid lint errors
      if (dep === 'commander' && typeof Command !== 'function') {
        missingDependencies.push(dep);
      }
    } catch (error) {
      missingDependencies.push(dep);
    }
  }
  
  if (missingDependencies.length > 0) {
    console.error(`\n${chalk.red('Error:')} Missing dependencies: ${missingDependencies.join(', ')}`);
    console.error(`Please run ${chalk.cyan('npm install')} in the Tascade AI directory to install all dependencies.`);
    return false;
  }
  
  return true;
}

// Main execution wrapped in try-catch for better error handling
try {
  // Check dependencies before running commands
  if (!checkDependencies()) {
    process.exit(1);
  }
  
  // Parse the command line arguments
  program.parse(process.argv);
  
  // If no arguments are provided, show help
  if (process.argv.length === 2) {
    program.help();
  }
} catch (error) {
  // Handle unexpected errors gracefully
  console.error(`\n${chalk.red('Error:')} An unexpected error occurred while running Tascade AI.`);
  console.error(`${chalk.yellow('Details:')} ${error.message}`);
  
  if (error.code === 'ERR_MODULE_NOT_FOUND') {
    console.error(`\n${chalk.yellow('Dependency Error:')} A required dependency is missing.`);
    console.error(`Please run ${chalk.cyan('npm install')} in the Tascade AI directory to install all dependencies.`);
    console.error(`If you're using npx, try running ${chalk.cyan('npx tascade-ai@latest')} instead.`);
  } else {
    console.error(`\n${chalk.yellow('Troubleshooting:')}`);
    console.error(`1. Make sure you're in the correct directory`);
    console.error(`2. Try reinstalling Tascade AI: ${chalk.cyan('npm install -g tascade-ai')}`);
    console.error(`3. Check for updates: ${chalk.cyan('npm update -g tascade-ai')}`);
  }
  
  console.error(`\nIf the problem persists, please report this issue at:`);
  console.error(`${chalk.cyan('https://github.com/Hackiri/tascade-aI/issues')}\n`);
  
  process.exit(1);
}
