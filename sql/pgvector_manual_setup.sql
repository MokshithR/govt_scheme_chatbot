"""
SQL commands for manual pgvector setup (if migration fails).

Use these commands if you need to set up pgvector manually in PostgreSQL.
"""

-- ============================================================================
-- Step 1: Enable pgvector Extension
-- ============================================================================

-- Enable the vector extension (requires superuser or CREATE EXTENSION privilege)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
-- Expected output: extname | extversion | ...
--                  vector  | 0.5.1      | ...


-- ============================================================================
-- Step 2: Add Embedding Column to GovernmentScheme Table
-- ============================================================================

-- Add vector column (768 dimensions for Gemini embeddings)
ALTER TABLE chatbot_governmentscheme 
ADD COLUMN IF NOT EXISTS embedding vector(768);

-- Verify column exists
\d chatbot_governmentscheme
-- Should show: embedding | vector(768) | 


-- ============================================================================
-- Step 3: Create Index for Fast Similarity Search
-- ============================================================================

-- Option A: IVFFlat index (faster build, good for < 1M rows)
CREATE INDEX IF NOT EXISTS chatbot_governmentscheme_embedding_idx 
ON chatbot_governmentscheme 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Option B: HNSW index (slower build, better for > 1M rows, requires PostgreSQL 15+)
-- CREATE INDEX IF NOT EXISTS chatbot_governmentscheme_embedding_idx 
-- ON chatbot_governmentscheme 
-- USING hnsw (embedding vector_cosine_ops);

-- Verify index exists
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'chatbot_governmentscheme' 
AND indexname LIKE '%embedding%';


-- ============================================================================
-- Step 4: Test Vector Operations
-- ============================================================================

-- Count schemes with/without embeddings
SELECT 
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
    COUNT(*) as total
FROM chatbot_governmentscheme;


-- Test similarity search (replace [...] with actual 768-dimensional vector)
-- Example: Find top 5 most similar schemes to a query embedding
SELECT 
    id,
    title,
    sector_id,
    1 - (embedding <=> '[0.1, 0.2, 0.3, ...]'::vector) as similarity_score
FROM chatbot_governmentscheme
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, 0.3, ...]'::vector
LIMIT 5;


-- ============================================================================
-- Step 5: Performance Tuning (Optional)
-- ============================================================================

-- Analyze table to update statistics (helps query planner)
ANALYZE chatbot_governmentscheme;

-- Adjust IVFFlat lists parameter based on dataset size
-- Rule of thumb: lists ≈ sqrt(total_rows)
-- For 10,000 rows: lists = 100
-- For 100,000 rows: lists = 316
-- For 1,000,000 rows: lists = 1000

-- Rebuild index with different lists parameter:
DROP INDEX IF EXISTS chatbot_governmentscheme_embedding_idx;
CREATE INDEX chatbot_governmentscheme_embedding_idx 
ON chatbot_governmentscheme 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 316);  -- Adjust based on your data size


-- ============================================================================
-- Step 6: Backup and Cleanup (Optional)
-- ============================================================================

-- Backup embeddings to a separate table (before regenerating)
CREATE TABLE chatbot_governmentscheme_embeddings_backup AS
SELECT id, embedding, last_updated
FROM chatbot_governmentscheme
WHERE embedding IS NOT NULL;

-- Clear all embeddings (to regenerate)
-- UPDATE chatbot_governmentscheme SET embedding = NULL;

-- Drop index (before bulk updates to speed up inserts)
-- DROP INDEX IF EXISTS chatbot_governmentscheme_embedding_idx;

-- Recreate index after bulk updates
-- (See Step 3 above)


-- ============================================================================
-- Common Queries
-- ============================================================================

-- Get embedding dimension for a specific row
SELECT id, title, vector_dims(embedding) as dimension
FROM chatbot_governmentscheme
WHERE id = 1;

-- Find schemes with NULL embeddings
SELECT id, title, sector_id
FROM chatbot_governmentscheme
WHERE embedding IS NULL
LIMIT 10;

-- Calculate average similarity between all pairs (expensive!)
-- SELECT AVG(1 - (a.embedding <=> b.embedding)) as avg_similarity
-- FROM chatbot_governmentscheme a, chatbot_governmentscheme b
-- WHERE a.id < b.id AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL
-- LIMIT 1000;


-- ============================================================================
-- Troubleshooting
-- ============================================================================

-- Check if pgvector is installed correctly
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Check PostgreSQL version (pgvector requires 12+)
SELECT version();

-- Check table size and index size
SELECT 
    pg_size_pretty(pg_total_relation_size('chatbot_governmentscheme')) as total_size,
    pg_size_pretty(pg_relation_size('chatbot_governmentscheme')) as table_size,
    pg_size_pretty(pg_indexes_size('chatbot_governmentscheme')) as indexes_size;

-- Reindex (if index is corrupted)
-- REINDEX INDEX chatbot_governmentscheme_embedding_idx;


-- ============================================================================
-- End of Manual Setup Commands
-- ============================================================================
