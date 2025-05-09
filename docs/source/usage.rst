Usage
=====

Basic Usage
----------

Here's a simple example of how to use DealFlow:

.. code-block:: python

    from dealflow import DealFlow
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType, ModelType
    
    # Initialize a language model
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
        company_business="We provide enterprise-grade cloud computing solutions.",
        company_values="We believe in empowering businesses through technology.",
        conversation_purpose="understand client needs and present solutions",
        use_tools=True
    )
    
    # Start the conversation
    sales_agent.seed_agent()
    
    # Process a user message
    response = sales_agent.step("Hi, I'm interested in your cloud solutions")
    print(response)

Advanced Features
---------------

Product Catalog Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    sales_agent = DealFlow(
        # ... other parameters ...
        product_catalog="path/to/catalog.txt",
        use_tools=True
    )

Conversation Stages
^^^^^^^^^^^^^^^^^

DealFlow automatically manages different stages of the sales conversation:

1. Introduction
2. Qualification
3. Value Proposition
4. Needs Analysis
5. Solution Presentation
6. Objection Handling
7. Close
8. End Conversation

You can access the current stage with:

.. code-block:: python

    current_stage = sales_agent.current_conversation_stage.name
    print(f"Current conversation stage: {current_stage}")

Streaming Responses
^^^^^^^^^^^^^^^^

For real-time UI applications, use the streaming feature:

.. code-block:: python

    for response_chunk in sales_agent.step(user_input, stream=True):
        # Process each chunk as it arrives
        print(response_chunk, end="", flush=True)