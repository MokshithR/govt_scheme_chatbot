#!/usr/bin/env python
"""
Preview web scraping - shows schemes being scraped without saving to database
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
from chatbot.models import GovernmentScheme
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preview_scraping():
    """Preview what schemes will be scraped without saving to database"""
    
    print("🔍 Web Scraping Preview - Identify New Schemes")
    print("=" * 60)
    
    # Create scraper with preview config
    config = ScrapingConfig(
        max_schemes_per_source=10,  # Limited for preview
        request_delay_min=0.3,      # Faster for preview
        request_delay_max=0.8,
        timeout=15,
        retry_attempts=2
    )
    
    scraper = GovernmentPortalScraper(config)
    
    # Get existing schemes from database for comparison
    existing_schemes = set()
    try:
        existing = GovernmentScheme.objects.values_list('title', flat=True)
        for title in existing:
            # Normalize title for comparison
            normalized = title.lower().strip()
            normalized = ' '.join(normalized.split())  # Remove extra spaces
            existing_schemes.add(normalized)
        print(f"📊 Found {len(existing_schemes)} existing schemes in database")
    except Exception as e:
        print(f"⚠️  Could not load existing schemes: {e}")
        existing_schemes = set()
    
    print("\n🕷️  Starting preview scraping (not saving to database)...")
    print("-" * 60)
    
    all_scraped_schemes = []
    new_schemes_found = []
    duplicate_schemes_found = []
    
    # Test central government scraping
    print("\n🇮🇳 Testing Central Government Portals...")
    try:
        central_schemes = scraper.scrape_india_gov_in()
        print(f"   Scraped {len(central_schemes)} schemes from central portals")
        
        for i, scheme in enumerate(central_schemes, 1):
            title = scheme.get('title', 'No Title')
            normalized_title = title.lower().strip()
            normalized_title = ' '.join(normalized_title.split())
            
            print(f"\n   {i}. {title}")
            print(f"      Sector: {scheme.get('sector', 'N/A')}")
            print(f"      Language: {scheme.get('language', 'N/A')}")
            print(f"      Source: {scheme.get('source_url', 'N/A')[:50]}...")
            
            # Check if this is a new scheme
            if normalized_title in existing_schemes:
                print(f"      Status: 🔄 ALREADY EXISTS")
                duplicate_schemes_found.append(scheme)
            else:
                print(f"      Status: ✅ NEW SCHEME")
                new_schemes_found.append(scheme)
            
            # Show keywords and tags
            keywords = scheme.get('keywords', [])
            tags = scheme.get('search_tags', [])
            print(f"      Keywords: {', '.join(keywords[:3])}...")
            print(f"      Tags: {', '.join(tags[:3])}...")
            
            all_scraped_schemes.append(scheme)
            
    except Exception as e:
        print(f"   ❌ Central scraping failed: {e}")
    
    # Test state government scraping
    print(f"\n🏛️  Testing State Government Portals...")
    try:
        state_schemes = scraper.scrape_state_government_sites()
        print(f"   Scraped {len(state_schemes)} schemes from state portals")
        
        for i, scheme in enumerate(state_schemes[:5], 1):  # Show first 5 only
            title = scheme.get('title', 'No Title')
            normalized_title = title.lower().strip()
            normalized_title = ' '.join(normalized_title.split())
            
            print(f"\n   {i}. {title}")
            print(f"      State: {scheme.get('state', 'N/A')}")
            print(f"      Sector: {scheme.get('sector', 'N/A')}")
            print(f"      Language: {scheme.get('language', 'N/A')}")
            
            # Check if this is a new scheme
            if normalized_title in existing_schemes:
                print(f"      Status: 🔄 ALREADY EXISTS")
                duplicate_schemes_found.append(scheme)
            else:
                print(f"      Status: ✅ NEW SCHEME")
                new_schemes_found.append(scheme)
            
            all_scraped_schemes.extend(state_schemes)
            
    except Exception as e:
        print(f"   ❌ State scraping failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SCRAPING PREVIEW SUMMARY")
    print("=" * 60)
    
    print(f"\n📈 Results:")
    print(f"   Total schemes scraped: {len(all_scraped_schemes)}")
    print(f"   New schemes identified: {len(new_schemes_found)}")
    print(f"   Existing schemes found: {len(duplicate_schemes_found)}")
    print(f"   Existing schemes in DB: {len(existing_schemes)}")
    
    # Show new schemes details
    if new_schemes_found:
        print(f"\n✅ NEW SCHEMES DETECTED ({len(new_schemes_found)}):")
        for i, scheme in enumerate(new_schemes_found[:10], 1):  # Show first 10
            print(f"   {i}. {scheme.get('title', 'No Title')}")
            print(f"      Sector: {scheme.get('sector', 'N/A')}")
            print(f"      Source: {scheme.get('source_url', 'N/A')[:60]}...")
            print(f"      Language: {scheme.get('language', 'N/A')}")
            print()
    
    # Show categories found
    if all_scraped_schemes:
        sectors = {}
        languages = {}
        states = {}
        
        for scheme in all_scraped_schemes:
            sector = scheme.get('sector', 'other')
            language = scheme.get('language', 'en')
            state = scheme.get('state', 'Central')
            
            sectors[sector] = sectors.get(sector, 0) + 1
            languages[language] = languages.get(language, 0) + 1
            states[state] = states.get(state, 0) + 1
        
        print(f"📂 Categories Found:")
        for sector, count in sectors.items():
            print(f"   • {sector}: {count} schemes")
        
        print(f"\n🌐 Languages Found:")
        for lang, count in languages.items():
            print(f"   • {lang}: {count} schemes")
        
        print(f"\n🏛️  Sources:")
        for state, count in states.items():
            print(f"   • {state}: {count} schemes")
    
    # Action recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if len(new_schemes_found) > 0:
        print(f"   ✅ Found {len(new_schemes_found)} new schemes!")
        print(f"   🚀 To save them to database:")
        print(f"      >>> result = scraper.save_schemes_to_database(new_schemes_found)")
        print(f"      >>> print(result)")
    else:
        print(f"   ℹ️  No new schemes found in this preview")
        print(f"   🔍 Try running full scraping for more results:")
        print(f"      >>> result = scraper.run_full_scraping()")
    
    print(f"\n🔍 To run full preview without saving:")
    print(f"      >>> all_schemes = scraper.scrape_india_gov_in()")
    print(f"      >>> state_schemes = scraper.scrape_state_government_sites()")
    print(f"      >>> total = all_schemes + state_schemes")
    print(f"      >>> print(f'Total: {len(total)} schemes')")
    
    return {
        'total_scraped': len(all_scraped_schemes),
        'new_schemes': len(new_schemes_found),
        'duplicates': len(duplicate_schemes_found),
        'new_schemes_data': new_schemes_found
    }

def check_scheme_exists(title):
    """Check if a specific scheme exists in database"""
    try:
        normalized = title.lower().strip()
        normalized = ' '.join(normalized.split())
        
        existing = GovernmentScheme.objects.filter(
            title__iexact=title.strip()
        ).first()
        
        if existing:
            print(f"✅ Scheme found in database:")
            print(f"   Title: {existing.title}")
            print(f"   Sector: {existing.sector}")
            print(f"   Last Updated: {existing.last_updated}")
            return True
        else:
            print(f"❌ Scheme not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error checking scheme: {e}")
        return False

if __name__ == "__main__":
    # Run preview scraping
    results = preview_scraping()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 Preview completed! New schemes: {results['new_schemes']}")
    print("=" * 60)
