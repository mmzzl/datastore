from celery import Celery
from app.core.config import settings

broker = settings.celery_broker_url or f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
backend = settings.celery_result_backend or (
    f"mongodb://{settings.mongodb_username}:{settings.mongodb_password}"
    f"@{settings.mongodb_host}:{settings.mongodb_port}/{settings.mongodb_database}"
)

celery_app = Celery("qlib_tasks", broker=broker, backend=backend)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=["app.qlib.train_task"],
)
