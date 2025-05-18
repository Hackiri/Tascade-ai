/**
 * commands.js
 * Command-line interface for the Tascade AI CLI
 * Inspired by claude-task-master's command structure
 */

import { program } from 'commander';
import path from 'path';
import fs from 'fs';
import chalk from 'chalk';
import inquirer from 'inquirer';
import dotenv from 'dotenv';
import { spawn } from 'child_process';
import { WebSocket } from 'ws';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer } from 'http';
import { createMCPClient } from '../mcp/client.js';
import { createMCPContextManager } from '../mcp/context_manager.js';
import parsePRD from '../ai/parse-prd.js';
import * as ui from './ui.js';
import { assessTaskComplexity } from '../utils/task_complexity.js';
import { 
  integrateComplexityWithTask,
  shouldSplitTaskByComplexity,
  analyzeDependenciesByComplexity,
  suggestVerificationCriteria,
  calculateComplexityBasedProgress
} from '../utils/feature_integration.js';
import { registerWorkflowCommands } from '../workflow/index.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config();

/**
 * Check if a port is available
 * @param {string} port - The port to check
 * @returns {Promise<boolean>} - True if the port is available, false otherwise
 */
async function checkPort(port) {
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
 * @param {string} port - The port to run the server on
 * @returns {ChildProcess} - The server process
 */
function startServer(port) {
  const serverPath = join(__dirname, '../../src/server.js');
  
  const server = spawn('node', [serverPath, '--port', port], {
    stdio: 'inherit',
    detached: true
  });
  
  server.unref();
  
  return server;
}

/**
 * Start the Tascade AI MCP server
 * @param {string} port - The port to run the server on
 * @returns {ChildProcess} - The server process
 */
function startMCPServer(port) {
  const serverPath = join(__dirname, '../../src/mcp/server.js');
  
  const server = spawn('node', [serverPath, '--port', port], {
    stdio: 'inherit',
    detached: true
  });
  
  server.unref();
  
  return server;
}

/**
 * Connect to the Tascade AI server
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
      reject(error);
    });
  });
}

/**
 * Send a command to the Tascade AI server
 * @param {WebSocket} client - The WebSocket client
 * @param {string} command - The command to send
 * @param {object} params - The command parameters
 * @returns {Promise<object>} - The command result
 */
async function sendCommand(client, command, params) {
  return new Promise((resolve, reject) => {
    const id = Date.now().toString();
    const message = {
      id,
      command,
      params
    };
    
    const handleMessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        
        if (response.id === id) {
          client.removeEventListener('message', handleMessage);
          resolve(response);
        }
      } catch (error) {
        // Ignore non-JSON messages
      }
    };
    
    client.addEventListener('message', handleMessage);
    client.send(JSON.stringify(message));
    
    // Set a timeout to prevent hanging
    setTimeout(() => {
      client.removeEventListener('message', handleMessage);
      reject(new Error('Command timed out'));
    }, 60000);
  });
}

/**
 * Check if all required dependencies are available
 * @returns {boolean} - True if all dependencies are available, false otherwise
 */
function checkDependencies() {
  const requiredDependencies = [
    'commander',
    'chalk',
    'ora',
    'inquirer',
    'ws'
  ];
  
  let allDependenciesAvailable = true;
  
  for (const dep of requiredDependencies) {
    try {
      // Special case for commander
      if (dep === 'commander' && typeof program.Command !== 'function') {
        console.error(`Required dependency '${dep}' is not available.`);
        allDependenciesAvailable = false;
      }
    } catch (error) {
      console.error(`Required dependency '${dep}' is not available.`);
      allDependenciesAvailable = false;
    }
  }
  
  return allDependenciesAvailable;
}

/**
 * Configure and register CLI commands
 * @param {Object} program - Commander program instance
 */
function registerCommands(programInstance) {
  // Create MCP client for server communication
  const mcpClient = {
    isConnected: () => false,
    connect: async () => {
      try {
        return await connectToServer();
      } catch (error) {
        throw new Error(`Failed to connect to server: ${error.message}`);
      }
    },
    disconnect: async () => {},
    send: async (command, params) => {
      try {
        const client = await connectToServer();
        const result = await sendCommand(client, command, params);
        client.close();
        return result;
      } catch (error) {
        throw new Error(`Failed to send command: ${error.message}`);
      }
    }
  };
  // Start server command
  programInstance
    .command('start')
    .description('Start the Tascade AI server')
    .option('-p, --port <port>', 'Port to run the server on', '8765')
    .action(async (options) => {
      const spinner = ui.startSpinner('Starting Tascade AI server...');
      
      try {
        // Check if the port is available
        const isPortAvailable = await checkPort(options.port);
        
        if (!isPortAvailable) {
          ui.stopSpinner(spinner, `Port ${options.port} is already in use. Please specify a different port.`, 'error');
          return;
        }
        
        // Start the server
        const server = startServer(options.port);
        
        ui.stopSpinner(spinner, `Tascade AI server started on port ${options.port}`, 'success');
        ui.displaySuccess(`Server is running at ws://localhost:${options.port}`);
        ui.displayInfo('Press Ctrl+C to stop the server');
        
        // Handle server exit
        process.on('SIGINT', () => {
          console.log(chalk.yellow('\nStopping Tascade AI server...'));
          process.exit(0);
        });
        
        // Keep the process running
        process.stdin.resume();
      } catch (error) {
        ui.stopSpinner(spinner, `Failed to start server: ${error.message}`, 'error');
        process.exit(1);
      }
    });
    
  // Tasks command
  programInstance
    .command('tasks')
    .description('Manage tasks')
    .option('-l, --list', 'List all tasks')
    .option('-a, --add', 'Add a new task')
    .option('-i, --id <id>', 'Get a specific task by ID')
    .option('-u, --update <id>', 'Update a task')
    .option('-d, --delete <id>', 'Delete a task')
    .option('-s, --status <status>', 'Filter tasks by status')
    .option('-p, --priority <priority>', 'Filter tasks by priority')
    .option('-t, --tag <tag>', 'Filter tasks by tag')
    .option('-w, --with-subtasks', 'Include subtasks in the output')
    .option('-c, --assess-complexity <id>', 'Assess complexity of a task')
    .action(async (options) => {
      try {
        // Connect to the server
        const spinner = ui.startSpinner('Connecting to Tascade AI server...');
        let client;
        
        try {
          client = await connectToServer();
          ui.stopSpinner(spinner, 'Connected to Tascade AI server', 'success');
        } catch (error) {
          ui.stopSpinner(spinner, `Failed to connect to server: ${error.message}`, 'error');
          ui.displayError('Make sure the server is running with the \'tascade-cli start\' command');
          return;
        }
        
        // List all tasks
        if (options.list) {
          const listSpinner = ui.startSpinner('Fetching tasks...');
          
          try {
            const result = await sendCommand(client, 'get-tasks', {});
            ui.stopSpinner(listSpinner, 'Tasks fetched successfully', 'success');
            
            if (result.tasks && result.tasks.length > 0) {
              // Enhance tasks with complexity information
              const enhancedTasks = result.tasks.map(task => integrateComplexityWithTask(task));
              
              const tableData = enhancedTasks.map(task => [
                task.id,
                task.title,
                ui.getStatusWithColor(task.status || 'pending'),
                task.priority || 'medium',
                task.complexityIndicator,
                task.assignee || 'Unassigned'
              ]);
              
              console.log(ui.createTable(
                ['ID', 'Title', 'Status', 'Priority', 'Complexity', 'Assignee'],
                tableData
              ));
              
              // Calculate and display complexity-based progress
              const progressMetrics = calculateComplexityBasedProgress(enhancedTasks);
              
              console.log('\n' + chalk.bold('Project Progress by Complexity:'));
              Object.entries(progressMetrics.completionByComplexity).forEach(([level, data]) => {
                if (data.total > 0) {
                  const levelFormatted = level.charAt(0).toUpperCase() + level.slice(1).replace('_', ' ');
                  const color = ui.getComplexityColor(level);
                  console.log(`${color(levelFormatted)}: ${data.completed}/${data.total} (${Math.round(data.percentage)}%)`);
                }
              });
              
              console.log('\n' + chalk.bold(`Weighted Progress: ${Math.round(progressMetrics.weightedProgress)}%`));
              console.log(ui.createProgressBar(progressMetrics.weightedProgress));
            } else {
              ui.displayInfo('No tasks found');
            }
          } catch (error) {
            ui.stopSpinner(listSpinner, `Failed to fetch tasks: ${error.message}`, 'error');
          }
        }
        
        // Get a specific task by ID
        else if (options.id) {
          const taskSpinner = ui.startSpinner(`Fetching task ${options.id}...`);
          
          try {
            const result = await sendCommand(client, 'get-task', { id: options.id });
            ui.stopSpinner(taskSpinner, 'Task fetched successfully', 'success');
            
            if (result.task) {
              const task = result.task;
              
              // Integrate complexity with task display
              const enhancedTask = integrateComplexityWithTask(task);
              
              ui.displayBox(
                `${chalk.bold('Task:')} ${enhancedTask.id} - ${enhancedTask.title}\n` +
                `${chalk.bold('Status:')} ${ui.getStatusWithColor(enhancedTask.status || 'pending')}\n` +
                `${chalk.bold('Priority:')} ${enhancedTask.priority || 'medium'}\n` +
                `${chalk.bold('Complexity:')} ${enhancedTask.complexityIndicator}\n` +
                `${chalk.bold('Assignee:')} ${enhancedTask.assignee || 'Unassigned'}\n\n` +
                `${chalk.bold('Description:')}\n${enhancedTask.description || 'No description'}`,
                'info'
              );
              
              // Show subtasks if any
              if (task.subtasks && task.subtasks.length > 0) {
                const subtaskTableData = task.subtasks.map(subtask => [
                  subtask.id,
                  subtask.title,
                  ui.getStatusWithColor(subtask.status || 'pending')
                ]);
                
                console.log(chalk.bold('\nSubtasks:'));
                console.log(ui.createTable(
                  ['ID', 'Title', 'Status'],
                  subtaskTableData
                ));
              }
            } else {
              ui.displayError(`Task with ID ${options.id} not found`);
            }
          } catch (error) {
            ui.stopSpinner(taskSpinner, `Failed to fetch task: ${error.message}`, 'error');
          }
        }
        
        // Assess task complexity
        else if (options.assessComplexity) {
          const taskId = options.assessComplexity;
          const complexitySpinner = ui.startSpinner(`Assessing complexity of task ${taskId}...`);
          
          try {
            const result = await sendCommand(client, 'get-task', { id: taskId });
            ui.stopSpinner(complexitySpinner, 'Task fetched for complexity assessment', 'success');
            
            if (result.task) {
              const task = result.task;
              
              // Assess task complexity
              const complexityAssessment = assessTaskComplexity(task);
              
              // Display complexity assessment
              console.log(ui.displayComplexityAssessment(complexityAssessment));
              
              // Check if task should be split based on complexity
              if (shouldSplitTaskByComplexity(task)) {
                ui.displayWarning('This task is complex and should be considered for splitting into smaller subtasks.');
              }
              
              // Suggest verification criteria based on complexity
              const suggestedCriteria = suggestVerificationCriteria(task);
              if (suggestedCriteria.length > 0) {
                console.log(chalk.bold('\nSuggested Verification Criteria:'));
                suggestedCriteria.forEach(criterion => {
                  console.log(`  ${chalk.cyan('•')} ${criterion.description} ${chalk.dim(`[${criterion.type}]`)}`);
                });
              }
              
              // If task has dependencies, analyze them
              if (task.dependencies && task.dependencies.length > 0) {
                const dependencySpinner = ui.startSpinner('Analyzing dependencies...');
                
                try {
                  // Get all tasks to analyze dependencies
                  const allTasksResult = await sendCommand(client, 'get-tasks', {});
                  const allTasks = allTasksResult.tasks || [];
                  
                  // Analyze dependencies by complexity
                  const dependencyAnalysis = analyzeDependenciesByComplexity(task, allTasks);
                  
                  ui.stopSpinner(dependencySpinner, 'Dependencies analyzed', 'success');
                  
                  if (dependencyAnalysis.isComplexDependencyChain) {
                    ui.displayWarning('This task has complex dependencies that may impact its completion.');
                  }
                } catch (error) {
                  ui.stopSpinner(dependencySpinner, `Failed to analyze dependencies: ${error.message}`, 'error');
                }
              }
              
              // Update task with complexity assessment if needed
              if (!task.complexity || task.complexity.level !== complexityAssessment.level) {
                const updateSpinner = ui.startSpinner('Updating task with complexity assessment...');
                
                try {
                  await sendCommand(client, 'update-task', {
                    id: taskId,
                    complexity: {
                      level: complexityAssessment.level,
                      score: complexityAssessment.overallScore,
                      assessedAt: new Date().toISOString()
                    }
                  });
                  
                  ui.stopSpinner(updateSpinner, 'Task updated with complexity assessment', 'success');
                } catch (error) {
                  ui.stopSpinner(updateSpinner, `Failed to update task: ${error.message}`, 'error');
                }
              }
            } else {
              ui.displayError(`Task with ID ${taskId} not found`);
            }
          } catch (error) {
            ui.stopSpinner(complexitySpinner, `Failed to assess task complexity: ${error.message}`, 'error');
          }
        }
        
        // Add a new task
        else if (options.add) {
          // Prompt for task details
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'title',
              message: 'Task title:',
              validate: (input) => input ? true : 'Title is required'
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
              choices: ['low', 'medium', 'high'],
              default: 'medium'
            },
            {
              type: 'input',
              name: 'assignee',
              message: 'Assignee (optional):'
            }
          ]);
          
          const addSpinner = ui.startSpinner('Adding task...');
          
          try {
            const result = await sendCommand(client, 'add-task', {
              title: answers.title,
              description: answers.description,
              priority: answers.priority,
              assignee: answers.assignee || null
            });
            
            ui.stopSpinner(addSpinner, 'Task added successfully', 'success');
            ui.displaySuccess(`Task added with ID: ${result.task.id}`);
          } catch (error) {
            ui.stopSpinner(addSpinner, `Failed to add task: ${error.message}`, 'error');
          }
        }
        
        // Default behavior - show help
        else {
          ui.displayCommandHelp('tasks', 'Manage tasks', [
            { flags: '-l, --list', description: 'List all tasks' },
            { flags: '-i, --id <id>', description: 'Get a specific task by ID' },
            { flags: '-a, --add', description: 'Add a new task' },
            { flags: '-c, --assess-complexity <id>', description: 'Assess complexity of a task' }
          ], [
            { command: 'tascade-cli tasks --list', description: 'List all tasks' },
            { command: 'tascade-cli tasks --id 123', description: 'Get task with ID 123' },
            { command: 'tascade-cli tasks --add', description: 'Add a new task' },
            { command: 'tascade-cli tasks --assess-complexity 123', description: 'Assess complexity of task with ID 123' }
          ]);
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        ui.displayError(`An unexpected error occurred: ${error.message}`);
        process.exit(1);
      }
    });
    
  // Register workflow commands
  registerWorkflowCommands(programInstance, mcpClient);
  
  // Time tracking command
  programInstance
    .command('track')
    .description('Track time for tasks')
    .option('-s, --start <taskId>', 'Start tracking time for a task')
    .option('-p, --stop <sessionId>', 'Stop tracking time')
    .option('-l, --list', 'List all time entries')
    .option('-u, --user <userId>', 'User ID for time tracking')
    .option('-d, --date <date>', 'Date for time entries (YYYY-MM-DD)')
    .option('-t, --task <taskId>', 'Filter time entries by task ID')
    .action(async (options) => {
      try {
        // Connect to the server
        const spinner = ui.startSpinner('Connecting to Tascade AI server...');
        let client;
        
        try {
          client = await connectToServer();
          ui.stopSpinner(spinner, 'Connected to Tascade AI server', 'success');
        } catch (error) {
          ui.stopSpinner(spinner, `Failed to connect to server: ${error.message}`, 'error');
          ui.displayError('Make sure the server is running with the \'tascade-cli start\' command');
          return;
        }
        
        // Start tracking time for a task
        if (options.start) {
          const startSpinner = ui.startSpinner(`Starting time tracking for task ${options.start}...`);
          
          try {
            const result = await sendCommand(client, 'start-tracking', {
              taskId: options.start
            });
            
            ui.stopSpinner(startSpinner, 'Time tracking started', 'success');
            ui.displaySuccess(`Session ID: ${result.sessionId}`);
            ui.displayInfo('Use this session ID to stop tracking time');
          } catch (error) {
            ui.stopSpinner(startSpinner, `Failed to start time tracking: ${error.message}`, 'error');
          }
        }
        
        // Stop tracking time
        else if (options.stop) {
          const stopSpinner = ui.startSpinner(`Stopping time tracking for session ${options.stop}...`);
          
          try {
            const result = await sendCommand(client, 'stop-tracking', {
              sessionId: options.stop
            });
            
            ui.stopSpinner(stopSpinner, 'Time tracking stopped', 'success');
            
            const duration = ui.formatDuration(result.duration);
            ui.displaySuccess(`Tracked time: ${duration}`);
          } catch (error) {
            ui.stopSpinner(stopSpinner, `Failed to stop time tracking: ${error.message}`, 'error');
          }
        }
        
        // List all time entries
        else if (options.list) {
          const listSpinner = ui.startSpinner('Fetching time entries...');
          
          try {
            const result = await sendCommand(client, 'get-time-entries', {});
            ui.stopSpinner(listSpinner, 'Time entries fetched successfully', 'success');
            
            if (result.entries && result.entries.length > 0) {
              const tableData = result.entries.map(entry => [
                entry.sessionId,
                entry.taskId,
                new Date(entry.startTime).toLocaleString(),
                entry.endTime ? new Date(entry.endTime).toLocaleString() : 'In progress',
                entry.duration ? ui.formatDuration(entry.duration) : 'In progress'
              ]);
              
              console.log(ui.createTable(
                ['Session ID', 'Task ID', 'Start Time', 'End Time', 'Duration'],
                tableData
              ));
            } else {
              ui.displayInfo('No time entries found');
            }
          } catch (error) {
            ui.stopSpinner(listSpinner, `Failed to fetch time entries: ${error.message}`, 'error');
          }
        }
        
        // Default behavior - show help
        else {
          ui.displayCommandHelp('track', 'Track time for tasks', [
            { flags: '-s, --start <taskId>', description: 'Start tracking time for a task' },
            { flags: '-p, --stop <sessionId>', description: 'Stop tracking time' },
            { flags: '-l, --list', description: 'List all time entries' }
          ], [
            { command: 'tascade-cli track --start 123', description: 'Start tracking time for task 123' },
            { command: 'tascade-cli track --stop abc123', description: 'Stop tracking time for session abc123' },
            { command: 'tascade-cli track --list', description: 'List all time entries' }
          ]);
        }
        
        // Close the connection
        client.close();
      } catch (error) {
        ui.displayError(`An unexpected error occurred: ${error.message}`);
        process.exit(1);
      }
    });
    
  // Generate tasks command
  programInstance
    .command('generate')
    .description('Generate tasks from a PRD file using AI')
    .option('-i, --input <file>', 'Path to the PRD file')
    .option('-o, --output <file>', 'Path to save the generated tasks')
    .option('-n, --num-tasks <number>', 'Number of tasks to generate', '5')
    .option('-p, --provider <provider>', 'AI provider to use', 'perplexity')
    .option('--priority <priority>', 'Default priority for tasks', 'medium')
    .option('-f, --force', 'Force overwrite of existing output file')
    .option('-c, --context <file>', 'Path to a context file with additional information')
    .option('-t, --template <file>', 'Path to a task template file')
    .action(async (options) => {
      try {
        // Display banner
        ui.displayBanner('Tascade AI', '1.0.0', 'Task Generator');
        
        // Validate input file
        if (!options.input) {
          if (!process.stdin.isTTY) {
            // Non-interactive mode
            ui.displayError('Input file is required');
            process.exit(1);
          }
          
          // Interactive mode - prompt for input file
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'input',
              message: 'Enter the path to the PRD file:',
              validate: (input) => {
                if (!input) return 'Input file is required';
                if (!fs.existsSync(input)) return 'File does not exist';
                return true;
              }
            }
          ]);
          
          options.input = answers.input;
        }
        
        // Validate output file
        if (!options.output) {
          if (!process.stdin.isTTY) {
            // Default output file based on input file
            const inputBasename = path.basename(options.input, path.extname(options.input));
            options.output = path.join(path.dirname(options.input), `${inputBasename}_tasks.json`);
          } else {
            // Interactive mode - prompt for output file
            const answers = await inquirer.prompt([
              {
                type: 'input',
                name: 'output',
                message: 'Enter the path to save the generated tasks:',
                default: () => {
                  const inputBasename = path.basename(options.input, path.extname(options.input));
                  return path.join(path.dirname(options.input), `${inputBasename}_tasks.json`);
                }
              }
            ]);
            
            options.output = answers.output;
          }
        }
        
        // Check if output file exists and confirm overwrite if not forced
        if (fs.existsSync(options.output) && !options.force) {
          if (!process.stdin.isTTY) {
            ui.displayError('Output file already exists. Use --force to overwrite.');
            process.exit(1);
          }
          
          const answers = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'overwrite',
              message: `Output file ${options.output} already exists. Overwrite?`,
              default: false
            }
          ]);
          
          if (!answers.overwrite) {
            ui.displayInfo('Operation cancelled');
            process.exit(0);
          }
        }
        
        // Parse options
        const numTasks = parseInt(options.numTasks, 10);
        
        // Generate tasks
        const generateSpinner = ui.startSpinner(`Generating ${numTasks} tasks from PRD using ${options.provider}...`);
        
        try {
          const result = await parsePRD({
            inputFile: options.input,
            outputFile: options.output,
            numTasks,
            provider: options.provider,
            priority: options.priority,
            force: true
          });
          
          ui.stopSpinner(generateSpinner, 'Tasks generated successfully', 'success');
          
          // Display task generation results
          if (result.tasks && result.tasks.length > 0) {
            ui.displayTaskGenerationResults(result.tasks);
          } else {
            ui.displayWarning('No tasks were generated');
          }
        } catch (error) {
          ui.stopSpinner(generateSpinner, `Failed to generate tasks: ${error.message}`, 'error');
        }
      } catch (error) {
        ui.displayError(`An unexpected error occurred: ${error.message}`);
        process.exit(1);
      }
    });
    
  // MCP command
  programInstance
    .command('mcp')
    .description('Start the MCP server')
    .option('-p, --port <port>', 'Port to run the server on', '8766')
    .option('-h, --host <host>', 'Host to bind the server to', 'localhost')
    .option('-t, --timeout <ms>', 'Connection timeout in milliseconds', '60000')
    .option('-r, --reconnect <attempts>', 'Maximum reconnection attempts', '3')
    .action(async (options) => {
      try {
        // Display banner
        ui.displayBanner('Tascade AI', '1.0.0', 'MCP Server');
        
        // Check if the port is available
        const isPortAvailable = await checkPort(options.port);
        
        if (!isPortAvailable) {
          ui.displayError(`Port ${options.port} is already in use. Please specify a different port.`);
          
          // Try to find an available port
          for (let port = 8767; port <= 8775; port++) {
            const available = await checkPort(port.toString());
            if (available) {
              ui.displayInfo(`Port ${port} is available. You can use: tascade-cli mcp --port ${port}`);
              break;
            }
          }
          
          return;
        }
        
        // Start the MCP server
        const spinner = ui.startSpinner(`Starting MCP server on port ${options.port}...`);
        
        try {
          const server = startMCPServer(options.port);
          ui.stopSpinner(spinner, `MCP server started on port ${options.port}`, 'success');
          ui.displaySuccess(`Server is running at ws://localhost:${options.port}`);
          ui.displayInfo('Press Ctrl+C to stop the server');
          
          // Handle server exit
          process.on('SIGINT', () => {
            console.log(chalk.yellow('\nStopping MCP server...'));
            process.exit(0);
          });
          
          // Keep the process running
          process.stdin.resume();
        } catch (error) {
          ui.stopSpinner(spinner, `Failed to start MCP server: ${error.message}`, 'error');
        }
      } catch (error) {
        ui.displayError(`An unexpected error occurred: ${error.message}`);
        process.exit(1);
      }
    });
    
  // Task decomposition command
  programInstance
    .command('decompose')
    .description('Decompose a task into subtasks using AI')
    .option('-i, --id <id>', 'ID of the task to decompose')
    .option('-n, --num-subtasks <number>', 'Number of subtasks to generate', '5')
    .option('-p, --provider <provider>', 'AI provider to use', 'perplexity')
    .option('--instructions <text>', 'Custom instructions for the AI decomposer')
    .option('-d, --debug', 'Enable debug mode')
    .action(async (options) => {
      try {
        // Display banner
        ui.displayBanner('Tascade AI', '1.0.0', 'Task Generator');
        
        // Validate input file
        if (!options.inputFile) {
          if (!process.stdin.isTTY) {
            // Non-interactive mode
            ui.displayError('Input file is required');
            process.exit(1);
          }
          
          // Interactive mode - prompt for input file
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'inputFile',
              message: 'Enter the path to the PRD file:',
              validate: (input) => {
                if (!input) return 'Input file is required';
                if (!fs.existsSync(input)) return 'File does not exist';
                return true;
              }
            }
          ]);
          
          options.inputFile = answers.inputFile;
        }
        
        // Validate output file
        if (!options.outputFile) {
          if (!process.stdin.isTTY) {
            // Default output file based on input file
            const inputBasename = path.basename(options.inputFile, path.extname(options.inputFile));
            options.outputFile = path.join(path.dirname(options.inputFile), `${inputBasename}_tasks.json`);
          } else {
            // Interactive mode - prompt for output file
            const answers = await inquirer.prompt([
              {
                type: 'input',
                name: 'outputFile',
                message: 'Enter the path to save the generated tasks:',
                default: () => {
                  const inputBasename = path.basename(options.inputFile, path.extname(options.inputFile));
                  return path.join(path.dirname(options.inputFile), `${inputBasename}_tasks.json`);
                }
              }
            ]);
            
            options.outputFile = answers.outputFile;
          }
        }
        
        // Check if output file exists and confirm overwrite if not forced
        if (fs.existsSync(options.outputFile) && !options.force) {
          if (!process.stdin.isTTY) {
            ui.displayError('Output file already exists. Use --force to overwrite.');
            process.exit(1);
          }
          
          const answers = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'overwrite',
              message: `Output file ${options.outputFile} already exists. Overwrite?`,
              default: false
            }
          ]);
          
          if (!answers.overwrite) {
            ui.displayInfo('Operation cancelled');
            process.exit(0);
          }
        }
        
        // Parse options
        const numTasks = parseInt(options.numTasks, 10);
        const debug = options.debug || process.env.DEBUG === 'true';
        
        // MCP server connection details
        const port = process.env.MCP_PORT || '8766'; // Default Windsurf MCP port
        const url = `ws://localhost:${port}`;
        
        // Display connection info
        ui.displayInfo(`Connecting to MCP server at ${url}`);
        
        // Create the MCP client
        const client = createMCPClient({
          url,
          debug,
          timeout: 120000, // 120 second timeout
          maxReconnectAttempts: 3
        });
        
        // Create the context manager
        const contextManager = createMCPContextManager({
          debug
        });
        
        // Create a unique context ID for this session
        const contextId = contextManager.createContext(null, {
          provider: options.provider,
          numTasks,
          inputFile: options.inputFile,
          outputFile: options.outputFile,
          startTime: new Date().toISOString()
        });
        
        // Start spinner for connection
        const connectionSpinner = ui.startSpinner('Connecting to MCP server...');
        
        try {
          await client.connect();
          ui.stopSpinner(connectionSpinner, 'Connected to MCP server', 'success');
          
          // Add connection step to context
          contextManager.addStep(contextId, 'connect_mcp', { 
            success: true, 
            url: client.url
          });
          
          // Try to discover available tools if the server supports it
          try {
            const toolsSpinner = ui.startSpinner('Discovering available tools...');
            const tools = await client.discoverTools();
            ui.stopSpinner(toolsSpinner, `Discovered ${tools.size} tools on the MCP server`, 'success');
            
            contextManager.updateContext(contextId, { availableTools: Array.from(tools.keys()) });
          } catch (error) {
            // Tool discovery is optional, so we'll just log the error but continue
            ui.displayWarning(`Tool discovery not supported: ${error.message}`);
          }
          
          // Generate tasks
          const taskSpinner = ui.startSpinner(`Generating ${numTasks} tasks from PRD using ${options.provider}...`);
          
          // Update context with task generation parameters
          contextManager.updateContext(contextId, {
            taskGenerationStarted: new Date().toISOString(),
            taskGenerationParams: {
              inputFile: options.inputFile,
              outputFile: options.outputFile,
              numTasks,
              provider: options.provider,
              priority: options.priority,
              force: options.force || false
            }
          });
          
          // Add a step for task generation start
          contextManager.addStep(contextId, 'generate_tasks_start', {
            timestamp: new Date().toISOString(),
            params: {
              inputFile: options.inputFile,
              outputFile: options.outputFile,
              numTasks,
              provider: options.provider
            }
          });
          
          const result = await client.generateTasks({
            inputFile: options.inputFile,
            outputFile: options.outputFile,
            numTasks,
            provider: options.provider,
            priority: options.priority,
            force: true
          });
          
          if (result.success) {
            ui.stopSpinner(taskSpinner, `Successfully generated ${result.tasks.length} tasks!`, 'success');
            
            // Update context with successful task generation
            contextManager.updateContext(contextId, {
              taskGenerationCompleted: new Date().toISOString(),
              taskGenerationSuccess: true,
              tasksGenerated: result.tasks.length
            });
            
            // Add a step for successful task generation
            contextManager.addStep(contextId, 'generate_tasks_complete', {
              success: true,
              taskCount: result.tasks.length,
              timestamp: new Date().toISOString()
            });
            
            // Display task generation results
            ui.displayTaskGenerationResults(result.tasks);
            
            // Verify the file was actually created
            if (fs.existsSync(options.outputFile)) {
              ui.displaySuccess(`Tasks saved to ${options.outputFile}`);
              
              // Add file stats to context
              const fileStats = fs.statSync(options.outputFile);
              contextManager.updateContext(contextId, {
                outputFileStats: {
                  size: fileStats.size,
                  created: fileStats.birthtime.toISOString(),
                  modified: fileStats.mtime.toISOString()
                }
              });
            } else {
              ui.displayWarning(`Output file ${options.outputFile} was not found. The tasks may not have been saved correctly.`);
              contextManager.updateContext(contextId, {
                outputFileError: 'File not found after task generation'
              });
            }
          } else {
            ui.stopSpinner(taskSpinner, `Failed to generate tasks: ${result.error || 'Unknown error'}`, 'error');
            
            // Update context with failed task generation
            contextManager.updateContext(contextId, {
              taskGenerationCompleted: new Date().toISOString(),
              taskGenerationSuccess: false,
              taskGenerationError: result.error || 'Unknown error'
            });
            
            // Add a step for failed task generation
            contextManager.addStep(contextId, 'generate_tasks_complete', {
              success: false,
              error: result.error || 'Unknown error',
              timestamp: new Date().toISOString()
            });
          }
        } catch (error) {
          ui.stopSpinner(connectionSpinner, `Error: ${error.message}`, 'error');
          ui.displayError(`Failed to generate tasks: ${error.message}`);
          
          // Update context with error
          contextManager.updateContext(contextId, {
            taskGenerationCompleted: new Date().toISOString(),
            taskGenerationSuccess: false,
            taskGenerationError: error.message
          });
          
          // Add a step for error
          contextManager.addStep(contextId, 'generate_tasks_error', {
            error: error.message,
            timestamp: new Date().toISOString()
          });
        } finally {
          // Export context for future reference
          try {
            const contextExportPath = path.join(path.dirname(options.outputFile), `context-${contextId}.json`);
            const exportedContext = contextManager.exportContext(contextId);
            fs.writeFileSync(contextExportPath, JSON.stringify(exportedContext, null, 2));
            ui.displayInfo(`Context data exported to ${contextExportPath}`);
          } catch (error) {
            ui.displayWarning(`Failed to export context data: ${error.message}`);
          }
          
          // Disconnect from the MCP server
          ui.displayInfo('Disconnecting from MCP server...');
          client.disconnect('Task generation completed');
          
          // Final context update
          contextManager.updateContext(contextId, {
            completed: true,
            completionTime: new Date().toISOString()
          });
        }
      } catch (error) {
        ui.displayError('An unexpected error occurred', error);
        process.exit(1);
      }
    });
    
  // MCP server status command
  programInstance
    .command('mcp-status')
    .description('Check the status of the MCP server')
    .option('-p, --port <port>', 'MCP server port', process.env.MCP_PORT || '8766')
    .option('-d, --debug', 'Enable debug mode')
    .action(async (options) => {
      try {
        // Display banner
        ui.displayBanner('Tascade AI', '1.0.0', 'MCP Status');
        
        const debug = options.debug || process.env.DEBUG === 'true';
        const url = `ws://localhost:${options.port}`;
        
        // Create the MCP client
        const client = createMCPClient({
          url,
          debug,
          timeout: 5000, // Short timeout for status check
          maxReconnectAttempts: 0 // Don't try to reconnect for status check
        });
        
        // Start spinner for connection
        const connectionSpinner = ui.startSpinner('Checking MCP server status...');
        
        try {
          await client.connect();
          ui.stopSpinner(connectionSpinner, 'MCP server is running', 'success');
          
          // Try to discover available tools
          try {
            const toolsSpinner = ui.startSpinner('Discovering available tools...');
            const tools = await client.discoverTools();
            ui.stopSpinner(toolsSpinner, `Discovered ${tools.size} tools on the MCP server`, 'success');
            
            // Display tools in a table
            const toolsData = Array.from(tools.entries()).map(([name, schema]) => [
              name,
              schema.description || 'No description'
            ]);
            
            if (toolsData.length > 0) {
              console.log('\n' + ui.createTable(['Tool Name', 'Description'], toolsData));
            }
          } catch (error) {
            ui.displayWarning(`Tool discovery not supported: ${error.message}`);
          }
          
          // Display MCP status
          ui.displayMCPStatus({
            connected: true,
            url,
            contextId: client.contextId,
            reconnectAttempts: client.reconnectAttempts
          });
          
          // Disconnect from the server
          client.disconnect('Status check completed');
        } catch (error) {
          ui.stopSpinner(connectionSpinner, 'MCP server is not running', 'error');
          ui.displayError(`Failed to connect to MCP server: ${error.message}`);
          
          // Display MCP status
          ui.displayMCPStatus({
            connected: false,
            url,
            contextId: null,
            reconnectAttempts: 0
          });
        }
      } catch (error) {
        ui.displayError('An unexpected error occurred', error);
        process.exit(1);
      }
    });
    
  // Start MCP server command
  programInstance
    .command('start-mcp')
    .description('Start the MCP server')
    .option('-p, --port <port>', 'Port to run the server on', process.env.MCP_PORT || '8766')
    .option('-d, --debug', 'Enable debug mode')
    .action(async (options) => {
      try {
        // Display banner
        ui.displayBanner('Tascade AI', '1.0.0', 'MCP Server');
        
        const debug = options.debug || process.env.DEBUG === 'true';
        const port = options.port;
        
        // Check if the port is already in use
        const isPortInUse = await new Promise((resolve) => {
          const net = require('net');
          const tester = net.createServer()
            .once('error', () => resolve(true))
            .once('listening', () => {
              tester.once('close', () => resolve(false)).close();
            })
            .listen(port);
        });
        
        if (isPortInUse) {
          ui.displayError(`Port ${port} is already in use. Please specify a different port.`);
          process.exit(1);
        }
        
        // Import the server dynamically to avoid circular dependencies
        const { startMCPServer } = await import('../mcp/server.js');
        
        // Start the server
        const serverSpinner = ui.startSpinner(`Starting MCP server on port ${port}...`);
        
        try {
          const server = await startMCPServer({ port, debug });
          ui.stopSpinner(serverSpinner, `MCP server started on port ${port}`, 'success');
          
          // Display server info
          ui.displayBox(
            `MCP server is running on port ${port}\n\n` +
            `To connect to the server, use:\n` +
            `  ws://localhost:${port}\n\n` +
            `Press Ctrl+C to stop the server`,
            'info'
          );
          
          // Handle graceful shutdown
          process.on('SIGINT', async () => {
            ui.displayInfo('Stopping MCP server...');
            await server.stop();
            ui.displaySuccess('MCP server stopped');
            process.exit(0);
          });
          
          // Keep the process running
          await new Promise(() => {}); // Never resolves
        } catch (error) {
          ui.stopSpinner(serverSpinner, `Failed to start MCP server: ${error.message}`, 'error');
          ui.displayError(`Failed to start MCP server: ${error.message}`);
          process.exit(1);
        }
      } catch (error) {
        ui.displayError('An unexpected error occurred', error);
        process.exit(1);
      }
    });
}

/**
 * Setup the CLI application
 * @returns {Object} Configured Commander program
 */
function setupCLI() {
  // Create a new Commander program
  const cli = new program.Command();
  
  // Configure the CLI
  cli
    .name('tascade-ai')
    .description('Tascade AI - AI-powered task management system for project planning and execution')
    .version('0.1.0')
    .option('-d, --debug', 'Enable debug mode')
    .option('-s, --silent', 'Suppress all output except errors')
    .option('-c, --config <path>', 'Path to configuration file');
  
  // Register commands
  registerCommands(cli);
  
  // Add help command
  cli
    .command('help')
    .description('Display help information')
    .action(() => {
      ui.displayHelp([
        // Task Management
        { name: 'tasks', description: 'Manage tasks (list, add, view, update)' },
        { name: 'generate', description: 'Generate tasks from a PRD file using AI' },
        { name: 'decompose', description: 'Decompose a task into subtasks using AI' },
        
        // Time Tracking
        { name: 'track', description: 'Track time for tasks (start, stop, list)' },
        { name: 'report', description: 'Generate time tracking reports' },
        
        // Server Management
        { name: 'start', description: 'Start the Tascade AI server' },
        { name: 'mcp', description: 'Start the MCP server' },
        { name: 'mcp-status', description: 'Check the status of the MCP server' },
        
        // Recommendations
        { name: 'recommend', description: 'Get task recommendations' },
        
        // Configuration
        { name: 'config', description: 'Configure Tascade AI settings' },
        { name: 'models', description: 'Manage AI models and providers' },
        
        // Utilities
        { name: 'init', description: 'Initialize a new Tascade AI project' },
        { name: 'help', description: 'Display help information' }
      ]);
    });
  
  return cli;
}

/**
 * Parse arguments and run the CLI
 * @param {Array} argv - Command-line arguments
 */
function runCLI(argv = process.argv) {
  // Check dependencies before running commands
  if (!checkDependencies()) {
    console.error('Missing required dependencies. Please run: npm install');
    process.exit(1);
  }
  
  const cli = setupCLI();
  cli.parse(argv);
  
  // If no command is specified, display help
  if (!argv.slice(2).length) {
    ui.displayHelp([
      // Task Management
      { name: 'tasks', description: 'Manage tasks (list, add, view, update)' },
      { name: 'generate', description: 'Generate tasks from a PRD file using AI' },
      { name: 'decompose', description: 'Decompose a task into subtasks using AI' },
      
      // Time Tracking
      { name: 'track', description: 'Track time for tasks (start, stop, list)' },
      { name: 'report', description: 'Generate time tracking reports' },
      
      // Server Management
      { name: 'start', description: 'Start the Tascade AI server' },
      { name: 'mcp', description: 'Start the MCP server' },
      { name: 'mcp-status', description: 'Check the status of the MCP server' },
      
      // Recommendations
      { name: 'recommend', description: 'Get task recommendations' },
      
      // Configuration
      { name: 'config', description: 'Configure Tascade AI settings' },
      { name: 'models', description: 'Manage AI models and providers' },
      
      // Utilities
      { name: 'init', description: 'Initialize a new Tascade AI project' },
      { name: 'help', description: 'Display help information' }
    ]);
  }
}

// Export all functions and utilities
export {
  registerCommands,
  setupCLI,
  runCLI,
  checkPort,
  startServer,
  startMCPServer,
  connectToServer,
  sendCommand,
  checkDependencies
};

// Default export
export default {
  registerCommands,
  setupCLI,
  runCLI,
  checkPort,
  startServer,
  startMCPServer,
  connectToServer,
  sendCommand,
  checkDependencies
};
