# examples/basic_conversation.py
import os
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from dealflow import DealFlow

# Load environment variables
load_dotenv()

# Initialize model
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
)

# Initialize DealFlow
sales_agent = DealFlow(
    model=model,
    salesperson_name="Alex Johnson",
    salesperson_role="Sales Representative",
    company_name="Yanmar",
    company_business="Yanmar is a global manufacturer of world-class products in a wide range of applications including tractors, construction equipment, generators, energy systems, climate control systems, aquafarming systems, as well as marine engines and propulsion systems.",
    company_values="Yanmar's innovative designs and products are designed with a never-ending focus on reliability and performance.",
    conversation_purpose="help customers find the right Yanmar tractor or service for their requirements",
    use_tools=True,
    product_catalog="examples/yanmar_product_catalog.txt",
    verbose=True,
)

# Start the conversation
sales_agent.seed_agent()

# Run the conversation
print("Welcome to the DealFlow example conversation. Type 'exit' to end.")
print("=" * 50)

while True:
    # Get human input
    human_input = input("You: ")
    
    if human_input.lower() == 'exit':
        print("Ending conversation.")
        break
    
    # Get response from sales agent
    response = sales_agent.step(human_input)
    
    # Remove any thought process from the output for clean display
    cleaned_response = response
    if "Thought: " in response:
        # Extract only the actual response part after the thought process
        parts = response.split(f"{sales_agent.config.get('salesperson_name')}: ")
        if len(parts) > 1:
            cleaned_response = parts[1]
    
    # Print response
    print(f"Alex Johnson: {cleaned_response}")
    
    # Check if conversation has ended
    if "<END_OF_CALL>" in response:
        print("Sales agent has ended the conversation.")
        break