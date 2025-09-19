from celery import Celery

from chatzzk.services.collector.container import Container
from chatzzk.services.collector.settings import collector_settings

TASK_MODULES = [
    "chatzzk.services.collector.jobs.tasks.discovery",
    "chatzzk.services.collector.jobs.tasks.processing",
]

celery_collector_app = Celery(
    "collector",  # 이 서비스의 Celery 앱 이름
    broker=collector_settings.celery_broker_url,
    backend=collector_settings.celery_result_backend,
    # Celery가 자동으로 Task를 찾을 경로
    include=TASK_MODULES,
)

celery_collector_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

# --- DI Container Initialization & Wiring ---
# This code runs once per worker process when it starts.
container = Container()
container.wire(modules=TASK_MODULES)
