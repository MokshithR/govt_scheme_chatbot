
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
