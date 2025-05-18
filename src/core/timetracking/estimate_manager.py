"""
Time Estimate Manager for the Task Time Tracking system.

This module provides functionality for managing time estimates,
including creating, updating, and querying estimates.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import os
import json
import logging
import uuid

from .models import TimeEstimate, TimeEstimateType


class TimeEstimateManager:
    """Manager for time estimates."""
    
    def __init__(self, 
                 data_dir: str = None,
                 estimates_file: str = "time_estimates.json",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the time estimate manager.
        
        Args:
            data_dir: Directory for storing time estimate data
            estimates_file: File name for time estimates
            logger: Optional logger
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.estimates_file = os.path.join(self.data_dir, estimates_file)
        self.logger = logger or logging.getLogger("tascade.timetracking")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize estimates
        self.estimates: Dict[str, TimeEstimate] = {}
        self.task_estimates: Dict[str, str] = {}  # Maps task_id to estimate_id
        
        # Load existing estimates
        self._load_estimates()
    
    def _load_estimates(self) -> None:
        """Load time estimates from the estimates file."""
        if not os.path.exists(self.estimates_file):
            self.logger.info(f"Time estimates file not found: {self.estimates_file}")
            return
        
        try:
            with open(self.estimates_file, "r") as f:
                data = json.load(f)
            
            for item in data:
                estimate = TimeEstimate.from_dict(item)
                self.estimates[estimate.id] = estimate
                
                # Map task to estimate
                if estimate.task_id:
                    self.task_estimates[estimate.task_id] = estimate.id
        except Exception as e:
            self.logger.error(f"Error loading time estimates: {e}")
    
    def _save_estimates(self) -> None:
        """Save time estimates to the estimates file."""
        try:
            data = [estimate.to_dict() for estimate in self.estimates.values()]
            
            with open(self.estimates_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving time estimates: {e}")
    
    def create_estimate(self, 
                        task_id: str,
                        estimate_type: TimeEstimateType = TimeEstimateType.FIXED,
                        estimate_value: Union[int, float, str, Dict[str, Any]] = 0,
                        unit: str = "hours",
                        created_by: Optional[str] = None,
                        confidence: Optional[int] = None,
                        notes: str = "",
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new time estimate.
        
        Args:
            task_id: Task identifier
            estimate_type: Type of estimate
            estimate_value: Estimated value (format depends on type)
            unit: Unit of measurement (hours, days, etc.)
            created_by: User who created the estimate
            confidence: Confidence level (0-100)
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            ID of the created estimate
        """
        # Create estimate
        estimate = TimeEstimate(
            task_id=task_id,
            estimate_type=estimate_type,
            estimate_value=estimate_value,
            unit=unit,
            created_by=created_by,
            confidence=confidence,
            notes=notes,
            metadata=metadata
        )
        
        # Store estimate
        self.estimates[estimate.id] = estimate
        
        # Map task to estimate
        self.task_estimates[task_id] = estimate.id
        
        # Save changes
        self._save_estimates()
        
        return estimate.id
    
    def update_estimate(self, 
                        estimate_id: str,
                        estimate_type: Optional[TimeEstimateType] = None,
                        estimate_value: Optional[Union[int, float, str, Dict[str, Any]]] = None,
                        unit: Optional[str] = None,
                        confidence: Optional[int] = None,
                        notes: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing time estimate.
        
        Args:
            estimate_id: Estimate identifier
            estimate_type: Type of estimate
            estimate_value: Estimated value (format depends on type)
            unit: Unit of measurement (hours, days, etc.)
            confidence: Confidence level (0-100)
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            True if update succeeded, False otherwise
        """
        if estimate_id not in self.estimates:
            self.logger.error(f"Time estimate not found: {estimate_id}")
            return False
        
        estimate = self.estimates[estimate_id]
        
        # Update fields
        if estimate_type is not None:
            estimate.estimate_type = estimate_type
        
        if estimate_value is not None:
            estimate.estimate_value = estimate_value
        
        if unit is not None:
            estimate.unit = unit
        
        if confidence is not None:
            estimate.confidence = confidence
        
        if notes is not None:
            estimate.notes = notes
        
        if metadata is not None:
            estimate.metadata.update(metadata)
        
        # Update timestamp
        estimate.updated_at = datetime.now()
        
        # Save changes
        self._save_estimates()
        
        return True
    
    def get_estimate(self, estimate_id: str) -> Optional[TimeEstimate]:
        """
        Get a time estimate by ID.
        
        Args:
            estimate_id: Estimate identifier
            
        Returns:
            Time estimate or None if not found
        """
        return self.estimates.get(estimate_id)
    
    def get_estimate_for_task(self, task_id: str) -> Optional[TimeEstimate]:
        """
        Get the time estimate for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Time estimate or None if not found
        """
        estimate_id = self.task_estimates.get(task_id)
        if not estimate_id:
            return None
        
        return self.estimates.get(estimate_id)
    
    def get_estimates(self, 
                      task_ids: Optional[List[str]] = None,
                      created_by: Optional[str] = None,
                      estimate_type: Optional[TimeEstimateType] = None,
                      min_confidence: Optional[int] = None,
                      max_confidence: Optional[int] = None) -> List[TimeEstimate]:
        """
        Get time estimates, optionally filtered.
        
        Args:
            task_ids: Filter by task IDs
            created_by: Filter by creator
            estimate_type: Filter by estimate type
            min_confidence: Filter by minimum confidence
            max_confidence: Filter by maximum confidence
            
        Returns:
            List of time estimates
        """
        result = list(self.estimates.values())
        
        # Apply filters
        if task_ids:
            result = [e for e in result if e.task_id in task_ids]
        
        if created_by:
            result = [e for e in result if e.created_by == created_by]
        
        if estimate_type:
            result = [e for e in result if e.estimate_type == estimate_type]
        
        if min_confidence is not None:
            result = [e for e in result if e.confidence is not None and e.confidence >= min_confidence]
        
        if max_confidence is not None:
            result = [e for e in result if e.confidence is not None and e.confidence <= max_confidence]
        
        # Sort by created_at
        result.sort(key=lambda e: e.created_at if e.created_at else datetime.min)
        
        return result
    
    def delete_estimate(self, estimate_id: str) -> bool:
        """
        Delete a time estimate.
        
        Args:
            estimate_id: Estimate identifier
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        if estimate_id not in self.estimates:
            self.logger.error(f"Time estimate not found: {estimate_id}")
            return False
        
        estimate = self.estimates[estimate_id]
        
        # Remove task mapping
        if estimate.task_id in self.task_estimates and self.task_estimates[estimate.task_id] == estimate_id:
            del self.task_estimates[estimate.task_id]
        
        # Remove estimate
        del self.estimates[estimate_id]
        
        # Save changes
        self._save_estimates()
        
        return True
    
    def delete_estimate_for_task(self, task_id: str) -> bool:
        """
        Delete the time estimate for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        estimate_id = self.task_estimates.get(task_id)
        if not estimate_id:
            self.logger.error(f"No time estimate found for task: {task_id}")
            return False
        
        return self.delete_estimate(estimate_id)
    
    def convert_estimate(self, 
                         estimate_id: str,
                         target_type: TimeEstimateType,
                         target_unit: Optional[str] = None) -> bool:
        """
        Convert an estimate to a different type.
        
        Args:
            estimate_id: Estimate identifier
            target_type: Target estimate type
            target_unit: Optional target unit
            
        Returns:
            True if conversion succeeded, False otherwise
        """
        if estimate_id not in self.estimates:
            self.logger.error(f"Time estimate not found: {estimate_id}")
            return False
        
        estimate = self.estimates[estimate_id]
        
        # If same type, just update unit if provided
        if estimate.estimate_type == target_type:
            if target_unit:
                estimate.unit = target_unit
                estimate.updated_at = datetime.now()
                self._save_estimates()
            return True
        
        # Convert based on source and target types
        source_type = estimate.estimate_type
        source_value = estimate.estimate_value
        source_unit = estimate.unit
        
        # Default target unit if not provided
        if not target_unit:
            if target_type == TimeEstimateType.STORY_POINTS:
                target_unit = "points"
            elif target_type == TimeEstimateType.T_SHIRT:
                target_unit = "size"
            else:
                target_unit = source_unit
        
        # Perform conversion
        target_value = None
        
        if source_type == TimeEstimateType.FIXED:
            # Fixed to other types
            if target_type == TimeEstimateType.RANGE:
                # Create a range with ±20%
                value = float(source_value)
                target_value = {
                    "min": round(value * 0.8, 2),
                    "max": round(value * 1.2, 2)
                }
            elif target_type == TimeEstimateType.STORY_POINTS:
                # Convert hours to points (rough estimate)
                value = float(source_value)
                if source_unit == "hours":
                    if value <= 1:
                        target_value = 1
                    elif value <= 4:
                        target_value = 2
                    elif value <= 8:
                        target_value = 3
                    elif value <= 16:
                        target_value = 5
                    elif value <= 32:
                        target_value = 8
                    else:
                        target_value = 13
                else:
                    # Default conversion
                    target_value = round(value)
            elif target_type == TimeEstimateType.T_SHIRT:
                # Convert hours to t-shirt sizes
                value = float(source_value)
                if source_unit == "hours":
                    if value <= 2:
                        target_value = "XS"
                    elif value <= 4:
                        target_value = "S"
                    elif value <= 8:
                        target_value = "M"
                    elif value <= 16:
                        target_value = "L"
                    elif value <= 32:
                        target_value = "XL"
                    else:
                        target_value = "XXL"
                else:
                    # Default conversion
                    target_value = "M"
        
        elif source_type == TimeEstimateType.RANGE:
            # Range to other types
            if isinstance(source_value, dict):
                min_val = source_value.get("min", 0)
                max_val = source_value.get("max", 0)
                avg_val = (min_val + max_val) / 2
                
                if target_type == TimeEstimateType.FIXED:
                    target_value = avg_val
                elif target_type == TimeEstimateType.STORY_POINTS:
                    # Convert average hours to points
                    if source_unit == "hours":
                        if avg_val <= 1:
                            target_value = 1
                        elif avg_val <= 4:
                            target_value = 2
                        elif avg_val <= 8:
                            target_value = 3
                        elif avg_val <= 16:
                            target_value = 5
                        elif avg_val <= 32:
                            target_value = 8
                        else:
                            target_value = 13
                    else:
                        # Default conversion
                        target_value = round(avg_val)
                elif target_type == TimeEstimateType.T_SHIRT:
                    # Convert average hours to t-shirt sizes
                    if source_unit == "hours":
                        if avg_val <= 2:
                            target_value = "XS"
                        elif avg_val <= 4:
                            target_value = "S"
                        elif avg_val <= 8:
                            target_value = "M"
                        elif avg_val <= 16:
                            target_value = "L"
                        elif avg_val <= 32:
                            target_value = "XL"
                        else:
                            target_value = "XXL"
                    else:
                        # Default conversion
                        target_value = "M"
            else:
                # Invalid range format, use as-is
                target_value = source_value
        
        elif source_type == TimeEstimateType.STORY_POINTS:
            # Story points to other types
            points = float(source_value)
            
            if target_type == TimeEstimateType.FIXED:
                # Convert points to hours (rough estimate)
                if points == 1:
                    target_value = 1
                elif points == 2:
                    target_value = 4
                elif points == 3:
                    target_value = 8
                elif points == 5:
                    target_value = 16
                elif points == 8:
                    target_value = 32
                elif points == 13:
                    target_value = 48
                else:
                    target_value = points * 4  # Default conversion
            elif target_type == TimeEstimateType.RANGE:
                # Convert points to hour range
                if points == 1:
                    target_value = {"min": 0.5, "max": 2}
                elif points == 2:
                    target_value = {"min": 2, "max": 6}
                elif points == 3:
                    target_value = {"min": 6, "max": 10}
                elif points == 5:
                    target_value = {"min": 10, "max": 20}
                elif points == 8:
                    target_value = {"min": 20, "max": 40}
                elif points == 13:
                    target_value = {"min": 40, "max": 60}
                else:
                    # Default conversion
                    hours = points * 4
                    target_value = {"min": hours * 0.8, "max": hours * 1.2}
            elif target_type == TimeEstimateType.T_SHIRT:
                # Convert points to t-shirt sizes
                if points <= 1:
                    target_value = "XS"
                elif points <= 2:
                    target_value = "S"
                elif points <= 3:
                    target_value = "M"
                elif points <= 5:
                    target_value = "L"
                elif points <= 8:
                    target_value = "XL"
                else:
                    target_value = "XXL"
        
        elif source_type == TimeEstimateType.T_SHIRT:
            # T-shirt sizes to other types
            size = str(source_value).upper()
            
            if target_type == TimeEstimateType.FIXED:
                # Convert t-shirt sizes to hours
                if size == "XS":
                    target_value = 2
                elif size == "S":
                    target_value = 4
                elif size == "M":
                    target_value = 8
                elif size == "L":
                    target_value = 16
                elif size == "XL":
                    target_value = 32
                elif size == "XXL":
                    target_value = 48
                else:
                    target_value = 8  # Default to medium
            elif target_type == TimeEstimateType.RANGE:
                # Convert t-shirt sizes to hour range
                if size == "XS":
                    target_value = {"min": 1, "max": 3}
                elif size == "S":
                    target_value = {"min": 2, "max": 6}
                elif size == "M":
                    target_value = {"min": 6, "max": 10}
                elif size == "L":
                    target_value = {"min": 10, "max": 20}
                elif size == "XL":
                    target_value = {"min": 20, "max": 40}
                elif size == "XXL":
                    target_value = {"min": 40, "max": 60}
                else:
                    target_value = {"min": 6, "max": 10}  # Default to medium
            elif target_type == TimeEstimateType.STORY_POINTS:
                # Convert t-shirt sizes to points
                if size == "XS":
                    target_value = 1
                elif size == "S":
                    target_value = 2
                elif size == "M":
                    target_value = 3
                elif size == "L":
                    target_value = 5
                elif size == "XL":
                    target_value = 8
                elif size == "XXL":
                    target_value = 13
                else:
                    target_value = 3  # Default to medium
        
        # If conversion failed, keep original value
        if target_value is None:
            target_value = source_value
        
        # Update estimate
        estimate.estimate_type = target_type
        estimate.estimate_value = target_value
        estimate.unit = target_unit
        estimate.updated_at = datetime.now()
        
        # Save changes
        self._save_estimates()
        
        return True
    
    def compare_estimate_to_actual(self, task_id: str, time_entries: List[Any]) -> Dict[str, Any]:
        """
        Compare estimated time to actual time spent.
        
        Args:
            task_id: Task identifier
            time_entries: List of time entries for the task
            
        Returns:
            Dictionary with comparison results
        """
        estimate = self.get_estimate_for_task(task_id)
        
        if not estimate:
            return {
                "has_estimate": False,
                "has_entries": bool(time_entries),
                "task_id": task_id
            }
        
        # Calculate total actual time
        total_actual = timedelta()
        for entry in time_entries:
            duration = entry.duration if hasattr(entry, "duration") else None
            if duration:
                total_actual += duration
        
        total_actual_seconds = total_actual.total_seconds()
        total_actual_hours = total_actual_seconds / 3600
        
        # Get estimated time in hours
        estimated_hours = 0
        estimated_min_hours = 0
        estimated_max_hours = 0
        
        if estimate.estimate_type == TimeEstimateType.FIXED:
            value = float(estimate.estimate_value)
            if estimate.unit == "hours":
                estimated_hours = value
            elif estimate.unit == "days":
                estimated_hours = value * 8  # Assuming 8-hour days
            elif estimate.unit == "minutes":
                estimated_hours = value / 60
            else:
                estimated_hours = value
        
        elif estimate.estimate_type == TimeEstimateType.RANGE:
            if isinstance(estimate.estimate_value, dict):
                min_val = float(estimate.estimate_value.get("min", 0))
                max_val = float(estimate.estimate_value.get("max", 0))
                
                if estimate.unit == "hours":
                    estimated_min_hours = min_val
                    estimated_max_hours = max_val
                    estimated_hours = (min_val + max_val) / 2
                elif estimate.unit == "days":
                    estimated_min_hours = min_val * 8
                    estimated_max_hours = max_val * 8
                    estimated_hours = (estimated_min_hours + estimated_max_hours) / 2
                elif estimate.unit == "minutes":
                    estimated_min_hours = min_val / 60
                    estimated_max_hours = max_val / 60
                    estimated_hours = (estimated_min_hours + estimated_max_hours) / 2
                else:
                    estimated_min_hours = min_val
                    estimated_max_hours = max_val
                    estimated_hours = (min_val + max_val) / 2
        
        elif estimate.estimate_type == TimeEstimateType.STORY_POINTS:
            # Convert story points to hours (rough estimate)
            points = float(estimate.estimate_value)
            if points == 1:
                estimated_hours = 1
            elif points == 2:
                estimated_hours = 4
            elif points == 3:
                estimated_hours = 8
            elif points == 5:
                estimated_hours = 16
            elif points == 8:
                estimated_hours = 32
            elif points == 13:
                estimated_hours = 48
            else:
                estimated_hours = points * 4  # Default conversion
        
        elif estimate.estimate_type == TimeEstimateType.T_SHIRT:
            # Convert t-shirt sizes to hours
            size = str(estimate.estimate_value).upper()
            if size == "XS":
                estimated_hours = 2
            elif size == "S":
                estimated_hours = 4
            elif size == "M":
                estimated_hours = 8
            elif size == "L":
                estimated_hours = 16
            elif size == "XL":
                estimated_hours = 32
            elif size == "XXL":
                estimated_hours = 48
            else:
                estimated_hours = 8  # Default to medium
        
        # Calculate variance
        variance_hours = total_actual_hours - estimated_hours
        variance_percentage = (variance_hours / estimated_hours * 100) if estimated_hours > 0 else 0
        
        # Determine if within range
        within_range = True
        if estimated_min_hours and estimated_max_hours:
            within_range = estimated_min_hours <= total_actual_hours <= estimated_max_hours
        
        return {
            "has_estimate": True,
            "has_entries": bool(time_entries),
            "task_id": task_id,
            "estimate_type": estimate.estimate_type.value,
            "estimate_value": estimate.estimate_value,
            "estimate_unit": estimate.unit,
            "estimate_formatted": estimate.formatted_estimate,
            "estimated_hours": estimated_hours,
            "actual_seconds": total_actual_seconds,
            "actual_hours": total_actual_hours,
            "variance_hours": variance_hours,
            "variance_percentage": variance_percentage,
            "within_range": within_range,
            "is_over_estimate": total_actual_hours > estimated_hours,
            "is_under_estimate": total_actual_hours < estimated_hours
        }