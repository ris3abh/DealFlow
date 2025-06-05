# src/dealflow/intelligence/flow_intelligence.py
"""
Flow Intelligence Engine - Automatically generates optimal conversation flows 
based on enabled tools, eliminating hardcoded business scenarios.

This is the core innovation of DealFlow 2.0 that enables infinite business flexibility.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
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
    priority: int = 50  # Priority for step selection
    description: str = ""


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


class FlowIntelligence:
    """
    Core engine that automatically generates conversation flows based on tool configuration.
    
    Key Innovation: Instead of hardcoding business scenarios, this engine analyzes
    enabled tools and generates optimal conversation flows automatically.
    """
    
    def __init__(self):
        self.flow_patterns = self._initialize_flow_patterns()
        self.tool_flow_mapping = self._initialize_tool_flow_mapping()
        logger.info("FlowIntelligence engine initialized")
    
    def _initialize_flow_patterns(self) -> Dict[str, FlowStep]:
        """Initialize the library of flow patterns that can be combined"""
        return {
            "introduction": FlowStep(
                step_type=FlowStepType.INTRODUCTION,
                stage_mapping=["INTRODUCTION", "QUALIFICATION"],
                triggers=["conversation_start"],
                next_possible=[FlowStepType.NEEDS_ASSESSMENT, FlowStepType.CATALOG_SEARCH, FlowStepType.SERVICE_EXPLANATION],
                priority=100,  # Always highest priority - every conversation starts here
                description="Greet customer, introduce company, and qualify if they're the right person to talk to"
            ),
            
            "needs_assessment": FlowStep(
                step_type=FlowStepType.NEEDS_ASSESSMENT,
                stage_mapping=["NEEDS_ANALYSIS", "VALUE_PROPOSITION"],
                triggers=["has_catalog_tools"],
                next_possible=[FlowStepType.CATALOG_SEARCH, FlowStepType.SERVICE_EXPLANATION],
                priority=80,
                description="Ask open-ended questions to understand customer needs and pain points"
            ),
            
            "catalog_search": FlowStep(
                step_type=FlowStepType.CATALOG_SEARCH,
                stage_mapping=["SOLUTION_PRESENTATION"],
                triggers=["catalog_tools_enabled"],
                next_possible=[FlowStepType.PURCHASE_PROCESS, FlowStepType.APPOINTMENT_BOOKING, FlowStepType.LEAD_CAPTURE],
                priority=70,
                description="Search and recommend products/services/events from catalog based on needs"
            ),
            
            "service_explanation": FlowStep(
                step_type=FlowStepType.SERVICE_EXPLANATION,
                stage_mapping=["VALUE_PROPOSITION", "SOLUTION_PRESENTATION"],
                triggers=["service_catalog_enabled"],
                next_possible=[FlowStepType.APPOINTMENT_BOOKING, FlowStepType.LEAD_CAPTURE],
                priority=70,
                description="Explain services and their benefits in detail"
            ),
            
            "purchase_process": FlowStep(
                step_type=FlowStepType.PURCHASE_PROCESS,
                stage_mapping=["CLOSE", "OBJECTION_HANDLING"],
                triggers=["payment_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=90,
                description="Guide customer through purchase process and payment"
            ),
            
            "appointment_booking": FlowStep(
                step_type=FlowStepType.APPOINTMENT_BOOKING,
                stage_mapping=["CLOSE", "OBJECTION_HANDLING"],
                triggers=["appointment_booking_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=85,
                description="Schedule appointment or consultation"
            ),
            
            "lead_capture": FlowStep(
                step_type=FlowStepType.LEAD_CAPTURE,
                stage_mapping=["CLOSE"],
                triggers=["lead_capture_enabled"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=75,
                description="Collect contact information for follow-up"
            ),
            
            "information_provision": FlowStep(
                step_type=FlowStepType.INFORMATION_PROVISION,
                stage_mapping=["SOLUTION_PRESENTATION", "VALUE_PROPOSITION"],
                triggers=["no_action_tools"],
                next_possible=[FlowStepType.TRANSACTION_COMPLETION],
                priority=50,
                description="Provide information and answer questions"
            ),
            
            "transaction_completion": FlowStep(
                step_type=FlowStepType.TRANSACTION_COMPLETION,
                stage_mapping=["END_CONVERSATION"],
                triggers=["goal_achieved", "fallback_reached"],
                next_possible=[],
                priority=100,
                description="Wrap up conversation with next steps and confirmation"
            )
        }
    
    def _initialize_tool_flow_mapping(self) -> Dict[str, List[str]]:
        """Map tools to the flow steps they enable"""
        return {
            # Catalog Tools
            "product_catalog": ["needs_assessment", "catalog_search"],
            "service_catalog": ["needs_assessment", "service_explanation"],
            "event_catalog": ["needs_assessment", "catalog_search"],
            "property_catalog": ["needs_assessment", "catalog_search"],
            
            # Action Tools
            "payment": ["purchase_process"],
            "shopping_cart": ["purchase_process"],
            "appointment_booking": ["appointment_booking"],
            "lead_capture": ["lead_capture"],
            
            # Support Tools (don't directly affect flow but enhance experience)
            "email_notification": [],
            "sms_notification": [],
            "calendar_integration": ["appointment_booking"],
            "crm_integration": ["lead_capture"]
        }
    
    def generate_conversation_flow(self, tools_enabled: List[str], business_context: Optional[Dict[str, Any]] = None) -> ConversationFlow:
        """
        Dynamically generate optimal conversation flow based on available tools.
        
        This is the core intelligence that replaces hardcoded business scenarios.
        
        Args:
            tools_enabled: List of enabled tool names
            business_context: Optional context about the business
            
        Returns:
            ConversationFlow: Complete flow configuration
        """
        logger.info(f"Generating conversation flow for tools: {tools_enabled}")
        
        # Step 1: Always start with introduction
        selected_steps = ["introduction"]
        
        # Step 2: Determine if we need needs assessment based on catalog tools
        if self._has_catalog_tools(tools_enabled):
            selected_steps.append("needs_assessment")
            
            # Add appropriate catalog step
            if any(tool in ["product_catalog", "event_catalog", "property_catalog"] for tool in tools_enabled):
                selected_steps.append("catalog_search")
            elif "service_catalog" in tools_enabled:
                selected_steps.append("service_explanation")
        
        # Step 3: Determine primary action based on highest priority action tool
        primary_action = self._get_primary_action_tool(tools_enabled)
        if primary_action:
            selected_steps.append(primary_action)
        else:
            # No action tools - default to information provision
            selected_steps.append("information_provision")
        
        # Step 4: Always end with transaction completion
        selected_steps.append("transaction_completion")
        
        # Step 5: Build flow steps from patterns
        flow_steps = [self.flow_patterns[step_name] for step_name in selected_steps]
        
        # Step 6: Generate completion criteria
        completion_criteria, fallback_criteria = self._generate_completion_criteria(tools_enabled, primary_action)
        
        # Step 7: Determine business type
        business_type = self._infer_business_type(tools_enabled, business_context)
        
        # Step 8: Create flow configuration
        flow = ConversationFlow(
            flow_id=self._generate_flow_id(tools_enabled),
            business_type=business_type,
            steps=flow_steps,
            primary_goal=self._determine_primary_goal(primary_action, business_type),
            completion_criteria=completion_criteria,
            fallback_criteria=fallback_criteria,
            estimated_duration=self._estimate_conversation_duration(flow_steps)
        )
        
        logger.info(f"Generated {len(flow_steps)} step flow for {business_type} business")
        return flow
    
    def _has_catalog_tools(self, tools_enabled: List[str]) -> bool:
        """Check if any catalog tools are enabled"""
        catalog_tools = ["product_catalog", "service_catalog", "event_catalog", "property_catalog"]
        return any(tool in tools_enabled for tool in catalog_tools)
    
    def _get_primary_action_tool(self, tools_enabled: List[str]) -> Optional[str]:
        """
        Determine the primary action tool based on priority.
        
        Priority order: payment > appointment_booking > lead_capture
        """
        action_priority = {
            "purchase_process": ["payment", "shopping_cart"],
            "appointment_booking": ["appointment_booking", "calendar_integration"],
            "lead_capture": ["lead_capture", "crm_integration"]
        }
        
        # Check in priority order
        for action_type, required_tools in action_priority.items():
            if any(tool in tools_enabled for tool in required_tools):
                return action_type
        
        return None
    
    def _generate_completion_criteria(self, tools_enabled: List[str], primary_action: Optional[str]) -> tuple:
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
    
    def _infer_business_type(self, tools_enabled: List[str], business_context: Optional[Dict[str, Any]]) -> str:
        """Infer business type from enabled tools and context"""
        if business_context and "business_type" in business_context:
            return business_context["business_type"]
        
        # Infer from tools
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
        """Generate unique flow ID based on tool combination"""
        tools_sorted = sorted(tools_enabled)
        tools_str = "_".join(tools_sorted)
        return f"flow_{hash(tools_str) % 10000:04d}"
    
    def _estimate_conversation_duration(self, flow_steps: List[FlowStep]) -> int:
        """Estimate conversation duration in seconds based on flow complexity"""
        base_duration = 120  # 2 minutes base
        step_duration = {
            FlowStepType.INTRODUCTION: 30,
            FlowStepType.NEEDS_ASSESSMENT: 60,
            FlowStepType.CATALOG_SEARCH: 90,
            FlowStepType.SERVICE_EXPLANATION: 120,
            FlowStepType.PURCHASE_PROCESS: 180,
            FlowStepType.APPOINTMENT_BOOKING: 120,
            FlowStepType.LEAD_CAPTURE: 60,
            FlowStepType.INFORMATION_PROVISION: 90,
            FlowStepType.TRANSACTION_COMPLETION: 30
        }
        
        total_duration = sum(step_duration.get(step.step_type, 60) for step in flow_steps)
        return max(total_duration, base_duration)
    
    def get_flow_summary(self, flow: ConversationFlow) -> Dict[str, Any]:
        """Get a human-readable summary of the flow"""
        return {
            "flow_id": flow.flow_id,
            "business_type": flow.business_type,
            "primary_goal": flow.primary_goal,
            "steps": [step.step_type.value for step in flow.steps],
            "estimated_duration_minutes": flow.estimated_duration // 60,
            "completion_criteria": flow.completion_criteria,
            "total_steps": len(flow.steps)
        }
    
    def validate_flow(self, flow: ConversationFlow) -> tuple[bool, List[str]]:
        """
        Validate that a generated flow is logical and complete.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check that flow starts with introduction
        if not flow.steps or flow.steps[0].step_type != FlowStepType.INTRODUCTION:
            issues.append("Flow must start with introduction step")
        
        # Check that flow ends with transaction completion
        if not flow.steps or flow.steps[-1].step_type != FlowStepType.TRANSACTION_COMPLETION:
            issues.append("Flow must end with transaction completion step")
        
        # Check for logical step progression
        for i, step in enumerate(flow.steps[:-1]):
            next_step = flow.steps[i + 1]
            if next_step.step_type not in step.next_possible:
                issues.append(f"Invalid progression from {step.step_type.value} to {next_step.step_type.value}")
        
        # Check that primary goal aligns with completion criteria
        if not flow.completion_criteria:
            issues.append("Flow must have completion criteria")
        
        # Check flow length is reasonable
        if len(flow.steps) < 2:
            issues.append("Flow must have at least 2 steps")
        elif len(flow.steps) > 10:
            issues.append("Flow should not exceed 10 steps for optimal user experience")
        
        return len(issues) == 0, issues