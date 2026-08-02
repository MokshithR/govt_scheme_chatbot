"""
Direct test of the scraper
"""
from chatbot.scraper.myscheme_scraper import MySchemeScaper

scraper = MySchemeScaper()
print("Testing scraper...")

schemes = scraper.get_scheme_urls_from_sitemap()
print(f"\n✅ Found {len(schemes)} schemes")

if schemes:
    print("\nFirst 10 schemes:")
    for i, s in enumerate(schemes[:10], 1):
        print(f"{i}. {s['title'][:70]}")
        print(f"   URL: {s['url']}\n")
else:
    print("❌ No schemes found!")
