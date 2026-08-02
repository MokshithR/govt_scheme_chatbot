import os
import logging
import time
from typing import List, Dict, Optional

from .gemini_utils import clean_markdown

logger = logging.getLogger(__name__)

# Lazy import to avoid hard dependency if package is missing
_genai = None

# Try to load .env automatically (best effort)
try:
    from dotenv import load_dotenv  # type: ignore
    # Load from project root and current dir
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    load_dotenv()
except Exception:
    pass


def _ensure_loaded() -> bool:
    global _genai
    if _genai is not None:
        return True
    try:
        import google.generativeai as genai  # type: ignore
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("Gemini API key not found in environment (GEMINI_API_KEY/GOOGLE_API_KEY)")
            return False
        genai.configure(api_key=api_key)
        _genai = genai
        return True
    except Exception as e:
        logger.warning(f"Gemini client not available: {e}")
        return False


def _build_context_snippet(schemes: List[Dict], language: str) -> str:
    items = []
    for s in schemes[:5]:
        title = s.get('title') or ''
        desc = s.get('short_description') or s.get('description') or ''
        benefits = s.get('benefits') or ''
        eligibility = s.get('eligibility_criteria') or ''
        link = s.get('application_link') or s.get('source_url') or ''
        sector = s.get('sector') or ''
        part = f"Title: {title}\nSector: {sector}\nDescription: {desc}\nBenefits: {benefits}\nEligibility: {eligibility}\nLink: {link}"
        items.append(part)
    header = "Context: Government scheme search results from database (PostgreSQL/MongoDB). Use these as the factual source."
    return header + "\n\n" + "\n\n---\n\n".join(items)


# Candidate model fallbacks (try in order if configured model fails)
CANDIDATE_MODELS = [
    os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash'),
    'gemini-1.5',
    'gemini-1.0',
    'gemini-1.0-preview',
    'text-bison@001',
    'chat-bison@001'
]


def _try_generate_with_model(model_name: str, prompt: str):
    """Try to generate content with a specific model name. Returns response or raises."""
    model = _genai.GenerativeModel(model_name)
    return model.generate_content(prompt)


def list_available_models() -> List[str]:
    """Return a list of available model ids from the configured SDK, or an empty list on error."""
    if not _ensure_loaded():
        return []
    try:
        # Try common SDK entrypoints to list models
        # 1) genai.list_models()
        if hasattr(_genai, 'list_models'):
            resp = _genai.list_models()
            # resp may be a list of dict-like objects
            try:
                return [getattr(m, 'name', None) or m.get('name') or m.get('id') for m in resp]
            except Exception:
                return [str(r) for r in resp]
        # 2) _genai.Model.list()
        if hasattr(_genai, 'Model') and hasattr(_genai.Model, 'list'):
            resp = _genai.Model.list()
            try:
                return [getattr(m, 'name', None) or m.get('name') or m.get('id') for m in resp]
            except Exception:
                return [str(r) for r in resp]
        # 3) fall back to attribute scan
        candidates = []
        for name in dir(_genai):
            if 'model' in name.lower():
                candidates.append(name)
        return candidates
    except Exception as e:
        logger.warning(f"Could not list Gemini models: {e}")
        return []


def gemini_enhance_response(query: str, language: str, base_text: str, schemes: List[Dict], intent: str) -> Optional[str]:
    """Use Gemini to rewrite the response in a friendly, detailed style, grounded in provided schemes.
    Returns enhanced text or None on failure.
    """
    if not _ensure_loaded():
        return None
    try:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        context = _build_context_snippet(schemes, language)
        system_style = (
            "You are a helpful, friendly assistant for Indian government schemes. "
            "Start with 2-3 friendly sentences, then provide more detail in plain-text paragraphs (no lists). "
            "Use the provided context as the primary source. If a field is clipped or missing, carefully complete the sentence and fill small gaps using your general knowledge, but: "
            "- clearly mark uncertain or inferred details (e.g., 'Typically', 'In most cases'). "
            "- avoid fabricating exact monetary figures or dates unless highly confident. "
            "- prefer citing or pointing to the official link for authoritative details. "
            "Prefer the conversation language ('en' or 'kn'). Keep the tone warm and clear. "
            "Return PLAIN TEXT only: no markdown, no headings, no bullets, no asterisks, no '#' symbols, "
            "no bold/italic formatting. Respond in normal sentences and short paragraphs only."
        )
        prompt = (
            f"{system_style}\n\n"
            f"User query: {query}\n"
            f"Detected intent: {intent}\n"
            f"Language: {language}\n\n"
            f"Base answer (from database):\n{base_text}\n\n"
            f"{context}\n\n"
            "Rewrite and enrich the base answer. Use the context as ground truth; where the context is incomplete, carefully complete the thought and label any inferred details. "
            "Include: a friendly intro, top 3-5 key points (benefits/eligibility/process), and a clear call-to-action with the official link if present."
        )
        attempts = 1
        try:
            attempts = int(os.environ.get("GEMINI_RETRIES", "2"))
        except Exception:
            attempts = 2
        backoff = 0.6
        last_exc = None
        resp = None
        # Try configured model first; on specific not-found error, try candidate fallbacks
        for i in range(max(1, attempts)):
            try:
                try:
                    resp = _try_generate_with_model(model_name, prompt)
                except Exception as e:
                    last_exc = e
                    msg = str(e).lower()
                    if 'not found' in msg or 'not supported' in msg or '404' in msg:
                        # try candidates in order
                        for alt in CANDIDATE_MODELS:
                            if alt == model_name:
                                continue
                            try:
                                resp = _try_generate_with_model(alt, prompt)
                                logger.info(f"Gemini: fell back to model {alt}")
                                break
                            except Exception:
                                continue
                    else:
                        raise
                if resp is not None:
                    break
            except Exception as e:
                last_exc = e
                if i < attempts - 1:
                    time.sleep(backoff)
                    backoff *= 1.6
                else:
                    raise
        text = getattr(resp, 'text', None)
        if not text:
            # SDK variants may use .candidates[0].content.parts[0].text
            try:
                candidates = getattr(resp, 'candidates', [])
                if candidates and candidates[0].content.parts:
                    text = candidates[0].content.parts[0].text
            except Exception:
                text = None
        return clean_markdown(text) if text else None
    except Exception as e:
        logger.warning(f"Gemini enhancement failed: {e}")
        return None


def gemini_is_greeting(message: str) -> Optional[bool]:
    """Classify whether the user message is a greeting using Gemini.
    Returns True for greeting, False for other, or None if unavailable/failure.
    """
    if not _ensure_loaded():
        return None
    try:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        prompt = (
            "You are a strict classifier. Decide if the user message is a greeting.\n"
            "GREETINGS include: hello, hi, hey, how are you, good morning/afternoon/evening, namaste, namaskara, etc.\n"
            "If it is a greeting, reply with exactly: GREETING\n"
            "Otherwise reply with exactly: OTHER\n"
            f"Message: {message}"
        )
        try:
            resp = _try_generate_with_model(model_name, prompt)
        except Exception as e:
            msg = str(e).lower()
            if 'not found' in msg or 'not supported' in msg or '404' in msg:
                resp = None
                for alt in CANDIDATE_MODELS:
                    if alt == model_name:
                        continue
                    try:
                        resp = _try_generate_with_model(alt, prompt)
                        logger.info(f"Gemini: fell back to model {alt} for greeting check")
                        break
                    except Exception:
                        continue
                if resp is None:
                    raise
            else:
                raise
        text = getattr(resp, 'text', '') or ''
        text = (text or '').strip().upper()
        if 'GREETING' in text and 'OTHER' not in text:
            return True
        if 'OTHER' in text and 'GREETING' not in text:
            return False
        # Defensive fallback on candidates
        try:
            candidates = getattr(resp, 'candidates', [])
            if candidates and candidates[0].content.parts:
                alt = candidates[0].content.parts[0].text.strip().upper()
                if alt == 'GREETING':
                    return True
                if alt == 'OTHER':
                    return False
        except Exception:
            pass
        return None
    except Exception as e:
        logger.warning(f"Gemini greeting classification failed: {e}")
        return None


def gemini_classify_intent(message: str) -> Optional[Dict[str, str]]:
    """Classify user intent using Gemini. Returns dict with keys:
    intent in {greeting, sector_query, scheme_query, application_date_query, application_general, unknown},
    sector (optional), scheme_name (optional).
    Returns None on failure/unavailable.
    """
    if not _ensure_loaded():
        return None
    try:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        prompt = (
            "You are an intent classifier for Indian government scheme queries.\n"
            "Return a single JSON object with keys: intent, sector, scheme_name.\n"
            "intent must be one of: greeting, sector_query, scheme_query, application_date_query, application_general, unknown.\n"
            "If sector or scheme_name is not applicable, set it to an empty string.\n"
            "Examples of sectors: agriculture, health, education, employment.\n"
            "Application date queries include questions about last date, deadline, closing date.\n"
            "Application_general includes: where/how to apply, where to register, how to check status, required documents, without specifying a specific date.\n"
            f"Message: {message}\n"
            "Respond with JSON only."
        )
        try:
            resp = _try_generate_with_model(model_name, prompt)
        except Exception as e:
            msg = str(e).lower()
            if 'not found' in msg or 'not supported' in msg or '404' in msg:
                resp = None
                for alt in CANDIDATE_MODELS:
                    if alt == model_name:
                        continue
                    try:
                        resp = _try_generate_with_model(alt, prompt)
                        logger.info(f"Gemini: fell back to model {alt} for intent classification")
                        break
                    except Exception:
                        continue
                if resp is None:
                    raise
            else:
                raise
        text = getattr(resp, 'text', '') or ''
        raw = (text or '').strip()
        import json as _json
        try:
            data = _json.loads(raw)
        except Exception:
            # Try extracting first JSON object if wrapped
            import re as _re
            m = _re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            try:
                data = _json.loads(m.group(0))
            except Exception:
                return None
        intent = (data.get('intent') or '').strip()
        sector = (data.get('sector') or '').strip()
        scheme_name = (data.get('scheme_name') or '').strip()
        if intent not in {"greeting", "sector_query", "scheme_query", "application_date_query", "application_general", "unknown"}:
            return None
        return {"intent": intent, "sector": sector, "scheme_name": scheme_name}
    except Exception as e:
        logger.warning(f"Gemini intent classification failed: {e}")
        return None


def gemini_answer(question: str) -> Optional[str]:
    """Generate an answer from Gemini for the given question. Returns text or None on failure."""
    if not _ensure_loaded():
        return None
    try:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        attempts = 1
        try:
            attempts = int(os.environ.get("GEMINI_RETRIES", "2"))
        except Exception:
            attempts = 2
        backoff = 0.6
        resp = None
        for i in range(max(1, attempts)):
            try:
                try:
                    resp = _try_generate_with_model(model_name, question)
                except Exception as e:
                    msg = str(e).lower()
                    if 'not found' in msg or 'not supported' in msg or '404' in msg:
                        resp = None
                        for alt in CANDIDATE_MODELS:
                            if alt == model_name:
                                continue
                            try:
                                resp = _try_generate_with_model(alt, question)
                                logger.info(f"Gemini: fell back to model {alt} for answer")
                                break
                            except Exception:
                                continue
                        if resp is None:
                            raise
                    else:
                        raise
                break
            except Exception as e:
                if i < attempts - 1:
                    time.sleep(backoff)
                    backoff *= 1.6
                else:
                    raise
        text = getattr(resp, 'text', '') or ''
        text = text.strip()
        cleaned = clean_markdown(text) if text else ''
        cleaned = cleaned.strip()
        return cleaned or None
    except Exception as e:
        logger.warning(f"Gemini answer failed: {e}")
        return None


def gemini_autofill_scheme(title: str, language: str = 'en') -> Optional[dict]:
    """Ask Gemini to produce a JSON object with fields for a GovernmentScheme given the title.
    Returns a dict mapping field names to values, or None on failure.
    """
    if not _ensure_loaded():
        return None
    try:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        model = _genai.GenerativeModel(model_name)
        prompt = (
            "You are a helpful assistant that, given the title of an Indian government scheme,"
            " returns a JSON object containing suggested values for administrative fields used by a database."
            " The JSON must contain the following keys (use empty string or empty lists where unknown):"
            " title, description, short_description, ministry, department, government_level, state, sector,"
            " eligibility_criteria, benefits, financial_assistance, application_process, required_documents,"
            " application_link, launch_date, last_date, validity_period, helpline_number, email, website,"
            " source_url, keywords, search_tags"
            "\n\nRespond with JSON only. Use ISO date format YYYY-MM-DD for dates. Do not include any explanatory text.\n"
            f"Title: {title}\nLanguage: {language}\n"
        )
        try:
            resp = _try_generate_with_model(model_name, prompt)
        except Exception as e:
            msg = str(e).lower()
            if 'not found' in msg or 'not supported' in msg or '404' in msg:
                resp = None
                for alt in CANDIDATE_MODELS:
                    if alt == model_name:
                        continue
                    try:
                        resp = _try_generate_with_model(alt, prompt)
                        logger.info(f"Gemini: fell back to model {alt} for autofill")
                        break
                    except Exception:
                        continue
                if resp is None:
                    raise
            else:
                raise
        text = getattr(resp, 'text', '') or ''
        raw = (text or '').strip()
        import json as _json
        try:
            data = _json.loads(raw)
        except Exception:
            # try to extract JSON object from the response
            import re as _re
            m = _re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            try:
                data = _json.loads(m.group(0))
            except Exception:
                return None
        # Ensure keys exist
        expected_keys = [
            'title', 'description', 'short_description', 'ministry', 'department', 'government_level',
            'state', 'sector', 'eligibility_criteria', 'benefits', 'financial_assistance', 'application_process',
            'required_documents', 'application_link', 'launch_date', 'last_date', 'validity_period',
            'helpline_number', 'email', 'website', 'source_url', 'keywords', 'search_tags'
        ]
        result = {k: data.get(k, '') for k in expected_keys}
        # Normalize list fields
        for lk in ('required_documents', 'keywords', 'search_tags'):
            if isinstance(result.get(lk), str):
                # try to parse as JSON list
                try:
                    parsed = _json.loads(result[lk])
                    if isinstance(parsed, list):
                        result[lk] = parsed
                    else:
                        result[lk] = [str(result[lk])]
                except Exception:
                    # comma separated fallback
                    result[lk] = [s.strip() for s in result[lk].split(',') if s.strip()]
            elif result.get(lk) is None:
                result[lk] = []

        return result
    except Exception as e:
        logger.warning(f"Gemini autofill failed: {e}")
        return None
