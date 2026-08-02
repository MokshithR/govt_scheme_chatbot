
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
curl -X POST http://127.0.0.1:8000/multilingual-voice/ \
  -H "Content-Type: application/json" \
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
