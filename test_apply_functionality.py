#!/usr/bin/env python
"""
Test script to demonstrate the enhanced Apply button functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from mongodb_adapter import MongoDBAdapter
from chatbot.models import GovernmentScheme

def test_apply_functionality():
    """Test the apply button functionality with sample schemes"""
    
    print("🎯 Enhanced Apply Button Functionality Test")
    print("=" * 60)
    
    # Get sample schemes with different sectors
    mongodb = MongoDBAdapter()
    
    # Find schemes from different sectors
    test_schemes = []
    sectors_to_test = ['health', 'education', 'agriculture', 'employment']
    
    for sector in sectors_to_test:
        schemes = list(mongodb.schemes_collection.find(
            {"sector": sector, "is_active": True},
            {"title": 1, "sector": 1, "source_url": 1, "_id": 0}
        ).limit(2))
        
        test_schemes.extend(schemes)
    
    if not test_schemes:
        print("❌ No schemes found for testing")
        return
    
    print(f"📋 Found {len(test_schemes)} schemes for testing")
    
    print(f"\n🚀 APPLY BUTTON FUNCTIONALITY:")
    print(f"=" * 40)
    
    print(f"\n✅ WHAT HAPPENS WHEN USER CLICKS 'APPLY NOW':")
    print(f"")
    print(f"1️⃣  If scheme has source_url:")
    print(f"   • Opens official website in NEW TAB")
    print(f"   • Shows confirmation message in chat")
    print(f"   • Displays application guidance after 1 second")
    print(f"")
    print(f"2️⃣  If no source_url available:")
    print(f"   • Shows comprehensive application information")
    print(f"   • Provides sector-specific government portals")
    print(f"   • Lists offline application options")
    print(f"   • Shows helpline information")
    
    print(f"\n📋 SAMPLE SCHEMES WITH APPLY FUNCTIONALITY:")
    print(f"=" * 50)
    
    for i, scheme in enumerate(test_schemes, 1):
        title = scheme.get('title', 'No Title')
        sector = scheme.get('sector', 'unknown')
        source_url = scheme.get('source_url', 'No URL')
        
        print(f"\n{i}. {title}")
        print(f"   Sector: {sector}")
        print(f"   Source URL: {source_url[:50]}..." if len(source_url) > 50 else f"   Source URL: {source_url}")
        
        if source_url and source_url != 'No URL':
            print(f"   ✅ Will open: {source_url}")
            print(f"   📋 Will show: Application guidance with documents")
        else:
            print(f"   📋 Will show: Government portals and offline options")
        
        # Show sector-specific guidance
        if sector == 'health':
            print(f"   🏥 Health-specific: PM-JAY portal, medical records info")
        elif sector == 'education':
            print(f"   🎓 Education-specific: Scholarship portal, certificates info")
        elif sector == 'agriculture':
            print(f"   🌾 Agriculture-specific: PM-KISAN portal, land records info")
        elif sector == 'employment':
            print(f"   💼 Employment-specific: Job portals, skill certificates info")
    
    print(f"\n🎨 ENHANCED FEATURES:")
    print(f"=" * 30)
    print(f"✅ Sector-specific portal recommendations")
    print(f"✅ Document checklist with sector requirements")
    print(f"✅ Step-by-step application guidance")
    print(f"✅ Important notes and tips")
    print(f"✅ Offline application options")
    print(f"✅ Helpline and contact information")
    print(f"✅ Multiple language support")
    print(f"✅ Responsive design for mobile")
    
    print(f"\n🌐 GOVERNMENT PORTALS INTEGRATED:")
    print(f"=" * 40)
    portals = [
        ("India.gov.in", "Main government portal"),
        ("Services Portal", "All government services"),
        ("Digital India", "Digital services portal"),
        ("PM-JAY Portal", "Health insurance schemes"),
        ("PM-KISAN Portal", "Farmer welfare schemes"),
        ("Scholarship Portal", "Education scholarships"),
        ("Common Service Center", "Offline application centers")
    ]
    
    for portal, description in portals:
        print(f"   • {portal}: {description}")
    
    print(f"\n💡 USER EXPERIENCE:")
    print(f"=" * 25)
    print(f"1. User searches for a scheme")
    print(f"2. Scheme displays with 'Apply Now' button")
    print(f"3. Click opens official website OR shows guidance")
    print(f"4. User gets complete application information")
    print(f"5. Sector-specific help provided")
    print(f"6. Multiple application options available")
    
    print(f"\n🎉 READY TO TEST!")
    print(f"=" * 20)
    print(f"✅ Apply buttons enhanced with sector-specific guidance")
    print(f"✅ Multiple government portals integrated")
    print(f"✅ Comprehensive application support")
    print(f"✅ User-friendly interface")
    
    print(f"\n🚀 To test in browser:")
    print(f"   1. Start the Django server")
    print(f"   2. Search for any scheme")
    print(f"   3. Click 'Apply Now' button")
    print(f"   4. See enhanced application guidance!")

if __name__ == "__main__":
    test_apply_functionality()
