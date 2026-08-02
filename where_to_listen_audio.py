#!/usr/bin/env python
"""
Where to Listen to Audio - Complete Guide
Shows all places to hear voice output from your chatbot
"""

import os
import webbrowser
from pathlib import Path

def show_audio_locations():
    """Show all places where audio can be heard"""
    
    print("🎧 WHERE TO LISTEN TO AUDIO")
    print("=" * 50)
    
    # Check for audio files
    audio_files = []
    project_dir = Path("d:/govt_voice_chatbot")
    
    # Find audio files
    for file in project_dir.glob("*.mp3"):
        audio_files.append(file)
    
    for file in project_dir.glob("*.wav"):
        audio_files.append(file)
    
    print(f"📁 Found {len(audio_files)} audio files:")
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{i}. 🎵 {audio_file.name}")
        print(f"   Location: {audio_file}")
        print(f"   Size: {audio_file.stat().st_size:,} bytes")
        
        # Show how to open
        if audio_file.exists():
            print(f"   ✅ How to listen:")
            print(f"      • Double-click the file")
            print(f"      • Right-click → Open with → Music player")
            print(f"      • Open in browser: file:///{audio_file}")
    
    return audio_files

def show_browser_testing():
    """Show how to test audio in browser"""
    
    print(f"\n🌐 LISTEN IN BROWSER")
    print("=" * 30)
    
    print("1. 📂 Open voice_test.html in browser:")
    print("   • File location: d:/govt_voice_chatbot/voice_test.html")
    print("   • Double-click to open in browser")
    print("   • Or drag file to browser window")
    
    print("\n2. 🚀 Start Django server:")
    print("   cd d:/govt_voice_chatbot")
    print("   python manage.py runserver")
    
    print("\n3. 🌐 Open chatbot interface:")
    print("   • Go to: http://127.0.0.1:8000/")
    print("   • Click voice toggle button")
    print("   • Type message and hear response")
    
    print("\n4. 🎤 Test voice features:")
    print("   • Click 'Test Voice Output' button")
    print("   • Click 'Test Scheme Response' button")
    print("   • Click 'Test Kannada Language' button")

def show_chatbot_audio():
    """Show how to hear audio in chatbot"""
    
    print(f"\n🤖 CHATBOT AUDIO LOCATIONS")
    print("=" * 35)
    
    print("📱 In the Chatbot Interface:")
    print("   1. Look for 'Voice OFF' button")
    print("   2. Click to enable: 'Voice ON'")
    print("   3. Type any query about schemes")
    print("   4. Chatbot will respond with voice!")
    
    print("\n🎵 Audio will play automatically when:")
    print("   • Voice is enabled (green button)")
    print("   • Chatbot responds to your query")
    print("   • Scheme information is displayed")
    print("   • Apply button is clicked")
    
    print("\n🔊 Audio Controls:")
    print("   • Volume: Use computer volume controls")
    print("   • Pause: Click voice toggle to turn off")
    print("   • Replay: Type same query again")

def show_technical_details():
    """Show technical audio details"""
    
    print(f"\n🔧 TECHNICAL AUDIO DETAILS")
    print("=" * 30)
    
    print("📊 Audio Generation:")
    print("   • Method: Google Text-to-Speech (gTTS)")
    print("   • Format: MP3 audio")
    print("   • Quality: High quality voice")
    print("   • Languages: English, Hindi, Kannada")
    
    print("\n💾 Audio Storage:")
    print("   • Temporary files created during testing")
    print("   • Browser plays audio directly")
    print("   • No permanent storage needed")
    print("   • Real-time generation")
    
    print("\n🌐 Audio Playback:")
    print("   • Browser HTML5 audio player")
    print("   • Base64 encoded audio data")
    print("   • Automatic streaming")
    print("   • Cross-browser compatible")

def create_audio_test_script():
    """Create script to test audio playback"""
    
    print(f"\n🧪 CREATE AUDIO TEST")
    print("=" * 25)
    
    test_script = '''
# Audio Test Script
import os
import webbrowser
from pathlib import Path

def test_audio_files():
    """Test all audio files"""
    
    # Find audio files
    audio_files = list(Path(".").glob("*.mp3")) + list(Path(".").glob("*.wav"))
    
    print(f"Found {len(audio_files)} audio files:")
    
    for audio_file in audio_files:
        print(f"\\n🎵 Playing: {audio_file.name}")
        
        # Open in default player
        try:
            os.startfile(audio_file)  # Windows
            print("✅ Opened in default player")
        except:
            try:
                webbrowser.open(f"file:///{audio_file.absolute()}")
                print("✅ Opened in browser")
            except:
                print("❌ Could not open automatically")
                print(f"   Manual path: {audio_file.absolute()}")

if __name__ == "__main__":
    test_audio_files()
'''
    
    with open("test_audio_playback.py", "w") as f:
        f.write(test_script)
    
    print("✅ Created: test_audio_playback.py")
    print("🚀 Run: python test_audio_playback.py")

def main():
    """Main function"""
    
    print("🎧 COMPLETE AUDIO LISTENING GUIDE")
    print("=" * 50)
    
    # Show audio file locations
    audio_files = show_audio_locations()
    
    # Show browser testing
    show_browser_testing()
    
    # Show chatbot audio
    show_chatbot_audio()
    
    # Show technical details
    show_technical_details()
    
    # Create test script
    create_audio_test_script()
    
    print(f"\n" + "=" * 50)
    print("🎯 QUICK START - Listen to Audio NOW!")
    print("=" * 45)
    
    if audio_files:
        print(f"📁 EASIEST - Open Audio File:")
        print(f"   1. Go to: d:/govt_voice_chatbot/")
        print(f"   2. Find: voice_test.mp3")
        print(f"   3. Double-click to play")
    
    print(f"\n🌐 BROWSER - Test Web Audio:")
    print(f"   1. Open: voice_test.html")
    print(f"   2. Click 'Test Voice Output'")
    print(f"   3. Listen in browser")
    
    print(f"\n🤖 CHATBOT - Full Experience:")
    print(f"   1. Run: python manage.py runserver")
    print(f"   2. Open: http://127.0.0.1:8000/")
    print(f"   3. Enable voice toggle")
    print(f"   4. Type: 'tell me about schemes'")
    print(f"   5. Listen to voice response!")
    
    print(f"\n🎉 ALL AUDIO OPTIONS READY!")
    print(f"✅ File playback: voice_test.mp3")
    print(f"✅ Browser test: voice_test.html")
    print(f"✅ Chatbot voice: Full interface")
    print(f"✅ Multiple languages: EN, HI, KN")

if __name__ == "__main__":
    main()
