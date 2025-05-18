# API Reference

This document provides a reference for programmatically using Tascade AI in your Node.js applications.

## Installation

```bash
npm install tascade-ai
```

## Basic Usage

```javascript
const tascade = require('tascade-ai');

// Initialize Tascade AI
const client = new tascade.Client({
  configPath: './tascade-config.json'
});

// Use Tascade AI features
async function main() {
  const tasks = await client.tasks.list();
  console.log(tasks);
}

main().catch(console.error);
```

## Task Management API

### List Tasks

```javascript
// List all tasks
const tasks = await client.tasks.list();

// List tasks with a specific status
const pendingTasks = await client.tasks.list({ status: 'pending' });

// List tasks with detailed information
const detailedTasks = await client.tasks.list({ detailed: true });
```

### Add Tasks

```javascript
// Add a new task
const newTask = await client.tasks.add({
  title: 'Implement user authentication',
  description: 'Add user login and registration functionality',
  status: 'pending',
  priority: 'high'
});
```

### Update Tasks

```javascript
// Update a task
const updatedTask = await client.tasks.update('task-123', {
  status: 'in-progress',
  priority: 'medium'
});

// Add a dependency
await client.tasks.addDependency('task-123', 'task-456');

// Remove a dependency
await client.tasks.removeDependency('task-123', 'task-456');
```

### Delete Tasks

```javascript
// Delete a task
await client.tasks.delete('task-123');
```

## Complexity Assessment API

### Analyze Task Complexity

```javascript
// Analyze task complexity
const complexity = await client.complexity.analyze('task-123');
console.log(`Complexity Score: ${complexity.score}/100`);
console.log(`Complexity Level: ${complexity.level}`);
```

### Suggest Task Splitting

```javascript
// Suggest how to split a complex task
const splitting = await client.complexity.suggestSplitting('task-123', {
  maxSubtasks: 5
});

// Create the suggested subtasks
for (const subtask of splitting.subtasks) {
  await client.tasks.add(subtask);
}
```

### Generate Verification Criteria

```javascript
// Generate verification criteria
const criteria = await client.complexity.generateVerificationCriteria('task-123');

// Display criteria by category
for (const category in criteria.byCategory) {
  console.log(`${category} Criteria:`);
  for (const criterion of criteria.byCategory[category]) {
    console.log(`- ${criterion.required ? '[REQUIRED]' : '[OPTIONAL]'} ${criterion.description}`);
  }
}
```

## Task Execution API

```javascript
// Execute a task
const execution = await client.execution.executeTask('task-123');

// Check if dependencies are satisfied
if (execution.dependenciesSatisfied) {
  console.log('All dependencies are satisfied');
} else {
  console.log('Missing dependencies:', execution.missingDependencies);
}

// Get related files
console.log('Related files:', execution.relatedFiles);
```

## Task Verification API

```javascript
// Verify a task
const verification = await client.verification.verifyTask('task-123');

// Check verification score
console.log(`Verification Score: ${verification.score}/100`);
console.log(`Pass: ${verification.pass ? 'Yes' : 'No'}`);

// Get verification results by criterion
for (const result of verification.results) {
  console.log(`${result.satisfied ? '✓' : '✗'} ${result.criterion.description}`);
}
```

## Time Tracking API

```javascript
// Start tracking time
const session = await client.timeTracking.start('task-123');
console.log(`Session ID: ${session.id}`);

// Stop tracking time
const entry = await client.timeTracking.stop(session.id);
console.log(`Time spent: ${entry.duration} minutes`);

// List time entries
const entries = await client.timeTracking.list();

// Generate time report
const report = await client.timeTracking.generateReport();
console.log(`Total time: ${report.totalTime} hours`);
```

## MCP Client API

```javascript
// Connect to MCP server
const mcpClient = new tascade.MCPClient({
  host: 'localhost',
  port: 8765
});

// Send a command
const response = await mcpClient.sendCommand('get-server-info', {});
console.log('Server info:', response);

// Listen for events
mcpClient.on('task-updated', (task) => {
  console.log('Task updated:', task);
});
```

## Error Handling

```javascript
try {
  const task = await client.tasks.get('non-existent-task');
} catch (error) {
  if (error.code === 'TASK_NOT_FOUND') {
    console.error('Task not found');
  } else {
    console.error('An error occurred:', error.message);
  }
}
```
