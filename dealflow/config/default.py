# dealflow/config/default.py
from typing import Dict, Any, Optional

class DefaultConfig:
    """Default configuration for DealFlow."""
    
    # Model configuration
    DEFAULT_MODEL_PLATFORM_TYPE = "OPENAI"
    DEFAULT_MODEL_TYPE = "GPT_4O_MINI"
    
    # Agent configuration
    DEFAULT_SALESPERSON_NAME = "Ted Lasso"
    DEFAULT_SALESPERSON_ROLE = "Sales Representative"
    DEFAULT_COMPANY_NAME = "Sleep Haven"
    DEFAULT_COMPANY_BUSINESS = """
        Sleep Haven is a premium mattress company that provides
        customers with the most comfortable and supportive sleeping experience possible. 
        We offer a range of high-quality mattresses, pillows, and bedding accessories 
        that are designed to meet the unique needs of our customers.
    """
    DEFAULT_COMPANY_VALUES = """
        Our mission at Sleep Haven is to help people achieve a better night's sleep by
        providing them with the best possible sleep solutions. We believe that quality sleep
        is essential to overall health and well-being, and we are committed to helping our
        customers achieve optimal sleep by offering exceptional products and customer service.
    """
    DEFAULT_CONVERSATION_PURPOSE = """
        Find out whether they are looking to achieve better sleep via buying a premier mattress.
    """
    DEFAULT_CONVERSATION_TYPE = "call"
    
    # Token limits
    DEFAULT_TOKEN_LIMIT = 4096
    
    # Tool configuration
    DEFAULT_USE_TOOLS = True
    
    @classmethod
    def get_default_agent_config(cls) -> Dict[str, Any]:
        """Get the default agent configuration.
        
        Returns:
            A dictionary with default agent configuration.
        """
        return {
            "salesperson_name": cls.DEFAULT_SALESPERSON_NAME,
            "salesperson_role": cls.DEFAULT_SALESPERSON_ROLE,
            "company_name": cls.DEFAULT_COMPANY_NAME,
            "company_business": cls.DEFAULT_COMPANY_BUSINESS,
            "company_values": cls.DEFAULT_COMPANY_VALUES,
            "conversation_purpose": cls.DEFAULT_CONVERSATION_PURPOSE,
            "conversation_type": cls.DEFAULT_CONVERSATION_TYPE,
            "use_tools": cls.DEFAULT_USE_TOOLS,
        }