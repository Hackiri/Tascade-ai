"""
Task Notification System for Tascade AI.

This module provides functionality for generating, managing, and delivering
notifications related to task events and updates.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json
import uuid
import os
from enum import Enum
from pathlib import Path
import time
import threading
import queue

from .models import Task, TaskStatus


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """Types of notifications."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    TASK_COMMENTED = "task_commented"
    TASK_REVIEWED = "task_reviewed"
    TASK_DEPENDENCY_ADDED = "task_dependency_added"
    TASK_DEPENDENCY_REMOVED = "task_dependency_removed"
    TASK_DEADLINE_APPROACHING = "task_deadline_approaching"
    TASK_OVERDUE = "task_overdue"
    TASK_BLOCKED = "task_blocked"
    TASK_UNBLOCKED = "task_unblocked"
    SYSTEM = "system"


class NotificationStatus(Enum):
    """Status of a notification."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Notification:
    """Represents a notification."""
    
    def __init__(self, 
                 id: str,
                 type: NotificationType,
                 title: str,
                 message: str,
                 created_at: datetime,
                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                 status: NotificationStatus = NotificationStatus.UNREAD,
                 user_id: Optional[str] = None,
                 task_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 actions: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize a notification.
        
        Args:
            id: Unique identifier for the notification
            type: Type of notification
            title: Title of the notification
            message: Message content
            created_at: When the notification was created
            priority: Priority level
            status: Status of the notification
            user_id: ID of the user the notification is for
            task_id: ID of the related task
            metadata: Additional metadata
            actions: Available actions for this notification
        """
        self.id = id
        self.type = type
        self.title = title
        self.message = message
        self.created_at = created_at
        self.priority = priority
        self.status = status
        self.user_id = user_id
        self.task_id = task_id
        self.metadata = metadata or {}
        self.actions = actions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the notification to a dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "priority": self.priority.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "metadata": self.metadata,
            "actions": self.actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create a notification from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=NotificationType(data.get("type", "system")),
            title=data.get("title", ""),
            message=data.get("message", ""),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now(),
            priority=NotificationPriority(data.get("priority", "medium")),
            status=NotificationStatus(data.get("status", "unread")),
            user_id=data.get("user_id"),
            task_id=data.get("task_id"),
            metadata=data.get("metadata", {}),
            actions=data.get("actions", [])
        )


class NotificationChannel:
    """Base class for notification delivery channels."""
    
    def __init__(self, name: str):
        """
        Initialize a notification channel.
        
        Args:
            name: Name of the channel
        """
        self.name = name
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification through this channel.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if the notification was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")


class ConsoleNotificationChannel(NotificationChannel):
    """Notification channel that prints to the console."""
    
    def __init__(self):
        """Initialize a console notification channel."""
        super().__init__("console")
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification to the console.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if the notification was sent successfully
        """
        priority_markers = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "🔔",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.URGENT: "🚨"
        }
        
        marker = priority_markers.get(notification.priority, "🔔")
        
        print(f"\n{marker} NOTIFICATION: {notification.title}")
        print(f"Type: {notification.type.value}")
        print(f"Message: {notification.message}")
        if notification.task_id:
            print(f"Task ID: {notification.task_id}")
        if notification.user_id:
            print(f"User ID: {notification.user_id}")
        print(f"Priority: {notification.priority.value}")
        print(f"Created at: {notification.created_at.isoformat()}")
        
        return True


class FileNotificationChannel(NotificationChannel):
    """Notification channel that writes to a file."""
    
    def __init__(self, file_path: str):
        """
        Initialize a file notification channel.
        
        Args:
            file_path: Path to the file to write notifications to
        """
        super().__init__("file")
        self.file_path = file_path
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification to a file.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if the notification was written successfully
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Append to file
            with open(self.file_path, 'a') as f:
                f.write(f"[{notification.created_at.isoformat()}] {notification.priority.value.upper()}: {notification.title}\n")
                f.write(f"Type: {notification.type.value}\n")
                f.write(f"Message: {notification.message}\n")
                if notification.task_id:
                    f.write(f"Task ID: {notification.task_id}\n")
                if notification.user_id:
                    f.write(f"User ID: {notification.user_id}\n")
                f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error writing notification to file: {e}")
            return False


class CallbackNotificationChannel(NotificationChannel):
    """Notification channel that calls a callback function."""
    
    def __init__(self, callback: Callable[[Notification], None]):
        """
        Initialize a callback notification channel.
        
        Args:
            callback: Function to call with the notification
        """
        super().__init__("callback")
        self.callback = callback
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification via callback.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if the callback was called successfully
        """
        try:
            self.callback(notification)
            return True
        except Exception as e:
            print(f"Error calling notification callback: {e}")
            return False


class NotificationDispatcher:
    """Dispatches notifications to registered channels."""
    
    def __init__(self):
        """Initialize a notification dispatcher."""
        self.channels = {}
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
    
    def register_channel(self, channel: NotificationChannel) -> None:
        """
        Register a notification channel.
        
        Args:
            channel: The channel to register
        """
        self.channels[channel.name] = channel
    
    def unregister_channel(self, channel_name: str) -> None:
        """
        Unregister a notification channel.
        
        Args:
            channel_name: Name of the channel to unregister
        """
        if channel_name in self.channels:
            del self.channels[channel_name]
    
    def dispatch(self, notification: Notification, 
                channel_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Dispatch a notification to specified channels.
        
        Args:
            notification: The notification to dispatch
            channel_names: Names of channels to dispatch to
                          If None, dispatch to all registered channels
            
        Returns:
            Dictionary mapping channel names to success status
        """
        if channel_names is None:
            channel_names = list(self.channels.keys())
        
        results = {}
        
        for name in channel_names:
            if name in self.channels:
                results[name] = self.channels[name].send(notification)
            else:
                results[name] = False
        
        return results
    
    def queue_notification(self, notification: Notification) -> None:
        """
        Queue a notification for asynchronous dispatch.
        
        Args:
            notification: The notification to queue
        """
        self.queue.put(notification)
    
    def start_dispatcher(self) -> None:
        """Start the asynchronous notification dispatcher."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._dispatcher_thread, daemon=True)
        self.thread.start()
    
    def stop_dispatcher(self) -> None:
        """Stop the asynchronous notification dispatcher."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _dispatcher_thread(self) -> None:
        """Thread function for asynchronous notification dispatch."""
        while self.running:
            try:
                # Get notification from queue with timeout
                notification = self.queue.get(timeout=1.0)
                
                # Dispatch to all channels
                self.dispatch(notification)
                
                # Mark as done
                self.queue.task_done()
            except queue.Empty:
                # No notifications in queue, continue waiting
                continue
            except Exception as e:
                print(f"Error in notification dispatcher thread: {e}")


class TaskNotificationSystem:
    """Task Notification System for generating and managing task notifications."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Task Notification system.
        
        Args:
            data_dir: Optional directory for storing notification data
        """
        self.data_dir = data_dir
        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
            self.notifications_file = os.path.join(self.data_dir, "notifications.json")
            self.notifications = self._load_notifications()
        else:
            # In-memory storage
            self.notifications = {}  # user_id -> list of notifications
        
        # Initialize dispatcher
        self.dispatcher = NotificationDispatcher()
        
        # Register default channels
        self.dispatcher.register_channel(ConsoleNotificationChannel())
        
        if self.data_dir:
            log_file = os.path.join(self.data_dir, "notifications.log")
            self.dispatcher.register_channel(FileNotificationChannel(log_file))
        
        # Start dispatcher
        self.dispatcher.start_dispatcher()
    
    def create_notification(self, 
                           type: Union[NotificationType, str],
                           title: str,
                           message: str,
                           priority: Union[NotificationPriority, str] = NotificationPriority.MEDIUM,
                           user_id: Optional[str] = None,
                           task_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           actions: Optional[List[Dict[str, Any]]] = None,
                           dispatch: bool = True) -> Notification:
        """
        Create a new notification.
        
        Args:
            type: Type of notification
            title: Title of the notification
            message: Message content
            priority: Priority level
            user_id: ID of the user the notification is for
            task_id: ID of the related task
            metadata: Additional metadata
            actions: Available actions for this notification
            dispatch: Whether to dispatch the notification immediately
            
        Returns:
            The created notification
        """
        # Convert string types to enums if necessary
        if isinstance(type, str):
            type = NotificationType(type)
        
        if isinstance(priority, str):
            priority = NotificationPriority(priority)
        
        # Create notification
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            title=title,
            message=message,
            created_at=datetime.now(),
            priority=priority,
            status=NotificationStatus.UNREAD,
            user_id=user_id,
            task_id=task_id,
            metadata=metadata,
            actions=actions
        )
        
        # Store notification
        if user_id:
            if user_id not in self.notifications:
                self.notifications[user_id] = []
            
            self.notifications[user_id].append(notification.to_dict())
        else:
            # System notifications without a user
            if "system" not in self.notifications:
                self.notifications["system"] = []
            
            self.notifications["system"].append(notification.to_dict())
        
        # Save notifications
        self._save_notifications()
        
        # Dispatch if requested
        if dispatch:
            self.dispatcher.queue_notification(notification)
        
        return notification
    
    def create_task_notification(self, task: Task, 
                               event_type: Union[NotificationType, str],
                               user_id: Optional[str] = None,
                               additional_message: Optional[str] = None) -> Notification:
        """
        Create a notification for a task event.
        
        Args:
            task: The task related to the notification
            event_type: Type of task event
            user_id: ID of the user the notification is for
            additional_message: Optional additional message
            
        Returns:
            The created notification
        """
        # Convert string type to enum if necessary
        if isinstance(event_type, str):
            event_type = NotificationType(event_type)
        
        # Determine title and message based on event type
        title = f"Task: {task.title}"
        message = ""
        priority = NotificationPriority.MEDIUM
        
        if event_type == NotificationType.TASK_CREATED:
            title = f"New Task Created: {task.title}"
            message = f"A new task has been created: {task.title}"
        
        elif event_type == NotificationType.TASK_UPDATED:
            title = f"Task Updated: {task.title}"
            message = f"Task '{task.title}' has been updated"
        
        elif event_type == NotificationType.TASK_COMPLETED:
            title = f"Task Completed: {task.title}"
            message = f"Task '{task.title}' has been marked as completed"
        
        elif event_type == NotificationType.TASK_ASSIGNED:
            title = f"Task Assigned: {task.title}"
            message = f"You have been assigned to task '{task.title}'"
        
        elif event_type == NotificationType.TASK_UNASSIGNED:
            title = f"Task Unassigned: {task.title}"
            message = f"You have been unassigned from task '{task.title}'"
        
        elif event_type == NotificationType.TASK_COMMENTED:
            title = f"New Comment on Task: {task.title}"
            message = f"A new comment has been added to task '{task.title}'"
        
        elif event_type == NotificationType.TASK_REVIEWED:
            title = f"Task Reviewed: {task.title}"
            message = f"Task '{task.title}' has been reviewed"
        
        elif event_type == NotificationType.TASK_DEPENDENCY_ADDED:
            title = f"Dependency Added: {task.title}"
            message = f"A new dependency has been added to task '{task.title}'"
        
        elif event_type == NotificationType.TASK_DEPENDENCY_REMOVED:
            title = f"Dependency Removed: {task.title}"
            message = f"A dependency has been removed from task '{task.title}'"
        
        elif event_type == NotificationType.TASK_DEADLINE_APPROACHING:
            title = f"Deadline Approaching: {task.title}"
            message = f"The deadline for task '{task.title}' is approaching"
            priority = NotificationPriority.HIGH
        
        elif event_type == NotificationType.TASK_OVERDUE:
            title = f"Task Overdue: {task.title}"
            message = f"Task '{task.title}' is overdue"
            priority = NotificationPriority.URGENT
        
        elif event_type == NotificationType.TASK_BLOCKED:
            title = f"Task Blocked: {task.title}"
            message = f"Task '{task.title}' is blocked by dependencies"
            priority = NotificationPriority.HIGH
        
        elif event_type == NotificationType.TASK_UNBLOCKED:
            title = f"Task Unblocked: {task.title}"
            message = f"Task '{task.title}' is no longer blocked"
        
        # Add additional message if provided
        if additional_message:
            message += f"\n{additional_message}"
        
        # Create metadata
        metadata = {
            "task_title": task.title,
            "task_status": task.status.value if hasattr(task, "status") else None,
            "task_priority": task.priority.value if hasattr(task, "priority") else None
        }
        
        # Create notification
        return self.create_notification(
            type=event_type,
            title=title,
            message=message,
            priority=priority,
            user_id=user_id,
            task_id=task.id,
            metadata=metadata
        )
    
    def get_notifications(self, user_id: Optional[str] = None, 
                        status: Optional[Union[NotificationStatus, str]] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user to get notifications for
                   If None, get system notifications
            status: Filter by notification status
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification dictionaries
        """
        # Determine which notifications to get
        if user_id:
            notifications = self.notifications.get(user_id, [])
        else:
            notifications = self.notifications.get("system", [])
        
        # Filter by status if specified
        if status:
            if isinstance(status, str):
                status = NotificationStatus(status)
            
            notifications = [n for n in notifications if NotificationStatus(n["status"]) == status]
        
        # Sort by created_at (newest first)
        notifications.sort(key=lambda n: n["created_at"], reverse=True)
        
        # Limit the number of notifications
        return notifications[:limit]
    
    def mark_notification_as_read(self, notification_id: str, 
                                user_id: Optional[str] = None) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark
            user_id: ID of the user the notification belongs to
                   If None, check system notifications
            
        Returns:
            True if the notification was found and marked, False otherwise
        """
        return self._update_notification_status(
            notification_id, 
            NotificationStatus.READ,
            user_id
        )
    
    def mark_notification_as_archived(self, notification_id: str, 
                                    user_id: Optional[str] = None) -> bool:
        """
        Mark a notification as archived.
        
        Args:
            notification_id: ID of the notification to mark
            user_id: ID of the user the notification belongs to
                   If None, check system notifications
            
        Returns:
            True if the notification was found and marked, False otherwise
        """
        return self._update_notification_status(
            notification_id, 
            NotificationStatus.ARCHIVED,
            user_id
        )
    
    def delete_notification(self, notification_id: str, 
                          user_id: Optional[str] = None) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification to delete
            user_id: ID of the user the notification belongs to
                   If None, check system notifications
            
        Returns:
            True if the notification was found and deleted, False otherwise
        """
        return self._update_notification_status(
            notification_id, 
            NotificationStatus.DELETED,
            user_id
        )
    
    def register_channel(self, channel: NotificationChannel) -> None:
        """
        Register a notification channel.
        
        Args:
            channel: The channel to register
        """
        self.dispatcher.register_channel(channel)
    
    def unregister_channel(self, channel_name: str) -> None:
        """
        Unregister a notification channel.
        
        Args:
            channel_name: Name of the channel to unregister
        """
        self.dispatcher.unregister_channel(channel_name)
    
    def _update_notification_status(self, notification_id: str, 
                                  status: NotificationStatus,
                                  user_id: Optional[str] = None) -> bool:
        """
        Update the status of a notification.
        
        Args:
            notification_id: ID of the notification to update
            status: New status
            user_id: ID of the user the notification belongs to
                   If None, check system notifications
            
        Returns:
            True if the notification was found and updated, False otherwise
        """
        # Determine which notifications to check
        if user_id:
            if user_id not in self.notifications:
                return False
            user_notifications = self.notifications[user_id]
        else:
            if "system" not in self.notifications:
                return False
            user_notifications = self.notifications["system"]
        
        # Find and update the notification
        for notification in user_notifications:
            if notification["id"] == notification_id:
                notification["status"] = status.value
                self._save_notifications()
                return True
        
        return False
    
    def _load_notifications(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load notifications from the data file."""
        if self.data_dir and os.path.exists(self.notifications_file):
            try:
                with open(self.notifications_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_notifications(self) -> None:
        """Save notifications to the data file."""
        if not self.data_dir:
            return
        
        try:
            with open(self.notifications_file, 'w') as f:
                json.dump(self.notifications, f, indent=2)
        except Exception as e:
            print(f"Error saving notifications: {e}")
