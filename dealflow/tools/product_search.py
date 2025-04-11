# dealflow/tools/product_search.py
from typing import Dict, Any, Optional
from camel.toolkits import FunctionTool as Tool
from dealflow.tools.product_search import ProductSearchTool
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.utils.logger import logger
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.utils.logger import logger

class ProductSearchTool(Tool):
    """Tool for searching product information."""
    
    def __init__(self, knowledge_retriever: EntityKnowledgeRetriever):
        """Initialize the product search tool.
        
        Args:
            knowledge_retriever: The knowledge retriever to use for searches.
        """
        self.knowledge_retriever = knowledge_retriever
        
        # Initialize the Tool superclass
        super().__init__(
            name="ProductSearch",
            func=self.search_products,
            description="Useful for when you need to answer questions about product information or services offered, availability and their costs."
        )
        
        logger.info("Initialized ProductSearchTool")
    
    def search_products(self, query: str) -> str:
        """Search for products based on a query.
        
        Args:
            query: The search query.
            
        Returns:
            Formatted information about matching products.
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