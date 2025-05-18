"""
Mobile client for Tascade AI.

This module provides a client for mobile applications to interact with
Tascade AI's time tracking system via the mobile API.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
import logging
import requests
import threading
import time
import queue


class TascadeMobileClient:
    """Client for the Tascade AI mobile API."""
    
    def __init__(self, 
                 api_url: str,
                 user_id: Optional[str] = None,
                 token: Optional[str] = None,
                 offline_mode: bool = False,
                 sync_interval: int = 300,  # 5 minutes
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the mobile client.
        
        Args:
            api_url: URL of the Tascade AI mobile API
            user_id: User identifier
            token: Authentication token
            offline_mode: Whether to operate in offline mode
            sync_interval: Interval between sync attempts in seconds
            logger: Optional logger
        """
        self.api_url = api_url.rstrip('/')
        self.user_id = user_id
        self.token = token
        self.offline_mode = offline_mode
        self.sync_interval = sync_interval
        self.logger = logger or logging.getLogger("tascade.mobile.client")
        
        # Offline storage
        self.offline_entries = []
        self.offline_queue = queue.Queue()
        
        # Sync thread
        self.sync_thread = None
        self.stop_sync = threading.Event()
        
        # Start sync thread if in offline mode
        if self.offline_mode:
            self._start_sync_thread()
    
    def _start_sync_thread(self) -> None:
        """Start the sync thread."""
        if self.sync_thread is not None:
            return
        
        self.stop_sync.clear()
        self.sync_thread = threading.Thread(target=self._sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
    
    def _stop_sync_thread(self) -> None:
        """Stop the sync thread."""
        if self.sync_thread is None:
            return
        
        self.stop_sync.set()
        self.sync_thread.join()
        self.sync_thread = None
    
    def _sync_worker(self) -> None:
        """Sync worker thread."""
        while not self.stop_sync.is_set():
            try:
                # Check if we're online
                if self._check_connectivity():
                    # Sync offline entries
                    self._sync_offline_entries()
                
                # Wait for next sync interval
                self.stop_sync.wait(self.sync_interval)
            except Exception as e:
                self.logger.error(f"Error in sync worker: {e}")
                # Wait a bit before retrying
                time.sleep(10)
    
    def _check_connectivity(self) -> bool:
        """Check if we have connectivity to the API."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _sync_offline_entries(self) -> None:
        """Sync offline entries with the server."""
        if not self.offline_entries:
            return
        
        try:
            # Get entries to sync
            entries_to_sync = self.offline_entries.copy()
            self.offline_entries = []
            
            # Send to server
            response = self._make_request(
                "POST",
                "/api/sync/upload",
                json={
                    'time_entries': entries_to_sync
                }
            )
            
            if response.status_code != 200:
                # Put entries back in the queue
                self.offline_entries.extend(entries_to_sync)
                self.logger.error(f"Failed to sync entries: {response.text}")
                return
            
            # Process response
            result = response.json()
            
            # Check for entries that failed to sync
            for entry_result in result.get('time_entries', []):
                if not entry_result.get('success'):
                    # Find the original entry
                    client_id = entry_result.get('client_id')
                    for entry in entries_to_sync:
                        if entry.get('client_id') == client_id:
                            # Put back in the queue
                            self.offline_entries.append(entry)
                            break
            
            self.logger.info(f"Synced {len(entries_to_sync) - len(self.offline_entries)} entries")
        except Exception as e:
            # Put entries back in the queue
            self.offline_entries.extend(entries_to_sync)
            self.logger.error(f"Error syncing entries: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object
        """
        url = f"{self.api_url}{endpoint}"
        
        # Add authentication token if available
        if self.token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f"Bearer {self.token}"
            kwargs['headers'] = headers
        
        return requests.request(method, url, **kwargs)
    
    # Authentication
    
    def login(self, user_id: str) -> Dict[str, Any]:
        """
        Login to the API.
        
        Args:
            user_id: User identifier
        
        Returns:
            Response data
        """
        response = self._make_request(
            "POST",
            "/api/auth/login",
            json={'user_id': user_id}
        )
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        
        result = response.json()
        
        # Update client state
        self.user_id = result.get('user_id')
        self.token = result.get('token')
        
        return result
    
    # Time entries
    
    def get_time_entries(self, 
                         task_id: Optional[str] = None,
                         from_date: Optional[datetime] = None,
                         to_date: Optional[datetime] = None,
                         tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get time entries.
        
        Args:
            task_id: Optional task identifier
            from_date: Optional start date
            to_date: Optional end date
            tags: Optional tags
        
        Returns:
            List of time entries
        """
        # Build query parameters
        params = {}
        
        if task_id:
            params['task_id'] = task_id
        
        if from_date:
            params['from_date'] = from_date.isoformat()
        
        if to_date:
            params['to_date'] = to_date.isoformat()
        
        if tags:
            params['tags'] = ','.join(tags)
        
        # Make request
        response = self._make_request(
            "GET",
            "/api/time/entries",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get time entries: {response.text}")
        
        return response.json()
    
    def create_time_entry(self, 
                          task_id: str,
                          description: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          duration_seconds: Optional[int] = None,
                          tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a time entry.
        
        Args:
            task_id: Task identifier
            description: Optional description
            start_time: Optional start time
            end_time: Optional end time
            duration_seconds: Optional duration in seconds
            tags: Optional tags
        
        Returns:
            Created time entry
        """
        # Build entry data
        entry_data = {
            'task_id': task_id,
            'user_id': self.user_id
        }
        
        if description:
            entry_data['description'] = description
        
        if start_time:
            entry_data['start_time'] = start_time.isoformat()
        
        if end_time:
            entry_data['end_time'] = end_time.isoformat()
        
        if duration_seconds:
            entry_data['duration_seconds'] = duration_seconds
        
        if tags:
            entry_data['tags'] = tags
        
        # Add client ID for offline mode
        if self.offline_mode:
            import uuid
            entry_data['client_id'] = str(uuid.uuid4())
        
        # Check if we're in offline mode
        if self.offline_mode and not self._check_connectivity():
            # Store entry for later sync
            self.offline_entries.append(entry_data)
            
            return {
                'success': True,
                'entry_id': entry_data['client_id'],
                'offline': True
            }
        
        # Make request
        response = self._make_request(
            "POST",
            "/api/time/entries",
            json=entry_data
        )
        
        if response.status_code != 201:
            # If we're in offline mode, store for later sync
            if self.offline_mode:
                self.offline_entries.append(entry_data)
                
                return {
                    'success': True,
                    'entry_id': entry_data['client_id'],
                    'offline': True
                }
            
            raise Exception(f"Failed to create time entry: {response.text}")
        
        return response.json()
    
    def update_time_entry(self, 
                          entry_id: str,
                          task_id: Optional[str] = None,
                          description: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          duration_seconds: Optional[int] = None,
                          tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update a time entry.
        
        Args:
            entry_id: Entry identifier
            task_id: Optional task identifier
            description: Optional description
            start_time: Optional start time
            end_time: Optional end time
            duration_seconds: Optional duration in seconds
            tags: Optional tags
        
        Returns:
            Updated time entry
        """
        # Build update data
        update_data = {}
        
        if task_id:
            update_data['task_id'] = task_id
        
        if description:
            update_data['description'] = description
        
        if start_time:
            update_data['start_time'] = start_time.isoformat()
        
        if end_time:
            update_data['end_time'] = end_time.isoformat()
        
        if duration_seconds:
            update_data['duration_seconds'] = duration_seconds
        
        if tags:
            update_data['tags'] = tags
        
        # Make request
        response = self._make_request(
            "PUT",
            f"/api/time/entries/{entry_id}",
            json=update_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to update time entry: {response.text}")
        
        return response.json()
    
    def delete_time_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Delete a time entry.
        
        Args:
            entry_id: Entry identifier
        
        Returns:
            Response data
        """
        response = self._make_request(
            "DELETE",
            f"/api/time/entries/{entry_id}"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to delete time entry: {response.text}")
        
        return response.json()
    
    # Work sessions
    
    def start_session(self, 
                      task_id: str,
                      description: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a work session.
        
        Args:
            task_id: Task identifier
            description: Optional description
            tags: Optional tags
        
        Returns:
            Session data
        """
        # Build session data
        session_data = {
            'task_id': task_id
        }
        
        if description:
            session_data['description'] = description
        
        if tags:
            session_data['tags'] = tags
        
        # Make request
        response = self._make_request(
            "POST",
            "/api/time/sessions/start",
            json=session_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to start session: {response.text}")
        
        return response.json()
    
    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """
        Pause a work session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data
        """
        response = self._make_request(
            "POST",
            f"/api/time/sessions/{session_id}/pause"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to pause session: {response.text}")
        
        return response.json()
    
    def resume_session(self, session_id: str) -> Dict[str, Any]:
        """
        Resume a work session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data
        """
        response = self._make_request(
            "POST",
            f"/api/time/sessions/{session_id}/resume"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to resume session: {response.text}")
        
        return response.json()
    
    def stop_session(self, session_id: str) -> Dict[str, Any]:
        """
        Stop a work session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data
        """
        response = self._make_request(
            "POST",
            f"/api/time/sessions/{session_id}/stop"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to stop session: {response.text}")
        
        return response.json()
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current tracking status.
        
        Returns:
            Tracking status
        """
        response = self._make_request(
            "GET",
            "/api/time/sessions/status"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get tracking status: {response.text}")
        
        return response.json()
    
    # Time estimates
    
    def get_estimates(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get time estimates.
        
        Args:
            task_id: Optional task identifier
        
        Returns:
            List of time estimates
        """
        # Build query parameters
        params = {}
        
        if task_id:
            params['task_id'] = task_id
        
        # Make request
        response = self._make_request(
            "GET",
            "/api/time/estimates",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get time estimates: {response.text}")
        
        return response.json()
    
    def create_estimate(self, 
                        task_id: str,
                        estimate_type: str,
                        estimate_value: Union[int, float, str, Dict[str, Any]],
                        unit: str = "hours",
                        confidence: Optional[int] = None,
                        notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a time estimate.
        
        Args:
            task_id: Task identifier
            estimate_type: Estimate type
            estimate_value: Estimate value
            unit: Unit of measurement
            confidence: Optional confidence level
            notes: Optional notes
        
        Returns:
            Created time estimate
        """
        # Build estimate data
        estimate_data = {
            'task_id': task_id,
            'estimate_type': estimate_type,
            'estimate_value': estimate_value,
            'unit': unit
        }
        
        if confidence is not None:
            estimate_data['confidence'] = confidence
        
        if notes:
            estimate_data['notes'] = notes
        
        # Make request
        response = self._make_request(
            "POST",
            "/api/time/estimates",
            json=estimate_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create time estimate: {response.text}")
        
        return response.json()
    
    # Productivity
    
    def get_productivity(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get productivity metrics and insights.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            task_ids: Optional task identifiers
        
        Returns:
            Productivity data
        """
        # Build query parameters
        params = {}
        
        if start_date:
            params['start_date'] = start_date.isoformat()
        
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        if task_ids:
            params['task_ids'] = ','.join(task_ids)
        
        # Make request
        response = self._make_request(
            "GET",
            "/api/time/productivity",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get productivity data: {response.text}")
        
        return response.json()
    
    # Reports
    
    def generate_report(self, 
                        report_type: str,
                        task_id: Optional[str] = None,
                        from_date: Optional[datetime] = None,
                        to_date: Optional[datetime] = None,
                        output_format: str = "json") -> Union[Dict[str, Any], str]:
        """
        Generate a time tracking report.
        
        Args:
            report_type: Report type
            task_id: Optional task identifier
            from_date: Optional start date
            to_date: Optional end date
            output_format: Output format
        
        Returns:
            Report data
        """
        # Build query parameters
        params = {
            'format': output_format
        }
        
        if task_id:
            params['task_id'] = task_id
        
        if from_date:
            params['from_date'] = from_date.isoformat()
        
        if to_date:
            params['to_date'] = to_date.isoformat()
        
        # Make request
        response = self._make_request(
            "GET",
            f"/api/time/reports/{report_type}",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to generate report: {response.text}")
        
        if output_format == 'json':
            return response.json()
        else:
            return response.text
    
    # Sync
    
    def sync(self) -> Dict[str, Any]:
        """
        Synchronize data with the server.
        
        Returns:
            Sync result
        """
        # Sync offline entries
        if self.offline_entries:
            self._sync_offline_entries()
        
        # Get latest data
        response = self._make_request(
            "GET",
            "/api/sync/download"
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to sync data: {response.text}")
        
        return response.json()
    
    def __del__(self):
        """Cleanup when the client is deleted."""
        self._stop_sync_thread()
