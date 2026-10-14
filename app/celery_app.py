from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "deribit_exchange_client",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)
celery_app.conf.update(
    enable_utc=True,
    timezone="UTC",
    beat_schedule={
        "collect-index-prices-every-minute": {
            "task": "app.tasks.collect_index_prices",
            "schedule": crontab(minute="*"),
        }
    },
)
