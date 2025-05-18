"""
Task Collaboration System for Tascade AI.

This module provides collaborative task management features including team assignment,
progress sharing, notifications, and collaborative editing.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import uuid
import os
from enum import Enum
from pathlib import Path

from .models import Task, TaskStatus, TaskPriority


class CollaborationRole(Enum):
    """Roles for task collaboration."""
    OWNER = "owner"
    ASSIGNEE = "assignee"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class CollaborationAction(Enum):
    """Actions for collaboration events."""
    ASSIGNED = "assigned"
    UPDATED = "updated"
    COMMENTED = "commented"
    REVIEWED = "reviewed"
    STATUS_CHANGED = "status_changed"
    COMPLETED = "completed"


class Comment:
    """Represents a comment on a task."""
    
    def __init__(self, 
                 id: str,
                 user_id: str,
                 content: str,
                 created_at: datetime,
                 parent_id: Optional[str] = None,
                 edited: bool = False,
                 edited_at: Optional[datetime] = None):
        """
        Initialize a comment.
        
        Args:
            id: Unique identifier for the comment
            user_id: ID of the user who created the comment
            content: Content of the comment
            created_at: When the comment was created
            parent_id: ID of the parent comment if this is a reply
            edited: Whether the comment has been edited
            edited_at: When the comment was last edited
        """
        self.id = id
        self.user_id = user_id
        self.content = content
        self.created_at = created_at
        self.parent_id = parent_id
        self.edited = edited
        self.edited_at = edited_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the comment to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "parent_id": self.parent_id,
            "edited": self.edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """Create a comment from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            content=data.get("content", ""),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now(),
            parent_id=data.get("parent_id"),
            edited=data.get("edited", False),
            edited_at=datetime.fromisoformat(data.get("edited_at")) if data.get("edited_at") else None
        )


class CollaborationEvent:
    """Represents a collaboration event on a task."""
    
    def __init__(self,
                 id: str,
                 task_id: str,
                 user_id: str,
                 action: CollaborationAction,
                 timestamp: datetime,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a collaboration event.
        
        Args:
            id: Unique identifier for the event
            task_id: ID of the task this event is related to
            user_id: ID of the user who triggered the event
            action: Type of action that occurred
            timestamp: When the event occurred
            details: Additional details about the event
        """
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.action = action
        self.timestamp = timestamp
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "action": self.action.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationEvent':
        """Create an event from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            task_id=data.get("task_id", ""),
            user_id=data.get("user_id", ""),
            action=CollaborationAction(data.get("action", "updated")),
            timestamp=datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now(),
            details=data.get("details", {})
        )


class TaskCollaboration:
    """Task Collaboration System for enabling team collaboration on tasks."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Task Collaboration system.
        
        Args:
            data_dir: Optional directory for storing collaboration data
        """
        self.data_dir = data_dir
        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Initialize data files
            self.comments_file = os.path.join(self.data_dir, "comments.json")
            self.events_file = os.path.join(self.data_dir, "events.json")
            self.assignments_file = os.path.join(self.data_dir, "assignments.json")
            
            # Load existing data
            self.comments = self._load_comments()
            self.events = self._load_events()
            self.assignments = self._load_assignments()
        else:
            # In-memory storage
            self.comments = {}  # task_id -> list of comments
            self.events = {}    # task_id -> list of events
            self.assignments = {}  # task_id -> dict of user_id -> role
    
    def assign_task(self, task: Task, user_id: str, 
                   role: CollaborationRole = CollaborationRole.ASSIGNEE) -> Dict[str, Any]:
        """
        Assign a task to a user with a specific role.
        
        Args:
            task: The task to assign
            user_id: ID of the user to assign the task to
            role: Role to assign to the user
            
        Returns:
            Dictionary with assignment information
        """
        task_id = task.id
        
        # Initialize assignments for this task if needed
        if task_id not in self.assignments:
            self.assignments[task_id] = {}
        
        # Add the assignment
        self.assignments[task_id][user_id] = role.value
        
        # Create an event for this assignment
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            action=CollaborationAction.ASSIGNED,
            timestamp=datetime.now(),
            details={"role": role.value}
        )
        
        self._add_event(event)
        
        # Update task's collaboration context
        if not hasattr(task, "collaboration_context") or not task.collaboration_context:
            task.collaboration_context = {}
        
        task.collaboration_context["assignments"] = self.assignments.get(task_id, {})
        
        # Save data
        self._save_data()
        
        return {
            "task_id": task_id,
            "user_id": user_id,
            "role": role.value,
            "timestamp": event.timestamp.isoformat()
        }
    
    def unassign_task(self, task: Task, user_id: str) -> Dict[str, Any]:
        """
        Remove a user's assignment from a task.
        
        Args:
            task: The task to unassign
            user_id: ID of the user to unassign
            
        Returns:
            Dictionary with unassignment information
        """
        task_id = task.id
        
        # Check if the task has assignments
        if task_id not in self.assignments or user_id not in self.assignments[task_id]:
            return {
                "error": f"User {user_id} is not assigned to task {task_id}"
            }
        
        # Get the role before removing
        role = self.assignments[task_id][user_id]
        
        # Remove the assignment
        del self.assignments[task_id][user_id]
        
        # Create an event for this unassignment
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            action=CollaborationAction.UPDATED,
            timestamp=datetime.now(),
            details={"action": "unassigned", "previous_role": role}
        )
        
        self._add_event(event)
        
        # Update task's collaboration context
        if hasattr(task, "collaboration_context") and task.collaboration_context:
            task.collaboration_context["assignments"] = self.assignments.get(task_id, {})
        
        # Save data
        self._save_data()
        
        return {
            "task_id": task_id,
            "user_id": user_id,
            "previous_role": role,
            "timestamp": event.timestamp.isoformat()
        }
    
    def get_task_assignments(self, task_id: str) -> Dict[str, Any]:
        """
        Get all assignments for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary with assignment information
        """
        return {
            "task_id": task_id,
            "assignments": self.assignments.get(task_id, {})
        }
    
    def add_comment(self, task: Task, user_id: str, content: str, 
                   parent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a comment to a task.
        
        Args:
            task: The task to comment on
            user_id: ID of the user adding the comment
            content: Content of the comment
            parent_id: Optional ID of the parent comment if this is a reply
            
        Returns:
            Dictionary with comment information
        """
        task_id = task.id
        
        # Create the comment
        comment = Comment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=content,
            created_at=datetime.now(),
            parent_id=parent_id
        )
        
        # Initialize comments for this task if needed
        if task_id not in self.comments:
            self.comments[task_id] = []
        
        # Add the comment
        self.comments[task_id].append(comment.to_dict())
        
        # Create an event for this comment
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            action=CollaborationAction.COMMENTED,
            timestamp=comment.created_at,
            details={"comment_id": comment.id, "parent_id": parent_id}
        )
        
        self._add_event(event)
        
        # Update task's collaboration context
        if not hasattr(task, "collaboration_context") or not task.collaboration_context:
            task.collaboration_context = {}
        
        if "comments" not in task.collaboration_context:
            task.collaboration_context["comments"] = []
        
        task.collaboration_context["comments"] = self.comments.get(task_id, [])
        
        # Save data
        self._save_data()
        
        return {
            "task_id": task_id,
            "comment": comment.to_dict()
        }
    
    def edit_comment(self, task: Task, comment_id: str, 
                    user_id: str, new_content: str) -> Dict[str, Any]:
        """
        Edit an existing comment.
        
        Args:
            task: The task containing the comment
            comment_id: ID of the comment to edit
            user_id: ID of the user editing the comment
            new_content: New content for the comment
            
        Returns:
            Dictionary with edited comment information
        """
        task_id = task.id
        
        # Check if the task has comments
        if task_id not in self.comments:
            return {"error": f"No comments found for task {task_id}"}
        
        # Find the comment
        comment_found = False
        for i, comment_dict in enumerate(self.comments[task_id]):
            if comment_dict["id"] == comment_id:
                # Check if the user is the comment author
                if comment_dict["user_id"] != user_id:
                    return {"error": "Only the comment author can edit the comment"}
                
                # Update the comment
                comment_dict["content"] = new_content
                comment_dict["edited"] = True
                comment_dict["edited_at"] = datetime.now().isoformat()
                
                comment_found = True
                break
        
        if not comment_found:
            return {"error": f"Comment {comment_id} not found in task {task_id}"}
        
        # Create an event for this edit
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            action=CollaborationAction.UPDATED,
            timestamp=datetime.now(),
            details={"action": "edited_comment", "comment_id": comment_id}
        )
        
        self._add_event(event)
        
        # Update task's collaboration context
        if hasattr(task, "collaboration_context") and task.collaboration_context:
            task.collaboration_context["comments"] = self.comments.get(task_id, [])
        
        # Save data
        self._save_data()
        
        return {
            "task_id": task_id,
            "comment_id": comment_id,
            "edited": True,
            "edited_at": datetime.now().isoformat()
        }
    
    def get_comments(self, task_id: str, 
                    include_replies: bool = True) -> Dict[str, Any]:
        """
        Get all comments for a task.
        
        Args:
            task_id: ID of the task
            include_replies: Whether to include reply comments
            
        Returns:
            Dictionary with comments
        """
        if task_id not in self.comments:
            return {
                "task_id": task_id,
                "comments": []
            }
        
        comments = self.comments[task_id]
        
        if not include_replies:
            # Filter out replies
            comments = [c for c in comments if not c.get("parent_id")]
        
        return {
            "task_id": task_id,
            "comments": comments
        }
    
    def add_review(self, task: Task, user_id: str, status: str, 
                  comments: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a review to a task.
        
        Args:
            task: The task to review
            user_id: ID of the reviewer
            status: Review status (approved, rejected, changes_requested)
            comments: Optional review comments
            
        Returns:
            Dictionary with review information
        """
        task_id = task.id
        
        # Check if the user is a reviewer
        if (task_id in self.assignments and 
            user_id in self.assignments[task_id] and 
            self.assignments[task_id][user_id] == CollaborationRole.REVIEWER.value):
            
            # Create an event for this review
            event = CollaborationEvent(
                id=str(uuid.uuid4()),
                task_id=task_id,
                user_id=user_id,
                action=CollaborationAction.REVIEWED,
                timestamp=datetime.now(),
                details={"status": status, "comments": comments}
            )
            
            self._add_event(event)
            
            # Update task's collaboration context
            if not hasattr(task, "collaboration_context") or not task.collaboration_context:
                task.collaboration_context = {}
            
            if "reviews" not in task.collaboration_context:
                task.collaboration_context["reviews"] = []
            
            review = {
                "user_id": user_id,
                "status": status,
                "comments": comments,
                "timestamp": event.timestamp.isoformat()
            }
            
            task.collaboration_context["reviews"].append(review)
            
            # Save data
            self._save_data()
            
            return {
                "task_id": task_id,
                "review": review
            }
        else:
            return {"error": f"User {user_id} is not a reviewer for task {task_id}"}
    
    def get_activity_feed(self, task_id: Optional[str] = None, 
                         user_id: Optional[str] = None,
                         limit: int = 20) -> Dict[str, Any]:
        """
        Get activity feed for a task or user.
        
        Args:
            task_id: Optional ID of the task to get events for
            user_id: Optional ID of the user to get events for
            limit: Maximum number of events to return
            
        Returns:
            Dictionary with activity feed events
        """
        events = []
        
        if task_id:
            # Get events for a specific task
            events = self.events.get(task_id, [])
        elif user_id:
            # Get events for a specific user across all tasks
            for task_events in self.events.values():
                events.extend([e for e in task_events if e["user_id"] == user_id])
        else:
            # Get all events
            for task_events in self.events.values():
                events.extend(task_events)
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e["timestamp"] if isinstance(e["timestamp"], str) 
                   else e["timestamp"].isoformat(), reverse=True)
        events = events[:limit]
        
        return {
            "task_id": task_id,
            "user_id": user_id,
            "events": events
        }
    
    def _add_event(self, event: CollaborationEvent) -> None:
        """Add an event to the events store."""
        task_id = event.task_id
        
        # Initialize events for this task if needed
        if task_id not in self.events:
            self.events[task_id] = []
        
        # Add the event
        self.events[task_id].append(event.to_dict())
    
    def _load_comments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load comments from the data file."""
        if self.data_dir and os.path.exists(self.comments_file):
            try:
                with open(self.comments_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _load_events(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load events from the data file."""
        if self.data_dir and os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _load_assignments(self) -> Dict[str, Dict[str, str]]:
        """Load assignments from the data file."""
        if self.data_dir and os.path.exists(self.assignments_file):
            try:
                with open(self.assignments_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_data(self) -> None:
        """Save all data to the data files."""
        if not self.data_dir:
            return
        
        try:
            with open(self.comments_file, 'w') as f:
                json.dump(self.comments, f, indent=2)
            
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
            
            with open(self.assignments_file, 'w') as f:
                json.dump(self.assignments, f, indent=2)
        except Exception as e:
            print(f"Error saving collaboration data: {e}")
