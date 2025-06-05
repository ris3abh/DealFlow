# src/dealflow/services/firecrawl.py

import asyncio
import os
import re
import json
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from pydantic import BaseModel

try:
    from firecrawl import AsyncFirecrawlApp
except ImportError:
    raise ImportError("firecrawl-py is required. Install with: pip install firecrawl-py")

from dealflow.schemas.product import Product, ProductCatalog
from dealflow.utils.logger import logger
from dealflow.exceptions import KnowledgeBaseError

class FlexibleProductExtractor:
    """Flexible product extractor that allows custom schemas and prompts."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Firecrawl API key."""
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable required")
        
        self.app = AsyncFirecrawlApp(api_key=self.api_key)
        logger.info("FlexibleProductExtractor initialized")
    
    async def extract_with_custom_schema(
        self,
        urls: List[str],
        prompt: str,
        schema: Dict[str, Any],
        company_name: str
    ) -> Dict[str, Any]:
        """Extract using custom schema and prompt.
        
        Args:
            urls: List of URLs to extract from
            prompt: Custom extraction prompt
            schema: Pydantic model schema
            company_name: Company name for catalog
            
        Returns:
            Raw extraction response
        """
        try:
            logger.info(f"Extracting from {len(urls)} URLs with custom schema")
            logger.info(f"Prompt: {prompt[:100]}...")
            
            response = await self.app.extract(
                urls=urls,
                prompt=prompt,
                schema=schema
            )
            
            logger.info("Extraction completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise KnowledgeBaseError(f"Failed to extract: {e}")
    
    async def extract_products_simple(
        self,
        urls: List[str],
        company_name: str,
        custom_prompt: Optional[str] = None
    ) -> ProductCatalog:
        """Simple product extraction with default schema.
        
        Args:
            urls: URLs to extract from
            company_name: Company name
            custom_prompt: Optional custom prompt
            
        Returns:
            ProductCatalog with extracted products
        """
        # Default extraction schema
        class DefaultProductSchema(BaseModel):
            category: Optional[str] = None
            name: str
            description: Optional[str] = None
            price: Optional[str] = None
            product_link: Optional[str] = None
            
        class DefaultExtractionSchema(BaseModel):
            products: List[DefaultProductSchema]
        
        # Default prompt
        default_prompt = custom_prompt or """
        Extract all products and services from this website. For each product include:
        - name: Product or service name
        - description: Detailed product description
        - price: Price if available
        - category: Product category
        - product_link: Direct link to product page if available
        
        Be thorough and extract all available products/services.
        """
        
        try:
            # Extract using default schema
            response = await self.extract_with_custom_schema(
                urls=urls,
                prompt=default_prompt,
                schema=DefaultExtractionSchema.model_json_schema(),
                company_name=company_name
            )
            
            # Convert to ProductCatalog
            catalog = self._convert_to_catalog(response, company_name)
            return catalog
            
        except Exception as e:
            logger.error(f"Simple extraction failed: {e}")
            raise KnowledgeBaseError(f"Failed to extract products: {e}")
    
    def _convert_to_catalog(self, response: Any, company_name: str) -> ProductCatalog:
        """Convert extraction response to ProductCatalog."""
        try:
            products = []
            
            # Handle different response formats
            products_data = []
            if isinstance(response, list):
                for item in response:
                    if isinstance(item, dict) and 'products' in item:
                        products_data.extend(item['products'])
            elif isinstance(response, dict) and 'products' in response:
                products_data = response['products']
            
            # Convert each product
            for i, product_data in enumerate(products_data):
                try:
                    product_id = f"{self._slugify(company_name)}_{i}_{int(datetime.now().timestamp())}"
                    
                    product = Product(
                        id=product_id,
                        name=product_data.get('name', f'Product {i}'),
                        description=product_data.get('description', ''),
                        price=self._extract_price(product_data.get('price', 0)),
                        category=product_data.get('category', 'general'),
                        url=product_data.get('product_link')
                    )
                    
                    products.append(product)
                    
                except Exception as e:
                    logger.warning(f"Failed to process product {i}: {e}")
                    continue
            
            # Create catalog
            catalog_id = f"{self._slugify(company_name)}_{int(datetime.now().timestamp())}"
            catalog = ProductCatalog(
                catalog_id=catalog_id,
                company_name=company_name,
                products=products
            )
            
            logger.info(f"Created catalog with {len(products)} products")
            return catalog
            
        except Exception as e:
            logger.error(f"Failed to convert to catalog: {e}")
            raise KnowledgeBaseError(f"Failed to convert response: {e}")
    
    def _extract_price(self, price_value: Any) -> float:
        """Extract numeric price from various formats."""
        if isinstance(price_value, (int, float)):
            return float(price_value)
        
        if isinstance(price_value, str):
            # Remove currency symbols and extract number
            numbers = re.findall(r'[\d.]+', price_value.replace(',', ''))
            if numbers:
                return float(numbers[0])
        
        return 0.0
    
    def _slugify(self, text: str) -> str:
        """Create URL-friendly slug from text."""
        # Simple slugify without external dependency
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text[:30]  # Limit length

# Catalog manager for saving/loading
class CatalogManager:
    """Manage product catalog files."""
    
    def __init__(self, storage_dir: str = "catalogs/"):
        """Initialize with storage directory."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_catalog(self, catalog: ProductCatalog) -> str:
        """Save catalog to JSON file."""
        import json
        
        file_path = os.path.join(self.storage_dir, f"{catalog.catalog_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(catalog.dict(), f, indent=2, default=str)
        
        logger.info(f"Saved catalog to {file_path}")
        return file_path
    
    def load_catalog(self, catalog_id: str) -> ProductCatalog:
        """Load catalog from JSON file."""
        import json
        
        file_path = os.path.join(self.storage_dir, f"{catalog_id}.json")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return ProductCatalog(**data)