"""
Anthropic AI Provider for Tascade AI.
This module provides integration with Anthropic's Claude models.
"""

import os
from typing import Dict, List, Any, Optional
import json

from .base import BaseAIProvider
from ..models import Task, ProjectRule


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider for AI services in Tascade AI."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
            model: Anthropic model to use (defaults to claude-3-opus-20240229)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        
        # Import anthropic here to avoid dependency issues if not using this provider
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Anthropic Python SDK not installed. Install with 'pip install anthropic'")
    
    def _call_claude(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Call the Claude API with the given prompt.
        
        Args:
            prompt: The prompt to send to Claude
            system_prompt: Optional system prompt to set context
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Claude's response as a string
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Error calling Anthropic API: {str(e)}")
    
    def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        Analyze a task using Claude and provide insights.
        
        Args:
            task: The task to analyze
            
        Returns:
            Dict containing analysis results
        """
        prompt = f"""
        Analyze the following task and provide insights:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        Status: {task.status.value}
        Priority: {task.priority.value}
        Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
        Subtasks: {', '.join(task.subtasks) if task.subtasks else 'None'}
        
        Please provide a structured analysis with:
        1. A complexity score from 1-10
        2. Estimated effort in hours
        3. A list of recommendations
        4. An implementation approach
        
        Format your response as a JSON object with these keys:
        - complexity_score (float)
        - estimated_effort_hours (float)
        - recommendations (array of strings)
        - implementation_approach (string)
        """
        
        system_prompt = "You are an expert software development task analyzer. Provide concise, actionable insights."
        
        response = self._call_claude(prompt, system_prompt, temperature=0.2)
        
        try:
            # Extract JSON from response (in case there's any extra text)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            analysis = json.loads(json_str)
            
            # Ensure required fields are present
            required_fields = ["complexity_score", "estimated_effort_hours", "recommendations"]
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = None
            
            return analysis
        except Exception as e:
            # Fallback to a default analysis if parsing fails
            return {
                "complexity_score": 5.0,
                "estimated_effort_hours": 4.0,
                "recommendations": ["Unable to generate recommendations due to an error"],
                "error": str(e)
            }
    
    def decompose_task(self, task: Task, project_rules: List[ProjectRule], 
                      custom_instructions: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Decompose a task into subtasks using Claude.
        
        Args:
            task: The parent task to decompose
            project_rules: List of project rules to consider
            custom_instructions: Optional custom instructions for decomposition
            
        Returns:
            List of dictionaries representing subtasks
        """
        # Format project rules for the prompt
        rules_text = ""
        if project_rules:
            rules_text = "Project Rules to consider:\n"
            for rule in project_rules:
                if rule.is_active:
                    rules_text += f"- {rule.name}: {rule.content}\n"
        
        # Build the prompt
        prompt = f"""
        Decompose the following task into smaller, actionable subtasks:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        
        {rules_text}
        
        {custom_instructions or ''}
        
        For each subtask, provide:
        1. A clear, concise title
        2. A detailed description
        3. Any dependencies on other subtasks (by number, e.g., "depends on subtask 1")
        
        Format your response as a JSON array of objects, each with:
        - title (string)
        - description (string)
        - dependencies (array of integers, can be empty)
        """
        
        system_prompt = "You are an expert at breaking down complex tasks into manageable subtasks. Be thorough but practical."
        
        response = self._call_claude(prompt, system_prompt, temperature=0.3)
        
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            subtasks = json.loads(json_str)
            
            # Convert numeric dependencies to task IDs if needed
            for subtask in subtasks:
                if "dependencies" in subtask and isinstance(subtask["dependencies"], list):
                    # This is a placeholder - in a real implementation, we would map
                    # the numeric dependencies to actual task IDs
                    pass
            
            return subtasks
        except Exception as e:
            # Return a minimal result if parsing fails
            return [{
                "title": f"Subtask for {task.title}",
                "description": "Error generating subtasks: " + str(e),
                "dependencies": []
            }]
    
    def generate_implementation_guide(self, task: Task, project_rules: List[ProjectRule]) -> str:
        """
        Generate an implementation guide for a task using Claude.
        
        Args:
            task: The task to generate a guide for
            project_rules: List of project rules to consider
            
        Returns:
            Implementation guide as a string
        """
        # Format project rules for the prompt
        rules_text = ""
        if project_rules:
            rules_text = "Project Rules to consider:\n"
            for rule in project_rules:
                if rule.is_active:
                    rules_text += f"- {rule.name}: {rule.content}\n"
        
        prompt = f"""
        Generate a detailed implementation guide for the following task:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        
        {rules_text}
        
        The implementation guide should include:
        1. Step-by-step instructions
        2. Key considerations and potential pitfalls
        3. Technical approach and best practices
        4. Any relevant code patterns or examples
        
        Format your response as a markdown document with clear sections.
        """
        
        system_prompt = "You are an expert software developer providing implementation guidance. Be specific, practical, and thorough."
        
        return self._call_claude(prompt, system_prompt, temperature=0.4)
    
    def generate_verification_criteria(self, task: Task) -> str:
        """
        Generate verification criteria for a task using Claude.
        
        Args:
            task: The task to generate criteria for
            
        Returns:
            Verification criteria as a string
        """
        prompt = f"""
        Generate verification criteria for the following task:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        
        The verification criteria should include:
        1. Functional acceptance criteria
        2. Test cases or scenarios
        3. Quality metrics or standards
        4. Definition of "done" for this task
        
        Format your response as a markdown document with clear sections.
        """
        
        system_prompt = "You are an expert in quality assurance and testing. Provide clear, testable verification criteria."
        
        return self._call_claude(prompt, system_prompt, temperature=0.3)
    
    def apply_rules_to_task(self, task: Task, rules: List[ProjectRule]) -> List[Dict[str, Any]]:
        """
        Apply project rules to a task and get recommendations using Claude.
        
        Args:
            task: The task to apply rules to
            rules: List of project rules to apply
            
        Returns:
            List of dictionaries with rule applications and recommendations
        """
        if not rules:
            return []
        
        # Format rules for the prompt
        rules_text = "Project Rules to apply:\n"
        for i, rule in enumerate(rules):
            rules_text += f"{i+1}. {rule.name}: {rule.content}\n"
        
        prompt = f"""
        Apply the following project rules to this task and provide recommendations:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        
        {rules_text}
        
        For each rule, determine:
        1. If it applies to this task
        2. Specific recommendations based on the rule
        3. Any implementation notes
        
        Format your response as a JSON array of objects, each with:
        - rule_id (string, matching the rule's ID)
        - applies (boolean)
        - recommendations (array of strings)
        - implementation_notes (string)
        """
        
        system_prompt = "You are an expert at applying project standards and guidelines. Be specific and practical."
        
        response = self._call_claude(prompt, system_prompt, temperature=0.2)
        
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            rule_applications = json.loads(json_str)
            
            # Ensure rule_id is present and valid
            for app in rule_applications:
                if "rule_id" not in app or not any(r.id == app["rule_id"] for r in rules):
                    # Find the corresponding rule by index
                    index = rule_applications.index(app)
                    if index < len(rules):
                        app["rule_id"] = rules[index].id
            
            return rule_applications
        except Exception as e:
            # Return a minimal result if parsing fails
            return [{
                "rule_id": rule.id,
                "applies": True,
                "recommendations": ["Error generating recommendations: " + str(e)],
                "implementation_notes": ""
            } for rule in rules]
    
    def analyze_task_complexity(self, task: Task) -> Dict[str, Any]:
        """
        Analyze the complexity of a task using Claude.
        
        Args:
            task: The task to analyze
            
        Returns:
            Dictionary with complexity analysis
        """
        # This is similar to analyze_task but more focused on complexity
        prompt = f"""
        Analyze the complexity of the following task:
        
        Task: {task.title}
        Description: {task.description or 'No description provided'}
        Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
        Subtasks: {', '.join(task.subtasks) if task.subtasks else 'None'}
        
        Provide a detailed complexity analysis with:
        1. A complexity score from 1-10
        2. Factors contributing to complexity
        3. Recommendations for managing complexity
        
        Format your response as a JSON object with these keys:
        - complexity_score (float)
        - factors (object with factor names and values)
        - recommendations (array of strings)
        """
        
        system_prompt = "You are an expert at analyzing task complexity in software development. Be thorough but concise."
        
        response = self._call_claude(prompt, system_prompt, temperature=0.2)
        
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            analysis = json.loads(json_str)
            
            # Add estimated effort based on complexity
            if "complexity_score" in analysis:
                analysis["estimated_effort_hours"] = analysis["complexity_score"] * 0.8
            
            return analysis
        except Exception as e:
            # Return a minimal result if parsing fails
            return {
                "complexity_score": 5.0,
                "estimated_effort_hours": 4.0,
                "factors": {"error": str(e)},
                "recommendations": ["Unable to generate recommendations due to an error"]
            }
    
    def generate_dependency_graph(self, task: Task, all_tasks: Dict[str, Task], format: str = "text") -> str:
        """
        Generate a dependency graph for a task using Claude.
        
        Args:
            task: The task to generate a graph for
            all_tasks: Dictionary of all tasks
            format: Output format (text, json, mermaid)
            
        Returns:
            Dependency graph in the specified format
        """
        # Build a dependency tree
        def build_dependency_tree(task_id, visited=None):
            if visited is None:
                visited = set()
            
            if task_id in visited:
                return {"id": task_id, "title": all_tasks.get(task_id, Task(title="Unknown")).title, "circular": True}
            
            visited.add(task_id)
            
            current_task = all_tasks.get(task_id)
            if not current_task:
                return {"id": task_id, "title": "Unknown Task", "dependencies": []}
            
            dependencies = []
            for dep_id in current_task.dependencies:
                dependencies.append(build_dependency_tree(dep_id, visited.copy()))
            
            return {
                "id": task_id,
                "title": current_task.title,
                "dependencies": dependencies
            }
        
        # Build the tree
        tree = build_dependency_tree(task.id)
        
        if format == "json":
            return json.dumps(tree, indent=2)
        
        elif format == "mermaid":
            # Generate Mermaid diagram
            mermaid_lines = ["graph TD;"]
            
            def add_mermaid_nodes(node, parent_id=None):
                node_id = node["id"].replace("-", "_")  # Mermaid doesn't like hyphens in IDs
                
                # Add the node
                if node.get("circular", False):
                    mermaid_lines.append(f'  {node_id}["🔄 {node["title"]} (circular)"];')
                else:
                    mermaid_lines.append(f'  {node_id}["{node["title"]}"];')
                
                # Add the edge from parent if applicable
                if parent_id:
                    mermaid_lines.append(f'  {parent_id} --> {node_id};')
                
                # Process dependencies
                for dep in node.get("dependencies", []):
                    add_mermaid_nodes(dep, node_id)
            
            add_mermaid_nodes(tree)
            return "\n".join(mermaid_lines)
        
        else:  # Default to text format
            # For text format, we'll use Claude to generate a readable representation
            prompt = f"""
            Generate a text-based dependency graph for the following task tree:
            
            {json.dumps(tree, indent=2)}
            
            Format the dependency graph as a hierarchical text representation with:
            - Clear indentation to show hierarchy
            - Task titles and IDs
            - Markers for circular dependencies
            
            The output should be easy to read in a terminal or text editor.
            """
            
            system_prompt = "You are an expert at visualizing task dependencies. Create a clear, readable text representation."
            
            return self._call_claude(prompt, system_prompt, temperature=0.1)
