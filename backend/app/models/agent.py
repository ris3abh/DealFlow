from pydantic import BaseModel
from typing import Optional

class AgentConfig(BaseModel):
    agent_id: str
    salesperson_name: str
    salesperson_role: str
    company_name: str
    company_business: str
    company_values: str
    conversation_purpose: str
    conversation_type: str = "chat"
    model_type: str = "GPT_4O_MINI"
    product_catalog_path: Optional[str] = None

class AgentResponse(BaseModel):
    agent_id: str
    salesperson_name: str
    status: str