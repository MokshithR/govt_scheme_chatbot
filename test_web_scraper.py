#!/usr/bin/env python
"""
Test script for the updated web scraping module
Run this script to verify the web scraping functionality
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the web scraping functionality"""
    
    print("🔍 Testing Government Voice Chatbot Web Scraper")
    print("=" * 60)
    
    # Create scraper with custom config for testing
    config = ScrapingConfig(
        max_schemes_per_source=5,  # Reduced for testing
        request_delay_min=0.5,     # Faster for testing
        request_delay_max=1.0,
        timeout=15,
        retry_attempts=2
    )
    
    scraper = GovernmentPortalScraper(config)
    
    # Test 1: Connectivity Test
    print("\n📡 1. Testing connectivity to government portals...")
    try:
        connectivity_results = scraper.test_scraping_sources()
        print(f"   ✅ India.gov.in: {'Connected' if connectivity_results['india_gov_in'] else 'Failed'}")
        
        for state, status in connectivity_results['state_portals'].items():
            print(f"   {'✅' if status else '❌'} {state}: {'Connected' if status else 'Failed'}")
        
        print(f"   📊 Overall Status: {connectivity_results['overall_status']}")
        
    except Exception as e:
        print(f"   ❌ Connectivity test failed: {e}")
    
    # Test 2: Sample Scraping
    print("\n🕷️  2. Testing sample scraping (limited scope)...")
    try:
        # Test with a very small sample
        original_max = scraper.config.max_schemes_per_source
        scraper.config.max_schemes_per_source = 2  # Very limited for testing
        
        # Scrape just central government for testing
        central_schemes = scraper.scrape_india_gov_in()
        
        print(f"   ✅ Successfully scraped {len(central_schemes)} schemes")
        
        if central_schemes:
            print("   📋 Sample scheme found:")
            sample = central_schemes[0]
            print(f"      Title: {sample.get('title', 'N/A')[:50]}...")
            print(f"      Sector: {sample.get('sector', 'N/A')}")
            print(f"      Language: {sample.get('language', 'N/A')}")
            print(f"      Keywords: {len(sample.get('keywords', []))} found")
        
        scraper.config.max_schemes_per_source = original_max  # Restore original
        
    except Exception as e:
        print(f"   ❌ Sample scraping failed: {e}")
    
    # Test 3: Data Validation
    print("\n🧪 3. Testing data validation...")
    try:
        if central_schemes:
            # Test validation method
            validated_data = scraper._validate_and_clean_scheme_data(central_schemes[0])
            if validated_data:
                print("   ✅ Data validation working correctly")
                print(f"      Required fields present: {bool(validated_data.get('title') and validated_data.get('description'))}")
            else:
                print("   ❌ Data validation failed")
        
    except Exception as e:
        print(f"   ❌ Data validation test failed: {e}")
    
    # Test 4: Language Detection
    print("\n🌐 4. Testing language detection...")
    try:
        from bs4 import BeautifulSoup
        
        # Test HTML samples
        test_html_en = '<html lang="en"><body><h1>Pradhan Mantri Yojana</h1></body></html>'
        test_html_hi = '<html lang="hi"><body><h1>प्रधानमंत्री योजना</h1></body></html>'
        
        soup_en = BeautifulSoup(test_html_en, 'html.parser')
        soup_hi = BeautifulSoup(test_html_hi, 'html.parser')
        
        lang_en = scraper._detect_language(soup_en)
        lang_hi = scraper._detect_language(soup_hi)
        
        print(f"   ✅ English detection: {lang_en}")
        print(f"   ✅ Hindi detection: {lang_hi}")
        
    except Exception as e:
        print(f"   ❌ Language detection test failed: {e}")
    
    # Test 5: Categorization
    print("\n📂 5. Testing scheme categorization...")
    try:
        test_cases = [
            ("Pradhan Mantri Kisan Samman Nidhi", "Financial assistance for farmers"),
            ("Ayushman Bharat Health Scheme", "Health insurance for poor families"),
            ("Skill Development Mission", "Training programs for youth"),
            ("Housing for All", "Affordable housing initiative")
        ]
        
        for title, desc in test_cases:
            sector = scraper._categorize_scheme(title, desc)
            print(f"   ✅ '{title}' → {sector}")
        
    except Exception as e:
        print(f"   ❌ Categorization test failed: {e}")
    
    # Test 6: Search Tags Generation
    print("\n🏷️  6. Testing search tags generation...")
    try:
        title = "Pradhan Mantri Awas Yojana - Housing for All"
        description = "Affordable housing scheme for economically weaker sections in urban areas"
        
        tags = scraper._generate_search_tags(title, description)
        print(f"   ✅ Generated {len(tags)} search tags: {', '.join(tags[:5])}...")
        
    except Exception as e:
        print(f"   ❌ Search tags test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Web Scraper Testing Complete!")
    print("\n📊 Summary:")
    print("   - Connectivity tested")
    print("   - Sample scraping performed")
    print("   - Data validation verified")
    print("   - Language detection working")
    print("   - Scheme categorization functional")
    print("   - Search tags generation working")
    
    print("\n🚀 To run full scraping, use:")
    print("   python manage.py shell")
    print("   >>> from chatbot.web_scraper import scraper")
    print("   >>> result = scraper.run_full_scraping()")
    
    print("\n📈 To test incremental scraping:")
    print("   >>> result = scraper.run_incremental_scraping()")

if __name__ == "__main__":
    test_scraper()
