"""
Debug script to see what MyScheme.gov.in homepage looks like
Takes a screenshot to see what's being rendered
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument("--start-maximized")

print("🔍 Opening Chrome...")
driver = webdriver.Chrome(options=options)

print("🌐 Loading MyScheme.gov.in...")
driver.get("https://www.myscheme.gov.in")
time.sleep(8)  # Wait for page load

print("📸 Taking screenshot...")
driver.save_screenshot("myscheme_homepage.png")
print("   Saved to: myscheme_homepage.png")

print("\n📊 Page Title:", driver.title)
print("📊 Current URL:", driver.current_url)

print("\n🔍 Finding all links...")
all_links = driver.find_elements(By.CSS_SELECTOR, "a")
print(f"   Total links found: {len(all_links)}")

print("\n📋 Sample links (first 20):")
for i, link in enumerate(all_links[:20], 1):
    try:
        text = link.text.strip()
        href = link.get_attribute("href")
        if text or href:
            print(f"   {i}. {text[:50] if text else '(no text)'} → {href}")
    except:
        pass

print("\n🔍 Looking for buttons...")
buttons = driver.find_elements(By.CSS_SELECTOR, "button")
print(f"   Total buttons found: {len(buttons)}")

print("\n📋 Sample buttons (first 10):")
for i, btn in enumerate(buttons[:10], 1):
    try:
        text = btn.text.strip()
        if text:
            print(f"   {i}. {text}")
    except:
        pass

print("\n✅ Test complete!")
print("💡 Check myscheme_homepage.png to see what the page looks like")

input("\nPress ENTER to close browser...")
driver.quit()
