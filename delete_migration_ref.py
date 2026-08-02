import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("DELETE FROM django_migrations WHERE app='chatbot' AND name='0013_scrapedscheme';")
print('✅ Migration reference deleted')
