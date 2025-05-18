#!/usr/bin/env python3
"""
Test script for the Task Execution System in Tascade AI.

This script demonstrates the new Task Execution features implemented from mcp-shrimp-task-manager:
1. Task Complexity Assessment
2. Execution Preparation
3. Execution Step Logging
4. Execution Status Tracking
5. Execution Completion

These features provide a structured approach to executing tasks with detailed guidance,
complexity assessment, and quality requirements.
"""

import sys
import os
import json
from datetime import datetime
import time

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the core modules
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
    """Test Task Execution System in Tascade AI."""
    print_section("Tascade AI Task Execution System Demo")
    
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
    
    # Task 2: Design Database Schema (dependency for Task 1)
    task2 = Task(
        id="task2",
        title="Design Database Schema",
        description="""
Design a comprehensive database schema for the authentication system with:
- User management tables
- Role and permission tables
- Session storage
- Audit logging
        """,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.DONE,  # Already completed
        dependencies=[],
        created_at=datetime.now()
    )
    task_manager.add_task(task2)
    print(f"Created task: {task2.id} - {task2.title} (status: {task2.status.value})")
    
    # Add dependency
    task1.dependencies.append(task2.id)
    print(f"Added dependency: {task1.id} depends on {task2.id}")
    
    # Test Task Complexity Assessment
    print_section("Task Complexity Assessment")
    
    print("Assessing complexity of task1...")
    complexity_result = task_manager.assess_task_complexity("task1")
    print(f"Complexity Level: {complexity_result['complexity']['level']}")
    print("\nComplexity Metrics:")
    for metric, value in complexity_result['complexity']['metrics'].items():
        print(f"  {metric}: {value}")
    
    print("\nRecommendations:")
    for recommendation in complexity_result['complexity']['recommendations']:
        print(f"  - {recommendation}")
    
    # Test Task Execution Preparation
    print_section("Task Execution Preparation")
    
    print("Preparing execution for task1...")
    preparation_result = task_manager.prepare_task_execution("task1")
    
    print("\nExecution Guidance:")
    print("Execution Steps:")
    for step in preparation_result['preparation']['execution_guidance']['execution_steps']:
        print(f"  - {step['step']}: {step['description']}")
    
    print("\nQuality Requirements:")
    for req in preparation_result['preparation']['execution_guidance']['quality_requirements']:
        print(f"  - {req['requirement']} ({req['importance']}): {req['description']}")
    
    # Test Task Execution Step Logging
    print_section("Task Execution Step Logging")
    
    # Log execution steps
    print("Logging execution steps for task1...")
    
    # Step 1: Analyze Requirements
    step1_result = task_manager.log_execution_step(
        "task1", 
        "Analyze Requirements", 
        "started",
        "Starting to analyze authentication system requirements"
    )
    print(f"Logged step: {step1_result['step_log']['step_name']} - {step1_result['step_log']['status']}")
    
    # Simulate work being done
    time.sleep(1)
    
    # Complete Step 1
    step1_complete_result = task_manager.log_execution_step(
        "task1", 
        "Analyze Requirements", 
        "completed",
        "Completed requirements analysis, identified key authentication components"
    )
    print(f"Logged step: {step1_complete_result['step_log']['step_name']} - {step1_complete_result['step_log']['status']}")
    
    # Step 2: Design Solution
    step2_result = task_manager.log_execution_step(
        "task1", 
        "Design Solution", 
        "started",
        "Starting to design the authentication system architecture"
    )
    print(f"Logged step: {step2_result['step_log']['step_name']} - {step2_result['step_log']['status']}")
    
    # Simulate work being done
    time.sleep(1)
    
    # Complete Step 2
    step2_complete_result = task_manager.log_execution_step(
        "task1", 
        "Design Solution", 
        "completed",
        "Completed authentication system design with JWT implementation"
    )
    print(f"Logged step: {step2_complete_result['step_log']['step_name']} - {step2_complete_result['step_log']['status']}")
    
    # Test Task Execution Status
    print_section("Task Execution Status")
    
    print("Getting execution status for task1...")
    status_result = task_manager.get_task_execution_status("task1")
    
    print(f"Status: {status_result['execution_status']['status']}")
    print(f"Progress: {status_result['execution_status']['progress']}%")
    print(f"Steps Completed: {status_result['execution_status']['steps_completed']} of {status_result['execution_status']['total_steps']}")
    print(f"Duration: {status_result['execution_status']['duration_seconds']} seconds")
    
    # Step 3: Implement Solution
    step3_result = task_manager.log_execution_step(
        "task1", 
        "Implement Solution", 
        "started",
        "Starting implementation of authentication system"
    )
    print(f"\nLogged step: {step3_result['step_log']['step_name']} - {step3_result['step_log']['status']}")
    
    # Simulate work being done
    time.sleep(1)
    
    # Complete Step 3
    step3_complete_result = task_manager.log_execution_step(
        "task1", 
        "Implement Solution", 
        "completed",
        "Completed implementation of user registration, login, and role-based access control"
    )
    print(f"Logged step: {step3_complete_result['step_log']['step_name']} - {step3_complete_result['step_log']['status']}")
    
    # Step 4: Test and Verify
    step4_result = task_manager.log_execution_step(
        "task1", 
        "Test and Verify", 
        "started",
        "Starting testing of authentication system"
    )
    print(f"Logged step: {step4_result['step_log']['step_name']} - {step4_result['step_log']['status']}")
    
    # Simulate work being done
    time.sleep(1)
    
    # Complete Step 4
    step4_complete_result = task_manager.log_execution_step(
        "task1", 
        "Test and Verify", 
        "completed",
        "Completed testing, all verification criteria met"
    )
    print(f"Logged step: {step4_complete_result['step_log']['step_name']} - {step4_complete_result['step_log']['status']}")
    
    # Get updated status
    print("\nGetting updated execution status for task1...")
    updated_status_result = task_manager.get_task_execution_status("task1")
    
    print(f"Status: {updated_status_result['execution_status']['status']}")
    print(f"Progress: {updated_status_result['execution_status']['progress']}%")
    print(f"Steps Completed: {updated_status_result['execution_status']['steps_completed']} of {updated_status_result['execution_status']['total_steps']}")
    print(f"Duration: {updated_status_result['execution_status']['duration_seconds']} seconds")
    
    # Test Task Execution Completion
    print_section("Task Execution Completion")
    
    print("Completing execution for task1...")
    completion_result = task_manager.complete_task_execution(
        "task1",
        True,  # Success
        "Successfully implemented authentication system with all required features"
    )
    
    print(f"Execution Success: {completion_result['execution_summary']['success']}")
    print(f"Duration: {completion_result['execution_summary']['duration']} seconds")
    print(f"Steps Completed: {completion_result['execution_summary']['steps_completed']} of {completion_result['execution_summary']['total_steps']}")
    print(f"Completion Notes: {completion_result['execution_summary']['completion_notes']}")
    
    # Verify task status has been updated
    task1_updated = task_manager.get_task("task1")
    print(f"\nUpdated Task Status: {task1_updated.status.value}")
    
    # Show execution logs
    print_section("Execution Logs")
    
    print("Execution logs for task1:")
    for log in task1_updated.execution_context.get("logs", []):
        timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%H:%M:%S")
        print(f"[{timestamp}] [{log['level'].upper()}] {log['message']}")
    
    print_section("Demo Complete")
    print("The Task Execution System has been successfully integrated into Tascade AI.")
    print("This system provides a structured approach to executing tasks with detailed")
    print("guidance, complexity assessment, and quality requirements.")

if __name__ == "__main__":
    main()
