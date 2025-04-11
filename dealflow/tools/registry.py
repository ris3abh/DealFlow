# dealflow/tools/registry.py
from typing import List, Dict, Any, Optional
from camel.toolkits import FunctionTool as Tool
from dealflow.tools.product_search import ProductSearchTool
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.utils.logger import logger

class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self, knowledge_retriever: Optional[EntityKnowledgeRetriever] = None):
        """Initialize the tool registry.
        
        Args:
            knowledge_retriever: Optional knowledge retriever for product search.
        """
        self.tools = []
        self.knowledge_retriever = knowledge_retriever
        
        # Register default tools
        self._register_default_tools()
        
        logger.info(f"Initialized ToolRegistry with {len(self.tools)} tools")
    
    def _register_default_tools(self):
        """Register default tools."""
        # Add product search tool if knowledge retriever is available
        if self.knowledge_retriever:
            self.register_tool(ProductSearchTool(self.knowledge_retriever))
    
    def register_tool(self, tool: Tool):
        """Register a tool.
        
        Args:
            tool: The tool to register.
        """
        self.tools.append(tool)
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tools(self) -> List[Tool]:
        """Get all registered tools.
        
        Returns:
            A list of registered tools.
        """
        return self.tools
    
    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: The name of the tool.
            
        Returns:
            The tool if found, None otherwise.
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tool_names(self) -> List[str]:
        """Get the names of all registered tools.
        
        Returns:
            A list of tool names.
        """
        return [tool.name for tool in self.tools]
    
    def get_tool_names_str(self) -> str:
        """Get a comma-separated string of tool names.
        
        Returns:
            A comma-separated string of tool names.
        """
        return ", ".join(self.get_tool_names())
    
    def format_tools_for_prompt(self) -> str:
        """Format tools for inclusion in a prompt.
        
        Returns:
            A formatted string of tools.
        """
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])