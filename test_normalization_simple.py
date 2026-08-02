"""
Universal Query Normalization Test - Works for ALL Schemes

Tests the universal normalization function that works for any government scheme.
"""

from chatbot.utils.normalization import normalize_query

def test_normalization():
    """Test universal query normalization for ALL schemes"""
    
    test_cases = [
        # PM-KISAN tests
        {
            "input": "what are the benefits of pm kisan samman nidhi",
            "expected": "pm kisan samman nidhi",
            "description": "PM-KISAN: Question with 'benefits'"
        },
        {
            "input": "benefits of pm kisan samman nidhi yojana",
            "expected": "pm kisan samman nidhi",
            "description": "PM-KISAN: With suffix 'yojana'"
        },
        {
            "input": "pm kisan samman nidhi scheme details",
            "expected": "pm kisan samman nidhi",
            "description": "PM-KISAN: With suffixes 'scheme' and 'details'"
        },
        {
            "input": "what are the benefits from pm kisan samman nidhi yojana",
            "expected": "pm kisan samman nidhi",
            "description": "PM-KISAN: Full question with 'yojana'"
        },
        
        # Ayushman Bharat tests
        {
            "input": "tell me about ayushman bharat scheme",
            "expected": "ayushman bharat",
            "description": "Ayushman Bharat: With suffix 'scheme'"
        },
        {
            "input": "ayushman bharat yojna information",
            "expected": "ayushman bharat",
            "description": "Ayushman Bharat: With typo 'yojna'"
        },
        {
            "input": "what is ayushman bharat yojana eligibility",
            "expected": "ayushman bharat",
            "description": "Ayushman Bharat: Question with 'eligibility'"
        },
        
        # PM Mudra tests
        {
            "input": "mudra yojna benefits",
            "expected": "mudra",
            "description": "Mudra: Short form with 'yojna'"
        },
        {
            "input": "pradhan mantri mudra yojana details",
            "expected": "mudra",
            "description": "Mudra: Full name with generic terms removed"
        },
        
        # Beti Bachao Beti Padhao tests
        {
            "input": "beti bachao beti padhao scheme",
            "expected": "beti bachao beti padhao",
            "description": "Beti Bachao: With suffix 'scheme'"
        },
        {
            "input": "tell me about beti bachao padhao yojana",
            "expected": "beti bachao padhao",
            "description": "Beti Bachao: Variation without 'beti'"
        },
        
        # NMSA tests
        {
            "input": "nmsa scheme information",
            "expected": "nmsa",
            "description": "NMSA: Abbreviation with 'scheme'"
        },
        {
            "input": "national mission for sustainable agriculture program details",
            "expected": "national mission sustainable agriculture",
            "description": "NMSA: Full name (removes 'for', 'program', 'details')"
        },
        
        # Generic tests
        {
            "input": "eligibility for pm kisan",
            "expected": "pm kisan",
            "description": "Generic: Short query"
        },
        {
            "input": "how to apply for kisan samman nidhi",
            "expected": "kisan samman nidhi",
            "description": "Generic: Question without scheme suffix"
        }
    ]
    
    print("\n" + "="*80)
    print("QUERY NORMALIZATION FUNCTION TEST")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        input_query = test['input']
        expected_output = test['expected']
        description = test['description']
        
        # Run normalization
        actual_output = normalize_query(input_query)
        
        # Check if it matches
        is_correct = actual_output == expected_output
        status = "✅ PASS" if is_correct else "❌ FAIL"
        
        if is_correct:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} - {description}")
        print(f"  📝 Input:    {input_query}")
        print(f"  🎯 Expected: {expected_output}")
        print(f"  ✅ Got:      {actual_output}")
        
        if not is_correct:
            print(f"  ❌ MISMATCH!")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print(f"{'='*80}\n")
    
    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_normalization()
    exit(0 if success else 1)
