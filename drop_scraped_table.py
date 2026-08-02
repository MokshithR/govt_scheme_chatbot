import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute('DROP TABLE IF EXISTS scraped_scheme CASCADE;')
print('✅ Table scraped_scheme dropped successfully')
