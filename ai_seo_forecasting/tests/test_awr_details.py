#!/usr/bin/env python3
"""
Comprehensive AWR API Test Suite
Tests all documented AWR API endpoints to understand what data is available
"""

import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv("AWR_API_KEY")
BASE_URL = "https://api.awrcloud.com/v2/get.php"
TEST_PROJECT = "pella.com"
TEST_PROJECT_ID = "27"

if not API_KEY:
    print("❌ AWR_API_KEY not found!")
    exit(1)

print("=" * 80)
print("AWR API COMPREHENSIVE TEST SUITE")
print("=" * 80)
print(f"Project: {TEST_PROJECT} (ID: {TEST_PROJECT_ID})")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 80)


def test_api(name, action, params=None, method="get"):
    """Test an AWR API endpoint"""
    url = f"{BASE_URL}?token={API_KEY}&action={action}"
    if params:
        for key, val in params.items():
            url += f"&{key}={val}"
    
    try:
        response = requests.get(url, headers={"accept": "application/json"}, timeout=30)
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"Action: {action}")
        print(f"Status: {response.status_code}")
        
        if isinstance(data, dict):
            if data.get('response_code') in [15, 30]:
                print(f"❌ FAILED: {data.get('message', 'Unknown error')}")
                return False
            
            print(f"✅ SUCCESS")
            print(f"Response Keys: {list(data.keys())[:10]}")
            
            # Show useful data
            for key in ['fileName', 'projects', 'dates', 'keywords', 'websites']:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        print(f"  {key}: {len(val)} items")
                    else:
                        print(f"  {key}: {str(val)[:100]}")
            
            return data
        else:
            print(f"✅ SUCCESS (non-JSON response)")
            print(f"Response length: {len(str(data))} chars")
            return data
            
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"❌ ERROR: {str(e)}")
        return False


# ============================================================================
# SECTION 1: BASIC PROJECT DATA (Already Working)
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 1: BASIC PROJECT DATA")
print("="*80)

test_api("Get All Projects", "projects")
test_api("Get Project Details", "details", {"project": TEST_PROJECT})
test_api("Get Update Dates", "get_dates", {"project": TEST_PROJECT})


# ============================================================================
# SECTION 2: RANKINGS DATA (CRITICAL FOR SEO ANALYSIS)
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 2: RANKINGS DATA - THE MOST IMPORTANT!")
print("="*80)

# Calculate date range (last 7 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

rankings_params = {
    "project": TEST_PROJECT,
    "startDate": start_date.strftime("%Y-%m-%d"),
    "stopDate": end_date.strftime("%Y-%m-%d"),
    "format": "json",
    "searchEngineId": "-1",  # All search engines
    "keywordGroupId": "-1",  # All keywords
    "websiteId": "-1",  # All websites
}

# Step 1: Schedule the export
print("\n--- Step 1: Schedule Rankings Export ---")
export_result = test_api("Schedule Rankings Export", "export_ranking", rankings_params)

# Step 2: Download the export (if we got a fileName)
if export_result and isinstance(export_result, dict) and 'fileName' in export_result:
    print("\n--- Step 2: Download Rankings Data ---")
    test_api("Get Rankings Data", "get_export", {
        "project": TEST_PROJECT,
        "fileName": export_result['fileName']
    })
else:
    print("\n⚠️ Skipping download - no fileName received")


# ============================================================================
# SECTION 3: KEYWORD DIFFICULTY
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 3: KEYWORD DIFFICULTY")
print("="*80)

test_api("Estimate KW Difficulty", "estimate_keyword_difficulty", {
    "projectIds": TEST_PROJECT_ID
})

test_api("Request KW Difficulty Update", "update_keyword_difficulty", {
    "projectIds": TEST_PROJECT_ID
})

test_api("Get KW Difficulty Data", "export_keyword_difficulty", {
    "projectId": TEST_PROJECT_ID,
    "searchEngineId": "-1",
    "keywordGroupId": "-1",
    "mode": "plain"
})


# ============================================================================
# SECTION 4: TOP SITES (COMPETITOR ANALYSIS)
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 4: TOP SITES - COMPETITOR ANALYSIS")
print("="*80)

topsites_params = {
    "project": TEST_PROJECT,
    "startDate": start_date.strftime("%Y-%m-%d"),
    "stopDate": end_date.strftime("%Y-%m-%d"),
    "topUrls": "50",
    "encodeurl": "false"
}

topsites_result = test_api("Schedule Top Sites Export", "topsites_export", topsites_params)

if topsites_result and isinstance(topsites_result, dict) and 'fileName' in topsites_result:
    test_api("Get Top Sites Data", "get_topsites", {
        "project": TEST_PROJECT,
        "fileName": topsites_result['fileName']
    })


# ============================================================================
# SECTION 5: GOOGLE DATA (SEARCH VOLUME & CTR)
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 5: GOOGLE DATA")
print("="*80)

# CTR Data
test_api("Get CTR Data", "export_ctr", {
    "date": datetime.now().strftime("%Y-%m-15"),
    "searches-type": "allSearches",
    "value": "exact",
    "device": "allDevices",
    "format": "json"
})

# Search Volume Data
test_api("Get Search Volume", "export_search_volume", {
    "projectId": TEST_PROJECT_ID,
    "dataType": "searchVolume",
    "keywordGroupIds": "-1",
    "mode": "plain"
})


# ============================================================================
# SECTION 6: ON-DEMAND UPDATES
# ============================================================================
print("\n\n" + "="*80)
print("SECTION 6: ON-DEMAND UPDATES")
print("="*80)

test_api("Estimate On-Demand Update", "estimate_on_demand", {
    "projectIds": TEST_PROJECT_ID,
    "speed": "slow"
})

# Uncomment to actually request an update (uses resources!)
# test_api("Request On-Demand Update", "on_demand", {
#     "projectIds": TEST_PROJECT_ID,
#     "speed": "slow"
# })


# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("""
KEY FINDINGS:

1. RANKINGS DATA (export_ranking + get_export):
   - This is THE critical endpoint for actual keyword rankings
   - Returns: rank positions, URLs, dates, search engines
   - Must schedule export first, then download with fileName
   
2. KEYWORD DIFFICULTY (export_keyword_difficulty):
   - Provides competitiveness scores for keywords
   - Useful for prioritizing keyword targets
   
3. TOP SITES (topsites_export + get_topsites):
   - Shows competitor domains in top results
   - Critical for competitive analysis
   
4. SEARCH VOLUME (export_search_volume):
   - AdWords search volume data
   - Helps understand keyword potential
   
5. CTR DATA (export_ctr):
   - Organic CTR benchmarks
   - Useful for traffic forecasting

NEXT STEPS:
- Implement AWRRankingsTool (export_ranking + get_export)
- Implement AWRKeywordDifficultyTool
- Implement AWRTopSitesTool
- Implement AWRSearchVolumeTool
""")

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)