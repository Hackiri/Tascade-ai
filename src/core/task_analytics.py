"""
Task Analytics System for Tascade AI.

This module provides comprehensive analytics and reporting capabilities for task data,
including performance metrics, trend analysis, and data visualization.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import statistics
from enum import Enum
import math
import csv
from io import StringIO
import os
from pathlib import Path

from .models import Task, TaskStatus, TaskPriority


class AnalyticsTimeFrame(Enum):
    """Time frames for analytics reports."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL = "all"


class AnalyticsMetricType(Enum):
    """Types of analytics metrics."""
    COMPLETION_RATE = "completion_rate"
    AVERAGE_DURATION = "average_duration"
    TASK_DISTRIBUTION = "task_distribution"
    COMPLEXITY_DISTRIBUTION = "complexity_distribution"
    DEPENDENCY_DEPTH = "dependency_depth"
    EXECUTION_EFFICIENCY = "execution_efficiency"
    STATUS_BREAKDOWN = "status_breakdown"
    PRIORITY_BREAKDOWN = "priority_breakdown"


class TaskAnalytics:
    """Task Analytics System for generating insights from task data."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Task Analytics system.
        
        Args:
            data_dir: Optional directory for storing analytics data
        """
        self.data_dir = data_dir
        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
    
    def calculate_completion_rate(self, tasks: List[Task], 
                                timeframe: AnalyticsTimeFrame = AnalyticsTimeFrame.ALL) -> Dict[str, Any]:
        """
        Calculate task completion rate metrics.
        
        Args:
            tasks: List of tasks to analyze
            timeframe: Time frame for the analysis
            
        Returns:
            Dictionary with completion rate metrics
        """
        # Filter tasks by timeframe
        filtered_tasks = self._filter_by_timeframe(tasks, timeframe)
        
        # Count tasks by status
        total_tasks = len(filtered_tasks)
        if total_tasks == 0:
            return {
                "completion_rate": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "pending_tasks": 0,
                "timeframe": timeframe.value
            }
        
        completed_tasks = sum(1 for task in filtered_tasks if task.status == TaskStatus.DONE)
        in_progress_tasks = sum(1 for task in filtered_tasks if task.status == TaskStatus.IN_PROGRESS)
        pending_tasks = sum(1 for task in filtered_tasks if task.status == TaskStatus.PENDING)
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        return {
            "completion_rate": round(completion_rate, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "timeframe": timeframe.value
        }
    
    def calculate_average_duration(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Calculate average task duration metrics.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary with duration metrics
        """
        # Filter for completed tasks with duration data
        completed_tasks = [
            task for task in tasks 
            if task.status == TaskStatus.DONE and 
            task.completed_at and task.started_at
        ]
        
        if not completed_tasks:
            return {
                "average_duration_hours": 0,
                "median_duration_hours": 0,
                "min_duration_hours": 0,
                "max_duration_hours": 0,
                "total_tasks_analyzed": 0
            }
        
        # Calculate durations in hours
        durations = []
        for task in completed_tasks:
            if task.completed_at and task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds() / 3600
                durations.append(duration)
        
        if not durations:
            return {
                "average_duration_hours": 0,
                "median_duration_hours": 0,
                "min_duration_hours": 0,
                "max_duration_hours": 0,
                "total_tasks_analyzed": 0
            }
        
        # Calculate statistics
        avg_duration = statistics.mean(durations)
        median_duration = statistics.median(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        return {
            "average_duration_hours": round(avg_duration, 2),
            "median_duration_hours": round(median_duration, 2),
            "min_duration_hours": round(min_duration, 2),
            "max_duration_hours": round(max_duration, 2),
            "total_tasks_analyzed": len(completed_tasks)
        }
    
    def analyze_task_distribution(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Analyze task distribution by various attributes.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary with task distribution metrics
        """
        # Status distribution
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for task in tasks if task.status == status)
        
        # Priority distribution
        priority_counts = {}
        for priority in TaskPriority:
            priority_counts[priority.value] = sum(1 for task in tasks if task.priority == priority)
        
        # Dependency distribution
        dependency_counts = {
            "no_dependencies": sum(1 for task in tasks if not task.dependencies),
            "1_dependency": sum(1 for task in tasks if len(task.dependencies) == 1),
            "2_dependencies": sum(1 for task in tasks if len(task.dependencies) == 2),
            "3+_dependencies": sum(1 for task in tasks if len(task.dependencies) >= 3)
        }
        
        # Subtask distribution
        subtask_counts = {
            "no_subtasks": sum(1 for task in tasks if not getattr(task, "subtasks", [])),
            "1_subtask": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) == 1),
            "2_subtasks": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) == 2),
            "3+_subtasks": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) >= 3)
        }
        
        return {
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "dependency_distribution": dependency_counts,
            "subtask_distribution": subtask_counts,
            "total_tasks": len(tasks)
        }
    
    def analyze_execution_efficiency(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Analyze task execution efficiency based on execution logs.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary with execution efficiency metrics
        """
        # Filter for tasks with execution data
        executed_tasks = [
            task for task in tasks 
            if hasattr(task, "execution_context") and 
            task.execution_context and 
            "logs" in task.execution_context
        ]
        
        if not executed_tasks:
            return {
                "average_steps_per_task": 0,
                "average_execution_time_hours": 0,
                "execution_success_rate": 0,
                "tasks_analyzed": 0
            }
        
        # Calculate metrics
        total_steps = 0
        total_execution_time = 0
        successful_executions = 0
        
        for task in executed_tasks:
            # Count execution steps
            logs = task.execution_context.get("logs", [])
            steps = set()
            for log in logs:
                if "step_name" in log:
                    steps.add(log["step_name"])
            total_steps += len(steps)
            
            # Calculate execution time
            if "execution_summary" in task.execution_context:
                summary = task.execution_context["execution_summary"]
                if "duration" in summary:
                    # Convert seconds to hours
                    total_execution_time += summary["duration"] / 3600
                
                # Count successful executions
                if summary.get("success", False):
                    successful_executions += 1
        
        # Calculate averages
        avg_steps = total_steps / len(executed_tasks) if executed_tasks else 0
        avg_execution_time = total_execution_time / len(executed_tasks) if executed_tasks else 0
        success_rate = (successful_executions / len(executed_tasks)) * 100 if executed_tasks else 0
        
        return {
            "average_steps_per_task": round(avg_steps, 2),
            "average_execution_time_hours": round(avg_execution_time, 2),
            "execution_success_rate": round(success_rate, 2),
            "tasks_analyzed": len(executed_tasks)
        }
    
    def calculate_dependency_metrics(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Calculate metrics related to task dependencies.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dictionary with dependency metrics
        """
        # Create task lookup dictionary
        task_dict = {task.id: task for task in tasks}
        
        # Calculate dependency depths
        depths = []
        for task in tasks:
            depth = self._calculate_dependency_depth(task.id, task_dict)
            depths.append(depth)
        
        if not depths:
            return {
                "average_dependency_depth": 0,
                "max_dependency_depth": 0,
                "tasks_with_dependencies": 0,
                "total_dependencies": 0,
                "tasks_analyzed": 0
            }
        
        # Calculate metrics
        avg_depth = statistics.mean(depths) if depths else 0
        max_depth = max(depths) if depths else 0
        tasks_with_deps = sum(1 for task in tasks if task.dependencies)
        total_deps = sum(len(task.dependencies) for task in tasks)
        
        return {
            "average_dependency_depth": round(avg_depth, 2),
            "max_dependency_depth": max_depth,
            "tasks_with_dependencies": tasks_with_deps,
            "total_dependencies": total_deps,
            "tasks_analyzed": len(tasks)
        }
    
    def generate_trend_report(self, tasks: List[Task], 
                            metric_type: AnalyticsMetricType,
                            timeframes: List[AnalyticsTimeFrame]) -> Dict[str, Any]:
        """
        Generate a trend report for a specific metric over multiple timeframes.
        
        Args:
            tasks: List of tasks to analyze
            metric_type: Type of metric to analyze
            timeframes: List of timeframes to include in the trend
            
        Returns:
            Dictionary with trend data
        """
        trend_data = []
        
        for timeframe in timeframes:
            if metric_type == AnalyticsMetricType.COMPLETION_RATE:
                result = self.calculate_completion_rate(tasks, timeframe)
                trend_data.append({
                    "timeframe": timeframe.value,
                    "value": result["completion_rate"]
                })
            elif metric_type == AnalyticsMetricType.TASK_DISTRIBUTION:
                # Filter tasks for the timeframe
                filtered_tasks = self._filter_by_timeframe(tasks, timeframe)
                result = self.analyze_task_distribution(filtered_tasks)
                trend_data.append({
                    "timeframe": timeframe.value,
                    "value": result["status_distribution"]
                })
            # Add other metric types as needed
        
        return {
            "metric_type": metric_type.value,
            "trend_data": trend_data
        }
    
    def export_analytics_report(self, tasks: List[Task], 
                              format: str = "json",
                              output_path: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        Generate and export a comprehensive analytics report.
        
        Args:
            tasks: List of tasks to analyze
            format: Output format ('json' or 'csv')
            output_path: Optional path to save the report
            
        Returns:
            Report data as string or dictionary
        """
        # Generate all analytics
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "completion_metrics": self.calculate_completion_rate(tasks),
            "duration_metrics": self.calculate_average_duration(tasks),
            "distribution_metrics": self.analyze_task_distribution(tasks),
            "dependency_metrics": self.calculate_dependency_metrics(tasks),
            "execution_metrics": self.analyze_execution_efficiency(tasks)
        }
        
        # Export in the requested format
        if format.lower() == "json":
            result = json.dumps(report, indent=2)
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(result)
            return result
        
        elif format.lower() == "csv":
            # Flatten the report for CSV format
            flat_data = self._flatten_report_for_csv(report)
            
            # Write to CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            for key, value in flat_data.items():
                writer.writerow([key, value])
            
            result = output.getvalue()
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(result)
            return result
        
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'.")
    
    def generate_visualization_data(self, tasks: List[Task], 
                                  visualization_type: str) -> Dict[str, Any]:
        """
        Generate data for visualizations.
        
        Args:
            tasks: List of tasks to analyze
            visualization_type: Type of visualization ('gantt', 'burndown', 'pie', 'bar')
            
        Returns:
            Data formatted for the specified visualization
        """
        if visualization_type == "gantt":
            return self._generate_gantt_data(tasks)
        elif visualization_type == "burndown":
            return self._generate_burndown_data(tasks)
        elif visualization_type == "pie":
            return self._generate_pie_chart_data(tasks)
        elif visualization_type == "bar":
            return self._generate_bar_chart_data(tasks)
        else:
            raise ValueError(f"Unsupported visualization type: {visualization_type}")
    
    def _filter_by_timeframe(self, tasks: List[Task], 
                           timeframe: AnalyticsTimeFrame) -> List[Task]:
        """
        Filter tasks by the specified timeframe.
        
        Args:
            tasks: List of tasks to filter
            timeframe: Timeframe to filter by
            
        Returns:
            Filtered list of tasks
        """
        if timeframe == AnalyticsTimeFrame.ALL:
            return tasks
        
        now = datetime.now()
        cutoff_date = None
        
        if timeframe == AnalyticsTimeFrame.DAY:
            cutoff_date = now - timedelta(days=1)
        elif timeframe == AnalyticsTimeFrame.WEEK:
            cutoff_date = now - timedelta(days=7)
        elif timeframe == AnalyticsTimeFrame.MONTH:
            cutoff_date = now - timedelta(days=30)
        elif timeframe == AnalyticsTimeFrame.QUARTER:
            cutoff_date = now - timedelta(days=90)
        elif timeframe == AnalyticsTimeFrame.YEAR:
            cutoff_date = now - timedelta(days=365)
        
        return [
            task for task in tasks 
            if task.created_at and task.created_at >= cutoff_date
        ]
    
    def _calculate_dependency_depth(self, task_id: str, 
                                  task_dict: Dict[str, Task], 
                                  visited: Optional[set] = None) -> int:
        """
        Calculate the dependency depth for a task.
        
        Args:
            task_id: ID of the task to calculate depth for
            task_dict: Dictionary mapping task IDs to Task objects
            visited: Set of visited task IDs (for cycle detection)
            
        Returns:
            Dependency depth (integer)
        """
        if visited is None:
            visited = set()
        
        # Check for cycles
        if task_id in visited:
            return 0
        
        visited.add(task_id)
        
        task = task_dict.get(task_id)
        if not task or not task.dependencies:
            return 0
        
        # Calculate max depth of dependencies
        depths = []
        for dep_id in task.dependencies:
            depth = 1 + self._calculate_dependency_depth(dep_id, task_dict, visited.copy())
            depths.append(depth)
        
        return max(depths) if depths else 0
    
    def _flatten_report_for_csv(self, report: Dict[str, Any], 
                              prefix: str = "", 
                              result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Flatten a nested report dictionary for CSV export.
        
        Args:
            report: Report dictionary to flatten
            prefix: Prefix for keys in the flattened dictionary
            result: Dictionary to store the flattened result
            
        Returns:
            Flattened dictionary
        """
        if result is None:
            result = {}
        
        for key, value in report.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_report_for_csv(value, new_key, result)
            elif isinstance(value, list):
                result[new_key] = json.dumps(value)
            else:
                result[new_key] = value
        
        return result
    
    def _generate_gantt_data(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate data for a Gantt chart visualization."""
        gantt_data = []
        
        for task in tasks:
            if task.started_at:
                start_date = task.started_at.isoformat()
                end_date = task.completed_at.isoformat() if task.completed_at else None
                
                if not end_date and task.status == TaskStatus.IN_PROGRESS:
                    # For in-progress tasks, use current time as temporary end
                    end_date = datetime.now().isoformat()
                
                if end_date:
                    gantt_data.append({
                        "id": task.id,
                        "title": task.title,
                        "start": start_date,
                        "end": end_date,
                        "status": task.status.value,
                        "dependencies": task.dependencies
                    })
        
        return {
            "chart_type": "gantt",
            "data": gantt_data
        }
    
    def _generate_burndown_data(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate data for a burndown chart visualization."""
        # Group tasks by completion date
        completion_dates = {}
        
        # Find the earliest and latest dates
        all_dates = [task.created_at for task in tasks if task.created_at]
        all_dates.extend([task.completed_at for task in tasks if task.completed_at])
        
        if not all_dates:
            return {
                "chart_type": "burndown",
                "data": []
            }
        
        start_date = min(all_dates).date()
        end_date = max(all_dates).date()
        
        # Initialize data points for each day
        current_date = start_date
        data_points = []
        remaining_tasks = len(tasks)
        
        while current_date <= end_date:
            # Count tasks completed on this date
            completed_today = sum(
                1 for task in tasks 
                if task.completed_at and task.completed_at.date() == current_date
            )
            
            remaining_tasks -= completed_today
            
            data_points.append({
                "date": current_date.isoformat(),
                "remaining_tasks": remaining_tasks
            })
            
            current_date += timedelta(days=1)
        
        return {
            "chart_type": "burndown",
            "data": data_points
        }
    
    def _generate_pie_chart_data(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate data for pie chart visualizations."""
        # Status distribution
        status_data = []
        for status in TaskStatus:
            count = sum(1 for task in tasks if task.status == status)
            if count > 0:
                status_data.append({
                    "label": status.value,
                    "value": count
                })
        
        # Priority distribution
        priority_data = []
        for priority in TaskPriority:
            count = sum(1 for task in tasks if task.priority == priority)
            if count > 0:
                priority_data.append({
                    "label": priority.value,
                    "value": count
                })
        
        return {
            "chart_type": "pie",
            "status_data": status_data,
            "priority_data": priority_data
        }
    
    def _generate_bar_chart_data(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate data for bar chart visualizations."""
        # Dependency counts
        dependency_data = [
            {"label": "0", "value": sum(1 for task in tasks if not task.dependencies)},
            {"label": "1", "value": sum(1 for task in tasks if len(task.dependencies) == 1)},
            {"label": "2", "value": sum(1 for task in tasks if len(task.dependencies) == 2)},
            {"label": "3+", "value": sum(1 for task in tasks if len(task.dependencies) >= 3)}
        ]
        
        # Subtask counts
        subtask_data = [
            {"label": "0", "value": sum(1 for task in tasks if not getattr(task, "subtasks", []))},
            {"label": "1", "value": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) == 1)},
            {"label": "2", "value": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) == 2)},
            {"label": "3+", "value": sum(1 for task in tasks if len(getattr(task, "subtasks", [])) >= 3)}
        ]
        
        return {
            "chart_type": "bar",
            "dependency_data": dependency_data,
            "subtask_data": subtask_data
        }
