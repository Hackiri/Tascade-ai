"""
CLI commands for the Natural Language Task Processing system.

This module implements the CLI commands for interacting with the Natural Language
Task Processing system in Tascade AI.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

import click

from ..core.nlp.manager import TascadeNLPManager
from ..core.nlp.parser import DefaultNLParser
from ..core.nlp.executor import TaskCommandExecutor


def setup_nlp_parser(subparsers):
    """
    Set up the command-line parser for NLP commands.
    
    Args:
        subparsers: Subparsers object from argparse
    """
    # NLP command
    nlp_parser = subparsers.add_parser("nlp", help="Natural language processing commands")
    nlp_subparsers = nlp_parser.add_subparsers(dest="nlp_command", help="NLP commands")
    
    # Process command
    process_parser = nlp_subparsers.add_parser("process", help="Process natural language input")
    process_parser.add_argument("input", help="Natural language input text")
    process_parser.add_argument("--session-id", help="Session ID for conversation context")
    
    # Chat command
    chat_parser = nlp_subparsers.add_parser("chat", help="Start interactive chat session")
    chat_parser.add_argument("--session-id", help="Session ID for conversation context")
    
    # History command
    history_parser = nlp_subparsers.add_parser("history", help="Show conversation history")
    history_parser.add_argument("--session-id", required=True, help="Session ID for conversation context")
    
    # Clear history command
    clear_parser = nlp_subparsers.add_parser("clear", help="Clear conversation history")
    clear_parser.add_argument("--session-id", required=True, help="Session ID for conversation context")


def handle_nlp_command(args, task_manager, recommendation_system=None):
    """
    Handle NLP commands.
    
    Args:
        args: Parsed command-line arguments
        task_manager: Task manager instance
        recommendation_system: Optional recommendation system
    """
    # Create NLP manager
    nlp_manager = TascadeNLPManager(
        task_manager=task_manager,
        recommendation_system=recommendation_system
    )
    
    # Process command
    if args.nlp_command == "process":
        result = nlp_manager.process_input(
            text=args.input,
            session_id=args.session_id
        )
        
        # Print result
        click.echo(result["message"])
        
        if result["data"]:
            # Format data based on content
            if "task" in result["data"]:
                _print_task(result["data"]["task"])
            elif "tasks" in result["data"]:
                _print_tasks(result["data"]["tasks"])
            elif "recommendations" in result["data"]:
                _print_recommendations(result["data"]["recommendations"])
    
    # Chat command
    elif args.nlp_command == "chat":
        session_id = args.session_id or "default"
        click.echo(click.style(f"Starting chat session (ID: {session_id}). Type 'exit' or 'quit' to end.", fg="green"))
        click.echo(click.style("Type your commands in natural language:", fg="green"))
        
        while True:
            # Get user input
            try:
                user_input = input(click.style("You: ", fg="blue"))
            except (KeyboardInterrupt, EOFError):
                click.echo("\nChat session ended.")
                break
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                click.echo("Chat session ended.")
                break
            
            # Process input
            result = nlp_manager.process_input(
                text=user_input,
                session_id=session_id
            )
            
            # Print result
            click.echo(click.style("Tascade: ", fg="green") + result["message"])
            
            if result["data"]:
                # Format data based on content
                if "task" in result["data"]:
                    _print_task(result["data"]["task"])
                elif "tasks" in result["data"]:
                    _print_tasks(result["data"]["tasks"])
                elif "recommendations" in result["data"]:
                    _print_recommendations(result["data"]["recommendations"])
    
    # History command
    elif args.nlp_command == "history":
        history = nlp_manager.get_session_history(args.session_id)
        
        if not history:
            click.echo(f"No conversation history found for session ID: {args.session_id}")
            return
        
        click.echo(f"Conversation history for session ID: {args.session_id}")
        click.echo("-------------------------------------------")
        
        for i, turn in enumerate(history, 1):
            click.echo(f"Turn {i}:")
            click.echo(click.style(f"You: {turn['user_input']}", fg="blue"))
            click.echo(click.style(f"Tascade: {turn['system_response']}", fg="green"))
            click.echo("-------------------------------------------")
    
    # Clear history command
    elif args.nlp_command == "clear":
        success = nlp_manager.clear_session_history(args.session_id)
        
        if success:
            click.echo(f"Conversation history cleared for session ID: {args.session_id}")
        else:
            click.echo(f"No conversation history found for session ID: {args.session_id}")


def _print_task(task):
    """
    Print a task in a formatted way.
    
    Args:
        task: Task data
    """
    click.echo("\nTask Details:")
    click.echo(f"ID: {task.get('id', 'N/A')}")
    click.echo(f"Title: {task.get('title', 'N/A')}")
    click.echo(f"Status: {task.get('status', 'N/A')}")
    click.echo(f"Priority: {task.get('priority', 'N/A')}")
    
    if "due_date" in task:
        click.echo(f"Due Date: {task['due_date']}")
    
    if "description" in task and task["description"]:
        click.echo("\nDescription:")
        click.echo(task["description"])
    
    if "dependencies" in task and task["dependencies"]:
        click.echo("\nDependencies:")
        for dep in task["dependencies"]:
            click.echo(f"- {dep}")


def _print_tasks(tasks):
    """
    Print a list of tasks in a formatted way.
    
    Args:
        tasks: List of task data
    """
    if not tasks:
        click.echo("No tasks found.")
        return
    
    click.echo(f"\nFound {len(tasks)} tasks:")
    
    # Print header
    click.echo(f"{'ID':<10} {'Title':<30} {'Status':<15} {'Priority':<10} {'Due Date':<15}")
    click.echo("-" * 80)
    
    # Print tasks
    for task in tasks:
        task_id = task.get("id", "N/A")
        title = task.get("title", "N/A")
        status = task.get("status", "N/A")
        priority = task.get("priority", "N/A")
        due_date = task.get("due_date", "N/A")
        
        # Truncate title if too long
        if len(title) > 27:
            title = title[:24] + "..."
        
        click.echo(f"{task_id:<10} {title:<30} {status:<15} {priority:<10} {due_date:<15}")


def _print_recommendations(recommendations):
    """
    Print task recommendations in a formatted way.
    
    Args:
        recommendations: List of recommended tasks
    """
    if not recommendations:
        click.echo("No recommendations available.")
        return
    
    click.echo(f"\nRecommended Tasks ({len(recommendations)}):")
    
    # Print header
    click.echo(f"{'ID':<10} {'Title':<30} {'Score':<10} {'Priority':<10} {'Due Date':<15}")
    click.echo("-" * 80)
    
    # Print recommendations
    for rec in recommendations:
        task = rec.get("task", {})
        task_id = task.get("id", "N/A")
        title = task.get("title", "N/A")
        score = f"{rec.get('score', 0):.2f}"
        priority = task.get("priority", "N/A")
        due_date = task.get("due_date", "N/A")
        
        # Truncate title if too long
        if len(title) > 27:
            title = title[:24] + "..."
        
        click.echo(f"{task_id:<10} {title:<30} {score:<10} {priority:<10} {due_date:<15}")
        
        # Print explanation if available
        if "explanation" in rec:
            click.echo(f"  Reason: {rec['explanation']}")
