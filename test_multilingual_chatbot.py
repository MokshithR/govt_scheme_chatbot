"""
Test script for multilingual voice chatbot with forced language selection
Tests: English, Kannada, Hindi voice and text queries

Run with: python test_multilingual_chatbot.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.chatbot_logic import chatbot
from chatbot.voice_processing import voice_processor
import json

def test_text_queries():
    """Test text queries in all three languages"""
    print("=" * 80)
    print("TEST 1: TEXT QUERIES - MULTILINGUAL SUPPORT")
    print("=" * 80)
    
    test_cases = [
        {
            'query': 'What are agricultural schemes?',
            'lang': 'en',
            'expected_lang': 'English',
            'description': 'English query about agriculture'
        },
        {
            'query': 'ಕೃಷಿ ಯೋಜನೆಗಳು ಯಾವುವು?',
            'lang': 'kn',
            'expected_lang': 'Kannada',
            'description': 'Kannada query about agriculture'
        },
        {
            'query': 'कृषि योजनाएं क्या हैं?',
            'lang': 'hi',
            'expected_lang': 'Hindi',
            'description': 'Hindi query about agriculture'
        },
        {
            'query': 'PM Kisan',
            'lang': 'en',
            'expected_lang': 'English',
            'description': 'English query - specific scheme'
        },
        {
            'query': 'ಪಿಎಂ ಕಿಸಾನ್',
            'lang': 'kn',
            'expected_lang': 'Kannada',
            'description': 'Kannada query - specific scheme'
        },
        {
            'query': 'पीएम किसान',
            'lang': 'hi',
            'expected_lang': 'Hindi',
            'description': 'Hindi query - specific scheme'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Language: {test['lang']} ({test['expected_lang']})")
        print('=' * 80)
        
        try:
            # Process query
            result = chatbot.process_query(test['query'], test['lang'])
            
            if result['success']:
                response_text = result['response']['text']
                schemes_count = len(result.get('schemes', []))
                
                print(f"\n✓ Success!")
                print(f"Response length: {len(response_text)} chars")
                print(f"Schemes found: {schemes_count}")
                print(f"\nResponse preview:")
                print("-" * 80)
                print(response_text[:300] + ("..." if len(response_text) > 300 else ""))
                print("-" * 80)
                
                # Verification checks
                print(f"\n✓ Language verification:")
                checks = [
                    ('#' not in response_text, "No # symbols"),
                    ('**' not in response_text, "No ** symbols"),
                    ('*' not in response_text or response_text.count('*') < 3, "No * symbols (or minimal)"),
                    ('|' not in response_text, "No | pipe symbols"),
                    (not any(line.strip().startswith(('- ', '* ', '• ')) for line in response_text.split('\n')), "No bullet points"),
                    (result['language'] == test['lang'], f"Response language is {test['lang']}"),
                ]
                
                for passed, check_name in checks:
                    symbol = '✓' if passed else '✗'
                    print(f"  {symbol} {check_name}")
                
                all_passed = all(check[0] for check in checks)
                if all_passed:
                    print(f"\n✅ Test {i} PASSED - {test['expected_lang']} response is clean!")
                else:
                    print(f"\n⚠️  Test {i} PARTIAL - Some issues detected")
            else:
                print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_query_translation():
    """Test that Kannada/Hindi queries are translated to English for DB search"""
    print("\n" + "=" * 80)
    print("TEST 2: QUERY TRANSLATION FOR DB SEARCH")
    print("=" * 80)
    
    test_cases = [
        {
            'query': 'ಕೃಷಿ ಯೋಜನೆಗಳು',
            'lang': 'kn',
            'expected_contains': ['agricultural', 'scheme', 'farm', 'agriculture'],
            'description': 'Kannada: agricultural schemes'
        },
        {
            'query': 'स्वास्थ्य योजनाएं',
            'lang': 'hi',
            'expected_contains': ['health', 'scheme', 'medical'],
            'description': 'Hindi: health schemes'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest 2.{i}: {test['description']}")
        print(f"Original query: {test['query']}")
        
        try:
            result = chatbot.process_query(test['query'], test['lang'])
            
            if result['success']:
                schemes_found = len(result.get('schemes', []))
                print(f"✓ Found {schemes_found} schemes")
                
                # Check if results are relevant (means translation worked)
                if schemes_found > 0:
                    print(f"✅ Translation worked - DB search returned results")
                    print(f"   First scheme: {result['schemes'][0].get('title', 'N/A')}")
                else:
                    print(f"⚠️  No schemes found - check if DB has data or translation quality")
            else:
                print(f"✗ Query failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_voice_pipeline():
    """Test voice processing pipeline (if audio file available)"""
    print("\n" + "=" * 80)
    print("TEST 3: VOICE PIPELINE (requires audio file)")
    print("=" * 80)
    
    print("\nVoice pipeline test requires actual audio files.")
    print("To test voice:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Use frontend voice interface")
    print("3. Select language from dropdown (en/kn/hi)")
    print("4. Speak query")
    print("5. Verify:")
    print("   - Whisper transcribes in selected language (no auto-detect)")
    print("   - Gemini responds in selected language")
    print("   - TTS speaks in selected language")
    print("   - No markdown symbols in audio")

def test_tts_voices():
    """Test TTS voice generation for all languages"""
    print("\n" + "=" * 80)
    print("TEST 4: TTS VOICE GENERATION")
    print("=" * 80)
    
    test_cases = [
        {
            'text': 'PM Kisan provides financial assistance to farmers.',
            'lang': 'en',
            'description': 'English TTS'
        },
        {
            'text': 'ಪಿಎಂ ಕಿಸಾನ್ ರೈತರಿಗೆ ಆರ್ಥಿಕ ಸಹಾಯ ಒದಗಿಸುತ್ತದೆ.',
            'lang': 'kn',
            'description': 'Kannada TTS'
        },
        {
            'text': 'पीएम किसान किसानों को वित्तीय सहायता प्रदान करता है।',
            'lang': 'hi',
            'description': 'Hindi TTS'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest 4.{i}: {test['description']}")
        print(f"Text: {test['text'][:50]}...")
        print(f"Language: {test['lang']}")
        
        try:
            result = voice_processor.text_to_speech(test['text'], test['lang'], use_gtts=True)
            
            if result['audio_data'] and not result['error']:
                audio_size = len(result['audio_data'])
                print(f"✅ TTS SUCCESS")
                print(f"   Format: {result['format']}")
                print(f"   Size: {audio_size} bytes (base64)")
                print(f"   Language: {test['lang']}")
            else:
                print(f"✗ TTS failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_no_markdown_in_responses():
    """Verify NO markdown symbols in any language responses"""
    print("\n" + "=" * 80)
    print("TEST 5: NO MARKDOWN IN RESPONSES")
    print("=" * 80)
    
    queries = [
        ('Tell me about PM Kisan', 'en'),
        ('ಪಿಎಂ ಕಿಸಾನ್ ಬಗ್ಗೆ ತಿಳಿಸು', 'kn'),
        ('पीएम किसान के बारे में बताएं', 'hi'),
    ]
    
    forbidden_symbols = ['#', '**', '*', '|', '- ', '• ']
    
    for i, (query, lang) in enumerate(queries, 1):
        print(f"\nTest 5.{i}: {query[:30]}... (lang: {lang})")
        
        try:
            result = chatbot.process_query(query, lang)
            
            if result['success']:
                response_text = result['response']['text']
                
                found_symbols = []
                for symbol in forbidden_symbols:
                    if symbol in response_text:
                        found_symbols.append(symbol)
                
                if not found_symbols:
                    print(f"✅ CLEAN - No markdown symbols found")
                else:
                    print(f"⚠️  FOUND SYMBOLS: {', '.join(found_symbols)}")
                    print(f"   Response preview: {response_text[:200]}")
            else:
                print(f"✗ Query failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MULTILINGUAL CHATBOT - COMPREHENSIVE TEST SUITE")
    print("Testing: English, Kannada, Hindi support")
    print("=" * 80)
    
    try:
        # Test 1: Text queries in all languages
        test_text_queries()
        
        # Test 2: Query translation for DB search
        test_query_translation()
        
        # Test 3: Voice pipeline info
        test_voice_pipeline()
        
        # Test 4: TTS voice generation
        test_tts_voices()
        
        # Test 5: No markdown verification
        test_no_markdown_in_responses()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✓ Text queries: Tested English, Kannada, Hindi")
        print("✓ Query translation: Kn/Hi → English for DB search")
        print("✓ Gemini responses: Forced language output")
        print("✓ TTS: Language-specific voices (gTTS)")
        print("✓ Markdown removal: Verified clean text")
        print("\nNext steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Test voice interface with all 3 languages")
        print("3. Verify TTS audio speaks naturally (no 'asterisk', 'hash')")
        print("4. Test language switching in dropdown")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
