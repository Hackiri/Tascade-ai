#!/usr/bin/env python3
"""
Test script for the Task Collaboration System in Tascade AI.

This script demonstrates the new Task Collaboration features:
1. Task Assignment and Role Management
2. Task Comments and Replies
3. Task Reviews
4. Activity Feed and Event Tracking
5. Collaborative Editing

These features enable team collaboration on tasks, improving communication,
tracking, and accountability in project management.
"""

import sys
import os
import json
from datetime import datetime
import time
import uuid

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
    """Test Task Collaboration System in Tascade AI."""
    print_section("Tascade AI Task Collaboration System Demo")
    
    # Initialize TaskManager
    print("Initializing TaskManager...")
    task_manager = TaskManager()
    
    # Create sample users
    print_section("Creating Sample Users")
    users = {
        "user1": {"name": "Alice", "role": "Project Manager"},
        "user2": {"name": "Bob", "role": "Developer"},
        "user3": {"name": "Charlie", "role": "Designer"},
        "user4": {"name": "Diana", "role": "QA Engineer"}
    }
    
    for user_id, user_info in users.items():
        print(f"Created user: {user_id} - {user_info['name']} ({user_info['role']})")
    
    # Create sample tasks
    print_section("Creating Sample Tasks")
    
    # Task 1: Implement User Authentication
    task1 = Task(
        id="task1",
        title="Implement User Authentication",
        description="""
Create a secure authentication system with the following features:
- User registration with email verification
- Login with JWT token-based authentication
- Password reset functionality
- Role-based access control
        """,
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        dependencies=[],
        created_at=datetime.now()
    )
    task_manager.add_task(task1)
    print(f"Created task: {task1.id} - {task1.title}")
    
    # Task 2: Design User Interface
    task2 = Task(
        id="task2",
        title="Design User Interface",
        description="""
Design a modern and user-friendly interface for the authentication system:
- Login and registration screens
- Password reset flow
- User profile page
- Account settings
        """,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        dependencies=[],
        created_at=datetime.now()
    )
    task_manager.add_task(task2)
    print(f"Created task: {task2.id} - {task2.title}")
    
    # Test Task Assignment
    print_section("Task Assignment")
    
    print("Assigning tasks to users with different roles...")
    
    # Assign Task 1 to multiple users with different roles
    assign1 = task_manager.assign_task("task1", "user1", "owner")
    print(f"Assigned {users['user1']['name']} as owner of Task 1")
    
    assign2 = task_manager.assign_task("task1", "user2", "assignee")
    print(f"Assigned {users['user2']['name']} as assignee of Task 1")
    
    assign3 = task_manager.assign_task("task1", "user4", "reviewer")
    print(f"Assigned {users['user4']['name']} as reviewer of Task 1")
    
    # Assign Task 2 to users
    assign4 = task_manager.assign_task("task2", "user1", "owner")
    print(f"Assigned {users['user1']['name']} as owner of Task 2")
    
    assign5 = task_manager.assign_task("task2", "user3", "assignee")
    print(f"Assigned {users['user3']['name']} as assignee of Task 2")
    
    # Get task assignments
    print("\nGetting assignments for Task 1...")
    task1_assignments = task_manager.get_task_assignments("task1")
    
    print("Task 1 Assignments:")
    for user_id, role in task1_assignments["assignments"].items():
        user_name = users[user_id]["name"] if user_id in users else user_id
        print(f"  {user_name}: {role}")
    
    # Test Task Comments
    print_section("Task Comments")
    
    print("Adding comments to Task 1...")
    
    # Add comments from different users
    comment1 = task_manager.add_comment(
        "task1", 
        "user1", 
        "Let's make sure we follow security best practices for the JWT implementation."
    )
    print(f"Comment added by {users['user1']['name']}")
    
    comment2 = task_manager.add_comment(
        "task1", 
        "user2", 
        "I'll start with the user registration and email verification components."
    )
    print(f"Comment added by {users['user2']['name']}")
    
    # Add a reply to a comment
    comment1_id = comment1["comment"]["id"]
    reply1 = task_manager.add_comment(
        "task1", 
        "user4", 
        "We should also consider implementing rate limiting to prevent brute force attacks.",
        parent_id=comment1_id
    )
    print(f"Reply added by {users['user4']['name']} to {users['user1']['name']}'s comment")
    
    # Get all comments for Task 1
    print("\nGetting all comments for Task 1...")
    task1_comments = task_manager.get_comments("task1")
    
    print(f"Task 1 has {len(task1_comments['comments'])} comments/replies")
    for comment in task1_comments["comments"]:
        user_name = users[comment["user_id"]]["name"] if comment["user_id"] in users else comment["user_id"]
        is_reply = "parent_id" in comment and comment["parent_id"]
        prefix = "  └─ Reply" if is_reply else "Comment"
        print(f"{prefix} by {user_name}: {comment['content'][:50]}..." if len(comment['content']) > 50 else f"{prefix} by {user_name}: {comment['content']}")
    
    # Test Comment Editing
    print_section("Comment Editing")
    
    print("Editing a comment...")
    comment2_id = comment2["comment"]["id"]
    edit_result = task_manager.edit_comment(
        "task1",
        comment2_id,
        "user2",
        "I'll start with the user registration and email verification components. I've already set up the basic structure."
    )
    
    if "success" in edit_result and edit_result["success"]:
        print(f"Comment successfully edited by {users['user2']['name']}")
        print(f"Edit timestamp: {edit_result['edited_comment']['edited_at']}")
    else:
        print(f"Error editing comment: {edit_result.get('error', 'Unknown error')}")
    
    # Test Task Reviews
    print_section("Task Reviews")
    
    print("Adding a review to Task 1...")
    
    # Add a review from the reviewer
    review1 = task_manager.add_review(
        "task1",
        "user4",
        "changes_requested",
        "The implementation looks good, but we need to improve error handling for invalid tokens."
    )
    
    if "success" in review1 and review1["success"]:
        print(f"Review added by {users['user4']['name']}")
        print(f"Review status: {review1['review']['status']}")
        print(f"Review comments: {review1['review']['comments']}")
    else:
        print(f"Error adding review: {review1.get('error', 'Unknown error')}")
    
    # Try to add a review from a non-reviewer (should fail)
    review2 = task_manager.add_review(
        "task1",
        "user3",
        "approved",
        "Looks good to me!"
    )
    
    if "error" in review2:
        print(f"\nExpected error when non-reviewer tries to add a review: {review2['error']}")
    
    # Test Activity Feed
    print_section("Activity Feed")
    
    print("Getting activity feed for Task 1...")
    task1_activity = task_manager.get_activity_feed("task1")
    
    print(f"Task 1 has {len(task1_activity['activity_feed'])} activity events")
    print("\nRecent activity:")
    for event in task1_activity["activity_feed"][:5]:  # Show only the 5 most recent events
        user_name = users[event["user_id"]]["name"] if event["user_id"] in users else event["user_id"]
        timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
        print(f"[{timestamp}] {user_name} - {event['action']}")
        
        # Show details for certain event types
        if event["action"] == "commented" and "details" in event and "comment_id" in event["details"]:
            comment_id = event["details"]["comment_id"]
            is_reply = "parent_id" in event["details"] and event["details"]["parent_id"]
            if is_reply:
                print(f"  └─ Added a reply to a comment")
            else:
                print(f"  └─ Added a new comment")
        elif event["action"] == "reviewed" and "details" in event and "status" in event["details"]:
            print(f"  └─ Review status: {event['details']['status']}")
    
    print("\nGetting activity feed for user2...")
    user2_activity = task_manager.get_activity_feed(user_id="user2")
    
    print(f"{users['user2']['name']} has {len(user2_activity['activity_feed'])} activity events")
    for event in user2_activity["activity_feed"]:
        timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
        task_id = event["task_id"]
        print(f"[{timestamp}] Task {task_id} - {event['action']}")
    
    # Test Unassigning
    print_section("Task Unassignment")
    
    print("Unassigning a user from Task 2...")
    unassign_result = task_manager.unassign_task("task2", "user3")
    
    if "success" in unassign_result and unassign_result["success"]:
        print(f"Successfully unassigned {users['user3']['name']} from Task 2")
        print(f"Previous role: {unassign_result['unassignment']['previous_role']}")
    else:
        print(f"Error unassigning user: {unassign_result.get('error', 'Unknown error')}")
    
    # Get updated assignments
    print("\nGetting updated assignments for Task 2...")
    task2_assignments = task_manager.get_task_assignments("task2")
    
    print("Task 2 Assignments:")
    for user_id, role in task2_assignments["assignments"].items():
        user_name = users[user_id]["name"] if user_id in users else user_id
        print(f"  {user_name}: {role}")
    
    print_section("Demo Complete")
    print("The Task Collaboration System has been successfully integrated into Tascade AI.")
    print("This system enables team collaboration on tasks, improving communication,")
    print("tracking, and accountability in project management.")

if __name__ == "__main__":
    main()
