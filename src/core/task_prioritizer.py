"""
Task Prioritizer for Tascade AI.

This module provides functionality for prioritizing tasks and finding the next task to work on.
It considers task dependencies, status, priority, and complexity to make intelligent recommendations.

Inspired by the task prioritization algorithm in claude-task-master.
"""

from typing import Dict, List, Set, Optional, Any, Union
from .models import Task, TaskStatus, TaskPriority

class TaskPrioritizer:
    """
    Prioritizes tasks and recommends the next task to work on.
    
    This class provides methods for finding the next task to work on based on
    dependencies, status, priority, and other factors. It helps optimize
    workflow by suggesting the most appropriate task to tackle next.
    """
    
    @staticmethod
    def find_next_task(tasks: Dict[str, Task]) -> Optional[Dict[str, Any]]:
        """
        Find the next task to work on.
        
        Prioritization rules:
        1. Prefer subtasks of in-progress parent tasks
        2. Prefer tasks with no dependencies
        3. Prefer tasks with all dependencies completed
        4. Prefer higher priority tasks
        5. Prefer simpler tasks when priority is equal
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            Dictionary with next task information or None if no eligible tasks
        """
        if not tasks:
            return None
        
        # Helper function to convert priority to numeric value
        def priority_value(priority: TaskPriority) -> int:
            priority_map = {
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }
            return priority_map.get(priority, 0)
        
        # Build a set of completed task IDs
        completed_tasks = {
            task_id for task_id, task in tasks.items() 
            if task.status == TaskStatus.DONE
        }
        
        # Find eligible tasks (pending tasks with all dependencies satisfied)
        eligible_tasks = []
        for task_id, task in tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are satisfied
            all_dependencies_met = True
            for dep_id in task.dependencies:
                if dep_id not in completed_tasks:
                    all_dependencies_met = False
                    break
            
            if all_dependencies_met:
                eligible_tasks.append({
                    "id": task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority,
                    "priority_value": priority_value(task.priority),
                    "complexity": task.complexity_score or 5,  # Default to medium complexity
                    "dependencies": task.dependencies,
                    "is_subtask": False,
                    "parent_in_progress": False
                })
        
        # If no eligible tasks, return None
        if not eligible_tasks:
            return None
        
        # Sort eligible tasks by priority (higher first), then by complexity (lower first)
        sorted_tasks = sorted(
            eligible_tasks,
            key=lambda t: (-t["priority_value"], t["complexity"])
        )
        
        # Return the highest priority task
        return sorted_tasks[0]
    
    @staticmethod
    def find_next_task_with_subtasks(tasks: Dict[str, Task]) -> Optional[Dict[str, Any]]:
        """
        Find the next task to work on, considering both top-level tasks and subtasks.
        
        Prioritization rules:
        1. Prefer subtasks of in-progress parent tasks
        2. Prefer tasks with no dependencies
        3. Prefer tasks with all dependencies completed
        4. Prefer higher priority tasks
        5. Prefer simpler tasks when priority is equal
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            Dictionary with next task information or None if no eligible tasks
        """
        if not tasks:
            return None
        
        # Helper function to convert priority to numeric value
        def priority_value(priority: TaskPriority) -> int:
            priority_map = {
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }
            return priority_map.get(priority, 0)
        
        # Build a set of completed task IDs
        completed_tasks = {
            task_id for task_id, task in tasks.items() 
            if task.status == TaskStatus.DONE
        }
        
        # Find in-progress parent tasks
        in_progress_parents = {
            task_id for task_id, task in tasks.items()
            if task.status == TaskStatus.IN_PROGRESS and hasattr(task, 'subtasks') and task.subtasks
        }
        
        # Find eligible tasks and subtasks
        eligible_tasks = []
        
        # First check for eligible subtasks of in-progress parents
        for parent_id in in_progress_parents:
            parent_task = tasks[parent_id]
            
            for subtask in parent_task.subtasks:
                if subtask.status != TaskStatus.PENDING:
                    continue
                
                # Check if all dependencies are satisfied
                all_dependencies_met = True
                for dep_id in subtask.dependencies:
                    if dep_id not in completed_tasks:
                        all_dependencies_met = False
                        break
                
                if all_dependencies_met:
                    eligible_tasks.append({
                        "id": f"{parent_id}.{subtask.id}",
                        "title": subtask.title,
                        "status": subtask.status.value,
                        "priority": subtask.priority if hasattr(subtask, 'priority') else parent_task.priority,
                        "priority_value": priority_value(subtask.priority if hasattr(subtask, 'priority') else parent_task.priority),
                        "complexity": subtask.complexity_score if hasattr(subtask, 'complexity_score') else 3,
                        "dependencies": subtask.dependencies,
                        "is_subtask": True,
                        "parent_id": parent_id,
                        "parent_in_progress": True
                    })
        
        # Then check for eligible top-level tasks
        for task_id, task in tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are satisfied
            all_dependencies_met = True
            for dep_id in task.dependencies:
                if dep_id not in completed_tasks:
                    all_dependencies_met = False
                    break
            
            if all_dependencies_met:
                eligible_tasks.append({
                    "id": task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority,
                    "priority_value": priority_value(task.priority),
                    "complexity": task.complexity_score or 5,  # Default to medium complexity
                    "dependencies": task.dependencies,
                    "is_subtask": False,
                    "parent_in_progress": False
                })
        
        # If no eligible tasks, return None
        if not eligible_tasks:
            return None
        
        # Sort eligible tasks:
        # 1. Subtasks of in-progress parents first
        # 2. Then by priority (higher first)
        # 3. Then by complexity (lower first)
        sorted_tasks = sorted(
            eligible_tasks,
            key=lambda t: (
                -int(t["parent_in_progress"]),
                -t["priority_value"],
                t["complexity"]
            )
        )
        
        # Return the highest priority task
        return sorted_tasks[0]
    
    @staticmethod
    def get_task_queue(tasks: Dict[str, Task], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a prioritized queue of tasks to work on.
        
        Args:
            tasks: Dictionary of all tasks
            limit: Maximum number of tasks to include in the queue
            
        Returns:
            List of prioritized tasks
        """
        # Start with an empty queue
        queue = []
        
        # Make a copy of tasks to avoid modifying the original
        remaining_tasks = tasks.copy()
        
        # Build the queue by repeatedly finding the next task
        while len(queue) < limit and remaining_tasks:
            next_task = TaskPrioritizer.find_next_task_with_subtasks(remaining_tasks)
            if not next_task:
                break
                
            queue.append(next_task)
            
            # Remove the selected task from consideration for the next iteration
            task_id = next_task["id"]
            if "." in task_id:  # It's a subtask
                parent_id, subtask_id = task_id.split(".")
                if parent_id in remaining_tasks:
                    # Just mark the subtask as "done" for queue building purposes
                    for i, subtask in enumerate(remaining_tasks[parent_id].subtasks):
                        if str(subtask.id) == subtask_id:
                            # Create a copy to avoid modifying the original
                            remaining_tasks[parent_id].subtasks[i] = subtask.copy()
                            remaining_tasks[parent_id].subtasks[i].status = TaskStatus.DONE
                            break
            else:  # It's a top-level task
                if task_id in remaining_tasks:
                    del remaining_tasks[task_id]
        
        return queue
    
    @staticmethod
    def estimate_completion_time(tasks: Dict[str, Task]) -> Dict[str, Any]:
        """
        Estimate completion time for remaining tasks based on historical data.
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            Dictionary with completion time estimates
        """
        # Get completed tasks with execution time data
        completed_tasks_with_time = [
            task for task in tasks.values()
            if task.status == TaskStatus.DONE 
            and task.execution_context 
            and "metrics" in task.execution_context
            and "time_spent" in task.execution_context["metrics"]
        ]
        
        # If no historical data, use default estimates
        if not completed_tasks_with_time:
            return {
                "has_historical_data": False,
                "pending_tasks": sum(1 for task in tasks.values() if task.status == TaskStatus.PENDING),
                "average_completion_time": None,
                "estimated_total_time": None,
                "estimated_completion_date": None,
                "confidence": "low"
            }
        
        # Calculate average completion time
        total_time = sum(task.execution_context["metrics"]["time_spent"] for task in completed_tasks_with_time)
        average_time = total_time / len(completed_tasks_with_time)
        
        # Count pending tasks
        pending_tasks = [task for task in tasks.values() if task.status == TaskStatus.PENDING]
        pending_count = len(pending_tasks)
        
        # Estimate total remaining time
        estimated_total_time = average_time * pending_count
        
        # Determine confidence level based on amount of historical data
        confidence = "low"
        if len(completed_tasks_with_time) >= 10:
            confidence = "high"
        elif len(completed_tasks_with_time) >= 5:
            confidence = "medium"
        
        return {
            "has_historical_data": True,
            "pending_tasks": pending_count,
            "average_completion_time": average_time,
            "estimated_total_time": estimated_total_time,
            "confidence": confidence
        }
