# dealflow/knowledge_base/loader.py
import os
import json
import re
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, time

from dealflow.exceptions import KnowledgeBaseError
from dealflow.utils.logger import logger
from dealflow.schemas.entity import Entity, EntityType

class EntityKnowledgeLoader:
    """Loader for entity knowledge."""
    
    @staticmethod
    def load_from_text(file_path: str) -> str:
        """Load entity knowledge from a text file.
        
        Args:
            file_path: Path to the text file.
            
        Returns:
            The content of the text file.
            
        Raises:
            KnowledgeBaseError: If the file doesn't exist or is invalid.
        """
        if not os.path.exists(file_path):
            raise KnowledgeBaseError(f"File {file_path} not found.")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            raise KnowledgeBaseError(f"Error loading file {file_path}: {e}")
    
    @staticmethod
    def parse_product_catalog(content: str) -> List[Entity]:
        """Parse product catalog text into structured entity data.
        
        Args:
            content: The product catalog text.
            
        Returns:
            A list of Entity objects representing products.
        """
        entities = []
        current_entity = {}
        entity_type = EntityType.PRODUCT
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                if current_entity and 'name' in current_entity:
                    # Create an Entity object
                    entity = Entity(
                        name=current_entity.get('name', 'Unknown'),
                        entity_type=entity_type,
                        description=current_entity.get('description', ''),
                        price=current_entity.get('price'),
                        properties={
                            'sizes': current_entity.get('sizes', []),
                            **{k: v for k, v in current_entity.items() if k not in ['name', 'description', 'price', 'sizes']}
                        }
                    )
                    entities.append(entity)
                    current_entity = {}
                continue
                
            if line.startswith("Product") or "product" in line.lower():
                if current_entity and 'name' in current_entity:
                    # Create an Entity object
                    entity = Entity(
                        name=current_entity.get('name', 'Unknown'),
                        entity_type=entity_type,
                        description=current_entity.get('description', ''),
                        price=current_entity.get('price'),
                        properties={
                            'sizes': current_entity.get('sizes', []),
                            **{k: v for k, v in current_entity.items() if k not in ['name', 'description', 'price', 'sizes']}
                        }
                    )
                    entities.append(entity)
                    
                current_entity = {"name": line.split(":", 1)[1].strip() if ":" in line else line}
            elif "description" in line.lower() and ":" in line:
                current_entity["description"] = line.split(":", 1)[1].strip()
            elif "price" in line.lower():
                price_str = line.split(":", 1)[1].strip() if ":" in line else line
                # Extract numeric price value
                price_value = re.findall(r'[\d,]+\.\d+|\d+', price_str)
                if price_value:
                    current_entity["price"] = float(price_value[0].replace(',', ''))
                else:
                    current_entity["price"] = price_str
            elif "size" in line.lower() or "available" in line.lower():
                size_str = line.split(":", 1)[1].strip() if ":" in line else line
                sizes = [s.strip() for s in size_str.split(",")]
                current_entity["sizes"] = sizes
            else:
                # Handle other properties
                if ":" in line:
                    key, value = line.split(":", 1)
                    current_entity[key.strip().lower()] = value.strip()
        
        # Add the last entity if it exists
        if current_entity and 'name' in current_entity:
            entity = Entity(
                name=current_entity.get('name', 'Unknown'),
                entity_type=entity_type,
                description=current_entity.get('description', ''),
                price=current_entity.get('price'),
                properties={
                    'sizes': current_entity.get('sizes', []),
                    **{k: v for k, v in current_entity.items() if k not in ['name', 'description', 'price', 'sizes']}
                }
            )
            entities.append(entity)
            
        return entities
    
    @staticmethod
    def parse_appointment_catalog(content: str) -> List[Entity]:
        """Parse appointment catalog text into structured entity data.
        
        Args:
            content: The appointment catalog text.
            
        Returns:
            A list of Entity objects representing appointments.
        """
        entities = []
        current_entity = {}
        entity_type = EntityType.APPOINTMENT
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                if current_entity and 'name' in current_entity:
                    # Create an Entity object
                    entity = Entity(
                        name=current_entity.get('name', 'Unknown'),
                        entity_type=entity_type,
                        description=current_entity.get('description', ''),
                        price=current_entity.get('price'),
                        availability=current_entity.get('availability', {}),
                        properties={k: v for k, v in current_entity.items() 
                                   if k not in ['name', 'description', 'price', 'availability']}
                    )
                    entities.append(entity)
                    current_entity = {}
                continue
                
            if line.startswith("Appointment") or "appointment" in line.lower() or "service" in line.lower():
                if current_entity and 'name' in current_entity:
                    # Create an Entity object
                    entity = Entity(
                        name=current_entity.get('name', 'Unknown'),
                        entity_type=entity_type,
                        description=current_entity.get('description', ''),
                        price=current_entity.get('price'),
                        availability=current_entity.get('availability', {}),
                        properties={k: v for k, v in current_entity.items() 
                                   if k not in ['name', 'description', 'price', 'availability']}
                    )
                    entities.append(entity)
                    
                current_entity = {"name": line.split(":", 1)[1].strip() if ":" in line else line}
            elif "description" in line.lower() and ":" in line:
                current_entity["description"] = line.split(":", 1)[1].strip()
            elif "price" in line.lower():
                price_str = line.split(":", 1)[1].strip() if ":" in line else line
                # Extract numeric price value
                price_value = re.findall(r'[\d,]+\.\d+|\d+', price_str)
                if price_value:
                    current_entity["price"] = float(price_value[0].replace(',', ''))
                else:
                    current_entity["price"] = price_str
            elif "availability" in line.lower() or "hours" in line.lower() or "schedule" in line.lower():
                availability_str = line.split(":", 1)[1].strip() if ":" in line else line
                # Parse availability information (this is a simplified example)
                current_entity["availability"] = {
                    "text": availability_str
                }
            elif "duration" in line.lower():
                duration_str = line.split(":", 1)[1].strip() if ":" in line else line
                current_entity["duration"] = duration_str
            else:
                # Handle other properties
                if ":" in line:
                    key, value = line.split(":", 1)
                    current_entity[key.strip().lower()] = value.strip()
        
        # Add the last entity if it exists
        if current_entity and 'name' in current_entity:
            entity = Entity(
                name=current_entity.get('name', 'Unknown'),
                entity_type=entity_type,
                description=current_entity.get('description', ''),
                price=current_entity.get('price'),
                availability=current_entity.get('availability', {}),
                properties={k: v for k, v in current_entity.items() 
                           if k not in ['name', 'description', 'price', 'availability']}
            )
            entities.append(entity)
            
        return entities
    
    @staticmethod
    def load_entities_from_json(file_path: str) -> List[Entity]:
        """Load entities from a JSON file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            A list of Entity objects.
            
        Raises:
            KnowledgeBaseError: If the file doesn't exist or is invalid.
        """
        if not os.path.exists(file_path):
            raise KnowledgeBaseError(f"File {file_path} not found.")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            entities = []
            
            # Check if it's a list of entities or a single entity
            if isinstance(data, list):
                for item in data:
                    entities.append(Entity.from_dict(item))
            else:
                entities.append(Entity.from_dict(data))
                
            return entities
        except Exception as e:
            logger.error(f"Error loading entities from {file_path}: {e}")
            raise KnowledgeBaseError(f"Error loading entities from {file_path}: {e}")
    
    @staticmethod
    def load_price_mapping(file_path: str) -> Dict[str, str]:
        """Load entity price mapping from a JSON file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            A dictionary mapping entity names to price IDs.
            
        Raises:
            KnowledgeBaseError: If the file doesn't exist or is invalid.
        """
        if not os.path.exists(file_path):
            raise KnowledgeBaseError(f"File {file_path} not found.")
        
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            return mapping
        except Exception as e:
            logger.error(f"Error loading price mapping file {file_path}: {e}")
            raise KnowledgeBaseError(f"Error loading price mapping file {file_path}: {e}")