"""
Task Import/Export System for Tascade AI.

This module provides functionality for importing and exporting tasks in various formats,
enabling data portability and integration with other tools and systems.
"""

from typing import Dict, List, Any, Optional, Union, TextIO
from datetime import datetime
import json
import csv
import yaml
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
from pathlib import Path
import uuid
import re

from .models import Task, TaskStatus, TaskPriority


class TaskImportError(Exception):
    """Exception raised for errors during task import."""
    pass


class TaskExportError(Exception):
    """Exception raised for errors during task export."""
    pass


class TaskIO:
    """Task Import/Export System for data portability."""
    
    def __init__(self):
        """Initialize the Task Import/Export system."""
        self.supported_formats = {
            "json": {
                "import": self._import_json,
                "export": self._export_json,
                "extension": ".json"
            },
            "csv": {
                "import": self._import_csv,
                "export": self._export_csv,
                "extension": ".csv"
            },
            "yaml": {
                "import": self._import_yaml,
                "export": self._export_yaml,
                "extension": ".yaml"
            },
            "xml": {
                "import": self._import_xml,
                "export": self._export_xml,
                "extension": ".xml"
            },
            "markdown": {
                "import": self._import_markdown,
                "export": self._export_markdown,
                "extension": ".md"
            }
        }
    
    def import_tasks(self, file_path: str, format: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Import tasks from a file.
        
        Args:
            file_path: Path to the file to import
            format: Format of the file (json, csv, yaml, xml, markdown)
                   If None, will be inferred from file extension
            
        Returns:
            List of task dictionaries
        
        Raises:
            TaskImportError: If import fails
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise TaskImportError(f"File not found: {file_path}")
        
        # Infer format from file extension if not provided
        if format is None:
            _, ext = os.path.splitext(file_path)
            format = ext.lstrip('.').lower()
            
            # Handle .yml as yaml
            if format == "yml":
                format = "yaml"
        
        # Check if format is supported
        if format not in self.supported_formats:
            raise TaskImportError(f"Unsupported format: {format}")
        
        try:
            # Call the appropriate import function
            import_func = self.supported_formats[format]["import"]
            return import_func(file_path)
        except Exception as e:
            raise TaskImportError(f"Error importing tasks: {str(e)}")
    
    def export_tasks(self, tasks: List[Dict[str, Any]], file_path: str, 
                    format: Optional[str] = None) -> str:
        """
        Export tasks to a file.
        
        Args:
            tasks: List of task dictionaries to export
            file_path: Path to save the exported file
            format: Format to export (json, csv, yaml, xml, markdown)
                   If None, will be inferred from file extension
            
        Returns:
            Path to the exported file
        
        Raises:
            TaskExportError: If export fails
        """
        # Infer format from file extension if not provided
        if format is None:
            _, ext = os.path.splitext(file_path)
            format = ext.lstrip('.').lower()
            
            # Handle .yml as yaml
            if format == "yml":
                format = "yaml"
        
        # Check if format is supported
        if format not in self.supported_formats:
            raise TaskExportError(f"Unsupported format: {format}")
        
        try:
            # Call the appropriate export function
            export_func = self.supported_formats[format]["export"]
            export_func(tasks, file_path)
            return file_path
        except Exception as e:
            raise TaskExportError(f"Error exporting tasks: {str(e)}")
    
    def convert_format(self, tasks: List[Dict[str, Any]], 
                      from_format: str, to_format: str) -> str:
        """
        Convert tasks from one format to another without saving to file.
        
        Args:
            tasks: List of task dictionaries or raw content string
            from_format: Source format (json, csv, yaml, xml, markdown)
            to_format: Target format (json, csv, yaml, xml, markdown)
            
        Returns:
            String representation in the target format
        
        Raises:
            TaskImportError: If conversion fails
        """
        if from_format not in self.supported_formats:
            raise TaskImportError(f"Unsupported source format: {from_format}")
        
        if to_format not in self.supported_formats:
            raise TaskImportError(f"Unsupported target format: {to_format}")
        
        # If tasks is a string, parse it according to from_format
        if isinstance(tasks, str):
            try:
                if from_format == "json":
                    tasks = json.loads(tasks)
                elif from_format == "yaml":
                    tasks = yaml.safe_load(tasks)
                elif from_format in ["csv", "xml", "markdown"]:
                    raise TaskImportError(f"Direct string conversion not supported for {from_format}")
            except Exception as e:
                raise TaskImportError(f"Error parsing {from_format} content: {str(e)}")
        
        # Convert to the target format
        try:
            if to_format == "json":
                return json.dumps(tasks, indent=2)
            elif to_format == "yaml":
                return yaml.dump(tasks, default_flow_style=False)
            elif to_format == "csv":
                output = self._tasks_to_csv_string(tasks)
                return output
            elif to_format == "xml":
                return self._tasks_to_xml_string(tasks)
            elif to_format == "markdown":
                return self._tasks_to_markdown_string(tasks)
        except Exception as e:
            raise TaskExportError(f"Error converting to {to_format}: {str(e)}")
    
    def validate_import_data(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean imported task data.
        
        Args:
            tasks: List of task dictionaries to validate
            
        Returns:
            List of validated and cleaned task dictionaries
        """
        validated_tasks = []
        
        for task_data in tasks:
            # Ensure required fields
            if "title" not in task_data:
                task_data["title"] = "Imported Task"
            
            if "id" not in task_data:
                task_data["id"] = str(uuid.uuid4())
            
            # Validate status
            if "status" in task_data:
                try:
                    TaskStatus(task_data["status"])
                except ValueError:
                    task_data["status"] = TaskStatus.PENDING.value
            else:
                task_data["status"] = TaskStatus.PENDING.value
            
            # Validate priority
            if "priority" in task_data:
                try:
                    TaskPriority(task_data["priority"])
                except ValueError:
                    task_data["priority"] = TaskPriority.MEDIUM.value
            else:
                task_data["priority"] = TaskPriority.MEDIUM.value
            
            # Ensure created_at is a valid datetime
            if "created_at" in task_data and isinstance(task_data["created_at"], str):
                try:
                    datetime.fromisoformat(task_data["created_at"])
                except ValueError:
                    task_data["created_at"] = datetime.now().isoformat()
            else:
                task_data["created_at"] = datetime.now().isoformat()
            
            # Ensure dependencies is a list
            if "dependencies" in task_data and not isinstance(task_data["dependencies"], list):
                task_data["dependencies"] = []
            
            validated_tasks.append(task_data)
        
        return validated_tasks
    
    def _import_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tasks from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict) and "tasks" in data:
                tasks = data["tasks"]
            else:
                tasks = [data]  # Assume it's a single task
            
            return self.validate_import_data(tasks)
    
    def _export_json(self, tasks: List[Dict[str, Any]], file_path: str) -> None:
        """Export tasks to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def _import_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tasks from a CSV file."""
        tasks = []
        
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                task = {}
                
                # Process each field
                for key, value in row.items():
                    # Skip empty fields
                    if not value:
                        continue
                    
                    # Handle special fields
                    if key == "dependencies":
                        # Parse comma-separated dependencies
                        task[key] = [dep.strip() for dep in value.split(',') if dep.strip()]
                    elif key == "subtasks":
                        # Parse comma-separated subtasks
                        task[key] = [subtask.strip() for subtask in value.split(',') if subtask.strip()]
                    else:
                        task[key] = value
                
                tasks.append(task)
        
        return self.validate_import_data(tasks)
    
    def _export_csv(self, tasks: List[Dict[str, Any]], file_path: str) -> None:
        """Export tasks to a CSV file."""
        if not tasks:
            # Create empty file with headers
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "title", "description", "status", "priority", "dependencies"])
            return
        
        # Collect all possible fields
        fieldnames = set()
        for task in tasks:
            fieldnames.update(task.keys())
        
        # Ensure core fields are first in the order
        core_fields = ["id", "title", "description", "status", "priority", "dependencies"]
        ordered_fields = []
        
        for field in core_fields:
            if field in fieldnames:
                ordered_fields.append(field)
                fieldnames.remove(field)
        
        # Add remaining fields
        ordered_fields.extend(sorted(fieldnames))
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ordered_fields)
            writer.writeheader()
            
            for task in tasks:
                # Convert lists to comma-separated strings
                row = {}
                for key, value in task.items():
                    if isinstance(value, list):
                        row[key] = ','.join(str(item) for item in value)
                    else:
                        row[key] = value
                
                writer.writerow(row)
    
    def _tasks_to_csv_string(self, tasks: List[Dict[str, Any]]) -> str:
        """Convert tasks to a CSV string."""
        import io
        
        output = io.StringIO()
        
        if not tasks:
            return ""
        
        # Collect all possible fields
        fieldnames = set()
        for task in tasks:
            fieldnames.update(task.keys())
        
        # Ensure core fields are first in the order
        core_fields = ["id", "title", "description", "status", "priority", "dependencies"]
        ordered_fields = []
        
        for field in core_fields:
            if field in fieldnames:
                ordered_fields.append(field)
                fieldnames.remove(field)
        
        # Add remaining fields
        ordered_fields.extend(sorted(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=ordered_fields)
        writer.writeheader()
        
        for task in tasks:
            # Convert lists to comma-separated strings
            row = {}
            for key, value in task.items():
                if isinstance(value, list):
                    row[key] = ','.join(str(item) for item in value)
                else:
                    row[key] = value
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _import_yaml(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tasks from a YAML file."""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            
            # Handle different YAML structures
            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict) and "tasks" in data:
                tasks = data["tasks"]
            else:
                tasks = [data]  # Assume it's a single task
            
            return self.validate_import_data(tasks)
    
    def _export_yaml(self, tasks: List[Dict[str, Any]], file_path: str) -> None:
        """Export tasks to a YAML file."""
        with open(file_path, 'w') as f:
            yaml.dump(tasks, f, default_flow_style=False)
    
    def _import_xml(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tasks from an XML file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        tasks = []
        
        # Handle different XML structures
        if root.tag == "tasks":
            task_elements = root.findall("task")
        else:
            task_elements = [root]  # Assume it's a single task
        
        for task_elem in task_elements:
            task = {}
            
            # Process attributes
            for key, value in task_elem.attrib.items():
                task[key] = value
            
            # Process child elements
            for child in task_elem:
                # Handle special elements
                if child.tag == "dependencies":
                    task["dependencies"] = []
                    for dep in child.findall("dependency"):
                        task["dependencies"].append(dep.text)
                elif child.tag == "subtasks":
                    task["subtasks"] = []
                    for subtask in child.findall("subtask"):
                        task["subtasks"].append(subtask.text)
                else:
                    # Handle regular elements
                    task[child.tag] = child.text
            
            tasks.append(task)
        
        return self.validate_import_data(tasks)
    
    def _export_xml(self, tasks: List[Dict[str, Any]], file_path: str) -> None:
        """Export tasks to an XML file."""
        root = ET.Element("tasks")
        
        for task in tasks:
            task_elem = ET.SubElement(root, "task")
            
            for key, value in task.items():
                if key in ["id", "title"]:
                    # Use attributes for core identifiers
                    task_elem.set(key, str(value))
                elif isinstance(value, list):
                    # Handle list fields
                    list_elem = ET.SubElement(task_elem, key)
                    for item in value:
                        item_elem = ET.SubElement(list_elem, key[:-1])  # Remove trailing 's'
                        item_elem.text = str(item)
                else:
                    # Handle regular fields
                    field_elem = ET.SubElement(task_elem, key)
                    field_elem.text = str(value)
        
        # Format the XML with proper indentation
        xml_str = ET.tostring(root, encoding="unicode")
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        with open(file_path, 'w') as f:
            f.write(pretty_xml)
    
    def _tasks_to_xml_string(self, tasks: List[Dict[str, Any]]) -> str:
        """Convert tasks to an XML string."""
        root = ET.Element("tasks")
        
        for task in tasks:
            task_elem = ET.SubElement(root, "task")
            
            for key, value in task.items():
                if key in ["id", "title"]:
                    # Use attributes for core identifiers
                    task_elem.set(key, str(value))
                elif isinstance(value, list):
                    # Handle list fields
                    list_elem = ET.SubElement(task_elem, key)
                    for item in value:
                        item_elem = ET.SubElement(list_elem, key[:-1])  # Remove trailing 's'
                        item_elem.text = str(item)
                else:
                    # Handle regular fields
                    field_elem = ET.SubElement(task_elem, key)
                    field_elem.text = str(value)
        
        # Format the XML with proper indentation
        xml_str = ET.tostring(root, encoding="unicode")
        dom = xml.dom.minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")
    
    def _import_markdown(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tasks from a Markdown file."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        tasks = []
        
        # Parse task sections
        task_sections = re.split(r'(?m)^#{1,2}\s+', content)[1:]  # Skip first empty section
        
        for section in task_sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # First line is the title (from the heading)
            title = lines[0].strip()
            task = {"title": title}
            
            # Parse task attributes
            current_field = None
            field_content = []
            
            for line in lines[1:]:
                # Check for field markers
                field_match = re.match(r'\*\*([^:]+):\*\*\s*(.*)', line)
                if field_match:
                    # Save previous field if any
                    if current_field and field_content:
                        task[current_field.lower()] = '\n'.join(field_content).strip()
                        field_content = []
                    
                    # Start new field
                    current_field = field_match.group(1).strip()
                    content_start = field_match.group(2).strip()
                    if content_start:
                        field_content.append(content_start)
                elif current_field:
                    # Continue previous field
                    field_content.append(line)
            
            # Save last field
            if current_field and field_content:
                task[current_field.lower()] = '\n'.join(field_content).strip()
            
            # Handle special fields
            if "dependencies" in task and isinstance(task["dependencies"], str):
                task["dependencies"] = [dep.strip() for dep in task["dependencies"].split(',') if dep.strip()]
            
            if "id" not in task:
                task["id"] = str(uuid.uuid4())
            
            tasks.append(task)
        
        return self.validate_import_data(tasks)
    
    def _export_markdown(self, tasks: List[Dict[str, Any]], file_path: str) -> None:
        """Export tasks to a Markdown file."""
        markdown = self._tasks_to_markdown_string(tasks)
        
        with open(file_path, 'w') as f:
            f.write(markdown)
    
    def _tasks_to_markdown_string(self, tasks: List[Dict[str, Any]]) -> str:
        """Convert tasks to a Markdown string."""
        lines = ["# Task Export", ""]
        
        for task in tasks:
            # Task title as heading
            lines.append(f"## {task.get('title', 'Untitled Task')}")
            
            # Task ID
            lines.append(f"**ID:** {task.get('id', '')}")
            
            # Core fields
            if "description" in task:
                lines.append(f"**Description:**\n{task['description']}")
            
            if "status" in task:
                lines.append(f"**Status:** {task['status']}")
            
            if "priority" in task:
                lines.append(f"**Priority:** {task['priority']}")
            
            # Dependencies
            if "dependencies" in task and task["dependencies"]:
                if isinstance(task["dependencies"], list):
                    deps = ", ".join(task["dependencies"])
                else:
                    deps = str(task["dependencies"])
                lines.append(f"**Dependencies:** {deps}")
            
            # Other fields
            for key, value in task.items():
                if key not in ["id", "title", "description", "status", "priority", "dependencies"]:
                    if isinstance(value, list):
                        value_str = ", ".join(str(item) for item in value)
                    else:
                        value_str = str(value)
                    
                    lines.append(f"**{key.capitalize()}:** {value_str}")
            
            # Add separator
            lines.append("")
        
        return "\n".join(lines)
