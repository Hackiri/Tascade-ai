"""
Jira integration provider for Tascade AI.

This module provides functionality for integrating with Jira, including
issues, projects, and workflow features.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json
import logging
import requests
import base64
import re

from .base import (
    IntegrationProvider, 
    IntegrationConfig, 
    IntegrationType, 
    AuthType, 
    SyncDirection,
    IntegrationStatus
)


class JiraProvider(IntegrationProvider):
    """Jira integration provider."""
    
    # Default field mappings
    DEFAULT_MAPPINGS = {
        "to_external": {
            "title": "summary",
            "description": "description",
            "status": "status",
            "priority": "priority",
            "assignee": "assignee",
            "due_date": "duedate"
        },
        "to_tascade": {
            "summary": "title",
            "description": "description",
            "status": "status",
            "priority": "priority",
            "assignee": "assignee",
            "duedate": "due_date"
        }
    }
    
    # Status mappings - these will be overridden with actual statuses from Jira
    STATUS_MAP = {
        "pending": "To Do",
        "in_progress": "In Progress",
        "done": "Done",
        "review": "In Review",
        "cancelled": "Cancelled"
    }
    
    # Priority mappings
    PRIORITY_MAP = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Highest"
    }
    
    def __init__(self, config: IntegrationConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize a Jira integration provider.
        
        Args:
            config: Integration configuration
            logger: Optional logger
        """
        super().__init__(config, logger)
        
        # Ensure the config type is Jira
        if config.type != IntegrationType.JIRA:
            raise ValueError(f"Invalid integration type: {config.type}. Expected: {IntegrationType.JIRA}")
        
        # Set up default mappings if not provided
        if not self.config.sync_config.mappings:
            self.config.sync_config.mappings = self.DEFAULT_MAPPINGS
        
        # Extract Jira information from settings
        self.base_url = self.config.settings.get("base_url")
        self.project_key = self.config.settings.get("project_key")
        
        if not self.base_url:
            self.logger.warning("Jira base URL not provided")
        
        if not self.project_key:
            self.logger.warning("Jira project key not provided")
        
        # Initialize status and priority mappings
        self._initialize_mappings()
    
    def _initialize_mappings(self) -> None:
        """Initialize status and priority mappings from Jira."""
        # This would typically fetch the available statuses and priorities from Jira
        # For now, we'll use the default mappings
        pass
    
    def authenticate(self) -> bool:
        """
        Authenticate with Jira.
        
        Returns:
            True if authentication succeeded, False otherwise
        """
        # Check if authentication is needed
        if self.config.auth_config.is_expired():
            if not self._refresh_auth():
                return False
        
        # Test authentication
        try:
            response = self._make_request("GET", "/rest/api/2/myself")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Jira authentication error: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Jira.
        
        Returns:
            Dictionary with test results
        """
        results = {
            "success": False,
            "auth": False,
            "project_access": False,
            "issues_access": False,
            "details": {}
        }
        
        # Test authentication
        try:
            auth_response = self._make_request("GET", "/rest/api/2/myself")
            results["auth"] = auth_response.status_code == 200
            results["details"]["auth"] = {
                "status_code": auth_response.status_code,
                "user": auth_response.json().get("displayName") if auth_response.status_code == 200 else None
            }
        except Exception as e:
            self.logger.error(f"Jira authentication test error: {e}")
            results["details"]["auth"] = {"error": str(e)}
        
        # Test project access
        if self.project_key:
            try:
                project_response = self._make_request("GET", f"/rest/api/2/project/{self.project_key}")
                results["project_access"] = project_response.status_code == 200
                results["details"]["project"] = {
                    "status_code": project_response.status_code,
                    "name": project_response.json().get("name") if project_response.status_code == 200 else None
                }
            except Exception as e:
                self.logger.error(f"Jira project test error: {e}")
                results["details"]["project"] = {"error": str(e)}
        
        # Test issues access
        if self.project_key:
            try:
                jql = f"project={self.project_key}"
                issues_response = self._make_request("GET", "/rest/api/2/search", params={"jql": jql, "maxResults": 1})
                results["issues_access"] = issues_response.status_code == 200
                results["details"]["issues"] = {
                    "status_code": issues_response.status_code,
                    "count": issues_response.json().get("total", 0) if issues_response.status_code == 200 else 0
                }
            except Exception as e:
                self.logger.error(f"Jira issues test error: {e}")
                results["details"]["issues"] = {"error": str(e)}
        
        # Overall success
        results["success"] = results["auth"] and results["project_access"] and results["issues_access"]
        
        return results
    
    def import_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Import issues from Jira as tasks.
        
        Args:
            filters: Optional filters for issue selection
            
        Returns:
            List of imported tasks
        """
        if not self.base_url or not self.project_key:
            self.logger.error("Jira base URL or project key not provided")
            return []
        
        # Combine filters with config filters
        combined_filters = {**(self.config.sync_config.filters), **(filters or {})}
        
        # Build JQL query
        jql = f"project={self.project_key}"
        
        if "status" in combined_filters:
            jql += f" AND status='{combined_filters['status']}'"
        
        if "assignee" in combined_filters:
            assignee = combined_filters["assignee"]
            if assignee == "unassigned":
                jql += " AND assignee IS EMPTY"
            else:
                jql += f" AND assignee='{assignee}'"
        
        if "priority" in combined_filters:
            jql += f" AND priority='{combined_filters['priority']}'"
        
        if "updated_since" in combined_filters:
            jql += f" AND updated >= '{combined_filters['updated_since']}'"
        
        # Get issues
        try:
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,description,status,priority,assignee,duedate,created,updated"
            }
            
            response = self._make_request("GET", "/rest/api/2/search", params=params)
            
            if response.status_code != 200:
                self.logger.error(f"Jira issues import error: {response.status_code} - {response.text}")
                return []
            
            issues = response.json().get("issues", [])
            
            # Map issues to tasks
            tasks = []
            for issue in issues:
                task = self.map_external_to_task(issue)
                tasks.append(task)
            
            # Update last sync timestamp
            self.update_sync_timestamp()
            
            return tasks
        except Exception as e:
            self.logger.error(f"Jira issues import error: {e}")
            return []
    
    def export_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export tasks to Jira as issues.
        
        Args:
            tasks: Tasks to export
            
        Returns:
            Dictionary with export results
        """
        if not self.base_url or not self.project_key:
            self.logger.error("Jira base URL or project key not provided")
            return {"success": False, "error": "Jira configuration not provided"}
        
        results = {
            "success": True,
            "created": [],
            "updated": [],
            "errors": []
        }
        
        for task in tasks:
            # Check if the task has a Jira issue key
            issue_key = task.get("metadata", {}).get("jira_issue_key")
            
            if issue_key:
                # Update existing issue
                try:
                    issue_data = self.map_task_to_external(task)
                    response = self._make_request("PUT", f"/rest/api/2/issue/{issue_key}", json=issue_data)
                    
                    if response.status_code == 204:
                        results["updated"].append({
                            "task_id": task.get("id"),
                            "issue_key": issue_key
                        })
                    else:
                        results["errors"].append({
                            "task_id": task.get("id"),
                            "error": f"Failed to update issue: {response.status_code} - {response.text}"
                        })
                except Exception as e:
                    results["errors"].append({
                        "task_id": task.get("id"),
                        "error": f"Error updating issue: {str(e)}"
                    })
            else:
                # Create new issue
                try:
                    issue_data = self.map_task_to_external(task)
                    
                    # Add project key
                    if "fields" not in issue_data:
                        issue_data["fields"] = {}
                    
                    issue_data["fields"]["project"] = {"key": self.project_key}
                    
                    # Add issue type
                    issue_data["fields"]["issuetype"] = {"name": "Task"}
                    
                    response = self._make_request("POST", "/rest/api/2/issue", json=issue_data)
                    
                    if response.status_code == 201:
                        issue = response.json()
                        results["created"].append({
                            "task_id": task.get("id"),
                            "issue_key": issue.get("key"),
                            "issue_url": f"{self.base_url}/browse/{issue.get('key')}"
                        })
                    else:
                        results["errors"].append({
                            "task_id": task.get("id"),
                            "error": f"Failed to create issue: {response.status_code} - {response.text}"
                        })
                except Exception as e:
                    results["errors"].append({
                        "task_id": task.get("id"),
                        "error": f"Error creating issue: {str(e)}"
                    })
        
        # Update success flag if there were any errors
        if results["errors"]:
            results["success"] = False
        
        # Update last sync timestamp
        self.update_sync_timestamp()
        
        return results
    
    def sync(self, direction: Optional[SyncDirection] = None) -> Dict[str, Any]:
        """
        Synchronize tasks with Jira issues.
        
        Args:
            direction: Optional direction to override config
            
        Returns:
            Dictionary with synchronization results
        """
        # Use provided direction or default from config
        sync_direction = direction or self.config.sync_config.direction
        
        results = {
            "success": True,
            "direction": sync_direction.value,
            "imported": [],
            "exported": [],
            "errors": []
        }
        
        # Import from Jira
        if sync_direction in [SyncDirection.IMPORT, SyncDirection.BIDIRECTIONAL]:
            try:
                imported_tasks = self.import_tasks()
                results["imported"] = imported_tasks
            except Exception as e:
                results["success"] = False
                results["errors"].append({
                    "operation": "import",
                    "error": str(e)
                })
        
        # Export to Jira
        if sync_direction in [SyncDirection.EXPORT, SyncDirection.BIDIRECTIONAL]:
            # This would require access to the task manager to get tasks
            # For now, we'll just note that export would happen here
            results["exported"] = []
            results["errors"].append({
                "operation": "export",
                "error": "Export operation requires task manager access"
            })
        
        return results
    
    def get_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get webhooks registered with Jira.
        
        Returns:
            List of webhooks
        """
        try:
            response = self._make_request("GET", "/rest/webhooks/1.0/webhook")
            
            if response.status_code != 200:
                self.logger.error(f"Jira webhooks error: {response.status_code} - {response.text}")
                return []
            
            return response.json()
        except Exception as e:
            self.logger.error(f"Jira webhooks error: {e}")
            return []
    
    def register_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Register a webhook with Jira.
        
        Args:
            url: Webhook URL
            events: Events to trigger the webhook
            
        Returns:
            Dictionary with registration results
        """
        if not self.project_key:
            self.logger.error("Jira project key not provided")
            return {"success": False, "error": "Project key not provided"}
        
        # Map events to Jira events
        jira_events = []
        for event in events:
            if event == "issue_created":
                jira_events.append("jira:issue_created")
            elif event == "issue_updated":
                jira_events.append("jira:issue_updated")
            elif event == "issue_deleted":
                jira_events.append("jira:issue_deleted")
            else:
                jira_events.append(event)
        
        # Prepare webhook data
        webhook_data = {
            "name": "Tascade AI Integration",
            "url": url,
            "events": jira_events,
            "filters": {
                "issue-related-events-section": f"project = {self.project_key}"
            },
            "excludeBody": False
        }
        
        try:
            response = self._make_request("POST", "/rest/webhooks/1.0/webhook", json=webhook_data)
            
            if response.status_code == 201:
                webhook = response.json()
                return {
                    "success": True,
                    "id": webhook.get("id"),
                    "url": webhook.get("url"),
                    "events": webhook.get("events")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create webhook: {response.status_code} - {response.text}"
                }
        except Exception as e:
            self.logger.error(f"Jira webhook registration error: {e}")
            return {"success": False, "error": str(e)}
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload from Jira.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Dictionary with processing results
        """
        event_type = payload.get("webhookEvent")
        
        if not event_type:
            return {"success": False, "error": "Invalid webhook payload"}
        
        # Process based on event type
        if "issue" in payload:
            # Issue event
            issue = payload["issue"]
            task = self.map_external_to_task(issue)
            
            return {
                "success": True,
                "event_type": event_type,
                "task": task,
                "metadata": {
                    "jira_issue_key": issue.get("key"),
                    "jira_issue_url": f"{self.base_url}/browse/{issue.get('key')}"
                }
            }
        else:
            # Other event
            return {
                "success": True,
                "event_type": event_type,
                "data": payload
            }
    
    def _refresh_auth(self) -> bool:
        """
        Refresh authentication.
        
        Returns:
            True if refresh succeeded, False otherwise
        """
        # Jira API tokens don't expire, but we'll check if we need to refresh OAuth tokens
        if self.config.auth_config.auth_type == AuthType.OAUTH and self.config.auth_config.refresh_token:
            # This would require implementing OAuth refresh logic
            # For now, we'll just return False
            return False
        
        return True
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a request to the Jira API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        # Ensure authentication
        if not self.config.auth_config.credentials:
            raise ValueError("Jira authentication credentials not provided")
        
        # Build URL
        url = f"{self.base_url}{endpoint}"
        
        # Add authentication
        headers = kwargs.get("headers", {})
        
        if self.config.auth_config.auth_type == AuthType.API_KEY:
            email = self.config.auth_config.credentials.get("email")
            api_key = self.config.auth_config.credentials.get("api_key")
            auth = base64.b64encode(f"{email}:{api_key}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        elif self.config.auth_config.auth_type == AuthType.BASIC:
            username = self.config.auth_config.credentials.get("username")
            password = self.config.auth_config.credentials.get("password")
            auth = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        elif self.config.auth_config.auth_type == AuthType.OAUTH:
            token = self.config.auth_config.credentials.get("access_token")
            headers["Authorization"] = f"Bearer {token}"
        
        # Add Content-Type header
        headers["Content-Type"] = "application/json"
        
        # Update kwargs with headers
        kwargs["headers"] = headers
        
        # Make request
        return requests.request(method, url, **kwargs)
    
    def _add_default_external_fields(self, task: Dict[str, Any], external_task: Dict[str, Any]) -> None:
        """
        Add default fields to the Jira issue.
        
        Args:
            task: Tascade task
            external_task: Jira issue to modify
        """
        # Ensure fields object exists
        if "fields" not in external_task:
            external_task["fields"] = {}
        
        # Map title to summary
        if "title" in task and "summary" not in external_task["fields"]:
            external_task["fields"]["summary"] = task["title"]
        
        # Map description
        if "description" in task and "description" not in external_task["fields"]:
            external_task["fields"]["description"] = task["description"]
        
        # Map status
        if "status" in task and "status" not in external_task["fields"]:
            status = task["status"]
            jira_status = self.STATUS_MAP.get(status)
            if jira_status:
                external_task["fields"]["status"] = {"name": jira_status}
        
        # Map priority
        if "priority" in task and "priority" not in external_task["fields"]:
            priority = task["priority"]
            jira_priority = self.PRIORITY_MAP.get(priority)
            if jira_priority:
                external_task["fields"]["priority"] = {"name": jira_priority}
        
        # Map assignee
        if "assignee" in task and "assignee" not in external_task["fields"]:
            assignee = task["assignee"]
            if assignee:
                external_task["fields"]["assignee"] = {"name": assignee}
        
        # Map due date
        if "due_date" in task and "duedate" not in external_task["fields"]:
            due_date = task["due_date"]
            if due_date:
                external_task["fields"]["duedate"] = due_date
    
    def _add_default_tascade_fields(self, external_task: Dict[str, Any], task: Dict[str, Any]) -> None:
        """
        Add default fields to the Tascade task.
        
        Args:
            external_task: Jira issue
            task: Tascade task to modify
        """
        # Extract fields
        fields = external_task.get("fields", {})
        
        # Map summary to title
        if "summary" in fields and "title" not in task:
            task["title"] = fields["summary"]
        
        # Map description
        if "description" in fields and "description" not in task:
            task["description"] = fields["description"]
        
        # Map status
        if "status" in fields and "status" not in task:
            status = fields["status"]
            if isinstance(status, dict):
                status_name = status.get("name")
                # Reverse lookup in STATUS_MAP
                for tascade_status, jira_status in self.STATUS_MAP.items():
                    if jira_status == status_name:
                        task["status"] = tascade_status
                        break
                else:
                    # Default if not found
                    task["status"] = "pending"
            else:
                task["status"] = "pending"
        
        # Map priority
        if "priority" in fields and "priority" not in task:
            priority = fields["priority"]
            if isinstance(priority, dict):
                priority_name = priority.get("name")
                # Reverse lookup in PRIORITY_MAP
                for tascade_priority, jira_priority in self.PRIORITY_MAP.items():
                    if jira_priority == priority_name:
                        task["priority"] = tascade_priority
                        break
                else:
                    # Default if not found
                    task["priority"] = "medium"
            else:
                task["priority"] = "medium"
        
        # Map assignee
        if "assignee" in fields and "assignee" not in task:
            assignee = fields["assignee"]
            if isinstance(assignee, dict):
                task["assignee"] = assignee.get("name") or assignee.get("displayName")
        
        # Map due date
        if "duedate" in fields and "due_date" not in task:
            task["due_date"] = fields["duedate"]
        
        # Extract Jira metadata
        task["metadata"] = task.get("metadata", {})
        task["metadata"]["jira_issue_key"] = external_task.get("key")
        task["metadata"]["jira_issue_url"] = f"{self.base_url}/browse/{external_task.get('key')}"
        
        # Set source
        task["source"] = "jira"