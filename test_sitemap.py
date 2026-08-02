"""
Quick test to check MyScheme.gov.in sitemap structure
"""
import requests
from bs4 import BeautifulSoup

# Test sitemap
sitemap_url = 'https://www.myscheme.gov.in/sitemap.xml'

print(f"Fetching: {sitemap_url}\n")

try:
    response = requests.get(sitemap_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"\nFirst 1000 characters:")
    print("="*60)
    print(response.text[:1000])
    print("="*60)
    
    # Try parsing as XML
    soup = BeautifulSoup(response.content, 'xml')
    locs = soup.find_all('loc')
    
    print(f"\n\nFound {len(locs)} <loc> tags")
    print("\nFirst 10 URLs:")
    for i, loc in enumerate(locs[:10], 1):
        url = loc.text.strip()
        has_schemes = '/schemes/' in url or '/scheme/' in url
        print(f"{i}. {url} {'✓ SCHEME' if has_schemes else ''}")
    
    # Count scheme URLs
    scheme_urls = [loc.text.strip() for loc in locs if '/scheme' in loc.text.lower()]
    print(f"\n\n📊 Total scheme URLs found: {len(scheme_urls)}")
    
except Exception as e:
    print(f"Error: {e}")
