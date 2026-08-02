# chatbot/gemini_utils.py
import google.generativeai as genai
from django.conf import settings
import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)  # Use the standard Django logger

# Cache the configured model to avoid re-configuring on every call
_CACHED_MODEL: Optional[genai.GenerativeModel] = None


def clean_markdown(text: str) -> str:
    """Remove basic markdown formatting so TTS/SSML does not speak symbols.
    
    This function sanitizes text returned by Gemini to ensure voice synthesis
    speaks naturally without saying "asterisk", "hash", "pipe", etc.
    
    Args:
        text: Text that may contain markdown formatting
        
    Returns:
        Clean plain text safe for SSML/TTS
    """
    if not isinstance(text, str):
        return text

    # Remove headings ###, ##, #
    text = re.sub(r'#+\s*', '', text)

    # Remove bold/italic formatting **text** and *text*
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Remove bullets (*, -, •)
    text = text.replace("•", " ")
    text = text.replace("*", " ")
    text = text.replace("-", " ")

    # Remove table-like '|' characters
    text = text.replace("|", " ")

    # Collapse multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()


def configure_gemini() -> Optional[genai.GenerativeModel]:
    """Configures and returns a cached Gemini GenerativeModel, or None on failure.

    Reads GEMINI_API_KEY and an optional GEMINI_MODEL from Django settings. If
    the remote Gemini model cannot be used (wrong name / unsupported), this
    function will attempt to auto-select a working generation model from the
    available remote models and retry. If no suitable model is found, returns None.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        logger.warning('Gemini API Key (GEMINI_API_KEY) not found in settings; skipping remote AI.')
        return None

    model_name = getattr(settings, 'GEMINI_MODEL', '')
    
    # If no model specified or empty, use auto-detection
    if not model_name:
        model_name = 'gemini-1.5-flash-latest'  # Try latest first

    try:
        # Configure with API key
        genai.configure(api_key=api_key)

        # Try working model names in order of preference
        # Use actual available models from the API (as of Nov 2025)
        working_models = [
            'gemini-2.5-flash',           # Stable, fast, recommended
            'gemini-2.0-flash',           # Stable, alternative
            'gemini-2.5-pro',             # More capable
            'gemini-flash-latest',        # Latest flash version
            'gemini-pro-latest',          # Latest pro version
        ]
        
        for test_model in working_models:
            try:
                _CACHED_MODEL = genai.GenerativeModel(test_model)
                # Test the model with a simple prompt to verify it works
                test_response = _CACHED_MODEL.generate_content("Hi")
                if test_response and test_response.text:
                    logger.info('Successfully configured and tested model: %s', test_model)
                    return _CACHED_MODEL
            except Exception as e:
                logger.debug('Model %s failed: %s', test_model, str(e))
                continue
        
        logger.error('All known models failed to initialize')
        return None
            
    except Exception as e:
        logger.error('Error configuring Gemini API: %s', e)
        import traceback
        logger.debug(traceback.format_exc())
        # Try to list available models and auto-select a working one
        try:
            logger.info('Attempting to auto-select a working Gemini model from available models...')
            genai.configure(api_key=api_key)
            # The SDK exposes model listing; use safe attribute access
            list_fn = getattr(genai, 'list_models', None) or getattr(genai, 'Models', None)
            models = None
            if callable(list_fn):
                models = list_fn()
            elif hasattr(genai, 'Models') and hasattr(genai.Models, 'list'):
                models = genai.Models.list()

            if models:
                try:
                    # Models may be returned as an iterable of objects or dicts
                    names = []
                    candidates = []
                    for m in models:
                        nm = getattr(m, 'name', None) or m.get('name') if isinstance(m, dict) else None
                        if nm:
                            names.append(nm)
                            # Check if this model supports content generation
                            supported_methods = getattr(m, 'supported_generation_methods', None) or (m.get('supported_generation_methods') if isinstance(m, dict) else None)
                            if supported_methods and 'generateContent' in supported_methods:
                                candidates.append(nm)
                    
                    logger.info('Available Gemini models: %s', names[:20])
                    logger.info('Generation-capable models: %s', candidates[:10])
                    
                    # Try to pick a good default from candidates (prefer gemini-pro or gemini-1.5-*)
                    selected = None
                    for pref in ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']:
                        for c in candidates:
                            if pref in c:
                                selected = c
                                break
                        if selected:
                            break
                    
                    if not selected and candidates:
                        selected = candidates[0]
                    
                    if selected:
                        logger.info('Auto-selected model: %s', selected)
                        _CACHED_MODEL = genai.GenerativeModel(selected)
                        logger.info('Successfully configured auto-selected Gemini model: %s', selected)
                        return _CACHED_MODEL
                    else:
                        logger.warning('No generation-capable models found in available models list.')
                except Exception as select_e:
                    logger.warning('Model auto-selection failed: %s', select_e)
                    logger.info('Available models (raw): %s', str(models)[:1000])
        except Exception as list_e:
            logger.debug('Listing models failed: %s', list_e)

        _CACHED_MODEL = None
        return None


def _extract_title_from_prompt(prompt: str) -> str:
    """Attempt to extract the scheme title from prompts generated by views.

    The admin prompts use a pattern like: "... titled 'PM Surya Ghar'..." so we
    search for `titled '...'.` If not found, return a short fallback.
    """
    m = re.search(r"titled\s+'([^']+)'", prompt)
    if m:
        return m.group(1).strip()
    # try double quotes
    m = re.search(r'titled\s+"([^"]+)"', prompt)
    if m:
        return m.group(1).strip()
    return prompt.strip()[:50]


def _local_fallback_for_prompt(prompt: str) -> str:
    """Generate a deterministic, safe fallback string when remote AI is unavailable."""
    title = _extract_title_from_prompt(prompt)
    lower = prompt.lower()
    if 'description' in lower:
        return (
            f"{title} is a government scheme designed to support communities and individuals in need. "
            "The programme focuses on delivering key benefits to eligible beneficiaries, addressing both immediate needs and long-term improvements. "
            "Primary objectives include increasing access to services, providing financial or infrastructural support, and promoting inclusive development."
        )
    if 'eligibility' in lower:
        return (
            "- Resident of the relevant jurisdiction (e.g., India)\n"
            "- Meets any age or income thresholds specified by the scheme\n"
            "- Possesses required identity documents (Aadhaar, voter ID, etc.)\n"
            "- Meets any sector-specific conditions (e.g., farmer status, household income limits)"
        )
    if 'benefit' in lower or 'benefits' in lower:
        return (
            "- Direct financial assistance to eligible beneficiaries\n"
            "- Subsidies or discounts for goods and services related to the scheme\n"
            "- Access to government-provided infrastructure, training, or support services\n"
            "- Priority access to application processes or simplified documentation"
        )
    if 'documents' in lower or 'document' in lower:
        return (
            "- Proof of identity (Aadhaar / Voter ID / Passport)\n"
            "- Proof of residence (utility bill / ration card)\n"
            "- Proof of eligibility (income certificate, land records, etc.)\n"
            "- Passport-size photograph and completed application form"
        )
    # Generic fallback
    return f"No remote AI available. Suggested content for '{title}': Provide a short description, eligibility criteria, benefits and required documents."


def generate_text_with_gemini(prompt: str) -> str:
    """Generate text using Gemini when available, otherwise use a local fallback.

    This function never returns None: on failure it returns a helpful error
    string or a deterministic fallback so the admin UI can be prefilled.
    """
    model = configure_gemini()
    logger.debug("Generate text requested. Using remote model: %s", bool(model))

    # If remote model isn't configured, return deterministic local fallback
    if not model:
        logger.info('Using local fallback for AI generation (Gemini not configured or unavailable).')
        return clean_markdown(_local_fallback_for_prompt(prompt))

    try:
        logger.debug(f"Sending prompt to Gemini: '{prompt[:120]}...'")
        # Call generate_content without extra parameters for maximum compatibility
        response = model.generate_content(prompt)

        # Response handling: be defensive in case the SDK returns an unexpected shape
        generated_text = getattr(response, 'text', None)
        if generated_text:
            logger.debug('Gemini response received (truncated): %s', generated_text[:120])
            return clean_markdown(generated_text)

        # SDK may return parts or feedback; try to inspect for a fallback message
        parts = getattr(response, 'parts', None)
        if parts and len(parts) > 0:
            try:
                joined = ' '.join(p.text for p in parts if getattr(p, 'text', None))
                if joined:
                    return clean_markdown(joined)
            except Exception:
                pass

        # Safety block check
        pf = getattr(response, 'prompt_feedback', None)
        if pf and getattr(pf, 'block_reason', None):
            block_reason = getattr(pf, 'block_reason')
            logger.warning('Gemini prompt blocked: %s', block_reason)
            return clean_markdown(f"Error: The request was blocked by safety filters ({block_reason}).")

        logger.warning('Gemini returned no usable content; falling back to local generator.')
        return clean_markdown(_local_fallback_for_prompt(prompt))

    except Exception as e:
        # Known failure mode: model name not supported by SDK/API (404). Provide helpful log and fallback.
        logger.error('Error calling Gemini API: %s', e)
        import traceback
        logger.debug(traceback.format_exc())
        return clean_markdown(_local_fallback_for_prompt(prompt))