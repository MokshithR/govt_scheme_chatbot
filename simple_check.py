#!/usr/bin/env python
"""
Simple web scraper status check - handles connection issues gracefully
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme, WebScrapingLog
from datetime import datetime, timedelta

def simple_check():
    """Simple status check without network calls"""
    
    print("🔍 Web Scraper Status Check")
    print("=" * 40)
    
    # 1. Database Status
    try:
        total_schemes = GovernmentScheme.objects.count()
        active_schemes = GovernmentScheme.objects.filter(is_active=True).count()
        
        # Recent schemes (last 7 days)
        recent_date = datetime.now() - timedelta(days=7)
        recent_schemes = GovernmentScheme.objects.filter(
            last_updated__gte=recent_date
        ).count()
        
        print(f"📊 Database Status:")
        print(f"   Total Schemes: {total_schemes}")
        print(f"   Active Schemes: {active_schemes}")
        print(f"   Recent Updates: {recent_schemes}")
        
        # 2. Scheme Categories
        categories = GovernmentScheme.objects.values('sector').distinct()
        print(f"\n📂 Categories Found: {len(categories)}")
        for cat in categories[:5]:  # Show first 5
            count = GovernmentScheme.objects.filter(sector=cat['sector']).count()
            print(f"   • {cat['sector']}: {count} schemes")
        
        # 3. Languages
        languages = GovernmentScheme.objects.values('language').distinct()
        print(f"\n🌐 Languages: {', '.join([lang['language'] for lang in languages])}")
        
        # 4. Last Scraping Log
        last_scrape = WebScrapingLog.objects.filter(
            status='success'
        ).order_by('-completed_at').first()
        
        if last_scrape:
            days_ago = (datetime.now().date() - last_scrape.completed_at.date()).days
            print(f"\n📝 Last Scrape:")
            print(f"   Date: {last_scrape.completed_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Days Ago: {days_ago}")
            print(f"   Source: {last_scrape.source_name}")
            print(f"   Status: {last_scrape.status}")
        else:
            print(f"\n❌ No scraping history found")
        
        # 5. Recent Schemes
        print(f"\n📋 Recent Schemes:")
        recent = GovernmentScheme.objects.order_by('-last_updated')[:3]
        for scheme in recent:
            print(f"   • {scheme.title[:50]}...")
            print(f"     Sector: {scheme.sector} | Language: {scheme.language}")
        
        # 6. Recommendations
        print(f"\n💡 Status:")
        if total_schemes == 0:
            print("   🔴 No schemes in database - run scraping")
        elif total_schemes < 10:
            print("   🟡 Few schemes - consider more scraping")
        else:
            print("   🟢 Good number of schemes")
        
        if recent_schemes == 0:
            print("   🟡 No recent updates - run incremental scraping")
        else:
            print("   🟢 Database recently updated")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    print(f"\n🚀 To run scraping:")
    print(f"   python manage.py shell")
    print(f"   >>> from chatbot.web_scraper import scraper")
    print(f"   >>> result = scraper.run_full_scraping()")
    
    print(f"\n📈 To test connectivity:")
    print(f"   >>> connectivity = scraper.test_scraping_sources()")
    
    print(f"\n🔧 For incremental updates:")
    print(f"   >>> result = scraper.run_incremental_scraping()")

if __name__ == "__main__":
    simple_check()
