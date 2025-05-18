# Task Management

Tascade AI provides a comprehensive task management system that helps you organize, track, and execute your development tasks efficiently.

## Basic Task Operations

### List Tasks

```bash
# List all tasks
tascade-ai tasks --list

# List tasks with a specific status
tascade-ai tasks --list --status pending

# List tasks with detailed information
tascade-ai tasks --list --detailed
```

### Add Tasks

```bash
# Add a new task (interactive)
tascade-ai tasks --add

# Add a task with specific details
tascade-ai tasks --add --title "Implement user authentication" --description "Add user login and registration functionality"
```

### Update Tasks

```bash
# Update a task
tascade-ai tasks --update <task-id>

# Change task status
tascade-ai tasks --update <task-id> --status completed
```

### Delete Tasks

```bash
# Delete a task
tascade-ai tasks --delete <task-id>
```

## Task Execution

Tascade AI includes a task execution workflow that checks dependencies and provides guidance:

```bash
# Execute a task
tascade-ai execute --task <task-id> --interactive
```

The execution workflow:
1. Checks if all dependencies are completed
2. Assesses task complexity
3. Loads related files
4. Provides an interactive confirmation process
5. Marks the task as in-progress

## Task Splitting

For complex tasks, Tascade AI can suggest how to split them into manageable subtasks:

```bash
# Suggest task splitting
tascade-ai complexity --suggest-splitting <task-id> --interactive
```

The splitting process:
1. Analyzes task content and complexity
2. Identifies logical components
3. Groups related files
4. Generates appropriate subtasks
5. Estimates hours for each subtask

## Task Dependencies

Manage task dependencies to ensure proper execution order:

```bash
# Add a dependency
tascade-ai tasks --update <task-id> --add-dependency <dependency-id>

# Remove a dependency
tascade-ai tasks --update <task-id> --remove-dependency <dependency-id>

# List task dependencies
tascade-ai tasks --view <task-id> --show-dependencies
```

## Time Tracking

Track time spent on tasks:

```bash
# Start tracking time
tascade-ai track --start <task-id>

# Stop tracking time
tascade-ai track --stop <session-id>

# List time entries
tascade-ai track --list

# Generate time report
tascade-ai track --report
```

## Integration with Complexity and Verification

Task management is integrated with:
- **Complexity Assessment**: Helps prioritize and plan tasks
- **Task Verification**: Ensures tasks are completed correctly
- **MCP Server**: Allows integration with other tools and IDEs
