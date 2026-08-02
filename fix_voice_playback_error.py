#!/usr/bin/env python
"""
Voice Playback Error Fix
Comprehensive solution for voice playback issues
"""

import os
import webbrowser

def create_voice_error_fix():
    """Create a complete fix for voice playback errors"""
    
    print("🔧 VOICE PLAYBACK ERROR FIX")
    print("=" * 40)
    
    print("🚨 COMMON VOICE PLAYBACK ERRORS:")
    print("   1. Browser audio permissions blocked")
    print("   2. Network connection issues")
    print("   3. JavaScript errors in console")
    print("   4. Server endpoint not working")
    print("   5. Audio format compatibility")
    
    # Create enhanced JavaScript with error handling
    enhanced_js = '''
// Enhanced Multilingual Voice System with Error Handling
let multilingualVoiceEnabled = false;
let currentVoiceLanguage = 'en';
let voiceSpeed = 'normal';

// Toggle multilingual voice with enhanced error handling
function toggleMultilingualVoice() {
    try {
        multilingualVoiceEnabled = !multilingualVoiceEnabled;
        const voiceBtn = document.getElementById('multilingualVoiceBtn');
        const controlsPanel = document.getElementById('voiceControlsPanel');
        
        if (multilingualVoiceEnabled) {
            voiceBtn.innerHTML = '🔊 Multilingual Voice ON';
            voiceBtn.classList.add('voice-active');
            controlsPanel.style.display = 'block';
            log('🔊 Multilingual voice output enabled', 'bot');
            
            // Test audio permissions
            testAudioPermissions();
        } else {
            voiceBtn.innerHTML = '🔇 Multilingual Voice OFF';
            voiceBtn.classList.remove('voice-active');
            controlsPanel.style.display = 'none';
            log('🔇 Multilingual voice output disabled', 'bot');
        }
    } catch (error) {
        console.error('Toggle voice error:', error);
        log('❌ Error toggling voice: ' + error.message, 'bot');
    }
}

// Test audio permissions
function testAudioPermissions() {
    try {
        const audio = new Audio();
        audio.volume = 0.1;
        audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
        
        audio.play().then(() => {
            console.log('Audio permissions OK');
        }).catch((error) => {
            console.warn('Audio permission issue:', error);
            log('⚠️ Audio permissions may be blocked. Click anywhere on the page to enable.', 'bot');
        });
    } catch (error) {
        console.warn('Audio test error:', error);
    }
}

// Enhanced voice playback with retry mechanism
function playMultilingualVoiceResponse(text, language = null, retryCount = 0) {
    if (!multilingualVoiceEnabled) return;
    
    const maxRetries = 2;
    const targetLanguage = language || currentVoiceLanguage || 'en';
    
    // Show loading indicator
    log('🔄 Generating voice...', 'bot');
    
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
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status_code}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.audio_data) {
            try {
                // Create audio with enhanced error handling
                const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
                
                // Set audio properties
                audio.volume = 0.8;
                audio.playbackRate = 1.0;
                
                // Play with comprehensive error handling
                audio.play().then(() => {
                    const languageNames = {
                        'en': 'English', 'hi': 'हिन्दी', 'kn': 'ಕನ್ನಡ', 'ta': 'தமிழ்', 'te': 'తెలుగు',
                        'mr': 'मराठी', 'bn': 'বাংলা', 'gu': 'ગુજરાતી', 'ml': 'മലയാളം', 'pa': 'ਪੰਜਾਬੀ', 'ur': 'اردو'
                    };
                    const flags = {
                        'en': '🇺🇸', 'hi': '🇮🇳', 'kn': '🇮🇳', 'ta': '🇮🇳', 'te': '🇮🇳',
                        'mr': '🇮🇳', 'bn': '🇮🇳', 'gu': '🇮🇳', 'ml': '🇮🇳', 'pa': '🇮🇳', 'ur': '🇮🇳'
                    };
                    log(`🔊 Playing voice in ${flags[data.language]} ${data.language_display}`, 'bot');
                    
                    // Add audio event listeners
                    audio.addEventListener('ended', () => {
                        console.log('Voice playback completed');
                    });
                    
                    audio.addEventListener('error', (e) => {
                        console.error('Audio playback error:', e);
                        log('❌ Audio playback failed. Trying alternative...', 'bot');
                        
                        // Retry with different approach
                        if (retryCount < maxRetries) {
                            setTimeout(() => {
                                playMultilingualVoiceResponse(text, targetLanguage, retryCount + 1);
                            }, 1000);
                        } else {
                            log('❌ Voice failed after multiple attempts. Check browser audio permissions.', 'bot');
                        }
                    });
                    
                }).catch((playError) => {
                    console.error('Play error:', playError);
                    log('❌ Audio play failed: ' + playError.message, 'bot');
                    
                    // Try user interaction fallback
                    log('💡 Click anywhere on the page and try again', 'bot');
                });
                
            } catch (audioError) {
                console.error('Audio creation error:', audioError);
                log('❌ Failed to create audio: ' + audioError.message, 'bot');
            }
        } else {
            log(`❌ Voice generation failed: ${data.error}`, 'bot');
        }
    })
    .catch((error) => {
        console.error('Voice API error:', error);
        
        if (retryCount < maxRetries) {
            log(`🔄 Retrying voice generation (${retryCount + 1}/${maxRetries})...`, 'bot');
            setTimeout(() => {
                playMultilingualVoiceResponse(text, targetLanguage, retryCount + 1);
            }, 2000);
        } else {
            log('❌ Voice playback failed. Possible causes:', 'bot');
            log('• No internet connection', 'bot');
            log('• Server not responding', 'bot');
            log('• Browser audio permissions blocked', 'bot');
            log('• Try refreshing the page (Ctrl+F5)', 'bot');
        }
    });
}

// Change voice language with validation
function changeVoiceLanguage(language) {
    try {
        currentVoiceLanguage = language;
        const languageNames = {
            'en': 'English', 'hi': 'हिन्दी', 'kn': 'ಕನ್ನಡ', 'ta': 'தமிழ்', 'te': 'తెలుగు',
            'mr': 'मराठी', 'bn': 'বাংলा', 'gu': 'ગુજરાતી', 'ml': 'മലയാളം', 'pa': 'ਪੰਜਾਬੀ', 'ur': 'اردو'
        };
        const flags = {
            'en': '🇺🇸', 'hi': '🇮🇳', 'kn': '🇮🇳', 'ta': '🇮🇳', 'te': '🇮🇳',
            'mr': '🇮🇳', 'bn': '🇮🇳', 'gu': '🇮🇳', 'ml': '🇮🇳', 'pa': '🇮🇳', 'ur': '🇮🇳'
        };
        log(`🌍 Voice language changed to: ${flags[language]} ${languageNames[language]}`, 'bot');
    } catch (error) {
        console.error('Language change error:', error);
        log('❌ Error changing language: ' + error.message, 'bot');
    }
}

// Change voice speed with validation
function changeVoiceSpeed(speed) {
    try {
        voiceSpeed = speed;
        const speedIcons = { 'slow': '🐌', 'normal': '🚶', 'fast': '🏃' };
        log(`⚡ Voice speed changed to: ${speedIcons[speed]} ${speed}`, 'bot');
    } catch (error) {
        console.error('Speed change error:', error);
        log('❌ Error changing speed: ' + error.message, 'bot');
    }
}

// Enhanced log function with voice integration
function log(msg, cls = '') {
    const p = document.createElement('p');
    p.innerHTML = msg;
    if (cls) p.className = cls;
    document.getElementById('log').appendChild(p);
    document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
    
    // Enhanced voice playback with error handling
    if (cls === 'bot' && multilingualVoiceEnabled) {
        try {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = msg;
            const textContent = tempDiv.textContent || tempDiv.innerText || '';
            
            if (textContent.trim() && textContent.length > 10) {
                // Don't voice error messages or very short messages
                if (!msg.includes('❌') && !msg.includes('Error') && !msg.includes('failed')) {
                    setTimeout(() => {
                        playMultilingualVoiceResponse(textContent, currentVoiceLanguage);
                    }, 500);
                }
            }
        } catch (error) {
            console.error('Voice integration error:', error);
        }
    }
}

// Add page click handler for audio permissions
document.addEventListener('click', function() {
    if (multilingualVoiceEnabled) {
        // Enable audio context on user interaction
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
        } catch (error) {
            console.log('Audio context not available');
        }
    }
});

// Add keyboard shortcut for voice toggle
document.addEventListener('keydown', function(event) {
    // Ctrl+V to toggle voice
    if (event.ctrlKey && event.key === 'v') {
        event.preventDefault();
        toggleMultilingualVoice();
    }
});
'''
    
    with open("enhanced_voice_controls.js", "w", encoding='utf-8') as f:
        f.write(enhanced_js)
    
    print("✅ Created: enhanced_voice_controls.js")

def create_troubleshooting_guide():
    """Create a comprehensive troubleshooting guide"""
    
    guide = """
# Voice Playback Error Troubleshooting Guide

## 🚨 Immediate Fixes

### 1. Browser Audio Permissions
- **Click anywhere on the page** to enable audio
- **Allow audio permissions** when prompted
- **Check browser settings** for microphone/audio access

### 2. Network Connection
- **Check internet connection** (voice needs online TTS)
- **Try different network** if available
- **Refresh page** with Ctrl+F5

### 3. Server Issues
- **Restart Django server**: Ctrl+C, then `python manage.py runserver`
- **Check server console** for errors
- **Wait for full server startup**

## 🔧 Step-by-Step Troubleshooting

### Step 1: Basic Checks
```
1. Is the voice button green? (enabled)
2. Can you see language selector?
3. Is internet working?
4. Is browser volume up?
```

### Step 2: Browser Console Check
```
1. Press F12 (Developer Tools)
2. Go to Console tab
3. Look for red error messages
4. Common errors:
   - "Audio playback failed"
   - "Network error"
   - "Permission denied"
```

### Step 3: Test Voice Endpoint
```
1. Open new tab
2. Go to: http://127.0.0.1:8000/multilingual-voice-test.html
3. Test with different languages
4. Check if audio plays there
```

## 🌐 Browser-Specific Fixes

### Chrome/Edge
- Settings > Privacy > Microphone > Allow
- Clear cache: Ctrl+Shift+Del
- Disable extensions temporarily

### Firefox
- Settings > Privacy > Permissions > Microphone > Allow
- Refresh with Ctrl+F5
- Check about:config for media settings

### Safari
- Settings > Websites > Microphone > Allow
- Disable "Prevent cross-site tracking"
- Restart browser

## 🎯 Advanced Solutions

### 1. Replace with Enhanced JavaScript
Copy the enhanced_voice_controls.js content into your home.html

### 2. Add Audio Context
```javascript
// Add to page load
window.addEventListener('load', function() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    audioContext.resume();
});
```

### 3. Test with Simple Audio
```javascript
// Test basic audio
const testAudio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
testAudio.play();
```

## 📞 Support Commands

### Test Voice Directly
```bash
curl -X POST http://127.0.0.1:8000/multilingual-voice/ \\
  -H "Content-Type: application/json" \\
  -d '{"text":"Hello test","language":"en","speed":"normal"}'
```

### Check Server Status
```bash
python manage.py runserver --debug
```

## 🎉 Expected Working State

When voice is working:
- ✅ Voice button is green
- ✅ Language selector visible
- ✅ Console shows no errors
- ✅ Audio plays when bot responds
- ✅ Voice plays in selected language
- ✅ Speed control works

## 🔄 Final Resort

If nothing works:
1. **Clear all browser data**
2. **Try different browser**
3. **Check system audio drivers**
4. **Restart computer**
5. **Reinstall voice dependencies**
"""
    
    with open("VOICE_TROUBLESHOOTING.md", "w", encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Created: VOICE_TROUBLESHOOTING.md")

def create_quick_test_page():
    """Create a simple test page for voice"""
    
    test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Error Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        button { padding: 10px 20px; margin: 10px; font-size: 16px; cursor: pointer; }
        .status { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>🎤 Voice Error Test Page</h1>
    
    <button onclick="testBasicAudio()">1. Test Basic Audio</button>
    <button onclick="testVoiceEndpoint()">2. Test Voice Endpoint</button>
    <button onclick="testFullVoice()">3. Test Full Voice System</button>
    
    <div id="status" class="status">Click a test button to begin...</div>
    
    <script>
        function updateStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.innerHTML = message;
            status.className = isError ? 'status error' : 'status success';
        }
        
        function testBasicAudio() {
            updateStatus('Testing basic audio...');
            
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
                
                audio.play().then(() => {
                    updateStatus('✅ Basic audio working! Browser can play sound.');
                }).catch((error) => {
                    updateStatus('❌ Basic audio failed: ' + error.message + '<br>💡 Click anywhere on the page and try again.', true);
                });
                
            } catch (error) {
                updateStatus('❌ Audio creation failed: ' + error.message, true);
            }
        }
        
        function testVoiceEndpoint() {
            updateStatus('Testing voice endpoint...');
            
            fetch('/multilingual-voice/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'text': 'Hello, this is a test.',
                    'language': 'en',
                    'speed': 'normal'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatus('✅ Voice endpoint working! Audio size: ' + data.audio_size + ' bytes');
                } else {
                    updateStatus('❌ Voice endpoint failed: ' + data.error, true);
                }
            })
            .catch(error => {
                updateStatus('❌ Voice endpoint error: ' + error.message, true);
            });
        }
        
        function testFullVoice() {
            updateStatus('Testing full voice system...');
            
            fetch('/multilingual-voice/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'text': 'Full voice system test successful!',
                    'language': 'en',
                    'speed': 'normal'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.audio_data) {
                    try {
                        const audio = new Audio('data:audio/mp3;base64,' + data.audio_data);
                        audio.play().then(() => {
                            updateStatus('🎉 FULL VOICE SYSTEM WORKING!<br>✅ Endpoint: OK<br>✅ Audio: Playing<br>✅ Language: ' + data.language_display);
                        }).catch((error) => {
                            updateStatus('❌ Voice playback failed: ' + error.message + '<br>💡 Try clicking anywhere on the page first.', true);
                        });
                    } catch (error) {
                        updateStatus('❌ Audio creation failed: ' + error.message, true);
                    }
                } else {
                    updateStatus('❌ Voice system failed: ' + data.error, true);
                }
            })
            .catch(error => {
                updateStatus('❌ Voice system error: ' + error.message, true);
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
        
        // Enable audio on page load
        document.addEventListener('click', function() {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
        });
    </script>
</body>
</html>
"""
    
    with open("voice_error_test.html", "w", encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created: voice_error_test.html")

def main():
    """Main fix function"""
    
    print("🔧 VOICE PLAYBACK ERROR - COMPREHENSIVE FIX")
    print("=" * 55)
    
    print("🚨 COMMON CAUSES OF VOICE PLAYBACK ERRORS:")
    print("   1. Browser audio permissions blocked")
    print("   2. No user interaction (required for audio)")
    print("   3. Network connectivity issues")
    print("   4. Server endpoint not responding")
    print("   5. JavaScript errors in browser")
    
    # Create enhanced JavaScript
    create_voice_error_fix()
    
    # Create troubleshooting guide
    create_troubleshooting_guide()
    
    # Create test page
    create_quick_test_page()
    
    print(f"\n🎯 IMMEDIATE FIXES TO TRY:")
    print("=" * 30)
    
    print("1. 🖱️  CLICK ANYWHERE on the page to enable audio")
    print("2. 🔄 Refresh page with Ctrl+F5")
    print("3. 🔊 Check browser volume is up")
    print("4. 🌐 Check internet connection")
    print("5. 🎤 Restart server: python manage.py runserver")
    
    print(f"\n🧪 TEST YOUR VOICE:")
    print("=" * 20)
    print("1. Open: voice_error_test.html")
    print("2. Click 'Test Basic Audio'")
    print("3. Click 'Test Voice Endpoint'")
    print("4. Click 'Test Full Voice System'")
    
    print(f"\n📁 FILES CREATED:")
    print("   • enhanced_voice_controls.js - Better error handling")
    print("   • VOICE_TROUBLESHOOTING.md - Complete guide")
    print("   • voice_error_test.html - Quick test page")
    
    print(f"\n🎉 EXPECTED RESULT:")
    print("After fixes, voice should work with:")
    print("   ✅ Green voice button")
    print("   ✅ Audio plays automatically")
    print("   ✅ Multiple languages")
    print("   ✅ Speed control")
    print("   ✅ No console errors")

if __name__ == "__main__":
    main()
