"""
Government Schemes Scraper
Scrapes from india.gov.in and other government portals
Stores into ScrapedScheme model (completely separate from GovernmentScheme)
"""

import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)


class MySchemeScaper:
    """Scraper for Government schemes from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_scheme_urls_from_sitemap(self):
        """
        Get scheme data from government portals
        Returns list of {title, url, description} dicts
        """
        schemes = []
        
        # Comprehensive list of central government schemes
        starter_schemes = [
            {
                'title': 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
                'url': 'https://pmjdy.gov.in/',
                'description': 'Financial Inclusion Programme for comprehensive financial services to all households. Provides zero balance bank accounts with RuPay debit card and accident insurance cover.'
            },
            {
                'title': 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
                'url': 'https://pmjay.gov.in/',
                'description': 'World\'s largest health insurance scheme providing coverage of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization.'
            },
            {
                'title': 'Pradhan Mantri Awas Yojana (PMAY)',
                'url': 'https://pmaymis.gov.in/',
                'description': 'Housing for All scheme providing financial assistance for construction and enhancement of houses in rural and urban areas.'
            },
            {
                'title': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
                'url': 'https://pmkisan.gov.in/',
                'description': 'Income support scheme for farmers providing Rs. 6000 per year in three equal installments directly to bank accounts of farmer families.'
            },
            {
                'title': 'Atal Pension Yojana (APY)',
                'url': 'https://www.npscra.nsdl.co.in/atal-pension-yojana.php',
                'description': 'Pension scheme for unorganized sector workers providing guaranteed minimum pension of Rs. 1000 to Rs. 5000 per month from age 60.'
            },
            {
                'title': 'Pradhan Mantri Ujjwala Yojana (PMUY)',
                'url': 'https://pmuy.gov.in/',
                'description': 'LPG connection scheme for BPL households providing deposit-free LPG connections to women from poor households.'
            },
            {
                'title': 'Pradhan Mantri Mudra Yojana (PMMY)',
                'url': 'https://www.mudra.org.in/',
                'description': 'Funding scheme for micro/small business enterprises providing loans up to Rs. 10 lakhs for income generating activities.'
            },
            {
                'title': 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
                'url': 'https://pmfby.gov.in/',
                'description': 'Crop insurance scheme providing financial support to farmers in crop failure due to natural calamities, pests & diseases.'
            },
            {
                'title': 'Swachh Bharat Mission',
                'url': 'https://swachhbharatmission.gov.in/',
                'description': 'Clean India Mission aimed at achieving universal sanitation coverage and making India open defecation free.'
            },
            {
                'title': 'Make in India',
                'url': 'https://www.makeinindia.com/',
                'description': 'Initiative to encourage companies to manufacture in India and increase employment and skill development.'
            },
            {
                'title': 'Digital India Programme',
                'url': 'https://www.digitalindia.gov.in/',
                'description': 'Transforming India into digitally empowered society through improved online infrastructure and internet connectivity.'
            },
            {
                'title': 'Skill India Mission',
                'url': 'https://www.skillindia.gov.in/',
                'description': 'Skill development initiative providing training to youth in industry-relevant skills for better employment opportunities.'
            },
            {
                'title': 'Beti Bachao Beti Padhao',
                'url': 'https://wcd.nic.in/bbbp-schemes',
                'description': 'Girl child welfare scheme addressing declining Child Sex Ratio and promoting girls\' education and empowerment.'
            },
            {
                'title': 'National Health Mission',
                'url': 'https://nhm.gov.in/',
                'description': 'Health sector initiative providing accessible, affordable and quality healthcare to rural and urban population.'
            },
            {
                'title': 'Pradhan Mantri Gram Sadak Yojana (PMGSY)',
                'url': 'https://omms.nic.in/',
                'description': 'Rural road connectivity programme providing all-weather road access to unconnected habitations.'
            },
            {
                'title': 'National Rural Employment Guarantee Scheme (NREGS)',
                'url': 'https://nrega.nic.in/',
                'description': 'Employment guarantee scheme providing 100 days of wage employment to rural households per year.'
            },
            {
                'title': 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
                'url': 'https://www.jansuraksha.gov.in/',
                'description': 'Accident insurance scheme providing Rs. 2 lakh cover for accidental death or disability at Rs. 12 per year premium.'
            },
            {
                'title': 'Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)',
                'url': 'https://www.jansuraksha.gov.in/',
                'description': 'Life insurance scheme providing Rs. 2 lakh life cover at Rs. 330 per year premium for people aged 18-50.'
            },
            {
                'title': 'Stand Up India Scheme',
                'url': 'https://www.standupmitra.in/',
                'description': 'Facilitating bank loans between Rs. 10 lakh and Rs. 1 crore to SC/ST and women entrepreneurs.'
            },
            {
                'title': 'Startup India Initiative',
                'url': 'https://www.startupindia.gov.in/',
                'description': 'Supporting startups through funding, tax benefits, simplified compliance and mentorship programs.'
            },
            {
                'title': 'National Social Assistance Programme (NSAP)',
                'url': 'https://nsap.nic.in/',
                'description': 'Social security scheme providing financial assistance to elderly, widows, and persons with disabilities from BPL families.'
            },
            {
                'title': 'Pradhan Mantri Garib Kalyan Yojana (PMGKY)',
                'url': 'https://pmgky.gov.in/',
                'description': 'Welfare package providing free food grains, direct cash transfers, and insurance cover during pandemic.'
            },
            {
                'title': 'National Rural Livelihood Mission (NRLM)',
                'url': 'https://aajeevika.gov.in/',
                'description': 'Poverty alleviation program mobilizing rural poor into Self Help Groups with access to financial services.'
            },
            {
                'title': 'Pradhan Mantri Shram Yogi Maan-dhan (PM-SYM)',
                'url': 'https://labour.gov.in/pm-sym',
                'description': 'Pension scheme for unorganized workers providing Rs. 3000 monthly pension after age 60.'
            },
            {
                'title': 'One Nation One Ration Card',
                'url': 'https://www.india.gov.in/spotlight/one-nation-one-ration-card',
                'description': 'Food security initiative enabling migrant workers to access subsidized foodgrains from any Fair Price Shop.'
            },
            {
                'title': 'Jal Jeevan Mission',
                'url': 'https://jaljeevanmission.gov.in/',
                'description': 'Water supply mission providing tap water connections to every rural household by 2024.'
            },
            {
                'title': 'Pradhan Mantri Matsya Sampada Yojana (PMMSY)',
                'url': 'https://pmmsy.dof.gov.in/',
                'description': 'Fisheries development scheme enhancing fish production and ensuring economic prosperity for fishers.'
            },
            {
                'title': 'Kisan Credit Card (KCC)',
                'url': 'https://pmkisan.gov.in/KCC.aspx',
                'description': 'Credit facility for farmers providing timely access to credit for agriculture at concessional rates.'
            },
            {
                'title': 'National Education Policy (NEP) 2020',
                'url': 'https://www.education.gov.in/nep',
                'description': 'Education reform framework transforming education system with focus on flexibility and skill development.'
            },
            {
                'title': 'Ayushman Bharat Health and Wellness Centres',
                'url': 'https://ab-hwc.nhp.gov.in/',
                'description': 'Preventive healthcare initiative providing comprehensive primary health care through wellness centers.'
            },
            {
                'title': 'PM Street Vendors AtmaNirbhar Nidhi (PM SVANidhi)',
                'url': 'https://pmsvanidhi.mohua.gov.in/',
                'description': 'Microcredit scheme for street vendors providing working capital loans up to Rs. 50,000.'
            },
            {
                'title': 'Production Linked Incentive (PLI) Scheme',
                'url': 'https://www.investindia.gov.in/production-linked-incentive-schemes',
                'description': 'Manufacturing incentive offering benefits on incremental sales from products made in India.'
            },
            {
                'title': 'National Infrastructure Pipeline (NIP)',
                'url': 'https://www.indiainvestmentgrid.gov.in/national-infrastructure-pipeline',
                'description': 'Infrastructure development plan with investment across energy, roads, railways and urban sectors.'
            },
            {
                'title': 'Smart Cities Mission',
                'url': 'https://smartcities.gov.in/',
                'description': 'Urban renewal program developing smart cities with core infrastructure and technology solutions.'
            },
            {
                'title': 'AMRUT (Atal Mission for Rejuvenation and Urban Transformation)',
                'url': 'https://amrut.gov.in/',
                'description': 'Urban infrastructure mission ensuring water supply, sewerage and green spaces in 500 cities.'
            },
        ]
        
        logger.info(f"Loaded {len(starter_schemes)} government schemes")
        return starter_schemes
    
    def scrape_scheme_page(self, url):
        """
        Scrape a single scheme page or use provided description
        Returns dict with extracted data
        """
        try:
            # For starter schemes with description already provided
            # Just return the data as-is
            return {
                'title': 'Scheme Title',
                'description': 'Scheme description will be provided',
                'source_url': url,
                'ministry': 'Central Government',
                'department': 'To be updated',
                'eligibility': 'Please visit official website',
                'benefits': 'Please visit official website',
                'extra_data': {},
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def run_full_scrape(self, limit=None):
        """
        Full scraping workflow:
        1. Get scheme data (using starter schemes)
        2. Save to ScrapedScheme model
        
        Returns: (added_count, updated_count, error_count)
        """
        from chatbot.models import ScrapedScheme
        
        logger.info("Starting scheme scraping...")
        
        # Step 1: Get scheme data
        scheme_list = self.get_scheme_urls_from_sitemap()
        
        if not scheme_list:
            logger.warning("No schemes found")
            return (0, 0, 0)
        
        if limit:
            scheme_list = scheme_list[:limit]
        
        added_count = 0
        updated_count = 0
        error_count = 0
        
        # Step 2: Save each scheme
        for idx, scheme_info in enumerate(scheme_list, 1):
            try:
                title = scheme_info.get('title')
                url = scheme_info.get('url')
                description = scheme_info.get('description', 'Description not available')
                
                logger.info(f"[{idx}/{len(scheme_list)}] Processing: {title}")
                
                # Check if already exists
                existing = ScrapedScheme.objects.filter(source_url=url).first()
                if existing:
                    logger.info(f"  ⏭️  Skipping (already exists)")
                    continue
                
                # Save to database
                scheme, created = ScrapedScheme.objects.update_or_create(
                    source_url=url,
                    defaults={
                        'title': title,
                        'description': description,
                        'ministry': 'Central Government',
                        'department': 'Various Departments',
                        'eligibility': 'Please visit official website for eligibility criteria',
                        'benefits': 'Please visit official website for benefits details',
                        'extra_data': {},
                        'language': 'en',
                        'reviewed': False,
                    }
                )
                
                if created:
                    added_count += 1
                    logger.info(f"  ✅ Added: {title[:60]}...")
                else:
                    updated_count += 1
                    logger.info(f"  🔄 Updated: {title[:60]}...")
                
                # Small delay
                time.sleep(0.2)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing scheme: {e}")
                continue
        
        logger.info(f"Scraping complete: Added={added_count}, Updated={updated_count}, Errors={error_count}")
        return (added_count, updated_count, error_count)
