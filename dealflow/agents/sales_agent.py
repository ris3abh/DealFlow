# dealflow/agents/sales_agent.py
from typing import Dict, Any, Optional, List, Union

from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.messages import BaseMessage

from dealflow.prompts.sales import SALES_AGENT_PROMPT, SALES_AGENT_TOOLS_PROMPT
from dealflow.stages.conversation import ConversationStage, ConversationStages
from dealflow.memory.conversation import ConversationMemory
from dealflow.agents.stage_analyzer import StageAnalyzer
from dealflow.tools.registry import ToolRegistry
from dealflow.utils.logger import logger
from dealflow.utils.timer import time_logger

class SalesAgent:
    """Agent for conducting sales conversations."""
    
    def __init__(
        self,
        model: BaseModelBackend,
        config: Dict[str, Any],
        memory: ConversationMemory,
        stage_analyzer: StageAnalyzer,
        tool_registry: Optional[ToolRegistry] = None,
        verbose: bool = False,
    ):
        """Initialize the sales agent.
        
        Args:
            model: The model backend to use.
            config: Agent configuration.
            memory: Conversation memory.
            stage_analyzer: Stage analyzer.
            tool_registry: Optional tool registry.
            verbose: Whether to enable verbose logging.
        """
        self.model = model
        self.config = config
        self.memory = memory
        self.stage_analyzer = stage_analyzer
        self.tool_registry = tool_registry
        self.verbose = verbose
        
        self.salesperson_name = config.get("salesperson_name")
        self.use_tools = config.get("use_tools", False)
        
        # Initialize the CAMEL chat agent
        system_message = self._create_system_message()
        self.agent = ChatAgent(
            system_message=system_message,
            model=model,
            verbose=verbose
        )
        
        logger.info(f"Initialized SalesAgent for {self.salesperson_name}")
    
    def _create_system_message(self) -> BaseMessage:
        """Create the system message for the agent.
        
        Returns:
            The system message.
        """
        stages_dict = ConversationStages.get_all_stages_as_dict()
        stages_str = "\n".join([f"{k}: {v}" for k, v in stages_dict.items()])
        
        system_content = SALES_AGENT_PROMPT.format(
            salesperson_name=self.config.get("salesperson_name"),
            salesperson_role=self.config.get("salesperson_role"),
            company_name=self.config.get("company_name"),
            company_business=self.config.get("company_business"),
            company_values=self.config.get("company_values"),
            conversation_purpose=self.config.get("conversation_purpose"),
            conversation_type=self.config.get("conversation_type"),
            conversation_stages=stages_str,
            conversation_history=""
        )
        
        return BaseMessage.make_assistant_message(
            role_name=self.config.get("salesperson_name"),
            content=system_content
        )
    
    @time_logger
    def step(self, conversation_stage: ConversationStage) -> str:
        """Generate the next response in the conversation.
        
        Args:
            conversation_stage: The current conversation stage.
            
        Returns:
            The agent's response.
        """
        # Get conversation history
        conversation_history = self.memory.get_conversation_history()
        
        # Create the user message with updated context
        stages_dict = ConversationStages.get_all_stages_as_dict()
        stages_str = "\n".join([f"{k}: {v}" for k, v in stages_dict.items()])
        
        if self.use_tools and self.tool_registry:
            # Use tools prompt template
            user_content = SALES_AGENT_TOOLS_PROMPT.format(
                salesperson_name=self.config.get("salesperson_name"),
                salesperson_role=self.config.get("salesperson_role"),
                company_name=self.config.get("company_name"),
                company_business=self.config.get("company_business"),
                company_values=self.config.get("company_values"),
                conversation_purpose=self.config.get("conversation_purpose"),
                conversation_type=self.config.get("conversation_type"),
                conversation_stages=stages_str,
                conversation_history=conversation_history,
                tools=self.tool_registry.format_tools_for_prompt(),
                tool_names=self.tool_registry.get_tool_names_str(),
                agent_scratchpad=""
            )
            
            # Use tools to generate response (this is simplified)
            tools = self.tool_registry.get_tools()
            response = self.agent.step_with_tools(user_content, tools)
        else:
            # Use standard prompt template
            user_content = SALES_AGENT_PROMPT.format(
                salesperson_name=self.config.get("salesperson_name"),
                salesperson_role=self.config.get("salesperson_role"),
                company_name=self.config.get("company_name"),
                company_business=self.config.get("company_business"),
                company_values=self.config.get("company_values"),
                conversation_purpose=self.config.get("conversation_purpose"),
                conversation_type=self.config.get("conversation_type"),
                conversation_stages=stages_str,
                conversation_history=conversation_history
            )
            
            user_message = BaseMessage.make_user_message(
                role_name="User",
                content=user_content
            )
            
            # Generate response
            response = self.agent.step(user_message)
        
        # Extract the content from the response
        if hasattr(response, "msg"):
            content = response.msg.content
        else:
            content = str(response)
        
        # Process the response
        content = content.replace("<END_OF_TURN>", "").strip()
        
        if self.verbose:
            logger.info(f"Generated response: {content}")
        
        return content
    
    @time_logger
    def streaming_step(self, conversation_stage: ConversationStage):
        """Generate the next response in the conversation with streaming.
        
        Args:
            conversation_stage: The current conversation stage.
            
        Returns:
            A generator yielding chunks of the response.
        """
        # Implementation for streaming would go here
        # For now, we'll return a simple generator that yields the full response
        response = self.step(conversation_stage)
        yield response