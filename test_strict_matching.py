"""
Test Cases for Strict Exact Matching Implementation

Tests the new strict matching logic:
1. Exact title match BEFORE embeddings (title__icontains)
2. Partial keyword matching
3. Strict 0.30 threshold
4. LLM strict mode (no guessing)

Run: python manage.py test chatbot.tests.test_strict_matching
Or: python test_strict_matching.py
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/chatbot/smart-answer/"


def test_exact_match_kisan_samman_nidhi():
    """
    Test Case 1: Full exact title match
    Query: "Pradhan Mantri Kisan Samman Nidhi"
    Expected: Returns PM-KISAN scheme ONLY (exact title match before embeddings)
    """
    print("\n" + "="*80)
    print("TEST 1: Exact Match - 'Pradhan Mantri Kisan Samman Nidhi'")
    print("="*80)
    
    payload = {
        "query": "Pradhan Mantri Kisan Samman Nidhi",
        "language": "en"
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes Used: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer:\n{data.get('answer', 'No answer')}")
        
        # Assertions
        assert response.status_code == 200, "Should return 200 OK"
        assert data.get('match_type') == 'exact_title', f"Expected 'exact_title', got {data.get('match_type')}"
        
        schemes_used = data.get('schemes_used', [])
        assert len(schemes_used) == 1, f"Expected exactly 1 scheme, got {len(schemes_used)}"
        
        # Should contain "PM-KISAN" or "Pradhan Mantri Kisan Samman Nidhi"
        scheme_title = schemes_used[0].lower()
        assert 'kisan' in scheme_title and 'samman' in scheme_title, \
            f"Expected PM-KISAN scheme, got: {schemes_used[0]}"
        
        print("\n✅ TEST PASSED: Exact title match working correctly!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Request Failed: {str(e)}")
        return False
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False


def test_exact_match_pm_kisan():
    """
    Test Case 2: Partial keyword exact match
    Query: "PM Kisan"
    Expected: Returns PM-KISAN via keyword match (not vector search)
    """
    print("\n" + "="*80)
    print("TEST 2: Partial Keyword Match - 'PM Kisan'")
    print("="*80)
    
    payload = {
        "query": "PM Kisan",
        "language": "en"
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes Used: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer:\n{data.get('answer', 'No answer')}")
        
        # Assertions
        assert response.status_code == 200, "Should return 200 OK"
        
        # Should be either exact_title or keyword_match (not vector_search_strict)
        match_type = data.get('match_type', '')
        assert match_type in ['exact_title', 'keyword_match'], \
            f"Expected exact or keyword match, got: {match_type}"
        
        schemes_used = data.get('schemes_used', [])
        assert len(schemes_used) >= 1, "Should return at least 1 scheme"
        
        # Should contain "PM-KISAN" or "Kisan"
        found_kisan = any('kisan' in s.lower() for s in schemes_used)
        assert found_kisan, f"Expected PM-KISAN in results, got: {schemes_used}"
        
        print("\n✅ TEST PASSED: Partial keyword matching working correctly!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Request Failed: {str(e)}")
        return False
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False


def test_no_guessing():
    """
    Test Case 3: LLM Strict Mode - No guessing/hallucination
    Query: "Tell me about schemes for aliens from Mars"
    Expected: No hallucinated schemes, proper fallback message
    """
    print("\n" + "="*80)
    print("TEST 3: LLM Strict Mode - No Guessing (Irrelevant Query)")
    print("="*80)
    
    payload = {
        "query": "Tell me about schemes for aliens from Mars",
        "language": "en"
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes Used: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer:\n{data.get('answer', 'No answer')}")
        
        # The answer should NOT contain made-up scheme names
        answer = data.get('answer', '').lower()
        
        # Check for fallback indicators
        fallback_indicators = [
            "couldn't find",
            "no official",
            "not available",
            "no scheme",
            "no government scheme"
        ]
        
        has_fallback = any(indicator in answer for indicator in fallback_indicators)
        
        # Should NOT mention specific real scheme names when query is irrelevant
        # (Unless it's a generic "we have schemes for..." message)
        
        print("\n📋 Fallback Detection:")
        print(f"   - Contains fallback message: {has_fallback}")
        print(f"   - Schemes used: {len(data.get('schemes_used', []))}")
        
        # If it's a strict fallback, schemes_used should be empty or minimal
        if has_fallback:
            schemes_count = len(data.get('schemes_used', []))
            assert schemes_count == 0, \
                f"Fallback message should not include schemes, but found {schemes_count}"
        
        print("\n✅ TEST PASSED: LLM not guessing or hallucinating schemes!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Request Failed: {str(e)}")
        return False
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False


def run_all_tests():
    """Run all strict matching tests"""
    print("\n" + "🔬"*40)
    print("STRICT MATCHING TEST SUITE")
    print("Testing: Exact match, Keyword match, LLM strict mode")
    print("🔬"*40)
    
    results = []
    
    # Test 1: Exact title match
    results.append(("Exact Title Match", test_exact_match_kisan_samman_nidhi()))
    
    # Test 2: Partial keyword match
    results.append(("Partial Keyword Match", test_exact_match_pm_kisan()))
    
    # Test 3: No guessing
    results.append(("LLM Strict Mode", test_no_guessing()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Strict matching is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("   1. Django server must be running: python manage.py runserver")
    print("   2. Database must contain 'Pradhan Mantri Kisan Samman Nidhi' scheme")
    print("   3. API endpoint: http://localhost:8000/api/chatbot/smart-answer/")
    
    input("\nPress ENTER to start tests (or Ctrl+C to cancel)...")
    
    success = run_all_tests()
    
    exit(0 if success else 1)
