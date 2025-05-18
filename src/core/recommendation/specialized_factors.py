"""
Specialized Recommendation Factors for the Task Recommendation System.

This module implements specialized recommendation factors that enhance
the Task Recommendation System with more advanced scoring capabilities.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import logging
import re
import os

from .base import RecommendationFactor


class ContextAwarenessFactor(RecommendationFactor):
    """Factor that scores tasks based on the user's current working context."""
    
    def __init__(self, weight: float = 1.0):
        """
        Initialize a context awareness factor.
        
        Args:
            weight: Weight of this factor in the overall score (0.0-1.0)
        """
        super().__init__(weight, "ContextAwarenessFactor")
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on the user's current working context.
        
        Args:
            task: Task data
            context: Additional context (user preferences, history, etc.)
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Default score
        score = 0.5
        
        # Get current working context
        current_files = context.get("current_files", [])
        current_directory = context.get("current_directory", "")
        recent_commands = context.get("recent_commands", [])
        
        # Score based on file context
        file_context_score = self._score_file_context(task, current_files)
        
        # Score based on directory context
        directory_context_score = self._score_directory_context(task, current_directory)
        
        # Score based on command context
        command_context_score = self._score_command_context(task, recent_commands)
        
        # Combine scores
        context_scores = [
            file_context_score,
            directory_context_score,
            command_context_score
        ]
        
        # Calculate final score (average of non-zero scores)
        non_zero_scores = [s for s in context_scores if s > 0]
        if non_zero_scores:
            score = sum(non_zero_scores) / len(non_zero_scores)
        
        return score
    
    def _score_file_context(self, task: Dict[str, Any], current_files: List[str]) -> float:
        """
        Score based on the files the user is currently working with.
        
        Args:
            task: Task data
            current_files: List of files the user is currently working with
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not current_files:
            return 0.0
        
        score = 0.0
        
        # Get task-related files
        task_files = []
        
        # Extract file paths from task description
        description = task.get("description", "")
        file_patterns = [
            r'`([^`]+\.[a-zA-Z0-9]+)`',  # Files in backticks
            r'[\'"]([^\'"]+\.[a-zA-Z0-9]+)[\'"]',  # Files in quotes
            r'\b([a-zA-Z0-9_\-/\.]+\.(py|js|html|css|md|json|yaml|yml|xml|txt))\b'  # Common file extensions
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, description)
            if matches:
                if isinstance(matches[0], tuple):
                    # If the regex has groups, flatten the results
                    matches = [m[0] for m in matches]
                task_files.extend(matches)
        
        # Check for file name matches
        for task_file in task_files:
            for current_file in current_files:
                # Extract file name from path
                current_file_name = os.path.basename(current_file)
                
                if task_file == current_file_name or task_file in current_file:
                    score = 1.0
                    break
        
        # Check for directory matches
        if score < 0.5:
            for task_file in task_files:
                task_dir = os.path.dirname(task_file)
                if task_dir:
                    for current_file in current_files:
                        current_dir = os.path.dirname(current_file)
                        if task_dir in current_dir or current_dir in task_dir:
                            score = max(score, 0.7)
                            break
        
        return score
    
    def _score_directory_context(self, task: Dict[str, Any], current_directory: str) -> float:
        """
        Score based on the directory the user is currently working in.
        
        Args:
            task: Task data
            current_directory: Directory the user is currently working in
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not current_directory:
            return 0.0
        
        score = 0.0
        
        # Check if task category matches directory
        category = task.get("category", "").lower()
        if category:
            # Extract directory name from path
            dir_name = os.path.basename(current_directory).lower()
            
            # Check for direct match
            if category == dir_name:
                score = 1.0
            # Check for partial match
            elif category in dir_name or dir_name in category:
                score = 0.8
            # Check for parent directory match
            else:
                parent_dir = os.path.basename(os.path.dirname(current_directory)).lower()
                if category == parent_dir:
                    score = 0.7
                elif category in parent_dir or parent_dir in category:
                    score = 0.5
        
        return score
    
    def _score_command_context(self, task: Dict[str, Any], recent_commands: List[str]) -> float:
        """
        Score based on the commands the user has recently executed.
        
        Args:
            task: Task data
            recent_commands: List of commands the user has recently executed
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not recent_commands:
            return 0.0
        
        score = 0.0
        
        # Get task keywords
        task_keywords = []
        
        # Extract keywords from task title and description
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()
        
        # Add task category, type, and tags
        task_keywords.append(task.get("category", "").lower())
        task_keywords.append(task.get("type", "").lower())
        task_keywords.extend([tag.lower() for tag in task.get("tags", [])])
        
        # Add words from title and description
        task_keywords.extend(re.findall(r'\b[a-zA-Z]+\b', title))
        task_keywords.extend(re.findall(r'\b[a-zA-Z]+\b', description))
        
        # Remove empty strings and duplicates
        task_keywords = [kw for kw in task_keywords if kw]
        task_keywords = list(set(task_keywords))
        
        # Check for keyword matches in recent commands
        for command in recent_commands:
            command_lower = command.lower()
            for keyword in task_keywords:
                if keyword in command_lower:
                    score = max(score, 0.6)
                    
                    # Increase score for more specific matches
                    if len(keyword) > 5 and keyword in command_lower:
                        score = max(score, 0.8)
                    
                    # Check for exact command match
                    if keyword == command_lower:
                        score = 1.0
        
        return score


class CollaborationFactor(RecommendationFactor):
    """Factor that scores tasks based on collaboration requirements."""
    
    def __init__(self, weight: float = 1.0):
        """
        Initialize a collaboration factor.
        
        Args:
            weight: Weight of this factor in the overall score (0.0-1.0)
        """
        super().__init__(weight, "CollaborationFactor")
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on collaboration requirements.
        
        Args:
            task: Task data
            context: Additional context (user preferences, history, etc.)
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Default score
        score = 0.5
        
        # Get user preferences
        user_preferences = context.get("user_preferences", [])
        user_id = context.get("user_id", "")
        
        # Get collaboration preferences
        collaboration_preference = None
        for pref in user_preferences:
            if pref.get("preference_type") == "preferred_collaboration":
                collaboration_preference = pref.get("preference_value")
                break
        
        # If no preference, return default score
        if not collaboration_preference:
            return score
        
        # Get task collaboration requirements
        task_assignees = task.get("assignees", [])
        task_reviewers = task.get("reviewers", [])
        task_owner = task.get("owner", "")
        
        # Calculate collaboration score
        if collaboration_preference == "solo":
            # User prefers solo tasks
            if not task_assignees or (len(task_assignees) == 1 and user_id in task_assignees):
                score = 0.9
            else:
                score = 0.3
        elif collaboration_preference == "team":
            # User prefers team tasks
            if task_assignees and len(task_assignees) > 1:
                score = 0.9
            else:
                score = 0.4
        elif collaboration_preference == "review":
            # User prefers review tasks
            if user_id in task_reviewers:
                score = 0.9
            else:
                score = 0.5
        elif collaboration_preference == "lead":
            # User prefers to lead tasks
            if task_owner == user_id:
                score = 0.9
            else:
                score = 0.4
        
        return score


class LearningOpportunityFactor(RecommendationFactor):
    """Factor that scores tasks based on learning opportunities."""
    
    def __init__(self, weight: float = 1.0):
        """
        Initialize a learning opportunity factor.
        
        Args:
            weight: Weight of this factor in the overall score (0.0-1.0)
        """
        super().__init__(weight, "LearningOpportunityFactor")
    
    def score(self, task: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a task based on learning opportunities.
        
        Args:
            task: Task data
            context: Additional context (user preferences, history, etc.)
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Default score
        score = 0.5
        
        # Get user preferences
        user_preferences = context.get("user_preferences", [])
        
        # Get learning preferences
        learning_preference = None
        for pref in user_preferences:
            if pref.get("preference_type") == "learning_interests":
                learning_preference = pref.get("preference_value", [])
                break
        
        # If no preference, return default score
        if not learning_preference:
            return score
        
        # Get task learning opportunities
        task_tags = task.get("tags", [])
        task_category = task.get("category", "")
        task_type = task.get("type", "")
        task_description = task.get("description", "")
        
        # Calculate learning score
        matches = 0
        total_interests = len(learning_preference)
        
        for interest in learning_preference:
            # Check tags
            if interest in task_tags:
                matches += 1
                continue
            
            # Check category
            if interest.lower() == task_category.lower():
                matches += 1
                continue
            
            # Check type
            if interest.lower() == task_type.lower():
                matches += 1
                continue
            
            # Check description
            if interest.lower() in task_description.lower():
                matches += 0.5  # Partial match
                continue
        
        # Calculate score based on matches
        if total_interests > 0:
            score = min(1.0, matches / total_interests)
        
        return score
