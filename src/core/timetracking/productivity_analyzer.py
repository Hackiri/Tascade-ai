"""
Productivity Analyzer for the Task Time Tracking system.

This module implements the Productivity Analyzer component, which analyzes
time tracking data to identify productivity patterns and provide insights.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
import logging
import statistics
from collections import defaultdict

from .models import TimeEntry, TimeEstimate, TimeEntryStatus, TimeEntryType
from .entry_manager import TimeEntryManager
from .estimate_manager import TimeEstimateManager


class ProductivityMetrics:
    """Container for productivity metrics."""
    
    def __init__(self):
        """Initialize productivity metrics."""
        # Time distribution
        self.total_tracked_time = timedelta(0)
        self.focus_time = timedelta(0)
        self.break_time = timedelta(0)
        
        # Efficiency metrics
        self.focus_percentage = 0.0
        self.task_switching_count = 0
        self.avg_session_duration = timedelta(0)
        self.longest_session = timedelta(0)
        
        # Estimation accuracy
        self.estimation_accuracy = 0.0
        self.overestimation_percentage = 0.0
        self.underestimation_percentage = 0.0
        
        # Productivity score (0-100)
        self.productivity_score = 0
        
        # Additional metrics
        self.metrics: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "total_tracked_time_seconds": self.total_tracked_time.total_seconds(),
            "focus_time_seconds": self.focus_time.total_seconds(),
            "break_time_seconds": self.break_time.total_seconds(),
            "focus_percentage": self.focus_percentage,
            "task_switching_count": self.task_switching_count,
            "avg_session_duration_seconds": self.avg_session_duration.total_seconds(),
            "longest_session_seconds": self.longest_session.total_seconds(),
            "estimation_accuracy": self.estimation_accuracy,
            "overestimation_percentage": self.overestimation_percentage,
            "underestimation_percentage": self.underestimation_percentage,
            "productivity_score": self.productivity_score,
            **self.metrics
        }


class ProductivityInsight:
    """Represents an insight derived from productivity analysis."""
    
    def __init__(self, 
                 insight_type: str,
                 description: str,
                 confidence: float,
                 supporting_data: Optional[Dict[str, Any]] = None,
                 recommendation: Optional[str] = None):
        """
        Initialize a productivity insight.
        
        Args:
            insight_type: Type of insight
            description: Description of the insight
            confidence: Confidence level (0.0-1.0)
            supporting_data: Data supporting the insight
            recommendation: Optional recommendation based on the insight
        """
        self.insight_type = insight_type
        self.description = description
        self.confidence = confidence
        self.supporting_data = supporting_data or {}
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert insight to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "type": self.insight_type,
            "description": self.description,
            "confidence": self.confidence,
            "supporting_data": self.supporting_data,
            "recommendation": self.recommendation
        }


class ProductivityAnalyzer:
    """Analyzes time tracking data to identify productivity patterns."""
    
    def __init__(self, 
                 entry_manager: TimeEntryManager,
                 estimate_manager: Optional[TimeEstimateManager] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the productivity analyzer.
        
        Args:
            entry_manager: Time entry manager
            estimate_manager: Optional time estimate manager
            logger: Optional logger
        """
        self.entry_manager = entry_manager
        self.estimate_manager = estimate_manager
        self.logger = logger or logging.getLogger("tascade.timetracking.productivity")
    
    def analyze_productivity(self, 
                            user_id: Optional[str] = None,
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None,
                            task_ids: Optional[List[str]] = None) -> Tuple[ProductivityMetrics, List[ProductivityInsight]]:
        """
        Analyze productivity for a user within a date range.
        
        Args:
            user_id: Optional user identifier
            start_date: Optional start date
            end_date: Optional end date
            task_ids: Optional list of task IDs to analyze
            
        Returns:
            Tuple of (metrics, insights)
        """
        # Initialize metrics
        metrics = ProductivityMetrics()
        insights = []
        
        # Get time entries
        entries = self._get_time_entries(user_id, start_date, end_date, task_ids)
        if not entries:
            self.logger.warning("No time entries found for analysis")
            return metrics, insights
        
        # Calculate basic metrics
        self._calculate_time_distribution(entries, metrics)
        self._calculate_efficiency_metrics(entries, metrics)
        
        # Calculate estimation accuracy if estimate manager is available
        if self.estimate_manager and task_ids:
            self._calculate_estimation_accuracy(entries, task_ids, metrics)
        
        # Calculate productivity score
        self._calculate_productivity_score(metrics)
        
        # Generate insights
        insights = self._generate_insights(entries, metrics)
        
        return metrics, insights
    
    def _get_time_entries(self, 
                         user_id: Optional[str] = None,
                         start_date: Optional[date] = None,
                         end_date: Optional[date] = None,
                         task_ids: Optional[List[str]] = None) -> List[TimeEntry]:
        """
        Get time entries for analysis.
        
        Args:
            user_id: Optional user identifier
            start_date: Optional start date
            end_date: Optional end date
            task_ids: Optional list of task IDs
            
        Returns:
            List of time entries
        """
        filters = {}
        
        if user_id:
            filters["user_id"] = user_id
        
        if start_date:
            filters["start_date"] = start_date
        
        if end_date:
            filters["end_date"] = end_date
        
        if task_ids:
            filters["task_ids"] = task_ids
        
        return self.entry_manager.get_entries(filters)
    
    def _calculate_time_distribution(self, entries: List[TimeEntry], metrics: ProductivityMetrics) -> None:
        """
        Calculate time distribution metrics.
        
        Args:
            entries: List of time entries
            metrics: Metrics object to update
        """
        total_seconds = 0
        focus_seconds = 0
        break_seconds = 0
        
        for entry in entries:
            duration = entry.duration_seconds or 0
            total_seconds += duration
            
            # Determine if this is focus time or break time
            if "break" in entry.tags or "pause" in entry.tags:
                break_seconds += duration
            else:
                focus_seconds += duration
        
        metrics.total_tracked_time = timedelta(seconds=total_seconds)
        metrics.focus_time = timedelta(seconds=focus_seconds)
        metrics.break_time = timedelta(seconds=break_seconds)
        
        # Calculate focus percentage
        if total_seconds > 0:
            metrics.focus_percentage = (focus_seconds / total_seconds) * 100
    
    def _calculate_efficiency_metrics(self, entries: List[TimeEntry], metrics: ProductivityMetrics) -> None:
        """
        Calculate efficiency metrics.
        
        Args:
            entries: List of time entries
            metrics: Metrics object to update
        """
        # Sort entries by start time
        sorted_entries = sorted(entries, key=lambda e: e.start_time or datetime.min)
        
        # Calculate task switching
        if len(sorted_entries) > 1:
            current_task = sorted_entries[0].task_id
            switches = 0
            
            for entry in sorted_entries[1:]:
                if entry.task_id != current_task:
                    switches += 1
                    current_task = entry.task_id
            
            metrics.task_switching_count = switches
        
        # Calculate session durations
        session_durations = []
        for entry in entries:
            if entry.duration_seconds:
                session_durations.append(entry.duration_seconds)
        
        if session_durations:
            avg_duration = statistics.mean(session_durations)
            max_duration = max(session_durations)
            
            metrics.avg_session_duration = timedelta(seconds=avg_duration)
            metrics.longest_session = timedelta(seconds=max_duration)
            
            # Add additional metrics
            metrics.metrics["session_count"] = len(session_durations)
            metrics.metrics["session_duration_stddev"] = statistics.stdev(session_durations) if len(session_durations) > 1 else 0
    
    def _calculate_estimation_accuracy(self, 
                                      entries: List[TimeEntry], 
                                      task_ids: List[str],
                                      metrics: ProductivityMetrics) -> None:
        """
        Calculate estimation accuracy metrics.
        
        Args:
            entries: List of time entries
            task_ids: List of task IDs
            metrics: Metrics object to update
        """
        if not self.estimate_manager:
            return
        
        # Group entries by task
        task_durations = defaultdict(int)
        for entry in entries:
            if entry.task_id:
                task_durations[entry.task_id] += entry.duration_seconds or 0
        
        # Compare with estimates
        accuracy_values = []
        overestimations = 0
        underestimations = 0
        total_comparisons = 0
        
        for task_id in task_ids:
            if task_id not in task_durations:
                continue
            
            actual_duration = task_durations[task_id]
            estimates = self.estimate_manager.get_estimates(task_id)
            
            if not estimates:
                continue
            
            # Use the most recent estimate
            latest_estimate = max(estimates, key=lambda e: e.created_at)
            estimated_seconds = self._convert_estimate_to_seconds(latest_estimate)
            
            if estimated_seconds <= 0:
                continue
            
            # Calculate accuracy
            accuracy = 1.0 - min(abs(actual_duration - estimated_seconds) / estimated_seconds, 1.0)
            accuracy_values.append(accuracy)
            
            # Track over/under estimation
            if estimated_seconds > actual_duration:
                overestimations += 1
            elif estimated_seconds < actual_duration:
                underestimations += 1
            
            total_comparisons += 1
        
        # Update metrics
        if accuracy_values:
            metrics.estimation_accuracy = statistics.mean(accuracy_values) * 100
        
        if total_comparisons > 0:
            metrics.overestimation_percentage = (overestimations / total_comparisons) * 100
            metrics.underestimation_percentage = (underestimations / total_comparisons) * 100
    
    def _calculate_productivity_score(self, metrics: ProductivityMetrics) -> None:
        """
        Calculate overall productivity score.
        
        Args:
            metrics: Metrics object to update
        """
        # Define weights for different factors
        weights = {
            "focus_percentage": 0.4,
            "estimation_accuracy": 0.3,
            "task_switching": 0.2,
            "session_duration": 0.1
        }
        
        # Calculate individual scores
        focus_score = min(metrics.focus_percentage, 100)
        
        estimation_score = metrics.estimation_accuracy
        
        # Task switching score (lower is better)
        max_switches = 20  # Arbitrary maximum
        switch_ratio = min(metrics.task_switching_count / max_switches, 1.0)
        task_switching_score = 100 * (1 - switch_ratio)
        
        # Session duration score
        ideal_session = 25 * 60  # 25 minutes (pomodoro)
        if metrics.avg_session_duration.total_seconds() > 0:
            session_ratio = min(metrics.avg_session_duration.total_seconds() / ideal_session, 2.0)
            # Score peaks at 1.0 ratio, decreases for shorter or longer sessions
            if session_ratio <= 1.0:
                session_score = 100 * session_ratio
            else:
                session_score = 100 * (2.0 - session_ratio)
        else:
            session_score = 0
        
        # Calculate weighted score
        weighted_score = (
            weights["focus_percentage"] * focus_score +
            weights["estimation_accuracy"] * estimation_score +
            weights["task_switching"] * task_switching_score +
            weights["session_duration"] * session_score
        )
        
        metrics.productivity_score = round(weighted_score)
    
    def _generate_insights(self, 
                          entries: List[TimeEntry], 
                          metrics: ProductivityMetrics) -> List[ProductivityInsight]:
        """
        Generate insights based on productivity metrics.
        
        Args:
            entries: List of time entries
            metrics: Productivity metrics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Focus time insights
        if metrics.focus_percentage < 70:
            insights.append(ProductivityInsight(
                insight_type="focus_time",
                description="Your focus time is below the recommended level of 70%",
                confidence=0.8,
                supporting_data={"focus_percentage": metrics.focus_percentage},
                recommendation="Try to reduce interruptions and allocate dedicated focus blocks"
            ))
        elif metrics.focus_percentage > 90:
            insights.append(ProductivityInsight(
                insight_type="break_time",
                description="You might not be taking enough breaks",
                confidence=0.7,
                supporting_data={"focus_percentage": metrics.focus_percentage},
                recommendation="Consider incorporating short breaks to maintain productivity"
            ))
        
        # Task switching insights
        if metrics.task_switching_count > 10:
            insights.append(ProductivityInsight(
                insight_type="task_switching",
                description="You're switching between tasks frequently",
                confidence=0.8,
                supporting_data={"task_switching_count": metrics.task_switching_count},
                recommendation="Try to batch similar tasks and reduce context switching"
            ))
        
        # Session duration insights
        avg_minutes = metrics.avg_session_duration.total_seconds() / 60
        if avg_minutes < 15:
            insights.append(ProductivityInsight(
                insight_type="session_duration",
                description="Your work sessions are quite short",
                confidence=0.7,
                supporting_data={"avg_session_minutes": avg_minutes},
                recommendation="Try techniques like Pomodoro (25 min focus, 5 min break)"
            ))
        elif avg_minutes > 90:
            insights.append(ProductivityInsight(
                insight_type="session_duration",
                description="Your work sessions are very long",
                confidence=0.7,
                supporting_data={"avg_session_minutes": avg_minutes},
                recommendation="Consider breaking up long sessions with short breaks"
            ))
        
        # Estimation accuracy insights
        if metrics.estimation_accuracy < 70:
            if metrics.overestimation_percentage > metrics.underestimation_percentage:
                insights.append(ProductivityInsight(
                    insight_type="estimation",
                    description="You tend to overestimate how long tasks will take",
                    confidence=0.8,
                    supporting_data={
                        "accuracy": metrics.estimation_accuracy,
                        "overestimation": metrics.overestimation_percentage
                    },
                    recommendation="Try breaking tasks into smaller, more predictable units"
                ))
            else:
                insights.append(ProductivityInsight(
                    insight_type="estimation",
                    description="You tend to underestimate how long tasks will take",
                    confidence=0.8,
                    supporting_data={
                        "accuracy": metrics.estimation_accuracy,
                        "underestimation": metrics.underestimation_percentage
                    },
                    recommendation="Add buffer time to your estimates for unexpected complications"
                ))
        
        return insights
    
    def _convert_estimate_to_seconds(self, estimate: TimeEstimate) -> int:
        """
        Convert a time estimate to seconds.
        
        Args:
            estimate: Time estimate
            
        Returns:
            Estimated seconds
        """
        value = estimate.estimate_value
        unit = estimate.unit.lower()
        
        if estimate.estimate_type == TimeEstimateType.FIXED:
            # Convert to seconds based on unit
            if unit == "seconds":
                return int(value)
            elif unit == "minutes":
                return int(value * 60)
            elif unit == "hours":
                return int(value * 3600)
            elif unit == "days":
                return int(value * 8 * 3600)  # Assuming 8-hour workday
        
        elif estimate.estimate_type == TimeEstimateType.RANGE:
            # For range estimates, use the average
            if isinstance(value, dict) and "min" in value and "max" in value:
                avg_value = (value["min"] + value["max"]) / 2
                
                if unit == "seconds":
                    return int(avg_value)
                elif unit == "minutes":
                    return int(avg_value * 60)
                elif unit == "hours":
                    return int(avg_value * 3600)
                elif unit == "days":
                    return int(avg_value * 8 * 3600)
        
        elif estimate.estimate_type == TimeEstimateType.STORY_POINTS:
            # Convert story points to hours (assuming 1 point = 4 hours)
            return int(value * 4 * 3600)
        
        elif estimate.estimate_type == TimeEstimateType.T_SHIRT:
            # Convert t-shirt sizes to hours
            size_mapping = {
                "xs": 1,
                "s": 2,
                "m": 4,
                "l": 8,
                "xl": 16,
                "xxl": 32
            }
            
            if isinstance(value, str) and value.lower() in size_mapping:
                return size_mapping[value.lower()] * 3600
        
        # Default fallback
        return 0
