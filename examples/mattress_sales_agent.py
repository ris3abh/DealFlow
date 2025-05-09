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
        salesperson_name="Sarah Mills",
        salesperson_role="Sleep Consultant",
        company_name="Sleep Haven",
        company_business="We provide premium mattresses and sleep solutions for all types of sleepers.",
        company_values="At Sleep Haven, we believe that quality sleep is essential to overall health and well-being. We are committed to helping our customers achieve optimal sleep by offering exceptional products and customer service.",
        conversation_purpose="understand the customer's sleep preferences and recommend the right mattress",
        product_catalog="examples/catalog/mattress_catalog.txt",  # Include the product catalog
        use_tools=True
    )
    
    # Seed the agent to initialize
    sales_agent.seed_agent()
    
    # Simulate a conversation
    print("\n--- Starting conversation ---\n")
    
    # First message
    human_input = "Hi, I'm looking for a new mattress. My current one is causing back pain."
    print(f"Customer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nSarah Mills: {response}")
    
    # Second message
    human_input = "I prefer something firm. And I tend to sleep hot."
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nSarah Mills: {response}")
    
    # Third message
    human_input = "The SupportPlus sounds good. Do you have any other cooling options though?"
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nSarah Mills: {response}")
    
    # Fourth message
    human_input = "And what's your return policy if I don't like it?"
    print(f"\nCustomer: {human_input}")
    
    response = sales_agent.step(human_input)
    print(f"\nSarah Mills: {response}")
    
    print("\n--- Conversation ended ---")
    
    # Show conversation state
    print("\nCurrent conversation stage:", sales_agent.current_conversation_stage.name)

if __name__ == "__main__":
    main()