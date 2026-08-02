#!/usr/bin/env python
"""
Quick new scheme detector - fast check for new schemes without full scraping
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
from chatbot.models import GovernmentScheme
import requests
from bs4 import BeautifulSoup
import re

def quick_new_scheme_check():
    """Quick check for new schemes without saving to database"""
    
    print("🔍 Quick New Scheme Detector")
    print("=" * 50)
    
    # Get existing scheme titles
    existing_titles = set()
    try:
        schemes = GovernmentScheme.objects.values_list('title', flat=True)
        for title in schemes:
            normalized = title.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
            existing_titles.add(normalized)
        print(f"📊 Database has {len(existing_titles)} schemes")
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return
    
    # Quick scrape from one portal
    print("\n🕷️  Quick scraping from India.gov.in...")
    
    try:
        # Simple requests scrape (no Selenium for speed)
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        url = "https://www.india.gov.in/my-government/schemes"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find scheme links
            scheme_links = soup.find_all('a', href=True)
            
            new_schemes = []
            processed = 0
            
            for link in scheme_links[:20]:  # Check first 20 links
                try:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if ('scheme' in href.lower() or 'yojana' in text.lower() or 
                        'scheme' in text.lower()) and len(text) > 10:
                        
                        # Normalize for comparison
                        normalized = text.lower().strip()
                        normalized = re.sub(r'\s+', ' ', normalized)
                        
                        processed += 1
                        print(f"\n   {processed}. {text}")
                        
                        if normalized in existing_titles:
                            print(f"      Status: 🔄 Already in database")
                        else:
                            print(f"      Status: ✅ NEW SCHEME DETECTED!")
                            new_schemes.append({
                                'title': text,
                                'url': f"https://www.india.gov.in{href}" if href.startswith('/') else href
                            })
                        
                except Exception as e:
                    continue
            
            # Summary
            print(f"\n" + "=" * 50)
            print(f"📊 QUICK CHECK RESULTS")
            print(f"=" * 50)
            print(f"Schemes processed: {processed}")
            print(f"New schemes found: {len(new_schemes)}")
            
            if new_schemes:
                print(f"\n✅ NEW SCHEMES:")
                for i, scheme in enumerate(new_schemes, 1):
                    print(f"   {i}. {scheme['title']}")
                    print(f"      URL: {scheme['url']}")
                
                print(f"\n💡 To scrape full details:")
                print(f"   >>> from chatbot.web_scraper import scraper")
                print(f"   >>> result = scraper.run_full_scraping()")
            else:
                print(f"\nℹ️  No new schemes found in quick check")
                print(f"💡 Try full scraping for more comprehensive results")
        
        else:
            print(f"❌ Failed to access India.gov.in (Status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Quick scraping failed: {e}")
        print(f"💡 Try using the full scraper with Selenium fallback")

def check_specific_scheme(title):
    """Check if a specific scheme title exists"""
    try:
        existing = GovernmentScheme.objects.filter(
            title__icontains=title
        )
        
        if existing.exists():
            print(f"✅ Found {existing.count()} matching scheme(s):")
            for scheme in existing[:5]:  # Show first 5
                print(f"   • {scheme.title}")
                print(f"     Sector: {scheme.sector} | Language: {scheme.language}")
        else:
            print(f"❌ No schemes found matching: {title}")
            
    except Exception as e:
        print(f"❌ Error checking scheme: {e}")

if __name__ == "__main__":
    # Run quick check
    quick_new_scheme_check()
    
    print(f"\n🔧 Additional commands:")
    print(f"   Check specific scheme: check_specific_scheme('scheme name')")
    print(f"   Full preview: python preview_scraping.py")
