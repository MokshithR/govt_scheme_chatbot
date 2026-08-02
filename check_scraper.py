#!/usr/bin/env python
"""
Quick check script for web scraping status
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import scraper
from chatbot.models import GovernmentScheme, WebScrapingLog
from datetime import datetime, timedelta

def quick_check():
    """Quick status check of web scraping"""
    
    print("🔍 Web Scraper Quick Status Check")
    print("=" * 40)
    
    # 1. Database Status
    total_schemes = GovernmentScheme.objects.count()
    active_schemes = GovernmentScheme.objects.filter(is_active=True).count()
    recent_schemes = GovernmentScheme.objects.filter(
        last_updated__gte=datetime.now() - timedelta(days=7)
    ).count()
    
    print(f"📊 Database Status:")
    print(f"   Total Schemes: {total_schemes}")
    print(f"   Active Schemes: {active_schemes}")
    print(f"   Recent Updates (7 days): {recent_schemes}")
    
    # 2. Last Scraping Log
    last_scrape = WebScrapingLog.objects.filter(
        status='success'
    ).order_by('-completed_at').first()
    
    if last_scrape:
        days_ago = (datetime.now().date() - last_scrape.completed_at.date()).days
        print(f"\n📝 Last Successful Scrape:")
        print(f"   Date: {last_scrape.completed_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Days Ago: {days_ago}")
        print(f"   Schemes Found: {last_scrape.schemes_found}")
        print(f"   Duration: {last_scrape.duration_seconds}s")
        print(f"   Source: {last_scrape.source_name}")
    else:
        print(f"\n❌ No successful scraping history found")
    
    # 3. Connectivity Test
    print(f"\n📡 Connectivity Status:")
    connectivity = scraper.test_scraping_sources()
    
    print(f"   India.gov.in: {'✅' if connectivity['india_gov_in'] else '❌'}")
    
    working_states = sum(1 for status in connectivity['state_portals'].values() if status)
    total_states = len(connectivity['state_portals'])
    print(f"   State Portals: {working_states}/{total_states} working")
    
    if connectivity['overall_status'] == 'good':
        status_icon = "🟢"
    elif connectivity['overall_status'] == 'partial':
        status_icon = "🟡"
    else:
        status_icon = "🔴"
    
    print(f"   Overall: {status_icon} {connectivity['overall_status']}")
    
    # 4. Recommendations
    print(f"\n💡 Recommendations:")
    
    if total_schemes == 0:
        print("   🔴 Run full scraping: scraper.run_full_scraping()")
    elif days_ago > 7 if 'days_ago' in locals() else True:
        print("   🟡 Consider incremental scraping: scraper.run_incremental_scraping()")
    else:
        print("   🟢 Database is up to date")
    
    if connectivity['overall_status'] == 'failed':
        print("   🔴 Check internet connection and firewall settings")
    elif connectivity['overall_status'] == 'partial':
        print("   🟡 Some portals may be temporarily unavailable")
    
    print(f"\n🚀 Quick Commands:")
    print(f"   Test connectivity: scraper.test_scraping_sources()")
    print(f"   Full scraping: scraper.run_full_scraping()")
    print(f"   Incremental: scraper.run_incremental_scraping()")

if __name__ == "__main__":
    quick_check()
