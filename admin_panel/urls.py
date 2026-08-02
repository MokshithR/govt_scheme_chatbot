"""
URL configuration for admin panel
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Scheme management
    path('schemes/', views.manage_schemes, name='manage_schemes'),
    path('schemes/add/', views.add_scheme, name='add_scheme'),
    path('schemes/<str:scheme_id>/edit/', views.edit_scheme, name='edit_scheme'),
    path('schemes/<str:scheme_id>/delete/', views.delete_scheme, name='delete_scheme'),
    
    # Scraping
    path('scraping/run/', views.run_scraping, name='run_scraping'),
    path('scraping/logs/', views.scraping_logs, name='scraping_logs'),
    path('scraping/run-async/', views.run_scraping_async, name='run_scraping_async'),
    path('scraping/dry-run/', views.dry_run_preview, name='scraping_dry_run'),
    # User-facing login
    path('user/login/', views.user_login, name='user_login'),
    
    # API endpoints
    path('api/stats/', views.api_scheme_stats, name='api_scheme_stats'),
]
