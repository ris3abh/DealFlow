"""
crawler_ingestor.py

This module provides functions to dynamically ingest product knowledge from a client's website
and manage the crawling process. This is the original crawler module, which has been enhanced
by the intelligent_crawler.py module.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

from camel.loaders import Firecrawl
from dealflow.schemas.entity import Entity, EntityType
from dealflow.utils.logger import logger

def crawl_website(url: str) -> List[str]:
    """
    Map the given domain to extract all URLs.
    
    Args:
        url (str): The target domain URL.
    
    Returns:
        List[str]: A list of URLs discovered on the domain.
    """
    firecrawl = Firecrawl()
    mapped = firecrawl.map_site(url)
    links = mapped.get("links", [])
    return links

def scrape_pages(links: List[str], rate_limit_delay: float = 2.0) -> List[str]:
    """
    Scrape content from each link as markdown with rate limiting.
    
    Args:
        links (List[str]): A list of URLs to scrape.
        rate_limit_delay (float): Delay between requests in seconds.
    
    Returns:
        List[str]: A list of markdown strings scraped from the pages.
    """
    import time
    import random
    
    firecrawl = Firecrawl()
    pages = []
    
    for link in links:
        try:
            # Respect rate limits with adaptive delay
            time.sleep(rate_limit_delay)
            
            # Attempt to crawl the page
            data = firecrawl.crawl(url=link)
            markdown = data["data"][0]["markdown"]
            pages.append(markdown)
            
            # Add a small random delay for better rate limit management
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.error(f"Failed to scrape {link}: {e}")
    
    return pages

def parse_markdown_to_entities(markdown_list: List[str]) -> List[Entity]:
    """
    Convert a list of markdown strings into a list of Entity objects.
    
    This uses basic regex rules to identify:
    - The product name (using a "Product:" prefix)
    - A description (using the first paragraph after the title)
    - A price (searching for 'Price:' followed by a number)
    
    Args:
        markdown_list (List[str]): List of markdown contents.
    
    Returns:
        List[Entity]: List of parsed Entity objects.
    """
    entities = []
    for md in markdown_list:
        # Extract product name using a simple 'Product:' marker or heading pattern
        name_patterns = [
            r'Product:\s*(.+)',  # Product: Name
            r'^#\s+(.+)',  # Markdown heading
            r'<h[1-3][^>]*>([^<]+)</h[1-3]>'  # HTML heading
        ]
        
        name = "Unknown Product"
        for pattern in name_patterns:
            match = re.search(pattern, md, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                break

        # Extract description from paragraphs
        paragraphs = [p.strip() for p in md.split("\n\n") if p.strip()]
        description = paragraphs[1] if len(paragraphs) > 1 else "No description available."

        # Extract price: search for a line containing "Price:" followed by a number
        price_match = re.search(r'Price:\s*\$?([\d,]+\.\d+|[\d,]+)', md, re.IGNORECASE)
        if price_match:
            try:
                price = float(price_match.group(1).replace(',', ''))
            except Exception:
                price = None
        else:
            price = None
        
        # Extract properties (key-value pairs)
        properties = {}
        property_pattern = r'([A-Za-z ]+):\s*([^:\n]+)'
        for match in re.finditer(property_pattern, md):
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            
            # Skip if this is the product name or description or price
            if key in ['product', 'description', 'price']:
                continue
                
            properties[key] = value

        # For simplicity, assume every parsed entry is a PRODUCT.
        entity = Entity(
            name=name,
            entity_type=EntityType.PRODUCT,
            description=description,
            price=price,
            properties=properties
        )
        entities.append(entity)
    
    return entities

def save_entities_to_cache(entities: List[Entity], cache_path: str = "client_cache/entities.json") -> None:
    """
    Save the list of entities to a cache file in JSON format.
    
    Args:
        entities (List[Entity]): The list of Entity objects.
        cache_path (str): File path for caching.
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entities], f, indent=2)

def load_cached_entities(cache_path: str = "client_cache/entities.json") -> List[Entity]:
    """
    Load cached entities from a JSON file.
    
    Args:
        cache_path (str): File path for cached entities.
    
    Returns:
        List[Entity]: List of cached Entity objects.
    """
    if not os.path.exists(cache_path):
        return []
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Entity.from_dict(e) for e in data]

def ingest_and_save(
    domain: str, 
    cache_path: str = "client_cache/entities.json",
    max_links: int = 50,
    rate_limit_delay: float = 2.0
) -> List[Entity]:
    """
    Perform the complete ingestion:
      1. Map the domain to extract URLs.
      2. Scrape each page to get markdown content.
      3. Parse the markdown into Entity objects.
      4. Cache the parsed entities.
    
    Args:
        domain (str): The domain URL to ingest.
        cache_path (str): The cache file path.
        max_links (int): Maximum number of links to process.
        rate_limit_delay (float): Delay between requests in seconds.
    
    Returns:
        List[Entity]: The list of parsed Entity objects.
    """
    logger.info(f"Starting ingestion from domain: {domain}")
    links = crawl_website(domain)
    logger.info(f"Found {len(links)} links on domain {domain}")
    
    # Limit the number of links to process
    if len(links) > max_links:
        import random
        links = random.sample(links, max_links)
        logger.info(f"Limited to {max_links} random links")
    
    markdown_list = scrape_pages(links, rate_limit_delay)
    logger.info(f"Scraped {len(markdown_list)} pages")
    
    entities = parse_markdown_to_entities(markdown_list)
    logger.info(f"Parsed {len(entities)} entities")
    
    save_entities_to_cache(entities, cache_path)
    logger.info(f"Saved entities to cache at {cache_path}")
    
    return entities