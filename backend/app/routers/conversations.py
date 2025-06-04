from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.conversation import MessageRequest, MessageResponse, ConversationMessage
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

@router.post("/agents/{agent_id}/chat", response_model=MessageResponse)
async def chat_with_agent(agent_id: str, message_request: MessageRequest):
    """Send a message to an agent and get a response."""
    try:
        response = agent_service.process_message(agent_id, message_request.message)
        return response
    except KeyError:
        raise HTTPException(status_code=404, detail="Agent not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/agents/{agent_id}/conversation", response_model=List[ConversationMessage])
def get_conversation(agent_id: str):
    """Get the conversation history for an agent."""
    conversation = agent_service.get_conversation(agent_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation