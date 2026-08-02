"""
Debug Logging Utilities for AI Chatbot
Provides color-coded logging for:
1. Semantic search distances
2. Fallback triggers (greeting/threshold)
3. RAG prompts sent to Gemini
4. Cache hit/miss events
"""

import logging
from colorama import Fore, Back, Style, init

# Initialize colorama for Windows support
init(autoreset=True)

logger = logging.getLogger(__name__)


def log_search_distances(query, results):
    """
    Log semantic search results with color-coded distances
    
    Args:
        query: User query string
        results: List of search results with 'distance' field
    
    Color coding:
        Green (<0.3): Excellent match
        Yellow (0.3-0.55): Good match
        Red (>0.55): Poor match (triggers fallback)
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}SEMANTIC SEARCH RESULTS")
    print(f"{Fore.CYAN}Query: {Fore.WHITE}{query}")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    if not results:
        print(f"{Fore.RED}⚠ No results found (no embeddings in database)")
        return
    
    for i, result in enumerate(results, 1):
        distance = result.get('distance', 999)
        title = result.get('title', 'Unknown')
        
        # Color code by distance
        if distance < 0.3:
            color = Fore.GREEN
            status = "EXCELLENT ✓✓"
        elif distance <= 0.55:
            color = Fore.YELLOW
            status = "GOOD ✓"
        else:
            color = Fore.RED
            status = "POOR ✗ (FILTERED OUT)"
        
        print(f"{color}[{i}] Distance: {distance:.4f} ({status})")
        print(f"    Title: {title[:80]}")
        print()
    
    print(f"{Fore.CYAN}{'='*70}\n")


def log_fallback_trigger(trigger_type, query, details=None):
    """
    Log when fallback response is triggered
    
    Args:
        trigger_type: 'greeting' or 'threshold'
        query: User query string
        details: Optional dict with additional context
    """
    print(f"\n{Back.YELLOW}{Fore.BLACK}{'='*70}")
    print(f"{Back.YELLOW}{Fore.BLACK} FALLBACK TRIGGERED ")
    print(f"{Back.YELLOW}{Fore.BLACK}{'='*70}{Style.RESET_ALL}")
    
    print(f"{Fore.YELLOW}Type: {trigger_type.upper()}")
    print(f"{Fore.YELLOW}Query: {query}")
    
    if trigger_type == 'greeting':
        print(f"{Fore.YELLOW}Action: Returning greeting response (no DB search)")
        print(f"{Fore.YELLOW}Response Time: <100ms (instant)")
    
    elif trigger_type == 'threshold':
        print(f"{Fore.YELLOW}Action: No good matches (all distances > 0.55)")
        print(f"{Fore.YELLOW}Response: NO_RESULTS_MESSAGE")
        if details and 'best_distance' in details:
            print(f"{Fore.YELLOW}Best Distance: {details['best_distance']:.4f}")
    
    print(f"{Fore.YELLOW}{'='*70}\n")


def log_rag_prompt(query, schemes_text, prompt_template):
    """
    Log the exact prompt sent to Gemini for RAG
    
    Args:
        query: User query
        schemes_text: Context text with scheme details
        prompt_template: The full prompt template used
    """
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}RAG PROMPT SENT TO GEMINI")
    print(f"{Fore.MAGENTA}{'='*70}\n")
    
    print(f"{Fore.MAGENTA}User Query:")
    print(f"{Fore.WHITE}{query}\n")
    
    print(f"{Fore.MAGENTA}Schemes Context (first 500 chars):")
    print(f"{Fore.WHITE}{schemes_text[:500]}...")
    print(f"{Fore.MAGENTA}[Total context length: {len(schemes_text)} chars]\n")
    
    full_prompt = prompt_template.format(query=query, schemes_text=schemes_text)
    print(f"{Fore.MAGENTA}Full Prompt (first 500 chars):")
    print(f"{Fore.WHITE}{full_prompt[:500]}...")
    print(f"{Fore.MAGENTA}[Total prompt length: {len(full_prompt)} chars]\n")
    
    print(f"{Fore.MAGENTA}{'='*70}\n")


def log_cache_event(event_type, key, hit_or_miss=None):
    """
    Log Redis cache hit/miss events
    
    Args:
        event_type: 'hit', 'miss', or 'set'
        key: Cache key (will be truncated to first 50 chars)
        hit_or_miss: Optional boolean for legacy support
    """
    if hit_or_miss is not None:
        event_type = 'hit' if hit_or_miss else 'miss'
    
    key_short = key[:50] + '...' if len(key) > 50 else key
    
    if event_type == 'hit':
        print(f"{Fore.GREEN}🗄 CACHE HIT: {key_short}")
    elif event_type == 'miss':
        print(f"{Fore.CYAN}🔍 CACHE MISS: {key_short} (generating fresh response)")
    elif event_type == 'set':
        print(f"{Fore.BLUE}💾 CACHE SET: {key_short} (TTL: 12 hours)")
    
    print()


def log_embedding_generation(text, embedding_length):
    """
    Log embedding generation events
    
    Args:
        text: Text being embedded (will be truncated)
        embedding_length: Length of generated embedding vector
    """
    text_short = text[:100] + '...' if len(text) > 100 else text
    
    print(f"{Fore.CYAN}🧮 EMBEDDING GENERATED")
    print(f"{Fore.CYAN}Text: {Fore.WHITE}{text_short}")
    print(f"{Fore.CYAN}Dimensions: {Fore.WHITE}{embedding_length}")
    
    if embedding_length != 768:
        print(f"{Fore.RED}⚠ WARNING: Expected 768 dimensions, got {embedding_length}")
    else:
        print(f"{Fore.GREEN}✓ Dimensions OK")
    
    print()


def log_error(error_type, error_message, context=None):
    """
    Log errors with context
    
    Args:
        error_type: Type of error (e.g., 'embedding', 'search', 'gemini')
        error_message: Error message string
        context: Optional dict with additional context
    """
    print(f"\n{Back.RED}{Fore.WHITE}{'='*70}")
    print(f"{Back.RED}{Fore.WHITE} ERROR ")
    print(f"{Back.RED}{Fore.WHITE}{'='*70}{Style.RESET_ALL}")
    
    print(f"{Fore.RED}Type: {error_type}")
    print(f"{Fore.RED}Message: {error_message}")
    
    if context:
        print(f"{Fore.RED}Context:")
        for key, value in context.items():
            print(f"{Fore.RED}  - {key}: {value}")
    
    print(f"{Fore.RED}{'='*70}\n")


def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}TEST: {test_name}")
    print(f"{Fore.CYAN}{'='*70}\n")


def print_test_result(passed, message):
    """Print test result with color coding"""
    if passed:
        print(f"{Fore.GREEN}✓ PASSED: {message}\n")
    else:
        print(f"{Fore.RED}✗ FAILED: {message}\n")
