#!/usr/bin/env python3
"""
Test script for advanced features in Tascade AI.

This script demonstrates the new features implemented from claude-task-master and mcp-shrimp-task-manager:
1. Task Splitting
2. Task Verification
3. Dependency Management
4. Task Prioritization
5. Task Reflection

This script focuses on demonstrating the new Task Splitting and Task Verification features.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the core modules to avoid dependencies
from src.core.models import Task, TaskStatus, TaskPriority
from src.core.task_manager import TaskManager

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test advanced features in Tascade AI."""
    print_section("Tascade AI Advanced Features Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample tasks with dependencies
    print_section("Creating Sample Tasks")
    
    # Task 1: Design a RESTful API
    task1 = Task(
        id="task1",
        title="Design a RESTful API",
        description="Create a comprehensive design for a RESTful API that supports user authentication, resource management, and data analytics.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now(),
        complexity_score=8,
        verification_criteria="""
1. API design follows RESTful principles
2. Authentication mechanism is secure and follows best practices
3. Resource endpoints are clearly defined with appropriate HTTP methods
4. Request/response formats are documented
5. Error handling strategy is comprehensive
"""
    )
    task_manager.add_task(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Implement User Authentication
    task2 = Task(
        id="task2",
        title="Implement User Authentication",
        description="Implement a secure user authentication system using JWT tokens.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now(),
        complexity_score=6,
        verification_criteria="""
1. JWT implementation is secure
2. Password hashing uses strong algorithms
3. Token refresh mechanism works correctly
4. Authentication endpoints are properly secured
5. Input validation is thorough
"""
    )
    task_manager.add_task(task2)
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Test Task Splitting
    print_section("Task Splitting")
    
    print("Splitting task1 using 'technical' strategy...")
    split_result = task_manager.split_task("task1", strategy="technical", num_subtasks=5)
    print_json(split_result)
    
    # Get the generated subtasks
    subtasks = [task_manager.get_task(subtask_id) for subtask_id in task_manager.get_task("task1").subtasks]
    
    print("\nGenerated Subtasks:")
    for subtask in subtasks:
        print(f"- {subtask.id}: {subtask.title}")
        print(f"  Description: {subtask.description}")
        print(f"  Dependencies: {subtask.dependencies}")
        print()
    
    # Test Task Verification
    print_section("Task Verification")
    
    # Mark a subtask as completed
    if subtasks:
        completed_subtask = subtasks[0]
        completed_subtask.status = TaskStatus.DONE
        
        # Add execution context to the completed subtask
        completed_subtask.execution_context = {
            "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "end_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "status": "completed",
            "metrics": {
                "time_spent": 3600,  # 1 hour in seconds
                "steps_completed": 5,
                "total_steps": 5
            },
            "logs": [
                {
                    "time": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "level": "info",
                    "message": f"Started working on {completed_subtask.title}"
                },
                {
                    "time": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "level": "info",
                    "message": f"Completed {completed_subtask.title}"
                }
            ]
        }
        
        print(f"Marked subtask {completed_subtask.id} as DONE")
        
        # Create artifacts for verification
        artifacts = {
            "code_snippet": """
def design_data_model():
    \"\"\"Design the data model for the API.\"\"\"
    # Define user schema
    user_schema = {
        "id": "string",
        "username": "string",
        "email": "string",
        "password_hash": "string",
        "created_at": "datetime",
        "last_login": "datetime"
    }
    
    # Define resource schema
    resource_schema = {
        "id": "string",
        "name": "string",
        "description": "string",
        "owner_id": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
    
    return {
        "user": user_schema,
        "resource": resource_schema
    }
""",
            "documentation": """
# API Data Model

## User Entity
- id: Unique identifier for the user
- username: User's username
- email: User's email address
- password_hash: Hashed password
- created_at: Account creation timestamp
- last_login: Last login timestamp

## Resource Entity
- id: Unique identifier for the resource
- name: Resource name
- description: Resource description
- owner_id: ID of the user who owns the resource
- created_at: Resource creation timestamp
- updated_at: Resource last update timestamp
"""
        }
        
        print("Verifying completed subtask...")
        verification_result = task_manager.verify_task(completed_subtask.id, artifacts)
        
        print("\nVerification Report:")
        print(verification_result["verification_report"])
        
        # If verification failed, show improvement suggestions
        if not verification_result["verification_result"].get("verified", False):
            print("\nImprovement Suggestions:")
            for suggestion in verification_result["verification_result"].get("improvement_suggestions", []):
                print(f"- {suggestion}")
    
    # Test Task Dependency Management
    print_section("Dependency Management")
    
    # Add dependencies between subtasks
    if len(subtasks) >= 3:
        # Make subtask 2 depend on subtask 1
        subtasks[1].dependencies.append(subtasks[0].id)
        print(f"Added dependency: {subtasks[1].id} depends on {subtasks[0].id}")
        
        # Make subtask 3 depend on subtask 2
        subtasks[2].dependencies.append(subtasks[1].id)
        print(f"Added dependency: {subtasks[2].id} depends on {subtasks[1].id}")
        
        # Validate dependencies
        print("\nValidating dependencies...")
        validation_result = task_manager.validate_dependencies()
        print_json(validation_result)
    
    # Test Task Prioritization
    print_section("Task Prioritization")
    
    # Find next task
    print("Finding next task to work on...")
    next_task = task_manager.find_next_task()
    print_json(next_task)
    
    # Get task queue
    print("\nGetting prioritized task queue...")
    task_queue = task_manager.get_task_queue(limit=5)
    print_json(task_queue)
    
    # Test Task Reflection
    print_section("Task Reflection")
    
    # Reflect on a completed subtask
    if subtasks and subtasks[0].status == TaskStatus.DONE:
        print(f"Reflecting on completed subtask {subtasks[0].id}...")
        task_reflection = task_manager.reflect_on_task(subtasks[0].id)
        print_json(task_reflection)
    
    # Reflect on the project
    print("\nReflecting on the entire project...")
    project_reflection = task_manager.reflect_on_project()
    print_json(project_reflection)
    
    print_section("Demo Complete")
    print("The advanced features from claude-task-master and mcp-shrimp-task-manager")
    print("have been successfully integrated into Tascade AI.")

if __name__ == "__main__":
    main()
