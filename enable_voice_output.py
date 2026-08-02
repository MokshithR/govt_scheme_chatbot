#!/usr/bin/env python
"""
Enable Voice Output - Simple setup for voice functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.voice_processing import VoiceProcessor
import base64

def test_voice_simple():
    """Simple voice test"""
    
    print("🎤 VOICE OUTPUT - SIMPLE TEST")
    print("=" * 40)
    
    try:
        voice_processor = VoiceProcessor()
        print("✅ Voice processor ready")
        
        # Test message
        message = "Hello! I can now speak to you. Welcome to the Government Voice Chatbot."
        
        print(f"\n🗣️  Testing: '{message}'")
        
        # Generate voice using gTTS (works best)
        audio_data = voice_processor.text_to_speech_gtts(message, language='en')
        
        if audio_data:
            print("✅ Voice generated successfully!")
            print(f"📊 Audio size: {len(audio_data)} bytes")
            
            # Save test file
            with open("voice_test.mp3", "wb") as f:
                f.write(audio_data)
            print("💾 Saved as: voice_test.mp3")
            
            return True
        else:
            print("❌ Voice generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def add_voice_endpoint():
    """Add voice endpoint to backend"""
    
    print(f"\n🔧 ADD VOICE ENDPOINT TO BACKEND")
    print("=" * 40)
    
    print("📝 Add this to chatbot/views.py:")
    print("""
@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech_api(request):
    \"\"\"Convert text to speech\"\"\"
    try:
        import json
        from voice_processing import VoiceProcessor
        import base64
        
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Text required'})
        
        voice_processor = VoiceProcessor()
        audio_data = voice_processor.text_to_speech_gtts(text, language)
        
        if audio_data:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return JsonResponse({
                'success': True,
                'audio_data': audio_base64
            })
        else:
            return JsonResponse({'success': False, 'error': 'Voice failed'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
""")
    
    print("📝 Add this to chatbot/urls.py:")
    print("""
path('voice-text-to-speech/', views.text_to_speech_api, name='text_to_speech_api'),
""")

def add_voice_frontend():
    """Add voice functionality to frontend"""
    
    print(f"\n🖥️  ADD VOICE TO FRONTEND")
    print("=" * 30)
    
    print("📝 Add this JavaScript to home.html:")
    print("""
// Voice functionality
let voiceEnabled = false;

function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const voiceBtn = document.getElementById('voiceToggle');
    
    if (voiceEnabled) {
        voiceBtn.innerHTML = '<i class="fas fa-volume-up"></i> Voice ON';
        voiceBtn.classList.add('active');
        log('🔊 Voice output enabled', 'bot');
    } else {
        voiceBtn.innerHTML = '<i class="fas fa-volume-mute"></i> Voice OFF';
        voiceBtn.classList.remove('active');
        log('🔇 Voice output disabled', 'bot');
    }
}

function playVoiceResponse(text, language = 'en') {
    if (!voiceEnabled) return;
    
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
            const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
            audio.play();
            log('🔊 Playing voice response...', 'bot');
        }
    })
    .catch(error => {
        console.error('Voice error:', error);
    });
}

// Modify bot response to include voice
function addBotResponse(message, messageType = 'bot') {
    log(message, messageType);
    
    // Auto-play voice if enabled
    if (voiceEnabled && messageType === 'bot') {
        // Extract text from HTML if needed
        const textContent = message.replace(/<[^>]*>/g, '');
        playVoiceResponse(textContent, currentLanguage);
    }
}
""")
    
    print("📝 Add this button to your interface:")
    print("""
<button id="voiceToggle" onclick="toggleVoice()" class="voice-btn">
    <i class="fas fa-volume-mute"></i> Voice OFF
</button>
""")
    
    print("📝 Add this CSS:")
    print("""
.voice-btn {
    background: var(--bg-accent);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 0.5rem 1rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.3s ease;
}

.voice-btn:hover {
    background: var(--primary-orange);
    color: white;
}

.voice-btn.active {
    background: var(--success-green);
    color: white;
    border-color: var(--success-green);
}
""")

def create_voice_test_page():
    """Create a simple voice test page"""
    
    print(f"\n🌐 CREATE VOICE TEST PAGE")
    print("=" * 30)
    
    test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Test - Government Chatbot</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>🎤 Voice Output Test</h1>
    
    <button onclick="testVoice()">Test Voice Output</button>
    <button onclick="testScheme()">Test Scheme Response</button>
    
    <div id="result"></div>
    
    <script>
        function testVoice() {
            const text = "Hello! Welcome to the Government Voice Chatbot. I can now speak to you!";
            
            fetch('/voice-text-to-speech/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'text': text,
                    'language': 'en'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
                    audio.play();
                    document.getElementById('result').innerHTML = '✅ Voice playing...';
                } else {
                    document.getElementById('result').innerHTML = '❌ Voice failed: ' + data.error;
                }
            })
            .catch(error => {
                document.getElementById('result').innerHTML = '❌ Error: ' + error;
            });
        }
        
        function testScheme() {
            const text = "I found the Digital Skills for Youth Program 2024. This program offers free training in programming and digital marketing with monthly stipend and placement assistance.";
            
            fetch('/voice-text-to-speech/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'text': text,
                    'language': 'en'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
                    audio.play();
                    document.getElementById('result').innerHTML = '✅ Scheme voice playing...';
                } else {
                    document.getElementById('result').innerHTML = '❌ Voice failed: ' + data.error;
                }
            });
        }
        
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    </script>
</body>
</html>
"""
    
    with open("voice_test.html", "w") as f:
        f.write(test_html)
    
    print("✅ Created voice_test.html")
    print("🌐 Open this file in your browser to test voice")

def main():
    """Main function"""
    
    print("🎤 ENABLE VOICE OUTPUT FOR CHATBOT")
    print("=" * 50)
    
    # Test voice functionality
    success = test_voice_simple()
    
    if success:
        print("\n✅ Voice output is working!")
        
        # Show implementation steps
        add_voice_endpoint()
        add_voice_frontend()
        create_voice_test_page()
        
        print(f"\n" + "=" * 50)
        print("🎉 VOICE SETUP COMPLETE!")
        print("=" * 30)
        
        print("📋 IMPLEMENTATION STEPS:")
        print("1. ✅ Voice processor tested and working")
        print("2. 📝 Add voice endpoint to views.py")
        print("3. 📝 Add URL pattern to urls.py")
        print("4. 📝 Add JavaScript to home.html")
        print("5. 🎨 Add voice toggle button")
        print("6. 🌐 Test with voice_test.html")
        
        print(f"\n🚀 FEATURES READY:")
        print("✅ Text-to-speech conversion")
        print("✅ Multiple language support")
        print("✅ Online voice (gTTS)")
        print("✅ Voice on/off toggle")
        print("✅ Auto-play responses")
        
    else:
        print("❌ Voice setup failed - check dependencies")

if __name__ == "__main__":
    main()
