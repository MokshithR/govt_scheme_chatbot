#!/usr/bin/env python
"""
Auto Web Scraper - Automatically detects new schemes and stores in MongoDB Compass
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.web_scraper import GovernmentPortalScraper, ScrapingConfig
from chatbot.models import GovernmentScheme, WebScrapingLog
from mongodb_adapter import MongoDBAdapter
import re
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoSchemeDetector:
    """Automatic new scheme detection and MongoDB storage"""
    
    def __init__(self):
        self.scraper = GovernmentPortalScraper()
        self.mongodb = MongoDBAdapter()
        self.new_schemes_buffer = []
        
    def load_existing_schemes_from_mongodb(self):
        """Load existing scheme titles from MongoDB for comparison"""
        try:
            # Get all existing schemes from MongoDB
            existing_schemes = list(self.mongodb.schemes_collection.find(
                {"is_active": True}, 
                {"title": 1, "_id": 0}
            ))
            
            existing_titles = set()
            for scheme in existing_schemes:
                if 'title' in scheme:
                    # Normalize title for comparison
                    normalized = scheme['title'].lower().strip()
                    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
                    normalized = re.sub(r'\s+', ' ', normalized)
                    existing_titles.add(normalized)
            
            logger.info(f"Loaded {len(existing_titles)} existing schemes from MongoDB")
            return existing_titles
            
        except Exception as e:
            logger.error(f"Error loading existing schemes from MongoDB: {e}")
            return set()
    
    def load_existing_schemes_from_django(self):
        """Load existing scheme titles from Django DB for comparison"""
        try:
            existing_schemes = GovernmentScheme.objects.all()
            existing_titles = set()
            
            for scheme in existing_schemes:
                # Normalize title for comparison
                normalized = scheme.title.lower().strip()
                normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
                normalized = re.sub(r'\s+', ' ', normalized)
                existing_titles.add(normalized)
            
            logger.info(f"Loaded {len(existing_titles)} existing schemes from Django DB")
            return existing_titles
            
        except Exception as e:
            logger.error(f"Error loading existing schemes from Django DB: {e}")
            return set()
    
    def is_new_scheme(self, scheme_title, existing_titles):
        """Check if a scheme is new compared to existing titles"""
        # Normalize scraped title
        normalized = scheme_title.lower().strip()
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized not in existing_titles
    
    def scrape_and_detect_new_schemes(self, max_schemes=20):
        """Scrape schemes and detect new ones"""
        logger.info("Starting automatic new scheme detection...")
        
        # Load existing schemes from both databases
        mongodb_titles = self.load_existing_schemes_from_mongodb()
        django_titles = self.load_existing_schemes_from_django()
        
        # Combine all existing titles
        all_existing_titles = mongodb_titles.union(django_titles)
        logger.info(f"Total existing schemes to check against: {len(all_existing_titles)}")
        
        # Scrape new schemes
        logger.info("Scraping central government schemes from multiple sites...")
        central_schemes = self.scraper.scrape_central_government_sites()
        
        logger.info("Scraping state government schemes...")
        state_schemes = self.scraper.scrape_state_government_sites()
        
        all_scraped_schemes = central_schemes + state_schemes
        logger.info(f"Total schemes scraped: {len(all_scraped_schemes)}")
        
        # Detect new schemes
        new_schemes = []
        duplicate_count = 0
        
        for scheme in all_scraped_schemes[:max_schemes]:  # Limit for processing
            title = scheme.get('title', '')
            
            if self.is_new_scheme(title, all_existing_titles):
                # Add metadata for new scheme
                scheme['detected_as_new'] = True
                scheme['detection_date'] = datetime.now()
                scheme['detection_source'] = 'auto_web_scraper'
                new_schemes.append(scheme)
                logger.info(f"✅ NEW SCHEME DETECTED: {title}")
            else:
                duplicate_count += 1
                logger.debug(f"🔄 Existing scheme: {title}")
        
        logger.info(f"Detection complete: {len(new_schemes)} new schemes, {duplicate_count} duplicates")
        return new_schemes
    
    def store_new_schemes_in_mongodb(self, new_schemes):
        """Store new schemes in MongoDB Compass"""
        if not new_schemes:
            logger.info("No new schemes to store")
            return {'stored': 0, 'errors': 0}
        
        logger.info(f"Storing {len(new_schemes)} new schemes in MongoDB...")
        
        stored_count = 0
        error_count = 0
        
        for scheme in new_schemes:
            try:
                # Prepare scheme data for MongoDB
                mongodb_scheme = {
                    'title': scheme.get('title', ''),
                    'description': scheme.get('description', ''),
                    'short_description': scheme.get('short_description', ''),
                    'sector': scheme.get('sector', 'other'),
                    'government_level': scheme.get('government_level', 'central'),
                    'ministry': scheme.get('ministry', 'Government of India'),
                    'department': scheme.get('department', 'Various Departments'),
                    'state': scheme.get('state', ''),
                    'language': scheme.get('language', 'en'),
                    'eligibility_criteria': scheme.get('eligibility_criteria', ''),
                    'benefits': scheme.get('benefits', ''),
                    'application_process': scheme.get('application_process', ''),
                    'source_url': scheme.get('source_url', ''),
                    'keywords': scheme.get('keywords', []),
                    'search_tags': scheme.get('search_tags', []),
                    'is_active': True,
                    'created_at': datetime.now(),
                    'last_updated': datetime.now(),
                    'detected_as_new': scheme.get('detected_as_new', False),
                    'detection_date': scheme.get('detection_date', datetime.now()),
                    'detection_source': scheme.get('detection_source', 'auto_web_scraper')
                }
                
                # Check if already exists in MongoDB (double check)
                title_pattern = f'^{re.escape(scheme.get("title", ""))}$'
                existing = self.mongodb.schemes_collection.find_one({
                    'title': {'$regex': title_pattern, '$options': 'i'}
                })
                
                if existing:
                    logger.warning(f"Scheme already exists in MongoDB: {scheme.get('title', '')}")
                    continue
                
                # Insert into MongoDB
                result = self.mongodb.schemes_collection.insert_one(mongodb_scheme)
                
                if result.inserted_id:
                    stored_count += 1
                    logger.info(f"✅ Stored in MongoDB: {scheme.get('title', '')}")
                else:
                    error_count += 1
                    logger.error(f"Failed to store: {scheme.get('title', '')}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error storing scheme {scheme.get('title', '')}: {e}")
        
        logger.info(f"MongoDB storage complete: {stored_count} stored, {error_count} errors")
        return {'stored': stored_count, 'errors': error_count}
    
    def also_store_in_django(self, new_schemes):
        """Optionally also store in Django DB"""
        if not new_schemes:
            return {'stored': 0, 'errors': 0}
        
        logger.info(f"Also storing {len(new_schemes)} new schemes in Django DB...")
        
        # Use the existing scraper method
        result = self.scraper.save_schemes_to_database(new_schemes)
        logger.info(f"Django DB storage complete: {result}")
        return result
    
    def run_auto_detection_and_storage(self, max_schemes=20, store_in_django=False):
        """Complete automatic detection and storage process"""
        logger.info("🚀 Starting automatic new scheme detection and storage...")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape and detect new schemes
            new_schemes = self.scrape_and_detect_new_schemes(max_schemes)
            
            if not new_schemes:
                logger.info("No new schemes detected")
                return {
                    'new_schemes_found': 0,
                    'stored_in_mongodb': 0,
                    'stored_in_django': 0,
                    'duration_seconds': 0,
                    'status': 'no_new_schemes'
                }
            
            # Step 2: Store in MongoDB
            mongodb_result = self.store_new_schemes_in_mongodb(new_schemes)
            
            # Step 3: Optionally store in Django
            django_result = {'stored': 0, 'errors': 0}
            if store_in_django:
                django_result = self.also_store_in_django(new_schemes)
            
            # Calculate duration
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            # Create log entry
            log_entry = WebScrapingLog(
                source_url="Auto Detection - Multiple Sources",
                source_name="Auto Web Scraper",
                status="success",
                started_at=start_time,
                completed_at=end_time,
                schemes_found=len(new_schemes),
                duration_seconds=duration
            )
            log_entry.save()
            
            final_result = {
                'new_schemes_found': len(new_schemes),
                'stored_in_mongodb': mongodb_result['stored'],
                'mongodb_errors': mongodb_result['errors'],
                'stored_in_django': django_result.get('stored', 0),
                'django_errors': django_result.get('errors', 0),
                'duration_seconds': duration,
                'status': 'success',
                'new_schemes': new_schemes[:5]  # Return first 5 for preview
            }
            
            logger.info(f"🎉 Auto detection completed: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"Auto detection failed: {e}")
            return {
                'new_schemes_found': 0,
                'stored_in_mongodb': 0,
                'stored_in_django': 0,
                'duration_seconds': 0,
                'status': 'failed',
                'error': str(e)
            }

def run_auto_scraper():
    """Run the automatic scraper"""
    detector = AutoSchemeDetector()
    
    print("🤖 Auto Web Scraper for MongoDB Compass")
    print("=" * 60)
    
    # Run automatic detection and storage
    result = detector.run_auto_detection_and_storage(
        max_schemes=15,  # Limit for demo
        store_in_django=True  # Also store in Django
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   New schemes found: {result['new_schemes_found']}")
    print(f"   Stored in MongoDB: {result['stored_in_mongodb']}")
    print(f"   Stored in Django: {result['stored_in_django']}")
    print(f"   Duration: {result['duration_seconds']}s")
    print(f"   Status: {result['status']}")
    
    if result.get('new_schemes'):
        print(f"\n✅ NEW SCHEMES STORED:")
        for i, scheme in enumerate(result['new_schemes'], 1):
            print(f"   {i}. {scheme['title']}")
            print(f"      Sector: {scheme['sector']}")
            print(f"      Language: {scheme['language']}")
    
    return result

if __name__ == "__main__":
    run_auto_scraper()
