"""Check fuzzy scores for failing test cases"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from chatbot.utils.normalization import normalize_query, universal_fuzzy_match
from chatbot.models import GovernmentScheme

# Failing test cases
failing_cases = [
    {"query": "pmkisan yojana", "normalized": "pmkisan"},
    {"query": "ayushman", "normalized": "ayushman"},
    {"query": "mudra yojana", "normalized": "mudra"},
    {"query": "pmmy scheme", "normalized": "pmmy"},
    {"query": "nmsa scheme", "normalized": "nmsa"},
    {"query": "pm awas yojana", "normalized": "pm awas"},
    {"query": "fasal bima yojana", "normalized": "fasal bima"},
]

print("\nChecking fuzzy scores for failing cases (threshold: 60%):\n")

for test in failing_cases:
    fuzzy_matches = universal_fuzzy_match(
        query=test['normalized'],
        schemes_queryset=GovernmentScheme.objects,
        confidence_threshold=60.0,  # Very low to see all matches
        limit=3
    )
    
    print(f"Query: '{test['query']}' → Normalized: '{test['normalized']}'")
    if fuzzy_matches:
        for m in fuzzy_matches:
            print(f"  - {m['title']}: {m['score']:.1f}%")
    else:
        print(f"  ❌ No match found even at 60%")
    print()
