# src/dealflow/intelligence/prompt_intelligence.py
"""
Prompt Intelligence Engine v2.0 - Dynamic System Prompt Generation

Automatically generates contextual, business-specific system prompts from
conversation flows and business configuration. Follows "Smart Simplicity" approach:
- Business-aware (company info + business type)
- Tool-aware (available tools + execution order)  
- Goal-focused (primary objective + success criteria)
- Professional tone (consistent across all businesses)

Integrates seamlessly with CAMEL's BaseMessage system.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

from dealflow.intelligence.flow_intelligence import ConversationFlow, FlowStep
from dealflow.utils.logger import logger


@dataclass
class PromptComponents:
    """Components that make up a complete system prompt"""
    agent_identity: str
    company_context: str
    business_capabilities: str
    conversation_strategy: str
    tool_guidelines: str
    success_criteria: str
    conversation_rules: str


@dataclass
class BusinessContext:
    """Business context for prompt generation"""
    company_name: str
    agent_name: str
    agent_role: str
    company_description: str
    company_values: Optional[str] = None
    conversation_purpose: Optional[str] = None


class PromptIntelligence:
    """
    Core engine that generates dynamic system prompts from conversation flows.
    
    Key Innovation: Instead of hardcoded prompts, this engine analyzes flows
    and business context to generate contextual system prompts automatically.
    
    Design Principles:
    - Smart Simplicity (80% results, 20% complexity)
    - Business-aware but not business-specific
    - Tool-aware with clear execution guidance
    - Goal-focused with measurable success criteria
    - Professional tone for consistency
    """
    
    def __init__(self):
        self.prompt_templates = self._initialize_prompt_templates()
        self.business_type_strategies = self._initialize_business_strategies()
        self.tool_guidelines = self._initialize_tool_guidelines()
        self.prompt_cache = {}  # Cache for performance
        
        logger.info("Prompt Intelligence Engine v2.0 initialized")
    
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize core prompt templates"""
        return {
            "agent_identity": """Never forget your name is {agent_name}. You work as a {agent_role} at {company_name}.

{company_description}

{company_values}""",

            "conversation_strategy_base": """Your primary goal is to {primary_goal}. Success means: {success_criteria}.

Conversation Strategy:
{strategy_steps}

Always maintain a professional, helpful tone while guiding the conversation toward your goal.""",

            "tool_guidelines_base": """Available Tools:
{available_tools}

Tool Usage Rules:
{tool_rules}

CRITICAL: Only recommend products/services that exist in our catalog. Always search before making specific recommendations.""",

            "conversation_rules": """Conversation Guidelines:
- Keep responses concise and engaging (2-3 sentences typically)
- Ask one question at a time to avoid overwhelming the customer
- Listen actively and acknowledge customer needs
- Be helpful and solution-oriented
- If you cannot help with something, politely explain and suggest alternatives
- End conversations naturally when goals are achieved or customer is not interested

When you complete your objective or the conversation naturally ends, include <END_OF_CONVERSATION> in your response."""
        }
    
    def _initialize_business_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize conversation strategies by business type and goal"""
        return {
            "complete_purchase": {
                "description": "guide customers through product selection and purchase",
                "strategy_steps": [
                    "1. Understand customer needs through thoughtful questions",
                    "2. Search and recommend the best matching products from our catalog", 
                    "3. Address any concerns or questions about your recommendations",
                    "4. Guide them through the purchase process when they're ready",
                    "5. Complete the transaction and provide confirmation with next steps"
                ],
                "success_criteria": "payment completed, purchase confirmed, receipt provided"
            },
            "book_appointment": {
                "description": "understand customer needs and schedule appropriate appointments",
                "strategy_steps": [
                    "1. Understand their specific needs, problems, or goals",
                    "2. Explain relevant services and their benefits",
                    "3. Recommend the most appropriate service or specialist", 
                    "4. Check availability and schedule the appointment",
                    "5. Confirm appointment details and provide preparation instructions"
                ],
                "success_criteria": "appointment scheduled, calendar invite sent, confirmation provided"
            },
            "capture_qualified_lead": {
                "description": "provide valuable information and capture contact details for follow-up",
                "strategy_steps": [
                    "1. Understand their interests, requirements, and timeline",
                    "2. Provide relevant information about our offerings",
                    "3. Assess their level of interest and decision-making process",
                    "4. Collect contact information for personalized follow-up",
                    "5. Set clear expectations for next steps and follow-up timing"
                ],
                "success_criteria": "contact information collected, lead qualified, follow-up scheduled"
            },
            "provide_information_and_build_interest": {
                "description": "answer questions and provide helpful information about our offerings",
                "strategy_steps": [
                    "1. Listen carefully to understand what information they need",
                    "2. Provide comprehensive, accurate information from our catalog",
                    "3. Highlight key benefits and value propositions",
                    "4. Answer follow-up questions thoroughly", 
                    "5. Gauge interest and offer appropriate next steps"
                ],
                "success_criteria": "questions answered, information provided, customer satisfied"
            }
        }
    
    def _initialize_tool_guidelines(self) -> Dict[str, Dict[str, str]]:
        """Initialize tool-specific guidelines and usage patterns"""
        return {
            "product_catalog": {
                "description": "Search and recommend products from our catalog",
                "usage_rule": "Always search the catalog before making product recommendations",
                "execution_order": "1"
            },
            "service_catalog": {
                "description": "Search and explain services from our catalog", 
                "usage_rule": "Always search services before recommending specific options",
                "execution_order": "1"
            },
            "event_catalog": {
                "description": "Search and recommend events from our catalog",
                "usage_rule": "Always search events before providing specific recommendations",
                "execution_order": "1"
            },
            "property_catalog": {
                "description": "Search and recommend properties from our catalog",
                "usage_rule": "Always search properties before making specific recommendations", 
                "execution_order": "1"
            },
            "payment": {
                "description": "Process secure payments and transactions",
                "usage_rule": "Only process payments after customer confirms purchase intent",
                "execution_order": "3"
            },
            "appointment_booking": {
                "description": "Schedule appointments and check availability",
                "usage_rule": "Check availability before confirming any appointment times",
                "execution_order": "3"
            },
            "lead_capture": {
                "description": "Collect contact information for follow-up",
                "usage_rule": "Only request contact info after establishing genuine interest",
                "execution_order": "3"
            },
            "email_notification": {
                "description": "Send email confirmations and notifications",
                "usage_rule": "Send confirmations after completing transactions or bookings",
                "execution_order": "4"
            },
            "sms_notification": {
                "description": "Send SMS confirmations and reminders",
                "usage_rule": "Send SMS for time-sensitive confirmations only",
                "execution_order": "4"
            }
        }
    
    def generate_system_prompt(
        self, 
        flow: ConversationFlow, 
        business_context: BusinessContext,
        tools_enabled: List[str]
    ) -> str:
        """
        Generate complete system prompt from flow and business context.
        
        Args:
            flow: Generated conversation flow
            business_context: Business information
            tools_enabled: List of enabled tools
            
        Returns:
            Complete system prompt ready for CAMEL BaseMessage
        """
        logger.info(f"Generating system prompt for {flow.business_type} business with {len(tools_enabled)} tools")
        
        # Check cache first
        cache_key = self._generate_cache_key(flow.flow_id, business_context, tools_enabled)
        if cache_key in self.prompt_cache:
            logger.debug("Returning cached prompt")
            return self.prompt_cache[cache_key]
        
        # Generate prompt components
        components = self._generate_prompt_components(flow, business_context, tools_enabled)
        
        # Assemble complete prompt
        complete_prompt = self._assemble_prompt(components)
        
        # Cache the result
        self.prompt_cache[cache_key] = complete_prompt
        
        logger.info(f"Generated system prompt: {len(complete_prompt)} characters")
        return complete_prompt
    
    def _generate_prompt_components(
        self, 
        flow: ConversationFlow, 
        business_context: BusinessContext,
        tools_enabled: List[str]
    ) -> PromptComponents:
        """Generate all components of the system prompt"""
        
        # 1. Agent Identity
        agent_identity = self._generate_agent_identity(business_context)
        
        # 2. Company Context (already in agent identity)
        company_context = ""
        
        # 3. Business Capabilities  
        business_capabilities = self._generate_business_capabilities(flow, tools_enabled)
        
        # 4. Conversation Strategy
        conversation_strategy = self._generate_conversation_strategy(flow)
        
        # 5. Tool Guidelines
        tool_guidelines = self._generate_tool_guidelines(tools_enabled)
        
        # 6. Success Criteria
        success_criteria = self._generate_success_criteria(flow)
        
        # 7. Conversation Rules
        conversation_rules = self.prompt_templates["conversation_rules"]
        
        return PromptComponents(
            agent_identity=agent_identity,
            company_context=company_context,
            business_capabilities=business_capabilities,
            conversation_strategy=conversation_strategy,
            tool_guidelines=tool_guidelines,
            success_criteria=success_criteria,
            conversation_rules=conversation_rules
        )
    
    def _generate_agent_identity(self, business_context: BusinessContext) -> str:
        """Generate agent identity section"""
        company_values_text = ""
        if business_context.company_values:
            company_values_text = f"\nOur values: {business_context.company_values}"
        
        return self.prompt_templates["agent_identity"].format(
            agent_name=business_context.agent_name,
            agent_role=business_context.agent_role,
            company_name=business_context.company_name,
            company_description=business_context.company_description,
            company_values=company_values_text
        )
    
    def _generate_business_capabilities(self, flow: ConversationFlow, tools_enabled: List[str]) -> str:
        """Generate business capabilities description based on tools"""
        capabilities = []
        
        # Catalog capabilities
        if "product_catalog" in tools_enabled:
            capabilities.append("searching and recommending products from our catalog")
        if "service_catalog" in tools_enabled:
            capabilities.append("explaining our services and their benefits")
        if "event_catalog" in tools_enabled:
            capabilities.append("finding and suggesting events that match customer interests")
        if "property_catalog" in tools_enabled:
            capabilities.append("searching and presenting properties that meet customer criteria")
        
        # Action capabilities
        if "payment" in tools_enabled:
            capabilities.append("processing secure payments and completing purchases")
        if "appointment_booking" in tools_enabled:
            capabilities.append("scheduling appointments and consultations")
        if "lead_capture" in tools_enabled:
            capabilities.append("collecting contact information for personalized follow-up")
        
        if not capabilities:
            capabilities = ["providing information and answering questions"]
        
        # Format capabilities naturally
        if len(capabilities) == 1:
            capability_text = capabilities[0]
        elif len(capabilities) == 2:
            capability_text = f"{capabilities[0]} and {capabilities[1]}"
        else:
            capability_text = f"{', '.join(capabilities[:-1])}, and {capabilities[-1]}"
        
        return f"You help customers by {capability_text}."
    
    def _generate_conversation_strategy(self, flow: ConversationFlow) -> str:
        """Generate conversation strategy based on flow primary goal"""
        strategy_config = self.business_type_strategies.get(flow.primary_goal)
        
        if not strategy_config:
            # Fallback strategy
            strategy_config = self.business_type_strategies["provide_information_and_build_interest"]
        
        strategy_steps_text = "\n".join(strategy_config["strategy_steps"])
        
        return self.prompt_templates["conversation_strategy_base"].format(
            primary_goal=strategy_config["description"],
            success_criteria=strategy_config["success_criteria"],
            strategy_steps=strategy_steps_text
        )
    
    def _generate_tool_guidelines(self, tools_enabled: List[str]) -> str:
        """Generate tool guidelines and usage rules"""
        if not tools_enabled:
            return ""
        
        # Get tool descriptions and rules
        available_tools = []
        tool_rules = []
        
        # Sort tools by execution order for logical presentation
        sorted_tools = sorted(
            tools_enabled, 
            key=lambda t: int(self.tool_guidelines.get(t, {}).get("execution_order", "5"))
        )
        
        for tool in sorted_tools:
            tool_info = self.tool_guidelines.get(tool, {})
            if tool_info:
                available_tools.append(f"- {tool}: {tool_info['description']}")
                tool_rules.append(f"- {tool_info['usage_rule']}")
        
        if not available_tools:
            return ""
        
        available_tools_text = "\n".join(available_tools)
        tool_rules_text = "\n".join(tool_rules)
        
        return self.prompt_templates["tool_guidelines_base"].format(
            available_tools=available_tools_text,
            tool_rules=tool_rules_text
        )
    
    def _generate_success_criteria(self, flow: ConversationFlow) -> str:
        """Generate success criteria section"""
        criteria_text = ", ".join(flow.completion_criteria)
        return f"Your success is measured by: {criteria_text}."
    
    def _assemble_prompt(self, components: PromptComponents) -> str:
        """Assemble all components into a complete system prompt"""
        prompt_sections = []
        
        # 1. Agent Identity (always first)
        prompt_sections.append(components.agent_identity)
        
        # 2. Business Capabilities
        if components.business_capabilities:
            prompt_sections.append(components.business_capabilities)
        
        # 3. Conversation Strategy  
        if components.conversation_strategy:
            prompt_sections.append(components.conversation_strategy)
        
        # 4. Tool Guidelines
        if components.tool_guidelines:
            prompt_sections.append(components.tool_guidelines)
        
        # 5. Conversation Rules (always last)
        prompt_sections.append(components.conversation_rules)
        
        # Join with double newlines for readability
        complete_prompt = "\n\n".join(prompt_sections)
        
        return complete_prompt
    
    def _generate_cache_key(
        self, 
        flow_id: str, 
        business_context: BusinessContext,
        tools_enabled: List[str]
    ) -> str:
        """Generate cache key for prompt caching"""
        tools_str = "_".join(sorted(tools_enabled))
        context_key = f"{business_context.company_name}_{business_context.agent_name}_{business_context.agent_role}"
        return f"{flow_id}_{context_key}_{tools_str}"
    
    def create_camel_system_message(
        self, 
        flow: ConversationFlow,
        business_context: BusinessContext,
        tools_enabled: List[str]
    ) -> str:
        """
        Create system prompt optimized for CAMEL BaseMessage.
        
        This is the main interface method that other components will use.
        Returns a string ready to be wrapped in BaseMessage.make_assistant_message()
        
        Args:
            flow: Generated conversation flow
            business_context: Business information  
            tools_enabled: List of enabled tools
            
        Returns:
            System prompt string ready for CAMEL BaseMessage
        """
        return self.generate_system_prompt(flow, business_context, tools_enabled)
    
    def get_prompt_summary(
        self,
        flow: ConversationFlow,
        business_context: BusinessContext, 
        tools_enabled: List[str]
    ) -> Dict[str, Any]:
        """Get a summary of the generated prompt for debugging/analysis"""
        prompt = self.generate_system_prompt(flow, business_context, tools_enabled)
        
        return {
            "flow_id": flow.flow_id,
            "business_type": flow.business_type,
            "primary_goal": flow.primary_goal,
            "tools_count": len(tools_enabled),
            "tools_enabled": tools_enabled,
            "prompt_length": len(prompt),
            "prompt_sections": [
                "agent_identity",
                "business_capabilities", 
                "conversation_strategy",
                "tool_guidelines",
                "conversation_rules"
            ],
            "cache_key": self._generate_cache_key(flow.flow_id, business_context, tools_enabled)
        }
    
    def clear_cache(self) -> None:
        """Clear the prompt cache"""
        self.prompt_cache.clear()
        logger.info("Prompt cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_prompts": len(self.prompt_cache),
            "cache_keys": list(self.prompt_cache.keys())
        }


# # Testing and example functions
# def create_test_business_contexts() -> Dict[str, BusinessContext]:
#     """Create test business contexts for different scenarios"""
#     return {
#         "ecommerce": BusinessContext(
#             company_name="TechGear Pro",
#             agent_name="Alex",
#             agent_role="Sales Consultant", 
#             company_description="We sell premium electronics and tech accessories for professionals and enthusiasts.",
#             company_values="Quality, innovation, and customer satisfaction are our core values.",
#             conversation_purpose="help customers find the perfect tech solutions for their needs"
#         ),
#         "service_business": BusinessContext(
#             company_name="Legal Solutions Inc",
#             agent_name="Sarah",
#             agent_role="Legal Consultant",
#             company_description="We provide comprehensive legal services for small businesses and individuals.",
#             company_values="Integrity, expertise, and personalized service.",
#             conversation_purpose="understand legal needs and schedule appropriate consultations"
#         ),
#         "event_business": BusinessContext(
#             company_name="Epic Events",
#             agent_name="Mike", 
#             agent_role="Event Specialist",
#             company_description="We organize and host amazing events, from corporate conferences to private parties.",
#             company_values="Creativity, attention to detail, and unforgettable experiences.",
#             conversation_purpose="help customers discover and book the perfect events"
#         ),
#         "real_estate": BusinessContext(
#             company_name="Prime Properties",
#             agent_name="Jennifer",
#             agent_role="Real Estate Agent",
#             company_description="We help clients find their dream homes and investment properties in prime locations.",
#             company_values="Trust, expertise, and personalized service for every client.",
#             conversation_purpose="understand property needs and provide qualified leads to our specialists"
#         )
#     }


# def test_prompt_generation():
#     """Test prompt generation with different business types and tool combinations"""
#     # Import flow intelligence for testing
#     from dealflow.intelligence.flow_intelligence import FlowIntelligence
    
#     prompt_engine = PromptIntelligence()
#     flow_engine = FlowIntelligence()
#     business_contexts = create_test_business_contexts()
    
#     test_cases = [
#         ("ecommerce", ["product_catalog", "payment", "email_notification"]),
#         ("service_business", ["service_catalog", "appointment_booking"]),
#         ("event_business", ["event_catalog", "payment"]),
#         ("real_estate", ["property_catalog", "lead_capture"])
#     ]
    
#     results = {}
    
#     for business_type, tools in test_cases:
#         try:
#             # Generate flow
#             flow = flow_engine.generate_conversation_flow(tools)
            
#             # Get business context
#             business_context = business_contexts[business_type]
            
#             # Generate prompt
#             prompt = prompt_engine.generate_system_prompt(flow, business_context, tools)
            
#             # Get summary
#             summary = prompt_engine.get_prompt_summary(flow, business_context, tools)
            
#             results[business_type] = {
#                 "summary": summary,
#                 "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
#                 "full_prompt_length": len(prompt)
#             }
            
#             logger.info(f"Generated prompt for {business_type}: {len(prompt)} characters")
            
#         except Exception as e:
#             logger.error(f"Failed to generate prompt for {business_type}: {e}")
#             results[business_type] = {"error": str(e)}
    
#     return results


# if __name__ == "__main__":
#     # Quick test of the Prompt Intelligence Engine
#     logger.info("Testing Prompt Intelligence Engine v2.0")
    
#     # Test prompt generation
#     results = test_prompt_generation()
    
#     for business_type, result in results.items():
#         print(f"\n{'='*50}")
#         print(f"Business Type: {business_type.upper()}")
#         print(f"{'='*50}")
        
#         if "error" in result:
#             print(f"Error: {result['error']}")
#             continue
            
#         summary = result["summary"]
#         print(f"Flow ID: {summary['flow_id']}")
#         print(f"Primary Goal: {summary['primary_goal']}")
#         print(f"Tools: {summary['tools_enabled']}")
#         print(f"Prompt Length: {summary['prompt_length']} characters")
#         print(f"\nPrompt Preview:")
#         print(result["prompt_preview"])
    
#     # Test caching
#     prompt_engine = PromptIntelligence()
#     print(f"\nCache stats: {prompt_engine.get_cache_stats()}")