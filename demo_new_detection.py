#!/usr/bin/env python
"""
Demo: How to identify new schemes during scraping without saving to database
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
from chatbot.models import GovernmentScheme
import re

def demonstrate_new_scheme_detection():
    """Demonstrate how new scheme detection works"""
    
    print("🎯 New Scheme Detection Demo")
    print("=" * 50)
    
    # Step 1: Load existing schemes from database
    print("📊 Step 1: Loading existing schemes from database...")
    try:
        existing_schemes = GovernmentScheme.objects.all()
        existing_titles = set()
        
        for scheme in existing_schemes:
            # Normalize title for comparison
            normalized = scheme.title.lower().strip()
            normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)  # Remove special chars
            normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
            existing_titles.add(normalized)
        
        print(f"   ✅ Loaded {len(existing_titles)} existing schemes")
        
        # Show some existing schemes
        print("   📋 Existing schemes in database:")
        for scheme in existing_schemes[:3]:
            print(f"      • {scheme.title}")
        
    except Exception as e:
        print(f"   ❌ Error loading database: {e}")
        existing_titles = set()
    
    # Step 2: Simulate scraping new schemes
    print(f"\n🕷️  Step 2: Simulating web scraping...")
    
    # Sample scraped schemes (normally this would come from actual scraping)
    sample_scraped_schemes = [
        {
            'title': 'Pradhan Mantri Awas Yojana (PMAY)',
            'description': 'Housing for All scheme',
            'sector': 'urban_development',
            'language': 'en',
            'source_url': 'https://example.com/pmay'
        },
        {
            'title': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
            'description': 'Income support for farmers',
            'sector': 'agriculture', 
            'language': 'en',
            'source_url': 'https://example.com/pmkisan'
        },
        {
            'title': 'NEW SCHEME: Digital India Startup Fund',
            'description': 'Funding for tech startups',
            'sector': 'technology',
            'language': 'en', 
            'source_url': 'https://example.com/startupfund'
        },
        {
            'title': 'Ayushman Bharat Health Mission',
            'description': 'Health insurance for poor',
            'sector': 'health',
            'language': 'en',
            'source_url': 'https://example.com/ayushman'
        },
        {
            'title': 'Fresh Scheme: Women Empowerment Program 2024',
            'description': 'Skill training for women',
            'sector': 'women_empowerment',
            'language': 'en',
            'source_url': 'https://example.com/women2024'
        }
    ]
    
    print(f"   📥 Scraped {len(sample_scraped_schemes)} schemes from web")
    
    # Step 3: Identify new vs existing schemes
    print(f"\n🔍 Step 3: Identifying new schemes...")
    
    new_schemes = []
    existing_found = []
    
    for scheme in sample_scraped_schemes:
        title = scheme['title']
        
        # Normalize title for comparison
        normalized = title.lower().strip()
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        print(f"\n   📄 Processing: {title}")
        
        if normalized in existing_titles:
            print(f"      Status: 🔄 ALREADY EXISTS in database")
            existing_found.append(scheme)
        else:
            print(f"      Status: ✅ NEW SCHEME - Not in database")
            new_schemes.append(scheme)
        
        print(f"      Sector: {scheme['sector']}")
        print(f"      Language: {scheme['language']}")
    
    # Step 4: Show results
    print(f"\n" + "=" * 50)
    print(f"📊 DETECTION RESULTS")
    print(f"=" * 50)
    
    print(f"\n📈 Summary:")
    print(f"   Total scraped: {len(sample_scraped_schemes)}")
    print(f"   New schemes: {len(new_schemes)}")
    print(f"   Existing found: {len(existing_found)}")
    print(f"   Database size: {len(existing_titles)}")
    
    if new_schemes:
        print(f"\n✅ NEW SCHEMES TO ADD:")
        for i, scheme in enumerate(new_schemes, 1):
            print(f"   {i}. {scheme['title']}")
            print(f"      Sector: {scheme['sector']}")
            print(f"      Description: {scheme['description']}")
            print(f"      Source: {scheme['source_url']}")
    
    if existing_found:
        print(f"\n🔄 EXISTING SCHEMES (skipped):")
        for scheme in existing_found:
            print(f"   • {scheme['title']}")
    
    # Step 5: Show how to save only new schemes
    print(f"\n💾 Step 5: How to save only new schemes...")
    print(f"   # Create scraper instance")
    print(f"   >>> from chatbot.web_scraper import scraper")
    print(f"   ")
    print(f"   # Save only new schemes to database")
    print(f"   >>> result = scraper.save_schemes_to_database(new_schemes)")
    print(f"   >>> print(result)")
    print(f"   ")
    print(f"   # Expected output:")
    print(f"   # {{'added': 2, 'updated': 0, 'skipped': 0, 'errors': 0, 'total_processed': 2}}")
    
    return {
        'new_schemes': new_schemes,
        'existing_found': existing_found,
        'total_scraped': len(sample_scraped_schemes)
    }

def show_detection_methods():
    """Show different methods to detect new schemes"""
    
    print(f"\n🔧 METHODS TO DETECT NEW SCHEMES")
    print(f"=" * 50)
    
    print(f"\n1️⃣  Title Comparison Method:")
    print(f"   ✅ Fast and simple")
    print(f"   ✅ Works for exact matches")
    print(f"   ❌ May miss similar titles")
    
    print(f"\n2️⃣  URL + Title Method:")
    print(f"   ✅ More accurate")
    print(f"   ✅ Catches same content from different sources")
    print(f"   ❌ Requires URL tracking")
    
    print(f"\n3️⃣  Content Similarity Method:")
    print(f"   ✅ Catches variations of same scheme")
    print(f"   ✅ Handles title changes")
    print(f"   ❌ More complex, requires text similarity")
    
    print(f"\n4️⃣  Ministry + Sector + Title Method:")
    print(f"   ✅ Very accurate")
    print(f"   ✅ Multiple criteria")
    print(f"   ❌ More database queries")
    
    print(f"\n📋 IMPLEMENTATION EXAMPLES:")
    print(f"")
    print(f"   # Method 1: Simple title check")
    print(f"   existing = GovernmentScheme.objects.filter(")
    print(f"       title__iexact=scraped_title")
    print(f"   ).exists()")
    print(f"")
    print(f"   # Method 2: URL + title check")
    print(f"   existing = GovernmentScheme.objects.filter(")
    print(f"       title__iexact=scraped_title,")
    print(f"       source_url=scraped_url")
    print(f"   ).first()")
    print(f"")
    print(f"   # Method 3: Content similarity")
    print(f"   # (Requires fuzzy matching library)")
    print(f"   from difflib import SequenceMatcher")
    print(f"   similarity = SequenceMatcher(None, title1, title2).ratio()")
    print(f"   if similarity > 0.8:  # 80% similar")
    print(f"       # Consider as duplicate")

if __name__ == "__main__":
    # Run demonstration
    results = demonstrate_new_scheme_detection()
    
    # Show detection methods
    show_detection_methods()
    
    print(f"\n🎯 Demo completed!")
    print(f"   New schemes identified: {len(results['new_schemes'])}")
    print(f"   Existing schemes found: {len(results['existing_found'])}")
