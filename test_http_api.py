"""
Quick HTTP API test for markdown cleanup
Run Django server first: python manage.py runserver
Then run this script: python test_http_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

test_queries = [
    ("What are the agricultural schemes?", "en"),
    ("PM Kisan Samman Nidhi", "en"),
    ("Kisan Credit Card", "en"),
    ("कृषि योजनाएं", "hi"),  # Hindi: Agricultural schemes
]

print("=" * 70)
print("HTTP API MARKDOWN CLEANUP TEST")
print("=" * 70)
print("\nTesting endpoint: /api/text-chat/")
print("Make sure Django server is running: python manage.py runserver\n")

for i, (query, language) in enumerate(test_queries, 1):
    print(f"\n{'=' * 70}")
    print(f"TEST {i}: {query} (language: {language})")
    print('=' * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/text-chat/",
            headers={"Content-Type": "application/json"},
            json={"query": query, "language": language},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract response text
            response_text = ""
            if isinstance(data.get('response'), dict):
                response_text = data['response'].get('text', '')
            elif isinstance(data.get('response'), str):
                response_text = data['response']
            
            print(f"\n✓ Status: {response.status_code} OK")
            print(f"Response length: {len(response_text)} chars")
            print(f"\nResponse preview:")
            print("-" * 70)
            print(response_text[:500] + ("..." if len(response_text) > 500 else ""))
            print("-" * 70)
            
            # Verification checks
            print("\n✓ Markdown verification:")
            checks = [
                ('#' not in response_text, "No # symbols"),
                ('**' not in response_text, "No ** symbols"),
                ('*' not in response_text or response_text.count('*') < 3, "No * symbols (or minimal)"),
                ('|' not in response_text, "No | pipe symbols"),
                (not any(line.strip().startswith(('- ', '* ', '• ')) for line in response_text.split('\n')), "No bullet points"),
            ]
            
            for passed, check_name in checks:
                symbol = '✓' if passed else '✗'
                print(f"  {symbol} {check_name}")
            
            if all(check[0] for check in checks):
                print("\n✅ ALL CHECKS PASSED - Response is clean!")
            else:
                print("\n⚠️  Some markdown symbols detected")
                
        else:
            print(f"\n✗ HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed!")
        print("Make sure Django server is running:")
        print("  python manage.py runserver")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
print("VOICE TESTING NEXT")
print("=" * 70)
print("\nTo test voice output:")
print("1. Use your frontend voice interface")
print("2. Speak queries: 'agricultural schemes', 'PM Kisan', 'Kisan Credit Card'")
print("3. Listen to audio output")
print("4. Verify TTS does NOT say 'asterisk', 'hash', 'dash', 'pipe'")
print("\nExpected: Natural speech like 'PM Kisan provides financial assistance'")
print("NOT: 'asterisk asterisk PM Kisan asterisk asterisk provides...'")
