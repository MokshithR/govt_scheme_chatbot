from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Authentication
    path('login/', views.login_page, name='login_page'),
    path('logout/', views.logout_view, name='logout'),
    path('api/auth/login/', views.user_login, name='user_login'),
    
    # Main interface (protected)
    path('', views.home, name='home'),
    
    # Voice and text chat endpoints
    path('voice/', views.voice_api, name='voice_api'),
    path('api/chat/text/', views.text_chat_api, name='text_chat_api'),
    path('api/chat/voice/', views.voice_api, name='voice_chat_api'),
    path('multilingual-voice/', views.multilingual_voice_api, name='multilingual_voice_api'),
    
    # Translation endpoints
    path('api/translate/', views.translate_content_api, name='translate_content_api'),
    path('api/translate/schemes/', views.translate_schemes_batch, name='translate_schemes_batch'),
    path('api/translate/scheme-detail/', views.translate_scheme_detail, name='translate_scheme_detail'),
    
    # Chat history
    path('api/chat/history/<str:session_id>/', views.chat_history_api, name='chat_history_api'),
    
    # Scheme search and information
    path('api/schemes/search/', views.scheme_search_api, name='scheme_search_api'),
    path('api/chat/advanced-search/', views.advanced_search_api, name='advanced_search_api'),
    path('api/vector-search/', views.vector_search_api, name='vector_search_api'),  # Legacy endpoint
    path('api/search/', views.vector_search_api, name='semantic_search_api'),  # NEW: Primary semantic search endpoint
    path('api/schemes/languages/', views.supported_languages_api, name='supported_languages_api'),
    path('api/schemes/sectors/', views.available_sectors_api, name='available_sectors_api'),
    
    # Database status
    path('api/database/status/', views.database_status_api, name='database_status_api'),
    path('api/voice/test/', views.voice_test_api, name='voice_test_api'),

    # Public schemes listing (shows schemes present in database/admin)
    path('schemes/all/', views.schemes_all, name='schemes_all'),
    path('scheme/<int:scheme_id>/', views.scheme_detail, name='scheme_detail'),
    path('test/translation/', views.translation_test, name='translation_test'),
    path('test/microphone/', views.test_microphone, name='test_microphone'),
    
    # Admin helpers (avoid '/admin/' prefix to prevent conflict with Django admin site)
    path('chatbot/admin/generate-details/', views.admin_generate_details, name='admin_generate_details'),
    
    # Semantic Search & Smart Answer APIs (Gemini + pgvector)
    path('api/semantic-search/', views.semantic_search_api, name='semantic_search_api'),
    path('api/smart-answer/', views.smart_answer_api, name='smart_answer_api'),
    
    # NEW: HuggingFace-based Semantic Search & RAG APIs
    path('api/semantic-search-v2/', views.semantic_search_view, name='semantic_search_v2'),
    path('api/smart-answer-v2/', views.smart_answer_view, name='smart_answer_v2'),
    
    # NEW: Scheme Suggestions API (Auto-Complete with Fuzzy Matching)
    path('api/suggestions/', views.scheme_suggestions_view, name='scheme_suggestions'),
    
    # NEW: Smart Query API (Production-ready with correct pipeline order)
    path('api/query/', views.smart_query_api, name='smart_query'),
    
    # User Authentication APIs
    path('api/auth/register/', views.user_register, name='user_register'),
    path('api/auth/login/', views.user_login, name='user_login'),
    path('api/auth/logout/', views.user_logout, name='user_logout'),
    path('api/auth/profile/', views.user_profile, name='user_profile'),
    path('api/auth/profile/update/', views.update_profile, name='update_profile'),
    path('api/auth/notifications/', views.user_notifications, name='user_notifications'),
    path('api/auth/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/auth/status/', views.check_auth_status, name='check_auth_status'),
]