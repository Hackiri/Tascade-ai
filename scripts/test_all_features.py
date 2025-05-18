#!/usr/bin/env python3
"""
Tascade AI Feature Test Script

This script tests all major features of Tascade AI to ensure they're working correctly.
It's designed to be run after installing the npm package.

Usage:
    python test_all_features.py [--port PORT]

Options:
    --port PORT    Port to use for the MCP server (default: 8766)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def run_command(command, check=True):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def print_header(title):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def print_test(name, description):
    """Print a test name and description."""
    print(f"{BOLD}{YELLOW}Testing: {name}{RESET}")
    print(f"  {description}")

def print_result(success, message=""):
    """Print a test result."""
    if success:
        print(f"{GREEN}✓ PASS{RESET} {message}")
    else:
        print(f"{RED}✗ FAIL{RESET} {message}")
    print()

def create_test_project():
    """Create a test project directory."""
    test_dir = f"tascade-test-{uuid.uuid4().hex[:8]}"
    os.makedirs(test_dir, exist_ok=True)
    os.chdir(test_dir)
    print(f"Created test directory: {os.getcwd()}")
    return test_dir

def cleanup_test_project(test_dir):
    """Clean up the test project directory."""
    os.chdir("..")
    # Uncomment to remove the test directory
    # import shutil
    # shutil.rmtree(test_dir)
    print(f"Test directory preserved for inspection: {test_dir}")

def test_installation():
    """Test that Tascade AI is installed and accessible."""
    print_header("Testing Installation")
    
    print_test("Command Availability", "Check if Tascade AI commands are available")
    stdout, stderr, code = run_command("npx tascade-ai --help", check=False)
    success = code == 0 and "Usage:" in stdout
    print_result(success, f"Return code: {code}")
    if not success:
        print(f"Error: {stderr}")
        sys.exit(1)
    
    print_test("Version Check", "Verify Tascade AI version")
    stdout, stderr, code = run_command("npx tascade-ai --version", check=False)
    success = code == 0 and stdout.strip()
    print_result(success, f"Version: {stdout}")
    
    return success

def test_initialization():
    """Test initializing a project with Tascade AI."""
    print_header("Testing Project Initialization")
    
    print_test("Project Init", "Initialize Tascade AI in the project")
    stdout, stderr, code = run_command("npx tascade-ai init", check=False)
    success = code == 0
    print_result(success)
    
    print_test("Config Creation", "Check if configuration files were created")
    has_config = os.path.exists(".tascade-ai") and os.path.exists(".tascade-ai/data.json")
    print_result(has_config)
    
    return success and has_config

def test_task_management():
    """Test task management features."""
    print_header("Testing Task Management")
    
    # Add a task
    print_test("Add Task", "Create a new task")
    task_data = {
        "title": f"Test Task {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "This is a test task created by the test script",
        "priority": "high"
    }
    task_json = json.dumps(task_data)
    
    # Use echo to pipe the JSON to the command
    stdout, stderr, code = run_command(f"echo '{task_json}' | npx tascade-ai tasks --add", check=False)
    add_success = code == 0
    print_result(add_success)
    
    # List tasks
    print_test("List Tasks", "List all tasks")
    stdout, stderr, code = run_command("npx tascade-ai tasks --list", check=False)
    list_success = code == 0 and task_data["title"] in stdout
    print_result(list_success)
    
    # Extract task ID from the list output
    task_id = None
    try:
        # This is a simple extraction method - may need adjustment based on actual output format
        for line in stdout.split("\n"):
            if task_data["title"] in line:
                # Assuming ID is at the beginning of the line
                task_id = line.split()[0]
                break
    except Exception as e:
        print(f"Error extracting task ID: {e}")
    
    if not task_id:
        print(f"{YELLOW}Warning: Could not extract task ID, skipping update and delete tests{RESET}")
        return add_success and list_success
    
    # Update task
    print_test("Update Task", f"Update task {task_id}")
    stdout, stderr, code = run_command(f"npx tascade-ai tasks --update {task_id} --status in-progress", check=False)
    update_success = code == 0
    print_result(update_success)
    
    # Get task
    print_test("Get Task", f"Get task {task_id}")
    stdout, stderr, code = run_command(f"npx tascade-ai tasks --get {task_id}", check=False)
    get_success = code == 0 and task_data["title"] in stdout and "in-progress" in stdout.lower()
    print_result(get_success)
    
    # Delete task
    print_test("Delete Task", f"Delete task {task_id}")
    stdout, stderr, code = run_command(f"npx tascade-ai tasks --delete {task_id}", check=False)
    delete_success = code == 0
    print_result(delete_success)
    
    # Verify deletion
    stdout, stderr, code = run_command("npx tascade-ai tasks --list", check=False)
    verify_delete = task_id not in stdout
    print_result(verify_delete, "Task successfully deleted")
    
    return add_success and list_success and update_success and get_success and delete_success and verify_delete

def test_time_tracking():
    """Test time tracking features."""
    print_header("Testing Time Tracking")
    
    # Add a task for time tracking
    print_test("Create Task for Tracking", "Create a new task for time tracking")
    task_data = {
        "title": f"Time Tracking Test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "This is a test task for time tracking",
        "priority": "medium"
    }
    task_json = json.dumps(task_data)
    
    stdout, stderr, code = run_command(f"echo '{task_json}' | npx tascade-ai tasks --add", check=False)
    add_success = code == 0
    print_result(add_success)
    
    # Get task ID
    stdout, stderr, code = run_command("npx tascade-ai tasks --list", check=False)
    task_id = None
    try:
        for line in stdout.split("\n"):
            if task_data["title"] in line:
                task_id = line.split()[0]
                break
    except Exception as e:
        print(f"Error extracting task ID: {e}")
    
    if not task_id:
        print(f"{YELLOW}Warning: Could not extract task ID, skipping time tracking tests{RESET}")
        return add_success
    
    # Start time tracking
    print_test("Start Time Tracking", f"Start tracking time for task {task_id}")
    stdout, stderr, code = run_command(f"npx tascade-ai track --start {task_id}", check=False)
    start_success = code == 0
    print_result(start_success)
    
    # Extract session ID
    session_id = None
    try:
        # This is a simple extraction method - may need adjustment based on actual output format
        for line in stdout.split("\n"):
            if "session" in line.lower() and "id" in line.lower():
                # Extract session ID - format depends on actual output
                parts = line.split(":")
                if len(parts) > 1:
                    session_id = parts[1].strip()
                break
    except Exception as e:
        print(f"Error extracting session ID: {e}")
    
    if not session_id:
        print(f"{YELLOW}Warning: Could not extract session ID, skipping stop tracking test{RESET}")
        return add_success and start_success
    
    # Wait a bit to accumulate some tracking time
    print("Waiting 3 seconds to simulate work...")
    time.sleep(3)
    
    # Stop time tracking
    print_test("Stop Time Tracking", f"Stop tracking time for session {session_id}")
    stdout, stderr, code = run_command(f"npx tascade-ai track --stop {session_id}", check=False)
    stop_success = code == 0
    print_result(stop_success)
    
    # List time entries
    print_test("List Time Entries", "List all time entries")
    stdout, stderr, code = run_command("npx tascade-ai track --list", check=False)
    list_success = code == 0 and task_id in stdout
    print_result(list_success)
    
    # Clean up - delete the task
    run_command(f"npx tascade-ai tasks --delete {task_id}", check=False)
    
    return add_success and start_success and stop_success and list_success

def test_mcp_server(port):
    """Test MCP server functionality."""
    print_header("Testing MCP Server")
    
    # Start MCP server in the background
    print_test("Start MCP Server", f"Start the MCP server on port {port}")
    process = subprocess.Popen(
        f"npx tascade-ai mcp --port {port}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    # Check if the server is running
    stdout, stderr, code = run_command(f"lsof -i :{port}", check=False)
    server_running = code == 0 and "LISTEN" in stdout
    print_result(server_running, f"Server running on port {port}")
    
    if server_running:
        # Test a simple WebSocket connection
        print_test("WebSocket Connection", "Test connecting to the MCP server")
        # This is a placeholder - in a real test, you would use a WebSocket client
        print(f"{YELLOW}Note: WebSocket connection test requires a WebSocket client.{RESET}")
        print(f"{YELLOW}Please use the Windsurf integration test for a complete test.{RESET}")
        
        # Kill the server process
        process.terminate()
        process.wait(timeout=5)
        print("MCP server stopped.")
    else:
        print(f"{RED}Failed to start MCP server on port {port}{RESET}")
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
    
    return server_running

def main():
    parser = argparse.ArgumentParser(description="Test Tascade AI features")
    parser.add_argument("--port", type=int, default=8766, help="Port to use for the MCP server")
    args = parser.parse_args()
    
    print_header("Tascade AI Feature Test")
    print(f"Starting tests at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing with port: {args.port}")
    
    # Track test results
    results = {}
    
    # Test installation
    results["installation"] = test_installation()
    
    # Create a test project
    test_dir = create_test_project()
    
    try:
        # Test initialization
        results["initialization"] = test_initialization()
        
        # Test task management
        results["task_management"] = test_task_management()
        
        # Test time tracking
        results["time_tracking"] = test_time_tracking()
        
        # Test MCP server
        results["mcp_server"] = test_mcp_server(args.port)
    finally:
        # Clean up
        cleanup_test_project(test_dir)
    
    # Print summary
    print_header("Test Summary")
    all_passed = True
    for test, passed in results.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"{test.replace('_', ' ').title()}: {status}")
        all_passed = all_passed and passed
    
    print(f"\nOverall Result: {'All tests passed!' if all_passed else 'Some tests failed.'}")
    print(f"Tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
