#!/usr/bin/env python3
"""
Visualization demo for Tascade AI.

This script demonstrates the advanced visualization capabilities of Tascade AI
for time tracking data.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import random

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.visualization.time_charts import (
    TimeSeriesChart, GanttChart, CalendarHeatmap, ActivityHeatmap
)
from src.visualization.productivity_charts import (
    ProductivityTrendChart, ProductivityComparisonChart
)
from src.visualization.task_charts import (
    TaskCompletionChart, TaskDistributionChart, TaskRelationshipChart
)
from src.visualization.dashboard import Dashboard


def generate_sample_time_entries(num_entries=100, num_tasks=5, start_date=None, end_date=None):
    """Generate sample time entries for visualization."""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)
    
    if end_date is None:
        end_date = datetime.now()
    
    # Generate task IDs
    task_ids = [f"task_{i}" for i in range(1, num_tasks + 1)]
    
    # Generate task names
    task_names = {
        "task_1": "Feature Development",
        "task_2": "Bug Fixing",
        "task_3": "Documentation",
        "task_4": "Testing",
        "task_5": "Meetings"
    }
    
    # Generate categories
    categories = ["Development", "Planning", "Research", "Communication"]
    
    # Generate time entries
    time_entries = []
    
    for _ in range(num_entries):
        # Random task
        task_id = random.choice(task_ids)
        
        # Random category
        category = random.choice(categories)
        
        # Random date between start and end
        days_range = (end_date - start_date).days
        random_days = random.randint(0, days_range)
        entry_date = start_date + timedelta(days=random_days)
        
        # Random time
        hour = random.randint(8, 17)
        minute = random.randint(0, 59)
        entry_date = entry_date.replace(hour=hour, minute=minute)
        
        # Random duration (15 minutes to 3 hours)
        duration_minutes = random.randint(15, 180)
        duration_seconds = duration_minutes * 60
        
        # End time
        end_time = entry_date + timedelta(minutes=duration_minutes)
        
        # Create entry
        entry = {
            "id": f"entry_{_}",
            "task_id": task_id,
            "task_name": task_names.get(task_id, task_id),
            "category": category,
            "start_time": entry_date.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "description": f"Working on {task_names.get(task_id, task_id)}",
            "completed": random.random() > 0.2  # 80% chance of completion
        }
        
        time_entries.append(entry)
    
    return time_entries


def generate_sample_task_relationships(num_tasks=5):
    """Generate sample task relationships for visualization."""
    # Generate task names
    task_names = {
        "task_1": "Feature Development",
        "task_2": "Bug Fixing",
        "task_3": "Documentation",
        "task_4": "Testing",
        "task_5": "Meetings"
    }
    
    # Generate relationships
    relationships = [
        {"task": "Feature Development", "related_to": "Bug Fixing", "category": "Development"},
        {"task": "Feature Development", "related_to": "Testing", "category": "Development"},
        {"task": "Bug Fixing", "related_to": "Testing", "category": "Quality Assurance"},
        {"task": "Testing", "related_to": "Documentation", "category": "Quality Assurance"},
        {"task": "Meetings", "related_to": "Feature Development", "category": "Planning"},
        {"task": "Meetings", "related_to": "Documentation", "category": "Planning"},
        {"task": "Documentation", "related_to": "Feature Development", "category": "Documentation"}
    ]
    
    return relationships


def demo_time_series_chart(time_entries, output_dir):
    """Demonstrate time series chart."""
    print("Generating time series chart...")
    
    chart = TimeSeriesChart(
        data=time_entries,
        time_field="start_time",
        value_field="duration_seconds",
        category_field="task_name",
        chart_type="line",
        time_grouping="daily",
        title="Time Spent by Task",
        subtitle="Daily time tracking data",
        stacked=False,
        show_markers=True
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "time_series_chart.png")
    chart.save(output_path)
    
    print(f"Time series chart saved to: {output_path}")
    
    return chart


def demo_gantt_chart(time_entries, output_dir):
    """Demonstrate Gantt chart."""
    print("Generating Gantt chart...")
    
    # Use a subset of entries for clarity
    subset_entries = time_entries[:20]
    
    chart = GanttChart(
        data=subset_entries,
        task_field="task_name",
        start_field="start_time",
        end_field="end_time",
        category_field="category",
        title="Task Timeline",
        subtitle="Gantt chart of recent tasks",
        width=12,
        height=8
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "gantt_chart.png")
    chart.save(output_path)
    
    print(f"Gantt chart saved to: {output_path}")
    
    return chart


def demo_calendar_heatmap(time_entries, output_dir):
    """Demonstrate calendar heatmap."""
    print("Generating calendar heatmap...")
    
    chart = CalendarHeatmap(
        data=time_entries,
        date_field="start_time",
        value_field="duration_seconds",
        title="Daily Activity Heatmap",
        subtitle="Time spent per day",
        width=12,
        height=10
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "calendar_heatmap.png")
    chart.save(output_path)
    
    print(f"Calendar heatmap saved to: {output_path}")
    
    return chart


def demo_activity_heatmap(time_entries, output_dir):
    """Demonstrate activity heatmap."""
    print("Generating activity heatmap...")
    
    chart = ActivityHeatmap(
        data=time_entries,
        time_field="start_time",
        value_field="duration_seconds",
        title="Activity Patterns",
        subtitle="Time spent by hour and day of week"
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "activity_heatmap.png")
    chart.save(output_path)
    
    print(f"Activity heatmap saved to: {output_path}")
    
    return chart


def demo_productivity_trend(time_entries, output_dir):
    """Demonstrate productivity trend chart."""
    print("Generating productivity trend chart...")
    
    chart = ProductivityTrendChart(
        data=time_entries,
        time_field="start_time",
        value_field="duration_seconds",
        category_field="category",
        title="Productivity Trend",
        subtitle="Time spent by category over time",
        show_trend=True,
        trend_window=7
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "productivity_trend.png")
    chart.save(output_path)
    
    print(f"Productivity trend chart saved to: {output_path}")
    
    return chart


def demo_productivity_comparison(time_entries, output_dir):
    """Demonstrate productivity comparison chart."""
    print("Generating productivity comparison chart...")
    
    chart = ProductivityComparisonChart(
        data=time_entries,
        category_field="task_name",
        value_field="duration_seconds",
        secondary_category_field="category",
        title="Task Comparison",
        subtitle="Time spent by task and category",
        chart_type="bar",
        sort_by="value",
        sort_ascending=False,
        show_average=True
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "productivity_comparison.png")
    chart.save(output_path)
    
    print(f"Productivity comparison chart saved to: {output_path}")
    
    return chart


def demo_task_completion(time_entries, output_dir):
    """Demonstrate task completion chart."""
    print("Generating task completion chart...")
    
    chart = TaskCompletionChart(
        data=time_entries,
        task_field="task_name",
        completion_field="completed",
        time_field="start_time",
        title="Task Completion Rate",
        subtitle="Completion rate over time",
        show_trend=True,
        trend_window=7
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "task_completion.png")
    chart.save(output_path)
    
    print(f"Task completion chart saved to: {output_path}")
    
    return chart


def demo_task_distribution(time_entries, output_dir):
    """Demonstrate task distribution chart."""
    print("Generating task distribution chart...")
    
    chart = TaskDistributionChart(
        data=time_entries,
        task_field="task_name",
        value_field="duration_seconds",
        category_field="category",
        title="Time Distribution by Task",
        subtitle="Percentage of time spent on each task",
        chart_type="pie",
        sort_by="value",
        sort_ascending=False
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "task_distribution.png")
    chart.save(output_path)
    
    print(f"Task distribution chart saved to: {output_path}")
    
    return chart


def demo_task_relationship(relationships, output_dir):
    """Demonstrate task relationship chart."""
    print("Generating task relationship chart...")
    
    chart = TaskRelationshipChart(
        data=relationships,
        task_field="task",
        relation_field="related_to",
        category_field="category",
        title="Task Relationships",
        subtitle="Connections between tasks",
        layout="spring",
        show_labels=True,
        width=10,
        height=10
    )
    
    chart.render()
    output_path = os.path.join(output_dir, "task_relationship.png")
    chart.save(output_path)
    
    print(f"Task relationship chart saved to: {output_path}")
    
    return chart


def demo_dashboard(time_entries, relationships, output_dir):
    """Demonstrate dashboard."""
    print("Generating dashboard...")
    
    # Create dashboard
    dashboard = Dashboard(
        title="Tascade AI Time Tracking Dashboard",
        subtitle="Advanced visualization of time tracking data",
        layout="grid",
        theme="light",
        width=1200,
        height=800
    )
    
    # Add time series chart
    dashboard.add_time_series(
        title="Time Spent by Task",
        data=time_entries,
        time_field="start_time",
        value_field="duration_seconds",
        category_field="task_name",
        chart_type="line",
        time_grouping="daily",
        width=2,
        height=1
    )
    
    # Add productivity comparison chart
    dashboard.add_productivity_comparison(
        title="Task Comparison",
        data=time_entries,
        category_field="task_name",
        value_field="duration_seconds",
        secondary_category_field="category",
        chart_type="bar",
        width=1,
        height=1
    )
    
    # Add task distribution chart
    dashboard.add_task_distribution(
        title="Time Distribution",
        data=time_entries,
        task_field="task_name",
        value_field="duration_seconds",
        chart_type="pie",
        width=1,
        height=1
    )
    
    # Add activity heatmap
    dashboard.add_activity_heatmap(
        title="Activity Patterns",
        data=time_entries,
        time_field="start_time",
        value_field="duration_seconds",
        width=1,
        height=1
    )
    
    # Add task completion chart
    dashboard.add_task_completion(
        title="Task Completion Rate",
        data=time_entries,
        task_field="task_name",
        completion_field="completed",
        time_field="start_time",
        width=1,
        height=1
    )
    
    # Add task relationship chart
    dashboard.add_task_relationship(
        title="Task Relationships",
        data=relationships,
        task_field="task",
        relation_field="related_to",
        category_field="category",
        width=2,
        height=2
    )
    
    # Save dashboard
    output_path = os.path.join(output_dir, "dashboard.html")
    dashboard.save(output_path)
    
    print(f"Dashboard saved to: {output_path}")


def main():
    """Main function."""
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'visualization')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate sample data
    print("Generating sample data...")
    time_entries = generate_sample_time_entries(num_entries=200, num_tasks=5)
    relationships = generate_sample_task_relationships()
    
    # Save sample data
    with open(os.path.join(output_dir, "sample_time_entries.json"), "w") as f:
        json.dump(time_entries, f, indent=2)
    
    with open(os.path.join(output_dir, "sample_relationships.json"), "w") as f:
        json.dump(relationships, f, indent=2)
    
    # Demonstrate individual charts
    demo_time_series_chart(time_entries, output_dir)
    demo_gantt_chart(time_entries, output_dir)
    demo_calendar_heatmap(time_entries, output_dir)
    demo_activity_heatmap(time_entries, output_dir)
    demo_productivity_trend(time_entries, output_dir)
    demo_productivity_comparison(time_entries, output_dir)
    demo_task_completion(time_entries, output_dir)
    demo_task_distribution(time_entries, output_dir)
    demo_task_relationship(relationships, output_dir)
    
    # Demonstrate dashboard
    demo_dashboard(time_entries, relationships, output_dir)
    
    print("\nVisualization demo completed successfully!")
    print(f"All output files are in: {output_dir}")


if __name__ == "__main__":
    main()
