# dealflow/utils/timer.py

import time
import functools
from typing import Callable, Any

from dealflow.utils.logger import logger

def time_logger(func: Callable) -> Callable:
    """Decorator to log the execution time of a function.
    
    Args:
        func: The function to be decorated.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper