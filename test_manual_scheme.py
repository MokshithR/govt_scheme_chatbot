#!/usr/bin/env python
"""
Manually add Garib Kalyan Rojgar Abhiyaan to test the system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme
from datetime import datetime, date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_garib_kalyan_rojgar_abhiyaan():
    """Manually add Garib Kalyan Rojgar Abhiyaan scheme to the database"""
    
    print("🏛️ Adding Garib Kalyan Rojgar Abhiyaan to database...")
    
    # Check if scheme already exists
    existing = GovernmentScheme.objects.filter(title__icontains="garib kalyan rojgar").first()
    if existing:
        print(f"⚠️ Scheme already exists: {existing.title}")
        return existing
    
    # Create the scheme
    scheme = GovernmentScheme(
        title="Garib Kalyan Rojgar Abhiyaan",
        description="The Garib Kalyan Rojgar Abhiyaan (GKRA) is a public works program launched by the Government of India to provide employment opportunities to migrant workers and rural citizens who were affected by the COVID-19 pandemic. The scheme aims to empower and provide livelihood opportunities in rural areas by intensifying natural resource management works and focusing on 25 different types of works across 116 districts in 6 states.",
        short_description="A public works program providing employment to migrant workers and rural citizens affected by COVID-19.",
        sector="employment",
        sub_sectors=["rural_development", "employment", "social_welfare"],
        ministry="Ministry of Rural Development",
        department="Department of Rural Development",
        government_level="central",
        eligibility_criteria="Migrant workers and rural citizens who returned to their villages due to COVID-19 lockdown. Citizens from 116 districts across 6 states (Bihar, Jharkhand, Madhya Pradesh, Odisha, Rajasthan, and Uttar Pradesh) are eligible.",
        benefits="1. Employment opportunities in rural areas\n2. Wage employment for 125 days per worker\n3. Focus on 25 types of works including rural infrastructure, water conservation, and sanitation\n4. Immediate livelihood support to affected families",
        financial_assistance="Wage employment as per Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA) rates",
        application_process="1. Register at local Gram Panchayat\n2. Submit job card application\n3. Provide proof of residence and identity\n4. Contact local Rural Development Department office",
        required_documents=["Aadhaar Card", "Residence Proof", "Identity Card", "Bank Account Details", "Job Card"],
        launch_date=date(2020, 6, 20),
        validity_period="125 days per worker (extendable based on need)",
        helpline_number="1800-425-9399",
        website="https://ruraldevelopment.gov.in/garib-kalyan-rojgar-abhiyaan",
        source_url="https://ruraldevelopment.gov.in/garib-kalyan-rojgar-abhiyaan",
        language="en",
        keywords=["garib", "kalyan", "rojgar", "abhiyaan", "employment", "rural", "migrant", "workers", "covid", "public works", "mgnrega"],
        search_tags=["garib kalyan rojgar abhiyaan", "employment scheme", "rural employment", "migrant workers", "public works program", "covid relief", "rural development"],
        is_active=True
    )
    
    try:
        scheme.save()
        print(f"✅ Successfully added scheme: {scheme.title}")
        print(f"   ID: {scheme.id}")
        print(f"   Sector: {scheme.sector}")
        print(f"   Ministry: {scheme.ministry}")
        print(f"   Launch Date: {scheme.launch_date}")
        print(f"   Keywords: {scheme.keywords}")
        print(f"   Search Tags: {scheme.search_tags}")
        return scheme
        
    except Exception as e:
        print(f"❌ Error saving scheme: {e}")
        return None

def test_scheme_search():
    """Test if the scheme can be found through search"""
    
    print("\n🔍 Testing scheme search functionality...")
    
    # Test different search queries
    search_queries = [
        "Garib Kalyan Rojgar Abhiyaan",
        "garib kalyan",
        "rojgar abhiyaan", 
        "employment scheme",
        "migrant workers",
        "rural employment"
    ]
    
    for query in search_queries:
        print(f"\n📋 Searching for: '{query}'")
        
        # Search in title
        title_matches = GovernmentScheme.objects.filter(
            title__icontains=query,
            is_active=True
        )
        
        # Search in description
        desc_matches = GovernmentScheme.objects.filter(
            description__icontains=query,
            is_active=True
        )
        
        # Search in keywords
        keyword_matches = GovernmentScheme.objects.filter(
            keywords__contains=[query.lower()],
            is_active=True
        )
        
        # Search in search tags
        tag_matches = GovernmentScheme.objects.filter(
            search_tags__contains=[query.lower()],
            is_active=True
        )
        
        total_matches = title_matches.count() + desc_matches.count() + keyword_matches.count() + tag_matches.count()
        
        if total_matches > 0:
            print(f"   ✅ Found {total_matches} matches")
            for scheme in title_matches:
                print(f"      📄 {scheme.title} (Title match)")
        else:
            print(f"   ❌ No matches found")

if __name__ == "__main__":
    # Add the scheme
    scheme = add_garib_kalyan_rojgar_abhiyaan()
    
    if scheme:
        # Test search functionality
        test_scheme_search()
        
        print(f"\n🎉 SUCCESS: Garib Kalyan Rojgar Abhiyaan has been added to the database!")
        print(f"   The scheme should now be available in your chatbot search results.")
    else:
        print(f"\n❌ FAILED: Could not add the scheme to the database.")
