"""
Actions for the Task Automation System.

This module defines various actions that can be executed by automation rules.
"""

from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime
import uuid
import json
import requests

from .base import Action, ActionType


class CreateTaskAction(Action):
    """Action for creating a new task."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a create task action.
        
        Args:
            config: Configuration for the action
                - title: Title of the task
                - description: Description of the task
                - priority: Priority of the task
                - status: Initial status of the task
                - assignee: Optional assignee for the task
                - dependencies: Optional list of dependencies
                - due_date: Optional due date
                - tags: Optional list of tags
        """
        super().__init__(ActionType.CREATE_TASK, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Create the task
        task_data = {
            "title": self.config.get("title", "New Task"),
            "description": self.config.get("description", ""),
            "priority": self.config.get("priority", "medium"),
            "status": self.config.get("status", "pending"),
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional fields if provided
        if "assignee" in self.config:
            task_data["assignee"] = self.config["assignee"]
        
        if "dependencies" in self.config:
            task_data["dependencies"] = self.config["dependencies"]
        
        if "due_date" in self.config:
            task_data["due_date"] = self.config["due_date"]
        
        if "tags" in self.config:
            task_data["tags"] = self.config["tags"]
        
        # Create the task
        result = task_manager.add_task(task_data)
        
        return {
            "success": True,
            "task_id": result.get("id"),
            "task": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateTaskAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            CreateTaskAction instance
        """
        return cls(config=data.get("config", {}))


class UpdateTaskAction(Action):
    """Action for updating a task."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an update task action.
        
        Args:
            config: Configuration for the action
                - task_id: ID of the task to update
                - updates: Dictionary of fields to update
        """
        super().__init__(ActionType.UPDATE_TASK, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Get the task ID
        task_id = self.config.get("task_id")
        
        # If no task ID is provided, try to get it from the context
        if not task_id:
            task = context.get("task")
            if task:
                task_id = task.get("id")
        
        if not task_id:
            raise ValueError("Task ID not found in config or context")
        
        # Get the updates
        updates = self.config.get("updates", {})
        if not updates:
            return {
                "success": False,
                "error": "No updates provided"
            }
        
        # Update the task
        result = task_manager.update_task(task_id, updates)
        
        return {
            "success": True,
            "task_id": task_id,
            "updates": updates,
            "task": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateTaskAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            UpdateTaskAction instance
        """
        return cls(config=data.get("config", {}))


class AssignTaskAction(Action):
    """Action for assigning a task to a user."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an assign task action.
        
        Args:
            config: Configuration for the action
                - task_id: ID of the task to assign
                - assignee: User ID to assign the task to
        """
        super().__init__(ActionType.ASSIGN_TASK, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Get the task ID
        task_id = self.config.get("task_id")
        
        # If no task ID is provided, try to get it from the context
        if not task_id:
            task = context.get("task")
            if task:
                task_id = task.get("id")
        
        if not task_id:
            raise ValueError("Task ID not found in config or context")
        
        # Get the assignee
        assignee = self.config.get("assignee")
        if not assignee:
            raise ValueError("Assignee not provided")
        
        # Update the task
        result = task_manager.update_task(task_id, {"assignee": assignee})
        
        return {
            "success": True,
            "task_id": task_id,
            "assignee": assignee,
            "task": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssignTaskAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            AssignTaskAction instance
        """
        return cls(config=data.get("config", {}))


class AddDependencyAction(Action):
    """Action for adding a dependency to a task."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an add dependency action.
        
        Args:
            config: Configuration for the action
                - task_id: ID of the task to add the dependency to
                - dependency_id: ID of the dependency to add
        """
        super().__init__(ActionType.ADD_DEPENDENCY, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Get the task ID
        task_id = self.config.get("task_id")
        
        # If no task ID is provided, try to get it from the context
        if not task_id:
            task = context.get("task")
            if task:
                task_id = task.get("id")
        
        if not task_id:
            raise ValueError("Task ID not found in config or context")
        
        # Get the dependency ID
        dependency_id = self.config.get("dependency_id")
        if not dependency_id:
            raise ValueError("Dependency ID not provided")
        
        # Add the dependency
        result = task_manager.add_dependency(task_id, dependency_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "dependency_id": dependency_id,
            "result": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AddDependencyAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            AddDependencyAction instance
        """
        return cls(config=data.get("config", {}))


class RemoveDependencyAction(Action):
    """Action for removing a dependency from a task."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a remove dependency action.
        
        Args:
            config: Configuration for the action
                - task_id: ID of the task to remove the dependency from
                - dependency_id: ID of the dependency to remove
        """
        super().__init__(ActionType.REMOVE_DEPENDENCY, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Get the task ID
        task_id = self.config.get("task_id")
        
        # If no task ID is provided, try to get it from the context
        if not task_id:
            task = context.get("task")
            if task:
                task_id = task.get("id")
        
        if not task_id:
            raise ValueError("Task ID not found in config or context")
        
        # Get the dependency ID
        dependency_id = self.config.get("dependency_id")
        if not dependency_id:
            raise ValueError("Dependency ID not provided")
        
        # Remove the dependency
        result = task_manager.remove_dependency(task_id, dependency_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "dependency_id": dependency_id,
            "result": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemoveDependencyAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            RemoveDependencyAction instance
        """
        return cls(config=data.get("config", {}))


class SendNotificationAction(Action):
    """Action for sending a notification."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a send notification action.
        
        Args:
            config: Configuration for the action
                - type: Type of notification
                - title: Title of the notification
                - message: Message of the notification
                - priority: Priority of the notification
                - user_id: Optional user ID to send the notification to
                - task_id: Optional task ID related to the notification
        """
        super().__init__(ActionType.SEND_NOTIFICATION, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the notification system from the context
        notification_system = context.get("notification_system")
        if not notification_system:
            raise ValueError("Notification system not found in context")
        
        # Get the notification details
        notification_type = self.config.get("type", "system")
        title = self.config.get("title", "Notification")
        message = self.config.get("message", "")
        priority = self.config.get("priority", "medium")
        
        # Get the user ID
        user_id = self.config.get("user_id")
        
        # Get the task ID
        task_id = self.config.get("task_id")
        
        # If no task ID is provided, try to get it from the context
        if not task_id:
            task = context.get("task")
            if task:
                task_id = task.get("id")
        
        # Create the notification
        notification = notification_system.create_notification(
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            user_id=user_id,
            task_id=task_id
        )
        
        return {
            "success": True,
            "notification_id": notification.id,
            "notification": notification.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SendNotificationAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            SendNotificationAction instance
        """
        return cls(config=data.get("config", {}))


class CallWebhookAction(Action):
    """Action for calling a webhook."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a call webhook action.
        
        Args:
            config: Configuration for the action
                - url: URL of the webhook
                - method: HTTP method to use (GET, POST, PUT, DELETE)
                - headers: Optional headers to include
                - data: Optional data to send
                - timeout: Optional timeout in seconds
        """
        super().__init__(ActionType.CALL_WEBHOOK, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the webhook details
        url = self.config.get("url")
        if not url:
            raise ValueError("Webhook URL not provided")
        
        method = self.config.get("method", "POST").upper()
        headers = self.config.get("headers", {})
        data = self.config.get("data", {})
        timeout = self.config.get("timeout", 30)
        
        # Make the request
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Try to parse the response as JSON
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response_data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallWebhookAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            CallWebhookAction instance
        """
        return cls(config=data.get("config", {}))


class CreateTaskFromTemplateAction(Action):
    """Action for creating a task from a template."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a create task from template action.
        
        Args:
            config: Configuration for the action
                - template_id: ID of the template to use
                - override_values: Optional values to override in the template
        """
        super().__init__(ActionType.CREATE_TASK, config)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        # Get the task manager from the context
        task_manager = context.get("task_manager")
        if not task_manager:
            raise ValueError("Task manager not found in context")
        
        # Get the template ID
        template_id = self.config.get("template_id")
        if not template_id:
            raise ValueError("Template ID not provided")
        
        # Get the override values
        override_values = self.config.get("override_values", {})
        
        # Create the task from the template
        result = task_manager.create_task_from_template(template_id, override_values)
        
        return {
            "success": True,
            "task_id": result.get("id"),
            "task": result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateTaskFromTemplateAction':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            CreateTaskFromTemplateAction instance
        """
        return cls(config=data.get("config", {}))


# Registry of action types to classes
ACTION_REGISTRY: Dict[str, Type[Action]] = {
    ActionType.CREATE_TASK.value: CreateTaskAction,
    ActionType.UPDATE_TASK.value: UpdateTaskAction,
    ActionType.ASSIGN_TASK.value: AssignTaskAction,
    ActionType.ADD_DEPENDENCY.value: AddDependencyAction,
    ActionType.REMOVE_DEPENDENCY.value: RemoveDependencyAction,
    ActionType.SEND_NOTIFICATION.value: SendNotificationAction,
    ActionType.CALL_WEBHOOK.value: CallWebhookAction
}


def create_action_from_dict(data: Dict[str, Any]) -> Action:
    """
    Create an action from a dictionary.
    
    Args:
        data: Dictionary representation of the action
        
    Returns:
        Action instance
    
    Raises:
        ValueError: If the action type is not supported
    """
    action_type = data.get("type")
    
    # Special case for create task from template
    if action_type == ActionType.CREATE_TASK.value and data.get("config", {}).get("template_id"):
        return CreateTaskFromTemplateAction.from_dict(data)
    
    if not action_type or action_type not in ACTION_REGISTRY:
        raise ValueError(f"Unsupported action type: {action_type}")
    
    action_class = ACTION_REGISTRY[action_type]
    return action_class.from_dict(data)