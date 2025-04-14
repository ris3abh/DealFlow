"""
crawler_ingestor.py

This module provides functions to dynamically ingest product knowledge from a client’s website using Firecrawl,
parse the content into Entity objects (using the DealFlow Entity schema), and cache the results for
one-time ingestion per client.
"""

import os
import json
import re
from typing import List

from camel.loaders import Firecrawl
from dealflow.schemas.entity import Entity, EntityType

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

def scrape_pages(links: List[str]) -> List[str]:
    """
    Scrape content from each link as markdown.
    
    Args:
        links (List[str]): A list of URLs to scrape.
    
    Returns:
        List[str]: A list of markdown strings scraped from the pages.
    """
    firecrawl = Firecrawl()
    pages = []
    for link in links:
        try:
            data = firecrawl.crawl(url=link)
            markdown = data["data"][0]["markdown"]
            pages.append(markdown)
        except Exception as e:
            print(f"Failed to scrape {link}: {e}")
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
        # Extract product name using a simple 'Product:' marker.
        match = re.search(r'Product:\s*(.+)', md, re.IGNORECASE)
        name = match.group(1).strip() if match else "Unknown Product"

        # Extract description from the second paragraph, if available.
        paragraphs = [p.strip() for p in md.split("\n\n") if p.strip()]
        description = paragraphs[1] if len(paragraphs) > 1 else "No description available."

        # Extract price: search for a line containing "Price:" followed by a number.
        price_match = re.search(r'Price:\s*\$?([\d,]+\.\d+|[\d,]+)', md, re.IGNORECASE)
        if price_match:
            try:
                price = float(price_match.group(1).replace(',', ''))
            except Exception:
                price = None
        else:
            price = None

        # For simplicity, assume every parsed entry is a PRODUCT.
        entity = Entity(
            name=name,
            entity_type=EntityType.PRODUCT,
            description=description,
            price=price
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

def ingest_and_save(domain: str, cache_path: str = "client_cache/entities.json") -> List[Entity]:
    """
    Perform the complete ingestion:
      1. Map the domain to extract URLs.
      2. Scrape each page to get markdown content.
      3. Parse the markdown into Entity objects.
      4. Cache the parsed entities.
    
    Args:
        domain (str): The domain URL to ingest.
        cache_path (str): The cache file path.
    
    Returns:
        List[Entity]: The list of parsed Entity objects.
    """
    print("Starting ingestion from domain:", domain)
    links = crawl_website(domain)
    print(f"Found {len(links)} links on domain {domain}")
    markdown_list = scrape_pages(links)
    print(f"Scraped {len(markdown_list)} pages")
    entities = parse_markdown_to_entities(markdown_list)
    print(f"Parsed {len(entities)} entities")
    save_entities_to_cache(entities, cache_path)
    print(f"Saved entities to cache at {cache_path}")
    return entities
