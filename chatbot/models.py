from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

# 🛠️ FIX: ADD THE MISSING SECTOR MODEL
class Sector(models.Model):
    """Model for storing scheme sectors"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sector'  # Match your existing PostgreSQL table
        ordering = ['name']

    def __str__(self):
        return self.name


class GovernmentScheme(models.Model):
    """Model for storing government schemes information"""
    
    SECTOR_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('health', 'Health'),
        ('education', 'Education'),
        ('employment', 'Employment'),
        ('social_welfare', 'Social Welfare'),
        ('rural_development', 'Rural Development'),
        ('urban_development', 'Urban Development'),
        ('women_empowerment', 'Women Empowerment'),
        ('youth_development', 'Youth Development'),
        ('senior_citizens', 'Senior Citizens'),
        ('disability', 'Disability'),
        ('other', 'Other'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('kn', 'Kannada'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('bn', 'Bengali'),
        ('gu', 'Gujarati'),
        ('mr', 'Marathi'),
        ('pa', 'Punjabi'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=500, help_text="Scheme title")
    description = models.TextField(help_text="Detailed description of the scheme")
    # 🛠️ FIX: Removed 'max_length=1000' which is invalid for a TextField
    short_description = models.TextField(help_text="Brief description", blank=True, null=True, default='')
    
    # Categorization
    # 🛠️ FIX: Use the 'Sector' model defined above
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True)
    sub_sectors = models.JSONField(default=list, help_text="Additional sectors this scheme covers")
    
    # Government Information
    ministry = models.CharField(max_length=200, help_text="Responsible ministry")
    department = models.CharField(max_length=200, help_text="Responsible department")
    government_level = models.CharField(
        max_length=20,
        choices=[('central', 'Central'), ('state', 'State'), ('local', 'Local')],
        help_text="Level of government"
    )
    state = models.CharField(max_length=100, blank=True, null=True, help_text="State (if applicable)")
    
    # Eligibility and Benefits
    eligibility_criteria = models.TextField(help_text="Who can apply")
    benefits = models.TextField(help_text="What benefits are provided")
    financial_assistance = models.TextField(blank=True, null=True, help_text="Financial assistance details")
    
    # Application Process
    application_process = models.TextField(help_text="How to apply")
    required_documents = models.JSONField(default=list, help_text="Documents required for application")
    application_link = models.URLField(blank=True, null=True, help_text="Online application link")
    
    # Important Dates
    launch_date = models.DateField(help_text="When the scheme was launched")
    last_date = models.DateField(blank=True, null=True, help_text="Last date to apply")
    validity_period = models.CharField(max_length=100, blank=True, null=True, help_text="Scheme validity period")
    
    # Contact Information
    helpline_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Multilingual Support
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    title_translations = models.JSONField(default=dict, help_text="Translations of title in different languages")
    description_translations = models.JSONField(default=dict, help_text="Translations of description")
    short_description_translations = models.JSONField(default=dict, blank=True, help_text="Translations of short description")
    benefits_translations = models.JSONField(default=dict, blank=True, help_text="Translations of benefits")
    eligibility_criteria_translations = models.JSONField(default=dict, blank=True, help_text="Translations of eligibility criteria")
    application_process_translations = models.JSONField(default=dict, blank=True, help_text="Translations of application process")
    financial_assistance_translations = models.JSONField(default=dict, blank=True, help_text="Translations of financial assistance")
    
    # Metadata
    origin = models.CharField(max_length=64, default='bulk-import', help_text="Origin/source of this scheme record (e.g., 'web-scrape', 'bulk-import', 'manual-entry')")
    source_url = models.URLField(help_text="Source URL where this information was scraped from")
    data_source = models.CharField(
        max_length=20,
        default='manual',
        choices=(('manual', 'Manual'), ('scraped', 'Scraped')),
        help_text="Whether this scheme was manually added or scraped from a website"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether the scheme is currently active")
    
    # Search and Keywords
    keywords = models.JSONField(default=list, help_text="Keywords for search functionality")
    search_tags = models.JSONField(default=list, help_text="Tags for better search and categorization")
    
    class Meta:
        db_table = 'scheme'
        indexes = [
            models.Index(fields=['sector']),
            models.Index(fields=['government_level']),
            models.Index(fields=['state']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        # 🛠️ FIX: Access the 'name' property of the sector object
        return f"{self.title} - {self.sector.name if self.sector else 'N/A'}"

    def get_title(self, lang: str = 'en') -> str:
        """Return translated title for given language code, falling back to stored title.

        - `lang` should be an ISO code like 'en', 'hi', 'kn' or with region 'en-US'.
        - The method tries exact match, then base-language match, then case-insensitive startswith.
        """
        if not lang:
            lang = 'en'
        title_map = self.title_translations or {}
        # direct lookup
        if lang in title_map and title_map[lang]:
            return title_map[lang]
        # try base language (en-US -> en)
        if '-' in lang:
            base = lang.split('-')[0]
            if base in title_map and title_map[base]:
                return title_map[base]
        # case-insensitive fallback
        for k, v in title_map.items():
            if not k:
                continue
            if k.lower() == lang.lower() or k.split('-')[0].lower() == lang.split('-')[0].lower():
                return v
        return self.title or ''

    def get_description(self, lang: str = 'en') -> str:
        """Return translated description for given language code, falling back to stored description."""
        if not lang:
            lang = 'en'
        desc_map = self.description_translations or {}
        if lang in desc_map and desc_map[lang]:
            return desc_map[lang]
        if '-' in lang:
            base = lang.split('-')[0]
            if base in desc_map and desc_map[base]:
                return desc_map[base]
        for k, v in desc_map.items():
            if not k:
                continue
            if k.lower() == lang.lower() or k.split('-')[0].lower() == lang.split('-')[0].lower():
                return v
        return self.description or ''

    def get_field_translation(self, field_name: str, lang: str = 'en') -> str:
        """Generic helper to get translation for any text field.
        
        Args:
            field_name: Name of the field (e.g., 'benefits', 'eligibility_criteria')
            lang: Language code (e.g., 'en', 'hi', 'kn')
        
        Returns:
            Translated text if available, otherwise original English text
        """
        if not lang or lang == 'en':
            return getattr(self, field_name, '') or ''
        
        # Check if there's a corresponding _translations field
        translations_field = f"{field_name}_translations"
        if not hasattr(self, translations_field):
            return getattr(self, field_name, '') or ''
        
        trans_map = getattr(self, translations_field) or {}
        
        # Direct match
        if lang in trans_map and trans_map[lang]:
            return trans_map[lang]
        
        # Base language fallback (en-US -> en)
        if '-' in lang:
            base = lang.split('-')[0]
            if base in trans_map and trans_map[base]:
                return trans_map[base]
        
        # Case-insensitive fallback
        for k, v in trans_map.items():
            if not k:
                continue
            if k.lower() == lang.lower() or k.split('-')[0].lower() == lang.split('-')[0].lower():
                return v
        
        # Final fallback to original field
        return getattr(self, field_name, '') or ''


class ChatSession(models.Model):
    """Model for storing chat sessions"""
    
    session_id = models.CharField(max_length=100, unique=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    language = models.CharField(max_length=10, choices=GovernmentScheme.LANGUAGE_CHOICES, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_sessions'
    
    def __str__(self):
        return f"Session {self.session_id} - {self.language}"


class ChatMessage(models.Model):
    """Model for storing individual chat messages"""
    
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    text_content = models.TextField(help_text="Text content of the message")
    audio_file = models.FileField(upload_to='chat_audio/', blank=True, null=True)
    language = models.CharField(max_length=10, choices=GovernmentScheme.LANGUAGE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # For bot messages
    related_schemes = models.JSONField(default=list, help_text="IDs of schemes mentioned in this response")
    confidence_score = models.FloatField(blank=True, null=True, help_text="Confidence score for the response")
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.text_content[:50]}..."


class WebScrapingLog(models.Model):
    """Model for logging web scraping activities"""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]
    
    source_url = models.URLField()
    source_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    schemes_found = models.IntegerField(default=0)
    schemes_added = models.IntegerField(default=0)
    schemes_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'scraping_logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.source_name} - {self.status} - {self.schemes_found} schemes"


class AdminUser(models.Model):
    """Extended user model for admin panel"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('moderator', 'Moderator')],
        default='admin'
    )
    can_scrape = models.BooleanField(default=True)
    can_manage_schemes = models.BooleanField(default=True)
    can_manage_users = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'admin_users'
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


class UserProfile(models.Model):
    """Extended user profile for government scheme assistant"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    EDUCATION_CHOICES = [
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('higher_secondary', 'Higher Secondary'),
        ('graduate', 'Graduate'),
        ('postgraduate', 'Postgraduate'),
        ('other', 'Other'),
    ]
    
    EMPLOYMENT_CHOICES = [
        ('employed', 'Employed'),
        ('unemployed', 'Unemployed'),
        ('self_employed', 'Self Employed'),
        ('student', 'Student'),
        ('retired', 'Retired'),
        ('homemaker', 'Homemaker'),
        ('other', 'Other'),
    ]
    
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='govt_profile')
    
    # Personal Information
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Mobile number for notifications")
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Age in years")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    education = models.CharField(max_length=20, choices=EDUCATION_CHOICES, blank=True, null=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, blank=True, null=True)
    
    # Location Information
    state = models.CharField(max_length=100, blank=True, null=True, help_text="State of residence")
    district = models.CharField(max_length=100, blank=True, null=True, help_text="District of residence")
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text="PIN code")
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10, 
        choices=GovernmentScheme.LANGUAGE_CHOICES, 
        default='en',
        help_text="Preferred interface language"
    )
    interested_sectors = models.JSONField(
        default=list, 
        help_text="List of sectors user is interested in"
    )
    notification_preferences = models.JSONField(
        default=dict, 
        help_text="Notification settings"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False, help_text="Whether user profile is verified")
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['preferred_language']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Profile"


class UserSchemeInteraction(models.Model):
    """Track user interactions with schemes"""
    
    INTERACTION_TYPES = [
        ('viewed', 'Viewed'),
        ('applied', 'Applied'),
        ('bookmarked', 'Bookmarked'),
        ('shared', 'Shared'),
        ('inquired', 'Inquired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheme_interactions')
    scheme_id = models.CharField(max_length=100, help_text="MongoDB scheme ID")
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_data = models.JSONField(default=dict, help_text="Additional interaction details")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_scheme_interactions'
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['scheme_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.scheme_id}"


class UserSearchHistory(models.Model):
    """Track user search queries for personalization"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.TextField(help_text="Search query text")
    language = models.CharField(max_length=10, choices=GovernmentScheme.LANGUAGE_CHOICES, default='en')
    results_count = models.IntegerField(default=0, help_text="Number of results returned")
    clicked_schemes = models.JSONField(default=list, help_text="IDs of schemes user clicked on")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_search_history'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['language']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.query[:50]}..."


class UserNotification(models.Model):
    """User notifications for scheme updates and recommendations"""
    
    NOTIFICATION_TYPES = [
        ('scheme_recommendation', 'Scheme Recommendation'),
        ('scheme_update', 'Scheme Update'),
        ('application_deadline', 'Application Deadline'),
        ('new_scheme', 'New Scheme'),
        ('system', 'System Message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    scheme_id = models.CharField(max_length=100, blank=True, null=True, help_text="Related scheme ID")
    is_read = models.BooleanField(default=False, help_text="Whether notification has been read")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ScrapedScheme(models.Model):
    """
    Model for storing scraped schemes from MyScheme.gov.in
    Completely separate from GovernmentScheme - only stores title and URL
    """
    title = models.CharField(max_length=500)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scraped_scheme'
        ordering = ['-created_at']  # Newest first
    
    def __str__(self):
        return self.title