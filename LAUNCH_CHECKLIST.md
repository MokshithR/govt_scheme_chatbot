# AI CHATBOT - FINAL LAUNCH CHECKLIST

**Date:** _______________  
**Tester:** _______________  
**Environment:** [ ] Development [ ] Staging [ ] Production

---

## PRE-LAUNCH VERIFICATION

### 1. DATABASE & EMBEDDINGS ✓

- [ ] **PostgreSQL Running**
  ```bash
  # Test connection
  docker ps | grep postgres
  # Should show running container
  ```

- [ ] **pgvector Extension Enabled**
  ```sql
  SELECT * FROM pg_extension WHERE extname = 'vector';
  -- Should return 1 row
  ```

- [ ] **Scheme Table Has vector(768) Column**
  ```sql
  SELECT column_name, data_type 
  FROM information_schema.columns 
  WHERE table_name = 'scheme' AND column_name = 'embedding';
  -- Should show: embedding | USER-DEFINED (vector)
  ```

- [ ] **All Schemes Have Embeddings**
  ```sql
  SELECT 
    COUNT(*) AS total,
    COUNT(embedding) AS with_embeddings,
    COUNT(*) - COUNT(embedding) AS missing
  FROM scheme;
  -- Target: missing = 0 (or at least < 5)
  ```
  
  **Current Count:** _______ / 106+ schemes with embeddings

- [ ] **Embeddings Are Valid 768-Dimensional Vectors**
  ```bash
  python manage.py test_ai_chatbot
  # Test 1 should PASS: "Embedding generated: 768 dims, all numeric, validated"
  ```

---

### 2. REDIS CACHE ✓

- [ ] **Redis Server Running**
  ```bash
  redis-cli ping
  # Should return: PONG
  ```

- [ ] **Redis Connection in Django Works**
  ```python
  # In Django shell
  from django.core.cache import cache
  cache.set('test_key', 'test_value', 10)
  print(cache.get('test_key'))  # Should print: test_value
  ```

- [ ] **Cache Keys Properly Namespaced**
  ```bash
  redis-cli KEYS "semantic_search:*"
  redis-cli KEYS "smart_answer:*"
  # After testing, should show cached queries
  ```

- [ ] **TTL Set to 12 Hours (43200s)**
  ```bash
  # After making a query
  redis-cli TTL "smart_answer:<some_hash>"
  # Should return value close to 43200
  ```

---

### 3. VECTOR SEARCH ACCURACY ✓

- [ ] **Test Query 1: Agriculture**
  ```bash
  curl -X POST http://localhost:8000/api/semantic-search-v2/ \
    -H "Content-Type: application/json" \
    -d '{"query": "loan schemes for farmers"}'
  ```
  **Expected:** Results include PM-KISAN, Kisan Credit Card, or similar agriculture schemes
  
  **Actual Result:** _______________________________________________

- [ ] **Test Query 2: Education**
  ```bash
  curl -X POST http://localhost:8000/api/semantic-search-v2/ \
    -H "Content-Type: application/json" \
    -d '{"query": "scholarship for college students"}'
  ```
  **Expected:** Results include education sector schemes
  
  **Actual Result:** _______________________________________________

- [ ] **Test Query 3: Healthcare**
  ```bash
  curl -X POST http://localhost:8000/api/semantic-search-v2/ \
    -H "Content-Type: application/json" \
    -d '{"query": "health insurance for senior citizens"}'
  ```
  **Expected:** Results include Ayushman Bharat or health schemes
  
  **Actual Result:** _______________________________________________

- [ ] **Distance Threshold Working (0.55)**
  - Good matches have distance ≤ 0.55
  - Poor matches are filtered out
  - Check with: Use `api_test_samples/irrelevant_query.json`

- [ ] **Results Sorted by Distance (Ascending)**
  - First result has smallest distance
  - Last result has largest distance

---

### 4. GREETING FALLBACK ✓

- [ ] **Test Greeting 1: "hello"**
  ```bash
  curl -X POST http://localhost:8000/api/smart-answer-v2/ \
    -H "Content-Type: application/json" \
    -d '{"query": "hello"}'
  ```
  **Expected Output:**
  - `"answer"` contains "YOJANAMITHRA"
  - `"schemes_used": []` (empty array)
  - Response time < 100ms
  
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Test Greeting 2: "hi"**
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Test Greeting 3: "namaste"**
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Test Greeting 4: "good morning"**
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Test Greeting 5: "how are you"**
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Verify No Database Query for Greetings**
  - Check Django logs
  - Should NOT see vector search queries
  - Should NOT see Gemini API calls

---

### 5. RAG ANSWERS ✓

- [ ] **Test RAG Query 1: Farming Loans**
  Use: `api_test_samples/loan_for_farmers.json`
  ```bash
  curl -X POST http://localhost:8000/api/smart-answer-v2/ \
    -H "Content-Type: application/json" \
    -d @api_test_samples/loan_for_farmers.json
  ```
  **Check:**
  - [ ] Answer is factual and relevant
  - [ ] `schemes_used` array contains 1-3 scheme names
  - [ ] Answer mentions specific amounts (e.g., ₹3 lakhs)
  - [ ] Answer includes application process
  - [ ] No hallucinated schemes

- [ ] **Test RAG Query 2: Crop Benefits**
  Use: `api_test_samples/crop_benefits.json`
  
  **Check:**
  - [ ] Multiple schemes mentioned
  - [ ] Benefits clearly explained
  - [ ] Official website included

- [ ] **Test RAG Query 3: Education Scholarship**
  Use: `api_test_samples/education_scholarship.json`
  
  **Check:**
  - [ ] Education sector schemes only
  - [ ] Eligibility criteria mentioned
  - [ ] Income limits specified

- [ ] **Test Irrelevant Query Fallback**
  Use: `api_test_samples/irrelevant_query.json`
  
  **Expected:**
  - [ ] Returns NO_RESULTS_MESSAGE
  - [ ] `schemes_used: []` (empty)
  - [ ] No hallucinated information
  - [ ] Gemini NOT called (fast response)

- [ ] **Gemini API Quota Check**
  - Visit: https://makersuite.google.com/app/apikey
  - Verify API key is active
  - Check quota limits
  
  **Status:** _______________________________________________

---

### 6. SSML VOICE OUTPUT ✓

- [ ] **SSML Tags Present**
  - All smart answer responses wrapped in `<speak>...</speak>`
  - Greeting response has `<break time="300ms"/>` tags

- [ ] **SSML Validation**
  ```bash
  python manage.py test_ai_chatbot
  # Test 6 should PASS: "SSML validation OK"
  ```

- [ ] **Test Voice Playback (if frontend ready)**
  - Navigate to chatbot page
  - Ask a question
  - Click voice/audio button
  - Verify audio plays correctly
  
  **Result:** [ ] PASS [ ] FAIL [ ] N/A (frontend not ready)

---

### 7. API RESPONSE STRUCTURE ✓

- [ ] **Semantic Search Response Format**
  ```json
  {
    "query": "string",
    "results": [
      {
        "id": "number",
        "title": "string",
        "short_description": "string",
        "distance": "float (0-2)",
        "similarity_score": "float (0-100)"
      }
    ],
    "count": "number"
  }
  ```

- [ ] **Smart Answer Response Format**
  ```json
  {
    "answer": "string",
    "ssml": "<speak>...</speak>",
    "schemes_used": ["string", "string"]
  }
  ```

- [ ] **JSON Serialization Test**
  ```bash
  python manage.py test_ai_chatbot
  # Test 5 should PASS: "JSON structure OK"
  ```

---

### 8. PERFORMANCE BENCHMARKS ✓

- [ ] **Response Time - Greeting (Cached)**
  - Target: < 100ms
  - Actual: _______ ms

- [ ] **Response Time - RAG First Query (Uncached)**
  - Target: < 5 seconds
  - Actual: _______ ms

- [ ] **Response Time - RAG Cached Query**
  - Target: < 500ms
  - Actual: _______ ms

- [ ] **Response Time - Semantic Search**
  - Target: < 3 seconds
  - Actual: _______ ms

- [ ] **Cache Hit Rate After 10 Queries**
  ```bash
  # Run same query 10 times, check cache
  redis-cli INFO stats | grep keyspace_hits
  ```
  - Hit Rate: _______ %
  - Target: > 70%

---

### 9. ERROR HANDLING ✓

- [ ] **Empty Query**
  ```bash
  curl -X POST http://localhost:8000/api/smart-answer-v2/ \
    -H "Content-Type: application/json" \
    -d '{"query": ""}'
  ```
  **Expected:** HTTP 400 with error message
  
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Missing Query Field**
  ```bash
  curl -X POST http://localhost:8000/api/smart-answer-v2/ \
    -H "Content-Type: application/json" \
    -d '{}'
  ```
  **Expected:** HTTP 400 with error message
  
  **Result:** [ ] PASS [ ] FAIL

- [ ] **Invalid JSON**
  ```bash
  curl -X POST http://localhost:8000/api/smart-answer-v2/ \
    -H "Content-Type: application/json" \
    -d 'not valid json'
  ```
  **Expected:** HTTP 400 or 500 with error
  
  **Result:** [ ] PASS [ ] FAIL

---

### 10. AUTOMATED TEST SUITE ✓

- [ ] **Run Complete Test Suite**
  ```bash
  python manage.py test_ai_chatbot
  ```
  
  **Results:**
  - [ ] Test 1: Embedding Validity - PASSED
  - [ ] Test 2: Vector Similarity - PASSED
  - [ ] Test 3: Greeting Fallback - PASSED
  - [ ] Test 4: RAG Response - PASSED
  - [ ] Test 5: JSON Structure - PASSED
  - [ ] Test 6: SSML Validation - PASSED
  
  **Final Score:** _______ / 6 tests passed

---

### 11. FRONTEND INTEGRATION ✓

- [ ] **API Endpoints Accessible from Frontend**
  - Check CORS settings if needed
  - Verify BASE_URL in frontend config

- [ ] **Test from Frontend UI**
  - [ ] Voice input working
  - [ ] Text input working
  - [ ] Response displayed correctly
  - [ ] Audio playback working
  - [ ] Scheme cards displayed
  - [ ] "Apply Now" buttons working

- [ ] **Test Different Languages (if multilingual)**
  - [ ] English queries
  - [ ] Hindi queries
  - [ ] Kannada queries (if supported)

---

### 12. DEPLOYMENT READINESS ✓

- [ ] **Environment Variables Set**
  ```bash
  # Check .env file has:
  GEMINI_API_KEY=xxxxx
  REDIS_HOST=localhost
  REDIS_PORT=6379
  DATABASE_URL=postgresql://...
  ```

- [ ] **Dependencies Installed**
  ```bash
  pip freeze | grep -E "(sentence-transformers|google-generativeai|redis|psycopg2|pgvector)"
  ```
  **Required packages present:** [ ] YES [ ] NO

- [ ] **Static Files Collected (if production)**
  ```bash
  python manage.py collectstatic --noinput
  ```

- [ ] **Database Migrations Applied**
  ```bash
  python manage.py showmigrations
  # All should show [X] (applied)
  ```

- [ ] **Debug Mode OFF (production only)**
  ```python
  # settings.py
  DEBUG = False  # For production
  ```

- [ ] **Allowed Hosts Configured (production only)**
  ```python
  # settings.py
  ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
  ```

---

### 13. SECURITY CHECKS ✓

- [ ] **API Rate Limiting (if implemented)**
  - Test: Send 100 requests rapidly
  - Expected: Rate limit triggers after X requests

- [ ] **CSRF Protection**
  - Endpoints use `@csrf_exempt` (REST API standard)
  - Or CSRF tokens implemented

- [ ] **Input Sanitization**
  - Test SQL injection: `{"query": "'; DROP TABLE scheme;--"}`
  - Should be safely handled

- [ ] **API Key Security**
  - Gemini API key in .env (not hardcoded)
  - .env file in .gitignore

---

### 14. MONITORING & LOGGING ✓

- [ ] **Enable Debug Middleware (development)**
  ```python
  # settings.py
  MIDDLEWARE = [
      # ... existing ...
      'chatbot.middleware.ChatbotQueryLoggerMiddleware',
  ]
  ```

- [ ] **Test Logging Output**
  - Start server
  - Make a query
  - Verify colored logs appear in console:
    - ╔═══ CHATBOT QUERY INCOMING
    - Semantic search distances
    - Fallback triggers
    - RAG prompts

- [ ] **Production Logging Setup (if deploying)**
  - Configure logging to file
  - Set up error alerting
  - Monitor Gemini API usage

---

### 15. BACKUP & RECOVERY ✓

- [ ] **Database Backup**
  ```bash
  # Export schemes with embeddings
  docker exec postgres_container pg_dump -U user -d dbname -t scheme > scheme_backup.sql
  ```

- [ ] **Redis Backup (optional)**
  ```bash
  redis-cli BGSAVE
  ```

- [ ] **Code Version Control**
  - [ ] All code committed to git
  - [ ] .env file in .gitignore
  - [ ] requirements.txt up to date

---

## FINAL SIGN-OFF

### Critical Issues Found
_List any issues that must be fixed before launch:_

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Non-Critical Issues
_List minor issues to fix post-launch:_

1. _______________________________________________
2. _______________________________________________

### Performance Metrics
- Average response time (RAG): _______ seconds
- Average response time (greeting): _______ ms
- Cache hit rate: _______ %
- Schemes with embeddings: _______ / 106+

### Ready for Launch?

- [ ] **YES** - All critical tests passed, system ready for production
- [ ] **NO** - Issues found, need to fix before launch
- [ ] **PARTIAL** - Ready for staging/beta testing

**Tester Signature:** _______________________________________________

**Date:** _______________________________________________

---

## POST-LAUNCH MONITORING (First 24 Hours)

- [ ] Monitor API error rate (target: < 1%)
- [ ] Monitor average response time
- [ ] Check Gemini API quota usage
- [ ] Monitor Redis memory usage
- [ ] Check PostgreSQL performance
- [ ] Collect user feedback
- [ ] Review server logs for errors

**Notes:**
_______________________________________________
_______________________________________________
_______________________________________________
