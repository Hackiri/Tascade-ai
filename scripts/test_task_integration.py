#!/usr/bin/env python3
"""
Test script for the Task Integration System.

This script demonstrates the functionality of the Task Integration System,
including creating, updating, and managing integrations with external services.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.task_integration import TaskIntegrationSystem
from src.core.integration.base import IntegrationType, AuthType, SyncDirection, IntegrationStatus
from src.core.task_manager import TaskManager
from src.core.models import Task, TaskStatus, TaskPriority


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("tascade.test")


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_result(result):
    """Print a result dictionary."""
    print(json.dumps(result, indent=2))


def test_available_integrations(integration_system):
    """Test getting available integrations."""
    print_section("Available Integrations")
    
    integrations = integration_system.get_available_integrations()
    
    print(f"Found {len(integrations)} available integration types:")
    for integration in integrations:
        print(f"- {integration['name']} ({integration['type']}): {integration['description']}")
        print(f"  Auth types: {', '.join(integration['auth_types'])}")
        print(f"  Features: {', '.join(integration['features'])}")


def test_create_github_integration(integration_system):
    """Test creating a GitHub integration."""
    print_section("Creating GitHub Integration")
    
    # Create GitHub integration
    result = integration_system.create_integration(
        name="Test GitHub Integration",
        type="github",
        auth_config={
            "auth_type": "token",
            "credentials": {
                "token": "github_token_placeholder"
            }
        },
        sync_config={
            "direction": "bidirectional",
            "interval_minutes": 30,
            "filters": {
                "state": "all",
                "labels": ["bug", "enhancement"]
            }
        },
        settings={
            "owner": "example",
            "repo": "test-repo"
        }
    )
    
    print_result(result)
    
    return result.get("integration_id")


def test_create_jira_integration(integration_system):
    """Test creating a Jira integration."""
    print_section("Creating Jira Integration")
    
    # Create Jira integration
    result = integration_system.create_integration(
        name="Test Jira Integration",
        type="jira",
        auth_config={
            "auth_type": "api_key",
            "credentials": {
                "email": "user@example.com",
                "api_key": "jira_api_key_placeholder"
            }
        },
        sync_config={
            "direction": "import",
            "interval_minutes": 60,
            "filters": {
                "status": "Open",
                "assignee": "currentUser()"
            }
        },
        settings={
            "base_url": "https://example.atlassian.net",
            "project_key": "TEST"
        }
    )
    
    print_result(result)
    
    return result.get("integration_id")


def test_get_integrations(integration_system):
    """Test getting configured integrations."""
    print_section("Configured Integrations")
    
    integrations = integration_system.get_integrations()
    
    print(f"Found {len(integrations)} configured integrations:")
    for integration in integrations:
        print(f"- {integration['name']} ({integration['type']}): {integration['status']}")
        print(f"  ID: {integration['id']}")
        print(f"  Created: {integration['created_at']}")


def test_update_integration(integration_system, integration_id):
    """Test updating an integration."""
    print_section(f"Updating Integration {integration_id}")
    
    # Update integration
    result = integration_system.update_integration(
        integration_id=integration_id,
        name="Updated GitHub Integration",
        sync_config={
            "interval_minutes": 15
        }
    )
    
    print_result(result)


def test_activate_integration(integration_system, integration_id):
    """Test activating an integration."""
    print_section(f"Activating Integration {integration_id}")
    
    # Activate integration
    result = integration_system.activate_integration(integration_id)
    
    print_result(result)


def test_test_integration(integration_system, integration_id):
    """Test testing an integration connection."""
    print_section(f"Testing Integration {integration_id}")
    
    # Test integration
    result = integration_system.test_integration(integration_id)
    
    print_result(result)


def test_import_tasks(integration_system, integration_id):
    """Test importing tasks from an integration."""
    print_section(f"Importing Tasks from Integration {integration_id}")
    
    # Import tasks
    result = integration_system.import_tasks(
        integration_id=integration_id,
        filters={
            "state": "open",
            "labels": ["bug"]
        }
    )
    
    print_result(result)


def test_export_tasks(integration_system, integration_id, task_manager):
    """Test exporting tasks to an integration."""
    print_section(f"Exporting Tasks to Integration {integration_id}")
    
    # Create some test tasks
    task1 = Task(
        title="Test Task 1",
        description="This is a test task for export",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        due_date=(datetime.now() + timedelta(days=7)).isoformat()
    )
    
    task2 = Task(
        title="Test Task 2",
        description="Another test task for export",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=(datetime.now() + timedelta(days=3)).isoformat()
    )
    
    # Add tasks to task manager
    task_id1 = task_manager.add_task(task1)
    task_id2 = task_manager.add_task(task2)
    
    print(f"Created test tasks with IDs: {task_id1}, {task_id2}")
    
    # Export tasks
    result = integration_system.export_tasks(
        integration_id=integration_id,
        task_ids=[task_id1, task_id2]
    )
    
    print_result(result)


def test_sync_integration(integration_system, integration_id):
    """Test synchronizing an integration."""
    print_section(f"Synchronizing Integration {integration_id}")
    
    # Sync integration
    result = integration_system.sync_integration(
        integration_id=integration_id,
        direction="import"
    )
    
    print_result(result)


def test_scheduler(integration_system):
    """Test the synchronization scheduler."""
    print_section("Sync Scheduler")
    
    # Start scheduler
    start_result = integration_system.start_sync_scheduler()
    print("Start scheduler result:")
    print_result(start_result)
    
    print("Scheduler is running. In a real application, it would periodically sync integrations.")
    print("Press Enter to stop the scheduler...")
    input()
    
    # Stop scheduler
    stop_result = integration_system.stop_sync_scheduler()
    print("Stop scheduler result:")
    print_result(stop_result)


def test_webhook(integration_system, integration_id):
    """Test processing a webhook payload."""
    print_section(f"Processing Webhook for Integration {integration_id}")
    
    # Simulate a GitHub issue webhook payload
    webhook_payload = {
        "action": "opened",
        "issue": {
            "number": 123,
            "title": "Test Issue from Webhook",
            "body": "This is a test issue created via webhook",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignee": {"login": "testuser"},
            "html_url": "https://github.com/example/test-repo/issues/123"
        },
        "repository": {
            "full_name": "example/test-repo"
        }
    }
    
    # Process webhook
    result = integration_system.process_webhook(
        integration_id=integration_id,
        payload=webhook_payload
    )
    
    print_result(result)


def test_deactivate_integration(integration_system, integration_id):
    """Test deactivating an integration."""
    print_section(f"Deactivating Integration {integration_id}")
    
    # Deactivate integration
    result = integration_system.deactivate_integration(integration_id)
    
    print_result(result)


def test_delete_integration(integration_system, integration_id):
    """Test deleting an integration."""
    print_section(f"Deleting Integration {integration_id}")
    
    # Delete integration
    result = integration_system.delete_integration(integration_id)
    
    print_result(result)


def main():
    """Run the Task Integration System test."""
    logger = setup_logging()
    
    print_section("Task Integration System Test")
    
    # Create a data directory in the current directory for testing
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize task manager
    task_manager = TaskManager(data_dir=data_dir)
    
    # Initialize integration system
    integration_system = TaskIntegrationSystem(
        task_manager=task_manager,
        data_dir=data_dir,
        logger=logger
    )
    
    # Test available integrations
    test_available_integrations(integration_system)
    
    # Test creating integrations
    github_id = test_create_github_integration(integration_system)
    jira_id = test_create_jira_integration(integration_system)
    
    # Test getting integrations
    test_get_integrations(integration_system)
    
    # Test updating an integration
    if github_id:
        test_update_integration(integration_system, github_id)
    
    # Test activating an integration
    if github_id:
        test_activate_integration(integration_system, github_id)
    
    # Test testing an integration
    if github_id:
        test_test_integration(integration_system, github_id)
    
    # Test importing tasks
    if github_id:
        test_import_tasks(integration_system, github_id)
    
    # Test exporting tasks
    if github_id:
        test_export_tasks(integration_system, github_id, task_manager)
    
    # Test synchronizing an integration
    if github_id:
        test_sync_integration(integration_system, github_id)
    
    # Test webhook processing
    if github_id:
        test_webhook(integration_system, github_id)
    
    # Test the scheduler
    test_scheduler(integration_system)
    
    # Test deactivating an integration
    if github_id:
        test_deactivate_integration(integration_system, github_id)
    
    # Test deleting integrations
    if github_id:
        test_delete_integration(integration_system, github_id)
    
    if jira_id:
        test_delete_integration(integration_system, jira_id)
    
    print_section("Test Complete")
    print("The Task Integration System test has completed successfully.")


if __name__ == "__main__":
    main()