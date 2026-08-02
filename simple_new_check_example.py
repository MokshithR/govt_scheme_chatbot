#!/usr/bin/env python
"""
Simple Example: Check if scraped data is new (not in database)
Ready-to-use code for new scheme detection
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from mongodb_adapter import MongoDBAdapter
from chatbot.models import GovernmentScheme
from datetime import datetime
import re

def normalize_title(title):
    """Normalize title for comparison"""
    if not title:
        return ''
    
    # Convert to lowercase, remove special chars, normalize spaces
    normalized = title.lower().strip()
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def is_new_scheme(title, existing_titles):
    """Check if scheme is new (not in database)"""
    normalized = normalize_title(title)
    return normalized not in existing_titles

def load_existing_scheme_titles():
    """Load all existing scheme titles from database"""
    existing_titles = set()
    
    try:
        # Load from MongoDB
        mongodb = MongoDBAdapter()
        mongo_schemes = list(mongodb.schemes_collection.find(
            {"is_active": True}, 
            {"title": 1, "_id": 0}
        ))
        
        for scheme in mongo_schemes:
            title = scheme.get('title', '')
            normalized = normalize_title(title)
            existing_titles.add(normalized)
        
        # Load from Django
        django_schemes = GovernmentScheme.objects.filter(is_active=True)
        for scheme in django_schemes:
            title = scheme.title
            normalized = normalize_title(title)
            existing_titles.add(normalized)
        
        print(f"✅ Loaded {len(existing_titles)} existing schemes")
        return existing_titles
        
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return set()

def check_new_schemes_example():
    """Practical example of checking new schemes"""
    
    print("🔍 PRACTICAL EXAMPLE: Check New Schemes")
    print("=" * 50)
    
    # Step 1: Load existing schemes
    print("📊 Step 1: Loading existing schemes...")
    existing_titles = load_existing_scheme_titles()
    
    # Step 2: Sample scraped data (normally from web scraper)
    print("\n🕷️  Step 2: Sample scraped data...")
    
    scraped_schemes = [
        {
            'title': 'Pradhan Mantri Kisan Samman Nidhi',
            'description': 'Farmer income support scheme',
            'sector': 'agriculture'
        },
        {
            'title': 'NEW Digital India Startup Fund 2024',
            'description': 'Funding for tech startups',
            'sector': 'technology'
        },
        {
            'title': 'Ayushman Bharat Health Scheme',
            'description': 'Health insurance for poor',
            'sector': 'health'
        }
    ]
    
    print(f"   Scraped {len(scraped_schemes)} schemes")
    
    # Step 3: Check each scheme
    print("\n🔍 Step 3: Checking each scheme...")
    
    new_schemes = []
    duplicates = []
    
    for i, scheme in enumerate(scraped_schemes, 1):
        title = scheme['title']
        
        if is_new_scheme(title, existing_titles):
            print(f"   {i}. ✅ NEW: {title}")
            new_schemes.append(scheme)
        else:
            print(f"   {i}. ❌ EXISTS: {title}")
            duplicates.append(scheme)
    
    # Step 4: Results
    print(f"\n📊 Results:")
    print(f"   New schemes: {len(new_schemes)}")
    print(f"   Duplicates: {len(duplicates)}")
    
    if new_schemes:
        print(f"\n✅ New schemes to save:")
        for scheme in new_schemes:
            print(f"   • {scheme['title']} ({scheme['sector']})")
    
    return new_schemes

def save_new_schemes_to_mongodb(new_schemes):
    """Save only new schemes to MongoDB"""
    if not new_schemes:
        print("❌ No new schemes to save")
        return
    
    print(f"\n💾 Saving {len(new_schemes)} new schemes to MongoDB...")
    
    try:
        mongodb = MongoDBAdapter()
        
        for scheme in new_schemes:
            # Prepare data for MongoDB
            mongodb_scheme = {
                'title': scheme['title'],
                'description': scheme['description'],
                'sector': scheme['sector'],
                'government_level': 'central',
                'ministry': 'Government of India',
                'language': 'en',
                'is_active': True,
                'created_at': datetime.now(),
                'detected_as_new': True
            }
            
            # Insert into MongoDB
            result = mongodb.schemes_collection.insert_one(mongodb_scheme)
            
            if result.inserted_id:
                print(f"   ✅ Saved: {scheme['title']}")
            else:
                print(f"   ❌ Failed to save: {scheme['title']}")
        
        print(f"🎉 Successfully saved {len(new_schemes)} new schemes!")
        
    except Exception as e:
        print(f"❌ Error saving to MongoDB: {e}")

# COMPLETE WORKING EXAMPLE
def complete_example():
    """Complete working example you can copy and use"""
    
    print("🚀 COMPLETE WORKING EXAMPLE")
    print("=" * 40)
    print("Copy this code for your project:")
    print()
    
    example_code = '''
# 1. Load existing schemes
existing_titles = load_existing_scheme_titles()

# 2. Get scraped schemes (from your web scraper)
scraped_schemes = [
    {'title': 'Scheme Name', 'description': 'Description', 'sector': 'category'},
    # ... more schemes
]

# 3. Filter new schemes
new_schemes = []
for scheme in scraped_schemes:
    if is_new_scheme(scheme['title'], existing_titles):
        new_schemes.append(scheme)
        print(f"✅ NEW: {scheme['title']}")
    else:
        print(f"❌ EXISTS: {scheme['title']}")

# 4. Save only new schemes
if new_schemes:
    save_new_schemes_to_mongodb(new_schemes)
    print(f"🎉 Saved {len(new_schemes)} new schemes!")
else:
    print("ℹ️  No new schemes found")
'''
    
    print(example_code)

if __name__ == "__main__":
    # Run the practical example
    new_schemes = check_new_schemes_example()
    
    # Show complete working example
    complete_example()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 EXAMPLE COMPLETE!")
    print(f"   New schemes detected: {len(new_schemes)}")
    print(f"   Ready to implement in your scraper!")
    print("=" * 50)
