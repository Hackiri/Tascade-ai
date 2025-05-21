from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import uvicorn
import os
import sys
from typing import List, Optional, Dict, Any

# Adjust path to import from core
# This might need adjustment based on how the MCP server is launched
# If launched as a module (python -m src.integrations.mcp_server), this should work
# If launched as a script (python src/integrations/mcp_server.py), path adjustments are more complex
# For now, let's assume it might be run from the project root for path simplicity, or handle path in execution

# Correcting import paths assuming the server might be run from the project root 
# or the module path is correctly set up.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.task_manager import TaskManager
from src.core.models import Task, TaskStatus, TaskPriority, ProjectRule # Import Pydantic models if you make them
from src.core.ai_decomposer import AIDecomposer

app = FastAPI(
    title="Tascade AI MCP Server",
    description="Provides AI-powered task management functionalities via MCP.",
    version="0.1.0"
)

# Initialize TaskManager
# Data persistence for the MCP server - tasks loaded/saved here
# Consistent with CLI: ~/.tascade-ai/tasks.json
DATA_DIR = os.path.join(os.path.expanduser("~"), ".tascade-ai")
DATA_FILE = os.path.join(DATA_DIR, "tasks.json")
os.makedirs(DATA_DIR, exist_ok=True)

task_manager = TaskManager()
if os.path.exists(DATA_FILE):
    task_manager.load_from_file(DATA_FILE)
else:
    # Ensure file is created if it doesn't exist, so save can work
    task_manager.save_to_file(DATA_FILE) 

# --- Pydantic Models for Request/Response Bodies (align with MCP tool schemas) ---

class TaskOutput(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str # Enum values as strings
    priority: str # Enum values as strings
    dependencies: List[str] = []
    subtasks: List[str] = []
    created_at: str
    updated_at: str
    project_context_tags: List[str] = []
    details: Optional[Dict[str, Any]] = None
    
    # Task execution tracking fields
    start_time: Optional[str] = None
    completion_time: Optional[str] = None
    duration_minutes: Optional[float] = None
    time_spent_minutes: Optional[float] = None
    blocked_reason: Optional[str] = None
    blocker_task_id: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_effort_hours: Optional[float] = None
    actual_effort_hours: Optional[float] = None

    @classmethod
    def from_task(cls, task: Task) -> 'TaskOutput':
        # Convert datetime objects to ISO format strings if they exist
        start_time = task.start_time.isoformat() if task.start_time else None
        completion_time = task.completion_time.isoformat() if task.completion_time else None
        
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            dependencies=task.dependencies,
            subtasks=task.subtasks,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            project_context_tags=task.project_context_tags,
            details=task.details,
            
            # Task execution tracking fields
            start_time=start_time,
            completion_time=completion_time,
            duration_minutes=task.duration_minutes,
            time_spent_minutes=task.time_spent_minutes,
            blocked_reason=task.blocked_reason,
            blocker_task_id=task.blocker_task_id,
            assigned_to=task.assigned_to,
            estimated_effort_hours=task.estimated_effort_hours,
            actual_effort_hours=task.actual_effort_hours
        )

class ListTasksResponse(BaseModel):
    tasks: List[TaskOutput]

class ImportPrdRequest(BaseModel):
    prd_file_path: str # Assuming Windsurf can provide an absolute path
    project_root: str # MCP usually provides project root

class ImportPrdResponse(BaseModel):
    imported_tasks: List[TaskOutput]
    message: str

class ProjectRuleOutput(BaseModel):
    id: str
    name: str
    description: str
    applies_to_tags: List[str] = []
    content: str
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_rule(cls, rule: ProjectRule) -> 'ProjectRuleOutput':
        return cls(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            applies_to_tags=rule.applies_to_tags,
            content=rule.content,
            is_active=rule.is_active,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat()
        )

class ProjectRuleCreateInput(BaseModel):
    name: str
    description: str
    content: str
    applies_to_tags: List[str] = []
    is_active: bool = True

class ProjectRuleUpdateInput(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    applies_to_tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ListProjectRulesResponse(BaseModel):
    rules: List[ProjectRuleOutput]

class SimpleSuccessResponse(BaseModel):
    message: str


# --- Pydantic Models for Task Execution Tracking ---
class TaskExecutionRequest(BaseModel):
    task_id: str
    user: Optional[str] = None


class TaskBlockRequest(BaseModel):
    task_id: str
    reason: str
    blocker_task_id: Optional[str] = None
    user: Optional[str] = None


class TaskUnblockRequest(BaseModel):
    task_id: str
    resolution: str
    user: Optional[str] = None


class TaskCompleteRequest(BaseModel):
    task_id: str
    user: Optional[str] = None
    completion_notes: Optional[str] = None


class TaskPauseRequest(BaseModel):
    task_id: str
    user: Optional[str] = None
    pause_reason: Optional[str] = None


# --- Pydantic Models for Task Analysis ---
class TaskAnalysisResponse(BaseModel):
    task_id: str
    task_title: str
    complexity_score: float
    estimated_effort_hours: float
    factors: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class DependencyGraphRequest(BaseModel):
    task_id: str
    format: str = "text"  # text, json, or mermaid


class DependencyGraphResponse(BaseModel):
    task_id: str
    task_title: str
    graph: str


class CriticalPathResponse(BaseModel):
    total_duration: float
    path: List[Dict[str, Any]]

# --- Pydantic Models for AI Decomposition --- 
class AIDecompositionPreparationRequest(BaseModel):
    parent_task_id: str
    project_root: str
    custom_instructions: Optional[str] = None

class MCPCallInfo(BaseModel):
    tool_name: str
    server_name: str
    params: Dict[str, Any]
    purpose: str

class AIDecompositionPreparationResponse(BaseModel):
    mcp_call_sequence: List[MCPCallInfo]
    message: Optional[str] = None

class LLMSuggestedSubtask(BaseModel):
    title: str
    description: Optional[str] = None
    # We might receive other fields from the LLM, but title is crucial.
    # Keeping it simple for now; parse_llm_response_for_subtasks handles this structure.

class AIFinalizeSubtasksRequest(BaseModel):
    parent_task_id: str
    llm_suggested_subtasks: List[LLMSuggestedSubtask] # List of {title: str, description: str}
    user_who_confirmed: Optional[str] = "agent_or_user_via_agent"

class AIFinalizeSubtasksResponse(BaseModel):
    created_subtasks: List[TaskOutput]
    message: str

# --- MCP Endpoints ---

@app.get("/mcp/status", tags=["MCP General"])
async def get_status():
    """Checks the status of the Tascade AI MCP server."""
    return {"status": "running", "message": "Tascade AI MCP Server is active."}

@app.post("/mcp/list_tasks", response_model=ListTasksResponse, tags=["MCP Tasks"])
async def list_tasks_endpoint(status: Optional[str] = Body(None), priority: Optional[str] = Body(None)):
    """Lists tasks, with optional filtering."""
    filter_status = TaskStatus(status.lower()) if status else None
    filter_priority = TaskPriority(priority.lower()) if priority else None
    
    core_tasks = task_manager.list_tasks(status=filter_status, priority=filter_priority)
    output_tasks = [TaskOutput.from_task(task) for task in core_tasks]
    return ListTasksResponse(tasks=output_tasks)

@app.post("/mcp/import_prd", response_model=ImportPrdResponse, tags=["MCP Tasks"])
async def import_prd_endpoint(request_body: ImportPrdRequest):
    """Imports tasks from a PRD file provided by its absolute path."""
    # Construct absolute path if not already, using project_root if prd_file_path is relative
    # For now, assuming prd_file_path from Windsurf might be absolute or resolvable
    # A robust version would handle path joining with project_root carefully
    prd_path = request_body.prd_file_path
    if not os.path.isabs(prd_path):
        prd_path = os.path.join(request_body.project_root, prd_path)

    if not os.path.exists(prd_path) or not os.path.isfile(prd_path):
        raise HTTPException(status_code=400, detail=f"PRD file not found or is not a file: {prd_path}")

    try:
        imported_core_tasks = task_manager.import_tasks_from_prd(prd_path)
        task_manager.save_to_file(DATA_FILE) # Persist after import
        output_tasks = [TaskOutput.from_task(task) for task in imported_core_tasks]
        return ImportPrdResponse(
            imported_tasks=output_tasks,
            message=f"Successfully imported {len(output_tasks)} tasks from {os.path.basename(prd_path)}."
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Failed to import PRD: {str(e)}")

# --- MCP Project Rule Endpoints ---

PROJECT_RULES_TAG = "MCP Project Rules"

@app.post("/mcp/rules/add", response_model=ProjectRuleOutput, tags=[PROJECT_RULES_TAG])
async def add_project_rule_endpoint(rule_input: ProjectRuleCreateInput):
    """Adds a new project rule."""
    try:
        core_rule = task_manager.add_project_rule(
            name=rule_input.name,
            description=rule_input.description,
            content=rule_input.content,
            applies_to_tags=rule_input.applies_to_tags,
            is_active=rule_input.is_active
        )
        task_manager.save_to_file(DATA_FILE)
        return ProjectRuleOutput.from_rule(core_rule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add project rule: {str(e)}")

@app.post("/mcp/rules/list", response_model=ListProjectRulesResponse, tags=[PROJECT_RULES_TAG])
async def list_project_rules_endpoint():
    """Lists all project rules."""
    core_rules = task_manager.list_project_rules()
    output_rules = [ProjectRuleOutput.from_rule(rule) for rule in core_rules]
    return ListProjectRulesResponse(rules=output_rules)

@app.get("/mcp/rules/{rule_id}", response_model=ProjectRuleOutput, tags=[PROJECT_RULES_TAG])
async def get_project_rule_endpoint(rule_id: str):
    """Gets detailed information for a specific project rule."""
    core_rule = task_manager.get_project_rule(rule_id)
    if not core_rule:
        raise HTTPException(status_code=404, detail=f"Project rule with ID '{rule_id}' not found.")
    return ProjectRuleOutput.from_rule(core_rule)

@app.post("/mcp/rules/{rule_id}/update", response_model=ProjectRuleOutput, tags=[PROJECT_RULES_TAG])
async def update_project_rule_endpoint(rule_id: str, rule_update_input: ProjectRuleUpdateInput):
    """Updates an existing project rule. Only provided fields are changed."""
    update_data = rule_update_input.model_dump(exclude_unset=True) # Pydantic v2 way
    # For Pydantic v1: update_data = rule_update_input.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update information provided.")

    updated_rule = task_manager.update_project_rule(rule_id, update_data)
    if not updated_rule:
        raise HTTPException(status_code=404, detail=f"Project rule with ID '{rule_id}' not found or no changes made.")
    
    task_manager.save_to_file(DATA_FILE)
    return ProjectRuleOutput.from_rule(updated_rule)

@app.post("/mcp/rules/{rule_id}/delete", response_model=SimpleSuccessResponse, tags=[PROJECT_RULES_TAG])
async def delete_project_rule_endpoint(rule_id: str):
    """Deletes a project rule."""
    rule_to_delete = task_manager.get_project_rule(rule_id) # Check existence for better error msg
    if not rule_to_delete:
        raise HTTPException(status_code=404, detail=f"Project rule with ID '{rule_id}' not found.")

    if task_manager.delete_project_rule(rule_id):
        task_manager.save_to_file(DATA_FILE)
        return SimpleSuccessResponse(message=f"Project rule '{rule_to_delete.name}' (ID: {rule_id}) deleted successfully.")
    else:
        # Should be caught by the check above, but as a fallback
        raise HTTPException(status_code=500, detail=f"Failed to delete project rule with ID '{rule_id}'.")

@app.post("/mcp/rules/{rule_id}/activate", response_model=ProjectRuleOutput, tags=[PROJECT_RULES_TAG])
async def activate_project_rule_endpoint(rule_id: str):
    """Activates a project rule (sets is_active to True)."""
    updated_rule = task_manager.update_project_rule(rule_id, {'is_active': True})
    if not updated_rule:
        raise HTTPException(status_code=404, detail=f"Project rule with ID '{rule_id}' not found.")
    task_manager.save_to_file(DATA_FILE)
    return ProjectRuleOutput.from_rule(updated_rule)

@app.post("/mcp/rules/{rule_id}/deactivate", response_model=ProjectRuleOutput, tags=[PROJECT_RULES_TAG])
async def deactivate_project_rule_endpoint(rule_id: str):
    """Deactivates a project rule (sets is_active to False)."""
    updated_rule = task_manager.update_project_rule(rule_id, {'is_active': False})
    if not updated_rule:
        raise HTTPException(status_code=404, detail=f"Project rule with ID '{rule_id}' not found.")
    task_manager.save_to_file(DATA_FILE)
    return ProjectRuleOutput.from_rule(updated_rule)


# --- MCP Task Execution Tracking Endpoints ---
TASK_EXECUTION_TAG = "MCP Task Execution"

@app.post("/mcp/tasks/start", response_model=TaskOutput, tags=[TASK_EXECUTION_TAG])
def start_task_endpoint(request: TaskExecutionRequest):
    """Start a task, marking it as in-progress and recording the start time."""
    try:
        task = task_manager.start_task(request.task_id, user=request.user)
        task_manager.save_to_file(DATA_FILE)
        return TaskOutput.from_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tasks/complete", response_model=TaskOutput, tags=[TASK_EXECUTION_TAG])
def complete_task_endpoint(request: TaskCompleteRequest):
    """Complete a task, recording completion time and calculating duration."""
    try:
        task = task_manager.complete_task(
            request.task_id, 
            user=request.user, 
            completion_notes=request.completion_notes
        )
        task_manager.save_to_file(DATA_FILE)
        return TaskOutput.from_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tasks/pause", response_model=TaskOutput, tags=[TASK_EXECUTION_TAG])
def pause_task_endpoint(request: TaskPauseRequest):
    """Pause a task that is in progress, tracking time spent so far."""
    try:
        task = task_manager.pause_task(
            request.task_id, 
            user=request.user, 
            pause_reason=request.pause_reason
        )
        task_manager.save_to_file(DATA_FILE)
        return TaskOutput.from_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tasks/block", response_model=TaskOutput, tags=[TASK_EXECUTION_TAG])
def block_task_endpoint(request: TaskBlockRequest):
    """Mark a task as blocked with a reason and optional blocker task."""
    try:
        task = task_manager.block_task(
            request.task_id, 
            request.reason, 
            blocker_task_id=request.blocker_task_id, 
            user=request.user
        )
        task_manager.save_to_file(DATA_FILE)
        return TaskOutput.from_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tasks/unblock", response_model=TaskOutput, tags=[TASK_EXECUTION_TAG])
def unblock_task_endpoint(request: TaskUnblockRequest):
    """Unblock a previously blocked task with a resolution."""
    try:
        task = task_manager.unblock_task(
            request.task_id, 
            request.resolution, 
            user=request.user
        )
        task_manager.save_to_file(DATA_FILE)
        return TaskOutput.from_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- MCP Task Analysis Endpoints ---
TASK_ANALYSIS_TAG = "MCP Task Analysis"

@app.get("/mcp/tasks/{task_id}/analyze", response_model=TaskAnalysisResponse, tags=[TASK_ANALYSIS_TAG])
def analyze_task_endpoint(task_id: str):
    """Analyze the complexity of a task and provide recommendations."""
    try:
        task = task_manager.get_task(task_id)
        analysis = task_manager.analyze_task_complexity(task_id)
        
        return TaskAnalysisResponse(
            task_id=task_id,
            task_title=task.title,
            complexity_score=analysis["complexity_score"],
            estimated_effort_hours=analysis["estimated_effort_hours"],
            factors=analysis.get("factors"),
            recommendations=analysis.get("recommendations")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tasks/dependencies", response_model=DependencyGraphResponse, tags=[TASK_ANALYSIS_TAG])
def dependency_graph_endpoint(request: DependencyGraphRequest):
    """Generate a dependency graph for a task in the specified format."""
    try:
        task = task_manager.get_task(request.task_id)
        graph = task_manager.generate_dependency_graph(request.task_id, format=request.format)
        
        return DependencyGraphResponse(
            task_id=request.task_id,
            task_title=task.title,
            graph=graph
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mcp/tasks/critical-path", response_model=CriticalPathResponse, tags=[TASK_ANALYSIS_TAG])
def critical_path_endpoint(task_id: Optional[str] = None):
    """Identify the critical path of tasks based on dependencies and estimated effort."""
    try:
        critical_path = task_manager.get_critical_path(task_id)
        if not critical_path:
            raise HTTPException(status_code=404, detail="No critical path found")
            
        return CriticalPathResponse(
            total_duration=critical_path["total_duration"],
            path=critical_path["path"]
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


# --- MCP AI Decomposition Endpoints ---
AI_DECOMPOSITION_TAG = "MCP AI Decomposition"

@app.post("/mcp/ai/prepare_decomposition_calls", response_model=AIDecompositionPreparationResponse, tags=[AI_DECOMPOSITION_TAG])
async def prepare_ai_decomposition_calls_endpoint(request: AIDecompositionPreparationRequest):
    """Prepares the sequence of MCP calls required for AI task decomposition."""
    parent_task = task_manager.get_task(request.parent_task_id)
    if not parent_task:
        raise HTTPException(status_code=404, detail=f"Parent task with ID '{request.parent_task_id}' not found.")

    active_rules = [rule for rule in task_manager.list_project_rules() if rule.is_active]
    
    # Assuming tascade-ai is the server name configured for decomposition
    # This could be made configurable if needed.
    decomposer = AIDecomposer(task_manager_mcp_server_name="tascade-ai") 

    try:
        mcp_call_sequence_raw = decomposer.prepare_mcp_calls_for_decomposition(
            parent_task=parent_task,
            project_rules=active_rules,
            custom_instructions=request.custom_instructions,
            project_root=request.project_root
        )
        # Convert to Pydantic models for response validation
        mcp_call_sequence_typed = [MCPCallInfo(**call) for call in mcp_call_sequence_raw]
        
        return AIDecompositionPreparationResponse(
            mcp_call_sequence=mcp_call_sequence_typed,
            message="MCP call sequence for AI task decomposition prepared."
        )
    except Exception as e:
        # Log e for server-side diagnostics
        print(f"Error during AI decomposition preparation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error preparing AI decomposition: {str(e)}")

@app.post("/mcp/ai/finalize_subtasks", response_model=AIFinalizeSubtasksResponse, tags=[AI_DECOMPOSITION_TAG])
async def finalize_ai_subtasks_endpoint(request: AIFinalizeSubtasksRequest):
    """Parses LLM-suggested subtasks and adds them to the parent task."""
    parent_task = task_manager.get_task(request.parent_task_id)
    if not parent_task:
        raise HTTPException(status_code=404, detail=f"Parent task ID '{request.parent_task_id}' not found.")

    # Convert Pydantic models back to simple dicts for AIDecomposer, if necessary,
    # or update AIDecomposer to accept these Pydantic models.
    # For now, parse_llm_response_for_subtasks expects List[Dict[str,str]].
    llm_subtasks_as_dicts = [sub.model_dump(exclude_none=True) for sub in request.llm_suggested_subtasks]

    decomposer = AIDecomposer() # task_manager_mcp_server_name not needed here
    try:
        parsed_subtasks_for_tm = decomposer.parse_llm_response_for_subtasks(llm_subtasks_as_dicts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing LLM suggested subtasks: {str(e)}")

    if not parsed_subtasks_for_tm:
        return AIFinalizeSubtasksResponse(
            created_subtasks=[],
            message="No valid subtasks parsed from LLM suggestions. No tasks were added."
        )
    
    try:
        created_core_tasks = task_manager.add_subtasks_from_ai(
            parent_task_id=request.parent_task_id,
            suggested_subtasks=parsed_subtasks_for_tm,
            user=request.user_who_confirmed
        )
        task_manager.save_to_file(DATA_FILE) # Persist changes
        
        output_tasks = [TaskOutput.from_task(task) for task in created_core_tasks]
        return AIFinalizeSubtasksResponse(
            created_subtasks=output_tasks,
            message=f"Successfully finalized and added {len(output_tasks)} AI-generated subtasks."
        )
    except Exception as e:
        # Log e
        print(f"Error during AI subtask finalization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error finalizing AI subtasks: {str(e)}")


# --- Main execution for running the server (e.g., for local testing) ---
if __name__ == "__main__":
    # This allows running the server directly for testing: python src/integrations/mcp_server.py
    # For actual MCP use, Windsurf/Cursor would launch this process as per its config.
    # Default port for MCP servers is often around 3000-4000. Let's pick one.
    uvicorn.run(app, host="127.0.0.1", port=3838, log_level="info")
