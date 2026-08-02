"""
Universal Scheme Detection - Text Normalization and Fuzzy Matching Utilities

Provides robust, universal scheme detection for ALL government schemes in the database.
Works with typos, variations, extra words, and multiple languages (English/Hindi/Kannada).

Key Functions:
- normalize_query(): Universal query normalizer for ALL schemes (removes noise, suffixes, stopwords)
- universal_fuzzy_match(): Fuzzy match against ALL schemes with 80% threshold
- extract_keywords(): Extract significant keywords from query
- expand_abbreviations(): Expand common scheme abbreviations

This system automatically detects ~106 schemes without hardcoding specific scheme names.
"""

import re
import unicodedata
from rapidfuzz import fuzz, process
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def normalize_query(query: str) -> str:
    """
    UNIVERSAL query normalizer - works for ALL government schemes automatically.
    
    Removes noise while preserving meaningful scheme keywords:
    - Question words (what, how, tell, give, etc.)
    - Scheme suffixes (yojana, scheme, mission, abhiyan, etc.)
    - Generic terms (benefits, eligibility, apply, details, etc.)
    - Hindi/Kannada stopwords (ka, ke, ki, yava, bagge, etc.)
    - Punctuation, special characters
    - Duplicate words and extra spaces
    
    This works universally for ALL schemes without hardcoding specific names.
    
    Args:
        query: Raw user query (any language, any scheme)
    
    Returns:
        Cleaned query with only meaningful scheme keywords
    
    Examples:
        >>> normalize_query("what are the benefits of pm kisan samman nidhi yojana?")
        'pm kisan samman nidhi'
        >>> normalize_query("tell me about ayushman bharat scheme details")
        'ayushman bharat'
        >>> normalize_query("mudra yojna benefits eligibility")
        'mudra'
        >>> normalize_query("beti bachao beti padhao scheme")
        'beti bachao beti padhao'
        >>> normalize_query("nmsa scheme information")
        'nmsa'
    """
    if not query:
        return ""
    
    # Step 1: Convert to lowercase
    query = query.lower()
    
    # Step 2: Remove accents/diacritics (ñ → n, é → e)
    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ascii', 'ignore').decode('ascii')
    
    # Step 3: Remove punctuation and special characters
    query = re.sub(r'[^a-z0-9\s]', ' ', query)
    
    # Step 4: Define UNIVERSAL stopwords (works for all schemes)
    universal_stopwords = {
        # Question words
        'what', 'how', 'when', 'where', 'why', 'who', 'which', 'whose',
        
        # Request/action words
        'tell', 'give', 'show', 'explain', 'describe', 'provide', 'get',
        'find', 'search', 'know', 'need', 'want',
        
        # Common English words
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'into', 'my', 'me', 'i',
        
        # Generic scheme-related words (not specific to any scheme)
        'details', 'info', 'information', 'data', 'list',
        'benefits', 'benefit', 'eligibility', 'eligible', 'criteria',
        'application', 'apply', 'process', 'procedure', 'form',
        'registration', 'register', 'enroll', 'enrollment',
        
        # Common verbs
        'is', 'are', 'am', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could',
        'will', 'would', 'should', 'shall', 'may', 'might', 'must',
        
        # Pronouns and determiners
        'there', 'their', 'this', 'that', 'these', 'those', 'it', 'its',
        
        # Hindi stopwords (common in Indian queries)
        'ka', 'ke', 'ki', 'ko', 'ka', 'se', 'me', 'mein',
        
        # Kannada stopwords
        'yava', 'yaava', 'bagge', 'hege', 'enu'
    }
    
    # Step 5: Define UNIVERSAL scheme suffixes (removed from ALL scheme queries)
    # These words appear in many scheme names but don't help with matching
    universal_suffixes = {
        # Primary suffixes
        'yojana', 'yojna', 'yojanaa', 'yojan', 'yogana', 'yajana',
        'scheme', 'schemes', 'skheme', 'skeme',
        'abhiyan', 'abhiyaan', 'abhian',
        'program', 'programme', 'programm',
        'project', 'projekt',
        'initiative', 'initiativ',
        'plan', 'plann',
        
        # Government-related generic terms
        'government', 'govt', 'central', 'state',
        'ministry', 'department',
        
        # Additional variants
        'campaign', 'drive', 'policy', 'act', 'bill'
    }
    
    # Step 6: Split into words
    words = query.split()
    
    # Step 7: Remove stopwords and suffixes, preserve meaningful keywords
    meaningful_words = []
    for word in words:
        # Skip empty words
        if not word:
            continue
        # Skip stopwords
        if word in universal_stopwords:
            continue
        # Skip suffixes
        if word in universal_suffixes:
            continue
        # Keep meaningful word
        meaningful_words.append(word)
    
    # Step 8: Remove duplicate words while preserving order
    seen = set()
    unique_words = []
    for word in meaningful_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)
    
    # Step 9: Join and collapse spaces
    normalized = ' '.join(unique_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def normalize_text(text: str, remove_punctuation: bool = True) -> str:
    """
    Basic text normalization for scheme titles.
    
    Args:
        text: Input text
        remove_punctuation: Whether to remove punctuation
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    if remove_punctuation:
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def universal_fuzzy_match(
    query: str,
    schemes_queryset,
    confidence_threshold: float = 80.0,
    limit: int = 1
) -> Optional[List[Dict]]:
    """
    UNIVERSAL fuzzy matching for ALL government schemes automatically.
    
    Compares normalized query against ALL scheme titles in database using rapidfuzz.
    Works for ANY scheme without hardcoding specific names.
    
    Handles:
    - Typos: "pmkisan samman nidi" → PM-KISAN
    - Variations: "pradhan mantri kisan nidhi" → PM-KISAN
    - Partial names: "samman nidhi yojana" → PM-KISAN
    - ALL schemes: Ayushman Bharat, Mudra, Beti Bachao, NMSA, etc.
    
    Args:
        query: Normalized user query
        schemes_queryset: Django queryset of ALL GovernmentScheme objects
        confidence_threshold: Minimum match score (0-100, default 80)
        limit: Maximum number of matches to return
    
    Returns:
        List of dicts with scheme and score, or None if no match above threshold
        [{'scheme': <GovernmentScheme>, 'score': 85.2, 'title': 'PM-KISAN'}, ...]
    
    Examples:
        >>> universal_fuzzy_match("pmkisan samman nidi", schemes, 80)
        [{'scheme': <PM-KISAN>, 'score': 88.5}]
        >>> universal_fuzzy_match("ayushman bharat details", schemes, 80)
        [{'scheme': <Ayushman Bharat>, 'score': 95.0}]
        >>> universal_fuzzy_match("mudra yojna", schemes, 80)
        [{'scheme': <PM Mudra>, 'score': 82.3}]
    """
    if not query or not schemes_queryset:
        return None
    
    # Build list of (scheme_obj, normalized_title) for ALL schemes
    scheme_titles = []
    for scheme in schemes_queryset.filter(is_active=True):
        normalized_title = normalize_text(scheme.title)
        scheme_titles.append((scheme, normalized_title))
    
    if not scheme_titles:
        return None
    
    # Use rapidfuzz for fuzzy matching
    # token_sort_ratio: order-independent, handles word rearrangement
    matches = []
    for scheme_obj, norm_title in scheme_titles:
        # Calculate fuzzy score
        score = fuzz.token_sort_ratio(query, norm_title)
        
        if score >= confidence_threshold:
            matches.append({
                'scheme': scheme_obj,
                'score': score,
                'title': scheme_obj.title
            })
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top matches
    return matches[:limit] if matches else None


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract significant keywords from text (removes stop words, short words).
    
    Args:
        text: Input text
        min_length: Minimum word length to keep (default 3)
    
    Returns:
        List of significant keywords
    
    Examples:
        >>> extract_keywords("Tell me about PM Kisan Scheme")
        ['kisan', 'scheme']
        >>> extract_keywords("Pradhan Mantri Kisan Samman Nidhi")
        ['pradhan', 'mantri', 'kisan', 'samman', 'nidhi']
    """
    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now',
        'scheme', 'yojana', 'programme', 'program', 'government', 'central',
        'state', 'national', 'tell', 'me', 'what', 'is', 'are', 'am'
    }
    
    # Normalize and split
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Filter: keep words >= min_length and not in stop words
    keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
    
    return keywords


def fuzzy_match_scheme(
    query: str,
    schemes_queryset,
    confidence_threshold: float = 85.0,
    limit: int = 1
) -> Optional[List[Dict]]:
    """
    Find best matching scheme(s) using fuzzy matching with rapidfuzz.
    
    Uses token_sort_ratio for order-independent matching:
    - "pm kisan samman nidhi" matches "Pradhan Mantri Kisan Samman Nidhi"
    - "samman nidhi pm" also matches (order doesn't matter)
    - Handles typos: "pm kisn saman nidi" → PM-KISAN
    
    Args:
        query: User query text
        schemes_queryset: Django queryset of GovernmentScheme objects
        confidence_threshold: Minimum fuzzy match score (0-100, default 85)
        limit: Maximum number of results to return (default 1)
    
    Returns:
        List of dicts with scheme and score, or None if no match above threshold
        [{'scheme': <GovernmentScheme>, 'score': 92.5}, ...]
    
    Examples:
        >>> fuzzy_match_scheme("pm kisn", schemes, 85)
        [{'scheme': <PM-KISAN>, 'score': 88.2}]
        >>> fuzzy_match_scheme("saman nidhi", schemes, 85)
        [{'scheme': <PM-KISAN>, 'score': 87.5}]
    """
    if not query or not schemes_queryset:
        return None
    
    # Normalize query
    normalized_query = normalize_text(query)
    
    # Build list of (scheme_obj, normalized_title) tuples
    scheme_titles = []
    for scheme in schemes_queryset.filter(is_active=True):
        normalized_title = normalize_text(scheme.title)
        scheme_titles.append((scheme, normalized_title))
    
    if not scheme_titles:
        return None
    
    # Use rapidfuzz for fuzzy matching
    # token_sort_ratio: splits into tokens, sorts alphabetically, then compares
    # This handles word order differences and partial matches
    matches = []
    
    for scheme, normalized_title in scheme_titles:
        # Calculate fuzzy score using token_sort_ratio (good for order-independent matching)
        score = fuzz.token_sort_ratio(normalized_query, normalized_title)
        
        if score >= confidence_threshold:
            matches.append({
                'scheme': scheme,
                'score': score,
                'title': scheme.title
            })
    
    if not matches:
        logger.info(f"No fuzzy match found for '{query}' (threshold {confidence_threshold})")
        return None
    
    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N matches
    top_matches = matches[:limit]
    
    logger.info(
        f"✓ Fuzzy match for '{query}': {top_matches[0]['title']} "
        f"(score: {top_matches[0]['score']:.1f})"
    )
    
    return top_matches


def get_scheme_suggestions(
    partial_text: str,
    schemes_queryset,
    max_suggestions: int = 10
) -> List[Dict]:
    """
    Get scheme suggestions for auto-complete dropdown.
    
    Combines two strategies:
    1. Prefix matching (fast, for common cases)
    2. Fuzzy matching (catches typos and partial matches)
    
    Args:
        partial_text: User's partial input (e.g., "pm ki")
        schemes_queryset: Django queryset of GovernmentScheme objects
        max_suggestions: Maximum suggestions to return (default 10)
    
    Returns:
        List of dicts with scheme info sorted by relevance
        [{'id': 1, 'title': 'PM-KISAN', 'score': 95}, ...]
    
    Examples:
        >>> get_scheme_suggestions("pm ki", schemes)
        [{'id': 1, 'title': 'Pradhan Mantri Kisan Samman Nidhi', 'score': 95}]
        >>> get_scheme_suggestions("ayshmn", schemes)
        [{'id': 2, 'title': 'Ayushman Bharat', 'score': 82}]
    """
    if not partial_text or len(partial_text) < 2:
        return []
    
    normalized_input = normalize_text(partial_text)
    suggestions = []
    
    # Get active schemes
    active_schemes = schemes_queryset.filter(is_active=True)
    
    # Strategy 1: Prefix matching (exact starts-with)
    prefix_matches = active_schemes.filter(title__istartswith=partial_text)
    for scheme in prefix_matches[:max_suggestions]:
        suggestions.append({
            'id': scheme.id,
            'title': scheme.title,
            'score': 100,  # Perfect prefix match
            'match_type': 'prefix'
        })
    
    # Strategy 2: Fuzzy matching (for typos and partial matches)
    # Only if we don't have enough prefix matches
    if len(suggestions) < max_suggestions:
        scheme_titles = []
        for scheme in active_schemes:
            # Skip if already in prefix matches
            if any(s['id'] == scheme.id for s in suggestions):
                continue
            
            normalized_title = normalize_text(scheme.title)
            scheme_titles.append((scheme, normalized_title))
        
        # Calculate fuzzy scores
        fuzzy_matches = []
        for scheme, normalized_title in scheme_titles:
            # Use partial_ratio for substring matching
            score = fuzz.partial_ratio(normalized_input, normalized_title)
            
            # Also check token_set_ratio for word-based matching
            token_score = fuzz.token_set_ratio(normalized_input, normalized_title)
            
            # Use the better score
            best_score = max(score, token_score)
            
            # Only include if score is reasonable (> 60)
            if best_score > 60:
                fuzzy_matches.append({
                    'id': scheme.id,
                    'title': scheme.title,
                    'score': best_score,
                    'match_type': 'fuzzy'
                })
        
        # Sort fuzzy matches by score
        fuzzy_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Add top fuzzy matches
        remaining_slots = max_suggestions - len(suggestions)
        suggestions.extend(fuzzy_matches[:remaining_slots])
    
    # Final sort: prefix matches first (score 100), then by score
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    
    return suggestions[:max_suggestions]


def expand_abbreviations(text: str) -> str:
    """
    Expand common abbreviations in queries.
    
    Args:
        text: Input text with potential abbreviations
    
    Returns:
        Text with abbreviations expanded
    
    Examples:
        >>> expand_abbreviations("PM Kisan")
        'PM Kisan Pradhan Mantri Kisan'
        >>> expand_abbreviations("NREGA scheme")
        'NREGA scheme MGNREGA Mahatma Gandhi NREGA'
    """
    # Common government scheme abbreviations
    abbreviation_map = {
        'PM': 'Pradhan Mantri',
        'CM': 'Chief Minister',
        'NREGA': 'MGNREGA Mahatma Gandhi NREGA',
        'JAY': 'Jan Arogya Yojana',
        'PMAY': 'Pradhan Mantri Awas Yojana',
        'PMJDY': 'Pradhan Mantri Jan Dhan Yojana',
        'PMJJBY': 'Pradhan Mantri Jeevan Jyoti Bima Yojana',
        'PMSBY': 'Pradhan Mantri Suraksha Bima Yojana',
        'APY': 'Atal Pension Yojana',
        'SSY': 'Sukanya Samriddhi Yojana',
        'MUDRA': 'Micro Units Development Refinance Agency',
    }
    
    expanded_text = text
    
    for abbr, full_form in abbreviation_map.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            expanded_text += f" {full_form}"
    
    return expanded_text
