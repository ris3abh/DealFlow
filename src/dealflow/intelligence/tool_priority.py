# src/dealflow/intelligence/tool_priority.py
"""
Tool Priority System v2.0 - Intelligent Tool Orchestration

Intelligently determines conversation goals, tool execution order, and success metrics
based on business requirements and enabled tools. Eliminates hardcoded tool logic
by using priority-based decision making.

Key Innovation: Tool combinations → Intelligent execution strategies
- Analyzes tool combinations to determine primary business goals
- Generates optimal tool execution order based on conversation phases
- Maps tools to measurable success criteria
- Provides fallback strategies when primary tools fail
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from dealflow.utils.logger import logger


class ToolCategory(Enum):
    """Categories of tools in the system"""
    CATALOG = "catalog"      # Discovery phase tools
    ACTION = "action"        # Conversion phase tools  
    SUPPORT = "support"      # Enhancement phase tools


class ExecutionPhase(Enum):
    """Phases of tool execution in conversation flow"""
    DISCOVERY = "discovery"      # Understanding needs, searching catalogs
    ENGAGEMENT = "engagement"    # Presenting options, building interest
    CONVERSION = "conversion"    # Completing transactions, bookings
    SUPPORT = "support"         # Confirmations, notifications, follow-up


@dataclass
class ConversationGoal:
    """Represents a conversation goal determined by tool analysis"""
    name: str
    description: str
    success_metric: str
    fallback_metric: str
    priority: int = 50
    estimated_completion_time: int = 300  # seconds
    required_tools: List[str] = None
    
    def __post_init__(self):
        if self.required_tools is None:
            self.required_tools = []


@dataclass
class ToolExecution:
    """Defines how and when a tool should be executed"""
    tool_name: str
    execution_phase: ExecutionPhase
    trigger_condition: str
    priority: int
    required: bool = False
    depends_on: List[str] = None  # Tools that must execute before this one
    timeout_seconds: int = 30
    retry_attempts: int = 2
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class ToolPriorityResult:
    """Result of tool priority analysis"""
    conversation_goal: ConversationGoal
    tool_execution_order: List[ToolExecution]
    success_criteria: List[str]
    fallback_criteria: List[str]
    estimated_duration: int
    business_type: str


class ToolPriority:
    """
    Core engine that determines optimal tool usage strategies based on business requirements.
    
    Key Innovation: Instead of hardcoded tool orchestration, this engine analyzes
    tool combinations and generates intelligent execution strategies automatically.
    
    Design Principles:
    - Priority-based goal determination (payment > appointments > leads)
    - Phase-based execution (discovery → engagement → conversion → support)
    - Measurable success criteria for each goal type
    - Intelligent fallback strategies
    - Tool dependency management
    """
    
    def __init__(self):
        self.tool_categories = self._initialize_tool_categories()
        self.conversation_goals = self._initialize_conversation_goals()
        self.tool_priorities = self._initialize_tool_priorities()
        self.execution_phases = self._initialize_execution_phases()
        self.success_metrics = self._initialize_success_metrics()
        
        logger.info("Tool Priority System v2.0 initialized")
    
    def _initialize_tool_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tool categorization with priorities and characteristics"""
        return {
            # CATALOG TOOLS - Discovery Phase (Medium Priority)
            "product_catalog": {
                "category": ToolCategory.CATALOG,
                "priority": 50,
                "execution_phase": ExecutionPhase.DISCOVERY,
                "description": "Search and recommend products",
                "business_impact": "enables_product_sales",
                "required_for": ["complete_purchase"],
                "dependencies": []
            },
            "service_catalog": {
                "category": ToolCategory.CATALOG,
                "priority": 50,
                "execution_phase": ExecutionPhase.DISCOVERY,
                "description": "Search and explain services",
                "business_impact": "enables_service_sales",
                "required_for": ["book_appointment", "capture_qualified_lead"],
                "dependencies": []
            },
            "event_catalog": {
                "category": ToolCategory.CATALOG,
                "priority": 50,
                "execution_phase": ExecutionPhase.DISCOVERY,
                "description": "Search and recommend events",
                "business_impact": "enables_event_sales",
                "required_for": ["complete_purchase"],
                "dependencies": []
            },
            "property_catalog": {
                "category": ToolCategory.CATALOG,
                "priority": 50,
                "execution_phase": ExecutionPhase.DISCOVERY,
                "description": "Search and present properties",
                "business_impact": "enables_property_sales",
                "required_for": ["capture_qualified_lead"],
                "dependencies": []
            },
            
            # ACTION TOOLS - Conversion Phase (High Priority)
            "payment": {
                "category": ToolCategory.ACTION,
                "priority": 100,  # Highest - direct revenue
                "execution_phase": ExecutionPhase.CONVERSION,
                "description": "Process payments and complete purchases",
                "business_impact": "generates_revenue",
                "required_for": [],
                "dependencies": ["product_catalog", "event_catalog"]  # Need something to sell
            },
            "appointment_booking": {
                "category": ToolCategory.ACTION,
                "priority": 90,  # High - lead conversion
                "execution_phase": ExecutionPhase.CONVERSION,
                "description": "Schedule appointments and consultations",
                "business_impact": "converts_leads",
                "required_for": [],
                "dependencies": ["service_catalog"]  # Need services to book
            },
            "lead_capture": {
                "category": ToolCategory.ACTION,
                "priority": 80,  # Medium-High - future revenue
                "execution_phase": ExecutionPhase.CONVERSION,
                "description": "Collect contact information for follow-up",
                "business_impact": "generates_leads",
                "required_for": [],
                "dependencies": []  # Can work with any catalog
            },
            
            # SUPPORT TOOLS - Support Phase (Low Priority)
            "email_notification": {
                "category": ToolCategory.SUPPORT,
                "priority": 20,  # Low - enhancement only
                "execution_phase": ExecutionPhase.SUPPORT,
                "description": "Send email confirmations and notifications",
                "business_impact": "enhances_experience",
                "required_for": [],
                "dependencies": ["payment", "appointment_booking"]  # Need something to confirm
            },
            "sms_notification": {
                "category": ToolCategory.SUPPORT,
                "priority": 15,  # Low - enhancement only
                "execution_phase": ExecutionPhase.SUPPORT,
                "description": "Send SMS confirmations and reminders",
                "business_impact": "enhances_experience", 
                "required_for": [],
                "dependencies": ["appointment_booking"]  # Mainly for appointment reminders
            }
        }
    
    def _initialize_conversation_goals(self) -> Dict[str, ConversationGoal]:
        """Initialize possible conversation goals based on tool combinations"""
        return {
            "complete_purchase": ConversationGoal(
                name="complete_purchase",
                description="Guide customer through product selection and purchase completion",
                success_metric="payment_completed",
                fallback_metric="cart_populated",
                priority=100,  # Highest priority - direct revenue
                estimated_completion_time=420,  # 7 minutes
                required_tools=["payment"]
            ),
            "book_appointment": ConversationGoal(
                name="book_appointment",
                description="Understand customer needs and schedule appropriate appointment",
                success_metric="appointment_scheduled",
                fallback_metric="availability_checked",
                priority=90,  # High priority - lead conversion
                estimated_completion_time=360,  # 6 minutes
                required_tools=["appointment_booking"]
            ),
            "capture_qualified_lead": ConversationGoal(
                name="capture_qualified_lead",
                description="Provide valuable information and capture contact details for follow-up",
                success_metric="contact_info_collected",
                fallback_metric="interest_demonstrated",
                priority=80,  # Medium-high priority - future revenue
                estimated_completion_time=300,  # 5 minutes
                required_tools=["lead_capture"]
            ),
            "provide_information": ConversationGoal(
                name="provide_information",
                description="Answer questions and provide helpful information about offerings",
                success_metric="questions_answered",
                fallback_metric="catalog_searched",
                priority=50,  # Lowest priority - no direct business outcome
                estimated_completion_time=240,  # 4 minutes
                required_tools=[]  # Can work with just catalog tools
            )
        }
    
    def _initialize_tool_priorities(self) -> Dict[str, int]:
        """Initialize tool priority rankings for conflict resolution"""
        return {
            # Action tools (highest priority)
            "payment": 100,
            "appointment_booking": 90, 
            "lead_capture": 80,
            
            # Catalog tools (medium priority)
            "product_catalog": 50,
            "service_catalog": 50,
            "event_catalog": 50,
            "property_catalog": 50,
            
            # Support tools (lowest priority)
            "email_notification": 20,
            "sms_notification": 15
        }
    
    def _initialize_execution_phases(self) -> Dict[ExecutionPhase, Dict[str, Any]]:
        """Initialize execution phase characteristics"""
        return {
            ExecutionPhase.DISCOVERY: {
                "description": "Understanding customer needs and exploring options",
                "typical_tools": ["product_catalog", "service_catalog", "event_catalog", "property_catalog"],
                "success_indicators": ["needs_identified", "options_presented", "interest_generated"],
                "estimated_duration": 120  # 2 minutes
            },
            ExecutionPhase.ENGAGEMENT: {
                "description": "Presenting solutions and building purchase intent",
                "typical_tools": [],  # This phase uses results from discovery
                "success_indicators": ["solution_presented", "value_demonstrated", "objections_addressed"],
                "estimated_duration": 90  # 1.5 minutes
            },
            ExecutionPhase.CONVERSION: {
                "description": "Completing transactions, bookings, or lead capture",
                "typical_tools": ["payment", "appointment_booking", "lead_capture"],
                "success_indicators": ["action_completed", "transaction_confirmed", "next_steps_defined"],
                "estimated_duration": 180  # 3 minutes
            },
            ExecutionPhase.SUPPORT: {
                "description": "Confirmations, notifications, and follow-up",
                "typical_tools": ["email_notification", "sms_notification"],
                "success_indicators": ["confirmation_sent", "follow_up_scheduled", "customer_satisfied"],
                "estimated_duration": 30  # 30 seconds
            }
        }
    
    def _initialize_success_metrics(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize success and fallback metrics for each goal type"""
        return {
            "complete_purchase": {
                "success": ["payment_completed", "purchase_confirmed", "receipt_provided"],
                "fallback": ["cart_populated", "payment_intent_created", "product_interest_expressed"]
            },
            "book_appointment": {
                "success": ["appointment_scheduled", "calendar_invite_sent", "confirmation_provided"],
                "fallback": ["availability_checked", "appointment_interest_expressed", "contact_info_collected"]
            },
            "capture_qualified_lead": {
                "success": ["contact_info_collected", "lead_qualified", "follow_up_scheduled"],
                "fallback": ["interest_level_assessed", "basic_info_collected", "future_contact_agreed"]
            },
            "provide_information": {
                "success": ["questions_answered", "information_provided", "customer_satisfied"],
                "fallback": ["basic_questions_answered", "some_information_provided"]
            }
        }
    
    def analyze_tool_combination(self, tools_enabled: List[str]) -> ToolPriorityResult:
        """
        Analyze tool combination and determine optimal execution strategy.
        
        This is the main method that orchestrates tool priority analysis.
        
        Args:
            tools_enabled: List of enabled tool names
            
        Returns:
            ToolPriorityResult with complete execution strategy
        """
        logger.info(f"Analyzing tool combination: {tools_enabled}")
        
        # Step 1: Validate tools
        self._validate_tools(tools_enabled)
        
        # Step 2: Determine conversation goal
        conversation_goal = self.get_conversation_goal(tools_enabled)
        
        # Step 3: Generate tool execution order
        tool_execution_order = self.get_tool_execution_order(tools_enabled)
        
        # Step 4: Get success criteria
        success_criteria, fallback_criteria = self._get_success_criteria(conversation_goal.name)
        
        # Step 5: Estimate total duration
        estimated_duration = self._estimate_total_duration(tool_execution_order, conversation_goal)
        
        # Step 6: Infer business type
        business_type = self._infer_business_type(tools_enabled, conversation_goal)
        
        result = ToolPriorityResult(
            conversation_goal=conversation_goal,
            tool_execution_order=tool_execution_order,
            success_criteria=success_criteria,
            fallback_criteria=fallback_criteria,
            estimated_duration=estimated_duration,
            business_type=business_type
        )
        
        logger.info(f"Tool analysis complete: Goal={conversation_goal.name}, Tools={len(tool_execution_order)}, Duration={estimated_duration}s")
        return result
    
    def get_conversation_goal(self, tools_enabled: List[str]) -> ConversationGoal:
        """
        Determine primary conversation goal from enabled tools using priority-based analysis.
        
        Priority order: payment > appointment_booking > lead_capture > information
        """
        logger.debug(f"Determining conversation goal for tools: {tools_enabled}")
        
        # Find highest priority goal that can be achieved with available tools
        possible_goals = []
        
        for goal_name, goal in self.conversation_goals.items():
            if self._can_achieve_goal(goal, tools_enabled):
                possible_goals.append(goal)
        
        if not possible_goals:
            # Fallback to information provision if no other goals possible
            return self.conversation_goals["provide_information"]
        
        # Return highest priority achievable goal
        primary_goal = max(possible_goals, key=lambda g: g.priority)
        logger.info(f"Primary conversation goal: {primary_goal.name}")
        return primary_goal
    
    def get_tool_execution_order(self, tools_enabled: List[str]) -> List[ToolExecution]:
        """
        Determine optimal execution order for tools based on phases and dependencies.
        
        Returns tools organized by execution phase with proper dependency handling.
        """
        logger.debug(f"Determining tool execution order for: {tools_enabled}")
        
        execution_plan = []
        
        # Group tools by execution phase
        tools_by_phase = {phase: [] for phase in ExecutionPhase}
        
        for tool in tools_enabled:
            if tool in self.tool_categories:
                tool_info = self.tool_categories[tool]
                phase = tool_info["execution_phase"]
                tools_by_phase[phase].append(tool)
        
        # Generate execution plan for each phase
        phase_order = [
            ExecutionPhase.DISCOVERY,
            ExecutionPhase.ENGAGEMENT, 
            ExecutionPhase.CONVERSION,
            ExecutionPhase.SUPPORT
        ]
        
        for phase in phase_order:
            phase_tools = tools_by_phase[phase]
            if not phase_tools:
                continue
            
            # Sort tools within phase by priority
            phase_tools.sort(key=lambda t: self.tool_priorities.get(t, 0), reverse=True)
            
            for tool in phase_tools:
                tool_info = self.tool_categories[tool]
                
                execution = ToolExecution(
                    tool_name=tool,
                    execution_phase=phase,
                    trigger_condition=self._get_trigger_condition(tool, phase),
                    priority=tool_info["priority"],
                    required=self._is_tool_required(tool, tools_enabled),
                    depends_on=self._get_dependencies(tool, tools_enabled),
                    timeout_seconds=self._get_tool_timeout(tool),
                    retry_attempts=self._get_retry_attempts(tool)
                )
                execution_plan.append(execution)
        
        logger.info(f"Generated execution plan with {len(execution_plan)} tools across {len([p for p in phase_order if tools_by_phase[p]])} phases")
        return execution_plan
    
    def _validate_tools(self, tools_enabled: List[str]) -> None:
        """Validate that all tools are recognized and properly configured"""
        unknown_tools = [tool for tool in tools_enabled if tool not in self.tool_categories]
        if unknown_tools:
            raise ValueError(f"Unknown tools: {unknown_tools}")
        
        # Validate tool dependencies
        for tool in tools_enabled:
            tool_info = self.tool_categories[tool]
            dependencies = tool_info.get("dependencies", [])
            missing_deps = [dep for dep in dependencies if dep not in tools_enabled]
            if missing_deps:
                logger.warning(f"Tool '{tool}' has missing dependencies: {missing_deps}")
    
    def _can_achieve_goal(self, goal: ConversationGoal, tools_enabled: List[str]) -> bool:
        """Check if a goal can be achieved with the available tools"""
        required_tools = goal.required_tools
        if not required_tools:
            return True  # Goal doesn't require specific tools
        
        return any(tool in tools_enabled for tool in required_tools)
    
    def _get_success_criteria(self, goal_name: str) -> Tuple[List[str], List[str]]:
        """Get success and fallback criteria for a goal"""
        metrics = self.success_metrics.get(goal_name, {})
        success = metrics.get("success", [])
        fallback = metrics.get("fallback", [])
        return success, fallback
    
    def _estimate_total_duration(self, tool_execution_order: List[ToolExecution], goal: ConversationGoal) -> int:
        """Estimate total conversation duration based on tools and goal"""
        # Start with goal's estimated completion time
        base_duration = goal.estimated_completion_time
        
        # Add overhead for each tool execution
        tool_overhead = len(tool_execution_order) * 15  # 15 seconds per tool
        
        # Add phase overhead
        phases_used = set(tool.execution_phase for tool in tool_execution_order)
        phase_overhead = len(phases_used) * 30  # 30 seconds per phase transition
        
        total_duration = base_duration + tool_overhead + phase_overhead
        return total_duration
    
    def _infer_business_type(self, tools_enabled: List[str], goal: ConversationGoal) -> str:
        """Infer business type from tool combination and goal"""
        if "product_catalog" in tools_enabled and goal.name == "complete_purchase":
            return "ecommerce"
        elif "service_catalog" in tools_enabled and goal.name == "book_appointment":
            return "service_business"
        elif "event_catalog" in tools_enabled:
            return "event_business"
        elif "property_catalog" in tools_enabled:
            return "real_estate"
        elif goal.name == "book_appointment":
            return "appointment_based"
        else:
            return "information_business"
    
    def _get_trigger_condition(self, tool: str, phase: ExecutionPhase) -> str:
        """Get trigger condition for tool execution"""
        trigger_mapping = {
            ExecutionPhase.DISCOVERY: "customer_inquiry_received",
            ExecutionPhase.ENGAGEMENT: "customer_shows_interest", 
            ExecutionPhase.CONVERSION: "customer_ready_to_act",
            ExecutionPhase.SUPPORT: "action_completed"
        }
        return trigger_mapping.get(phase, "manual_trigger")
    
    def _is_tool_required(self, tool: str, tools_enabled: List[str]) -> bool:
        """Determine if a tool is required for the conversation goal"""
        tool_info = self.tool_categories.get(tool, {})
        # Action tools are generally required, catalog tools depend on context
        return tool_info.get("category") == ToolCategory.ACTION
    
    def _get_dependencies(self, tool: str, tools_enabled: List[str]) -> List[str]:
        """Get actual dependencies for a tool based on what's enabled"""
        tool_info = self.tool_categories.get(tool, {})
        all_dependencies = tool_info.get("dependencies", [])
        # Only return dependencies that are actually enabled
        return [dep for dep in all_dependencies if dep in tools_enabled]
    
    def _get_tool_timeout(self, tool: str) -> int:
        """Get timeout for tool execution"""
        timeout_mapping = {
            "payment": 60,  # Payment can take longer
            "appointment_booking": 45,  # Calendar operations can be slow
            "product_catalog": 30,
            "service_catalog": 30,
            "event_catalog": 30,
            "property_catalog": 30,
            "lead_capture": 20,
            "email_notification": 15,
            "sms_notification": 10
        }
        return timeout_mapping.get(tool, 30)
    
    def _get_retry_attempts(self, tool: str) -> int:
        """Get retry attempts for tool execution"""
        retry_mapping = {
            "payment": 3,  # Payment is critical, retry more
            "appointment_booking": 3,  # Appointments are important
            "product_catalog": 2,
            "service_catalog": 2,
            "event_catalog": 2,
            "property_catalog": 2,
            "lead_capture": 2,
            "email_notification": 1,  # Notifications can fail gracefully
            "sms_notification": 1
        }
        return retry_mapping.get(tool, 2)
    
    def get_priority_summary(self, result: ToolPriorityResult) -> Dict[str, Any]:
        """Get a human-readable summary of the priority analysis"""
        return {
            "conversation_goal": {
                "name": result.conversation_goal.name,
                "description": result.conversation_goal.description,
                "priority": result.conversation_goal.priority,
                "estimated_time_minutes": result.conversation_goal.estimated_completion_time // 60
            },
            "execution_strategy": {
                "total_tools": len(result.tool_execution_order),
                "phases_used": list(set(tool.execution_phase.value for tool in result.tool_execution_order)),
                "critical_tools": [tool.tool_name for tool in result.tool_execution_order if tool.required],
                "estimated_duration_minutes": result.estimated_duration // 60
            },
            "success_metrics": {
                "primary_success": result.success_criteria,
                "fallback_success": result.fallback_criteria
            },
            "business_context": {
                "business_type": result.business_type,
                "revenue_impact": "high" if result.conversation_goal.priority >= 90 else "medium" if result.conversation_goal.priority >= 80 else "low"
            }
        }


# # Testing functions
# def test_tool_priority_system():
#     """Test the tool priority system with different tool combinations"""
#     priority_system = ToolPriority()
    
#     test_cases = [
#         ("E-commerce", ["product_catalog", "payment", "email_notification"]),
#         ("Service Business", ["service_catalog", "appointment_booking"]),
#         ("Event Business", ["event_catalog", "payment"]),
#         ("Real Estate", ["property_catalog", "lead_capture"]),
#         ("Simple Info", ["service_catalog"])  # Edge case
#     ]
    
#     results = {}
    
#     for business_name, tools in test_cases:
#         try:
#             result = priority_system.analyze_tool_combination(tools)
#             summary = priority_system.get_priority_summary(result)
#             results[business_name] = summary
            
#             logger.info(f"Analysis complete for {business_name}: Goal={result.conversation_goal.name}")
            
#         except Exception as e:
#             logger.error(f"Failed to analyze {business_name}: {e}")
#             results[business_name] = {"error": str(e)}
    
#     return results


# if __name__ == "__main__":
#     # Quick test of the Tool Priority System
#     logger.info("Testing Tool Priority System v2.0")
    
#     results = test_tool_priority_system()
    
#     for business_name, result in results.items():
#         print(f"\n{'='*60}")
#         print(f"Business: {business_name.upper()}")
#         print(f"{'='*60}")
        
#         if "error" in result:
#             print(f"Error: {result['error']}")
#             continue
        
#         goal = result["conversation_goal"]
#         strategy = result["execution_strategy"]
#         metrics = result["success_metrics"]
#         context = result["business_context"]
        
#         print(f"🎯 Goal: {goal['name']} (Priority: {goal['priority']})")
#         print(f"📝 Description: {goal['description']}")
#         print(f"⏱️  Estimated Time: {goal['estimated_time_minutes']} minutes")
#         print(f"\n🔧 Execution Strategy:")
#         print(f"   Tools: {strategy['total_tools']}")
#         print(f"   Phases: {', '.join(strategy['phases_used'])}")
#         print(f"   Critical Tools: {', '.join(strategy['critical_tools'])}")
#         print(f"   Total Duration: {strategy['estimated_duration_minutes']} minutes")
#         print(f"\n📊 Success Metrics:")
#         print(f"   Primary: {', '.join(metrics['primary_success'])}")
#         print(f"   Fallback: {', '.join(metrics['fallback_success'])}")
#         print(f"\n🏢 Business Context:")
#         print(f"   Type: {context['business_type']}")
#         print(f"   Revenue Impact: {context['revenue_impact']}")