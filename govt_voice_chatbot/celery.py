import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')

app = Celery('govt_voice_chatbot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
