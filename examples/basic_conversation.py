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
    company_name="Sleep Haven",
    company_business="Sleep Haven is a premium mattress company that provides customers with the most comfortable and supportive sleeping experience possible.",
    company_values="We believe that quality sleep is essential to overall health and well-being.",
    conversation_purpose="help customers find the perfect mattress for their needs",
    use_tools=True,
    product_catalog="examples/product_catalog.txt",
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
    
    # Print response
    print(f"Alex Johnson: {response}")
    
    # Check if conversation has ended
    if "<END_OF_CALL>" in response:
        print("Sales agent has ended the conversation.")
        break