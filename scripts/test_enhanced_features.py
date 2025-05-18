#!/usr/bin/env python3
"""
Test script for enhanced features in Tascade AI.

This script demonstrates the new features implemented from claude-task-master and mcp-shrimp-task-manager:
1. Dependency Management
2. Task Prioritization
3. Task Reflection

Usage:
    python scripts/test_enhanced_features.py
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.task_manager import TaskManager
from src.core.models import Task, TaskStatus, TaskPriority

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test enhanced features in Tascade AI."""
    print_section("Tascade AI Enhanced Features Demo")
    
    # Initialize TaskManager with Anthropic AI provider
    task_manager = TaskManager("anthropic")
    
    # Create sample tasks with dependencies
    print_section("Creating Sample Tasks")
    
    # Create a task with subtasks
    task1_id = task_manager.add_task(
        title="Implement Authentication System",
        description="Create a secure authentication system for the application",
        priority=TaskPriority.HIGH
    )
    print(f"Created task: {task1_id} - Implement Authentication System")
    
    task2_id = task_manager.add_task(
        title="Design Database Schema",
        description="Design the database schema for user data",
        priority=TaskPriority.MEDIUM
    )
    print(f"Created task: {task2_id} - Design Database Schema")
    
    task3_id = task_manager.add_task(
        title="Implement User Interface",
        description="Create the user interface for login and registration",
        priority=TaskPriority.MEDIUM,
        dependencies=[task1_id]  # Depends on authentication system
    )
    print(f"Created task: {task3_id} - Implement User Interface (depends on {task1_id})")
    
    task4_id = task_manager.add_task(
        title="Implement API Endpoints",
        description="Create API endpoints for user management",
        priority=TaskPriority.MEDIUM,
        dependencies=[task1_id, task2_id]  # Depends on auth system and database schema
    )
    print(f"Created task: {task4_id} - Implement API Endpoints (depends on {task1_id}, {task2_id})")
    
    task5_id = task_manager.add_task(
        title="Write Documentation",
        description="Document the authentication system and API endpoints",
        priority=TaskPriority.LOW,
        dependencies=[task3_id, task4_id]  # Depends on UI and API
    )
    print(f"Created task: {task5_id} - Write Documentation (depends on {task3_id}, {task4_id})")
    
    # Create a circular dependency for testing
    task6_id = task_manager.add_task(
        title="Deploy Application",
        description="Deploy the application to production",
        priority=TaskPriority.LOW,
        dependencies=[task5_id]  # Depends on documentation
    )
    print(f"Created task: {task6_id} - Deploy Application (depends on {task5_id})")
    
    # Add a circular dependency (task5 depends on task6, creating a cycle)
    task5 = task_manager.get_task(task5_id)
    task5.dependencies.append(task6_id)
    print(f"Added circular dependency: {task5_id} now depends on {task6_id}")
    
    # Test Dependency Management
    print_section("Dependency Management")
    
    # Validate dependencies
    print("Validating dependencies...")
    validation_result = task_manager.validate_dependencies()
    print_json(validation_result)
    
    # Fix dependencies
    print("\nFixing invalid dependencies...")
    fix_report = task_manager.fix_dependencies()
    print_json(fix_report)
    
    # Validate again to confirm fixes
    print("\nValidating dependencies after fixes...")
    validation_result = task_manager.validate_dependencies()
    print_json(validation_result)
    
    # Get dependency chain for a task
    print("\nGetting dependency chain for task5...")
    dependency_chain = task_manager.get_dependency_chain(task5_id)
    print_json(dependency_chain)
    
    # Find blocked tasks
    print("\nFinding blocked tasks...")
    blocked_tasks = task_manager.find_blocked_tasks()
    print_json(blocked_tasks)
    
    # Test Task Prioritization
    print_section("Task Prioritization")
    
    # Find next task
    print("Finding next task to work on...")
    next_task = task_manager.find_next_task()
    print_json(next_task)
    
    # Get task queue
    print("\nGetting prioritized task queue...")
    task_queue = task_manager.get_task_queue(limit=3)
    print_json(task_queue)
    
    # Mark a task as in progress for testing
    task1 = task_manager.get_task(task1_id)
    task1.status = TaskStatus.IN_PROGRESS
    print(f"\nMarked task {task1_id} as IN_PROGRESS")
    
    # Complete a task with execution data for testing
    task2 = task_manager.get_task(task2_id)
    task2.status = TaskStatus.DONE
    
    # Add execution context to the completed task
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now() - timedelta(minutes=15)
    
    task2.execution_context = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "status": "completed",
        "metrics": {
            "time_spent": (end_time - start_time).total_seconds(),
            "steps_completed": 5,
            "total_steps": 5,
            "checkpoints": [
                {
                    "time": (start_time + timedelta(minutes=10)).isoformat(),
                    "step_name": "Define user table schema",
                    "status": "completed"
                },
                {
                    "time": (start_time + timedelta(minutes=25)).isoformat(),
                    "step_name": "Define authentication table schema",
                    "status": "completed"
                },
                {
                    "time": (start_time + timedelta(minutes=40)).isoformat(),
                    "step_name": "Define relationships between tables",
                    "status": "completed"
                }
            ]
        },
        "logs": [
            {
                "time": start_time.isoformat(),
                "level": "info",
                "message": "Started database schema design"
            },
            {
                "time": (start_time + timedelta(minutes=20)).isoformat(),
                "level": "info",
                "message": "Completed user table schema"
            },
            {
                "time": (start_time + timedelta(minutes=35)).isoformat(),
                "level": "warning",
                "message": "Potential performance issue with current index strategy"
            },
            {
                "time": end_time.isoformat(),
                "level": "info",
                "message": "Completed database schema design"
            }
        ]
    }
    print(f"Added execution context to task {task2_id}")
    
    # Find next task again after updates
    print("\nFinding next task after updates...")
    next_task = task_manager.find_next_task()
    print_json(next_task)
    
    # Estimate completion time
    print("\nEstimating project completion time...")
    completion_estimate = task_manager.estimate_completion_time()
    print_json(completion_estimate)
    
    # Test Task Reflection
    print_section("Task Reflection")
    
    # Reflect on a completed task
    print("Reflecting on completed task...")
    task_reflection = task_manager.reflect_on_task(task2_id)
    print_json(task_reflection)
    
    # Reflect on the project
    print("\nReflecting on the entire project...")
    project_reflection = task_manager.reflect_on_project()
    print_json(project_reflection)
    
    print_section("Demo Complete")
    print("The enhanced features from claude-task-master and mcp-shrimp-task-manager")
    print("have been successfully integrated into Tascade AI.")

if __name__ == "__main__":
    main()
