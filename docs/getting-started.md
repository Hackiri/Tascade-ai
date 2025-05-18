# Getting Started with Tascade AI

This guide will help you get started with Tascade AI, an AI-powered task management system for project planning and execution.

## Installation

You can use Tascade AI without installing it by using `npx`:

```bash
# Start the Tascade AI MCP server
npx tascade-ai mcp

# Manage tasks
npx tascade-ai tasks --list
```

If you prefer to install Tascade AI globally:

```bash
npm install -g tascade-ai
```

Then you can use it directly:

```bash
tascade-ai --help
```

## Basic Usage

### Viewing Help

To see all available commands:

```bash
tascade-ai --help
```

For help with a specific command:

```bash
tascade-ai <command> --help
```

### Task Management

List all tasks:

```bash
tascade-ai tasks --list
```

Add a new task (interactive):

```bash
tascade-ai tasks --add
```

### Task Complexity

Analyze task complexity:

```bash
tascade-ai complexity --analyze <task-id>
```

Suggest how to split a complex task:

```bash
tascade-ai complexity --suggest-splitting <task-id> --interactive
```

### Task Execution and Verification

Execute a task with dependency checking:

```bash
tascade-ai execute --task <task-id> --interactive
```

Verify a task with scoring system:

```bash
tascade-ai verify --task <task-id> --interactive
```

## Next Steps

- Learn about [Task Management](./task-management.md)
- Explore [Complexity Assessment](./complexity-assessment.md)
- Understand [Task Verification](./task-verification.md)
- Set up [MCP Integration](./mcp-integration.md)
