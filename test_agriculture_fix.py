import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot

print("=" * 80)
print("TESTING SECTOR SEARCH - AGRICULTURE")
print("=" * 80)

test_queries = [
    "agriculture",
    "schemes for agriculture", 
    "farmer schemes",
    "show me agriculture programs",
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-" * 80)
    result = chatbot.process_query(query, language='en')
    if result['success']:
        response = result['response']['text']
        print(response[:500])  # First 500 chars
        print()
        
        # Show scheme details
        schemes = result.get('schemes', [])
        print(f"Schemes found: {len(schemes)}")
        for i, scheme in enumerate(schemes[:10], 1):
            if isinstance(scheme, dict):
                print(f"  {i}. {scheme.get('title', 'Unknown')}")
            else:
                print(f"  {i}. {getattr(scheme, 'title', 'Unknown')}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print("=" * 80)
