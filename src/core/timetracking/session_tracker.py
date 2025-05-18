"""
Work Session Tracker for the Task Time Tracking system.

This module implements the Work Session Tracker component, which manages
active work sessions, tracks productivity metrics, and provides insights
into work patterns.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import uuid
import json
import logging
import os
import time
import threading

from .models import TimeEntry, TimeEntryStatus, TimeEntryType
from .entry_manager import TimeEntryManager


class WorkSession:
    """Represents a work session with active time tracking."""
    
    def __init__(self, 
                 id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 task_id: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 description: str = "",
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a work session.
        
        Args:
            id: Unique identifier
            user_id: User identifier
            task_id: Task identifier
            start_time: Start time of the session
            description: Session description
            tags: Session tags
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.task_id = task_id
        self.start_time = start_time or datetime.now()
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        
        # Session state
        self.is_active = True
        self.is_paused = False
        self.pause_start_time: Optional[datetime] = None
        self.total_pause_duration = timedelta(seconds=0)
        self.activity_log: List[Dict[str, Any]] = []
        
        # Record session start
        self._log_activity("session_start")
    
    def pause(self) -> bool:
        """
        Pause the work session.
        
        Returns:
            True if paused successfully, False if already paused
        """
        if self.is_paused:
            return False
        
        self.is_paused = True
        self.pause_start_time = datetime.now()
        self._log_activity("session_pause")
        return True
    
    def resume(self) -> bool:
        """
        Resume the work session.
        
        Returns:
            True if resumed successfully, False if not paused
        """
        if not self.is_paused:
            return False
        
        if self.pause_start_time:
            pause_duration = datetime.now() - self.pause_start_time
            self.total_pause_duration += pause_duration
        
        self.is_paused = False
        self.pause_start_time = None
        self._log_activity("session_resume")
        return True
    
    def end(self) -> Dict[str, Any]:
        """
        End the work session and return session data.
        
        Returns:
            Session data including duration and metrics
        """
        if not self.is_active:
            return self.get_session_data()
        
        self.is_active = False
        
        # If paused, resume first to calculate correct duration
        if self.is_paused:
            self.resume()
        
        self._log_activity("session_end")
        return self.get_session_data()
    
    def add_activity(self, activity_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an activity to the session log.
        
        Args:
            activity_type: Type of activity
            details: Activity details
        """
        self._log_activity(activity_type, details)
    
    def get_session_data(self) -> Dict[str, Any]:
        """
        Get session data including duration and metrics.
        
        Returns:
            Session data
        """
        end_time = datetime.now() if self.is_active else self.activity_log[-1]["timestamp"]
        
        # Calculate active duration (excluding pauses)
        if self.is_paused and self.pause_start_time:
            current_pause_duration = datetime.now() - self.pause_start_time
            total_pause = self.total_pause_duration + current_pause_duration
        else:
            total_pause = self.total_pause_duration
        
        total_duration = end_time - self.start_time
        active_duration = total_duration - total_pause
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat() if not self.is_active else None,
            "description": self.description,
            "tags": self.tags,
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "total_duration_seconds": total_duration.total_seconds(),
            "active_duration_seconds": active_duration.total_seconds(),
            "pause_duration_seconds": total_pause.total_seconds(),
            "activity_count": len(self.activity_log),
            "metadata": self.metadata
        }
    
    def to_time_entry(self) -> TimeEntry:
        """
        Convert session to a time entry.
        
        Returns:
            TimeEntry object
        """
        session_data = self.get_session_data()
        
        # Only create time entry if session is ended
        if self.is_active:
            raise ValueError("Cannot convert active session to time entry")
        
        return TimeEntry(
            task_id=self.task_id,
            user_id=self.user_id,
            description=self.description,
            start_time=self.start_time,
            end_time=datetime.fromisoformat(session_data["end_time"]),
            duration_seconds=int(session_data["active_duration_seconds"]),
            status=TimeEntryStatus.COMPLETED,
            type=TimeEntryType.TIMER,
            tags=self.tags,
            metadata={
                "session_id": self.id,
                "pause_duration_seconds": session_data["pause_duration_seconds"],
                "activity_log": self.activity_log,
                **self.metadata
            }
        )
    
    def _log_activity(self, activity_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an activity in the session.
        
        Args:
            activity_type: Type of activity
            details: Activity details
        """
        self.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "details": details or {}
        })


class WorkSessionTracker:
    """Tracks and manages work sessions for tasks."""
    
    def __init__(self, 
                 entry_manager: TimeEntryManager,
                 auto_pause_after_minutes: int = 15,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the work session tracker.
        
        Args:
            entry_manager: Time entry manager
            auto_pause_after_minutes: Minutes of inactivity before auto-pause (0 to disable)
            logger: Optional logger
        """
        self.entry_manager = entry_manager
        self.auto_pause_after_minutes = auto_pause_after_minutes
        self.logger = logger or logging.getLogger("tascade.timetracking.session")
        
        # Active sessions by ID
        self.active_sessions: Dict[str, WorkSession] = {}
        
        # Activity monitoring
        self.activity_monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        # Start activity monitoring if auto-pause is enabled
        if self.auto_pause_after_minutes > 0:
            self._start_activity_monitoring()
    
    def start_session(self, 
                     task_id: str, 
                     user_id: Optional[str] = None,
                     description: str = "",
                     tags: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new work session for a task.
        
        Args:
            task_id: Task identifier
            user_id: User identifier
            description: Session description
            tags: Session tags
            metadata: Additional metadata
            
        Returns:
            Session ID
        """
        # End any existing session for this task and user
        self._end_existing_sessions(task_id, user_id)
        
        # Create new session
        session = WorkSession(
            task_id=task_id,
            user_id=user_id,
            description=description,
            tags=tags,
            metadata=metadata
        )
        
        # Store session
        self.active_sessions[session.id] = session
        self.logger.info(f"Started work session {session.id} for task {task_id}")
        
        return session.id
    
    def pause_session(self, session_id: str) -> bool:
        """
        Pause a work session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if paused successfully
        """
        if session_id not in self.active_sessions:
            self.logger.warning(f"Cannot pause non-existent session {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        result = session.pause()
        
        if result:
            self.logger.info(f"Paused work session {session_id}")
        else:
            self.logger.warning(f"Session {session_id} is already paused")
        
        return result
    
    def resume_session(self, session_id: str) -> bool:
        """
        Resume a paused work session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if resumed successfully
        """
        if session_id not in self.active_sessions:
            self.logger.warning(f"Cannot resume non-existent session {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        result = session.resume()
        
        if result:
            self.logger.info(f"Resumed work session {session_id}")
        else:
            self.logger.warning(f"Session {session_id} is not paused")
        
        return result
    
    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        End a work session and create a time entry.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if successful, None otherwise
        """
        if session_id not in self.active_sessions:
            self.logger.warning(f"Cannot end non-existent session {session_id}")
            return None
        
        # End session
        session = self.active_sessions[session_id]
        session_data = session.end()
        
        # Create time entry
        try:
            time_entry = session.to_time_entry()
            entry_id = self.entry_manager.add_entry(time_entry)
            session_data["time_entry_id"] = entry_id
        except Exception as e:
            self.logger.error(f"Error creating time entry for session {session_id}: {str(e)}")
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        self.logger.info(f"Ended work session {session_id}")
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a work session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if found, None otherwise
        """
        if session_id not in self.active_sessions:
            self.logger.warning(f"Session {session_id} not found")
            return None
        
        return self.active_sessions[session_id].get_session_data()
    
    def get_active_sessions(self, 
                           task_id: Optional[str] = None, 
                           user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active work sessions, optionally filtered.
        
        Args:
            task_id: Optional task identifier to filter by
            user_id: Optional user identifier to filter by
            
        Returns:
            List of session data
        """
        sessions = []
        
        for session in self.active_sessions.values():
            # Apply filters
            if task_id and session.task_id != task_id:
                continue
            if user_id and session.user_id != user_id:
                continue
            
            sessions.append(session.get_session_data())
        
        return sessions
    
    def record_activity(self, 
                       session_id: str, 
                       activity_type: str, 
                       details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record an activity in a work session.
        
        Args:
            session_id: Session identifier
            activity_type: Type of activity
            details: Activity details
            
        Returns:
            True if recorded successfully
        """
        if session_id not in self.active_sessions:
            self.logger.warning(f"Cannot record activity for non-existent session {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        session.add_activity(activity_type, details)
        
        # If session was paused due to inactivity, resume it
        if session.is_paused:
            session.resume()
            self.logger.info(f"Automatically resumed session {session_id} due to activity")
        
        return True
    
    def end_all_sessions(self, 
                        task_id: Optional[str] = None, 
                        user_id: Optional[str] = None) -> int:
        """
        End all active sessions, optionally filtered.
        
        Args:
            task_id: Optional task identifier to filter by
            user_id: Optional user identifier to filter by
            
        Returns:
            Number of sessions ended
        """
        sessions_to_end = []
        
        # Identify sessions to end
        for session_id, session in self.active_sessions.items():
            # Apply filters
            if task_id and session.task_id != task_id:
                continue
            if user_id and session.user_id != user_id:
                continue
            
            sessions_to_end.append(session_id)
        
        # End sessions
        for session_id in sessions_to_end:
            self.end_session(session_id)
        
        return len(sessions_to_end)
    
    def cleanup(self) -> None:
        """Clean up resources used by the session tracker."""
        # Stop activity monitoring
        if self.activity_monitor_thread and self.activity_monitor_thread.is_alive():
            self.stop_monitoring.set()
            self.activity_monitor_thread.join(timeout=2.0)
        
        # End all active sessions
        self.end_all_sessions()
    
    def _end_existing_sessions(self, task_id: str, user_id: Optional[str]) -> int:
        """
        End any existing sessions for the given task and user.
        
        Args:
            task_id: Task identifier
            user_id: Optional user identifier
            
        Returns:
            Number of sessions ended
        """
        return self.end_all_sessions(task_id=task_id, user_id=user_id)
    
    def _start_activity_monitoring(self) -> None:
        """Start the activity monitoring thread."""
        if self.activity_monitor_thread and self.activity_monitor_thread.is_alive():
            return
        
        self.stop_monitoring.clear()
        self.activity_monitor_thread = threading.Thread(
            target=self._activity_monitor_loop,
            daemon=True
        )
        self.activity_monitor_thread.start()
    
    def _activity_monitor_loop(self) -> None:
        """Activity monitoring loop to auto-pause inactive sessions."""
        while not self.stop_monitoring.is_set():
            try:
                self._check_session_activity()
            except Exception as e:
                self.logger.error(f"Error in activity monitoring: {str(e)}")
            
            # Sleep for a minute
            time.sleep(60)
    
    def _check_session_activity(self) -> None:
        """Check for inactive sessions and auto-pause them."""
        now = datetime.now()
        inactivity_threshold = timedelta(minutes=self.auto_pause_after_minutes)
        
        for session_id, session in list(self.active_sessions.items()):
            # Skip already paused sessions
            if session.is_paused:
                continue
            
            # Check last activity
            if session.activity_log:
                last_activity = datetime.fromisoformat(session.activity_log[-1]["timestamp"])
                inactive_duration = now - last_activity
                
                # Auto-pause if inactive for too long
                if inactive_duration >= inactivity_threshold:
                    session.pause()
                    session.add_activity("auto_pause", {
                        "reason": "inactivity",
                        "inactive_minutes": inactive_duration.total_seconds() / 60
                    })
                    self.logger.info(
                        f"Auto-paused session {session_id} after "
                        f"{inactive_duration.total_seconds() / 60:.1f} minutes of inactivity"
                    )
