#!/usr/bin/env python3
"""
Test script for core features in Tascade AI.

This script demonstrates the new features implemented from claude-task-master and mcp-shrimp-task-manager:
1. Dependency Management
2. Task Prioritization
3. Task Reflection

This simplified version avoids dependencies on external packages.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the core modules to avoid dependencies
from src.core.models import Task, TaskStatus, TaskPriority
from src.core.dependency_manager import DependencyManager
from src.core.task_prioritizer import TaskPrioritizer
from src.core.task_reflector import TaskReflector

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test core features in Tascade AI."""
    print_section("Tascade AI Core Features Demo")
    
    # Create sample tasks with dependencies
    print_section("Creating Sample Tasks")
    
    # Create tasks manually
    tasks = {}
    
    # Task 1: Implement Authentication System
    task1 = Task(
        id="task1",
        title="Implement Authentication System",
        description="Create a secure authentication system for the application",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now()
    )
    tasks[task1.id] = task1
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Design Database Schema
    task2 = Task(
        id="task2",
        title="Design Database Schema",
        description="Design the database schema for user data",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now()
    )
    tasks[task2.id] = task2
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Task 3: Implement User Interface
    task3 = Task(
        id="task3",
        title="Implement User Interface",
        description="Create the user interface for login and registration",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=[task1.id],  # Depends on authentication system
        created_at=datetime.now()
    )
    tasks[task3.id] = task3
    print(f"Created task: {task3.id} - {task3.title} (depends on {task1.id})")
    
    # Task 4: Implement API Endpoints
    task4 = Task(
        id="task4",
        title="Implement API Endpoints",
        description="Create API endpoints for user management",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=[task1.id, task2.id],  # Depends on auth system and database schema
        created_at=datetime.now()
    )
    tasks[task4.id] = task4
    print(f"Created task: {task4.id} - {task4.title} (depends on {task1.id}, {task2.id})")
    
    # Task 5: Write Documentation
    task5 = Task(
        id="task5",
        title="Write Documentation",
        description="Document the authentication system and API endpoints",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        dependencies=[task3.id, task4.id],  # Depends on UI and API
        created_at=datetime.now()
    )
    tasks[task5.id] = task5
    print(f"Created task: {task5.id} - {task5.title} (depends on {task3.id}, {task4.id})")
    
    # Task 6: Deploy Application
    task6 = Task(
        id="task6",
        title="Deploy Application",
        description="Deploy the application to production",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        dependencies=[task5.id],  # Depends on documentation
        created_at=datetime.now()
    )
    tasks[task6.id] = task6
    print(f"Created task: {task6.id} - {task6.title} (depends on {task5.id})")
    
    # Add a circular dependency (task5 depends on task6, creating a cycle)
    task5.dependencies.append(task6.id)
    print(f"Added circular dependency: {task5.id} now depends on {task6.id}")
    
    # Test Dependency Management
    print_section("Dependency Management")
    
    # Validate dependencies
    print("Validating dependencies...")
    validation_result = DependencyManager.validate_dependencies(tasks)
    print_json(validation_result)
    
    # Fix dependencies
    print("\nFixing invalid dependencies...")
    updated_tasks, fix_report = DependencyManager.fix_dependencies(tasks)
    print_json(fix_report)
    
    # Update tasks with fixed dependencies
    tasks = updated_tasks
    
    # Validate again to confirm fixes
    print("\nValidating dependencies after fixes...")
    validation_result = DependencyManager.validate_dependencies(tasks)
    print_json(validation_result)
    
    # Get dependency chain for a task
    print("\nGetting dependency chain for task5...")
    dependency_chain = DependencyManager.get_dependency_chain(tasks, "task5")
    print_json(dependency_chain)
    
    # Find blocked tasks
    print("\nFinding blocked tasks...")
    blocked_tasks = DependencyManager.find_blocked_tasks(tasks)
    print_json(blocked_tasks)
    
    # Test Task Prioritization
    print_section("Task Prioritization")
    
    # Find next task
    print("Finding next task to work on...")
    next_task = TaskPrioritizer.find_next_task(tasks)
    print_json(next_task)
    
    # Get task queue
    print("\nGetting prioritized task queue...")
    task_queue = TaskPrioritizer.get_task_queue(tasks, limit=3)
    print_json(task_queue)
    
    # Mark a task as in progress for testing
    tasks["task1"].status = TaskStatus.IN_PROGRESS
    print(f"\nMarked task task1 as IN_PROGRESS")
    
    # Complete a task with execution data for testing
    tasks["task2"].status = TaskStatus.DONE
    
    # Add execution context to the completed task
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now() - timedelta(minutes=15)
    
    tasks["task2"].execution_context = {
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
    print(f"Added execution context to task task2")
    
    # Find next task again after updates
    print("\nFinding next task after updates...")
    next_task = TaskPrioritizer.find_next_task(tasks)
    print_json(next_task)
    
    # Estimate completion time
    print("\nEstimating project completion time...")
    completion_estimate = TaskPrioritizer.estimate_completion_time(tasks)
    print_json(completion_estimate)
    
    # Test Task Reflection
    print_section("Task Reflection")
    
    # Create a task reflector without AI provider for testing
    task_reflector = TaskReflector()
    
    # Reflect on a completed task
    print("Reflecting on completed task...")
    task_reflection = task_reflector.reflect_on_task(tasks["task2"])
    print_json(task_reflection)
    
    # Reflect on the project
    print("\nReflecting on the entire project...")
    project_reflection = task_reflector.reflect_on_project(tasks)
    print_json(project_reflection)
    
    print_section("Demo Complete")
    print("The enhanced features from claude-task-master and mcp-shrimp-task-manager")
    print("have been successfully integrated into Tascade AI.")

if __name__ == "__main__":
    main()
