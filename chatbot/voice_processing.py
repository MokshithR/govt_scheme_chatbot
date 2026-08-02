"""
Voice processing module for speech-to-text and text-to-speech functionality
Supports multiple Indian languages including Kannada, Hindi, and English
"""

import os
import tempfile
import logging
import io
import base64
from django.conf import settings

# Try to import optional dependencies with fallbacks
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError as e:
    print(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError as e:
    print(f"pyttsx3 not available: {e}")
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError as e:
    print(f"gTTS not available: {e}")
    GTTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Handles voice processing operations"""
    
    def __init__(self):
        self.whisper_model = None
        self.tts_engine = None
        self._load_models()
    
    def _load_models(self):
        """Load Whisper model for speech recognition"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available - voice recognition disabled")
            self.whisper_model = None
            return
            
        try:
            # Check if we're on Windows and adjust model loading
            import platform
            if platform.system() == "Windows":
                # Use smaller model for Windows compatibility and force CPU device
                try:
                    self.whisper_model = whisper.load_model("tiny", device="cpu")
                except TypeError:
                    # Older whisper versions may not accept device kwarg
                    self.whisper_model = whisper.load_model("tiny")
            else:
                try:
                    self.whisper_model = whisper.load_model("base")
                except Exception:
                    # Fall back to tiny if base fails to load
                    self.whisper_model = whisper.load_model("tiny")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Try to load tiny model as fallback
            try:
                try:
                    self.whisper_model = whisper.load_model("tiny", device="cpu")
                except TypeError:
                    self.whisper_model = whisper.load_model("tiny")
                logger.info("Whisper tiny model loaded as fallback")
            except Exception as e2:
                logger.error(f"Failed to load even tiny model: {e2}")
                self.whisper_model = None
    
    def _get_tts_engine(self):
        """Initialize text-to-speech engine"""
        if not PYTTSX3_AVAILABLE:
            logger.warning("pyttsx3 not available - offline TTS disabled")
            return None
            
        if self.tts_engine is None:
            try:
                self.tts_engine = pyttsx3.init()
                # Configure voice properties
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to find a suitable voice for Indian languages
                    for voice in voices:
                        if 'hindi' in voice.name.lower() or 'indian' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                # Set speech rate and volume
                self.tts_engine.setProperty('rate', 150)  # Speed of speech
                self.tts_engine.setProperty('volume', 0.9)  # Volume level
                logger.info("TTS engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize TTS engine: {e}")
                self.tts_engine = None
        return self.tts_engine
    
    def detect_language(self, audio_file_path):
        """
        Detect the language of the audio using Whisper
        Returns language code (en, hi, kn, etc.)
        """
        if not WHISPER_AVAILABLE or not self.whisper_model:
            logger.warning("Whisper model not available, defaulting to English")
            return 'en'  # Default to English if model not loaded
        
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found for language detection: {audio_file_path}")
                return 'en'
            
            # Load and transcribe audio to detect language
            result = self.whisper_model.transcribe(
                audio_file_path, 
                language=None,
                fp16=False,
                verbose=False
            )
            detected_language = result.get('language', 'en')
            
            # Map Whisper language codes to our language codes
            language_mapping = {
                'en': 'en',  # English
                'hi': 'hi',  # Hindi
                'kn': 'kn',  # Kannada
                'ta': 'ta',  # Tamil
                'te': 'te',  # Telugu
                'ml': 'ml',  # Malayalam
                'mr': 'mr',  # Marathi
                'te': 'te',
                'bn': 'bn',
                'gu': 'gu',
                'mr': 'mr',
                'pa': 'pa',
                'kannada': 'kn',  # Alternative name
                'hindi': 'hi',    # Alternative name
                'tamil': 'ta',    # Alternative name
                'telugu': 'te',   # Alternative name
                'bengali': 'bn',  # Alternative name
                'gujarati': 'gu', # Alternative name
                'marathi': 'mr',  # Alternative name
                'punjabi': 'pa',  # Alternative name
            }
            
            mapped_language = language_mapping.get(detected_language, 'en')
            logger.info(f"Detected language: {detected_language} -> {mapped_language}")
            return mapped_language
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'en'
    
    def speech_to_text(self, audio_file_path, language=None):
        """
        Convert speech to text using Whisper
        Args:
            audio_file_path: Path to the audio file
            language: Optional language code for better accuracy
        Returns:
            dict with 'text', 'language', and 'confidence'
        """
        if not self.whisper_model:
            logger.warning("Whisper model not available, using fallback")
            return {
                'text': 'Voice input received (Whisper not available)',
                'language': 'en',
                'confidence': 0.5,
                'error': 'Whisper model not loaded'
            }
            
        try:
            # Validate audio file
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise ValueError("Audio file is empty")
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("Audio file too large (max 10MB)")
            
            # Validate whisper model
            if not hasattr(self.whisper_model, 'transcribe'):
                logger.error("Whisper model not properly initialized")
                self._load_models()  # Try reloading the model
                
            # IMPORTANT: Always use the language provided by user (no auto-detection)
            # Language MUST be provided from frontend dropdown selection
            if not language:
                logger.warning("No language specified, defaulting to English")
                language = 'en'
            
            # Transcribe audio with FORCED language from user selection
            result = self.whisper_model.transcribe(
                audio_file_path,
                language=language,  # Force this language, no auto-detection
                fp16=False,  # Use fp32 for better compatibility
                verbose=False  # Reduce output verbosity
            )
            
            # Clean up the text
            text = result['text'].strip() if result.get('text') else ''
            
            return {
                'text': text,
                'language': language,
                'confidence': 0.9,  # Whisper doesn't provide confidence scores directly
                'error': None
            }
        except FileNotFoundError as e:
            logger.error(f"Audio file not found: {e}")
            return {
                'text': '',
                'language': language or 'en',
                'confidence': 0.0,
                'error': str(e)
            }
        except ValueError as e:
            logger.error(f"Invalid audio input: {e}")
            return {
                'text': '',
                'language': language or 'en',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def text_to_speech_gtts(self, text, language='en', slow=False):
        """
        Convert text to speech using Google Text-to-Speech
        Args:
            text: Text to convert to speech
            language: Language code (en, hi, kn, etc.)
            slow: Whether to speak slowly
        Returns:
            bytes: Audio data in MP3 format
        """
        try:
            # Map our language codes to gTTS language codes
            gtts_language_mapping = {
                'en': 'en',
                'hi': 'hi',
                'kn': 'kn',
                'ta': 'ta',
                'te': 'te',
                'bn': 'bn',
                'gu': 'gu',
                'mr': 'mr',
                'pa': 'pa',
            }
            
            gtts_lang = gtts_language_mapping.get(language, 'en')
            
            # Create gTTS object
            tts = gTTS(text=text, lang=gtts_lang, slow=slow)
            
            # Save to bytes
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.getvalue()
        except Exception as e:
            logger.error(f"gTTS conversion failed: {e}")
            return None
    
    def text_to_speech_pyttsx3(self, text, language='en'):
        """
        Convert text to speech using pyttsx3 (offline)
        Args:
            text: Text to convert to speech
            language: Language code (limited support)
        Returns:
            bytes: Audio data in WAV format
        """
        try:
            engine = self._get_tts_engine()
            if not engine:
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Configure engine for the specific file
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read the generated audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return audio_data
        except Exception as e:
            logger.error(f"pyttsx3 conversion failed: {e}")
            return None
    
    def text_to_speech(self, text, language='en', use_gtts=True):
        """
        Convert text to speech using the preferred method
        Args:
            text: Text to convert to speech
            language: Language code
            use_gtts: Whether to use gTTS (requires internet) or pyttsx3 (offline)
        Returns:
            dict with 'audio_data', 'format', and 'error'
        """
        try:
            if use_gtts:
                # Try gTTS first (better quality, requires internet)
                audio_data = self.text_to_speech_gtts(text, language)
                if audio_data:
                    return {
                        'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                        'format': 'mp3',
                        'error': None
                    }
            
            # Fallback to pyttsx3 (offline, lower quality)
            audio_data = self.text_to_speech_pyttsx3(text, language)
            if audio_data:
                return {
                    'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                    'format': 'wav',
                    'error': None
                }
            
            return {
                'audio_data': None,
                'format': None,
                'error': 'Failed to generate speech'
            }
        except Exception as e:
            logger.error(f"Text to speech conversion failed: {e}")
            return {
                'audio_data': None,
                'format': None,
                'error': str(e)
            }
    
    def process_voice_input(self, audio_file_path):
        """
        Process voice input: convert speech to text and detect language
        Args:
            audio_file_path: Path to the audio file
        Returns:
            dict with transcription results
        """
        try:
            # Check if Whisper model is available
            if not self.whisper_model:
                logger.warning("Whisper model not available, using fallback")
                return self._fallback_voice_processing(audio_file_path)
            
            # First detect language
            detected_language = self.detect_language(audio_file_path)
            
            # Convert speech to text
            result = self.speech_to_text(audio_file_path, detected_language)
            
            if result.get('error'):
                logger.warning(f"Whisper failed: {result['error']}, using fallback")
                return self._fallback_voice_processing(audio_file_path)
            
            return {
                'success': True,
                'text': result['text'],
                'language': result['language'],
                'confidence': result['confidence'],
                'error': result.get('error')
            }
        except Exception as e:
            logger.error(f"Voice input processing failed: {e}")
            return self._fallback_voice_processing(audio_file_path)
    
    def _fallback_voice_processing(self, audio_file_path):
        """
        Fallback voice processing when Whisper is not available
        Provides helpful guidance to use Web Speech API
        """
        try:
            logger.info("Server-side voice processing not available - recommending Web Speech API")
            return {
                'success': False,
                'text': '',
                'language': 'en',
                'confidence': 0.0,
                'error': 'Server-side voice processing is not available. Please use the "CLICK & SPEAK" button which uses your browser\'s built-in speech recognition.'
            }
        except Exception as e:
            logger.error(f"Fallback voice processing failed: {e}")
            return {
                'success': False,
                'text': '',
                'language': 'en',
                'confidence': 0.0,
                'error': 'Voice processing failed. Please use the text input instead.'
            }
    
    def generate_voice_response(self, text, language='en', use_gtts=True):
        """
        Generate voice response for the given text
        Args:
            text: Text to convert to speech
            language: Language code
            use_gtts: Whether to use gTTS or pyttsx3
        Returns:
            dict with audio response
        """
        try:
            result = self.text_to_speech(text, language, use_gtts)
            
            return {
                'success': result['error'] is None,
                'audio_data': result['audio_data'],
                'format': result['format'],
                'error': result['error']
            }
        except Exception as e:
            logger.error(f"Voice response generation failed: {e}")
            return {
                'success': False,
                'audio_data': None,
                'format': None,
                'error': str(e)
            }


# Global instance
voice_processor = VoiceProcessor()
