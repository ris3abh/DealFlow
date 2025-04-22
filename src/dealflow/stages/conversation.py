# dealflow/stages/conversation.py
from enum import Enum
from typing import Dict, Optional

class ConversationStage(Enum):
    """Enumeration of conversation stages in a sales process."""
    INTRODUCTION = "1"
    QUALIFICATION = "2"
    VALUE_PROPOSITION = "3"
    NEEDS_ANALYSIS = "4"
    SOLUTION_PRESENTATION = "5"
    OBJECTION_HANDLING = "6"
    CLOSE = "7"
    END_CONVERSATION = "8"

class ConversationStages:
    """Manages conversation stages for a sales conversation."""
    
    # Detailed descriptions of each stage
    STAGE_DESCRIPTIONS: Dict[ConversationStage, str] = {
        ConversationStage.INTRODUCTION: 
            "Introduction: Start the conversation by introducing yourself and your company. "
            "Be polite and respectful while keeping the tone of the conversation professional. "
            "Your greeting should be welcoming. Always clarify in your greeting the reason why you are contacting the prospect.",
        
        ConversationStage.QUALIFICATION: 
            "Qualification: Qualify the prospect by confirming if they are the right person to talk to "
            "regarding your product/service. Ensure that they have the authority to make purchasing decisions.",
        
        ConversationStage.VALUE_PROPOSITION: 
            "Value proposition: Briefly explain how your product/service can benefit the prospect. "
            "Focus on the unique selling points and value proposition of your product/service that sets it apart from competitors.",
        
        ConversationStage.NEEDS_ANALYSIS: 
            "Needs analysis: Ask open-ended questions to uncover the prospect's needs and pain points. "
            "Listen carefully to their responses and take notes.",
        
        ConversationStage.SOLUTION_PRESENTATION: 
            "Solution presentation: Based on the prospect's needs, present your product/service as the solution "
            "that can address their pain points.",
        
        ConversationStage.OBJECTION_HANDLING: 
            "Objection handling: Address any objections that the prospect may have regarding your product/service. "
            "Be prepared to provide evidence or testimonials to support your claims.",
        
        ConversationStage.CLOSE: 
            "Close: Ask for the sale by proposing a next step. This could be a demo, a trial or a meeting with decision-makers. "
            "Ensure to summarize what has been discussed and reiterate the benefits.",
        
        ConversationStage.END_CONVERSATION: 
            "End conversation: The prospect has to leave the call, the prospect is not interested, "
            "or next steps where already determined by the sales agent."
    }
    
    @classmethod
    def get_stage_description(cls, stage: ConversationStage) -> str:
        """Get the description for a given conversation stage.
        
        Args:
            stage: The conversation stage to get the description for.
            
        Returns:
            The description of the conversation stage.
        """
        return cls.STAGE_DESCRIPTIONS.get(stage, "Unknown stage")
    
    @classmethod
    def get_stage_by_id(cls, stage_id: str) -> Optional[ConversationStage]:
        """Get a conversation stage by its ID.
        
        Args:
            stage_id: The ID of the conversation stage.
            
        Returns:
            The conversation stage if found, None otherwise.
        """
        for stage in ConversationStage:
            if stage.value == stage_id:
                return stage
        return None
    
    @classmethod
    def get_all_stages_as_dict(cls) -> Dict[str, str]:
        """Get all stages as a dictionary of ID -> description.
        
        Returns:
            A dictionary mapping stage IDs to their descriptions.
        """
        return {stage.value: cls.get_stage_description(stage) for stage in ConversationStage}