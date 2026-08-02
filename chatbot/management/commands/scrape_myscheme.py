"""
Django management command to scrape MyScheme.gov.in using Selenium
Stores data in ScrapedScheme table (separate from GovernmentScheme)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from django.core.management.base import BaseCommand
from chatbot.models import ScrapedScheme


class Command(BaseCommand):
    help = "Scrapes only scheme titles from MyScheme.gov.in using visible Chromium"

    def handle(self, *args, **kwargs):

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")  # Visible mode

        driver = webdriver.Chrome(options=options)

        try:
            self.stdout.write("🌐 Loading MyScheme.gov.in...")
            driver.get("https://www.myscheme.gov.in")
            
            # Wait for page to load
            time.sleep(5)
            
            # Try to close sign-in modal/popup if it appears
            self.stdout.write("🔍 Checking for sign-in modal...")
            try:
                # Try different ways to close the modal
                close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close'], button.close, .modal-close, [class*='close']")
                for btn in close_buttons:
                    try:
                        btn.click()
                        self.stdout.write("   ✅ Closed sign-in modal")
                        time.sleep(2)
                        break
                    except:
                        pass
                
                # Press ESC key to close any modal
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
                
            except:
                self.stdout.write("   No modal found or already closed")
            
            self.stdout.write("📜 Scrolling page to load all schemes...")
            # scroll multiple times to load all cards
            for i in range(25):  # Increased to 25 scrolls to load more schemes
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                if i % 5 == 0:
                    self.stdout.write(f"   Scroll {i+1}/25...")

            self.stdout.write("🔍 Searching for scheme cards...")
            
            # Try multiple selectors to find scheme cards
            selectors_to_try = [
                ("div[class*='SchemeCard'] a", "SchemeCard links"),
                ("div[class*='Card'] a", "Card links"),
                ("a[href*='/schemes/']", "Scheme detail links"),
                ("a[href*='/scheme/']", "Scheme links"),
                (".MuiCard-root a", "MUI Card links"),
                ("h3 a", "Heading links"),
                ("article a", "Article links"),
            ]
            
            cards = []
            used_selector = None
            
            for selector, description in selectors_to_try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(cards) > 5:  # Found meaningful results
                    used_selector = description
                    self.stdout.write(f"   ✅ Found {len(cards)} links using: {description}")
                    break
            
            if not cards or len(cards) < 5:
                # Fallback: get all links and filter by href pattern
                self.stdout.write("   ⚠️  Using fallback: getting all links...")
                all_links = driver.find_elements(By.CSS_SELECTOR, "a")
                cards = [link for link in all_links if ('/schemes/' in (link.get_attribute("href") or '') or '/scheme/' in (link.get_attribute("href") or ''))]
                self.stdout.write(f"   Found {len(cards)} scheme-related links")

            titles_added = 0
            duplicates = 0

            self.stdout.write(f"\n📥 Processing {len(cards)} scheme links...")
            
            for card in cards:
                try:
                    title = card.text.strip()
                    url = card.get_attribute("href")

                    # Skip navigation/empty links
                    if not title or not url or len(title) < 5:
                        continue
                    
                    # Skip common navigation items
                    skip_keywords = ['home', 'about', 'login', 'search', 'filter', 'back to']
                    if any(keyword in title.lower() for keyword in skip_keywords):
                        continue

                    # Try to create/get scheme
                    obj, created = ScrapedScheme.objects.get_or_create(
                        title=title,
                        url=url
                    )
                    
                    if created:
                        titles_added += 1
                        if titles_added <= 10:  # Show first 10
                            self.stdout.write(f"   ✅ {title[:60]}...")
                    else:
                        duplicates += 1
                        
                except Exception as e:
                    continue

            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS(
                f"✅ Scraping Complete!"
            ))
            self.stdout.write(f"   Added: {titles_added}")
            self.stdout.write(f"   Duplicates skipped: {duplicates}")
            self.stdout.write(f"   Total processed: {titles_added + duplicates}")
            self.stdout.write("="*60)
            
        finally:
            driver.quit()
            self.stdout.write("\n🔒 Browser closed.")
