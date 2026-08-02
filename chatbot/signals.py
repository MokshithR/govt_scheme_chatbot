import os
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import GovernmentScheme

try:
    import pymongo
except Exception:  # pragma: no cover
    pymongo = None

logger = logging.getLogger(__name__)


def _get_collection():
    if not pymongo:
        return None
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    db_name = os.getenv('MONGODB_DB', os.getenv('MONGODB_DATABASE', 'govt_schemes'))
    coll_name = os.getenv('MONGODB_COLLECTION', 'government_schemes')
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    client.server_info()
    return client[db_name][coll_name]


def _transform_scheme(s: GovernmentScheme) -> dict:
    # Denormalize Django model into Mongo document for search
    sector_name = s.sector.name if s.sector_id else ''
    doc = {
        '_id': f'sql:{s.pk}',
        'sql_id': s.pk,
        'title': s.title or '',
        'description': s.description or '',
        'short_description': (s.description or '')[:200],
        'sector': sector_name,
        'department': s.department or '',
        'eligibility_criteria': s.eligibility_criteria or '',
        'benefits': s.benefits or '',
        'application_process': '',
        'application_link': s.application_link or '',
        'launch_date': str(s.launch_date) if s.launch_date else '',
        'last_date': str(s.last_date) if s.last_date else '',
        'ministry': '',
        'government_level': '',
        'language': 'en',
        'keywords': [],
        'search_tags': [sector_name.lower()] if sector_name else [],
        'source_url': '',
        'is_active': True,
        'cached_at': __import__('datetime').datetime.utcnow(),
    }
    return doc


@receiver(post_save, sender=GovernmentScheme)
def upsert_scheme_to_mongo(sender, instance: GovernmentScheme, **kwargs):
    try:
        coll = _get_collection()
        if not coll:
            return
        doc = _transform_scheme(instance)
        coll.update_one({'_id': doc['_id']}, {'$set': doc}, upsert=True)
        logger.info("Mongo cache upserted for scheme id=%s title='%s'", instance.pk, instance.title)
    except Exception as e:
        logger.warning("Failed to upsert scheme to Mongo cache: %s", e)


@receiver(post_delete, sender=GovernmentScheme)
def delete_scheme_from_mongo(sender, instance: GovernmentScheme, **kwargs):
    try:
        coll = _get_collection()
        if not coll:
            return
        coll.delete_one({'_id': f'sql:{instance.pk}'})
        logger.info("Mongo cache deleted for scheme id=%s title='%s'", instance.pk, instance.title)
    except Exception as e:
        logger.warning("Failed to delete scheme from Mongo cache: %s", e)
