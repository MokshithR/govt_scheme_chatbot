"""
Test script to add sample scraped schemes to database
This simulates what the real scraper would do
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import ScrapedScheme

# Sample schemes (what would be scraped from india.gov.in)
sample_schemes = [
    {
        'title': 'Pradhan Mantri Jan Dhan Yojana',
        'url': 'https://www.india.gov.in/spotlight/pradhan-mantri-jan-dhan-yojana',
    },
    {
        'title': 'Pradhan Mantri Awas Yojana - Gramin',
        'url': 'https://www.india.gov.in/spotlight/pradhan-mantri-awas-yojana-gramin',
    },
    {
        'title': 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana',
        'url': 'https://www.india.gov.in/spotlight/ayushman-bharat-pmjay',
    },
    {
        'title': 'Pradhan Mantri Kisan Samman Nidhi',
        'url': 'https://www.india.gov.in/spotlight/pradhan-mantri-kisan-samman-nidhi-pm-kisan',
    },
    {
        'title': 'Atal Pension Yojana',
        'url': 'https://www.india.gov.in/spotlight/atal-pension-yojana',
    },
    {
        'title': 'Swachh Bharat Mission',
        'url': 'https://www.india.gov.in/spotlight/swachh-bharat-mission',
    },
    {
        'title': 'Digital India Programme',
        'url': 'https://www.india.gov.in/spotlight/digital-india-programme',
    },
    {
        'title': 'Make in India',
        'url': 'https://www.india.gov.in/spotlight/make-india',
    },
]

added = 0
skipped = 0

print('📊 Adding sample scraped schemes...')
print()

for scheme_data in sample_schemes:
    existing = ScrapedScheme.objects.filter(url=scheme_data['url']).first()
    
    if not existing:
        ScrapedScheme.objects.create(
            title=scheme_data['title'],
            url=scheme_data['url'],
            source='india.gov.in'
        )
        print(f"✅ Added: {scheme_data['title']}")
        added += 1
    else:
        print(f"⏭️  Skipped (duplicate): {scheme_data['title']}")
        skipped += 1

print()
print('=' * 60)
print(f'✅ Complete! Added: {added}, Skipped: {skipped}')
print('=' * 60)
print()
print('💡 View in Django Admin:')
print('   http://localhost:8000/admin/chatbot/scrapedscheme/')
