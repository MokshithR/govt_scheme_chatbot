# HOW TO USE DEBUG LOGGERS IN YOUR VIEWS

This guide shows you how to integrate the debug logging helpers into your `smart_answer_view()` and `semantic_search_view()` functions.

---

## STEP 1: Enable the Middleware

Add this to your `settings.py`:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # ADD THIS LINE:
    'chatbot.middleware.ChatbotQueryLoggerMiddleware',  # <-- Debug logging
]
```

**What it does:**
- Logs every incoming query to `/api/semantic-search-v2/` and `/api/smart-answer-v2/`
- Prints query, endpoint, timestamp
- Measures and logs response time
- Color codes: FAST (<1s), OK (1-3s), SLOW (>3s)

---

## STEP 2: Add Debug Loggers to semantic_search_view()

Open `chatbot/views.py` and find your `semantic_search_view()` function.

Add these imports at the top of the file:

```python
# At the top of views.py
from chatbot.debug_loggers import (
    log_search_distances,
    log_cache_event,
    log_embedding_generation,
    log_error
)
```

Then modify `semantic_search_view()` like this:

```python
@csrf_exempt
@api_view(['POST'])
def semantic_search_view(request):
    try:
        # Get query
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check cache
        cache_key = f"semantic_search:{hashlib.md5(query.encode()).hexdigest()}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            # LOG: Cache hit
            log_cache_event('hit', cache_key)
            return Response(cached_response)
        else:
            # LOG: Cache miss
            log_cache_event('miss', cache_key)
        
        # Generate embedding
        query_embedding = create_embedding(query)
        
        # LOG: Embedding generated
        log_embedding_generation(query, len(query_embedding))
        
        # Search
        results = search_similar_schemes(
            query_embedding, 
            top_k=5,
            filters={'is_active': True}
        )
        
        # LOG: Search distances (COLOR CODED)
        log_search_distances(query, results)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['id'],
                'title': result['title'],
                'short_description': result.get('short_description', ''),
                'distance': result['distance'],
                'similarity_score': result.get('similarity_score', 0)
            })
        
        response_data = {
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        }
        
        # Cache response
        cache.set(cache_key, response_data, timeout=43200)
        log_cache_event('set', cache_key)
        
        return Response(response_data)
        
    except Exception as e:
        # LOG: Error
        log_error('semantic_search', str(e), {'query': query})
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## STEP 3: Add Debug Loggers to smart_answer_view()

Find your `smart_answer_view()` function and modify it like this:

```python
# Additional imports needed
from chatbot.debug_loggers import (
    log_search_distances,
    log_fallback_trigger,
    log_rag_prompt,
    log_cache_event,
    log_embedding_generation,
    log_error
)

@csrf_exempt
@api_view(['POST'])
def smart_answer_view(request):
    try:
        # Get query
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for greeting
        query_lower = query.lower()
        if any(greeting in query_lower for greeting in GREETINGS):
            # LOG: Greeting fallback triggered
            log_fallback_trigger('greeting', query)
            
            return Response({
                'answer': GREETING_RESPONSE,
                'ssml': GREETING_SSML,
                'schemes_used': []
            })
        
        # Check cache
        cache_key = f"smart_answer:{hashlib.md5(query.encode()).hexdigest()}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            log_cache_event('hit', cache_key)
            return Response(cached_response)
        else:
            log_cache_event('miss', cache_key)
        
        # Generate embedding
        query_embedding = create_embedding(query)
        log_embedding_generation(query, len(query_embedding))
        
        # Search
        results = search_similar_schemes(
            query_embedding,
            top_k=5,
            filters={'is_active': True}
        )
        
        # LOG: Search distances (COLOR CODED)
        log_search_distances(query, results)
        
        # Filter by threshold
        THRESHOLD = 0.55
        good_matches = [r for r in results if r['distance'] <= THRESHOLD]
        
        # Check if no good matches
        if not good_matches:
            # LOG: Threshold fallback triggered
            best_distance = results[0]['distance'] if results else 999
            log_fallback_trigger('threshold', query, {'best_distance': best_distance})
            
            return Response({
                'answer': NO_RESULTS_MESSAGE,
                'ssml': NO_RESULTS_SSML,
                'schemes_used': []
            })
        
        # Build context from schemes
        schemes_text = ""
        schemes_used = []
        
        for match in good_matches:
            scheme = match['scheme_object']
            schemes_used.append(scheme.title)
            
            schemes_text += f"\n\nScheme: {scheme.title}\n"
            schemes_text += f"Ministry: {getattr(scheme, 'ministry', 'N/A')}\n"
            schemes_text += f"Government Level: {getattr(scheme, 'government_level', 'N/A')}\n"
            schemes_text += f"State: {getattr(scheme, 'state', 'All India')}\n"
            schemes_text += f"Description: {scheme.short_description}\n"
            
            if hasattr(scheme, 'eligibility_criteria'):
                schemes_text += f"Eligibility: {scheme.eligibility_criteria}\n"
            
            if hasattr(scheme, 'financial_assistance'):
                schemes_text += f"Financial Assistance: {scheme.financial_assistance}\n"
            
            if hasattr(scheme, 'official_website'):
                schemes_text += f"Official Website: {scheme.official_website}\n"
        
        # Build RAG prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            schemes_text=schemes_text
        )
        
        # LOG: RAG prompt (shows what's sent to Gemini)
        log_rag_prompt(query, schemes_text, USER_PROMPT_TEMPLATE)
        
        # Call Gemini
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        generation_config = {
            "temperature": 0,
            "top_p": 0.1,
            "top_k": 1,
            "max_output_tokens": 300,
        }
        
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        final_answer = response.text
        ssml_output = f"<speak>{final_answer}</speak>"
        
        response_data = {
            'answer': final_answer,
            'ssml': ssml_output,
            'schemes_used': schemes_used
        }
        
        # Cache response
        cache.set(cache_key, response_data, timeout=43200)
        log_cache_event('set', cache_key)
        
        return Response(response_data)
        
    except Exception as e:
        log_error('smart_answer', str(e), {'query': query})
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## STEP 4: Install colorama (for colored logs)

```bash
pip install colorama
```

Add to `requirements.txt`:
```
colorama>=0.4.6
```

---

## STEP 5: Test the Debug Loggers

Start your Django server:
```bash
python manage.py runserver
```

Make a test query:
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d '{"query": "loan for farmers"}'
```

**You should see colored output like:**

```
╔════════════════════════════════════════════════════════════
║ CHATBOT QUERY INCOMING
╠════════════════════════════════════════════════════════════
║ Endpoint: /api/smart-answer-v2/
║ Query: loan for farmers
║ Timestamp: 2025-11-23 14:30:45
╚════════════════════════════════════════════════════════════

🔍 CACHE MISS: smart_answer:a1b2c3... (generating fresh response)

🧮 EMBEDDING GENERATED
Text: loan for farmers
Dimensions: 768
✓ Dimensions OK

======================================================================
SEMANTIC SEARCH RESULTS
Query: loan for farmers
======================================================================

[1] Distance: 0.2341 (EXCELLENT ✓✓)
    Title: Kisan Credit Card Scheme

[2] Distance: 0.3892 (GOOD ✓)
    Title: PM-KISAN Direct Benefit Transfer

[3] Distance: 0.4521 (GOOD ✓)
    Title: Agricultural Term Loans

======================================================================

======================================================================
RAG PROMPT SENT TO GEMINI
======================================================================

User Query:
loan for farmers

Schemes Context (first 500 chars):
Scheme: Kisan Credit Card Scheme
Ministry: Ministry of Agriculture
Government Level: Central
State: All India
Description: Provides credit to farmers for agricultural needs...
[Total context length: 1847 chars]

Full Prompt (first 500 chars):
You are a government schemes assistant. Answer based on these schemes:

Scheme: Kisan Credit Card Scheme
Ministry: Ministry of Agriculture
...
[Total prompt length: 1950 chars]

======================================================================

💾 CACHE SET: smart_answer:a1b2c3... (TTL: 12 hours)

╔════════════════════════════════════════════════════════════
║ CHATBOT RESPONSE SENT
╠════════════════════════════════════════════════════════════
║ Endpoint: /api/smart-answer-v2/
║ Status: 200
║ Response Time: 2.34s (OK)
╚════════════════════════════════════════════════════════════
```

---

## STEP 6: Test Different Scenarios

### Test Greeting (should trigger fallback):
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

**Expected log:**
```
==================================================================== 
 FALLBACK TRIGGERED 
====================================================================
Type: GREETING
Query: hello
Action: Returning greeting response (no DB search)
Response Time: <100ms (instant)
====================================================================
```

### Test Irrelevant Query (should trigger threshold fallback):
```bash
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing research"}'
```

**Expected log:**
```
[1] Distance: 0.7823 (POOR ✗ (FILTERED OUT))
    Title: Some Scheme

[2] Distance: 0.8145 (POOR ✗ (FILTERED OUT))
    Title: Another Scheme

==================================================================== 
 FALLBACK TRIGGERED 
====================================================================
Type: THRESHOLD
Query: quantum computing research
Action: No good matches (all distances > 0.55)
Response: NO_RESULTS_MESSAGE
Best Distance: 0.7823
====================================================================
```

### Test Cached Query (should be fast):
```bash
# Run same query twice
curl -X POST http://localhost:8000/api/smart-answer-v2/ \
  -H "Content-Type: application/json" \
  -d '{"query": "loan for farmers"}'
```

**Expected log (second time):**
```
🗄 CACHE HIT: smart_answer:a1b2c3...

Response Time: 0.05s (FAST ✓)
```

---

## STEP 7: Disable Debug Logging (Production)

When deploying to production, **REMOVE** the middleware:

```python
# settings.py - PRODUCTION
MIDDLEWARE = [
    # ... other middleware ...
    # 'chatbot.middleware.ChatbotQueryLoggerMiddleware',  # COMMENTED OUT
]
```

Or keep it but configure proper logging to file instead of console.

---

## TROUBLESHOOTING DEBUG LOGGERS

### Colors not showing on Windows?
Install colorama:
```bash
pip install colorama
```

### Too much output in console?
Comment out specific loggers you don't need:
```python
# log_search_distances(query, results)  # DISABLED
log_fallback_trigger('greeting', query)  # ENABLED
```

### Want to save logs to file?
Add file handler in settings.py:
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'chatbot_debug.log',
        },
    },
    'loggers': {
        'chatbot': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

---

## SUMMARY

**What you get:**
- ✅ Every query logged with timestamp
- ✅ Color-coded search distances (green/yellow/red)
- ✅ Fallback triggers clearly marked
- ✅ Exact RAG prompts shown (debug Gemini input)
- ✅ Cache hit/miss tracking
- ✅ Response time monitoring
- ✅ Error tracking with context

**Production recommendation:**
- Keep middleware for monitoring
- Configure file logging instead of console
- Set log level to WARNING or ERROR (not DEBUG)
