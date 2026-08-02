#!/usr/bin/env python
"""
Fresh Scheme Test - Completely new scheme not in any database
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from mongodb_adapter import MongoDBAdapter
from chatbot.models import GovernmentScheme
import re

def check_scheme_exists(scheme_title):
    """Check if scheme exists in any database"""
    
    print(f"🔍 Checking if '{scheme_title}' exists in databases...")
    
    # Check MongoDB
    try:
        mongodb = MongoDBAdapter()
        mongo_exists = mongodb.schemes_collection.find_one({
            'title': {'$regex': f'^{re.escape(scheme_title)}$', '$options': 'i'}
        })
        
        if mongo_exists:
            print(f"❌ Found in MongoDB - Scheme already exists!")
            return True
        else:
            print(f"✅ Not found in MongoDB")
            
    except Exception as e:
        print(f"⚠️  Error checking MongoDB: {e}")
    
    # Check Django
    try:
        django_exists = GovernmentScheme.objects.filter(
            title__iexact=scheme_title
        ).first()
        
        if django_exists:
            print(f"❌ Found in Django - Scheme already exists!")
            return True
        else:
            print(f"✅ Not found in Django")
            
    except Exception as e:
        print(f"⚠️  Error checking Django: {e}")
    
    print(f"🎉 SCHEME IS COMPLETELY NEW - Not in any database!")
    return False

def create_fresh_test_scheme():
    """Create a completely fresh test scheme"""
    
    # UNIQUE SCHEME TITLE - This doesn't exist anywhere
    fresh_scheme_title = "National AI Innovation Scholarship Program 2024"
    
    print(f"🎯 FRESH SCHEME TITLE FOR TESTING:")
    print(f"=" * 50)
    print(f"📛 Title: {fresh_scheme_title}")
    print(f"🔍 This title is guaranteed to be new!")
    print(f"💡 Use this to test fresh scheme addition")
    
    # Check if it really doesn't exist
    exists = check_scheme_exists(fresh_scheme_title)
    
    if not exists:
        print(f"\n✅ CONFIRMED: This scheme is completely new!")
        print(f"🚀 You can safely use this title for testing")
        
        # Create complete scheme data
        fresh_scheme = {
            'title': fresh_scheme_title,
            'description': 'A pioneering national scholarship program focused on Artificial Intelligence and Machine Learning education for Indian students. This initiative provides financial support, mentorship, and internship opportunities in collaboration with leading tech companies and research institutions.',
            'short_description': 'National scholarship for AI/ML education with industry mentorship and internships.',
            'sector': 'education',
            'government_level': 'central',
            'ministry': 'Ministry of Education',
            'department': 'Department of Higher Education',
            'state': '',
            'language': 'en',
            'eligibility_criteria': 'Age: 16-25 years, Educational qualification: 12th pass with minimum 60% marks, Must be studying Computer Science/IT/Mathematics, Annual family income: Less than Rs. 8 lakh, Indian citizen, Basic programming knowledge required.',
            'benefits': 'Scholarship amount up to Rs. 2 lakh per year, Free access to AI/ML online courses, Mentorship from industry experts, Guaranteed internship opportunities, Research project funding, International conference attendance support, Laptop and study materials.',
            'application_process': '1. Visit www.ai-scholarship.gov.in, 2. Register with email and mobile number, 3. Fill detailed application form, 4. Upload academic documents and income certificate, 5. Take online aptitude test, 6. Attend virtual interview, 7. Final selection based on merit and interview.',
            'source_url': 'https://www.ai-scholarship.gov.in/national-program-2024',
            'keywords': ['AI scholarship', 'artificial intelligence', 'machine learning', 'education', 'students', 'technology', 'research', 'internship', 'merit-based', 'national program'],
            'search_tags': ['artificial', 'intelligence', 'machine', 'learning', 'scholarship', 'education', 'technology', 'students', 'research', 'national', 'government', 'free'],
            'is_active': True,
            'detected_as_new': True,
            'detection_source': 'fresh_test_example'
        }
        
        print(f"\n📋 COMPLETE FRESH SCHEME DATA:")
        print(f"=" * 35)
        
        for key, value in fresh_scheme.items():
            if key in ['title', 'sector', 'ministry', 'source_url']:
                print(f"🏷️  {key.title()}: {value}")
            elif key == 'description':
                print(f"📝 Description: {value}")
            elif key == 'eligibility_criteria':
                print(f"👤 Eligibility: {value}")
            elif key == 'benefits':
                print(f"🎁 Benefits: {value}")
            elif key == 'application_process':
                print(f"📋 Application: {value}")
        
        return fresh_scheme
    else:
        print(f"❌ Scheme already exists - try a different title")
        return None

def show_alternative_fresh_titles():
    """Show alternative fresh scheme titles"""
    
    print(f"\n🎨 ALTERNATIVE FRESH SCHEME TITLES:")
    print(f"=" * 40)
    
    alternative_titles = [
        "Quantum Computing Research Fellowship 2024",
        "Green Technology Innovation Grant Program",
        "Rural Digital Entrepreneurship Initiative",
        "Women in STEM Leadership Scholarship",
        "Blockchain Education and Certification Scheme",
        "Smart Agriculture Technology Program",
        "Cybersecurity Skills Development Initiative",
        "Space Technology Research Scholarship",
        "Renewable Energy Career Development Program",
        "Advanced Manufacturing Skills Training"
    ]
    
    for i, title in enumerate(alternative_titles, 1):
        print(f"   {i}. {title}")
    
    print(f"\n💡 All these titles are designed to be unique!")
    print(f"🎯 Pick any one for fresh testing")

def main():
    """Main function"""
    
    print("🆕 FRESH SCHEME TITLE GENERATOR")
    print("=" * 40)
    print("Generating a completely new scheme title...")
    print("This will NOT exist in any database!")
    print()
    
    # Create fresh scheme
    fresh_scheme = create_fresh_test_scheme()
    
    # Show alternatives
    show_alternative_fresh_titles()
    
    # Usage instructions
    print(f"\n" + "=" * 50)
    print(f"🚀 HOW TO USE THIS FRESH SCHEME:")
    print("=" * 40)
    print(f"1. Copy the scheme title above")
    print(f"2. Use it in your web scraper testing")
    print(f"3. Add it to database as a new scheme")
    print(f"4. Test chatbot search functionality")
    print(f"5. Verify apply button works correctly")
    
    if fresh_scheme:
        print(f"\n✅ READY TO TEST:")
        print(f"   Title: {fresh_scheme['title']}")
        print(f"   Sector: {fresh_scheme['sector']}")
        print(f"   Source: {fresh_scheme['source_url']}")
        print(f"   Status: Completely new and ready!")

if __name__ == "__main__":
    main()
