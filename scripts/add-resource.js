#!/usr/bin/env node

/**
 * Script to add a resource to the Tascade AI MCP server
 */

import WebSocket from 'ws';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs';
import path from 'path';

// Configuration
const MCP_SERVER_URL = 'ws://localhost:8766';

// Sample resource to add
const sampleResource = {
  uri: 'sample/prd',
  content: fs.readFileSync(path.join(process.cwd(), 'sample_prd.md'), 'utf-8'),
  metadata: {
    type: 'markdown',
    title: 'Sample PRD',
    description: 'A sample Product Requirements Document'
  }
};

// Connect to the MCP server
console.log(`Connecting to MCP server at ${MCP_SERVER_URL}...`);
const ws = new WebSocket(MCP_SERVER_URL);

ws.on('open', () => {
  console.log('Connected to MCP server');
  
  // Add the resource
  console.log(`Adding resource: ${sampleResource.uri}`);
  
  const message = {
    command: 'add-resource',
    params: sampleResource,
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
    if (response.id) {
      ws.close();
    }
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
