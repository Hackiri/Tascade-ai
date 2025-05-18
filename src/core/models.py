from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REVIEW = "review"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # List of Task IDs
    subtasks: List[str] = field(default_factory=list)      # List of Task IDs
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None
    
    # Task effort estimation and tracking
    estimated_effort_hours: Optional[float] = None
    actual_effort_hours: Optional[float] = None
    
    # Task execution tracking fields
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    time_spent_minutes: Optional[float] = None
    blocked_reason: Optional[str] = None
    blocker_task_id: Optional[str] = None
    
    # Enhanced task fields from claude-task-master and mcp-shrimp-task-manager
    implementation_guide: Optional[str] = None  # Detailed implementation instructions
    verification_criteria: Optional[str] = None  # How to verify task completion
    related_files: List[Dict[str, str]] = field(default_factory=list)  # Files related to this task
    analysis_result: Optional[str] = None  # AI-generated analysis of the task
    complexity_score: Optional[float] = None  # Task complexity score (1-10)
    execution_context: Optional[Dict[str, Any]] = field(default_factory=dict)  # Context for task execution
    
    project_context_tags: List[str] = field(default_factory=list) # Tags linking to project rules/context
    details: Optional[Dict[str, Any]] = field(default_factory=dict) # For additional, dynamic information
    history: List[Dict[str, Any]] = field(default_factory=list) # Log of changes

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status.lower())
        if isinstance(self.priority, str):
            self.priority = TaskPriority(self.priority.lower())

    def update_status(self, new_status: TaskStatus, user: Optional[str] = "system"):
        self._add_history_entry(f"Status changed from {self.status.value} to {new_status.value}", user)
        self.status = new_status
        self.touch()

    def add_dependency(self, task_id: str, user: Optional[str] = "system"):
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self._add_history_entry(f"Added dependency: {task_id}", user)
            self.touch()

    def remove_dependency(self, task_id: str, user: Optional[str] = "system"):
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self._add_history_entry(f"Removed dependency: {task_id}", user)
            self.touch()

    def add_subtask(self, subtask_id: str, user: Optional[str] = "system"):
        if subtask_id not in self.subtasks:
            self.subtasks.append(subtask_id)
            self._add_history_entry(f"Added subtask: {subtask_id}", user)
            self.touch()

    def _add_history_entry(self, change_description: str, user: Optional[str] = "system"):
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "change": change_description
        })

    def touch(self):
        """Updates the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

# Example of how a ProjectRule might look (to be expanded later)
@dataclass
class ProjectRule:
    name: str
    description: str
    content: str # The actual rule/guideline content
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    applies_to_tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def touch(self):
        self.updated_at = datetime.utcnow()
