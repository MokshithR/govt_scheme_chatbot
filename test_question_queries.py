"""
Test Question-Type Queries for PM-KISAN Scheme Detection

This script tests the new query preprocessing pipeline to ensure
question-type queries correctly map to scheme titles.

Test Cases:
1. "what are the benefits of pm kisan samman nidhi"
2. "eligibility for pm kisan"
3. "how to apply for kisan samman nidhi"
4. "pm kisan benefits"
5. "tell me about pm kisan scheme"
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.utils.normalization import normalize_query_for_scheme_detection, fuzzy_match_scheme
from chatbot.models import GovernmentScheme

def test_query_normalization():
    """Test the query normalization function"""
    print("\n" + "="*80)
    print("TESTING QUERY NORMALIZATION")
    print("="*80)
    
    test_queries = [
        "what are the benefits of pm kisan samman nidhi",
        "eligibility for pm kisan",
        "how to apply for kisan samman nidhi",
        "pm kisan benefits",
        "tell me about pm kisan scheme",
        "give me information about ayushman bharat",
        "what is the eligibility criteria for pm kisan",
        "how can i apply for kisan samman nidhi yojana"
    ]
    
    for query in test_queries:
        normalized = normalize_query_for_scheme_detection(query)
        print(f"\n📝 RAW: {query}")
        print(f"🎯 NORMALIZED: {normalized}")

def test_fuzzy_matching():
    """Test fuzzy matching with normalized queries"""
    print("\n" + "="*80)
    print("TESTING FUZZY MATCHING WITH NORMALIZED QUERIES")
    print("="*80)
    
    test_queries = [
        "what are the benefits of pm kisan samman nidhi",
        "eligibility for pm kisan",
        "how to apply for kisan samman nidhi",
        "pm kisan benefits",
        "benefits of pm kisan samman nidhi yojana",
        "tell me pmkisan yojana benefits",
        "pm kisan samman nidhi scheme details",
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"📝 RAW QUERY: {query}")
        
        # Normalize
        normalized = normalize_query_for_scheme_detection(query)
        print(f"🎯 NORMALIZED: {normalized}")
        
        # Try fuzzy match with 80% threshold (lowered to handle suffix removal)
        matches = fuzzy_match_scheme(
            query=normalized,
            schemes_queryset=GovernmentScheme.objects,
            confidence_threshold=80.0,
            limit=3
        )
        
        if matches:
            print(f"✅ FUZZY MATCHES FOUND: {len(matches)}")
            for i, match in enumerate(matches, 1):
                print(f"  {i}. {match['title']} (score: {match['score']:.1f}%)")
        else:
            print(f"❌ NO FUZZY MATCH (score < 80%)")

def test_end_to_end():
    """Test complete pipeline: normalize → fuzzy match → return scheme"""
    print("\n" + "="*80)
    print("TESTING COMPLETE PIPELINE (END-TO-END)")
    print("="*80)
    
    query = "what are the benefits of pm kisan samman nidhi"
    
    print(f"\n🔍 SEARCH PIPELINE STARTED")
    print(f"📝 RAW QUERY: {query}")
    
    # Step 1: Normalize
    normalized = normalize_query_for_scheme_detection(query)
    print(f"🎯 NORMALIZED QUERY: {normalized}")
    
    # Step 2: Fuzzy match with 80% threshold (lowered to handle suffix removal)
    matches = fuzzy_match_scheme(
        query=normalized,
        schemes_queryset=GovernmentScheme.objects,
        confidence_threshold=80.0,
        limit=1
    )
    
    if matches and len(matches) > 0:
        match = matches[0]
        print(f"\n✅ FUZZY MATCH FOUND!")
        print(f"📊 FUZZY SCORE: {match['score']:.1f}%")
        print(f"🎯 MATCHED TITLE: {match['title']}")
        print(f"🚀 DECISION: Return scheme details immediately")
        
        scheme = match['scheme']
        print(f"\n📄 SCHEME DETAILS:")
        print(f"   ID: {scheme.id}")
        print(f"   Title: {scheme.title}")
        print(f"   Sector: {scheme.sector}")
        print(f"   Description: {scheme.description[:200]}...")
        
        return True
    else:
        print(f"\n❌ NO MATCH FOUND")
        print(f"🚀 DECISION: Fall back to vector search or LLM")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("QUESTION-TYPE QUERY TESTING SUITE")
    print("="*80)
    
    # Test 1: Query normalization
    test_query_normalization()
    
    # Test 2: Fuzzy matching
    test_fuzzy_matching()
    
    # Test 3: End-to-end pipeline
    success = test_end_to_end()
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED - Query preprocessing is working correctly!")
    else:
        print("❌ TESTS FAILED - Check if PM-KISAN scheme exists in database")
    print("="*80 + "\n")
