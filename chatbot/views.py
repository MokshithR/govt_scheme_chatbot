"""
Views for the Government Voice Chatbot
Integrates chatbot logic, voice processing, and MongoDB adapter
"""

import json
import uuid
import tempfile
import os
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views import View
from django.middleware.csrf import get_token
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Import our sophisticated backend modules
from .chatbot_logic import chatbot
from .voice_processing import VoiceProcessor
from .gemini_utils import generate_text_with_gemini
from .fallback_translations import FALLBACK_TRANSLATIONS
from .fast_translator import get_fast_translator
from .models import (
    GovernmentScheme,
    ChatSession,
    ChatMessage,
    UserProfile,
    UserSchemeInteraction,
    UserSearchHistory,
    UserNotification,
)

logger = logging.getLogger(__name__)

# Initialize voice processor
try:
    voice_processor = VoiceProcessor()
    logger.info("Voice processor initialized successfully")
except Exception as e:
    logger.warning(f"Voice processor initialization failed: {e}")
    voice_processor = None


def login_page(request):
    """Render the YOJANA MITHRA login page"""
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('chatbot:home')
    return render(request, 'login.html')


def logout_view(request):
    """Logout user and redirect to login page"""
    logout(request)
    from django.shortcuts import redirect
    return redirect('chatbot:login_page')


@login_required(login_url='/login/')
def home(request):
    """Render the main YOJANA MITHRA chatbot interface"""
    return render(request, 'home.html', {
        'user': request.user,
        'brand_name': 'YOJANA MITHRA'
    })


def translate_schemes_list(schemes, lang):
    """
    Translate a list of schemes to the target language.
    Returns formatted plain text without markdown, suitable for TTS.
    
    Args:
        schemes: List of GovernmentScheme objects
        lang: Target language code ('en', 'kn', 'hi')
    
    Returns:
        str: Translated, formatted plain text
    """
    if lang == 'en' or not schemes:
        # Return English formatted text
        return format_schemes_plain_text(schemes, 'en')
    
    # Format schemes in English first
    english_text = format_schemes_plain_text(schemes, 'en')
    
    # Translate to target language using Gemini
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
    
    target_lang_name = language_names.get(lang, lang)
    
    prompt = f"""Translate this list of Indian Government Schemes from English to {target_lang_name}.

IMPORTANT FORMATTING RULES:
- Use PLAIN TEXT only - NO markdown symbols (* # - etc.)
- Use natural bullet points or numbered lists in {target_lang_name}
- Keep scheme names in English (they are official names)
- Translate ALL descriptions, benefits, eligibility, and other content
- Use formal, government-appropriate language
- Make it clear and easy to understand for native speakers
- Do NOT use asterisks, hashtags, or markdown formatting
- Use proper {target_lang_name} script and grammar

English text:
{english_text}

{target_lang_name} translation (plain text, no markdown):"""

    try:
        translated = generate_text_with_gemini(prompt)
        if translated and len(translated.strip()) > 50:
            return translated.strip()
        else:
            logger.warning(f"Translation to {target_lang_name} failed, using English")
            return english_text
    except Exception as e:
        logger.error(f"Scheme list translation error: {e}")
        return english_text


def format_schemes_plain_text(schemes, lang='en'):
    """
    Format schemes as clean plain text without markdown.
    
    Args:
        schemes: List of GovernmentScheme objects
        lang: Language code (for future use)
    
    Returns:
        str: Formatted plain text
    """
    if not schemes:
        return "No schemes available."
    
    output = []
    output.append(f"Available Government Schemes ({len(schemes)} total)\n")
    
    for idx, scheme in enumerate(schemes, 1):
        output.append(f"\n{idx}. {scheme.title}")
        
        # Sector
        if scheme.sector:
            output.append(f"   Sector: {scheme.sector.name}")
        
        # Description
        if scheme.description:
            desc = scheme.description[:200] + "..." if len(scheme.description) > 200 else scheme.description
            output.append(f"   Description: {desc}")
        
        # Benefits
        if scheme.benefits:
            benefits = scheme.benefits[:150] + "..." if len(scheme.benefits) > 150 else scheme.benefits
            output.append(f"   Benefits: {benefits}")
        
        # Eligibility
        if scheme.eligibility:
            eligibility = scheme.eligibility[:150] + "..." if len(scheme.eligibility) > 150 else scheme.eligibility
            output.append(f"   Eligibility: {eligibility}")
        
        # Ministry
        if scheme.ministry_department:
            output.append(f"   Ministry: {scheme.ministry_department}")
        
        # Website
        if scheme.official_website:
            output.append(f"   Website: {scheme.official_website}")
    
    return "\n".join(output)


def schemes_all(request):
    """Render a page with all GovernmentScheme entries present in the database.
    Groups schemes by sector with filter buttons.
    Supports multilingual display based on 'lang' query parameter.
    """
    from collections import defaultdict
    
    # Get language from query parameter (default: en)
    lang = request.GET.get('lang', 'en')
    
    try:
        schemes = list(GovernmentScheme.objects.select_related('sector').order_by('sector__name', 'title').all())
        # Group schemes by sector
        schemes_by_sector = defaultdict(list)
        for scheme in schemes:
            sector_name = scheme.sector.name if scheme.sector else 'Other'
            schemes_by_sector[sector_name].append(scheme)
        # Get sector counts for buttons
        sector_counts = {sector: len(items) for sector, items in schemes_by_sector.items()}
    except Exception:
        schemes = []
        schemes_by_sector = {}
        sector_counts = {}
    
    return render(request, 'schemes_list.html', {
        'schemes': schemes,
        'count': len(schemes),
        'schemes_by_sector': dict(schemes_by_sector),
        'sector_counts': sector_counts,
        'lang': lang  # Pass language to template
    })


def scheme_detail(request, scheme_id):
    """Display detailed information about a specific government scheme.
    
    Shows all available fields including:
    - Basic info (title, description, sector)
    - Eligibility criteria and benefits
    - Application process and required documents
    - Financial assistance details
    - Contact information (helpline, email, website)
    - Important dates and validity
    - Keywords, tags, and translations
    - Action buttons for application and official website
    
    Supports multilingual display via 'lang' query parameter.
    """
    from django.shortcuts import get_object_or_404
    import json
    
    # Get language from query parameter
    lang = request.GET.get('lang', 'en')
    
    # Fetch scheme with related sector data
    scheme = get_object_or_404(
        GovernmentScheme.objects.select_related('sector'),
        pk=scheme_id
    )

    # Check cache first for complete translated scheme
    cache_key = f"scheme_detail:{scheme_id}:{lang}"
    if cache_key in _translation_cache:
        logger.info(f"Using cached translation for scheme {scheme_id} in {lang}")
        cached_data = _translation_cache[cache_key]
        
        # Use cached translations
        display_title = cached_data.get('title', scheme.title)
        display_description = cached_data.get('description', scheme.description or '')
        display_short_description = cached_data.get('short_description', scheme.short_description or '')
        display_benefits = cached_data.get('benefits', scheme.benefits or '')
        display_eligibility = cached_data.get('eligibility_criteria', scheme.eligibility_criteria or '')
        display_application_process = cached_data.get('application_process', scheme.application_process or '')
        display_financial_assistance = cached_data.get('financial_assistance', scheme.financial_assistance or '')
        display_ministry = cached_data.get('ministry', scheme.ministry or '')
        display_department = cached_data.get('department', scheme.department or '')
        display_sector_name = cached_data.get('sector_name', scheme.sector.name if scheme.sector else '')
        display_government_level = cached_data.get('government_level', scheme.government_level or '')
        display_state = cached_data.get('state', scheme.state or '')
    else:
        # No cache - need to translate
        logger.info(f"Translating scheme {scheme_id} to {lang} (not in cache)")
        
        # Helper function to get translated text (database first, then API translation)
        def get_translated_field(field_name, original_value):
            """Get translation from database or use Google Translate"""
            if lang == 'en' or not original_value:
                return original_value
            
            # Try database translation first
            if field_name in ['title', 'description']:
                if field_name == 'title':
                    db_translation = scheme.get_title(lang)
                else:
                    db_translation = scheme.get_description(lang)
                
                # If database has translation (not fallback to English), use it
                if db_translation != original_value:
                    return db_translation
            else:
                # For other fields, use get_field_translation
                db_translation = scheme.get_field_translation(field_name, lang)
                if db_translation != original_value:
                    return db_translation
            
            # No database translation found - use Google Translate
            try:
                from chatbot.fast_translator import get_fast_translator
                translator = get_fast_translator()
                translated = translator.translate(original_value, lang)
                return translated
            except Exception as e:
                logger.error(f"Translation failed for {field_name}: {e}")
                return original_value

        # Compute language-aware display fields
        display_title = get_translated_field('title', scheme.title)
        display_description = get_translated_field('description', scheme.description or '')
        display_short_description = get_translated_field('short_description', scheme.short_description or '')
        display_benefits = get_translated_field('benefits', scheme.benefits or '')
        display_eligibility = get_translated_field('eligibility_criteria', scheme.eligibility_criteria or '')
        display_application_process = get_translated_field('application_process', scheme.application_process or '')
        display_financial_assistance = get_translated_field('financial_assistance', scheme.financial_assistance or '')
        
        # Translate other fields too
        display_ministry = get_translated_field('ministry', scheme.ministry or '')
        display_department = get_translated_field('department', scheme.department or '')
        display_sector_name = get_translated_field('sector_name', scheme.sector.name if scheme.sector else '')
        display_government_level = get_translated_field('government_level', scheme.government_level or '')
        display_state = get_translated_field('state', scheme.state or '')
        
        # Cache the translations for future use
        _translation_cache[cache_key] = {
            'title': display_title,
            'description': display_description,
            'short_description': display_short_description,
            'benefits': display_benefits,
            'eligibility_criteria': display_eligibility,
            'application_process': display_application_process,
            'financial_assistance': display_financial_assistance,
            'ministry': display_ministry,
            'department': display_department,
            'sector_name': display_sector_name,
            'government_level': display_government_level,
            'state': display_state,
        }
        logger.info(f"Cached translation for scheme {scheme_id} in {lang}")

    # Process JSON fields for template rendering
    context = {
        'scheme': scheme,
        'sector_name': display_sector_name,
        'lang': lang,  # Pass language to template
        'display_title': display_title,
        'display_description': display_description,
        'display_short_description': display_short_description,
        'display_benefits': display_benefits,
        'display_eligibility': display_eligibility,
        'display_application_process': display_application_process,
        'display_financial_assistance': display_financial_assistance,
        'display_ministry': display_ministry,
        'display_department': display_department,
        'display_government_level': display_government_level,
        'display_state': display_state,
        
        # Parse JSON fields safely
        'keywords': scheme.keywords if isinstance(scheme.keywords, list) else [],
        'search_tags': scheme.search_tags if isinstance(scheme.search_tags, list) else [],
        'sub_sectors': scheme.sub_sectors if isinstance(scheme.sub_sectors, list) else [],
        'required_documents': scheme.required_documents if isinstance(scheme.required_documents, list) else [],
        
        # Parse translations
        'title_translations': scheme.title_translations if isinstance(scheme.title_translations, dict) else {},
        'description_translations': scheme.description_translations if isinstance(scheme.description_translations, dict) else {},
        
        # Format dates
        'launch_date_formatted': scheme.launch_date.strftime('%B %d, %Y') if scheme.launch_date else None,
        'last_date_formatted': scheme.last_date.strftime('%B %d, %Y') if scheme.last_date else None,
    }
    
    return render(request, 'scheme_detail.html', context)


def translation_test(request):
    """Test page for translation API"""
    return render(request, 'translation_test.html')


def test_microphone(request):
    """Test page for microphone diagnostics"""
    return render(request, 'test_microphone.html')


@csrf_exempt
@require_http_methods(["POST"])
def admin_generate_details(request):
    """Generate scheme details for admin autofill.
    Order of operation:
      1) If GOOGLE_API_KEY is set and google-generativeai is available, use Gemini to generate.
      2) Otherwise, return a safe local stub so the admin remains usable offline.
    """
    try:
        import json
        import os

        data = json.loads(request.body.decode('utf-8'))
        title = (data.get('title') or '').strip()
        field = (data.get('field') or '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)

        # If a specific field is requested, use the shared Gemini helper to generate only that
        # field's content and return a simple shape: {success, field, value}.
        if field:
            # Map field identifiers from frontend to human-readable prompts
            field_prompts = {
                'description': "a detailed scheme description",
                'short_description': "a 2-3 line concise summary",
                'ministry': "the most likely responsible ministry name",
                'eligibility_criteria': "clear bullet-point eligibility criteria",
                'benefits': "clear bullet-point list of benefits",
                'financial_assistance': "details of financial assistance provided",
                'application_process': "step-by-step application process",
                'required_documents': "bullet list of required documents",
                'application_link': "a plausible official application URL (if known) or guidance text",
                'helpline_number': "a helpline number or guidance on where to find it",
                'email': "an official email or guidance on contacting the department",
                'website': "the official scheme or department website URL",
                'source_url': "the primary source URL where scheme information is published",
            }

            hint = field_prompts.get(field)
            if not hint:
                return JsonResponse({'success': False, 'error': f'Unsupported field: {field}'}, status=400)

            prompt = (
                "You are helping an admin fill details for an Indian government scheme titled '" + title + "'. "
                "Generate " + hint + ". "
                "Focus only on that field, in English. "
                "Do not repeat the title unless helpful, and avoid extra commentary."
            )
            generated_text = generate_text_with_gemini(prompt)
            return JsonResponse({
                'success': True,
                'provider': 'gemini_utils',
                'field': field,
                'value': generated_text or ''
            })

        def _stub():
            return {
                'generated_description': (
                    f"Overview of {title}. This scheme aims to provide benefits to eligible citizens "
                    f"with a focus on impact and accessibility."
                ),
                'generated_short_description': (
                    f"Brief summary of {title} with key purpose and target beneficiaries."
                ),
                'generated_ministry': "Ministry of [Relevant Ministry]",
                'generated_eligibility': (
                    "Eligibility includes domicile-based criteria, income thresholds, and applicable "
                    "demographic groups as notified by the department."
                ),
                'generated_benefits': (
                    "Financial assistance, subsidies, or in-kind support as per scheme guidelines. "
                    "Benefits vary by applicant category."
                ),
                'generated_financial_assistance': (
                    "Assistance may include direct benefit transfer, subsidies, or reimbursement as per norms."
                ),
                'generated_application_process': (
                    "Apply online via official portal or offline at designated centers; submit required documents; track status online."
                ),
                'generated_documents': (
                    "Proof of identity; address; income certificate; age/domicile certificate; bank passbook; passport photo."
                ),
                'generated_application_link': "https://www.example.gov.in/apply",
                'generated_helpline_number': "1800-000-0000",
                'generated_email': "support@example.gov.in",
                'generated_website': "https://www.example.gov.in",
                'generated_source_url': "https://www.source.example.gov.in/scheme"
            }

        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            try:
                # Lazy import so the app runs even if the package is not installed
                import google.generativeai as genai
                genai.configure(api_key=api_key)

                # Prefer a lightweight, fast model
                model_names = [
                    'gemini-1.5-flash',
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-pro',   # fallback if flash not available
                    'gemini-pro'        # legacy name fallback
                ]

                prompt = (
                    "You are assisting a government schemes admin to fill structured fields. "
                    "Given a scheme title, generate concise content in English for these fields: "
                    "description, short_description, ministry, eligibility, benefits, financial_assistance, "
                    "application_process, required_documents, application_link, helpline_number, email, website, source_url. "
                    "Keep it neutral, factual, and generic if the title is ambiguous. "
                    "Return STRICT JSON with exactly these keys: "
                    "generated_description, generated_short_description, generated_ministry, generated_eligibility, "
                    "generated_benefits, generated_financial_assistance, generated_application_process, generated_documents, "
                    "generated_application_link, generated_helpline_number, generated_email, generated_website, generated_source_url."
                )

                response_text = None
                last_error = None
                for name in model_names:
                    try:
                        model = genai.GenerativeModel(name)
                        # Ask the model to return JSON directly to reduce parsing issues
                        gen_cfg = { 'response_mime_type': 'application/json' }
                        resp = model.generate_content(
                            f"Title: {title}\n\n{prompt}",
                            generation_config=gen_cfg
                        )
                        # Newer SDK returns .text; some return candidate parts
                        if hasattr(resp, 'text') and resp.text:
                            response_text = resp.text
                        elif getattr(resp, 'candidates', None):
                            parts = []
                            for c in resp.candidates:
                                ct = getattr(getattr(c, 'content', None), 'parts', []) or []
                                for p in ct:
                                    val = getattr(p, 'text', None)
                                    if val:
                                        parts.append(val)
                            response_text = "\n".join(parts).strip() if parts else None
                        if response_text:
                            break
                    except Exception as inner_e:
                        last_error = inner_e
                        continue

                if response_text:
                    # Try to parse JSON strictly
                    try:
                        cleaned = response_text.strip()
                        payload = json.loads(cleaned)

                        base = _stub()
                        # Keep only known keys as strings
                        for k in list(base.keys()):
                            if k in payload and isinstance(payload[k], str) and payload[k].strip():
                                base[k] = payload[k].strip()
                        return JsonResponse({'success': True, 'provider': 'gemini', **base})
                    except Exception as parse_e:
                        logger.info(f"Gemini JSON parse failed, falling back to stub: {parse_e}")
                else:
                    if last_error:
                        logger.info(f"Gemini generation produced no text: {last_error}")
            except Exception as e:
                logger.info(f"Gemini not used (missing package or error): {e}")

        # Fallback: local stub
        return JsonResponse({'success': True, 'provider': 'stub', **_stub()})

    except Exception as e:
        logger.warning(f"admin_generate_details failed: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def voice_api(request):
    """
    Handle voice input from the frontend
    This endpoint processes voice input and returns both text and audio responses
    """
    try:
        # Generate or get session ID
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        # Set chatbot session
        chatbot.set_session(session_id)
        
        # Get language from 'lang' parameter (user-selected from dropdown)
        user_lang = request.POST.get('lang', 'en')
        if user_lang not in ['en', 'kn', 'hi']:
            user_lang = 'en'  # Default to English if invalid
        chatbot.set_language(user_lang)
        
        # Handle voice input
        if 'audio' in request.FILES:
            # Process uploaded audio file
            audio_file = request.FILES['audio']
            
            # Save audio file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Process voice query using our sophisticated voice processor
                result = chatbot.process_voice_query(temp_file_path)
                
                if result['success']:
                    return JsonResponse({
                        'success': True,
                        'you': result.get('text_response', ''),
                        'bot': result.get('text_response', ''),
                        'audio_response': result.get('audio_response', ''),
                        'audio_format': result.get('audio_format', None),
                        'audio_error': result.get('audio_error', None),
                        'language': result.get('language', 'en'),
                        'schemes': result.get('schemes', []),
                        'confidence': result.get('confidence', 0.8)
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': result.get('error', 'Voice processing failed'),
                        'bot': 'Sorry, I could not process your voice input. Please try again.'
                    })
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        else:
            # Fallback: Use microphone input (for development/testing)
            # This simulates voice input for testing purposes
            return JsonResponse({
                'success': False,
                'error': 'No audio file provided',
                'bot': 'Please provide an audio file or use the microphone.'
            })
    
    except Exception as e:
        logger.error(f"Voice API error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'bot': 'Sorry, there was an error processing your request. Please try again.'
        })


@api_view(['POST'])
def text_chat_api(request):
    """
    Handle text-based chat queries
    This endpoint processes text input and returns relevant scheme information
    """
    try:
        data = request.data
        query = data.get('query', '').strip()
        # Accept 'lang' parameter from frontend (user-selected language)
        user_lang = data.get('lang', data.get('language', 'en'))
        if user_lang not in ['en', 'kn', 'hi']:
            user_lang = 'en'  # Default to English if invalid
        
        logger.info(f"Received text query: {query}, language: {user_lang}")
        
        if not query:
            return Response({
                'success': False,
                'error': 'Query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate or get session ID
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        # Set chatbot session and language
        chatbot.set_session(session_id)
        chatbot.set_language(user_lang)
        
        # Process the query using our sophisticated chatbot logic
        result = chatbot.process_query(query, user_lang)
        
        logger.info(f"Chatbot result: {result}")
        
        if result['success']:
            return Response({
                'success': True,
                'response': result['response']['text'],
                'schemes': result['schemes'],
                'intent': result['intent'],
                'keywords': result['keywords'],
                'language': result['language'],
                'confidence': result['response'].get('confidence', 0.8),
                'scheme_count': len(result['schemes'])
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Query processing failed'),
                'response': result['response']['text']
            })
    
    except Exception as e:
        logger.error(f"Text chat API error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'response': 'Sorry, there was an error processing your request. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def chat_history_api(request, session_id):
    """
    Get chat history for a specific session
    """
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        history = []
        for message in messages:
            history.append({
                'type': message.message_type,
                'content': message.text_content,
                'timestamp': message.timestamp.isoformat(),
                'language': message.language,
                'confidence': message.confidence_score,
                'related_schemes': message.related_schemes
            })
        
        return Response({
            'success': True,
            'session_id': session_id,
            'language': session.language,
            'message_count': len(history),
            'messages': history
        })
    
    except ChatSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== USER AUTHENTICATION VIEWS ====================

@csrf_exempt
@api_view(['POST'])
def user_register(request):
    """
    Register a new user with profile information
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'error': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format
        try:
            validate_email(data['email'])
        except ValidationError:
            return Response({
                'success': False,
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return Response({
                'success': False,
                'error': 'Email already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user with transaction
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            
            # Create user profile
            from .models import UserProfile
            profile = UserProfile.objects.create(
                user=user,
                phone_number=data.get('phone_number', ''),
                age=data.get('age'),
                gender=data.get('gender'),
                education=data.get('education'),
                employment_status=data.get('employment_status'),
                state=data.get('state'),
                district=data.get('district'),
                pincode=data.get('pincode'),
                preferred_language=data.get('preferred_language', 'en'),
                interested_sectors=data.get('interested_sectors', []),
                notification_preferences=data.get('notification_preferences', {
                    'email_notifications': True,
                    'sms_notifications': False,
                    'scheme_recommendations': True,
                    'deadline_reminders': True
                })
            )
            
            # Log the user in
            login(request, user)
            
            return Response({
                'success': True,
                'message': 'Registration successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile': {
                        'preferred_language': profile.preferred_language,
                        'state': profile.state,
                        'interested_sectors': profile.interested_sectors
                    }
                }
            }, status=status.HTTP_201_CREATED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return Response({
            'success': False,
            'error': 'Registration failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def user_login(request):
    """
    Authenticate and login user
    """
    try:
        data = json.loads(request.body)
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Get user profile - handle missing fields gracefully
            profile_data = {}
            try:
                if hasattr(user, 'govt_profile'):
                    profile = user.govt_profile
                    profile_data = {
                        'preferred_language': getattr(profile, 'preferred_language', 'en'),
                        'state': getattr(profile, 'state', ''),
                        'interested_sectors': getattr(profile, 'interested_sectors', ''),
                    }
                    # Only add phone_number and is_verified if they exist
                    if hasattr(profile, 'phone_number'):
                        profile_data['phone_number'] = profile.phone_number
                    if hasattr(profile, 'is_verified'):
                        profile_data['is_verified'] = profile.is_verified
            except Exception as e:
                logger.warning(f"Profile data error: {e}")
                profile_data = {}
            
            # Update last login - handle gracefully
            try:
                from .models import UserProfile
                if hasattr(user, 'govt_profile'):
                    user.govt_profile.last_login = timezone.now()
                    user.govt_profile.save()
            except Exception as e:
                logger.warning(f"Last login update error: {e}")
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile': profile_data
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return Response({
            'success': False,
            'error': 'Login failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def user_logout(request):
    """
    Logout the current user
    """
    try:
        logout(request)
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({
            'success': False,
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@login_required
def user_profile(request):
    """
    Get current user profile information
    """
    try:
        user = request.user
        
        # Get user profile
        try:
            profile = user.govt_profile
            profile_data = {
                'phone_number': profile.phone_number,
                'age': profile.age,
                'gender': profile.gender,
                'education': profile.education,
                'employment_status': profile.employment_status,
                'state': profile.state,
                'district': profile.district,
                'pincode': profile.pincode,
                'preferred_language': profile.preferred_language,
                'interested_sectors': profile.interested_sectors,
                'notification_preferences': profile.notification_preferences,
                'is_verified': profile.is_verified,
                'created_at': profile.created_at.isoformat(),
                'last_login': profile.last_login.isoformat() if profile.last_login else None
            }
        except:
            profile_data = {}
        
        # Get user statistics
        from .models import UserSchemeInteraction, UserSearchHistory, UserNotification
        
        interactions_count = UserSchemeInteraction.objects.filter(user=user).count()
        searches_count = UserSearchHistory.objects.filter(user=user).count()
        unread_notifications = UserNotification.objects.filter(user=user, is_read=False).count()
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat(),
                'profile': profile_data,
                'statistics': {
                    'interactions_count': interactions_count,
                    'searches_count': searches_count,
                    'unread_notifications': unread_notifications
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@login_required
def update_profile(request):
    """
    Update user profile information
    """
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update user basic info
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Validate new email
            try:
                validate_email(data['email'])
                if User.objects.exclude(id=user.id).filter(email=data['email']).exists():
                    return Response({
                        'success': False,
                        'error': 'Email already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.email = data['email']
            except ValidationError:
                return Response({
                    'success': False,
                    'error': 'Invalid email format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        user.save()
        
        # Update or create profile
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update profile fields
        profile_fields = [
            'phone_number', 'age', 'gender', 'education', 'employment_status',
            'state', 'district', 'pincode', 'preferred_language', 
            'interested_sectors', 'notification_preferences'
        ]
        
        for field in profile_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        profile.save()
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully'
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return Response({
            'success': False,
            'error': 'Failed to update profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@login_required
def user_notifications(request):
    """
    Get user notifications
    """
    try:
        user = request.user
        notifications = UserNotification.objects.filter(user=user)[:20]  # Last 20 notifications
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'scheme_id': notification.scheme_id,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'notifications': notifications_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Notifications fetch error: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read
    """
    try:
        user = request.user
        
        try:
            notification = UserNotification.objects.get(id=notification_id, user=user)
            notification.is_read = True
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            }, status=status.HTTP_200_OK)
            
        except UserNotification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Mark notification error: {e}")
        return Response({
            'success': False,
            'error': 'Failed to mark notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def check_auth_status(request):
    """
    Check if user is authenticated
    """
    try:
        if request.user.is_authenticated:
            user = request.user
            
            # Get basic profile info
            try:
                profile = user.govt_profile
                profile_data = {
                    'preferred_language': profile.preferred_language,
                    'state': profile.state,
                    'interested_sectors': profile.interested_sectors
                }
            except:
                profile_data = {}
            
            return Response({
                'success': True,
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'profile': profile_data
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': True,
                'authenticated': False
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        return Response({
            'success': False,
            'error': 'Failed to check auth status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def scheme_search_api(request):
    """
    Search for government schemes
    """
    try:
        query = request.GET.get('q', '').strip()
        sector = request.GET.get('sector', '')
        language = request.GET.get('language', 'en')
        limit = int(request.GET.get('limit', 10))
        
        if not query:
            return Response({
                'success': False,
                'error': 'Query parameter "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use chatbot logic to search schemes
        chatbot.set_language(language)
        result = chatbot.process_query(query, language)

        if not result['success']:
            return Response({
                'success': False,
                'error': 'Search failed',
                'schemes': []
            })

        schemes = result['schemes'][:limit]

        # Auto-generate voice output for the textual response (voice-only behavior)
        resp_text = ''
        try:
            resp_obj = result.get('response')
            if isinstance(resp_obj, dict):
                resp_text = resp_obj.get('text', '')
            elif isinstance(resp_obj, str):
                resp_text = resp_obj
        except Exception:
            resp_text = ''

        # Fallback to a simple summary if response text not available
        if not resp_text:
            # Build a short summary from the first scheme
            if schemes:
                first = schemes[0]
                resp_text = f"Here's information about {first.get('title','the matching scheme')}: {first.get('short_description','')[:200]}"
            else:
                resp_text = query

        # Generate speech (base64) using voice_processor
        try:
            tts = voice_processor.text_to_speech(resp_text, language=language, use_gtts=True)
            audio_b64 = tts.get('audio_data')
            audio_format = tts.get('format')
            audio_error = tts.get('error')
        except Exception as e:
            audio_b64 = None
            audio_format = None
            audio_error = str(e)

        return Response({
            'success': True,
            'query': query,
            'scheme_count': len(schemes),
            'schemes': schemes,
            'language': language,
            'audio_response': audio_b64,
            'audio_format': audio_format,
            'audio_error': audio_error
        })
    
    except Exception as e:
        logger.error(f"Scheme search API error: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'schemes': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def supported_languages_api(request):
    """
    Get list of supported languages
    """
    # Restrict UI language options to these three languages (English, Hindi, Kannada)
    languages = [
        {'code': 'en', 'name': 'English'},
        {'code': 'hi', 'name': 'Hindi'},
        {'code': 'kn', 'name': 'Kannada'},
    ]
    
    return Response({
        'success': True,
        'languages': languages,
        'default_language': 'en'
    })


@api_view(['GET'])
def available_sectors_api(request):
    """
    Get list of available sectors
    """
    sectors = [
        {'code': 'agriculture', 'name': 'Agriculture'},
        {'code': 'health', 'name': 'Health'},
        {'code': 'education', 'name': 'Education'},
        {'code': 'employment', 'name': 'Employment'},
        {'code': 'social_welfare', 'name': 'Social Welfare'},
        {'code': 'rural_development', 'name': 'Rural Development'},
        {'code': 'urban_development', 'name': 'Urban Development'},
        {'code': 'women_empowerment', 'name': 'Women Empowerment'},
        {'code': 'youth_development', 'name': 'Youth Development'},
        {'code': 'senior_citizens', 'name': 'Senior Citizens'},
        {'code': 'disability', 'name': 'Disability'}
    ]
    
    return Response({
        'success': True,
        'sectors': sectors
    })


@api_view(['POST', 'GET'])
def voice_test_api(request):
    """
    Simple test endpoint to generate TTS for a short text without uploading audio.
    POST or GET params:
      - text: text to speak (default: 'This is a voice test')
      - language: 'en'|'hi'|'kn' (default 'en')
      - use_gtts: optional 'true' or 'false' (default true)
    Returns JSON with base64 `audio_response`, `audio_format`, and `audio_error`.
    """
    try:
        text = request.data.get('text') if request.method == 'POST' else request.GET.get('text')
        language = request.data.get('language') if request.method == 'POST' else request.GET.get('language')
        use_gtts = request.data.get('use_gtts') if request.method == 'POST' else request.GET.get('use_gtts')
        text = (text or 'This is a voice test from the Government Scheme Assistant').strip()
        language = (language or 'en').strip()
        use_gtts_flag = True
        if use_gtts is not None and str(use_gtts).lower() in ('false', '0', 'no'):
            use_gtts_flag = False

        # Use the voice processor to generate speech
        try:
            result = voice_processor.text_to_speech(text, language=language, use_gtts=use_gtts_flag)
        except Exception as e:
            return Response({'success': False, 'error': f'TTS generation failed: {e}'}, status=500)

        return Response({
            'success': True,
            'text': text,
            'audio_response': result.get('audio_data'),
            'audio_format': result.get('format'),
            'audio_error': result.get('error')
        })
    except Exception as e:
        logger.error(f"voice_test_api error: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def database_status_api(request):
    """
    Check database status and connection
    """
    try:
        # Test MongoDB connection
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from mongodb_adapter import MongoDBAdapter
        
        adapter = MongoDBAdapter()
        
        # Test connection and get scheme count
        total_schemes = adapter.get_total_schemes()
        
        # Get sample schemes
        sample_schemes = adapter.search_schemes("agriculture", ["agriculture"], {}, "search")[:3]
        
        return Response({
            'success': True,
            'mongodb_connected': True,
            'total_schemes': total_schemes,
            'sample_schemes': len(sample_schemes),
            'database_name': 'Govt_schemes',
            'collection_name': 'government_schemes'
        })
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return Response({
            'success': False,
            'mongodb_connected': False,
            'error': str(e),
            'total_schemes': 0
        })


@api_view(['POST'])
def advanced_search_api(request):
    """
    Advanced search API with filters and sorting
    """
    try:
        # Get search parameters
        data = json.loads(request.body)
        sector = data.get('sector', '')
        ministry = data.get('ministry', '')
        eligibility = data.get('eligibility', '')
        sort_by = data.get('sortBy', 'relevance')
        language = data.get('language', 'en')
        
        # Generate session ID
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        # Set chatbot language and session
        chatbot.set_language(language)
        chatbot.set_session(session_id)
        
        # Build advanced search query
        search_query = "Show me government schemes"
        keywords = []
        entities = {}
        
        if sector:
            search_query += f" in {sector} sector"
            keywords.append(sector)
            entities['sectors'] = [sector]
        
        if ministry:
            search_query += f" from {ministry} ministry"
            keywords.append(ministry)
            entities['ministry'] = ministry
        
        if eligibility:
            search_query += f" for {eligibility}"
            keywords.extend(eligibility.split())
            entities['eligibility'] = eligibility
        
        # Perform advanced search using MongoDB adapter
        from mongodb_adapter import MongoDBAdapter
        mongodb_adapter = MongoDBAdapter()
        
        # Enhanced search with additional filters
        schemes = mongodb_adapter.advanced_search(
            query=search_query,
            keywords=keywords,
            entities=entities,
            sector=sector,
            ministry=ministry,
            eligibility=eligibility,
            sort_by=sort_by
        )
        
        # Generate response message
        if schemes:
            response_msg = f"Found {len(schemes)} government schemes"
            if sector:
                response_msg += f" in {sector} sector"
            if ministry:
                response_msg += f" from {ministry} ministry"
            if eligibility:
                response_msg += f" for {eligibility}"
            response_msg += f", sorted by {sort_by}."
        else:
            response_msg = "No schemes found matching your search criteria. Try adjusting your filters or using different keywords."
        
        # Save search to chat history
        try:
            ChatMessage.objects.create(
                session=chatbot.session,
                message_type='user',
                text_content=search_query,
                language=language,
                related_schemes=[str(scheme.get('_id', '')) for scheme in schemes[:5]]  # Store up to 5 scheme IDs
            )
            
            ChatMessage.objects.create(
                session=chatbot.session,
                message_type='bot',
                text_content=response_msg,
                language=language,
                related_schemes=[str(scheme.get('_id', '')) for scheme in schemes[:5]]
            )
        except Exception as e:
            logger.warning(f"Failed to save advanced search to chat history: {e}")
        
        return Response({
            'success': True,
            'response': response_msg,
            'schemes': schemes,
            'search_params': {
                'sector': sector,
                'ministry': ministry,
                'eligibility': eligibility,
                'sort_by': sort_by,
                'language': language
            },
            'total_results': len(schemes)
        })
    
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data',
            'schemes': []
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Advanced search API error: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'schemes': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def multilingual_voice_api(request):
    """Convert text to speech in multiple languages"""
    try:
        import json
        import base64
        from .voice_processing import VoiceProcessor
        
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'en')
        voice_speed = data.get('speed', 'normal')  # slow, normal, fast
        
        if not text:
            return JsonResponse({
                'success': False, 
                'error': 'Text is required'
            })
        
        # Initialize voice processor
        voice_processor = VoiceProcessor()
        
        # Language mapping for gTTS
        language_mapping = {
            'en': 'en',      # English
            'hi': 'hi',      # Hindi
            'kn': 'kn',      # Kannada
            'ta': 'ta',      # Tamil
            'te': 'te',      # Telugu
            'mr': 'mr',      # Marathi
            'bn': 'bn',      # Bengali
            'gu': 'gu',      # Gujarati
            'ml': 'ml',      # Malayalam
            'pa': 'pa',      # Punjabi
            'ur': 'ur',      # Urdu
        }
        
        # Get correct language code
        gtts_language = language_mapping.get(language, 'en')
        
        # Generate voice with speed control
        slow = (voice_speed == 'slow')
        audio_data = voice_processor.text_to_speech_gtts(
            text, 
            language=gtts_language, 
            slow=slow
        )
        
        if audio_data:
            # Convert to base64 for frontend
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Get display name for language
            names = {
                'en': 'English',
                'hi': 'हिन्दी (Hindi)',
                'kn': 'ಕನ್ನಡ (Kannada)',
                'ta': 'தமிழ் (Tamil)',
                'te': 'తెలుగు (Telugu)',
                'mr': 'मराठी (Marathi)',
                'bn': 'বাংলা (Bengali)',
                'gu': 'ગુજરાતી (Gujarati)',
                'ml': 'മലയാളം (Malayalam)',
                'pa': 'ਪੰਜਾਬੀ (Punjabi)',
                'ur': 'اردو (Urdu)'
            }
            
            return JsonResponse({
                'success': True,
                'audio_data': audio_base64,
                'language': language,
                'language_display': names.get(language, 'English'),
                'speed': voice_speed,
                'text_length': len(text),
                'audio_size': len(audio_data)
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Voice generation failed'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })


# Translation cache to avoid repeated API calls
_translation_cache = {}

@csrf_exempt
@require_http_methods(["POST"])
def translate_content_api(request):
    """Translate page content and database records dynamically using Gemini"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        target_language = data.get('language', 'en')
        content_type = data.get('type', 'text')  # text, scheme, list
        
        if not content or target_language == 'en':
            return JsonResponse({
                'success': True,
                'translated': content,
                'cached': False
            })
        
        # Create cache key
        cache_key = f"{target_language}:{content_type}:{str(content)[:100]}"
        
        # Check cache first
        if cache_key in _translation_cache:
            return JsonResponse({
                'success': True,
                'translated': _translation_cache[cache_key],
                'cached': True
            })
        
        # Translate using Gemini
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
        
        if content_type == 'scheme':
            # Translate scheme data (JSON format)
            prompt = f"""Translate this government scheme information from English to {target_lang_name}.
Maintain the JSON structure exactly. Only translate the values, not the keys.
Preserve all URLs, numbers, and special formatting.

English JSON:
{content}

{target_lang_name} JSON:"""
        elif content_type == 'list':
            # Translate list of items
            prompt = f"""Translate these items from English to {target_lang_name}.
Keep each item on a separate line.
Maintain any special characters, emojis, or formatting.

English:
{content}

{target_lang_name}:"""
        else:
            # Simple text translation
            prompt = f"""Translate this text from English to {target_lang_name}.
Maintain all formatting, emojis, and special characters.

English: {content}

{target_lang_name}:"""
        
        try:
            translated = generate_text_with_gemini(prompt)
            if translated and len(translated.strip()) > 0:
                # Cache the translation
                _translation_cache[cache_key] = translated.strip()
                
                return JsonResponse({
                    'success': True,
                    'translated': translated.strip(),
                    'cached': False
                })
            else:
                # Fallback to original
                return JsonResponse({
                    'success': True,
                    'translated': content,
                    'cached': False,
                    'note': 'Translation failed, using original'
                })
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return JsonResponse({
                'success': True,
                'translated': content,
                'cached': False,
                'error': str(e)
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@api_view(['POST'])
def vector_search_api(request):
    """
    Semantic search API using pgvector + Gemini embeddings + LLM reranking.
    
    POST /api/search/
    Body:
    {
        "query": "schemes for farmers",
        "top_k": 5,  // optional, default 5
        "sector": "agriculture",  // optional filter
        "government_level": "central",  // optional filter
        "use_llm": true,  // optional, default true
        "llm_model": "gemini-1.5-flash"  // optional, flash or pro
    }
    
    Response:
    {
        "success": true,
        "answer": "LLM-generated answer...",
        "schemes": [...],
        "ssml": "<speak>...</speak>",
        "query": "schemes for farmers",
        "top_k": 5
    }
    """
    def generate_ssml(text):
        """Convert text to SSML for voice output"""
        # Clean text for SSML
        clean_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<speak>{clean_text}</speak>'
    
    try:
        from chatbot.vector_search import get_vector_search_service
        
        # Parse request
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        query = data.get('query', '').strip()
        if not query:
            return Response(
                {'success': False, 'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        top_k = data.get('top_k', 5)
        sector_filter = data.get('sector')
        government_level_filter = data.get('government_level')
        use_llm = data.get('use_llm', True)
        llm_model = data.get('llm_model', 'gemini-1.5-flash')
        
        # Validate parameters
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            return Response(
                {'success': False, 'error': 'top_k must be between 1 and 20'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if llm_model not in ['gemini-1.5-flash', 'gemini-1.5-pro']:
            llm_model = 'gemini-1.5-flash'
        
        # Perform search
        service = get_vector_search_service()
        result = service.search(
            query=query,
            top_k=top_k,
            sector_filter=sector_filter,
            government_level_filter=government_level_filter,
            use_llm_reranking=use_llm,
            llm_model=llm_model,
        )
        
        # Log search for analytics (optional)
        try:
            if request.user.is_authenticated:
                profile = UserProfile.objects.get(user=request.user)
                UserSearchHistory.objects.create(
                    user_profile=profile,
                    query=query,
                    results_count=len(result['schemes']),
                )
        except Exception as e:
            logger.warning(f'Failed to log search history: {e}')
        
        return Response({
            'success': True,
            'answer': result['answer'],
            'schemes': result['schemes'],
            'ssml': generate_ssml(result['answer']) if result['answer'] else '',
            'query': result['query'],
            'top_k': result['top_k'],
        })
        
    except ValueError as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f'Vector search API error: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'success': False, 'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(["POST"])
def translate_schemes_batch(request):
    """Translate multiple schemes at once for schemes list page"""
    try:
        data = json.loads(request.body)
        scheme_ids = data.get('scheme_ids', [])
        target_language = data.get('target_language', 'en')
        
        if target_language == 'en' or not scheme_ids:
            return JsonResponse({
                'status': 'success',
                'translated_schemes': []
            })
        
        # Limit to 20 schemes at a time to avoid timeout
        scheme_ids = scheme_ids[:20]
        translated_schemes = []
        
        # Get schemes from database
        schemes = GovernmentScheme.objects.filter(id__in=scheme_ids, is_active=True)
        
        # Language mapping
        language_names = {
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'bn': 'Bengali'
        }
        target_lang_name = language_names.get(target_language, target_language)
        
        # Build a batch translation prompt for ALL schemes at once
        schemes_list = []
        for scheme in schemes:
            cache_key = f"{target_language}:scheme:{scheme.id}"
            
            # Check cache
            if cache_key in _translation_cache:
                translated_schemes.append(_translation_cache[cache_key])
                continue
            
            # Prepare scheme data
            description = scheme.short_description or scheme.description
            if description and len(description) > 180:
                description = description[:177] + '...'
            elif not description:
                description = 'No description available'
            
            # Translate fallback descriptions locally
            if 'is a government scheme designed to support' in description or description == 'No description available':
                # Use pre-translated fallback
                fallback_desc = FALLBACK_TRANSLATIONS.get(target_language, {}).get('generic', description)
                if description == 'No description available':
                    fallback_desc = FALLBACK_TRANSLATIONS.get(target_language, {}).get('no_description', description)
                    
                schemes_list.append({
                    'id': scheme.id,
                    'title': scheme.title,  # Will be translated by Gemini
                    'description': fallback_desc,  # Use pre-translated fallback
                    'government_level': scheme.government_level or '',
                    'state': scheme.state or ''
                })
            else:
                schemes_list.append({
                    'id': scheme.id,
                    'title': scheme.title,
                    'description': description,
                    'government_level': scheme.government_level or '',
                    'state': scheme.state or ''
                })
        
        # Single batch translation for all schemes using FastTranslator (instant, no rate limits!)
        if schemes_list:
            try:
                # Use googletrans for instant translation
                translator = get_fast_translator()
                logger.info(f"Translating {len(schemes_list)} schemes to {target_lang_name} using FastTranslator")
                
                for scheme_data in schemes_list:
                    try:
                        # Translate each scheme
                        translated_scheme = translator.translate_scheme(scheme_data, target_language)
                        translated_schemes.append(translated_scheme)
                        
                        # Cache the result
                        cache_key = f"{target_language}:scheme:{scheme_data['id']}"
                        _translation_cache[cache_key] = translated_scheme
                        
                    except Exception as e:
                        logger.error(f"Error translating scheme {scheme_data.get('id')}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Use original on error
                        translated_schemes.append(scheme_data)
                
                logger.info(f"Successfully translated {len(translated_schemes)} schemes using FastTranslator")
                
            except Exception as e:
                logger.error(f"Error in batch translation: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Use original on error
                translated_schemes = schemes_list
        
        return JsonResponse({
            'status': 'success',
            'translated_schemes': translated_schemes
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def translate_scheme_detail(request):
    """Translate detailed scheme information for scheme detail page"""
    try:
        data = json.loads(request.body)
        scheme_id = data.get('scheme_id')
        target_language = data.get('target_language', 'en')
        
        if not scheme_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Scheme ID is required'
            }, status=400)
        
        if target_language == 'en':
            return JsonResponse({
                'status': 'success',
                'translation': {}
            })
        
        # Get scheme from database
        try:
            scheme = GovernmentScheme.objects.select_related('sector').get(id=scheme_id, is_active=True)
        except GovernmentScheme.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Scheme not found'
            }, status=404)
        
        # Language mapping
        language_names = {
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'bn': 'Bengali'
        }
        target_lang_name = language_names.get(target_language, target_language)
        
        # Check cache first
        cache_key = f"{target_language}:detail:{scheme.id}"
        if cache_key in _translation_cache:
            logger.info(f"Using cached translation for scheme {scheme.id} in {target_lang_name}")
            return JsonResponse({
                'status': 'success',
                'translation': _translation_cache[cache_key]
            })
        
        # Prepare content for translation - ALL fields
        content_to_translate = {
            'title': scheme.title,
            'description': scheme.description or '',
            'short_description': scheme.short_description or '',
            'eligibility_criteria': scheme.eligibility_criteria or '',
            'benefits': scheme.benefits or '',
            'financial_assistance': scheme.financial_assistance or '',
            'application_process': scheme.application_process or '',
            'government_level': scheme.government_level or '',
            'state': scheme.state or '',
            'sector_name': scheme.sector.name if scheme.sector else '',
            'ministry': scheme.ministry or '',
            'department': scheme.department or '',
            'validity_period': scheme.validity_period or '',
        }
        
        logger.info(f"Translating scheme detail {scheme.id} to {target_lang_name}")
        
        try:
            # Use FastTranslator for instant translation
            translator = get_fast_translator()
            translated_content = {}
            
            # Translate each field
            for field, text in content_to_translate.items():
                if text:
                    try:
                        translated_text = translator.translate(text, target_language)
                        translated_content[field] = translated_text
                    except Exception as e:
                        logger.error(f"Error translating {field}: {e}")
                        translated_content[field] = text  # Fallback to original
                else:
                    translated_content[field] = text
            
            # Cache the result
            _translation_cache[cache_key] = translated_content
            
            logger.info(f"Successfully translated scheme detail {scheme.id} using FastTranslator")
            
            return JsonResponse({
                'status': 'success',
                'translation': translated_content
            })
            
        except Exception as e:
            logger.error(f"Error in scheme detail translation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return JsonResponse({
                'status': 'error',
                'message': 'Translation failed',
                'details': str(e)
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in translate_scheme_detail: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# =============================================================================
# SEMANTIC SEARCH & SMART ANSWER APIs (Gemini + pgvector)
# =============================================================================

@api_view(['POST'])
def semantic_search_api(request):
    """
    Semantic Search API - Find schemes using vector similarity search.
    
    Uses Gemini embeddings + pgvector for intelligent scheme matching.
    
    Request Body:
        {
            "query": "farming subsidy for women",
            "top_k": 5,  // optional, default 5
            "is_active": true  // optional, default true
        }
    
    Response:
        {
            "query": "farming subsidy for women",
            "results_count": 3,
            "results": [
                {
                    "id": 5,
                    "title": "Mahila Kisan Sashaktikaran Pariyojana",
                    "short_description": "...",
                    "government_level": "central",
                    "state": "",
                    "application_link": "https://...",
                    "website": "https://...",
                    "distance": 0.234,
                    "similarity_score": 0.883
                },
                ...
            ],
            "cached": false
        }
    """
    from chatbot.serializers import (
        SemanticSearchRequestSerializer,
        SemanticSearchResponseSerializer,
        ErrorResponseSerializer
    )
    from chatbot.embedding_utils import create_query_embedding
    from chatbot.vector_search import (
        semantic_search,
        get_cached_search_results,
        cache_search_results,
        get_cached_embedding,
        cache_embedding
    )
    
    try:
        # Validate request data
        request_serializer = SemanticSearchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            error_serializer = ErrorResponseSerializer(data={
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': request_serializer.errors
            })
            error_serializer.is_valid()
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data
        query = validated_data['query']
        top_k = validated_data.get('top_k', 5)
        is_active_filter = validated_data.get('is_active', True)
        
        # Check cache for search results
        cached_results = get_cached_search_results(query)
        if cached_results:
            logger.info(f"Cache hit for semantic search: {query[:50]}...")
            response_data = {
                'query': query,
                'results_count': len(cached_results),
                'results': cached_results[:top_k],  # Apply top_k limit
                'cached': True
            }
            response_serializer = SemanticSearchResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        # Check cache for query embedding
        query_embedding = get_cached_embedding(query)
        
        if not query_embedding:
            # Generate new embedding
            logger.info(f"Generating embedding for query: {query[:50]}...")
            query_embedding = create_query_embedding(query)
            
            if not query_embedding:
                error_serializer = ErrorResponseSerializer(data={
                    'error': 'Failed to generate query embedding',
                    'error_code': 'EMBEDDING_ERROR'
                })
                error_serializer.is_valid()
                return Response(
                    error_serializer.data,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Cache the embedding
            cache_embedding(query, query_embedding)
        
        # Prepare filters
        filters = {}
        if is_active_filter:
            filters['is_active'] = True
        
        # Perform semantic search
        logger.info(f"Performing vector search with top_k={top_k}")
        search_results = semantic_search(
            query_embedding=query_embedding,
            top_k=top_k,
            use_cache=True,
            filters=filters
        )
        
        # Cache the results
        cache_search_results(query, search_results)
        
        # Prepare response
        response_data = {
            'query': query,
            'results_count': len(search_results),
            'results': search_results,
            'cached': False
        }
        
        response_serializer = SemanticSearchResponseSerializer(data=response_data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Semantic search API error: {e}", exc_info=True)
        error_serializer = ErrorResponseSerializer(data={
            'error': str(e),
            'error_code': 'INTERNAL_ERROR'
        })
        error_serializer.is_valid()
        return Response(
            error_serializer.data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def smart_answer_api(request):
    """
    Smart Answer API - RAG-based intelligent responses using Gemini LLM.
    
    This endpoint:
    1. Generates embedding for user query
    2. Retrieves top-k relevant schemes via vector search
    3. Uses Gemini LLM to generate natural language answer
    4. Returns answer + supporting schemes
    
    Request Body:
        {
            "query": "What schemes are available for women farmers in Karnataka?",
            "top_k": 5,  // optional, default 5
            "model": "gemini-1.5-flash",  // optional, flash or pro
            "include_ssml": false  // optional, for voice output
        }
    
    Response:
        {
            "query": "What schemes are available...",
            "answer": "Based on government schemes, here are options for women farmers in Karnataka...",
            "answer_ssml": "<speak>Based on government schemes...</speak>",  // if include_ssml=true
            "schemes_used": [
                {
                    "id": 5,
                    "title": "Mahila Kisan Sashaktikaran Pariyojana",
                    "description": "...",
                    "eligibility_criteria": "...",
                    "benefits": "...",
                    "application_link": "...",
                    ...
                },
                ...
            ],
            "schemes_count": 3,
            "model_used": "gemini-1.5-flash",
            "cached": false
        }
    """
    import os
    import google.generativeai as genai
    from chatbot.serializers import (
        SmartAnswerRequestSerializer,
        SmartAnswerResponseSerializer,
        ErrorResponseSerializer
    )
    from chatbot.embedding_utils import create_query_embedding
    from chatbot.vector_search import (
        semantic_search,
        get_cached_embedding,
        cache_embedding
    )
    from chatbot.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, SSML_WRAPPER_TEMPLATE
    
    try:
        # Validate request data
        request_serializer = SmartAnswerRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            error_serializer = ErrorResponseSerializer(data={
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': request_serializer.errors
            })
            error_serializer.is_valid()
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data
        query = validated_data['query']
        top_k = validated_data.get('top_k', 5)
        model_name = validated_data.get('model', 'gemini-1.5-flash')
        include_ssml = validated_data.get('include_ssml', False)
        
        # Use environment variable for model selection if available
        model_name = os.getenv('GCP_MODEL', model_name)
        if 'gemini' not in model_name:
            # Ensure valid Gemini model
            model_name = 'gemini-1.5-flash'
        
        logger.info(f"Smart answer request: {query[:100]}... | model={model_name}")
        
        # Step 1: Generate query embedding (with caching)
        query_embedding = get_cached_embedding(query)
        
        if not query_embedding:
            logger.info("Generating new embedding for query")
            query_embedding = create_query_embedding(query)
            
            if not query_embedding:
                error_serializer = ErrorResponseSerializer(data={
                    'error': 'Failed to generate query embedding',
                    'error_code': 'EMBEDDING_ERROR'
                })
                error_serializer.is_valid()
                return Response(
                    error_serializer.data,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            cache_embedding(query, query_embedding)
        
        # Step 2: Retrieve relevant schemes via semantic search
        logger.info(f"Retrieving top {top_k} schemes for context")
        retrieved_schemes = semantic_search(
            query_embedding=query_embedding,
            top_k=top_k,
            use_cache=True,
            filters={'is_active': True}
        )
        
        if not retrieved_schemes:
            # No schemes found
            logger.warning("No relevant schemes found for query")
            response_data = {
                'query': query,
                'answer': 'No official scheme found for your request. Please contact your local government office or visit official government portals for assistance.',
                'answer_ssml': SSML_WRAPPER_TEMPLATE.format(
                    text='No official scheme found for your request.'
                ) if include_ssml else '',
                'schemes_used': [],
                'schemes_count': 0,
                'model_used': model_name,
                'cached': False
            }
            response_serializer = SmartAnswerResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        # Step 3: Build context from retrieved schemes
        context_parts = []
        for i, scheme in enumerate(retrieved_schemes, 1):
            context_part = f"""
Scheme {i}: {scheme['title']}
- Sector/Category: {scheme.get('ministry', 'Not specified')}
- Government Level: {scheme.get('government_level', 'Not specified')}
- State: {scheme.get('state', 'Pan-India') or 'Pan-India'}
- Eligibility: {scheme.get('eligibility_criteria', 'Check official website')[:300]}
- Benefits: {scheme.get('benefits', 'Check official website')[:300]}
- Application Link: {scheme.get('application_link', 'Visit official website')}
- Website: {scheme.get('website', 'Contact local office')}
- Similarity Score: {scheme.get('similarity_score', 0):.2f}
"""
            context_parts.append(context_part.strip())
        
        context = "\n\n".join(context_parts)
        
        # Step 4: Generate LLM response using Gemini
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            user_query=query
        )
        
        logger.info(f"Generating LLM response with model: {model_name}")
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY environment variable not set')
        genai.configure(api_key=api_key)
        
        # Create model with system instruction
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT
        )
        
        # Generate response with strict parameters to prevent hallucination
        generation_config = {
            'temperature': 0,  # Deterministic, factual responses
            'max_output_tokens': 300,  # Keep responses concise
            'top_p': 0.1,  # Low diversity, stick to facts
            'top_k': 1,  # Most likely tokens only
        }
        
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        answer = response.text.strip()
        
        # CRITICAL: Remove any markdown formatting from Gemini response
        from chatbot.utils.formatting import sanitize_markdown
        answer = sanitize_markdown(answer)
        
        # Generate SSML if requested
        answer_ssml = ''
        if include_ssml:
            answer_ssml = SSML_WRAPPER_TEMPLATE.format(text=answer)
        
        # Step 5: Prepare response
        response_data = {
            'query': query,
            'answer': answer,
            'answer_ssml': answer_ssml,
            'schemes_used': retrieved_schemes,
            'schemes_count': len(retrieved_schemes),
            'model_used': model_name,
            'cached': False
        }
        
        response_serializer = SmartAnswerResponseSerializer(data=response_data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Smart answer API error: {e}", exc_info=True)
        error_serializer = ErrorResponseSerializer(data={
            'error': str(e),
            'error_code': 'INTERNAL_ERROR'
        })
        error_serializer.is_valid()
        return Response(
            error_serializer.data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# NEW HUGGINGFACE-BASED SEMANTIC SEARCH + RAG ENDPOINTS
# ============================================================================

@csrf_exempt
@api_view(['POST'])
def semantic_search_view(request):
    """
    ============================================================
    UPGRADED Semantic Search API with Smart Matching
    ============================================================
    
    NEW FEATURES:
    1. Exact title match (highest priority)
    2. Sector-based matching (return all schemes in sector)
    3. Title boost in vector search results
    4. Lower similarity threshold (0.40 instead of 0.55)
    
    POST /api/semantic-search-v2/
    Request: { "query": "PM Kisan" } or { "query": "agriculture schemes" }
    Response: { "query": "...", "results": [...], "match_type": "exact"/"sector"/"semantic" }
    """
    from django.core.cache import cache
    from chatbot.embedding_utils import create_embedding, exact_title_match
    from chatbot.vector_search import search_similar_schemes, boost_title_match
    from chatbot.models import GovernmentScheme, Sector
    import hashlib
    import json
    
    try:
        # Get query from request
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response({
                'error': 'Query parameter is required',
                'error_code': 'MISSING_QUERY'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Semantic search request: {query[:100]}")
        
        # Check Redis cache first (12 hours TTL)
        cache_key = f"semantic_search_v2:{hashlib.md5(query.encode()).hexdigest()}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Cache hit for query: {query[:50]}...")
            return Response(json.loads(cached_results))
        
        # ============================================================
        # IMPROVEMENT #1: Exact Title Match (HIGHEST PRIORITY)
        # ============================================================
        # Check if query matches any scheme title exactly or partially
        # This prevents fallback for direct scheme name queries
        
        active_schemes = GovernmentScheme.objects.filter(is_active=True)
        
        for scheme in active_schemes:
            if exact_title_match(query, scheme.title):
                # Found exact/partial title match - return ONLY this scheme
                logger.info(f"Exact title match found: {scheme.title}")
                
                formatted_results = [{
                    'id': scheme.id,
                    'title': scheme.title,
                    'short_description': scheme.short_description or '',
                    'distance': 0.0,  # Perfect match
                    'similarity_score': 100.0
                }]
                
                response_data = {
                    'query': query,
                    'results': formatted_results,
                    'count': 1,
                    'match_type': 'exact_title'
                }
                
                # Cache and return
                cache.set(cache_key, json.dumps(response_data), 43200)
                return Response(response_data)
        
        # ============================================================
        # IMPROVEMENT #5: Sector/Category Matching
        # ============================================================
        # If query contains sector keywords, return all schemes in that sector
        
        SECTOR_KEYWORDS = {
            'agriculture': ['agriculture', 'farming', 'farmer', 'crop', 'krishi'],
            'education': ['education', 'school', 'college', 'student', 'scholarship', 'study'],
            'health': ['health', 'medical', 'hospital', 'treatment', 'insurance', 'ayushman'],
            'women': ['women', 'woman', 'mahila', 'girl', 'female'],
            'skill': ['skill', 'training', 'employment', 'job', 'placement'],
            'youth': ['youth', 'young', 'startup', 'entrepreneur'],
            'senior': ['senior', 'elderly', 'old age', 'pension'],
        }
        
        query_lower = query.lower()
        matched_sector = None
        
        for sector_name, keywords in SECTOR_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                matched_sector = sector_name
                break
        
        if matched_sector:
            # Check if this is a general sector query (e.g., "agriculture schemes")
            # Generic indicators: "schemes", "programs", "all", "list"
            is_general_sector_query = any(word in query_lower for word in [
                'schemes', 'scheme', 'programs', 'program', 'all', 'list', 'available'
            ])
            
            if is_general_sector_query:
                # Return ALL schemes in this sector
                logger.info(f"Sector match found: {matched_sector}")
                
                # Query by sector name
                sector_schemes = GovernmentScheme.objects.filter(
                    is_active=True
                ).filter(
                    sector__name__icontains=matched_sector
                )[:10]  # Top 10 schemes
                
                if sector_schemes.count() > 0:
                    formatted_results = []
                    for scheme in sector_schemes:
                        formatted_results.append({
                            'id': scheme.id,
                            'title': scheme.title,
                            'short_description': scheme.short_description or '',
                            'distance': 0.1,  # Very high relevance
                            'similarity_score': 95.0
                        })
                    
                    response_data = {
                        'query': query,
                        'results': formatted_results,
                        'count': len(formatted_results),
                        'match_type': 'sector',
                        'sector': matched_sector
                    }
                    
                    # Cache and return
                    cache.set(cache_key, json.dumps(response_data), 43200)
                    return Response(response_data)
        
        # ============================================================
        # Standard Embedding-Based Search
        # ============================================================
        
        # Generate embedding for the query
        query_embedding = create_embedding(query)
        
        if query_embedding is None:
            return Response({
                'error': 'Failed to generate embedding',
                'error_code': 'EMBEDDING_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Search for similar schemes (top 10 for better coverage)
        results = search_similar_schemes(
            query_embedding=query_embedding,
            top_k=10,
            filters={'is_active': True}
        )
        
        # ============================================================
        # IMPROVEMENT #3: Apply Title Boost
        # ============================================================
        # Override distance for schemes with matching titles
        
        for result in results:
            manual_distance = boost_title_match(query, result['title'])
            if manual_distance is not None:
                result['distance'] = manual_distance
                result['similarity_score'] = max(0, (1 - manual_distance / 2) * 100)
                logger.info(f"Title boost applied to: {result['title']} (distance: {manual_distance})")
        
        # Re-sort by distance after boosting
        results.sort(key=lambda x: x['distance'])
        
        # Take top 5 after boosting
        results = results[:5]
        
        # Format response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['id'],
                'title': result['title'],
                'short_description': result['short_description'],
                'distance': result['distance'],
                'similarity_score': result['similarity_score']
            })
        
        response_data = {
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'match_type': 'semantic'
        }
        
        # Cache the results for 12 hours (43200 seconds)
        cache.set(cache_key, json.dumps(response_data), 43200)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'error_code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def smart_answer_view(request):
    """
    Smart Answer API with RAG using HuggingFace + Gemini.
    
    Features:
    - Greeting detection (returns friendly greeting instead of scheme search)
    - Similarity threshold (0.55) - returns fallback if no good matches
    - RAG with Gemini LLM for high-quality matches
    - SSML support for voice output
    
    POST /api/smart-answer/
    Request: { "query": "hello" } or { "query": "farming schemes" }
    Response: { "answer": "...", "ssml": "...", "schemes_used": [...] }
    """
    from django.core.cache import cache
    from chatbot.embedding_utils import create_embedding
    from chatbot.vector_search import search_similar_schemes
    from chatbot.prompts import (
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE,
        GREETINGS,
        GREETING_RESPONSE,
        GREETING_SSML,
        NO_RESULTS_MESSAGE,
        NO_RESULTS_SSML
    )
    import google.generativeai as genai
    import os
    import hashlib
    import json
    
    try:
        # Get query from request
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response({
                'error': 'Query parameter is required',
                'error_code': 'MISSING_QUERY'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Smart answer request: {query[:100]}")
        
        # FEATURE 1: Greeting Detection
        # Check if query is a casual greeting - return greeting response without scheme search
        query_lower = query.lower()
        is_greeting = any(greeting in query_lower for greeting in GREETINGS)
        
        if is_greeting:
            logger.info(f"Greeting detected: {query}")
            return Response({
                'answer': GREETING_RESPONSE,
                'ssml': GREETING_SSML,
                'schemes_used': []
            })
        
        # Check Redis cache for non-greeting queries (12 hours TTL)
        cache_key = f"smart_answer:{hashlib.md5(query.encode()).hexdigest()}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.info(f"Cache hit for smart answer: {query[:50]}...")
            return Response(json.loads(cached_response))
        
        # Import required modules
        from chatbot.models import GovernmentScheme
        from chatbot.utils.normalization import (
            universal_fuzzy_match,
            normalize_query,
            normalize_text, 
            expand_abbreviations
        )
        from chatbot.utils.formatting import format_scheme_answer, format_for_llm, format_fallback_message
        
        # ============================================================
        # STEP 1: UNIVERSAL QUERY NORMALIZATION
        # ============================================================
        # Remove noise, preserve meaningful scheme keywords
        # Works for ALL schemes automatically (PM-KISAN, Ayushman Bharat, Mudra, etc.)
        
        normalized_query = normalize_query(query)
        
        logger.info(f"🔍 UNIVERSAL SCHEME DETECTION STARTED")
        logger.info(f"📝 RAW_QUERY: {query}")
        logger.info(f"🎯 NORMALIZED_QUERY: {normalized_query}")
        
        # Use normalized query for matching if it has meaningful content
        # Otherwise fall back to original query
        search_query = normalized_query if normalized_query.strip() else query
        
        if search_query != query:
            logger.info(f"📊 QUERY_TRANSFORMATION: Original='{query}' → Normalized='{search_query}'")
        
        # ============================================================
        # STEP 2: UNIVERSAL FUZZY MATCHING (ALL SCHEMES)
        # ============================================================
        # Fuzzy match against ALL schemes in database automatically
        # Works for: PM-KISAN, Ayushman Bharat, Mudra, Beti Bachao, NMSA, etc.
        # Handles typos, variations, partial names
        # ============================================================
        
        # Try UNIVERSAL fuzzy matching (75% threshold)
        # Compares against ALL active schemes in database
        fuzzy_matches = universal_fuzzy_match(
            query=search_query,
            schemes_queryset=GovernmentScheme.objects,
            confidence_threshold=75.0,  # Balanced: catches variations without false positives
            limit=1
        )
        
        if fuzzy_matches and len(fuzzy_matches) > 0:
            matched_scheme = fuzzy_matches[0]['scheme']
            fuzzy_score = fuzzy_matches[0]['score']
            
            logger.info(f"✅ FUZZY_MATCH_SUCCESS")
            logger.info(f"📊 FUZZY_SCORE: {fuzzy_score:.1f}%")
            logger.info(f"🎯 MATCHED_SCHEME: {matched_scheme.title}")
            logger.info(f"🆔 SCHEME_ID: {matched_scheme.id}")
            logger.info(f"🚀 RETURN_REASON: Fuzzy match above 75% threshold - returning immediately (NO LLM, NO embedding)")
            
            # Format scheme answer immediately - NO LLM needed
            formatted_answer = format_scheme_answer(matched_scheme)
            
            # Build response and return IMMEDIATELY
            response_data = {
                'answer': formatted_answer,
                'ssml': f"<speak>{formatted_answer}</speak>",
                'schemes_used': [matched_scheme.title],
                'match_type': 'universal_fuzzy_match',
                'fuzzy_score': fuzzy_score,
                'scheme_id': matched_scheme.id
            }
            
            # Cache the response
            cache.set(cache_key, json.dumps(response_data), 43200)
            
            logger.info(f"✅ SUCCESS: Returning fuzzy match for '{matched_scheme.title}'")
            return Response(response_data)
        
        logger.info(f"⏭️  FUZZY_MATCH_FAILED: No match with score >= 75%, proceeding to exact match...")
        
        # ============================================================
        # STEP 3: EXACT TITLE MATCH (FALLBACK)
        # ============================================================
        # Try exact substring match using normalized query
        
        # Try exact icontains match on NORMALIZED query (not raw query)
        exact_match = GovernmentScheme.objects.filter(
            is_active=True,
            title__icontains=search_query
        ).first()
        
        if exact_match:
            logger.info(f"✅ EXACT MATCH FOUND!")
            logger.info(f"🎯 MATCHED TITLE: {exact_match.title}")
            logger.info(f"🚀 DECISION: Return scheme details immediately (NO LLM, NO embedding search)")
            
            # Format scheme answer immediately - NO LLM needed
            formatted_answer = format_scheme_answer(exact_match)
            
            # Build response and return IMMEDIATELY
            response_data = {
                'answer': formatted_answer,
                'ssml': f"<speak>{formatted_answer}</speak>",
                'schemes_used': [exact_match.title],
                'match_type': 'exact_title',
                'scheme_id': exact_match.id
            }
            
            # Cache the response
            cache.set(cache_key, json.dumps(response_data), 43200)
            
            logger.info(f"✓ Returning exact match result for: {exact_match.title}")
            return Response(response_data)
        
        logger.info(f"⏭️  No exact match found, trying keyword match...")
        
        # ============================================================
        # STEP 3: PARTIAL KEYWORD MATCH
        # ============================================================
        # If no exact match, try significant keyword matching using NORMALIZED query
        
        from chatbot.utils.normalization import extract_keywords
        
        # Extract significant keywords from the NORMALIZED query
        query_keywords = extract_keywords(search_query, min_length=3)
        
        logger.info(f"🔑 EXTRACTED KEYWORDS: {query_keywords}")
        
        if query_keywords:
            # Try to find schemes matching significant keywords
            keyword_matches = []
            
            for keyword in query_keywords:
                matches = GovernmentScheme.objects.filter(
                    is_active=True,
                    title__icontains=keyword
                )
                for match in matches:
                    if match not in keyword_matches:
                        keyword_matches.append(match)
            
            logger.info(f"📋 KEYWORD MATCHES FOUND: {len(keyword_matches)}")
            
            # If exactly 1 significant match found, return it
            if len(keyword_matches) == 1:
                single_match = keyword_matches[0]
                logger.info(f"✅ SINGLE KEYWORD MATCH FOUND!")
                logger.info(f"🎯 MATCHED TITLE: {single_match.title}")
                logger.info(f"🚀 DECISION: Return scheme details immediately (NO LLM, NO embedding search)")
                
                # Format scheme answer immediately - NO LLM needed
                formatted_answer = format_scheme_answer(single_match)
                
                # Build response and return IMMEDIATELY
                response_data = {
                    'answer': formatted_answer,
                    'ssml': f"<speak>{formatted_answer}</speak>",
                    'schemes_used': [single_match.title],
                    'match_type': 'partial_keyword',
                    'scheme_id': single_match.id
                }
                
                # Cache the response
                cache.set(cache_key, json.dumps(response_data), 43200)
                
                logger.info(f"✓ Returning keyword match result for: {single_match.title}")
                return Response(response_data)
        
        logger.info(f"⏭️  No keyword match found, falling back to vector embedding search...")
        
        # ============================================================
        # STEP 5: VECTOR SEARCH (if no exact/fuzzy/keyword match)
        # ============================================================
        # Pipeline: DB search → Filter by threshold → THEN call Gemini
        
        from chatbot.embedding_utils import create_embedding
        from chatbot.vector_search import search_similar_schemes
        
        logger.info(f"🔍 STEP 5: VECTOR SEARCH STARTED")
        logger.info(f"📝 SEARCH_QUERY: {search_query}")
        logger.info(f"🧮 Generating embedding for query...")
        
        # Generate embedding for the query
        query_embedding = create_embedding(query)
        
        if query_embedding is None:
            logger.error(f"❌ EMBEDDING_GENERATION_FAILED")
            return Response({
                'error': 'Failed to generate embedding',
                'error_code': 'EMBEDDING_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"✅ Embedding generated successfully")
        logger.info(f"🔍 Searching similar schemes using pgvector (top 5)...")
        
        # Search for similar schemes (top 5)
        results = search_similar_schemes(
            query_embedding=query_embedding,
            top_k=5,
            filters={'is_active': True}
        )
        
        logger.info(f"📊 VECTOR_SEARCH_RESULTS: {len(results)} schemes found")
        
        # Apply title boost (fuzzy match on titles)
        from chatbot.vector_search import boost_title_match
        
        logger.info(f"🎯 Applying title boost (fuzzy match on scheme titles)...")
        for result in results:
            manual_distance = boost_title_match(query, result['title'])
            if manual_distance is not None:
                result['distance'] = manual_distance
                logger.info(f"  ✓ Title boost applied: {result['title']} → distance={manual_distance:.3f}")
        
        # Re-sort after boosting
        results.sort(key=lambda x: x['distance'])
        
        # Log top results
        logger.info(f"📊 TOP_VECTOR_RESULTS:")
        for i, r in enumerate(results[:3], 1):
            logger.info(f"  {i}. {r['title']} (distance: {r['distance']:.3f})")
        
        # ============================================================
        # STEP 5.1: APPLY STRICT THRESHOLD (0.30)
        # ============================================================
        # Only accept highly confident matches (distance <= 0.30 = ~85% similarity)
        
        DISTANCE_THRESHOLD = 0.30  # Strict threshold
        good_matches = [r for r in results if r['distance'] <= DISTANCE_THRESHOLD]
        
        logger.info(f"📏 THRESHOLD_CHECK: Applying distance threshold = {DISTANCE_THRESHOLD}")
        logger.info(f"✅ GOOD_MATCHES: {len(good_matches)} schemes within threshold")
        
        if not good_matches:
            # No confident matches - return 'No official scheme found'
            logger.info(f"❌ VECTOR_SEARCH_FAILED: All distances > {DISTANCE_THRESHOLD}")
            logger.info(f"🚀 RETURN_REASON: No schemes found within similarity threshold")
            
            # DO NOT call Gemini - return structured response
            no_match_message = "No official scheme found for your request."
            
            response_data = {
                'answer': no_match_message,
                'ssml': f"<speak>{no_match_message}</speak>",
                'schemes_used': [],
                'match_type': 'no_match_vector_threshold'
            }
            
            cache.set(cache_key, json.dumps(response_data), 43200)
            return Response(response_data)
        
        # Good matches found - log details before calling LLM
        logger.info(f"✅ VECTOR_SEARCH_SUCCESS: {len(good_matches)} schemes found")
        for i, match in enumerate(good_matches, 1):
            logger.info(f"  {i}. {match['title']} (distance: {match['distance']:.3f})")
        logger.info(f"🚀 RETURN_REASON: Proceeding to LLM with {len(good_matches)} schemes")
        
        # ============================================================
        # STEP 6: LLM ANSWER GENERATION (STRICT MODE)
        # ============================================================
        # Call Gemini ONLY with schemes found in Step 5
        # CRITICAL: Gemini must ONLY use provided schemes, never guess/invent
        
        logger.info(f"🤖 STEP 6: LLM_ANSWER_GENERATION (Gemini 1.5 Flash)")
        logger.info(f"📋 INPUT_SCHEMES: {len(good_matches)} schemes")
        
        from chatbot.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
        
        # Check if exact_title_match utility function exists
        try:
            from chatbot.embedding_utils import exact_title_match
            
            # Check if query matches any of the returned schemes
            for match in good_matches:
                scheme = match.get('scheme_object')
                if scheme and exact_title_match(query, scheme.title):
                    # Exact match within vector results - prioritize it
                    logger.info(f"✓ EXACT_MATCH_IN_VECTOR_RESULTS: {scheme.title}")
                    good_matches = [match]  # Use only this scheme
                    break
        except ImportError:
            pass  # Continue with all good matches
        
        # Build context from confident matches
        schemes_text_parts = []
        schemes_used = []
        
        for i, match in enumerate(good_matches, 1):
            scheme_obj = match.get('scheme_object')
            if scheme_obj:
                scheme_text = f"""
Scheme {i}: {scheme_obj.title}
- Distance Score: {match['distance']:.3f} (Confidence: {match.get('similarity_score', 0):.1f}%)
- Ministry: {scheme_obj.ministry or 'Not specified'}
- Government Level: {scheme_obj.government_level or 'Not specified'}
- Eligibility: {scheme_obj.eligibility_criteria[:200] if scheme_obj.eligibility_criteria else 'Check official website'}
- Benefits: {scheme_obj.benefits[:200] if scheme_obj.benefits else 'Check official website'}
- Application: {scheme_obj.application_link or scheme_obj.website or 'Visit official portal'}
"""
                schemes_text_parts.append(scheme_text.strip())
                schemes_used.append(scheme_obj.title)
        
        schemes_context = "\n\n".join(schemes_text_parts)
        
        # Configure Gemini with STRICT rules
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return Response({
                'error': 'GEMINI_API_KEY not configured',
                'error_code': 'CONFIG_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        genai.configure(api_key=api_key)
        
        # STRICT SYSTEM PROMPT - Prevents guessing/hallucination
        strict_system_prompt = """You are a FACTUAL government schemes assistant.

CRITICAL RULES (NEVER VIOLATE):
1. Use ONLY the schemes provided in the context below
2. NEVER guess, invent, or hallucinate scheme names
3. NEVER mention schemes not in the provided list
4. If user asks about schemes in general (e.g., "agricultural schemes"), list the provided schemes
5. If user asks about a specific scheme, check if it matches any provided scheme
6. If the scheme is in the list, answer about THAT SCHEME ONLY
7. If no schemes are provided in context: return exactly "No official scheme found for your request."
8. Always cite official links from the data
9. Keep answers concise (2-4 sentences)

FORMATTING RULES (STRICTLY ENFORCE):
- NO markdown formatting (no **, *, #, -, •, numbered lists)
- Use PLAIN TEXT ONLY
- Separate multiple schemes with a blank line
- Use simple text structure without bullets or formatting symbols
- NO bold, italic, headers, or special characters

Remember: You must ONLY use schemes from the provided context. No exceptions."""
        
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=strict_system_prompt
        )
        
        # Build strict user prompt
        user_prompt = f"""User Question: {query}

Available Government Schemes (ONLY use these - DO NOT invent others):

{schemes_context}

IMPORTANT INSTRUCTIONS:
1. If the user asks about schemes in general: Summarize the schemes provided above
2. If the user asks about a specific scheme: Check if it matches any above, answer about THAT scheme only
3. If no schemes are provided above: Return exactly "No official scheme found for your request."
4. Do NOT mention any schemes not in the list above
5. Use only the facts provided
6. Be helpful but strictly factual

Provide a concise, accurate answer (2-4 sentences):"""
        
        # Generate answer with Gemini (strict mode, temperature=0)
        logger.info(f"🤖 Calling Gemini API (temperature=0, strict mode)...")
        try:
            response = model.generate_content(
                user_prompt,
                generation_config={
                    'temperature': 0,  # Deterministic, no randomness
                    'max_output_tokens': 300,
                    'top_p': 0.1,
                    'top_k': 1
                }
            )
            
            final_answer = response.text.strip()
            
            # CRITICAL: Remove any markdown formatting from Gemini response
            from chatbot.utils.formatting import sanitize_markdown
            final_answer = sanitize_markdown(final_answer)
            
            logger.info(f"✅ GEMINI_RESPONSE_SUCCESS: {len(final_answer)} characters")
            logger.info(f"📝 Answer preview: {final_answer[:100]}...")
        except Exception as e:
            logger.error(f"❌ GEMINI_API_ERROR: {str(e)}")
            # Fallback: return schemes without LLM enhancement
            from chatbot.utils.formatting import sanitize_markdown
            final_answer = f"Here are the relevant government schemes:\n\n{schemes_context}"
            final_answer = sanitize_markdown(final_answer)
            logger.info(f"⚠️  Using fallback response (no LLM)")
        
        # Build response with match metadata
        logger.info(f"📦 Building response with {len(good_matches)} schemes")
        
        response_data = {
            'answer': final_answer,
            'ssml': f"<speak>{final_answer}</speak>",
            'schemes_used': [s['title'] for s in good_matches],
            'match_type': 'vector_llm',  # Vector search + LLM answer
            'similarity_threshold': DISTANCE_THRESHOLD,
            'matches_count': len(good_matches)
        }
        
        # Cache the result
        cache.set(cache_key, json.dumps(response_data), 43200)  # 12 hours
        logger.info(f"✅ Response cached and ready to return")
        logger.info(f"🚀 RETURN_REASON: Vector search + LLM answer generation complete")
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error in smart_answer_view: {str(e)}")
        return Response({
            'error': str(e),
            'answer': 'Sorry, I encountered an error processing your request.',
            'ssml': '<speak>Sorry, I encountered an error processing your request.</speak>'
        }, status=500)


# ============================================================
# SCHEME SUGGESTIONS API (Auto-Complete with Fuzzy Matching)
# ============================================================
        schemes_text_parts = []
        schemes_used = []
        
        for i, scheme in enumerate(good_matches, 1):
            scheme_text = f"""
Scheme {i}: {scheme['title']}
- Ministry/Department: {scheme.get('ministry', 'Not specified')}
- Government Level: {scheme.get('government_level', 'Not specified')}
- State: {scheme.get('state', 'Pan-India') or 'Pan-India'}
- Eligibility: {scheme.get('eligibility_criteria', 'Check official website')[:250]}
- Benefits: {scheme.get('benefits', 'Check official website')[:250]}
- How to Apply: Visit {scheme.get('application_link', 'official website')}
"""
            schemes_text_parts.append(scheme_text.strip())
            schemes_used.append(scheme['title'])
        
        schemes_text = "\n\n".join(schemes_text_parts)
        
        # Build user prompt with context
        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            schemes_text=schemes_text
        )
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return Response({
                'error': 'GEMINI_API_KEY not configured',
                'error_code': 'CONFIG_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        genai.configure(api_key=api_key)
        
        # Generate answer with Gemini (temperature=0 for factual responses)
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        generation_config = {
            'temperature': 0,  # Deterministic, factual responses
            'max_output_tokens': 300,
            'top_p': 0.1,
            'top_k': 1
        }
        
        logger.info("Generating answer with Gemini...")
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        final_answer = response.text.strip()
        
        # CRITICAL: Remove any markdown formatting for clean SSML voice output
        from chatbot.utils.formatting import sanitize_markdown
        final_answer = sanitize_markdown(final_answer)
        
        # Generate SSML for voice output
        ssml_answer = f"<speak>{final_answer}</speak>"
        
        # Build response
        response_data = {
            'answer': final_answer,
            'ssml': ssml_answer,
            'schemes_used': schemes_used
        }
        
        # Cache the response for 12 hours
        cache.set(cache_key, json.dumps(response_data), 43200)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Smart answer error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'error_code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# SCHEME SUGGESTIONS API (Auto-Complete with Fuzzy Matching)
# ============================================================

@api_view(['POST', 'GET'])
@csrf_exempt
def scheme_suggestions_view(request):
    """
    Scheme Suggestions API for Auto-Complete Dropdown.
    
    Provides intelligent auto-suggestions as user types:
    - Handles typos with fuzzy matching (rapidfuzz)
    - Supports abbreviations (PM → Pradhan Mantri)
    - Combines prefix matching + fuzzy matching
    - Returns top 10 most relevant schemes
    
    Features:
    - "pm ki" → suggests "Pradhan Mantri Kisan Samman Nidhi"
    - "ayshmn" → suggests "Ayushman Bharat"
    - "saman nidhi" → suggests "PM-KISAN"
    - Fast response (<50ms) for real-time UI
    
    POST/GET /api/suggestions/
    Request: { "partial_text": "pm ki", "max_suggestions": 10 }
    Response: [
        {"id": 1, "title": "Pradhan Mantri Kisan...", "score": 95, "match_type": "prefix"},
        {"id": 2, "title": "PM-KISAN", "score": 88, "match_type": "fuzzy"}
    ]
    """
    from chatbot.models import GovernmentScheme
    from chatbot.utils.normalization import get_scheme_suggestions
    from chatbot.serializers import SuggestionRequestSerializer, SchemeSuggestionSerializer
    
    try:
        # Handle both POST and GET requests
        if request.method == 'POST':
            partial_text = request.data.get('partial_text', '').strip()
            max_suggestions = request.data.get('max_suggestions', 10)
        else:  # GET
            partial_text = request.query_params.get('partial_text', '').strip()
            max_suggestions = int(request.query_params.get('max_suggestions', 10))
        
        # Validate input
        if not partial_text:
            return Response({
                'error': 'partial_text parameter is required',
                'error_code': 'MISSING_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(partial_text) < 2:
            return Response({
                'error': 'partial_text must be at least 2 characters',
                'error_code': 'INPUT_TOO_SHORT'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and cap max_suggestions
        try:
            max_suggestions = max(1, min(int(max_suggestions), 20))
        except (ValueError, TypeError):
            max_suggestions = 10
        
        logger.info(f"Suggestions request: '{partial_text}' (max: {max_suggestions})")
        
        # Get suggestions using fuzzy + prefix matching
        suggestions = get_scheme_suggestions(
            partial_text=partial_text,
            schemes_queryset=GovernmentScheme.objects,
            max_suggestions=max_suggestions
        )
        
        # Serialize response
        serializer = SchemeSuggestionSerializer(suggestions, many=True)
        
        logger.info(f"Returning {len(suggestions)} suggestions for '{partial_text}'")
        
        return Response({
            'suggestions': serializer.data,
            'count': len(suggestions),
            'query': partial_text
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'error_code': 'INTERNAL_ERROR',
            'suggestions': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# SMART QUERY API - PRODUCTION-READY
# ============================================================
# Complete rebuild with correct pipeline order and friendly responses
# Pipeline: Normalize → Exact Match → Fuzzy Match → Sector Intent → Vector Search → Gemini Fallback

@api_view(['POST'])
def smart_query_api(request):
    """
    Smart Query API - Friendly, Accurate, and Zero-Hallucination
    
    Pipeline (STRICT ORDER):
    1. Normalize query (remove yojana, scheme, etc.)
    2. Exact match (ILIKE + synonyms) → Return DB data immediately
    3. Fuzzy match (trigram ≥ 0.55) → Return DB data immediately
    4. Sector intent detection → Return list of DB schemes
    5. Vector search (cosine similarity > 0.70) → Return DB data
    6. Gemini fallback (only for greetings/chit-chat)
    
    Response Format:
    {
        "response": "<friendly conversational text>",
        "schemes": [...],  # List of schemes (if applicable)
        "exact_match": {...},  # Single scheme (if exact match)
        "fuzzy_match": {...},  # Single scheme (if fuzzy match)
        "match_type": "exact_match | fuzzy_match | sector_match | vector_match | gemini_fallback"
    }
    
    Rules:
    - DB data is NEVER modified (zero hallucination)
    - Friendly intro + exact DB content
    - Gemini used ONLY for non-scheme queries
    """
    from chatbot.query_helpers import (
        normalize_query_for_matching,
        detect_sector_intent,
        find_scheme_by_synonym,
        serialize_scheme,
        generate_friendly_intro,
        get_gemini_fallback_response
    )
    from chatbot.embedding_utils import create_embedding
    from chatbot.vector_search import search_similar_schemes
    
    try:
        # Get query from request
        query = request.data.get('query', '').strip()
        language = request.data.get('language', 'en')
        
        if not query:
            return Response({
                'error': 'Query parameter is required',
                'error_code': 'MISSING_QUERY'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"📝 SMART_QUERY: '{query}'")
        
        # Get language from user's UI selection (not auto-detected)
        user_language = request.data.get('lang', 'en')  # EN/KN/HI from dropdown
        logger.info(f"🌍 USER_SELECTED_LANGUAGE: {user_language}")
        
        # ============================================================
        # STEP 1: NORMALIZE QUERY
        # ============================================================
        normalized_query = normalize_query_for_matching(query)
        logger.info(f"🎯 NORMALIZED: '{normalized_query}'")
        
        # If normalized query is empty, it's likely a greeting or casual query
        if not normalized_query or len(normalized_query) < 3:
            logger.info(f"⚠️  Empty normalized query - using Gemini fallback")
            
            from chatbot.utils.multilingual import get_friendly_greeting, translate_with_gemini
            from .utils.formatting import sanitize_markdown
            
            greeting = get_friendly_greeting(user_language)
            greeting = sanitize_markdown(greeting)
            
            return Response({
                'language': user_language,
                'response': greeting,
                'schemes': [],
                'exact_match': None,
                'fuzzy_match': None,
                'match_type': 'greeting'
            })
        
        # ============================================================
        # STEP 2: EXACT MATCH (ILIKE + Synonyms)
        # ============================================================
        logger.info(f"🔍 STEP 2: Checking exact match...")
        
        # Try exact ILIKE match
        exact_scheme = GovernmentScheme.objects.filter(
            Q(title__icontains=normalized_query) | Q(title__icontains=query),
            is_active=True
        ).first()
        
        # Try synonym match if no exact match
        if not exact_scheme:
            exact_scheme = find_scheme_by_synonym(normalized_query, GovernmentScheme.objects)
        
        if exact_scheme:
            logger.info(f"✅ EXACT_MATCH: {exact_scheme.title}")
            
            from chatbot.utils.multilingual import get_match_intro, translate_scheme_if_needed
            from .utils.formatting import format_scheme_answer, sanitize_markdown
            
            # Get translated title for intro
            scheme_title = exact_scheme.title
            if user_language in ['kn', 'hi']:
                title_translations = exact_scheme.title_translations or {}
                if user_language in title_translations and title_translations[user_language]:
                    scheme_title = title_translations[user_language]
            
            friendly_intro = get_match_intro(user_language, 'exact_match', scheme_title=scheme_title)
            
            # Format scheme with language support
            formatted_scheme = format_scheme_answer(exact_scheme, include_llm_enhancement=False, user_language=user_language)
            
            # Translate if needed (no DB translation available)
            has_translation = user_language in (exact_scheme.title_translations or {}) and (exact_scheme.title_translations or {}).get(user_language)
            formatted_scheme = translate_scheme_if_needed(formatted_scheme, user_language, has_translation)
            
            # Sanitize
            formatted_scheme = sanitize_markdown(formatted_scheme)
            friendly_intro = sanitize_markdown(friendly_intro)
            
            return Response({
                'language': user_language,
                'response': friendly_intro,
                'schemes': [formatted_scheme],
                'exact_match': formatted_scheme,
                'fuzzy_match': None,
                'match_type': 'exact_match'
            })
        
        logger.info(f"⏭️  No exact match found")
        
        # ============================================================
        # STEP 3: FUZZY MATCH (Trigram Similarity ≥ 0.55)
        # ============================================================
        logger.info(f"🔍 STEP 3: Checking fuzzy match (trigram)...")
        
        # Use PostgreSQL trigram similarity
        fuzzy_matches = GovernmentScheme.objects.filter(
            is_active=True
        ).annotate(
            similarity=TrigramSimilarity('title', normalized_query)
        ).filter(
            similarity__gte=0.55  # 55% similarity threshold
        ).order_by('-similarity')[:1]
        
        if fuzzy_matches.exists():
            fuzzy_scheme = fuzzy_matches.first()
            similarity_score = fuzzy_scheme.similarity
            logger.info(f"✅ FUZZY_MATCH: {fuzzy_scheme.title} (similarity: {similarity_score:.2f})")
            
            from chatbot.utils.multilingual import get_match_intro, translate_scheme_if_needed
            from .utils.formatting import format_scheme_answer, sanitize_markdown
            
            # Get translated title for intro
            scheme_title = fuzzy_scheme.title
            if user_language in ['kn', 'hi']:
                title_translations = fuzzy_scheme.title_translations or {}
                if user_language in title_translations and title_translations[user_language]:
                    scheme_title = title_translations[user_language]
            
            friendly_intro = get_match_intro(user_language, 'fuzzy_match', scheme_title=scheme_title)
            
            # Format scheme with language support
            formatted_scheme = format_scheme_answer(fuzzy_scheme, include_llm_enhancement=False, user_language=user_language)
            
            # Translate if needed
            has_translation = user_language in (fuzzy_scheme.title_translations or {}) and (fuzzy_scheme.title_translations or {}).get(user_language)
            formatted_scheme = translate_scheme_if_needed(formatted_scheme, user_language, has_translation)
            
            # Sanitize
            formatted_scheme = sanitize_markdown(formatted_scheme)
            friendly_intro = sanitize_markdown(friendly_intro)
            
            return Response({
                'language': user_language,
                'response': friendly_intro,
                'schemes': [formatted_scheme],
                'exact_match': None,
                'fuzzy_match': formatted_scheme,
                'match_type': 'fuzzy_match',
                'similarity_score': float(similarity_score)
            })
        
        logger.info(f"⏭️  No fuzzy match found")
        
        # ============================================================
        # STEP 4: SECTOR INTENT DETECTION
        # ============================================================
        logger.info(f"🔍 STEP 4: Checking sector intent...")
        
        detected_sector = detect_sector_intent(query)
        
        if detected_sector:
            logger.info(f"✅ SECTOR_DETECTED: {detected_sector}")
            
            # Get all schemes from this sector
            sector_schemes = GovernmentScheme.objects.filter(
                sector__name__iexact=detected_sector,
                is_active=True
            )[:10]  # Limit to 10 schemes
            
            if sector_schemes.exists():
                count = sector_schemes.count()
                logger.info(f"✅ SECTOR_SCHEMES: {count} schemes found")
                
                from chatbot.utils.multilingual import get_sector_intro, translate_scheme_if_needed
                from .utils.formatting import format_scheme_answer, sanitize_markdown
                
                friendly_intro = get_sector_intro(user_language, detected_sector, count)
                
                # Format each scheme separately with language support
                formatted_schemes = []
                for scheme in sector_schemes:
                    formatted = format_scheme_answer(scheme, include_llm_enhancement=False, user_language=user_language)
                    
                    # Translate if needed
                    has_translation = user_language in (scheme.title_translations or {}) and (scheme.title_translations or {}).get(user_language)
                    formatted = translate_scheme_if_needed(formatted, user_language, has_translation)
                    
                    formatted = sanitize_markdown(formatted)
                    formatted_schemes.append(formatted)
                
                # Sanitize friendly intro
                friendly_intro = sanitize_markdown(friendly_intro)
                
                return Response({
                    'language': user_language,
                    'response': friendly_intro,
                    'schemes': formatted_schemes,
                    'exact_match': None,
                    'fuzzy_match': None,
                    'match_type': 'sector_match',
                    'sector': detected_sector,
                    'count': count
                })
        
        logger.info(f"⏭️  No sector match found")
        
        # ============================================================
        # STEP 5: VECTOR SEARCH (Cosine Similarity > 0.70)
        # ============================================================
        logger.info(f"🔍 STEP 5: Performing vector search...")
        
        # Generate embedding
        query_embedding = create_embedding(query)
        
        if query_embedding is None:
            logger.error(f"❌ Failed to generate embedding")
        else:
            # Search for similar schemes
            vector_results = search_similar_schemes(
                query_embedding=query_embedding,
                top_k=5,
                filters={'is_active': True}
            )
            
            logger.info(f"📊 VECTOR_RESULTS: {len(vector_results)} schemes found")
            
            # Filter by similarity threshold (0.70 = 70% similarity)
            # Note: distance threshold 0.30 roughly corresponds to 70% similarity
            good_vector_matches = [r for r in vector_results if r['distance'] <= 0.30]
            
            if good_vector_matches:
                count = len(good_vector_matches)
                logger.info(f"✅ VECTOR_MATCH: {count} schemes above threshold")
                
                # If single strong match, return it
                if count == 1:
                    top_match = good_vector_matches[0]
                    scheme_obj = top_match.get('scheme_object')
                    
                    if scheme_obj:
                        from chatbot.utils.multilingual import get_match_intro, translate_scheme_if_needed
                        from .utils.formatting import format_scheme_answer, sanitize_markdown
                        
                        # Get translated title for intro
                        scheme_title = scheme_obj.title
                        if user_language in ['kn', 'hi']:
                            title_translations = scheme_obj.title_translations or {}
                            if user_language in title_translations and title_translations[user_language]:
                                scheme_title = title_translations[user_language]
                        
                        friendly_intro = get_match_intro(user_language, 'vector_match', scheme_title=scheme_title, count=1)
                        
                        # Format scheme with language support
                        formatted_scheme = format_scheme_answer(scheme_obj, include_llm_enhancement=False, user_language=user_language)
                        
                        # Translate if needed
                        has_translation = user_language in (scheme_obj.title_translations or {}) and (scheme_obj.title_translations or {}).get(user_language)
                        formatted_scheme = translate_scheme_if_needed(formatted_scheme, user_language, has_translation)
                        
                        # Sanitize
                        formatted_scheme = sanitize_markdown(formatted_scheme)
                        friendly_intro = sanitize_markdown(friendly_intro)
                        
                        return Response({
                            'language': user_language,
                            'response': friendly_intro,
                            'schemes': [formatted_scheme],
                            'exact_match': None,
                            'fuzzy_match': None,
                            'match_type': 'vector_match',
                            'similarity_score': 1.0 - top_match['distance']
                        })
                
                # Multiple matches - return list with multilingual support
                else:
                    from chatbot.utils.multilingual import get_match_intro, translate_scheme_if_needed
                    from .utils.formatting import format_scheme_answer, sanitize_markdown
                    
                    friendly_intro = get_match_intro(user_language, 'vector_match', count=count)
                    
                    # Format each scheme separately with language support
                    formatted_schemes = []
                    for match in good_vector_matches:
                        scheme_obj = match.get('scheme_object')
                        if scheme_obj:
                            formatted = format_scheme_answer(scheme_obj, include_llm_enhancement=False, user_language=user_language)
                            
                            # Translate if needed
                            has_translation = user_language in (scheme_obj.title_translations or {}) and (scheme_obj.title_translations or {}).get(user_language)
                            formatted = translate_scheme_if_needed(formatted, user_language, has_translation)
                            
                            formatted = sanitize_markdown(formatted)
                            formatted_schemes.append(formatted)
                    
                    # Sanitize friendly intro
                    friendly_intro = sanitize_markdown(friendly_intro)
                    
                    return Response({
                        'language': user_language,
                        'response': friendly_intro,
                        'schemes': formatted_schemes,
                        'exact_match': None,
                        'fuzzy_match': None,
                        'match_type': 'vector_match',
                        'count': count
                    })
        
        logger.info(f"⏭️  No vector match found")
        
        # ============================================================
        # STEP 6: GEMINI FALLBACK (Only for non-scheme queries)
        # ============================================================
        logger.info(f"🔍 STEP 6: Using Gemini fallback...")
        
        from chatbot.utils.multilingual import get_no_scheme_message
        from .utils.formatting import sanitize_markdown
        
        fallback_message = get_no_scheme_message(user_language, query)
        fallback_message = sanitize_markdown(fallback_message)
        
        return Response({
            'language': user_language,
            'response': fallback_message,
            'schemes': [],
            'exact_match': None,
            'fuzzy_match': None,
            'match_type': 'no_match'
        })
    
    except Exception as e:
        logger.error(f"❌ SMART_QUERY_ERROR: {str(e)}", exc_info=True)
        return Response({
            'error': str(e),
            'error_code': 'INTERNAL_ERROR',
            'response': "Sorry, I encountered an error. Please try again!"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


