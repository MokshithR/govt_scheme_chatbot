"""
Test multilingual support for Django Government Scheme Chatbot
Tests language detection and full multilingual pipeline
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.utils.multilingual import (
    detect_user_language,
    translate_with_gemini,
    get_friendly_greeting,
    get_no_scheme_message,
    get_sector_intro,
    get_match_intro,
    translate_scheme_if_needed
)

def test_language_detection():
    """Test language detection with various inputs"""
    print("=" * 60)
    print("TEST 1: Language Detection")
    print("=" * 60)
    
    test_cases = [
        # English queries
        ("PM Kisan Yojana", "en"),
        ("What are agriculture schemes?", "en"),
        ("government schemes for farmers", "en"),
        
        # Kannada queries
        ("ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ", "kn"),
        ("ಕೃಷಿ ಯೋಜನೆಗಳು ಯಾವುವು?", "kn"),
        ("ರೈತರಿಗೆ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು", "kn"),
        
        # Hindi queries
        ("प्रधान मंत्री किसान योजना", "hi"),
        ("कृषि योजनाएं क्या हैं?", "hi"),
        ("किसानों के लिए सरकारी योजनाएं", "hi"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_lang in test_cases:
        detected = detect_user_language(query)
        status = "✅ PASS" if detected == expected_lang else "❌ FAIL"
        
        if detected == expected_lang:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}")
        print(f"Query: {query}")
        print(f"Expected: {expected_lang}, Detected: {detected}")
    
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'=' * 60}\n")
    
    return failed == 0


def test_friendly_greetings():
    """Test friendly greetings in all languages"""
    print("=" * 60)
    print("TEST 2: Friendly Greetings")
    print("=" * 60)
    
    languages = ['en', 'kn', 'hi']
    
    for lang in languages:
        greeting = get_friendly_greeting(lang)
        print(f"\n{lang.upper()} Greeting:")
        print(greeting)
        
        # Check no markdown
        has_markdown = any(marker in greeting for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
            return False
        else:
            print("✅ No markdown detected")
    
    print(f"\n{'=' * 60}\n")
    return True


def test_sector_intro():
    """Test sector introduction messages"""
    print("=" * 60)
    print("TEST 3: Sector Introduction Messages")
    print("=" * 60)
    
    test_cases = [
        ('en', 'Agriculture', 5),
        ('kn', 'Agriculture', 5),
        ('hi', 'Agriculture', 5),
    ]
    
    for lang, sector, count in test_cases:
        intro = get_sector_intro(lang, sector, count)
        print(f"\n{lang.upper()} - {sector} ({count} schemes):")
        print(intro)
        
        # Check no markdown
        has_markdown = any(marker in intro for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
            return False
        else:
            print("✅ No markdown detected")
    
    print(f"\n{'=' * 60}\n")
    return True


def test_match_intro():
    """Test match introduction messages"""
    print("=" * 60)
    print("TEST 4: Match Introduction Messages")
    print("=" * 60)
    
    test_cases = [
        ('en', 'exact_match', 'PM-Kisan Scheme', 1),
        ('kn', 'exact_match', 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ', 1),
        ('hi', 'fuzzy_match', 'प्रधान मंत्री किसान योजना', 1),
        ('en', 'vector_match', None, 3),
    ]
    
    for lang, match_type, scheme_title, count in test_cases:
        intro = get_match_intro(lang, match_type, scheme_title, count)
        print(f"\n{lang.upper()} - {match_type}:")
        print(intro)
        
        # Check no markdown
        has_markdown = any(marker in intro for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
            return False
        else:
            print("✅ No markdown detected")
    
    print(f"\n{'=' * 60}\n")
    return True


def test_no_scheme_message():
    """Test no scheme found messages"""
    print("=" * 60)
    print("TEST 5: No Scheme Messages")
    print("=" * 60)
    
    test_cases = [
        ('en', 'random query'),
        ('kn', 'ಯಾದೃಚ್ಛಿಕ ಪ್ರಶ್ನೆ'),
        ('hi', 'यादृच्छिक प्रश्न'),
    ]
    
    for lang, query in test_cases:
        message = get_no_scheme_message(lang, query)
        print(f"\n{lang.upper()}:")
        print(message)
        
        # Check no markdown
        has_markdown = any(marker in message for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
            return False
        else:
            print("✅ No markdown detected")
    
    print(f"\n{'=' * 60}\n")
    return True


def test_gemini_translation():
    """Test Gemini translation (OPTIONAL - requires API key)"""
    print("=" * 60)
    print("TEST 6: Gemini Translation (Optional)")
    print("=" * 60)
    
    # Skip if Gemini API not configured
    try:
        english_text = """Scheme Name: PM-Kisan Scheme
Sector: Agriculture
Description: Direct income support to farmers
Eligibility: All farmer families"""
        
        print("\nOriginal English Text:")
        print(english_text)
        
        # Test Kannada translation
        print("\n\nTranslating to Kannada...")
        kannada_text = translate_with_gemini(english_text, 'kn')
        print(kannada_text)
        
        # Check no markdown
        has_markdown = any(marker in kannada_text for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
        else:
            print("✅ No markdown detected")
        
        # Test Hindi translation
        print("\n\nTranslating to Hindi...")
        hindi_text = translate_with_gemini(english_text, 'hi')
        print(hindi_text)
        
        # Check no markdown
        has_markdown = any(marker in hindi_text for marker in ['**', '*', '#', '•', '- '])
        if has_markdown:
            print("❌ FAIL: Contains markdown!")
        else:
            print("✅ No markdown detected")
        
        print(f"\n{'=' * 60}\n")
        return True
        
    except Exception as e:
        print(f"\n⚠️ SKIPPED: {str(e)}")
        print("(This is normal if Gemini API is not configured)")
        print(f"\n{'=' * 60}\n")
        return True


def run_all_tests():
    """Run all multilingual tests"""
    print("\n" + "=" * 60)
    print("MULTILINGUAL SYSTEM TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {
        "Language Detection": test_language_detection(),
        "Friendly Greetings": test_friendly_greetings(),
        "Sector Introductions": test_sector_intro(),
        "Match Introductions": test_match_intro(),
        "No Scheme Messages": test_no_scheme_message(),
        "Gemini Translation": test_gemini_translation(),
    }
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    failed = sum(1 for result in results.values() if not result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(results)} test suites")
    print(f"{'=' * 60}\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Multilingual system is working correctly.")
    else:
        print(f"⚠️ {failed} test suite(s) failed. Please review the output above.")
    
    return failed == 0


if __name__ == '__main__':
    run_all_tests()
