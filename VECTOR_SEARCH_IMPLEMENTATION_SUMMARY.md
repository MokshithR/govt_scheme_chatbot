# Vector Search Implementation Summary

## ✅ All Tasks Completed

### TASK 1: Generate Embeddings Management Command
**File:** `chatbot/management/commands/generate_embeddings.py`

**Features:**
- Fetches all rows from the `scheme` table
- Generates Gemini embeddings using model `models/embedding-001`
- Embeds: title + description + eligibility_criteria + benefits + department + keywords
- Stores 768-dimensional vectors in `scheme.embedding` column
- Skips rows where embedding already exists (unless `--update-existing` flag used)
- Batch processing with configurable batch size (default: 10)
- Progress logging with success/error tracking
- Rate limiting (2s delay between batches)

**Usage:**
```bash
# Generate embeddings for all schemes without embeddings
python manage.py generate_embeddings

# Custom batch size
python manage.py generate_embeddings --batch-size 20

# Update existing embeddings
python manage.py generate_embeddings --update-existing

# Generate for specific scheme
python manage.py generate_embeddings --scheme-id 123
```

---

### TASK 2: Vector Search API Endpoint
**File:** `chatbot/views.py` (function: `vector_search_api`)
**URL:** `/api/search/` (primary) and `/api/vector-search/` (legacy)

**Features:**
1. **Query Embedding:** Generates embedding using Gemini `models/embedding-001`
2. **pgvector Search:** Executes SQL query:
   ```sql
   SELECT ... FROM scheme 
   WHERE embedding IS NOT NULL
   ORDER BY embedding <=> query_embedding::vector
   LIMIT 5
   ```
3. **LLM Reranking:** Uses `gemini-1.5-flash` or `gemini-1.5-pro` with:
   - System prompt enforcing zero-hallucination
   - Context from top retrieved schemes
   - Temperature = 0 (configured in Gemini model)
4. **Response Format:**
   ```json
   {
     "success": true,
     "answer": "LLM-generated answer with scheme details",
     "schemes": [...],
     "ssml": "<speak>answer in SSML format</speak>",
     "query": "user question",
     "top_k": 5
   }
   ```

**Special Behaviors:**
- If no schemes match → Returns: "No official scheme found for your request..."
- If user asks "What is your name?" → Responds: "I am YOJANAMITHRA, a Government Scheme Chatbot..."
- Handles greetings politely
- Only answers from supplied schemes (no hallucination)

**API Request Example:**
```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "schemes for farmers",
    "top_k": 5,
    "sector": "agriculture",
    "government_level": "central",
    "use_llm": true,
    "llm_model": "gemini-1.5-flash"
  }'
```

---

### TASK 3: Redis Caching
**File:** `chatbot/vector_search.py` (class: `VectorSearchService`)

**Caching Layers:**
1. **Query Embeddings Cache**
   - TTL: 12 hours
   - Key: `query_embedding:<md5_hash>`
   - Cached after first generation

2. **Vector Search Results Cache**
   - TTL: 12 hours
   - Key: `vector_search:<params_hash>`
   - Cached after database query

3. **LLM Response Cache**
   - TTL: 12 hours
   - Key: `llm_response:<query+context_hash>`
   - Cached after LLM generation

**Configuration:**
- Redis backend: `django_redis.cache.RedisCache`
- Compression: `zlib`
- Connection pool: 50 max connections
- All caches use MD5 hashing for keys

---

### TASK 4: Unit Tests
**File:** `chatbot/tests/test_vector_search.py`

**Test Cases:**
1. ✅ `test_generate_query_embedding` - Tests embedding generation
2. ✅ `test_generate_query_embedding_invalid_dimension` - Tests dimension validation
3. ✅ `test_generate_llm_response` - Tests LLM answer generation
4. ✅ `test_generate_llm_response_no_schemes` - Tests "No scheme found" response
5. ✅ `test_singleton_pattern` - Tests service singleton
6. ✅ `test_vector_search_api_success` - Tests API endpoint success
7. ✅ `test_search_api_endpoint` - Tests new `/api/search/` endpoint
8. ✅ `test_vector_search_api_missing_query` - Tests error handling
9. ✅ `test_vector_search_api_with_filters` - Tests sector/level filters
10. ✅ `test_system_prompt_contains_rules` - Tests prompt has YOJANAMITHRA name
11. ✅ `test_user_prompt_template_formatting` - Tests prompt formatting

**Run Tests:**
```bash
python manage.py test chatbot.tests.test_vector_search
```

---

## 🔧 Configuration Requirements

### Environment Variables (.env)
```env
POSTGRES_DB=govt_chatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
GEMINI_API_KEY=your_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
```

### Database Setup
```sql
-- Extension already created in Docker container
CREATE EXTENSION IF NOT EXISTS vector;

-- Embedding column already added
ALTER TABLE scheme ADD COLUMN embedding vector(768);

-- Index already created
CREATE INDEX scheme_embedding_idx ON scheme 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 🚀 Next Steps to Use the System

### Step 1: Generate Embeddings
```bash
python manage.py generate_embeddings --batch-size 10
```

### Step 2: Start Redis (if not running)
```bash
# Windows (if using Redis from Windows installer)
redis-server

# Docker
docker run -d --name redis -p 6379:6379 redis:latest
```

### Step 3: Test the API
```bash
# Test with curl
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What schemes are available for farmers?"}'

# Or use Python
import requests
response = requests.post('http://localhost:8000/api/search/', 
    json={'query': 'health insurance schemes'})
print(response.json())
```

---

## 📋 System Prompt (YOJANAMITHRA)

The AI assistant is configured to:
- Identify as "YOJANAMITHRA" when asked
- Only answer from official government schemes (zero hallucination)
- Handle greetings politely
- Return "No official scheme found" for non-scheme questions
- Keep answers short and actionable (scheme name, eligibility, benefits, how to apply)
- Use simple language suitable for all literacy levels

---

## 🎯 Key Features Implemented

✅ **Correct Table Name:** All queries use `scheme` table (not `chatbot_governmentscheme`)
✅ **768-Dimensional Embeddings:** Using Gemini `models/embedding-001`
✅ **pgvector Integration:** Cosine similarity search with IVFFlat index
✅ **Redis Caching:** 12-hour TTL for all layers
✅ **Zero-Hallucination:** System prompt enforces official-schemes-only responses
✅ **SSML Support:** All responses include `<speak>` tags for voice output
✅ **Temperature = 0:** Configured in Gemini for deterministic responses
✅ **Batch Processing:** Safe embedding generation with rate limiting
✅ **Comprehensive Tests:** 11 test cases covering all functionality
✅ **YOJANAMITHRA Identity:** Chatbot responds with its name when asked

---

## 📊 Performance Optimizations

- **Redis caching** reduces repeated API calls
- **Batch processing** respects Gemini rate limits
- **IVFFlat index** speeds up similarity search
- **Connection pooling** for Redis and PostgreSQL
- **Query result caching** prevents duplicate database queries

---

## 🐛 Troubleshooting

### If embeddings fail to generate:
1. Check `GEMINI_API_KEY` is set correctly
2. Verify `scheme` table exists in database
3. Ensure pgvector extension is installed
4. Check API quota limits

### If vector search returns errors:
1. Verify embeddings exist in database: `SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;`
2. Check index exists: `\di` in psql
3. Ensure Redis is running: `redis-cli ping`
4. Check logs for detailed error messages

---

**Implementation Date:** November 21, 2025
**Database:** PostgreSQL 16 with pgvector (Docker container)
**Status:** ✅ All 4 tasks completed and tested
