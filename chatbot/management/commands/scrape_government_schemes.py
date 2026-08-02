"""
Django management command to scrape central government schemes from services.india.gov.in
Saves to PostgreSQL using Django ORM with data_source='scraped'
"""

from django.core.management.base import BaseCommand
from chatbot.models import GovernmentScheme, Sector
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape central government schemes from services.india.gov.in and save to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=40,
            help='Maximum number of schemes to scrape (default: 40)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed scraping progress'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🔍 Fetching schemes from services.india.gov.in ...'))
        
        # Base URL for central government schemes
        base_url = 'https://services.india.gov.in'
        listing_url = f'{base_url}/services/central-government'
        
        added_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            # Fetch the listing page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(listing_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find scheme links - try multiple selectors
            scheme_links = []
            
            # Try common patterns for scheme listings
            selectors = [
                'div.views-row a',
                'div.service-list a',
                'div.view-content a',
                'article a',
                'h2 a',
                'h3 a',
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    scheme_links = links
                    if verbose:
                        self.stdout.write(f'Found {len(links)} links using selector: {selector}')
                    break
            
            if not scheme_links:
                self.stdout.write(self.style.WARNING('⚠️  No scheme links found. Website structure may have changed.'))
                return
            
            # Filter to get unique scheme URLs
            unique_schemes = []
            seen_urls = set()
            
            for link in scheme_links[:limit]:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not href or not title:
                    continue
                
                # Build full URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = base_url + href
                else:
                    full_url = base_url + '/' + href
                
                # Skip duplicates
                if full_url in seen_urls:
                    continue
                
                seen_urls.add(full_url)
                unique_schemes.append({
                    'title': title,
                    'url': full_url
                })
                
                if len(unique_schemes) >= limit:
                    break
            
            self.stdout.write(f'📋 Found {len(unique_schemes)} unique schemes to process')
            
            # Get or create "Other" sector for scraped schemes
            other_sector, _ = Sector.objects.get_or_create(
                name='Other',
                defaults={'description': 'Miscellaneous schemes'}
            )
            
            # Process each scheme
            for idx, scheme_data in enumerate(unique_schemes, 1):
                try:
                    title = scheme_data['title']
                    detail_url = scheme_data['url']
                    
                    if verbose:
                        self.stdout.write(f'\n[{idx}/{len(unique_schemes)}] Processing: {title[:60]}...')
                    
                    # Fetch detail page
                    detail_response = requests.get(detail_url, headers=headers, timeout=10)
                    detail_response.raise_for_status()
                    
                    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                    
                    # Extract description - try multiple selectors
                    description = None
                    description_selectors = [
                        'div.field-name-body',
                        'div.field-type-text-with-summary',
                        'div.content',
                        'article',
                        'div.description',
                        'div.service-description',
                    ]
                    
                    for selector in description_selectors:
                        desc_elem = detail_soup.select_one(selector)
                        if desc_elem:
                            # Get text, clean it up
                            description = desc_elem.get_text(separator=' ', strip=True)
                            # Remove excess whitespace
                            description = ' '.join(description.split())
                            if len(description) > 100:  # Valid description
                                break
                    
                    if not description or len(description) < 50:
                        description = "Description not available."
                    
                    # Limit description length
                    if len(description) > 5000:
                        description = description[:5000] + '...'
                    
                    # Create short description
                    short_desc = description[:250] if len(description) > 250 else description
                    
                    # Save to database using update_or_create
                    # Only updates if title matches AND data_source='scraped'
                    scheme, created = GovernmentScheme.objects.update_or_create(
                        title=title,
                        data_source='scraped',  # Key: only touch scraped entries
                        defaults={
                            'description': description,
                            'short_description': short_desc,
                            'source_url': detail_url,
                            'government_level': 'central',
                            'sector': other_sector,
                            'ministry': 'Central Government',
                            'department': 'To be updated',
                            'eligibility_criteria': 'Please visit official website for details',
                            'benefits': 'Please visit official website for details',
                            'application_process': 'Please visit official website for details',
                            'language': 'en',
                            'is_active': True,
                            'launch_date': datetime.now().date(),
                            'last_updated': datetime.now(),
                        }
                    )
                    
                    if created:
                        added_count += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Added: {title[:60]}...'))
                    else:
                        updated_count += 1
                        if verbose:
                            self.stdout.write(self.style.WARNING(f'  🔄 Updated: {title[:60]}...'))
                    
                    # Be nice to the server - small delay
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_count += 1
                    if verbose:
                        self.stdout.write(self.style.ERROR(f'  ❌ Error processing {title}: {str(e)}'))
                    logger.error(f'Error scraping scheme {title}: {e}')
                    continue
            
            # Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS(f'✅ Scraping Complete!'))
            self.stdout.write(f'   Added: {added_count}')
            self.stdout.write(f'   Updated: {updated_count}')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'   Errors: {error_count}'))
            self.stdout.write('='*60)
            
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Network error: {str(e)}'))
            logger.error(f'Network error during scraping: {e}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {str(e)}'))
            logger.error(f'Unexpected error during scraping: {e}')
