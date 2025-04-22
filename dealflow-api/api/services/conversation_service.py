from typing import Tuple, List, Dict, Any, AsyncGenerator, Optional
import asyncio
from datetime import datetime

from dealflow.stages.conversation import ConversationStage as DealFlowStage
from api.models.schemas import ConversationStage
from api.core.client_manager import ClientManager
from api.utils.logging import logger

class ConversationService:
    """Service for handling conversations"""
    
    def __init__(self, client_manager: ClientManager):
        self.client_manager = client_manager
    
    async def process_message(
        self, conversation_id: str, message: str
    ) -> Tuple[str, ConversationStage]:
        """Process a message and get a response"""
        # Get DealFlow instance
        dealflow = await self.client_manager.get_dealflow_instance(
            self.client_manager.conversation_sessions[conversation_id].client_id,
            conversation_id
        )
        
        # Process message through DealFlow
        response = dealflow.step(message)
        
        # Get current conversation stage
        stage = dealflow.current_conversation_stage
        
        # Update stage in session
        session = self.client_manager.conversation_sessions[conversation_id]
        session.current_stage = stage.value
        
        # Add response to conversation history
        session.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })
        
        # Update last active timestamp
        session.last_active = datetime.now()
        
        return response, session.current_stage
    
    async def stream_message(
        self, conversation_id: str, message: str
    ) -> AsyncGenerator[str, None]:
        """Stream a message response"""
        # Get DealFlow instance
        dealflow = await self.client_manager.get_dealflow_instance(
            self.client_manager.conversation_sessions[conversation_id].client_id,
            conversation_id
        )
        
        # Create a response buffer to collect the full response
        response_buffer = []
        
        # Use streaming response from DealFlow
        for chunk in dealflow.step(message, stream=True):
            # Add to buffer
            response_buffer.append(chunk)
            
            # Format as SSE
            yield f"data: {chunk}\n\n"
            
            # Small delay to simulate realistic typing speed
            await asyncio.sleep(0.01)
            
        # Combine the full response
        full_response = "".join(response_buffer)
        
        # Get current conversation stage after response
        stage = dealflow.current_conversation_stage
        
        # Update stage in session
        session = self.client_manager.conversation_sessions[conversation_id]
        session.current_stage = stage.value
        
        # Add full response to conversation history
        session.messages.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now()
        })
        
        # Update last active timestamp
        session.last_active = datetime.now()
        
        # Send end of stream
        yield "data: [DONE]\n\n"