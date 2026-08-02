import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot

print("=" * 80)
print("SECTOR SEARCH TEST - All Variations")
print("=" * 80)

test_queries = [
    ("agriculture", "Should return all 22 agriculture schemes"),
    ("farmer schemes", "Should return all 22 agriculture schemes"),
    ("health", "Should return all health schemes"),
    ("education", "Should return all education schemes"),
    ("employment", "Should return all employment schemes"),
    ("schemes for students", "Should return education schemes"),
]

for query, expected in test_queries:
    print(f"\nQuery: '{query}'")
    print(f"Expected: {expected}")
    print("-" * 80)
    
    result = chatbot.process_query(query, language='en')
    if result['success']:
        schemes = result.get('schemes', [])
        print(f"✓ Found {len(schemes)} schemes")
        
        # Show first 5
        for i, scheme in enumerate(schemes[:5], 1):
            if isinstance(scheme, dict):
                title = scheme.get('title', 'Unknown')
                sector = scheme.get('sector', 'Unknown')
            else:
                title = getattr(scheme, 'title', 'Unknown')
                sector = getattr(scheme.sector, 'name', 'Unknown') if hasattr(scheme, 'sector') and scheme.sector else 'Unknown'
            print(f"  {i}. {title} (Sector: {sector})")
        
        if len(schemes) > 5:
            print(f"  ... and {len(schemes) - 5} more")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
