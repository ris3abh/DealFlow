# src/dealflow/intelligence/behavior_engine.py
"""
Behavior Engine v2.0 - Master Orchestrator

The revolutionary engine that orchestrates all intelligence components to transform
simple configuration into complete agent behavior. This is the core innovation that
enables infinite business flexibility with zero hardcoded logic.

Key Innovation: Simple Config → Complete Intelligent Agent
- Orchestrates Flow Intelligence, Prompt Intelligence, and Tool Priority
- Validates configurations and handles errors gracefully
- Generates complete AgentConfiguration ready for production
- Provides monitoring and analytics configuration
- Handles integration requirements automatically

This is the "magic" that makes DealFlow 2.0 revolutionary.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time
import uuid
from datetime import datetime

from dealflow.intelligence.flow_intelligence import FlowIntelligence, ConversationFlow
from dealflow.intelligence.prompt_intelligence import PromptIntelligence, BusinessContext
from dealflow.intelligence.tool_priority import ToolPriority, ToolPriorityResult
from dealflow.schemas.configuration import (
    SmartAgentConfig, AgentConfiguration, ConversationGoal,
    ToolExecutionOrder, IntegrationRequirement, MonitoringConfig,
    ValidationResult, ConfigurationValidator
)
from dealflow.utils.logger import logger


@dataclass
class BehaviorAnalysis:
    """Complete analysis of agent behavior requirements"""
    flow_analysis: ConversationFlow
    prompt_analysis: str
    tool_analysis: ToolPriorityResult
    integration_requirements: List[IntegrationRequirement]
    monitoring_config: MonitoringConfig
    estimated_performance: Dict[str, Any]


@dataclass
class ConfigurationError:
    """Represents a configuration error with context"""
    error_type: str
    message: str
    component: str
    suggested_fix: str


class BehaviorEngine:
    """
    Master orchestrator that combines all intelligence engines to create complete agent behavior.
    
    Key Innovation: This engine eliminates the need for hardcoded business logic by
    intelligently combining the outputs of specialized intelligence engines.
    
    Architecture:
    1. Configuration Validation (ensure input is valid)
    2. Intelligence Engine Orchestration (generate behavior components)
    3. Integration Requirements Analysis (determine needed services)
    4. Monitoring Configuration (set up analytics and alerts)
    5. Complete Agent Assembly (create AgentConfiguration)
    
    Design Principles:
    - Fail fast with clear error messages
    - Graceful degradation when possible
    - Complete configuration validation
    - Performance optimization through caching
    - Comprehensive monitoring setup
    """
    
    def __init__(self):
        # Initialize all intelligence engines
        self.flow_intelligence = FlowIntelligence()
        self.prompt_intelligence = PromptIntelligence()
        self.tool_priority = ToolPriority()
        self.configuration_validator = ConfigurationValidator()
        
        # Cache for performance
        self.configuration_cache = {}
        
        # Integration requirements mapping
        self.integration_requirements_map = self._initialize_integration_requirements()
        
        # Monitoring templates
        self.monitoring_templates = self._initialize_monitoring_templates()
        
        logger.info("Behavior Engine v2.0 initialized - Master orchestrator ready")
    
    def _initialize_integration_requirements(self) -> Dict[str, List[str]]:
        """Initialize mapping of tools to required integrations"""
        return {
            "product_catalog": ["firecrawl"],
            "service_catalog": ["firecrawl"],
            "event_catalog": ["firecrawl"],
            "property_catalog": ["firecrawl"],
            "payment": ["stripe"],
            "appointment_booking": ["google_calendar"],
            "email_notification": ["sendgrid"],
            "sms_notification": ["twilio"]
        }
    
    def _initialize_monitoring_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize monitoring configuration templates by goal type"""
        return {
            "complete_purchase": {
                "key_metrics": [
                    "conversation_completion_rate",
                    "payment_completion_rate", 
                    "average_order_value",
                    "cart_abandonment_rate",
                    "tool_success_rate",
                    "average_conversation_duration"
                ],
                "alert_thresholds": {
                    "payment_completion_rate": 0.8,
                    "conversation_completion_rate": 0.7,
                    "tool_success_rate": 0.9
                },
                "dashboard_widgets": [
                    "revenue_dashboard",
                    "conversion_funnel",
                    "payment_analytics",
                    "tool_performance"
                ]
            },
            "book_appointment": {
                "key_metrics": [
                    "appointment_booking_rate",
                    "no_show_rate", 
                    "appointment_completion_rate",
                    "availability_check_success",
                    "tool_success_rate",
                    "average_conversation_duration"
                ],
                "alert_thresholds": {
                    "appointment_booking_rate": 0.6,
                    "no_show_rate": 0.2,
                    "tool_success_rate": 0.9
                },
                "dashboard_widgets": [
                    "appointment_dashboard",
                    "booking_funnel",
                    "calendar_analytics",
                    "tool_performance"
                ]
            },
            "capture_qualified_lead": {
                "key_metrics": [
                    "lead_capture_rate",
                    "lead_quality_score",
                    "follow_up_response_rate",
                    "interest_level_assessment",
                    "tool_success_rate",
                    "average_conversation_duration"
                ],
                "alert_thresholds": {
                    "lead_capture_rate": 0.5,
                    "lead_quality_score": 0.7,
                    "tool_success_rate": 0.9
                },
                "dashboard_widgets": [
                    "lead_dashboard",
                    "qualification_funnel",
                    "follow_up_analytics",
                    "tool_performance"
                ]
            },
            "provide_information": {
                "key_metrics": [
                    "question_answer_rate",
                    "customer_satisfaction_score",
                    "information_accuracy",
                    "tool_success_rate",
                    "average_conversation_duration"
                ],
                "alert_thresholds": {
                    "question_answer_rate": 0.8,
                    "customer_satisfaction_score": 0.7,
                    "tool_success_rate": 0.9
                },
                "dashboard_widgets": [
                    "information_dashboard",
                    "satisfaction_analytics",
                    "knowledge_performance",
                    "tool_performance"
                ]
            }
        }
    
    def configure_agent(self, config: SmartAgentConfig) -> AgentConfiguration:
        """
        Transform simple configuration into complete agent configuration.
        
        This is the main method that orchestrates all intelligence engines to create
        a complete, intelligent agent from minimal user input.
        
        Args:
            config: Simple user configuration
            
        Returns:
            AgentConfiguration: Complete agent ready for production
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If intelligence engine orchestration fails
        """
        logger.info("Starting agent configuration process")
        start_time = time.time()
        
        try:
            # Step 1: Validate Configuration
            validation_result = self._validate_configuration(config)
            if not validation_result.is_valid:
                raise ValueError(f"Configuration validation failed: {validation_result.errors}")
            
            # Step 2: Check Cache
            cache_key = self._generate_cache_key(config)
            if cache_key in self.configuration_cache:
                logger.info("Returning cached configuration")
                return self.configuration_cache[cache_key]
            
            # Step 3: Orchestrate Intelligence Engines
            behavior_analysis = self._orchestrate_intelligence_engines(config)
            
            # Step 4: Generate Integration Requirements
            integration_requirements = self._generate_integration_requirements(
                config.tools_enabled, config.integrations
            )
            
            # Step 5: Configure Monitoring
            monitoring_config = self._configure_monitoring(behavior_analysis.tool_analysis)
            
            # Step 6: Assemble Complete Configuration
            agent_configuration = self._assemble_agent_configuration(
                config, behavior_analysis, integration_requirements, monitoring_config
            )
            
            # Step 7: Cache Result
            self.configuration_cache[cache_key] = agent_configuration
            
            processing_time = time.time() - start_time
            logger.info(f"Agent configuration complete in {processing_time:.2f}s - {agent_configuration.business_type} agent ready")
            
            return agent_configuration
            
        except Exception as e:
            logger.error(f"Agent configuration failed: {e}")
            raise RuntimeError(f"Failed to configure agent: {e}")
    
    def _validate_configuration(self, config: SmartAgentConfig) -> ValidationResult:
        """Validate configuration using the configuration validator"""
        logger.debug("Validating configuration")
        return self.configuration_validator.validate(config)
    
    def _orchestrate_intelligence_engines(self, config: SmartAgentConfig) -> BehaviorAnalysis:
        """
        Orchestrate all intelligence engines to analyze configuration.
        
        This is the core orchestration logic that combines:
        - Flow Intelligence (conversation flow generation)
        - Tool Priority (goal determination and tool orchestration)  
        - Prompt Intelligence (dynamic prompt generation)
        """
        logger.info("Orchestrating intelligence engines")
        
        # Step 1: Generate conversation flow
        logger.debug("Generating conversation flow")
        flow_analysis = self.flow_intelligence.generate_conversation_flow(
            tools_enabled=config.tools_enabled,
            business_context=config.to_dict()
        )
        
        # Step 2: Analyze tool priorities and goals
        logger.debug("Analyzing tool priorities")
        tool_analysis = self.tool_priority.analyze_tool_combination(config.tools_enabled)
        
        # Step 3: Generate dynamic system prompt
        logger.debug("Generating system prompt")
        business_context = BusinessContext(
            company_name=config.company_info.company_name,
            agent_name=config.company_info.agent_name,
            agent_role=config.company_info.agent_role,
            company_description=config.company_info.company_description,
            company_values=config.company_info.company_values,
            conversation_purpose=getattr(config, 'conversation_purpose', None)
        )
        
        prompt_analysis = self.prompt_intelligence.generate_system_prompt(
            flow=flow_analysis,
            business_context=business_context,
            tools_enabled=config.tools_enabled
        )
        
        # Step 4: Analyze integration requirements
        integration_requirements = self._generate_integration_requirements(
            config.tools_enabled, config.integrations
        )
        
        # Step 5: Configure monitoring
        monitoring_config = self._configure_monitoring(tool_analysis)
        
        # Step 6: Estimate performance
        estimated_performance = self._estimate_agent_performance(
            flow_analysis, tool_analysis, config.tools_enabled
        )
        
        return BehaviorAnalysis(
            flow_analysis=flow_analysis,
            prompt_analysis=prompt_analysis,
            tool_analysis=tool_analysis,
            integration_requirements=integration_requirements,
            monitoring_config=monitoring_config,
            estimated_performance=estimated_performance
        )
    
    def _generate_integration_requirements(
        self, 
        tools_enabled: List[str], 
        configured_integrations: Dict[str, Any]
    ) -> List[IntegrationRequirement]:
        """Generate integration requirements based on enabled tools"""
        logger.debug("Generating integration requirements")
        
        requirements = []
        
        for tool in tools_enabled:
            required_services = self.integration_requirements_map.get(tool, [])
            
            for service in required_services:
                # Check if integration is already configured
                is_configured = service in configured_integrations
                
                requirement = IntegrationRequirement(
                    service_name=service,
                    required=True,
                    purpose=f"Required by {tool}",
                    fallback_available=self._has_fallback_integration(service)
                )
                requirements.append(requirement)
        
        return requirements
    
    def _configure_monitoring(self, tool_analysis: ToolPriorityResult) -> MonitoringConfig:
        """Configure monitoring based on conversation goal and tools"""
        logger.debug("Configuring monitoring")
        
        goal_name = tool_analysis.conversation_goal.name
        template = self.monitoring_templates.get(goal_name, self.monitoring_templates["provide_information"])
        
        return MonitoringConfig(
            key_metrics=template["key_metrics"],
            alert_thresholds=template["alert_thresholds"],
            dashboard_widgets=template["dashboard_widgets"],
            analytics_enabled=True
        )
    
    def _assemble_agent_configuration(
        self,
        config: SmartAgentConfig,
        analysis: BehaviorAnalysis,
        integration_requirements: List[IntegrationRequirement],
        monitoring_config: MonitoringConfig
    ) -> AgentConfiguration:
        """Assemble complete agent configuration from all components"""
        logger.debug("Assembling complete agent configuration")
        
        # Convert tool analysis to configuration format
        tool_execution_order = [
            ToolExecutionOrder(
                tool_name=tool.tool_name,
                execution_phase=tool.execution_phase.value,
                trigger_condition=tool.trigger_condition,
                priority=tool.priority,
                required=tool.required
            )
            for tool in analysis.tool_analysis.tool_execution_order
        ]
        
        # Convert conversation goal
        conversation_goal = ConversationGoal(
            name=analysis.tool_analysis.conversation_goal.name,
            description=analysis.tool_analysis.conversation_goal.description,
            success_metric=analysis.tool_analysis.conversation_goal.success_metric,
            fallback_metric=analysis.tool_analysis.conversation_goal.fallback_metric,
            priority=analysis.tool_analysis.conversation_goal.priority
        )
        
        # Generate unique configuration ID
        configuration_id = self._generate_configuration_id(config)
        
        return AgentConfiguration(
            # Core agent configuration
            system_prompt=analysis.prompt_analysis,
            conversation_flow=analysis.flow_analysis,  # This might need serialization
            conversation_goal=conversation_goal,
            
            # Tool configuration
            tools_enabled=config.tools_enabled,
            tool_execution_order=tool_execution_order,
            
            # Integration configuration
            integration_requirements=integration_requirements,
            integration_configs=config.integrations,
            
            # Monitoring and analytics
            monitoring_config=monitoring_config,
            
            # Metadata
            configuration_id=configuration_id,
            business_type=analysis.tool_analysis.business_type,
            created_at=datetime.utcnow(),
            version="2.0",
            
            # Performance settings (with intelligent defaults)
            response_timeout=self._calculate_response_timeout(analysis.tool_analysis),
            max_tool_execution_time=self._calculate_max_tool_time(config.tools_enabled),
            max_concurrent_tools=self._calculate_max_concurrent_tools(config.tools_enabled)
        )
    
    def _estimate_agent_performance(
        self, 
        flow: ConversationFlow, 
        tool_analysis: ToolPriorityResult,
        tools_enabled: List[str]
    ) -> Dict[str, Any]:
        """Estimate agent performance characteristics"""
        return {
            "estimated_success_rate": self._estimate_success_rate(tool_analysis.conversation_goal),
            "estimated_conversation_duration": tool_analysis.estimated_duration,
            "complexity_score": self._calculate_complexity_score(flow, tools_enabled),
            "resource_requirements": self._estimate_resource_requirements(tools_enabled),
            "scalability_rating": self._calculate_scalability_rating(tools_enabled)
        }
    
    def _generate_cache_key(self, config: SmartAgentConfig) -> str:
        """Generate cache key for configuration"""
        key_components = [
            config.company_info.company_name,
            config.company_info.agent_name,
            "_".join(sorted(config.tools_enabled)),
            config.business_type.value
        ]
        return "_".join(key_components).lower().replace(" ", "_")
    
    def _generate_configuration_id(self, config: SmartAgentConfig) -> str:
        """Generate unique configuration ID"""
        base_id = f"{config.company_info.company_name}_{config.company_info.agent_name}"
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{base_id}_{unique_suffix}".lower().replace(" ", "_")
    
    def _has_fallback_integration(self, service: str) -> bool:
        """Check if a service has fallback options"""
        fallback_services = {
            "stripe": False,  # No fallback for payments
            "google_calendar": False,  # No fallback for calendar
            "firecrawl": True,  # Could fallback to file-based catalogs
            "sendgrid": True,  # Could fallback to other email services
            "twilio": True   # Could fallback to other SMS services
        }
        return fallback_services.get(service, False)
    
    def _estimate_success_rate(self, goal: ConversationGoal) -> float:
        """Estimate success rate based on goal complexity"""
        base_rates = {
            "complete_purchase": 0.75,
            "book_appointment": 0.65,
            "capture_qualified_lead": 0.55,
            "provide_information": 0.85
        }
        return base_rates.get(goal.name, 0.70)
    
    def _calculate_complexity_score(self, flow: ConversationFlow, tools_enabled: List[str]) -> int:
        """Calculate complexity score (1-10)"""
        base_score = len(flow.steps)
        tool_complexity = len(tools_enabled) * 0.5
        duration_factor = flow.estimated_duration / 300  # Normalize to 5 minutes
        
        complexity = base_score + tool_complexity + duration_factor
        return max(1, min(10, int(complexity)))
    
    def _estimate_resource_requirements(self, tools_enabled: List[str]) -> Dict[str, str]:
        """Estimate resource requirements"""
        tool_count = len(tools_enabled)
        
        if tool_count <= 2:
            return {"cpu": "low", "memory": "low", "network": "medium"}
        elif tool_count <= 4:
            return {"cpu": "medium", "memory": "medium", "network": "medium"}
        else:
            return {"cpu": "high", "memory": "high", "network": "high"}
    
    def _calculate_scalability_rating(self, tools_enabled: List[str]) -> str:
        """Calculate scalability rating"""
        if len(tools_enabled) <= 3:
            return "high"
        elif len(tools_enabled) <= 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_response_timeout(self, tool_analysis: ToolPriorityResult) -> int:
        """Calculate appropriate response timeout"""
        base_timeout = 30
        tool_count_factor = len(tool_analysis.tool_execution_order) * 5
        complexity_factor = 10 if tool_analysis.conversation_goal.priority >= 90 else 5
        
        return base_timeout + tool_count_factor + complexity_factor
    
    def _calculate_max_tool_time(self, tools_enabled: List[str]) -> int:
        """Calculate maximum tool execution time"""
        if "payment" in tools_enabled:
            return 90  # Payment needs more time
        elif "appointment_booking" in tools_enabled:
            return 75  # Calendar operations can be slow
        else:
            return 60  # Standard timeout
    
    def _calculate_max_concurrent_tools(self, tools_enabled: List[str]) -> int:
        """Calculate maximum concurrent tools"""
        if len(tools_enabled) <= 3:
            return 2
        elif len(tools_enabled) <= 5:
            return 3
        else:
            return 4
    
    def get_configuration_summary(self, config: AgentConfiguration) -> Dict[str, Any]:
        """Get a human-readable summary of the configuration"""
        return {
            "agent_identity": {
                "business_type": config.business_type,
                "configuration_id": config.configuration_id,
                "created_at": config.created_at.isoformat(),
                "version": config.version
            },
            "conversation_setup": {
                "primary_goal": config.conversation_goal.name,
                "goal_description": config.conversation_goal.description,
                "success_metric": config.conversation_goal.success_metric,
                "estimated_duration_minutes": getattr(config.conversation_flow, 'estimated_duration', 300) // 60
            },
            "tool_configuration": {
                "tools_enabled": config.tools_enabled,
                "tool_count": len(config.tools_enabled),
                "critical_tools": [tool.tool_name for tool in config.tool_execution_order if tool.required],
                "execution_phases": list(set(tool.execution_phase for tool in config.tool_execution_order))
            },
            "integration_requirements": {
                "required_services": [req.service_name for req in config.integration_requirements if req.required],
                "optional_services": [req.service_name for req in config.integration_requirements if not req.required],
                "total_integrations": len(config.integration_requirements)
            },
            "monitoring_setup": {
                "key_metrics": len(config.monitoring_config.key_metrics),
                "alert_thresholds": len(config.monitoring_config.alert_thresholds),
                "dashboard_widgets": len(config.monitoring_config.dashboard_widgets),
                "analytics_enabled": config.monitoring_config.analytics_enabled
            },
            "performance_settings": {
                "response_timeout": config.response_timeout,
                "max_tool_execution_time": config.max_tool_execution_time,
                "max_concurrent_tools": config.max_concurrent_tools
            }
        }
    
    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self.configuration_cache.clear()
        # Also clear intelligence engine caches
        self.flow_intelligence.clear_cache()
        self.prompt_intelligence.clear_cache()
        logger.info("All caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "behavior_engine_cache": len(self.configuration_cache),
            "flow_intelligence_cache": len(self.flow_intelligence.flow_cache),
            "prompt_intelligence_cache": len(self.prompt_intelligence.prompt_cache),
            "total_cached_configurations": len(self.configuration_cache)
        }


# # Testing functions
# def test_behavior_engine():
#     """Test the behavior engine with different configurations"""
#     from dealflow.schemas.configuration import SmartAgentConfig, CompanyInfo, BusinessType
    
#     behavior_engine = BehaviorEngine()
    
#     # Test case 1: E-commerce
#     ecommerce_config = SmartAgentConfig(
#         company_info=CompanyInfo(
#             company_name="TechGear Pro",
#             agent_name="Alex",
#             agent_role="Sales Consultant",
#             company_description="We sell premium electronics and tech accessories.",
#             company_values="Quality, innovation, and customer satisfaction."
#         ),
#         tools_enabled=["product_catalog", "payment", "email_notification"],
#         business_type=BusinessType.ECOMMERCE
#     )
    
#     # Test case 2: Service Business
#     service_config = SmartAgentConfig(
#         company_info=CompanyInfo(
#             company_name="Legal Solutions",
#             agent_name="Sarah",
#             agent_role="Legal Consultant", 
#             company_description="We provide comprehensive legal services.",
#             company_values="Integrity, expertise, and personalized service."
#         ),
#         tools_enabled=["service_catalog", "appointment_booking"],
#         business_type=BusinessType.SERVICE_BUSINESS
#     )
    
#     test_cases = [
#         ("E-commerce", ecommerce_config),
#         ("Service Business", service_config)
#     ]
    
#     results = {}
    
#     for name, config in test_cases:
#         try:
#             agent_config = behavior_engine.configure_agent(config)
#             summary = behavior_engine.get_configuration_summary(agent_config)
#             results[name] = summary
            
#             logger.info(f"Successfully configured {name} agent")
            
#         except Exception as e:
#             logger.error(f"Failed to configure {name} agent: {e}")
#             results[name] = {"error": str(e)}
    
#     return results


# if __name__ == "__main__":
#     # Test the Behavior Engine
#     logger.info("Testing Behavior Engine v2.0 - Master Orchestrator")
    
#     results = test_behavior_engine()
    
#     for business_name, result in results.items():
#         print(f"\n{'='*70}")
#         print(f"AGENT CONFIGURATION: {business_name.upper()}")
#         print(f"{'='*70}")
        
#         if "error" in result:
#             print(f"❌ Error: {result['error']}")
#             continue
        
#         identity = result["agent_identity"]
#         conversation = result["conversation_setup"]
#         tools = result["tool_configuration"]
#         integrations = result["integration_requirements"]
#         monitoring = result["monitoring_setup"]
#         performance = result["performance_settings"]
        
#         print(f"🤖 Agent Identity:")
#         print(f"   Business Type: {identity['business_type']}")
#         print(f"   Configuration ID: {identity['configuration_id']}")
#         print(f"   Version: {identity['version']}")
        
#         print(f"\n💬 Conversation Setup:")
#         print(f"   Primary Goal: {conversation['primary_goal']}")
#         print(f"   Success Metric: {conversation['success_metric']}")
#         print(f"   Duration: {conversation['estimated_duration_minutes']} minutes")
        
#         print(f"\n🔧 Tool Configuration:")
#         print(f"   Tools Enabled: {', '.join(tools['tools_enabled'])}")
#         print(f"   Critical Tools: {', '.join(tools['critical_tools'])}")
#         print(f"   Execution Phases: {', '.join(tools['execution_phases'])}")
        
#         print(f"\n🔗 Integration Requirements:")
#         print(f"   Required Services: {', '.join(integrations['required_services'])}")
#         print(f"   Total Integrations: {integrations['total_integrations']}")
        
#         print(f"\n📊 Monitoring & Performance:")
#         print(f"   Key Metrics: {monitoring['key_metrics']} tracked")
#         print(f"   Response Timeout: {performance['response_timeout']}s")
#         print(f"   Max Concurrent Tools: {performance['max_concurrent_tools']}")
    
#     # Show cache stats
#     behavior_engine = BehaviorEngine()
#     print(f"\n📈 Cache Statistics:")
#     cache_stats = behavior_engine.get_cache_stats()
#     for key, value in cache_stats.items():
#         print(f"   {key}: {value}")