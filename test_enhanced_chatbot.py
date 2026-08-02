"""
Test script for enhanced chatbot with fuzzy matching and comprehensive responses
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot

# Test queries based on user requirements
test_queries = [
    # 1. Basic Info Query
    ("What is PM Kisan?", "Should return: Name, Eligibility, Benefits, Documents, How to Apply, Links"),
    
    # 2. Eligibility Query
    ("Who is eligible for Ayushman Bharat?", "Should return comprehensive eligibility criteria"),
    
    # 3. Documents Query
    ("Documents needed for PMAY?", "Should list all required documents"),
    
    # 4. Application Process Query
    ("How to apply for scholarships?", "Should provide step-by-step application process"),
    
    # 5. Benefits Query
    ("What are the benefits of MNREGA?", "Should list all scheme benefits"),
    
    # 6. Category Search
    ("Show me schemes for farmers", "Should return all agriculture/farmer schemes"),
    
    # 7. Location-based Query
    ("Schemes available in Karnataka", "Should filter schemes by state/location"),
    
    # 8. Fuzzy Matching Test (with typo)
    ("prdhaan manthri awaas yojna", "Should correct to 'Pradhan Mantri Awas Yojana'"),
    
    # 9. Voice-style Query
    ("Tell me about student scholarships", "Natural language query"),
    
    # 10. Amount Query
    ("How much money in Jan Dhan Yojana?", "Should return financial benefit details"),
]

def test_chatbot():
    print("=" * 80)
    print("ENHANCED CHATBOT TEST - 10 Query Types")
    print("=" * 80)
    
    for i, (query, expected) in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}/10: {query}")
        print(f"Expected: {expected}")
        print("-" * 80)
        
        # Test in English
        response = chatbot(query, language='en')
        
        print("Response:")
        print(response)
        
        # Check if response contains key elements
        has_name = "**" in response  # Scheme name in bold
        has_structure = any(emoji in response for emoji in ["📋", "✅", "💰", "📄", "📝", "🔗"])
        
        print("\nResponse Quality Check:")
        print(f"  ✓ Has scheme name: {has_name}")
        print(f"  ✓ Has structured format: {has_structure}")
        print(f"  ✓ Response length: {len(response)} chars")
        
        if i < len(test_queries):
            input("\nPress Enter for next test...")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_chatbot()
