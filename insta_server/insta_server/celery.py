import os
from celery import Celery
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE","insta_server.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
app = Celery("insta_server")
app.config_from_object("django.conf:settings",namespace="CELERY")
app.autodiscover_tasks()
