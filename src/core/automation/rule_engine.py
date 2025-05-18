"""
Rule Engine for the Task Automation System.

This module provides the core engine for evaluating and executing automation rules.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json
import os
import threading
import queue
import time
import uuid
import logging

from .base import AutomationRule, Trigger, Condition, Action
from .triggers import create_trigger_from_dict
from .conditions import create_condition_from_dict
from .actions import create_action_from_dict


class RuleEngine:
    """Engine for evaluating and executing automation rules."""
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the rule engine.
        
        Args:
            rules_file: Optional path to a file containing rules
        """
        self.rules: Dict[str, AutomationRule] = {}
        self.rules_file = rules_file
        self.event_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.logger = logging.getLogger("tascade.automation.rule_engine")
        
        # Load rules if a file is provided
        if self.rules_file and os.path.exists(self.rules_file):
            self._load_rules()
    
    def register_rule(self, rule: AutomationRule) -> None:
        """
        Register a rule with the engine.
        
        Args:
            rule: Rule to register
        """
        self.rules[rule.id] = rule
        
        # Save rules if a file is provided
        if self.rules_file:
            self._save_rules()
    
    def unregister_rule(self, rule_id: str) -> bool:
        """
        Unregister a rule from the engine.
        
        Args:
            rule_id: ID of the rule to unregister
            
        Returns:
            True if the rule was unregistered, False if it wasn't found
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            
            # Save rules if a file is provided
            if self.rules_file:
                self._save_rules()
            
            return True
        
        return False
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """
        Get a rule by ID.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            The rule if found, None otherwise
        """
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[AutomationRule]:
        """
        Get all rules.
        
        Returns:
            List of all rules
        """
        return list(self.rules.values())
    
    def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process an event and execute matching rules.
        
        Args:
            event: Event to process
            
        Returns:
            List of results from executing matching rules
        """
        results = []
        
        # Add timestamp to the event if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.now().isoformat()
        
        # Find rules that match the event
        matching_rules = []
        for rule in self.rules.values():
            if rule.matches_event(event):
                matching_rules.append(rule)
        
        # Execute matching rules
        for rule in matching_rules:
            # Create context for rule evaluation and execution
            context = {
                "event": event,
                "rule": rule.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add task to context if present in the event
            if "task" in event:
                context["task"] = event["task"]
            
            # Add task ID to context if present in the event
            if "task_id" in event:
                context["task_id"] = event["task_id"]
            
            # Evaluate the rule's conditions
            if rule.evaluate(context):
                # Execute the rule's actions
                action_results = rule.execute(context)
                
                results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "matched": True,
                    "executed": True,
                    "results": action_results
                })
            else:
                results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "matched": True,
                    "executed": False,
                    "reason": "Conditions not met"
                })
        
        return results
    
    def queue_event(self, event: Dict[str, Any]) -> None:
        """
        Queue an event for asynchronous processing.
        
        Args:
            event: Event to queue
        """
        self.event_queue.put(event)
    
    def start_processing(self) -> None:
        """Start asynchronous event processing."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
    
    def stop_processing(self) -> None:
        """Stop asynchronous event processing."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def create_rule(self, 
                   name: str,
                   description: str,
                   triggers: List[Dict[str, Any]],
                   conditions: List[Dict[str, Any]],
                   actions: List[Dict[str, Any]],
                   enabled: bool = True) -> AutomationRule:
        """
        Create a new automation rule.
        
        Args:
            name: Name of the rule
            description: Description of the rule
            triggers: List of trigger configurations
            conditions: List of condition configurations
            actions: List of action configurations
            enabled: Whether the rule is enabled
            
        Returns:
            The created rule
        """
        # Create triggers
        trigger_objects = []
        for trigger_config in triggers:
            try:
                trigger = create_trigger_from_dict(trigger_config)
                trigger_objects.append(trigger)
            except ValueError as e:
                self.logger.error(f"Error creating trigger: {e}")
                continue
        
        # Create conditions
        condition_objects = []
        for condition_config in conditions:
            try:
                condition = create_condition_from_dict(condition_config)
                condition_objects.append(condition)
            except ValueError as e:
                self.logger.error(f"Error creating condition: {e}")
                continue
        
        # Create actions
        action_objects = []
        for action_config in actions:
            try:
                action = create_action_from_dict(action_config)
                action_objects.append(action)
            except ValueError as e:
                self.logger.error(f"Error creating action: {e}")
                continue
        
        # Create the rule
        rule = AutomationRule(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            triggers=trigger_objects,
            conditions=condition_objects,
            actions=action_objects,
            enabled=enabled,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Register the rule
        self.register_rule(rule)
        
        return rule
    
    def update_rule(self, 
                   rule_id: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   triggers: Optional[List[Dict[str, Any]]] = None,
                   conditions: Optional[List[Dict[str, Any]]] = None,
                   actions: Optional[List[Dict[str, Any]]] = None,
                   enabled: Optional[bool] = None) -> Optional[AutomationRule]:
        """
        Update an existing automation rule.
        
        Args:
            rule_id: ID of the rule to update
            name: New name for the rule
            description: New description for the rule
            triggers: New trigger configurations
            conditions: New condition configurations
            actions: New action configurations
            enabled: New enabled state
            
        Returns:
            The updated rule, or None if the rule wasn't found
        """
        # Get the rule
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        # Update the rule
        if name is not None:
            rule.name = name
        
        if description is not None:
            rule.description = description
        
        if enabled is not None:
            rule.enabled = enabled
        
        # Update triggers if provided
        if triggers is not None:
            trigger_objects = []
            for trigger_config in triggers:
                try:
                    trigger = create_trigger_from_dict(trigger_config)
                    trigger_objects.append(trigger)
                except ValueError as e:
                    self.logger.error(f"Error creating trigger: {e}")
                    continue
            
            rule.triggers = trigger_objects
        
        # Update conditions if provided
        if conditions is not None:
            condition_objects = []
            for condition_config in conditions:
                try:
                    condition = create_condition_from_dict(condition_config)
                    condition_objects.append(condition)
                except ValueError as e:
                    self.logger.error(f"Error creating condition: {e}")
                    continue
            
            rule.conditions = condition_objects
        
        # Update actions if provided
        if actions is not None:
            action_objects = []
            for action_config in actions:
                try:
                    action = create_action_from_dict(action_config)
                    action_objects.append(action)
                except ValueError as e:
                    self.logger.error(f"Error creating action: {e}")
                    continue
            
            rule.actions = action_objects
        
        # Update the timestamp
        rule.updated_at = datetime.now()
        
        # Save the rules
        if self.rules_file:
            self._save_rules()
        
        return rule
    
    def _process_events(self) -> None:
        """Process events from the queue."""
        while self.running:
            try:
                # Get an event from the queue with timeout
                event = self.event_queue.get(timeout=1.0)
                
                # Process the event
                try:
                    self.process_event(event)
                except Exception as e:
                    self.logger.error(f"Error processing event: {e}")
                
                # Mark as done
                self.event_queue.task_done()
            except queue.Empty:
                # No events in queue, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"Error in event processing thread: {e}")
    
    def _load_rules(self) -> None:
        """Load rules from the rules file."""
        try:
            with open(self.rules_file, 'r') as f:
                rules_data = json.load(f)
            
            for rule_data in rules_data:
                try:
                    rule = AutomationRule.from_dict(
                        rule_data,
                        create_trigger_from_dict,
                        create_condition_from_dict,
                        create_action_from_dict
                    )
                    self.rules[rule.id] = rule
                except Exception as e:
                    self.logger.error(f"Error loading rule: {e}")
        except Exception as e:
            self.logger.error(f"Error loading rules: {e}")
    
    def _save_rules(self) -> None:
        """Save rules to the rules file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
            
            # Convert rules to dictionaries
            rules_data = [rule.to_dict() for rule in self.rules.values()]
            
            # Save to file
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving rules: {e}")