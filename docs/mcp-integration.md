# MCP Integration

Tascade AI includes a Model Context Protocol (MCP) server that allows integration with IDEs and other development tools.

## Overview

The MCP server:
- Provides a WebSocket interface for real-time communication
- Allows external tools to interact with Tascade AI
- Supports task management, complexity assessment, and verification
- Can be extended with custom handlers

## Starting the MCP Server

```bash
# Start the MCP server on the default port (8765)
tascade-ai mcp

# Start the MCP server on a specific port
tascade-ai mcp --port 8766

# Check the status of the MCP server
tascade-ai mcp-status
```

## Port Conflict Handling

Tascade AI automatically handles port conflicts:
- If the default port (8765) is in use, it will try alternative ports
- The server will notify you of the port it's using
- You can specify a port with the `--port` option

## Connecting to the MCP Server

Connect to the WebSocket server at `ws://localhost:8765` (or your specified port) and send commands in JSON format:

```json
{
  "command": "get-server-info",
  "params": {},
  "id": "1"
}
```

## Available Commands

### Server Information

```json
{
  "command": "get-server-info",
  "params": {},
  "id": "1"
}
```

### Task Management

```json
{
  "command": "list-tasks",
  "params": {
    "status": "pending"
  },
  "id": "2"
}
```

```json
{
  "command": "add-task",
  "params": {
    "title": "Implement user authentication",
    "description": "Add user login and registration functionality"
  },
  "id": "3"
}
```

### Complexity Assessment

```json
{
  "command": "analyze-complexity",
  "params": {
    "taskId": "task-123"
  },
  "id": "4"
}
```

### Task Verification

```json
{
  "command": "generate-verification-criteria",
  "params": {
    "taskId": "task-123"
  },
  "id": "5"
}
```

## Example Client Implementation

Here's a simple JavaScript client example:

```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', function open() {
  const message = {
    command: 'get-server-info',
    params: {},
    id: '1'
  };
  ws.send(JSON.stringify(message));
});

ws.on('message', function incoming(data) {
  const response = JSON.parse(data);
  console.log('Received:', response);
});
```

## Extending the MCP Server

You can extend the MCP server with custom handlers:

1. Create a handler file in `src/mcp/handlers/`
2. Implement the handler function
3. Register the handler in the MCP server

Example handler:

```javascript
// src/mcp/handlers/custom_handler.js
export default async function handleCustomCommand(params, context) {
  // Implementation
  return {
    result: 'success',
    data: { /* your data */ }
  };
}
```
