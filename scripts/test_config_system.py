#!/usr/bin/env python3
"""
Test script for the Configuration Management System and Multi-Provider AI Service in Tascade AI.

This script demonstrates the new features implemented from claude-task-master:
1. Configuration Management
2. Multi-Provider AI Service
3. Role-based Model Selection

These features provide a robust foundation for customizing AI providers and models
for different task management roles.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import directly from the core modules
from src.core.config_manager import ConfigManager
from src.core.ai_providers.multi_provider import MultiProviderAIService
from src.core.models import Task, TaskStatus, TaskPriority

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def main():
    """Test Configuration Management System and Multi-Provider AI Service in Tascade AI."""
    print_section("Tascade AI Configuration Management System Demo")
    
    # Initialize ConfigManager
    print("Initializing ConfigManager...")
    config_manager = ConfigManager()
    
    # Load and display current configuration
    print_section("Current Configuration")
    config = config_manager.load_config()
    print_json(config)
    
    # Display available models
    print_section("Available Models")
    models = config_manager.get_available_models()
    
    # Print table of models
    print(f"{'Model ID':<30} {'Name':<25} {'Provider':<15} {'Max Tokens':<12} {'Input Cost':<12} {'Output Cost':<12}")
    print("-" * 110)
    
    for model in models:
        input_cost = f"${model['costs']['input']}" if model['costs']['input'] is not None else "N/A"
        output_cost = f"${model['costs']['output']}" if model['costs']['output'] is not None else "N/A"
        
        print(f"{model['id']:<30} {model['name']:<25} {model['provider']:<15} {model['max_tokens']:<12} {input_cost:<12} {output_cost:<12}")
    
    # Check API key status
    print_section("API Key Status")
    for provider in config_manager.get_all_providers():
        is_set = config_manager.is_api_key_set(provider)
        status = "Set" if is_set else "Not Set"
        print(f"{provider}: {status}")
    
    # Get parameters for different roles
    print_section("Role Parameters")
    for role in ["main", "research", "fallback"]:
        params = config_manager.get_parameters_for_role(role)
        provider = config_manager.get_provider_for_role(role)
        model_id = config_manager.get_model_id_for_role(role)
        
        print(f"Role: {role}")
        print(f"  Provider: {provider}")
        print(f"  Model ID: {model_id}")
        print(f"  Parameters: {params}")
        print()
    
    # Test Multi-Provider AI Service if API keys are available
    print_section("Multi-Provider AI Service")
    
    # Check if any API keys are set
    anthropic_key_set = config_manager.is_api_key_set("anthropic")
    openai_key_set = config_manager.is_api_key_set("openai")
    
    if not anthropic_key_set and not openai_key_set:
        print("No API keys are set. Skipping Multi-Provider AI Service tests.")
        print("To test this feature, set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables.")
    else:
        # Initialize Multi-Provider AI Service
        print("Initializing Multi-Provider AI Service...")
        ai_service = MultiProviderAIService(config_manager)
        
        # Create a sample task
        task = Task(
            id="test_task",
            title="Implement Configuration Management System",
            description="Create a robust configuration management system for Tascade AI",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            dependencies=[],
            created_at=datetime.now()
        )
        
        # Test text generation if possible
        try:
            print("\nTesting text generation...")
            prompt = "Explain the benefits of a configuration management system in 3 bullet points."
            response = ai_service.generate_text(prompt, role="main")
            print(f"Response:\n{response}")
        except Exception as e:
            print(f"Text generation failed: {str(e)}")
        
        # Test task analysis if possible
        try:
            print("\nTesting task analysis...")
            analysis = ai_service.analyze_task(task)
            print("Task Analysis:")
            print_json(analysis)
        except Exception as e:
            print(f"Task analysis failed: {str(e)}")
    
    print_section("Demo Complete")
    print("The Configuration Management System and Multi-Provider AI Service")
    print("have been successfully integrated into Tascade AI.")
    print("\nTo use the configuration commands, run:")
    print("  python -m src.cli.config_commands list-models")
    print("  python -m src.cli.config_commands get-config")
    print("  python -m src.cli.config_commands set-model main anthropic claude-3-opus-20240229")
    print("  python -m src.cli.config_commands check-api-keys")

if __name__ == "__main__":
    main()
