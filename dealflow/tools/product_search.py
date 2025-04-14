# dealflow/tools/product_search.py
from typing import Dict, Any, Optional, List
from camel.toolkits import FunctionTool
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.utils.logger import logger

class ProductSearchTool:
    """Tool for searching product information."""
    
    def __init__(self, knowledge_retriever: EntityKnowledgeRetriever):
        """Initialize the product search tool.
        
        Args:
            knowledge_retriever: The knowledge retriever to use for searches.
        """
        self.knowledge_retriever = knowledge_retriever
        
        # Create the function tool by wrapping the search_products method
        self._tool = FunctionTool(self.search_products)
        
        logger.info("Initialized ProductSearchTool")
    
    def search_products(self, query: str) -> str:
        """Search for products based on a query.
        
        Args:
            query: The search query string to find products.
            
        Returns:
            str: Formatted information about matching products.
        """
        try:
            # Query the knowledge base
            results = self.knowledge_retriever.query(query)
            
            if not results:
                return "I couldn't find any products matching your query."
            
            # Format the results
            formatted_results = "Here's what I found:\n\n"
            for result in results:
                text = result.get("text", "")
                formatted_results += f"{text}\n\n"
            
            return formatted_results.strip()
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return f"I encountered an error while searching for products: {str(e)}"
    
    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._tool.get_function_name()
    
    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._tool.get_function_description() or "Search for product information in the knowledge base."
    
    def __call__(self, query: str) -> str:
        """Make the tool callable.
        
        Args:
            query: The search query.
            
        Returns:
            The search results.
        """
        return self._tool(query)