# Quick Start: Testing Multilingual Chatbot

## Prerequisites

✅ `langdetect` installed (`pip install langdetect`)  
✅ Django server running  
✅ Database with schemes loaded  

## Test 1: Language Detection (Unit Test)

```bash
python test_multilingual_system.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED! Multilingual system is working correctly.
```

## Test 2: API Testing with cURL

### English Query

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"pm kisan scheme\"}"
```

**Expected Response:**
```json
{
  "language": "en",
  "response": "Sure! Here's the information about PM-Kisan Scheme.",
  "schemes": ["Scheme Name: PM-Kisan Scheme\n..."],
  "match_type": "exact_match"
}
```

### Kannada Query

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"ಕೃಷಿ ಯೋಜನೆಗಳು\"}"
```

**Expected Response:**
```json
{
  "language": "kn",
  "response": "Agriculture ವಿಭಾಗದಿಂದ 5 ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ.",
  "schemes": ["Scheme Name: ...\n..."],
  "match_type": "sector_match"
}
```

### Hindi Query

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"कृषि योजनाएं\"}"
```

**Expected Response:**
```json
{
  "language": "hi",
  "response": "Agriculture क्षेत्र से 5 योजनाएँ मिलीं।",
  "schemes": ["Scheme Name: ...\n..."],
  "match_type": "sector_match"
}
```

## Test 3: Empty Query (Greeting Test)

### English

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"hello\"}"
```

**Expected:**
```json
{
  "language": "en",
  "response": "Hello! I'm your Government Schemes Assistant...",
  "match_type": "greeting"
}
```

### Kannada

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"ನಮಸ್ಕಾರ\"}"
```

**Expected:**
```json
{
  "language": "kn",
  "response": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಯೋಜನೆ ಸಹಾಯಕ...",
  "match_type": "greeting"
}
```

### Hindi

```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"नमस्ते\"}"
```

**Expected:**
```json
{
  "language": "hi",
  "response": "नमस्ते! मैं आपका सरकारी योजना सहायक हूँ...",
  "match_type": "greeting"
}
```

## Test 4: Python API Testing

Create `test_api_multilingual.py`:

```python
import requests
import json

API_URL = "http://localhost:8000/api/chatbot/smart-query/"

def test_query(query, expected_language):
    response = requests.post(
        API_URL,
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    data = response.json()
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Expected Language: {expected_language}")
    print(f"Detected Language: {data.get('language')}")
    print(f"Response: {data.get('response')[:100]}...")
    print(f"Match Type: {data.get('match_type')}")
    print(f"Schemes Count: {len(data.get('schemes', []))}")
    print(f"{'='*60}")
    
    # Check no markdown
    response_text = data.get('response', '')
    has_markdown = any(m in response_text for m in ['**', '*', '#', '•'])
    print(f"✅ No markdown" if not has_markdown else "❌ Contains markdown!")
    
    return data.get('language') == expected_language

# Test cases
tests = [
    ("pm kisan scheme", "en"),
    ("ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್", "kn"),
    ("प्रधान मंत्री किसान", "hi"),
    ("agriculture schemes", "en"),
    ("ಕೃಷಿ ಯೋಜನೆಗಳು", "kn"),
    ("कृषि योजनाएं", "hi"),
]

passed = sum(1 for query, lang in tests if test_query(query, lang))
print(f"\n\n🎯 FINAL: {passed}/{len(tests)} tests passed")
```

Run it:

```bash
python test_api_multilingual.py
```

## Test 5: Check for Markdown

All responses should be **plain text only**. Check for these patterns (should NOT appear):

- `**bold**`
- `*italic*`
- `# heading`
- `• bullet`
- `1. numbered`
- `[link](url)`

### Verification Script

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chatbot/smart-query/",
    json={"query": "ಕೃಷಿ ಯೋಜನೆಗಳು"}
)

data = response.json()
full_text = data['response'] + ' '.join(data.get('schemes', []))

markdown_patterns = ['**', '*', '#', '•', '- ', '1. ', '2. ']
found_markdown = [p for p in markdown_patterns if p in full_text]

if found_markdown:
    print(f"❌ FAIL: Found markdown: {found_markdown}")
else:
    print("✅ PASS: No markdown detected!")
```

## Test 6: Database Translation Check

Check if scheme has translations:

```python
from chatbot.models import GovernmentScheme

scheme = GovernmentScheme.objects.first()
print(f"Scheme: {scheme.title}")
print(f"Kannada: {scheme.title_translations.get('kn', 'NOT SET')}")
print(f"Hindi: {scheme.title_translations.get('hi', 'NOT SET')}")
```

## Common Issues & Solutions

### Issue 1: Language Detected as English for Kannada/Hindi

**Cause:** Query too short

**Solution:** Use longer queries (4+ words)

```bash
# ❌ Too short
"ಕೃಷಿ"  # Might detect as 'en'

# ✅ Better
"ಕೃಷಿ ಯೋಜನೆಗಳು ಯಾವುವು"  # Detects as 'kn'
```

### Issue 2: Response Contains Markdown

**Cause:** `sanitize_markdown()` not applied

**Solution:** Check `views.py` - all responses should call `sanitize_markdown()`

### Issue 3: Translation Not Working

**Cause:** Gemini API key missing

**Solution:**
1. Check `.env` file has `GEMINI_API_KEY`
2. Restart Django server
3. Check logs for API errors

### Issue 4: Server Not Running

```bash
# Start Django server
python manage.py runserver 8000

# Or use run.bat/start.bat
```

## Quick Verification Checklist

- [ ] `langdetect` installed
- [ ] Django server running on port 8000
- [ ] Database has schemes loaded
- [ ] Test suite passes: `python test_multilingual_system.py`
- [ ] English API query works
- [ ] Kannada API query works
- [ ] Hindi API query works
- [ ] No markdown in responses
- [ ] `language` field present in all responses
- [ ] Greetings work in all 3 languages

## Performance Benchmark

Expected response times:

- **English query:** ~200-500ms
- **Kannada/Hindi with DB translation:** ~300-600ms
- **Kannada/Hindi without DB translation:** ~1500-3000ms (Gemini translation)

## Logs to Check

Watch Django console for these logs:

```
🌍 DETECTED_LANGUAGE: kn
🎯 STEP 1: Checking exact match...
✅ EXACT_MATCH found: PM-Kisan Scheme
```

## Success Criteria

✅ All 3 languages detected correctly  
✅ Greetings in correct language  
✅ Scheme responses in correct language  
✅ NO markdown in any response  
✅ `language` field in all JSON responses  
✅ Response times acceptable (<3s)  

---

**Ready to test?** Start with the unit tests, then move to API testing!

```bash
# Step 1: Unit tests
python test_multilingual_system.py

# Step 2: API test (English)
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"pm kisan scheme\"}"

# Step 3: API test (Kannada)
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"ಕೃಷಿ ಯೋಜನೆಗಳು\"}"

# Step 4: API test (Hindi)
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"कृषि योजनाएं\"}"
```

All tests passing? **You're ready for production!** 🎉
