"""List all schemes in database to understand actual titles"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from chatbot.models import GovernmentScheme

print("\n" + "="*80)
print("ALL SCHEMES IN DATABASE")
print("="*80 + "\n")

schemes = GovernmentScheme.objects.filter(is_active=True).order_by('title')

for i, scheme in enumerate(schemes, 1):
    print(f"{i}. {scheme.title}")

print(f"\n{'='*80}")
print(f"Total: {schemes.count()} active schemes")
print("="*80 + "\n")
