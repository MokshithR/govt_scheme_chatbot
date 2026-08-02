#!/usr/bin/env python
"""
Voice Feature Test - Verify the multilingual voice is now visible
"""

import requests
import json

def test_voice_feature_visibility():
    """Test if the voice feature is visible in the interface"""
    
    print("🎤 VOICE FEATURE VISIBILITY TEST")
    print("=" * 45)
    
    # Check if server is running
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        
        if response.status_code == 200:
            print("✅ Django server is running!")
            
            # Check if multilingual voice elements are in the HTML
            html_content = response.text
            
            voice_elements = [
                'multilingualVoiceBtn',
                'multilingual-voice-controls',
                'toggleMultilingualVoice()',
                'voiceLanguageSelect',
                'voiceSpeedSelect',
                '🔇 Multilingual Voice OFF'
            ]
            
            print(f"\n🔍 CHECKING VOICE ELEMENTS:")
            found_elements = 0
            
            for element in voice_elements:
                if element in html_content:
                    print(f"   ✅ Found: {element}")
                    found_elements += 1
                else:
                    print(f"   ❌ Missing: {element}")
            
            print(f"\n📊 RESULTS:")
            print(f"   Found: {found_elements}/{len(voice_elements)} elements")
            
            if found_elements >= len(voice_elements) - 1:
                print("   ✅ Voice feature is properly integrated!")
                return True
            else:
                print("   ⚠️  Some voice elements may be missing")
                return False
                
        else:
            print(f"❌ Server responded with: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Django server is not running!")
        print("💡 Start server with: python manage.py runserver")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_voice_endpoint():
    """Test the multilingual voice endpoint"""
    
    print(f"\n🌐 TESTING VOICE ENDPOINT")
    print("=" * 30)
    
    try:
        # Test the multilingual voice endpoint
        test_data = {
            'text': 'Hello, this is a test of the multilingual voice system.',
            'language': 'en',
            'speed': 'normal'
        }
        
        response = requests.post(
            'http://127.0.0.1:8000/multilingual-voice/',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ Voice endpoint is working!")
                print(f"   🎵 Language: {data.get('language_display', 'Unknown')}")
                print(f"   ⚡ Speed: {data.get('speed', 'unknown')}")
                print(f"   📊 Audio size: {data.get('audio_size', 0):,} bytes")
                print(f"   📝 Text length: {data.get('text_length', 0)} chars")
                return True
            else:
                print(f"❌ Voice generation failed: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            if response.status_code == 404:
                print("💡 Server may need restart to load new URL patterns")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def show_usage_instructions():
    """Show how to use the voice feature"""
    
    print(f"\n🎯 HOW TO USE MULTILINGUAL VOICE")
    print("=" * 40)
    
    print("1. 🌐 Open your chatbot interface:")
    print("   http://127.0.0.1:8000/")
    
    print("\n2. 🔊 Enable multilingual voice:")
    print("   • Look for '🔇 Multilingual Voice OFF' button")
    print("   • Click it to turn ON (becomes green)")
    
    print("\n3. 🌍 Select language:")
    print("   • Choose from 11 Indian languages")
    print("   • Options: English, Hindi, Kannada, Tamil, etc.")
    
    print("\n4. ⚡ Set voice speed:")
    print("   • Slow: 🐌 For better understanding")
    print("   • Normal: 🚶 Regular speed")
    print("   • Fast: 🏃 Quick responses")
    
    print("\n5. 💬 Test the voice:")
    print("   • Type any message in the chat")
    print("   • Chatbot responds with text + voice")
    print("   • Voice plays in selected language")
    
    print("\n✨ FEATURES AVAILABLE:")
    print("   ✅ Real-time voice generation")
    print("   ✅ 11 Indian languages")
    print("   ✅ Speed control")
    print("   ✅ Auto-play for responses")
    print("   ✅ High-quality Google TTS")

def main():
    """Main test function"""
    
    print("🎤 MULTILINGUAL VOICE FEATURE TEST")
    print("=" * 50)
    
    # Test if voice feature is visible
    visibility_ok = test_voice_feature_visibility()
    
    # Test voice endpoint
    endpoint_ok = test_voice_endpoint()
    
    # Show usage instructions
    show_usage_instructions()
    
    print(f"\n" + "=" * 50)
    print("🎉 TEST SUMMARY")
    print("=" * 20)
    
    if visibility_ok:
        print("✅ Voice feature is visible in interface")
    else:
        print("❌ Voice feature may not be properly integrated")
    
    if endpoint_ok:
        print("✅ Voice endpoint is working")
    else:
        print("❌ Voice endpoint needs attention")
    
    if visibility_ok and endpoint_ok:
        print("\n🚀 MULTILINGUAL VOICE IS READY!")
        print("You can now use voice responses in 11 Indian languages!")
    else:
        print("\n⚠️  Some issues detected - check the details above")
    
    print(f"\n💡 If voice features aren't showing:")
    print("   1. Restart Django server (Ctrl+C, then python manage.py runserver)")
    print("   2. Clear browser cache (Ctrl+F5)")
    print("   3. Check internet connection for voice generation")

if __name__ == "__main__":
    main()
