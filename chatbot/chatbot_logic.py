"""
Chatbot logic for processing user queries and returning relevant scheme information
Supports multiple languages and intelligent query processing
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .models import GovernmentScheme, ChatSession, ChatMessage
from .voice_processing import voice_processor
import json
from .gemini_utils import generate_text_with_gemini

try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not installed. Install with: pip install fuzzywuzzy python-Levenshtein")

logger = logging.getLogger(__name__)


class GovernmentChatbot:
    """Main chatbot class for processing government scheme queries"""
    
    def __init__(self):
        self.language = 'en'
        self.session_id = None
        self.session = None
        self._scheme_names_cache = None
        self._cache_timestamp = None
    
    def _get_scheme_names(self) -> List[str]:
        """Get cached list of all scheme titles from DB for fuzzy matching"""
        from datetime import datetime, timedelta
        
        # Cache for 5 minutes
        if self._scheme_names_cache and self._cache_timestamp:
            if datetime.now() - self._cache_timestamp < timedelta(minutes=5):
                return self._scheme_names_cache
        
        try:
            scheme_titles = list(GovernmentScheme.objects.filter(is_active=True).values_list('title', flat=True))
            self._scheme_names_cache = scheme_titles
            self._cache_timestamp = datetime.now()
            return scheme_titles
        except Exception as e:
            logger.warning(f"Failed to fetch scheme names from DB: {e}")
            # Fallback to common scheme names
            return [
                "Pradhan Mantri Awas Yojana",
                "PM Kisan",
                "Ayushman Bharat",
                "Ujjwala Yojana",
                "PMMVY",
                "Pradhan Mantri Matru Vandana Yojana",
                "Pradhan Mantri Kisan Samman Nidhi",
                "PM Jan Dhan Yojana",
                "Sukanya Samriddhi Yojana",
                "Atal Pension Yojana",
            ]
    
    def correct_spelling(self, user_text: str) -> Tuple[str, Optional[str]]:
        """Correct spelling using fuzzy matching against known scheme names.
        
        Returns:
            Tuple of (corrected_text, matched_scheme_name or None)
        """
        if not FUZZY_AVAILABLE:
            return user_text, None
        
        schemes = self._get_scheme_names()
        if not schemes:
            return user_text, None
        
        best_match = None
        highest_score = 0
        
        for scheme in schemes:
            score = fuzz.ratio(user_text.lower(), scheme.lower())
            if score > highest_score:
                highest_score = score
                best_match = scheme
        
        # If we have a strong match (70%+), suggest it
        if highest_score >= 70 and best_match:
            logger.info(f"Fuzzy match: '{user_text}' -> '{best_match}' (score: {highest_score})")
            return best_match, best_match
        
        # Also check partial matches in the query (for multi-word queries)
        words = user_text.split()
        if len(words) > 2:
            for scheme in schemes:
                # Check if any significant part of the scheme name appears with typos
                scheme_words = scheme.split()
                for sw in scheme_words:
                    if len(sw) > 3:  # Only match meaningful words
                        for uw in words:
                            if len(uw) > 3:
                                score = fuzz.ratio(uw.lower(), sw.lower())
                                if score >= 75:
                                    logger.info(f"Partial fuzzy match: '{user_text}' contains '{uw}' ~ '{sw}' from '{scheme}'")
                                    return user_text, scheme  # Keep original query but note the match
        
        return user_text, None
    
    def translate_response(self, text: str, target_language: str) -> str:
        """Translate response text to target language using Gemini AI.
        
        Args:
            text: The English text to translate
            target_language: Target language code ('hi' for Hindi, 'kn' for Kannada)
        
        Returns:
            Translated text (or original if translation fails)
        """
        if target_language == 'en' or not text:
            return text
        
        language_names = {
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'ml': 'Malayalam',
            'pa': 'Punjabi'
        }
        
        target_lang_name = language_names.get(target_language, target_language)
        
        try:
            prompt = f"""Translate the following government scheme information from English to {target_lang_name}.
Preserve scheme names, numbers, and links as-is.
Make the translation natural and easy to understand for native speakers.
Return PLAIN TEXT only. Do NOT use markdown: no headings, no bullets, no asterisks, no '#' symbols,
no bold/italic formatting. Respond in clean sentences and short paragraphs only.

English text:
{text}

{target_lang_name} translation (plain text, no markdown):"""

            translated = generate_text_with_gemini(prompt)
            if translated and len(translated.strip()) > 10:
                logger.info(f"Successfully translated response to {target_lang_name}")
                return translated.strip()
            else:
                logger.warning(f"Translation to {target_lang_name} returned empty result")
                return text
        except Exception as e:
            logger.error(f"Translation to {target_lang_name} failed: {e}")
            return text
    
    def set_language(self, language: str):
        """Set the language for responses"""
        self.language = language
    
    def set_session(self, session_id: str):
        """Set the current chat session"""
        self.session_id = session_id
        try:
            self.session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            self.session = ChatSession.objects.create(
                session_id=session_id,
                language=self.language
            )
    
    def process_query(self, query: str, language: str = 'en') -> Dict:
        """
        Process user query and return relevant scheme information
        Args:
            query: User's query text
            language: Language of the query
        Returns:
            dict with response information
        """
        try:
            self.set_language(language)
            
            # Store original query for response generation
            original_query = query
            
            # If query is in Kannada or Hindi, translate to English for DB search
            # Database schemes are in English, so we need English for accurate search
            search_query = query
            if language != 'en':
                try:
                    lang_names = {'kn': 'Kannada', 'hi': 'Hindi'}
                    lang_full = lang_names.get(language, language)
                    translation_prompt = (
                        f"Translate the following {lang_full} text to English. "
                        f"Return ONLY the English translation, no explanations.\n\n"
                        f"Text to translate: {query}"
                    )
                    search_query = generate_text_with_gemini(translation_prompt).strip()
                    logger.info(f"Translated query from {language} to English: {query} → {search_query}")
                except Exception as e:
                    logger.warning(f"Query translation failed: {e}, using original query")
                    search_query = query
            
            # Apply fuzzy spell correction (on English search query)
            corrected_query, matched_scheme = self.correct_spelling(search_query)
            did_correct = corrected_query != search_query
            
            # Log user message (original query in user's language)
            if self.session:
                ChatMessage.objects.create(
                    session=self.session,
                    message_type='user',
                    text_content=original_query,
                    language=language
                )
            
            # Use corrected English query for DB processing
            working_query = corrected_query
            
            # Analyze query intent
            intent = self._analyze_intent(working_query)
            
            # Extract keywords and entities
            keywords = self._extract_keywords(working_query)
            entities = self._extract_entities(working_query)
            
            # If we found a fuzzy match, add it to keywords for better search
            if matched_scheme:
                keywords.insert(0, matched_scheme)
            
            # Search for relevant schemes (using English query for DB)
            relevant_schemes = self._search_schemes(working_query, keywords, entities, intent)
            
            # Generate response (using original query to preserve user's language context)
            response = self._generate_response(original_query, relevant_schemes, intent, language)
            
            # No need to translate - Gemini generates response in target language directly
            
            # If we corrected spelling, prepend a note in the user's language
            if did_correct and matched_scheme:
                correction_msg = f"Did you mean '{matched_scheme}'?" if language == 'en' else f"क्या आपका मतलब '{matched_scheme}' था?" if language == 'hi' else f"'{matched_scheme}' ಎಂದು ನೀವು ಹೇಳುತ್ತಿದ್ದೀರಾ?"
                correction_note = correction_msg + "\n\n"
                response['text'] = correction_note + response['text']
            
            # Log bot response
            if self.session:
                ChatMessage.objects.create(
                    session=self.session,
                    message_type='bot',
                    text_content=response['text'],
                    language=language,
                    related_schemes=[scheme.get('_id', '') for scheme in relevant_schemes[:3]],
                    confidence_score=response.get('confidence', 0.8)
                )
            
            # For sector searches or general queries, return more schemes (up to 25)
            # For specific queries (like single scheme lookup), return fewer (5)
            max_schemes = 25 if (intent in ['sector_specific', 'search_scheme', 'general_query'] or entities.get('sectors')) else 5
            
            return {
                'success': True,
                'response': response,
                'schemes': [self._format_scheme(scheme) for scheme in relevant_schemes[:max_schemes]],
                'intent': intent,
                'keywords': keywords,
                'language': language,
                'spelling_corrected': did_correct,
                'matched_scheme': matched_scheme
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': {
                    'text': self._get_error_response(language),
                    'confidence': 0.0,
                    'intent': 'error',
                    'scheme_count': 0
                }
            }
    
    def process_voice_query(self, audio_file_path: str) -> Dict:
        """
        Process voice query: convert speech to text and process
        Args:
            audio_file_path: Path to the audio file
        Returns:
            dict with response and audio
        """
        try:
            # Convert speech to text using voice processor
            stt_result = voice_processor.process_voice_input(audio_file_path)
            
            if not stt_result['success']:
                return {
                    'success': False,
                    'error': stt_result['error'],
                    'text_response': 'Voice processing failed. Please try again or use text input.',
                    'audio_response': None,
                    'language': 'en',
                    'schemes': [],
                    'confidence': 0.0
                }
            
            # Process the text query using our chatbot logic
            query_result = self.process_query(
                stt_result['text'], 
                stt_result['language']
            )
            
            if not query_result['success']:
                return {
                    'success': False,
                    'error': query_result.get('error', 'Query processing failed'),
                    'text_response': query_result['response']['text'],
                    'audio_response': None,
                    'language': stt_result['language'],
                    'schemes': [],
                    'confidence': 0.0
                }
            
            # Generate voice response
            try:
                voice_result = voice_processor.generate_voice_response(
                    query_result['response']['text'],
                    query_result['language']
                )
                audio_response = voice_result.get('audio_data') if voice_result.get('success') else None
                audio_format = voice_result.get('format')
                audio_error = voice_result.get('error')
            except Exception as e:
                logger.warning(f"Voice response generation failed: {e}")
                audio_response = None
                audio_format = None
                audio_error = str(e)
            
            return {
                'success': True,
                'text_response': query_result['response']['text'],
                'audio_response': audio_response,
                'audio_format': audio_format,
                'audio_error': audio_error,
                'language': query_result['language'],
                'schemes': query_result['schemes'],
                'confidence': query_result['response'].get('confidence', 0.8),
                'user_text': stt_result['text']
            }
            
        except Exception as e:
            logger.error(f"Error processing voice query: {e}")
            return {
                'success': False,
                'error': str(e),
                'text_response': 'An error occurred while processing your voice input. Please try again.',
                'audio_response': None,
                'language': 'en',
                'schemes': [],
                'confidence': 0.0
            }
    
    def _analyze_intent(self, query: str) -> str:
        """Analyze user intent from the query"""
        query_lower = query.lower()
        
        # Intent patterns (English and Kannada)
        intent_patterns = {
            'search_scheme': [
                r'scheme.*for',
                r'program.*for',
                r'yojana.*for',
                r'benefit.*for',
                r'help.*with',
                r'support.*for',
                # Kannada patterns
                r'ಯೋಜನೆ',
                r'ಕಾರ್ಯಕ್ರಮ',
                r'ಲಾಭ',
                r'ಸಹಾಯ',
                r'ಬೆಂಬಲ'
            ],
            'get_info': [
                r'what.*is',
                r'tell.*about',
                r'information.*about',
                r'details.*of',
                r'explain',
                # Kannada patterns
                r'ಏನು',
                r'ಹೇಳಿ',
                r'ಮಾಹಿತಿ',
                r'ವಿವರ',
                r'ವಿವರಿಸಿ'
            ],
            'eligibility': [
                r'eligible',
                r'qualify',
                r'criteria',
                r'requirements',
                r'who.*can.*apply',
                # Kannada patterns
                r'ಅರ್ಹತೆ',
                r'ಅರ್ಹ',
                r'ನಿಯಮ',
                r'ಅವಶ್ಯಕತೆ',
                r'ಯಾರು.*ಅರ್ಜಿ'
            ],
            'application': [
                r'how.*to.*apply',
                r'apply.*for',
                r'application.*process',
                r'where.*to.*apply',
                r'documents.*required',
                # Kannada patterns
                r'ಎಲ್ಲಿ.*ಅರ್ಜಿ',
                r'ಅರ್ಜಿ.*ಹಾಕಿ',
                r'ಅರ್ಜಿ.*ಪ್ರಕ್ರಿಯೆ',
                r'ಎಲ್ಲಿ.*ಅರ್ಜಿ',
                r'ದಾಖಲೆ.*ಅವಶ್ಯಕ'
            ],
            'benefits': [
                r'benefits',
                r'advantages',
                r'what.*do.*i.*get',
                r'assistance',
                r'help.*provided',
                # Kannada patterns
                r'ಲಾಭ',
                r'ಅನುಕೂಲ',
                r'ಏನು.*ಸಿಗುತ್ತದೆ',
                r'ಸಹಾಯ',
                r'ಬೆಂಬಲ.*ನೀಡುತ್ತಾರೆ'
            ],
            'sector_specific': [
                r'agriculture',
                r'health',
                r'education',
                r'employment',
                r'farmer',
                r'student',
                r'job',
                # Kannada patterns
                r'ಕೃಷಿ',
                r'ಆರೋಗ್ಯ',
                r'ಶಿಕ್ಷಣ',
                r'ಉದ್ಯೋಗ',
                r'ರೈತ',
                r'ವಿದ್ಯಾರ್ಥಿ',
                r'ಕೆಲಸ'
            ],
            'greeting': [
                r'hello',
                r'hi',
                r'good.*morning',
                r'good.*afternoon',
                r'good.*evening',
                # Kannada patterns
                r'ನಮಸ್ಕಾರ',
                r'ಹಲೋ',
                r'ಶುಭ.*ಬೆಳಿಗ್ಗೆ',
                r'ಶುಭ.*ಮಧ್ಯಾಹ್ನ',
                r'ಶುಭ.*ಸಂಜೆ'
            ],
            'help': [
                r'help',
                r'what.*can.*you.*do',
                r'how.*to.*use',
                r'commands',
                # Kannada patterns
                r'ಸಹಾಯ',
                r'ಏನು.*ಮಾಡಬಹುದು',
                r'ಹೇಗೆ.*ಬಳಸುವುದು',
                r'ಆಜ್ಞೆಗಳು'
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return 'general_query'
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from the query"""
        # Remove common stop words
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now', 'please', 'thank', 'thanks'
        }
        
        # Extract words and phrases
        # First try to find exact scheme names
        scheme_names = [
            'pradhan mantri awas yojana',
            'pmay',
            'awas yojana'
        ]
        query_lower = query.lower()
        for scheme in scheme_names:
            if scheme in query_lower:
                return [scheme]
        
        # If no exact scheme found, extract individual words
        words = re.findall(r'\b\w+\b', query_lower)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract entities from the query"""
        entities = {
            'sectors': [],
            'age_groups': [],
            'genders': [],
            'locations': [],
            'scheme_types': []
        }
        
        query_lower = query.lower()
        
        # Extract sectors
        sector_keywords = {
            'agriculture': ['agriculture', 'farmer', 'farming', 'crop', 'irrigation', 'kisan'],
            'health': ['health', 'medical', 'hospital', 'doctor', 'medicine', 'treatment'],
            'education': ['education', 'school', 'college', 'student', 'scholarship', 'learning'],
            'employment': ['employment', 'job', 'work', 'skill', 'training', 'rogar'],
            'housing': ['housing', 'house', 'home', 'awas', 'pmay', 'residence'],
            'social_welfare': ['welfare', 'pension', 'widow', 'disabled', 'senior', 'social', 'housing', 'house', 'awas'],
            'urban_development': ['urban', 'city', 'housing', 'house', 'awas', 'pmay'],
            'women_empowerment': ['women', 'girl', 'female', 'empowerment', 'beti', 'mahila'],
            'youth_development': ['youth', 'young', 'student', 'youth development']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                entities['sectors'].append(sector)
        
        # Extract age groups
        age_patterns = {
            'children': ['child', 'children', 'kid', 'kids', 'minor', 'under 18'],
            'youth': ['youth', 'young', 'teenager', '18-30', '18-35'],
            'adult': ['adult', 'middle age', '30-60', '35-60'],
            'senior': ['senior', 'elderly', 'old', 'above 60', '60+', 'pension']
        }
        
        for age_group, patterns in age_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                entities['age_groups'].append(age_group)
        
        # Extract genders
        if any(word in query_lower for word in ['women', 'woman', 'girl', 'female', 'ladies']):
            entities['genders'].append('female')
        if any(word in query_lower for word in ['men', 'man', 'boy', 'male', 'gentlemen']):
            entities['genders'].append('male')
        
        return entities
    
    def _search_schemes(self, query: str, keywords: List[str], entities: Dict, intent: str) -> List[Dict]:
        """Search for relevant schemes: try PostgreSQL (Django ORM) first, then MongoDB, then fallback.

        Note: PostgreSQL search is the primary source and is now more inclusive:
        - We OR together matches on individual words instead of AND-ing filters per word.
        - We fetch up to 50 recent schemes before any higher-level limit is applied.
        """
        # 1) Try PostgreSQL via Django ORM
        try:
            qs = GovernmentScheme.objects.filter(is_active=True)

            # Sector filter (ForeignKey -> filter by related name) - case-insensitive
            if entities.get('sectors'):
                from django.db.models import Q
                sector_q = Q()
                for sector in entities['sectors']:
                    sector_q |= Q(sector__name__icontains=sector)
                qs = qs.filter(sector_q)

            # Intent-specific filters
            if intent == 'eligibility':
                qs = qs.exclude(eligibility_criteria__isnull=True).exclude(eligibility_criteria='')
            elif intent == 'application':
                qs = qs.exclude(application_process__isnull=True).exclude(application_process='')
            elif intent == 'benefits':
                qs = qs.exclude(benefits__isnull=True).exclude(benefits='')

            # Flexible keyword search
            # Skip keyword filtering if we already have sector filters and reasonable results
            # This prevents over-filtering on sector queries like "farmer schemes" or "agriculture"
            from django.db.models import Q
            skip_keyword_filter = False
            if entities.get('sectors') and qs.count() >= 5:
                # If sector filter already gives us good results, don't narrow further with keywords
                skip_keyword_filter = True
            
            if not skip_keyword_filter:
                if keywords:
                    q_obj = Q()
                    for kw in keywords[:10]:
                        q_obj |= (
                            Q(title__icontains=kw) |
                            Q(description__icontains=kw) |
                            Q(short_description__icontains=kw) |
                            Q(benefits__icontains=kw) |
                            Q(eligibility_criteria__icontains=kw) |
                            Q(sector__name__icontains=kw) |
                            Q(keywords__contains=[kw]) |
                            Q(search_tags__contains=[kw])
                        )
                    if q_obj:
                        qs = qs.filter(q_obj)
                else:
                    # Use words from full query; OR all word matches instead of AND-ing filters
                    words = re.findall(r"\b\w+\b", query.lower())[:10]
                    if words:
                        q_obj = Q()
                        for word in words:
                            q_obj |= (
                                Q(title__icontains=word) |
                                Q(description__icontains=word) |
                                Q(short_description__icontains=word)
                                | Q(keywords__contains=[word])
                                | Q(search_tags__contains=[word])
                            )
                        qs = qs.filter(q_obj)

            # Fetch up to 50 most recently updated schemes from PostgreSQL.
            qs = qs.order_by('-last_updated')[:50]

            def _model_to_doc(s):
                return {
                    '_id': f'sql:{s.pk}',
                    'title': s.title or '',
                    'description': s.description or '',
                    'short_description': s.short_description or (s.description or '')[:200],
                    'sector': (s.sector.name if s.sector_id else ''),
                    'ministry': s.ministry or '',
                    'department': s.department or '',
                    'government_level': s.government_level or '',
                    'state': s.state or '',
                    'eligibility_criteria': s.eligibility_criteria or '',
                    'benefits': s.benefits or '',
                    'application_process': s.application_process or '',
                    'application_link': s.application_link or '',
                    'launch_date': str(s.launch_date) if s.launch_date else '',
                    'last_date': str(s.last_date) if s.last_date else '',
                    'helpline_number': s.helpline_number or '',
                    'email': s.email or '',
                    'website': s.website or '',
                    'source_url': s.source_url or '',
                    'keywords': s.keywords or [],
                    'search_tags': s.search_tags or [],
                    'language': s.language or 'en',
                    'is_active': bool(s.is_active),
                }

            orm_results = [_model_to_doc(s) for s in qs]
            if orm_results:
                logger.info(f"Found {len(orm_results)} schemes via PostgreSQL for query: {query}")
                return orm_results
        except Exception as e:
            logger.warning(f"PostgreSQL search failed or not configured: {e}")

        # 2) Fallback to MongoDB adapter if available
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mongodb_adapter import MongoDBAdapter
            adapter = MongoDBAdapter()
            schemes = adapter.search_schemes(query, keywords, entities, intent)
            if schemes:
                logger.info(f"Found {len(schemes)} schemes via MongoDB for query: {query}")
                return schemes
        except Exception as e:
            logger.warning(f"MongoDB search failed: {e}")

        # 3) Final fallback
        return self._get_fallback_schemes(keywords)
    
    def _get_fallback_schemes(self, keywords: List[str]) -> List[Dict]:
        """Provide fallback schemes when MongoDB is not available"""
        fallback_schemes = [
            {
                'title': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
                'description': 'Income support scheme for farmers providing ₹6,000 per year',
                'short_description': '₹6,000 annual income support for farmers',
                'sector': 'agriculture',
                'ministry': 'Ministry of Agriculture and Farmers Welfare',
                'government_level': 'central',
                'eligibility_criteria': 'All landholding farmer families',
                'benefits': '₹6,000 per year in three installments',
                'website': 'https://pmkisan.gov.in/',
                'keywords': ['agriculture', 'farmers', 'income support'],
                'is_active': True
            },
            {
                'title': 'Ayushman Bharat - PM Jan Arogya Yojana',
                'description': 'Health insurance scheme providing ₹5 lakh coverage per family',
                'short_description': '₹5 lakh health insurance coverage',
                'sector': 'health',
                'ministry': 'Ministry of Health and Family Welfare',
                'government_level': 'central',
                'eligibility_criteria': 'Vulnerable families as per SECC-2011',
                'benefits': 'Health insurance up to ₹5 lakh per family per year',
                'website': 'https://pmjay.gov.in/',
                'keywords': ['health', 'insurance', 'medical'],
                'is_active': True
            }
        ]
        
        # Filter schemes based on keywords
        if keywords:
            filtered_schemes = []
            for scheme in fallback_schemes:
                for keyword in keywords:
                    if (keyword.lower() in scheme['sector'].lower() or 
                        keyword.lower() in scheme['title'].lower() or
                        any(k.lower() in keyword.lower() for k in scheme['keywords'])):
                        filtered_schemes.append(scheme)
                        break
            return filtered_schemes
        
        return fallback_schemes
    
    def _generate_response(self, query: str, schemes: List[GovernmentScheme], intent: str, language: str) -> Dict:
        """Generate response based on query and found schemes"""
        try:
            if not schemes:
                # If no schemes found, use Gemini to craft a helpful reply that is explicit
                # about the limitation of the local database and does NOT invent schemes.
                base = self._get_no_results_response(intent, language)
                try:
                    # Map language code to full name for clarity
                    lang_names = {'en': 'English', 'kn': 'Kannada', 'hi': 'Hindi'}
                    lang_full = lang_names.get(language, 'English')
                    
                    prompt = (
                        f"Respond ONLY in {lang_full}. Do not translate to other languages.\n\n"
                        f"User query: {query}\n\n"
                        "Context: The system searched its INTERNAL government schemes database "
                        "(PostgreSQL/MongoDB) and did not find any matching scheme for this query.\n\n"
                        "Instruction: Talk to the user in a friendly way and:\n"
                        "1) Clearly state that no matching scheme was found in this internal database.\n"
                        "2) Do NOT guess or invent new scheme names or details.\n"
                        "3) Suggest helpful next steps like rephrasing the query, mentioning the sector, "
                        "   or providing more details.\n"
                        "4) Keep the answer concise (3-5 sentences).\n"
                        "5) Return PLAIN TEXT only: no markdown, no headings, no bullets, no asterisks, "
                        "no '#' symbols, no bold/italic formatting, no pipes '|', no dashes '-'.\n"
                        f"6) Your entire response must be in {lang_full} language only."
                    )
                    ai_reply = generate_text_with_gemini(prompt)
                    if ai_reply and ai_reply.strip():
                        return {'text': ai_reply.strip(), 'confidence': 0.6, 'intent': intent, 'scheme_count': 0}
                except Exception:
                    pass

                return {'text': base, 'confidence': 0.5, 'intent': intent, 'scheme_count': 0}

            # For specific intents, generate structured response
            if intent == 'greeting':
                base_response = self._get_greeting_response(language)
                return {'text': base_response, 'confidence': 0.9, 'intent': intent, 'scheme_count': 0}
            elif intent == 'help':
                base_response = self._get_help_response(language)
                return {'text': base_response, 'confidence': 0.9, 'intent': intent, 'scheme_count': 0}

            # For scheme queries, use Gemini to create structured, detailed responses
            try:
                # Prepare comprehensive scheme context
                scheme_details = []
                for s in schemes[:3]:  # Top 3 most relevant
                    if isinstance(s, dict):
                        details = {
                            'title': s.get('title', ''),
                            'description': s.get('description', ''),
                            'short_description': s.get('short_description', ''),
                            'sector': s.get('sector', ''),
                            'eligibility': s.get('eligibility_criteria', ''),
                            'benefits': s.get('benefits', ''),
                            'documents': s.get('required_documents', []) if isinstance(s.get('required_documents'), list) else [],
                            'application': s.get('application_process', ''),
                            'application_link': s.get('application_link', ''),
                            'website': s.get('website', ''),
                            'helpline': s.get('helpline_number', ''),
                            'ministry': s.get('ministry', ''),
                        }
                    else:
                        details = {
                            'title': getattr(s, 'title', ''),
                            'description': getattr(s, 'description', ''),
                            'short_description': getattr(s, 'short_description', ''),
                            'sector': getattr(s.sector, 'name', '') if s.sector else '',
                            'eligibility': getattr(s, 'eligibility_criteria', ''),
                            'benefits': getattr(s, 'benefits', ''),
                            'documents': getattr(s, 'required_documents', []) if isinstance(getattr(s, 'required_documents', []), list) else [],
                            'application': getattr(s, 'application_process', ''),
                            'application_link': getattr(s, 'application_link', ''),
                            'website': getattr(s, 'website', ''),
                            'helpline': getattr(s, 'helpline_number', ''),
                            'ministry': getattr(s, 'ministry', ''),
                        }
                    scheme_details.append(details)

                # Build detailed context for Gemini
                context_parts = []
                for i, d in enumerate(scheme_details, 1):
                    ctx = f"""
Scheme {i}:
- Name: {d['title']}
- Sector: {d['sector']}
- Ministry: {d['ministry']}
- Description: {d['short_description'] or d['description'][:200]}
- Eligibility: {d['eligibility'][:300] if d['eligibility'] else 'Not specified'}
- Benefits: {d['benefits'][:300] if d['benefits'] else 'Not specified'}
- Documents: {', '.join(d['documents'][:5]) if d['documents'] else 'Check official site'}
- How to Apply: {d['application'][:200] if d['application'] else 'Visit official website'}
- Website: {d['website'] or d['application_link'] or 'Not available'}
- Helpline: {d['helpline'] or 'Not available'}
"""
                    context_parts.append(ctx.strip())

                scheme_context = "\n\n".join(context_parts)

                # Map language code to full name for Gemini clarity
                lang_names = {'en': 'English', 'kn': 'Kannada', 'hi': 'Hindi'}
                lang_full = lang_names.get(language, 'English')

                # Create intent-specific prompt with language forcing
                if intent == 'get_info':
                    instruction = (
                        f"Provide comprehensive information about the scheme(s) ONLY in {lang_full}. "
                        "Include: Name, Sector, Description, Key Benefits, and Website link."
                    )
                elif intent == 'eligibility':
                    instruction = (
                        f"Explain who is eligible for the scheme(s) ONLY in {lang_full}. "
                        "List eligibility criteria clearly."
                    )
                elif intent == 'application':
                    instruction = (
                        f"Explain how to apply for the scheme(s) ONLY in {lang_full}. "
                        "Include: Step-by-step process, required documents, application link/website, and helpline if available."
                    )
                elif intent == 'benefits':
                    instruction = (
                        f"Explain the benefits provided by the scheme(s) ONLY in {lang_full}. "
                        "Include financial assistance amounts, services provided, and other advantages."
                    )
                else:
                    instruction = (
                        f"Provide a complete overview of the scheme(s) ONLY in {lang_full} covering: "
                        "Name, Eligibility, Benefits, Required Documents, How to Apply, and Website/Contact."
                    )

                prompt = (
                    f"Respond ONLY in {lang_full}. Do not translate to other languages. Your entire response must be in {lang_full}.\n\n"
                    f"You are a government scheme information assistant. Answer user queries clearly and concisely.\n\n"
                    "IMPORTANT GROUNDING RULES:\n"
                    "- You ONLY know about the schemes listed under 'Available Scheme Information'.\n"
                    "- Do NOT introduce or guess any other scheme names (central or state) that are not in this list.\n"
                    "- Preserve scheme titles exactly as given in the list (you may adjust only minor casing).\n"
                    "- If the user query mentions a slightly different name (e.g. 'SSP scholarship'), "
                    "  map it to the closest title from the list, but always show the actual stored title.\n"
                    "- Do NOT change 'SSP scholarship' into an unrelated scheme like 'SC/ST Pre-matric Scholarship' "
                    "  unless that exact scheme is present in the provided list.\n"
                    "- If some field (benefits, eligibility, dates, etc.) is missing or empty in the context, "
                    "  say that the information is not available in this database instead of inventing details.\n\n"
                    "OUTPUT FORMAT RULES (CRITICAL FOR TTS):\n"
                    "- Return PLAIN TEXT only. Do NOT use any markdown formatting.\n"
                    "- No headings (no lines starting with '#', '##', or '###').\n"
                    "- No bullets or lists using '-', '*', '•' or numbers with dots.\n"
                    "- No bold/italic markers like **text** or *text*.\n"
                    "- No pipe symbols '|', no dashes at line starts.\n"
                    "- Use clean sentences only. Separate schemes with blank lines.\n"
                    f"- Your entire response must be in {lang_full} language.\n\n"
                    f"User Query: {query}\n"
                    f"Intent: {intent}\n\n"
                    f"Available Scheme Information:\n{scheme_context}\n\n"
                    f"Instruction: {instruction}\n\n"
                    "Format your response with simple paragraphs. "
                    "Keep it concise (3-5 sentences per scheme). "
                    "If multiple schemes match, separate them clearly with blank lines. "
                    "Always include the website/application link if available."
                )

                ai_text = generate_text_with_gemini(prompt)
                if ai_text and ai_text.strip():
                    return {
                        'text': ai_text.strip(),
                        'confidence': 0.85,
                        'intent': intent,
                        'scheme_count': len(schemes)
                    }
            except Exception as e:
                logger.warning(f"Gemini response generation failed: {e}")

            # Fallback to structured base responses if Gemini fails
            if intent == 'get_info':
                base_response = self._get_info_response(schemes, language)
            elif intent == 'eligibility':
                base_response = self._get_eligibility_response(schemes, language)
            elif intent == 'application':
                base_response = self._get_application_response(schemes, language)
            elif intent == 'benefits':
                base_response = self._get_benefits_response(schemes, language)
            else:
                base_response = self._get_general_response(schemes, query, language)

            return {
                'text': base_response,
                'confidence': 0.75,
                'intent': intent,
                'scheme_count': len(schemes)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'text': self._get_error_response(language),
                'confidence': 0.0,
                'intent': intent,
                'scheme_count': 0
            }
    
    def _get_greeting_response(self, language: str) -> str:
        """Get greeting response"""
        responses = {
            'en': "Hello! I'm your Government Scheme Assistant. I can help you find information about various government schemes. What would you like to know?",
            'hi': "नमस्ते! मैं आपका सरकारी योजना सहायक हूं। मैं आपको विभिन्न सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। आप क्या जानना चाहते हैं?",
            'kn': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಯೋಜನೆ ಸಹಾಯಕ. ನಾನು ವಿವಿಧ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಲು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಹುದು. ನೀವು ಏನು ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?"
        }
        return responses.get(language, responses['en'])
    
    def _get_help_response(self, language: str) -> str:
        """Get help response"""
        responses = {
            'en': "I can help you with:\n• Finding government schemes by sector (agriculture, health, education, employment)\n• Checking eligibility criteria\n• Understanding benefits and application process\n• Getting scheme details and contact information\n\nJust ask me about any scheme or topic!",
            'hi': "मैं आपकी इन चीजों में मदद कर सकता हूं:\n• क्षेत्र के अनुसार सरकारी योजनाएं खोजना (कृषि, स्वास्थ्य, शिक्षा, रोजगार)\n• पात्रता मानदंड जांचना\n• लाभ और आवेदन प्रक्रिया समझना\n• योजना विवरण और संपर्क जानकारी प्राप्त करना\n\nबस किसी भी योजना या विषय के बारे में पूछें!",
            'kn': "ನಾನು ನಿಮಗೆ ಇವುಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು:\n• ಕ್ಷೇತ್ರದ ಪ್ರಕಾರ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕುವುದು (ಕೃಷಿ, ಆರೋಗ್ಯ, ಶಿಕ್ಷಣ, ಉದ್ಯೋಗ)\n• ಅರ್ಹತಾ ಮಾನದಂಡಗಳನ್ನು ಪರಿಶೀಲಿಸುವುದು\n• ಪ್ರಯೋಜನಗಳು ಮತ್ತು ಅರ್ಜಿ ಪ್ರಕ್ರಿಯೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವುದು\n• ಯೋಜನೆ ವಿವರಗಳು ಮತ್ತು ಸಂಪರ್ಕ ಮಾಹಿತಿ ಪಡೆಯುವುದು\n\nಯಾವುದೇ ಯೋಜನೆ ಅಥವಾ ವಿಷಯದ ಬಗ್ಗೆ ಕೇಳಿ!"
        }
        return responses.get(language, responses['en'])
    
    def _get_info_response(self, schemes: List[Dict], language: str) -> str:
        """Get information response with complete scheme details"""
        if not schemes:
            return self._get_no_results_response('get_info', language)
        
        scheme = schemes[0] if isinstance(schemes[0], dict) else schemes[0]
        
        if isinstance(scheme, dict):
            title = scheme.get('title', '')
            desc = scheme.get('short_description', '') or scheme.get('description', '')[:200]
            sector = scheme.get('sector', '')
            ministry = scheme.get('ministry', '')
            eligibility = scheme.get('eligibility_criteria', '')[:200]
            benefits = scheme.get('benefits', '')[:200]
            link = scheme.get('website', '') or scheme.get('application_link', '') or scheme.get('source_url', '')
        else:
            title = getattr(scheme, 'title', '')
            desc = getattr(scheme, 'short_description', '') or getattr(scheme, 'description', '')[:200]
            sector = getattr(scheme.sector, 'name', '') if scheme.sector else ''
            ministry = getattr(scheme, 'ministry', '')
            eligibility = getattr(scheme, 'eligibility_criteria', '')[:200]
            benefits = getattr(scheme, 'benefits', '')[:200]
            link = getattr(scheme, 'website', '') or getattr(scheme, 'application_link', '') or getattr(scheme, 'source_url', '')
        
        response = f"**{title}**\n\n"
        response += f"📋 **Description:** {desc}\n\n"
        if sector:
            response += f"🏢 **Sector:** {sector}\n"
        if ministry:
            response += f"🏛️ **Ministry:** {ministry}\n\n"
        if eligibility:
            response += f"✅ **Eligibility:** {eligibility}...\n\n"
        if benefits:
            response += f"💰 **Benefits:** {benefits}...\n\n"
        if link:
            response += f"🔗 **More info:** {link}"
        
        return response
    
    def _get_eligibility_response(self, schemes: List[Dict], language: str) -> str:
        """Get eligibility response"""
        if not schemes:
            return self._get_no_results_response('eligibility', language)
        
        response = "**Eligibility Criteria:**\n\n"
        
        for i, scheme in enumerate(schemes[:3], 1):
            if isinstance(scheme, dict):
                title = scheme.get('title', '')
                eligibility = scheme.get('eligibility_criteria', 'Not specified')
            else:
                title = getattr(scheme, 'title', '')
                eligibility = getattr(scheme, 'eligibility_criteria', 'Not specified')
            
            response += f"{i}. **{title}**\n"
            response += f"   {eligibility[:250]}...\n\n"
        
        return response
    
    def _get_application_response(self, schemes: List[Dict], language: str) -> str:
        """Get application process response with documents and links"""
        if not schemes:
            return self._get_no_results_response('application', language)
        
        response = "**How to Apply:**\n\n"
        
        for i, scheme in enumerate(schemes[:3], 1):
            if isinstance(scheme, dict):
                title = scheme.get('title', '')
                app_process = scheme.get('application_process', '')
                docs = scheme.get('required_documents', [])
                link = scheme.get('application_link', '') or scheme.get('website', '')
            else:
                title = getattr(scheme, 'title', '')
                app_process = getattr(scheme, 'application_process', '')
                docs = getattr(scheme, 'required_documents', [])
                link = getattr(scheme, 'application_link', '') or getattr(scheme, 'website', '')
            
            response += f"{i}. **{title}**\n"
            if app_process:
                response += f"   📝 **Process:** {app_process[:200]}...\n"
            if docs and isinstance(docs, list):
                response += f"   📄 **Documents:** {', '.join(docs[:5])}\n"
            if link:
                response += f"   🔗 **Apply:** {link}\n\n"
        
        return response
    
    def _get_benefits_response(self, schemes: List[Dict], language: str) -> str:
        """Get benefits response"""
        if not schemes:
            return self._get_no_results_response('benefits', language)
        
        response = "**Benefits Provided:**\n\n"
        
        for i, scheme in enumerate(schemes[:3], 1):
            if isinstance(scheme, dict):
                title = scheme.get('title', '')
                benefits = scheme.get('benefits', 'Not specified')
            else:
                title = getattr(scheme, 'title', '')
                benefits = getattr(scheme, 'benefits', 'Not specified')
            
            response += f"{i}. **{title}**\n"
            response += f"   💰 {benefits[:250]}...\n\n"
        
        return response
    
    def _get_general_response(self, schemes: List[Dict], query: str, language: str) -> str:
        """Get general response with comprehensive scheme overview"""
        if not schemes:
            return self._get_no_results_response('general_query', language)
        
        response = f"Found **{len(schemes)} scheme(s)**:\n\n"
        
        # Show up to 15 schemes for sector/category searches
        for i, scheme in enumerate(schemes[:15], 1):
            if isinstance(scheme, dict):
                title = scheme.get('title', '')
                sector = scheme.get('sector', '')
                desc = scheme.get('short_description', '')[:150]
                benefits = scheme.get('benefits', '')[:100]
                link = scheme.get('website', '') or scheme.get('source_url', '')
            else:
                title = getattr(scheme, 'title', '')
                sector = getattr(scheme.sector, 'name', '') if scheme.sector else ''
                desc = getattr(scheme, 'short_description', '')[:150]
                benefits = getattr(scheme, 'benefits', '')[:100]
                link = getattr(scheme, 'website', '') or getattr(scheme, 'source_url', '')
            
            response += f"{i}. **{title}**\n"
            if sector:
                response += f"   🏢 {sector}\n"
            if desc:
                response += f"   📋 {desc}\n"
            if benefits:
                response += f"   💰 {benefits}\n"
            if link:
                response += f"   🔗 {link}\n"
            response += "\n"
        
        return response
    
    def _get_no_results_response(self, intent: str, language: str) -> str:
        """Get response when no schemes are found"""
        responses = {
            'en': "I couldn't find any schemes matching your query. Please try rephrasing your question or ask about a specific sector like agriculture, health, education, or employment.",
            'hi': "मुझे आपके प्रश्न से मेल खाने वाली कोई योजना नहीं मिली। कृपया अपना प्रश्न दोबारा पूछें या कृषि, स्वास्थ्य, शिक्षा या रोजगार जैसे किसी विशिष्ट क्षेत्र के बारे में पूछें।",
            'kn': "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಹೊಂದಾಣಿಕೆಯಾಗುವ ಯಾವುದೇ ಯೋಜನೆಗಳು ನನಗೆ ಸಿಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಮತ್ತೆ ಕೇಳಿ ಅಥವಾ ಕೃಷಿ, ಆರೋಗ್ಯ, ಶಿಕ್ಷಣ ಅಥವಾ ಉದ್ಯೋಗದಂತಹ ನಿರ್ದಿಷ್ಟ ಕ್ಷೇತ್ರದ ಬಗ್ಗೆ ಕೇಳಿ."
        }
        return responses.get(language, responses['en'])
    
    def _get_error_response(self, language: str) -> str:
        """Get error response"""
        responses = {
            'en': "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question.",
            'hi': "मुझे खेद है, आपके अनुरोध को संसाधित करने में त्रुटि आई। कृपया पुनः प्रयास करें या अपना प्रश्न दोबारा पूछें।",
            'kn': "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಸಂಸ್ಕರಿಸುವಾಗ ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಮತ್ತೆ ಕೇಳಿ."
        }
        return responses.get(language, responses['en'])
    
    def _format_scheme(self, scheme: Dict) -> Dict:
        """Format scheme for API response"""
        return {
            'id': str(scheme.get('_id', '')),
            'title': scheme.get('title', ''),
            'description': scheme.get('description', ''),
            'short_description': scheme.get('short_description', ''),
            'sector': scheme.get('sector', ''),
            'ministry': scheme.get('ministry', ''),
            'department': scheme.get('department', ''),
            'government_level': scheme.get('government_level', ''),
            'state': scheme.get('state', ''),
            'eligibility_criteria': scheme.get('eligibility_criteria', ''),
            'benefits': scheme.get('benefits', ''),
            'application_process': scheme.get('application_process', ''),
            'application_link': scheme.get('application_link', ''),
            'launch_date': scheme.get('launch_date', ''),
            'last_date': scheme.get('last_date', ''),
            'helpline_number': scheme.get('helpline_number', ''),
            'email': scheme.get('email', ''),
            'website': scheme.get('website', ''),
            'source_url': scheme.get('source_url', ''),
            'keywords': scheme.get('keywords', []),
            'search_tags': scheme.get('search_tags', []),
            'language': scheme.get('language', 'en'),
            'is_active': scheme.get('is_active', True)
        }


# Global chatbot instance
chatbot = GovernmentChatbot()
