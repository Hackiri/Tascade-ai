"""
Task analysis visualizations for Tascade AI.

This module provides various task-focused visualizations for time tracking data,
including task completion, distribution, and relationship charts.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
import json
import logging
import os
import tempfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns
import networkx as nx
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from .core import (
    VisualizationBase, ChartType, OutputFormat, ColorPalette, 
    TimeGrouping, DataPreprocessor
)


class TaskCompletionChart(VisualizationBase):
    """Chart for visualizing task completion over time."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 task_field: str,
                 completion_field: str,
                 time_field: str,
                 category_field: Optional[str] = None,
                 show_incomplete: bool = True,
                 show_trend: bool = True,
                 trend_window: int = 7,
                 **kwargs):
        """
        Initialize the task completion chart.
        
        Args:
            data: List of data points
            task_field: Field containing task names
            completion_field: Field containing completion status
            time_field: Field containing time information
            category_field: Optional field for categorizing tasks
            show_incomplete: Whether to show incomplete tasks
            show_trend: Whether to show completion trend
            trend_window: Window size for moving average trend
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.task_field = task_field
        self.completion_field = completion_field
        self.time_field = time_field
        self.category_field = category_field
        self.show_incomplete = show_incomplete
        self.show_trend = show_trend
        self.trend_window = trend_window
        
        # Convert to DataFrame
        self.df = pd.DataFrame(self.data)
        
        # Convert time field to datetime
        self.df[self.time_field] = pd.to_datetime(self.df[self.time_field])
        
        # Extract date
        self.df['date'] = self.df[self.time_field].dt.date
        
        # Group by date
        grouped = self.df.groupby('date')
        
        # Calculate completion metrics
        self.completion_data = pd.DataFrame()
        self.completion_data['total'] = grouped[self.task_field].count()
        self.completion_data['completed'] = grouped[self.completion_field].sum()
        self.completion_data['completion_rate'] = self.completion_data['completed'] / self.completion_data['total']
        
        # Calculate trend if needed
        if self.show_trend:
            self.completion_data['trend'] = self.completion_data['completion_rate'].rolling(
                window=self.trend_window, 
                min_periods=1
            ).mean()
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the task completion chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Create a second y-axis for the number of tasks
        ax2 = self.ax.twinx()
        
        # Plot completion rate
        line1 = self.ax.plot(
            self.completion_data.index,
            self.completion_data['completion_rate'],
            marker='o',
            markersize=5,
            color='blue',
            label='Completion Rate'
        )
        
        # Plot trend if needed
        if self.show_trend:
            line2 = self.ax.plot(
                self.completion_data.index,
                self.completion_data['trend'],
                linestyle='--',
                linewidth=2,
                color='green',
                alpha=0.7,
                label=f"{self.trend_window}-day Trend"
            )
        
        # Plot number of tasks
        bar1 = ax2.bar(
            self.completion_data.index,
            self.completion_data['completed'],
            color='green',
            alpha=0.5,
            label='Completed Tasks'
        )
        
        if self.show_incomplete:
            bar2 = ax2.bar(
                self.completion_data.index,
                self.completion_data['total'] - self.completion_data['completed'],
                bottom=self.completion_data['completed'],
                color='red',
                alpha=0.5,
                label='Incomplete Tasks'
            )
        
        # Set labels
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Completion Rate')
        ax2.set_ylabel('Number of Tasks')
        
        # Format x-axis as dates
        self.ax.xaxis_date()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Set y-axis limits
        self.ax.set_ylim(0, 1.05)
        
        # Add legend
        lines = line1
        if self.show_trend:
            lines += line2
        
        bars = [bar1]
        if self.show_incomplete:
            bars.append(bar2)
        
        labels = [l.get_label() for l in lines + bars]
        self.ax.legend(lines + bars, labels, loc='upper left')
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax


class TaskDistributionChart(VisualizationBase):
    """Chart for visualizing the distribution of time across tasks."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 task_field: str,
                 value_field: str,
                 category_field: Optional[str] = None,
                 chart_type: Union[str, ChartType] = ChartType.PIE.value,
                 sort_by: str = 'value',
                 sort_ascending: bool = False,
                 show_percentages: bool = True,
                 limit: Optional[int] = 10,
                 **kwargs):
        """
        Initialize the task distribution chart.
        
        Args:
            data: List of data points
            task_field: Field containing task names
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing tasks
            chart_type: Type of chart to create
            sort_by: Field to sort by ('value' or 'task')
            sort_ascending: Whether to sort in ascending order
            show_percentages: Whether to show percentage labels
            limit: Maximum number of tasks to show
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.task_field = task_field
        self.value_field = value_field
        self.category_field = category_field
        
        if isinstance(chart_type, ChartType):
            self.chart_type = chart_type
        else:
            try:
                self.chart_type = ChartType(chart_type)
            except ValueError:
                self.logger.warning(f"Unknown chart type: {chart_type}, using PIE")
                self.chart_type = ChartType.PIE
        
        self.sort_by = sort_by
        self.sort_ascending = sort_ascending
        self.show_percentages = show_percentages
        self.limit = limit
        
        # Prepare data
        if self.category_field:
            # Group by task and category
            df = pd.DataFrame(self.data)
            grouped = df.groupby([self.task_field, self.category_field])
            
            # Aggregate
            aggregated = grouped[self.value_field].sum().reset_index()
            
            # Pivot to get categories as columns
            self.df = aggregated.pivot(
                index=self.task_field,
                columns=self.category_field,
                values=self.value_field
            ).fillna(0)
            
            # Sort if needed
            if self.sort_by == 'value':
                # Sort by total value
                self.df['total'] = self.df.sum(axis=1)
                self.df = self.df.sort_values('total', ascending=self.sort_ascending)
                self.df = self.df.drop('total', axis=1)
            else:
                # Sort by task name
                self.df = self.df.sort_index(ascending=self.sort_ascending)
        else:
            # Group by task
            df = pd.DataFrame(self.data)
            grouped = df.groupby(self.task_field)
            
            # Aggregate
            self.df = grouped[self.value_field].sum().reset_index()
            
            # Sort if needed
            if self.sort_by == 'value':
                self.df = self.df.sort_values(self.value_field, ascending=self.sort_ascending)
            else:
                self.df = self.df.sort_values(self.task_field, ascending=self.sort_ascending)
        
        # Limit number of tasks if needed
        if self.limit:
            if self.category_field:
                if self.sort_by == 'value':
                    # Keep top/bottom tasks
                    if self.sort_ascending:
                        self.df = self.df.head(self.limit)
                    else:
                        self.df = self.df.tail(self.limit)
                else:
                    # Just take first N tasks
                    self.df = self.df.head(self.limit)
                
                # Create "Other" category for remaining tasks
                if len(self.df) < len(aggregated[self.task_field].unique()):
                    # Get tasks not in the top N
                    other_tasks = set(aggregated[self.task_field].unique()) - set(self.df.index)
                    
                    # Calculate values for other tasks
                    other_values = {}
                    for category in self.df.columns:
                        other_values[category] = aggregated[
                            (aggregated[self.task_field].isin(other_tasks)) & 
                            (aggregated[self.category_field] == category)
                        ][self.value_field].sum()
                    
                    # Add "Other" row
                    self.df.loc['Other'] = pd.Series(other_values)
            else:
                if self.sort_by == 'value':
                    # Keep top/bottom tasks
                    if self.sort_ascending:
                        top_tasks = self.df.head(self.limit)
                    else:
                        top_tasks = self.df.tail(self.limit)
                else:
                    # Just take first N tasks
                    top_tasks = self.df.head(self.limit)
                
                # Create "Other" category for remaining tasks
                if len(top_tasks) < len(self.df):
                    # Get tasks not in the top N
                    other_tasks = set(self.df[self.task_field]) - set(top_tasks[self.task_field])
                    
                    # Calculate value for other tasks
                    other_value = self.df[self.df[self.task_field].isin(other_tasks)][self.value_field].sum()
                    
                    # Add "Other" row
                    other_row = pd.DataFrame({
                        self.task_field: ['Other'],
                        self.value_field: [other_value]
                    })
                    
                    # Update DataFrame
                    self.df = pd.concat([top_tasks, other_row])
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the task distribution chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Plot based on chart type
        if self.category_field:
            # Plot with categories
            if self.chart_type == ChartType.PIE:
                # For pie charts, use the sum across categories
                total_by_task = self.df.sum(axis=1)
                
                # Create pie chart
                wedges, texts, autotexts = self.ax.pie(
                    total_by_task,
                    labels=total_by_task.index,
                    autopct='%1.1f%%' if self.show_percentages else None,
                    startangle=90
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                self.ax.axis('equal')
                
                # Adjust text properties
                plt.setp(autotexts, size=self.font_size - 2, weight='bold')
                plt.setp(texts, size=self.font_size)
            elif self.chart_type == ChartType.BAR:
                self.df.plot(kind='bar', ax=self.ax, stacked=True)
                
                # Add percentage labels if needed
                if self.show_percentages:
                    total = self.df.sum().sum()
                    
                    for i, task in enumerate(self.df.index):
                        task_total = self.df.loc[task].sum()
                        percentage = task_total / total * 100
                        
                        self.ax.text(
                            i,
                            task_total,
                            f"{percentage:.1f}%",
                            ha='center',
                            va='bottom',
                            fontsize=self.font_size - 2
                        )
            elif self.chart_type == ChartType.TREEMAP:
                self.logger.warning("Treemap not implemented for task distribution with categories")
                self.df.plot(kind='bar', ax=self.ax, stacked=True)
            else:
                self.logger.warning(f"Unsupported chart type for task distribution with categories: {self.chart_type}, using BAR")
                self.df.plot(kind='bar', ax=self.ax, stacked=True)
        else:
            # Plot without categories
            if self.chart_type == ChartType.PIE:
                # Create pie chart
                wedges, texts, autotexts = self.ax.pie(
                    self.df[self.value_field],
                    labels=self.df[self.task_field],
                    autopct='%1.1f%%' if self.show_percentages else None,
                    startangle=90
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                self.ax.axis('equal')
                
                # Adjust text properties
                plt.setp(autotexts, size=self.font_size - 2, weight='bold')
                plt.setp(texts, size=self.font_size)
            elif self.chart_type == ChartType.BAR:
                bars = self.ax.bar(
                    self.df[self.task_field],
                    self.df[self.value_field]
                )
                
                # Add percentage labels if needed
                if self.show_percentages:
                    total = self.df[self.value_field].sum()
                    
                    for bar in bars:
                        height = bar.get_height()
                        percentage = height / total * 100
                        
                        self.ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            height,
                            f"{percentage:.1f}%",
                            ha='center',
                            va='bottom',
                            fontsize=self.font_size - 2
                        )
                
                # Rotate x-axis labels for better readability
                plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            elif self.chart_type == ChartType.TREEMAP:
                self.logger.warning("Treemap not implemented for task distribution without categories")
                bars = self.ax.bar(
                    self.df[self.task_field],
                    self.df[self.value_field]
                )
                
                # Rotate x-axis labels for better readability
                plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            else:
                self.logger.warning(f"Unsupported chart type for task distribution: {self.chart_type}, using BAR")
                bars = self.ax.bar(
                    self.df[self.task_field],
                    self.df[self.value_field]
                )
                
                # Rotate x-axis labels for better readability
                plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add labels
        if self.chart_type != ChartType.PIE:
            self._add_annotations(
                x_label="Task",
                y_label=self.value_field.replace('_', ' ').title()
            )
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax


class TaskRelationshipChart(VisualizationBase):
    """Chart for visualizing relationships between tasks."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 task_field: str,
                 relation_field: str,
                 value_field: Optional[str] = None,
                 category_field: Optional[str] = None,
                 layout: str = 'spring',
                 node_size_field: Optional[str] = None,
                 edge_width_field: Optional[str] = None,
                 show_labels: bool = True,
                 **kwargs):
        """
        Initialize the task relationship chart.
        
        Args:
            data: List of data points
            task_field: Field containing task names
            relation_field: Field containing related task names
            value_field: Optional field for node values
            category_field: Optional field for categorizing tasks
            layout: Network layout algorithm
            node_size_field: Optional field for node sizes
            edge_width_field: Optional field for edge widths
            show_labels: Whether to show task labels
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.task_field = task_field
        self.relation_field = relation_field
        self.value_field = value_field
        self.category_field = category_field
        self.layout = layout
        self.node_size_field = node_size_field
        self.edge_width_field = edge_width_field
        self.show_labels = show_labels
        
        # Create network graph
        self.G = nx.DiGraph()
        
        # Add nodes and edges
        for item in self.data:
            task = item.get(self.task_field)
            related_task = item.get(self.relation_field)
            
            if not task or not related_task:
                continue
            
            # Add nodes
            if task not in self.G:
                node_attrs = {'name': task}
                
                if self.value_field and self.value_field in item:
                    node_attrs['value'] = item[self.value_field]
                
                if self.category_field and self.category_field in item:
                    node_attrs['category'] = item[self.category_field]
                
                if self.node_size_field and self.node_size_field in item:
                    node_attrs['size'] = item[self.node_size_field]
                
                self.G.add_node(task, **node_attrs)
            
            if related_task not in self.G:
                self.G.add_node(related_task, name=related_task)
            
            # Add edge
            edge_attrs = {}
            
            if self.edge_width_field and self.edge_width_field in item:
                edge_attrs['width'] = item[self.edge_width_field]
            
            self.G.add_edge(task, related_task, **edge_attrs)
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the task relationship chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Clear axes
        self.ax.clear()
        
        # Calculate layout
        if self.layout == 'spring':
            pos = nx.spring_layout(self.G)
        elif self.layout == 'circular':
            pos = nx.circular_layout(self.G)
        elif self.layout == 'shell':
            pos = nx.shell_layout(self.G)
        elif self.layout == 'spectral':
            pos = nx.spectral_layout(self.G)
        else:
            self.logger.warning(f"Unknown layout: {self.layout}, using spring")
            pos = nx.spring_layout(self.G)
        
        # Get node sizes
        if self.node_size_field:
            node_sizes = [
                self.G.nodes[node].get('size', 300) for node in self.G.nodes
            ]
        else:
            node_sizes = 300
        
        # Get node colors
        if self.category_field:
            # Get unique categories
            categories = set()
            for node in self.G.nodes:
                category = self.G.nodes[node].get('category')
                if category:
                    categories.add(category)
            
            # Create color map
            cmap = plt.cm.get_cmap('tab10', len(categories))
            category_colors = {
                category: cmap(i) for i, category in enumerate(categories)
            }
            
            # Get node colors
            node_colors = [
                category_colors.get(
                    self.G.nodes[node].get('category'),
                    (0.7, 0.7, 0.7, 1.0)  # Default gray for nodes without category
                ) for node in self.G.nodes
            ]
        else:
            node_colors = 'skyblue'
        
        # Get edge widths
        if self.edge_width_field:
            edge_widths = [
                self.G.edges[edge].get('width', 1.0) for edge in self.G.edges
            ]
        else:
            edge_widths = 1.0
        
        # Draw network
        nx.draw_networkx_nodes(
            self.G,
            pos,
            ax=self.ax,
            node_size=node_sizes,
            node_color=node_colors,
            alpha=0.8
        )
        
        nx.draw_networkx_edges(
            self.G,
            pos,
            ax=self.ax,
            width=edge_widths,
            alpha=0.6,
            arrows=True,
            arrowsize=10,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )
        
        if self.show_labels:
            nx.draw_networkx_labels(
                self.G,
                pos,
                ax=self.ax,
                font_size=self.font_size - 2,
                font_family=self.font_family
            )
        
        # Add legend if needed
        if self.category_field:
            legend_elements = [
                Patch(facecolor=category_colors[category], label=category)
                for category in categories
            ]
            
            self.ax.legend(
                handles=legend_elements,
                loc=self.legend_position
            )
        
        # Remove axis
        self.ax.set_axis_off()
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax
