"""
CLI commands for the Task Time Tracking system.

This module implements the CLI commands for interacting with the Task Time Tracking
system in Tascade AI.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date

import click
from tabulate import tabulate

from ..core.task_timetracking import TaskTimeTrackingSystem


def setup_timetracking_parser(subparsers):
    """
    Set up the command-line parser for time tracking commands.
    
    Args:
        subparsers: Subparsers object from argparse
    """
    # Time tracking command
    time_parser = subparsers.add_parser("time", help="Time tracking commands")
    time_subparsers = time_parser.add_subparsers(dest="time_command", help="Time tracking commands")
    
    # Start command
    start_parser = time_subparsers.add_parser("start", help="Start time tracking for a task")
    start_parser.add_argument("task_id", help="Task ID to track time for")
    start_parser.add_argument("--description", "-d", help="Description of the time entry")
    start_parser.add_argument("--tags", "-t", help="Comma-separated list of tags")
    start_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # Stop command
    stop_parser = time_subparsers.add_parser("stop", help="Stop time tracking for a task")
    stop_parser.add_argument("--session", "-s", help="Session ID to stop (default: most recent)")
    stop_parser.add_argument("--task", "-t", help="Task ID to stop tracking for")
    stop_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # Pause command
    pause_parser = time_subparsers.add_parser("pause", help="Pause time tracking for a task")
    pause_parser.add_argument("--session", "-s", help="Session ID to pause (default: most recent)")
    pause_parser.add_argument("--task", "-t", help="Task ID to pause tracking for")
    pause_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # Resume command
    resume_parser = time_subparsers.add_parser("resume", help="Resume time tracking for a task")
    resume_parser.add_argument("--session", "-s", help="Session ID to resume (default: most recent)")
    resume_parser.add_argument("--task", "-t", help="Task ID to resume tracking for")
    resume_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # Add command (manual time entry)
    add_parser = time_subparsers.add_parser("add", help="Add a manual time entry")
    add_parser.add_argument("task_id", help="Task ID to add time for")
    add_parser.add_argument("duration", help="Duration in format HH:MM or minutes")
    add_parser.add_argument("--description", "-d", help="Description of the time entry")
    add_parser.add_argument("--date", help="Date of the time entry (YYYY-MM-DD, default: today)")
    add_parser.add_argument("--start", help="Start time (HH:MM, default: now)")
    add_parser.add_argument("--tags", "-t", help="Comma-separated list of tags")
    add_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # List command
    list_parser = time_subparsers.add_parser("list", help="List time entries")
    list_parser.add_argument("--task", "-t", help="Filter by task ID")
    list_parser.add_argument("--user", "-u", help="Filter by user ID")
    list_parser.add_argument("--date", "-d", help="Filter by date (YYYY-MM-DD)")
    list_parser.add_argument("--from", dest="from_date", help="Filter from date (YYYY-MM-DD)")
    list_parser.add_argument("--to", dest="to_date", help="Filter to date (YYYY-MM-DD)")
    list_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    list_parser.add_argument("--limit", type=int, default=20, help="Limit number of entries")
    
    # Status command
    status_parser = time_subparsers.add_parser("status", help="Show current time tracking status")
    status_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    
    # Report command
    report_parser = time_subparsers.add_parser("report", help="Generate time tracking reports")
    report_parser.add_argument("report_type", choices=["summary", "daily", "task", "estimate"], 
                              help="Type of report to generate")
    report_parser.add_argument("--task", "-t", help="Filter by task ID")
    report_parser.add_argument("--user", "-u", help="Filter by user ID")
    report_parser.add_argument("--from", dest="from_date", help="From date (YYYY-MM-DD)")
    report_parser.add_argument("--to", dest="to_date", help="To date (YYYY-MM-DD)")
    report_parser.add_argument("--format", "-f", choices=["text", "json", "csv"], default="text",
                              help="Output format")
    report_parser.add_argument("--output", "-o", help="Output file path")
    
    # Estimate command
    estimate_parser = time_subparsers.add_parser("estimate", help="Manage time estimates")
    estimate_subparsers = estimate_parser.add_subparsers(dest="estimate_command", help="Estimate commands")
    
    # Add estimate command
    add_estimate_parser = estimate_subparsers.add_parser("add", help="Add a time estimate")
    add_estimate_parser.add_argument("task_id", help="Task ID to estimate")
    add_estimate_parser.add_argument("value", help="Estimate value (number or range)")
    add_estimate_parser.add_argument("--type", "-t", choices=["fixed", "range", "points", "t_shirt"],
                                    default="fixed", help="Estimate type")
    add_estimate_parser.add_argument("--unit", "-u", choices=["minutes", "hours", "days"],
                                    default="hours", help="Time unit")
    add_estimate_parser.add_argument("--confidence", "-c", type=int, help="Confidence level (0-100)")
    add_estimate_parser.add_argument("--notes", "-n", help="Additional notes")
    
    # List estimates command
    list_estimate_parser = estimate_subparsers.add_parser("list", help="List time estimates")
    list_estimate_parser.add_argument("--task", "-t", help="Filter by task ID")
    list_estimate_parser.add_argument("--user", "-u", help="Filter by user ID")
    
    # Productivity command
    productivity_parser = time_subparsers.add_parser("productivity", help="Analyze productivity")
    productivity_parser.add_argument("--user", "-u", help="User ID (default: current user)")
    productivity_parser.add_argument("--from", dest="from_date", help="From date (YYYY-MM-DD)")
    productivity_parser.add_argument("--to", dest="to_date", help="To date (YYYY-MM-DD)")
    productivity_parser.add_argument("--task", "-t", help="Filter by task ID")
    productivity_parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                                   help="Output format")


def handle_timetracking_command(args, task_manager=None, time_tracking=None):
    """
    Handle time tracking commands.
    
    Args:
        args: Parsed command-line arguments
        task_manager: Task manager instance
        time_tracking: Time tracking system instance
    """
    # Initialize time tracking system if not provided
    if not time_tracking:
        time_tracking = TaskTimeTrackingSystem(task_manager=task_manager)
    
    # Handle commands
    if args.time_command == "start":
        _handle_start_command(args, time_tracking)
    elif args.time_command == "stop":
        _handle_stop_command(args, time_tracking)
    elif args.time_command == "pause":
        _handle_pause_command(args, time_tracking)
    elif args.time_command == "resume":
        _handle_resume_command(args, time_tracking)
    elif args.time_command == "add":
        _handle_add_command(args, time_tracking)
    elif args.time_command == "list":
        _handle_list_command(args, time_tracking)
    elif args.time_command == "status":
        _handle_status_command(args, time_tracking)
    elif args.time_command == "report":
        _handle_report_command(args, time_tracking)
    elif args.time_command == "estimate":
        _handle_estimate_command(args, time_tracking)
    elif args.time_command == "productivity":
        _handle_productivity_command(args, time_tracking)
    else:
        click.echo("Unknown time tracking command. Use 'tascade-ai time --help' for usage information.")


def _handle_start_command(args, time_tracking):
    """
    Handle the start command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Parse tags
    tags = args.tags.split(",") if args.tags else []
    
    # Start time tracking
    try:
        session_id = time_tracking.start_tracking(
            task_id=args.task_id,
            user_id=args.user,
            description=args.description,
            tags=tags
        )
        
        click.echo(click.style(f"Started time tracking for task {args.task_id}", fg="green"))
        click.echo(f"Session ID: {session_id}")
    except Exception as e:
        click.echo(click.style(f"Error starting time tracking: {str(e)}", fg="red"))


def _handle_stop_command(args, time_tracking):
    """
    Handle the stop command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    try:
        if args.session:
            # Stop specific session
            result = time_tracking.stop_tracking(session_id=args.session)
        elif args.task:
            # Stop tracking for task
            result = time_tracking.stop_tracking_for_task(
                task_id=args.task,
                user_id=args.user
            )
        else:
            # Stop most recent session
            result = time_tracking.stop_tracking(user_id=args.user)
        
        if result:
            duration = timedelta(seconds=result.get("duration_seconds", 0))
            task_id = result.get("task_id", "unknown")
            
            click.echo(click.style(f"Stopped time tracking for task {task_id}", fg="green"))
            click.echo(f"Duration: {_format_duration(duration)}")
        else:
            click.echo("No active time tracking session found")
    except Exception as e:
        click.echo(click.style(f"Error stopping time tracking: {str(e)}", fg="red"))


def _handle_pause_command(args, time_tracking):
    """
    Handle the pause command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    try:
        if args.session:
            # Pause specific session
            result = time_tracking.pause_tracking(session_id=args.session)
        elif args.task:
            # Pause tracking for task
            result = time_tracking.pause_tracking_for_task(
                task_id=args.task,
                user_id=args.user
            )
        else:
            # Pause most recent session
            result = time_tracking.pause_tracking(user_id=args.user)
        
        if result:
            task_id = result.get("task_id", "unknown")
            click.echo(click.style(f"Paused time tracking for task {task_id}", fg="yellow"))
        else:
            click.echo("No active time tracking session found or session already paused")
    except Exception as e:
        click.echo(click.style(f"Error pausing time tracking: {str(e)}", fg="red"))


def _handle_resume_command(args, time_tracking):
    """
    Handle the resume command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    try:
        if args.session:
            # Resume specific session
            result = time_tracking.resume_tracking(session_id=args.session)
        elif args.task:
            # Resume tracking for task
            result = time_tracking.resume_tracking_for_task(
                task_id=args.task,
                user_id=args.user
            )
        else:
            # Resume most recent session
            result = time_tracking.resume_tracking(user_id=args.user)
        
        if result:
            task_id = result.get("task_id", "unknown")
            click.echo(click.style(f"Resumed time tracking for task {task_id}", fg="green"))
        else:
            click.echo("No paused time tracking session found")
    except Exception as e:
        click.echo(click.style(f"Error resuming time tracking: {str(e)}", fg="red"))


def _handle_add_command(args, time_tracking):
    """
    Handle the add command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Parse duration
    duration_seconds = _parse_duration(args.duration)
    if duration_seconds <= 0:
        click.echo(click.style("Invalid duration format. Use HH:MM or minutes.", fg="red"))
        return
    
    # Parse date and time
    entry_date = datetime.now().date()
    if args.date:
        try:
            entry_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(click.style("Invalid date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    start_time = datetime.now().time()
    if args.start:
        try:
            start_time = datetime.strptime(args.start, "%H:%M").time()
        except ValueError:
            click.echo(click.style("Invalid time format. Use HH:MM.", fg="red"))
            return
    
    # Combine date and time
    start_datetime = datetime.combine(entry_date, start_time)
    end_datetime = start_datetime + timedelta(seconds=duration_seconds)
    
    # Parse tags
    tags = args.tags.split(",") if args.tags else []
    
    # Add manual time entry
    try:
        entry_id = time_tracking.add_manual_entry(
            task_id=args.task_id,
            user_id=args.user,
            start_time=start_datetime,
            end_time=end_datetime,
            description=args.description,
            tags=tags
        )
        
        click.echo(click.style(f"Added manual time entry for task {args.task_id}", fg="green"))
        click.echo(f"Duration: {_format_duration(timedelta(seconds=duration_seconds))}")
        click.echo(f"Entry ID: {entry_id}")
    except Exception as e:
        click.echo(click.style(f"Error adding time entry: {str(e)}", fg="red"))


def _handle_list_command(args, time_tracking):
    """
    Handle the list command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Build filters
    filters = {}
    
    if args.task:
        filters["task_id"] = args.task
    
    if args.user:
        filters["user_id"] = args.user
    
    if args.date:
        try:
            entry_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            filters["date"] = entry_date
        except ValueError:
            click.echo(click.style("Invalid date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
            filters["from_date"] = from_date
        except ValueError:
            click.echo(click.style("Invalid from_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
            filters["to_date"] = to_date
        except ValueError:
            click.echo(click.style("Invalid to_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    if args.tags:
        filters["tags"] = args.tags.split(",")
    
    # Get time entries
    try:
        entries = time_tracking.get_time_entries(filters, limit=args.limit)
        
        if not entries:
            click.echo("No time entries found")
            return
        
        # Prepare table data
        table_data = []
        for entry in entries:
            start_time = entry.start_time.strftime("%Y-%m-%d %H:%M") if entry.start_time else "N/A"
            duration = _format_duration(timedelta(seconds=entry.duration_seconds or 0))
            
            table_data.append([
                entry.id,
                entry.task_id,
                start_time,
                duration,
                entry.description or "",
                ", ".join(entry.tags)
            ])
        
        # Print table
        click.echo(tabulate(
            table_data,
            headers=["ID", "Task", "Start Time", "Duration", "Description", "Tags"],
            tablefmt="grid"
        ))
    except Exception as e:
        click.echo(click.style(f"Error listing time entries: {str(e)}", fg="red"))


def _handle_status_command(args, time_tracking):
    """
    Handle the status command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    try:
        status = time_tracking.get_tracking_status(user_id=args.user)
        
        if not status or not status.get("active_sessions"):
            click.echo("No active time tracking sessions")
            return
        
        active_sessions = status.get("active_sessions", [])
        
        click.echo(click.style(f"Active time tracking sessions: {len(active_sessions)}", fg="green"))
        
        # Prepare table data
        table_data = []
        for session in active_sessions:
            task_id = session.get("task_id", "N/A")
            start_time = datetime.fromisoformat(session.get("start_time"))
            start_str = start_time.strftime("%Y-%m-%d %H:%M")
            
            duration = timedelta(seconds=session.get("active_duration_seconds", 0))
            duration_str = _format_duration(duration)
            
            status_str = "PAUSED" if session.get("is_paused") else "ACTIVE"
            status_color = "yellow" if session.get("is_paused") else "green"
            
            table_data.append([
                session.get("id"),
                task_id,
                start_str,
                duration_str,
                click.style(status_str, fg=status_color),
                session.get("description", "")
            ])
        
        # Print table
        click.echo(tabulate(
            table_data,
            headers=["Session ID", "Task", "Start Time", "Duration", "Status", "Description"],
            tablefmt="grid"
        ))
    except Exception as e:
        click.echo(click.style(f"Error getting tracking status: {str(e)}", fg="red"))


def _handle_report_command(args, time_tracking):
    """
    Handle the report command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Build filters
    filters = {}
    
    if args.task:
        filters["task_id"] = args.task
    
    if args.user:
        filters["user_id"] = args.user
    
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
            filters["from_date"] = from_date
        except ValueError:
            click.echo(click.style("Invalid from_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
            filters["to_date"] = to_date
        except ValueError:
            click.echo(click.style("Invalid to_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    # Generate report
    try:
        report = time_tracking.generate_report(
            report_type=args.report_type,
            filters=filters,
            output_format=args.format
        )
        
        if not report:
            click.echo("No data available for report")
            return
        
        # Output report
        if args.output:
            with open(args.output, "w") as f:
                if args.format == "json":
                    json.dump(report, f, indent=2)
                else:
                    f.write(report)
            click.echo(f"Report saved to {args.output}")
        else:
            if args.format == "json":
                click.echo(json.dumps(report, indent=2))
            else:
                click.echo(report)
    except Exception as e:
        click.echo(click.style(f"Error generating report: {str(e)}", fg="red"))


def _handle_estimate_command(args, time_tracking):
    """
    Handle the estimate command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    if args.estimate_command == "add":
        _handle_add_estimate_command(args, time_tracking)
    elif args.estimate_command == "list":
        _handle_list_estimate_command(args, time_tracking)
    else:
        click.echo("Unknown estimate command. Use 'tascade-ai time estimate --help' for usage information.")


def _handle_add_estimate_command(args, time_tracking):
    """
    Handle the add estimate command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Parse estimate value
    estimate_value = args.value
    
    if args.type == "range":
        # Parse range format (min-max)
        try:
            min_val, max_val = args.value.split("-")
            estimate_value = {
                "min": float(min_val.strip()),
                "max": float(max_val.strip())
            }
        except (ValueError, AttributeError):
            click.echo(click.style("Invalid range format. Use 'min-max' (e.g., '2-4').", fg="red"))
            return
    elif args.type in ["fixed", "points"]:
        # Parse numeric value
        try:
            estimate_value = float(args.value)
        except ValueError:
            click.echo(click.style("Invalid numeric value.", fg="red"))
            return
    
    # Add estimate
    try:
        estimate_id = time_tracking.add_estimate(
            task_id=args.task_id,
            estimate_type=args.type,
            estimate_value=estimate_value,
            unit=args.unit,
            confidence=args.confidence,
            notes=args.notes
        )
        
        click.echo(click.style(f"Added time estimate for task {args.task_id}", fg="green"))
        click.echo(f"Estimate ID: {estimate_id}")
    except Exception as e:
        click.echo(click.style(f"Error adding time estimate: {str(e)}", fg="red"))


def _handle_list_estimate_command(args, time_tracking):
    """
    Handle the list estimate command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Build filters
    filters = {}
    
    if args.task:
        filters["task_id"] = args.task
    
    if args.user:
        filters["user_id"] = args.user
    
    # Get estimates
    try:
        estimates = time_tracking.get_estimates(filters)
        
        if not estimates:
            click.echo("No time estimates found")
            return
        
        # Prepare table data
        table_data = []
        for estimate in estimates:
            created_at = estimate.created_at.strftime("%Y-%m-%d") if estimate.created_at else "N/A"
            
            # Format estimate value
            if estimate.estimate_type.value == "range":
                value = f"{estimate.estimate_value['min']}-{estimate.estimate_value['max']}"
            else:
                value = str(estimate.estimate_value)
            
            table_data.append([
                estimate.id,
                estimate.task_id,
                estimate.estimate_type.value,
                value,
                estimate.unit,
                estimate.confidence or "N/A",
                created_at,
                estimate.notes or ""
            ])
        
        # Print table
        click.echo(tabulate(
            table_data,
            headers=["ID", "Task", "Type", "Value", "Unit", "Confidence", "Created", "Notes"],
            tablefmt="grid"
        ))
    except Exception as e:
        click.echo(click.style(f"Error listing time estimates: {str(e)}", fg="red"))


def _handle_productivity_command(args, time_tracking):
    """
    Handle the productivity command.
    
    Args:
        args: Parsed command-line arguments
        time_tracking: Time tracking system instance
    """
    # Build filters
    task_ids = [args.task] if args.task else None
    
    from_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(click.style("Invalid from_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    to_date = None
    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(click.style("Invalid to_date format. Use YYYY-MM-DD.", fg="red"))
            return
    
    # Analyze productivity
    try:
        metrics, insights = time_tracking.analyze_productivity(
            user_id=args.user,
            start_date=from_date,
            end_date=to_date,
            task_ids=task_ids
        )
        
        if args.format == "json":
            # Output JSON format
            result = {
                "metrics": metrics.to_dict(),
                "insights": [insight.to_dict() for insight in insights]
            }
            click.echo(json.dumps(result, indent=2))
        else:
            # Output text format
            click.echo(click.style("=== Productivity Metrics ===", fg="blue", bold=True))
            click.echo(f"Total tracked time: {_format_duration(metrics.total_tracked_time)}")
            click.echo(f"Focus time: {_format_duration(metrics.focus_time)} ({metrics.focus_percentage:.1f}%)")
            click.echo(f"Break time: {_format_duration(metrics.break_time)}")
            click.echo(f"Task switching count: {metrics.task_switching_count}")
            click.echo(f"Average session duration: {_format_duration(metrics.avg_session_duration)}")
            click.echo(f"Longest session: {_format_duration(metrics.longest_session)}")
            
            if metrics.estimation_accuracy > 0:
                click.echo(f"Estimation accuracy: {metrics.estimation_accuracy:.1f}%")
                click.echo(f"Overestimation: {metrics.overestimation_percentage:.1f}%")
                click.echo(f"Underestimation: {metrics.underestimation_percentage:.1f}%")
            
            click.echo(f"Productivity score: {metrics.productivity_score}/100")
            
            if insights:
                click.echo("\n" + click.style("=== Productivity Insights ===", fg="blue", bold=True))
                for i, insight in enumerate(insights, 1):
                    click.echo(f"{i}. {click.style(insight.description, bold=True)}")
                    if insight.recommendation:
                        click.echo(f"   Recommendation: {insight.recommendation}")
    except Exception as e:
        click.echo(click.style(f"Error analyzing productivity: {str(e)}", fg="red"))


def _parse_duration(duration_str):
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration string (HH:MM or minutes)
        
    Returns:
        Duration in seconds
    """
    try:
        if ":" in duration_str:
            # Parse HH:MM format
            hours, minutes = duration_str.split(":")
            return (int(hours) * 60 + int(minutes)) * 60
        else:
            # Parse minutes
            return int(duration_str) * 60
    except ValueError:
        return 0


def _format_duration(duration):
    """
    Format timedelta to string.
    
    Args:
        duration: Timedelta object
        
    Returns:
        Formatted duration string
    """
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
