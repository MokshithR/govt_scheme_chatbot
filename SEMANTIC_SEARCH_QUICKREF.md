# Semantic Search & RAG - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1. Set Environment Variable
```bash
# In .env file
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Generate Embeddings
```powershell
python manage.py generate_embeddings
```

### 3. Test APIs
```powershell
# Semantic Search
curl -X POST http://localhost:8000/api/semantic-search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "farming schemes"}'

# Smart Answer
curl -X POST http://localhost:8000/api/smart-answer/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What schemes help small farmers?"}'
```

## 📡 API Endpoints

### `/api/semantic-search/` (POST)
Find schemes by semantic similarity

**Request:**
```json
{
  "query": "education loan",
  "top_k": 5,
  "is_active": true
}
```

**Response:** List of schemes with similarity scores

---

### `/api/smart-answer/` (POST)
Get intelligent answers using RAG

**Request:**
```json
{
  "query": "How to apply for health insurance?",
  "model": "gemini-1.5-flash",
  "top_k": 5
}
```

**Response:** Natural language answer + source schemes

## 🔧 Management Commands

```powershell
# Generate all missing embeddings
python manage.py generate_embeddings

# Force regenerate all
python manage.py generate_embeddings --force

# Generate for specific scheme
python manage.py generate_embeddings --scheme-id 42

# Custom batch size and delay
python manage.py generate_embeddings --batch-size 10 --delay 2.0
```

## 📊 Key Files

| File | Purpose |
|------|---------|
| `chatbot/embedding_utils.py` | Text cleaning + embedding generation |
| `chatbot/vector_search.py` | pgvector similarity search + caching |
| `chatbot/serializers.py` | DRF serializers for APIs |
| `chatbot/prompts.py` | System prompts for Gemini LLM |
| `chatbot/views.py` | API view functions |
| `chatbot/urls.py` | URL routing |
| `chatbot/management/commands/generate_embeddings.py` | Embedding command |

## 🎛️ Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key

# Optional (with defaults)
GCP_MODEL=gemini-1.5-flash    # or gemini-1.5-pro
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
```

## 🔍 Database Queries

```sql
-- Check embedding status
SELECT 
    COUNT(*) as total,
    COUNT(embedding) as with_embeddings,
    COUNT(*) - COUNT(embedding) as without_embeddings
FROM scheme;

-- View a single embedding
SELECT id, title, embedding FROM scheme WHERE id = 1;

-- Test vector search manually
SELECT 
    title, 
    (embedding <-> '[0.1, 0.2, ...]'::vector) AS distance
FROM scheme
WHERE embedding IS NOT NULL
ORDER BY distance
LIMIT 5;
```

## 🚨 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY not configured` | Add to `.env` file |
| `429 Quota Exceeded` | Wait 24h or reduce batch size |
| `Invalid embedding dimension` | Check vector(768) column type |
| `Redis connection error` | Start Redis: `docker run -d -p 6379:6379 redis` |
| `No results from search` | Run `generate_embeddings` first |

## 📈 Performance Tips

- **Cache Hit:** ~10-50ms
- **Cold Search:** ~200-500ms  
- **Smart Answer (flash):** ~1-3 seconds
- **Smart Answer (pro):** ~3-7 seconds

**Optimization:**
1. Use Redis caching (enabled by default)
2. Choose `flash` for speed, `pro` for accuracy
3. Set appropriate `top_k` (3-10 recommended)

## 🎯 Example Usage (Python)

```python
import requests

# Semantic Search
response = requests.post(
    'http://localhost:8000/api/semantic-search/',
    json={'query': 'startup funding', 'top_k': 5}
)
results = response.json()['results']

# Smart Answer
response = requests.post(
    'http://localhost:8000/api/smart-answer/',
    json={
        'query': 'What schemes help women entrepreneurs?',
        'model': 'gemini-1.5-flash'
    }
)
answer = response.json()['answer']
print(answer)
```

## 📝 Response Fields

### Semantic Search Result:
- `id` - Scheme ID
- `title` - Scheme name
- `short_description` - Brief summary
- `distance` - Cosine distance (lower = better)
- `similarity_score` - 0-1 scale (higher = better)
- `application_link` - URL to apply
- `website` - Official website

### Smart Answer Result:
- `answer` - Natural language response
- `schemes_used` - Source schemes with full details
- `schemes_count` - Number of schemes used
- `model_used` - Gemini model name
- `cached` - Whether from cache

## 🔐 Security Checklist

- ✅ API key in `.env` (not in code)
- ✅ `.env` in `.gitignore`
- ✅ Input validation via DRF serializers
- ✅ Parameterized SQL queries (no injection)
- ✅ Rate limiting (recommended for production)

## 📚 Documentation Links

- Full Guide: `SEMANTIC_SEARCH_SETUP.md`
- Gemini API: https://ai.google.dev
- pgvector: https://github.com/pgvector/pgvector
- DRF: https://www.django-rest-framework.org

---

**Questions? Issues? Check the full documentation in `SEMANTIC_SEARCH_SETUP.md`**
