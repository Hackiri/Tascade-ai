"""
Task Template System for Tascade AI.

This module provides functionality for creating, managing, and applying templates
for common task types to enhance productivity and standardization.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import uuid
import os
from pathlib import Path
import copy

from .models import Task, TaskStatus, TaskPriority


class TaskTemplate:
    """Represents a reusable task template."""
    
    def __init__(self, 
                 id: str,
                 name: str,
                 description: str,
                 category: str,
                 created_at: datetime,
                 updated_at: Optional[datetime] = None,
                 task_defaults: Optional[Dict[str, Any]] = None,
                 subtask_templates: Optional[List[Dict[str, Any]]] = None,
                 verification_criteria: Optional[List[str]] = None,
                 implementation_guide: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        """
        Initialize a task template.
        
        Args:
            id: Unique identifier for the template
            name: Name of the template
            description: Description of the template
            category: Category for organizing templates
            created_at: When the template was created
            updated_at: When the template was last updated
            task_defaults: Default values for task fields
            subtask_templates: Templates for subtasks
            verification_criteria: Default verification criteria
            implementation_guide: Default implementation guide
            tags: Tags for categorizing the template
        """
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.created_at = created_at
        self.updated_at = updated_at or created_at
        self.task_defaults = task_defaults or {}
        self.subtask_templates = subtask_templates or []
        self.verification_criteria = verification_criteria or []
        self.implementation_guide = implementation_guide or ""
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "task_defaults": self.task_defaults,
            "subtask_templates": self.subtask_templates,
            "verification_criteria": self.verification_criteria,
            "implementation_guide": self.implementation_guide,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskTemplate':
        """Create a template from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", "General"),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None,
            task_defaults=data.get("task_defaults", {}),
            subtask_templates=data.get("subtask_templates", []),
            verification_criteria=data.get("verification_criteria", []),
            implementation_guide=data.get("implementation_guide", ""),
            tags=data.get("tags", [])
        )


class TaskTemplateSystem:
    """Task Template System for managing reusable task templates."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Task Template system.
        
        Args:
            data_dir: Optional directory for storing template data
        """
        self.data_dir = data_dir
        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
            self.templates_file = os.path.join(self.data_dir, "templates.json")
            self.templates = self._load_templates()
        else:
            # In-memory storage
            self.templates = {}  # id -> template
    
    def create_template(self, name: str, description: str, category: str,
                       task_defaults: Dict[str, Any],
                       subtask_templates: Optional[List[Dict[str, Any]]] = None,
                       verification_criteria: Optional[List[str]] = None,
                       implementation_guide: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new task template.
        
        Args:
            name: Name of the template
            description: Description of the template
            category: Category for organizing templates
            task_defaults: Default values for task fields
            subtask_templates: Templates for subtasks
            verification_criteria: Default verification criteria
            implementation_guide: Default implementation guide
            tags: Tags for categorizing the template
            
        Returns:
            Dictionary with the created template
        """
        # Generate a unique ID
        template_id = str(uuid.uuid4())
        
        # Create the template
        template = TaskTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            created_at=datetime.now(),
            task_defaults=task_defaults,
            subtask_templates=subtask_templates,
            verification_criteria=verification_criteria,
            implementation_guide=implementation_guide,
            tags=tags
        )
        
        # Add to templates
        self.templates[template_id] = template
        
        # Save templates
        self._save_templates()
        
        return template.to_dict()
    
    def update_template(self, template_id: str, 
                       updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing task template.
        
        Args:
            template_id: ID of the template to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with the updated template
        """
        # Check if template exists
        if template_id not in self.templates:
            return {"error": f"Template with ID {template_id} not found"}
        
        # Get the template
        template = self.templates[template_id]
        
        # Update fields
        if "name" in updates:
            template.name = updates["name"]
        if "description" in updates:
            template.description = updates["description"]
        if "category" in updates:
            template.category = updates["category"]
        if "task_defaults" in updates:
            template.task_defaults = updates["task_defaults"]
        if "subtask_templates" in updates:
            template.subtask_templates = updates["subtask_templates"]
        if "verification_criteria" in updates:
            template.verification_criteria = updates["verification_criteria"]
        if "implementation_guide" in updates:
            template.implementation_guide = updates["implementation_guide"]
        if "tags" in updates:
            template.tags = updates["tags"]
        
        # Update the updated_at timestamp
        template.updated_at = datetime.now()
        
        # Save templates
        self._save_templates()
        
        return template.to_dict()
    
    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """
        Delete a task template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            Dictionary with the result of the operation
        """
        # Check if template exists
        if template_id not in self.templates:
            return {"error": f"Template with ID {template_id} not found"}
        
        # Get template info before deletion
        template_name = self.templates[template_id].name
        
        # Delete the template
        del self.templates[template_id]
        
        # Save templates
        self._save_templates()
        
        return {
            "success": True,
            "message": f"Template '{template_name}' (ID: {template_id}) deleted successfully"
        }
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        Get a task template by ID.
        
        Args:
            template_id: ID of the template to get
            
        Returns:
            Dictionary with the template data
        """
        # Check if template exists
        if template_id not in self.templates:
            return {"error": f"Template with ID {template_id} not found"}
        
        # Return the template
        return self.templates[template_id].to_dict()
    
    def list_templates(self, category: Optional[str] = None, 
                      tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all task templates, optionally filtered by category or tags.
        
        Args:
            category: Optional category to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = list(self.templates.values())
        
        # Filter by category if specified
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filter by tags if specified
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        # Convert to dictionaries
        return [t.to_dict() for t in templates]
    
    def get_categories(self) -> List[str]:
        """
        Get all template categories.
        
        Returns:
            List of category names
        """
        return sorted(list(set(t.category for t in self.templates.values())))
    
    def get_tags(self) -> List[str]:
        """
        Get all template tags.
        
        Returns:
            List of tag names
        """
        tags = set()
        for template in self.templates.values():
            tags.update(template.tags)
        return sorted(list(tags))
    
    def apply_template(self, template_id: str, 
                      custom_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply a template to create a new task.
        
        Args:
            template_id: ID of the template to apply
            custom_values: Optional custom values to override template defaults
            
        Returns:
            Dictionary with the task data created from the template
        """
        # Check if template exists
        if template_id not in self.templates:
            return {"error": f"Template with ID {template_id} not found"}
        
        # Get the template
        template = self.templates[template_id]
        
        # Start with template defaults
        task_data = copy.deepcopy(template.task_defaults)
        
        # Override with custom values if provided
        if custom_values:
            for key, value in custom_values.items():
                task_data[key] = value
        
        # Ensure required fields
        if "id" not in task_data:
            task_data["id"] = str(uuid.uuid4())
        if "created_at" not in task_data:
            task_data["created_at"] = datetime.now().isoformat()
        if "status" not in task_data:
            task_data["status"] = TaskStatus.PENDING.value
        
        # Add template metadata
        task_data["template_id"] = template_id
        task_data["template_name"] = template.name
        
        # Process subtasks if any
        subtasks = []
        if template.subtask_templates:
            for subtask_template in template.subtask_templates:
                subtask = copy.deepcopy(subtask_template)
                if "id" not in subtask:
                    subtask["id"] = f"{task_data['id']}.{len(subtasks) + 1}"
                subtasks.append(subtask)
        
        # Add verification criteria and implementation guide
        if template.verification_criteria:
            task_data["verification_criteria"] = template.verification_criteria
        
        if template.implementation_guide:
            if "execution_context" not in task_data:
                task_data["execution_context"] = {}
            task_data["execution_context"]["implementation_guide"] = template.implementation_guide
        
        return {
            "task": task_data,
            "subtasks": subtasks
        }
    
    def create_template_from_task(self, task: Task, name: str, 
                                category: str, 
                                include_subtasks: bool = True,
                                tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a template from an existing task.
        
        Args:
            task: The task to create a template from
            name: Name for the new template
            category: Category for the new template
            include_subtasks: Whether to include subtasks in the template
            tags: Optional tags for the template
            
        Returns:
            Dictionary with the created template
        """
        # Create task defaults from the task
        task_dict = {
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value if hasattr(task, "priority") else TaskPriority.MEDIUM.value
        }
        
        # Add verification criteria if available
        verification_criteria = None
        if hasattr(task, "verification_criteria") and task.verification_criteria:
            verification_criteria = task.verification_criteria if isinstance(task.verification_criteria, list) else [task.verification_criteria]
        
        # Add implementation guide if available
        implementation_guide = None
        if (hasattr(task, "execution_context") and task.execution_context and 
            "implementation_guide" in task.execution_context):
            implementation_guide = task.execution_context["implementation_guide"]
        
        # Process subtasks if requested
        subtask_templates = None
        if include_subtasks and hasattr(task, "subtasks") and task.subtasks:
            subtask_templates = []
            for subtask_id in task.subtasks:
                # This would need to be expanded to actually get the subtask data
                # For now, just add a placeholder
                subtask_templates.append({
                    "title": f"Subtask for {task.title}",
                    "description": "Subtask description"
                })
        
        # Create the template
        return self.create_template(
            name=name,
            description=f"Template created from task: {task.title}",
            category=category,
            task_defaults=task_dict,
            subtask_templates=subtask_templates,
            verification_criteria=verification_criteria,
            implementation_guide=implementation_guide,
            tags=tags
        )
    
    def _load_templates(self) -> Dict[str, TaskTemplate]:
        """Load templates from the data file."""
        if self.data_dir and os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r') as f:
                    templates_data = json.load(f)
                    
                templates = {}
                for template_id, template_data in templates_data.items():
                    templates[template_id] = TaskTemplate.from_dict(template_data)
                
                return templates
            except Exception as e:
                print(f"Error loading templates: {e}")
                return {}
        return {}
    
    def _save_templates(self) -> None:
        """Save templates to the data file."""
        if not self.data_dir:
            return
        
        try:
            templates_data = {
                template_id: template.to_dict()
                for template_id, template in self.templates.items()
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)
        except Exception as e:
            print(f"Error saving templates: {e}")
