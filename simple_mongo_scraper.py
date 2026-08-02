#!/usr/bin/env python
"""
Simple Auto MongoDB Scraper - Uses only working central government sites
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
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMongoDBAutoScraper:
    """Simple auto scraper that focuses on working sites"""
    
    def __init__(self):
        # Use only working sites based on our test
        self.working_portals = [
            {
                'name': 'National Portal Services',
                'urls': [
                    "https://services.india.gov.in/",
                    "https://services.india.gov.in/service/listing?cat_id=2"
                ],
                'selectors': ['.service-list a', '.scheme-item a', 'a[href*="service"]', '.listing a'],
                'language': 'en'
            },
            {
                'name': 'PM India Portal',
                'urls': [
                    "https://www.pmindia.gov.in/en/"
                ],
                'selectors': ['a[href*="scheme"]', '.scheme-list a', '.initiative-item a'],
                'language': 'en'
            },
            {
                'name': 'Digital India',
                'urls': [
                    "https://digitalindia.gov.in/"
                ],
                'selectors': ['.initiative-card a', '.scheme-item a', 'a[href*="initiative"]'],
                'language': 'en'
            }
        ]
        
        self.mongodb = MongoDBAdapter()
        self.scraper = GovernmentPortalScraper()
        
    def load_existing_schemes(self):
        """Load existing scheme titles from MongoDB"""
        try:
            existing_schemes = list(self.mongodb.schemes_collection.find(
                {"is_active": True}, 
                {"title": 1, "_id": 0}
            ))
            
            existing_titles = set()
            for scheme in existing_schemes:
                if 'title' in scheme:
                    normalized = scheme['title'].lower().strip()
                    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
                    normalized = re.sub(r'\s+', ' ', normalized)
                    existing_titles.add(normalized)
            
            logger.info(f"Loaded {len(existing_titles)} existing schemes from MongoDB")
            return existing_titles
            
        except Exception as e:
            logger.error(f"Error loading existing schemes: {e}")
            return set()
    
    def is_new_scheme(self, title, existing_titles):
        """Check if scheme is new"""
        normalized = title.lower().strip()
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized not in existing_titles
    
    def scrape_working_portals(self, max_schemes=10):
        """Scrape only working portals"""
        logger.info("Scraping working central government portals...")
        
        all_schemes = []
        
        for portal in self.working_portals:
            try:
                logger.info(f"Scraping {portal['name']}...")
                portal_schemes = self._scrape_portal_simple(portal, max_schemes)
                all_schemes.extend(portal_schemes)
                logger.info(f"Got {len(portal_schemes)} schemes from {portal['name']}")
                
            except Exception as e:
                logger.error(f"Error scraping {portal['name']}: {e}")
                continue
        
        return all_schemes
    
    def _scrape_portal_simple(self, portal, max_schemes):
        """Simple portal scraping without deep page scraping"""
        schemes = []
        
        try:
            for url in portal['urls']:
                try:
                    response = self.scraper._make_request_with_retry(url)
                    if not response:
                        continue
                        
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find scheme/service items
                    scheme_elements = []
                    for selector in portal.get('selectors', ['a']):
                        elements = soup.select(selector)
                        if elements:
                            scheme_elements = elements[:max_schemes]
                            break
                    
                    # Extract scheme data from elements
                    for element in scheme_elements:
                        try:
                            title = element.get_text().strip()
                            
                            if len(title) > 10 and len(title) < 200:
                                description = element.get('title', '') or title
                                
                                scheme_data = {
                                    'title': title,
                                    'description': description[:500],
                                    'short_description': description[:300],
                                    'source_url': url,
                                    'source_portal': portal['name'],
                                    'government_level': 'central',
                                    'ministry': 'Government of India',
                                    'department': 'Various Departments',
                                    'sector': self.scraper._categorize_scheme(title, description),
                                    'language': portal.get('language', 'en'),
                                    'is_active': True,
                                    'keywords': self.scraper._extract_keywords(title, description),
                                    'search_tags': self.scraper._generate_search_tags(title, description)
                                }
                                
                                schemes.append(scheme_data)
                                
                        except Exception as e:
                            continue
                    
                    if len(schemes) >= max_schemes:
                        break
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in portal scraping: {e}")
        
        return schemes
    
    def detect_and_store_new_schemes(self, max_schemes=10):
        """Detect new schemes and store in MongoDB"""
        logger.info("🚀 Starting simple auto detection and storage...")
        
        try:
            # Load existing schemes
            existing_titles = self.load_existing_schemes()
            
            # Scrape new schemes
            scraped_schemes = self.scrape_working_portals(max_schemes)
            logger.info(f"Scraped {len(scraped_schemes)} schemes")
            
            # Detect new schemes
            new_schemes = []
            for scheme in scraped_schemes:
                if self.is_new_scheme(scheme['title'], existing_titles):
                    scheme['detected_as_new'] = True
                    scheme['detection_date'] = datetime.now()
                    scheme['detection_source'] = 'simple_auto_scraper'
                    new_schemes.append(scheme)
                    logger.info(f"✅ NEW: {scheme['title']}")
                else:
                    logger.debug(f"🔄 Existing: {scheme['title']}")
            
            # Store new schemes in MongoDB
            stored_count = 0
            error_count = 0
            
            for scheme in new_schemes:
                try:
                    mongodb_scheme = {
                        'title': scheme['title'],
                        'description': scheme['description'],
                        'short_description': scheme['short_description'],
                        'sector': scheme['sector'],
                        'government_level': scheme['government_level'],
                        'ministry': scheme['ministry'],
                        'department': scheme['department'],
                        'language': scheme['language'],
                        'source_url': scheme['source_url'],
                        'keywords': scheme['keywords'],
                        'search_tags': scheme['search_tags'],
                        'is_active': True,
                        'created_at': datetime.now(),
                        'last_updated': datetime.now(),
                        'detected_as_new': scheme['detected_as_new'],
                        'detection_date': scheme['detection_date'],
                        'detection_source': scheme['detection_source']
                    }
                    
                    result = self.mongodb.schemes_collection.insert_one(mongodb_scheme)
                    if result.inserted_id:
                        stored_count += 1
                        logger.info(f"✅ Stored in MongoDB: {scheme['title']}")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error storing {scheme['title']}: {e}")
            
            result = {
                'scraped': len(scraped_schemes),
                'new_found': len(new_schemes),
                'stored_in_mongodb': stored_count,
                'errors': error_count,
                'status': 'success'
            }
            
            logger.info(f"🎉 Complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Auto detection failed: {e}")
            return {'status': 'failed', 'error': str(e)}

def run_simple_auto_scraper():
    """Run the simple auto scraper"""
    scraper = SimpleMongoDBAutoScraper()
    
    print("🤖 Simple Auto MongoDB Scraper")
    print("=" * 50)
    
    result = scraper.detect_and_store_new_schemes(max_schemes=8)
    
    print(f"\n📊 RESULTS:")
    print(f"   Schemes scraped: {result.get('scraped', 0)}")
    print(f"   New schemes found: {result.get('new_found', 0)}")
    print(f"   Stored in MongoDB: {result.get('stored_in_mongodb', 0)}")
    print(f"   Errors: {result.get('errors', 0)}")
    print(f"   Status: {result.get('status', 'unknown')}")
    
    return result

if __name__ == "__main__":
    run_simple_auto_scraper()
