"""
Multi-Provider AI Service for Tascade AI.

This module provides a unified interface for multiple AI providers,
with support for role-based model selection, fallbacks, and retries.

Inspired by the ai-services-unified module in claude-task-master.
"""

from typing import Dict, List, Optional, Any, Union, Callable
import logging
import time
import json

from .base import BaseAIProvider
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from ..config_manager import ConfigManager

# Maximum number of retries for AI calls
MAX_RETRIES = 3

# Retry delay in seconds (with exponential backoff)
INITIAL_RETRY_DELAY = 1

class MultiProviderAIService(BaseAIProvider):
    """
    Unified AI service that can use multiple providers based on configuration.
    
    This class provides a unified interface for multiple AI providers,
    with support for role-based model selection, fallbacks, and retries.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, project_root: Optional[str] = None):
        """
        Initialize the MultiProviderAIService.
        
        Args:
            config_manager: Optional ConfigManager instance
            project_root: Optional path to the project root directory
        """
        self.config_manager = config_manager or ConfigManager(project_root)
        self.provider_instances = {}
        self.logger = logging.getLogger(__name__)
    
    def _get_provider_instance(self, provider_name: str, model_id: str) -> BaseAIProvider:
        """
        Get or create a provider instance for the specified provider and model.
        
        Args:
            provider_name: Provider name
            model_id: Model ID
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If the provider is not supported
        """
        # Create a cache key for this provider-model combination
        cache_key = f"{provider_name}:{model_id}"
        
        # Return cached instance if available
        if cache_key in self.provider_instances:
            return self.provider_instances[cache_key]
        
        # Create a new provider instance
        if provider_name.lower() == "anthropic":
            provider = AnthropicProvider(model=model_id)
        elif provider_name.lower() == "openai":
            provider = OpenAIProvider(model=model_id)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        # Cache the instance
        self.provider_instances[cache_key] = provider
        
        return provider
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        error_str = str(error).lower()
        
        # Common retryable error patterns
        retryable_patterns = [
            "rate limit",
            "rate_limit",
            "too many requests",
            "timeout",
            "connection",
            "network",
            "server error",
            "internal server error",
            "503",
            "502",
            "429"
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def _extract_error_message(self, error: Exception) -> str:
        """
        Extract a user-friendly error message from an exception.
        
        Args:
            error: Exception to extract message from
            
        Returns:
            User-friendly error message
        """
        error_str = str(error)
        
        # Try to extract a more specific message if it's a JSON string
        try:
            if error_str.startswith('{') and error_str.endswith('}'):
                error_data = json.loads(error_str)
                if isinstance(error_data, dict):
                    # Look for common error message fields
                    for field in ["message", "error", "detail", "details"]:
                        if field in error_data:
                            message = error_data[field]
                            if isinstance(message, str):
                                return message
                            elif isinstance(message, dict) and "message" in message:
                                return message["message"]
        except:
            pass
        
        return error_str
    
    def _attempt_with_retries(self, provider_fn: Callable, params: Dict[str, Any], 
                             provider_name: str, model_id: str, role: str) -> Any:
        """
        Attempt an AI provider call with retries.
        
        Args:
            provider_fn: Provider function to call
            params: Parameters for the function
            provider_name: Provider name (for logging)
            model_id: Model ID (for logging)
            role: Role being attempted (for logging)
            
        Returns:
            Result from the provider function
            
        Raises:
            Exception: If all retry attempts fail
        """
        retries = 0
        last_error = None
        
        while retries <= MAX_RETRIES:
            try:
                if retries > 0:
                    self.logger.info(f"Retry {retries}/{MAX_RETRIES} for {provider_name}/{model_id} ({role})")
                
                return provider_fn(**params)
                
            except Exception as e:
                last_error = e
                
                if self._is_retryable_error(e) and retries < MAX_RETRIES:
                    # Calculate backoff delay
                    delay = INITIAL_RETRY_DELAY * (2 ** retries)
                    
                    self.logger.warning(
                        f"Retryable error with {provider_name}/{model_id} ({role}): "
                        f"{self._extract_error_message(e)}. Retrying in {delay}s..."
                    )
                    
                    time.sleep(delay)
                    retries += 1
                else:
                    # Non-retryable error or max retries reached
                    self.logger.error(
                        f"Error with {provider_name}/{model_id} ({role}): "
                        f"{self._extract_error_message(e)}"
                    )
                    break
        
        # If we get here, all retries failed
        raise last_error
    
    def _unified_service_runner(self, service_type: str, params: Dict[str, Any]) -> Any:
        """
        Run a unified service with role-based provider selection and fallbacks.
        
        Args:
            service_type: Service type ('generate_text', 'generate_object')
            params: Parameters for the service
            
        Returns:
            Result from the service
            
        Raises:
            Exception: If all attempts fail
        """
        # Extract role from params (default to 'main')
        role = params.pop("role", "main")
        
        # Validate role
        if role not in ["main", "research", "fallback"]:
            raise ValueError(f"Invalid role: {role}. Must be 'main', 'research', or 'fallback'")
        
        # Get parameters for this role
        role_params = self.config_manager.get_parameters_for_role(role)
        
        # Determine the sequence of roles to try
        role_sequence = [role]
        
        # Add fallback to the sequence if it's configured and not already in the sequence
        fallback_provider = self.config_manager.get_provider_for_role("fallback")
        if fallback_provider and "fallback" not in role_sequence:
            role_sequence.append("fallback")
        
        # Try each role in sequence
        last_error = None
        
        for attempt_role in role_sequence:
            # Get provider and model for this role
            provider_name = self.config_manager.get_provider_for_role(attempt_role)
            model_id = self.config_manager.get_model_id_for_role(attempt_role)
            
            # Skip if provider or model is not configured
            if not provider_name or not model_id:
                self.logger.warning(f"Skipping {attempt_role} role: provider or model not configured")
                continue
            
            # Get role-specific parameters
            attempt_params = self.config_manager.get_parameters_for_role(attempt_role)
            
            try:
                # Get provider instance
                provider = self._get_provider_instance(provider_name, model_id)
                
                # Determine which provider function to call
                if service_type == "generate_text":
                    provider_fn = provider.generate_text
                elif service_type == "generate_object":
                    provider_fn = provider.generate_json
                else:
                    raise ValueError(f"Unsupported service type: {service_type}")
                
                # Prepare parameters for the provider
                provider_params = params.copy()
                
                # Add role-specific parameters
                provider_params["temperature"] = attempt_params.get("temperature", 0.7)
                
                # Attempt the call with retries
                self.logger.info(f"Attempting {service_type} with {provider_name}/{model_id} ({attempt_role})")
                
                return self._attempt_with_retries(
                    provider_fn, 
                    provider_params,
                    provider_name,
                    model_id,
                    attempt_role
                )
                
            except Exception as e:
                last_error = e
                self.logger.error(
                    f"Failed {service_type} with {provider_name}/{model_id} ({attempt_role}): "
                    f"{self._extract_error_message(e)}"
                )
        
        # If we get here, all attempts failed
        error_message = f"All attempts failed for {service_type}"
        if last_error:
            error_message += f": {self._extract_error_message(last_error)}"
        
        raise RuntimeError(error_message)
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, 
                     temperature: Optional[float] = None, role: str = "main") -> str:
        """
        Generate text using the configured AI provider for the specified role.
        
        Args:
            prompt: The prompt to send to the AI
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            role: Role to use ('main', 'research', or 'fallback')
            
        Returns:
            Generated text
            
        Raises:
            Exception: If text generation fails
        """
        params = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "role": role
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        
        return self._unified_service_runner("generate_text", params)
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None,
                     schema: Optional[Dict[str, Any]] = None, 
                     temperature: Optional[float] = None, role: str = "main") -> Dict[str, Any]:
        """
        Generate a JSON object using the configured AI provider for the specified role.
        
        Args:
            prompt: The prompt to send to the AI
            system_prompt: Optional system prompt
            schema: Optional JSON schema
            temperature: Optional temperature override
            role: Role to use ('main', 'research', or 'fallback')
            
        Returns:
            Generated JSON object
            
        Raises:
            Exception: If JSON generation fails
        """
        params = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "schema": schema,
            "role": role
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        
        return self._unified_service_runner("generate_object", params)
    
    # Implement BaseAIProvider methods
    
    def analyze_task(self, task):
        """Analyze a task using the configured AI provider."""
        prompt = f"""
        Analyze the following task and provide insights:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        Status: {task.status.value}
        Priority: {task.priority.value}
        Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
        Subtasks: {', '.join(task.subtasks) if hasattr(task, 'subtasks') and task.subtasks else 'None'}
        
        Please provide a structured analysis with:
        1. A complexity score from 1-10
        2. Estimated effort in hours
        3. A list of recommendations
        4. An implementation approach
        
        Format your response as a JSON object with these keys:
        - complexity_score (float)
        - estimated_hours (float)
        - recommendations (array of strings)
        - implementation_approach (string)
        """
        
        system_prompt = "You are an expert task analyst. Provide detailed, actionable insights for tasks."
        
        try:
            return self.generate_json(prompt, system_prompt, role="main")
        except Exception as e:
            self.logger.error(f"Task analysis failed: {str(e)}")
            return {
                "complexity_score": 5.0,
                "estimated_hours": 4.0,
                "recommendations": ["Could not generate AI recommendations due to an error"],
                "implementation_approach": "Please retry the analysis or proceed based on your own assessment."
            }
    
    def generate_implementation_guide(self, task, project_rules):
        """Generate an implementation guide for a task."""
        rules_text = "\n".join([f"- {rule.description}" for rule in project_rules]) if project_rules else "No specific project rules."
        
        prompt = f"""
        Generate a detailed implementation guide for the following task:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        Status: {task.status.value}
        Priority: {task.priority.value}
        Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
        
        Project Rules:
        {rules_text}
        
        Please provide a comprehensive implementation guide that includes:
        1. Step-by-step instructions
        2. Best practices to follow
        3. Potential challenges and how to address them
        4. Resources that might be helpful
        
        The guide should be detailed enough for someone to implement the task successfully.
        """
        
        system_prompt = "You are an expert implementation guide creator. Provide detailed, actionable guides for tasks."
        
        try:
            return self.generate_text(prompt, system_prompt, role="main")
        except Exception as e:
            self.logger.error(f"Implementation guide generation failed: {str(e)}")
            return "Could not generate implementation guide due to an error. Please try again later."
    
    def generate_verification_criteria(self, task):
        """Generate verification criteria for a task."""
        prompt = f"""
        Generate verification criteria for the following task:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        Status: {task.status.value}
        Priority: {task.priority.value}
        
        Please provide a comprehensive list of verification criteria that can be used to determine if the task has been completed successfully.
        Each criterion should be specific, measurable, and directly related to the task.
        
        Format the criteria as a numbered list.
        """
        
        system_prompt = "You are an expert in quality assurance. Provide specific, measurable verification criteria for tasks."
        
        try:
            return self.generate_text(prompt, system_prompt, role="main")
        except Exception as e:
            self.logger.error(f"Verification criteria generation failed: {str(e)}")
            return "1. Task implementation meets the requirements specified in the description.\n2. Code or deliverable is functional and error-free."
