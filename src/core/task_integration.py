"""
Task Integration System for Tascade AI.

This module provides functionality for connecting Tascade AI with external
tools and services, enabling seamless workflow integration.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json
import os
import logging

from core.integration.base import (
    IntegrationProvider, 
    IntegrationConfig, 
    IntegrationType, 
    AuthType, 
    SyncDirection,
    IntegrationStatus
)
from core.integration.manager import IntegrationManager
from core.models import Task


class TaskIntegrationSystem:
    """Task Integration System for Tascade AI."""
    
    def __init__(self, 
                 task_manager=None,
                 data_dir: str = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Task Integration System.
        
        Args:
            task_manager: Task Manager instance
            data_dir: Directory for storing integration data
            logger: Optional logger
        """
        self.task_manager = task_manager
        self.logger = logger or logging.getLogger("tascade.integration")
        
        # Initialize integration manager
        self.integration_manager = IntegrationManager(
            data_dir=data_dir,
            logger=self.logger
        )
        
        # Flag to track if the sync scheduler is running
        self.scheduler_running = False
    
    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """
        Get available integration types.
        
        Returns:
            List of available integration types
        """
        return [
            {
                "type": IntegrationType.GITHUB.value,
                "name": "GitHub",
                "description": "Integrate with GitHub issues and projects",
                "auth_types": [AuthType.TOKEN.value, AuthType.OAUTH.value],
                "features": ["issues", "projects", "pull_requests", "webhooks"]
            },
            {
                "type": IntegrationType.JIRA.value,
                "name": "Jira",
                "description": "Integrate with Jira issues and projects",
                "auth_types": [AuthType.API_KEY.value, AuthType.BASIC.value, AuthType.OAUTH.value],
                "features": ["issues", "projects", "sprints", "webhooks"]
            },
            {
                "type": IntegrationType.TRELLO.value,
                "name": "Trello",
                "description": "Integrate with Trello boards and cards",
                "auth_types": [AuthType.API_KEY.value, AuthType.OAUTH.value],
                "features": ["boards", "cards", "lists", "webhooks"]
            },
            {
                "type": IntegrationType.SLACK.value,
                "name": "Slack",
                "description": "Integrate with Slack channels and messages",
                "auth_types": [AuthType.TOKEN.value, AuthType.OAUTH.value],
                "features": ["channels", "messages", "notifications", "webhooks"]
            },
            {
                "type": IntegrationType.CALENDAR.value,
                "name": "Calendar",
                "description": "Integrate with calendar services (Google, Outlook)",
                "auth_types": [AuthType.OAUTH.value],
                "features": ["events", "reminders", "availability"]
            },
            {
                "type": IntegrationType.EMAIL.value,
                "name": "Email",
                "description": "Integrate with email services",
                "auth_types": [AuthType.OAUTH.value, AuthType.BASIC.value],
                "features": ["send", "receive", "templates"]
            },
            {
                "type": IntegrationType.WEBHOOK.value,
                "name": "Webhook",
                "description": "Generic webhook integration",
                "auth_types": [AuthType.TOKEN.value, AuthType.NONE.value],
                "features": ["incoming", "outgoing"]
            }
        ]
    
    def get_integrations(self, 
                         type: Optional[str] = None,
                         status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get configured integrations.
        
        Args:
            type: Optional integration type filter
            status: Optional status filter
            
        Returns:
            List of integration configurations
        """
        # Convert string parameters to enums if provided
        type_enum = IntegrationType(type) if type else None
        status_enum = IntegrationStatus(status) if status else None
        
        # Get integrations from manager
        integrations = self.integration_manager.get_integrations(
            type=type_enum,
            status=status_enum
        )
        
        # Convert to dictionaries
        return [config.to_dict() for config in integrations]
    
    def get_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Get an integration by ID.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration configuration or error
        """
        config = self.integration_manager.get_integration(integration_id)
        
        if not config:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        return {
            "success": True,
            "integration": config.to_dict()
        }
    
    def create_integration(self, 
                          name: str,
                          type: str,
                          auth_config: Dict[str, Any],
                          sync_config: Dict[str, Any],
                          settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new integration.
        
        Args:
            name: Display name
            type: Integration type
            auth_config: Authentication configuration
            sync_config: Synchronization configuration
            settings: Optional provider-specific settings
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Convert string type to enum
            type_enum = IntegrationType(type)
            
            # Create integration
            result = self.integration_manager.create_integration(
                name=name,
                type=type_enum,
                auth_config=auth_config,
                sync_config=sync_config,
                settings=settings
            )
            
            return result
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid integration type: {type}"
            }
        except Exception as e:
            self.logger.error(f"Error creating integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_integration(self, 
                          integration_id: str,
                          name: Optional[str] = None,
                          auth_config: Optional[Dict[str, Any]] = None,
                          sync_config: Optional[Dict[str, Any]] = None,
                          settings: Optional[Dict[str, Any]] = None,
                          status: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing integration.
        
        Args:
            integration_id: Integration ID
            name: Optional new name
            auth_config: Optional new authentication configuration
            sync_config: Optional new synchronization configuration
            settings: Optional new provider-specific settings
            status: Optional new status
            
        Returns:
            Dictionary with update results
        """
        try:
            # Convert string status to enum if provided
            status_enum = IntegrationStatus(status) if status else None
            
            # Update integration
            result = self.integration_manager.update_integration(
                integration_id=integration_id,
                name=name,
                auth_config=auth_config,
                sync_config=sync_config,
                settings=settings,
                status=status_enum
            )
            
            return result
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid integration status: {status}"
            }
        except Exception as e:
            self.logger.error(f"Error updating integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Delete an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with deletion results
        """
        return self.integration_manager.delete_integration(integration_id)
    
    def activate_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Activate an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with activation results
        """
        return self.integration_manager.activate_integration(integration_id)
    
    def deactivate_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Deactivate an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with deactivation results
        """
        return self.integration_manager.deactivate_integration(integration_id)
    
    def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Test an integration connection.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with test results
        """
        return self.integration_manager.test_integration(integration_id)
    
    def import_tasks(self, integration_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Import tasks from an integration.
        
        Args:
            integration_id: Integration ID
            filters: Optional filters for task selection
            
        Returns:
            Dictionary with import results
        """
        # Import tasks from integration
        result = self.integration_manager.import_tasks(integration_id, filters)
        
        if not result.get("success"):
            return result
        
        # If task manager is available, add imported tasks
        if self.task_manager:
            imported_tasks = result.get("tasks", [])
            added_tasks = []
            
            for task_data in imported_tasks:
                try:
                    # Create task from imported data
                    task = Task.from_dict(task_data)
                    
                    # Add task to task manager
                    task_id = self.task_manager.add_task(task)
                    
                    added_tasks.append({
                        "task_id": task_id,
                        "title": task.title,
                        "source": task_data.get("source")
                    })
                except Exception as e:
                    self.logger.error(f"Error adding imported task: {e}")
            
            result["added_tasks"] = added_tasks
            result["added_count"] = len(added_tasks)
        
        return result
    
    def export_tasks(self, integration_id: str, task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export tasks to an integration.
        
        Args:
            integration_id: Integration ID
            task_ids: Optional list of task IDs to export
            
        Returns:
            Dictionary with export results
        """
        if not self.task_manager:
            return {
                "success": False,
                "error": "Task manager not available"
            }
        
        try:
            # Get tasks from task manager
            tasks = []
            
            if task_ids:
                # Get specific tasks
                for task_id in task_ids:
                    task = self.task_manager.get_task(task_id)
                    if task:
                        tasks.append(task.to_dict())
            else:
                # Get all tasks
                all_tasks = self.task_manager.get_tasks()
                tasks = [task.to_dict() for task in all_tasks]
            
            # Export tasks to integration
            result = self.integration_manager.export_tasks(integration_id, tasks)
            
            return result
        except Exception as e:
            self.logger.error(f"Error exporting tasks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_integration(self, integration_id: str, direction: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronize tasks with an integration.
        
        Args:
            integration_id: Integration ID
            direction: Optional direction to override config
            
        Returns:
            Dictionary with synchronization results
        """
        try:
            # Convert string direction to enum if provided
            direction_enum = SyncDirection(direction) if direction else None
            
            # Sync integration
            result = self.integration_manager.sync_integration(
                integration_id=integration_id,
                direction=direction_enum
            )
            
            return result
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid sync direction: {direction}"
            }
        except Exception as e:
            self.logger.error(f"Error syncing integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_sync_scheduler(self) -> Dict[str, Any]:
        """
        Start the synchronization scheduler.
        
        Returns:
            Dictionary with start results
        """
        if self.scheduler_running:
            return {
                "success": True,
                "message": "Sync scheduler is already running"
            }
        
        # Start scheduler
        success = self.integration_manager.start_sync_scheduler()
        
        if success:
            self.scheduler_running = True
            return {
                "success": True,
                "message": "Sync scheduler started successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to start sync scheduler"
            }
    
    def stop_sync_scheduler(self) -> Dict[str, Any]:
        """
        Stop the synchronization scheduler.
        
        Returns:
            Dictionary with stop results
        """
        if not self.scheduler_running:
            return {
                "success": True,
                "message": "Sync scheduler is not running"
            }
        
        # Stop scheduler
        success = self.integration_manager.stop_sync_scheduler()
        
        if success:
            self.scheduler_running = False
            return {
                "success": True,
                "message": "Sync scheduler stopped successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to stop sync scheduler"
            }
    
    def process_webhook(self, integration_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload from an integration.
        
        Args:
            integration_id: Integration ID
            payload: Webhook payload
            
        Returns:
            Dictionary with processing results
        """
        # Process webhook
        result = self.integration_manager.process_webhook(integration_id, payload)
        
        if not result.get("success"):
            return result
        
        # Handle task events
        if "task" in result and self.task_manager:
            task_data = result["task"]
            event_type = result.get("event_type")
            
            try:
                if event_type and "created" in event_type:
                    # Create new task
                    task = Task.from_dict(task_data)
                    task_id = self.task_manager.add_task(task)
                    result["task_id"] = task_id
                elif event_type and "updated" in event_type:
                    # Update existing task
                    task_id = task_data.get("id")
                    if task_id:
                        task = Task.from_dict(task_data)
                        self.task_manager.update_task(task_id, task)
                        result["task_id"] = task_id
                elif event_type and "deleted" in event_type:
                    # Delete task
                    task_id = task_data.get("id")
                    if task_id:
                        self.task_manager.delete_task(task_id)
                        result["task_id"] = task_id
            except Exception as e:
                self.logger.error(f"Error processing task event: {e}")
                result["task_error"] = str(e)
        
        return result