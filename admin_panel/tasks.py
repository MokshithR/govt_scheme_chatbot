from celery import shared_task
import logging
from chatbot.web_scraper import scraper

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_scraping_task(self):
    logger.info("Celery task: starting scraping run")
    try:
        result = scraper.run_full_scraping()
        logger.info(f"Celery task: scraping completed: {result}")
        return {'success': True, 'result': result}
    except Exception as e:
        logger.error(f"Celery task: scraping failed: {e}")
        return {'success': False, 'error': str(e)}
