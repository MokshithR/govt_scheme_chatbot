"""
Test API with Question-Type Queries

This script tests the smart-answer-v2 API endpoint with question-type queries
to verify the complete pipeline works end-to-end.

Usage:
1. Make sure server is running: python manage.py runserver
2. Run this script: python test_api_question_queries.py
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/smart-answer-v2/"

# Test queries
test_queries = [
    {
        "query": "what are the benefits of pm kisan samman nidhi",
        "expected_match": "PM Kisan",
        "expected_match_type": "fuzzy_match"
    },
    {
        "query": "eligibility for pm kisan",
        "expected_match": "PM Kisan",
        "expected_match_type": "exact_title"  # May match via keyword/exact
    },
    {
        "query": "how to apply for kisan samman nidhi",
        "expected_match": "PM Kisan",
        "expected_match_type": "fuzzy_match"
    },
    {
        "query": "pm kisan benefits",
        "expected_match": "PM Kisan",
        "expected_match_type": "exact_title"  # May match via keyword/exact
    },
    {
        "query": "tell me about ayushman bharat",
        "expected_match": "Ayushman Bharat",
        "expected_match_type": "fuzzy_match"
    }
]

def test_query(query_text, expected_match, expected_match_type):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING QUERY")
    print(f"{'='*80}")
    print(f"📝 Query: {query_text}")
    
    # Make API request
    try:
        response = requests.post(
            API_URL,
            json={"query": query_text, "language": "en"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if scheme was matched
            schemes_used = data.get('schemes_used', [])
            match_type = data.get('match_type', 'unknown')
            
            print(f"\n✅ API RESPONSE SUCCESS")
            print(f"📊 Match Type: {match_type}")
            print(f"🎯 Schemes Used: {schemes_used}")
            
            # Verify expected match
            if schemes_used and any(expected_match.lower() in s.lower() for s in schemes_used):
                print(f"✅ CORRECT SCHEME MATCHED: {schemes_used[0]}")
                
                # Show answer preview
                answer = data.get('answer', '')
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"\n📝 Answer Preview:")
                print(f"{answer_preview}")
                
                return True
            else:
                print(f"❌ WRONG SCHEME MATCHED")
                print(f"   Expected: {expected_match}")
                print(f"   Got: {schemes_used}")
                return False
        else:
            print(f"❌ API ERROR: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Server not running?")
        print(f"   Make sure to run: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("API TESTING SUITE - QUESTION-TYPE QUERIES")
    print("="*80)
    print(f"Testing endpoint: {API_URL}")
    print(f"Total test cases: {len(test_queries)}")
    
    # Run tests
    results = []
    for test in test_queries:
        result = test_query(
            test['query'],
            test['expected_match'],
            test['expected_match_type']
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Question-type queries work correctly!")
    else:
        print(f"\n⚠️  Some tests failed. Check logs above for details.")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
