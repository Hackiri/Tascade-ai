"""
Task Recommendation System for Tascade AI.

This module implements the Task Recommendation System, which provides
personalized task recommendations based on user preferences, project
priorities, and historical data.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
from pathlib import Path

from .recommendation.base import UserPreference
from .recommendation.preference_manager import FileBasedPreferenceManager
from .recommendation.historical_analyzer import TaskPerformanceAnalyzer
from .recommendation.workload_balancer import TaskWorkloadBalancer
from .recommendation.engine import DefaultRecommendationEngine
from .recommendation.factors import (
    PriorityFactor, DeadlineFactor, DependencyFactor, 
    UserPreferenceFactor, CompletionTimeFactor, 
    HistoricalSuccessFactor, WorkloadFactor
)


class TaskRecommendationSystem:
    """Task Recommendation System for Tascade AI."""
    
    def __init__(self, 
                 task_manager=None,
                 time_tracking_system=None,
                 data_dir: str = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Task Recommendation System.
        
        Args:
            task_manager: Task Manager instance
            time_tracking_system: Time Tracking System instance
            data_dir: Directory for storing recommendation data
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger("tascade.recommendation")
        self.task_manager = task_manager
        self.time_tracking_system = time_tracking_system
        
        # Set up data directory
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data", "recommendation")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize components
        self.preference_manager = FileBasedPreferenceManager(
            data_dir=self.data_dir,
            logger=self.logger
        )
        
        self.historical_analyzer = TaskPerformanceAnalyzer(
            task_manager=self.task_manager,
            time_tracking_system=self.time_tracking_system,
            data_dir=self.data_dir,
            logger=self.logger
        )
        
        self.workload_balancer = TaskWorkloadBalancer(
            task_manager=self.task_manager,
            time_tracking_system=self.time_tracking_system,
            historical_analyzer=self.historical_analyzer,
            data_dir=self.data_dir,
            logger=self.logger
        )
        
        self.recommendation_engine = DefaultRecommendationEngine(
            user_preference_manager=self.preference_manager,
            historical_analyzer=self.historical_analyzer,
            workload_balancer=self.workload_balancer,
            task_manager=self.task_manager,
            logger=self.logger
        )
    
    def recommend_tasks(self, 
                       user_id: str, 
                       limit: int = 10, 
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get task recommendations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of recommendations
            context: Additional context
            
        Returns:
            Recommendation results
        """
        try:
            # Get all tasks from task manager
            if self.task_manager:
                all_tasks = self.task_manager.get_all_tasks()
                
                # Filter to pending tasks
                pending_tasks = [task for task in all_tasks if task.get("status", "") == "pending"]
                
                # Get recommendations
                recommendations = self.recommendation_engine.recommend_tasks(
                    tasks=pending_tasks,
                    user_id=user_id,
                    context=context,
                    limit=limit
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "recommendations": recommendations,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.error("Task manager not available")
                return {
                    "success": False,
                    "error": "Task manager not available",
                    "user_id": user_id,
                    "recommendations": [],
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "recommendations": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def set_user_preference(self, 
                          user_id: str, 
                          preference_type: str, 
                          preference_value: Any, 
                          weight: float = 1.0) -> Dict[str, Any]:
        """
        Set a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            preference_value: Value of the preference
            weight: Weight of this preference in recommendations
            
        Returns:
            Result of setting the preference
        """
        try:
            # Create preference
            preference = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                preference_value=preference_value,
                weight=weight
            )
            
            # Set preference
            success = self.preference_manager.set_preference(preference)
            
            return {
                "success": success,
                "user_id": user_id,
                "preference_type": preference_type,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "preference_type": preference_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences
        """
        try:
            # Get preferences
            preferences = self.preference_manager.get_preferences(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "preferences": [pref.to_dict() for pref in preferences],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting preferences: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "preferences": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def delete_user_preference(self, user_id: str, preference_type: str) -> Dict[str, Any]:
        """
        Delete a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference to delete
            
        Returns:
            Result of deleting the preference
        """
        try:
            # Delete preference
            success = self.preference_manager.delete_preference(user_id, preference_type)
            
            return {
                "success": success,
                "user_id": user_id,
                "preference_type": preference_type,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error deleting preference: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "preference_type": preference_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def record_task_completion(self, 
                             user_id: str, 
                             task_id: str, 
                             task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a task completion for analysis.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            task_data: Task data
            
        Returns:
            Result of recording the completion
        """
        try:
            # Record completion
            success = self.historical_analyzer.record_task_completion(
                user_id=user_id,
                task_id=task_id,
                task_data=task_data
            )
            
            return {
                "success": success,
                "user_id": user_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error recording task completion: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_user_performance(self, 
                           user_id: str, 
                           start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get user performance analysis.
        
        Args:
            user_id: User identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Performance analysis
        """
        try:
            # Get performance
            performance = self.historical_analyzer.analyze_user_performance(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "performance": performance,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting user performance: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "performance": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def set_workload_settings(self, 
                            user_id: str, 
                            daily_capacity_minutes: int = 480,
                            max_concurrent_tasks: int = 5,
                            preferred_task_size: str = "medium",
                            category_limits: Optional[Dict[str, int]] = None,
                            priority_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
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
            Result of setting workload settings
        """
        try:
            # Set workload settings
            success = self.workload_balancer.set_user_workload_settings(
                user_id=user_id,
                daily_capacity_minutes=daily_capacity_minutes,
                max_concurrent_tasks=max_concurrent_tasks,
                preferred_task_size=preferred_task_size,
                category_limits=category_limits,
                priority_weights=priority_weights
            )
            
            return {
                "success": success,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error setting workload settings: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_workload_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get workload settings for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Workload settings
        """
        try:
            # Get workload settings
            settings = self.workload_balancer.get_user_workload_settings(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "settings": settings,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting workload settings: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "settings": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def get_workload_metrics(self, user_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get workload metrics for a user.
        
        Args:
            user_id: User identifier
            tasks: Tasks to calculate metrics for
            
        Returns:
            Workload metrics
        """
        try:
            # Get workload metrics
            metrics = self.workload_balancer.calculate_workload_metrics(user_id, tasks)
            
            return {
                "success": True,
                "user_id": user_id,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting workload metrics: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "metrics": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def explain_recommendation(self, 
                             user_id: str, 
                             task_id: str, 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Explain why a task was recommended.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            context: Additional context
            
        Returns:
            Explanation of recommendation
        """
        try:
            # Get task from task manager
            if self.task_manager:
                task = self.task_manager.get_task(task_id)
                
                if task:
                    # Get explanation
                    explanation = self.recommendation_engine.explain_recommendation(
                        task=task,
                        user_id=user_id,
                        context=context
                    )
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "task_id": task_id,
                        "explanation": explanation,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Task not found: {task_id}",
                        "user_id": user_id,
                        "task_id": task_id,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                self.logger.error("Task manager not available")
                return {
                    "success": False,
                    "error": "Task manager not available",
                    "user_id": user_id,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error explaining recommendation: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_task_completion_patterns(self, 
                                   user_id: str, 
                                   task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get task completion patterns for a user.
        
        Args:
            user_id: User identifier
            task_type: Optional task type filter
            
        Returns:
            Task completion patterns
        """
        try:
            # Get task completion patterns
            patterns = self.historical_analyzer.get_task_completion_patterns(
                user_id=user_id,
                task_type=task_type
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "patterns": patterns,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting task completion patterns: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "patterns": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def predict_task_completion_time(self, 
                                   user_id: str, 
                                   task_id: str) -> Dict[str, Any]:
        """
        Predict completion time for a task.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            
        Returns:
            Prediction results
        """
        try:
            # Get task from task manager
            if self.task_manager:
                task = self.task_manager.get_task(task_id)
                
                if task:
                    # Get prediction
                    prediction = self.historical_analyzer.predict_completion_time(
                        task=task,
                        user_id=user_id
                    )
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "task_id": task_id,
                        "prediction": prediction,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Task not found: {task_id}",
                        "user_id": user_id,
                        "task_id": task_id,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                self.logger.error("Task manager not available")
                return {
                    "success": False,
                    "error": "Task manager not available",
                    "user_id": user_id,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error predicting task completion time: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
