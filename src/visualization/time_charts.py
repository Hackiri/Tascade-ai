"""
Time-based visualizations for Tascade AI.

This module provides various time-based visualizations for time tracking data,
including time series charts, Gantt charts, and calendar heatmaps.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
import json
import logging
import os
import tempfile
import calendar
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

from .core import (
    VisualizationBase, ChartType, OutputFormat, ColorPalette, 
    TimeGrouping, DataPreprocessor
)


class TimeSeriesChart(VisualizationBase):
    """Time series chart for visualizing time tracking data over time."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 time_field: str,
                 value_field: str,
                 category_field: Optional[str] = None,
                 chart_type: Union[str, ChartType] = ChartType.LINE.value,
                 time_grouping: Union[str, TimeGrouping] = TimeGrouping.DAILY.value,
                 aggregation: str = 'sum',
                 stacked: bool = False,
                 cumulative: bool = False,
                 show_markers: bool = False,
                 marker_style: str = 'o',
                 line_style: str = '-',
                 line_width: float = 2.0,
                 fill_alpha: float = 0.2,
                 **kwargs):
        """
        Initialize the time series chart.
        
        Args:
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing data
            chart_type: Type of chart to create
            time_grouping: Time grouping to use
            aggregation: Aggregation function to use
            stacked: Whether to stack multiple series
            cumulative: Whether to show cumulative values
            show_markers: Whether to show markers on lines
            marker_style: Style of markers
            line_style: Style of lines
            line_width: Width of lines
            fill_alpha: Alpha value for area fills
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.time_field = time_field
        self.value_field = value_field
        self.category_field = category_field
        
        if isinstance(chart_type, ChartType):
            self.chart_type = chart_type
        else:
            try:
                self.chart_type = ChartType(chart_type)
            except ValueError:
                self.logger.warning(f"Unknown chart type: {chart_type}, using LINE")
                self.chart_type = ChartType.LINE
        
        if isinstance(time_grouping, TimeGrouping):
            self.time_grouping = time_grouping
        else:
            try:
                self.time_grouping = TimeGrouping(time_grouping)
            except ValueError:
                self.logger.warning(f"Unknown time grouping: {time_grouping}, using DAILY")
                self.time_grouping = TimeGrouping.DAILY
        
        self.aggregation = aggregation
        self.stacked = stacked
        self.cumulative = cumulative
        self.show_markers = show_markers
        self.marker_style = marker_style
        self.line_style = line_style
        self.line_width = line_width
        self.fill_alpha = fill_alpha
        
        # Prepare data
        self.df = DataPreprocessor.prepare_time_series_data(
            data=self.data,
            time_field=self.time_field,
            value_field=self.value_field,
            category_field=self.category_field,
            time_grouping=self.time_grouping,
            aggregation=self.aggregation
        )
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the time series chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Apply cumulative transformation if needed
        if self.cumulative and self.category_field:
            self.df = self.df.cumsum()
        elif self.cumulative:
            self.df[self.value_field] = self.df[self.value_field].cumsum()
        
        # Plot based on chart type
        if self.chart_type == ChartType.LINE:
            if self.category_field:
                for column in self.df.columns:
                    self.ax.plot(
                        self.df.index, 
                        self.df[column], 
                        label=column,
                        marker=self.marker_style if self.show_markers else None,
                        linestyle=self.line_style,
                        linewidth=self.line_width
                    )
            else:
                self.ax.plot(
                    self.df.index, 
                    self.df[self.value_field], 
                    marker=self.marker_style if self.show_markers else None,
                    linestyle=self.line_style,
                    linewidth=self.line_width
                )
        
        elif self.chart_type == ChartType.BAR:
            if self.category_field:
                if self.stacked:
                    self.df.plot(kind='bar', stacked=True, ax=self.ax)
                else:
                    self.df.plot(kind='bar', ax=self.ax)
            else:
                self.ax.bar(self.df.index, self.df[self.value_field])
        
        elif self.chart_type == ChartType.AREA:
            if self.category_field:
                if self.stacked:
                    self.df.plot(kind='area', stacked=True, alpha=self.fill_alpha, ax=self.ax)
                else:
                    for column in self.df.columns:
                        self.ax.fill_between(
                            self.df.index, 
                            self.df[column], 
                            alpha=self.fill_alpha,
                            label=column
                        )
            else:
                self.ax.fill_between(
                    self.df.index, 
                    self.df[self.value_field], 
                    alpha=self.fill_alpha
                )
        
        # Format time axis
        self._format_time_axis(axis='x', time_grouping=self.time_grouping)
        
        # Add legend if needed
        if self.category_field:
            self._add_legend()
        
        # Add labels
        self._add_annotations(
            x_label="Time",
            y_label=self.value_field.replace('_', ' ').title()
        )
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax


class GanttChart(VisualizationBase):
    """Gantt chart for visualizing time tracking sessions."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 task_field: str,
                 start_field: str,
                 end_field: str,
                 category_field: Optional[str] = None,
                 sort_by: str = 'start',
                 show_duration: bool = True,
                 show_now_line: bool = True,
                 bar_height: float = 0.8,
                 bar_alpha: float = 0.8,
                 **kwargs):
        """
        Initialize the Gantt chart.
        
        Args:
            data: List of data points
            task_field: Field containing task names
            start_field: Field containing start times
            end_field: Field containing end times
            category_field: Optional field for categorizing tasks
            sort_by: Field to sort tasks by ('start', 'end', 'duration', or task_field)
            show_duration: Whether to show duration labels
            show_now_line: Whether to show a line for the current time
            bar_height: Height of task bars
            bar_alpha: Alpha value for task bars
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.task_field = task_field
        self.start_field = start_field
        self.end_field = end_field
        self.category_field = category_field
        self.sort_by = sort_by
        self.show_duration = show_duration
        self.show_now_line = show_now_line
        self.bar_height = bar_height
        self.bar_alpha = bar_alpha
        
        # Prepare data
        self.df = DataPreprocessor.prepare_gantt_data(
            data=self.data,
            task_field=self.task_field,
            start_field=self.start_field,
            end_field=self.end_field,
            category_field=self.category_field
        )
        
        # Sort data
        if self.sort_by == 'start':
            self.df = self.df.sort_values(self.start_field)
        elif self.sort_by == 'end':
            self.df = self.df.sort_values(self.end_field)
        elif self.sort_by == 'duration':
            self.df = self.df.sort_values('duration')
        elif self.sort_by == self.task_field:
            self.df = self.df.sort_values(self.task_field)
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a human-readable string."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the Gantt chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Create a mapping of tasks to y-positions
        tasks = self.df[self.task_field].unique()
        task_positions = {task: i for i, task in enumerate(tasks)}
        
        # Create a mapping of categories to colors if needed
        if self.category_field:
            categories = self.df[self.category_field].unique()
            color_map = {category: color for category, color in zip(
                categories, 
                plt.cm.get_cmap('tab10')(np.linspace(0, 1, len(categories)))
            )}
        
        # Plot task bars
        for _, row in self.df.iterrows():
            start = row[self.start_field]
            end = row[self.end_field]
            task = row[self.task_field]
            duration = row['duration']
            
            # Get color based on category if available
            if self.category_field:
                category = row[self.category_field]
                color = color_map[category]
            else:
                color = plt.cm.tab10(0)
            
            # Plot bar
            self.ax.barh(
                task_positions[task],
                duration / 3600,  # Convert to hours for better visualization
                left=mdates.date2num(start),
                height=self.bar_height,
                color=color,
                alpha=self.bar_alpha,
                edgecolor='black',
                linewidth=1
            )
            
            # Add duration label if needed
            if self.show_duration:
                duration_str = self._format_duration(duration)
                self.ax.text(
                    mdates.date2num(start) + (mdates.date2num(end) - mdates.date2num(start)) / 2,
                    task_positions[task],
                    duration_str,
                    ha='center',
                    va='center',
                    fontsize=self.font_size - 2,
                    fontweight='bold',
                    color='black'
                )
        
        # Add a line for the current time if needed
        if self.show_now_line:
            now = datetime.now()
            self.ax.axvline(
                x=mdates.date2num(now),
                color='red',
                linestyle='--',
                linewidth=2,
                alpha=0.7
            )
            self.ax.text(
                mdates.date2num(now),
                len(tasks),
                "Now",
                ha='center',
                va='bottom',
                fontsize=self.font_size,
                fontweight='bold',
                color='red'
            )
        
        # Set y-axis ticks and labels
        self.ax.set_yticks(list(task_positions.values()))
        self.ax.set_yticklabels(list(task_positions.keys()))
        
        # Format x-axis as time
        self.ax.xaxis_date()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add legend if needed
        if self.category_field:
            legend_elements = [
                plt.Rectangle((0, 0), 1, 1, color=color_map[category], alpha=self.bar_alpha)
                for category in categories
            ]
            self.ax.legend(legend_elements, categories, loc=self.legend_position)
        
        # Add labels
        self._add_annotations(
            x_label="Time",
            y_label="Task"
        )
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax


class CalendarHeatmap(VisualizationBase):
    """Calendar heatmap for visualizing time tracking data by day."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 date_field: str,
                 value_field: str,
                 start_date: Optional[Union[str, datetime, date]] = None,
                 end_date: Optional[Union[str, datetime, date]] = None,
                 aggregation: str = 'sum',
                 cmap: str = 'YlGnBu',
                 show_values: bool = True,
                 show_month_labels: bool = True,
                 show_day_labels: bool = True,
                 value_format: str = '{:.1f}',
                 **kwargs):
        """
        Initialize the calendar heatmap.
        
        Args:
            data: List of data points
            date_field: Field containing date information
            value_field: Field containing the value to plot
            start_date: Optional start date for the calendar
            end_date: Optional end date for the calendar
            aggregation: Aggregation function to use
            cmap: Colormap to use
            show_values: Whether to show values in cells
            show_month_labels: Whether to show month labels
            show_day_labels: Whether to show day labels
            value_format: Format string for values
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.date_field = date_field
        self.value_field = value_field
        self.aggregation = aggregation
        self.cmap = cmap
        self.show_values = show_values
        self.show_month_labels = show_month_labels
        self.show_day_labels = show_day_labels
        self.value_format = value_format
        
        # Convert to DataFrame
        self.df = pd.DataFrame(data)
        
        # Convert date field to datetime
        self.df[date_field] = pd.to_datetime(self.df[date_field])
        
        # Set start and end dates
        if start_date is None:
            self.start_date = self.df[date_field].min().date()
        elif isinstance(start_date, str):
            self.start_date = pd.to_datetime(start_date).date()
        elif isinstance(start_date, datetime):
            self.start_date = start_date.date()
        else:
            self.start_date = start_date
        
        if end_date is None:
            self.end_date = self.df[date_field].max().date()
        elif isinstance(end_date, str):
            self.end_date = pd.to_datetime(end_date).date()
        elif isinstance(end_date, datetime):
            self.end_date = end_date.date()
        else:
            self.end_date = end_date
        
        # Group by date and aggregate
        self.df['date'] = self.df[date_field].dt.date
        grouped = self.df.groupby('date')
        
        if self.aggregation == 'sum':
            self.daily_values = grouped[value_field].sum()
        elif self.aggregation == 'mean':
            self.daily_values = grouped[value_field].mean()
        elif self.aggregation == 'min':
            self.daily_values = grouped[value_field].min()
        elif self.aggregation == 'max':
            self.daily_values = grouped[value_field].max()
        elif self.aggregation == 'count':
            self.daily_values = grouped[value_field].count()
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the calendar heatmap.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height), dpi=self.dpi)
        self.fig.patch.set_facecolor(self.background_color)
        
        # Calculate the number of calendar rows needed
        start_year = self.start_date.year
        start_month = self.start_date.month
        end_year = self.end_date.year
        end_month = self.end_date.month
        
        num_months = (end_year - start_year) * 12 + (end_month - start_month) + 1
        calendar_rows = (num_months + 3) // 4  # 4 months per row, rounded up
        
        # Create a grid of subplots for each month
        fig, axes = plt.subplots(
            calendar_rows, 
            4, 
            figsize=(self.width, self.height * calendar_rows / 2),
            dpi=self.dpi
        )
        fig.patch.set_facecolor(self.background_color)
        
        # Flatten axes array for easier indexing
        if calendar_rows > 1:
            axes = axes.flatten()
        
        # Set title
        if self.title:
            fig.suptitle(
                self.title, 
                fontsize=self.font_size + 4, 
                fontweight='bold',
                y=0.98
            )
        
        # Set subtitle
        if self.subtitle:
            fig.text(
                0.5, 0.96, 
                self.subtitle,
                horizontalalignment='center',
                fontsize=self.font_size + 2,
                fontstyle='italic'
            )
        
        # Get colormap
        cmap = plt.cm.get_cmap(self.cmap)
        
        # Get min and max values for color scaling
        vmin = self.daily_values.min()
        vmax = self.daily_values.max()
        
        # Plot each month
        month_idx = 0
        current_date = date(self.start_date.year, self.start_date.month, 1)
        end_month_date = date(self.end_date.year, self.end_date.month, 1)
        
        while current_date <= end_month_date:
            # Get the axis for this month
            if calendar_rows > 1:
                ax = axes[month_idx]
            else:
                ax = axes[month_idx]
            
            # Get the calendar for this month
            cal = calendar.monthcalendar(current_date.year, current_date.month)
            
            # Set month title
            ax.set_title(
                current_date.strftime('%B %Y'),
                fontsize=self.font_size,
                fontweight='bold'
            )
            
            # Remove axis ticks and spines
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Add day labels if needed
            if self.show_day_labels:
                for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
                    ax.text(
                        i / 7 + 1/14, 
                        -0.05, 
                        day,
                        ha='center',
                        va='center',
                        fontsize=self.font_size - 2
                    )
            
            # Plot each day
            for week_idx, week in enumerate(cal):
                for day_idx, day in enumerate(week):
                    if day == 0:
                        continue
                    
                    day_date = date(current_date.year, current_date.month, day)
                    
                    # Skip days outside the date range
                    if day_date < self.start_date or day_date > self.end_date:
                        continue
                    
                    # Get the value for this day
                    if day_date in self.daily_values.index:
                        value = self.daily_values.loc[day_date]
                    else:
                        value = 0
                    
                    # Calculate color based on value
                    if vmax > vmin:
                        color_val = (value - vmin) / (vmax - vmin)
                    else:
                        color_val = 0.5
                    
                    # Plot the day cell
                    rect = plt.Rectangle(
                        (day_idx / 7, 1 - (week_idx + 1) / len(cal)),
                        1/7,
                        1/len(cal),
                        color=cmap(color_val),
                        edgecolor='gray',
                        linewidth=0.5
                    )
                    ax.add_patch(rect)
                    
                    # Add value text if needed
                    if self.show_values:
                        ax.text(
                            day_idx / 7 + 1/14,
                            1 - (week_idx + 1) / len(cal) + 1/(2*len(cal)),
                            self.value_format.format(value),
                            ha='center',
                            va='center',
                            fontsize=self.font_size - 4,
                            color='black' if color_val < 0.7 else 'white'
                        )
            
            # Move to next month
            month_idx += 1
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        
        # Hide unused subplots
        for i in range(month_idx, len(axes)):
            if calendar_rows > 1:
                axes[i].axis('off')
            else:
                axes[i].axis('off')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = fig.colorbar(
            sm, 
            ax=axes, 
            orientation='horizontal',
            pad=0.05,
            aspect=40
        )
        cbar.set_label(self.value_field.replace('_', ' ').title())
        
        # Adjust layout
        fig.tight_layout()
        if self.title or self.subtitle:
            fig.subplots_adjust(top=0.9)
        
        # Store figure and return
        self.fig = fig
        self.ax = axes[0]  # Just store the first axis for consistency
        
        return self.fig, self.ax


class ActivityHeatmap(VisualizationBase):
    """Heatmap for visualizing activity patterns by hour and day."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 time_field: str,
                 value_field: str,
                 start_date: Optional[Union[str, datetime, date]] = None,
                 end_date: Optional[Union[str, datetime, date]] = None,
                 aggregation: str = 'sum',
                 cmap: str = 'YlGnBu',
                 show_values: bool = True,
                 value_format: str = '{:.1f}',
                 **kwargs):
        """
        Initialize the activity heatmap.
        
        Args:
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            start_date: Optional start date
            end_date: Optional end date
            aggregation: Aggregation function to use
            cmap: Colormap to use
            show_values: Whether to show values in cells
            value_format: Format string for values
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.time_field = time_field
        self.value_field = value_field
        self.aggregation = aggregation
        self.cmap = cmap
        self.show_values = show_values
        self.value_format = value_format
        
        # Convert to DataFrame
        self.df = pd.DataFrame(data)
        
        # Convert time field to datetime
        self.df[time_field] = pd.to_datetime(self.df[time_field])
        
        # Set start and end dates
        if start_date is None:
            self.start_date = self.df[time_field].min().date()
        elif isinstance(start_date, str):
            self.start_date = pd.to_datetime(start_date).date()
        elif isinstance(start_date, datetime):
            self.start_date = start_date.date()
        else:
            self.start_date = start_date
        
        if end_date is None:
            self.end_date = self.df[time_field].max().date()
        elif isinstance(end_date, str):
            self.end_date = pd.to_datetime(end_date).date()
        elif isinstance(end_date, datetime):
            self.end_date = end_date.date()
        else:
            self.end_date = end_date
        
        # Extract hour and day of week
        self.df['hour'] = self.df[time_field].dt.hour
        self.df['day_of_week'] = self.df[time_field].dt.dayofweek
        
        # Filter by date range
        mask = (
            (self.df[time_field].dt.date >= self.start_date) & 
            (self.df[time_field].dt.date <= self.end_date)
        )
        self.df = self.df[mask]
        
        # Group by hour and day of week
        grouped = self.df.groupby(['day_of_week', 'hour'])
        
        if self.aggregation == 'sum':
            self.activity_values = grouped[value_field].sum().unstack()
        elif self.aggregation == 'mean':
            self.activity_values = grouped[value_field].mean().unstack()
        elif self.aggregation == 'min':
            self.activity_values = grouped[value_field].min().unstack()
        elif self.aggregation == 'max':
            self.activity_values = grouped[value_field].max().unstack()
        elif self.aggregation == 'count':
            self.activity_values = grouped[value_field].count().unstack()
        
        # Fill missing values
        self.activity_values = self.activity_values.fillna(0)
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the activity heatmap.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Create heatmap
        sns.heatmap(
            self.activity_values,
            cmap=self.cmap,
            ax=self.ax,
            annot=self.show_values,
            fmt='.1f',  # Fixed format string
            linewidths=0.5,
            cbar_kws={'label': self.value_field.replace('_', ' ').title()}
        )
        
        # Set labels
        self.ax.set_xlabel('Hour of Day')
        self.ax.set_ylabel('Day of Week')
        
        # Set y-tick labels
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.ax.set_yticklabels(day_names, rotation=0)
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax
