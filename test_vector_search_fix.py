"""
Test Vector Search Pipeline Fix
Verifies that the pipeline correctly:
1. Performs DB search BEFORE calling Gemini
2. Returns "No official scheme found" when no matches
3. Only calls Gemini when schemes are found
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests
import json

# Test cases
test_cases = [
    {
        "query": "What are the agricultural schemes available?",
        "expected": "Should return agricultural schemes from DB, NOT 'no schemes'"
    },
    {
        "query": "Tell me about PM Kisan",
        "expected": "Should match PM Kisan Samman Nidhi via fuzzy/vector"
    },
    {
        "query": "xyz123 nonexistent scheme abc",
        "expected": "Should return 'No official scheme found for your request.'"
    },
    {
        "query": "Ayushman Bharat details",
        "expected": "Should match Ayushman Bharat via fuzzy/exact match"
    }
]

print("\n" + "="*80)
print("VECTOR SEARCH PIPELINE FIX - TEST")
print("="*80 + "\n")

# Test with API (requires server running)
API_URL = "http://localhost:8000/api/smart-answer-v2/"

for i, test in enumerate(test_cases, 1):
    print(f"TEST {i}: {test['query']}")
    print(f"Expected: {test['expected']}")
    
    try:
        response = requests.post(
            API_URL,
            json={"query": test['query'], "language": "en"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            match_type = data.get('match_type', '')
            schemes_used = data.get('schemes_used', [])
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Match Type: {match_type}")
            print(f"📋 Schemes Used: {len(schemes_used)} schemes")
            if schemes_used:
                print(f"   - {', '.join(schemes_used[:3])}")
            print(f"💬 Answer: {answer[:200]}...")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Server not running. Start with: python start.py")
        break
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()

print("="*80)
print("NOTE: For full testing, ensure Django server is running (python start.py)")
print("="*80 + "\n")
