# Tascade AI (Pre-release)

> **Last Updated:** May 21, 2025

> **Note:** Tascade AI is currently in pre-release. While functional, it may contain bugs or incomplete features. We welcome feedback and contributions!

Tascade AI is an advanced AI-powered task management system designed for project planning and execution. It combines the best features of leading task management tools to provide a comprehensive solution for AI-assisted development.

## Features

*   **Unified Task Management Core:** Robust system for defining, tracking, and managing development tasks.
*   **Project Context & Rules:** Define project-specific guidelines and coding standards to steer AI.
*   **PRD Parsing & Initial Task Generation:** Process requirement documents to auto-generate initial tasks.
*   **AI-Powered Task Decomposition & Planning:** Advanced AI for breaking down complex tasks into detailed sub-tasks.
*   **Task Recommendation System:** Intelligent, personalized task recommendations based on user preferences, project priorities, and historical data.
*   **Flexible LLM Integration:** Support for multiple Large Language Models.
*   **Interactive Feedback & Refinement Loop:** Mechanisms for users to review and refine AI-generated plans.
*   **Comprehensive Task Lifecycle Management:** Status tracking, dependency mapping, and outcome verification.
*   **Persistent Task Memory & History:** Historical record of tasks, decisions, and outcomes.
*   **Native Windsurf IDE Experience:** Custom UI, context-aware commands, and intelligent suggestions.
*   **Command-Line Interface (CLI):** Supplementary CLI for operations outside the Windsurf IDE.
*   **Extensible and Modular Architecture:** Designed for future enhancements.

## Pre-release Information

Tascade AI v0.1.0 is currently available as a pre-release. This means:

- Core functionality is implemented and working
- Some features may be incomplete or subject to change
- We're actively seeking feedback to improve the package
- Breaking changes may occur before the stable release

### Testing the Pre-release

We've created comprehensive testing resources to help you evaluate Tascade AI:

- [TESTING.md](./TESTING.md): Detailed testing scenarios and instructions
- [scripts/test_all_features.py](./scripts/test_all_features.py): Automated test script for all major features
- [scripts/test_windsurf_integration.py](./scripts/test_windsurf_integration.py): Test script for Windsurf integration

To run the automated tests:

```bash
# Install Tascade AI
npm install -g tascade-ai

# Run the feature tests
python scripts/test_all_features.py

# Test Windsurf integration (requires Windsurf)
python scripts/test_windsurf_integration.py --port 8766
```

### Reporting Issues

If you encounter any bugs or have suggestions for improvements, please:

1. Check the [GitHub Issues](https://github.com/Hackiri/tascade-aI/issues) to see if it's already reported
2. Submit a new issue with details about:
   - What you were trying to do
   - What happened
   - What you expected to happen
   - Steps to reproduce the issue
   - Test results from our testing scripts (if applicable)

## Getting Started

You can use Tascade AI either via npm (recommended for most users) or by cloning the repository (recommended for developers).

### Option 1: Using npm (Recommended for Users)

Tascade AI is available as an npm package, which means you can use it without installing anything using `npx`:

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

If you prefer to install Tascade AI globally:

```bash
npm install -g tascade-ai

# Then use it directly
tascade-ai --help
```

### Option 2: Using nix-shell (Recommended for Development Environments)

If you have Nix package manager installed, you can use the provided `shell.nix` file to set up a consistent development environment:

```bash
# Start a nix-shell with all dependencies
nix-shell shell.nix

# Run the MCP server within the nix-shell
node bin/tascade-cli.js mcp
```

This method ensures all dependencies are correctly installed and managed by the Nix package manager.

### Option 3: From Source (Alternative for Developers)

#### Prerequisites

*   Python 3.8 or higher.
*   `pip` (Python package installer).
*   `git` (for cloning the repository).

#### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Hackiri/tascade-aI.git
    cd tascade-ai
    ```

2.  **Create and activate a virtual environment (recommended):**
    On macOS and Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    On Windows:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    The project's dependencies are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Tascade AI:**
    To make the `tascade-ai` CLI command available, install the project package itself. Installing in editable mode (`-e`) is useful for development, as changes to the source code will be immediately effective.
    ```bash
    pip install -e .
    ```

5.  **Verify installation:**
    You should now be able to run the CLI:
    ```bash
    tascade-ai --help
    ```

### Data Storage

Tascade AI stores its data (tasks, rules, etc.) in a JSON file located by default at:
`~/.tascade-ai/tasks.json`

This directory and file will be created automatically on the first run if they don't exist.

## Usage

### Command-Line Interface (CLI)

Tascade AI includes a powerful command-line interface for managing tasks and interacting with the system. The CLI features a modern design inspired by the claude-task-master project:

```bash
# Install globally
npm install -g tascade-ai

# View all available commands
tascade-ai help
```

### Task Management

```bash
# List all tasks
tascade-ai tasks --list

# Add a new task
tascade-ai tasks --add

# View a specific task
tascade-ai tasks --id <id>

# Update a task
tascade-ai tasks --update <id>

# Generate tasks from a PRD file
tascade-ai generate -i <input-file> -o <output-file>

# Decompose a task into subtasks
tascade-ai decompose --id <task-id>
```

### Time Tracking

```bash
# Start tracking time for a task
tascade-ai track --start <taskId>

# Stop tracking time
tascade-ai track --stop <sessionId>

# List all time entries
tascade-ai track --list
```

### Server Management

```bash
# Start the MCP server
tascade-ai mcp

# Check MCP server status
tascade-ai mcp-status
# Start the Tascade AI server
tascade-ai start

# Start the MCP server
tascade-ai mcp

# Check MCP server status
tascade-ai mcp-status
```

### CLI Features

- Colorful gradient text for headers and banners
- Boxed UI elements for important information
- Progress bars for task status visualization
- Animated spinners for loading indicators
- Formatted tables for data presentation
- Color-coded status indicators
- Improved error handling
- Interactive prompts for missing information
- Comprehensive help documentation

### Documentation

For detailed documentation on the CLI, see:
- [Command Reference](./docs/command-reference.md) - Complete list of all available commands
- [Tutorial](./docs/tutorial.md) - Step-by-step guide to getting started
- [Enhanced CLI Documentation](./docs/enhanced_cli.md) - Detailed information on UI features

**Basic Task Management (Examples):**

*   **Generating tasks from a PRD using AI:**
    ```bash
    tascade-ai generate --input ./examples/sample_prd.md --output ./tasks.json --num-tasks 15
    ```
    
    This command uses AI to analyze a Product Requirements Document (PRD) and automatically generate tasks based on its content. You can specify the number of tasks to generate and choose between different AI providers (Anthropic Claude or OpenAI).
*   **Listing tasks:**
    ```bash
    tascade-ai list
    tascade-ai list --status pending --priority high
    ```

**Managing Project Rules (Examples):**

*   **Adding a new rule:**
    ```bash
    tascade-ai rules add -n "Python Style Guide" -d "PEP 8 adherence" -c "All Python code must follow PEP 8." -t "python,lint"
    ```
*   **Listing rules:**
    ```bash
    tascade-ai rules list --show-content
    ```
*   **Activating/Deactivating a rule:**
    ```bash
    tascade-ai rules activate <RULE_ID>
    tascade-ai rules deactivate <RULE_ID>
    ```

**AI-Powered Task Decomposition (CLI):**

This feature allows you to use AI to break down an existing task into smaller, actionable subtasks. The CLI command simulates the interaction with the AI backend (`taskmaster-ai` MCP server).

*   **Decomposing a task:**
    ```bash
    tascade-ai tasks decompose <PARENT_TASK_ID>
    ```
    For example, if you have a task with ID `task_123`:
    ```bash
    tascade-ai tasks decompose task_123
    ```
*   **Providing custom instructions to the AI:**
    ```bash
    tascade-ai tasks decompose <PARENT_TASK_ID> --instructions "Focus on backend development steps first. Ensure subtasks are testable."
    ```
*   **Specifying the project root (important for AI context):**
    The `--project-root` option tells the AI tools where your project is located. If not provided, it defaults to the current directory.
    ```bash
    tascade tasks decompose <PARENT_TASK_ID> --project-root /path/to/your/project
    ```

**How AI Decomposition Works (CLI Simulation):**

1.  The command identifies the parent task and any active project rules.
2.  It prepares the necessary information for the AI (simulating calls to the `taskmaster-ai` MCP server).
3.  The AI (simulated in the CLI) suggests a list of subtasks.
4.  You will be shown these suggested subtasks and asked for confirmation:
    ```
    Suggested Subtasks for Review:
      1. Title: Simulated Subtask 1: Design Database Model
         Description: Define tables, columns, and relationships for the new feature.
      2. Title: Simulated Subtask 2: Implement API Endpoints
         Description: Create CRUD endpoints for the new resource.
      ...
    
    Do you want to add these subtasks? [Y/n]: 
    ```
5.  If you confirm (e.g., by typing 'Y' and pressing Enter), the subtasks will be added to the parent task and saved.

(More usage examples to be added)

## Task Recommendation System

Tascade AI includes a powerful Task Recommendation System that provides intelligent, personalized task recommendations based on user preferences, project priorities, and historical data.

### Key Features

* **Personalized Recommendations:** Tailors task suggestions based on user preferences and past performance
* **Historical Performance Analysis:** Learns from past task completions to improve recommendations
* **Workload Balancing:** Prevents user overload by distributing tasks optimally
* **Time Prediction:** Predicts task completion times based on historical data
* **Recommendation Explanation:** Provides clear explanations for why tasks are recommended

### Basic Usage

```python
from src.core.task_recommendation import TaskRecommendationSystem

# Initialize the recommendation system
recommendation_system = TaskRecommendationSystem(
    task_manager=task_manager,
    time_tracking_system=time_tracking_system
)

# Get recommendations for a user
recommendations = recommendation_system.recommend_tasks(
    user_id="user123",
    limit=5
)

# Print recommended tasks
for rec in recommendations["recommendations"]:
    print(f"Task: {rec['task']['title']}")
    print(f"Score: {rec['score']}")
```

For more detailed information, see the [Task Recommendation System documentation](docs/task_recommendation_system.md).

## MCP Server Integration

Tascade AI includes a Model Context Protocol (MCP) server that allows integration with IDEs and other development tools. The MCP server provides a WebSocket interface for interacting with Tascade AI's task management and time tracking features.

### Key Features

* **WebSocket API:** Connect to Tascade AI from any IDE or tool that supports WebSockets
* **Task Management:** Create, update, and manage tasks through the MCP server
* **Time Tracking:** Track time spent on tasks and generate reports
* **Visualization:** Generate visualizations and dashboards for time tracking data
* **IDE Integration:** Seamlessly integrate with your favorite IDE

### Basic Usage

1. **Start the MCP Server:**

```bash
# Using the wrapper script
./scripts/mcp_server_wrapper.sh

# Or directly with Nix
nix-shell mcp-shell.nix --run "python src/mcp/simple_server.py"
```

2. **Connect to the MCP Server:**

Connect to the WebSocket server at `ws://localhost:8766` and send commands in JSON format:

```json
{
  "command": "get-server-info",
  "params": {},
  "id": "1"
}
```

3. **Integrate with Windsurf:**

Add the Tascade AI MCP server to your Windsurf configuration:

```json
"tascade-ai": {
  "command": "/path/to/tascade-ai/scripts/mcp_server_wrapper.sh",
  "args": [],
  "disabled": false,
  "autoApprove": [
    "get-server-info",
    "get-tasks",
    "add-task",
    "update-task"
  ]
}
```

For more detailed information, see the [MCP Integration Guide](docs/mcp_integration.md).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
