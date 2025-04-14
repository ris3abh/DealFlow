# dealflow/agents/sales_agent.py
from typing import Dict, Any, Optional, List, Union
import json

from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.messages import BaseMessage, OpenAIMessage

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
            model=model
        )
        
        logger.info(f"Initialized SalesAgent for {self.salesperson_name}")
    
    def _create_system_message(self) -> BaseMessage:
        """Create the system message for the agent.
        
        Returns:
            The system message.
        """
        stages_dict = ConversationStages.get_all_stages_as_dict()
        stages_str = "\n".join([f"{k}: {v}" for k, v in stages_dict.items()])
        
        # Choose the appropriate prompt based on whether tools are used
        if self.use_tools and self.tool_registry:
            system_content = SALES_AGENT_TOOLS_PROMPT.format(
                salesperson_name=self.config.get("salesperson_name"),
                salesperson_role=self.config.get("salesperson_role"),
                company_name=self.config.get("company_name"),
                company_business=self.config.get("company_business"),
                company_values=self.config.get("company_values"),
                conversation_purpose=self.config.get("conversation_purpose"),
                conversation_type=self.config.get("conversation_type"),
                conversation_stages=stages_str,
                conversation_history="",
                tools=self.tool_registry.format_tools_for_prompt(),
                tool_names=self.tool_registry.get_tool_names_str(),
                agent_scratchpad=""
            )
        else:
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
        
        return BaseMessage.make_system_message(
            content=system_content
        )
    
    def _handle_tool_calls(self, response_dict: Dict[str, Any]) -> str:
        """Handle tool calls in the response.
        
        Args:
            response_dict: The response dictionary containing tool calls.
            
        Returns:
            The final response after tool execution.
        """
        if "tool_calls" not in response_dict:
            return response_dict.get("content", "")
        
        tools = self.tool_registry.get_tools()
        tools_dict = {tool.name: tool for tool in tools}
        
        # Initialize response parts with any content that came before tool calls
        response_parts = [response_dict.get("content", "")]
        
        # Process each tool call
        for tool_call in response_dict.get("tool_calls", []):
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            
            if tool_name in tools_dict:
                tool = tools_dict[tool_name]
                
                # Execute the tool with the provided arguments
                if "query" in tool_args:
                    tool_result = tool(tool_args["query"])
                else:
                    # If no query parameter, pass the first value as input
                    first_arg = next(iter(tool_args.values()), "")
                    tool_result = tool(first_arg)
                
                # Add the observation to the response
                response_parts.append(f"Observation: {tool_result}")
            else:
                response_parts.append(f"Error: Tool '{tool_name}' not found")
        
        # Generate a final response based on tool execution results
        final_prompt = BaseMessage.make_user_message(
            role_name="User",
            content=f"Based on the following information, provide a helpful response to the customer:\n\n{' '.join(response_parts)}"
        )
        
        final_response = self.agent.step(final_prompt)
        
        if hasattr(final_response, "msg"):
            return final_response.msg.content
        return str(final_response)
    
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
        
        # Prepare user message with conversation history
        user_message = BaseMessage.make_user_message(
            role_name="User",
            content=f"Current conversation stage: {conversation_stage.name}\n\nConversation history:\n{conversation_history}\n\nPlease continue the conversation based on the history and current stage."
        )
        
        # Get response from the agent
        response = self.agent.step(user_message)
        
        # Process the response
        if hasattr(response, "msg"):
            if hasattr(response.msg, "content_dict") and self.use_tools and self.tool_registry:
                # Handle tool calls if present
                content = self._handle_tool_calls(response.msg.content_dict)
            else:
                content = response.msg.content
        else:
            content = str(response)
        
        # Clean up the response
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