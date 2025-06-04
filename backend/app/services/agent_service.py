from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import traceback

# This would use the actual DealFlow in production
# For now, we'll create a simplified mock
try:
    # Try to import DealFlow and related components
    from dealflow import DealFlow
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType, ModelType
    DEALFLOW_AVAILABLE = True
except ImportError:
    # If import fails, we'll use a mock implementation
    DEALFLOW_AVAILABLE = False

class AgentService:
    def __init__(self):
        self.agents = {}  # agent_id -> agent instance
        self.conversations = {}  # agent_id -> list of messages
    
    def initialize_agent(self, config):
        """Initialize a new agent with the given configuration."""
        agent_id = config.agent_id
        
        try:
            if DEALFLOW_AVAILABLE:
                # Initialize with actual DealFlow
                model = ModelFactory.create(
                    model_platform=ModelPlatformType.OPENAI,
                    model_type=getattr(ModelType, config.model_type),
                )
                
                agent = DealFlow(
                    model=model,
                    salesperson_name=config.salesperson_name,
                    salesperson_role=config.salesperson_role,
                    company_name=config.company_name,
                    company_business=config.company_business, 
                    company_values=config.company_values,
                    conversation_purpose=config.conversation_purpose,
                    conversation_type=config.conversation_type,
                    product_catalog=config.product_catalog_path,
                    use_tools=True,
                    verbose=True
                )
                
                # Seed the agent
                agent.seed_agent()
            else:
                # Use a mock agent
                agent = MockAgent(config)
            
            # Store the agent and initialize conversation
            self.agents[agent_id] = agent
            self.conversations[agent_id] = []
            
            return True
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_agent(self, agent_id):
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self):
        """Get all active agents."""
        return self.agents
    
    def delete_agent(self, agent_id):
        """Delete an agent and its conversation."""
        if agent_id not in self.agents:
            return False
        
        # Clean up product catalog file if it exists
        agent = self.agents[agent_id]
        if hasattr(agent, 'config') and agent.config.get("product_catalog_path"):
            catalog_path = agent.config.get("product_catalog_path")
            if catalog_path and os.path.exists(catalog_path):
                try:
                    os.remove(catalog_path)
                except:
                    # Just continue if deletion fails
                    pass
        
        # Remove from dictionaries
        del self.agents[agent_id]
        if agent_id in self.conversations:
            del self.conversations[agent_id]
        
        return True
    
    def process_message(self, agent_id, message):
        """Process a message and get a response from the agent."""
        if agent_id not in self.agents:
            raise KeyError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        timestamp = datetime.now().isoformat()
        
        # Add user message to conversation
        self.conversations[agent_id].append({
            "role": "user",
            "content": message,
            "timestamp": timestamp
        })
        
        # Get response from agent
        if DEALFLOW_AVAILABLE and not isinstance(agent, MockAgent):
            # Use actual DealFlow agent
            response = agent.step(message)
        else:
            # Use mock agent
            response = agent.generate_response(message)
        
        # Add agent response to conversation
        self.conversations[agent_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": timestamp
        })
        
        return {
            "agent_id": agent_id,
            "message": response,
            "timestamp": timestamp
        }
    
    def get_conversation(self, agent_id):
        """Get the conversation history for an agent."""
        return self.conversations.get(agent_id)


class MockAgent:
    """Mock agent for when DealFlow is not available."""
    
    def __init__(self, config):
        self.config = {
            "salesperson_name": config.salesperson_name,
            "salesperson_role": config.salesperson_role,
            "company_name": config.company_name,
            "company_business": config.company_business,
            "company_values": config.company_values,
            "conversation_purpose": config.conversation_purpose,
            "product_catalog_path": config.product_catalog_path
        }
        
        # Load product catalog if available
        self.product_catalog = ""
        if config.product_catalog_path and os.path.exists(config.product_catalog_path):
            try:
                with open(config.product_catalog_path, "r", encoding="utf-8") as f:
                    self.product_catalog = f.read()
            except:
                pass
    
    def generate_response(self, message):
        """Generate a response based on the message and agent configuration."""
        message_lower = message.lower()
        name = self.config["salesperson_name"]
        company = self.config["company_name"]
        
        # Simple response logic based on message content
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return f"Hello! I'm {name}, a {self.config['salesperson_role']} at {company}. How can I help you today?"
        
        if any(word in message_lower for word in ["product", "tractor", "offer", "sell"]):
            if self.product_catalog:
                return f"We offer a variety of products at {company}. Based on your requirements, I can recommend the best options. Could you tell me more about your specific needs?"
            else:
                return f"At {company}, we offer a wide range of products. Could you tell me more about what you're looking for?"
        
        if any(word in message_lower for word in ["price", "cost", "how much", "expensive"]):
            return "Our pricing varies based on the specific model and features you need. I'd be happy to provide detailed pricing once we determine the right product for your requirements."
        
        # Default response
        return f"Thank you for your message. I'm here to help you find the right {company} product for your needs. Could you tell me more about what you're looking for?"