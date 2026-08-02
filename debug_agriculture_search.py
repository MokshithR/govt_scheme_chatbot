import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme, Sector

# Check Sector table
print("=== SECTORS IN DATABASE ===")
sectors = Sector.objects.all()
for sector in sectors:
    count = GovernmentScheme.objects.filter(sector=sector, is_active=True).count()
    print(f"{sector.name}: {count} schemes")

print("\n=== TESTING AGRICULTURE SEARCH ===")
# Test different search approaches
print("\n1. Exact match 'agriculture':")
schemes = GovernmentScheme.objects.filter(sector__name='agriculture', is_active=True)
print(f"   Found: {schemes.count()} schemes")

print("\n2. Case-insensitive match 'agriculture':")
schemes = GovernmentScheme.objects.filter(sector__name__iexact='agriculture', is_active=True)
print(f"   Found: {schemes.count()} schemes")

print("\n3. Contains 'agriculture':")
schemes = GovernmentScheme.objects.filter(sector__name__icontains='agriculture', is_active=True)
print(f"   Found: {schemes.count()} schemes")
for s in schemes[:5]:
    print(f"   - {s.title}")

print("\n4. All agriculture-related by keyword:")
from django.db.models import Q
agriculture_keywords = ['agriculture', 'farmer', 'farming', 'crop', 'irrigation', 'kisan']
q_obj = Q()
for kw in agriculture_keywords:
    q_obj |= (
        Q(sector__name__icontains=kw) |
        Q(title__icontains=kw) |
        Q(description__icontains=kw) |
        Q(keywords__contains=[kw]) |
        Q(search_tags__contains=[kw])
    )
schemes = GovernmentScheme.objects.filter(q_obj, is_active=True).distinct()
print(f"   Found: {schemes.count()} schemes")
for s in schemes[:10]:
    print(f"   - {s.title} (Sector: {s.sector.name if s.sector else 'None'})")
