#!/usr/bin/env python3
"""
Test script for the Task Analytics System in Tascade AI.

This script demonstrates the new Task Analytics features:
1. Completion Rate Analysis
2. Duration Metrics
3. Task Distribution Analysis
4. Dependency Metrics
5. Execution Efficiency Analysis
6. Trend Reporting
7. Analytics Export
8. Visualization Data Generation

These features provide comprehensive insights and reporting capabilities
for task data, enabling data-driven project management.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import time
import random

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

def create_sample_tasks(task_manager):
    """Create a set of sample tasks with various statuses, priorities, and dependencies."""
    print("Creating sample tasks...")
    
    # Create tasks with different statuses
    statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.DONE, 
                TaskStatus.PENDING, TaskStatus.DONE, TaskStatus.IN_PROGRESS]
    
    priorities = [TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW,
                  TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
    
    # Base date for task creation (30 days ago)
    base_date = datetime.now() - timedelta(days=30)
    
    tasks = []
    for i in range(1, 21):
        # Vary creation dates across the last 30 days
        days_offset = random.randint(0, 29)
        created_at = base_date + timedelta(days=days_offset)
        
        # For completed tasks, add completion dates
        completed_at = None
        started_at = None
        
        if i <= 6:
            # First 6 tasks use the predefined statuses and priorities
            status = statuses[i-1]
            priority = priorities[i-1]
        else:
            # Remaining tasks get random statuses and priorities
            status = random.choice(list(TaskStatus))
            priority = random.choice(list(TaskPriority))
        
        if status == TaskStatus.IN_PROGRESS or status == TaskStatus.DONE:
            # Started sometime after creation
            started_at = created_at + timedelta(hours=random.randint(1, 24))
            
            if status == TaskStatus.DONE:
                # Completed sometime after starting
                completion_hours = random.randint(2, 72)
                completed_at = started_at + timedelta(hours=completion_hours)
        
        task = Task(
            id=f"task{i}",
            title=f"Sample Task {i}",
            description=f"This is a sample task #{i} for testing analytics",
            status=status,
            priority=priority,
            dependencies=[],
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # Add some execution context for completed tasks
        if status == TaskStatus.DONE:
            execution_duration = (completed_at - started_at).total_seconds()
            task.execution_context = {
                "execution_summary": {
                    "success": True,
                    "duration": execution_duration,
                    "steps_completed": random.randint(3, 8),
                    "total_steps": random.randint(3, 8),
                    "completion_notes": f"Task {i} completed successfully"
                },
                "logs": []
            }
            
            # Add some execution logs
            step_names = ["Analysis", "Design", "Implementation", "Testing", "Documentation"]
            log_time = started_at
            
            for step in step_names[:task.execution_context["execution_summary"]["steps_completed"]]:
                # Log step start
                task.execution_context["logs"].append({
                    "timestamp": log_time.isoformat(),
                    "level": "info",
                    "message": f"Started {step}",
                    "step_name": step,
                    "status": "started"
                })
                
                # Move time forward
                log_time += timedelta(hours=random.randint(1, 8))
                
                # Log step completion
                task.execution_context["logs"].append({
                    "timestamp": log_time.isoformat(),
                    "level": "info",
                    "message": f"Completed {step}",
                    "step_name": step,
                    "status": "completed"
                })
                
                # Move time forward
                log_time += timedelta(hours=random.randint(1, 4))
        
        task_manager.add_task(task)
        tasks.append(task)
    
    # Add some dependencies
    tasks[1].dependencies.append(tasks[0].id)  # Task 2 depends on Task 1
    tasks[3].dependencies.append(tasks[1].id)  # Task 4 depends on Task 2
    tasks[5].dependencies.append(tasks[3].id)  # Task 6 depends on Task 4
    tasks[7].dependencies.append(tasks[5].id)  # Task 8 depends on Task 6
    
    # Add more complex dependencies
    tasks[9].dependencies.append(tasks[8].id)   # Task 10 depends on Task 9
    tasks[10].dependencies.append(tasks[9].id)  # Task 11 depends on Task 10
    tasks[11].dependencies.append(tasks[10].id) # Task 12 depends on Task 11
    
    # Add multiple dependencies
    tasks[15].dependencies.append(tasks[12].id)  # Task 16 depends on Task 13
    tasks[15].dependencies.append(tasks[13].id)  # Task 16 depends on Task 14
    tasks[15].dependencies.append(tasks[14].id)  # Task 16 depends on Task 15
    
    # Update tasks with dependencies
    for task in tasks:
        task_manager.update_task(task)
    
    print(f"Created {len(tasks)} sample tasks with various statuses, priorities, and dependencies")
    return tasks

def main():
    """Test Task Analytics System in Tascade AI."""
    print_section("Tascade AI Task Analytics System Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample tasks
    print_section("Creating Sample Tasks")
    create_sample_tasks(task_manager)
    
    # Test Completion Rate Analysis
    print_section("Completion Rate Analysis")
    
    print("Getting completion rate for all time...")
    completion_rate = task_manager.get_completion_rate("all")
    print(f"Overall Completion Rate: {completion_rate['completion_rate']['completion_rate']}%")
    print(f"Total Tasks: {completion_rate['completion_rate']['total_tasks']}")
    print(f"Completed Tasks: {completion_rate['completion_rate']['completed_tasks']}")
    print(f"In Progress Tasks: {completion_rate['completion_rate']['in_progress_tasks']}")
    print(f"Pending Tasks: {completion_rate['completion_rate']['pending_tasks']}")
    
    print("\nGetting completion rate for last week...")
    weekly_completion_rate = task_manager.get_completion_rate("week")
    print(f"Weekly Completion Rate: {weekly_completion_rate['completion_rate']['completion_rate']}%")
    
    # Test Duration Metrics
    print_section("Duration Metrics")
    
    duration_metrics = task_manager.get_duration_metrics()
    print(f"Average Duration: {duration_metrics['duration_metrics']['average_duration_hours']} hours")
    print(f"Median Duration: {duration_metrics['duration_metrics']['median_duration_hours']} hours")
    print(f"Min Duration: {duration_metrics['duration_metrics']['min_duration_hours']} hours")
    print(f"Max Duration: {duration_metrics['duration_metrics']['max_duration_hours']} hours")
    print(f"Tasks Analyzed: {duration_metrics['duration_metrics']['total_tasks_analyzed']}")
    
    # Test Task Distribution Analysis
    print_section("Task Distribution Analysis")
    
    distribution = task_manager.get_task_distribution()
    
    print("Status Distribution:")
    for status, count in distribution['distribution']['status_distribution'].items():
        print(f"  {status}: {count} tasks")
    
    print("\nPriority Distribution:")
    for priority, count in distribution['distribution']['priority_distribution'].items():
        print(f"  {priority}: {count} tasks")
    
    print("\nDependency Distribution:")
    for dep_category, count in distribution['distribution']['dependency_distribution'].items():
        print(f"  {dep_category}: {count} tasks")
    
    # Test Dependency Metrics
    print_section("Dependency Metrics")
    
    dependency_metrics = task_manager.get_dependency_metrics()
    print(f"Average Dependency Depth: {dependency_metrics['dependency_metrics']['average_dependency_depth']}")
    print(f"Max Dependency Depth: {dependency_metrics['dependency_metrics']['max_dependency_depth']}")
    print(f"Tasks with Dependencies: {dependency_metrics['dependency_metrics']['tasks_with_dependencies']}")
    print(f"Total Dependencies: {dependency_metrics['dependency_metrics']['total_dependencies']}")
    
    # Test Execution Efficiency Analysis
    print_section("Execution Efficiency Analysis")
    
    efficiency_metrics = task_manager.get_execution_efficiency()
    print(f"Average Steps per Task: {efficiency_metrics['execution_efficiency']['average_steps_per_task']}")
    print(f"Average Execution Time: {efficiency_metrics['execution_efficiency']['average_execution_time_hours']} hours")
    print(f"Execution Success Rate: {efficiency_metrics['execution_efficiency']['execution_success_rate']}%")
    print(f"Tasks Analyzed: {efficiency_metrics['execution_efficiency']['tasks_analyzed']}")
    
    # Test Trend Reporting
    print_section("Trend Reporting")
    
    print("Generating trend report for completion rate...")
    trend_report = task_manager.generate_trend_report(
        "completion_rate", 
        ["day", "week", "month", "all"]
    )
    
    print("Completion Rate Trends:")
    for data_point in trend_report['trend_report']['trend_data']:
        print(f"  {data_point['timeframe']}: {data_point['value']}%")
    
    # Test Analytics Export
    print_section("Analytics Export")
    
    print("Exporting analytics report as JSON...")
    export_dir = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
    os.makedirs(export_dir, exist_ok=True)
    
    json_path = os.path.join(export_dir, "analytics_report.json")
    json_report = task_manager.export_analytics_report("json", json_path)
    print(json_report['report'])
    
    print("\nExporting analytics report as CSV...")
    csv_path = os.path.join(export_dir, "analytics_report.csv")
    csv_report = task_manager.export_analytics_report("csv", csv_path)
    print(f"CSV report saved to: {csv_path}")
    
    # Test Visualization Data Generation
    print_section("Visualization Data Generation")
    
    print("Generating Gantt chart data...")
    gantt_data = task_manager.generate_visualization_data("gantt")
    print(f"Generated Gantt data for {len(gantt_data['visualization_data']['data'])} tasks")
    
    print("\nGenerating Burndown chart data...")
    burndown_data = task_manager.generate_visualization_data("burndown")
    print(f"Generated Burndown data with {len(burndown_data['visualization_data']['data'])} data points")
    
    print("\nGenerating Pie chart data...")
    pie_data = task_manager.generate_visualization_data("pie")
    print("Status Distribution:")
    for item in pie_data['visualization_data']['status_data']:
        print(f"  {item['label']}: {item['value']}")
    
    print("\nGenerating Bar chart data...")
    bar_data = task_manager.generate_visualization_data("bar")
    print("Dependency Distribution:")
    for item in bar_data['visualization_data']['dependency_data']:
        print(f"  {item['label']} dependencies: {item['value']} tasks")
    
    print_section("Demo Complete")
    print("The Task Analytics System has been successfully integrated into Tascade AI.")
    print("This system provides comprehensive insights and reporting capabilities")
    print("for task data, enabling data-driven project management.")

if __name__ == "__main__":
    main()
