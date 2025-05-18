"""
GitHub integration provider for Tascade AI.

This module provides functionality for integrating with GitHub, including
issues, pull requests, and project management features.
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


class GitHubProvider(IntegrationProvider):
    """GitHub integration provider."""
    
    # GitHub API base URL
    API_BASE_URL = "https://api.github.com"
    
    # Default field mappings
    DEFAULT_MAPPINGS = {
        "to_external": {
            "title": "title",
            "description": "body",
            "status": "state",
            "priority": "labels",
            "assignee": "assignee",
            "due_date": "milestone"
        },
        "to_tascade": {
            "title": "title",
            "body": "description",
            "state": "status",
            "labels": "priority",
            "assignee": "assignee",
            "milestone": "due_date"
        }
    }
    
    # Status mappings
    STATUS_MAP = {
        "pending": "open",
        "in_progress": "open",
        "done": "closed",
        "review": "open",
        "cancelled": "closed"
    }
    
    # Reverse status mappings
    REVERSE_STATUS_MAP = {
        "open": "pending",
        "closed": "done"
    }
    
    def __init__(self, config: IntegrationConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize a GitHub integration provider.
        
        Args:
            config: Integration configuration
            logger: Optional logger
        """
        super().__init__(config, logger)
        
        # Ensure the config type is GitHub
        if config.type != IntegrationType.GITHUB:
            raise ValueError(f"Invalid integration type: {config.type}. Expected: {IntegrationType.GITHUB}")
        
        # Set up default mappings if not provided
        if not self.config.sync_config.mappings:
            self.config.sync_config.mappings = self.DEFAULT_MAPPINGS
        
        # Extract repository information from settings
        self.owner = self.config.settings.get("owner")
        self.repo = self.config.settings.get("repo")
        
        if not self.owner or not self.repo:
            self.logger.warning("GitHub repository owner or name not provided")
    
    def authenticate(self) -> bool:
        """
        Authenticate with GitHub.
        
        Returns:
            True if authentication succeeded, False otherwise
        """
        # Check if authentication is needed
        if self.config.auth_config.is_expired():
            if not self._refresh_auth():
                return False
        
        # Test authentication
        try:
            response = self._make_request("GET", "/user")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub authentication error: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to GitHub.
        
        Returns:
            Dictionary with test results
        """
        results = {
            "success": False,
            "auth": False,
            "repo_access": False,
            "issues_access": False,
            "details": {}
        }
        
        # Test authentication
        try:
            auth_response = self._make_request("GET", "/user")
            results["auth"] = auth_response.status_code == 200
            results["details"]["auth"] = {
                "status_code": auth_response.status_code,
                "user": auth_response.json().get("login") if auth_response.status_code == 200 else None
            }
        except Exception as e:
            self.logger.error(f"GitHub authentication test error: {e}")
            results["details"]["auth"] = {"error": str(e)}
        
        # Test repository access
        if self.owner and self.repo:
            try:
                repo_response = self._make_request("GET", f"/repos/{self.owner}/{self.repo}")
                results["repo_access"] = repo_response.status_code == 200
                results["details"]["repo"] = {
                    "status_code": repo_response.status_code,
                    "name": repo_response.json().get("full_name") if repo_response.status_code == 200 else None
                }
            except Exception as e:
                self.logger.error(f"GitHub repository test error: {e}")
                results["details"]["repo"] = {"error": str(e)}
        
        # Test issues access
        if self.owner and self.repo:
            try:
                issues_response = self._make_request("GET", f"/repos/{self.owner}/{self.repo}/issues", params={"per_page": 1})
                results["issues_access"] = issues_response.status_code == 200
                results["details"]["issues"] = {
                    "status_code": issues_response.status_code,
                    "count": len(issues_response.json()) if issues_response.status_code == 200 else 0
                }
            except Exception as e:
                self.logger.error(f"GitHub issues test error: {e}")
                results["details"]["issues"] = {"error": str(e)}
        
        # Overall success
        results["success"] = results["auth"] and results["repo_access"] and results["issues_access"]
        
        return results
    
    def import_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Import issues from GitHub as tasks.
        
        Args:
            filters: Optional filters for issue selection
            
        Returns:
            List of imported tasks
        """
        if not self.owner or not self.repo:
            self.logger.error("GitHub repository owner or name not provided")
            return []
        
        # Combine filters with config filters
        combined_filters = {**(self.config.sync_config.filters), **(filters or {})}
        
        # Convert filters to GitHub API parameters
        params = {
            "state": combined_filters.get("state", "all"),
            "per_page": 100
        }
        
        if "labels" in combined_filters:
            params["labels"] = ",".join(combined_filters["labels"])
        
        if "assignee" in combined_filters:
            params["assignee"] = combined_filters["assignee"]
        
        if "milestone" in combined_filters:
            params["milestone"] = combined_filters["milestone"]
        
        # Get issues
        try:
            response = self._make_request("GET", f"/repos/{self.owner}/{self.repo}/issues", params=params)
            
            if response.status_code != 200:
                self.logger.error(f"GitHub issues import error: {response.status_code} - {response.text}")
                return []
            
            issues = response.json()
            
            # Map issues to tasks
            tasks = []
            for issue in issues:
                # Skip pull requests
                if "pull_request" in issue:
                    continue
                
                task = self.map_external_to_task(issue)
                tasks.append(task)
            
            # Update last sync timestamp
            self.update_sync_timestamp()
            
            return tasks
        except Exception as e:
            self.logger.error(f"GitHub issues import error: {e}")
            return []
    
    def export_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export tasks to GitHub as issues.
        
        Args:
            tasks: Tasks to export
            
        Returns:
            Dictionary with export results
        """
        if not self.owner or not self.repo:
            self.logger.error("GitHub repository owner or name not provided")
            return {"success": False, "error": "Repository information not provided"}
        
        results = {
            "success": True,
            "created": [],
            "updated": [],
            "errors": []
        }
        
        for task in tasks:
            # Check if the task has a GitHub issue ID
            issue_number = task.get("metadata", {}).get("github_issue_number")
            
            if issue_number:
                # Update existing issue
                try:
                    issue_data = self.map_task_to_external(task)
                    response = self._make_request("PATCH", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", json=issue_data)
                    
                    if response.status_code == 200:
                        results["updated"].append({
                            "task_id": task.get("id"),
                            "issue_number": issue_number,
                            "issue_url": response.json().get("html_url")
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
                    response = self._make_request("POST", f"/repos/{self.owner}/{self.repo}/issues", json=issue_data)
                    
                    if response.status_code == 201:
                        issue = response.json()
                        results["created"].append({
                            "task_id": task.get("id"),
                            "issue_number": issue.get("number"),
                            "issue_url": issue.get("html_url")
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
        Synchronize tasks with GitHub issues.
        
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
        
        # Import from GitHub
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
        
        # Export to GitHub
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
        Get webhooks registered with GitHub.
        
        Returns:
            List of webhooks
        """
        if not self.owner or not self.repo:
            self.logger.error("GitHub repository owner or name not provided")
            return []
        
        try:
            response = self._make_request("GET", f"/repos/{self.owner}/{self.repo}/hooks")
            
            if response.status_code != 200:
                self.logger.error(f"GitHub webhooks error: {response.status_code} - {response.text}")
                return []
            
            return response.json()
        except Exception as e:
            self.logger.error(f"GitHub webhooks error: {e}")
            return []
    
    def register_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Register a webhook with GitHub.
        
        Args:
            url: Webhook URL
            events: Events to trigger the webhook
            
        Returns:
            Dictionary with registration results
        """
        if not self.owner or not self.repo:
            self.logger.error("GitHub repository owner or name not provided")
            return {"success": False, "error": "Repository information not provided"}
        
        # Prepare webhook data
        webhook_data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        try:
            response = self._make_request("POST", f"/repos/{self.owner}/{self.repo}/hooks", json=webhook_data)
            
            if response.status_code == 201:
                webhook = response.json()
                return {
                    "success": True,
                    "id": webhook.get("id"),
                    "url": webhook.get("config", {}).get("url"),
                    "events": webhook.get("events")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create webhook: {response.status_code} - {response.text}"
                }
        except Exception as e:
            self.logger.error(f"GitHub webhook registration error: {e}")
            return {"success": False, "error": str(e)}
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload from GitHub.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Dictionary with processing results
        """
        event_type = payload.get("action")
        
        if not event_type:
            return {"success": False, "error": "Invalid webhook payload"}
        
        # Process based on event type
        if "issue" in payload:
            # Issue event
            issue = payload["issue"]
            task = self.map_external_to_task(issue)
            
            return {
                "success": True,
                "event_type": f"issue_{event_type}",
                "task": task,
                "metadata": {
                    "github_issue_number": issue.get("number"),
                    "github_issue_url": issue.get("html_url")
                }
            }
        elif "pull_request" in payload:
            # Pull request event
            pr = payload["pull_request"]
            
            return {
                "success": True,
                "event_type": f"pull_request_{event_type}",
                "data": {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "url": pr.get("html_url"),
                    "state": pr.get("state"),
                    "user": pr.get("user", {}).get("login")
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
        # GitHub tokens don't expire, but we'll check if we need to refresh OAuth tokens
        if self.config.auth_config.auth_type == AuthType.OAUTH and self.config.auth_config.refresh_token:
            # This would require implementing OAuth refresh logic
            # For now, we'll just return False
            return False
        
        return True
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a request to the GitHub API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        # Ensure authentication
        if not self.config.auth_config.credentials:
            raise ValueError("GitHub authentication credentials not provided")
        
        # Build URL
        url = f"{self.API_BASE_URL}{endpoint}"
        
        # Add authentication
        headers = kwargs.get("headers", {})
        
        if self.config.auth_config.auth_type == AuthType.TOKEN:
            token = self.config.auth_config.credentials.get("token")
            headers["Authorization"] = f"token {token}"
        elif self.config.auth_config.auth_type == AuthType.BASIC:
            username = self.config.auth_config.credentials.get("username")
            password = self.config.auth_config.credentials.get("password")
            auth = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        elif self.config.auth_config.auth_type == AuthType.OAUTH:
            token = self.config.auth_config.credentials.get("access_token")
            headers["Authorization"] = f"token {token}"
        
        # Add User-Agent
        headers["User-Agent"] = "Tascade-AI-Integration"
        
        # Add Accept header for API version
        headers["Accept"] = "application/vnd.github.v3+json"
        
        # Update kwargs with headers
        kwargs["headers"] = headers
        
        # Make request
        return requests.request(method, url, **kwargs)
    
    def _add_default_external_fields(self, task: Dict[str, Any], external_task: Dict[str, Any]) -> None:
        """
        Add default fields to the GitHub issue.
        
        Args:
            task: Tascade task
            external_task: GitHub issue to modify
        """
        # Map status
        if "status" in task and "state" not in external_task:
            status = task["status"]
            external_task["state"] = self.STATUS_MAP.get(status, "open")
        
        # Map priority to labels
        if "priority" in task and "labels" not in external_task:
            priority = task["priority"]
            external_task["labels"] = [priority]
        
        # Map description to body
        if "description" in task and "body" not in external_task:
            external_task["body"] = task["description"]
        
        # Add Tascade metadata
        if "body" in external_task:
            metadata = f"\n\n<!-- Tascade Task ID: {task.get('id')} -->"
            external_task["body"] += metadata
    
    def _add_default_tascade_fields(self, external_task: Dict[str, Any], task: Dict[str, Any]) -> None:
        """
        Add default fields to the Tascade task.
        
        Args:
            external_task: GitHub issue
            task: Tascade task to modify
        """
        # Map state to status
        if "state" in external_task and "status" not in task:
            state = external_task["state"]
            task["status"] = self.REVERSE_STATUS_MAP.get(state, "pending")
        
        # Map labels to priority
        if "labels" in external_task and "priority" not in task:
            labels = external_task["labels"]
            if labels and isinstance(labels, list):
                # Use the first label as priority
                task["priority"] = labels[0].get("name") if isinstance(labels[0], dict) else labels[0]
            else:
                task["priority"] = "medium"
        
        # Map body to description
        if "body" in external_task and "description" not in task:
            body = external_task["body"]
            
            # Remove Tascade metadata
            body = re.sub(r"<!-- Tascade Task ID: .* -->", "", body).strip()
            
            task["description"] = body
        
        # Extract GitHub metadata
        task["metadata"] = task.get("metadata", {})
        task["metadata"]["github_issue_number"] = external_task.get("number")
        task["metadata"]["github_issue_url"] = external_task.get("html_url")
        
        # Set source
        task["source"] = "github"