#!/usr/bin/env python3
"""
Test script for the Task Time Tracking System in Tascade AI.

This script demonstrates the new Time Tracking features:
1. Manual time entry
2. Automatic time tracking with start/stop/pause/resume
3. Time estimates
4. Productivity analysis
5. Time tracking reports
"""

import os
import sys
import json
from datetime import datetime, timedelta
import time

# Add the project root to the Python path to allow importing the package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.task_manager import TaskManager
from src.core.task_timetracking import TaskTimeTrackingSystem
from src.core.timetracking.models import TimeEntryStatus, TimeEntryType, TimeEstimateType
from src.core.timetracking.session_tracker import WorkSessionTracker
from src.core.timetracking.productivity_analyzer import ProductivityAnalyzer


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))


def format_duration(seconds):
    """Format duration in seconds to a readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def main():
    """Test the Task Time Tracking System in Tascade AI."""
    print_section("Task Time Tracking System Test")
    
    # Initialize the task manager
    task_manager = TaskManager()
    
    # Initialize the time tracking system
    time_tracking = TaskTimeTrackingSystem(task_manager=task_manager)
    
    # Create test tasks
    print("Creating test tasks...")
    
    task1_id = task_manager.create_task({
        "title": "Implement user authentication",
        "description": "Add user authentication using JWT tokens",
        "priority": "high",
        "status": "pending"
    })
    
    task2_id = task_manager.create_task({
        "title": "Design database schema",
        "description": "Create the database schema for the application",
        "priority": "medium",
        "status": "pending"
    })
    
    task3_id = task_manager.create_task({
        "title": "Write API documentation",
        "description": "Document the REST API endpoints",
        "priority": "low",
        "status": "pending"
    })
    
    print(f"Created tasks: {task1_id}, {task2_id}, {task3_id}")
    
    # Test 1: Manual Time Entry
    print_section("Test 1: Manual Time Entry")
    
    # Add manual time entries
    entry1_id = time_tracking.add_manual_entry(
        task_id=task1_id,
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1),
        description="Initial authentication setup",
        tags=["coding", "backend"]
    )
    
    entry2_id = time_tracking.add_manual_entry(
        task_id=task2_id,
        duration_seconds=45 * 60,  # 45 minutes
        description="Database schema design",
        tags=["design", "database"]
    )
    
    print(f"Added manual time entries: {entry1_id}, {entry2_id}")
    
    # List time entries
    entries = time_tracking.get_time_entries({})
    print(f"\nTime entries ({len(entries)}):")
    
    for entry in entries:
        start_time = entry.start_time.strftime("%Y-%m-%d %H:%M") if entry.start_time else "N/A"
        duration = format_duration(entry.duration_seconds or 0)
        
        print(f"- {entry.id}: {entry.task_id} - {start_time} - {duration} - {entry.description}")
    
    # Test 2: Time Tracking Session
    print_section("Test 2: Time Tracking Session")
    
    # Start tracking
    print("Starting time tracking for task...")
    session_id = time_tracking.start_tracking(
        task_id=task3_id,
        description="Writing API documentation",
        tags=["documentation", "api"]
    )
    
    print(f"Started tracking session: {session_id}")
    
    # Get current status
    status = time_tracking.get_tracking_status()
    print("\nCurrent tracking status:")
    print_json(status)
    
    # Simulate work (sleep for a few seconds)
    print("\nWorking on task...")
    time.sleep(3)
    
    # Pause tracking
    print("\nPausing tracking...")
    pause_result = time_tracking.pause_tracking(session_id=session_id)
    print(f"Paused: {pause_result}")
    
    # Get updated status
    status = time_tracking.get_tracking_status()
    print("\nUpdated tracking status (paused):")
    print_json(status)
    
    # Simulate break (sleep for a few seconds)
    print("\nTaking a break...")
    time.sleep(2)
    
    # Resume tracking
    print("\nResuming tracking...")
    resume_result = time_tracking.resume_tracking(session_id=session_id)
    print(f"Resumed: {resume_result}")
    
    # Simulate more work (sleep for a few seconds)
    print("\nContinuing work...")
    time.sleep(3)
    
    # Stop tracking
    print("\nStopping tracking...")
    stop_result = time_tracking.stop_tracking(session_id=session_id)
    print(f"Stopped tracking. Duration: {format_duration(stop_result.get('duration_seconds', 0))}")
    
    # List updated time entries
    entries = time_tracking.get_time_entries({})
    print(f"\nUpdated time entries ({len(entries)}):")
    
    for entry in entries:
        start_time = entry.start_time.strftime("%Y-%m-%d %H:%M") if entry.start_time else "N/A"
        duration = format_duration(entry.duration_seconds or 0)
        
        print(f"- {entry.id}: {entry.task_id} - {start_time} - {duration} - {entry.description}")
    
    # Test 3: Time Estimates
    print_section("Test 3: Time Estimates")
    
    # Add time estimates
    estimate1_id = time_tracking.add_estimate(
        task_id=task1_id,
        estimate_type="fixed",
        estimate_value=4,
        unit="hours",
        confidence=80,
        notes="Based on similar authentication implementations"
    )
    
    estimate2_id = time_tracking.add_estimate(
        task_id=task2_id,
        estimate_type="range",
        estimate_value={"min": 2, "max": 4},
        unit="hours",
        confidence=70,
        notes="Depends on complexity of relationships"
    )
    
    estimate3_id = time_tracking.add_estimate(
        task_id=task3_id,
        estimate_type="fixed",
        estimate_value=2,
        unit="hours",
        confidence=90,
        notes="Standard API documentation"
    )
    
    print(f"Added time estimates: {estimate1_id}, {estimate2_id}, {estimate3_id}")
    
    # Get estimates
    estimates = time_tracking.get_estimates({})
    print(f"\nTime estimates ({len(estimates)}):")
    
    for estimate in estimates:
        if estimate.estimate_type == TimeEstimateType.RANGE:
            value = f"{estimate.estimate_value['min']}-{estimate.estimate_value['max']} {estimate.unit}"
        else:
            value = f"{estimate.estimate_value} {estimate.unit}"
        
        print(f"- {estimate.id}: {estimate.task_id} - {value} - Confidence: {estimate.confidence}%")
    
    # Test 4: Productivity Analysis
    print_section("Test 4: Productivity Analysis")
    
    # Add more time entries for better analysis
    time_tracking.add_manual_entry(
        task_id=task1_id,
        duration_seconds=90 * 60,  # 90 minutes
        description="JWT implementation",
        tags=["coding", "backend"]
    )
    
    time_tracking.add_manual_entry(
        task_id=task2_id,
        duration_seconds=120 * 60,  # 2 hours
        description="Database schema refinement",
        tags=["design", "database"]
    )
    
    # Analyze productivity
    metrics, insights = time_tracking.analyze_productivity()
    
    print("Productivity Metrics:")
    print(f"- Total tracked time: {format_duration(metrics.total_tracked_time.total_seconds())}")
    print(f"- Focus time: {format_duration(metrics.focus_time.total_seconds())} ({metrics.focus_percentage:.1f}%)")
    print(f"- Task switching count: {metrics.task_switching_count}")
    print(f"- Average session duration: {format_duration(metrics.avg_session_duration.total_seconds())}")
    print(f"- Productivity score: {metrics.productivity_score}/100")
    
    if insights:
        print("\nProductivity Insights:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight.description}")
            if insight.recommendation:
                print(f"   Recommendation: {insight.recommendation}")
    
    # Test 5: Time Reports
    print_section("Test 5: Time Reports")
    
    # Generate summary report
    summary_report = time_tracking.generate_report(
        report_type="summary",
        filters={},
        output_format="text"
    )
    
    print("Summary Report:")
    print(summary_report)
    
    # Generate task report
    task_report = time_tracking.generate_report(
        report_type="task",
        filters={"task_id": task1_id},
        output_format="text"
    )
    
    print("\nTask Report:")
    print(task_report)
    
    print_section("Test Complete")
    print("The Task Time Tracking System is working correctly.")


if __name__ == "__main__":
    main()
