"""
India.gov.in Schemes Scraper
Scrapes only scheme titles and URLs from https://www.india.gov.in/my-government/schemes
Uses requests + BeautifulSoup (no Selenium, no dynamic loading)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


def scrape_india_gov_titles():
    """
    Scrapes only scheme titles and links from india.gov.in/my-government/schemes
    
    Returns:
        list of dicts: [{'title': '...', 'url': '...'}, ...]
    
    Example:
        schemes = scrape_india_gov_titles()
        for scheme in schemes:
            print(scheme['title'], scheme['url'])
    """
    
    target_url = 'https://www.india.gov.in/my-government/schemes'
    schemes = []
    
    try:
        logger.info(f"Fetching schemes from: {target_url}")
        
        # Step 1: Fetch the page with proper headers and SSL verification
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(target_url, headers=headers, timeout=60, verify=True)
        response.raise_for_status()  # Raise error for bad status codes
        
        logger.info(f"Page fetched successfully (Status: {response.status_code}, Size: {len(response.content)} bytes)")
        
        # Step 2: Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Step 3: Try multiple CSS selectors to find scheme links
        selectors = [
            'div.view-content h3 a',  # Original selector
            'div.view-content a',      # Broader selector
            'div.views-row a',         # Alternative structure
            'article a',               # Generic article links
            'h3 a',                    # Any h3 link
        ]
        
        scheme_links = []
        for selector in selectors:
            scheme_links = soup.select(selector)
            if scheme_links:
                logger.info(f"Found {len(scheme_links)} links using selector: {selector}")
                break
        
        if not scheme_links:
            logger.warning("No scheme links found with any selector. Page might have different structure.")
            logger.debug(f"Page HTML preview: {str(soup)[:500]}")
            return []
        
        logger.info(f"Found {len(scheme_links)} scheme links total")
        
        # Step 4: Extract title and URL from each link
        for link in scheme_links:
            # Get title text (strip whitespace)
            title = link.get_text(strip=True)
            
            # Get href attribute and convert to absolute URL
            relative_url = link.get('href', '')
            absolute_url = urljoin(target_url, relative_url)
            
            # Only add if we have both title and URL, and filter out navigation/footer links
            if title and absolute_url and len(title) > 5:
                # Skip common navigation items
                skip_keywords = ['home', 'login', 'contact', 'about', 'privacy', 'terms']
                if not any(keyword in title.lower() for keyword in skip_keywords):
                    schemes.append({
                        'title': title,
                        'url': absolute_url
                    })
                    logger.debug(f"Found: {title}")
        
        logger.info(f"Successfully scraped {len(schemes)} schemes")
        return schemes
        
    except requests.Timeout:
        logger.error(f"Timeout while connecting to {target_url}. The website might be slow or unreachable.")
        return []
    
    except requests.RequestException as e:
        logger.error(f"Network error while scraping: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return []


def get_scheme_count():
    """
    Quick function to check how many schemes are available
    without saving to database
    
    Returns:
        int: Number of schemes found
    """
    schemes = scrape_india_gov_titles()
    return len(schemes)
