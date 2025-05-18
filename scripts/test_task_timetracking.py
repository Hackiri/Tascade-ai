#!/usr/bin/env python3
"""
Test script for the Task Time Tracking System.

This script demonstrates the functionality of the Task Time Tracking System,
including creating time entries, managing time estimates, and generating reports.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.task_timetracking import TaskTimeTrackingSystem
from src.core.timetracking.models import TimeEntryStatus, TimeEstimateType
from src.core.timetracking.reporting import ReportType, ReportFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_timetracking")

def print_section(title: str):
    """Print a section title with formatting."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(title: str, result: Dict[str, Any]):
    """Print a result with formatting."""
    print(f"\n--- {title} ---")
    print(json.dumps(result, indent=2, default=str))

def test_time_entries(time_tracking: TaskTimeTrackingSystem):
    """Test time entry functionality."""
    print_section("Testing Time Entries")
    
    # Create a time entry
    entry_result = time_tracking.create_time_entry(
        task_id="task-123",
        description="Working on documentation",
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1),
        user_id="user-456",
        billable=True,
        tags=["documentation", "writing"]
    )
    print_result("Create Time Entry", entry_result)
    
    if not entry_result["success"]:
        logger.error("Failed to create time entry")
        return
    
    entry_id = entry_result["entry_id"]
    
    # Get time entry
    get_result = time_tracking.get_time_entry(entry_id)
    print_result("Get Time Entry", get_result)
    
    # Update time entry
    update_result = time_tracking.update_time_entry(
        entry_id=entry_id,
        description="Updated: Working on API documentation",
        tags=["documentation", "api", "writing"]
    )
    print_result("Update Time Entry", update_result)
    
    # Create an active time entry
    active_result = time_tracking.start_timer(
        task_id="task-456",
        description="Active development work",
        user_id="user-456",
        tags=["development", "coding"]
    )
    print_result("Start Timer", active_result)
    
    if active_result["success"]:
        active_id = active_result["entry_id"]
        
        # Pause the timer
        pause_result = time_tracking.pause_timer(active_id)
        print_result("Pause Timer", pause_result)
        
        # Resume the timer
        resume_result = time_tracking.resume_timer(active_id)
        print_result("Resume Timer", resume_result)
        
        # Stop the timer with the entry ID
        stop_result = time_tracking.stop_timer(entry_id=active_id)
        print_result("Stop Timer", stop_result)
    
    # Get entries for a task
    task_entries = time_tracking.get_time_entries_for_task("task-123")
    print_result("Get Entries for Task", task_entries)
    
    # Get entries for a user
    user_entries = time_tracking.get_time_entries_for_user("user-456")
    print_result("Get Entries for User", user_entries)

def test_time_estimates(time_tracking: TaskTimeTrackingSystem):
    """Test time estimate functionality."""
    print_section("Testing Time Estimates")
    
    # Create a fixed time estimate
    fixed_estimate = time_tracking.create_time_estimate(
        task_id="task-123",
        estimate_type="fixed",
        estimate_value=8,
        unit="hours",
        created_by="user-456",
        confidence=80,
        notes="Initial estimate for documentation task"
    )
    print_result("Create Fixed Time Estimate", fixed_estimate)
    
    if not fixed_estimate["success"]:
        logger.error("Failed to create fixed time estimate")
        return
    
    fixed_id = fixed_estimate["estimate_id"]
    
    # Get time estimate
    get_result = time_tracking.get_time_estimate(fixed_id)
    print_result("Get Time Estimate", get_result)
    
    # Update time estimate
    update_result = time_tracking.update_time_estimate(
        estimate_id=fixed_id,
        estimate_value=10,
        confidence=70,
        notes="Updated estimate after reviewing requirements"
    )
    print_result("Update Time Estimate", update_result)
    
    # Create a range time estimate
    range_estimate = time_tracking.create_time_estimate(
        task_id="task-456",
        estimate_type="range",
        estimate_value={"min": 16, "max": 24},
        unit="hours",
        created_by="user-789",
        confidence=60,
        notes="Development work estimate with uncertainty"
    )
    print_result("Create Range Time Estimate", range_estimate)
    
    # Get estimate for task
    task_estimate = time_tracking.get_time_estimate_for_task("task-123")
    print_result("Get Estimate for Task", task_estimate)
    
    # Compare estimate to actual
    comparison = time_tracking.compare_estimate_to_actual("task-123")
    print_result("Compare Estimate to Actual", comparison)

def test_reporting(time_tracking: TaskTimeTrackingSystem):
    """Test reporting functionality."""
    print_section("Testing Reporting")
    
    # Generate a summary report
    summary_report = time_tracking.generate_report(
        report_type="summary",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        title="Weekly Summary Report"
    )
    print_result("Summary Report", summary_report)
    
    # Generate a daily report
    daily_report = time_tracking.generate_report(
        report_type="daily",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        title="Daily Time Report"
    )
    print_result("Daily Report", daily_report)
    
    # Generate a task report
    task_report = time_tracking.generate_report(
        report_type="task",
        task_ids=["task-123", "task-456"],
        title="Task Time Report"
    )
    print_result("Task Report", task_report)
    
    # Generate an estimate comparison report
    estimate_report = time_tracking.generate_report(
        report_type="estimate_comparison",
        task_ids=["task-123", "task-456"],
        title="Estimate vs. Actual Report"
    )
    print_result("Estimate Comparison Report", estimate_report)

def test_analytics(time_tracking: TaskTimeTrackingSystem):
    """Test analytics functionality."""
    print_section("Testing Analytics")
    
    # Get time by day
    time_by_day = time_tracking.get_time_by_day(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    print_result("Time by Day", time_by_day)
    
    # Get time by task
    time_by_task = time_tracking.get_time_by_task(
        user_id="user-456",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    print_result("Time by Task", time_by_task)
    
    # Get time by tag
    time_by_tag = time_tracking.get_time_by_tag(
        user_id="user-456",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    print_result("Time by Tag", time_by_tag)

def test_settings(time_tracking: TaskTimeTrackingSystem):
    """Test settings functionality."""
    print_section("Testing Settings")
    
    # Get current settings
    current_settings = time_tracking.get_settings()
    print_result("Current Settings", current_settings)
    
    # Update settings
    updated_settings = time_tracking.update_settings(
        default_estimate_type="range",
        round_to_nearest=15,
        track_idle_time=True,
        auto_pause_after_minutes=30,
        billable_by_default=True
    )
    print_result("Updated Settings", updated_settings)

def main():
    """Main function to run the tests."""
    print_section("Task Time Tracking System Test")
    
    # Create the time tracking system
    time_tracking = TaskTimeTrackingSystem()
    
    # Run tests
    test_time_entries(time_tracking)
    test_time_estimates(time_tracking)
    test_reporting(time_tracking)
    test_analytics(time_tracking)
    test_settings(time_tracking)
    
    print("\nTests completed.")

if __name__ == "__main__":
    main()
