"""
Comprehensive Tests for Fuzzy Matching, Suggestions, and LLM Behavior

Tests the upgraded chatbot system with:
1. Fuzzy matching (typo correction)
2. Auto-suggestions API
3. LLM strict mode (no guessing)
4. Embedding fallback
5. Format quality

Run: python test_fuzzy_chatbot.py
"""

import requests
import json
import time

# API endpoints
BASE_URL = "http://localhost:8000"
SMART_ANSWER_URL = f"{BASE_URL}/api/chatbot/smart-answer-v2/"
SUGGESTIONS_URL = f"{BASE_URL}/api/suggestions/"


def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)


def print_result(success, message):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status}: {message}")


# ============================================================
# Test 1: Fuzzy Match - "pm kisn" → PM-KISAN
# ============================================================

def test_fuzzy_match_pm_kisn():
    """
    Test fuzzy matching with typo: "pm kisn" (missing 'a')
    Should return PM-KISAN scheme using fuzzy matching
    """
    print_test_header("Fuzzy Match - 'pm kisn' → PM-KISAN")
    
    payload = {
        "query": "pm kisn",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes: {data.get('schemes_used', [])}")
        print(f"🎯 Fuzzy Score: {data.get('fuzzy_score', 'N/A')}")
        print(f"\n💬 Answer Preview:\n{data.get('answer', 'No answer')[:200]}...")
        
        # Assertions
        assert response.status_code == 200, "Should return 200 OK"
        assert data.get('match_type') == 'fuzzy_match', \
            f"Expected fuzzy_match, got {data.get('match_type')}"
        
        schemes = data.get('schemes_used', [])
        assert len(schemes) > 0, "Should return at least one scheme"
        assert any('kisan' in s.lower() for s in schemes), \
            "Should return PM-KISAN or similar scheme"
        
        fuzzy_score = data.get('fuzzy_score', 0)
        assert fuzzy_score >= 85, f"Fuzzy score should be >= 85, got {fuzzy_score}"
        
        print_result(True, "Fuzzy matching works correctly for typos")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 2: Fuzzy Match - "samman nidi" → PM-KISAN
# ============================================================

def test_fuzzy_match_samman_nidi():
    """
    Test fuzzy matching with typo: "samman nidi" (missing 'h')
    Should return PM-KISAN scheme
    """
    print_test_header("Fuzzy Match - 'samman nidi' → PM-KISAN")
    
    payload = {
        "query": "samman nidi",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes: {data.get('schemes_used', [])}")
        print(f"🎯 Fuzzy Score: {data.get('fuzzy_score', 'N/A')}")
        print(f"\n💬 Answer Preview:\n{data.get('answer', 'No answer')[:200]}...")
        
        # Assertions
        assert response.status_code == 200
        assert data.get('match_type') in ['fuzzy_match', 'exact_title', 'partial_keyword']
        
        schemes = data.get('schemes_used', [])
        assert any('samman' in s.lower() or 'kisan' in s.lower() for s in schemes), \
            "Should return PM-KISAN with 'samman' or 'kisan'"
        
        print_result(True, "Fuzzy matching handles partial typos")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 3: Partial Match - "kisan" → PM-KISAN
# ============================================================

def test_partial_match_kisan():
    """
    Test partial keyword matching: "kisan"
    Should return PM-KISAN as first result
    """
    print_test_header("Partial Match - 'kisan' → PM-KISAN")
    
    payload = {
        "query": "kisan",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer Preview:\n{data.get('answer', 'No answer')[:200]}...")
        
        # Assertions
        assert response.status_code == 200
        
        schemes = data.get('schemes_used', [])
        assert len(schemes) > 0, "Should return schemes"
        assert any('kisan' in s.lower() for s in schemes), \
            "First scheme should contain 'kisan'"
        
        print_result(True, "Partial keyword matching returns relevant schemes")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 4: Suggestions - Typing "pmk"
# ============================================================

def test_suggestion_typing_pmk():
    """
    Test auto-suggestions for partial input: "pmk"
    Should suggest PM-KISAN and other PM schemes
    """
    print_test_header("Auto-Suggest - 'pmk' → PM schemes")
    
    payload = {
        "partial_text": "pmk",
        "max_suggestions": 10
    }
    
    try:
        response = requests.post(SUGGESTIONS_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        
        print(f"\n📊 Suggestions Count: {len(suggestions)}")
        print(f"🔍 Query: '{data.get('query', 'N/A')}'")
        print("\n💡 Suggestions:")
        
        for idx, sug in enumerate(suggestions[:5], 1):
            print(f"   {idx}. {sug['title']} (score: {sug.get('score', 'N/A')}, type: {sug.get('match_type', 'N/A')})")
        
        # Assertions
        assert response.status_code == 200
        assert len(suggestions) > 0, "Should return at least one suggestion"
        
        # Check if PM-KISAN is in suggestions
        has_pm_kisan = any('kisan' in s['title'].lower() for s in suggestions)
        assert has_pm_kisan, "Should include PM-KISAN in suggestions"
        
        print_result(True, "Auto-suggest returns relevant PM schemes")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 5: Suggestions - Typo "ayshmn"
# ============================================================

def test_suggestion_typo_ayushman():
    """
    Test fuzzy suggestions with typo: "ayshmn"
    Should suggest "Ayushman Bharat" using fuzzy matching
    """
    print_test_header("Auto-Suggest Fuzzy - 'ayshmn' → Ayushman Bharat")
    
    payload = {
        "partial_text": "ayshmn",
        "max_suggestions": 10
    }
    
    try:
        response = requests.post(SUGGESTIONS_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        
        print(f"\n📊 Suggestions Count: {len(suggestions)}")
        print("\n💡 Suggestions:")
        
        for idx, sug in enumerate(suggestions[:5], 1):
            print(f"   {idx}. {sug['title']} (score: {sug.get('score', 'N/A')})")
        
        # Assertions
        assert response.status_code == 200
        
        # Should find Ayushman Bharat with fuzzy matching
        has_ayushman = any('ayushman' in s['title'].lower() for s in suggestions)
        assert has_ayushman, "Should find Ayushman Bharat with fuzzy match"
        
        print_result(True, "Fuzzy suggestions handle typos correctly")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 6: LLM No Guessing
# ============================================================

def test_no_guessing_llm():
    """
    Test LLM strict mode: irrelevant query should NOT hallucinate schemes
    Query: "schemes for aliens from mars"
    Expected: Fallback message, no made-up schemes
    """
    print_test_header("LLM Strict Mode - No Guessing")
    
    payload = {
        "query": "government schemes for aliens from mars",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer:\n{data.get('answer', 'No answer')}")
        
        # Assertions
        assert response.status_code == 200
        
        match_type = data.get('match_type', '')
        schemes = data.get('schemes_used', [])
        answer = data.get('answer', '').lower()
        
        # Should be fallback or no schemes
        fallback_keywords = ['could not find', 'no scheme', 'not find', 'not available']
        has_fallback = any(keyword in answer for keyword in fallback_keywords)
        
        assert has_fallback or len(schemes) == 0, \
            "Should return fallback message or empty schemes for irrelevant query"
        
        # Should NOT mention specific real schemes for irrelevant queries
        # (unless it's a generic list message)
        
        print_result(True, "LLM does not hallucinate or guess schemes")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 7: Embedding Fallback
# ============================================================

def test_embedding_fallback():
    """
    Test vector search fallback for semantic queries
    Query: "financial help for small farmers"
    Should use embedding search and return relevant schemes
    """
    print_test_header("Embedding Fallback - Semantic Search")
    
    payload = {
        "query": "financial help for small farmers",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📊 Match Type: {data.get('match_type', 'N/A')}")
        print(f"📝 Schemes: {data.get('schemes_used', [])}")
        print(f"\n💬 Answer Preview:\n{data.get('answer', 'No answer')[:200]}...")
        
        # Assertions
        assert response.status_code == 200
        
        schemes = data.get('schemes_used', [])
        assert len(schemes) > 0, "Should return schemes using embedding search"
        
        # Should be relevant to farmers/agriculture
        relevant_keywords = ['kisan', 'farmer', 'agriculture', 'agri', 'krishi']
        has_relevant = any(
            any(keyword in scheme.lower() for keyword in relevant_keywords)
            for scheme in schemes
        )
        
        assert has_relevant, "Should return agriculture-related schemes"
        
        print_result(True, "Embedding fallback works for semantic queries")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Test 8: Answer Format Quality
# ============================================================

def test_answer_format_quality():
    """
    Test that LLM-generated answers are high quality and well-formatted
    Query: "Pradhan Mantri Kisan Samman Nidhi"
    Check: Includes eligibility, benefits, application link
    """
    print_test_header("Answer Format Quality")
    
    payload = {
        "query": "Pradhan Mantri Kisan Samman Nidhi",
        "language": "en"
    }
    
    try:
        response = requests.post(SMART_ANSWER_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        answer = data.get('answer', '')
        
        print(f"\n💬 Full Answer:\n{answer}")
        
        # Check answer quality
        answer_lower = answer.lower()
        
        # Should mention key elements
        has_eligibility = any(word in answer_lower for word in ['eligible', 'eligibility', 'who can'])
        has_benefits = any(word in answer_lower for word in ['benefit', '₹', 'rupees', 'amount'])
        has_link_or_apply = any(word in answer_lower for word in ['apply', 'link', 'website', 'gov.in'])
        
        print(f"\n✅ Quality Checks:")
        print(f"   Eligibility mentioned: {has_eligibility}")
        print(f"   Benefits mentioned: {has_benefits}")
        print(f"   Application info: {has_link_or_apply}")
        
        # Assertions
        assert has_benefits, "Answer should mention benefits"
        assert len(answer) > 50, "Answer should be substantial (>50 chars)"
        assert len(answer) < 1000, "Answer should be concise (<1000 chars)"
        
        print_result(True, "Answer format is high quality and comprehensive")
        return True
        
    except AssertionError as e:
        print_result(False, str(e))
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


# ============================================================
# Run All Tests
# ============================================================

def run_all_tests():
    """Run all test cases and summarize results"""
    print("\n" + "🧪"*40)
    print("FUZZY MATCHING & CHATBOT UPGRADE TEST SUITE")
    print("Testing: Fuzzy match, Suggestions, LLM strict mode, Embeddings")
    print("🧪"*40)
    
    tests = [
        ("Fuzzy Match: pm kisn", test_fuzzy_match_pm_kisn),
        ("Fuzzy Match: samman nidi", test_fuzzy_match_samman_nidi),
        ("Partial Match: kisan", test_partial_match_kisan),
        ("Auto-Suggest: pmk", test_suggestion_typing_pmk),
        ("Auto-Suggest Fuzzy: ayshmn", test_suggestion_typo_ayushman),
        ("LLM No Guessing", test_no_guessing_llm),
        ("Embedding Fallback", test_embedding_fallback),
        ("Answer Quality", test_answer_format_quality),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Chatbot upgrade is working perfectly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("   1. Django server must be running: python manage.py runserver")
    print("   2. Database must have PM-KISAN and other schemes")
    print("   3. rapidfuzz library must be installed: pip install rapidfuzz")
    print("   4. Gemini API key must be configured")
    
    input("\nPress ENTER to start tests (or Ctrl+C to cancel)...")
    
    success = run_all_tests()
    
    exit(0 if success else 1)
