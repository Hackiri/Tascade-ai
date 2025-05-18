#!/usr/bin/env node

/**
 * Node.js MCP Server for Tascade AI
 * 
 * This script implements a WebSocket server that handles MCP commands for Tascade AI.
 */

import WebSocket, { WebSocketServer } from 'ws';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectDir = path.join(__dirname, '..');

// Parse command line arguments
const args = process.argv.slice(2);
let port = 8765;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--port' || args[i] === '-p') {
    port = parseInt(args[i + 1], 10);
    i++;
  }
}

// Create a WebSocket server
const wss = new WebSocketServer({ port });

console.log(`Tascade AI MCP Server running at ws://localhost:${port}`);

// Handle connections
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  // Send welcome message
  ws.send(JSON.stringify({
    message: 'Welcome to Tascade AI MCP Server',
    timestamp: new Date().toISOString()
  }));
  
  // Handle messages
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      if (!data.command) {
        ws.send(JSON.stringify({ error: 'Missing command' }));
        return;
      }
      
      console.log(`Received command: ${data.command}`);
      
      // Handle commands
      switch (data.command) {
        case 'generate-tasks':
          await handleGenerateTasks(ws, data.params || {});
          break;
        default:
          ws.send(JSON.stringify({ 
            error: `Unknown command: ${data.command}`,
            command: data.command,
            timestamp: new Date().toISOString()
          }));
      }
    } catch (error) {
      console.error('Error handling message:', error);
      ws.send(JSON.stringify({ 
        error: `Error handling message: ${error.message}`,
        timestamp: new Date().toISOString()
      }));
    }
  });
  
  // Handle disconnections
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

/**
 * Handle the generate-tasks command
 * 
 * @param {WebSocket} ws - WebSocket connection
 * @param {Object} params - Command parameters
 */
async function handleGenerateTasks(ws, params) {
  // Validate parameters
  if (!params.input_file) {
    ws.send(JSON.stringify({ 
      error: 'Missing required parameter: input_file',
      command: 'generate-tasks',
      timestamp: new Date().toISOString()
    }));
    return;
  }
  
  if (!params.output_file) {
    ws.send(JSON.stringify({ 
      error: 'Missing required parameter: output_file',
      command: 'generate-tasks',
      timestamp: new Date().toISOString()
    }));
    return;
  }
  
  // Build the command
  const cmd = [
    path.join(projectDir, 'bin', 'tascade-ai.js'),
    'generate',
    '--input', params.input_file,
    '--output', params.output_file
  ];
  
  // Add optional parameters
  if (params.num_tasks) {
    cmd.push('--num-tasks', params.num_tasks.toString());
  }
  
  if (params.provider) {
    cmd.push('--provider', params.provider);
  }
  
  if (params.priority) {
    cmd.push('--priority', params.priority);
  }
  
  if (params.force) {
    cmd.push('--force');
  }
  
  console.log(`Running command: node ${cmd.join(' ')}`);
  
  try {
    // Run the command
    const child = spawn('node', cmd, { 
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { 
        ...process.env,
        // Explicitly pass API keys and configuration
        PERPLEXITY_API_KEY: process.env.PERPLEXITY_API_KEY,
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
        MODEL: process.env.MODEL,
        PERPLEXITY_MODEL: process.env.PERPLEXITY_MODEL,
        MAX_TOKENS: process.env.MAX_TOKENS,
        TEMPERATURE: process.env.TEMPERATURE,
        DEFAULT_SUBTASKS: process.env.DEFAULT_SUBTASKS,
        DEFAULT_PRIORITY: process.env.DEFAULT_PRIORITY
      }
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
      if (code !== 0) {
        ws.send(JSON.stringify({ 
          error: `Command failed with code ${code}: ${stderr}`,
          command: 'generate-tasks',
          timestamp: new Date().toISOString()
        }));
        return;
      }
      
      // Read the output file
      try {
        const tasks = JSON.parse(fs.readFileSync(params.output_file, 'utf-8'));
        
        ws.send(JSON.stringify({
          success: true,
          command: 'generate-tasks',
          tasks: tasks.tasks,
          metadata: tasks.metadata || {},
          message: 'Tasks generated successfully',
          timestamp: new Date().toISOString()
        }));
      } catch (error) {
        ws.send(JSON.stringify({ 
          error: `Failed to read generated tasks: ${error.message}`,
          command: 'generate-tasks',
          timestamp: new Date().toISOString()
        }));
      }
    });
  } catch (error) {
    ws.send(JSON.stringify({ 
      error: `Failed to run command: ${error.message}`,
      command: 'generate-tasks',
      timestamp: new Date().toISOString()
    }));
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\nStopping Tascade AI MCP Server...');
  wss.close();
  process.exit(0);
});
