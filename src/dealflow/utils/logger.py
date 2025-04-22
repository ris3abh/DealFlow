# dealflow/utils/logger.py

import logging
from typing import Optional

def setup_logger(name: str = "dealflow", level: int = logging.INFO) -> logging.Logger:
    """Set up a logger.
    
    Args:
        name: Name of the logger.
        level: Logging level.
        
    Returns:
        The configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handler if not already set up
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Global logger instance
logger = setup_logger()