#!/usr/bin/env python3
"""
Mobile CLI for Tascade AI.

This module provides a command-line interface for mobile devices to interact with
Tascade AI's time tracking system.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from .client import TascadeMobileClient


def setup_logging() -> logging.Logger:
    """Set up logging."""
    logger = logging.getLogger("tascade.mobile.cli")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def parse_datetime(date_str: str) -> datetime:
    """Parse a datetime string."""
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        # Try different formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse datetime: {date_str}")


def format_duration(seconds: int) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    return f"{hours}h {minutes}m {seconds}s"


def print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Print a table."""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print headers
    header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))


def handle_login(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle login command."""
    try:
        result = client.login(args.user_id)
        
        print(f"Logged in as {result['user_id']}")
        print(f"Token: {result['token']}")
        
        # Save token to config file
        config_dir = os.path.expanduser("~/.tascade")
        os.makedirs(config_dir, exist_ok=True)
        
        with open(os.path.join(config_dir, "mobile_config.json"), "w") as f:
            json.dump({
                "api_url": args.api_url,
                "user_id": result["user_id"],
                "token": result["token"]
            }, f)
        
        print(f"Configuration saved to {os.path.join(config_dir, 'mobile_config.json')}")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        sys.exit(1)


def handle_entries(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle entries command."""
    if args.entries_action == "list":
        # Parse filters
        filters = {}
        
        if args.task_id:
            filters["task_id"] = args.task_id
        
        if args.from_date:
            try:
                filters["from_date"] = parse_datetime(args.from_date)
            except ValueError as e:
                logger.error(f"Invalid from_date: {e}")
                sys.exit(1)
        
        if args.to_date:
            try:
                filters["to_date"] = parse_datetime(args.to_date)
            except ValueError as e:
                logger.error(f"Invalid to_date: {e}")
                sys.exit(1)
        
        if args.tags:
            filters["tags"] = args.tags.split(",")
        
        # Get entries
        try:
            entries = client.get_time_entries(**filters)
            
            if not entries:
                print("No time entries found.")
                return
            
            # Print entries
            headers = ["ID", "Task", "Description", "Start", "End", "Duration"]
            rows = []
            
            for entry in entries:
                start_time = entry.get("start_time", "")
                if start_time:
                    start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M")
                
                end_time = entry.get("end_time", "")
                if end_time:
                    end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M")
                
                duration = entry.get("duration_seconds", 0)
                if duration:
                    duration = format_duration(duration)
                
                rows.append([
                    entry.get("id", ""),
                    entry.get("task_id", ""),
                    entry.get("description", "")[:30],
                    start_time,
                    end_time,
                    duration
                ])
            
            print_table(headers, rows)
        except Exception as e:
            logger.error(f"Failed to get time entries: {e}")
            sys.exit(1)
    
    elif args.entries_action == "add":
        # Parse entry data
        entry_data = {
            "task_id": args.task_id
        }
        
        if args.description:
            entry_data["description"] = args.description
        
        if args.start_time:
            try:
                entry_data["start_time"] = parse_datetime(args.start_time)
            except ValueError as e:
                logger.error(f"Invalid start_time: {e}")
                sys.exit(1)
        
        if args.end_time:
            try:
                entry_data["end_time"] = parse_datetime(args.end_time)
            except ValueError as e:
                logger.error(f"Invalid end_time: {e}")
                sys.exit(1)
        
        if args.duration:
            # Parse duration string (e.g., "1h 30m")
            duration_seconds = 0
            
            parts = args.duration.split()
            for part in parts:
                if part.endswith("h"):
                    try:
                        hours = float(part[:-1])
                        duration_seconds += int(hours * 3600)
                    except ValueError:
                        logger.error(f"Invalid duration format: {args.duration}")
                        sys.exit(1)
                elif part.endswith("m"):
                    try:
                        minutes = float(part[:-1])
                        duration_seconds += int(minutes * 60)
                    except ValueError:
                        logger.error(f"Invalid duration format: {args.duration}")
                        sys.exit(1)
                elif part.endswith("s"):
                    try:
                        seconds = float(part[:-1])
                        duration_seconds += int(seconds)
                    except ValueError:
                        logger.error(f"Invalid duration format: {args.duration}")
                        sys.exit(1)
                else:
                    logger.error(f"Invalid duration format: {args.duration}")
                    sys.exit(1)
            
            entry_data["duration_seconds"] = duration_seconds
        
        if args.tags:
            entry_data["tags"] = args.tags.split(",")
        
        # Create entry
        try:
            result = client.create_time_entry(**entry_data)
            
            if result.get("offline"):
                print(f"Time entry created offline with ID: {result['entry_id']}")
                print("It will be synchronized when online.")
            else:
                print(f"Time entry created with ID: {result['entry_id']}")
        except Exception as e:
            logger.error(f"Failed to create time entry: {e}")
            sys.exit(1)
    
    elif args.entries_action == "delete":
        try:
            result = client.delete_time_entry(args.entry_id)
            
            print(f"Time entry deleted: {args.entry_id}")
        except Exception as e:
            logger.error(f"Failed to delete time entry: {e}")
            sys.exit(1)


def handle_sessions(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle sessions command."""
    if args.sessions_action == "start":
        # Parse session data
        session_data = {
            "task_id": args.task_id
        }
        
        if args.description:
            session_data["description"] = args.description
        
        if args.tags:
            session_data["tags"] = args.tags.split(",")
        
        # Start session
        try:
            result = client.start_session(**session_data)
            
            print(f"Session started with ID: {result['session_id']}")
            print(f"Task: {result['session']['task_id']}")
            print(f"Started at: {datetime.fromisoformat(result['session']['start_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            sys.exit(1)
    
    elif args.sessions_action == "pause":
        try:
            result = client.pause_session(args.session_id)
            
            print(f"Session paused: {args.session_id}")
            print(f"Paused at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Failed to pause session: {e}")
            sys.exit(1)
    
    elif args.sessions_action == "resume":
        try:
            result = client.resume_session(args.session_id)
            
            print(f"Session resumed: {args.session_id}")
            print(f"Resumed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Failed to resume session: {e}")
            sys.exit(1)
    
    elif args.sessions_action == "stop":
        try:
            result = client.stop_session(args.session_id)
            
            print(f"Session stopped: {args.session_id}")
            print(f"Duration: {format_duration(result['duration_seconds'])}")
            print(f"Time entry created with ID: {result['entry_id']}")
        except Exception as e:
            logger.error(f"Failed to stop session: {e}")
            sys.exit(1)
    
    elif args.sessions_action == "status":
        try:
            status = client.get_session_status()
            
            if status.get("active_session"):
                session = status["active_session"]
                
                print(f"Active session: {session['id']}")
                print(f"Task: {session['task_id']}")
                print(f"Started at: {datetime.fromisoformat(session['start_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                if session.get("paused"):
                    print(f"Status: Paused")
                    print(f"Paused at: {datetime.fromisoformat(session['paused_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"Status: Running")
                
                elapsed = session.get("elapsed_seconds", 0)
                print(f"Elapsed time: {format_duration(elapsed)}")
            else:
                print("No active session.")
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            sys.exit(1)


def handle_estimates(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle estimates command."""
    if args.estimates_action == "list":
        # Parse filters
        filters = {}
        
        if args.task_id:
            filters["task_id"] = args.task_id
        
        # Get estimates
        try:
            estimates = client.get_estimates(**filters)
            
            if not estimates:
                print("No time estimates found.")
                return
            
            # Print estimates
            headers = ["ID", "Task", "Type", "Value", "Unit", "Confidence", "Notes"]
            rows = []
            
            for estimate in estimates:
                rows.append([
                    estimate.get("id", ""),
                    estimate.get("task_id", ""),
                    estimate.get("estimate_type", ""),
                    estimate.get("estimate_value", ""),
                    estimate.get("unit", ""),
                    estimate.get("confidence", ""),
                    estimate.get("notes", "")[:30]
                ])
            
            print_table(headers, rows)
        except Exception as e:
            logger.error(f"Failed to get time estimates: {e}")
            sys.exit(1)
    
    elif args.estimates_action == "add":
        # Parse estimate data
        estimate_data = {
            "task_id": args.task_id,
            "estimate_type": args.estimate_type,
            "estimate_value": args.estimate_value,
            "unit": args.unit
        }
        
        if args.confidence:
            try:
                estimate_data["confidence"] = int(args.confidence)
            except ValueError:
                logger.error(f"Invalid confidence value: {args.confidence}")
                sys.exit(1)
        
        if args.notes:
            estimate_data["notes"] = args.notes
        
        # Create estimate
        try:
            result = client.create_estimate(**estimate_data)
            
            print(f"Time estimate created with ID: {result['estimate_id']}")
        except Exception as e:
            logger.error(f"Failed to create time estimate: {e}")
            sys.exit(1)


def handle_productivity(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle productivity command."""
    # Parse filters
    filters = {}
    
    if args.start_date:
        try:
            filters["start_date"] = parse_datetime(args.start_date)
        except ValueError as e:
            logger.error(f"Invalid start_date: {e}")
            sys.exit(1)
    
    if args.end_date:
        try:
            filters["end_date"] = parse_datetime(args.end_date)
        except ValueError as e:
            logger.error(f"Invalid end_date: {e}")
            sys.exit(1)
    
    if args.task_ids:
        filters["task_ids"] = args.task_ids.split(",")
    
    # Get productivity data
    try:
        result = client.get_productivity(**filters)
        
        # Print metrics
        print("Productivity Metrics:")
        print(f"Total time tracked: {format_duration(result['metrics']['total_time_tracked'])}")
        print(f"Average daily time: {format_duration(result['metrics']['average_daily_time'])}")
        print(f"Most productive day: {result['metrics']['most_productive_day']}")
        print(f"Most productive hour: {result['metrics']['most_productive_hour']}")
        
        # Print insights
        print("\nProductivity Insights:")
        for insight in result["insights"]:
            print(f"- {insight['message']}")
    except Exception as e:
        logger.error(f"Failed to get productivity data: {e}")
        sys.exit(1)


def handle_reports(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle reports command."""
    # Parse filters
    filters = {
        "report_type": args.report_type,
        "output_format": args.format
    }
    
    if args.task_id:
        filters["task_id"] = args.task_id
    
    if args.from_date:
        try:
            filters["from_date"] = parse_datetime(args.from_date)
        except ValueError as e:
            logger.error(f"Invalid from_date: {e}")
            sys.exit(1)
    
    if args.to_date:
        try:
            filters["to_date"] = parse_datetime(args.to_date)
        except ValueError as e:
            logger.error(f"Invalid to_date: {e}")
            sys.exit(1)
    
    # Generate report
    try:
        result = client.generate_report(**filters)
        
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(result)
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)


def handle_sync(args: argparse.Namespace, client: TascadeMobileClient, logger: logging.Logger) -> None:
    """Handle sync command."""
    try:
        result = client.sync()
        
        print(f"Synchronized {len(result['time_entries'])} time entries")
        print(f"Synchronized {len(result['time_estimates'])} time estimates")
        print(f"Sync time: {result['sync_time']}")
    except Exception as e:
        logger.error(f"Failed to sync data: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    # Set up logging
    logger = setup_logging()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Tascade AI Mobile CLI")
    
    # Global arguments
    parser.add_argument("--api-url", default="http://localhost:5000", help="API URL")
    parser.add_argument("--offline", action="store_true", help="Enable offline mode")
    
    # Load config if available
    config_file = os.path.expanduser("~/.tascade/mobile_config.json")
    config = {}
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    # Subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to the API")
    login_parser.add_argument("user_id", help="User ID")
    
    # Entries command
    entries_parser = subparsers.add_parser("entries", help="Manage time entries")
    entries_subparsers = entries_parser.add_subparsers(dest="entries_action", help="Action")
    
    # List entries
    list_entries_parser = entries_subparsers.add_parser("list", help="List time entries")
    list_entries_parser.add_argument("--task-id", help="Filter by task ID")
    list_entries_parser.add_argument("--from-date", help="Filter by start date")
    list_entries_parser.add_argument("--to-date", help="Filter by end date")
    list_entries_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    
    # Add entry
    add_entry_parser = entries_subparsers.add_parser("add", help="Add a time entry")
    add_entry_parser.add_argument("task_id", help="Task ID")
    add_entry_parser.add_argument("--description", help="Entry description")
    add_entry_parser.add_argument("--start-time", help="Start time")
    add_entry_parser.add_argument("--end-time", help="End time")
    add_entry_parser.add_argument("--duration", help="Duration (e.g., '1h 30m')")
    add_entry_parser.add_argument("--tags", help="Tags (comma-separated)")
    
    # Delete entry
    delete_entry_parser = entries_subparsers.add_parser("delete", help="Delete a time entry")
    delete_entry_parser.add_argument("entry_id", help="Entry ID")
    
    # Sessions command
    sessions_parser = subparsers.add_parser("sessions", help="Manage work sessions")
    sessions_subparsers = sessions_parser.add_subparsers(dest="sessions_action", help="Action")
    
    # Start session
    start_session_parser = sessions_subparsers.add_parser("start", help="Start a work session")
    start_session_parser.add_argument("task_id", help="Task ID")
    start_session_parser.add_argument("--description", help="Session description")
    start_session_parser.add_argument("--tags", help="Tags (comma-separated)")
    
    # Pause session
    pause_session_parser = sessions_subparsers.add_parser("pause", help="Pause a work session")
    pause_session_parser.add_argument("session_id", help="Session ID")
    
    # Resume session
    resume_session_parser = sessions_subparsers.add_parser("resume", help="Resume a work session")
    resume_session_parser.add_argument("session_id", help="Session ID")
    
    # Stop session
    stop_session_parser = sessions_subparsers.add_parser("stop", help="Stop a work session")
    stop_session_parser.add_argument("session_id", help="Session ID")
    
    # Status
    status_parser = sessions_subparsers.add_parser("status", help="Get current tracking status")
    
    # Estimates command
    estimates_parser = subparsers.add_parser("estimates", help="Manage time estimates")
    estimates_subparsers = estimates_parser.add_subparsers(dest="estimates_action", help="Action")
    
    # List estimates
    list_estimates_parser = estimates_subparsers.add_parser("list", help="List time estimates")
    list_estimates_parser.add_argument("--task-id", help="Filter by task ID")
    
    # Add estimate
    add_estimate_parser = estimates_subparsers.add_parser("add", help="Add a time estimate")
    add_estimate_parser.add_argument("task_id", help="Task ID")
    add_estimate_parser.add_argument("estimate_type", choices=["fixed", "range", "distribution"], help="Estimate type")
    add_estimate_parser.add_argument("estimate_value", help="Estimate value")
    add_estimate_parser.add_argument("--unit", default="hours", help="Unit of measurement")
    add_estimate_parser.add_argument("--confidence", help="Confidence level (0-100)")
    add_estimate_parser.add_argument("--notes", help="Notes")
    
    # Productivity command
    productivity_parser = subparsers.add_parser("productivity", help="Get productivity metrics")
    productivity_parser.add_argument("--start-date", help="Start date")
    productivity_parser.add_argument("--end-date", help="End date")
    productivity_parser.add_argument("--task-ids", help="Task IDs (comma-separated)")
    
    # Reports command
    reports_parser = subparsers.add_parser("reports", help="Generate reports")
    reports_parser.add_argument("report_type", choices=["summary", "detailed", "comparison"], help="Report type")
    reports_parser.add_argument("--task-id", help="Filter by task ID")
    reports_parser.add_argument("--from-date", help="Filter by start date")
    reports_parser.add_argument("--to-date", help="Filter by end date")
    reports_parser.add_argument("--format", default="json", choices=["json", "text", "csv"], help="Output format")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize data")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set default API URL from config
    if not args.api_url and "api_url" in config:
        args.api_url = config["api_url"]
    
    # Create client
    client = TascadeMobileClient(
        api_url=args.api_url,
        user_id=config.get("user_id"),
        token=config.get("token"),
        offline_mode=args.offline
    )
    
    # Handle commands
    if args.command == "login":
        handle_login(args, client, logger)
    elif args.command == "entries":
        if not args.entries_action:
            entries_parser.print_help()
            sys.exit(1)
        handle_entries(args, client, logger)
    elif args.command == "sessions":
        if not args.sessions_action:
            sessions_parser.print_help()
            sys.exit(1)
        handle_sessions(args, client, logger)
    elif args.command == "estimates":
        if not args.estimates_action:
            estimates_parser.print_help()
            sys.exit(1)
        handle_estimates(args, client, logger)
    elif args.command == "productivity":
        handle_productivity(args, client, logger)
    elif args.command == "reports":
        handle_reports(args, client, logger)
    elif args.command == "sync":
        handle_sync(args, client, logger)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
