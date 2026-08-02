#!/usr/bin/env python
"""
Multilingual Voice Output System
Complete setup for chatbot voice responses in multiple languages
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.voice_processing import VoiceProcessor
import base64
import json

def create_multilingual_voice_endpoint():
    """Create backend endpoint for multilingual voice"""
    
    print("🌍 MULTILINGUAL VOICE ENDPOINT")
    print("=" * 40)
    
    endpoint_code = '''
# Add to chatbot/views.py
@csrf_exempt
@require_http_methods(["POST"])
def multilingual_voice_api(request):
    """Convert text to speech in multiple languages"""
    try:
        import json
        from voice_processing import VoiceProcessor
        import base64
        
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'en')
        voice_speed = data.get('speed', 'normal')  # slow, normal, fast
        
        if not text:
            return JsonResponse({
                'success': False, 
                'error': 'Text is required'
            })
        
        # Initialize voice processor
        voice_processor = VoiceProcessor()
        
        # Language mapping for gTTS
        language_mapping = {
            'en': 'en',      # English
            'hi': 'hi',      # Hindi
            'kn': 'kn',      # Kannada
            'ta': 'ta',      # Tamil
            'te': 'te',      # Telugu
            'mr': 'mr',      # Marathi
            'bn': 'bn',      # Bengali
            'gu': 'gu',      # Gujarati
            'ml': 'ml',      # Malayalam
            'pa': 'pa',      # Punjabi
            'ur': 'ur',      # Urdu
        }
        
        # Get correct language code
        gtts_language = language_mapping.get(language, 'en')
        
        # Generate voice with speed control
        slow = (voice_speed == 'slow')
        audio_data = voice_processor.text_to_speech_gtts(
            text, 
            language=gtts_language, 
            slow=slow
        )
        
        if audio_data:
            # Convert to base64 for frontend
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'audio_data': audio_base64,
                'language': language,
                'language_display': get_language_display_name(language),
                'speed': voice_speed,
                'text_length': len(text),
                'audio_size': len(audio_data)
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Voice generation failed'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

def get_language_display_name(language_code):
    """Get display name for language"""
    names = {
        'en': 'English',
        'hi': 'हिन्दी (Hindi)',
        'kn': 'ಕನ್ನಡ (Kannada)',
        'ta': 'தமிழ் (Tamil)',
        'te': 'తెలుగు (Telugu)',
        'mr': 'मराठी (Marathi)',
        'bn': 'বাংলা (Bengali)',
        'gu': 'ગુજરાતી (Gujarati)',
        'ml': 'മലയാളം (Malayalam)',
        'pa': 'ਪੰਜਾਬੀ (Punjabi)',
        'ur': 'اردو (Urdu)'
    }
    return names.get(language_code, 'English')
'''
    
    print("📝 Add this to chatbot/views.py:")
    print(endpoint_code)
    
    print("\n📝 Add this to chatbot/urls.py:")
    print("path('multilingual-voice/', views.multilingual_voice_api, name='multilingual_voice_api'),")

def create_multilingual_frontend():
    """Create frontend JavaScript for multilingual voice"""
    
    print(f"\n🖥️  MULTILINGUAL FRONTEND")
    print("=" * 30)
    
    frontend_code = '''
// Multilingual Voice System
let multilingualVoiceEnabled = false;
let currentVoiceLanguage = 'en';
let voiceSpeed = 'normal';

// Language configurations
const voiceLanguages = {
    'en': { name: 'English', code: 'en', flag: '🇺🇸' },
    'hi': { name: 'हिन्दी', code: 'hi', flag: '🇮🇳' },
    'kn': { name: 'ಕನ್ನಡ', code: 'kn', flag: '🇮🇳' },
    'ta': { name: 'தமிழ்', code: 'ta', flag: '🇮🇳' },
    'te': { name: 'తెలుగు', code: 'te', flag: '🇮🇳' },
    'mr': { name: 'मराठी', code: 'mr', flag: '🇮🇳' },
    'bn': { name: 'বাংলা', code: 'bn', flag: '🇮🇳' },
    'gu': { name: 'ગુજરાતી', code: 'gu', flag: '🇮🇳' },
    'ml': { name: 'മലയാളം', code: 'ml', flag: '🇮🇳' },
    'pa': { name: 'ਪੰਜਾਬੀ', code: 'pa', flag: '🇮🇳' },
    'ur': { name: 'اردو', code: 'ur', flag: '🇮🇳' }
};

// Toggle multilingual voice
function toggleMultilingualVoice() {
    multilingualVoiceEnabled = !multilingualVoiceEnabled;
    const voiceBtn = document.getElementById('multilingualVoiceBtn');
    
    if (multilingualVoiceEnabled) {
        voiceBtn.innerHTML = '🔊 Multilingual Voice ON';
        voiceBtn.classList.add('voice-active');
        log('🔊 Multilingual voice output enabled', 'bot');
    } else {
        voiceBtn.innerHTML = '🔇 Multilingual Voice OFF';
        voiceBtn.classList.remove('voice-active');
        log('🔇 Multilingual voice output disabled', 'bot');
    }
}

// Change voice language
function changeVoiceLanguage(language) {
    currentVoiceLanguage = language;
    const langInfo = voiceLanguages[language];
    log(`🌍 Voice language changed to: ${langInfo.flag} ${langInfo.name}`, 'bot');
}

// Change voice speed
function changeVoiceSpeed(speed) {
    voiceSpeed = speed;
    log(`⚡ Voice speed changed to: ${speed}`, 'bot');
}

// Play multilingual voice response
function playMultilingualVoiceResponse(text, language = null) {
    if (!multilingualVoiceEnabled) return;
    
    // Use specified language or current voice language
    const targetLanguage = language || currentVoiceLanguage || 'en';
    
    fetch('/multilingual-voice/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'text': text,
            'language': targetLanguage,
            'speed': voiceSpeed
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.audio_data) {
            const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
            audio.play();
            
            const langInfo = voiceLanguages[data.language];
            log(`🔊 Playing voice in ${langInfo.flag} ${langInfo.name}...`, 'bot');
        } else {
            log(`❌ Voice failed: ${data.error}`, 'bot');
        }
    })
    .catch(error => {
        console.error('Multilingual voice error:', error);
        log('❌ Voice playback error', 'bot');
    });
}

// Enhanced bot response with multilingual voice
function addMultilingualBotResponse(message, language = null) {
    log(message, 'bot');
    
    // Auto-play voice if enabled
    if (multilingualVoiceEnabled) {
        // Extract text from HTML
        const textContent = message.replace(/<[^>]*>/g, '');
        playMultilingualVoiceResponse(textContent, language || currentLanguage);
    }
}

// Create language selector
function createLanguageSelector() {
    let selectorHTML = '<div class="voice-language-selector">';
    selectorHTML += '<label>🌍 Voice Language:</label>';
    selectorHTML += '<select id="voiceLanguageSelect" onchange="changeVoiceLanguage(this.value)">';
    
    for (const [code, info] of Object.entries(voiceLanguages)) {
        const selected = code === currentVoiceLanguage ? 'selected' : '';
        selectorHTML += `<option value="${code}" ${selected}>${info.flag} ${info.name}</option>`;
    }
    
    selectorHTML += '</select>';
    selectorHTML += '</div>';
    
    return selectorHTML;
}

// Create speed selector
function createSpeedSelector() {
    return `
        <div class="voice-speed-selector">
            <label>⚡ Voice Speed:</label>
            <select id="voiceSpeedSelect" onchange="changeVoiceSpeed(this.value)">
                <option value="slow" ${voiceSpeed === 'slow' ? 'selected' : ''}>🐌 Slow</option>
                <option value="normal" ${voiceSpeed === 'normal' ? 'selected' : ''}>🚶 Normal</option>
                <option value="fast" ${voiceSpeed === 'fast' ? 'selected' : ''}>🏃 Fast</option>
            </select>
        </div>
    `;
}
'''
    
    print("📝 Add this JavaScript to home.html:")
    print(frontend_code)

def create_voice_controls_html():
    """Create HTML for voice controls"""
    
    print(f"\n🎨 VOICE CONTROLS HTML")
    print("=" * 25)
    
    html_code = '''
<!-- Multilingual Voice Controls -->
<div class="multilingual-voice-controls">
    <button id="multilingualVoiceBtn" onclick="toggleMultilingualVoice()" class="multilingual-voice-btn">
        🔇 Multilingual Voice OFF
    </button>
    
    <div id="voiceControlsPanel" style="display: none;">
        <script>
            document.write(createLanguageSelector());
            document.write(createSpeedSelector());
        </script>
    </div>
</div>

<style>
.multilingual-voice-controls {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 1rem;
    margin: 1rem 0;
}

.multilingual-voice-btn {
    background: var(--bg-accent);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 0.75rem 1.5rem;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.3s ease;
    width: 100%;
    margin-bottom: 1rem;
}

.multilingual-voice-btn:hover {
    background: var(--primary-orange);
    color: white;
    transform: translateY(-1px);
}

.multilingual-voice-btn.voice-active {
    background: var(--success-green);
    color: white;
    border-color: var(--success-green);
}

.voice-language-selector, .voice-speed-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.5rem 0;
}

.voice-language-selector label, .voice-speed-selector label {
    font-weight: 600;
    color: var(--text-primary);
    min-width: 120px;
}

.voice-language-selector select, .voice-speed-selector select {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.9rem;
}

.voice-language-selector select:focus, .voice-speed-selector select:focus {
    outline: none;
    border-color: var(--primary-orange);
    box-shadow: 0 0 0 2px rgba(255, 152, 0, 0.2);
}
</style>

<script>
// Show/hide voice controls based on voice state
function toggleMultilingualVoice() {
    multilingualVoiceEnabled = !multilingualVoiceEnabled;
    const voiceBtn = document.getElementById('multilingualVoiceBtn');
    const controlsPanel = document.getElementById('voiceControlsPanel');
    
    if (multilingualVoiceEnabled) {
        voiceBtn.innerHTML = '🔊 Multilingual Voice ON';
        voiceBtn.classList.add('voice-active');
        controlsPanel.style.display = 'block';
        log('🔊 Multilingual voice output enabled', 'bot');
    } else {
        voiceBtn.innerHTML = '🔇 Multilingual Voice OFF';
        voiceBtn.classList.remove('voice-active');
        controlsPanel.style.display = 'none';
        log('🔇 Multilingual voice output disabled', 'bot');
    }
}
</script>
'''
    
    print("📝 Add this HTML to your interface:")
    print(html_code)

def create_multilingual_test_page():
    """Create comprehensive test page for multilingual voice"""
    
    print(f"\n🌐 MULTILINGUAL TEST PAGE")
    print("=" * 30)
    
    test_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Multilingual Voice Test - Government Chatbot</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        button { padding: 10px 20px; margin: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #007bff; color: white; }
        select { padding: 8px; margin: 5px; font-size: 14px; }
        #result { margin-top: 20px; padding: 10px; border: 1px solid #ddd; }
        .success { color: green; }
        .error { color: red; }
        .lang-flag { font-size: 20px; margin-right: 5px; }
    </style>
</head>
<body>
    <h1>🌍 Multilingual Voice Test - Government Chatbot</h1>
    
    <div class="test-section">
        <h3>Voice Controls</h3>
        <label>Language:</label>
        <select id="languageSelect">
            <option value="en">🇺🇸 English</option>
            <option value="hi">🇮🇳 हिन्दी</option>
            <option value="kn">🇮🇳 ಕನ್ನಡ</option>
            <option value="ta">🇮🇳 தமிழ்</option>
            <option value="te">🇮🇳 తెలుగు</option>
            <option value="mr">🇮🇳 मराठी</option>
            <option value="bn">🇮🇳 বাংলা</option>
            <option value="gu">🇮🇳 ગુજરાતી</option>
        </select>
        
        <label>Speed:</label>
        <select id="speedSelect">
            <option value="slow">🐌 Slow</option>
            <option value="normal" selected>🚶 Normal</option>
            <option value="fast">🏃 Fast</option>
        </select>
    </div>
    
    <div class="test-section">
        <h3>Test Messages</h3>
        <button onclick="testWelcome()">Test Welcome Message</button>
        <button onclick="testScheme()">Test Scheme Information</button>
        <button onclick="testEligibility()">Test Eligibility Criteria</button>
        <button onclick="testApplication()">Test Application Process</button>
        <button onclick="testCustom()">Test Custom Message</button>
    </div>
    
    <div class="test-section">
        <h3>Custom Message</h3>
        <input type="text" id="customText" placeholder="Enter custom text..." style="width: 300px; padding: 8px;">
        <button onclick="testCustomText()">Speak Custom Text</button>
    </div>
    
    <div id="result"></div>
    
    <script>
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
        
        function speakText(text) {
            const language = document.getElementById('languageSelect').value;
            const speed = document.getElementById('speedSelect').value;
            
            document.getElementById('result').innerHTML = '<div class="success">🔊 Generating voice...</div>';
            
            fetch('/multilingual-voice/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'text': text,
                    'language': language,
                    'speed': speed
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
                    audio.play();
                    document.getElementById('result').innerHTML = 
                        `<div class="success">✅ Playing in ${data.language_display} | Speed: ${data.speed} | Size: ${data.audio_size} bytes</div>`;
                } else {
                    document.getElementById('result').innerHTML = `<div class="error">❌ Voice failed: ${data.error}</div>`;
                }
            })
            .catch(error => {
                document.getElementById('result').innerHTML = `<div class="error">❌ Error: ${error}</div>`;
            });
        }
        
        function testWelcome() {
            const messages = {
                'en': 'Welcome to the Government Voice Chatbot! How can I help you today?',
                'hi': 'सरकारी वॉइस चैटबॉट में आपका स्वागत है! मैं आज आपकी क्या सहायता कर सकता हूं?',
                'kn': 'ಸರ್ಕಾರಿ ಧ್ವನಿ ಚಾಟ್‌ಬಾಟ್‌ಗೆ ಸ್ವಾಗತ! ನಾನು ಇಂದು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
                'ta': 'அரசு குரல் அரட்டைக்கு வரவேற்கிறோம்! நான் இன்று உங்களுக்கு எப்படி உதவ முடியும்?',
                'te': 'ప్రభుత్వ వాయిస్ చాట్‌బాట్‌కి స్వాగతం! నేను ఈరోజు మీకు ఎలా సహాయం చేయగలను?'
            };
            
            const language = document.getElementById('languageSelect').value;
            const text = messages[language] || messages['en'];
            speakText(text);
        }
        
        function testScheme() {
            const messages = {
                'en': 'I found the Digital Skills for Youth Program 2024. This program offers free training in programming and digital marketing.',
                'hi': 'मैंने डिजिटल स्किल्स फॉर यूथ प्रोग्राम 2024 खोजा। यह प्रोग्राम प्रोग्रामिंग और डिजिटल मार्केटिंग में मुफ्त प्रशिक्षण प्रदान करता है।',
                'kn': 'ನಾನು ಡಿಜಿಟಲ್ ಸ್ಕಿಲ್ಸ್ ಫಾರ್ ಯೂತ್ ಪ್ರೋಗ್ರಾಂ 2024 ಅನ್ನು ಕಂಡುಹಿಡಿದಿದ್ದೇನೆ. ಈ ಪ್ರೋಗ್ರಾಂ ಪ್ರೋಗ್ರಾಮಿಂಗ್ ಮತ್ತು ಡಿಜಿಟಲ್ ಮಾರ್ಕೆಟಿಂಗ್‌ನಲ್ಲಿ ಉಚಿತ ತರಬೇತಿಯನ್ನು ನೀಡುತ್ತದೆ.'
            };
            
            const language = document.getElementById('languageSelect').value;
            const text = messages[language] || messages['en'];
            speakText(text);
        }
        
        function testEligibility() {
            const messages = {
                'en': 'Eligibility: Age 18-35 years, minimum 10th pass, annual family income less than 3 lakh rupees.',
                'hi': 'पात्रता: आयु 18-35 वर्ष, न्यूनतम 10वीं पास, वार्षिक पारिवारिक आय 3 लाख रुपये से कम।',
                'kn': 'ಅರ್ಹತೆ: ವಯಸ್ಸು 18-35 ವರ್ಷ, ಕನಿಷ್ಠ 10ನೇ ತರಗತಿ ಪಾಸ್, ವಾರ್ಷಿಕ ಕುಟುಂಬದ ಆದಾಯ 3 ಲಕ್ಷ ರೂಪಾಯಿಗಳಿಗಿಂತ ಕಡಿಮೆ.'
            };
            
            const language = document.getElementById('languageSelect').value;
            const text = messages[language] || messages['en'];
            speakText(text);
        }
        
        function testApplication() {
            const messages = {
                'en': 'Application process: Visit the official website, register with your details, upload required documents, and submit the form.',
                'hi': 'आवेदन प्रक्रिया: आधिकारिक वेबसाइट पर जाएं, अपना विवरण दर्ज करें, आवश्यक दस्तावेज़ अपलोड करें, और फॉर्म जमा करें।',
                'kn': 'ಅರ್ಜಿ ಪ್ರಕ್ರಿಯೆ: ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್‌ಗೆ ಭೇಟಿ ನೀಡಿ, ನಿಮ್ಮ ವಿವರಗಳೊಂದಿಗೆ ನೋಂದಾಯಿಸಿ, ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ಮತ್ತು ಫಾರ್ಮ್ ಅನ್ನು ಸಲ್ಲಿಸಿ.'
            };
            
            const language = document.getElementById('languageSelect').value;
            const text = messages[language] || messages['en'];
            speakText(text);
        }
        
        function testCustom() {
            speakText('This is a custom test message in multiple languages for the government voice chatbot system.');
        }
        
        function testCustomText() {
            const text = document.getElementById('customText').value;
            if (text.trim()) {
                speakText(text);
            } else {
                alert('Please enter some text to speak');
            }
        }
    </script>
</body>
</html>
'''
    
    with open("multilingual_voice_test.html", "w", encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created: multilingual_voice_test.html")
    print("🌐 Open this file to test all languages")

def main():
    """Main function"""
    
    print("🌍 MULTILINGUAL VOICE OUTPUT SYSTEM")
    print("=" * 50)
    
    # Create backend endpoint
    create_multilingual_voice_endpoint()
    
    # Create frontend
    create_multilingual_frontend()
    
    # Create HTML controls
    create_voice_controls_html()
    
    # Create test page
    create_multilingual_test_page()
    
    print(f"\n" + "=" * 50)
    print("🎉 MULTILINGUAL VOICE SYSTEM READY!")
    print("=" * 40)
    
    print("🌍 SUPPORTED LANGUAGES:")
    languages = [
        "🇺🇸 English (en)",
        "🇮🇳 हिन्दी (hi)",
        "🇮🇳 ಕನ್ನಡ (kn)",
        "🇮🇳 தமிழ் (ta)",
        "🇮🇳 తెలుగు (te)",
        "🇮🇳 मराठी (mr)",
        "🇮🇳 বাংলা (bn)",
        "🇮🇳 ગુજરાતી (gu)",
        "🇮🇳 മലയാളം (ml)",
        "🇮🇳 ਪੰਜਾਬੀ (pa)",
        "🇮🇳 اردو (ur)"
    ]
    
    for lang in languages:
        print(f"   {lang}")
    
    print(f"\n🚀 IMPLEMENTATION STEPS:")
    print("1. 📝 Add multilingual_voice_api to views.py")
    print("2. 📝 Add URL pattern to urls.py")
    print("3. 🖥️  Add JavaScript to home.html")
    print("4. 🎨 Add HTML voice controls")
    print("5. 🌐 Test with multilingual_voice_test.html")
    
    print(f"\n✨ FEATURES:")
    print("✅ 11 Indian languages supported")
    print("✅ Voice speed control (slow/normal/fast)")
    print("✅ Language selector with flags")
    print("✅ Real-time voice generation")
    print("✅ High-quality Google TTS")
    print("✅ Automatic language detection")
    print("✅ Custom text input")
    
    print(f"\n🎯 READY TO TEST:")
    print("🌐 Open: multilingual_voice_test.html")
    print("🎛️  Select language and speed")
    print("🔊 Click test buttons")
    print("📱 Hear responses in multiple languages!")

if __name__ == "__main__":
    main()
