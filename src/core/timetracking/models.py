"""
Models for the Task Time Tracking system.

This module defines the core data structures for time tracking,
including time entries, estimates, and time tracking settings.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json


class TimeEntryStatus(Enum):
    """Status of a time entry."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DELETED = "deleted"


class TimeEntryType(Enum):
    """Type of time entry."""
    MANUAL = "manual"  # Manually entered time
    TIMER = "timer"    # Time tracked with timer
    IMPORT = "import"  # Imported from external source


class TimeEstimateType(Enum):
    """Type of time estimate."""
    FIXED = "fixed"          # Fixed time estimate
    RANGE = "range"          # Range estimate (min/max)
    STORY_POINTS = "points"  # Story points
    T_SHIRT = "t_shirt"      # T-shirt sizing (S, M, L, XL)


class TimeEntry:
    """Represents a time entry for a task."""
    
    def __init__(self, 
                 id: Optional[str] = None,
                 task_id: str = "",
                 user_id: Optional[str] = None,
                 description: str = "",
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 duration_seconds: Optional[int] = None,
                 status: TimeEntryStatus = TimeEntryStatus.COMPLETED,
                 type: TimeEntryType = TimeEntryType.MANUAL,
                 tags: Optional[List[str]] = None,
                 billable: bool = False,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a time entry.
        
        Args:
            id: Unique identifier
            task_id: Task identifier
            user_id: User identifier
            description: Description of work done
            start_time: When the time entry started
            end_time: When the time entry ended
            duration_seconds: Duration in seconds (alternative to end_time)
            status: Status of the time entry
            type: Type of time entry
            tags: Tags for categorization
            billable: Whether the time is billable
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.task_id = task_id
        self.user_id = user_id
        self.description = description
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.status = status
        self.type = type
        self.tags = tags or []
        self.billable = billable
        self.metadata = metadata or {}
        
        # If duration is provided but not end_time, calculate end_time
        if duration_seconds is not None and end_time is None:
            self.end_time = self.start_time + timedelta(seconds=duration_seconds)
        
        # If active, ensure end_time is None
        if self.status == TimeEntryStatus.ACTIVE:
            self.end_time = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """
        Get the duration of the time entry.
        
        Returns:
            Duration as timedelta or None if active
        """
        if self.end_time is None:
            if self.status == TimeEntryStatus.ACTIVE:
                # For active entries, calculate duration up to now
                return datetime.now() - self.start_time
            return None
        
        return self.end_time - self.start_time
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """
        Get the duration in seconds.
        
        Returns:
            Duration in seconds or None if active
        """
        duration = self.duration
        if duration is None:
            return None
        
        return int(duration.total_seconds())
    
    @property
    def duration_formatted(self) -> str:
        """
        Get the duration formatted as HH:MM:SS.
        
        Returns:
            Formatted duration
        """
        duration = self.duration
        if duration is None:
            return "00:00:00"
        
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def start(self) -> None:
        """Start the time entry."""
        if self.status != TimeEntryStatus.ACTIVE:
            self.start_time = datetime.now()
            self.end_time = None
            self.status = TimeEntryStatus.ACTIVE
    
    def pause(self) -> None:
        """Pause the time entry."""
        if self.status == TimeEntryStatus.ACTIVE:
            self.end_time = datetime.now()
            self.status = TimeEntryStatus.PAUSED
    
    def resume(self) -> None:
        """Resume the time entry."""
        if self.status == TimeEntryStatus.PAUSED:
            # Calculate duration so far
            duration = self.duration
            
            # Set new start time, keeping the same duration
            self.start_time = datetime.now() - duration
            self.end_time = None
            self.status = TimeEntryStatus.ACTIVE
    
    def stop(self) -> None:
        """Stop the time entry."""
        if self.status in [TimeEntryStatus.ACTIVE, TimeEntryStatus.PAUSED]:
            if self.status == TimeEntryStatus.ACTIVE:
                self.end_time = datetime.now()
            self.status = TimeEntryStatus.COMPLETED
    
    def delete(self) -> None:
        """Mark the time entry as deleted."""
        self.status = TimeEntryStatus.DELETED
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self.duration_formatted,
            "status": self.status.value,
            "type": self.type.value,
            "tags": self.tags,
            "billable": self.billable,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeEntry':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TimeEntry instance
        """
        start_time = None
        if data.get("start_time"):
            start_time = datetime.fromisoformat(data["start_time"])
        
        end_time = None
        if data.get("end_time"):
            end_time = datetime.fromisoformat(data["end_time"])
        
        return cls(
            id=data.get("id"),
            task_id=data.get("task_id", ""),
            user_id=data.get("user_id"),
            description=data.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=data.get("duration_seconds"),
            status=TimeEntryStatus(data.get("status", "completed")),
            type=TimeEntryType(data.get("type", "manual")),
            tags=data.get("tags", []),
            billable=data.get("billable", False),
            metadata=data.get("metadata", {})
        )


class TimeEstimate:
    """Represents a time estimate for a task."""
    
    def __init__(self, 
                 id: Optional[str] = None,
                 task_id: str = "",
                 estimate_type: TimeEstimateType = TimeEstimateType.FIXED,
                 estimate_value: Union[int, float, str, Dict[str, Any]] = 0,
                 unit: str = "hours",
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 created_by: Optional[str] = None,
                 confidence: Optional[int] = None,
                 notes: str = "",
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a time estimate.
        
        Args:
            id: Unique identifier
            task_id: Task identifier
            estimate_type: Type of estimate
            estimate_value: Estimated value (format depends on type)
            unit: Unit of measurement (hours, days, etc.)
            created_at: When the estimate was created
            updated_at: When the estimate was last updated
            created_by: User who created the estimate
            confidence: Confidence level (0-100)
            notes: Additional notes
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.task_id = task_id
        self.estimate_type = estimate_type
        self.estimate_value = estimate_value
        self.unit = unit
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.created_by = created_by
        self.confidence = confidence
        self.notes = notes
        self.metadata = metadata or {}
    
    @property
    def formatted_estimate(self) -> str:
        """
        Get a formatted string representation of the estimate.
        
        Returns:
            Formatted estimate
        """
        if self.estimate_type == TimeEstimateType.FIXED:
            return f"{self.estimate_value} {self.unit}"
        elif self.estimate_type == TimeEstimateType.RANGE:
            if isinstance(self.estimate_value, dict):
                min_val = self.estimate_value.get("min", 0)
                max_val = self.estimate_value.get("max", 0)
                return f"{min_val}-{max_val} {self.unit}"
            return f"{self.estimate_value} {self.unit}"
        elif self.estimate_type == TimeEstimateType.STORY_POINTS:
            return f"{self.estimate_value} points"
        elif self.estimate_type == TimeEstimateType.T_SHIRT:
            return f"{self.estimate_value}"
        return str(self.estimate_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "estimate_type": self.estimate_type.value,
            "estimate_value": self.estimate_value,
            "unit": self.unit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "confidence": self.confidence,
            "notes": self.notes,
            "formatted_estimate": self.formatted_estimate,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeEstimate':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TimeEstimate instance
        """
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            id=data.get("id"),
            task_id=data.get("task_id", ""),
            estimate_type=TimeEstimateType(data.get("estimate_type", "fixed")),
            estimate_value=data.get("estimate_value", 0),
            unit=data.get("unit", "hours"),
            created_at=created_at,
            updated_at=updated_at,
            created_by=data.get("created_by"),
            confidence=data.get("confidence"),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {})
        )


class TimeTrackingSettings:
    """Settings for time tracking."""
    
    def __init__(self, 
                 default_estimate_type: TimeEstimateType = TimeEstimateType.FIXED,
                 default_unit: str = "hours",
                 round_to_nearest: int = 0,  # 0 = no rounding, 15 = round to nearest 15 minutes
                 track_idle_time: bool = True,
                 auto_pause_after_minutes: int = 0,  # 0 = disabled
                 billable_by_default: bool = False,
                 required_fields: Optional[List[str]] = None,
                 time_format: str = "HH:MM:SS",
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize time tracking settings.
        
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
        """
        self.default_estimate_type = default_estimate_type
        self.default_unit = default_unit
        self.round_to_nearest = round_to_nearest
        self.track_idle_time = track_idle_time
        self.auto_pause_after_minutes = auto_pause_after_minutes
        self.billable_by_default = billable_by_default
        self.required_fields = required_fields or ["task_id", "start_time"]
        self.time_format = time_format
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "default_estimate_type": self.default_estimate_type.value,
            "default_unit": self.default_unit,
            "round_to_nearest": self.round_to_nearest,
            "track_idle_time": self.track_idle_time,
            "auto_pause_after_minutes": self.auto_pause_after_minutes,
            "billable_by_default": self.billable_by_default,
            "required_fields": self.required_fields,
            "time_format": self.time_format,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeTrackingSettings':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TimeTrackingSettings instance
        """
        return cls(
            default_estimate_type=TimeEstimateType(data.get("default_estimate_type", "fixed")),
            default_unit=data.get("default_unit", "hours"),
            round_to_nearest=data.get("round_to_nearest", 0),
            track_idle_time=data.get("track_idle_time", True),
            auto_pause_after_minutes=data.get("auto_pause_after_minutes", 0),
            billable_by_default=data.get("billable_by_default", False),
            required_fields=data.get("required_fields", ["task_id", "start_time"]),
            time_format=data.get("time_format", "HH:MM:SS"),
            metadata=data.get("metadata", {})
        )