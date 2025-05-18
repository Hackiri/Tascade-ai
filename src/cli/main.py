#!/usr/bin/env python3
import os
import sys
import click
from typing import Optional
from src.core.task_manager import TaskManager
from src.parsers.prd_parser import MarkdownPRDParser
from src.core.models import TaskStatus, TaskPriority, ProjectRule # For potential future commands
from src.core.task_timetracking import TaskTimeTrackingSystem
from .task_commands import setup_task_parser, handle_task_command
from .rule_commands import setup_rule_parser, handle_rule_command
from .recommendation_commands import setup_recommendation_parser, handle_recommendation_command
from .nlp_commands import setup_nlp_parser, handle_nlp_command
from .timetracking_commands import setup_timetracking_parser, handle_timetracking_command

# Define a default path for the data file where tasks will be stored
# For simplicity, let's assume it's in the same directory as the script or a known location.
# A more robust solution might use appdirs or place it in the project root.
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".tascade-ai")
DEFAULT_DATA_FILE = os.path.join(DEFAULT_DATA_DIR, "tasks.json")

# Ensure the data directory exists
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

@click.group()
@click.pass_context
def cli(ctx):
    """Tascade AI CLI: Manage your AI-assisted development tasks."""
    # Initialize the task manager
    ctx.obj = {}
    ctx.obj['task_manager'] = TaskManager()
    
    # Initialize the time tracking system
    ctx.obj['time_tracking'] = TaskTimeTrackingSystem()
    
    # Load tasks from the default file when the CLI is invoked
    # This makes the TaskManager instance aware of existing tasks for subsequent commands
    if os.path.exists(DEFAULT_DATA_FILE):
        ctx.obj['task_manager'].load_from_file(DEFAULT_DATA_FILE)
    else:
        # If the file doesn't exist, it might be the first run. 
        # load_from_file handles FileNotFoundError gracefully.
        ctx.obj['task_manager'].load_from_file(DEFAULT_DATA_FILE)

@cli.command("import-prd")
@click.option('--prd-file', '-f', required=True, type=click.Path(exists=True, dir_okay=False, readable=True),
              help="Path to the PRD Markdown file.")
@click.pass_obj
def import_prd(obj, prd_file: str):
    """Imports tasks from a Product Requirements Document (PRD) Markdown file."""
    task_manager = obj['task_manager']
    click.echo(f"Importing tasks from PRD: {prd_file}")
    
    imported_tasks = task_manager.import_tasks_from_prd(prd_file)
    
    if imported_tasks:
        click.echo(click.style(f"Successfully imported {len(imported_tasks)} tasks:", fg="green"))
        for task in imported_tasks:
            click.echo(f"  - ID: {task.id}, Title: {task.title}")
        # Save tasks to the default file after import
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"All tasks saved to {DEFAULT_DATA_FILE}", fg="blue"))
    else:
        click.echo(click.style("No new tasks were imported.", fg="yellow"))

@cli.command("list")
@click.option('--status', type=click.Choice([s.value for s in TaskStatus], case_sensitive=False),
              help='Filter tasks by status.')
@click.option('--priority', type=click.Choice([p.value for p in TaskPriority], case_sensitive=False),
              help='Filter tasks by priority.')
@click.pass_obj
def list_tasks(obj, status: Optional[str], priority: Optional[str]):
    """Lists all tasks, with optional filters for status and priority."""
    task_manager = obj['task_manager']
    click.echo(click.style("Current Tasks:", fg="cyan"))
    
    filter_status = TaskStatus(status.lower()) if status else None
    filter_priority = TaskPriority(priority.lower()) if priority else None
    
    tasks = task_manager.list_tasks(status=filter_status, priority=filter_priority)
    
    if not tasks:
        click.echo("No tasks found matching your criteria." if (status or priority) else "No tasks found.")
        return

    for task in tasks:
        click.echo(f"- ID: {task.id}")
        click.echo(f"  Title: {task.title}")
        click.echo(f"  Status: {task.status.value}")
        click.echo(f"  Priority: {task.priority.value}")
        if task.dependencies:
            click.echo(f"  Dependencies: {', '.join(task.dependencies)}")
        if task.subtasks:
            click.echo(f"  Subtasks: {', '.join(task.subtasks)}")
        click.echo("---")

# Set up the recommendation parser
setup_recommendation_parser(cli.command_class.subcommands)

# --- Task Specific Commands ---
@cli.group("tasks")
def tasks_group():
    """Manage specific tasks, including AI-powered operations."""
    pass


@tasks_group.command("start")
@click.argument("task_id")
@click.option("--user", "-u", default=None, help="User who is starting the task.")
@click.pass_obj
def start_task(task_manager: TaskManager, task_id: str, user: str):
    """Start working on a task, marking it as in-progress."""
    try:
        task = task_manager.start_task(task_id, user=user)
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Task '{task.title}' (ID: {task.id}) started successfully.", fg="green"))
        click.echo(f"Status: {task.status.value}")
        if task.start_time:
            click.echo(f"Started at: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        click.echo(click.style(f"Error starting task: {e}", fg="red"))


@tasks_group.command("complete")
@click.argument("task_id")
@click.option("--user", "-u", default=None, help="User who completed the task.")
@click.option("--notes", "-n", default=None, help="Completion notes or comments.")
@click.pass_obj
def complete_task(task_manager: TaskManager, task_id: str, user: str, notes: str):
    """Mark a task as completed."""
    try:
        task = task_manager.complete_task(task_id, user=user, completion_notes=notes)
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Task '{task.title}' (ID: {task.id}) completed successfully.", fg="green"))
        click.echo(f"Status: {task.status.value}")
        if task.completion_time:
            click.echo(f"Completed at: {task.completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if task.duration_minutes is not None:
            hours = task.duration_minutes // 60
            minutes = task.duration_minutes % 60
            click.echo(f"Duration: {hours}h {minutes}m")
    except Exception as e:
        click.echo(click.style(f"Error completing task: {e}", fg="red"))


@tasks_group.command("pause")
@click.argument("task_id")
@click.option("--user", "-u", default=None, help="User who is pausing the task.")
@click.option("--reason", "-r", default=None, help="Reason for pausing the task.")
@click.pass_obj
def pause_task(task_manager: TaskManager, task_id: str, user: str, reason: str):
    """Pause a task that is in progress."""
    try:
        task = task_manager.pause_task(task_id, user=user, pause_reason=reason)
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Task '{task.title}' (ID: {task.id}) paused successfully.", fg="green"))
        click.echo(f"Status: {task.status.value}")
        if task.time_spent_minutes is not None:
            hours = task.time_spent_minutes // 60
            minutes = task.time_spent_minutes % 60
            click.echo(f"Time spent so far: {hours}h {minutes}m")
    except Exception as e:
        click.echo(click.style(f"Error pausing task: {e}", fg="red"))


@tasks_group.command("block")
@click.argument("task_id")
@click.option("--reason", "-r", required=True, help="Reason why the task is blocked.")
@click.option("--blocker-task", "-b", default=None, help="ID of the task that is blocking this one.")
@click.option("--user", "-u", default=None, help="User who is marking the task as blocked.")
@click.pass_obj
def block_task(task_manager: TaskManager, task_id: str, reason: str, blocker_task: str, user: str):
    """Mark a task as blocked, with a reason and optional blocker task ID."""
    try:
        task = task_manager.block_task(task_id, reason, blocker_task_id=blocker_task, user=user)
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Task '{task.title}' (ID: {task.id}) marked as blocked.", fg="yellow"))
        click.echo(f"Status: {task.status.value}")
        click.echo(f"Blocked reason: {reason}")
        if blocker_task:
            click.echo(f"Blocked by task: {blocker_task}")
    except Exception as e:
        click.echo(click.style(f"Error blocking task: {e}", fg="red"))


@tasks_group.command("unblock")
@click.argument("task_id")
@click.option("--resolution", "-r", required=True, help="How the blocker was resolved.")
@click.option("--user", "-u", default=None, help="User who is unblocking the task.")
@click.pass_obj
def unblock_task(task_manager: TaskManager, task_id: str, resolution: str, user: str):
    """Unblock a previously blocked task."""
    try:
        task = task_manager.unblock_task(task_id, resolution, user=user)
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Task '{task.title}' (ID: {task.id}) unblocked successfully.", fg="green"))
        click.echo(f"Status: {task.status.value}")
        click.echo(f"Resolution: {resolution}")
    except Exception as e:
        click.echo(click.style(f"Error unblocking task: {e}", fg="red"))


# --- Task Analysis Commands ---
@tasks_group.command("analyze")
@click.argument("task_id")
@click.pass_obj
def analyze_task(task_manager: TaskManager, task_id: str):
    """Analyze the complexity of a task."""
    try:
        complexity_result = task_manager.analyze_task_complexity(task_id)
        task = task_manager.get_task(task_id)
        
        click.echo(click.style(f"Task Analysis: '{task.title}' (ID: {task.id})", fg="blue", bold=True))
        click.echo("="*50)
        click.echo(f"Complexity Score: {complexity_result['complexity_score']}/10")
        click.echo(f"Estimated Effort: {complexity_result['estimated_effort_hours']} hours")
        
        if complexity_result.get('factors'):
            click.echo("\nComplexity Factors:")
            for factor, value in complexity_result['factors'].items():
                click.echo(f"  - {factor}: {value}")
                
        if complexity_result.get('recommendations'):
            click.echo("\nRecommendations:")
            for rec in complexity_result['recommendations']:
                click.echo(f"  - {rec}")
                
    except Exception as e:
        click.echo(click.style(f"Error analyzing task: {e}", fg="red"))


@tasks_group.command("dependencies")
@click.argument("task_id")
@click.option("--format", "-f", type=click.Choice(['text', 'json', 'mermaid']), default="text", 
              help="Output format for the dependency graph.")
@click.option("--output", "-o", type=click.Path(), default=None, 
              help="Save the output to a file instead of displaying it.")
@click.pass_obj
def show_dependencies(task_manager: TaskManager, task_id: str, format: str, output: str):
    """Show the dependency graph for a task."""
    try:
        graph = task_manager.generate_dependency_graph(task_id, format=format)
        task = task_manager.get_task(task_id)
        
        if output:
            with open(output, 'w') as f:
                f.write(graph)
            click.echo(click.style(f"Dependency graph for task '{task.title}' saved to {output}", fg="green"))
        else:
            click.echo(click.style(f"Dependency Graph for: '{task.title}' (ID: {task.id})", fg="blue", bold=True))
            click.echo("="*50)
            click.echo(graph)
            
    except Exception as e:
        click.echo(click.style(f"Error generating dependency graph: {e}", fg="red"))


@tasks_group.command("critical-path")
@click.argument("task_id", required=False)
@click.pass_obj
def show_critical_path(task_manager: TaskManager, task_id: str = None):
    """Show the critical path of tasks based on dependencies and estimated effort."""
    try:
        critical_path = task_manager.get_critical_path(task_id)
        
        if not critical_path:
            click.echo("No critical path found.")
            return
            
        click.echo(click.style("Critical Path Analysis", fg="blue", bold=True))
        click.echo("="*50)
        click.echo(f"Total Path Duration: {critical_path['total_duration']} hours")
        click.echo("\nPath:")
        
        for i, task_info in enumerate(critical_path['path']):
            task = task_info['task']
            click.echo(f"{i+1}. {task.title} (ID: {task.id})")
            click.echo(f"   Effort: {task_info['effort']} hours")
            if i < len(critical_path['path']) - 1:
                click.echo("   ↓")
                
    except Exception as e:
        click.echo(click.style(f"Error finding critical path: {e}", fg="red"))


# --- Project Rules CLI Commands ---
@cli.group("rules")
def rules_group():
    """Manage project-specific rules and guidelines."""
    pass

@rules_group.command("add")
@click.option('--name', '-n', required=True, help="Name of the project rule.")
@click.option('--description', '-d', required=True, help="Short description of the rule's purpose.")
@click.option('--content', '-c', required=True, help="The full content of the rule or guideline.")
@click.option('--tags', '-t', default='', help="Comma-separated list of tags this rule applies to (e.g., 'backend,api').")
@click.option('--active/--inactive', 'is_active', default=True, help="Set the rule as active (default) or inactive.")
@click.pass_obj
def add_rule(task_manager: TaskManager, name: str, description: str, content: str, tags: str, is_active: bool):
    """Adds a new project rule."""
    applies_to_tags = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    
    try:
        rule = task_manager.add_project_rule(
            name=name,
            description=description,
            content=content,
            applies_to_tags=applies_to_tags,
            is_active=is_active
        )
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Project rule '{rule.name}' (ID: {rule.id}) added successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error adding project rule: {e}", fg="red"))

@rules_group.command("list")
@click.option('--show-content', is_flag=True, help="Display the full content of each rule.")
@click.pass_obj
def list_rules(task_manager: TaskManager, show_content: bool):
    """Lists all project rules."""
    project_rules = task_manager.list_project_rules()
    if not project_rules:
        click.echo("No project rules found.")
        return

    click.echo(click.style("Project Rules:", fg="cyan"))
    for rule in project_rules:
        status_color = "green" if rule.is_active else "red"
        active_text = click.style("Active" if rule.is_active else "Inactive", fg=status_color)
        click.echo(f"- ID: {rule.id}")
        click.echo(f"  Name: {rule.name}")
        click.echo(f"  Status: {active_text}")
        click.echo(f"  Description: {rule.description}")
        if rule.applies_to_tags:
            click.echo(f"  Applies to Tags: {', '.join(rule.applies_to_tags)}")
        if show_content:
            click.echo(f"  Content: \n{'-'*10}\n{rule.content}\n{'-'*10}")
        click.echo("---")

@rules_group.command("show")
@click.argument('rule_id')
@click.pass_obj
def show_rule(task_manager: TaskManager, rule_id: str):
    """Shows detailed information for a specific project rule."""
    rule = task_manager.get_project_rule(rule_id)
    if not rule:
        click.echo(click.style(f"Error: Project rule with ID '{rule_id}' not found.", fg="red"))
        return

    status_color = "green" if rule.is_active else "red"
    active_text = click.style("Active" if rule.is_active else "Inactive", fg=status_color)
    click.echo(click.style(f"Details for Rule ID: {rule.id}", fg="cyan"))
    click.echo(f"  Name: {rule.name}")
    click.echo(f"  Status: {active_text}")
    click.echo(f"  Description: {rule.description}")
    if rule.applies_to_tags:
        click.echo(f"  Applies to Tags: {', '.join(rule.applies_to_tags)}")
    click.echo(f"  Created At: {rule.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    click.echo(f"  Updated At: {rule.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    click.echo(f"  Content: \n{'-'*10}\n{rule.content}\n{'-'*10}")

@rules_group.command("update")
@click.argument('rule_id')
@click.option('--name', '-n', help="New name for the project rule.")
@click.option('--description', '-d', help="New short description of the rule's purpose.")
@click.option('--content', '-c', help="New full content of the rule or guideline.")
@click.option('--tags', help="Comma-separated list of tags this rule applies to (e.g., 'backend,api'). Use '' to clear tags.")
@click.option('--active/--inactive', 'is_active', default=None, help="Set the rule as active or inactive.")
@click.pass_obj
def update_rule(task_manager: TaskManager, rule_id: str, name: Optional[str], description: Optional[str], 
                content: Optional[str], tags: Optional[str], is_active: Optional[bool]):
    """Updates an existing project rule. Only provided fields are changed."""
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if content is not None:
        update_data['content'] = content
    if tags is not None:
        update_data['applies_to_tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    if is_active is not None:
        update_data['is_active'] = is_active

    if not update_data:
        click.echo("No update information provided.")
        return

    updated_rule = task_manager.update_project_rule(rule_id, update_data)

    if updated_rule:
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Project rule '{updated_rule.name}' (ID: {rule_id}) updated successfully.", fg="green"))
    else:
        click.echo(click.style(f"Error: Project rule with ID '{rule_id}' not found or no changes made.", fg="red"))

@rules_group.command("delete")
@click.argument('rule_id')
@click.option('--yes', '-y', is_flag=True, help="Skip confirmation prompt.")
@click.pass_obj
def delete_rule(task_manager: TaskManager, rule_id: str, yes: bool):
    """Deletes a project rule."""
    rule = task_manager.get_project_rule(rule_id)
    if not rule:
        click.echo(click.style(f"Error: Project rule with ID '{rule_id}' not found.", fg="red"))
        return

    if not yes:
        click.confirm(f"Are you sure you want to delete rule '{rule.name}' (ID: {rule_id})?", abort=True)

    if task_manager.delete_project_rule(rule_id):
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Project rule '{rule.name}' (ID: {rule_id}) deleted successfully.", fg="green"))
    else:
        # This case should ideally not be reached if get_project_rule found it earlier
        click.echo(click.style(f"Error: Failed to delete project rule with ID '{rule_id}'.", fg="red"))

@rules_group.command("activate")
@click.argument('rule_id')
@click.pass_obj
def activate_rule(task_manager: TaskManager, rule_id: str):
    """Activates a project rule (sets is_active to True)."""
    updated_rule = task_manager.update_project_rule(rule_id, {'is_active': True})
    if updated_rule:
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Project rule '{updated_rule.name}' (ID: {rule_id}) activated.", fg="green"))
    else:
        click.echo(click.style(f"Error: Project rule with ID '{rule_id}' not found.", fg="red"))

@rules_group.command("deactivate")
@click.argument('rule_id')
@click.pass_obj
def deactivate_rule(task_manager: TaskManager, rule_id: str):
    """Deactivates a project rule (sets is_active to False)."""
    updated_rule = task_manager.update_project_rule(rule_id, {'is_active': False})
    if updated_rule:
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"Project rule '{updated_rule.name}' (ID: {rule_id}) deactivated.", fg="yellow"))
    else:
        click.echo(click.style(f"Error: Project rule with ID '{rule_id}' not found.", fg="red"))


from ..core.ai_decomposer import AIDecomposer
import json # For pretty printing dicts

@tasks_group.command("decompose")
@click.argument('task_id')
@click.option('--instructions', '-i', help="Custom instructions for the AI decomposer.")
@click.option('--project-root', default=None, help="Project root directory (defaults to current dir for CLI). Required for AI tools.")
@click.pass_obj
def decompose_task(task_manager: TaskManager, task_id: str, instructions: Optional[str], project_root: Optional[str]):
    """Decomposes a task into subtasks using AI (simulated MCP calls)."""
    
    parent_task = task_manager.get_task(task_id)
    if not parent_task:
        click.echo(click.style(f"Error: Task with ID '{task_id}' not found.", fg="red"))
        return

    if project_root is None:
        project_root = os.getcwd()
        click.echo(click.style(f"No --project-root provided, defaulting to current directory: {project_root}", fg="yellow"))

    click.echo(click.style(f"Decomposing task: '{parent_task.title}' (ID: {parent_task.id})", fg="cyan"))

    active_rules = [rule for rule in task_manager.list_project_rules() if rule.is_active]
    if active_rules:
        click.echo(f"Considering {len(active_rules)} active project rules for decomposition.")

    decomposer = AIDecomposer(task_manager_mcp_server_name="taskmaster-ai")
    
    mcp_call_sequence = decomposer.prepare_mcp_calls_for_decomposition(
        parent_task,
        active_rules,
        custom_instructions=instructions,
        project_root=project_root
    )

    # Simulate MCP call execution
    temp_task_master_id = None
    llm_response_content = None

    click.echo(click.style("Simulating MCP Call Sequence:", fg="magenta"))

    # 1. Simulate mcp3_add_task
    add_task_call_info = next((call for call in mcp_call_sequence if call['tool_name'] == 'mcp3_add_task'), None)
    if add_task_call_info:
        click.echo(f"  1. Would call MCP tool: {add_task_call_info['tool_name']} on server '{decomposer.task_manager_mcp_server_name}'")
        click.echo(f"     Purpose: {add_task_call_info['purpose']}")
        # click.echo(f"     Params: {json.dumps(add_task_call_info['params'], indent=2)}")
        temp_task_master_id = f"simulated_tm_id_{uuid.uuid4()}" # Simulate ID generation
        click.echo(click.style(f"     Simulated '{decomposer.task_manager_mcp_server_name}' task ID: {temp_task_master_id}", fg="green"))
    else:
        click.echo(click.style("Error: mcp3_add_task preparation failed.", fg="red"))
        return

    # 2. Simulate mcp3_expand_task
    expand_task_call_info = next((call for call in mcp_call_sequence if call['tool_name'] == 'mcp3_expand_task'), None)
    if expand_task_call_info:
        # Inject the simulated temp_task_master_id into params for the call
        expand_task_call_info['params']['id'] = temp_task_master_id
        click.echo(f"  2. Would call MCP tool: {expand_task_call_info['tool_name']} on server '{decomposer.task_manager_mcp_server_name}'")
        click.echo(f"     Purpose: {expand_task_call_info['purpose']}")
        # click.echo(f"     Params (prompt might be long): {{'id': '{temp_task_master_id}', 'projectRoot': '{project_root}', 'prompt': '[...]', 'force': True}}")
        
        # Simulate LLM response (this is where actual LLM call would happen)
        simulated_llm_output_for_cli = [
            {'title': 'Simulated Subtask 1: Design Database Model', 'description': 'Define tables, columns, and relationships for the new feature.'},
            {'title': 'Simulated Subtask 2: Implement API Endpoints', 'description': 'Create CRUD endpoints for the new resource.'},
            {'title': 'Simulated Subtask 3: Develop UI Components', 'description': 'Build frontend components to interact with the new API.'}
        ]
        llm_response_content = simulated_llm_output_for_cli # In reality, this comes from the MCP tool
        click.echo(click.style(f"     Simulated LLM response received (containing {len(llm_response_content)} subtasks).", fg="green"))
    else:
        click.echo(click.style("Error: mcp3_expand_task preparation failed.", fg="red"))
        return

    # Parse the (simulated) LLM response
    try:
        parsed_subtasks = decomposer.parse_llm_response_for_subtasks(llm_response_content)
    except ValueError as e:
        click.echo(click.style(f"Error parsing LLM response: {e}", fg="red"))
        return

    if not parsed_subtasks:
        click.echo(click.style("AI did not suggest any subtasks.", fg="yellow"))
        # Attempt to clean up the temporary task in taskmaster-ai if it was created
        if temp_task_master_id:
            click.echo(f"  3. Would call MCP tool: mcp3_remove_task on server '{decomposer.task_manager_mcp_server_name}' with ID {temp_task_master_id} for cleanup.")
        return

    # User Review and Confirmation
    click.echo(click.style("\nSuggested Subtasks for Review:", fg="yellow"))
    for i, subtask in enumerate(parsed_subtasks):
        click.echo(f"  {i+1}. Title: {subtask['title']}")
        click.echo(f"     Description: {subtask['description']}")
    
    if not click.confirm(click.style("\nDo you want to add these subtasks?", fg="blue"), default=True):
        click.echo("Subtask addition aborted by user.")
        # Attempt to clean up the temporary task in taskmaster-ai
        if temp_task_master_id:
            click.echo(f"  3. Would call MCP tool: mcp3_remove_task on server '{decomposer.task_manager_mcp_server_name}' with ID {temp_task_master_id} for cleanup.")
        return

    # Add confirmed subtasks to TaskManager
    created_subtasks = task_manager.add_subtasks_from_ai(parent_task.id, parsed_subtasks)
    
    if created_subtasks:
        click.echo(click.style(f"Successfully added {len(created_subtasks)} subtasks to '{parent_task.title}'.", fg="green"))
        task_manager.save_to_file(DEFAULT_DATA_FILE)
        click.echo(click.style(f"All changes saved to {DEFAULT_DATA_FILE}", fg="blue"))
    else:
        click.echo(click.style("No subtasks were added.", fg="yellow"))

    # 3. Simulate mcp3_remove_task for cleanup
    if temp_task_master_id:
        click.echo(f"  3. Would call MCP tool: mcp3_remove_task on server '{decomposer.task_manager_mcp_server_name}' with ID {temp_task_master_id} for cleanup.")
        click.echo(click.style("Simulated MCP cleanup call complete.", fg="magenta"))

# Handle recommendation commands
@cli.command("recommend", context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def recommend_command(ctx, args):
    """Task recommendation commands."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Task recommendation commands")
    subparsers = parser.add_subparsers(dest="recommendation_command", help="Recommendation commands")
    
    # Set up recommendation parser
    setup_recommendation_parser(subparsers)
    
    # Parse arguments
    try:
        parsed_args = parser.parse_args(["recommend"] + list(args))
    except SystemExit:
        return
    
    # Handle recommendation command
    return handle_recommendation_command(
        parsed_args, 
        ctx.obj['task_manager'], 
        ctx.obj['time_tracking']
    )


# Handle NLP commands
@cli.command("nlp", context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def nlp_command(ctx, args):
    """Natural language processing commands."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Natural language processing commands")
    subparsers = parser.add_subparsers(dest="nlp_command", help="NLP commands")
    
    # Set up NLP parser
    setup_nlp_parser(subparsers)
    
    # Parse arguments
    try:
        parsed_args = parser.parse_args(["nlp"] + list(args))
    except SystemExit:
        return
    
    # Handle NLP command
    return handle_nlp_command(
        parsed_args, 
        ctx.obj['task_manager'],
        ctx.obj.get('recommendation_system')
    )


# Handle Time Tracking commands
@cli.command("time", context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def time_command(ctx, args):
    """Time tracking commands."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Time tracking commands")
    subparsers = parser.add_subparsers(dest="time_command", help="Time tracking commands")
    
    # Set up time tracking parser
    setup_timetracking_parser(subparsers)
    
    # Parse arguments
    try:
        parsed_args = parser.parse_args(["time"] + list(args))
    except SystemExit:
        return
    
    # Handle time tracking command
    return handle_timetracking_command(
        parsed_args, 
        ctx.obj['task_manager'],
        ctx.obj['time_tracking']
    )


if __name__ == '__main__':
    cli()
