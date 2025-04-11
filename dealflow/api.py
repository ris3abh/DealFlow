# dealflow/api.py
from typing import Dict, Any, Optional, List, Union

from camel.models import BaseModelBackend

from dealflow.controller import DealFlow
from dealflow.models.adapter import ModelAdapter
from dealflow.utils.logger import logger
from dealflow.utils.timer import time_logger
from dealflow.exceptions import DealFlowError

class DealFlowAPI:
    """API interface for DealFlow."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        verbose: bool = True,
        max_turns: int = 20,
        model_platform: str = "OPENAI",
        model_type: str = "GPT_4O_MINI",
        product_catalog: Optional[str] = None,
        use_tools: bool = True,
    ):
        """Initialize the DealFlow API.
        
        Args:
            config_path: Optional path to a configuration file.
            verbose: Whether to enable verbose logging.
            max_turns: Maximum number of conversation turns.
            model_platform: The model platform to use.
            model_type: The model type to use.
            product_catalog: Optional path to a product catalog file.
            use_tools: Whether to use tools.
        """
        self.config_path = config_path
        self.verbose = verbose
        self.max_turns = max_turns
        self.current_turn = 0
        self.product_catalog = product_catalog
        self.use_tools = use_tools
        
        # Create model
        try:
            self.model = ModelAdapter.create_model(
                model_platform=model_platform,
                model_type=model_type
            )
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            raise DealFlowError(f"Failed to initialize DealFlow API: {e}")
        
        # Initialize DealFlow controller
        self.agent = self._initialize_agent()
        
        logger.info("Initialized DealFlowAPI")
    
    def _initialize_agent(self) -> DealFlow:
        """Initialize the DealFlow agent.
        
        Returns:
            Initialized DealFlow agent.
        """
        try:
            agent = DealFlow(
                model=self.model,
                config_path=self.config_path,
                product_catalog=self.product_catalog,
                use_tools=self.use_tools,
                verbose=self.verbose
            )
            
            agent.seed_agent()
            return agent
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise DealFlowError(f"Failed to initialize DealFlow agent: {e}")
    
    @time_logger
    async def do(self, human_input: Optional[str] = None) -> Dict[str, Any]:
        """Process a human input and generate a response.
        
        Args:
            human_input: Optional input from the human user.
            
        Returns:
            A dictionary containing the agent's response and metadata.
        """
        self.current_turn += 1
        
        if self.current_turn >= self.max_turns:
            logger.info("Maximum number of turns reached - ending the conversation.")
            return {
                "response": "In case you'll have any questions - just message me again!",
                "conversation_stage": "END",
                "turn": self.current_turn,
                "max_turns_reached": True
            }
        
        try:
            # Process the input
            response = self.agent.step(human_input)
            
            # Get the current conversation stage
            stage = self.agent.current_conversation_stage
            
            return {
                "response": response,
                "conversation_stage": stage.name,
                "turn": self.current_turn,
                "max_turns_reached": False
            }
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request.",
                "error": str(e),
                "turn": self.current_turn,
                "max_turns_reached": False
            }
    
    @time_logger
    async def do_stream(self, human_input: Optional[str] = None):
        """Process a human input and generate a streaming response.
        
        Args:
            human_input: Optional input from the human user.
            
        Returns:
            A generator yielding chunks of the response.
        """
        self.current_turn += 1
        
        if self.current_turn >= self.max_turns:
            logger.info("Maximum number of turns reached - ending the conversation.")
            yield "In case you'll have any questions - just message me again!"
            return
        
        try:
            # Process the input with streaming
            stream_generator = self.agent.step(human_input, stream=True)
            
            # Yield chunks from the generator
            for chunk in stream_generator:
                yield chunk
        except Exception as e:
            logger.error(f"Error processing streaming input: {e}")
            yield "I'm sorry, I encountered an error while processing your request."