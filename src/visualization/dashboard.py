"""
Dashboard module for Tascade AI.

This module provides a dashboard interface for visualizing time tracking data,
combining multiple visualization types into a cohesive view.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
import json
import logging
import os
import tempfile
import base64
from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import seaborn as sns

from .core import (
    VisualizationBase, ChartType, OutputFormat, ColorPalette, 
    TimeGrouping, DataPreprocessor
)
from .time_charts import (
    TimeSeriesChart, GanttChart, CalendarHeatmap, ActivityHeatmap
)
from .productivity_charts import (
    ProductivityTrendChart, ProductivityComparisonChart
)
from .task_charts import (
    TaskCompletionChart, TaskDistributionChart, TaskRelationshipChart
)


class DashboardLayout(Enum):
    """Dashboard layout options."""
    GRID = "grid"
    FLOW = "flow"
    TABS = "tabs"
    CUSTOM = "custom"


class DashboardTheme(Enum):
    """Dashboard theme options."""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    CUSTOM = "custom"


class Dashboard:
    """Dashboard for visualizing time tracking data."""
    
    def __init__(self, 
                 title: str = "Tascade AI Dashboard",
                 subtitle: Optional[str] = None,
                 layout: Union[str, DashboardLayout] = DashboardLayout.GRID.value,
                 theme: Union[str, DashboardTheme] = DashboardTheme.LIGHT.value,
                 width: int = 1200,
                 height: int = 800,
                 dpi: int = 100,
                 output_format: Union[str, OutputFormat] = OutputFormat.HTML.value,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the dashboard.
        
        Args:
            title: Dashboard title
            subtitle: Dashboard subtitle
            layout: Dashboard layout
            theme: Dashboard theme
            width: Dashboard width in pixels
            height: Dashboard height in pixels
            dpi: Dashboard resolution in dots per inch
            output_format: Output format
            logger: Optional logger
        """
        self.title = title
        self.subtitle = subtitle
        
        if isinstance(layout, DashboardLayout):
            self.layout = layout
        else:
            try:
                self.layout = DashboardLayout(layout)
            except ValueError:
                if logger:
                    logger.warning(f"Unknown layout: {layout}, using GRID")
                self.layout = DashboardLayout.GRID
        
        if isinstance(theme, DashboardTheme):
            self.theme = theme
        else:
            try:
                self.theme = DashboardTheme(theme)
            except ValueError:
                if logger:
                    logger.warning(f"Unknown theme: {theme}, using LIGHT")
                self.theme = DashboardTheme.LIGHT
        
        self.width = width
        self.height = height
        self.dpi = dpi
        
        if isinstance(output_format, OutputFormat):
            self.output_format = output_format
        else:
            try:
                self.output_format = OutputFormat(output_format)
            except ValueError:
                if logger:
                    logger.warning(f"Unknown output format: {output_format}, using HTML")
                self.output_format = OutputFormat.HTML
        
        self.logger = logger or logging.getLogger("tascade.visualization.dashboard")
        
        # Initialize panels
        self.panels = []
        
        # Set theme
        self._set_theme()
    
    def _set_theme(self) -> None:
        """Set the dashboard theme."""
        if self.theme == DashboardTheme.LIGHT:
            plt.style.use('default')
            self.background_color = '#ffffff'
            self.text_color = '#333333'
            self.accent_color = '#4285f4'
            self.grid_color = '#eeeeee'
        elif self.theme == DashboardTheme.DARK:
            plt.style.use('dark_background')
            self.background_color = '#333333'
            self.text_color = '#ffffff'
            self.accent_color = '#4285f4'
            self.grid_color = '#555555'
        elif self.theme == DashboardTheme.BLUE:
            plt.style.use('default')
            self.background_color = '#f0f8ff'
            self.text_color = '#333333'
            self.accent_color = '#1e88e5'
            self.grid_color = '#e3f2fd'
        elif self.theme == DashboardTheme.GREEN:
            plt.style.use('default')
            self.background_color = '#f1f8e9'
            self.text_color = '#333333'
            self.accent_color = '#43a047'
            self.grid_color = '#e8f5e9'
    
    def add_panel(self, 
                  title: str,
                  visualization: VisualizationBase,
                  width: int = 1,
                  height: int = 1,
                  position: Optional[Tuple[int, int]] = None) -> None:
        """
        Add a panel to the dashboard.
        
        Args:
            title: Panel title
            visualization: Visualization to add
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
        """
        self.panels.append({
            'title': title,
            'visualization': visualization,
            'width': width,
            'height': height,
            'position': position
        })
    
    def add_time_series(self, 
                        title: str,
                        data: List[Dict[str, Any]],
                        time_field: str,
                        value_field: str,
                        category_field: Optional[str] = None,
                        chart_type: Union[str, ChartType] = ChartType.LINE.value,
                        time_grouping: Union[str, TimeGrouping] = TimeGrouping.DAILY.value,
                        width: int = 1,
                        height: int = 1,
                        position: Optional[Tuple[int, int]] = None,
                        **kwargs) -> None:
        """
        Add a time series chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing data
            chart_type: Type of chart to create
            time_grouping: Time grouping to use
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for TimeSeriesChart
        """
        visualization = TimeSeriesChart(
            data=data,
            time_field=time_field,
            value_field=value_field,
            category_field=category_field,
            chart_type=chart_type,
            time_grouping=time_grouping,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_gantt_chart(self, 
                        title: str,
                        data: List[Dict[str, Any]],
                        task_field: str,
                        start_field: str,
                        end_field: str,
                        category_field: Optional[str] = None,
                        width: int = 2,
                        height: int = 1,
                        position: Optional[Tuple[int, int]] = None,
                        **kwargs) -> None:
        """
        Add a Gantt chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            task_field: Field containing task names
            start_field: Field containing start times
            end_field: Field containing end times
            category_field: Optional field for categorizing tasks
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for GanttChart
        """
        visualization = GanttChart(
            data=data,
            task_field=task_field,
            start_field=start_field,
            end_field=end_field,
            category_field=category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_calendar_heatmap(self, 
                            title: str,
                            data: List[Dict[str, Any]],
                            date_field: str,
                            value_field: str,
                            width: int = 2,
                            height: int = 2,
                            position: Optional[Tuple[int, int]] = None,
                            **kwargs) -> None:
        """
        Add a calendar heatmap to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            date_field: Field containing date information
            value_field: Field containing the value to plot
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for CalendarHeatmap
        """
        visualization = CalendarHeatmap(
            data=data,
            date_field=date_field,
            value_field=value_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_activity_heatmap(self, 
                            title: str,
                            data: List[Dict[str, Any]],
                            time_field: str,
                            value_field: str,
                            width: int = 1,
                            height: int = 1,
                            position: Optional[Tuple[int, int]] = None,
                            **kwargs) -> None:
        """
        Add an activity heatmap to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for ActivityHeatmap
        """
        visualization = ActivityHeatmap(
            data=data,
            time_field=time_field,
            value_field=value_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_productivity_trend(self, 
                              title: str,
                              data: List[Dict[str, Any]],
                              time_field: str,
                              value_field: str,
                              target_field: Optional[str] = None,
                              category_field: Optional[str] = None,
                              width: int = 1,
                              height: int = 1,
                              position: Optional[Tuple[int, int]] = None,
                              **kwargs) -> None:
        """
        Add a productivity trend chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            target_field: Optional field containing target values
            category_field: Optional field for categorizing data
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for ProductivityTrendChart
        """
        visualization = ProductivityTrendChart(
            data=data,
            time_field=time_field,
            value_field=value_field,
            target_field=target_field,
            category_field=category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_productivity_comparison(self, 
                                   title: str,
                                   data: List[Dict[str, Any]],
                                   category_field: str,
                                   value_field: str,
                                   secondary_category_field: Optional[str] = None,
                                   width: int = 1,
                                   height: int = 1,
                                   position: Optional[Tuple[int, int]] = None,
                                   **kwargs) -> None:
        """
        Add a productivity comparison chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            category_field: Field for categorizing data
            value_field: Field containing the value to plot
            secondary_category_field: Optional field for secondary categorization
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for ProductivityComparisonChart
        """
        visualization = ProductivityComparisonChart(
            data=data,
            category_field=category_field,
            value_field=value_field,
            secondary_category_field=secondary_category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_task_completion(self, 
                           title: str,
                           data: List[Dict[str, Any]],
                           task_field: str,
                           completion_field: str,
                           time_field: str,
                           category_field: Optional[str] = None,
                           width: int = 1,
                           height: int = 1,
                           position: Optional[Tuple[int, int]] = None,
                           **kwargs) -> None:
        """
        Add a task completion chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            task_field: Field containing task names
            completion_field: Field containing completion status
            time_field: Field containing time information
            category_field: Optional field for categorizing tasks
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for TaskCompletionChart
        """
        visualization = TaskCompletionChart(
            data=data,
            task_field=task_field,
            completion_field=completion_field,
            time_field=time_field,
            category_field=category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_task_distribution(self, 
                             title: str,
                             data: List[Dict[str, Any]],
                             task_field: str,
                             value_field: str,
                             category_field: Optional[str] = None,
                             width: int = 1,
                             height: int = 1,
                             position: Optional[Tuple[int, int]] = None,
                             **kwargs) -> None:
        """
        Add a task distribution chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            task_field: Field containing task names
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing tasks
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for TaskDistributionChart
        """
        visualization = TaskDistributionChart(
            data=data,
            task_field=task_field,
            value_field=value_field,
            category_field=category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def add_task_relationship(self, 
                             title: str,
                             data: List[Dict[str, Any]],
                             task_field: str,
                             relation_field: str,
                             value_field: Optional[str] = None,
                             category_field: Optional[str] = None,
                             width: int = 2,
                             height: int = 2,
                             position: Optional[Tuple[int, int]] = None,
                             **kwargs) -> None:
        """
        Add a task relationship chart to the dashboard.
        
        Args:
            title: Panel title
            data: List of data points
            task_field: Field containing task names
            relation_field: Field containing related task names
            value_field: Optional field for node values
            category_field: Optional field for categorizing tasks
            width: Panel width (in grid units)
            height: Panel height (in grid units)
            position: Optional position (row, column) for custom layouts
            **kwargs: Additional arguments for TaskRelationshipChart
        """
        visualization = TaskRelationshipChart(
            data=data,
            task_field=task_field,
            relation_field=relation_field,
            value_field=value_field,
            category_field=category_field,
            **kwargs
        )
        
        self.add_panel(
            title=title,
            visualization=visualization,
            width=width,
            height=height,
            position=position
        )
    
    def _render_grid_layout(self) -> str:
        """
        Render the dashboard with a grid layout.
        
        Returns:
            HTML content
        """
        # Calculate grid dimensions
        max_width = max([panel['width'] for panel in self.panels])
        max_height = max([panel['height'] for panel in self.panels])
        
        # Create grid layout
        grid_html = f"""
        <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat({max_width}, 1fr); grid-gap: 20px;">
        """
        
        # Add panels
        for i, panel in enumerate(self.panels):
            # Render visualization
            panel['visualization'].render()
            img_data = panel['visualization'].to_base64()
            
            # Create panel HTML
            panel_html = f"""
            <div class="dashboard-panel" style="grid-column: span {panel['width']}; grid-row: span {panel['height']}; background-color: {self.background_color}; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden;">
                <div class="panel-header" style="padding: 10px; background-color: {self.accent_color}; color: white;">
                    <h3 style="margin: 0;">{panel['title']}</h3>
                </div>
                <div class="panel-body" style="padding: 10px;">
                    <img src="data:image/png;base64,{img_data}" style="width: 100%; height: auto;">
                </div>
            </div>
            """
            
            grid_html += panel_html
            
            # Close visualization to free memory
            panel['visualization'].close()
        
        grid_html += "</div>"
        
        return grid_html
    
    def _render_flow_layout(self) -> str:
        """
        Render the dashboard with a flow layout.
        
        Returns:
            HTML content
        """
        flow_html = f"""
        <div class="dashboard-flow" style="display: flex; flex-wrap: wrap; gap: 20px;">
        """
        
        # Add panels
        for i, panel in enumerate(self.panels):
            # Render visualization
            panel['visualization'].render()
            img_data = panel['visualization'].to_base64()
            
            # Calculate panel width
            panel_width = f"{100 * panel['width'] / 3}%"
            
            # Create panel HTML
            panel_html = f"""
            <div class="dashboard-panel" style="flex: 0 0 {panel_width}; background-color: {self.background_color}; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden;">
                <div class="panel-header" style="padding: 10px; background-color: {self.accent_color}; color: white;">
                    <h3 style="margin: 0;">{panel['title']}</h3>
                </div>
                <div class="panel-body" style="padding: 10px;">
                    <img src="data:image/png;base64,{img_data}" style="width: 100%; height: auto;">
                </div>
            </div>
            """
            
            flow_html += panel_html
            
            # Close visualization to free memory
            panel['visualization'].close()
        
        flow_html += "</div>"
        
        return flow_html
    
    def _render_tabs_layout(self) -> str:
        """
        Render the dashboard with a tabs layout.
        
        Returns:
            HTML content
        """
        tabs_html = f"""
        <div class="dashboard-tabs">
            <div class="tabs-header" style="display: flex; border-bottom: 1px solid {self.grid_color};">
        """
        
        # Add tab headers
        for i, panel in enumerate(self.panels):
            active_class = "active" if i == 0 else ""
            tabs_html += f"""
            <div class="tab-header {active_class}" onclick="showTab({i})" style="padding: 10px 20px; cursor: pointer; background-color: {self.accent_color if i == 0 else self.background_color}; color: {self.text_color}; border-radius: 5px 5px 0 0;">{panel['title']}</div>
            """
        
        tabs_html += """
            </div>
            <div class="tabs-content">
        """
        
        # Add tab content
        for i, panel in enumerate(self.panels):
            # Render visualization
            panel['visualization'].render()
            img_data = panel['visualization'].to_base64()
            
            # Create tab content HTML
            display_style = "block" if i == 0 else "none"
            tabs_html += f"""
            <div id="tab-{i}" class="tab-content" style="display: {display_style}; padding: 20px; background-color: {self.background_color};">
                <img src="data:image/png;base64,{img_data}" style="width: 100%; height: auto;">
            </div>
            """
            
            # Close visualization to free memory
            panel['visualization'].close()
        
        tabs_html += """
            </div>
        </div>
        <script>
            function showTab(tabIndex) {
                // Hide all tabs
                var tabContents = document.getElementsByClassName('tab-content');
                for (var i = 0; i < tabContents.length; i++) {
                    tabContents[i].style.display = 'none';
                }
                
                // Show selected tab
                document.getElementById('tab-' + tabIndex).style.display = 'block';
                
                // Update tab headers
                var tabHeaders = document.getElementsByClassName('tab-header');
                for (var i = 0; i < tabHeaders.length; i++) {
                    if (i === tabIndex) {
                        tabHeaders[i].style.backgroundColor = '#4285f4';
                        tabHeaders[i].style.color = 'white';
                    } else {
                        tabHeaders[i].style.backgroundColor = '#ffffff';
                        tabHeaders[i].style.color = '#333333';
                    }
                }
            }
        </script>
        """
        
        return tabs_html
    
    def _render_custom_layout(self) -> str:
        """
        Render the dashboard with a custom layout.
        
        Returns:
            HTML content
        """
        # Calculate grid dimensions
        max_row = 0
        max_col = 0
        
        for panel in self.panels:
            if panel['position']:
                row, col = panel['position']
                max_row = max(max_row, row + panel['height'])
                max_col = max(max_col, col + panel['width'])
        
        # Create grid layout
        custom_html = f"""
        <div class="dashboard-custom" style="display: grid; grid-template-columns: repeat({max_col}, 1fr); grid-template-rows: repeat({max_row}, auto); grid-gap: 20px;">
        """
        
        # Add panels
        for i, panel in enumerate(self.panels):
            # Render visualization
            panel['visualization'].render()
            img_data = panel['visualization'].to_base64()
            
            # Get position
            if panel['position']:
                row, col = panel['position']
            else:
                # Default position
                row = i // max_col
                col = i % max_col
            
            # Create panel HTML
            panel_html = f"""
            <div class="dashboard-panel" style="grid-column: {col + 1} / span {panel['width']}; grid-row: {row + 1} / span {panel['height']}; background-color: {self.background_color}; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden;">
                <div class="panel-header" style="padding: 10px; background-color: {self.accent_color}; color: white;">
                    <h3 style="margin: 0;">{panel['title']}</h3>
                </div>
                <div class="panel-body" style="padding: 10px;">
                    <img src="data:image/png;base64,{img_data}" style="width: 100%; height: auto;">
                </div>
            </div>
            """
            
            custom_html += panel_html
            
            # Close visualization to free memory
            panel['visualization'].close()
        
        custom_html += "</div>"
        
        return custom_html
    
    def render(self) -> str:
        """
        Render the dashboard.
        
        Returns:
            HTML content
        """
        # Create HTML header
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {self.background_color};
                    color: {self.text_color};
                }}
                .dashboard-header {{
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .dashboard-header h1 {{
                    margin: 0;
                    color: {self.accent_color};
                }}
                .dashboard-header p {{
                    margin: 10px 0 0 0;
                    color: {self.text_color};
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-header">
                <h1>{self.title}</h1>
                {f'<p>{self.subtitle}</p>' if self.subtitle else ''}
            </div>
        """
        
        # Render layout
        if self.layout == DashboardLayout.GRID:
            html += self._render_grid_layout()
        elif self.layout == DashboardLayout.FLOW:
            html += self._render_flow_layout()
        elif self.layout == DashboardLayout.TABS:
            html += self._render_tabs_layout()
        elif self.layout == DashboardLayout.CUSTOM:
            html += self._render_custom_layout()
        
        # Close HTML
        html += """
        </body>
        </html>
        """
        
        return html
    
    def save(self, output_path: str) -> str:
        """
        Save the dashboard to a file.
        
        Args:
            output_path: Path to save the file to
        
        Returns:
            Path to the saved file
        """
        # Render dashboard
        html = self.render()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
