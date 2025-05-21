#!/usr/bin/env node

/**
 * Simple MCP client script to interact with the Tascade AI MCP server
 */

import WebSocket from 'ws';
import { v4 as uuidv4 } from 'uuid';

// Configuration
const MCP_SERVER_URL = 'ws://localhost:8766';
const COMMANDS = process.argv.slice(2);

if (COMMANDS.length === 0) {
  console.log('Usage: node mcp-client.js <command> [params]');
  console.log('Available commands: list-tools, list-resources, get-resource');
  process.exit(1);
}

// Connect to the MCP server
console.log(`Connecting to MCP server at ${MCP_SERVER_URL}...`);
const ws = new WebSocket(MCP_SERVER_URL);

ws.on('open', () => {
  console.log('Connected to MCP server');
  
  // Execute the command
  const command = COMMANDS[0];
  const params = COMMANDS.slice(1);
  
  console.log(`Executing command: ${command}`);
  
  const message = {
    command,
    params: params.length > 0 ? parseParams(params) : {},
    id: uuidv4()
  };
  
  ws.send(JSON.stringify(message));
});

ws.on('message', (data) => {
  try {
    const response = JSON.parse(data.toString());
    console.log('Response:');
    console.log(JSON.stringify(response, null, 2));
    
    // Close the connection after receiving the response
    ws.close();
  } catch (error) {
    console.error('Error parsing response:', error);
    ws.close();
  }
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
  process.exit(1);
});

ws.on('close', () => {
  console.log('Disconnected from MCP server');
  process.exit(0);
});

/**
 * Parse command parameters
 * @param {string[]} params - Parameter strings in the format key=value
 * @returns {Object} - Parsed parameters
 */
function parseParams(params) {
  const result = {};
  
  for (const param of params) {
    const [key, value] = param.split('=');
    if (key && value) {
      result[key] = value;
    }
  }
  
  return result;
}
