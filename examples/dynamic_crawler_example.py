"""
dynamic_crawler_example.py

Example script demonstrating the intelligent crawler for extracting product/service 
information from any website to use with DealFlow.
"""

import os
import sys
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from dealflow import DealFlow
from dealflow.knowledge_base.intelligent_crawler import ingest_and_save, load_cached_entities

# Add parent directory to path to allow imports when running from examples directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def run_crawler_example(domain_url, company_name=None):
    """Run the crawler example with the given domain URL."""
    
    # Extract domain name from URL for file naming
    import re
    domain_name = re.sub(r'https?://(www\.)?', '', domain_url).rstrip('/')
    domain_name = re.sub(r'[^\w]', '_', domain_name)
    
    # Define cache paths
    cache_dir = "client_cache"
    cache_entities_path = f"{cache_dir}/{domain_name}_entities.json"
    dynamic_catalog_file = f"{cache_dir}/{domain_name}_product_catalog.txt"
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    # Initialize the model
    print(f"Initializing model for {domain_url}...")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    # Check if we already have cached entities
    if os.path.exists(cache_entities_path):
        print(f"Loading {len(load_cached_entities(cache_entities_path))} entities from cache...")
        entities = load_cached_entities(cache_entities_path)
    else:
        # No cache, run the intelligent crawler
        print(f"No cache found. Starting intelligent crawling of {domain_url}...")
        entities = ingest_and_save(
            domain=domain_url,
            model=model,
            cache_path=cache_entities_path,
            max_pages=30  # Limit for example purposes
        )
    
    if not entities:
        print("No entities were found or extracted. Exiting...")
        return
    
    print(f"Successfully loaded {len(entities)} entities from {domain_url}")
    
    # Print summary of entities found
    entity_types = {}
    for entity in entities:
        entity_type = entity.entity_type.value
        if entity_type not in entity_types:
            entity_types[entity_type] = 0
        entity_types[entity_type] += 1
    
    print("\nEntity Types Summary:")
    for entity_type, count in entity_types.items():
        print(f"  - {entity_type.capitalize()}: {count}")
    
    print("\nSample Entities:")
    for i, entity in enumerate(entities[:3]):  # Show first 3 entities
        print(f"\n--- Entity {i+1} ---")
        print(f"Name: {entity.name}")
        print(f"Type: {entity.entity_type.value}")
        print(f"Price: {entity.price if entity.price else 'Not specified'}")
        if entity.description:
            print(f"Description: {entity.description[:100]}..." if len(entity.description) > 100 else entity.description)
        if entity.properties:
            print("Properties:")
            for key, value in entity.properties.items():
                print(f"  - {key}: {value}")
    
    # Use the extracted information with DealFlow
    if company_name is None:
        # Use domain name as company name if not provided
        company_name = domain_name.replace('_', ' ').title()
    
    print(f"\nInitializing DealFlow sales agent with data from {domain_url}...")
    sales_agent = DealFlow(
        model=model,
        salesperson_name="Alex Johnson",
        salesperson_role="Sales Representative",
        company_name="Yanmar",
        company_business="Yanmar is a global manufacturer of world-class products in a wide range of applications including tractors, construction equipment, generators, energy systems, climate control systems, aquafarming systems, as well as marine engines and propulsion systems.",
        company_values="Yanmar's innovative designs and products are designed with a never-ending focus on reliability and performance.",
        conversation_purpose="help customers find the right Yanmar tractor or service for their requirements",
        use_tools=True,
        product_catalog=dynamic_catalog_file,
        verbose=True
    )

    # Start DealFlow conversation
    sales_agent.seed_agent()
    
    # Interactive conversation loop
    print("\n" + "="*50)
    print(f"Welcome to the DealFlow conversation for {company_name}.")
    print("Type 'exit' to end the conversation.")
    print("="*50 + "\n")
    
    while True:
        # Get human input
        human_input = input("You: ")
        
        if human_input.lower() == 'exit':
            print("Ending conversation.")
            break
        
        # Get response from sales agent
        response = sales_agent.step(human_input)
        
        # Clean up response for display
        cleaned_response = response
        # Print response
        print(f"Alex: {cleaned_response}")
        
        # Check if conversation has ended
        if "<END_OF_CALL>" in response:
            print("Sales agent has ended the conversation.")
            break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the DealFlow intelligent crawler on a domain")
    parser.add_argument("domain", help="The domain URL to crawl (e.g., https://example.com)")
    parser.add_argument("--company", help="Company name (defaults to domain name)")
    
    args = parser.parse_args()
    
    run_crawler_example(args.domain, args.company)