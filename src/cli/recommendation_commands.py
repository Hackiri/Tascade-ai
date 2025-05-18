"""
CLI commands for the Task Recommendation System.

This module provides CLI commands for interacting with the
Task Recommendation System from the command line.
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..core.task_recommendation import TaskRecommendationSystem
from ..core.task_manager import TaskManager
from ..core.task_timetracking import TaskTimeTrackingSystem


def setup_recommendation_parser(subparsers):
    """Set up the recommendation parser."""
    # Create recommendation parser
    recommendation_parser = subparsers.add_parser(
        "recommend",
        help="Task recommendation commands"
    )
    recommendation_subparsers = recommendation_parser.add_subparsers(
        dest="recommendation_command",
        help="Recommendation commands"
    )
    
    # Get recommendations
    get_parser = recommendation_subparsers.add_parser(
        "get",
        help="Get task recommendations"
    )
    get_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to get recommendations for"
    )
    get_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of recommendations to return"
    )
    get_parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    
    # Set user preference
    preference_parser = recommendation_subparsers.add_parser(
        "set-preference",
        help="Set user preference"
    )
    preference_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to set preference for"
    )
    preference_parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="Preference type"
    )
    preference_parser.add_argument(
        "--value",
        type=str,
        required=True,
        help="Preference value (use JSON format for lists or objects)"
    )
    preference_parser.add_argument(
        "--weight",
        type=float,
        default=1.0,
        help="Preference weight"
    )
    
    # Get user preferences
    get_preferences_parser = recommendation_subparsers.add_parser(
        "get-preferences",
        help="Get user preferences"
    )
    get_preferences_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to get preferences for"
    )
    get_preferences_parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    
    # Delete user preference
    delete_preference_parser = recommendation_subparsers.add_parser(
        "delete-preference",
        help="Delete user preference"
    )
    delete_preference_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to delete preference for"
    )
    delete_preference_parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="Preference type to delete"
    )
    
    # Record task completion
    record_completion_parser = recommendation_subparsers.add_parser(
        "record-completion",
        help="Record task completion"
    )
    record_completion_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to record completion for"
    )
    record_completion_parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="Task ID to record completion for"
    )
    
    # Get user performance
    performance_parser = recommendation_subparsers.add_parser(
        "get-performance",
        help="Get user performance"
    )
    performance_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to get performance for"
    )
    performance_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze"
    )
    performance_parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    
    # Set workload settings
    workload_parser = recommendation_subparsers.add_parser(
        "set-workload",
        help="Set workload settings"
    )
    workload_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to set workload for"
    )
    workload_parser.add_argument(
        "--daily-capacity",
        type=int,
        default=480,
        help="Daily capacity in minutes"
    )
    workload_parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="Maximum concurrent tasks"
    )
    workload_parser.add_argument(
        "--preferred-size",
        type=str,
        choices=["small", "medium", "large"],
        default="medium",
        help="Preferred task size"
    )
    
    # Get workload settings
    get_workload_parser = recommendation_subparsers.add_parser(
        "get-workload",
        help="Get workload settings"
    )
    get_workload_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to get workload for"
    )
    get_workload_parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    
    # Explain recommendation
    explain_parser = recommendation_subparsers.add_parser(
        "explain",
        help="Explain task recommendation"
    )
    explain_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to explain for"
    )
    explain_parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="Task ID to explain"
    )
    
    # Predict task completion time
    predict_parser = recommendation_subparsers.add_parser(
        "predict-time",
        help="Predict task completion time"
    )
    predict_parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to predict for"
    )
    predict_parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="Task ID to predict for"
    )


def handle_recommendation_command(args, task_manager, time_tracking_system):
    """Handle recommendation commands."""
    # Create recommendation system
    recommendation_system = TaskRecommendationSystem(
        task_manager=task_manager,
        time_tracking_system=time_tracking_system
    )
    
    # Handle commands
    if args.recommendation_command == "get":
        return handle_get_recommendations(args, recommendation_system)
    elif args.recommendation_command == "set-preference":
        return handle_set_preference(args, recommendation_system)
    elif args.recommendation_command == "get-preferences":
        return handle_get_preferences(args, recommendation_system)
    elif args.recommendation_command == "delete-preference":
        return handle_delete_preference(args, recommendation_system)
    elif args.recommendation_command == "record-completion":
        return handle_record_completion(args, recommendation_system, task_manager)
    elif args.recommendation_command == "get-performance":
        return handle_get_performance(args, recommendation_system)
    elif args.recommendation_command == "set-workload":
        return handle_set_workload(args, recommendation_system)
    elif args.recommendation_command == "get-workload":
        return handle_get_workload(args, recommendation_system)
    elif args.recommendation_command == "explain":
        return handle_explain(args, recommendation_system)
    elif args.recommendation_command == "predict-time":
        return handle_predict_time(args, recommendation_system)
    else:
        print("Unknown recommendation command. Use 'recommend --help' for usage information.")
        return 1


def handle_get_recommendations(args, recommendation_system):
    """Handle get recommendations command."""
    # Get recommendations
    result = recommendation_system.recommend_tasks(
        user_id=args.user_id,
        limit=args.limit
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    recommendations = result["recommendations"]
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Print as table
        print("\nTask Recommendations:")
        print(f"{'ID':<10} {'Title':<40} {'Priority':<10} {'Score':<10}")
        print("-" * 70)
        
        for rec in recommendations:
            task = rec["task"]
            print(f"{task['id']:<10} {task['title'][:38]:<40} {task['priority']:<10} {rec['score']:.2f}")
        
        print(f"\nTotal: {len(recommendations)} recommendations")
    
    return 0


def handle_set_preference(args, recommendation_system):
    """Handle set preference command."""
    # Parse value
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        # If not valid JSON, use as string
        value = args.value
    
    # Set preference
    result = recommendation_system.set_user_preference(
        user_id=args.user_id,
        preference_type=args.type,
        preference_value=value,
        weight=args.weight
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Preference '{args.type}' set for user '{args.user_id}'")
    return 0


def handle_get_preferences(args, recommendation_system):
    """Handle get preferences command."""
    # Get preferences
    result = recommendation_system.get_user_preferences(args.user_id)
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    preferences = result["preferences"]
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Print as table
        print("\nUser Preferences:")
        print(f"{'Type':<20} {'Value':<40} {'Weight':<10}")
        print("-" * 70)
        
        for pref in preferences:
            value_str = str(pref["preference_value"])
            if len(value_str) > 38:
                value_str = value_str[:35] + "..."
            
            print(f"{pref['preference_type']:<20} {value_str:<40} {pref['weight']:<10}")
        
        print(f"\nTotal: {len(preferences)} preferences")
    
    return 0


def handle_delete_preference(args, recommendation_system):
    """Handle delete preference command."""
    # Delete preference
    result = recommendation_system.delete_user_preference(
        user_id=args.user_id,
        preference_type=args.type
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Preference '{args.type}' deleted for user '{args.user_id}'")
    return 0


def handle_record_completion(args, recommendation_system, task_manager):
    """Handle record completion command."""
    # Get task
    task = task_manager.get_task(args.task_id)
    
    if not task:
        print(f"Error: Task '{args.task_id}' not found")
        return 1
    
    # Record completion
    result = recommendation_system.record_task_completion(
        user_id=args.user_id,
        task_id=args.task_id,
        task_data=task
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Task completion recorded for task '{args.task_id}' and user '{args.user_id}'")
    return 0


def handle_get_performance(args, recommendation_system):
    """Handle get performance command."""
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    # Get performance
    result = recommendation_system.get_user_performance(
        user_id=args.user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    performance = result["performance"]
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Print as table
        print("\nUser Performance:")
        print(f"User ID: {args.user_id}")
        print(f"Date Range: {start_date.date()} to {end_date.date()} ({args.days} days)")
        print(f"Task Count: {performance.get('task_count', 0)}")
        print(f"Average Accuracy: {performance.get('average_accuracy', 0):.2f}%")
        
        # Print category performance
        print("\nCategory Performance:")
        print(f"{'Category':<20} {'Count':<10} {'Avg Accuracy':<15} {'Avg Time (min)':<15}")
        print("-" * 60)
        
        for category, data in performance.get("category_performance", {}).items():
            print(f"{category:<20} {data.get('count', 0):<10} {data.get('average_accuracy', 0):.2f}%{'':<5} {data.get('average_completion_time', 0):<15}")
    
    return 0


def handle_set_workload(args, recommendation_system):
    """Handle set workload command."""
    # Set workload settings
    result = recommendation_system.set_workload_settings(
        user_id=args.user_id,
        daily_capacity_minutes=args.daily_capacity,
        max_concurrent_tasks=args.max_tasks,
        preferred_task_size=args.preferred_size
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Workload settings set for user '{args.user_id}'")
    return 0


def handle_get_workload(args, recommendation_system):
    """Handle get workload command."""
    # Get workload settings
    result = recommendation_system.get_workload_settings(args.user_id)
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    settings = result["settings"]
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Print as table
        print("\nWorkload Settings:")
        print(f"User ID: {args.user_id}")
        print(f"Daily Capacity: {settings.get('daily_capacity_minutes', 0)} minutes")
        print(f"Max Concurrent Tasks: {settings.get('max_concurrent_tasks', 0)}")
        print(f"Preferred Task Size: {settings.get('preferred_task_size', 'medium')}")
        
        # Print category limits
        category_limits = settings.get("category_limits", {})
        if category_limits:
            print("\nCategory Limits:")
            print(f"{'Category':<20} {'Limit':<10}")
            print("-" * 30)
            
            for category, limit in category_limits.items():
                print(f"{category:<20} {limit:<10}")
        
        # Print priority weights
        priority_weights = settings.get("priority_weights", {})
        if priority_weights:
            print("\nPriority Weights:")
            print(f"{'Priority':<20} {'Weight':<10}")
            print("-" * 30)
            
            for priority, weight in priority_weights.items():
                print(f"{priority:<20} {weight:<10}")
    
    return 0


def handle_explain(args, recommendation_system):
    """Handle explain command."""
    # Get explanation
    result = recommendation_system.explain_recommendation(
        user_id=args.user_id,
        task_id=args.task_id
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    explanation = result["explanation"]
    
    print("\nRecommendation Explanation:")
    print(f"Task ID: {args.task_id}")
    print(f"Overall Score: {explanation.get('overall_score', 0):.2f}")
    print("\nTop Factors:")
    
    for factor, score in explanation.get("top_factors", []):
        print(f"- {factor}: {score:.2f}")
    
    print("\nExplanation:")
    print(explanation.get("explanation", "No explanation available"))
    
    return 0


def handle_predict_time(args, recommendation_system):
    """Handle predict time command."""
    # Get prediction
    result = recommendation_system.predict_task_completion_time(
        user_id=args.user_id,
        task_id=args.task_id
    )
    
    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1
    
    prediction = result["prediction"]
    
    print("\nTask Completion Time Prediction:")
    print(f"Task ID: {args.task_id}")
    print(f"Predicted Time: {prediction.get('predicted_minutes', 0)} minutes")
    print(f"Confidence: {prediction.get('confidence', 0):.2f}")
    print(f"Basis: {prediction.get('basis', 'Unknown')}")
    
    if "similar_tasks_count" in prediction:
        print(f"Similar Tasks: {prediction['similar_tasks_count']}")
    
    return 0
