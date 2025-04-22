# dealflow/controller.py
from typing import List, Dict, Any, Optional, Union

from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.messages import BaseMessage

from dealflow.agents.sales_agent import SalesAgent
from dealflow.agents.stage_analyzer import StageAnalyzer
from dealflow.config.loader import ConfigLoader
from dealflow.memory.conversation import ConversationMemory
from dealflow.tools.registry import ToolRegistry
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.exceptions import DealFlowError
from dealflow.utils.logger import logger
from dealflow.utils.timer import time_logger
from dealflow.stages.conversation import ConversationStage, ConversationStages

class DealFlow:
    """Main controller class for the DealFlow sales agent."""
    
    def __init__(
        self,
        model: BaseModelBackend,
        config_path: Optional[str] = None,
        salesperson_name: Optional[str] = None,
        salesperson_role: Optional[str] = None,
        company_name: Optional[str] = None,
        company_business: Optional[str] = None,
        company_values: Optional[str] = None,
        conversation_purpose: Optional[str] = None,
        conversation_type: Optional[str] = None,
        use_tools: bool = True,
        product_catalog: Optional[str] = None,
        verbose: bool = False,
    ):
        """Initialize the DealFlow controller.
        
        Args:
            model: The model backend to use.
            config_path: Optional path to a configuration file.
            salesperson_name: Name of the salesperson.
            salesperson_role: Role of the salesperson.
            company_name: Name of the company.
            company_business: Business description of the company.
            company_values: Values of the company.
            conversation_purpose: Purpose of the conversation.
            conversation_type: Type of the conversation (e.g., "call", "chat").
            use_tools: Whether to use tools.
            product_catalog: Path to a product catalog file.
            verbose: Whether to enable verbose logging.
        """
        # Load configuration
        self.config = ConfigLoader.create_config(
            config_path,
            salesperson_name=salesperson_name,
            salesperson_role=salesperson_role,
            company_name=company_name,
            company_business=company_business,
            company_values=company_values,
            conversation_purpose=conversation_purpose,
            conversation_type=conversation_type,
            use_tools=use_tools,
        )
        
        self.model = model
        self.verbose = verbose
        self.use_tools = self.config.get("use_tools", True)
        self.product_catalog_path = product_catalog
        
        # Initialize memory
        self.memory = ConversationMemory()
        
        # Initialize knowledge base if product catalog is provided
        self.knowledge_retriever = None
        if product_catalog:
            self.knowledge_retriever = EntityKnowledgeRetriever()
            self.knowledge_retriever.load_from_file(product_catalog)
        
        # Initialize tool registry if tools are enabled
        self.tool_registry = None
        if self.use_tools and self.knowledge_retriever:
            self.tool_registry = ToolRegistry(knowledge_retriever=self.knowledge_retriever)
        
        # Initialize stage analyzer
        self.stage_analyzer = StageAnalyzer(model=self.model)
        
        # Initialize sales agent
        self.sales_agent = SalesAgent(
            model=self.model,
            config=self.config,
            memory=self.memory,
            stage_analyzer=self.stage_analyzer,
            tool_registry=self.tool_registry,
            verbose=self.verbose
        )
        
        # Current conversation stage
        self.current_conversation_stage = ConversationStage.INTRODUCTION
        
        logger.info(f"Initialized DealFlow with {model.__class__.__name__}")
        
        # Debug: Log all known product names
        if self.knowledge_retriever:
            product_names = self.knowledge_retriever.get_all_product_names()
            if product_names:
                logger.info(f"Loaded product catalog with {len(product_names)} products: {', '.join(product_names)}")
    
    @time_logger
    def seed_agent(self):
        """Seed the agent with initial configuration."""
        self.memory.clear()
        self.current_conversation_stage = ConversationStage.INTRODUCTION
        logger.info("Agent seeded and ready for conversation")
    
    @time_logger
    def determine_conversation_stage(self):
        """Determine the current conversation stage."""
        conversation_history = self.memory.get_conversation_history()
        stage_id = self.stage_analyzer.analyze(
            conversation_history=conversation_history,
            current_stage_id=self.current_conversation_stage.value
        )
        
        new_stage = ConversationStages.get_stage_by_id(stage_id)
        if new_stage:
            self.current_conversation_stage = new_stage
        
        logger.info(f"Conversation stage determined: {self.current_conversation_stage.name}")
        return self.current_conversation_stage
    
    @time_logger
    def step(self, human_input: Optional[str] = None, stream: bool = False):
        """Execute one step of the conversation.
        
        Args:
            human_input: Optional input from the human user.
            stream: Whether to stream the response.
            
        Returns:
            The agent's response.
        """
        # Add human input to memory if provided
        if human_input:
            self.memory.add_user_message(human_input)
        
        # Determine conversation stage
        self.determine_conversation_stage()
        
        # Generate agent response
        if stream:
            return self.sales_agent.streaming_step(
                conversation_stage=self.current_conversation_stage
            )
        else:
            response = self.sales_agent.step(
                conversation_stage=self.current_conversation_stage
            )
            
            # Add agent response to memory
            self.memory.add_assistant_message(
                response,
                role_name=self.config.get("salesperson_name")
            )
            
            return response
    
    def reload_product_catalog(self, product_catalog: Optional[str] = None):
        """Reload the product catalog.
        
        Args:
            product_catalog: Optional path to a product catalog file. If None, uses the original path.
        """
        catalog_path = product_catalog or self.product_catalog_path
        if not catalog_path:
            logger.warning("No product catalog path provided for reload")
            return
            
        if self.knowledge_retriever:
            # Clear existing knowledge
            self.knowledge_retriever.clear()
            # Load new catalog
            self.knowledge_retriever.load_from_file(catalog_path)
            
            # Log known products
            product_names = self.knowledge_retriever.get_all_product_names()
            logger.info(f"Reloaded product catalog with {len(product_names)} products")
        else:
            logger.warning("Knowledge retriever not initialized, cannot reload catalog")