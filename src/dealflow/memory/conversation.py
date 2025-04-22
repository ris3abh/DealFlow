# dealflow/memory/conversation.py
from typing import List, Tuple, Optional, Dict, Any

from camel.memories import (
    ChatHistoryBlock,
    LongtermAgentMemory,
    MemoryRecord,
    ScoreBasedContextCreator,
    VectorDBBlock,
)
from camel.messages import BaseMessage
from camel.types import ModelType, OpenAIBackendRole
from camel.utils import OpenAITokenCounter

from dealflow.utils.logger import logger
from dealflow.exceptions import MemoryError

class ConversationMemory:
    """Memory for storing and retrieving conversation history."""
    
    def __init__(
        self, 
        model_type: ModelType = ModelType.GPT_4O_MINI,
        token_limit: int = 1024,
        keep_rate: float = 0.9
    ):
        """Initialize conversation memory.
        
        Args:
            model_type: The model type for token counting.
            token_limit: The maximum number of tokens allowed in the context.
            keep_rate: The rate at which to keep historical messages.
        """
        self.token_counter = OpenAITokenCounter(model_type)
        self.context_creator = ScoreBasedContextCreator(
            token_counter=self.token_counter,
            token_limit=token_limit,
        )
        self.chat_history_block = ChatHistoryBlock(keep_rate=keep_rate)
        self.vector_db_block = VectorDBBlock()
        
        self.memory = LongtermAgentMemory(
            context_creator=self.context_creator,
            chat_history_block=self.chat_history_block,
            vector_db_block=self.vector_db_block,
        )
        
        logger.info(f"Initialized conversation memory with token limit {token_limit}")
        
    def add_user_message(self, content: str) -> None:
        """Add a user message to memory.
        
        Args:
            content: The content of the message.
        """
        try:
            record = MemoryRecord(
                message=BaseMessage.make_user_message(
                    role_name="User",
                    content=content,
                ),
                role_at_backend=OpenAIBackendRole.USER,
            )
            self.memory.write_record(record)
            logger.debug(f"Added user message to memory: {content[:50]}...")
        except Exception as e:
            logger.error(f"Error adding user message to memory: {e}")
            raise MemoryError(f"Error adding user message to memory: {e}")
    
    def add_assistant_message(self, content: str, role_name: str = "Assistant") -> None:
        """Add an assistant message to memory.
        
        Args:
            content: The content of the message.
            role_name: The name of the assistant role.
        """
        try:
            record = MemoryRecord(
                message=BaseMessage.make_assistant_message(
                    role_name=role_name,
                    content=content,
                ),
                role_at_backend=OpenAIBackendRole.ASSISTANT,
            )
            self.memory.write_record(record)
            logger.debug(f"Added assistant message to memory: {content[:50]}...")
        except Exception as e:
            logger.error(f"Error adding assistant message to memory: {e}")
            raise MemoryError(f"Error adding assistant message to memory: {e}")
    
    def get_context(self) -> Tuple[List[Dict[str, str]], int]:
        """Get the conversation context.
        
        Returns:
            A tuple containing the conversation context and the token count.
        """
        try:
            context, token_count = self.memory.get_context()
            logger.debug(f"Retrieved context with token count: {token_count}")
            return context, token_count
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise MemoryError(f"Error retrieving context: {e}")
    
    def get_conversation_history(self, as_string: bool = True) -> Any:
        """Get the conversation history.
        
        Args:
            as_string: Whether to return the history as a string.
            
        Returns:
            The conversation history as a string or a list of messages.
        """
        try:
            context, _ = self.get_context()
            
            if as_string:
                history = ""
                for message in context:
                    role = message.get("role", "")
                    content = message.get("content", "")
                    if role == "user":
                        history += f"User: {content}\n"
                    elif role == "assistant":
                        history += f"Assistant: {content}\n"
                return history.strip()
            else:
                return context
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            raise MemoryError(f"Error retrieving conversation history: {e}")
    
    def clear(self) -> None:
        """Clear the memory."""
        try:
            self.memory.clear()
            logger.info("Cleared conversation memory")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            raise MemoryError(f"Error clearing memory: {e}")