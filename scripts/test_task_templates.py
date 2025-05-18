#!/usr/bin/env python3
"""
Test script for the Task Template System in Tascade AI.

This script demonstrates the new Task Template features:
1. Template Creation and Management
2. Template Categories and Tags
3. Applying Templates to Create Tasks
4. Creating Templates from Existing Tasks
5. Template Customization

These features enhance productivity by providing standardized starting points
for common task types, ensuring consistency and reducing repetitive work.
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
    """Test Task Template System in Tascade AI."""
    print_section("Tascade AI Task Template System Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample tasks for later use
    print_section("Creating Sample Tasks")
    
    # Task 1: Implement API Endpoint
    task1 = Task(
        id="task1",
        title="Implement REST API Endpoint",
        description="""
Create a new REST API endpoint with the following features:
- GET, POST, PUT, DELETE methods
- JSON request/response handling
- Input validation
- Error handling
- Authentication middleware
- Rate limiting
        """,
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=[],
        created_at=datetime.now(),
        verification_criteria=[
            "Endpoint responds with correct status codes",
            "Input validation rejects invalid data",
            "Authentication works correctly",
            "Rate limiting prevents abuse"
        ]
    )
    
    # Add execution context with implementation guide
    task1.execution_context = {
        "implementation_guide": """
## Implementation Steps

1. Define the route in the router file
2. Create a controller function
3. Add input validation middleware
4. Implement authentication checks
5. Add rate limiting configuration
6. Write error handling logic
7. Implement the business logic
8. Return appropriate responses
"""
    }
    
    task_manager.add_task(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Test Template Creation
    print_section("Template Creation")
    
    print("Creating a new API Endpoint template...")
    api_template = task_manager.create_template(
        name="REST API Endpoint",
        description="Template for creating new REST API endpoints",
        category="Backend Development",
        task_defaults={
            "title": "Implement [Resource] API Endpoint",
            "description": "Create a new REST API endpoint for [Resource] with standard methods",
            "priority": TaskPriority.MEDIUM.value
        },
        subtask_templates=[
            {
                "title": "Define API Routes",
                "description": "Create route definitions in the router file"
            },
            {
                "title": "Implement Controller Functions",
                "description": "Create controller functions for each HTTP method"
            },
            {
                "title": "Add Validation",
                "description": "Implement input validation for the API endpoint"
            },
            {
                "title": "Write Tests",
                "description": "Create unit and integration tests for the endpoint"
            }
        ],
        verification_criteria=[
            "Endpoint responds with correct status codes",
            "Input validation rejects invalid data",
            "Authentication works correctly",
            "Tests pass successfully"
        ],
        implementation_guide="""
## Implementation Guide

1. Define the route in the router file
2. Create controller functions for each HTTP method
3. Add input validation middleware
4. Implement authentication checks
5. Write comprehensive tests
""",
        tags=["api", "backend", "rest"]
    )
    
    if "success" in api_template and api_template["success"]:
        print(f"Successfully created API Endpoint template")
        api_template_id = api_template["template"]["id"]
        print(f"Template ID: {api_template_id}")
    else:
        print(f"Error creating template: {api_template.get('error', 'Unknown error')}")
        return
    
    # Create another template
    print("\nCreating a Bug Fix template...")
    bug_template = task_manager.create_template(
        name="Bug Fix",
        description="Template for bug fix tasks",
        category="Maintenance",
        task_defaults={
            "title": "Fix: [Bug Description]",
            "description": "Fix a bug related to [Feature/Component]",
            "priority": TaskPriority.HIGH.value
        },
        subtask_templates=[
            {
                "title": "Reproduce the Bug",
                "description": "Create a reliable reproduction case for the bug"
            },
            {
                "title": "Identify Root Cause",
                "description": "Debug and identify the root cause of the issue"
            },
            {
                "title": "Implement Fix",
                "description": "Make the necessary code changes to fix the bug"
            },
            {
                "title": "Add Tests",
                "description": "Add tests to prevent regression"
            }
        ],
        verification_criteria=[
            "Bug no longer occurs in the reproduction case",
            "All existing tests pass",
            "New regression tests added",
            "No new bugs introduced"
        ],
        tags=["bug", "fix", "maintenance"]
    )
    
    if "success" in bug_template and bug_template["success"]:
        print(f"Successfully created Bug Fix template")
        bug_template_id = bug_template["template"]["id"]
    else:
        print(f"Error creating template: {bug_template.get('error', 'Unknown error')}")
    
    # Create a template from an existing task
    print("\nCreating a template from an existing task...")
    task_template = task_manager.create_template_from_task(
        task_id="task1",
        name="API Implementation",
        category="Backend Development",
        include_subtasks=True,
        tags=["api", "implementation"]
    )
    
    if "success" in task_template and task_template["success"]:
        print(f"Successfully created template from task")
        task_template_id = task_template["template"]["id"]
    else:
        print(f"Error creating template: {task_template.get('error', 'Unknown error')}")
    
    # Test Template Listing and Filtering
    print_section("Template Listing and Filtering")
    
    print("Listing all templates...")
    all_templates = task_manager.list_templates()
    
    print(f"Found {len(all_templates['templates'])} templates:")
    for template in all_templates["templates"]:
        print(f"  - {template['name']} ({template['category']})")
    
    print("\nListing templates in 'Backend Development' category...")
    backend_templates = task_manager.list_templates(category="Backend Development")
    
    print(f"Found {len(backend_templates['templates'])} Backend Development templates:")
    for template in backend_templates["templates"]:
        print(f"  - {template['name']}")
    
    print("\nListing templates with 'api' tag...")
    api_templates = task_manager.list_templates(tags=["api"])
    
    print(f"Found {len(api_templates['templates'])} templates with 'api' tag:")
    for template in api_templates["templates"]:
        print(f"  - {template['name']}")
    
    # Test Template Categories and Tags
    print_section("Template Categories and Tags")
    
    print("Getting all template categories...")
    categories = task_manager.get_template_categories()
    
    print("Template Categories:")
    for category in categories["categories"]:
        print(f"  - {category}")
    
    print("\nGetting all template tags...")
    tags = task_manager.get_template_tags()
    
    print("Template Tags:")
    for tag in tags["tags"]:
        print(f"  - {tag}")
    
    # Test Applying Templates
    print_section("Applying Templates")
    
    print("Applying the API Endpoint template with custom values...")
    new_task = task_manager.apply_template(
        api_template_id,
        custom_values={
            "title": "Implement User Profile API Endpoint",
            "description": """
Create a new REST API endpoint for user profiles with the following features:
- GET: Retrieve user profile data
- PUT: Update user profile information
- DELETE: Remove user profile (soft delete)
- Authentication required for all operations
- Rate limiting to prevent abuse
            """,
            "priority": TaskPriority.HIGH.value
        }
    )
    
    if "success" in new_task and new_task["success"]:
        print(f"Successfully created task from template: {new_task['task']['title']}")
        print(f"Task ID: {new_task['task']['id']}")
        
        print("\nSubtasks created:")
        for subtask in new_task["subtasks"]:
            print(f"  - {subtask['title']}")
        
        # Get the full task to see all details
        created_task_id = new_task['task']['id']
        full_task = task_manager.get_task(created_task_id)
        
        print("\nVerification criteria added from template:")
        if hasattr(full_task, "verification_criteria") and full_task.verification_criteria:
            for criterion in full_task.verification_criteria:
                print(f"  - {criterion}")
        
        print("\nImplementation guide added from template:")
        if (hasattr(full_task, "execution_context") and full_task.execution_context and 
            "implementation_guide" in full_task.execution_context):
            print("Implementation guide successfully added to task")
    else:
        print(f"Error applying template: {new_task.get('error', 'Unknown error')}")
    
    # Test Template Updates
    print_section("Template Updates")
    
    print("Updating the Bug Fix template...")
    update_result = task_manager.update_template(
        bug_template_id,
        updates={
            "description": "Updated template for bug fix tasks with improved workflow",
            "verification_criteria": [
                "Bug no longer occurs in the reproduction case",
                "All existing tests pass",
                "New regression tests added",
                "No new bugs introduced",
                "Documentation updated if necessary"
            ],
            "tags": ["bug", "fix", "maintenance", "quality"]
        }
    )
    
    if "success" in update_result and update_result["success"]:
        print("Successfully updated Bug Fix template")
        print(f"New description: {update_result['template']['description']}")
        print(f"New tags: {', '.join(update_result['template']['tags'])}")
        print(f"Updated at: {update_result['template']['updated_at']}")
    else:
        print(f"Error updating template: {update_result.get('error', 'Unknown error')}")
    
    # Test Template Deletion
    print_section("Template Deletion")
    
    print("Deleting a template...")
    delete_result = task_manager.delete_template(task_template_id)
    
    if "success" in delete_result and delete_result["success"]:
        print(f"Successfully deleted template: {delete_result['message']}")
    else:
        print(f"Error deleting template: {delete_result.get('error', 'Unknown error')}")
    
    # Verify deletion
    print("\nListing templates after deletion...")
    remaining_templates = task_manager.list_templates()
    
    print(f"Found {len(remaining_templates['templates'])} templates:")
    for template in remaining_templates["templates"]:
        print(f"  - {template['name']} ({template['category']})")
    
    print_section("Demo Complete")
    print("The Task Template System has been successfully integrated into Tascade AI.")
    print("This system enhances productivity by providing standardized starting points")
    print("for common task types, ensuring consistency and reducing repetitive work.")

if __name__ == "__main__":
    main()
