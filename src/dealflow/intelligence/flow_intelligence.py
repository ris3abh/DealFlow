# src/dealflow/intelligence/flow_intelligence.py
"""
Flow Intelligence Engine v2.0 - The core innovation of DealFlow 2.0

Automatically generates optimal conversation flows based on enabled tools,
eliminating hardcoded business scenarios and enabling infinite business flexibility.

Key Innovation: Simple tool configuration → Intelligent conversation behavior
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import time
from dealflow.utils.logger import logger


class FlowStepType(Enum):
    """Types of flow steps in a conversation"""
    INTRODUCTION = "introduction"
    QUALIFICATION = "qualification"  
    NEEDS_ASSESSMENT = "needs_assessment"
    CATALOG_SEARCH = "catalog_search"
    SERVICE_EXPLANATION = "service_explanation"
    PURCHASE_PROCESS = "purchase_process"
    APPOINTMENT_BOOKING = "appointment_booking"
    LEAD_CAPTURE = "lead_capture"
    INFORMATION_PROVISION = "information_provision"
    TRANSACTION_COMPLETION = "transaction_completion"


@dataclass
class FlowStep:
    """Represents a single step in the conversation flow"""
    step_type: FlowStepType
    stage_mapping: List[str]  # Maps to CAMEL conversation stages
    triggers: List[str]  # What triggers this step
    next_possible: List[FlowStepType]  # Possible next steps
    priority: int = 50  # Priority for step selection (higher = more important)
    description: str = ""
    estimated_duration: int = 60  # seconds
    success_criteria: List[str] = None
    
    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = []


@dataclass
class ConversationFlow:
    """Complete conversation flow configuration"""
    flow_id: str
    business_type: str
    steps: List[FlowStep]
    primary_goal: str
    completion_criteria: List[str]
    fallback_criteria: List[str]
    estimated_duration: int = 300  # seconds
    max_steps: int = 6  # Complexity limit
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class FlowValidationResult:
    """Result of flow validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    optimization_suggestions: List[str]
    
    def __post_init__(self):
        if not hasattr(self, 'errors'):
            self.errors = []
        if not hasattr(self, 'warnings'):
            self.warnings = []
        if not hasattr(self, 'optimization_suggestions'):
            self.optimization_suggestions = []


class FlowIntelligence:
    """
    Core engine that automatically generates conversation flows based on tool configuration.
    
    Key Innovation: Instead of hardcoding business scenarios, this engine analyzes
    enabled tools and generates optimal conversation flows automatically.
    
    Design Principles:
    - Simplicity over complexity
    - Consistent tool combinations = consistent flows
    - Rule-based validation for reliability
    - Hard limits on flow complexity
    """
    
    def __init__(self):
        self.flow_patterns = self._initialize_flow_patterns()
        self.tool_flow_mapping = self._initialize_tool_flow_mapping()
        self.flow_cache = {}  # Cache generated flows for performance
        self.validation_rules = self._initialize_validation_rules()
        
        logger.info("Flow Intelligence Engine v2.0 initialized")
    
    def _initialize_flow_patterns(self) -> Dict[str, FlowStep]:
        """Initialize the library of flow patterns that can be combined"""
        return {
            "introduction": FlowStep(
                step_type=FlowStepType.INTRODUCTION,
                stage_mapping=["INTRODUCTION", "QUALIFICATION"],
                triggers=["conversation_start"],
                next_possible=[FlowStepType.NEEDS_ASSESSMENT, FlowStepType.CATALOG_SEARCH],
                priority=100,  # Always highest priority - every conversation starts here
                description="Greet customer, introduce company, and qualify if they're the right person to talk to",
                estimated_duration=30,
                success_criteria=["customer_greeted", "company_introduced", "contact_qualified"]
            ),
            
            "needs_assessment": FlowStep(
                step_type=FlowStepType.NEEDS_ASSESSMENT,
                stage_mapping=["NEEDS_ANALYSIS", "VALUE_PROPOSITION"],
                triggers=["has_catalog_tools"],
                next_possible=[FlowStepType.CATALOG_SEARCH, FlowStepType.SERVICE_EXPLANATION],
                priority=80,
                description="Ask open-ended questions to understand customer needs and pain points",
                estimated_duration=90,
                success_criteria=["needs_identified", "pain_points_discovered", "requirements_clarified"]
            ),
            
            "catalog_search": FlowStep(
                step_type=FlowStepType.CATALOG_SEARCH,
                stage_mapping=["SOLUTION_PRESENTATION"],
                triggers=["catalog_tools_enabled"],
                next_possible=[FlowStepType.PURCHASE_PROCESS, FlowStepType.APPOINTMENT_BOOKING, FlowStepType.LEAD_CAPTURE],
                priority=70,
                description="Search and recommend products/services/events from catalog based on needs",
                estimated_duration=120,
                success_criteria=["catalog_searched", "recommendations_provided", "options_presented"]
            ),
            
            "service_explanation": FlowStep(
                step_type=FlowStepType.SERVICE_EXPLANATION,
                stage_mapping=["VALUE_PROPOSITION", "SOLUTION_PRESENTATION"],
                triggers=["service_catalog_enabled"],
                next_possible=[FlowStepType.APPOINTMENT_BOOKING, FlowStepType.LEAD_CAPTURE],
                priority=70,
                description="Explain services and their benefits in detail",
                estimated_duration=100,
                success_criteria=["service_explained", "benefits_communicated", "value_demonstrated"]
            ),
            
            "purchase_process": FlowStep(
                step_type=FlowStepType.PURCHASE_PROCESS,
                stage_mapping=["CLOSE", "OBJECTION_HANDLING"],
                triggers=["payment_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=90,
                description="Guide customer through purchase process and payment",
                estimated_duration=180,
                success_criteria=["purchase_intent_confirmed", "payment_processed", "transaction_completed"]
            ),
            
            "appointment_booking": FlowStep(
                step_type=FlowStepType.APPOINTMENT_BOOKING,
                stage_mapping=["CLOSE", "OBJECTION_HANDLING"],
                triggers=["appointment_booking_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=85,
                description="Schedule appointment or consultation",
                estimated_duration=120,
                success_criteria=["availability_checked", "appointment_scheduled", "confirmation_sent"]
            ),
            
            "lead_capture": FlowStep(
                step_type=FlowStepType.LEAD_CAPTURE,
                stage_mapping=["CLOSE"],
                triggers=["lead_capture_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=75,
                description="Collect contact information for follow-up",
                estimated_duration=90,
                success_criteria=["contact_info_collected", "interest_level_assessed", "follow_up_scheduled"]
            ),
            
            "information_provision": FlowStep(
                step_type=FlowStepType.INFORMATION_PROVISION,
                stage_mapping=["SOLUTION_PRESENTATION", "VALUE_PROPOSITION"],
                triggers=["no_action_tools"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=50,
                description="Provide information and answer questions",
                estimated_duration=120,
                success_criteria=["questions_answered", "information_provided", "customer_educated"]
            ),
            
            "transaction_completion": FlowStep(
                step_type=FlowStepType.TRANSACTION_COMPLETION,
                stage_mapping=["END_CONVERSATION"],
                triggers=["goal_achieved", "fallback_reached"],
                next_possible=[],
                priority=100,
                description="Wrap up conversation with next steps and confirmation",
                estimated_duration=30,
                success_criteria=["next_steps_confirmed", "contact_info_provided", "conversation_closed"]
            )
        }
    
    def _initialize_tool_flow_mapping(self) -> Dict[str, List[str]]:
        """
        Map tools to the flow steps they enable.
        
        Key Principle: Same tool combination = Same flow pattern
        This ensures consistency and predictability.
        """
        return {
            # Catalog Tools (Always require needs assessment first)
            "product_catalog": ["needs_assessment", "catalog_search"],
            "service_catalog": ["needs_assessment", "service_explanation"],
            "event_catalog": ["needs_assessment", "catalog_search"],
            "property_catalog": ["needs_assessment", "catalog_search"],
            
            # Action Tools (Primary business goals)
            "payment": ["purchase_process"],  # Stripe only
            "appointment_booking": ["appointment_booking"],  # Google Calendar only
            "lead_capture": ["lead_capture"],
            
            # Support Tools (Don't affect flow structure)
            "email_notification": [],  # Gmail only
            "sms_notification": [],
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for flow integrity"""
        return {
            "max_steps": 6,  # Complexity limit
            "min_steps": 3,  # Minimum viable flow
            "required_start": FlowStepType.INTRODUCTION,
            "required_end": FlowStepType.TRANSACTION_COMPLETION,
            "max_duration": 600,  # 10 minutes max conversation
            "required_catalog_tool": True,  # Must have at least one catalog tool
        }
    
    def generate_conversation_flow(
        self, 
        tools_enabled: List[str], 
        business_context: Optional[Dict[str, Any]] = None
    ) -> ConversationFlow:
        """
        Dynamically generate optimal conversation flow based on available tools.
        
        This is the core intelligence that replaces hardcoded business scenarios.
        
        Args:
            tools_enabled: List of enabled tool names
            business_context: Optional context (currently unused for simplicity)
            
        Returns:
            ConversationFlow: Complete flow configuration
            
        Raises:
            ValueError: If tool configuration is invalid
        """
        logger.info(f"Generating conversation flow for tools: {tools_enabled}")
        
        # Validate tool requirements
        self._validate_tool_requirements(tools_enabled)
        
        # Check cache first for performance
        cache_key = self._generate_cache_key(tools_enabled)
        if cache_key in self.flow_cache:
            logger.info("Returning cached flow")
            return self.flow_cache[cache_key]
        
        # Step 1: Always start with introduction
        selected_steps = ["introduction"]
        
        # Step 2: Determine if we need needs assessment (required for catalog tools)
        if self._has_catalog_tools(tools_enabled):
            selected_steps.append("needs_assessment")
            
            # Step 3: Add appropriate catalog step
            catalog_step = self._determine_catalog_step(tools_enabled)
            selected_steps.append(catalog_step)
        
        # Step 4: Determine primary action based on highest priority action tool
        primary_action = self._get_primary_action_tool(tools_enabled)
        if primary_action:
            selected_steps.append(primary_action)
        else:
            # No action tools - default to information provision
            selected_steps.append("information_provision")
        
        # Step 5: Always end with transaction completion
        selected_steps.append("transaction_completion")
        
        # Step 6: Build flow steps from patterns
        flow_steps = [self.flow_patterns[step_name] for step_name in selected_steps]
        
        # Step 7: Generate completion criteria
        completion_criteria, fallback_criteria = self._generate_completion_criteria(tools_enabled, primary_action)
        
        # Step 8: Determine business type
        business_type = self._infer_business_type(tools_enabled)
        
        # Step 9: Create flow configuration
        flow = ConversationFlow(
            flow_id=self._generate_flow_id(tools_enabled),
            business_type=business_type,
            steps=flow_steps,
            primary_goal=self._determine_primary_goal(primary_action, business_type),
            completion_criteria=completion_criteria,
            fallback_criteria=fallback_criteria,
            estimated_duration=sum(step.estimated_duration for step in flow_steps),
            max_steps=len(flow_steps)
        )
        
        # Step 10: Validate the generated flow
        validation_result = self.validate_flow(flow)
        if not validation_result.is_valid:
            error_msg = f"Generated invalid flow: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Step 11: Cache the flow for performance
        self.flow_cache[cache_key] = flow
        
        logger.info(f"Generated {len(flow_steps)} step flow for {business_type} business")
        return flow
    
    def _validate_tool_requirements(self, tools_enabled: List[str]) -> None:
        """Validate that tool configuration meets basic requirements"""
        if not tools_enabled:
            raise ValueError("At least one tool must be enabled")
        
        # Must have at least one catalog tool (our core requirement)
        if not self._has_catalog_tools(tools_enabled):
            raise ValueError("At least one catalog tool (product_catalog, service_catalog, event_catalog, or property_catalog) must be enabled")
        
        # Validate tool names
        valid_tools = set(self.tool_flow_mapping.keys())
        invalid_tools = [tool for tool in tools_enabled if tool not in valid_tools]
        if invalid_tools:
            raise ValueError(f"Invalid tools detected: {invalid_tools}")
        
        logger.debug("Tool requirements validation passed")
    
    def _has_catalog_tools(self, tools_enabled: List[str]) -> bool:
        """Check if any catalog tools are enabled"""
        catalog_tools = ["product_catalog", "service_catalog", "event_catalog", "property_catalog"]
        return any(tool in tools_enabled for tool in catalog_tools)
    
    def _determine_catalog_step(self, tools_enabled: List[str]) -> str:
        """Determine which catalog step to use based on enabled tools"""
        if "service_catalog" in tools_enabled:
            return "service_explanation"
        else:
            # product_catalog, event_catalog, property_catalog all use catalog_search
            return "catalog_search"
    
    def _get_primary_action_tool(self, tools_enabled: List[str]) -> Optional[str]:
        """
        Determine the primary action tool based on priority.
        
        Priority order (highest to lowest):
        1. payment (purchase_process) - Direct revenue
        2. appointment_booking - Lead conversion  
        3. lead_capture - Future revenue
        """
        action_priority = [
            ("purchase_process", ["payment"]),
            ("appointment_booking", ["appointment_booking"]),
            ("lead_capture", ["lead_capture"])
        ]
        
        # Check in priority order
        for action_type, required_tools in action_priority:
            if any(tool in tools_enabled for tool in required_tools):
                return action_type
        
        return None
    
    def _generate_completion_criteria(self, tools_enabled: List[str], primary_action: Optional[str]) -> Tuple[List[str], List[str]]:
        """Generate completion and fallback criteria based on tools and primary action"""
        completion_criteria = []
        fallback_criteria = []
        
        if primary_action == "purchase_process":
            completion_criteria = [
                "payment_completed",
                "purchase_confirmed", 
                "receipt_provided"
            ]
            fallback_criteria = [
                "cart_populated",
                "payment_intent_created",
                "product_interest_expressed"
            ]
        elif primary_action == "appointment_booking":
            completion_criteria = [
                "appointment_scheduled",
                "calendar_invite_sent",
                "confirmation_provided"
            ]
            fallback_criteria = [
                "availability_checked",
                "appointment_interest_expressed",
                "contact_information_collected"
            ]
        elif primary_action == "lead_capture":
            completion_criteria = [
                "contact_information_collected",
                "lead_qualified",
                "follow_up_scheduled"
            ]
            fallback_criteria = [
                "interest_level_assessed",
                "basic_info_collected",
                "future_contact_agreed"
            ]
        else:
            # Information provision
            completion_criteria = [
                "questions_answered",
                "information_provided",
                "customer_satisfied"
            ]
            fallback_criteria = [
                "basic_questions_answered",
                "some_information_provided"
            ]
        
        return completion_criteria, fallback_criteria
    
    def _infer_business_type(self, tools_enabled: List[str]) -> str:
        """
        Infer business type from enabled tools using simple, consistent rules.
        
        Keep it simple - same tool combination = same business type
        """
        if "product_catalog" in tools_enabled and "payment" in tools_enabled:
            return "ecommerce"
        elif "service_catalog" in tools_enabled and "appointment_booking" in tools_enabled:
            return "service_business"
        elif "event_catalog" in tools_enabled:
            return "event_business"
        elif "property_catalog" in tools_enabled:
            return "real_estate"
        elif "appointment_booking" in tools_enabled:
            return "appointment_based"
        else:
            return "information_business"
    
    def _determine_primary_goal(self, primary_action: Optional[str], business_type: str) -> str:
        """Determine the primary conversation goal"""
        if primary_action == "purchase_process":
            return "complete_purchase"
        elif primary_action == "appointment_booking":
            return "book_appointment"
        elif primary_action == "lead_capture":
            return "capture_qualified_lead"
        else:
            return "provide_information_and_build_interest"
    
    def _generate_flow_id(self, tools_enabled: List[str]) -> str:
        """Generate unique but deterministic flow ID based on tool combination"""
        tools_sorted = sorted(tools_enabled)
        tools_str = "_".join(tools_sorted)
        # Use SHA-256 hash for deterministic but unique IDs
        hash_object = hashlib.sha256(tools_str.encode())
        return f"flow_{hash_object.hexdigest()[:8]}"
    
    def _generate_cache_key(self, tools_enabled: List[str]) -> str:
        """Generate cache key for tool combination"""
        return "_".join(sorted(tools_enabled))
    
    def validate_flow(self, flow: ConversationFlow) -> FlowValidationResult:
        """
        Validate that a generated flow is logical and complete using rule-based validation.
        
        Args:
            flow: The flow to validate
            
        Returns:
            FlowValidationResult with validation status and feedback
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Rule 1: Flow must start with introduction
        if not flow.steps or flow.steps[0].step_type != FlowStepType.INTRODUCTION:
            errors.append("Flow must start with introduction step")
        
        # Rule 2: Flow must end with transaction completion
        if not flow.steps or flow.steps[-1].step_type != FlowStepType.TRANSACTION_COMPLETION:
            errors.append("Flow must end with transaction completion step")
        
        # Rule 3: Check step count limits
        if len(flow.steps) > self.validation_rules["max_steps"]:
            errors.append(f"Flow exceeds maximum steps ({self.validation_rules['max_steps']}): {len(flow.steps)}")
        elif len(flow.steps) < self.validation_rules["min_steps"]:
            errors.append(f"Flow below minimum steps ({self.validation_rules['min_steps']}): {len(flow.steps)}")
        
        # Rule 4: Check for logical step progression
        for i, step in enumerate(flow.steps[:-1]):
            next_step = flow.steps[i + 1]
            if next_step.step_type not in step.next_possible:
                errors.append(f"Invalid progression from {step.step_type.value} to {next_step.step_type.value}")
        
        # Rule 5: Check estimated duration
        if flow.estimated_duration > self.validation_rules["max_duration"]:
            warnings.append(f"Flow duration ({flow.estimated_duration}s) exceeds recommended maximum ({self.validation_rules['max_duration']}s)")
        
        # Rule 6: Check that primary goal aligns with completion criteria
        if not flow.completion_criteria:
            errors.append("Flow must have completion criteria")
        
        # Generate optimization suggestions
        if flow.estimated_duration > 300:  # 5 minutes
            suggestions.append("Consider simplifying the flow to reduce conversation time")
        
        if len(flow.steps) == self.validation_rules["max_steps"]:
            suggestions.append("Flow is at maximum complexity - monitor performance closely")
        
        return FlowValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            optimization_suggestions=suggestions
        )
    
    def get_flow_summary(self, flow: ConversationFlow) -> Dict[str, Any]:
        """Get a human-readable summary of the flow"""
        return {
            "flow_id": flow.flow_id,
            "business_type": flow.business_type,
            "primary_goal": flow.primary_goal,
            "steps": [step.step_type.value for step in flow.steps],
            "estimated_duration_minutes": flow.estimated_duration // 60,
            "completion_criteria": flow.completion_criteria,
            "total_steps": len(flow.steps),
            "created_at": flow.created_at,
            "max_steps": flow.max_steps
        }
    
    def clear_cache(self) -> None:
        """Clear the flow cache"""
        self.flow_cache.clear()
        logger.info("Flow cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_flows": len(self.flow_cache),
            "cache_keys": list(self.flow_cache.keys())
        }


# Example usage and testing functions
def create_example_flows():
    """Create example flows for different business types"""
    engine = FlowIntelligence()
    
    examples = {
        "E-commerce Store": ["product_catalog", "payment", "email_notification"],
        "Service Business": ["service_catalog", "appointment_booking"],
        "Event Business": ["event_catalog", "payment"],
        "Real Estate": ["property_catalog", "appointment_booking", "lead_capture"],
        "Consultation Business": ["service_catalog", "lead_capture"],
    }
    
    results = {}
    for business_name, tools in examples.items():
        try:
            flow = engine.generate_conversation_flow(tools)
            summary = engine.get_flow_summary(flow)
            results[business_name] = summary
            logger.info(f"Generated flow for {business_name}: {len(flow.steps)} steps")
        except Exception as e:
            logger.error(f"Failed to generate flow for {business_name}: {e}")
            results[business_name] = {"error": str(e)}
    
    return results


if __name__ == "__main__":
    # Quick test of the Flow Intelligence Engine
    logger.info("Testing Flow Intelligence Engine v2.0")
    
    engine = FlowIntelligence()
    
    # Test different tool combinations
    test_cases = [
        ["product_catalog", "payment"],
        ["service_catalog", "appointment_booking"],
        ["event_catalog", "payment", "email_notification"],
        ["property_catalog", "lead_capture"],
    ]
    
    for tools in test_cases:
        try:
            flow = engine.generate_conversation_flow(tools)
            summary = engine.get_flow_summary(flow)
            print(f"\nTools: {tools}")
            print(f"Business Type: {summary['business_type']}")
            print(f"Steps: {summary['steps']}")
            print(f"Duration: {summary['estimated_duration_minutes']} minutes")
            print(f"Goal: {summary['primary_goal']}")
        except Exception as e:
            print(f"Error with tools {tools}: {e}")
    
    print(f"\nCache stats: {engine.get_cache_stats()}")


# engine = FlowIntelligence()
# import json

# # E-commerce flow
# # E-commerce flow
# flow = engine.generate_conversation_flow(["product_catalog", "payment"])
# with open("product_catalog_payment.log", "w") as file:
#     file.write(json.dumps(engine.get_flow_summary(flow), indent=2))

# # Service business flow  
# flow = engine.generate_conversation_flow(["service_catalog", "appointment_booking"])
# with open("service_catalog_appointment.log", "w") as file:
#     file.write(json.dumps(engine.get_flow_summary(flow), indent=2))