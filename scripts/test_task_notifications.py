#!/usr/bin/env python3
"""
Test script for the Task Notification System in Tascade AI.

This script demonstrates the new Task Notification features:
1. Creating and managing notifications
2. Task event notifications
3. Notification channels
4. Notification filtering and status management
5. Asynchronous notification dispatch

These features enable real-time alerts and updates about task events.
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
from src.core.task_notifications import (
    TaskNotificationSystem, 
    NotificationType, 
    NotificationPriority,
    NotificationStatus,
    NotificationChannel,
    CallbackNotificationChannel
)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test Task Notification System in Tascade AI."""
    print_section("Tascade AI Task Notification System Demo")
    
    # Create data directory
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "notifications")
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize TaskNotificationSystem
    print("Initializing Task Notification System...")
    notification_system = TaskNotificationSystem(data_dir=data_dir)
    
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
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Task 3: API Development
    task3 = Task(
        id="task3",
        title="API Development",
        description="Develop the REST API",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task2"],
        created_at=datetime.now()
    )
    print(f"Created task: {task3.id} - {task3.title}")
    
    # Task 4: Frontend Development with deadline
    task4 = Task(
        id="task4",
        title="Frontend Development",
        description="Develop the frontend",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=["task3"],
        created_at=datetime.now(),
        due_date=datetime.now() - timedelta(days=1)  # Overdue
    )
    print(f"Created task: {task4.id} - {task4.title}")
    
    # Test 1: Basic Notification Creation
    print_section("Basic Notification Creation")
    
    # Create a system notification
    system_notification = notification_system.create_notification(
        type=NotificationType.SYSTEM,
        title="System Maintenance",
        message="System maintenance scheduled for tomorrow",
        priority=NotificationPriority.MEDIUM
    )
    print(f"Created system notification: {system_notification.id}")
    
    # Create a user notification
    user_notification = notification_system.create_notification(
        type=NotificationType.SYSTEM,
        title="Welcome to Tascade AI",
        message="Thank you for using Tascade AI",
        priority=NotificationPriority.LOW,
        user_id="user1"
    )
    print(f"Created user notification: {user_notification.id}")
    
    # Test 2: Task Event Notifications
    print_section("Task Event Notifications")
    
    # Task created notification
    notification_system.create_task_notification(
        task=task1,
        event_type=NotificationType.TASK_CREATED,
        user_id="user1"
    )
    print(f"Created task created notification for {task1.title}")
    
    # Task completed notification
    notification_system.create_task_notification(
        task=task1,
        event_type=NotificationType.TASK_COMPLETED,
        user_id="user1"
    )
    print(f"Created task completed notification for {task1.title}")
    
    # Task assigned notification
    notification_system.create_task_notification(
        task=task2,
        event_type=NotificationType.TASK_ASSIGNED,
        user_id="user2",
        additional_message="Please start working on this as soon as possible."
    )
    print(f"Created task assigned notification for {task2.title}")
    
    # Task commented notification
    notification_system.create_task_notification(
        task=task2,
        event_type=NotificationType.TASK_COMMENTED,
        user_id="user1",
        additional_message="New comment: 'How's the progress on this task?'"
    )
    print(f"Created task commented notification for {task2.title}")
    
    # Task deadline approaching notification
    notification_system.create_task_notification(
        task=task3,
        event_type=NotificationType.TASK_DEADLINE_APPROACHING,
        user_id="user2",
        additional_message="The deadline is in 2 days."
    )
    print(f"Created deadline approaching notification for {task3.title}")
    
    # Task overdue notification
    notification_system.create_task_notification(
        task=task4,
        event_type=NotificationType.TASK_OVERDUE,
        user_id="user2",
        additional_message="This task is now overdue by 1 day."
    )
    print(f"Created overdue notification for {task4.title}")
    
    # Test 3: Custom Notification Channel
    print_section("Custom Notification Channel")
    
    # Define a callback function for notifications
    notification_log = []
    def notification_callback(notification):
        notification_log.append(notification.to_dict())
        print(f"Callback received notification: {notification.title}")
    
    # Register a callback channel
    callback_channel = CallbackNotificationChannel(notification_callback)
    notification_system.register_channel(callback_channel)
    print("Registered callback notification channel")
    
    # Create a notification that will be sent to all channels
    notification_system.create_notification(
        type=NotificationType.SYSTEM,
        title="Important Announcement",
        message="This is an important system announcement",
        priority=NotificationPriority.HIGH
    )
    print("Created notification that should be sent to all channels")
    
    # Give time for async dispatch
    print("Waiting for async dispatch...")
    time.sleep(1)
    
    # Show that the callback was called
    print(f"Callback received {len(notification_log)} notifications")
    
    # Test 4: Notification Filtering and Status Management
    print_section("Notification Filtering and Status Management")
    
    # Get all notifications for user1
    user1_notifications = notification_system.get_notifications(user_id="user1")
    print(f"User1 has {len(user1_notifications)} notifications:")
    for notification in user1_notifications:
        print(f"  - {notification['title']} ({notification['status']})")
    
    # Get all notifications for user2
    user2_notifications = notification_system.get_notifications(user_id="user2")
    print(f"\nUser2 has {len(user2_notifications)} notifications:")
    for notification in user2_notifications:
        print(f"  - {notification['title']} ({notification['status']})")
    
    # Get system notifications
    system_notifications = notification_system.get_notifications()
    print(f"\nSystem has {len(system_notifications)} notifications:")
    for notification in system_notifications:
        print(f"  - {notification['title']} ({notification['status']})")
    
    # Mark a notification as read
    if user1_notifications:
        notification_id = user1_notifications[0]["id"]
        notification_system.mark_notification_as_read(notification_id, "user1")
        print(f"\nMarked notification {notification_id} as read")
    
    # Mark a notification as archived
    if len(user1_notifications) > 1:
        notification_id = user1_notifications[1]["id"]
        notification_system.mark_notification_as_archived(notification_id, "user1")
        print(f"Marked notification {notification_id} as archived")
    
    # Get only unread notifications
    unread_notifications = notification_system.get_notifications(
        user_id="user1", 
        status=NotificationStatus.UNREAD
    )
    print(f"\nUser1 has {len(unread_notifications)} unread notifications:")
    for notification in unread_notifications:
        print(f"  - {notification['title']}")
    
    # Test 5: Notification Priorities
    print_section("Notification Priorities")
    
    # Create notifications with different priorities
    priorities = [
        NotificationPriority.LOW,
        NotificationPriority.MEDIUM,
        NotificationPriority.HIGH,
        NotificationPriority.URGENT
    ]
    
    for priority in priorities:
        notification_system.create_notification(
            type=NotificationType.SYSTEM,
            title=f"{priority.value.capitalize()} Priority Notification",
            message=f"This is a {priority.value} priority notification",
            priority=priority,
            user_id="user3"
        )
        print(f"Created {priority.value} priority notification")
    
    # Get notifications for user3 and sort by priority
    user3_notifications = notification_system.get_notifications(user_id="user3")
    print(f"\nUser3 has {len(user3_notifications)} notifications sorted by creation time (newest first):")
    for notification in user3_notifications:
        print(f"  - {notification['title']} (Priority: {notification['priority']})")
    
    print_section("Demo Complete")
    print("The Task Notification System has been successfully integrated into Tascade AI.")
    print("This system enables real-time alerts and updates about task events.")

if __name__ == "__main__":
    main()
