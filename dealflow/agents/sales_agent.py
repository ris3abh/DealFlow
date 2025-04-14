# dealflow/agents/sales_agent.py
from typing import Dict, Any, Optional, List, Union, Set
import json
import re

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
        
        # Track known products from searches
        self.known_products: Set[str] = set()
        self.last_tool_results: Dict[str, Any] = {}
        
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
        
        return system_content

    def _extract_product_names_from_response(self, text: str) -> List[str]:
        """Extract product names from a response text.
        
        Args:
            text: The text to extract product names from.
            
        Returns:
            List of extracted product names.
        """
        # Look for quoted product names
        quoted_products = re.findall(r'"([^"]*)"', text)
        
        # Also look for product names with specific patterns
        pattern_products = re.findall(r'(?:our|the)\s+([A-Z][a-zA-Z\s-]+(?:Mattress|Pillow|Blanket|Sheet|Base))', text)
        
        # Combine and remove duplicates
        all_products = quoted_products + pattern_products
        return list(set(all_products))

    def _verify_products_in_response(self, response: str) -> bool:
        """Verify that products mentioned in the response exist in known products.
        
        Args:
            response: The response to verify.
            
        Returns:
            True if all mentioned products are known, False otherwise.
        """
        if not self.known_products:
            # If we haven't searched for products yet, we can't verify
            return True
            
        mentioned_products = self._extract_product_names_from_response(response)
        
        # Check if any mentioned products are not in known products
        for product in mentioned_products:
            product_exists = False
            for known_product in self.known_products:
                # Do fuzzy matching to account for slight variations
                if product.lower() in known_product.lower() or known_product.lower() in product.lower():
                    product_exists = True
                    break
                    
            if not product_exists:
                logger.warning(f"Product '{product}' mentioned but not found in catalog")
                return False
                
        return True
    
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
                
                # Update known products if this is a product search
                if tool_name == "search_products":
                    # Extract product names from the search result
                    product_names = self._extract_product_names_from_tool_result(tool_result)
                    self.known_products.update(product_names)
                    # Store the result for future reference
                    self.last_tool_results[tool_name] = tool_result
                
                # Add the observation to the response
                response_parts.append(f"Observation: {tool_result}")
            else:
                response_parts.append(f"Error: Tool '{tool_name}' not found")
        
        # Generate a final response based on tool execution results
        # Add explicit instructions to use only products from the catalog
        instruction = ""
        if "search_products" in self.last_tool_results:
            instruction = f"Based on the product search results above, ONLY mention products that were found in our catalog. Do NOT invent or hallucinate product names. The products available are: {', '.join(self.known_products)}. Provide a helpful response to the customer using ONLY this information."
        else:
            instruction = "Provide a helpful response to the customer based on the information above."
            
        final_prompt = BaseMessage.make_user_message(
            role_name="User",
            content=f"{' '.join(response_parts)}\n\n{instruction}"
        )
        
        final_response = self.agent.step(final_prompt)
        
        if hasattr(final_response, "msg"):
            return final_response.msg.content
        return str(final_response)
    
    def _extract_product_names_from_tool_result(self, tool_result: str) -> List[str]:
        """Extract product names from a tool result.
        
        Args:
            tool_result: The tool result to extract product names from.
            
        Returns:
            List of extracted product names.
        """
        # For now, let's use a simple pattern matching for product names
        # This could be improved with more sophisticated NLP techniques
        product_patterns = [
            r'Product: ([^\n]+)',  # Match "Product: Name"
            r'([A-Z][a-zA-Z\s-]+(?:Mattress|Pillow|Blanket|Sheet|Base))'  # Match CamelCase product names
        ]
        
        product_names = []
        for pattern in product_patterns:
            matches = re.findall(pattern, tool_result)
            product_names.extend(matches)
        
        # Clean up the product names
        product_names = [name.strip() for name in product_names if name.strip()]
        
        logger.info(f"Extracted product names: {product_names}")
        return product_names
    
    def _ensure_product_fidelity(self, response: str) -> str:
        """Ensure that the response only mentions products from the catalog.
        
        Args:
            response: The agent's response.
            
        Returns:
            Updated response that only mentions products from the catalog.
        """
        if not self.known_products:
            # No known products to check against
            return response
            
        # Extract potential product names from the response
        mentioned_products = self._extract_product_names_from_response(response)
        
        # Check each mentioned product
        for product in mentioned_products:
            product_exists = False
            for known_product in self.known_products:
                # Do fuzzy matching to account for slight variations
                if product.lower() in known_product.lower() or known_product.lower() in product.lower():
                    # Replace the mention with the exact known product name
                    response = response.replace(product, known_product)
                    product_exists = True
                    break
            
            if not product_exists:
                # Replace the unknown product with a generic reference
                logger.warning(f"Replacing unknown product '{product}' in response")
                response = response.replace(product, "one of our premium mattresses")
        
        return response
    
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
        
        # Ensure product fidelity
        content = self._ensure_product_fidelity(content)
        
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