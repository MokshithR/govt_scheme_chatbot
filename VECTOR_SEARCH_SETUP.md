# Vector Search Setup Guide

## 🚀 Quick Start: pgvector + Gemini Semantic Search

This guide walks you through setting up semantic search for government schemes using PostgreSQL pgvector, Gemini embeddings, and LLM reranking.

---

## 📋 Prerequisites

1. **PostgreSQL 12+** installed and running
2. **Redis** installed and running (for caching)
3. **Gemini API Key** from Google AI Studio
4. Python 3.10+

---

## 🔧 Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `psycopg2-binary` - PostgreSQL adapter
- `pgvector` - Vector extension Python client
- `redis` - Redis client
- `django-redis` - Django Redis cache backend
- `google-generativeai` - Gemini API client

---

### 2. Enable pgvector Extension in PostgreSQL

Connect to your PostgreSQL database:

```bash
psql -U your_username -d your_database
```

Run the following SQL:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Expected output:**
```
 extname | extversion | ...
---------+------------+-----
 vector  | 0.5.1      | ...
```

---

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# PostgreSQL (required)
POSTGRES_DB=govt_chatbot
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Gemini API (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Redis (optional, defaults to localhost:6379)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
```

**Get Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Create new API key
3. Copy and paste into `.env`

---

### 4. Run Database Migrations

Apply the pgvector migration:

```powershell
python manage.py migrate chatbot 0002_add_pgvector_embedding
```

**What this does:**
- Enables `vector` extension
- Adds `embedding vector(768)` column to `chatbot_governmentscheme` table
- Creates IVFFlat index for fast similarity search

**Verify migration:**

```sql
-- Check column exists
\d chatbot_governmentscheme

-- Should show:
-- embedding | vector(768) | 
```

---

### 5. Generate Embeddings for Existing Schemes

Run the management command to generate embeddings:

```powershell
# Generate embeddings for all schemes (batch processing)
python manage.py generate_embeddings --batch-size 10

# Generate for a specific scheme
python manage.py generate_embeddings --scheme-id 123

# Update existing embeddings (re-generate all)
python manage.py generate_embeddings --update-existing
```

**Expected output:**
```
Processing 150 schemes without embeddings...

  ✓ Scheme 1: "PM-KISAN: Direct Income Support..." - Embedding generated
  ✓ Scheme 2: "Ayushman Bharat - Health Insurance..." - Embedding generated
  ...

Waiting 2 seconds before next batch...

=========================================================
✓ Successfully processed: 150 schemes
✗ Errors: 0 schemes
=========================================================

Embeddings generated! You can now use vector search API.
```

**Troubleshooting:**
- **Rate limit errors:** Increase `--batch-size` wait time (edit `generate_embeddings.py` line 134)
- **API key errors:** Verify `GEMINI_API_KEY` is set correctly
- **Dimension errors:** Gemini always returns 768; check if migration ran correctly

---

### 6. Start Redis (if not running)

**Windows:**
```powershell
# Download Redis for Windows: https://github.com/microsoftarchive/redis/releases
redis-server.exe
```

**Linux/Mac:**
```bash
redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### 7. Test the API

Start Django dev server:

```powershell
python manage.py runserver
```

**Test vector search endpoint:**

```bash
curl -X POST http://127.0.0.1:8000/api/vector-search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "schemes for farmers",
    "top_k": 5,
    "use_llm": true
  }'
```

**Expected response:**
```json
{
  "success": true,
  "answer": "PM-KISAN provides ₹6000/year to small and marginal farmers...",
  "schemes": [
    {
      "id": 1,
      "title": "PM-KISAN",
      "similarity_score": 0.89,
      "sector": "Agriculture",
      ...
    }
  ],
  "query": "schemes for farmers",
  "top_k": 5
}
```

---

## 📚 API Usage

### Endpoint: `/api/vector-search/`

**Method:** POST

**Request Body:**
```json
{
  "query": "health insurance for poor families",
  "top_k": 5,                    // optional, default 5 (max 20)
  "sector": "Health",             // optional filter
  "government_level": "central",  // optional: central/state/local
  "use_llm": true,                // optional, default true
  "llm_model": "gemini-1.5-flash" // optional: flash (fast) or pro (accurate)
}
```

**Response:**
```json
{
  "success": true,
  "answer": "LLM-generated answer with scheme details",
  "schemes": [...],  // Top-K most similar schemes
  "query": "...",
  "top_k": 5
}
```

**Example queries:**
- `"schemes for women entrepreneurs"`
- `"health insurance for senior citizens"`
- `"education loans for students"`
- `"farming subsidies in Karnataka"`

---

## 🧪 Running Tests

Run all vector search tests:

```powershell
python manage.py test chatbot.tests.test_vector_search
```

**Test coverage:**
- Embedding generation
- Vector similarity search
- LLM response generation
- API endpoint validation
- Prompt template formatting

---

## 🔍 SQL Queries for Debugging

### Check embeddings count:
```sql
SELECT 
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
    COUNT(*) as total
FROM chatbot_governmentscheme;
```

### Manual similarity search (cosine distance):
```sql
SELECT 
    id,
    title,
    sector_id,
    1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM chatbot_governmentscheme
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

### Check index status:
```sql
SELECT * FROM pg_indexes 
WHERE tablename = 'chatbot_governmentscheme' 
AND indexname LIKE '%embedding%';
```

---

## ⚙️ Configuration Options

### Adjust cache TTL (time-to-live):

Edit `chatbot/vector_search.py`:

```python
class VectorSearchService:
    def __init__(self):
        self.cache_ttl = 3600         # LLM responses (1 hour)
        self.embedding_cache_ttl = 86400  # Query embeddings (24 hours)
```

### Change vector index settings:

Edit migration `0002_add_pgvector_embedding.py`:

```python
# IVFFlat index parameters
# lists: number of clusters (higher = more accuracy, slower build)
# Recommended: sqrt(total_rows) for lists parameter
CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on dataset size
```

### Switch LLM model:

- **Fast responses:** `gemini-1.5-flash` (default)
- **Higher accuracy:** `gemini-1.5-pro`

Set in API request:
```json
{
  "query": "...",
  "llm_model": "gemini-1.5-pro"
}
```

---

## 🚨 Troubleshooting

### 1. `CREATE EXTENSION vector` fails
**Error:** `extension "vector" is not available`

**Solution:**
Install pgvector extension on your PostgreSQL server:
- Ubuntu: `sudo apt install postgresql-15-pgvector`
- macOS (Homebrew): `brew install pgvector`
- Windows: Download from https://github.com/pgvector/pgvector/releases

### 2. Embedding generation fails with API error
**Error:** `google.generativeai.types.BlockedPromptException`

**Solution:**
Some scheme descriptions may trigger content filters. Skip those schemes:
```powershell
python manage.py generate_embeddings --batch-size 1
```
(Smaller batches help identify problematic schemes)

### 3. Redis connection refused
**Error:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution:**
Start Redis server or disable caching temporarily:

In `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### 4. Slow vector search queries
**Solutions:**
- Rebuild index with more lists: `CREATE INDEX ... WITH (lists = 200);`
- Use HNSW index instead of IVFFlat (PostgreSQL 15+):
  ```sql
  CREATE INDEX ON chatbot_governmentscheme 
  USING hnsw (embedding vector_cosine_ops);
  ```
- Reduce `top_k` in API requests

---

## 📊 Performance Benchmarks

Typical performance (on moderate hardware):

| Operation                  | Time      |
|----------------------------|-----------|
| Generate single embedding  | ~200ms    |
| Vector search (1M schemes) | ~50ms     |
| LLM reranking (flash)      | ~800ms    |
| LLM reranking (pro)        | ~2000ms   |
| Full pipeline (with cache) | ~100ms    |

**Optimization tips:**
- Use `gemini-1.5-flash` for faster responses
- Enable Redis caching (reduces repeat queries to ~10ms)
- Generate embeddings in batches during off-peak hours

---

## 🎯 Next Steps

1. **Add more schemes:** Run web scraper or bulk import
2. **Regenerate embeddings:** After adding new schemes
3. **Integrate with voice:** Connect vector search to voice API
4. **Monitor usage:** Add analytics to track popular queries
5. **Fine-tune prompts:** Customize `chatbot/prompts.py` for your use case

---

## 📞 Support

For issues or questions:
- Check Django logs: `python manage.py runserver --verbosity 2`
- Enable debug logging in `settings.py`: `DEBUG = True`
- Review test failures: `python manage.py test chatbot.tests.test_vector_search -v 2`

---

## 🔐 Security Notes

1. **Never commit `.env` file** - contains API keys
2. **Rate limit API endpoint** - add throttling in production
3. **Validate user input** - prevent SQL injection (already handled by Django ORM)
4. **Rotate API keys** - regularly update `GEMINI_API_KEY`

---

**Setup complete! 🎉 Your semantic search is ready.**
