"""
Natural Language Parser implementation for the Tascade AI NLP system.

This module implements the core parser that processes natural language input
and extracts intents and entities for task management operations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta

from .base import NLParser, IntentRecognizer, EntityExtractor, NLPResult, Intent, Entity


class RuleBasedIntentRecognizer(IntentRecognizer):
    """
    Rule-based intent recognizer that uses patterns to identify intents.
    
    This class implements a simple pattern-matching approach to intent recognition,
    using predefined patterns for common task management operations.
    """
    
    def __init__(self):
        """Initialize the rule-based intent recognizer with predefined patterns."""
        self.intent_patterns = {
            "create_task": [
                r"create\s+(?:a\s+)?(?:new\s+)?task",
                r"add\s+(?:a\s+)?(?:new\s+)?task",
                r"make\s+(?:a\s+)?(?:new\s+)?task",
                r"start\s+(?:a\s+)?(?:new\s+)?task"
            ],
            "list_tasks": [
                r"list\s+(?:all\s+)?tasks",
                r"show\s+(?:all\s+)?tasks",
                r"display\s+(?:all\s+)?tasks",
                r"what\s+(?:are\s+)?(?:my\s+)?tasks"
            ],
            "update_task": [
                r"update\s+(?:the\s+)?task",
                r"modify\s+(?:the\s+)?task",
                r"change\s+(?:the\s+)?task",
                r"edit\s+(?:the\s+)?task"
            ],
            "delete_task": [
                r"delete\s+(?:the\s+)?task",
                r"remove\s+(?:the\s+)?task",
                r"cancel\s+(?:the\s+)?task"
            ],
            "complete_task": [
                r"complete\s+(?:the\s+)?task",
                r"finish\s+(?:the\s+)?task",
                r"mark\s+(?:the\s+)?task\s+(?:as\s+)?(?:complete|completed|done)",
                r"set\s+(?:the\s+)?task\s+(?:as\s+)?(?:complete|completed|done)"
            ],
            "get_task": [
                r"get\s+(?:the\s+)?task",
                r"show\s+(?:the\s+)?task",
                r"display\s+(?:the\s+)?task",
                r"find\s+(?:the\s+)?task"
            ],
            "set_priority": [
                r"set\s+(?:the\s+)?(?:task\s+)?priority",
                r"change\s+(?:the\s+)?(?:task\s+)?priority",
                r"update\s+(?:the\s+)?(?:task\s+)?priority"
            ],
            "set_due_date": [
                r"set\s+(?:the\s+)?(?:task\s+)?due\s+date",
                r"change\s+(?:the\s+)?(?:task\s+)?due\s+date",
                r"update\s+(?:the\s+)?(?:task\s+)?due\s+date"
            ],
            "add_dependency": [
                r"add\s+(?:a\s+)?dependency",
                r"create\s+(?:a\s+)?dependency",
                r"set\s+(?:a\s+)?dependency"
            ],
            "remove_dependency": [
                r"remove\s+(?:a\s+)?dependency",
                r"delete\s+(?:a\s+)?dependency",
                r"cancel\s+(?:a\s+)?dependency"
            ],
            "get_recommendations": [
                r"(?:get|show|display)\s+(?:task\s+)?recommendations",
                r"recommend\s+(?:a\s+)?task",
                r"what\s+should\s+I\s+work\s+on",
                r"suggest\s+(?:a\s+)?task"
            ],
            "help": [
                r"help",
                r"how\s+(?:do\s+)?I",
                r"what\s+can\s+(?:you|I)\s+do",
                r"what\s+commands"
            ]
        }
        
        # Compile patterns for faster matching
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def recognize_intents(self, text: str) -> List[Intent]:
        """
        Recognize intents from natural language text using pattern matching.
        
        Args:
            text: Natural language text to analyze
            
        Returns:
            List of recognized intents with confidence scores
        """
        intents = []
        text_lower = text.lower()
        
        # Check each intent pattern
        for intent_name, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    # Calculate confidence based on match length and position
                    match_length = match.end() - match.start()
                    text_length = len(text_lower)
                    position_factor = 1.0 - (match.start() / text_length) * 0.5
                    coverage_factor = match_length / text_length
                    
                    # Combine factors for final confidence score
                    confidence = 0.7 + (position_factor * 0.2) + (coverage_factor * 0.1)
                    confidence = min(confidence, 0.95)  # Cap at 0.95
                    
                    intents.append(Intent(intent_name, confidence))
                    break  # Only add each intent once
        
        # Add fallback intent if no intents were recognized
        if not intents:
            intents.append(Intent("unknown", 0.3))
        
        return sorted(intents, key=lambda x: x.confidence, reverse=True)


class PatternEntityExtractor(EntityExtractor):
    """
    Pattern-based entity extractor that uses regular expressions to extract entities.
    
    This class implements a pattern-matching approach to entity extraction,
    using predefined patterns for common entity types in task management.
    """
    
    def __init__(self):
        """Initialize the pattern-based entity extractor with predefined patterns."""
        # Task ID patterns
        self.task_id_patterns = [
            r"task\s+(?:id\s+)?([a-zA-Z0-9_-]+)",
            r"#([a-zA-Z0-9_-]+)"
        ]
        
        # Priority patterns
        self.priority_patterns = [
            r"priority\s+(?:is\s+)?(\w+)",
            r"(\w+)\s+priority"
        ]
        
        # Date patterns
        self.date_patterns = [
            r"(?:due|by|on)\s+(?:the\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})",
            r"(?:due|by|on)\s+(?:the\s+)?(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(?:due|by|on)\s+(?:the\s+)?(\d{4}-\d{1,2}-\d{1,2})"
        ]
        
        # Relative date patterns
        self.relative_date_patterns = [
            r"(today)",
            r"(tomorrow)",
            r"(yesterday)",
            r"next\s+(week|month|year)",
            r"in\s+(\d+)\s+(day|days|week|weeks|month|months)"
        ]
        
        # Title patterns
        self.title_patterns = [
            r"title\s+(?:is\s+)?[\"'](.+?)[\"']",
            r"called\s+[\"'](.+?)[\"']",
            r"named\s+[\"'](.+?)[\"']"
        ]
        
        # Description patterns
        self.description_patterns = [
            r"description\s+(?:is\s+)?[\"'](.+?)[\"']",
            r"description:\s*[\"'](.+?)[\"']"
        ]
        
        # Compile all patterns
        self.compiled_patterns = {
            "task_id": [re.compile(p, re.IGNORECASE) for p in self.task_id_patterns],
            "priority": [re.compile(p, re.IGNORECASE) for p in self.priority_patterns],
            "date": [re.compile(p, re.IGNORECASE) for p in self.date_patterns],
            "relative_date": [re.compile(p, re.IGNORECASE) for p in self.relative_date_patterns],
            "title": [re.compile(p, re.IGNORECASE) for p in self.title_patterns],
            "description": [re.compile(p, re.IGNORECASE) for p in self.description_patterns]
        }
    
    def extract_entities(self, text: str, intents: List[Intent]) -> List[Entity]:
        """
        Extract entities from natural language text using pattern matching.
        
        Args:
            text: Natural language text to analyze
            intents: List of recognized intents to guide extraction
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract task IDs
        for pattern in self.compiled_patterns["task_id"]:
            for match in pattern.finditer(text):
                task_id = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                entities.append(Entity("task_id", task_id, start_pos, end_pos))
        
        # Extract priorities
        for pattern in self.compiled_patterns["priority"]:
            for match in pattern.finditer(text):
                priority = match.group(1).lower()
                start_pos = match.start(1)
                end_pos = match.end(1)
                
                # Normalize priority values
                if priority in ["high", "urgent", "important"]:
                    normalized_priority = "high"
                elif priority in ["medium", "normal", "moderate"]:
                    normalized_priority = "medium"
                elif priority in ["low", "minor"]:
                    normalized_priority = "low"
                else:
                    normalized_priority = priority
                
                entities.append(Entity("priority", normalized_priority, start_pos, end_pos))
        
        # Extract dates
        for pattern in self.compiled_patterns["date"]:
            for match in pattern.finditer(text):
                date_str = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                entities.append(Entity("date", date_str, start_pos, end_pos))
        
        # Extract relative dates
        for pattern in self.compiled_patterns["relative_date"]:
            for match in pattern.finditer(text):
                relative_date = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                entities.append(Entity("relative_date", relative_date, start_pos, end_pos))
        
        # Extract titles
        for pattern in self.compiled_patterns["title"]:
            for match in pattern.finditer(text):
                title = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                entities.append(Entity("title", title, start_pos, end_pos))
        
        # Extract descriptions
        for pattern in self.compiled_patterns["description"]:
            for match in pattern.finditer(text):
                description = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                entities.append(Entity("description", description, start_pos, end_pos))
        
        # Extract title from create_task intent if not already extracted
        if not any(e.entity_type == "title" for e in entities):
            primary_intent = sorted(intents, key=lambda x: x.confidence, reverse=True)[0]
            if primary_intent.name == "create_task":
                # Try to extract title from the text after "create task" or similar
                create_patterns = [
                    re.compile(r"create\s+(?:a\s+)?(?:new\s+)?task\s+(?:called\s+)?[\"']?([^\"']+)[\"']?", re.IGNORECASE),
                    re.compile(r"add\s+(?:a\s+)?(?:new\s+)?task\s+(?:called\s+)?[\"']?([^\"']+)[\"']?", re.IGNORECASE)
                ]
                
                for pattern in create_patterns:
                    match = pattern.search(text)
                    if match:
                        title = match.group(1).strip()
                        if title:
                            start_pos = match.start(1)
                            end_pos = match.end(1)
                            entities.append(Entity("title", title, start_pos, end_pos))
                            break
        
        return entities


class DefaultNLParser(NLParser):
    """
    Default implementation of the Natural Language Parser.
    
    This class combines intent recognition and entity extraction to parse
    natural language input for task management operations.
    """
    
    def __init__(self, 
                 intent_recognizer: Optional[IntentRecognizer] = None,
                 entity_extractor: Optional[EntityExtractor] = None):
        """
        Initialize the default NL parser.
        
        Args:
            intent_recognizer: Intent recognizer to use (default: RuleBasedIntentRecognizer)
            entity_extractor: Entity extractor to use (default: PatternEntityExtractor)
        """
        self.intent_recognizer = intent_recognizer or RuleBasedIntentRecognizer()
        self.entity_extractor = entity_extractor or PatternEntityExtractor()
    
    def parse(self, text: str) -> NLPResult:
        """
        Parse natural language text into intents and entities.
        
        Args:
            text: Natural language text to parse
            
        Returns:
            NLPResult containing recognized intents and entities
        """
        # Recognize intents
        intents = self.intent_recognizer.recognize_intents(text)
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(text, intents)
        
        # Create and return NLP result
        return NLPResult(text, intents, entities)
