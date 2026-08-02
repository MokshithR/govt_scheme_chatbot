#!/usr/bin/env python
"""
Example: How to check if new scraped data is not in database
Demonstrates new scheme detection with real examples
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from mongodb_adapter import MongoDBAdapter
from chatbot.models import GovernmentScheme
import re
from datetime import datetime

def demonstrate_new_scheme_detection():
    """Demonstrate how to detect new schemes vs existing ones"""
    
    print("🔍 NEW SCHEME DETECTION EXAMPLE")
    print("=" * 60)
    
    # Step 1: Load existing schemes from database
    print("📊 STEP 1: Loading existing schemes from database...")
    
    try:
        # Load from MongoDB
        mongodb = MongoDBAdapter()
        existing_mongo = list(mongodb.schemes_collection.find(
            {"is_active": True}, 
            {"title": 1, "sector": 1, "_id": 0}
        ))
        
        # Load from Django
        existing_django = list(GovernmentScheme.objects.filter(
            is_active=True
        ).values('title', 'sector'))
        
        # Combine and normalize existing titles
        existing_titles = set()
        
        print("   📋 Existing schemes in MongoDB:")
        for scheme in existing_mongo[:5]:  # Show first 5
            title = scheme.get('title', '')
            normalized = normalize_title(title)
            existing_titles.add(normalized)
            print(f"      • {title[:50]}...")
        
        print(f"   📋 Existing schemes in Django:")
        for scheme in existing_django[:3]:  # Show first 3
            title = scheme.get('title', '')
            normalized = normalize_title(title)
            existing_titles.add(normalized)
            print(f"      • {title[:50]}...")
        
        print(f"   ✅ Total existing schemes: {len(existing_titles)}")
        
    except Exception as e:
        print(f"   ❌ Error loading database: {e}")
        existing_titles = set()
    
    # Step 2: Simulate new scraped data
    print(f"\n🕷️  STEP 2: Simulating web scraping - New data found...")
    
    # Sample scraped schemes (normally from actual web scraping)
    scraped_schemes = [
        {
            'title': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
            'description': 'Income support of Rs. 6000 per year to farmers',
            'sector': 'agriculture',
            'source_url': 'https://pmkisan.gov.in/',
            'ministry': 'Ministry of Agriculture'
        },
        {
            'title': 'Ayushman Bharat Health Insurance Scheme',
            'description': 'Health insurance coverage of Rs. 5 lakh per family',
            'sector': 'health',
            'source_url': 'https://pmjay.gov.in/',
            'ministry': 'Ministry of Health'
        },
        {
            'title': 'NEW: Digital India Startup Fund 2024',
            'description': 'Funding for technology startups and innovation',
            'sector': 'technology',
            'source_url': 'https://startupindia.gov.in/',
            'ministry': 'Ministry of Electronics'
        },
        {
            'title': 'Pradhan Mantri Awas Yojana - Housing for All',
            'description': 'Affordable housing for economically weaker sections',
            'sector': 'housing',
            'source_url': 'https://pmay.gov.in/',
            'ministry': 'Ministry of Housing'
        },
        {
            'title': 'Fresh Scheme: Women Empowerment Program 2024',
            'description': 'Skill development and financial assistance for women',
            'sector': 'women_empowerment',
            'source_url': 'https://wcd.gov.in/',
            'ministry': 'Ministry of Women Development'
        }
    ]
    
    print(f"   📥 Scraped {len(scraped_schemes)} schemes from web")
    
    # Step 3: Check each scraped scheme against database
    print(f"\n🔍 STEP 3: Checking each scraped scheme against database...")
    print("=" * 60)
    
    new_schemes = []
    existing_schemes = []
    
    for i, scheme in enumerate(scraped_schemes, 1):
        title = scheme['title']
        normalized = normalize_title(title)
        
        print(f"\n{i}. 📄 Checking: {title}")
        print(f"   Normalized: '{normalized}'")
        
        if normalized in existing_titles:
            print(f"   ❌ RESULT: ALREADY EXISTS in database")
            print(f"   🔄 Action: Skip (duplicate)")
            existing_schemes.append(scheme)
        else:
            print(f"   ✅ RESULT: NEW SCHEME - Not in database")
            print(f"   🆕 Action: Add to database")
            scheme['detected_as_new'] = True
            scheme['detection_date'] = datetime.now()
            new_schemes.append(scheme)
        
        print(f"   📂 Sector: {scheme['sector']}")
        print(f"   🔗 Source: {scheme['source_url']}")
    
    # Step 4: Show results
    print(f"\n" + "=" * 60)
    print(f"📊 DETECTION RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"\n📈 Summary:")
    print(f"   Total scraped: {len(scraped_schemes)}")
    print(f"   New schemes: {len(new_schemes)}")
    print(f"   Existing found: {len(existing_schemes)}")
    print(f"   Database size: {len(existing_titles)}")
    
    if new_schemes:
        print(f"\n✅ NEW SCHEMES TO ADD ({len(new_schemes)}):")
        for i, scheme in enumerate(new_schemes, 1):
            print(f"   {i}. {scheme['title']}")
            print(f"      Sector: {scheme['sector']}")
            print(f"      Description: {scheme['description']}")
            print(f"      Source: {scheme['source_url']}")
            print(f"      Detection Date: {scheme['detection_date']}")
            print()
    
    if existing_schemes:
        print(f"🔄 EXISTING SCHEMES (SKIPPED):")
        for scheme in existing_schemes:
            print(f"   • {scheme['title']} (Sector: {scheme['sector']})")
    
    # Step 5: Show how to save only new schemes
    print(f"💾 STEP 5: How to save only NEW schemes...")
    print("=" * 45)
    
    print(f"\n# Code to save only new schemes:")
    print(f"```python")
    print(f"# Save only new schemes to MongoDB")
    print(f"for scheme in new_schemes:")
    print(f"    result = mongodb.schemes_collection.insert_one({{")
    print(f"        'title': scheme['title'],")
    print(f"        'description': scheme['description'],")
    print(f"        'sector': scheme['sector'],")
    print(f"        'source_url': scheme['source_url'],")
    print(f"        'detected_as_new': True,")
    print(f"        'detection_date': datetime.now()")
    print(f"    }})")
    print(f"    print(f'Added: {{scheme[\"title\"]}}')")
    print(f"```")
    
    print(f"\n# Expected output:")
    print(f"Added: NEW: Digital India Startup Fund 2024")
    print(f"Added: Fresh Scheme: Women Empowerment Program 2024")
    
    return {
        'total_scraped': len(scraped_schemes),
        'new_schemes': len(new_schemes),
        'existing_found': len(existing_schemes),
        'new_schemes_data': new_schemes
    }

def normalize_title(title):
    """Normalize title for accurate comparison"""
    if not title:
        return ''
    
    # Convert to lowercase and remove extra spaces
    normalized = title.lower().strip()
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def show_detection_methods():
    """Show different methods for detecting new schemes"""
    
    print(f"\n🔧 DETECTION METHODS COMPARISON")
    print("=" * 40)
    
    methods = [
        {
            'name': 'Exact Title Match',
            'code': "title1.lower() == title2.lower()",
            'accuracy': 'High',
            'speed': 'Fast',
            'pros': ['Simple', 'Fast', 'Accurate for exact matches'],
            'cons': ['Misses variations', 'Case sensitive issues']
        },
        {
            'name': 'Normalized Title Match',
            'code': "normalize_title(title1) == normalize_title(title2)",
            'accuracy': 'Very High',
            'speed': 'Fast',
            'pros': ['Handles spacing', 'Removes punctuation', 'Case insensitive'],
            'cons': ['Still exact matching']
        },
        {
            'name': 'Fuzzy String Matching',
            'code': "similarity > 0.8 (using difflib)",
            'accuracy': 'Medium',
            'speed': 'Slow',
            'pros': ['Catches similar titles', 'Handles variations'],
            'cons': ['Computationally expensive', 'False positives']
        },
        {
            'name': 'Multiple Criteria Match',
            'code': "title + sector + ministry combination",
            'accuracy': 'Very High',
            'speed': 'Medium',
            'pros': ['Most accurate', 'Multiple data points'],
            'cons': ['More database queries', 'Complex logic']
        }
    ]
    
    for method in methods:
        print(f"\n📋 {method['name']}:")
        print(f"   Code: {method['code']}")
        print(f"   Accuracy: {method['accuracy']} | Speed: {method['speed']}")
        print(f"   ✅ Pros: {', '.join(method['pros'])}")
        print(f"   ❌ Cons: {', '.join(method['cons'])}")
    
    print(f"\n💡 RECOMMENDED: Use 'Normalized Title Match' for best balance")

if __name__ == "__main__":
    # Run the demonstration
    results = demonstrate_new_scheme_detection()
    
    # Show detection methods
    show_detection_methods()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 EXAMPLE COMPLETED!")
    print(f"   New schemes detected: {results['new_schemes']}")
    print(f"   Existing schemes found: {results['existing_found']}")
    print(f"   Ready to save only new schemes!")
    print("=" * 60)
