"""
Configuration Commands for Tascade AI CLI.

This module provides command-line interface commands for managing Tascade AI configuration,
including AI providers, models, and global settings.

Inspired by the commands module in claude-task-master.
"""

import argparse
import sys
import os
import json
from typing import Dict, List, Optional, Any, Union
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config_manager import ConfigManager, SUPPORTED_MODELS

# Initialize colorama
colorama.init()

def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def print_info(message: str) -> None:
    """Print an info message in blue."""
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

def list_models_command(args: argparse.Namespace) -> None:
    """
    List all available models with their details.
    
    Args:
        args: Command-line arguments
    """
    config_manager = ConfigManager()
    models = config_manager.get_available_models()
    
    # Filter by provider if specified
    if args.provider:
        models = [m for m in models if m["provider"].lower() == args.provider.lower()]
    
    # Filter by role if specified
    if args.role:
        models = [m for m in models if args.role in m["allowed_roles"]]
    
    # Prepare table data
    table_data = []
    for model in models:
        input_cost = model["costs"]["input"] if model["costs"]["input"] is not None else "N/A"
        output_cost = model["costs"]["output"] if model["costs"]["output"] is not None else "N/A"
        
        table_data.append([
            model["id"],
            model["name"],
            model["provider"],
            model["max_tokens"],
            f"${input_cost}" if input_cost != "N/A" else "N/A",
            f"${output_cost}" if output_cost != "N/A" else "N/A",
            ", ".join(model["allowed_roles"])
        ])
    
    # Sort by provider and model name
    table_data.sort(key=lambda x: (x[2], x[1]))
    
    # Print table
    headers = ["Model ID", "Name", "Provider", "Max Tokens", "Input Cost*", "Output Cost*", "Allowed Roles"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("* Cost per 1M tokens in USD")
    
    # Print current configuration
    print_info("\nCurrent Configuration:")
    for role in ["main", "research", "fallback"]:
        provider = config_manager.get_provider_for_role(role)
        model_id = config_manager.get_model_id_for_role(role)
        
        if provider and model_id:
            print(f"  {role.capitalize()}: {provider}/{model_id}")
        else:
            print(f"  {role.capitalize()}: Not configured")

def get_config_command(args: argparse.Namespace) -> None:
    """
    Get the current configuration.
    
    Args:
        args: Command-line arguments
    """
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if args.json:
        print(json.dumps(config, indent=2))
    else:
        # Print models configuration
        print_info("Models Configuration:")
        for role in ["main", "research", "fallback"]:
            model_config = config["models"][role]
            provider = model_config.get("provider")
            model_id = model_config.get("model_id")
            
            if provider and model_id:
                print(f"  {role.capitalize()}:")
                print(f"    Provider: {provider}")
                print(f"    Model ID: {model_id}")
                print(f"    Max Tokens: {model_config.get('max_tokens', 'Not set')}")
                print(f"    Temperature: {model_config.get('temperature', 'Not set')}")
            else:
                print(f"  {role.capitalize()}: Not configured")
        
        # Print global configuration
        print_info("\nGlobal Configuration:")
        for key, value in config["global"].items():
            print(f"  {key}: {value}")
        
        # Print API key status
        print_info("\nAPI Key Status:")
        for provider in config_manager.get_all_providers():
            is_set = config_manager.is_api_key_set(provider)
            status = f"{Fore.GREEN}Set{Style.RESET_ALL}" if is_set else f"{Fore.RED}Not Set{Style.RESET_ALL}"
            print(f"  {provider}: {status}")

def set_model_command(args: argparse.Namespace) -> None:
    """
    Set the model for a specific role.
    
    Args:
        args: Command-line arguments
    """
    config_manager = ConfigManager()
    
    # Validate role
    if args.role not in ["main", "research", "fallback"]:
        print_error(f"Invalid role: {args.role}. Must be 'main', 'research', or 'fallback'")
        return
    
    # Validate provider
    if not config_manager.validate_provider(args.provider):
        print_error(f"Invalid provider: {args.provider}")
        print_info(f"Supported providers: {', '.join(config_manager.get_all_providers())}")
        return
    
    # Validate provider-model combination
    if not config_manager.validate_provider_model_combination(args.provider, args.model):
        print_warning(f"Unknown model {args.model} for provider {args.provider}")
        print_info(f"Available models for {args.provider}:")
        for model_id, model_info in SUPPORTED_MODELS.get(args.provider, {}).items():
            print(f"  - {model_id}: {model_info.get('name', model_id)}")
        
        # Ask for confirmation
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            return
    
    # Set model configuration
    try:
        config_manager.set_model_config_for_role(
            args.role,
            args.provider,
            args.model,
            args.max_tokens,
            args.temperature
        )
        print_success(f"Successfully set {args.role} model to {args.provider}/{args.model}")
    except Exception as e:
        print_error(f"Error setting model: {str(e)}")

def set_global_command(args: argparse.Namespace) -> None:
    """
    Set a global configuration value.
    
    Args:
        args: Command-line arguments
    """
    config_manager = ConfigManager()
    
    # Convert value to appropriate type
    value = args.value
    if value.lower() == "true":
        value = True
    elif value.lower() == "false":
        value = False
    elif value.isdigit():
        value = int(value)
    elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
        value = float(value)
    
    # Set global configuration
    try:
        config_manager.set_global_config(args.key, value)
        print_success(f"Successfully set {args.key} to {value}")
    except Exception as e:
        print_error(f"Error setting global configuration: {str(e)}")

def check_api_keys_command(args: argparse.Namespace) -> None:
    """
    Check the status of API keys for all providers.
    
    Args:
        args: Command-line arguments
    """
    config_manager = ConfigManager()
    
    print_info("API Key Status:")
    for provider in config_manager.get_all_providers():
        is_set = config_manager.is_api_key_set(provider)
        status = f"{Fore.GREEN}Set{Style.RESET_ALL}" if is_set else f"{Fore.RED}Not Set{Style.RESET_ALL}"
        
        # Get environment variable name for this provider
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY"
        }
        env_var = env_var_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
        
        print(f"  {provider}: {status} (Environment Variable: {env_var})")
    
    # Print instructions for setting API keys
    print_info("\nTo set API keys, use environment variables:")
    print("  export ANTHROPIC_API_KEY=your_api_key")
    print("  export OPENAI_API_KEY=your_api_key")
    print("  etc.")

def main() -> None:
    """Main entry point for the configuration commands."""
    parser = argparse.ArgumentParser(description="Tascade AI Configuration Commands")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # list-models command
    list_models_parser = subparsers.add_parser("list-models", help="List all available models")
    list_models_parser.add_argument("--provider", help="Filter by provider")
    list_models_parser.add_argument("--role", help="Filter by role (main, research, fallback)")
    list_models_parser.set_defaults(func=list_models_command)
    
    # get-config command
    get_config_parser = subparsers.add_parser("get-config", help="Get the current configuration")
    get_config_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    get_config_parser.set_defaults(func=get_config_command)
    
    # set-model command
    set_model_parser = subparsers.add_parser("set-model", help="Set the model for a specific role")
    set_model_parser.add_argument("role", choices=["main", "research", "fallback"], help="Role to set model for")
    set_model_parser.add_argument("provider", help="Provider name")
    set_model_parser.add_argument("model", help="Model ID")
    set_model_parser.add_argument("--max-tokens", type=int, help="Maximum tokens")
    set_model_parser.add_argument("--temperature", type=float, help="Temperature")
    set_model_parser.set_defaults(func=set_model_command)
    
    # set-global command
    set_global_parser = subparsers.add_parser("set-global", help="Set a global configuration value")
    set_global_parser.add_argument("key", help="Configuration key")
    set_global_parser.add_argument("value", help="Configuration value")
    set_global_parser.set_defaults(func=set_global_command)
    
    # check-api-keys command
    check_api_keys_parser = subparsers.add_parser("check-api-keys", help="Check the status of API keys")
    check_api_keys_parser.set_defaults(func=check_api_keys_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Run the appropriate command
    args.func(args)

if __name__ == "__main__":
    main()
