"""
Web scraping module for government portals
Fetches scheme information from various government websites
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime, date
from urllib.parse import urljoin, urlparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import json
from typing import List, Dict, Optional, Tuple
import random
from dataclasses import dataclass
from .models import GovernmentScheme, WebScrapingLog
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for web scraping"""
    max_schemes_per_source: int = 50
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0
    timeout: int = 30
    retry_attempts: int = 3
    save_to_file: bool = True
    use_selenium: bool = False
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]


class GovernmentPortalScraper:
    """Enhanced scraper for government portals with better error handling and rate limiting"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.driver = None
        self.scraped_urls = set()  # Track scraped URLs to avoid duplicates
        # Optionally initialize Selenium WebDriver if configured
        if self.config.use_selenium:
            self._setup_selenium()
        logger.info(f"Web scraper initialized (use_selenium={self.config.use_selenium})")
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver with enhanced options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster scraping
            chrome_options.add_argument(f'--user-agent={random.choice(self.config.user_agents)}')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.config.timeout)
            self.driver.implicitly_wait(10)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            self.driver = None
    
    def __del__(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def _make_request_with_retry(self, url: str, use_selenium: bool = False) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                # Rotate user agent
                self.session.headers['User-Agent'] = random.choice(self.config.user_agents)
                # If Selenium requested and driver is available, try it first
                if use_selenium and self.driver:
                    try:
                        self.driver.get(url)
                        html = self.driver.page_source
                        # build a lightweight response-like object
                        class SimpleResp:
                            def __init__(self, text, url):
                                self.content = text.encode('utf-8')
                                self.status_code = 200
                                self.url = url
                        return SimpleResp(html, url)
                    except Exception as se:
                        logger.warning(f"Selenium fetch failed for {url}: {se}")

                # Fallback to requests
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                # if response is suspiciously short and selenium is allowed, try selenium once
                if self.config.use_selenium and len(response.content) < 500:
                    logger.debug(f"Response small ({len(response.content)} bytes) for {url}, trying Selenium fallback")
                    if not self.driver:
                        self._setup_selenium()
                    if self.driver:
                        try:
                            self.driver.get(url)
                            html = self.driver.page_source
                            class SimpleResp:
                                def __init__(self, text, url):
                                    self.content = text.encode('utf-8')
                                    self.status_code = 200
                                    self.url = url
                            return SimpleResp(html, url)
                        except Exception as se:
                            logger.warning(f"Selenium fallback failed for {url}: {se}")
                return response
                    
            except (requests.RequestException, TimeoutException, WebDriverException) as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    delay = random.uniform(2, 5)
                    time.sleep(delay)
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
        
        return None
    
    def _random_delay(self):
        """Add random delay to be respectful to servers"""
        delay = random.uniform(self.config.request_delay_min, self.config.request_delay_max)
        time.sleep(delay)
    
    def scrape_central_government_sites(self) -> List[Dict]:
        """Enhanced scraping from multiple central government websites"""
        schemes = []
        log_entry = WebScrapingLog(
            source_url="Multiple Central Government Sites",
            source_name="Central Government Portals",
            status="started",
            started_at=datetime.now()
        )
        
        try:
            # Multiple reliable central government portals
            central_portals = [
                {
                    'name': 'India.gov.in Schemes',
                    'urls': [
                        "https://www.india.gov.in/my-government/schemes",
                        "https://www.india.gov.in/my-government/schemes/central-schemes",
                        "https://www.india.gov.in/my-government/schemes/state-schemes"
                    ],
                    'selectors': ['a[href*="scheme"]', 'a[href*="yojana"]', '.scheme-list a', '.schemes a'],
                    'language': 'en'
                },
                {
                    'name': 'MyGov India',
                    'urls': [
                        "https://www.mygov.in/schemes/",
                        "https://www.mygov.in/groups/overview/government-schemes/"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-item a', '.card-scheme a', '.schemes-list a'],
                    'language': 'en'
                },
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
                        "https://www.pmindia.gov.in/en/",
                        "https://www.pmindia.gov.in/en/government-schemes/"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-list a', '.initiative-item a'],
                    'language': 'en'
                },
                {
                    'name': 'Digital India',
                    'urls': [
                        "https://digitalindia.gov.in/",
                        "https://digitalindia.gov.in/initiatives/"
                    ],
                    'selectors': ['.initiative-card a', '.scheme-item a', 'a[href*="initiative"]'],
                    'language': 'en'
                },
                {
                    'name': 'Ministry of Rural Development',
                    'urls': [
                        "https://ruraldevelopment.gov.in/schemes",
                        "https://ruraldevelopment.gov.in/schemes-list"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-list a', '.schemes a', 'a[href*="rojgar"]'],
                    'language': 'en'
                },
                {
                    'name': 'Ministry of Labor and Employment',
                    'urls': [
                        "https://labour.gov.in/schemes",
                        "https://labour.gov.in/welfare-schemes"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-item a', 'a[href*="employment"]', 'a[href*="rojgar"]'],
                    'language': 'en'
                },
                {
                    'name': 'National Career Service',
                    'urls': [
                        "https://www.ncs.gov.in/",
                        "https://www.ncs.gov.in/pages/schemes.html"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-list a', '.welfare-scheme a'],
                    'use_selenium': False,
                    'language': 'en'
                },
                {
                    'name': 'Skill India',
                    'urls': [
                        "https://www.skillindia.gov.in/",
                        "https://www.skillindia.gov.in/schemes"
                    ],
                    'selectors': ['a[href*="scheme"]', '.program-item a', '.initiative a'],
                    'language': 'en'
                },
                {
                    'name': 'CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises)',
                    'urls': [
                        "https://www.cgtmse.in/",
                        "https://www.cgtmse.in/schemes"
                    ],
                    'selectors': ['a[href*="scheme"]', '.scheme-item a', '.product a'],
                    'language': 'en'
                }
            ]
            
            for portal in central_portals:
                try:
                    portal_schemes = self._scrape_central_portal(portal)
                    schemes.extend(portal_schemes)
                    logger.info(f"Scraped {len(portal_schemes)} schemes from {portal['name']}")
                except Exception as e:
                    logger.error(f"Error scraping {portal['name']}: {e}")
                    continue
            
            log_entry.status = "success"
            log_entry.schemes_found = len(schemes)
            log_entry.completed_at = datetime.now()
            log_entry.duration_seconds = int((log_entry.completed_at - log_entry.started_at).total_seconds())
            
        except Exception as e:
            logger.error(f"Error scraping india.gov.in: {e}")
            log_entry.status = "failed"
            log_entry.error_message = str(e)
            log_entry.completed_at = datetime.now()
        
        finally:
            log_entry.save()
        
        return schemes
    
    def _scrape_central_portal(self, portal: Dict) -> List[Dict]:
        """Scrape schemes from a specific central government portal"""
        schemes = []
        
        try:
            for url in portal['urls']:
                try:
                    # Use per-portal Selenium flag if present
                    use_selenium = bool(portal.get('use_selenium', False) or self.config.use_selenium)
                    response = self._make_request_with_retry(url, use_selenium=use_selenium)
                    if not response:
                        logger.warning(f"Failed to fetch {url}")
                        continue
                        
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Use portal-specific selectors
                    scheme_elements = []
                    for selector in portal.get('selectors', ['a[href*="scheme"]']):
                        elements = soup.select(selector)
                        if elements:
                            scheme_elements.extend(elements)
                            break  # Use first successful selector
                    
                    # Fallback to generic search if no specific selectors work
                    if not scheme_elements:
                        scheme_elements = soup.find_all(['a', 'div'], class_=re.compile(r'scheme|program|yojana|initiative|service', re.I))
                    
                    processed_count = 0
                    for element in scheme_elements[:self.config.max_schemes_per_source]:
                        try:
                            if element.name == 'a' and element.get('href'):
                                scheme_url = urljoin(url, element.get('href'))
                                
                                # Skip if already scraped
                                if scheme_url in self.scraped_urls:
                                    continue
                                
                                scheme_data = self._scrape_scheme_page(scheme_url)
                                if scheme_data:
                                    scheme_data.update({
                                        'source_portal': portal['name'],
                                        'language': portal.get('language', 'en'),
                                        'government_level': 'central'
                                    })
                                    schemes.append(scheme_data)
                                    self.scraped_urls.add(scheme_url)
                                    processed_count += 1
                                    
                            elif element.name in ['div', 'article', 'section']:
                                # Extract text content from div elements
                                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                                if title_elem:
                                    title = title_elem.get_text().strip()
                                    description = element.get_text().strip()[:800]
                                    
                                    if len(title) > 10 and len(description) > 50:
                                        scheme_data = {
                                            'title': title,
                                            'description': description,
                                            'short_description': description[:300] + '...' if len(description) > 300 else description,
                                            'source_url': url,
                                            'source_portal': portal['name'],
                                            'government_level': 'central',
                                            'ministry': 'Government of India',
                                            'department': 'Various Departments',
                                            'sector': self._categorize_scheme(title, description),
                                            'language': portal.get('language', 'en'),
                                            'is_active': True
                                        }
                                        schemes.append(scheme_data)
                                        processed_count += 1
                            
                            if processed_count >= self.config.max_schemes_per_source:
                                break
                                
                            self._random_delay()
                            
                        except Exception as e:
                            logger.error(f"Error processing scheme element: {e}")
                            continue
                    
                    logger.info(f"Successfully scraped {len(schemes)} schemes from {portal['name']} - {url}")
                    
                except Exception as e:
                    logger.error(f"Error scraping {url} from {portal['name']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping central portal {portal['name']}: {e}")
        
        return schemes
    
    def scrape_state_government_sites(self) -> List[Dict]:
        """Scrape schemes from state government websites"""
        schemes = []
        
        # List of state government portals with enhanced URLs
        state_portals = [
            {
                'name': 'Karnataka Government',
                'url': 'https://karnataka.gov.in/',
                'schemes_path': '/english/schemes',
                'language': 'kn',
                'selectors': ['a[href*="scheme"]', 'a[href*="yojane"]', '.scheme-item a']
            },
            {
                'name': 'Maharashtra Government',
                'url': 'https://www.maharashtra.gov.in/',
                'schemes_path': '/en/schemes',
                'language': 'mr',
                'selectors': ['a[href*="scheme"]', 'a[href*="yojana"]', '.scheme-list a']
            },
            {
                'name': 'Tamil Nadu Government',
                'url': 'https://www.tn.gov.in/',
                'schemes_path': '/schemes',
                'language': 'ta',
                'selectors': ['a[href*="scheme"]', 'a[href*="thittam"]', '.schemes a']
            },
            {
                'name': 'Uttar Pradesh Government',
                'url': 'https://up.gov.in/',
                'schemes_path': '/en/schemes',
                'language': 'hi',
                'selectors': ['a[href*="scheme"]', 'a[href*="yojna"]', '.scheme-section a']
            },
            {
                'name': 'West Bengal Government',
                'url': 'https://wb.gov.in/',
                'schemes_path': '/schemes',
                'language': 'bn',
                'selectors': ['a[href*="scheme"]', 'a[href*="projukti"]', '.scheme-list a']
            }
        ]
        
        for portal in state_portals:
            try:
                # honor per-portal selenium flag in state portals
                portal.setdefault('use_selenium', False)
                portal_schemes = self._scrape_state_portal(portal)
                schemes.extend(portal_schemes)
            except Exception as e:
                logger.error(f"Error scraping {portal['name']}: {e}")
                continue
        
        return schemes
    
    def _scrape_state_portal(self, portal: Dict) -> List[Dict]:
        """Enhanced scraping from state portal with better error handling"""
        schemes = []
        
        try:
            schemes_url = urljoin(portal['url'], portal['schemes_path'])
            response = self._make_request_with_retry(schemes_url)
            if not response:
                logger.warning(f"Failed to fetch {schemes_url}")
                return schemes
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use portal-specific selectors with fallback
            scheme_elements = []
            for selector in portal.get('selectors', ['a[href*="scheme"]']):
                elements = soup.select(selector)
                if elements:
                    scheme_elements.extend(elements)
                    break  # Use first successful selector
            
            # Fallback to generic search if no specific selectors work
            if not scheme_elements:
                scheme_elements = soup.find_all(['a', 'div'], class_=re.compile(r'scheme|program|yojana|thittam|projukti', re.I))
            
            processed_count = 0
            for element in scheme_elements[:self.config.max_schemes_per_source]:
                try:
                    if element.name == 'a' and element.get('href'):
                        scheme_url = urljoin(schemes_url, element.get('href'))
                        
                        # Skip if already scraped
                        if scheme_url in self.scraped_urls:
                            continue
                        
                        scheme_data = self._scrape_scheme_page(scheme_url)
                        if scheme_data:
                            scheme_data.update({
                                'state': portal['name'].replace(' Government', ''),
                                'language': portal.get('language', 'en'),
                                'government_level': 'state'
                            })
                            schemes.append(scheme_data)
                            self.scraped_urls.add(scheme_url)
                            processed_count += 1
                            
                    elif element.name in ['div', 'article', 'section']:
                        # Extract text content from div elements
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if title_elem:
                            title = title_elem.get_text().strip()
                            description = element.get_text().strip()[:800]
                            
                            if len(title) > 10 and len(description) > 50:
                                scheme_data = {
                                    'title': title,
                                    'description': description,
                                    'short_description': description[:300] + '...' if len(description) > 300 else description,
                                    'source_url': schemes_url,
                                    'state': portal['name'].replace(' Government', ''),
                                    'government_level': 'state',
                                    'ministry': 'State Government',
                                    'department': 'Various Departments',
                                    'sector': self._categorize_scheme(title, description),
                                    'language': portal.get('language', 'en'),
                                    'is_active': True
                                }
                                schemes.append(scheme_data)
                                processed_count += 1
                    
                    if processed_count >= self.config.max_schemes_per_source:
                        break
                        
                    self._random_delay()
                    
                except Exception as e:
                    logger.error(f"Error processing scheme element: {e}")
                    continue
                    
            logger.info(f"Successfully scraped {len(schemes)} schemes from {portal['name']}")
                    
        except Exception as e:
            logger.error(f"Error scraping state portal {portal['name']}: {e}")
        
        return schemes
    
    def _scrape_scheme_page(self, url: str) -> Optional[Dict]:
        """Enhanced scheme page scraping with fallback methods"""
        try:
            # Use requests only (skip Selenium to avoid WebDriver issues)
            response = self._make_request_with_retry(url)
            if not response:
                logger.error(f"Failed to fetch {url}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract scheme information with enhanced methods
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            if not title or len(title) < 5:
                logger.warning(f"No valid title found for {url}")
                return None
            
            if not description or len(description) < 20:
                logger.warning(f"No valid description found for {url}")
                description = f"Scheme information available at {url}. Please visit the official website for complete details."
            
            # Extract other details with enhanced methods
            scheme_data = {
                'title': self._clean_text(title),
                'description': self._clean_text(description),
                'short_description': self._clean_text(description[:300] + '...' if len(description) > 300 else description),
                'source_url': url,
                'government_level': 'central',
                'ministry': self._extract_ministry(soup),
                'department': self._extract_department(soup),
                'sector': self._categorize_scheme(title, description),
                'eligibility_criteria': self._extract_eligibility(soup),
                'benefits': self._extract_benefits(soup),
                'application_process': self._extract_application_process(soup),
                'launch_date': self._extract_launch_date(soup),
                'language': self._detect_language(soup),
                'keywords': self._extract_keywords(title, description),
                'search_tags': self._generate_search_tags(title, description),
                'is_active': True,
                'last_updated': datetime.now()
            }
            
            return scheme_data
            
        except Exception as e:
            logger.error(f"Error scraping scheme page {url}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text
    
    def _detect_language(self, soup: BeautifulSoup) -> str:
        """Detect language of the page"""
        # Check html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag.get('lang').lower()
            if lang.startswith('hi'): return 'hi'
            if lang.startswith('kn'): return 'kn'
            if lang.startswith('ta'): return 'ta'
            if lang.startswith('te'): return 'te'
            if lang.startswith('bn'): return 'bn'
            if lang.startswith('mr'): return 'mr'
            if lang.startswith('gu'): return 'gu'
            if lang.startswith('pa'): return 'pa'
        
        # Check content for language indicators
        page_text = soup.get_text().lower()[:1000]
        if any(word in page_text for word in ['योजना', 'सरकार', 'भारत']): return 'hi'
        if any(word in page_text for word in ['ಯೋಜನೆ', 'ಸರ್ಕಾರ', 'ಭಾರತ']): return 'kn'
        if any(word in page_text for word in ['திட்டம்', 'அரசு', 'இந்திய']): return 'ta'
        
        return 'en'
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Enhanced scheme title extraction"""
        # Try different selectors for title in order of preference
        title_selectors = [
            'h1',
            '.page-title',
            '.scheme-title',
            '.content-title',
            '.title',
            'h2',
            '.heading',
            'title'  # HTML title tag as fallback
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                # Filter out common non-scheme titles
                if (text and len(text) > 5 and 
                    not any(word in text.lower() for word in ['home', 'navigation', 'menu', 'header', 'footer'])):
                    return text
        
        # Try to find title from URL structure
        url_title = self._extract_title_from_url(soup)
        if url_title:
            return url_title
        
        return ""
    
    def _extract_title_from_url(self, soup: BeautifulSoup) -> str:
        """Extract title from URL if no HTML title found"""
        try:
            # Look for breadcrumbs or navigation that might contain title
            breadcrumb_selectors = [
                '.breadcrumb a',
                '.breadcrumbs a',
                '.nav-breadcrumb a',
                '.page-breadcrumb a'
            ]
            
            for selector in breadcrumb_selectors:
                elements = soup.select(selector)
                if elements:
                    # Return the last breadcrumb (usually the current page)
                    last_breadcrumb = elements[-1].get_text().strip()
                    if len(last_breadcrumb) > 3:
                        return last_breadcrumb
        except Exception:
            pass
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Enhanced scheme description extraction"""
        # Try different selectors for description
        desc_selectors = [
            '.scheme-description',
            '.content-description',
            '.description',
            '.summary',
            '.overview',
            '.about',
            '.scheme-details',
            'main p',
            '.main-content p',
            'article p'
        ]
        
        for selector in desc_selectors:
            elements = soup.select(selector)
            if elements:
                descriptions = []
                for elem in elements:
                    text = elem.get_text().strip()
                    # Filter out navigation and footer text
                    if (len(text) > 20 and 
                        not any(skip in text.lower() for skip in ['copyright', 'all rights', 'privacy', 'terms', 'contact'])):
                        descriptions.append(text)
                
                if descriptions:
                    # Join first few meaningful paragraphs
                    combined_desc = ' '.join(descriptions[:3])
                    if len(combined_desc) > 50:
                        return combined_desc
        
        # Fallback: extract text from main content area
        main_selectors = ['main', '.main-content', '.content', '#content']
        for selector in main_selectors:
            main_elem = soup.select_one(selector)
            if main_elem:
                text = main_elem.get_text().strip()
                if len(text) > 100:
                    # Return first 500 characters of main content
                    return text[:500]
        
        return ""
    
    def _extract_ministry(self, soup: BeautifulSoup) -> str:
        """Enhanced ministry extraction with better patterns"""
        ministry_patterns = [
            r'ministry\s+of\s+([^\n,\.]+)',
            r'department\s+of\s+([^\n,\.]+)',
            r'ministry[:\s]+([^\n,\.]+)',
            r'department[:\s]+([^\n,\.]+)',
            r'presented\s+by\s+([^\n,\.]+)',
            r'under\s+([^\n,\.]+)'
        ]
        
        page_text = soup.get_text()
        
        for pattern in ministry_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                ministry = match.group(1).strip()
                if len(ministry) > 3 and len(ministry) < 100:
                    return ministry.title()
        
        # Look for specific ministry indicators
        ministry_keywords = {
            'Ministry of Agriculture': ['agriculture', 'farming', 'kisan'],
            'Ministry of Health': ['health', 'medical', 'hospital', 'ayushman'],
            'Ministry of Education': ['education', 'school', 'college', 'scholarship'],
            'Ministry of Rural Development': ['rural', 'village', 'panchayat'],
            'Ministry of Women & Child Development': ['women', 'child', 'mahila'],
            'Ministry of Skill Development': ['skill', 'training', 'employment'],
            'Ministry of Finance': ['finance', 'financial', 'economic'],
            'Ministry of Social Justice': ['social', 'justice', 'empowerment']
        }
        
        text_lower = page_text.lower()
        for ministry, keywords in ministry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return ministry
        
        return "Government of India"
    
    def _extract_department(self, soup: BeautifulSoup) -> str:
        """Extract responsible department"""
        # Similar to ministry extraction
        dept_keywords = ['department', 'division', 'board', 'commission']
        
        for keyword in dept_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for element in elements:
                parent = element.parent
                if parent:
                    text = parent.get_text().strip()
                    if len(text) < 100:
                        return text
        
        return "Various Departments"
    
    def _categorize_scheme(self, title: str, description: str) -> str:
        """Enhanced scheme categorization with more sectors"""
        text = (title + ' ' + description).lower()
        
        sector_keywords = {
            'agriculture': ['agriculture', 'farmer', 'crop', 'irrigation', 'soil', 'farming', 'kisan', 'krishi'],
            'health': ['health', 'medical', 'hospital', 'doctor', 'medicine', 'treatment', 'ayushman', 'swasthya'],
            'education': ['education', 'school', 'college', 'student', 'scholarship', 'learning', 'skill', 'shiksha'],
            'employment': ['employment', 'job', 'work', 'skill', 'training', 'rojgar', 'naukri'],
            'social_welfare': ['welfare', 'pension', 'widow', 'disabled', 'senior', 'social', 'samajik'],
            'rural_development': ['rural', 'village', 'gram', 'panchayat', 'rural development', 'gaon'],
            'women_empowerment': ['women', 'girl', 'female', 'empowerment', 'beti', 'mahila', 'nari'],
            'youth_development': ['youth', 'young', 'student', 'yuva'],
            'housing': ['housing', 'house', 'home', 'shelter', 'awas', 'makaan'],
            'financial_inclusion': ['finance', 'bank', 'loan', 'credit', 'financial', 'arthik'],
            'infrastructure': ['road', 'bridge', 'transport', 'electricity', 'water', 'sadak'],
            'environment': ['environment', 'forest', 'wildlife', 'pollution', 'climate', 'paryavaran'],
            'technology': ['technology', 'digital', 'computer', 'internet', 'startup', 'tech'],
            'tourism': ['tourism', 'travel', 'hotel', 'heritage', 'culture', 'darshan'],
            'sports': ['sports', 'game', 'athlete', 'khel', 'khelkud'],
            'energy': ['energy', 'power', 'electricity', 'solar', 'renewable', 'vidyut']
        }
        
        # Score each sector based on keyword matches
        sector_scores = {}
        for sector, keywords in sector_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                sector_scores[sector] = score
        
        # Return sector with highest score
        if sector_scores:
            return max(sector_scores, key=sector_scores.get)
        
        return 'other'
    
    def _extract_eligibility(self, soup: BeautifulSoup) -> str:
        """Enhanced eligibility criteria extraction"""
        eligibility_keywords = [
            'eligibility', 'eligible', 'criteria', 'qualification', 'who can apply',
            'पात्रता', 'योग्यता', 'ಅರ್ಹತೆ', 'தகுதி', 'అర్హత'
        ]
        
        # Look for sections with eligibility information
        section_selectors = [
            '.eligibility',
            '.eligibility-criteria',
            '.who-can-apply',
            '.qualification',
            '#eligibility'
        ]
        
        for selector in section_selectors:
            section = soup.select_one(selector)
            if section:
                text = section.get_text().strip()
                if len(text) > 30 and len(text) < 2000:
                    return self._clean_text(text)
        
        # Search for eligibility keywords in text
        for keyword in eligibility_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for element in elements:
                parent = element.parent
                if parent:
                    # Get surrounding context
                    context = self._get_surrounding_text(parent, 200)
                    if len(context) > 50 and len(context) < 1000:
                        return self._clean_text(context)
        
        return "Please check official website for eligibility criteria"
    
    def _get_surrounding_text(self, element, max_chars: int = 200) -> str:
        """Get surrounding text from an element"""
        try:
            parent = element.parent
            if parent:
                text = parent.get_text().strip()
                if len(text) > max_chars:
                    # Try to get text around the keyword
                    element_text = element.get_text().strip()
                    start_pos = text.find(element_text)
                    if start_pos != -1:
                        start = max(0, start_pos - 50)
                        end = min(len(text), start_pos + len(element_text) + max_chars)
                        return text[start:end]
                return text
        except Exception:
            pass
        return ""
    
    def _extract_benefits(self, soup: BeautifulSoup) -> str:
        """Enhanced benefits extraction"""
        benefit_keywords = [
            'benefit', 'advantage', 'assistance', 'support', 'help', 'aid',
            'लाभ', 'सहायता', 'ಲಾಭ', 'நலன்கள்', 'ప్రయోజనాలు'
        ]
        
        # Look for benefit sections
        section_selectors = [
            '.benefits',
            '.advantages',
            '.scheme-benefits',
            '.assistance',
            '#benefits'
        ]
        
        for selector in section_selectors:
            section = soup.select_one(selector)
            if section:
                text = section.get_text().strip()
                if len(text) > 30 and len(text) < 2000:
                    return self._clean_text(text)
        
        # Search for benefit keywords
        for keyword in benefit_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for element in elements:
                parent = element.parent
                if parent:
                    context = self._get_surrounding_text(parent, 300)
                    if len(context) > 50 and len(context) < 1000:
                        return self._clean_text(context)
        
        return "Please check official website for benefits details"
    
    def _extract_application_process(self, soup: BeautifulSoup) -> str:
        """Enhanced application process extraction"""
        process_keywords = [
            'apply', 'application', 'process', 'procedure', 'how to apply',
            'आवेदन', 'आवेदन प्रक्रिया', 'ಅರ್ಜಿ', 'விண்ணப்பம்', 'దరఖాస్తు'
        ]
        
        # Look for application sections
        section_selectors = [
            '.application',
            '.application-process',
            '.how-to-apply',
            '.apply-now',
            '#application'
        ]
        
        for selector in section_selectors:
            section = soup.select_one(selector)
            if section:
                text = section.get_text().strip()
                if len(text) > 30 and len(text) < 2000:
                    return self._clean_text(text)
        
        # Search for application keywords
        for keyword in process_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for element in elements:
                parent = element.parent
                if parent:
                    context = self._get_surrounding_text(parent, 400)
                    if len(context) > 50 and len(context) < 1500:
                        return self._clean_text(context)
        
        return "Please visit official website for application process"
    
    def _extract_launch_date(self, soup: BeautifulSoup) -> date:
        """Enhanced launch date extraction"""
        # Look for date patterns in the text
        page_text = soup.get_text()
        
        # Enhanced date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',  # DD Month YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
            # Indian month names
            r'(\d{1,2})\s+(जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    date_str = match.group()
                    # Simple date parsing - can be enhanced with proper date parsing library
                    if re.search(r'\d{4}', date_str):
                        year = int(re.search(r'\d{4}', date_str).group())
                        if 2000 <= year <= date.today().year:  # Reasonable year range
                            return date(year, 1, 1)  # Default to January 1st of that year
                except Exception:
                    continue
        
        # Look for launch-related keywords with dates
        launch_patterns = [
            r'launched\s+on\s+(.+)',
            r'launched\s+in\s+(\d{4})',
            r'started\s+on\s+(.+)',
            r'शुरू\s+(.+)',
            r'आरंभ\s+(.+)'
        ]
        
        for pattern in launch_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    text = match.group(1)
                    year_match = re.search(r'\d{4}', text)
                    if year_match:
                        year = int(year_match.group())
                        if 2000 <= year <= date.today().year:
                            return date(year, 1, 1)
                except Exception:
                    continue
        
        return date.today()
    
    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """Enhanced keyword extraction with more comprehensive terms"""
        text = (title + ' ' + description).lower()
        
        keywords = []
        
        # Government scheme related keywords
        scheme_keywords = [
            'scheme', 'program', 'yojana', 'initiative', 'policy', 'plan',
            'योजना', 'कार्यक्रम', 'ಯೋಜನೆ', 'திட்டம்', 'పథకం',
            'project', 'mission', 'campaign', 'drive', 'abhiyaan', 'abhiyan'
        ]
        for keyword in scheme_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Enhanced sector keywords
        sector_keywords = [
            'agriculture', 'health', 'education', 'employment', 'welfare', 'development',
            'rural', 'urban', 'women', 'child', 'youth', 'senior', 'disabled',
            'housing', 'finance', 'infrastructure', 'environment', 'technology',
            'tourism', 'sports', 'energy', 'transport', 'water', 'sanitation'
        ]
        for keyword in sector_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Benefit-related keywords
        benefit_keywords = [
            'subsidy', 'grant', 'loan', 'scholarship', 'pension', 'allowance',
            'assistance', 'support', 'aid', 'benefit', 'compensation',
            'अनुदान', 'पेंशन', 'छात्रवृत्ति', 'सहायता'
        ]
        for keyword in benefit_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Target group keywords
        target_keywords = [
            'farmer', 'student', 'women', 'girl', 'senior citizen', 'disabled',
            'bpl', 'below poverty line', 'minority', 'sc', 'st', 'obc',
            'किसान', 'छात्र', 'महिला', 'वरिष्ठ नागरिक', 'गरीब', 'garib', 'kalyan'
        ]
        for keyword in target_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Employment specific keywords
        employment_keywords = [
            'rojgar', 'employment', 'job', 'work', 'skill', 'training', 'naukri',
            'रोजगार', 'नौकरी', 'काम', 'कौशल'
        ]
        for keyword in employment_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # Remove duplicates and limit
        keywords = list(set(keywords))[:10]
        return keywords
    
    def _generate_search_tags(self, title: str, description: str) -> List[str]:
        """Enhanced search tags generation for better searchability"""
        text = (title + ' ' + description).lower()
        
        tags = []
        
        # Sector-based tags
        sector_tags = {
            'agriculture': ['farmer', 'agriculture', 'crop', 'irrigation', 'kisan', 'krishi'],
            'health': ['health', 'medical', 'hospital', 'doctor', 'medicine', 'ayushman', 'swasthya'],
            'education': ['education', 'school', 'college', 'student', 'scholarship', 'shiksha'],
            'employment': ['job', 'employment', 'work', 'rojgar', 'naukri', 'skill'],
            'welfare': ['welfare', 'pension', 'social', 'samajik'],
            'rural': ['rural', 'village', 'gram', 'gaon', 'panchayat'],
            'women': ['women', 'girl', 'female', 'mahila', 'nari', 'beti'],
            'housing': ['housing', 'house', 'home', 'awas', 'makaan', 'shelter'],
            'finance': ['finance', 'bank', 'loan', 'credit', 'arthik'],
            'infrastructure': ['road', 'bridge', 'transport', 'sadak', 'electricity'],
            'environment': ['environment', 'forest', 'pollution', 'paryavaran'],
            'technology': ['technology', 'digital', 'computer', 'internet', 'startup'],
            'energy': ['energy', 'power', 'electricity', 'solar', 'vidyut']
        }
        
        for sector, keywords in sector_tags.items():
            if any(word in text for word in keywords):
                tags.append(sector)
        
        # Government level tags
        if any(word in text for word in ['central', 'national', 'union', 'bharat sarkar']):
            tags.append('central')
        if any(word in text for word in ['state', 'state government', 'rajya']):
            tags.append('state')
        
        # Target audience tags
        audience_tags = {
            'bpl': ['bpl', 'below poverty line', 'garib'],
            'minority': ['minority', 'muslim', 'sikh', 'christian', 'jain'],
            'sc_st': ['sc', 'st', 'scheduled caste', 'scheduled tribe'],
            'obc': ['obc', 'other backward classes'],
            'senior_citizen': ['senior citizen', 'elderly', 'old age', 'vridh'],
            'disabled': ['disabled', 'handicapped', 'divyang'],
            'student': ['student', 'scholarship', 'education'],
            'women': ['women', 'widow', 'female'],
            'farmer': ['farmer', 'agriculture', 'kisan']
        }
        
        for audience, keywords in audience_tags.items():
            if any(word in text for word in keywords):
                tags.append(audience)
        
        # Benefit type tags
        benefit_tags = {
            'financial': ['subsidy', 'grant', 'loan', 'financial', 'money'],
            'education': ['scholarship', 'education', 'training'],
            'health': ['medical', 'health', 'treatment'],
            'housing': ['housing', 'house', 'shelter'],
            'pension': ['pension', 'retirement', 'old age']
        }
        
        for benefit, keywords in benefit_tags.items():
            if any(word in text for word in keywords):
                tags.append(benefit)
        
        # Special initiative tags
        initiative_tags = {
            'digital_india': ['digital india', 'digital'],
            'make_in_india': ['make in india'],
            'swachh_bharat': ['swachh bharat', 'cleanliness'],
            'skill_india': ['skill india', 'skill development'],
            'startup_india': ['startup india', 'startup']
        }
        
        for initiative, keywords in initiative_tags.items():
            if any(word in text for word in keywords):
                tags.append(initiative)
        
        # Remove duplicates and return
        unique_tags = list(set(tags))
        return unique_tags[:20]  # Increased limit for better filtering
    
    def save_schemes_to_database(self, schemes: List[Dict]) -> Dict:
        """Enhanced database saving with better error handling and validation"""
        added_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for scheme_data in schemes:
            try:
                # Validate required fields
                if not scheme_data.get('title') or not scheme_data.get('description'):
                    logger.warning(f"Skipping scheme with missing title or description")
                    skipped_count += 1
                    continue
                
                # Clean and validate data
                scheme_data = self._validate_and_clean_scheme_data(scheme_data)
                if not scheme_data:
                    skipped_count += 1
                    continue
                
                # Check if scheme already exists (multiple criteria)
                existing_scheme = self._find_existing_scheme(scheme_data)
                
                if existing_scheme:
                    # Update existing scheme with new data
                    updated = self._update_existing_scheme(existing_scheme, scheme_data)
                    if updated:
                        updated_count += 1
                        logger.debug(f"Updated scheme: {scheme_data['title']}")
                else:
                    # Create new scheme
                    try:
                        GovernmentScheme.objects.create(**scheme_data)
                        added_count += 1
                        logger.debug(f"Added new scheme: {scheme_data['title']}")
                    except Exception as e:
                        logger.error(f"Error creating scheme {scheme_data.get('title', 'Unknown')}: {e}")
                        error_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing scheme {scheme_data.get('title', 'Unknown')}: {e}")
                error_count += 1
                continue
        
        result = {
            'added': added_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_processed': len(schemes)
        }
        
        logger.info(f"Database save completed: {result}")
        return result
    
    def _validate_and_clean_scheme_data(self, scheme_data: Dict) -> Optional[Dict]:
        """Validate and clean scheme data before saving"""
        try:
            # Required fields validation
            if not scheme_data.get('title') or len(scheme_data['title'].strip()) < 3:
                return None
            
            if not scheme_data.get('description') or len(scheme_data['description'].strip()) < 20:
                return None
            
            # Clean text fields
            for field in ['title', 'description', 'short_description', 'eligibility_criteria', 
                         'benefits', 'application_process', 'ministry', 'department']:
                if field in scheme_data and scheme_data[field]:
                    scheme_data[field] = self._clean_text(str(scheme_data[field]))
            
            # Ensure short description doesn't exceed limit
            if 'short_description' in scheme_data and len(scheme_data['short_description']) > 500:
                scheme_data['short_description'] = scheme_data['short_description'][:497] + '...'
            
            # Set default values for missing fields
            defaults = {
                'government_level': 'central',
                'sector': 'other',
                'language': 'en',
                'is_active': True,
                'ministry': 'Government of India',
                'department': 'Various Departments'
            }
            
            for field, default_value in defaults.items():
                if field not in scheme_data or not scheme_data[field]:
                    scheme_data[field] = default_value
            
            # Ensure lists are properly formatted
            for field in ['keywords', 'search_tags']:
                if field in scheme_data and scheme_data[field]:
                    if isinstance(scheme_data[field], str):
                        scheme_data[field] = [scheme_data[field]]
                    elif not isinstance(scheme_data[field], list):
                        scheme_data[field] = []
                else:
                    scheme_data[field] = []
            
            return scheme_data
            
        except Exception as e:
            logger.error(f"Error validating scheme data: {e}")
            return None
    
    def _find_existing_scheme(self, scheme_data: Dict) -> Optional[GovernmentScheme]:
        """Find existing scheme using multiple criteria"""
        try:
            # Try exact title match first
            existing = GovernmentScheme.objects.filter(
                title__iexact=scheme_data['title'].strip()
            ).first()
            
            if existing:
                return existing
            
            # Try title + source URL match
            if scheme_data.get('source_url'):
                existing = GovernmentScheme.objects.filter(
                    title__iexact=scheme_data['title'].strip(),
                    source_url=scheme_data['source_url']
                ).first()
                if existing:
                    return existing
            
            # Try similarity match (optional - can be enhanced with fuzzy matching)
            title_words = scheme_data['title'].lower().split()[:3]  # First 3 words
            if len(title_words) >= 2:
                for word in title_words:
                    if len(word) > 3:  # Skip very short words
                        similar = GovernmentScheme.objects.filter(
                            title__icontains=word
                        ).first()
                        if similar:
                            return similar
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding existing scheme: {e}")
            return None
    
    def _update_existing_scheme(self, existing_scheme: GovernmentScheme, new_data: Dict) -> bool:
        """Update existing scheme with new data"""
        try:
            # Only update fields that have meaningful changes
            updated = False
            
            for key, value in new_data.items():
                if hasattr(existing_scheme, key) and value:
                    current_value = getattr(existing_scheme, key)
                    if str(current_value).strip() != str(value).strip():
                        setattr(existing_scheme, key, value)
                        updated = True
            
            if updated:
                existing_scheme.last_updated = datetime.now()
                existing_scheme.save()
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating existing scheme: {e}")
            return False
    
    def run_full_scraping(self) -> Dict:
        """Enhanced full scraping process with better monitoring"""
        logger.info("Starting enhanced full scraping process")
        
        all_schemes = []
        scraping_stats = {
            'central_schemes': 0,
            'state_schemes': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Scrape central government schemes
        try:
            logger.info("Scraping central government schemes...")
            central_schemes = self.scrape_india_gov_in()
            all_schemes.extend(central_schemes)
            scraping_stats['central_schemes'] = len(central_schemes)
            logger.info(f"Successfully scraped {len(central_schemes)} central government schemes")
        except Exception as e:
            logger.error(f"Error scraping central schemes: {e}")
            scraping_stats['errors'] += 1
        
        # Scrape state government schemes
        try:
            logger.info("Scraping state government schemes...")
            state_schemes = self.scrape_state_government_sites()
            all_schemes.extend(state_schemes)
            scraping_stats['state_schemes'] = len(state_schemes)
            logger.info(f"Successfully scraped {len(state_schemes)} state government schemes")
        except Exception as e:
            logger.error(f"Error scraping state schemes: {e}")
            scraping_stats['errors'] += 1
        
        # Remove duplicates before saving
        unique_schemes = self._remove_duplicate_schemes(all_schemes)
        logger.info(f"Removed {len(all_schemes) - len(unique_schemes)} duplicate schemes")
        # Optionally save raw scraped records to Excel for review (backup / garbage filter)
        try:
            if self.config.save_to_file:
                try:
                    self.save_scraped_to_excel(unique_schemes)
                except Exception as e:
                    logger.warning(f"Failed to save scraped records to Excel: {e}")
        except Exception:
            pass

        # Save to database
        try:
            logger.info("Saving schemes to database...")
            save_result = self.save_schemes_to_database(unique_schemes)
            logger.info(f"Database save completed: {save_result}")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            save_result = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': len(unique_schemes), 'total_processed': len(unique_schemes)}
        
        # Calculate duration
        end_time = datetime.now()
        duration = int((end_time - scraping_stats['start_time']).total_seconds())
        
        # Final result
        final_result = {
            'total_scraped': len(all_schemes),
            'unique_schemes': len(unique_schemes),
            'duplicates_removed': len(all_schemes) - len(unique_schemes),
            'added_to_db': save_result.get('added', 0),
            'updated_in_db': save_result.get('updated', 0),
            'skipped': save_result.get('skipped', 0),
            'db_errors': save_result.get('errors', 0),
            'scraping_errors': scraping_stats['errors'],
            'duration_seconds': duration,
            'central_schemes': scraping_stats['central_schemes'],
            'state_schemes': scraping_stats['state_schemes'],
            'success_rate': round((len(unique_schemes) / len(all_schemes) * 100) if all_schemes else 0, 2)
        }
        
        logger.info(f"Enhanced scraping completed in {duration}s: {final_result}")
        return final_result
    
    def _remove_duplicate_schemes(self, schemes: List[Dict]) -> List[Dict]:
        """Remove duplicate schemes based on title similarity"""
        seen_titles = set()
        unique_schemes = []
        
        for scheme in schemes:
            title_normalized = scheme['title'].lower().strip()
            
            # Simple normalization - remove extra spaces and special chars
            title_normalized = re.sub(r'\s+', ' ', title_normalized)
            title_normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title_normalized)
            
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_schemes.append(scheme)
            else:
                logger.debug(f"Duplicate scheme found and removed: {scheme['title']}")
        
        return unique_schemes

    def save_scraped_to_excel(self, schemes: List[Dict], dest_dir: str = 'data/scraped') -> str:
        """Save scraped scheme dictionaries to an Excel file for offline review.

        Returns the path to the saved file.
        """
        try:
            Path(dest_dir).mkdir(parents=True, exist_ok=True)

            rows = []
            for s in schemes:
                rows.append({
                    'title': s.get('title'),
                    'short_description': s.get('short_description') or '',
                    'description': s.get('description') or '',
                    'source_url': s.get('source_url') or s.get('source_portal_url') or '',
                    'source_portal': s.get('source_portal') or s.get('source_name') or '',
                    'language': s.get('language') or '',
                    'sector': s.get('sector') or '',
                    'ministry': s.get('ministry') or '',
                    'department': s.get('department') or '',
                    'government_level': s.get('government_level') or '',
                    'is_active': s.get('is_active', True),
                })

            df = pd.DataFrame(rows)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = Path(dest_dir) / f'scraped_{timestamp}.xlsx'
            df.to_excel(file_path, index=False)
            logger.info(f"Saved {len(rows)} scraped records to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving scraped records to Excel: {e}")
            raise
    
    def run_incremental_scraping(self) -> Dict:
        """Run incremental scraping for new schemes only"""
        logger.info("Starting incremental scraping process")
        
        try:
            # Get last scraping date from logs
            last_scraping = WebScrapingLog.objects.filter(
                status='success'
            ).order_by('-completed_at').first()
            
            if last_scraping:
                days_since_last = (datetime.now().date() - last_scraping.completed_at.date()).days
                if days_since_last < 7:  # Don't scrape if last run was less than 7 days ago
                    logger.info(f"Skipping incremental scraping - last run was {days_since_last} days ago")
                    return {'skipped': True, 'reason': 'Recent scraping found', 'days_since_last': days_since_last}
            
            # Run full scraping with reduced scope
            original_config = self.config
            self.config.max_schemes_per_source = 20  # Reduced for incremental
            
            result = self.run_full_scraping()
            result['scraping_type'] = 'incremental'
            
            # Restore original config
            self.config = original_config
            
            return result
            
        except Exception as e:
            logger.error(f"Error in incremental scraping: {e}")
            return {'error': str(e), 'scraping_type': 'incremental'}
    
    def test_scraping_sources(self) -> Dict:
        """Test connectivity to all scraping sources"""
        logger.info("Testing scraping sources connectivity")
        
        test_results = {
            'india_gov_in': False,
            'state_portals': {},
            'overall_status': 'failed'
        }
        
        # Test central government portal
        try:
            response = self._make_request_with_retry("https://www.india.gov.in/")
            if response and response.status_code == 200:
                test_results['india_gov_in'] = True
                logger.info("India.gov.in connectivity: OK")
        except Exception as e:
            logger.error(f"India.gov.in connectivity failed: {e}")
        
        # Test state portals
        state_portals = [
            {'name': 'Karnataka', 'url': 'https://karnataka.gov.in/'},
            {'name': 'Maharashtra', 'url': 'https://www.maharashtra.gov.in/'},
            {'name': 'Tamil Nadu', 'url': 'https://www.tn.gov.in/'},
            {'name': 'Uttar Pradesh', 'url': 'https://up.gov.in/'},
            {'name': 'West Bengal', 'url': 'https://wb.gov.in/'}
        ]
        
        for portal in state_portals:
            try:
                response = self._make_request_with_retry(portal['url'])
                if response and response.status_code == 200:
                    test_results['state_portals'][portal['name']] = True
                    logger.info(f"{portal['name']} portal connectivity: OK")
                else:
                    test_results['state_portals'][portal['name']] = False
            except Exception as e:
                test_results['state_portals'][portal['name']] = False
                logger.error(f"{portal['name']} portal connectivity failed: {e}")
        
        # Determine overall status
        central_ok = test_results['india_gov_in']
        state_ok_count = sum(1 for status in test_results['state_portals'].values() if status)
        
        if central_ok and state_ok_count >= 3:
            test_results['overall_status'] = 'good'
        elif central_ok or state_ok_count >= 2:
            test_results['overall_status'] = 'partial'
        
        logger.info(f"Connectivity test completed: {test_results['overall_status']}")
        return test_results


# Global scraper instance - enable Selenium if env var SCRAPER_USE_SELENIUM is set
import os as _os
use_selenium_glob = str(_os.getenv('SCRAPER_USE_SELENIUM', 'false')).lower() in ('1', 'true', 'yes')
scraper = GovernmentPortalScraper(config=ScrapingConfig(use_selenium=use_selenium_glob))
