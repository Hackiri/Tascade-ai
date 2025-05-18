"""
Productivity visualizations for Tascade AI.

This module provides various productivity-focused visualizations for time tracking data,
including productivity trends, comparisons, and distribution charts.
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
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from .core import (
    VisualizationBase, ChartType, OutputFormat, ColorPalette, 
    TimeGrouping, DataPreprocessor
)


class ProductivityTrendChart(VisualizationBase):
    """Chart for visualizing productivity trends over time."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 time_field: str,
                 value_field: str,
                 target_field: Optional[str] = None,
                 category_field: Optional[str] = None,
                 time_grouping: Union[str, TimeGrouping] = TimeGrouping.DAILY.value,
                 show_target: bool = True,
                 show_trend: bool = True,
                 trend_window: int = 7,
                 show_annotations: bool = True,
                 **kwargs):
        """
        Initialize the productivity trend chart.
        
        Args:
            data: List of data points
            time_field: Field containing time information
            value_field: Field containing the value to plot
            target_field: Optional field containing target values
            category_field: Optional field for categorizing data
            time_grouping: Time grouping to use
            show_target: Whether to show target values
            show_trend: Whether to show trend line
            trend_window: Window size for moving average trend
            show_annotations: Whether to show annotations for significant changes
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.time_field = time_field
        self.value_field = value_field
        self.target_field = target_field
        self.category_field = category_field
        
        if isinstance(time_grouping, TimeGrouping):
            self.time_grouping = time_grouping
        else:
            try:
                self.time_grouping = TimeGrouping(time_grouping)
            except ValueError:
                self.logger.warning(f"Unknown time grouping: {time_grouping}, using DAILY")
                self.time_grouping = TimeGrouping.DAILY
        
        self.show_target = show_target
        self.show_trend = show_trend
        self.trend_window = trend_window
        self.show_annotations = show_annotations
        
        # Prepare data
        self.df = DataPreprocessor.prepare_time_series_data(
            data=self.data,
            time_field=self.time_field,
            value_field=self.value_field,
            category_field=self.category_field,
            time_grouping=self.time_grouping,
            aggregation='sum'
        )
    
    def _calculate_trend(self, series: pd.Series) -> pd.Series:
        """Calculate moving average trend."""
        return series.rolling(window=self.trend_window, min_periods=1).mean()
    
    def _find_significant_changes(self, series: pd.Series, threshold: float = 0.2) -> List[Tuple[int, float]]:
        """Find significant changes in the series."""
        # Calculate percentage changes
        pct_changes = series.pct_change().fillna(0)
        
        # Find significant changes
        significant_changes = []
        
        for i, change in enumerate(pct_changes):
            if abs(change) >= threshold:
                significant_changes.append((i, change))
        
        return significant_changes
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the productivity trend chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Plot data
        if self.category_field:
            # Plot each category
            for column in self.df.columns:
                self.ax.plot(
                    self.df.index, 
                    self.df[column], 
                    marker='o',
                    markersize=5,
                    label=column
                )
                
                # Add trend line if needed
                if self.show_trend:
                    trend = self._calculate_trend(self.df[column])
                    self.ax.plot(
                        self.df.index,
                        trend,
                        linestyle='--',
                        linewidth=2,
                        alpha=0.7
                    )
                
                # Add annotations if needed
                if self.show_annotations:
                    significant_changes = self._find_significant_changes(self.df[column])
                    
                    for idx, change in significant_changes:
                        if idx > 0 and idx < len(self.df.index):
                            self.ax.annotate(
                                f"{change*100:.1f}%",
                                xy=(self.df.index[idx], self.df[column].iloc[idx]),
                                xytext=(0, 10 if change > 0 else -20),
                                textcoords='offset points',
                                ha='center',
                                va='bottom' if change > 0 else 'top',
                                fontsize=self.font_size - 2,
                                arrowprops=dict(arrowstyle='->', color='black')
                            )
        else:
            # Plot single series
            self.ax.plot(
                self.df.index, 
                self.df[self.value_field], 
                marker='o',
                markersize=5
            )
            
            # Add trend line if needed
            if self.show_trend:
                trend = self._calculate_trend(self.df[self.value_field])
                self.ax.plot(
                    self.df.index,
                    trend,
                    linestyle='--',
                    linewidth=2,
                    alpha=0.7,
                    label=f"{self.trend_window}-period Moving Average"
                )
            
            # Add annotations if needed
            if self.show_annotations:
                significant_changes = self._find_significant_changes(self.df[self.value_field])
                
                for idx, change in significant_changes:
                    if idx > 0 and idx < len(self.df.index):
                        self.ax.annotate(
                            f"{change*100:.1f}%",
                            xy=(self.df.index[idx], self.df[self.value_field].iloc[idx]),
                            xytext=(0, 10 if change > 0 else -20),
                            textcoords='offset points',
                            ha='center',
                            va='bottom' if change > 0 else 'top',
                            fontsize=self.font_size - 2,
                            arrowprops=dict(arrowstyle='->', color='black')
                        )
        
        # Add target line if needed
        if self.show_target and self.target_field:
            target_df = DataPreprocessor.prepare_time_series_data(
                data=self.data,
                time_field=self.time_field,
                value_field=self.target_field,
                time_grouping=self.time_grouping,
                aggregation='mean'
            )
            
            self.ax.plot(
                target_df.index,
                target_df[self.target_field],
                linestyle='-.',
                color='red',
                linewidth=2,
                label='Target'
            )
        
        # Format time axis
        self._format_time_axis(axis='x', time_grouping=self.time_grouping)
        
        # Add legend if needed
        if self.category_field or self.show_trend or (self.show_target and self.target_field):
            self._add_legend()
        
        # Add labels
        self._add_annotations(
            x_label="Time",
            y_label=self.value_field.replace('_', ' ').title()
        )
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax


class ProductivityComparisonChart(VisualizationBase):
    """Chart for comparing productivity across different categories."""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 category_field: str,
                 value_field: str,
                 secondary_category_field: Optional[str] = None,
                 chart_type: Union[str, ChartType] = ChartType.BAR.value,
                 sort_by: str = 'value',
                 sort_ascending: bool = False,
                 show_average: bool = True,
                 show_percentages: bool = True,
                 limit: Optional[int] = None,
                 **kwargs):
        """
        Initialize the productivity comparison chart.
        
        Args:
            data: List of data points
            category_field: Field for categorizing data
            value_field: Field containing the value to plot
            secondary_category_field: Optional field for secondary categorization
            chart_type: Type of chart to create
            sort_by: Field to sort by ('value' or 'category')
            sort_ascending: Whether to sort in ascending order
            show_average: Whether to show average line
            show_percentages: Whether to show percentage labels
            limit: Maximum number of categories to show
            **kwargs: Additional arguments for VisualizationBase
        """
        super().__init__(**kwargs)
        
        self.data = data
        self.category_field = category_field
        self.value_field = value_field
        self.secondary_category_field = secondary_category_field
        
        if isinstance(chart_type, ChartType):
            self.chart_type = chart_type
        else:
            try:
                self.chart_type = ChartType(chart_type)
            except ValueError:
                self.logger.warning(f"Unknown chart type: {chart_type}, using BAR")
                self.chart_type = ChartType.BAR
        
        self.sort_by = sort_by
        self.sort_ascending = sort_ascending
        self.show_average = show_average
        self.show_percentages = show_percentages
        self.limit = limit
        
        # Prepare data
        if self.secondary_category_field:
            # Group by both category fields
            df = pd.DataFrame(self.data)
            grouped = df.groupby([self.category_field, self.secondary_category_field])
            
            # Aggregate
            aggregated = grouped[self.value_field].sum().reset_index()
            
            # Pivot to get secondary categories as columns
            self.df = aggregated.pivot(
                index=self.category_field,
                columns=self.secondary_category_field,
                values=self.value_field
            ).fillna(0)
            
            # Sort if needed
            if self.sort_by == 'value':
                # Sort by total value
                self.df['total'] = self.df.sum(axis=1)
                self.df = self.df.sort_values('total', ascending=self.sort_ascending)
                self.df = self.df.drop('total', axis=1)
            else:
                # Sort by category name
                self.df = self.df.sort_index(ascending=self.sort_ascending)
        else:
            # Group by category field
            self.df = DataPreprocessor.prepare_categorical_data(
                data=self.data,
                category_field=self.category_field,
                value_field=self.value_field,
                aggregation='sum'
            )
            
            # Sort if needed
            if self.sort_by == 'value':
                self.df = self.df.sort_values(self.value_field, ascending=self.sort_ascending)
            else:
                self.df = self.df.sort_values(self.category_field, ascending=self.sort_ascending)
        
        # Limit number of categories if needed
        if self.limit and len(self.df) > self.limit:
            if self.secondary_category_field:
                if self.sort_by == 'value':
                    # Keep top/bottom categories
                    if self.sort_ascending:
                        self.df = self.df.head(self.limit)
                    else:
                        self.df = self.df.tail(self.limit)
                else:
                    # Just take first N categories
                    self.df = self.df.head(self.limit)
            else:
                if self.sort_by == 'value':
                    # Keep top/bottom categories
                    if self.sort_ascending:
                        self.df = self.df.head(self.limit)
                    else:
                        self.df = self.df.tail(self.limit)
                else:
                    # Just take first N categories
                    self.df = self.df.head(self.limit)
    
    def render(self) -> Tuple[Figure, Axes]:
        """
        Render the productivity comparison chart.
        
        Returns:
            Figure and axes objects
        """
        # Create figure and axes
        self.fig, self.ax = self._create_figure()
        
        # Plot based on chart type
        if self.secondary_category_field:
            # Plot with secondary categories
            if self.chart_type == ChartType.BAR:
                self.df.plot(kind='bar', ax=self.ax)
            elif self.chart_type == ChartType.PIE:
                # For pie charts, use the sum across secondary categories
                self.df.sum(axis=1).plot(kind='pie', ax=self.ax, autopct='%1.1f%%')
            elif self.chart_type == ChartType.AREA:
                self.df.plot(kind='area', ax=self.ax, stacked=True, alpha=0.7)
            else:
                self.logger.warning(f"Unsupported chart type for secondary categories: {self.chart_type}, using BAR")
                self.df.plot(kind='bar', ax=self.ax)
        else:
            # Plot without secondary categories
            if self.chart_type == ChartType.BAR:
                bars = self.ax.bar(
                    self.df[self.category_field], 
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
            elif self.chart_type == ChartType.PIE:
                self.ax.pie(
                    self.df[self.value_field],
                    labels=self.df[self.category_field],
                    autopct='%1.1f%%',
                    startangle=90
                )
                self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            elif self.chart_type == ChartType.AREA:
                self.ax.fill_between(
                    range(len(self.df)),
                    self.df[self.value_field],
                    alpha=0.7
                )
                self.ax.set_xticks(range(len(self.df)))
                self.ax.set_xticklabels(self.df[self.category_field])
            else:
                self.logger.warning(f"Unsupported chart type: {self.chart_type}, using BAR")
                self.ax.bar(
                    self.df[self.category_field], 
                    self.df[self.value_field]
                )
        
        # Add average line if needed
        if self.show_average and self.chart_type != ChartType.PIE:
            if self.secondary_category_field:
                # Calculate average for each secondary category
                for column in self.df.columns:
                    avg = self.df[column].mean()
                    self.ax.axhline(
                        y=avg,
                        linestyle='--',
                        color='gray',
                        alpha=0.7
                    )
                    
                    self.ax.text(
                        len(self.df),
                        avg,
                        f"Avg {column}: {avg:.1f}",
                        ha='left',
                        va='center',
                        fontsize=self.font_size - 2
                    )
            else:
                # Calculate overall average
                avg = self.df[self.value_field].mean()
                self.ax.axhline(
                    y=avg,
                    linestyle='--',
                    color='red',
                    alpha=0.7,
                    label=f"Average: {avg:.1f}"
                )
        
        # Add legend if needed
        if self.secondary_category_field or (self.show_average and self.chart_type != ChartType.PIE):
            self._add_legend()
        
        # Add labels
        if self.chart_type != ChartType.PIE:
            self._add_annotations(
                x_label=self.category_field.replace('_', ' ').title(),
                y_label=self.value_field.replace('_', ' ').title()
            )
        
        # Adjust layout
        self.fig.tight_layout()
        
        return self.fig, self.ax
