#!/bin/bash
# Test script for task execution tracking features in Tascade AI

echo "=== Tascade AI Task Execution Tracking Test ==="
echo "This script demonstrates the new task execution tracking features"
echo

# Create a test task
echo "Creating a test task..."
python -m src.cli.main tasks add "Test Task" --description "A task to test execution tracking" --priority high

# List tasks to get the ID
echo
echo "Listing tasks to get the ID..."
python -m src.cli.main list
echo

# Prompt for task ID
read -p "Enter the task ID from the list above: " TASK_ID
echo

# Start the task
echo "Starting task $TASK_ID..."
python -m src.cli.main tasks start $TASK_ID
echo

# Pause the task
echo "Pausing task $TASK_ID..."
python -m src.cli.main tasks pause $TASK_ID --reason "Taking a break"
echo

# Block the task
echo "Blocking task $TASK_ID..."
python -m src.cli.main tasks block $TASK_ID --reason "Waiting for dependency"
echo

# Unblock the task
echo "Unblocking task $TASK_ID..."
python -m src.cli.main tasks unblock $TASK_ID --resolution "Dependency resolved"
echo

# Complete the task
echo "Completing task $TASK_ID..."
python -m src.cli.main tasks complete $TASK_ID --notes "Task completed successfully"
echo

# Analyze the task
echo "Analyzing task $TASK_ID..."
python -m src.cli.main tasks analyze $TASK_ID
echo

echo "=== Test completed ==="
