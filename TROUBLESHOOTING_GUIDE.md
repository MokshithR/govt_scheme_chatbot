# AI CHATBOT TROUBLESHOOTING GUIDE

## Quick Diagnostics

Run this command first to check system health:
```bash
python manage.py test_ai_chatbot
```

---

## 1. COMMON ERRORS

### Error: "Redis connection refused"
**Symptoms:**
- API returns 500 error
- Logs show "ConnectionError: Error 10061"

**Solutions:**
1. Check if Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Start Redis if not running:
   ```bash
   # Windows (if installed as service)
   net start Redis
   
   # Or run manually
   redis-server
   ```

3. Check Redis connection in Django settings:
   ```python
   # settings.py
   REDIS_HOST = 'localhost'  # or '127.0.0.1'
   REDIS_PORT = 6379
   ```

4. Test connection manually:
   ```python
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   r.ping()  # Should return True
   ```

---

### Error: "Embedding dimension mismatch"
**Symptoms:**
- Error: "Expected 768 dimensions, got X"
- Search fails with vector length error

**Solutions:**
1. Check embedding generation:
   ```python
   from chatbot.embedding_utils import create_embedding
   emb = create_embedding("test")
   print(len(emb))  # Should be 768
   ```

2. Verify HuggingFace model loaded correctly:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
   print(model.get_sentence_embedding_dimension())  # Should be 768
   ```

3. Regenerate embeddings if corrupted:
   ```bash
   python manage.py generate_embeddings --force
   ```

4. Check database column type:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'scheme' AND column_name = 'embedding';
   -- Should be: vector(768)
   ```

---

### Error: "Gemini API key missing"
**Symptoms:**
- Smart answer endpoint fails
- Error: "API key not valid"

**Solutions:**
1. Check `.env` file has key:
   ```
   GEMINI_API_KEY=your_key_here
   ```

2. Verify key is loaded:
   ```python
   import os
   print(os.getenv('GEMINI_API_KEY'))  # Should not be None
   ```

3. Test Gemini connection:
   ```bash
   python test_gemini_api.py
   ```

4. Get new API key if needed:
   - Visit: https://makersuite.google.com/app/apikey
   - Create new key
   - Update `.env` file

---

### Error: "No schemes have embeddings"
**Symptoms:**
- Search returns empty results
- Count shows 0 schemes with embeddings

**Solutions:**
1. Check database:
   ```sql
   SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;
   ```

2. Generate embeddings:
   ```bash
   python manage.py generate_embeddings
   ```

3. Verify batch processing:
   ```bash
   python manage.py generate_embeddings --batch-size 10
   ```

4. Check for specific scheme:
   ```bash
   python manage.py generate_embeddings --scheme-id 1
   ```

---

## 2. INACCURATE RAG ANSWERS

### Problem: Chatbot returns irrelevant schemes
**Diagnosis:**
- Threshold too high (allowing poor matches)
- Scheme descriptions not specific enough

**Solutions:**
1. Lower similarity threshold in `smart_answer_view()`:
   ```python
   # Current: 0.55
   # Try: 0.45 for stricter matching
   good_matches = [r for r in results if r['distance'] <= 0.45]
   ```

2. Check search distances:
   ```python
   from chatbot.debug_loggers import log_search_distances
   # Add to smart_answer_view before filtering
   log_search_distances(query, results)
   ```

3. Improve scheme descriptions:
   - Add more keywords to `search_tags`
   - Update `short_description` with relevant terms
   - Include sector-specific terminology

4. Test with sample queries:
   ```bash
   python test_new_api_endpoints.py
   ```

---

### Problem: Chatbot hallucinates information
**Diagnosis:**
- RAG not using retrieved schemes
- Gemini generating without context

**Solutions:**
1. Verify schemes_used in response:
   ```json
   {
     "answer": "...",
     "schemes_used": ["PM-KISAN", "KCC"]  // Should NOT be empty
   }
   ```

2. Check RAG prompt construction:
   ```python
   from chatbot.debug_loggers import log_rag_prompt
   # Add to smart_answer_view before Gemini call
   log_rag_prompt(query, schemes_text, USER_PROMPT_TEMPLATE)
   ```

3. Strengthen SYSTEM_PROMPT:
   ```python
   # chatbot/prompts.py
   SYSTEM_PROMPT = """
   You are a factual government schemes assistant.
   CRITICAL RULES:
   1. ONLY use information from provided schemes
   2. NEVER invent scheme names, amounts, or links
   3. If uncertain, say "I don't have that information"
   4. Quote official website URLs exactly as provided
   """
   ```

4. Lower Gemini temperature (already at 0):
   ```python
   generation_config = {
       "temperature": 0,  # Maximum determinism
       "top_p": 0.1,      # Reduced randomness
       "top_k": 1,        # Most likely token
   }
   ```

---

### Problem: Answers too generic
**Diagnosis:**
- Not enough context from schemes
- Gemini summarizing too much

**Solutions:**
1. Increase max_output_tokens:
   ```python
   # Current: 300
   # Try: 500 for more detailed answers
   "max_output_tokens": 500
   ```

2. Improve context building in `smart_answer_view()`:
   ```python
   # Add more fields to schemes_text
   schemes_text += f"\n- Application Process: {scheme.application_process}"
   schemes_text += f"\n- Required Documents: {scheme.required_documents}"
   ```

3. Update USER_PROMPT_TEMPLATE:
   ```python
   USER_PROMPT_TEMPLATE = """
   User Question: {query}
   
   Relevant Schemes:
   {schemes_text}
   
   Provide a DETAILED answer with:
   1. Specific eligibility criteria
   2. Exact benefit amounts
   3. Step-by-step application process
   4. Official website links
   """
   ```

---

## 3. INCORRECT EMBEDDINGS

### Problem: Embedding generation fails for some schemes
**Diagnosis:**
- Null/empty text fields
- Unicode/encoding issues

**Solutions:**
1. Check scheme data:
   ```python
   from chatbot.models import Scheme
   scheme = Scheme.objects.get(id=X)
   print(scheme.title)  # Should not be None
   print(scheme.short_description)
   ```

2. Test embedding preparation:
   ```python
   from chatbot.embedding_utils import prepare_embedding_text
   text = prepare_embedding_text(scheme)
   print(len(text))  # Should be > 0
   print(text[:200])  # Check for encoding issues
   ```

3. Handle JSONB fields properly:
   ```python
   # embedding_utils.py already does this:
   keywords = scheme.keywords or []
   if isinstance(keywords, str):
       keywords = json.loads(keywords)
   ```

4. Regenerate specific scheme:
   ```bash
   python manage.py generate_embeddings --scheme-id X --force
   ```

---

### Problem: Search returns unexpected results
**Diagnosis:**
- Embeddings not reflecting scheme content
- Model not loaded correctly

**Solutions:**
1. Test similarity manually:
   ```python
   from chatbot.vector_search import find_similar_to_scheme
   results = find_similar_to_scheme(scheme_id=1, top_k=5)
   for r in results:
       print(f"{r['title']}: {r['distance']:.4f}")
   ```

2. Verify model output:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
   
   text1 = "agriculture loan for farmers"
   text2 = "health insurance for senior citizens"
   
   emb1 = model.encode(text1)
   emb2 = model.encode(text2)
   
   # Calculate cosine distance
   from scipy.spatial.distance import cosine
   distance = cosine(emb1, emb2)
   print(distance)  # Should be > 0.5 (different topics)
   ```

3. Rebuild all embeddings:
   ```bash
   python manage.py generate_embeddings --force
   ```

---

## 4. PERFORMANCE & CACHING

### Problem: Slow API responses (>5 seconds)
**Diagnosis:**
- Cache not working
- Database query slow
- Gemini API delay

**Solutions:**
1. Check cache hit rate:
   ```python
   from chatbot.debug_loggers import log_cache_event
   # Add to API views
   log_cache_event('hit', cache_key)  # or 'miss'
   ```

2. Monitor response times:
   ```python
   # chatbot/middleware.py already logs this
   # Check console for "Response Time: X.XXs"
   ```

3. Test cache manually:
   ```python
   import redis
   import hashlib
   
   r = redis.Redis(host='localhost', port=6379, db=0)
   query = "test query"
   cache_key = f"smart_answer:{hashlib.md5(query.encode()).hexdigest()}"
   
   # Check if cached
   cached = r.get(cache_key)
   print(f"Cached: {cached is not None}")
   ```

4. Optimize database queries:
   ```sql
   -- Check if index exists
   SELECT indexname, indexdef 
   FROM pg_indexes 
   WHERE tablename = 'scheme';
   
   -- Create index if missing
   CREATE INDEX ON scheme USING ivfflat (embedding vector_cosine_ops);
   ```

---

### Problem: Redis memory usage too high
**Diagnosis:**
- Too many cached responses
- TTL too long

**Solutions:**
1. Check Redis memory:
   ```bash
   redis-cli INFO memory
   ```

2. Reduce TTL (currently 12 hours):
   ```python
   # In smart_answer_view()
   # Current: 43200 seconds (12 hours)
   # Try: 3600 seconds (1 hour)
   cache.set(cache_key, response, timeout=3600)
   ```

3. Clear old cache:
   ```bash
   redis-cli FLUSHDB
   ```

4. Set maxmemory policy:
   ```bash
   redis-cli CONFIG SET maxmemory 256mb
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

---

## 5. PGVECTOR INDEX HEALTH

### Check index status
```sql
-- List all indexes on scheme table
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'scheme';

-- Check index size
SELECT pg_size_pretty(pg_relation_size('scheme_embedding_idx'));

-- Check if index is being used
EXPLAIN ANALYZE 
SELECT id, title, (embedding <-> '[0.1,0.2,...]'::vector) AS distance 
FROM scheme 
ORDER BY embedding <-> '[0.1,0.2,...]'::vector 
LIMIT 5;
```

### Rebuild index if needed
```sql
-- Drop old index
DROP INDEX IF EXISTS scheme_embedding_idx;

-- Create new IVFFlat index (faster for large datasets)
CREATE INDEX ON scheme USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Or HNSW index (better accuracy)
CREATE INDEX ON scheme USING hnsw (embedding vector_cosine_ops);

-- Analyze table
ANALYZE scheme;
```

### Monitor query performance
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as queries:
    # Run search
    results = search_similar_schemes(query_embedding)
    
    # Check query time
    for q in queries:
        print(f"Time: {q['time']}s")
        print(f"SQL: {q['sql'][:200]}")
```

---

## 6. TESTING CHECKLIST

Before deployment, verify:

- [ ] Run `python manage.py test_ai_chatbot` - all 6 tests pass
- [ ] Test greeting fallback: `curl -X POST http://localhost:8000/api/smart-answer-v2/ -d '{"query":"hello"}'`
- [ ] Test semantic search: Use POSTMAN with `api_test_samples/loan_for_farmers.json`
- [ ] Test irrelevant query fallback: Use `api_test_samples/irrelevant_query.json`
- [ ] Check Redis: `redis-cli ping`
- [ ] Check embeddings count: `SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;`
- [ ] Monitor logs: Enable `ChatbotQueryLoggerMiddleware` in settings
- [ ] Test response time: Should be <5s for RAG, <100ms for greetings
- [ ] Verify cache: Second identical query should be <500ms
- [ ] Check Gemini quota: Visit https://makersuite.google.com/app/apikey

---

## 7. DEBUG MODE

Enable detailed logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'chatbot': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Add middleware
MIDDLEWARE = [
    # ... existing middleware ...
    'chatbot.middleware.ChatbotQueryLoggerMiddleware',
]
```

Use debug loggers in views:

```python
from chatbot.debug_loggers import (
    log_search_distances,
    log_fallback_trigger,
    log_rag_prompt,
    log_cache_event,
    log_error
)

# Example usage in smart_answer_view
log_search_distances(query, results)
log_fallback_trigger('threshold', query, {'best_distance': 0.75})
log_rag_prompt(query, schemes_text, USER_PROMPT_TEMPLATE)
```

---

## 8. EMERGENCY FIXES

### Complete system reset:
```bash
# 1. Clear Redis cache
redis-cli FLUSHDB

# 2. Regenerate all embeddings
python manage.py generate_embeddings --force

# 3. Restart Django server
# Kill existing process, then:
python manage.py runserver

# 4. Test system
python manage.py test_ai_chatbot
```

### Rollback to Gemini-based system:
If HuggingFace system fails, old Gemini endpoints still exist:
- `/api/semantic-search/` (old Gemini version)
- `/api/smart-answer/` (old Gemini version)

Update frontend to use old endpoints temporarily.

---

## Support

For additional help:
1. Check Django logs: `python manage.py runserver` output
2. Check PostgreSQL logs: `docker logs postgres_container`
3. Check Redis logs: `redis-cli MONITOR`
4. Review documentation: `HUGGINGFACE_API_COMPLETE.md`
