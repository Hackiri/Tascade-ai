"""
Historical Performance Analyzer for the Task Recommendation System.

This module implements the historical performance analysis functionality,
analyzing past task completion patterns to improve task recommendations.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
import statistics
from collections import defaultdict

from .base import HistoricalPerformanceAnalyzer


class TaskPerformanceAnalyzer(HistoricalPerformanceAnalyzer):
    """Analyzer for historical task performance."""
    
    def __init__(self, 
                 task_manager=None,
                 time_tracking_system=None,
                 data_dir: str = None,
                 performance_file: str = "performance_history.json",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a task performance analyzer.
        
        Args:
            task_manager: Task Manager instance
            time_tracking_system: Time Tracking System instance
            data_dir: Directory for storing performance data
            performance_file: File name for performance history
            logger: Optional logger
        """
        super().__init__(logger)
        self.task_manager = task_manager
        self.time_tracking_system = time_tracking_system
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.performance_file = os.path.join(self.data_dir, performance_file)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize performance history
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Load existing performance history
        self._load_performance_history()
    
    def _load_performance_history(self) -> None:
        """Load performance history from the performance file."""
        if not os.path.exists(self.performance_file):
            self.logger.info(f"Performance history file not found: {self.performance_file}")
            return
        
        try:
            with open(self.performance_file, 'r') as f:
                self.performance_history = json.load(f)
                
            self.logger.info(f"Loaded performance history for {len(self.performance_history)} users")
        except Exception as e:
            self.logger.error(f"Error loading performance history: {e}")
    
    def _save_performance_history(self) -> None:
        """Save performance history to the performance file."""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2)
                
            self.logger.info(f"Saved performance history for {len(self.performance_history)} users")
        except Exception as e:
            self.logger.error(f"Error saving performance history: {e}")
    
    def record_task_completion(self, 
                             user_id: str, 
                             task_id: str, 
                             task_data: Dict[str, Any],
                             completion_time: Optional[int] = None,
                             estimated_time: Optional[int] = None) -> bool:
        """
        Record a task completion for analysis.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            task_data: Task data
            completion_time: Actual completion time in minutes
            estimated_time: Estimated completion time in minutes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize user history if needed
            if user_id not in self.performance_history:
                self.performance_history[user_id] = []
            
            # Get completion time from time tracking system if available
            if completion_time is None and self.time_tracking_system:
                time_data = self.time_tracking_system.get_time_by_task(task_id=task_id, user_id=user_id)
                if time_data.get("success", False):
                    task_time = time_data.get("time_by_task", {}).get(task_id, {})
                    completion_time = task_time.get("seconds", 0) // 60  # Convert to minutes
            
            # Get estimated time from task data if available
            if estimated_time is None:
                estimated_time = task_data.get("estimated_time", 0)
            
            # Create completion record
            completion_record = {
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "category": task_data.get("category", ""),
                "type": task_data.get("type", ""),
                "priority": task_data.get("priority", "normal"),
                "tags": task_data.get("tags", []),
                "completion_time": completion_time,
                "estimated_time": estimated_time,
                "accuracy": self._calculate_estimation_accuracy(estimated_time, completion_time),
                "metadata": task_data.get("metadata", {})
            }
            
            # Add to history
            self.performance_history[user_id].append(completion_record)
            
            # Save history
            self._save_performance_history()
            
            return True
        except Exception as e:
            self.logger.error(f"Error recording task completion: {e}")
            return False
    
    def _calculate_estimation_accuracy(self, estimated_time: Optional[int], actual_time: Optional[int]) -> float:
        """
        Calculate estimation accuracy.
        
        Args:
            estimated_time: Estimated time in minutes
            actual_time: Actual time in minutes
            
        Returns:
            Accuracy as a percentage (0-100)
        """
        if estimated_time is None or actual_time is None or estimated_time == 0:
            return 0.0
        
        # Calculate accuracy
        accuracy = 100.0 - min(100.0, abs(actual_time - estimated_time) / estimated_time * 100.0)
        
        return max(0.0, accuracy)
    
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
        if user_id not in self.performance_history:
            return {
                "user_id": user_id,
                "task_count": 0,
                "average_accuracy": 0.0,
                "category_performance": {},
                "type_performance": {},
                "priority_performance": {},
                "tag_performance": {},
                "time_of_day_performance": {}
            }
        
        # Get user history
        history = self.performance_history[user_id]
        
        # Filter by date if specified
        if start_date or end_date:
            filtered_history = []
            for record in history:
                completed_at = datetime.fromisoformat(record["completed_at"])
                if start_date and completed_at < start_date:
                    continue
                if end_date and completed_at > end_date:
                    continue
                filtered_history.append(record)
            history = filtered_history
        
        if not history:
            return {
                "user_id": user_id,
                "task_count": 0,
                "average_accuracy": 0.0,
                "category_performance": {},
                "type_performance": {},
                "priority_performance": {},
                "tag_performance": {},
                "time_of_day_performance": {}
            }
        
        # Calculate overall metrics
        accuracies = [record["accuracy"] for record in history if "accuracy" in record]
        avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
        
        # Analyze by category
        category_performance = self._analyze_by_attribute(history, "category")
        
        # Analyze by type
        type_performance = self._analyze_by_attribute(history, "type")
        
        # Analyze by priority
        priority_performance = self._analyze_by_attribute(history, "priority")
        
        # Analyze by tag
        tag_performance = self._analyze_by_tags(history)
        
        # Analyze by time of day
        time_of_day_performance = self._analyze_by_time_of_day(history)
        
        return {
            "user_id": user_id,
            "task_count": len(history),
            "average_accuracy": avg_accuracy,
            "category_performance": category_performance,
            "type_performance": type_performance,
            "priority_performance": priority_performance,
            "tag_performance": tag_performance,
            "time_of_day_performance": time_of_day_performance
        }
    
    def _analyze_by_attribute(self, history: List[Dict[str, Any]], attribute: str) -> Dict[str, Any]:
        """
        Analyze performance by a specific attribute.
        
        Args:
            history: Task completion history
            attribute: Attribute to analyze by
            
        Returns:
            Performance analysis by attribute
        """
        performance = {}
        
        # Group by attribute
        attribute_groups = defaultdict(list)
        for record in history:
            if attribute in record:
                attribute_value = record[attribute]
                attribute_groups[attribute_value].append(record)
        
        # Calculate metrics for each attribute value
        for attr_value, records in attribute_groups.items():
            if not attr_value:  # Skip empty values
                continue
                
            accuracies = [record["accuracy"] for record in records if "accuracy" in record]
            avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
            
            completion_times = [record["completion_time"] for record in records if "completion_time" in record]
            avg_completion_time = statistics.mean(completion_times) if completion_times else 0
            
            performance[attr_value] = {
                "count": len(records),
                "average_accuracy": avg_accuracy,
                "average_completion_time": avg_completion_time
            }
        
        return performance
    
    def _analyze_by_tags(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze performance by tags.
        
        Args:
            history: Task completion history
            
        Returns:
            Performance analysis by tags
        """
        performance = {}
        
        # Group by tag
        tag_groups = defaultdict(list)
        for record in history:
            if "tags" in record and record["tags"]:
                for tag in record["tags"]:
                    tag_groups[tag].append(record)
        
        # Calculate metrics for each tag
        for tag, records in tag_groups.items():
            if not tag:  # Skip empty tags
                continue
                
            accuracies = [record["accuracy"] for record in records if "accuracy" in record]
            avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
            
            completion_times = [record["completion_time"] for record in records if "completion_time" in record]
            avg_completion_time = statistics.mean(completion_times) if completion_times else 0
            
            performance[tag] = {
                "count": len(records),
                "average_accuracy": avg_accuracy,
                "average_completion_time": avg_completion_time
            }
        
        return performance
    
    def _analyze_by_time_of_day(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze performance by time of day.
        
        Args:
            history: Task completion history
            
        Returns:
            Performance analysis by time of day
        """
        performance = {
            "morning": {"count": 0, "average_accuracy": 0.0, "average_completion_time": 0},
            "afternoon": {"count": 0, "average_accuracy": 0.0, "average_completion_time": 0},
            "evening": {"count": 0, "average_accuracy": 0.0, "average_completion_time": 0},
            "night": {"count": 0, "average_accuracy": 0.0, "average_completion_time": 0}
        }
        
        # Group by time of day
        time_groups = defaultdict(list)
        for record in history:
            if "completed_at" in record:
                completed_at = datetime.fromisoformat(record["completed_at"])
                hour = completed_at.hour
                
                if 5 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 17:
                    time_of_day = "afternoon"
                elif 17 <= hour < 22:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"
                
                time_groups[time_of_day].append(record)
        
        # Calculate metrics for each time of day
        for time_of_day, records in time_groups.items():
            accuracies = [record["accuracy"] for record in records if "accuracy" in record]
            avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
            
            completion_times = [record["completion_time"] for record in records if "completion_time" in record]
            avg_completion_time = statistics.mean(completion_times) if completion_times else 0
            
            performance[time_of_day] = {
                "count": len(records),
                "average_accuracy": avg_accuracy,
                "average_completion_time": avg_completion_time
            }
        
        return performance
    
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
        if user_id not in self.performance_history:
            return {
                "user_id": user_id,
                "task_count": 0,
                "patterns": {}
            }
        
        # Get user history
        history = self.performance_history[user_id]
        
        # Filter by task type if specified
        if task_type:
            history = [record for record in history if record.get("type") == task_type]
        
        if not history:
            return {
                "user_id": user_id,
                "task_count": 0,
                "patterns": {}
            }
        
        # Analyze completion patterns
        patterns = {
            "day_of_week": self._analyze_day_of_week_pattern(history),
            "time_of_day": self._analyze_time_of_day_pattern(history),
            "task_size": self._analyze_task_size_pattern(history),
            "sequential_tasks": self._analyze_sequential_task_pattern(history)
        }
        
        return {
            "user_id": user_id,
            "task_count": len(history),
            "patterns": patterns
        }
    
    def _analyze_day_of_week_pattern(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze completion pattern by day of week.
        
        Args:
            history: Task completion history
            
        Returns:
            Completion pattern by day of week
        """
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_counts = {day: 0 for day in days}
        
        for record in history:
            if "completed_at" in record:
                completed_at = datetime.fromisoformat(record["completed_at"])
                day = days[completed_at.weekday()]
                day_counts[day] += 1
        
        total = sum(day_counts.values())
        day_percentages = {day: (count / total * 100) if total > 0 else 0 for day, count in day_counts.items()}
        
        return {
            "counts": day_counts,
            "percentages": day_percentages,
            "preferred_days": sorted(days, key=lambda d: day_counts[d], reverse=True)
        }
    
    def _analyze_time_of_day_pattern(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze completion pattern by time of day.
        
        Args:
            history: Task completion history
            
        Returns:
            Completion pattern by time of day
        """
        times = ["morning", "afternoon", "evening", "night"]
        time_counts = {time: 0 for time in times}
        
        for record in history:
            if "completed_at" in record:
                completed_at = datetime.fromisoformat(record["completed_at"])
                hour = completed_at.hour
                
                if 5 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 17:
                    time_of_day = "afternoon"
                elif 17 <= hour < 22:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"
                
                time_counts[time_of_day] += 1
        
        total = sum(time_counts.values())
        time_percentages = {time: (count / total * 100) if total > 0 else 0 for time, count in time_counts.items()}
        
        return {
            "counts": time_counts,
            "percentages": time_percentages,
            "preferred_times": sorted(times, key=lambda t: time_counts[t], reverse=True)
        }
    
    def _analyze_task_size_pattern(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze completion pattern by task size.
        
        Args:
            history: Task completion history
            
        Returns:
            Completion pattern by task size
        """
        sizes = ["small", "medium", "large"]
        size_counts = {size: 0 for size in sizes}
        size_accuracies = {size: [] for size in sizes}
        
        for record in history:
            completion_time = record.get("completion_time", 0)
            
            # Categorize by size
            if completion_time < 30:  # Less than 30 minutes
                size = "small"
            elif completion_time < 120:  # Less than 2 hours
                size = "medium"
            else:  # 2 hours or more
                size = "large"
            
            size_counts[size] += 1
            
            if "accuracy" in record:
                size_accuracies[size].append(record["accuracy"])
        
        # Calculate average accuracy by size
        avg_accuracies = {}
        for size, accuracies in size_accuracies.items():
            avg_accuracies[size] = statistics.mean(accuracies) if accuracies else 0.0
        
        total = sum(size_counts.values())
        size_percentages = {size: (count / total * 100) if total > 0 else 0 for size, count in size_counts.items()}
        
        return {
            "counts": size_counts,
            "percentages": size_percentages,
            "average_accuracies": avg_accuracies,
            "preferred_sizes": sorted(sizes, key=lambda s: avg_accuracies[s], reverse=True)
        }
    
    def _analyze_sequential_task_pattern(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze pattern of sequential task completions.
        
        Args:
            history: Task completion history
            
        Returns:
            Sequential task pattern
        """
        # Sort history by completion time
        sorted_history = sorted(history, key=lambda r: r["completed_at"] if "completed_at" in r else "")
        
        # Analyze transitions between task types
        transitions = defaultdict(lambda: defaultdict(int))
        
        for i in range(len(sorted_history) - 1):
            current_type = sorted_history[i].get("type", "")
            next_type = sorted_history[i + 1].get("type", "")
            
            if current_type and next_type:
                transitions[current_type][next_type] += 1
        
        # Convert to regular dict
        transitions_dict = {}
        for current_type, next_types in transitions.items():
            transitions_dict[current_type] = dict(next_types)
        
        return {
            "transitions": transitions_dict
        }
    
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
        if not user_id or user_id not in self.performance_history:
            # Use task's estimated time if available
            estimated_time = task.get("estimated_time", 0)
            return {
                "task_id": task.get("id", ""),
                "user_id": user_id,
                "predicted_minutes": estimated_time,
                "confidence": 0.5,
                "basis": "task_estimate"
            }
        
        # Get user history
        history = self.performance_history[user_id]
        
        if not history:
            # Use task's estimated time if available
            estimated_time = task.get("estimated_time", 0)
            return {
                "task_id": task.get("id", ""),
                "user_id": user_id,
                "predicted_minutes": estimated_time,
                "confidence": 0.5,
                "basis": "task_estimate"
            }
        
        # Get task attributes
        task_category = task.get("category", "")
        task_type = task.get("type", "")
        task_tags = task.get("tags", [])
        task_estimate = task.get("estimated_time", 0)
        
        # Find similar tasks in history
        similar_tasks = []
        
        # By category and type
        if task_category and task_type:
            category_type_matches = [
                record for record in history 
                if record.get("category") == task_category and record.get("type") == task_type
            ]
            similar_tasks.extend(category_type_matches)
        
        # By tags
        if task_tags:
            for record in history:
                record_tags = record.get("tags", [])
                if record_tags and any(tag in task_tags for tag in record_tags):
                    similar_tasks.append(record)
        
        # Remove duplicates
        similar_tasks = list({record["task_id"]: record for record in similar_tasks}.values())
        
        if not similar_tasks:
            # Use task's estimated time if available
            return {
                "task_id": task.get("id", ""),
                "user_id": user_id,
                "predicted_minutes": task_estimate,
                "confidence": 0.5,
                "basis": "task_estimate"
            }
        
        # Calculate prediction
        completion_times = [record["completion_time"] for record in similar_tasks if "completion_time" in record]
        
        if not completion_times:
            return {
                "task_id": task.get("id", ""),
                "user_id": user_id,
                "predicted_minutes": task_estimate,
                "confidence": 0.5,
                "basis": "task_estimate"
            }
        
        # Calculate average completion time
        avg_completion_time = statistics.mean(completion_times)
        
        # Calculate confidence based on sample size and variance
        confidence = min(0.9, 0.5 + (len(completion_times) / 20))
        
        if len(completion_times) > 1:
            try:
                variance = statistics.variance(completion_times)
                normalized_variance = min(1.0, variance / (avg_completion_time + 1))
                confidence = confidence * (1.0 - normalized_variance * 0.5)
            except statistics.StatisticsError:
                pass
        
        # Blend with task estimate if available
        if task_estimate > 0:
            blended_estimate = (avg_completion_time + task_estimate) / 2
            basis = "historical_and_task_estimate"
        else:
            blended_estimate = avg_completion_time
            basis = "historical"
        
        return {
            "task_id": task.get("id", ""),
            "user_id": user_id,
            "predicted_minutes": round(blended_estimate),
            "confidence": round(confidence, 2),
            "basis": basis,
            "similar_tasks_count": len(similar_tasks)
        }
