"""
Debug script to test MyScheme.gov.in scraper
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")  # Visible mode

print("🔍 Opening Chrome...")
driver = webdriver.Chrome(options=options)

print("🌐 Loading MyScheme.gov.in/schemes...")
driver.get("https://www.myscheme.gov.in/schemes")
time.sleep(4)  # Page load

print("📜 Scrolling page...")
# scroll multiple times to load all cards
for i in range(10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    print(f"   Scroll {i+1}/10 complete")

print("\n🔍 Looking for scheme cards...")

# Try different selectors
selectors = [
    ".MuiCard-root a",
    "a[href*='/schemes/']",
    "div[class*='Card'] a",
    "article a",
    "a",
]

for selector in selectors:
    cards = driver.find_elements(By.CSS_SELECTOR, selector)
    print(f"\n   Selector: {selector}")
    print(f"   Found: {len(cards)} elements")
    
    if len(cards) > 0:
        print(f"   Sample titles:")
        for card in cards[:5]:
            try:
                title = card.text.strip()
                url = card.get_attribute("href")
                if title and url:
                    print(f"      - {title[:50]}... → {url[:60]}...")
            except:
                continue

print("\n\n✅ Test complete. Check the output above.")
print("💡 If you see scheme titles, the scraper is working!")
print("💡 If not, the page structure may have changed.")

input("\nPress ENTER to close browser...")
driver.quit()
