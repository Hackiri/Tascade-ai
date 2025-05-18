"""
User Preference Manager for the Task Recommendation System.

This module implements the user preference management functionality,
allowing users to set, get, and delete preferences that influence task recommendations.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import os
import json
import logging
import uuid

from .base import UserPreference, UserPreferenceManager


class FileBasedPreferenceManager(UserPreferenceManager):
    """User preference manager that stores preferences in a JSON file."""
    
    def __init__(self, 
                 data_dir: str = None,
                 preferences_file: str = "user_preferences.json",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a file-based preference manager.
        
        Args:
            data_dir: Directory for storing preference data
            preferences_file: File name for preferences
            logger: Optional logger
        """
        super().__init__(logger)
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tascade", "data")
        self.preferences_file = os.path.join(self.data_dir, preferences_file)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize preferences
        self.preferences: Dict[str, Dict[str, UserPreference]] = {}
        
        # Load existing preferences
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """Load preferences from the preferences file."""
        if not os.path.exists(self.preferences_file):
            self.logger.info(f"Preferences file not found: {self.preferences_file}")
            return
        
        try:
            with open(self.preferences_file, 'r') as f:
                data = json.load(f)
                
                for user_id, user_prefs in data.items():
                    self.preferences[user_id] = {}
                    for pref_type, pref_data in user_prefs.items():
                        self.preferences[user_id][pref_type] = UserPreference.from_dict(pref_data)
                        
            self.logger.info(f"Loaded preferences for {len(self.preferences)} users")
        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
    
    def _save_preferences(self) -> None:
        """Save preferences to the preferences file."""
        try:
            # Convert to serializable format
            data = {}
            for user_id, user_prefs in self.preferences.items():
                data[user_id] = {}
                for pref_type, pref in user_prefs.items():
                    data[user_id][pref_type] = pref.to_dict()
            
            with open(self.preferences_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved preferences for {len(self.preferences)} users")
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
    
    def get_preferences(self, user_id: str) -> List[UserPreference]:
        """
        Get preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user preferences
        """
        if user_id not in self.preferences:
            return []
        
        return list(self.preferences[user_id].values())
    
    def get_preference(self, user_id: str, preference_type: str) -> Optional[UserPreference]:
        """
        Get a specific preference for a user.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            
        Returns:
            User preference or None if not found
        """
        if user_id not in self.preferences or preference_type not in self.preferences[user_id]:
            return None
        
        return self.preferences[user_id][preference_type]
    
    def set_preference(self, preference: UserPreference) -> bool:
        """
        Set a user preference.
        
        Args:
            preference: Preference to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = preference.user_id
            pref_type = preference.preference_type
            
            # Initialize user preferences if needed
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
            
            # Update preference
            preference.updated_at = datetime.now()
            self.preferences[user_id][pref_type] = preference
            
            # Save preferences
            self._save_preferences()
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            return False
    
    def delete_preference(self, user_id: str, preference_type: str) -> bool:
        """
        Delete a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.preferences or preference_type not in self.preferences[user_id]:
                return False
            
            # Delete preference
            del self.preferences[user_id][preference_type]
            
            # Clean up empty user entries
            if not self.preferences[user_id]:
                del self.preferences[user_id]
            
            # Save preferences
            self._save_preferences()
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting preference: {e}")
            return False
    
    def clear_preferences(self, user_id: str) -> bool:
        """
        Clear all preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.preferences:
                return False
            
            # Delete all preferences for user
            del self.preferences[user_id]
            
            # Save preferences
            self._save_preferences()
            
            return True
        except Exception as e:
            self.logger.error(f"Error clearing preferences: {e}")
            return False


class PreferenceType:
    """Enumeration of preference types."""
    
    TAG = "tag_preference"
    CATEGORY = "category_preference"
    PRIORITY = "priority_preference"
    TIME_OF_DAY = "time_of_day_preference"
    DURATION = "duration_preference"
    COMPLEXITY = "complexity_preference"
    TASK_TYPE = "task_type_preference"
    CUSTOM = "custom_preference"


def create_preference(user_id: str, 
                     preference_type: str, 
                     preference_value: Any, 
                     weight: float = 1.0,
                     metadata: Optional[Dict[str, Any]] = None) -> UserPreference:
    """
    Create a user preference.
    
    Args:
        user_id: User identifier
        preference_type: Type of preference
        preference_value: Value of the preference
        weight: Weight of this preference in recommendations
        metadata: Additional metadata
        
    Returns:
        User preference
    """
    return UserPreference(
        user_id=user_id,
        preference_type=preference_type,
        preference_value=preference_value,
        weight=weight,
        metadata=metadata
    )
