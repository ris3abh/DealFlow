from typing import Dict, List, Optional, Any
import os
import re
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
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentService, cls).__new__(cls)
            cls._instance.agents = {}  # agent_id -> agent instance
            cls._instance.conversations = {}  # agent_id -> list of messages
        return cls._instance
    
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
            
            print(f"Successfully initialized agent {agent_id}")
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
        if hasattr(agent, 'config') and hasattr(agent.config, 'get'):
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
    
    def _clean_agent_response(self, response: str) -> str:
        """Clean the agent response to remove internal reasoning."""
        if not response:
            return ""
        
        # Remove the internal reasoning pattern (Thought, Action, Observation)
        # Look for the pattern and extract only the final response
        
        # Pattern 1: Extract text after the agent name
        agent_name_pattern = r'([A-Za-z\s]+):\s*(.*?)$'
        match = re.search(agent_name_pattern, response, re.DOTALL)
        if match:
            agent_response = match.group(2).strip()
            # If this looks like a clean response (no "Thought:" or "Action:"), use it
            if not any(keyword in agent_response for keyword in ["Thought:", "Action:", "Observation:"]):
                return agent_response
        
        # Pattern 2: Extract everything after the last occurrence of agent name
        lines = response.split('\n')
        agent_response_lines = []
        found_agent_response = False
        
        for line in lines:
            # Look for lines that start with an agent name followed by a colon
            if ':' in line and not any(keyword in line for keyword in ["Thought:", "Action:", "Observation:"]):
                # This might be the agent's response
                parts = line.split(':', 1)
                if len(parts) == 2 and not parts[0].strip() in ["Thought", "Action", "Observation"]:
                    agent_response_lines = [parts[1].strip()]
                    found_agent_response = True
                    continue
            
            # If we found the agent response, keep collecting lines
            if found_agent_response:
                agent_response_lines.append(line.strip())
        
        if agent_response_lines:
            cleaned_response = '\n'.join(agent_response_lines).strip()
            if cleaned_response and not any(keyword in cleaned_response for keyword in ["Thought:", "Action:", "Observation:"]):
                return cleaned_response
        
        # Pattern 3: If response contains reasoning patterns, extract the final answer
        if any(keyword in response for keyword in ["Thought:", "Action:", "Observation:"]):
            # Try to find the final response after all the reasoning
            parts = response.split("Observation:")
            if len(parts) > 1:
                # Get everything after the last observation
                final_part = parts[-1].strip()
                
                # Look for agent name in the final part
                agent_lines = final_part.split('\n')
                for line in agent_lines:
                    if ':' in line and not any(keyword in line for keyword in ["Thought", "Action", "Observation"]):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        
        # Fallback: Return the original response if we can't clean it
        # But remove any obvious reasoning patterns
        cleaned = response
        for pattern in [r'Thought:.*?(?=Action:|$)', r'Action:.*?(?=Action Input:|$)', r'Action Input:.*?(?=Observation:|$)', r'Observation:.*?(?=[A-Za-z\s]+:|$)']:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        return cleaned.strip()
    
    def process_message(self, agent_id, message):
        """Process a message and get a response from the agent."""
        if agent_id not in self.agents:
            print(f"Agent {agent_id} not found in agents: {list(self.agents.keys())}")
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
            raw_response = agent.step(message)
            
            # Clean the response to remove internal reasoning
            response = self._clean_agent_response(raw_response)
            
            # If cleaning resulted in empty response, provide fallback
            if not response or len(response.strip()) < 10:
                response = f"Thank you for your question. I'm here to help you find the right Yanmar product for your needs. Could you tell me more about your specific requirements?"
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
        
        # Enhanced response logic with product catalog integration
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return f"Hello! I'm {name}, a {self.config['salesperson_role']} at {company}. How can I help you today?"
        
        if any(word in message_lower for word in ["product", "tractor", "offer", "sell", "recommend", "brush", "terrain", "farming"]):
            if self.product_catalog:
                # Try to extract relevant products from catalog
                if "brush" in message_lower or "terrain" in message_lower:
                    return f"Based on your needs for brush clearing and uneven terrain work, I'd recommend looking at our YT347 or YM346 tractors. The YT347 offers 47 horsepower and is designed for properties of 25 acres or more, while the YM346 provides 46 horsepower with great versatility. Both would handle your light farming and property maintenance tasks well. Would you like me to provide more details about either of these models?"
                else:
                    return f"We offer a variety of Yanmar tractors at {company}. Based on your requirements, I can recommend the best options. Could you tell me more about your specific needs - such as property size and what tasks you'll be performing?"
            else:
                return f"At {company}, we offer a wide range of products. Could you tell me more about what you're looking for?"
        
        if any(word in message_lower for word in ["price", "cost", "how much", "expensive"]):
            return "Our pricing varies based on the specific model and features you need. For example, our YT347 is priced at $40,000, while our YM346 is $37,000. I'd be happy to provide detailed pricing once we determine the right product for your requirements."
        
        if any(word in message_lower for word in ["reliable", "longevity", "last", "durable"]):
            return f"Absolutely! {company} tractors are renowned for their reliability and longevity. Our diesel engines are built to last, and we use high-quality materials throughout. Many of our customers have tractors that have been running strong for decades with proper maintenance."
        
        # Default response
        return f"Thank you for your message. I'm here to help you find the right {company} product for your needs. Could you tell me more about what you're looking for?"


# Create a global instance
agent_service = AgentService()