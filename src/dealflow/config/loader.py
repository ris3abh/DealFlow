# dealflow/config/loader.py
import json
import os
from typing import Dict, Any, Optional

from dealflow.config.default import DefaultConfig
from dealflow.exceptions import ConfigurationError

class ConfigLoader:
    """Configuration loader for DealFlow."""
    
    @staticmethod
    def load_from_json(config_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file.
        
        Args:
            config_path: Path to the JSON configuration file.
            
        Returns:
            A dictionary with the configuration.
            
        Raises:
            ConfigurationError: If the configuration file doesn't exist or is invalid.
        """
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file {config_path} not found.")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Error decoding JSON from {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration from {config_path}: {e}")
    
    @classmethod
    def create_config(cls, config_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a configuration by merging default config with provided config.
        
        Args:
            config_path: Optional path to a JSON configuration file.
            **kwargs: Additional configuration parameters.
            
        Returns:
            A dictionary with the merged configuration.
        """
        # Start with default configuration
        config = DefaultConfig.get_default_agent_config()
        
        # Update with JSON configuration if provided
        if config_path:
            json_config = cls.load_from_json(config_path)
            config.update(json_config)
        
        # Update with kwargs
        config.update({k: v for k, v in kwargs.items() if v is not None})
        
        return config