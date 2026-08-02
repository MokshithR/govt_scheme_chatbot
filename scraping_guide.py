#!/usr/bin/env python
"""
Complete Web Scraping Guide - Shows all available options
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

def show_scraping_options():
    """Show all available web scraping options"""
    
    print("🌐 GOVERNMENT WEB SCRAPING OPTIONS")
    print("=" * 60)
    
    print("\n📊 CURRENT STATUS:")
    try:
        # MongoDB status
        mongodb = MongoDBAdapter()
        mongo_count = mongodb.schemes_collection.count_documents({"is_active": True})
        
        # Django status
        django_count = GovernmentScheme.objects.filter(is_active=True).count()
        
        print(f"   MongoDB Schemes: {mongo_count}")
        print(f"   Django DB Schemes: {django_count}")
        
    except Exception as e:
        print(f"   Status check failed: {e}")
    
    print(f"\n🚀 AVAILABLE SCRAPING OPTIONS:")
    
    print(f"\n1️⃣  QUICK STATUS CHECK")
    print(f"   python simple_check.py")
    print(f"   ✅ Fast database status")
    print(f"   ✅ No network calls")
    print(f"   ✅ Shows existing schemes")
    
    print(f"\n2️⃣  CONNECTIVITY TEST")
    print(f"   python test_central_sites.py")
    print(f"   ✅ Tests all central government sites")
    print(f"   ✅ Shows which sites are working")
    print(f"   ✅ Sample scraping test")
    
    print(f"\n3️⃣  PREVIEW SCRAPING (No Save)")
    print(f"   python preview_scraping.py")
    print(f"   ✅ Shows new vs existing schemes")
    print(f"   ✅ Doesn't save to database")
    print(f"   ✅ Safe for testing")
    
    print(f"\n4️⃣  AUTO MONGODB SCRAPER ⭐")
    print(f"   python simple_mongo_scraper.py")
    print(f"   ✅ Automatically detects NEW schemes")
    print(f"   ✅ Stores directly to MongoDB Compass")
    print(f"   ✅ Avoids duplicates")
    print(f"   ✅ Uses working sites only")
    
    print(f"\n5️⃣  FULL SCRAPING (Django + MongoDB)")
    print(f"   python auto_mongodb_scraper.py")
    print(f"   ✅ Comprehensive scraping")
    print(f"   ✅ Saves to both databases")
    print(f"   ✅ More sites but slower")
    
    print(f"\n6️⃣  DJANGO SHELL COMMANDS")
    print(f"   python manage.py shell")
    print(f"   >>> from chatbot.web_scraper import scraper")
    print(f"   >>> result = scraper.scrape_central_government_sites()")
    print(f"   >>> result = scraper.run_full_scraping()")
    
    print(f"\n🎯 RECOMMENDED WORKFLOW:")
    print(f"   1. Check status: python simple_check.py")
    print(f"   2. Test sites: python test_central_sites.py")
    print(f"   3. Auto scrape: python simple_mongo_scraper.py")
    
    print(f"\n📋 NEW SCHEMES DETECTION:")
    print(f"   ✅ Compares with existing MongoDB schemes")
    print(f"   ✅ Normalizes titles for accurate comparison")
    print(f"   ✅ Only stores genuinely new schemes")
    print(f"   ✅ Adds detection metadata")
    
    print(f"\n🗄️  MONGODB COMPASS INTEGRATION:")
    print(f"   ✅ Automatic storage to MongoDB")
    print(f"   ✅ Real-time viewing in Compass")
    print(f"   ✅ Searchable by title, sector, keywords")
    print(f"   ✅ Includes detection timestamps")
    
    print(f"\n🔧 WORKING CENTRAL GOVERNMENT SITES:")
    working_sites = [
        "✅ National Portal Services (services.india.gov.in)",
        "✅ PM India Portal (pmindia.gov.in)",
        "✅ Digital India (digitalindia.gov.in)",
        "❌ India.gov.in (connection issues)",
        "🟡 MyGov India (partial)"
    ]
    
    for site in working_sites:
        print(f"   {site}")
    
    print(f"\n💡 TIPS FOR BEST RESULTS:")
    print(f"   • Run scraping during off-peak hours")
    print(f"   • Use simple_mongo_scraper.py for reliability")
    print(f"   • Check MongoDB Compass for real-time updates")
    print(f"   • Monitor logs for any errors")
    print(f"   • Run connectivity test if issues occur")
    
    print(f"\n📈 SCALING OPTIONS:")
    print(f"   • Increase max_schemes parameter for more results")
    print(f"   • Add more state portals as needed")
    print(f"   • Schedule automatic runs with cron/task scheduler")
    print(f"   • Monitor MongoDB storage usage")

def show_mongodb_status():
    """Show current MongoDB status"""
    
    print(f"\n🗄️  MONGODB COMPASS STATUS")
    print("=" * 40)
    
    try:
        mongodb = MongoDBAdapter()
        
        # Get collection stats
        total_schemes = mongodb.schemes_collection.count_documents({})
        active_schemes = mongodb.schemes_collection.count_documents({"is_active": True})
        
        # Get recent schemes
        recent_schemes = list(mongodb.schemes_collection.find(
            {"is_active": True},
            {"title": 1, "sector": 1, "created_at": 1, "_id": 0}
        ).sort("created_at", -1).limit(5))
        
        print(f"   Total Schemes: {total_schemes}")
        print(f"   Active Schemes: {active_schemes}")
        
        if recent_schemes:
            print(f"\n   📋 Recent Schemes:")
            for i, scheme in enumerate(recent_schemes, 1):
                created = scheme.get('created_at', 'Unknown')
                title = scheme.get('title', 'No Title')[:40]
                sector = scheme.get('sector', 'N/A')
                print(f"   {i}. {title}...")
                print(f"      Sector: {sector} | Added: {created}")
        
        # Show sectors
        sectors = mongodb.schemes_collection.distinct("sector", {"is_active": True})
        print(f"\n   📂 Sectors: {len(sectors)}")
        for sector in sectors[:5]:
            count = mongodb.schemes_collection.count_documents({"sector": sector, "is_active": True})
            print(f"   • {sector}: {count} schemes")
        
        print(f"\n   ✅ MongoDB is connected and ready!")
        print(f"   💾 Check MongoDB Compass to view data")
        
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        print(f"   💡 Ensure MongoDB is running and Compass is connected")

if __name__ == "__main__":
    show_scraping_options()
    show_mongodb_status()
    
    print(f"\n" + "="*60)
    print(f"🎉 Ready to start web scraping!")
    print(f"💾 New schemes will automatically store in MongoDB Compass")
    print(f"🔍 Use simple_mongo_scraper.py for best results")
    print("="*60)
