# Docker PostgreSQL Migration Validation Guide

This guide provides **step-by-step validation** after migrating from Windows PostgreSQL to Docker PostgreSQL.

---

## Prerequisites

Before starting validation:
- ✅ Windows PostgreSQL service stopped: `postgresql-x64-18`
- ✅ Docker PostgreSQL container running: `pgvector`
- ✅ `.env` updated with correct credentials (password: `postgres`)
- ✅ Connection test passed: `python test_docker_postgres_connection.py`

---

## Step 1: Run Django Migrations

Apply all Django migrations to the Docker PostgreSQL database:

```powershell
python manage.py migrate
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, chatbot, ...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

**✓ Success Criteria:**
- No error messages
- All migrations show `OK`
- No "relation does not exist" errors

**✗ If Migration Fails:**
```
django.db.utils.OperationalError: FATAL: password authentication failed
```
→ Check `.env` file: `POSTGRES_PASSWORD` should be `postgres`

```
django.db.utils.ProgrammingError: relation "scheme" does not exist
```
→ Your Docker database is empty. Restore the backup first (see below).

---

## Step 2: Verify Django Tables Created

Check that Django created its standard tables:

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "\dt"
```

**Expected Output:**
```
                   List of relations
 Schema |            Name            | Type  |  Owner   
--------+----------------------------+-------+----------
 public | auth_group                 | table | postgres
 public | auth_permission            | table | postgres
 public | django_content_type        | table | postgres
 public | django_migrations          | table | postgres
 public | django_session             | table | postgres
 public | scheme                     | table | postgres
 ...
```

**✓ Success Criteria:**
- `django_migrations` table exists
- `scheme` table exists
- Standard Django tables (auth, contenttypes, sessions) exist

---

## Step 3: Verify pgvector Extension

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
```

**Expected Output:**
```
 extname | extversion 
---------+------------
 vector  | 0.8.1
```

**✗ If pgvector Missing:**
```powershell
# Install pgvector extension
docker exec -it pgvector psql -U postgres -d govt_schemes -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Step 4: Check Scheme Table Structure

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "\d scheme"
```

**Expected Output:**
```
                                         Table "public.scheme"
      Column       |          Type          | Collation | Nullable |              Default               
-------------------+------------------------+-----------+----------+------------------------------------
 id                | integer                |           | not null | nextval('scheme_id_seq'::regclass)
 title             | character varying(500) |           | not null | 
 description       | text                   |           | not null | 
 eligibility       | text                   |           |          | 
 benefits          | text                   |           |          | 
 embedding         | vector(768)            |           |          | 
 ...
Indexes:
    "scheme_pkey" PRIMARY KEY, btree (id)
    "scheme_embedding_idx" ivfflat (embedding vector_cosine_ops)
```

**✓ Success Criteria:**
- `embedding` column has type `vector(768)`
- Index `scheme_embedding_idx` exists with `ivfflat` and `vector_cosine_ops`

**✗ If Embedding Column Missing:**
```sql
ALTER TABLE scheme ADD COLUMN embedding vector(768);
CREATE INDEX scheme_embedding_idx ON scheme USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## Step 5: Check Data Migration

Verify that your scheme data exists:

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "SELECT COUNT(*) FROM scheme;"
```

**Expected Output:**
```
 count 
-------
   156
```

**✗ If Count is 0:**
Your Docker database is empty. Restore from backup:

```powershell
# Option A: If you have a SQL dump file
docker exec -i pgvector psql -U postgres -d govt_schemes < backup.sql

# Option B: If data is still in Windows PostgreSQL
# 1. Export from Windows PostgreSQL
pg_dump -U postgres -h localhost -p 5432 govt_schemes > backup.sql

# 2. Import to Docker PostgreSQL
docker exec -i pgvector psql -U postgres -d govt_schemes < backup.sql
```

---

## Step 6: Generate Embeddings

Generate vector embeddings for all schemes (if not already done):

```powershell
python manage.py generate_embeddings --batch-size 10
```

**Expected Output:**
```
Generating embeddings for 156 schemes...
Processing batch 1/16...
Processing batch 2/16...
...
Successfully generated 156 embeddings!
```

**✓ Success Criteria:**
- No API errors
- All schemes processed
- Message shows total count matches database count

**✗ If Gemini API Error:**
```
google.api_core.exceptions.PermissionDenied: API key not valid
```
→ Check `.env` file: `GEMINI_API_KEY` must be set

---

## Step 7: Verify Embeddings Stored

Check that embeddings are actually in the database:

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;"
```

**Expected Output:**
```
 count 
-------
   156
```

**✓ Success Criteria:**
- Count matches total scheme count (all schemes have embeddings)

**✗ If Count is 0:**
- Re-run: `python manage.py generate_embeddings --batch-size 10`
- Check for errors in the output

---

## Step 8: Test Django Server

Start the Django development server:

```powershell
python manage.py runserver
```

**Expected Output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
January 15, 2025 - 14:30:00
Django version 5.2, using settings 'govt_voice_chatbot.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**✓ Success Criteria:**
- No database connection errors
- No migration warnings
- Server starts successfully

**✗ If Connection Error:**
```
django.db.utils.OperationalError: could not connect to server
```
→ Docker container not running: `docker start pgvector`

---

## Step 9: Test Vector Search API

Test the `/api/search/` endpoint:

```powershell
# Using curl (if installed)
curl -X POST http://localhost:8000/api/search/ -H "Content-Type: application/json" -d "{\"query\":\"farmer loan scheme\"}"

# Using PowerShell Invoke-WebRequest
$body = @{query = "farmer loan scheme"} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/search/ -Method POST -Body $body -ContentType "application/json"
```

**Expected Output (JSON):**
```json
{
  "results": [
    {
      "title": "PM-KISAN Scheme",
      "description": "Direct income support to farmers...",
      "similarity_score": 0.87,
      ...
    }
  ],
  "response": "Based on your query about farmer loan schemes, here are relevant options...",
  "ssml": "<speak>Based on your query about farmer loan schemes...</speak>"
}
```

**✓ Success Criteria:**
- HTTP 200 status
- `results` array contains schemes
- `response` text is relevant
- `ssml` field is present

**✗ If Empty Results:**
```json
{"results": [], "response": "No schemes found"}
```
→ Embeddings not generated: Run `python manage.py generate_embeddings`

**✗ If 500 Error:**
```
django.db.utils.ProgrammingError: operator does not exist: vector <=>
```
→ pgvector extension not installed: Run `CREATE EXTENSION vector;`

---

## Step 10: Run Unit Tests

Validate all functionality with automated tests:

```powershell
python manage.py test chatbot.tests.test_vector_search
```

**Expected Output:**
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...........
----------------------------------------------------------------------
Ran 11 tests in 15.234s

OK
Destroying test database for alias 'default'...
```

**✓ Success Criteria:**
- All tests pass (OK)
- No database errors
- No import errors

---

## Validation Checklist

Use this checklist to confirm complete migration:

- [ ] Windows PostgreSQL service stopped (`postgresql-x64-18`)
- [ ] Docker PostgreSQL container running (`docker ps | findstr pgvector`)
- [ ] Connection test passes (`python test_docker_postgres_connection.py`)
- [ ] Port 5432 only used by Docker (`netstat -ano | findstr :5432`)
- [ ] `.env` has correct credentials (password: `postgres`, database: `govt_schemes`)
- [ ] Django migrations applied (`python manage.py migrate`)
- [ ] pgvector extension installed (version 0.8.1)
- [ ] `scheme` table has `embedding` column (type `vector(768)`)
- [ ] Vector index exists (`scheme_embedding_idx` with IVFFlat)
- [ ] Scheme data migrated (count > 0)
- [ ] Embeddings generated (all schemes have embeddings)
- [ ] Django server starts without errors
- [ ] Vector search API returns results
- [ ] Unit tests pass

---

## Rollback Plan

If migration fails and you need to revert to Windows PostgreSQL:

```powershell
# 1. Stop Docker PostgreSQL
docker stop pgvector

# 2. Start Windows PostgreSQL
Start-Service postgresql-x64-18

# 3. Update .env
# Change:
#   POSTGRES_PASSWORD=postgres
# To:
#   POSTGRES_PASSWORD=mok123

# 4. Restart Django server
python manage.py runserver
```

**Note:** Rollback means losing pgvector functionality. Vector search will not work.

---

## Troubleshooting

### Problem: Django still connects to Windows PostgreSQL

**Symptoms:**
- `test_docker_postgres_connection.py` shows no pgvector extension
- Schemes exist but vector search fails

**Solution:**
```powershell
# Verify Windows service is stopped
Get-Service postgresql-x64-18

# If running, stop it
Stop-Service postgresql-x64-18 -Force

# Verify port 5432
netstat -ano | findstr :5432

# Should only show Docker process, not Windows PostgreSQL
```

### Problem: Port conflict (both PostgreSQL instances running)

**Symptoms:**
- `netstat` shows multiple processes on port 5432
- Connection test gives inconsistent results

**Solution A (Recommended):**
```powershell
# Stop Windows PostgreSQL permanently
.\stop_windows_postgres.ps1
```

**Solution B (Alternative):**
```powershell
# Change Docker port mapping
docker stop pgvector
docker rm pgvector
docker run -d --name pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:pg16

# Update .env
# Change POSTGRES_PORT=5432 to POSTGRES_PORT=5433
```

### Problem: No schemes in Docker database

**Symptoms:**
- `SELECT COUNT(*) FROM scheme;` returns 0
- API returns "No schemes found"

**Solution:**
```powershell
# Export from Windows PostgreSQL
pg_dump -U postgres -h localhost -p 5432 -t scheme govt_schemes > scheme_backup.sql

# Import to Docker PostgreSQL
docker exec -i pgvector psql -U postgres -d govt_schemes < scheme_backup.sql

# Verify
docker exec -it pgvector psql -U postgres -d govt_schemes -c "SELECT COUNT(*) FROM scheme;"
```

### Problem: Embeddings not persisting

**Symptoms:**
- `generate_embeddings` command succeeds but count is still 0
- Database shows NULL embeddings

**Solution:**
```powershell
# Check PostgreSQL logs
docker logs pgvector

# Verify database connection in Django
python manage.py dbshell
# In psql shell:
SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;

# If 0, manually test embedding update
UPDATE scheme SET embedding = ARRAY[0.1, 0.2, ...]::vector WHERE id = 1;
```

---

## Post-Migration Optimization

After successful migration, consider these optimizations:

### 1. Adjust Vector Index Parameters

```sql
-- Drop existing index
DROP INDEX IF EXISTS scheme_embedding_idx;

-- Recreate with optimized parameters for your dataset size
-- For 100-500 schemes: lists = 10
-- For 500-1000 schemes: lists = 50
-- For 1000+ schemes: lists = 100
CREATE INDEX scheme_embedding_idx ON scheme 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 50);
```

### 2. Analyze Table Statistics

```sql
-- Update PostgreSQL query planner statistics
ANALYZE scheme;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = 'scheme';
```

### 3. Monitor Performance

```python
# Add to settings.py for query logging
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Next Steps

After validation is complete:

1. **Update Documentation**: Document your production database credentials
2. **Backup Strategy**: Set up automated backups for Docker PostgreSQL
3. **Monitoring**: Add health checks for pgvector extension
4. **Performance Testing**: Load test with realistic query volumes
5. **Security Hardening**: Change default `postgres` password

---

**MIGRATION STATUS**: Use the checklist above to track your progress!
