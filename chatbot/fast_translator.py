"""
Fast translation using googletrans (no API key, no rate limits)
"""
import logging
import time

logger = logging.getLogger(__name__)

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans not installed. Run: pip install googletrans==4.0.0rc1")


class FastTranslator:
    """Fast translator using Google Translate (no API key needed)"""
    
    def __init__(self):
        self.language_codes = {
            'hi': 'hi',  # Hindi
            'kn': 'kn',  # Kannada
            'ta': 'ta',  # Tamil
            'te': 'te',  # Telugu
            'mr': 'mr',  # Marathi
            'bn': 'bn',  # Bengali
            'gu': 'gu',  # Gujarati
            'ml': 'ml',  # Malayalam
            'pa': 'pa',  # Punjabi
            'en': 'en'   # English
        }
        self._translator = None
    
    def _get_translator(self):
        """Get or create translator instance with retry"""
        if not GOOGLETRANS_AVAILABLE:
            return None
        
        if self._translator is None:
            try:
                self._translator = Translator()
            except Exception as e:
                logger.error(f"Failed to create translator: {e}")
                return None
        return self._translator
    
    def translate(self, text, target_lang='kn', source_lang='en', retries=3):
        """
        Translate text using Google Translate with retry mechanism
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code (hi, kn, ta, etc.)
            source_lang (str): Source language code (default: en)
            retries (int): Number of retry attempts
            
        Returns:
            str: Translated text or original if translation fails
        """
        if not GOOGLETRANS_AVAILABLE:
            logger.warning("googletrans not available, returning original text")
            return text
        
        translator = self._get_translator()
        if not translator:
            return text
            
        if target_lang == source_lang:
            return text
        
        # Get proper language code
        dest_code = self.language_codes.get(target_lang, target_lang)
        src_code = self.language_codes.get(source_lang, source_lang)
        
        for attempt in range(retries):
            try:
                # Create fresh translator on retry
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{retries}")
                    time.sleep(0.5)  # Brief pause before retry
                    self._translator = Translator()
                    translator = self._translator
                
                # Translate
                result = translator.translate(text, dest=dest_code, src=src_code)
                
                if result and result.text:
                    return result.text
                else:
                    logger.warning(f"Empty translation result for: {text[:50]}")
                    
            except Exception as e:
                logger.error(f"Translation error (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    # Last attempt failed
                    return text
                    
        return text
    
    def translate_batch(self, texts, target_lang='kn', source_lang='en'):
        """
        Translate multiple texts at once
        
        Args:
            texts (list): List of texts to translate
            target_lang (str): Target language code
            source_lang (str): Source language code
            
        Returns:
            list: List of translated texts
        """
        # Translate individually for better reliability
        return [self.translate(text, target_lang, source_lang) for text in texts]
    
    def translate_scheme(self, scheme_data, target_lang='kn'):
        """
        Translate a scheme dictionary
        
        Args:
            scheme_data (dict): Scheme with title, description, etc.
            target_lang (str): Target language code
            
        Returns:
            dict: Translated scheme data
        """
        if not GOOGLETRANS_AVAILABLE:
            return scheme_data
        
        # Copy original data
        translated = dict(scheme_data)
        
        try:
            # Translate each field individually for better reliability
            if 'title' in scheme_data and scheme_data['title']:
                translated['title'] = self.translate(scheme_data['title'], target_lang)
            
            if 'description' in scheme_data and scheme_data['description']:
                translated['description'] = self.translate(scheme_data['description'], target_lang)
            
            if 'government_level' in scheme_data and scheme_data['government_level']:
                translated['government_level'] = self.translate(scheme_data['government_level'], target_lang)
            
            if 'state' in scheme_data and scheme_data['state']:
                translated['state'] = self.translate(scheme_data['state'], target_lang)
            
            # Keep id unchanged
            if 'id' in scheme_data:
                translated['id'] = scheme_data['id']
                
            return translated
            
        except Exception as e:
            logger.error(f"Scheme translation error: {e}")
            return scheme_data


# Global translator instance
_fast_translator = None

def get_fast_translator():
    """Get or create global FastTranslator instance"""
    global _fast_translator
    if _fast_translator is None:
        _fast_translator = FastTranslator()
    return _fast_translator
