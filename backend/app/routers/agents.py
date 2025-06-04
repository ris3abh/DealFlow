from fastapi import APIRouter, File, Form, UploadFile, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Optional, Any
import uuid
import os
import tempfile
from app.models.agent import AgentConfig, AgentResponse
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

@router.post("/create", response_model=AgentResponse)
async def create_agent(
    background_tasks: BackgroundTasks,
    salesperson_name: str = Form(...),
    salesperson_role: str = Form(...),
    company_name: str = Form(...),
    company_business: str = Form(...),
    company_values: str = Form(...),
    conversation_purpose: str = Form(...),
    conversation_type: str = Form("chat"),
    model_type: str = Form("GPT_4O_MINI"),
    product_catalog: Optional[UploadFile] = File(None)
):
    """Create a new sales agent with the provided configuration."""
    try:
        # Generate a unique ID for the agent
        agent_id = str(uuid.uuid4())
        
        # Save product catalog if provided
        catalog_path = None
        if product_catalog:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            catalog_path = os.path.join(temp_dir, f"catalog_{agent_id}.txt")
            
            # Save file content
            content = await product_catalog.read()
            with open(catalog_path, "wb") as f:
                f.write(content)
        
        # Create agent config
        config = AgentConfig(
            agent_id=agent_id,
            salesperson_name=salesperson_name,
            salesperson_role=salesperson_role,
            company_name=company_name,
            company_business=company_business,
            company_values=company_values,
            conversation_purpose=conversation_purpose,
            conversation_type=conversation_type,
            model_type=model_type,
            product_catalog_path=catalog_path
        )
        
        # Initialize agent in background
        background_tasks.add_task(agent_service.initialize_agent, config)
        
        return AgentResponse(
            agent_id=agent_id,
            salesperson_name=salesperson_name,
            status="initializing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str):
    """Get agent details by ID."""
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        agent_id=agent_id,
        salesperson_name=agent.config.get("salesperson_name", "Unknown"),
        status="active"
    )

@router.get("/", response_model=List[AgentResponse])
def list_agents():
    """Get a list of all active agents."""
    agents = agent_service.list_agents()
    return [
        AgentResponse(
            agent_id=agent_id,
            salesperson_name=agent.config.get("salesperson_name", "Unknown"),
            status="active"
        )
        for agent_id, agent in agents.items()
    ]

@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Delete an agent by ID."""
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "success", "message": f"Agent {agent_id} deleted"}