# dealflow/schemas/entity.py
from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class EntityType(Enum):
    """Types of entities that can be sold or booked."""
    PRODUCT = "product"
    SERVICE = "service"
    APPOINTMENT = "appointment"
    PROPERTY = "property"
    EVENT = "event"
    CUSTOM = "custom"

@dataclass
class Entity:
    """Schema for a generic sales entity (product, service, appointment, etc.)."""
    
    name: str
    entity_type: EntityType
    description: str
    price: Optional[Union[float, str]] = None
    availability: Optional[Dict[str, Any]] = None  # For appointments/showings
    properties: Dict[str, Any] = field(default_factory=dict)  # Flexible properties
    external_id: Optional[str] = None  # For integrations (stripe, calendar, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "entity_type": self.entity_type.value,
            "description": self.description,
            "price": self.price,
            "availability": self.availability,
            "properties": self.properties,
            "external_id": self.external_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create an Entity from a dictionary."""
        return cls(
            name=data.get("name", ""),
            entity_type=EntityType(data.get("entity_type", "custom")),
            description=data.get("description", ""),
            price=data.get("price"),
            availability=data.get("availability"),
            properties=data.get("properties", {}),
            external_id=data.get("external_id"),
            metadata=data.get("metadata", {}),
        )
    
    def format_for_display(self) -> str:
        """Format the entity information for display."""
        result = f"{self.entity_type.value.capitalize()}: {self.name}\n"
        result += f"Description: {self.description}\n"
        
        if self.price:
            result += f"Price: {self.price}\n"
        
        if self.availability:
            result += "Availability: "
            if isinstance(self.availability, dict):
                for key, value in self.availability.items():
                    result += f"{key}: {value}, "
                result = result.rstrip(", ") + "\n"
            else:
                result += f"{self.availability}\n"
        
        for key, value in self.properties.items():
            if isinstance(value, list):
                result += f"{key.capitalize()}: {', '.join(map(str, value))}\n"
            else:
                result += f"{key.capitalize()}: {value}\n"
        
        return result