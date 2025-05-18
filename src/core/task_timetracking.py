"""
Task Time Tracking System for Tascade AI.

This module provides functionality for tracking time spent on tasks,
including time entries, estimates, reports, and analytics.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging

from src.core.timetracking.models import (
    TimeEntry, TimeEstimate, TimeEntryStatus, TimeEntryType,
    TimeEstimateType, TimeTrackingSettings
)
from src.core.timetracking.entry_manager import TimeEntryManager
from src.core.timetracking.estimate_manager import TimeEstimateManager
from src.core.timetracking.reporting import TimeTrackingReport, ReportType, ReportFormat
from src.core.timetracking.report_types import (
    SummaryReport, DailyReport, TaskReport, EstimateComparisonReport
)


class TaskTimeTrackingSystem:
    """Task Time Tracking System for Tascade AI."""
    
    def __init__(self, 
                 task_manager=None,
                 data_dir: str = None,
                 settings: Optional[TimeTrackingSettings] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Task Time Tracking System.
        
        Args:
            task_manager: Task Manager instance
            data_dir: Directory for storing time tracking data
            settings: Time tracking settings
            logger: Optional logger
        """
        self.task_manager = task_manager
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.settings = settings or TimeTrackingSettings()
        self.logger = logger or logging.getLogger("tascade.timetracking")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize managers
        self.entry_manager = TimeEntryManager(
            data_dir=self.data_dir,
            settings=self.settings,
            logger=self.logger
        )
        
        self.estimate_manager = TimeEstimateManager(
            data_dir=self.data_dir,
            logger=self.logger
        )
    
    # Time Entry Methods
    
    def create_time_entry(self, 
                         task_id: str,
                         description: str = "",
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         duration_seconds: Optional[int] = None,
                         status: str = "completed",
                         type: str = "manual",
                         user_id: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         billable: Optional[bool] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new time entry.
        
        Args:
            task_id: Task identifier
            description: Description of work done
            start_time: When the time entry started
            end_time: When the time entry ended
            duration_seconds: Duration in seconds (alternative to end_time)
            status: Status of the time entry
            type: Type of time entry
            user_id: User identifier
            tags: Tags for categorization
            billable: Whether the time is billable
            metadata: Additional metadata
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Validate task existence if task manager is available
            if self.task_manager and not self.task_manager.get_task(task_id):
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }
            
            # Convert string enums to enum values
            entry_status = TimeEntryStatus(status)
            entry_type = TimeEntryType(type)
            
            # Create entry
            entry_id = self.entry_manager.create_entry(
                task_id=task_id,
                description=description,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                status=entry_status,
                type=entry_type,
                user_id=user_id,
                tags=tags,
                billable=billable,
                metadata=metadata
            )
            
            # Get created entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None
            }
        except Exception as e:
            self.logger.error(f"Error creating time entry: {e}")
            return {
                "success": False,
                "error": str(e)
                }
    
    # Time Estimate Methods
    
    def create_time_estimate(self, 
                           task_id: str,
                           estimate_type: str = "fixed",
                           estimate_value: Union[int, float, str, Dict[str, Any]] = 0,
                           unit: str = "hours",
                           created_by: Optional[str] = None,
                           confidence: Optional[int] = None,
                           notes: str = "",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new time estimate.
        
        Args:
            task_id: Task identifier
            estimate_type: Type of estimate
            estimate_value: Estimated value (format depends on type)
            unit: Unit of measurement (hours, days, etc.)
            created_by: User who created the estimate
            confidence: Confidence level (0-100)
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Validate task existence if task manager is available
            if self.task_manager and not self.task_manager.get_task(task_id):
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }
            
            # Convert string enum to enum value
            est_type = TimeEstimateType(estimate_type)
            
            # Create estimate
            estimate_id = self.estimate_manager.create_estimate(
                task_id=task_id,
                estimate_type=est_type,
                estimate_value=estimate_value,
                unit=unit,
                created_by=created_by,
                confidence=confidence,
                notes=notes,
                metadata=metadata
            )
            
            # Get created estimate
            estimate = self.estimate_manager.get_estimate(estimate_id)
            
            return {
                "success": True,
                "estimate_id": estimate_id,
                "estimate": estimate.to_dict() if estimate else None
            }
        except Exception as e:
            self.logger.error(f"Error creating time estimate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_time_estimate(self, 
                           estimate_id: str,
                           estimate_type: Optional[str] = None,
                           estimate_value: Optional[Union[int, float, str, Dict[str, Any]]] = None,
                           unit: Optional[str] = None,
                           confidence: Optional[int] = None,
                           notes: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update an existing time estimate.
        
        Args:
            estimate_id: Estimate identifier
            estimate_type: Type of estimate
            estimate_value: Estimated value (format depends on type)
            unit: Unit of measurement (hours, days, etc.)
            confidence: Confidence level (0-100)
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            Dictionary with update results
        """
        try:
            # Convert string enum to enum value if provided
            est_type = TimeEstimateType(estimate_type) if estimate_type else None
            
            # Update estimate
            success = self.estimate_manager.update_estimate(
                estimate_id=estimate_id,
                estimate_type=est_type,
                estimate_value=estimate_value,
                unit=unit,
                confidence=confidence,
                notes=notes,
                metadata=metadata
            )
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time estimate not found: {estimate_id}"
                }
            
            # Get updated estimate
            estimate = self.estimate_manager.get_estimate(estimate_id)
            
            return {
                "success": True,
                "estimate_id": estimate_id,
                "estimate": estimate.to_dict() if estimate else None
            }
        except Exception as e:
            self.logger.error(f"Error updating time estimate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_estimate(self, estimate_id: str) -> Dict[str, Any]:
        """
        Get a time estimate by ID.
        
        Args:
            estimate_id: Estimate identifier
            
        Returns:
            Dictionary with time estimate data
        """
        try:
            estimate = self.estimate_manager.get_estimate(estimate_id)
            
            if not estimate:
                return {
                    "success": False,
                    "error": f"Time estimate not found: {estimate_id}"
                }
            
            return {
                "success": True,
                "estimate": estimate.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Error getting time estimate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_estimate_for_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get the time estimate for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with time estimate data
        """
        try:
            estimate = self.estimate_manager.get_estimate_for_task(task_id)
            
            if not estimate:
                return {
                    "success": True,
                    "has_estimate": False,
                    "task_id": task_id
                }
            
            return {
                "success": True,
                "has_estimate": True,
                "estimate": estimate.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Error getting time estimate for task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_time_estimate(self, estimate_id: str) -> Dict[str, Any]:
        """
        Delete a time estimate.
        
        Args:
            estimate_id: Estimate identifier
            
        Returns:
            Dictionary with deletion results
        """
        try:
            success = self.estimate_manager.delete_estimate(estimate_id)
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time estimate not found: {estimate_id}"
                }
            
            return {
                "success": True,
                "estimate_id": estimate_id
            }
        except Exception as e:
            self.logger.error(f"Error deleting time estimate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_time_estimate_for_task(self, task_id: str) -> Dict[str, Any]:
        """
        Delete the time estimate for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with deletion results
        """
        try:
            success = self.estimate_manager.delete_estimate_for_task(task_id)
            
            if not success:
                return {
                    "success": False,
                    "error": f"No time estimate found for task: {task_id}"
                }
            
            return {
                "success": True,
                "task_id": task_id
            }
        except Exception as e:
            self.logger.error(f"Error deleting time estimate for task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def convert_time_estimate(self, estimate_id: str, target_type: str, target_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert an estimate to a different type.
        
        Args:
            estimate_id: Estimate identifier
            target_type: Target estimate type
            target_unit: Optional target unit
            
        Returns:
            Dictionary with conversion results
        """
        try:
            # Convert string enum to enum value
            est_type = TimeEstimateType(target_type)
            
            # Convert estimate
            success = self.estimate_manager.convert_estimate(
                estimate_id=estimate_id,
                target_type=est_type,
                target_unit=target_unit
            )
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time estimate not found: {estimate_id}"
                }
            
            # Get converted estimate
            estimate = self.estimate_manager.get_estimate(estimate_id)
            
            return {
                "success": True,
                "estimate_id": estimate_id,
                "estimate": estimate.to_dict() if estimate else None
            }
        except Exception as e:
            self.logger.error(f"Error converting time estimate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Reporting Methods
    
    def generate_report(self,
                       report_type: str = "summary",
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       task_ids: Optional[List[str]] = None,
                       user_ids: Optional[List[str]] = None,
                       tags: Optional[List[str]] = None,
                       include_active: bool = True,
                       include_billable_only: bool = False,
                       group_by: Optional[str] = None,
                       format: str = "json",
                       title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a time tracking report.
        
        Args:
            report_type: Type of report
            start_date: Start date for report period
            end_date: End date for report period
            task_ids: Optional list of task IDs to include
            user_ids: Optional list of user IDs to include
            tags: Optional list of tags to include
            include_active: Whether to include active entries
            include_billable_only: Whether to include only billable entries
            group_by: Optional grouping field
            format: Output format
            title: Optional report title
            
        Returns:
            Dictionary with report data
        """
        try:
            # Convert string enums to enum values
            rep_type = ReportType(report_type)
            rep_format = ReportFormat(format)
            
            # Get time entries
            # Handle multiple task_ids and user_ids by making multiple queries if needed
            entries = []
            
            if task_ids:
                # If task_ids is provided, query each task separately and combine results
                for task_id in task_ids:
                    task_entries = self.entry_manager.get_entries(
                        task_id=task_id,
                        user_id=None if user_ids else None,  # Will be filtered later if user_ids is provided
                        tags=tags,
                        start_date=start_date,
                        end_date=end_date,
                        include_deleted=False
                    )
                    entries.extend(task_entries)
            elif user_ids:
                # If only user_ids is provided, query each user separately
                for user_id in user_ids:
                    user_entries = self.entry_manager.get_entries(
                        user_id=user_id,
                        tags=tags,
                        start_date=start_date,
                        end_date=end_date,
                        include_deleted=False
                    )
                    entries.extend(user_entries)
            else:
                # No specific task_ids or user_ids, get all entries with other filters
                entries = self.entry_manager.get_entries(
                    tags=tags,
                    start_date=start_date,
                    end_date=end_date,
                    include_deleted=False
                )
                
            # Apply user_ids filter if task_ids was used for the query
            if task_ids and user_ids:
                entries = [entry for entry in entries if entry.user_id in user_ids]
            
            # Get estimates for tasks if needed
            estimates = None
            if rep_type == ReportType.ESTIMATE_COMPARISON or rep_type == ReportType.TASK:
                estimates = {}
                task_set = set(task_ids) if task_ids else set(entry.task_id for entry in entries if entry.task_id)
                
                for task_id in task_set:
                    estimate = self.estimate_manager.get_estimate_for_task(task_id)
                    if estimate:
                        estimates[task_id] = estimate
            
            # Create appropriate report type
            if rep_type == ReportType.SUMMARY:
                report = SummaryReport(
                    start_date=start_date,
                    end_date=end_date,
                    task_ids=task_ids,
                    user_ids=user_ids,
                    tags=tags,
                    include_active=include_active,
                    include_billable_only=include_billable_only,
                    group_by=group_by,
                    format=rep_format,
                    title=title,
                    logger=self.logger
                )
            elif rep_type == ReportType.DAILY:
                report = DailyReport(
                    start_date=start_date,
                    end_date=end_date,
                    task_ids=task_ids,
                    user_ids=user_ids,
                    tags=tags,
                    include_active=include_active,
                    include_billable_only=include_billable_only,
                    group_by=group_by,
                    format=rep_format,
                    title=title,
                    logger=self.logger
                )
            elif rep_type == ReportType.TASK:
                report = TaskReport(
                    start_date=start_date,
                    end_date=end_date,
                    task_ids=task_ids,
                    user_ids=user_ids,
                    tags=tags,
                    include_active=include_active,
                    include_billable_only=include_billable_only,
                    group_by=group_by,
                    format=rep_format,
                    title=title,
                    logger=self.logger
                )
            elif rep_type == ReportType.ESTIMATE_COMPARISON:
                report = EstimateComparisonReport(
                    start_date=start_date,
                    end_date=end_date,
                    task_ids=task_ids,
                    user_ids=user_ids,
                    tags=tags,
                    include_active=include_active,
                    include_billable_only=include_billable_only,
                    group_by=group_by,
                    format=rep_format,
                    title=title,
                    logger=self.logger
                )
            else:
                # Default to summary report
                report = SummaryReport(
                    start_date=start_date,
                    end_date=end_date,
                    task_ids=task_ids,
                    user_ids=user_ids,
                    tags=tags,
                    include_active=include_active,
                    include_billable_only=include_billable_only,
                    group_by=group_by,
                    format=rep_format,
                    title=title,
                    logger=self.logger
                )
            
            # Generate report
            report_data = report.generate(entries, estimates)
            
            # Format output if requested
            formatted_output = None
            if rep_format != ReportFormat.JSON:
                formatted_output = report.format_output()
            
            return {
                "success": True,
                "report_type": report_type,
                "report_data": report_data,
                "formatted_output": formatted_output
            }
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_estimate_to_actual(self, task_id: str) -> Dict[str, Any]:
        """
        Compare estimated time to actual time spent on a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get time entries for the task
            entries = self.entry_manager.get_entries(task_id=task_id, include_deleted=False)
            
            # Get comparison
            comparison = self.estimate_manager.compare_estimate_to_actual(task_id, entries)
            
            return {
                "success": True,
                "task_id": task_id,
                "comparison": comparison
            }
        except Exception as e:
            self.logger.error(f"Error comparing estimate to actual: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Settings Methods
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get time tracking settings.
        
        Returns:
            Dictionary with settings data
        """
        try:
            return {
                "success": True,
                "settings": self.settings.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Error getting settings: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_settings(self, 
                       default_estimate_type: Optional[str] = None,
                       default_unit: Optional[str] = None,
                       round_to_nearest: Optional[int] = None,
                       track_idle_time: Optional[bool] = None,
                       auto_pause_after_minutes: Optional[int] = None,
                       billable_by_default: Optional[bool] = None,
                       required_fields: Optional[List[str]] = None,
                       time_format: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update time tracking settings.
        
        Args:
            default_estimate_type: Default type for estimates
            default_unit: Default unit for time
            round_to_nearest: Round time entries to nearest minutes
            track_idle_time: Whether to track idle time
            auto_pause_after_minutes: Auto-pause after inactivity
            billable_by_default: Whether new entries are billable by default
            required_fields: Fields required for time entries
            time_format: Format for displaying time
            metadata: Additional metadata
            
        Returns:
            Dictionary with update results
        """
        try:
            # Create new settings object with current values
            new_settings = TimeTrackingSettings(
                default_estimate_type=TimeEstimateType(default_estimate_type) if default_estimate_type else self.settings.default_estimate_type,
                default_unit=default_unit or self.settings.default_unit,
                round_to_nearest=round_to_nearest if round_to_nearest is not None else self.settings.round_to_nearest,
                track_idle_time=track_idle_time if track_idle_time is not None else self.settings.track_idle_time,
                auto_pause_after_minutes=auto_pause_after_minutes if auto_pause_after_minutes is not None else self.settings.auto_pause_after_minutes,
                billable_by_default=billable_by_default if billable_by_default is not None else self.settings.billable_by_default,
                required_fields=required_fields or self.settings.required_fields,
                time_format=time_format or self.settings.time_format,
                metadata=metadata or self.settings.metadata
            )
            
            # Update settings
            self.settings = new_settings
            self.entry_manager.update_settings(new_settings)
            
            return {
                "success": True,
                "settings": new_settings.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Analytics Methods
    
    def get_time_by_day(self, 
                       task_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get time grouped by day.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            tags: Filter by tags
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary with time by day
        """
        try:
            time_by_day = self.entry_manager.get_time_by_day(
                task_id=task_id,
                user_id=user_id,
                tags=tags,
                start_date=start_date,
                end_date=end_date
            )
            
            # Convert timedeltas to seconds for JSON serialization
            result = {}
            for day, duration in time_by_day.items():
                result[day] = {
                    "seconds": int(duration.total_seconds()),
                    "hours": round(duration.total_seconds() / 3600, 2),
                    "formatted": self._format_duration(int(duration.total_seconds()))
                }
            
            return {
                "success": True,
                "time_by_day": result
            }
        except Exception as e:
            self.logger.error(f"Error getting time by day: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_by_task(self, 
                        user_id: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get time grouped by task.
        
        Args:
            user_id: Filter by user ID
            tags: Filter by tags
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary with time by task
        """
        try:
            time_by_task = self.entry_manager.get_time_by_task(
                user_id=user_id,
                tags=tags,
                start_date=start_date,
                end_date=end_date
            )
            
            # Convert timedeltas to seconds for JSON serialization
            result = {}
            for task_id, duration in time_by_task.items():
                result[task_id] = {
                    "seconds": int(duration.total_seconds()),
                    "hours": round(duration.total_seconds() / 3600, 2),
                    "formatted": self._format_duration(int(duration.total_seconds()))
                }
            
            return {
                "success": True,
                "time_by_task": result
            }
        except Exception as e:
            self.logger.error(f"Error getting time by task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_by_tag(self, 
                       task_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get time grouped by tag.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary with time by tag
        """
        try:
            time_by_tag = self.entry_manager.get_time_by_tag(
                task_id=task_id,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Convert timedeltas to seconds for JSON serialization
            result = {}
            for tag, duration in time_by_tag.items():
                result[tag] = {
                    "seconds": int(duration.total_seconds()),
                    "hours": round(duration.total_seconds() / 3600, 2),
                    "formatted": self._format_duration(int(duration.total_seconds()))
                }
            
            return {
                "success": True,
                "time_by_tag": result
            }
        except Exception as e:
            self.logger.error(f"Error getting time by tag: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds as HH:MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def update_time_entry(self, 
                         entry_id: str,
                         task_id: Optional[str] = None,
                         description: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         duration_seconds: Optional[int] = None,
                         status: Optional[str] = None,
                         type: Optional[str] = None,
                         user_id: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         billable: Optional[bool] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update an existing time entry.
        
        Args:
            entry_id: Entry identifier
            task_id: Task identifier
            description: Description of work done
            start_time: When the time entry started
            end_time: When the time entry ended
            duration_seconds: Duration in seconds (alternative to end_time)
            status: Status of the time entry
            type: Type of time entry
            user_id: User identifier
            tags: Tags for categorization
            billable: Whether the time is billable
            metadata: Additional metadata
            
        Returns:
            Dictionary with update results
        """
        try:
            # Validate task existence if task manager is available and task_id is provided
            if self.task_manager and task_id and not self.task_manager.get_task(task_id):
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }
            
            # Convert string enums to enum values if provided
            entry_status = TimeEntryStatus(status) if status else None
            entry_type = TimeEntryType(type) if type else None
            
            # Update entry
            success = self.entry_manager.update_entry(
                entry_id=entry_id,
                task_id=task_id,
                description=description,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                status=entry_status,
                type=entry_type,
                user_id=user_id,
                tags=tags,
                billable=billable,
                metadata=metadata
            )
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time entry not found: {entry_id}"
                }
            
            # Get updated entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None
            }
        except Exception as e:
            self.logger.error(f"Error updating time entry: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Get a time entry by ID.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            Dictionary with time entry data
        """
        try:
            entry = self.entry_manager.get_entry(entry_id)
            
            if not entry:
                return {
                    "success": False,
                    "error": f"Time entry not found: {entry_id}"
                }
            
            return {
                "success": True,
                "entry": entry.to_dict()
            }
        except Exception as e:
            self.logger.error(f"Error getting time entry: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_time_entries_for_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get time entries for a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with time entries for the task
        """
        return self.get_time_entries(task_id=task_id)
    
    def get_time_entries_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get time entries for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with time entries for the user
        """
        return self.get_time_entries(user_id=user_id)
    
    def get_time_entries(self, 
                        task_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        status: Optional[str] = None,
                        type: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        billable: Optional[bool] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        include_deleted: bool = False) -> Dict[str, Any]:
        """
        Get time entries, optionally filtered.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            status: Filter by status
            type: Filter by type
            tags: Filter by tags
            billable: Filter by billable flag
            start_date: Filter by start date
            end_date: Filter by end date
            include_deleted: Whether to include deleted entries
            
        Returns:
            Dictionary with time entries
        """
        try:
            # Convert string enums to enum values if provided
            entry_status = TimeEntryStatus(status) if status else None
            entry_type = TimeEntryType(type) if type else None
            
            # Get entries
            entries = self.entry_manager.get_entries(
                task_id=task_id,
                user_id=user_id,
                status=entry_status,
                type=entry_type,
                tags=tags,
                billable=billable,
                start_date=start_date,
                end_date=end_date,
                include_deleted=include_deleted
            )
            
            return {
                "success": True,
                "entries": [entry.to_dict() for entry in entries],
                "count": len(entries)
            }
        except Exception as e:
            self.logger.error(f"Error getting time entries: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_time_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Delete a time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            Dictionary with deletion results
        """
        try:
            success = self.entry_manager.delete_entry(entry_id)
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time entry not found: {entry_id}"
                }
            
            return {
                "success": True,
                "entry_id": entry_id
            }
        except Exception as e:
            self.logger.error(f"Error deleting time entry: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_timer(self, 
                   task_id: str,
                   description: str = "",
                   user_id: Optional[str] = None,
                   tags: Optional[List[str]] = None,
                   billable: Optional[bool] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a timer for a task.
        
        Args:
            task_id: Task identifier
            description: Description of work done
            user_id: User identifier
            tags: Tags for categorization
            billable: Whether the time is billable
            metadata: Additional metadata
            
        Returns:
            Dictionary with timer results
        """
        try:
            # Validate task existence if task manager is available
            if self.task_manager and not self.task_manager.get_task(task_id):
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }
            
            # Start timer
            entry_id = self.entry_manager.start_timer(
                task_id=task_id,
                description=description,
                user_id=user_id,
                tags=tags,
                billable=billable,
                metadata=metadata
            )
            
            # Get created entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None,
                "started_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error starting timer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_timer(self, entry_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop a timer.
        
        Args:
            entry_id: Entry identifier (optional, uses active timer if not provided)
            
        Returns:
            Dictionary with timer results
        """
        try:
            # If entry_id is provided, stop that specific timer
            # Otherwise, stop the active timer
            if entry_id:
                success = self.entry_manager.stop_timer(entry_id)
                if not success:
                    return {
                        "success": False,
                        "error": f"Time entry not found or not active: {entry_id}"
                    }
            else:
                # Stop the active timer
                entry_id = self.entry_manager.stop_timer()
                
                if not entry_id:
                    return {
                        "success": False,
                        "error": "No active timer to stop"
                    }
            
            # Get stopped entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None,
                "stopped_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error stopping timer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def pause_timer(self, entry_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Pause a time entry.
        
        Args:
            entry_id: Entry identifier (optional, uses active timer if not provided)
            
        Returns:
            Dictionary with pause results
        """
        try:
            # If no entry ID provided, use active timer
            if not entry_id:
                active_entry = self.entry_manager.get_active_entry()
                if not active_entry:
                    return {
                        "success": False,
                        "error": "No active timer to pause"
                    }
                entry_id = active_entry.id
            
            # Pause entry
            success = self.entry_manager.pause_entry(entry_id)
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time entry not found: {entry_id}"
                }
            
            # Get paused entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None,
                "paused_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error pausing timer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def resume_timer(self, entry_id: str) -> Dict[str, Any]:
        """
        Resume a paused time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            Dictionary with resume results
        """
        try:
            # Resume entry
            success = self.entry_manager.resume_entry(entry_id)
            
            if not success:
                return {
                    "success": False,
                    "error": f"Time entry not found: {entry_id}"
                }
            
            # Get resumed entry
            entry = self.entry_manager.get_entry(entry_id)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": entry.to_dict() if entry else None,
                "resumed_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error resuming timer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_active_timer(self) -> Dict[str, Any]:
        """
        Get the active timer.
        
        Returns:
            Dictionary with active timer data
        """
        try:
            entry = self.entry_manager.get_active_entry()
            
            if not entry:
                return {
                    "success": True,
                    "has_active_timer": False
                }
            
            return {
                "success": True,
                "has_active_timer": True,
                "entry_id": entry.id,
                "entry": entry.to_dict(),
                "running_for_seconds": entry.duration.total_seconds() if entry.duration else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting active timer: {e}")
            return {
                "success": False,
                "error": str(e)
            }