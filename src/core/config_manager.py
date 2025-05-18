"""
Configuration Manager for Tascade AI.

This module provides functionality for managing configuration settings,
including AI providers, models, and global settings.

Inspired by the config-manager module in claude-task-master.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

# Default configuration values
DEFAULT_CONFIG = {
    "models": {
        "main": {
            "provider": "anthropic",
            "model_id": "claude-3-opus-20240229",
            "max_tokens": 64000,
            "temperature": 0.2
        },
        "research": {
            "provider": "openai",
            "model_id": "gpt-4o",
            "max_tokens": 8000,
            "temperature": 0.1
        },
        "fallback": {
            "provider": None,
            "model_id": None,
            "max_tokens": 4000,
            "temperature": 0.3
        }
    },
    "global": {
        "log_level": "info",
        "debug": False,
        "default_subtasks": 5,
        "default_num_tasks": 10,
        "default_priority": "medium",
        "project_name": "Tascade AI Project"
    }
}

# Supported models with their capabilities and costs
SUPPORTED_MODELS = {
    "anthropic": {
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "description": "Most powerful Claude model for complex tasks",
            "max_tokens": 200000,
            "input_cost": 15.0,  # Cost per 1M tokens in USD
            "output_cost": 75.0,  # Cost per 1M tokens in USD
            "allowed_roles": ["main", "research", "fallback"]
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "description": "Balanced Claude model for most tasks",
            "max_tokens": 200000,
            "input_cost": 3.0,
            "output_cost": 15.0,
            "allowed_roles": ["main", "research", "fallback"]
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "description": "Fastest Claude model for simpler tasks",
            "max_tokens": 200000,
            "input_cost": 0.25,
            "output_cost": 1.25,
            "allowed_roles": ["main", "research", "fallback"]
        }
    },
    "openai": {
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "Most capable OpenAI model",
            "max_tokens": 128000,
            "input_cost": 5.0,
            "output_cost": 15.0,
            "allowed_roles": ["main", "research", "fallback"]
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "description": "Powerful and cost-effective OpenAI model",
            "max_tokens": 128000,
            "input_cost": 10.0,
            "output_cost": 30.0,
            "allowed_roles": ["main", "research", "fallback"]
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "Fast and economical OpenAI model",
            "max_tokens": 16000,
            "input_cost": 0.5,
            "output_cost": 1.5,
            "allowed_roles": ["main", "research", "fallback"]
        }
    }
}

# Configuration file name
CONFIG_FILE_NAME = ".tascadeconfig"

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class ConfigManager:
    """
    Manages configuration settings for Tascade AI.
    
    This class provides methods for loading, validating, and updating configuration
    settings, including AI provider settings, model selection, and global preferences.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            project_root: Optional path to the project root directory
        """
        self.project_root = project_root or self._find_project_root()
        self.config = None
        self.load_config()
    
    def _find_project_root(self) -> str:
        """
        Find the project root directory.
        
        Returns:
            Path to the project root directory
        """
        # Start with the current working directory
        current_dir = os.getcwd()
        
        # Look for common project root indicators
        root_indicators = [
            ".git",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "src"
        ]
        
        # Traverse up the directory tree
        while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
            # Check if any indicators exist in this directory
            for indicator in root_indicators:
                if os.path.exists(os.path.join(current_dir, indicator)):
                    return current_dir
            
            # Move up one directory
            current_dir = os.path.dirname(current_dir)
        
        # If no project root found, use the current directory
        return os.getcwd()
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load the configuration from file or create default if not exists.
        
        Args:
            force_reload: If True, reload the config even if already loaded
            
        Returns:
            The loaded configuration dictionary
        """
        if self.config is not None and not force_reload:
            return self.config
        
        config_path = os.path.join(self.project_root, CONFIG_FILE_NAME)
        
        # If config file exists, load it
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Validate the loaded config
                self.config = self._validate_config(loaded_config)
                return self.config
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}")
            except Exception as e:
                raise ConfigurationError(f"Error loading configuration: {str(e)}")
        else:
            # Create default config
            self.config = DEFAULT_CONFIG.copy()
            self.save_config()
            return self.config
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the configuration and fill in missing values with defaults.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validated configuration dictionary
        """
        validated_config = DEFAULT_CONFIG.copy()
        
        # Update with provided values, keeping the structure
        if "models" in config:
            for role in ["main", "research", "fallback"]:
                if role in config["models"]:
                    for key, value in config["models"][role].items():
                        if key in validated_config["models"][role]:
                            validated_config["models"][role][key] = value
        
        if "global" in config:
            for key, value in config["global"].items():
                if key in validated_config["global"]:
                    validated_config["global"][key] = value
        
        # Validate provider-model combinations
        for role in ["main", "research"]:
            provider = validated_config["models"][role]["provider"]
            model_id = validated_config["models"][role]["model_id"]
            
            if provider and model_id and not self.validate_provider_model_combination(provider, model_id):
                logging.warning(f"Unknown model {model_id} for provider {provider} in {role} role")
        
        return validated_config
    
    def save_config(self) -> bool:
        """
        Save the current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config:
            return False
        
        config_path = os.path.join(self.project_root, CONFIG_FILE_NAME)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            return False
    
    def validate_provider(self, provider: str) -> bool:
        """
        Validate if a provider is supported.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            True if provider is supported, False otherwise
        """
        return provider in SUPPORTED_MODELS
    
    def validate_provider_model_combination(self, provider: str, model_id: str) -> bool:
        """
        Validate if a provider-model combination is supported.
        
        Args:
            provider: Provider name
            model_id: Model ID
            
        Returns:
            True if the combination is supported, False otherwise
        """
        return (
            provider in SUPPORTED_MODELS and
            model_id in SUPPORTED_MODELS.get(provider, {})
        )
    
    def get_model_config_for_role(self, role: str) -> Dict[str, Any]:
        """
        Get the model configuration for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Model configuration dictionary
        """
        if role not in ["main", "research", "fallback"]:
            raise ValueError(f"Invalid role: {role}. Must be 'main', 'research', or 'fallback'")
        
        return self.config["models"][role]
    
    def get_provider_for_role(self, role: str) -> Optional[str]:
        """
        Get the provider for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Provider name or None if not set
        """
        return self.get_model_config_for_role(role).get("provider")
    
    def get_model_id_for_role(self, role: str) -> Optional[str]:
        """
        Get the model ID for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Model ID or None if not set
        """
        return self.get_model_config_for_role(role).get("model_id")
    
    def get_max_tokens_for_role(self, role: str) -> int:
        """
        Get the maximum tokens for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Maximum tokens
        """
        return self.get_model_config_for_role(role).get("max_tokens", 4000)
    
    def get_temperature_for_role(self, role: str) -> float:
        """
        Get the temperature for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Temperature value
        """
        return self.get_model_config_for_role(role).get("temperature", 0.7)
    
    def set_model_config_for_role(self, role: str, provider: str, model_id: str,
                                max_tokens: Optional[int] = None, 
                                temperature: Optional[float] = None) -> bool:
        """
        Set the model configuration for a specific role.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            provider: Provider name
            model_id: Model ID
            max_tokens: Optional maximum tokens
            temperature: Optional temperature
            
        Returns:
            True if successful, False otherwise
        """
        if role not in ["main", "research", "fallback"]:
            raise ValueError(f"Invalid role: {role}. Must be 'main', 'research', or 'fallback'")
        
        if not self.validate_provider(provider):
            raise ValueError(f"Invalid provider: {provider}")
        
        if not self.validate_provider_model_combination(provider, model_id):
            logging.warning(f"Unknown model {model_id} for provider {provider}")
        
        self.config["models"][role]["provider"] = provider
        self.config["models"][role]["model_id"] = model_id
        
        if max_tokens is not None:
            self.config["models"][role]["max_tokens"] = max_tokens
        
        if temperature is not None:
            self.config["models"][role]["temperature"] = temperature
        
        return self.save_config()
    
    def get_global_config(self) -> Dict[str, Any]:
        """
        Get the global configuration.
        
        Returns:
            Global configuration dictionary
        """
        return self.config["global"]
    
    def get_log_level(self) -> str:
        """
        Get the log level.
        
        Returns:
            Log level string
        """
        return self.get_global_config().get("log_level", "info")
    
    def get_debug_flag(self) -> bool:
        """
        Get the debug flag.
        
        Returns:
            Debug flag boolean
        """
        return self.get_global_config().get("debug", False)
    
    def get_default_subtasks(self) -> int:
        """
        Get the default number of subtasks.
        
        Returns:
            Default number of subtasks
        """
        return self.get_global_config().get("default_subtasks", 5)
    
    def get_default_num_tasks(self) -> int:
        """
        Get the default number of tasks.
        
        Returns:
            Default number of tasks
        """
        return self.get_global_config().get("default_num_tasks", 10)
    
    def get_default_priority(self) -> str:
        """
        Get the default priority.
        
        Returns:
            Default priority string
        """
        return self.get_global_config().get("default_priority", "medium")
    
    def get_project_name(self) -> str:
        """
        Get the project name.
        
        Returns:
            Project name string
        """
        return self.get_global_config().get("project_name", "Tascade AI Project")
    
    def set_global_config(self, key: str, value: Any) -> bool:
        """
        Set a global configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful, False otherwise
        """
        if key not in self.config["global"]:
            logging.warning(f"Unknown global configuration key: {key}")
        
        self.config["global"][key] = value
        return self.save_config()
    
    def get_parameters_for_role(self, role: str) -> Dict[str, Any]:
        """
        Get the parameters for a specific role, including model-specific overrides.
        
        Args:
            role: Role name ('main', 'research', or 'fallback')
            
        Returns:
            Dictionary with parameters (max_tokens, temperature)
        """
        model_config = self.get_model_config_for_role(role)
        provider = model_config.get("provider")
        model_id = model_config.get("model_id")
        
        # Start with the configured values
        params = {
            "max_tokens": model_config.get("max_tokens", 4000),
            "temperature": model_config.get("temperature", 0.7)
        }
        
        # Apply model-specific overrides if available
        if provider and model_id and self.validate_provider_model_combination(provider, model_id):
            model_info = SUPPORTED_MODELS[provider][model_id]
            
            # Override max_tokens if model has a lower limit
            if "max_tokens" in model_info and model_info["max_tokens"] < params["max_tokens"]:
                params["max_tokens"] = model_info["max_tokens"]
        
        return params
    
    def is_api_key_set(self, provider: str) -> bool:
        """
        Check if the API key for a provider is set in the environment.
        
        Args:
            provider: Provider name
            
        Returns:
            True if the API key is set, False otherwise
        """
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY"
        }
        
        env_var = env_var_map.get(provider.lower())
        if not env_var:
            return False
        
        return bool(os.environ.get(env_var))
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available models with their details.
        
        Returns:
            List of model information dictionaries
        """
        models = []
        
        for provider, provider_models in SUPPORTED_MODELS.items():
            for model_id, model_info in provider_models.items():
                models.append({
                    "id": model_id,
                    "name": model_info.get("name", model_id),
                    "provider": provider,
                    "description": model_info.get("description", ""),
                    "max_tokens": model_info.get("max_tokens"),
                    "costs": {
                        "input": model_info.get("input_cost"),
                        "output": model_info.get("output_cost")
                    },
                    "allowed_roles": model_info.get("allowed_roles", ["main", "research", "fallback"])
                })
        
        return models
    
    def is_config_file_present(self) -> bool:
        """
        Check if the configuration file exists.
        
        Returns:
            True if the file exists, False otherwise
        """
        config_path = os.path.join(self.project_root, CONFIG_FILE_NAME)
        return os.path.exists(config_path)
    
    def get_all_providers(self) -> List[str]:
        """
        Get a list of all supported providers.
        
        Returns:
            List of provider names
        """
        return list(SUPPORTED_MODELS.keys())
