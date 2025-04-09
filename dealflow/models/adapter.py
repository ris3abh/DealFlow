# dealflow/models/adapter.py
from typing import Optional, Dict, Any

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from dealflow.exceptions import ModelError
from dealflow.utils.logger import logger

class ModelAdapter:
    """Adapter for CAMEL models."""
    
    @staticmethod
    def create_model(
        model_platform: str = "OPENAI",
        model_type: str = "GPT_4O_MINI",
        temperature: float = 0.7,
        model_config_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Create a CAMEL model.
        
        Args:
            model_platform: The model platform type (e.g., "OPENAI", "ANTHROPIC").
            model_type: The model type (e.g., "GPT_4O_MINI", "CLAUDE_3_OPUS").
            temperature: The temperature for the model.
            model_config_dict: Additional model configuration parameters.
            **kwargs: Additional arguments for model creation.
            
        Returns:
            A CAMEL model instance.
            
        Raises:
            ModelError: If the model creation fails.
        """
        try:
            # Convert string platform type to enum
            platform_type = getattr(ModelPlatformType, model_platform.upper())
            
            # Convert string model type to enum
            model_enum_type = getattr(ModelType, model_type.upper())
            
            # Default config with temperature
            config = {"temperature": temperature}
            
            # Update with provided config
            if model_config_dict:
                config.update(model_config_dict)
            
            logger.info(f"Creating model with platform={platform_type}, type={model_enum_type}")
            
            # Create the model
            model = ModelFactory.create(
                model_platform=platform_type,
                model_type=model_enum_type,
                model_config_dict=config,
                **kwargs
            )
            
            return model
            
        except AttributeError as e:
            raise ModelError(f"Invalid model platform or type: {e}")
        except Exception as e:
            raise ModelError(f"Error creating model: {e}")