#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from dealflow import DealFlow

# Load environment variables (for API keys)
load_dotenv()

def main():
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it in your .env file or environment variables.")
        return
    
    # Initialize the language model
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    # Configure the sales agent
    sales_agent = DealFlow(
        model=model,
        salesperson_name="Alex Johnson",
        salesperson_role="Solutions Consultant",
        company_name="TechSolutions Inc.",
        company_business="We provide enterprise-grade cloud computing solutions for businesses of all sizes.",
        company_values="We believe in empowering businesses through technology that's accessible, reliable, and forward-thinking.",
        conversation_purpose="understand the client's cloud infrastructure needs and present our scalable solutions",
        use_tools=True
    )
    
    # Seed the agent to initialize
    sales_agent.seed_agent()
    
    # Simulate a conversation
    print("\n--- Starting conversation ---\n")
    
    # First customer message
    human_input = "Hi, I got your email about cloud solutions. Can you tell me more?"
    print(f"Customer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nAlex Johnson: {response}")
    
    # Second customer message
    human_input = "We're looking for something scalable. Our current solution doesn't handle traffic spikes well."
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nAlex Johnson: {response}")
    
    # Third customer message
    human_input = "What kind of support do you provide? Our team is small and we don't have dedicated IT staff."
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nAlex Johnson: {response}")
    
    print("\n--- Conversation ended ---")
    
    # Show conversation state
    print("\nCurrent conversation stage:", sales_agent.current_conversation_stage.name)

if __name__ == "__main__":
    main()