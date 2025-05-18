#!/usr/bin/env python3
"""
Test script for the Task Planning System in Tascade AI.

This script demonstrates the new Task Planning features implemented from mcp-shrimp-task-manager:
1. Execution Plan Generation
2. Completion Date Estimation
3. Gantt Chart Generation

These features provide detailed planning capabilities for tasks, enhancing project management.
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
    """Test Task Planning features in Tascade AI."""
    print_section("Tascade AI Task Planning Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample tasks
    print_section("Creating Sample Tasks")
    
    # Task 1: Implement Authentication System
    task1 = Task(
        id="task1",
        title="Implement Authentication System",
        description="""
Create a secure authentication system with the following features:
- User registration with email verification
- Login with JWT token-based authentication
- Password reset functionality
- Two-factor authentication option
- Role-based access control
- Session management with timeout
        """,
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now(),
        complexity_score=8,
        verification_criteria="""
1. User registration works with proper validation
2. Email verification process is secure
3. JWT implementation follows security best practices
4. Password reset flow is secure and user-friendly
5. Two-factor authentication works correctly
6. Role-based permissions are enforced
7. Sessions expire after the configured timeout
"""
    )
    task_manager.add_task(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Design Database Schema
    task2 = Task(
        id="task2",
        title="Design Database Schema",
        description="""
Design a comprehensive database schema for the application with:
- User management tables
- Content storage and organization
- Analytics data collection
- Audit logging
- Efficient indexing strategy
        """,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now(),
        complexity_score=6,
        verification_criteria="""
1. Schema supports all required data entities
2. Relationships are properly defined
3. Indexing strategy optimizes query performance
4. Schema follows normalization best practices
5. Data integrity constraints are in place
"""
    )
    task_manager.add_task(task2)
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Test Execution Plan Generation
    print_section("Execution Plan Generation")
    
    print("Generating execution plan for task1...")
    context = {
        "team_skills": ["JavaScript", "Node.js", "React", "MongoDB"],
        "project_constraints": {
            "deadline": (datetime.now() + timedelta(days=14)).isoformat(),
            "resources": "Limited backend developer availability"
        }
    }
    execution_plan = task_manager.generate_execution_plan("task1", context)
    print_json(execution_plan)
    
    # Test Completion Date Estimation
    print_section("Completion Date Estimation")
    
    print("Estimating completion date for task1...")
    start_date = datetime.now()
    completion_estimation = task_manager.estimate_completion_date("task1", start_date)
    print_json(completion_estimation)
    
    # Test Gantt Chart Generation
    print_section("Gantt Chart Generation")
    
    print("Generating Gantt chart for task1...")
    gantt_chart = task_manager.generate_gantt_chart("task1", start_date)
    print(gantt_chart["gantt_chart"])
    
    # Test Execution Plan for a Different Task Type
    print_section("Execution Plan for Different Task Type")
    
    print("Generating execution plan for task2 (database design)...")
    execution_plan2 = task_manager.generate_execution_plan("task2")
    print_json(execution_plan2)
    
    print_section("Demo Complete")
    print("The Task Planning System has been successfully integrated into Tascade AI.")
    print("This system provides detailed execution plans, completion date estimates,")
    print("and Gantt charts for visualizing task timelines.")

if __name__ == "__main__":
    main()
