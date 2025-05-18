"""
Time Entry Manager for the Task Time Tracking system.

This module provides functionality for managing time entries,
including creating, updating, and querying time entries.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
import uuid

from .models import TimeEntry, TimeEntryStatus, TimeEntryType, TimeTrackingSettings


class TimeEntryManager:
    """Manager for time entries."""
    
    def __init__(self, 
                 data_dir: str = None,
                 entries_file: str = "time_entries.json",
                 settings: Optional[TimeTrackingSettings] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the time entry manager.
        
        Args:
            data_dir: Directory for storing time entry data
            entries_file: File name for time entries
            settings: Time tracking settings
            logger: Optional logger
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.entries_file = os.path.join(self.data_dir, entries_file)
        self.settings = settings or TimeTrackingSettings()
        self.logger = logger or logging.getLogger("tascade.timetracking")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize entries
        self.entries: Dict[str, TimeEntry] = {}
        self.active_entry: Optional[str] = None
        
        # Load existing entries
        self._load_entries()
    
    def _load_entries(self) -> None:
        """Load time entries from the entries file."""
        if not os.path.exists(self.entries_file):
            self.logger.info(f"Time entries file not found: {self.entries_file}")
            return
        
        try:
            with open(self.entries_file, "r") as f:
                data = json.load(f)
            
            for item in data:
                entry = TimeEntry.from_dict(item)
                self.entries[entry.id] = entry
                
                # Check if there's an active entry
                if entry.status == TimeEntryStatus.ACTIVE:
                    self.active_entry = entry.id
        except Exception as e:
            self.logger.error(f"Error loading time entries: {e}")
    
    def _save_entries(self) -> None:
        """Save time entries to the entries file."""
        try:
            data = [entry.to_dict() for entry in self.entries.values()]
            
            with open(self.entries_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving time entries: {e}")
    
    def create_entry(self, 
                     task_id: str,
                     description: str = "",
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     duration_seconds: Optional[int] = None,
                     status: TimeEntryStatus = TimeEntryStatus.COMPLETED,
                     type: TimeEntryType = TimeEntryType.MANUAL,
                     user_id: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     billable: Optional[bool] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
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
            ID of the created entry
        """
        # Apply settings
        if billable is None:
            billable = self.settings.billable_by_default
        
        # Create entry
        entry = TimeEntry(
            task_id=task_id,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            status=status,
            type=type,
            user_id=user_id,
            tags=tags,
            billable=billable,
            metadata=metadata
        )
        
        # If this is an active entry, handle existing active entry
        if status == TimeEntryStatus.ACTIVE:
            if self.active_entry:
                # Stop existing active entry
                self.stop_entry(self.active_entry)
            
            self.active_entry = entry.id
        
        # Apply rounding if needed
        if self.settings.round_to_nearest > 0 and entry.end_time:
            self._apply_rounding(entry)
        
        # Store entry
        self.entries[entry.id] = entry
        self._save_entries()
        
        return entry.id
    
    def update_entry(self, 
                     entry_id: str,
                     task_id: Optional[str] = None,
                     description: Optional[str] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     duration_seconds: Optional[int] = None,
                     status: Optional[TimeEntryStatus] = None,
                     type: Optional[TimeEntryType] = None,
                     user_id: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     billable: Optional[bool] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
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
            True if update succeeded, False otherwise
        """
        if entry_id not in self.entries:
            self.logger.error(f"Time entry not found: {entry_id}")
            return False
        
        entry = self.entries[entry_id]
        
        # Update fields
        if task_id is not None:
            entry.task_id = task_id
        
        if description is not None:
            entry.description = description
        
        if start_time is not None:
            entry.start_time = start_time
        
        if end_time is not None:
            entry.end_time = end_time
        elif duration_seconds is not None and entry.start_time:
            entry.end_time = entry.start_time + timedelta(seconds=duration_seconds)
        
        if status is not None:
            old_status = entry.status
            entry.status = status
            
            # Handle status changes
            if old_status != TimeEntryStatus.ACTIVE and status == TimeEntryStatus.ACTIVE:
                # Entry is becoming active
                if self.active_entry and self.active_entry != entry_id:
                    # Stop existing active entry
                    self.stop_entry(self.active_entry)
                
                self.active_entry = entry_id
                entry.end_time = None
            elif old_status == TimeEntryStatus.ACTIVE and status != TimeEntryStatus.ACTIVE:
                # Entry is no longer active
                if self.active_entry == entry_id:
                    self.active_entry = None
                
                # Set end time if not already set
                if entry.end_time is None and status == TimeEntryStatus.COMPLETED:
                    entry.end_time = datetime.now()
        
        if type is not None:
            entry.type = type
        
        if user_id is not None:
            entry.user_id = user_id
        
        if tags is not None:
            entry.tags = tags
        
        if billable is not None:
            entry.billable = billable
        
        if metadata is not None:
            entry.metadata.update(metadata)
        
        # Apply rounding if needed
        if self.settings.round_to_nearest > 0 and entry.end_time:
            self._apply_rounding(entry)
        
        # Save changes
        self._save_entries()
        
        return True
    
    def get_entry(self, entry_id: str) -> Optional[TimeEntry]:
        """
        Get a time entry by ID.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            Time entry or None if not found
        """
        return self.entries.get(entry_id)
    
    def get_entries(self, 
                    task_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    status: Optional[TimeEntryStatus] = None,
                    type: Optional[TimeEntryType] = None,
                    tags: Optional[List[str]] = None,
                    billable: Optional[bool] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    include_deleted: bool = False) -> List[TimeEntry]:
        """
        Get time entries, optionally filtered.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            status: Filter by status
            type: Filter by type
            tags: Filter by tags (entries must have at least one of these tags)
            billable: Filter by billable flag
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            include_deleted: Whether to include deleted entries
            
        Returns:
            List of time entries
        """
        result = list(self.entries.values())
        
        # Apply filters
        if not include_deleted:
            result = [e for e in result if e.status != TimeEntryStatus.DELETED]
        
        if task_id:
            result = [e for e in result if e.task_id == task_id]
        
        if user_id:
            result = [e for e in result if e.user_id == user_id]
        
        if status:
            result = [e for e in result if e.status == status]
        
        if type:
            result = [e for e in result if e.type == type]
        
        if tags:
            result = [e for e in result if any(tag in e.tags for tag in tags)]
        
        if billable is not None:
            result = [e for e in result if e.billable == billable]
        
        if start_date:
            result = [e for e in result if e.start_time and e.start_time >= start_date]
        
        if end_date:
            result = [e for e in result if e.start_time and e.start_time <= end_date]
        
        # Sort by start time
        result.sort(key=lambda e: e.start_time if e.start_time else datetime.min)
        
        return result
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        if entry_id not in self.entries:
            self.logger.error(f"Time entry not found: {entry_id}")
            return False
        
        entry = self.entries[entry_id]
        
        # Mark as deleted
        entry.delete()
        
        # If this was the active entry, clear active entry
        if self.active_entry == entry_id:
            self.active_entry = None
        
        # Save changes
        self._save_entries()
        
        return True
    
    def start_timer(self, 
                    task_id: str,
                    description: str = "",
                    user_id: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    billable: Optional[bool] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
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
            ID of the created entry
        """
        return self.create_entry(
            task_id=task_id,
            description=description,
            start_time=datetime.now(),
            status=TimeEntryStatus.ACTIVE,
            type=TimeEntryType.TIMER,
            user_id=user_id,
            tags=tags,
            billable=billable,
            metadata=metadata
        )
    
    def stop_timer(self, entry_id: Optional[str] = None) -> Union[Optional[str], bool]:
        """
        Stop a timer.
        
        Args:
            entry_id: Entry identifier (optional, uses active timer if not provided)
            
        Returns:
            ID of the stopped entry, True if specific entry stopped, or None if no active timer
        """
        # If entry_id is provided, stop that specific entry
        if entry_id:
            return self.stop_entry(entry_id)
            
        # Otherwise, stop the active timer
        if not self.active_entry:
            self.logger.warning("No active timer to stop")
            return None
        
        self.stop_entry(self.active_entry)
        return self.active_entry
    
    def pause_entry(self, entry_id: str) -> bool:
        """
        Pause a time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            True if pause succeeded, False otherwise
        """
        if entry_id not in self.entries:
            self.logger.error(f"Time entry not found: {entry_id}")
            return False
        
        entry = self.entries[entry_id]
        
        # Pause entry
        entry.pause()
        
        # If this was the active entry, clear active entry
        if self.active_entry == entry_id:
            self.active_entry = None
        
        # Save changes
        self._save_entries()
        
        return True
    
    def resume_entry(self, entry_id: str) -> bool:
        """
        Resume a paused time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            True if resume succeeded, False otherwise
        """
        if entry_id not in self.entries:
            self.logger.error(f"Time entry not found: {entry_id}")
            return False
        
        entry = self.entries[entry_id]
        
        # If there's an active entry, stop it
        if self.active_entry:
            self.stop_entry(self.active_entry)
        
        # Resume entry
        entry.resume()
        self.active_entry = entry_id
        
        # Save changes
        self._save_entries()
        
        return True
    
    def stop_entry(self, entry_id: str) -> bool:
        """
        Stop a time entry.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            True if stop succeeded, False otherwise
        """
        if entry_id not in self.entries:
            self.logger.error(f"Time entry not found: {entry_id}")
            return False
        
        entry = self.entries[entry_id]
        
        # Stop entry
        entry.stop()
        
        # If this was the active entry, clear active entry
        if self.active_entry == entry_id:
            self.active_entry = None
        
        # Apply rounding if needed
        if self.settings.round_to_nearest > 0:
            self._apply_rounding(entry)
        
        # Save changes
        self._save_entries()
        
        return True
    
    def get_active_entry(self) -> Optional[TimeEntry]:
        """
        Get the active time entry.
        
        Returns:
            Active time entry or None if no active entry
        """
        if not self.active_entry:
            return None
        
        return self.entries.get(self.active_entry)
    
    def get_total_time(self, 
                       task_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       billable: Optional[bool] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       include_active: bool = True) -> timedelta:
        """
        Get total time for entries matching filters.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            tags: Filter by tags
            billable: Filter by billable flag
            start_date: Filter by start date
            end_date: Filter by end date
            include_active: Whether to include active entries
            
        Returns:
            Total time as timedelta
        """
        # Get filtered entries
        entries = self.get_entries(
            task_id=task_id,
            user_id=user_id,
            tags=tags,
            billable=billable,
            start_date=start_date,
            end_date=end_date,
            include_deleted=False
        )
        
        # Filter out active entries if not included
        if not include_active:
            entries = [e for e in entries if e.status != TimeEntryStatus.ACTIVE]
        
        # Sum durations
        total = timedelta()
        for entry in entries:
            duration = entry.duration
            if duration:
                total += duration
        
        return total
    
    def get_time_by_day(self, 
                        task_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, timedelta]:
        """
        Get time grouped by day.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            tags: Filter by tags
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary mapping dates to total time
        """
        # Get filtered entries
        entries = self.get_entries(
            task_id=task_id,
            user_id=user_id,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            include_deleted=False
        )
        
        # Group by day
        result: Dict[str, timedelta] = {}
        for entry in entries:
            if not entry.start_time:
                continue
            
            day = entry.start_time.date().isoformat()
            duration = entry.duration
            
            if not duration:
                continue
            
            if day not in result:
                result[day] = timedelta()
            
            result[day] += duration
        
        return result
    
    def get_time_by_task(self, 
                         user_id: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, timedelta]:
        """
        Get time grouped by task.
        
        Args:
            user_id: Filter by user ID
            tags: Filter by tags
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary mapping task IDs to total time
        """
        # Get filtered entries
        entries = self.get_entries(
            user_id=user_id,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            include_deleted=False
        )
        
        # Group by task
        result: Dict[str, timedelta] = {}
        for entry in entries:
            task_id = entry.task_id
            duration = entry.duration
            
            if not duration:
                continue
            
            if task_id not in result:
                result[task_id] = timedelta()
            
            result[task_id] += duration
        
        return result
    
    def get_time_by_tag(self, 
                        task_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, timedelta]:
        """
        Get time grouped by tag.
        
        Args:
            task_id: Filter by task ID
            user_id: Filter by user ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary mapping tags to total time
        """
        # Get filtered entries
        entries = self.get_entries(
            task_id=task_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            include_deleted=False
        )
        
        # Group by tag
        result: Dict[str, timedelta] = {}
        for entry in entries:
            duration = entry.duration
            
            if not duration:
                continue
            
            # Add time to each tag
            for tag in entry.tags:
                if tag not in result:
                    result[tag] = timedelta()
                
                result[tag] += duration
        
        return result
    
    def update_settings(self, settings: TimeTrackingSettings) -> None:
        """
        Update time tracking settings.
        
        Args:
            settings: New settings
        """
        self.settings = settings
    
    def _apply_rounding(self, entry: TimeEntry) -> None:
        """
        Apply time rounding to an entry.
        
        Args:
            entry: Time entry to round
        """
        if not entry.end_time or not entry.start_time:
            return
        
        # Get duration in minutes
        duration_minutes = entry.duration.total_seconds() / 60
        
        # Round to nearest interval
        rounded_minutes = round(duration_minutes / self.settings.round_to_nearest) * self.settings.round_to_nearest
        
        # Update end time
        entry.end_time = entry.start_time + timedelta(minutes=rounded_minutes)