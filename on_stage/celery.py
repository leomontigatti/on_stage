import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "on_stage.settings")

app = Celery("on_stage")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if not settings.DEBUG:
    app.conf.beat_schedule = {
        # Executes every day at 12:00 hs.
        "choreography_price_update": {
            "name": "update_choreography_price",
            "task": "choreography.tasks.update_choreography_price",
            "schedule": crontab(hour=12, minute=0),
        },
    }
