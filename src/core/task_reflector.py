"""
Task Reflector for Tascade AI.

This module provides functionality for reflecting on tasks and their execution,
generating insights, and improving task management through analysis.

Inspired by the task reflection system in mcp-shrimp-task-manager.
"""

from typing import Dict, List, Optional, Any, Union
from .models import Task, TaskStatus
from .ai_providers.base import BaseAIProvider
from datetime import datetime
import json

class TaskReflector:
    """
    Reflects on tasks and their execution to generate insights.
    
    This class provides methods for analyzing task execution patterns,
    generating insights, and improving task management through reflection.
    """
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize the TaskReflector.
        
        Args:
            ai_provider: Optional AI provider for enhanced reflection capabilities
        """
        self.ai_provider = ai_provider
    
    def reflect_on_task(self, task: Task) -> Dict[str, Any]:
        """
        Reflect on a task and generate insights.
        
        Args:
            task: The task to reflect on
            
        Returns:
            Dictionary with reflection results
        """
        # Initialize reflection result
        reflection = {
            "task_id": task.id,
            "task_title": task.title,
            "reflection_time": datetime.now().isoformat(),
            "insights": [],
            "recommendations": [],
            "patterns": [],
            "metrics": {}
        }
        
        # If the task is not completed, reflection is limited
        if task.status != TaskStatus.DONE:
            reflection["insights"].append(
                "Task is not yet completed. Full reflection will be available after completion."
            )
            return reflection
        
        # Basic reflection without AI
        if not task.execution_context:
            reflection["insights"].append(
                "No execution data available for this task. Consider using task execution tracking in the future."
            )
            return reflection
        
        # Extract metrics from execution context
        if "metrics" in task.execution_context:
            reflection["metrics"] = task.execution_context["metrics"]
            
            # Add insights based on metrics
            if "time_spent" in task.execution_context["metrics"]:
                time_spent = task.execution_context["metrics"]["time_spent"]
                reflection["insights"].append(
                    f"Task took {time_spent} seconds to complete."
                )
                
                # Compare with complexity score if available
                if task.complexity_score is not None:
                    expected_time = task.complexity_score * 600  # Simple heuristic: 10 minutes per complexity point
                    if time_spent > expected_time * 1.5:
                        reflection["insights"].append(
                            f"Task took longer than expected based on its complexity score. "
                            f"Expected around {expected_time} seconds, took {time_spent} seconds."
                        )
                        reflection["recommendations"].append(
                            "Consider breaking down similar tasks into smaller subtasks in the future."
                        )
                    elif time_spent < expected_time * 0.5:
                        reflection["insights"].append(
                            f"Task was completed faster than expected based on its complexity score. "
                            f"Expected around {expected_time} seconds, took {time_spent} seconds."
                        )
                        reflection["recommendations"].append(
                            "The complexity score for similar tasks might be overestimated."
                        )
        
        # Extract patterns from execution logs
        if "logs" in task.execution_context:
            logs = task.execution_context["logs"]
            
            # Look for patterns in logs
            error_count = sum(1 for log in logs if log.get("level") == "error")
            if error_count > 0:
                reflection["patterns"].append({
                    "type": "errors",
                    "count": error_count,
                    "description": f"Task encountered {error_count} errors during execution."
                })
                reflection["recommendations"].append(
                    "Review error handling for similar tasks to reduce errors."
                )
            
            # Check for long pauses between log entries
            if len(logs) > 1:
                logs_with_time = [log for log in logs if "time" in log]
                if len(logs_with_time) > 1:
                    logs_with_time.sort(key=lambda x: x["time"])
                    
                    long_pauses = []
                    for i in range(1, len(logs_with_time)):
                        try:
                            time1 = datetime.fromisoformat(logs_with_time[i-1]["time"])
                            time2 = datetime.fromisoformat(logs_with_time[i]["time"])
                            pause = (time2 - time1).total_seconds()
                            
                            if pause > 300:  # 5 minutes
                                long_pauses.append({
                                    "start": logs_with_time[i-1]["time"],
                                    "end": logs_with_time[i]["time"],
                                    "duration": pause,
                                    "before_message": logs_with_time[i-1].get("message", ""),
                                    "after_message": logs_with_time[i].get("message", "")
                                })
                        except (ValueError, TypeError):
                            continue
                    
                    if long_pauses:
                        reflection["patterns"].append({
                            "type": "long_pauses",
                            "count": len(long_pauses),
                            "pauses": long_pauses,
                            "description": f"Task had {len(long_pauses)} long pauses (>5 min) during execution."
                        })
                        reflection["recommendations"].append(
                            "Consider breaking down tasks at points where long pauses occurred."
                        )
        
        # Use AI provider for enhanced reflection if available
        if self.ai_provider:
            try:
                ai_reflection = self._generate_ai_reflection(task)
                
                # Merge AI insights with basic insights
                if "insights" in ai_reflection:
                    reflection["insights"].extend(ai_reflection["insights"])
                
                if "recommendations" in ai_reflection:
                    reflection["recommendations"].extend(ai_reflection["recommendations"])
                
                if "patterns" in ai_reflection:
                    reflection["patterns"].extend(ai_reflection["patterns"])
                
            except Exception as e:
                reflection["insights"].append(
                    f"Error generating AI reflection: {str(e)}"
                )
        
        return reflection
    
    def _generate_ai_reflection(self, task: Task) -> Dict[str, Any]:
        """
        Generate task reflection using AI.
        
        Args:
            task: The task to reflect on
            
        Returns:
            Dictionary with AI-generated reflection
        """
        if not self.ai_provider:
            return {}
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "complexity_score": task.complexity_score,
            "execution_context": task.execution_context
        }
        
        # Create prompt for AI
        prompt = f"""
        Reflect on the following completed task and provide insights, patterns, and recommendations:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Analyze the execution patterns, time spent, and any issues encountered.
        Identify what went well and what could be improved.
        Suggest recommendations for similar tasks in the future.
        
        Provide your reflection as a JSON object with the following structure:
        {{
            "insights": ["insight1", "insight2", ...],
            "patterns": [
                {{
                    "type": "pattern_type",
                    "description": "pattern_description",
                    "significance": "high/medium/low"
                }},
                ...
            ],
            "recommendations": ["recommendation1", "recommendation2", ...]
        }}
        """
        
        # Get reflection from AI provider
        system_prompt = "You are an expert task analyst. Analyze the task execution data and provide insightful reflection."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"insights": ["Could not parse AI reflection as JSON."]}
        except json.JSONDecodeError:
            return {"insights": ["Could not parse AI reflection as JSON."]}
    
    def reflect_on_project(self, tasks: Dict[str, Task]) -> Dict[str, Any]:
        """
        Reflect on an entire project based on its tasks.
        
        Args:
            tasks: Dictionary of all tasks in the project
            
        Returns:
            Dictionary with project reflection results
        """
        # Initialize project reflection
        reflection = {
            "reflection_time": datetime.now().isoformat(),
            "task_count": len(tasks),
            "completed_tasks": sum(1 for task in tasks.values() if task.status == TaskStatus.DONE),
            "insights": [],
            "patterns": [],
            "recommendations": [],
            "metrics": {}
        }
        
        # Calculate basic metrics
        completed_tasks = [task for task in tasks.values() if task.status == TaskStatus.DONE]
        pending_tasks = [task for task in tasks.values() if task.status == TaskStatus.PENDING]
        in_progress_tasks = [task for task in tasks.values() if task.status == TaskStatus.IN_PROGRESS]
        
        reflection["metrics"]["completion_rate"] = len(completed_tasks) / len(tasks) if tasks else 0
        
        # Calculate average complexity
        tasks_with_complexity = [task for task in tasks.values() if task.complexity_score is not None]
        if tasks_with_complexity:
            avg_complexity = sum(task.complexity_score for task in tasks_with_complexity) / len(tasks_with_complexity)
            reflection["metrics"]["average_complexity"] = avg_complexity
        
        # Calculate average execution time
        tasks_with_time = [
            task for task in completed_tasks
            if task.execution_context 
            and "metrics" in task.execution_context
            and "time_spent" in task.execution_context["metrics"]
        ]
        
        if tasks_with_time:
            avg_time = sum(task.execution_context["metrics"]["time_spent"] for task in tasks_with_time) / len(tasks_with_time)
            reflection["metrics"]["average_execution_time"] = avg_time
        
        # Generate insights
        if reflection["metrics"].get("completion_rate", 0) < 0.3:
            reflection["insights"].append(
                "Project has a low completion rate. Consider re-evaluating task scope or adding resources."
            )
        
        if len(in_progress_tasks) > 3:
            reflection["insights"].append(
                f"There are {len(in_progress_tasks)} tasks in progress simultaneously. "
                "Consider focusing on fewer tasks at a time for better efficiency."
            )
        
        # Identify bottlenecks
        dependency_counts = {}
        for task in tasks.values():
            for dep_id in task.dependencies:
                dependency_counts[dep_id] = dependency_counts.get(dep_id, 0) + 1
        
        bottlenecks = [
            (task_id, count) for task_id, count in dependency_counts.items()
            if count > 2 and task_id in tasks and tasks[task_id].status != TaskStatus.DONE
        ]
        
        if bottlenecks:
            bottleneck_info = []
            for task_id, count in bottlenecks:
                task = tasks[task_id]
                bottleneck_info.append({
                    "id": task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "blocking_count": count
                })
            
            reflection["patterns"].append({
                "type": "bottlenecks",
                "bottlenecks": bottleneck_info,
                "description": f"Identified {len(bottlenecks)} tasks that are blocking multiple other tasks."
            })
            
            reflection["recommendations"].append(
                "Prioritize completing bottleneck tasks to unblock project progress."
            )
        
        # Use AI provider for enhanced project reflection if available
        if self.ai_provider:
            try:
                # Prepare project data for AI
                project_data = {
                    "task_count": len(tasks),
                    "completed_tasks": len(completed_tasks),
                    "pending_tasks": len(pending_tasks),
                    "in_progress_tasks": len(in_progress_tasks),
                    "metrics": reflection["metrics"]
                }
                
                # Create prompt for AI
                prompt = f"""
                Reflect on the following project data and provide insights, patterns, and recommendations:
                
                Project: {json.dumps(project_data, indent=2)}
                
                Analyze the project progress, task completion patterns, and any bottlenecks.
                Identify what is going well and what could be improved.
                Suggest recommendations for improving project management.
                
                Provide your reflection as a JSON object with the following structure:
                {{
                    "insights": ["insight1", "insight2", ...],
                    "patterns": [
                        {{
                            "type": "pattern_type",
                            "description": "pattern_description",
                            "significance": "high/medium/low"
                        }},
                        ...
                    ],
                    "recommendations": ["recommendation1", "recommendation2", ...]
                }}
                """
                
                # Get reflection from AI provider
                system_prompt = "You are an expert project analyst. Analyze the project data and provide insightful reflection."
                response = self.ai_provider.generate_text(prompt, system_prompt)
                
                # Parse response as JSON
                try:
                    # Extract JSON from response
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        ai_reflection = json.loads(json_str)
                        
                        # Merge AI insights with basic insights
                        if "insights" in ai_reflection:
                            reflection["insights"].extend(ai_reflection["insights"])
                        
                        if "recommendations" in ai_reflection:
                            reflection["recommendations"].extend(ai_reflection["recommendations"])
                        
                        if "patterns" in ai_reflection:
                            reflection["patterns"].extend(ai_reflection["patterns"])
                except json.JSONDecodeError:
                    reflection["insights"].append("Could not parse AI project reflection as JSON.")
            except Exception as e:
                reflection["insights"].append(
                    f"Error generating AI project reflection: {str(e)}"
                )
        
        return reflection
