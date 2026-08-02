# QUICK START - TESTING YOUR AI CHATBOT

This is your **5-minute quick test** to verify everything works.

---

## STEP 1: Run the Automated Test Suite (1 minute)

```bash
python manage.py test_ai_chatbot
```

**Expected Output:**
```
======================================================================
AI CHATBOT SYSTEM - AUTOMATED TEST SUITE
======================================================================

======================================================================
TEST: Embedding Validity
======================================================================

✓ PASSED: Embedding generated: 768 dims, all numeric, validated

======================================================================
TEST: Vector Similarity Search
======================================================================

✓ PASSED: Search OK: 5 results, best distance=0.2341, 'Kisan Credit Card Scheme'

======================================================================
TEST: Greeting Fallback Detection
======================================================================

✓ PASSED: Greeting detection OK: 5 greetings tested, response ready

======================================================================
TEST: RAG Response Pipeline
======================================================================

✓ PASSED: RAG pipeline OK: 3 good matches, ready for Gemini

======================================================================
TEST: JSON Output Structure
======================================================================

✓ PASSED: JSON structure OK: All required fields present, serializable

======================================================================
TEST: SSML Validation
======================================================================

✓ PASSED: SSML validation OK: Proper tags, content present

======================================================================
FINAL RESULTS: 6/6 TESTS PASSED
======================================================================

✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT
```

**If any test FAILS:** Check `TROUBLESHOOTING_GUIDE.md`

---

## STEP 2: Test API Endpoints with Curl (2 minutes)

### Test 1: Greeting Response
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"hello\"}"
```

**Expected Response:**
```json
{
  "answer": "Hello! I am YOJANAMITHRA, your Government Schemes Assistant...",
  "ssml": "<speak>Hello! I am YOJANAMITHRA...</speak>",
  "schemes_used": []
}
```

✅ **Check:** `schemes_used` is empty array, response < 100ms

---

### Test 2: Real Query - Farming
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What loan schemes are available for farmers?\"}"
```

**Expected Response:**
```json
{
  "answer": "Farmers can avail the following loan schemes:\n\n1. Kisan Credit Card (KCC): Provides credit up to ₹3 lakhs for agricultural needs...",
  "ssml": "<speak>Farmers can avail the following loan schemes...</speak>",
  "schemes_used": ["Kisan Credit Card", "PM-KISAN"]
}
```

✅ **Check:** 
- Answer mentions specific schemes
- `schemes_used` has 1-3 items
- Contains amounts (₹ symbols)
- Response < 5 seconds

---

### Test 3: Semantic Search
```bash
curl -X POST http://localhost:8000/api/semantic-search-v2/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"education scholarship for students\"}"
```

**Expected Response:**
```json
{
  "query": "education scholarship for students",
  "results": [
    {
      "id": 23,
      "title": "Post Matric Scholarship for SC/ST Students",
      "short_description": "Financial assistance for SC/ST students...",
      "distance": 0.2845,
      "similarity_score": 85.77
    },
    {
      "id": 45,
      "title": "National Scholarship Portal",
      "distance": 0.3201,
      "similarity_score": 83.99
    }
  ],
  "count": 2
}
```

✅ **Check:**
- Results are relevant to education
- Distances are < 0.6
- Sorted by distance (ascending)

---

### Test 4: Irrelevant Query (Fallback)
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"best pizza restaurants near me\"}"
```

**Expected Response:**
```json
{
  "answer": "I couldn't find any relevant government schemes for your query...",
  "ssml": "<speak>I couldn't find any relevant government schemes...</speak>",
  "schemes_used": []
}
```

✅ **Check:**
- Returns NO_RESULTS_MESSAGE
- `schemes_used` is empty
- No hallucinated schemes

---

## STEP 3: Test with POSTMAN (1 minute)

### Import Test Collection

1. Open POSTMAN
2. Create new request
3. Method: **POST**
4. URL: `http://localhost:8000/api/smart-answer-v2/`
5. Headers: `Content-Type: application/json`
6. Body (raw JSON):

**Use the sample files in `api_test_samples/` folder:**

- `loan_for_farmers.json` - Agriculture query
- `crop_benefits.json` - Farming benefits
- `education_scholarship.json` - Education query
- `greeting_hello.json` - Greeting test
- `irrelevant_query.json` - Fallback test

### Quick POSTMAN Test:
```json
{
  "query": "health insurance for senior citizens"
}
```

**Send → Check Response:**
- Status: 200 OK
- Response has `answer`, `ssml`, `schemes_used`
- SSML wrapped in `<speak>` tags

---

## STEP 4: Check Database & Cache (1 minute)

### Check Embeddings Count
```sql
SELECT 
  COUNT(*) AS total,
  COUNT(embedding) AS with_embeddings,
  COUNT(*) - COUNT(embedding) AS missing
FROM scheme;
```

**Expected:** 
- Total: 106+
- With embeddings: 106+
- Missing: 0

---

### Check Redis Cache
```bash
redis-cli ping
```
**Expected:** `PONG`

```bash
redis-cli KEYS "smart_answer:*"
```
**Expected:** Shows cached queries (after you've made some requests)

---

## STEP 5: Enable Debug Logging (Optional)

Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... existing middleware ...
    'chatbot.middleware.ChatbotQueryLoggerMiddleware',
]
```

Restart server and run a query. You'll see:
```
╔════════════════════════════════════════════════════════════
║ CHATBOT QUERY INCOMING
╠════════════════════════════════════════════════════════════
║ Endpoint: /api/smart-answer-v2/
║ Query: loan for farmers
║ Timestamp: 2025-11-23 14:30:45
╚════════════════════════════════════════════════════════════
```

See full guide: `DEBUG_LOGGING_GUIDE.md`

---

## TROUBLESHOOTING

### ❌ Test Suite Fails
```
✗ FAILED: No search results (database may be empty)
```
**Fix:** Run `python manage.py generate_embeddings`

---

### ❌ Redis Connection Error
```
ConnectionRefusedError: [Errno 10061]
```
**Fix:** 
```bash
redis-server  # Start Redis
# Or: net start Redis (Windows service)
```

---

### ❌ Gemini API Error
```
API key not valid
```
**Fix:** Check `.env` file has `GEMINI_API_KEY=your_key_here`

---

### ❌ Empty Response / No Schemes
```json
{
  "answer": "I couldn't find any relevant government schemes...",
  "schemes_used": []
}
```

**Diagnosis:** Check if query is too specific or embeddings missing

**Fix:**
```bash
# Check embeddings
SELECT COUNT(embedding) FROM scheme;

# Regenerate if needed
python manage.py generate_embeddings --force
```

---

## SUCCESS CHECKLIST

After completing these 5 steps, you should have:

- ✅ All 6 automated tests PASSED
- ✅ Greeting response works (instant, <100ms)
- ✅ Real queries return relevant schemes
- ✅ Semantic search returns accurate results
- ✅ Fallback works for irrelevant queries
- ✅ Database has 106+ embeddings
- ✅ Redis cache working
- ✅ SSML output valid

**If all ✅ → Your chatbot is READY FOR DEPLOYMENT!**

---

## NEXT STEPS

1. **Frontend Integration:** Connect your UI to the API endpoints
2. **Full Testing:** Use `LAUNCH_CHECKLIST.md` for comprehensive testing
3. **Production Setup:** Configure for deployment
4. **Monitoring:** Set up logging and error tracking

---

## QUICK REFERENCE

**API Endpoints:**
- Semantic Search: `POST /api/semantic-search-v2/`
- Smart Answer (RAG): `POST /api/smart-answer-v2/`

**Management Commands:**
- Test system: `python manage.py test_ai_chatbot`
- Generate embeddings: `python manage.py generate_embeddings`

**Documentation:**
- Full implementation: `HUGGINGFACE_API_COMPLETE.md`
- Troubleshooting: `TROUBLESHOOTING_GUIDE.md`
- Launch checklist: `LAUNCH_CHECKLIST.md`
- Debug logging: `DEBUG_LOGGING_GUIDE.md`
