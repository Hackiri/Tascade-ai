#!/usr/bin/env python3
"""
Test script for the Task Import/Export System in Tascade AI.

This script demonstrates the new Task Import/Export features:
1. Exporting Tasks to Various Formats
2. Importing Tasks from Various Formats
3. Format Conversion
4. Selective Export
5. Merge Importing

These features enable data portability and integration with external tools and systems.
"""

import sys
import os
import json
from datetime import datetime
import time
import shutil

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
    """Test Task Import/Export System in Tascade AI."""
    print_section("Tascade AI Task Import/Export System Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample tasks
    print_section("Creating Sample Tasks")
    
    # Create a set of sample tasks with different statuses, priorities, and dependencies
    tasks = []
    
    # Task 1: Project Setup
    task1 = Task(
        id="task1",
        title="Project Setup",
        description="""
Set up the project environment with:
- Repository initialization
- Dependency management
- CI/CD configuration
- Development environment setup
        """,
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=[],
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    task_manager.add_task(task1)
    tasks.append(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Database Design
    task2 = Task(
        id="task2",
        title="Database Design",
        description="""
Design the database schema:
- Define tables and relationships
- Create migration scripts
- Set up test data
- Document schema
        """,
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=["task1"],
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    task_manager.add_task(task2)
    tasks.append(task2)
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Task 3: API Development
    task3 = Task(
        id="task3",
        title="API Development",
        description="""
Develop the REST API:
- Define endpoints
- Implement controllers
- Add authentication
- Write tests
        """,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.IN_PROGRESS,
        dependencies=["task2"],
        created_at=datetime.now(),
        started_at=datetime.now()
    )
    task_manager.add_task(task3)
    tasks.append(task3)
    print(f"Created task: {task3.id} - {task3.title}")
    
    # Task 4: Frontend Development
    task4 = Task(
        id="task4",
        title="Frontend Development",
        description="""
Develop the frontend:
- Set up framework
- Create components
- Implement state management
- Connect to API
        """,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task3"],
        created_at=datetime.now()
    )
    task_manager.add_task(task4)
    tasks.append(task4)
    print(f"Created task: {task4.id} - {task4.title}")
    
    # Task 5: Deployment
    task5 = Task(
        id="task5",
        title="Deployment",
        description="""
Deploy the application:
- Configure servers
- Set up monitoring
- Deploy application
- Perform smoke tests
        """,
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        dependencies=["task3", "task4"],
        created_at=datetime.now()
    )
    task_manager.add_task(task5)
    tasks.append(task5)
    print(f"Created task: {task5.id} - {task5.title}")
    
    # Add verification criteria and execution context to some tasks
    task3.verification_criteria = [
        "All endpoints return correct responses",
        "Authentication works properly",
        "All tests pass",
        "API documentation is complete"
    ]
    
    task3.execution_context = {
        "implementation_guide": """
## Implementation Steps

1. Define API routes
2. Implement controllers
3. Add authentication middleware
4. Write unit tests
5. Create integration tests
6. Generate API documentation
        """
    }
    
    # Update task with additional data
    task_manager.update_task(task3)
    
    # Create export directory
    export_dir = os.path.join(os.path.dirname(__file__), "..", "data", "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    # Get supported formats
    print_section("Supported Formats")
    
    formats = task_manager.get_supported_formats()
    print("Supported import/export formats:")
    for format in formats["formats"]:
        print(f"  - {format}")
    
    # Test Task Export
    print_section("Task Export")
    
    # Export to JSON
    json_path = os.path.join(export_dir, "tasks.json")
    print(f"Exporting all tasks to JSON: {json_path}")
    json_result = task_manager.export_tasks(json_path, "json")
    
    if "success" in json_result and json_result["success"]:
        print(f"Successfully exported {len(tasks)} tasks to JSON")
    else:
        print(f"Error exporting to JSON: {json_result.get('error', 'Unknown error')}")
    
    # Export to CSV
    csv_path = os.path.join(export_dir, "tasks.csv")
    print(f"\nExporting all tasks to CSV: {csv_path}")
    csv_result = task_manager.export_tasks(csv_path, "csv")
    
    if "success" in csv_result and csv_result["success"]:
        print(f"Successfully exported {len(tasks)} tasks to CSV")
    else:
        print(f"Error exporting to CSV: {csv_result.get('error', 'Unknown error')}")
    
    # Export to YAML
    yaml_path = os.path.join(export_dir, "tasks.yaml")
    print(f"\nExporting all tasks to YAML: {yaml_path}")
    yaml_result = task_manager.export_tasks(yaml_path, "yaml")
    
    if "success" in yaml_result and yaml_result["success"]:
        print(f"Successfully exported {len(tasks)} tasks to YAML")
    else:
        print(f"Error exporting to YAML: {yaml_result.get('error', 'Unknown error')}")
    
    # Export to XML
    xml_path = os.path.join(export_dir, "tasks.xml")
    print(f"\nExporting all tasks to XML: {xml_path}")
    xml_result = task_manager.export_tasks(xml_path, "xml")
    
    if "success" in xml_result and xml_result["success"]:
        print(f"Successfully exported {len(tasks)} tasks to XML")
    else:
        print(f"Error exporting to XML: {xml_result.get('error', 'Unknown error')}")
    
    # Export to Markdown
    md_path = os.path.join(export_dir, "tasks.md")
    print(f"\nExporting all tasks to Markdown: {md_path}")
    md_result = task_manager.export_tasks(md_path, "markdown")
    
    if "success" in md_result and md_result["success"]:
        print(f"Successfully exported {len(tasks)} tasks to Markdown")
    else:
        print(f"Error exporting to Markdown: {md_result.get('error', 'Unknown error')}")
    
    # Test Selective Export
    print_section("Selective Export")
    
    # Export only in-progress tasks
    in_progress_path = os.path.join(export_dir, "in_progress_tasks.json")
    print(f"Exporting only in-progress tasks: {in_progress_path}")
    in_progress_result = task_manager.export_tasks(
        in_progress_path, 
        "json",
        task_ids=["task3"]  # Only task3 is in progress
    )
    
    if "success" in in_progress_result and in_progress_result["success"]:
        print(f"Successfully exported in-progress tasks")
    else:
        print(f"Error exporting in-progress tasks: {in_progress_result.get('error', 'Unknown error')}")
    
    # Test Format Conversion
    print_section("Format Conversion")
    
    # Convert JSON to YAML
    print("Converting JSON to YAML...")
    
    with open(json_path, 'r') as f:
        json_content = f.read()
    
    conversion_result = task_manager.convert_format(json_content, "json", "yaml")
    
    if "success" in conversion_result and conversion_result["success"]:
        print("Successfully converted JSON to YAML")
        print("\nSample of converted YAML content:")
        yaml_lines = conversion_result["converted_content"].split('\n')
        for line in yaml_lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        print("  ...")
    else:
        print(f"Error converting format: {conversion_result.get('error', 'Unknown error')}")
    
    # Test Task Import
    print_section("Task Import")
    
    # Create a new task manager for import testing
    import_manager = TaskManager()
    
    # Import from JSON
    print("Importing tasks from JSON...")
    json_import_result = import_manager.import_tasks(json_path)
    
    if "success" in json_import_result and json_import_result["success"]:
        print(f"Successfully imported {len(json_import_result['imported_tasks'])} tasks from JSON")
        
        # List imported tasks
        print("\nImported tasks:")
        for task in import_manager.get_all_tasks()["tasks"]:
            print(f"  - {task['id']}: {task['title']} ({task['status']})")
    else:
        print(f"Error importing from JSON: {json_import_result.get('error', 'Unknown error')}")
    
    # Test Merge Import
    print_section("Merge Import")
    
    # Create a new task for the original manager
    new_task = Task(
        id="task6",
        title="Documentation",
        description="Create comprehensive documentation for the project",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task5"],
        created_at=datetime.now()
    )
    task_manager.add_task(new_task)
    print(f"Added new task to original manager: {new_task.id} - {new_task.title}")
    
    # Export the new task set
    merge_export_path = os.path.join(export_dir, "merge_tasks.json")
    task_manager.export_tasks(merge_export_path)
    
    # Import with merge
    print("\nImporting tasks with merge...")
    merge_import_result = import_manager.import_tasks(merge_export_path, merge=True)
    
    if "success" in merge_import_result and merge_import_result["success"]:
        print(f"Successfully merged {len(merge_import_result['imported_tasks'])} tasks")
        
        # List all tasks after merge
        print("\nTasks after merge:")
        for task in import_manager.get_all_tasks()["tasks"]:
            print(f"  - {task['id']}: {task['title']} ({task['status']})")
    else:
        print(f"Error merging tasks: {merge_import_result.get('error', 'Unknown error')}")
    
    # Test Import from Different Formats
    print_section("Import from Different Formats")
    
    # Create a new task manager for each format
    formats_to_test = ["csv", "yaml", "xml", "markdown"]
    
    for format in formats_to_test:
        format_manager = TaskManager()
        format_path = os.path.join(export_dir, f"tasks.{format if format != 'yaml' else 'yaml'}")
        
        print(f"Importing from {format.upper()}...")
        format_result = format_manager.import_tasks(format_path, format)
        
        if "success" in format_result and format_result["success"]:
            print(f"Successfully imported {len(format_result['imported_tasks'])} tasks from {format.upper()}")
            
            # Count tasks by status
            statuses = {}
            for task in format_manager.get_all_tasks()["tasks"]:
                status = task["status"]
                if status not in statuses:
                    statuses[status] = 0
                statuses[status] += 1
            
            print(f"  Task status breakdown:")
            for status, count in statuses.items():
                print(f"    {status}: {count} tasks")
        else:
            print(f"Error importing from {format.upper()}: {format_result.get('error', 'Unknown error')}")
    
    print_section("Demo Complete")
    print("The Task Import/Export System has been successfully integrated into Tascade AI.")
    print("This system enables data portability and integration with external tools and systems.")

if __name__ == "__main__":
    main()
