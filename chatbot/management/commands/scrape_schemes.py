"""
Management command to scrape schemes from india.gov.in
Usage: python manage.py scrape_schemes
"""

from django.core.management.base import BaseCommand
from chatbot.models import ScrapedScheme
from chatbot.scrapers.india_gov_scraper import scrape_india_gov_titles


class Command(BaseCommand):
    help = 'Scrape scheme titles and URLs from india.gov.in/my-government/schemes'

    def handle(self, *args, **options):
        """
        Main command logic:
        1. Call scraper function
        2. Loop over scraped items
        3. Save only new titles (avoid duplicates)
        4. Print summary
        """
        
        self.stdout.write(self.style.WARNING('🔍 Starting scheme scraping from india.gov.in...'))
        self.stdout.write('')
        
        # Step 1: Call the scraper
        scraped_schemes = scrape_india_gov_titles()
        
        if not scraped_schemes:
            self.stdout.write(self.style.ERROR('❌ No schemes found or scraping failed.'))
            return
        
        # Step 2: Track statistics
        added_count = 0
        skipped_count = 0
        total_count = len(scraped_schemes)
        
        # Step 3: Save each scheme (skip duplicates)
        for scheme_data in scraped_schemes:
            title = scheme_data['title']
            url = scheme_data['url']
            
            # Check if this URL already exists (avoid duplicates)
            existing_scheme = ScrapedScheme.objects.filter(url=url).first()
            
            if existing_scheme:
                self.stdout.write(f"  ⏭️  Skipped (duplicate): {title[:60]}...")
                skipped_count += 1
            else:
                # Create new scheme entry
                ScrapedScheme.objects.create(
                    title=title,
                    url=url,
                    source='india.gov.in'
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ Added: {title[:60]}..."))
                added_count += 1
        
        # Step 4: Print summary
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Scraping completed!'))
        self.stdout.write(f'   Added: {added_count}')
        self.stdout.write(f'   Skipped (duplicates): {skipped_count}')
        self.stdout.write(f'   Total: {total_count}')
        self.stdout.write('=' * 60)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('💡 View scraped schemes in Django Admin:'))
        self.stdout.write('   /admin/chatbot/scrapedscheme/')
