"""
Command Executor for the Natural Language Task Processing system.

This module implements the command executor that translates parsed natural
language intents and entities into actual task operations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta

from .base import CommandExecutor, NLPResult, Intent, Entity


class TaskCommandExecutor(CommandExecutor):
    """
    Command executor for task management operations.
    
    This class executes commands based on recognized intents and entities,
    interacting with the Task Manager to perform operations.
    """
    
    def __init__(self, task_manager, recommendation_system=None):
        """
        Initialize the task command executor.
        
        Args:
            task_manager: Task manager instance to execute operations on
            recommendation_system: Optional recommendation system for task suggestions
        """
        self.task_manager = task_manager
        self.recommendation_system = recommendation_system
        self.logger = logging.getLogger(__name__)
    
    def execute(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute a command based on NLP result.
        
        Args:
            nlp_result: Result of natural language processing
            
        Returns:
            Result of command execution
        """
        # Get primary intent
        primary_intent = nlp_result.primary_intent
        
        if not primary_intent:
            return self._create_response(
                success=False,
                message="I couldn't understand what you want to do. Please try again.",
                data=None
            )
        
        # Execute appropriate command based on intent
        intent_name = primary_intent.name
        
        try:
            if intent_name == "create_task":
                return self._execute_create_task(nlp_result)
            elif intent_name == "list_tasks":
                return self._execute_list_tasks(nlp_result)
            elif intent_name == "update_task":
                return self._execute_update_task(nlp_result)
            elif intent_name == "delete_task":
                return self._execute_delete_task(nlp_result)
            elif intent_name == "complete_task":
                return self._execute_complete_task(nlp_result)
            elif intent_name == "get_task":
                return self._execute_get_task(nlp_result)
            elif intent_name == "set_priority":
                return self._execute_set_priority(nlp_result)
            elif intent_name == "set_due_date":
                return self._execute_set_due_date(nlp_result)
            elif intent_name == "add_dependency":
                return self._execute_add_dependency(nlp_result)
            elif intent_name == "remove_dependency":
                return self._execute_remove_dependency(nlp_result)
            elif intent_name == "get_recommendations":
                return self._execute_get_recommendations(nlp_result)
            elif intent_name == "help":
                return self._execute_help(nlp_result)
            else:
                return self._create_response(
                    success=False,
                    message=f"I don't know how to {intent_name}. Try asking for help to see what I can do.",
                    data=None
                )
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return self._create_response(
                success=False,
                message=f"An error occurred: {str(e)}",
                data=None
            )
    
    def _execute_create_task(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute create task command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract title
        title_entities = nlp_result.get_entities_by_type("title")
        if title_entities:
            title = title_entities[0].value
        else:
            # Try to extract title from the text after "create task" or similar
            raw_text = nlp_result.raw_text
            words = raw_text.split()
            task_index = -1
            
            for i, word in enumerate(words):
                if word.lower() == "task":
                    task_index = i
                    break
            
            if task_index >= 0 and task_index + 1 < len(words):
                title = " ".join(words[task_index + 1:])
            else:
                title = "New Task"
        
        # Extract description
        description_entities = nlp_result.get_entities_by_type("description")
        description = description_entities[0].value if description_entities else ""
        
        # Extract priority
        priority_entities = nlp_result.get_entities_by_type("priority")
        priority = priority_entities[0].value if priority_entities else "medium"
        
        # Extract due date
        date_entities = nlp_result.get_entities_by_type("date")
        relative_date_entities = nlp_result.get_entities_by_type("relative_date")
        
        due_date = None
        if date_entities:
            due_date = date_entities[0].value
        elif relative_date_entities:
            relative_date = relative_date_entities[0].value
            due_date = self._parse_relative_date(relative_date)
        
        # Create task
        task_data = {
            "title": title,
            "description": description,
            "priority": priority
        }
        
        if due_date:
            task_data["due_date"] = due_date
        
        try:
            task_id = self.task_manager.create_task(task_data)
            
            return self._create_response(
                success=True,
                message=f"Task '{title}' created successfully with ID {task_id}.",
                data={"task_id": task_id, "task_data": task_data}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to create task: {str(e)}",
                data=None
            )
    
    def _execute_list_tasks(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute list tasks command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract filters
        status_filters = []
        priority_filters = []
        
        # Check for status in text
        raw_text = nlp_result.raw_text.lower()
        if "pending" in raw_text:
            status_filters.append("pending")
        if "in progress" in raw_text or "in-progress" in raw_text:
            status_filters.append("in-progress")
        if "completed" in raw_text or "done" in raw_text:
            status_filters.append("completed")
        
        # Check for priority in text
        priority_entities = nlp_result.get_entities_by_type("priority")
        for entity in priority_entities:
            priority_filters.append(entity.value)
        
        # Get tasks
        try:
            filters = {}
            if status_filters:
                filters["status"] = status_filters
            if priority_filters:
                filters["priority"] = priority_filters
            
            tasks = self.task_manager.list_tasks(filters)
            
            if not tasks:
                message = "No tasks found."
                if filters:
                    filter_desc = []
                    if "status" in filters:
                        filter_desc.append(f"status={','.join(filters['status'])}")
                    if "priority" in filters:
                        filter_desc.append(f"priority={','.join(filters['priority'])}")
                    message = f"No tasks found matching filters: {' '.join(filter_desc)}."
            else:
                message = f"Found {len(tasks)} tasks."
            
            return self._create_response(
                success=True,
                message=message,
                data={"tasks": tasks, "filters": filters}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to list tasks: {str(e)}",
                data=None
            )
    
    def _execute_get_task(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute get task command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to view.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        try:
            task = self.task_manager.get_task(task_id)
            
            if not task:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Found task: {task['title']}",
                data={"task": task}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to get task: {str(e)}",
                data=None
            )
    
    def _execute_update_task(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute update task command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to update.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        # Extract fields to update
        update_data = {}
        
        # Title
        title_entities = nlp_result.get_entities_by_type("title")
        if title_entities:
            update_data["title"] = title_entities[0].value
        
        # Description
        description_entities = nlp_result.get_entities_by_type("description")
        if description_entities:
            update_data["description"] = description_entities[0].value
        
        # Priority
        priority_entities = nlp_result.get_entities_by_type("priority")
        if priority_entities:
            update_data["priority"] = priority_entities[0].value
        
        # Due date
        date_entities = nlp_result.get_entities_by_type("date")
        relative_date_entities = nlp_result.get_entities_by_type("relative_date")
        
        if date_entities:
            update_data["due_date"] = date_entities[0].value
        elif relative_date_entities:
            relative_date = relative_date_entities[0].value
            update_data["due_date"] = self._parse_relative_date(relative_date)
        
        if not update_data:
            return self._create_response(
                success=False,
                message="I couldn't determine what you want to update. Please specify title, description, priority, or due date.",
                data=None
            )
        
        try:
            success = self.task_manager.update_task(task_id, update_data)
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found or couldn't be updated.",
                    data=None
                )
            
            fields_updated = ", ".join(update_data.keys())
            return self._create_response(
                success=True,
                message=f"Task {task_id} updated successfully. Fields updated: {fields_updated}.",
                data={"task_id": task_id, "updated_fields": update_data}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to update task: {str(e)}",
                data=None
            )
    
    def _execute_delete_task(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute delete task command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to delete.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        try:
            success = self.task_manager.delete_task(task_id)
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found or couldn't be deleted.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Task {task_id} deleted successfully.",
                data={"task_id": task_id}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to delete task: {str(e)}",
                data=None
            )
    
    def _execute_complete_task(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute complete task command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to mark as complete.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        try:
            success = self.task_manager.update_task(task_id, {"status": "completed"})
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found or couldn't be marked as complete.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Task {task_id} marked as complete.",
                data={"task_id": task_id}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to complete task: {str(e)}",
                data=None
            )
    
    def _execute_set_priority(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute set priority command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to update.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        # Extract priority
        priority_entities = nlp_result.get_entities_by_type("priority")
        
        if not priority_entities:
            return self._create_response(
                success=False,
                message="I couldn't determine the priority level. Please specify high, medium, or low.",
                data=None
            )
        
        priority = priority_entities[0].value
        
        try:
            success = self.task_manager.update_task(task_id, {"priority": priority})
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found or priority couldn't be updated.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Priority for task {task_id} set to {priority}.",
                data={"task_id": task_id, "priority": priority}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to set priority: {str(e)}",
                data=None
            )
    
    def _execute_set_due_date(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute set due date command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task ID
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if not task_id_entities:
            return self._create_response(
                success=False,
                message="I couldn't find a task ID in your request. Please specify which task you want to update.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        
        # Extract due date
        date_entities = nlp_result.get_entities_by_type("date")
        relative_date_entities = nlp_result.get_entities_by_type("relative_date")
        
        if not date_entities and not relative_date_entities:
            return self._create_response(
                success=False,
                message="I couldn't determine the due date. Please specify a date.",
                data=None
            )
        
        if date_entities:
            due_date = date_entities[0].value
        else:
            relative_date = relative_date_entities[0].value
            due_date = self._parse_relative_date(relative_date)
        
        try:
            success = self.task_manager.update_task(task_id, {"due_date": due_date})
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Task with ID {task_id} not found or due date couldn't be updated.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Due date for task {task_id} set to {due_date}.",
                data={"task_id": task_id, "due_date": due_date}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to set due date: {str(e)}",
                data=None
            )
    
    def _execute_add_dependency(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute add dependency command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task IDs
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if len(task_id_entities) < 2:
            return self._create_response(
                success=False,
                message="I need two task IDs to create a dependency. Please specify which task depends on which.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        depends_on_id = task_id_entities[1].value
        
        try:
            success = self.task_manager.add_dependency(task_id, depends_on_id)
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Couldn't add dependency. Check that both tasks exist and there are no circular dependencies.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Dependency added: Task {task_id} now depends on task {depends_on_id}.",
                data={"task_id": task_id, "depends_on": depends_on_id}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to add dependency: {str(e)}",
                data=None
            )
    
    def _execute_remove_dependency(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute remove dependency command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        # Extract task IDs
        task_id_entities = nlp_result.get_entities_by_type("task_id")
        
        if len(task_id_entities) < 2:
            return self._create_response(
                success=False,
                message="I need two task IDs to remove a dependency. Please specify which dependency to remove.",
                data=None
            )
        
        task_id = task_id_entities[0].value
        depends_on_id = task_id_entities[1].value
        
        try:
            success = self.task_manager.remove_dependency(task_id, depends_on_id)
            
            if not success:
                return self._create_response(
                    success=False,
                    message=f"Couldn't remove dependency. Check that both tasks exist and the dependency exists.",
                    data=None
                )
            
            return self._create_response(
                success=True,
                message=f"Dependency removed: Task {task_id} no longer depends on task {depends_on_id}.",
                data={"task_id": task_id, "depends_on": depends_on_id}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to remove dependency: {str(e)}",
                data=None
            )
    
    def _execute_get_recommendations(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute get recommendations command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        if not self.recommendation_system:
            return self._create_response(
                success=False,
                message="Task recommendation system is not available.",
                data=None
            )
        
        # Extract user ID if present
        user_id = None
        raw_text = nlp_result.raw_text.lower()
        
        if "for user" in raw_text:
            # Try to extract user ID after "for user"
            user_index = raw_text.find("for user")
            if user_index >= 0:
                user_part = raw_text[user_index + 9:].strip()
                user_id = user_part.split()[0]
        
        # Extract limit if present
        limit = 5  # Default
        if "top" in raw_text:
            # Try to extract limit after "top"
            top_index = raw_text.find("top")
            if top_index >= 0:
                top_part = raw_text[top_index + 3:].strip()
                try:
                    limit = int(top_part.split()[0])
                except (ValueError, IndexError):
                    pass
        
        try:
            # Get all tasks
            tasks = self.task_manager.list_tasks({})
            
            # Get recommendations
            recommendations = self.recommendation_system.recommend_tasks(
                tasks=tasks,
                user_id=user_id,
                limit=limit
            )
            
            if not recommendations:
                return self._create_response(
                    success=True,
                    message="No task recommendations available at this time.",
                    data={"recommendations": []}
                )
            
            return self._create_response(
                success=True,
                message=f"Here are {len(recommendations)} recommended tasks.",
                data={"recommendations": recommendations}
            )
        except Exception as e:
            return self._create_response(
                success=False,
                message=f"Failed to get recommendations: {str(e)}",
                data=None
            )
    
    def _execute_help(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute help command.
        
        Args:
            nlp_result: NLP result containing intents and entities
            
        Returns:
            Command execution result
        """
        help_text = """
I can help you manage your tasks using natural language. Here are some examples of what you can say:

- "Create a new task called Fix login bug"
- "List all tasks"
- "List high priority tasks"
- "Show task #123"
- "Update task #123 with title 'Updated title'"
- "Set priority of task #123 to high"
- "Set due date of task #123 to next Friday"
- "Mark task #123 as complete"
- "Delete task #123"
- "Add dependency: task #123 depends on task #456"
- "Remove dependency between task #123 and task #456"
- "Recommend tasks for me"
- "What should I work on next?"

You can also ask for help on specific commands, like "How do I create a task?"
"""
        
        return self._create_response(
            success=True,
            message=help_text.strip(),
            data=None
        )
    
    def _create_response(self, success: bool, message: str, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a standardized response format.
        
        Args:
            success: Whether the command was successful
            message: Response message
            data: Optional data to include in the response
            
        Returns:
            Standardized response dictionary
        """
        return {
            "success": success,
            "message": message,
            "data": data,
            "response": message  # For conversation context
        }
    
    def _parse_relative_date(self, relative_date: str) -> str:
        """
        Parse a relative date into an actual date string.
        
        Args:
            relative_date: Relative date string (e.g., "today", "tomorrow")
            
        Returns:
            Date string in ISO format
        """
        today = datetime.now().date()
        
        if relative_date.lower() == "today":
            return today.isoformat()
        elif relative_date.lower() == "tomorrow":
            return (today + timedelta(days=1)).isoformat()
        elif relative_date.lower() == "yesterday":
            return (today - timedelta(days=1)).isoformat()
        elif relative_date.lower().startswith("next"):
            parts = relative_date.lower().split()
            if len(parts) >= 2:
                unit = parts[1]
                if unit == "week":
                    return (today + timedelta(weeks=1)).isoformat()
                elif unit == "month":
                    # Simple approximation for next month
                    if today.month == 12:
                        return datetime(today.year + 1, 1, today.day).date().isoformat()
                    else:
                        return datetime(today.year, today.month + 1, today.day).date().isoformat()
                elif unit == "year":
                    return datetime(today.year + 1, today.month, today.day).date().isoformat()
        elif relative_date.lower().startswith("in"):
            parts = relative_date.lower().split()
            if len(parts) >= 3:
                try:
                    amount = int(parts[1])
                    unit = parts[2]
                    if unit in ["day", "days"]:
                        return (today + timedelta(days=amount)).isoformat()
                    elif unit in ["week", "weeks"]:
                        return (today + timedelta(weeks=amount)).isoformat()
                    elif unit in ["month", "months"]:
                        # Simple approximation for months
                        month = today.month + amount
                        year = today.year
                        while month > 12:
                            month -= 12
                            year += 1
                        return datetime(year, month, today.day).date().isoformat()
                except (ValueError, IndexError):
                    pass
        
        # Default to today if we can't parse
        return today.isoformat()
