"""
Test script for HuggingFace-based Semantic Search and Smart Answer APIs

This script demonstrates how to use the new API endpoints:
- /api/semantic-search-v2/ - Vector similarity search
- /api/smart-answer-v2/ - RAG with Gemini LLM

Requirements:
1. Django server must be running: python manage.py runserver
2. Embeddings must be generated: python manage.py generate_embeddings
3. Redis must be running (for caching)
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/chatbot"

def test_semantic_search(query):
    """Test the semantic search endpoint"""
    print(f"\n{'='*60}")
    print(f"TESTING SEMANTIC SEARCH")
    print(f"{'='*60}")
    print(f"Query: {query}")
    
    url = f"{BASE_URL}/api/semantic-search-v2/"
    payload = {"query": query}
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} results:")
        for i, result in enumerate(data['results'], 1):
            print(f"\n  {i}. {result['title']}")
            print(f"     Similarity: {result['similarity_score']:.1f}%")
            print(f"     Distance: {result['distance']:.3f}")
            print(f"     Description: {result['short_description'][:100]}...")
    else:
        print(f"Error: {response.json()}")


def test_smart_answer(query):
    """Test the smart answer endpoint"""
    print(f"\n{'='*60}")
    print(f"TESTING SMART ANSWER (RAG)")
    print(f"{'='*60}")
    print(f"Query: {query}")
    
    url = f"{BASE_URL}/api/smart-answer-v2/"
    payload = {"query": query}
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nSchemes Used: {', '.join(data['schemes_used']) if data['schemes_used'] else 'None'}")
        print(f"\nSSML Output:\n{data['ssml'][:200]}...")
    else:
        print(f"Error: {response.json()}")


if __name__ == "__main__":
    print("""
    HuggingFace Semantic Search + RAG Test Suite
    =============================================
    
    This script tests the new API endpoints that use:
    - sentence-transformers/all-mpnet-base-v2 for embeddings
    - PostgreSQL pgvector for similarity search  
    - Gemini 1.5 Flash for intelligent answers
    - Redis for caching (12-hour TTL)
    """)
    
    # Test 1: Greeting (should return greeting, not search schemes)
    print("\n\n--- TEST 1: Greeting Detection ---")
    test_smart_answer("hello")
    
    # Test 2: Casual greeting
    print("\n\n--- TEST 2: Another Greeting ---")
    test_smart_answer("good morning")
    
    # Test 3: Semantic search for farming schemes
    print("\n\n--- TEST 3: Semantic Search - Farming ---")
    test_semantic_search("farming schemes for small farmers")
    
    # Test 4: Smart answer for farming
    print("\n\n--- TEST 4: Smart Answer - Farming ---")
    test_smart_answer("What government schemes help small farmers?")
    
    # Test 5: Search for education schemes
    print("\n\n--- TEST 5: Semantic Search - Education ---")
    test_semantic_search("scholarship for students")
    
    # Test 6: Smart answer for students
    print("\n\n--- TEST 6: Smart Answer - Education ---")
    test_smart_answer("Are there any scholarships for college students?")
    
    # Test 7: No matches (should return fallback)
    print("\n\n--- TEST 7: No Good Matches (Fallback) ---")
    test_smart_answer("quantum computing research grants")
    
    # Test 8: Women empowerment
    print("\n\n--- TEST 8: Semantic Search - Women ---")
    test_semantic_search("schemes for women entrepreneurs")
    
    # Test 9: Health schemes
    print("\n\n--- TEST 9: Smart Answer - Healthcare ---")
    test_smart_answer("What health insurance schemes are available?")
    
    # Test 10: Empty query (should return error)
    print("\n\n--- TEST 10: Empty Query Error ---")
    test_semantic_search("")
    
    print(f"\n\n{'='*60}")
    print("TEST SUITE COMPLETE")
    print(f"{'='*60}\n")
