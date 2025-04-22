# dealflow/exceptions.py

class DealFlowError(Exception):
    """Base exception for all DealFlow errors."""
    pass

class ConfigurationError(DealFlowError):
    """Exception raised for configuration errors."""
    pass

class ModelError(DealFlowError):
    """Exception raised for model-related errors."""
    pass

class AgentError(DealFlowError):
    """Exception raised for agent-related errors."""
    pass

class ToolError(DealFlowError):
    """Exception raised for tool-related errors."""
    pass

class MemoryError(DealFlowError):
    """Exception raised for memory-related errors."""
    pass

class KnowledgeBaseError(DealFlowError):
    """Exception raised for knowledge base-related errors."""
    pass