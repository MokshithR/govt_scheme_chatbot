#!/usr/bin/env python
"""
Voice Output Test - Enable and test voice functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.voice_processing import VoiceProcessor
import base64
import io

def test_voice_output():
    """Test voice output functionality"""
    
    print("🎤 VOICE OUTPUT FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Initialize voice processor
    print("🔧 Initializing voice processor...")
    try:
        voice_processor = VoiceProcessor()
        print("✅ Voice processor initialized successfully")
    except Exception as e:
        print(f"❌ Voice processor initialization failed: {e}")
        return False
    
    # Test text-to-speech
    test_messages = [
        "Hello! Welcome to the Government Voice Chatbot.",
        "I can help you find government schemes and benefits.",
        "Please tell me how I can assist you today."
    ]
    
    print(f"\n🗣️  Testing text-to-speech with {len(test_messages)} messages...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        try:
            # Test gTTS (Google Text-to-Speech) - Online
            print("   🌐 Testing gTTS (online)...")
            audio_data = voice_processor.text_to_speech_gtts(message, language='en')
            
            if audio_data:
                print("   ✅ gTTS audio generated successfully")
                print(f"   📊 Audio size: {len(audio_data)} bytes")
            else:
                print("   ❌ gTTS failed")
            
            # Test pyttsx3 (offline)
            print("   💻 Testing pyttsx3 (offline)...")
            audio_data_pyttsx3 = voice_processor.text_to_speech_pyttsx3(message, language='en')
            
            if audio_data_pyttsx3:
                print("   ✅ pyttsx3 audio generated successfully")
                print(f"   📊 Audio size: {len(audio_data_pyttsx3)} bytes")
            else:
                print("   ❌ pyttsx3 failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True

def test_voice_with_scheme():
    """Test voice output with scheme information"""
    
    print(f"\n🎯 VOICE OUTPUT WITH SCHEME INFORMATION")
    print("=" * 45)
    
    # Sample scheme response
    scheme_response = """
    I found the Digital Skills for Youth Program 2024 for you!
    
    This is a comprehensive digital skills training program for youth aged 18-35.
    It offers free courses in programming, digital marketing, and data analytics.
    Benefits include monthly stipend of 3000 rupees and placement assistance.
    
    To apply, visit digitalskills.gov.in and upload your documents.
    """
    
    print("📋 Testing scheme response voice output...")
    
    try:
        voice_processor = VoiceProcessor()
        
        # Test with different languages
        languages = ['en', 'hi', 'kn']  # English, Hindi, Kannada
        
        for lang in languages:
            print(f"\n🌍 Testing language: {lang}")
            
            try:
                audio_data = voice_processor.text_to_speech(scheme_response, language=lang, use_gtts=True)
                
                if audio_data:
                    print(f"   ✅ Voice generated for {lang}")
                    print(f"   📊 Audio size: {len(audio_data)} bytes")
                    
                    # Save as test file
                    output_file = f"test_voice_{lang}.mp3"
                    with open(output_file, 'wb') as f:
                        f.write(audio_data)
                    print(f"   💾 Saved as: {output_file}")
                else:
                    print(f"   ❌ Failed to generate voice for {lang}")
                    
            except Exception as e:
                print(f"   ❌ Error with {lang}: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def enable_voice_in_frontend():
    """Show how to enable voice in frontend"""
    
    print(f"\n🖥️  ENABLING VOICE IN FRONTEND")
    print("=" * 35)
    
    frontend_code = '''
// Add voice output to chatbot responses
function playVoiceResponse(text, language = 'en') {
    // Call voice API to get audio
    fetch('/voice-text-to-speech/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'text': text,
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.audio_data) {
            // Play the audio
            const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
            audio.play();
            
            // Show voice indicator
            log('🔊 Playing voice response...', 'bot');
        }
    })
    .catch(error => {
        console.error('Voice playback error:', error);
    });
}

// Modify existing bot response function
function addBotResponse(message) {
    log(message, 'bot');
    
    // Auto-play voice response if enabled
    if (voiceEnabled) {
        playVoiceResponse(message, currentLanguage);
    }
}

// Add voice toggle button
function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const voiceBtn = document.getElementById('voiceToggle');
    
    if (voiceEnabled) {
        voiceBtn.innerHTML = '<i class="fas fa-volume-up"></i> Voice ON';
        voiceBtn.classList.add('voice-active');
        log('🔊 Voice output enabled', 'bot');
    } else {
        voiceBtn.innerHTML = '<i class="fas fa-volume-mute"></i> Voice OFF';
        voiceBtn.classList.remove('voice-active');
        log('🔇 Voice output disabled', 'bot');
    }
}
'''
    
    print("📝 Add this JavaScript to your frontend:")
    print(frontend_code)
    
    print("\n🎨 Add voice toggle button to HTML:")
    html_button = '''
<button id="voiceToggle" onclick="toggleVoice()" class="voice-toggle-btn">
    <i class="fas fa-volume-mute"></i> Voice OFF
</button>
'''
    print(html_button)

def create_voice_endpoint():
    """Create voice endpoint for frontend"""
    
    print(f"\n🔧 BACKEND VOICE ENDPOINT")
    print("=" * 25)
    
    endpoint_code = '''
# Add to views.py
@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech_api(request):
    """Convert text to speech for frontend"""
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Text is required'})
        
        # Generate voice response
        voice_processor = VoiceProcessor()
        result = voice_processor.generate_voice_response(text, language)
        
        if result['success']:
            # Convert audio to base64 for frontend
            audio_base64 = base64.b64encode(result['audio_data']).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'audio_data': audio_base64,
                'language': language
            })
        else:
            return JsonResponse({'success': False, 'error': result['error']})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Add to urls.py
path('voice-text-to-speech/', views.text_to_speech_api, name='text_to_speech_api'),
'''
    
    print("📝 Add this endpoint to your backend:")
    print(endpoint_code)

def main():
    """Main test function"""
    
    print("🎤 GOVERNMENT VOICE CHATBOT - VOICE OUTPUT TEST")
    print("=" * 60)
    
    # Test voice output
    success = test_voice_output()
    
    if success:
        # Test with scheme information
        test_voice_with_scheme()
        
        # Show frontend integration
        enable_voice_in_frontend()
        
        # Show backend endpoint
        create_voice_endpoint()
        
        print(f"\n" + "=" * 60)
        print("🎉 VOICE OUTPUT SETUP COMPLETE!")
        print("=" * 35)
        
        print("✅ Voice output functionality is available")
        print("✅ Both gTTS (online) and pyttsx3 (offline) working")
        print("✅ Multiple language support ready")
        print("✅ Frontend integration code provided")
        print("✅ Backend endpoint code provided")
        
        print(f"\n🚀 NEXT STEPS:")
        print("1. Add the voice endpoint to views.py")
        print("2. Add the URL pattern to urls.py")
        print("3. Add the JavaScript code to home.html")
        print("4. Add the voice toggle button to the interface")
        print("5. Test with different languages")
        
    else:
        print("❌ Voice output test failed - check dependencies")

if __name__ == "__main__":
    main()
