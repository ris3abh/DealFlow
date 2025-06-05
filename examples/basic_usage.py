#!/usr/bin/env python3
"""
basic_example.py - Demo of DealFlow with minimal dependencies

This script demonstrates the core functionality of DealFlow using only
the necessary CAMEL dependencies (model_platforms and rag) instead of
the full camel-ai[all] package.

Requirements:
    camel-ai[model_platforms,rag]==0.2.45
    python-dotenv>=1.1.0
    requests>=2.23.3
"""
import os
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from dotenv import load_dotenv

from dealflow import DealFlow

# Load environment variables (for API keys)
load_dotenv()

def main():
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it in your .env file or environment variables.")
        return
    
    print("Initializing model...")
    # Initialize the language model
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    print("Creating sales agent...")
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
    
    print("Seeding the agent...")
    # Start the conversation
    sales_agent.seed_agent()
    
    # Show basic interaction
    print("\n--- Starting conversation ---\n")
    
    # Human input handling
    human_input = "Hi, I got your email about cloud solutions. Can you tell me more?"
    print(f"Customer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nAlex Johnson: {response}")
    
    # Another interaction
    human_input = "We're looking for something scalable. Our current solution doesn't handle traffic spikes well."
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nAlex Johnson: {response}")
    
    print("\n--- Conversation ended ---")
    
    # Show conversation state
    print("\nCurrent conversation stage:", sales_agent.current_conversation_stage.name)

if __name__ == "__main__":
    main()