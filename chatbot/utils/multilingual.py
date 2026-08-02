"""
Multilingual Support Utilities
==============================
Complete language detection and translation system for Government Scheme Chatbot.

Supported Languages:
- English (en)
- Kannada (kn)
- Hindi (hi)
"""

import os
import logging
from typing import Optional, Dict
import google.generativeai as genai

logger = logging.getLogger(__name__)


def detect_user_language(text: str) -> str:
    """
    Detect language from user input using langdetect.
    
    Args:
        text: User input text
        
    Returns:
        Language code: 'kn' (Kannada), 'hi' (Hindi), 'en' (English - default)
    """
    if not text or len(text.strip()) < 2:
        return 'en'
    
    try:
        from langdetect import detect, DetectorFactory
        # Set seed for consistent results
        DetectorFactory.seed = 0
        
        detected = detect(text.strip())
        
        # Map language codes
        if detected == 'kn':
            return 'kn'  # Kannada
        elif detected == 'hi':
            return 'hi'  # Hindi
        else:
            return 'en'  # Default to English
            
    except Exception as e:
        logger.warning(f"Language detection failed: {e}. Defaulting to English.")
        return 'en'


def translate_with_gemini(text: str, target_language: str) -> str:
    """
    Translate text to target language using Gemini API.
    
    Args:
        text: Text to translate (in English)
        target_language: Target language code ('kn' or 'hi')
        
    Returns:
        Translated text (plain text, NO markdown)
    """
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not set. Returning original text.")
            return text
        
        genai.configure(api_key=api_key)
        
        # Language name mapping
        language_names = {
            'kn': 'Kannada',
            'hi': 'Hindi'
        }
        
        target_lang_name = language_names.get(target_language, 'English')
        
        system_prompt = f"""You are a professional translator for government schemes.

CRITICAL RULES:
1. Translate the text into natural, fluent {target_lang_name}
2. Keep all field labels (Scheme Name:, Sector:, etc.) intact
3. Translate ONLY the values, NOT the labels
4. NO markdown formatting (no **, *, #, -, •)
5. NO bullets, NO headings, NO bold text
6. Maintain the exact same structure and line breaks
7. Keep separator lines (----) as-is
8. Translate scheme names accurately
9. Use formal, respectful language
10. Keep URLs and numbers unchanged"""
        
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        prompt = f"Translate this text into natural {target_lang_name}. Preserve structure and field labels:\n\n{text}"
        
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,  # Low temperature for consistent translation
                'max_output_tokens': 2000,
            }
        )
        
        translated = response.text.strip()
        
        # Remove any markdown that Gemini might add
        from chatbot.utils.formatting import sanitize_markdown
        translated = sanitize_markdown(translated)
        
        return translated
        
    except Exception as e:
        logger.error(f"Translation failed: {e}. Returning original text.")
        return text


def get_friendly_greeting(language: str) -> str:
    """
    Get friendly greeting message in specified language.
    
    Args:
        language: Language code ('en', 'kn', 'hi')
        
    Returns:
        Greeting message in specified language
    """
    greetings = {
        'en': "Hello! I'm your Government Schemes Assistant. Which scheme would you like to know about?",
        'kn': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಯೋಜನೆ ಸಹಾಯಕ. ನೀವು ಯಾವ ಯೋಜನೆ ಬಗ್ಗೆ ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?",
        'hi': "नमस्ते! मैं आपका सरकारी योजना सहायक हूँ। आप किस योजना के बारे में जानना चाहते हैं?"
    }
    
    return greetings.get(language, greetings['en'])


def get_no_scheme_message(language: str, query: str = "") -> str:
    """
    Get 'no scheme found' message in specified language.
    
    Args:
        language: Language code ('en', 'kn', 'hi')
        query: User's query (optional)
        
    Returns:
        No scheme message in specified language
    """
    messages = {
        'en': f"I couldn't find any scheme matching '{query}'. Please try with different keywords or ask about a sector like agriculture, health, or education.",
        'kn': f"'{query}' ಗೆ ಹೊಂದಿಕೆಯಾಗುವ ಯೋಜನೆ ಸಿಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಬೇರೆ ಪದಗಳೊಂದಿಗೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಕೃಷಿ, ಆರೋಗ್ಯ, ಶಿಕ್ಷಣದಂತಹ ವಿಭಾಗಗಳ ಬಗ್ಗೆ ಕೇಳಿ.",
        'hi': f"'{query}' से मेल खाने वाली कोई योजना नहीं मिली। कृपया अन्य शब्दों से प्रयास करें या कृषि, स्वास्थ्य, शिक्षा जैसे क्षेत्र के बारे में पूछें।"
    }
    
    return messages.get(language, messages['en'])


def get_sector_intro(language: str, sector: str, count: int) -> str:
    """
    Get sector introduction message in specified language.
    
    Args:
        language: Language code ('en', 'kn', 'hi')
        sector: Sector name
        count: Number of schemes found
        
    Returns:
        Sector intro message in specified language
    """
    if language == 'kn':
        if count == 1:
            return f"{sector} ವಿಭಾಗದಿಂದ 1 ಯೋಜನೆ ಇಲ್ಲಿದೆ."
        else:
            return f"{sector} ವಿಭಾಗದಿಂದ {count} ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ."
    
    elif language == 'hi':
        if count == 1:
            return f"{sector} क्षेत्र से 1 योजना यहाँ है।"
        else:
            return f"{sector} क्षेत्र से {count} योजनाएँ मिलीं।"
    
    else:  # English
        if count == 1:
            return f"Here is 1 scheme from the {sector} sector."
        else:
            return f"I found {count} schemes from the {sector} sector."


def get_match_intro(language: str, match_type: str, scheme_title: str = None, count: int = 0) -> str:
    """
    Get match type introduction message in specified language.
    
    Args:
        language: Language code ('en', 'kn', 'hi')
        match_type: Type of match ('exact_match', 'fuzzy_match', 'vector_match')
        scheme_title: Name of matched scheme (optional)
        count: Number of schemes (for multiple matches)
        
    Returns:
        Match intro message in specified language
    """
    if language == 'kn':
        if match_type == 'exact_match':
            return f"{scheme_title} ಬಗ್ಗೆ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ."
        elif match_type == 'fuzzy_match':
            return f"ನಿಮಗಾಗಿ ಈ ಯೋಜನೆ ಸಿಕ್ಕಿದೆ: {scheme_title}"
        elif match_type == 'vector_match':
            if count == 1:
                return f"ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಸಂಬಂಧಿಸಿದ ಯೋಜನೆ: {scheme_title}"
            else:
                return f"ನಿಮಗಾಗಿ {count} ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ."
    
    elif language == 'hi':
        if match_type == 'exact_match':
            return f"{scheme_title} के बारे में जानकारी यहाँ है।"
        elif match_type == 'fuzzy_match':
            return f"आपके लिए यह योजना मिली: {scheme_title}"
        elif match_type == 'vector_match':
            if count == 1:
                return f"आपके प्रश्न से संबंधित योजना: {scheme_title}"
            else:
                return f"आपके लिए {count} योजनाएँ मिलीं।"
    
    else:  # English
        if match_type == 'exact_match':
            return f"Sure! Here's the information about {scheme_title}."
        elif match_type == 'fuzzy_match':
            return f"I found this scheme for you: {scheme_title}"
        elif match_type == 'vector_match':
            if count == 1:
                return f"Based on your query, here's what I found: {scheme_title}"
            else:
                return f"I found {count} relevant schemes for you."
    
    return "Here's what I found for you."


def translate_scheme_if_needed(scheme_text: str, user_language: str, scheme_has_translation: bool = False) -> str:
    """
    Translate scheme text if translation doesn't exist in database.
    
    Args:
        scheme_text: Formatted scheme text in English
        user_language: Target language ('kn' or 'hi')
        scheme_has_translation: Whether scheme already has translation in DB
        
    Returns:
        Translated scheme text or original if translation failed
    """
    # If already translated or English, return as-is
    if user_language == 'en' or scheme_has_translation:
        return scheme_text
    
    # Translate using Gemini
    if user_language in ['kn', 'hi']:
        logger.info(f"Translating scheme to {user_language} using Gemini...")
        return translate_with_gemini(scheme_text, user_language)
    
    return scheme_text
