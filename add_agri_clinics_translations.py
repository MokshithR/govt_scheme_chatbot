"""
Add Kannada translations for Agri-Clinics scheme to database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme

# Find the Agri-Clinics scheme
scheme = GovernmentScheme.objects.filter(title__icontains='Agri-Clinics').first()

if not scheme:
    print("❌ Agri-Clinics scheme not found!")
    exit(1)

print(f"✓ Found scheme: {scheme.title} (ID: {scheme.id})")

# Add Kannada translations for all fields
scheme.short_description_translations = {
    'kn': 'ಕ್ಲಿನಿಕ್‌ಗಳ ಮೂಲಕ ರೈತರಿಗೆ ಕೃಷಿ ಸಲಹೆ ಮತ್ತು ವ್ಯವಸಾಯ ಸೇವೆಗಳನ್ನು ಒದಗಿಸಲು ಕೃಷಿ ಪದವೀಧರರಿಗೆ ಸ್ವಯಂ ಉದ್ಯೋಗ ಯೋಜನೆ.',
    'hi': 'कृषि स्नातकों को किसानों को क्लीनिक के माध्यम से कृषि सलाह और व्यावसायिक सेवाएं प्रदान करने के लिए स्व-रोजगार योजना।'
}

scheme.description_translations = {
    'kn': '''ಈ ಯೋಜನೆಯು ಕೃಷಿ ಉತ್ಪಾದಕತೆ ಮತ್ತು ಆದಾಯವನ್ನು ಹೆಚ್ಚಿಸಲು ರೈತರಿಗೆ ಸಲಹಾ ಮತ್ತು ವಿಸ್ತರಣೆ ಸೇವೆಗಳನ್ನು ಒದಗಿಸುವ ತಜ್ಞ ಕೃಷಿ-ಉದ್ಯಮಿಗಳನ್ನು ರಚಿಸುವ ಗುರಿಯನ್ನು ಹೊಂದಿದೆ. ಇದು ಕೃಷಿ ಪದವೀಧರರಿಗೆ ಕೃಷಿ-ಕ್ಲಿನಿಕ್/ಕೃಷಿ-ವ್ಯವಸಾಯ ಕೇಂದ್ರಗಳನ್ನು ಸ್ಥಾಪಿಸಲು ತರಬೇತಿ ನೀಡುತ್ತದೆ, ರೈತರಿಗೆ ಕೃಷಿ ಪದ್ಧತಿಗಳು, ಬೆಳೆ ರಕ್ಷಣೆ, ಮಣ್ಣಿನ ಆರೋಗ್ಯ, ಪಶು ಆರೋಗ್ಯ, ಮಾರುಕಟ್ಟೆ ಪ್ರವೃತ್ತಿಗಳು ಮತ್ತು ಇತರ ಸಂಬಂಧಿತ ಸೇವೆಗಳ ಬಗ್ಗೆ ತಜ್ಞ ಸಲಹೆಯನ್ನು ನೀಡುತ್ತದೆ. ಈ ಯೋಜನೆಯು ನಿರುದ್ಯೋಗಿ ಕೃಷಿ ಪದವೀಧರರಿಗೆ ಸ್ವಯಂ ಉದ್ಯೋಗ ಅವಕಾಶಗಳನ್ನು ಸೃಷ್ಟಿಸುವ ಮೂಲಕ ಬೆಂಬಲಿಸುತ್ತದೆ, ಆರ್ಥಿಕ ಮತ್ತು ಸಾಲ-ಸಂಯೋಜಿತ ಸಬ್ಸಿಡಿಗಳಿಂದ ಪೂರಕವಾಗಿದೆ.''',
    'hi': 'यह योजना कृषि उत्पादकता और आय बढ़ाने के लिए किसानों को सलाहकार और विस्तार सेवाएं प्रदान करने वाले विशेषज्ञ कृषि-उद्यमियों को बनाने का लक्ष्य रखती है।'
}

scheme.eligibility_criteria_translations = {
    'kn': 'ನಿರುದ್ಯೋಗಿ ಕೃಷಿ ಪದವೀಧರರು, ಡಿಪ್ಲೊಮಾ ಹೊಂದಿರುವವರು, ಕೃಷಿ ಮತ್ತು ಸಂಬಂಧಿತ ಕ್ಷೇತ್ರಗಳಲ್ಲಿ ಮಧ್ಯಂತರರು; ವಯಸ್ಸು ಸಾಮಾನ್ಯವಾಗಿ 18 ರಿಂದ 60 ವರ್ಷಗಳು.',
    'hi': 'बेरोजगार कृषि स्नातक, डिप्लोमा धारक, कृषि और संबद्ध क्षेत्रों में इंटरमीडिएट; आयु आमतौर पर 18 से 60 वर्ष।'
}

scheme.benefits_translations = {
    'kn': '''ತರಬೇತಿ ಮತ್ತು ಕೌಶಲ್ಯ ಅಭಿವೃದ್ಧಿ ಉಚಿತವಾಗಿ.
ಆರ್ಥಿಕ ನೆರವು ಸಾಲ-ಸಂಯೋಜಿತ ಸಬ್ಸಿಡಿ ಸೇರಿದಂತೆ (ವ್ಯಕ್ತಿಗಳಿಗೆ ₹20 ಲಕ್ಷದವರೆಗೆ ಸಾಲ, ಗುಂಪುಗಳಿಗೆ ₹1 ಕೋಟಿ).
ತಜ್ಞ ಕೃಷಿ-ಉದ್ಯಮಿತ್ವ ಮತ್ತು ವ್ಯಾಪಾರ ಸ್ಥಾಪನೆಗೆ ಬೆಂಬಲ.
ಹ್ಯಾಂಡ್‌ಹೋಲ್ಡಿಂಗ್ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ ಬೆಂಬಲ.''',
    'hi': '''निःशुल्क प्रशिक्षण और कौशल विकास।
क्रेडिट-लिंक्ड सब्सिडी सहित वित्तीय सहायता (व्यक्तियों के लिए ₹20 लाख तक ऋण, समूहों के लिए ₹1 करोड़)।
विशेषज्ञ कृषि-उद्यमिता और व्यवसाय स्थापना के लिए समर्थन।
हैंडहोल्डिंग और मेंटरिंग समर्थन।'''
}

scheme.financial_assistance_translations = {
    'kn': 'NABARD ಮೂಲಕ ಸಾಲ-ಸಂಯೋಜಿತ ಬ್ಯಾಕ್-ಎಂಡ್ ಸಂಯೋಜಿತ ಸಬ್ಸಿಡಿ; MUDRA ನಂತಹ ಯೋಜನೆಗಳ ಅಡಿಯಲ್ಲಿ ಸಾಲ ನಿಬಂಧನೆಗಳು.',
    'hi': 'NABARD के माध्यम से क्रेडिट-लिंक्ड बैक-एंड कंपोजिट सब्सिडी; MUDRA जैसी योजनाओं के तहत ऋण प्रावधान।'
}

scheme.application_process_translations = {
    'kn': '''ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ಮೂಲಕ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ: agriclinics.net
ಅಭ್ಯರ್ಥಿಗಳು ನೋಡಲ್ ತರಬೇತಿ ಸಂಸ್ಥೆಗಳ (NTIs) ಮೂಲಕ ಸ್ಕ್ರೀನಿಂಗ್ ಮತ್ತು ಆಯ್ಕೆಗೆ ಒಳಗಾಗುತ್ತಾರೆ
MANAGE ಮೂಲಕ ಕಡ್ಡಾಯ ತರಬೇತಿ ಮತ್ತು ಪ್ರಮಾಣೀಕರಣ''',
    'hi': '''आधिकारिक पोर्टल के माध्यम से ऑनलाइन आवेदन करें: agriclinics.net
उम्मीदवार नोडल प्रशिक्षण संस्थानों (NTIs) के माध्यम से स्क्रीनिंग और चयन से गुजरते हैं
MANAGE द्वारा अनिवार्य प्रशिक्षण और प्रमाणन'''
}

# Save the scheme
scheme.save()

print("\n✅ Successfully added Kannada and Hindi translations!")
print(f"\nTranslated fields:")
print(f"  ✓ Short Description")
print(f"  ✓ Full Description")
print(f"  ✓ Eligibility Criteria")
print(f"  ✓ Benefits")
print(f"  ✓ Financial Assistance")
print(f"  ✓ Application Process")

print(f"\nNow visit: http://localhost:8000/scheme/{scheme.id}/?lang=kn")
print("All content should now display in Kannada!")
