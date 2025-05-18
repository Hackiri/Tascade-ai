"""
Base AI Provider interface for Tascade AI.
All AI provider implementations should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ..models import Task, ProjectRule


class BaseAIProvider(ABC):
    """Base class for AI providers in Tascade AI."""
    
    @abstractmethod
    def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        Analyze a task and provide insights.
        
        Args:
            task: The task to analyze
            
        Returns:
            Dict containing analysis results with keys:
                - complexity_score: float (1-10)
                - estimated_effort_hours: float
                - recommendations: List[str]
                - implementation_approach: str (optional)
        """
        pass
    
    @abstractmethod
    def decompose_task(self, task: Task, project_rules: List[ProjectRule], 
                      custom_instructions: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Decompose a task into subtasks.
        
        Args:
            task: The parent task to decompose
            project_rules: List of project rules to consider
            custom_instructions: Optional custom instructions for decomposition
            
        Returns:
            List of dictionaries representing subtasks
        """
        pass
    
    @abstractmethod
    def generate_implementation_guide(self, task: Task, project_rules: List[ProjectRule]) -> str:
        """
        Generate an implementation guide for a task.
        
        Args:
            task: The task to generate a guide for
            project_rules: List of project rules to consider
            
        Returns:
            Implementation guide as a string
        """
        pass
    
    @abstractmethod
    def generate_verification_criteria(self, task: Task) -> str:
        """
        Generate verification criteria for a task.
        
        Args:
            task: The task to generate criteria for
            
        Returns:
            Verification criteria as a string
        """
        pass
    
    @abstractmethod
    def apply_rules_to_task(self, task: Task, rules: List[ProjectRule]) -> List[Dict[str, Any]]:
        """
        Apply project rules to a task and get recommendations.
        
        Args:
            task: The task to apply rules to
            rules: List of project rules to apply
            
        Returns:
            List of dictionaries with rule applications and recommendations
        """
        pass
    
    @abstractmethod
    def analyze_task_complexity(self, task: Task) -> Dict[str, Any]:
        """
        Analyze the complexity of a task.
        
        Args:
            task: The task to analyze
            
        Returns:
            Dictionary with complexity analysis
        """
        pass
    
    @abstractmethod
    def generate_dependency_graph(self, task: Task, all_tasks: Dict[str, Task], format: str = "text") -> str:
        """
        Generate a dependency graph for a task.
        
        Args:
            task: The task to generate a graph for
            all_tasks: Dictionary of all tasks
            format: Output format (text, json, mermaid)
            
        Returns:
            Dependency graph in the specified format
        """
        pass
