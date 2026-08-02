"""
Quick test script for vector search system.

Run this after setting up pgvector and generating embeddings to verify everything works.

Usage: python test_vector_search_quick.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.vector_search import get_vector_search_service
from chatbot.models import GovernmentScheme
from django.db import connection


def test_pgvector_installed():
    """Check if pgvector extension is enabled."""
    print("1. Testing pgvector extension...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            if result:
                print("   ✓ pgvector extension is installed")
                return True
            else:
                print("   ✗ pgvector extension NOT found")
                print("   Run: CREATE EXTENSION vector; in PostgreSQL")
                return False
    except Exception as e:
        print(f"   ✗ Error checking pgvector: {e}")
        return False


def test_embedding_column():
    """Check if embedding column exists."""
    print("\n2. Testing embedding column...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'chatbot_governmentscheme' 
                AND column_name = 'embedding';
            """)
            result = cursor.fetchone()
            if result:
                print(f"   ✓ Embedding column exists (type: {result[1]})")
                return True
            else:
                print("   ✗ Embedding column NOT found")
                print("   Run: python manage.py migrate chatbot 0002_add_pgvector_embedding")
                return False
    except Exception as e:
        print(f"   ✗ Error checking column: {e}")
        return False


def test_embeddings_count():
    """Count schemes with embeddings."""
    print("\n3. Counting schemes with embeddings...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
                    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
                    COUNT(*) as total
                FROM chatbot_governmentscheme;
            """)
            row = cursor.fetchone()
            with_emb, without_emb, total = row
            
            print(f"   Total schemes: {total}")
            print(f"   With embeddings: {with_emb}")
            print(f"   Without embeddings: {without_emb}")
            
            if with_emb > 0:
                print(f"   ✓ Found {with_emb} schemes with embeddings")
                return True
            else:
                print("   ✗ No embeddings found")
                print("   Run: python manage.py generate_embeddings")
                return False
    except Exception as e:
        print(f"   ✗ Error counting embeddings: {e}")
        return False


def test_gemini_api():
    """Test Gemini API connection."""
    print("\n4. Testing Gemini API connection...")
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("   ✗ GEMINI_API_KEY not set in environment")
        print("   Add to .env file: GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"   API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Test embedding generation
        result = genai.embed_content(
            model="models/embedding-001",
            content="test query",
            task_type="retrieval_query",
        )
        
        if len(result['embedding']) == 768:
            print("   ✓ Gemini API connection successful")
            return True
        else:
            print(f"   ✗ Invalid embedding dimension: {len(result['embedding'])}")
            return False
            
    except Exception as e:
        print(f"   ✗ Gemini API error: {e}")
        return False


def test_vector_search():
    """Test actual vector search."""
    print("\n5. Testing vector search...")
    
    try:
        service = get_vector_search_service()
        result = service.search(
            query="schemes for farmers",
            top_k=3,
            use_llm_reranking=False,  # Skip LLM for speed
        )
        
        if result['schemes']:
            print(f"   ✓ Found {len(result['schemes'])} schemes")
            print(f"   Top result: {result['schemes'][0]['title']}")
            print(f"   Similarity: {result['schemes'][0]['similarity_score']:.2%}")
            return True
        else:
            print("   ✗ No schemes found in vector search")
            return False
            
    except Exception as e:
        print(f"   ✗ Vector search error: {e}")
        return False


def test_llm_reranking():
    """Test LLM response generation."""
    print("\n6. Testing LLM reranking...")
    
    try:
        service = get_vector_search_service()
        result = service.search(
            query="health schemes for senior citizens",
            top_k=3,
            use_llm_reranking=True,
            llm_model="gemini-1.5-flash",
        )
        
        if result['answer']:
            print(f"   ✓ LLM generated answer")
            print(f"   Preview: {result['answer'][:100]}...")
            return True
        else:
            print("   ✗ No LLM answer generated")
            return False
            
    except Exception as e:
        print(f"   ✗ LLM error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Vector Search System - Quick Test")
    print("=" * 70)
    
    tests = [
        test_pgvector_installed,
        test_embedding_column,
        test_embeddings_count,
        test_gemini_api,
        test_vector_search,
        test_llm_reranking,
    ]
    
    results = []
    for test in tests:
        try:
            passed = test()
            results.append(passed)
        except Exception as e:
            print(f"   ✗ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Vector search is ready to use.")
        print("\nTry the API:")
        print("  curl -X POST http://127.0.0.1:8000/api/vector-search/ \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"query": "schemes for farmers", "top_k": 5}\'')
    else:
        print("✗ Some tests failed. Check the output above for details.")
        print("\nCommon fixes:")
        print("  1. Run: python manage.py migrate chatbot 0002_add_pgvector_embedding")
        print("  2. Run: python manage.py generate_embeddings")
        print("  3. Check .env file has GEMINI_API_KEY")
        print("  4. Ensure PostgreSQL + pgvector are installed")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
