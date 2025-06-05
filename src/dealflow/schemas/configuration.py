# src/dealflow/schemas/configuration.py
"""
Configuration schemas for DealFlow 2.0 intelligent auto-configuration.

These schemas define the simple input format that gets transformed into
complete agent configurations by the intelligence engines.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class BusinessType(Enum):
    """Standard business types supported by DealFlow"""
    ECOMMERCE = "ecommerce"
    SERVICE_BUSINESS = "service_business"
    EVENT_BUSINESS = "event_business"
    REAL_ESTATE = "real_estate"
    APPOINTMENT_BASED = "appointment_based"
    INFORMATION_BUSINESS = "information_business"
    AUTO_DETECT = "auto_detect"


class ToolCategory(Enum):
    """Categories of tools available in DealFlow"""
    CATALOG = "catalog"
    ACTION = "action"
    SUPPORT = "support"


@dataclass
class CompanyInfo:
    """Company information for agent personalization"""
    company_name: str
    agent_name: str
    agent_role: str
    company_description: str
    company_values: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    business_hours: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "company_description": self.company_description,
            "company_values": self.company_values,
            "contact_info": self.contact_info or {},
            "business_hours": self.business_hours or {}
        }


@dataclass
class CatalogConfig:
    """Configuration for catalog tools"""
    catalog_type: str  # product, service, event, property
    urls: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    extract_schema: Optional[Dict[str, Any]] = None
    refresh_interval: int = 3600  # seconds


@dataclass
class IntegrationConfig:
    """Configuration for external service integrations"""
    service_name: str
    config: Dict[str, Any]
    enabled: bool = True
    fallback_enabled: bool = True
    health_check_interval: int = 300  # seconds


@dataclass
class SmartAgentConfig:
    """
    Simple input configuration that gets transformed into complete agent setup.
    
    This is the user-facing configuration - simple and intuitive.
    The intelligence engines transform this into complex agent behavior.
    """
    # Required: Company information
    company_info: CompanyInfo
    
    # Required: Tools to enable
    tools_enabled: List[str]
    
    # Optional: Catalog configurations
    catalogs: Dict[str, CatalogConfig] = field(default_factory=dict)
    
    # Optional: Integration configurations
    integrations: Dict[str, IntegrationConfig] = field(default_factory=dict)
    
    # Optional: Business context hints
    business_type: BusinessType = BusinessType.AUTO_DETECT
    target_audience: Optional[str] = None
    conversation_style: Optional[str] = None  # casual, professional, friendly
    
    # Optional: Advanced settings
    max_conversation_duration: int = 1800  # 30 minutes
    conversation_timeout: int = 300  # 5 minutes of inactivity
    enable_fallbacks: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing"""
        return {
            "company_info": self.company_info.to_dict(),
            "tools_enabled": self.tools_enabled,
            "catalogs": {k: v.__dict__ for k, v in self.catalogs.items()},
            "integrations": {k: v.__dict__ for k, v in self.integrations.items()},
            "business_type": self.business_type.value,
            "target_audience": self.target_audience,
            "conversation_style": self.conversation_style,
            "max_conversation_duration": self.max_conversation_duration,
            "conversation_timeout": self.conversation_timeout,
            "enable_fallbacks": self.enable_fallbacks
        }


@dataclass
class ConversationGoal:
    """Represents a conversation goal determined by intelligence engines"""
    name: str
    description: str
    success_metric: str
    fallback_metric: str
    priority: int = 50
    estimated_completion_time: int = 300  # seconds


@dataclass
class ToolExecutionOrder:
    """Defines the order and conditions for tool execution"""
    tool_name: str
    execution_phase: str  # discovery, engagement, completion, support
    trigger_condition: str
    priority: int
    required: bool = False


@dataclass
class IntegrationRequirement:
    """Defines integration requirements based on tools"""
    service_name: str
    required: bool
    purpose: str
    fallback_available: bool = False


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and analytics"""
    key_metrics: List[str]
    alert_thresholds: Dict[str, float]
    dashboard_widgets: List[str]
    analytics_enabled: bool = True


@dataclass
class AgentConfiguration:
    """
    Complete agent configuration generated by intelligence engines.
    
    This is the internal configuration that powers the agent behavior.
    Generated automatically from SmartAgentConfig.
    """
    # Core agent configuration
    system_prompt: str
    conversation_flow: Any  # ConversationFlow object
    conversation_goal: ConversationGoal
    
    # Tool configuration
    tools_enabled: List[str]
    tool_execution_order: List[ToolExecutionOrder]
    
    # Integration configuration
    integration_requirements: List[IntegrationRequirement]
    integration_configs: Dict[str, IntegrationConfig]
    
    # Monitoring and analytics
    monitoring_config: MonitoringConfig
    
    # Metadata
    configuration_id: str
    business_type: str
    created_at: datetime
    version: str = "2.0"
    
    # Performance settings
    response_timeout: int = 30
    max_tool_execution_time: int = 60
    max_concurrent_tools: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "system_prompt": self.system_prompt,
            "conversation_goal": self.conversation_goal.__dict__,
            "tools_enabled": self.tools_enabled,
            "tool_execution_order": [order.__dict__ for order in self.tool_execution_order],
            "integration_requirements": [req.__dict__ for req in self.integration_requirements],
            "integration_configs": {k: v.__dict__ for k, v in self.integration_configs.items()},
            "monitoring_config": self.monitoring_config.__dict__,
            "configuration_id": self.configuration_id,
            "business_type": self.business_type,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "response_timeout": self.response_timeout,
            "max_tool_execution_time": self.max_tool_execution_time,
            "max_concurrent_tools": self.max_concurrent_tools
        }


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ConfigurationValidator:
    """Validates SmartAgentConfig for completeness and correctness"""
    
    def __init__(self):
        self.required_integrations = {
            "product_catalog": ["firecrawl"],
            "service_catalog": ["firecrawl"],
            "event_catalog": ["firecrawl"],
            "property_catalog": ["firecrawl"],
            "payment": ["stripe"],
            "appointment_booking": ["google_calendar"],
            "email_notification": ["sendgrid"],
            "sms_notification": ["twilio"]
        }
    
    def validate(self, config: SmartAgentConfig) -> ValidationResult:
        """
        Validate a smart agent configuration.
        
        Args:
            config: The configuration to validate
            
        Returns:
            ValidationResult with validation status and feedback
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Validate company info
        company_errors = self._validate_company_info(config.company_info)
        errors.extend(company_errors)
        
        # Validate tools
        tool_errors, tool_warnings = self._validate_tools(config.tools_enabled)
        errors.extend(tool_errors)
        warnings.extend(tool_warnings)
        
        # Validate integrations
        integration_errors, integration_warnings = self._validate_integrations(
            config.tools_enabled, config.integrations
        )
        errors.extend(integration_errors)
        warnings.extend(integration_warnings)
        
        # Validate catalog configurations
        catalog_errors = self._validate_catalogs(config.catalogs, config.tools_enabled)
        errors.extend(catalog_errors)
        
        # Generate suggestions
        suggestions.extend(self._generate_suggestions(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_company_info(self, company_info: CompanyInfo) -> List[str]:
        """Validate company information completeness"""
        errors = []
        
        if not company_info.company_name:
            errors.append("Company name is required")
        
        if not company_info.agent_name:
            errors.append("Agent name is required")
        
        if not company_info.agent_role:
            errors.append("Agent role is required")
        
        if not company_info.company_description:
            errors.append("Company description is required")
        
        if len(company_info.company_description) < 50:
            errors.append("Company description should be at least 50 characters for better agent performance")
        
        return errors
    
    def _validate_tools(self, tools_enabled: List[str]) -> tuple[List[str], List[str]]:
        """Validate tool configuration"""
        errors = []
        warnings = []
        
        if not tools_enabled:
            errors.append("At least one tool must be enabled")
            return errors, warnings
        
        # Check for valid tool names
        valid_tools = {
            "product_catalog", "service_catalog", "event_catalog", "property_catalog",
            "payment", "shopping_cart", "appointment_booking", "lead_capture",
            "email_notification", "sms_notification", "calendar_integration", "crm_integration"
        }
        
        invalid_tools = [tool for tool in tools_enabled if tool not in valid_tools]
        if invalid_tools:
            errors.append(f"Invalid tools: {invalid_tools}")
        
        # Check for logical tool combinations
        catalog_tools = [tool for tool in tools_enabled if tool.endswith("_catalog")]
        action_tools = [tool for tool in tools_enabled if tool in ["payment", "appointment_booking", "lead_capture"]]
        
        if catalog_tools and not action_tools:
            warnings.append("You have catalog tools but no action tools. Consider adding payment, appointment_booking, or lead_capture")
        
        if "payment" in tools_enabled and not any(tool.endswith("_catalog") for tool in tools_enabled):
            warnings.append("Payment tool enabled but no catalog tools. Customers may not know what to buy")
        
        return errors, warnings
    
    def _validate_integrations(self, tools_enabled: List[str], integrations: Dict[str, IntegrationConfig]) -> tuple[List[str], List[str]]:
        """Validate integration configurations"""
        errors = []
        warnings = []
        
        # Check required integrations for enabled tools
        for tool in tools_enabled:
            required_services = self.required_integrations.get(tool, [])
            for service in required_services:
                if service not in integrations:
                    errors.append(f"Tool '{tool}' requires '{service}' integration but it's not configured")
                elif not integrations[service].enabled:
                    warnings.append(f"Tool '{tool}' requires '{service}' integration but it's disabled")
        
        # Validate integration configurations
        for service_name, integration in integrations.items():
            if not integration.config:
                errors.append(f"Integration '{service_name}' has empty configuration")
            
            # Service-specific validation
            if service_name == "stripe" and "api_key" not in integration.config:
                errors.append("Stripe integration requires 'api_key' in configuration")
            
            if service_name == "firecrawl" and "api_key" not in integration.config:
                errors.append("Firecrawl integration requires 'api_key' in configuration")
        
        return errors, warnings
    
    def _validate_catalogs(self, catalogs: Dict[str, CatalogConfig], tools_enabled: List[str]) -> List[str]:
        """Validate catalog configurations"""
        errors = []
        
        # Check that enabled catalog tools have corresponding catalog configs
        for tool in tools_enabled:
            if tool.endswith("_catalog"):
                catalog_type = tool.replace("_catalog", "")
                if catalog_type not in catalogs:
                    errors.append(f"Tool '{tool}' is enabled but no catalog configuration provided")
                else:
                    catalog = catalogs[catalog_type]
                    if not catalog.urls and not catalog.file_paths:
                        errors.append(f"Catalog '{catalog_type}' must have either URLs or file paths configured")
                    
                    if catalog.urls and not catalog.extract_schema:
                        errors.append(f"Catalog '{catalog_type}' with URLs requires extract_schema for web scraping")
        
        return errors
    
    def _generate_suggestions(self, config: SmartAgentConfig) -> List[str]:
        """Generate helpful suggestions for improving the configuration"""
        suggestions = []
        
        # Suggest business type if auto-detect
        if config.business_type == BusinessType.AUTO_DETECT:
            suggestions.append("Consider specifying business_type for more targeted optimization")
        
        # Suggest conversation style if not set
        if not config.conversation_style:
            suggestions.append("Consider setting conversation_style (casual/professional/friendly) for better customer experience")
        
        # Suggest target audience if not set
        if not config.target_audience:
            suggestions.append("Consider defining target_audience for more personalized conversations")
        
        # Suggest support tools for better experience
        if "payment" in config.tools_enabled and "email_notification" not in config.tools_enabled:
            suggestions.append("Consider adding email_notification for purchase confirmations")
        
        if "appointment_booking" in config.tools_enabled and "sms_notification" not in config.tools_enabled:
            suggestions.append("Consider adding sms_notification for appointment reminders")
        
        # Suggest company values if not provided
        if not config.company_info.company_values:
            suggestions.append("Consider adding company values to help the agent represent your brand better")
        
        return suggestions


# Example configurations for different business types
class ExampleConfigs:
    """Example configurations for common business scenarios"""
    
    @staticmethod
    def ecommerce_store() -> SmartAgentConfig:
        """Example configuration for an e-commerce store"""
        return SmartAgentConfig(
            company_info=CompanyInfo(
                company_name="TechGear Pro",
                agent_name="Alex",
                agent_role="Sales Consultant",
                company_description="We sell premium electronics and tech accessories for professionals and enthusiasts.",
                company_values="Quality, innovation, and customer satisfaction are our core values."
            ),
            tools_enabled=["product_catalog", "payment", "email_notification"],
            catalogs={
                "product": CatalogConfig(
                    catalog_type="product",
                    urls=["https://techgearpro.com/products"],
                    extract_schema={
                        "products": {
                            "name": "Product name",
                            "price": "Price in USD",
                            "description": "Product description",
                            "category": "Product category"
                        }
                    }
                )
            },
            integrations={
                "firecrawl": IntegrationConfig("firecrawl", {"api_key": "your_api_key"}),
                "stripe": IntegrationConfig("stripe", {"api_key": "your_stripe_key"}),
                "sendgrid": IntegrationConfig("sendgrid", {"api_key": "your_sendgrid_key"})
            },
            business_type=BusinessType.ECOMMERCE,
            conversation_style="professional"
        )
    
    @staticmethod
    def service_business() -> SmartAgentConfig:
        """Example configuration for a service business"""
        return SmartAgentConfig(
            company_info=CompanyInfo(
                company_name="Legal Solutions Inc",
                agent_name="Sarah",
                agent_role="Legal Consultant",
                company_description="We provide comprehensive legal services for small businesses and individuals.",
                company_values="Integrity, expertise, and personalized service."
            ),
            tools_enabled=["service_catalog", "appointment_booking", "lead_capture"],
            catalogs={
                "service": CatalogConfig(
                    catalog_type="service",
                    file_paths=["./services.txt"]
                )
            },
            integrations={
                "google_calendar": IntegrationConfig("google_calendar", {"credentials_path": "creds.json"}),
                "sendgrid": IntegrationConfig("sendgrid", {"api_key": "your_sendgrid_key"})
            },
            business_type=BusinessType.SERVICE_BUSINESS,
            conversation_style="professional"
        )
    
    @staticmethod
    def event_business() -> SmartAgentConfig:
        """Example configuration for an event business"""
        return SmartAgentConfig(
            company_info=CompanyInfo(
                company_name="Epic Events",
                agent_name="Mike",
                agent_role="Event Specialist",
                company_description="We organize and host amazing events, from corporate conferences to private parties.",
                company_values="Creativity, attention to detail, and unforgettable experiences."
            ),
            tools_enabled=["event_catalog", "payment", "email_notification"],
            catalogs={
                "event": CatalogConfig(
                    catalog_type="event",
                    urls=["https://epicevents.com/events"],
                    extract_schema={
                        "events": {
                            "title": "Event name",
                            "date": "Event date",
                            "price": "Ticket price",
                            "description": "Event description",
                            "venue": "Event venue"
                        }
                    }
                )
            },
            integrations={
                "firecrawl": IntegrationConfig("firecrawl", {"api_key": "your_api_key"}),
                "stripe": IntegrationConfig("stripe", {"api_key": "your_stripe_key"}),
                "sendgrid": IntegrationConfig("sendgrid", {"api_key": "your_sendgrid_key"})
            },
            business_type=BusinessType.EVENT_BUSINESS,
            conversation_style="friendly"
        )