"""
intelligent_crawler.py

This module provides functions to dynamically ingest product knowledge from a client's website
using LLM-guided crawling to intelligently identify and extract product/service information.
"""

import os
import json
import re
import time
import random
from collections import defaultdict, deque
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional, Tuple, Set

from camel.loaders import Firecrawl
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from dealflow.schemas.entity import Entity, EntityType
from dealflow.utils.logger import logger

class IntelligentCrawler:
    """Crawler with adaptive rate limiting and intelligent prioritization."""
    
    def __init__(
        self, 
        base_url: str, 
        model: BaseModelBackend, 
        max_pages: int = 50,
        min_delay: float = 2.0,
        cache_dir: str = "client_cache"
    ):
        """Initialize the intelligent crawler.
        
        Args:
            base_url: The base URL to crawl.
            model: The LLM model for content analysis.
            max_pages: Maximum number of pages to crawl.
            min_delay: Minimum delay between requests in seconds.
            cache_dir: Directory for caching crawled data.
        """
        self.base_url = base_url
        self.model = model
        self.max_pages = max_pages
        self.visited = set()
        self.firecrawl = Firecrawl()
        self.cache_dir = cache_dir
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Rate limiting settings
        self.rate_limits = {
            'delay': min_delay,  # Initial delay between requests
            'backoff_factor': 2.0,  # How much to increase delay after 429
            'max_delay': 60.0,  # Maximum delay
            'successes_to_decrease': 5,  # Successful requests before decreasing delay
            'success_counter': 0
        }
        
        logger.info(f"Initialized IntelligentCrawler for {base_url}")
    
    def crawl(self) -> List[Entity]:
        """Main crawl method with intelligent traversal.
        
        Returns:
            A list of extracted entities.
        """
        # Get initial links
        logger.info(f"Starting initial mapping of {self.base_url}")
        all_links = self._get_all_links(self.base_url)
        logger.info(f"Found {len(all_links)} links on domain {self.base_url}")
        
        # Prioritize using LLM
        logger.info("Prioritizing URLs using LLM analysis")
        prioritized_links = self._prioritize_urls(all_links)
        
        # Create a queue with prioritized links
        queue = deque(prioritized_links)
        entities = []
        page_count = 0
        
        logger.info(f"Starting crawl with {len(queue)} prioritized URLs")
        
        while queue and page_count < self.max_pages:
            url = queue.popleft()
            
            if url in self.visited:
                continue
                
            self.visited.add(url)
            
            # Respect rate limits with adaptive delay
            time.sleep(self.rate_limits['delay'])
            
            try:
                # Fetch page content
                logger.info(f"Fetching page: {url}")
                content = self._fetch_page(url)
                
                # Success - maybe decrease delay
                self.rate_limits['success_counter'] += 1
                if self.rate_limits['success_counter'] >= self.rate_limits['successes_to_decrease']:
                    self.rate_limits['delay'] = max(1.0, self.rate_limits['delay'] * 0.8)
                    self.rate_limits['success_counter'] = 0
                    logger.info(f"Decreased request delay to {self.rate_limits['delay']}s")
                
                # Check if content is relevant using LLM
                logger.info(f"Assessing content relevance for {url}")
                is_relevant, relevance_info = self._assess_content_relevance(content, url)
                
                if is_relevant:
                    logger.info(f"Page {url} contains relevant product/service info")
                    # Extract entity
                    entity = self._extract_entity(content, url)
                    if entity:
                        entities.append(entity)
                        logger.info(f"Extracted entity: {entity.name}")
                    
                    # If it's a listing page, find product links and add to queue
                    if relevance_info.get('type') == 'product_listing':
                        logger.info(f"Page {url} is a product listing, extracting links")
                        new_links = self._extract_product_links(content, url)
                        for link in new_links:
                            if link not in self.visited:
                                queue.appendleft(link)  # Higher priority
                                logger.info(f"Added product link to queue: {link}")
                else:
                    logger.info(f"Page {url} does not contain relevant product/service info")
                
                page_count += 1
                
            except Exception as e:
                if "429" in str(e):
                    # Rate limited - back off
                    self.rate_limits['delay'] = min(
                        self.rate_limits['max_delay'],
                        self.rate_limits['delay'] * self.rate_limits['backoff_factor']
                    )
                    logger.warning(f"Rate limited. New delay: {self.rate_limits['delay']}s")
                    
                    # Put URL back in queue to retry later
                    queue.append(url)
                    self.visited.remove(url)
                else:
                    logger.error(f"Error crawling {url}: {e}")
        
        logger.info(f"Crawl complete. Extracted {len(entities)} entities")
        return entities
    
    def _get_all_links(self, url: str) -> List[str]:
        """Get all links from the base URL.
        
        Args:
            url: The URL to get links from.
            
        Returns:
            A list of URLs found on the page.
        """
        try:
            # Use firecrawl's map_site with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    mapped = self.firecrawl.map_site(url)
                    links = mapped.get("links", [])
                    
                    # Filter links to stay on the same domain
                    base_domain = urlparse(self.base_url).netloc
                    filtered_links = [
                        link for link in links 
                        if urlparse(link).netloc == base_domain
                    ]
                    
                    return filtered_links
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        # Rate limited - exponential backoff
                        backoff_time = 2 ** attempt * 5 + random.uniform(0, 1)
                        logger.warning(f"Rate limited during mapping. Backing off for {backoff_time}s")
                        time.sleep(backoff_time)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Error getting links from {url}: {e}")
            return []
    
    def _fetch_page(self, url: str) -> str:
        """Fetch a page with error handling.
        
        Args:
            url: The URL to fetch.
            
        Returns:
            The page content as markdown.
            
        Raises:
            Exception: If the page cannot be fetched.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = self.firecrawl.crawl(url=url)
                return data["data"][0]["markdown"]
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # Rate limited - exponential backoff
                    backoff_time = 2 ** attempt * 5 + random.uniform(0, 1)
                    logger.warning(f"Rate limited during fetch. Backing off for {backoff_time}s")
                    time.sleep(backoff_time)
                else:
                    raise
    
    def _prioritize_urls(self, links: List[str]) -> List[str]:
        """Prioritize URLs based on likelihood of containing product/service info.
        
        Args:
            links: A list of URLs to prioritize.
            
        Returns:
            A prioritized list of URLs.
        """
        # Group URLs by path depth and structure
        grouped_urls = defaultdict(list)
        
        for link in links:
            # Strip the base domain and query parameters
            path = urlparse(link).path
            path_parts = path.strip('/').split('/')
            
            # Group by first directory level
            if path_parts:
                key = path_parts[0] if path_parts[0] else "root"
                grouped_urls[key].append(link)
        
        # Sample URLs from each group to analyze patterns
        samples = []
        for group, urls in grouped_urls.items():
            samples.extend(urls[:min(3, len(urls))])
        
        # If we have too many samples, limit to a reasonable number
        if len(samples) > 15:
            samples = random.sample(samples, 15)
        
        # Use LLM to identify likely product/service URL patterns
        prompt = f"""
        As a web crawler expert, analyze these URLs from {self.base_url} and identify patterns 
        for URLs that are likely to contain product or service information.
        
        URLs:
        {samples}
        
        Based only on URL structure (not content), provide JSON output with:
        1. A list of path patterns that likely contain product/service listings
        2. A list of path patterns that likely contain individual product/service details
        3. A list of path patterns to avoid (support, news, legal, etc.)
        
        Format:
        {{
          "product_listing_patterns": ["pattern1", "pattern2"],
          "product_detail_patterns": ["pattern1", "pattern2"],
          "avoid_patterns": ["pattern1", "pattern2"]
        }}
        """
        
        # Create a properly formatted message for the model
        from camel.messages import BaseMessage
        message = BaseMessage.make_user_message(
            role_name="WebCrawlExpert",
            content=prompt
        )
        
        # Get response from the model
        agent = ChatAgent(system_message="You are a web crawling expert.", model=self.model)
        response = agent.step(prompt)
        response_content = response.msg.content if hasattr(response, "msg") else str(response)
        
        # Default patterns if LLM fails
        default_patterns = {
            "product_listing_patterns": [r"/products?/", r"/services?/", r"/catalog/"],
            "product_detail_patterns": [r"/products?/.+", r"/services?/.+", r"/item/"],
            "avoid_patterns": [r"/support/", r"/news/", r"/legal/", r"/privacy/", r"/terms/", r"/login/"]
        }
        
        try:
            # Extract JSON from the response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```(?:json)?(.*?)```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                patterns = json.loads(json_str)
            else:
                # Try direct parsing if not in code blocks
                patterns = json.loads(response_content)
                
            # Validate the response has the expected keys
            if not all(k in patterns for k in ["product_listing_patterns", "product_detail_patterns", "avoid_patterns"]):
                raise ValueError("Missing required keys in LLM response")
                
        except Exception as e:
            logger.warning(f"Error parsing LLM URL patterns: {e}. Using defaults.")
            patterns = default_patterns
        
        # Apply the patterns to prioritize URLs
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for link in links:
            path = urlparse(link).path
            
            # Skip URLs that match avoid patterns
            if any(re.search(pattern, path, re.IGNORECASE) for pattern in patterns["avoid_patterns"]):
                continue
                
            # High priority: product detail pages
            if any(re.search(pattern, path, re.IGNORECASE) for pattern in patterns["product_detail_patterns"]):
                high_priority.append(link)
            # Medium priority: product listing pages
            elif any(re.search(pattern, path, re.IGNORECASE) for pattern in patterns["product_listing_patterns"]):
                medium_priority.append(link)
            # Low priority: everything else
            else:
                low_priority.append(link)
        
        # Return prioritized URLs with limits to avoid rate limiting
        result = high_priority[:20] + medium_priority[:15] + low_priority[:5]
        
        # Shuffle within priority groups to avoid hitting the same patterns repeatedly
        random.shuffle(high_priority)
        random.shuffle(medium_priority)
        random.shuffle(low_priority)
        
        logger.info(f"Prioritized URLs: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low")
        return result
    
    def _assess_content_relevance(self, content: str, url: str) -> Tuple[bool, Dict[str, Any]]:
        """Assess if page contains useful product/service information using LLM.
        
        Args:
            content: The page content.
            url: The URL of the page.
            
        Returns:
            A tuple of (is_relevant, relevance_info).
        """
        # Extract a representative sample of the content
        sample = content[:1500] + ("..." if len(content) > 1500 else "")
        
        prompt = f"""
        Analyze this web page content and determine if it contains valuable product or service information.
        
        URL: {url}
        Content sample: 
        {sample}
        
        Respond with JSON:
        {{
          "is_product_page": true/false,
          "confidence": 0-100,
          "type": "product_listing/product_detail/service/other",
          "reasoning": "brief explanation"
        }}
        """
        
        # Create a properly formatted message for the model
        from camel.messages import BaseMessage
        message = BaseMessage.make_user_message(
            role_name="ContentAnalyst",
            content=prompt
        )
        
        # Get response from the model
        response = self.model.generate_response(message)
        response_content = response.msg.content if hasattr(response, "msg") else str(response)
        
        # Default result if parsing fails
        default_result = {
            "is_product_page": False,
            "confidence": 0,
            "type": "other",
            "reasoning": "Failed to analyze content"
        }
        
        try:
            # Extract JSON from the response
            json_match = re.search(r'```(?:json)?(.*?)```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                result = json.loads(json_str)
            else:
                # Try direct parsing if not in code blocks
                result = json.loads(response_content)
                
            # Convert is_product_page to a boolean if it's a string
            if isinstance(result.get("is_product_page"), str):
                result["is_product_page"] = result["is_product_page"].lower() == "true"
                
            return result["is_product_page"], result
            
        except Exception as e:
            logger.warning(f"Error parsing content relevance: {e}")
            return False, default_result
    
    def _extract_entity(self, content: str, url: str) -> Optional[Entity]:
        """Extract structured entity information using LLM.
        
        Args:
            content: The page content.
            url: The URL of the page.
            
        Returns:
            An Entity object if extraction succeeds, None otherwise.
        """
        # Limit content to avoid token limits
        limited_content = content[:3000]
        
        prompt = f"""
        Extract structured product/service information from this web page content.
        
        URL: {url}
        
        Content:
        {limited_content}
        
        Return a JSON object with the following structure:
        {{
          "entity_type": "product/service/appointment/event/other",
          "name": "Entity name",
          "description": "Concise description",
          "price": "Price information if available, otherwise null",
          "properties": {{
            "key1": "value1",
            "key2": "value2",
            ...
          }}
        }}
        
        Extract only factual information from the page. If information is not available, use null.
        Do not hallucinate or invent details.
        """
        
        # Create a properly formatted message for the model
        from camel.messages import BaseMessage
        message = BaseMessage.make_user_message(
            role_name="EntityExtractor",
            content=prompt
        )
        
        # Get response from the model
        response = self.model.generate_response(message)
        response_content = response.msg.content if hasattr(response, "msg") else str(response)
        
        try:
            # Extract JSON from the response
            json_match = re.search(r'```(?:json)?(.*?)```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                entity_data = json.loads(json_str)
            else:
                # Try direct parsing if not in code blocks
                entity_data = json.loads(response_content)
            
            # Convert entity_type string to EntityType enum
            entity_type_str = entity_data.get("entity_type", "product").lower()
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                # Default to PRODUCT if not a valid EntityType
                entity_type = EntityType.PRODUCT
            
            # Create Entity object
            entity = Entity(
                name=entity_data.get("name", "Unknown"),
                entity_type=entity_type,
                description=entity_data.get("description", ""),
                price=entity_data.get("price"),
                properties=entity_data.get("properties", {})
            )
            return entity
            
        except Exception as e:
            logger.warning(f"Error extracting entity from {url}: {e}")
            return None
    
    def _extract_product_links(self, content: str, base_url: str) -> List[str]:
        """Extract product links from a listing page.
        
        Args:
            content: The page content.
            base_url: The base URL for resolving relative links.
            
        Returns:
            A list of product URLs.
        """
        # Extract all links using regex
        link_pattern = r'href=[\'"]?([^\'" >]+)'
        matches = re.findall(link_pattern, content)
        
        # Resolve relative URLs
        links = []
        for match in matches:
            # Skip anchor links and javascript
            if match.startswith('#') or match.startswith('javascript:'):
                continue
                
            # Resolve relative URLs
            full_url = urljoin(base_url, match)
            
            # Only keep links to the same domain
            if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                links.append(full_url)
        
        # Remove duplicates
        links = list(set(links))
        
        return links

def ingest_and_save(
    domain: str, 
    model: BaseModelBackend,
    cache_path: str = "client_cache/entities.json", 
    max_pages: int = 50
) -> List[Entity]:
    """Intelligent domain-agnostic product/service information ingestion.
    
    Args:
        domain: The domain URL to ingest.
        model: The LLM model for content analysis.
        cache_path: The cache file path.
        max_pages: Maximum number of pages to crawl.
        
    Returns:
        A list of extracted entities.
    """
    logger.info(f"Starting intelligent ingestion from {domain}")
    
    # Create cache directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    # Create intelligent crawler
    crawler = IntelligentCrawler(domain, model, max_pages=max_pages)
    
    # Run the crawl
    entities = crawler.crawl()
    
    logger.info(f"Extracted {len(entities)} entities from {domain}")
    
    # Save to cache
    save_entities_to_cache(entities, cache_path)
    logger.info(f"Saved entities to cache at {cache_path}")
    
    # Also create a text file in product catalog format for compatibility
    catalog_path = os.path.join(os.path.dirname(cache_path), "dynamic_product_catalog.txt")
    save_as_product_catalog(entities, catalog_path)
    logger.info(f"Saved product catalog at {catalog_path}")
    
    return entities

def load_cached_entities(cache_path: str = "client_cache/entities.json") -> List[Entity]:
    """Load cached entities from a JSON file.
    
    Args:
        cache_path: File path for cached entities.
    
    Returns:
        List of cached Entity objects.
    """
    if not os.path.exists(cache_path):
        return []
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Entity.from_dict(e) for e in data]

def save_entities_to_cache(entities: List[Entity], cache_path: str) -> None:
    """Save the list of entities to a cache file in JSON format.
    
    Args:
        entities: The list of Entity objects.
        cache_path: File path for caching.
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entities], f, indent=2)

def save_as_product_catalog(entities: List[Entity], catalog_path: str) -> None:
    """Save entities as a text product catalog for compatibility.
    
    Args:
        entities: The list of Entity objects.
        catalog_path: File path for the product catalog.
    """
    with open(catalog_path, "w", encoding="utf-8") as f:
        for entity in entities:
            f.write(f"Product: {entity.name}\n")
            f.write(f"Description: {entity.description}\n")
            
            if entity.price:
                f.write(f"Price: {entity.price}\n")
            
            # Write properties
            for key, value in entity.properties.items():
                # Skip empty or None values
                if value is None or value == "":
                    continue
                    
                # Format based on type
                if isinstance(value, list):
                    f.write(f"{key.capitalize()}: {', '.join(map(str, value))}\n")
                else:
                    f.write(f"{key.capitalize()}: {value}\n")
            
            # Add blank line between entities
            f.write("\n")