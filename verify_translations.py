"""
Verify that translations are properly stored in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme

# Get the Agri-Clinics scheme
scheme = GovernmentScheme.objects.get(id=20)

print(f"Scheme: {scheme.title}")
print(f"\n{'='*60}")
print(f"Checking Kannada translations...")
print(f"{'='*60}\n")

# Check each field
fields = [
    'short_description',
    'description',
    'eligibility_criteria',
    'benefits',
    'financial_assistance',
    'application_process'
]

for field in fields:
    trans_field = f"{field}_translations"
    trans_data = getattr(scheme, trans_field, {})
    
    print(f"\n{field.upper()}:")
    print(f"  Has translations field: {hasattr(scheme, trans_field)}")
    print(f"  Translations data type: {type(trans_data)}")
    print(f"  Has 'kn' key: {'kn' in trans_data if trans_data else False}")
    
    if trans_data and 'kn' in trans_data:
        kn_text = trans_data['kn']
        print(f"  Kannada text (first 100 chars): {kn_text[:100]}...")
        
        # Test the helper method
        result = scheme.get_field_translation(field, 'kn')
        print(f"  Helper method returns: {result[:100]}...")
    else:
        print(f"  ❌ No Kannada translation found!")

print(f"\n{'='*60}")
print(f"Testing helper methods directly...")
print(f"{'='*60}\n")

print(f"get_title('kn'): {scheme.get_title('kn')[:80]}...")
print(f"get_description('kn'): {scheme.get_description('kn')[:80]}...")
print(f"get_field_translation('benefits', 'kn'): {scheme.get_field_translation('benefits', 'kn')[:80]}...")
