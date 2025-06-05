#!/usr/bin/env python3
"""Debug script to check environment variables."""

import os
from dotenv import load_dotenv

print("=== Environment Debug ===")

# Check current working directory
print(f"Current directory: {os.getcwd()}")

# Check if .env file exists
env_path = ".env"
if os.path.exists(env_path):
    print(f"✅ .env file found at: {os.path.abspath(env_path)}")
    
    # Show .env file contents (without revealing the actual key)
    with open(env_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                key = line.split('=')[0]
                print(f"   Found key: {key}")
else:
    print("❌ .env file not found")

# Load environment variables
print("\n=== Loading .env ===")
load_dotenv()

# Check if OPENAI_API_KEY is loaded
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    # Show first and last 4 characters for verification
    masked_key = f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else "***"
    print(f"✅ OPENAI_API_KEY loaded: {masked_key}")
else:
    print("❌ OPENAI_API_KEY not found")

# Check all environment variables starting with OPENAI
print("\n=== All OPENAI env vars ===")
for key, value in os.environ.items():
    if key.startswith('OPENAI'):
        masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
        print(f"{key}: {masked_value}")

print("\n=== Manual Check ===")
print("Please run these commands manually:")
print("1. echo $OPENAI_API_KEY")
print("2. python -c \"import os; print(os.getenv('OPENAI_API_KEY'))\"")