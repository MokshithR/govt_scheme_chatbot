"""
Embedding Utilities for Government Schemes Chatbot

This module provides functions for generating embeddings using HuggingFace's
sentence-transformers model. These embeddings are used for semantic search
with PostgreSQL pgvector.

Model: sentence-transformers/all-mpnet-base-v2
- Embedding dimension: 768
- Best for semantic search and similarity tasks
- Optimized for English text
"""

from sentence_transformers import SentenceTransformer
import logging
import json

logger = logging.getLogger(__name__)

# Load the pre-trained sentence transformer model
# This model converts text into 768-dimensional vectors
# Model is loaded once when the module is imported (singleton pattern)
try:
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    logger.info("Successfully loaded sentence-transformers model: all-mpnet-base-v2")
except Exception as e:
    logger.error(f"Failed to load sentence-transformers model: {e}")
    model = None


def clean_text(text):
    """
    Clean and normalize text for embedding generation.
    
    Args:
        text: Input text (can be None, string, or other types)
    
    Returns:
        str: Cleaned text string, or empty string if input is None/invalid
    
    Examples:
        >>> clean_text(None)
        ''
        >>> clean_text("  Hello World  ")
        'Hello World'
        >>> clean_text(123)
        '123'
    """
    if text is None:
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Remove null bytes and excessive whitespace
    text = text.replace('\x00', '')
    text = ' '.join(text.split())
    
    return text


def normalize_text(text):
    """
    Normalize text for exact/partial title matching.
    Used for smart scheme name detection before embedding search.
    
    Normalization steps:
    - Convert to lowercase
    - Remove special characters and punctuation
    - Replace multiple spaces with single space
    - Strip leading/trailing whitespace
    
    Args:
        text (str): Input text to normalize
    
    Returns:
        str: Normalized text for comparison
    
    Examples:
        >>> normalize_text("PM-KISAN Samman Nidhi (Scheme)")
        'pm kisan samman nidhi scheme'
        >>> normalize_text("  Agriculture   Loan  ")
        'agriculture loan'
    """
    if not text:
        return ""
    
    import re
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters, keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    
    return text.strip()


def prepare_embedding_text(scheme):
    """
    Prepare comprehensive text from a Scheme object for embedding generation.
    
    This function combines all relevant scheme fields into a single text string
    that will be used to generate the embedding vector. Fields are weighted by
    importance (title appears twice to increase its significance).
    
    Args:
        scheme: Django Scheme model instance with the following attributes:
            - title (str): Scheme name
            - short_description (str): Brief summary
            - description (str): Detailed description
            - eligibility (str): Who can apply
            - benefits (str): What applicants receive
            - eligibility_criteria (str): Specific requirements
            - financial_assistance (str): Financial benefits
            - application_process (str): How to apply
            - ministry (str): Government ministry
            - department (str): Department name
            - state (str): State/region
            - keywords (JSONB array): Search keywords
            - search_tags (JSONB array): Additional tags
    
    Returns:
        str: Combined text ready for embedding generation
    
    Example:
        >>> scheme = Scheme.objects.get(id=1)
        >>> text = prepare_embedding_text(scheme)
        >>> # Returns: "PM-KISAN PM-KISAN Direct benefit transfer for farmers..."
    """
    # Collect text components
    components = []
    
    # ============================================================
    # IMPROVEMENT #4: Enhanced Title Embedding
    # ============================================================
    # Add title in multiple formats to improve matching:
    # 1. Original title (2x for importance)
    # 2. Title without parentheses/symbols (for abbreviation matching)
    # 3. Lowercase normalized version
    # 4. Common abbreviation expansions
    
    title = clean_text(scheme.title)
    if title:
        # Original title (double weight)
        components.append(title)
        components.append(title)
        
        # Title without parentheses and special symbols
        # "PM-KISAN (Scheme)" → "PM KISAN Scheme"
        import re
        title_clean = re.sub(r'[()\[\]{}]', ' ', title)
        title_clean = ' '.join(title_clean.split())
        components.append(title_clean)
        
        # Lowercase version for better matching
        components.append(title.lower())
        
        # Common abbreviation expansions for popular schemes
        # This helps match queries like "PM Kisan" or "Pradhan Mantri Kisan"
        abbrev_expansions = []
        
        # PM-KISAN expansions
        if 'pm-kisan' in title.lower() or 'pmkisan' in title.lower():
            abbrev_expansions.extend([
                'PM Kisan',
                'PM KISAN',
                'Pradhan Mantri Kisan Samman Nidhi',
                'Prime Minister Kisan'
            ])
        
        # PM-JAY (Ayushman Bharat) expansions
        if 'pm-jay' in title.lower() or 'ayushman' in title.lower():
            abbrev_expansions.extend([
                'PM JAY',
                'Ayushman Bharat',
                'Pradhan Mantri Jan Arogya Yojana'
            ])
        
        # Add other common scheme abbreviations
        if 'nrega' in title.lower() or 'mgnrega' in title.lower():
            abbrev_expansions.extend([
                'NREGA',
                'MGNREGA',
                'Mahatma Gandhi NREGA',
                'Rural Employment Guarantee'
            ])
        
        components.extend(abbrev_expansions)
    
    # Add main description fields
    components.append(clean_text(scheme.short_description))
    components.append(clean_text(scheme.description))
    
    # Add eligibility and benefits information
    components.append(clean_text(scheme.eligibility))
    components.append(clean_text(scheme.benefits))
    components.append(clean_text(scheme.eligibility_criteria))
    components.append(clean_text(scheme.financial_assistance))
    components.append(clean_text(scheme.application_process))
    
    # Add organizational and location metadata
    components.append(clean_text(scheme.ministry))
    components.append(clean_text(scheme.department))
    components.append(clean_text(scheme.state))
    
    # ============================================================
    # IMPROVEMENT #4: Enhanced Keyword/Tag Processing
    # ============================================================
    # Keywords and search_tags are critical for matching
    # Add them prominently in the embedding text
    
    # Process keywords field
    if scheme.keywords:
        try:
            # If keywords is already a Python list
            if isinstance(scheme.keywords, list):
                keywords_text = ' '.join([clean_text(kw) for kw in scheme.keywords])
                components.append(keywords_text)
                # Add keywords again for extra weight
                components.append(keywords_text)
            # If keywords is a JSON string
            elif isinstance(scheme.keywords, str):
                keywords_list = json.loads(scheme.keywords)
                keywords_text = ' '.join([clean_text(kw) for kw in keywords_list])
                components.append(keywords_text)
                # Add keywords again for extra weight
                components.append(keywords_text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse keywords for scheme {scheme.id}: {e}")
    
    # Process search_tags field
    if scheme.search_tags:
        try:
            # If search_tags is already a Python list
            if isinstance(scheme.search_tags, list):
                tags_text = ' '.join([clean_text(tag) for tag in scheme.search_tags])
                components.append(tags_text)
                # Add tags again for extra weight
                components.append(tags_text)
            # If search_tags is a JSON string
            elif isinstance(scheme.search_tags, str):
                tags_list = json.loads(scheme.search_tags)
                tags_text = ' '.join([clean_text(tag) for tag in tags_list])
                components.append(tags_text)
                # Add tags again for extra weight
                components.append(tags_text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse search_tags for scheme {scheme.id}: {e}")
    
    # Combine all components into a single text string
    # Filter out empty strings before joining
    combined_text = ' '.join(filter(None, components))
    
    # Limit total text length to 10,000 characters to prevent excessive processing
    if len(combined_text) > 10000:
        logger.warning(f"Truncating scheme {scheme.id} text from {len(combined_text)} to 10000 chars")
        combined_text = combined_text[:10000]
    
    return combined_text


def create_embedding(text):
    """
    Generate a 768-dimensional embedding vector from text using sentence-transformers.
    
    This function uses the all-mpnet-base-v2 model to convert text into a dense
    vector representation that captures semantic meaning. The resulting vector
    can be stored in PostgreSQL with pgvector and used for similarity search.
    
    Args:
        text (str): Input text to embed
    
    Returns:
        list: 768-dimensional embedding vector as a Python list of floats
              Returns None if embedding generation fails
    
    Raises:
        Exception: If the model is not loaded or embedding generation fails
    
    Example:
        >>> embedding = create_embedding("agriculture scheme for farmers")
        >>> len(embedding)
        768
        >>> isinstance(embedding, list)
        True
        >>> isinstance(embedding[0], float)
        True
    
    Note:
        - The model must be successfully loaded before calling this function
        - Input text should be preprocessed with clean_text() first
        - Returns None if model is not available
    """
    if model is None:
        logger.error("Sentence transformer model is not loaded. Cannot create embedding.")
        return None
    
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding generation")
        return None
    
    try:
        # Generate embedding using the sentence transformer model
        # encode() returns a numpy array, convert to list for JSON serialization
        embedding = model.encode(text, convert_to_tensor=False)
        
        # Convert numpy array to Python list of floats
        embedding_list = embedding.tolist()
        
        # Validate embedding dimensions (should be 768 for all-mpnet-base-v2)
        if len(embedding_list) != 768:
            logger.error(f"Unexpected embedding dimension: {len(embedding_list)}, expected 768")
            return None
        
        logger.info(f"Successfully generated embedding of dimension {len(embedding_list)}")
        return embedding_list
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def exact_title_match(query, scheme_title):
    """
    Check if query exactly or partially matches a scheme title.
    Used for HIGHEST PRIORITY matching before vector search.
    
    Matching algorithm:
    1. Normalize both query and title (lowercase, remove punctuation)
    2. Check for exact match
    3. Check if query is 80% contained in title (partial match)
    4. Check if title is 80% contained in query
    
    Args:
        query (str): User's search query
        scheme_title (str): Scheme title from database
    
    Returns:
        bool: True if match found, False otherwise
    
    Examples:
        >>> exact_title_match("PM Kisan", "PM-KISAN Samman Nidhi Yojana")
        True
        >>> exact_title_match("ayushman bharat", "Ayushman Bharat - PM-JAY")
        True
        >>> exact_title_match("random query", "PM-KISAN")
        False
    """
    if not query or not scheme_title:
        return False
    
    # Normalize both strings
    query_norm = normalize_text(query)
    title_norm = normalize_text(scheme_title)
    
    # Exact match
    if query_norm == title_norm:
        return True
    
    # Check if query is substantially contained in title (80% threshold)
    # This allows "PM Kisan" to match "PM-KISAN Samman Nidhi Yojana"
    if len(query_norm) >= 3:  # Minimum 3 characters
        # Count matching words
        query_words = set(query_norm.split())
        title_words = set(title_norm.split())
        
        if len(query_words) > 0:
            matching_words = query_words.intersection(title_words)
            match_ratio = len(matching_words) / len(query_words)
            
            # If 80% or more of query words are in title, consider it a match
            if match_ratio >= 0.8:
                return True
    
    # Check if title is contained in query (reverse check)
    if len(title_norm) >= 3 and len(title_norm) <= len(query_norm):
        if title_norm in query_norm:
            return True
    
    return False


def validate_embedding(embedding):
    """
    Validate that an embedding has the correct format and dimensions.
    
    Args:
        embedding: The embedding to validate
    
    Returns:
        bool: True if embedding is valid, False otherwise
    
    Example:
        >>> valid_emb = [0.1] * 768
        >>> validate_embedding(valid_emb)
        True
        >>> invalid_emb = [0.1] * 512
        >>> validate_embedding(invalid_emb)
        False
    """
    if embedding is None:
        return False
    
    if not isinstance(embedding, list):
        logger.error(f"Embedding is not a list: {type(embedding)}")
        return False
    
    if len(embedding) != 768:
        logger.error(f"Invalid embedding dimension: {len(embedding)}, expected 768")
        return False
    
    # Check that all values are numeric
    try:
        for val in embedding:
            float(val)
    except (TypeError, ValueError) as e:
        logger.error(f"Embedding contains non-numeric values: {e}")
        return False
    
    return True
