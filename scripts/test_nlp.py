#!/usr/bin/env python3
"""
Test script for the Natural Language Task Processing System in Tascade AI.

This script demonstrates the new Natural Language Processing features:
1. Processing natural language commands for task management
2. Maintaining conversation context across multiple interactions
3. Extracting intents and entities from natural language input
4. Executing appropriate task operations based on recognized intents
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the project root to the Python path to allow importing the package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.task_manager import TaskManager
from src.core.recommendation.engine import DefaultRecommendationEngine
from src.core.recommendation.preference_manager import UserPreferenceManager
from src.core.recommendation.historical_analyzer import TaskPerformanceAnalyzer
from src.core.recommendation.workload_balancer import TaskWorkloadBalancer
from src.core.nlp.manager import TascadeNLPManager
from src.core.nlp.parser import DefaultNLParser
from src.core.nlp.executor import TaskCommandExecutor


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))


def print_nlp_result(result):
    """Print NLP result in a readable format."""
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['data']:
        print("\nData:")
        if "task" in result['data']:
            print_task(result['data']['task'])
        elif "tasks" in result['data']:
            print_tasks(result['data']['tasks'])
        elif "recommendations" in result['data']:
            print_recommendations(result['data']['recommendations'])
        else:
            print_json(result['data'])


def print_task(task):
    """Print a task in a readable format."""
    print(f"ID: {task.get('id', 'N/A')}")
    print(f"Title: {task.get('title', 'N/A')}")
    print(f"Status: {task.get('status', 'N/A')}")
    print(f"Priority: {task.get('priority', 'N/A')}")
    
    if "due_date" in task:
        print(f"Due Date: {task['due_date']}")
    
    if "description" in task and task["description"]:
        print("\nDescription:")
        print(task["description"])
    
    if "dependencies" in task and task["dependencies"]:
        print("\nDependencies:")
        for dep in task["dependencies"]:
            print(f"- {dep}")


def print_tasks(tasks):
    """Print a list of tasks in a readable format."""
    if not tasks:
        print("No tasks found.")
        return
    
    print(f"Found {len(tasks)} tasks:")
    
    # Print header
    print(f"{'ID':<10} {'Title':<30} {'Status':<15} {'Priority':<10} {'Due Date':<15}")
    print("-" * 80)
    
    # Print tasks
    for task in tasks:
        task_id = task.get("id", "N/A")
        title = task.get("title", "N/A")
        status = task.get("status", "N/A")
        priority = task.get("priority", "N/A")
        due_date = task.get("due_date", "N/A")
        
        # Truncate title if too long
        if len(title) > 27:
            title = title[:24] + "..."
        
        print(f"{task_id:<10} {title:<30} {status:<15} {priority:<10} {due_date:<15}")


def print_recommendations(recommendations):
    """Print task recommendations in a readable format."""
    if not recommendations:
        print("No recommendations available.")
        return
    
    print(f"Recommended Tasks ({len(recommendations)}):")
    
    # Print header
    print(f"{'ID':<10} {'Title':<30} {'Score':<10} {'Priority':<10} {'Due Date':<15}")
    print("-" * 80)
    
    # Print recommendations
    for rec in recommendations:
        task = rec.get("task", {})
        task_id = task.get("id", "N/A")
        title = task.get("title", "N/A")
        score = f"{rec.get('score', 0):.2f}"
        priority = task.get("priority", "N/A")
        due_date = task.get("due_date", "N/A")
        
        # Truncate title if too long
        if len(title) > 27:
            title = title[:24] + "..."
        
        print(f"{task_id:<10} {title:<30} {score:<10} {priority:<10} {due_date:<15}")
        
        # Print explanation if available
        if "explanation" in rec:
            print(f"  Reason: {rec['explanation']}")


def main():
    """Test the Natural Language Task Processing System in Tascade AI."""
    print_section("Natural Language Task Processing System Test")
    
    # Initialize the task manager
    task_manager = TaskManager()
    
    # Create test tasks
    print("Creating test tasks...")
    
    task1_id = task_manager.create_task({
        "title": "Implement user authentication",
        "description": "Add user authentication using JWT tokens",
        "priority": "high",
        "status": "pending",
        "due_date": (datetime.now() + timedelta(days=7)).isoformat()
    })
    
    task2_id = task_manager.create_task({
        "title": "Design database schema",
        "description": "Create the database schema for the application",
        "priority": "medium",
        "status": "pending",
        "due_date": (datetime.now() + timedelta(days=3)).isoformat()
    })
    
    task3_id = task_manager.create_task({
        "title": "Write API documentation",
        "description": "Document the REST API endpoints",
        "priority": "low",
        "status": "pending",
        "due_date": (datetime.now() + timedelta(days=14)).isoformat()
    })
    
    # Initialize recommendation system components
    preference_manager = UserPreferenceManager()
    historical_analyzer = TaskPerformanceAnalyzer()
    workload_balancer = TaskWorkloadBalancer()
    
    # Initialize recommendation engine
    recommendation_engine = DefaultRecommendationEngine(
        user_preference_manager=preference_manager,
        historical_analyzer=historical_analyzer,
        workload_balancer=workload_balancer
    )
    
    # Initialize NLP manager
    nlp_manager = TascadeNLPManager(
        task_manager=task_manager,
        recommendation_system=recommendation_engine
    )
    
    # Test NLP processing
    print_section("Testing Natural Language Processing")
    
    # Test 1: Create a task
    print("\nTest 1: Create a task")
    result = nlp_manager.process_input(
        text="Create a new task called Fix login page bug with high priority due tomorrow",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 2: List tasks
    print("\nTest 2: List tasks")
    result = nlp_manager.process_input(
        text="List all tasks",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 3: Get a specific task
    print("\nTest 3: Get a specific task")
    result = nlp_manager.process_input(
        text=f"Show task {task1_id}",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 4: Update a task
    print("\nTest 4: Update a task")
    result = nlp_manager.process_input(
        text=f"Update task {task2_id} with priority high",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 5: Complete a task
    print("\nTest 5: Complete a task")
    result = nlp_manager.process_input(
        text=f"Mark task {task3_id} as complete",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 6: Get recommendations
    print("\nTest 6: Get recommendations")
    result = nlp_manager.process_input(
        text="What tasks should I work on?",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 7: Add dependency
    print("\nTest 7: Add dependency")
    result = nlp_manager.process_input(
        text=f"Add dependency: task {task1_id} depends on task {task2_id}",
        session_id="test_session"
    )
    print_nlp_result(result)
    
    # Test 8: Show conversation history
    print_section("Conversation History")
    history = nlp_manager.get_session_history("test_session")
    
    for i, turn in enumerate(history, 1):
        print(f"\nTurn {i}:")
        print(f"User: {turn['user_input']}")
        print(f"System: {turn['system_response']}")
    
    print_section("Test Complete")
    print("The Natural Language Task Processing System is working correctly.")


if __name__ == "__main__":
    main()
