#!/usr/bin/env python
"""
Simple test script to check if the web scraper can find Garib Kalyan Rojgar Abhiyaan
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_specific_sites():
    """Test specific government sites for Garib Kalyan Rojgar Abhiyaan"""
    
    # Create scraper with minimal config
    config = ScrapingConfig()
    config.max_schemes_per_source = 10
    config.request_delay_min = 1.0
    config.request_delay_max = 2.0
    config.timeout = 15
    config.retry_attempts = 2
    
    scraper = GovernmentPortalScraper(config)
    
    # Test specific URLs that might have Garib Kalyan Rojgar Abhiyaan
    test_urls = [
        "https://ruraldevelopment.gov.in/schemes",
        "https://labour.gov.in/schemes", 
        "https://www.india.gov.in/my-government/schemes",
        "https://www.mygov.in/schemes/",
        "https://www.pmindia.gov.in/en/government-schemes/"
    ]
    
    print("🔍 Testing specific government sites for Garib Kalyan Rojgar Abhiyaan...")
    print("=" * 70)
    
    all_schemes = []
    
    for url in test_urls:
        try:
            print(f"\n📋 Scraping: {url}")
            response = scraper._make_request_with_retry(url)
            
            if response:
                print(f"✅ Successfully fetched {url}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for scheme links
                scheme_links = soup.find_all('a', href=True)
                relevant_links = []
                
                for link in scheme_links:
                    text = link.get_text().lower()
                    href = link.get('href', '').lower()
                    
                    # Look for employment/rojgar related schemes
                    if any(keyword in text or keyword in href for keyword in [
                        'garib', 'kalyan', 'rojgar', 'abhiyaan', 'employment', 
                        'scheme', 'yojana', 'योजना', 'रोजगार'
                    ]):
                        full_url = urljoin(url, link.get('href'))
                        relevant_links.append({
                            'title': link.get_text().strip(),
                            'url': full_url,
                            'source': url
                        })
                
                print(f"🔗 Found {len(relevant_links)} relevant scheme links")
                
                # Try to scrape first few relevant links
                for i, link_data in enumerate(relevant_links[:3]):
                    try:
                        print(f"   📄 Scraping scheme: {link_data['title'][:50]}...")
                        scheme_data = scraper._scrape_scheme_page(link_data['url'])
                        
                        if scheme_data:
                            # Check if this might be Garib Kalyan Rojgar Abhiyaan
                            title_lower = scheme_data.get('title', '').lower()
                            desc_lower = scheme_data.get('description', '').lower()
                            
                            if any(keyword in title_lower or keyword in desc_lower 
                                  for keyword in ['garib kalyan', 'rojgar abhiyaan', 'employment scheme']):
                                print(f"   🎯 POTENTIAL MATCH FOUND!")
                                print(f"      Title: {scheme_data.get('title', 'N/A')}")
                                print(f"      Sector: {scheme_data.get('sector', 'N/A')}")
                                print(f"      Description: {scheme_data.get('description', 'N/A')[:200]}...")
                                all_schemes.append(scheme_data)
                            else:
                                print(f"   ✓ Scheme scraped: {scheme_data.get('title', 'N/A')}")
                                all_schemes.append(scheme_data)
                        else:
                            print(f"   ❌ Failed to scrape scheme details")
                            
                    except Exception as e:
                        print(f"   ❌ Error scraping scheme: {e}")
                        
            else:
                print(f"❌ Failed to fetch {url}")
                
        except Exception as e:
            print(f"❌ Error with {url}: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total schemes found: {len(all_schemes)}")
    
    # Check for Garib Kalyan Rojgar Abhiyaan specifically
    gkra_found = False
    for scheme in all_schemes:
        title_lower = scheme.get('title', '').lower()
        desc_lower = scheme.get('description', '').lower()
        if any(keyword in title_lower or keyword in desc_lower 
              for keyword in ['garib kalyan', 'rojgar abhiyaan']):
            print(f"\n🎯 GARIB KALYAN ROJGAR ABHIYAAN FOUND:")
            print(f"   Title: {scheme.get('title', 'N/A')}")
            print(f"   Source: {scheme.get('source_url', 'N/A')}")
            print(f"   Sector: {scheme.get('sector', 'N/A')}")
            print(f"   Description: {scheme.get('description', 'N/A')[:300]}...")
            gkra_found = True
            break
    
    if not gkra_found:
        print(f"\n❌ Garib Kalyan Rojgar Abhiyaan not found in scraped results")
        print(f"   Found schemes:")
        for i, scheme in enumerate(all_schemes[:5], 1):
            print(f"   {i}. {scheme.get('title', 'N/A')}")
    
    return all_schemes

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    
    test_specific_sites()
