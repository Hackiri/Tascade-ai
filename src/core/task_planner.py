"""
Task Planner for Tascade AI.

This module provides functionality for generating detailed execution plans for tasks,
including step-by-step instructions, resource requirements, and risk assessments.

Inspired by the task planning system in mcp-shrimp-task-manager.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from .models import Task, TaskStatus, TaskPriority
from .ai_providers.base import BaseAIProvider
import json

class TaskPlanner:
    """
    Generates detailed execution plans for tasks.
    
    This class provides methods for creating structured execution plans,
    including step-by-step instructions, resource requirements, risk assessments,
    and estimated timelines.
    """
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize the TaskPlanner.
        
        Args:
            ai_provider: Optional AI provider for enhanced planning capabilities
        """
        self.ai_provider = ai_provider
    
    def generate_execution_plan(self, task: Task, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a detailed execution plan for a task.
        
        Args:
            task: The task to generate a plan for
            context: Optional context information (e.g., project constraints, team skills)
            
        Returns:
            Dictionary containing the execution plan
        """
        # If using AI provider for enhanced planning
        if self.ai_provider:
            try:
                return self._generate_plan_with_ai(task, context)
            except Exception as e:
                print(f"Error using AI provider for task planning: {str(e)}")
                # Fall back to heuristic planning if AI fails
        
        # Heuristic-based planning (fallback)
        return self._generate_plan_heuristic(task, context)
    
    def _generate_plan_with_ai(self, task: Task, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a task execution plan using AI.
        
        Args:
            task: The task to generate a plan for
            context: Optional context information
            
        Returns:
            Dictionary containing the execution plan
        """
        if not self.ai_provider:
            raise ValueError("No AI provider available for task planning")
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "priority": task.priority.value,
            "status": task.status.value,
            "dependencies": task.dependencies,
            "complexity_score": task.complexity_score if hasattr(task, "complexity_score") else None,
            "implementation_guide": task.implementation_guide if hasattr(task, "implementation_guide") else None,
            "verification_criteria": task.verification_criteria if hasattr(task, "verification_criteria") else None
        }
        
        # Prepare context data
        context_data = context or {}
        
        # Create prompt for AI
        prompt = f"""
        Generate a detailed execution plan for the following task:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Context: {json.dumps(context_data, indent=2) if context_data else "No additional context provided"}
        
        Please provide a comprehensive execution plan that includes:
        1. A step-by-step breakdown of the implementation process
        2. Required resources and dependencies
        3. Risk assessment and mitigation strategies
        4. Timeline estimates for each step
        5. Key checkpoints and validation criteria
        
        Format your response as a JSON object with the following structure:
        {{
            "steps": [
                {{
                    "step_number": 1,
                    "title": "Step title",
                    "description": "Detailed description of the step",
                    "estimated_duration": "2h", // Estimated duration in hours
                    "resources_required": ["Resource 1", "Resource 2"],
                    "validation_criteria": "How to validate this step is complete",
                    "risks": [
                        {{
                            "description": "Risk description",
                            "probability": "high/medium/low",
                            "impact": "high/medium/low",
                            "mitigation": "Mitigation strategy"
                        }}
                    ]
                }}
            ],
            "total_estimated_duration": "8h", // Total estimated duration in hours
            "key_dependencies": ["Dependency 1", "Dependency 2"],
            "critical_path_steps": [1, 3, 5], // Step numbers that are on the critical path
            "recommended_approach": "Overall recommended approach",
            "success_criteria": "Overall success criteria for the task"
        }}
        """
        
        # Get execution plan from AI provider
        system_prompt = "You are an expert task planning specialist. Create detailed, actionable execution plans for tasks."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan = json.loads(json_str)
                
                # Add metadata
                plan["generated_at"] = datetime.now().isoformat()
                plan["generated_by"] = "AI"
                
                return plan
            else:
                raise ValueError("Could not extract JSON from AI response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")
    
    def _generate_plan_heuristic(self, task: Task, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a task execution plan using heuristic methods.
        
        Args:
            task: The task to generate a plan for
            context: Optional context information
            
        Returns:
            Dictionary containing the execution plan
        """
        # Simple heuristic planning based on task type and complexity
        
        # Determine task type based on title/description
        task_type = "development"  # Default
        if task.title:
            title_lower = task.title.lower()
            if "design" in title_lower or "architecture" in title_lower:
                task_type = "design"
            elif "test" in title_lower or "qa" in title_lower:
                task_type = "testing"
            elif "document" in title_lower or "doc" in title_lower:
                task_type = "documentation"
            elif "research" in title_lower or "investigate" in title_lower:
                task_type = "research"
        
        # Determine complexity (1-10 scale)
        complexity = getattr(task, "complexity_score", 5)
        if complexity is None:
            complexity = 5  # Default medium complexity
        
        # Generate steps based on task type
        steps = []
        
        if task_type == "design":
            steps = [
                {
                    "step_number": 1,
                    "title": "Requirements Analysis",
                    "description": "Analyze and document all requirements for the design",
                    "estimated_duration": f"{max(1, int(complexity * 0.5))}h",
                    "resources_required": ["Requirements documentation", "Stakeholder input"],
                    "validation_criteria": "All requirements are documented and prioritized",
                    "risks": [
                        {
                            "description": "Incomplete requirements",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Schedule stakeholder review sessions"
                        }
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Initial Design Draft",
                    "description": "Create initial design draft based on requirements",
                    "estimated_duration": f"{max(2, int(complexity * 0.8))}h",
                    "resources_required": ["Design tools", "Reference materials"],
                    "validation_criteria": "Design draft covers all requirements",
                    "risks": [
                        {
                            "description": "Design conflicts with existing systems",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Review existing system architecture"
                        }
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Design Review",
                    "description": "Conduct design review with stakeholders",
                    "estimated_duration": f"{max(1, int(complexity * 0.3))}h",
                    "resources_required": ["Stakeholder availability", "Design documentation"],
                    "validation_criteria": "Design is approved by all stakeholders",
                    "risks": [
                        {
                            "description": "Stakeholder disagreement",
                            "probability": "medium",
                            "impact": "medium",
                            "mitigation": "Prepare alternative design options"
                        }
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Final Design Documentation",
                    "description": "Finalize design documentation based on review feedback",
                    "estimated_duration": f"{max(1, int(complexity * 0.4))}h",
                    "resources_required": ["Design tools", "Review feedback"],
                    "validation_criteria": "Design documentation is complete and addresses all feedback",
                    "risks": [
                        {
                            "description": "Missed implementation details",
                            "probability": "low",
                            "impact": "medium",
                            "mitigation": "Use design checklist for completeness"
                        }
                    ]
                }
            ]
        elif task_type == "development":
            steps = [
                {
                    "step_number": 1,
                    "title": "Setup Development Environment",
                    "description": "Prepare development environment and tools",
                    "estimated_duration": "1h",
                    "resources_required": ["Development tools", "Access credentials"],
                    "validation_criteria": "Environment is ready for development",
                    "risks": [
                        {
                            "description": "Environment configuration issues",
                            "probability": "low",
                            "impact": "medium",
                            "mitigation": "Document environment setup process"
                        }
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Implement Core Functionality",
                    "description": "Develop the core functionality of the task",
                    "estimated_duration": f"{max(2, int(complexity * 1.0))}h",
                    "resources_required": ["Development tools", "Design documentation"],
                    "validation_criteria": "Core functionality works as expected",
                    "risks": [
                        {
                            "description": "Technical challenges",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Research potential solutions in advance"
                        }
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Write Unit Tests",
                    "description": "Create unit tests for the implemented functionality",
                    "estimated_duration": f"{max(1, int(complexity * 0.6))}h",
                    "resources_required": ["Testing framework", "Test data"],
                    "validation_criteria": "Tests cover all critical functionality",
                    "risks": [
                        {
                            "description": "Insufficient test coverage",
                            "probability": "medium",
                            "impact": "medium",
                            "mitigation": "Use code coverage tools"
                        }
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Code Review",
                    "description": "Submit code for review and address feedback",
                    "estimated_duration": f"{max(1, int(complexity * 0.4))}h",
                    "resources_required": ["Code review tools", "Reviewer availability"],
                    "validation_criteria": "Code passes review with no major issues",
                    "risks": [
                        {
                            "description": "Delayed review",
                            "probability": "medium",
                            "impact": "low",
                            "mitigation": "Schedule review in advance"
                        }
                    ]
                },
                {
                    "step_number": 5,
                    "title": "Integration Testing",
                    "description": "Test integration with other components",
                    "estimated_duration": f"{max(1, int(complexity * 0.5))}h",
                    "resources_required": ["Test environment", "Integration test suite"],
                    "validation_criteria": "Integration tests pass successfully",
                    "risks": [
                        {
                            "description": "Integration issues",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Test with mock components first"
                        }
                    ]
                }
            ]
        elif task_type == "testing":
            steps = [
                {
                    "step_number": 1,
                    "title": "Test Plan Creation",
                    "description": "Create a comprehensive test plan",
                    "estimated_duration": f"{max(1, int(complexity * 0.5))}h",
                    "resources_required": ["Requirements documentation", "Design documentation"],
                    "validation_criteria": "Test plan covers all requirements",
                    "risks": [
                        {
                            "description": "Incomplete requirements understanding",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Review requirements with stakeholders"
                        }
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Test Case Development",
                    "description": "Develop detailed test cases",
                    "estimated_duration": f"{max(2, int(complexity * 0.8))}h",
                    "resources_required": ["Test management tools", "Test data"],
                    "validation_criteria": "Test cases cover all functionality",
                    "risks": [
                        {
                            "description": "Missing edge cases",
                            "probability": "medium",
                            "impact": "medium",
                            "mitigation": "Use boundary analysis techniques"
                        }
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Test Execution",
                    "description": "Execute all test cases",
                    "estimated_duration": f"{max(2, int(complexity * 0.7))}h",
                    "resources_required": ["Test environment", "Test data"],
                    "validation_criteria": "All test cases executed with results documented",
                    "risks": [
                        {
                            "description": "Environment issues",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Prepare backup test environment"
                        }
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Defect Reporting",
                    "description": "Document and report any defects found",
                    "estimated_duration": f"{max(1, int(complexity * 0.3))}h",
                    "resources_required": ["Defect tracking system"],
                    "validation_criteria": "All defects are documented with clear reproduction steps",
                    "risks": [
                        {
                            "description": "Unclear defect reports",
                            "probability": "low",
                            "impact": "medium",
                            "mitigation": "Use defect report template"
                        }
                    ]
                }
            ]
        elif task_type == "documentation":
            steps = [
                {
                    "step_number": 1,
                    "title": "Information Gathering",
                    "description": "Gather all necessary information for documentation",
                    "estimated_duration": f"{max(1, int(complexity * 0.5))}h",
                    "resources_required": ["Subject matter experts", "Existing documentation"],
                    "validation_criteria": "All required information is collected",
                    "risks": [
                        {
                            "description": "Incomplete information",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Create information checklist"
                        }
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Draft Documentation",
                    "description": "Create initial documentation draft",
                    "estimated_duration": f"{max(2, int(complexity * 0.8))}h",
                    "resources_required": ["Documentation tools", "Style guide"],
                    "validation_criteria": "Draft covers all required topics",
                    "risks": [
                        {
                            "description": "Technical inaccuracies",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Regular review with subject matter experts"
                        }
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Documentation Review",
                    "description": "Review documentation for accuracy and completeness",
                    "estimated_duration": f"{max(1, int(complexity * 0.4))}h",
                    "resources_required": ["Reviewer availability", "Review checklist"],
                    "validation_criteria": "Documentation passes review with no major issues",
                    "risks": [
                        {
                            "description": "Delayed review",
                            "probability": "medium",
                            "impact": "low",
                            "mitigation": "Schedule review in advance"
                        }
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Finalize Documentation",
                    "description": "Incorporate review feedback and finalize documentation",
                    "estimated_duration": f"{max(1, int(complexity * 0.3))}h",
                    "resources_required": ["Documentation tools", "Review feedback"],
                    "validation_criteria": "Documentation is complete and addresses all feedback",
                    "risks": [
                        {
                            "description": "Formatting issues",
                            "probability": "low",
                            "impact": "low",
                            "mitigation": "Use documentation templates"
                        }
                    ]
                }
            ]
        elif task_type == "research":
            steps = [
                {
                    "step_number": 1,
                    "title": "Define Research Questions",
                    "description": "Clearly define the research questions and objectives",
                    "estimated_duration": f"{max(1, int(complexity * 0.3))}h",
                    "resources_required": ["Project requirements", "Stakeholder input"],
                    "validation_criteria": "Research questions are clearly defined and agreed upon",
                    "risks": [
                        {
                            "description": "Scope creep",
                            "probability": "high",
                            "impact": "high",
                            "mitigation": "Document and get sign-off on research scope"
                        }
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Information Gathering",
                    "description": "Gather information from various sources",
                    "estimated_duration": f"{max(2, int(complexity * 1.0))}h",
                    "resources_required": ["Access to information sources", "Research tools"],
                    "validation_criteria": "Sufficient information is gathered to address research questions",
                    "risks": [
                        {
                            "description": "Limited information availability",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Identify alternative information sources"
                        }
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Analysis",
                    "description": "Analyze gathered information",
                    "estimated_duration": f"{max(2, int(complexity * 0.8))}h",
                    "resources_required": ["Analysis tools", "Gathered information"],
                    "validation_criteria": "Analysis provides clear insights",
                    "risks": [
                        {
                            "description": "Inconclusive results",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Define analysis methodology in advance"
                        }
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Research Report",
                    "description": "Create a comprehensive research report",
                    "estimated_duration": f"{max(1, int(complexity * 0.6))}h",
                    "resources_required": ["Documentation tools", "Analysis results"],
                    "validation_criteria": "Report addresses all research questions with clear conclusions",
                    "risks": [
                        {
                            "description": "Unclear conclusions",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Use structured reporting format"
                        }
                    ]
                }
            ]
        
        # Calculate total duration
        total_hours = sum(int(step["estimated_duration"].replace("h", "")) for step in steps)
        
        # Determine critical path (all steps for simple heuristic)
        critical_path = list(range(1, len(steps) + 1))
        
        # Build the execution plan
        plan = {
            "steps": steps,
            "total_estimated_duration": f"{total_hours}h",
            "key_dependencies": task.dependencies if task.dependencies else [],
            "critical_path_steps": critical_path,
            "recommended_approach": f"Follow the steps sequentially, focusing on quality at each stage.",
            "success_criteria": "All steps completed successfully with validation criteria met.",
            "generated_at": datetime.now().isoformat(),
            "generated_by": "Heuristic"
        }
        
        return plan
    
    def estimate_completion_date(self, task: Task, execution_plan: Dict[str, Any], 
                                start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Estimate the completion date for a task based on its execution plan.
        
        Args:
            task: The task to estimate
            execution_plan: The execution plan for the task
            start_date: Optional start date (defaults to current date/time)
            
        Returns:
            Dictionary with estimated dates for each step and overall completion
        """
        if not start_date:
            start_date = datetime.now()
        
        # Extract total duration from execution plan
        total_duration_str = execution_plan.get("total_estimated_duration", "0h")
        try:
            total_hours = int(total_duration_str.replace("h", ""))
        except ValueError:
            total_hours = 0
        
        # Default working hours per day (8 hours)
        working_hours_per_day = 8
        
        # Calculate working days needed
        working_days = total_hours / working_hours_per_day
        
        # Calculate estimated completion date (considering only working days)
        current_date = start_date
        remaining_days = working_days
        
        while remaining_days > 0:
            # Skip weekends (assuming Monday=0, Sunday=6)
            if current_date.weekday() < 5:  # Monday to Friday
                remaining_days -= 1
            
            current_date += timedelta(days=1)
        
        # Calculate step completion dates
        step_dates = {}
        current_date = start_date
        remaining_hours = 0
        
        for step in execution_plan.get("steps", []):
            step_number = step.get("step_number")
            duration_str = step.get("estimated_duration", "0h")
            
            try:
                step_hours = int(duration_str.replace("h", ""))
            except ValueError:
                step_hours = 0
            
            # Add remaining hours from previous step
            step_hours += remaining_hours
            
            # Calculate days needed for this step
            step_days = step_hours // working_hours_per_day
            remaining_hours = step_hours % working_hours_per_day
            
            # Calculate step completion date
            step_date = current_date
            remaining_step_days = step_days
            
            while remaining_step_days > 0:
                # Skip weekends
                if step_date.weekday() < 5:  # Monday to Friday
                    remaining_step_days -= 1
                
                step_date += timedelta(days=1)
            
            # If there are remaining hours but not enough for a full day,
            # add them to the next step instead of extending this step's date
            
            # Store step completion date
            step_dates[step_number] = step_date.isoformat()
            
            # Update current date for next step
            current_date = step_date
        
        # Build the estimation result
        estimation = {
            "task_id": task.id,
            "start_date": start_date.isoformat(),
            "estimated_completion_date": current_date.isoformat(),
            "total_working_days": working_days,
            "total_hours": total_hours,
            "step_completion_dates": step_dates
        }
        
        return estimation
    
    def generate_gantt_chart(self, task: Task, execution_plan: Dict[str, Any], 
                            start_date: Optional[datetime] = None) -> str:
        """
        Generate a Gantt chart for the task execution plan in Mermaid format.
        
        Args:
            task: The task to generate a chart for
            execution_plan: The execution plan for the task
            start_date: Optional start date (defaults to current date/time)
            
        Returns:
            Mermaid Gantt chart as a string
        """
        if not start_date:
            start_date = datetime.now()
        
        # Start building the Mermaid Gantt chart
        gantt_chart = [
            "```mermaid",
            "gantt",
            f"    title Task Execution Plan: {task.title}",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat %m/%d",
            "    excludes weekends",
            ""
        ]
        
        # Add sections for each step
        current_date = start_date
        working_hours_per_day = 8
        
        for step in execution_plan.get("steps", []):
            step_number = step.get("step_number")
            step_title = step.get("title")
            duration_str = step.get("estimated_duration", "0h")
            
            try:
                step_hours = int(duration_str.replace("h", ""))
            except ValueError:
                step_hours = 0
            
            # Calculate days needed for this step
            step_days = max(1, round(step_hours / working_hours_per_day))
            
            # Format dates for Mermaid
            start_date_str = current_date.strftime("%Y-%m-%d")
            
            # Add step to Gantt chart
            gantt_chart.append(f"    Step {step_number}: {step_title} : {start_date_str}, {step_days}d")
            
            # Update current date for next step
            for _ in range(step_days):
                current_date += timedelta(days=1)
                # Skip weekends
                while current_date.weekday() >= 5:  # Saturday or Sunday
                    current_date += timedelta(days=1)
        
        # Close the Mermaid chart
        gantt_chart.append("```")
        
        return "\n".join(gantt_chart)
