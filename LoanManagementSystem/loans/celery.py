# celery.py
from __future__ import absolute_import, unicode_literals
import os
from loans.celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LoanManagementSystem.settings')

app = Celery('LoanManagementSystem')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
