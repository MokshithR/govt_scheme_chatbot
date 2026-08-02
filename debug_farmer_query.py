import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot

query = "farmer schemes"
print(f"Testing query: '{query}'")
print("=" * 80)

result = chatbot.process_query(query, language='en')

print(f"\nIntent: {result.get('intent')}")
print(f"Keywords: {result.get('keywords')}")

# Check the extracted entities
from chatbot.chatbot_logic import GovernmentChatbot
bot = GovernmentChatbot()
entities = bot._extract_entities(query)
print(f"Entities: {entities}")

print(f"\nSchemes found: {len(result.get('schemes', []))}")
for i, scheme in enumerate(result.get('schemes', [])[:10], 1):
    if isinstance(scheme, dict):
        print(f"  {i}. {scheme.get('title', 'Unknown')}")
    else:
        print(f"  {i}. {getattr(scheme, 'title', 'Unknown')}")
