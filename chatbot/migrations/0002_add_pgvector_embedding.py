"""
Migration to add pgvector extension and embedding column to GovernmentScheme model.

This migration:
1. Enables the pgvector extension in PostgreSQL
2. Adds a vector column (dimension=768) to store Gemini embeddings
3. Creates a GIN index for fast nearest-neighbor search

Run with: python manage.py migrate
"""

from django.db import migrations
from django.contrib.postgres.operations import CreateExtension


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),  # Update this to your actual last migration
    ]

    operations = [
        # Step 1: Enable pgvector extension
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector CASCADE;",
        ),
        
        # Step 2: Add embedding column (768 dimensions for Gemini embeddings)
        migrations.RunSQL(
            sql="""
                ALTER TABLE chatbot_governmentscheme 
                ADD COLUMN IF NOT EXISTS embedding vector(768);
            """,
            reverse_sql="""
                ALTER TABLE chatbot_governmentscheme 
                DROP COLUMN IF EXISTS embedding;
            """,
        ),
        
        # Step 3: Create index for fast similarity search using cosine distance
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS chatbot_governmentscheme_embedding_idx 
                ON chatbot_governmentscheme 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS chatbot_governmentscheme_embedding_idx;
            """,
        ),
    ]
