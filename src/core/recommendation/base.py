"""
Base classes and interfaces for the Task Recommendation System.

This module defines the core interfaces and abstract classes for the
recommendation system, including the recommendation engine, scoring system,
and user preference management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import logging


class RecommendationFactor(ABC):
    """Base class for recommendation factors."""
    
    def __init__(self, weight: float = 1.0, name: str = None):
        """
        Initialize a recommendation factor.
        
        Args:
            weight: Weight of this factor in the overall score (0.0-1.0)
            name: Name of the factor
        """
        self.weight = weight
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on this factor.
        
        Args:
            task: Task data
            context: Additional context (user preferences, history, etc.)
            
        Returns:
            Score between 0.0 and 1.0
        """
        pass


class UserPreference:
    """User preference for task recommendations."""
    
    def __init__(self, 
                 user_id: str,
                 preference_type: str,
                 preference_value: Any,
                 weight: float = 1.0,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            preference_value: Value of the preference
            weight: Weight of this preference in recommendations
            created_at: When the preference was created
            updated_at: When the preference was last updated
            metadata: Additional metadata
        """
        self.user_id = user_id
        self.preference_type = preference_type
        self.preference_value = preference_value
        self.weight = weight
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "preference_type": self.preference_type,
            "preference_value": self.preference_value,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreference':
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            preference_type=data["preference_type"],
            preference_value=data["preference_value"],
            weight=data.get("weight", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
            metadata=data.get("metadata", {})
        )


class TaskScore:
    """Score for a task recommendation."""
    
    def __init__(self, 
                 task_id: str,
                 overall_score: float,
                 factor_scores: Dict[str, float],
                 timestamp: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a task score.
        
        Args:
            task_id: Task identifier
            overall_score: Overall recommendation score
            factor_scores: Scores by individual factors
            timestamp: When the score was calculated
            metadata: Additional metadata
        """
        self.task_id = task_id
        self.overall_score = overall_score
        self.factor_scores = factor_scores
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "overall_score": self.overall_score,
            "factor_scores": self.factor_scores,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskScore':
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            overall_score=data["overall_score"],
            factor_scores=data["factor_scores"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            metadata=data.get("metadata", {})
        )


class RecommendationEngine(ABC):
    """Base class for recommendation engines."""
    
    def __init__(self, factors: Optional[List[RecommendationFactor]] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize a recommendation engine.
        
        Args:
            factors: List of recommendation factors
            logger: Optional logger
        """
        self.factors = factors or []
        self.logger = logger or logging.getLogger("tascade.recommendation")
    
    @abstractmethod
    def recommend_tasks(self, 
                        tasks: List[Dict[str, Any]], 
                        user_id: Optional[str] = None, 
                        context: Optional[Dict[str, Any]] = None, 
                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recommend tasks for a user.
        
        Args:
            tasks: List of tasks to consider
            user_id: User to recommend for
            context: Additional context
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended tasks with scores
        """
        pass
    
    @abstractmethod
    def score_task(self, 
                  task: Dict[str, Any], 
                  user_id: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None) -> TaskScore:
        """
        Score a task for recommendation.
        
        Args:
            task: Task to score
            user_id: User to score for
            context: Additional context
            
        Returns:
            Task score
        """
        pass
    
    def add_factor(self, factor: RecommendationFactor) -> None:
        """
        Add a recommendation factor.
        
        Args:
            factor: Factor to add
        """
        self.factors.append(factor)
    
    def remove_factor(self, factor_name: str) -> bool:
        """
        Remove a recommendation factor.
        
        Args:
            factor_name: Name of factor to remove
            
        Returns:
            True if factor was removed, False otherwise
        """
        for i, factor in enumerate(self.factors):
            if factor.name == factor_name:
                self.factors.pop(i)
                return True
        return False


class UserPreferenceManager(ABC):
    """Base class for user preference managers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize a user preference manager.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger("tascade.recommendation")
    
    @abstractmethod
    def get_preferences(self, user_id: str) -> List[UserPreference]:
        """
        Get preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user preferences
        """
        pass
    
    @abstractmethod
    def set_preference(self, preference: UserPreference) -> bool:
        """
        Set a user preference.
        
        Args:
            preference: Preference to set
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_preference(self, user_id: str, preference_type: str) -> bool:
        """
        Delete a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass


class HistoricalPerformanceAnalyzer(ABC):
    """Base class for historical performance analyzers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize a historical performance analyzer.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger("tascade.recommendation")
    
    @abstractmethod
    def analyze_user_performance(self, 
                               user_id: str, 
                               start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyze user performance.
        
        Args:
            user_id: User identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Performance analysis results
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def predict_completion_time(self, 
                              task: Dict[str, Any], 
                              user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Predict completion time for a task.
        
        Args:
            task: Task to predict for
            user_id: User to predict for
            
        Returns:
            Prediction results
        """
        pass


class WorkloadBalancer(ABC):
    """Base class for workload balancers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize a workload balancer.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger("tascade.recommendation")
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
