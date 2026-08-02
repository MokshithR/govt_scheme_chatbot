from django.core.management.base import BaseCommand
from chatbot.models import GovernmentScheme
from datetime import date

class Command(BaseCommand):
    help = 'Add Garib Kalyan Rojgar Abhiyaan scheme to the database'

    def handle(self, *args, **options):
        self.stdout.write('🏛️ Adding Garib Kalyan Rojgar Abhiyaan to database...')
        
        # Check if scheme already exists
        existing = GovernmentScheme.objects.filter(title__icontains="garib kalyan rojgar").first()
        if existing:
            self.stdout.write(self.style.WARNING(f'⚠️ Scheme already exists: {existing.title}'))
            return
        
        # Create the scheme
        scheme = GovernmentScheme(
            title="Garib Kalyan Rojgar Abhiyaan",
            description="The Garib Kalyan Rojgar Abhiyaan (GKRA) is a public works program launched by the Government of India to provide employment opportunities to migrant workers and rural citizens who were affected by the COVID-19 pandemic. The scheme aims to empower and provide livelihood opportunities in rural areas by intensifying natural resource management works and focusing on 25 different types of works across 116 districts in 6 states.",
            short_description="A public works program providing employment to migrant workers and rural citizens affected by COVID-19.",
            sector="employment",
            sub_sectors=["rural_development", "employment", "social_welfare"],
            ministry="Ministry of Rural Development",
            department="Department of Rural Development",
            government_level="central",
            eligibility_criteria="Migrant workers and rural citizens who returned to their villages due to COVID-19 lockdown. Citizens from 116 districts across 6 states (Bihar, Jharkhand, Madhya Pradesh, Odisha, Rajasthan, and Uttar Pradesh) are eligible.",
            benefits="1. Employment opportunities in rural areas\n2. Wage employment for 125 days per worker\n3. Focus on 25 types of works including rural infrastructure, water conservation, and sanitation\n4. Immediate livelihood support to affected families",
            financial_assistance="Wage employment as per Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA) rates",
            application_process="1. Register at local Gram Panchayat\n2. Submit job card application\n3. Provide proof of residence and identity\n4. Contact local Rural Development Department office",
            required_documents=["Aadhaar Card", "Residence Proof", "Identity Card", "Bank Account Details", "Job Card"],
            launch_date=date(2020, 6, 20),
            validity_period="125 days per worker (extendable based on need)",
            helpline_number="1800-425-9399",
            website="https://ruraldevelopment.gov.in/garib-kalyan-rojgar-abhiyaan",
            source_url="https://ruraldevelopment.gov.in/garib-kalyan-rojgar-abhiyaan",
            language="en",
            keywords=["garib", "kalyan", "rojgar", "abhiyaan", "employment", "rural", "migrant", "workers", "covid", "public works", "mgnrega"],
            search_tags=["garib kalyan rojgar abhiyaan", "employment scheme", "rural employment", "migrant workers", "public works program", "covid relief", "rural development"],
            is_active=True
        )
        
        try:
            scheme.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully added scheme: {scheme.title}'))
            self.stdout.write(f'   ID: {scheme.id}')
            self.stdout.write(f'   Sector: {scheme.sector}')
            self.stdout.write(f'   Ministry: {scheme.ministry}')
            self.stdout.write(f'   Launch Date: {scheme.launch_date}')
            self.stdout.write(f'   Keywords: {scheme.keywords}')
            self.stdout.write(f'   Search Tags: {scheme.search_tags}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error saving scheme: {e}'))
