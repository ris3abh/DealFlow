"""
intelligent_crawler_example.py

Example script demonstrating the enhanced intelligent crawler integration with DealFlow.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from dealflow import DealFlow
from dealflow.knowledge_base.integration import setup_knowledge_from_domain
from dealflow.utils.logger import logger, setup_logger

# Set up logging with more detailed output
setup_logger(level=20)  # INFO level

# Add parent directory to path to allow imports when running from examples directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def run_intelligent_crawler_demo(args):
    """Run a demo of the intelligent crawler with DealFlow integration."""
    
    domain_url = args.domain
    company_name = args.company
    max_pages = args.max_pages
    force_refresh = args.force_refresh
    
    print(f"\n{'=' * 60}")
    print(f"INTELLIGENT CRAWLER DEMO: {domain_url}")
    print(f"{'=' * 60}\n")
    
    # Extract company name from domain if not provided
    if not company_name:
        import re
        company_name = re.sub(r'https?://(www\.)?', '', domain_url).split('.')[0]
        company_name = company_name.replace('-', ' ').replace('_', ' ').title()
    
    print(f"Company Name: {company_name}")
    print(f"Max Pages to Crawl: {max_pages}")
    print(f"Force Refresh: {force_refresh}")
    print("\nInitializing model...")
    
    # Initialize the model
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    print("\n1. Setting up knowledge base from domain...")
    print(f"   - Starting intelligent crawling of {domain_url}")
    
    # Set up knowledge base
    try:
        retriever, catalog_path = setup_knowledge_from_domain(
            domain_url=domain_url,
            model=model,
            force_refresh=force_refresh,
            max_pages=max_pages
        )
        
        # Get product names
        product_names = retriever.get_all_product_names()
        
        print(f"\n   - Successfully extracted {len(product_names)} products/services")
        print("   - Sample products/services:")
        for i, name in enumerate(product_names[:5]):
            print(f"     {i+1}. {name}")
        if len(product_names) > 5:
            print(f"     ... and {len(product_names) - 5} more")
            
        print(f"\n   - Product catalog saved at: {catalog_path}")
        
    except Exception as e:
        print(f"\nError setting up knowledge base: {e}")
        print("Exiting demo...")
        return
    
    print("\n2. Initializing DealFlow sales agent...")
    # Initialize DealFlow
    sales_agent = DealFlow(
        model=model,
        salesperson_name="Alex Johnson",
        salesperson_role="Sales Representative",
        company_name=company_name,
        company_business=f"Provider of various products and services to meet customer needs",
        company_values="Helping customers find the perfect solutions for their needs with integrity and excellent service",
        conversation_purpose="assist customers in finding the right products or services",
        use_tools=True,
        product_catalog=catalog_path,
        verbose=args.verbose
    )
    
    # Seed the agent
    sales_agent.seed_agent()
    print("   - Sales agent successfully initialized and seeded")
    
    print("\n3. Starting interactive conversation...\n")
    print(f"{'=' * 60}")
    print("Welcome to the intelligent DealFlow conversation.")
    print(f"You're now chatting with Alex from {company_name}.")
    print("(Type 'exit' to end the conversation)")
    print(f"{'=' * 60}\n")
    
    # Interactive conversation loop
    while True:
        # Get human input
        human_input = input("You: ")
        
        if human_input.lower() in ['exit', 'quit', 'bye']:
            print("\nEnding conversation.")
            break
        
        try:
            # Get response from sales agent
            response = sales_agent.step(human_input)
            
            # Print response
            print(f"Alex: {response}")
            
            # Check if conversation has ended
            if "<END_OF_CALL>" in response:
                print("\nSales agent has ended the conversation.")
                break
                
        except Exception as e:
            print(f"\nError during conversation: {e}")
            print("Continuing conversation...")
    
    print(f"\n{'=' * 60}")
    print("Demo completed successfully!")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the DealFlow intelligent crawler demo")
    parser.add_argument("domain", help="The domain URL to crawl (e.g., https://example.com)")
    parser.add_argument("--company", help="Company name (defaults to domain name)")
    parser.add_argument("--max-pages", type=int, default=30, help="Maximum number of pages to crawl")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh of cached data")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    run_intelligent_crawler_demo(args)