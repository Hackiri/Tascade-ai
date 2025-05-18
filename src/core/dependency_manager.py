"""
Dependency Manager for Tascade AI.

This module provides functionality for managing task dependencies, including:
- Validating dependencies
- Detecting circular dependencies
- Fixing invalid dependencies
- Analyzing dependency chains

Inspired by the dependency management system in claude-task-master.
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from .models import Task, TaskStatus

class DependencyManager:
    """
    Manages task dependencies and relationships.
    
    This class provides methods for validating, analyzing, and fixing task dependencies.
    It helps ensure that task dependencies are valid and don't create circular references.
    """
    
    @staticmethod
    def is_circular_dependency(tasks: Dict[str, Task], task_id: str, dependency_id: str, 
                              chain: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """
        Check if adding a dependency would create a circular dependency.
        
        Args:
            tasks: Dictionary of all tasks
            task_id: ID of task that would depend on dependency_id
            dependency_id: ID of task that would be a dependency
            chain: Current chain of dependencies being checked (for recursive calls)
            
        Returns:
            Tuple of (is_circular, dependency_chain)
        """
        if chain is None:
            chain = []
        
        # If the dependency is already in the chain, we have a cycle
        if dependency_id in chain:
            return True, chain + [dependency_id]
        
        # If the dependency doesn't exist, it can't create a cycle
        if dependency_id not in tasks:
            return False, []
        
        # Check if any of the dependency's dependencies would create a cycle
        dependency_task = tasks[dependency_id]
        if dependency_task.dependencies:
            new_chain = chain + [dependency_id]
            for dep_id in dependency_task.dependencies:
                is_circular, cycle_chain = DependencyManager.is_circular_dependency(
                    tasks, task_id, dep_id, new_chain
                )
                if is_circular:
                    return True, cycle_chain
        
        return False, []
    
    @staticmethod
    def validate_dependencies(tasks: Dict[str, Task]) -> Dict[str, Any]:
        """
        Validate all task dependencies.
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "issues": [],
            "circular_dependencies": [],
            "missing_dependencies": [],
            "duplicate_dependencies": [],
            "self_dependencies": []
        }
        
        # Check each task's dependencies
        for task_id, task in tasks.items():
            if not task.dependencies:
                continue
            
            # Check for duplicate dependencies
            unique_deps = set(task.dependencies)
            if len(unique_deps) < len(task.dependencies):
                result["valid"] = False
                duplicates = [dep for dep in task.dependencies 
                             if task.dependencies.count(dep) > 1]
                result["duplicate_dependencies"].append({
                    "task_id": task_id,
                    "duplicates": list(set(duplicates))
                })
                result["issues"].append(
                    f"Task {task_id} has duplicate dependencies: {', '.join(set(duplicates))}"
                )
            
            # Check for self-dependencies
            if task_id in task.dependencies:
                result["valid"] = False
                result["self_dependencies"].append(task_id)
                result["issues"].append(
                    f"Task {task_id} depends on itself"
                )
            
            # Check for missing dependencies
            missing = [dep_id for dep_id in task.dependencies if dep_id not in tasks]
            if missing:
                result["valid"] = False
                result["missing_dependencies"].append({
                    "task_id": task_id,
                    "missing": missing
                })
                result["issues"].append(
                    f"Task {task_id} has missing dependencies: {', '.join(missing)}"
                )
            
            # Check for circular dependencies
            for dep_id in task.dependencies:
                if dep_id in tasks:
                    is_circular, cycle_chain = DependencyManager.is_circular_dependency(
                        tasks, task_id, dep_id, [task_id]
                    )
                    if is_circular:
                        result["valid"] = False
                        cycle = " -> ".join(cycle_chain)
                        if cycle not in result["circular_dependencies"]:
                            result["circular_dependencies"].append(cycle)
                            result["issues"].append(
                                f"Circular dependency detected: {cycle}"
                            )
        
        return result
    
    @staticmethod
    def fix_dependencies(tasks: Dict[str, Task]) -> Tuple[Dict[str, Task], Dict[str, Any]]:
        """
        Fix invalid dependencies in tasks.
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            Tuple of (updated_tasks, fix_report)
        """
        # Make a copy of tasks to avoid modifying the original
        updated_tasks = {task_id: task.copy() for task_id, task in tasks.items()}
        
        fix_report = {
            "fixed_issues": [],
            "removed_dependencies": [],
            "changes_made": False
        }
        
        # First validate to find issues
        validation = DependencyManager.validate_dependencies(updated_tasks)
        
        # Fix duplicate dependencies
        for issue in validation.get("duplicate_dependencies", []):
            task_id = issue["task_id"]
            if task_id in updated_tasks:
                old_deps = updated_tasks[task_id].dependencies.copy()
                updated_tasks[task_id].dependencies = list(set(old_deps))
                fix_report["fixed_issues"].append(
                    f"Removed duplicate dependencies from task {task_id}"
                )
                fix_report["changes_made"] = True
        
        # Fix self-dependencies
        for task_id in validation.get("self_dependencies", []):
            if task_id in updated_tasks:
                updated_tasks[task_id].dependencies = [
                    dep for dep in updated_tasks[task_id].dependencies
                    if dep != task_id
                ]
                fix_report["fixed_issues"].append(
                    f"Removed self-dependency from task {task_id}"
                )
                fix_report["removed_dependencies"].append({
                    "task_id": task_id,
                    "dependency_id": task_id,
                    "reason": "self_dependency"
                })
                fix_report["changes_made"] = True
        
        # Fix missing dependencies
        for issue in validation.get("missing_dependencies", []):
            task_id = issue["task_id"]
            if task_id in updated_tasks:
                missing = issue["missing"]
                old_deps = updated_tasks[task_id].dependencies.copy()
                updated_tasks[task_id].dependencies = [
                    dep for dep in old_deps if dep not in missing
                ]
                fix_report["fixed_issues"].append(
                    f"Removed missing dependencies from task {task_id}: {', '.join(missing)}"
                )
                for dep_id in missing:
                    fix_report["removed_dependencies"].append({
                        "task_id": task_id,
                        "dependency_id": dep_id,
                        "reason": "missing_dependency"
                    })
                fix_report["changes_made"] = True
        
        # Fix circular dependencies
        if validation.get("circular_dependencies"):
            # This is more complex - we need to break cycles
            # For each cycle, remove the last dependency in the chain
            for cycle in validation["circular_dependencies"]:
                cycle_parts = cycle.split(" -> ")
                if len(cycle_parts) >= 2:
                    dependent_id = cycle_parts[-2]
                    dependency_id = cycle_parts[-1]
                    
                    if dependent_id in updated_tasks:
                        old_deps = updated_tasks[dependent_id].dependencies.copy()
                        if dependency_id in old_deps:
                            updated_tasks[dependent_id].dependencies = [
                                dep for dep in old_deps if dep != dependency_id
                            ]
                            fix_report["fixed_issues"].append(
                                f"Broke circular dependency by removing {dependency_id} from {dependent_id}'s dependencies"
                            )
                            fix_report["removed_dependencies"].append({
                                "task_id": dependent_id,
                                "dependency_id": dependency_id,
                                "reason": "circular_dependency"
                            })
                            fix_report["changes_made"] = True
        
        return updated_tasks, fix_report
    
    @staticmethod
    def get_dependency_chain(tasks: Dict[str, Task], task_id: str) -> Dict[str, Any]:
        """
        Get the full dependency chain for a task, organized by levels.
        
        Args:
            tasks: Dictionary of all tasks
            task_id: ID of the task to analyze
            
        Returns:
            Dictionary with dependency chain information
        """
        if task_id not in tasks:
            return {
                "task_id": task_id,
                "exists": False,
                "chain": [],
                "levels": []
            }
        
        # Initialize result
        result = {
            "task_id": task_id,
            "exists": True,
            "chain": [],
            "levels": []
        }
        
        # Set to track visited tasks to avoid cycles
        visited = set()
        
        # Function to recursively build dependency levels
        def build_levels(current_id: str, level: int = 0) -> None:
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            # Ensure we have enough levels
            while len(result["levels"]) <= level:
                result["levels"].append([])
            
            # Add task to current level
            if current_id in tasks:
                task = tasks[current_id]
                result["levels"][level].append({
                    "id": current_id,
                    "title": task.title,
                    "status": task.status.value,
                    "dependencies": task.dependencies
                })
                
                # Add to chain if not already present
                if current_id not in result["chain"]:
                    result["chain"].append(current_id)
                
                # Process dependencies
                for dep_id in task.dependencies:
                    build_levels(dep_id, level + 1)
        
        # Build levels starting from the target task
        build_levels(task_id)
        
        return result
    
    @staticmethod
    def find_blocked_tasks(tasks: Dict[str, Task]) -> List[Dict[str, Any]]:
        """
        Find tasks that are blocked by incomplete dependencies.
        
        Args:
            tasks: Dictionary of all tasks
            
        Returns:
            List of blocked tasks with their blockers
        """
        blocked_tasks = []
        
        for task_id, task in tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
                
            blockers = []
            for dep_id in task.dependencies:
                if dep_id in tasks and tasks[dep_id].status != TaskStatus.DONE:
                    blockers.append({
                        "id": dep_id,
                        "title": tasks[dep_id].title,
                        "status": tasks[dep_id].status.value
                    })
            
            if blockers:
                blocked_tasks.append({
                    "id": task_id,
                    "title": task.title,
                    "blockers": blockers
                })
        
        return blocked_tasks
    
    @staticmethod
    def get_dependent_tasks(tasks: Dict[str, Task], task_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks that depend on the specified task.
        
        Args:
            tasks: Dictionary of all tasks
            task_id: ID of the task to find dependents for
            
        Returns:
            List of dependent tasks
        """
        dependents = []
        
        for dependent_id, dependent in tasks.items():
            if task_id in dependent.dependencies:
                dependents.append({
                    "id": dependent_id,
                    "title": dependent.title,
                    "status": dependent.status.value
                })
        
        return dependents
