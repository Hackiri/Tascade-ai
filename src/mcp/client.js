#!/usr/bin/env node

/**
 * MCP Client Module for Tascade AI
 * 
 * This module provides a robust client implementation for interacting with MCP servers.
 * It handles connection management, context tracking, error handling, and reconnection logic.
 */

import WebSocket from 'ws';
import { EventEmitter } from 'events';
import chalk from 'chalk';
import { v4 as uuidv4 } from 'uuid';

/**
 * MCP Client class for managing connections to MCP servers
 * Implements context management and sequential thinking for robust operation
 * 
 * Enhanced with features inspired by claude-task-master:
 * - Tool discovery and introspection
 * - Resource management
 * - Improved error handling and recovery
 * - Support for multiple concurrent commands
 * - Command batching and sequencing
 */
export class MCPClient extends EventEmitter {
  /**
   * Create a new MCP client
   * @param {Object} options - Configuration options
   * @param {string} options.url - WebSocket URL of the MCP server
   * @param {number} options.timeout - Command timeout in milliseconds (default: 30000)
   * @param {number} options.maxReconnectAttempts - Maximum reconnection attempts (default: 3)
   * @param {number} options.reconnectDelay - Base delay between reconnection attempts in ms (default: 2000)
   * @param {boolean} options.debug - Enable debug logging (default: false)
   */
  constructor(options = {}) {
    super();
    
    this.url = options.url || 'ws://localhost:8765';
    this.timeout = options.timeout || 30000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 3;
    this.reconnectDelay = options.reconnectDelay || 2000;
    this.debug = options.debug || false;
    
    // Connection state
    this.ws = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.intentionalClose = false;
    
    // Command tracking
    this.pendingCommands = new Map();
    this.contextId = null;
    this.sequenceId = 0;
    
    // Tool and resource discovery
    this.availableTools = new Map();
    this.availableResources = new Map();
    this.toolsDiscovered = false;
    
    // Bind methods to preserve 'this' context
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.sendCommand = this.sendCommand.bind(this);
    this.discoverTools = this.discoverTools.bind(this);
    this.listResources = this.listResources.bind(this);
    this.getResource = this.getResource.bind(this);
    this.batchCommands = this.batchCommands.bind(this);
    this._handleOpen = this._handleOpen.bind(this);
    this._handleMessage = this._handleMessage.bind(this);
    this._handleError = this._handleError.bind(this);
    this._handleClose = this._handleClose.bind(this);
  }
  
  /**
   * Connect to the MCP server
   * @returns {Promise} Resolves when connected, rejects on failure
   */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.connected && this.ws) {
        this._log('Already connected to MCP server');
        return resolve();
      }
      
      this._log(`Connecting to MCP server at ${this.url}...`);
      
      try {
        this.ws = new WebSocket(this.url);
        
        // Set up one-time event for this connection attempt
        const onceConnected = () => {
          this.connected = true;
          this.reconnectAttempts = 0;
          this._log('Connected to MCP server', 'success');
          resolve();
        };
        
        const onceError = (error) => {
          this._log(`Connection error: ${error.message}`, 'error');
          reject(error);
        };
        
        this.ws.once('open', () => {
          this.ws.removeListener('error', onceError);
          onceConnected();
        });
        
        this.ws.once('error', (error) => {
          this.ws.removeListener('open', onceConnected);
          onceError(error);
        });
        
        // Set up ongoing event handlers
        this.ws.on('message', this._handleMessage);
        this.ws.on('error', this._handleError);
        this.ws.on('close', this._handleClose);
      } catch (error) {
        this._log(`Failed to create WebSocket: ${error.message}`, 'error');
        reject(error);
      }
    });
  }
  
  /**
   * Disconnect from the MCP server
   * @param {string} reason - Reason for disconnection
   */
  disconnect(reason = 'Client requested disconnect') {
    if (!this.connected || !this.ws) {
      this._log('Not connected to MCP server');
      return;
    }
    
    this._log(`Disconnecting from MCP server: ${reason}`);
    this.intentionalClose = true;
    
    // Clear any pending commands
    for (const [id, command] of this.pendingCommands.entries()) {
      clearTimeout(command.timeoutId);
      command.reject(new Error('Connection closed'));
      this.pendingCommands.delete(id);
    }
    
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.close(1000, reason);
    }
  }
  
  /**
   * Send a command to the MCP server
   * @param {string} command - Command name
   * @param {Object} params - Command parameters
   * @param {Object} options - Command options
   * @param {number} options.timeout - Command timeout in milliseconds
   * @returns {Promise} Resolves with command result, rejects on error
   */
  sendCommand(command, params = {}, options = {}) {
    return new Promise(async (resolve, reject) => {
      if (!this.connected) {
        try {
          await this.connect();
        } catch (error) {
          return reject(new Error(`Failed to connect: ${error.message}`));
        }
      }
      
      const commandId = uuidv4();
      const timeout = options.timeout || this.timeout;
      
      // Create the command message with context and sequence tracking
      const message = {
        id: commandId,
        command,
        params,
        context: this.contextId,
        sequence: this.sequenceId++
      };
      
      // Set up command timeout
      const timeoutId = setTimeout(() => {
        if (this.pendingCommands.has(commandId)) {
          this.pendingCommands.delete(commandId);
          reject(new Error(`Command timed out after ${timeout}ms`));
        }
      }, timeout);
      
      // Store the pending command
      this.pendingCommands.set(commandId, {
        command,
        params,
        timeoutId,
        resolve,
        reject,
        sentAt: Date.now()
      });
      
      // Send the command
      this._log(`Sending command: ${command}`, 'info', message);
      this.ws.send(JSON.stringify(message));
    });
  }
  
  /**
   * Discover available tools from the MCP server
   * @returns {Promise<Map<string, Object>>} Map of tool names to tool schemas
   */
  async discoverTools() {
    try {
      const response = await this.sendCommand('list-tools');
      
      if (response.success && Array.isArray(response.tools)) {
        // Clear existing tools
        this.availableTools.clear();
        
        // Add each tool to the map
        for (const tool of response.tools) {
          this.availableTools.set(tool.name, {
            name: tool.name,
            description: tool.description,
            parameters: tool.parameters
          });
        }
        
        this.toolsDiscovered = true;
        this._log(`Discovered ${this.availableTools.size} tools`, 'info');
        this.emit('tools_discovered', Array.from(this.availableTools.values()));
      }
      
      return this.availableTools;
    } catch (error) {
      this._log(`Failed to discover tools: ${error.message}`, 'error');
      throw error;
    }
  }
  
  /**
   * List available resources from the MCP server
   * @param {Object} options - Options for listing resources
   * @param {string} options.cursor - Pagination cursor
   * @returns {Promise<Array<string>>} List of resource URIs
   */
  async listResources(options = {}) {
    try {
      const response = await this.sendCommand('list-resources', options);
      
      if (response.success && Array.isArray(response.resources)) {
        // Update the available resources map
        for (const uri of response.resources) {
          if (!this.availableResources.has(uri)) {
            this.availableResources.set(uri, null); // Placeholder until resource is fetched
          }
        }
        
        this._log(`Found ${response.resources.length} resources`, 'info');
        this.emit('resources_listed', response.resources);
      }
      
      return response.resources || [];
    } catch (error) {
      this._log(`Failed to list resources: ${error.message}`, 'error');
      throw error;
    }
  }
  
  /**
   * Get a resource from the MCP server
   * @param {string} uri - Resource URI
   * @returns {Promise<any>} Resource content
   */
  async getResource(uri) {
    try {
      // Check if we already have the resource cached
      if (this.availableResources.has(uri) && this.availableResources.get(uri) !== null) {
        return this.availableResources.get(uri);
      }
      
      const response = await this.sendCommand('get-resource', { uri });
      
      if (response.success && response.resource) {
        // Cache the resource
        this.availableResources.set(uri, response.resource);
        this._log(`Retrieved resource: ${uri}`, 'info');
        this.emit('resource_retrieved', { uri, resource: response.resource });
        return response.resource;
      }
      
      throw new Error(response.error || 'Failed to get resource');
    } catch (error) {
      this._log(`Failed to get resource ${uri}: ${error.message}`, 'error');
      throw error;
    }
  }
  
  /**
   * Execute a batch of commands in sequence
   * @param {Array<Object>} commands - Array of command objects
   * @param {string} commands[].command - Command name
   * @param {Object} commands[].params - Command parameters
   * @param {Object} options - Batch options
   * @param {boolean} options.stopOnError - Whether to stop on first error
   * @returns {Promise<Array<Object>>} Array of command results
   */
  async batchCommands(commands, options = {}) {
    const { stopOnError = true } = options;
    const results = [];
    
    for (let i = 0; i < commands.length; i++) {
      const { command, params } = commands[i];
      
      try {
        this._log(`Executing batch command ${i + 1}/${commands.length}: ${command}`, 'info');
        const result = await this.sendCommand(command, params);
        results.push(result);
      } catch (error) {
        this._log(`Error in batch command ${i + 1}/${commands.length}: ${error.message}`, 'error');
        results.push({ error: error.message });
        
        if (stopOnError) {
          this._log('Stopping batch execution due to error', 'warn');
          break;
        }
      }
    }
    
    return results;
  }
  
  /**
   * Generate tasks from a PRD file
   * @param {Object} options - Task generation options
   * @param {string} options.inputFile - Path to the PRD file
   * @param {string} options.outputFile - Path to save the generated tasks
   * @param {number} options.numTasks - Number of tasks to generate
   * @param {string} options.provider - AI provider to use
   * @param {string} options.priority - Default priority for tasks
   * @param {boolean} options.force - Force overwrite of existing output file
   * @returns {Promise} Resolves with generated tasks, rejects on error
   */
  generateTasks(options) {
    const {
      inputFile,
      outputFile,
      numTasks = 5,
      provider = 'perplexity',
      priority = 'medium',
      force = false
    } = options;
    
    if (!inputFile) {
      return Promise.reject(new Error('Input file is required'));
    }
    
    if (!outputFile) {
      return Promise.reject(new Error('Output file is required'));
    }
    
    return this.sendCommand('generate-tasks', {
      input_file: inputFile,
      output_file: outputFile,
      num_tasks: numTasks,
      provider,
      priority,
      force
    });
  }
  
  /**
   * Handle WebSocket open event
   * @private
   */
  _handleOpen() {
    this.connected = true;
    this.reconnectAttempts = 0;
    this.emit('connected');
  }
  
  /**
   * Handle WebSocket message event
   * @param {WebSocket.Data} data - Message data
   * @private
   */
  _handleMessage(data) {
    try {
      const response = JSON.parse(data.toString());
      this._log('Received response', 'debug', response);
      
      // Handle welcome message and initialize context
      if (response.message && response.message.includes('Welcome')) {
        this.emit('welcome', response);
        
        // Initialize context if not already set
        if (!this.contextId) {
          this.contextId = uuidv4();
          this._log(`Initialized context: ${this.contextId}`, 'debug');
        }
        return;
      }
      
      // Handle command response with ID
      if (response.id && this.pendingCommands.has(response.id)) {
        const pendingCommand = this.pendingCommands.get(response.id);
        clearTimeout(pendingCommand.timeoutId);
        
        if (response.error) {
          pendingCommand.reject(new Error(
            typeof response.error === 'object' 
              ? response.error.message || JSON.stringify(response.error)
              : response.error
          ));
        } else {
          pendingCommand.resolve(response);
        }
        
        this.pendingCommands.delete(response.id);
        return;
      }
      
      // Handle command response without ID but with command name
      // This handles cases where the server responds without including the original command ID
      if (response.command) {
        // Find any pending commands with matching command name
        for (const [id, pendingCommand] of this.pendingCommands.entries()) {
          if (pendingCommand.command === response.command) {
            this._log(`Matched response to pending command by name: ${response.command}`, 'debug');
            clearTimeout(pendingCommand.timeoutId);
            
            if (response.error) {
              pendingCommand.reject(new Error(
                typeof response.error === 'object' 
                  ? response.error.message || JSON.stringify(response.error)
                  : response.error
              ));
            } else {
              pendingCommand.resolve(response);
            }
            
            this.pendingCommands.delete(id);
            return;
          }
        }
      }
      
      // Handle server-initiated messages
      this.emit('message', response);
    } catch (error) {
      this._log(`Error parsing message: ${error.message}`, 'error');
      this.emit('error', new Error(`Failed to parse server message: ${error.message}`));
    }
  }
  
  /**
   * Handle WebSocket error event
   * @param {Error} error - Error object
   * @private
   */
  _handleError(error) {
    this._log(`WebSocket error: ${error.message}`, 'error');
    this.emit('error', error);
    
    // Don't attempt to reconnect if it was an intentional close
    if (this.intentionalClose) {
      return;
    }
    
    this._attemptReconnect();
  }
  
  /**
   * Handle WebSocket close event
   * @param {number} code - Close code
   * @param {string} reason - Close reason
   * @private
   */
  _handleClose(code, reason) {
    const wasConnected = this.connected;
    this.connected = false;
    
    this._log(`WebSocket closed: ${code}${reason ? `, ${reason}` : ''}`, wasConnected ? 'warn' : 'debug');
    this.emit('disconnected', { code, reason });
    
    // Don't attempt to reconnect if it was an intentional close
    if (this.intentionalClose) {
      this.intentionalClose = false;
      return;
    }
    
    this._attemptReconnect();
  }
  
  /**
   * Attempt to reconnect to the MCP server
   * @private
   */
  _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this._log('Maximum reconnection attempts reached', 'error');
      this.emit('reconnect_failed');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    this._log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`, 'warn');
    this.emit('reconnecting', { attempt: this.reconnectAttempts, max: this.maxReconnectAttempts });
    
    setTimeout(() => {
      if (!this.connected) {
        // Try to find an alternative port if the original port is unavailable
        if (this.reconnectAttempts > 1) {
          this._tryAlternativePorts()
            .then(newUrl => {
              if (newUrl && newUrl !== this.url) {
                this._log(`Switching to alternative port: ${newUrl}`, 'info');
                this.url = newUrl;
              }
              return this.connect();
            })
            .then(() => this.emit('reconnected'))
            .catch(error => {
              this._log(`Reconnection failed: ${error.message}`, 'error');
              this._attemptReconnect();
            });
        } else {
          this.connect()
            .then(() => this.emit('reconnected'))
            .catch(error => {
              this._log(`Reconnection failed: ${error.message}`, 'error');
              this._attemptReconnect();
            });
        }
      }
    }, delay);
  }
  
  /**
   * Try to find alternative ports if the original port is unavailable
   * This handles the port conflict scenario described in the memory
   * @private
   * @returns {Promise<string>} New URL if an alternative port is found
   */
  async _tryAlternativePorts() {
    const currentUrl = new URL(this.url);
    const currentPort = parseInt(currentUrl.port, 10);
    
    // Try a range of ports around the current port
    const portsToTry = [
      8766, // Windsurf MCP default port
      8767, // Our default port
      8770, // Common alternative
      8765  // Original port
    ];
    
    // Add a range of ports to try
    for (let i = 1; i <= 5; i++) {
      portsToTry.push(currentPort + i);
    }
    
    // Filter out the current port and remove duplicates
    const uniquePorts = [...new Set(portsToTry)].filter(port => port !== currentPort);
    
    this._log(`Trying alternative ports: ${uniquePorts.join(', ')}`, 'debug');
    
    // Try each port
    for (const port of uniquePorts) {
      const testUrl = new URL(currentUrl);
      testUrl.port = port.toString();
      
      try {
        // Create a temporary WebSocket to test the port
        const testWs = new WebSocket(testUrl);
        
        // Wait for the connection to open or fail
        const result = await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            testWs.close();
            resolve(false);
          }, 1000);
          
          testWs.onopen = () => {
            clearTimeout(timeout);
            testWs.close();
            resolve(true);
          };
          
          testWs.onerror = () => {
            clearTimeout(timeout);
            testWs.close();
            resolve(false);
          };
        });
        
        if (result) {
          this._log(`Found available MCP server at port ${port}`, 'success');
          return testUrl.toString();
        }
      } catch (error) {
        // Ignore errors and try the next port
      }
    }
    
    // If no alternative port is found, return the original URL
    return this.url;
  }
  
  /**
   * Log a message with the appropriate level
   * @param {string} message - Message to log
   * @param {string} level - Log level (debug, info, warn, error, success)
   * @param {Object} data - Additional data to log in debug mode
   * @private
   */
  _log(message, level = 'info', data = null) {
    // Skip debug messages unless debug mode is enabled
    if (level === 'debug' && !this.debug) {
      return;
    }
    
    const prefix = '[MCP Client]';
    let formattedMessage;
    
    switch (level) {
      case 'debug':
        formattedMessage = chalk.dim(`${prefix} ${message}`);
        break;
      case 'info':
        formattedMessage = chalk.blue(`${prefix} ${message}`);
        break;
      case 'warn':
        formattedMessage = chalk.yellow(`${prefix} ${message}`);
        break;
      case 'error':
        formattedMessage = chalk.red(`${prefix} ${message}`);
        break;
      case 'success':
        formattedMessage = chalk.green(`${prefix} ${message}`);
        break;
      default:
        formattedMessage = `${prefix} ${message}`;
    }
    
    console.log(formattedMessage);
    
    if (data && this.debug) {
      console.log(chalk.dim(JSON.stringify(data, null, 2)));
    }
  }
}

/**
 * Create a new MCP client with the specified options
 * @param {Object} options - Client options
 * @returns {MCPClient} New MCP client instance
 */
export function createMCPClient(options = {}) {
  return new MCPClient(options);
}

export default MCPClient;
