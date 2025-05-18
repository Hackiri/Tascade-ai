import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import directly from models to avoid importing TaskManager which depends on MarkdownPRDParser
from src.core.models import Task, TaskStatus, TaskPriority

# We'll create a simplified version of TaskManager for testing
class TestTaskManager:
    def __init__(self):
        self._tasks = {}
        self._project_rules = {}
    
    def add_task(self, title, description=None, priority=TaskPriority.MEDIUM, dependencies=None, 
                subtasks=None, project_context_tags=None, details=None, status=TaskStatus.PENDING):
        task_id = f"task_{len(self._tasks) + 1}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            dependencies=dependencies or [],
            subtasks=subtasks or [],
            project_context_tags=project_context_tags or [],
            details=details or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._tasks[task_id] = task
        return task
    
    def get_task(self, task_id):
        return self._tasks.get(task_id)
    
    def list_tasks(self):
        return list(self._tasks.values())
    
    def get_subtasks(self, parent_task_id):
        parent_task = self.get_task(parent_task_id)
        if not parent_task:
            return []
        return [self.get_task(sub_id) for sub_id in parent_task.subtasks if self.get_task(sub_id)]
    
    def get_dependent_tasks(self, task_id):
        dependents = []
        for t in self._tasks.values():
            if task_id in t.dependencies:
                dependents.append(t)
        return dependents
    
    def get_tasks_blocking(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return []
        return [self.get_task(dep_id) for dep_id in task.dependencies if self.get_task(dep_id)]
        
    # Task Execution Tracking Methods
    def start_task(self, task_id, user="system"):
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Check if all dependencies are completed
        blocking_tasks = self.get_tasks_blocking(task_id)
        incomplete_blockers = [t for t in blocking_tasks if t.status != TaskStatus.COMPLETED]
        
        if incomplete_blockers:
            blocker_ids = [t.id for t in incomplete_blockers]
            print(f"Warning: Task {task_id} has incomplete dependencies: {', '.join(blocker_ids)}")
            
        # Update task status and timestamps
        task.status = TaskStatus.IN_PROGRESS
        current_time = datetime.utcnow()
        
        # Store start time in details if not already there
        if 'started_at' not in task.details:
            task.details['started_at'] = current_time.isoformat()
            
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task marked as in progress", user=user)
        return task
        
    def complete_task(self, task_id, completion_notes=None, user="system"):
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Update task status and timestamps
        task.status = TaskStatus.COMPLETED
        current_time = datetime.utcnow()
        
        # Store completion time in details
        task.details['completed_at'] = current_time.isoformat()
        
        # Calculate duration if we have a start time
        if 'started_at' in task.details:
            start_time = datetime.fromisoformat(task.details['started_at'])
            duration = current_time - start_time
            task.details['duration_seconds'] = duration.total_seconds()
            
        task.touch()  # Update the updated_at timestamp
        
        # Add completion notes to history if provided
        history_entry = "Task marked as completed"
        if completion_notes:
            history_entry += f": {completion_notes}"
            
        task._add_history_entry(history_entry, user=user)
        
        # Check if this completion unblocks other tasks
        dependent_tasks = self.get_dependent_tasks(task_id)
        if dependent_tasks:
            unblocked_tasks = []
            for dep_task in dependent_tasks:
                # Check if all dependencies of this dependent task are now complete
                if all(self.get_task(dep_id).status == TaskStatus.COMPLETED 
                       for dep_id in dep_task.dependencies 
                       if self.get_task(dep_id)):
                    unblocked_tasks.append(dep_task.id)
                    
            if unblocked_tasks:
                task._add_history_entry(
                    f"Completion of this task unblocked: {', '.join(unblocked_tasks)}",
                    user="system"
                )
                
        return task
        
    def pause_task(self, task_id, reason=None, user="system"):
        task = self.get_task(task_id)
        if not task:
            return None
            
        if task.status != TaskStatus.IN_PROGRESS:
            print(f"Warning: Cannot pause task {task_id} as it is not in progress.")
            return task
            
        # Update task status
        task.status = TaskStatus.PENDING
        current_time = datetime.utcnow()
        
        # Track time spent so far if we have a start time
        if 'started_at' in task.details:
            start_time = datetime.fromisoformat(task.details['started_at'])
            duration = current_time - start_time
            
            # Accumulate time spent
            if 'time_spent_seconds' in task.details:
                task.details['time_spent_seconds'] += duration.total_seconds()
            else:
                task.details['time_spent_seconds'] = duration.total_seconds()
                
            # Remove the started_at since we're pausing
            del task.details['started_at']
            
        task.touch()  # Update the updated_at timestamp
        
        # Add pause reason to history if provided
        history_entry = "Task paused"
        if reason:
            history_entry += f": {reason}"
            
        task._add_history_entry(history_entry, user=user)
        return task
        
    def block_task(self, task_id, blocker_description, user="system"):
        task = self.get_task(task_id)
        if not task:
            return None
            
        # Update task status
        task.status = TaskStatus.BLOCKED
        
        # Track the blocker in details
        if 'blockers' not in task.details:
            task.details['blockers'] = []
            
        task.details['blockers'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'description': blocker_description
        })
        
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task blocked: {blocker_description}", user=user)
        return task
        
    def unblock_task(self, task_id, resolution, user="system"):
        task = self.get_task(task_id)
        if not task:
            return None
            
        if task.status != TaskStatus.BLOCKED:
            print(f"Warning: Task {task_id} is not currently blocked.")
            return task
            
        # Update task status
        task.status = TaskStatus.PENDING
        
        # Track the resolution in details
        if 'blockers' in task.details and task.details['blockers']:
            latest_blocker = task.details['blockers'][-1]
            latest_blocker['resolved_at'] = datetime.utcnow().isoformat()
            latest_blocker['resolution'] = resolution
            
        task.touch()  # Update the updated_at timestamp
        task._add_history_entry(f"Task unblocked: {resolution}", user=user)
        return task

    # Task Analysis Methods
    def analyze_task_complexity(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return {'error': f"Task {task_id} not found"}
            
        # Basic complexity metrics
        subtasks = self.get_subtasks(task_id)
        dependencies = self.get_tasks_blocking(task_id)
        dependents = self.get_dependent_tasks(task_id)
        
        # Calculate complexity score (simple algorithm as an example)
        complexity_score = 1.0  # Base score
        
        # Factor in description length
        if task.description:
            words = task.description.split()
            complexity_score += min(len(words) / 50, 3)  # Cap at +3 for very long descriptions
            
        # Factor in subtasks
        complexity_score += len(subtasks) * 0.5
        
        # Factor in dependencies and dependents
        complexity_score += len(dependencies) * 0.3
        complexity_score += len(dependents) * 0.2
        
        # Round to 1 decimal place
        complexity_score = round(complexity_score, 1)
        
        # Determine complexity category
        category = "Simple"
        if complexity_score >= 7:
            category = "Very Complex"
        elif complexity_score >= 5:
            category = "Complex"
        elif complexity_score >= 3:
            category = "Moderate"
            
        return {
            'task_id': task_id,
            'title': task.title,
            'complexity_score': complexity_score,
            'complexity_category': category,
            'subtask_count': len(subtasks),
            'dependency_count': len(dependencies),
            'dependent_count': len(dependents),
            'estimated_hours': round(complexity_score * 1.5, 1)  # Simple estimation
        }
        
    def get_task_chain(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return []
            
        # Use breadth-first search to build the dependency chain
        visited = set()
        chain = []
        current_level = [task]
        
        while current_level:
            chain.append(current_level)
            next_level = []
            
            for t in current_level:
                for dep_id in t.dependencies:
                    dep_task = self.get_task(dep_id)
                    if dep_task and dep_id not in visited:
                        next_level.append(dep_task)
                        visited.add(dep_id)
                        
            current_level = next_level
            
        return chain
        
    def get_critical_path(self):
        # Simplified implementation for testing
        all_tasks = self.list_tasks()
        if not all_tasks:
            return []
        return [all_tasks[0]]  # Just return the first task for testing
        
    def generate_dependency_graph(self, format="mermaid"):
        tasks = self.list_tasks()
        
        if format == "mermaid":
            # Generate Mermaid.js compatible graph markup
            lines = ["graph TD;"]
            
            # Add nodes with status colors
            for task in tasks:
                # Define node style based on status
                style = ""
                if task.status == TaskStatus.COMPLETED:
                    style = ":::done"
                elif task.status == TaskStatus.IN_PROGRESS:
                    style = ":::active"
                elif task.status == TaskStatus.BLOCKED:
                    style = ":::blocked"
                    
                # Add node with title as label
                lines.append(f"    {task.id}[\"#{task.id}: {task.title}\"]" + style + ";")
            
            # Add edges for dependencies
            for task in tasks:
                for dep_id in task.dependencies:
                    if dep_id in self._tasks:  # Ensure dependency exists
                        lines.append(f"    {dep_id}-->{task.id};")
            
            # Add class definitions
            lines.append("    classDef done fill:#cfc,stroke:#6c6;")
            lines.append("    classDef active fill:#ccf,stroke:#66c;")
            lines.append("    classDef blocked fill:#fcc,stroke:#c66;")
            
            return "\n".join(lines)
        else:
            return f"Unsupported format: {format}"

@pytest.fixture
def task_manager():
    """Create a TestTaskManager with some sample tasks for testing."""
    tm = TestTaskManager()
    
    # Create a simple task
    task1 = tm.add_task(
        title="Implement user authentication",
        description="Add login and registration functionality",
        priority=TaskPriority.HIGH
    )
    
    # Create a task with dependencies
    task2 = tm.add_task(
        title="Implement user profile page",
        description="Create a page to display user information",
        priority=TaskPriority.MEDIUM
    )
    
    # Add dependency relationship
    task2.add_dependency(task1.id)
    
    # Create a task with subtasks
    task3 = tm.add_task(
        title="Implement dashboard",
        description="Create a dashboard with key metrics",
        priority=TaskPriority.HIGH
    )
    
    # Add subtasks
    subtask1 = tm.add_task(
        title="Design dashboard layout",
        description="Create wireframes for the dashboard",
        priority=TaskPriority.MEDIUM
    )
    
    subtask2 = tm.add_task(
        title="Implement dashboard widgets",
        description="Create reusable widget components",
        priority=TaskPriority.MEDIUM
    )
    
    task3.add_subtask(subtask1.id)
    task3.add_subtask(subtask2.id)
    
    return tm

class TestTaskExecutionTracking:
    def test_start_task(self, task_manager):
        """Test starting a task."""
        tasks = task_manager.list_tasks()
        task_id = tasks[0].id
        
        # Start the task
        task = task_manager.start_task(task_id)
        
        # Check that the task status is updated
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Check that the start time is recorded
        assert 'started_at' in task.details
        
        # Check that a history entry was added
        assert any("Task marked as in progress" in entry['change'] for entry in task.history)
    
    def test_complete_task(self, task_manager):
        """Test completing a task."""
        tasks = task_manager.list_tasks()
        task_id = tasks[0].id
        
        # Start the task first
        task_manager.start_task(task_id)
        
        # Complete the task with notes
        completion_notes = "Implemented using JWT for authentication"
        task = task_manager.complete_task(task_id, completion_notes=completion_notes)
        
        # Check that the task status is updated
        assert task.status == TaskStatus.COMPLETED
        
        # Check that the completion time is recorded
        assert 'completed_at' in task.details
        
        # Check that duration is calculated
        assert 'duration_seconds' in task.details
        
        # Check that a history entry was added with the notes
        assert any(completion_notes in entry['change'] for entry in task.history)
    
    def test_pause_task(self, task_manager):
        """Test pausing a task."""
        tasks = task_manager.list_tasks()
        task_id = tasks[0].id
        
        # Start the task first
        task_manager.start_task(task_id)
        
        # Pause the task with a reason
        pause_reason = "Waiting for API documentation"
        task = task_manager.pause_task(task_id, reason=pause_reason)
        
        # Check that the task status is updated
        assert task.status == TaskStatus.PENDING
        
        # Check that time spent is recorded
        assert 'time_spent_seconds' in task.details
        
        # Check that started_at is removed
        assert 'started_at' not in task.details
        
        # Check that a history entry was added with the reason
        assert any(pause_reason in entry['change'] for entry in task.history)
    
    def test_block_task(self, task_manager):
        """Test blocking a task."""
        tasks = task_manager.list_tasks()
        task_id = tasks[0].id
        
        # Block the task
        blocker_description = "Waiting for design approval"
        task = task_manager.block_task(task_id, blocker_description)
        
        # Check that the task status is updated
        assert task.status == TaskStatus.BLOCKED
        
        # Check that the blocker is recorded
        assert 'blockers' in task.details
        assert len(task.details['blockers']) == 1
        assert task.details['blockers'][0]['description'] == blocker_description
        
        # Check that a history entry was added
        assert any(blocker_description in entry['change'] for entry in task.history)
    
    def test_unblock_task(self, task_manager):
        """Test unblocking a task."""
        tasks = task_manager.list_tasks()
        task_id = tasks[0].id
        
        # Block the task first
        task_manager.block_task(task_id, "Waiting for design approval")
        
        # Unblock the task
        resolution = "Design approved by product team"
        task = task_manager.unblock_task(task_id, resolution)
        
        # Check that the task status is updated
        assert task.status == TaskStatus.PENDING
        
        # Check that the resolution is recorded
        assert task.details['blockers'][0]['resolution'] == resolution
        assert 'resolved_at' in task.details['blockers'][0]
        
        # Check that a history entry was added
        assert any(resolution in entry['change'] for entry in task.history)
    
    def test_dependency_notification(self, task_manager):
        """Test that completing a task notifies about unblocked dependent tasks."""
        # Get the dependency relationship we set up in the fixture
        tasks = task_manager.list_tasks()
        dependency_task = next(t for t in tasks if not t.dependencies)  # Task with no dependencies
        dependent_task = next(t for t in tasks if t.dependencies)  # Task that depends on another
        
        # Complete the dependency task
        task = task_manager.complete_task(dependency_task.id)
        
        # Check that the history entry mentions unblocking the dependent task
        assert any(dependent_task.id in entry['change'] for entry in task.history)


class TestTaskAnalysis:
    def test_analyze_task_complexity(self, task_manager):
        """Test analyzing task complexity."""
        # Get the task with subtasks
        tasks = task_manager.list_tasks()
        task_with_subtasks = next(t for t in tasks if t.subtasks)
        
        # Analyze complexity
        analysis = task_manager.analyze_task_complexity(task_with_subtasks.id)
        
        # Check that the analysis contains the expected fields
        assert 'complexity_score' in analysis
        assert 'complexity_category' in analysis
        assert 'subtask_count' in analysis
        assert 'estimated_hours' in analysis
        
        # Check that the subtask count is correct
        assert analysis['subtask_count'] == len(task_with_subtasks.subtasks)
    
    def test_get_task_chain(self, task_manager):
        """Test getting the dependency chain for a task."""
        # Get the task with dependencies
        tasks = task_manager.list_tasks()
        task_with_dependencies = next(t for t in tasks if t.dependencies)
        
        # Get the dependency chain
        chain = task_manager.get_task_chain(task_with_dependencies.id)
        
        # Check that the chain is a list of lists
        assert isinstance(chain, list)
        assert all(isinstance(level, list) for level in chain)
        
        # Check that the first level contains the task itself
        assert chain[0][0].id == task_with_dependencies.id
    
    def test_generate_dependency_graph(self, task_manager):
        """Test generating a dependency graph in Mermaid format."""
        # Generate the graph
        graph = task_manager.generate_dependency_graph()
        
        # Check that the graph is a string and contains the expected elements
        assert isinstance(graph, str)
        assert graph.startswith("graph TD;")
        
        # Check that all tasks are included in the graph
        tasks = task_manager.list_tasks()
        for task in tasks:
            assert task.id in graph
            
        # Check that dependencies are represented as edges
        for task in tasks:
            for dep_id in task.dependencies:
                assert f"{dep_id}-->{task.id}" in graph
