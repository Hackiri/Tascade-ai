import pytest
from unittest.mock import MagicMock
from datetime import datetime
import json # Added for tests that might involve JSON strings

from src.core.ai_decomposer import AIDecomposer
from src.core.models import Task, ProjectRule, TaskStatus, TaskPriority

# Fixtures for common test data
@pytest.fixture
def sample_parent_task():
    """Returns a sample parent Task object using keyword arguments."""
    return Task(
        title="Develop New Authentication Feature", # Non-default first
        id="parent_task_123",
        description="Implement a new OAuth 2.0 based authentication system for the application.",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        dependencies=[],
        subtasks=[],
        created_at=datetime(2023, 1, 1, 10, 0, 0),
        updated_at=datetime(2023, 1, 1, 10, 0, 0),
        project_context_tags=["backend", "security"],
        details={"target_release": "v2.5"}
    )

@pytest.fixture
def sample_project_rules():
    """Returns a list of sample ProjectRule objects using keyword arguments."""
    return [
        ProjectRule(
            name="API Endpoint Naming Convention", # Non-default first
            description="All API endpoints must follow RESTful naming conventions.",
            content="Endpoints should be plural nouns, e.g., /users, /products. Use hyphens for multi-word resources.",
            id="rule_001",
            applies_to_tags=["api", "backend"],
            is_active=True,
            created_at=datetime(2023, 1, 1, 9, 0, 0),
            updated_at=datetime(2023, 1, 1, 9, 0, 0)
        ),
        ProjectRule(
            name="Code Commenting Standard", # Non-default first
            description="All functions and complex logic must be adequately commented.",
            content="Use docstrings for all public modules, classes, functions, and methods.",
            id="rule_002",
            applies_to_tags=["backend", "frontend"],
            is_active=True,
            created_at=datetime(2023, 1, 1, 9, 5, 0),
            updated_at=datetime(2023, 1, 1, 9, 5, 0)
        ),
        ProjectRule(
            name="Frontend State Management", # Non-default first
            description="Use Redux for frontend state.",
            content="All global frontend state must be managed via Redux store.",
            id="rule_003",
            applies_to_tags=["frontend"],
            is_active=False, # This rule is inactive
            created_at=datetime(2023, 1, 1, 9, 10, 0),
            updated_at=datetime(2023, 1, 1, 9, 10, 0)
        )
    ]

class TestAIDecomposerConstructPrompt:
    def test_construct_llm_prompt_basic(self, sample_parent_task):
        decomposer = AIDecomposer()
        prompt = decomposer._construct_llm_prompt(sample_parent_task, [], None)

        assert "You are an expert task decomposition AI." in prompt
        assert f"Parent Task Title: {sample_parent_task.title}" in prompt
        assert f"Parent Task Description: {sample_parent_task.description}" in prompt
        assert "Project Rules: None provided." in prompt
        assert "Custom Instructions: None provided." in prompt
        assert "Your primary goal is to break this parent task down into smaller, actionable subtasks" in prompt

    def test_construct_llm_prompt_with_rules(self, sample_parent_task, sample_project_rules):
        decomposer = AIDecomposer()
        active_rules = [rule for rule in sample_project_rules if rule.is_active]
        prompt = decomposer._construct_llm_prompt(sample_parent_task, active_rules, None)

        assert f"Parent Task Title: {sample_parent_task.title}" in prompt
        assert "Project Rules:" in prompt
        for rule in active_rules:
            assert f"- Rule Name: {rule.name}" in prompt
            assert f"  Rule Content: {rule.content}" in prompt
        assert sample_project_rules[2].name not in prompt # Inactive rule
        assert "Custom Instructions: None provided." in prompt

    def test_construct_llm_prompt_with_custom_instructions(self, sample_parent_task):
        decomposer = AIDecomposer()
        custom_instructions = "Focus on backend tasks first. Max 5 subtasks."
        prompt = decomposer._construct_llm_prompt(sample_parent_task, [], custom_instructions)

        assert f"Parent Task Title: {sample_parent_task.title}" in prompt
        assert "Project Rules: None provided." in prompt
        assert f"Custom Instructions: {custom_instructions}" in prompt

    def test_construct_llm_prompt_with_rules_and_instructions(self, sample_parent_task, sample_project_rules):
        decomposer = AIDecomposer()
        active_rules = [rule for rule in sample_project_rules if rule.is_active]
        custom_instructions = "Prioritize API design and database schema subtasks."
        prompt = decomposer._construct_llm_prompt(sample_parent_task, active_rules, custom_instructions)

        assert f"Parent Task Title: {sample_parent_task.title}" in prompt
        assert "Project Rules:" in prompt
        for rule in active_rules:
            assert f"- Rule Name: {rule.name}" in prompt
        assert f"Custom Instructions: {custom_instructions}" in prompt

    def test_construct_llm_prompt_includes_output_format_guidance(self, sample_parent_task):
        decomposer = AIDecomposer()
        prompt = decomposer._construct_llm_prompt(sample_parent_task, [], None)

        assert "Output Format Guidance:" in prompt
        assert "Provide your response as a JSON array of objects" in prompt
        assert "Each object in the array should represent a subtask and have the following keys:" in prompt
        assert '"title": "(string, required) - A concise and descriptive title for the subtask."' in prompt
        assert '"description": "(string, optional) - A brief explanation of what the subtask entails."' in prompt


class TestAIDecomposerPrepareMCPCalls:
    @pytest.fixture
    def decomposer_with_mocked_prompt(self, monkeypatch):
        decomposer = AIDecomposer(task_manager_mcp_server_name="fake_tm_server")
        mock_prompt_content = "This is a mocked LLM prompt."
        monkeypatch.setattr(decomposer, '_construct_llm_prompt', MagicMock(return_value=mock_prompt_content))
        return decomposer, mock_prompt_content

    def test_prepare_mcp_calls_structure_and_content(self, decomposer_with_mocked_prompt, sample_parent_task, sample_project_rules):
        decomposer, mock_prompt_content = decomposer_with_mocked_prompt
        active_rules = [rule for rule in sample_project_rules if rule.is_active]
        custom_instructions = "Test instructions."
        project_root = "/test/project/root"

        mcp_calls = decomposer.prepare_mcp_calls_for_decomposition(
            parent_task=sample_parent_task,
            project_rules=active_rules,
            custom_instructions=custom_instructions,
            project_root=project_root
        )

        assert len(mcp_calls) == 2
        add_task_call = mcp_calls[0]
        assert add_task_call['tool_name'] == 'mcp3_add_task'
        # ... (rest of the assertions for this test remain largely the same)

    def test_prepare_mcp_calls_uses_constructed_prompt(self, decomposer_with_mocked_prompt, sample_parent_task):
        decomposer, mock_prompt_content = decomposer_with_mocked_prompt
        project_root = "/another/root"

        mcp_calls = decomposer.prepare_mcp_calls_for_decomposition(
            parent_task=sample_parent_task,
            project_rules=[],
            custom_instructions=None,
            project_root=project_root
        )
        # The prompt is used in the second MCP call (expand_task), not the first one (add_task)
        assert mcp_calls[1]['params']['prompt'] == mock_prompt_content
        decomposer._construct_llm_prompt.assert_called_once_with(sample_parent_task, [], None)


class TestAIDecomposerParseLLMResponse:
    @pytest.fixture
    def decomposer(self):
        return AIDecomposer()

    def test_parse_valid_llm_response(self, decomposer):
        llm_response = [
            {"title": "Subtask 1 Title", "description": "Subtask 1 Description"},
            {"title": "Subtask 2 Title", "description": "Subtask 2 Description"}
        ]
        # Assuming titles are stripped by the parser
        expected_subtasks = [
            {"title": "Subtask 1 Title", "description": "Subtask 1 Description"},
            {"title": "Subtask 2 Title", "description": "Subtask 2 Description"}
        ]
        assert decomposer.parse_llm_response_for_subtasks(llm_response) == expected_subtasks

    def test_parse_valid_llm_response_json_string(self, decomposer):
        llm_response_str = json.dumps([
            {"title": "Subtask 1 Title ", "description": "Subtask 1 Description"},
            {"title": " Subtask 2 Title", "description": "Subtask 2 Description"}
        ])
        expected_subtasks = [
            {"title": "Subtask 1 Title", "description": "Subtask 1 Description"}, # Title stripped
            {"title": "Subtask 2 Title", "description": "Subtask 2 Description"}  # Title stripped
        ]
        assert decomposer.parse_llm_response_for_subtasks(llm_response_str) == expected_subtasks


    def test_parse_valid_llm_response_missing_description(self, decomposer):
        llm_response = [
            {"title": "Subtask 1 Title"},
            {"title": "Subtask 2 Title", "description": "Subtask 2 Description"}
        ]
        expected_subtasks = [
            {"title": "Subtask 1 Title", "description": None},
            {"title": "Subtask 2 Title", "description": "Subtask 2 Description"}
        ]
        assert decomposer.parse_llm_response_for_subtasks(llm_response) == expected_subtasks

    def test_parse_llm_response_empty_list(self, decomposer):
        llm_response = []
        assert decomposer.parse_llm_response_for_subtasks(llm_response) == []
        assert decomposer.parse_llm_response_for_subtasks("[]") == [] # Empty JSON array string

    def test_parse_llm_response_missing_title_raises_value_error(self, decomposer):
        llm_response = [{"description": "This subtask is missing a title"}]
        with pytest.raises(ValueError, match="Subtask suggestion at index 0 missing 'title'"):
            decomposer.parse_llm_response_for_subtasks(llm_response)

    def test_parse_llm_response_empty_title_raises_value_error(self, decomposer):
        llm_response = [{"title": "  ", "description": "This subtask has an empty title"}] # Title is whitespace
        with pytest.raises(ValueError, match="Subtask suggestion at index 0 missing 'title'"):
            decomposer.parse_llm_response_for_subtasks(llm_response)

    def test_parse_llm_response_invalid_json_string_raises_value_error(self, decomposer):
        llm_response_str = "This is not a valid JSON list"
        with pytest.raises(ValueError, match="Failed to parse LLM response string as JSON"):
            decomposer.parse_llm_response_for_subtasks(llm_response_str)

    def test_parse_llm_response_json_not_a_list_raises_value_error(self, decomposer):
        llm_response_str = json.dumps({"not_a": "list"})
        with pytest.raises(ValueError, match="Parsed LLM response .* is not a list"):
            decomposer.parse_llm_response_for_subtasks(llm_response_str)

    def test_parse_llm_response_input_not_list_or_string_raises_type_error(self, decomposer):
        llm_response_invalid_type = 12345
        with pytest.raises(TypeError, match="LLM response is not a list or a JSON string"):
            decomposer.parse_llm_response_for_subtasks(llm_response_invalid_type)

    def test_parse_llm_response_list_item_not_a_dict_raises_type_error(self, decomposer):
        llm_response = ["This is not a dict", {"title": "Valid subtask"}]
        with pytest.raises(TypeError, match="LLM response item at index 0 is not a dictionary"):
            decomposer.parse_llm_response_for_subtasks(llm_response)

    def test_parse_llm_response_with_extra_keys(self, decomposer):
        llm_response = [
            {"title": "Subtask 1", "description": "Desc 1", "priority": "High"},
            {"title": "Subtask 2", "extra_info": "Some info"}
        ]
        expected_subtasks = [
            {"title": "Subtask 1", "description": "Desc 1"},
            {"title": "Subtask 2", "description": None} # extra_info is ignored, description becomes None
        ]
        assert decomposer.parse_llm_response_for_subtasks(llm_response) == expected_subtasks