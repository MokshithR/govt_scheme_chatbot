"""
Test script to verify Gemini API configuration and translation functionality
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.gemini_utils import configure_gemini, generate_text_with_gemini
import google.generativeai as genai
from django.conf import settings

def test_gemini_connection():
    """Test basic Gemini API connection"""
    print("=" * 60)
    print("TESTING GEMINI API CONNECTION")
    print("=" * 60)
    
    # Check API key
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("❌ GEMINI_API_KEY not found in settings")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    # Configure Gemini
    print("\n🔧 Configuring Gemini...")
    model = configure_gemini()
    
    if not model:
        print("❌ Failed to configure Gemini model")
        return False
    
    print(f"✅ Model configured successfully")
    
    # Test basic generation
    print("\n📝 Testing basic text generation...")
    try:
        response = model.generate_content("Say 'Hello from Gemini API!'")
        if response and response.text:
            print(f"✅ Response: {response.text}")
            return True
        else:
            print("❌ No text in response")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_translation():
    """Test translation functionality"""
    print("\n" + "=" * 60)
    print("TESTING TRANSLATION FUNCTIONALITY")
    print("=" * 60)
    
    model = configure_gemini()
    if not model:
        print("❌ Cannot test translation - model not configured")
        return False
    
    # Test English to Hindi
    print("\n🇮🇳 Testing English to Hindi translation...")
    try:
        prompt = "Translate the following text to Hindi (Devanagari script only, no Roman script): 'Available Government Schemes'"
        response = model.generate_content(prompt)
        if response and response.text:
            print(f"✅ Hindi: {response.text}")
        else:
            print("❌ No translation received")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test English to Kannada
    print("\n🇮🇳 Testing English to Kannada translation...")
    try:
        prompt = "Translate the following text to Kannada (Kannada script only): 'Available Government Schemes'"
        response = model.generate_content(prompt)
        if response and response.text:
            print(f"✅ Kannada: {response.text}")
        else:
            print("❌ No translation received")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_scheme_translation():
    """Test scheme object translation"""
    print("\n" + "=" * 60)
    print("TESTING SCHEME OBJECT TRANSLATION")
    print("=" * 60)
    
    model = configure_gemini()
    if not model:
        print("❌ Cannot test scheme translation - model not configured")
        return False
    
    # Sample scheme
    scheme = {
        'title': 'PM Surya Ghar Muft Bijli Yojana',
        'description': 'This scheme provides free electricity through rooftop solar installations for residential households.',
        'government_level': 'Central',
        'state': 'All India'
    }
    
    print("\n📋 Original Scheme:")
    print(f"   Title: {scheme['title']}")
    print(f"   Description: {scheme['description'][:60]}...")
    
    # Translate to Hindi
    print("\n🔄 Translating to Hindi...")
    try:
        prompt = f"""Translate this government scheme to Hindi (Devanagari script only).
Return only a JSON object with these exact keys: title, description, government_level, state

Scheme to translate:
{scheme}

Respond with valid JSON only."""
        
        response = model.generate_content(prompt)
        if response and response.text:
            print(f"✅ Translation received:")
            print(response.text[:200] + "...")
            return True
        else:
            print("❌ No translation received")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_available_models():
    """List all available Gemini models"""
    print("\n" + "=" * 60)
    print("LISTING AVAILABLE GEMINI MODELS")
    print("=" * 60)
    
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        print("\n📋 Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"   ✓ {m.name}")
                print(f"     Display Name: {m.display_name}")
                print(f"     Description: {m.description[:80]}...")
                print()
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    print("\n🚀 GEMINI API TEST SUITE\n")
    
    # Run all tests
    results = []
    
    results.append(("API Connection", test_gemini_connection()))
    results.append(("Translation", test_translation()))
    results.append(("Scheme Translation", test_scheme_translation()))
    
    # List available models
    list_available_models()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! Gemini API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
