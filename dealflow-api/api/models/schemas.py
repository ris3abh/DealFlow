from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Client schemas
class ClientConfig(BaseModel):
    """Client configuration schema"""
    salesperson_name: str = "Ted Lasso"
    salesperson_role: str = "Sales Representative"
    company_name: str = "Sleep Haven"
    company_business: str = "Premium mattress company"
    company_values: str = "Quality sleep is essential to health and well-being"
    conversation_purpose: str = "Find out customer sleep needs and recommend products"
    conversation_type: str = "chat"
    use_tools: bool = True
    product_catalog_path: Optional[str] = None
    model_platform: Optional[str] = None
    model_type: Optional[str] = None
    temperature: Optional[float] = 0.7
    verbose: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "salesperson_name": "Ted Lasso",
                "salesperson_role": "Sleep Consultant",
                "company_name": "Sleep Haven",
                "company_business": "Premium mattress company providing comfortable sleep solutions",
                "company_values": "Quality sleep is essential to health and well-being",
                "conversation_purpose": "Find out customer sleep needs and recommend products",
                "conversation_type": "chat",
                "use_tools": True,
                "product_catalog_path": "catalogs/sleep_haven_products.txt",
                "model_platform": "OPENAI",
                "model_type": "GPT_4O_MINI",
                "temperature": 0.7,
                "verbose": False
            }
        }

class ClientResponse(BaseModel):
    """Client response schema"""
    id: str
    config: ClientConfig
    created_at: datetime
    active_conversations: int = 0

# Conversation schemas
class ConversationStage(str, Enum):
    """Conversation stage enum"""
    INTRODUCTION = "1"
    QUALIFICATION = "2"
    VALUE_PROPOSITION = "3"
    NEEDS_ANALYSIS = "4"
    SOLUTION_PRESENTATION = "5"
    OBJECTION_HANDLING = "6"
    CLOSE = "7"
    END_CONVERSATION = "8"

class Message(BaseModel):
    """Message schema"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationSession(BaseModel):
    """Conversation session schema"""
    id: str
    client_id: str
    created_at: datetime
    last_active: datetime
    messages: List[Message] = []
    current_stage: ConversationStage = ConversationStage.INTRODUCTION
    metadata: Dict[str, Any] = {}

class ConversationRequest(BaseModel):
    """Conversation request schema"""
    client_id: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Hi, I'm looking for a new mattress."
            }
        }

class ConversationResponse(BaseModel):
    """Conversation response schema"""
    id: str
    message: str
    stage: ConversationStage
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Hello! Welcome to Sleep Haven. I'd be happy to help you find a mattress that meets your needs. What kind of mattress are you currently using, and what are you looking for in a new one?",
                "stage": "1"
            }
        }

# Usage schemas
class ClientUsage(BaseModel):
    """Client usage schema"""
    client_id: str
    total_conversations: int
    total_messages: int
    average_conversation_length: float
    average_response_time: float

class SystemUsage(BaseModel):
    """System usage schema"""
    total_clients: int
    active_clients: int
    total_conversations: int
    active_conversations: int
    average_response_time: float