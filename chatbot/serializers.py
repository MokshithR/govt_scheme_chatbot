"""
Django REST Framework Serializers for Semantic Search and Smart Answer APIs

These serializers handle:
1. Input validation for API requests
2. Output formatting for API responses
3. Data transformation between models and JSON
"""

from rest_framework import serializers
from chatbot.models import GovernmentScheme


class SemanticSearchRequestSerializer(serializers.Serializer):
    """
    Serializer for semantic search API request.
    
    Validates the incoming query and optional parameters.
    """
    query = serializers.CharField(
        required=True,
        min_length=3,
        max_length=500,
        help_text="Search query for finding relevant government schemes"
    )
    
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Number of results to return (1-20)"
    )
    
    is_active = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Filter by active schemes only"
    )


class SchemeResultSerializer(serializers.Serializer):
    """
    Serializer for individual scheme search results.
    
    Returns minimal fields for semantic search responses.
    """
    id = serializers.IntegerField(help_text="Scheme ID")
    
    title = serializers.CharField(help_text="Scheme title")
    
    short_description = serializers.CharField(
        allow_blank=True,
        help_text="Brief description of the scheme"
    )
    
    government_level = serializers.CharField(
        allow_blank=True,
        help_text="Government level (central/state/local)"
    )
    
    state = serializers.CharField(
        allow_blank=True,
        help_text="State name (if state-level scheme)"
    )
    
    application_link = serializers.URLField(
        allow_blank=True,
        required=False,
        help_text="URL to apply for the scheme"
    )
    
    website = serializers.URLField(
        allow_blank=True,
        required=False,
        help_text="Official website of the scheme"
    )
    
    distance = serializers.FloatField(
        help_text="Cosine distance from query (lower = more similar)"
    )
    
    similarity_score = serializers.FloatField(
        help_text="Similarity score (0-1 scale, higher = more similar)"
    )


class SemanticSearchResponseSerializer(serializers.Serializer):
    """
    Serializer for semantic search API response.
    
    Returns the list of matching schemes with metadata.
    """
    query = serializers.CharField(help_text="Original search query")
    
    results_count = serializers.IntegerField(help_text="Number of results found")
    
    results = SchemeResultSerializer(many=True, help_text="List of matching schemes")
    
    cached = serializers.BooleanField(
        default=False,
        help_text="Whether results were retrieved from cache"
    )


class SmartAnswerRequestSerializer(serializers.Serializer):
    """
    Serializer for smart answer API request (RAG endpoint).
    
    Validates the user's question and optional parameters.
    """
    query = serializers.CharField(
        required=True,
        min_length=5,
        max_length=1000,
        help_text="User's question about government schemes"
    )
    
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10,
        help_text="Number of schemes to retrieve for context (1-10)"
    )
    
    model = serializers.ChoiceField(
        choices=['gemini-1.5-flash', 'gemini-1.5-pro'],
        required=False,
        default='gemini-1.5-flash',
        help_text="Gemini model to use (flash is faster, pro is more accurate)"
    )
    
    include_ssml = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Include SSML version of the answer for voice output"
    )


class DetailedSchemeSerializer(serializers.Serializer):
    """
    Serializer for detailed scheme information in smart answer response.
    
    Returns more fields than the basic search result.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    short_description = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    government_level = serializers.CharField(allow_blank=True)
    state = serializers.CharField(allow_blank=True)
    ministry = serializers.CharField(allow_blank=True)
    department = serializers.CharField(allow_blank=True)
    eligibility_criteria = serializers.CharField(allow_blank=True)
    benefits = serializers.CharField(allow_blank=True)
    application_link = serializers.URLField(allow_blank=True, required=False)
    website = serializers.URLField(allow_blank=True, required=False)
    similarity_score = serializers.FloatField()


class SmartAnswerResponseSerializer(serializers.Serializer):
    """
    Serializer for smart answer API response (RAG output).
    
    Returns the LLM-generated answer with supporting schemes.
    """
    query = serializers.CharField(help_text="Original user question")
    
    answer = serializers.CharField(help_text="LLM-generated answer using retrieved schemes")
    
    answer_ssml = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="SSML version of the answer for voice synthesis"
    )
    
    schemes_used = DetailedSchemeSerializer(
        many=True,
        help_text="Government schemes used to generate the answer"
    )
    
    schemes_count = serializers.IntegerField(
        help_text="Number of schemes used for context"
    )
    
    model_used = serializers.CharField(help_text="Gemini model used for generation")
    
    cached = serializers.BooleanField(
        default=False,
        help_text="Whether response was retrieved from cache"
    )


class ErrorResponseSerializer(serializers.Serializer):
    """
    Standard error response serializer.
    """
    error = serializers.CharField(help_text="Error message")
    
    error_code = serializers.CharField(
        required=False,
        help_text="Machine-readable error code"
    )
    
    details = serializers.DictField(
        required=False,
        help_text="Additional error details"
    )


# ============================================================
# SUGGESTION API SERIALIZERS (NEW)
# ============================================================

class SchemeSuggestionSerializer(serializers.Serializer):
    """
    Serializer for scheme auto-complete suggestions.
    
    Used by /api/suggestions/ endpoint to return scheme titles for dropdown.
    Supports fuzzy matching and prefix matching for typo tolerance.
    """
    id = serializers.IntegerField(
        read_only=True,
        help_text="Scheme ID"
    )
    
    title = serializers.CharField(
        max_length=500,
        help_text="Scheme title (e.g., 'Pradhan Mantri Kisan Samman Nidhi')"
    )
    
    score = serializers.FloatField(
        read_only=True,
        required=False,
        help_text="Match score (0-100, higher is better)"
    )
    
    match_type = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Match type: 'prefix' (exact start) or 'fuzzy' (typo-tolerant)"
    )
    
    class Meta:
        fields = ['id', 'title', 'score', 'match_type']


class SuggestionRequestSerializer(serializers.Serializer):
    """
    Serializer for suggestion API request.
    
    Validates partial text input for auto-complete.
    """
    partial_text = serializers.CharField(
        required=True,
        min_length=2,
        max_length=200,
        help_text="Partial text typed by user (minimum 2 characters)"
    )
    
    max_suggestions = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=20,
        help_text="Maximum number of suggestions to return (default 10)"
    )

