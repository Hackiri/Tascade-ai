"""
Workload Balancer for the Task Recommendation System.

This module implements the workload balancing functionality,
distributing tasks optimally based on user capacity and preferences.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
from collections import defaultdict

from .base import WorkloadBalancer


class TaskWorkloadBalancer(WorkloadBalancer):
    """Balancer for task workloads."""
    
    def __init__(self, 
                 task_manager=None,
                 time_tracking_system=None,
                 historical_analyzer=None,
                 data_dir: str = None,
                 workload_file: str = "workload_settings.json",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a task workload balancer.
        
        Args:
            task_manager: Task Manager instance
            time_tracking_system: Time Tracking System instance
            historical_analyzer: Historical Performance Analyzer instance
            data_dir: Directory for storing workload data
            workload_file: File name for workload settings
            logger: Optional logger
        """
        super().__init__(logger)
        self.task_manager = task_manager
        self.time_tracking_system = time_tracking_system
        self.historical_analyzer = historical_analyzer
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.workload_file = os.path.join(self.data_dir, workload_file)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize workload settings
        self.workload_settings: Dict[str, Dict[str, Any]] = {}
        
        # Load existing workload settings
        self._load_workload_settings()
    
    def _load_workload_settings(self) -> None:
        """Load workload settings from the workload file."""
        if not os.path.exists(self.workload_file):
            self.logger.info(f"Workload settings file not found: {self.workload_file}")
            return
        
        try:
            with open(self.workload_file, 'r') as f:
                self.workload_settings = json.load(f)
                
            self.logger.info(f"Loaded workload settings for {len(self.workload_settings)} users")
        except Exception as e:
            self.logger.error(f"Error loading workload settings: {e}")
    
    def _save_workload_settings(self) -> None:
        """Save workload settings to the workload file."""
        try:
            with open(self.workload_file, 'w') as f:
                json.dump(self.workload_settings, f, indent=2)
                
            self.logger.info(f"Saved workload settings for {len(self.workload_settings)} users")
        except Exception as e:
            self.logger.error(f"Error saving workload settings: {e}")
    
    def set_user_workload_settings(self, 
                                 user_id: str, 
                                 daily_capacity_minutes: int = 480,  # 8 hours
                                 max_concurrent_tasks: int = 5,
                                 preferred_task_size: str = "medium",
                                 category_limits: Optional[Dict[str, int]] = None,
                                 priority_weights: Optional[Dict[str, float]] = None) -> bool:
        """
        Set workload settings for a user.
        
        Args:
            user_id: User identifier
            daily_capacity_minutes: Daily capacity in minutes
            max_concurrent_tasks: Maximum concurrent tasks
            preferred_task_size: Preferred task size (small, medium, large)
            category_limits: Maximum tasks per category
            priority_weights: Weights for different priorities
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.workload_settings[user_id] = {
                "daily_capacity_minutes": daily_capacity_minutes,
                "max_concurrent_tasks": max_concurrent_tasks,
                "preferred_task_size": preferred_task_size,
                "category_limits": category_limits or {},
                "priority_weights": priority_weights or {
                    "critical": 2.0,
                    "high": 1.5,
                    "medium": 1.0,
                    "normal": 0.8,
                    "low": 0.5
                },
                "updated_at": datetime.now().isoformat()
            }
            
            self._save_workload_settings()
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting workload settings: {e}")
            return False
    
    def get_user_workload_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get workload settings for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Workload settings
        """
        if user_id not in self.workload_settings:
            # Return default settings
            return {
                "daily_capacity_minutes": 480,  # 8 hours
                "max_concurrent_tasks": 5,
                "preferred_task_size": "medium",
                "category_limits": {},
                "priority_weights": {
                    "critical": 2.0,
                    "high": 1.5,
                    "medium": 1.0,
                    "normal": 0.8,
                    "low": 0.5
                }
            }
        
        return self.workload_settings[user_id]
    
    def balance_workload(self, 
                       user_id: str, 
                       tasks: List[Dict[str, Any]], 
                       time_period: Optional[timedelta] = None) -> List[Dict[str, Any]]:
        """
        Balance workload for a user.
        
        Args:
            user_id: User identifier
            tasks: Tasks to balance
            time_period: Time period for balancing
            
        Returns:
            Balanced task list
        """
        if not tasks:
            return []
        
        # Get user settings
        settings = self.get_user_workload_settings(user_id)
        
        # Default time period to one day if not specified
        if time_period is None:
            time_period = timedelta(days=1)
        
        # Calculate total minutes in time period
        total_minutes = time_period.total_seconds() / 60
        
        # Calculate daily capacity
        daily_capacity = settings["daily_capacity_minutes"]
        
        # Calculate capacity for time period
        capacity_minutes = daily_capacity * (total_minutes / (24 * 60))
        
        # Get task predictions if historical analyzer is available
        task_predictions = {}
        if self.historical_analyzer:
            for task in tasks:
                prediction = self.historical_analyzer.predict_completion_time(task, user_id)
                task_predictions[task.get("id", "")] = prediction
        
        # Score tasks for balancing
        scored_tasks = []
        for task in tasks:
            task_id = task.get("id", "")
            
            # Get estimated time
            if task_id in task_predictions:
                estimated_minutes = task_predictions[task_id].get("predicted_minutes", 0)
            else:
                estimated_minutes = task.get("estimated_time", 60)  # Default to 1 hour
            
            # Get priority weight
            priority = task.get("priority", "normal").lower()
            priority_weight = settings["priority_weights"].get(priority, 1.0)
            
            # Get category
            category = task.get("category", "")
            
            # Calculate score
            score = priority_weight
            
            # Adjust for preferred task size
            preferred_size = settings["preferred_task_size"]
            if preferred_size == "small" and estimated_minutes < 30:
                score *= 1.2
            elif preferred_size == "medium" and 30 <= estimated_minutes < 120:
                score *= 1.2
            elif preferred_size == "large" and estimated_minutes >= 120:
                score *= 1.2
            
            scored_tasks.append({
                "task": task,
                "score": score,
                "estimated_minutes": estimated_minutes,
                "category": category
            })
        
        # Sort tasks by score (descending)
        scored_tasks.sort(key=lambda t: t["score"], reverse=True)
        
        # Initialize balanced task list
        balanced_tasks = []
        
        # Track allocated time and categories
        allocated_minutes = 0
        category_counts = defaultdict(int)
        
        # Allocate tasks
        for task_info in scored_tasks:
            task = task_info["task"]
            estimated_minutes = task_info["estimated_minutes"]
            category = task_info["category"]
            
            # Check if adding this task would exceed capacity
            if allocated_minutes + estimated_minutes > capacity_minutes:
                continue
            
            # Check if adding this task would exceed category limit
            if category and category in settings["category_limits"]:
                if category_counts[category] >= settings["category_limits"][category]:
                    continue
            
            # Add task to balanced list
            balanced_tasks.append(task)
            
            # Update tracking
            allocated_minutes += estimated_minutes
            category_counts[category] += 1
            
            # Check if we've reached max concurrent tasks
            if len(balanced_tasks) >= settings["max_concurrent_tasks"]:
                break
        
        return balanced_tasks
    
    def get_optimal_task_count(self, 
                             user_id: str, 
                             time_period: Optional[timedelta] = None) -> int:
        """
        Get optimal task count for a user.
        
        Args:
            user_id: User identifier
            time_period: Time period for calculation
            
        Returns:
            Optimal task count
        """
        # Get user settings
        settings = self.get_user_workload_settings(user_id)
        
        # Default time period to one day if not specified
        if time_period is None:
            time_period = timedelta(days=1)
        
        # Calculate total minutes in time period
        total_minutes = time_period.total_seconds() / 60
        
        # Calculate daily capacity
        daily_capacity = settings["daily_capacity_minutes"]
        
        # Calculate capacity for time period
        capacity_minutes = daily_capacity * (total_minutes / (24 * 60))
        
        # Get average task duration from historical data if available
        avg_task_duration = 60  # Default to 1 hour
        
        if self.historical_analyzer and hasattr(self.historical_analyzer, "analyze_user_performance"):
            performance = self.historical_analyzer.analyze_user_performance(user_id)
            
            # Calculate average task duration across all categories
            total_duration = 0
            total_count = 0
            
            for category, data in performance.get("category_performance", {}).items():
                avg_time = data.get("average_completion_time", 0)
                count = data.get("count", 0)
                
                if avg_time > 0 and count > 0:
                    total_duration += avg_time * count
                    total_count += count
            
            if total_count > 0:
                avg_task_duration = total_duration / total_count
        
        # Calculate optimal task count
        optimal_count = int(capacity_minutes / avg_task_duration)
        
        # Limit by max concurrent tasks
        max_concurrent = settings["max_concurrent_tasks"]
        
        return min(optimal_count, max_concurrent)
    
    def calculate_workload_metrics(self, 
                                 user_id: str, 
                                 tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate workload metrics for a user.
        
        Args:
            user_id: User identifier
            tasks: Tasks to calculate metrics for
            
        Returns:
            Workload metrics
        """
        if not tasks:
            return {
                "user_id": user_id,
                "total_tasks": 0,
                "total_estimated_minutes": 0,
                "category_balance": {},
                "priority_balance": {},
                "size_balance": {}
            }
        
        # Get user settings
        settings = self.get_user_workload_settings(user_id)
        
        # Get task predictions if historical analyzer is available
        task_predictions = {}
        if self.historical_analyzer:
            for task in tasks:
                prediction = self.historical_analyzer.predict_completion_time(task, user_id)
                task_predictions[task.get("id", "")] = prediction
        
        # Calculate metrics
        total_tasks = len(tasks)
        total_estimated_minutes = 0
        
        # Count by category, priority, and size
        category_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        size_counts = {"small": 0, "medium": 0, "large": 0}
        
        for task in tasks:
            task_id = task.get("id", "")
            
            # Get estimated time
            if task_id in task_predictions:
                estimated_minutes = task_predictions[task_id].get("predicted_minutes", 0)
            else:
                estimated_minutes = task.get("estimated_time", 60)  # Default to 1 hour
            
            # Update total estimated minutes
            total_estimated_minutes += estimated_minutes
            
            # Update category count
            category = task.get("category", "")
            if category:
                category_counts[category] += 1
            
            # Update priority count
            priority = task.get("priority", "normal").lower()
            priority_counts[priority] += 1
            
            # Update size count
            if estimated_minutes < 30:
                size_counts["small"] += 1
            elif estimated_minutes < 120:
                size_counts["medium"] += 1
            else:
                size_counts["large"] += 1
        
        # Calculate balance ratios
        category_balance = {category: count / total_tasks for category, count in category_counts.items()}
        priority_balance = {priority: count / total_tasks for priority, count in priority_counts.items()}
        size_balance = {size: count / total_tasks for size, count in size_counts.items()}
        
        # Calculate workload percentage of capacity
        daily_capacity = settings["daily_capacity_minutes"]
        workload_percentage = (total_estimated_minutes / daily_capacity) * 100 if daily_capacity > 0 else 0
        
        return {
            "user_id": user_id,
            "total_tasks": total_tasks,
            "total_estimated_minutes": total_estimated_minutes,
            "workload_percentage": workload_percentage,
            "category_balance": category_balance,
            "priority_balance": priority_balance,
            "size_balance": size_balance
        }
