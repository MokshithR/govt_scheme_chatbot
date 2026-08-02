"""
Script to initialize or add sample government schemes data directly to MongoDB.
"""
import pymongo
from datetime import datetime, date
import logging
import os

# Set up a basic logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- MongoDB Connection Details (from mongodb_adapter.py) ---
MONGO_URI = 'mongodb://localhost:27017/'
DATABASE_NAME = 'govt_schemes'
COLLECTION_NAME = 'government_schemes'

def get_mongo_collection():
    """Establishes MongoDB connection and returns the schemes collection."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info() # Test connection
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        logger.info(f"Successfully connected to MongoDB database '{DATABASE_NAME}'.")
        return collection
    except pymongo.errors.ServerSelectionTimeoutError as err:
        logger.error(f"Failed to connect to MongoDB at {MONGO_URI}.")
        logger.error("Please ensure the 'mongod' server is running in a separate terminal.")
        return None

# --- Sample Data (Matches the MongoDB Schema) ---
# This data includes the fields your chatbot logic actually searches for.
sample_schemes = [
    {
        'title': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
        'description': 'PM-KISAN is a Central Sector Scheme with 100% funding from Government of India. Under the scheme, income support of Rs.6000/- per year is provided to all farmer families across the country in three equal installments of Rs.2000/- each every four months.',
        'short_description': 'Income support of Rs.6000/- per year to all farmer families',
        'sector': 'Agriculture', # Matches the mapped name in mongodb_adapter
        'ministry': 'Ministry of Agriculture and Farmers Welfare',
        'department': 'Department of Agriculture, Cooperation and Farmers Welfare',
        'government_level': 'central',
        'eligibility_criteria': 'All landholding farmer families with cultivable land in their names',
        'benefits': 'Rs.6000/- per year in three equal installments of Rs.2000/- each',
        'application_process': 'Registration through Common Service Centres (CSC) or online portal',
        'launch_date': datetime(2019, 2, 1),
        'language': 'en',
        'keywords': ['farmer', 'agriculture', 'income support', 'pm-kisan'],
        'search_tags': ['agriculture', 'central', 'farmer welfare'],
        'source_url': 'https://pmkisan.gov.in/',
        'is_active': True
    },
    {
        'title': 'Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)',
        'description': 'AB-PMJAY is the largest health assurance scheme in the world which aims at providing a health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization to over 10.74 crores poor and vulnerable families.',
        'short_description': 'Health cover of Rs. 5 lakhs per family per year for hospitalization',
        'sector': 'Health', # Matches the mapped name
        'ministry': 'Ministry of Health and Family Welfare',
        'department': 'Department of Health and Family Welfare',
        'government_level': 'central',
        'eligibility_criteria': 'Families identified as per SECC database, having deprivation criteria',
        'benefits': 'Health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization',
        'application_process': 'Eligible families can avail services at empaneled hospitals',
        'launch_date': datetime(2018, 9, 23),
        'language': 'en',
        'keywords': ['health', 'medical', 'hospitalization', 'ayushman bharat'],
        'search_tags': ['health', 'central', 'medical insurance'],
        'source_url': 'https://pmjay.gov.in/',
        'is_active': True
    },
    {
        'title': 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
        'description': 'PMJDY is a National Mission for Financial Inclusion to ensure access to financial services, namely, Banking/ Savings & Deposit Accounts, Remittance, Credit, Insurance, Pension in an affordable manner.',
        'short_description': 'Financial inclusion mission to provide banking services to all',
        'sector': 'Social Welfare', # Matches the mapped name
        'ministry': 'Ministry of Finance',
        'department': 'Department of Financial Services',
        'government_level': 'central',
        'eligibility_criteria': 'All unbanked households in the country',
        'benefits': 'Zero balance savings account, RuPay debit card, accident insurance cover of Rs.1 lakh',
        'application_process': 'Visit any bank branch or Business Correspondent outlet',
        'launch_date': datetime(2014, 8, 28),
        'language': 'en',
        'keywords': ['banking', 'financial inclusion', 'jan dhan', 'savings account'],
        'search_tags': ['social welfare', 'central', 'banking'],
        'source_url': 'https://pmjdy.gov.in/',
        'is_active': True
    },
    {
        'title': 'Pradhan Mantri Mudra Yojana (PMMY)',
        'description': 'PMMY is a scheme launched by the Hon\'ble Prime Minister on April 8, 2015 for providing loans up to 10 lakh to the non-corporate, non-farm small/micro enterprises.',
        'short_description': 'Loans up to 10 lakh for small/micro enterprises',
        'sector': 'Employment and Skill Development', # Matches the mapped name
        'ministry': 'Ministry of Finance',
        'department': 'Department of Financial Services',
        'government_level': 'central',
        'eligibility_criteria': 'Non-corporate, non-farm small/micro enterprises',
        'benefits': 'Loans up to Rs.10 lakh under three categories: Shishu (up to Rs.50,000), Kishore (Rs.50,000 to Rs.5 lakh), Tarun (Rs.5 lakh to Rs.10 lakh)',
        'application_process': 'Apply through any of the lending institutions like Banks, NBFCs, MFIs',
        'launch_date': datetime(2015, 4, 8),
        'language': 'en',
        'keywords': ['loan', 'mudra', 'small business', 'micro enterprise'],
        'search_tags': ['employment', 'central', 'loan'],
        'source_url': 'https://mudra.org.in/',
        'is_active': True
    },
    {
        'title': 'Beti Bachao Beti Padhao Scheme',
        'description': 'Aims to address the declining Child Sex Ratio (CSR) and related issues of women empowerment over a life-cycle continuum.',
        'short_description': 'Aims to address the declining Child Sex Ratio (CSR).',
        'sector': 'Women and Child Development', # Matches the mapped name
        'ministry': 'Ministry of Women and Child Development',
        'department': 'Ministry of Women and Child Development',
        'government_level': 'central',
        'eligibility_criteria': 'Targets districts with low Child Sex Ratio.',
        'benefits': 'Awareness campaigns, improvement in girl child education, and welfare services.',
        'application_process': 'This is a social campaign; benefits are delivered through various service points like schools and health centers.',
        'launch_date': datetime(2015, 1, 22),
        'language': 'en',
        'keywords': ['girl child', 'women', 'empowerment', 'beti bachao'],
        'search_tags': ['women', 'child', 'central', 'education'],
        'source_url': 'https://wcd.nic.in/bbbp-schemes',
        'is_active': True
    }
]

def load_data():
    """Loads the sample schemes into the MongoDB collection."""
    
    collection = get_mongo_collection()
    if collection is None:
        logger.error("Data loading aborted. MongoDB connection failed.")
        return

    logger.info(f"Adding/Updating {len(sample_schemes)} schemes in '{COLLECTION_NAME}' collection...")
    
    created_count = 0
    updated_count = 0
    
    for scheme_data in sample_schemes:
        try:
            # Use update_one with upsert=True to create if not exist, or update if it does
            result = collection.update_one(
                {'title': scheme_data['title']},  # Filter to find existing document
                {'$set': scheme_data},             # Data to insert or update
                upsert=True                        # Create if it doesn't exist
            )
            
            if result.upserted_id:
                created_count += 1
                logger.info(f"  Created: {scheme_data['title']}")
            elif result.matched_count > 0:
                updated_count += 1
                logger.info(f"  Updated: {scheme_data['title']}")
                
        except Exception as e:
            logger.error(f"Error processing {scheme_data['title']}: {e}")

    logger.info(
        f"\nSuccessfully processed {len(sample_schemes)} schemes. "
        f"Created: {created_count}, Updated: {updated_count}"
    )
    
    # Display summary
    total_schemes = collection.count_documents({})
    logger.info(f"Total schemes in MongoDB: {total_schemes}")
    logger.info("Data loading complete.")


if __name__ == "__main__":
    # Ensure Django environment is set up (in case models are imported elsewhere)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
    try:
        import django
        django.setup()
    except ImportError:
        logger.warning("Could not set up Django (this is OK if script is standalone).")
    
    load_data()