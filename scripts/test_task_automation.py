#!/usr/bin/env python3
"""
Test script for the Task Automation System in Tascade AI.

This script demonstrates the new Task Automation features:
1. Creating and managing automation rules
2. Scheduling events
3. Task event handling
4. Recurring task creation
5. Deadline reminders
6. Dependency notifications

These features enable automation of routine task operations and workflows.
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
from src.core.task_manager import TaskManager
from src.core.task_notifications import TaskNotificationSystem
from src.core.task_automation import TaskAutomationSystem

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test Task Automation System in Tascade AI."""
    print_section("Tascade AI Task Automation System Demo")
    
    # Create data directories
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    automation_dir = os.path.join(data_dir, "automation")
    notification_dir = os.path.join(data_dir, "notifications")
    
    os.makedirs(automation_dir, exist_ok=True)
    os.makedirs(notification_dir, exist_ok=True)
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Initialize TaskNotificationSystem
    print("Initializing TaskNotificationSystem...")
    notification_system = TaskNotificationSystem(data_dir=notification_dir)
    
    # Initialize TaskAutomationSystem
    print("Initializing TaskAutomationSystem...")
    automation_system = TaskAutomationSystem(
        task_manager=task_manager,
        notification_system=notification_system,
        data_dir=automation_dir
    )
    
    # Create sample tasks
    print_section("Creating Sample Tasks")
    
    # Task 1: Project Setup
    task1 = Task(
        id="task1",
        title="Project Setup",
        description="Set up the project environment",
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        dependencies=[],
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    task_manager.add_task(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Database Design
    task2 = Task(
        id="task2",
        title="Database Design",
        description="Design the database schema",
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        dependencies=["task1"],
        created_at=datetime.now(),
        started_at=datetime.now()
    )
    task_manager.add_task(task2)
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Task 3: API Development
    task3 = Task(
        id="task3",
        title="API Development",
        description="Develop the REST API",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task2"],
        created_at=datetime.now(),
        due_date=datetime.now() + timedelta(days=7)
    )
    task_manager.add_task(task3)
    print(f"Created task: {task3.id} - {task3.title}")
    
    # Test 1: Creating Automation Rules
    print_section("Creating Automation Rules")
    
    # Rule 1: Send notification when a task is completed
    print("Creating rule: Task Completion Notification")
    rule1_result = automation_system.create_task_status_changed_rule(
        name="Task Completion Notification",
        to_status="done",
        actions=[
            {
                "type": "send_notification",
                "config": {
                    "type": "task_completed",
                    "title": "Task Completed",
                    "message": "The task has been marked as completed",
                    "priority": "medium"
                }
            }
        ]
    )
    print_json(rule1_result)
    
    # Rule 2: Automatically assign high priority tasks
    print("\nCreating rule: Auto-assign High Priority Tasks")
    rule2_result = automation_system.create_rule(
        name="Auto-assign High Priority Tasks",
        description="Automatically assign high priority tasks to the team lead",
        triggers=[
            {
                "type": "task_created",
                "config": {}
            }
        ],
        conditions=[
            {
                "type": "task_priority",
                "config": {
                    "priority": "high",
                    "operator": "eq"
                }
            }
        ],
        actions=[
            {
                "type": "assign_task",
                "config": {
                    "assignee": "team_lead"
                }
            }
        ]
    )
    print_json(rule2_result)
    
    # Rule 3: Send deadline reminder
    print("\nCreating rule: Deadline Reminder")
    rule3_result = automation_system.create_deadline_reminder_rule(
        name="Deadline Reminder - 2 Days",
        days_before=2,
        notification_message="This task is due in 2 days",
        notification_priority="high"
    )
    print_json(rule3_result)
    
    # Test 2: Scheduling Events
    print_section("Scheduling Events")
    
    # Schedule a one-time event
    print("Scheduling a one-time event")
    event1_result = automation_system.schedule_event(
        event_type="scheduled",
        scheduled_time=datetime.now() + timedelta(minutes=1),
        data={
            "message": "This is a scheduled event"
        }
    )
    print_json(event1_result)
    
    # Schedule a recurring event
    print("\nScheduling a recurring event")
    event2_result = automation_system.schedule_event(
        event_type="recurring",
        scheduled_time=datetime.now() + timedelta(minutes=2),
        data={
            "message": "This is a recurring event"
        },
        recurring=True,
        recurrence_config={
            "frequency": "daily",
            "every_days": 1
        }
    )
    print_json(event2_result)
    
    # Test 3: Recurring Task Creation
    print_section("Recurring Task Creation")
    
    # Create a recurring task rule
    print("Creating a recurring task rule")
    recurring_task_result = automation_system.create_recurring_task_rule(
        name="Weekly Status Report",
        frequency="weekly",
        task_template={
            "title": "Weekly Status Report",
            "description": "Prepare the weekly status report",
            "priority": "medium",
            "status": "pending"
        },
        start_time=datetime.now() + timedelta(minutes=3),
        recurrence_config={
            "every_weeks": 1,
            "day_of_week": 0  # Monday
        }
    )
    print_json(recurring_task_result)
    
    # Test 4: Task Event Handling
    print_section("Task Event Handling")
    
    # Trigger a task created event
    print("Triggering a task created event")
    task4 = Task(
        id="task4",
        title="Frontend Development",
        description="Develop the frontend",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        dependencies=["task3"],
        created_at=datetime.now()
    )
    
    event_result = automation_system.handle_task_event(
        event_type="task_created",
        task=task4
    )
    print_json(event_result)
    
    # Add the task to the task manager
    task_manager.add_task(task4)
    print(f"Created task: {task4.id} - {task4.title}")
    
    # Trigger a task status changed event
    print("\nTriggering a task status changed event")
    task2.status = TaskStatus.DONE
    task2.completed_at = datetime.now()
    
    event_result = automation_system.handle_task_event(
        event_type="task_status_changed",
        task=task2,
        additional_data={
            "from_status": "in_progress",
            "to_status": "done"
        }
    )
    print_json(event_result)
    
    # Update the task in the task manager
    task_manager.update_task(task2)
    
    # Test 5: Listing Rules and Events
    print_section("Listing Rules and Events")
    
    # Get all rules
    print("Getting all rules")
    rules_result = automation_system.get_all_rules()
    print(f"Total rules: {rules_result['count']}")
    for rule in rules_result['rules']:
        print(f"- {rule['id']}: {rule['name']} (Enabled: {rule['enabled']})")
    
    # Get all events
    print("\nGetting all events")
    events_result = automation_system.get_all_events()
    print(f"Total events: {events_result['count']}")
    for event in events_result['events']:
        print(f"- {event['id']}: {event['event_type']} (Scheduled: {event['scheduled_time']})")
    
    # Test 6: Manual Rule Triggering
    print_section("Manual Rule Triggering")
    
    # Get the first rule
    if rules_result['count'] > 0:
        rule_id = rules_result['rules'][0]['id']
        print(f"Manually triggering rule: {rule_id}")
        
        trigger_result = automation_system.trigger_rule(
            rule_id=rule_id,
            context={
                "task": task3.__dict__
            }
        )
        print_json(trigger_result)
    
    # Wait for scheduled events
    print_section("Waiting for Scheduled Events")
    print("Waiting for 5 seconds to allow scheduled events to trigger...")
    time.sleep(5)
    
    # Check notifications
    print_section("Checking Notifications")
    
    # Get all notifications
    notifications = notification_system.get_notifications()
    print(f"Total notifications: {len(notifications)}")
    for notification in notifications:
        print(f"- {notification['id']}: {notification['title']} ({notification['status']})")
        print(f"  Message: {notification['message']}")
        print(f"  Created: {notification['created_at']}")
        print()
    
    # Cleanup
    print_section("Cleanup")
    
    # Shutdown the automation system
    print("Shutting down the automation system...")
    automation_system.shutdown()
    
    print_section("Demo Complete")
    print("The Task Automation System has been successfully integrated into Tascade AI.")
    print("This system enables automation of routine task operations and workflows.")

if __name__ == "__main__":
    main()