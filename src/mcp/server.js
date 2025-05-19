#!/usr/bin/env node

/**
 * Enhanced MCP Server for Tascade AI
 * 
 * This implementation is inspired by the claude-task-master project structure
 * and incorporates best practices for MCP server design.
 */

import { WebSocketServer } from 'ws';
import { EventEmitter } from 'events';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import dotenv from 'dotenv';
import { registerFeatureIntegrations } from './integration/index.js';

// Load environment variables
dotenv.config();

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectDir = path.join(__dirname, '../..');

/**
 * Enhanced MCP Server class for Tascade AI
 */
class TascadeMCPServer extends EventEmitter {
  /**
   * Create a new MCP server
   * @param {Object} options - Server options
   * @param {number} options.port - Port to listen on
   * @param {string} options.name - Server name
   * @param {string} options.version - Server version
   */
  constructor(options = {}) {
    super();
    
    // Get version from package.json
    const packagePath = path.join(projectDir, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    this.options = {
      port: options.port || parseInt(process.env.MCP_PORT || '8767', 10),
      name: options.name || 'Tascade AI MCP Server',
      version: options.version || packageJson.version || '1.0.0'
    };
    
    this.server = null;
    this.clients = new Set();
    this.mcpServer = null;
    this.db = null;
    this.features = {};
    this.tools = new Map();
    this.resources = new Map();
    this.handlers = new Map();
    
    // Bind methods
    this.start = this.start.bind(this);
    this.stop = this.stop.bind(this);
    this.handleConnection = this.handleConnection.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.registerTool = this.registerTool.bind(this);
    this.addResource = this.addResource.bind(this);
    this.setDatabase = this.setDatabase.bind(this);
    this.registerMCPServer = this.registerMCPServer.bind(this);
    
    // Register default tools
    this.registerDefaultTools();
  }
  
  /**
   * Register a tool with the MCP server
   * @param {string} name - Tool name
   * @param {Function} handler - Tool handler function
   * @param {Object} schema - Tool schema
   */
  registerTool(name, handler, schema = {}) {
    this.tools.set(name, {
      name,
      handler,
      schema
    });
    
    console.log(`Registered tool: ${name}`);
    return this;
  }
  
  /**
   * Set the database connection
   * @param {Object} db - Database connection
   * @returns {TascadeMCPServer} - Server instance for chaining
   */
  setDatabase(db) {
    this.db = db;
    return this;
  }

  /**
   * Register an MCP server instance
   * @param {Object} mcpServer - MCP server instance
   * @returns {TascadeMCPServer} - Server instance for chaining
   */
  registerMCPServer(mcpServer) {
    this.mcpServer = mcpServer;
    return this;
  }
  
  /**
   * Add a resource to the MCP server
   * @param {string} uri - Resource URI
   * @param {any} content - Resource content
   */
  addResource(uri, content) {
    this.resources.set(uri, content);
    return this;
  }
  
  /**
   * Register default tools with the MCP server
   */
  registerDefaultTools() {
    // Generate tasks tool
    this.registerTool('generate-tasks', async (params, client) => {
      const { input_file, output_file, num_tasks = 5, provider = 'perplexity', priority = 'medium', force = false } = params;
      
      if (!input_file) {
        return { error: 'Missing required parameter: input_file' };
      }
      
      if (!output_file) {
        return { error: 'Missing required parameter: output_file' };
      }
      
      // Build the command
      const cmd = [
        path.join(projectDir, 'bin', 'tascade-ai.js'),
        'generate',
        '--input', input_file,
        '--output', output_file
      ];
      
      // Add optional parameters
      if (num_tasks) {
        cmd.push('--num-tasks', num_tasks.toString());
      }
      
      if (provider) {
        cmd.push('--provider', provider);
      }
      
      if (priority) {
        cmd.push('--priority', priority);
      }
      
      if (force) {
        cmd.push('--force');
      }
      
      console.log(`Running command: node ${cmd.join(' ')}`);
      
      try {
        // Run the command
        const result = await this.runCommand('node', cmd, {
          env: {
            ...process.env,
            ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
            PERPLEXITY_API_KEY: process.env.PERPLEXITY_API_KEY,
            OPENAI_API_KEY: process.env.OPENAI_API_KEY,
            MODEL: process.env.MODEL,
            PERPLEXITY_MODEL: process.env.PERPLEXITY_MODEL,
            MAX_TOKENS: process.env.MAX_TOKENS,
            TEMPERATURE: process.env.TEMPERATURE,
            DEFAULT_SUBTASKS: process.env.DEFAULT_SUBTASKS,
            DEFAULT_PRIORITY: process.env.DEFAULT_PRIORITY
          }
        });
        
        if (result.code !== 0) {
          return { 
            error: `Command failed with code ${result.code}: ${result.stderr}`,
            stdout: result.stdout,
            stderr: result.stderr
          };
        }
        
        // Read the output file
        try {
          const tasks = JSON.parse(fs.readFileSync(output_file, 'utf-8'));
          
          return {
            success: true,
            command: 'generate-tasks',
            tasks: tasks.tasks,
            metadata: tasks.metadata || {},
            message: 'Tasks generated successfully',
            timestamp: new Date().toISOString()
          };
        } catch (error) {
          return { 
            error: `Failed to read generated tasks: ${error.message}`,
            command: 'generate-tasks',
            timestamp: new Date().toISOString()
          };
        }
      } catch (error) {
        return { 
          error: `Failed to run command: ${error.message}`,
          command: 'generate-tasks',
          timestamp: new Date().toISOString()
        };
      }
    }, {
      description: 'Generate tasks from a PRD file',
      parameters: {
        input_file: { type: 'string', description: 'Path to the PRD file' },
        output_file: { type: 'string', description: 'Path to save the generated tasks' },
        num_tasks: { type: 'number', description: 'Number of tasks to generate' },
        provider: { type: 'string', description: 'AI provider to use' },
        priority: { type: 'string', description: 'Default priority for tasks' },
        force: { type: 'boolean', description: 'Force overwrite of existing output file' }
      }
    });
    
    // List tools tool
    this.registerTool('list-tools', async (params, client) => {
      const tools = Array.from(this.tools.values()).map(tool => ({
        name: tool.name,
        description: tool.schema.description || '',
        parameters: tool.schema.parameters || {}
      }));
      
      return {
        success: true,
        tools,
        timestamp: new Date().toISOString()
      };
    }, {
      description: 'List available tools',
      parameters: {}
    });
    
    // List resources tool
    this.registerTool('list-resources', async (params, client) => {
      const resources = Array.from(this.resources.keys());
      
      return {
        success: true,
        resources,
        timestamp: new Date().toISOString()
      };
    }, {
      description: 'List available resources',
      parameters: {}
    });
    
    // Get resource tool
    this.registerTool('get-resource', async (params, client) => {
      const { uri } = params;
      
      if (!uri) {
        return { error: 'Missing required parameter: uri' };
      }
      
      if (!this.resources.has(uri)) {
        return { error: `Resource not found: ${uri}` };
      }
      
      return {
        success: true,
        resource: this.resources.get(uri),
        timestamp: new Date().toISOString()
      };
    }, {
      description: 'Get a resource',
      parameters: {
        uri: { type: 'string', description: 'Resource URI' }
      }
    });
  }
  
  /**
   * Run a command and return the result
   * @param {string} command - Command to run
   * @param {Array<string>} args - Command arguments
   * @param {Object} options - Command options
   * @returns {Promise<Object>} - Command result
   */
  runCommand(command, args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, { 
        stdio: ['ignore', 'pipe', 'pipe'],
        ...options
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log(`stdout: ${data.toString()}`);
      });
      
      child.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error(`stderr: ${data.toString()}`);
      });
      
      child.on('close', (code) => {
        resolve({
          code,
          stdout,
          stderr
        });
      });
      
      child.on('error', (error) => {
        reject(error);
      });
    });
  }
  
  /**
   * Start the MCP server
   * @returns {Promise<TascadeMCPServer>} - Server instance
   */
  async start() {
    return new Promise((resolve, reject) => {
      try {
        this.server = new WebSocketServer({ port: this.options.port });
        
        this.server.on('connection', this.handleConnection);
        
        this.server.on('error', (error) => {
          console.error(`Server error: ${error.message}`);
          this.emit('error', error);
          reject(error);
        });
        
        this.server.on('listening', () => {
          console.log(`${this.options.name} v${this.options.version} running at ws://localhost:${this.options.port}`);
          this.emit('start');
          resolve(this);
        });
      } catch (error) {
        console.error(`Failed to start server: ${error.message}`);
        this.emit('error', error);
        reject(error);
      }
    });
  }
  
  /**
   * Stop the MCP server
   * @returns {Promise<void>}
   */
  async stop() {
    return new Promise((resolve, reject) => {
      if (!this.server) {
        resolve();
        return;
      }
      
      // Close all client connections
      for (const client of this.clients) {
        client.close();
      }
      
      this.server.close((error) => {
        if (error) {
          console.error(`Error stopping server: ${error.message}`);
          reject(error);
          return;
        }
        
        console.log('Server stopped');
        this.emit('stop');
        resolve();
      });
    });
  }
  
  /**
   * Handle a new WebSocket connection
   * @param {WebSocket} ws - WebSocket connection
   * @param {Object} request - HTTP request
   */
  handleConnection(ws, request) {
    console.log('Client connected');
    this.clients.add(ws);
    
    // Send welcome message
    ws.send(JSON.stringify({
      message: `Welcome to ${this.options.name} v${this.options.version}`,
      timestamp: new Date().toISOString()
    }));
    
    // Set up event handlers
    ws.on('message', (message) => this.handleMessage(ws, message));
    
    ws.on('close', () => {
      console.log('Client disconnected');
      this.clients.delete(ws);
    });
    
    ws.on('error', (error) => {
      console.error(`Client error: ${error.message}`);
      this.clients.delete(ws);
    });
  }
  
  /**
   * Handle a WebSocket message
   * @param {WebSocket} client - WebSocket client
   * @param {WebSocket.Data} message - Message data
   */
  async handleMessage(client, message) {
    try {
      const data = JSON.parse(message.toString());
      
      if (!data.command) {
        client.send(JSON.stringify({ 
          id: data.id,
          error: 'Missing command',
          timestamp: new Date().toISOString()
        }));
        return;
      }
      
      console.log(`Received command: ${data.command}`);
      
      // Check if the command exists
      if (!this.tools.has(data.command)) {
        client.send(JSON.stringify({ 
          id: data.id,
          error: {
            code: 'unknown_command',
            message: `Unknown command: ${data.command}`
          },
          timestamp: new Date().toISOString()
        }));
        return;
      }
      
      // Execute the command
      try {
        const tool = this.tools.get(data.command);
        const result = await tool.handler(data.params || {}, client);
        
        client.send(JSON.stringify({
          id: data.id,
          ...result,
          timestamp: new Date().toISOString()
        }));
      } catch (error) {
        console.error(`Error executing command ${data.command}: ${error.message}`);
        client.send(JSON.stringify({ 
          id: data.id,
          error: `Error executing command: ${error.message}`,
          timestamp: new Date().toISOString()
        }));
      }
    } catch (error) {
      console.error(`Error parsing message: ${error.message}`);
      client.send(JSON.stringify({ 
        error: `Error parsing message: ${error.message}`,
        timestamp: new Date().toISOString()
      }));
    }
  }
  
  /**
   * Run a command and return the result
   * @param {string} command - Command to run
   * @param {Array<string>} args - Command arguments
   * @param {Object} options - Command options
   * @returns {Promise<Object>} - Command result
   */
  runCommand(command, args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, { 
        stdio: ['ignore', 'pipe', 'pipe'],
        ...options
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log(`stdout: ${data.toString()}`);
      });
      
      child.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error(`stderr: ${data.toString()}`);
      });
      
      child.on('close', (code) => {
        resolve({
          code,
          stdout,
          stderr
        });
      });
      
      child.on('error', (error) => {
        reject(error);
      });
    });
  }
}

/**
 * Create and start the MCP server
 */
async function main() {
  try {
    // Create database connection (placeholder for now)
    const dbConnection = {
      getTask: async (id) => {
        console.log(`Mock DB: Getting task ${id}`);
        return {
          id,
          title: 'Sample Task',
          description: 'This is a sample task for testing',
          status: 'pending',
          priority: 'medium',
          subtasks: [],
          dependencies: []
        };
      },
      updateTask: async (task) => {
        console.log(`Mock DB: Updating task ${task.id}`);
        return task;
      },
      getAllTasks: async () => {
        console.log('Mock DB: Getting all tasks');
        return [];
      },
      getTasksByProject: async (projectId) => {
        console.log(`Mock DB: Getting tasks for project ${projectId}`);
        return [];
      }
    };
    
    // Create MCP server instance (placeholder for now)
    const mcpServerInstance = {
      tool: (name, options, handler) => {
        console.log(`Registered tool: ${name}`);
        return mcpServerInstance;
      }
    };
    
    // Create and start the server
    const server = new TascadeMCPServer()
      .setDatabase(dbConnection)
      .registerMCPServer(mcpServerInstance);
    
    await server.start();
    
    console.log(`Tascade AI MCP Server started on port ${server.options.port}`);
    
    // Handle process termination
    process.on('SIGINT', async () => {
      console.log('Shutting down Tascade AI MCP Server...');
      await server.stop();
      process.exit(0);
    });
  } catch (error) {
    console.error('Failed to start Tascade AI MCP Server:', error);
    process.exit(1);
  }
}

// If this file is run directly, start the server
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}

export default TascadeMCPServer;
