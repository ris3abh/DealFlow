"""
integration.py

Integration module for connecting the intelligent crawler with DealFlow's
knowledge base systems.
"""

import os
import time
import re
from typing import List, Optional, Dict, Any, Tuple

from camel.models import BaseModelBackend
from dealflow.knowledge_base.intelligent_crawler import ingest_and_save, load_cached_entities
from dealflow.knowledge_base.retriever import EntityKnowledgeRetriever
from dealflow.schemas.entity import Entity
from dealflow.utils.logger import logger

class IntelligentKnowledgeBase:
    """Integration class for combining intelligent crawler with DealFlow."""
    
    def __init__(
        self,
        model: BaseModelBackend,
        cache_dir: str = "client_cache"
    ):
        """Initialize the intelligent knowledge base.
        
        Args:
            model: The LLM model for content analysis.
            cache_dir: Directory for caching extracted data.
        """
        self.model = model
        self.cache_dir = cache_dir
        self.retriever = None
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"Initialized IntelligentKnowledgeBase with cache directory: {cache_dir}")
    
    def load_from_domain(
        self, 
        domain_url: str,
        force_refresh: bool = False,
        max_pages: int = 50,
        cache_expiry_days: float = 7.0
    ) -> EntityKnowledgeRetriever:
        """Load knowledge base from a domain URL.
        
        This method will:
        1. Check if cached data exists and is not expired
        2. If no valid cache, crawl the domain intelligently
        3. Load the entities into a retriever
        
        Args:
            domain_url: The URL of the domain to crawl.
            force_refresh: Whether to force a refresh of the cache.
            max_pages: Maximum number of pages to crawl.
            cache_expiry_days: Number of days after which the cache expires.
            
        Returns:
            An initialized EntityKnowledgeRetriever.
        """
        # Extract domain name for file naming
        domain_name = self._extract_domain_name(domain_url)
        
        # Define cache paths
        entities_path = os.path.join(self.cache_dir, f"{domain_name}_entities.json")
        catalog_path = os.path.join(self.cache_dir, f"{domain_name}_product_catalog.txt")
        
        # Check if we need to refresh the cache
        cache_is_valid = self._is_cache_valid(entities_path, cache_expiry_days)
        
        if force_refresh or not cache_is_valid:
            logger.info(f"Cache invalid or force refresh requested. Crawling {domain_url}...")
            entities = ingest_and_save(
                domain=domain_url,
                model=self.model,
                cache_path=entities_path,
                max_pages=max_pages
            )
        else:
            logger.info(f"Loading entities from cache: {entities_path}")
            entities = load_cached_entities(entities_path)
        
        # Create and initialize retriever
        retriever = EntityKnowledgeRetriever()
        
        # If entities were successfully loaded/created, add them to the retriever
        if entities:
            logger.info(f"Adding {len(entities)} entities to retriever")
            retriever.batch_add_entities(entities)
        else:
            logger.warning(f"No entities found for {domain_url}")
        
        # Store the retriever
        self.retriever = retriever
        
        return retriever
    
    def load_from_file(self, file_path: str) -> EntityKnowledgeRetriever:
        """Load knowledge base from a file.
        
        Args:
            file_path: Path to the file containing product information.
            
        Returns:
            An initialized EntityKnowledgeRetriever.
        """
        # Create and initialize retriever
        retriever = EntityKnowledgeRetriever()
        
        # Load content from file
        logger.info(f"Loading content from file: {file_path}")
        retriever.load_from_file(file_path)
        
        # Store the retriever
        self.retriever = retriever
        
        return retriever
    
    def get_retriever(self) -> Optional[EntityKnowledgeRetriever]:
        """Get the current retriever.
        
        Returns:
            The current EntityKnowledgeRetriever, or None if not initialized.
        """
        return self.retriever
    
    def refresh_domain_data(
        self, 
        domain_url: str,
        max_pages: int = 50
    ) -> EntityKnowledgeRetriever:
        """Force refresh of domain data.
        
        Args:
            domain_url: The URL of the domain to refresh.
            max_pages: Maximum number of pages to crawl.
            
        Returns:
            An updated EntityKnowledgeRetriever.
        """
        return self.load_from_domain(
            domain_url=domain_url,
            force_refresh=True,
            max_pages=max_pages
        )
    
    def query_knowledge_base(
        self, 
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base.
        
        Args:
            query: The query string.
            top_k: Number of top results to return.
            
        Returns:
            List of results matching the query.
            
        Raises:
            ValueError: If the retriever is not initialized.
        """
        if not self.retriever:
            raise ValueError("Knowledge base not initialized. Call load_from_domain or load_from_file first.")
        
        return self.retriever.query(query, top_k=top_k)
    
    def get_all_product_names(self) -> List[str]:
        """Get all product names in the knowledge base.
        
        Returns:
            List of all product names.
            
        Raises:
            ValueError: If the retriever is not initialized.
        """
        if not self.retriever:
            raise ValueError("Knowledge base not initialized. Call load_from_domain or load_from_file first.")
        
        return self.retriever.get_all_product_names()
    
    def _extract_domain_name(self, domain_url: str) -> str:
        """Extract a clean domain name from a URL for file naming.
        
        Args:
            domain_url: The URL to extract from.
            
        Returns:
            A cleaned domain name string.
        """
        # Remove protocol and www
        domain_name = re.sub(r'https?://(www\.)?', '', domain_url.lower()).rstrip('/')
        
        # Replace non-alphanumeric characters with underscores
        domain_name = re.sub(r'[^\w]', '_', domain_name)
        
        return domain_name
    
    def _is_cache_valid(self, cache_path: str, expiry_days: float) -> bool:
        """Check if a cache file exists and is not expired.
        
        Args:
            cache_path: Path to the cache file.
            expiry_days: Number of days after which the cache expires.
            
        Returns:
            True if the cache is valid, False otherwise.
        """
        if not os.path.exists(cache_path):
            return False
        
        # Check file modification time
        mtime = os.path.getmtime(cache_path)
        age_in_days = (time.time() - mtime) / (60 * 60 * 24)
        
        return age_in_days < expiry_days


def setup_knowledge_from_domain(
    domain_url: str,
    model: BaseModelBackend,
    force_refresh: bool = False,
    max_pages: int = 50
) -> Tuple[EntityKnowledgeRetriever, str]:
    """Convenience function to setup knowledge base from a domain.
    
    Args:
        domain_url: The URL of the domain to crawl.
        model: The LLM model for content analysis.
        force_refresh: Whether to force a refresh of the cache.
        max_pages: Maximum number of pages to crawl.
        
    Returns:
        A tuple of (EntityKnowledgeRetriever, catalog_path).
    """
    kb = IntelligentKnowledgeBase(model=model)
    retriever = kb.load_from_domain(
        domain_url=domain_url,
        force_refresh=force_refresh,
        max_pages=max_pages
    )
    
    # Get the catalog path for compatibility with DealFlow
    domain_name = kb._extract_domain_name(domain_url)
    catalog_path = os.path.join(kb.cache_dir, f"{domain_name}_product_catalog.txt")
    
    return retriever, catalog_path