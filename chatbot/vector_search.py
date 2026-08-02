"""
Vector Similarity Search for Government Schemes

This module provides functions for performing semantic search on government schemes
using PostgreSQL's pgvector extension. It uses cosine distance to find the most
similar schemes based on their embedding vectors.

How pgvector similarity search works:
1. Each scheme has a 768-dimensional embedding vector stored in the database
2. When a user searches, their query is converted to a similar embedding vector
3. pgvector's <-> operator calculates cosine distance between vectors
4. Lower distance = more similar content (0 = identical, 2 = opposite)
5. Results are sorted by distance to find the most relevant schemes

The <-> operator is optimized by pgvector's HNSW or IVFFlat indexes for fast search.
"""

from django.db import connection
from chatbot.models import GovernmentScheme
import logging
import re

logger = logging.getLogger(__name__)


def boost_title_match(query, scheme_title):
    """
    ============================================================
    IMPROVEMENT #3: Boost Title Match in Vector Search
    ============================================================
    
    Manually boost schemes whose titles closely match the query.
    This overrides weak embedding similarity when title is a clear match.
    
    Returns a manual distance score if title matches query:
    - 0.0 if exact match (highest priority)
    - 0.05 if strong partial match (very high priority)
    - None if no match (use embedding distance)
    
    Args:
        query (str): User's search query
        scheme_title (str): Scheme title from database
    
    Returns:
        float or None: Manual distance score, or None to use embedding distance
    
    Examples:
        >>> boost_title_match("PM Kisan", "PM-KISAN Samman Nidhi")
        0.05
        >>> boost_title_match("random query", "Some Scheme")
        None
    """
    if not query or not scheme_title:
        return None
    
    # Normalize both strings for comparison
    query_norm = query.lower().strip()
    title_norm = scheme_title.lower().strip()
    
    # Remove special characters for comparison
    query_clean = re.sub(r'[^a-z0-9\s]', ' ', query_norm)
    title_clean = re.sub(r'[^a-z0-9\s]', ' ', title_norm)
    
    query_clean = ' '.join(query_clean.split())
    title_clean = ' '.join(title_clean.split())
    
    # Exact match → distance 0.0 (perfect)
    if query_clean == title_clean:
        return 0.0
    
    # Strong partial match → distance 0.05 (very high priority)
    # Check if query is substantially in title or vice versa
    if query_clean in title_clean or title_clean in query_clean:
        return 0.05
    
    # Check word-level matching (80% threshold)
    query_words = set(query_clean.split())
    title_words = set(title_clean.split())
    
    if len(query_words) > 0:
        matching_words = query_words.intersection(title_words)
        match_ratio = len(matching_words) / len(query_words)
        
        # If 80% or more of query words match, boost it
        if match_ratio >= 0.8:
            return 0.05
    
    # No title match - use embedding distance
    return None


def search_similar_schemes(query_embedding, top_k=5, filters=None):
    """
    Search for schemes similar to the query embedding using pgvector cosine distance.
    
    This function performs a vector similarity search using PostgreSQL's pgvector
    extension. It finds schemes whose embeddings are closest to the query embedding
    in the 768-dimensional vector space.
    
    How the search works:
    - The <-> operator calculates cosine distance between two vectors
    - Distance ranges from 0 (identical) to 2 (completely opposite)
    - Results are ordered by distance (ascending) to get most similar first
    - LIMIT clause restricts results to top_k most similar schemes
    
    Args:
        query_embedding (list): 768-dimensional embedding vector as a Python list
        top_k (int): Number of top results to return (default: 5)
        filters (dict): Optional filters to apply, e.g., {'is_active': True, 'state': 'Karnataka'}
    
    Returns:
        list: List of dictionaries containing:
            - id (int): Scheme ID
            - title (str): Scheme title
            - short_description (str): Brief description
            - sector (str): Sector name (if available)
            - distance (float): Cosine distance from query (lower = more similar)
            - similarity_score (float): Similarity percentage (0-100, higher = more similar)
            - scheme_object (GovernmentScheme): Full Django model instance
    
    Raises:
        ValueError: If query_embedding is None or has invalid dimensions
        Exception: If database query fails
    
    Example:
        >>> from chatbot.embedding_utils import create_query_embedding
        >>> query_emb = create_query_embedding("farming schemes")
        >>> results = search_similar_schemes(query_emb, top_k=5)
        >>> for result in results:
        ...     print(f"{result['title']} - Similarity: {result['similarity_score']:.1f}%")
    """
    # Safety check: validate query embedding
    if query_embedding is None:
        logger.error("query_embedding is None")
        raise ValueError("query_embedding cannot be None")
    
    if not isinstance(query_embedding, list):
        logger.error(f"query_embedding is not a list: {type(query_embedding)}")
        raise ValueError("query_embedding must be a list of floats")
    
    if len(query_embedding) != 768:
        logger.error(f"Invalid embedding dimension: {len(query_embedding)}, expected 768")
        raise ValueError(f"query_embedding must have 768 dimensions, got {len(query_embedding)}")
    
    # Check if all values are numeric
    try:
        for val in query_embedding:
            float(val)
    except (TypeError, ValueError) as e:
        logger.error(f"query_embedding contains non-numeric values: {e}")
        raise ValueError("query_embedding must contain only numeric values")
    
    # Validate top_k parameter
    if not isinstance(top_k, int) or top_k < 1:
        logger.warning(f"Invalid top_k: {top_k}, using default of 5")
        top_k = 5
    
    # Limit top_k to reasonable maximum to prevent resource exhaustion
    if top_k > 100:
        logger.warning(f"top_k {top_k} exceeds maximum, limiting to 100")
        top_k = 100
    
    # Convert Python list to PostgreSQL vector format: [0.1, 0.2, ...] -> '[0.1,0.2,...]'
    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Build the SQL query
    # The <-> operator computes cosine distance between two vectors
    # We select the distance as a separate column for transparency
    sql = """
        SELECT 
            id,
            title,
            short_description,
            description,
            sector_id,
            ministry,
            department,
            state,
            government_level,
            eligibility_criteria,
            benefits,
            application_link,
            is_active,
            (embedding <-> %s::vector) AS distance
        FROM scheme
        WHERE embedding IS NOT NULL
    """
    
    params = [vector_str]
    
    # Apply optional filters
    # Filters allow narrowing results by scheme properties (e.g., only active schemes)
    if filters:
        if 'is_active' in filters:
            sql += " AND is_active = %s"
            params.append(filters['is_active'])
        
        if 'state' in filters and filters['state']:
            sql += " AND state = %s"
            params.append(filters['state'])
        
        if 'government_level' in filters and filters['government_level']:
            sql += " AND government_level = %s"
            params.append(filters['government_level'])
        
        if 'sector_id' in filters and filters['sector_id']:
            sql += " AND sector_id = %s"
            params.append(filters['sector_id'])
    
    # Order by distance (ascending) to get most similar results first
    # The <-> operator is used again in ORDER BY for sorting
    # pgvector's index makes this operation very fast even with millions of vectors
    sql += """
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """
    
    params.append(vector_str)
    params.append(top_k)
    
    results = []
    
    try:
        # Execute raw SQL query using Django's database connection
        with connection.cursor() as cursor:
            logger.info(f"Executing vector search with top_k={top_k}, filters={filters}")
            cursor.execute(sql, params)
            
            # Fetch all matching rows
            rows = cursor.fetchall()
            
            # Get column names for mapping
            columns = [col[0] for col in cursor.description]
            
            logger.info(f"Vector search returned {len(rows)} results")
            
            # Convert database rows to structured dictionaries
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # ============================================================
                # IMPROVEMENT #3: Apply Title Boost
                # ============================================================
                # Check if title matches query - if yes, override embedding distance
                distance = row_dict['distance']
                
                # Get query from embedding (not directly available, so we skip for now)
                # The title boost will be applied at a higher level in the views
                # For now, we keep the embedding distance
                
                # Calculate similarity score from distance
                # Cosine distance ranges from 0 to 2
                # Convert to percentage: 0 distance = 100% similar, 2 distance = 0% similar
                similarity_score = max(0, (1 - distance / 2) * 100)
                
                # Fetch the full Scheme object for additional data
                try:
                    scheme = GovernmentScheme.objects.select_related('sector').get(id=row_dict['id'])
                except GovernmentScheme.DoesNotExist:
                    logger.warning(f"Scheme {row_dict['id']} not found in Django ORM")
                    scheme = None
                
                result = {
                    'id': row_dict['id'],
                    'title': row_dict['title'],
                    'short_description': row_dict['short_description'] or '',
                    'description': row_dict['description'] or '',
                    'sector': scheme.sector.name if scheme and scheme.sector else 'Unknown',
                    'sector_id': row_dict['sector_id'],
                    'ministry': row_dict['ministry'] or '',
                    'department': row_dict['department'] or '',
                    'state': row_dict['state'] or '',
                    'government_level': row_dict['government_level'] or '',
                    'eligibility_criteria': row_dict['eligibility_criteria'] or '',
                    'benefits': row_dict['benefits'] or '',
                    'application_link': row_dict['application_link'] or '',
                    'is_active': row_dict['is_active'],
                    'distance': float(distance),
                    'similarity_score': round(similarity_score, 2),
                    'scheme_object': scheme,
                }
                
                results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise


def get_scheme_embedding(scheme_id):
    """
    Retrieve the embedding vector for a specific scheme.
    
    Args:
        scheme_id (int): ID of the scheme
    
    Returns:
        list: 768-dimensional embedding vector, or None if not found
    
    Example:
        >>> embedding = get_scheme_embedding(42)
        >>> len(embedding)
        768
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT embedding FROM scheme WHERE id = %s AND embedding IS NOT NULL",
                [scheme_id]
            )
            row = cursor.fetchone()
            
            if row and row[0]:
                # pgvector returns the vector as a string like '[0.1,0.2,...]'
                # Convert to Python list
                vector_str = row[0]
                if isinstance(vector_str, str):
                    # Remove brackets and split by comma
                    vector_str = vector_str.strip('[]')
                    embedding = [float(x) for x in vector_str.split(',')]
                    return embedding
                return row[0]  # Already a list
            
            return None
            
    except Exception as e:
        logger.error(f"Failed to get embedding for scheme {scheme_id}: {e}")
        return None


def count_schemes_with_embeddings():
    """
    Count how many schemes have embeddings stored.
    
    Returns:
        dict: Dictionary with counts:
            - total: Total number of schemes
            - with_embeddings: Schemes that have embeddings
            - without_embeddings: Schemes without embeddings
    
    Example:
        >>> stats = count_schemes_with_embeddings()
        >>> print(f"{stats['with_embeddings']} out of {stats['total']} schemes have embeddings")
    """
    try:
        with connection.cursor() as cursor:
            # Count total schemes
            cursor.execute("SELECT COUNT(*) FROM scheme")
            total = cursor.fetchone()[0]
            
            # Count schemes with embeddings
            cursor.execute("SELECT COUNT(*) FROM scheme WHERE embedding IS NOT NULL")
            with_embeddings = cursor.fetchone()[0]
            
            without_embeddings = total - with_embeddings
            
            return {
                'total': total,
                'with_embeddings': with_embeddings,
                'without_embeddings': without_embeddings,
            }
            
    except Exception as e:
        logger.error(f"Failed to count embeddings: {e}")
        return {
            'total': 0,
            'with_embeddings': 0,
            'without_embeddings': 0,
        }


def find_similar_to_scheme(scheme_id, top_k=5):
    """
    Find schemes similar to a given scheme using its embedding.
    
    This is useful for "you may also be interested in" recommendations.
    
    Args:
        scheme_id (int): ID of the source scheme
        top_k (int): Number of similar schemes to return
    
    Returns:
        list: List of similar schemes (excluding the source scheme itself)
    
    Example:
        >>> similar = find_similar_to_scheme(42, top_k=5)
        >>> for scheme in similar:
        ...     print(f"Similar: {scheme['title']} ({scheme['similarity_score']:.1f}%)")
    """
    # Get the embedding for the source scheme
    embedding = get_scheme_embedding(scheme_id)
    
    if embedding is None:
        logger.warning(f"Scheme {scheme_id} has no embedding")
        return []
    
    # Search for similar schemes (will include the source scheme)
    results = search_similar_schemes(embedding, top_k=top_k + 1)
    
    # Filter out the source scheme itself
    filtered_results = [r for r in results if r['id'] != scheme_id]
    
    # Return only top_k results
    return filtered_results[:top_k]
