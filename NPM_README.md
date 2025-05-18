# Tascade AI

Tascade AI is an advanced AI-powered task management system designed for project planning and execution. It combines the best features of leading task management tools to provide a comprehensive solution for AI-assisted development.

## Quick Start with npx

You can use Tascade AI without installing it by using `npx`:

```bash
# Start the Tascade AI MCP server
npx tascade-ai mcp

# Manage tasks
npx tascade-ai tasks --list
npx tascade-ai tasks --add

# Track time
npx tascade-ai track --start <task-id>
npx tascade-ai track --stop <session-id>
npx tascade-ai track --list
```

## Installation

If you prefer to install Tascade AI globally:

```bash
npm install -g tascade-ai
```

Then you can use it directly:

```bash
tascade-ai --help
```

## Features

- **Unified Task Management Core:** Robust system for defining, tracking, and managing development tasks.
- **AI-Powered Task Decomposition & Planning:** Advanced AI for breaking down complex tasks into detailed sub-tasks.
- **Task Complexity Assessment:** Sophisticated analysis of task complexity with visual indicators and recommendations.
- **Intelligent Task Splitting:** Automatic generation of subtasks based on complexity analysis.
- **Verification Criteria Generation:** Creation of task-specific verification criteria based on complexity.
- **Time Tracking:** Track time spent on tasks and generate reports.
- **MCP Server Integration:** Connect to Tascade AI from any IDE or tool that supports WebSockets.
- **Visualization:** Generate visualizations and dashboards for task complexity and progress.

## MCP Server Integration

Tascade AI includes a Model Context Protocol (MCP) server that allows integration with IDEs and other development tools:

```bash
# Start the MCP server
npx tascade-ai mcp --port 8765
```

Connect to the WebSocket server at `ws://localhost:8765` and send commands in JSON format:

```json
{
  "command": "get-server-info",
  "params": {},
  "id": "1"
}
```

## Commands

### Task Management

```bash
# List all tasks
npx tascade-ai tasks --list

# List tasks with a specific status
npx tascade-ai tasks --list --status pending

# Add a new task (interactive)
npx tascade-ai tasks --add
```

### Task Complexity Workflow

```bash
# Analyze task complexity
npx tascade-ai complexity --analyze <task-id>

# Suggest how to split a complex task
npx tascade-ai complexity --suggest-splitting <task-id> --interactive

# Generate verification criteria based on complexity
npx tascade-ai complexity --verify <task-id>

# Show project complexity metrics
npx tascade-ai complexity --metrics --detailed
```

### Task Execution and Verification

```bash
# Execute a task with dependency checking
npx tascade-ai execute --task <task-id> --interactive

# Verify a task with scoring system
npx tascade-ai verify --task <task-id> --interactive
```

### Time Tracking

```bash
# Start tracking time for a task
npx tascade-ai track --start <task-id>

# Stop tracking time
npx tascade-ai track --stop <session-id>

# List time entries
npx tascade-ai track --list
```

### MCP Server

```bash
# Start the MCP server
npx tascade-ai mcp --port 8765
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
