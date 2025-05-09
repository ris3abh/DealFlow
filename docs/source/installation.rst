Installation
===========

Requirements
-----------

* Python 3.12+
* CAMEL framework
* OpenAI API key or other supported model provider

Basic Installation
-----------------

You can install DealFlow directly from the Spinutech Azure Artifacts repository:

.. code-block:: bash

    pip install dealflow

Configuration
------------

After installation, you'll need to set up your environment with appropriate API keys:

.. code-block:: bash

    # Set environment variables for your chosen model provider
    export OPENAI_API_KEY=your_api_key_here

    # Or use a .env file with python-dotenv
    echo "OPENAI_API_KEY=your_api_key_here" > .env

Development Installation
-----------------------

For development purposes, you can install the package in editable mode:

.. code-block:: bash

    git clone https://bsstfs.visualstudio.com/DefaultCollection/DealFlow/_git/DealFlow
    cd DealFlow
    pip install -e .