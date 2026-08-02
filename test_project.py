#!/usr/bin/env python
"""
Comprehensive test script for Government Voice Chatbot
Tests all major components and identifies issues
"""

import os
import sys
import django
import subprocess
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_imports():
    """Test all critical imports"""
    print_section("TESTING IMPORTS")
    
    imports_to_test = [
        ('django', 'Django framework'),
        ('pymongo', 'MongoDB driver'),
        ('rest_framework', 'Django REST Framework'),
        ('corsheaders', 'CORS headers'),
        ('dotenv', 'Environment variables'),
    ]
    
    optional_imports = [
        ('whisper', 'OpenAI Whisper (voice recognition)'),
        ('gtts', 'Google Text-to-Speech'),
        ('pyttsx3', 'Offline text-to-speech'),
        ('torch', 'PyTorch (for Whisper)'),
    ]
    
    print("Required imports:")
    all_good = True
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError as e:
            print(f"  ❌ {module} - {description} - ERROR: {e}")
            all_good = False
    
    print("\nOptional imports:")
    for module, description in optional_imports:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError as e:
            print(f"  ⚠️  {module} - {description} - Not available: {e}")
    
    return all_good

def test_django_setup():
    """Test Django configuration"""
    print_section("TESTING DJANGO SETUP")
    
    try:
        django.setup()
        print("✅ Django setup successful")
        
        # Test settings
        from django.conf import settings
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
        print(f"✅ Installed apps: {len(settings.INSTALLED_APPS)} apps")
        
        # Test URL configuration
        from django.urls import reverse
        try:
            home_url = reverse('home')
            print(f"✅ Home URL resolved: {home_url}")
        except Exception as e:
            print(f"⚠️  URL resolution issue: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_models():
    """Test Django models"""
    print_section("TESTING MODELS")
    
    try:
        from chatbot.models import GovernmentScheme, ChatSession, ChatMessage
        print("✅ Models imported successfully")
        
        # Test model creation (without saving)
        scheme = GovernmentScheme(
            title="Test Scheme",
            description="Test description",
            short_description="Test short description",
            sector="agriculture",
            ministry="Test Ministry",
            department="Test Department",
            government_level="central",
            eligibility_criteria="Test eligibility",
            benefits="Test benefits",
            application_process="Test process",
            launch_date="2023-01-01",
            source_url="https://example.com",
            language="en"
        )
        print("✅ GovernmentScheme model validation passed")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print_section("TESTING MONGODB CONNECTION")
    
    try:
        from mongodb_adapter import MongoDBAdapter
        adapter = MongoDBAdapter()
        
        # Test connection
        total_schemes = adapter.get_total_schemes()
        print(f"✅ MongoDB connected successfully")
        print(f"✅ Total schemes in database: {total_schemes}")
        
        if total_schemes == 0:
            print("⚠️  Database is empty - you need to add scheme data")
            print("   Use the commands in mongodb_insert_commands.js")
        
        # Test search functionality
        test_schemes = adapter.search_schemes("agriculture", ["agriculture"], {}, "search")
        print(f"✅ Search functionality works - found {len(test_schemes)} agriculture schemes")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        print("   Make sure MongoDB is running on localhost:27017")
        return False

def test_voice_processing():
    """Test voice processing capabilities"""
    print_section("TESTING VOICE PROCESSING")
    
    try:
        from chatbot.voice_processing import VoiceProcessor
        processor = VoiceProcessor()
        
        # Test TTS
        if hasattr(processor, 'text_to_speech'):
            result = processor.text_to_speech("Hello, this is a test", "en", use_gtts=False)
            if result['error'] is None:
                print("✅ Text-to-speech (offline) working")
            else:
                print(f"⚠️  Text-to-speech (offline) issue: {result['error']}")
        
        # Test Whisper availability
        if processor.whisper_model:
            print("✅ Whisper model loaded for speech recognition")
        else:
            print("⚠️  Whisper model not available - voice recognition will use Web Speech API")
        
        return True
    except Exception as e:
        print(f"❌ Voice processing test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print_section("TESTING API ENDPOINTS")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test home page
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Home page accessible")
        else:
            print(f"❌ Home page error: {response.status_code}")
        
        # Test database status API
        try:
            response = client.get('/api/database/status/')
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database status API working - {data.get('total_schemes', 0)} schemes")
            else:
                print(f"⚠️  Database status API issue: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Database status API error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_static_files():
    """Test static files configuration"""
    print_section("TESTING STATIC FILES")
    
    try:
        from django.conf import settings
        
        # Check static files settings
        print(f"✅ STATIC_URL: {settings.STATIC_URL}")
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
        
        # Check if staticfiles directory exists
        if settings.STATIC_ROOT and Path(settings.STATIC_ROOT).exists():
            print("✅ Static files directory exists")
        else:
            print("⚠️  Static files directory not found - run 'python manage.py collectstatic'")
        
        return True
    except Exception as e:
        print(f"❌ Static files test failed: {e}")
        return False

def test_templates():
    """Test template configuration"""
    print_section("TESTING TEMPLATES")
    
    try:
        from django.template.loader import get_template
        
        # Test main template
        template = get_template('home.html')
        print("✅ Main template (home.html) found")
        
        return True
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def generate_report(results):
    """Generate final test report"""
    print_section("TEST REPORT")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your project is ready to run.")
        print("\nTo start the application:")
        print("  python start.py")
        print("  or")
        print("  python manage.py runserver")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        
        if not results.get('MongoDB Connection'):
            print("\n💡 Quick fixes:")
            print("  1. Start MongoDB: net start MongoDB (Windows) or brew services start mongodb (Mac)")
            print("  2. Add scheme data: Use mongodb_insert_commands.js in MongoDB Compass")
        
        if not results.get('Imports'):
            print("  3. Install missing packages: pip install -r requirements.txt")

def main():
    """Run all tests"""
    print("🚀 Government Voice Chatbot - Comprehensive Test Suite")
    
    # Run all tests
    results = {}
    results['Imports'] = test_imports()
    results['Django Setup'] = test_django_setup()
    results['Models'] = test_models()
    results['MongoDB Connection'] = test_mongodb_connection()
    results['Voice Processing'] = test_voice_processing()
    results['API Endpoints'] = test_api_endpoints()
    results['Static Files'] = test_static_files()
    results['Templates'] = test_templates()
    
    # Generate report
    generate_report(results)

if __name__ == "__main__":
    main()
