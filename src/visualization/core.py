"""
Core visualization module for Tascade AI.

This module provides the foundation for all visualization types,
including data preparation, rendering, and export capabilities.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, date
import json
import logging
import os
import tempfile
from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns

# Set Seaborn style for better aesthetics
sns.set_style("whitegrid")
sns.set_context("talk")


class ChartType(Enum):
    """Chart types supported by the visualization module."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GANTT = "gantt"
    CALENDAR = "calendar"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    SUNBURST = "sunburst"
    TREEMAP = "treemap"
    RADAR = "radar"
    BUBBLE = "bubble"


class OutputFormat(Enum):
    """Output formats supported by the visualization module."""
    PNG = "png"
    JPG = "jpg"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"


class ColorPalette(Enum):
    """Color palettes supported by the visualization module."""
    DEFAULT = "default"
    PASTEL = "pastel"
    DARK = "dark"
    COLORBLIND = "colorblind"
    DEEP = "deep"
    MUTED = "muted"
    BRIGHT = "bright"
    CUSTOM = "custom"


class TimeGrouping(Enum):
    """Time grouping options for time-based visualizations."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class VisualizationBase:
    """Base class for all visualizations."""
    
    def __init__(self, 
                 title: str = "",
                 subtitle: Optional[str] = None,
                 width: int = 10,
                 height: int = 6,
                 dpi: int = 100,
                 color_palette: Union[str, List[str]] = ColorPalette.DEFAULT.value,
                 theme: str = "whitegrid",
                 font_family: str = "sans-serif",
                 font_size: int = 12,
                 background_color: str = "white",
                 show_legend: bool = True,
                 legend_position: str = "best",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the visualization.
        
        Args:
            title: Chart title
            subtitle: Chart subtitle
            width: Chart width in inches
            height: Chart height in inches
            dpi: Chart resolution in dots per inch
            color_palette: Color palette to use
            theme: Chart theme
            font_family: Font family to use
            font_size: Base font size
            background_color: Background color
            show_legend: Whether to show the legend
            legend_position: Position of the legend
            logger: Optional logger
        """
        self.title = title
        self.subtitle = subtitle
        self.width = width
        self.height = height
        self.dpi = dpi
        self.color_palette = color_palette
        self.theme = theme
        self.font_family = font_family
        self.font_size = font_size
        self.background_color = background_color
        self.show_legend = show_legend
        self.legend_position = legend_position
        self.logger = logger or logging.getLogger("tascade.visualization")
        
        # Set up figure and axes
        self.fig: Optional[Figure] = None
        self.ax: Optional[Axes] = None
        
        # Set up style
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Set up the visualization style."""
        # Set Seaborn style
        sns.set_style(self.theme)
        
        # Set font properties
        plt.rcParams['font.family'] = self.font_family
        plt.rcParams['font.size'] = self.font_size
        
        # Set color palette
        if isinstance(self.color_palette, str):
            if self.color_palette in [p.value for p in ColorPalette]:
                if self.color_palette == ColorPalette.DEFAULT.value:
                    sns.set_palette("tab10")
                else:
                    sns.set_palette(self.color_palette)
            else:
                self.logger.warning(f"Unknown color palette: {self.color_palette}, using default")
                sns.set_palette("tab10")
        else:
            # Custom color list
            sns.set_palette(self.color_palette)
    
    def _create_figure(self) -> Tuple[Figure, Axes]:
        """Create a figure and axes."""
        fig, ax = plt.subplots(figsize=(self.width, self.height), dpi=self.dpi)
        fig.patch.set_facecolor(self.background_color)
        
        # Set title and subtitle
        if self.title:
            ax.set_title(self.title, fontsize=self.font_size + 4, fontweight='bold')
        
        if self.subtitle:
            ax.text(0.5, 0.98, self.subtitle, 
                    horizontalalignment='center',
                    verticalalignment='top',
                    transform=ax.transAxes,
                    fontsize=self.font_size + 2,
                    fontstyle='italic')
        
        return fig, ax
    
    def _add_legend(self) -> None:
        """Add a legend to the chart."""
        if self.show_legend and self.ax is not None:
            self.ax.legend(loc=self.legend_position)
    
    def _add_annotations(self, 
                         annotations: Optional[Dict[str, str]] = None,
                         x_label: Optional[str] = None,
                         y_label: Optional[str] = None) -> None:
        """
        Add annotations to the chart.
        
        Args:
            annotations: Dictionary of annotations to add
            x_label: Label for the x-axis
            y_label: Label for the y-axis
        """
        if self.ax is None:
            return
        
        # Add axis labels
        if x_label:
            self.ax.set_xlabel(x_label, fontsize=self.font_size + 2)
        
        if y_label:
            self.ax.set_ylabel(y_label, fontsize=self.font_size + 2)
        
        # Add annotations
        if annotations:
            for pos, text in annotations.items():
                try:
                    x, y = pos.split(',')
                    self.ax.annotate(text, (float(x), float(y)))
                except Exception as e:
                    self.logger.warning(f"Failed to add annotation: {e}")
    
    def _format_time_axis(self, axis: str = 'x', time_grouping: TimeGrouping = TimeGrouping.DAILY) -> None:
        """
        Format a time-based axis.
        
        Args:
            axis: Which axis to format ('x' or 'y')
            time_grouping: Time grouping to use
        """
        if self.ax is None:
            return
        
        target_axis = self.ax.xaxis if axis == 'x' else self.ax.yaxis
        
        # Set formatter based on time grouping
        if time_grouping == TimeGrouping.HOURLY:
            target_axis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            target_axis.set_major_locator(mdates.HourLocator())
        elif time_grouping == TimeGrouping.DAILY:
            target_axis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            target_axis.set_major_locator(mdates.DayLocator())
        elif time_grouping == TimeGrouping.WEEKLY:
            target_axis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            target_axis.set_major_locator(mdates.WeekdayLocator())
        elif time_grouping == TimeGrouping.MONTHLY:
            target_axis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            target_axis.set_major_locator(mdates.MonthLocator())
        elif time_grouping == TimeGrouping.QUARTERLY:
            target_axis.set_major_formatter(mdates.DateFormatter('%Y-Q%q'))
            target_axis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
        elif time_grouping == TimeGrouping.YEARLY:
            target_axis.set_major_formatter(mdates.DateFormatter('%Y'))
            target_axis.set_major_locator(mdates.YearLocator())
        
        # Rotate labels if x-axis
        if axis == 'x':
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the visualization.
        
        Returns:
            Figure and axes objects
        """
        raise NotImplementedError("Subclasses must implement render()")
    
    def save(self, 
             output_path: str,
             output_format: Union[str, OutputFormat] = OutputFormat.PNG.value,
             **kwargs) -> str:
        """
        Save the visualization to a file.
        
        Args:
            output_path: Path to save the file to
            output_format: Output format
            **kwargs: Additional arguments for the save function
        
        Returns:
            Path to the saved file
        """
        if self.fig is None:
            self.render()
        
        if isinstance(output_format, OutputFormat):
            output_format = output_format.value
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Add extension if not present
        if not output_path.lower().endswith(f".{output_format}"):
            output_path = f"{output_path}.{output_format}"
        
        # Save the figure
        self.fig.savefig(output_path, format=output_format, bbox_inches='tight', **kwargs)
        
        return output_path
    
    def to_base64(self, output_format: Union[str, OutputFormat] = OutputFormat.PNG.value) -> str:
        """
        Convert the visualization to a base64-encoded string.
        
        Args:
            output_format: Output format
        
        Returns:
            Base64-encoded string
        """
        if self.fig is None:
            self.render()
        
        if isinstance(output_format, OutputFormat):
            output_format = output_format.value
        
        import io
        import base64
        
        buf = io.BytesIO()
        self.fig.savefig(buf, format=output_format, bbox_inches='tight')
        buf.seek(0)
        
        return base64.b64encode(buf.read()).decode('utf-8')
    
    def show(self) -> None:
        """Show the visualization."""
        if self.fig is None:
            self.render()
        
        plt.show()
    
    def close(self) -> None:
        """Close the figure."""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None


class DataPreprocessor:
    """Data preprocessor for visualizations."""
    
    @staticmethod
    def prepare_time_series_data(data: List[Dict[str, Any]],
                                time_field: str,
                                value_field: str,
                                category_field: Optional[str] = None,
                                time_grouping: TimeGrouping = TimeGrouping.DAILY,
                                aggregation: str = 'sum') -> pd.DataFrame:
        """
        Prepare time series data for visualization.
        
        Args:
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing data
            time_grouping: Time grouping to use
            aggregation: Aggregation function to use
        
        Returns:
            Prepared DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert time field to datetime
        df[time_field] = pd.to_datetime(df[time_field])
        
        # Set time field as index
        df = df.set_index(time_field)
        
        # Group by time
        if time_grouping == TimeGrouping.HOURLY:
            df = df.groupby([pd.Grouper(freq='H'), category_field] if category_field else pd.Grouper(freq='H'))
        elif time_grouping == TimeGrouping.DAILY:
            df = df.groupby([pd.Grouper(freq='D'), category_field] if category_field else pd.Grouper(freq='D'))
        elif time_grouping == TimeGrouping.WEEKLY:
            df = df.groupby([pd.Grouper(freq='W'), category_field] if category_field else pd.Grouper(freq='W'))
        elif time_grouping == TimeGrouping.MONTHLY:
            df = df.groupby([pd.Grouper(freq='M'), category_field] if category_field else pd.Grouper(freq='M'))
        elif time_grouping == TimeGrouping.QUARTERLY:
            df = df.groupby([pd.Grouper(freq='Q'), category_field] if category_field else pd.Grouper(freq='Q'))
        elif time_grouping == TimeGrouping.YEARLY:
            df = df.groupby([pd.Grouper(freq='Y'), category_field] if category_field else pd.Grouper(freq='Y'))
        
        # Aggregate
        if aggregation == 'sum':
            df = df[value_field].sum().reset_index()
        elif aggregation == 'mean':
            df = df[value_field].mean().reset_index()
        elif aggregation == 'min':
            df = df[value_field].min().reset_index()
        elif aggregation == 'max':
            df = df[value_field].max().reset_index()
        elif aggregation == 'count':
            df = df[value_field].count().reset_index()
        
        # Pivot if category field is provided
        if category_field:
            df = df.pivot(index=time_field, columns=category_field, values=value_field)
            df = df.fillna(0)
        
        return df
    
    @staticmethod
    def prepare_categorical_data(data: List[Dict[str, Any]],
                                category_field: str,
                                value_field: str,
                                aggregation: str = 'sum') -> pd.DataFrame:
        """
        Prepare categorical data for visualization.
        
        Args:
            data: List of data points
            category_field: Field for categorizing data
            value_field: Field containing the value to plot
            aggregation: Aggregation function to use
        
        Returns:
            Prepared DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Group by category
        grouped = df.groupby(category_field)
        
        # Aggregate
        if aggregation == 'sum':
            result = grouped[value_field].sum()
        elif aggregation == 'mean':
            result = grouped[value_field].mean()
        elif aggregation == 'min':
            result = grouped[value_field].min()
        elif aggregation == 'max':
            result = grouped[value_field].max()
        elif aggregation == 'count':
            result = grouped[value_field].count()
        
        return result.reset_index()
    
    @staticmethod
    def prepare_distribution_data(data: List[Dict[str, Any]],
                                 value_field: str,
                                 category_field: Optional[str] = None,
                                 bins: int = 10) -> pd.DataFrame:
        """
        Prepare distribution data for visualization.
        
        Args:
            data: List of data points
            value_field: Field containing the value to plot
            category_field: Optional field for categorizing data
            bins: Number of bins for histogram
        
        Returns:
            Prepared DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if category_field:
            # Group by category
            result = {}
            
            for category, group in df.groupby(category_field):
                hist, bin_edges = np.histogram(group[value_field], bins=bins)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                
                result[category] = {
                    'bin_centers': bin_centers,
                    'counts': hist
                }
            
            return result
        else:
            # Calculate histogram
            hist, bin_edges = np.histogram(df[value_field], bins=bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            return pd.DataFrame({
                'bin_centers': bin_centers,
                'counts': hist
            })
    
    @staticmethod
    def prepare_correlation_data(data: List[Dict[str, Any]],
                                fields: List[str]) -> pd.DataFrame:
        """
        Prepare correlation data for visualization.
        
        Args:
            data: List of data points
            fields: Fields to calculate correlation for
        
        Returns:
            Correlation matrix
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Calculate correlation
        return df[fields].corr()
    
    @staticmethod
    def prepare_gantt_data(data: List[Dict[str, Any]],
                          task_field: str,
                          start_field: str,
                          end_field: str,
                          category_field: Optional[str] = None) -> pd.DataFrame:
        """
        Prepare Gantt chart data for visualization.
        
        Args:
            data: List of data points
            task_field: Field containing task names
            start_field: Field containing start times
            end_field: Field containing end times
            category_field: Optional field for categorizing tasks
        
        Returns:
            Prepared DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert time fields to datetime
        df[start_field] = pd.to_datetime(df[start_field])
        df[end_field] = pd.to_datetime(df[end_field])
        
        # Calculate duration
        df['duration'] = (df[end_field] - df[start_field]).dt.total_seconds()
        
        # Sort by start time
        df = df.sort_values(start_field)
        
        return df
