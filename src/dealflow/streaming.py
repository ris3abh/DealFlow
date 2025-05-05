# src/dealflow/streaming.py
"""Streaming functionality for the DealFlow sales agent."""

from typing import Generator, Optional
from dealflow.utils.logger import logger

class StreamingResponse:
    """Handles streaming responses from the sales agent."""
    
    def __init__(self, content: str):
        """Initialize a streaming response.
        
        Args:
            content: Initial content to stream.
        """
        self.content = content
        
    def __iter__(self) -> Generator[str, None, None]:
        """Yield the content as a single chunk.
        
        This basic implementation just yields the entire content as one chunk.
        A more sophisticated implementation would yield chunks as they become available.
        
        Yields:
            Chunks of the content.
        """
        yield self.content