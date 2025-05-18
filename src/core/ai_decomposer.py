"""
Module for AI-powered task decomposition.
"""

from typing import List, Dict, Optional, Any
import json # For parsing potential JSON responses
import uuid # For generating unique IDs in examples or simulations

from .models import Task, ProjectRule # Assuming Task and ProjectRule are in models.py

# Placeholder for actual MCP tool calling mechanism if we were to do it directly.
# In our case, this class will prepare parameters for MCP calls made by the main agent.
# from ..integrations.mcp_client import call_mcp_tool # Example

class AIDecomposer:
    """
    Handles the decomposition of tasks using an AI model via an MCP server.
    """

    def __init__(self, task_manager_mcp_server_name: str = "taskmaster-ai"):
        """
        Initializes the AIDecomposer.

        Args:
            task_manager_mcp_server_name: The name of the MCP server to use for task operations (e.g., taskmaster-ai).
        """
        self.task_manager_mcp_server_name = task_manager_mcp_server_name

    def _construct_llm_prompt(
        self,
        parent_task: Task,
        project_rules: List[ProjectRule],
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Constructs the detailed prompt for the LLM to decompose the task.
        The prompt will request output in a structured JSON format.
        """
        prompt_lines = []
        prompt_lines.append("You are an expert task decomposition AI. Your primary goal is to break this parent task down into smaller, actionable subtasks.")
        
        # Parent task details
        prompt_lines.append(f"Parent Task Title: {parent_task.title}")
        if parent_task.description:
            prompt_lines.append(f"Parent Task Description: {parent_task.description}")
        
        # Project rules
        active_rules = [rule for rule in project_rules if rule.is_active]
        if active_rules:
            prompt_lines.append("Project Rules:")
            for rule in active_rules:
                prompt_lines.append(f"- Rule Name: {rule.name}")
                prompt_lines.append(f"  Rule Content: {rule.content}")
        else:
            prompt_lines.append("Project Rules: None provided.")
        
        # Custom instructions
        if custom_instructions:
            prompt_lines.append(f"Custom Instructions: {custom_instructions}")
        else:
            prompt_lines.append("Custom Instructions: None provided.")
        
        # Output format guidance
        prompt_lines.append("Output Format Guidance:")
        prompt_lines.append("Provide your response as a JSON array of objects.")
        prompt_lines.append("Each object in the array should represent a subtask and have the following keys:")
        prompt_lines.append('"title": "(string, required) - A concise and descriptive title for the subtask."')
        prompt_lines.append('"description": "(string, optional) - A brief explanation of what the subtask entails."')
        
        return "\n".join(prompt_lines)

    def prepare_mcp_calls_for_decomposition(
        self, 
        parent_task: Task, 
        project_rules: List[ProjectRule], 
        custom_instructions: Optional[str] = None,
        project_root: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Prepares the sequence of MCP tool call configurations needed to decompose a task.

        This involves:
        1. Adding a temporary task to the task_manager_mcp_server (e.g., taskmaster-ai).
        2. Expanding this temporary task using the task_manager_mcp_server's LLM capabilities.
        3. (Implicitly, the caller will later handle removing the temporary task).

        Args:
            parent_task_for_decomposition: The Tascade AI task to decompose.
            active_rules: A list of active project rules to guide decomposition.
            custom_instructions: Optional user-provided instructions.
            project_root: The root directory of the project, required by taskmaster-ai tools.

        Returns:
            A list of dictionaries, where each dictionary defines an MCP tool call
            (e.g., {'tool_name': 'mcp3_add_task', 'params': {...}}).
            The caller (main agent) will execute these calls.
        """
        if not project_root:
            # In a real scenario, project_root might be dynamically determined or configured.
            # For now, it's a required parameter for taskmaster-ai tools.
            # We might need a way to get this from the environment or CLI context.
            # raise ValueError("project_root must be provided for taskmaster-ai tools.")
            # For now, we'll rely on the caller to pass it or the main agent to inject it.
            pass 

        mcp_calls = []

        # Step 1: Prepare mcp3_add_task call for a temporary placeholder task
        # The description for this temporary task in taskmaster-ai can be minimal,
        # as the full context will be in the prompt for mcp3_expand_task.
        temp_task_title = f"[TEMP] Decompose: {parent_task.title[:50]}" 
        temp_task_description = f"Temporary placeholder task for AI decomposition of Tascade AI task ID: {parent_task.id}"
        
        add_task_params = {
            "projectRoot": project_root,
            "title": temp_task_title,
            "description": temp_task_description,
            # No need to specify dependencies, priority, etc. for this temp task
        }
        mcp_calls.append({
            "tool_name": "mcp3_add_task", 
            "params": add_task_params,
            "purpose": "Create temporary task in taskmaster-ai for decomposition"
        })

        # Step 2: Prepare mcp3_expand_task call
        # The ID for this call will be the ID returned by the mcp3_add_task call.
        # The main agent will need to manage this chaining.
        decomposition_prompt = self._construct_llm_prompt(
            parent_task, project_rules, custom_instructions
        )
        expand_task_params = {
            # 'id' will be filled by the agent from the result of mcp3_add_task
            "projectRoot": project_root,
            "prompt": decomposition_prompt,
            "force": True # Ensure it expands even if some subtasks (unlikely for new temp) exist
        }
        mcp_calls.append({
            "tool_name": "mcp3_expand_task", 
            "params": expand_task_params,
            "purpose": "Expand temporary task using LLM to get subtask suggestions"
        })
        
        # Step 3 (Cleanup - to be handled by the caller after getting results):
        # A call to mcp3_remove_task will be needed, using the ID from mcp3_add_task.
        # We'll let the main agent orchestrate this since it depends on successful expansion.

        return mcp_calls

    def parse_llm_response_for_subtasks(self, llm_response_content: Any) -> List[Dict[str, str]]:
        """
        Parses the LLM's response to extract subtasks.

        Args:
            llm_response_content: The content from the LLM, either a list of dictionaries
                                  or a JSON string representing a list of subtask objects.

        Returns:
            A list of dictionaries, where each dictionary is a subtask 
            with 'title' and 'description'.
        
        Raises:
            TypeError: If the response is not a list or JSON string, or if list items are not dictionaries.
            ValueError: If the response cannot be parsed as expected or subtasks are missing required fields.
        """
        if not llm_response_content:
            return []

        # Check input type
        if not isinstance(llm_response_content, (list, str)):
            raise TypeError("LLM response is not a list or a JSON string")

        try:
            # Parse JSON if it's a string
            if isinstance(llm_response_content, str):
                try:
                    subtasks = json.loads(llm_response_content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse LLM response string as JSON: {e}")
            else:
                subtasks = llm_response_content

            # Validate that we have a list
            if not isinstance(subtasks, list):
                raise ValueError(f"Parsed LLM response {type(subtasks)} is not a list")

            validated_subtasks = []
            for i, subtask_data in enumerate(subtasks):
                # Check that each item is a dictionary
                if not isinstance(subtask_data, dict):
                    raise TypeError(f"LLM response item at index {i} is not a dictionary")
                
                # Check for title and validate it
                title = subtask_data.get('title', '').strip() if isinstance(subtask_data.get('title'), str) else None
                if not title:
                    raise ValueError(f"Subtask suggestion at index {i} missing 'title'")
                
                # Description is optional
                description = subtask_data.get('description')
                
                validated_subtasks.append({'title': title, 'description': description})
            
            return validated_subtasks
            
        except (TypeError, ValueError) as e:
            # Re-raise these exceptions as they already have appropriate messages
            raise
        except Exception as e:
            # For any other unexpected errors
            raise ValueError(f"Error processing LLM subtask response: {str(e)}")

# Example usage (conceptual - actual calls made by agent)
if __name__ == '__main__':
    # Dummy data for demonstration
    from datetime import datetime
    parent_task_example = Task(
        id='task123', title='Develop New User Authentication Feature',
        description='Create a secure and user-friendly authentication system including registration, login, and password recovery.',
        status='PENDING', priority='HIGH', dependencies=[], subtasks=[],
        created_at=datetime.now(), updated_at=datetime.now()
    )
    rule1 = ProjectRule(
        id='rule001', name='Security Standards', description='All auth features must use bcrypt and JWT.',
        content='- Use bcrypt for password hashing.\n- Use JWT for session management.\n- Implement rate limiting.',
        tags=['security', 'auth'], is_active=True, created_at=datetime.now()
    )

    decomposer = AIDecomposer(task_manager_mcp_server_name="taskmaster-ai")
    
    # 1. Construct the prompt (internal method, but shown for clarity)
    prompt = decomposer._construct_llm_prompt(parent_task_example, [rule1], "Ensure subtasks are backend focused first.")
    print("--- CONSTRUCTED PROMPT ---")
    print(prompt)
    print("\n-------------------------")

    # 2. Prepare MCP calls
    # project_root would be sourced from the current project context in a real scenario
    mcp_call_sequence = decomposer.prepare_mcp_calls_for_decomposition(
        parent_task=parent_task_example, 
        project_rules=[rule1], 
        custom_instructions="Ensure subtasks are backend focused first.",
        project_root="/Users/wm/CascadeProjects/Tascade AI" # Example project root
    )
    print("\n--- PREPARED MCP CALLS ---")
    for call_info in mcp_call_sequence:
        print(f"Tool: {call_info['tool_name']}")
        print(f"  Purpose: {call_info['purpose']}")
        # print(f"  Params: {json.dumps(call_info['params'], indent=2)}") # Params can be verbose
    print("\n-------------------------")

    # 3. Simulate parsing a response (this would come from the mcp3_expand_task call)
    # This structure depends on what mcp3_expand_task actually returns.
    # Assuming it's a list of dicts as per our prompt's request.
    simulated_llm_output_from_expand_task = [
        {'title': 'Design Auth Database Schema', 'description': 'Define tables for users, roles, permissions.'},
        {'title': 'Implement User Registration Endpoint', 'description': 'Create API for new user sign-up with password hashing.'},
        {'title': 'Implement Login Endpoint with JWT', 'description': 'Verify credentials and issue JWT upon successful login.'}
    ]
    
    # Or if it's a JSON string:
    # simulated_llm_output_from_expand_task = json.dumps([
    #     {'title': 'Design Auth Database Schema', 'description': 'Define tables for users, roles, permissions.'},
    #     {'title': 'Implement User Registration Endpoint', 'description': 'Create API for new user sign-up with password hashing.'},
    #     {'title': 'Implement Login Endpoint with JWT', 'description': 'Verify credentials and issue JWT upon successful login.'}
    # ])

    try:
        parsed_subtasks = decomposer.parse_llm_response_for_subtasks(simulated_llm_output_from_expand_task)
        print("\n--- PARSED SUBTASKS ---")
        for subtask in parsed_subtasks:
            print(f"- {subtask['title']}: {subtask['description']}")
        print("\n-----------------------")
    except ValueError as e:
        print(f"Error parsing simulated LLM response: {e}")

