#!/usr/bin/env python3
"""
Direct AWR API Test Script
Tests different authentication methods to find the correct one
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AWR_API_KEY")
BASE_URL = "https://api.awrcloud.com/v2/get.php"

if not API_KEY:
    print("❌ AWR_API_KEY not found in environment!")
    exit(1)

print("🧪 Testing AWR API Authentication Methods...")
print(f"API Key (first 10 chars): {API_KEY[:10]}...")
print("=" * 60)

# Test 1: No auth (baseline)
print("\n📍 Test 1: No Authentication")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects",
        headers={"accept": "application/json"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Bearer Token (current implementation)
print("\n📍 Test 2: Bearer Token Authentication")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects",
        headers={
            "accept": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Query Parameter
print("\n📍 Test 3: Query Parameter Authentication")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects&token={API_KEY}",
        headers={"accept": "application/json"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: API Key in query (alternative name)
print("\n📍 Test 4: API Key Parameter")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects&apikey={API_KEY}",
        headers={"accept": "application/json"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Basic Auth
print("\n📍 Test 5: Basic Authentication")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects",
        headers={"accept": "application/json"},
        auth=(API_KEY, ''),  # Username = API key, password empty
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 6: X-API-Key header
print("\n📍 Test 6: X-API-Key Header")
try:
    response = requests.get(
        f"{BASE_URL}?action=projects",
        headers={
            "accept": "application/json",
            "X-API-Key": API_KEY
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Projects returned: {len(data.get('projects', []))}")
    if data.get('projects'):
        print("✅ SUCCESS - Projects found!")
        print(f"First project: {data['projects'][0]['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("🏁 Testing Complete!")
print("\nWhichever test shows projects is the correct auth method.")