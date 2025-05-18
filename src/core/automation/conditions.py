"""
Conditions for the Task Automation System.

This module defines various conditions that can be used in automation rules.
"""

from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime, time
import re

from .base import Condition, ConditionType


class TaskStatusCondition(Condition):
    """Condition for checking a task's status."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task status condition.
        
        Args:
            config: Configuration for the condition
                - status: Status to match
                - operator: Optional operator for comparison (eq, ne)
        """
        super().__init__(ConditionType.TASK_STATUS, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        status = task.get("status")
        if status is None:
            return False
        
        # Get the status to match
        match_status = self.config.get("status")
        if match_status is None:
            return False
        
        # Get the operator (default to equality)
        operator = self.config.get("operator", "eq")
        
        if operator == "eq":
            return status == match_status
        elif operator == "ne":
            return status != match_status
        else:
            # Unsupported operator
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStatusCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskStatusCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskPriorityCondition(Condition):
    """Condition for checking a task's priority."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task priority condition.
        
        Args:
            config: Configuration for the condition
                - priority: Priority to match
                - operator: Optional operator for comparison (eq, ne, gt, lt, ge, le)
        """
        super().__init__(ConditionType.TASK_PRIORITY, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        priority = task.get("priority")
        if priority is None:
            return False
        
        # Get the priority to match
        match_priority = self.config.get("priority")
        if match_priority is None:
            return False
        
        # Get the operator (default to equality)
        operator = self.config.get("operator", "eq")
        
        # Priority comparison
        # Note: This assumes that priorities can be compared (e.g., HIGH > MEDIUM > LOW)
        # If priorities are strings, we might need to map them to numeric values
        
        if operator == "eq":
            return priority == match_priority
        elif operator == "ne":
            return priority != match_priority
        elif operator == "gt":
            return priority > match_priority
        elif operator == "lt":
            return priority < match_priority
        elif operator == "ge":
            return priority >= match_priority
        elif operator == "le":
            return priority <= match_priority
        else:
            # Unsupported operator
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskPriorityCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskPriorityCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskAssigneeCondition(Condition):
    """Condition for checking a task's assignee."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task assignee condition.
        
        Args:
            config: Configuration for the condition
                - assignee: Assignee to match
                - is_assigned: Optional boolean to check if the task is assigned at all
        """
        super().__init__(ConditionType.TASK_ASSIGNEE, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        assignee = task.get("assignee")
        
        # Check if we're just checking if the task is assigned
        if "is_assigned" in self.config:
            is_assigned = bool(assignee)
            return is_assigned == self.config["is_assigned"]
        
        # Check if the assignee matches
        match_assignee = self.config.get("assignee")
        if match_assignee is None:
            return False
        
        return assignee == match_assignee
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskAssigneeCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskAssigneeCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskHasDependenciesCondition(Condition):
    """Condition for checking if a task has dependencies."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task has dependencies condition.
        
        Args:
            config: Configuration for the condition
                - has_dependencies: Boolean to check if the task has dependencies
                - count: Optional number of dependencies to check for
                - operator: Optional operator for count comparison (eq, ne, gt, lt, ge, le)
        """
        super().__init__(ConditionType.TASK_HAS_DEPENDENCIES, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        dependencies = task.get("dependencies", [])
        
        # Check if we're just checking if the task has dependencies
        if "has_dependencies" in self.config:
            has_dependencies = len(dependencies) > 0
            return has_dependencies == self.config["has_dependencies"]
        
        # Check if we're checking for a specific count
        if "count" in self.config:
            count = len(dependencies)
            match_count = self.config["count"]
            
            # Get the operator (default to equality)
            operator = self.config.get("operator", "eq")
            
            if operator == "eq":
                return count == match_count
            elif operator == "ne":
                return count != match_count
            elif operator == "gt":
                return count > match_count
            elif operator == "lt":
                return count < match_count
            elif operator == "ge":
                return count >= match_count
            elif operator == "le":
                return count <= match_count
            else:
                # Unsupported operator
                return False
        
        # Default to checking if the task has any dependencies
        return len(dependencies) > 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskHasDependenciesCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskHasDependenciesCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskDependenciesCompletedCondition(Condition):
    """Condition for checking if a task's dependencies are completed."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task dependencies completed condition.
        
        Args:
            config: Configuration for the condition
                - all_completed: Boolean to check if all dependencies are completed
                - percentage_completed: Optional percentage of dependencies that must be completed
        """
        super().__init__(ConditionType.TASK_DEPENDENCIES_COMPLETED, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        dependencies = task.get("dependencies", [])
        
        if not dependencies:
            # No dependencies, so they're all "completed"
            return True
        
        # Get the dependency tasks
        dependency_tasks = context.get("dependency_tasks", {})
        
        if not dependency_tasks:
            # We don't have information about the dependencies
            return False
        
        # Count how many dependencies are completed
        completed_count = 0
        for dep_id in dependencies:
            dep_task = dependency_tasks.get(dep_id)
            if dep_task and dep_task.get("status") == "done":
                completed_count += 1
        
        # Check if we're checking if all dependencies are completed
        if "all_completed" in self.config:
            all_completed = completed_count == len(dependencies)
            return all_completed == self.config["all_completed"]
        
        # Check if we're checking for a percentage completed
        if "percentage_completed" in self.config:
            percentage = (completed_count / len(dependencies)) * 100
            return percentage >= self.config["percentage_completed"]
        
        # Default to checking if all dependencies are completed
        return completed_count == len(dependencies)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDependenciesCompletedCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskDependenciesCompletedCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskPastDueCondition(Condition):
    """Condition for checking if a task is past due."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task past due condition.
        
        Args:
            config: Configuration for the condition
                - is_past_due: Boolean to check if the task is past due
                - days_overdue: Optional number of days the task is overdue
                - operator: Optional operator for days_overdue comparison (eq, ne, gt, lt, ge, le)
        """
        super().__init__(ConditionType.TASK_PAST_DUE, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        # Get the due date
        due_date = task.get("due_date")
        if not due_date:
            # No due date, so it can't be past due
            return False
        
        # Convert to datetime if it's a string
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        
        # Get the current time
        now = context.get("current_time", datetime.now())
        
        # Check if the task is past due
        is_past_due = now > due_date
        
        # Check if we're just checking if the task is past due
        if "is_past_due" in self.config:
            return is_past_due == self.config["is_past_due"]
        
        # If the task is not past due, we can return False for any other checks
        if not is_past_due:
            return False
        
        # Check if we're checking for a specific number of days overdue
        if "days_overdue" in self.config:
            days_overdue = (now - due_date).days
            match_days = self.config["days_overdue"]
            
            # Get the operator (default to equality)
            operator = self.config.get("operator", "eq")
            
            if operator == "eq":
                return days_overdue == match_days
            elif operator == "ne":
                return days_overdue != match_days
            elif operator == "gt":
                return days_overdue > match_days
            elif operator == "lt":
                return days_overdue < match_days
            elif operator == "ge":
                return days_overdue >= match_days
            elif operator == "le":
                return days_overdue <= match_days
            else:
                # Unsupported operator
                return False
        
        # Default to checking if the task is past due
        return is_past_due
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskPastDueCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskPastDueCondition instance
        """
        return cls(config=data.get("config", {}))


class TaskHasTagsCondition(Condition):
    """Condition for checking if a task has specific tags."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a task has tags condition.
        
        Args:
            config: Configuration for the condition
                - tags: List of tags to check for
                - match_all: Optional boolean to check if all tags must match (default: False)
        """
        super().__init__(ConditionType.TASK_HAS_TAGS, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        task = context.get("task", {})
        
        if not task:
            return False
        
        # Get the task tags
        task_tags = task.get("tags", [])
        
        # Get the tags to match
        match_tags = self.config.get("tags", [])
        if not match_tags:
            return False
        
        # Check if we need to match all tags or any tag
        match_all = self.config.get("match_all", False)
        
        if match_all:
            # All tags must match
            return all(tag in task_tags for tag in match_tags)
        else:
            # Any tag can match
            return any(tag in task_tags for tag in match_tags)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskHasTagsCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TaskHasTagsCondition instance
        """
        return cls(config=data.get("config", {}))


class TimeOfDayCondition(Condition):
    """Condition for checking the time of day."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a time of day condition.
        
        Args:
            config: Configuration for the condition
                - start_time: Start time in HH:MM format
                - end_time: End time in HH:MM format
        """
        super().__init__(ConditionType.TIME_OF_DAY, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the current time
        now = context.get("current_time", datetime.now())
        current_time = now.time()
        
        # Get the start and end times
        start_time_str = self.config.get("start_time")
        end_time_str = self.config.get("end_time")
        
        if not start_time_str or not end_time_str:
            return False
        
        # Parse the times
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        # Check if the current time is within the range
        if start_time <= end_time:
            # Normal case: start_time <= current_time <= end_time
            return start_time <= current_time <= end_time
        else:
            # Wrap around case: current_time >= start_time or current_time <= end_time
            return current_time >= start_time or current_time <= end_time
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeOfDayCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            TimeOfDayCondition instance
        """
        return cls(config=data.get("config", {}))


class DayOfWeekCondition(Condition):
    """Condition for checking the day of the week."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a day of week condition.
        
        Args:
            config: Configuration for the condition
                - days: List of days to match (0-6, where 0 is Monday)
        """
        super().__init__(ConditionType.DAY_OF_WEEK, config)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context for evaluation
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the current time
        now = context.get("current_time", datetime.now())
        
        # Get the day of the week (0 is Monday in Python's datetime)
        day_of_week = now.weekday()
        
        # Get the days to match
        match_days = self.config.get("days", [])
        if not match_days:
            return False
        
        # Check if the current day is in the list of days to match
        return day_of_week in match_days
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DayOfWeekCondition':
        """
        Create a condition from a dictionary.
        
        Args:
            data: Dictionary representation of the condition
            
        Returns:
            DayOfWeekCondition instance
        """
        return cls(config=data.get("config", {}))


# Registry of condition types to classes
CONDITION_REGISTRY: Dict[str, Type[Condition]] = {
    ConditionType.TASK_STATUS.value: TaskStatusCondition,
    ConditionType.TASK_PRIORITY.value: TaskPriorityCondition,
    ConditionType.TASK_ASSIGNEE.value: TaskAssigneeCondition,
    ConditionType.TASK_HAS_DEPENDENCIES.value: TaskHasDependenciesCondition,
    ConditionType.TASK_DEPENDENCIES_COMPLETED.value: TaskDependenciesCompletedCondition,
    ConditionType.TASK_PAST_DUE.value: TaskPastDueCondition,
    ConditionType.TASK_HAS_TAGS.value: TaskHasTagsCondition,
    ConditionType.TIME_OF_DAY.value: TimeOfDayCondition,
    ConditionType.DAY_OF_WEEK.value: DayOfWeekCondition
}


def create_condition_from_dict(data: Dict[str, Any]) -> Condition:
    """
    Create a condition from a dictionary.
    
    Args:
        data: Dictionary representation of the condition
        
    Returns:
        Condition instance
    
    Raises:
        ValueError: If the condition type is not supported
    """
    condition_type = data.get("type")
    if not condition_type or condition_type not in CONDITION_REGISTRY:
        raise ValueError(f"Unsupported condition type: {condition_type}")
    
    condition_class = CONDITION_REGISTRY[condition_type]
    return condition_class.from_dict(data)