#!/usr/bin/env python3
"""
Test script for the Task Visualization System in Tascade AI.

This script demonstrates the new Task Visualization features:
1. Gantt Chart Generation
2. Dependency Graph Generation
3. Burndown Chart Generation
4. Status Distribution Charts
5. Priority Distribution Charts
6. Timeline Visualization
7. Dashboard Generation

These features enable visual representation of task data for better project understanding.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import time

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the core modules
from src.core.models import Task, TaskStatus, TaskPriority
from src.core.task_visualization import TaskVisualizationSystem, ChartType

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def main():
    """Test Task Visualization System in Tascade AI."""
    print_section("Tascade AI Task Visualization System Demo")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "visualizations")
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize TaskVisualizationSystem
    print("Initializing Task Visualization System...")
    visualization_system = TaskVisualizationSystem(output_dir=output_dir)
    
    # Create sample tasks with realistic dates
    print_section("Creating Sample Tasks")
    
    # Base date for our sample project
    base_date = datetime.now() - timedelta(days=30)  # Project started 30 days ago
    
    # Task 1: Project Setup (Completed)
    task1 = Task(
        id="task1",
        title="Project Setup",
        description="Set up the project environment",
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=[],
        created_at=base_date,
        started_at=base_date,
        completed_at=base_date + timedelta(days=2)
    )
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Requirements Analysis (Completed)
    task2 = Task(
        id="task2",
        title="Requirements Analysis",
        description="Analyze project requirements",
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=["task1"],
        created_at=base_date,
        started_at=base_date + timedelta(days=2),
        completed_at=base_date + timedelta(days=7)
    )
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Task 3: Database Design (Completed)
    task3 = Task(
        id="task3",
        title="Database Design",
        description="Design the database schema",
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=["task2"],
        created_at=base_date + timedelta(days=7),
        started_at=base_date + timedelta(days=7),
        completed_at=base_date + timedelta(days=12)
    )
    print(f"Created task: {task3.id} - {task3.title}")
    
    # Task 4: API Development (In Progress)
    task4 = Task(
        id="task4",
        title="API Development",
        description="Develop the REST API",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.IN_PROGRESS,
        dependencies=["task3"],
        created_at=base_date + timedelta(days=12),
        started_at=base_date + timedelta(days=12),
        due_date=base_date + timedelta(days=22)
    )
    print(f"Created task: {task4.id} - {task4.title}")
    
    # Task 5: Frontend Development (Pending)
    task5 = Task(
        id="task5",
        title="Frontend Development",
        description="Develop the frontend",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task4"],
        created_at=base_date + timedelta(days=12),
        due_date=base_date + timedelta(days=27)
    )
    print(f"Created task: {task5.id} - {task5.title}")
    
    # Task 6: Testing (Pending)
    task6 = Task(
        id="task6",
        title="Testing",
        description="Test the application",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=["task4", "task5"],
        created_at=base_date + timedelta(days=12),
        due_date=base_date + timedelta(days=32)
    )
    print(f"Created task: {task6.id} - {task6.title}")
    
    # Task 7: Documentation (Pending)
    task7 = Task(
        id="task7",
        title="Documentation",
        description="Create documentation",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        dependencies=["task6"],
        created_at=base_date + timedelta(days=12),
        due_date=base_date + timedelta(days=35)
    )
    print(f"Created task: {task7.id} - {task7.title}")
    
    # Task 8: Deployment (Pending)
    task8 = Task(
        id="task8",
        title="Deployment",
        description="Deploy the application",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=["task6", "task7"],
        created_at=base_date + timedelta(days=12),
        due_date=base_date + timedelta(days=40)
    )
    print(f"Created task: {task8.id} - {task8.title}")
    
    # Collect all tasks
    tasks = [task1, task2, task3, task4, task5, task6, task7, task8]
    
    # Test 1: Gantt Chart
    print_section("Gantt Chart")
    
    gantt_chart = visualization_system.generate_gantt_chart(
        tasks=tasks,
        title="Project Timeline Gantt Chart",
        include_completed=True
    )
    
    print("Generated Gantt Chart:")
    print(gantt_chart)
    print(f"\nGantt chart saved to: {output_dir}")
    
    # Test 2: Dependency Graph
    print_section("Dependency Graph")
    
    dependency_graph = visualization_system.generate_dependency_graph(
        tasks=tasks,
        title="Task Dependencies"
    )
    
    print("Generated Dependency Graph:")
    print(dependency_graph)
    print(f"\nDependency graph saved to: {output_dir}")
    
    # Test 3: Burndown Chart
    print_section("Burndown Chart")
    
    burndown_chart = visualization_system.generate_burndown_chart(
        tasks=tasks,
        start_date=base_date,
        end_date=base_date + timedelta(days=40),
        title="Project Burndown"
    )
    
    print("Generated Burndown Chart:")
    print(burndown_chart)
    print(f"\nBurndown chart saved to: {output_dir}")
    
    # Test 4: Status Distribution
    print_section("Status Distribution")
    
    status_chart = visualization_system.generate_status_distribution(
        tasks=tasks,
        title="Task Status Distribution"
    )
    
    print("Generated Status Distribution Chart:")
    print(status_chart)
    print(f"\nStatus distribution chart saved to: {output_dir}")
    
    # Test 5: Priority Distribution
    print_section("Priority Distribution")
    
    priority_chart = visualization_system.generate_priority_distribution(
        tasks=tasks,
        title="Task Priority Distribution"
    )
    
    print("Generated Priority Distribution Chart:")
    print(priority_chart)
    print(f"\nPriority distribution chart saved to: {output_dir}")
    
    # Test 6: Timeline
    print_section("Timeline")
    
    timeline = visualization_system.generate_timeline(
        tasks=tasks,
        title="Project Timeline"
    )
    
    print("Generated Timeline:")
    print(timeline)
    print(f"\nTimeline saved to: {output_dir}")
    
    # Test 7: Dashboard
    print_section("Dashboard")
    
    dashboard = visualization_system.generate_dashboard(
        tasks=tasks,
        title="Project Dashboard",
        include_charts=[
            ChartType.STATUS_DISTRIBUTION,
            ChartType.PRIORITY_DISTRIBUTION,
            ChartType.GANTT,
            ChartType.DEPENDENCY
        ]
    )
    
    print("Generated Dashboard (excerpt):")
    # Print just the first few lines of the dashboard
    dashboard_lines = dashboard.split('\n')
    for line in dashboard_lines[:20]:
        print(line)
    print("...")
    print(f"\nComplete dashboard saved to: {output_dir}")
    
    print_section("Demo Complete")
    print("The Task Visualization System has been successfully integrated into Tascade AI.")
    print("This system enables visual representation of task data for better project understanding.")
    print(f"All visualizations have been saved to: {output_dir}")

if __name__ == "__main__":
    main()
