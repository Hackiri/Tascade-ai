"""
Recommendation Engine for the Task Recommendation System.

This module implements the core recommendation engine functionality,
combining various factors to generate personalized task recommendations.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import logging
import statistics
from collections import defaultdict

from .base import RecommendationEngine, RecommendationFactor, TaskScore
from .factors import (
    PriorityFactor, DeadlineFactor, DependencyFactor, 
    UserPreferenceFactor, CompletionTimeFactor, 
    HistoricalSuccessFactor, WorkloadFactor
)
from .specialized_factors import (
    ContextAwarenessFactor, CollaborationFactor, LearningOpportunityFactor
)


class DefaultRecommendationEngine(RecommendationEngine):
    """Default implementation of the recommendation engine."""
    
    def __init__(self, 
                 factors: Optional[List[RecommendationFactor]] = None,
                 user_preference_manager=None,
                 historical_analyzer=None,
                 workload_balancer=None,
                 task_manager=None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the default recommendation engine.
        
        Args:
            factors: List of recommendation factors
            user_preference_manager: User Preference Manager instance
            historical_analyzer: Historical Performance Analyzer instance
            workload_balancer: Workload Balancer instance
            task_manager: Task Manager instance
            logger: Optional logger
        """
        super().__init__(factors, logger)
        self.user_preference_manager = user_preference_manager
        self.historical_analyzer = historical_analyzer
        self.workload_balancer = workload_balancer
        self.task_manager = task_manager
        
        # Add default factors if none provided
        if not self.factors:
            self._add_default_factors()
    
    def _add_default_factors(self) -> None:
        """Add default recommendation factors."""
        # Core factors
        self.add_factor(PriorityFactor(weight=1.0))
        self.add_factor(DeadlineFactor(weight=1.0))
        self.add_factor(DependencyFactor(weight=0.8))
        
        # User preference factors
        if self.user_preference_manager:
            self.add_factor(UserPreferenceFactor(weight=0.7))
        
        # Historical analysis factors
        if self.historical_analyzer:
            self.add_factor(HistoricalSuccessFactor(weight=0.6))
            self.add_factor(CompletionTimeFactor(weight=0.5))
        
        # Workload factors
        if self.workload_balancer:
            self.add_factor(WorkloadFactor(weight=0.5))
        
        # Specialized factors
        self.add_factor(ContextAwarenessFactor(weight=0.7))
        self.add_factor(CollaborationFactor(weight=0.6))
        self.add_factor(LearningOpportunityFactor(weight=0.5))
    
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
        if not tasks:
            return []
        
        # Initialize context if not provided
        if context is None:
            context = {}
        
        # Add user preferences to context if available
        if user_id and self.user_preference_manager:
            user_preferences = self.user_preference_manager.get_preferences(user_id)
            context["user_preferences"] = [pref.to_dict() for pref in user_preferences]
        
        # Add historical performance to context if available
        if user_id and self.historical_analyzer:
            historical_performance = self.historical_analyzer.analyze_user_performance(user_id)
            context["historical_performance"] = historical_performance
        
        # Add workload metrics to context if available
        if user_id and self.workload_balancer:
            workload_metrics = self.workload_balancer.calculate_workload_metrics(user_id, tasks)
            context["workload_metrics"] = workload_metrics
        
        # Add all tasks to context for dependency checking
        all_tasks = {task.get("id", ""): task for task in tasks}
        context["all_tasks"] = all_tasks
        
        # Score each task
        scored_tasks = []
        for task in tasks:
            task_score = self.score_task(task, user_id, context)
            scored_tasks.append({
                "task": task,
                "score": task_score.overall_score,
                "factor_scores": task_score.factor_scores,
                "timestamp": task_score.timestamp.isoformat()
            })
        
        # Sort by score (descending)
        scored_tasks.sort(key=lambda t: t["score"], reverse=True)
        
        # Apply workload balancing if available
        if user_id and self.workload_balancer:
            # Get top tasks (2x limit to give balancer more options)
            top_tasks = [t["task"] for t in scored_tasks[:limit*2]]
            
            # Balance workload
            balanced_tasks = self.workload_balancer.balance_workload(user_id, top_tasks)
            
            # If balancer returned tasks, use those
            if balanced_tasks:
                # Re-score balanced tasks to get scores
                balanced_scored_tasks = []
                for task in balanced_tasks:
                    task_score = self.score_task(task, user_id, context)
                    balanced_scored_tasks.append({
                        "task": task,
                        "score": task_score.overall_score,
                        "factor_scores": task_score.factor_scores,
                        "timestamp": task_score.timestamp.isoformat()
                    })
                
                # Sort by score (descending)
                balanced_scored_tasks.sort(key=lambda t: t["score"], reverse=True)
                
                # Limit to requested number
                return balanced_scored_tasks[:limit]
        
        # Limit to requested number
        return scored_tasks[:limit]
    
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
        # Initialize context if not provided
        if context is None:
            context = {}
        
        # Add user ID to context
        if user_id:
            context["user_id"] = user_id
        
        # Calculate scores for each factor
        factor_scores = {}
        weighted_scores = []
        
        for factor in self.factors:
            try:
                # Calculate factor score
                factor_score = factor.score(task, context)
                
                # Store factor score
                factor_scores[factor.name] = factor_score
                
                # Add weighted score
                weighted_scores.append(factor_score * factor.weight)
            except Exception as e:
                self.logger.error(f"Error calculating score for factor {factor.name}: {e}")
                factor_scores[factor.name] = 0.0
        
        # Calculate overall score
        if weighted_scores:
            total_weight = sum(factor.weight for factor in self.factors)
            overall_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.0
        
        # Create task score
        return TaskScore(
            task_id=task.get("id", ""),
            overall_score=overall_score,
            factor_scores=factor_scores,
            metadata={"user_id": user_id} if user_id else {}
        )
    
    def get_factor_weights(self) -> Dict[str, float]:
        """
        Get the weights for all factors.
        
        Returns:
            Dictionary mapping factor names to weights
        """
        return {factor.name: factor.weight for factor in self.factors}
    
    def set_factor_weight(self, factor_name: str, weight: float) -> bool:
        """
        Set the weight for a factor.
        
        Args:
            factor_name: Name of the factor
            weight: New weight
            
        Returns:
            True if successful, False otherwise
        """
        for factor in self.factors:
            if factor.name == factor_name:
                factor.weight = weight
                return True
        return False
    
    def explain_recommendation(self, 
                             task: Dict[str, Any], 
                             user_id: Optional[str] = None, 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Explain why a task was recommended.
        
        Args:
            task: Task to explain
            user_id: User to explain for
            context: Additional context
            
        Returns:
            Explanation of recommendation
        """
        # Score the task
        task_score = self.score_task(task, user_id, context)
        
        # Get top factors
        factor_scores = task_score.factor_scores
        sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create explanation
        explanation = {
            "task_id": task.get("id", ""),
            "overall_score": task_score.overall_score,
            "top_factors": sorted_factors[:3],
            "all_factors": factor_scores,
            "explanation": self._generate_explanation_text(task, sorted_factors, user_id)
        }
        
        return explanation
    
    def _generate_explanation_text(self, 
                                 task: Dict[str, Any], 
                                 sorted_factors: List[tuple], 
                                 user_id: Optional[str] = None) -> str:
        """
        Generate explanation text for a recommendation.
        
        Args:
            task: Task to explain
            sorted_factors: Sorted list of (factor_name, score) tuples
            user_id: User to explain for
            
        Returns:
            Explanation text
        """
        explanation = f"Task '{task.get('title', '')}' was recommended because:\n"
        
        # Add top factors
        for i, (factor_name, score) in enumerate(sorted_factors[:3]):
            if score > 0.7:
                strength = "strongly"
            elif score > 0.4:
                strength = "moderately"
            else:
                strength = "somewhat"
            
            if factor_name == "PriorityFactor":
                explanation += f"- It has a {strength} high priority ({task.get('priority', 'normal')})\n"
            elif factor_name == "DeadlineFactor":
                if "due_date" in task:
                    explanation += f"- It has a {strength} urgent deadline\n"
                else:
                    explanation += f"- Deadline considerations were {strength} important\n"
            elif factor_name == "DependencyFactor":
                explanation += f"- It has {strength} few or completed dependencies\n"
            elif factor_name == "UserPreferenceFactor":
                explanation += f"- It {strength} matches your preferences\n"
            elif factor_name == "HistoricalSuccessFactor":
                explanation += f"- You have {strength} succeeded with similar tasks in the past\n"
            elif factor_name == "CompletionTimeFactor":
                explanation += f"- Its estimated completion time {strength} fits your preferences\n"
            elif factor_name == "WorkloadFactor":
                explanation += f"- It {strength} helps balance your workload\n"
            elif factor_name == "ContextAwarenessFactor":
                explanation += f"- It {strength} relates to your current working context\n"
            elif factor_name == "CollaborationFactor":
                explanation += f"- It {strength} aligns with your collaboration preferences\n"
            elif factor_name == "LearningOpportunityFactor":
                explanation += f"- It {strength} provides learning opportunities in your areas of interest\n"
            else:
                explanation += f"- {factor_name}: {score:.2f}\n"
        
        return explanation
