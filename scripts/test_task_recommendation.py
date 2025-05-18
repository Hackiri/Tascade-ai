#!/usr/bin/env python3
"""
Test script for the Task Recommendation System.

This script demonstrates the functionality of the Task Recommendation System,
including user preferences, historical analysis, workload balancing, and
task recommendations.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only the recommendation system to avoid external dependencies
from src.core.task_recommendation import TaskRecommendationSystem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tascade.test")


def create_sample_tasks():
    """Create sample tasks for testing."""
    tasks = []
    
    # Create some tasks with different priorities, categories, and deadlines
    tasks.append({
        "id": "task1",
        "title": "Implement login functionality",
        "description": "Create login form and authentication logic",
        "status": "pending",
        "priority": "high",
        "category": "frontend",
        "type": "feature",
        "tags": ["authentication", "ui"],
        "estimated_time": 120,  # 2 hours
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task2",
        "title": "Fix navigation bar bug",
        "description": "Fix issue with dropdown menu in navigation bar",
        "status": "pending",
        "priority": "medium",
        "category": "frontend",
        "type": "bug",
        "tags": ["ui", "bug"],
        "estimated_time": 60,  # 1 hour
        "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task3",
        "title": "Implement user profile API",
        "description": "Create API endpoints for user profile management",
        "status": "pending",
        "priority": "medium",
        "category": "backend",
        "type": "feature",
        "tags": ["api", "user"],
        "estimated_time": 180,  # 3 hours
        "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
        "dependencies": ["task1"]
    })
    
    tasks.append({
        "id": "task4",
        "title": "Optimize database queries",
        "description": "Improve performance of database queries",
        "status": "pending",
        "priority": "low",
        "category": "backend",
        "type": "optimization",
        "tags": ["database", "performance"],
        "estimated_time": 240,  # 4 hours
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task5",
        "title": "Write user documentation",
        "description": "Create user documentation for the application",
        "status": "pending",
        "priority": "low",
        "category": "documentation",
        "type": "documentation",
        "tags": ["docs", "user"],
        "estimated_time": 300,  # 5 hours
        "due_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "dependencies": ["task1", "task3"]
    })
    
    tasks.append({
        "id": "task6",
        "title": "Critical security patch",
        "description": "Apply security patch to authentication system",
        "status": "pending",
        "priority": "critical",
        "category": "security",
        "type": "bug",
        "tags": ["security", "authentication"],
        "estimated_time": 90,  # 1.5 hours
        "due_date": (datetime.now() + timedelta(hours=12)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task7",
        "title": "Update dependencies",
        "description": "Update project dependencies to latest versions",
        "status": "pending",
        "priority": "medium",
        "category": "maintenance",
        "type": "maintenance",
        "tags": ["dependencies", "update"],
        "estimated_time": 120,  # 2 hours
        "due_date": (datetime.now() + timedelta(days=4)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task8",
        "title": "Implement dark mode",
        "description": "Add dark mode theme to the application",
        "status": "pending",
        "priority": "medium",
        "category": "frontend",
        "type": "feature",
        "tags": ["ui", "theme"],
        "estimated_time": 180,  # 3 hours
        "due_date": (datetime.now() + timedelta(days=6)).isoformat(),
        "dependencies": ["task2"]
    })
    
    tasks.append({
        "id": "task9",
        "title": "Create unit tests",
        "description": "Write unit tests for core functionality",
        "status": "pending",
        "priority": "high",
        "category": "testing",
        "type": "test",
        "tags": ["test", "quality"],
        "estimated_time": 240,  # 4 hours
        "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
        "dependencies": []
    })
    
    tasks.append({
        "id": "task10",
        "title": "Setup CI/CD pipeline",
        "description": "Configure continuous integration and deployment",
        "status": "pending",
        "priority": "high",
        "category": "devops",
        "type": "infrastructure",
        "tags": ["ci", "cd", "automation"],
        "estimated_time": 300,  # 5 hours
        "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "dependencies": ["task9"]
    })
    
    return tasks


def create_completed_tasks():
    """Create sample completed tasks for historical data."""
    completed_tasks = []
    
    # Create some completed tasks with different attributes
    completed_tasks.append({
        "id": "completed1",
        "title": "Setup project structure",
        "description": "Initialize project and setup basic structure",
        "status": "done",
        "priority": "high",
        "category": "setup",
        "type": "infrastructure",
        "tags": ["setup", "initialization"],
        "estimated_time": 120,  # 2 hours
        "actual_time": 90,  # 1.5 hours
        "completed_at": (datetime.now() - timedelta(days=10)).isoformat()
    })
    
    completed_tasks.append({
        "id": "completed2",
        "title": "Implement authentication service",
        "description": "Create authentication service for user login",
        "status": "done",
        "priority": "high",
        "category": "backend",
        "type": "feature",
        "tags": ["authentication", "security"],
        "estimated_time": 180,  # 3 hours
        "actual_time": 240,  # 4 hours (overestimated)
        "completed_at": (datetime.now() - timedelta(days=8)).isoformat()
    })
    
    completed_tasks.append({
        "id": "completed3",
        "title": "Design database schema",
        "description": "Create database schema for the application",
        "status": "done",
        "priority": "high",
        "category": "backend",
        "type": "design",
        "tags": ["database", "design"],
        "estimated_time": 120,  # 2 hours
        "actual_time": 150,  # 2.5 hours
        "completed_at": (datetime.now() - timedelta(days=7)).isoformat()
    })
    
    completed_tasks.append({
        "id": "completed4",
        "title": "Create UI mockups",
        "description": "Design UI mockups for main screens",
        "status": "done",
        "priority": "medium",
        "category": "design",
        "type": "design",
        "tags": ["ui", "design"],
        "estimated_time": 240,  # 4 hours
        "actual_time": 210,  # 3.5 hours
        "completed_at": (datetime.now() - timedelta(days=6)).isoformat()
    })
    
    completed_tasks.append({
        "id": "completed5",
        "title": "Implement user registration",
        "description": "Create user registration functionality",
        "status": "done",
        "priority": "high",
        "category": "frontend",
        "type": "feature",
        "tags": ["authentication", "ui"],
        "estimated_time": 180,  # 3 hours
        "actual_time": 150,  # 2.5 hours
        "completed_at": (datetime.now() - timedelta(days=5)).isoformat()
    })
    
    return completed_tasks


def create_mock_task_manager(tasks):
    """Create a mock task manager with the given tasks."""
    class MockTaskManager:
        def __init__(self, tasks):
            self.tasks = tasks
        
        def get_all_tasks(self):
            return self.tasks
        
        def get_task(self, task_id):
            for task in self.tasks:
                if task.get("id") == task_id:
                    return task
            return None
    
    return MockTaskManager(tasks)


def create_mock_time_tracking_system():
    """Create a mock time tracking system."""
    class MockTimeTrackingSystem:
        def __init__(self):
            self.time_entries = {}
        
        def get_time_by_task(self, task_id, user_id=None):
            if task_id in self.time_entries:
                return {
                    "success": True,
                    "time_by_task": {
                        task_id: self.time_entries[task_id]
                    }
                }
            return {
                "success": False,
                "time_by_task": {}
            }
        
        def add_time_entry(self, task_id, seconds, user_id=None):
            self.time_entries[task_id] = {
                "seconds": seconds,
                "user_id": user_id
            }
            return True
    
    return MockTimeTrackingSystem()


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))


def main():
    """Main function to test the Task Recommendation System."""
    print_section("Task Recommendation System Test")
    
    # Create sample tasks
    all_tasks = create_sample_tasks()
    completed_tasks = create_completed_tasks()
    
    # Combine all tasks
    combined_tasks = all_tasks + completed_tasks
    
    # Create mock task manager and time tracking system
    task_manager = create_mock_task_manager(combined_tasks)
    time_tracking_system = create_mock_time_tracking_system()
    
    # Add some time entries
    for task in completed_tasks:
        time_tracking_system.add_time_entry(
            task_id=task["id"],
            seconds=task.get("actual_time", 0) * 60,  # Convert minutes to seconds
            user_id="user1"
        )
    
    # Create data directory
    data_dir = os.path.join(os.path.expanduser("~"), ".tascade", "data", "test_recommendation")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create recommendation system
    recommendation_system = TaskRecommendationSystem(
        task_manager=task_manager,
        time_tracking_system=time_tracking_system,
        data_dir=data_dir,
        logger=logger
    )
    
    # Test user preferences
    print_section("Setting User Preferences")
    
    # Set some user preferences
    preference_results = []
    
    preference_results.append(recommendation_system.set_user_preference(
        user_id="user1",
        preference_type="preferred_categories",
        preference_value=["frontend", "backend"],
        weight=0.8
    ))
    
    preference_results.append(recommendation_system.set_user_preference(
        user_id="user1",
        preference_type="preferred_tags",
        preference_value=["ui", "api"],
        weight=0.7
    ))
    
    preference_results.append(recommendation_system.set_user_preference(
        user_id="user1",
        preference_type="preferred_time_of_day",
        preference_value="morning",
        weight=0.6
    ))
    
    for result in preference_results:
        print_json(result)
    
    # Get user preferences
    print_section("Getting User Preferences")
    preferences = recommendation_system.get_user_preferences("user1")
    print_json(preferences)
    
    # Test historical performance
    print_section("Recording Task Completions")
    
    # Record task completions
    completion_results = []
    
    for task in completed_tasks:
        completion_results.append(recommendation_system.record_task_completion(
            user_id="user1",
            task_id=task["id"],
            task_data=task
        ))
    
    for result in completion_results:
        print_json(result)
    
    # Get user performance
    print_section("Getting User Performance")
    performance = recommendation_system.get_user_performance("user1")
    print_json(performance)
    
    # Test workload balancing
    print_section("Setting Workload Settings")
    
    # Set workload settings
    workload_settings_result = recommendation_system.set_workload_settings(
        user_id="user1",
        daily_capacity_minutes=480,  # 8 hours
        max_concurrent_tasks=5,
        preferred_task_size="medium",
        category_limits={
            "frontend": 2,
            "backend": 2,
            "documentation": 1
        },
        priority_weights={
            "critical": 2.0,
            "high": 1.5,
            "medium": 1.0,
            "normal": 0.8,
            "low": 0.5
        }
    )
    
    print_json(workload_settings_result)
    
    # Get workload settings
    print_section("Getting Workload Settings")
    workload_settings = recommendation_system.get_workload_settings("user1")
    print_json(workload_settings)
    
    # Get workload metrics
    print_section("Getting Workload Metrics")
    workload_metrics = recommendation_system.get_workload_metrics("user1", all_tasks)
    print_json(workload_metrics)
    
    # Test task recommendations
    print_section("Getting Task Recommendations")
    recommendations = recommendation_system.recommend_tasks("user1", limit=5)
    print_json(recommendations)
    
    # Test recommendation explanation
    if recommendations["success"] and recommendations["recommendations"]:
        print_section("Explaining Recommendation")
        top_recommendation = recommendations["recommendations"][0]
        task_id = top_recommendation["task"]["id"]
        
        explanation = recommendation_system.explain_recommendation("user1", task_id)
        print_json(explanation)
    
    # Test task completion patterns
    print_section("Getting Task Completion Patterns")
    patterns = recommendation_system.get_task_completion_patterns("user1")
    print_json(patterns)
    
    # Test task completion time prediction
    print_section("Predicting Task Completion Time")
    prediction_results = []
    
    for task in all_tasks[:3]:  # Test with first 3 pending tasks
        prediction_results.append(recommendation_system.predict_task_completion_time(
            user_id="user1",
            task_id=task["id"]
        ))
    
    for result in prediction_results:
        print_json(result)


if __name__ == "__main__":
    main()
