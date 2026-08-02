#!/usr/bin/env python
"""
Test connection to Docker PostgreSQL and verify pgvector extension.

This script confirms that:
1. Python can connect to PostgreSQL on localhost:5432
2. The database name is 'govt_schemes'
3. The pgvector extension is installed
4. The 'scheme' table exists with embedding column
5. Vector index exists

Run with: python test_docker_postgres_connection.py
"""

import sys
import os

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"⚠️  Warning: Could not setup Django: {e}")
    print("Trying direct psycopg2 connection instead...\n")

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection parameters from .env
DB_NAME = os.getenv('POSTGRES_DB', 'govt_schemes')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', '127.0.0.1')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

print("=" * 70)
print("DOCKER POSTGRESQL CONNECTION TEST")
print("=" * 70)
print()

print("Configuration:")
print(f"  Database: {DB_NAME}")
print(f"  User:     {DB_USER}")
print(f"  Host:     {DB_HOST}")
print(f"  Port:     {DB_PORT}")
print(f"  Password: {'*' * len(DB_PASSWORD)}")
print()

# Test 1: Connect to PostgreSQL
print("Test 1: Connecting to PostgreSQL...")
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("  ✓ Connection successful!")
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print()
    print("TROUBLESHOOTING:")
    print("1. Check if Docker container is running: docker ps | findstr pgvector")
    print("2. Check if Windows PostgreSQL is stopped: Get-Service postgresql-x64-18")
    print("3. Verify port 5432 is free: netstat -ano | findstr :5432")
    sys.exit(1)

# Test 2: Get PostgreSQL version
print()
print("Test 2: PostgreSQL version...")
try:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    # Extract version number
    if 'PostgreSQL' in version:
        version_short = version.split('PostgreSQL ')[1].split(' ')[0]
        print(f"  ✓ PostgreSQL {version_short}")
    else:
        print(f"  ✓ {version[:80]}...")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 3: Check database name
print()
print("Test 3: Current database...")
try:
    cursor.execute("SELECT current_database();")
    current_db = cursor.fetchone()[0]
    if current_db == 'govt_schemes':
        print(f"  ✓ Connected to: {current_db}")
    else:
        print(f"  ⚠️  WARNING: Expected 'govt_schemes', got '{current_db}'")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 4: Check for pgvector extension
print()
print("Test 4: Checking pgvector extension...")
try:
    cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname='vector';")
    result = cursor.fetchone()
    if result:
        print(f"  ✓ pgvector extension installed (version {result[1]})")
    else:
        print("  ✗ pgvector extension NOT FOUND!")
        print("  This means you're connected to the WRONG database!")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 5: List all extensions
print()
print("Test 5: All installed extensions...")
try:
    cursor.execute("SELECT extname FROM pg_extension ORDER BY extname;")
    extensions = [row[0] for row in cursor.fetchall()]
    print(f"  Extensions: {', '.join(extensions)}")
    
    # Verify we have the expected extensions for Docker PostgreSQL
    if 'vector' in extensions:
        print("  ✓ This is the Docker PostgreSQL database (has pgvector)")
    elif 'pg_trgm' in extensions and 'vector' not in extensions:
        print("  ✗ WARNING: This looks like Windows PostgreSQL (no pgvector)!")
    else:
        print("  ⚠️  Unable to determine database source")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 6: Check 'scheme' table exists
print()
print("Test 6: Checking 'scheme' table...")
try:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'scheme'
        );
    """)
    table_exists = cursor.fetchone()[0]
    if table_exists:
        print("  ✓ Table 'scheme' exists")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM scheme;")
        count = cursor.fetchone()[0]
        print(f"  ✓ Table has {count} schemes")
    else:
        print("  ✗ Table 'scheme' NOT FOUND!")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 7: Check embedding column
print()
print("Test 7: Checking 'embedding' column...")
try:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'scheme' AND column_name = 'embedding';
    """)
    result = cursor.fetchone()
    if result:
        print(f"  ✓ Column 'embedding' exists (type: {result[1]})")
        
        # Check how many schemes have embeddings
        cursor.execute("SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL;")
        embedded_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scheme;")
        total_count = cursor.fetchone()[0]
        
        print(f"  ✓ Embeddings: {embedded_count}/{total_count} schemes have embeddings")
        
        if embedded_count == 0:
            print("  ℹ️  No embeddings yet. Run: python manage.py generate_embeddings")
    else:
        print("  ✗ Column 'embedding' NOT FOUND!")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 8: Check vector index
print()
print("Test 8: Checking vector index...")
try:
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'scheme' AND indexname LIKE '%embedding%';
    """)
    indexes = cursor.fetchall()
    if indexes:
        for idx_name, idx_def in indexes:
            print(f"  ✓ Index: {idx_name}")
            if 'ivfflat' in idx_def.lower():
                print("    Type: IVFFlat (optimized for vector search)")
    else:
        print("  ⚠️  No vector index found (searches will be slower)")
        print("    Create with: CREATE INDEX scheme_embedding_idx ON scheme USING ivfflat (embedding vector_cosine_ops);")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Close connection
cursor.close()
conn.close()

print()
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)

# Final verdict
try:
    # Reconnect for final check
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cursor = conn.cursor()
    cursor.execute("SELECT extname FROM pg_extension WHERE extname='vector';")
    has_pgvector = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    if has_pgvector:
        print("✓ SUCCESS: Connected to Docker PostgreSQL with pgvector!")
        print()
        print("NEXT STEPS:")
        print("1. Run migrations:           python manage.py migrate")
        print("2. Generate embeddings:      python manage.py generate_embeddings --batch-size 10")
        print("3. Start Django server:      python manage.py runserver")
        print("4. Test API:                 POST to http://localhost:8000/api/search/")
    else:
        print("✗ FAILURE: Connected to database WITHOUT pgvector!")
        print("You are likely still connected to Windows PostgreSQL.")
        print()
        print("TROUBLESHOOTING:")
        print("1. Stop Windows PostgreSQL:  Run stop_windows_postgres.ps1 as Administrator")
        print("2. Restart Docker container: docker restart pgvector")
        print("3. Re-run this test:         python test_docker_postgres_connection.py")
except:
    pass

print("=" * 70)
