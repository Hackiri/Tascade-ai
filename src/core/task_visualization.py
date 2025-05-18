"""
Task Visualization System for Tascade AI.

This module provides functionality for generating visual representations
of tasks, dependencies, and timelines.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import json
import os
from enum import Enum
from pathlib import Path
import time
import math

from .models import Task, TaskStatus, TaskPriority


class ChartType(Enum):
    """Types of charts that can be generated."""
    GANTT = "gantt"
    BURNDOWN = "burndown"
    DEPENDENCY = "dependency"
    STATUS_DISTRIBUTION = "status_distribution"
    PRIORITY_DISTRIBUTION = "priority_distribution"
    TIMELINE = "timeline"


class TaskVisualizationSystem:
    """Task Visualization System for generating visual representations of tasks."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the Task Visualization system.
        
        Args:
            output_dir: Optional directory for storing visualization outputs
        """
        self.output_dir = output_dir
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_gantt_chart(self, tasks: List[Task], 
                           title: str = "Task Timeline",
                           include_completed: bool = True) -> str:
        """
        Generate a Mermaid Gantt chart for the given tasks.
        
        Args:
            tasks: List of tasks to include in the chart
            title: Title of the chart
            include_completed: Whether to include completed tasks
            
        Returns:
            Mermaid Gantt chart code
        """
        # Filter tasks if needed
        if not include_completed:
            tasks = [t for t in tasks if t.status != TaskStatus.DONE]
        
        # Start building the Gantt chart
        gantt = [
            "```mermaid",
            "gantt",
            f"    title {title}",
            "    dateFormat  YYYY-MM-DD",
            "    axisFormat %Y-%m-%d",
            "    excludes weekends"
        ]
        
        # Add sections for each priority
        priorities = {
            TaskPriority.HIGH: "High Priority",
            TaskPriority.MEDIUM: "Medium Priority",
            TaskPriority.LOW: "Low Priority"
        }
        
        # Track tasks by priority
        tasks_by_priority = {
            TaskPriority.HIGH: [],
            TaskPriority.MEDIUM: [],
            TaskPriority.LOW: []
        }
        
        # Group tasks by priority
        for task in tasks:
            if task.priority in tasks_by_priority:
                tasks_by_priority[task.priority].append(task)
            else:
                # Default to medium priority if not specified
                tasks_by_priority[TaskPriority.MEDIUM].append(task)
        
        # Add tasks to the chart by priority
        for priority, priority_tasks in tasks_by_priority.items():
            if not priority_tasks:
                continue
            
            gantt.append(f"    section {priorities[priority]}")
            
            for task in priority_tasks:
                # Determine task start and end dates
                start_date = task.started_at or task.created_at or datetime.now()
                
                # For completed tasks, use the actual completion date
                if task.status == TaskStatus.DONE and task.completed_at:
                    end_date = task.completed_at
                # For tasks with due dates, use the due date
                elif task.due_date:
                    end_date = task.due_date
                # Otherwise, estimate based on complexity or default duration
                else:
                    # Default to 3 days if no other information
                    end_date = start_date + timedelta(days=3)
                
                # Format dates
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                
                # Determine task status for display
                status_display = ""
                if task.status == TaskStatus.DONE:
                    status_display = "done"
                elif task.status == TaskStatus.IN_PROGRESS:
                    status_display = "active"
                
                # Add the task to the chart
                gantt.append(f"    {task.title} :{status_display}, {start_str}, {end_str}")
                
                # Add dependencies if any
                if task.dependencies:
                    for dep_id in task.dependencies:
                        gantt.append(f"    {task.id} requires {dep_id}")
        
        # Close the Mermaid code block
        gantt.append("```")
        
        # Join the lines into a single string
        gantt_chart = "\n".join(gantt)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"gantt_chart_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(gantt_chart)
        
        return gantt_chart
    
    def generate_dependency_graph(self, tasks: List[Task], 
                                title: str = "Task Dependencies") -> str:
        """
        Generate a Mermaid graph diagram showing task dependencies.
        
        Args:
            tasks: List of tasks to include in the graph
            title: Title of the graph
            
        Returns:
            Mermaid graph diagram code
        """
        # Create a mapping of task IDs to tasks for easy lookup
        task_map = {task.id: task for task in tasks}
        
        # Start building the graph
        graph = [
            "```mermaid",
            "graph TD",
            f"    title[{title}]",
            "    classDef done fill:#ccffcc,stroke:#004400",
            "    classDef inProgress fill:#ffffcc,stroke:#444400",
            "    classDef pending fill:#ffcccc,stroke:#440000",
            "    classDef blocked fill:#ccccff,stroke:#000044"
        ]
        
        # Add nodes for each task
        for task in tasks:
            # Create node with task ID and title
            graph.append(f"    {task.id}[\"{task.id}: {task.title}\"]")
            
            # Add class based on status
            if task.status == TaskStatus.DONE:
                graph.append(f"    class {task.id} done")
            elif task.status == TaskStatus.IN_PROGRESS:
                graph.append(f"    class {task.id} inProgress")
            elif task.status == TaskStatus.PENDING:
                # Check if blocked by dependencies
                blocked = False
                if task.dependencies:
                    for dep_id in task.dependencies:
                        if dep_id in task_map and task_map[dep_id].status != TaskStatus.DONE:
                            blocked = True
                            break
                
                if blocked:
                    graph.append(f"    class {task.id} blocked")
                else:
                    graph.append(f"    class {task.id} pending")
        
        # Add edges for dependencies
        for task in tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id in task_map:
                        graph.append(f"    {dep_id} --> {task.id}")
        
        # Close the Mermaid code block
        graph.append("```")
        
        # Join the lines into a single string
        dependency_graph = "\n".join(graph)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"dependency_graph_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(dependency_graph)
        
        return dependency_graph
    
    def generate_burndown_chart(self, tasks: List[Task], 
                              start_date: datetime,
                              end_date: datetime,
                              title: str = "Burndown Chart") -> str:
        """
        Generate a Mermaid line chart showing task burndown.
        
        Args:
            tasks: List of tasks to include in the chart
            start_date: Start date for the chart
            end_date: End date for the chart
            title: Title of the chart
            
        Returns:
            Mermaid line chart code
        """
        # Calculate the number of days in the chart
        days = (end_date - start_date).days + 1
        
        # Create a list of dates for the chart
        dates = [start_date + timedelta(days=i) for i in range(days)]
        
        # Count the number of tasks completed on each date
        completed_tasks = []
        remaining_tasks = len(tasks)
        
        for date in dates:
            # Count tasks completed on or before this date
            completed_on_date = sum(1 for task in tasks 
                                  if task.completed_at and task.completed_at.date() <= date.date())
            
            completed_tasks.append(completed_on_date)
        
        # Calculate remaining tasks for each date
        remaining_tasks_by_date = [remaining_tasks - completed for completed in completed_tasks]
        
        # Calculate ideal burndown (straight line from start to end)
        ideal_burndown = []
        for i in range(days):
            ideal = remaining_tasks - (i * remaining_tasks / (days - 1))
            ideal_burndown.append(round(ideal, 1))
        
        # Start building the chart
        chart = [
            "```mermaid",
            "%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffcccc', 'lineColor': '#ff0000', 'secondaryColor': '#ccffcc'}}}%%",
            "xychart-beta",
            f"    title {title}",
            "    x-axis [" + ", ".join([date.strftime("%m-%d") for date in dates]) + "]",
            "    y-axis \"Tasks Remaining\"",
            "    line [" + ", ".join([str(count) for count in remaining_tasks_by_date]) + "]",
            "    line [" + ", ".join([str(count) for count in ideal_burndown]) + "]"
        ]
        
        # Close the Mermaid code block
        chart.append("```")
        
        # Join the lines into a single string
        burndown_chart = "\n".join(chart)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"burndown_chart_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(burndown_chart)
        
        return burndown_chart
    
    def generate_status_distribution(self, tasks: List[Task],
                                   title: str = "Task Status Distribution") -> str:
        """
        Generate a Mermaid pie chart showing task status distribution.
        
        Args:
            tasks: List of tasks to include in the chart
            title: Title of the chart
            
        Returns:
            Mermaid pie chart code
        """
        # Count tasks by status
        status_counts = {}
        for task in tasks:
            status = task.status.value if hasattr(task.status, "value") else str(task.status)
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Start building the chart
        chart = [
            "```mermaid",
            "pie",
            f"    title {title}"
        ]
        
        # Add slices for each status
        for status, count in status_counts.items():
            chart.append(f"    \"{status}\" : {count}")
        
        # Close the Mermaid code block
        chart.append("```")
        
        # Join the lines into a single string
        pie_chart = "\n".join(chart)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"status_distribution_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(pie_chart)
        
        return pie_chart
    
    def generate_priority_distribution(self, tasks: List[Task],
                                     title: str = "Task Priority Distribution") -> str:
        """
        Generate a Mermaid pie chart showing task priority distribution.
        
        Args:
            tasks: List of tasks to include in the chart
            title: Title of the chart
            
        Returns:
            Mermaid pie chart code
        """
        # Count tasks by priority
        priority_counts = {}
        for task in tasks:
            priority = task.priority.value if hasattr(task.priority, "value") else str(task.priority)
            if priority not in priority_counts:
                priority_counts[priority] = 0
            priority_counts[priority] += 1
        
        # Start building the chart
        chart = [
            "```mermaid",
            "pie",
            f"    title {title}"
        ]
        
        # Add slices for each priority
        for priority, count in priority_counts.items():
            chart.append(f"    \"{priority}\" : {count}")
        
        # Close the Mermaid code block
        chart.append("```")
        
        # Join the lines into a single string
        pie_chart = "\n".join(chart)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"priority_distribution_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(pie_chart)
        
        return pie_chart
    
    def generate_timeline(self, tasks: List[Task],
                        title: str = "Task Timeline") -> str:
        """
        Generate a Mermaid timeline diagram showing task start and completion dates.
        
        Args:
            tasks: List of tasks to include in the timeline
            title: Title of the timeline
            
        Returns:
            Mermaid timeline diagram code
        """
        # Start building the timeline
        timeline = [
            "```mermaid",
            "timeline",
            f"    title {title}"
        ]
        
        # Group tasks by month
        tasks_by_month = {}
        for task in tasks:
            # Use created_at as the default date
            date = task.created_at
            
            # For completed tasks, use completed_at
            if task.status == TaskStatus.DONE and task.completed_at:
                date = task.completed_at
            
            if not date:
                continue
            
            # Format month key
            month_key = date.strftime("%Y-%m")
            
            if month_key not in tasks_by_month:
                tasks_by_month[month_key] = []
            
            tasks_by_month[month_key].append(task)
        
        # Sort months
        sorted_months = sorted(tasks_by_month.keys())
        
        # Add sections for each month
        for month in sorted_months:
            month_tasks = tasks_by_month[month]
            
            # Format month display
            month_display = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
            timeline.append(f"    section {month_display}")
            
            # Add tasks for this month
            for task in month_tasks:
                status_marker = ""
                if task.status == TaskStatus.DONE:
                    status_marker = "✅ "
                elif task.status == TaskStatus.IN_PROGRESS:
                    status_marker = "🔄 "
                elif task.status == TaskStatus.PENDING:
                    status_marker = "⏳ "
                
                timeline.append(f"    {status_marker}{task.title}")
        
        # Close the Mermaid code block
        timeline.append("```")
        
        # Join the lines into a single string
        timeline_diagram = "\n".join(timeline)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"timeline_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(timeline_diagram)
        
        return timeline_diagram
    
    def generate_chart(self, tasks: List[Task], 
                     chart_type: Union[ChartType, str],
                     title: Optional[str] = None,
                     **kwargs) -> str:
        """
        Generate a chart of the specified type.
        
        Args:
            tasks: List of tasks to include in the chart
            chart_type: Type of chart to generate
            title: Title of the chart
            **kwargs: Additional arguments for the specific chart type
            
        Returns:
            Mermaid chart code
        """
        # Convert string chart type to enum if necessary
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type)
        
        # Generate default title if not provided
        if not title:
            title = f"Task {chart_type.value.replace('_', ' ').title()}"
        
        # Generate the requested chart type
        if chart_type == ChartType.GANTT:
            return self.generate_gantt_chart(tasks, title, **kwargs)
        
        elif chart_type == ChartType.DEPENDENCY:
            return self.generate_dependency_graph(tasks, title)
        
        elif chart_type == ChartType.BURNDOWN:
            # Get start and end dates from kwargs or use defaults
            start_date = kwargs.get("start_date")
            end_date = kwargs.get("end_date")
            
            if not start_date:
                # Use earliest task creation date or today
                start_date = min((task.created_at for task in tasks if task.created_at), 
                               default=datetime.now())
            
            if not end_date:
                # Use latest task due date or today + 30 days
                end_date = max((task.due_date for task in tasks if task.due_date), 
                             default=datetime.now() + timedelta(days=30))
            
            return self.generate_burndown_chart(tasks, start_date, end_date, title)
        
        elif chart_type == ChartType.STATUS_DISTRIBUTION:
            return self.generate_status_distribution(tasks, title)
        
        elif chart_type == ChartType.PRIORITY_DISTRIBUTION:
            return self.generate_priority_distribution(tasks, title)
        
        elif chart_type == ChartType.TIMELINE:
            return self.generate_timeline(tasks, title)
        
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
    
    def generate_dashboard(self, tasks: List[Task], 
                         title: str = "Task Dashboard",
                         include_charts: Optional[List[ChartType]] = None) -> str:
        """
        Generate a comprehensive dashboard with multiple charts.
        
        Args:
            tasks: List of tasks to include in the dashboard
            title: Title of the dashboard
            include_charts: List of chart types to include
            
        Returns:
            Markdown dashboard with multiple charts
        """
        # Default charts to include if not specified
        if not include_charts:
            include_charts = [
                ChartType.STATUS_DISTRIBUTION,
                ChartType.PRIORITY_DISTRIBUTION,
                ChartType.GANTT,
                ChartType.DEPENDENCY
            ]
        
        # Start building the dashboard
        dashboard = [
            f"# {title}",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Tasks: {len(tasks)}",
            ""
        ]
        
        # Add each requested chart
        for chart_type in include_charts:
            dashboard.append(f"## {chart_type.value.replace('_', ' ').title()}")
            dashboard.append(self.generate_chart(tasks, chart_type))
            dashboard.append("")
        
        # Add task summary table
        dashboard.append("## Task Summary")
        dashboard.append("| ID | Title | Status | Priority | Dependencies |")
        dashboard.append("|----|-------|--------|----------|--------------|")
        
        for task in sorted(tasks, key=lambda t: t.id):
            status = task.status.value if hasattr(task.status, "value") else str(task.status)
            priority = task.priority.value if hasattr(task.priority, "value") else str(task.priority)
            dependencies = ", ".join(task.dependencies) if task.dependencies else "-"
            
            dashboard.append(f"| {task.id} | {task.title} | {status} | {priority} | {dependencies} |")
        
        # Join the lines into a single string
        dashboard_md = "\n".join(dashboard)
        
        # Save to file if output directory is specified
        if self.output_dir:
            file_path = os.path.join(self.output_dir, f"dashboard_{int(time.time())}.md")
            with open(file_path, 'w') as f:
                f.write(dashboard_md)
        
        return dashboard_md
