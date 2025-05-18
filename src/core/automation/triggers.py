"""
Triggers for the Task Automation System.

This module defines various triggers that can activate automation rules.
"""

from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime, time
import re

from .base import Trigger, TriggerType


class TaskCreatedTrigger(Trigger):
    """Trigger for when a task is created."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task created trigger.
        
        Args:
            config: Configuration for the trigger
                - task_id: Optional specific task ID to match
                - priority: Optional priority to match
        """
        super().__init__(TriggerType.TASK_CREATED, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "task_created":
            return False
        
        # Check if we need to match a specific task ID
        if self.config.get("task_id") and event.get("task_id") != self.config["task_id"]:
            return False
        
        # Check if we need to match a specific priority
        if self.config.get("priority") and event.get("task", {}).get("priority") != self.config["priority"]:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskCreatedTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            TaskCreatedTrigger instance
        """
        return cls(config=data.get("config", {}))


class TaskUpdatedTrigger(Trigger):
    """Trigger for when a task is updated."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task updated trigger.
        
        Args:
            config: Configuration for the trigger
                - task_id: Optional specific task ID to match
                - fields: Optional list of fields to check for changes
        """
        super().__init__(TriggerType.TASK_UPDATED, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "task_updated":
            return False
        
        # Check if we need to match a specific task ID
        if self.config.get("task_id") and event.get("task_id") != self.config["task_id"]:
            return False
        
        # Check if we need to match specific fields being updated
        if self.config.get("fields"):
            # Get the fields that were updated
            updated_fields = event.get("updated_fields", [])
            
            # Check if any of the specified fields were updated
            if not any(field in updated_fields for field in self.config["fields"]):
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskUpdatedTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            TaskUpdatedTrigger instance
        """
        return cls(config=data.get("config", {}))


class TaskStatusChangedTrigger(Trigger):
    """Trigger for when a task's status changes."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task status changed trigger.
        
        Args:
            config: Configuration for the trigger
                - task_id: Optional specific task ID to match
                - from_status: Optional status to match as the previous status
                - to_status: Optional status to match as the new status
        """
        super().__init__(TriggerType.TASK_STATUS_CHANGED, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "task_status_changed":
            return False
        
        # Check if we need to match a specific task ID
        if self.config.get("task_id") and event.get("task_id") != self.config["task_id"]:
            return False
        
        # Check if we need to match a specific previous status
        if self.config.get("from_status") and event.get("from_status") != self.config["from_status"]:
            return False
        
        # Check if we need to match a specific new status
        if self.config.get("to_status") and event.get("to_status") != self.config["to_status"]:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStatusChangedTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            TaskStatusChangedTrigger instance
        """
        return cls(config=data.get("config", {}))


class TaskAssignedTrigger(Trigger):
    """Trigger for when a task is assigned."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task assigned trigger.
        
        Args:
            config: Configuration for the trigger
                - task_id: Optional specific task ID to match
                - assignee: Optional assignee to match
                - previous_assignee: Optional previous assignee to match
        """
        super().__init__(TriggerType.TASK_ASSIGNED, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "task_assigned":
            return False
        
        # Check if we need to match a specific task ID
        if self.config.get("task_id") and event.get("task_id") != self.config["task_id"]:
            return False
        
        # Check if we need to match a specific assignee
        if self.config.get("assignee") and event.get("assignee") != self.config["assignee"]:
            return False
        
        # Check if we need to match a specific previous assignee
        if self.config.get("previous_assignee") and event.get("previous_assignee") != self.config["previous_assignee"]:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskAssignedTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            TaskAssignedTrigger instance
        """
        return cls(config=data.get("config", {}))


class ScheduledTrigger(Trigger):
    """Trigger for scheduled events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a scheduled trigger.
        
        Args:
            config: Configuration for the trigger
                - schedule_id: ID of the schedule
                - scheduled_time: ISO formatted datetime for when the trigger should fire
        """
        super().__init__(TriggerType.SCHEDULED, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "scheduled":
            return False
        
        # Check if we need to match a specific schedule ID
        if self.config.get("schedule_id") and event.get("schedule_id") != self.config["schedule_id"]:
            return False
        
        # Check if the scheduled time matches
        if self.config.get("scheduled_time"):
            scheduled_time = datetime.fromisoformat(self.config["scheduled_time"])
            event_time = datetime.fromisoformat(event.get("time", ""))
            
            # Allow a small window of tolerance (5 minutes)
            time_diff = abs((scheduled_time - event_time).total_seconds())
            if time_diff > 300:  # 5 minutes in seconds
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            ScheduledTrigger instance
        """
        return cls(config=data.get("config", {}))


class RecurringTrigger(Trigger):
    """Trigger for recurring events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a recurring trigger.
        
        Args:
            config: Configuration for the trigger
                - schedule_id: ID of the schedule
                - frequency: How often the trigger should fire (daily, weekly, monthly, etc.)
                - day_of_week: For weekly frequency, which day of the week (0-6, where 0 is Monday)
                - day_of_month: For monthly frequency, which day of the month (1-31)
                - time_of_day: Time of day in HH:MM format
        """
        super().__init__(TriggerType.RECURRING, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "recurring":
            return False
        
        # Check if we need to match a specific schedule ID
        if self.config.get("schedule_id") and event.get("schedule_id") != self.config["schedule_id"]:
            return False
        
        # Check if the frequency matches
        if self.config.get("frequency") and event.get("frequency") != self.config["frequency"]:
            return False
        
        # For weekly frequency, check if the day of the week matches
        if (self.config.get("frequency") == "weekly" and 
            self.config.get("day_of_week") is not None and 
            event.get("day_of_week") != self.config["day_of_week"]):
            return False
        
        # For monthly frequency, check if the day of the month matches
        if (self.config.get("frequency") == "monthly" and 
            self.config.get("day_of_month") is not None and 
            event.get("day_of_month") != self.config["day_of_month"]):
            return False
        
        # Check if the time of day matches
        if self.config.get("time_of_day"):
            config_time = datetime.strptime(self.config["time_of_day"], "%H:%M").time()
            event_time = datetime.strptime(event.get("time_of_day", "00:00"), "%H:%M").time()
            
            # Allow a small window of tolerance (5 minutes)
            config_minutes = config_time.hour * 60 + config_time.minute
            event_minutes = event_time.hour * 60 + event_time.minute
            
            if abs(config_minutes - event_minutes) > 5:
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecurringTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            RecurringTrigger instance
        """
        return cls(config=data.get("config", {}))


class DeadlineApproachingTrigger(Trigger):
    """Trigger for when a task's deadline is approaching."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a deadline approaching trigger.
        
        Args:
            config: Configuration for the trigger
                - task_id: Optional specific task ID to match
                - days_before: Number of days before the deadline to trigger
        """
        super().__init__(TriggerType.DEADLINE_APPROACHING, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "deadline_approaching":
            return False
        
        # Check if we need to match a specific task ID
        if self.config.get("task_id") and event.get("task_id") != self.config["task_id"]:
            return False
        
        # Check if the days before matches
        if self.config.get("days_before") is not None:
            if event.get("days_before") != self.config["days_before"]:
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeadlineApproachingTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            DeadlineApproachingTrigger instance
        """
        return cls(config=data.get("config", {}))


class ManualTrigger(Trigger):
    """Trigger for manual activation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a manual trigger.
        
        Args:
            config: Configuration for the trigger
                - trigger_id: Optional ID for the manual trigger
        """
        super().__init__(TriggerType.MANUAL, config)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        if event.get("type") != "manual":
            return False
        
        # Check if we need to match a specific trigger ID
        if self.config.get("trigger_id") and event.get("trigger_id") != self.config["trigger_id"]:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ManualTrigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            ManualTrigger instance
        """
        return cls(config=data.get("config", {}))


# Registry of trigger types to classes
TRIGGER_REGISTRY: Dict[str, Type[Trigger]] = {
    TriggerType.TASK_CREATED.value: TaskCreatedTrigger,
    TriggerType.TASK_UPDATED.value: TaskUpdatedTrigger,
    TriggerType.TASK_STATUS_CHANGED.value: TaskStatusChangedTrigger,
    TriggerType.TASK_ASSIGNED.value: TaskAssignedTrigger,
    TriggerType.SCHEDULED.value: ScheduledTrigger,
    TriggerType.RECURRING.value: RecurringTrigger,
    TriggerType.DEADLINE_APPROACHING.value: DeadlineApproachingTrigger,
    TriggerType.MANUAL.value: ManualTrigger
}


def create_trigger_from_dict(data: Dict[str, Any]) -> Trigger:
    """
    Create a trigger from a dictionary.
    
    Args:
        data: Dictionary representation of the trigger
        
    Returns:
        Trigger instance
    
    Raises:
        ValueError: If the trigger type is not supported
    """
    trigger_type = data.get("type")
    if not trigger_type or trigger_type not in TRIGGER_REGISTRY:
        raise ValueError(f"Unsupported trigger type: {trigger_type}")
    
    trigger_class = TRIGGER_REGISTRY[trigger_type]
    return trigger_class.from_dict(data)