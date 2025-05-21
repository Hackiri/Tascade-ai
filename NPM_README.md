# Tascade AI

> **Last Updated:** May 21, 2025

Tascade AI is an advanced AI-powered task management system designed for project planning and execution. It combines the best features of leading task management tools to provide a comprehensive solution for AI-assisted development.

## Quick Start with npx

You can use Tascade AI without installing it by using `npx`:

```bash
# Start the Tascade AI MCP server (runs on port 8766 by default)
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
# Start the MCP server (default port is 8766)
npx tascade-ai mcp

# Or specify a custom port
npx tascade-ai mcp --port 8765
```

Connect to the WebSocket server at the specified port (e.g., `ws://localhost:8766`) and send commands in JSON format:

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
# Start the MCP server with default settings
npx tascade-ai mcp

# Start with a custom port
npx tascade-ai mcp --port 8765

# Check MCP server status
npx tascade-ai mcp-status
```

## Environment Variables

Tascade AI supports configuration through environment variables. Create a `.env` file in your project root based on the example below:

```
# API Keys (Required for AI task generation)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# AI Model Configuration
MODEL=claude-3-7-sonnet-20250219
PERPLEXITY_MODEL=sonar-pro
MAX_TOKENS=64000
TEMPERATURE=0.2

# Task Generation Defaults
DEFAULT_SUBTASKS=5
DEFAULT_PRIORITY=medium

# MCP Server Configuration
MCP_PORT=8766

# Debug Mode (set to true for verbose logging)
DEBUG=false
```

## Development with nix-shell

For development environments with Nix package manager, you can use the provided `shell.nix` file:

```bash
# Start a nix-shell with all dependencies
nix-shell shell.nix

# Run the MCP server within the nix-shell
node bin/tascade-cli.js mcp
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
