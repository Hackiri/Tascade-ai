"""
Base classes for the Task Integration System.

This module defines the core interfaces for integration providers,
authentication, and data synchronization.
"""

from typing import Dict, List, Any, Optional, Union, Callable, Type
from enum import Enum
from datetime import datetime
import uuid
import json
import abc
import logging


class IntegrationType(Enum):
    """Types of integrations supported by the system."""
    GITHUB = "github"
    JIRA = "jira"
    TRELLO = "trello"
    SLACK = "slack"
    DISCORD = "discord"
    CALENDAR = "calendar"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class AuthType(Enum):
    """Types of authentication supported by integrations."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    BASIC = "basic"
    TOKEN = "token"
    CUSTOM = "custom"


class SyncDirection(Enum):
    """Directions for data synchronization."""
    IMPORT = "import"  # From external system to Tascade
    EXPORT = "export"  # From Tascade to external system
    BIDIRECTIONAL = "bidirectional"  # Both ways


class IntegrationStatus(Enum):
    """Status of an integration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class AuthenticationConfig:
    """Configuration for authentication with external systems."""
    
    def __init__(self, 
                 auth_type: AuthType,
                 credentials: Dict[str, Any],
                 scopes: Optional[List[str]] = None,
                 expires_at: Optional[datetime] = None,
                 refresh_token: Optional[str] = None):
        """
        Initialize authentication configuration.
        
        Args:
            auth_type: Type of authentication
            credentials: Authentication credentials
            scopes: Optional scopes for OAuth
            expires_at: Optional expiration time
            refresh_token: Optional refresh token
        """
        self.auth_type = auth_type
        self.credentials = credentials
        self.scopes = scopes or []
        self.expires_at = expires_at
        self.refresh_token = refresh_token
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "auth_type": self.auth_type.value,
            "credentials": self.credentials,
            "scopes": self.scopes,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refresh_token": self.refresh_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthenticationConfig':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            AuthenticationConfig instance
        """
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            auth_type=AuthType(data.get("auth_type", "none")),
            credentials=data.get("credentials", {}),
            scopes=data.get("scopes", []),
            expires_at=expires_at,
            refresh_token=data.get("refresh_token")
        )
    
    def is_expired(self) -> bool:
        """
        Check if authentication is expired.
        
        Returns:
            True if expired, False otherwise
        """
        if not self.expires_at:
            return False
        
        return datetime.now() > self.expires_at


class SyncConfig:
    """Configuration for data synchronization."""
    
    def __init__(self, 
                 direction: SyncDirection,
                 interval_minutes: int = 60,
                 filters: Optional[Dict[str, Any]] = None,
                 mappings: Optional[Dict[str, Any]] = None,
                 last_sync: Optional[datetime] = None):
        """
        Initialize synchronization configuration.
        
        Args:
            direction: Direction of synchronization
            interval_minutes: Interval between syncs in minutes
            filters: Optional filters for data selection
            mappings: Optional field mappings
            last_sync: Optional timestamp of last sync
        """
        self.direction = direction
        self.interval_minutes = interval_minutes
        self.filters = filters or {}
        self.mappings = mappings or {}
        self.last_sync = last_sync
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "direction": self.direction.value,
            "interval_minutes": self.interval_minutes,
            "filters": self.filters,
            "mappings": self.mappings,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncConfig':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            SyncConfig instance
        """
        last_sync = None
        if data.get("last_sync"):
            last_sync = datetime.fromisoformat(data["last_sync"])
        
        return cls(
            direction=SyncDirection(data.get("direction", "import")),
            interval_minutes=data.get("interval_minutes", 60),
            filters=data.get("filters", {}),
            mappings=data.get("mappings", {}),
            last_sync=last_sync
        )


class IntegrationConfig:
    """Configuration for an integration."""
    
    def __init__(self, 
                 id: str,
                 name: str,
                 type: IntegrationType,
                 auth_config: AuthenticationConfig,
                 sync_config: SyncConfig,
                 settings: Optional[Dict[str, Any]] = None,
                 status: IntegrationStatus = IntegrationStatus.INACTIVE,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize integration configuration.
        
        Args:
            id: Unique identifier
            name: Display name
            type: Type of integration
            auth_config: Authentication configuration
            sync_config: Synchronization configuration
            settings: Optional provider-specific settings
            status: Status of the integration
            created_at: When the integration was created
            updated_at: When the integration was last updated
            metadata: Additional metadata
        """
        self.id = id
        self.name = name
        self.type = type
        self.auth_config = auth_config
        self.sync_config = sync_config
        self.settings = settings or {}
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "auth_config": self.auth_config.to_dict(),
            "sync_config": self.sync_config.to_dict(),
            "settings": self.settings,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntegrationConfig':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            IntegrationConfig instance
        """
        auth_config = AuthenticationConfig.from_dict(data.get("auth_config", {}))
        sync_config = SyncConfig.from_dict(data.get("sync_config", {}))
        
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=IntegrationType(data.get("type", "custom")),
            auth_config=auth_config,
            sync_config=sync_config,
            settings=data.get("settings", {}),
            status=IntegrationStatus(data.get("status", "inactive")),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )


class IntegrationProvider(abc.ABC):
    """Base class for integration providers."""
    
    def __init__(self, config: IntegrationConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize an integration provider.
        
        Args:
            config: Integration configuration
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger(f"tascade.integration.{config.type.value}")
    
    @abc.abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the external system.
        
        Returns:
            True if authentication succeeded, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the external system.
        
        Returns:
            Dictionary with test results
        """
        pass
    
    @abc.abstractmethod
    def import_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Import tasks from the external system.
        
        Args:
            filters: Optional filters for task selection
            
        Returns:
            List of imported tasks
        """
        pass
    
    @abc.abstractmethod
    def export_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export tasks to the external system.
        
        Args:
            tasks: Tasks to export
            
        Returns:
            Dictionary with export results
        """
        pass
    
    @abc.abstractmethod
    def sync(self, direction: Optional[SyncDirection] = None) -> Dict[str, Any]:
        """
        Synchronize tasks with the external system.
        
        Args:
            direction: Optional direction to override config
            
        Returns:
            Dictionary with synchronization results
        """
        pass
    
    @abc.abstractmethod
    def get_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get webhooks registered with the external system.
        
        Returns:
            List of webhooks
        """
        pass
    
    @abc.abstractmethod
    def register_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Register a webhook with the external system.
        
        Args:
            url: Webhook URL
            events: Events to trigger the webhook
            
        Returns:
            Dictionary with registration results
        """
        pass
    
    @abc.abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload from the external system.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def refresh_auth_if_needed(self) -> bool:
        """
        Refresh authentication if needed.
        
        Returns:
            True if refresh succeeded or wasn't needed, False otherwise
        """
        if not self.config.auth_config.is_expired():
            return True
        
        try:
            return self._refresh_auth()
        except Exception as e:
            self.logger.error(f"Error refreshing authentication: {e}")
            return False
    
    @abc.abstractmethod
    def _refresh_auth(self) -> bool:
        """
        Refresh authentication.
        
        Returns:
            True if refresh succeeded, False otherwise
        """
        pass
    
    def update_sync_timestamp(self) -> None:
        """Update the last sync timestamp."""
        self.config.sync_config.last_sync = datetime.now()
    
    def map_task_to_external(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a Tascade task to the external system's format.
        
        Args:
            task: Tascade task
            
        Returns:
            Task in external system format
        """
        mappings = self.config.sync_config.mappings
        external_task = {}
        
        for tascade_field, external_field in mappings.get("to_external", {}).items():
            if tascade_field in task:
                external_task[external_field] = task[tascade_field]
        
        # Add any default fields not covered by mappings
        self._add_default_external_fields(task, external_task)
        
        return external_task
    
    def map_external_to_task(self, external_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map an external system task to Tascade format.
        
        Args:
            external_task: External system task
            
        Returns:
            Task in Tascade format
        """
        mappings = self.config.sync_config.mappings
        task = {}
        
        for external_field, tascade_field in mappings.get("to_tascade", {}).items():
            if external_field in external_task:
                task[tascade_field] = external_task[external_field]
        
        # Add any default fields not covered by mappings
        self._add_default_tascade_fields(external_task, task)
        
        return task
    
    @abc.abstractmethod
    def _add_default_external_fields(self, task: Dict[str, Any], external_task: Dict[str, Any]) -> None:
        """
        Add default fields to the external task.
        
        Args:
            task: Tascade task
            external_task: External task to modify
        """
        pass
    
    @abc.abstractmethod
    def _add_default_tascade_fields(self, external_task: Dict[str, Any], task: Dict[str, Any]) -> None:
        """
        Add default fields to the Tascade task.
        
        Args:
            external_task: External system task
            task: Tascade task to modify
        """
        pass