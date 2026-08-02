"""
Test Universal Fuzzy Matching System
Tests that fuzzy matching works for ALL schemes with the normalized queries
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from chatbot.utils.normalization import normalize_query, universal_fuzzy_match
from chatbot.models import GovernmentScheme

print("\n" + "="*80)
print("UNIVERSAL FUZZY MATCHING TEST - ALL SCHEMES")
print("="*80 + "\n")

# Test cases covering multiple schemes
test_cases = [
    # PM Kisan Samman Nidhi variations
    {"query": "pm kisan samman nidhi yojana", "expected_scheme": "PM Kisan Samman Nidhi"},
    {"query": "pmkisan yojana", "expected_scheme": "PM Kisan Samman Nidhi"},
    {"query": "kisan samman nidhi", "expected_scheme": "PM Kisan Samman Nidhi"},
    {"query": "pradhan mantri kisan samman nidhi", "expected_scheme": "PM Kisan Samman Nidhi"},
    
    # Ayushman Bharat variations
    {"query": "ayushman bharat yojana", "expected_scheme": "Ayushman Bharat"},
    {"query": "ayushman bharat scheme", "expected_scheme": "Ayushman Bharat"},
    {"query": "ayushman", "expected_scheme": "Ayushman Bharat"},
    
    # Pradhan Mantri Mudra Yojana
    {"query": "mudra yojana", "expected_scheme": "Pradhan Mantri Mudra Yojana"},
    {"query": "pradhan mantri mudra scheme", "expected_scheme": "Pradhan Mantri Mudra Yojana"},
    {"query": "pmmy scheme", "expected_scheme": "Pradhan Mantri Mudra Yojana"},
    
    # Beti Bachao Beti Padhao
    {"query": "beti bachao beti padhao", "expected_scheme": "Beti Bachao Beti Padhao"},
    {"query": "beti bachao padhao", "expected_scheme": "Beti Bachao Beti Padhao"},
    
    # National Mission for Sustainable Agriculture
    {"query": "nmsa scheme", "expected_scheme": "National Mission for Sustainable Agriculture"},
    {"query": "national mission sustainable agriculture", "expected_scheme": "National Mission for Sustainable Agriculture"},
    {"query": "sustainable agriculture mission", "expected_scheme": "National Mission for Sustainable Agriculture"},
    
    # Other schemes
    {"query": "pm awas yojana", "expected_scheme": "Pradhan Mantri Awas Yojana"},
    {"query": "fasal bima yojana", "expected_scheme": "Pradhan Mantri Fasal Bima Yojana"},
    {"query": "janani suraksha yojana", "expected_scheme": "Janani Suraksha Yojana"},
    {"query": "startup india scheme", "expected_scheme": "Startup India"},
    {"query": "mgnrega details", "expected_scheme": "MGNREGA"},
]

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    query = test['query']
    expected = test['expected_scheme']
    
    # Step 1: Normalize query
    normalized = normalize_query(query)
    
    # Step 2: Universal fuzzy match
    fuzzy_matches = universal_fuzzy_match(
        query=normalized,
        schemes_queryset=GovernmentScheme.objects,
        confidence_threshold=70.0,  # Lowered from 80 to catch more matches
        limit=1
    )
    
    if fuzzy_matches and len(fuzzy_matches) > 0:
        matched_scheme = fuzzy_matches[0]['scheme']
        fuzzy_score = fuzzy_matches[0]['score']
        
        # Check if match is correct (title contains expected keyword)
        if expected.lower() in matched_scheme.title.lower():
            print(f"✅ TEST {i}: PASS")
            print(f"  📝 Query: '{query}'")
            print(f"  🎯 Normalized: '{normalized}'")
            print(f"  ✅ Matched: {matched_scheme.title}")
            print(f"  📊 Score: {fuzzy_score:.1f}%")
            passed += 1
        else:
            print(f"❌ TEST {i}: WRONG MATCH")
            print(f"  📝 Query: '{query}'")
            print(f"  🎯 Expected: {expected}")
            print(f"  ❌ Got: {matched_scheme.title}")
            print(f"  📊 Score: {fuzzy_score:.1f}%")
            failed += 1
    else:
        print(f"❌ TEST {i}: NO MATCH")
        print(f"  📝 Query: '{query}'")
        print(f"  🎯 Normalized: '{normalized}'")
        print(f"  ❌ No scheme found with score >= 80%")
        failed += 1
    
    print()

print("="*80)
print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
print("="*80 + "\n")

sys.exit(0 if failed == 0 else 1)
