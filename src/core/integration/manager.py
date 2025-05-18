"""
Integration Manager for Tascade AI.

This module provides the main interface for managing integrations with
external tools and services.
"""

from typing import Dict, List, Any, Optional, Union, Callable, Type
from datetime import datetime
import json
import os
import logging
import importlib
import uuid
import threading
import time
import schedule

from .base import (
    IntegrationProvider,
    IntegrationConfig,
    IntegrationType,
    AuthType,
    SyncDirection,
    IntegrationStatus
)

# Import providers
from .github import GitHubProvider
from .jira import JiraProvider


class IntegrationManager:
    """Manager for task integrations."""
    
    # Provider mapping
    PROVIDER_MAPPING = {
        IntegrationType.GITHUB: GitHubProvider,
        IntegrationType.JIRA: JiraProvider
    }
    
    def __init__(self, 
                 data_dir: str = None,
                 config_file: str = "integrations.json",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the integration manager.
        
        Args:
            data_dir: Directory for storing integration data
            config_file: Configuration file name
            logger: Optional logger
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.config_file = os.path.join(self.data_dir, config_file)
        self.logger = logger or logging.getLogger("tascade.integration")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize integrations
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.providers: Dict[str, IntegrationProvider] = {}
        
        # Load existing integrations
        self._load_integrations()
        
        # Initialize sync scheduler
        self.scheduler_thread = None
        self.scheduler_running = False
    
    def _load_integrations(self) -> None:
        """Load integrations from the configuration file."""
        if not os.path.exists(self.config_file):
            self.logger.info(f"Integration configuration file not found: {self.config_file}")
            return
        
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
            
            for item in data:
                config = IntegrationConfig.from_dict(item)
                self.integrations[config.id] = config
                
                # Initialize provider if integration is active
                if config.status == IntegrationStatus.ACTIVE:
                    self._initialize_provider(config.id)
        except Exception as e:
            self.logger.error(f"Error loading integrations: {e}")
    
    def _save_integrations(self) -> None:
        """Save integrations to the configuration file."""
        try:
            data = [config.to_dict() for config in self.integrations.values()]
            
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving integrations: {e}")
    
    def _initialize_provider(self, integration_id: str) -> bool:
        """
        Initialize a provider for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            True if initialization succeeded, False otherwise
        """
        if integration_id not in self.integrations:
            self.logger.error(f"Integration not found: {integration_id}")
            return False
        
        config = self.integrations[integration_id]
        
        # Get provider class
        provider_class = self.PROVIDER_MAPPING.get(config.type)
        
        if not provider_class:
            self.logger.error(f"Provider not found for integration type: {config.type}")
            return False
        
        try:
            # Initialize provider
            provider = provider_class(config, self.logger)
            
            # Authenticate
            if not provider.authenticate():
                self.logger.error(f"Authentication failed for integration: {integration_id}")
                config.status = IntegrationStatus.ERROR
                self._save_integrations()
                return False
            
            # Store provider
            self.providers[integration_id] = provider
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing provider for integration {integration_id}: {e}")
            config.status = IntegrationStatus.ERROR
            self._save_integrations()
            return False
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """
        Get an integration by ID.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration configuration or None if not found
        """
        return self.integrations.get(integration_id)
    
    def get_integrations(self, 
                         type: Optional[IntegrationType] = None,
                         status: Optional[IntegrationStatus] = None) -> List[IntegrationConfig]:
        """
        Get integrations, optionally filtered by type and status.
        
        Args:
            type: Optional integration type filter
            status: Optional status filter
            
        Returns:
            List of integration configurations
        """
        result = list(self.integrations.values())
        
        if type:
            result = [config for config in result if config.type == type]
        
        if status:
            result = [config for config in result if config.status == status]
        
        return result
    
    def create_integration(self, 
                          name: str,
                          type: IntegrationType,
                          auth_config: Dict[str, Any],
                          sync_config: Dict[str, Any],
                          settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new integration.
        
        Args:
            name: Display name
            type: Integration type
            auth_config: Authentication configuration
            sync_config: Synchronization configuration
            settings: Optional provider-specific settings
            
        Returns:
            Dictionary with creation results
        """
        # Create authentication config
        auth_type = AuthType(auth_config.pop("auth_type", "none"))
        auth = {
            "auth_type": auth_type,
            "credentials": auth_config.get("credentials", {}),
            "scopes": auth_config.get("scopes", []),
            "expires_at": auth_config.get("expires_at"),
            "refresh_token": auth_config.get("refresh_token")
        }
        auth_obj = AuthenticationConfig.from_dict(auth)
        
        # Create synchronization config
        sync_direction = SyncDirection(sync_config.pop("direction", "import"))
        sync = {
            "direction": sync_direction,
            "interval_minutes": sync_config.get("interval_minutes", 60),
            "filters": sync_config.get("filters", {}),
            "mappings": sync_config.get("mappings", {}),
            "last_sync": None
        }
        sync_obj = SyncConfig.from_dict(sync)
        
        # Create integration config
        integration_id = str(uuid.uuid4())
        config = IntegrationConfig(
            id=integration_id,
            name=name,
            type=type,
            auth_config=auth_obj,
            sync_config=sync_obj,
            settings=settings or {},
            status=IntegrationStatus.PENDING
        )
        
        # Store integration
        self.integrations[integration_id] = config
        self._save_integrations()
        
        return {
            "success": True,
            "integration_id": integration_id,
            "name": name,
            "type": type.value,
            "status": config.status.value
        }
    
    def update_integration(self, 
                          integration_id: str,
                          name: Optional[str] = None,
                          auth_config: Optional[Dict[str, Any]] = None,
                          sync_config: Optional[Dict[str, Any]] = None,
                          settings: Optional[Dict[str, Any]] = None,
                          status: Optional[IntegrationStatus] = None) -> Dict[str, Any]:
        """
        Update an existing integration.
        
        Args:
            integration_id: Integration ID
            name: Optional new name
            auth_config: Optional new authentication configuration
            sync_config: Optional new synchronization configuration
            settings: Optional new provider-specific settings
            status: Optional new status
            
        Returns:
            Dictionary with update results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        config = self.integrations[integration_id]
        
        # Update name
        if name is not None:
            config.name = name
        
        # Update authentication config
        if auth_config is not None:
            auth_type = AuthType(auth_config.pop("auth_type", config.auth_config.auth_type.value))
            auth = {
                "auth_type": auth_type,
                "credentials": auth_config.get("credentials", config.auth_config.credentials),
                "scopes": auth_config.get("scopes", config.auth_config.scopes),
                "expires_at": auth_config.get("expires_at", config.auth_config.expires_at),
                "refresh_token": auth_config.get("refresh_token", config.auth_config.refresh_token)
            }
            config.auth_config = AuthenticationConfig.from_dict(auth)
        
        # Update synchronization config
        if sync_config is not None:
            sync_direction = SyncDirection(sync_config.pop("direction", config.sync_config.direction.value))
            sync = {
                "direction": sync_direction,
                "interval_minutes": sync_config.get("interval_minutes", config.sync_config.interval_minutes),
                "filters": sync_config.get("filters", config.sync_config.filters),
                "mappings": sync_config.get("mappings", config.sync_config.mappings),
                "last_sync": config.sync_config.last_sync
            }
            config.sync_config = SyncConfig.from_dict(sync)
        
        # Update settings
        if settings is not None:
            config.settings.update(settings)
        
        # Update status
        if status is not None:
            old_status = config.status
            config.status = status
            
            # Initialize or remove provider based on status change
            if old_status != IntegrationStatus.ACTIVE and status == IntegrationStatus.ACTIVE:
                self._initialize_provider(integration_id)
            elif old_status == IntegrationStatus.ACTIVE and status != IntegrationStatus.ACTIVE:
                if integration_id in self.providers:
                    del self.providers[integration_id]
        
        # Update timestamp
        config.updated_at = datetime.now()
        
        # Save changes
        self._save_integrations()
        
        return {
            "success": True,
            "integration_id": integration_id,
            "name": config.name,
            "type": config.type.value,
            "status": config.status.value
        }
    
    def delete_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Delete an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with deletion results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Remove provider if active
        if integration_id in self.providers:
            del self.providers[integration_id]
        
        # Remove integration
        del self.integrations[integration_id]
        
        # Save changes
        self._save_integrations()
        
        return {
            "success": True,
            "integration_id": integration_id
        }
    
    def activate_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Activate an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with activation results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        config = self.integrations[integration_id]
        
        # Initialize provider
        if not self._initialize_provider(integration_id):
            return {
                "success": False,
                "error": "Failed to initialize provider"
            }
        
        # Update status
        config.status = IntegrationStatus.ACTIVE
        config.updated_at = datetime.now()
        
        # Save changes
        self._save_integrations()
        
        return {
            "success": True,
            "integration_id": integration_id,
            "status": config.status.value
        }
    
    def deactivate_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Deactivate an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with deactivation results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        config = self.integrations[integration_id]
        
        # Remove provider
        if integration_id in self.providers:
            del self.providers[integration_id]
        
        # Update status
        config.status = IntegrationStatus.INACTIVE
        config.updated_at = datetime.now()
        
        # Save changes
        self._save_integrations()
        
        return {
            "success": True,
            "integration_id": integration_id,
            "status": config.status.value
        }
    
    def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Test an integration connection.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Dictionary with test results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Test connection
        try:
            results = provider.test_connection()
            return results
        except Exception as e:
            self.logger.error(f"Error testing integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_tasks(self, integration_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Import tasks from an integration.
        
        Args:
            integration_id: Integration ID
            filters: Optional filters for task selection
            
        Returns:
            Dictionary with import results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Import tasks
        try:
            tasks = provider.import_tasks(filters)
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks)
            }
        except Exception as e:
            self.logger.error(f"Error importing tasks from integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_tasks(self, integration_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export tasks to an integration.
        
        Args:
            integration_id: Integration ID
            tasks: Tasks to export
            
        Returns:
            Dictionary with export results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Export tasks
        try:
            results = provider.export_tasks(tasks)
            return results
        except Exception as e:
            self.logger.error(f"Error exporting tasks to integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_integration(self, integration_id: str, direction: Optional[SyncDirection] = None) -> Dict[str, Any]:
        """
        Synchronize tasks with an integration.
        
        Args:
            integration_id: Integration ID
            direction: Optional direction to override config
            
        Returns:
            Dictionary with synchronization results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Sync tasks
        try:
            results = provider.sync(direction)
            return results
        except Exception as e:
            self.logger.error(f"Error syncing integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def register_webhook(self, integration_id: str, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Register a webhook with an integration.
        
        Args:
            integration_id: Integration ID
            url: Webhook URL
            events: Events to trigger the webhook
            
        Returns:
            Dictionary with registration results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Register webhook
        try:
            results = provider.register_webhook(url, events)
            return results
        except Exception as e:
            self.logger.error(f"Error registering webhook for integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_webhook(self, integration_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload from an integration.
        
        Args:
            integration_id: Integration ID
            payload: Webhook payload
            
        Returns:
            Dictionary with processing results
        """
        if integration_id not in self.integrations:
            return {
                "success": False,
                "error": f"Integration not found: {integration_id}"
            }
        
        # Get or initialize provider
        provider = self.providers.get(integration_id)
        
        if not provider:
            if not self._initialize_provider(integration_id):
                return {
                    "success": False,
                    "error": "Failed to initialize provider"
                }
            provider = self.providers[integration_id]
        
        # Process webhook
        try:
            results = provider.process_webhook(payload)
            return results
        except Exception as e:
            self.logger.error(f"Error processing webhook for integration {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_sync_scheduler(self) -> bool:
        """
        Start the synchronization scheduler.
        
        Returns:
            True if scheduler started, False otherwise
        """
        if self.scheduler_running:
            self.logger.warning("Sync scheduler is already running")
            return True
        
        # Set up scheduler
        self._setup_sync_schedules()
        
        # Start scheduler thread
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        return True
    
    def stop_sync_scheduler(self) -> bool:
        """
        Stop the synchronization scheduler.
        
        Returns:
            True if scheduler stopped, False otherwise
        """
        if not self.scheduler_running:
            self.logger.warning("Sync scheduler is not running")
            return True
        
        # Stop scheduler
        self.scheduler_running = False
        
        # Clear schedules
        schedule.clear()
        
        return True
    
    def _setup_sync_schedules(self) -> None:
        """
        Set up synchronization schedules for active integrations.
        """
        # Clear existing schedules
        schedule.clear()
        
        # Set up schedules for active integrations
        for integration_id, config in self.integrations.items():
            if config.status == IntegrationStatus.ACTIVE:
                interval_minutes = config.sync_config.interval_minutes
                
                # Schedule sync job
                schedule.every(interval_minutes).minutes.do(
                    self._scheduled_sync, integration_id=integration_id
                )
                
                self.logger.info(f"Scheduled sync for integration {integration_id} every {interval_minutes} minutes")
    
    def _scheduled_sync(self, integration_id: str) -> None:
        """
        Perform a scheduled synchronization.
        
        Args:
            integration_id: Integration ID
        """
        self.logger.info(f"Running scheduled sync for integration {integration_id}")
        
        try:
            results = self.sync_integration(integration_id)
            
            if results.get("success"):
                self.logger.info(f"Scheduled sync for integration {integration_id} completed successfully")
            else:
                self.logger.error(f"Scheduled sync for integration {integration_id} failed: {results.get('error')}")
        except Exception as e:
            self.logger.error(f"Error in scheduled sync for integration {integration_id}: {e}")
    
    def _run_scheduler(self) -> None:
        """
        Run the scheduler loop.
        """
        self.logger.info("Starting integration sync scheduler")
        
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in sync scheduler: {e}")
                time.sleep(5)  # Wait a bit longer on error