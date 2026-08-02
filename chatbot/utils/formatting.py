"""
Scheme Answer Formatting Utilities

Provides clean, concise, high-quality formatting for scheme information.
Designed to produce professional, user-friendly output for chatbot responses.

Key Functions:
- format_scheme_answer(): Format single scheme into clean text
- format_multiple_schemes(): Format multiple schemes into list
- format_eligibility(): Extract and format eligibility criteria
- format_benefits(): Extract and format key benefits
"""

import re
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def format_scheme_answer(scheme, include_llm_enhancement: bool = True, user_language: str = 'en') -> str:
    """
    Format a single government scheme into clean plain text (NO MARKDOWN).
    Supports multilingual output (English, Kannada, Hindi).
    
    Output structure with clear separator:
        Scheme Name: <title>
        Sector: <sector>
        Eligibility: <eligibility>
        Benefits: <benefits>
        Required Documents: <documents>
        Application Process: <process>
        Helpline: <helpline>
        Website: <website>
        ------------------------------------
    
    Args:
        scheme: GovernmentScheme model instance
        include_llm_enhancement: Whether to include prompt-ready format (default True)
        user_language: Target language code ('en', 'kn', 'hi')
    
    Returns:
        Clean plain text with separator (NO markdown symbols)
    """
    if not scheme:
        return "Scheme information not available."
    
    # Build formatted output (plain text only)
    lines = []
    
    # 1. Scheme Name - Use translated title if available
    title = scheme.title or "Government Scheme"
    
    # Check for translation in database
    if user_language in ['kn', 'hi']:
        title_translations = scheme.title_translations or {}
        if user_language in title_translations and title_translations[user_language]:
            title = title_translations[user_language]
    
    title_clean = sanitize_markdown(title)
    lines.append(f"Scheme Name: {title_clean}")
    
    # 2. Sector
    if hasattr(scheme, 'sector') and scheme.sector:
        lines.append(f"Sector: {scheme.sector.name}")
    
    # 3. Eligibility
    if scheme.eligibility_criteria:
        eligibility = format_eligibility_plain(scheme.eligibility_criteria)
        eligibility = sanitize_markdown(eligibility)
        lines.append(f"Eligibility: {eligibility}")
    
    # 4. Benefits (plain text, no bullets)
    if scheme.benefits:
        benefits = format_benefits_plain(scheme.benefits)
        benefits = sanitize_markdown(benefits)
        lines.append(f"Benefits: {benefits}")
    
    # 5. Required Documents
    if hasattr(scheme, 'required_documents') and scheme.required_documents:
        if isinstance(scheme.required_documents, list):
            docs = ", ".join(scheme.required_documents[:5])
            docs = sanitize_markdown(docs)
            lines.append(f"Required Documents: {docs}")
    
    # 6. Application Process
    if scheme.application_process:
        process = clean_text(scheme.application_process)
        process_short = extract_first_sentence(process, max_length=200)
        process_short = sanitize_markdown(process_short)
        lines.append(f"Application Process: {process_short}")
    
    # 7. Helpline
    if hasattr(scheme, 'helpline_number') and scheme.helpline_number:
        lines.append(f"Helpline: {scheme.helpline_number}")
    elif hasattr(scheme, 'helpline') and scheme.helpline:
        lines.append(f"Helpline: {scheme.helpline}")
    elif hasattr(scheme, 'contact_number') and scheme.contact_number:
        lines.append(f"Contact: {scheme.contact_number}")
    
    # 8. Website
    link = scheme.application_link or scheme.website
    if hasattr(scheme, 'official_link') and not link:
        link = scheme.official_link
    if link:
        lines.append(f"Website: {link}")
    
    # Add separator line
    lines.append("------------------------------------")
    
    return "\n".join(lines)


def format_multiple_schemes(schemes: List, max_schemes: int = 10) -> str:
    """
    Format multiple schemes as SEPARATE BLOCKS (NO MARKDOWN).
    
    Each scheme is fully formatted with all fields and separated by lines.
    
    Args:
        schemes: List of GovernmentScheme instances
        max_schemes: Maximum number of schemes to include (default 10)
    
    Returns:
        Plain text formatted scheme list with clear separators
    
    Example Output:
        Scheme 1:
        Scheme Name: PM-KISAN
        Sector: Agriculture
        Eligibility: ...
        Benefits: ...
        Website: ...
        ------------------------------------
        
        Scheme 2:
        Scheme Name: Ayushman Bharat
        Sector: Health
        Eligibility: ...
        Benefits: ...
        Website: ...
        ------------------------------------
    """
    if not schemes:
        return "No schemes found matching your criteria."
    
    # Limit to max_schemes
    schemes_to_show = schemes[:max_schemes]
    
    # Format each scheme as a complete block
    scheme_blocks = []
    
    for idx, scheme in enumerate(schemes_to_show, 1):
        # Use format_scheme_answer for each scheme (already has separator)
        formatted_scheme = format_scheme_answer(scheme, include_llm_enhancement=False)
        
        # Add scheme number header
        block = f"Scheme {idx}:\n{formatted_scheme}"
        scheme_blocks.append(block)
    
    # Join all blocks with blank lines
    return "\n\n".join(scheme_blocks)


def format_eligibility(eligibility_text: str, max_length: int = 200) -> str:
    """
    Format eligibility criteria into concise, readable text.
    
    Args:
        eligibility_text: Raw eligibility criteria text
        max_length: Maximum length of output (default 200)
    
    Returns:
        Clean, concise eligibility text
    
    Examples:
        >>> format_eligibility("Small and marginal farmers who own cultivable land...")
        'Small and marginal farmers with cultivable land up to 2 hectares'
    """
    if not eligibility_text:
        return "See official website for eligibility details"
    
    # Clean the text
    clean = clean_text(eligibility_text)
    
    # Get first sentence or truncate
    result = extract_first_sentence(clean, max_length=max_length)
    
    return result


def format_eligibility_plain(eligibility_text: str, max_length: int = 300) -> str:
    """
    Format eligibility criteria into plain text (NO markdown).
    
    Args:
        eligibility_text: Raw eligibility criteria text
        max_length: Maximum length of output (default 300)
    
    Returns:
        Clean plain text eligibility (no bullets, no markdown)
    """
    if not eligibility_text:
        return "See official website for eligibility criteria."
    
    # Clean the text and remove markdown
    clean = clean_text(eligibility_text)
    clean = remove_markdown(clean)
    
    # Get first 2-3 sentences
    sentences = re.split(r'[.!?]\s+', clean)
    result_sentences = []
    current_length = 0
    
    for sentence in sentences[:3]:
        sentence = sentence.strip()
        if sentence and current_length + len(sentence) < max_length:
            result_sentences.append(sentence)
            current_length += len(sentence)
    
    result = ". ".join(result_sentences)
    if result and not result.endswith('.'):
        result += '.'
    
    return result if result else "See official website for eligibility criteria."


def format_benefits(benefits_text: str, max_bullets: int = 3) -> List[str]:
    """
    Extract and format key benefits into bullet points.
    
    Args:
        benefits_text: Raw benefits text
        max_bullets: Maximum number of bullet points (default 3)
    
    Returns:
        List of benefit strings (without bullet symbols)
    
    Examples:
        >>> format_benefits("₹6000 per year. Direct bank transfer. No middleman.")
        ['₹6000 per year', 'Direct bank transfer', 'No middleman']
    """
    if not benefits_text:
        return ["Financial and non-financial benefits provided"]
    
    # Clean text
    clean = clean_text(benefits_text)
    
    # Try to split by common delimiters
    # Check for existing bullets or numbers
    if re.search(r'[•\-\*]\s', clean):
        # Already has bullets
        bullets = re.split(r'[•\-\*]\s+', clean)
        bullets = [b.strip() for b in bullets if b.strip()]
    elif re.search(r'\d+\.\s', clean):
        # Numbered list
        bullets = re.split(r'\d+\.\s+', clean)
        bullets = [b.strip() for b in bullets if b.strip()]
    else:
        # Split by sentences or periods
        bullets = re.split(r'[.;]\s+', clean)
        bullets = [b.strip() + '.' if not b.endswith('.') else b.strip() 
                  for b in bullets if b.strip()]
    
    # Take top N bullets
    top_bullets = bullets[:max_bullets]
    
    # Ensure each bullet is not too long
    formatted_bullets = []
    for bullet in top_bullets:
        if len(bullet) > 120:
            # Truncate long bullets
            bullet = bullet[:117] + '...'
        formatted_bullets.append(bullet)
    
    return formatted_bullets if formatted_bullets else ["See official website for benefits"]


def format_benefits_plain(benefits_text: str, max_length: int = 400) -> str:
    """
    Format benefits into plain text (NO markdown, NO bullets).
    
    Args:
        benefits_text: Raw benefits text
        max_length: Maximum length of output (default 400)
    
    Returns:
        Clean plain text benefits (comma-separated or sentence format)
    
    Examples:
        >>> format_benefits_plain("₹6000 per year. Direct bank transfer. No middleman.")
        'Rs 6000 per year, direct bank transfer, no middleman.'
    """
    if not benefits_text:
        return "Financial and non-financial benefits as per scheme guidelines."
    
    # Clean text and remove markdown
    clean = clean_text(benefits_text)
    clean = remove_markdown(clean)
    
    # Try to split by common delimiters
    if re.search(r'[•\-\*]\s', clean):
        # Remove bullet symbols
        clean = re.sub(r'[•\-\*]\s+', '', clean)
    
    if re.search(r'\d+\.\s', clean):
        # Remove numbering
        clean = re.sub(r'\d+\.\s+', '', clean)
    
    # Split by periods/semicolons and join with commas
    parts = re.split(r'[.;]\s+', clean)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
    
    # Take first 3-4 benefit points
    result_parts = parts[:4]
    
    # Join with commas if multiple, otherwise use as-is
    if len(result_parts) > 1:
        result = ", ".join(result_parts)
        if not result.endswith('.'):
            result += '.'
    else:
        result = result_parts[0] if result_parts else clean
        if not result.endswith('.'):
            result += '.'
    
    # Truncate if too long
    if len(result) > max_length:
        result = result[:max_length-3] + '...'
    
    return result


def sanitize_markdown(text: str) -> str:
    """
    AGGRESSIVELY remove ALL markdown symbols and formatting.
    
    This is the MAIN sanitizer used before returning any text to frontend.
    
    Removes:
    - Bold: ** __ 
    - Italic: * _ (single)
    - Headers: # ## ### (all levels)
    - Bullets: • * - (anywhere in text)
    - Numbered lists: 1. 2. 3.
    - Links: [text](url)
    - Code: `code` ```code```
    - All remaining stray * # - symbols
    
    Preserves:
    - Line breaks between content blocks
    - Paragraph spacing for readability
    
    Args:
        text: Text that may contain markdown
    
    Returns:
        100% clean plain text with preserved structure
    """
    if not text:
        return ""
    
    # First, normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove bold+italic (***text*** or ___text___) - MUST be first!
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    text = re.sub(r'___(.+?)___', r'\1', text)
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic (*text* or _text_) - be careful not to break underscores in words
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    
    # Remove headers (# ## ###) but keep the text on its own line
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove bullet points but preserve content
    text = re.sub(r'^\s*[•\*\-]\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove numbered lists but preserve content and add separation
    text = re.sub(r'^\s*\d+\.\s+(.+)$', r'\n\1', text, flags=re.MULTILINE)
    
    # Remove inline bullets
    text = re.sub(r'\s*[•]\s*', ' ', text)
    
    # Remove links [text](url) → text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Remove inline code `code` → code
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove code blocks ```code``` → (empty)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove any remaining backticks
    text = text.replace('`', '')
    
    # Remove table pipes |
    text = text.replace('|', ' ')
    
    # SSML safety: Escape HTML entities for voice synthesis
    text = text.replace('&', 'and')
    text = text.replace('<', '')
    text = text.replace('>', '')
    
    # Remove any remaining stray markdown symbols (including standalone asterisks)
    text = re.sub(r'\*+', '', text)  # Remove any asterisks
    text = re.sub(r'#+', '', text)   # Remove any hash symbols
    text = re.sub(r'_+(?!\w)', '', text)  # Remove trailing underscores
    
    # Clean up excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up spaces at start/end of lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Clean up multiple spaces within lines
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def remove_markdown(text: str) -> str:
    """
    Alias for sanitize_markdown (for backward compatibility).
    """
    return sanitize_markdown(text)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, HTML tags, and special characters.
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special Unicode characters but keep common ones (₹, etc.)
    # text = re.sub(r'[^\w\s\d.,!?;:\-₹%()\/]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_first_sentence(text: str, max_length: int = 150) -> str:
    """
    Extract first sentence or truncate to max_length.
    
    Args:
        text: Input text
        max_length: Maximum length (default 150)
    
    Returns:
        First sentence or truncated text
    """
    if not text:
        return ""
    
    # Find first sentence (period followed by space or end)
    match = re.search(r'^[^.!?]+[.!?](?:\s|$)', text)
    
    if match:
        sentence = match.group(0).strip()
        if len(sentence) <= max_length:
            return sentence
    
    # Fallback: truncate at max_length
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.7:  # At least 70% of max_length
        truncated = truncated[:last_space]
    
    return truncated.strip() + '...'


def format_for_llm(scheme, user_query: str) -> str:
    """
    Format scheme information for LLM processing (Gemini).
    
    Provides structured data that the LLM can use to generate natural answers.
    
    Args:
        scheme: GovernmentScheme instance
        user_query: Original user query (for context)
    
    Returns:
        Formatted text for LLM prompt
    """
    lines = []
    
    lines.append(f"SCHEME: {scheme.title}")
    lines.append(f"CATEGORY: {scheme.sector.name if hasattr(scheme, 'sector') and scheme.sector else 'General'}")
    
    if scheme.short_description:
        lines.append(f"DESCRIPTION: {clean_text(scheme.short_description)[:300]}")
    
    if scheme.eligibility_criteria:
        lines.append(f"ELIGIBILITY: {format_eligibility(scheme.eligibility_criteria)}")
    
    if scheme.benefits:
        benefits = format_benefits(scheme.benefits, max_bullets=3)
        lines.append(f"BENEFITS: {'; '.join(benefits)}")
    
    if scheme.application_process:
        process = clean_text(scheme.application_process)[:200]
        lines.append(f"HOW TO APPLY: {process}")
    
    link = scheme.application_link or scheme.website or scheme.official_link
    if link:
        lines.append(f"OFFICIAL LINK: {link}")
    
    return "\n".join(lines)


def format_fallback_message(query: str) -> str:
    """
    Format a helpful fallback message when no schemes are found (NO MARKDOWN).
    
    Args:
        query: User's original query
    
    Returns:
        Plain text fallback message
    """
    return f"""I couldn't find an official government scheme matching "{query}" exactly.

This could mean:
The scheme name might be slightly different, or it might be a state-specific scheme. Try searching with different keywords or abbreviations.

Popular schemes you can explore:
PM-KISAN - Financial assistance for farmers
Ayushman Bharat - Health insurance for families
PMAY - Housing for all
Sukanya Samriddhi - Savings scheme for girl child
MUDRA - Loans for small businesses

How can I help you find the right scheme?"""
