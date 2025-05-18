# Tascade AI Pre-release Testing Guide

This guide provides comprehensive testing scenarios for the Tascade AI pre-release. By following these steps, you can help us identify issues and improve the package before the stable release.

## Prerequisites

- Node.js v16 or higher
- Python 3.8 or higher (for some Tascade AI features)
- Git (optional, for cloning the repository)

## Installation Testing

### 1. Global Installation

```bash
# Install Tascade AI globally
npm install -g tascade-ai

# Verify installation
tascade-ai --version
tascade-ai --help
```

### 2. Using with npx

```bash
# Run Tascade AI without installing
npx tascade-ai --help
```

## Feature Testing

### 1. Task Management

```bash
# Initialize Tascade AI in a project
mkdir tascade-test
cd tascade-test
npx tascade-ai init

# Add a task
npx tascade-ai tasks --add
# Follow the prompts to create a task

# List tasks
npx tascade-ai tasks --list

# Update a task
npx tascade-ai tasks --update <task-id> --status in-progress

# Delete a task
npx tascade-ai tasks --delete <task-id>
```

### 2. AI Task Generation from PRD

```bash
# Set your API key for the AI provider
export ANTHROPIC_API_KEY=your_api_key_here  # For Anthropic Claude
# OR
export OPENAI_API_KEY=your_api_key_here     # For OpenAI

# Generate tasks from a PRD file
npx tascade-ai generate --input ./examples/sample_prd.md --output ./tasks.json

# Generate tasks with specific options
npx tascade-ai generate --input ./examples/sample_prd.md --output ./tasks.json --num-tasks 15 --provider openai

# Run the test script directly
node ./examples/test_generate_tasks.js
```

### 3. Time Tracking

```bash
# Start tracking time for a task
npx tascade-ai track --start <task-id>
# Enter a description of what you're working on

# Stop tracking time
npx tascade-ai track --stop <session-id>

# List time entries
npx tascade-ai track --list
```

### 3. MCP Server Integration

```bash
# Start the MCP server on the default port
npx tascade-ai mcp

# Start the MCP server on a specific port
npx tascade-ai mcp --port 8766

# Test port conflict handling
# In a separate terminal, run another instance on the same port
# It should automatically find an available port
npx tascade-ai mcp --port 8766
```

### 4. Windsurf Integration

If you have Windsurf installed:

1. Ensure your Windsurf MCP configuration includes Tascade AI:
   ```json
   "tascade-ai": {
     "command": "npx tascade-ai mcp",
     "args": ["--port", "8766"],
     "disabled": false,
     "autoApprove": [
       "get-server-info",
       "get-tasks",
       "get-task",
       "add-task",
       "update-task",
       "delete-task",
       "get-time-entries",
       "add-time-entry",
       "start-tracking",
       "stop-tracking"
     ]
   }
   ```

2. Start Windsurf and verify that it can connect to the Tascade AI MCP server
3. Test task management and time tracking through Windsurf

## Edge Case Testing

### 1. Error Handling

```bash
# Test with invalid task ID
npx tascade-ai tasks --update nonexistent-task --status completed

# Test with invalid command
npx tascade-ai invalid-command

# Test with missing parameters
npx tascade-ai tasks --update
```

### 2. Concurrent Operations

```bash
# Start multiple time tracking sessions
npx tascade-ai track --start <task-id-1>
npx tascade-ai track --start <task-id-2>

# Stop tracking time for both sessions
npx tascade-ai track --stop <session-id-1>
npx tascade-ai track --stop <session-id-2>
```

### 3. Performance Testing

```bash
# Create multiple tasks (10+)
for i in {1..10}; do
  echo '{"title":"Test Task '$i'","description":"Test Description '$i'","priority":"medium"}' | npx tascade-ai tasks --add
done

# List all tasks and measure performance
time npx tascade-ai tasks --list
```

## Reporting Test Results

After testing, please report your findings:

1. What worked well?
2. What didn't work as expected?
3. Any suggestions for improvements?
4. Environment details (OS, Node.js version, etc.)

Submit your feedback as a GitHub issue at: https://github.com/Hackiri/tascade-aI/issues

## Automated Testing

For developers who have cloned the repository:

```bash
# Run the Windsurf integration test
cd /path/to/tascade-ai
python scripts/test_windsurf_integration.py --port 8766
```

Thank you for helping test Tascade AI! Your feedback is invaluable in making this tool better for everyone.
