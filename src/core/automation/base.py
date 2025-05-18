"""
Base classes for the Task Automation System.

This module defines the core interfaces for automation rules, triggers,
conditions, and actions.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
import uuid
import json


class TriggerType(Enum):
    """Types of triggers for automation rules."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMMENTED = "task_commented"
    TASK_DEPENDENCY_ADDED = "task_dependency_added"
    TASK_DEPENDENCY_REMOVED = "task_dependency_removed"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    DEADLINE_APPROACHING = "deadline_approaching"
    DEADLINE_PASSED = "deadline_passed"
    MANUAL = "manual"
    EXTERNAL = "external"


class ConditionType(Enum):
    """Types of conditions for automation rules."""
    TASK_STATUS = "task_status"
    TASK_PRIORITY = "task_priority"
    TASK_ASSIGNEE = "task_assignee"
    TASK_HAS_DEPENDENCIES = "task_has_dependencies"
    TASK_DEPENDENCIES_COMPLETED = "task_dependencies_completed"
    TASK_PAST_DUE = "task_past_due"
    TASK_HAS_TAGS = "task_has_tags"
    TASK_COMPLEXITY = "task_complexity"
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    CUSTOM = "custom"


class ActionType(Enum):
    """Types of actions for automation rules."""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    ASSIGN_TASK = "assign_task"
    ADD_DEPENDENCY = "add_dependency"
    REMOVE_DEPENDENCY = "remove_dependency"
    SEND_NOTIFICATION = "send_notification"
    EXECUTE_COMMAND = "execute_command"
    CALL_WEBHOOK = "call_webhook"
    CUSTOM = "custom"


class Trigger:
    """Base class for triggers."""
    
    def __init__(self, type: TriggerType, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a trigger.
        
        Args:
            type: Type of trigger
            config: Configuration for the trigger
        """
        self.type = type
        self.config = config or {}
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """
        Check if the trigger matches the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the trigger matches the event, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the trigger to a dictionary.
        
        Returns:
            Dictionary representation of the trigger
        """
        return {
            "type": self.type.value,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trigger':
        """
        Create a trigger from a dictionary.
        
        Args:
            data: Dictionary representation of the trigger
            
        Returns:
            Trigger instance
        """
        raise NotImplementedError("Subclasses must implement this method")


class Condition:
    """Base class for conditions."""
    
    def __init__(self, type: ConditionType, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a condition.
        
        Args:
            type: Type of condition
            config: Configuration for the condition
        """
        self.type = type
        self.config = config or {}
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the condition to a dictionary.
        
        Returns:
            Dictionary representation of the condition
        """
        return {
            "type": self.type.value,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            Condition instance
        """
        raise NotImplementedError("Subclasses must implement this method")


class Action:
    """Base class for actions."""
    
    def __init__(self, type: ActionType, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an action.
        
        Args:
            type: Type of action
            config: Configuration for the action
        """
        self.type = type
        self.config = config or {}
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            context: Context for execution
            
        Returns:
            Result of the action execution
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the action to a dictionary.
        
        Returns:
            Dictionary representation of the action
        """
        return {
            "type": self.type.value,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """
        Create an action from a dictionary.
        
        Args:
            data: Dictionary representation of the action
            
        Returns:
            Action instance
        """
        raise NotImplementedError("Subclasses must implement this method")


class AutomationRule:
    """Represents an automation rule."""
    
    def __init__(self, 
                 id: Optional[str] = None,
                 name: str = "",
                 description: str = "",
                 triggers: Optional[List[Trigger]] = None,
                 conditions: Optional[List[Condition]] = None,
                 actions: Optional[List[Action]] = None,
                 enabled: bool = True,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an automation rule.
        
        Args:
            id: Unique identifier for the rule
            name: Name of the rule
            description: Description of the rule
            triggers: List of triggers that can activate the rule
            conditions: List of conditions that must be met for the rule to execute
            actions: List of actions to execute when the rule is triggered
            enabled: Whether the rule is enabled
            created_at: When the rule was created
            updated_at: When the rule was last updated
            metadata: Additional metadata for the rule
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.triggers = triggers or []
        self.conditions = conditions or []
        self.actions = actions or []
        self.enabled = enabled
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
    
    def matches_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if the rule matches an event.
        
        Args:
            event: Event to check
            
        Returns:
            True if any trigger matches the event, False otherwise
        """
        if not self.enabled:
            return False
        
        return any(trigger.matches(event) for trigger in self.triggers)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the rule should be executed.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if all conditions are met, False otherwise
        """
        if not self.enabled:
            return False
        
        # If there are no conditions, the rule is always executed
        if not self.conditions:
            return True
        
        return all(condition.evaluate(context) for condition in self.conditions)
    
    def execute(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the rule's actions.
        
        Args:
            context: Context for execution
            
        Returns:
            Results of action executions
        """
        if not self.enabled:
            return []
        
        results = []
        
        for action in self.actions:
            try:
                result = action.execute(context)
                results.append({
                    "action": action.type.value,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "action": action.type.value,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the rule to a dictionary.
        
        Returns:
            Dictionary representation of the rule
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "triggers": [trigger.to_dict() for trigger in self.triggers],
            "conditions": [condition.to_dict() for condition in self.conditions],
            "actions": [action.to_dict() for action in self.actions],
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], 
                trigger_factory: Callable[[Dict[str, Any]], Trigger],
                condition_factory: Callable[[Dict[str, Any]], Condition],
                action_factory: Callable[[Dict[str, Any]], Action]) -> 'AutomationRule':
        """
        Create a rule from a dictionary.
        
        Args:
            data: Dictionary representation of the rule
            trigger_factory: Function to create triggers from dictionaries
            condition_factory: Function to create conditions from dictionaries
            action_factory: Function to create actions from dictionaries
            
        Returns:
            AutomationRule instance
        """
        triggers = [trigger_factory(t) for t in data.get("triggers", [])]
        conditions = [condition_factory(c) for c in data.get("conditions", [])]
        actions = [action_factory(a) for a in data.get("actions", [])]
        
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            triggers=triggers,
            conditions=conditions,
            actions=actions,
            enabled=data.get("enabled", True),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )