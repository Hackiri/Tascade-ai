"""
Task Executor for Tascade AI.

This module provides functionality for executing tasks with structured guidance,
complexity assessment, and quality requirements.

Inspired by the task execution system in mcp-shrimp-task-manager.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from .models import Task, TaskStatus, TaskPriority
from .ai_providers.base import BaseAIProvider
import json
import logging

class ComplexityAssessment:
    """
    Assessment of task complexity with metrics and recommendations.
    """
    
    def __init__(self, level: str, metrics: Dict[str, Any], recommendations: Optional[List[str]] = None):
        """
        Initialize the ComplexityAssessment.
        
        Args:
            level: Complexity level ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH')
            metrics: Metrics used to determine complexity
            recommendations: Optional recommendations based on complexity
        """
        self.level = level
        self.metrics = metrics
        self.recommendations = recommendations or []

class TaskExecutor:
    """
    Executes tasks with structured guidance and complexity assessment.
    
    This class provides methods for preparing task execution, assessing complexity,
    generating execution plans, and tracking execution progress.
    """
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize the TaskExecutor.
        
        Args:
            ai_provider: Optional AI provider for enhanced execution capabilities
        """
        self.ai_provider = ai_provider
        self.logger = logging.getLogger(__name__)
    
    def assess_complexity(self, task: Task) -> ComplexityAssessment:
        """
        Assess the complexity of a task.
        
        Args:
            task: The task to assess
            
        Returns:
            ComplexityAssessment object with complexity level, metrics, and recommendations
        """
        # Calculate basic metrics
        metrics = {
            "description_length": len(task.description or ""),
            "dependencies_count": len(task.dependencies or []),
            "subtasks_count": len(task.subtasks) if hasattr(task, "subtasks") else 0,
            "implementation_guide_length": len(task.implementation_guide) if hasattr(task, "implementation_guide") and task.implementation_guide else 0,
            "verification_criteria_count": len(task.verification_criteria.split('\n')) if hasattr(task, "verification_criteria") and task.verification_criteria else 0
        }
        
        # Determine complexity level based on metrics
        level = "LOW"
        
        # Use a weighted scoring system
        complexity_score = (
            metrics["description_length"] * 0.01 +
            metrics["dependencies_count"] * 5 +
            metrics["subtasks_count"] * 3 +
            (10 - metrics["implementation_guide_length"] * 0.001) +  # Lower score if good implementation guide
            (10 - metrics["verification_criteria_count"] * 2)  # Lower score if good verification criteria
        )
        
        if complexity_score > 50:
            level = "VERY_HIGH"
        elif complexity_score > 30:
            level = "HIGH"
        elif complexity_score > 15:
            level = "MEDIUM"
        
        # Generate recommendations based on complexity
        recommendations = []
        
        if level == "VERY_HIGH":
            recommendations = [
                "Consider breaking this task into smaller subtasks",
                "Create a detailed implementation guide before starting",
                "Allocate extra time for testing and debugging",
                "Review dependencies carefully before starting"
            ]
        elif level == "HIGH":
            recommendations = [
                "Plan implementation in stages with checkpoints",
                "Identify potential challenges before starting",
                "Consider pair programming or code review"
            ]
        elif level == "MEDIUM":
            recommendations = [
                "Create a basic implementation plan",
                "Test each component as you implement it"
            ]
        
        # If using AI provider, enhance assessment
        if self.ai_provider:
            try:
                enhanced_assessment = self._assess_complexity_with_ai(task, metrics, level)
                return enhanced_assessment
            except Exception as e:
                self.logger.error(f"Error using AI for complexity assessment: {str(e)}")
                # Fall back to basic assessment
        
        return ComplexityAssessment(level, metrics, recommendations)
    
    def _assess_complexity_with_ai(self, task: Task, metrics: Dict[str, Any], 
                                 basic_level: str) -> ComplexityAssessment:
        """
        Enhance complexity assessment using AI.
        
        Args:
            task: The task to assess
            metrics: Basic metrics calculated
            basic_level: Basic complexity level determined
            
        Returns:
            Enhanced ComplexityAssessment
        """
        if not self.ai_provider:
            raise ValueError("No AI provider available for complexity assessment")
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "priority": task.priority.value,
            "status": task.status.value,
            "dependencies": task.dependencies,
            "metrics": metrics,
            "basic_level": basic_level
        }
        
        # Create prompt for AI
        prompt = f"""
        Assess the complexity of the following task:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Please analyze the task complexity and provide:
        1. A complexity level ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH')
        2. Justification for this complexity level
        3. Specific recommendations for handling this complexity
        
        Format your response as a JSON object with the following structure:
        {{
            "level": "COMPLEXITY_LEVEL",
            "justification": "Explanation of why this level was assigned",
            "recommendations": [
                "Specific recommendation 1",
                "Specific recommendation 2",
                ...
            ]
        }}
        """
        
        # Get complexity assessment from AI provider
        system_prompt = "You are an expert task complexity analyst. Evaluate task complexity and provide recommendations."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                assessment_data = json.loads(json_str)
                
                # Create enhanced assessment
                level = assessment_data.get("level", basic_level)
                recommendations = assessment_data.get("recommendations", [])
                
                # Add justification as a metric
                metrics["ai_justification"] = assessment_data.get("justification", "")
                
                return ComplexityAssessment(level, metrics, recommendations)
            else:
                raise ValueError("Could not extract JSON from AI response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")
    
    def prepare_execution(self, task: Task, related_tasks: Optional[Dict[str, Task]] = None) -> Dict[str, Any]:
        """
        Prepare for task execution by gathering all necessary information.
        
        Args:
            task: The task to execute
            related_tasks: Optional dictionary of related tasks (e.g., dependencies)
            
        Returns:
            Dictionary with execution preparation information
        """
        # Assess task complexity
        complexity_assessment = self.assess_complexity(task)
        
        # Get dependency tasks
        dependency_tasks = []
        if task.dependencies and related_tasks:
            for dep_id in task.dependencies:
                if dep_id in related_tasks:
                    dependency_tasks.append(related_tasks[dep_id])
        
        # Generate execution guidance
        execution_guidance = self._generate_execution_guidance(task, complexity_assessment, dependency_tasks)
        
        # Prepare execution context
        execution_context = {
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "complexity_assessment": {
                "level": complexity_assessment.level,
                "metrics": complexity_assessment.metrics,
                "recommendations": complexity_assessment.recommendations
            },
            "dependency_tasks": [dep.id for dep in dependency_tasks],
            "execution_guidance": execution_guidance,
            "steps": [],
            "logs": []
        }
        
        # Store execution context in task
        if not hasattr(task, "execution_context") or not task.execution_context:
            task.execution_context = {}
        
        task.execution_context.update(execution_context)
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        
        return {
            "task_id": task.id,
            "complexity_assessment": execution_context["complexity_assessment"],
            "execution_guidance": execution_guidance,
            "dependency_tasks": execution_context["dependency_tasks"]
        }
    
    def _generate_execution_guidance(self, task: Task, complexity_assessment: ComplexityAssessment,
                                   dependency_tasks: List[Task]) -> Dict[str, Any]:
        """
        Generate execution guidance for a task.
        
        Args:
            task: The task to generate guidance for
            complexity_assessment: Complexity assessment for the task
            dependency_tasks: List of dependency tasks
            
        Returns:
            Dictionary with execution guidance
        """
        # Basic execution steps
        execution_steps = [
            {
                "step": "Analyze Requirements",
                "description": "Understand task requirements and constraints",
                "tips": [
                    "Read the task description thoroughly",
                    "Identify key requirements and deliverables",
                    "Note any constraints or limitations"
                ]
            },
            {
                "step": "Design Solution",
                "description": "Develop implementation plan and testing strategy",
                "tips": [
                    "Break down the task into smaller components",
                    "Consider alternative approaches",
                    "Plan how to test the implementation"
                ]
            },
            {
                "step": "Implement Solution",
                "description": "Execute according to plan, handle edge cases",
                "tips": [
                    "Follow the implementation guide if available",
                    "Handle error cases and exceptions",
                    "Document your code as you write it"
                ]
            },
            {
                "step": "Test and Verify",
                "description": "Ensure functionality correctness and robustness",
                "tips": [
                    "Test against the verification criteria",
                    "Verify edge cases and error handling",
                    "Check for any performance issues"
                ]
            }
        ]
        
        # Quality requirements
        quality_requirements = [
            {
                "requirement": "Scope Management",
                "description": "Only modify relevant code, avoid feature creep",
                "importance": "High"
            },
            {
                "requirement": "Code Quality",
                "description": "Comply with coding standards, handle exceptions",
                "importance": "High"
            },
            {
                "requirement": "Performance Considerations",
                "description": "Pay attention to algorithm efficiency and resource usage",
                "importance": "Medium"
            }
        ]
        
        # Add complexity-specific guidance
        if complexity_assessment.level == "VERY_HIGH":
            execution_steps.insert(1, {
                "step": "Break Down Task",
                "description": "Split the task into smaller, manageable subtasks",
                "tips": [
                    "Identify logical components that can be implemented separately",
                    "Create a dependency graph for subtasks",
                    "Prioritize subtasks based on dependencies"
                ]
            })
            
            quality_requirements.append({
                "requirement": "Risk Management",
                "description": "Identify and mitigate high-risk components early",
                "importance": "Very High"
            })
        elif complexity_assessment.level == "HIGH":
            quality_requirements.append({
                "requirement": "Incremental Testing",
                "description": "Test each component as it's implemented",
                "importance": "High"
            })
        
        # If using AI provider, enhance guidance
        if self.ai_provider:
            try:
                enhanced_guidance = self._generate_execution_guidance_with_ai(task, complexity_assessment, dependency_tasks)
                return enhanced_guidance
            except Exception as e:
                self.logger.error(f"Error using AI for execution guidance: {str(e)}")
                # Fall back to basic guidance
        
        return {
            "execution_steps": execution_steps,
            "quality_requirements": quality_requirements,
            "complexity_recommendations": complexity_assessment.recommendations
        }
    
    def _generate_execution_guidance_with_ai(self, task: Task, complexity_assessment: ComplexityAssessment,
                                          dependency_tasks: List[Task]) -> Dict[str, Any]:
        """
        Generate enhanced execution guidance using AI.
        
        Args:
            task: The task to generate guidance for
            complexity_assessment: Complexity assessment for the task
            dependency_tasks: List of dependency tasks
            
        Returns:
            Dictionary with enhanced execution guidance
        """
        if not self.ai_provider:
            raise ValueError("No AI provider available for execution guidance")
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "priority": task.priority.value,
            "status": task.status.value,
            "dependencies": task.dependencies,
            "implementation_guide": task.implementation_guide if hasattr(task, "implementation_guide") else None,
            "verification_criteria": task.verification_criteria if hasattr(task, "verification_criteria") else None
        }
        
        # Prepare complexity assessment data
        complexity_data = {
            "level": complexity_assessment.level,
            "metrics": complexity_assessment.metrics,
            "recommendations": complexity_assessment.recommendations
        }
        
        # Prepare dependency tasks data
        dependency_data = []
        for dep_task in dependency_tasks:
            dependency_data.append({
                "id": dep_task.id,
                "title": dep_task.title,
                "status": dep_task.status.value
            })
        
        # Create prompt for AI
        prompt = f"""
        Generate execution guidance for the following task:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Complexity Assessment: {json.dumps(complexity_data, indent=2)}
        
        Dependency Tasks: {json.dumps(dependency_data, indent=2)}
        
        Please provide comprehensive execution guidance including:
        1. Detailed execution steps with descriptions and tips
        2. Quality requirements with importance levels
        3. Task-specific recommendations
        
        Format your response as a JSON object with the following structure:
        {{
            "execution_steps": [
                {{
                    "step": "Step Name",
                    "description": "Step description",
                    "tips": ["Tip 1", "Tip 2", ...]
                }},
                ...
            ],
            "quality_requirements": [
                {{
                    "requirement": "Requirement Name",
                    "description": "Requirement description",
                    "importance": "High/Medium/Low"
                }},
                ...
            ],
            "task_specific_recommendations": [
                "Recommendation 1",
                "Recommendation 2",
                ...
            ]
        }}
        """
        
        # Get execution guidance from AI provider
        system_prompt = "You are an expert task execution specialist. Provide detailed, actionable guidance for executing tasks."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                guidance_data = json.loads(json_str)
                
                # Ensure all required fields are present
                if "execution_steps" not in guidance_data:
                    guidance_data["execution_steps"] = []
                
                if "quality_requirements" not in guidance_data:
                    guidance_data["quality_requirements"] = []
                
                # Rename task_specific_recommendations to complexity_recommendations for consistency
                if "task_specific_recommendations" in guidance_data:
                    guidance_data["complexity_recommendations"] = guidance_data.pop("task_specific_recommendations")
                else:
                    guidance_data["complexity_recommendations"] = complexity_assessment.recommendations
                
                return guidance_data
            else:
                raise ValueError("Could not extract JSON from AI response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")
    
    def log_execution_step(self, task: Task, step_name: str, status: str, 
                         details: Optional[str] = None) -> Dict[str, Any]:
        """
        Log an execution step for a task.
        
        Args:
            task: The task being executed
            step_name: Name of the execution step
            status: Status of the step ('started', 'completed', 'failed')
            details: Optional details about the step
            
        Returns:
            Dictionary with the logged step information
        """
        if not hasattr(task, "execution_context") or not task.execution_context:
            raise ValueError(f"Task {task.id} is not being executed")
        
        # Create step log
        step_log = {
            "step_name": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        # Add to execution context
        if "steps" not in task.execution_context:
            task.execution_context["steps"] = []
        
        task.execution_context["steps"].append(step_log)
        
        # Add to execution logs
        if "logs" not in task.execution_context:
            task.execution_context["logs"] = []
        
        log_entry = {
            "timestamp": step_log["timestamp"],
            "level": "info",
            "message": f"Step '{step_name}' {status}" + (f": {details}" if details else "")
        }
        
        task.execution_context["logs"].append(log_entry)
        
        return step_log
    
    def complete_execution(self, task: Task, success: bool, 
                         completion_notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete the execution of a task.
        
        Args:
            task: The task being executed
            success: Whether the execution was successful
            completion_notes: Optional notes about the completion
            
        Returns:
            Dictionary with execution summary
        """
        if not hasattr(task, "execution_context") or not task.execution_context:
            raise ValueError(f"Task {task.id} is not being executed")
        
        # Update execution context
        task.execution_context["end_time"] = datetime.now().isoformat()
        task.execution_context["status"] = "completed" if success else "failed"
        
        if completion_notes:
            task.execution_context["completion_notes"] = completion_notes
        
        # Calculate execution duration
        start_time = datetime.fromisoformat(task.execution_context["start_time"])
        end_time = datetime.fromisoformat(task.execution_context["end_time"])
        duration_seconds = (end_time - start_time).total_seconds()
        
        task.execution_context["metrics"] = {
            "duration_seconds": duration_seconds,
            "steps_completed": len([s for s in task.execution_context.get("steps", []) if s["status"] == "completed"]),
            "total_steps": len(task.execution_context.get("steps", []))
        }
        
        # Update task status
        task.status = TaskStatus.DONE if success else TaskStatus.FAILED
        
        # Generate execution summary
        execution_summary = {
            "task_id": task.id,
            "success": success,
            "duration": duration_seconds,
            "steps_completed": task.execution_context["metrics"]["steps_completed"],
            "total_steps": task.execution_context["metrics"]["total_steps"],
            "completion_notes": completion_notes
        }
        
        # Add to execution logs
        if "logs" not in task.execution_context:
            task.execution_context["logs"] = []
        
        log_level = "info" if success else "error"
        log_message = f"Task execution {'completed successfully' if success else 'failed'}"
        if completion_notes:
            log_message += f": {completion_notes}"
        
        log_entry = {
            "timestamp": task.execution_context["end_time"],
            "level": log_level,
            "message": log_message
        }
        
        task.execution_context["logs"].append(log_entry)
        
        return execution_summary
    
    def get_execution_status(self, task: Task) -> Dict[str, Any]:
        """
        Get the current execution status of a task.
        
        Args:
            task: The task to get status for
            
        Returns:
            Dictionary with execution status information
        """
        if not hasattr(task, "execution_context") or not task.execution_context:
            return {
                "task_id": task.id,
                "status": "not_started",
                "message": "Task execution has not started"
            }
        
        # Get execution status
        status = task.execution_context.get("status", "unknown")
        
        # Get current step (last step in the steps list)
        current_step = None
        steps = task.execution_context.get("steps", [])
        if steps:
            current_step = steps[-1]
        
        # Calculate progress percentage
        progress = 0
        total_steps = task.execution_context.get("metrics", {}).get("total_steps", 0)
        steps_completed = task.execution_context.get("metrics", {}).get("steps_completed", 0)
        
        if total_steps > 0:
            progress = (steps_completed / total_steps) * 100
        
        # Get execution duration
        duration = None
        if "start_time" in task.execution_context:
            start_time = datetime.fromisoformat(task.execution_context["start_time"])
            
            if "end_time" in task.execution_context:
                end_time = datetime.fromisoformat(task.execution_context["end_time"])
                duration = (end_time - start_time).total_seconds()
            else:
                duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "task_id": task.id,
            "status": status,
            "current_step": current_step,
            "progress": progress,
            "duration_seconds": duration,
            "steps_completed": steps_completed,
            "total_steps": total_steps
        }
