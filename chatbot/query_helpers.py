"""
Smart Query API - Helper Functions
Production-ready helper functions for the /api/query/ endpoint
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, F
from django.contrib.postgres.search import TrigramSimilarity
import google.generativeai as genai
import os


# ============================================================
# HELPER 1: NORMALIZE QUERY
# ============================================================

def normalize_query_for_matching(query: str) -> str:
    """
    Normalize user query for accurate scheme matching.
    
    Steps:
    1. Lowercase
    2. Remove accents/diacritics
    3. Remove punctuation
    4. Remove suffix words (yojana, scheme, mission, etc.)
    5. Remove stopwords
    6. Remove duplicate words
    7. Fix common spelling variations
    
    Args:
        query: Raw user input
        
    Returns:
        Normalized query string
        
    Examples:
        "PM Kisan Samman Nidhi Yojana" → "pm kisan samman nidhi"
        "agriculture schemes available" → "agriculture"
        "ayushman bharat scheme details" → "ayushman bharat"
    """
    if not query:
        return ""
    
    # Step 1: Lowercase
    query = query.lower()
    
    # Step 2: Remove accents/diacritics
    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ascii', 'ignore').decode('ascii')
    
    # Step 3: Remove punctuation
    query = re.sub(r'[^a-z0-9\s]', ' ', query)
    
    # Step 4: Fix common spelling variations BEFORE removing suffixes
    spelling_fixes = {
        # PM Kisan variations
        'pmkisan': 'pm kisan',
        'pm kissan': 'pm kisan',
        'pm kishan': 'pm kisan',
        'saman': 'samman',
        'samandan': 'samman',
        'nidhi': 'nidhi',
        'nidi': 'nidhi',
        
        # Ayushman variations
        'ayushman': 'ayushman',
        'aayushman': 'ayushman',
        'ayushmaan': 'ayushman',
        
        # Common words
        'yojna': 'yojana',
        'yojana': 'yojana',
        'yogana': 'yojana',
        'yajana': 'yojana',
    }
    
    for wrong, correct in spelling_fixes.items():
        query = query.replace(wrong, correct)
    
    # Step 5: Remove suffix words (scheme-related generic terms)
    suffix_words = {
        'yojana', 'yojna', 'scheme', 'schemes', 'mission', 'abhiyan', 'abhiyaan',
        'program', 'programme', 'project', 'initiative', 'campaign', 'drive',
        'government', 'govt', 'central', 'state', 'national',
        'details', 'information', 'info', 'benefits', 'eligibility',
        'application', 'apply', 'process', 'available', 'list'
    }
    
    # Step 6: Remove stopwords
    stopwords = {
        'what', 'how', 'when', 'where', 'why', 'who', 'which', 'whose',
        'tell', 'give', 'show', 'explain', 'describe', 'provide', 'get',
        'find', 'search', 'know', 'need', 'want', 'about',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'into', 'my', 'me', 'i',
        'is', 'are', 'am', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could',
        'will', 'would', 'should', 'shall', 'may', 'might', 'must',
        'there', 'their', 'this', 'that', 'these', 'those', 'it', 'its'
    }
    
    # Split into words
    words = query.split()
    
    # Filter words
    meaningful_words = []
    for word in words:
        if not word:
            continue
        if word in stopwords:
            continue
        if word in suffix_words:
            continue
        meaningful_words.append(word)
    
    # Step 7: Remove duplicate words while preserving order
    seen = set()
    unique_words = []
    for word in meaningful_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)
    
    # Join and collapse spaces
    normalized = ' '.join(unique_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


# ============================================================
# HELPER 2: DETECT SECTOR INTENT
# ============================================================

def detect_sector_intent(query: str) -> Optional[str]:
    """
    Detect if user is asking about schemes from a specific sector.
    
    Args:
        query: Normalized query
        
    Returns:
        Sector name if detected, else None
        
    Examples:
        "agriculture schemes" → "agriculture"
        "health yojana" → "health"
        "education programs" → "education"
    """
    query_lower = query.lower()
    
    sector_keywords = {
        'agriculture': ['agriculture', 'agricultural', 'farming', 'farmer', 'crop', 'kisan'],
        'health': ['health', 'healthcare', 'medical', 'hospital', 'ayushman', 'treatment'],
        'education': ['education', 'educational', 'school', 'scholarship', 'student', 'study'],
        'employment': ['employment', 'job', 'rozgar', 'work', 'skill', 'training'],
        'social_welfare': ['social', 'welfare', 'pension', 'widow', 'disabled'],
        'rural_development': ['rural', 'village', 'grameen', 'mgnrega'],
        'urban_development': ['urban', 'city', 'municipal', 'housing', 'awas'],
        'women_empowerment': ['women', 'woman', 'girl', 'beti', 'mahila', 'nari'],
        'youth_development': ['youth', 'young', 'yuva'],
        'senior_citizens': ['senior', 'elderly', 'old', 'age'],
        'disability': ['disabled', 'disability', 'handicapped'],
    }
    
    for sector, keywords in sector_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                return sector
    
    return None


# ============================================================
# HELPER 3: SCHEME NAME SYNONYMS
# ============================================================

SCHEME_SYNONYMS = {
    'pm kisan samman nidhi': [
        'pm kisan', 'pmkisan', 'kisan samman nidhi', 'pradhan mantri kisan samman nidhi',
        'pm kisan yojana', 'kisan yojana', 'pm kissan', 'pm kishan'
    ],
    'ayushman bharat': [
        'ayushman', 'pmjay', 'pm jan arogya yojana', 'jan arogya',
        'ayushman bharat yojana', 'aayushman bharat'
    ],
    'pradhan mantri awas yojana': [
        'pm awas', 'pmay', 'awas yojana', 'housing scheme', 'pradhan mantri awas'
    ],
    'pradhan mantri mudra yojana': [
        'mudra', 'pmmy', 'mudra yojana', 'mudra loan', 'pm mudra'
    ],
    'beti bachao beti padhao': [
        'bbbp', 'beti bachao', 'beti padhao', 'girl child scheme'
    ],
    'mgnrega': [
        'nrega', 'mahatma gandhi nrega', 'employment guarantee', 'rural employment'
    ],
}


def find_scheme_by_synonym(normalized_query: str, schemes_queryset) -> Optional[object]:
    """
    Find scheme by checking synonyms.
    
    Args:
        normalized_query: Normalized user query
        schemes_queryset: Django queryset of schemes
        
    Returns:
        Scheme object if found, else None
    """
    for canonical_name, synonyms in SCHEME_SYNONYMS.items():
        # Check if query matches canonical name or any synonym
        if normalized_query == canonical_name or normalized_query in synonyms:
            # Try to find scheme with canonical name
            scheme = schemes_queryset.filter(
                title__icontains=canonical_name,
                is_active=True
            ).first()
            if scheme:
                return scheme
    
    return None


# ============================================================
# HELPER 4: SERIALIZE SCHEME FOR RESPONSE
# ============================================================

def serialize_scheme(scheme) -> Dict:
    """
    Serialize GovernmentScheme object to JSON-friendly dict.
    
    Args:
        scheme: GovernmentScheme instance
        
    Returns:
        Dictionary with scheme data
    """
    return {
        'id': scheme.id,
        'title': scheme.title,
        'description': scheme.description,
        'short_description': scheme.short_description or scheme.description[:200] + '...',
        'sector': scheme.sector.name if scheme.sector else 'Other',
        'ministry': scheme.ministry,
        'department': scheme.department,
        'government_level': scheme.government_level,
        'state': scheme.state,
        'eligibility_criteria': scheme.eligibility_criteria,
        'benefits': scheme.benefits,
        'financial_assistance': scheme.financial_assistance,
        'application_process': scheme.application_process,
        'required_documents': scheme.required_documents,
        'application_link': scheme.application_link,
        'launch_date': scheme.launch_date.isoformat() if scheme.launch_date else None,
        'last_date': scheme.last_date.isoformat() if scheme.last_date else None,
        'helpline_number': scheme.helpline_number,
        'email': scheme.email,
        'website': scheme.website,
        'language': scheme.language,
    }


# ============================================================
# HELPER 5: FRIENDLY INTRO GENERATOR
# ============================================================

def generate_friendly_intro(match_type: str, scheme_title: str = None, sector: str = None, count: int = 0) -> str:
    """
    Generate friendly conversational intro based on match type (NO MARKDOWN).
    
    Args:
        match_type: Type of match (exact, fuzzy, sector, vector, etc.)
        scheme_title: Name of matched scheme (if applicable)
        sector: Sector name (if applicable)
        count: Number of schemes (if multiple)
        
    Returns:
        Friendly intro message (plain text only)
    """
    if match_type == 'exact_match':
        return f"Sure! Here's the information about {scheme_title}."
    
    elif match_type == 'fuzzy_match':
        return f"I found this scheme for you: {scheme_title}."
    
    elif match_type == 'sector_match':
        if count == 1:
            return f"Here's 1 scheme from the {sector} sector."
        else:
            return f"Great! I found {count} schemes from the {sector} sector."
    
    elif match_type == 'vector_match':
        if count == 1:
            return f"Based on your query, here's what I found: {scheme_title}."
        else:
            return f"I found {count} relevant schemes for you."
    
    else:
        return "Here's what I found for you."


# ============================================================
# HELPER 6: GEMINI FALLBACK
# ============================================================

def get_gemini_fallback_response(query: str) -> str:
    """
    Get conversational response from Gemini for non-scheme queries.
    
    Args:
        query: User query
        
    Returns:
        Gemini's response
    """
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return "I'm here to help you with government schemes. Please try asking about a specific scheme or sector!"
        
        genai.configure(api_key=api_key)
        
        system_prompt = """You are a helpful government schemes chatbot assistant.

CRITICAL FORMATTING RULES:
- Respond ONLY in plain text
- NO markdown formatting (no **, *, #, -, •)
- NO headings, NO bullets, NO bold text
- NO numbered lists
- Use simple sentences only

Content Rules:
1. Be friendly, conversational, and warm
2. Keep responses SHORT (1-2 sentences max)
3. If user greets you → greet back warmly
4. If user asks about schemes → suggest they specify a sector or scheme name
5. If user asks unrelated question → politely redirect to government schemes
6. NO emojis
7. Never make up or invent scheme names
8. Plain text ONLY - no formatting symbols
"""
        
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        response = model.generate_content(
            query,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 100,
            }
        )
        
        answer = response.text.strip()
        
        # Remove any markdown formatting
        from chatbot.utils.formatting import sanitize_markdown
        answer = sanitize_markdown(answer)
        
        return answer
    
    except Exception as e:
        return "I'm here to help you with government schemes! Please ask about a specific scheme or sector like agriculture, health, or education 😊"
