"""
Tests for the Task Recommendation System.

This module contains tests for the Task Recommendation System,
ensuring it works correctly with other components of Tascade AI.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import tempfile
import json
import shutil

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.task_recommendation import TaskRecommendationSystem
from src.core.recommendation.base import UserPreference


class TestTaskRecommendationSystem(unittest.TestCase):
    """Tests for the Task Recommendation System."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock task manager
        self.mock_task_manager = MagicMock()
        self.mock_task_manager.get_all_tasks.return_value = self._create_sample_tasks()
        self.mock_task_manager.get_task.side_effect = self._get_task_by_id
        
        # Create mock time tracking system
        self.mock_time_tracking = MagicMock()
        self.mock_time_tracking.get_time_by_task.return_value = {
            "success": True,
            "time_by_task": {
                "task1": {"seconds": 7200},  # 2 hours
                "task2": {"seconds": 3600}   # 1 hour
            }
        }
        
        # Create recommendation system
        self.recommendation_system = TaskRecommendationSystem(
            task_manager=self.mock_task_manager,
            time_tracking_system=self.mock_time_tracking,
            data_dir=self.test_dir
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def _create_sample_tasks(self):
        """Create sample tasks for testing."""
        return [
            {
                "id": "task1",
                "title": "Implement login functionality",
                "description": "Create login form and authentication logic",
                "status": "pending",
                "priority": "high",
                "category": "frontend",
                "type": "feature",
                "tags": ["authentication", "ui"],
                "estimated_time": 120,  # 2 hours
                "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "dependencies": []
            },
            {
                "id": "task2",
                "title": "Fix navigation bar bug",
                "description": "Fix issue with dropdown menu in navigation bar",
                "status": "pending",
                "priority": "medium",
                "category": "frontend",
                "type": "bug",
                "tags": ["ui", "bug"],
                "estimated_time": 60,  # 1 hour
                "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                "dependencies": []
            },
            {
                "id": "task3",
                "title": "Implement user profile API",
                "description": "Create API endpoints for user profile management",
                "status": "done",  # This task is done, should not be recommended
                "priority": "medium",
                "category": "backend",
                "type": "feature",
                "tags": ["api", "user"],
                "estimated_time": 180,  # 3 hours
                "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                "dependencies": ["task1"]
            }
        ]
    
    def _get_task_by_id(self, task_id):
        """Get a task by ID."""
        for task in self._create_sample_tasks():
            if task["id"] == task_id:
                return task
        return None
    
    def test_recommend_tasks(self):
        """Test recommending tasks."""
        # Get recommendations
        recommendations = self.recommendation_system.recommend_tasks(
            user_id="test_user",
            limit=5
        )
        
        # Check recommendations
        self.assertTrue(recommendations["success"])
        self.assertEqual(recommendations["user_id"], "test_user")
        self.assertIsNotNone(recommendations["recommendations"])
        self.assertGreaterEqual(len(recommendations["recommendations"]), 1)
        
        # Check that only pending tasks are recommended
        for rec in recommendations["recommendations"]:
            self.assertEqual(rec["task"]["status"], "pending")
    
    def test_user_preferences(self):
        """Test user preferences."""
        # Set a preference
        result = self.recommendation_system.set_user_preference(
            user_id="test_user",
            preference_type="preferred_categories",
            preference_value=["frontend"],
            weight=0.8
        )
        
        self.assertTrue(result["success"])
        
        # Get preferences
        preferences = self.recommendation_system.get_user_preferences("test_user")
        
        self.assertTrue(preferences["success"])
        self.assertEqual(preferences["user_id"], "test_user")
        self.assertGreaterEqual(len(preferences["preferences"]), 1)
        
        # Check preference value
        pref = preferences["preferences"][0]
        self.assertEqual(pref["preference_type"], "preferred_categories")
        self.assertEqual(pref["preference_value"], ["frontend"])
        self.assertEqual(pref["weight"], 0.8)
        
        # Delete preference
        result = self.recommendation_system.delete_user_preference(
            user_id="test_user",
            preference_type="preferred_categories"
        )
        
        self.assertTrue(result["success"])
        
        # Check that preference is deleted
        preferences = self.recommendation_system.get_user_preferences("test_user")
        self.assertEqual(len(preferences["preferences"]), 0)
    
    def test_historical_analysis(self):
        """Test historical performance analysis."""
        # Record task completion
        task_data = self._get_task_by_id("task3")
        
        result = self.recommendation_system.record_task_completion(
            user_id="test_user",
            task_id="task3",
            task_data=task_data
        )
        
        self.assertTrue(result["success"])
        
        # Get user performance
        performance = self.recommendation_system.get_user_performance("test_user")
        
        self.assertTrue(performance["success"])
        self.assertEqual(performance["user_id"], "test_user")
        self.assertIsNotNone(performance["performance"])
        
        # Get task completion patterns
        patterns = self.recommendation_system.get_task_completion_patterns("test_user")
        
        self.assertTrue(patterns["success"])
        self.assertEqual(patterns["user_id"], "test_user")
        self.assertIsNotNone(patterns["patterns"])
    
    def test_workload_balancing(self):
        """Test workload balancing."""
        # Set workload settings
        result = self.recommendation_system.set_workload_settings(
            user_id="test_user",
            daily_capacity_minutes=480,  # 8 hours
            max_concurrent_tasks=5,
            preferred_task_size="medium"
        )
        
        self.assertTrue(result["success"])
        
        # Get workload settings
        settings = self.recommendation_system.get_workload_settings("test_user")
        
        self.assertTrue(settings["success"])
        self.assertEqual(settings["user_id"], "test_user")
        self.assertEqual(settings["settings"]["daily_capacity_minutes"], 480)
        self.assertEqual(settings["settings"]["max_concurrent_tasks"], 5)
        self.assertEqual(settings["settings"]["preferred_task_size"], "medium")
        
        # Get workload metrics
        tasks = self._create_sample_tasks()
        metrics = self.recommendation_system.get_workload_metrics("test_user", tasks)
        
        self.assertTrue(metrics["success"])
        self.assertEqual(metrics["user_id"], "test_user")
        self.assertIsNotNone(metrics["metrics"])
        self.assertEqual(metrics["metrics"]["total_tasks"], 3)
    
    def test_recommendation_explanation(self):
        """Test recommendation explanation."""
        # Get explanation
        explanation = self.recommendation_system.explain_recommendation(
            user_id="test_user",
            task_id="task1"
        )
        
        self.assertTrue(explanation["success"])
        self.assertEqual(explanation["user_id"], "test_user")
        self.assertEqual(explanation["task_id"], "task1")
        self.assertIsNotNone(explanation["explanation"])
        self.assertIsNotNone(explanation["explanation"]["explanation"])
    
    def test_task_completion_time_prediction(self):
        """Test task completion time prediction."""
        # Record task completion for historical data
        task_data = self._get_task_by_id("task3")
        
        self.recommendation_system.record_task_completion(
            user_id="test_user",
            task_id="task3",
            task_data=task_data
        )
        
        # Predict completion time
        prediction = self.recommendation_system.predict_task_completion_time(
            user_id="test_user",
            task_id="task1"
        )
        
        self.assertTrue(prediction["success"])
        self.assertEqual(prediction["user_id"], "test_user")
        self.assertEqual(prediction["task_id"], "task1")
        self.assertIsNotNone(prediction["prediction"])
        self.assertIsNotNone(prediction["prediction"]["predicted_minutes"])
    
    def test_integration_with_task_manager(self):
        """Test integration with task manager."""
        # Verify that task manager is called
        self.recommendation_system.recommend_tasks("test_user")
        self.mock_task_manager.get_all_tasks.assert_called_once()
    
    def test_integration_with_time_tracking(self):
        """Test integration with time tracking system."""
        # Record task completion
        task_data = self._get_task_by_id("task1")
        
        self.recommendation_system.record_task_completion(
            user_id="test_user",
            task_id="task1",
            task_data=task_data
        )
        
        # Verify that time tracking system is called
        self.mock_time_tracking.get_time_by_task.assert_called_with(
            task_id="task1",
            user_id="test_user"
        )


if __name__ == "__main__":
    unittest.main()
