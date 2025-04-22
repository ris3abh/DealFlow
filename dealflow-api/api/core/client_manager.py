from typing import Dict, Optional, Any
import asyncio
from datetime import datetime
import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from dealflow.controller import DealFlow
from dealflow.models.adapter import ModelAdapter
from api.core.config import settings
from api.models.schemas import ClientConfig, ConversationSession

class ClientManager:
    """Manages DealFlow instances and configurations for multiple clients"""
    
    def __init__(self):
        self.clients: Dict[str, ClientConfig] = {}
        self.active_dealflow_instances: Dict[str, DealFlow] = {}
        self.conversation_sessions: Dict[str, ConversationSession] = {}
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the client manager"""
        # Load clients from database
        # This is a placeholder - implement with your ORM
        pass
    
    async def cleanup(self):
        """Clean up resources on shutdown"""
        self.active_dealflow_instances.clear()
        self.conversation_sessions.clear()
    
    async def register_client(self, client_config: ClientConfig) -> str:
        """Register a new client"""
        async with self.lock:
            client_id = str(uuid.uuid4())
            self.clients[client_id] = client_config
            return client_id
    
    async def get_client(self, client_id: str) -> Optional[ClientConfig]:
        """Get client configuration by ID"""
        return self.clients.get(client_id)
    
    async def update_client(self, client_id: str, client_config: ClientConfig) -> bool:
        """Update client configuration"""
        if client_id not in self.clients:
            return False
        
        async with self.lock:
            self.clients[client_id] = client_config
            
            # Update any active DealFlow instances for this client
            active_conversations = [
                conv_id for conv_id, session in self.conversation_sessions.items()
                if session.client_id == client_id
            ]
            
            for conv_id in active_conversations:
                if conv_id in self.active_dealflow_instances:
                    # Create a new instance with updated config
                    await self.get_dealflow_instance(client_id, conv_id, force_refresh=True)
            
            return True
    
    async def delete_client(self, client_id: str) -> bool:
        """Delete a client"""
        if client_id not in self.clients:
            return False
        
        async with self.lock:
            # Clean up any active instances
            active_conversations = [
                conv_id for conv_id, session in self.conversation_sessions.items()
                if session.client_id == client_id
            ]
            
            for conv_id in active_conversations:
                if conv_id in self.active_dealflow_instances:
                    del self.active_dealflow_instances[conv_id]
                del self.conversation_sessions[conv_id]
            
            del self.clients[client_id]
            return True
    
    async def get_dealflow_instance(
        self, client_id: str, conversation_id: str, force_refresh: bool = False
    ) -> DealFlow:
        """Get a DealFlow instance for a specific client and conversation"""
        if client_id not in self.clients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        # Check if we already have an instance for this conversation
        if not force_refresh and conversation_id in self.active_dealflow_instances:
            return self.active_dealflow_instances[conversation_id]
        
        # Create a new DealFlow instance with the client's configuration
        client_config = self.clients[client_id]
        
        # Create model instance
        model = ModelAdapter.create_model(
            model_platform=client_config.model_platform or settings.DEFAULT_MODEL_PLATFORM,
            model_type=client_config.model_type or settings.DEFAULT_MODEL_TYPE,
            temperature=client_config.temperature or 0.7
        )
        
        # Create DealFlow instance
        dealflow = DealFlow(
            model=model,
            salesperson_name=client_config.salesperson_name,
            salesperson_role=client_config.salesperson_role,
            company_name=client_config.company_name,
            company_business=client_config.company_business,
            company_values=client_config.company_values,
            conversation_purpose=client_config.conversation_purpose,
            conversation_type=client_config.conversation_type,
            use_tools=client_config.use_tools,
            product_catalog=client_config.product_catalog_path,
            verbose=client_config.verbose
        )
        
        # Seed the agent
        dealflow.seed_agent()
        
        # Store the instance
        async with self.lock:
            self.active_dealflow_instances[conversation_id] = dealflow
            
            # Create or update conversation session
            if conversation_id not in self.conversation_sessions:
                self.conversation_sessions[conversation_id] = ConversationSession(
                    id=conversation_id,
                    client_id=client_id,
                    created_at=datetime.now(),
                    last_active=datetime.now(),
                    messages=[]
                )
            else:
                self.conversation_sessions[conversation_id].last_active = datetime.now()
        
        return dealflow
    
    async def cleanup_inactive_conversations(self):
        """Clean up inactive conversation sessions"""
        now = datetime.now()
        timeout_seconds = settings.CONVERSATION_TIMEOUT_MINUTES * 60
        
        async with self.lock:
            inactive_conversations = [
                conv_id for conv_id, session in self.conversation_sessions.items()
                if (now - session.last_active).total_seconds() > timeout_seconds
            ]
            
            for conv_id in inactive_conversations:
                if conv_id in self.active_dealflow_instances:
                    del self.active_dealflow_instances[conv_id]
                del self.conversation_sessions[conv_id]

# Singleton instance
_client_manager = ClientManager()

def get_client_manager():
    """Get the global client manager instance"""
    return _client_manager