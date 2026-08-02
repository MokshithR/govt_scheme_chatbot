#!/usr/bin/env python
"""
Test multiple central government websites for scraping
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
import requests

def test_central_government_sites():
    """Test connectivity to multiple central government websites"""
    
    print("🌐 Testing Central Government Websites")
    print("=" * 50)
    
    # Test sites
    central_sites = {
        'India.gov.in': [
            "https://www.india.gov.in/my-government/schemes",
            "https://www.india.gov.in/my-government/schemes/central-schemes"
        ],
        'MyGov India': [
            "https://www.mygov.in/schemes/",
            "https://www.mygov.in/groups/overview/government-schemes/"
        ],
        'National Portal Services': [
            "https://services.india.gov.in/",
            "https://services.india.gov.in/service/listing?cat_id=2"
        ],
        'PM India Portal': [
            "https://www.pmindia.gov.in/en/",
            "https://www.pmindia.gov.in/en/government-schemes/"
        ],
        'Digital India': [
            "https://digitalindia.gov.in/",
            "https://digitalindia.gov.in/initiatives/"
        ]
    }
    
    # Test each site
    working_sites = {}
    
    for site_name, urls in central_sites.items():
        print(f"\n🔍 Testing {site_name}...")
        
        site_status = {
            'working_urls': [],
            'failed_urls': [],
            'overall_status': 'failed'
        }
        
        for url in urls:
            try:
                print(f"   📡 Checking {url}...")
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    print(f"      ✅ Working (Status: {response.status_code})")
                    site_status['working_urls'].append(url)
                else:
                    print(f"      ❌ Failed (Status: {response.status_code})")
                    site_status['failed_urls'].append(url)
                    
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:50]}...")
                site_status['failed_urls'].append(url)
        
        # Determine overall status
        if len(site_status['working_urls']) > 0:
            site_status['overall_status'] = 'working'
        
        working_sites[site_name] = site_status
        
        # Print summary for this site
        working_count = len(site_status['working_urls'])
        total_count = len(urls)
        print(f"   📊 Summary: {working_count}/{total_count} URLs working")
    
    # Overall summary
    print(f"\n" + "=" * 50)
    print(f"📊 OVERALL CONNECTIVITY SUMMARY")
    print(f"=" * 50)
    
    total_working_sites = 0
    for site_name, status in working_sites.items():
        if status['overall_status'] == 'working':
            print(f"   ✅ {site_name}: {len(status['working_urls'])} URLs working")
            total_working_sites += 1
        else:
            print(f"   ❌ {site_name}: No URLs working")
    
    print(f"\n🎯 Result: {total_working_sites}/{len(central_sites)} sites accessible")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if total_working_sites >= 3:
        print("   🟢 Good connectivity - can proceed with scraping")
        print("   🚀 Use: scraper.scrape_central_government_sites()")
    elif total_working_sites >= 1:
        print("   🟡 Partial connectivity - some sites available")
        print("   🔧 Try: scraper.scrape_central_government_sites()")
    else:
        print("   🔴 Poor connectivity - check internet/firewall")
        print("   🌐 Try using VPN or different network")
    
    return working_sites

def test_sample_scraping():
    """Test sample scraping from working sites"""
    
    print(f"\n🕷️  Testing Sample Scraping")
    print("=" * 50)
    
    try:
        # Create scraper with limited config for testing
        config = ScrapingConfig(
            max_schemes_per_source=3,  # Very limited for testing
            request_delay_min=0.3,
            request_delay_max=0.6,
            timeout=10,
            retry_attempts=1
        )
        
        scraper = GovernmentPortalScraper(config)
        
        print("📡 Scraping from central government sites...")
        central_schemes = scraper.scrape_central_government_sites()
        
        print(f"✅ Successfully scraped {len(central_schemes)} schemes")
        
        if central_schemes:
            print(f"\n📋 Sample schemes found:")
            for i, scheme in enumerate(central_schemes[:3], 1):
                print(f"   {i}. {scheme.get('title', 'No Title')}")
                print(f"      Source: {scheme.get('source_portal', 'Unknown')}")
                print(f"      Sector: {scheme.get('sector', 'N/A')}")
                print(f"      Language: {scheme.get('language', 'N/A')}")
                print()
        
        return central_schemes
        
    except Exception as e:
        print(f"❌ Sample scraping failed: {e}")
        return []

if __name__ == "__main__":
    # Test connectivity
    connectivity_results = test_central_government_sites()
    
    # Test sample scraping if any sites are working
    working_count = sum(1 for site in connectivity_results.values() 
                       if site['overall_status'] == 'working')
    
    if working_count > 0:
        print(f"\n" + "="*50)
        sample_results = test_sample_scraping()
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Working sites: {working_count}")
        print(f"   Schemes scraped: {len(sample_results)}")
        print(f"   Ready for auto-scraping: {'✅ Yes' if working_count > 0 else '❌ No'}")
    else:
        print(f"\n❌ No working sites found - cannot proceed with scraping")
        print(f"💡 Try: 1) Check internet connection")
        print(f"      2) Use VPN")
        print(f"      3) Try again later")
