# dealflow/agents/stage_analyzer.py
from typing import Optional, Dict, Any

from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.messages import BaseMessage

from dealflow.prompts.stage import STAGE_ANALYZER_PROMPT
from dealflow.stages.conversation import ConversationStages
from dealflow.utils.logger import logger
from dealflow.utils.timer import time_logger

class StageAnalyzer:
    """Analyzer for determining the current conversation stage."""
    
    def __init__(self, model: BaseModelBackend):
        """Initialize the stage analyzer.
        
        Args:
            model: The model backend to use.
        """
        self.model = model
        
        # Initialize the CAMEL chat agent
        system_message = BaseMessage.make_assistant_message(
            role_name="StageAnalyzer",
            content="You are a sales stage analyzer helping to determine the appropriate conversation stage."
        )
        
        self.agent = ChatAgent(
            system_message=system_message,
            model=model
        )
        
        logger.info("Initialized StageAnalyzer")
    
    @time_logger
    def analyze(
        self, 
        conversation_history: str,
        current_stage_id: str
    ) -> str:
        """Analyze the conversation history to determine the appropriate stage.
        
        Args:
            conversation_history: The conversation history.
            current_stage_id: The current conversation stage ID.
            
        Returns:
            The determined conversation stage ID.
        """
        # Format the prompt
        stages_dict = ConversationStages.get_all_stages_as_dict()
        stages_str = "\n".join([f"{k}: {v}" for k, v in stages_dict.items()])
        
        prompt = STAGE_ANALYZER_PROMPT.format(
            conversation_history=conversation_history,
            conversation_stage_id=current_stage_id,
            conversation_stages=stages_str
        )
        
        # Create user message
        user_message = BaseMessage.make_user_message(
            role_name="User",
            content=prompt
        )
        
        # Get response from the agent
        response = self.agent.step(user_message)
        
        # Extract the stage ID from the response
        if hasattr(response, "msg"):
            stage_id = response.msg.content.strip()
        else:
            stage_id = str(response).strip()
        
        # Validate the stage ID
        if not stage_id.isdigit() or stage_id not in stages_dict:
            logger.warning(f"Invalid stage ID: {stage_id}, using current stage")
            return current_stage_id
        
        logger.info(f"Analyzed stage: {stage_id}")
        return stage_id