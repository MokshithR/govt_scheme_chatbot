"""
Example: Using the Vector Search API

This script demonstrates how to use the semantic search API endpoint.
"""

import requests
import json

# API endpoint (update if your server runs on different port)
API_URL = "http://127.0.0.1:8000/api/vector-search/"


def search_schemes(query, top_k=5, sector=None, government_level=None, use_llm=True):
    """
    Search for government schemes using semantic search.
    
    Args:
        query: User's natural language query
        top_k: Number of results to return (1-20)
        sector: Optional sector filter (e.g., 'Agriculture', 'Health')
        government_level: Optional filter ('central', 'state', 'local')
        use_llm: Whether to use Gemini LLM for answer generation
    
    Returns:
        API response as dict
    """
    payload = {
        "query": query,
        "top_k": top_k,
        "use_llm": use_llm,
    }
    
    if sector:
        payload["sector"] = sector
    
    if government_level:
        payload["government_level"] = government_level
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None


def main():
    """Run example searches."""
    
    print("=" * 70)
    print("Vector Search API Examples")
    print("=" * 70)
    
    # Example 1: Simple search
    print("\n1. Simple search: 'schemes for farmers'")
    print("-" * 70)
    result = search_schemes("schemes for farmers", top_k=3)
    
    if result and result.get('success'):
        print(f"\nLLM Answer:\n{result['answer']}\n")
        print(f"Found {len(result['schemes'])} schemes:")
        for i, scheme in enumerate(result['schemes'], 1):
            print(f"\n  {i}. {scheme['title']}")
            print(f"     Similarity: {scheme['similarity_score']:.2%}")
            print(f"     Sector: {scheme.get('sector', 'N/A')}")
            print(f"     Website: {scheme.get('website', 'N/A')}")
    else:
        print("Search failed!")
    
    # Example 2: Search with filters
    print("\n\n2. Filtered search: Health sector, Central government")
    print("-" * 70)
    result = search_schemes(
        query="health insurance for poor families",
        top_k=3,
        sector="Health",
        government_level="central"
    )
    
    if result and result.get('success'):
        print(f"\nLLM Answer:\n{result['answer']}\n")
        print(f"Found {len(result['schemes'])} schemes in Health sector (Central)")
    
    # Example 3: Search without LLM (just vector retrieval)
    print("\n\n3. Vector search only (no LLM reranking)")
    print("-" * 70)
    result = search_schemes(
        query="education loans for students",
        top_k=5,
        use_llm=False
    )
    
    if result and result.get('success'):
        print(f"Found {len(result['schemes'])} schemes (raw vector search):")
        for i, scheme in enumerate(result['schemes'], 1):
            print(f"\n  {i}. {scheme['title']} (score: {scheme['similarity_score']:.2%})")
    
    # Example 4: Search with different LLM model
    print("\n\n4. Using Gemini Pro (more accurate, slower)")
    print("-" * 70)
    
    payload = {
        "query": "schemes for women entrepreneurs",
        "top_k": 3,
        "use_llm": True,
        "llm_model": "gemini-1.5-pro"  # Switch to Pro model
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        if response.ok:
            result = response.json()
            print(f"\nPro Model Answer:\n{result['answer']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
