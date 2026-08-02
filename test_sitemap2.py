"""
Check the actual sitemap file from the index
"""
import requests
from bs4 import BeautifulSoup

# The real sitemap
sitemap_url = 'https://www.myscheme.gov.in/sitemap-0.xml'

print(f"Fetching: {sitemap_url}\n")

try:
    response = requests.get(sitemap_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    # Parse as XML
    soup = BeautifulSoup(response.content, 'xml')
    locs = soup.find_all('loc')
    
    print(f"\nFound {len(locs)} <loc> tags")
    print("\nFirst 20 URLs:")
    for i, loc in enumerate(locs[:20], 1):
        url = loc.text.strip()
        has_schemes = '/schemes/' in url or '/scheme/' in url
        print(f"{i}. {url} {'✓ SCHEME' if has_schemes else ''}")
    
    # Count scheme URLs
    scheme_urls = [loc.text.strip() for loc in locs if '/scheme' in loc.text.lower()]
    print(f"\n\n📊 Total scheme URLs found: {len(scheme_urls)}")
    
    if scheme_urls:
        print("\nSample scheme URLs:")
        for url in scheme_urls[:5]:
            print(f"  - {url}")
    
except Exception as e:
    print(f"Error: {e}")
