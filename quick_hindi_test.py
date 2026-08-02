import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot

# Quick Hindi test
print("Testing Hindi translation...")
result = chatbot.process_query('agriculture', language='hi')
response = result['response']['text']
has_hindi = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in response)
print(f"Hindi translation working: {has_hindi}")
print(f"Response preview: {response[:200]}")
print(f"Schemes found: {len(result.get('schemes', []))}")
