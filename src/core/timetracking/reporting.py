"""
Time Tracking Reports for the Task Time Tracking system.

This module provides functionality for generating reports on time tracking data,
including summaries, charts, and analytics.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
import calendar
from enum import Enum

from .models import TimeEntry, TimeEstimate, TimeEntryStatus, TimeEstimateType


class ReportType(Enum):
    """Types of time tracking reports."""
    SUMMARY = "summary"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TASK = "task"
    USER = "user"
    TAG = "tag"
    ESTIMATE_COMPARISON = "estimate_comparison"
    BILLABLE = "billable"
    CUSTOM = "custom"


class ReportFormat(Enum):
    """Output formats for reports."""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"


class TimeTrackingReport:
    """Base class for time tracking reports."""
    
    def __init__(self, 
                 report_type: ReportType,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 task_ids: Optional[List[str]] = None,
                 user_ids: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 include_active: bool = True,
                 include_billable_only: bool = False,
                 group_by: Optional[str] = None,
                 format: ReportFormat = ReportFormat.JSON,
                 title: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a time tracking report.
        
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
            logger: Optional logger
        """
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date or datetime.now()
        self.task_ids = task_ids
        self.user_ids = user_ids
        self.tags = tags
        self.include_active = include_active
        self.include_billable_only = include_billable_only
        self.group_by = group_by
        self.format = format
        self.title = title or f"{report_type.value.title()} Report"
        self.logger = logger or logging.getLogger("tascade.timetracking")
        
        # Initialize report data
        self.data: Dict[str, Any] = {
            "report_type": report_type.value,
            "title": self.title,
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": self.start_date.isoformat() if self.start_date else None,
                "end": self.end_date.isoformat()
            },
            "filters": {
                "task_ids": self.task_ids,
                "user_ids": self.user_ids,
                "tags": self.tags,
                "include_active": self.include_active,
                "include_billable_only": self.include_billable_only
            },
            "group_by": self.group_by,
            "summary": {},
            "details": []
        }
    
    def generate(self, time_entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> Dict[str, Any]:
        """
        Generate the report.
        
        Args:
            time_entries: List of time entries
            estimates: Optional dictionary mapping task IDs to time estimates
            
        Returns:
            Report data
        """
        # Filter entries based on report criteria
        filtered_entries = self._filter_entries(time_entries)
        
        # Generate report data
        self._generate_report_data(filtered_entries, estimates)
        
        return self.data
    
    def _filter_entries(self, time_entries: List[TimeEntry]) -> List[TimeEntry]:
        """
        Filter time entries based on report criteria.
        
        Args:
            time_entries: List of time entries
            
        Returns:
            Filtered list of time entries
        """
        result = []
        
        for entry in time_entries:
            # Skip deleted entries
            if entry.status == TimeEntryStatus.DELETED:
                continue
            
            # Skip active entries if not included
            if not self.include_active and entry.status == TimeEntryStatus.ACTIVE:
                continue
            
            # Filter by date range
            if self.start_date and entry.start_time and entry.start_time < self.start_date:
                continue
            
            if self.end_date and entry.start_time and entry.start_time > self.end_date:
                continue
            
            # Filter by task IDs
            if self.task_ids and entry.task_id not in self.task_ids:
                continue
            
            # Filter by user IDs
            if self.user_ids and entry.user_id not in self.user_ids:
                continue
            
            # Filter by tags
            if self.tags and not any(tag in entry.tags for tag in self.tags):
                continue
            
            # Filter by billable flag
            if self.include_billable_only and not entry.billable:
                continue
            
            result.append(entry)
        
        return result
    
    def _generate_report_data(self, entries: List[TimeEntry], estimates: Optional[Dict[str, TimeEstimate]] = None) -> None:
        """
        Generate report data from filtered entries.
        
        Args:
            entries: Filtered time entries
            estimates: Optional dictionary mapping task IDs to time estimates
        """
        # This method should be implemented by subclasses
        pass
    
    def format_output(self) -> str:
        """
        Format the report output.
        
        Returns:
            Formatted report
        """
        if self.format == ReportFormat.JSON:
            return json.dumps(self.data, indent=2)
        elif self.format == ReportFormat.TEXT:
            return self._format_as_text()
        elif self.format == ReportFormat.MARKDOWN:
            return self._format_as_markdown()
        elif self.format == ReportFormat.HTML:
            return self._format_as_html()
        elif self.format == ReportFormat.CSV:
            return self._format_as_csv()
        else:
            return json.dumps(self.data, indent=2)
    
    def _format_as_text(self) -> str:
        """
        Format the report as plain text.
        
        Returns:
            Text formatted report
        """
        # This method should be implemented by subclasses
        return f"Report: {self.title}\nType: {self.report_type.value}\nGenerated: {self.data['generated_at']}"
    
    def _format_as_markdown(self) -> str:
        """
        Format the report as Markdown.
        
        Returns:
            Markdown formatted report
        """
        # This method should be implemented by subclasses
        return f"# {self.title}\n\n**Type:** {self.report_type.value}\n\n**Generated:** {self.data['generated_at']}"
    
    def _format_as_html(self) -> str:
        """
        Format the report as HTML.
        
        Returns:
            HTML formatted report
        """
        # This method should be implemented by subclasses
        return f"<h1>{self.title}</h1><p><strong>Type:</strong> {self.report_type.value}</p><p><strong>Generated:</strong> {self.data['generated_at']}</p>"
    
    def _format_as_csv(self) -> str:
        """
        Format the report as CSV.
        
        Returns:
            CSV formatted report
        """
        # This method should be implemented by subclasses
        return f"Report,{self.title}\nType,{self.report_type.value}\nGenerated,{self.data['generated_at']}"
    
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
    
    def _format_duration_hours(self, seconds: int) -> str:
        """
        Format duration in seconds as decimal hours.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration in hours
        """
        hours = seconds / 3600
        
        return f"{hours:.2f} hours"