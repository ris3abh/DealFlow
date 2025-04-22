from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
import uuid
from datetime import datetime
import asyncio

from api.models.schemas import (
    ConversationRequest, 
    ConversationResponse, 
    ConversationSession,
    Message
)
from api.core.client_manager import get_client_manager, ClientManager
from api.services.conversation_service import ConversationService

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    client_manager: ClientManager = Depends(get_client_manager)
):
    """Start a new conversation"""
    # Check if client exists
    client = await client_manager.get_client(request.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {request.client_id} not found"
        )
    
    # Create conversation ID
    conversation_id = str(uuid.uuid4())
    
    # Initialize DealFlow instance
    dealflow = await client_manager.get_dealflow_instance(
        request.client_id, conversation_id
    )
    
    # Create conversation service
    conversation_service = ConversationService(client_manager)
    
    # Process initial message if provided
    if request.message:
        # Add message to session
        session = client_manager.conversation_sessions[conversation_id]
        session.messages.append(
            Message(role="user", content=request.message)
        )
        session.last_active = datetime.now()
        
        # Process message
        response, stage = await conversation_service.process_message(
            conversation_id, request.message
        )
        
        # Return response
        return ConversationResponse(
            id=conversation_id,
            message=response,
            stage=stage
        )
    else:
        # Just return the new conversation ID with empty message
        return ConversationResponse(
            id=conversation_id,
            message="",
            stage=client_manager.conversation_sessions[conversation_id].current_stage
        )

@router.post("/{conversation_id}", response_model=ConversationResponse)
async def continue_conversation(
    conversation_id: str,
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    client_manager: ClientManager = Depends(get_client_manager)
):
    """Continue an existing conversation"""
    # Check if conversation exists
    if conversation_id not in client_manager.conversation_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Check if client matches
    session = client_manager.conversation_sessions[conversation_id]
    if session.client_id != request.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client ID does not match conversation owner"
        )
    
    # Create conversation service
    conversation_service = ConversationService(client_manager)
    
    # Add message to session
    session.messages.append(
        Message(role="user", content=request.message)
    )
    session.last_active = datetime.now()
    
    # Process message
    response, stage = await conversation_service.process_message(
        conversation_id, request.message
    )
    
    # Return response
    return ConversationResponse(
        id=conversation_id,
        message=response,
        stage=stage
    )

@router.post("/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    request: ConversationRequest,
    client_manager: ClientManager = Depends(get_client_manager)
):
    """Stream a conversation response"""
    # Check if conversation exists
    if conversation_id not in client_manager.conversation_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Check if client matches
    session = client_manager.conversation_sessions[conversation_id]
    if session.client_id != request.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client ID does not match conversation owner"
        )
    
    # Create conversation service
    conversation_service = ConversationService(client_manager)
    
    # Add message to session
    session.messages.append(
        Message(role="user", content=request.message)
    )
    session.last_active = datetime.now()
    
    # Stream response
    return StreamingResponse(
        conversation_service.stream_message(conversation_id, request.message),
        media_type="text/event-stream"
    )

@router.get("/{conversation_id}", response_model=ConversationSession)
async def get_conversation(
    conversation_id: str,
    client_id: str,
    client_manager: ClientManager = Depends(get_client_manager)
):
    """Get conversation details"""
    # Check if conversation exists
    if conversation_id not in client_manager.conversation_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Check if client matches
    session = client_manager.conversation_sessions[conversation_id]
    if session.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client ID does not match conversation owner"
        )
    
    return session

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_conversation(
    conversation_id: str,
    client_id: str,
    client_manager: ClientManager = Depends(get_client_manager)
):
    """End a conversation"""
    # Check if conversation exists
    if conversation_id not in client_manager.conversation_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Check if client matches
    session = client_manager.conversation_sessions[conversation_id]
    if session.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client ID does not match conversation owner"
        )
    
    # Clean up resources
    if conversation_id in client_manager.active_dealflow_instances:
        del client_manager.active_dealflow_instances[conversation_id]
    del client_manager.conversation_sessions[conversation_id]
    
    # Here you would archive the conversation in your database
    
    return None