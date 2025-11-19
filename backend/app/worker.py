from celery import Celery
from config import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks']
)

celery_app.conf.task_routes = {
    "app.tasks.process_document_task": "main-queue"
}
