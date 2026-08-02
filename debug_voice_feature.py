#!/usr/bin/env python
"""
Voice Feature Debug - Find and fix issues
"""

import requests
import json

def debug_voice_issues():
    """Debug what's not working with the voice feature"""
    
    print("🔧 VOICE FEATURE DEBUG")
    print("=" * 30)
    
    issues_found = []
    
    # Test 1: Check server
    print("1. 🔍 Checking server status...")
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server error: {response.status_code}")
            issues_found.append("Server not responding correctly")
    except:
        print("   ❌ Server not running")
        issues_found.append("Server not running")
    
    # Test 2: Check voice endpoint
    print("\n2. 🎤 Checking voice endpoint...")
    try:
        test_data = {
            'text': 'Hello test',
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
                print("   ✅ Voice endpoint working")
            else:
                print(f"   ❌ Voice generation failed: {data.get('error')}")
                issues_found.append("Voice generation failed")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            if response.status_code == 404:
                print("   💡 URL not found - server needs restart")
                issues_found.append("Voice endpoint not found - restart server")
            elif response.status_code == 500:
                print("   💡 Server error - check backend code")
                issues_found.append("Server error in voice endpoint")
                
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        issues_found.append("Cannot connect to voice endpoint")
    
    # Test 3: Check HTML content
    print("\n3. 📄 Checking HTML content...")
    try:
        response = requests.get('http://127.0.0.1:8000/')
        html = response.text
        
        required_elements = [
            'multilingualVoiceBtn',
            'toggleMultilingualVoice()',
            'playMultilingualVoiceResponse(',
            'voiceLanguageSelect',
            'multilingual-voice-controls'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"   ❌ Missing elements: {missing_elements}")
            issues_found.append(f"HTML missing: {', '.join(missing_elements)}")
        else:
            print("   ✅ All required HTML elements found")
            
    except Exception as e:
        print(f"   ❌ Error checking HTML: {e}")
        issues_found.append("Cannot check HTML content")
    
    return issues_found

def create_fix_script():
    """Create a script to fix common issues"""
    
    print("\n🔧 CREATING FIX SCRIPT...")
    
    fix_script = '''
# Voice Feature Fix Script
# Run these commands to fix common issues

echo "🔧 Fixing Voice Feature Issues..."

# 1. Check if server is running
echo "1. Checking server status..."
curl -s http://127.0.0.1:8000/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Server is running"
else
    echo "❌ Server not running - please start with: python manage.py runserver"
fi

# 2. Test voice endpoint
echo "2. Testing voice endpoint..."
curl -s -X POST http://127.0.0.1:8000/multilingual-voice/ \\
  -H "Content-Type: application/json" \\
  -d '{"text":"test","language":"en","speed":"normal"}' | head -20

# 3. Check if URLs are properly configured
echo "3. Checking URL configuration..."
python manage.py show_urls | grep multilingual

echo "🔧 Fix complete!"
'''
    
    with open("fix_voice_feature.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo 🔧 Fixing Voice Feature Issues...\n\n")
        f.write("echo 1. Testing server connection...\n")
        f.write("curl -s http://127.0.0.1:8000/ >nul 2>&1\n")
        f.write("if %errorlevel% equ 0 (\n")
        f.write("    echo ✅ Server is running\n")
        f.write(") else (\n")
        f.write("    echo ❌ Server not running\n")
        f.write("    echo 💡 Start with: python manage.py runserver\n")
        f.write(")\n\n")
        f.write("echo 2. Testing voice endpoint...\n")
        f.write("curl -s -X POST http://127.0.0.1:8000/multilingual-voice/ -H \"Content-Type: application/json\" -d \"{\\\"text\\\":\\\"test\\\",\\\"language\\\":\\\"en\\\",\\\"speed\\\":\\\"normal\\\"}\"\n\n")
        f.write("echo 🔧 Test complete!\n")
        f.write("pause\n")
    
    print("✅ Created: fix_voice_feature.bat")

def show_solutions():
    """Show solutions for common issues"""
    
    print("\n💡 COMMON SOLUTIONS")
    print("=" * 25)
    
    print("🔄 1. SERVER RESTART (Most Common Fix):")
    print("   • Stop server: Ctrl+C")
    print("   • Restart: python manage.py runserver")
    print("   • Wait for server to fully load")
    
    print("\n🌐 2. BROWSER ISSUES:")
    print("   • Clear cache: Ctrl+F5")
    print("   • Try different browser")
    print("   • Check browser console for errors")
    
    print("\n🔗 3. NETWORK ISSUES:")
    print("   • Check internet connection")
    print("   • Voice needs internet for Google TTS")
    print("   • Try again with stable connection")
    
    print("\n📝 4. CODE ISSUES:")
    print("   • Check views.py has multilingual_voice_api")
    print("   • Check urls.py has multilingual-voice/ path")
    print("   • Check home.html has voice controls")
    
    print("\n🎤 5. VOICE SPECIFIC:")
    print("   • Make sure voice is enabled (green button)")
    print("   • Select correct language")
    print("   • Check browser volume")
    print("   • Allow audio permissions")

def main():
    """Main debug function"""
    
    print("🔧 VOICE FEATURE DEBUG & FIX")
    print("=" * 40)
    
    # Debug current issues
    issues = debug_voice_issues()
    
    # Show results
    print(f"\n📊 DEBUG RESULTS:")
    print(f"   Issues found: {len(issues)}")
    
    if issues:
        print("\n❌ ISSUES DETECTED:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✅ No issues found - voice feature should be working!")
    
    # Create fix script
    create_fix_script()
    
    # Show solutions
    show_solutions()
    
    print(f"\n" + "=" * 40)
    print("🎯 QUICK FIXES TO TRY:")
    print("=" * 30)
    
    print("1. 🔄 Restart Django server (most common fix)")
    print("2. 🌐 Refresh browser with Ctrl+F5")
    print("3. 🎤 Check if voice button is green (enabled)")
    print("4. 🌍 Select a language and try typing a message")
    print("5. 🔊 Check browser volume and audio permissions")
    
    print(f"\n📁 Created helper file: fix_voice_feature.bat")
    print("   Run this file to quickly test the voice feature")

if __name__ == "__main__":
    main()
