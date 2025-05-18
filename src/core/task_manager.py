from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from .models import Task, TaskStatus, TaskPriority, ProjectRule
from ..parsers.prd_parser import MarkdownPRDParser
from .ai_providers.base import BaseAIProvider
from .dependency_manager import DependencyManager
from .task_prioritizer import TaskPrioritizer
from .task_reflector import TaskReflector
from .task_splitter import TaskSplitter
from .task_verifier import TaskVerifier
from .task_planner import TaskPlanner
from .task_executor import TaskExecutor
from .task_analytics import TaskAnalytics, AnalyticsTimeFrame, AnalyticsMetricType
from .task_collaboration import TaskCollaboration, CollaborationRole, CollaborationAction
from .task_templates import TaskTemplateSystem
from .task_io import TaskIO, TaskImportError, TaskExportError
from .prompts import load_prompt, render_template
import uuid
import os
import json
from datetime import datetime, timedelta
from enum import Enum

class TaskManager:
    def __init__(self, ai_provider: Optional[Union[BaseAIProvider, str]] = None):
        """Initialize the TaskManager.
        
        Args:
            ai_provider: Optional AI provider instance or provider name ('anthropic', 'openai')
                         If a string is provided, the corresponding provider will be initialized
                         with API keys from environment variables.
        """
        self._tasks: Dict[str, Task] = {}
        self._project_rules: Dict[str, ProjectRule] = {}
        
        # Initialize AI provider if specified
        self.ai_provider = None
        if ai_provider:
            if isinstance(ai_provider, BaseAIProvider):
                self.ai_provider = ai_provider
            elif isinstance(ai_provider, str):
                self.ai_provider = self._initialize_ai_provider(ai_provider)
                
        # Initialize helper components
        self.task_reflector = TaskReflector(self.ai_provider)
        self.task_splitter = TaskSplitter(self.ai_provider)
        self.task_verifier = TaskVerifier(self.ai_provider)
        self.task_planner = TaskPlanner(self.ai_provider)
        self.task_executor = TaskExecutor(self.ai_provider)
        
        # Initialize analytics component
        analytics_dir = os.path.join(self.data_dir, "analytics") if self.data_dir else None
        self.task_analytics = TaskAnalytics(analytics_dir)
        
        # Initialize collaboration component
        collaboration_dir = os.path.join(self.data_dir, "collaboration") if self.data_dir else None
        self.task_collaboration = TaskCollaboration(collaboration_dir)
        
        # Initialize templates component
        templates_dir = os.path.join(self.data_dir, "templates") if self.data_dir else None
        self.task_templates = TaskTemplateSystem(templates_dir)
        
        # Initialize import/export component
        self.task_io = TaskIO()
    
    def _initialize_ai_provider(self, provider_name: str) -> Optional[BaseAIProvider]:
        """Initialize an AI provider by name.
        
        Args:
            provider_name: Name of the provider ('anthropic', 'openai')
            
        Returns:
            Initialized AI provider or None if initialization fails
        """
        try:
            if provider_name.lower() == 'anthropic':
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if api_key:
                    return AnthropicProvider(api_key=api_key)
            elif provider_name.lower() == 'openai':
                api_key = os.environ.get('OPENAI_API_KEY')
                if api_key:
                    return OpenAIProvider(api_key=api_key)
            return None
        except Exception as e:
            print(f"Error initializing AI provider: {str(e)}")
            return None
    
    def set_ai_provider(self, provider: Union[BaseAIProvider, str]) -> bool:
        """Set or change the AI provider.
        
        Args:
            provider: AI provider instance or provider name ('anthropic', 'openai')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(provider, BaseAIProvider):
                self.ai_provider = provider
                return True
            elif isinstance(provider, str):
                provider_instance = self._initialize_ai_provider(provider)
                if provider_instance:
                    self.ai_provider = provider_instance
                    return True
            return False
        except Exception as e:
            print(f"Error setting AI provider: {str(e)}")
            return False

    # Task Management Methods
    def add_task(self, title: str, description: Optional[str] = None, 
                 priority: TaskPriority = TaskPriority.MEDIUM, 
                 dependencies: Optional[List[str]] = None, 
                 subtasks: Optional[List[str]] = None,
                 project_context_tags: Optional[List[str]] = None,
                 details: Optional[Dict[str, Any]] = None,
                 status: TaskStatus = TaskStatus.PENDING) -> Task:
        """Creates a new task and adds it to the manager."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            dependencies=dependencies or [],
            subtasks=subtasks or [],
            project_context_tags=project_context_tags or [],
            details=details or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._tasks[task_id] = task
        task._add_history_entry("Task created", user="system")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieves a task by its ID."""
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, update_data: Dict[str, Any], user: Optional[str] = "system") -> Optional[Task]:
        """Updates an existing task. Allows partial updates."""
        task = self.get_task(task_id)
        if not task:
            return None

        changes = []
        for key, value in update_data.items():
            if hasattr(task, key):
                old_value = getattr(task, key)
                if isinstance(old_value, Enum) and isinstance(value, str):
                    # Convert string to Enum type if necessary
                    enum_class = type(old_value)
                    try:
                        value = enum_class(value.lower())
                    except ValueError:
                        # Invalid enum value, skip or handle error
                        print(f"Warning: Invalid value '{value}' for {key}. Skipping update for this field.")
                        continue
                
                if old_value != value:
                    setattr(task, key, value)
                    changes.append(f"{key} changed from '{old_value}' to '{value}'")
            else:
                 # Potentially updating task.details or other custom fields
                 if key in task.details and task.details[key] != value:
                    changes.append(f"details.{key} changed from '{task.details[key]}' to '{value}'")
                    task.details[key] = value
                 elif key not in task.details:
                    changes.append(f"details.{key} set to '{value}'")
                    task.details[key] = value
        
        if changes:
            task.touch()
            task._add_history_entry(f"Task updated: {'; '.join(changes)}", user=user)
        return task

    def delete_task(self, task_id: str, user: Optional[str] = "system") -> bool:
        """Deletes a task by its ID."""
        if task_id in self._tasks:
            # Potentially add to history of other tasks if it was a dependency/subtask
            # For now, just simple deletion
            del self._tasks[task_id]
            # Consider adding a global history log for deletions if needed
            return True
        return False

    def list_tasks(self, status: Optional[TaskStatus] = None, 
                     priority: Optional[TaskPriority] = None, 
                     assigned_to: Optional[str] = None,
                     tags_include_any: Optional[List[str]] = None) -> List[Task]:
        """Lists tasks, optionally filtering by status, priority, assignee, or tags."""
        filtered_tasks = list(self._tasks.values())

        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]
        if priority:
            filtered_tasks = [task for task in filtered_tasks if task.priority == priority]
        if assigned_to:
            filtered_tasks = [task for task in filtered_tasks if task.assigned_to == assigned_to]
        if tags_include_any:
            filtered_tasks = [task for task in filtered_tasks 
                              if any(tag in task.project_context_tags for tag in tags_include_any)]
            
        return sorted(filtered_tasks, key=lambda t: t.created_at)

    def get_subtasks(self, parent_task_id: str) -> List[Task]:
        """Retrieves all direct subtasks for a given parent task ID."""
        parent_task = self.get_task(parent_task_id)
        if not parent_task:
            return []
        return [self.get_task(sub_id) for sub_id in parent_task.subtasks if self.get_task(sub_id)]

    def add_subtasks_from_ai(
        self,
        parent_task_id: str,
        suggested_subtasks: List[Dict[str, str]],
        user: Optional[str] = "system_ai"
    ) -> List[Task]:
        """
        Adds subtasks generated by AI to a parent task.

        Args:
            parent_task_id: The ID of the parent task.
            suggested_subtasks: A list of dictionaries, each with 'title' and 'description'
                                for a new subtask.
            user: The user initiating the action, defaults to 'system_ai'.

        Returns:
            A list of the newly created Task objects (subtasks).
        """
        parent_task = self.get_task(parent_task_id)
        if not parent_task:
            print(f"Warning: Parent task with ID '{parent_task_id}' not found. Cannot add AI subtasks.")
            return []

        created_tasks: List[Task] = []
        new_subtask_ids: List[str] = []

        # Determine properties to inherit from parent
        inherited_priority = parent_task.priority
        inherited_tags = list(parent_task.project_context_tags) # Create a copy

        for sub_suggestion in suggested_subtasks:
            title = sub_suggestion.get('title')
            description = sub_suggestion.get('description')

            if not title:
                print(f"Warning: AI suggested subtask for parent '{parent_task_id}' is missing a title. Skipping.")
                continue

            # Add a detail indicating AI generation
            subtask_details = {
                "ai_generated_from_parent_id": parent_task_id,
                "ai_generation_timestamp": datetime.utcnow().isoformat()
            }

            new_subtask = self.add_task(
                title=title,
                description=description,
                priority=inherited_priority,
                project_context_tags=inherited_tags,
                details=subtask_details,
                status=TaskStatus.PENDING # Subtasks start as PENDING
            )
            # add_task already adds a history entry to the new_subtask: "Task created"
            created_tasks.append(new_subtask)
            new_subtask_ids.append(new_subtask.id)

        if new_subtask_ids:
            parent_task.subtasks.extend(new_subtask_ids)
            parent_task.touch() # Update parent's updated_at timestamp
            parent_task._add_history_entry(
                f"{len(new_subtask_ids)} subtask(s) added by AI ({user}).",
                user=user
            )
            # Note: self.save_to_file() is not called here; caller should handle persistence.
            print(f"Added {len(new_subtask_ids)} AI-generated subtasks to parent task '{parent_task_id}'.")
        
        return created_tasks

    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """Retrieves tasks that list the given task_id as a dependency."""
        dependents = []
        for t in self._tasks.values():
            if task_id in t.dependencies:
                dependents.append(t)
        return dependents
    
    def get_tasks_blocking(self, task_id: str) -> List[Task]:
        """Retrieves tasks that the given task_id depends on (i.e., its direct blockers)."""
        task = self.get_task(task_id)
        if not task:
            return []
        return [self.get_task(dep_id) for dep_id in task.dependencies if self.get_task(dep_id)]

    # Task Execution Tracking Methods
    def start_task(self, task_id: str, user: Optional[str] = "system") -> Optional[Task]:
        """Mark a task as in progress and record start time."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Check if all dependencies are completed
        blocking_tasks = self.get_tasks_blocking(task_id)
        incomplete_blockers = [t for t in blocking_tasks if t.status != TaskStatus.COMPLETED]
        
        if incomplete_blockers:
            blocker_ids = [t.id for t in incomplete_blockers]
            print(f"Warning: Task {task_id} has incomplete dependencies: {', '.join(blocker_ids)}")
            # You could choose to prevent starting or just warn
            
        # Update task status and timestamps
        task.status = TaskStatus.IN_PROGRESS
        current_time = datetime.utcnow()
        
        # Store start time in details if not already there
        if 'started_at' not in task.details:
            task.details['started_at'] = current_time.isoformat()
            
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task marked as in progress", user=user)
        return task
        
    def complete_task(self, task_id: str, completion_notes: Optional[str] = None, user: Optional[str] = "system") -> Optional[Task]:
        """Mark a task as complete with optional completion notes."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Update task status and timestamps
        task.status = TaskStatus.COMPLETED
        current_time = datetime.utcnow()
        
        # Store completion time in details
        task.details['completed_at'] = current_time.isoformat()
        
        # Calculate duration if we have a start time
        if 'started_at' in task.details:
            start_time = datetime.fromisoformat(task.details['started_at'])
            duration = current_time - start_time
            task.details['duration_seconds'] = duration.total_seconds()
            
        task.touch()  # Update the updated_at timestamp
        
        # Add completion notes to history if provided
        history_entry = "Task marked as completed"
        if completion_notes:
            history_entry += f": {completion_notes}"
            
        task._add_history_entry(history_entry, user=user)
        
        # Check if this completion unblocks other tasks
        dependent_tasks = self.get_dependent_tasks(task_id)
        if dependent_tasks:
            unblocked_tasks = []
            for dep_task in dependent_tasks:
                # Check if all dependencies of this dependent task are now complete
                if all(self.get_task(dep_id).status == TaskStatus.COMPLETED 
                       for dep_id in dep_task.dependencies 
                       if self.get_task(dep_id)):
                    unblocked_tasks.append(dep_task.id)
                    
            if unblocked_tasks:
                task._add_history_entry(
                    f"Completion of this task unblocked: {', '.join(unblocked_tasks)}",
                    user="system"
                )
                
        return task
        
    def pause_task(self, task_id: str, reason: Optional[str] = None, user: Optional[str] = "system") -> Optional[Task]:
        """Pause a task that is in progress."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        if task.status != TaskStatus.IN_PROGRESS:
            print(f"Warning: Cannot pause task {task_id} as it is not in progress.")
            return task
            
        # Update task status
        task.status = TaskStatus.PENDING
        current_time = datetime.utcnow()
        
        # Track time spent so far if we have a start time
        if 'started_at' in task.details:
            start_time = datetime.fromisoformat(task.details['started_at'])
            duration = current_time - start_time
            
            # Accumulate time spent
            if 'time_spent_seconds' in task.details:
                task.details['time_spent_seconds'] += duration.total_seconds()
            else:
                task.details['time_spent_seconds'] = duration.total_seconds()
                
            # Remove the started_at since we're pausing
            del task.details['started_at']
            
        task.touch()  # Update the updated_at timestamp
        
        # Add pause reason to history if provided
        history_entry = "Task paused"
        if reason:
            history_entry += f": {reason}"
            
        task._add_history_entry(history_entry, user=user)
        return task
        
    def block_task(self, task_id: str, blocker_description: str, user: Optional[str] = "system") -> Optional[Task]:
        """Mark a task as blocked by an external factor."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Update task status
        task.status = TaskStatus.BLOCKED
        
        # Track the blocker in details
        if 'blockers' not in task.details:
            task.details['blockers'] = []
            
        task.details['blockers'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'description': blocker_description
        })
        
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task blocked: {blocker_description}", user=user)
        return task
        
    def unblock_task(self, task_id: str, resolution: str, user: Optional[str] = "system") -> Optional[Task]:
        """Resolve a blocker and mark the task as pending."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        if task.status != TaskStatus.BLOCKED:
            print(f"Warning: Task {task_id} is not currently blocked.")
            return task
            
        # Update task status
        task.status = TaskStatus.PENDING
        
        # Track the resolution in details
        if 'blockers' in task.details and task.details['blockers']:
            latest_blocker = task.details['blockers'][-1]
            latest_blocker['resolved_at'] = datetime.utcnow().isoformat()
            latest_blocker['resolution'] = resolution
            
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task unblocked: {resolution}", user=user)
        return task

    # Task Analysis Methods
    def generate_implementation_guide(self, task_id: str) -> str:
        """Generate an implementation guide for a task.
        
        If an AI provider is available, it will be used to generate a detailed guide.
        Otherwise, a simple template-based guide will be generated.
        
        Args:
            task_id: ID of the task to generate a guide for
            
        Returns:
            Implementation guide as a string
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Get relevant project rules
        applicable_rules = []
        for rule_id, rule in self._project_rules.items():
            if rule.is_active:
                # Check if rule applies to this task's tags
                if not rule.applies_to_tags or any(tag in task.project_context_tags for tag in rule.applies_to_tags):
                    applicable_rules.append(rule)
        
        # If we have an AI provider, use it to generate a detailed guide
        if self.ai_provider:
            try:
                guide = self.ai_provider.generate_implementation_guide(task, applicable_rules)
                
                # Store the guide in the task for future reference
                task.implementation_guide = guide
                
                return guide
            except Exception as e:
                print(f"Error using AI provider for implementation guide: {str(e)}")
                # Fall back to template-based guide if AI fails
        
        # Template-based guide (fallback)
        # Load the implementation guide template
        try:
            from .prompts import load_prompt, render_template
            template = load_prompt("implementation_guide")
            
            # Format project rules for the template
            rules_text = ""
            if applicable_rules:
                rules_text = "Project Rules to consider:\n"
                for rule in applicable_rules:
                    rules_text += f"- {rule.name}: {rule.content}\n"
            
            # Render the template with task information
            guide = render_template(template, {
                "title": task.title,
                "description": task.description or "No description provided",
                "priority": task.priority.value,
                "project_rules": rules_text
            })
            
            # Store the guide in the task for future reference
            task.implementation_guide = guide
            
            return guide
        except Exception as e:
            print(f"Error generating implementation guide from template: {str(e)}")
            
            # Very simple fallback if template loading fails
            guide = f"# Implementation Guide for: {task.title}\n\n"
            guide += f"## Description\n{task.description or 'No description provided'}\n\n"
            guide += "## Steps\n1. Analyze requirements\n2. Design solution\n3. Implement code\n4. Test implementation\n5. Document changes\n\n"
            guide += "## Considerations\n- Follow project coding standards\n- Consider performance implications\n- Ensure proper error handling\n"
            
            # Store the guide in the task for future reference
            task.implementation_guide = guide
            
            return guide
    
    # Task Execution Tracking Methods
    
    def start_task_execution(self, task_id: str) -> Dict[str, Any]:
        """Start execution tracking for a task.
        
        Records the start time and initializes execution metrics.
        
        Args:
            task_id: ID of the task to start execution for
            
        Returns:
            Dictionary with execution context information
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Check if task can be executed (all dependencies satisfied)
        blocked_by = []
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.DONE:
                blocked_by.append(dep_id)
        
        if blocked_by:
            raise ValueError(f"Task {task_id} cannot be executed because it depends on incomplete tasks: {', '.join(blocked_by)}")
        
        # Initialize execution context
        execution_context = {
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "metrics": {
                "steps_completed": 0,
                "total_steps": 0,
                "time_spent": 0,
                "checkpoints": []
            },
            "logs": []
        }
        
        # Update task status and context
        task.status = TaskStatus.IN_PROGRESS
        task.execution_context = execution_context
        
        # Log the start of execution
        self._add_execution_log(task, "Execution started")
        
        return execution_context
    
    def update_execution_progress(self, task_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the execution progress for a task.
        
        Args:
            task_id: ID of the task to update progress for
            progress_data: Dictionary with progress information
                - step_name: Name of the current step
                - step_index: Index of the current step (optional)
                - total_steps: Total number of steps (optional)
                - status: Status message (optional)
                - metrics: Additional metrics (optional)
            
        Returns:
            Updated execution context
            
        Raises:
            ValueError: If the task is not found or not in progress
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        if task.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Task {task_id} is not in progress (current status: {task.status})")
        
        if not task.execution_context:
            # Initialize execution context if not already done
            task.execution_context = self.start_task_execution(task_id)
        
        # Update execution context with progress data
        context = task.execution_context
        
        # Update metrics
        if "step_index" in progress_data and "total_steps" in progress_data:
            context["metrics"]["steps_completed"] = progress_data["step_index"]
            context["metrics"]["total_steps"] = progress_data["total_steps"]
        
        # Add checkpoint
        if "step_name" in progress_data:
            checkpoint = {
                "time": datetime.now().isoformat(),
                "step_name": progress_data["step_name"],
                "status": progress_data.get("status", "in_progress")
            }
            context["metrics"]["checkpoints"].append(checkpoint)
        
        # Update additional metrics if provided
        if "metrics" in progress_data and isinstance(progress_data["metrics"], dict):
            for key, value in progress_data["metrics"].items():
                if key not in context["metrics"]:
                    context["metrics"][key] = value
        
        # Log the progress update
        log_message = f"Progress update: {progress_data.get('step_name', 'Unknown step')}"
        if "status" in progress_data:
            log_message += f" - {progress_data['status']}"
        self._add_execution_log(task, log_message)
        
        return context
    
    def complete_task_execution(self, task_id: str, result_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete the execution of a task.
        
        Args:
            task_id: ID of the task to complete
            result_data: Dictionary with result information (optional)
                - success: Whether the execution was successful (default: True)
                - output: Output data from the execution (optional)
                - metrics: Additional metrics (optional)
                - notes: Additional notes (optional)
            
        Returns:
            Final execution context
            
        Raises:
            ValueError: If the task is not found or not in progress
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        if task.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Task {task_id} is not in progress (current status: {task.status})")
        
        if not task.execution_context:
            raise ValueError(f"Task {task_id} has no execution context")
        
        # Process result data
        result_data = result_data or {}
        success = result_data.get("success", True)
        
        # Update execution context
        context = task.execution_context
        context["end_time"] = datetime.now().isoformat()
        context["status"] = "completed" if success else "failed"
        
        # Calculate time spent
        if "start_time" in context:
            start_time = datetime.fromisoformat(context["start_time"])
            end_time = datetime.fromisoformat(context["end_time"])
            time_spent = (end_time - start_time).total_seconds()
            context["metrics"]["time_spent"] = time_spent
        
        # Update additional metrics if provided
        if "metrics" in result_data and isinstance(result_data["metrics"], dict):
            for key, value in result_data["metrics"].items():
                context["metrics"][key] = value
        
        # Add output data if provided
        if "output" in result_data:
            context["output"] = result_data["output"]
        
        # Update task status
        task.status = TaskStatus.DONE if success else TaskStatus.FAILED
        
        # Add notes if provided
        if "notes" in result_data:
            if task.notes:
                task.notes += f"\n\n{result_data['notes']}"
            else:
                task.notes = result_data["notes"]
        
        # Log the completion
        status_str = "successfully" if success else "with failures"
        self._add_execution_log(task, f"Execution completed {status_str}")
        
        return context
    
    def get_execution_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get execution metrics for a task.
        
        Args:
            task_id: ID of the task to get metrics for
            
        Returns:
            Dictionary with execution metrics
            
        Raises:
            ValueError: If the task is not found or has no execution context
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        if not task.execution_context:
            raise ValueError(f"Task {task_id} has no execution context")
        
        return task.execution_context["metrics"]
    
    def get_execution_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """Get execution logs for a task.
        
        Args:
            task_id: ID of the task to get logs for
            
        Returns:
            List of log entries
            
        Raises:
            ValueError: If the task is not found or has no execution context
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        if not task.execution_context or "logs" not in task.execution_context:
            return []
        
        return task.execution_context["logs"]
    
    def _add_execution_log(self, task: Task, message: str, level: str = "info") -> None:
        """Add a log entry to the task execution context.
        
        Args:
            task: Task to add log to
            message: Log message
            level: Log level (info, warning, error)
        """
        if not task.execution_context:
            task.execution_context = {
                "start_time": datetime.now().isoformat(),
                "status": "in_progress",
                "metrics": {},
                "logs": []
            }
        
        if "logs" not in task.execution_context:
            task.execution_context["logs"] = []
        
        log_entry = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        task.execution_context["logs"].append(log_entry)
    
    # Task Reporting Methods
    
    def generate_execution_report(self, task_ids: List[str] = None) -> Dict[str, Any]:
        """Generate a report on task execution metrics.
        
        Args:
            task_ids: List of task IDs to include in the report (default: all tasks)
            
        Returns:
            Dictionary with report data
        """
        # Get tasks to include in the report
        if task_ids:
            tasks = [task for task in self._tasks.values() if task.id in task_ids]
        else:
            tasks = list(self._tasks.values())
        
        # Initialize report data
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "status_summary": {
                "pending": 0,
                "in_progress": 0,
                "done": 0,
                "failed": 0,
                "blocked": 0
            },
            "execution_metrics": {
                "total_execution_time": 0,
                "average_execution_time": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            },
            "complexity_summary": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "average_score": 0
            },
            "tasks_by_execution_time": [],
            "recent_executions": []
        }
        
        # Collect data from tasks
        total_complexity = 0
        tasks_with_complexity = 0
        total_execution_time = 0
        tasks_with_execution_time = 0
        
        for task in tasks:
            # Update status summary
            if task.status == TaskStatus.PENDING:
                report["status_summary"]["pending"] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                report["status_summary"]["in_progress"] += 1
            elif task.status == TaskStatus.DONE:
                report["status_summary"]["done"] += 1
                report["execution_metrics"]["completed_tasks"] += 1
            elif task.status == TaskStatus.FAILED:
                report["status_summary"]["failed"] += 1
                report["execution_metrics"]["failed_tasks"] += 1
            
            # Check if task is blocked by dependencies
            blocked = False
            for dep_id in task.dependencies:
                dep_task = self.get_task(dep_id)
                if dep_task and dep_task.status != TaskStatus.DONE:
                    blocked = True
                    break
            
            if blocked:
                report["status_summary"]["blocked"] += 1
            
            # Update complexity summary if available
            if task.complexity_score is not None:
                total_complexity += task.complexity_score
                tasks_with_complexity += 1
                
                if task.complexity_score < 3:
                    report["complexity_summary"]["low"] += 1
                elif task.complexity_score < 7:
                    report["complexity_summary"]["medium"] += 1
                else:
                    report["complexity_summary"]["high"] += 1
            
            # Update execution metrics if available
            if task.execution_context and "metrics" in task.execution_context:
                metrics = task.execution_context["metrics"]
                if "time_spent" in metrics and metrics["time_spent"] > 0:
                    execution_time = metrics["time_spent"]
                    total_execution_time += execution_time
                    tasks_with_execution_time += 1
                    
                    # Add to tasks by execution time
                    report["tasks_by_execution_time"].append({
                        "id": task.id,
                        "title": task.title,
                        "execution_time": execution_time
                    })
            
            # Add to recent executions if completed recently
            if task.execution_context and "end_time" in task.execution_context:
                report["recent_executions"].append({
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "end_time": task.execution_context["end_time"],
                    "execution_time": task.execution_context["metrics"].get("time_spent", 0) if "metrics" in task.execution_context else 0
                })
        
        # Calculate averages and sort lists
        if tasks_with_complexity > 0:
            report["complexity_summary"]["average_score"] = total_complexity / tasks_with_complexity
        
        if tasks_with_execution_time > 0:
            report["execution_metrics"]["total_execution_time"] = total_execution_time
            report["execution_metrics"]["average_execution_time"] = total_execution_time / tasks_with_execution_time
        
        # Sort tasks by execution time (descending)
        report["tasks_by_execution_time"].sort(key=lambda x: x["execution_time"], reverse=True)
        
        # Sort recent executions by end time (most recent first)
        report["recent_executions"].sort(key=lambda x: x["end_time"], reverse=True)
        
        # Limit lists to top 10
        report["tasks_by_execution_time"] = report["tasks_by_execution_time"][:10]
        report["recent_executions"] = report["recent_executions"][:10]
        
        return report
    
    def generate_task_timeline(self, task_id: str) -> List[Dict[str, Any]]:
        """Generate a timeline of task execution events.
        
        Args:
            task_id: ID of the task to generate timeline for
            
        Returns:
            List of timeline events
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        timeline = []
        
        # Add task creation event
        timeline.append({
            "time": task.created_at.isoformat() if isinstance(task.created_at, datetime) else task.created_at,
            "event": "created",
            "description": f"Task '{task.title}' was created"
        })
        
        # Add status change events from history
        if task.history:
            for entry in task.history:
                if "status" in entry:
                    timeline.append({
                        "time": entry.get("timestamp", ""),
                        "event": "status_change",
                        "description": f"Status changed to {entry['status']}",
                        "details": entry
                    })
        
        # Add execution events if available
        if task.execution_context:
            # Add execution start event
            if "start_time" in task.execution_context:
                timeline.append({
                    "time": task.execution_context["start_time"],
                    "event": "execution_started",
                    "description": "Task execution started"
                })
            
            # Add checkpoint events
            if "metrics" in task.execution_context and "checkpoints" in task.execution_context["metrics"]:
                for checkpoint in task.execution_context["metrics"]["checkpoints"]:
                    timeline.append({
                        "time": checkpoint["time"],
                        "event": "checkpoint",
                        "description": f"Checkpoint: {checkpoint['step_name']}",
                        "details": checkpoint
                    })
            
            # Add execution end event
            if "end_time" in task.execution_context:
                timeline.append({
                    "time": task.execution_context["end_time"],
                    "event": "execution_completed",
                    "description": f"Task execution completed with status: {task.execution_context['status']}"
                })
        
        # Sort timeline by time
        timeline.sort(key=lambda x: x["time"])
        
        return timeline
    
    def generate_dependency_graph(self, task_ids: List[str] = None) -> Dict[str, Any]:
        """Generate a dependency graph for visualization.
        
        Args:
            task_ids: List of task IDs to include in the graph (default: all tasks)
            
        Returns:
            Dictionary with graph data in a format suitable for visualization
        """
        # Get tasks to include in the graph
        if task_ids:
            tasks = [task for task in self._tasks.values() if task.id in task_ids]
        else:
            tasks = list(self._tasks.values())
        
        # Initialize graph data
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes (tasks)
        for task in tasks:
            node = {
                "id": task.id,
                "label": task.title,
                "status": task.status.value,
                "complexity": task.complexity_score if task.complexity_score is not None else 0
            }
            graph["nodes"].append(node)
        
        # Add edges (dependencies)
        for task in tasks:
            for dep_id in task.dependencies:
                # Only add edge if both tasks are in the graph
                if dep_id in [node["id"] for node in graph["nodes"]]:
                    edge = {
                        "source": dep_id,
                        "target": task.id
                    }
                    graph["edges"].append(edge)
        
        return graph
    
    def export_execution_data(self, format_type: str = "json", task_ids: List[str] = None, file_path: str = None) -> Union[str, Dict[str, Any]]:
        """Export task execution data in a format suitable for external analysis.
        
        Args:
            format_type: Format to export data in (json, csv)
            task_ids: List of task IDs to include (default: all tasks)
            file_path: Path to save the exported data to (optional)
            
        Returns:
            Exported data as string or dictionary
            
        Raises:
            ValueError: If an invalid format type is specified
        """
        # Get tasks to include in the export
        if task_ids:
            tasks = [task for task in self._tasks.values() if task.id in task_ids]
        else:
            tasks = list(self._tasks.values())
        
        # Filter tasks with execution data
        tasks_with_execution = [task for task in tasks if task.execution_context]
        
        if not tasks_with_execution:
            if format_type == "json":
                result = {"tasks": []}
                if file_path:
                    with open(file_path, "w") as f:
                        json.dump(result, f, indent=2)
                return result
            elif format_type == "csv":
                result = "id,title,status,start_time,end_time,execution_time,success\n"
                if file_path:
                    with open(file_path, "w") as f:
                        f.write(result)
                return result
            else:
                raise ValueError(f"Invalid format type: {format_type}")
        
        # Prepare data for export
        if format_type == "json":
            # Prepare JSON data
            export_data = {
                "tasks": [],
                "summary": {
                    "total_tasks": len(tasks_with_execution),
                    "total_execution_time": 0,
                    "average_execution_time": 0,
                    "success_rate": 0
                }
            }
            
            total_execution_time = 0
            successful_tasks = 0
            
            for task in tasks_with_execution:
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat() if isinstance(task.created_at, datetime) else task.created_at,
                    "dependencies": task.dependencies,
                    "execution": {
                        "start_time": task.execution_context.get("start_time", ""),
                        "end_time": task.execution_context.get("end_time", ""),
                        "status": task.execution_context.get("status", "")
                    }
                }
                
                # Add metrics if available
                if "metrics" in task.execution_context:
                    task_data["execution"]["metrics"] = task.execution_context["metrics"]
                    
                    # Update summary metrics
                    if "time_spent" in task.execution_context["metrics"]:
                        execution_time = task.execution_context["metrics"]["time_spent"]
                        task_data["execution"]["execution_time"] = execution_time
                        total_execution_time += execution_time
                
                # Add success status
                is_successful = (task.execution_context.get("status") == "completed" or task.status == TaskStatus.DONE)
                task_data["execution"]["success"] = is_successful
                if is_successful:
                    successful_tasks += 1
                
                export_data["tasks"].append(task_data)
            
            # Update summary metrics
            if tasks_with_execution:
                export_data["summary"]["total_execution_time"] = total_execution_time
                export_data["summary"]["average_execution_time"] = total_execution_time / len(tasks_with_execution)
                export_data["summary"]["success_rate"] = (successful_tasks / len(tasks_with_execution)) * 100
            
            # Save to file if specified
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(export_data, f, indent=2)
            
            return export_data
        
        elif format_type == "csv":
            # Prepare CSV data
            header = "id,title,status,start_time,end_time,execution_time,success\n"
            rows = []
            
            for task in tasks_with_execution:
                # Get execution time if available
                execution_time = ""
                if "metrics" in task.execution_context and "time_spent" in task.execution_context["metrics"]:
                    execution_time = str(task.execution_context["metrics"]["time_spent"])
                
                # Get success status
                is_successful = (task.execution_context.get("status") == "completed" or task.status == TaskStatus.DONE)
                success = "true" if is_successful else "false"
                
                # Create CSV row
                row = [
                    task.id,
                    f"\"{task.title.replace('"', '""')}\"",  # Escape quotes in title
                    task.status.value,
                    task.execution_context.get("start_time", ""),
                    task.execution_context.get("end_time", ""),
                    execution_time,
                    success
                ]
                
                rows.append(",".join(row))
            
            # Combine header and rows
            csv_data = header + "\n".join(rows)
            
            # Save to file if specified
            if file_path:
                with open(file_path, "w") as f:
                    f.write(csv_data)
            
            return csv_data
        
        else:
            raise ValueError(f"Invalid format type: {format_type}")
    
    def track_execution_performance(self, time_period: str = "week", task_ids: List[str] = None) -> Dict[str, Any]:
        """Track task execution performance over time.
        
        Args:
            time_period: Time period to group by (day, week, month)
            task_ids: List of task IDs to include (default: all tasks)
            
        Returns:
            Dictionary with performance data over time
        """
        # Get tasks to include in the analysis
        if task_ids:
            tasks = [task for task in self._tasks.values() if task.id in task_ids]
        else:
            tasks = list(self._tasks.values())
        
        # Filter tasks with execution data
        tasks_with_execution = [task for task in tasks if task.execution_context and 
                               "start_time" in task.execution_context and 
                               "end_time" in task.execution_context]
        
        if not tasks_with_execution:
            return {
                "time_periods": [],
                "metrics": {
                    "tasks_completed": [],
                    "average_execution_time": [],
                    "success_rate": []
                }
            }
        
        # Determine date range
        start_dates = [datetime.fromisoformat(task.execution_context["start_time"]) 
                      for task in tasks_with_execution]
        end_dates = [datetime.fromisoformat(task.execution_context["end_time"]) 
                    for task in tasks_with_execution]
        
        min_date = min(start_dates)
        max_date = max(end_dates)
        
        # Generate time periods
        time_periods = []
        current_date = min_date
        
        if time_period == "day":
            delta = timedelta(days=1)
            format_str = "%Y-%m-%d"
        elif time_period == "week":
            delta = timedelta(weeks=1)
            format_str = "%Y-W%W"
        else:  # month
            format_str = "%Y-%m"
            
        while current_date <= max_date:
            if time_period == "month":
                # For months, we need to handle the increment differently
                next_month = current_date.month + 1
                next_year = current_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_date = current_date.replace(year=next_year, month=next_month, day=1)
            else:
                next_date = current_date + delta
            
            period_label = current_date.strftime(format_str)
            time_periods.append({
                "label": period_label,
                "start": current_date.isoformat(),
                "end": next_date.isoformat()
            })
            
            current_date = next_date
        
        # Initialize metrics
        metrics = {
            "tasks_completed": [0] * len(time_periods),
            "average_execution_time": [0] * len(time_periods),
            "success_rate": [0] * len(time_periods),
            "total_execution_time": [0] * len(time_periods),
            "tasks_started": [0] * len(time_periods),
            "tasks_succeeded": [0] * len(time_periods),
            "tasks_failed": [0] * len(time_periods)
        }
        
        # Collect metrics for each time period
        for i, period in enumerate(time_periods):
            period_start = datetime.fromisoformat(period["start"])
            period_end = datetime.fromisoformat(period["end"])
            
            # Tasks started in this period
            started_in_period = [task for task in tasks_with_execution 
                               if period_start <= datetime.fromisoformat(task.execution_context["start_time"]) < period_end]
            metrics["tasks_started"][i] = len(started_in_period)
            
            # Tasks completed in this period
            completed_in_period = [task for task in tasks_with_execution 
                                 if period_start <= datetime.fromisoformat(task.execution_context["end_time"]) < period_end]
            metrics["tasks_completed"][i] = len(completed_in_period)
            
            # Success rate
            succeeded = [task for task in completed_in_period 
                        if task.execution_context.get("status") == "completed" or task.status == TaskStatus.DONE]
            metrics["tasks_succeeded"][i] = len(succeeded)
            metrics["tasks_failed"][i] = len(completed_in_period) - len(succeeded)
            
            if completed_in_period:
                metrics["success_rate"][i] = len(succeeded) / len(completed_in_period) * 100
            
            # Execution time
            execution_times = []
            for task in completed_in_period:
                if "metrics" in task.execution_context and "time_spent" in task.execution_context["metrics"]:
                    execution_times.append(task.execution_context["metrics"]["time_spent"])
            
            if execution_times:
                metrics["total_execution_time"][i] = sum(execution_times)
                metrics["average_execution_time"][i] = sum(execution_times) / len(execution_times)
        
        # Prepare result
        result = {
            "time_periods": [period["label"] for period in time_periods],
            "metrics": metrics
        }
        
        return result
    
    def generate_dependency_graph(self, task_ids: List[str] = None) -> Dict[str, Any]:
        """Generate a dependency graph for visualization.
        
        Args:
            task_ids: List of task IDs to include in the graph (default: all tasks)
            
        Returns:
            Dictionary with graph data in a format suitable for visualization
        """
        # Get tasks to include in the graph
        if task_ids:
            tasks = [task for task in self._tasks.values() if task.id in task_ids]
        else:
            tasks = list(self._tasks.values())
        
        # Initialize graph data
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes (tasks)
        for task in tasks:
            node = {
                "id": task.id,
                "label": task.title,
                "status": task.status.value,
                "complexity": task.complexity_score if task.complexity_score is not None else 0
            }
            graph["nodes"].append(node)
        
        # Add edges (dependencies)
        for task in tasks:
            for dep_id in task.dependencies:
                # Only add edge if both tasks are in the graph
                if dep_id in [node["id"] for node in graph["nodes"]]:
                    edge = {
                        "source": dep_id,
                        "target": task.id
                    }
                    graph["edges"].append(edge)
        
        return graph
    
    def _add_execution_log(self, task: Task, message: str, level: str = "info") -> None:
        """Add a log entry to the task execution context.
        
        Args:
            task: Task to add log to
            message: Log message
            level: Log level (info, warning, error)
        """
        if not task.execution_context:
            task.execution_context = {
                "start_time": datetime.now().isoformat(),
                "status": "in_progress",
                "metrics": {},
                "logs": []
            }
        
        if "logs" not in task.execution_context:
            task.execution_context["logs"] = []
        
        log_entry = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        task.execution_context["logs"].append(log_entry)
    
    # Dependency Management Methods
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate all task dependencies.
        
        Checks for circular dependencies, missing dependencies, and other issues.
        
        Returns:
            Dictionary with validation results
        """
        return DependencyManager.validate_dependencies(self._tasks)
    
    def fix_dependencies(self) -> Dict[str, Any]:
        """Fix invalid dependencies in tasks.
        
        Removes circular dependencies, self-dependencies, and missing dependencies.
        
        Returns:
            Dictionary with fix report
        """
        updated_tasks, fix_report = DependencyManager.fix_dependencies(self._tasks)
        
        # Update tasks with fixed dependencies if changes were made
        if fix_report["changes_made"]:
            self._tasks = updated_tasks
        
        return fix_report
    
    def get_dependency_chain(self, task_id: str) -> Dict[str, Any]:
        """Get the full dependency chain for a task, organized by levels.
        
        Args:
            task_id: ID of the task to analyze
            
        Returns:
            Dictionary with dependency chain information
        """
        return DependencyManager.get_dependency_chain(self._tasks, task_id)
    
    def find_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Find tasks that are blocked by incomplete dependencies.
        
        Returns:
            List of blocked tasks with their blockers
        """
        return DependencyManager.find_blocked_tasks(self._tasks)
    
    def is_circular_dependency(self, task_id: str, dependency_id: str) -> Tuple[bool, List[str]]:
        """Check if adding a dependency would create a circular dependency.
        
        Args:
            task_id: ID of task that would depend on dependency_id
            dependency_id: ID of task that would be a dependency
            
        Returns:
            Tuple of (is_circular, dependency_chain)
        """
        return DependencyManager.is_circular_dependency(self._tasks, task_id, dependency_id)
    
    # Task Prioritization Methods
    
    def find_next_task(self) -> Optional[Dict[str, Any]]:
        """Find the next task to work on.
        
        Prioritizes tasks based on dependencies, status, and priority.
        
        Returns:
            Dictionary with next task information or None if no eligible tasks
        """
        return TaskPrioritizer.find_next_task(self._tasks)
    
    def find_next_task_with_subtasks(self) -> Optional[Dict[str, Any]]:
        """Find the next task to work on, considering both top-level tasks and subtasks.
        
        Prioritizes subtasks of in-progress parent tasks, then other eligible tasks.
        
        Returns:
            Dictionary with next task information or None if no eligible tasks
        """
        return TaskPrioritizer.find_next_task_with_subtasks(self._tasks)
    
    def get_task_queue(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get a prioritized queue of tasks to work on.
        
        Args:
            limit: Maximum number of tasks to include in the queue
            
        Returns:
            List of prioritized tasks
        """
        return TaskPrioritizer.get_task_queue(self._tasks, limit)
    
    def estimate_completion_time(self) -> Dict[str, Any]:
        """Estimate completion time for remaining tasks based on historical data.
        
        Returns:
            Dictionary with completion time estimates
        """
        return TaskPrioritizer.estimate_completion_time(self._tasks)
    
    # Task Reflection Methods
    
    def reflect_on_task(self, task_id: str) -> Dict[str, Any]:
        """Reflect on a task and generate insights.
        
        Args:
            task_id: ID of the task to reflect on
            
        Returns:
            Dictionary with reflection results
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        reflection = self.task_reflector.reflect_on_task(task)
        
        # Store reflection in task analysis_results if available
        if hasattr(task, 'analysis_results') and reflection:
            if task.analysis_results:
                # Append new reflection
                if isinstance(task.analysis_results, dict):
                    task.analysis_results["reflection"] = reflection
                elif isinstance(task.analysis_results, str):
                    try:
                        # Try to parse existing analysis results as JSON
                        analysis_dict = json.loads(task.analysis_results)
                        analysis_dict["reflection"] = reflection
                        task.analysis_results = json.dumps(analysis_dict)
                    except json.JSONDecodeError:
                        # If not valid JSON, append as new section
                        task.analysis_results += f"\n\n## Task Reflection\n{json.dumps(reflection, indent=2)}"
            else:
                # Initialize analysis results with reflection
                task.analysis_results = {"reflection": reflection}
        
        return reflection
    
    def reflect_on_project(self) -> Dict[str, Any]:
        """Generate reflection and insights for the entire project.
        
        Returns:
            Dictionary with project reflection results
        """
        return self.task_reflector.reflect_on_project(self.tasks)
    
    # Task Splitting Methods
    
    def split_task(self, task_id: str, strategy: str = "auto", num_subtasks: int = None) -> Dict[str, Any]:
        """Split a task into subtasks using the specified strategy.
        
        Args:
            task_id: ID of the task to split
            strategy: Decomposition strategy to use ('functional', 'technical', 'development_stage', 'risk_based', or 'auto')
            num_subtasks: Target number of subtasks (optional)
            
        Returns:
            Dictionary with splitting results
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Split the task
        subtasks = self.task_splitter.split_task(task, strategy, num_subtasks)
        
        # Optimize subtask dependencies
        optimized_subtasks = self.task_splitter.optimize_subtask_dependencies(subtasks)
        
        # Add subtasks to the task manager
        for subtask in optimized_subtasks:
            self.tasks[subtask.id] = subtask
        
        # Validate subtask coverage
        coverage_validation = self.task_splitter.validate_subtask_coverage(task, optimized_subtasks)
        
        # Update parent task with subtasks
        if not hasattr(task, 'subtasks'):
            task.subtasks = []
        task.subtasks = [subtask.id for subtask in optimized_subtasks]
        
        return {
            "success": True,
            "task_id": task_id,
            "strategy": strategy,
            "subtasks": [{
                "id": subtask.id,
                "title": subtask.title,
                "dependencies": subtask.dependencies
            } for subtask in optimized_subtasks],
            "coverage_validation": coverage_validation
        }
    
    # Task Verification Methods
    
    def verify_task(self, task_id: str, artifacts: Dict[str, Any] = None) -> Dict[str, Any]:
        """Verify that a task meets its verification criteria.
        
        Args:
            task_id: ID of the task to verify
            artifacts: Optional dictionary of artifacts related to the task (e.g., code, test results)
            
        Returns:
            Dictionary with verification results
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Verify the task
        verification_result = self.task_verifier.verify_task(task, artifacts)
        
        # Generate verification report
        verification_report = self.task_verifier.generate_verification_report(task, verification_result)
        
        # If task failed verification, suggest improvements
        if not verification_result.get("verified", False):
            improvement_suggestions = self.task_verifier.suggest_improvements(task, verification_result)
            verification_result["improvement_suggestions"] = improvement_suggestions
        
        # Store verification result in task execution context
        if not hasattr(task, "execution_context") or not task.execution_context:
            task.execution_context = {}
        
        task.execution_context["verification"] = {
            "result": verification_result,
            "report": verification_report,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "task_id": task_id,
            "verification_result": verification_result,
            "verification_report": verification_report
        }
    
    # Task Planning Methods
    
    def generate_execution_plan(self, task_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a detailed execution plan for a task.
        
        Args:
            task_id: ID of the task to generate a plan for
            context: Optional context information (e.g., project constraints, team skills)
            
        Returns:
            Dictionary containing the execution plan
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Generate the execution plan
        execution_plan = self.task_planner.generate_execution_plan(task, context)
        
        # Store execution plan in task execution context
        if not hasattr(task, "execution_context") or not task.execution_context:
            task.execution_context = {}
        
        task.execution_context["execution_plan"] = {
            "plan": execution_plan,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "task_id": task_id,
            "execution_plan": execution_plan
        }
    
    def estimate_completion_date(self, task_id: str, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Estimate the completion date for a task based on its execution plan.
        
        Args:
            task_id: ID of the task to estimate
            start_date: Optional start date (defaults to current date/time)
            
        Returns:
            Dictionary with estimated dates for each step and overall completion
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Check if task has an execution plan
        if not hasattr(task, "execution_context") or not task.execution_context or "execution_plan" not in task.execution_context:
            # Generate an execution plan first
            execution_plan_result = self.generate_execution_plan(task_id)
            if "error" in execution_plan_result:
                return execution_plan_result
            execution_plan = execution_plan_result["execution_plan"]
        else:
            execution_plan = task.execution_context["execution_plan"]["plan"]
        
        # Estimate completion date
        estimation = self.task_planner.estimate_completion_date(task, execution_plan, start_date)
        
        # Store estimation in task execution context
        if not hasattr(task, "execution_context") or not task.execution_context:
            task.execution_context = {}
        
        task.execution_context["completion_estimation"] = {
            "estimation": estimation,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "task_id": task_id,
            "estimation": estimation
        }
    
    def generate_gantt_chart(self, task_id: str, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a Gantt chart for the task execution plan.
        
        Args:
            task_id: ID of the task to generate a chart for
            start_date: Optional start date (defaults to current date/time)
            
        Returns:
            Dictionary with the Gantt chart in Mermaid format
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Check if task has an execution plan
        if not hasattr(task, "execution_context") or not task.execution_context or "execution_plan" not in task.execution_context:
            # Generate an execution plan first
            execution_plan_result = self.generate_execution_plan(task_id)
            if "error" in execution_plan_result:
                return execution_plan_result
            execution_plan = execution_plan_result["execution_plan"]
        else:
            execution_plan = task.execution_context["execution_plan"]["plan"]
        
        # Generate Gantt chart
        gantt_chart = self.task_planner.generate_gantt_chart(task, execution_plan, start_date)
        
        return {
            "success": True,
            "task_id": task_id,
            "gantt_chart": gantt_chart
        }
    
    # Task Execution Methods
    
    def prepare_task_execution(self, task_id: str) -> Dict[str, Any]:
        """Prepare for task execution by gathering all necessary information.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            Dictionary with execution preparation information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        # Get related tasks (dependencies)
        related_tasks = {}
        if task.dependencies:
            for dep_id in task.dependencies:
                dep_task = self.get_task(dep_id)
                if dep_task:
                    related_tasks[dep_id] = dep_task
        
        # Prepare for execution
        preparation_result = self.task_executor.prepare_execution(task, related_tasks)
        
        # Save task changes
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "task_id": task_id,
            "preparation": preparation_result
        }
    
    def log_execution_step(self, task_id: str, step_name: str, status: str, 
                         details: Optional[str] = None) -> Dict[str, Any]:
        """Log an execution step for a task.
        
        Args:
            task_id: ID of the task being executed
            step_name: Name of the execution step
            status: Status of the step ('started', 'completed', 'failed')
            details: Optional details about the step
            
        Returns:
            Dictionary with the logged step information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        try:
            step_log = self.task_executor.log_execution_step(task, step_name, status, details)
            
            # Save task changes
            self.tasks[task_id] = task
            
            return {
                "success": True,
                "task_id": task_id,
                "step_log": step_log
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def complete_task_execution(self, task_id: str, success: bool, 
                             completion_notes: Optional[str] = None) -> Dict[str, Any]:
        """Complete the execution of a task.
        
        Args:
            task_id: ID of the task being executed
            success: Whether the execution was successful
            completion_notes: Optional notes about the completion
            
        Returns:
            Dictionary with execution summary
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        try:
            execution_summary = self.task_executor.complete_execution(task, success, completion_notes)
            
            # Save task changes
            self.tasks[task_id] = task
            
            return {
                "success": True,
                "task_id": task_id,
                "execution_summary": execution_summary
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def get_task_execution_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current execution status of a task.
        
        Args:
            task_id: ID of the task to get status for
            
        Returns:
            Dictionary with execution status information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        execution_status = self.task_executor.get_execution_status(task)
        
        return {
            "success": True,
            "task_id": task_id,
            "execution_status": execution_status
        }
    
    def assess_task_complexity(self, task_id: str) -> Dict[str, Any]:
        """Assess the complexity of a task.
        
        Args:
            task_id: ID of the task to assess
            
        Returns:
            Dictionary with complexity assessment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        complexity_assessment = self.task_executor.assess_complexity(task)
        
        return {
            "success": True,
            "task_id": task_id,
            "complexity": {
                "level": complexity_assessment.level,
                "metrics": complexity_assessment.metrics,
                "recommendations": complexity_assessment.recommendations
            }
        }
    
    # Task Analytics Methods
    
    def get_completion_rate(self, timeframe: str = "all") -> Dict[str, Any]:
        """Get task completion rate metrics.
        
        Args:
            timeframe: Time frame for analysis (day, week, month, quarter, year, all)
            
        Returns:
            Dictionary with completion rate metrics
        """
        try:
            time_frame_enum = AnalyticsTimeFrame(timeframe)
            result = self.task_analytics.calculate_completion_rate(list(self.tasks.values()), time_frame_enum)
            return {
                "success": True,
                "completion_rate": result
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def get_duration_metrics(self) -> Dict[str, Any]:
        """Get task duration metrics.
        
        Returns:
            Dictionary with duration metrics
        """
        result = self.task_analytics.calculate_average_duration(list(self.tasks.values()))
        return {
            "success": True,
            "duration_metrics": result
        }
    
    def get_task_distribution(self) -> Dict[str, Any]:
        """Get task distribution metrics.
        
        Returns:
            Dictionary with task distribution metrics
        """
        result = self.task_analytics.analyze_task_distribution(list(self.tasks.values()))
        return {
            "success": True,
            "distribution": result
        }
    
    def get_dependency_metrics(self) -> Dict[str, Any]:
        """Get task dependency metrics.
        
        Returns:
            Dictionary with dependency metrics
        """
        result = self.task_analytics.calculate_dependency_metrics(list(self.tasks.values()))
        return {
            "success": True,
            "dependency_metrics": result
        }
    
    def get_execution_efficiency(self) -> Dict[str, Any]:
        """Get task execution efficiency metrics.
        
        Returns:
            Dictionary with execution efficiency metrics
        """
        result = self.task_analytics.analyze_execution_efficiency(list(self.tasks.values()))
        return {
            "success": True,
            "execution_efficiency": result
        }
    
    def generate_trend_report(self, metric_type: str, timeframes: List[str]) -> Dict[str, Any]:
        """Generate a trend report for a specific metric.
        
        Args:
            metric_type: Type of metric to analyze
            timeframes: List of timeframes to include
            
        Returns:
            Dictionary with trend data
        """
        try:
            # Convert string parameters to enums
            metric_enum = AnalyticsMetricType(metric_type)
            timeframe_enums = [AnalyticsTimeFrame(tf) for tf in timeframes]
            
            result = self.task_analytics.generate_trend_report(
                list(self.tasks.values()),
                metric_enum,
                timeframe_enums
            )
            
            return {
                "success": True,
                "trend_report": result
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def export_analytics_report(self, format: str = "json", output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate and export a comprehensive analytics report.
        
        Args:
            format: Output format ('json' or 'csv')
            output_path: Optional path to save the report
            
        Returns:
            Dictionary with the report or path to the saved report
        """
        try:
            result = self.task_analytics.export_analytics_report(
                list(self.tasks.values()),
                format,
                output_path
            )
            
            return {
                "success": True,
                "report": result if not output_path else "Report saved to " + output_path
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def generate_visualization_data(self, visualization_type: str) -> Dict[str, Any]:
        """Generate data for visualizations.
        
        Args:
            visualization_type: Type of visualization ('gantt', 'burndown', 'pie', 'bar')
            
        Returns:
            Dictionary with visualization data
        """
        try:
            result = self.task_analytics.generate_visualization_data(
                list(self.tasks.values()),
                visualization_type
            )
            
            return {
                "success": True,
                "visualization_data": result
            }
        except ValueError as e:
            return {"error": str(e)}
    
    # Task Collaboration Methods
    
    def assign_task(self, task_id: str, user_id: str, role: str = "assignee") -> Dict[str, Any]:
        """Assign a task to a user with a specific role.
        
        Args:
            task_id: ID of the task to assign
            user_id: ID of the user to assign the task to
            role: Role to assign to the user (owner, assignee, reviewer, observer)
            
        Returns:
            Dictionary with assignment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        try:
            # Convert string role to enum
            role_enum = CollaborationRole(role)
            
            result = self.task_collaboration.assign_task(task, user_id, role_enum)
            
            # Save task changes
            self.tasks[task_id] = task
            
            return {
                "success": True,
                "assignment": result
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def unassign_task(self, task_id: str, user_id: str) -> Dict[str, Any]:
        """Remove a user's assignment from a task.
        
        Args:
            task_id: ID of the task to unassign
            user_id: ID of the user to unassign
            
        Returns:
            Dictionary with unassignment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.unassign_task(task, user_id)
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Save task changes
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "unassignment": result
        }
    
    def get_task_assignments(self, task_id: str) -> Dict[str, Any]:
        """Get all assignments for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary with assignment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.get_task_assignments(task_id)
        
        return {
            "success": True,
            "assignments": result["assignments"]
        }
    
    def add_comment(self, task_id: str, user_id: str, content: str, 
                  parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Add a comment to a task.
        
        Args:
            task_id: ID of the task to comment on
            user_id: ID of the user adding the comment
            content: Content of the comment
            parent_id: Optional ID of the parent comment if this is a reply
            
        Returns:
            Dictionary with comment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.add_comment(task, user_id, content, parent_id)
        
        # Save task changes
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "comment": result["comment"]
        }
    
    def edit_comment(self, task_id: str, comment_id: str, 
                   user_id: str, new_content: str) -> Dict[str, Any]:
        """Edit an existing comment.
        
        Args:
            task_id: ID of the task containing the comment
            comment_id: ID of the comment to edit
            user_id: ID of the user editing the comment
            new_content: New content for the comment
            
        Returns:
            Dictionary with edited comment information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.edit_comment(task, comment_id, user_id, new_content)
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Save task changes
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "edited_comment": result
        }
    
    def get_comments(self, task_id: str, include_replies: bool = True) -> Dict[str, Any]:
        """Get all comments for a task.
        
        Args:
            task_id: ID of the task
            include_replies: Whether to include reply comments
            
        Returns:
            Dictionary with comments
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.get_comments(task_id, include_replies)
        
        return {
            "success": True,
            "comments": result["comments"]
        }
    
    def add_review(self, task_id: str, user_id: str, status: str, 
                 comments: Optional[str] = None) -> Dict[str, Any]:
        """Add a review to a task.
        
        Args:
            task_id: ID of the task to review
            user_id: ID of the reviewer
            status: Review status (approved, rejected, changes_requested)
            comments: Optional review comments
            
        Returns:
            Dictionary with review information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        result = self.task_collaboration.add_review(task, user_id, status, comments)
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Save task changes
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "review": result["review"]
        }
    
    def get_activity_feed(self, task_id: Optional[str] = None, 
                        user_id: Optional[str] = None,
                        limit: int = 20) -> Dict[str, Any]:
        """Get activity feed for a task or user.
        
        Args:
            task_id: Optional ID of the task to get events for
            user_id: Optional ID of the user to get events for
            limit: Maximum number of events to return
            
        Returns:
            Dictionary with activity feed events
        """
        result = self.task_collaboration.get_activity_feed(task_id, user_id, limit)
        
        return {
            "success": True,
            "activity_feed": result["events"]
        }
    
    # Task Template Methods
    
    def create_template(self, name: str, description: str, category: str,
                      task_defaults: Dict[str, Any],
                      subtask_templates: Optional[List[Dict[str, Any]]] = None,
                      verification_criteria: Optional[List[str]] = None,
                      implementation_guide: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new task template.
        
        Args:
            name: Name of the template
            description: Description of the template
            category: Category for organizing templates
            task_defaults: Default values for task fields
            subtask_templates: Templates for subtasks
            verification_criteria: Default verification criteria
            implementation_guide: Default implementation guide
            tags: Tags for categorizing the template
            
        Returns:
            Dictionary with the created template
        """
        try:
            result = self.task_templates.create_template(
                name=name,
                description=description,
                category=category,
                task_defaults=task_defaults,
                subtask_templates=subtask_templates,
                verification_criteria=verification_criteria,
                implementation_guide=implementation_guide,
                tags=tags
            )
            
            return {
                "success": True,
                "template": result
            }
        except Exception as e:
            return {"error": str(e)}
    
    def update_template(self, template_id: str, 
                      updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task template.
        
        Args:
            template_id: ID of the template to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with the updated template
        """
        result = self.task_templates.update_template(template_id, updates)
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {
            "success": True,
            "template": result
        }
    
    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Delete a task template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            Dictionary with the result of the operation
        """
        result = self.task_templates.delete_template(template_id)
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {
            "success": True,
            "message": result["message"]
        }
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a task template by ID.
        
        Args:
            template_id: ID of the template to get
            
        Returns:
            Dictionary with the template data
        """
        result = self.task_templates.get_template(template_id)
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {
            "success": True,
            "template": result
        }
    
    def list_templates(self, category: Optional[str] = None, 
                     tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """List all task templates, optionally filtered by category or tags.
        
        Args:
            category: Optional category to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            Dictionary with list of templates
        """
        templates = self.task_templates.list_templates(category, tags)
        
        return {
            "success": True,
            "templates": templates
        }
    
    def get_template_categories(self) -> Dict[str, Any]:
        """Get all template categories.
        
        Returns:
            Dictionary with list of category names
        """
        categories = self.task_templates.get_categories()
        
        return {
            "success": True,
            "categories": categories
        }
    
    def get_template_tags(self) -> Dict[str, Any]:
        """Get all template tags.
        
        Returns:
            Dictionary with list of tag names
        """
        tags = self.task_templates.get_tags()
        
        return {
            "success": True,
            "tags": tags
        }
    
    def apply_template(self, template_id: str, 
                     custom_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a template to create a new task.
        
        Args:
            template_id: ID of the template to apply
            custom_values: Optional custom values to override template defaults
            
        Returns:
            Dictionary with the task data created from the template
        """
        result = self.task_templates.apply_template(template_id, custom_values)
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Create the actual task from the template data
        task_data = result["task"]
        task = self._create_task_from_data(task_data)
        
        # Add the task to the task manager
        self.tasks[task.id] = task
        
        # Process subtasks if any
        subtasks = []
        if "subtasks" in result and result["subtasks"]:
            for subtask_data in result["subtasks"]:
                subtask_id = subtask_data.get("id", f"{task.id}.{len(subtasks) + 1}")
                subtask_title = subtask_data.get("title", f"Subtask for {task.title}")
                subtask_description = subtask_data.get("description", "")
                
                # Create a subtask
                subtask = self.add_subtask(
                    task.id,
                    subtask_title,
                    subtask_description
                )
                
                if "success" in subtask and subtask["success"]:
                    subtasks.append(subtask["subtask"])
        
        return {
            "success": True,
            "task": self._task_to_dict(task),
            "subtasks": subtasks
        }
    
    def create_template_from_task(self, task_id: str, name: str, 
                               category: str, 
                               include_subtasks: bool = True,
                               tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a template from an existing task.
        
        Args:
            task_id: ID of the task to create a template from
            name: Name for the new template
            category: Category for the new template
            include_subtasks: Whether to include subtasks in the template
            tags: Optional tags for the template
            
        Returns:
            Dictionary with the created template
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        
        try:
            result = self.task_templates.create_template_from_task(
                task=task,
                name=name,
                category=category,
                include_subtasks=include_subtasks,
                tags=tags
            )
            
            return {
                "success": True,
                "template": result
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _create_task_from_data(self, task_data: Dict[str, Any]) -> Task:
        """Create a Task object from dictionary data.
        
        Args:
            task_data: Dictionary with task data
            
        Returns:
            Task object
        """
        # Extract basic fields
        task_id = task_data.get("id", str(uuid.uuid4()))
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        
        # Parse status and priority
        status_str = task_data.get("status", TaskStatus.PENDING.value)
        try:
            status = TaskStatus(status_str)
        except ValueError:
            status = TaskStatus.PENDING
        
        priority_str = task_data.get("priority", TaskPriority.MEDIUM.value)
        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM
        
        # Parse dates
        created_at = datetime.now()
        if "created_at" in task_data and isinstance(task_data["created_at"], str):
            try:
                created_at = datetime.fromisoformat(task_data["created_at"])
            except ValueError:
                pass
        
        started_at = None
        if "started_at" in task_data and isinstance(task_data["started_at"], str):
            try:
                started_at = datetime.fromisoformat(task_data["started_at"])
            except ValueError:
                pass
        
        completed_at = None
        if "completed_at" in task_data and isinstance(task_data["completed_at"], str):
            try:
                completed_at = datetime.fromisoformat(task_data["completed_at"])
            except ValueError:
                pass
        
        # Create the task
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            dependencies=task_data.get("dependencies", []),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # Add additional fields if present
        if "verification_criteria" in task_data:
            task.verification_criteria = task_data["verification_criteria"]
        
        if "execution_context" in task_data:
            task.execution_context = task_data["execution_context"]
        
        if "subtasks" in task_data:
            task.subtasks = task_data["subtasks"]
        
        if "collaboration_context" in task_data:
            task.collaboration_context = task_data["collaboration_context"]
        
        return task
    
    # Task Import/Export Methods
    
    def import_tasks(self, file_path: str, format: Optional[str] = None,
                    merge: bool = False) -> Dict[str, Any]:
        """Import tasks from a file.
        
        Args:
            file_path: Path to the file to import
            format: Format of the file (json, csv, yaml, xml, markdown)
                   If None, will be inferred from file extension
            merge: Whether to merge with existing tasks or replace them
            
        Returns:
            Dictionary with import results
        """
        try:
            # Import tasks from file
            imported_task_data = self.task_io.import_tasks(file_path, format)
            
            imported_tasks = []
            for task_data in imported_task_data:
                task = self._create_task_from_data(task_data)
                imported_tasks.append(task)
            
            # Add tasks to the task manager
            if not merge:
                # Replace existing tasks
                self.tasks = {}
            
            for task in imported_tasks:
                self.tasks[task.id] = task
            
            return {
                "success": True,
                "message": f"Successfully imported {len(imported_tasks)} tasks",
                "imported_tasks": [self._task_to_dict(task) for task in imported_tasks]
            }
        except TaskImportError as e:
            return {"error": str(e)}
    
    def export_tasks(self, file_path: str, format: Optional[str] = None,
                   task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export tasks to a file.
        
        Args:
            file_path: Path to save the exported file
            format: Format to export (json, csv, yaml, xml, markdown)
                   If None, will be inferred from file extension
            task_ids: Optional list of task IDs to export
                     If None, all tasks will be exported
            
        Returns:
            Dictionary with export results
        """
        try:
            # Get tasks to export
            if task_ids:
                tasks_to_export = []
                for task_id in task_ids:
                    task = self.get_task(task_id)
                    if task:
                        tasks_to_export.append(task)
            else:
                tasks_to_export = list(self.tasks.values())
            
            # Convert tasks to dictionaries
            task_dicts = [self._task_to_dict(task) for task in tasks_to_export]
            
            # Export tasks to file
            exported_file = self.task_io.export_tasks(task_dicts, file_path, format)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(task_dicts)} tasks to {exported_file}",
                "exported_file": exported_file
            }
        except TaskExportError as e:
            return {"error": str(e)}
    
    def convert_format(self, tasks: Union[List[Dict[str, Any]], str], 
                     from_format: str, to_format: str) -> Dict[str, Any]:
        """Convert tasks from one format to another without saving to file.
        
        Args:
            tasks: List of task dictionaries or raw content string
            from_format: Source format (json, csv, yaml, xml, markdown)
            to_format: Target format (json, csv, yaml, xml, markdown)
            
        Returns:
            Dictionary with conversion results
        """
        try:
            # Convert format
            converted = self.task_io.convert_format(tasks, from_format, to_format)
            
            return {
                "success": True,
                "converted_content": converted
            }
        except (TaskImportError, TaskExportError) as e:
            return {"error": str(e)}
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get a list of supported import/export formats.
        
        Returns:
            Dictionary with supported formats
        """
        return {
            "success": True,
            "formats": list(self.task_io.supported_formats.keys())
        }
    
    def apply_project_rules(self, task_id: str) -> List[Dict[str, Any]]:
        """Apply project rules to a task and get recommendations.
        
        If an AI provider is available, it will be used to generate detailed recommendations.
        Otherwise, a simple rule-matching approach will be used.
        
        Args:
            task_id: ID of the task to apply rules to
            
        Returns:
            List of dictionaries with rule applications and recommendations
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Get relevant project rules
        applicable_rules = []
        for rule_id, rule in self._project_rules.items():
            if rule.is_active:
                # Check if rule applies to this task's tags
                if not rule.applies_to_tags or any(tag in task.project_context_tags for tag in rule.applies_to_tags):
                    applicable_rules.append(rule)
        
        if not applicable_rules:
            return []  # No applicable rules
        
        # If we have an AI provider, use it to apply rules and generate recommendations
        if self.ai_provider:
            try:
                return self.ai_provider.apply_rules_to_task(task, applicable_rules)
            except Exception as e:
                print(f"Error using AI provider to apply rules: {str(e)}")
                # Fall back to simple rule matching if AI fails
        
        # Simple rule matching (fallback)
        rule_applications = []
        for rule in applicable_rules:
            # Simple matching based on keywords in task title/description
            keywords = [word.lower() for word in rule.name.split() + rule.description.split()]
            task_text = (task.title + " " + (task.description or "")).lower()
            
            # Check if any keywords are in the task text
            matches = [keyword for keyword in keywords if keyword in task_text and len(keyword) > 3]
            applies = len(matches) > 0
            
            application = {
                "rule_id": rule.id,
                "applies": applies,
                "recommendations": [rule.content] if applies else [],
                "implementation_notes": f"Matching keywords: {', '.join(matches)}" if matches else "No keyword matches found"
            }
            
            rule_applications.append(application)
        
        return rule_applications
    
    def generate_verification_criteria(self, task_id: str) -> str:
        """Generate verification criteria for a task.
        
        If an AI provider is available, it will be used to generate detailed criteria.
        Otherwise, a simple template-based criteria will be generated.
        
        Args:
            task_id: ID of the task to generate criteria for
            
        Returns:
            Verification criteria as a string
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # If we have an AI provider, use it to generate detailed criteria
        if self.ai_provider:
            try:
                criteria = self.ai_provider.generate_verification_criteria(task)
                
                # Store the criteria in the task for future reference
                task.verification_criteria = criteria
                
                return criteria
            except Exception as e:
                print(f"Error using AI provider for verification criteria: {str(e)}")
                # Fall back to template-based criteria if AI fails
        
        # Template-based criteria (fallback)
        # Load the verification criteria template
        try:
            from .prompts import load_prompt, render_template
            template = load_prompt("verification_criteria")
            
            # Render the template with task information
            criteria = render_template(template, {
                "title": task.title,
                "description": task.description or "No description provided",
                "priority": task.priority.value
            })
            
            # Store the criteria in the task for future reference
            task.verification_criteria = criteria
            
            return criteria
        except Exception as e:
            print(f"Error generating verification criteria from template: {str(e)}")
            
            # Very simple fallback if template loading fails
            criteria = f"# Verification Criteria for: {task.title}\n\n"
            criteria += f"## Description\n{task.description or 'No description provided'}\n\n"
            criteria += "## Acceptance Criteria\n- The implementation meets the requirements\n- The code passes all tests\n- The code follows project standards\n\n"
            criteria += "## Test Cases\n1. Test basic functionality\n2. Test edge cases\n3. Test error handling\n\n"
            criteria += "## Definition of Done\nThe task is considered done when all acceptance criteria are met and all tests pass."
            
            # Store the criteria in the task for future reference
            task.verification_criteria = criteria
            
            return criteria
    
    def analyze_task_complexity(self, task_id: str) -> Dict[str, Any]:
        """Analyze the complexity of a task based on its description, subtasks, and dependencies.
        
        If an AI provider is available, it will be used for more sophisticated analysis.
        Otherwise, a heuristic approach will be used.
        
        Args:
            task_id: ID of the task to analyze
            
        Returns:
            Dictionary with complexity analysis results
            
        Raises:
            ValueError: If the task is not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # If we have an AI provider, use it for more sophisticated analysis
        if self.ai_provider:
            try:
                # Get all dependencies as tasks
                dependency_tasks = []
                for dep_id in task.dependencies:
                    dep_task = self.get_task(dep_id)
                    if dep_task:
                        dependency_tasks.append(dep_task)
                
                # Use the AI provider to analyze the task
                analysis = self.ai_provider.analyze_task_complexity(task)
                
                # Store the analysis result in the task for future reference
                if not task.analysis_result:
                    task.analysis_result = json.dumps(analysis)
                
                # Update the task's complexity score
                task.complexity_score = analysis.get("complexity_score")
                
                # Update the task's estimated effort hours if not already set
                if not task.estimated_effort_hours and "estimated_effort_hours" in analysis:
                    task.estimated_effort_hours = analysis["estimated_effort_hours"]
                
                return analysis
            except Exception as e:
                print(f"Error using AI provider for task analysis: {str(e)}")
                # Fall back to heuristic analysis if AI fails
        
        # Heuristic analysis (fallback)
        # Basic metrics
        description_length = len(task.description or "")
        dependencies_count = len(task.dependencies)
        subtasks_count = len(task.subtasks)
        
        # Simple complexity scoring
        complexity_score = min(10, (
            description_length / 100 +  # Longer descriptions suggest more complexity
            dependencies_count * 1.5 +  # Dependencies add complexity
            subtasks_count * 0.5        # More subtasks indicate complexity but less than dependencies
        ))
        
        # Estimated effort (simple heuristic)
        estimated_effort_hours = complexity_score * 0.8  # Simple multiplier
        
        # Recommendations based on complexity
        recommendations = []
        if complexity_score > 7:
            recommendations.append("Consider breaking this task into smaller subtasks")
            recommendations.append("Schedule a planning session for this complex task")
        elif complexity_score > 4:
            recommendations.append("Review dependencies before starting")
        
        if dependencies_count > 3:
            recommendations.append("Map out dependency chain to identify critical path")
        
        # Update the task's complexity score and estimated effort
        task.complexity_score = complexity_score
        if not task.estimated_effort_hours:
            task.estimated_effort_hours = estimated_effort_hours
        
        analysis_result = {
            "complexity_score": complexity_score,
            "estimated_effort_hours": estimated_effort_hours,
            "factors": {
                "description_length": description_length,
                "dependencies_count": dependencies_count,
                "subtasks_count": subtasks_count
            },
            "recommendations": recommendations
        }
        
        # Store the analysis result in the task for future reference
        if not task.analysis_result:
            task.analysis_result = json.dumps(analysis_result)
        
        return analysis_result
        
    def get_task_chain(self, task_id: str) -> List[List[Task]]:
        """Get the full dependency chain for a task, organized by levels."""
        task = self.get_task(task_id)
        if not task:
            return []
            
        # Use breadth-first search to build the dependency chain
        visited = set()
        chain = []
        current_level = [task]
        
        while current_level:
            chain.append(current_level)
            next_level = []
            
            for t in current_level:
                for dep_id in t.dependencies:
                    dep_task = self.get_task(dep_id)
                    if dep_task and dep_id not in visited:
                        next_level.append(dep_task)
                        visited.add(dep_id)
                        
            current_level = next_level
            
        return chain
        
    def get_critical_path(self) -> List[Task]:
        """Identify the critical path of tasks based on dependencies and estimated effort."""
        # This is a simplified implementation
        # A full critical path algorithm would use a topological sort and calculate earliest/latest start times
        
        # First, find all tasks with no dependents (leaf tasks)
        all_tasks = self.list_tasks()
        all_task_ids = {t.id for t in all_tasks}
        
        # Find tasks that are not dependencies of any other task
        leaf_tasks = []
        for task in all_tasks:
            is_dependency = False
            for other_task in all_tasks:
                if task.id in other_task.dependencies:
                    is_dependency = True
                    break
            if not is_dependency:
                leaf_tasks.append(task)
                
        # Find the leaf task with the highest complexity
        if not leaf_tasks:
            return []
            
        # Use our complexity analysis to find the most complex leaf task
        leaf_complexities = [(task, self.analyze_task_complexity(task.id)['complexity_score']) 
                            for task in leaf_tasks]
        most_complex_leaf = max(leaf_complexities, key=lambda x: x[1])[0]
        
        # Build the path from this leaf task back to root tasks
        critical_path = [most_complex_leaf]
        current_task = most_complex_leaf
        
        while current_task.dependencies:
            # Find the most complex dependency
            dependencies = [self.get_task(dep_id) for dep_id in current_task.dependencies 
                           if self.get_task(dep_id)]
            if not dependencies:
                break
                
            dep_complexities = [(task, self.analyze_task_complexity(task.id)['complexity_score']) 
                               for task in dependencies]
            most_complex_dep = max(dep_complexities, key=lambda x: x[1])[0]
            
            critical_path.insert(0, most_complex_dep)
            current_task = most_complex_dep
            
        return critical_path
        
    def generate_dependency_graph(self, format: str = "mermaid") -> str:
        """Generate a representation of task dependencies in specified format."""
        tasks = self.list_tasks()
        
        if format == "mermaid":
            # Generate Mermaid.js compatible graph markup
            lines = ["graph TD;"]
            
            # Add nodes with status colors
            for task in tasks:
                # Define node style based on status
                style = ""
                if task.status == TaskStatus.COMPLETED:
                    style = ":::done"
                elif task.status == TaskStatus.IN_PROGRESS:
                    style = ":::active"
                elif task.status == TaskStatus.BLOCKED:
                    style = ":::blocked"
                    
                # Add node with title as label
                lines.append(f"    {task.id}[\"#{task.id}: {task.title}\"]" + style + ";")
            
            # Add edges for dependencies
            for task in tasks:
                for dep_id in task.dependencies:
                    if dep_id in self._tasks:  # Ensure dependency exists
                        lines.append(f"    {dep_id}-->{task.id};")
            
            # Add class definitions
            lines.append("    classDef done fill:#cfc,stroke:#6c6;")
            lines.append("    classDef active fill:#ccf,stroke:#66c;")
            lines.append("    classDef blocked fill:#fcc,stroke:#c66;")
            
            return "\n".join(lines)
        else:
            return f"Unsupported format: {format}"

    def import_tasks_from_prd(self, prd_file_path: str) -> List[Task]:
        """
        Parses a PRD Markdown file and imports tasks into the task manager.
        Returns a list of newly created Task objects.
        """
        # Assumes MarkdownPRDParser is imported at the top
        
        parser = MarkdownPRDParser()
        potential_tasks_data = parser.parse_file(prd_file_path)
        
        created_tasks: List[Task] = []
        if not potential_tasks_data:
            # parser.parse_file handles its own error printing for file not found etc.
            return created_tasks

        for task_data in potential_tasks_data:
            title = task_data.get("title")
            description = task_data.get("description")
            
            if title: 
                # add_task uses its own defaults for priority, status if not provided
                new_task = self.add_task(
                    title=title,
                    description=description
                )
                created_tasks.append(new_task)
            else:
                print(f"Warning: Potential task from PRD '{prd_file_path}' skipped due to missing title: {task_data}")
                
        if created_tasks:
            print(f"Successfully imported {len(created_tasks)} tasks from {prd_file_path}")
        else:
            # This covers cases where the PRD was parsed but yielded no actionable tasks (e.g., empty or no H2/H3s)
            print(f"No actionable tasks were imported from {prd_file_path}")
            
        return created_tasks

    # Project Rule Management (Placeholder - to be expanded)
    def add_project_rule(self, name: str, description: str, content: str, applies_to_tags: Optional[List[str]] = None) -> ProjectRule:
        rule_id = str(uuid.uuid4())
        rule = ProjectRule(
            id=rule_id,
            name=name,
            description=description,
            applies_to_tags=applies_to_tags or [],
            content=content
        )
        self._project_rules[rule_id] = rule
        return rule

    def get_project_rule(self, rule_id: str) -> Optional[ProjectRule]:
        return self._project_rules.get(rule_id)

    def list_project_rules(self) -> List[ProjectRule]:
        return sorted(list(self._project_rules.values()), key=lambda r: r.created_at)

    def update_project_rule(self, rule_id: str, update_data: Dict[str, Any], user: Optional[str] = "system") -> Optional[ProjectRule]:
        """Updates an existing project rule. Allows partial updates."""
        rule = self.get_project_rule(rule_id)
        if not rule:
            return None

        # For now, we won't add a full history to rules like tasks, but we'll touch the timestamp
        # A more complex system might log changes to rules as well.
        changed_fields = False
        for key, value in update_data.items():
            if hasattr(rule, key):
                old_value = getattr(rule, key)
                # Handle boolean conversion for 'is_active' if passed as string
                if key == 'is_active' and isinstance(value, str):
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    else:
                        print(f"Warning: Invalid string value '{value}' for 'is_active'. Must be 'true' or 'false'. Skipping update for this field.")
                        continue # Skip this field if conversion is not clear
                
                if old_value != value:
                    setattr(rule, key, value)
                    changed_fields = True
        
        if changed_fields:
            rule.touch()
            # print(f"Project rule {rule_id} updated by {user}.") # Optional logging
        return rule

    def delete_project_rule(self, rule_id: str, user: Optional[str] = "system") -> bool:
        """Deletes a project rule by its ID."""
        if rule_id in self._project_rules:
            del self._project_rules[rule_id]
            # print(f"Project rule {rule_id} deleted by {user}.") # Optional logging
            return True
        return False


    def save_to_file(self, file_path: str):
        """Saves tasks and rules to a file (e.g., JSON). Basic placeholder."""
        # This is a very basic example. Production use would need robust serialization.
        import json
        data = {
            "tasks": {tid: task.__dict__ for tid, task in self._tasks.items()},
            "project_rules": {rid: rule.__dict__ for rid, rule in self._project_rules.items()}
        }
        # Need to handle datetime and Enum serialization properly
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, '__dict__'): # For dataclasses
                return obj.__dict__
            return str(obj)

        with open(file_path, 'w') as f:
            json.dump(data, f, default=custom_serializer, indent=4)
        print(f"Data saved to {file_path}")

    def load_from_file(self, file_path: str):
        """Loads tasks and rules from a file. Basic placeholder."""
        import json
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self._tasks = {}
            for task_id, task_data in data.get("tasks", {}).items():
                # Need to handle datetime and Enum deserialization properly
                task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'])
                task_data['status'] = TaskStatus(task_data['status'])
                task_data['priority'] = TaskPriority(task_data['priority'])
                # Re-instantiate Task objects
                self._tasks[task_id] = Task(**task_data)

            self._project_rules = {}
            for rule_id, rule_data in data.get("project_rules", {}).items():
                rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                rule_data['updated_at'] = datetime.fromisoformat(rule_data['updated_at'])
                # Ensure 'is_active' is a boolean, defaulting if missing or handling type
                is_active_val = rule_data.get('is_active')
                if isinstance(is_active_val, str):
                    rule_data['is_active'] = is_active_val.lower() == 'true'
                elif is_active_val is None: # if 'is_active' is not in JSON, dataclass default takes over
                    pass # Let dataclass default handle it if not present in JSON
                else:
                    rule_data['is_active'] = bool(is_active_val) # Explicitly cast
                
                self._project_rules[rule_id] = ProjectRule(**rule_data)
            print(f"Data loaded from {file_path}")
        except FileNotFoundError:
            print(f"File not found: {file_path}. Starting with an empty task manager.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}. Starting with an empty task manager.")
        except Exception as e:
            print(f"An error occurred while loading data: {e}. Starting with an empty task manager.")

