#!/usr/bin/env python3
"""
Mobile API server for Tascade AI.

This module provides a server for the Tascade AI mobile API.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

from .api import MobileTimeTrackingAPI
from ..core.task_timetracking import TaskTimeTrackingSystem


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging."""
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger("tascade.mobile.server")
    
    return logger


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load server configuration.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    # Default configuration
    config = {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
        "secret_key": None,
        "log_level": "INFO"
    }
    
    # Load configuration from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    return config


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Tascade AI Mobile API Server")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Log level")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override configuration with command-line arguments
    if args.host:
        config["host"] = args.host
    
    if args.port:
        config["port"] = args.port
    
    if args.debug:
        config["debug"] = True
    
    if args.log_level:
        config["log_level"] = args.log_level
    
    # Set up logging
    logger = setup_logging(config["log_level"])
    
    # Initialize time tracking system
    time_tracking = TaskTimeTrackingSystem()
    
    # Initialize API
    api = MobileTimeTrackingAPI(
        time_tracking=time_tracking,
        host=config["host"],
        port=config["port"],
        debug=config["debug"],
        secret_key=config["secret_key"],
        logger=logger
    )
    
    # Log configuration
    logger.info(f"Starting server on {config['host']}:{config['port']}")
    if config["debug"]:
        logger.info("Debug mode enabled")
    
    # Run server
    try:
        api.run()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
