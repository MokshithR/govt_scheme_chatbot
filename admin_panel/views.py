"""
Admin panel views for managing government schemes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from chatbot.models import AdminUser
from django.contrib.auth.models import User
from chatbot.models import GovernmentScheme, WebScrapingLog, Sector
from chatbot.web_scraper import scraper
import json
import logging

logger = logging.getLogger(__name__)


def admin_login(request):
    """
    Admin login view
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'adminuser'):
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'admin_panel/login.html')


def user_login(request):
    """Simple site user login view (non-admin)."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'user/login.html')


def admin_logout(request):
    """
    Admin logout view
    """
    logout(request)
    return redirect('admin_login')


@login_required
def admin_dashboard(request):
    """
    Admin dashboard
    """
    try:
        admin_user = request.user.adminuser
        
        # Get statistics
        total_schemes = GovernmentScheme.objects.count()
        active_schemes = GovernmentScheme.objects.filter(is_active=True).count()
        recent_scraping = WebScrapingLog.objects.order_by('-started_at').first()
        
        # Get recent schemes
        recent_schemes = GovernmentScheme.objects.order_by('-created_at')[:10]

        # Get current active schemes (most recently updated)
        active_schemes_list = GovernmentScheme.objects.filter(is_active=True).order_by('-last_updated')[:20]
        
        # Get scraping logs
        scraping_logs = WebScrapingLog.objects.order_by('-started_at')[:10]
        
        context = {
            'admin_user': admin_user,
            'total_schemes': total_schemes,
            'active_schemes': active_schemes,
            'recent_scraping': recent_scraping,
            'recent_schemes': recent_schemes,
            'active_schemes_list': active_schemes_list,
            'scraping_logs': scraping_logs,
        }
        
        return render(request, 'admin_panel/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in admin_dashboard: {e}")
        messages.error(request, 'An error occurred while loading the dashboard.')
        return redirect('admin_login')


@login_required
def manage_schemes(request):
    """
    Manage government schemes
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_manage_schemes:
            messages.error(request, 'You do not have permission to manage schemes.')
            return redirect('admin_dashboard')
        
        # Get search parameters
        search_query = request.GET.get('search', '')
        sector_filter = request.GET.get('sector', '')
        status_filter = request.GET.get('status', '')
        level_filter = request.GET.get('level', '')
        language_filter = request.GET.get('language', '')
        state_filter = request.GET.get('state', '')
        
        # Build filters
        schemes = GovernmentScheme.objects.all()
        
        if search_query:
            schemes = schemes.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(ministry__icontains=search_query)
            )
        
        if sector_filter:
            schemes = schemes.filter(sector__name=sector_filter)
        if level_filter:
            schemes = schemes.filter(government_level=level_filter)
        if language_filter:
            schemes = schemes.filter(language=language_filter)
        if state_filter:
            schemes = schemes.filter(state__iexact=state_filter)
        
        if status_filter == 'active':
            schemes = schemes.filter(is_active=True)
        elif status_filter == 'inactive':
            schemes = schemes.filter(is_active=False)
        
        # Pagination
        paginator = Paginator(schemes.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Build choices for filters
        sectors = GovernmentScheme.SECTOR_CHOICES
        levels = [('central', 'Central'), ('state', 'State'), ('local', 'Local')]
        languages = GovernmentScheme.LANGUAGE_CHOICES
        states = GovernmentScheme.objects.exclude(state__isnull=True).exclude(state__exact='').values_list('state', flat=True).distinct().order_by('state')
        
        context = {
            'admin_user': admin_user,
            'page_obj': page_obj,
            'sectors': sectors,
            'levels': levels,
            'languages': languages,
            'states': states,
            'search_query': search_query,
            'sector_filter': sector_filter,
            'status_filter': status_filter,
            'level_filter': level_filter,
            'language_filter': language_filter,
            'state_filter': state_filter,
        }
        
        return render(request, 'admin_panel/manage_schemes.html', context)
        
    except Exception as e:
        logger.error(f"Error in manage_schemes: {e}")
        messages.error(request, 'An error occurred while loading schemes.')
        return redirect('admin_dashboard')


@login_required
def add_scheme(request):
    """
    Add new government scheme
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_manage_schemes:
            messages.error(request, 'You do not have permission to manage schemes.')
            return redirect('admin_dashboard')
        
        if request.method == 'POST':
            try:
                # Create new scheme
                # Resolve sector ForeignKey from posted string
                sector_name = request.POST.get('sector', '').strip() or 'other'
                sector_obj, _ = Sector.objects.get_or_create(name=sector_name)

                scheme = GovernmentScheme.objects.create(
                    title=request.POST.get('title'),
                    description=request.POST.get('description'),
                    short_description=request.POST.get('short_description', ''),
                    sector=sector_obj,
                    ministry=request.POST.get('ministry', ''),
                    department=request.POST.get('department', ''),
                    government_level=request.POST.get('government_level', 'central'),
                    state=request.POST.get('state'),
                    eligibility_criteria=request.POST.get('eligibility_criteria', ''),
                    benefits=request.POST.get('benefits', ''),
                    financial_assistance=request.POST.get('financial_assistance'),
                    application_process=request.POST.get('application_process', ''),
                    application_link=request.POST.get('application_link'),
                    launch_date=request.POST.get('launch_date'),
                    last_date=request.POST.get('last_date'),
                    validity_period=request.POST.get('validity_period'),
                    helpline_number=request.POST.get('helpline_number'),
                    email=request.POST.get('email'),
                    website=request.POST.get('website'),
                    source_url=request.POST.get('source_url', ''),
                    language=request.POST.get('language', 'en'),
                    is_active=request.POST.get('is_active') == 'on'
                )
                
                messages.success(request, f'Scheme "{scheme.title}" added successfully.')
                return redirect('manage_schemes')
                
            except Exception as e:
                logger.error(f"Error creating scheme: {e}")
                messages.error(request, f'Error creating scheme: {str(e)}')
        
        context = {
            'admin_user': admin_user,
            'sector_choices': GovernmentScheme.SECTOR_CHOICES,
            'language_choices': GovernmentScheme.LANGUAGE_CHOICES,
        }
        
        return render(request, 'admin_panel/add_scheme.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_scheme: {e}")
        messages.error(request, 'An error occurred while loading the add scheme page.')
        return redirect('admin_dashboard')


@login_required
def edit_scheme(request, scheme_id):
    """
    Edit government scheme
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_manage_schemes:
            messages.error(request, 'You do not have permission to manage schemes.')
            return redirect('admin_dashboard')
        
        scheme = get_object_or_404(GovernmentScheme, id=scheme_id)
        
        if request.method == 'POST':
            try:
                # Update scheme
                scheme.title = request.POST.get('title')
                scheme.description = request.POST.get('description')
                scheme.short_description = request.POST.get('short_description', '')
                # Resolve sector ForeignKey from posted string
                sector_name = request.POST.get('sector', '').strip() or 'other'
                scheme.sector, _ = Sector.objects.get_or_create(name=sector_name)
                scheme.ministry = request.POST.get('ministry', '')
                scheme.department = request.POST.get('department', '')
                scheme.government_level = request.POST.get('government_level', 'central')
                scheme.state = request.POST.get('state')
                scheme.eligibility_criteria = request.POST.get('eligibility_criteria', '')
                scheme.benefits = request.POST.get('benefits', '')
                scheme.financial_assistance = request.POST.get('financial_assistance')
                scheme.application_process = request.POST.get('application_process', '')
                scheme.application_link = request.POST.get('application_link')
                scheme.launch_date = request.POST.get('launch_date')
                scheme.last_date = request.POST.get('last_date')
                scheme.validity_period = request.POST.get('validity_period')
                scheme.helpline_number = request.POST.get('helpline_number')
                scheme.email = request.POST.get('email')
                scheme.website = request.POST.get('website')
                scheme.source_url = request.POST.get('source_url', '')
                scheme.language = request.POST.get('language', 'en')
                scheme.is_active = request.POST.get('is_active') == 'on'
                
                scheme.save()
                
                messages.success(request, f'Scheme "{scheme.title}" updated successfully.')
                return redirect('manage_schemes')
                
            except Exception as e:
                logger.error(f"Error updating scheme: {e}")
                messages.error(request, f'Error updating scheme: {str(e)}')
        
        context = {
            'admin_user': admin_user,
            'scheme': scheme,
            'sector_choices': GovernmentScheme.SECTOR_CHOICES,
            'language_choices': GovernmentScheme.LANGUAGE_CHOICES,
        }
        
        return render(request, 'admin_panel/edit_scheme.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_scheme: {e}")
        messages.error(request, 'An error occurred while loading the edit scheme page.')
        return redirect('admin_dashboard')


@login_required
def delete_scheme(request, scheme_id):
    """
    Delete government scheme
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_manage_schemes:
            messages.error(request, 'You do not have permission to manage schemes.')
            return redirect('admin_dashboard')
        
        scheme = get_object_or_404(GovernmentScheme, id=scheme_id)
        scheme_title = scheme.title
        scheme.delete()
        
        messages.success(request, f'Scheme "{scheme_title}" deleted successfully.')
        return redirect('manage_schemes')
        
    except Exception as e:
        logger.error(f"Error in delete_scheme: {e}")
        messages.error(request, 'An error occurred while deleting the scheme.')
        return redirect('admin_dashboard')


@login_required
def run_scraping(request):
    """
    Run web scraping
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_scrape:
            messages.error(request, 'You do not have permission to run scraping.')
            return redirect('admin_dashboard')
        
        if request.method == 'POST':
            try:
                # Run scraping
                result = scraper.run_full_scraping()
                
                messages.success(request, f'Scraping completed successfully. Added: {result["added_to_db"]}, Updated: {result["updated_in_db"]}')
                return redirect('admin_dashboard')
                
            except Exception as e:
                logger.error(f"Error running scraping: {e}")
                messages.error(request, f'Error running scraping: {str(e)}')
        
        return redirect('admin_dashboard')
        
    except Exception as e:
        logger.error(f"Error in run_scraping: {e}")
        messages.error(request, 'An error occurred while running scraping.')
        return redirect('admin_dashboard')


@login_required
def run_scraping_async(request):
    """Trigger scraping in background (Celery) or run minimally if Celery not configured."""
    try:
        admin_user = request.user.adminuser
        if not admin_user.can_scrape:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        # Try to enqueue Celery task if available
        try:
            from admin_panel.tasks import run_scraping_task
            task = run_scraping_task.delay()
            return JsonResponse({'success': True, 'task_id': task.id})
        except Exception:
            # Fallback: run synchronously but return quickly
            result = scraper.run_full_scraping()
            return JsonResponse({'success': True, 'result': result})

    except Exception as e:
        logger.error(f"Error in run_scraping_async: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def dry_run_preview(request):
    """Preview parsed schemes without saving to DB."""
    try:
        admin_user = request.user.adminuser
        if not admin_user.can_manage_schemes:
            messages.error(request, 'You do not have permission to preview schemes.')
            return redirect('admin_dashboard')

        # Run scrapers but do not save — limit results
        central = scraper.scrape_central_government_sites()
        state = scraper.scrape_state_government_sites()
        combined = (central or []) + (state or [])
        combined = combined[:80]

        return render(request, 'admin_panel/dry_run_preview.html', {'schemes': combined})

    except Exception as e:
        logger.error(f"Error in dry_run_preview: {e}")
        messages.error(request, 'An error occurred during dry-run.')
        return redirect('admin_dashboard')


@login_required
def scraping_logs(request):
    """
    View scraping logs
    """
    try:
        admin_user = request.user.adminuser
        
        if not admin_user.can_scrape:
            messages.error(request, 'You do not have permission to view scraping logs.')
            return redirect('admin_dashboard')
        
        # Get scraping logs
        logs = WebScrapingLog.objects.order_by('-started_at')
        
        # Pagination
        paginator = Paginator(logs, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'admin_user': admin_user,
            'page_obj': page_obj,
        }
        
        return render(request, 'admin_panel/scraping_logs.html', context)
        
    except Exception as e:
        logger.error(f"Error in scraping_logs: {e}")
        messages.error(request, 'An error occurred while loading scraping logs.')
        return redirect('admin_dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_scheme_stats(request):
    """
    API endpoint for scheme statistics
    """
    try:
        admin_user = request.user.adminuser
        
        # Get statistics
        total_schemes = GovernmentScheme.objects.count()
        active_schemes = GovernmentScheme.objects.filter(is_active=True).count()
        inactive_schemes = GovernmentScheme.objects.filter(is_active=False).count()
        
        # Get sector-wise counts
        sector_counts = {}
        for sector, _ in GovernmentScheme.SECTOR_CHOICES:
            count = GovernmentScheme.objects.filter(sector=sector).count()
            if count > 0:
                sector_counts[sector] = count
        
        # Get language-wise counts
        language_counts = {}
        for language, _ in GovernmentScheme.LANGUAGE_CHOICES:
            count = GovernmentScheme.objects.filter(language=language).count()
            if count > 0:
                language_counts[language] = count
        
        return Response({
            'success': True,
            'stats': {
                'total_schemes': total_schemes,
                'active_schemes': active_schemes,
                'inactive_schemes': inactive_schemes,
                'sector_counts': sector_counts,
                'language_counts': language_counts,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in api_scheme_stats: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)