"""
Recommendation factors for the Task Recommendation System.

This module implements various factors used to score tasks for recommendations,
including priority-based, deadline-based, dependency-based, and user preference-based factors.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import logging

from .base import RecommendationFactor


class PriorityFactor(RecommendationFactor):
    """Factor that scores tasks based on priority."""
    
    def __init__(self, weight: float = 1.0, name: str = "PriorityFactor"):
        """
        Initialize a priority factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
        """
        super().__init__(weight, name)
        self.priority_scores = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "normal": 0.4,
            "low": 0.2
        }
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on priority.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        priority = task.get("priority", "normal").lower()
        return self.priority_scores.get(priority, 0.4)


class DeadlineFactor(RecommendationFactor):
    """Factor that scores tasks based on deadline proximity."""
    
    def __init__(self, weight: float = 1.0, name: str = "DeadlineFactor", urgency_threshold_days: int = 7):
        """
        Initialize a deadline factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
            urgency_threshold_days: Days threshold for urgency calculation
        """
        super().__init__(weight, name)
        self.urgency_threshold_days = urgency_threshold_days
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on deadline proximity.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # If no due date, give a middle score
        if "due_date" not in task or not task["due_date"]:
            return 0.5
        
        # Parse due date
        if isinstance(task["due_date"], str):
            try:
                due_date = datetime.fromisoformat(task["due_date"])
            except ValueError:
                return 0.5
        elif isinstance(task["due_date"], datetime):
            due_date = task["due_date"]
        else:
            return 0.5
        
        # Calculate days until due
        now = datetime.now()
        if due_date < now:
            # Overdue tasks get highest score
            return 1.0
        
        days_until_due = (due_date - now).days
        
        # Score based on urgency threshold
        if days_until_due <= 0:
            return 1.0
        elif days_until_due >= self.urgency_threshold_days:
            return 0.2
        else:
            # Linear scale from 0.2 to 1.0 based on days until due
            return 1.0 - (days_until_due / self.urgency_threshold_days) * 0.8


class DependencyFactor(RecommendationFactor):
    """Factor that scores tasks based on dependency readiness."""
    
    def __init__(self, weight: float = 1.0, name: str = "DependencyFactor"):
        """
        Initialize a dependency factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
        """
        super().__init__(weight, name)
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on dependency readiness.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # If no dependencies, task is ready
        if "dependencies" not in task or not task["dependencies"]:
            return 1.0
        
        # Get all tasks to check dependency status
        all_tasks = context.get("all_tasks", {})
        
        # Check if all dependencies are completed
        dependencies = task.get("dependencies", [])
        if not dependencies:
            return 1.0
        
        completed_deps = 0
        for dep_id in dependencies:
            if dep_id in all_tasks and all_tasks[dep_id].get("status") == "completed":
                completed_deps += 1
        
        # Score based on percentage of completed dependencies
        if not dependencies:
            return 1.0
        
        return completed_deps / len(dependencies)


class UserPreferenceFactor(RecommendationFactor):
    """Factor that scores tasks based on user preferences."""
    
    def __init__(self, weight: float = 1.0, name: str = "UserPreferenceFactor"):
        """
        Initialize a user preference factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
        """
        super().__init__(weight, name)
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on user preferences.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Get user preferences
        user_preferences = context.get("user_preferences", [])
        if not user_preferences:
            return 0.5
        
        # Calculate preference match score
        preference_score = 0.5  # Default middle score
        preference_count = 0
        
        for pref in user_preferences:
            pref_type = pref.get("preference_type")
            pref_value = pref.get("preference_value")
            pref_weight = pref.get("weight", 1.0)
            
            # Check if task matches preference
            if pref_type == "tag_preference" and "tags" in task:
                if pref_value in task["tags"]:
                    preference_score += 0.5 * pref_weight
                    preference_count += 1
            
            elif pref_type == "category_preference" and "category" in task:
                if pref_value == task["category"]:
                    preference_score += 0.5 * pref_weight
                    preference_count += 1
            
            elif pref_type == "priority_preference" and "priority" in task:
                if pref_value == task["priority"]:
                    preference_score += 0.5 * pref_weight
                    preference_count += 1
        
        # Normalize score
        if preference_count > 0:
            preference_score = min(preference_score, 1.0)
        
        return preference_score


class CompletionTimeFactor(RecommendationFactor):
    """Factor that scores tasks based on estimated completion time."""
    
    def __init__(self, weight: float = 1.0, name: str = "CompletionTimeFactor", prefer_shorter: bool = True):
        """
        Initialize a completion time factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
            prefer_shorter: Whether to prefer shorter tasks (True) or longer tasks (False)
        """
        super().__init__(weight, name)
        self.prefer_shorter = prefer_shorter
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on estimated completion time.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Get estimated time
        estimated_time = task.get("estimated_time", None)
        if estimated_time is None:
            return 0.5  # Default middle score
        
        # Get all tasks to normalize score
        all_tasks = context.get("all_tasks", [])
        if not all_tasks:
            return 0.5
        
        # Get min and max estimated times
        times = [t.get("estimated_time", 0) for t in all_tasks if "estimated_time" in t]
        if not times:
            return 0.5
        
        min_time = min(times)
        max_time = max(times)
        
        # Avoid division by zero
        if min_time == max_time:
            return 0.5
        
        # Normalize score between 0 and 1
        normalized_score = (estimated_time - min_time) / (max_time - min_time)
        
        # Invert score if we prefer shorter tasks
        if self.prefer_shorter:
            normalized_score = 1.0 - normalized_score
        
        return normalized_score


class HistoricalSuccessFactor(RecommendationFactor):
    """Factor that scores tasks based on historical success with similar tasks."""
    
    def __init__(self, weight: float = 1.0, name: str = "HistoricalSuccessFactor"):
        """
        Initialize a historical success factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
        """
        super().__init__(weight, name)
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on historical success.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Get historical performance
        historical_performance = context.get("historical_performance", {})
        if not historical_performance:
            return 0.5  # Default middle score
        
        # Get task category or type
        task_category = task.get("category", None)
        task_type = task.get("type", None)
        
        # Check historical success rate for similar tasks
        category_success = historical_performance.get(f"category_{task_category}", 0.5) if task_category else 0.5
        type_success = historical_performance.get(f"type_{task_type}", 0.5) if task_type else 0.5
        
        # Combine scores
        return (category_success + type_success) / 2


class WorkloadFactor(RecommendationFactor):
    """Factor that scores tasks based on current workload balance."""
    
    def __init__(self, weight: float = 1.0, name: str = "WorkloadFactor"):
        """
        Initialize a workload factor.
        
        Args:
            weight: Weight of this factor in the overall score
            name: Name of the factor
        """
        super().__init__(weight, name)
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on workload balance.
        
        Args:
            task: Task data
            context: Additional context
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Get workload metrics
        workload_metrics = context.get("workload_metrics", {})
        if not workload_metrics:
            return 0.5  # Default middle score
        
        # Get task category or type
        task_category = task.get("category", None)
        task_priority = task.get("priority", "normal")
        
        # Check if this task helps balance workload
        category_balance = workload_metrics.get("category_balance", {})
        priority_balance = workload_metrics.get("priority_balance", {})
        
        # If this category is underrepresented, score higher
        category_score = 0.5
        if task_category and category_balance:
            category_ratio = category_balance.get(task_category, 0.5)
            if category_ratio < 0.3:  # Underrepresented
                category_score = 0.8
            elif category_ratio > 0.7:  # Overrepresented
                category_score = 0.2
        
        # If this priority is underrepresented, score higher
        priority_score = 0.5
        if priority_balance:
            priority_ratio = priority_balance.get(task_priority, 0.5)
            if priority_ratio < 0.3:  # Underrepresented
                priority_score = 0.8
            elif priority_ratio > 0.7:  # Overrepresented
                priority_score = 0.2
        
        # Combine scores
        return (category_score + priority_score) / 2
