from fastapi import APIRouter, File, Form, UploadFile, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Optional, Any
import uuid
import os
import tempfile
from app.models.agent import AgentConfig, AgentResponse
from app.services.agent_service import agent_service

router = APIRouter()

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
            # Create temp file with unique name
            temp_dir = tempfile.gettempdir()
            filename = f"{agent_id}_{product_catalog.filename}"
            catalog_path = os.path.join(temp_dir, filename)
            
            # Save file content
            content = await product_catalog.read()
            with open(catalog_path, "wb") as f:
                f.write(content)
            
            print(f"Saved catalog to: {catalog_path}")
        
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
        print(f"Error in create_agent: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str):
    """Get agent details by ID."""
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Handle both real DealFlow agents and mock agents
    if hasattr(agent, 'config') and hasattr(agent.config, 'get'):
        salesperson_name = agent.config.get("salesperson_name", "Unknown")
    elif hasattr(agent, 'config') and isinstance(agent.config, dict):
        salesperson_name = agent.config.get("salesperson_name", "Unknown")
    else:
        salesperson_name = "Unknown"
    
    return AgentResponse(
        agent_id=agent_id,
        salesperson_name=salesperson_name,
        status="active"
    )

@router.get("/", response_model=List[AgentResponse])
def list_agents():
    """Get a list of all active agents."""
    agents = agent_service.list_agents()
    result = []
    
    for agent_id, agent in agents.items():
        # Handle both real DealFlow agents and mock agents
        if hasattr(agent, 'config') and hasattr(agent.config, 'get'):
            salesperson_name = agent.config.get("salesperson_name", "Unknown")
        elif hasattr(agent, 'config') and isinstance(agent.config, dict):
            salesperson_name = agent.config.get("salesperson_name", "Unknown")
        else:
            salesperson_name = "Unknown"
            
        result.append(AgentResponse(
            agent_id=agent_id,
            salesperson_name=salesperson_name,
            status="active"
        ))
    
    return result

@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Delete an agent by ID."""
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "success", "message": f"Agent {agent_id} deleted"}