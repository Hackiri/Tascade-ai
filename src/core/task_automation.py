"""
Task Automation System for Tascade AI.

This module provides functionality for automating routine task operations
and workflows through rules, triggers, conditions, and actions.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import os
import json
import logging

from .models import Task, TaskStatus, TaskPriority
from .automation.base import AutomationRule, Trigger, Condition, Action
from .automation.rule_engine import RuleEngine
from .automation.scheduler import Scheduler
from .automation.triggers import create_trigger_from_dict
from .automation.conditions import create_condition_from_dict
from .automation.actions import create_action_from_dict


class TaskAutomationSystem:
    """Task Automation System for automating routine task operations and workflows."""
    
    def __init__(self, 
                task_manager,
                notification_system=None,
                data_dir: Optional[str] = None):
        """
        Initialize the Task Automation System.
        
        Args:
            task_manager: Task Manager instance
            notification_system: Optional Notification System instance
            data_dir: Optional directory for storing automation data
        """
        self.task_manager = task_manager
        self.notification_system = notification_system
        self.data_dir = data_dir
        self.logger = logging.getLogger("tascade.automation")
        
        # Create data directory if provided
        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Set up file paths
            self.rules_file = os.path.join(self.data_dir, "rules.json")
            self.events_file = os.path.join(self.data_dir, "events.json")
        else:
            self.rules_file = None
            self.events_file = None
        
        # Initialize the rule engine
        self.rule_engine = RuleEngine(rules_file=self.rules_file)
        
        # Initialize the scheduler
        self.scheduler = Scheduler(
            events_file=self.events_file,
            event_callback=self._handle_scheduled_event
        )
        
        # Start the rule engine and scheduler
        self.rule_engine.start_processing()
        self.scheduler.start()
    
    def create_rule(self, 
                   name: str,
                   description: str,
                   triggers: List[Dict[str, Any]],
                   conditions: List[Dict[str, Any]],
                   actions: List[Dict[str, Any]],
                   enabled: bool = True) -> Dict[str, Any]:
        """
        Create a new automation rule.
        
        Args:
            name: Name of the rule
            description: Description of the rule
            triggers: List of trigger configurations
            conditions: List of condition configurations
            actions: List of action configurations
            enabled: Whether the rule is enabled
            
        Returns:
            Dictionary with the created rule information
        """
        rule = self.rule_engine.create_rule(
            name=name,
            description=description,
            triggers=triggers,
            conditions=conditions,
            actions=actions,
            enabled=enabled
        )
        
        return {
            "success": True,
            "rule_id": rule.id,
            "rule": rule.to_dict()
        }
    
    def update_rule(self, 
                   rule_id: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   triggers: Optional[List[Dict[str, Any]]] = None,
                   conditions: Optional[List[Dict[str, Any]]] = None,
                   actions: Optional[List[Dict[str, Any]]] = None,
                   enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update an existing automation rule.
        
        Args:
            rule_id: ID of the rule to update
            name: New name for the rule
            description: New description for the rule
            triggers: New trigger configurations
            conditions: New condition configurations
            actions: New action configurations
            enabled: New enabled state
            
        Returns:
            Dictionary with the updated rule information
        """
        rule = self.rule_engine.update_rule(
            rule_id=rule_id,
            name=name,
            description=description,
            triggers=triggers,
            conditions=conditions,
            actions=actions,
            enabled=enabled
        )
        
        if not rule:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
        
        return {
            "success": True,
            "rule_id": rule.id,
            "rule": rule.to_dict()
        }
    
    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Delete an automation rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            Dictionary with the result of the operation
        """
        success = self.rule_engine.unregister_rule(rule_id)
        
        if not success:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
        
        return {
            "success": True,
            "rule_id": rule_id
        }
    
    def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Get an automation rule by ID.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            Dictionary with the rule information
        """
        rule = self.rule_engine.get_rule(rule_id)
        
        if not rule:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
        
        return {
            "success": True,
            "rule_id": rule.id,
            "rule": rule.to_dict()
        }
    
    def get_all_rules(self) -> Dict[str, Any]:
        """
        Get all automation rules.
        
        Returns:
            Dictionary with all rules
        """
        rules = self.rule_engine.get_all_rules()
        
        return {
            "success": True,
            "count": len(rules),
            "rules": [rule.to_dict() for rule in rules]
        }
    
    def trigger_rule(self, rule_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Manually trigger a rule.
        
        Args:
            rule_id: ID of the rule to trigger
            context: Optional context for rule execution
            
        Returns:
            Dictionary with the result of the operation
        """
        rule = self.rule_engine.get_rule(rule_id)
        
        if not rule:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
        
        # Create a manual trigger event
        event = {
            "type": "manual",
            "trigger_id": rule_id,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Process the event
        results = self.rule_engine.process_event(event)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "results": results
        }
    
    def schedule_event(self, 
                      event_type: str,
                      scheduled_time: Union[datetime, str],
                      data: Optional[Dict[str, Any]] = None,
                      recurring: bool = False,
                      recurrence_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule an event.
        
        Args:
            event_type: Type of event
            scheduled_time: When the event should occur
            data: Additional data for the event
            recurring: Whether the event recurs
            recurrence_config: Configuration for recurring events
            
        Returns:
            Dictionary with the scheduled event information
        """
        event_id = self.scheduler.schedule_event(
            event_type=event_type,
            scheduled_time=scheduled_time,
            data=data,
            recurring=recurring,
            recurrence_config=recurrence_config
        )
        
        return {
            "success": True,
            "event_id": event_id
        }
    
    def cancel_event(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled event.
        
        Args:
            event_id: ID of the event to cancel
            
        Returns:
            Dictionary with the result of the operation
        """
        success = self.scheduler.cancel_event(event_id)
        
        if not success:
            return {
                "success": False,
                "error": f"Event with ID {event_id} not found"
            }
        
        return {
            "success": True,
            "event_id": event_id
        }
    
    def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        Get a scheduled event by ID.
        
        Args:
            event_id: ID of the event to get
            
        Returns:
            Dictionary with the event information
        """
        event = self.scheduler.get_event(event_id)
        
        if not event:
            return {
                "success": False,
                "error": f"Event with ID {event_id} not found"
            }
        
        return {
            "success": True,
            "event_id": event.id,
            "event": event.to_dict()
        }
    
    def get_all_events(self) -> Dict[str, Any]:
        """
        Get all scheduled events.
        
        Returns:
            Dictionary with all events
        """
        events = self.scheduler.get_all_events()
        
        return {
            "success": True,
            "count": len(events),
            "events": [event.to_dict() for event in events]
        }
    
    def handle_task_event(self, 
                         event_type: str,
                         task: Task,
                         additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle a task event.
        
        Args:
            event_type: Type of event
            task: Task related to the event
            additional_data: Additional data for the event
            
        Returns:
            Dictionary with the result of the operation
        """
        # Create the event
        event = {
            "type": event_type,
            "task_id": task.id,
            "task": task.__dict__,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add additional data if provided
        if additional_data:
            event.update(additional_data)
        
        # Queue the event for processing
        self.rule_engine.queue_event(event)
        
        return {
            "success": True,
            "event_type": event_type,
            "task_id": task.id
        }
    
    def create_task_created_rule(self, 
                               name: str,
                               actions: List[Dict[str, Any]],
                               conditions: Optional[List[Dict[str, Any]]] = None,
                               task_id: Optional[str] = None,
                               priority: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a rule that triggers when a task is created.
        
        Args:
            name: Name of the rule
            actions: Actions to execute
            conditions: Optional conditions to check
            task_id: Optional specific task ID to match
            priority: Optional priority to match
            
        Returns:
            Dictionary with the created rule information
        """
        # Create the trigger
        trigger_config = {}
        if task_id:
            trigger_config["task_id"] = task_id
        if priority:
            trigger_config["priority"] = priority
        
        trigger = {
            "type": "task_created",
            "config": trigger_config
        }
        
        # Create the rule
        return self.create_rule(
            name=name,
            description=f"Triggers when a task is created",
            triggers=[trigger],
            conditions=conditions or [],
            actions=actions
        )
    
    def create_task_status_changed_rule(self, 
                                      name: str,
                                      actions: List[Dict[str, Any]],
                                      conditions: Optional[List[Dict[str, Any]]] = None,
                                      task_id: Optional[str] = None,
                                      from_status: Optional[str] = None,
                                      to_status: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a rule that triggers when a task's status changes.
        
        Args:
            name: Name of the rule
            actions: Actions to execute
            conditions: Optional conditions to check
            task_id: Optional specific task ID to match
            from_status: Optional status to match as the previous status
            to_status: Optional status to match as the new status
            
        Returns:
            Dictionary with the created rule information
        """
        # Create the trigger
        trigger_config = {}
        if task_id:
            trigger_config["task_id"] = task_id
        if from_status:
            trigger_config["from_status"] = from_status
        if to_status:
            trigger_config["to_status"] = to_status
        
        trigger = {
            "type": "task_status_changed",
            "config": trigger_config
        }
        
        # Create the rule
        return self.create_rule(
            name=name,
            description=f"Triggers when a task's status changes",
            triggers=[trigger],
            conditions=conditions or [],
            actions=actions
        )
    
    def create_recurring_task_rule(self, 
                                 name: str,
                                 frequency: str,
                                 task_template: Dict[str, Any],
                                 start_time: Optional[Union[datetime, str]] = None,
                                 recurrence_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a rule that creates a recurring task.
        
        Args:
            name: Name of the rule
            frequency: Frequency of recurrence (daily, weekly, monthly)
            task_template: Template for the task to create
            start_time: Optional start time for the first occurrence
            recurrence_config: Optional additional recurrence configuration
            
        Returns:
            Dictionary with the created rule and event information
        """
        # Set up the start time
        if not start_time:
            start_time = datetime.now()
        elif isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        # Set up the recurrence configuration
        config = recurrence_config or {}
        config["frequency"] = frequency
        
        # Create the action to create a task
        action = {
            "type": "create_task",
            "config": task_template
        }
        
        # Schedule the recurring event
        event_result = self.schedule_event(
            event_type="recurring",
            scheduled_time=start_time,
            data={"task_template": task_template},
            recurring=True,
            recurrence_config=config
        )
        
        # Create a rule that triggers on the recurring event
        trigger = {
            "type": "recurring",
            "config": {
                "schedule_id": event_result["event_id"],
                "frequency": frequency
            }
        }
        
        rule_result = self.create_rule(
            name=name,
            description=f"Creates a recurring task ({frequency})",
            triggers=[trigger],
            conditions=[],
            actions=[action]
        )
        
        return {
            "success": True,
            "rule_id": rule_result["rule_id"],
            "event_id": event_result["event_id"],
            "frequency": frequency
        }
    
    def create_deadline_reminder_rule(self, 
                                    name: str,
                                    days_before: int,
                                    notification_message: str,
                                    notification_priority: str = "medium") -> Dict[str, Any]:
        """
        Create a rule that sends a reminder when a task's deadline is approaching.
        
        Args:
            name: Name of the rule
            days_before: Number of days before the deadline to send the reminder
            notification_message: Message for the notification
            notification_priority: Priority for the notification
            
        Returns:
            Dictionary with the created rule information
        """
        # Create the trigger
        trigger = {
            "type": "deadline_approaching",
            "config": {
                "days_before": days_before
            }
        }
        
        # Create the action to send a notification
        action = {
            "type": "send_notification",
            "config": {
                "type": "task_deadline_approaching",
                "title": f"Deadline Approaching: {{task.title}}",
                "message": notification_message,
                "priority": notification_priority
            }
        }
        
        # Create the rule
        return self.create_rule(
            name=name,
            description=f"Sends a reminder {days_before} days before a task's deadline",
            triggers=[trigger],
            conditions=[],
            actions=[action]
        )
    
    def create_dependency_notification_rule(self, 
                                         name: str,
                                         notification_message: str,
                                         notification_priority: str = "medium") -> Dict[str, Any]:
        """
        Create a rule that notifies when all dependencies for a task are completed.
        
        Args:
            name: Name of the rule
            notification_message: Message for the notification
            notification_priority: Priority for the notification
            
        Returns:
            Dictionary with the created rule information
        """
        # Create the trigger for task status changes
        trigger = {
            "type": "task_status_changed",
            "config": {
                "to_status": "done"
            }
        }
        
        # Create the condition to check if the task has dependents
        condition = {
            "type": "task_has_dependencies",
            "config": {
                "has_dependencies": True
            }
        }
        
        # Create the action to send a notification
        action = {
            "type": "send_notification",
            "config": {
                "type": "task_dependency_completed",
                "title": "Dependency Completed: {{task.title}}",
                "message": notification_message,
                "priority": notification_priority
            }
        }
        
        # Create the rule
        return self.create_rule(
            name=name,
            description="Notifies when all dependencies for a task are completed",
            triggers=[trigger],
            conditions=[condition],
            actions=[action]
        )
    
    def shutdown(self) -> None:
        """Shutdown the Task Automation System."""
        # Stop the rule engine and scheduler
        self.rule_engine.stop_processing()
        self.scheduler.stop()
    
    def _handle_scheduled_event(self, event: Dict[str, Any]) -> None:
        """
        Handle a scheduled event.
        
        Args:
            event: Event data
        """
        # Queue the event for processing by the rule engine
        self.rule_engine.queue_event(event)