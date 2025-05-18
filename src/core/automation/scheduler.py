"""
Scheduler for the Task Automation System.

This module provides functionality for scheduling automation events.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import json
import os
import threading
import time
import uuid
import logging
import heapq


class ScheduledEvent:
    """Represents a scheduled event."""
    
    def __init__(self, 
                 id: str,
                 event_type: str,
                 scheduled_time: datetime,
                 data: Optional[Dict[str, Any]] = None,
                 recurring: bool = False,
                 recurrence_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a scheduled event.
        
        Args:
            id: Unique identifier for the event
            event_type: Type of event
            scheduled_time: When the event is scheduled to occur
            data: Additional data for the event
            recurring: Whether the event recurs
            recurrence_config: Configuration for recurring events
        """
        self.id = id
        self.event_type = event_type
        self.scheduled_time = scheduled_time
        self.data = data or {}
        self.recurring = recurring
        self.recurrence_config = recurrence_config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "event_type": self.event_type,
            "scheduled_time": self.scheduled_time.isoformat(),
            "data": self.data,
            "recurring": self.recurring,
            "recurrence_config": self.recurrence_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledEvent':
        """
        Create an event from a dictionary.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            ScheduledEvent instance
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=data.get("event_type", "scheduled"),
            scheduled_time=datetime.fromisoformat(data.get("scheduled_time")),
            data=data.get("data", {}),
            recurring=data.get("recurring", False),
            recurrence_config=data.get("recurrence_config", {})
        )
    
    def get_next_occurrence(self) -> Optional[datetime]:
        """
        Get the next occurrence time for a recurring event.
        
        Returns:
            Next occurrence time, or None if not recurring
        """
        if not self.recurring:
            return None
        
        frequency = self.recurrence_config.get("frequency")
        if not frequency:
            return None
        
        now = datetime.now()
        
        if frequency == "daily":
            # Daily recurrence
            days = self.recurrence_config.get("every_days", 1)
            next_time = self.scheduled_time + timedelta(days=days)
            
            # If the next time is in the past, calculate the next occurrence
            while next_time < now:
                next_time += timedelta(days=days)
            
            return next_time
        
        elif frequency == "weekly":
            # Weekly recurrence
            weeks = self.recurrence_config.get("every_weeks", 1)
            next_time = self.scheduled_time + timedelta(weeks=weeks)
            
            # If the next time is in the past, calculate the next occurrence
            while next_time < now:
                next_time += timedelta(weeks=weeks)
            
            return next_time
        
        elif frequency == "monthly":
            # Monthly recurrence
            months = self.recurrence_config.get("every_months", 1)
            
            # Get the day of the month
            day_of_month = self.scheduled_time.day
            
            # Get the next month
            next_month = self.scheduled_time.month + months
            next_year = self.scheduled_time.year
            
            # Adjust year if needed
            while next_month > 12:
                next_month -= 12
                next_year += 1
            
            # Create the next occurrence
            try:
                next_time = datetime(
                    year=next_year,
                    month=next_month,
                    day=day_of_month,
                    hour=self.scheduled_time.hour,
                    minute=self.scheduled_time.minute,
                    second=self.scheduled_time.second,
                    microsecond=self.scheduled_time.microsecond
                )
            except ValueError:
                # Handle invalid dates (e.g., February 30)
                # Use the last day of the month
                if next_month == 2:
                    # Check for leap year
                    if (next_year % 4 == 0 and next_year % 100 != 0) or (next_year % 400 == 0):
                        day_of_month = min(day_of_month, 29)
                    else:
                        day_of_month = min(day_of_month, 28)
                elif next_month in [4, 6, 9, 11]:
                    day_of_month = min(day_of_month, 30)
                
                next_time = datetime(
                    year=next_year,
                    month=next_month,
                    day=day_of_month,
                    hour=self.scheduled_time.hour,
                    minute=self.scheduled_time.minute,
                    second=self.scheduled_time.second,
                    microsecond=self.scheduled_time.microsecond
                )
            
            # If the next time is in the past, calculate the next occurrence
            while next_time < now:
                # Get the next month
                next_month += months
                
                # Adjust year if needed
                while next_month > 12:
                    next_month -= 12
                    next_year += 1
                
                # Create the next occurrence
                try:
                    next_time = datetime(
                        year=next_year,
                        month=next_month,
                        day=day_of_month,
                        hour=self.scheduled_time.hour,
                        minute=self.scheduled_time.minute,
                        second=self.scheduled_time.second,
                        microsecond=self.scheduled_time.microsecond
                    )
                except ValueError:
                    # Handle invalid dates (e.g., February 30)
                    # Use the last day of the month
                    if next_month == 2:
                        # Check for leap year
                        if (next_year % 4 == 0 and next_year % 100 != 0) or (next_year % 400 == 0):
                            day_of_month = min(day_of_month, 29)
                        else:
                            day_of_month = min(day_of_month, 28)
                    elif next_month in [4, 6, 9, 11]:
                        day_of_month = min(day_of_month, 30)
                    
                    next_time = datetime(
                        year=next_year,
                        month=next_month,
                        day=day_of_month,
                        hour=self.scheduled_time.hour,
                        minute=self.scheduled_time.minute,
                        second=self.scheduled_time.second,
                        microsecond=self.scheduled_time.microsecond
                    )
            
            return next_time
        
        return None
    
    def __lt__(self, other):
        """
        Compare events by scheduled time.
        
        Args:
            other: Another ScheduledEvent
            
        Returns:
            True if this event is scheduled before the other
        """
        return self.scheduled_time < other.scheduled_time


class Scheduler:
    """Scheduler for time-based automation."""
    
    def __init__(self, 
                events_file: Optional[str] = None,
                event_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the scheduler.
        
        Args:
            events_file: Optional path to a file containing events
            event_callback: Optional callback for when events are triggered
        """
        self.events: Dict[str, ScheduledEvent] = {}
        self.events_file = events_file
        self.event_callback = event_callback
        self.event_queue: List[ScheduledEvent] = []
        self.running = False
        self.thread = None
        self.logger = logging.getLogger("tascade.automation.scheduler")
        
        # Load events if a file is provided
        if self.events_file and os.path.exists(self.events_file):
            self._load_events()
    
    def schedule_event(self, 
                      event_type: str,
                      scheduled_time: Union[datetime, str],
                      data: Optional[Dict[str, Any]] = None,
                      recurring: bool = False,
                      recurrence_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule an event.
        
        Args:
            event_type: Type of event
            scheduled_time: When the event should occur
            data: Additional data for the event
            recurring: Whether the event recurs
            recurrence_config: Configuration for recurring events
            
        Returns:
            ID of the scheduled event
        """
        # Convert string to datetime if needed
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time)
        
        # Create the event
        event_id = str(uuid.uuid4())
        event = ScheduledEvent(
            id=event_id,
            event_type=event_type,
            scheduled_time=scheduled_time,
            data=data,
            recurring=recurring,
            recurrence_config=recurrence_config
        )
        
        # Store the event
        self.events[event_id] = event
        
        # Add to the event queue
        heapq.heappush(self.event_queue, event)
        
        # Save events if a file is provided
        if self.events_file:
            self._save_events()
        
        return event_id
    
    def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a scheduled event.
        
        Args:
            event_id: ID of the event to cancel
            
        Returns:
            True if the event was cancelled, False if it wasn't found
        """
        if event_id in self.events:
            # Remove from the events dictionary
            del self.events[event_id]
            
            # Rebuild the event queue
            self.event_queue = [event for event in self.event_queue if event.id != event_id]
            heapq.heapify(self.event_queue)
            
            # Save events if a file is provided
            if self.events_file:
                self._save_events()
            
            return True
        
        return False
    
    def get_event(self, event_id: str) -> Optional[ScheduledEvent]:
        """
        Get an event by ID.
        
        Args:
            event_id: ID of the event to get
            
        Returns:
            The event if found, None otherwise
        """
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[ScheduledEvent]:
        """
        Get all scheduled events.
        
        Returns:
            List of all scheduled events
        """
        return list(self.events.values())
    
    def get_due_events(self) -> List[ScheduledEvent]:
        """
        Get events that are due for execution.
        
        Returns:
            List of due events
        """
        now = datetime.now()
        due_events = []
        
        # Check each event in the queue
        while self.event_queue and self.event_queue[0].scheduled_time <= now:
            # Pop the event from the queue
            event = heapq.heappop(self.event_queue)
            
            # Add to due events
            due_events.append(event)
            
            # If the event is recurring, schedule the next occurrence
            if event.recurring:
                next_time = event.get_next_occurrence()
                if next_time:
                    # Create a new event for the next occurrence
                    next_event = ScheduledEvent(
                        id=event.id,
                        event_type=event.event_type,
                        scheduled_time=next_time,
                        data=event.data,
                        recurring=event.recurring,
                        recurrence_config=event.recurrence_config
                    )
                    
                    # Update the event in the events dictionary
                    self.events[event.id] = next_event
                    
                    # Add to the event queue
                    heapq.heappush(self.event_queue, next_event)
            else:
                # Remove the event from the events dictionary
                if event.id in self.events:
                    del self.events[event.id]
        
        # Save events if a file is provided
        if due_events and self.events_file:
            self._save_events()
        
        return due_events
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _run(self) -> None:
        """Run the scheduler."""
        while self.running:
            try:
                # Get due events
                due_events = self.get_due_events()
                
                # Process due events
                for event in due_events:
                    try:
                        # Create the event data
                        event_data = {
                            "type": event.event_type,
                            "schedule_id": event.id,
                            "time": event.scheduled_time.isoformat(),
                            **event.data
                        }
                        
                        # Call the callback if provided
                        if self.event_callback:
                            self.event_callback(event_data)
                    except Exception as e:
                        self.logger.error(f"Error processing event {event.id}: {e}")
                
                # Sleep for a short time
                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Error in scheduler thread: {e}")
    
    def _load_events(self) -> None:
        """Load events from the events file."""
        try:
            with open(self.events_file, 'r') as f:
                events_data = json.load(f)
            
            for event_data in events_data:
                try:
                    event = ScheduledEvent.from_dict(event_data)
                    self.events[event.id] = event
                    heapq.heappush(self.event_queue, event)
                except Exception as e:
                    self.logger.error(f"Error loading event: {e}")
        except Exception as e:
            self.logger.error(f"Error loading events: {e}")
    
    def _save_events(self) -> None:
        """Save events to the events file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
            
            # Convert events to dictionaries
            events_data = [event.to_dict() for event in self.events.values()]
            
            # Save to file
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving events: {e}")