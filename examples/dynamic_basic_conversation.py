import os
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from dealflow import DealFlow
from dealflow.knowledge_base.crawler_ingestor import load_cached_entities, ingest_and_save

# Load environment variables (FIRECRAWL_API_KEY, OPENAI_API_KEY, etc.)
load_dotenv()

# Define the client domain and cache paths
domain = "https://www.yanmar.com/us/"  # Replace with actual client domain
cache_entities_path = "client_cache/yanmar_entities.json"
dynamic_catalog_file = "client_cache/yanmar_dynamic_product_catalog.txt"

# Ingest dynamic entities if cache does not exist
if os.path.exists(cache_entities_path):
    entities = load_cached_entities(cache_entities_path)
    print(f"Loaded {len(entities)} entities from cache.")
else:
    entities = ingest_and_save(domain, cache_entities_path)
    print(f"Ingested and saved {len(entities)} entities.")

# (Optional) For compatibility with DealFlow's current product catalog loader,
# write the dynamic entities to a text file in a suitable format.
with open(dynamic_catalog_file, "w", encoding="utf-8") as f:
    for entity in entities:
        f.write("Product: " + entity.name + "\n")
        f.write("Description: " + entity.description + "\n")
        if entity.price:
            f.write("Price: $" + str(entity.price) + "\n")
        f.write("\n")

# Initialize the model
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
)

# Initialize DealFlow with the dynamically generated product catalog file.
sales_agent = DealFlow(
    model=model,
    salesperson_name="Alex Johnson",
    salesperson_role="Sales Representative",
    company_name="DynamicClient Inc.",
    company_business="Offering dynamically scraped and up-to-date product information.",
    company_values="Innovation, agility, and transparency.",
    conversation_purpose="help customers discover the best products for their needs.",
    use_tools=True,
    product_catalog=dynamic_catalog_file,  # Use dynamic file in place of static catalog
    verbose=True,
)

sales_agent.seed_agent()

print("Welcome to the Dynamic DealFlow example conversation. Type 'exit' to end.")
print("=" * 50)

while True:
    human_input = input("You: ")
    if human_input.lower() == "exit":
        print("Ending conversation.")
        break
    response = sales_agent.step(human_input)
    print("Alex Johnson:", response)
    if "<END_OF_CALL>" in response:
        print("Sales agent has ended the conversation.")
        break
