# Command Reference

This document provides a comprehensive reference for all Tascade AI CLI commands.

## Global Options

These options can be used with any command:

```
-V, --version         Output the version number
-d, --debug           Enable debug mode
-s, --silent          Suppress all output except errors
-c, --config <path>   Path to configuration file
-h, --help            Display help for command
```

## Main Commands

### start

Start the Tascade AI server.

```bash
tascade-ai start [options]
```

Options:
- `--port <port>` - Port to run the server on (default: 3000)
- `--host <host>` - Host to bind to (default: localhost)

### tasks

Manage tasks.

```bash
tascade-ai tasks [options]
```

Options:
- `--list` - List all tasks
- `--add` - Add a new task
- `--update <id>` - Update a task
- `--delete <id>` - Delete a task
- `--view <id>` - View task details
- `--status <status>` - Filter tasks by status
- `--detailed` - Show detailed information
- `--format <format>` - Output format (json, table)

### complexity

Task complexity workflow.

```bash
tascade-ai complexity [options]
```

Options:
- `-a, --analyze <id>` - Analyze complexity of a task
- `-s, --suggest-splitting <id>` - Suggest how to split a complex task
- `-v, --verify <id>` - Generate verification criteria based on complexity
- `-m, --metrics` - Show project complexity metrics
- `-d, --detailed` - Show detailed information
- `-i, --interactive` - Run in interactive mode
- `-n, --max-subtasks <number>` - Maximum number of subtasks to create (default: 5)

### execute

Execute a task with dependency checking and complexity assessment.

```bash
tascade-ai execute [options]
```

Options:
- `-t, --task <id>` - ID of the task to execute
- `-i, --interactive` - Run in interactive mode

### verify

Verify a task with scoring system.

```bash
tascade-ai verify [options]
```

Options:
- `-t, --task <id>` - ID of the task to verify
- `-i, --interactive` - Run in interactive mode

### track

Track time for tasks.

```bash
tascade-ai track [options]
```

Options:
- `--start <id>` - Start tracking time for a task
- `--stop <session-id>` - Stop tracking time
- `--list` - List time entries
- `--report` - Generate time report
- `--format <format>` - Output format (json, table)

### generate

Generate tasks from a PRD file using AI.

```bash
tascade-ai generate [options]
```

Options:
- `-f, --file <path>` - Path to PRD file
- `-o, --output <path>` - Output file path
- `-i, --interactive` - Run in interactive mode

### mcp

Start the MCP server.

```bash
tascade-ai mcp [options]
```

Options:
- `-p, --port <port>` - Port to run the server on (default: 8765)
- `-h, --host <host>` - Host to bind to (default: localhost)

### mcp-status

Check the status of the MCP server.

```bash
tascade-ai mcp-status [options]
```

Options:
- `-p, --port <port>` - Port to check (default: 8765)

### decompose

Decompose a task into subtasks using AI.

```bash
tascade-ai decompose [options]
```

Options:
- `-t, --task <id>` - ID of the task to decompose
- `-m, --max-subtasks <number>` - Maximum number of subtasks to create (default: 5)
- `-i, --interactive` - Run in interactive mode

## Example Usage

```bash
# List all tasks
tascade-ai tasks --list

# Analyze task complexity
tascade-ai complexity --analyze task-123

# Execute a task
tascade-ai execute --task task-123 --interactive

# Start the MCP server on a specific port
tascade-ai mcp --port 8766
```
