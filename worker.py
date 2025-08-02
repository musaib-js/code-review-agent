from celery import Celery
from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.autodiscover_tasks(["celery_tasks.review"])
