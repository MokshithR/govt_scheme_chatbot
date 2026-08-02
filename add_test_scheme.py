#!/usr/bin/env python
"""
Complete Example: Add New Scheme to Test Chatbot
Shows how to add a new scheme and test it in the chatbot
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
import re

def create_test_scheme():
    """Create a complete test scheme example"""
    
    test_scheme = {
        'title': 'Digital Skills for Youth Program 2024',
        'description': 'A comprehensive digital skills training program for youth aged 18-35, offering free courses in programming, digital marketing, data analytics, and artificial intelligence. The program includes certification, placement assistance, and stipend for eligible candidates.',
        'short_description': 'Free digital skills training with certification and placement support for youth.',
        'sector': 'employment',
        'government_level': 'central',
        'ministry': 'Ministry of Skill Development and Entrepreneurship',
        'department': 'Department of Technical Education',
        'state': '',
        'language': 'en',
        'eligibility_criteria': 'Age: 18-35 years, Educational qualification: Minimum 10th pass, Annual family income: Less than Rs. 3 lakh, Must have basic computer knowledge, Indian citizen with valid Aadhaar card.',
        'benefits': 'Free training courses worth Rs. 50,000, Monthly stipend of Rs. 3000 during training, Industry-recognized certification, Placement assistance with top companies, Access to online learning platform, Mentorship from industry experts.',
        'application_process': '1. Register on the official portal www.digitalskills.gov.in, 2. Fill the application form with personal details, 3. Upload required documents (Aadhaar, income certificate, educational certificates), 4. Submit the application and take the online assessment test, 5. Selected candidates will receive confirmation via email and SMS.',
        'source_url': 'https://www.digitalskills.gov.in/youth-program-2024',
        'keywords': ['digital skills', 'youth training', 'programming', 'certification', 'placement', 'free courses', 'skill development', 'employment'],
        'search_tags': ['digital', 'skills', 'youth', 'training', 'employment', 'certification', 'technology', 'career', 'free', 'government'],
        'is_active': True,
        'created_at': datetime.now(),
        'last_updated': datetime.now(),
        'detected_as_new': True,
        'detection_date': datetime.now(),
        'detection_source': 'test_example'
    }
    
    return test_scheme

def add_scheme_to_mongodb(scheme):
    """Add scheme to MongoDB database"""
    
    print("💾 Adding new scheme to MongoDB...")
    
    try:
        mongodb = MongoDBAdapter()
        
        # Check if scheme already exists
        existing = mongodb.schemes_collection.find_one({
            'title': {'$regex': f'^{re.escape(scheme["title"])}$', '$options': 'i'}
        })
        
        if existing:
            print(f"❌ Scheme already exists: {scheme['title']}")
            return False
        
        # Insert new scheme
        result = mongodb.schemes_collection.insert_one(scheme)
        
        if result.inserted_id:
            print(f"✅ Successfully added to MongoDB:")
            print(f"   Title: {scheme['title']}")
            print(f"   Sector: {scheme['sector']}")
            print(f"   Ministry: {scheme['ministry']}")
            print(f"   Document ID: {result.inserted_id}")
            return True
        else:
            print(f"❌ Failed to add to MongoDB")
            return False
            
    except Exception as e:
        print(f"❌ Error adding to MongoDB: {e}")
        return False

def add_scheme_to_django(scheme):
    """Add scheme to Django database"""
    
    print("\n💾 Adding new scheme to Django database...")
    
    try:
        # Check if already exists
        existing = GovernmentScheme.objects.filter(
            title__iexact=scheme['title']
        ).first()
        
        if existing:
            print(f"❌ Scheme already exists in Django: {scheme['title']}")
            return False
        
        # Create new scheme
        new_scheme = GovernmentScheme(
            title=scheme['title'],
            description=scheme['description'],
            short_description=scheme['short_description'],
            sector=scheme['sector'],
            government_level=scheme['government_level'],
            ministry=scheme['ministry'],
            department=scheme['department'],
            state=scheme['state'],
            language=scheme['language'],
            eligibility_criteria=scheme['eligibility_criteria'],
            benefits=scheme['benefits'],
            application_process=scheme['application_process'],
            source_url=scheme['source_url'],
            keywords=scheme['keywords'],
            search_tags=scheme['search_tags'],
            is_active=scheme['is_active'],
            launch_date=datetime.now().date(),  # Add missing launch_date
            last_updated=scheme['last_updated']
        )
        
        new_scheme.save()
        
        print(f"✅ Successfully added to Django:")
        print(f"   Title: {scheme['title']}")
        print(f"   ID: {new_scheme.id}")
        print(f"   Sector: {scheme['sector']}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding to Django: {e}")
        return False

def verify_scheme_in_databases(scheme_title):
    """Verify scheme exists in both databases"""
    
    print(f"\n🔍 Verifying scheme in databases...")
    
    # Check MongoDB
    try:
        mongodb = MongoDBAdapter()
        mongo_scheme = mongodb.schemes_collection.find_one({
            'title': {'$regex': f'^{re.escape(scheme_title)}$', '$options': 'i'}
        })
        
        if mongo_scheme:
            print(f"✅ Found in MongoDB:")
            print(f"   Title: {mongo_scheme['title']}")
            print(f"   Sector: {mongo_scheme['sector']}")
            print(f"   Created: {mongo_scheme['created_at']}")
        else:
            print(f"❌ Not found in MongoDB")
            
    except Exception as e:
        print(f"❌ Error checking MongoDB: {e}")
    
    # Check Django
    try:
        django_scheme = GovernmentScheme.objects.filter(
            title__iexact=scheme_title
        ).first()
        
        if django_scheme:
            print(f"✅ Found in Django:")
            print(f"   Title: {django_scheme.title}")
            print(f"   ID: {django_scheme.id}")
            print(f"   Sector: {django_scheme.sector}")
            print(f"   Updated: {django_scheme.last_updated}")
        else:
            print(f"❌ Not found in Django")
            
    except Exception as e:
        print(f"❌ Error checking Django: {e}")

def show_chatbot_test_queries(scheme_title):
    """Show test queries for the chatbot"""
    
    print(f"\n🤖 CHATBOT TEST QUERIES")
    print("=" * 40)
    
    test_queries = [
        f"Tell me about {scheme_title}",
        f"What are the benefits of {scheme_title}?",
        f"Who is eligible for {scheme_title}?",
        f"How to apply for {scheme_title}?",
        "Digital skills training programs",
        "Free certification courses for youth",
        "Government schemes for employment",
        "Skill development programs 2024",
        "Youth training with placement",
        "Digital marketing government course"
    ]
    
    print("Test these queries in your chatbot:")
    for i, query in enumerate(test_queries, 1):
        print(f"   {i}. \"{query}\"")
    
    print(f"\n💡 Expected Results:")
    print(f"   • Chatbot should find the new scheme")
    print(f"   • Show detailed information about the program")
    print(f"   • Display eligibility criteria")
    print(f"   • Show application process")
    print(f"   • Provide apply button with link")

def show_scheme_details(scheme):
    """Display complete scheme details"""
    
    print(f"\n📋 COMPLETE SCHEME DETAILS")
    print("=" * 40)
    
    print(f"🏷️  Title: {scheme['title']}")
    print(f"📂 Sector: {scheme['sector']}")
    print(f"🏛️  Ministry: {scheme['ministry']}")
    print(f"🌐 Language: {scheme['language']}")
    print(f"🔗 Source: {scheme['source_url']}")
    print(f"\n📝 Description:")
    print(f"   {scheme['description']}")
    print(f"\n👤 Eligibility:")
    print(f"   {scheme['eligibility_criteria']}")
    print(f"\n🎁 Benefits:")
    print(f"   {scheme['benefits']}")
    print(f"\n📋 Application Process:")
    print(f"   {scheme['application_process']}")
    print(f"\n🏷️  Keywords: {', '.join(scheme['keywords'])}")
    print(f"🔍 Search Tags: {', '.join(scheme['search_tags'])}")

def main():
    """Main function to run the complete example"""
    
    print("🎯 COMPLETE EXAMPLE: Add New Scheme to Test Chatbot")
    print("=" * 60)
    
    # Step 1: Create test scheme
    print("📝 Step 1: Creating test scheme...")
    test_scheme = create_test_scheme()
    show_scheme_details(test_scheme)
    
    # Step 2: Add to MongoDB
    print(f"\n" + "=" * 60)
    print("💾 Step 2: Adding to databases...")
    mongo_success = add_scheme_to_mongodb(test_scheme)
    django_success = add_scheme_to_django(test_scheme)
    
    # Step 3: Verify addition
    print(f"\n" + "=" * 60)
    print("🔍 Step 3: Verifying scheme addition...")
    verify_scheme_in_databases(test_scheme['title'])
    
    # Step 4: Show chatbot test queries
    print(f"\n" + "=" * 60)
    show_chatbot_test_queries(test_scheme['title'])
    
    # Step 5: Summary
    print(f"\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 20)
    
    if mongo_success and django_success:
        print(f"✅ SUCCESS: New scheme added to both databases")
        print(f"✅ Ready to test in chatbot")
        print(f"✅ Scheme: {test_scheme['title']}")
    elif mongo_success or django_success:
        print(f"⚠️  PARTIAL SUCCESS: Added to one database")
    else:
        print(f"❌ FAILED: Could not add scheme to databases")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Start your Django server")
    print(f"   2. Open the chatbot interface")
    print(f"   3. Try the test queries shown above")
    print(f"   4. Verify the scheme appears in search results")
    print(f"   5. Test the apply button functionality")
    
    return test_scheme

if __name__ == "__main__":
    main()
