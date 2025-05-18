"""
Specific report types for the Task Time Tracking system.

This module provides implementations of various time tracking reports,
including summary, daily, weekly, monthly, and comparison reports.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
import calendar
from enum import Enum
import csv
import io

from .models import TimeEntry, TimeEstimate, TimeEntryStatus, TimeEstimateType
from .reporting import TimeTrackingReport, ReportType, ReportFormat


class SummaryReport(TimeTrackingReport):
    """Summary report for time tracking."""
    
    def __init__(self, **kwargs):
        """Initialize a summary report."""
        kwargs["report_type"] = ReportType.SUMMARY
        super().__init__(**kwargs)
    
    def _generate_report_data(self, entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> None:
        """
        Generate summary report data.
        
        Args:
            entries: Filtered time entries
            estimates: Optional dictionary mapping task IDs to time estimates
        """
        # Calculate total time
        total_seconds = 0
        billable_seconds = 0
        entry_count = len(entries)
        task_ids = set()
        user_ids = set()
        tags = set()
        
        # Group entries by status
        status_counts = {}
        
        for entry in entries:
            # Get duration in seconds
            duration = entry.duration_seconds
            if duration is None:
                continue
            
            # Add to total time
            total_seconds += duration
            
            # Add to billable time if applicable
            if entry.billable:
                billable_seconds += duration
            
            # Add to task IDs
            if entry.task_id:
                task_ids.add(entry.task_id)
            
            # Add to user IDs
            if entry.user_id:
                user_ids.add(entry.user_id)
            
            # Add to tags
            for tag in entry.tags:
                tags.add(tag)
            
            # Add to status counts
            status = entry.status.value
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Calculate average time per entry
        avg_seconds_per_entry = total_seconds / entry_count if entry_count > 0 else 0
        
        # Calculate average time per task
        avg_seconds_per_task = total_seconds / len(task_ids) if task_ids else 0
        
        # Calculate billable percentage
        billable_percentage = (billable_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Add summary data
        self.data["summary"] = {
            "total_entries": entry_count,
            "total_time_seconds": total_seconds,
            "total_time_formatted": self._format_duration(total_seconds),
            "total_time_hours": round(total_seconds / 3600, 2),
            "billable_time_seconds": billable_seconds,
            "billable_time_formatted": self._format_duration(billable_seconds),
            "billable_time_hours": round(billable_seconds / 3600, 2),
            "billable_percentage": round(billable_percentage, 2),
            "unique_tasks": len(task_ids),
            "unique_users": len(user_ids),
            "unique_tags": len(tags),
            "avg_time_per_entry_seconds": round(avg_seconds_per_entry, 2),
            "avg_time_per_entry_formatted": self._format_duration(int(avg_seconds_per_entry)),
            "avg_time_per_task_seconds": round(avg_seconds_per_task, 2),
            "avg_time_per_task_formatted": self._format_duration(int(avg_seconds_per_task)),
            "status_counts": status_counts
        }
        
        # Add details
        self.data["details"] = [entry.to_dict() for entry in entries]
    
    def _format_as_text(self) -> str:
        """
        Format the summary report as plain text.
        
        Returns:
            Text formatted report
        """
        summary = self.data["summary"]
        
        lines = [
            f"Summary Report",
            f"Generated: {self.data['generated_at']}",
            f"Period: {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"Total Entries: {summary['total_entries']}",
            f"Total Time: {summary['total_time_formatted']} ({summary['total_time_hours']} hours)",
            f"Billable Time: {summary['billable_time_formatted']} ({summary['billable_time_hours']} hours)",
            f"Billable Percentage: {summary['billable_percentage']}%",
            f"Unique Tasks: {summary['unique_tasks']}",
            f"Unique Users: {summary['unique_users']}",
            f"Unique Tags: {summary['unique_tags']}",
            f"Average Time per Entry: {summary['avg_time_per_entry_formatted']}",
            f"Average Time per Task: {summary['avg_time_per_task_formatted']}",
            "",
            "Status Counts:"
        ]
        
        for status, count in summary["status_counts"].items():
            lines.append(f"  {status}: {count}")
        
        return "\n".join(lines)
    
    def _format_as_markdown(self) -> str:
        """
        Format the summary report as Markdown.
        
        Returns:
            Markdown formatted report
        """
        summary = self.data["summary"]
        
        lines = [
            f"# Summary Report",
            f"**Generated:** {self.data['generated_at']}",
            f"**Period:** {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"**Total Entries:** {summary['total_entries']}",
            f"**Total Time:** {summary['total_time_formatted']} ({summary['total_time_hours']} hours)",
            f"**Billable Time:** {summary['billable_time_formatted']} ({summary['billable_time_hours']} hours)",
            f"**Billable Percentage:** {summary['billable_percentage']}%",
            f"**Unique Tasks:** {summary['unique_tasks']}",
            f"**Unique Users:** {summary['unique_users']}",
            f"**Unique Tags:** {summary['unique_tags']}",
            f"**Average Time per Entry:** {summary['avg_time_per_entry_formatted']}",
            f"**Average Time per Task:** {summary['avg_time_per_task_formatted']}",
            "",
            "### Status Counts",
            ""
        ]
        
        for status, count in summary["status_counts"].items():
            lines.append(f"- **{status}:** {count}")
        
        return "\n".join(lines)


class DailyReport(TimeTrackingReport):
    """Daily time tracking report."""
    
    def __init__(self, **kwargs):
        """Initialize a daily report."""
        kwargs["report_type"] = ReportType.DAILY
        super().__init__(**kwargs)
    
    def _generate_report_data(self, entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> None:
        """
        Generate daily report data.
        
        Args:
            entries: Filtered time entries
            estimates: Optional dictionary mapping task IDs to time estimates
        """
        # Group entries by day
        days: Dict[str, List[TimeEntry]] = {}
        
        for entry in entries:
            if not entry.start_time:
                continue
            
            day = entry.start_time.date().isoformat()
            
            if day not in days:
                days[day] = []
            
            days[day].append(entry)
        
        # Calculate daily totals
        daily_totals = []
        
        for day, day_entries in sorted(days.items()):
            # Calculate total time for the day
            total_seconds = 0
            billable_seconds = 0
            entry_count = len(day_entries)
            task_ids = set()
            
            for entry in day_entries:
                # Get duration in seconds
                duration = entry.duration_seconds
                if duration is None:
                    continue
                
                # Add to total time
                total_seconds += duration
                
                # Add to billable time if applicable
                if entry.billable:
                    billable_seconds += duration
                
                # Add to task IDs
                if entry.task_id:
                    task_ids.add(entry.task_id)
            
            # Calculate billable percentage
            billable_percentage = (billable_seconds / total_seconds * 100) if total_seconds > 0 else 0
            
            # Add daily total
            daily_totals.append({
                "date": day,
                "entry_count": entry_count,
                "total_seconds": total_seconds,
                "total_formatted": self._format_duration(total_seconds),
                "total_hours": round(total_seconds / 3600, 2),
                "billable_seconds": billable_seconds,
                "billable_formatted": self._format_duration(billable_seconds),
                "billable_hours": round(billable_seconds / 3600, 2),
                "billable_percentage": round(billable_percentage, 2),
                "unique_tasks": len(task_ids)
            })
        
        # Calculate overall totals
        total_seconds = sum(day["total_seconds"] for day in daily_totals)
        billable_seconds = sum(day["billable_seconds"] for day in daily_totals)
        entry_count = sum(day["entry_count"] for day in daily_totals)
        billable_percentage = (billable_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Add summary data
        self.data["summary"] = {
            "total_days": len(daily_totals),
            "total_entries": entry_count,
            "total_time_seconds": total_seconds,
            "total_time_formatted": self._format_duration(total_seconds),
            "total_time_hours": round(total_seconds / 3600, 2),
            "billable_time_seconds": billable_seconds,
            "billable_time_formatted": self._format_duration(billable_seconds),
            "billable_time_hours": round(billable_seconds / 3600, 2),
            "billable_percentage": round(billable_percentage, 2),
            "avg_hours_per_day": round(total_seconds / 3600 / len(daily_totals), 2) if daily_totals else 0
        }
        
        # Add details
        self.data["details"] = daily_totals
    
    def _format_as_text(self) -> str:
        """
        Format the daily report as plain text.
        
        Returns:
            Text formatted report
        """
        summary = self.data["summary"]
        details = self.data["details"]
        
        lines = [
            f"Daily Report",
            f"Generated: {self.data['generated_at']}",
            f"Period: {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"Total Days: {summary['total_days']}",
            f"Total Entries: {summary['total_entries']}",
            f"Total Time: {summary['total_time_formatted']} ({summary['total_time_hours']} hours)",
            f"Billable Time: {summary['billable_time_formatted']} ({summary['billable_time_hours']} hours)",
            f"Billable Percentage: {summary['billable_percentage']}%",
            f"Average Hours per Day: {summary['avg_hours_per_day']}",
            "",
            "Daily Breakdown:"
        ]
        
        for day in details:
            lines.append(f"  {day['date']}: {day['total_formatted']} ({day['total_hours']} hours) - {day['entry_count']} entries")
        
        return "\n".join(lines)
    
    def _format_as_markdown(self) -> str:
        """
        Format the daily report as Markdown.
        
        Returns:
            Markdown formatted report
        """
        summary = self.data["summary"]
        details = self.data["details"]
        
        lines = [
            f"# Daily Report",
            f"**Generated:** {self.data['generated_at']}",
            f"**Period:** {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"**Total Days:** {summary['total_days']}",
            f"**Total Entries:** {summary['total_entries']}",
            f"**Total Time:** {summary['total_time_formatted']} ({summary['total_time_hours']} hours)",
            f"**Billable Time:** {summary['billable_time_formatted']} ({summary['billable_time_hours']} hours)",
            f"**Billable Percentage:** {summary['billable_percentage']}%",
            f"**Average Hours per Day:** {summary['avg_hours_per_day']}",
            "",
            "### Daily Breakdown",
            "",
            "| Date | Hours | Entries | Billable Hours | Billable % |",
            "|------|-------|---------|----------------|------------|"
        ]
        
        for day in details:
            lines.append(f"| {day['date']} | {day['total_hours']} | {day['entry_count']} | {day['billable_hours']} | {day['billable_percentage']}% |")
        
        return "\n".join(lines)


class TaskReport(TimeTrackingReport):
    """Task-based time tracking report."""
    
    def __init__(self, **kwargs):
        """Initialize a task report."""
        kwargs["report_type"] = ReportType.TASK
        super().__init__(**kwargs)
    
    def _generate_report_data(self, entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> None:
        """
        Generate task report data.
        
        Args:
            entries: Filtered time entries
            estimates: Optional dictionary mapping task IDs to time estimates
        """
        # Group entries by task
        tasks: Dict[str, List[TimeEntry]] = {}
        
        for entry in entries:
            task_id = entry.task_id or "unknown"
            
            if task_id not in tasks:
                tasks[task_id] = []
            
            tasks[task_id].append(entry)
        
        # Calculate task totals
        task_totals = []
        
        for task_id, task_entries in sorted(tasks.items()):
            # Calculate total time for the task
            total_seconds = 0
            billable_seconds = 0
            entry_count = len(task_entries)
            
            for entry in task_entries:
                # Get duration in seconds
                duration = entry.duration_seconds
                if duration is None:
                    continue
                
                # Add to total time
                total_seconds += duration
                
                # Add to billable time if applicable
                if entry.billable:
                    billable_seconds += duration
            
            # Calculate billable percentage
            billable_percentage = (billable_seconds / total_seconds * 100) if total_seconds > 0 else 0
            
            # Get estimate if available
            estimate_data = None
            if estimates and task_id in estimates:
                estimate = estimates[task_id]
                estimate_data = estimate.to_dict()
            
            # Add task total
            task_totals.append({
                "task_id": task_id,
                "entry_count": entry_count,
                "total_seconds": total_seconds,
                "total_formatted": self._format_duration(total_seconds),
                "total_hours": round(total_seconds / 3600, 2),
                "billable_seconds": billable_seconds,
                "billable_formatted": self._format_duration(billable_seconds),
                "billable_hours": round(billable_seconds / 3600, 2),
                "billable_percentage": round(billable_percentage, 2),
                "estimate": estimate_data
            })
        
        # Calculate overall totals
        total_seconds = sum(task["total_seconds"] for task in task_totals)
        billable_seconds = sum(task["billable_seconds"] for task in task_totals)
        entry_count = sum(task["entry_count"] for task in task_totals)
        billable_percentage = (billable_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Add summary data
        self.data["summary"] = {
            "total_tasks": len(task_totals),
            "total_entries": entry_count,
            "total_time_seconds": total_seconds,
            "total_time_formatted": self._format_duration(total_seconds),
            "total_time_hours": round(total_seconds / 3600, 2),
            "billable_time_seconds": billable_seconds,
            "billable_time_formatted": self._format_duration(billable_seconds),
            "billable_time_hours": round(billable_seconds / 3600, 2),
            "billable_percentage": round(billable_percentage, 2),
            "avg_hours_per_task": round(total_seconds / 3600 / len(task_totals), 2) if task_totals else 0
        }
        
        # Add details
        self.data["details"] = task_totals
    
    def _format_as_markdown(self) -> str:
        """
        Format the task report as Markdown.
        
        Returns:
            Markdown formatted report
        """
        summary = self.data["summary"]
        details = self.data["details"]
        
        lines = [
            f"# Task Report",
            f"**Generated:** {self.data['generated_at']}",
            f"**Period:** {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"**Total Tasks:** {summary['total_tasks']}",
            f"**Total Entries:** {summary['total_entries']}",
            f"**Total Time:** {summary['total_time_formatted']} ({summary['total_time_hours']} hours)",
            f"**Billable Time:** {summary['billable_time_formatted']} ({summary['billable_time_hours']} hours)",
            f"**Billable Percentage:** {summary['billable_percentage']}%",
            f"**Average Hours per Task:** {summary['avg_hours_per_task']}",
            "",
            "### Task Breakdown",
            "",
            "| Task ID | Hours | Entries | Billable Hours | Billable % | Estimate |",
            "|---------|-------|---------|----------------|------------|----------|"
        ]
        
        for task in details:
            estimate_str = task.get("estimate", {}).get("formatted_estimate", "N/A")
            lines.append(f"| {task['task_id']} | {task['total_hours']} | {task['entry_count']} | {task['billable_hours']} | {task['billable_percentage']}% | {estimate_str} |")
        
        return "\n".join(lines)


class EstimateComparisonReport(TimeTrackingReport):
    """Report comparing time estimates to actual time spent."""
    
    def __init__(self, **kwargs):
        """Initialize an estimate comparison report."""
        kwargs["report_type"] = ReportType.ESTIMATE_COMPARISON
        super().__init__(**kwargs)
    
    def _generate_report_data(self, entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> None:
        """
        Generate estimate comparison report data.
        
        Args:
            entries: Filtered time entries
            estimates: Optional dictionary mapping task IDs to time estimates
        """
        if not estimates:
            self.data["summary"] = {
                "error": "No estimates provided for comparison"
            }
            return
        
        # Group entries by task
        tasks: Dict[str, List[TimeEntry]] = {}
        
        for entry in entries:
            task_id = entry.task_id or "unknown"
            
            if task_id not in tasks:
                tasks[task_id] = []
            
            tasks[task_id].append(entry)
        
        # Calculate comparisons
        comparisons = []
        total_estimated_hours = 0
        total_actual_hours = 0
        total_variance_hours = 0
        over_estimate_count = 0
        under_estimate_count = 0
        within_range_count = 0
        
        for task_id, task_entries in sorted(tasks.items()):
            # Skip tasks without estimates
            if task_id not in estimates:
                continue
            
            estimate = estimates[task_id]
            
            # Calculate total time for the task
            total_seconds = 0
            
            for entry in task_entries:
                # Get duration in seconds
                duration = entry.duration_seconds
                if duration is None:
                    continue
                
                # Add to total time
                total_seconds += duration
            
            total_hours = total_seconds / 3600
            
            # Get estimated time in hours
            estimated_hours = 0
            estimated_min_hours = 0
            estimated_max_hours = 0
            
            if estimate.estimate_type == TimeEstimateType.FIXED:
                value = float(estimate.estimate_value)
                if estimate.unit == "hours":
                    estimated_hours = value
                elif estimate.unit == "days":
                    estimated_hours = value * 8  # Assuming 8-hour days
                elif estimate.unit == "minutes":
                    estimated_hours = value / 60
                else:
                    estimated_hours = value
            
            elif estimate.estimate_type == TimeEstimateType.RANGE:
                if isinstance(estimate.estimate_value, dict):
                    min_val = float(estimate.estimate_value.get("min", 0))
                    max_val = float(estimate.estimate_value.get("max", 0))
                    
                    if estimate.unit == "hours":
                        estimated_min_hours = min_val
                        estimated_max_hours = max_val
                        estimated_hours = (min_val + max_val) / 2
                    elif estimate.unit == "days":
                        estimated_min_hours = min_val * 8
                        estimated_max_hours = max_val * 8
                        estimated_hours = (estimated_min_hours + estimated_max_hours) / 2
                    elif estimate.unit == "minutes":
                        estimated_min_hours = min_val / 60
                        estimated_max_hours = max_val / 60
                        estimated_hours = (estimated_min_hours + estimated_max_hours) / 2
                    else:
                        estimated_min_hours = min_val
                        estimated_max_hours = max_val
                        estimated_hours = (min_val + max_val) / 2
            
            elif estimate.estimate_type == TimeEstimateType.STORY_POINTS:
                # Convert story points to hours (rough estimate)
                points = float(estimate.estimate_value)
                if points == 1:
                    estimated_hours = 1
                elif points == 2:
                    estimated_hours = 4
                elif points == 3:
                    estimated_hours = 8
                elif points == 5:
                    estimated_hours = 16
                elif points == 8:
                    estimated_hours = 32
                elif points == 13:
                    estimated_hours = 48
                else:
                    estimated_hours = points * 4  # Default conversion
            
            elif estimate.estimate_type == TimeEstimateType.T_SHIRT:
                # Convert t-shirt sizes to hours
                size = str(estimate.estimate_value).upper()
                if size == "XS":
                    estimated_hours = 2
                elif size == "S":
                    estimated_hours = 4
                elif size == "M":
                    estimated_hours = 8
                elif size == "L":
                    estimated_hours = 16
                elif size == "XL":
                    estimated_hours = 32
                elif size == "XXL":
                    estimated_hours = 48
                else:
                    estimated_hours = 8  # Default to medium
            
            # Calculate variance
            variance_hours = total_hours - estimated_hours
            variance_percentage = (variance_hours / estimated_hours * 100) if estimated_hours > 0 else 0
            
            # Determine if within range
            within_range = True
            if estimated_min_hours and estimated_max_hours:
                within_range = estimated_min_hours <= total_hours <= estimated_max_hours
            
            # Update counters
            total_estimated_hours += estimated_hours
            total_actual_hours += total_hours
            total_variance_hours += variance_hours
            
            if total_hours > estimated_hours:
                over_estimate_count += 1
            elif total_hours < estimated_hours:
                under_estimate_count += 1
            
            if within_range:
                within_range_count += 1
            
            # Add comparison
            comparisons.append({
                "task_id": task_id,
                "estimate_type": estimate.estimate_type.value,
                "estimate_value": estimate.estimate_value,
                "estimate_unit": estimate.unit,
                "estimate_formatted": estimate.formatted_estimate,
                "estimated_hours": round(estimated_hours, 2),
                "actual_seconds": total_seconds,
                "actual_hours": round(total_hours, 2),
                "variance_hours": round(variance_hours, 2),
                "variance_percentage": round(variance_percentage, 2),
                "within_range": within_range,
                "is_over_estimate": total_hours > estimated_hours,
                "is_under_estimate": total_hours < estimated_hours
            })
        
        # Calculate overall variance
        total_variance_percentage = (total_variance_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0
        accuracy_percentage = 100 - abs(total_variance_percentage) if total_estimated_hours > 0 else 0
        
        # Add summary data
        self.data["summary"] = {
            "total_tasks_with_estimates": len(comparisons),
            "total_estimated_hours": round(total_estimated_hours, 2),
            "total_actual_hours": round(total_actual_hours, 2),
            "total_variance_hours": round(total_variance_hours, 2),
            "total_variance_percentage": round(total_variance_percentage, 2),
            "estimate_accuracy_percentage": round(accuracy_percentage, 2),
            "over_estimate_count": over_estimate_count,
            "under_estimate_count": under_estimate_count,
            "within_range_count": within_range_count
        }
        
        # Add details
        self.data["details"] = comparisons
    
    def _format_as_markdown(self) -> str:
        """
        Format the estimate comparison report as Markdown.
        
        Returns:
            Markdown formatted report
        """
        summary = self.data["summary"]
        details = self.data["details"]
        
        if "error" in summary:
            return f"# Estimate Comparison Report\n\n**Error:** {summary['error']}"
        
        lines = [
            f"# Estimate Comparison Report",
            f"**Generated:** {self.data['generated_at']}",
            f"**Period:** {self.data['period']['start'] or 'All time'} to {self.data['period']['end']}",
            "",
            f"**Tasks with Estimates:** {summary['total_tasks_with_estimates']}",
            f"**Total Estimated Hours:** {summary['total_estimated_hours']}",
            f"**Total Actual Hours:** {summary['total_actual_hours']}",
            f"**Total Variance Hours:** {summary['total_variance_hours']} ({summary['total_variance_percentage']}%)",
            f"**Estimate Accuracy:** {summary['estimate_accuracy_percentage']}%",
            f"**Over Estimates:** {summary['over_estimate_count']}",
            f"**Under Estimates:** {summary['under_estimate_count']}",
            f"**Within Range:** {summary['within_range_count']}",
            "",
            "### Task Comparison",
            "",
            "| Task ID | Estimate | Est. Hours | Actual Hours | Variance | Variance % | Status |",
            "|---------|----------|------------|--------------|----------|------------|--------|"
        ]
        
        for comp in details:
            status = "✅ Within Range" if comp["within_range"] else "⚠️ Over" if comp["is_over_estimate"] else "⚠️ Under"
            lines.append(f"| {comp['task_id']} | {comp['estimate_formatted']} | {comp['estimated_hours']} | {comp['actual_hours']} | {comp['variance_hours']} | {comp['variance_percentage']}% | {status} |")
        
        return "\n".join(lines)