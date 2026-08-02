"""
Django Middleware for Chatbot Query Logging
Logs all incoming queries to semantic search and smart answer endpoints
"""

import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ChatbotQueryLoggerMiddleware(MiddlewareMixin):
    """
    Middleware to log all chatbot API requests
    Tracks query, endpoint, response time, and status
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._chatbot_start_time = time.time()
        
        # Log incoming chatbot queries
        if request.path in ['/api/semantic-search-v2/', '/api/smart-answer-v2/']:
            if request.method == 'POST':
                try:
                    import json
                    body = json.loads(request.body)
                    query = body.get('query', 'N/A')
                    
                    logger.info(f"""
╔════════════════════════════════════════════════════════════
║ CHATBOT QUERY INCOMING
╠════════════════════════════════════════════════════════════
║ Endpoint: {request.path}
║ Query: {query}
║ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
╚════════════════════════════════════════════════════════════
""")
                except Exception as e:
                    logger.warning(f"Could not parse request body: {e}")
        
        return None
    
    def process_response(self, request, response):
        """Log response time and status"""
        if hasattr(request, '_chatbot_start_time'):
            if request.path in ['/api/semantic-search-v2/', '/api/smart-answer-v2/']:
                elapsed = time.time() - request._chatbot_start_time
                
                # Color code by response time
                if elapsed < 1.0:
                    time_status = "FAST ✓"
                elif elapsed < 3.0:
                    time_status = "OK"
                else:
                    time_status = "SLOW ⚠"
                
                logger.info(f"""
╔════════════════════════════════════════════════════════════
║ CHATBOT RESPONSE SENT
╠════════════════════════════════════════════════════════════
║ Endpoint: {request.path}
║ Status: {response.status_code}
║ Response Time: {elapsed:.2f}s ({time_status})
╚════════════════════════════════════════════════════════════
""")
        
        return response
