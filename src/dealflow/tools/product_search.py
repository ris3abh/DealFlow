# dealflow/tools/product_search.py
from typing import Dict, Any, Optional, List
import re
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
                return "I couldn't find any products matching your query in our catalog."
            
            # Format the results
            formatted_results = "Here's what I found in our product catalog:\n\n"
            
            # Track product names for clarity
            product_names = []
            
            for result in results:
                text = result.get("text", "")
                
                # Try to extract product name for better formatting
                product_name = self._extract_product_name(text)
                if product_name:
                    product_names.append(product_name)
                
                formatted_results += f"{text}\n\n"
            
            # Add a summary of available products
            if product_names:
                formatted_results += f"Available products: {', '.join(product_names)}"
            
            return formatted_results.strip()
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return f"I encountered an error while searching for products: {str(e)}"
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        """Extract a product name from text.
        
        Args:
            text: The text to extract a product name from.
            
        Returns:
            The extracted product name, or None if no product name was found.
        """
        # Try different patterns to extract a product name
        patterns = [
            r'^Product:?\s*([^\n]+)',  # Product: Name at start of text
            r'^([A-Z][a-zA-Z\s-]+(?:Mattress|Pillow|Blanket|Sheet|Base))',  # CamelCase product name at start
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._tool.get_function_name()
    
    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return (self._tool.get_function_description() or 
                "Search for product information in our catalog. ALWAYS use this tool BEFORE mentioning specific products to ensure they exist in our catalog.")
    
    def __call__(self, query: str) -> str:
        """Make the tool callable.
        
        Args:
            query: The search query.
            
        Returns:
            The search results.
        """
        logger.info(f"ProductSearchTool called with query: {query}")
        result = self._tool(query)
        logger.info(f"ProductSearchTool result length: {len(result) if result else 0}")
        return result