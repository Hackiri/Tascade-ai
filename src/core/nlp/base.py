"""
Base interfaces and abstract classes for the Natural Language Task Processing system.

This module defines the core interfaces and abstract classes that form the foundation
of the Natural Language Task Processing system in Tascade AI.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set, Union


class Intent:
    """Represents a recognized intent from natural language input."""
    
    def __init__(self, 
                 name: str, 
                 confidence: float, 
                 parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize an Intent object.
        
        Args:
            name: Name of the intent (e.g., 'create_task', 'list_tasks')
            confidence: Confidence score (0.0-1.0) of the intent recognition
            parameters: Optional parameters extracted from the intent
        """
        self.name = name
        self.confidence = confidence
        self.parameters = parameters or {}
    
    def __str__(self) -> str:
        """Return string representation of the intent."""
        return f"Intent(name='{self.name}', confidence={self.confidence:.2f}, parameters={self.parameters})"
    
    def __repr__(self) -> str:
        """Return string representation of the intent."""
        return self.__str__()


class Entity:
    """Represents an extracted entity from natural language input."""
    
    def __init__(self, 
                 entity_type: str, 
                 value: Any, 
                 start_pos: int, 
                 end_pos: int, 
                 confidence: float = 1.0,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an Entity object.
        
        Args:
            entity_type: Type of entity (e.g., 'task_id', 'priority', 'date')
            value: Extracted value of the entity
            start_pos: Start position in the original text
            end_pos: End position in the original text
            confidence: Confidence score (0.0-1.0) of the entity extraction
            metadata: Optional metadata for the entity
        """
        self.entity_type = entity_type
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.confidence = confidence
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        """Return string representation of the entity."""
        return (f"Entity(type='{self.entity_type}', value='{self.value}', "
                f"position={self.start_pos}-{self.end_pos}, confidence={self.confidence:.2f})")
    
    def __repr__(self) -> str:
        """Return string representation of the entity."""
        return self.__str__()


class NLPResult:
    """Represents the result of natural language processing."""
    
    def __init__(self, 
                 raw_text: str, 
                 intents: List[Intent], 
                 entities: List[Entity],
                 response: Optional[str] = None):
        """
        Initialize an NLPResult object.
        
        Args:
            raw_text: Original input text
            intents: List of recognized intents
            entities: List of extracted entities
            response: Optional response text
        """
        self.raw_text = raw_text
        self.intents = intents
        self.entities = entities
        self.response = response
    
    @property
    def primary_intent(self) -> Optional[Intent]:
        """Get the primary intent with highest confidence."""
        if not self.intents:
            return None
        return sorted(self.intents, key=lambda x: x.confidence, reverse=True)[0]
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of entities matching the specified type
        """
        return [entity for entity in self.entities if entity.entity_type == entity_type]
    
    def __str__(self) -> str:
        """Return string representation of the NLP result."""
        return (f"NLPResult(text='{self.raw_text[:50]}...', "
                f"primary_intent={self.primary_intent}, "
                f"entities_count={len(self.entities)})")


class NLParser(ABC):
    """Abstract base class for natural language parsers."""
    
    @abstractmethod
    def parse(self, text: str) -> NLPResult:
        """
        Parse natural language text into intents and entities.
        
        Args:
            text: Natural language text to parse
            
        Returns:
            NLPResult containing recognized intents and entities
        """
        pass


class IntentRecognizer(ABC):
    """Abstract base class for intent recognizers."""
    
    @abstractmethod
    def recognize_intents(self, text: str) -> List[Intent]:
        """
        Recognize intents from natural language text.
        
        Args:
            text: Natural language text to analyze
            
        Returns:
            List of recognized intents with confidence scores
        """
        pass


class EntityExtractor(ABC):
    """Abstract base class for entity extractors."""
    
    @abstractmethod
    def extract_entities(self, text: str, intents: List[Intent]) -> List[Entity]:
        """
        Extract entities from natural language text.
        
        Args:
            text: Natural language text to analyze
            intents: List of recognized intents to guide extraction
            
        Returns:
            List of extracted entities
        """
        pass


class CommandExecutor(ABC):
    """Abstract base class for command executors."""
    
    @abstractmethod
    def execute(self, nlp_result: NLPResult) -> Dict[str, Any]:
        """
        Execute a command based on NLP result.
        
        Args:
            nlp_result: Result of natural language processing
            
        Returns:
            Result of command execution
        """
        pass


class ConversationContext:
    """Manages conversation context for multi-turn interactions."""
    
    def __init__(self, 
                 session_id: str, 
                 max_history: int = 10):
        """
        Initialize a ConversationContext object.
        
        Args:
            session_id: Unique identifier for the conversation session
            max_history: Maximum number of turns to keep in history
        """
        self.session_id = session_id
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.context_variables: Dict[str, Any] = {}
    
    def add_turn(self, 
                user_input: str, 
                nlp_result: NLPResult, 
                system_response: str) -> None:
        """
        Add a conversation turn to the history.
        
        Args:
            user_input: User's input text
            nlp_result: Result of natural language processing
            system_response: System's response text
        """
        turn = {
            "user_input": user_input,
            "nlp_result": nlp_result,
            "system_response": system_response,
            "timestamp": self._get_current_timestamp()
        }
        
        self.history.append(turn)
        
        # Trim history if it exceeds max_history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def set_context_variable(self, key: str, value: Any) -> None:
        """
        Set a context variable.
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.context_variables[key] = value
    
    def get_context_variable(self, key: str, default: Any = None) -> Any:
        """
        Get a context variable.
        
        Args:
            key: Variable name
            default: Default value if variable doesn't exist
            
        Returns:
            Variable value or default
        """
        return self.context_variables.get(key, default)
    
    def clear_context_variables(self) -> None:
        """Clear all context variables."""
        self.context_variables = {}
    
    def get_last_intent(self) -> Optional[Intent]:
        """
        Get the primary intent from the last turn.
        
        Returns:
            Last primary intent or None if history is empty
        """
        if not self.history:
            return None
        
        last_turn = self.history[-1]
        return last_turn["nlp_result"].primary_intent
    
    def get_recent_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """
        Get entities from recent conversation turns.
        
        Args:
            entity_type: Optional type of entities to retrieve
            
        Returns:
            List of entities from recent turns
        """
        entities = []
        
        for turn in reversed(self.history):
            nlp_result = turn["nlp_result"]
            
            if entity_type:
                turn_entities = nlp_result.get_entities_by_type(entity_type)
            else:
                turn_entities = nlp_result.entities
            
            entities.extend(turn_entities)
        
        return entities
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp as string.
        
        Returns:
            Current timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()


class NLPManager:
    """
    Main manager class for the Natural Language Processing system.
    
    This class orchestrates the NLP pipeline, managing the parser,
    intent recognizer, entity extractor, command executor, and
    conversation context.
    """
    
    def __init__(self, 
                 parser: NLParser,
                 command_executor: CommandExecutor):
        """
        Initialize an NLPManager object.
        
        Args:
            parser: Natural language parser
            command_executor: Command executor
        """
        self.parser = parser
        self.command_executor = command_executor
        self.conversation_contexts: Dict[str, ConversationContext] = {}
    
    def process_input(self, 
                     text: str, 
                     session_id: str = "default") -> Dict[str, Any]:
        """
        Process natural language input and execute appropriate commands.
        
        Args:
            text: Natural language input text
            session_id: Session identifier for conversation context
            
        Returns:
            Result of command execution
        """
        # Get or create conversation context
        context = self._get_conversation_context(session_id)
        
        # Parse input
        nlp_result = self.parser.parse(text)
        
        # Execute command
        result = self.command_executor.execute(nlp_result)
        
        # Update conversation context
        context.add_turn(text, nlp_result, result.get("response", ""))
        
        return result
    
    def _get_conversation_context(self, session_id: str) -> ConversationContext:
        """
        Get or create a conversation context for the given session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation context
        """
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(session_id)
        
        return self.conversation_contexts[session_id]
