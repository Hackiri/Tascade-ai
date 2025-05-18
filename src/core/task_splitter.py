"""
Task Splitter for Tascade AI.

This module provides functionality for splitting complex tasks into smaller, more manageable subtasks.
It uses various decomposition strategies to create optimal task breakdowns.

Inspired by the task splitting system in mcp-shrimp-task-manager.
"""

from typing import Dict, List, Optional, Any, Union
from .models import Task, TaskStatus, TaskPriority
from .ai_providers.base import BaseAIProvider
import json
import uuid
from datetime import datetime

class TaskSplitter:
    """
    Splits complex tasks into smaller, more manageable subtasks.
    
    This class provides methods for decomposing tasks using various strategies,
    including functional decomposition, technical layer decomposition, and
    risk-based decomposition.
    """
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize the TaskSplitter.
        
        Args:
            ai_provider: Optional AI provider for enhanced splitting capabilities
        """
        self.ai_provider = ai_provider
        
        # Define decomposition strategies
        self.strategies = {
            "functional": "Decompose task into independent, testable sub-functions with clear inputs and outputs",
            "technical": "Separate task along architectural layers, ensuring clear interfaces",
            "development_stage": "Prioritize core functionality first, optimization features later",
            "risk_based": "Isolate high-risk parts to reduce overall risk"
        }
    
    def split_task(self, task: Task, strategy: str = "auto", num_subtasks: int = None) -> List[Task]:
        """
        Split a task into subtasks using the specified strategy.
        
        Args:
            task: The task to split
            strategy: Decomposition strategy to use ('functional', 'technical', 'development_stage', 'risk_based', or 'auto')
            num_subtasks: Target number of subtasks (optional)
            
        Returns:
            List of generated subtasks
        """
        if strategy not in self.strategies and strategy != "auto":
            raise ValueError(f"Invalid strategy: {strategy}. Valid strategies are: {', '.join(self.strategies.keys())} or 'auto'")
        
        # If using AI provider for enhanced splitting
        if self.ai_provider:
            try:
                return self._split_task_with_ai(task, strategy, num_subtasks)
            except Exception as e:
                print(f"Error using AI provider for task splitting: {str(e)}")
                # Fall back to heuristic splitting if AI fails
        
        # Heuristic-based splitting (fallback)
        return self._split_task_heuristic(task, strategy, num_subtasks)
    
    def _split_task_with_ai(self, task: Task, strategy: str, num_subtasks: int = None) -> List[Task]:
        """
        Split a task into subtasks using AI.
        
        Args:
            task: The task to split
            strategy: Decomposition strategy to use
            num_subtasks: Target number of subtasks (optional)
            
        Returns:
            List of generated subtasks
        """
        if not self.ai_provider:
            raise ValueError("No AI provider available for task splitting")
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "priority": task.priority.value,
            "complexity_score": task.complexity_score
        }
        
        # Create prompt for AI
        prompt = f"""
        Split the following task into smaller, more manageable subtasks:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Decomposition Strategy: {strategy if strategy != "auto" else "Choose the most appropriate strategy"}
        {f"Target Number of Subtasks: {num_subtasks}" if num_subtasks else ""}
        
        For each subtask, provide:
        1. A clear, concise title
        2. A detailed description
        3. Estimated complexity (1-10 scale)
        4. Dependencies on other subtasks (if any)
        
        Ensure that:
        - Each subtask is atomic and can be completed independently
        - Dependencies form a directed acyclic graph (no circular dependencies)
        - The complete set of subtasks fully covers the original task scope
        
        Provide your response as a JSON array with the following structure:
        [
            {{
                "title": "Subtask Title",
                "description": "Detailed description of the subtask",
                "complexity": <number 1-10>,
                "dependencies": ["Subtask Title 1", "Subtask Title 2"]
            }},
            ...
        ]
        """
        
        # Get subtasks from AI provider
        system_prompt = "You are an expert task decomposition specialist. Break down complex tasks into optimal subtasks."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                subtask_data = json.loads(json_str)
                
                # Convert to Task objects
                subtasks = []
                title_to_id = {}  # Map of titles to IDs for resolving dependencies
                
                # First pass: create tasks with temporary IDs
                for i, data in enumerate(subtask_data):
                    subtask_id = f"{task.id}.{i+1}" if hasattr(task, 'id') else f"subtask_{i+1}"
                    title_to_id[data["title"]] = subtask_id
                    
                    subtask = Task(
                        id=subtask_id,
                        title=data["title"],
                        description=data["description"],
                        priority=task.priority,  # Inherit priority from parent
                        status=TaskStatus.PENDING,
                        dependencies=[],  # Will be resolved in second pass
                        created_at=datetime.now()
                    )
                    
                    # Set complexity score if provided
                    if "complexity" in data:
                        subtask.complexity_score = data["complexity"]
                    
                    subtasks.append(subtask)
                
                # Second pass: resolve dependencies
                for i, data in enumerate(subtask_data):
                    if "dependencies" in data and data["dependencies"]:
                        for dep_title in data["dependencies"]:
                            if dep_title in title_to_id:
                                subtasks[i].dependencies.append(title_to_id[dep_title])
                
                return subtasks
            else:
                raise ValueError("Could not extract JSON from AI response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")
    
    def _split_task_heuristic(self, task: Task, strategy: str, num_subtasks: int = None) -> List[Task]:
        """
        Split a task into subtasks using heuristic methods.
        
        Args:
            task: The task to split
            strategy: Decomposition strategy to use
            num_subtasks: Target number of subtasks (optional)
            
        Returns:
            List of generated subtasks
        """
        # Determine number of subtasks based on complexity if not specified
        if num_subtasks is None:
            if task.complexity_score is not None:
                # Simple heuristic: 1 subtask per complexity point
                num_subtasks = max(2, min(10, int(task.complexity_score)))
            else:
                # Default to 3 subtasks
                num_subtasks = 3
        
        # Choose strategy if 'auto'
        if strategy == "auto":
            # Simple heuristic: choose strategy based on task title/description
            if task.description and ("risk" in task.description.lower() or "security" in task.description.lower()):
                strategy = "risk_based"
            elif task.description and ("api" in task.description.lower() or "interface" in task.description.lower()):
                strategy = "technical"
            elif task.description and ("phase" in task.description.lower() or "stage" in task.description.lower()):
                strategy = "development_stage"
            else:
                strategy = "functional"  # Default
        
        # Generate generic subtasks based on strategy
        subtasks = []
        
        if strategy == "functional":
            # Functional decomposition: input/process/output
            templates = [
                ("Define Input Requirements", "Define and validate all input requirements for {task}"),
                ("Implement Core Processing", "Implement the core processing logic for {task}"),
                ("Create Output Handling", "Create the output handling and validation for {task}"),
                ("Implement Error Handling", "Implement comprehensive error handling for {task}"),
                ("Create Unit Tests", "Create unit tests to verify the functionality of {task}")
            ]
        elif strategy == "technical":
            # Technical layer decomposition
            templates = [
                ("Design Data Model", "Design the data model and schema for {task}"),
                ("Implement Business Logic", "Implement the core business logic for {task}"),
                ("Create API Interface", "Create the API interface for {task}"),
                ("Implement UI Components", "Implement the user interface components for {task}"),
                ("Create Integration Tests", "Create integration tests to verify {task}")
            ]
        elif strategy == "development_stage":
            # Development stage decomposition
            templates = [
                ("Define Requirements", "Define detailed requirements for {task}"),
                ("Create Prototype", "Create a basic prototype for {task}"),
                ("Implement Core Features", "Implement the core features of {task}"),
                ("Add Optimization", "Add performance optimization for {task}"),
                ("Implement Advanced Features", "Implement advanced features for {task}")
            ]
        elif strategy == "risk_based":
            # Risk-based decomposition
            templates = [
                ("Identify Risk Factors", "Identify all risk factors for {task}"),
                ("Implement Core Functionality", "Implement the core functionality with minimal risk"),
                ("Address Security Concerns", "Address security concerns for {task}"),
                ("Implement Edge Cases", "Implement handling for edge cases in {task}"),
                ("Create Validation Tests", "Create validation tests to verify risk mitigation")
            ]
        
        # Select templates based on num_subtasks
        selected_templates = templates[:min(num_subtasks, len(templates))]
        
        # Create subtasks from templates
        for i, (title_template, desc_template) in enumerate(selected_templates):
            title = title_template.format(task=task.title)
            description = desc_template.format(task=task.title)
            
            subtask_id = f"{task.id}.{i+1}" if hasattr(task, 'id') else f"subtask_{i+1}"
            
            subtask = Task(
                id=subtask_id,
                title=title,
                description=description,
                priority=task.priority,  # Inherit priority from parent
                status=TaskStatus.PENDING,
                dependencies=[],
                created_at=datetime.now()
            )
            
            # Add dependencies (each subtask depends on the previous one)
            if i > 0:
                prev_subtask_id = f"{task.id}.{i}" if hasattr(task, 'id') else f"subtask_{i}"
                subtask.dependencies.append(prev_subtask_id)
            
            subtasks.append(subtask)
        
        return subtasks
    
    def optimize_subtask_dependencies(self, subtasks: List[Task]) -> List[Task]:
        """
        Optimize dependencies between subtasks to improve parallelization.
        
        Args:
            subtasks: List of subtasks to optimize
            
        Returns:
            Optimized list of subtasks
        """
        if not subtasks:
            return []
        
        # Create a map of subtask IDs to subtasks
        subtask_map = {subtask.id: subtask for subtask in subtasks}
        
        # Identify potential parallel tracks
        # This is a simple heuristic that groups subtasks by their first word
        # More sophisticated algorithms could be used here
        tracks = {}
        for subtask in subtasks:
            first_word = subtask.title.split()[0] if subtask.title else ""
            if first_word not in tracks:
                tracks[first_word] = []
            tracks[first_word].append(subtask.id)
        
        # Optimize dependencies within each track
        for track_ids in tracks.values():
            if len(track_ids) <= 1:
                continue
                
            # Sort subtasks in the track by their existing dependency count
            track_ids.sort(key=lambda sid: len(subtask_map[sid].dependencies))
            
            # Create a chain of dependencies within the track
            for i in range(1, len(track_ids)):
                curr_subtask = subtask_map[track_ids[i]]
                prev_subtask_id = track_ids[i-1]
                
                # Add dependency if not already present
                if prev_subtask_id not in curr_subtask.dependencies:
                    curr_subtask.dependencies.append(prev_subtask_id)
        
        return list(subtask_map.values())
    
    def validate_subtask_coverage(self, task: Task, subtasks: List[Task]) -> Dict[str, Any]:
        """
        Validate that the subtasks fully cover the original task scope.
        
        Args:
            task: Original task
            subtasks: Generated subtasks
            
        Returns:
            Dictionary with validation results
        """
        # Simple validation based on keyword matching
        # More sophisticated validation could be implemented with AI
        
        result = {
            "complete_coverage": True,
            "missing_aspects": [],
            "recommendations": []
        }
        
        if not subtasks:
            result["complete_coverage"] = False
            result["missing_aspects"].append("No subtasks generated")
            result["recommendations"].append("Generate at least 2-3 subtasks to cover the task scope")
            return result
        
        # Extract key terms from task description
        task_terms = set()
        if task.description:
            # Simple term extraction (could be improved with NLP)
            task_terms = set(word.lower() for word in task.description.split() if len(word) > 3)
        
        # Extract terms from subtask descriptions
        subtask_terms = set()
        for subtask in subtasks:
            if subtask.description:
                subtask_terms.update(word.lower() for word in subtask.description.split() if len(word) > 3)
        
        # Find missing terms
        missing_terms = task_terms - subtask_terms
        if missing_terms:
            result["complete_coverage"] = False
            result["missing_aspects"].append(f"Key terms not covered in subtasks: {', '.join(missing_terms)}")
            result["recommendations"].append("Add subtasks to cover the missing aspects")
        
        # Check for testing/validation subtasks
        has_testing = any("test" in subtask.title.lower() or "test" in (subtask.description or "").lower() for subtask in subtasks)
        if not has_testing:
            result["recommendations"].append("Consider adding a testing/validation subtask")
        
        return result
