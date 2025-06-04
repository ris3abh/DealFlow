from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    agent_id: str
    message: str
    timestamp: str

class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str