"""
Test Smart Query API - Complete Pipeline Verification
Tests all pipeline steps with various query types
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/query/"

# Test cases covering all pipeline steps
test_cases = [
    # ==== STEP 1: Greetings (Gemini Fallback) ====
    {
        "query": "Hello",
        "expected_type": "gemini_fallback",
        "description": "Greeting - should use Gemini"
    },
    {
        "query": "Hi, how are you?",
        "expected_type": "gemini_fallback",
        "description": "Casual greeting"
    },
    
    # ==== STEP 2: Exact Match ====
    {
        "query": "PM Kisan Samman Nidhi",
        "expected_type": "exact_match",
        "description": "Exact scheme name"
    },
    {
        "query": "PM Kisan Samman Nidhi Yojana details",
        "expected_type": "exact_match",
        "description": "Exact match with suffix words"
    },
    {
        "query": "pmkisan",
        "expected_type": "exact_match",
        "description": "Synonym match (pmkisan → PM Kisan)"
    },
    {
        "query": "ayushman bharat scheme",
        "expected_type": "exact_match",
        "description": "Ayushman Bharat exact match"
    },
    
    # ==== STEP 3: Fuzzy Match ====
    {
        "query": "pm kissan samman nidi",
        "expected_type": "fuzzy_match",
        "description": "Spelling variations (kissan, nidi)"
    },
    {
        "query": "kisan samman nidhi yojana",
        "expected_type": "fuzzy_match",
        "description": "Partial name fuzzy match"
    },
    {
        "query": "ayushmaan bharat",
        "expected_type": "fuzzy_match",
        "description": "Ayushman spelling variation"
    },
    
    # ==== STEP 4: Sector Intent ====
    {
        "query": "What are the agricultural schemes available?",
        "expected_type": "sector_match",
        "description": "Agriculture sector query"
    },
    {
        "query": "show me health schemes",
        "expected_type": "sector_match",
        "description": "Health sector query"
    },
    {
        "query": "education programs for students",
        "expected_type": "sector_match",
        "description": "Education sector query"
    },
    {
        "query": "farmer schemes",
        "expected_type": "sector_match",
        "description": "Agriculture sector (farmer keyword)"
    },
    
    # ==== STEP 5: Vector Search ====
    {
        "query": "schemes for rural employment",
        "expected_type": "vector_match",
        "description": "Vector search - employment query"
    },
    {
        "query": "housing assistance for poor",
        "expected_type": "vector_match",
        "description": "Vector search - housing query"
    },
    
    # ==== STEP 6: No Match (Gemini Fallback) ====
    {
        "query": "xyz123 nonexistent scheme",
        "expected_type": "gemini_fallback",
        "description": "No match - should fallback to Gemini"
    },
]

def test_query_api():
    """Test the smart query API with all test cases"""
    
    print("\n" + "="*80)
    print("SMART QUERY API - COMPREHENSIVE TEST")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test['query']
        expected_type = test['expected_type']
        description = test['description']
        
        print(f"\n{'─'*80}")
        print(f"TEST {i}: {description}")
        print(f"Query: '{query}'")
        print(f"Expected: {expected_type}")
        print(f"{'─'*80}")
        
        try:
            # Make API request
            response = requests.post(
                API_URL,
                json={"query": query, "language": "en"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                match_type = data.get('match_type', '')
                response_text = data.get('response', '')
                schemes = data.get('schemes', [])
                exact_match = data.get('exact_match')
                fuzzy_match = data.get('fuzzy_match')
                
                # Check if match_type matches expectation
                if match_type == expected_type:
                    print(f"✅ PASS - Match Type: {match_type}")
                    passed += 1
                else:
                    print(f"❌ FAIL - Expected: {expected_type}, Got: {match_type}")
                    failed += 1
                
                # Display response details
                print(f"\n📊 Response Details:")
                print(f"   Match Type: {match_type}")
                print(f"   Schemes Count: {len(schemes)}")
                
                if exact_match:
                    print(f"   Exact Match: {exact_match['title']}")
                elif fuzzy_match:
                    print(f"   Fuzzy Match: {fuzzy_match['title']}")
                    if 'similarity_score' in data:
                        print(f"   Similarity: {data['similarity_score']:.2f}")
                elif schemes:
                    print(f"   Schemes: {', '.join([s['title'] for s in schemes[:3]])}")
                
                # Display response preview
                print(f"\n💬 Response Preview:")
                preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
                print(f"   {preview}")
                
            else:
                print(f"❌ FAIL - HTTP {response.status_code}")
                print(f"   {response.text[:200]}")
                failed += 1
        
        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR - Server not running")
            print(f"   Please start the server with: python manage.py runserver")
            break
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80 + "\n")
    
    return passed, failed


if __name__ == "__main__":
    print("\n🚀 Starting Smart Query API Tests...")
    print("⚠️  Make sure the Django server is running (python manage.py runserver)\n")
    
    passed, failed = test_query_api()
    
    if failed == 0:
        print("✅ ALL TESTS PASSED! 🎉")
    else:
        print(f"⚠️  {failed} tests failed. Review the output above.")
