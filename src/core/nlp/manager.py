"""
Natural Language Processing Manager for the Tascade AI NLP system.

This module implements the main manager class that orchestrates the NLP pipeline,
integrating the parser, executor, and conversation context.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set, Union

from .base import NLPManager, NLParser, CommandExecutor, ConversationContext
from .parser import DefaultNLParser
from .executor import TaskCommandExecutor


class TascadeNLPManager:
    """
    Main manager class for the Tascade AI Natural Language Processing system.
    
    This class orchestrates the NLP pipeline, managing the parser, executor,
    and conversation contexts for natural language task processing.
    """
    
    def __init__(self, 
                 task_manager, 
                 recommendation_system=None,
                 parser: Optional[NLParser] = None,
                 command_executor: Optional[CommandExecutor] = None):
        """
        Initialize the Tascade NLP Manager.
        
        Args:
            task_manager: Task manager instance
            recommendation_system: Optional recommendation system
            parser: Optional custom parser (default: DefaultNLParser)
            command_executor: Optional custom command executor (default: TaskCommandExecutor)
        """
        self.task_manager = task_manager
        self.recommendation_system = recommendation_system
        self.parser = parser or DefaultNLParser()
        self.command_executor = command_executor or TaskCommandExecutor(
            task_manager=task_manager,
            recommendation_system=recommendation_system
        )
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.logger = logging.getLogger(__name__)
    
    def process_input(self, 
                     text: str, 
                     session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural language input and execute appropriate commands.
        
        Args:
            text: Natural language input text
            session_id: Optional session identifier for conversation context
            
        Returns:
            Result of command execution
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get or create conversation context
        context = self._get_conversation_context(session_id)
        
        try:
            # Parse input
            nlp_result = self.parser.parse(text)
            
            # Execute command
            result = self.command_executor.execute(nlp_result)
            
            # Update conversation context
            context.add_turn(text, nlp_result, result.get("response", ""))
            
            return result
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred while processing your request: {str(e)}",
                "data": None,
                "response": f"An error occurred while processing your request: {str(e)}"
            }
    
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
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns
        """
        context = self._get_conversation_context(session_id)
        return context.history
    
    def clear_session_history(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if session_id in self.conversation_contexts:
            self.conversation_contexts[session_id].history = []
            return True
        return False
