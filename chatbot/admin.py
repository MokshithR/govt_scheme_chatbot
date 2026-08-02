from django.contrib import admin
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
import subprocess
from .models import (
    GovernmentScheme,
    ChatSession,
    ChatMessage,
    WebScrapingLog,
    AdminUser,
    UserProfile,
    UserSchemeInteraction,
    UserSearchHistory,
    UserNotification,
    ScrapedScheme,
)

@admin.register(GovernmentScheme)
class GovernmentSchemeAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'sector', 'government_level', 'state', 'language', 'is_active', 'created_at'
    )
    list_filter = ('sector', 'government_level', 'language', 'is_active', 'state')
    search_fields = ('title', 'description', 'ministry', 'department', 'source_url')
    date_hierarchy = 'created_at'
    # Autofill via Gemini removed: buttons and admin endpoint were causing issues.
    # If you want to re-enable in future, re-add a Media JS and a secure admin view here.


@admin.register(WebScrapingLog)
class WebScrapingLogAdmin(admin.ModelAdmin):
    list_display = ('source_name', 'status', 'schemes_found', 'schemes_added', 'schemes_updated', 'started_at', 'completed_at')
    list_filter = ('status', 'source_name')
    search_fields = ('source_name', 'error_message')
    date_hierarchy = 'started_at'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'language', 'created_at', 'last_activity', 'is_active')
    list_filter = ('language', 'is_active')
    search_fields = ('session_id',)
    date_hierarchy = 'created_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'language', 'timestamp')
    list_filter = ('message_type', 'language')
    search_fields = ('text_content',)
    date_hierarchy = 'timestamp'


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'can_scrape', 'can_manage_schemes', 'can_manage_users', 'created_at', 'last_login')
    list_filter = ('role', 'can_scrape', 'can_manage_schemes', 'can_manage_users')
    search_fields = ('user__username', 'user__email')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_language', 'state', 'is_verified', 'created_at')
    list_filter = ('preferred_language', 'state', 'is_verified')
    search_fields = ('user__username', 'user__email', 'state', 'district', 'pincode')


@admin.register(UserSchemeInteraction)
class UserSchemeInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'scheme_id', 'interaction_type', 'created_at')
    list_filter = ('interaction_type',)
    search_fields = ('user__username', 'scheme_id')
    date_hierarchy = 'created_at'


@admin.register(UserSearchHistory)
class UserSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'language', 'results_count', 'created_at')
    list_filter = ('language',)
    search_fields = ('user__username', 'query')
    date_hierarchy = 'created_at'


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title', 'message')
    date_hierarchy = 'created_at'


@admin.register(ScrapedScheme)
class ScrapedSchemeAdmin(admin.ModelAdmin):
    """
    Admin interface for ScrapedScheme model
    Shows scraped schemes from MyScheme.gov.in with custom scrape button
    """
    
    list_display = ('title', 'url', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'url')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    # Show 50 schemes per page
    list_per_page = 50
    
    def get_urls(self):
        """Add custom URL for scrape button"""
        urls = super().get_urls()
        custom = [
            path('scrape-myscheme/', self.scrape_myscheme)
        ]
        return custom + urls
    
    def scrape_myscheme(self, request):
        """
        Custom admin view to trigger Selenium scraping
        Opens visible Chromium and scrapes MyScheme.gov.in
        """
        subprocess.call(["python", "manage.py", "scrape_myscheme"])
        return HttpResponse("<h2>Scraping Completed!</h2><p>Check ScrapedScheme table.</p>")
    
    def changelist_view(self, request, extra_context=None):
        """
        Override to inject custom scrape button in admin toolbar
        """
        extra_context = extra_context or {}
        
        # Create blue scrape button HTML
        extra_context['scrape_button_html'] = format_html(
            '<a href="scrape-myscheme/" class="button" style="padding: 8px 12px; '
            'background: #0f62fe; color: white; border-radius: 4px; text-decoration: none;">'
            '🚀 Scrape MyScheme (Live)</a>'
        )
        
        return super().changelist_view(request, extra_context=extra_context)

