"""
Quick test for scheme translation API
"""
import requests
import json

# Test the batch translation endpoint
url = "http://127.0.0.1:8000/api/translate/schemes/"

# Sample request - translate first 3 schemes to Kannada
data = {
    "scheme_ids": [1, 2, 3],
    "target_language": "kn"
}

print("🧪 Testing Scheme Translation API")
print("=" * 60)
print(f"URL: {url}")
print(f"Request: {json.dumps(data, indent=2)}")
print("=" * 60)

try:
    response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('status')}")
        print(f"📝 Translated Schemes: {len(result.get('translated_schemes', []))}")
        
        # Show first translated scheme
        if result.get('translated_schemes'):
            first_scheme = result['translated_schemes'][0]
            print("\n🎯 First Translated Scheme:")
            print(f"   ID: {first_scheme.get('id')}")
            print(f"   Title: {first_scheme.get('title')}")
            print(f"   Description: {first_scheme.get('description', '')[:100]}...")
            print(f"   Level: {first_scheme.get('government_level')}")
            print(f"   State: {first_scheme.get('state')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
print("✅ Test complete - refresh your browser and try clicking Kannada button")
